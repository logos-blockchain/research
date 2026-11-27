"""Argument 3. (i) 5.4 as printed at G = 72,000; (ii) a bound against an ACTIVE coalition.

Active bound, for an online honest node at its first use (GENESIS model A1-A3 and S):
  c = c_loc just before; all its slots < use; len(c) >= d(use - D - 1) (it holds those honest blocks)
  len(c[0:cut-1]) <= d(t_g) + A((t_g, cut-1])                       (GENESIS 5.3)
  #gap blocks on c >= N((cut-1+D, use-D-1]) - M_pre(cut-1)          (N over G - 2D slots)
  F1 = {N_{G-2D} - M_pre <= PHI}                 -> floor part
  age part: sl_T - sl_Y < K forces y + z >= G - K where y = sl_Y - cut, z = use - 1 - sl_T
     E_y: no block of c in the first y0 slots of the gap:   M_pre + M_post + 1 >= N_{y0 - D}
     E_z: no block of c in the last  z0 slots of the gap:   M_pre >= N_{z0 - 2D}
  for any y0 + z0 = G - K + 1 (so that y >= y0 or z >= z0).
"""
import math

import numpy as np
from scipy import stats

import walk as w

K, PHI = w.K, w.PHI


def S(n, L, p, d):
    tr = L - n * d
    if tr < n:
        return 0.0
    return stats.binom.logcdf(n - 1, tr, p) / math.log(10)


def R(m, p):
    if m <= 0:
        return 0.0
    return (m * math.log1p(-p) + math.log1p(m * p / (1 - p))) / math.log(10)


def printed(G, h, d):
    a, b = S(PHI + 1, G, h, d), R(G - K - 2 * d + 1, h)
    return a, b


def pmf_N(m, h, D, nmax):
    n = np.arange(nmax + 1)
    lc = w.N_logcdf(n, m, h, D)
    prev = np.concatenate([[-np.inf], lc[:-1]])
    with np.errstate(divide="ignore", invalid="ignore"):
        lp = lc + np.log1p(-np.exp(np.minimum(prev - lc, 0)))
    lp = np.where(np.isfinite(lc), lp, -np.inf)
    return np.exp(lc), np.exp(lp)


def floor_part(G, h, a, D, pre, phi=PHI, end=True):
    m = G - 2 * D if end else G - D
    T = w.sf(pre)
    cdf, pmf = pmf_N(m, h, D, phi + T.size - 2)
    tot = cdf[phi]
    j = np.arange(1, T.size - 1)
    tot += float(np.sum(T[j] * pmf[phi + j]))
    return tot


def ge_N(dist, m, h, D):
    """P(X >= N(m)), X of law dist."""
    T = w.sf(dist)
    cdf, pmf = pmf_N(m, h, D, T.size - 2)
    n = np.arange(T.size - 1)
    return float(np.sum(T[n] * pmf[n]))


def age_part(G, h, a, D, pre, post):
    sp = np.convolve(pre, post)[:1200]
    sp = np.concatenate([[0.0], sp])[:1200]          # + 1
    best = (math.inf, None)
    tot = G - K + 1
    for frac in (0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7):
        y0 = int(tot * frac)
        z0 = tot - y0
        if y0 - D <= 0 or z0 - 2 * D <= 0:
            continue
        v = ge_N(sp, y0 - D, h, D) + ge_N(pre, z0 - 2 * D, h, D)
        if v < best[0]:
            best = (v, (y0, z0))
    return best


if __name__ == "__main__":
    print("5.4 as printed at G = 72,000 (log10 of the two terms), and with G - d (5.10):")
    for name, xh, xa, D in w.STATES:
        h = w.p_of(xh)
        a1, b1 = printed(72_000, h, D)
        a2, b2 = printed(72_000 - D, h, D)
        print(f"  {name:28s} S {a1:8.2f}  R {b1:9.1f} | G-d: S {a2:8.2f} R {b2:9.1f}")
    for D in (15,):
        h = w.p_of(0.63 / 0.93)
        a1, b1 = printed(72_000, h, D)
        print(f"  (not required) tenth offline corrected AND 15 late: S {a1:8.2f}")
        h = w.p_of(0.63)
        a1, b1 = printed(72_000, h, D)
        print(f"  (not required) tenth offline before AND 15 late: S {a1:8.2f}")
    print()
    print("Active coalition: floor part, age part at G = 72,000, and at G* as printed")
    for name, xh, xa, D in w.STATES:
        h, a = w.p_of(xh), w.p_of(xa)
        pre, post, inf, th = w.tails(h, a, D)
        fp = floor_part(72_000, h, a, D, pre)
        ag = age_part(72_000, h, a, D, pre, post)
        # least G with the printed bound and with the active bound <= 1e-9

        def printed_sum(G):
            x, y = printed(G, h, D)
            return 10 ** x + 10 ** y

        def active_sum(G):
            return floor_part(G, h, a, D, pre) + age_part(G, h, a, D, pre, post)[0]

        def least(fn, lo=K + 100, hi=80_000):
            while lo < hi:
                mid = (lo + hi) // 2
                if fn(mid) <= 1e-9:
                    hi = mid
                else:
                    lo = mid + 1
            return lo

        gs, ga = least(printed_sum), least(active_sum)
        print(f"  {name:28s} floor {fp:.2e}  age {ag[0]:.2e} {ag[1]}  | E[M_pre]={np.sum(np.arange(pre.size)*pre):.2f}"
              f" P(M_pre>=1)={1-pre[0]:.3f}  G* printed {gs}, active bound at that G {active_sum(gs):.2e};"
              f" least G active {ga} (+{ga-gs})")
