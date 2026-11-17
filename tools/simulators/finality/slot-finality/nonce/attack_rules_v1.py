# The chance of each grinding attack, by finality rule, at the same delays (10 s and 15 s) and shares.
#
# Attack 1, undo a final payment (private chain, best of n nonces by the coalition's own wins):
#   DEPTH (master)   the target is final once k = 2160 blocks of the honest chain follow it. The
#                    coalition withholds, so that takes tau = 2160 gaps. Success: its branch leads by
#                    one at some slot from tau on.
#                      P = sum_t P(tau = t) sum_j P(U = j) [1 - (1 - sf_t(2160 - j))^n]
#                    U = its lead before the target plus the most it gains after tau; sf_t the upper
#                    tail of Binomial(t, a).
#   SLOT (#532/#533) the target is final K slots later (the floor is met in the attacker's best
#                    case, where every honest win counts as an occupied slot). Chance read from
#                    attack_today_*.npy at T = K.
#   FIRST MET (B)    final at the earlier of the two. While the coalition withholds, 2160 blocks
#                    take longer than K, so the chance is SLOT's, plus the chance that tau < K.
#   BOTH (A)         final at the later of the two: at most DEPTH's chance.
# n is fixed, or drawn from the choices complete at a cut-off (today_log2M0_*.npy).
# Attack 3, own a stretch: the coalition keeps the nonce with the most wins in a stretch of S slots.
#   P(its wins in the stretch exceed the honest chain's blocks in it), by S and n.
# Shares of 1 to 25 % need by_share.py first.
# Usage: python attack_rules.py > attack_rules.out
import numpy as np
from scipy import stats
from scipy.special import logsumexp

from model import Walk, rates

BITS = (0, 8, 16, 24, 40, 64)
SHARES = (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3)
CELLS = [(a, d) for a in SHARES for d in (10, 15)]
K_BLOCKS = 2160


def tag(alpha):
    return f"{int(round(alpha * 100)):02d}"


def label(alpha):
    return "a third" if alpha > 0.33 else f"{int(round(alpha * 100))} %"


def weights(alpha, delta):
    total = 4_000_000
    lg = np.load(f"today_log2M0_{tag(alpha)}_{delta}.npy").astype(float)
    lg = np.minimum(lg, np.quantile(lg, 1 - 1e-4 * total / lg.size))
    w = np.zeros(65)
    np.add.at(w, np.clip(np.floor(np.maximum(lg, 0)).astype(int), 0, 64), 1.0 / total)
    w[0] += 1 - lg.size / total
    return w


def depth_chance(alpha, delta, grid):
    """log10 of the chance against the depth rule for n = 2^b, b in grid; and P(tau < 18 h, 10 h)."""
    a, h = rates(alpha)
    w = Walk(alpha, delta)
    g = w.reach()
    start = w.start_at_cutoff().sum(axis=0)[w.lo:]              # lead before the target, >= 0
    tail = g[delta, :w.lo + 1][::-1]                             # P(F >= j), j = 1.. (index j-1)
    fut = np.concatenate(([1 - tail[0]], tail[:-1] - tail[1:]))  # P(F = j), j = 0..
    u = np.convolve(start[:400], fut[:600])
    js = np.arange(u.size)
    logu = np.log(np.maximum(u, 1e-320))
    step = 20
    fs = np.arange(0, int(8 * K_BLOCKS / h), step)               # failures of the negative binomial
    ts = K_BLOCKS * delta + K_BLOCKS + fs
    logtau = stats.nbinom.logpmf(fs, K_BLOCKS, h) + np.log(step)
    out = {b: [] for b in grid}
    for t, lt in zip(ts, logtau):
        if lt < -800:
            continue
        logsf = stats.binom.logsf(K_BLOCKS - js - 1, t, a)       # P(W >= 2160 - j)
        for b in grid:
            n = 2.0 ** b
            # log(1 - (1 - sf)^n) = log(-expm1(n log1p(-sf)))
            x = n * np.log1p(-np.exp(np.minimum(logsf, -1e-300)))
            lp = np.where(x > -1e-10, np.log(n) + logsf, np.log(-np.expm1(x)))
            out[b].append(lt + logsumexp(logu + lp))
    early = [float(stats.nbinom.cdf(int(hh * 3600) - K_BLOCKS * delta - K_BLOCKS, K_BLOCKS, h)) for hh in (18, 10)]
    return {b: logsumexp(v) / np.log(10) for b, v in out.items()}, early


def stretch(alpha, delta, slots, bits):
    a, h = rates(alpha)
    w = Walk(alpha, delta, lo=400, hi=10)
    real_a, w.a = w.a, 0.0
    p = w.start_at_block()
    for _ in range(slots):
        p = w.step(p)
    hon = p.sum(axis=0)[:w.lo + 1][::-1]                        # P(honest blocks = i)
    cdf_h = np.cumsum(hon)
    ks = np.arange(0, slots + 1)
    sf = stats.binom.sf(ks, slots, real_a)
    res = []
    for b in bits:
        cdf = np.exp(2.0 ** b * np.log1p(-np.minimum(sf, 1 - 1e-16)))
        pm = np.diff(np.concatenate(([0.0], cdf)))
        win = np.where(ks >= 1, cdf_h[np.clip(ks - 1, 0, cdf_h.size - 1)], 0.0)   # honest blocks <= k - 1
        res.append(float((pm * win).sum()))
    mean_h = float((np.arange(hon.size) * hon).sum())
    return res, mean_h, slots * real_a


if __name__ == "__main__":
    grid = list(range(65))
    print("ATTACK 1: undo a final payment. log10 of the chance of one attempt, private chain with the best of n nonces.")
    print("share | delay | rule | no grinding | n = 2^8 | 2^16 | 2^24 | 2^40 | 2^64 | n from the choices complete at a cut-off")
    for alpha, delta in CELLS:
        who = label(alpha)
        w = weights(alpha, delta)
        dep, early = depth_chance(alpha, delta, grid)
        arr = np.load(f"attack_today_{tag(alpha)}_{delta}.npy")          # [quarter hour, log2 n]
        rows = {"DEPTH, 2,160 blocks": np.array([dep[b] for b in grid])}
        for hh in (18, 10):
            rows[f"SLOT, {hh} h"] = np.log10(np.maximum(arr[hh * 4 - 1], 1e-320))
        for name, lg in rows.items():
            ok = w > 0
            mix = float(logsumexp(np.log(w[ok]) + lg[ok] * np.log(10)) / np.log(10))
            fmt = lambda v: f"{v:7.1f}" if v > -300 else " < -300"     # below the floats' reach
            print(f"{who:8s} | {delta:2d} s | {name:20s} | " + " | ".join(fmt(lg[b]) for b in BITS) + f" | {fmt(mix)}")
        print(f"{who:8s} | {delta:2d} s | chance that 2,160 honest blocks come before 18 h: {early[0]:.2e}; before 10 h: {early[1]:.2e} (coalition withholding)")
    print("\nATTACK 3: own a stretch. Chance that the coalition's wins in a stretch it chose exceed the honest chain's blocks in it.")
    print("share | delay | stretch | honest blocks (mean) | coalition wins (mean) | no grinding | best of 8 | 2^8 | 2^16 | 2^24 | 2^40")
    for alpha, delta in CELLS:
        who = label(alpha)
        for span, s in (("10 min", 600), ("1 h", 3600), ("3 h", 10800)):
            res, mh, ma = stretch(alpha, delta, s, (0, 3, 8, 16, 24, 40))
            print(f"{who:8s} | {delta:2d} s | {span:6s} | {mh:6.1f} | {ma:6.1f} | " + " | ".join(f"{r:9.2e}" for r in res))
