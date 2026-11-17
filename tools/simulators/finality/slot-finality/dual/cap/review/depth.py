"""Reviewer's own depth-bound calls (item 4), slot reading. Usage: python depth.py"""
import os, sys, json, math, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import env
import numpy as np
from joblib import Parallel, delayed
F = 1/30
R = os.path.dirname(os.path.abspath(__file__))
def run(tag, alpha, delta, scale, kmax):
    from finality_sim.lcbounds import slot_pdf, ub_curve
    t0 = time.time()
    d = -math.log(1 - F) * scale * (delta + 1)
    g = math.exp(-(1 - alpha) * d)
    a = max(10, math.ceil(math.log(1e-10) / math.log(1 - g)) + 1)
    c = ub_curve(kmax, slot_pdf(1 - alpha, d, a), a, max(30, a + 1), 1e-16, 1e-14)
    np.save(f"{R}/depth_{tag}.npy", c)
    at = lambda n: float(c[n-1]) if n <= c.size else 0.0
    hit = np.nonzero(c <= 1e-9)[0]
    need = int(hit[0]) + 1 if hit.size else -1
    return dict(tag=tag, d=d, alphabet=a, at_k_code=at(2160), at_k_text=at(4320), need_code=need,
                need_text=math.ceil(need/2), size=int(c.size), secs=time.time()-t0)
jobs = [("third_12", 1/3, 12, 1.5, 4400), ("third_15", 1/3, 15, 1.5, 8000), ("30_15", 0.3, 15, 1/0.7, 4400),
        ("third_10", 1/3, 10, 1.5, 4400)]
if __name__ == "__main__":
    with open(f"{R}/depth.txt", "w") as o:
        for r in Parallel(n_jobs=2, return_as="generator_unordered")(delayed(run)(*j) for j in jobs):
            o.write(json.dumps(r) + "\n"); o.flush()
