# The window D2 needs if its delay gives no protection, from d2_fallback.out: without the delay D2
# leaves about 2^b fewer choices than today's chain at every cut-off (b = 6: the measured shift in
# the top 1 % of cut-offs is 5.8 to 6.7 bits, and D2's count there is taken from above).
# With G2 = G / 2^b: E[min(1, u min(G2, B) min(G2', B))] = phi_2 of today's chain at budget B 2^b,
# read at u / 4^b. So D2's two-nonce factor at budget B is today's at budget B 2^b, divided by 4^b.
# Windows are read off the wait curves. D1 without its delay is today's chain (repro/recheck.out).
# Usage: python d2_fallback_windows.py > d2_fallback_windows.out
import os
import sys

import numpy as np
from joblib import Parallel, delayed

from delayed_chain import wait_hours, name

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
F, EPS, SHIFT = 1 / 30, 1e-9, 6


def facs(a, delta, bits):
    from finality_sim.grinding import factors, pair_bounds
    ts, lo, up, lo2, up2 = pair_bounds(F, a, budget_bits=bits, depths=4000, floor=100, per_bit=4, delta=delta)
    return factors(ts, lo2, up2, EPS)


if __name__ == "__main__":
    keys = [(a, d, b) for a in (0.30, 1 / 3) for d in (10, 15) for b in (40, 64)]
    today = Parallel(n_jobs=8)(delayed(facs)(a, d, b) for a, d, b in keys)
    moved = Parallel(n_jobs=8)(delayed(facs)(a, d, b + SHIFT) for a, d, b in keys)
    print("share | delay | budget | today's chain (D1 without delay): two-nonce factor, window (h) | D2 without delay: factor, window (h)")
    for (a, d, b), (tl, th), (ml, mh) in zip(keys, today, moved):
        dl, dh = max(1.0, ml / 4.0 ** SHIFT), max(1.0, mh / 4.0 ** SHIFT)
        print(f"{name(a):8s} | {d:2d} s | 2^{b} | {tl:9.3g}-{th:9.3g}  {wait_hours(a, d, tl):6.2f}-{wait_hours(a, d, th):6.2f} | "
              f"{dl:9.3g}-{dh:9.3g}  {wait_hours(a, d, dl):6.2f}-{wait_hours(a, d, dh):6.2f}")
