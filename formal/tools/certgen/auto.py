"""Python model of Cryptarchia/Prob/Auto.lean + Cold2.lean (floats for search, Fractions for certificates)."""
import math
from fractions import Fraction as Fr

def acap(n): return min(n, 2)

def gtab(t0, t1, t2):
    return lambda a, b, u: t0(b, u) if a == 0 else (t1(b, u) if a == 1 else t2(b, u))

def xg(i, c, z, s, d, tau, one=1):
    inv = lambda v: one / v
    if i == 0: f = lambda b, u: inv(c) if b else one; return c, one, gtab(f, f, f)
    if i == 1: return c, one, (lambda a, b, u: one)
    if i == 2: return z, one, gtab(lambda b, u: one if b else 0 * one, lambda b, u: one, lambda b, u: one)
    if i == 3: return c, one, gtab(lambda b, u: inv(z) if b else one, lambda b, u: z / s, lambda b, u: z / s)
    if i == 4: return c, one, gtab(lambda b, u: inv(c * z) if b else one, lambda b, u: z / s, lambda b, u: z / s)
    if i == 5: return c * z, one, gtab(lambda b, u: inv(z) if b else one, lambda b, u: inv(z) if b else one, lambda b, u: inv(s) if b else one)
    if i == 6: return c * z, one, gtab(lambda b, u: inv(c * z) if b else one, lambda b, u: inv(c * z) if b else one, lambda b, u: inv(s) if b else one)
    zero = lambda b, u: 0 * one
    if i == 7: return d * z, one, gtab(lambda b, u: inv(z) if b else one, zero, zero)
    if i == 8: return d * z, one, gtab(lambda b, u: inv(d * z) if b else one, zero, zero)
    if i == 9: return d * z, one, gtab(lambda b, u: (inv(d * d * z) if u else inv(d * z)) if b else one, zero, zero)
    if i == 10: return d * z, one, gtab(lambda b, u: 0 * one if u else (inv(d * z) if b else one), zero, zero)
    if i == 11: return d * z, one, (lambda a, b, u: inv(z) if b else one)
    if i == 12: return d * z, one, (lambda a, b, u: inv(d * z) if b else one)
    if i == 13: return d * z, one, (lambda a, b, u: (inv(d * d * z) if u else inv(d * z)) if b else one)
    if i == 14: return d * z, one, (lambda a, b, u: 0 * one if u else (inv(d * z) if b else one))
    if i == 15: return z, one, gtab(lambda b, u: inv(z) if u else 0 * one, zero, zero)
    if i == 16: return z, one, (lambda a, b, u: inv(z) if u else 0 * one)
    if i == 17: return one, tau, (lambda a, b, u: one)
    return one, one, (lambda a, b, u: one)

def slot4(B, F):
    ff, ft, tf, tt = F(False, False), F(False, True), F(True, False), F(True, True)
    c1 = ft - ff; c2 = tf - ff; c3 = tt - tf - ft + ff
    zero = c1 * 0
    return ff + max(c1, zero) * B['amax'] + (c2 * B['hhi'] if ff <= tf else c2 * B['hlo']) + max(c3, zero) * B['hahi']

def step_val(B, D, x, th, g, v, q, a, u):
    def F(hh, aa):
        a2 = acap(a + (1 if aa else 0))
        xf = x if aa else x * 0 + 1
        if hh: nxt = v[(0, a2, True)]
        elif q + 1 == D: nxt = g(a2, True, u)
        else: nxt = v[(q + 1, a2, u)]
        return xf * nxt
    return th * slot4(B, F)

def solve(B, D, x, th, g, iters=4000):
    v = {(q, a, u): float(g(a, True, u)) for q in range(D) for a in range(3) for u in (False, True)}
    for _ in range(iters):
        nv = {}
        diff = 0.0
        for key in v:
            q, a, u = key
            val = max(float(g(a, True, u)), step_val(B, D, x, th, g, v, q, a, u))
            nv[key] = val
            diff = max(diff, abs(val - v[key]))
        v = nv
        if diff < 1e-15: break
    return v

def autoBound(B, x, th, g, v):
    def F(hh, aa):
        a2 = acap(1 if aa else 0)
        xf = x if aa else x * 0 + 1
        return xf * (v[(0, a2, False)] if hh else g(a2, False, False))
    return th * slot4(B, F)

def es(B, D, c, z, s, d, tau):
    out = []
    for i in range(19):
        x, th, g = xg(i, c, z, s, d, tau, 1.0)
        v = solve(B, D, x, th, g)
        out.append(autoBound(B, x, th, g, v))
    return out

def lp_needed(B, D, c, z, s, k, d, e):
    """smallest lp satisfying the Cert2 class conditions"""
    cands = [e[0], e[1] - (1 - (s + k) / z) * B['slo'] * B['elo'] ** D]
    for (ia, ib, rho) in [(3, 7, 0), (4, 8, 1), (4, 9, 2), (5, 11, 0), (6, 12, 1), (6, 13, 2)]:
        wa = s * c ** rho; wb = k * d ** rho
        cands.append((wa * e[ia] + wb * e[ib]) / (wa + wb))
    for (ia, ib, iab) in [(4, 10, 15), (6, 14, 16)]:
        # e_a <= lp and s c^3 (e_a - lp) + k d^3 max(e_b - lp, 0) + k e_abs <= 0
        wa = s * c ** 3; wb = k * d ** 3
        lo = max(e[ia], (wa * e[ia] + k * e[iab]) / wa)     # if e_b <= lp
        # if e_b > lp: lp >= (wa e_a + wb e_b + k e_abs)/(wa + wb)
        lo2 = (wa * e[ia] + wb * e[ib] + k * e[iab]) / (wa + wb)
        lp = lo if e[ib] <= lo else max(lo2, e[ia])
        cands.append(lp)
    return max(cands)
