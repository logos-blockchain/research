"""How much of the deeper-reference gain does re-rooting recover? (PLAN.md Phases 2b and 2d)

Reads a run of ``configs/reroot-overload-paired.yaml``: the spec 1.2.5 rule at depth 1, cousins
(depth 2), the ceiling (depth 0), and re-rooting arms at depth 1 (``reroot_share`` of the stake,
``reroot_delay`` slots from detection to publication), every arm on the same random streams.
Replicate *i* of each arm is therefore a matched pair.

Prints four tables, with the load rho from ``rho_for``:

1. accuracy, one row per (delay, U): the equilibrium D̂/D of every arm;
2. lost slots, one row per (delay, U): per arm, the occupied window slots its count misses whose
   shallowest block sits at depth 2, and at depth 3 or more (% of occupied slots);
3. re-rooting, one row per (delay, U, arm): the paired gaps to depth 1, depth 2 and the ceiling
   (mean ± SEM, |t|), the share of the depth-2 gain recovered, (arm − d1) / (d2 − d1), the slots
   only copies cover at depth 2 and at depth 3 or more and the copies made for window blocks
   (% of occupied slots), and the mean time from a copy's slot to its publication;
4. the depth-2 arm's wait (Phase 2d), one row per (delay, U): the equilibrium share of canonical
   window blocks with an entry whose parent is off the chain; and, over every epoch including the
   burn-in, the epochs in which a node receives such a block before such a parent, and the
   longest wait (slots). ``scripts/parent_wait_blocks.py`` lists those blocks.

The gaps of table 3 form one family. Its Bonferroni |t| threshold at 5 % (two-sided,
Student t with pairs − 1 degrees of freedom) is printed under it.

Run:  python scripts/reroot_analysis.py runs/<dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from tsi_sim.plotting.figures_pernode import equilibrium, rho_for, sem

DELAY = "blend_delay_max"
KEYS = [DELAY, "max_uncles", "replicate"]
ARM = ["uncle_depth", "reroot_share", "reroot_delay"]
D1, D2, CEIL = (1, 0.0, 0.0), (2, 0.0, 0.0), (0, 0.0, 0.0)


def _name(arm: tuple) -> str:
    depth, share, delay = arm
    if share > 0:
        return f"rr {share:g}/{delay:g}"
    return {1: "d1", 2: "d2", 0: "ceil"}.get(depth, f"d{depth}")


def _gap(arm: pd.DataFrame, ref: pd.DataFrame, col: str) -> tuple[float, float, float]:
    """Paired gap ``arm − ref`` in ``col``: mean, SEM and |t| (0 when every pair is equal)."""
    g = (arm[col] - ref[col].loc[arm.index]).to_numpy()
    se = sem(g)
    return g.mean(), se, abs(g.mean()) / se if se > 0 else (np.inf if g.any() else 0.0)


def tables(df: pd.DataFrame) -> tuple[list[pd.DataFrame], int, int]:
    eq = equilibrium(df)
    arms = sorted({tuple(r) for r in eq[ARM].itertuples(index=False)},
                  key=lambda a: (a[1] > 0, a[0] == 0, a[0], -a[1], a[2]))
    rr = [a for a in arms if a[1] > 0]
    delays = sorted(eq[DELAY].unique())
    rho = dict(zip(delays, rho_for(df, delays), strict=True))
    raw = df[(df.uncle_depth == D2[0]) & (df.reroot_share == 0.0)].groupby([DELAY, "max_uncles"])
    acc, lost, reroot, wait = [], [], [], []
    n_pairs = set()
    for (delay, cap), cell in eq.groupby([DELAY, "max_uncles"]):
        arm = {a: cell[(cell.uncle_depth == a[0]) & (cell.reroot_share == a[1])
                       & (cell.reroot_delay == a[2])].set_index(KEYS) for a in arms}
        n_pairs |= {len(x) for x in arm.values()}
        head = {"delay": delay, "rho": f"{rho[delay]:.2f}", "U": cap}
        acc.append({**head, **{_name(a): arm[a].mean_ratio.mean() for a in arms}})
        lost.append({**head, **{_name(a): "/".join(
            f"{100 * s.mean():.2f}"
            for s in (arm[a].lost_d2_share, arm[a].lost_d3_share + arm[a].lost_d4plus_share))
            for a in arms}})
        d1, d2 = arm[D1], arm[D2]
        gain = d2.mean_ratio.mean() - d1.mean_ratio.mean()
        for a in rr:
            row = {**head, "arm": _name(a)}
            for ref, tag in ((d1, "d1"), (d2, "d2"), (arm[CEIL], "ceil")):
                m, se, t = _gap(arm[a], ref, "mean_ratio")
                row[f"-{tag}"] = f"{m:+.4f}±{se:.4f}"
                row[f"-{tag} |t|"] = f"{t:.1f}"
            row["of d2 gain"] = f"{(arm[a].mean_ratio.mean() - d1.mean_ratio.mean()) / gain:.2f}"
            row["rerooted d2/d3+/made %"] = "/".join(
                f"{100 * arm[a][c].mean():.2f}"
                for c in ("rerooted_d2_share", "rerooted_d3plus_share", "reroot_made_share"))
            row["lag"] = f"{arm[a].reroot_lag_mean.mean():.1f}"
            reroot.append(row)
        r = raw.get_group((delay, cap))
        wait.append({**head,
                     "blocks %": f"{100 * d2.parent_wait_block_share.mean():.2f}",
                     "epochs with a wait": f"{(r.parent_wait_node_share > 0).sum()} / {len(r)}",
                     "longest wait": f"{r.parent_wait_max.max():.2f}"})
    assert len(n_pairs) == 1, "every arm must have the same replicates"
    n_tests = 3 * len(reroot)
    return [pd.DataFrame(t) for t in (acc, lost, reroot, wait)], n_tests, n_pairs.pop()


def main() -> None:
    run = Path(sys.argv[1])
    df = pd.read_parquet(run / "results.parquet")
    assert df.paired_streams.all(), "every arm must share its random streams"
    assert (df.deep_ref_share == 0.0).all(), "counting rejected an entry selection emitted"
    out, n_tests, n = tables(df)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    titles = ["accuracy: equilibrium D̂/D",
              "lost slots at depth 2 / depth >= 3 (% of occupied)",
              "re-rooting: paired gaps to depth 1, depth 2 and the ceiling, share of the depth-2 "
              "gain, slots (% of occupied), lag (slots)",
              "depth 2 (Phase 2d): blocks with an off-chain parent (%), epochs in which a node "
              "waits, longest wait (slots)"]
    for title, table in zip(titles, out, strict=True):
        print(f"\n== {title}")
        print(table.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
        if title.startswith("re-rooting"):
            thr = stats.t.ppf(1 - 0.025 / n_tests, n - 1)
            print(f"Bonferroni |t| threshold for {n_tests} gaps at 5 % ({n} pairs): {thr:.2f}")


if __name__ == "__main__":
    main()
