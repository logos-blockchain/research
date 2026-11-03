"""NETWORK.md's tables, read from runs/l1 to runs/l5; tables.py dispatches l* here.

    python scripts/tables.py l1today | l1frontier | l1convention | l2departs | l2time |
                             l3partition | l4hedge | l5cost
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from tables import md

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs"
UPTIMES = (1.0, 0.95, 0.9)


def _pct(v: float, digits: int = 1) -> str:
    return "none" if not math.isfinite(v) else f"{100 * v:.{digits}f} %"


def _share(a: float) -> str:
    return "a third" if abs(a - 1 / 3) < 1e-9 else f"{100 * a:.0f} %"


def l1today() -> None:
    t = pd.read_csv(RUNS / "l1" / "today.csv")
    print(md(pd.DataFrame({
        "minimum stake": [f"{'the minimum' if n == 'minimum' else 'the cap'}, {100 * s:.3f} % of the supply ({v:,.0f} LGO)"
                          for n, s, v in zip(t.min_stake, t.min_stake_supply, t.min_stake_lgo)],
        "honest declared stake": t.honest_locked_active.map(lambda v: f"{100 * v:.1f} % of the active stake"),
        "coalitions held, below: uptime 1": t["alpha_u1.0"].map(lambda v: _pct(v, 2)),
        "uptime 0.95": t["alpha_u0.95"].map(lambda v: _pct(v, 2)),
        "uptime 0.9": t["alpha_u0.9"].map(lambda v: _pct(v, 2)),
        "a third of the declarations takes": [
            f"{d:,} declarations, {100 * s:.1f} % of the supply, {100 * a:.2f} % of the active stake"
            for d, s, a in zip(t.third_declarations, t.third_stake_supply, t.third_stake_active)]})))


def l1frontier() -> None:
    t = pd.read_csv(RUNS / "l1" / "frontier.csv")
    print(md(pd.DataFrame({
        "coalition": t.alpha.map(_share),
        "honest declared stake, more than: uptime 1": t["locked_u1.0"].map(lambda v: _pct(v, 0)),
        "uptime 0.95": t["locked_u0.95"].map(lambda v: _pct(v, 0)),
        "uptime 0.9": t["locked_u0.9"].map(lambda v: _pct(v, 0)),
        "of the honest stake, uptime 1": t.of_honest_u1.map(lambda v: _pct(v, 0)),
        "honest declarations at the minimum stake": t.nodes_at_min_u1.map(
            lambda v: "none" if not math.isfinite(v) else f"{v:,.0f}"),
        "minimum stake for 1,000 honest declarations": t.min_stake_multiple_u1.map(
            lambda v: "none" if not math.isfinite(v) else f"{v:.0f} times today's")})))


def l1convention() -> None:
    t = pd.read_csv(RUNS / "l1" / "convention.csv")
    print(md(pd.DataFrame({
        "uptime of the honest declarations": t.uptime.map(lambda v: f"{v:g}"),
        "largest coalition share of the declared weight": [
            ("below a third" if s else f"{100 * v:.1f} %") for v, s in zip(t.largest_share, t.strict)]})))


def _l2() -> pd.DataFrame:
    return pd.read_csv(RUNS / "l2" / "gadget.csv")


def l2departs() -> None:
    d = _l2()
    rows = []
    for blend, g in d.groupby("blend", sort=False):
        row = {"Blend": blend}
        for lag, h in g.groupby("lag"):
            row[f"lag {lag}"] = f"{int((h.first_off >= 0).sum())} of {len(h)}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def l2time() -> None:
    d = _l2()
    rows = []
    for blend, g in d.groupby("blend", sort=False):
        ok = g.groupby("lag").first_off.max()
        lag = int(min(L for L, v in ok.items() if v < 0))
        h = g[g.lag == lag]
        row = {"Blend": blend, "lag (slots)": lag}
        for R, x in h.groupby("round_slots"):
            row[f"rounds of {R} slots: mean / 95th percentile / longest (s)"] = (
                f"{x.mean_p50.mean():.0f} / {x.p95_p95.max():.0f} / {x.max_p95.max():.0f}")
        row["rounds justified"] = f"{h.justified.min():.3f}"
        row["two thirds of the votes at the median / 95th-percentile node (s)"] = (
            f"{h.quorum_p50.mean():.2f} / {h.quorum_p95.max():.2f}")
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def l3partition() -> None:
    t = pd.read_csv(RUNS / "l3" / "partition.csv")
    rows = []
    for (s, a), g in t.groupby(["side_share", "coalition_share"], sort=True):
        def verdict(col, cf):
            lo, hi = int(g[col].min()), int(g[col].max())
            got = f"{lo}" if lo == hi else f"{lo}–{hi}"
            return f"{got} of {int(g.span_rounds.iloc[0])}; {'certifies' if cf else 'stalls'}"
        rows.append({
            "honest declarations, side / rest": f"{100 * s:.0f} % / {100 * (1 - s):.0f} %",
            "coalition's share of the declared weight": f"{a:.2f}",
            "side: rounds justified on the engine; the closed form": verdict(
                "side_justified", g.side_closed_form.iloc[0]),
            "rest: rounds justified; the closed form": verdict(
                "rest_justified", g.rest_closed_form.iloc[0]),
            "runs that finalize both sides": f"{int((g.finalized_conflicts > 0).sum())} of {len(g)}"})
    print(md(pd.DataFrame(rows)))


def l4hedge() -> None:
    t = pd.read_csv(RUNS / "l4" / "hedge.csv")
    print(md(pd.DataFrame({
        "coalition's stake": [f"{n}, {100 * a:.2f} %" if "declarations" in n else n
                              for n, a in zip(t.share, t.alpha)],
        "random delay, specification's Blend (h)": t.random_h.map(lambda v: f"{v:.2f}"),
        "worst case at 10 s (h)": t.worst_h.map(lambda v: f"{v:.2f}"),
        "worst case, nonce of §3.1 after a deflation (h)": t.nonce_deflated_h.map(
            lambda v: "–" if not math.isfinite(v) else f"{v:.2f}")})))


def l5cost() -> None:
    t = pd.read_csv(RUNS / "l5" / "cost.csv")
    t = t[t.round_slots == 60]
    print(md(pd.DataFrame({
        "declared nodes": t.nodes.map(lambda v: f"{v:,}"),
        "votes a second": t.votes_per_s.map(lambda v: f"{v:.1f}"),
        "Ed25519, ed25519-dalek: one core": t["core Ed25519, ed25519-dalek"].map(lambda v: _pct(v, 2)),
        "Ed25519, aws-lc-rs": t["core Ed25519, aws-lc-rs"].map(lambda v: _pct(v, 2)),
        "ML-DSA-44, aws-lc-rs": t["core ML-DSA-44, aws-lc-rs"].map(lambda v: _pct(v, 2)),
        "received, Ed25519 (KB/s)": t["bytes_per_s Ed25519, ed25519-dalek"].map(lambda v: f"{v / 1000:.1f}"),
        "received, ML-DSA-44 (KB/s)": t["bytes_per_s ML-DSA-44, aws-lc-rs"].map(lambda v: f"{v / 1000:.0f}"),
        "certificate, Ed25519 (KB)": t["certificate Ed25519, ed25519-dalek"].map(lambda v: f"{v / 1000:.1f}"),
        "certificate, ML-DSA-44 (MB)": t["certificate ML-DSA-44, aws-lc-rs"].map(lambda v: f"{v / 1e6:.2f}")})))
