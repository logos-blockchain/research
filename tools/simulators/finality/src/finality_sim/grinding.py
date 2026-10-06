"""Phase B6: grinding the epoch nonce (PLAN.md, the research before review).

The nonce of the next epoch is the hash chain ``eta_B = H(eta_parent || rho_LEAD || sl)`` at the last
block before the cut-off slot, ``6 floor(k/f)`` into the epoch (``cryptarchia-v1-protocol.md``,
Epoch Nonce). A coalition that withholds its wins can choose the chain that ends there. It forks
at the honest block ``d`` canonical blocks before the cut-off and keeps any ``j > d`` of the ``W_d``
wins it made after that block, so that its chain displaces the honest one. Every choice ends in a
different nonce, so the coalition picks among

    G = 1 + sum over d of S_d,    S_d = sum over j > d of C(W_d, j),

nonces. An attack that succeeds with probability ``u`` against one schedule succeeds with
probability at most ``phi(u) = E[min(1, u min(G, B))]`` when the coalition evaluates at most ``B``
schedules and picks among them.

Read backwards from the cut-off, the lead ``L_d = W_d - d`` is a random walk. Its first value is the
coalition's wins after the last canonical honest block. Each later step adds the wins before the
next canonical honest block back, and in that block's slot, and subtracts one. A slot holds a
coalition win with probability ``p_a``, independently of the honest blocks. The delay models are
those of ``finality_sim.recovery``:

- random delay: a slot holds a canonical honest block with probability ``g p_h``, the canonical
  growth A1 measured thinning the honest wins;
- worst case of ``delta`` slots: a canonical honest block is followed by ``delta`` slots in which no
  honest win extends the chain, and the next is the first honest win after them.

The cut-off falls at a uniformly random point of the gap between two canonical honest blocks. With
``M = max_d S_d`` and ``x = min(1/u, B)``, the walk gives two bounds exactly:

    E[min(1, u min(M, B))]  <=  phi(u)  <=  min(1, uB) P(M >= x) + u + u sum_d E[S_d; S_d < x].
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from numba import njit, prange
from scipy import stats

from finality_sim.recovery import occupancy

PER_BIT = 16          # grid points per bit, for the thresholds x and for u
TINY = 1e-40          # a walk ends once less probability than this is left
ROUND = 1e-9          # log2 S this close below a threshold counts as reaching it


def walk(f: float, alpha: float, growth: float | None = None,
         delta: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """The pmf of the first lead ``L_0``, and of a later step plus one."""
    if (growth is None) == (delta is None):
        raise ValueError("set exactly one of growth and delta")
    a = occupancy(f, alpha)
    ph = occupancy(f, 1.0 - alpha)
    h, dead = (growth * ph, 0) if growth is not None else (ph, delta)
    r = a * (1.0 - h) / (a * (1.0 - h) + h)         # a coalition win before the honest block
    n = int(math.ceil(math.log(TINY) / math.log(r)))
    geo = (1.0 - r) * r ** np.arange(n + 1)
    step = np.convolve(stats.binom.pmf(np.arange(dead + 2), dead + 1, a), geo)
    # slots m between the last canonical honest block and the cut-off: P(m) = P(gap > m) / E[gap]
    m = np.arange(dead + int(math.ceil(math.log(TINY) / math.log1p(-h))) + 1)
    pm = np.where(m <= dead, 1.0, (1.0 - h) ** (m - dead)) / (dead + 1.0 / h)
    y = np.arange(n + dead + 1)
    first = stats.binom.pmf(y[:, None], m[None, :], a) @ pm
    return first, step


@njit(cache=True)
def _log2_s(depths, cap):
    """log2 S for a lead L = 1..cap at depth d = 0..depths: the sum over i < L of C(L + d, i)."""
    out = np.full((depths + 1, cap + 1), -np.inf)
    for d in range(depths + 1):
        for lead in range(1, cap + 1):
            w = lead + d
            top = (math.lgamma(w + 1) - math.lgamma(lead) - math.lgamma(w - lead + 2)) / math.log(2)
            ratio, total = 1.0, 1.0                  # C(w, i) / C(w, lead - 1), from i = lead - 1 down
            for i in range(lead - 1, 0, -1):
                ratio *= i / (w - i + 1)
                total += ratio
            out[d, lead] = top + math.log2(total)
    return out


@lru_cache(maxsize=4)
def _table(depths: int, cap: int) -> np.ndarray:
    return _log2_s(depths, cap)


@njit(cache=True)
def _absorbed(first, step, tab, x, floor):
    """P(M >= 2^x): the walk stops on reaching a lead whose S is at least 2^x."""
    depths, cap = tab.shape[0] - 1, tab.shape[1] - 1
    n = floor + cap + 1                               # index i holds the lead i - floor
    p = np.zeros(n)
    hit = 0.0
    for y in range(first.size):
        if y >= 1 and (y > cap or tab[0, y] >= x - ROUND):
            hit += first[y]
        else:
            p[y + floor] += first[y]
    for d in range(1, depths + 1):
        q = np.zeros(n)
        for i in range(n):
            if p[i] == 0.0:
                continue
            for z in range(step.size):
                j = i + z - 1
                if j >= n:
                    hit += p[i] * step[z]
                elif j >= 0:
                    q[j] += p[i] * step[z]
        for i in range(floor + 1, n):
            if tab[d, i - floor] >= x - ROUND:
                hit += q[i]
                q[i] = 0.0
        left = 0.0
        for i in range(n):
            left += q[i]
        p = q
        if left < TINY:
            return hit, d
    return hit, depths + 1


@njit(cache=True, parallel=True)
def _max_tail(first, step, tab, xs, floor):
    out = np.zeros(xs.size)
    reach = np.zeros(xs.size, np.int64)
    for k in prange(xs.size):
        out[k], reach[k] = _absorbed(first, step, tab, xs[k], floor)
    return out, reach.max()


@njit(cache=True)
def _union(first, step, tab, xs, floor):
    """sum over d of E[S_d; S_d < 2^x] for each threshold x."""
    depths, cap = tab.shape[0] - 1, tab.shape[1] - 1
    n = floor + cap + 1
    diff = np.zeros(xs.size + 1)
    p = np.zeros(n)
    for y in range(min(first.size, cap + 1)):
        p[y + floor] += first[y]
    for d in range(depths + 1):
        for i in range(floor + 1, n):
            if p[i] > 0.0:
                s = tab[d, i - floor]
                diff[np.searchsorted(xs, s + ROUND, side="right")] += p[i] * 2.0 ** s
        q = np.zeros(n)
        for i in range(n):
            if p[i] == 0.0:
                continue
            for z in range(step.size):
                j = i + z - 1
                if 0 <= j < n:
                    q[j] += p[i] * step[z]
        left = 0.0
        for i in range(n):
            left += q[i]
        p = q
        if left < TINY:
            return np.cumsum(diff)[:xs.size], d
    return np.cumsum(diff)[:xs.size], depths + 1


def tail(f: float, alpha: float, xs: np.ndarray, growth: float | None = None,
         delta: int | None = None, depths: int = 4000, floor: int = 100,
         cap: int = 300) -> np.ndarray:
    """``P(M >= 2^x)`` for each x in xs.

    The walk is dropped once it trails by ``floor`` blocks, and a lead above ``cap`` counts as
    reaching every threshold. A walk that has not ended within ``depths`` blocks raises.
    """
    first, step = walk(f, alpha, growth, delta)
    out, reach = _max_tail(first, step, _table(depths, cap), np.asarray(xs, float), floor)
    if reach > depths:
        raise ValueError("the walk outlasted the depths tabulated")
    return out


def bounds(f: float, alpha: float, growth: float | None = None, delta: int | None = None,
           budget_bits: int = 64, depths: int = 4000, floor: int = 100, cap: int = 300,
           per_bit: int = PER_BIT) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Lower and upper bounds on ``phi(u)`` at ``u = 2^-t``, for t on a grid of ``1/per_bit`` bit up
    to ``budget_bits + 60``, and ``P(G > 1)``. The walk is truncated as in ``tail``."""
    xs = np.arange(budget_bits * per_bit + 1) / per_bit
    tail_x = tail(f, alpha, xs, growth, delta, depths, floor, cap)
    first, step = walk(f, alpha, growth, delta)
    below, reach = _union(first, step, _table(depths, cap), xs, floor)
    if reach > depths:
        raise ValueError("the walk outlasted the depths tabulated")
    x = 2.0 ** xs
    # the integral of P(M >= y) over 0 <= y <= x_k, from below: P(M >= y) >= P(M >= x_{k+1}) on a step
    area = np.concatenate(([tail_x[0]], tail_x[0] + np.cumsum(np.diff(x) * tail_x[1:])))
    ts = np.arange((budget_bits + 60) * per_bit + 1) / per_bit
    u = 2.0 ** -ts
    k = np.minimum(np.arange(ts.size), xs.size - 1)   # x = min(1/u, B)
    lower = np.maximum(u, u * area[k])
    upper = np.minimum(1.0, u * x[-1]) * tail_x[k] + u + u * below[k]
    upper = np.minimum(upper, np.minimum(1.0, u * x[-1]))
    return ts, lower, upper, float(tail_x[0])


def factors(ts: np.ndarray, lower: np.ndarray, upper: np.ndarray, eps: float) -> tuple[float, float]:
    """The factor ``eps / u`` by which the chance against one schedule must fall so that ``phi``
    stays at ``eps``, bounded from below and from above."""
    u = 2.0 ** -ts
    lo = eps / u[np.nonzero(lower > eps)[0][-1]]       # the smallest u the lower bound already fails
    hi = eps / u[np.nonzero(upper <= eps)[0][0]]       # the largest u the upper bound holds
    return max(1.0, lo), hi                            # phi(u) >= u


def lead_pmf(f: float, alpha: float, depth: int, growth: float | None = None,
             delta: int | None = None) -> tuple[np.ndarray, int]:
    """The pmf of ``L_depth`` and the lead of its first entry."""
    first, step = walk(f, alpha, growth, delta)
    p = first
    for _ in range(depth):
        p = np.convolve(p, step)
    return p, -depth


@njit(cache=True)
def _simulate(n_samples, h, a, dead, n_slots, d_out, seed):
    np.random.seed(seed)
    leads = np.full((n_samples, d_out + 1), -(1 << 40), np.int64)
    log2g = np.empty(n_samples)
    log2m = np.full(n_samples, -np.inf)
    canon = np.zeros(n_slots, np.bool_)
    adv = np.zeros(n_slots, np.bool_)
    for s in range(n_samples):
        last = 0                                    # a canonical honest block at slot 0
        for t in range(1, n_slots):
            canon[t] = np.random.random() < h and t - last > dead
            if canon[t]:
                last = t
            adv[t] = np.random.random() < a
        total, best, wins, d = 1.0, 0.0, 0, 0
        for t in range(n_slots - 1, 0, -1):          # the cut-off is slot n_slots
            if canon[t]:
                if d <= d_out:
                    leads[s, d] = wins - d
                if wins > d:
                    c, term = 1.0, 1.0
                    for j in range(1, wins - d):        # C(wins, i) for i < wins - d
                        c *= (wins - j + 1) / j
                        term += c
                    total += term
                    best = max(best, term)
                d += 1
            if adv[t]:
                wins += 1
        log2g[s] = math.log2(total)
        if best > 0.0:
            log2m[s] = math.log2(best)
    return leads, log2g, log2m


def simulate(f: float, alpha: float, n_samples: int, n_slots: int, d_out: int, seed: int,
             growth: float | None = None,
             delta: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Slot by slot, forwards from a canonical honest block: ``L_d`` for ``d <= d_out``, and
    ``log2 G`` and ``log2 M`` over the forks the ``n_slots`` slots before the cut-off hold."""
    if (growth is None) == (delta is None):
        raise ValueError("set exactly one of growth and delta")
    ph = occupancy(f, 1.0 - alpha)
    h, dead = (growth * ph, 0) if growth is not None else (ph, delta)
    return _simulate(n_samples, h, occupancy(f, alpha), dead, n_slots, d_out, seed)
