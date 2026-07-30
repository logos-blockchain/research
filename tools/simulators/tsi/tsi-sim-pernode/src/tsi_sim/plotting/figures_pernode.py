"""Per-node divergence & topology figures. Each takes the results frame, returns a Figure.

Headline finding these visualise: per-node ``D_est`` spread stays ~0 and window agreement
stays ~1 (validating the reduced model) even while nodes disagree on the current tip;
topology/latency instead shift the shared *mean* accuracy, which uncles recover.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import style

CONFIG_COLS = ["n_nodes", "stake_dist", "topology", "degree", "link_latency_mean",
               "blend_hops", "blend_delay_max", "latency", "max_uncles",
               "uncle_strategy", "uncle_window", "init_dest", "k"]

# Graph topologies (as opposed to the full_mesh baseline) and the dominant latency knob each
# is plotted against: regular varies the per-link latency, blend varies the per-hop mix delay.
GRAPH_TOPOLOGIES = ("regular", "blend")


def _lat_axis(topo: str) -> tuple[str, str]:
    """(dataframe column, axis label) for the dominant latency knob of a graph topology."""
    if topo == "blend":
        return "blend_delay_max", "max blending delay per hop (slots)"
    return "link_latency_mean", "mean per-link latency (slots)"


def equilibrium(df: pd.DataFrame, burn_frac: float = 0.5) -> pd.DataFrame:
    """Per-(config, replicate) tail means of the summary columns.

    Burn-in is a fraction of each trajectory's *observed* last epoch, not the configured
    ``epochs`` — early-stopped runs (config.early_stop) terminate well before the planned
    ``epochs``, so thresholding on the configured value would drop every row.
    """
    max_epoch = df.groupby([*CONFIG_COLS, "replicate"])["epoch"].transform("max")
    tail = df[df["epoch"] >= max_epoch * burn_frac]
    agg = {c: (c, "mean") for c in
           ("mean_ratio", "range_ratio", "iqr_ratio", "agreement_window", "agreement_tip",
            "mean_q", "mean_q_eff", "mean_orphan_rate", "max_ratio", "min_ratio")}
    return tail.groupby([*CONFIG_COLS, "replicate"], as_index=False).agg(**agg)


def _prov(df: pd.DataFrame) -> str:
    k = [int(x) for x in sorted(df["k"].unique())]
    n = [int(x) for x in sorted(df["n_nodes"].unique())]
    return f"tsi-sim-pernode  |  k={k}  N={n}  reps={int(df['replicate'].nunique())}"


# --- Figure 1: headline — D_est spread ~0 & agreement, vs epoch --------------
def divergence_vs_epoch(df: pd.DataFrame, stake_dist: str, topo: str = "regular") -> plt.Figure:
    style.apply_style()
    sub = df[(df["stake_dist"] == stake_dist) & (df["topology"] == topo)]
    if sub.empty:
        sub = df[df["stake_dist"] == stake_dist]
    g = sub.groupby("epoch").agg(
        range_ratio=("range_ratio", "mean"), iqr_ratio=("iqr_ratio", "mean"),
        agree_w=("agreement_window", "mean"), agree_t=("agreement_tip", "mean"))
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(6.4, 5.0))
    ax1.plot(g.index, g["range_ratio"], "o-", color=style.color_for(1), label="range (max−min)")
    ax1.plot(g.index, g["iqr_ratio"], "s--", color=style.color_for(0), label="IQR")
    ax1.set_ylabel(r"per-node $\hat D/D_{\mathrm{true}}$ spread")
    ax1.set_title(f"Per-node D_est divergence stays ~0 ({stake_dist}, {topo})")
    ax1.legend()
    ax2.plot(g.index, g["agree_w"], "o-", color=style.color_for(2), label="window prefix")
    ax2.plot(g.index, g["agree_t"], "^--", color=style.color_for(3), label="current tip")
    ax2.set_ylim(0, 1.05)
    ax2.set_xlabel("epoch")
    ax2.set_ylabel("node agreement fraction")
    ax2.legend(title="agreement on")
    return fig


# --- Figure 2: mean accuracy vs latency, per degree --------------------------
def accuracy_vs_link_latency(df: pd.DataFrame, stake_dist: str,
                             topo: str = "regular") -> plt.Figure:
    style.apply_style()
    lat_col, lat_label = _lat_axis(topo)
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["topology"] == topo)]
    umin = int(eq["max_uncles"].min()) if not eq.empty else 0   # min U WITHIN this (dist, topo)
    eq = eq[eq["max_uncles"] == umin]
    lls = sorted(eq[lat_col].unique())
    fig, ax = plt.subplots()
    for i, deg in enumerate(sorted(eq["degree"].unique())):
        s = eq[eq["degree"] == deg].groupby(lat_col)["mean_ratio"].mean()
        ax.plot(lls, [s.get(x, np.nan) for x in lls], "o-", color=style.color_for(i),
                label=f"degree={deg}")
    ax.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
    ax.set_xlabel(lat_label)
    ax.set_ylabel(r"mean $\hat D / D_{\mathrm{true}}$")
    ax.set_title(f"Accuracy vs latency ({stake_dist}, {topo}, U={umin})")
    ax.legend(title="peering")
    return fig


# --- Figure 3: mean accuracy vs U, per latency (uncle recovery) --------------
def accuracy_vs_u(df: pd.DataFrame, stake_dist: str, topo: str = "regular") -> plt.Figure:
    style.apply_style()
    lat_col, lat_label = _lat_axis(topo)
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["topology"] == topo)]
    uvals = sorted(eq["max_uncles"].unique())
    fig, ax = plt.subplots()
    for i, ll in enumerate(sorted(eq[lat_col].unique())):
        s = eq[eq[lat_col] == ll].groupby("max_uncles")["mean_ratio"].mean()
        ax.plot(uvals, [s.get(x, np.nan) for x in uvals], "o-", color=style.color_for(i),
                label=f"{ll:g}")
    ax.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
    ax.set_xlabel("max uncles per block  $U$")
    ax.set_ylabel(r"mean $\hat D / D_{\mathrm{true}}$")
    ax.set_title(f"Uncle recovery under topology ({stake_dist}, {topo})")
    ax.set_xticks(uvals)
    # Slot-counting bounds the equilibrium at 1 (it cannot over-count occupied slots); any
    # above-1 reading is sampling noise, so cap the view at the bound rather than show headroom.
    ax.set_ylim(top=1.01)
    ax.legend(title=lat_label)
    return fig


# --- Figure 4: tip agreement vs latency, per degree --------------------------
def tip_agreement_vs_latency(df: pd.DataFrame, stake_dist: str,
                             topo: str = "regular") -> plt.Figure:
    style.apply_style()
    lat_col, lat_label = _lat_axis(topo)
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["topology"] == topo)]
    umin = int(eq["max_uncles"].min()) if not eq.empty else 0   # min U WITHIN this (dist, topo)
    eq = eq[eq["max_uncles"] == umin]
    lls = sorted(eq[lat_col].unique())
    fig, ax = plt.subplots()
    for i, deg in enumerate(sorted(eq["degree"].unique())):
        s = eq[eq["degree"] == deg].groupby(lat_col)["agreement_tip"].mean()
        ax.plot(lls, [s.get(x, np.nan) for x in lls], "o-", color=style.color_for(i),
                label=f"degree={deg}")
    ax.set_xlabel(lat_label)
    ax.set_ylabel("current-tip agreement fraction")
    ax.set_title(f"Tip-level fork disagreement vs topology ({stake_dist}, {topo})")
    ax.legend(title="peering")
    return fig


# --- Figure 6: accuracy heatmap over latency x uncle-cap (per degree) --------
def heatmap_accuracy(df: pd.DataFrame, stake_dist: str, degree: int,
                     topo: str = "regular") -> plt.Figure:
    """Decision chart: mean D_est/D_true over (latency knob) x (uncle cap) at a degree."""
    style.apply_style()
    lat_col, lat_label = _lat_axis(topo)
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["topology"] == topo)
            & (eq["degree"] == degree) & (eq["init_dest"] == "common")]
    piv = eq.groupby([lat_col, "max_uncles"])["mean_ratio"].mean().unstack("max_uncles")
    lls = piv.index.to_numpy()
    uvals = piv.columns.to_numpy()
    data = piv.to_numpy()

    fig, ax = plt.subplots()
    # Accuracy is bounded by 1 (slot-counting cannot over-count), so the colour scale tops out
    # at the true maximum 1.0 rather than treating above-1 noise as a symmetric deviation.
    lo = float(np.nanmin(data)) if np.isfinite(data).any() else 0.5
    im = ax.imshow(data, origin="lower", aspect="auto", cmap=style.SEQUENTIAL_CMAP,
                   vmin=lo, vmax=1.0)
    ax.set_xticks(range(len(uvals)), uvals)
    ax.set_yticks(range(len(lls)), [f"{x:g}" for x in lls])
    ax.set_xlabel("max uncles per block  $U$")
    ax.set_ylabel(lat_label)
    ax.set_title(
        f"Accuracy $\\hat D/D_{{\\mathrm{{true}}}}$ ({stake_dist}, {topo}, degree={degree})")
    for yi in range(len(lls)):
        for xi in range(len(uvals)):
            v = data[yi, xi]
            if np.isfinite(v):
                safe = 0.98 <= v <= 1.02
                tc = "white" if (v - lo) / max(1e-9, 1.0 - lo) < 0.45 else "black"
                ax.text(xi, yi, f"{v:.2f}", ha="center", va="center", fontsize=7,
                        color=tc, fontweight="bold" if safe else "normal")
    fig.colorbar(im, ax=ax, label=r"$\hat D / D_{\mathrm{true}}$")
    ax.grid(False)
    return fig


# --- Figure 5: heterogeneous-start recovery (spread preserved) ---------------
def heterogeneous_recovery(df: pd.DataFrame, stake_dist: str,
                           topo: str = "regular") -> plt.Figure | None:
    # filter to ONE topology — the injected-spread dynamics differ by propagation model, so
    # merging regular + blend would plot a curve neither regime actually follows.
    het = df[(df["stake_dist"] == stake_dist) & (df["init_dest"] == "heterogeneous")
             & (df["topology"] == topo)]
    if het.empty:
        return None
    style.apply_style()
    g = het.groupby("epoch")["range_ratio"].agg(["mean", "std"])
    fig, ax = plt.subplots()
    ax.errorbar(g.index, g["mean"], yerr=g["std"], marker="o", color=style.color_for(1), capsize=2)
    ax.set_xlabel("epoch")
    ax.set_ylabel(r"per-node spread  range($\hat D/D_{\mathrm{true}}$)")
    ax.set_title(f"Heterogeneous start: injected disagreement is preserved ({stake_dist}, {topo})")
    return fig


# --- Figure 7: bootstrap — block-production rate stabilisation ----------------
def block_production_stabilization(df: pd.DataFrame, stake_dist: str | None = None) -> plt.Figure:
    """Cold-start dynamics: block production rate + ``D_est`` convergence per ``genesis_d_factor``.

    At bootstrap no node knows the true total stake, so the difficulty ``D_est`` is only a guess.
    A guess *below* the truth (``genesis_d_factor < 1``) inflates every node's win probability
    ``phi(w_i / D_est)`` → a block "storm" many times the target rate; TSI reads the high density
    and raises ``D_est`` until production settles at the equilibrium rate ``~f`` within a couple of
    epochs. A guess *above* the truth under-produces and is corrected up. Top panel: production
    rate ``n_blocks / epoch_len`` (log scale) vs epoch; bottom: ``D_est / D_true`` vs epoch.
    """
    style.apply_style()
    sub = df if stake_dist is None else df[df["stake_dist"] == stake_dist]
    if sub.empty:
        sub = df
    sub = sub.copy()
    f = float(sub["f"].iloc[0])
    sub["epoch_len"] = np.floor(sub["k"] / sub["f"]) * 10.0        # E = 10*floor(k/f)
    sub["blocks_per_slot"] = sub["n_blocks"] / sub["epoch_len"]

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(6.4, 5.6))
    for i, g in enumerate(sorted(sub["genesis_d_factor"].unique())):
        s = sub[sub["genesis_d_factor"] == g]
        rate = s.groupby("epoch")["blocks_per_slot"].mean()
        # D_est that DROVE each epoch's production (start-of-epoch estimate), so both panels
        # are indexed by the same operating estimate — the gdf=0.01 curve starts at 0.01.
        ratio_in = s.groupby("epoch")["mean_ratio_in"].mean()
        c = style.color_for(i)
        ax1.plot(rate.index, rate.to_numpy(), "o-", color=c, ms=3.5, label=f"{g:g}")
        ax2.plot(ratio_in.index, ratio_in.to_numpy(), "o-", color=c, ms=3.5, label=f"{g:g}")
    ax1.axhline(f, color="0.4", lw=1.0, ls="--", zorder=0)
    ax1.text(0.99, f, r" equilibrium $\approx f$", transform=ax1.get_yaxis_transform(),
             va="bottom", ha="right", fontsize=7, color="0.4")
    ax1.set_yscale("log")
    ax1.set_ylabel("block production\n(blocks / slot)")
    ax1.set_title("Bootstrap: block production stabilises to the target rate")
    ax1.legend(title=r"genesis $D_{\mathrm{est}}/D_{\mathrm{true}}$", ncol=2, loc="upper right")
    ax2.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
    ax2.set_yscale("log")
    ax2.set_xlabel("epoch")
    ax2.set_ylabel(r"$D_{\mathrm{est}} / D_{\mathrm{true}}$ (start of epoch)")
    ax2.set_title(r"...as TSI corrects $D_{\mathrm{est}}$ to the true total stake")
    return fig


# --- Figure 8: uncle-window sufficiency — accuracy vs W, per delay -------------
def accuracy_vs_uncle_window(df: pd.DataFrame, stake_dist: str,
                             topo: str = "regular") -> plt.Figure:
    """Mean ``D_hat/D`` vs the uncle window ``W``, one line per delay (the topology's latency knob).

    An uncle can only reference an orphan whose slot is within ``W`` of the referencing block, so
    when block visibility is delayed the orphans spread over a wider slot range — a small ``W``
    then fails to reach them and the estimate stays low. This shows, at a fixed uncle cap, the
    critical ``W`` at which recovery kicks in, and how it grows with the delay.
    """
    style.apply_style()
    lat_col, lat_label = _lat_axis(topo)
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["topology"] == topo)]
    u = int(eq["max_uncles"].max()) if not eq.empty else 0     # this study fixes a single U
    eq = eq[eq["max_uncles"] == u]
    ws = sorted(eq["uncle_window"].unique())
    fig, ax = plt.subplots()
    for i, d in enumerate(sorted(eq[lat_col].unique())):
        s = eq[eq[lat_col] == d].groupby("uncle_window")["mean_ratio"].mean()
        ax.plot(ws, [s.get(x, np.nan) for x in ws], "o-", color=style.color_for(i), label=f"{d:g}")
    ax.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
    ax.set_xscale("log")
    ax.set_xlabel("uncle window  $W$  (slots)")
    ax.set_ylabel(r"mean $\hat D / D_{\mathrm{true}}$")
    ax.set_title(f"Uncle-window sufficiency ({stake_dist}, {topo}, U={u})")
    ax.set_ylim(top=1.01)          # bounded by 1 (see accuracy_vs_u); no above-1 headroom
    ax.legend(title=lat_label)
    return fig


# --- Figure 9: W x delay accuracy heatmap -------------------------------------
def heatmap_window_delay(df: pd.DataFrame, stake_dist: str, topo: str = "regular") -> plt.Figure:
    """Accuracy ``D_hat/D`` over uncle window ``W`` (rows) x delay (cols) at a fixed uncle cap.

    Reads off the ``(W, delay)`` relation directly: blue cells are where ``W`` is too small for the
    delay (uncles can't reach the orphans) — the boundary is the minimum window a given delay needs.
    """
    style.apply_style()
    lat_col, lat_label = _lat_axis(topo)
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["topology"] == topo)]
    u = int(eq["max_uncles"].max()) if not eq.empty else 0
    eq = eq[eq["max_uncles"] == u]
    piv = eq.groupby(["uncle_window", lat_col])["mean_ratio"].mean().unstack(lat_col)
    ws = piv.index.to_numpy()
    delays = piv.columns.to_numpy()
    data = piv.to_numpy()

    fig, ax = plt.subplots()
    # Accuracy is bounded by 1 (slot-counting cannot over-count), so the colour scale tops out
    # at the true maximum 1.0 rather than treating above-1 noise as a symmetric deviation.
    lo = float(np.nanmin(data)) if np.isfinite(data).any() else 0.5
    im = ax.imshow(data, origin="lower", aspect="auto", cmap=style.SEQUENTIAL_CMAP,
                   vmin=lo, vmax=1.0)
    ax.set_xticks(range(len(delays)), [f"{x:g}" for x in delays])
    ax.set_yticks(range(len(ws)), [f"{int(x)}" for x in ws])
    ax.set_xlabel(lat_label)
    ax.set_ylabel("uncle window  $W$  (slots)")
    ax.set_title(f"Accuracy over (W x delay) ({stake_dist}, {topo}, U={u})")
    for yi in range(len(ws)):
        for xi in range(len(delays)):
            v = data[yi, xi]
            if np.isfinite(v):
                tc = "white" if (v - lo) / max(1e-9, 1.0 - lo) < 0.45 else "black"
                ax.text(xi, yi, f"{v:.2f}", ha="center", va="center", fontsize=7,
                        color=tc, fontweight="bold" if 0.98 <= v <= 1.02 else "normal")
    fig.colorbar(im, ax=ax, label=r"$\hat D / D_{\mathrm{true}}$")
    ax.grid(False)
    return fig


# --- Figure 10: joint (W x U) safe region at a fixed delay --------------------
def heatmap_window_uncles(df: pd.DataFrame, stake_dist: str, delay: float,
                          topo: str = "blend") -> plt.Figure:
    """Accuracy ``D_hat/D`` over uncle window ``W`` (rows) x uncle cap ``U`` (cols) at one delay.

    Maps the joint ``(W, U)`` safe region: white cells are recovered. Moving right (more uncles)
    vs up (wider window) shows which lever matters where — a wider window only helps until one
    uncle per block can no longer drain the orphan queue, past which you must add uncles instead.
    """
    style.apply_style()
    lat_col, lat_label = _lat_axis(topo)
    eq = equilibrium(df)
    eq = eq[(eq["stake_dist"] == stake_dist) & (eq["topology"] == topo) & (eq[lat_col] == delay)]
    piv = eq.groupby(["uncle_window", "max_uncles"])["mean_ratio"].mean().unstack("max_uncles")
    ws = piv.index.to_numpy()
    us = piv.columns.to_numpy()
    data = piv.to_numpy()

    fig, ax = plt.subplots()
    # Accuracy is bounded by 1 (slot-counting cannot over-count), so the colour scale tops out
    # at the true maximum 1.0 rather than treating above-1 noise as a symmetric deviation.
    lo = float(np.nanmin(data)) if np.isfinite(data).any() else 0.5
    im = ax.imshow(data, origin="lower", aspect="auto", cmap=style.SEQUENTIAL_CMAP,
                   vmin=lo, vmax=1.0)
    ax.set_xticks(range(len(us)), [f"{int(x)}" for x in us])
    ax.set_yticks(range(len(ws)), [f"{int(x)}" for x in ws])
    ax.set_xlabel("max uncles per block  $U$")
    ax.set_ylabel("uncle window  $W$  (slots)")
    knob = lat_label.split("(")[0].strip()
    ax.set_title(f"(W x U) accuracy ({stake_dist}, {topo}, {knob}={delay:g})")
    for yi in range(len(ws)):
        for xi in range(len(us)):
            v = data[yi, xi]
            if np.isfinite(v):
                tc = "white" if (v - lo) / max(1e-9, 1.0 - lo) < 0.45 else "black"
                ax.text(xi, yi, f"{v:.2f}", ha="center", va="center", fontsize=7,
                        color=tc, fontweight="bold" if 0.98 <= v <= 1.02 else "normal")
    fig.colorbar(im, ax=ax, label=r"$\hat D / D_{\mathrm{true}}$")
    ax.grid(False)
    return fig
