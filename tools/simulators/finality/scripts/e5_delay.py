"""Phase E5: the private race on the DAG when every honest block arrives as late as Delta allows.

    python scripts/e5_delay.py        # writes runs/e5/race.csv

A full mesh whose every link takes Delta slots: each honest block reaches every other node exactly
Delta slots after its slot. Equal stake, a coalition holding alpha withholds its wins; the window
is that of E2 (w = 7.5 / f_A) and at least Delta + 1. The race of E2: premining, a strictly
heavier coalition, honest blocks that do not descend from the target counting for neither side.
1,000 nodes, about 60,000 targets per point.
"""

from __future__ import annotations

import pathlib

import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from finality_sim.areon import build_dag, dag_race

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "e5"
FS = (1 / 30, 0.25)
DELAYS = (1, 5, 10, 20)
ALPHAS = (0.10, 0.25, 1 / 3)
K_MAX = 60


def window(f: float, delta: int) -> int:
    return max(round(30 * 0.25 / f), delta + 1)


def one(f: float, delta: int, alpha: float, rep: int) -> dict:
    cfg = SimConfig(n_nodes=1000, topology="full_mesh", latency=float(delta), epochs=1, f=f,
                    k=max(16, round(2000 * f)),
                    max_uncles=0, prune_arrival=False, stake_dist="uniform",
                    adversary_frac=alpha, adversary_strategy="withhold", replicate=rep)
    w = window(f, delta)
    d = build_dag(cfg, w)
    first = d.n_blocks // 10
    span = d.slot[-1] - d.slot[first]
    succ, scored = dag_race(d, K_MAX, w, premine=True, win_at=1, first=first,
                            descendants_only=True)
    return dict(f=f, delay_s=delta, window=w, alpha=round(alpha, 4), replicate=rep,
                scored=scored, honest_per_slot=(d.n_blocks - first) / span,
                layers_per_slot=(d.height[-1] - d.height[first]) / span,
                **{f"s{k}": int(succ[k - 1]) for k in range(1, K_MAX + 1)})


def main() -> None:
    rows = Parallel(n_jobs=-2)(delayed(one)(f, d, a, r) for f in FS for d in DELAYS
                               for a in ALPHAS for r in range(round(16 * 0.25 / f)))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "race.csv", index=False)
    g = t.groupby(["f", "delay_s", "alpha"], sort=False).sum(numeric_only=True)
    for k in (5, 10, 20, 40):
        g[f"p{k}"] = g[f"s{k}"] / g.scored
    print(g[["scored", "p5", "p10", "p20", "p40"]])


if __name__ == "__main__":
    main()
