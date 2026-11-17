"""Rule B (the first count met: 2,160 blocks, or 18 h and the floor) after a deflation.
Bound 1 (no depth bound): min over t0 <= K of w(t0) + P(Binomial(t0 - 1, p_all) >= k), as b_bound.py.
Bound 2: w(K) + depth bound at k (read from depth_fast*.txt by hand).
Usage: python b_fast.py > out/b_fast.txt
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402,F401
from joblib import Parallel, delayed  # noqa: E402
from scipy.stats import binom  # noqa: E402

F, k, K = 1 / 30, 2160, 64800


def case(name, a, d):
    from finality_sim.waitbound import wait_curve
    sc = 1 / (1 - a)
    c = wait_curve(K, a, d, F, floor=1e-13, scale=sc)
    w = lambda t: float(c[t - 1]) if t <= c.size else 0.0
    p_all = 1 - (1 - F) ** sc
    best = min((w(t0) + float(binom.sf(k - 1, t0 - 1, p_all)), t0) for t0 in range(k, K + 1, 10))
    return f"{name}, {d} s, deflated (scale {sc:.4f}): w(K) = {w(K):.2g}; B's bound 1 = {best[0]:.2g} at t0 = {best[1] / 3600:.2f} h -> {'holds' if best[0] <= 1e-9 else 'not shown'}"


if __name__ == "__main__":
    jobs = [("30 %", 0.30, 10), ("30 %", 0.30, 12), ("30 %", 0.30, 15), ("a third", 1 / 3, 10), ("a third", 1 / 3, 12), ("a third", 1 / 3, 15)]
    for line in Parallel(n_jobs=3)(delayed(case)(*j) for j in jobs):
        print(line, flush=True)
