"""Phase K.1: settlement after a wait of T slots, under both delay models (SLOTS.md K.1).

    python scripts/k1_settle.py      # needs runs/a1 and runs/b2; writes runs/k1/*.csv

A wait of T slots accepts the prefix up to a target's slot once T slots have passed since it
(src/finality_sim/slots.py).

random.csv: the shortest wait at 1e-3, 1e-6 and 1e-9 for B2's shares, on testnet's Blend and the
specification's, in B4's model of the private race with a premined lead at A1's growth g. Beside
it the depth rule's depth (B5's closed form), its time on the report's clock, 30/((1 − α)g)
seconds a block, and on the model's own clock, 1/h, with h = (1 − α)·g·λ and λ = −ln(1 − f).

worst.csv: the shortest wait whose worst-case bound (slots.worst_needed) is at most 1e-6 and
1e-9, for B2's shares and delays, from B2's upper bound at every depth (runs/b2/ub.parquet); the
depth D the bound uses there; B2's upper depth and its time on the worst-case clock, Δ + 1/p_h
slots a block; and, as an estimate of the attack's time, B2's lower depth on the same clock.

played.csv: the premined race scored T slots after each target, on the engine's specification
Blend with the coalition withholding (B4's timelines: one epoch at k = 256, 64 replicates a
share) and on independent slots at the model's rates, at the waits whose closed-form chance is
1e-2 and 1e-3. The standard error is the spread of the replicates' rates over the square root of
their number, since successes cluster within a run.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from b2_settlement import ADV, DELAYS_S
from b3_race import BASE, CONFIGS
from finality_sim.private_race import strict_depth
from finality_sim.race import withhold_timelines
from finality_sim.recovery import occupancy
from finality_sim.slots import (race_wait, rates, wait_logfail, wait_needed, worst_logbound,
                                worst_needed)

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "k1"
F = 1 / 30
EPS_RANDOM = (1e-3, 1e-6, 1e-9)
EPS_WORST = (1e-6, 1e-9)
PLAYED_ALPHAS = (0.10, 0.25, 0.30, 1 / 3)
PLAYED_EPS = (1e-2, 1e-3)
REPLICATES = 64
SLOTS = BASE["epochs"] * 10 * int(BASE["k"] / F)
JOBS = 6


def growths() -> dict[str, float]:
    """A1's canonical growth per f on testnet's Blend and the specification's, as B4 and B5 read it."""
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    return {"testnet": float(s[(s.blend_hops == 1) & (s.blend_delay_max == 1)].growth_per_f.iloc[0]),
            "specification": float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)]
                                   .growth_per_f.iloc[0])}


def random_row(blend: str, g: float, alpha: float, eps: float) -> dict:
    a, h = rates(alpha, g, F)
    q = a / (a + h)
    depth = int(strict_depth(q, math.log(eps), lead=True))
    wait = wait_needed(alpha, eps, g, F)
    report_s = depth * 30 / ((1 - alpha) * g)
    model_s = depth / h
    return dict(blend=blend, growth=g, alpha=alpha, eps=eps, wait_slots=wait, wait_h=wait / 3600,
                depth=depth, depth_report_h=report_s / 3600, depth_model_h=model_s / 3600,
                ratio_report=wait / report_s, ratio_model=wait / model_s)


def worst_row(alpha: float, delay: int, eps: float, log_ub: np.ndarray, lower: pd.Series) -> dict:
    wait = worst_needed(alpha, eps, delay, log_ub, F)
    val, d_used = worst_logbound(wait, alpha, delay, log_ub, F)
    ub_depth = int(np.argmax(log_ub <= math.log(eps))) + 1
    clock = delay + 1 / occupancy(F, 1 - alpha)
    return dict(alpha=alpha, delay_s=delay, eps=eps, wait_slots=wait, wait_h=wait / 3600,
                bound_at_wait=math.exp(val), depth_used=d_used, ub_depth=ub_depth, clock_s=clock,
                ub_h=ub_depth * clock / 3600, ratio=wait / (ub_depth * clock),
                lb_depth=float(lower.lb_depth), lb_extrapolated=bool(lower.lb_extrapolated),
                lb_h_estimate=float(lower.lb_depth) * clock / 3600)


def played_rep(kind: str, alpha: float, rep: int, a: float, h: float, waits: list[int]):
    if kind == "engine":
        cfg = SimConfig(**BASE, **CONFIGS["spec"], adversary_frac=alpha, replicate=rep)
        canon, adv, _ = withhold_timelines(cfg)
    else:
        rng = np.random.default_rng([rep, int(alpha * 1000), 7])
        canon = np.nonzero(rng.random(SLOTS) < h)[0].astype(np.int64)
        adv = np.nonzero(rng.random(SLOTS) < a)[0].astype(np.int64)
    succ, scored = race_wait(canon, adv, waits, premine=True)
    return succ, scored


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gs = growths()

    rows = Parallel(n_jobs=JOBS)(delayed(random_row)(b, g, a, e) for b, g in gs.items()
                                 for a in ADV for e in EPS_RANDOM)
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "random.csv", index=False)
    print(r.to_string(index=False, float_format=lambda v: f"{v:.4g}"), end="\n\n")

    ub = pd.read_parquet(HERE / "runs" / "b2" / "ub.parquet")
    depths = pd.read_csv(HERE / "runs" / "b2" / "depths.csv")
    jobs = []
    for (adv, delay), c in ub.groupby(["adv", "delay_s"]):
        c = c.sort_values("depth")
        if not np.array_equal(c.depth.to_numpy(), np.arange(1, len(c) + 1)):
            raise ValueError("B2's curve skips a depth")
        log_ub = np.log(np.minimum(c.ub.to_numpy(), 1.0))
        for eps in EPS_WORST:
            lower = depths[np.isclose(depths.adv, adv) & (depths.delay_s == delay)
                           & np.isclose(depths.eps, eps)].iloc[0]
            jobs.append((float(adv), int(delay), eps, log_ub, lower))
    rows = Parallel(n_jobs=JOBS)(delayed(worst_row)(*j) for j in jobs)
    w = pd.DataFrame(rows).sort_values(["eps", "alpha", "delay_s"])
    w.to_csv(OUT / "worst.csv", index=False)
    with pd.option_context("display.width", 250):
        print(w.to_string(index=False, float_format=lambda v: f"{v:.4g}"), end="\n\n")

    g = gs["specification"]
    out = []
    for alpha in PLAYED_ALPHAS:
        a, h = rates(alpha, g, F)
        waits = [wait_needed(alpha, e, g, F) for e in PLAYED_EPS]
        for kind in ("engine", "model"):
            runs = Parallel(n_jobs=JOBS)(delayed(played_rep)(kind, alpha, rep, a, h, waits)
                                         for rep in range(REPLICATES))
            for i, (e, t) in enumerate(zip(PLAYED_EPS, waits)):
                succ = np.array([s[sorted(waits).index(t)] for s, _ in runs], float)
                scored = np.array([n for _, n in runs], float)
                rate = succ.sum() / scored.sum()
                per = succ / np.maximum(scored, 1)
                out.append(dict(timelines=kind, alpha=alpha, eps=e, wait_slots=t, wait_h=t / 3600,
                                closed=math.exp(wait_logfail(t, alpha, g, F)), targets=int(scored.sum()),
                                successes=int(succ.sum()), rate=rate,
                                se=float(per.std(ddof=1) / math.sqrt(len(per)))))
    p = pd.DataFrame(out)
    p.to_csv(OUT / "played.csv", index=False)
    print(p.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    main()
