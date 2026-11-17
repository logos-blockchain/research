import sys, numpy as np
from rv import *
K, PHI = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (64800, 1291)
print("thresholds", [round(thr(PHI, K, d), 4) for d in (0, 6, 15)])
S = Sim(14, 10)
t, ep, x = S.t, S.ep, S.x
def rep(name, build, lo, hi):
    D, r = S.run(build)
    print(f"{name}\n   D[{lo}..{hi+1}] " + " ".join(f"{v:.4f}" for v in D[lo:hi+2]) + f"  minD {D[lo:hi+2].min():.4f} true max rate/f {(-np.expm1(LN/D[lo:hi+2].min()))/f:.3f}")
    for nm, d in (("wins", 0), ("b6", 6), ("b15", 15)):
        st = S.stats(S.wait(r, d, PHI, K), K, lo, hi)
        print(f"   {nm:5s} late {100*st['share']:5.1f}%  longest {st['longest_d']:6.2f} d  mean-late {st['mean_late_h']:5.2f} h  max {st['max_h']:5.2f} h  extra {st['extra_min']:6.1f} min")
    for nm, d in (("b6", 6), ("b15", 15)):
        T = S.wait(r, d, 2160, 0); m = (ep >= lo) & (ep < hi) & ~np.isnan(T)
        print(f"   depth {nm}: {T[m].min()/3600:.2f} to {T[m].max()/3600:.2f} h")
for a, an in ((0.1, "tenth"), (0.2, "fifth"), (0.3, "30%"), (1/3, "third")):
    print("=====", an)
    rep("S1", 1-a*(t >= 3*E+P), 3, 8)
    rep("S1b", 1-a*(t >= 3*E), 3, 8)
    rep("S2", 1-a*(x >= 6), 3, 11)
    rep("S3", 1-a*(ep % 2 == 1), 3, 11)
    rep("S5", 1-a*(x < 6), 3, 11)
print("===== leaving")
for xx in (0.3, 0.5):
    for lab, t0 in (("start", 3*E), ("mid", 3*E+3*U), ("end", 3*E+P)):
        rep(f"L {xx} {lab}", 1-xx*(t >= t0), 3, 8)
for xx in (0.48,):
    for lab, t1 in (("start", 7*E), ("endwin", 6*E+P)):
        rep(f"R {xx} {lab}", 1-xx*((t >= 3*E) & (t < t1)), 3, 10)
