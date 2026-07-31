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

from tsi_sim.config import SimConfig  # noqa: E402
from tsi_sim.plotting import style  # noqa: E402
from tsi_sim.topology import build_path_latency  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"


def graph_ell_mean(df: pd.DataFrame) -> float:
    """``ell_mean`` — the mean shortest-path (gossip) latency of the run's OWN peering graph.

    Measured from the run's recorded ``(n_nodes, degree, link_latency_mean, link_latency_dist)``
    rather than hardcoded, so the rho axis stays correct if any of those change. It is a statistical
    property of the random d-regular geo graph (seed-invariant to <1% at this N), so one
    representative draw suffices. Post-processing only — this rebuilds the latency *graph* to read
    off its mean, and never touches or re-runs the simulation.
    """
    row = df.iloc[0]
    cfg = SimConfig(n_nodes=int(row.n_nodes), degree=int(row.degree), topology="blend",
                    link_latency_mean=float(row.link_latency_mean),
                    link_latency_dist=str(row.link_latency_dist), k=int(row.k))
    pl = build_path_latency(cfg, np.random.default_rng(0))
    n = pl.shape[0]
    return float(pl[~np.eye(n, dtype=bool)].mean())


def load() -> pd.DataFrame:
    src = sorted(RUNS.glob("*_rho-boundary/results.parquet"))[-1]
    df = pd.read_parquet(src)
    keys = ["blend_delay_max", "max_uncles", "replicate"]
    df["emax"] = df.groupby(keys).epoch.transform("max")
    tail = df[df.epoch >= df.emax // 2]
    # Per-trajectory tail mean FIRST, then mean + SEM ACROSS replicates. Pooling every
    # (replicate x tail-epoch) row instead would treat correlated within-trajectory epochs as
    # independent samples and understate the true replicate spread (by ~1.5x, up to ~3x).
    per_rep = (tail.groupby(keys, as_index=False).mean_ratio.mean())
    g = (per_rep.groupby(["blend_delay_max", "max_uncles"])
         .mean_ratio.agg(["mean", "sem"]).reset_index())
    # Derive the rho axis from the run itself — f, hops, and the *measured* ell_mean — not from
    # hardcoded constants: rho = f*D_vis with D_vis = hops*delta_max/2 + (hops+1)*ell_mean. This
    # only re-labels the x-axis from the existing simulation data; it never re-simulates.
    f = float(df.f.iloc[0])
    hops = int(df.blend_hops.iloc[0])
    ell = graph_ell_mean(df)
    g["rho"] = f * (hops * g.blend_delay_max / 2.0 + (hops + 1) * ell)
    g["deficit"] = 1.0 - g["mean"]
    return g


def fig26(g: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    floor = 3e-4
    for i, U in enumerate((0, 1, 2, 3)):
        s = g[g.max_uncles == U].sort_values("rho")
        c = style.OKABE_ITO[i]
        # left: deficit on a log axis. A cell counts as a RESOLVED positive deficit only if it
        # is both positive and above its own 2*SEM noise level; unresolved cells (at/below noise,
        # or slightly negative because D̂/D sits a hair above 1 from sampling noise) are clamped to
        # the axis floor and drawn HOLLOW, so a point on the floor cannot be misread as a measured
        # deficit. A faint line joins the series for legibility.
        rho = s.rho.values
        d = np.clip(s.deficit.values, floor, None)
        resolved = (s.deficit.values > floor) & (s.deficit.values > 2.0 * s["sem"].values)
        ax1.plot(rho, d, "-", lw=0.8, color=c, alpha=0.5, zorder=0)
        ax1.plot(rho[resolved], d[resolved], "o", ms=4, color=c, label=f"U = {U}")
        ax1.plot(rho[~resolved], d[~resolved], "o", ms=4, mfc="none", mec=c)
        # right: accuracy, capped at 1.0, with the across-replicate SEM
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
