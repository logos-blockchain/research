# Review 3, check 5: stretch() of attack_rules.py.
# (a) the script's own function; (b) the same sum with P(max = k) in logs; (c) as (b) with the stretch
# starting at a stationary slot instead of at a block; (d) Monte Carlo for three cells.
# Run from the parent directory: python review3/stretch_check.py
import sys

import numpy as np
from joblib import Parallel, delayed
from numba import njit
from scipy import stats
from scipy.special import logsumexp

sys.path.insert(0, ".")
import attack_rules as ar  # noqa: E402
from model import Walk, age_pmf, rates  # noqa: E402

BITS = (0, 3, 8, 16, 24, 40)


def honest_law(alpha, delta, slots, stationary):
    w = Walk(alpha, delta, lo=400, hi=10)
    w.a = 0.0
    if stationary:
        p = np.zeros((delta + 1, w.n))
        for m, pm in enumerate(age_pmf(alpha, delta)):
            p[max(delta - m, 0), w.lo] += pm
        p /= p.sum()
    else:
        p = w.start_at_block()
    for _ in range(slots):
        p = w.step(p)
    return p.sum(axis=0)[:w.lo + 1][::-1]


def stretch_logs(alpha, delta, slots, bits, stationary):
    a, _ = rates(alpha)
    hon = honest_law(alpha, delta, slots, stationary)
    cdf_h = np.cumsum(hon)
    ks = np.arange(1, min(slots, hon.size) + 1)
    logwin = np.log(np.maximum(cdf_h[ks - 1], 1e-320))
    sf = stats.binom.sf(ks, slots, a)
    logF = np.where(sf < 0.5, np.log1p(-sf), stats.binom.logcdf(ks, slots, a))
    logratio = np.minimum(stats.binom.logpmf(ks, slots, a) - logF, 0.0)
    res = []
    for b in bits:
        n = 2.0 ** b
        with np.errstate(divide="ignore"):
            y = n * np.log1p(-np.minimum(np.exp(logratio), 1 - 1e-17))
            lg1 = np.where(y > -1e-9, np.log(n) + logratio, np.log(-np.expm1(y)))
        res.append(float(np.exp(logsumexp(n * logF + lg1 + logwin))))
    return res


@njit
def mc(seed, trials, slots, a, h, delta, n, burn):
    np.random.seed(seed)
    s_stat = 0
    s_block = 0
    for _ in range(trials):
        dead = 0
        for _s in range(burn):                     # reach a stationary slot
            if dead > 0:
                dead -= 1
            elif np.random.random() < h:
                dead = delta
        hs = 0
        for _s in range(slots):
            if dead > 0:
                dead -= 1
            elif np.random.random() < h:
                hs += 1
                dead = delta
        hb = 0
        dead = delta                               # the stretch starts just after a block
        for _s in range(slots):
            if dead > 0:
                dead -= 1
            elif np.random.random() < h:
                hb += 1
                dead = delta
        best = 0
        for _i in range(n):
            w = 0
            for _s in range(slots):
                if np.random.random() < a:
                    w += 1
            if w > best:
                best = w
        if best >= hs + 1:
            s_stat += 1
        if best >= hb + 1:
            s_block += 1
    return s_stat, s_block


def row(alpha, delta, span, s):
    old = ar.stretch(alpha, delta, s, BITS)[0]
    new = stretch_logs(alpha, delta, s, BITS, False)
    sta = stretch_logs(alpha, delta, s, BITS, True)
    return (f"{ar.label(alpha):8s} | {delta:2d} s | {span:6s} | script: " + " ".join(f"{v:9.2e}" for v in old)
            + " | in logs: " + " ".join(f"{v:9.2e}" for v in new) + " | stationary start: " + " ".join(f"{v:9.2e}" for v in sta))


if __name__ == "__main__":
    alpha, delta, s = 1 / 3, 10, 600
    a, h = rates(alpha)
    print("Monte Carlo, a third, 10 s, 10 min")
    for n, trials in ((1, 2_400_000), (8, 1_200_000), (256, 240_000)):
        chunk = trials // 12
        tot = np.array(Parallel(n_jobs=12)(delayed(mc)(77 + i + n, chunk, s, a, h, delta, n, 800) for i in range(12))).sum(axis=0)
        p = tot / (chunk * 12)
        se = np.sqrt(p * (1 - p) / (chunk * 12))
        b = int(np.log2(n))
        print(f"n = {n:3d} | MC stationary start {p[0]:.4f} +- {se[0]:.4f} | MC start at a block {p[1]:.4f} +- {se[1]:.4f} | "
              f"script {ar.stretch(alpha, delta, s, [b])[0][0]:.4f} | stationary formula {stretch_logs(alpha, delta, s, [b], True)[0]:.4f}", flush=True)
    print("\nAll cells, columns n = 2^0, 3, 8, 16, 24, 40")
    jobs = [(al, d, span, sl) for al, d in ar.CELLS for span, sl in (("10 min", 600), ("1 h", 3600), ("3 h", 10800))]
    for line in Parallel(n_jobs=12)(delayed(row)(*j) for j in jobs):
        print(line, flush=True)
