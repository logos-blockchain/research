"""What the deeper rules and re-rooting do against an adversary (PLAN.md Phase 4).

``selfish`` reads a run of ``configs/selfish-depth-paired.yaml`` and one of
``configs/selfish-routec-paired.yaml``. Their cells share streams, so replicate *i* of every arm
is a matched pair: depth 1 (``d1``, the spec rule), depth 2 (``d2``), the ceiling (``ceil``, any
depth, window to the fork point), route C (``C``, any depth, window to the entry's own slot), and
re-rooting at depth 1 by half or all of the honest stake, 10 slots after detection (``rr 0.5``,
``rr 1``). The coalition mines a private chain under SM1 and never re-roots. One row per
(delay, U, coalition share α), with the load ρ the delay gives without a coalition
(``rho_for``):

1. accuracy: the equilibrium D̂/D of every arm, the paired gaps of every other arm to depth 1,
   and of route C to the ceiling and to re-rooting by all the honest stake (mean ± SEM; * marks
   a gap resolved by Bonferroni over the table at 5 %, Student t with pairs − 1 degrees of
   freedom);
2. lost slots: per arm, the occupied window slots its count misses that hold an honest block, at
   depth 1 / 2 / ≥ 3, and those none of whose blocks the coalition published (% of occupied
   slots);
3. the coalition's share of the canonical window blocks per arm, and its paired gap to depth 1.

``withhold`` reads a run of ``configs/withhold-depth-paired.yaml``: per arm, D̂/D against the
active-stake line 1 − α (α realised), with the paired gaps to depth 1.

``growth`` reads any run and prints, per (delay, U, arm), the chain's growth (canonical window
blocks per slot) against f, the mean gap between consecutive canonical blocks in slots, and the
blocks the chain adds over the s = 3⌊k/f⌋ slots of the stake snapshot phase, in units of k. Under
a one-block lag (route A) a spent note stays eligible for one such gap.

``mdp`` solves the selfish-mining MDP of the report's section 6.6 (γ = 0, lead cap 64) for the
revenue-optimal policy. Per α it prints the recovery ceiling η and D̂/D* (p_ref = 1) when a rule
counts the first block (the spec), the first two blocks (cousins) or every block of each discarded
honest chain; the attacker's own ceiling at depths 1 and 2; and, for the depth-maximising
adversary of section 6.10, η at depths 1 and 2. The MDP has no window.

Exclusions, printed: a replicate whose realised coalition share misses its label by more than
0.01 is dropped from every arm, since the Pareto stake draw can leave no node set near the label.
A half-share re-rooting arm whose realised share of the honest stake misses 0.5 by more than 0.01
is dropped from that arm.

Checks, asserted before any table: every row shares its streams; counting rejected no entry that
selection emitted; in epoch 0 every arm of a replicate builds the tree depth 1 builds.

Run:  python scripts/adversary_analysis.py selfish runs/<selfish-depth> runs/<selfish-routec>
      python scripts/adversary_analysis.py withhold runs/<withhold-depth>
      python scripts/adversary_analysis.py growth runs/<any run>
      python scripts/adversary_analysis.py mdp
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask, _reroot_mask
from tsi_sim.plotting.figures_pernode import CONFIG_COLS, equilibrium, rho_for, sem
from tsi_sim.stake import stake_for

DELAY = "blend_delay_max"
CELL = [DELAY, "max_uncles", "adversary_frac"]
KEYS = [*CELL, "replicate"]
# Columns that read only the block tree, which no counting rule changes in epoch 0.
TREE = ["n_blocks", "n_active_window", "fork_rate", "max_reorg_depth", "mean_reorg_depth",
        "mean_orphan_rate", "agreement_tip", "agreement_window", "mean_ratio_in", "adv_blocks",
        "honest_blocks"]
ORDER = ["d1", "d2", "ceil", "C", "rr 0.5", "rr 1"]
TOL = 0.01
_FIELDS = {f.name for f in dataclasses.fields(SimConfig)}


def _load(run: Path) -> pd.DataFrame:
    df = pd.read_parquet(run / "results.parquet")
    default = SimConfig()
    for c in CONFIG_COLS:
        if c not in df.columns:
            df[c] = getattr(default, c)
    assert df.paired_streams.all(), f"{run}: every arm must share its random streams"
    assert (df.deep_ref_share == 0.0).all(), f"{run}: counting rejected an entry selection emitted"
    df["arm"] = _arm(df)
    return df


def _arm(df: pd.DataFrame) -> pd.Series:
    name = df.uncle_depth.map({1: "d1", 2: "d2", 0: "ceil"})
    name = name.where(df.uncle_window_anchor == "parent", "C")
    return name.where(df.reroot_share == 0.0, "rr " + df.reroot_share.map("{:g}".format))


def _config(row: pd.Series) -> SimConfig:
    return SimConfig(**{c: row[c].item() if hasattr(row[c], "item") else row[c]
                        for c in row.index if c in _FIELDS})


def _realised(df: pd.DataFrame) -> pd.DataFrame:
    """Per (cell, replicate): the coalition's realised stake share; and per half-share re-rooting
    replicate, the realised share of the honest stake that re-roots."""
    rows = []
    first = df[df.epoch == 0].drop_duplicates(KEYS + ["arm"])
    for _, r in first.iterrows():
        cfg = _config(r)
        stake = stake_for(cfg)
        adv = _adversary_mask(cfg, stake)
        tot = float(stake.sum())
        a = float(stake[adv].sum()) / tot if adv is not None else 0.0
        share = np.nan
        if cfg.reroot_share > 0.0:
            rr = _reroot_mask(cfg, stake, adv)
            honest = tot - (float(stake[adv].sum()) if adv is not None else 0.0)
            share = float(stake[rr].sum()) / honest
        rows.append({**{k: r[k] for k in KEYS}, "arm": r.arm, "alpha_real": a,
                     "reroot_real": share})
    return pd.DataFrame(rows)


def _exclude(eq: pd.DataFrame, real: pd.DataFrame, rr_label: str | None) -> pd.DataFrame:
    real = real.copy()
    off_a = (real.alpha_real - real.adversary_frac).abs() > TOL
    drop = set(map(tuple, real.loc[off_a, KEYS].drop_duplicates().to_numpy().tolist()))
    off_r = (real.arm == rr_label) & ((real.reroot_real - 0.5).abs() > TOL)
    drop_rr = set(map(tuple, real.loc[off_r, KEYS].to_numpy().tolist())) - drop
    print(f"exclusions: {len(drop)} replicates off their coalition label by > {TOL} "
          f"(every arm): {sorted(drop)}")
    if rr_label:
        print(f"            {len(drop_rr)} {rr_label} replicates off a half of the honest stake "
              f"by > {TOL}: {sorted(drop_rr)}")
    key = list(map(tuple, eq[KEYS].to_numpy().tolist()))
    keep = np.array([k not in drop and not (a == rr_label and k in drop_rr)
                     for k, a in zip(key, eq.arm, strict=True)])
    return eq[keep]


def _gap(arm: pd.DataFrame, ref: pd.DataFrame, col: str) -> tuple[float, float, float, int]:
    """Paired gap ``arm − ref`` in ``col`` over their common replicates: mean, SEM, |t|, pairs."""
    idx = arm.index.intersection(ref.index)
    g = (arm[col].loc[idx] - ref[col].loc[idx]).to_numpy()
    se = sem(g)
    t = abs(g.mean()) / se if se > 0 else (np.inf if g.any() else 0.0)
    return g.mean(), se, t, len(g)


def _tree_check(df: pd.DataFrame) -> int:
    e0 = df[df.epoch == 0].set_index(KEYS)
    ref = e0[e0.arm == "d1"]
    n = 0
    for a in set(e0.arm) - {"d1"}:
        rows = e0[e0.arm == a]
        assert rows.index.isin(ref.index).all(), f"{a}: a replicate without a depth-1 partner"
        for c in TREE:
            x, y = rows[c], ref[c].loc[rows.index]
            same = (x == y) | (x.isna() & y.isna())
            assert same.all(), f"{a}: epoch-0 {c} differs from depth 1 in {(~same).sum()} rows"
        n += len(rows)
    return n


def _thr(n_tests: int, n: int) -> float:
    return float(stats.t.ppf(1 - 0.025 / n_tests, n - 1))


def _fmt(gaps: dict[str, tuple[float, float, float, int]], n_tests: int) -> dict[str, str]:
    return {k: f"{m:+.4f}±{se:.4f}{'*' if t > _thr(n_tests, n) else ''}"
            for k, (m, se, t, n) in gaps.items()}


def selfish(run_d: Path, run_c: Path) -> None:
    d, c = _load(run_d), _load(run_c)
    assert set(c.arm) == {"C"} and "C" not in set(d.arm)
    df = pd.concat([d, c], ignore_index=True)
    n_tree = _tree_check(df)
    real = _realised(df)
    eq = equilibrium(df)
    eq["arm"] = _arm(eq)
    eq = _exclude(eq, real, "rr 0.5")
    arms = [a for a in ORDER if a in set(eq.arm)]
    delays = sorted(eq[DELAY].unique())
    rho = dict(zip(delays, rho_for(df, delays), strict=True))
    cells = list(eq.groupby(CELL))
    vs_d1 = [a for a in arms if a != "d1"]
    n_acc = len(cells) * (len(vs_d1) + 2)
    n_adv = len(cells) * len(vs_d1)
    acc, lost, adv = [], [], []
    for (delay, cap, alpha), cell in cells:
        arm = {a: cell[cell.arm == a].set_index(KEYS) for a in arms}
        head = {"delay": delay, "rho": f"{rho[delay]:.2f}", "U": cap, "α": alpha,
                "n": len(arm["d1"])}
        gaps = {f"{a}-d1": _gap(arm[a], arm["d1"], "mean_ratio") for a in vs_d1}
        gaps["C-ceil"] = _gap(arm["C"], arm["ceil"], "mean_ratio")
        gaps["C-rr 1"] = _gap(arm["C"], arm["rr 1"], "mean_ratio")
        acc.append({**head, **{a: arm[a].mean_ratio.mean() for a in arms},
                    **_fmt(gaps, n_acc)})
        lost.append({**head, **{a: "/".join(f"{100 * s.mean():.2f}" for s in (
            arm[a].lost_honest_d1_share, arm[a].lost_honest_d2_share,
            arm[a].lost_honest_d3plus_share, arm[a].lost_unpublished_share)) for a in arms},
            "rr 1 copies %": f"{100 * arm['rr 1'].reroot_made_share.mean():.2f}"})
        gaps = {f"{a}-d1": _gap(arm[a], arm["d1"], "adv_block_share") for a in vs_d1}
        adv.append({**head, **{a: arm[a].adv_block_share.mean() for a in arms},
                    **_fmt(gaps, n_adv)})
    print(f"checks: {n_tree} epoch-0 rows of the other arms build the tree depth 1 builds")
    _print("accuracy: equilibrium D̂/D, and the paired gaps", pd.DataFrame(acc), n_acc)
    _print("lost slots holding an honest block at depth 1 / 2 / >= 3, and those the coalition "
           "never published (% of occupied)", pd.DataFrame(lost))
    _print("the coalition's share of the canonical window blocks, and the paired gaps",
           pd.DataFrame(adv), n_adv)


def withhold(run: Path) -> None:
    df = _load(run)
    n_tree = _tree_check(df)
    real = _realised(df)
    eq = equilibrium(df)
    eq["arm"] = _arm(eq)
    eq = _exclude(eq, real, None)
    a_real = real.drop_duplicates(KEYS).set_index(KEYS).alpha_real
    arms = [a for a in ORDER if a in set(eq.arm)]
    delays = sorted(eq[DELAY].unique())
    rho = dict(zip(delays, rho_for(df, delays), strict=True))
    cells = list(eq.groupby(CELL))
    vs_d1 = [a for a in arms if a != "d1"]
    n_tests = len(cells) * len(vs_d1)
    rows = []
    for (delay, cap, alpha), cell in cells:
        arm = {a: cell[cell.arm == a].set_index(KEYS) for a in arms}
        line = (1.0 - a_real.loc[arm["d1"].index]).mean()
        gaps = {f"{a}-d1": _gap(arm[a], arm["d1"], "mean_ratio") for a in vs_d1}
        rows.append({"delay": delay, "rho": f"{rho[delay]:.2f}", "U": cap, "α": alpha,
                     "n": len(arm["d1"]), "1-α": line,
                     **{a: arm[a].mean_ratio.mean() for a in arms}, **_fmt(gaps, n_tests)})
    print(f"checks: {n_tree} epoch-0 rows of the other arms build the tree depth 1 builds")
    _print("withholding: equilibrium D̂/D against 1 − α (realised), and the paired gaps",
           pd.DataFrame(rows), n_tests)


def growth(run: Path) -> None:
    df = _load(run)
    eq = equilibrium(df)
    eq["arm"] = _arm(eq)
    geometry = SimConfig(k=int(df.k.iloc[0]), f=float(df.f.iloc[0]))
    phase = 3 * (geometry.period_T // 6)                 # s = 3⌊k/f⌋ slots
    eq["rate"] = (eq.adv_blocks + eq.honest_blocks) / geometry.period_T
    rows = []
    for (delay, cap, arm), cell in eq.groupby([DELAY, "max_uncles", "arm"]):
        rows.append({"delay": delay, "U": cap, "arm": arm, "n": len(cell),
                     "chain/f": cell.rate.mean() / geometry.f, "gap": 1.0 / cell.rate.mean(),
                     "phase/k": cell.rate.mean() * phase / geometry.k})
    _print(f"chain growth (k = {geometry.k})", pd.DataFrame(rows))


def mdp() -> None:
    from tsi_sim.reorg import (
        alpha_effective,
        countable_recovery_from_depths,
        simulate_deepest_reorg,
    )
    from tsi_sim.selfish_mdp import optimal_policy_stats

    rows = []
    for alpha in (0.34, 0.40, 0.46):
        s = optimal_policy_stats(alpha, 0.0, cap=64)
        assert s.deviates
        rows.append({"α": alpha, "revenue": s.revenue,
                     "η d1": s.recovery(1), "η d2": s.recovery(2),
                     "D̂/D* d1": s.dhat_ratio(1.0), "D̂/D* d2": s.dhat_ratio(1.0, max_depth=2),
                     "D̂/D* any": s.dhat_ratio(1.0, countable=False),
                     "D̂/D* none": s.dhat_ratio(0.0),
                     "η adv d1": s.recovery(1, adv=True), "η adv d2": s.recovery(2, adv=True)})
    _print("revenue-optimal selfish policy (γ = 0, cap 64): recovery and D̂/D* at p_ref = 1",
           pd.DataFrame(rows))
    rows = []
    for o in (0.0, 0.35):
        for alpha in (0.10, 0.20, 0.30):
            depths = simulate_deepest_reorg(alpha_effective(alpha, o), 4_000_000,
                                            np.random.default_rng(5))
            rows.append({"α": alpha, "o": o, "E[depth]": depths.mean(),
                         "η d1": countable_recovery_from_depths(depths),
                         "η d2": countable_recovery_from_depths(depths, max_depth=2)})
    _print("depth-maximising adversary (section 6.10): recovery at depths 1 and 2",
           pd.DataFrame(rows))


def _print(title: str, table: pd.DataFrame, n_tests: int = 0) -> None:
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 60)
    print(f"\n== {title}")
    print(table.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    if n_tests:
        print(f"* = resolved by Bonferroni over {n_tests} gaps at 5 % (|t| > "
              f"{_thr(n_tests, 20):.2f} at 20 pairs)")


def main() -> None:
    mode, runs = sys.argv[1], [Path(p) for p in sys.argv[2:]]
    {"selfish": selfish, "withhold": withhold, "growth": growth, "mdp": mdp}[mode](*runs)


if __name__ == "__main__":
    main()
