"""Float evaluation of settleEps2 (Tail2.lean) with the Lean automaton bounds (alo/halo band)."""
import math, numpy as np
import auto
from auto import xg, solve, autoBound, lp_needed

def slot4(B, F):
    ff, ft, tf, tt = F(False, False), F(False, True), F(True, False), F(True, True)
    c1 = ft - ff; c2 = tf - ff; c3 = tt - tf - ft + ff
    return (ff + c1 * (B['amax'] if ff <= ft else B['alo']) + c2 * (B['hhi'] if ff <= tf else B['hlo'])
            + c3 * (B['hahi'] if tf + ft <= tt + ff else B['halo']))
auto.slot4 = slot4

def band(f, beta, tol=1e-3):
    """float band matching cert2.band_exact"""
    lam = -math.log(1 - f); rh = (1 - beta) * lam
    h = 1 - math.exp(-rh); p1 = rh * math.exp(-rh); a = 1 - (1 - f) ** beta
    hhi, hlo, am = h * (1 + tol), h * (1 - tol), a * (1 + tol)
    return dict(hhi=hhi, hlo=hlo, amax=am, alo=am, hahi=hhi * am, halo=hlo * am,
                slo=p1 * (1 - tol) * (1 - am), hnlo=hlo * (1 - am), elo=(1 - hhi) * (1 - am))

def es(B, D, c, z, s, d, tau, idx=range(19)):
    out = {}
    for i in idx:
        x, th, g = xg(i, c, z, s, d, tau, 1.0)
        v = solve(B, D, x, th, g)
        out[i] = autoBound(B, x, th, g, v)
    return out

def lse(xs): m = max(xs); return m + math.log10(sum(10 ** (x - m) for x in xs))

def terms(B, D, k, N, fden, par, G, Gp, J, Lw, r, T, x, yy, tau, e=None):
    c, z, s, kap, d = par
    if e is None: e = es(B, D, c, z, s, d, tau)
    lp = lp_needed(B, D, c, z, s, kap, d, e)
    lr = e[0]; b = e[1]; stat = 1 + (b - 1) / (1 - lr)
    kf = k * fden; epl = 10 * kf; nonce = 6 * kf
    grow = epl - nonce - D - 3 - G; nbD = (grow + D) // (T + D); nEp = (N + 2) // epl
    PT = 1 - (1 - B['hlo']) ** T
    L = math.log10
    t = dict(
        long=L(N + 1) + (G // D) * L(1 - (1 - B['hhi']) ** D),
        empty=L(N + 1) + Gp * L(1 - B['hlo']),
        span=L(N + Gp + 1) + (J + 1) * L(e[17]) - (Lw + 1) * L(tau),
        fail=L(N + Gp + 1) + J * L(lp) + L(e[2]) + L(stat),
        win=L(N + 1) + Lw * L(1 + (x - 1) * (1 - B['elo'])) - (k + 1) * L(x),
        reach=L(N + G + 1) + L(stat) - (r + 1) * L(c),
        grow=L(max(nEp, 1)) + nbD * L(1 + (yy - 1) * PT) - (k + r) * L(yy))
    return t, lse(list(t.values())), lp, e
