"""Independent re-implementation. Rates piecewise constant on a grid of dt seconds; cumulative
counts piecewise linear; finality time by exact linear interpolation (no quantization)."""
import numpy as np
from math import log
f, U = 1/30, 64800
E, P = 10*U, 6*U
LN = log(1-f)

def thr(phi, K, d):
    g = phi/K; r = g/(1-d*g); return log(1-r)/LN

class Sim:
    def __init__(s, NE=14, dt=10):
        s.NE, s.dt = NE, dt
        s.n = NE*E//dt
        s.t = np.arange(s.n)*dt          # cell start times
        s.ep = s.t//E
        s.x = (s.t % E)/U               # position in epoch in U
    def run(s, build):
        D = np.ones(s.NE+1); r = np.empty(s.n)
        ce, cp = E//s.dt, P//s.dt
        for e in range(s.NE):
            sl = slice(e*ce, (e+1)*ce)
            r[sl] = -np.expm1(LN*build[sl]/D[e])
            D[e+1] = D[e]*r[e*ce:e*ce+cp].mean()/f
        return D, r
    def wait(s, r, d, need, kmin):
        rho = r/(1+d*r)
        cum = np.concatenate(([0.0], np.cumsum(rho*s.dt)))
        tgt = cum[:-1]+need
        idx = np.searchsorted(cum, tgt, side='left')
        ok = idx < cum.size
        idc = np.minimum(idx, cum.size-1)
        frac = (tgt-cum[idc-1])/np.maximum(cum[idc]-cum[idc-1], 1e-300)
        T = ((idc-1+frac) - np.arange(s.n))*s.dt
        T = np.maximum(T, kmin); T[~ok] = np.nan
        return T
    def stats(s, T, K, lo, hi, eps=1e-6):
        m = (s.ep >= lo) & (s.ep < hi) & ~np.isnan(T)
        tt = T[m]; late = tt > K+eps
        # longest run
        z = np.concatenate(([0], late.astype(int), [0])); dz = np.diff(z)
        st = np.where(dz == 1)[0]; en = np.where(dz == -1)[0]
        longest = (en-st).max()*s.dt if st.size else 0
        return dict(share=late.mean(), longest_d=longest/86400, max_h=tt.max()/3600,
                    mean_late_h=tt[late].mean()/3600 if late.any() else K/3600,
                    extra_min=(tt.mean()-K)/60, total_extra_h=(tt-K).sum()*s.dt/3600/3600)
