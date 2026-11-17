# Independent re-simulation of the compounding policy (review 4). Plain numpy, geometric gaps for
# the honest chain, exact big-integer tail table, isf-based max-of-n or brute force.
import math, sys
import numpy as np
from scipy import stats
from multiprocessing import Pool

F = 1 / 30
WMAX = 400
def table():
    T = np.full((WMAX + 1, WMAX + 2), -np.inf)
    for w in range(WMAX + 1):
        acc = 0
        for j in range(w, -1, -1):
            acc += math.comb(w, j)
            T[w, j] = math.log2(acc)
    return T
T = table()

def one_G(rng, a, h, delta, near, s_win, k):
    """log2 G for one cut-off, with k coalition wins placed uniformly in the last s_win slots."""
    # honest chain: first block at Geom-1, then gaps delta + Geom
    m = int(near * h) + 200
    gaps = rng.geometric(h, m) + delta
    gaps[0] -= delta + 1
    pos = np.cumsum(gaps)
    pos = pos[pos < near]
    nout = rng.binomial(near - s_win, a)
    advp = np.concatenate([rng.choice(near - s_win, nout, replace=False),
                           near - s_win + rng.choice(s_win, k, replace=False)])
    advp.sort()
    if len(pos) == 0:
        return 0.0
    p = pos[::-1]                                    # d = 0, 1, ...
    W = len(advp) - np.searchsorted(advp, p, side="right")   # wins strictly after the block's slot
    W = np.minimum(W, WMAX)
    d = np.arange(len(p))
    ok = (W >= d + 1)
    ok[0] = W[0] >= 1
    if not ok.any():
        return 0.0
    v = T[W[ok], np.minimum(d[ok] + 1, WMAX + 1)]
    if ok[0]:
        v[0] = math.log2(2.0 ** W[0] - 1.0)
    mx = max(v.max(), 0.0)
    return mx + math.log2(2.0 ** (0.0 - mx) + np.sum(2.0 ** (v - mx)))

def chains(args):
    seed, nch, epochs, alpha, delta, bits, s_win, near, brute = args
    rng = np.random.default_rng(seed)
    a, h = 1 - (1 - F) ** alpha, 1 - (1 - F) ** (1 - alpha)
    out = np.zeros((epochs, nch))
    for c in range(nch):
        ln = 0.0
        for e in range(epochs):
            n = 2.0 ** ln
            if brute:
                ni = max(1, int(math.floor(n)))      # integer candidates
                k = int(rng.binomial(s_win, a, ni).max())
            else:
                q = -math.expm1(math.log(rng.random()) / n)     # P(max > k) target
                k = int(stats.binom.isf(q, s_win, a))
            ln = min(one_G(rng, a, h, delta, near, s_win, k), bits)
            out[e, c] = ln
    return out

if __name__ == "__main__":
    alpha, delta, bits, s_win, near, brute, nch, epochs = sys.argv[1:9]
    alpha = 1 / 3 if alpha == "third" else float(alpha)
    delta, bits, s_win, near, brute, nch, epochs = int(delta), float(bits), int(s_win), int(near), int(brute), int(nch), int(epochs)
    P = 10
    with Pool(P) as pool:
        o = np.concatenate(pool.map(chains, [(900 + i, nch // P, epochs, alpha, delta, bits, s_win, near, brute) for i in range(P)]), axis=1)
    thr = sys.argv[9:] or ["8"]
    for t in thr:
        t = float(t)
        print(f"alpha {alpha:.4f} delta {delta} bits {bits} S {s_win} near {near} brute {brute} | >= 2^{t:g}: " +
              " ".join(f"{e+1}:{np.mean(o[e] >= t):.4f}" for e in (0, 1, 2, 4, 9, 19, 39) if e < epochs), flush=True)
    print("   mean log2 n: " + " ".join(f"{e+1}:{o[e].mean():.3f}" for e in (0, 4, 19) if e < epochs))
