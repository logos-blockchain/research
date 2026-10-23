"""A bound for a wait of ``T`` slots in the model of Gaži, Ren and Russell (SLOTS.md, K.7).

K.1 bounds a wait under the worst case through B2's depth: ``min_D [UB(D) + P(N − W − 2 < D)]``.
B2 freezes its chain at the earliest moment the target could be ``D`` deep, when the coalition's
lead, the honest successes and twice the coalition's successes since the target reach ``D``. K.1
then also waits for the honest chain to grow ``D`` blocks at its slowest. This module bounds the
wait in the paper's own model instead.

- **The event.** The paper's Lemma 10: the prefix up to slot ``ℓ`` stays in every dominant chain
  from ``t`` on if the margin ``μ_ℓ`` is negative at every time from ``t``. A wait of ``T`` slots
  fixes that prefix at ``ℓ + T``, so it fails only if ``μ_ℓ ≥ 0`` at some time from ``ℓ + T``.
- **The chain.** LCanalysis's phase chain on ``(μ_ℓ, ρ)`` as ``lcbounds`` ports it: the same
  symbols, transitions and final vector, and the same stationary reach where it starts. Only the
  freeze moves, from a count of blocks to a clock.
- **The clock.** A step is a phase: a wait for the next success, exponential with a mean of one
  block interval, then, for a phase of ``h`` honest successes, its span, which is below ``h·Δ``.
  The clock counts each wait rounded up to a whole level and each span as ``h·Δ``, so it runs
  ahead of time. The chain therefore freezes at, or before, the step in which ``T`` passes, and
  keeps the state after that step, which bounds the margin over all of the step.
- **The start.** The step that covers ``ℓ`` is weighted by its length, which is at most its wait
  plus ``h·Δ``, over the mean step, ``1/g`` block intervals with ``g = e^(−(1 − α)·D)`` and ``D``
  the delay in block intervals. The clock starts at that step's start, before ``ℓ``. The weights
  add ``g + (1 − α)·D − 1`` to the mass.
- **Slots.** The paper computes in continuous time, and B2 reads it at ``D = f·Δ``. On a lottery
  of whole slots a phase also holds the slot of its first honest success, so the coalition wins
  in ``Δ + 1`` slots of a lone honest success, where continuous time gives it ``Δ``. With
  ``slots`` the chain runs at ``Δ + 1`` slots and at ``λ = −ln(1 − f)`` successes a slot, whose
  chance of at least one per slot is the lottery's: each phase then gives the coalition its slots
  and the honest depth needs gaps of ``Δ + 1``, as the slotted model does.

``_levels`` runs the chain level by level, as ``lcbounds._ub_levels`` runs it over depths: a step
from level ``l`` ends at ``l + c + G``, ``c`` its symbol's cost and ``G`` geometric at ``q``. With
LCanalysis's counts as costs and ``q = 0`` it is ``ub_curve`` (``count_curve``, a gate).
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

from .lcbounds import SlotPdf, _final_matrix, _general_move, slot_pdf, warmup

F = 1 / 30
INIT_TAIL = 1e-60       # the first step's wait is followed until the mass left is below this


def symbols(sp: SlotPdf, alphabet: int, min_prob: float) -> tuple[np.ndarray, ...]:
    """The general symbols ``(H = h, D = j, A = i)`` above ``min_prob`` and their probabilities,
    in ``lcbounds._ub_levels``'s order."""
    sh, sj, si, sprob = [], [], [], []
    for h in range(1, alphabet + 1):
        for j in range(1, max(1, h - 1) + 1):
            for i in range(alphabet):
                p = sp.ph[h - 1] * sp.pd[h - 1, j - 1] * sp.pa[h - 1, j - 1, i]
                if p > min_prob:
                    sh.append(h)
                    sj.append(j)
                    si.append(i)
                    sprob.append(p)
    return (np.array(sh, np.int64), np.array(sj, np.int64), np.array(si, np.int64),
            np.array(sprob))


def state_index(states: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The chain's states, flattened: the diagonal ``x = y ≥ 0`` and the plane ``x < 0 ≤ y``.
    Returns the index of ``(x, y)`` at ``[x + states, y]`` (−1 where none), and each state's x, y."""
    idx = -np.ones((2 * states + 1, states + 1), np.int64)
    xs, ys = [], []
    for x in range(-states, states + 1):
        for y in range(0, states + 1):
            if x >= 0 and y != x:
                continue
            idx[x + states, y] = len(xs)
            xs.append(x)
            ys.append(y)
    return idx, np.array(xs, np.int64), np.array(ys, np.int64)


@njit(cache=True)
def _table(idx, xs, ys, states, c_adv, c_spec, sh, sj, si, sp, sc, pa_only, p_spec):
    """Each state's moves, merged by cost and destination: ``row[n]..row[n + 1]`` index the
    entries ``(cost, dst, prob)`` of state ``n``, sorted by cost."""
    n = xs.size
    cap = sh.size + 2
    row = np.zeros(n + 1, np.int64)
    e_cost = np.empty(n * cap, np.int64)
    e_dst = np.empty(n * cap, np.int64)
    e_prob = np.empty(n * cap)
    k_cost = np.empty(cap, np.int64)
    k_dst = np.empty(cap, np.int64)
    k_prob = np.empty(cap)
    pos = 0
    for st in range(n):
        x, y = xs[st], ys[st]
        m = 0
        dst = -1
        if x >= 0 and x < states:                                 # (a=1, h=0)
            dst = idx[x + 1 + states, x + 1]
        elif x == -1 and y < states:
            dst = idx[y + 1 + states, y + 1]
        elif x < -1 and y < states:
            dst = idx[x + 1 + states, y + 1]
        if dst >= 0:
            k_cost[m], k_dst[m], k_prob[m] = c_adv, dst, pa_only
            m += 1
        if x == 0:                                                # (a=0, h=1)
            k_cost[m], k_dst[m], k_prob[m] = c_spec, idx[states - 1, 0], p_spec
            m += 1
        for s in range(sh.size):
            ok, dx, dy = _general_move(x, y, sh[s], sj[s], si[s], states)
            if ok:
                k_cost[m], k_dst[m], k_prob[m] = sc[s], idx[dx + states, dy], sp[s]
                m += 1
        order = np.argsort(k_cost[:m] * n + k_dst[:m], kind="mergesort")
        row[st] = pos
        last = -1
        for r in range(m):
            o = order[r]
            key = k_cost[o] * n + k_dst[o]
            if key == last:
                e_prob[pos - 1] += k_prob[o]
            else:
                e_cost[pos], e_dst[pos], e_prob[pos] = k_cost[o], k_dst[o], k_prob[o]
                pos += 1
                last = key
    row[n] = pos
    return row, e_cost[:pos].copy(), e_dst[:pos].copy(), e_prob[:pos].copy()


@njit(cache=True)
def _absorb(row, e_cost, e_dst, e_prob, xs, v, states):
    """The costs in use, ascending, and ``absorb[k, n]``: the weight ``v`` of the state after a
    step from state ``n``, over the moves whose cost is at least the ``k``-th cost. A step from
    level ``l`` that ends at ``l + c`` crosses every level in ``(l, l + c]``."""
    n = xs.size
    c_max = 0
    for e in range(e_cost.size):
        c_max = max(c_max, e_cost[e])
    used = np.zeros(c_max + 1, np.bool_)
    for e in range(e_cost.size):
        used[e_cost[e]] = True
    cvals = np.nonzero(used)[0]
    pos = -np.ones(c_max + 1, np.int64)
    for k in range(cvals.size):
        pos[cvals[k]] = k
    absorb = np.zeros((cvals.size, n))
    for st in range(n):
        for e in range(row[st], row[st + 1]):
            absorb[pos[e_cost[e]], st] += e_prob[e] * v[states + xs[e_dst[e]]]
    for k in range(cvals.size - 2, -1, -1):
        absorb[k] += absorb[k + 1]
    return cvals, absorb


@njit(cache=True)
def _levels(t_max, floor, q, row, e_cost, e_dst, e_prob, cvals, absorb, inj_level, inj_weight,
            inj_state, out):
    """The level pass. ``out[t]`` gathers, for every level ``t``, the weight ``v`` of the state
    after the step that crosses ``t``; it may arrive holding the first step's share. A step from
    level ``l`` ends at ``l + c + G``, ``G`` geometric at ``q`` (``q = 0``: ``G = 0``). Entry ``j``
    of the injection adds ``inj_weight[j, b]·inj_state[b]`` to the pool at ``inj_level[j] + b``.
    Returns the last level at which ``out`` is final: ``t_max``, or the first past the injection
    whose bound is at most ``floor``.

    The mass in the pool at ``l`` crosses ``l + 1`` whatever it draws; the part that fires at ``l``
    crosses ``l + m`` when its cost is at least ``m``. Each level keeps, per cost, the fired mass's
    weight summed over the states, so ``out[l + 1]`` is a sum of positive terms."""
    n = row.size - 1
    n_c = cvals.size
    c_max = cvals[n_c - 1]
    big = max(c_max + 1, inj_state.shape[0] + 1)
    group = np.zeros(c_max + 1, np.int64)            # the cost group that holds offset m
    k = 0
    for m in range(1, c_max + 1):
        while cvals[k] < m:
            k += 1
        group[m] = k
    pool = np.zeros((big, n))
    fired = np.zeros((big, n_c))                     # per level, the fired weight per cost group
    fire = 1.0 - q
    n_inj = inj_level.size
    j_inj = 0
    for level in range(t_max):
        cur = level % big
        while j_inj < n_inj and inj_level[j_inj] <= level:
            for b in range(inj_state.shape[0]):
                wt = inj_weight[j_inj, b]
                if wt != 0.0:
                    dst = (inj_level[j_inj] + b) % big
                    for st in range(n):
                        pool[dst, st] += wt * inj_state[b, st]
            j_inj += 1
        now = 0.0
        for kk in range(n_c):
            fired[cur, kk] = 0.0
        for st in range(n):
            u = pool[cur, st]
            if u == 0.0:
                continue
            now += u * absorb[0, st]                              # the step in progress
            fu = fire * u
            for kk in range(n_c):
                fired[cur, kk] += fu * absorb[kk, st]
            for e in range(row[st], row[st + 1]):
                pool[(level + e_cost[e]) % big, e_dst[e]] += fu * e_prob[e]
            if q > 0.0:
                pool[(level + 1) % big, st] += q * u
            pool[cur, st] = 0.0
        total = now
        for m in range(2, c_max + 1):                             # fired m levels before
            if level + 1 - m < 0:
                break
            total += fired[(level + 1 - m) % big, group[m]]
        out[level + 1] += total
        if floor > 0.0 and j_inj >= n_inj and out[level + 1] <= floor:
            return level + 1
    return t_max


class Chain:
    """LCanalysis's chain at one point, with a cost per move: the counts, or the clock."""

    def __init__(self, alpha: float, d: float, alphabet: int, states: int, min_prob: float):
        self.states = states
        self.sp = slot_pdf(1 - alpha, d, alphabet)
        self.st0 = warmup(self.sp.pad, alphabet, states, upper=True)
        self.v = _final_matrix(self.sp.pad, alphabet, states)[states:].sum(axis=0)
        self.sh, self.sj, self.si, self.sprob = symbols(self.sp, alphabet, min_prob)
        self.p_spec = self.sp.ph[0] * self.sp.pa[0, 0, 0]
        self.idx, self.xs, self.ys = state_index(states)

    def moves(self, c_adv: int, c_spec: int, sc: np.ndarray):
        row, e_cost, e_dst, e_prob = _table(self.idx, self.xs, self.ys, self.states, c_adv,
                                            c_spec, self.sh, self.sj, self.si, self.sprob,
                                            np.asarray(sc, np.int64), self.sp.pa_only,
                                            self.p_spec)
        cvals, absorb = _absorb(row, e_cost, e_dst, e_prob, self.xs, self.v, self.states)
        return row, e_cost, e_dst, e_prob, cvals, absorb

    def diagonal(self, i: int) -> int:
        return int(self.idx[i + self.states, i])


def count_curve(k_max: int, alpha: float, d: float, alphabet: int, states: int,
                min_prob: float = 0.0) -> np.ndarray:
    """``lcbounds.ub_curve`` through ``_levels``: each move costs LCanalysis's count, ``h + 2a``
    for a phase and two for an adversary-only symbol, with no wait; the initial lead ``i`` starts
    at level ``i`` and is confirmed on arrival at every depth up to ``i``. A gate of the pass."""
    ch = Chain(alpha, d, alphabet, states, min_prob)
    row, e_cost, e_dst, e_prob, cvals, absorb = ch.moves(2, 1, ch.sh + 2 * ch.si)
    z = states
    out = np.zeros(k_max + int(cvals[-1]) + 2)
    inj_state = np.zeros((states + 1, ch.xs.size))
    for i in range(states + 1):
        inj_state[i, ch.diagonal(i)] = ch.st0[z + i]
        out[1:min(i, k_max) + 1] += ch.st0[z + i] * ch.v[z + i]   # confirmed on arrival
    _levels(k_max, 0.0, 0.0, row, e_cost, e_dst, e_prob, cvals, absorb,
            np.zeros(1, np.int64), np.ones((1, states + 1)), inj_state, out)
    return out[1:k_max + 1]


def first_step(ch: Chain, row, e_cost, e_dst, e_prob, f_u: float, g: float,
               t_len: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """The step that covers the target, weighted by its length, for the clock.

    A move of body ``b`` levels (its cost less the wait's first level) whose wait ends in level
    ``n`` weighs ``P(s)·g·f_u·∫_{n−1}^{n} (e + b)·f_u·e^(−f_u·e) de``: the length-biased law with
    the step's length bounded by its wait plus ``b``, over the mean step, ``1/(g·f_u)`` levels. It
    crosses every level up to ``n + b``.

    Returns the injection (levels, weights per body, states per body), the first step's share of
    ``out[t]`` for ``t < t_len``, and the mass whose wait outlasts the injection, which the bound
    adds at every later level."""
    z = ch.states
    b_max = int(e_cost.max()) - 1
    inj_state = np.zeros((b_max + 1, ch.xs.size))
    crossed = np.zeros(b_max + 1)
    for i in range(ch.states + 1):
        m0 = ch.st0[z + i]
        if m0 == 0.0:
            continue
        st = ch.diagonal(i)
        for e in range(row[st], row[st + 1]):
            b = int(e_cost[e]) - 1
            inj_state[b, e_dst[e]] += m0 * e_prob[e]
            crossed[b] += m0 * e_prob[e] * ch.v[z + ch.xs[e_dst[e]]]

    def tail(m: np.ndarray, b: int) -> np.ndarray:
        """The weight of the waits that end in level ``m`` or later."""
        e = m - 1.0
        return g * f_u * np.exp(-f_u * e) * (e + 1.0 / f_u + b)

    n_last = 1
    while tail(np.array([n_last + 1.0]), b_max)[0] > INIT_TAIL:
        n_last += 1
    n = np.arange(1, n_last + 1, dtype=float)
    bodies = [b for b in range(b_max + 1) if inj_state[b].any()]
    inj_weight = np.zeros((n.size, b_max + 1))
    for b in bodies:
        inj_weight[:, b] = tail(n, b) - tail(n + 1.0, b)
    left = sum(float(tail(np.array([n_last + 1.0]), b)[0] * inj_state[b].sum()) for b in bodies)
    t = np.arange(t_len)
    first = np.zeros(t_len)
    for b in bodies:
        first += crossed[b] * tail(np.maximum(1, t - b).astype(float), b)
    first[0] = 0.0
    return n.astype(np.int64), inj_weight, inj_state, first, left


def alphabet_for(alpha: float, d: float, tail: float = 1e-10) -> int:
    """B2's alphabet: the honest run's truncated mass ``(1 − g)^A`` stays below ``tail``."""
    g = math.exp(-(1 - alpha) * d)
    return max(10, math.ceil(math.log(tail) / math.log(1 - g)) + 1)


def wait_curve(t_max: int, alpha: float, delta_s: float, f: float = F,
               alphabet: int | None = None, states: int | None = None, min_prob: float = 1e-16,
               floor: float = 0.0, unit: float = 1.0, body: str = "h",
               slots: bool = True, scale: float = 1.0) -> np.ndarray:
    """The bound at waits of ``1, 2, ...`` levels of ``unit`` slots (entry ``t − 1`` holds ``t``),
    up to ``t_max`` or the first past the first step at most ``floor``. B2's alphabet and states.
    ``f`` is the lottery's chance that a slot is won; with ``slots`` the chain runs at ``Δ + 1``
    slots and ``−ln(1 − f)`` successes a slot, without it at ``Δ`` and ``f``, as B2 reads it.
    ``scale`` multiplies both shares' rates: a deflated inference raises them by ``1/(1 − α)``.

    ``body = "h"`` charges a phase of ``h`` honest successes ``h·Δ``, which bounds its span.
    ``"d"`` charges ``d·Δ``, ``d`` the honest depth it adds, which the span exceeds: not a bound,
    it brackets what the first charge costs."""
    if slots:
        f, delta_s = -math.log(1 - f), delta_s + 1
    f *= scale
    d = f * delta_s
    alphabet = alphabet_for(alpha, d) if alphabet is None else alphabet
    states = max(30, alphabet + 1) if states is None else states
    delta_lv = round(delta_s / unit)
    if delta_lv < 1 or abs(delta_lv * unit - delta_s) > 1e-9:
        raise ValueError("the unit must divide the delay")
    ch = Chain(alpha, d, alphabet, states, min_prob)
    if body == "h":
        sc = 1 + ch.sh * delta_lv
    elif body == "d":
        sc = 1 + ch.sj * delta_lv
    else:
        raise ValueError(body)
    row, e_cost, e_dst, e_prob, cvals, absorb = ch.moves(1, 1 + delta_lv, sc)
    f_u = f * unit
    g = math.exp(-(1 - alpha) * d)
    inj_level, inj_weight, inj_state, first, left = first_step(
        ch, row, e_cost, e_dst, e_prob, f_u, g, t_max + int(cvals[-1]) + 2)
    out = first
    last = _levels(t_max, floor, math.exp(-f_u), row, e_cost, e_dst, e_prob, cvals, absorb,
                   inj_level, inj_weight, inj_state, out)
    res = out[1:last + 1].copy()
    res[int(inj_level[-1]):] += left
    return np.minimum(res, 1.0)


def wait_needed(curve: np.ndarray, eps: float) -> int:
    """The shortest wait, in levels, whose bound is at most ``eps``; −1 if none in the curve."""
    hit = np.nonzero(curve <= eps)[0]
    return int(hit[0]) + 1 if hit.size else -1


@njit(cache=True)
def steps(n_slots, rate_h, rate_a, delta, seed):
    """The model's steps drawn in continuous time, as LCanalysis cuts them: an adversary-only
    symbol at each adversarial success outside a phase, and a phase from an honest success until
    ``delta`` slots pass without one, with its honest successes ``h``, the honest depth ``d`` they
    add (one more whenever a success comes at least ``delta`` after the last that added one) and
    the adversarial successes ``a`` within it. Returns ``h`` (0 for adversary-only), ``d``, ``a``
    and each step's end; each step starts where the last ended."""
    np.random.seed(seed)
    cap = int(n_slots * (rate_h + rate_a) * 1.2) + 1000
    hs = np.empty(cap, np.int64)
    ds = np.empty(cap, np.int64)
    as_ = np.empty(cap, np.int64)
    ends = np.empty(cap)
    t = 0.0
    nxt_h = np.random.exponential(1.0 / rate_h)
    nxt_a = np.random.exponential(1.0 / rate_a)
    n = 0
    while t < n_slots and n < cap:
        if nxt_a < nxt_h:
            t = nxt_a
            nxt_a = t + np.random.exponential(1.0 / rate_a)
            hs[n], ds[n], as_[n], ends[n] = 0, 0, 1, t
            n += 1
            continue
        last = nxt_h
        jump = nxt_h
        h, d, a = 1, 1, 0
        nxt_h = last + np.random.exponential(1.0 / rate_h)
        while nxt_h - last < delta:
            last = nxt_h
            h += 1
            if last - jump >= delta:
                d += 1
                jump = last
            nxt_h = last + np.random.exponential(1.0 / rate_h)
        end = last + delta
        while nxt_a <= end:
            a += 1
            nxt_a = nxt_a + np.random.exponential(1.0 / rate_a)
        t = end
        hs[n], ds[n], as_[n], ends[n] = h, d, a, t
        n += 1
    return hs[:n], ds[:n], as_[:n], ends[:n]


@njit(cache=True)
def play_one(hs, ds, as_, ends, x0, k, target, wait):
    """One target of ``play_chain``: from step ``k`` on the diagonal at reach ``x0``, the chain of
    ``_general_move`` until the first step that ends at ``target + wait`` or later, whose state it
    keeps, then the final chain for 200 steps. True if the margin reaches zero after the freeze."""
    n = hs.size
    x, y = x0, x0
    m = k
    frozen = False
    after = 0
    while m < n and after <= 200:
        h, d, a = hs[m], ds[m], as_[m]
        if not frozen:
            if h == 0:
                if x >= 0:
                    x, y = x + 1, x + 1
                elif x == -1:
                    x, y = y + 1, y + 1
                else:
                    x, y = x + 1, y + 1
            elif x >= 0:
                if x == 0 and h == 1 and a == 0:
                    x, y = -1, 0
                else:
                    dst = x + a - d if x > d else a
                    x, y = dst, dst
            elif x < -a:
                x, y = x + a - d, max(0, y + a - d)
            else:
                dst = max(0, y + a - d)
                x, y = dst, dst
            if ends[m] >= target + wait:
                frozen = True
                if x >= 0:
                    return True
        else:
            after += 1
            if h == 0:
                x = x + 1
            elif x < -a or x > d:
                x = x + a - d
            else:
                x = min(0, x) + a
            if x >= 0:
                return True
        m += 1
    return False


@njit(cache=True)
def play_chain(hs, ds, as_, ends, waits, n_targets, burn, tail, seed):
    """The bounding chain played on drawn steps with their true lengths. Targets fall at uniform
    times; each starts at the step that covers it, on the diagonal at the reach there
    (``play_one``). Returns the failures per wait and the targets. ``tail`` slots are kept after
    the last wait so that every target runs its course."""
    np.random.seed(seed)
    n = hs.size
    reach = np.zeros(n, np.int64)                    # the reach at each step's start
    r = 0
    for k in range(n):
        reach[k] = r
        if hs[k] == 0:
            r += 1
        elif r > ds[k]:
            r = r + as_[k] - ds[k]
        else:
            r = as_[k]
    fails = np.zeros(waits.size, np.int64)
    t_lo = ends[burn]
    t_hi = ends[n - 1] - waits[waits.size - 1] - tail
    for _ in range(n_targets):
        target = t_lo + np.random.random() * (t_hi - t_lo)
        lo, hi = burn, n - 1                         # the first step that ends at the target or later
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if ends[mid] >= target:
                hi = mid
            else:
                lo = mid
        for wi in range(waits.size):
            if play_one(hs, ds, as_, ends, reach[hi], hi, target, waits[wi]):
                fails[wi] += 1
    return fails, n_targets


@njit(cache=True)
def attack_longest(d_sym, a_sym, t_sym, burn, give_up):
    """Gaži, Ren and Russell's attack (§4.7, as ``grr_attack`` plays it) against waits. For each
    target symbol, the time from the previous symbol's close to the last symbol at which the
    attack holds two chains at or above the public depth: a wait fails exactly when it is at most
    that time. −1 where the attack never does; −2 for a target whose race outlasts the data."""
    n = d_sym.size
    longest = np.full(n, -2, np.int64)
    lead = 0
    for j0 in range(n):
        if j0 >= burn:
            x, y = lead, 0
            best = -1
            step = 0
            while j0 + step < n:
                d, a = d_sym[j0 + step], a_sym[j0 + step]
                if d < 0:
                    x += 1
                    y += 1
                else:
                    if y < 0:
                        s_tmp = y + a - d
                        l_tmp = max(0, x + a - d)
                    else:
                        s_tmp = max(0, y + a - d)
                        l_tmp = x + a - d
                    x, y = max(l_tmp, s_tmp), min(l_tmp, s_tmp)
                if y >= 0:
                    best = t_sym[j0 + step] - t_sym[j0 - 1]
                if y < -give_up:
                    break
                step += 1
            if j0 + step < n:
                longest[j0] = best
        d, a = d_sym[j0], a_sym[j0]
        lead = max(lead + a - max(d, 0), 0)
    return longest
