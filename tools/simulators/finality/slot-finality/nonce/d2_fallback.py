# What the delayed chained minima (D2) fall back to when the delay gives no protection (broken, or
# outrun so far that every candidate's value is seen at once), beside D1, which falls back to
# today's hash chain.
#
# Without the delay a coalition's choice under D2 is, as today, a fork point and a subset of its
# wins after it. The pre-nonce changes only if the last sub-window's smallest contribution changes.
# Contributions are chained: c(b) = hash(c(parent) || rho(b)), so every chain prefix the coalition
# can build has a fresh uniform value. A prefix of i coalition blocks on a fork that keeps n honest
# blocks of the sub-window holds the sub-window's minimum with chance 1 / (n + i). The number of
# distinct nonces is at most
#   G2 = 1 + (changes of the kept honest minimum) + sum over fork points and prefixes of 1 / (n + 1),
# over the prefixes that some feasible choice extends. This is the expectation given the slots,
# taken from above (1/(n+1) for every prefix); by concavity it bounds phi(u) = E[min(1, u G)] from
# above. A fork that empties the sub-window counts as today's.
# Output: the laws of log2 G (today) and log2 G2 side by side, and the shift between them.
# Usage: python d2_fallback.py > d2_fallback.out
import math

import numpy as np
from numba import njit, prange

from model import rates
from today_choices import log2_tail_table, WMAX, _l2add

SUB = 15552          # the last sub-window, slots (25 sub-windows of the 108 h before the cut-off)


@njit(parallel=True, cache=True)
def sample(n, a, h, delta, near, post, seed, table):
    lg = np.empty(n)
    lg2 = np.empty(n)
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
        nsub = 0
        for i in range(near - SUB, near):
            if canon[i]:
                nsub += 1
        w, d = 0, 0
        g = 0.0                 # log2 of today's count, starting at 1
        g2 = 0.0                # log2 of D2's count, starting at 1
        dmax = 0
        for i in range(near - 1, -1, -1):
            if canon[i]:
                ww = min(w, WMAX)
                if d == 0:
                    v = math.log2(2.0 ** ww - 1.0) if ww >= 1 else -np.inf
                    jm = 1
                else:
                    jm = max(0, d + 1 - z)
                    v = table[ww, jm] if jm <= ww else -np.inf
                g = _l2add(g, v)
                if v > -np.inf:
                    dmax = d
                    keep = nsub - d
                    if keep < 1:
                        g2 = _l2add(g2, v)                     # the fork empties the sub-window
                    else:
                        # prefixes that end at the coalition's t-th win (of ww) with i blocks, and
                        # that some feasible choice extends: i + (ww - t) >= jm
                        nodes = -np.inf
                        for t in range(1, ww + 1):
                            k = max(0, jm - ww + t - 1)
                            if k <= t - 1:
                                nodes = _l2add(nodes, table[t - 1, k])
                        g2 = _l2add(g2, nodes - math.log2(keep + 1.0))
                d += 1
            if adv[i]:
                w += 1
        # the kept honest minimum changes at the j-th dropped block with chance 1 / (nsub - j)
        hsum = 0.0
        for j in range(min(dmax, nsub - 1)):
            hsum += 1.0 / (nsub - j)
        if hsum > 0.0:
            g2 = _l2add(g2, math.log2(hsum))
        lg[s], lg2[s] = g, g2
    return lg, lg2


if __name__ == "__main__":
    table = log2_tail_table()
    n = 2_000_000
    for alpha in (0.30, 1 / 3):
        for delta in (10, 15):
            a, h = rates(alpha)
            lg, lg2 = sample(n, a, h, delta, SUB + 2000, 6000, 777, table)
            who = "30 %" if alpha == 0.30 else "a third"
            print(f"== {who}, worst case {delta} s, {n} cut-offs")
            qs = [0.5, 0.9, 0.99, 0.999, 0.9999]
            q1 = np.quantile(lg, qs)
            q2 = np.quantile(lg2, qs)
            print("   quantile            : " + " / ".join(f"{q:.4g}" for q in qs))
            print("   log2 choices, today : " + " / ".join(f"{v:.1f}" for v in q1))
            print("   log2 choices, D2    : " + " / ".join(f"{v:.1f}" for v in q2))
            print(f"   mean choices, D2 (cut at 2^40): {np.mean(2.0 ** np.minimum(lg2, 40)):.3g}; share of cut-offs with more than 2 choices: today {np.mean(lg > 1):.3f}, D2 {np.mean(lg2 > 1):.3f}")
            big = lg > np.quantile(lg, 0.99)
            diff = lg[big] - lg2[big]
            print(f"   shift log2(today / D2) in the top 1 % of cut-offs: median {np.median(diff):.2f}, 10 % {np.quantile(diff, 0.1):.2f}, 90 % {np.quantile(diff, 0.9):.2f}")
            for x in (8, 16, 24, 32):
                print(f"   P(choices >= 2^{x}): today {np.mean(lg >= x):.3e}   D2 {np.mean(lg2 >= x):.3e}")
