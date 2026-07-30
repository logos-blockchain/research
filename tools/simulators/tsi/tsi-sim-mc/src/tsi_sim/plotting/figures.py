"""Figure builders. Each takes the results DataFrame and returns a Matplotlib Figure.

Rows are per (config, epoch). We summarise each config to its *equilibrium* by averaging
the tail epochs (after a burn-in), keeping replicates so we can draw percentile bands.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .. import concurrency, theory
from ..config import SimConfig
from . import style

CONFIG_COLS = ["n_nodes", "stake_dist", "latency", "max_uncles", "uncle_strategy", "k"]


def _ceiling_line(ax, f: float) -> None:
    """Overlay the intrinsic block-count overshoot ceiling ``-ln(1-f)/f`` (~1.017)."""
    c = float(theory.block_count_ceiling(f))
    ax.axhline(c, color="0.55", lw=0.9, ls=":", zorder=0)
    ax.text(0.99, c, f" full-recovery ceiling {c:.3f}", transform=ax.get_yaxis_transform(),
            ha="right", va="bottom", fontsize=7, color="0.4")


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
    _ceiling_line(ax, float(df["f"].iloc[0]))
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
    if any(u > 0 for u in uvals):
        _ceiling_line(ax, float(sub["f"].iloc[0]))
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
    _ceiling_line(ax, float(df["f"].iloc[0]))
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
    # per-epoch tail variance (mean of each replicate's within-tail variance), matching the
    # marginal Var[D/D_true] that theory.variance_ratio denotes -- NOT the variance across
    # replicate means (which is ~T smaller).
    var_by_u = eq.groupby("max_uncles")["var_ratio"].mean()
    qeff_by_u = eq.groupby("max_uncles")["q_eff"].mean()
    f = float(df["f"].iloc[0])
    T = int(round(6 * float(df["k"].iloc[0]) / f))   # measurement window length
    fig, ax = plt.subplots()
    ax.plot(uvals, [var_by_u.get(u, np.nan) for u in uvals], "o-",
            color=style.color_for(0), label="empirical per-epoch tail variance")
    theo = [float(theory.variance_ratio(f, min(qeff_by_u.get(u, np.nan), 1.0), T)) for u in uvals]
    ax.plot(uvals, theo, "s--", color=style.color_for(1), label=r"theory $(q_{\mathrm{eff}})$")
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


def _config_from_df(df: pd.DataFrame, stake_dist: str, n_nodes: int, latency: int) -> SimConfig:
    """Reconstruct a single-epoch SimConfig from the swept parameters for re-simulation."""
    r = df.iloc[0]
    return SimConfig(
        n_nodes=int(n_nodes), stake_dist=stake_dist, latency=int(latency),
        k=int(r["k"]), pareto_shape=float(r["pareto_shape"]), f=float(r["f"]), epochs=1,
    )


# --- Figure 9: peak concurrent block proposals vs latency -------------------
def concurrency_vs_latency(df: pd.DataFrame, stake_dist: str, n_nodes: int,
                           reps: int = 6) -> plt.Figure:
    """Proposals per latency-sized bucket vs L: the max bucket is the peak concurrency."""
    style.apply_style()
    latencies = sorted(int(x) for x in df["latency"].unique())
    f = float(df["f"].iloc[0])
    maxc, p99c, meanc = [], [], []
    for lat in latencies:
        cfg = _config_from_df(df, stake_dist, n_nodes, lat)
        stats = [concurrency.concurrency_stats(cfg, replicate=r) for r in range(reps)]
        maxc.append(max(s["max"] for s in stats))
        p99c.append(float(np.mean([s["p99"] for s in stats])))
        meanc.append(float(np.mean([s["mean"] for s in stats])))

    fig, ax = plt.subplots()
    ax.plot(latencies, maxc, "o-", color=style.color_for(1), label="max (peak concurrency)")
    ax.plot(latencies, p99c, "s--", color=style.color_for(0), label="99th percentile bucket")
    ax.plot(latencies, meanc, "^:", color=style.color_for(2), label="mean per bucket")
    # expected proposals per bucket ~ L * (-ln(1-f)); reference for the mean
    ref = [max(lat, 1) * (-np.log(1 - f)) for lat in latencies]
    ax.plot(latencies, ref, color="0.6", lw=0.9, ls="-", zorder=0,
            label=r"expected mean $=L\,(-\ln(1-f))$")
    ax.set_xlabel("network latency  $L$ (slots) = bucket size")
    ax.set_ylabel("block proposals per $L$-slot bucket")
    ax.set_title(f"Concurrent block proposals per latency-window ({stake_dist}, N={n_nodes})")
    ax.legend()
    return fig


# --- Figure 10: proposals-per-bucket across time (small multiples) ----------
def concurrency_timeseries(df: pd.DataFrame, stake_dist: str, n_nodes: int,
                           window_slots: int = 3000) -> plt.Figure:
    """Block proposals per latency-sized bucket across time, one panel per latency.

    Each panel steps through the proposals-per-bucket over the first ``window_slots``; the
    dashed line marks the peak concurrency observed over the *whole* epoch for that latency.
    """
    style.apply_style()
    latencies = sorted(int(x) for x in df["latency"].unique() if x > 0)
    if len(latencies) > 4:
        idx = np.linspace(0, len(latencies) - 1, 4).round().astype(int)
        latencies = [latencies[i] for i in idx]

    fig, axes = plt.subplots(len(latencies), 1, sharex=True,
                             figsize=(6.4, 1.5 * len(latencies) + 0.5))
    axes = np.atleast_1d(axes)
    for i, (lat, ax) in enumerate(zip(latencies, axes, strict=True)):
        cfg = _config_from_df(df, stake_dist, n_nodes, lat)
        ws = concurrency.proposal_slots(cfg, replicate=0)
        epoch_max = int(concurrency.window_counts(ws, cfg.epoch_len, lat).max())
        span = min(window_slots, cfg.epoch_len)
        counts = concurrency.window_counts(ws[ws < span], span, lat)
        centers = (np.arange(counts.size) + 0.5) * lat
        ax.step(centers, counts, where="mid", color=style.color_for(i), lw=1.2)
        ax.axhline(epoch_max, color="0.45", ls="--", lw=0.9)
        ax.text(0.995, 0.92, f"L={lat}  ·  epoch peak = {epoch_max}", transform=ax.transAxes,
                ha="right", va="top", fontsize=8)
        ax.set_ylim(0, epoch_max + 1)
        ax.set_ylabel("proposals")
    axes[-1].set_xlabel("slot (time)")
    axes[0].set_title(
        f"Block proposals across time, bucketed by latency ({stake_dist}, N={n_nodes})"
    )
    return fig
