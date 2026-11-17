# attack_today with the max-of-n law computed from the survival function (log1p(-sf)) instead of binom.logcdf
import sys, numpy as np
from scipy import stats
sys.path.insert(0, ".")
import attack_today as A
from model import rates
A.HOURS_MAX = 24
def chance2(big, small, g, p, t, a, logn_list):
    mean, sd = t*a, (t*a*(1-a))**0.5
    ks = np.arange(max(0, int(mean-12*sd)), int(mean+40*sd)+1)
    lead = np.arange(big.n)-big.lo
    q = np.zeros(ks.size)
    live = np.nonzero(p.sum(axis=0) > 1e-60)[0]
    for j, k in enumerate(ks):
        x = lead[live]+k
        idx = np.clip(x+small.lo, 0, small.n-1)
        val = np.where(x >= 1, 1.0, np.where(x+small.lo < 0, 0.0, g[:, idx]))
        q[j] = float((p[:, live]*val).sum())
    def lc(k):
        sf = stats.binom.sf(k, t, a); c = stats.binom.logcdf(k, t, a)
        return np.where(sf < 1e-3, np.log1p(-sf), c)
    l1, l0 = lc(ks), lc(ks-1)
    return [float(((np.exp(2.0**b*l1)-np.exp(2.0**b*l0))*q).sum()) for b in logn_list]
grid = np.arange(0, 65)
for alpha, delta in A.CELLS:
    a, _ = rates(alpha)
    big, small, g, snaps = A.snapshots(alpha, delta)
    lg = np.load(f"today_log2G_{A.tag(alpha)}_{delta}.npy").astype(float); total = 4_000_000
    lg = np.minimum(lg, np.quantile(lg, 1-1e-4*total/lg.size))
    w = np.zeros(grid.size); fl = np.clip(np.floor(np.maximum(lg, 0)).astype(int), 0, 64)
    np.add.at(w, fl, 1.0/total); w[0] += 1-lg.size/total
    res = {}
    for name, fn in (("orig", A.chance), ("fixed", chance2)):
        fixed = {b: None for b in A.BITS}; mixed = {b: None for b in A.BITS}
        for i, p in enumerate(snaps):
            t = (i+1)*A.QUARTER
            c = np.array(fn(big, small, g, p, t, a, grid))
            for b in A.BITS:
                if fixed[b] is None and c[b] <= 1e-9: fixed[b] = t/3600
                cm = float((w*c[np.minimum(grid, b)]).sum())
                if mixed[b] is None and cm <= 1e-9: mixed[b] = t/3600
        res[name] = (fixed, mixed)
    for b in A.BITS:
        print(f"{alpha:.3f} {delta} 2^{b}: fixed orig {res['orig'][0][b]} fixed corrected {res['fixed'][0][b]} | mix orig {res['orig'][1][b]} corrected {res['fixed'][1][b]}", flush=True)
