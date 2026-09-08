"""Simulations of the Blend load-driven admission mechanisms, as specified.

Simulates the exact rules of `blend-protocol.md` 1.7.0 (logos-lips branch
`docs/blend-load-driven-admission`, on the admission budget of #421) against
the measured Equi-X curves:

  * quantize_report  — the Load rule: novel arrivals against a core connection's
    share r_1, sixteen levels, rounded to nearest; exact integers.
  * EdgeDifficulty   — the per-node door controller (`Edge Difficulty`): every W
    rounds, on the distinct tokens presented P_n, x2 above 2*r_E per served
    round, x3/4 below r_E, bounds [d_edge_min, d_edge_max].
  * blend_difficulty — the consensus controller (`Blend Difficulty`): a pure
    function of one epoch's reports, d = BASE * l_star // max(L_MIN, lower
    median); an empty report set yields BASE. Exact integers, real BN254 modulus.

Five studies:

  1. door    — the door under constant and adaptive floods, over the budget and
               the shares of #421: does the price find the flood, who gets the
               edge share, what does the defender's CPU do?
  2. grace   — stranded honest solvers vs the grace window G.
  3. median  — how far a colluding fraction moves d_blend; quantization ties.
  4. leader  — the edge leader: pre-mining duty cycle, slot-time solving risk.
  5. loop    — level -> d_blend -> F_W -> novel arrivals -> level, closed over
               transaction demand and solver hashpower.

Run:  python -m equix_bench.blend_admission --out results/blend-admission
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from .difficulty_control import mint_rate_per_machine

# ----------------------------------------------------------------- calibration
# Pooled measured mint rates (results */main/mining.csv, tokens_per_sec_machine).
# Pi 5: the target machine, whole machine (4 workers) — RPi5-16GB, the slower of
# the two measured boards; RPi5-8GB agrees within 0.5% on every point. 285HX:
# the fastest measured solver, per core (machine / 24 workers) — the marginal
# attacker.
PI5_MINT: list[tuple[int, float]] = [(100, 4.4530), (300, 1.3950), (1000, 0.4243), (3000, 0.1715)]
ATTACKER_CORE_MINT: list[tuple[int, float]] = [(100, 3.5514), (300, 1.2694), (1000, 0.3868), (3000, 0.1114)]

# Public header verification rate, one Pi 5 core: 6.388 ms median, 3.99x to
# four threads. Primary record: reports/blend/header-verification/
# console-RPi5.txt, measured at logos-blockchain 87138d2 (three-branch
# circuit), performance governor.
V_HEADER = 157.0
# Equi-X verify, cold challenge, Pi 5, C implementation (findings.md section 3;
# results.csv medians 54.9-55.2 us across both Pi boards).
T_TOKEN_VERIFY = 54.7e-6

# ------------------------------------------------- spec constants (1.7.0)
ROUND = 1.0          # seconds per round
W = 30               # observation window, rounds
DELTA_MAX = 3        # maximal blending delay, rounds
BETA_MAX = 3         # blending operations per message
F_C, R_C = 1.0, 0    # cover messages per round, replication
F_D, R_D = 1 / 30, 0 # data messages per round, replication
F_T = 199 / 30       # messages carrying transactions per round, whatever quota backs them
# The rate a core connection carries (Expected Traffic).
F_1 = max(F_C * (1 + R_C), (F_D + F_T) * (1 + R_D)) * BETA_MAX      # 20.0
V = 156              # messages/s the slowest targeted node processes (one below 157 measured)
R = 2 * V // 3       # growth of the admission budget per round: 104
B = (V - R) * DELTA_MAX                                            # its largest value: 156
PHI_CC = 4           # peering degree; a node holds PHI_CC-1 .. PHI_CC+1 core connections
PHI_CC_RANGE = (PHI_CC - 1, PHI_CC, PHI_CC + 1)
R_1 = R // (PHI_CC + 1)                                            # a core connection's share: 20
R_E = R - R_1 * PHI_CC                                             # the edge share: 24
PHI_W = 0.25         # share of F_T sized for the proof of work branch
F_W_SIZED = PHI_W * F_T                                            # 1.658
F_TX = (1 - PHI_W) * F_T                                           # the rest of F_T: 4.975
_l_star = 8 * F_1 / R_1
assert _l_star.is_integer(), "l_star must be a level"
L_STAR = int(_l_star)                                              # the load set point: 8
L_MIN = math.ceil(L_STAR * PHI_W)                                  # the loosening floor: 2
D_EDGE_MIN = 300
D_EDGE_MAX = 1000
T_R = 600            # challenge rotation, rounds
G = 60               # price grace window, rounds

# BN254 scalar field modulus (the PowTarget field).
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617
BLEND_DIFFICULTY_BASE = P // 2**19


def pi5_rate(d: float) -> float:
    """Tokens/s a whole Pi 5 mints at effort d (pooled, measured)."""
    return mint_rate_per_machine(d, PI5_MINT)


def attacker_core_rate(d: float) -> float:
    """Tokens/s one fastest-measured core mints at effort d."""
    return mint_rate_per_machine(d, ATTACKER_CORE_MINT)


# --------------------------------------------------------------------- the load


def quantize_report(novel: int, served_rounds: int) -> int:
    """The Load rule, verbatim: the level of A_n novel arrivals over S_n served
    rounds against a core connection's share, sixteen levels, rounded to
    nearest, exact integers. No served round -> 0."""
    if served_rounds == 0:
        return 0
    return min(15, (16 * novel + R_1 * served_rounds) // (2 * R_1 * served_rounds))


def quantize_level(novel_per_round: float) -> int:
    """The same rule on a mean rate (the loop study)."""
    return min(15, int(math.floor((16 * novel_per_round + R_1) / (2 * R_1))))


# ------------------------------------------------------------- the controllers


@dataclass
class EdgeDifficulty:
    """The Edge Difficulty rule, verbatim: every W rounds, against the distinct
    tokens presented P over those rounds (passing checks 1-3, served or not)
    and the served rounds S:

      1. if P > 2*r_E*S: d <- min(2d, Max)
      2. if P < r_E*S:   d <- max(3d//4, Min)
      3. otherwise unchanged.

    P counts every distinct token, served or refused: the door needs the excess
    demand that Load's served-only count cannot carry. The raise threshold is
    twice the decay threshold because doubling d halves a fixed solver's rate,
    so a narrower band would oscillate.
    """
    d: int = D_EDGE_MIN

    def retarget(self, presentations: float, served_rounds: int = W) -> int:
        if presentations > 2 * R_E * served_rounds:
            self.d = min(2 * self.d, D_EDGE_MAX)
        elif presentations < R_E * served_rounds:
            self.d = max(3 * self.d // 4, D_EDGE_MIN)
        return self.d


def grace_floor(d_history: list[int], at: int) -> int:
    """The lowest price in force during the past G rounds, `at` inclusive
    (check 2 of Edge Admission)."""
    return min(d_history[max(0, at - G + 1): at + 1])


def lower_median(values: list[int]) -> int:
    return sorted(values)[(len(values) - 1) // 2]


def blend_difficulty(reports: list[int]) -> int:
    """The Blend Difficulty rule, verbatim (exact integers): a pure function of
    one epoch's report set. No reports -> BASE (the calibrated prior); a median
    below L_MIN loosens no further than BASE*L_STAR//L_MIN, where the proof of
    work branch reaches the whole of F_T. The historical recursive rule (x2 step
    clamp, hold on empty) was dropped so a checkpoint-bootstrapped node can
    compute the value from carried ledger state alone; runaway_epochs_uncapped()
    below records why the pre-fix zero branch needed a cap at all."""
    if not reports:
        return BLEND_DIFFICULTY_BASE
    load = max(L_MIN, lower_median(reports))
    return (BLEND_DIFFICULTY_BASE * L_STAR) // load


def d_blend(s: int, reports_by_epoch) -> int:
    """The epoch wrapper: BASE for the bootstrap epochs, else the pure rule on
    the reports attesting epoch s-3."""
    if s < 3:
        return BLEND_DIFFICULTY_BASE
    return blend_difficulty(reports_by_epoch(s - 3))


# --------------------------------------------------------------- study 1: door


@dataclass
class DoorTrace:
    round: list[int] = field(default_factory=list)
    d: list[int] = field(default_factory=list)
    offered: list[int] = field(default_factory=list)        # edge presentations this round
    served_attacker: list[int] = field(default_factory=list)
    served_honest: list[int] = field(default_factory=list)
    refused_honest: list[int] = field(default_factory=list)
    load_levels: list[int] = field(default_factory=list)    # the Load rule over trailing W
    cpu: list[float] = field(default_factory=list)          # fraction of one core
    budget_empty: list[bool] = field(default_factory=list)
    mining: list[float] = field(default_factory=list)       # attacker cores mining this round


def simulate_door(rounds: int, attacker_cores, honest_edge_rate: float = 2.0,
                  seed: int = 0, adaptive_giveup: int | None = None,
                  core_novel_mean: float | None = None) -> DoorTrace:
    """The door over #421's admission. Each round the budget grows by R to at
    most B. Core traffic: Poisson(core_novel_mean) novel messages, each read
    once per neighbor (flooding), each connection read up to its share r_1.
    Edge: the attacker owns `attacker_cores(t)` fastest-measured cores and
    presents distinct valid tokens at the grace-floor price (rate-limited by its
    hashpower); with `adaptive_giveup` it mines only while d < giveup. Honest
    edge nodes offer Poisson(honest_edge_rate) per round with valid tokens
    (they pre-mine; study 2 prices that). Edge connections are served in random
    arrival order, together up to their share r_E, within the budget (checks 4
    and admission rule 3).

    Load counts novel arrivals: the core novel messages plus the edge
    connections served (an edge message is novel once). The door reads the
    presentations. Each offer is a distinct fresh token, which matches the
    one-token-counts-once rule; checks 1 and 3 (window rotation, spent cache)
    are not modeled — token identity never repeats here by construction."""
    rng = random.Random(seed)
    ctrl = EdgeDifficulty()
    tr = DoorTrace()
    window: list[int] = []             # per-round novel arrivals, trailing W
    pwindow: list[int] = []            # per-round presentations, trailing W
    if core_novel_mean is None:
        # The sized operating point: F_1 novel per round in total, the honest
        # edge messages being part of F_T rather than on top of it.
        core_novel_mean = F_1 - honest_edge_rate
    budget = B
    d_hist: list[int] = []
    for t in range(rounds):
        budget = min(B, budget + R)
        d_hist.append(ctrl.d)
        mint_price = grace_floor(d_hist, len(d_hist) - 1)   # check 2: the floor, not the spot price
        cores = attacker_cores(t)
        if adaptive_giveup is not None and cores > 0:
            cores = cores if ctrl.d < adaptive_giveup else 0.0
        atk_offers = _poisson(rng, cores * attacker_core_rate(mint_price) * ROUND)
        hon_offers = _poisson(rng, honest_edge_rate * ROUND)

        # Core: every novel message arrives once per neighbor; each connection
        # is read up to its share, all within the budget.
        core_novel = _poisson(rng, core_novel_mean)
        core_reads = min(PHI_CC * core_novel, PHI_CC * R_1, budget)
        budget -= core_reads
        core_novel = min(core_novel, core_reads)

        # Edge: random arrival order, together up to r_E, within the budget.
        offers = ["a"] * atk_offers + ["h"] * hon_offers
        rng.shuffle(offers)
        taken = offers[:min(R_E, budget)]
        budget -= len(taken)
        acc_a, acc_h = taken.count("a"), taken.count("h")

        novel = core_novel + acc_a + acc_h
        presentations = atk_offers + hon_offers
        window.append(novel); pwindow.append(presentations)
        if len(pwindow) > W:
            pwindow.pop(0)
        if len(window) > W:
            window.pop(0)

        # CPU: one header verification per novel message, one token check per
        # presentation.
        cpu = novel / V_HEADER + presentations * T_TOKEN_VERIFY

        tr.round.append(t); tr.d.append(ctrl.d)
        tr.offered.append(presentations)
        tr.served_attacker.append(acc_a); tr.served_honest.append(acc_h)
        tr.refused_honest.append(hon_offers - acc_h)
        tr.load_levels.append(quantize_report(sum(window), len(window)))
        tr.cpu.append(cpu)
        tr.budget_empty.append(budget == 0)
        tr.mining.append(cores)

        if (t + 1) % W == 0:
            ctrl.retarget(sum(pwindow), W)
    return tr


def _poisson(rng: random.Random, lam: float) -> int:
    """Knuth's Poisson sampler; adequate for the small rates used here."""
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def trip_cores(d: float = D_EDGE_MIN) -> float:
    """Fastest-measured cores that trip the raise at price d: 2*r_E per round."""
    return 2 * R_E / attacker_core_rate(d)


def hold_cores(d: float = D_EDGE_MIN) -> float:
    """Fastest-measured cores that fill the edge share at price d: r_E per round."""
    return R_E / attacker_core_rate(d)


# -------------------------------------------------------------- study 2: grace


def stranded_probability(mean_solve: float, grace: float = G * ROUND) -> float:
    """P(an exponential solve outlives the grace window) — the worst case, where
    the price steps up immediately after the quote."""
    return math.exp(-grace / mean_solve)


def simulate_stranded(tr: DoorTrace, device_rate, solvers_per_round: float = 1.0,
                      seed: int = 1) -> tuple[int, int]:
    """Honest solvers through a door trace: each reads the quote at its start
    round, solves for Exp(1/device_rate(d_quote)) seconds, and passes check 2
    iff its quote clears the lowest d in force during the G rounds before it
    presents. Returns (stranded, total)."""
    rng = random.Random(seed)
    stranded = total = 0
    n = len(tr.d)
    for t in range(n):
        for _ in range(_poisson(rng, solvers_per_round)):
            quote = tr.d[t]
            solve = rng.expovariate(device_rate(quote))
            arrive = t + int(solve / ROUND)
            if arrive >= n:
                continue
            floor = grace_floor(tr.d, arrive)
            total += 1
            if quote < floor:
                stranded += 1
    return stranded, total


# ------------------------------------------------------------- study 3: median


def median_shift(n: int, colluders: float, direction: str, rng: random.Random,
                 honest_median: float = F_1, gsd: float = 1.6) -> tuple[int, int]:
    """One epoch of reports: n declarations, a `colluders` fraction reporting the
    extreme (15 to tighten, 0 to loosen), the rest lognormal around
    honest_median novel arrivals per round. Returns (honest-only median,
    shifted median), in levels."""
    honest = [quantize_level(honest_median * math.exp(rng.gauss(0, math.log(gsd))))
              for _ in range(n - int(n * colluders))]
    extreme = 15 if direction == "tighten" else 0
    reports = honest + [extreme] * int(n * colluders)
    return lower_median(honest), lower_median(reports)


def runaway_epochs_uncapped() -> int:
    """Epochs of sustained median 0 until the ORIGINAL recursive rule (hold
    state, double per epoch, bounded only by p-1) reached free admission from
    BASE. Exact, from the real modulus — the number that motivated flooring the
    median."""
    d, epochs = BLEND_DIFFICULTY_BASE, 0
    while d < P - 1:
        d = min(d * 2, P - 1)
        epochs += 1
    return epochs


def zero_median_settles_at() -> int:
    """Where the rule sits under a median of 0 — the L_MIN floor, instantly and
    statelessly."""
    return blend_difficulty([0])


# ------------------------------------------------------------- study 4: leader


def erlang3_tail(mean_token: float, budget: float) -> float:
    """P(sum of three exponential token solves exceeds the budget)."""
    lam = 1.0 / mean_token
    x = lam * budget
    return math.exp(-x) * (1 + x + x * x / 2)


def premine_duty(d: int, tokens: int = 3, rotation: float = T_R * ROUND) -> float:
    """Fraction of a Pi 5 spent keeping `tokens` fresh across a rotation."""
    return tokens * (1.0 / pi5_rate(d)) / rotation


# ------------------------------------------------------------ study 5: the loop


def realized_f_w(d: int, hashpower: float = 1.0) -> float:
    """The proof of work rate at threshold `d` from solvers of fixed capacity:
    proportional to the threshold, and equal to the sized rate at BASE when
    `hashpower` is 1 — an assumption about exogenous mining, not a derived
    fact. `hashpower` scales the solvers against the sizing."""
    return hashpower * F_W_SIZED * d / BLEND_DIFFICULTY_BASE


def novel_rate(f_tx: float, f_w: float, cover: bool = False) -> float:
    """Novel arrivals per round at a node: every message once per hop. With
    `cover`, the cover traffic F_C is counted too; the specification's F_1
    takes the larger of cover and data, not their sum."""
    data = (F_D + f_tx + f_w) * (1 + R_D)
    return (data + (F_C * (1 + R_C) if cover else 0.0)) * BETA_MAX


def loop_step(level: int, f_tx: float = F_TX, hashpower: float = 1.0,
              cover: bool = False) -> int:
    """One turn of level -> d_blend -> F_W -> novel arrivals -> level."""
    d = blend_difficulty([level])
    return quantize_level(novel_rate(f_tx, realized_f_w(d, hashpower), cover))


def loop_attractor(start: int, **kw) -> list[int]:
    """The cycle the map settles into from `start`: a single level if it has a
    fixed point, several if it cycles."""
    seen, level = [], start
    while level not in seen:
        seen.append(level)
        level = loop_step(level, **kw)
    return sorted(set(seen[seen.index(level):]))


LOOP_DEMANDS = ((0.0, "none"), (F_TX / 2, "half"), (F_TX, "sized"), (F_T, "all of F_T"))
LOOP_HASHPOWERS = (0.5, 1.0, 2.0, 4.0, 8.0)


def loop_survey(demands=LOOP_DEMANDS, hashpowers=LOOP_HASHPOWERS, cover: bool = False) -> dict:
    """Every attractor of the map, from every starting level, over the
    transaction demand F_tx and the solvers' hashpower."""
    out = {}
    for f_tx, name in demands:
        for h in hashpowers:
            cycles = {tuple(loop_attractor(s, f_tx=f_tx, hashpower=h, cover=cover))
                      for s in range(16)}
            out[(name, h)] = sorted(cycles)
    return out


def blend_difficulty_sqrt(reports: list[int]) -> int:
    """CANDIDATE, not specified: the same re-anchor with half the gain,
    d = BASE * sqrt(l_star / max(L_MIN, median)), as integers with a 2**40
    scale. Range [BASE*sqrt(8/15), 2*BASE] — span 2.7x against the
    proportional rule's 7.5x."""
    if not reports:
        return BLEND_DIFFICULTY_BASE
    load = max(L_MIN, lower_median(reports))
    return (BLEND_DIFFICULTY_BASE * math.isqrt((L_STAR << 40) // load)) >> 20


def loop_step_rule(level: int, rule, f_tx: float = F_TX, hashpower: float = 1.0,
                   cover: bool = False) -> int:
    d = rule([level])
    return quantize_level(novel_rate(f_tx, realized_f_w(d, hashpower), cover))


def loop_attractor_rule(start: int, rule, **kw) -> list[int]:
    seen, level = [], start
    while level not in seen:
        seen.append(level)
        level = loop_step_rule(level, rule, **kw)
    return sorted(set(seen[seen.index(level):]))


def loop_attractor_two_epoch(start: tuple[int, int], f_tx: float = F_TX,
                             hashpower: float = 1.0, cover: bool = False) -> list[int]:
    """CANDIDATE, not specified: d from the mean of two consecutive epochs'
    medians (reports of s-3 and s-4; retention four epochs). The map is on
    pairs of levels; returns the levels the cycle visits."""
    seen, state = [], start
    while state not in seen:
        seen.append(state)
        m = (state[0] + state[1]) // 2
        d = blend_difficulty([m])
        nxt = quantize_level(novel_rate(f_tx, realized_f_w(d, hashpower), cover))
        state = (nxt, state[0])
    cyc = seen[seen.index(state):]
    return sorted({lvl for pair in cyc for lvl in pair[:1]})


def loop_survey_candidates(demands=LOOP_DEMANDS, hashpowers=LOOP_HASHPOWERS) -> dict:
    """Attractors of the two candidate damping rules, for comparison with the
    specified proportional rule."""
    out = {}
    for f_tx, name in demands:
        for h in hashpowers:
            sq = {tuple(loop_attractor_rule(s, blend_difficulty_sqrt, f_tx=f_tx, hashpower=h))
                  for s in range(16)}
            te = {tuple(loop_attractor_two_epoch((a, b), f_tx=f_tx, hashpower=h))
                  for a in range(16) for b in range(16)}
            out[(name, h)] = (sorted(sq), sorted(te))
    return out


def loop_gain(f_tx: float = F_TX, hashpower: float = 1.0, cover: bool = False) -> float:
    """|d level'/d level| of the continuous map at its fixed point: the share of
    the novel traffic the proof of work branch carries there. Below 1 the map
    converges; at 1 it is marginal and the quantized map cycles."""
    base = novel_rate(f_tx, 0.0, cover) * 8 / R_1               # the inelastic part, in levels
    k = 8 * BETA_MAX * hashpower * F_W_SIZED * L_STAR / R_1    # elastic part = k / level
    # fixed point: level = base + k / level
    level = (base + math.sqrt(base * base + 4 * k)) / 2
    return k / (level * level)


def _plot_door(tr: DoorTrace, path: Path, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(4, 1, figsize=(8, 9), sharex=True)
    ax[0].plot(tr.round, tr.offered, color="#DD8452", lw=0.7, label="edge presentations / round")
    ax[0].axhline(R_E, ls="--", color="#333", label=f"edge share $r_E$={R_E}")
    ax[0].axhline(2 * R_E, ls=":", color="#333", label=f"raise threshold $2 r_E$={2 * R_E}")
    ax[0].set_ylabel("presentations / round"); ax[0].set_title(title); ax[0].legend(fontsize=8)
    ax[1].plot(tr.round, tr.d, color="#55A868")
    ax[1].set_ylabel("door price $d_{edge}$"); ax[1].set_ylim(0, D_EDGE_MAX * 1.1)
    ax[2].plot(tr.round, tr.load_levels, color="#4C72B0", lw=0.8, label="reported load level")
    ax[2].axhline(L_STAR, ls="--", color="#C44E52", label="$\\ell^*$")
    ax[2].set_ylabel("load level"); ax[2].set_ylim(0, 15.5); ax[2].legend(fontsize=8)
    ax[3].plot(tr.round, [c * 100 for c in tr.cpu], color="#937860", lw=0.8)
    ax[3].set_ylabel("CPU, % of one core"); ax[3].set_xlabel("round (1 s)")
    for a in ax:
        a.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def _plot_median(path: Path, seed: int = 3) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rng = random.Random(seed)
    fracs = [i / 100 for i in range(0, 50, 2)]
    out = {}
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for i, direction in enumerate(("tighten", "loosen")):
        for n, color in ((32, "#4C72B0"), (100, "#55A868"), (1000, "#C44E52")):
            mult = []
            for c in fracs:
                trials = [median_shift(n, c, direction, rng) for _ in range(200)]
                # d_blend multiplier vs the honest value under the stateless
                # rule: the L_MIN floor caps the loosening.
                ratios = [max(hm, L_MIN) / max(L_MIN, sm) for hm, sm in trials]
                mult.append(sum(ratios) / len(ratios))
            ax[i].plot([f * 100 for f in fracs], mult, color=color, label=f"N={n}")
            out[(direction, n)] = dict(zip(fracs, mult))
        ax[i].axhline(1.0, ls="--", color="#333", lw=0.8)
        ax[i].set_title(f"colluders {direction}")
        ax[i].set_xlabel("colluding fraction, %")
        ax[i].grid(True, alpha=0.3)
    ax[0].set_ylabel("d_blend multiplier / epoch")
    ax[0].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return out


def _fmt_cycles(cycles) -> str:
    return ", ".join("fixed [%d]" % c[0] if len(c) == 1
                     else "cycle {%s}" % ",".join(map(str, c)) for c in cycles)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Blend load-driven admission simulations")
    ap.add_argument("--out", default="results/blend-admission")
    ap.add_argument("--rounds", type=int, default=3600)
    args = ap.parse_args(argv)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    lines = ["# Blend load-driven admission — simulation results\n"]
    attack = slice(700, 2400)

    # Study 1a: floods of 200 and 60 fastest cores, rounds [600, 2400).
    flood = simulate_door(args.rounds, lambda t: 200.0 if 600 <= t < 2400 else 0.0)
    _plot_door(flood, out / "door_flood.png", "Door under a 200-core flood (rounds 600–2400)")
    mid = simulate_door(args.rounds, lambda t: 60.0 if 600 <= t < 2400 else 0.0, seed=2)
    _plot_door(mid, out / "door_mid.png", "Door under a 60-core flood (rounds 600–2400)")
    acc_a = sum(flood.served_attacker[attack]); acc_h = sum(flood.served_honest[attack])
    ref_h = sum(flood.refused_honest[attack])
    peak_cpu = max(flood.cpu) * 100
    ceil_round = next(t for t, d in enumerate(flood.d) if d == D_EDGE_MAX)
    back_round = next((t for t, d in enumerate(flood.d) if t > 2400 and d == D_EDGE_MIN), None)
    mid_prices = sorted(set(mid.d[2000:2400]))
    mid_acc_a = sum(mid.served_attacker[attack]); mid_acc_h = sum(mid.served_honest[attack])
    mid_ref_h = sum(mid.refused_honest[attack])
    lines += [
        "## 1. The door under flood",
        f"- Trip point at the floor: 2·r_E = {2 * R_E} presentations per round, "
        f"{trip_cores():.0f} fastest cores; filling the edge share r_E = {R_E} at the floor "
        f"takes {hold_cores():.0f}. Holding the ceiling takes {trip_cores(D_EDGE_MAX):.0f}.",
        f"- 200 cores: floor→ceiling in {ceil_round - 600} rounds, held for the whole flood, "
        f"home in {back_round - 2400 if back_round else '>'} rounds after it. The attacker "
        f"takes {acc_a / max(1, acc_a + acc_h) * 100:.0f}% of the edge share; "
        f"{ref_h / max(1, ref_h + acc_h) * 100:.0f}% of honest offers are refused per round. "
        f"Peak CPU {peak_cpu:.0f}% of one Pi 5 core (headers + token checks).",
        f"- 60 cores: the price escalates to the ceiling, then settles at "
        f"{mid_prices[0] if len(mid_prices) == 1 else f'{mid_prices[0]}–{mid_prices[-1]}'} once the grace "
        f"floor catches up, where the attacker presents between r_E and 2·r_E and holds "
        f"{mid_acc_a / max(1, mid_acc_a + mid_acc_h) * 100:.0f}% of the share "
        f"({mid_ref_h / max(1, mid_ref_h + mid_acc_h) * 100:.0f}% of honest offers refused). "
        f"The band is where a priced occupation sits.",
        f"- Budget-empty rounds during the 200-core flood: "
        f"{sum(flood.budget_empty[attack])} of {2400 - 700} — the shares bound edge service "
        f"before the budget does.",
    ]

    # Study 1c: the same flood over a quiet core ambient: the door reads edge
    # presentations only, so it decays home the same way.
    quiet = simulate_door(args.rounds, lambda t: 200.0 if 600 <= t < 2400 else 0.0,
                          core_novel_mean=5.0, seed=4)
    _plot_door(quiet, out / "door_quiet.png",
               "The same flood over a quiet core ambient (5 novel/round)")
    q_back = next((t for t, d in enumerate(quiet.d) if t > 2400 and d == D_EDGE_MIN), None)
    sized_level = sorted(set(flood.load_levels[100:600]))
    lines += [
        "## 1c. Core traffic is not the door's signal",
        f"- Over a quiet core ambient (5 novel/round) the price decays home "
        f"{q_back - 2400 if q_back else '>'} rounds after the flood, as over the sized ambient "
        f"({back_round - 2400 if back_round else '>'}): the door reads edge presentations only.",
        f"- The reported load at the sized ambient sits at level {sized_level} before the "
        f"flood (set point {L_STAR}) and reaches {max(flood.load_levels[attack])} during it: "
        f"a full edge share is {R_E / R_1:.1f} core shares, {8 * R_E / R_1:.1f} levels, so a "
        f"flooded door reports the top level.",
    ]

    # Study 1b: adaptive attackers, give-up at 500.
    adaptive = simulate_door(args.rounds, lambda t: 60.0 if 600 <= t < 2400 else 0.0,
                             adaptive_giveup=500, seed=5)
    _plot_door(adaptive, out / "door_adaptive.png",
               "Door vs an adaptive attacker (60 cores, mines only while d < 500)")
    core_s = sum(adaptive.mining[attack]); core_s_const = sum(mid.mining[attack])
    acc_a2 = sum(adaptive.served_attacker[attack]); acc_h2 = sum(adaptive.served_honest[attack])
    prices = sorted(set(adaptive.d[attack]))
    sa, na = simulate_stranded(adaptive, lambda d: pi5_rate(d) / 4.0, seed=2)
    lines += [
        "## 1b. Adaptive attackers (give-up 500)",
        f"- 60 cores mining only below 500: a sawtooth over {prices[0]}–{prices[-1]} "
        f"({len(prices)} distinct prices; ×2 from wherever the decay re-admits the attacker, "
        f"×3/4 steps down while it waits). Mining duty {core_s / core_s_const * 100:.0f}%, "
        f"{acc_a2 / max(1, acc_a2 + acc_h2) * 100:.0f}% of served edge connections.",
        f"- Cost per served attacker message: {core_s / max(1, acc_a2):.1f} core-seconds "
        f"adaptive against {core_s_const / max(1, mid_acc_a):.1f} for the constant 60-core "
        f"flood — adapting buys no discount; the grace floor prices the token at the lowest "
        f"price the attacker waited for.",
        f"- Honest single-core solvers through the sawtooth: {sa}/{na} stranded.",
    ]

    # Study 2: stranded solvers, analytic worst case and through the flood trace.
    lines += ["## 2. Grace window", "",
              "| device | d | mean solve | P(stranded), worst case |", "|---|---|---|---|"]
    for name, div in (("Pi 5, 4 cores", 1.0), ("Pi 5, 1 core", 4.0)):
        for d in (D_EDGE_MIN, D_EDGE_MAX):
            mean = div / pi5_rate(d)
            lines.append(f"| {name} | {d} | {mean:.2f} s | {stranded_probability(mean):.2g} |")
    s4, n4 = simulate_stranded(flood, lambda d: pi5_rate(d))
    s1, n1 = simulate_stranded(flood, lambda d: pi5_rate(d) / 4.0, seed=2)
    lines += ["", f"- Through the 200-core flood trace: {s4}/{n4} four-core and {s1}/{n1} "
                  f"single-core solvers stranded (price steps are what strands, not the tail alone)."]

    # Study 3: median manipulation, both directions; runaway; quantization ties.
    shifts = _plot_median(out / "median_shift.png")
    ra = runaway_epochs_uncapped()
    rng = random.Random(9)
    ranks16 = [quantize_level(F_1 * math.exp(rng.gauss(0, math.log(1.6)))) for _ in range(100)]
    ties16 = 1 - len(set(ranks16)) / 100
    lines += [
        "## 3. Median robustness",
        f"- The rule is a pure re-anchor to BASE·{L_STAR}/max({L_MIN}, median), so a shifted "
        f"median is a bounded bias with no memory: at 30% colluders the mean multiplier is "
        f"{shifts[('tighten', 100)][0.30]:.2f} (tighten) / {shifts[('loosen', 100)][0.30]:.2f} "
        f"(loosen) at N=100, and it vanishes the epoch capture ends.",
        f"- The original recursive rule's zero-median branch doubled per epoch and reached free "
        f"admission in {ra} epochs from BASE; flooring the median at L_MIN = {L_MIN} closes it "
        f"statelessly — a zero median sits at {zero_median_settles_at() / BLEND_DIFFICULTY_BASE:.0f}"
        f"·BASE, where the branch reaches F_T, instantly and reversibly.",
        f"- Sixteen levels leave {ties16 * 100:.0f}% of 100 heterogeneous reporters sharing a "
        f"level — the targeting oracle sees buckets, not a ranking.",
    ]

    # Study 4: the edge-leader budget.
    lines += ["## 4. Edge leader", "",
              "| d | pre-mine duty (3 tokens per rotation) | P(3 solves > 15 s) | P(> 30 s) |",
              "|---|---|---|---|"]
    for d in (D_EDGE_MIN, D_EDGE_MAX):
        mean = 1.0 / pi5_rate(d)
        lines.append(f"| {d} | {premine_duty(d) * 100:.2f}% | {erlang3_tail(mean, 15):.2g} "
                     f"| {erlang3_tail(mean, 30):.2g} |")
    lines += ["", "- Pre-mining to the ceiling costs ~"
              f"{premine_duty(D_EDGE_MAX) * 100:.1f}% of a Pi 5 and removes the slot-time risk; "
              "solving at slot time at the ceiling misses the 15 s traversal budget "
              f"{erlang3_tail(1 / pi5_rate(D_EDGE_MAX), 15) * 100:.1f}% of the time."]

    # Study 5: the control loop, closed over demand and hashpower.
    survey = loop_survey()
    survey_cover = loop_survey(cover=True)
    cands = loop_survey_candidates()
    lines += ["## 5. The control loop, closed", "",
              "| F_tx \\ hashpower | " + " | ".join(f"×{h:g}" for h in LOOP_HASHPOWERS) + " |",
              "|---|" + "---|" * len(LOOP_HASHPOWERS)]
    for _, name in LOOP_DEMANDS:
        lines.append(f"| {name} | " + " | ".join(_fmt_cycles(survey[(name, h)])
                                                  for h in LOOP_HASHPOWERS) + " |")
    design = survey[("sized", 1.0)]
    worst = max(lvl for cycles in survey.values() for c in cycles for lvl in c)
    max_fw = max(realized_f_w(blend_difficulty([lvl]), h)
                 for (name, h), cycles in survey.items() for c in cycles for lvl in c)
    lines += ["", "Candidate rules (sqrt re-anchor / two-epoch mean), same grid:", "",
              "| F_tx \\ hashpower | " + " | ".join(f"×{h:g}" for h in LOOP_HASHPOWERS) + " |",
              "|---|" + "---|" * len(LOOP_HASHPOWERS)]
    for _, name in LOOP_DEMANDS:
        lines.append(f"| {name} | " + " | ".join(
            _fmt_cycles(cands[(name, h)][0]) + " / " + _fmt_cycles(cands[(name, h)][1])
            for h in LOOP_HASHPOWERS) + " |")
    lines += [
        "",
        f"- The design point (sized demand, hashpower ×1) is {_fmt_cycles(design)}: "
        f"{novel_rate(F_TX, F_W_SIZED):.1f} novel/round against r_1 = {R_1}, F_W = "
        f"{F_W_SIZED:.2f}, d = BASE. Loop gain there {loop_gain():.2f} ≈ φ.",
        f"- With no transaction demand the branch is the whole traffic and the gain is "
        f"{loop_gain(0.0):.2f}: the quantized map cycles (period 2, {survey[('none', 1.0)]}), "
        f"bounded by the floor L_MIN (d ≤ {L_STAR // L_MIN}·BASE, where F_W reaches F_T).",
        f"- The realized F_W stays below F_T in every attractor? "
        f"{'yes' if max_fw <= F_T + 1e-9 else 'NO: %.2f' % max_fw} (F_T = {F_T:.2f}). "
        f"Hashpower beyond the range's span pins the threshold at the tight end "
        f"(level 15, d = BASE·{L_STAR}/15) and the shares bind, as intended.",
        f"- Candidate damping, not specified — the sqrt re-anchor (gain halved, span 2.7×) "
        f"and the two-epoch mean (retention 4 epochs): with no demand at ×1 they give "
        f"{_fmt_cycles(cands[('none', 1.0)][0])} and {_fmt_cycles(cands[('none', 1.0)][1])}; "
        f"at the design point {_fmt_cycles(cands[('sized', 1.0)][0])} and "
        f"{_fmt_cycles(cands[('sized', 1.0)][1])}; at ×4 sized "
        f"{_fmt_cycles(cands[('sized', 4.0)][0])} and {_fmt_cycles(cands[('sized', 4.0)][1])}.",
        f"- Counting cover traffic in the novel arrivals (F_1 takes the larger of cover and "
        f"data, not the sum) moves the design point to {_fmt_cycles(survey_cover[('sized', 1.0)])}: "
        f"{novel_rate(F_TX, F_W_SIZED, cover=True):.1f} novel/round, one level above ℓ*.",
    ]

    header = "<!-- generated by equix_bench.blend_admission; the curated report is simulation.md -->\n"
    (out / "summary.md").write_text(header + "\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
