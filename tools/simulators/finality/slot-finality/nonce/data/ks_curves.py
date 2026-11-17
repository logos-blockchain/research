# The study's wait bound (finality_sim.waitbound.wait_curve, K.7) on B5's grid of shares,
# at 10 s, 10 s deflated (both rates raised by 1/(1 - a), as K.7 and G7 read it), 12 s and 15 s,
# for waits of 1 .. 64,800 slots, as K.7's grid_logs computes them (floor 1e-50).
# Also: B6's grinding factors on B6's worst-case grid at 10 s (k2_holds: point(dict(delta=10), a,
# per_bit=4)), and the calibration of the resisting nonce's factor.
# Usage: python ks_curves.py   (writes ks_factors.csv and ks_curves.npy beside this file)
import math
import os
import sys
import time

import numpy as np
from joblib import Parallel, delayed

from ks_common import EPS, F, GRID, WGRID, add_src

OUT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(OUT, "..", "..", "..", "src")
add_src(SRC)
T = 64800
FLOOR = 1e-50


def logs(a, d, dfl):
    from finality_sim.waitbound import wait_curve
    c = wait_curve(T, a, d, floor=FLOOR, scale=1 / (1 - a) if dfl else 1.0)
    out = np.full(T, math.log(FLOOR))
    with np.errstate(divide="ignore"):
        out[:c.size] = np.log(np.maximum(c, 1e-300))
    return out.astype(np.float32)


def factor_row(a):
    from finality_sim.grinding import factors, pair_bounds
    ts, lower, upper, lower2, upper2 = pair_bounds(F, a, budget_bits=64, depths=4000, floor=100,
                                                   per_bit=4, delta=10)
    lo1, hi1 = factors(ts, lower, upper, EPS)
    lo2, hi2 = factors(ts, lower2, upper2, EPS)
    return (a, lo1, hi1, lo2, hi2)


def need(alpha, delta, eps, scale=1.0):
    from finality_sim.waitbound import wait_curve, wait_needed
    return wait_needed(wait_curve(1_500_000, alpha, delta, F, floor=eps / 10, scale=scale), eps)


if __name__ == "__main__":
    t0 = time.time()
    par = Parallel(n_jobs=14)
    # calibration of the resisting nonce: (1.10)^2, slots.md §4 "at most 1.10" per nonce
    fr = 1.10 ** 2
    cal = par(delayed(need)(*args) for args in (
        (1 / 3, 10, EPS / fr), (1 / 3, 10, EPS / fr, 1.5), (0.30, 10, EPS / fr, 1 / 0.7),
        (0.30, 10, EPS / fr)))
    print("calibration with F_res = 1.21: a third 10 s:", cal[0] / 3600, "h (K.7 prints 10.2);",
          "a third deflated:", cal[1] / 3600, "h (M.7 prints 12.47);",
          "30 % deflated:", cal[2] / 3600, "h (M.7 prints 6.43);",
          "30 % plain:", cal[3] / 3600, "h (K.7 prints 6.0)", flush=True)
    fac = par(delayed(factor_row)(float(a)) for a in WGRID)
    np.savetxt(f"{OUT}/ks_factors.csv", np.array(fac), delimiter=",",
               header="alpha,factor_lo,factor_hi,pair_lo,pair_hi", comments="")
    print(f"factors done ({time.time() - t0:.0f} s)", flush=True)
    cases = ((10, False), (10, True), (12, False), (15, False))
    pts = [(float(a), d, dfl) for d, dfl in cases for a in GRID]
    res = par(delayed(logs)(*p) for p in pts)
    arr = np.stack(res).reshape(len(cases), len(GRID), T)
    np.save(f"{OUT}/ks_curves.npy", arr)
    print(f"curves done ({time.time() - t0:.0f} s)", flush=True)
