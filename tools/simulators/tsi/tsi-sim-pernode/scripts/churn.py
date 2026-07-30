#!/usr/bin/env python
"""Organic honest stake churn: does TSI track active stake within-epoch? (report §6.x, fig29).

The active honest stake oscillates (sine, weekly cycle), ramps, or steps down; TSI should
track it with a one-epoch lag (β=1, §6.5 EMA law). We measure D̂/D_active (should stay ~1)
and D̂/D_total (follows the active fraction), plus the fork rate the transient induces.
Blend, U=2, degree 6, k=256. Writes runs/churn.parquet and fig29_churn.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.plotting import style

BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3, blend_delay_max=8.0,
            max_uncles=2, uncle_window=300, k=256, epochs=40, genesis_d_factor=0.5)
GRID = [(m, p, r) for m in ("sine", "ramp", "step") for p in (2, 4, 8) for r in range(4)]


def _one(mode: str, period: int, rep: int) -> list[dict]:
    cfg = SimConfig(**BASE, churn_amp=0.3, churn_period=period, churn_mode=mode, replicate=rep)
    rows = run_trajectory(cfg)
    for r in rows:
        r["mode"], r["period"] = mode, period
    return rows


def fig29(df: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.0), sharey=True)
    for ax, mode in zip(axes, ("sine", "ramp", "step"), strict=True):
        s = df[(df["mode"] == mode) & (df.period == 4)]
        g = s.groupby("epoch").agg(active=("active_stake_frac", "mean"),
                                   tot=("mean_ratio", "mean"))
        g["corr"] = g.tot / g.active
        ax.plot(g.index, g.active, "--", color="0.6", lw=1.4, label="active stake / total")
        ax.plot(g.index, g.tot, "-o", ms=3, color=style.OKABE_ITO[0], label="D̂ / D_total")
        ax.plot(g.index, g["corr"], "-s", ms=3, color=style.OKABE_ITO[1], label="D̂ / D_active")
        ax.axhline(1.0, color="0.8", lw=0.7, ls=":")
        ax.set_xlabel("epoch")
        ax.set_title(f"{mode} churn (30 %, period 4)")
    axes[0].set_ylabel("stake fraction / accuracy")
    axes[0].legend(fontsize=8, loc="lower left")
    fig.suptitle("TSI tracks active stake under organic churn (β=1, one-epoch lag); "
                 "corrected accuracy stays ~1", y=1.03)
    style.save(fig, Path(__file__).resolve().parents[1] / "report-figures" / "fig29_churn",
               provenance="scripts/churn.py")
    plt.close(fig)


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "runs"
    res = Parallel(n_jobs=6, backend="loky", inner_max_num_threads=1)(
        delayed(_one)(m, p, r) for m, p, r in GRID)
    df = pd.DataFrame([row for traj in res for row in traj])
    df.to_parquet(out / "churn.parquet", index=False)
    fig29(df)
    print("=== churn: D̂/D_active (tracking accuracy) and worst lag, period 4 ===")
    for (mode,), g in df[df.period == 4].groupby(["mode"]):
        t = g[g.epoch >= 8]
        corr = (t.mean_ratio / t.active_stake_frac)
        print(f"{mode}: D̂/D_active {corr.mean():.3f} (min {corr.min():.3f}), "
              f"range_ratio {t.range_ratio.max():.4f}, fork_rate {t.fork_rate.mean():.3f}")
    print(f"wrote {out/'churn.parquet'} and fig29_churn")


if __name__ == "__main__":
    main()
