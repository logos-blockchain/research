"""The share a window holds at 15 s after that share deflated the inference.

For each share: the wait at 1e-9 with every honest block 15 slots late, in the epoch after the
coalition withheld through one observation period (both rates raised by 1 / (1 - share)), and the
chance after 10, 15, 18 and 36 hours. The study's wait bound, nonce unbiased.

Usage: <study's python> share_held.py <jobs>      writes out_share_held.txt beside this file
"""
import os
import sys

import a_vs_c  # sets the caches and the path to the study  # noqa: F401
from a_vs_c import HOURS, W, cell, run
from joblib import Parallel, delayed

SHARES = (0.25, 0.26, 0.27, 0.28, 0.29, 0.31, 0.32, 0.34)
JOBS = [(f"{100 * s:.0f} % 15 s deflated", s, 15, 1.0, "deflated") for s in SHARES]

if __name__ == "__main__":
    jobs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    with open(os.path.join(W, "out_share_held.txt"), "w") as out:
        head = ("state | share | lottery's factor | wait at 1e-9 (h) | "
                + " | ".join(f"chance after {h} h" for h in HOURS))
        print(head, flush=True)
        out.write(head + "\n")
        for r in Parallel(n_jobs=jobs, return_as="generator")(delayed(run)(*j) for j in JOBS):
            name, share, delta, online, s, k, wait, at = r
            line = f"{name} | {s:.4f} | {k:.4f} | {wait:.2f} | " + " | ".join(cell(v) for v in at)
            print(line, flush=True)
            out.write(line + "\n")
            out.flush()
