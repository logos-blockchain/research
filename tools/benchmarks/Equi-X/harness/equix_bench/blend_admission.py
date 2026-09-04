"""Simulations of the Blend load-driven admission mechanisms, as specified.

Simulates the exact rules of `blend-protocol.md` 1.7.0 (logos-lips branch
`docs/blend-load-driven-admission`) against the measured Equi-X curves:

  * EdgeDifficulty  — the per-node door controller (`Edge Difficulty`): retarget
    every W rounds, x2 up / x3/4 down against the load levels, bounds
    [d_edge_min, d_edge_max].
  * blend_difficulty — the consensus controller (`Blend Difficulty`): the lower
    median of quantized load reports, d = BASE * l_star // median, clamped to a
    x2 step and below the field modulus. Exact integers, real BN254 modulus.

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
# Pi 5: the target machine, whole machine (4 workers). 285HX: the fastest
# measured solver, per core (machine / 24 workers) — the marginal attacker.
PI5_MINT: list[tuple[int, float]] = [(100, 4.4530), (300, 1.3950), (1000, 0.4243), (3000, 0.1715)]
ATTACKER_CORE_MINT: list[tuple[int, float]] = [(100, 3.5514), (300, 1.2694), (1000, 0.3868), (3000, 0.1114)]

# Public header verification rate, one Pi 5 core (tools/benchmarks/blend-header-verification).
V_HEADER = 157.0
# Equi-X verify, cold challenge, Pi 5, C implementation (findings.md section 3).
T_TOKEN_VERIFY = 54.7e-6

# ------------------------------------------------- spec constants (1.7.0)
ROUND = 1.0          # seconds per round
W = 30               # observation window, rounds
L_STAR = 4           # load set point, in eighths
D_EDGE_MIN = 300
D_EDGE_MAX = 1000
T_R = 600            # challenge rotation, rounds
G = 60               # price grace window, rounds
LAMBDA_E = 12        # edge connections accepted per round
PHI_CC_MAX = 8
F_1 = 3.0            # messages per connection per round, expected
E_EPOCH = 648_000    # rounds per epoch

# BN254 scalar field modulus (the PowTarget field).
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617
BLEND_DIFFICULTY_BASE = P // 2**19
BLEND_MAX_STEP = 2


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

      1. if 8*A > (l*+1)*V*W: d <- min(2d, Max)
      2. if 8*A < (l*-1)*V*W: d <- max(3d//4, Min)
      3. otherwise unchanged.
    """
    d: int = D_EDGE_MIN
    history: list[int] = field(default_factory=list)   # d per round, for min-over-G

    def note_round(self) -> None:
        self.history.append(self.d)

    def retarget(self, arrivals: float, V: float) -> int:
        if 8 * arrivals > (L_STAR + 1) * V * W:
            self.d = min(2 * self.d, D_EDGE_MAX)
        elif 8 * arrivals < (L_STAR - 1) * V * W:
            self.d = max(3 * self.d // 4, D_EDGE_MIN)
        return self.d

    def floor_over_grace(self) -> int:
        """The lowest value in force during the past G rounds (acceptance rule 3)."""
        window = self.history[-G:] if self.history else [self.d]
        return min(window)


def lower_median(values: list[int]) -> int:
    return sorted(values)[(len(values) - 1) // 2]


def blend_difficulty(reports: list[int], previous: int) -> int:
    """One epoch step of the Blend Difficulty rule, verbatim (exact integers).
    The loosening is capped at the level-1 fixed point L_STAR*BASE — the fix the
    runaway study below motivated; without it a sustained median of 0 doubles
    every epoch and reaches free admission (every ticket below p-1) in 19
    epochs."""
    if not reports:
        return previous
    load = lower_median(reports)
    lo = previous // BLEND_MAX_STEP
    hi = min(previous * BLEND_MAX_STEP, L_STAR * BLEND_DIFFICULTY_BASE)
    if load == 0:
        return hi
    return max(lo, min((BLEND_DIFFICULTY_BASE * L_STAR) // load, hi))


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
                  adaptive_giveup: int | None = None) -> DoorTrace:
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
    d_blend network-wide) without paying any work."""
    rng = random.Random(seed)
    ctrl = EdgeDifficulty()
    tr = DoorTrace()
    window: list[float] = []           # per-round arrivals, trailing W
    core_mean = PHI_CC_MAX * F_1
    for t in range(rounds):
        cores = attacker_cores(t)
        if adaptive_giveup is not None and cores > 0:
            cores = cores if ctrl.d < adaptive_giveup else 0.0
        atk_offers = _poisson(rng, cores * attacker_core_rate(ctrl.d) * ROUND)
        hon_offers = _poisson(rng, honest_edge_rate * ROUND)
        core_arrivals = _poisson(rng, core_mean)

        # Acceptance: random arrival order, first LAMBDA_E valid tokens win.
        offers = ["a"] * atk_offers + ["h"] * hon_offers
        rng.shuffle(offers)
        taken = offers[:LAMBDA_E]
        acc_a, acc_h = taken.count("a"), taken.count("h")

        arrivals = core_arrivals + atk_offers + hon_offers   # offered demand (Load)
        window.append(arrivals)
        if len(window) > W:
            window.pop(0)

        # CPU: header verifications for core traffic and accepted edge messages,
        # token verifications for every edge offer.
        cpu = (core_arrivals + acc_a + acc_h) / V + (atk_offers + hon_offers) * T_TOKEN_VERIFY

        tr.round.append(t); tr.d.append(ctrl.d)
        tr.offered.append(atk_offers + hon_offers)
        tr.accepted_attacker.append(acc_a); tr.accepted_honest.append(acc_h)
        tr.refused_honest.append(hon_offers - acc_h)
        tr.load_levels.append(8 * sum(window) / (V * W))
        tr.cpu.append(cpu)

        ctrl.note_round()
        if (t + 1) % W == 0:
            ctrl.retarget(sum(window), V)
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
            floor = min(tr.d[max(0, arrive - G): arrive + 1])
            total += 1
            if quote < floor:
                stranded += 1
    return stranded, total


# ------------------------------------------------------------- study 3: median


def quantize(load: float, levels: int = 16) -> int:
    return min(levels - 1, int(8 * load * (levels / 16)))


def median_shift(n: int, colluders: float, direction: str, rng: random.Random,
                 honest_median: float = 0.5, gsd: float = 1.6,
                 levels: int = 16) -> tuple[int, int]:
    """One epoch of reports: n declarations, a `colluders` fraction reporting the
    extreme (15 to tighten, 0 to loosen), the rest lognormal around
    honest_median. Returns (honest-only median, shifted median), in levels."""
    honest = [quantize(honest_median * math.exp(rng.gauss(0, math.log(gsd))), levels)
              for _ in range(n - int(n * colluders))]
    extreme = levels - 1 if direction == "tighten" else 0
    reports = honest + [extreme] * int(n * colluders)
    return lower_median(honest), lower_median(reports)


def runaway_epochs_uncapped() -> int:
    """Epochs of sustained median 0 until an UNCAPPED loosening (hi bounded only
    by p-1, the rule before the fix) reaches free admission from BASE. Exact,
    from the real modulus — the number that motivated the level-1 cap."""
    d, epochs = BLEND_DIFFICULTY_BASE, 0
    while d < P - 1:
        d = min(d * BLEND_MAX_STEP, P - 1)
        epochs += 1
    return epochs


def zero_median_settles_at() -> int:
    """Where the capped rule settles under a sustained median of 0."""
    d = BLEND_DIFFICULTY_BASE
    for _ in range(30):
        d = blend_difficulty([0], d)
    return d


# ------------------------------------------------------------- study 4: leader


def erlang3_tail(mean_token: float, budget: float) -> float:
    """P(sum of three exponential token solves exceeds the budget)."""
    lam = 1.0 / mean_token
    x = lam * budget
    return math.exp(-x) * (1 + x + x * x / 2)


def premine_duty(d: int, tokens: int = 3, rotation: float = T_R * ROUND) -> float:
    """Fraction of a Pi 5 spent keeping `tokens` fresh across a rotation."""
    return tokens * (1.0 / pi5_rate(d)) / rotation


# --------------------------------------------------------------------- reports


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
    ax[2].axhline(L_STAR + 1, ls=":", color="#C44E52", lw=0.8)
    ax[2].axhline(L_STAR - 1, ls=":", color="#C44E52", lw=0.8)
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
                # d_blend multiplier vs the honest value: 4/median (level 0 -> the
                # x2-per-epoch runaway, plotted at the plain x2 step).
                ratios = []
                for hm, sm in trials:
                    hm, sm = max(hm, 1), sm
                    ratios.append(2.0 if sm == 0 else hm / sm)
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

    # Study 1a: constant flood of 120 fastest cores, rounds [600, 2400).
    # The trip point is ~57 cores at the floor (8*(26+c*1.269) > 5*157 needs
    # c > 56.8); 120 cores escalate floor->600->ceiling in two retargets and
    # then HOLD there: at 1000 their offers land the load inside the deadband,
    # so the price neither decays under fire nor oscillates.
    flood = simulate_door(args.rounds, lambda t: 120.0 if 600 <= t < 2400 else 0.0)
    _plot_door(flood, out / "door_flood.png", "Door under a 120-core flood (rounds 600–2400)")
    in_attack = slice(700, 2400)
    acc_a = sum(flood.accepted_attacker[in_attack]); acc_h = sum(flood.accepted_honest[in_attack])
    ref_h = sum(flood.refused_honest[in_attack])
    peak_cpu = max(flood.cpu) * 100
    ceil_round = next(t for t, d in enumerate(flood.d) if d == D_EDGE_MAX)
    back_round = next((t for t, d in enumerate(flood.d) if t > 2400 and d == D_EDGE_MIN), None)
    lines += [
        "## 1. The door under flood",
        f"- Escalation floor→ceiling in {ceil_round - 600} rounds; decay back in "
        f"{back_round - 2400 if back_round else '>'} rounds after the flood.",
        f"- During the flood the attacker takes {acc_a / max(1, acc_a + acc_h) * 100:.0f}% of the "
        f"acceptance rate; {ref_h / max(1, ref_h + acc_h) * 100:.0f}% of honest offers are refused "
        f"at the rate cap (retried next rounds).",
        f"- Peak CPU {peak_cpu:.0f}% of one Pi 5 core (headers + token checks) — the door holds "
        f"the verification budget.",
    ]

    # Study 1b: adaptive attacker, give-up at 800.
    adaptive = simulate_door(args.rounds, lambda t: 120.0 if 600 <= t < 2400 else 0.0,
                             adaptive_giveup=800)
    _plot_door(adaptive, out / "door_adaptive.png",
               "Door vs an adaptive attacker (mines only while d < 800)")
    atk_on = sum(1 for t in range(600, 2400) if adaptive.accepted_attacker[t] > 0)
    sat = sum(1 for t in range(600, 2400) if adaptive.load_levels[t] > L_STAR + 1)
    acc_a2 = sum(adaptive.accepted_attacker[700:2400])
    acc_h2 = sum(adaptive.accepted_honest[700:2400])
    lines += [
        "## 1b. Adaptive attacker (give-up 800)",
        f"- No sawtooth: the price settles at {adaptive.d[1500]} — the deadband holds the "
        f"one value just below the give-up, so the generic controller's oscillation "
        f"(research run 4) does not occur under the specified integer rule.",
        f"- The equilibrium is a stable, priced occupation instead: attack duty "
        f"{atk_on / 18:.0f}% of the window, {acc_a2 / max(1, acc_a2 + acc_h2) * 100:.0f}% of the "
        f"acceptance rate, {sat}/1800 rounds above the upper deadband. The floor on that "
        f"occupation is the work itself: just-below-trip pressure costs ~57 fastest cores "
        f"at any price the attacker settles at.",
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
    ranks16 = [quantize(0.5 * math.exp(rng.gauss(0, math.log(1.6)))) for _ in range(100)]
    ties16 = 1 - len(set(ranks16)) / 100
    lines += [
        "## 3. Median robustness",
        f"- Below half the reporters, the per-epoch multiplier stays within the x2 clamp and "
        f"re-anchors to BASE*4/median: at 30% colluders the mean multiplier is "
        f"{shifts[('tighten', 100)][0.30]:.2f} (tighten) / {shifts[('loosen', 100)][0.30]:.2f} "
        f"(loosen) at N=100.",
        f"- The zero-median branch, uncapped, doubles per epoch and reaches free admission in "
        f"{ra} epochs from BASE — which is why the rule caps the loosening at the level-1 "
        f"fixed point: under a sustained median of 0 it now settles at 4*BASE "
        f"({zero_median_settles_at() // BLEND_DIFFICULTY_BASE}x BASE) and stays.",
        f"- Sixteen levels leave {ties16 * 100:.0f}% of 100 heterogeneous reporters sharing a "
        f"level — the targeting oracle sees buckets, not a ranking.",
    ]

    # Study 4: the edge-leader budget.
    lines += ["## 4. Edge leader", "",
              "| d | pre-mine duty (3 tokens / rotation) | P(3 solves > 15 s) | P(> 30 s) |",
              "|---|---|---|---|"]
    for d in (D_EDGE_MIN, D_EDGE_MAX):
        mean = 1.0 / pi5_rate(d)
        lines.append(f"| {d} | {premine_duty(d) * 100:.2f}% | {erlang3_tail(mean, 15) * 100:.2f}% "
                     f"| {erlang3_tail(mean, 30) * 100:.3f}% |")
    lines += ["", "- Pre-mining to the ceiling costs ~"
              f"{premine_duty(D_EDGE_MAX) * 100:.1f}% of a Pi 5 and removes the slot-time risk; "
              "solving at slot time at the ceiling misses the 15 s traversal budget "
              f"{erlang3_tail(1 / pi5_rate(D_EDGE_MAX), 15) * 100:.1f}% of the time."]

    (out / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
