#!/usr/bin/env python
"""Adversary grids (§6.3 uncle suppression, §6.4 withhold vs suppress) — committed generators.

Suppression x load (§6.3): beta_adv {0.1, 0.3, 0.5} x blending budget {8, 16, 24} s
(loads rho ~ 0.56 / 0.96 / 1.36), U = 2, N = 1000 -> runs/adversary_grid/suppress.parquet.
Withhold vs suppress (§6.4): beta_adv {0.1..0.5} x {regular, blend} x strategy, N = 400,
exact oracle -> runs/adversary_grid/withhold.parquet.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory

EPOCHS = 20
REPS = 16          # withhold at N=400 is noisy; average enough replicates for a clean curve


def _suppress_cell(beta_adv: float, delay: float, rep: int) -> dict:
    cfg = SimConfig(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
                    link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                    blend_delay_max=delay, max_uncles=2, uncle_window=300, k=256,
                    epochs=EPOCHS, genesis_d_factor=0.5,
                    adversary_frac=beta_adv, adversary_strategy="suppress", replicate=rep)
    df = pd.DataFrame(run_trajectory(cfg))
    t = df[df.epoch >= EPOCHS // 2]
    return dict(beta_adv=beta_adv, delay=delay, rep=rep,
                mean_ratio=float(t.mean_ratio.mean()))


def _withhold_cell(beta_adv: float, topo: str, strategy: str, rep: int) -> dict:
    cfg = SimConfig(n_nodes=400, stake_dist="pareto", topology=topo, degree=6,
                    link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                    blend_delay_max=4.0, max_uncles=2, uncle_window=300, k=256,
                    epochs=EPOCHS, genesis_d_factor=0.5,
                    adversary_frac=beta_adv, adversary_strategy=strategy,
                    windowed_fork_choice=False, prune_arrival=False, replicate=rep)
    df = pd.DataFrame(run_trajectory(cfg))
    t = df[df.epoch >= EPOCHS // 2]
    return dict(beta_adv=beta_adv, topo=topo, strategy=strategy, rep=rep,
                mean_ratio=float(t.mean_ratio.mean()))


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "runs" / "adversary_grid"
    out.mkdir(parents=True, exist_ok=True)
    sup_jobs = [(b, d, r) for b in (0.1, 0.3, 0.5) for d in (8.0, 16.0, 24.0)
                for r in range(REPS)]
    sup = pd.DataFrame(Parallel(n_jobs=6, backend="loky", inner_max_num_threads=1)(
        delayed(_suppress_cell)(b, d, r) for b, d, r in sup_jobs))
    sup.to_parquet(out / "suppress.parquet", index=False)
    print("suppression (D_hat/D by beta_adv x delay):")
    print(sup.groupby(["delay", "beta_adv"]).mean_ratio.mean().unstack().round(3).to_string())

    wh_jobs = [(b, t, s, r) for b in (0.1, 0.2, 0.3, 0.4, 0.5) for t in ("regular", "blend")
               for s in ("withhold", "suppress") for r in range(REPS)]
    wh = pd.DataFrame(Parallel(n_jobs=6, backend="loky", inner_max_num_threads=1)(
        delayed(_withhold_cell)(b, t, s, r) for b, t, s, r in wh_jobs))
    wh.to_parquet(out / "withhold.parquet", index=False)
    print("withhold vs suppress (D_hat/D):")
    print(wh.groupby(["strategy", "topo", "beta_adv"]).mean_ratio.mean()
            .unstack().round(3).to_string())
    print(f"wrote {out}/suppress.parquet + withhold.parquet")


if __name__ == "__main__":
    main()
