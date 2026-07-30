"""Render the per-node simulator figure TYPES that the report was missing (fig17-fig22, plus fig5).

Each comes from an existing ``figures_pernode`` function on committed sweep data, so the report
includes and discusses every figure the simulator generates (§3). The bootstrap type
(``block_production_stabilization``) is fig1, rendered by scripts/bootstrap_dynamics.py. To run:
  python scripts/regenerate_extra_figs.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tsi_sim.plotting import figures_pernode as F
from tsi_sim.plotting import style

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"

# Large-scale source: the N=10000 fullscale run (also holds N-scaling context via §3.2 table).
FULL = sorted(RUNS.glob("2026-07-2*_fullscale/results.parquet"))[-1]
HET = sorted(RUNS.glob("2026-07-2*_default/results.parquet"))[-1]
WIN = sorted(RUNS.glob("2026-07-2*_uncle-window/results.parquet"))[-1]
WU = sorted(RUNS.glob("2026-07-2*_window-uncles/results.parquet"))[-1]


def main() -> None:
    full = pd.read_parquet(FULL)
    het = pd.read_parquet(HET)
    win = pd.read_parquet(WIN)
    wu = pd.read_parquet(WU)

    jobs = [
        ("fig2_uncle_recovery", F.accuracy_vs_u(full, "pareto", "blend")),
        ("fig4_window", F.accuracy_vs_uncle_window(win, "pareto", "blend")),
        ("fig17_divergence", F.divergence_vs_epoch(full, "pareto", "blend")),
        ("fig18_tip_agreement", F.tip_agreement_vs_latency(full, "pareto", "blend")),
        ("fig19_accuracy_vs_latency", F.accuracy_vs_link_latency(full, "pareto", "regular")),
        ("fig20_heatmap_accuracy", F.heatmap_accuracy(full, "pareto", 6, "blend")),
        ("fig21_heterogeneous_recovery", F.heterogeneous_recovery(het, "uniform", "regular")),
        ("fig22_heatmap_window_delay", F.heatmap_window_delay(win, "pareto", "blend")),
        # fig5 (W x U safe region at one delay): the (window x uncles) sweep, blend, delay=16 s
        # (the delay the report's §3.5 "W=100, U=4 -> 0.96" callout reads off).
        ("fig5_window_uncles", F.heatmap_window_uncles(wu, "pareto", 16.0, "blend")),
    ]
    for stem, fig in jobs:
        if fig is None:
            print(f"SKIP {stem} (no data)")
            continue
        style.save(fig, FIGS / stem, provenance="scripts/regenerate_extra_figs.py")
        print(f"wrote {stem}")


if __name__ == "__main__":
    main()
