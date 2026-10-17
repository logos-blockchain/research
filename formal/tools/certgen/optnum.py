"""Settlement parameters for a numeric certificate, optimized against the exact terms.

`planE.stage2` picks the window, span, empty-run, reach and growth parameters by
log-sum heuristics. Here they are chosen by minimizing the float value of the seven
terms of `settleEps3E` (as `planE.terms` bounds them) directly, then rounded to integers."""
import math
from fractions import Fraction as Fr
from certnum import rdn


def total(cfg, B, P, Lw, J, Gp, r, T, x, yy):
    f = float; D, k, N, G = cfg['Delta'], cfg['k'], cfg['N'], cfg['G']
    e17, e2, lp, lr, b, lpi = f(P['e'][17]), f(P['e'][2]), f(P['lp']), f(P['lr']), f(P['b']), f(P['lpi'])
    tau, c = f(Fr(cfg['tau'])), f(Fr(cfg['c']))
    hhi, hlo, elo = f(B['hhi']), f(B['hlo']), f(B['elo'])
    stat = 1 + (b - 1) / (1 - lr)
    kf = k * 30; epl = 10 * kf; nonce = 6 * kf
    nbD = (epl - nonce - D - 3 - G + D) // (T + D); nEp = (N + 2) // epl
    L = math.log
    logs = [L(N + Gp + 1) + (G // D) * L(1 - (1 - hhi) ** D), L(N + 1) + Gp * L(1 - hlo),
            L(N + Gp + 1) + (J + 1) * L(e17) - (Lw + 1) * L(tau),
            L(N + Gp + 1) + J * L(lpi) + G * L(lp / lpi) + L(e2 * stat),
            L(N + 1) + Lw * L(1 + (x - 1) * (1 - elo)) - (k + 1) * L(x),
            L(N + G + 1) + L(stat) - (r + 1) * L(c),
            L(max(nEp, 1)) + nbD * L(1 + (yy - 1) * (1 - (1 - hlo) ** T)) - (k + r) * L(yy)]
    mx = max(logs)
    return mx + L(sum(math.exp(v - mx) for v in logs))


def optimize(cfg, B, P):
    """the best integer (Lw, J, G', r, T) and rational (x, yy)"""
    from scipy.optimize import minimize
    best = None
    for T in range(5, 80):
        def obj(p):
            Lw, J, Gp, r, x, yy = p
            if min(Lw, J, Gp, r) < 1 or x <= 1.0001 or not (0.05 < yy < 0.9999): return 1e9
            if Lw + cfg['G'] >= 10 * cfg['k'] * 30: return 1e9
            return total(cfg, B, P, Lw, J, Gp, r, T, x, yy)
        p0 = [cfg['Lw'], cfg['J'], cfg['Gp'], cfg['r'], float(Fr(cfg['x'])), float(Fr(cfg['yy']))]
        r_ = minimize(obj, p0, method='Nelder-Mead', options=dict(maxiter=8000, xatol=1e-6, fatol=1e-10))
        if best is None or r_.fun < best[0]: best = (r_.fun, T, r_.x)
    _, T, (Lw, J, Gp, r, x, yy) = best
    cand = dict(Lw=round(Lw), J=round(J), Gp=round(Gp), r=round(r), T=T, x=str(rdn(Fr(x), 5)), yy=str(rdn(Fr(yy), 4)))
    # integer polish: one step in each length
    def val(cd): return total(cfg, B, P, cd['Lw'], cd['J'], cd['Gp'], cd['r'], cd['T'], float(Fr(cd['x'])), float(Fr(cd['yy'])))
    improved = True
    while improved:
        improved = False
        for key in ('Lw', 'J', 'Gp', 'r'):
            for dlt in (-1, 1):
                cd = dict(cand); cd[key] += dlt
                if cd[key] >= 1 and val(cd) < val(cand): cand = cd; improved = True
    return cand, math.exp(val(cand))
