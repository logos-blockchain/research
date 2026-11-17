# Grinding over several epochs with today's hash chain: does a ground nonce in one epoch give the
# coalition more nonces to choose among at the next cut-off?
#
# Policy simulated (one the coalition can run: it uses only its own slots): at each cut-off, of the
# n nonces it holds, it keeps the one that gives it the most wins in the last S slots before the
# NEXT cut-off. It withholds near every cut-off. The number of nonces it then holds at the next
# cut-off is the number of chains complete at that cut-off (fork point d, more than d of its wins
# kept), capped at its budget B. Epoch 0 starts with one nonce (no choice).
# The wins in the last S slots are drawn as the largest of n Binomial(S, a) draws, placed uniformly
# in those slots; every other slot is an ordinary draw.
# Output: by epoch, the share of chains whose coalition holds at least 2^8 nonces, and at least
# half its budget (in bits); the first epoch is the single-epoch law (no compounding).
# Usage: python compound.py > compound.out
import math
import numpy as np
from numba import njit, prange
from scipy import stats

from model import rates
from today_choices import log2_tail_table, WMAX, _l2add

NEAR, POST = 8000, 0


@njit(parallel=True, cache=True)
def run(chains, epochs, a, h, delta, s_win, logcdf, bits, seed, table):
    out = np.zeros((epochs, chains))
    for c in prange(chains):
        np.random.seed(seed + c)
        ln = 0.0                                   # log2 of the nonces held
        adv = np.zeros(NEAR, np.bool_)
        canon = np.zeros(NEAR, np.bool_)
        idx = np.arange(s_win)
        for e in range(epochs):
            # wins in the last s_win slots: the largest of n draws
            n = 2.0 ** ln
            target = math.log(np.random.random()) / n
            k = 0
            while k < s_win and logcdf[k] < target:
                k += 1
            for i in range(NEAR):
                adv[i] = False
            for i in range(NEAR - s_win):
                adv[i] = np.random.random() < a
            for j in range(k):                     # k distinct slots of the window
                r = j + int(np.random.random() * (s_win - j))
                idx[j], idx[r] = idx[r], idx[j]
                adv[NEAR - s_win + idx[j]] = True
            dead = 0
            for i in range(NEAR):
                canon[i] = False
                hon = np.random.random() < h
                if dead > 0:
                    dead -= 1
                elif hon:
                    canon[i] = True
                    dead = delta
            w, d = 0, 0
            g = 0.0
            for i in range(NEAR - 1, -1, -1):
                if canon[i]:
                    ww = min(w, WMAX)
                    if d == 0:
                        v = math.log2(2.0 ** ww - 1.0) if ww >= 1 else -np.inf
                    else:
                        v = table[ww, d + 1] if d + 1 <= ww else -np.inf
                    g = _l2add(g, v)
                    d += 1
                if adv[i]:
                    w += 1
            ln = min(g, bits)
            out[e, c] = ln
    return out


if __name__ == "__main__":
    table = log2_tail_table()
    chains, epochs = 20000, 40
    print("share | delay | budget | window S | epoch: share of chains with >= 2^8 nonces / with >= half the budget's bits")
    for alpha in (0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3):
        a, h = rates(alpha)
        who = "a third" if alpha > 0.33 else f"{int(round(alpha * 100))} %"
        for delta in (10, 15):
            for bits in (16, 24, 40):
                best = None
                for s_win in (600, 1800, 3600):
                    sf = stats.binom.sf(np.arange(s_win + 1), s_win, a)
                    logcdf = np.log1p(-np.minimum(sf, 1 - 1e-300))
                    logcdf[sf <= 0] = 0.0
                    o = run(chains, epochs, a, h, delta, s_win, logcdf, float(bits), 4242, table)
                    score = np.mean(o[-1] >= bits / 2)
                    if best is None or score > best[0]:
                        best = (score, s_win, o)
                _, s_win, o = best
                cells = [f"{e + 1}: {np.mean(o[e] >= 8):.4f} / {np.mean(o[e] >= bits / 2):.4f}" for e in (0, 1, 2, 4, 9, 19, 39)]
                print(f"{who:8s} | {delta:2d} s | 2^{bits} | {s_win:4d} | " + " | ".join(cells), flush=True)
