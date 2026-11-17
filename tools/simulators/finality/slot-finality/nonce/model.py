# The epoch nonce study of 2026-11-17: an independent model, written without the finality study's
# code (research repository, tools/simulators/finality). It shares that study's network model only:
#
#   - slots of 1 s; a share alpha of the stake wins a slot with chance a = 1 - (1 - f)^alpha, the honest
#     rest with chance h = 1 - (1 - f)^(1 - alpha), independently per slot;
#   - worst case of DELTA slots: after a block of the honest chain (a "canonical" block), honest wins
#     in the next DELTA slots do not extend the chain; the next canonical block is the first honest
#     win after them. So the gap between canonical blocks is DELTA + Geometric(h) slots.
#   - "lead" of a private branch: the coalition's wins after the block it forks from, less the
#     canonical blocks after that block. The branch can displace the honest chain while lead >= 1.
#
# Exact quantities (dynamic programming, no sampling):
#   survival(T)   P(a branch forked from a canonical block has lead >= 1 at some time >= T slots later)
#   open_after(T) P(some branch forked before the cut-off has lead >= 1 at some time >= T slots after it)
#   backward_max  the law of the largest lead over all fork points, read at the cut-off
# Usage: imported by the other scripts; `python model.py` prints a self-check against sampling.
import math

import numpy as np

F = 1 / 30


def rates(alpha, f=F):
    return 1 - (1 - f) ** alpha, 1 - (1 - f) ** (1 - alpha)


def clock(alpha, delta, f=F):
    """Mean slots between canonical blocks."""
    _, h = rates(alpha, f)
    return delta + 1 / h


def gap_wins_pmf(alpha, delta, f=F, tiny=1e-40):
    """pmf of the coalition's wins in one whole canonical gap (DELTA dead slots, then the slots up
    to and including the next honest win)."""
    a, h = rates(alpha, f)
    # slots before the honest win: each is "coalition win" with chance a; the count of slots is
    # Geometric. Wins among them: geometric with ratio r.
    r = a * (1 - h) / (a * (1 - h) + h)
    n = int(math.ceil(math.log(tiny) / math.log(r)))
    geo = (1 - r) * r ** np.arange(n + 1)
    # the DELTA dead slots and the honest win's own slot: Binomial(DELTA + 1, a)
    k = np.arange(delta + 2)
    binom = np.array([math.comb(delta + 1, int(i)) * a ** i * (1 - a) ** (delta + 1 - i) for i in k])
    return np.convolve(binom, geo)


def alltime_max_pmf(step, tiny=1e-40):
    """pmf of max(0, sup of partial sums) of a walk whose increments are (Y - 1), Y ~ step, with
    negative drift: Lindley's recursion M <- max(0, M + Y - 1) iterated to its fixed point."""
    m = np.zeros(4096)
    m[0] = 1.0
    for _ in range(100000):
        new = np.convolve(m, step)          # index i holds M + Y = i, so M + Y - 1 = i - 1
        nxt = np.zeros_like(m)
        nxt[0] = new[0] + new[1]
        top = min(m.size, new.size - 1)
        nxt[1:top] = new[2:top + 1]
        if np.abs(nxt - m).sum() < 1e-15:
            m = nxt
            break
        m = nxt
    last = int(np.nonzero(m > tiny)[0][-1])
    return m[:last + 1]


def age_pmf(alpha, delta, f=F, tiny=1e-40):
    """pmf of the slots since the last canonical block, read at a fixed slot boundary."""
    _, h = rates(alpha, f)
    n = delta + int(math.ceil(math.log(tiny) / math.log1p(-h))) + 1
    m = np.arange(n)
    p = np.where(m <= delta, 1.0, (1 - h) ** np.maximum(m - delta, 0))
    return p / (delta + 1 / h)


class Walk:
    """The lead of a private branch, slot by slot. State: (phase c, lead x); c > 0 counts the dead
    slots left, c = 0 means an honest win makes a canonical block."""

    def __init__(self, alpha, delta, f=F, lo=700, hi=300):
        self.alpha, self.delta = alpha, delta
        self.a, self.h = rates(alpha, f)
        self.lo, self.hi = lo, hi
        self.n = lo + hi + 1                 # index i holds lead i - lo
        self._g = None

    def step(self, p):
        """One slot. p[c, i]."""
        a, h, d = self.a, self.h, self.delta
        q = np.zeros_like(p)
        up = np.zeros_like(p)                # after the coalition's draw
        up[:, 1:] += a * p[:, :-1]
        up[:, -1] += a * p[:, -1]            # clipped at the top (negligible mass)
        up += (1 - a) * p
        for c in range(1, d + 1):            # dead slots count down
            q[c - 1] += up[c]
        # c = 0: honest win with chance h makes a canonical block
        q[0] += (1 - h) * up[0]
        dst = d
        q[dst, :-1] += h * up[0, 1:]
        q[dst, 0] += h * up[0, 0]            # clipped at the bottom (negligible mass)
        return q

    def reach(self):
        """g[c, i] = P(lead >= 1 at some slot from now on | state)."""
        if self._g is not None:
            return self._g
        a, h, d = self.a, self.h, self.delta
        g = np.zeros((d + 1, self.n))
        one = self.lo + 1
        g[:, one:] = 1.0
        for it in range(200000):
            new = np.zeros_like(g)
            # value after the coalition's draw, given the phase transition
            for c in range(1, d + 1):
                nxt = g[c - 1]
                new[c, :-1] = a * nxt[1:] + (1 - a) * nxt[:-1]
                new[c, -1] = nxt[-1]
            stay, drop = g[0], g[d]
            # c = 0: (win, no honest) -> x+1 ; (win, honest) -> x ; (no win, no honest) -> x ;
            # (no win, honest) -> x-1
            e_stay = np.empty(self.n)
            e_stay[:-1] = a * stay[1:] + (1 - a) * stay[:-1]
            e_stay[-1] = stay[-1]
            e_drop = np.empty(self.n)
            e_drop[1:] = a * drop[1:] + (1 - a) * drop[:-1]
            e_drop[0] = a * drop[0]
            new[0] = (1 - h) * e_stay + h * e_drop
            new[:, one:] = 1.0
            diff = np.abs(new - g).max()
            g = new
            if diff < 1e-17 and it > 1000:
                break
        self._g = g
        return g

    def start_at_block(self):
        p = np.zeros((self.delta + 1, self.n))
        p[self.delta, self.lo] = 1.0
        return p

    def start_at_cutoff(self):
        """Joint law, at the cut-off, of the phase and of the largest lead over all fork points
        before it (0 if no branch leads)."""
        step = gap_wins_pmf(self.alpha, self.delta)
        back = alltime_max_pmf(step)                     # before the last canonical block
        age = age_pmf(self.alpha, self.delta)
        p = np.zeros((self.delta + 1, self.n))
        for m, pm in enumerate(age):
            if pm < 1e-30:
                break
            wins = np.array([math.comb(m, j) * self.a ** j * (1 - self.a) ** (m - j)
                             for j in range(min(m, 80) + 1)])
            lead = np.convolve(wins, back)
            c = max(self.delta - m, 0)
            k = min(lead.size, self.hi)
            p[c, self.lo:self.lo + k] += pm * lead[:k]
        return p

    def curve(self, start, t_list):
        """P(lead >= 1 at some slot >= t) for each t of t_list (increasing), from `start`."""
        g = self.reach()
        p = start.copy()
        out, t = [], 0
        for target in t_list:
            while t < target:
                p = self.step(p)
                t += 1
            out.append(float((p * g).sum()))
        return np.array(out)


def survival(alpha, delta, t_list):
    w = Walk(alpha, delta)
    return w.curve(w.start_at_block(), t_list)


def open_after(alpha, delta, t_list):
    w = Walk(alpha, delta)
    return w.curve(w.start_at_cutoff(), t_list)


def sample_check(alpha, delta, t, n, seed=1):
    """Sampling check of survival(t) and open_after(t), slot by slot, for small t."""
    rng = np.random.default_rng(seed)
    a, h = rates(alpha)
    horizon = t + 6000
    pre = 4000
    surv = np.zeros(n, bool)
    opn = np.zeros(n, bool)
    for s in range(n):
        adv = rng.random(pre + horizon) < a
        hon = rng.random(pre + horizon) < h
        canon = np.zeros(pre + horizon, bool)
        dead = 0
        for i in range(pre + horizon):
            if dead > 0:
                dead -= 1
            elif hon[i]:
                canon[i] = True
                dead = delta
        # survival: fork at the first canonical block at or after slot `pre`
        idx = np.nonzero(canon[pre:pre + 500])[0]
        if idx.size:
            b = pre + idx[0]
            lead = np.cumsum(adv[b + 1:].astype(int) - canon[b + 1:].astype(int))
            surv[s] = lead[t - 1:].max() >= 1 if lead.size >= t else False
        # open: cut-off after slot pre - 1; fork points are canonical blocks before it
        blocks = np.nonzero(canon[:pre])[0]
        wins_after = np.cumsum(adv[:pre][::-1])[::-1]         # wins at slots >= i
        best = 0
        for d, b in enumerate(blocks[::-1][:200]):
            w = wins_after[b + 1] if b + 1 < pre else 0
            best = max(best, w - d)
        fwd = np.cumsum(adv[pre:].astype(int) - canon[pre:].astype(int))
        opn[s] = best + fwd[t - 1:].max() >= 1
    return surv.mean(), opn.mean()


if __name__ == "__main__":
    for alpha in (0.30, 1 / 3):
        for delta in (10, 15):
            ts = [600, 1200, 1800]
            s = survival(alpha, delta, ts)
            o = open_after(alpha, delta, ts)
            print(f"alpha={alpha:.3f} delta={delta}: exact survival {s}, open {o}")
            for t, se, oe in zip(ts[:2], s, o):
                sm, om = sample_check(alpha, delta, t, 4000)
                print(f"   t={t}: sampled survival {sm:.4f} (exact {se:.4f}), open {om:.4f} (exact {oe:.4f})")
