"""GENESIS.md, checks of the proofs. Each check supports a proof; none replaces it.

(a) the closed form of N(m) against a slot-by-slot dynamic programme (statement 5.2 (4));
(b) the tails of M_pre and M_post against a Monte Carlo of the process of statement 6.2 (b);
(c) P1(x) against a Monte Carlo of M_pre + Z_x + M+_post computed from slot bits by the definitions
    of statement 6.2, without the reduction of 6.2 (b) (at a short window, where the chance is large);
    beside it, the sum with M_post in place of M+_post against the bound before the correction;
(d) random executions of the Delta-model with a randomised coalition: the inequalities of
    statements 5.1, 5.2 (3), 5.3, 5.4 and the implication of 6.1, checked on every chain;
(e) the step of statement 6.2 (a), at inflated rates: from the same slot bits, the event that 6.1
    gives, A((a, b)) >= N((a + Delta, b - Delta - 2]) for some a <= sigma and b > sigma + x, against
    M_pre + Z_x + M+_post >= 0 (which it must imply) and M_pre + Z_x + M_post >= 0 (which it need not),
    with a and b over the same ranges as the maxima.
Usage: python g06_checks.py > out_06_checks.txt
"""
import math
import random

import numpy as np
from numba import njit

from common_g import Window, log_pmf_greedy, p_of, pmf_greedy_dp


@njit(cache=True)
def _mc_max(n_paths, n_steps, l0, pa, ph, delta, mcap, seed):
    np.random.seed(seed)
    counts = np.zeros(mcap + 1, np.int64)
    for _ in range(n_paths):
        y = 0
        for _i in range(l0):
            if np.random.random() < pa:
                y += 1
        best = y
        dead = 0
        for _s in range(n_steps):
            if np.random.random() < pa:
                y += 1
            if dead == 0:
                if np.random.random() < ph:
                    y -= 1
                    dead = delta
            else:
                np.random.random()
                dead -= 1
            if y > best:
                best = y
        counts[min(best, mcap)] += 1
    return counts


@njit(cache=True)
def _greedy_counts(h, delta):
    """greedy prefix counts: out[v] = picks among h[0:v] (picks need gaps of delta + 1)."""
    out = np.zeros(h.size + 1, np.int64)
    dead = 0
    c = 0
    for i in range(h.size):
        if dead == 0 and h[i]:
            c += 1
            dead = delta
        elif dead > 0:
            dead -= 1
        out[i + 1] = c
    return out


@njit(cache=True)
def _greedy_last(h, delta):
    """(picks of the greedy choice on h with gaps of delta + 1, index of its last pick or -1)."""
    dead = 0
    c = 0
    last = -1
    for i in range(h.size):
        if dead == 0 and h[i]:
            c += 1
            dead = delta
            last = i
        elif dead > 0:
            dead -= 1
    return c, last


@njit(cache=True)
def _mc_p1(n_samples, x, l_side, pa, ph, delta, seed):
    """Samples with M_pre + Z_x + M_post >= 0 and with M_pre + Z_x + M+_post >= 0, from slot bits."""
    np.random.seed(seed)
    hits = 0
    hits_plus = 0
    for _ in range(n_samples):
        # pre: slots sl, sl-1, ... (index 0 is slot sl); M_pre = max_u A_rev(u) - H_rev(u - delta)
        a = np.random.random(l_side) < pa
        h = np.random.random(l_side) < ph
        hr = _greedy_counts(h, delta)
        acc = 0
        mpre = 0
        for u in range(1, l_side + 1):
            acc += a[u - 1]
            v = u - delta
            val = acc - (hr[v] if v > 0 else 0)
            if val > mpre:
                mpre = val
        # window: A over x slots, N over its slots delta+1..x
        aw = np.sum(np.random.random(x) < pa)
        hw = np.random.random(x) < ph
        nw, last = _greedy_last(hw[delta:], delta)
        tau = delta + 1 if last < 0 else min(delta + 1, x - (delta + 1 + last))
        # post: slots e+1, e+2, ...; M_post = max_u A(u) - H(slots delta+1 .. u-delta-1)
        a2 = np.random.random(l_side) < pa
        h2 = np.random.random(l_side) < ph
        hf = _greedy_counts(h2[delta:], delta)
        acc = 0
        mpost = 0
        for u in range(1, l_side + 1):
            acc += a2[u - 1]
            v = u - 2 * delta - 1
            val = acc - (hf[v] if v > 0 else 0)
            if val > mpost:
                mpost = val
        mplus = mpost
        if tau <= delta:
            extra = 1 + np.sum(a2[:delta - tau])
            if extra > mplus:
                mplus = extra
        if mpre + (aw - nw) + mpost >= 0:
            hits += 1
        if mpre + (aw - nw) + mplus >= 0:
            hits_plus += 1
    return hits, hits_plus


@njit(cache=True)
def _mc_step(n_samples, x, side, pa, ph, delta, seed):
    """(e): slots 1..T, T = 2 side + x, sigma = side. Per sample, from the same bits: the event of 6.1,
    max over a in [0, sigma] and b in (sigma + x, T + 1] of A(a+1..b-1) - N(a+delta+1..b-delta-2) >= 0,
    and the sums M_pre + Z_x + M_post and M_pre + Z_x + M+_post with the maxima over the same a and b.
    Returns (events, events with the corrected sum < 0, events with the uncorrected sum < 0,
    samples with the corrected sum >= 0)."""
    np.random.seed(seed)
    T = 2 * side + x
    sigma = side
    A = np.zeros(T + 2, np.int64)
    hb = np.zeros(T + 2, np.bool_)
    cnt = np.zeros(T + 2, np.int64)
    n_event = 0
    bad_new = 0
    bad_old = 0
    n_new = 0
    for _ in range(n_samples):
        for v in range(1, T + 1):
            A[v] = A[v - 1] + (1 if np.random.random() < pa else 0)
            hb[v] = np.random.random() < ph
        best = -(10 ** 9)
        mpre = -(10 ** 9)
        for a in range(0, sigma + 1):
            start = a + delta + 1
            c = 0
            last = -(10 ** 9)
            for v in range(0, T + 1):
                if v >= start and hb[v] and v - last >= delta + 1:
                    c += 1
                    last = v
                cnt[v] = c
            val = (A[sigma] - A[a]) - (cnt[sigma] if sigma >= start else 0)
            if val > mpre:
                mpre = val
            for b in range(sigma + x + 1, T + 2):
                top = b - delta - 2
                v2 = (A[b - 1] - A[a]) - (cnt[top] if top >= start else 0)
                if v2 > best:
                    best = v2
        c = 0
        last = -(10 ** 9)
        lastpick = -1
        for v in range(sigma + delta + 1, sigma + x + 1):
            if hb[v] and v - last >= delta + 1:
                c += 1
                last = v
                lastpick = v
        z = (A[sigma + x] - A[sigma]) - c
        tau = delta + 1 if lastpick < 0 else min(delta + 1, sigma + x - lastpick)
        start = sigma + x + delta + 1
        c = 0
        last = -(10 ** 9)
        for v in range(0, T + 1):
            if v >= start and hb[v] and v - last >= delta + 1:
                c += 1
                last = v
            cnt[v] = c
        mpost = -(10 ** 9)
        for b in range(sigma + x + 1, T + 2):
            top = b - delta - 2
            v2 = (A[b - 1] - A[sigma + x]) - (cnt[top] if top >= start else 0)
            if v2 > mpost:
                mpost = v2
        mplus = mpost
        if tau <= delta:
            extra = 1 + (A[sigma + x + delta - tau] - A[sigma + x])
            if extra > mplus:
                mplus = extra
        if mpre + z + mplus >= 0:
            n_new += 1
        if best >= 0:
            n_event += 1
            if mpre + z + mplus < 0:
                bad_new += 1
            if mpre + z + mpost < 0:
                bad_old += 1
    return n_event, bad_new, bad_old, n_new


def forward_hit(m, l0, pa, ph, delta, steps, depth=400):
    """P(max_{v <= steps} Y_v >= m) exactly, by a forward pass with an absorbing level m."""
    from scipy import stats
    P = np.zeros((depth + m, delta + 1))
    off = depth
    absorbed = 0.0
    for y in range(l0 + 1):
        pr = stats.binom.pmf(y, l0, pa)
        if y >= m:
            absorbed += pr
        else:
            P[y + off, 0] += pr
    for _ in range(steps):
        N = np.zeros_like(P)
        c0 = P[:, 0]
        up, both, stay, down = c0 * pa * (1 - ph), c0 * pa * ph, c0 * (1 - pa) * (1 - ph), c0 * (1 - pa) * ph
        N[1:, 0] += up[:-1]
        absorbed += up[-1]
        N[:, delta] += both
        N[:, 0] += stay
        N[:-1, delta] += down[1:]
        for c in range(1, delta + 1):
            x = P[:, c]
            N[1:, c - 1] += x[:-1] * pa
            absorbed += x[-1] * pa
            N[:, c - 1] += x * (1 - pa)
        P = N
    return absorbed


# ------------------------------------------------------------------------------------------------
# (d) random executions
# ------------------------------------------------------------------------------------------------
def h_delta(slots, lo, hi, delta):
    """largest set of honest slots in (lo, hi] with gaps of at least delta + 1."""
    c, last = 0, -10 ** 9
    for t in slots:
        if lo < t <= hi and t - last >= delta + 1:
            c += 1
            last = t
    return c


def run_execution(rng, T, n_nodes, ph, pa, delta):
    # blocks: id -> (parent, slot, honest, length)
    blocks = {0: (None, 0, True, 0)}
    known = [dict() for _ in range(n_nodes)]       # node -> {block id: slot from which known}
    for n in range(n_nodes):
        known[n][0] = 0
    honest_slots, adv_slots = [], []
    adv_blocks = []

    def ancestors(b):
        out = []
        while b is not None:
            out.append(b)
            b = blocks[b][0]
        return out

    def learn(n, b, t):
        for x in ancestors(b):
            if x not in known[n] or known[n][x] > t:
                known[n][x] = t

    next_id = 1
    for t in range(1, T + 1):
        h_win = rng.random() < ph
        a_win = rng.random() < pa
        if a_win:
            adv_slots.append(t)
            # the coalition makes 1-3 blocks at slot t on random existing chains with slot < t
            for _ in range(rng.randint(1, 3)):
                cands = [b for b, v in blocks.items() if v[1] < t]
                if rng.random() < 0.5:
                    par = max(cands, key=lambda b: (blocks[b][3], rng.random()))
                else:
                    par = rng.choice(cands)
                blocks[next_id] = (par, t, False, blocks[par][3] + 1)
                adv_blocks.append(next_id)
                # release to random nodes at random times, or never
                for n in range(n_nodes):
                    if rng.random() < 0.6:
                        learn(n, next_id, t + rng.randint(0, 3 * delta))
                next_id += 1
        if h_win:
            honest_slots.append(t)
            leader = rng.randrange(n_nodes)
            view = [b for b, s0 in known[leader].items() if s0 <= t and blocks[b][1] < t]
            best = max(blocks[b][3] for b in view)
            par = rng.choice([b for b in view if blocks[b][3] == best])
            hid = next_id
            next_id += 1
            blocks[hid] = (par, t, True, blocks[par][3] + 1)
            for n in range(n_nodes):
                learn(n, hid, t if n == leader else t + rng.randint(1, delta + 1))
    return blocks, known, honest_slots, adv_slots


def checks_d(seed, n_exec=150, T=400, n_nodes=4, ph=0.22, pa=0.12, delta=3):
    rng = random.Random(seed)
    n_checks = {"5.1": 0, "5.2 (3)": 0, "5.3": 0, "5.4": 0, "6.1": 0}
    n_fail = dict.fromkeys(n_checks, 0)
    n_dense = 0
    for _ in range(n_exec):
        blocks, known, hs, as_ = run_execution(rng, T, n_nodes, ph, pa, delta)
        hset = set(hs)
        aset = set(as_)
        d = [0] * (T + 2)
        for b, (par, sl, hon, ln) in blocks.items():
            if hon and sl >= 1:
                d[sl] = max(d[sl], ln)
        for t in range(1, T + 2):
            d[t] = max(d[t], d[t - 1])
        A = lambda lo, hi: sum(1 for t in as_ if lo < t < hi)      # noqa: E731 (open interval)
        Ac = lambda lo, hi: sum(1 for t in as_ if lo < t <= hi)    # noqa: E731 (lo, hi]

        def chain(b):
            out = []
            while b is not None:
                out.append(b)
                b = blocks[b][0]
            return out[::-1]

        def prefix_len(ch, e):
            ln = 0
            for b in ch:
                if blocks[b][1] <= e:
                    ln = blocks[b][3]
            return ln
        # 5.1: an honest block at t has length >= d(t - delta - 1) + 1
        for b, (par, sl, hon, ln) in blocks.items():
            if hon and sl >= 1:
                n_checks["5.1"] += 1
                if ln < (d[sl - delta - 1] if sl - delta - 1 >= 0 else 0) + 1:
                    n_fail["5.1"] += 1
        # 5.2 (3): d(t2) - d(t1) >= h_delta(honest slots in (t1 + delta, t2])
        for _k in range(40):
            t1, t2 = sorted(rng.sample(range(0, T + 1), 2))
            n_checks["5.2 (3)"] += 1
            if d[t2] - d[t1] < h_delta(hs, t1 + delta, t2, delta):
                n_fail["5.2 (3)"] += 1
        # honest chains at the end: each node's longest known chain
        ys = []
        for n in range(n_nodes):
            view = [b for b, s0 in known[n].items() if s0 <= T]
            best = max(blocks[b][3] for b in view)
            ys.append(rng.choice([b for b in view if blocks[b][3] == best]))
        tips = list(blocks.keys())
        for x_tip in rng.sample(tips, min(60, len(tips))):
            X = chain(x_tip)
            for e in rng.sample(range(1, T + 1), 6):
                # 5.3: len(X[0:e]) <= d(t_g) + A((t_g, e]), g the last honest block of X[0:e]
                xs = [b for b in X if blocks[b][1] <= e]
                g = max((b for b in xs if blocks[b][2]), key=lambda b: blocks[b][1])
                t_g = blocks[g][1]
                lx = blocks[xs[-1]][3]
                n_checks["5.3"] += 1
                if lx > d[t_g] + Ac(t_g, e):
                    n_fail["5.3"] += 1
                for y_tip in ys:
                    Y = chain(y_tip)
                    after = [b for b in Y if blocks[b][1] > e and blocks[b][2]]
                    if after:
                        b_ = blocks[after[0]][1]
                        dref = d[b_ - delta - 1] if b_ - delta - 1 >= 0 else 0
                    else:
                        b_ = T + 1
                        dref = d[T - delta - 1]
                    ly = prefix_len(Y, e)
                    # 5.4: len(Y[0:e]) >= d(b - delta - 2) - A((e, b)) (uniform form)
                    dref2 = d[b_ - delta - 2] if b_ - delta - 2 >= 0 else 0
                    n_checks["5.4"] += 1
                    if ly < dref2 - A(e, b_):
                        n_fail["5.4"] += 1
                    # 6.1: if X is at least as long as Y up to e, the lottery event holds
                    if lx >= ly:
                        n_dense += 1
                        n_checks["6.1"] += 1
                        if A(t_g, b_) < h_delta(hs, t_g + delta, b_ - delta - 2, delta):
                            n_fail["6.1"] += 1
    return n_checks, n_fail, n_dense


if __name__ == "__main__":
    print("(a) N(m): closed form against the dynamic programme")
    for m, p, dl in ((50, 0.2, 3), (400, 0.05, 10), (1000, 0.0235, 15), (3000, 0.0235, 10)):
        a = np.exp(log_pmf_greedy(m, p, dl))
        b = pmf_greedy_dp(m, p, dl)
        mask = b > 1e-280
        print(f"  m = {m}, p = {p}, Delta = {dl}: largest absolute difference {np.max(np.abs(a - b)):.1e}, "
              f"largest relative difference where the mass exceeds 1e-280 "
              f"{np.max(np.abs(a[mask] / b[mask] - 1)):.1e}")

    print("\n(b) tails of M_pre and M_post: bound of statement 6.2 (c) against a Monte Carlo of 200,000 paths of 30,000 steps")
    for share, dl in ((0.30, 10), (1 / 3, 15)):
        pa, ph = p_of(share), p_of(1 - share)
        w = Window(pa, ph, dl)
        for name, l0, tail in (("M_pre", dl, w.t_pre), ("M_post", 2 * dl + 1, w.t_post)):
            cnt = _mc_max(200_000, 30_000, l0, pa, ph, dl, 60, 7 + l0)
            emp = cnt[::-1].cumsum()[::-1] / cnt.sum()
            print(f"  share {share:.4f}, Delta = {dl}, {name}: " + "; ".join(
                f"m = {m}: bound {tail[m]:.4f}, sampled {emp[m]:.4f} +- {math.sqrt(emp[m] * (1 - emp[m]) / cnt.sum()):.4f}"
                for m in (1, 2, 3, 5, 8)))

    print("\n(b') the same tails: bound of statement 6.2 (c) against an exact forward computation of P(max of the first 40,000 steps >= m), a lower bound")
    pa, ph, dl = p_of(0.30), p_of(0.70), 10
    w = Window(pa, ph, dl)
    for name, l0, tail in (("M_pre", dl, w.t_pre), ("M_post", 2 * dl + 1, w.t_post)):
        print(f"  share 0.3000, Delta = 10, {name}: " + "; ".join(
            f"m = {m}: bound {tail[m]:.12f}, forward {forward_hit(m, l0, pa, ph, dl, 40_000):.12f}"
            for m in (1, 3, 8)))

    print("\n(c) P1(x) against a Monte Carlo from slot bits (400,000 samples, sides of 6,000 slots)")
    for share, dl, x in ((0.30, 10, 1500), (0.30, 10, 3000), (1 / 3, 15, 3000)):
        pa, ph = p_of(share), p_of(1 - share)
        w = Window(pa, ph, dl)
        n = 400_000
        hits, hits_plus = _mc_p1(n, x, 6000, pa, ph, dl, 11 + x)
        q, qp = hits / n, hits_plus / n
        print(f"  share {share:.4f}, Delta = {dl}, x = {x}: P1 = {w.p1(x):.4f}; sampled with M+_post {qp:.4f} +- "
              f"{math.sqrt(qp * (1 - qp) / n):.4f} | before the correction {w.p1(x, corrected=False):.4f}; sampled with M_post "
              f"{q:.4f} +- {math.sqrt(q * (1 - q) / n):.4f}")

    print("\n(d) random executions (Delta = 3, p_h = 0.22, p_a = 0.12, 4 honest nodes, 400 slots, randomised coalition)")
    tot_c, tot_f, dense = {}, {}, 0
    for sd in range(4):
        c, fl, dn = checks_d(1000 + sd)
        for k in c:
            tot_c[k] = tot_c.get(k, 0) + c[k]
            tot_f[k] = tot_f.get(k, 0) + fl[k]
        dense += dn
    for k in tot_c:
        print(f"  statement {k}: {tot_c[k]} checks, {tot_f[k]} violations")
    print(f"  pairs in which the chain X was at least as long as Y up to e: {dense}")

    print("\n(e) the step of 6.2 (a) path by path (Delta = 3, p_h = 0.22, p_a = 0.12, x = 40, a and b within 150 slots "
          "of the window, 100,000 samples)")
    pa, ph, dl, x = 0.12, 0.22, 3, 40
    n = 100_000
    ev, bad_new, bad_old, n_new = _mc_step(n, x, 150, pa, ph, dl, 4242)
    print(f"  samples with the event of 6.1: {ev}; of these, with M_pre + Z_x + M+_post < 0: {bad_new}; "
          f"with M_pre + Z_x + M_post < 0: {bad_old}")
    q = n_new / n
    print(f"  frequency of M_pre + Z_x + M+_post >= 0: {q:.4f} +- {math.sqrt(q * (1 - q) / n):.4f}; "
          f"of the event: {ev / n:.4f}; P1(x) = {Window(pa, ph, dl).p1(x):.4f}")
