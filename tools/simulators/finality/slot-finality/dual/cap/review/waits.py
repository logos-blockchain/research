"""Reviewer's own wait-bound calls (items 3, 5). Usage: python waits.py <jobs>"""
import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import env
import numpy as np
from joblib import Parallel, delayed
F = 1/30
R = os.path.dirname(os.path.abspath(__file__))
def run(tag, alpha, d, s, tmax, save):
    from finality_sim.waitbound import wait_curve, wait_needed
    t0 = time.time()
    c = wait_curve(tmax, alpha, d, F, floor=1e-13, scale=s)
    at = lambda t: float(c[t-1]) if c.size >= t else 0.0
    if save: np.save(f"{R}/curve_{tag}.npy", c)
    return dict(tag=tag, alpha=alpha, d=d, scale=s, at18=at(64800), at36=at(129600) if tmax >= 129600 else None,
                need_h=wait_needed(c, 1e-9)/3600, size=int(c.size), secs=time.time()-t0)
T = 1/3
D1 = (1 - (1-F)**(2/3)) / F
jobs = [("15_1.03", T, 15, 1.03, 64800, 0), ("15_1.04", T, 15, 1.04, 64800, 0),
        ("14_1.17", T, 14, 1.17, 64800, 0), ("14_1.18", T, 14, 1.18, 64800, 0),
        ("13_1.32", T, 13, 1.32, 64800, 0), ("13_1.33", T, 13, 1.33, 64800, 0),
        ("12_1.49", T, 12, 1.49, 64800, 0), ("12_1.50", T, 12, 1.50, 64800, 0),
        ("12_first", T, 12, 1/D1, 64800, 0),
        ("30_15", 0.30, 15, 1/0.7, 64800, 1), ("third_10_1.5", T, 10, 1.5, 64800, 1),
        ("15_1.50_36h", T, 15, 1.50, 129600, 0), ("15_1.51_36h", T, 15, 1.51, 129600, 0),
        ("16_1.50_36h", T, 16, 1.50, 129600, 0)]
if __name__ == "__main__":
    with open(f"{R}/waits.txt", "w") as o:
        for r in Parallel(n_jobs=int(sys.argv[1]), return_as="generator_unordered")(delayed(run)(*j) for j in jobs):
            o.write(json.dumps(r) + "\n"); o.flush()
