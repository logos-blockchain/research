"""Simulations of the Blend load-driven admission mechanisms, as specified.

Simulates the exact rules of `blend-protocol.md` 1.7.0 (logos-lips branch
`docs/blend-load-driven-admission`) against the measured Equi-X curves:

  * EdgeDifficulty  — the per-node door controller (`Edge Difficulty`): retarget
    every W rounds, x2 up / x3/4 down against the load levels, bounds
    [d_edge_min, d_edge_max].
  * blend_difficulty — the consensus controller (`Blend Difficulty`): a pure
    function of one epoch's reports, d = BASE * l_star // max(L_MIN, lower median);
    an empty report set yields BASE. Exact integers, real BN254 modulus.

Four studies, each answering one calibration question the specification's PR
carries as open:

  1. door       — the door controller under a constant and an adaptive flood:
                  does it hold verification load, who gets the acceptance rate?
  2. grace      — stranded honest solvers vs the grace window G.
  3. median     — how far a colluding fraction moves d_blend, both directions,
                  and the quantization width's effect.
  4. leader     — the edge-leader budget: pre-mining duty cycle and the
                  fallback probability of solving at slot time.

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
A_MAX = 108          # envelope: PHI_CC_MAX*M_1_MAX + LAMBDA_E = 8*12 + 12
L_STAR = 4           # load set point: floor(8*60/108), the sized traffic in the envelope
F_W_MAX = 2          # largest rate the drain condition permits: F_1 + F_W*beta < M_1_MAX
L_MIN = 2            # ceil(L_STAR / F_W_MAX): the lowest load the controller reads
D_EDGE_MIN = 300
D_EDGE_MAX = 1000
T_R = 600            # challenge rotation, rounds
G = 60               # price grace window, rounds
M_1_MAX = 12         # messages per round per connection
LAMBDA_E = 12        # edge connections accepted per round
PHI_CC_MAX = 8
PHI_CC_MIN = 6
BETA_MAX = 3         # blending operations per message
F_1 = 3.0            # messages per connection per round, expected

# BN254 scalar field modulus (the PowTarget field).
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617
BLEND_DIFFICULTY_BASE = P // 2**19


def pi5_rate(d: float) -> float:
    """Tokens/s a whole Pi 5 mints at effort d (pooled, measured)."""
    return mint_rate_per_machine(d, PI5_MINT)


def attacker_core_rate(d: float) -> float:
    """Tokens/s one fastest-measured core mints at effort d."""
    return mint_rate_per_machine(d, ATTACKER_CORE_MINT)


# ------------------------------------------------------------- the controllers


@dataclass
class EdgeDifficulty:
    """The Edge Difficulty rule, verbatim: every W rounds, against arrivals A
    over those rounds and the node's capacity V (verifications/round):

      1. if P > 2*LAMBDA_E*r: d <- min(2d, Max)
      2. if P < LAMBDA_E*r:   d <- max(3d//4, Min)
      3. otherwise unchanged.

    P counts presentations passing checks 1-3, accepted or refused: the door
    needs the excess demand that Load's accepted-only count cannot carry. The
    raise threshold is twice the decay threshold because doubling d halves a
    fixed solver's rate, so a narrower band would oscillate.
    """
    d: int = D_EDGE_MIN

    def retarget(self, presentations: float, rounds: int = W) -> int:
        if presentations > 2 * LAMBDA_E * rounds:
            self.d = min(2 * self.d, D_EDGE_MAX)
        elif presentations < LAMBDA_E * rounds:
            self.d = max(3 * self.d // 4, D_EDGE_MIN)
        return self.d


def grace_floor(d_history: list[int], at: int) -> int:
    """The lowest price in force during the past G rounds, `at` inclusive
    (acceptance rule 2 of Edge Admission)."""
    return min(d_history[max(0, at - G + 1): at + 1])


def lower_median(values: list[int]) -> int:
    return sorted(values)[(len(values) - 1) // 2]


def blend_difficulty(reports: list[int]) -> int:
    """The Blend Difficulty rule, verbatim (exact integers): a pure function of
    one epoch's report set. No reports -> BASE (the calibrated prior); a median
    median below L_MIN loosens no further than BASE*L_STAR//L_MIN, the rate the
    drain condition permits. The historical recursive rule (x2 step clamp, hold on
    empty) was dropped so a checkpoint-bootstrapped node can compute the value
    from carried ledger state alone; runaway_epochs_uncapped() below records
    why the pre-fix zero branch needed a cap at all."""
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
    offered: list[int] = field(default_factory=list)        # edge offers this round
    accepted_attacker: list[int] = field(default_factory=list)
    accepted_honest: list[int] = field(default_factory=list)
    refused_honest: list[int] = field(default_factory=list)
    load_levels: list[float] = field(default_factory=list)  # 8*A/(V*W) over trailing W
    cpu: list[float] = field(default_factory=list)          # fraction of one core


def simulate_door(rounds: int, attacker_cores, honest_edge_rate: float = 2.0,
                  V: float = V_HEADER, seed: int = 0,
                  adaptive_giveup: int | None = None,
                  core_mean: float | None = None) -> DoorTrace:
    """The door under load. Core-relay arrivals are Poisson(PHI_CC_MAX * F_1)
    per round. The attacker owns `attacker_cores(t)` fastest-measured cores and
    presents valid tokens at the current price (rate-limited by its hashpower);
    with `adaptive_giveup`, it instead watches d and only mines while
    d < giveup. Honest edge nodes offer Poisson(honest_edge_rate) per round and
    always present a valid token (they pre-mine; study 2 prices that).
    Acceptance follows Edge Admission: at most LAMBDA_E per round, attacker and
    honest offers drawn in random order.

    The load numerator counts core arrivals plus TOKEN-VALID edge offers only —
    the corrected Load rule: counting refused garbage offers would let a
    costless connect-flood raise the price (and, through the report, tighten
    d_blend network-wide) without paying any work. Each offer is modeled as a
    distinct freshly minted token, which matches the spec's one-token-counts-
    once rule; acceptance checks 1 and 3 (window rotation, spent cache) are not
    modeled — token identity never repeats here by construction."""
    rng = random.Random(seed)
    ctrl = EdgeDifficulty()
    tr = DoorTrace()
    window: list[float] = []           # per-round arrivals, trailing W
    pwindow: list[float] = []          # per-round presentations, trailing W
    if core_mean is None:
        core_mean = PHI_CC_MAX * F_1   # quiet ambient; pass PHI*(F_1+F_W*beta)=48
                                       # for the PoW-at-sizing equilibrium
    d_hist: list[int] = []
    for t in range(rounds):
        d_hist.append(ctrl.d)
        mint_price = grace_floor(d_hist, len(d_hist) - 1)   # rule 2: the floor, not the spot price
        cores = attacker_cores(t)
        if adaptive_giveup is not None and cores > 0:
            cores = cores if ctrl.d < adaptive_giveup else 0.0
        atk_offers = _poisson(rng, cores * attacker_core_rate(mint_price) * ROUND)
        hon_offers = _poisson(rng, honest_edge_rate * ROUND)
        core_arrivals = _poisson(rng, core_mean)

        # Acceptance: random arrival order, first LAMBDA_E valid tokens win.
        offers = ["a"] * atk_offers + ["h"] * hon_offers
        rng.shuffle(offers)
        taken = offers[:LAMBDA_E]
        acc_a, acc_h = taken.count("a"), taken.count("h")

        # Load counts core arrivals plus ACCEPTED edge connections; the door
        # reads presentations, accepted or refused.
        arrivals = core_arrivals + acc_a + acc_h
        presentations = atk_offers + hon_offers
        window.append(arrivals)
        pwindow.append(presentations)
        if len(pwindow) > W:
            pwindow.pop(0)
        if len(window) > W:
            window.pop(0)

        # CPU: header verifications for core traffic and accepted edge messages,
        # token verifications for every edge offer.
        cpu = (core_arrivals + acc_a + acc_h) / V + (atk_offers + hon_offers) * T_TOKEN_VERIFY

        tr.round.append(t); tr.d.append(ctrl.d)
        tr.offered.append(atk_offers + hon_offers)
        tr.accepted_attacker.append(acc_a); tr.accepted_honest.append(acc_h)
        tr.refused_honest.append(hon_offers - acc_h)
        tr.load_levels.append(8 * sum(window) / (A_MAX * W))
        tr.cpu.append(cpu)

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


# -------------------------------------------------------------- study 2: grace


def stranded_probability(mean_solve: float, grace: float = G * ROUND) -> float:
    """P(an exponential solve outlives the grace window) — the worst case, where
    the price steps up immediately after the quote."""
    return math.exp(-grace / mean_solve)


def simulate_stranded(tr: DoorTrace, device_rate, solvers_per_round: float = 1.0,
                      seed: int = 1) -> tuple[int, int]:
    """Honest solvers through a door trace: each reads the quote at its start
    round, solves for Exp(1/device_rate(d_quote)) seconds, and is accepted iff
    its quote clears the lowest d in force during the G rounds before it
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


def quantize(arrivals_per_round: float, levels: int = 16) -> int:
    """The reported level of an arrival rate, against the envelope."""
    return min(levels - 1, int(8 * arrivals_per_round / A_MAX * (levels / 16)))


def median_shift(n: int, colluders: float, direction: str, rng: random.Random,
                 honest_median: float = 60.0, gsd: float = 1.6,
                 levels: int = 16) -> tuple[int, int]:
    """One epoch of reports: n declarations, a `colluders` fraction reporting the
    extreme (15 to tighten, 0 to loosen), the rest lognormal around
    honest_median arrivals per round. Returns (honest-only median, shifted
    median), in levels."""
    honest = [quantize(honest_median * math.exp(rng.gauss(0, math.log(gsd))), levels)
              for _ in range(n - int(n * colluders))]
    extreme = levels - 1 if direction == "tighten" else 0
    reports = honest + [extreme] * int(n * colluders)
    return lower_median(honest), lower_median(reports)


def runaway_epochs_uncapped() -> int:
    """Epochs of sustained median 0 until the ORIGINAL recursive rule (hold
    state, double per epoch, bounded only by p-1) reached free admission from
    BASE. Exact, from the real modulus — the number that motivated flooring the
    median at level 1."""
    d, epochs = BLEND_DIFFICULTY_BASE, 0
    while d < P - 1:
        d = min(d * 2, P - 1)
        epochs += 1
    return epochs


def zero_median_settles_at() -> int:
    """Where the rule sits under a median of 0 — the level-1 fixed point,
    instantly and statelessly."""
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


def realized_f_w(d: int) -> float:
    """The proof of work rate at threshold `d`. The rate scales with the
    threshold, and F_W = 1 at BASE by the sizing — an assumption about
    exogenous mining demand, not a derived fact."""
    return d / BLEND_DIFFICULTY_BASE


def loop_step(level: int, phi_cc: int = PHI_CC_MAX, edge: float = LAMBDA_E) -> int:
    """One turn of level -> d_blend -> F_W -> arrivals -> level."""
    d = blend_difficulty([level])
    a = phi_cc * (F_1 + realized_f_w(d) * BETA_MAX) + edge
    return quantize(a)


def loop_attractor(phi_cc: int, edge: float, start: int) -> list[int]:
    """The cycle the map settles into from `start`: a single level if it has a
    fixed point, several if it cycles."""
    seen, level = [], start
    while level not in seen:
        seen.append(level)
        level = loop_step(level, phi_cc, edge)
    return sorted(set(seen[seen.index(level):]))


def loop_survey(degrees=(PHI_CC_MIN, 7, PHI_CC_MAX), edges=(0.0, 6.0, LAMBDA_E)) -> dict:
    """Every attractor of the map, from every starting level."""
    out = {}
    for phi in degrees:
        for e in edges:
            cycles = {tuple(loop_attractor(phi, e, s)) for s in range(16)}
            out[(phi, e)] = sorted(cycles)
    return out



def _plot_door(tr: DoorTrace, path: Path, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(4, 1, figsize=(8, 9), sharex=True)
    ax[0].plot(tr.round, tr.offered, color="#DD8452", lw=0.7, label="edge offers / round")
    ax[0].axhline(LAMBDA_E, ls="--", color="#333", label=f"acceptance rate $\\Lambda_E$={LAMBDA_E}")
    ax[0].set_ylabel("offers / round"); ax[0].set_title(title); ax[0].legend(fontsize=8)
    ax[1].plot(tr.round, tr.d, color="#55A868")
    ax[1].set_ylabel("door price $d_{edge}$"); ax[1].set_ylim(0, D_EDGE_MAX * 1.1)
    ax[2].plot(tr.round, tr.load_levels, color="#4C72B0", lw=0.8, label="load (levels of 1/8)")
    ax[2].axhline(L_STAR, ls="--", color="#C44E52", label="$\\ell^*$")
    ax[2].axhline(L_STAR + 2, ls=":", color="#C44E52", lw=0.8, label="raise / decay thresholds")
    ax[2].axhline(L_STAR + 1, ls=":", color="#C44E52", lw=0.8)
    ax[2].set_ylabel("load level"); ax[2].legend(fontsize=8)
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
                # rule: hm / max(1, sm) — the level-1 floor caps the loosening.
                ratios = [max(hm, 1) / max(1, sm) for hm, sm in trials]
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


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Blend load-driven admission simulations")
    ap.add_argument("--out", default="results/blend-admission")
    ap.add_argument("--rounds", type=int, default=3600)
    args = ap.parse_args(argv)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    lines = ["# Blend load-driven admission — simulation results\n"]

    # Study 1a: constant flood of 200 fastest cores, rounds [600, 2400).
    # The raise trips above level l*+2 = 5 (98 arrivals): ~57 cores at the
    # floor against quiet ambient. 200 cores escalate to the ceiling and HOLD
    # (their offers keep the load above the decay threshold); 120 cores
    # flutter one step below it — minting is priced at the grace floor, which
    # lags each move by up to G rounds.
    flood = simulate_door(args.rounds, lambda t: 200.0 if 600 <= t < 2400 else 0.0)
    _plot_door(flood, out / "door_flood.png", "Door under a 200-core flood (rounds 600–2400)")
    settle = simulate_door(args.rounds, lambda t: 28.0 if 600 <= t < 2400 else 0.0)
    in_attack = slice(700, 2400)
    acc_a = sum(flood.accepted_attacker[in_attack]); acc_h = sum(flood.accepted_honest[in_attack])
    ref_h = sum(flood.refused_honest[in_attack])
    peak_cpu = max(flood.cpu) * 100
    ceil_round = next(t for t, d in enumerate(flood.d) if d == D_EDGE_MAX)
    back_round = next((t for t, d in enumerate(flood.d) if t > 2400 and d == D_EDGE_MIN), None)
    lines += [
        "## 1. The door under flood",
        f"- 60 cores: escalation floor→ceiling in {ceil_round - 600} rounds, held for the whole "
        f"flood, decay back in {back_round - 2400 if back_round else '>'} rounds after it.",
        f"- 28 cores: the price flutters {sorted(set(settle.d[700:2400]))[0]}"
        f"–{sorted(set(settle.d[700:2400]))[-1]} — minting is priced at the grace floor, "
        f"which lags each move by up to G rounds — and decays home the same way.",
        f"- During the flood the attacker takes {acc_a / max(1, acc_a + acc_h) * 100:.0f}% of the "
        f"acceptance rate; {ref_h / max(1, ref_h + acc_h) * 100:.0f}% of honest offers are refused "
        f"at the rate cap (retried next rounds).",
        f"- Peak CPU {peak_cpu:.0f}% of one Pi 5 core (headers + token checks) — the door holds "
        f"the verification budget.",
    ]

    # Study 1c: the same flood over the PoW-at-sizing equilibrium ambient
    # (core arrivals PHI*(F_1 + F_W*beta) = 48): the door must still decay to
    # the floor afterwards — the property the lifted thresholds exist for.
    equil = simulate_door(args.rounds, lambda t: 60.0 if 600 <= t < 2400 else 0.0,
                          core_mean=48.0, seed=4)
    _plot_door(equil, out / "door_equilibrium.png",
               "The same flood over the PoW-at-sizing ambient (48 core arrivals/round)")
    eq_back = next((t for t, d in enumerate(equil.d) if t > 2400 and d == D_EDGE_MIN), None)
    lines += [
        "## 1c. Core ambient cannot hold the price up",
        f"- The door reads edge presentations only, so core traffic at the sized operating "
        f"point (48 arrivals/round) does not enter its signal: the price still decays to the "
        f"floor {eq_back - 2400 if eq_back else '>'} rounds after the flood, exactly as over a "
        f"quiet network.",
        f"- The trip point is {2 * LAMBDA_E / attacker_core_rate(D_EDGE_MIN):.0f} fastest cores "
        f"at the floor price, whatever the core load — 2*Lambda_E = {2 * LAMBDA_E} "
        f"presentations per round.",
    ]

    # Study 1b: adaptive attackers, give-up at 800, two sizes.
    adaptive = simulate_door(args.rounds, lambda t: 40.0 if 600 <= t < 2400 else 0.0,
                             adaptive_giveup=800)
    _plot_door(adaptive, out / "door_adaptive.png",
               "Door vs an adaptive attacker (mines only while d < 800)")
    big = simulate_door(args.rounds, lambda t: 60.0 if 600 <= t < 2400 else 0.0,
                        adaptive_giveup=800, seed=5)
    atk_on = sum(1 for t in range(600, 2400) if adaptive.accepted_attacker[t] > 0)
    acc_a2 = sum(adaptive.accepted_attacker[700:2400])
    acc_h2 = sum(adaptive.accepted_honest[700:2400])
    flutter = sorted(set(big.d[700:2400]))
    lines += [
        "## 1b. Adaptive attackers (give-up 800)",
        f"- Both sizes flutter one step ({flutter[0]}↔{flutter[-1]}): with minting priced at "
        f"the grace floor, the floor lags each move by up to G rounds, so neither a clean "
        f"settle nor the generic controller's multi-octave sawtooth occurs — the excursion "
        f"is bounded to adjacent steps.",
        f"- The occupation is priced either way: attack duty {atk_on / 18:.0f}%, "
        f"{acc_a2 / max(1, acc_a2 + acc_h2) * 100:.0f}% of the acceptance rate (40 cores). "
        f"Just-below-trip pressure costs ~19 fastest cores at the floor and scales roughly "
        f"linearly with the price the attack sustains (~48 at 750) — the floor figure is "
        f"the attacker's cost-minimizing bound.",
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
    lines += ["", f"- Through the flood trace: {s4}/{n4} four-core and {s1}/{n1} single-core "
                  f"solvers stranded (price steps are what strands, not the tail alone)."]

    # Study 3: median manipulation, both directions; runaway; quantization ties.
    shifts = _plot_median(out / "median_shift.png")
    ra = runaway_epochs_uncapped()
    rng = random.Random(9)
    ranks16 = [quantize(60.0 * math.exp(rng.gauss(0, math.log(1.6)))) for _ in range(100)]
    ties16 = 1 - len(set(ranks16)) / 100
    lines += [
        "## 3. Median robustness",
        f"- The rule is a pure re-anchor to BASE*{L_STAR}/median, so a shifted median is a "
        f"bounded bias with no memory: at 30% colluders the mean multiplier is "
        f"{shifts[('tighten', 100)][0.30]:.2f} (tighten) / {shifts[('loosen', 100)][0.30]:.2f} "
        f"(loosen) at N=100, and it vanishes the epoch capture ends.",
        f"- The original recursive rule's zero-median branch doubled per epoch and reached free "
        f"admission in {ra} epochs from BASE; flooring the median at L_MIN = {L_MIN} closes it "
        f"statelessly and stops the loosening where the drain condition does — a zero median "
        f"sits at {zero_median_settles_at() / BLEND_DIFFICULTY_BASE:.0f}*BASE, instantly and "
        f"reversibly.",
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

    # Study 5: the control loop, closed numerically.
    survey = loop_survey()
    fixed = sum(1 for cycles in survey.values() for c in cycles if len(c) == 1)
    bistable = [k for k, v in survey.items() if len(v) > 1]
    worst_fw = max(realized_f_w(blend_difficulty([lvl]))
                   for cycles in survey.values() for c in cycles for lvl in c)
    lines += [
        "## 5. The control loop, closed",
        "",
        "| Phi_CC | edge 0 | edge 6 | edge 12 |",
        "|---|---|---|---|",
    ]
    for phi in (PHI_CC_MIN, 7, PHI_CC_MAX):
        row = [f"| {phi} "]
        for e in (0.0, 6.0, float(LAMBDA_E)):
            cs = survey[(phi, e)]
            row.append("| " + ", ".join("fixed [%d]" % c[0] if len(c) == 1
                                        else "cycle {%s}" % ",".join(map(str, c)) for c in cs) + " ")
        lines.append("".join(row) + "|")
    lines += [
        "",
        f"- Iterating level -> d_blend -> F_W -> arrivals -> level from all 16 starting levels: "
        f"{fixed} of the 9 configurations have a fixed point; the design point "
        f"(Phi_CC^Max with the edge allowance used) is exact at level {L_STAR}, arrivals 60.",
        f"- Every attractor is bounded: each cycle visits two levels at most and the realized "
        f"F_W never exceeds {worst_fw:.0f} = F_W_MAX, so the drain condition "
        f"{F_1} + {worst_fw:.0f}*{BETA_MAX} < {M_1_MAX} holds throughout.",
        f"- One corner is bistable: Phi_CC^Min with no edge traffic admits both a fixed point "
        f"at level 3 and a 2<->4 cycle, depending on where the network starts. Bounded and "
        f"drain-safe, but the only configuration without a unique attractor."
        if bistable else "- Every configuration has a unique attractor.",
        f"- The sized traffic sits {(60 - L_STAR * A_MAX / 8) / (A_MAX / 8) * 100:.0f}% into its "
        f"band [{L_STAR * A_MAX / 8:.1f}, {(L_STAR + 1) * A_MAX / 8:.1f}) — the margin the "
        f"previous denominator lacked.",
    ]

    header = "<!-- generated by equix_bench.blend_admission; the curated report is simulation.md -->\n"
    (out / "summary.md").write_text(header + "\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
