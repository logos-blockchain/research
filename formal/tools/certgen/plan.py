"""Choose certificate parameters for (beta, Delta): minimise lp, then split span/fail/window."""
import sys, json, math, numpy as np
from fractions import Fraction as Fr
from scipy.optimize import minimize, minimize_scalar
sys.path.insert(0, '.')
from eps5 import band, es, lse
from auto import lp_needed
L = math.log10

def opt_par(B, D, p0):
    def f(p):
        c, z, s, k, d = np.exp(p)
        if not (d < 1 and s >= 1 and s + k <= z and c > 1 and k >= 0): return 2.0
        e = es(B, D, c, z, s, d, 1.0, idx=range(17))
        return lp_needed(B, D, c, z, s, k, d, e)
    r = minimize(f, np.log(p0), method='Nelder-Mead', options=dict(maxiter=400, xatol=1e-5, fatol=1e-11))
    return np.exp(r.x), r.fun

def plan(beta, D, k=2160, N=648000, fden=30, p0=(1.1125, 1.4251, 1.0705, 0.1373, 0.4528), target_rel=1e-3):
    B = band(1 / fden, beta)
    par, lp = opt_par(B, D, p0)
    c, z, s, kap, d = par
    e = es(B, D, c, z, s, d, 1.0, idx=range(17))
    stat = 1 + (e[1] - 1) / (1 - e[0]); C = L(e[2] * stat)
    best = None
    Gp = 3000
    for tau in [1.002, 1.005, 1.01, 1.015, 1.02, 1.03, 1.05, 1.08, 1.12, 1.17, 1.25, 1.35, 1.5]:
        e17 = es(B, D, c, z, s, d, tau, idx=[17])[17]
        if not np.isfinite(e17) or e17 > 1e6: continue
        a, bb = L(e17), -L(lp)
        for Lw in range(20000, 200001, 1000):
            J = max(1, round(((Lw + 1) * L(tau) - a + C) / (a + bb)))
            sp = L(N + Gp + 1) + (J + 1) * a - (Lw + 1) * L(tau); fl = L(N + Gp + 1) - J * bb + C
            rw = minimize_scalar(lambda lx: L(N + 1) + Lw * L(1 + (math.exp(lx) - 1) * (1 - B['elo'])) - (k + 1) * lx / math.log(10),
                                 bounds=(1e-4, 3), method='bounded')
            tot = lse([sp, fl, rw.fun])
            if best is None or tot < best[0]: best = (tot, tau, Lw, J, math.exp(rw.x), sp, fl, rw.fun)
    tot = best[0]
    # remaining terms: make each <= target_rel * total
    goal = tot + L(target_rel)
    Gp = math.ceil((L(N + 1) - goal) / -L(1 - B['hlo']))
    r = math.ceil((L(N + 3000) + L(stat) - goal) / L(c))
    G = max(D * 2, math.ceil((L(N + 1) - goal) / -L(1 - (1 - B['hhi']) ** D)) * D + D)
    grow_best = None
    for T in range(5, 80, 1):
        kf = k * fden; grow = 10 * kf - 6 * kf - D - 3 - G; nbD = (grow + D) // (T + D); PT = 1 - (1 - B['hlo']) ** T
        for yy in np.linspace(0.2, 0.99, 80):
            v = nbD * L(1 + (yy - 1) * PT) - (k + r) * L(yy)
            if grow_best is None or v < grow_best[0]: grow_best = (v, T, yy)
    return dict(beta=beta, Delta=D, par=list(par), lp=lp, tot=tot, tau=best[1], Lw=best[2], J=best[3], x=best[4],
                parts=best[5:], G=G, Gp=Gp, r=r, T=grow_best[1], yy=grow_best[2], grow=grow_best[0])

if __name__ == "__main__":
    beta, D = float(sys.argv[1]), int(sys.argv[2])
    p = plan(beta, D)
    print(json.dumps(p))
