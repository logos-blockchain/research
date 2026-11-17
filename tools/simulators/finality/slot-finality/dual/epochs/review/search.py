import sys, numpy as np, itertools
from rv import *
K, PHI = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (64800, 1291)
S = Sim(16, 120); t, ep, x = S.t, S.ep, S.x
LO, HI = 4, 12
def ev(wh, a, d):
    """wh: fraction of coalition withholding (array 0..1)."""
    D, r = S.run(1-a*wh)
    st = S.stats(S.wait(r, d, PHI, K), K, LO, HI)
    m = (ep >= LO) & (ep < HI)
    cost = wh[m].mean()
    # same-epoch test: within epoch, late blocks exist and building stake 1 > D at some time
    return st, cost, D
def iv(a0, ln): return ((x-a0) % 10) < ln
for a, an, d in ((1/3, "third", 15), (1/3, "third", 6), (0.2, "fifth", 15)):
    print(f"==== {an} blocks {d}  K={K}")
    res = []
    # one interval, fine grid, partial q
    for q in (0.25, 0.5, 0.75, 1.0):
        for a0 in np.arange(0, 10, 0.25):
            for ln in np.arange(0.25, 10.01, 0.25):
                st, c, D = ev(q*iv(a0, ln), a, d)
                res.append((st['extra_min'], c, st['longest_d'], st['share'], st['max_h'], f"one q={q} from {a0} len {ln} D {D[LO]:.3f},{D[LO+1]:.3f}"))
    # two-epoch alternating intervals, 1U grid
    for a1 in range(10):
        for l1 in range(0, 11):
            if l1 == 0 and a1: continue
            for a2 in range(10):
                for l2 in range(0, 11):
                    if l2 == 0 and a2: continue
                    if l1 == 0 and l2 == 0: continue
                    wh = np.where(ep % 2 == 0, iv(a1, l1), iv(a2, l2)).astype(float)
                    st, c, D = ev(wh, a, d)
                    res.append((st['extra_min'], c, st['longest_d'], st['share'], st['max_h'], f"alt A[{a1},+{l1}) B[{a2},+{l2}) D {D[LO]:.3f},{D[LO+1]:.3f}"))
    res = [r for r in res if r[1] > 0]
    print(" top extra:"); [print(f"   extra {r[0]:6.1f} min cost {100*r[1]:4.1f}% eff {r[0]/r[1]:6.1f} longest {r[2]:5.2f} d late {100*r[3]:4.1f}% max {r[4]:.2f} h | {r[5]}") for r in sorted(res, key=lambda r: -r[0])[:6]]
    print(" top efficiency (extra per withheld share), extra>=5min:"); [print(f"   extra {r[0]:6.1f} min cost {100*r[1]:4.1f}% eff {r[0]/r[1]:6.1f} longest {r[2]:5.2f} d late {100*r[3]:4.1f}% | {r[5]}") for r in sorted([r for r in res if r[0] >= 5], key=lambda r: -r[0]/r[1])[:6]]
    print(" top longest:"); [print(f"   extra {r[0]:6.1f} min cost {100*r[1]:4.1f}% longest {r[2]:5.2f} d late {100*r[3]:4.1f}% | {r[5]}") for r in sorted(res, key=lambda r: -r[2])[:6]]
    print(" top late share:"); [print(f"   extra {r[0]:6.1f} min cost {100*r[1]:4.1f}% longest {r[2]:5.2f} d late {100*r[3]:4.1f}% | {r[5]}") for r in sorted(res, key=lambda r: -r[3])[:4]]
