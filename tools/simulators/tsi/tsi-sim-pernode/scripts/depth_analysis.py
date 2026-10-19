"""What do deeper references recover? (PLAN.md Phase 2)

Reads a run of one of the ``configs/depth-*-paired.yaml`` sweeps: the spec 1.2.5 rule at
``uncle_depth`` 1 against deeper arms (2 cousins, 3 children of cousins, 0 the ceiling), with
every arm on the same random streams. Replicate *i* of each arm is therefore a matched pair.

Prints, per (delay, U):

* the equilibrium D̂/D of every arm;
* for each deeper arm, the mean paired gap ``arm − depth 1`` with its SEM and |t|, and the
  number of pairs that are bit-identical (U = 0 must be identical in every pair);
* the lost-slot shares each arm leaves, in % of occupied slots (``fork.lost_slots``).

The Bonferroni threshold for the printed cells is given at the end.

Run:  python scripts/depth_analysis.py runs/<dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from tsi_sim.plotting.figures_pernode import equilibrium, sem

KEYS = ["blend_delay_max", "max_uncles", "replicate"]
LOST = ["lost_d1_share", "lost_d2_share", "lost_d3_share", "lost_d4plus_share"]
NAME = {1: "d1", 2: "d2", 3: "d3", 0: "ceil"}


def table(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    eq = equilibrium(df)
    depths = sorted(eq.uncle_depth.unique(), key=lambda d: (d == 0, d))
    base = eq[eq.uncle_depth == 1].set_index(KEYS)
    rows = []
    n_tests = 0
    for (delay, cap), cell in eq.groupby(["blend_delay_max", "max_uncles"]):
        row = {"delay": delay, "U": cap}
        for d in depths:
            arm = cell[cell.uncle_depth == d].set_index(KEYS)
            row[f"{NAME[d]}"] = arm.mean_ratio.mean()
            row[f"{NAME[d]} lost%"] = "/".join(f"{100 * arm[c].mean():.2f}" for c in LOST)
            if d == 1:
                continue
            gap = (arm.mean_ratio - base.mean_ratio.loc[arm.index]).to_numpy()
            se = sem(gap)
            row[f"{NAME[d]}-d1"] = gap.mean()
            row[f"{NAME[d]} se"] = se
            row[f"{NAME[d]} |t|"] = abs(gap.mean()) / se if se > 0 else np.nan
            row[f"{NAME[d]} same"] = f"{int((gap == 0.0).sum())}/{len(gap)}"
            n_tests += cap > 0
        rows.append(row)
    return pd.DataFrame(rows), n_tests


def main() -> None:
    run = Path(sys.argv[1])
    df = pd.read_parquet(run / "results.parquet")
    assert df.paired_streams.all(), "every arm must share its random streams"
    out, n_tests = table(df)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    print(out.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    if n_tests:
        thr = stats.norm.ppf(1 - 0.025 / n_tests)
        print(f"\nlost% columns: depth 1/2/3/>=4. Bonferroni |t| threshold for {n_tests} U >= 1 "
              f"gaps at 5 %: {thr:.2f}")


if __name__ == "__main__":
    main()
