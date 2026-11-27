"""Question (A): the repaired condition of SCHEDULE 3.6 at a first phase of 72,000, 108,000 and 144,000 slots, every state.

commit route     : min over g of  F(g) + A(g) + span(L1 - g)
                   F, A = the repaired 5.4 (floor and age part, active coalition) for the snapshot read at s0 and used at s0+g;
                   span(w) = no honest block of the final chain in w consecutive slots (GENESIS 6.1's inequality, +1 form).
                   Premises: S, GENESIS A1-A3.  U is not used.
settlement route : min over j of  U(L1 - j - 2) + span(j).   Premises: A6 and the study's clock (U), S, A1-A3.
Also the least L1 at 1e-9 (total) for each route.
"""
import os

import numpy as np

import r3_final as rf
import walk as w

GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "proofs", "genesis", ".cache")   # U, cached by g07_states.py
CUR = {"no disturbance": (0.3, 10, 1.0), "every block 15 late": (0.3, 15, 1.0),
       "tenth offline, corrected": (0.3 / 0.93, 10, 1.0), "tenth offline, before": (0.3 / 0.93, 10, 0.93),
       "D = honest online": (0.3, 10, 1 / 0.7)}
L1S = (72_000, 108_000, 144_000)
STEP = 250

for name, xh, xa, D in w.STATES:
    h, a = w.p_of(xh), w.p_of(xa)
    pre, post, inf, th = w.tails(h, a, D)
    al, d, sc = CUR[name]
    u = np.load(os.path.join(GEN, f"U_a{al:.6f}_d{d}_t160000_s{sc:.6f}.npy"), mmap_mode="r")
    js = np.arange(500, 100_001, STEP)
    sp = np.array([w.P1(int(j), h, a, D, pre, post, 1) for j in js])
    gs = np.arange(36_750, 110_001, STEP)
    fa = np.array([min(1.0, rf.floor_part(int(g), h, a, D, pre) + rf.age_part(int(g), h, a, D, pre, post)[0]) for g in gs])

    def settle(L1):
        ok = js < L1 - 100
        return float(np.min(u[L1 - js[ok] - 2 - 1] + sp[ok]))

    def commit(L1):
        best = 1.0
        for g, v in zip(gs, fa):
            wspan = L1 - g
            if wspan < js[0]:
                break
            k = min((wspan - js[0]) // STEP, len(js) - 1)      # span is non-increasing: rounding the span down is conservative
            best = min(best, v + sp[k])
        return float(best)

    def least(fn, lo, hi):
        while lo < hi:
            mid = (lo + hi) // 2
            if fn(mid) <= 1e-9:
                hi = mid
            else:
                lo = mid + 1
        return lo

    print(f"{name:26s} d={D}: commit " + ", ".join(f"{L}: {commit(L):.1e}" for L in L1S)
          + " | settlement " + ", ".join(f"{L}: {settle(L):.1e}" for L in L1S)
          + f" | least L1 at 1e-9: commit {least(commit, 40_000, 100_000)} (grid {STEP}), settlement {least(settle, 2_000, 90_000)}", flush=True)
