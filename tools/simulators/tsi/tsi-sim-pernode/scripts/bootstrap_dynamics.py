#!/usr/bin/env python
"""Full-scale bootstrap study: block production self-stabilises from any genesis guess (fig1).

Runs at the TRUE security parameter k = 2160, under the Blend transport, at N = 1 000 and
N = 5 000, WITH and WITHOUT uncle references (U = 2 vs U = 0) — so the cold-start behaviour of
the deployed configuration is measured, not extrapolated, and the role of uncles during
bootstrap is visible. genesis_d_factor = initial D_est / true stake (0.01x .. 2x).

Writes runs/bootstrap_fullscale/results.parquet and renders fig1_bootstrap (block-production
rate and D_est/D per epoch; solid = U 2, dashed = U 0; one colour per genesis guess).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.plotting import style

F = 1.0 / 30.0
EPOCHS = 12
# gdf 0.01 floods epoch 0 with ~100x blocks (memory-heavy); run it only at N = 1000.
GRID = [(1000, gdf, rep) for gdf in (0.01, 0.1, 0.5, 1.0, 2.0) for rep in range(3)] + \
       [(5000, gdf, rep) for gdf in (0.1, 1.0, 2.0) for rep in range(2)]


def _one(n: int, gdf: float, u: int, rep: int) -> list[dict]:
    cfg = SimConfig(n_nodes=n, k=2160, stake_dist="pareto", genesis_d_factor=gdf,
                    topology="blend", degree=6, blend_hops=3, blend_delay_max=8.0,
                    link_latency_dist="geo", link_latency_mean=0.5,
                    max_uncles=u, uncle_window=300, epochs=EPOCHS, replicate=rep)
    rows = run_trajectory(cfg)
    for r in rows:
        r["gdf"] = gdf
        r["u"] = u
    return rows


def fig1(df: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    d = df[df.n_nodes == 1000]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.2, 6.2), sharex=True)
    gdfs = sorted(d.gdf.unique())
    for i, gdf in enumerate(gdfs):
        for u, ls in ((2, "-"), (0, "--")):
            # Both panels are indexed by the estimate that DROVE each epoch's production: the
            # start-of-epoch estimate `mean_ratio_in` (block rate depends on it, and at epoch 0 it
            # IS the genesis guess, matching the legend). Plotting end-of-epoch `mean_ratio` here
            # would show the already-updated value at epoch 0 and offset the panels by one epoch.
            s = (d[(d.gdf == gdf) & (d.u == u)]
                 .groupby("epoch").agg(rate=("n_blocks", "mean"), ratio=("mean_ratio_in", "mean")))
            rate = s.rate / (10 * int(2160 / F))          # blocks per slot
            ax1.plot(s.index, rate, ls, color=style.OKABE_ITO[i], lw=1.4, ms=3,
                     marker="o" if u == 2 else None,
                     label=f"{gdf:g}×" if u == 2 else None)
            ax2.plot(s.index, s.ratio, ls, color=style.OKABE_ITO[i], lw=1.4, ms=3,
                     marker="o" if u == 2 else None)
    ax1.axhline(F, color="0.5", lw=0.9, ls=":")
    ax1.text(EPOCHS - 0.4, F * 1.25, "target f", fontsize=8, color="0.4", ha="right")
    ax1.set_yscale("log")
    ax1.set_ylabel("block production (blocks / slot)")
    ax1.set_title("Bootstrap at full scale (k = 2160, Blend, N = 1000): "
                  "solid = U 2, dashed = U 0")
    ax1.legend(fontsize=8, title="genesis D̂ / D", ncols=5)
    ax2.axhline(1.0, color="0.5", lw=0.9, ls=":")
    ax2.set_yscale("log")
    ax2.set_xlabel("epoch")
    ax2.set_ylabel(r"$\hat D / D$")
    style.save(fig, Path(__file__).resolve().parents[1] / "report-figures" / "fig1_bootstrap",
               provenance="scripts/bootstrap_dynamics.py (k=2160)")
    plt.close(fig)


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "runs" / "bootstrap_fullscale"
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(n, g, u, r) for (n, g, r) in GRID for u in (0, 2)]
    results = Parallel(n_jobs=3, backend="loky", inner_max_num_threads=1)(
        delayed(_one)(n, g, u, r) for n, g, u, r in jobs)
    df = pd.DataFrame([row for traj in results for row in traj])
    df.to_parquet(out / "results.parquet", index=False)
    fig1(df)
    # settle epochs: first epoch with block rate within 10% of f, per (n, gdf, u)
    el = 10 * int(2160 / F)
    df["rate"] = df.n_blocks / el
    st = (df.assign(ok=lambda x: (x.rate - F).abs() <= 0.1 * F)
            .groupby(["n_nodes", "gdf", "u", "replicate"])
            .apply(lambda g: int(g[g.ok].epoch.min()) if g.ok.any() else np.nan,
                   include_groups=False))
    print("settle epoch (first epoch within 10% of f):")
    print(st.groupby(["n_nodes", "gdf", "u"]).mean().round(2).to_string())
    print(f"wrote {out/'results.parquet'} ({len(df)} rows) and fig1_bootstrap")


if __name__ == "__main__":
    main()
