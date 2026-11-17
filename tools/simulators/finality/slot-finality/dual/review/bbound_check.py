"""Reviewer's recomputation of b_bound.py from the saved wait curves (read only), with nbinom
instead of binom, step 1, plus monotonicity of w and the alternative sum bound."""
import glob, os, math
import numpy as np
from scipy.stats import nbinom
F, k, K = 1/30, 2160, 64800
OUT = os.path.dirname(os.path.abspath(__file__)) + "/../out"
SC = {"deflated_(1.5)": 1.5, "lottery_1.25": 1.25, "lottery_1.925": 1.925, "deflated_(1-0.7)": 1/0.7}
for path in sorted(glob.glob(OUT + "/wait_*.npy")):
    name = os.path.basename(path)[5:-4]
    scale = next((v for s, v in SC.items() if name.endswith(s)), 1.0)
    c = np.load(path)
    mono = bool(np.all(np.diff(c[2000:]) <= 1e-300 + 1e-12*c[2000:-1]))
    inc = int(np.sum(np.diff(c) > 0))
    p = 1-(1-F)**scale
    t0 = np.arange(k+1, K+1)
    # P(T_k < t0) = P(k-th win at slot <= t0-1) = P(NB failures <= t0-1-k)
    e = nbinom.cdf(t0-1-k, k, p)
    w = np.where(t0 <= c.size, c[np.minimum(t0, c.size)-1], 0.0)
    v = w + e
    i = int(np.argmin(v))
    print(f"{name:32s} scale {scale:.3f} size {c.size} mono_tail {mono} (#increases {inc}, first vals {c[0]:.2g} {c[100]:.2g})"
          f"  w(K) {w[-1]:.2e}  best {v[i]:.2e} at {t0[i]/3600:.2f} h   e(K)={e[-1]:.2e}")
