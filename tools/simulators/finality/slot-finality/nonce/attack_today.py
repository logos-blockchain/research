# Today's nonce, read from the attack's side. The finality study bounds grinding by a union bound:
# with n nonces to choose among, an attack's chance is at most n times its chance against one.
# That bound lets the coalition choose on everything a nonce decides. It cannot: the lottery is
# private, so a nonce shows the coalition only its own winning slots, not the honest ones.
# This script plays one concrete attack and so gives a figure from below:
#   - at the cut-off the coalition evaluates n nonces, and keeps the one that gives it the most wins
#     in the T slots after a target slot fixed in advance;
#   - it runs the private-chain attack on that target: it builds on the best fork point before the
#     target and succeeds if its branch leads by one at some slot at least T after the target.
# Chance = sum_k P(best of n Binomial(T, a) = k) * P(lead before - honest blocks in T + k + later >= 1).
# n is fixed (2^b), or drawn from the law of the choices at a cut-off, capped at 2^b: either the
# largest set of choices complete at the cut-off (today_log2M0_*.npy; the coalition holds these for
# certain, so this column is an attack it can run), or every choice counted with hindsight of its
# lead after the cut-off (today_log2G_*.npy; it cannot always take these). Both are sampled, and the
# last 1e-4 of each law is cut to its 99.99 % point, which lowers the figure.
# The wait needed is the least T whose chance is at most 1e-9. With n = 1 this is the plain private
# attack. The study's wait bound covers every attack, so it lies above these figures.
# Usage: python attack_today.py > attack_today.out
import numpy as np
from scipy import stats

from model import Walk, rates

EPS = 1e-9
QUARTER = 900
HOURS_MAX = 48
BITS = (0, 8, 16, 24, 32, 40, 64)
CELLS = [(0.30, 10), (0.30, 15), (1 / 3, 10), (1 / 3, 15)]


def tag(alpha):
    return "30" if alpha == 0.30 else "33"


def snapshots(alpha, delta):
    """At each quarter hour T: the joint law of (lead before the target - honest blocks in T, phase)."""
    small = Walk(alpha, delta)
    g = small.reach()                                 # index i holds lead i - small.lo
    start_small = small.start_at_cutoff()
    big = Walk(alpha, delta, lo=4300, hi=300)
    p = np.zeros((delta + 1, big.n))
    p[:, big.lo - small.lo:big.lo - small.lo + small.n] = start_small
    big.a = 0.0                                       # the coalition's wins in T are added afterwards
    out = []
    for t in range(1, HOURS_MAX * 3600 + 1):
        p = big.step(p)
        if t % QUARTER == 0:
            out.append(p.copy())
    return big, small, g, out


def chance(big, small, g, p, t, a, logn_list):
    """For each log2 n: the attack's chance at wait t with the best of n nonces."""
    # q[k] = P(success | k wins in the window) = sum_{c, x} p[c, x] g[c, x + k]
    mean, sd = t * a, (t * a * (1 - a)) ** 0.5
    ks = np.arange(max(0, int(mean - 12 * sd)), int(mean + 40 * sd) + 1)
    lead = np.arange(big.n) - big.lo
    q = np.zeros(ks.size)
    live = np.nonzero(p.sum(axis=0) > 1e-60)[0]
    for j, k in enumerate(ks):
        x = lead[live] + k                             # lead when the wait ends
        idx = np.clip(x + small.lo, 0, small.n - 1)
        val = np.where(x >= 1, 1.0, np.where(x + small.lo < 0, 0.0, g[:, idx]))
        q[j] = float((p[:, live] * val).sum())
    # log F through the upper tail: logcdf rounds to 0 once the tail is below 1e-16, which would cut
    # the best of n near n = 2^52
    logcdf = np.log1p(-stats.binom.sf(ks, t, a))
    logcdf_prev = np.log1p(-stats.binom.sf(ks - 1, t, a))
    res = []
    for b in logn_list:
        n = 2.0 ** b
        pm = np.exp(n * logcdf) - np.exp(n * logcdf_prev)     # P(max = k)
        res.append(float((pm * q).sum()) + float(1 - np.exp(n * logcdf[-1])))
    return res


if __name__ == "__main__":
    grid = np.arange(0, 65)                             # log2 n grid for the mix over G
    print("the least wait (hours, steps of 0.25) whose chance is at most 1e-9, one concrete attack (from below)")
    print("share | delay | n nonces evaluated | n fixed at 2^b (hypothetical: n nonces in hand) | n = 1 + the largest set of choices complete at the cut-off, capped (an attack that can be run) | n = all choices counted with hindsight of the lead after the cut-off, capped (not always reachable)")
    for alpha, delta in CELLS:
        a, _ = rates(alpha)
        big, small, g, snaps = snapshots(alpha, delta)
        total = 4_000_000
        ws = []
        for kind in ("M0", "G"):
            lg = np.load(f"today_log2{kind}_{tag(alpha)}_{delta}.npy").astype(float)   # top 10 % of 4e6 samples, sorted
            cut = np.quantile(lg, 1 - 1e-4 * total / lg.size)
            lg = np.minimum(lg, cut)
            # weights of floor(log2 n) over the grid; the 90 % below the saved part count as n = 1
            w = np.zeros(grid.size)
            fl = np.clip(np.floor(np.maximum(lg, 0)).astype(int), 0, 64)
            np.add.at(w, fl, 1.0 / total)
            w[0] += 1 - lg.size / total
            ws.append(w)
        w0, w = ws
        mixed0 = {b: None for b in BITS}
        fixed = {b: None for b in BITS}
        mixed = {b: None for b in BITS}
        rows = []
        for i, p in enumerate(snaps):
            t = (i + 1) * QUARTER
            c = np.array(chance(big, small, g, p, t, a, grid))
            rows.append(c)
            for b in BITS:
                if fixed[b] is None and c[b] <= EPS:
                    fixed[b] = t / 3600
                cm = float((w * c[np.minimum(grid, b)]).sum())
                if mixed[b] is None and cm <= EPS:
                    mixed[b] = t / 3600
                cm0 = float((w0 * c[np.minimum(grid, b)]).sum())
                if mixed0[b] is None and cm0 <= EPS:
                    mixed0[b] = t / 3600
        np.save(f"attack_today_{tag(alpha)}_{delta}.npy", np.array(rows))
        who = "30 %" if alpha == 0.30 else "a third"
        for b in BITS:
            f = "> 48" if fixed[b] is None else f"{fixed[b]:.2f}"
            m = "> 48" if mixed[b] is None else f"{mixed[b]:.2f}"
            m0 = "> 48" if mixed0[b] is None else f"{mixed0[b]:.2f}"
            print(f"{who:8s} | {delta:2d} s | 2^{b:<2d} | {f:>6s} | {m0:>6s} | {m:>6s}", flush=True)
