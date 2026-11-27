"""Chance that a 30 % coalition displaces a block after K = 36,000 slots, by the lottery's factor S/D (the study's wait bound)."""
import os
import sys

W = os.path.dirname(os.path.abspath(__file__))
for d in (".cache/numba", ".cache/tmp"):
    os.makedirs(os.path.join(W, d), exist_ok=True)
os.environ["NUMBA_CACHE_DIR"] = os.path.join(W, ".cache", "numba")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = os.path.join(W, ".cache", "tmp")
os.environ["JOBLIB_TEMP_FOLDER"] = os.path.join(W, ".cache", "tmp")
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(W, "..", "..", "..", "src"))       # tools/simulators/finality/src

from joblib import Parallel, delayed  # noqa: E402

F, K = 1 / 30, 36000


def one(share, delta, online, scale):
    import numpy as np
    from finality_sim.waitbound import wait_curve
    s = share if online == 1.0 else share / (share + online * (1 - share))
    c = wait_curve(40000, s, delta, F, floor=0.0, scale=scale)
    hit = np.nonzero(c <= 1e-9)[0]
    return share, delta, online, scale, float(c[K - 1]), (int(hit[0]) + 1) / 3600 if hit.size else float("nan")


if __name__ == "__main__":
    jobs = [(0.30, 15, 1.0, r) for r in (0.95, 0.97, 0.99, 1.0, 1.01, 1.02, 1.03, 1.04, 1.06, 1.08, 1.094, 1.10, 1.12, 1.15, 1.2, 1.25, 1.3,
                                         1.4286, 1.5, 1.75, 2.0)]
    jobs += [(0.30, 10, 1.0, r) for r in (1.0, 1.1, 1.4286, 1.75, 2.0, 2.097)]
    jobs += [(0.30, 10, 0.9, r) for r in (1.0, 1.1, 1.2, 1.3, 1.4)]
    jobs += [(0.30, 12, 1.0, r) for r in (1.0, 1.1, 1.2, 1.4286)]
    for share, delta, online, scale, c, wait in Parallel(n_jobs=4, return_as="generator")(delayed(one)(*j) for j in jobs):
        print(f"share {share:.2f} delay {delta} online {online:.1f} factor {scale:.4f}: chance after 10 h {c:.4e}; wait at 1e-9 {wait:.3f} h",
              flush=True)
