# The study's wait bound (finality_sim.waitbound.wait_curve) for waits of 1 .. 64,800 slots, with no
# floor, against 30 % and a third: 10 s, 10 s deflated, 12 s, 15 s; and against 0.29 and 0.295 at 10 s
# (for the share on the restart path). Each curve is saved to curve_<tag>.npy beside this file.
# Prints: the chance after 10 h and 18 h (plain and x 1.21), and the waits at 1e-9, 1e-9/1.21,
# 1e-9/0.82 and 1e-9/0.26.
# Usage: <study's python> chances_and_waits.py
import os
import sys
import time

W = os.path.dirname(os.path.abspath(__file__))
for d in (".cache/numba", ".cache/tmp"):
    os.makedirs(os.path.join(W, d), exist_ok=True)
os.environ["NUMBA_CACHE_DIR"] = os.path.join(W, ".cache", "numba")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = os.path.join(W, ".cache", "tmp")
os.environ["JOBLIB_TEMP_FOLDER"] = os.path.join(W, ".cache", "tmp")
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
SRC = os.path.join(W, "..", "..", "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import numpy as np  # noqa: E402
from joblib import Parallel, delayed  # noqa: E402

OUT = W
T = 64800
F = 1 / 30


def curve(tag, alpha, delta, deflated):
    import sys
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    import numpy as np
    from finality_sim.waitbound import wait_curve
    t0 = time.time()
    c = wait_curve(T, alpha, delta, F, floor=0.0, scale=1 / (1 - alpha) if deflated else 1.0)
    np.save(f"{OUT}/curve_{tag}.npy", c)
    return tag, c.size, time.time() - t0


def wait(c, eps):
    hit = np.nonzero(c <= eps)[0]
    return int(hit[0]) + 1 if hit.size else -1


if __name__ == "__main__":
    jobs = []
    for a, an in ((0.30, "30"), (1 / 3, "third")):
        for d, dfl, dn in ((10, False, "10"), (10, True, "10dfl"), (12, False, "12"), (15, False, "15")):
            jobs.append((f"{an}_{dn}", a, d, dfl))
    jobs += [("29_10", 0.29, 10, False), ("295_10", 0.295, 10, False)]
    t0 = time.time()
    res = Parallel(n_jobs=6)(delayed(curve)(*j) for j in jobs)
    print(f"curves done in {time.time() - t0:.0f} s: " + ", ".join(f"{t}:{n}:{s:.0f}s" for t, n, s in res))
    print("tag | chance@10h | chance@18h | x1.21 @10h | x1.21 @18h | wait 1e-9 (slots, h) | wait 1e-9/1.21 | "
          "wait 1e-9/0.82 | wait 1e-9/0.26")
    for tag, *_ in jobs:
        c = np.load(f"{OUT}/curve_{tag}.npy")
        w = [wait(c, e) for e in (1e-9, 1e-9 / 1.21, 1e-9 / 0.82, 1e-9 / 0.26)]
        print(f"{tag:12s} | {c[35999]:.3e} | {c[64799]:.3e} | {1.21 * c[35999]:.3e} | {1.21 * c[64799]:.3e} | "
              + " | ".join(f"{x} = {x / 3600:.3f} h" if x > 0 else "past 18 h" for x in w))
