#!/usr/bin/env python
"""Capstone: the recommended configuration end-to-end at true k=2160 (report §8).

One config — f=1/30, W=300, U=2, β=1, degree 6, Blend 3 hops × 8 s, Pareto stake — run honest
and under a 30 % uncle-suppression adversary, confirming accuracy, consensus, fork rate, reorg
depth, and the emergent reference rate p_ref ALL hold together. Writes runs/capstone.parquet.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory

REC = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
           link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3, blend_delay_max=8.0,
           max_uncles=2, uncle_window=300, uncle_strategy="oldest", k=2160, epochs=40,
           genesis_d_factor=0.5, early_stop=True)


def _one(adv: float, rep: int) -> list[dict]:
    cfg = SimConfig(**REC, adversary_frac=adv, adversary_strategy="suppress", replicate=rep)
    rows = run_trajectory(cfg)
    for r in rows:
        r["adv"] = adv
    return rows


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "runs"
    jobs = [(a, r) for a in (0.0, 0.3) for r in range(8)]
    res = Parallel(n_jobs=4, backend="loky", inner_max_num_threads=1)(
        delayed(_one)(a, r) for a, r in jobs)
    df = pd.DataFrame([row for traj in res for row in traj])
    df.to_parquet(out / "capstone.parquet", index=False)
    print("=== Capstone: recommended config, all metrics together (equilibrium tail) ===")
    for adv, g in df.groupby("adv"):
        t = g[g.epoch >= g.epoch.max() // 2]
        print(f"adversary {adv:.0%}: D̂/D {t.mean_ratio.mean():.4f}  "
              f"range_ratio {t.range_ratio.max():.4f}  agreement {t.agreement_window.min():.4f}  "
              f"fork_rate {t.fork_rate.mean():.3f}  max_reorg_depth {t.max_reorg_depth.max()}  "
              f"p_ref {t.p_ref.mean():.3f}")
    print(f"wrote {out/'capstone.parquet'} ({len(df)} rows)")


if __name__ == "__main__":
    main()
