"""RFC-533, "What a third keeps", with an unbiased nonce: the chance that a third displaces a block
after 10 and after 18 hours, and two waits of its Alternatives.

The study's wait bound. Usage: <study's python> third_keeps.py      writes out_third_keeps.txt
"""
import os
import sys

W = os.path.dirname(os.path.abspath(__file__))
for name, sub in (("NUMBA_CACHE_DIR", ".cache/numba"), ("TMPDIR", ".cache/tmp"), ("JOBLIB_TEMP_FOLDER", ".cache/tmp")):
    path = os.path.join(W, sub)
    os.makedirs(path, exist_ok=True)
    os.environ[name] = path
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, os.path.join(W, "..", "..", "src"))

from joblib import Parallel, delayed  # noqa: E402

F, EPS = 1 / 30, 1e-9
JOBS = [
    ("third 10 s", 1 / 3, 10, 1.0, False),
    ("third 10 s deflated", 1 / 3, 10, 1.0, True),
    ("third 12 s", 1 / 3, 12, 1.0, False),
    ("third 15 s", 1 / 3, 15, 1.0, False),
    ("third 10 s, 0.95 online", 1 / 3, 10, 0.95, False),
    ("third 10 s, 0.96 online", 1 / 3, 10, 0.96, False),
    ("30 % 12 s", 0.30, 12, 1.0, False),
    ("30 % 10 s, 0.86 online", 0.30, 10, 0.86, False),
    ("30 % 10 s, 0.85 online", 0.30, 10, 0.85, False),
]


def run(name, share, delta, online, deflated):
    import numpy as np
    from finality_sim.waitbound import wait_curve
    a = share if online == 1.0 else share / (share + online * (1 - share))
    scale = 1 / (1 - a) if deflated else 1.0
    c = wait_curve(200_000, a, delta, F, floor=1e-24, scale=scale)
    hit = np.nonzero(c <= EPS)[0]
    wait = (hit[0] + 1) / 3600 if hit.size else float("nan")
    return name, a, scale, wait, float(c[36000 - 1]), float(c[64800 - 1])


if __name__ == "__main__":
    with open(os.path.join(W, "out_third_keeps.txt"), "w") as out:
        head = "state | share of the active stake | factor | wait at 1e-9 (h) | chance after 10 h | chance after 18 h"
        print(head, flush=True)
        out.write(head + "\n")
        for name, a, scale, wait, c10, c18 in Parallel(n_jobs=9)(delayed(run)(*j) for j in JOBS):
            line = f"{name} | {a:.4f} | {scale:.4f} | {wait:.2f} | {c10:.2e} | {c18:.2e}"
            print(line, flush=True)
            out.write(line + "\n")
