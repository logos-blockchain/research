import numpy as np
from math import exp, lgamma, log
from rv import *
# ---- item 6: one-off ramp for the longest stretch
for K, PHI in ((64800, 1291), (36000, 689)):
    S = Sim(14, 10); t, ep, x = S.t, S.ep, S.x
    for a, an in ((1/3, "third"), (0.3, "30%"), (0.2, "fifth")):
        th = thr(PHI, K, 15)
        b = np.ones(S.n); D = 1.0; lv = []
        b[(ep == 3) & (x >= 6)] = 1-a
        for e in range(4, 9):
            target = max(1-a, min(1.0, th*D*0.999))
            if target/D >= th: target = 1-a   # cannot be late any more; just withhold
            b[(ep == e) & (x < 6)] = target; b[(ep == e) & (x >= 6)] = 1-a
            D = D*(-np.expm1(LN*target/D))/f; lv.append((round(target, 3), round(D, 3)))
        b[ep >= 9] = 1-a
        Dv, r = S.run(b); st = S.stats(S.wait(r, 15, PHI, K), K, 3, 11)
        print(f"K={K} ramp {an} b15: window levels,(next D) {lv[:3]} longest {st['longest_d']:.2f} d  max {st['max_h']:.2f} h mean-late {st['mean_late_h']:.2f}")
        # full withholding from point a0 of the window (coalition copy of 'leaves mid window')
        best = max(((S.stats(S.wait(S.run(1-a*(t >= 3*E+a0*U))[1], 15, PHI, K), K, 3, 9)['longest_d'], a0) for a0 in np.arange(0, 6.01, 0.1)))
        print(f"      withhold for good from {best[1]:.1f} U into a window: longest {best[0]:.2f} d")
# ---- item 7: same epoch late and lottery above f
S = Sim(14, 10); t, ep, x = S.t, S.ep, S.x
for K, PHI in ((64800, 1291), (36000, 689)):
  for a, d, a0, ln in ((1/3, 15, 2.25, 7.75), (1/3, 15, 3, 7), (1/3, 15, 0, 3), (0.2, 15, 4.5, 5.5), (1/3, 6, 5.5, 4.5), (1/3, 6, 5.9, 4.1)):
    wh = ((x-a0) % 10) < ln
    D, r = S.run(1-a*wh); T = S.wait(r, d, PHI, K)
    m = ep == 8; late = (T > K+1e-6) & m
    print(f"K={K} a={a:.3f} blocks {d} withhold [{a0},{a0+ln}) every epoch: D={D[8]:.4f} ratio withholding {(1-a)/D[8]:.3f} (thr {thr(PHI,K,d):.3f}); late {100*late.sum()/m.sum():.1f}% of epoch 8, max wait {np.nanmax(T[m])/3600:.2f} h; "
          f"lottery when building {r[m].max()/f:.3f} f for {100*(~wh[m]).mean():.1f}% of the epoch; epoch-mean win rate {r[m].mean()/f:.3f} f")
# ---- item 8
def short(n, K, p, delta=15):
    s = K-n*delta
    return sum(exp(lgamma(s+1)-lgamma(i+1)-lgamma(s-i+1)+i*log(p)+(s-i)*log(1-p)) for i in range(n))
from fractions import Fraction
def short_exact(n, K, p, delta=15):   # independent: recursive pmf, float128-free check via logs of ratio
    s = K-n*delta; q = 1-p; lp = s*log(q); tot = 0.0; term = lp
    for i in range(n):
        tot += exp(term); term += log(s-i)-log(i+1)+log(p)-log(q)
    return tot
fz = 1/30
for K, n in ((64800, 1291), (36000, 689)):
    for nm, p in (("0.033", 0.033), ("1% high", 1-(1-fz)**(1/1.01)), ("2% high", 1-(1-fz)**(1/1.02)), ("exact f", fz)):
        print(f"K={K} n={n} {nm}: {short_exact(n, K, p):.3e}")
# ---- stochastic lateness at mean-rate 'never late' points
print("P(floor missed at K) by the same binomial formula, building/D = x:")
for K, n in ((64800, 1291), (36000, 689)):
    for d in (6, 15):
        print(f" K={K} d={d}: " + "  ".join(f"x={xx:.3f}: {short_exact(n, K, -np.expm1(LN*xx), d):.2e}" for xx in (1, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 2/3)))
