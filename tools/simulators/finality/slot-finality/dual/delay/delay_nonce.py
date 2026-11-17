"""The window by delay with the two-nonce factor of the single-delay design
(../../nonce/factor_by_delay.out), against a third. Three of its cases:
  A  delay of 4.5 h, 100 delay machines of the coalition
  B  delay of 6 h, 10,000 machines
  C  delay of 4.5 h, 10,000 machines
The factor R divides the target: the wait bound must be at most 1e-9 / R.
'offline' applies the same R to the case with a tenth of the honest stake offline (R is given
for the share only, so this is an assumption).
Usage: python delay_nonce.py <jobs>
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402,F401
from joblib import Parallel, delayed  # noqa: E402

F, EPS = 1 / 30, 1e-9
FAC = {}
for line in open(os.path.join(env.W, "..", "nonce", "factor_by_delay.out")):
    if line.startswith("a third"):
        p = [x.strip() for x in line.split("|")]
        v = [float(x) for x in p[2:]]
        FAC[int(p[1].split()[0])] = dict(A=v[1], B=v[4], C=v[2])


def need(d, case, kind, alpha, eps):
    from finality_sim.waitbound import wait_curve, wait_needed
    w = wait_needed(wait_curve(400_000, alpha, d, F, floor=eps / 10), eps)
    return d, case, kind, w / 3600


if __name__ == "__main__":
    a3, off = 1 / 3, (1 / 3) / (1 / 3 + (2 / 3) * 0.9)
    jobs = [(d, c, k, al, EPS / FAC[d][c]) for d in range(5, 16) for c in "ABC" for k, al in (("plain", a3), ("offline", off))]
    res = {}
    for d, c, k, h in Parallel(n_jobs=int(sys.argv[1]))(delayed(need)(*j) for j in jobs):
        res[(d, c, k)] = h
    print("Against a third. R = two-nonce factor; wait in hours; window = least whole hours.")
    print(f"{'delay':>5s} | " + " | ".join(f"{c}: {'R':>8s} {'wait':>6s} {'win':>4s} {'offline':>7s}" for c in "ABC"))
    for d in range(5, 16):
        print(f"{d:5d} | " + " | ".join(
            f"{c}: {FAC[d][c]:8.5g} {res[(d, c, 'plain')]:6.2f} {math.ceil(res[(d, c, 'plain')]):3d}h {res[(d, c, 'offline')]:7.2f}" for c in "ABC"))
