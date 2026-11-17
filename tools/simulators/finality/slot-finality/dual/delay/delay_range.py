"""The wait a finality window must cover, for a worst-case delivery delay from 5 to 15 slots.

For each delay d and each share (a third, 30 %) the study's wait bound (finality_sim.waitbound,
on the slot lottery) gives the least wait whose chance of displacement is at most the target:
  plain      target 1e-9, epoch nonce unbiased
  nonce      target 1e-9 / 1.21 (the candidate nonce's factor for two nonces, derived at 10 s)
  offline    target 1e-9, a tenth of the honest stake offline, inference corrected
  offline+n  the same with the nonce's factor
  deflated   target 1e-9, after the share deflated the inference (rates times 1/(1 - share))
Usage: python delay_range.py <jobs>      writes out/delay_range.csv
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402,F401
from joblib import Parallel, delayed  # noqa: E402

F, EPS, NONCE = 1 / 30, 1e-9, 1.21
T_MAX = 400_000


def online(a, u):
    return a / (a + (1 - a) * u)


def need(share_name, case, d, alpha, scale, eps):
    from finality_sim.waitbound import wait_curve, wait_needed
    t0 = time.time()
    w = wait_needed(wait_curve(T_MAX, alpha, d, F, floor=eps / 10, scale=scale), eps)
    return dict(share=share_name, case=case, delay=d, alpha=alpha, scale=scale, eps=eps, wait_slots=w,
                wait_h=w / 3600 if w > 0 else float("nan"), secs=time.time() - t0)


JOBS = []
for d in range(5, 16):
    for name, a in (("third", 1 / 3), ("30 %", 0.30)):
        JOBS += [(name, "plain", d, a, 1.0, EPS), (name, "nonce", d, a, 1.0, EPS / NONCE),
                 (name, "offline", d, online(a, 0.9), 1.0, EPS), (name, "offline+n", d, online(a, 0.9), 1.0, EPS / NONCE),
                 (name, "deflated", d, a, 1 / (1 - a), EPS)]

if __name__ == "__main__":
    import pandas as pd
    os.makedirs("out", exist_ok=True)
    rows = []
    for r in Parallel(n_jobs=int(sys.argv[1]), return_as="generator_unordered")(delayed(need)(*j) for j in JOBS):
        rows.append(r)
        print(f"{r['share']:6s} {r['case']:10s} d={r['delay']:2d} -> {r['wait_h']:6.2f} h ({r['secs']:.0f} s)", flush=True)
        pd.DataFrame(rows).sort_values(["share", "case", "delay"]).to_csv("out/delay_range.csv", index=False)
