# Review 3, check 1: depth_chance() of attack_rules.py.
# Part A: scaled-down depth, slot-by-slot Monte Carlo of the attack against the formula.
# Part B: full depth, the script's formula against the corrected count of honest blocks, and the grid step.
# Run from the parent directory: python review3/depth_check.py A|B
import sys

import numpy as np
from joblib import Parallel, delayed
from numba import njit
from scipy import stats
from scipy.special import logsumexp

sys.path.insert(0, ".")
from model import Walk, alltime_max_pmf, gap_wins_pmf, rates  # noqa: E402

BITS = (0, 8, 16, 24, 40, 64)
SHARES = (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3)


def tag(alpha):
    return f"{int(round(alpha * 100)):02d}"


def weights(alpha, delta):
    total = 4_000_000
    lg = np.load(f"today_log2M0_{tag(alpha)}_{delta}.npy").astype(float)
    lg = np.minimum(lg, np.quantile(lg, 1 - 1e-4 * total / lg.size))
    w = np.zeros(65)
    np.add.at(w, np.clip(np.floor(np.maximum(lg, 0)).astype(int), 0, 64), 1.0 / total)
    w[0] += 1 - lg.size / total
    return w


def formula(alpha, delta, depth, grid, step, variant, span=8.0):
    """log (natural) of the chance for n = 2^b.
    variant 'script': as attack_rules.depth_chance (lead read at a fixed slot, W >= depth - U).
    variant 'block' : the target is a block of the honest chain. L1 = lead of the best fork point before
                      the target, read after the target's slot with the target counted (>= -1).
                      Success: L1 + W - depth + F >= 1.
    """
    a, h = rates(alpha)
    w = Walk(alpha, delta)
    g = w.reach()
    tail = g[delta, :w.lo + 1][::-1]
    fut = np.concatenate(([1 - tail[0]], tail[:-1] - tail[1:]))
    if variant == "script":
        start = w.start_at_cutoff().sum(axis=0)[w.lo:]
        need = depth                                   # P(W >= depth - j), j = start + F
    else:
        gw = gap_wins_pmf(alpha, delta)
        start = np.convolve(alltime_max_pmf(gw), gw)   # index i holds L1 = i - 1
        need = depth + 2                               # L1 + F = j - 1, so W >= depth + 2 - j
    u = np.convolve(start[:400], fut[:600])
    js = np.arange(u.size)
    logu = np.log(np.maximum(u, 1e-320))
    fs = np.arange(0, int(span * depth / h), step)
    ts = depth * delta + depth + fs
    logtau = stats.nbinom.logpmf(fs, depth, h) + np.log(step)
    out = {b: [] for b in grid}
    for t, lt in zip(ts, logtau):
        if lt < -800:
            continue
        logsf = stats.binom.logsf(need - js - 1, t, a)
        for b in grid:
            n = 2.0 ** b
            with np.errstate(divide="ignore"):
                x = n * np.log1p(-np.exp(np.minimum(logsf, -1e-300)))
                lp = np.where(x > -1e-10, np.log(n) + logsf, np.log(-np.expm1(x)))
            out[b].append(lt + logsumexp(logu + lp))
    return {b: logsumexp(v) for b, v in out.items()}


@njit(cache=False)
def simulate(seed, trials, depth, a, h, delta, n, pre_blocks, horizon, window):
    """The attack, slot by slot. Returns successes of: oracle selection (best of n by own wins over
    the realised span), n = 1 (nonce 0 alone), and a selection the coalition can make (most own wins
    in a window fixed in advance)."""
    np.random.seed(seed)
    s_or = 0
    s_one = 0
    s_fix = 0
    wins = np.zeros(n, np.int64)
    sel = np.zeros(n, np.int64)
    for _ in range(trials):
        # history: best lead over fork points, block by block; the target is block number pre_blocks
        m = 0
        dead = 0
        blocks = 0
        lead0 = 0
        while True:
            if np.random.random() < a:
                m += 1
            if dead > 0:
                dead -= 1
            elif np.random.random() < h:
                blocks += 1
                dead = delta
                if blocks == pre_blocks:
                    lead0 = m - 1                      # the target counts against every fork point before it
                    break
                m = max(m - 1, 0)                      # a fork from this block has lead 0
        # the span: until `depth` blocks follow the target
        for i in range(n):
            wins[i] = 0
            sel[i] = 0
        tau = 0
        follow = 0
        s = 0
        while follow < depth or s < window:
            s += 1
            counting = follow < depth
            for i in range(n):
                if np.random.random() < a:
                    if counting:
                        wins[i] += 1
                    if s <= window:
                        sel[i] += 1
            if counting:
                tau = s
                if dead > 0:
                    dead -= 1
                elif np.random.random() < h:
                    follow += 1
                    dead = delta
        best = 0
        pick = 0
        for i in range(n):
            if wins[i] > best:
                best = wins[i]
            if sel[i] > sel[pick]:
                pick = i
        # after the span: one draw, from just after a block
        gain = 0
        top = 0
        dead = delta
        for _s in range(horizon):
            if np.random.random() < a:
                gain += 1
            if dead > 0:
                dead -= 1
            elif np.random.random() < h:
                gain -= 1
                dead = delta
            if gain > top:
                top = gain
        if lead0 + best - depth + top >= 1:
            s_or += 1
        if lead0 + wins[0] - depth + top >= 1:
            s_one += 1
        if lead0 + wins[pick] - depth + top >= 1:
            s_fix += 1
    return s_or, s_one, s_fix


def part_a():
    alpha, delta = 1 / 3, 10
    a, h = rates(alpha)
    print("PART A: scaled depth, a third, 10 s. Monte Carlo of the attack against the formula.")
    for depth in (40, 80):
        window = int(round(depth * (delta + 1 / h)))
        for n, trials in ((1, 4_800_000), (16, 1_200_000)):
            chunk = trials // 12
            res = Parallel(n_jobs=12)(delayed(simulate)(1000 + 17 * i + n + depth, chunk, depth, a, h, delta, n, 60, 5000, window)
                                      for i in range(12))
            tot = np.array(res).sum(axis=0)
            N = chunk * 12
            p = tot / N
            se = np.sqrt(p * (1 - p) / N)
            b = int(np.log2(n))
            f_script = np.exp(formula(alpha, delta, depth, [b], 1, "script", span=30)[b])
            f_block = np.exp(formula(alpha, delta, depth, [b], 1, "block", span=30)[b])
            print(f"depth {depth:3d} | n = {n:2d} | MC oracle best-of-n {p[0]:.3e} +- {se[0]:.1e} | MC nonce 0 alone {p[1]:.3e} +- {se[1]:.1e} | "
                  f"MC pick by wins in a fixed window of {window} slots {p[2]:.3e} +- {se[2]:.1e} | "
                  f"formula as in the script {f_script:.3e} | formula, target a block {f_block:.3e}", flush=True)


def full(alpha, delta):
    grid = list(range(65))
    w = weights(alpha, delta)
    ok = w > 0
    line = []
    for variant in ("script", "block"):
        r = formula(alpha, delta, 2160, grid, 20, variant)
        lg = np.array([r[b] for b in grid]) / np.log(10)
        mix = logsumexp(np.log(w[ok]) + lg[ok] * np.log(10)) / np.log(10)
        line.append(f"{variant}: " + " ".join(f"{lg[b]:8.2f}" for b in BITS) + f" mix {mix:8.2f}")
    return f"{tag(alpha)} | {delta:2d} | " + " | ".join(line)


def part_b():
    print("PART B: full depth 2160. log10 at n = 2^0, 8, 16, 24, 40, 64 and the mix; the script's formula, then the target as a block.")
    cells = [(a, d) for a in SHARES[4:] for d in (10, 15)]
    for line in Parallel(n_jobs=8)(delayed(full)(a, d) for a, d in cells):
        print(line, flush=True)
    for step in (20, 5):
        r = formula(1 / 3, 10, 2160, [0, 64], step, "script")
        print(f"grid step {step:2d}, a third, 10 s, script formula: n = 1 {r[0] / np.log(10):.4f}, n = 2^64 {r[64] / np.log(10):.4f}", flush=True)


if __name__ == "__main__":
    part_a() if sys.argv[1] == "A" else part_b()
