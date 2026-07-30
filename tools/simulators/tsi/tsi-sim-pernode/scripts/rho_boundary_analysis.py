"""Deficit-vs-load figure (fig26) from the rho-boundary sweep (configs/rho-boundary.yaml).

The "region below the block rate": the estimator equilibrium is bounded by 1 (it cannot over-count
occupied slots), so the signal of interest is the UNDER-COUNT DEFICIT  1 - D̂/D >= 0 as a function of
the load rho = f*D_vis, per uncle cap U. hops is fixed at 3 in the sweep so rho ∝ blend_delay_max.

Left panel:  deficit 1 - D̂/D vs rho, per U (log-y), with the U=⌈ρ⌉ boundary visible.
Right panel: the same as accuracy D̂/D vs rho, y-axis capped at the 1.0 bound — no above-1 headroom;
             residual above-1 shows only as ±σ error bars (sampling noise around ≤1).

Run:  python scripts/rho_boundary_analysis.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsi_sim.plotting import style  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
F = 1.0 / 30.0
HOPS = 3
LMEAN = 1.2  # degree-6, N=1000 geo graph (matches §4)


def load() -> pd.DataFrame:
    src = sorted(RUNS.glob("*_rho-boundary/results.parquet"))[-1]
    df = pd.read_parquet(src)
    keys = ["blend_delay_max", "max_uncles", "replicate"]
    df["emax"] = df.groupby(keys).epoch.transform("max")
    tail = df[df.epoch >= df.emax // 2]
    g = (tail.groupby(["blend_delay_max", "max_uncles"])
         .mean_ratio.agg(["mean", "sem"]).reset_index())
    g["rho"] = F * (HOPS * g.blend_delay_max / 2.0 + (HOPS + 1) * LMEAN)
    g["deficit"] = 1.0 - g["mean"]
    return g


def fig26(g: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    for i, U in enumerate((0, 1, 2, 3)):
        s = g[g.max_uncles == U].sort_values("rho")
        c = style.OKABE_ITO[i]
        # left: deficit (floored at a small positive value for the log axis)
        d = np.clip(s.deficit.values, 3e-4, None)
        ax1.plot(s.rho, d, "-o", ms=4, color=c, label=f"U = {U}")
        # right: accuracy, capped at 1.0
        ax2.errorbar(s.rho, s["mean"], yerr=s["sem"], fmt="-o", ms=4, capsize=2,
                     color=c, label=f"U = {U}")
    ax1.set_yscale("log")
    ax1.set_xlabel(r"load  $\rho = f\,D_{vis}$")
    ax1.set_ylabel(r"under-count deficit  $1 - \hat D/D$")
    ax1.set_title(r"deficit grows once $\rho$ exceeds the uncle cap")
    ax1.axvline(1.0, color="0.6", lw=0.8, ls=":")
    ax1.legend(fontsize=8, title="uncle cap")
    ax2.axhline(1.0, color="0.4", lw=1.0, ls="--")
    ax2.text(g.rho.min(), 1.001, r"$\hat D/D = 1$ bound (cannot over-count)",
             fontsize=7, color="0.4", va="bottom")
    ax2.set_ylim(0.0, 1.02)          # cap at the bound: no above-1 headroom
    ax2.set_xlabel(r"load  $\rho = f\,D_{vis}$")
    ax2.set_ylabel(r"accuracy  $\hat D/D$  (bounded by 1)")
    ax2.set_title("equilibrium sits at or below 1 at every load")
    ax2.legend(fontsize=8, loc="lower left", title="uncle cap")
    fig.suptitle(r"The region below the block rate: under-count deficit vs load "
                 r"(blend, N=1000, f=1/30, hops=3)", y=1.02)
    style.save(fig, FIGS / "fig26_deficit_vs_rho", provenance="scripts/rho_boundary_analysis.py")
    plt.close(fig)


def main() -> None:
    g = load()
    fig26(g)
    above = g[g["mean"] > 1 + 2 * g["sem"]]
    print(f"bounded-by-1 check: {len(above)}/{len(g)} cells above 1 by >2 SEM; "
          f"max D̂/D = {g['mean'].max():.4f}")
    print("wrote fig26_deficit_vs_rho")


if __name__ == "__main__":
    main()
