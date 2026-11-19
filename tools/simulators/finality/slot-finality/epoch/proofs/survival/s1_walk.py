"""The walk behind the survival law, per state (SURVIVAL.md, sections 6 and 9.1).

For each state: the chances h and a, the ratio r of Lemma 6.2, the rate of greedy d-isolated honest
wins, the drift, theta* (Lemma 6.4), the constants of Lemma 6.7, and the law of M, the all-time
maximum of the walk with steps Y - 1, from below and from above (Lemma 6.4). The last block compares
the study's helpers with these laws: `walk` (its `step` is the law of Y) and `_renewal(_ladder(step,
200))` (its law of M).
Usage: python s1_walk.py > out_1_walk.txt
"""
import math
import sys

import numpy as np

from sv_common import H, STATES, STUDY_SRC, chernoff, geo_ratio, max_law, rates, study_params, theta_star, y_law

sys.path.insert(0, STUDY_SRC)
from finality_sim.grinding import _ladder, _renewal, walk   # noqa: E402

MS = (1, 2, 5, 10, 20, 50, 100)

if __name__ == "__main__":
    print("1. per state: h, a, r (Lemma 6.2), rate of isolated honest wins 1/(d + 1/h), E[Y] - 1, theta* (Lemma 6.4), Lemma 6.7")
    laws = {}
    for key, label, xh, xa, d, _, _ in STATES:
        h, a = rates(xh, xa)
        r = geo_ratio(h, a)
        rate = 1 / (d + 1 / h)
        ey = (d + 1) * a + r / (1 - r)
        th = theta_star(h, a, d)
        c_th, c_rho, c_lam, c_C = chernoff(h, a, d)
        print(f"   {label}: x_h = {xh:.6f}, x_a = {xa:.6f}, d = {d} | h = {h:.6f}, a = {a:.6f}, r = {r:.6f} | "
              f"rate = {rate:.6f} per slot, a - rate = {a - rate:+.6f} | E[Y] - 1 = {ey - 1:+.6f} | theta* = {th:.6f} | "
              f"Lemma 6.7: theta = {c_th:.6f}, rho = {c_rho:.8f}, lambda = {c_lam:.8f} (a factor {c_lam ** H:.3e} an hour), C = {c_C:.4f}")
        laws[key] = (h, a, d, max_law(h, a, d))

    print("\n2. P(M >= m), from below | from above (Lemma 6.4: the Lindley recursion from 0 and from exp(-theta m))")
    for key, label, xh, xa, d, _, _ in STATES:
        h, a, d, (low, up, it) = laws[key]
        gap = max(abs(up[m] - low[m]) / up[m] for m in range(1, 301))
        cells = " | ".join(f"m = {m}: {low[m]:.6e}, {up[m]:.6e}" for m in MS)
        print(f"   {label}: {it} iterations; largest relative gap for m = 1..300: {gap:.1e}")
        print(f"      {cells}")

    print("\n3. the study's helpers against these laws (module grinding: walk, _ladder, _renewal; floor 200)")
    for key, label, xh, xa, d, _, _ in STATES:
        h, a, d, (low, up, it) = laws[key]
        fp, al = study_params(xh, xa)
        _, step = walk(fp, al, delta=d)
        y, _ = y_law(h, a, d)
        n = min(step.size, y.size)
        dy = float(np.max(np.abs(step[:n] - y[:n])))
        pm = _renewal(_ladder(step, 200))
        st_tail = np.cumsum(pm[::-1])[::-1]
        rel = [abs(st_tail[m] - up[m]) / up[m] for m in MS if m < st_tail.size]
        cells = " | ".join(f"m = {m}: {st_tail[m]:.6e}" for m in MS if m < st_tail.size)
        print(f"   {label}: study f' = {fp:.6f}, alpha = {al:.6f} | largest |step - law of Y| = {dy:.1e} | "
              f"study P(M >= m): {cells} | largest relative difference from above {max(rel):.1e}")
