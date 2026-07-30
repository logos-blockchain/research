#!/usr/bin/env python
"""Jitter/consensus grid (§6.1): exact oracle, per-(block,node) Exp jitter up to 3 slots.

jitter_mean {0, 0.1, 0.3, 1.0, 3.0} x {regular, blend} x N {1000, 2000}, 10 replicates, U = 2,
windowed_fork_choice/prune_arrival OFF (guaranteed-exact full-matrix mode). Writes one
tail-aggregated row per (topo, N, jitter, rep) to runs/jitter_grid/results.parquet.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory

JITTERS = [0.0, 0.1, 0.3, 1.0, 3.0]
TOPOS = ["regular", "blend"]
NS = [1000, 2000]
REPS = 10
EPOCHS = 20


def _one(topo: str, n: int, jm: float, rep: int) -> dict:
    cfg = SimConfig(n_nodes=n, stake_dist="pareto", topology=topo, degree=6,
                    link_latency_mean=0.5, link_latency_dist="geo",
                    blend_hops=3, blend_delay_max=4.0,
                    max_uncles=2, uncle_window=300, k=256, epochs=EPOCHS,
                    genesis_d_factor=0.5, jitter_mean=jm,
                    windowed_fork_choice=False, prune_arrival=False, replicate=rep)
    df = pd.DataFrame(run_trajectory(cfg))
    t = df[df.epoch >= EPOCHS // 2]
    return dict(topo=topo, N=n, jitter=jm, rep=rep,
                range_ratio=float(t.range_ratio.max()),
                agreement_window=float(t.agreement_window.min()),
                agreement_tip=float(t.agreement_tip.mean()),
                mean_ratio=float(t.mean_ratio.mean()))


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "runs" / "jitter_grid"
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(t, n, j, r) for t in TOPOS for n in NS for j in JITTERS for r in range(REPS)]
    rows = Parallel(n_jobs=4, backend="loky", inner_max_num_threads=1)(
        delayed(_one)(t, n, j, r) for t, n, j, r in jobs)
    df = pd.DataFrame(rows)
    df.to_parquet(out / "results.parquet", index=False)
    print(df.groupby("jitter").agg(range_max=("range_ratio", "max"),
                                   agr_min=("agreement_window", "min"),
                                   acc_lo=("mean_ratio", "min"),
                                   acc_hi=("mean_ratio", "max"),
                                   tip_worst=("agreement_tip", "min")).round(4).to_string())
    print(f"wrote {out/'results.parquet'} ({len(df)} rows)")


if __name__ == "__main__":
    main()
