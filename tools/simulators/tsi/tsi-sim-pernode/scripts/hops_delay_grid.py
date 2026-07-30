"""fig3 — uncle recovery under the Blend cascade: hops × per-hop delay × U (4-panel grid).

Committed generator for report fig3. Previously fig3 was produced ad hoc (via make_figures on the
blend-hops-delay run, then hand-copied into report-figures/) and had NO reproducible source in the
repo; this script closes that gap. Per uncle cap U it plots mean D̂/D vs the per-hop budget δ_max,
one curve per hop count, at N=1000 from the canonical blend-hops-delay sweep (per-trajectory 50%
burn-in via figures_pernode.equilibrium). Accuracy is bounded by 1 (slot-counting cannot over-count
occupied slots), so the y-axis is capped at the exact-recovery bound — no above-1 headroom.

Run:  python scripts/hops_delay_grid.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsi_sim.plotting import style  # noqa: E402
from tsi_sim.plotting.figures_pernode import equilibrium  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"


def main() -> None:
    import matplotlib.pyplot as plt
    src = sorted(RUNS.glob("*_blend-hops-delay/results.parquet"))[-1]
    eq = equilibrium(pd.read_parquet(src))
    eq = eq[(eq.n_nodes == 1000) & (eq.topology == "blend") & (eq.stake_dist == "pareto")]
    us = sorted(eq.max_uncles.unique())
    hops = sorted(eq.blend_hops.unique())
    style.apply_style()
    fig, axes = plt.subplots(1, len(us), figsize=(3.2 * len(us), 3.6), sharey=True)
    for ax, U in zip(axes, us, strict=True):
        s = eq[eq.max_uncles == U]
        for i, h in enumerate(hops):
            g = s[s.blend_hops == h].groupby("blend_delay_max").mean_ratio.agg(["mean", "sem"])
            ax.errorbar(g.index, g["mean"], yerr=g["sem"], fmt="-o", ms=4, capsize=2,
                        color=style.OKABE_ITO[i], label=f"{int(h)} hops")
        ax.axhline(1.0, color="0.4", lw=1.0, ls="--", zorder=0)
        ax.axhline(0.98, color="0.75", lw=0.8, ls=":", zorder=0)
        ax.set_title(f"U = {int(U)}")
        ax.set_xlabel(r"per-hop budget $\delta_{max}$ (s)")
    axes[0].set_ylabel(r"mean $\hat D / D$")
    axes[0].set_ylim(top=1.01)   # bounded by 1: cap at the exact-recovery bound
    axes[0].legend(fontsize=8, loc="lower left")
    fig.suptitle(r"Uncle recovery under Blend cascade: hops × per-hop delay × U "
                 r"(pareto, N=1000, f=1/30)", y=1.02)
    style.save(fig, FIGS / "fig3_hops_delay", provenance="scripts/hops_delay_grid.py")
    plt.close(fig)
    print("wrote fig3_hops_delay")


if __name__ == "__main__":
    main()
