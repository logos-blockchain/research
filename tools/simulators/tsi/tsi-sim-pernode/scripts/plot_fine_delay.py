"""High-precision figures for the LOW mixing-delay band (the design regime).

countable-vs-old.yaml samples delay at 4/8/16/32 with 5 replicates. That resolves the
overload regime but leaves the design regime under-measured: every countable-vs-unrestricted
gap at delay <= 8 sits inside the replicate noise there, so the only honest statement is
"no difference detected" — with no bound on how large an undetected difference could be.

fine-delay.yaml spends replicates instead of range (delay 1..5, 40 replicates) to turn that
into a real bound. Consumes:

  tsi-sweep --config configs/fine-delay.yaml --label fine-countable
  tsi-sweep --config configs/fine-delay.yaml --old --label fine-old

and renders (into --out):

  fine_accuracy_vs_delay   equilibrium D/D_true vs delay 1..5, countable (solid) vs
                           unrestricted (dashed) per U, replicate-SEM bars.
  fine_gap_vs_delay        THE precision figure: the countable - unrestricted gap with 95%
                           CIs, against the U=0 negative-control band. A CI straddling zero
                           means no difference at this power; the band shows the floor.

Usage:
  python scripts/plot_fine_delay.py --countable RUNDIR --old RUNDIR \
      --out figures/fine-delay
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tsi_sim.plotting import style
from tsi_sim.plotting.figures_pernode import equilibrium, sem

DELAY = "blend_delay_max"
# Normal approximation: with 40 replicates per arm the t-quantile is within ~2% of 1.96,
# and the replicate spread itself is the dominant uncertainty, so 1.96 is precise enough.
Z95 = 1.96


def _load(run_dir: str | Path) -> pd.DataFrame:
    return pd.read_parquet(Path(run_dir) / "results.parquet")


def _cells(df: pd.DataFrame) -> pd.DataFrame:
    """Per (delay, U): replicate mean, SEM and count of the equilibrium accuracy."""
    return equilibrium(df).groupby([DELAY, "max_uncles"], as_index=False).agg(
        mean_ratio=("mean_ratio", "mean"),
        sem_ratio=("mean_ratio", sem),
        n_rep=("mean_ratio", "size"),
        mean_q=("mean_q", "mean"),
        mean_q_eff=("mean_q_eff", "mean"))


def gaps(cnt: pd.DataFrame, old: pd.DataFrame) -> pd.DataFrame:
    """countable - unrestricted per cell, with the unpaired SE and 95% CI half-width."""
    m = cnt.merge(old, on=[DELAY, "max_uncles"], suffixes=("_c", "_o"))
    m["gap"] = m.mean_ratio_c - m.mean_ratio_o
    m["se"] = np.hypot(m.sem_ratio_c, m.sem_ratio_o)
    m["ci95"] = Z95 * m.se
    m["t"] = np.where(m.se > 0, np.abs(m.gap) / m.se.replace(0, np.nan), np.inf)
    return m.sort_values(["max_uncles", DELAY])


def fig_accuracy(cnt: pd.DataFrame, old: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for i, u in enumerate(sorted(cnt["max_uncles"].unique())):
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
    ax.set_title("Design-regime accuracy: countable vs unrestricted referencing")
    ax.legend(ncol=2, fontsize="x-small")
    return fig


def pooled_by_delay(g: pd.DataFrame) -> pd.DataFrame:
    """Inverse-variance pooled gap across the U >= 1 arms, per delay.

    Individual cells are underpowered against a sub-0.1 % effect even at 40 replicates, but
    the three uncle caps are independent measurements of the same underlying difference, so
    pooling them buys back a factor of ~sqrt(3) and is what actually resolves the trend.
    """
    u = g[g.max_uncles > 0]
    rows = []
    for d, s in u.groupby(DELAY):
        w = 1.0 / s.se.to_numpy() ** 2
        p = float((s.gap.to_numpy() * w).sum() / w.sum())
        e = float(np.sqrt(1.0 / w.sum()))
        rows.append({DELAY: d, "gap": p, "se": e, "ci95": Z95 * e,
                     "t": abs(p) / e if e > 0 else np.inf})
    return pd.DataFrame(rows).sort_values(DELAY)


def fig_gap(g: pd.DataFrame) -> plt.Figure:
    """The countable − unrestricted gap with 95% CIs, zoomed to the U >= 1 scale.

    The U=0 negative control is NOT plotted as a band here: with no uncles the models are
    identical by construction, but the unrecovered regime is so noisy that its CI (±0.025)
    is ~17x the entire range of the U >= 1 gaps and would fill the axes. Its magnitude is
    annotated instead — the point being that the control's noise floor lives far outside
    anything the uncle arms show, so those arms are measuring signal, not spread.
    """
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    pooled = pooled_by_delay(g)
    for i, u in enumerate(sorted(g["max_uncles"].unique())):
        if u == 0:
            continue
        a = g[g.max_uncles == u].sort_values(DELAY)
        ax.errorbar(a[DELAY], a.gap, yerr=a.ci95, fmt="-o", color=style.color_for(i),
                    label=f"U={u}", ms=4, capsize=3, lw=1.0, alpha=0.75)
    ax.errorbar(pooled[DELAY], pooled.gap, yerr=pooled.ci95, fmt="-D", color="0.15",
                label="pooled over U≥1", ms=5, capsize=4, lw=1.8, zorder=5)
    ax.axhline(0.0, color="0.3", lw=0.9, ls=":")
    ax.set_xlabel("max per-relay mixing delay (slots)")
    ax.set_ylabel(r"$\hat{D}/D$ gap:  countable $-$ unrestricted")
    ax.set_title("The first-fork cost across the design band (95% CI)")
    ctl = g[g.max_uncles == 0]
    if len(ctl):
        band = float(ctl.ci95.max())
        span = float(np.abs(np.r_[g[g.max_uncles > 0].gap + g[g.max_uncles > 0].ci95,
                                  g[g.max_uncles > 0].gap - g[g.max_uncles > 0].ci95]).max())
        ax.set_ylim(-1.35 * span, 1.35 * span)
        ax.text(0.015, 0.03,
                f"U=0 negative control (true gap = 0): 95% CI ±{band:.4f}, "
                f"{band / span:.0f}× outside this range",
                transform=ax.transAxes, fontsize=6.5, alpha=0.75)
    ax.legend(fontsize="x-small", ncol=2)
    return fig


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--countable", required=True, help="run dir of fine-countable")
    ap.add_argument("--old", required=True, help="run dir of fine-old")
    ap.add_argument("--out", default="figures/fine-delay")
    args = ap.parse_args()
    style.apply_style()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cnt, old = _cells(_load(args.countable)), _cells(_load(args.old))
    g = gaps(cnt, old)
    prov = "tsi-sim-pernode fine-delay.yaml (+--old)"

    written = []
    written += style.save(fig_accuracy(cnt, old), out / "fine_accuracy_vs_delay", prov)
    written += style.save(fig_gap(g), out / "fine_gap_vs_delay", prov)

    print(f"{'cell':<16} {'countable':>17} {'unrestricted':>17} "
          f"{'gap':>9} {'95% CI':>9} {'t':>6}  verdict")
    for _, r in g.iterrows():
        verdict = ("CONTROL (true gap = 0)" if r.max_uncles == 0 else
                   "resolved" if r.t >= 2 else "no difference resolved")
        print(f"U={int(r.max_uncles)} delay={r[DELAY]:>5g}  "
              f"{r.mean_ratio_c:.4f}+-{r.sem_ratio_c:.4f}  "
              f"{r.mean_ratio_o:.4f}+-{r.sem_ratio_o:.4f}  "
              f"{r.gap:+.4f}  +-{r.ci95:.4f} {r.t:6.2f}  {verdict}")
    worst = g[g.max_uncles > 0]
    print(f"\nn_rep = {int(g.n_rep_c.min())}/{int(g.n_rep_o.min())} per arm")
    print(f"widest 95% CI half-width at U>=1: +-{worst.ci95.max():.4f} "
          f"({100 * worst.ci95.max():.2f} pp)")
    # Per-cell significance must be read against the number of cells tested: with 15 cells,
    # ~0.75 are expected to clear t=2 by chance alone, so quote the Bonferroni threshold.
    bonf = 2.935 if len(worst) == 15 else float("nan")
    print(f"per-cell: {int((worst.t >= 2).sum())}/{len(worst)} cells with t>=2 "
          f"(expected by chance {0.05 * len(worst):.2f}); max t = {worst.t.max():.2f} "
          f"vs Bonferroni threshold {bonf:.3f}")

    print("\npooled over U>=1 (the three caps measure the same difference):")
    pooled = pooled_by_delay(g)
    for _, r in pooled.iterrows():
        mark = "  <-- resolved" if r.t >= 2 else ""
        print(f"  delay={r[DELAY]:>4g}: {r.gap:+.5f} +-{r.ci95:.5f}  t={r.t:5.2f}{mark}")
    w = 1.0 / worst.se.to_numpy() ** 2
    allp = float((worst.gap.to_numpy() * w).sum() / w.sum())
    alle = float(np.sqrt(1.0 / w.sum()))
    print(f"  whole band: {allp:+.5f} +-{Z95 * alle:.5f}  t={abs(allp) / alle:.2f}")

    ctl = g[g.max_uncles == 0]
    if len(ctl):
        print(f"\nU=0 negative control (true gap = 0): |gap| up to {ctl.gap.abs().max():.4f}, "
              f"max t = {ctl.t.max():.2f}, 95% CI +-{ctl.ci95.max():.4f} "
              f"-> control {'PASSES' if ctl.t.max() < 2 else 'FAILS'}")
    print(f"wrote {len(written)} files -> {out}")


if __name__ == "__main__":
    main()
