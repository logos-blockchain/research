"""Phase C1: the orphan share and canonical growth over block rate and delay (PLAN.md C1).

    python scripts/c1_rate.py            # writes runs/c1/{runs.parquet,summary.csv}

Same engine and settings as A1 (N = 1000, degree 6, Pareto stake, 0.1 s geo links, whole-round
mixing delays, 8 replicates, k = 256 so every run holds ~2,560 blocks), over f and the delay.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from finality_sim.baseline import run

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "c1"
REPLICATES = 8
INTERVALS = (60, 45, 30, 20, 15, 10)            # seconds between blocks, f = 1/interval
DELAYS = ((1, 1), (3, 1), (3, 3), (3, 8))       # (hops, Delta_max rounds)
BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
            link_latency_dist="geo", link_latency_mean=0.1, blend_delay_dist="rounds",
            k=256, epochs=1, max_uncles=0, prune_arrival=False)


def one(interval: int, hops: int, dmax: int, rep: int) -> dict:
    cfg = SimConfig(**BASE, f=1 / interval, blend_hops=hops, blend_delay_max=float(dmax),
                    replicate=rep)
    m = run(cfg)
    return dict(interval=interval, hops=hops, delta_max=dmax, replicate=rep,
                orphan_share=m.orphan_share, growth_per_f=m.growth_rate * interval,
                vis_mean=float(np.mean(m.vis_mean)),
                vis_full_p99=float(np.percentile(m.vis_full, 99)))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(i, h, d, r) for i in INTERVALS for h, d in DELAYS for r in range(REPLICATES)]
    df = pd.DataFrame(Parallel(n_jobs=-2, backend="loky")(delayed(one)(*j) for j in jobs))
    df.to_parquet(OUT / "runs.parquet")
    g = df.groupby(["hops", "delta_max", "interval"], sort=False)
    s = g.agg(orphan_share=("orphan_share", "mean"),
              orphan_sem=("orphan_share", lambda x: x.std(ddof=1) / np.sqrt(len(x))),
              growth_per_f=("growth_per_f", "mean"), vis_mean=("vis_mean", "mean"),
              vis_full_p99=("vis_full_p99", "mean")).reset_index()
    s.to_csv(OUT / "summary.csv", index=False)
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
