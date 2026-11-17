"""Option B: the lottery's factor each window holds at 15 s, and the rows the RFCs gain.

A factor is the rate of the lottery against f: the total active stake over the inferred total
stake. The study's wait bound, nonce unbiased, chance 1e-9 a block.

Usage: <study's python> limits.py <jobs> [stage]      writes out_limits[_<stage>].txt
"""
import os
import sys

import a_vs_c  # sets the caches and the path to the study  # noqa: F401
from a_vs_c import HOURS, W, cell, run
from joblib import Parallel, delayed

STAGES = {
    "1": [
        # a third at 15 s, against 18 h
        *[(f"third 15 s, factor {k:.3f}", 1 / 3, 15, 1.0, k)
          for k in (1.030, 1.032, 1.034, 1.035, 1.036, 1.037, 1.038, 1.040)],
        # 30 % at 15 s, against 18 h
        *[(f"30 % 15 s, factor {k:.3f}", 0.30, 15, 1.0, k) for k in (1.50, 1.55, 1.60, 1.65, 1.70)],
        # 30 % at 15 s, against 10 h
        *[(f"30 % 15 s, factor {k:.3f}", 0.30, 15, 1.0, k) for k in (1.04, 1.06, 1.08, 1.10, 1.12)],
        # the share 10 h holds at 15 s with a tenth of the honest stake offline
        ("27 % 15 s, 0.90 online", 0.27, 15, 0.9, 1.0),
        ("28 % 15 s, 0.90 online", 0.28, 15, 0.9, 1.0),
        # the three cases of the row against 30 %, and no disturbance
        ("30 % 10 s", 0.30, 10, 1.0, 1.0),
        ("30 % 15 s", 0.30, 15, 1.0, 1.0),
        ("30 % 10 s, 0.90 online", 0.30, 10, 0.9, 1.0),
        ("30 % 10 s deflated", 0.30, 10, 1.0, "deflated"),
    ],
    # 30 % against 18 h: how far each case and each pair of cases reaches
    "2": [
        ("30 % 21 s", 0.30, 21, 1.0, 1.0),
        ("30 % 22 s", 0.30, 22, 1.0, 1.0),
        ("30 % 17 s deflated", 0.30, 17, 1.0, "deflated"),
        ("30 % 18 s deflated", 0.30, 18, 1.0, "deflated"),
        ("30 % 16 s, 0.90 online", 0.30, 16, 0.9, 1.0),
        ("30 % 17 s, 0.90 online", 0.30, 17, 0.9, 1.0),
        ("30 % 18 s, 0.90 online", 0.30, 18, 0.9, 1.0),
        *[(f"30 % 10 s, {o:.2f} online", 0.30, 10, o, 1.0)
          for o in (0.85, 0.80, 0.78, 0.76, 0.75, 0.74, 0.72, 0.70)],
        ("30 % 10 s, 0.85 online, deflated", 0.30, 10, 0.85, "deflated"),
        ("30 % 10 s, 0.80 online, deflated", 0.30, 10, 0.80, "deflated"),
        *[(f"30 % {d} s, 0.90 online, deflated", 0.30, d, 0.9, "deflated") for d in (11, 12, 13, 14)],
    ],
}

if __name__ == "__main__":
    jobs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    stage = sys.argv[2] if len(sys.argv) > 2 else "1"
    if stage not in STAGES:
        # a refinement: stage is "<share>:<delay>:<k1>,<k2>,..."
        share, delay, ks = stage.split(":")
        rows = [(f"{float(share):.4f} {delay} s, factor {float(k):.3f}", float(share), int(delay), 1.0, float(k))
                for k in ks.split(",")]
        name = "out_limits_refine_" + stage.replace(":", "_").replace(",", "-") + ".txt"
    else:
        rows = STAGES[stage]
        name = f"out_limits_{stage}.txt"
    with open(os.path.join(W, name), "w") as out:
        head = ("state | coalition's share of the active stake | lottery's factor | wait at 1e-9 (h) | "
                + " | ".join(f"chance after {h} h" for h in HOURS))
        print(head, flush=True)
        out.write(head + "\n")
        for r in Parallel(n_jobs=jobs, return_as="generator")(delayed(run)(*j) for j in rows):
            label, share, delta, online, s, k, wait, at = r
            line = f"{label} | {s:.4f} | {k:.4f} | {wait:.2f} | " + " | ".join(cell(v) for v in at)
            print(line, flush=True)
            out.write(line + "\n")
            out.flush()
