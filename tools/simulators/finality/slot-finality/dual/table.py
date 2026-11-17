"""The safety table in ONE reading for both legs: the slot lottery (rate -ln(1-f) per slot, delay
delta + 1), which is the reading the wait bound uses. Read from out/bounds_cases.csv and
out/bounds_grid.csv. 'single' = the count of the authors' code and of the paper's Table 1;
'double' = the two-chain count (the code's curve at twice the depth), which is not verified.
With an argument 'extra' it also runs the depth bound at 16 to 19 s against a third (slot reading).
"""
import math
import sys

import env  # noqa: F401
import numpy as np
import pandas as pd

c = pd.read_csv(f"{env.W}/out/bounds_cases.csv").set_index("label")
ROWS = ["third, 10 s", "third, 12 s", "third, 13 s", "third, 14 s", "third, 15 s", "third, 20 s",
        "third, 10 s, deflated inference", "third, 10 s, 90% of honest online, corrected",
        "third, 10 s, 90% of honest online, not corrected",
        "third, 10 s, 80% of honest online, corrected", "third, 10 s, lottery 1.25 times fast",
        "third, 10 s, lottery 1.925 times fast", "30 %, 15 s", "30 %, 20 s", "30 %, 15 s, deflated inference"]


def fmt(x):
    return "<1e-14" if x == 0 else f"{x:.1e}"


print(f"{'case':50s} {'need single':>11s} {'need double':>11s} {'at 2160 single':>14s} {'double':>8s} | {'wait need h':>11s} {'at 18 h':>8s} {'at 10 h':>8s}")
for r in ROWS:
    x = c.loc[r]
    print(f"{r:50s} {int(x.depth_slot_need_code):11d} {int(x.depth_slot_need_paper):11d} "
          f"{fmt(x.depth_slot_at_k_code):>14s} {fmt(x.depth_slot_at_k_paper):>8s} | {x.wait_need_h:11.2f} "
          f"{fmt(x.wait_at_K18):>8s} {fmt(x.wait_at_K10):>8s}")

g = pd.read_csv(f"{env.W}/out/bounds_grid.csv")
for dl in (10, 15, 20):
    s = g[g.delta == dl].sort_values("alpha")
    out = []
    for col in ("depth_slot_at_k_code", "depth_slot_at_k_paper", "depth_cont_at_k_code", "depth_cont_at_k_paper", "wait_at_K18", "wait_at_K10"):
        v = np.log(np.maximum(s[col].values, 1e-14))
        a = s.alpha.values
        held = float("nan")
        for i in range(1, len(a)):
            if v[i - 1] <= math.log(1e-9) < v[i]:
                held = a[i - 1] + (a[i] - a[i - 1]) * (math.log(1e-9) - v[i - 1]) / (v[i] - v[i - 1])
        if v[-1] <= math.log(1e-9):
            held = a[-1]
        if v[0] > math.log(1e-9):
            held = -a[0]
        out.append(f"{col}={held:.3f}")
    print(f"largest share held at {dl} s ({len(s)} grid points; negative = below the grid): " + "  ".join(out))

if len(sys.argv) > 1 and sys.argv[1] == "extra":
    from joblib import Parallel, delayed
    from bounds import depth_curve, at, first, F, k

    def one(dl):
        cc = depth_curve(1 / 3, -math.log(1 - F) * (dl + 1))
        return dl, first(cc, 1e-9), at(cc, k), at(cc, 2 * k)
    for dl, need, a1, a2 in Parallel(n_jobs=4)(delayed(one)(d) for d in (16, 17, 18, 19)):
        print(f"third, {dl} s, slot reading: need single {need}, double {math.ceil(need / 2)}; at 2,160 single {fmt(a1)}, double {fmt(a2)}")
