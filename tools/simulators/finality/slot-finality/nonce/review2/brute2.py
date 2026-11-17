# Pooled test, windows with 2^8 <= G and all feasible forks <= 14 wins: brute-force mean vs formula, with standard errors.
import sys, math, numpy as np
sys.path.insert(0, "..")
from model import rates
from d2_fallback import SUB
from brute import window, forks, formula, brute, WCAP
rng = np.random.default_rng(11)
for alpha, delta in ((0.30, 10), (1/3, 15)):
    a, h = rates(alpha)
    dif1, difi, tot = [], [], []
    for s in range(6000):
        adv, canon, z = window(777 + s, a, h, delta, SUB + 2000, 6000)
        fk, nsub = forks(adv, canon, z)
        if not fk or max(w for _, w, _ in fk) > WCAP or any(nsub - d < 1 for d, _, _ in fk): continue
        g, g2 = formula(fk, nsub)
        if g < 256: continue
        _, g2i = formula(fk, nsub, True)
        b = np.array([brute(fk, nsub, rng) for _ in range(300)])
        dif1.append((b.mean() - g2, b.std() / math.sqrt(len(b)))); difi.append(b.mean() - g2i); tot.append((g2, g2i, b.mean()))
    d = np.array(dif1); t = np.array(tot)
    se = math.sqrt((d[:, 1] ** 2).sum()) / len(d)
    print(f"alpha {alpha:.3f} delta {delta}: {len(d)} windows; mean G2 {t[:,0].mean():.3f}, mean G2 with 1/(n+i) {t[:,1].mean():.3f}, brute {t[:,2].mean():.3f} +- {se:.3f}; "
          f"z-scores per window (brute - G2)/se: max {np.max(d[:,0]/d[:,1]):.2f}, share > 2: {np.mean(d[:,0]/d[:,1] > 2):.3f}")
