"""Wait-bound curves kept whole, for the bound on rule B (first met) and on rule A at other K.

Rule B makes a block immutable at tau = min(T_k, max(K, T_phi)), where T_n is the time until n
blocks of the chain follow the block. For any t0 <= K:
    P(B fails) <= w(t0) + P(T_k < t0),
because a block displaced after tau >= t0 is a block displaced after a wait of t0, which the wait
bound w covers whatever the adversary does. T_k cannot be shorter than the time the whole stake
needs for k lottery wins with no delay (a chain has one block per slot at most, and the coalition
may add its blocks to speed the chain up), so P(T_k < t0) <= P(Binomial(t0, p_all) >= k).
The other bound on B is the sum w(K) + depth_bound(k).

Usage: python curves.py <jobs>
"""
import math
import sys

import env  # noqa: F401
import numpy as np
from joblib import Parallel, delayed
from scipy.stats import binom

F, k, K = 1 / 30, 2160, 64800
EPS = 1e-9
TH = 1 / 3
CASES = [("third, 10 s", TH, 10, 1.0), ("third, 12 s", TH, 12, 1.0), ("third, 13 s", TH, 13, 1.0),
         ("third, 14 s", TH, 14, 1.0), ("third, 15 s", TH, 15, 1.0),
         ("third, 10 s, deflated (1.5)", TH, 10, 1.5), ("third, 10 s, lottery 1.25", TH, 10, 1.25),
         ("third, 10 s, lottery 1.925", TH, 10, 1.925),
         ("30 %, 10 s", 0.3, 10, 1.0), ("30 %, 15 s", 0.3, 15, 1.0),
         ("30 %, 10 s, deflated (1/0.7)", 0.3, 10, 1 / 0.7)]


def curve(label, alpha, delta, scale):
    from finality_sim.waitbound import wait_curve
    c = wait_curve(K, alpha, delta, F, floor=1e-30, scale=scale)
    return label, alpha, delta, scale, c


if __name__ == "__main__":
    for label, alpha, delta, scale, c in Parallel(n_jobs=int(sys.argv[1]), return_as="generator")(
            delayed(curve)(*x) for x in CASES):
        np.save(f"{env.W}/out/wait_{label.replace(' ', '_').replace(',', '').replace('%', 'pct').replace('/', '-')}.npy", c)
        p_all = 1 - (1 - F) ** scale
        best = (2.0, 0)
        for t0 in range(k, K + 1, 20):
            w = c[t0 - 1] if t0 <= c.size else 0.0
            e = binom.sf(k - 1, t0, p_all) if t0 < K else 0.0   # at t0 = K the slot leg holds K
            if w + e < best[0]:
                best = (w + e, t0)
        early = next(t for t in range(k, 3 * K, 20) if binom.sf(k - 1, t, p_all) >= EPS)
        wK = c[K - 1] if K <= c.size else 0.0
        print(f"{label:32s} w(K)={wK:.2e}  earliest k blocks at 1e-9: {early / 3600:5.2f} h  "
              f"B's bound, best t0={best[1] / 3600:5.2f} h: {best[0]:.2e}", flush=True)
