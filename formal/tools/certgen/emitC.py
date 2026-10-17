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
    cfg, T = res[:2]
    # the family and its tables, by the current rules, for the planned potential
    import emitE
    fam, B, P = emitE.retable(cfg, T, K)
    import emitF
    # the settlement parameters follow their rules at (N1, k1) (`ClosedData.derive`, `emitF.closed_rules`)
    cl = dict(k0=k0, m=M_DIV, N1=5184000, k1=2160, eps=emitF.EPS)
    q_ = emitF.emit_closed(cfg, T, fam, B, P, name, out_dir, cl)
    cl = q_['cl']
    print('closed params', {kk: (str(v) if isinstance(v, Fr) else v) for kk, v in cl.items()})
    consts, Qs, Cs = q_['C'], q_['Qs'], q_['Cs']
    short = {kk: q_[kk] for kk in ('t0', 'qs', 'As', 'qb', 'Ab')}
    for (N, k) in [(5184000, 2160), (31536000, 2160), (5184000, 1000), (5184000, 1500), (5184000, 3000)]:
        s, band = eval_closed(consts, Qs, Cs, cl, cl['G'], N, k)
        print(f'N={N} k={k}: settlement {s:.3e} band {band:.3e} total {s + band:.3e}')
        t = k // M_DIV; f = {kk: float(v) for kk, v in short.items()}
        sh = (N + cl['g'] * t + cl['G'] + 2) * (float(consts['A1']) + f['As'] * f['qs'] ** t) + (N // (300 * k) + 2) * f['Ab'] * f['qb'] ** t
        print(f'   short form {sh:.3e}')
    json.dump(dict(cfg, closed={kk: str(v) for kk, v in cl.items()}, consts={kk: str(v) for kk, v in consts.items()},
                   Q=[str(Q) for Q in Qs]), open(f"cfgC_{name}.json", "w"), indent=1)
