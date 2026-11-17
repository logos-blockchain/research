"""The study's two bounds, side by side, for the dual-finality study.

For a point (alpha, delta, scale):
  alpha  the adversary's share of the stake that makes blocks (its relative share),
  delta  the worst-case delivery delay in slots (1 slot = 1 s),
  scale  the lottery's rate as a multiple of f = 1/30 (1.5 after a third deflated the inference).

DEPTH: finality_sim.lcbounds.ub_curve, the depth bound of Gazi, Ren and Russell as the study
ports it (B2). It bounds the chance that a block with n blocks of the chain after it is displaced.
Two readings: "cont" is B2's (D = f*delta, continuous time); "slot" is the reading the wait bound
uses on the slot lottery (rate -ln(1-f) per slot, delay delta+1). Two counts: the code's count
(entry n) and the paper's count, which the study found to be the code's curve at 2n (SLOTS.md K.7).

WAIT: finality_sim.waitbound.wait_curve, the wait bound (K.7) on the slot lottery. It bounds the
chance that a block is displaced after a wait of T slots.

Usage: python bounds.py <jobs> <which>    which = cases | grid
Writes out/bounds_<which>.csv.
"""
import math
import sys
import time

import env  # noqa: F401  (first)
import numpy as np
from joblib import Parallel, delayed

F = 1 / 30
k = 2160
K18, K10 = 64800, 36000
EPS = 1e-9
MIN_PROB = 1e-16
FLOOR = 1e-14


def alphabet_for(alpha, d, tail=1e-10):
    g = math.exp(-(1 - alpha) * d)
    return max(10, math.ceil(math.log(tail) / math.log(1 - g)) + 1)


def depth_curve(alpha, d, k_max=40000):
    from finality_sim.lcbounds import slot_pdf, ub_curve
    a = alphabet_for(alpha, d)
    return ub_curve(k_max, slot_pdf(1 - alpha, d, a), a, max(30, a + 1), MIN_PROB, FLOOR)


def at(curve, n):
    """The bound at n (entry n-1); below FLOOR past the curve's end."""
    return float(curve[n - 1]) if n <= curve.size else 0.0


def first(curve, eps):
    hit = np.nonzero(curve <= eps)[0]
    return int(hit[0]) + 1 if hit.size else -1


def point(label, alpha, delta, scale):
    from finality_sim.waitbound import wait_curve
    t0 = time.time()
    row = dict(label=label, alpha=alpha, delta=delta, scale=scale)
    for name, d in (("cont", F * scale * delta), ("slot", -math.log(1 - F) * scale * (delta + 1))):
        c = depth_curve(alpha, d)
        row[f"depth_{name}_need_code"] = first(c, EPS)            # blocks, code's count
        row[f"depth_{name}_need_paper"] = math.ceil(first(c, EPS) / 2) if first(c, EPS) > 0 else -1
        row[f"depth_{name}_at_k_code"] = at(c, k)
        row[f"depth_{name}_at_k_paper"] = at(c, 2 * k)
    w = wait_curve(3 * K18, alpha, delta, F, floor=FLOOR, scale=scale)
    row["wait_need"] = first(w, EPS)
    row["wait_need_h"] = row["wait_need"] / 3600 if row["wait_need"] > 0 else math.nan
    row["wait_at_K18"] = at(w, K18)
    row["wait_at_K10"] = at(w, K10)
    row["secs"] = time.time() - t0
    return row


def online(a, u):
    """The adversary's relative share when a part u of the honest stake is online."""
    return a / (a + (1 - a) * u)


TH = 1 / 3
CASES = []
for a, an in ((TH, "third"), (0.30, "30 %")):
    for dl in (5, 10, 12, 13, 14, 15, 20):
        CASES.append((f"{an}, {dl} s", a, dl, 1.0))
    for dl in (10, 15):
        CASES.append((f"{an}, {dl} s, deflated inference", a, dl, 1 / (1 - a)))
    for u in (0.9, 0.8, 0.7):
        # lottery corrected to the online stake: rate f again, relative share higher
        CASES.append((f"{an}, 10 s, {u:.0%} of honest online, corrected", online(a, u), 10, 1.0))
        # not yet corrected: the lottery runs slow by the stake that left
        CASES.append((f"{an}, 10 s, {u:.0%} of honest online, not corrected",
                      online(a, u), 10, a + (1 - a) * u))
CASES.append(("third, 10 s, lottery 1.925 times fast", TH, 10, 1.925))
CASES.append(("third, 10 s, lottery 2 times fast", TH, 10, 2.0))
CASES.append(("third, 10 s, lottery 1.25 times fast", TH, 10, 1.25))

GRID = [(f"grid a={a:.3f} d={dl}", a, dl, 1.0)
        for dl in (10, 15, 20) for a in np.arange(0.25, 0.4001, 0.005)]

if __name__ == "__main__":
    jobs, which = int(sys.argv[1]), sys.argv[2]
    todo = CASES if which == "cases" else GRID
    import pandas as pd
    rows = []
    t0 = time.time()
    for r in Parallel(n_jobs=jobs, return_as="generator_unordered")(delayed(point)(*c) for c in todo):
        rows.append(r)
        print(f"{r['label']:55s} depth need code {r['depth_cont_need_code']:6d} "
              f"(slot {r['depth_slot_need_code']:6d})  at k: {r['depth_cont_at_k_code']:.2e} / paper "
              f"{r['depth_cont_at_k_paper']:.2e}   wait need {r['wait_need_h']:6.2f} h  at 18h "
              f"{r['wait_at_K18']:.2e} at 10h {r['wait_at_K10']:.2e}  ({r['secs']:.0f} s)", flush=True)
        pd.DataFrame(rows).to_csv(f"{env.W}/out/bounds_{which}.csv", index=False)
    print(f"done in {time.time() - t0:.0f} s")
