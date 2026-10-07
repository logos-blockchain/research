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
(``post_cutoff``). Given ``Z = z``, a fork point ``d >= z`` offers the table's choices at depth
``d - z`` and lead ``L_d + z``, a fork point ``1 <= d < z`` offers ``2^W_d``, and the last honest
block offers ``2^W_0 - 1`` (``_ztable``). Both bounds mix these over ``z`` up to the ``z`` past which
``Z`` lies with probability below ``ZCUT``; the upper bounds count that rest at ``min(1, uB)``. One
walk serves every ``z``: the walks agree before depth ``z``, and from it each reads the table at depth
``d - z`` with its lead raised by ``z`` (``_before``). Under random delay ``Z`` is exact. Under a worst
case of ``delta`` the upper bound takes the first gap after the cut-off whole, and the lower bound
leaves the coalition's wins in it out. Orphaned honest blocks as fork points, and slots the
coalition wins twice, are not counted.

**Two epochs.** An attack whose schedule spans two epochs meets two nonces, ground at two cut-offs
with independent choices ``G`` and ``G'``. It succeeds with probability at most
``phi_2(u) = E[min(1, u min(G, B) min(G', B))] = E[phi(u min(G', B))]`` (``pair_bounds``). ``phi`` is
concave with ``phi(0) = 0``, so ``phi(u (1 + Y)) <= phi(u) (1 + Y)`` and ``phi`` is subadditive. Two
upper bounds follow, and the smaller is taken:

    phi_2(u) <= phi(u) + sum_d E[phi(u min(S'_d, B))],
    phi_2(u) <= phi(uB) P(M' >= x) + phi(u) (1 + sum_d E[S'_d; S'_d < x])    for every x,

each ``phi`` at most the upper bound at the next larger ``u``. From below, ``G >= max(1, M)`` in both
epochs, ``M`` counting the forks completed after the cut-off.
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
ZCUT = 1e-12          # the post-cut-off lead is followed until less probability than this is left


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
def _ladder(step, floor):
    """The first height above 0 that the walk with steps Y - 1 reaches from 0, by height; its sum
    is below one, the walk never rising otherwise. The walk is dropped once it trails by floor."""
    n = floor + 1                                    # index i holds the lead i - floor <= 0
    p = np.zeros(n)
    p[floor] = 1.0
    h = np.zeros(step.size)
    while True:
        q = np.zeros(n)
        for i in range(n):
            if p[i] == 0.0:
                continue
            for y in range(step.size):
                j = i + y - 1
                if j > floor:
                    h[j - floor] += p[i] * step[y]
                elif j >= 0:
                    q[j] += p[i] * step[y]
        left = 0.0
        for i in range(n):
            left += q[i]
        p = q
        if left < TINY:
            return h


@njit(cache=True)
def _renewal(h):
    """The pmf of the walk's all-time maximum from 0: a geometric number of independent heights h."""
    stay = 1.0 - h.sum()
    u = [1.0]                                        # P(some sum of heights equals m)
    while len(u) < h.size or u[-1] * stay > TINY:
        m = len(u)
        v = 0.0
        for j in range(1, min(m, h.size - 1) + 1):
            v += h[j] * u[m - j]
        u.append(v)
    return stay * np.array(u)


def post_cutoff(f: float, alpha: float, growth: float | None = None, delta: int | None = None,
                floor: int = 200, lower: bool = False) -> np.ndarray:
    """The pmf of ``Z``, the most the coalition's private chain leads the public one after the
    cut-off: the lead just before each later canonical honest block, ``V_1 = Y_1`` and then
    ``V_(k+1) = V_k + Y_(k+1) - 1``. ``Z`` is ``Y_1`` plus the all-time maximum of the walk with steps
    ``Y - 1`` from 0. The first gap is taken whole, exact under random delay and from above under a
    worst case; ``lower`` leaves the coalition's wins in it out under a worst case, from below."""
    _, step = walk(f, alpha, growth, delta)
    top = _renewal(_ladder(step, floor))
    return top if (lower and delta is not None) else np.convolve(step, top)


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


def _ztable(base: np.ndarray, z: int, depths: int, cap: int, floor: int) -> np.ndarray:
    """log2 S_d given Z = z, by depth d = 0..depths and lead index i (the lead i - floor); -inf
    where a fork point offers no choice. ``base`` is ``_table`` with leads up to cap + z."""
    n = floor + cap + 1
    lead = np.arange(n) - floor
    out = np.full((depths + 1, n), -np.inf)
    ok = lead >= 1
    out[0, ok] = base[0, lead[ok]]                                       # 2^W_0 - 1
    top = min(z, depths + 1)
    if top > 1:
        w = lead[None, :] + np.arange(1, top)[:, None]                   # 2^W_d below depth z
        out[1:top] = np.where(w >= 0, w, -np.inf)
    if z <= depths:
        rows = np.arange(max(z, 1), depths + 1)
        cols = np.nonzero(lead + z >= 1)[0]
        out[np.ix_(rows, cols)] = base[(rows - z)[:, None], (lead[cols] + z)[None, :]]
    return out


def _place(first: np.ndarray, floor: int, n: int) -> tuple[np.ndarray, float]:
    """The first lead on a lattice of n leads from -floor, and the probability past its top."""
    init = np.zeros(n)
    k = min(first.size, n - floor)
    init[floor:floor + k] = first[:k]
    return init, float(first[k:].sum())


@njit(cache=True)
def _absorbed(init, over, step, tab, x):
    """P(M >= 2^x): the walk from ``init`` stops on reaching a lead whose S is at least 2^x; a lead
    past the table's, and ``over``, reach every threshold."""
    depths, n = tab.shape[0] - 1, tab.shape[1]                 # index i holds the lead i - floor
    p = init.copy()
    hit = over
    for i in range(n):
        if p[i] > 0.0 and tab[0, i] >= x - ROUND:
            hit += p[i]
            p[i] = 0.0
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
        for i in range(n):
            if q[i] > 0.0 and tab[d, i] >= x - ROUND:
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
def _max_tail(init, over, step, tab, xs):
    out = np.zeros(xs.size)
    reach = np.zeros(xs.size, np.int64)
    for k in prange(xs.size):
        out[k], reach[k] = _absorbed(init, over, step, tab, xs[k])
    return out, reach.max()


@njit(cache=True)
def _bin(diff, mass, xs, s, w):
    diff[np.searchsorted(xs, s + ROUND, side="right")] += w * 2.0 ** s
    mass[min(np.searchsorted(xs, s - ROUND), xs.size - 1)] += w


@njit(cache=True)
def _union(init, over, step, tab, xs):
    """By threshold, the increments over x of sum over d of E[S_d; S_d < 2^x]; and by bin, sum over d
    of P(S_d >= 1), bin k holding 2^xs[k-1] < S_d <= 2^xs[k], the last bin also every S_d above it
    and ``over``."""
    depths, n = tab.shape[0] - 1, tab.shape[1]
    diff = np.zeros(xs.size + 1)
    mass = np.zeros(xs.size)
    mass[-1] += over
    p = init.copy()
    for d in range(depths + 1):
        for i in range(n):
            if p[i] > 0.0 and tab[d, i] > -np.inf:
                _bin(diff, mass, xs, tab[d, i], p[i])
        q = np.zeros(n)
        for i in range(n):
            if p[i] == 0.0:
                continue
            for z in range(step.size):
                j = i + z - 1
                if j >= n:
                    mass[-1] += p[i] * step[z]
                elif j >= 0:
                    q[j] += p[i] * step[z]
        left = 0.0
        for i in range(n):
            left += q[i]
        p = q
        if left < TINY:
            return diff, mass, d
    return diff, mass, depths + 1


@njit(cache=True)
def _before(first, step, base, x, floor, cap, pz):
    """The walk before the post-cut-off lead z takes over, for every z at once. The last honest
    block's choices absorb it at depth 0, and 2^W_d at depths 1..z-1. Returns sum_z pz[z]
    P(absorbed before depth z); and sum_z pz[z] times the walk left at depth z, its lead raised by
    z, on a lattice of floor + cap + zmax + 1 leads (at z = 0, the first lead)."""
    zmax = pz.size - 1
    n = floor + cap + 1
    out = np.zeros(n + zmax)
    hit, before = 0.0, 0.0
    p = np.zeros(n)
    for y in range(first.size):
        i = y + floor
        if i < n + zmax:
            out[i] += pz[0] * first[y]
        else:
            before += pz[0] * first[y]
        if i >= n or (i - floor >= 1 and base[0, i - floor] >= x - ROUND):
            hit += first[y]
        else:
            p[i] += first[y]
    for z in range(1, zmax + 1):
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
        p = q
        before += pz[z] * hit
        for i in range(n):
            out[i + z] += pz[z] * p[i]
            if p[i] > 0.0 and i - floor + z >= x - ROUND:     # W_z = L_z + z
                hit += p[i]
                p[i] = 0.0
    return before, out


@njit(cache=True, parallel=True)
def _max_tail_mixed(first, step, base, tab, xs, floor, cap, pz):
    out = np.zeros(xs.size)
    reach = np.zeros(xs.size, np.int64)
    for k in prange(xs.size):
        before, init = _before(first, step, base, xs[k], floor, cap, pz)
        after, reach[k] = _absorbed(init, 0.0, step, tab, xs[k])
        out[k] = before + after
    return out, reach.max()


@njit(cache=True)
def _union_before(first, step, base, xs, floor, cap, pz):
    """``_union``'s terms before the post-cut-off lead takes over, each depth weighted by the
    probability of the z it precedes; and the walk handed over as in ``_before``, unabsorbed."""
    zmax = pz.size - 1
    n = floor + cap + 1
    ge = np.zeros(zmax + 2)                                     # ge[d] = P(d <= Z <= zmax)
    for z in range(zmax, -1, -1):
        ge[z] = ge[z + 1] + pz[z]
    diff = np.zeros(xs.size + 1)
    mass = np.zeros(xs.size)
    out = np.zeros(n + zmax)
    p = np.zeros(n)
    for y in range(first.size):
        i = y + floor
        if i < n + zmax:
            out[i] += pz[0] * first[y]
        else:
            mass[-1] += pz[0] * first[y]
        if i < n:
            p[i] += first[y]
        else:
            mass[-1] += ge[1] * first[y]
    for i in range(n):
        if p[i] > 0.0 and i - floor >= 1:
            _bin(diff, mass, xs, base[0, i - floor], ge[1] * p[i])
    for z in range(1, zmax + 1):
        q = np.zeros(n)
        for i in range(n):
            if p[i] == 0.0:
                continue
            for y in range(step.size):
                j = i + y - 1
                if j >= n:
                    mass[-1] += ge[z] * p[i] * step[y]
                elif j >= 0:
                    q[j] += p[i] * step[y]
        p = q
        for i in range(n):
            out[i + z] += pz[z] * p[i]
            if p[i] > 0.0 and ge[z + 1] > 0.0:
                _bin(diff, mass, xs, float(i - floor + z), ge[z + 1] * p[i])
    return diff, mass, out


def _mixture(f, alpha, growth, delta, xs, depths, floor, cap, lower, union):
    """P(M >= 2^x), and with ``union`` the union's sums by threshold and its mass by bin, each mixed
    over the post-cut-off lead; and the probability of the leads past the mixture."""
    first, step = walk(f, alpha, growth, delta)
    pz = post_cutoff(f, alpha, growth, delta, lower=lower)
    tail_mass = np.cumsum(pz[::-1])[::-1]
    zmax = int(np.nonzero(tail_mass > ZCUT)[0][-1])
    if zmax >= floor:
        raise ValueError("the post-cut-off lead outruns the walk's floor")
    base = _table(depths, cap + zmax)
    tab = _ztable(base, 0, depths, cap + zmax, floor)
    pz_in = pz[:zmax + 1].copy()
    tail, reach = _max_tail_mixed(first, step, base, tab, xs, floor, cap, pz_in)
    below, mass = np.zeros(xs.size), np.zeros(xs.size)
    if union:
        d_before, m_before, init = _union_before(first, step, base, xs, floor, cap, pz_in)
        d_after, m_after, r = _union(init, 0.0, step, tab, xs)
        below, mass = np.cumsum(d_before + d_after)[:xs.size], m_before + m_after
        reach = max(reach, r)
    if reach > depths:
        raise ValueError("the walk outlasted the depths tabulated")
    return tail, below, mass, float(pz[zmax + 1:].sum())


def tail(f: float, alpha: float, xs: np.ndarray, growth: float | None = None,
         delta: int | None = None, depths: int = 4000, floor: int = 100,
         cap: int = 300) -> np.ndarray:
    """``P(M >= 2^x)`` for each x in xs, over the choices complete at the cut-off.

    The walk is dropped once it trails by ``floor`` blocks, and a lead above ``cap`` counts as
    reaching every threshold. A walk that has not ended within ``depths`` blocks raises.
    """
    first, step = walk(f, alpha, growth, delta)
    tab = _ztable(_table(depths, cap), 0, depths, cap, floor)
    init, over = _place(first, floor, tab.shape[1])
    out, reach = _max_tail(init, over, step, tab, np.asarray(xs, float))
    if reach > depths:
        raise ValueError("the walk outlasted the depths tabulated")
    return out


def _bounds(f, alpha, growth, delta, budget_bits, depths, floor, cap, per_bit, after_cutoff, extra_bits):
    xs = np.arange(budget_bits * per_bit + 1) / per_bit
    if after_cutoff:
        tail_up, below, mass, rest = _mixture(f, alpha, growth, delta, xs, depths, floor, cap,
                                              False, True)
        tail_lo = tail_up if delta is None else _mixture(f, alpha, growth, delta, xs, depths, floor,
                                                         cap, True, False)[0]
    else:
        first, step = walk(f, alpha, growth, delta)
        tab = _ztable(_table(depths, cap), 0, depths, cap, floor)
        init, over = _place(first, floor, tab.shape[1])
        tail_up, reach = _max_tail(init, over, step, tab, xs)
        diff, mass, reach_u = _union(init, over, step, tab, xs)
        if max(reach, reach_u) > depths:
            raise ValueError("the walk outlasted the depths tabulated")
        below = np.cumsum(diff)[:xs.size]
        tail_lo, rest = tail_up, 0.0
    x = 2.0 ** xs
    # the integral of P(M >= y) over 0 <= y <= x_k, from below: P(M >= y) >= P(M >= x_{k+1}) on a step
    area = np.concatenate(([tail_lo[0]], tail_lo[0] + np.cumsum(np.diff(x) * tail_lo[1:])))
    ts = np.arange((budget_bits + extra_bits) * per_bit + 1) / per_bit
    u = 2.0 ** -ts
    k = np.minimum(np.arange(ts.size), xs.size - 1)   # x = min(1/u, B)
    lower = np.maximum(u, u * area[k])
    upper = np.minimum(1.0, u * x[-1]) * (tail_up[k] + rest) + u + u * below[k]
    upper = np.minimum(upper, np.minimum(1.0, u * x[-1]))
    return ts, lower, upper, tail_lo, tail_up, below, mass, rest, xs


def bounds(f: float, alpha: float, growth: float | None = None, delta: int | None = None,
           budget_bits: int = 64, depths: int = 4000, floor: int = 100, cap: int = 300,
           per_bit: int = PER_BIT,
           after_cutoff: bool = True) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Lower and upper bounds on ``phi(u)`` at ``u = 2^-t``, for t on a grid of ``1/per_bit`` bit up
    to ``budget_bits + 60``, and ``P(G > 1)`` for the choices complete at the cut-off. With
    ``after_cutoff`` both bounds count the forks completed after it. The walk is truncated as in
    ``tail``."""
    ts, lower, upper = _bounds(f, alpha, growth, delta, budget_bits, depths, floor, cap, per_bit,
                               after_cutoff, 60)[:3]
    return ts, lower, upper, float(tail(f, alpha, np.zeros(1), growth, delta, depths, floor, cap)[0])


def pair_bounds(f: float, alpha: float, growth: float | None = None, delta: int | None = None,
                budget_bits: int = 64, depths: int = 4000, floor: int = 100, cap: int = 300,
                per_bit: int = PER_BIT) -> tuple[np.ndarray, ...]:
    """Lower and upper bounds on ``phi(u)``, then on ``phi_2(u)``, at ``u = 2^-t`` for t on a grid of
    ``1/per_bit`` bit up to ``2 budget_bits + 60``: one epoch's nonce, then two independently
    ground ones."""
    ts, lower, upper, tail_lo, tail_up, below, mass, rest, xs = _bounds(
        f, alpha, growth, delta, budget_bits, depths, floor, cap, per_bit, True, budget_bits + 60)
    n = ts.size

    def at(v, k):                                     # v at u 2^xs[k]; one where that exceeds 1
        return np.concatenate((np.ones(k), v[:n - k]))

    hat = np.minimum.accumulate(upper)                # the least upper bound at any larger u
    hat_b = at(hat, xs.size - 1)                      # at u B
    upper2 = hat + sum(m * at(hat, k) for k, m in enumerate(mass) if m > 0.0)
    thr = np.full(n, np.inf)
    for k in range(xs.size):
        thr = np.minimum(thr, hat_b * tail_up[k] + hat * (1.0 + below[k]))
    upper2 = np.minimum(upper2, thr) + rest * hat_b
    upper2 = np.minimum(upper2, 2.0 ** -ts * 4.0 ** budget_bits)   # min(G, B) min(G', B) <= B^2
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
    log2mz = np.full(n_samples, -np.inf)
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
        total, total_z, best, best_z, wins, d = 1.0, 1.0, 0.0, 0.0, 0, 0
        for t in range(n_slots - 1, 0, -1):          # the cut-off is slot n_slots
            if canon[t]:
                if d <= d_out:
                    leads[s, d] = wins - d
                term = _choices(wins, d, 0)
                total += term
                best = max(best, term)
                term_z = _choices(wins, d, z)
                total_z += term_z
                best_z = max(best_z, term_z)
                d += 1
            if adv[t]:
                wins += 1
        log2g[s] = math.log2(total)
        log2gz[s] = math.log2(total_z)
        if best > 0.0:
            log2m[s] = math.log2(best)
        if best_z > 0.0:
            log2mz[s] = math.log2(best_z)
    return leads, log2g, log2m, log2gz, zs, log2mz


def simulate(f: float, alpha: float, n_samples: int, n_slots: int, d_out: int, seed: int,
             growth: float | None = None,
             delta: int | None = None) -> tuple[np.ndarray, ...]:
    """Slot by slot, forwards from a canonical honest block: ``L_d`` for ``d <= d_out``; ``log2 G``
    and ``log2 M`` over the forks the ``n_slots`` slots before the cut-off hold; ``log2 G`` with the
    forks the coalition completes after the cut-off as well; ``Z``; and ``log2 M`` with those forks."""
    if (growth is None) == (delta is None):
        raise ValueError("set exactly one of growth and delta")
    ph = occupancy(f, 1.0 - alpha)
    h, dead = (growth * ph, 0) if growth is not None else (ph, delta)
    return _simulate(n_samples, h, occupancy(f, alpha), dead, n_slots, d_out, seed)
