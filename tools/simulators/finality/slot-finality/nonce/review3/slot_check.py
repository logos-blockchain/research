# Review 3, checks 2 and 3: the SLOT rows of attack_rules.out.
# For each cell: (a) the stored attack_today array at rows 39 (10 h) and 71 (18 h);
# (b) the exact n = 1 chance by model.Walk.curve from start_at_cutoff (wide lattice, own code path);
# (c) the best-of-n chance recomputed with P(max = k) in logs (no 1 - 1e-16 cancellation, no 1e-60 column cut);
# (d) the mix over today_log2M0 with (c).
# Run from the parent directory: python review3/slot_check.py
import sys

import numpy as np
from joblib import Parallel, delayed
from scipy import stats
from scipy.special import logsumexp

sys.path.insert(0, ".")

BITS = (0, 8, 16, 24, 40, 64)
SHARES = (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3)


def tag(alpha):
    return f"{int(round(alpha * 100)):02d}"


def weights(alpha, delta):
    total = 4_000_000
    lg = np.load(f"today_log2M0_{tag(alpha)}_{delta}.npy").astype(float)
    assert lg.size == 400_000 and np.all(np.diff(lg) >= 0)
    lg = np.minimum(lg, np.quantile(lg, 1 - 1e-4 * total / lg.size))
    w = np.zeros(65)
    np.add.at(w, np.clip(np.floor(np.maximum(lg, 0)).astype(int), 0, 64), 1.0 / total)
    w[0] += 1 - lg.size / total
    return w


def log_chance(big, small, g, p, t, a, grid):
    """log of the chance for n = 2^b, b in grid. Everything in logs."""
    mean, sd = t * a, (t * a * (1 - a)) ** 0.5
    ks = np.arange(0, int(mean + 60 * sd) + 30)
    lead = np.arange(big.n) - big.lo
    live = np.nonzero(p.sum(axis=0) > 0)[0]
    pl = p[:, live]
    q = np.zeros(ks.size)
    for j, k in enumerate(ks):
        x = lead[live] + k
        idx = np.clip(x + small.lo, 0, small.n - 1)
        val = np.where(x >= 1, 1.0, np.where(x + small.lo < 0, 0.0, g[:, idx]))
        q[j] = float((pl * val).sum())
    logq = np.log(np.maximum(q, 1e-320))
    sf = stats.binom.sf(ks, t, a)
    logF = np.where(sf < 0.5, np.log1p(-sf), stats.binom.logcdf(ks, t, a))
    logpmf = stats.binom.logpmf(ks, t, a)
    logratio = np.minimum(logpmf - logF, 0.0)                 # pmf(k) / F(k)
    out = []
    for b in grid:
        n = 2.0 ** b
        y = n * np.log1p(-np.minimum(np.exp(logratio), 1 - 1e-17))
        with np.errstate(divide="ignore"):
            lg1 = np.where(y > -1e-9, np.log(n) + logratio, np.log(-np.expm1(y)))
        logpm = n * logF + lg1
        out.append(logsumexp(logpm + logq))
    return np.array(out)


def cell(alpha, delta):
    import attack_today as at
    from model import Walk, rates
    at.HOURS_MAX = 18
    a, _ = rates(alpha)
    big, small, g, snaps = at.snapshots(alpha, delta)
    grid = np.arange(65)
    arr = np.load(f"attack_today_{tag(alpha)}_{delta}.npy")
    w = weights(alpha, delta)
    wide = Walk(alpha, delta, lo=2600, hi=300)
    exact = wide.curve(wide.start_at_cutoff(), [36000, 64800])
    lines = []
    for hh, ex in zip((10, 18), exact):
        row = hh * 4 - 1
        t = (row + 1) * 900
        assert t == hh * 3600
        old = np.log10(np.maximum(arr[row], 1e-320))
        new = log_chance(big, small, g, snaps[row], t, a, grid) / np.log(10)
        ok = w > 0
        mix_old = logsumexp(np.log(w[ok]) + old[ok] * np.log(10)) / np.log(10)
        mix_new = logsumexp(np.log(w[ok]) + new[ok] * np.log(10)) / np.log(10)
        lines.append(f"{tag(alpha)} | {delta:2d} | {hh:2d} h | exact n=1 {np.log10(max(ex, 1e-320)):8.2f} | stored: "
                     + " ".join(f"{old[b]:8.2f}" for b in BITS) + f" mix {mix_old:8.2f} | recomputed: "
                     + " ".join(f"{new[b]:8.2f}" for b in BITS) + f" mix {mix_new:8.2f}")
    np.save(f"review3/slot_fixed_{tag(alpha)}_{delta}.npy", np.array([
        log_chance(big, small, g, snaps[39], 36000, a, grid) / np.log(10),
        log_chance(big, small, g, snaps[71], 64800, a, grid) / np.log(10)]))
    return "\n".join(lines)


if __name__ == "__main__":
    cells = [(a, d) for a in SHARES for d in (10, 15)]
    print("share | delay | wait | exact n = 1 (model.Walk.curve) | stored row, log10 at n = 2^0, 8, 16, 24, 40, 64, mix | recomputed in logs, same columns")
    for line in Parallel(n_jobs=12)(delayed(cell)(a, d) for a, d in cells):
        print(line, flush=True)
