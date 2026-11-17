# Check 1c: brute force of D2's distinct nonces against the author's G2, on the author's own windows.
# 1) rebuild window s of d2_fallback.sample from its seed in plain numpy; confirm lg, lg2 match;
# 2) for windows whose feasible forks all have <= WCAP wins, draw uniform contributions for every
#    chain prefix and every honest block, enumerate every feasible choice, count distinct minima.
import sys, math, numpy as np
sys.path.insert(0, "..")
from model import rates
from today_choices import log2_tail_table
from d2_fallback import sample, SUB
WCAP = 14
table = log2_tail_table()

def window(seed, a, h, delta, near, post):
    np.random.seed(seed)
    r = np.random.random(2 * near)
    adv = r[0::2] < a; hon = r[1::2] < h
    canon = np.zeros(near, bool); dead = 0
    for i in range(near):
        if dead > 0: dead -= 1
        elif hon[i]: canon[i] = True; dead = delta
    r = np.random.random(2 * post)
    lead = z = 0
    for i in range(post):
        if r[2*i] < a: lead += 1
        if dead > 0: dead -= 1
        elif r[2*i+1] < h: lead -= 1; dead = delta
        z = max(z, lead)
    return adv, canon, z

def forks(adv, canon, z):
    """my own reading of the model: list of (d, W_d, jmin) for feasible forks; nsub."""
    near = len(adv)
    nsub = int(canon[near - SUB:].sum())
    cpos = np.nonzero(canon)[0][::-1]
    cum = np.concatenate(([0], np.cumsum(adv[::-1])))      # cum[k] = wins in the last k slots
    out = []
    for d, i in enumerate(cpos):
        w = int(cum[near - 1 - i])                         # wins strictly after slot i
        jm = 1 if d == 0 else max(0, d + 1 - z)
        if jm <= w and not (d == 0 and w == 0):
            out.append((d, w, jm))
    return out, nsub

def formula(fk, nsub, exact_i=False):
    """G2 as the author states it (my own code); exact_i uses 1/(n+i) instead of 1/(n+1)."""
    g2 = 1.0; g = 1.0; dmax = 0
    for d, w, jm in fk:
        S = sum(math.comb(w, j) for j in range(jm, w + 1)) - (1 if d == 0 and jm == 0 else 0)
        g += S; dmax = d; keep = nsub - d
        if keep < 1: g2 += S; continue
        for t in range(1, w + 1):
            for i in range(1, t + 1):
                if i + (w - t) >= jm:
                    g2 += math.comb(t - 1, i - 1) / (keep + (i if exact_i else 1))
    g2 += sum(1.0 / (nsub - j) for j in range(min(dmax, nsub - 1)))
    return g, g2

def brute(fk, nsub, rng):
    hc = rng.random(nsub)
    base = hc.min()
    vals = [np.array([base])]
    for d, w, jm in fk:
        keep = nsub - d
        mk = hc[:keep].min()          # honest blocks in time order; the fork drops the last d
        n = 1 << w
        u = rng.random(n); run = np.empty(n); run[0] = np.inf
        for b in range(w):            # bit b = the b-th win in time; prefix = mask without top bit
            lo = 1 << b
            run[lo:2*lo] = np.minimum(run[0:lo], u[lo:2*lo])
        pc = np.zeros(n, np.int64)
        for b in range(w): pc[1 << b: 2 << b] = pc[0: 1 << b] + 1
        ok = pc >= jm
        vals.append(np.minimum(run[ok], mk))
    return len(np.unique(np.concatenate(vals)))

if __name__ == "__main__":
    rng = np.random.default_rng(7)
    for alpha, delta in ((0.30, 10), (1/3, 15)):
        a, h = rates(alpha)
        near, post, seed, nwin = SUB + 2000, 6000, 777, 6000
        lg, lg2 = sample(nwin, a, h, delta, near, post, seed, table)
        worst = 0.0; worst_g = 0.0; rows = []
        for s in range(nwin):
            adv, canon, z = window(seed + s, a, h, delta, near, post)
            fk, nsub = forks(adv, canon, z)
            g, g2 = formula(fk, nsub) if max([w for _, w, _ in fk], default=0) <= 60 else (None, None)
            if g is not None:
                worst_g = max(worst_g, abs(math.log2(g) - lg[s])); worst = max(worst, abs(math.log2(g2) - lg2[s]))
            if fk and max(w for _, w, _ in fk) <= WCAP and all(nsub - d >= 1 for d, _, _ in fk):
                reps = 40
                bm = np.mean([brute(fk, nsub, rng) for _ in range(reps)])
                _, g2i = formula(fk, nsub, True)
                rows.append((g, g2, g2i, bm))
            elif not fk:
                rows.append((1.0, g2, g2, 1.0))
        r = np.array(rows)
        print(f"alpha {alpha:.3f} delta {delta}: port vs author's sample over {nwin} windows: max |d log2 G| {worst_g:.2e}, max |d log2 G2| {worst:.2e}")
        print(f"  windows brute-forced (all feasible forks <= {WCAP} wins): {len(r)} of {nwin}")
        for lo, hi in ((0, 1), (1, 4), (4, 8), (8, 11), (11, 15)):
            m = (np.log2(r[:, 0]) >= lo) & (np.log2(r[:, 0]) < hi) if lo else (r[:, 0] < 2)
            if m.sum():
                print(f"  log2 G in [{lo},{hi}): {m.sum():5d} windows | mean today {r[m,0].mean():9.1f} | G2 (1/(n+1)) {r[m,1].mean():8.4f} | G2 (1/(n+i)) {r[m,2].mean():8.4f} | brute force {r[m,3].mean():8.4f} | windows with brute > G2 by > 4 s.e.-ish (0.15): {int((r[m,3] > r[m,1] + 0.15).sum())}")
