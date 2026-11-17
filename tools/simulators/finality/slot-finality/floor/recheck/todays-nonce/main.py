"""Compute every curve and every grinding factor the two tables need (cached in ./.cache/data).

    python main.py [n_jobs]

Variants of the pair (f, share) handed to pair_bounds:
  main    f = 1 - (1 - F)^scale, share a          (the lottery as it runs in the state)
  old     f = F,                 share a          (deflated states: the rate before the deflation)
  linear  f = F * scale,         share a          (deflated states: the slot chance scaled, not the rate)
  total   f as main,             share s          (offline states: share of all stake, not of the active)
  normal  f = F,                 share s          (the lottery of the undisturbed state, same delay)
"""

from __future__ import annotations

import sys
import time

import common as c
from joblib import Parallel, delayed

SHARES = [round(0.20 + 0.01 * i, 2) for i in range(14)]
S_A = 0.30
T_A = 300_000
T_B = 64_800
FLOOR = 1e-55
VARIANTS = ("main", "old", "linear", "total", "normal")


def variant_args(p: dict, variant: str) -> tuple[float, float]:
    if variant == "main":
        return p["f_grind"], p["a"]
    if variant == "old":
        return c.F, p["a"]
    if variant == "linear":
        return c.F * p["scale"], p["a"]
    if variant == "total":
        return p["f_grind"], p["s"]
    if variant == "normal":
        return c.F, p["s"]
    raise ValueError(variant)


def t_max_for(s: float) -> int:
    return T_A if s == S_A else T_B


def curve_job(state: int, s: float):
    p = c.params(state, s)
    t0 = time.time()
    cv = c.curve(p["a"], p["delta"], p["scale"], t_max_for(s), FLOOR)
    return ("curve", state, s, cv.size, time.time() - t0)


def grind_job(state: int, s: float, variant: str):
    p = c.params(state, s)
    f, a = variant_args(p, variant)
    t0 = time.time()
    row = c.grind(f, a, p["delta"])
    return ("grind", state, s, variant, row["two_lo"], row["two_hi"], row["error"], time.time() - t0)


def jobs() -> list:
    out = []
    # the long curves first: s = 0.30 to 300,000 slots, then the largest shares
    for s in [S_A] + sorted((x for x in SHARES if x != S_A), reverse=True):
        for st in (5, 6, 4, 3, 1, 2, 0):
            out.append(delayed(curve_job)(st, s))
    seen = set()
    for variant in VARIANTS:
        for st in range(len(c.STATES)):
            for s in SHARES:
                p = c.params(st, s)
                f, a = variant_args(p, variant)
                key = (round(f, 14), round(a, 12), p["delta"])
                if key in seen:
                    continue
                seen.add(key)
                out.append(delayed(grind_job)(st, s, variant))
    return out


if __name__ == "__main__":
    n_jobs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    t0 = time.time()
    js = jobs()
    print(f"{len(js)} jobs on {n_jobs} workers", flush=True)
    for r in Parallel(n_jobs=n_jobs, return_as="generator_unordered")(js):
        print(f"[{time.time() - t0:7.1f} s]", *r, flush=True)
    print(f"done in {time.time() - t0:.1f} s", flush=True)
