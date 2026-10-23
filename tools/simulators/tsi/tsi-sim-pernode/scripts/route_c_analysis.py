"""What does route C count? (PLAN.md Phase 2c)

Route C verifies a reference against the stake snapshot alone, so the simulator counts it at any
depth, with the window measured to the entry's own slot: ``uncle_depth = 0``,
``uncle_window_anchor = "uncle"`` and ``uncle_order = "uncle"`` (arm ``C``). Every arm shares its
random streams, so replicate *i* of each arm is a matched pair.

``honest`` reads a run of ``configs/routec-<grid>-paired.yaml`` and the other runs of the same
grid: the Phase 2 run (depth 1, 2, 3 and the ceiling, whose window is measured to the fork
point), the run of ``configs/routec-order-<grid>-paired.yaml`` (``C/fp``: route C's window, with
entries taken by their fork point first, as the ceiling takes them) and, on the overload grid,
the Phase 2b run (re-rooting, ``rr share/delay``). An arm that two runs hold must agree in every
column both record; the first copy is kept. It prints one row per (delay, U ≥ 1), with the load
rho from ``rho_for``:

1. accuracy: the equilibrium D̂/D of every depth arm and of C, and the paired gaps of C to the
   ceiling, to C/fp, to depth 2 and to depth 1 (mean ± SEM, |t|), where they ran;
2. re-rooting, where it ran: the paired gap of C to every re-rooting arm;
3. lost slots: per arm, the occupied window slots its count misses at depth 1 / 2 / ≥ 3 (% of
   occupied slots).

``spent`` reads a run of ``configs/routec-spent-paired.yaml`` and the route C overload run. It
prints one row per (delay, U, σ), where σ is the stake share whose notes are spent and whose
holder publishes its wins as entries: the realised σ; D̂/D against the snapshot's stake, and
against the active stake 1 − σ next to 1 / (1 − σ); the block rate (window slots that hold a
block, per slot) against f, next to 1 − σ; the share of the slots only the coalition won that
count; and the paired gap in D̂/D to σ = 0.

The gaps of each table form one family. Its Bonferroni |t| threshold at 5 % (two-sided, Student t
with pairs − 1 degrees of freedom) is printed under it.

Checks, asserted before any table is printed: every row shares its streams, and counting
rejected no entry selection emitted. ``honest``: in epoch 0 every arm of a replicate builds the
tree C builds, so the columns that read only the tree agree; at U = 0 every arm agrees with C in
every column both runs record. ``spent``: the σ = 0 rows equal the route C rows of the overload
run in every column both runs record.

Run:  python scripts/route_c_analysis.py honest runs/<route C dir> runs/<Phase 2 dir> [more runs]
      python scripts/route_c_analysis.py spent runs/<spent dir> runs/<route C overload dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from tsi_sim.config import SimConfig
from tsi_sim.plotting.figures_pernode import CONFIG_COLS, equilibrium, rho_for, sem

DELAY = "blend_delay_max"
KEYS = [DELAY, "max_uncles", "replicate"]
# Columns that read only the block tree, which no counting rule changes in epoch 0.
TREE = ["n_blocks", "n_active_window", "fork_rate", "max_reorg_depth", "mean_reorg_depth",
        "mean_orphan_rate", "agreement_tip", "agreement_window", "mean_ratio_in"]
ARM = ["uncle_depth", "uncle_window_anchor", "uncle_order", "reroot_share", "reroot_delay"]
DEPTHS = ["d1", "d2", "d3", "ceil"]


def _load(run: Path) -> tuple[pd.DataFrame, set[str]]:
    """The run's rows, labelled by arm, with every config column the run predates set to its
    default; and the columns the run itself recorded."""
    df = pd.read_parquet(run / "results.parquet")
    recorded = set(df.columns)
    default = SimConfig()
    for c in CONFIG_COLS:
        if c not in df.columns:
            df[c] = getattr(default, c)
    assert df.paired_streams.all(), f"{run}: every arm must share its random streams"
    assert (df.deep_ref_share == 0.0).all(), f"{run}: counting rejected an entry selection emitted"
    df["arm"] = _arm(df)
    return df, recorded


def _arm(df: pd.DataFrame) -> pd.Series:
    name = df.uncle_depth.map({1: "d1", 2: "d2", 3: "d3", 0: "ceil"})
    c = pd.Series(np.where(df.uncle_order == "uncle", "C", "C/fp"), index=df.index)
    name = name.where(df.uncle_window_anchor == "parent", c)
    rr = ("rr " + df.reroot_share.map("{:g}".format) + "/"
          + df.reroot_delay.map("{:g}".format))
    return name.where(df.reroot_share == 0.0, rr)


def _gap(arm: pd.DataFrame, ref: pd.DataFrame, col: str) -> tuple[float, float, float]:
    """Paired gap ``arm − ref`` in ``col``: mean, SEM and |t| (0 when every pair is equal)."""
    g = (arm[col] - ref[col].loc[arm.index]).to_numpy()
    se = sem(g)
    return g.mean(), se, abs(g.mean()) / se if se > 0 else (np.inf if g.any() else 0.0)


def _same(a: pd.DataFrame, b: pd.DataFrame, on: list[str], cols: list[str]) -> int:
    """Assert that every row of ``a`` has a partner in ``b`` on ``on`` and agrees with it in
    ``cols`` (NaN equal to NaN). Returns the number of rows compared."""
    m = a[on + cols].merge(b[on + cols], on=on, suffixes=("", "_b"), validate="one_to_one")
    assert len(m) == len(a), "a row has no partner"
    for c in cols:
        x, y = m[c], m[f"{c}_b"]
        same = (x == y) | (x.isna() & y.isna())
        assert same.all(), f"{c} differs in {int((~same).sum())} rows"
    return len(m)


def _shared(rec_a: set[str], rec_b: set[str]) -> list[str]:
    """The columns two runs both record, less the arm and the pairing keys."""
    return sorted((rec_a & rec_b) - set(ARM) - set(KEYS) - {"epoch", "arm"})


def honest(run_c: Path, *refs: Path) -> None:
    c, rec_c = _load(run_c)
    assert set(c.arm) == {"C"}
    on = KEYS + ["epoch"]
    parts, n_dup = [c], 0
    held: dict[str, tuple[pd.DataFrame, set[str]]] = {}
    for run in refs:
        df, rec = _load(run)
        assert "C" not in set(df.arm)
        for a, rows in df.groupby("arm"):
            if a in held:                               # the same arm in an earlier run
                first, rec_first = held[a]
                n_dup += _same(rows, first, on, _shared(rec, rec_first))
                continue
            held[a] = rows, rec
            parts.append(rows)
    df = pd.concat(parts, ignore_index=True)
    e0 = df[df.epoch == 0]
    n_tree = n_u0 = 0
    for rows, rec in held.values():
        n_tree += _same(rows[rows.epoch == 0], e0[e0.arm == "C"], KEYS, TREE)
        u0 = rows[rows.max_uncles == 0]
        if len(u0):
            n_u0 += _same(u0, c[c.max_uncles == 0], on, _shared(rec, rec_c))
    eq = equilibrium(df)
    eq["arm"] = _arm(eq)
    arms = set(eq.arm)
    depth = [a for a in [*DEPTHS, "C/fp", "C"] if a in arms]
    vs_depth = [a for a in ("ceil", "C/fp", "d2", "d1") if a in arms]
    vs_rr = sorted(a for a in arms if a.startswith("rr "))
    delays = sorted(eq[DELAY].unique())
    rho = dict(zip(delays, rho_for(df, delays), strict=True))
    acc, rr, lost = [], [], []
    n_pairs = set()
    for (delay, cap), cell in eq[eq.max_uncles > 0].groupby([DELAY, "max_uncles"]):
        arm = {a: cell[cell.arm == a].set_index(KEYS) for a in set(cell.arm)}
        n_pairs |= {len(x) for x in arm.values()}
        head = {"delay": delay, "rho": f"{rho[delay]:.2f}", "U": cap}
        row = {**head, **{a: arm[a].mean_ratio.mean() for a in depth}}
        for ref in vs_depth:
            m, se, t = _gap(arm["C"], arm[ref], "mean_ratio")
            row[f"C-{ref}"] = f"{m:+.4f}±{se:.4f}"
            row[f"C-{ref} |t|"] = f"{t:.1f}"
        acc.append(row)
        if vs_rr:
            row = dict(head)
            for ref in vs_rr:
                m, se, t = _gap(arm["C"], arm[ref], "mean_ratio")
                row[f"C-{ref[3:]}"] = f"{m:+.4f}±{se:.4f}"
                row[f"|t| {ref[3:]}"] = f"{t:.1f}"
            rr.append(row)
        lost.append({**head, **{a: "/".join(
            f"{100 * s.mean():.2f}" for s in (arm[a].lost_d1_share, arm[a].lost_d2_share,
                                              arm[a].lost_d3_share + arm[a].lost_d4plus_share))
            for a in depth}})
    assert len(n_pairs) == 1, "every arm must have the same replicates"
    n = n_pairs.pop()
    print(f"checks: {n_tree} epoch-0 rows of {len(held)} arms build the tree C builds; "
          f"{n_u0} U = 0 rows agree with C; {n_dup} rows of an arm two runs hold agree")
    _print("accuracy: equilibrium D̂/D, and the paired gaps of route C", pd.DataFrame(acc),
           len(vs_depth) * len(acc), n)
    if rr:
        _print("re-rooting (share/delay): the paired gaps of route C", pd.DataFrame(rr),
               len(vs_rr) * len(rr), n)
    _print("lost slots at depth 1 / 2 / >= 3 (% of occupied)", pd.DataFrame(lost))


def spent(run_s: Path, run_c: Path) -> None:
    s, rec_s = _load(run_s)
    c, rec_c = _load(run_c)
    assert set(s.arm) == {"C"} == set(c.arm)
    zero = s[s.spent_share == 0.0]
    ref = c.merge(zero[[DELAY, "max_uncles"]].drop_duplicates(), on=[DELAY, "max_uncles"])
    assert len(ref) == len(zero), "the σ = 0 rows and the route C rows differ in number"
    shared = _shared(rec_s, rec_c)
    n_same = _same(zero, ref, KEYS + ["epoch"], shared)
    eq = equilibrium(s)
    f = float(s.f.iloc[0])
    delays = sorted(eq[DELAY].unique())
    rho = dict(zip(delays, rho_for(s, delays), strict=True))
    rows = []
    n_pairs = set()
    for (delay, cap), cell in eq.groupby([DELAY, "max_uncles"]):
        base = cell[cell.spent_share == 0.0].set_index(KEYS)
        for share, arm in cell.groupby("spent_share"):
            arm = arm.set_index(KEYS)
            n_pairs.add(len(arm))
            row = {"delay": delay, "rho": f"{rho[delay]:.2f}", "U": cap, "share": share,
                   "σ": f"{1.0 - arm.active_stake_frac.mean():.3f}",
                   "D̂/D": arm.mean_ratio.mean(),
                   "D̂/D act": (arm.mean_ratio / arm.active_stake_frac).mean(),
                   "1/(1-σ)": (1.0 / arm.active_stake_frac).mean(),
                   "rate/f": arm.block_rate.mean() / f, "1-σ": arm.active_stake_frac.mean(),
                   "lone counted %": (f"{100 * arm.spent_counted_share.mean():.2f}"
                                      if share > 0 else "")}
            if share > 0:
                m, se, t = _gap(arm, base, "mean_ratio")
                row["-σ0"] = f"{m:+.4f}±{se:.4f}"
                row["-σ0 |t|"] = f"{t:.1f}"
            rows.append(row)
    assert len(n_pairs) == 1, "every share must have the same replicates"
    table = pd.DataFrame(rows)
    print(f"checks: {n_same} σ = 0 rows equal the route C rows in {len(shared)} columns")
    _print("spent stake: D̂ against the snapshot and the active stake, block rate against f",
           table, int((table.share > 0).sum()), n_pairs.pop())


def _print(title: str, table: pd.DataFrame, n_tests: int = 0, n: int = 0) -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(f"\n== {title}")
    print(table.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    if n_tests:
        thr = stats.t.ppf(1 - 0.025 / n_tests, n - 1)
        print(f"Bonferroni |t| threshold for {n_tests} gaps at 5 % ({n} pairs): {thr:.2f}")


def main() -> None:
    mode, runs = sys.argv[1], [Path(p) for p in sys.argv[2:]]
    {"honest": honest, "spent": spent}[mode](*runs)


if __name__ == "__main__":
    main()
