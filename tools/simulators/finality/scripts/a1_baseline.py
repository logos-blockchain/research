"""Phase A1: the baseline over the delay axis (PLAN.md A1, Q3).

    python scripts/a1_baseline.py            # writes runs/a1/{runs.parquet,summary.csv}

Every point: N = 1000 nodes, peering degree 6, Pareto stake, f = 1/30, one epoch of
10*floor(k/f) slots at k = 256, 8 replicates. Two families:

- calibration: the TSI report's points (3 hops, continuous mixing delay U(0, delta), 0.5 s geo
  links), where its engine measured o = 0.20, 0.35, 0.60 at delta = 2, 8, 32 s (§6.10, §7);
- node-aligned: whole-round mixing delays uniform on [1, Delta_max] (the node's release
  delayer), Delta_max from 1 to 12, at 1 and 3 hops and 0.1 s and 0.5 s mean geo links.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from finality_sim.baseline import DEPTHS, run

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "a1"
REPLICATES = 8
BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
            link_latency_dist="geo", k=256, epochs=1, f=1 / 30, max_uncles=0,
            prune_arrival=False)


def grid() -> list[dict]:
    pts = []
    for delta in (2.0, 8.0, 32.0):
        pts.append(dict(family="calibration", blend_hops=3, blend_delay_max=delta,
                        blend_delay_dist="continuous", link_latency_mean=0.5))
    for link in (0.1, 0.5):
        for hops in (1, 3):
            for dmax in (1, 2, 3, 5, 8, 12):
                pts.append(dict(family="rounds", blend_hops=hops, blend_delay_max=float(dmax),
                                blend_delay_dist="rounds", link_latency_mean=link))
    return pts


def one(point: dict, rep: int) -> dict:
    kw = {k: v for k, v in point.items() if k != "family"}
    cfg = SimConfig(**BASE, **kw, replicate=rep)
    m = run(cfg)
    row = dict(point, replicate=rep, orphan_share=m.orphan_share,
               occupied_per_f=m.occupied_rate / cfg.f, growth_per_f=m.growth_rate / cfg.f,
               blocks=m.n_blocks, vis_mean=float(np.mean(m.vis_mean)),
               vis_full_mean=float(np.mean(m.vis_full)),
               vis_full_p99=float(np.percentile(m.vis_full, 99)),
               vis_full_max=float(np.max(m.vis_full)))
    for d in DEPTHS:
        row[f"chain_{d}"] = m.depth_chain[d].tolist()
        row[f"seen_{d}"] = m.depth_seen[d].tolist()
    return row


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    keys = ["family", "blend_hops", "blend_delay_dist", "blend_delay_max", "link_latency_mean"]
    out = []
    for key, g in df.groupby(keys, sort=False):
        r = dict(zip(keys, key))
        n = len(g)
        for col in ("orphan_share", "occupied_per_f", "growth_per_f", "vis_mean",
                    "vis_full_mean", "vis_full_p99", "vis_full_max"):
            r[col] = g[col].mean()
            if col in ("orphan_share", "vis_mean"):
                r[col + "_sem"] = g[col].std(ddof=1) / np.sqrt(n)
        for d in DEPTHS:
            chain = np.concatenate([np.asarray(x) for x in g[f"chain_{d}"]])
            seen = np.concatenate([np.asarray(x) for x in g[f"seen_{d}"]])
            r[f"chain_{d}_p50_s"] = np.percentile(chain, 50)
            r[f"seen_{d}_p95_s"] = np.percentile(seen, 95)
        out.append(r)
    return pd.DataFrame(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pts = grid()
    jobs = [(p, r) for p in pts for r in range(REPLICATES)]
    rows = Parallel(n_jobs=-2, backend="loky")(delayed(one)(p, r) for p, r in jobs)
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / "runs.parquet")
    s = summarise(df)
    s.to_csv(OUT / "summary.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
