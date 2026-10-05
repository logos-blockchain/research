"""Plan and build a multi-epoch certificate; print its terms (no Lean)."""
import sys, json, math, time
from fractions import Fraction as Fr
import plan
from certE import tband, tband_derived, epoch_members, weakest, build_E, band_eps_float, EL, lp_in_exact, check_class
from cert2 import lp_exact, check_cert
from certnum import rup, rdn, flog10
from gen import chain

def rnd(x, n): return Fr(round(x * 10 ** n), 10 ** n)

def terms(cfg, B, P):
    """exact upper bounds on the seven terms of settleEps2E (as in emit2.epsilon, long term with N+G'+1)"""
    D, k, N = cfg['Delta'], cfg['k'], cfg['N']
    G, Gp, J, Lw, r, T = cfg['G'], cfg['Gp'], cfg['J'], cfg['Lw'], cfg['r'], cfg['T']
    x, yy = Fr(cfg['x']), Fr(cfg['yy'])
    es, lp, lr, b, tau, c = P['e'], P['lp'], P['lr'], P['b'], Fr(cfg['tau']), Fr(cfg['c'])
    stat = 1 + (b - 1) / (1 - lr)
    kf = k * 30; epl = 10 * kf; nonce = 6 * kf
    grow = epl - nonce - D - 3 - G; nbD = (grow + D) // (T + D); nEp = (N + 2) // epl
    out = {}
    base1 = rup(1 - (1 - B['hhi']) ** D, 14); out['long'] = chain(base1, G // D, True, name='la') + (base1,)
    base2 = rup(1 - B['hlo'], 14); out['empty'] = chain(base2, Gp, True, name='em') + (base2,)
    out['span_a'] = chain(es[17], J + 1, True, name='sa'); out['span_b'] = chain(tau, Lw + 1, False, name='sb')
    if 'lpi' in P:
        out['fail'] = chain(P['lpi'], J, True, name='fa')
        out['ratio'] = chain(lp / P['lpi'], G, True, name='ra')
    else:
        out['fail'] = chain(lp, J, True, name='fa')
    base3 = 1 + (x - 1) * (1 - B['elo']); out['win_a'] = chain(base3, Lw, True, name='wa') + (base3,)
    out['win_b'] = chain(x, k + 1, False, name='wb'); out['reach'] = chain(c, r + 1, False, name='rc')
    PT = 1 - (1 - B['hlo']) ** T
    base5 = rup(1 + (yy - 1) * PT, 14); out['grow_a'] = chain(base5, nbD, True, name='da') + (base5,)
    out['grow_b'] = chain(yy, k + r, False, name='db')
    U = lambda key: out[key][1]
    Ts = [(N + Gp + 1) * U('long'), (N + 1) * U('empty'), (N + Gp + 1) * (U('span_a') / U('span_b')),
          (N + Gp + 1) * (U('fail') * (U('ratio') if 'lpi' in P else 1) * es[2] * stat), (N + 1) * (U('win_a') / U('win_b')),
          (N + G + 1) * (stat / U('reach')), nEp * (U('grow_a') / U('grow_b'))]
    return out, [rup(t, 6) for t in Ts], dict(nbD=nbD, nEp=nEp, stat=stat)


def stage2(Bw, D, N, tau, lp_eff, e17, e2, stat, Gfix=None, k=2160, fden=30, target_rel=1e-3):
    """choose Lw, J, x, G', r, G, T, yy for the weakest band, a fixed span base and contraction"""
    from scipy.optimize import minimize_scalar
    import numpy as np
    L = math.log10
    a, bb = L(e17), -L(lp_eff)
    C = L(e2 * stat)
    best = None
    Gp = 3000
    for Lw in range(10000, 200001, 1000):
        J = max(1, round(((Lw + 1) * L(tau) - a + C) / (a + bb)))
        sp = L(N + Gp + 1) + (J + 1) * a - (Lw + 1) * L(tau); fl = L(N + Gp + 1) - J * bb + C
        rw = minimize_scalar(lambda lx: L(N + 1) + Lw * L(1 + (math.exp(lx) - 1) * (1 - Bw['elo'])) - (k + 1) * lx / math.log(10),
                             bounds=(1e-4, 3), method='bounded')
        tot = plan.lse([sp, fl, rw.fun])
        if best is None or tot < best[0]: best = (tot, Lw, J, math.exp(rw.x))
    tot, Lw, J, x = best
    goal = tot + L(target_rel)
    Gp = math.ceil((L(N + 1) - goal) / -L(1 - Bw['hlo']))
    r = math.ceil((L(N + 3000) + L(stat) - goal) / L(float(cfgc)) ) if False else None
    G = Gfix if Gfix else max(D * 2, math.ceil((L(N + 1) - goal) / -L(1 - (1 - Bw['hhi']) ** D)) * D + D)
    grow_best = None
    for T in range(5, 80, 1):
        kf = k * fden; grow = 10 * kf - 6 * kf - D - 3 - G; nbD = (grow + D) // (T + D); PT = 1 - (1 - Bw['hlo']) ** T
        for yy in np.linspace(0.2, 0.99, 80):
            v = nbD * L(1 + (yy - 1) * PT) - (k + 0) * L(yy)
            if grow_best is None or v < grow_best[0]: grow_best = (v, T, yy)
    return dict(Lw=Lw, J=J, x=x, Gp=Gp, G=G, T=grow_best[1], yy=grow_best[2], tot=tot, goal=goal)

def make(beta, D, delta, K, N, refined=True):
    t0 = time.time()
    T = tband(beta, delta)
    fam = epoch_members(T, K)
    bands = [m['B'] for m in fam]
    B = weakest(bands)
    Bf = {k: float(v) for k, v in (bands[-1] if refined else B).items()}
    plan.band = lambda f, b: Bf
    p = plan.plan(beta, D, N=N)
    c, z, s, kap, d = p['par']
    c, z, s, d = rnd(c, 4), rnd(z, 4), max(Fr(1), rnd(s, 4)), min(Fr(1), rnd(d, 4))
    kap = min(rnd(kap, 4), z - s)
    tau = Fr(p['tau']).limit_denominator(1000)
    G = max(p['G'], D + 1)
    cfg = dict(beta=beta, Delta=D, delta=delta, K=K, k=2160, N=N, G=G, Gp=p['Gp'], J=p['J'], Lw=p['Lw'], r=p['r'],
               T=p['T'], x=str(rnd(p['x'], 3)), yy=str(rnd(p['yy'], 2)), c=str(c), z=str(z), s=str(s), kap=str(kap),
               d=str(d), tau=str(tau), llo=str(T['llo']), lhi=str(T['lhi']))
    print('plan', {k: v for k, v in p.items() if k not in ('par',)}, f'{time.time()-t0:.0f}s', flush=True)
    P = build_E(bands, D, c, z, s, kap, d, tau)
    lp = lp_exact(B, D, c, z, s, kap, d, P['e'])
    P['lp'] = lp
    if refined:
        P['eik'], P['patk'] = [], []
        for kk, Bk in enumerate(bands):
            ek = [Fr(0)] * 19
            for i in P['eIn']: ek[i] = P['eIn'][i][kk]
            P['eik'].append(ek); P['patk'].append(rdn(Bk['slo'] * Bk['elo'] ** D, 13))
        lpi = max(lp_in_exact(D, c, z, s, kap, d, P['eik'][kk], P['patk'][kk]) for kk in range(len(bands)))
        for kk in range(len(bands)):
            oki, _ = check_class(D, c, z, s, kap, d, lpi, P['eik'][kk], P['patk'][kk])
            assert oki
        assert lpi <= lp
        P['lpi'] = lpi
        Bwf = {kk: float(v) for kk, v in B.items()}
        stat = float(1 + (P['b'] - 1) / (1 - P['lr']))
        s2 = stage2(Bwf, D, N, float(tau), float(lpi), float(P['e'][17]), float(P['e'][2]) * float(lp / lpi) ** G,
                    stat, Gfix=G)
        r = math.ceil((math.log10(N + 3000) + math.log10(stat) - s2['goal']) / math.log10(float(c)))
        cfg.update(Lw=s2['Lw'], J=s2['J'], x=str(rnd(s2['x'], 3)), Gp=s2['Gp'], T=s2['T'], yy=str(rnd(s2['yy'], 2)), r=r)
        print('lpi', float(lpi), 'ratio^G', float(lp / lpi) ** G, 'stage2', s2, flush=True)
    ok, oks = check_cert(B, D, c, z, s, kap, d, tau, lp, P['lr'], P['b'], P['e'])
    print('lp', float(lp), 'lr', float(P['lr']), 'b', float(P['b']), 'ok', ok, f'{time.time()-t0:.0f}s', flush=True)
    if not ok: print([i for i, o in enumerate(oks) if not o]); return None
    _, Ts, aux = terms(cfg, B, P)
    tot = sum(Ts)
    Ne = (N + G + cfg['Gp'] + D + 2) // EL + 1
    be = band_eps_float(T)
    print('terms', [f"{float(t):.2e}" for t in Ts], 'settle', f"{float(tot):.2e}", f'Ne {Ne} bandEps {be:.2e} -> {Ne*be:.2e}')
    return cfg, T, fam, B, P, Ts

if __name__ == "__main__":
    beta, D, delta, K, N = float(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    make(beta, D, delta, K, N)
