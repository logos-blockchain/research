"""Rule B (first met) and rule D (depth with a minimum age): a bound from the wait bound alone.

A rule makes a block immutable at a time tau. If tau >= t0 on every path but a set of chance e,
then P(displaced after tau) <= w(t0) + e, where w is the study's wait bound (curves.py saved it).

  B:  tau = min(T_k, max(K, T_phi)) >= min(T_k, K).  For t0 <= K: e = P(T_k < t0).
  DEPTH alone: tau = T_k.                              For any t0: e = P(T_k < t0).
  T_k >= the time the whole stake (scale times the inferred stake) needs for k lottery wins,
  because a chain holds one block per slot at most and the coalition may add its blocks to the
  chain to make it grow. So P(T_k < t0) <= P(Binomial(t0 - 1, p_all) >= k).

This bound does not use the depth bound. The other bound on B is w(K) + depth_bound(k).
(curves.py printed a first version that left e out at t0 = K. That was wrong: use this script.)
"""
import glob
import math
import os

import numpy as np
from scipy.stats import binom

F, k, K = 1 / 30, 2160, 64800
EPS = 1e-9
W = os.path.dirname(os.path.abspath(__file__))
SCALE = {"deflated_(1.5)": 1.5, "lottery_1.25": 1.25, "lottery_1.925": 1.925, "deflated_(1-0.7)": 1 / 0.7}

for path in sorted(glob.glob(f"{W}/out/wait_*.npy")):
    name = os.path.basename(path)[5:-4]
    scale = next((v for s, v in SCALE.items() if name.endswith(s)), 1.0)
    c = np.load(path)
    p_all = 1 - (1 - F) ** scale

    def w(t):
        return float(c[t - 1]) if t <= c.size else 0.0   # below 1e-30 past the curve's end

    best = (2.0, 0)
    for t0 in range(k, K + 1, 10):
        v = w(t0) + float(binom.sf(k - 1, t0 - 1, p_all))
        if v < best[0]:
            best = (v, t0)
    need = next((t for t in range(1, c.size + 1) if c[t - 1] <= EPS), None)
    early = next(t for t in range(k, 3 * K, 10) if binom.sf(k - 1, t - 1, p_all) >= EPS)
    med = next(t for t in range(k, 3 * K, 10) if binom.sf(k - 1, t - 1, p_all) >= 0.5)
    print(f"{name:34s} scale {scale:5.3f}  wait needed {need / 3600 if need else float('nan'):5.2f} h  "
          f"SLOT w(K) {w(K):.1e}  |  k blocks earliest {early / 3600:5.2f} h, median {med / 3600:5.2f} h  |  "
          f"B's bound {best[0]:.1e} at t0 = {best[1] / 3600:5.2f} h  -> {'holds' if best[0] <= EPS else 'NOT shown'}")
