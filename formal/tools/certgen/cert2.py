"""Exact (Fraction) Cert2 construction mirroring Cold2.lean / Auto.lean."""
import math
from fractions import Fraction as Fr
from certnum import rup, rdn, flog10
import auto
from auto import xg

TOL = 1e-3

def band_exact(f, beta, d=13, tol=TOL):
    """rounded band with relative tolerance `tol` on the honest and adversarial win rates.
    The worst-case kernel has adversary rate exactly amax, so alo = amax, hahi >= hhi*amax, halo <= hlo*amax."""
    lam = -math.log(1 - f); rh = (1 - beta) * lam
    h = 1 - math.exp(-rh); p1 = rh * math.exp(-rh); a = 1 - (1 - f) ** beta
    hhi = rup(h * (1 + tol), d); hlo = rdn(h * (1 - tol), d); amax = rup(a * (1 + tol), d)
    return dict(hhi=hhi, hlo=hlo, amax=amax, alo=amax, hahi=rup(hhi * amax, d), halo=rdn(hlo * amax, d),
                slo=rdn(Fr(p1) * (1 - tol) * (1 - amax), d), hnlo=rdn(hlo * (1 - amax), d),
                elo=rdn((1 - hhi) * (1 - amax), d))

def slot4(B, F):
    ff, ft, tf, tt = F(False, False), F(False, True), F(True, False), F(True, True)
    return (ff + (ft - ff) * (B['amax'] if ff <= ft else B['alo']) + (tf - ff) * (B['hhi'] if ff <= tf else B['hlo'])
            + (tt - tf - ft + ff) * (B['hahi'] if tf + ft <= tt + ff else B['halo']))

def acap(n): return min(n, 2)

def step_val(B, D, x, th, g, v, q, a, u):
    def F(hh, aa):
        a2 = acap(a + (1 if aa else 0)); xf = x if aa else 1
        if hh: nxt = v[(0, a2, True)]
        elif q + 1 == D: nxt = g(a2, True, u)
        else: nxt = v[(q + 1, a2, u)]
        return xf * nxt
    return th * slot4(B, F)

def auto_bound(B, x, th, g, v):
    def F(hh, aa):
        a2 = acap(1 if aa else 0); xf = x if aa else 1
        return xf * (v[(0, a2, False)] if hh else g(a2, False, False))
    return th * slot4(B, F)

def check_sol(B, D, x, th, g, v):
    for q in range(D):
        for a in range(3):
            for u in (False, True):
                if g(a, True, u) > v[(q, a, u)]: return False
                if step_val(B, D, x, th, g, v, q, a, u) > v[(q, a, u)]: return False
    return True

def solve_exact(B, D, x, th, g, d=13):
    Bf = {k: float(v) for k, v in B.items()}
    gf = lambda a, b, u: float(g(a, b, u))
    v = {(q, a, u): gf(a, True, u) for q in range(D) for a in range(3) for u in (False, True)}
    for _ in range(100000):
        nv = {key: max(gf(key[1], True, key[2]), float(step_val(Bf, D, float(x), float(th), gf, v, *key))) for key in v}
        diff = max(abs(nv[k] - v[k]) for k in v); v = nv
        if diff < 1e-16: break
    for bump in [1e-12, 1e-11, 1e-10, 1e-9, 1e-8, 1e-7]:
        m = max(v.values())
        V = {key: (rup(val * (1 + bump) + bump * m * (D + 1 - key[0]) / (D + 1), d) if val > 0 else Fr(0)) for key, val in v.items()}
        # zero entries must stay exact zeros only if the true value is 0
        if check_sol(B, D, x, th, g, V): return V
    raise Exception('no solution')

def xg_exact(i, c, z, s, d, tau):
    return xg(i, c, z, s, d, tau, Fr(1))

def build(B, D, c, z, s, kap, d, tau, d_dig=13):
    vs, es = [], []
    for i in range(19):
        x, th, g = xg_exact(i, c, z, s, d, tau)
        V = solve_exact(B, D, x, th, g, d_dig)
        vs.append(V); es.append(rup(auto_bound(B, x, th, g, V), d_dig))
    return vs, es

def lp_exact(B, D, c, z, s, k, d, e):
    """the least lp (rounded up) meeting all Cert2 class conditions, exactly"""
    cands = [e[0], e[1] - (1 - (s + k) / z) * B['slo'] * B['elo'] ** D]
    for (ia, ib, rho) in [(3, 7, 0), (4, 8, 1), (4, 9, 2), (5, 11, 0), (6, 12, 1), (6, 13, 2)]:
        wa = s * c ** rho; wb = k * d ** rho
        cands.append((wa * e[ia] + wb * e[ib]) / (wa + wb))
    for (ia, ib, iab) in [(4, 10, 15), (6, 14, 16)]:
        wa = s * c ** 3; wb = k * d ** 3
        lo = max(e[ia], (wa * e[ia] + k * e[iab]) / wa)
        lo2 = max((wa * e[ia] + wb * e[ib] + k * e[iab]) / (wa + wb), e[ia])
        cands.append(lo if e[ib] <= lo else lo2)
    lp = rup(max(cands), 13)
    return lp

def check_cert(B, D, c, z, s, k, d, tau, lp, lr, b, e):
    ok = [1 <= c, 1 <= z, 1 <= s, 0 <= k, 0 < d <= 1, s + k <= z, 1 <= tau, 0 <= lp < 1, 0 <= lr < 1, 1 <= b,
          1 <= e[17], e[0] <= lr, e[1] <= b, e[0] <= lp,
          e[1] - (1 - (s + k) / z) * (B['slo'] * B['elo'] ** D) <= lp,
          s * (e[3] - lp) + k * (e[7] - lp) <= 0, s * c * (e[4] - lp) + k * d * (e[8] - lp) <= 0,
          s * c ** 2 * (e[4] - lp) + k * d ** 2 * (e[9] - lp) <= 0, e[4] <= lp,
          s * c ** 3 * (e[4] - lp) + k * d ** 3 * max(e[10] - lp, 0) + k * e[15] <= 0,
          s * (e[5] - lp) + k * (e[11] - lp) <= 0, s * c * (e[6] - lp) + k * d * (e[12] - lp) <= 0,
          s * c ** 2 * (e[6] - lp) + k * d ** 2 * (e[13] - lp) <= 0, e[6] <= lp,
          s * c ** 3 * (e[6] - lp) + k * d ** 3 * max(e[14] - lp, 0) + k * e[16] <= 0]
    return all(ok), ok
