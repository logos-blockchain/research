# The least share of the honest stake online at which the window still holds, nonce unbiased, worst
# case at 10 s, inference corrected to the stake online (the coalition's share of the active stake is
# s / (s + x (1 - s))): 18 h against a third, 10 h against 30 %. For the RFCs' sentences that gave
# 89 / 88 % and 87 / 86 % with the factor 1.21.
# Usage: python online_limit.py > online_limit.out
import os
import sys
import numpy as np
from joblib import Parallel, delayed
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))


def run(share, online):
    from finality_sim.waitbound import wait_curve
    s = share / (share + online * (1 - share))
    c = wait_curve(2_500_000, s, 10, 1 / 30, floor=1e-11)
    hit = np.nonzero(c <= 1e-9)[0]
    return share, online, (hit[0] + 1) / 3600


if __name__ == "__main__":
    jobs = [(1 / 3, x) for x in (0.90, 0.89, 0.88, 0.87)] + [(0.30, x) for x in (0.88, 0.87, 0.86, 0.85)]
    for share, online, w in Parallel(n_jobs=8)(delayed(run)(*j) for j in jobs):
        print(f"{'a third' if share > 0.31 else '30 %'} | {online:.2f} of the honest stake online | wait {w:.2f} h")
