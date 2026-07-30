"""Figure builders. Each takes the results DataFrame and returns a Matplotlib Figure.

Rows are per (config, epoch). We summarise each config to its *equilibrium* by averaging
the tail epochs (after a burn-in), keeping replicates so we can draw percentile bands.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import style

CONFIG_COLS = ["n_nodes", "stake_dist", "latency", "max_uncles", "uncle_strategy", "k"]


def equilibrium(df: pd.DataFrame, burn_frac: float = 0.5) -> pd.DataFrame:
    """Per-(config, replicate) equilibrium means over the tail epochs."""
    cutoff = df["epochs"] * burn_frac
    tail = df[df["epoch"] >= cutoff]
    keys = [*CONFIG_COLS, "replicate"]
    return (
        tail.groupby(keys, as_index=False)
        .agg(
            ratio=("ratio", "mean"),
            q=("q", "mean"),
            q_eff=("q_eff", "mean"),
            var_ratio=("ratio", "var"),
            orphan_rate=("orphan_rate", "mean"),
            n_active=("n_active", "mean"),
        )
    )


def _series_over_replicates(eq: pd.DataFrame, xcol: str, ycol: str, xvals) -> np.ndarray:
    """Build a ``(n_replicates, len(xvals))`` matrix of ``ycol`` for band plots."""
    reps = sorted(eq["replicate"].unique())
    mat = np.full((len(reps), len(xvals)), np.nan)
    for i, r in enumerate(reps):
        sub = eq[eq["replicate"] == r].set_index(xcol)[ycol]
        for j, x in enumerate(xvals):
            if x in sub.index:
                mat[i, j] = sub.loc[x]
    return mat


def _provenance(df: pd.DataFrame) -> str:
    k = [int(x) for x in sorted(df["k"].unique())]
    n = [int(x) for x in sorted(df["n_nodes"].unique())]
    reps = int(df["replicate"].nunique())
    return f"tsi-sim  |  k={k}  N={n}  reps={reps}  f={float(df['f'].iloc[0]):.4g}"


# --- Figure 1: accuracy vs U per latency ------------------------------------
def accuracy_vs_u(df: pd.DataFrame, stake_dist: str, strategy: str = "oldest") -> plt.Figure:
    style.apply_style()
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["n_nodes"] == df["n_nodes"].max())]
    eq = eq[(eq["uncle_strategy"] == strategy) | (eq["max_uncles"] == 0)]
    latencies = sorted(eq["latency"].unique())
    uvals = sorted(eq["max_uncles"].unique())

    fig, ax = plt.subplots()
    for i, lat in enumerate(latencies):
        sub = eq[eq["latency"] == lat]
        mat = _series_over_replicates(sub, "max_uncles", "ratio", uvals)
        style.band_plot(ax, uvals, mat, color=style.color_for(i), label=f"L={lat}")
    ax.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
    ax.set_xlabel("max uncles per block  $U$")
    ax.set_ylabel(r"inferred / true stake  $\langle \hat D / D_{\mathrm{true}} \rangle$")
    ax.set_title(f"TSI accuracy vs uncle cap ({stake_dist} stake)")
    ax.set_xticks(uvals)
    ax.legend(title="latency (slots)", ncol=2)
    return fig


# --- Figure 2: q_eff vs U per latency ---------------------------------------
def qeff_vs_u(df: pd.DataFrame, stake_dist: str, strategy: str = "oldest") -> plt.Figure:
    style.apply_style()
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["n_nodes"] == df["n_nodes"].max())]
    eq = eq[(eq["uncle_strategy"] == strategy) | (eq["max_uncles"] == 0)]
    latencies = sorted(eq["latency"].unique())
    uvals = sorted(eq["max_uncles"].unique())

    fig, ax = plt.subplots()
    for i, lat in enumerate(latencies):
        sub = eq[eq["latency"] == lat]
        mat = _series_over_replicates(sub, "max_uncles", "q_eff", uvals)
        style.band_plot(ax, uvals, mat, color=style.color_for(i), label=f"L={lat}")
        base_q = sub[sub["max_uncles"] == 0]["q"].mean()
        if not np.isnan(base_q):
            ax.axhline(base_q, color=style.color_for(i), lw=0.8, ls=":", alpha=0.6)
    ax.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
    ax.set_xlabel("max uncles per block  $U$")
    ax.set_ylabel(r"effective utilisation  $q_{\mathrm{eff}}$")
    ax.set_title(f"Active-slot recovery vs uncle cap ({stake_dist} stake)")
    ax.set_xticks(uvals)
    ax.legend(title="latency (slots)", ncol=2)
    return fig


# --- Figure 3: convergence (ratio vs epoch) per U ---------------------------
def convergence(df: pd.DataFrame, stake_dist: str, latency: int,
                strategy: str = "oldest") -> plt.Figure:
    style.apply_style()
    sub = df[(df["stake_dist"] == stake_dist) & (df["latency"] == latency)
             & (df["n_nodes"] == df["n_nodes"].max())]
    sub = sub[(sub["uncle_strategy"] == strategy) | (sub["max_uncles"] == 0)]
    uvals = sorted(sub["max_uncles"].unique())
    epochs = sorted(sub["epoch"].unique())

    fig, ax = plt.subplots()
    for i, u in enumerate(uvals):
        su = sub[sub["max_uncles"] == u]
        mat = np.full((su["replicate"].nunique(), len(epochs)), np.nan)
        for ri, r in enumerate(sorted(su["replicate"].unique())):
            s = su[su["replicate"] == r].set_index("epoch")["ratio"]
            for j, e in enumerate(epochs):
                if e in s.index:
                    mat[ri, j] = s.loc[e]
        style.band_plot(ax, epochs, mat, color=style.color_for(i), label=f"U={u}")
    ax.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
    ax.set_xlabel("epoch")
    ax.set_ylabel(r"$\hat D / D_{\mathrm{true}}$")
    ax.set_title(f"Convergence ({stake_dist}, latency L={latency})")
    ax.legend(title="uncle cap", ncol=2)
    return fig


# --- Figure 4: accuracy heatmap over latency x U ----------------------------
def heatmap_accuracy(df: pd.DataFrame, stake_dist: str, n_nodes: int,
                     strategy: str = "oldest") -> plt.Figure:
    style.apply_style()
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["n_nodes"] == n_nodes)]
    eq = eq[(eq["uncle_strategy"] == strategy) | (eq["max_uncles"] == 0)]
    piv = eq.groupby(["latency", "max_uncles"])["ratio"].mean().unstack("max_uncles")
    latencies = piv.index.to_numpy()
    uvals = piv.columns.to_numpy()
    data = piv.to_numpy()

    fig, ax = plt.subplots()
    vmax = np.nanmax(np.abs(data - 1.0))
    im = ax.imshow(data, origin="lower", aspect="auto", cmap=style.DIVERGING_CMAP,
                   vmin=1 - vmax, vmax=1 + vmax)
    ax.set_xticks(range(len(uvals)), uvals)
    ax.set_yticks(range(len(latencies)), latencies)
    ax.set_xlabel("max uncles per block  $U$")
    ax.set_ylabel("network latency  $L$ (slots)")
    ax.set_title(f"Accuracy $\\hat D/D_{{\\mathrm{{true}}}}$ ({stake_dist}, N={n_nodes})")
    for yi in range(len(latencies)):
        for xi in range(len(uvals)):
            v = data[yi, xi]
            if not np.isnan(v):
                safe = 0.98 <= v <= 1.02
                ax.text(xi, yi, f"{v:.2f}", ha="center", va="center", fontsize=7,
                        color="black", fontweight="bold" if safe else "normal")
    fig.colorbar(im, ax=ax, label=r"$\hat D / D_{\mathrm{true}}$")
    ax.grid(False)
    return fig


# --- Figure 5: distribution comparison --------------------------------------
def dist_comparison(df: pd.DataFrame, latency: int, strategy: str = "oldest") -> plt.Figure:
    style.apply_style()
    eq = equilibrium(df)
    eq = eq[(eq["latency"] == latency) & (eq["n_nodes"] == df["n_nodes"].max())]
    eq = eq[(eq["uncle_strategy"] == strategy) | (eq["max_uncles"] == 0)]
    uvals = sorted(eq["max_uncles"].unique())
    fig, ax = plt.subplots()
    for i, dist in enumerate(sorted(eq["stake_dist"].unique())):
        sub = eq[eq["stake_dist"] == dist]
        mat = _series_over_replicates(sub, "max_uncles", "ratio", uvals)
        style.band_plot(ax, uvals, mat, color=style.color_for(i), label=dist)
    ax.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
    ax.set_xlabel("max uncles per block  $U$")
    ax.set_ylabel(r"$\hat D / D_{\mathrm{true}}$")
    ax.set_title(f"Stake-distribution comparison (latency L={latency})")
    ax.set_xticks(uvals)
    ax.legend(title="distribution")
    return fig


# --- Figure 6: variance vs U ------------------------------------------------
def variance_vs_u(df: pd.DataFrame, stake_dist: str, latency: int,
                  strategy: str = "oldest") -> plt.Figure:
    style.apply_style()
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["latency"] == latency)
            & (eq["n_nodes"] == df["n_nodes"].max())]
    eq = eq[(eq["uncle_strategy"] == strategy) | (eq["max_uncles"] == 0)]
    uvals = sorted(eq["max_uncles"].unique())
    var_by_u = eq.groupby("max_uncles")["ratio"].var()
    fig, ax = plt.subplots()
    ax.plot(uvals, [var_by_u.get(u, np.nan) for u in uvals], "o-",
            color=style.color_for(0), label="empirical (across replicates)")
    ax.set_xlabel("max uncles per block  $U$")
    ax.set_ylabel(r"$\mathrm{Var}[\hat D / D_{\mathrm{true}}]$")
    ax.set_title(f"Estimate variance vs uncle cap ({stake_dist}, L={latency})")
    ax.set_xticks(uvals)
    ax.legend()
    return fig


# --- Figure 7: strategy comparison ------------------------------------------
def strategy_comparison(df: pd.DataFrame, stake_dist: str, latency: int) -> plt.Figure:
    style.apply_style()
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["latency"] == latency)
            & (eq["n_nodes"] == df["n_nodes"].max()) & (eq["max_uncles"] > 0)]
    uvals = sorted(eq["max_uncles"].unique())
    fig, ax = plt.subplots()
    for i, strat in enumerate(sorted(eq["uncle_strategy"].unique())):
        sub = eq[eq["uncle_strategy"] == strat]
        mat = _series_over_replicates(sub, "max_uncles", "ratio", uvals)
        style.band_plot(ax, uvals, mat, color=style.color_for(i), label=strat)
    ax.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
    ax.set_xlabel("max uncles per block  $U$")
    ax.set_ylabel(r"$\hat D / D_{\mathrm{true}}$")
    ax.set_title(f"Uncle-selection strategy ({stake_dist}, L={latency})")
    ax.set_xticks(uvals)
    ax.legend(title="strategy")
    return fig


# --- Figure 8: diagnostics (orphan rate vs latency) -------------------------
def orphan_diagnostics(df: pd.DataFrame, stake_dist: str) -> plt.Figure:
    style.apply_style()
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["max_uncles"] == 0)
            & (eq["n_nodes"] == df["n_nodes"].max())]
    g = eq.groupby("latency")["orphan_rate"].agg(["mean", "std"])
    fig, ax = plt.subplots()
    ax.errorbar(g.index, g["mean"], yerr=g["std"], marker="o", color=style.color_for(1),
                capsize=3)
    ax.set_xlabel("network latency  $L$ (slots)")
    ax.set_ylabel("orphan rate (orphans / blocks)")
    ax.set_title(f"Fork/orphan rate vs latency ({stake_dist} stake)")
    return fig
