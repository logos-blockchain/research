"""Exact (Fraction) construction of a multi-epoch certificate `Cert2E` (Prob/Final2E.lean).

Later epochs: the estimate keeps lam*V/D in [llo, lhi] for the visible stake V
(full withholding allowed), so the honest exponent lam*H/D lies in
[(1-beta)*llo, lhi/(1-mu)] and the adversary's in [0, beta/(1-beta) * honest].
Members split the honest range; each has a band (`member_band`).

Tables:
* switching tables `vs` for indices 0, 1, 2, 17: one table that solves every
  member's recursion (`AutoSol (fam k)`);
* one-switch tables for the other indices: `vpost k` (member k's own solution),
  `vmax` (their maximum), `vpre k` (member k's recursion floored at `vmax`).
The potential certificate `Cert2` has an empty family; its `e i` are the
one-switch bounds, `lr`, `b`, `e 2`, `e 17` the switching bounds.
"""
import math
from fractions import Fraction as Fr
from certnum import rup, rdn, flog10
from cert2 import step_val, auto_bound, check_sol, solve_exact, xg_exact, lp_exact, check_cert
from emit_gen import member_band, LAM, ETA, ZETA, errLo, errHi

FP = Fr(33, 1000)            # f_p = fP / PRECISION in Config.spec
PERIOD = 388800              # 6 * kf
EL = 648000                  # 10 * kf
SIDX = [0, 1, 2, 17]
EIDX = [i for i in range(19) if i not in (2, 17)]


def tband(beta, delta, mu=Fr(0), d=8):
    """band constants (llo, lhi) consistent with constant stake: lhi = fp/((1-delta) clo),
    llo = fp/((1+delta) chi), rounded outward."""
    beta, delta = Fr(beta).limit_denominator(1000), Fr(delta).limit_denominator(10000)
    lhi = FP / (1 - delta)
    llo = FP / (1 + delta)
    for _ in range(30):
        Yh = lhi / (1 - mu); ylo = (1 - beta) * llo
        clo = 1 - Yh / 2 - 2 * errHi(Yh) / ylo
        Ya = beta / (1 - beta) * Yh
        chi = 1 + (errLo(Yh) + errLo(Ya)) / llo
        lhi = rup(FP / ((1 - delta) * clo), d); llo = rdn(FP / ((1 + delta) * chi), d)
    return dict(beta=beta, delta=delta, mu=mu, llo=llo, lhi=lhi)


def tband_derived(T):
    Yh = T['lhi'] / (1 - T['mu']); ylo = (1 - T['beta']) * T['llo']
    Ya = T['beta'] / (1 - T['beta']) * Yh
    clo = 1 - Yh / 2 - 2 * errHi(Yh) / ylo
    chi = 1 + (errLo(Yh) + errLo(Ya)) / T['llo']
    return dict(Yh=Yh, ylo=ylo, Ya=Ya, clo=clo, chi=chi)


def band_eps_float(T, P=PERIOD):
    dv = tband_derived(T); d = float(T['delta'])
    m = (P - 1) * float(dv['ylo'] * dv['clo'])
    return math.exp(-m * d * d / 2) + math.exp(-m * d * d * (0.5 - 2 / 9 * d))


def epoch_members(T, K, d=12):
    """K members covering the honest exponent [ylo, Yh] geometrically."""
    dv = tband_derived(T)
    lo, hi = float(dv['ylo']), float(dv['Yh'])
    ys = [rdn(dv['ylo'], d)] + [rdn(Fr(lo * (hi / lo) ** (j / K)), d) for j in range(1, K)] + [rup(dv['Yh'], d)]
    beta = T['beta']
    out = []
    for j in range(K):
        ylo, yhi = ys[j], ys[j + 1]
        ahi = rup(beta / (1 - beta) * yhi, d)
        out.append(dict(ylo=ylo, yhi=yhi, ahi=ahi, B=member_band(ylo, yhi, ahi)))
    return out


def weakest(bands):
    keys_max = ['hhi', 'amax', 'hahi']
    keys_min = ['hlo', 'slo', 'hnlo', 'elo', 'alo', 'halo']
    B = {k: max(b[k] for b in bands) for k in keys_max}
    B.update({k: min(b[k] for b in bands) for k in keys_min})
    return B


def keys(D):
    return [(q, a, u) for q in range(D) for a in range(3) for u in (False, True)]


def round_up_table(v, D, bump, d):
    m = max(v.values())
    return {key: (rup(val * (1 + bump) + bump * m * (D + 1 - key[0]) / (D + 1), d) if val > 0 else Fr(0))
            for key, val in v.items()}


def solve_switch(fam, D, x, th, g, d=13):
    """one table solving every member's recursion"""
    Bfs = [{k: float(v) for k, v in B.items()} for B in fam]
    gf = lambda a, b, u: float(g(a, b, u))
    v = {key: gf(key[1], True, key[2]) for key in keys(D)}
    for _ in range(100000):
        nv = {key: max([gf(key[1], True, key[2])] + [float(step_val(Bf, D, float(x), float(th), gf, v, *key)) for Bf in Bfs])
              for key in v}
        diff = max(abs(nv[k] - v[k]) for k in v); v = nv
        if diff < 1e-16: break
    for bump in [1e-12, 1e-11, 1e-10, 1e-9, 1e-8, 1e-7]:
        V = round_up_table(v, D, bump, d)
        if all(check_sol(B, D, x, th, g, V) for B in fam): return V
    raise Exception('no switching solution')


def check_pre(B, D, x, th, g, vmax, V):
    for key in keys(D):
        if vmax[key] > V[key]: return False
        if step_val(B, D, x, th, g, V, *key) > V[key]: return False
    return True


def solve_pre(B, D, x, th, g, vmax, d=13):
    Bf = {k: float(v) for k, v in B.items()}
    gf = lambda a, b, u: float(g(a, b, u))
    vm = {k: float(v) for k, v in vmax.items()}
    v = dict(vm)
    for _ in range(100000):
        nv = {key: max(vm[key], float(step_val(Bf, D, float(x), float(th), gf, v, *key))) for key in v}
        diff = max(abs(nv[k] - v[k]) for k in v); v = nv
        if diff < 1e-16: break
    for bump in [1e-12, 1e-11, 1e-10, 1e-9, 1e-8, 1e-7]:
        V = round_up_table(v, D, bump, d)
        V = {k: max(V[k], vmax[k]) for k in V}
        if check_pre(B, D, x, th, g, vmax, V): return V
    raise Exception('no pre-switch solution')


def build_E(fam, D, c, z, s, kap, d, tau, d_dig=13):
    """all tables and bounds; returns dict"""
    out = dict(vs={}, eS={}, post={}, vmax={}, pre={}, eE={})
    for i in SIDX:
        x, th, g = xg_exact(i, c, z, s, d, tau)
        V = solve_switch(fam, D, x, th, g, d_dig)
        out['vs'][i] = V
        out['eS'][i] = [rup(auto_bound(B, x, th, g, V), d_dig) for B in fam]
    for i in EIDX:
        x, th, g = xg_exact(i, c, z, s, d, tau)
        posts = [solve_exact(B, D, x, th, g, d_dig) for B in fam]
        vmax = {key: max(p[key] for p in posts) for key in keys(D)}
        pres = [solve_pre(B, D, x, th, g, vmax, d_dig) for B in fam]
        out['post'][i], out['vmax'][i], out['pre'][i] = posts, vmax, pres
        out['eE'][i] = [rup(auto_bound(B, x, th, g, P), d_dig) for B, P in zip(fam, pres)]
        out.setdefault('eIn', {})[i] = [rup(auto_bound(B, x, th, g, P), d_dig) for B, P in zip(fam, posts)]
    # the potential's numbers
    e = [Fr(0)] * 19
    for i in EIDX: e[i] = max(out['eE'][i])
    e[2] = max(out['eS'][2]); e[17] = max(out['eS'][17])
    lr = max(max(out['eS'][0]), e[0]); b = max(max(out['eS'][1]), e[1], Fr(1))
    out['e'], out['lr'], out['b'] = e, lr, b
    ei = [Fr(0)] * 19
    for i in EIDX: ei[i] = max(out['eIn'][i])
    ei[2], ei[17] = e[2], e[17]
    out['ei'] = ei
    out['pat0'] = rdn(min(B['slo'] * B['elo'] ** D for B in fam), 13)
    return out


def lp_in_exact(D, c, z, s, kap, d, ei, pat0):
    """the least in-epoch contraction meeting the class conditions with crossing bound pat0"""
    return lp_exact({'slo': pat0, 'elo': Fr(1)}, D, c, z, s, kap, d, ei)


def check_class(D, c, z, s, kap, d, lp, e, pat):
    ok = [e[0] <= lp, e[1] - (1 - (s + kap) / z) * pat <= lp,
          s * (e[3] - lp) + kap * (e[7] - lp) <= 0, s * c * (e[4] - lp) + kap * d * (e[8] - lp) <= 0,
          s * c ** 2 * (e[4] - lp) + kap * d ** 2 * (e[9] - lp) <= 0, e[4] <= lp,
          s * c ** 3 * (e[4] - lp) + kap * d ** 3 * max(e[10] - lp, 0) + kap * e[15] <= 0,
          s * (e[5] - lp) + kap * (e[11] - lp) <= 0, s * c * (e[6] - lp) + kap * d * (e[12] - lp) <= 0,
          s * c ** 2 * (e[6] - lp) + kap * d ** 2 * (e[13] - lp) <= 0, e[6] <= lp,
          s * c ** 3 * (e[6] - lp) + kap * d ** 3 * max(e[14] - lp, 0) + kap * e[16] <= 0]
    return all(ok), ok
