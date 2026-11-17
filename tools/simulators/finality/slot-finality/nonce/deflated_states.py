# For the RFCs: the two-epoch attack with the nonce unbiased (withhold for
# one observation period, race in the next epoch at thresholds raised by 1/(1 - share)), from the
# finality study's wait bound (waitbound.wait_curve with scale).
#  (a) chance of displacement after 18 h against a third at 10 to 15 s, after 10 h against 30 % at 10 to 15 s;
#  (b) the deflated inference together with 90 % of the honest stake online (the inference first
#      corrected to the stake online: the coalition's share of the active stake is
#      s' = s / (s + 0.9 (1 - s)); then deflated by the coalition's withholding: scale 1 / (1 - s')).
# Usage: python deflated_states.py > deflated_states.out
import os
import sys
import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
F, EPS = 1 / 30, 1e-9


def run(share, delta, online):
    from finality_sim.waitbound import wait_curve
    s = share if online == 1.0 else share / (share + online * (1 - share))
    c = wait_curve(2_500_000, s, delta, F, floor=1e-13, scale=1 / (1 - s))
    hit = np.nonzero(c <= EPS)[0]
    wait = (hit[0] + 1) / 3600 if hit.size else float("nan")
    at = lambda hh: float(c[hh * 3600 - 1]) if c.size >= hh * 3600 else float("nan")
    return share, delta, online, s, wait, at(18), at(10)


if __name__ == "__main__":
    jobs = [(a, d, 1.0) for a in (1 / 3, 0.30) for d in (10, 11, 12, 13, 14, 15)] + \
           [(a, d, 0.9) for a in (1 / 3, 0.30) for d in (10, 15)]
    print("share | delay | honest online | coalition's share of the active stake | wait at 1e-9 (h) | chance after 18 h | chance after 10 h")
    for share, delta, online, s, wait, c18, c10 in Parallel(n_jobs=12)(delayed(run)(*j) for j in jobs):
        who = "30 %" if share == 0.30 else "a third"
        print(f"{who:8s} | {delta:2d} s | {online:.1f} | {s:.4f} | {wait:6.2f} | {c18:.2e} | {c10:.2e}")
