"""The block-rewards baseline figure, the visual behind UPSTREAM-PENDING §6.

One figure, one claim: Figure 11's curve is reproduced by netting the emission against a
constant 0.5% burn, and the same paths run through equation (1) end ten years at 3.5%. Both
come from `baseline.run`, the run the gate suite checks; this module only draws it.

    PYTHONPATH=src python3 -m empowering_sim.plots_baseline
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import baseline
from .plots_emission import BLUE, INK, INK_2, SURFACE, _style

ORANGE = "#eb6834"      # categorical slot 2, after BLUE


def supply_paths(out: Path) -> Path:
    r = baseline.run(baseline.Params())
    t = np.arange(r.params.steps + 1) / r.params.steps_per_year
    fig11 = np.loadtxt(baseline.FIG11_SUPPLY, delimiter=",", comments="#")

    f, ax = plt.subplots(1, 1, figsize=(8.4, 4.6))
    f.patch.set_facecolor(SURFACE)
    burn = f"{100 * r.params.pooling_rate:g}%"
    series = [("drawn", BLUE, f"netted against a constant {burn} burn (Figure 11's accounting)"),
              ("minting", ORANGE, "equation (1): minting (1.0.0), or pooling over S_cap (1.1.0 on)")]
    for reading, colour, label in series:
        paths = np.c_[np.ones(r.params.seeds), r.supply[reading]]
        lo, hi = np.percentile(paths, [5, 95], axis=0)
        ax.fill_between(t, lo, hi, color=colour, alpha=0.12, linewidth=0, zorder=2)
        ax.plot(t, paths.mean(axis=0), color=colour, linewidth=1.8, zorder=4, label=label)
        ax.annotate(f"{r.mean(reading):.4f}", xy=(t[-1], r.mean(reading)),
                    xytext=(6, 0), textcoords="offset points", va="center",
                    color=INK_2, fontsize=8.5)
    ax.plot(fig11[:, 0], fig11[:, 1], color=INK, linewidth=1.0, zorder=5,
            label=f"published Figure 11, digitized (ends at {baseline.PUBLISHED_FINAL})")
    ax.axhline(1.0, color=INK_2, linewidth=0.8, linestyle=(0, (2, 2)), zorder=1)
    ax.set_xlim(0, r.params.years)
    ax.set_ylim(0.997, 1.04)
    ax.set_xlabel("years", color=INK_2, fontsize=9)
    ax.set_ylabel("normalized supply", color=INK_2, fontsize=9)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", labelcolor=INK_2)
    _style(ax, "", f"{r.params.seeds} seeds on Figure 9's paths, the baseline's parameters; "
                   "bands are 5–95% across seeds")
    f.suptitle(f"The 1.33% baseline, reproduced: equation (1) ends ten years at "
               f"{100 * (r.mean('minting') - 1):.1f}%",
               color=INK, fontsize=12.5, x=0.008, ha="left", y=0.985)
    f.tight_layout(rect=(0, 0, 0.97, 0.92))
    p = out / "baseline_supply.png"
    f.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(f)
    return p


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="empowering_sim.plots_baseline")
    ap.add_argument("--out", default="../../../../reports/empowering/figures")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"  wrote {supply_paths(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
