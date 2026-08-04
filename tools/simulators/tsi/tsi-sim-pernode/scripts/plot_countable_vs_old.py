"""Comparison figures: countable uncle model (spec counting rules) vs the old model.

Consumes the results of three sweeps:

  tsi-sweep --config configs/countable-vs-old.yaml --label cvo-countable
  tsi-sweep --config configs/countable-vs-old.yaml --old --label cvo-old
  tsi-sweep --config configs/absorption-window.yaml --label absorption-window

and renders (into --out):

  cvo_accuracy_vs_delay      equilibrium D/D_true vs Blend mixing delay; solid = countable,
                             dashed = old, one Okabe-Ito hue per U (color follows U).
  cvo_prediction_vs_sim      predicted log(1-f)/log(1-f/q_u) from the MEASURED q_u vs the
                             simulated equilibrium — the q -> q_u reduction check.
  cvo_recovery_vs_delay      measured recovery r = (q_eff - q)/(1 - q) and the first-fork
                             rejection share (deep_ref_share) vs delay.
  absorption_window          equilibrium vs the window absorption parameter W per delay.

Usage:
  python scripts/plot_countable_vs_old.py --countable RUNDIR --old RUNDIR \
      --absorption RUNDIR --out figures/countable-vs-old
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tsi_sim.plotting import style
from tsi_sim.plotting.figures_pernode import equilibrium
from tsi_sim.theory import expected_ratio

DELAY = "blend_delay_max"


def _load(run_dir: str | Path) -> pd.DataFrame:
    return pd.read_parquet(Path(run_dir) / "results.parquet")


def _eq(df: pd.DataFrame, extra_cols: tuple[str, ...] = ()) -> pd.DataFrame:
    """Equilibrium (post-burn) means per (delay, U) cell, averaged over replicates."""
    eq = equilibrium(df)
    keys = [DELAY, "max_uncles", *extra_cols]
    agg = {"mean_ratio": "mean", "mean_q": "mean", "mean_q_eff": "mean"}
    if "deep_ref_share" in eq.columns:
        agg["deep_ref_share"] = "mean"
    return eq.groupby(keys, as_index=False).agg(agg)


def fig_accuracy_vs_delay(cnt: pd.DataFrame, old: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots()
    us = sorted(cnt["max_uncles"].unique())
    for i, u in enumerate(us):
        c = style.color_for(i)
        a = cnt[cnt.max_uncles == u].sort_values(DELAY)
        b = old[old.max_uncles == u].sort_values(DELAY)
        ax.plot(a[DELAY], a.mean_ratio, "-o", color=c, label=f"U={u} countable", ms=4)
        ax.plot(b[DELAY], b.mean_ratio, "--s", color=c, label=f"U={u} old", ms=4,
                alpha=0.75)
    ax.axhline(1.0, color="0.4", lw=0.8, ls=":")
    ax.set_xlabel("max per-relay mixing delay (slots)")
    ax.set_ylabel(r"equilibrium $\hat{D}/D_{true}$")
    ax.set_title("Accuracy vs delay: countable (solid) vs old (dashed) uncle model")
    ax.legend(ncol=2)
    return fig


def fig_prediction_vs_sim(cnt: pd.DataFrame, f: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    sub = cnt[cnt.max_uncles > 0]
    pred = expected_ratio(f, sub.mean_q_eff.to_numpy())
    us = sorted(sub["max_uncles"].unique())
    for i, u in enumerate(us):
        m = (sub.max_uncles == u).to_numpy()
        ax.scatter(np.asarray(pred)[m], sub.mean_ratio.to_numpy()[m],
                   color=style.color_for(i), s=22, label=f"U={u}")
    lo = min(float(np.min(pred)), float(sub.mean_ratio.min())) - 0.01
    ax.plot([lo, 1.005], [lo, 1.005], color="0.3", lw=0.9, ls=":", label="prediction = sim")
    ax.set_xlabel(r"predicted  $\log(1-f)\,/\,\log(1-f/\bar{q}_u)$  (measured $\bar{q}_u$)")
    ax.set_ylabel(r"simulated equilibrium $\hat{D}/D_{true}$")
    ax.set_title(r"$q \to q_u$ reduction: prediction vs simulation")
    ax.legend()
    return fig


def fig_recovery_vs_delay(cnt: pd.DataFrame) -> plt.Figure:
    # Right panel: the non-recovered waste share 1-r (log scale). Under joint countable
    # selection+counting the first-fork restriction acts at SELECTION (deep orphans are
    # never referenced), so counting-side rejections (deep_ref_share) are 0 and the
    # restriction shows up inside 1-r together with capacity losses.
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.8))
    us = [u for u in sorted(cnt["max_uncles"].unique()) if u > 0]
    for i, u in enumerate(us):
        a = cnt[cnt.max_uncles == u].sort_values(DELAY)
        denom = np.maximum(1.0 - a.mean_q.to_numpy(), 1e-12)
        r = (a.mean_q_eff.to_numpy() - a.mean_q.to_numpy()) / denom
        ax1.plot(a[DELAY], r, "-o", color=style.color_for(i), label=f"U={u}", ms=4)
        ax2.semilogy(a[DELAY], np.maximum(1.0 - r, 1e-4), "-o",
                     color=style.color_for(i), label=f"U={u}", ms=4)
    ax1.set_xlabel("max per-relay mixing delay (slots)")
    ax1.set_ylabel(r"measured recovery $r=(\bar{q}_u-\bar{q})/(1-\bar{q})$")
    ax1.set_ylim(0, 1.02)
    ax1.set_title("Uncle recovery rate")
    ax1.legend()
    ax2.set_xlabel("max per-relay mixing delay (slots)")
    ax2.set_ylabel(r"non-recovered waste share $1-r$")
    ax2.set_title("Residual (first-fork + capacity losses)")
    ax2.legend()
    return fig


def fig_absorption_window(absw: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots()
    eq = equilibrium(absw)
    agg = eq.groupby([DELAY, "window_absorption"], as_index=False).mean_ratio.mean()
    for i, d in enumerate(sorted(agg[DELAY].unique())):
        a = agg[agg[DELAY] == d].sort_values("window_absorption")
        ax.plot(a.window_absorption, a.mean_ratio, "-o", color=style.color_for(i),
                label=f"delay={d:g}", ms=4)
    ax.axhline(1.0, color="0.4", lw=0.8, ls=":")
    ax.set_xlabel("window absorption parameter W (expected block-intervals)")
    ax.set_ylabel(r"equilibrium $\hat{D}/D_{true}$")
    ax.set_title("Accuracy vs the derived uncle window $w_u = W/f$ (U=1)")
    ax.legend(title=None)
    return fig


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--countable", required=True, help="run dir of cvo-countable")
    ap.add_argument("--old", required=True, help="run dir of cvo-old")
    ap.add_argument("--absorption", required=True, help="run dir of absorption-window")
    ap.add_argument("--out", default="figures/countable-vs-old")
    args = ap.parse_args()
    style.apply_style()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cnt_raw, old_raw = _load(args.countable), _load(args.old)
    f = float(cnt_raw["f"].iloc[0])
    cnt, old = _eq(cnt_raw), _eq(old_raw)
    prov = "tsi-sim-pernode countable-vs-old.yaml (+--old) / absorption-window.yaml"

    written = []
    written += style.save(fig_accuracy_vs_delay(cnt, old), out / "cvo_accuracy_vs_delay", prov)
    written += style.save(fig_prediction_vs_sim(cnt, f), out / "cvo_prediction_vs_sim", prov)
    written += style.save(fig_recovery_vs_delay(cnt), out / "cvo_recovery_vs_delay", prov)
    written += style.save(fig_absorption_window(_load(args.absorption)),
                          out / "absorption_window", prov)
    # headline numbers for the report / analysis doc
    for u in sorted(cnt["max_uncles"].unique()):
        for _, row in cnt[cnt.max_uncles == u].sort_values(DELAY).iterrows():
            q, qu = row.mean_q, row.mean_q_eff
            r = (qu - q) / max(1.0 - q, 1e-12)
            o = old[(old.max_uncles == u) & (old[DELAY] == row[DELAY])]
            old_ratio = float(o.mean_ratio.iloc[0]) if len(o) else float("nan")
            print(f"U={u} delay={row[DELAY]:>5g}  countable={row.mean_ratio:.4f} "
                  f"old={old_ratio:.4f}  q={q:.4f} q_u={qu:.4f} r={r:.4f} "
                  f"pred={float(expected_ratio(f, qu)):.4f} "
                  f"deep={row.get('deep_ref_share', float('nan')):.4f}")
    print(f"wrote {len(written)} files -> {out}")


if __name__ == "__main__":
    main()
