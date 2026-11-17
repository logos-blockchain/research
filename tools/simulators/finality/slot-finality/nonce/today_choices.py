# Today's nonce (the hash chain read at the cut-off): the number of nonces a coalition can choose
# among at one cut-off, sampled slot by slot. Independent of the finality study's walk; compared
# with its exact tail (finality_sim.grinding.tail) where sampling reaches.
#
# A choice is a fork point (a canonical block d canonical blocks before the cut-off) and a subset of
# the coalition's W_d wins after it, with j wins kept. The fork displaces the honest chain if
# j > d - Z, where Z is the most the coalition's private chain leads after the cut-off.
# At d = 0 (no honest block dropped) any non-empty subset counts.
#   G = 1 + sum_d S_d,  M = max_d S_d,  S_d = sum_{j >= jmin} C(W_d, j)
# Usage: python today_choices.py > today_choices.out
import math
import os
import sys

import numpy as np
from numba import njit, prange

from model import rates

WMAX = 400


def log2_tail_table():
    """t[w, j] = log2 sum_{i >= j} C(w, i)."""
    t = np.full((WMAX + 1, WMAX + 2), -np.inf)
    for w in range(WMAX + 1):
        logs = np.array([math.lgamma(w + 1) - math.lgamma(i + 1) - math.lgamma(w - i + 1) for i in range(w + 1)])
        logs /= math.log(2)
        acc = -np.inf
        for j in range(w, -1, -1):
            m = max(acc, logs[j])
            acc = m + math.log2(2 ** (acc - m) + 2 ** (logs[j] - m))
            t[w, j] = acc
    return t


@njit(cache=True)
def _l2add(x, y):
    if x == -np.inf:
        return y
    if y == -np.inf:
        return x
    m = max(x, y)
    return m + math.log2(2.0 ** (x - m) + 2.0 ** (y - m))


@njit(parallel=True, cache=True)
def sample(n, a, h, delta, near, post, seed, table):
    lg = np.empty(n)      # log2 G, with the lead after the cut-off
    lm = np.empty(n)      # log2 M (-inf if no choice)
    lm0 = np.empty(n)     # log2 M counting only forks complete at the cut-off (Z = 0)
    zs = np.empty(n, np.int64)
    for s in prange(n):
        np.random.seed(seed + s)
        adv = np.zeros(near, np.bool_)
        canon = np.zeros(near, np.bool_)
        dead = 0
        for i in range(near):
            adv[i] = np.random.random() < a
            hon = np.random.random() < h
            if dead > 0:
                dead -= 1
            elif hon:
                canon[i] = True
                dead = delta
        lead, z = 0, 0
        for i in range(post):
            if np.random.random() < a:
                lead += 1
            hon = np.random.random() < h
            if dead > 0:
                dead -= 1
            elif hon:
                lead -= 1
                dead = delta
            if lead > z:
                z = lead
        zs[s] = z
        w, d = 0, 0
        g, m, m0 = 0.0, -np.inf, -np.inf           # log2 of 1
        for i in range(near - 1, -1, -1):
            if canon[i]:
                ww = min(w, WMAX)
                if d == 0:
                    v = math.log2(2.0 ** ww - 1.0) if ww >= 1 else -np.inf
                    v0 = v
                else:
                    jm = max(0, d + 1 - z)
                    v = table[ww, jm] if jm <= ww else -np.inf
                    v0 = table[ww, d + 1] if d + 1 <= ww else -np.inf
                g = _l2add(g, v)
                if v > m:
                    m = v
                if v0 > m0:
                    m0 = v0
                d += 1
            if adv[i]:
                w += 1
        lg[s], lm[s], lm0[s] = g, m, m0
    return lg, lm, lm0, zs


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
    from finality_sim.grinding import tail, bounds   # noqa: E402
    table = log2_tail_table()
    n = 4_000_000
    xs = np.array([0.0, 1, 2, 4, 8, 12, 16, 20, 24, 28, 32])
    for alpha in (0.30, 1 / 3):
        for delta in (10, 15):
            a, h = rates(alpha)
            lg, lm, lm0, zs = sample(n, a, h, delta, 8000, 6000, 12345, table)
            who = "30 %" if alpha == 0.30 else "a third"
            print(f"== {who}, worst case {delta} s, {n} cut-offs sampled")
            print(f"   P(a choice exists at the cut-off, Z = 0): sampled {np.mean(lm0 > -np.inf):.4f}; "
                  f"with the lead after the cut-off: {np.mean(lg > 0):.4f}")
            q = np.quantile(lg, [0.5, 0.9, 0.99, 0.999, 0.9999])
            print("   log2 G quantiles 50 / 90 / 99 / 99.9 / 99.99 %: " + " / ".join(f"{v:.1f}" for v in q))
            print(f"   mean Z {zs.mean():.3f}, P(Z >= 1) {np.mean(zs >= 1):.4f}, max Z {zs.max()}")
            st = tail(1 / 30, alpha, xs, None, delta, 4000, 100, 300)
            print("   x | P(M >= 2^x), Z = 0: sampled | study's exact | P(G >= 2^x) with Z: sampled")
            for x, t in zip(xs, np.atleast_1d(st)):
                sm = np.mean(lm0 >= x - 1e-9)
                sg = np.mean(lg >= x - 1e-9) if x > 0 else np.mean(lg > 0)
                print(f"   {x:4.0f} | {sm:10.3e} | {t:10.3e} | {sg:10.3e}")
            # phi(u) = E[min(1, u min(G, B))] at B = 2^64, against the study's bounds
            ts, lower, upper, _ = bounds(1 / 30, alpha, None, delta, 64, 4000, 100)
            print("   t | phi(2^-t) sampled with G | study lower | study upper")
            for t in (4, 8, 12, 16, 20):
                u = 2.0 ** -t
                ph = np.mean(np.minimum(1.0, u * 2.0 ** np.minimum(lg, 64)))
                k = int(np.argmin(np.abs(ts - t)))
                print(f"   {t:3d} | {ph:10.3e} | {lower[k]:10.3e} | {upper[k]:10.3e}")
            np.save(f"today_log2G_{'30' if alpha == 0.30 else '33'}_{delta}.npy", np.sort(lg)[-400_000:].astype(np.float32))
            # 1 + M at Z = 0, in log2: the choices complete at the cut-off
            n0 = np.log2(1.0 + 2.0 ** np.minimum(lm0, 300.0))
            np.save(f"today_log2M0_{'30' if alpha == 0.30 else '33'}_{delta}.npy", np.sort(n0)[-400_000:].astype(np.float32))
