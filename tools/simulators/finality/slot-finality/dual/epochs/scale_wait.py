"""The wait the window must cover when the lottery runs faster than f by a factor `scale`
(a deflated inference, or stake that returned before the inference counted it), by delay.
Study's wait bound on the slot lottery, chance 1e-9, nonce unbiased. Usage: python scale_wait.py <jobs>
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402,F401
from joblib import Parallel, delayed  # noqa: E402

F, EPS = 1 / 30, 1e-9


def need(name, alpha, d, scale):
    from finality_sim.waitbound import wait_curve, wait_needed
    c = wait_curve(500_000, alpha, d, F, floor=EPS / 10, scale=scale)
    w = wait_needed(c, EPS)
    k18 = float(c[64800 - 1]) if c.size >= 64800 else 0.0
    k10 = float(c[36000 - 1]) if c.size >= 36000 else 0.0
    return name, d, scale, (w / 3600 if w > 0 else float("nan")), k18, k10


JOBS = [("third", 1 / 3, d, s) for d in (6, 10, 12, 15) for s in (1.0, 1.02, 1.05, 1.1, 1.2, 1.3, 1.4, 1.5, 1.75, 2.0)]
JOBS += [("30 %", 0.3, d, s) for d in (6, 10, 15) for s in (1.0, 1.05, 1.1, 1.2, 1.3, 1.43, 1.75, 2.0)]

if __name__ == "__main__":
    out = open("out/scale_wait.txt", "w")
    for r in Parallel(n_jobs=int(sys.argv[1]), return_as="generator")(delayed(need)(*j) for j in JOBS):
        line = f"{r[0]:6s} delay {r[1]:2d} s  scale {r[2]:5.2f}  wait {r[3]:7.2f} h   chance at 18 h {r[4]:.1e}   at 10 h {r[5]:.1e}"
        print(line, flush=True)
        out.write(line + "\n")
        out.flush()
