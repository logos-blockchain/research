"""Tables A and B from the cache main.py filled; one set per variant of the pair handed to
pair_bounds (see main.py).

    python report.py [variant ...]
"""

from __future__ import annotations

import math
import sys

import numpy as np

import common as c
from main import FLOOR, S_A, SHARES, T_A, VARIANTS, t_max_for, variant_args

WINDOWS = ((64_800, "18 h"), (36_000, "10 h"))
ENDS = ("two_lo", "two_hi")


def the_curve(state: int, s: float) -> np.ndarray:
    p = c.params(state, s)
    return c.curve(p["a"], p["delta"], p["scale"], t_max_for(s), FLOOR)


def the_grind(state: int, s: float, variant: str) -> dict:
    p = c.params(state, s)
    f, a = variant_args(p, variant)
    return c.grind(f, a, p["delta"])


def wait_h(cv: np.ndarray, t_max: int, eps: float) -> tuple[float, str]:
    t = c.wait_needed(cv, eps)
    if t > 0:
        return t / 3600, ""
    return math.nan, ("past t_max" if cv.size >= t_max else "below the curve's floor")


def table_a(variant: str) -> list[dict]:
    rows = []
    for st, (name, *_rest) in enumerate(c.STATES):
        cv = the_curve(st, S_A)
        g = the_grind(st, S_A, variant)
        row = dict(state=name, a=c.params(st, S_A)["a"], f=g["f"], share=g["a"], error=g["error"],
                   one_lo=g["one_lo"], one_hi=g["one_hi"], two_lo=g["two_lo"], two_hi=g["two_hi"])
        row["wait0"], row["note0"] = wait_h(cv, T_A, c.EPS)
        for end in ENDS:
            row[f"wait_{end}"], row[f"note_{end}"] = (
                wait_h(cv, T_A, c.EPS / g[end]) if g[end] == g[end] else (math.nan, "no factor"))
        rows.append(row)
    return rows


def log_chance(state: int, s: float, k: int) -> float:
    """ln of the chance after k slots; -inf where the curve fell to the floor before k."""
    cv = the_curve(state, s)
    return math.log(cv[k - 1]) if cv.size >= k else -math.inf


def crossing(g: list[float]) -> tuple[float, str]:
    """The share at which g, linear between the grid's shares, first rises through ln EPS."""
    target = math.log(c.EPS)
    if not g[0] <= target:
        return SHARES[0], "<"
    for i in range(len(SHARES) - 1):
        lo, hi = g[i], g[i + 1]
        if hi != hi:
            return SHARES[i], "no factor above"
        if hi > target:
            if lo == -math.inf:
                return SHARES[i], "lower point below the curve's floor"
            return SHARES[i] + (SHARES[i + 1] - SHARES[i]) * (target - lo) / (hi - lo), ""
    return SHARES[-1], ">="


def table_b(variant: str) -> list[dict]:
    rows = []
    for st, (name, *_rest) in enumerate(c.STATES):
        row = dict(state=name)
        for k, label in WINDOWS:
            lc = [log_chance(st, s, k) for s in SHARES]
            row[f"{label} none"] = crossing(lc)
            for end in ENDS:
                lf = [math.log(v) if v == v else math.nan
                      for v in (the_grind(st, s, variant)[end] for s in SHARES)]
                row[f"{label} {end}"] = crossing([a + b for a, b in zip(lc, lf)])
        rows.append(row)
    return rows


def fmt_share(v: tuple[float, str]) -> str:
    x, note = v
    if note in ("<", ">="):
        return f"{note} {x:.2f}"
    return f"{x:.3f}" + (f" ({note})" if note else "")


def show(variant: str) -> None:
    print(f"=== variant {variant} ===\n")
    print("Table A, s = 0.30 (hours; factor at 1e-9, two nonces)")
    print(f"{'state':28s} {'a':>7s} {'f':>9s} {'share':>7s} {'wait0':>7s} {'two_lo':>10s} {'two_hi':>10s} "
          f"{'wait_lo':>8s} {'wait_hi':>8s}  {'one_lo':>9s} {'one_hi':>9s}  notes")
    for r in table_a(variant):
        notes = " ".join(x for x in (r["error"], r["note0"], r["note_two_lo"], r["note_two_hi"]) if x)
        print(f"{r['state']:28s} {r['a']:7.4f} {r['f']:9.6f} {r['share']:7.4f} {r['wait0']:7.2f} "
              f"{r['two_lo']:10.3e} {r['two_hi']:10.3e} {r['wait_two_lo']:8.2f} {r['wait_two_hi']:8.2f}  "
              f"{r['one_lo']:9.2e} {r['one_hi']:9.2e}  {notes}")
    print("\nTable B, the largest share each window proves (no grinding | lower end | upper end)")
    print(f"{'state':28s} " + " ".join(f"{label + ' ' + col:>13s}" for _, label in WINDOWS
                                         for col in ("none", "lo", "hi")))
    for r in table_b(variant):
        print(f"{r['state']:28s} " + " ".join(
            f"{fmt_share(r[f'{label} {col}']):>13s}" for _, label in WINDOWS
            for col in ("none", "two_lo", "two_hi")))
    print()


def factors_grid(variant: str) -> None:
    print(f"--- factors at 1e-9, two nonces, lower-upper end, variant {variant} ---")
    print(f"{'s':>5s} " + " ".join(f"{'state ' + str(i):>19s}" for i in range(len(c.STATES))))
    for s in SHARES:
        cells = []
        for st in range(len(c.STATES)):
            g = the_grind(st, s, variant)
            cells.append(f"{g['two_lo']:.2e}-{g['two_hi']:.2e}" if not g["error"] else "error")
        print(f"{s:5.2f} " + " ".join(f"{x:>19s}" for x in cells))
    errs = {(st, s): the_grind(st, s, variant)["error"] for st in range(len(c.STATES)) for s in SHARES}
    for (st, s), e in errs.items():
        if e:
            print(f"  error at state {st}, s = {s}: {e}")
    print()


def chances_grid() -> None:
    for k, label in WINDOWS:
        print(f"--- log10 of the chance after {label} ({k} slots); '-' = below the floor {FLOOR:g} ---")
        print(f"{'s':>5s} " + " ".join(f"{'state ' + str(i):>9s}" for i in range(len(c.STATES))))
        for s in SHARES:
            cells = []
            for st in range(len(c.STATES)):
                v = log_chance(st, s, k)
                cells.append("-" if v == -math.inf else f"{v / math.log(10):.2f}")
            print(f"{s:5.2f} " + " ".join(f"{x:>9s}" for x in cells))
        print()


if __name__ == "__main__":
    variants = sys.argv[1:] or list(VARIANTS)
    chances_grid()
    for v in variants:
        show(v)
        factors_grid(v)
