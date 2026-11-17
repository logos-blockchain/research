"""Check of the capped-grinding waits against 30 %: a coalition that holds B nonces at both cut-offs.

Two nonces met, so the factor is B squared, and the wait is the first t with chance <= 1e-9 / B^2.
The study's wait bound, no other disturbance. Usage: <study's python> caps_check.py
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

import numpy as np  # noqa: E402
from finality_sim.waitbound import wait_curve  # noqa: E402

F, EPS = 1 / 30, 1e-9

for share, label in ((0.30, "30 %"), (1 / 3, "a third")):
    for delta in (10, 15):
        c = wait_curve(400_000, share, delta, F, floor=1e-27, scale=1.0)
        cells = []
        for bits in (0, 8, 16, 24):
            hit = np.nonzero(c <= EPS / 2.0 ** (2 * bits))[0]
            cells.append(f"2^{bits}: {(hit[0] + 1) / 3600:.2f} h" if hit.size else f"2^{bits}: not reached")
        print(f"{label}, {delta} s | " + " | ".join(cells), flush=True)
