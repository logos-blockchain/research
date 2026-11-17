"""Recheck of the rows for "K stays 18 h with its premise stated" against "K = 36 h".
Study's wait bound on the slot lottery, nonce unbiased, chance 1e-9, f = 1/30. Own job list;
the bound itself is the study's code (finality_sim.waitbound), the same that the rechecked rows use.
Usage: python recheck.py <jobs>   writes out/recheck.txt
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402,F401
from joblib import Parallel, delayed  # noqa: E402

F, EPS = 1 / 30, 1e-9


def online(a, u):
    return a / (a + (1 - a) * u)


def need(name, alpha, d, scale):
    from finality_sim.waitbound import wait_curve, wait_needed
    c = wait_curve(400_000, alpha, d, F, floor=EPS / 100, scale=scale)
    w = wait_needed(c, EPS)
    at = lambda t: float(c[t - 1]) if c.size >= t else 0.0
    return name, alpha, d, scale, (w / 3600 if w > 0 else float("nan")), at(64800), at(129600)


JOBS = [
    ("1 third, tenth offline, 15 s", online(1 / 3, 0.9), 15, 1.0),
    ("2 third, 16 s, deflated 1.5", 1 / 3, 16, 1.5),
    ("2 third, 15 s, deflated 1.5", 1 / 3, 15, 1.5),
    ("3 third, 20 s", 1 / 3, 20, 1.0),
    ("3 third, 21 s", 1 / 3, 21, 1.0),
    ("4 third, 80 % online, 10 s", online(1 / 3, 0.8), 10, 1.0),
    ("5 31 %, 15 s, deflated", 0.31, 15, 1 / 0.69),
    ("5 32 %, 15 s, deflated", 0.32, 15, 1 / 0.68),
    ("6 31 %, tenth offline, 15 s", online(0.31, 0.9), 15, 1.0),
]

if __name__ == "__main__":
    from scipy.stats import binom
    out = open("out/recheck.txt", "w")
    for K in (129600, 54000, 64800, 36000):
        n = 0
        while 36000 >= 0 and binom.cdf(n, K - (n + 1) * 15, F) <= EPS:
            n += 1
        line = f"7 floor at K = {K}: {n}   P(N < floor) = {binom.cdf(n - 1, K - n * 15, F):.3g}   P(N < floor + 1) = {binom.cdf(n, K - (n + 1) * 15, F):.3g}"
        print(line, flush=True); out.write(line + "\n")
    for r in Parallel(n_jobs=int(sys.argv[1]), return_as="generator")(delayed(need)(*j) for j in JOBS):
        line = f"{r[0]:30s} share {r[1]:.4f} delay {r[2]:2d} scale {r[3]:.4f}  wait {r[4]:6.2f} h   after 18 h {r[5]:.3g}   after 36 h {r[6]:.3g}"
        print(line, flush=True); out.write(line + "\n"); out.flush()
