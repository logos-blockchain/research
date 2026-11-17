"""The share a window holds through two and through three disturbances at once.

The disturbances: every honest block 15 slots late (in place of 10), a tenth of the honest stake
offline with the inference corrected to the stake online, and a deflated inference (the coalition
withheld through one observation period). The study's wait bound, nonce unbiased.

Usage: <study's python> share_held_pairs.py <jobs>      writes out_share_held_pairs.txt
"""
import os
import sys

import a_vs_c  # sets the caches and the path to the study  # noqa: F401
from a_vs_c import HOURS, W, cell, run
from joblib import Parallel, delayed

JOBS = [
    ("29 % 15 s, 0.90 online", 0.29, 15, 0.9, 1.0),
    ("31 % 15 s, 0.90 online", 0.31, 15, 0.9, 1.0),
    ("32 % 15 s, 0.90 online", 0.32, 15, 0.9, 1.0),
    ("31 % 10 s, 0.90 online, deflated", 0.31, 10, 0.9, "deflated"),
    ("32 % 10 s, 0.90 online, deflated", 0.32, 10, 0.9, "deflated"),
    ("26 % 15 s, 0.90 online, deflated", 0.26, 15, 0.9, "deflated"),
    ("27 % 15 s, 0.90 online, deflated", 0.27, 15, 0.9, "deflated"),
    ("28 % 15 s, 0.90 online, deflated", 0.28, 15, 0.9, "deflated"),
    ("29 % 15 s, 0.90 online, deflated", 0.29, 15, 0.9, "deflated"),
    ("31 % 15 s, 0.90 online, deflated", 0.31, 15, 0.9, "deflated"),
]

if __name__ == "__main__":
    jobs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    with open(os.path.join(W, "out_share_held_pairs.txt"), "w") as out:
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
