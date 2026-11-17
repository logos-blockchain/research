# The chance of each grinding attack, by finality rule, at the same delays (10 s and 15 s) and shares.
# Version 2, after the third review (review3/): the SLOT rows are summed in logarithms (version 1
# read arrays that lose every term below 1e-16), the DEPTH rule counts the target block against the
# coalition, and the stretch starts at an arbitrary slot. Version 1 is kept as attack_rules_v1.*.
#
# Attack 1, undo a final payment (private chain, best of n nonces by the coalition's own wins):
#   SLOT (#532/#533) the target is final K slots later (the floor taken as met, the attacker's best
#                    case). Chance = sum_k P(best of n >= k) [q(k) - q(k - 1)], q(k) = the chance
#                    of success given k wins in the wait: the lead before the target, less the
#                    honest blocks in the wait, plus k, reaches one then or later.
#   DEPTH (master)   the target is final once 2160 blocks of the honest chain follow it; the
#                    coalition withholds, so that takes tau = 2160 gaps. With L1 the best lead of an
#                    earlier fork point once the target counts against it (L1 >= -1), W the wins in
#                    tau and F the most gained afterwards: success iff L1 + W + F >= 2161.
#   FIRST MET        final at the earlier of the two: SLOT's chance, plus the chance that 2160
#                    honest blocks come before K (printed; negligible at these delays only).
#   BOTH             final at the later of the two: at most DEPTH's chance.
# n is fixed, or drawn from the choices complete at a cut-off (today_log2M0_*.npy; shares of 1 to
# 25 % need by_share.py first).
# Attack 3, own a stretch: P(the coalition's wins in a stretch of S slots it chose, best of n,
#   exceed the honest chain's blocks in it) = sum_i P(honest = i) P(best of n >= i + 1).
# Usage: python attack_rules.py > attack_rules.out
import numpy as np
from joblib import Parallel, delayed
from scipy import stats
from scipy.special import logsumexp

from model import Walk, age_pmf, alltime_max_pmf, gap_wins_pmf, rates

BITS = (0, 8, 16, 24, 40, 64)
SHARES = (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3)
K_BLOCKS = 2160
GRID = np.arange(65)
LN10 = np.log(10)


def tag(alpha):
    return f"{int(round(alpha * 100)):02d}"


def label(alpha):
    return "a third" if alpha > 0.33 else f"{int(round(alpha * 100))} %"


def log_best_ge(logsf, bits):
    """log P(best of 2^bits draws >= k) from log P(one draw >= k)."""
    n = 2.0 ** bits
    x = n * np.log1p(-np.exp(np.minimum(logsf, -1e-300)))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(x > -1e-10, np.log(n) + logsf, np.log(-np.expm1(x)))


def weights(alpha, delta):
    total = 4_000_000
    lg = np.load(f"today_log2M0_{tag(alpha)}_{delta}.npy").astype(float)
    lg = np.minimum(lg, np.quantile(lg, 1 - 1e-4 * total / lg.size))
    w = np.zeros(65)
    np.add.at(w, np.clip(np.floor(np.maximum(lg, 0)).astype(int), 0, 64), 1.0 / total)
    w[0] += 1 - lg.size / total
    return w


def slot_chance(alpha, delta, hours=(10, 18)):
    a, _ = rates(alpha)
    small = Walk(alpha, delta)
    g = small.reach()
    big = Walk(alpha, delta, lo=6600, hi=300)
    p = np.zeros((delta + 1, big.n))
    p[:, big.lo - small.lo:big.lo - small.lo + small.n] = small.start_at_cutoff()
    big.a = 0.0
    out, t = {}, 0
    for hh in hours:
        while t < hh * 3600:
            p = big.step(p)
            t += 1
        lead = np.arange(big.n) - big.lo
        live = np.nonzero(p.sum(axis=0) > 0)[0]
        kmax = int(-lead[live].min()) + 2
        ks = np.arange(0, kmax + 1)
        q = np.zeros(ks.size)
        pl = p[:, live]
        for j, k in enumerate(ks):
            x = lead[live] + k
            idx = np.clip(x + small.lo, 0, small.n - 1)
            val = np.where(x >= 1, 1.0, np.where(x + small.lo < 0, 0.0, g[:, idx]))
            q[j] = float((pl * val).sum())
        dq = np.diff(np.concatenate(([0.0], q)))
        ok = dq > 0
        logsf = stats.binom.logsf(ks - 1, t, a)                # P(W >= k)
        res = np.empty(GRID.size)
        for b in GRID:
            res[b] = logsumexp(log_best_ge(logsf, b)[ok] + np.log(dq[ok])) / LN10
        out[hh] = res
    return out


def depth_chance(alpha, delta):
    a, h = rates(alpha)
    w = Walk(alpha, delta)
    g = w.reach()
    step = gap_wins_pmf(alpha, delta)
    l1 = np.convolve(alltime_max_pmf(step)[:400], step[:200])    # index i holds L1 + 1 = i
    tail = g[delta, :w.lo + 1][::-1]                               # P(F >= j), j = 1..
    fut = np.concatenate(([1 - tail[0]], tail[:-1] - tail[1:]))
    u = np.convolve(l1, fut[:600])                                 # index j holds L1 + 1 + F = j
    js = np.arange(u.size)
    logu = np.log(np.maximum(u, 1e-320))
    stepf = 20
    fs = np.arange(0, int(8 * K_BLOCKS / h), stepf)
    ts = K_BLOCKS * delta + K_BLOCKS + fs
    logtau = stats.nbinom.logpmf(fs, K_BLOCKS, h) + np.log(stepf)
    acc = {b: [] for b in GRID}
    for t, lt in zip(ts, logtau):
        if lt < -1500:
            continue
        logsf = stats.binom.logsf(K_BLOCKS + 2 - js - 1, t, a)     # P(W >= 2162 - j)
        for b in GRID:
            acc[b].append(lt + logsumexp(logu + log_best_ge(logsf, b)))
    early = [float(stats.nbinom.cdf(int(hh * 3600) - K_BLOCKS * delta - K_BLOCKS, K_BLOCKS, h)) for hh in (18, 10)]
    return np.array([logsumexp(acc[b]) / LN10 for b in GRID]), early


def stretch(alpha, delta, slots, bits):
    a, h = rates(alpha)
    w = Walk(alpha, delta, lo=slots // (delta + 1) + 20, hi=10)
    w.a = 0.0
    p = np.zeros((delta + 1, w.n))
    for m, pm in enumerate(age_pmf(alpha, delta)):                 # an arbitrary slot: stationary phase
        p[max(delta - m, 0), w.lo] += pm
    for _ in range(slots):
        p = w.step(p)
    hon = p.sum(axis=0)[:w.lo + 1][::-1]                           # P(honest blocks = i)
    i = np.arange(hon.size)
    logsf = stats.binom.logsf(i, slots, a)                         # P(W >= i + 1)
    ok = hon > 0
    res = [float(np.exp(logsumexp(log_best_ge(logsf, b)[ok] + np.log(hon[ok])))) for b in bits]
    return res, float((i * hon).sum()), slots * a


def cell(alpha, delta):
    return alpha, delta, slot_chance(alpha, delta), depth_chance(alpha, delta), \
        [stretch(alpha, delta, s, (0, 3, 8, 16, 24, 40)) for s in (600, 3600, 10800)]


def fmt(v):
    return f"{v:7.1f}" if v > -1000 else " < -1000"


if __name__ == "__main__":
    cells = [(a, d) for a in SHARES for d in (10, 15)]
    res = Parallel(n_jobs=12)(delayed(cell)(a, d) for a, d in cells)
    print("ATTACK 1: undo a final payment. log10 of the chance of one attempt, private chain with the best of n nonces.")
    print("share | delay | rule | no grinding | n = 2^8 | 2^16 | 2^24 | 2^40 | 2^64 | n from the choices complete at a cut-off")
    for alpha, delta, slot, (dep, early), _ in res:
        who = label(alpha)
        w = weights(alpha, delta)
        ok = w > 0
        rows = {"DEPTH, 2,160 blocks": dep, "SLOT, 18 h": slot[18], "SLOT, 10 h": slot[10]}
        for name, lg in rows.items():
            mix = float(logsumexp(np.log(w[ok]) + lg[ok] * LN10) / LN10)
            print(f"{who:8s} | {delta:2d} s | {name:20s} | " + " | ".join(fmt(lg[b]) for b in BITS) + f" | {fmt(mix)}")
        print(f"{who:8s} | {delta:2d} s | chance that 2,160 honest blocks come before 18 h: {early[0]:.2e}; before 10 h: {early[1]:.2e} (coalition withholding)")
    print("\nATTACK 3: own a stretch that starts at an arbitrary slot. Chance that the coalition's wins in it exceed the honest chain's blocks in it.")
    print("share | delay | stretch | honest blocks (mean) | coalition wins (mean) | no grinding | best of 8 | 2^8 | 2^16 | 2^24 | 2^40")
    for alpha, delta, _, _, st in res:
        for span, (r, mh, ma) in zip(("10 min", "1 h", "3 h"), st):
            print(f"{label(alpha):8s} | {delta:2d} s | {span:6s} | {mh:6.1f} | {ma:6.1f} | " + " | ".join(f"{x:9.2e}" for x in r))
    # agreement with the reviewer's independent rows
    import os
    print("\ncheck against review3/slot_fixed_*.npy (largest difference in log10 over all n, rows 10 h and 18 h):")
    for alpha, delta, slot, _, _ in res:
        f = f"review3/slot_fixed_{tag(alpha)}_{delta}.npy"
        if os.path.exists(f):
            r = np.load(f)
            m = np.isfinite(r[0]) & (r[0] > -290) & np.isfinite(r[1]) & (r[1] > -290)
            d10 = np.abs(r[0][m] - slot[10][m]).max() if m.any() else float("nan")
            d18 = np.abs(r[1][m] - slot[18][m]).max() if m.any() else float("nan")
            print(f"   {label(alpha):8s} {delta} s: {d10:.3f}, {d18:.3f}")
