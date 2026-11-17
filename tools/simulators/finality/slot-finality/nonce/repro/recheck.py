# Recomputation after the independent review, which found the mix.
# The finality study takes B6's grinding factor at the wait's own delay for today's nonce
# (scripts/k2_holds.py); only the delayed nonce carries a factor derived at 10 s under a 15 s wait.
# 1. Waits at 10 s and 15 s for today's hash chain when a coalition evaluates 2^bits candidates an
#    epoch, with the pair factor (two nonces met) taken at the same delay. bits = 64 is the study's
#    budget for "today's nonce"; 8, 16, 24 are caps of the Phalanx kind: with 82 pieces of 52.7 s on
#    the coalition's hardware and a 108-hour window, one machine checks 90 candidates an epoch, so
#    2^8, 2^16, 2^24 are about 3, 730 and 186,000 machines.
# 2. Reading A (a nonce used from its cut-off on): a race that crosses the cut-off runs on a nonce the
#    racing chain chose among the 2^bits it evaluated, with certainty. In the study's union bound the
#    factor is the one-nonce factor of the epoch it started in, times 2^bits: phi(u * B) = eps.
# 3. The largest share 18 h and 10 h hold under a worst case of 15 s with today's nonce, with the
#    factors taken at 15 s.
# Usage: python recheck.py
import math
import os
import sys
import time

import numpy as np
from joblib import Parallel, delayed

OLD = None
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
sys.path.insert(0, FIG)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src"))
from ks_common import EPS, F, GRID, WGRID, fmt_share, held_worst   # noqa: E402


def facs(a, delta, bits):
    from finality_sim.grinding import factors, pair_bounds
    ts, lo, up, lo2, up2 = pair_bounds(F, a, budget_bits=bits, depths=4000, floor=100, per_bit=4, delta=delta)
    f1 = factors(ts, lo, up, EPS)
    f2 = factors(ts, lo2, up2, EPS)
    return (f1[0], f1[1], f2[0], f2[1])


def need(alpha, delta, factor):
    from finality_sim.waitbound import wait_curve, wait_needed
    eps = EPS / factor
    return wait_needed(wait_curve(2_500_000, alpha, delta, F, floor=eps / 10), eps) / 3600


if __name__ == "__main__":
    t0 = time.time()
    par = Parallel(n_jobs=14)
    shares = (0.30, 1 / 3)
    bits = (8, 16, 24, 40, 64)
    keys = [(a, d, b) for a in shares for d in (10, 15) for b in bits]
    fres = par(delayed(facs)(*k) for k in keys)
    fac = dict(zip(keys, fres))
    print(f"factors done in {time.time() - t0:.0f} s", flush=True)
    jobs = {}
    for (a, d, b), (l1, h1, l2, h2) in fac.items():
        jobs[("pair", a, d, b, "lo")] = (a, d, l2)
        jobs[("pair", a, d, b, "hi")] = (a, d, h2)
        if b in (40, 64):
            jobs[("readA", a, d, b, "lo")] = (a, d, l1 * 2.0 ** b)
            jobs[("readA", a, d, b, "hi")] = (a, d, h1 * 2.0 ** b)
    names = list(jobs)
    waits = par(delayed(need)(*jobs[n]) for n in names)
    w = dict(zip(names, waits))
    print(f"waits done in {time.time() - t0:.0f} s", flush=True)
    for a in shares:
        who = "30 %" if a == 0.30 else "a third"
        for d in (10, 15):
            for b in bits:
                l1, h1, l2, h2 = fac[(a, d, b)]
                print(f"{who:8s} {d:2d} s  2^{b:<2d}: one nonce {l1:9.3g}-{h1:9.3g}  pair {l2:9.3g}-{h2:9.3g}  "
                      f"wait {w[('pair', a, d, b, 'lo')]:6.2f}-{w[('pair', a, d, b, 'hi')]:6.2f} h", flush=True)
            for b in (40, 64):
                print(f"{who:8s} {d:2d} s  reading A, a race across the cut-off, 2^{b} evaluated: "
                      f"wait {w[('readA', a, d, b, 'lo')]:6.2f}-{w[('readA', a, d, b, 'hi')]:6.2f} h", flush=True)
    # 3. shares held at 15 s with factors at 15 s
    grid_f = par(delayed(facs)(float(a), 15, 64) for a in WGRID)
    arr = np.array(grid_f)
    curves = np.load(FIG + "/ks_curves.npy").astype(np.float64)
    ln = {i: np.interp(GRID, WGRID, np.log(arr[:, i])) for i in range(4)}
    print("largest share held at 1e-9 under a worst case of 15 s, today's nonce, factors at 15 s")
    for hours in (10, 12, 18):
        logs = curves[3][:, int(round(hours * 3600)) - 1]
        one = f"{fmt_share(held_worst(logs + ln[1], EPS))}-{fmt_share(held_worst(logs + ln[0], EPS))}"
        two = f"{fmt_share(held_worst(logs + ln[3], EPS))}-{fmt_share(held_worst(logs + ln[2], EPS))}"
        print(f"   K = {hours:2d} h: one ground nonce {one}; two ground nonces {two}")
    print(f"done in {time.time() - t0:.0f} s")
