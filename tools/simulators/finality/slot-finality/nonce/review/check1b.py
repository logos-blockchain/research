import numpy as np, check1
from check1 import one, rates
def fwd(alpha, delta, T, thr=1, H=150000, LO=1100, HI=120):
    a, h = rates(alpha); n = LO+HI+1
    p = np.zeros((delta+1, n)); p[delta, LO] = 1.0
    for t in range(T): p = one(p, a, h, delta, LO, False)
    k = LO+thr
    hit = p[:, k:].sum(); p[:, k:] = 0
    for t in range(H):
        p = one(p, a, h, delta, LO, False)
        m = p[:, k:].sum(); hit += m; p[:, k:] = 0
        if t > 5000 and m < 1e-9*hit: break
    return hit, t
print("30% 10s 12h survival", fwd(0.30, 10, 43200), "table 3.782e-34, study 2.372e-34")
print("30% 10s 9h survival", fwd(0.30, 10, 32400), "table 4.628e-26, study 4.639e-26")
print("33 15s 12h survival", fwd(1/3, 15, 43200), "table 3.090e-15")
for d in (10, 15):
    s1 = fwd(1/3, d, 7200)[0]; s0 = fwd(1/3, d, 7200, thr=0)[0]
    print("a third", d, "T=2h lead>=1", s1, "lead>=0", s0, "ratio", s0/s1)
