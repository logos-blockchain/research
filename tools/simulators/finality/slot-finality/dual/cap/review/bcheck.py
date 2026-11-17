import os
import numpy as np
from scipy.stats import binom
F, k, K = 1/30, 2160, 64800
R = os.path.dirname(os.path.abspath(__file__))
for tag, a in (("third_10_1.5", 1/3), ("30_15", 0.3)):
    c = np.load(f"{R}/curve_{tag}.npy")
    w = np.zeros(K); w[:min(K, c.size)] = c[:K]
    assert np.all(np.diff(c) <= 1e-18), "not monotone"
    p_all = 1 - (1 - F) ** (1/(1-a))
    t0 = np.arange(k, K + 1)
    b = w[t0 - 1] + binom.sf(k - 1, t0 - 1, p_all)
    i = b.argmin()
    print(tag, "w(K)", w[K-1], "bound1", b[i], "at h", t0[i]/3600, "mean h to 2160 slots", k/p_all/3600,
          "P(2160 slots within 18h)", binom.sf(k-1, K-1, p_all))
