"""SLOTS.md K.8's tables, read from runs/k8 (scripts/k8_cap.py); tables.py dispatches k8* here.

    python scripts/tables.py k8params | k8protection | k8stall | k8ratio | k8deflation | k8spec
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from tables import md

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs" / "k8"
CAPS = ("none", "20%", "10%", "5%", "2%")
RANDOM, WORST = "random, specification", "worst, 10 s"


def _share(v: float) -> str:
    return "a third" if abs(v - 1 / 3) < 1e-6 else f"{v:.2f}"


def _cap(c: str) -> str:
    return c if c == "none" else c.replace("%", " %")


def _d(v: float) -> str:
    if math.isinf(v):
        return "never"
    if v == 0:
        return "0"
    return f"{v:.0f}" if v >= 100 else f"{v:.2f}"


def k8params() -> None:
    p = pd.read_csv(RUNS / "params.csv")
    print(md(pd.DataFrame({
        "K": [f"{w}, {s / 3600:.0f} h" for w, s in zip(p.window, p.slots)],
        "floor φ": p.phi.map(lambda v: f"{v:,}"),
        "σ*: the largest side it holds back": p.sigma_star.map(lambda v: f"{v:.3f}"),
        "r*: the least stake that reaches it, random delay": p[f"r_star, {RANDOM}"].map(lambda v: f"{v:.3f}"),
        "r*, worst case at 10 s": p[f"r_star, {WORST}"].map(lambda v: f"{v:.3f}")})))


def k8protection() -> None:
    p = pd.read_csv(RUNS / "protection.csv")
    for w in ("⌊k/f⌋", "3⌊k/f⌋"):
        t = p[p.window == w]
        print(f"K = {w}, days: density form / depth form\n")
        rows = []
        for s in sorted(t.sigma.unique()):
            r = {"σ": _share(s)}
            for c in CAPS:
                x = t[(t.sigma == s) & (t.cap == c)].iloc[0]
                r[_cap(c)] = f"{_d(x.density_days)} / {_d(x.depth_mean_days)}"
            rows.append(r)
        print(md(pd.DataFrame(rows)))
        print()


def k8stall() -> None:
    s = pd.read_csv(RUNS / "stall.csv")
    for w in ("⌊k/f⌋", "3⌊k/f⌋"):
        t = s[s.window == w]
        print(f"K = {w}, days: the density form's stall, random delay / worst case at 10 s\n")
        rows = []
        for r in sorted(t.r.unique(), reverse=True):
            row = {"r": f"{r:.0%}".replace("%", " %")}
            for c in CAPS:
                a = t[(t.r == r) & (t.cap == c) & (t.model == RANDOM)].iloc[0]
                b = t[(t.r == r) & (t.cap == c) & (t.model == WORST)].iloc[0]
                row[_cap(c)] = f"{_d(a.density_stall_days)} / {_d(b.density_stall_days)}"
            rows.append(row)
        print(md(pd.DataFrame(rows)))
        print()
    t = s[(s.window == "3⌊k/f⌋") & (s.model == RANDOM)]
    print("K = 3⌊k/f⌋, random delay: under the depth form, the days until a block made at the fall is "
          "fixed; the days until the chain fills its slots within 5 % of f\n")
    rows = []
    for r in sorted(t.r.unique(), reverse=True):
        row = {"r": f"{r:.0%}".replace("%", " %"),
               "depth form": _d(t[(t.r == r) & (t.cap == "none")].iloc[0].depth_finality_days)}
        for c in CAPS:
            row[f"slow, {_cap(c)}"] = _d(t[(t.r == r) & (t.cap == c)].iloc[0].slow_days)
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def k8ratio() -> None:
    r = pd.read_csv(RUNS / "ratio.csv")
    rows = []
    for w in ("⌊k/f⌋", "3⌊k/f⌋"):
        for c in CAPS:
            a = r[(r.window == w) & (r.cap == c) & (r.model == RANDOM)].iloc[0]
            b = r[(r.window == w) & (r.cap == c) & (r.model == WORST)].iloc[0]
            rows.append({"K": w, "cap": _cap(c),
                         "protection, a side of 0.3 (days)": _d(a.protection_days),
                         "stall after a fall to 50 %, random / worst (days)":
                             f"{_d(a.stall_days)} / {_d(b.stall_days)}",
                         "protection over stall, random / worst": f"{a.ratio:.2f} / {b.ratio:.2f}"})
    print(md(pd.DataFrame(rows)))


def k8deflation() -> None:
    d = pd.read_csv(RUNS / "deflation.csv")
    rows = []
    for c in CAPS[1:]:
        row = {"cap an epoch": _cap(c)}
        for a in (0.25, 0.30, 1 / 3):
            x = d[(d.cap == c) & ((d.alpha - a).abs() < 1e-6)].iloc[0]
            row[f"α = {_share(a)}"] = (f"{int(x.periods)} periods: {x.withheld_days:.1f} days withheld, "
                                       f"{x.epochs_days:.1f} in all")
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def k8spec() -> None:
    s = pd.read_csv(RUNS / "spec.csv")
    print(md(pd.DataFrame({
        "f": [f"1/{int(i)}" for i in s.interval_s], "f_p": s.f_p,
        "occupied slots a slot at rest": s.rests_at.map(lambda v: f"{v:.4f}"),
        "estimate over the stake": s.estimate_over_stake.map(lambda v: f"{v:.4f}"),
        "block interval (s)": s.block_interval_s.map(lambda v: f"{v:.2f}")})))
