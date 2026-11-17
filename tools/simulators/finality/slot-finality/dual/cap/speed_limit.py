"""How fast the lottery may run before a window stops holding a third, by delay.
Study's wait bound on the slot lottery, nonce unbiased, chance 1e-9, f = 1/30. For each delay
10..15 s and each scale 1.00..1.60 (step 0.01): the chance after 18 h and after 36 h.
Usage: python speed_limit.py <jobs>   writes out/speed_limit.csv and out/speed_limit.txt
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402,F401
from joblib import Parallel, delayed  # noqa: E402

F, EPS = 1 / 30, 1e-9


def run(d, s):
    from finality_sim.waitbound import wait_curve
    c = wait_curve(129_600, 1 / 3, d, F, floor=EPS / 100, scale=s)
    at = lambda t: float(c[t - 1]) if c.size >= t else 0.0
    return d, s, at(64800), at(129600)


if __name__ == "__main__":
    jobs = [(d, round(1 + i / 100, 2)) for d in range(10, 16) for i in range(0, 61)]
    rows = []
    with open("out/speed_limit.csv", "w") as o:
        o.write("delay,scale,chance_18h,chance_36h\n")
        for r in Parallel(n_jobs=int(sys.argv[1]), return_as="generator")(delayed(run)(*j) for j in jobs):
            rows.append(r); o.write("%d,%.2f,%.4g,%.4g\n" % r); o.flush()
    with open("out/speed_limit.txt", "w") as o:
        for d in range(10, 16):
            for name, i in (("18 h", 2), ("36 h", 3)):
                ok = [r[1] for r in rows if r[0] == d and r[i] <= EPS]
                bad = [r[1] for r in rows if r[0] == d and r[i] > EPS]
                line = f"delay {d} s, {name}: holds a third up to a lottery {max(ok) if ok else 'none'} times fast; first failure at {min(bad) if bad else 'above 1.60'}"
                print(line); o.write(line + "\n")
