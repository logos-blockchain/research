"""GENESIS.md, section 8: the union over the divergence blocks of a history (statement 8.1).

Divergence slots are grouped in cells of g slots. A history whose divergence slots span L slots has
ceil(L / g) cells, and every g gives a bound; the least over every g from 1 to s is printed.
  - Forks with no honest block in their window: a cell costs P1(s - g + 1) (8.1 (1)).
  - Every fork: a cell costs U(s - g) + P1(G + 2 - s - g) for the cases of 6.3 other than t = now.
    The case t = now is counted in one of two ways (8.1 (2), 7.2):
      A: per cell, P1(K - s - g + 1), and U(K - 2) once for E_r;
      B: once for every divergence slot together, with E_r, U_(Delta + 1)(K - 1).
    The smaller total is printed for each K. "One divergence slot" is the span L = 1 (g = 1).
P1(x) is read for every x up to G + 1 from Window.p1_curve (the forward pass of 6.2), which the
script checks against the closed form Window.p1 at three windows.
The least windows are the least s at which a bound is at most 1e-9: for every fork, the cell part
alone (B without its once term), and the total at each K with s <= K - 1, or "none".
Usage: python g04_union.py > out_04_union.txt   (reads the curves cached by g03_settle.py)
"""
import math

import numpy as np

from common_g import (ALPHAS, DELTAS, EPS, GAP, H, K_CASES, S_GEN, YEAR, U_at, Window, p_of, pct,
                      settle_cached)

T_MAX = 160_000
SPANS = {"1 day": 24 * H, "30 days": 30 * 24 * H, "1 year": YEAR}


class Setting:
    def __init__(self, a, d):
        pa, ph = p_of(a), p_of(1 - a)
        self.w = Window(pa, ph, d)
        self.p1c = self.w.p1_curve(GAP + 1)
        self.u = settle_cached(a, d, T_MAX)
        self.u1 = settle_cached(a, d + 1, T_MAX)

    def U(self, w):
        return np.where(w >= 1, self.u[np.clip(w, 1, None) - 1], 1.0)

    def P1(self, x):
        return np.where(x >= 1, self.p1c[np.clip(x, 0, GAP + 1)], 1.0)

    def no_honest(self, s, span):
        g = np.arange(1, s + 1)
        v = np.ceil(span / g) * self.P1(s - g + 1)
        i = int(np.argmin(v))
        return float(min(1.0, v[i])), int(g[i])

    def every(self, s, span, K=None):
        """(cell part alone, its g) and, for a K, the total min(A, B)."""
        g = np.arange(1, s + 1)
        cells = np.ceil(span / g)
        base = self.U(s - g) + self.P1(GAP + 2 - s - g)
        vb = cells * base
        ib = int(np.argmin(vb))
        part = (float(min(1.0, vb[ib])), int(g[ib]))
        if K is None:
            return part, None
        va = cells * (base + self.P1(K - s - g + 1))
        tot_a = float(va.min()) + U_at(self.u, K - 2)
        tot_b = part[0] + U_at(self.u1, K - 1)
        return part, float(min(1.0, tot_a, tot_b))


def least(fn, lo, hi, step=10):
    """The least s in [lo, hi] with fn(s) <= EPS: a scan in steps, then slot by slot."""
    prev = lo
    for s in range(lo, hi + 1, step):
        if fn(s) <= EPS:
            for s2 in range(max(lo, prev), s + 1):
                if fn(s2) <= EPS:
                    return s2
        prev = s
    return None


if __name__ == "__main__":
    print(f"s = s_gen = {S_GEN}; spans of divergence slots: " +
          ", ".join(f"{k} = {v} slots" for k, v in SPANS.items()))
    for a in ALPHAS:
        for d in DELTAS:
            st = Setting(a, d)
            chk = max(abs(st.p1c[x] / st.w.p1(x) - 1) for x in (S_GEN, 20_000, 50_000))
            print(f"\n{pct(a)}, Delta = {d} (P1 by the forward pass against the closed form at 16200, 20000, 50000: "
                  f"largest relative difference {chk:.1e})")
            (u1, _), _ = st.every(S_GEN, 1)
            print(f"  one divergence slot: forks without honest blocks in the window P1(s) = {st.P1(S_GEN):.2e}; every fork, "
                  f"cases other than t = now, U(s - 1) + P1(G + 1 - s) = {u1:.3e}")
            for name, span in SPANS.items():
                v1, g1 = st.no_honest(S_GEN, span)
                (vu, gu), _ = st.every(S_GEN, span)
                tots = "; ".join(f"total at K = {K}: {st.every(S_GEN, span, K)[1]:.3e}" for K in K_CASES.values())
                print(f"  {name}: forks without honest blocks <= {v1:.2e} (g = {g1}); every fork, cells <= {vu:.3e} "
                      f"(g = {gu}); {tots}")
            for K in K_CASES.values():
                print(f"  K = {K}: once, U(K - 2) = {U_at(st.u, K - 2):.2e}, U_(Delta + 1)(K - 1) = {U_at(st.u1, K - 1):.2e}; "
                      f"one divergence slot, every fork, total {st.every(S_GEN, 1, K)[1]:.3e}")
            for name, span in (("one divergence slot", 1), ("1 day", 24 * H), ("1 year", YEAR)):
                ln = least(lambda s: st.no_honest(s, span)[0], 2_000, 120_000)
                lc = least(lambda s: st.every(s, span)[0][0], 2_000, T_MAX - 1)
                cells = [f"no honest block {ln} slots ({ln / H:.2f} h)",
                         f"every fork, cells alone {lc} slots ({lc / H:.2f} h)" if lc else "every fork, cells alone: none"]
                for K in K_CASES.values():
                    lk = least(lambda s: st.every(s, span, K)[1], 2_000, K - 1)
                    cells.append(f"every fork, total at K = {K}: " + (f"{lk} slots ({lk / H:.2f} h)" if lk else "none with s <= K - 1"))
                print(f"  least s for 1e-9, {name}: " + "; ".join(cells))
