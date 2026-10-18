"""The settlement estimate with a table witness for failed checks, over the span tilt `τ`.

The span term is `(N + 1) · e17^(J+1) / τ^(Lw+1)`: J + 1 phases lasting more than `Lw` slots, with
`e17` the band-worst bound on a phase's `E[τ^length]` (the automaton of index 17: tilt `τ`,
factor 1, terminal 1). The certificates fix `τ` as a searched constant (1.01 at k = 1000), chosen for
the old potential. With the table witness's failed-check numbers (`λ`, the switching factor, the
reach potential at `c_r` with its `lr`, `b`), this recomputes `e17` over a grid of `τ` with the
generator's own routines, reruns the settlement rules (`emitF.spec_rules`) and splits the bound by term.

Usage: python3 span.py NAME DEPTH LAMBDA SWITCH CR LR B [TAU ...]
"""
import sys, os, pickle
from fractions import Fraction as Fr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certgen"))
import certE, emitF, emitE, powq  # noqa: E402
from powq import pow_up, pow_dn  # noqa: E402
from certE import xg_exact, solve_switch, auto_bound  # noqa: E402
from certnum import rup  # noqa: E402


def terms(cfg, B, e, lp, lpi, sw, c, lr, b, tau, e17v):
    ee = list(e); ee[2] = e[2] * sw; ee[17] = e17v
    cf = dict(cfg); cf['c'] = str(c); cf['tau'] = str(tau)
    rl = emitF.spec_rules(cf, B, ee, lr, b, lpi, emitF.EPS)
    D, N, k = cf['Delta'], cf['N'], cf['k']
    Lw, J, x, G, Gp, r, Tg, yy = (rl[v] for v in ['Lw', 'J', 'x', 'G', 'Gp', 'r', 'T', 'yy'])
    nb = (certE.EL - certE.PERIOD - D - 3 - G + D) // (Tg + D); ne = (N + 2) // certE.EL
    d = powq.D_POW; F = 1 + (b - 1) / (1 - lr)
    pt = 1 - (1 - B['hhi']) ** Tg if 1 <= yy else 1 - (1 - B['hlo']) ** Tg
    b1, b5, b7 = 1 - (1 - B['hhi']) ** D, 1 + (x - 1) * (1 - B['elo']), 1 + (yy - 1) * pt
    t = dict(long=(N + Gp + 1) * pow_up(d, b1, G // D), empty=(N + 1) * pow_up(d, 1 - B['hlo'], Gp),
             span=(N + Gp + 1) * pow_up(d, e17v, J + 1) / pow_dn(d, tau, Lw + 1),
             fail=(N + Gp + 1) * pow_up(d, lpi, J) * pow_up(d, lp / lpi, G) * ee[2] * F,
             window=(N + 1) * pow_up(d, b5, Lw) / pow_dn(d, x, k + 1), reach=(N + G + 1) * F / pow_dn(d, c, r + 1),
             growth=ne * pow_up(d, b7, nb) / pow_dn(d, yy, k + r))
    return {kk: float(v) for kk, v in t.items()}, dict(J=J, Lw=Lw, G=G, r=r)


if __name__ == "__main__":
    a = sys.argv[1:]
    name, k = a[0], int(a[1])
    lpi, sw, c, lr, b = (Fr(v) for v in a[2:7])
    taus = [Fr(v) for v in a[7:]] or [Fr(v) for v in ('1.01', '1.015', '1.02', '1.03', '1.04')]
    certE.set_depth(k)
    cfg, T = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certgen", f"res_{name}.pkl"), 'rb'))[:2]
    fam, B, P = emitE.retable(cfg, T, 32)
    dats, e, lr0, b0, lp, lpi0 = emitF.check_all(cfg, T, fam, B, P)
    bands = [m['B'] for m in fam]
    z, s, d = (Fr(cfg[v]) for v in ['z', 's', 'd'])
    for tau in taus:
        x, th, g = xg_exact(17, c, z, s, d, tau)
        V = solve_switch(bands, cfg['Delta'], x, th, g, 13)
        e17v = max(rup(auto_bound(Bk, x, th, g, V), 13) for Bk in bands)
        t, p = terms(cfg, B, e, lp, lpi, sw, c, lr, b, tau, e17v)
        print(f"τ {float(tau):.3f}: e17 {float(e17v):.6f}, total {sum(t.values()):.2e} ({p}); "
              + ", ".join(f"{kk} {v:.1e}" for kk, v in t.items()), flush=True)
