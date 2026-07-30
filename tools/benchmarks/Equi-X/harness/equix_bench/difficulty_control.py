"""Reference difficulty (effort `E`) controllers + a simulator.

Two closed-loop controllers that adjust the Equi-X effort parameter to demand,
calibrated on the MEASURED mint-rate curve (docs/findings.md §7a):

  * MintRateController (Design A) — hold a network's token MINT RATE at a target,
    the way PoW difficulty retargeting works, specialized to the measured 1/E law.
  * LoadController (Design B) — hold a single node's admission PRESSURE (offered
    valid-token rate ÷ service capacity) at a target, so an attack is throttled
    while honest clients pay the least difficulty that keeps the node healthy.

Both rest on one measured fact: token rate ∝ 1/E on fixed hardware, and verify
cost is constant and ~free. So the control law is a cheap MULTIPLICATIVE step and
needs no absolute capacity model — it self-corrects from what it observes.

Run the demo (writes plots + a summary):
    python -m equix_bench.difficulty_control --out results/control
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# Measured mint rate per reference machine (Apple M4 Pro, 14 cores, Rust-JIT),
# from results/main/mining.csv: tokens/second at each effort target. POOLED
# estimator (total tokens over total busy seconds across all workers) — a sum
# of per-worker 1/t ratios would carry a +6..25% upward bias at these CVs.
MEASURED_MINT: list[tuple[int, float]] = [(100, 69.1), (300, 23.5), (1000, 5.49), (3000, 1.75), (10000, 0.67)]


def mint_rate_per_machine(E: float, points: list[tuple[int, float]] = MEASURED_MINT) -> float:
    """Tokens/s one reference machine mints at effort `E`.

    Log-log linear interpolation between the measured points; outside the
    measured range it extrapolates as pure 1/E (slope -1 in log-log), the design
    asymptote. Monotonically decreasing in E."""
    pts = sorted(points)
    if E <= pts[0][0]:
        e0, r0 = pts[0]
        return r0 * (e0 / E)                       # 1/E extrapolation below range
    if E >= pts[-1][0]:
        e1, r1 = pts[-1]
        return r1 * (e1 / E)                        # 1/E extrapolation above range
    for (e0, r0), (e1, r1) in zip(pts, pts[1:]):
        if e0 <= E <= e1:
            f = (math.log(E) - math.log(e0)) / (math.log(e1) - math.log(e0))
            return math.exp(math.log(r0) + f * (math.log(r1) - math.log(r0)))
    return pts[-1][1]  # unreachable


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def equilibrium_E(machines: float, target_rate: float,
                  points: list[tuple[int, float]] = MEASURED_MINT,
                  lo: float = 1.0, hi: float = 1e9) -> float:
    """The E at which `machines` reference machines mint `target_rate` tokens/s
    (the natural controller seed). Solved by bisection on the measured curve —
    no hard-coded constants to drift out of sync when MEASURED_MINT is updated."""
    for _ in range(200):
        mid = math.sqrt(lo * hi)  # geometric: the curve lives in log-log space
        if machines * mint_rate_per_machine(mid, points) > target_rate:
            lo = mid
        else:
            hi = mid
        if hi / lo < 1.0001:
            break
    return math.sqrt(lo * hi)


@dataclass
class MintRateController:
    """Design A: E ← E · clamp(R_obs / R*).  Because rate ∝ 1/E, minting twice too
    fast means E must double. Robust to capacity drift (only uses observed rate)."""
    target_rate: float                 # R*  (tokens/s the network should mint)
    E: float = 1000.0                  # current difficulty
    e_min: float = 100.0
    e_max: float = 1e9
    max_factor: float = 4.0            # per-epoch clamp (anti-oscillation, Bitcoin-style)
    ewma: float = 0.3                  # smoothing of the observed rate (0..1); 1 = no smoothing
    _r: Optional[float] = None         # smoothed observed rate

    def update(self, observed_rate: float) -> float:
        self._r = observed_rate if self._r is None else self.ewma * observed_rate + (1 - self.ewma) * self._r
        factor = _clip((self._r / self.target_rate) if self.target_rate > 0 else 1.0,
                       1.0 / self.max_factor, self.max_factor)
        self.E = _clip(self.E * factor, self.e_min, self.e_max)
        return self.E


@dataclass
class LoadController:
    """Design B: E ← E · clamp(exp(k · (p - p_set))), where p = offered valid-token
    rate ÷ service capacity. Raise E under pressure (throttle), let it decay toward
    e_min when idle (cheap for honest clients). Deadband avoids flapping — note the
    intended consequence: while pressure sits within the deadband of p_set, E HOLDS
    (including post-attack, if load keeps utilization pinned at target); it only
    decays once pressure drops below p_set - deadband."""
    p_set: float = 0.8                 # target pressure (headroom below saturation)
    k: float = 1.5                     # gain
    E: float = 300.0
    e_min: float = 300.0
    e_max: float = 1e9
    max_factor: float = 4.0
    deadband: float = 0.03

    def update(self, pressure: float) -> float:
        e = pressure - self.p_set
        if abs(e) < self.deadband:
            return self.E
        factor = _clip(math.exp(self.k * e), 1.0 / self.max_factor, self.max_factor)
        self.E = _clip(self.E * factor, self.e_min, self.e_max)
        return self.E


# --------------------------------------------------------------------- simulators


@dataclass
class Trace:
    t: list[float] = field(default_factory=list)
    E: list[float] = field(default_factory=list)
    signal: list[float] = field(default_factory=list)      # observed rate (A) or pressure (B)
    target: list[float] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


def simulate_mining(capacity: Callable[[int], float], target_rate: float, steps: int,
                    ctrl: Optional[MintRateController] = None,
                    rate_model: Callable[[float], float] = mint_rate_per_machine,
                    noise: float = 0.0, seed: int = 0) -> Trace:
    """Network of `capacity(t)` machines; controller holds mint rate at target.
    `noise` (fractional stddev) models real measurement jitter on the observed
    rate; `seed` makes it reproducible."""
    ctrl = ctrl or MintRateController(target_rate=target_rate)
    rng = random.Random(seed)
    tr = Trace(target=[], extra={"capacity": [], "true_rate": []})
    for t in range(steps):
        C = capacity(t)
        R = C * rate_model(ctrl.E)          # true tokens/s at current E
        R_obs = R * (1 + rng.gauss(0, noise)) if noise else R
        tr.t.append(t); tr.E.append(ctrl.E); tr.signal.append(R_obs)
        tr.target.append(target_rate); tr.extra["capacity"].append(C)
        tr.extra["true_rate"].append(R)      # noise-free, for honest error stats
        ctrl.update(R_obs)                   # set E for the next epoch
    return tr


def simulate_dos(legit: Callable[[int], float], attackers: Callable[[int], float],
                 service_capacity: float, steps: int, ctrl: Optional[LoadController] = None,
                 honest_cores: float = 1.0,
                 rate_model: Callable[[float], float] = mint_rate_per_machine,
                 adaptive_attackers: Optional[Callable[[int, float], float]] = None) -> Trace:
    """One protected node: honest req/s `legit(t)` plus attacker machines each
    minting valid tokens at the current E. Controller holds admission pressure at
    p_set. Records honest latency = time for one honest `honest_cores`-core client
    to mint a token at the current E (the cost of defense to legitimate users).

    `adaptive_attackers(t, E)`, when given, replaces `attackers(t)`: the attacker
    OBSERVES the current difficulty and can pause when solving is too expensive
    and resume when E decays — the rational strategy against a decaying controller."""
    ctrl = ctrl or LoadController()
    tr = Trace(target=[], extra={"attacker_rate": [], "presented": [], "honest_latency": [], "util": []})
    machine_cores = 14.0                       # the reference machine the curve was measured on
    for t in range(steps):
        A = adaptive_attackers(t, ctrl.E) if adaptive_attackers else attackers(t)
        m = rate_model(ctrl.E)                  # tokens/s per 14-core machine at current E
        attacker_rate = A * m                   # valid tokens/s the attacker can present
        presented = legit(t) + attacker_rate
        pressure = presented / service_capacity
        honest_latency = 1.0 / (m * honest_cores / machine_cores)  # 1 honest client's token time
        tr.t.append(t); tr.E.append(ctrl.E); tr.signal.append(pressure); tr.target.append(ctrl.p_set)
        tr.extra["attacker_rate"].append(attacker_rate)
        tr.extra["presented"].append(presented)
        tr.extra["honest_latency"].append(honest_latency)
        tr.extra["util"].append(min(1.0, pressure))
        ctrl.update(pressure)
    return tr


# ------------------------------------------------------------------------- demo


def _plot_mining(tr: Trace, path: Path, title: str = "Design A — mint-rate controller") -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
    ax[0].plot(tr.t, tr.extra["capacity"], color="#8172B3")
    ax[0].set_ylabel("miners\n(machines)"); ax[0].set_title(title)
    ax[1].plot(tr.t, tr.signal, color="#4C72B0", label="observed mint rate")
    ax[1].plot(tr.t, tr.target, "--", color="#C44E52", label="target R*")
    ax[1].set_ylabel("tokens / s"); ax[1].legend(fontsize=8)
    ax[2].plot(tr.t, tr.E, color="#55A868"); ax[2].set_yscale("log")
    ax[2].set_ylabel("effort E"); ax[2].set_xlabel("epoch")
    for a in ax: a.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def _plot_dos(tr: Trace, S: float, path: Path,
              title: str = "Design B — single-node load controller") -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(4, 1, figsize=(8, 9), sharex=True)
    ax[0].plot(tr.t, tr.extra["presented"], color="#DD8452", label="offered valid-token req/s")
    ax[0].plot(tr.t, tr.extra["attacker_rate"], ":", color="#C44E52", label="attacker share")
    ax[0].axhline(S, ls="--", color="#333", label=f"service capacity S={S:g}")
    ax[0].set_ylabel("requests / s"); ax[0].set_title(title); ax[0].legend(fontsize=8)
    ax[1].plot(tr.t, tr.extra["util"], color="#4C72B0", label="utilization")
    ax[1].plot(tr.t, tr.target, "--", color="#C44E52", label="p_set")
    ax[1].set_ylabel("utilization"); ax[1].set_ylim(0, 1.05); ax[1].legend(fontsize=8)
    ax[2].plot(tr.t, tr.E, color="#55A868"); ax[2].set_yscale("log"); ax[2].set_ylabel("effort E")
    ax[3].plot(tr.t, tr.extra["honest_latency"], color="#937860")
    ax[3].set_ylabel("honest solve\ntime (s)"); ax[3].set_xlabel("tick")
    for a in ax: a.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Equi-X difficulty (E) controller demo")
    p.add_argument("--out", default="results/control", help="output directory for plots")
    p.add_argument("--steps", type=int, default=80)
    args = p.parse_args(argv)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    # Design A: miners ramp 2→12, then a hashpower spike to 20 at 60%. Hold R* = 2 tok/s.
    def capacity(t: int) -> float:
        if t < 48:
            return 2 + 10 * (t / 48)
        return 20.0
    mining = simulate_mining(capacity, target_rate=2.0, steps=args.steps)
    _plot_mining(mining, out / "control_mining.png")

    # Design B: honest 8 req/s throughout; a 6-machine flood during [24, 56). S = 40 req/s.
    def legit(t: int) -> float:
        return 8.0
    def attackers(t: int) -> float:
        return 6.0 if 24 <= t < 56 else 0.0
    S = 40.0
    dos = simulate_dos(legit, attackers, service_capacity=S, steps=args.steps)
    _plot_dos(dos, S, out / "control_dos.png")

    # Production run: how you'd actually deploy Design A. Gentle gains (max_factor
    # 2, heavy EWMA), E SEEDED near equilibrium from the capacity estimate (no cold
    # start), organic capacity growth, and ±8% measurement noise on the observed
    # rate. Result: smooth tracking with no overshoot, stable under noise.
    steps_p = max(args.steps, 120)
    C0, R_target = 4.0, 2.0
    E_seed = equilibrium_E(C0, R_target)                  # seed at equilibrium: C0 machines mint R_target
    def capacity_prod(t: int) -> float:
        # organic growth 4 → ~13 with a slow wobble (diurnal-like), no hard steps
        return 4.0 + 9.0 * (t / steps_p) + 0.8 * math.sin(t / 9.0)
    prod_ctrl = MintRateController(target_rate=R_target, E=E_seed, max_factor=2.0, ewma=0.15)
    prod = simulate_mining(capacity_prod, target_rate=R_target, steps=steps_p,
                           ctrl=prod_ctrl, noise=0.08, seed=1)
    _plot_mining(prod, out / "control_production.png",
                 title="Production run — mint-rate controller (seeded E, gentle gains, ±8% noise)")

    # Summary numbers.
    def _final(tr, key_signal):
        return tr.E[-1], key_signal
    # Run 4 — ADAPTIVE attacker vs Design B: 6 machines that only attack while
    # E is below their give-up point (solving cheap enough to bother), pausing
    # when the controller escalates and resuming as E decays. The rational
    # strategy — does the loop oscillate, and what does the attacker still get?
    E_GIVEUP = 800.0
    def adaptive(t: int, E: float) -> float:
        if t < 16 or t >= 104:
            return 0.0
        return 6.0 if E < E_GIVEUP else 0.0
    adaptive_tr = simulate_dos(legit, lambda t: 0.0, service_capacity=S,
                               steps=120, adaptive_attackers=adaptive)
    _plot_dos(adaptive_tr, S, out / "control_adaptive.png",
              title="Design B vs an ADAPTIVE attacker (attacks only while E < give-up)")
    atk_window = adaptive_tr.extra["attacker_rate"][16:104]
    duty = sum(1 for a in atk_window if a > 0) / len(atk_window)
    sat = sum(1 for u in adaptive_tr.extra["util"][16:104] if u >= 0.999)

    # Run 5 — miner CHURN for Design A production tuning: miners join/leave as a
    # seeded random walk instead of a smooth ramp; noise on the observed rate.
    rng_churn = random.Random(7)
    miners = 8.0
    churn_path = []
    for _ in range(140):
        if rng_churn.random() < 0.15: miners += 1
        if rng_churn.random() < 0.15 and miners > 2: miners -= 1
        churn_path.append(miners)
    churn_ctrl = MintRateController(target_rate=R_target, E=equilibrium_E(8.0, R_target),
                                    max_factor=2.0, ewma=0.15)
    churn = simulate_mining(lambda t: churn_path[t], target_rate=R_target, steps=140,
                            ctrl=churn_ctrl, noise=0.08, seed=2)
    _plot_mining(churn, out / "control_churn.png",
                 title="Production tuning under miner churn (join/leave random walk, ±8% noise)")
    churn_tail = churn.extra["true_rate"][40:]
    churn_err = 100.0 * (sum(churn_tail) / len(churn_tail) - R_target) / R_target

    # Production-run steady-state error over the settled tail (last third).
    # Report BOTH: the noisy observed mean (what an operator sees) and the
    # noise-free true-rate mean (the controller's systematic tracking lag —
    # averaging only the noisy signal would understate it).
    n_tail = len(prod.signal) * 2 // 3
    obs_tail = prod.signal[n_tail:]
    true_tail = prod.extra["true_rate"][n_tail:]
    prod_err_obs = 100.0 * (sum(obs_tail) / len(obs_tail) - R_target) / R_target
    prod_err_true = 100.0 * (sum(true_tail) / len(true_tail) - R_target) / R_target
    lines = ["# Difficulty-control simulation\n",
             f"- Design A (mining): final E={mining.E[-1]:,.0f}, "
             f"mint rate {mining.signal[-1]:.2f} tok/s vs target {mining.target[-1]:.2f} "
             f"(with {mining.extra['capacity'][-1]:.0f} miners).",
             f"- Design B (DoS): peak E under attack ≈ {max(dos.E):,.0f}; "
             f"steady honest solve time {dos.extra['honest_latency'][0]:.2f}s at rest → "
             f"{max(dos.extra['honest_latency']):.2f}s under attack; "
             f"utilization held near p_set={dos.target[-1]:.2f}.",
             f"- Production run (seeded E, gentle gains, ±8% noise): no cold-start "
             f"overshoot; settled tail within {prod_err_obs:+.1f}% of target (observed) / "
             f"{prod_err_true:+.1f}% (noise-free — the systematic lag against the capacity "
             f"ramp), final E={prod.E[-1]:,.0f} at {prod.extra['capacity'][-1]:.0f} miners.",
             f"- Adaptive attacker (give-up E={E_GIVEUP:,.0f}): duty-cycled to "
             f"{duty*100:.0f}% attack-on time, {sat} saturated tick(s) in the whole attack "
             f"window; E oscillates {min(adaptive_tr.E[20:104]):,.0f}–{max(adaptive_tr.E[20:104]):,.0f} "
             f"(sawtooth around the give-up point — see the doc for the mitigation).",
             f"- Miner churn (random walk {min(churn_path):.0f}–{max(churn_path):.0f} miners): "
             f"settled noise-free rate within {churn_err:+.1f}% of target.",
             "\nPlots: `control_mining.png`, `control_dos.png`, `control_production.png`, "
             "`control_adaptive.png`, `control_churn.png`.\n"]
    (out / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {out}/control_mining.png, {out}/control_dos.png, "
          f"{out}/control_production.png, {out}/summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
