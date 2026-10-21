"""Phase K's tables for K.4 and K.5, read straight from runs/k5 (``python scripts/tables.py k5...``).

    python scripts/tables.py k5mapping | k5rate | k5blend | k5relays
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs"


def md(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(v) for v in r.to_list()) + " |")
    return "\n".join(out)


def _num(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def _pct(v: float) -> str:
    return "none" if v == 0 else f"{_num(100 * v)} %"


def k5mapping() -> None:
    m = pd.read_csv(RUNS / "k5" / "mapping.csv")
    rows = []
    for k, g in m.groupby("k", sort=False):
        one, three = g[g.multiple == 1].iloc[0], g[g.multiple == 3].iloc[0]
        rows.append({
            "k": k,
            "K = ⌊k/f⌋": f"{int(one.window):,} slots, {one.hours:.1f} h",
            "K = 3⌊k/f⌋": f"{int(three.window):,} slots, {three.hours:.1f} h",
            "offline grace margin, K / T_offline": f"{_num(one.offline_margin)} / {_num(three.offline_margin)}",
            "targets meeting two ground nonces": f"{_pct(one.two_nonces)} / {_pct(three.two_nonces)}",
            "targets outside B6's bound": f"{_pct(one.private_nonce)} / {_pct(three.private_nonce)}",
            "self-healing horizon in blocks, sides of 0.5 / 0.2 of the stake":
                f"{one.horizon_half_h:.1f} / {one.horizon_fifth_h:.1f} h",
        })
    print(md(pd.DataFrame(rows)))


def k5rate() -> None:
    r = pd.read_csv(RUNS / "k5" / "rate.csv")
    a = {0.25: "0.25", 0.3: "0.30"}
    print(md(pd.DataFrame({
        "block interval": r.interval.map(lambda v: f"{v} s"),
        "α": r.alpha.map(lambda v: a.get(round(v, 2), "0.33")),
        "random delay: B5's depth": [f"{int(d)} ({h:.1f} h)" for d, h in zip(r.random_depth, r.random_depth_h)],
        "random delay: a wait": r.random_wait_h.map(lambda v: f"{v:.1f} h"),
        "worst, 10 s: B2's depth": [f"{d:,} ({h:.1f} h)" for d, h in zip(r.worst_depth, r.worst_depth_h)],
        "worst, 10 s: a wait, bound": r.worst_wait_h.map(lambda v: f"{v:.1f} h"),
    })))


def k5blend() -> None:
    b = pd.read_csv(RUNS / "k5" / "blend.csv")

    def cell(d, h, w):
        if not math.isfinite(d):
            return "–"
        return f"{int(d):,} ({h:.1f} h), {w:.1f} h"

    rows = []
    for (hops, rounds), g in b.groupby(["hops", "rounds"], sort=False):
        lo, hi = g[g.alpha < 0.31].iloc[0], g[g.alpha > 0.31].iloc[0]
        rows.append({
            "hops": hops, "rounds": rounds, "Δ": f"{int(lo.delta_s)} s",
            "random, 0.30": cell(lo.random_depth, lo.random_h, lo.random_wait_h),
            "worst, 0.30": cell(lo.worst_depth, lo.worst_h, lo.worst_wait_h),
            "random, 0.33": cell(hi.random_depth, hi.random_h, hi.random_wait_h),
            "worst, 0.33": cell(hi.worst_depth, hi.worst_h, hi.worst_wait_h),
        })
    print(md(pd.DataFrame(rows)))


def k5relays() -> None:
    r = pd.read_csv(RUNS / "k5" / "relays.csv")
    arm = {(False, "hold"): "honest", (True, "hold"): "hostile, holding",
           (True, "deadline"): "hostile, holding to the deadline", (True, "drop"): "hostile, dropping"}
    a = {0.25: "0.25", 0.3: "0.30"}
    print(md(pd.DataFrame({
        "α": r.alpha.map(lambda v: a.get(round(v, 2), "0.33")),
        "relays": [arm[(h, x)] for h, x in zip(r.hostile, r.action)],
        "copies": r.copies,
        "closed form at 1e-9": [f"{int(d)} ({h:.1f} h)" for d, h in zip(r.depth, r.hours)],
        "a wait at 1e-9": r.wait_h.map(lambda v: f"{v:.1f} h"),
        "over honest relays: blocks / wait": [
            "–" if not h else f"+{100 * dc:.0f} % / +{100 * wc:.0f} %"
            for h, dc, wc in zip(r.hostile, r.depth_cost, r.wait_cost)],
    })))
