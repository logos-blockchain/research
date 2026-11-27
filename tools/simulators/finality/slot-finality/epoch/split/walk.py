"""Independent laws for the review. Written from the statements, not from common_g.py or sv_common.py.

h, a   : chance per slot that honest (building) stake / the coalition wins.
D      : delay in slots.
M      : sup over k >= 0 of the walk with steps Y - 1, Y = Bin(D+1, a) + Geo(r), r = a(1-h)/(a(1-h)+h)
lead   : M_pre = max over u <= sigma of A((u, sigma]) - N((u + D, sigma]) = Bin(D, a) + Geo(r) + M
post   : M_post = Bin(2D+1, a) + Geo(r) + M   (GENESIS 6.2, without the '+' correction)
"""
import math

import numpy as np
from scipy import optimize, stats

F = 1 / 30
K = 36_000
PHI = 689
S_GEN = 16_200
EPS = 1e-9


def p_of(x):
    return -math.expm1(x * math.log1p(-F))


# name, honest share of D, coalition share of D, delay
STATES = [
    ("no disturbance", 0.7, 0.3, 10),
    ("every block 15 late", 0.7, 0.3, 15),
    ("tenth offline, corrected", 0.63 / 0.93, 0.3 / 0.93, 10),
    ("tenth offline, before", 0.63, 0.3, 10),
    ("D = honest online", 1.0, 0.3 / 0.7, 10),
]


def step_law(h, a, D, size):
    """pmf of Y = Bin(D+1, a) + Geo(r) on 0..size-1 (tail lumped is below double precision)."""
    r = a * (1 - h) / (a * (1 - h) + h)
    g = (1 - r) * r ** np.arange(size)
    b = stats.binom.pmf(np.arange(D + 2), D + 1, a)
    y = np.convolve(b, g)[:size]
    return y, g, r


def theta_star(h, a, D):
    r = a * (1 - h) / (a * (1 - h) + h)

    def lmgf(t):
        if r * math.exp(t) >= 1:
            return math.inf
        return -t + (D + 1) * math.log1p(a * math.expm1(t)) + math.log(1 - r) - math.log(1 - r * math.exp(t))

    hi = 1e-4
    while lmgf(hi) < 0:
        hi *= 1.5
    return optimize.brentq(lmgf, hi / 1.5, hi, xtol=1e-14)


def law_of_M(h, a, D, size=1200, tol=1e-13):
    """Upper law of M on 0..size-1 plus mass at infinity, by iterating W -> (W + Y - 1)^+ from the
    start P(W >= m) = exp(-theta m), which dominates M (Ville). Returns pmf, inf mass, theta."""
    th = theta_star(h, a, D)
    y, g, r = step_law(h, a, D, 400)
    tail = np.exp(-th * np.arange(size + 1))
    w = tail[:-1] - tail[1:]
    inf = tail[-1]
    prev = None
    for it in range(20000):
        c = np.convolve(w, y)
        new = np.zeros(size)
        new[0] = c[0] + c[1]
        n = min(size, c.size - 1) - 1
        new[1:1 + n] = c[2:2 + n]
        inf_new = inf + c[size + 1:].sum()
        w, inf = new, min(inf_new, tail[-1])
        if it % 50 == 49:
            t = np.cumsum(w[::-1])[::-1]
            if prev is not None:
                k = min(size, 900)
                if np.max(np.abs(t[:k] / prev[:k] - 1)) < tol:
                    break
            prev = t
    return w, inf, th


def tails(h, a, D, size=1200):
    """(pmf of M_pre, pmf of M_post, inf) on 0..size-1; both are upper laws."""
    m, inf, th = law_of_M(h, a, D, size)
    y, g, r = step_law(h, a, D, 400)
    w = np.convolve(m, g)[:size]
    pre = np.convolve(w, stats.binom.pmf(np.arange(D + 1), D, a))[:size]
    post = np.convolve(w, stats.binom.pmf(np.arange(2 * D + 2), 2 * D + 1, a))[:size]
    return pre, post, inf, th


def sf(p):
    """P(X >= m) for m = 0..len(p)."""
    return np.append(np.cumsum(p[::-1])[::-1], 0.0)


def N_cdf(n, m, h, D):
    """P(N(m) <= n) for the greedy count of honest wins with gaps >= D+1 over m slots (array n)."""
    n = np.asarray(n)
    out = np.ones(n.shape)
    out[n < 0] = 0.0
    tr = m - n * D
    ok = (n >= 0) & (tr >= n + 1)
    out[ok] = stats.binom.cdf(n[ok], tr[ok], h)
    return out


def N_logcdf(n, m, h, D):
    n = np.asarray(n)
    out = np.zeros(n.shape)
    out[n < 0] = -np.inf
    tr = m - n * D
    ok = (n >= 0) & (tr >= n + 1)
    out[ok] = stats.binom.logcdf(n[ok], tr[ok], h)
    return out


def P1(x, h, a, D, pre, post, plus=1):
    """P(M_pre + M_post + plus + Bin(x, a) >= N(x - D)): an upper bound on GENESIS P_1(x) with plus = 1
    (since M^+_post <= M_post + 1), and the uncorrected value with plus = 0."""
    s = np.convolve(pre, post)
    s = np.concatenate([np.zeros(plus), s])
    # total coalition side: s + Bin(x, a)
    kmax = min(x, int(x * a + 60 * math.sqrt(x * a) + 400))
    b = stats.binom.pmf(np.arange(kmax + 1), x, a)
    tot = np.convolve(s[:1400], b)
    T = sf(tot)                        # P(tot >= n)
    n = np.arange(0, min(tot.size, (x - D) // (D + 1) + 3))
    cdf = N_cdf(n, x - D, h, D)
    pmf = np.diff(np.concatenate([[0.0], cdf]))
    pmf = np.maximum(pmf, 0.0)
    return float(np.sum(pmf * T[n]))
