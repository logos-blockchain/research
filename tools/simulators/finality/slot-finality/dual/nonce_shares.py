"""The largest share each leg holds at 1e-9 with today's epoch nonce, worst case at 10 s.

A leg holds a share when its bound times the grinding factor R is at most 1e-9. R is the study's
(SETTLEMENT.md B6), as reproduced per share at 10 s:
../nonce/data/ks_factors.csv (factor = one ground nonce, pair = two; lo and hi are the two
bounds on the factor). R does not depend on the leg. Between grid shares log R and the log of the
bound are interpolated linearly.

Legs: 2,160 blocks at the code's count; at the paper's count (code's curve at 4,320); a wait of
64,800 slots; a wait of 36,000 slots.  A holds what its better leg holds. B holds what its worse
leg holds.

Usage: python nonce_shares.py <jobs>
"""
import math
import sys

import env  # noqa: F401
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

F, k, K18, K10, EPS = 1 / 30, 2160, 64800, 36000, 1e-9
FLOOR = 1e-45
FAC = pd.read_csv(f"{env.W}/../nonce/data/ks_factors.csv")
GRID = [a for a in FAC.alpha if 0.20 <= a <= 0.3401]


def legs(alpha):
    from bounds import alphabet_for
    from finality_sim.lcbounds import slot_pdf, ub_curve
    from finality_sim.waitbound import wait_curve
    d = F * 10
    a = alphabet_for(alpha, d)
    c = ub_curve(2 * k, slot_pdf(1 - alpha, d, a), a, max(30, a + 1), 1e-16, FLOOR)
    w = wait_curve(K18, alpha, 10, F, floor=FLOOR)

    def at(x, n):
        return math.log(max(float(x[n - 1]), FLOOR)) if n <= x.size else math.log(FLOOR)
    return dict(alpha=alpha, depth_code=at(c, k), depth_paper=at(c, 2 * k), wait18=at(w, K18),
                wait10=at(w, K10))


def held(alphas, logb, logr):
    """Largest share with logb + logr <= log(EPS), linear between grid points."""
    m = np.asarray(logb) + np.asarray(logr) - math.log(EPS)
    if m[0] > 0:
        return float("nan")
    for i in range(1, len(m)):
        if m[i] > 0:
            return float(alphas[i - 1] + (alphas[i] - alphas[i - 1]) * (-m[i - 1]) / (m[i] - m[i - 1]))
    return float(alphas[-1])   # holds over the whole grid: at least this


if __name__ == "__main__":
    rows = Parallel(n_jobs=int(sys.argv[1]))(delayed(legs)(a) for a in GRID)
    t = pd.DataFrame(rows).merge(FAC, on="alpha")
    t.to_csv(f"{env.W}/out/nonce_legs.csv", index=False)
    print(f"grid of shares: {GRID[0]:.3f} to {GRID[-1]:.3f}; a value equal to the grid's end means 'at least'")
    print(f"{'grinding':34s} {'2,160 blk code':>15s} {'2,160 blk paper':>16s} {'18 h':>7s} {'10 h':>7s}")
    for name, col in (("none", None), ("one nonce, lower", "factor_lo"), ("one nonce, upper", "factor_hi"),
                      ("two nonces, lower", "pair_lo"), ("two nonces, upper", "pair_hi")):
        lr = np.zeros(len(t)) if col is None else np.log(t[col])
        print(f"{name:34s} " + " ".join(
            f"{held(t.alpha.values, t[leg].values, lr):>{wd}.3f}"
            for leg, wd in (("depth_code", 15), ("depth_paper", 16), ("wait18", 7), ("wait10", 7))))
