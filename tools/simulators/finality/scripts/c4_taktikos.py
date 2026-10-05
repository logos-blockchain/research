"""Phase C4: Taktikos curves against Cryptarchia's constant lottery (PLAN.md C4).

    python scripts/c4_taktikos.py        # writes runs/c4/{curves,engine,race}.csv

The first five curves are calibrated so that the whole stake, producing alone without delay,
makes a block every 30 slots on average, as f = 1/30 does:

- constant: Cryptarchia's lottery, f = 1/30;
- Topl-shaped: Topl's example (cutoff 40, amplitude 0.4, baseline 0.05) stretched in time;
- short cutoff: cutoff 40 slots, baseline f/8;
- short cutoff with a gap: the same after a 10-slot gap;
- gap 10: nothing for 10 slots, then a constant 1/20.

Two constant lotteries at 20 s and 15 s blocks (RATE.md, C1) price a faster constant lottery.

engine: 1,000 nodes, Pareto stake, 0.1 s links, testnet's Blend (1 hop, 1 round) and the
specification's (3 hops, up to 3 rounds), one epoch at k = 256, 8 replicates; orphan share,
canonical growth over f, and the canonical block interval.

race: equal stake, a coalition holding alpha withholds its wins. The honest chain comes from the
engine with that stake withheld; the coalition's private chain is its own renewal process under
the curve, drawn independently of the honest chain. A coalition that falls back to the public tip
restarts its interval there in reality; drawing it from its own last block instead favours it.
The race of B3 (premining, strict ties) scores 64 runs per point.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from finality_sim.baseline import measure_epoch
from finality_sim.race import race
from finality_sim.taktikos import Curve, build_epoch, constant, mean_interval, renewal_slots

F = 1 / 30
OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "c4"
BLENDS = {"testnet": dict(blend_hops=1, blend_delay_max=1.0),
          "specification": dict(blend_hops=3, blend_delay_max=3.0)}
BASE = dict(n_nodes=1000, topology="blend", degree=6, link_latency_dist="geo",
            link_latency_mean=0.1, k=256, epochs=1, f=F, max_uncles=0, prune_arrival=False,
            blend_delay_dist="rounds")
ALPHAS = (0.10, 0.25, 1 / 3)
REPLICATES, RACE_RUNS, K_MAX = 8, 64, 60


def calibrated(gap: int, cutoff: int, base: float, target: float = 30.0) -> Curve:
    """The amplitude that gives the whole stake a mean interval of ``target`` slots."""
    lo, hi = 1e-4, 1.0
    for _ in range(80):
        a = (lo + hi) / 2
        if mean_interval(Curve(gap, cutoff, a, base), 1.0) > target:
            lo = a
        else:
            hi = a
    return Curve(gap, cutoff, (lo + hi) / 2, base)


def stretched(shape: Curve, target: float = 30.0) -> Curve:
    """``shape`` stretched in time, coefficients scaled down alike, to a mean of ``target``."""
    lo, hi = 0.1, 20.0
    for _ in range(80):
        s = (lo + hi) / 2
        c = Curve(shape.gap, round(shape.cutoff * s), shape.amp / s, shape.base / s)
        if mean_interval(c, 1.0) < target:
            lo = s
        else:
            hi = s
    s = (lo + hi) / 2
    cut = round(shape.cutoff * s)
    lo, hi = 0.5, 2.0
    for _ in range(80):
        m = (lo + hi) / 2
        if mean_interval(Curve(shape.gap, cut, m * shape.amp / s, m * shape.base / s), 1.0) > target:
            lo = m
        else:
            hi = m
    m = (lo + hi) / 2
    return Curve(shape.gap, cut, m * shape.amp / s, m * shape.base / s)


CURVES = {
    "constant": constant(F),
    "Topl-shaped": stretched(Curve(0, 40, 0.4, 0.05)),
    "short cutoff": calibrated(0, 40, F / 8),
    "short cutoff, gap 10": calibrated(10, 40, F / 8),
    "gap 10": Curve(10, 10, 1 / 20, 1 / 20),
    "constant, 20 s": constant(1 / 20),
    "constant, 15 s": constant(1 / 15),
}


def canonical_slots(tree) -> np.ndarray:
    chain = np.asarray(tree.canonical_chain(), dtype=np.int64)
    return np.sort(tree.slot[chain])


def engine_point(curve: str, blend: str, rep: int) -> dict:
    cfg = SimConfig(**BASE, **BLENDS[blend], stake_dist="pareto", replicate=rep)
    tree, arrival = build_epoch(cfg, CURVES[curve])
    m = measure_epoch(tree, arrival, cfg.epoch_len)
    gaps = np.diff(canonical_slots(tree))
    produced = m.n_blocks / int(cfg.epoch_len * 0.9)
    return dict(curve=curve, blend=blend, replicate=rep, orphan_share=m.orphan_share,
                growth_per_f=m.growth_rate / F, produced_per_f=produced / F,
                interval_p50=float(np.percentile(gaps, 50)),
                interval_p99=float(np.percentile(gaps, 99)))


def race_point(curve: str, blend: str, alpha: float, rep: int) -> dict:
    cfg = SimConfig(**BASE, **BLENDS[blend], stake_dist="uniform", adversary_frac=alpha,
                    adversary_strategy="withhold", replicate=rep)
    tree, _ = build_epoch(cfg, CURVES[curve])
    canon = canonical_slots(tree)
    adv = renewal_slots(CURVES[curve], alpha, cfg.epoch_len,
                        np.random.default_rng([rep, int(alpha * 1000), 7]))
    succ, scored = race(canon, adv, K_MAX, premine=True, win_at=1)
    return dict(curve=curve, blend=blend, alpha=round(alpha, 4), replicate=rep,
                honest_per_f=canon.size / cfg.epoch_len / F,
                private_per_f=adv.size / cfg.epoch_len / F, scored=scored,
                **{f"s{k}": int(succ[k - 1]) for k in range(1, K_MAX + 1)})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, c in CURVES.items():
        rows.append(dict(curve=name, gap=c.gap, cutoff=c.cutoff, amp=c.amp, base=c.base,
                         mean_interval=mean_interval(c, 1.0),
                         **{f"lone_rate_per_f_{a:.2f}": 1 / mean_interval(c, a) / F
                            for a in (0.10, 0.25, 1 / 3, 0.67, 0.75, 0.90)}))
    pd.DataFrame(rows).to_csv(OUT / "curves.csv", index=False)
    print(pd.DataFrame(rows).round(4).to_string(index=False), end="\n\n")

    eng = Parallel(n_jobs=-2)(delayed(engine_point)(c, b, r) for c in CURVES for b in BLENDS
                              for r in range(REPLICATES))
    e = pd.DataFrame(eng)
    e.to_csv(OUT / "engine.csv", index=False)
    print(e.groupby(["curve", "blend"], sort=False).mean(numeric_only=True).round(3), end="\n\n")

    rr = Parallel(n_jobs=-2)(delayed(race_point)(c, b, a, r) for c in CURVES for b in BLENDS
                             for a in ALPHAS for r in range(RACE_RUNS))
    r = pd.DataFrame(rr)
    r.to_csv(OUT / "race.csv", index=False)
    g = r.groupby(["curve", "blend", "alpha"], sort=False).sum(numeric_only=True)
    for k in (10, 20, 40):
        g[f"p{k}"] = g[f"s{k}"] / g.scored
    print(g[["scored", "p10", "p20", "p40"]])


if __name__ == "__main__":
    main()
