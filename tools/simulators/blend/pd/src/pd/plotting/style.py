"""Shared academic matplotlib theme, palette, and helpers (copied from tsi-sim-mc).

Palette: Okabe-Ito — the standard colorblind-safe qualitative set — for categorical
series; ``cividis`` (perceptually uniform, CVD-safe) for heatmaps. Figures are saved as
300-dpi PNG.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# Okabe-Ito colorblind-safe qualitative palette
OKABE_ITO = [
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#000000",  # black
]
SEQUENTIAL_CMAP = "cividis"
DIVERGING_CMAP = "RdBu_r"


def apply_style() -> None:
    """Install the shared rcParams theme (idempotent)."""
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "figure.figsize": (6.4, 4.0),
            "font.size": 10,
            "font.family": "sans-serif",
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.6,
            "legend.frameon": False,
            "legend.fontsize": 8.5,
            "lines.linewidth": 1.8,
            "axes.prop_cycle": mpl.cycler(color=OKABE_ITO),
            "mathtext.default": "regular",
        }
    )


def color_for(index: int) -> str:
    return OKABE_ITO[index % len(OKABE_ITO)]


def band_plot(
    ax: plt.Axes,
    x: Sequence[float],
    series: np.ndarray,
    *,
    color: str,
    label: str | None = None,
    percentiles: tuple[float, float] = (10, 90),
) -> None:
    """Plot the mean of ``series`` (shape ``(n_replicates, len(x))``) with a percentile band."""
    x = np.asarray(x, dtype=float)
    mean = np.nanmean(series, axis=0)
    lo = np.nanpercentile(series, percentiles[0], axis=0)
    hi = np.nanpercentile(series, percentiles[1], axis=0)
    ax.plot(x, mean, color=color, label=label)
    ax.fill_between(x, lo, hi, color=color, alpha=0.18, linewidth=0)


def save(fig: plt.Figure, out_stem: str | Path, provenance: str | None = None) -> list[Path]:
    """Save ``fig`` as a 300-dpi PNG. ``out_stem`` has no suffix. Returns written paths."""
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    if provenance:
        fig.subplots_adjust(bottom=0.16)
        fig.text(0.99, 0.005, provenance, fontsize=6, alpha=0.5, va="bottom", ha="right")
    p = out_stem.with_suffix(".png")
    fig.savefig(p)
    plt.close(fig)
    return [p]
