# True brute force: draw n full Bernoulli schedules of the window, keep the row with most wins.
import math, sys, numpy as np
from multiprocessing import Pool
import indep
from indep import T, WMAX, F

def G_from(rng, a, h, delta, near, advp):
    m = int(near * h) + 200
    gaps = rng.geometric(h, m) + delta
    gaps[0] -= delta + 1
    pos = np.cumsum(gaps); pos = pos[pos < near]
    if len(pos) == 0: return 0.0
    p = pos[::-1]
    W = np.minimum(len(advp) - np.searchsorted(advp, p, side="right"), WMAX)
    d = np.arange(len(p))
    tot = 1.0
    for dd, w in zip(d, W):
        if dd == 0: tot += 2.0 ** w - 1
        elif w >= dd + 1: tot += sum(math.comb(int(w), j) for j in range(dd + 1, int(w) + 1))
    return math.log2(tot)

def chains(args):
    seed, nch, epochs, alpha, delta, bits, s_win, near = args
    rng = np.random.default_rng(seed)
    a, h = 1 - (1 - F) ** alpha, 1 - (1 - F) ** (1 - alpha)
    out = np.zeros((epochs, nch))
    for c in range(nch):
        ln = 0.0
        for e in range(epochs):
            ni = max(1, int(math.floor(2.0 ** ln)))
            sched = rng.random((ni, near)) < a           # n whole candidate schedules
            best = np.argmax(sched[:, near - s_win:].sum(axis=1))
            advp = np.flatnonzero(sched[best])
            ln = min(G_from(rng, a, h, delta, near, advp), bits)
            out[e, c] = ln
    return out

if __name__ == "__main__":
    for alpha, delta in ((1/3, 10), (0.25, 15)):
        with Pool(10) as pool:
            o = np.concatenate(pool.map(chains, [(5000 + i, 1000, 20, alpha, delta, 6.0, 600, 8000) for i in range(10)]), axis=1)
        for t in (4, 6):
            print(f"FULL brute alpha {alpha:.4f} delta {delta} cap 2^6 | >= 2^{t}: " + " ".join(f"{e+1}:{np.mean(o[e] >= t):.4f}" for e in (0, 1, 2, 4, 9, 19)), flush=True)
        print("   mean log2 n: " + " ".join(f"{e+1}:{o[e].mean():.3f}" for e in (0, 4, 19)))
