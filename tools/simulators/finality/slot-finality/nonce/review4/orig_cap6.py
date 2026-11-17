import os, sys, numpy as np
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from compound import run
from today_choices import log2_tail_table
from model import rates
t = log2_tail_table()
for alpha, delta in ((1/3, 10), (0.25, 15)):
    a, h = rates(alpha)
    sf = stats.binom.sf(np.arange(601), 600, a)
    lc = np.log1p(-np.minimum(sf, 1 - 1e-300)); lc[sf <= 0] = 0
    for bits in (6.0, 16.0):
        o = run(20000, 20, a, h, delta, 600, lc, bits, 777, t)
        for thr in (4, 6, 8):
            print(alpha, delta, bits, f">=2^{thr}", " ".join(f"{e+1}:{np.mean(o[e] >= thr):.4f}" for e in (0, 1, 2, 4, 9, 19)))
        print("   mean log2 n", " ".join(f"{e+1}:{o[e].mean():.3f}" for e in (0, 4, 19)))
# n = 1 reproduces Binomial; n = 2^40 quantiles
a, h = rates(1/3)
sf = stats.binom.sf(np.arange(601), 600, a); lc = np.log1p(-np.minimum(sf, 1 - 1e-300)); lc[sf <= 0] = 0
rng = np.random.default_rng(1); u = rng.random(1_000_000)
k1 = np.searchsorted(lc, np.log(u), side="left")
print("n=1 mean/var", k1.mean(), k1.var(), "binomial", 600*a, 600*a*(1-a))
print("n=1 pmf max abs err", np.abs(np.bincount(k1, minlength=40)[:40]/1e6 - stats.binom.pmf(np.arange(40), 600, a)).max())
k40 = np.searchsorted(lc, np.log(u) / 2.0**40, side="left")
print("n=2^40 median", np.median(k40), "exact median: smallest k with cdf^n>=.5 ->", int(stats.binom.isf(-np.expm1(np.log(.5)/2.0**40), 600, a)), "range", k40.min(), k40.max())
print("monotone logcdf:", np.all(np.diff(lc) >= 0), "first zero index", int(np.argmax(lc == 0)), "sf there", sf[np.argmax(lc == 0)], "min positive sf", sf[sf > 0].min())
