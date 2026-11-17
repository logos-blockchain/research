"""Independent recheck of floor.py. Written from the description; no import of the study code."""
import math, sys
from math import exp, lgamma, log
import numpy as np
from scipy.stats import nbinom, binom
from scipy.special import betainc

f = 1 / 30
H = 3600.0
def p_of(share): return 1 - (1 - f) ** share

# --- 1. spec code, verbatim structure -------------------------------------------------
def blocks_short(n, K, alpha, D, rnd=math.floor):
    p_h = 1 - (1 - f) ** (1 - alpha)
    slots = rnd(K - n * D)
    if slots < n: return 1.0
    # sum of pmf i<n, via log terms (spec) but vectorised
    i = np.arange(n)
    from scipy.special import gammaln
    return float(np.exp(gammaln(slots + 1) - gammaln(i + 1) - gammaln(slots - i + 1) + i * log(p_h) + (slots - i) * log(1 - p_h)).sum())
def floor(K, alpha, D, eps, rnd=math.floor):
    lo, hi = 0, K            # blocks_short monotone in n: bisection
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if blocks_short(mid, K, alpha, D, rnd) <= eps: lo = mid
        else: hi = mid - 1
    return lo
# Blend fit
def blend():
    p = p_of(1.0); return (64800 / 1825 - 1 / p)   # p/(1+pD) K = 1825  ->  D = K/1825 - 1/p
B = blend()
print("Blend D", B)
print("== 1. floors")
for K in (64800, 36000):
    for D, dn in ((B, "Blend"), (10, "10"), (15, "15")):
        for eps in (1e-9, 1e-3):
            row = [floor(K, a, D, eps) for a in (0, .05, .1, .15, .2, .25, .3, 1 / 3)]
            extra = ""
            if dn == "Blend":
                row2 = [floor(K, a, D, eps, math.ceil) for a in (0, .05, .1, .15, .2, .25, .3, 1 / 3)]
                extra = f"  ceil-rounding diff {[x - y for x, y in zip(row2, row)]}"
            print(K, dn, eps, row, extra)
# continuous-slot version of Blend (regularised beta, real 'slots') for one point
def short_cont(n, K, alpha, D):
    p = p_of(1 - alpha); s = K - n * D
    return 1 - betainc(n, s - n + 1, p)       # P(Bin(s,p) < n) continued in s
for a, e in ((0, 1e-9), (1/3, 1e-9), (.1, 1e-9)):
    n = 0; lo, hi = 0, 5000
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if short_cont(mid, 64800, a, B) <= e: lo = mid
        else: hi = mid - 1
    print("  continuous-slot Blend floor", a, e, lo)

# --- time to n blocks: T = n*D + NB (trials to n successes) ---------------------------
def cdfT(n, t, p, D):
    """P(T_n <= t) via negative binomial (failures before n-th success)."""
    s = math.floor(t - n * D)
    if s < n: return 0.0
    return float(nbinom.cdf(s - n, n, p))
def sfT(n, t, p, D):
    s = math.floor(t - n * D)
    if s < n: return 1.0
    return float(nbinom.sf(s - n, n, p))
def qT(n, q, p, D):
    lo, hi = 0, int(60 * n / p)
    while lo < hi:
        mid = (lo + hi) // 2
        ok = (cdfT(n, mid, p, D) >= q) if q < 0.9 else (sfT(n, mid, p, D) <= 1 - q)
        if ok: hi = mid
        else: lo = mid + 1
    return lo
def bis(fn, lo, hi):
    for _ in range(60):
        m = (lo + hi) / 2
        if fn(m): lo = m
        else: hi = m
    return lo
print("\n== 2. cost, K=64800")
K = 64800
for n in (1440, 1500):
    for dn, D in (("Blend", B), ("10s", 10)):
        out = []
        for e in (1e-9, 1e-3, .5):
            if sfT(n, K, p_of(1.0), D) > e: out.append("none")
            else: out.append(f"{100 * bis(lambda a: sfT(n, K, p_of(1 - a), D) <= e, 0, 1):.1f}%")
        p = p_of(2 / 3)
        print(n, dn, "missing stake", out, "third: median/latest h",
              round(max(K, qT(n, .5, p, D)) / H, 2), round(max(K, qT(n, 1 - 1e-9, p, D)) / H, 2))
    for dn, D in (("none", 0), ("Blend", B)):
        u = bis(lambda x: sfT(n, 54 * H, p_of(x), D) > 1e-9, 0, 3)
        print(n, "54h phase", dn, f"{100 * u:.1f}%")
    print(n, "halved stake mean days", n * (1 / p_of(.5) + B) / 86400)

print("\n== 3. benefit")
for n in (1019, 1440, 1500):
    s9 = bis(lambda s: cdfT(n + 1, K, p_of(s), 0) <= 1e-9, 0, 1)
    s5 = bis(lambda s: cdfT(n + 1, K, p_of(s), 0) <= .5, 0, 1)
    p = p_of(1 / 3)
    print(n, "s9 %.3f s5 %.3f" % (s9, s5), "third alone days mean/early %.2f / %.2f" % ((n + 1) / p / 86400, qT(n + 1, 1e-9, p, 0) / 86400),
          "halves Blend h", [round(max(K, qT(n, q, p_of(.5), B)) / H, 1) for q in (1e-9, .5, 1 - 1e-9)],
          "with n+1:", [round(max(K, qT(n + 1, q, p_of(.5), B)) / H, 1) for q in (1e-9, .5, 1 - 1e-9)])

# --- 4. eclipse ------------------------------------------------------------------------
print("\n== 4. eclipse, clean minimisation at mean rates (grid over start, 1 s)")
def eclipse_mean(n, a, D, K, fork_time=None, strict=False):
    pa, ph = p_of(a), p_of(1 - a)
    g = 1 / ph + D
    best = (1e18, None)
    for te in range(0, 4 * K, 10):
        hb = te / g                                   # node's blocks above the divergence
        nfin = n + 1 if strict else n                 # blocks needed for the child's immutability
        if te >= K and hb >= nfin: break
        need = max(n + 1, math.floor(hb) + 1)
        tf = need / pa if fork_time is None else fork_time(need)
        d = max(tf, K) - te
        if d < best[0]: best = (d, te)
    return best
memo = {}
def lucky(a):
    pa = p_of(a)
    def ft(need):
        if need not in memo: memo[need] = qT(need, 1e-3, pa, 0)
        return memo[need]
    return ft
for K in (64800, 36000):
  for n in ((1019, 1440, 1500) if K == 64800 else (560, 800)):
    for a in (1 / 3, .3):
        memo.clear()
        r = []
        for dn, D in (("0", 0), ("Blend", B), ("10", 10)):
            d, te = eclipse_mean(n, a, D, K)
            dl, tel = eclipse_mean(n, a, D, K, lucky(a))
            r.append(f"{dn}: {d / H:.1f} h (start {te / H:.1f} h) lucky {dl / H:.1f} h (start {tel/H:.1f})")
        print(K, n, round(a, 3), " | ".join(r))

# Monte Carlo: both chains random, attacker picks the best start with hindsight of both chains
print("\n== 4b. Monte Carlo, both chains random; minimal eclipse over start (K=64800, a=1/3)")
rng = np.random.default_rng(1)
def mc(n, a, D, K, N=20000, M=2600):
    pa, ph = p_of(a), p_of(1 - a)
    # honest block arrival times T_h(j) j=1..M ; fork T_f(j)
    Th = np.cumsum(rng.geometric(ph, size=(N, M)) + D, axis=1)
    Tf = np.cumsum(rng.geometric(pa, size=(N, M)), axis=1)
    # start just before the node holds j blocks (j = 1..): node then has j-1 blocks; valid while not final:
    # final when te >= K and blocks >= n  -> starting just before T_h(j) is valid iff j <= n or T_h(j) <= K
    j = np.arange(1, M + 1)
    need = np.maximum(n + 1, j)                       # more than j-1 blocks, and n+1
    tf = np.take_along_axis(Tf, np.broadcast_to(need - 1, (N, M)), axis=1)
    d = np.maximum(tf, K) - Th
    valid = (j[None, :] <= n) | (Th <= K)
    d = np.where(valid, d, np.inf)
    # also the start "just before K" if the node has < ... (covered when Th>K & j<=n) ; and start at K- with j blocks
    return d.min(axis=1)
for n in (1019, 1440, 1500):
    for dn, D in (("0", 0), ("Blend", B), ("10", 10)):
        d = mc(n, 1 / 3, D, 64800) / H
        print(n, dn, "mean %.1f median %.1f  q1e-3 %.1f  q1e-2 %.1f min %.1f" % (d.mean(), np.median(d), np.quantile(d, 1e-3), np.quantile(d, 1e-2), d.min()))

# MC check of a floor at eps 1e-3 (independent of the binomial identity)
print("\n== MC of the gap model: P(fewer than n blocks in K) , 10 s, a third")
N = 200000
for n, D, a in ((1098, 10, 1/3), (1099, 10, 1/3), (1528, 10, 0), (1529, 10, 0)):
    p = p_of(1 - a)
    T = n * D + n + rng.negative_binomial(n, p, size=N * 5)
    print(n, D, round(a, 3), "MC", (T > 64800).mean(), "exact", sfT(n, 64800, p, D))
