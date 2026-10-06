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

The cut-off falls at a point of the gap between two canonical honest blocks chosen in proportion to
the gap's length. With ``M = max_d S_d`` and ``x = min(1/u, B)``, the walk gives two bounds exactly:

    E[min(1, u min(M, B))]  <=  phi(u)  <=  min(1, uB) P(M >= x) + u + u sum_d E[S_d; S_d < x].

**After the cut-off.** The nonce is final only once the chain past the cut-off is. A coalition that
keeps winning after the cut-off can complete a fork that holds no more than ``d`` of its wins: it
needs ``j + Z > d``, where ``Z`` is the most its private chain ever leads the public one after the
cut-off. ``Z`` is the walk run forwards, independent of the history before the cut-off
(``post_cutoff``). Counting the coalition's later wins as earlier ones only adds choices, so the
upper bound runs the walk from ``L_0 + Z``; the lower bound counts the choices complete at the
cut-off. Orphaned honest blocks as fork points, and slots the coalition wins twice, are not
counted.

**Two epochs.** An attack whose schedule spans two epochs meets two nonces, ground at two cut-offs
with independent choices ``G`` and ``G'``. It succeeds with probability at most
``phi_2(u) = E[min(1, u min(G, B) min(G', B))] = E[phi(u min(G', B))]`` (``pair_bounds``). ``phi`` is
concave with ``phi(0) = 0``, so ``phi_2(u) <= phi(u) + sum_d E[phi(u min(S'_d, B))]``, with each
``phi`` at most the upper bound at the next larger ``u``. From below, ``G >= max(1, M)`` in both
epochs.
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
def _climb(step, z, floor):
    """P(the forward walk ever reaches a lead of z): V_1 = Y_1, V_(k+1) = V_k + Y_(k+1) - 1."""
    n = floor + z
    p = np.zeros(n)
    hit = 0.0
    for y in range(step.size):
        if y >= z:
            hit += step[y]
        else:
            p[y + floor] += step[y]
    while True:
        q = np.zeros(n)
        for i in range(n):
            if p[i] == 0.0:
                continue
            for y in range(step.size):
                j = i + y - 1
                if j >= n:
                    hit += p[i] * step[y]
                elif j >= 0:
                    q[j] += p[i] * step[y]
        left = 0.0
        for i in range(n):
            left += q[i]
        p = q
        if left < TINY:
            return hit


def post_cutoff(f: float, alpha: float, growth: float | None = None, delta: int | None = None,
                floor: int = 200) -> np.ndarray:
    """The pmf of ``Z``, the most the coalition's private chain leads the public one after the
    cut-off: the lead just before each later canonical honest block, the first gap taken whole."""
    _, step = walk(f, alpha, growth, delta)
    ge = [1.0]
    while ge[-1] > TINY:
        ge.append(_climb(step, len(ge), floor))
    ge = np.array(ge + [0.0])
    return ge[:-1] - ge[1:]


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


@njit(cache=True)
def _union_mass(first, step, tab, xs, floor):
    """The sum over d of P(S_d >= 1) by bin: bin k holds 2^xs[k-1] < S_d <= 2^xs[k], and the last
    bin also every S_d above it."""
    depths, cap = tab.shape[0] - 1, tab.shape[1] - 1
    n = floor + cap + 1
    hist = np.zeros(xs.size)
    p = np.zeros(n)
    for y in range(first.size):
        if y > cap:
            hist[-1] += first[y]
        else:
            p[y + floor] += first[y]
    for d in range(depths + 1):
        for i in range(floor + 1, n):
            if p[i] > 0.0:
                k = np.searchsorted(xs, tab[d, i - floor] - ROUND)
                hist[min(k, xs.size - 1)] += p[i]
        q = np.zeros(n)
        for i in range(n):
            if p[i] == 0.0:
                continue
            for z in range(step.size):
                j = i + z - 1
                if j >= n:
                    hist[-1] += p[i] * step[z]
                elif j >= 0:
                    q[j] += p[i] * step[z]
        left = 0.0
        for i in range(n):
            left += q[i]
        p = q
        if left < TINY:
            return hist, d
    return hist, depths + 1


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


def _bounds(f, alpha, growth, delta, budget_bits, depths, floor, cap, per_bit, after_cutoff, extra_bits):
    xs = np.arange(budget_bits * per_bit + 1) / per_bit
    first, step = walk(f, alpha, growth, delta)
    tab = _table(depths, cap)
    tail_lo, reach = _max_tail(first, step, tab, xs, floor)
    first_up = np.convolve(first, post_cutoff(f, alpha, growth, delta)) if after_cutoff else first
    tail_up, reach_t = _max_tail(first_up, step, tab, xs, floor)
    below, reach_u = _union(first_up, step, tab, xs, floor)
    if max(reach, reach_t, reach_u) > depths:
        raise ValueError("the walk outlasted the depths tabulated")
    x = 2.0 ** xs
    # the integral of P(M >= y) over 0 <= y <= x_k, from below: P(M >= y) >= P(M >= x_{k+1}) on a step
    area = np.concatenate(([tail_lo[0]], tail_lo[0] + np.cumsum(np.diff(x) * tail_lo[1:])))
    ts = np.arange((budget_bits + extra_bits) * per_bit + 1) / per_bit
    u = 2.0 ** -ts
    k = np.minimum(np.arange(ts.size), xs.size - 1)   # x = min(1/u, B)
    lower = np.maximum(u, u * area[k])
    upper = np.minimum(1.0, u * x[-1]) * tail_up[k] + u + u * below[k]
    upper = np.minimum(upper, np.minimum(1.0, u * x[-1]))
    return ts, lower, upper, tail_lo, first_up, step, tab, xs


def bounds(f: float, alpha: float, growth: float | None = None, delta: int | None = None,
           budget_bits: int = 64, depths: int = 4000, floor: int = 100, cap: int = 300,
           per_bit: int = PER_BIT,
           after_cutoff: bool = True) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Lower and upper bounds on ``phi(u)`` at ``u = 2^-t``, for t on a grid of ``1/per_bit`` bit up
    to ``budget_bits + 60``, and ``P(G > 1)`` for the choices complete at the cut-off. With
    ``after_cutoff`` the upper bound also counts forks completed after it. The walk is truncated as
    in ``tail``."""
    ts, lower, upper, tail_lo = _bounds(f, alpha, growth, delta, budget_bits, depths, floor, cap,
                                        per_bit, after_cutoff, 60)[:4]
    return ts, lower, upper, float(tail_lo[0])


def pair_bounds(f: float, alpha: float, growth: float | None = None, delta: int | None = None,
                budget_bits: int = 64, depths: int = 4000, floor: int = 100, cap: int = 300,
                per_bit: int = PER_BIT) -> tuple[np.ndarray, ...]:
    """Lower and upper bounds on ``phi(u)``, then on ``phi_2(u)``, at ``u = 2^-t`` for t on a grid of
    ``1/per_bit`` bit up to ``2 budget_bits + 60``: one epoch's nonce, then two independently
    ground ones."""
    ts, lower, upper, tail_lo, first_up, step, tab, xs = _bounds(
        f, alpha, growth, delta, budget_bits, depths, floor, cap, per_bit, True, budget_bits + 60)
    mass, reach = _union_mass(first_up, step, tab, xs, floor)
    if reach > depths:
        raise ValueError("the walk outlasted the depths tabulated")
    n = ts.size

    def at(v, k):                                     # v at u 2^xs[k]; one where that exceeds 1
        return np.concatenate((np.ones(k), v[:n - k]))

    hat = np.minimum.accumulate(upper)                # the least upper bound at any larger u
    upper2 = hat + sum(m * at(hat, k) for k, m in enumerate(mass) if m > 0.0)
    # max(1, M') rounded down to the grid
    m_lo = np.append(-np.diff(tail_lo), tail_lo[-1])
    m_lo[0] += 1.0 - tail_lo[0]
    lower2 = sum(m * at(lower, k) for k, m in enumerate(m_lo) if m > 0.0)
    return ts, lower, upper, lower2, np.minimum(1.0, upper2)


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
def _choices(wins, d, z):
    """S_d with the coalition leading by z after the cut-off: the sum over j >= j_min of
    C(wins, j), j_min = 1 at the last honest block and max(0, d + 1 - z) deeper."""
    j_min = 1 if d == 0 else max(0, d + 1 - z)
    if j_min > wins:
        return 0.0
    c, term = 1.0, 1.0
    for i in range(1, wins - j_min + 1):             # C(wins, i) for i <= wins - j_min
        c *= (wins - i + 1) / i
        term += c
    return term


@njit(cache=True)
def _simulate(n_samples, h, a, dead, n_slots, d_out, seed):
    np.random.seed(seed)
    leads = np.full((n_samples, d_out + 1), -(1 << 40), np.int64)
    log2g = np.empty(n_samples)
    log2gz = np.empty(n_samples)
    log2m = np.full(n_samples, -np.inf)
    zs = np.empty(n_samples, np.int64)
    canon = np.zeros(n_slots, np.bool_)
    adv = np.zeros(n_slots, np.bool_)
    for s in range(n_samples):
        last = 0                                    # a canonical honest block at slot 0
        for t in range(1, n_slots):
            canon[t] = np.random.random() < h and t - last > dead
            if canon[t]:
                last = t
            adv[t] = np.random.random() < a
        # after the cut-off: the most the coalition's private chain ever leads the public one
        lead, z, t = 0, 0, n_slots
        while lead > -60:
            if np.random.random() < a:              # wins count first within a slot
                lead += 1
                z = max(z, lead)
            if np.random.random() < h and t - last > dead:
                last = t
                lead -= 1
            t += 1
        zs[s] = z
        total, total_z, best, wins, d = 1.0, 1.0, 0.0, 0, 0
        for t in range(n_slots - 1, 0, -1):          # the cut-off is slot n_slots
            if canon[t]:
                if d <= d_out:
                    leads[s, d] = wins - d
                term = _choices(wins, d, 0)
                total += term
                best = max(best, term)
                total_z += _choices(wins, d, z)
                d += 1
            if adv[t]:
                wins += 1
        log2g[s] = math.log2(total)
        log2gz[s] = math.log2(total_z)
        if best > 0.0:
            log2m[s] = math.log2(best)
    return leads, log2g, log2m, log2gz, zs


def simulate(f: float, alpha: float, n_samples: int, n_slots: int, d_out: int, seed: int,
             growth: float | None = None,
             delta: int | None = None) -> tuple[np.ndarray, ...]:
    """Slot by slot, forwards from a canonical honest block: ``L_d`` for ``d <= d_out``; ``log2 G``
    and ``log2 M`` over the forks the ``n_slots`` slots before the cut-off hold; ``log2 G`` with the
    forks the coalition completes after the cut-off as well; and ``Z``."""
    if (growth is None) == (delta is None):
        raise ValueError("set exactly one of growth and delta")
    ph = occupancy(f, 1.0 - alpha)
    h, dead = (growth * ph, 0) if growth is not None else (ph, delta)
    return _simulate(n_samples, h, occupancy(f, alpha), dead, n_slots, d_out, seed)
