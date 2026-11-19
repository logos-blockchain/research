"""GENESIS.md, sections 3, 5 and 6: one divergence block, forks with no honest block in the window.

For each share and delay:
  - the tails of M_pre and M_post (statement 6.2 (c)), beside Lundberg's bound;
  - P(Z_s >= 0): one window without the maxima, which is RFC-532's single-window figure, and the
    strict variant, which is finality_sim.recovery's;
  - P1(s) = P(M_pre + Z_s + M+_post >= 0), the bound of statement 6.2, and the same sum with M_post in
    place of M+_post, which the step of 6.2 (a) before its correction gave;
  - P1 at other windows, and the least window with P1 <= 1e-9;
  - P1(K - s) for both K and P1(G + 1 - s), the terms of statement 6.3;
  - P1(s) with the honest chance lowered by the circuit's relative shortfall delta (assumption A1).
Usage: python g02_window.py > out_02_window.txt
"""
import math

import numpy as np

from common_g import (ALPHAS, DELTAS, EPS, GAP, H, K_CASES, S_GEN, Window, hit_zero_upper, p_of, pct,
                      shortfall, strict_single)


def least_window(w: Window, eps: float, lo: int = 2000, hi: int = 400_000) -> int:
    assert w.p1(hi) <= eps
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if w.p1(mid) <= eps:
            hi = mid
        else:
            lo = mid
    return hi


if __name__ == "__main__":
    grid = (8_000, 10_000, 12_000, 14_000, S_GEN, 18_000, 21_600, 2 * S_GEN)
    print(f"s = s_gen = {S_GEN} slots")
    for a in ALPHAS:
        for d in DELTAS:
            pa, ph = p_of(a), p_of(1 - a)
            w = Window(pa, ph, d)
            phi, th = hit_zero_upper(pa, ph, d)
            qs = 1 - pa + pa * math.exp(th)
            bound = np.array([[min(1.0, math.exp(-th * (dd - 1)) * qs ** c) for c in range(d + 1)]
                              for dd in range(1, phi.shape[0] + 1)])
            print(f"\n{pct(a)}, Delta = {d}: theta* = {th:.4f}; strip solution / Lundberg bound, "
                  f"largest ratio = {np.max(phi / bound):.4f}")
            print("  P(M_pre >= m), m = 1..6: " + ", ".join(f"{v:.4g}" for v in w.t_pre[1:7]))
            print("  P(M_post >= m), m = 1..6: " + ", ".join(f"{v:.4g}" for v in w.t_post[1:7]))
            print(f"  mass left at m > 120 (counted as failure): {w.inf_mass:.2e}")
            z0 = w.p1(S_GEN, with_max=False)
            st = strict_single(S_GEN, pa, ph, d)
            p1 = w.p1(S_GEN)
            old = w.p1(S_GEN, corrected=False)
            print(f"  one window, P(Z_s >= 0) = {z0:.3e}; strictly denser (recovery's figure) = {st:.3e}")
            print(f"  P1(s) = {p1:.4e}; P1(s) / P(Z_s >= 0) = {p1 / z0:.2f}; with M_post in place of M+_post "
                  f"{old:.4e} (P1 is {100 * (p1 / old - 1):.2f} % higher)")
            print("  P1(x): " + "; ".join(f"x = {x} ({x / H:g} h): {w.p1(x):.2e}" for x in grid))
            lw = least_window(w, EPS)
            print(f"  least window with P1 <= 1e-9: {lw} slots = {lw / H:.2f} h")
            print("  terms of 6.3: " + "; ".join(f"K = {K}: P1(K - s) = P1({K - S_GEN}) = {w.p1(K - S_GEN):.2e}"
                                                for K in K_CASES.values())
                  + f"; P1(G + 1 - s) = P1({GAP + 1 - S_GEN}) <= {w.p1(GAP + 1 - S_GEN):.1e}")
            dl = shortfall(1 - a)
            low = Window(pa, ph * (1 - dl), d).p1(S_GEN)
            print(f"  the circuit's shortfall for one note holding all honest stake: delta = {dl:.2e}; P1(s) at "
                  f"p_h (1 - delta) = {low:.4e} ({100 * (low / p1 - 1):+.2f} %)")
