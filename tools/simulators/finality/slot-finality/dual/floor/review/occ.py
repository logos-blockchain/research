"""Upper end of the cost side: every lottery win of the building stake counts as an occupied slot (uncles referenced, no delay loss)."""
from scipy.stats import binom
f = 1/30; K = 64800; H = 3600
p_of = lambda s: 1 - (1 - f) ** s
def bis(fn, lo, hi):
    for _ in range(60):
        m = (lo + hi) / 2
        if fn(m): lo = m
        else: hi = m
    return lo
for n in (1019, 1440, 1500):
    r = [bis(lambda a: binom.cdf(n - 1, K, p_of(1 - a)) <= e, 0, 1) for e in (1e-9, 1e-3, .5)]
    # time for n occupied slots, a third withholding: least t with P(Bin(t,p)>=n) >= q
    p = p_of(2/3); q = []
    for qq in (.5, 1 - 1e-9):
        lo, hi = 0, 400000
        while lo < hi:
            m = (lo + hi) // 2
            ok = binom.sf(n - 1, m, p) >= qq if qq < .9 else binom.cdf(n - 1, m, p) <= 1 - qq
            if ok: hi = m
            else: lo = m + 1
        q.append(round(max(K, lo) / H, 2))
    print(n, "missing stake 1e-9/1e-3/half: %.1f%% %.1f%% %.1f%%" % tuple(100 * x for x in r), "third withholds median/latest h", q,
          "mean occupied in K, third withholds: %.0f" % (p * K))
