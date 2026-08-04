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
  cvo_recovery_vs_delay      measured recovery r = (q_eff - q)/(1 - q) and the non-recovered
                             waste share 1-r vs delay. (NOT deep_ref_share: under joint
                             countable selection+counting that is identically 0 — the
                             first-fork restriction acts at selection, so it shows up
                             inside 1-r alongside capacity losses.)
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
from tsi_sim.plotting.figures_pernode import equilibrium, recovery_rate, sem
from tsi_sim.theory import expected_ratio, q_effective

DELAY = "blend_delay_max"


def _load(run_dir: str | Path) -> pd.DataFrame:
    return pd.read_parquet(Path(run_dir) / "results.parquet")


def _eq(df: pd.DataFrame, extra_cols: tuple[str, ...] = ()) -> pd.DataFrame:
    """Equilibrium (post-burn) per (delay, U) cell: replicate mean, SEM and count.

    ``equilibrium`` returns one row per (config, replicate); the spread across those
    replicates is the only uncertainty estimate available, and at high delay it is large
    enough to swamp the model difference — so every consumer here carries it.
    """
    eq = equilibrium(df)
    keys = [DELAY, "max_uncles", *extra_cols]
    agg = {"mean_ratio": ("mean_ratio", "mean"),
           "sem_ratio": ("mean_ratio", sem),
           "n_rep": ("mean_ratio", "size"),
           "mean_q": ("mean_q", "mean"),
           "mean_q_eff": ("mean_q_eff", "mean")}
    return eq.groupby(keys, as_index=False).agg(**agg)


def fig_accuracy_vs_delay(cnt: pd.DataFrame, old: pd.DataFrame) -> plt.Figure:
    """Accuracy vs delay per U, with replicate SEM bars.

    U=0 is the NEGATIVE CONTROL: with no uncles the two models are identical by
    construction, so the visible countable-vs-old gap on that pair of curves is pure
    between-run RNG noise and calibrates what a real difference has to beat.
    """
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    us = sorted(cnt["max_uncles"].unique())
    for i, u in enumerate(us):
        c = style.color_for(i)
        a = cnt[cnt.max_uncles == u].sort_values(DELAY)
        b = old[old.max_uncles == u].sort_values(DELAY)
        ctl = " (control)" if u == 0 else ""
        ax.errorbar(a[DELAY], a.mean_ratio, yerr=a.sem_ratio, fmt="-o", color=c,
                    label=f"U={u} countable{ctl}", ms=4, capsize=2, lw=1.2)
        ax.errorbar(b[DELAY], b.mean_ratio, yerr=b.sem_ratio, fmt="--s", color=c,
                    label=f"U={u} unrestricted{ctl}", ms=4, capsize=2, alpha=0.75, lw=1.2)
    ax.axhline(1.0, color="0.4", lw=0.8, ls=":")
    ax.set_xlabel("max per-relay mixing delay (slots)")
    ax.set_ylabel(r"equilibrium $\hat{D}/D_{true}$")
    ax.set_title("Accuracy vs delay: countable (solid) vs unrestricted (dashed) referencing")
    ax.legend(ncol=2, fontsize="x-small")
    return fig


def fig_prediction_vs_sim(cnt: pd.DataFrame, f: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    sub = cnt[cnt.max_uncles > 0]
    # Reconstruct q_u through the theory identity the report quotes, q_u = q + (1-q) r,
    # rather than reading mean_q_eff straight off the parquet: the figure then exercises
    # the same closed form the text claims.
    r = recovery_rate(sub.mean_q.to_numpy(), sub.mean_q_eff.to_numpy())
    pred = expected_ratio(f, q_effective(sub.mean_q.to_numpy(), r))
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
        r = recovery_rate(a.mean_q.to_numpy(), a.mean_q_eff.to_numpy())
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
    """Accuracy vs the derived window, with replicate SEM bars.

    The bars matter here: at the 32-slot delay the run-to-run spread is the dominant
    feature (replicate sd up to ~0.22), so that curve's shape is not interpretable as a
    trend — only its ceiling is, and the ceiling is set by U=1, not by the window.
    """
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    eq = equilibrium(absw)
    agg = eq.groupby([DELAY, "window_absorption"], as_index=False).agg(
        mean_ratio=("mean_ratio", "mean"), sem_ratio=("mean_ratio", sem))
    for i, d in enumerate(sorted(agg[DELAY].unique())):
        a = agg[agg[DELAY] == d].sort_values("window_absorption")
        ax.errorbar(a.window_absorption, a.mean_ratio, yerr=a.sem_ratio, fmt="-o",
                    color=style.color_for(i), label=f"delay={d:g}", ms=4, capsize=2, lw=1.2)
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
    # Headline numbers for the report. Every countable-vs-old gap is printed with the
    # two-sample t = |diff| / SE(diff) over replicates; |t| < 2 means the cell does NOT
    # resolve a model difference at this replicate count and must not be read as one.
    # The U=0 rows are the negative control (models identical by construction, so their
    # t is a pure noise reading).
    print(f"{'cell':<14} {'countable':>17} {'old':>17} {'diff':>9} {'t':>6}  verdict")
    for u in sorted(cnt["max_uncles"].unique()):
        for _, row in cnt[cnt.max_uncles == u].sort_values(DELAY).iterrows():
            q, qu = row.mean_q, row.mean_q_eff
            r = float(recovery_rate(q, qu))
            o = old[(old.max_uncles == u) & (old[DELAY] == row[DELAY])]
            if not len(o):
                continue
            orow = o.iloc[0]
            diff = row.mean_ratio - orow.mean_ratio
            se = float(np.hypot(row.sem_ratio, orow.sem_ratio))
            t = abs(diff) / se if se > 0 else float("inf")
            verdict = ("CONTROL (must be 0)" if u == 0 else
                       "resolved" if t >= 2 else "NOT RESOLVED (noise)")
            print(f"U={u} delay={row[DELAY]:>5g}  "
                  f"{row.mean_ratio:.4f}+-{row.sem_ratio:.4f}  "
                  f"{orow.mean_ratio:.4f}+-{orow.sem_ratio:.4f}  "
                  f"{diff:+.4f} {t:6.2f}  {verdict}")
            print(f"{'':>14}   q={q:.4f} q_u={qu:.4f} r={r:.4f} "
                  f"pred={float(expected_ratio(f, q_effective(q, r))):.4f} "
                  f"n_rep={int(row.n_rep)}")
    print(f"wrote {len(written)} files -> {out}")


if __name__ == "__main__":
    main()
