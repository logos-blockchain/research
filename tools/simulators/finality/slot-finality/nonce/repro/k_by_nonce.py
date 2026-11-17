# The least wait K (hours) that holds 30 % and a third at 1e-9 under each epoch-nonce design,
# read off the finality study's wait bound (finality_sim.waitbound, K.7's GRR-model reading),
# as the RFCs read it: the factor of an attack that meets two nonces divides the target.
# Factors are taken at the worst case of 10 s, where the study derives them; waits at 10 s and 15 s.
#
#   ideal        a nonce no one can bias (a trusted beacon, or a delay that is never broken): 1
#   delayed      the study's candidate (smallest contributions of 25 sub-windows, chained to the
#                parent's, a delay spanning the last sub-window plus 10 minutes): 1.10 per nonce
#                at H.2's bound, squared (the RFCs' "resists grinding", 1.21)
#   minima       the same rule with no delay (SETTLEMENT.md B7, worst case at 10 s): per nonce
#                6.59-9.44 at 30 %, 10.58-18.08 at a third, squared
#   capped       today's hash chain with every candidate costing a delay that parallelises
#                (Phalanx, CIP-0161): the coalition evaluates B candidates an epoch; B6's pair
#                bound computed here at B = 2^8, 2^12 and 2^16 (Phalanx's cap lies between 2^8
#                and 2^16, SETTLEMENT.md B7)
#   today        today's hash chain, B6's pair bound at B = 2^64 (ks_factors.csv)
# Usage: python k_by_nonce.py   (runs from anywhere; paths are relative to this file)
import math
import os
import sys
import time

import numpy as np
from joblib import Parallel, delayed

FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src")
sys.path.insert(0, SRC)

F = 1 / 30
EPS = 1e-9


def need(alpha, delta, factor):
    from finality_sim.waitbound import wait_curve, wait_needed
    eps = EPS / factor
    return wait_needed(wait_curve(1_500_000, alpha, delta, F, floor=eps / 10), eps) / 3600


def capped(alpha, bits):
    from finality_sim.grinding import factors, pair_bounds
    ts, lower, upper, lower2, upper2 = pair_bounds(F, alpha, budget_bits=bits, depths=4000,
                                                   floor=100, per_bit=4, delta=10)
    return factors(ts, lower2, upper2, EPS)


if __name__ == "__main__":
    t0 = time.time()
    par = Parallel(n_jobs=14)
    shares = (0.30, 1 / 3)
    caps = (8, 12, 16)
    cap_rows = par(delayed(capped)(a, b) for a in shares for b in caps)
    cap_f = {(a, b): cap_rows[i * len(caps) + j] for i, a in enumerate(shares)
             for j, b in enumerate(caps)}
    fac = np.genfromtxt(FIG + "/ks_factors.csv", delimiter=",", names=True)

    def today(a):
        i = int(np.argmin(np.abs(fac["alpha"] - a)))
        return float(fac["pair_lo"][i]), float(fac["pair_hi"][i])

    minima = {0.30: (6.59, 9.44), 1 / 3: (10.58, 18.08)}
    designs = []
    for a in shares:
        designs.append((a, "ideal", (1.0, 1.0)))
        designs.append((a, "delayed (study candidate)", (1.21, 1.21)))
        lo, hi = minima[a]
        designs.append((a, "minima, no delay", (lo * lo, hi * hi)))
        for b in caps:
            designs.append((a, f"capped, B = 2^{b}", cap_f[(a, b)]))
        designs.append((a, "today's hash chain", today(a)))
    jobs = [(a, d, f) for a, _, pair in designs for d in (10, 15) for f in pair]
    waits = par(delayed(need)(*j) for j in jobs)
    w = {j: v for j, v in zip(jobs, waits)}
    print(f"factors and waits computed in {time.time() - t0:.0f} s")
    print("share | design | pair factor (lo-hi) | K at 10 s (h) | K at 15 s (h)")
    for a, name, (lo, hi) in designs:
        k10 = (w[(a, 10, lo)], w[(a, 10, hi)])
        k15 = (w[(a, 15, lo)], w[(a, 15, hi)])
        who = "30 %" if a == 0.30 else "a third"
        fstr = f"{lo:.3g}" if lo == hi else f"{lo:.3g}-{hi:.3g}"
        k10s = f"{k10[0]:.2f}" if lo == hi else f"{k10[0]:.2f}-{k10[1]:.2f}"
        k15s = f"{k15[0]:.2f}" if lo == hi else f"{k15[0]:.2f}-{k15[1]:.2f}"
        print(f"{who:8s} | {name:26s} | {fstr:18s} | {k10s:12s} | {k15s}")
