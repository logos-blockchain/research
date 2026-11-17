# Two readings off the finality study's wait bound (the curves the shorter-K review saved).
# 1. "Accept the bias": the largest share of the stake a window K holds at 1e-9 with today's nonce,
#    with the study's delayed nonce and with no grinding, under a worst case of 10 s and of 15 s.
#    Today's nonce carries B6's factors at 1e-9 (one and two ground nonces, lower and upper bound),
#    which depend on the share and are derived at 10 s, as the RFCs read them.
# 2. A nonce that changes more often than K: a race of K slots then meets more than two nonces.
#    The wait needed when the per-nonce factor 1.10 of the study's delayed nonce is met n times.
# Usage: python accept_bias.py
import math
import os
import sys

import numpy as np
from joblib import Parallel, delayed

OLD = None
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
sys.path.insert(0, FIG)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src"))
from ks_common import EPS, F, GRID, WGRID, fmt_share, held_worst   # noqa: E402


def need(alpha, delta, factor):
    from finality_sim.waitbound import wait_curve, wait_needed
    eps = EPS / factor
    return wait_needed(wait_curve(1_500_000, alpha, delta, F, floor=eps / 10), eps) / 3600


if __name__ == "__main__":
    curves = np.load(FIG + "/ks_curves.npy").astype(np.float64)       # [case, share, wait - 1]
    fac = np.genfromtxt(FIG + "/ks_factors.csv", delimiter=",", names=True)
    assert np.allclose(fac["alpha"], WGRID)
    ln = {k: np.interp(GRID, WGRID, np.log(fac[k])) for k in ("factor_lo", "factor_hi", "pair_lo", "pair_hi")}
    cases = {"10 s": 0, "15 s": 3}
    print("1. largest share held at 1e-9 (>= 1/3 means a third holds)")
    print(f"{'K':>5s} {'delay':>5s} | no grinding | delayed nonce (1.21) | today, one nonce lo-hi | today, two nonces lo-hi")
    for hours in (10, 12, 18):
        col = int(round(hours * 3600)) - 1
        for name, c in cases.items():
            logs = curves[c][:, col]
            cells = [fmt_share(held_worst(logs, EPS)), fmt_share(held_worst(logs, EPS, math.log(1.21)))]
            for a, b in (("factor_lo", "factor_hi"), ("pair_lo", "pair_hi")):
                cells.append(f"{fmt_share(held_worst(logs + ln[b], EPS))}-{fmt_share(held_worst(logs + ln[a], EPS))}")
            print(f"{hours:5d} {name:>5s} | " + " | ".join(cells))
    print("\n2. wait (h) at 1e-9 when a race meets n nonces of factor 1.10 each")
    jobs = [(a, d, n) for a in (0.30, 1 / 3) for d in (10, 15) for n in (2, 3, 4, 7, 19)]
    res = Parallel(n_jobs=12)(delayed(need)(a, d, 1.10 ** n) for a, d, n in jobs)
    for (a, d, n), w in zip(jobs, res):
        who = "30 %" if a == 0.30 else "a third"
        print(f"   {who:8s} {d:2d} s  n={n:2d}  factor {1.10 ** n:6.2f}  wait {w:6.2f} h")
