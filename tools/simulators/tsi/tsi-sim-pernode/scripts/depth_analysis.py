"""What do deeper references recover? (PLAN.md Phase 2)

Reads a run of one of the ``configs/depth-*-paired.yaml`` sweeps: the spec 1.2.5 rule at
``uncle_depth`` 1 against deeper arms (2 cousins, 3 children of cousins, 0 the ceiling), with
every arm on the same random streams. Replicate *i* of each arm is therefore a matched pair.

Prints three tables, one row per (delay, U), with the load rho from ``rho_for``:

1. accuracy: the equilibrium D̂/D of every arm; for each deeper arm, the mean paired gap
   ``arm − depth 1`` with its SEM and |t|, and the number of bit-identical pairs (U = 0 must be
   identical in every pair);
2. steps (three or more arms): the paired gap between every two deeper arms (depth 3 over 2,
   the ceiling over 2 and over 3);
3. lost slots: the shares each arm leaves, in % of occupied slots (``fork.lost_slots``,
   depth 1/2/3/≥4), and the paired change in depth-1 loss against depth 1.

Each table's U ≥ 1 gaps form one family. Its Bonferroni |t| threshold at 5 % (two-sided,
Student t with pairs − 1 degrees of freedom) is printed under it.

Run:  python scripts/depth_analysis.py runs/<dir>
"""

from __future__ import annotations

import sys
from itertools import combinations
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from tsi_sim.plotting.figures_pernode import equilibrium, rho_for, sem

DELAY = "blend_delay_max"
KEYS = [DELAY, "max_uncles", "replicate"]
LOST = ["lost_d1_share", "lost_d2_share", "lost_d3_share", "lost_d4plus_share"]
NAME = {1: "d1", 2: "d2", 3: "d3", 0: "ceil"}


def _gap(arm: pd.DataFrame, ref: pd.DataFrame, col: str) -> tuple[float, float, float, int]:
    """Paired gap ``arm − ref`` in ``col``: mean, SEM, |t| and the bit-identical pairs."""
    g = (arm[col] - ref[col].loc[arm.index]).to_numpy()
    se = sem(g)
    return g.mean(), se, abs(g.mean()) / se if se > 0 else np.nan, int((g == 0.0).sum())


def tables(df: pd.DataFrame) -> tuple[list[pd.DataFrame], list[int], int]:
    eq = equilibrium(df)
    depths = sorted(eq.uncle_depth.unique(), key=lambda d: (d == 0, d))
    assert depths[0] == 1, "depth 1 is the reference arm"
    delays = sorted(eq[DELAY].unique())
    rho = dict(zip(delays, rho_for(df, delays), strict=True))
    acc, step, lost = [], [], []
    n_tests = [0, 0, 0]
    n_pairs = set()
    for (delay, cap), cell in eq.groupby([DELAY, "max_uncles"]):
        arm = {d: cell[cell.uncle_depth == d].set_index(KEYS) for d in depths}
        n_pairs |= {len(a) for a in arm.values()}
        head = {"delay": delay, "rho": f"{rho[delay]:.2f}", "U": cap}
        a, s, lo = dict(head), dict(head), dict(head)
        for d in depths:
            a[NAME[d]] = arm[d].mean_ratio.mean()
            lo[NAME[d]] = "/".join(f"{100 * arm[d][c].mean():.2f}" for c in LOST)
        for d in depths[1:]:
            m, se, t, same = _gap(arm[d], arm[1], "mean_ratio")
            a[f"{NAME[d]}-d1"] = f"{m:+.4f}±{se:.4f}"
            a[f"{NAME[d]} |t|"] = f"{t:.1f}"
            a[f"{NAME[d]} same"] = f"{same}/{len(arm[d])}"
            m, se, t, _ = _gap(arm[d], arm[1], "lost_d1_share")
            lo[f"{NAME[d]} Δd1 pp"] = f"{100 * m:+.3f}±{100 * se:.3f}"
            lo[f"{NAME[d]} |t|"] = f"{t:.1f}"
        for prev, d in combinations(depths[1:], 2):
            m, se, t, _ = _gap(arm[d], arm[prev], "mean_ratio")
            s[f"{NAME[d]}-{NAME[prev]}"] = f"{m:+.4f}±{se:.4f}"
            s[f"{NAME[d]}-{NAME[prev]} |t|"] = f"{t:.1f}"
        if cap > 0:
            n_tests[0] += len(depths) - 1
            n_tests[1] += comb(len(depths) - 1, 2)
            n_tests[2] += len(depths) - 1
        acc.append(a)
        step.append(s)
        lost.append(lo)
    assert len(n_pairs) == 1, "every arm must have the same replicates"
    return [pd.DataFrame(t) for t in (acc, step, lost)], n_tests, n_pairs.pop()


def main() -> None:
    run = Path(sys.argv[1])
    df = pd.read_parquet(run / "results.parquet")
    assert df.paired_streams.all(), "every arm must share its random streams"
    assert (df.deep_ref_share == 0.0).all(), "counting rejected an entry selection emitted"
    out, n_tests, n = tables(df)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    titles = ["accuracy: equilibrium D̂/D, and paired gap to depth 1",
              "steps: paired gap between the deeper arms",
              "lost slots, % of occupied (depth 1/2/3/>=4), and paired change in depth-1 loss"]
    for title, table, k in zip(titles, out, n_tests, strict=True):
        if k == 0 and title.startswith("steps"):
            continue
        print(f"\n== {title}")
        print(table.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
        if k:
            thr = stats.t.ppf(1 - 0.025 / k, n - 1)
            print(f"Bonferroni |t| threshold for {k} U >= 1 gaps at 5 % ({n} pairs): {thr:.2f}")


if __name__ == "__main__":
    main()
