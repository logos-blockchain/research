"""Option A against option C: what a window of 18 hours and one of 36 hours hold.

The finality study's wait bound on the slot lottery (finality_sim.waitbound.wait_curve), chance
1e-9 a block, nonce unbiased. The study is read only; every cache stays in this directory.

A state is (coalition's share of the stake, worst-case delay in slots, share of the honest stake
online, deflated or not). With part of the honest stake offline the inference is taken as
corrected to the stake online, so the coalition's share of the active stake is
s' = s / (s + x (1 - s)). A deflated inference raises both rates by 1 / (1 - s').

Usage: python3 a_vs_c.py <jobs>      writes out_a_vs_c.txt beside this file
"""
import os
import sys

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
sys.path.insert(0, os.path.join(W, "..", "..", "src"))

from joblib import Parallel, delayed  # noqa: E402

F, EPS, FLOOR = 1 / 30, 1e-9, 1e-13
HOURS = (10, 15, 18, 36)


def run(name, share, delta, online, scale):
    """scale: a number, or "deflated" for 1 / (1 - s')."""
    import numpy as np
    from finality_sim.waitbound import wait_curve
    s = share if online == 1.0 else share / (share + online * (1 - share))
    k = 1 / (1 - s) if scale == "deflated" else float(scale)
    c = wait_curve(1_000_000, s, delta, F, floor=FLOOR, scale=k)
    hit = np.nonzero(c <= EPS)[0]
    wait = (hit[0] + 1) / 3600 if hit.size else float("nan")
    # A curve that ends before an hour ended because the bound fell to FLOOR or below.
    at = [float(c[h * 3600 - 1]) if c.size >= h * 3600 else -1.0 for h in HOURS]
    return name, share, delta, online, s, k, wait, at


THIRD, P30 = 1 / 3, 0.30
JOBS = [
    # Known figures, to check this setup.
    ("check 35.57 h, 2.83e-5 at 18 h", THIRD, 15, 1.0, "deflated"),
    ("check 16.23 h", THIRD, 10, 0.9, 1.0),
    ("check 17.37 h", THIRD, 15, 1.0, 1.0),
    ("check 14.20 h", P30, 15, 1.0, "deflated"),
    # A third, one disturbance at a time, beyond the K row's cases.
    ("third 18 s", THIRD, 18, 1.0, 1.0),
    ("third 20 s", THIRD, 20, 1.0, 1.0),
    ("third 21 s", THIRD, 21, 1.0, 1.0),
    ("third 22 s", THIRD, 22, 1.0, 1.0),
    ("third 10 s, 0.80 online", THIRD, 10, 0.8, 1.0),
    ("third 10 s, 0.75 online", THIRD, 10, 0.75, 1.0),
    # A third, two disturbances.
    ("third 15 s, 0.90 online", THIRD, 15, 0.9, 1.0),
    ("third 12 s, 0.90 online", THIRD, 12, 0.9, 1.0),
    ("third 16 s deflated", THIRD, 16, 1.0, "deflated"),
    ("third 17 s deflated", THIRD, 17, 1.0, "deflated"),
    ("third 10 s, 0.90 online, deflated", THIRD, 10, 0.9, "deflated"),
    ("third 12 s, 0.90 online, deflated", THIRD, 12, 0.9, "deflated"),
    # A third, all three.
    ("third 15 s, 0.90 online, deflated", THIRD, 15, 0.9, "deflated"),
    # The lottery's factor that 36 hours holds at 15 s.
    ("third 15 s, factor 1.52", THIRD, 15, 1.0, 1.52),
    ("third 15 s, factor 1.55", THIRD, 15, 1.0, 1.55),
    # 30 %, for the ten-hour variant.
    ("30 % 15 s, 0.90 online", P30, 15, 0.9, 1.0),
    ("30 % 16 s deflated", P30, 16, 1.0, "deflated"),
    ("30 % 20 s", P30, 20, 1.0, 1.0),
    ("30 % 10 s, 0.90 online, deflated", P30, 10, 0.9, "deflated"),
    ("30 % 15 s, 0.90 online, deflated", P30, 15, 0.9, "deflated"),
]


def cell(v):
    return "below 1e-13" if v < 0 else f"{v:.2e}"


if __name__ == "__main__":
    jobs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    with open(os.path.join(W, "out_a_vs_c.txt"), "w") as out:
        head = ("state | coalition's share of the active stake | lottery's factor | wait at 1e-9 (h) | "
                + " | ".join(f"chance after {h} h" for h in HOURS))
        print(head, flush=True)
        out.write(head + "\n")
        for r in Parallel(n_jobs=jobs, return_as="generator")(delayed(run)(*j) for j in JOBS):
            name, share, delta, online, s, k, wait, at = r
            line = f"{name} | {s:.4f} | {k:.4f} | {wait:.2f} | " + " | ".join(cell(v) for v in at)
            print(line, flush=True)
            out.write(line + "\n")
            out.flush()
