"""SLOTS.md K.9's tables, read from runs/k9 (scripts/k9_occupancy.py); tables.py dispatches k9* here.

    python scripts/tables.py k9floor | k9protection | k9stall | k9quorum
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from tables import md
from tables_k3 import p10, share

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs" / "k9"


def _d(v: float) -> str:
    return "none" if not math.isfinite(v) else (f"{v:.0f}" if v >= 100 else f"{v:.2f}")


def k9floor() -> None:
    t = pd.read_csv(RUNS / "floor.csv")
    print(md(pd.DataFrame({
        "K": t.window, "α_max": t.alpha.map(share), "count": t["count"],
        "floor φ": t.phi.map(lambda v: f"{v:,}"),
        "withheld-from chain, mean": t.expected.map(lambda v: f"{v:,.0f}"),
        "nobody withholds: waits": t.log10_wait_full.map(p10),
        "withheld from: waits": t.log10_wait_attacked.map(p10),
        "largest side held at K": t.provisional_share.map(lambda v: f"{v:.3f}")})))


def k9protection() -> None:
    t = pd.read_csv(RUNS / "protection.csv")
    rows = []
    for (w, src), g in t.groupby(["window", "floor_from"], sort=False):
        row = {"K": w, "floor": f"{int(g.phi.iloc[0]):,}, {src}"}
        for s, m, e in zip(g.sigma, g.mean_days, g.early_days):
            row[f"σ = {share(s)}"] = f"{m:.2f} / {e:.2f}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def k9stall() -> None:
    t = pd.read_csv(RUNS / "stall.csv")
    rows = []
    for w, g in t.groupby("window", sort=False):
        row = {"K": w, "floor": f"{int(g.phi.iloc[0]):,}",
               "r*: blocks / occupied slots": f"{g.r_star_blocks.iloc[0]:.3f} / {g.r_star_occupied.iloc[0]:.3f}"}
        for r, b, o in zip(g.r, g.depth_blocks_days, g.depth_occupied_days):
            row[f"depth form, fall to {r:.0%}".replace("%", " %")] = f"{b:.2f} / {o:.2f}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def k9quorum() -> None:
    t = pd.read_csv(RUNS / "quorum.csv")
    print(md(pd.DataFrame({
        "α": t.alpha.map(share), "count": t["count"],
        "honest chain withheld from, per 1,000 slots": (1000 * t.live_rate).map(lambda v: f"{v:.2f}"),
        "side of (1 + α)/2, per 1,000 slots": (1000 * t.side_rate).map(lambda v: f"{v:.2f}"),
        "least K (days)": [("none" if s < 0 else _d(v)) for s, v in zip(t.least_slots, t.least_days)],
        "floor at it": [("–" if s < 0 else f"{v:,}") for s, v in zip(t.least_slots, t.phi_at_least)]})))
