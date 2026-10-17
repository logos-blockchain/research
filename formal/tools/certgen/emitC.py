"""Emit a closed-form multi-epoch certificate: one theorem for every depth k >= k0 and
every horizon N (`Cryptarchia/Prob/Closed.lean`).

The automaton tables do not depend on k or N: they depend on the band (f, beta), Delta and
the potential's constants. So the tables and the band family are planned once, with the
band valid from k0 on (its drift conditions only get easier as the period grows), and the
settlement bound's lengths grow with t = k / 20: G' = g t, J = j t, Lw = w t, r = rho t.
Each term of `settleEps3E` is then (N + c) * A * q^t (`settleEps3E_closed`), and the
estimate's band term is 3 / Q^t (`bandEps_closed`).

Usage: python3 emitC.py BETA DELTA DELTA_TSI K NAME OUTDIR K0 [MU] [RHO]
"""
import sys, os, math, pickle, json
from fractions import Fraction as Fr
from certnum import rup, rdn
import certE, planE

M_DIV = 20     # t = k / M_DIV


def closed_floats(P, B, cfg, D, j, w, g, rho, x, yy, Tg):
    """the closed form's constants and rates, in floats (as `closed_section` bounds them)"""
    f = float; m = M_DIV; G = cfg['G']
    e17, tau, lpi, lp, e2, b, lr = f(P['e'][17]), f(Fr(cfg['tau'])), f(P['lpi']), f(P['lp']), f(P['e'][2]), f(P['b']), f(P['lr'])
    c = f(Fr(cfg['c'])); hhi, hlo, elo = f(B['hhi']), f(B['hlo']), f(B['elo'])
    stat = 1 + (b - 1) / (1 - lr)
    nb = 120 * m // (Tg + D); nb0 = -(-(3 + G) // (Tg + D)) + 1
    bs = 1 + (yy - 1) * (1 - (1 - hlo) ** Tg)
    L = math.log
    return dict(A1=(1 - (1 - hhi) ** D) ** (G // D), q2=g * L(1 - hlo), A3=e17 / tau, q3=j * L(e17) - w * L(tau),
                A4=(lp / lpi) ** G * e2 * stat, q4=j * L(lpi), A5=1 / x, q5=w * L(1 + (x - 1) * (1 - elo)) - m * L(x),
                A6=stat / c, q6=-rho * L(c), A7=bs ** -nb0 * yy ** -m, q7=nb * L(bs) - (m + rho) * L(yy))


def closed_value(cf, N, t, g, G):
    """log of the settlement part of the closed form at (N, t)"""
    E = math.exp
    terms = [(N + g * t + 1) * cf['A1'], (N + 1) * E(cf['q2'] * t), (N + g * t + 1) * cf['A3'] * E(cf['q3'] * t),
             (N + g * t + 1) * cf['A4'] * E(cf['q4'] * t), (N + 1) * cf['A5'] * E(cf['q5'] * t),
             (N + G + 1) * cf['A6'] * E(cf['q6'] * t), (N + 2) * cf['A7'] * E(cf['q7'] * t)]
    return math.log(sum(terms))


def opt_params(P, B, cfg, D, N_ref=5184000, k_ref=2160):
    """integer per-t lengths and the free reals, minimizing the closed form at (N_ref, k_ref),
    with every term decaying"""
    from scipy.optimize import minimize
    m = M_DIV; t_ref = k_ref // m; G = cfg['G']
    best = None
    divs = [t - D for t in range(D + 5, 120 * m) if (120 * m) % t == 0]
    for Tg in divs[:14]:
        def obj(p):
            j, w, g, rho, x, yy = p
            if min(j, w, g, rho) <= 0 or x <= 1.0001 or not (0.05 < yy < 0.9999): return 1e9
            cf = closed_floats(P, B, cfg, D, math.ceil(j), math.ceil(w), math.ceil(g), math.ceil(rho), x, yy, Tg)
            if max(cf[k] for k in ('q2', 'q3', 'q4', 'q5', 'q6', 'q7')) >= 0: return 1e9
            return closed_value(cf, N_ref, t_ref, math.ceil(g), G)
        for x0 in [1.15, 1.22]:
            for yy0 in [0.5, 0.8]:
                r = minimize(obj, [9.07 * m, 16.2 * m, 0.85 * m, 0.147 * m, x0, yy0], method='Nelder-Mead',
                             options=dict(maxiter=6000, xatol=1e-7, fatol=1e-10))
                if best is None or r.fun < best[0]: best = (r.fun, Tg, r.x)
    _, Tg, (j, w, g, rho, x, yy) = best
    J, W, Gp, R = math.ceil(j), math.ceil(w), math.ceil(g), math.ceil(rho)
    X, YY = rdn(Fr(x), 5), rdn(Fr(yy), 4)
    cf = closed_floats(P, B, cfg, D, J, W, Gp, R, float(X), float(YY), Tg)
    return dict(j=J, w=W, g=Gp, rho=R, x=X, yy=YY, Tg=Tg,
                rate=max(cf[k] for k in ('q2', 'q3', 'q4', 'q5', 'q6', 'q7')),
                ref=math.exp(closed_value(cf, N_ref, t_ref, Gp, G)))


def closed_consts(cfg, T, B, P, D, cl):
    """the closed form's constants: each settlement term's `A` and `q`, the band's `C` and `Q`, and
    the short form's rates; every power bounded outward to 14 digits (`powq`)"""
    import powq
    G = cfg['G']; m = M_DIV; k0 = cl['k0']
    j, w, g, rho, Tg, x, yy = cl['j'], cl['w'], cl['g'], cl['rho'], cl['Tg'], cl['x'], cl['yy']
    e17, e2, lp, lr, b, lpi = P['e'][17], P['e'][2], P['lp'], P['lr'], P['b'], P['lpi']
    tau, c = Fr(cfg['tau']), Fr(cfg['c'])
    hhi, hlo, elo = B['hhi'], B['hlo'], B['elo']
    up = lambda base, n: powq.pow_up(14, base, n)
    dn = lambda base, n: powq.pow_dn(14, base, n)
    stat = 1 + (b - 1) / (1 - lr)
    nb = 120 * m // (Tg + D)
    assert 120 * m == nb * (Tg + D)
    nb0 = -(-(3 + G) // (Tg + D)) + 1
    bs = 1 + (yy - 1) * (1 - (1 - hlo) ** Tg)
    consts = dict(A1=up(rup(1 - (1 - hhi) ** D, 14), G // D), q2=up(rup(1 - hlo, 14), g),
                  A3=rup(e17 / tau, 14), q3=rup(up(e17, j) / dn(tau, w), 14),
                  A4=rup(up(lp / lpi, G) * e2 * stat, 14), q4=up(lpi, j),
                  A5=rup(1 / x, 14), q5=rup(up(1 + (x - 1) * (1 - elo), w) / dn(x, m), 14),
                  A6=rup(stat / c, 14), q6=rup(1 / dn(c, rho), 14),
                  A7=rup((1 / rdn(bs, 14)) ** nb0 * (1 / yy) ** m, 14), q7=rup(up(rup(bs, 14), nb) / dn(yy, m + rho), 14))
    # the band: exp a ≤ 1 / (1 - a) ≤ C, and exp (-p0 a) ≤ 1 / Q
    dv = certE.tband_derived(T)
    delta = T['delta']
    a1 = dv['ylo'] * dv['clo'] * delta ** 2 / 2
    a2 = dv['ylo'] * dv['clo'] * delta ** 2 * (Fr(1, 2) - Fr(2, 9) * delta)
    nexp, p0 = 4096, 180 * m
    Cs = [rup(1 / (1 - a), 10) for a in (a1, a2)]
    Qs = [dn(1 + rdn(p0 * a, 8) / nexp, nexp) for a in (a1, a2)]
    # the short form: from t0 = k0 / m on, every settlement term under the slowest settlement rate
    # qs, every band term under the slower band rate qb
    t0 = k0 // m
    qi = {i: consts[f'q{i}'] for i in range(2, 8)}
    Ai = {2: Fr(1), **{i: consts[f'A{i}'] for i in range(3, 8)}}
    qs = rup(max(qi.values()), 6)
    bq = [1 / Q for Q in Qs]
    qb = rup(max(bq), 6)
    As = sum(rup(Ai[i] * (qi[i] / qs) ** t0, 6) for i in qi)
    Ab = sum(rup(Cs[i] * (bq[i] / qb) ** t0, 6) for i in range(2))
    short = dict(t0=t0, qs=qs, As=As, qb=qb, Ab=Ab)
    return consts, Qs, nb, nb0, Cs, short


def eval_closed(consts, Qs, Cs, cl, G, N, k):
    """the closed form's value, in floats"""
    t = k // M_DIV; g = cl['g']
    c = {kk: float(v) for kk, v in consts.items()}
    s = ((N + g * t + 1) * c['A1'] + (N + 1) * c['q2'] ** t + (N + g * t + 1) * c['A3'] * c['q3'] ** t +
         (N + g * t + 1) * c['A4'] * c['q4'] ** t + (N + 1) * c['A5'] * c['q5'] ** t + (N + G + 1) * c['A6'] * c['q6'] ** t +
         (N + 2) * c['A7'] * c['q7'] ** t)
    band = (N // (300 * k) + 2) * sum(float(C) * float(1 / Q) ** t for C, Q in zip(Cs, Qs))
    return s, band


if __name__ == "__main__":
    beta, D, delta, K = float(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
    name, out_dir, k0 = sys.argv[5], sys.argv[6], int(sys.argv[7])
    mu = float(sys.argv[8]) if len(sys.argv) > 8 else 0.1
    rho = Fr(sys.argv[9]) if len(sys.argv) > 9 else certE.RHO
    pk = f"res_{name}.pkl"
    # the band is valid from depth k0 on: its drift conditions use the period 180 k0
    certE.PERIOD = 180 * k0
    orig = certE.tband
    planE.tband = lambda b_, d_, mu=Fr(0), d=8: orig(b_, d_, mu=mu, d=d, rho=rho)
    if os.path.exists(pk):
        res = pickle.load(open(pk, 'rb'))
    else:
        res = planE.make(beta, D, delta, K, 5184000, mu=mu)
        pickle.dump(res, open(pk, 'wb'))
    cfg, T, fam, B, P, Ts = res
    cl = opt_params(P, B, cfg, D)
    cl['k0'] = k0
    print('closed params', cl)
    import emitF
    emitF.emit_closed(cfg, T, fam, B, P, name, out_dir, cl)
    consts, Qs, nb, nb0, Cs, short = closed_consts(cfg, T, B, P, D, cl)
    for (N, k) in [(5184000, 2160), (31536000, 2160), (5184000, 1000), (5184000, 1500), (5184000, 3000)]:
        s, band = eval_closed(consts, Qs, Cs, cl, cfg['G'], N, k)
        print(f'N={N} k={k}: settlement {s:.3e} band {band:.3e} total {s + band:.3e}')
        t = k // M_DIV; f = {kk: float(v) for kk, v in short.items()}
        sh = (N + cl['g'] * t + cfg['G'] + 2) * (float(consts['A1']) + f['As'] * f['qs'] ** t) + (N // (300 * k) + 2) * f['Ab'] * f['qb'] ** t
        print(f'   short form {sh:.3e}')
    json.dump(dict(cfg, closed={kk: str(v) for kk, v in cl.items()}, consts={kk: str(v) for kk, v in consts.items()},
                   Q=[str(Q) for Q in Qs]), open(f"cfgC_{name}.json", "w"), indent=1)
