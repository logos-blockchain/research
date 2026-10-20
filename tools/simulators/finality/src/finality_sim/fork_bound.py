"""A bound on the choices at the cut-off from B6's walk alone (DESIGNS.md, H.2).

B7 samples ``G_min``, the nonces a coalition can still reach at the cut-off, over windows drawn
slot by slot (``finality_sim.nonce``). Given the slots, the contributions are independent uniforms,
so their expectation has a closed form. With ``N`` canonical blocks in a sub-window, the deepest
feasible fork dropping ``D`` of them and the coalition holding ``A`` wins after its fork point,
the kept minimum changes at the dropped block ``j`` (counted from the cut-off) with chance
``1/(N - j)``, and a win lies below the floor the deepest fork keeps with chance ``1/(N - D + 1)``::

    E[G_min | slots] = 1 + sum_{j < D} 1/(N - j) + A / (N - D + 1)

when the fork stays within the last sub-window, and the product of such factors over the
sub-windows it reaches otherwise. ``conditional_mean`` averages this over sampled slots, counting
a change of the kept minimum at every dropped block, which the sampler's count reaches when every
depth down to the deepest is feasible. ``gmin_bound`` bounds the expectation from B6's walk alone.
The walk descends by at most one per block, so a deepest feasible fork ``D >= 1`` sits where the
lead equals ``1 - Z``, the next gap holds no win and the walk never rises again, and there
``A = D + 1 - Z``; ``D = 0`` leaves ``A = L_0 <= 1``. On ``N >= N_lo`` the kept blocks number at
least ``N_lo - D``, so the sum above is at most ``H(N_lo) - H(N_lo - D) + A/(N_lo - D + 1)``. A
fork that stays in the sub-window leaves at most ``H(N_max) + A`` whatever ``N`` and ``D``, with
``A <= D + 1``; a fork that crosses into the previous sub-window is bounded apart (``_crossing``).
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit
from scipy import stats

from finality_sim.grinding import _ladder, _renewal, post_cutoff, walk
from finality_sim.nonce import _choices_min, _feasible, _rates


def deepest_fork(f: float, alpha: float, growth: float | None = None, delta: int | None = None,
                 d_max: int = 800, floor: int = 200) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """For ``d = 0..d_max``: ``P(D = d)``, ``E[A; D = d]`` and ``E[A^2; D = d]``, with ``D`` the
    deepest feasible fork and ``A`` the coalition's wins after its fork point.

    ``P(D = d | Z) = P(L_d = 1 - Z) P(Y = 0) P(M = 0)`` for ``d >= 1``, with ``L_d`` the lead ``d``
    blocks back, ``Y`` the wins of a gap and ``M`` the all-time maximum of the walk from zero; and
    ``P(D = 0, L_0 = l | Z) = P(L_0 = l) P(Y + M <= 1 - Z - l)``. ``Z`` is B6's lead after the
    cut-off, from above under a worst case."""
    first, step = walk(f, alpha, growth, delta)
    pz = post_cutoff(f, alpha, growth, delta, floor=floor)
    pm = _renewal(_ladder(step, floor))
    stay = float(pm[0])
    cdf_t = np.cumsum(np.convolve(step, pm))                        # P(Y + M <= t)
    zs = np.arange(pz.size)
    p = np.zeros(d_max + 1)
    a1 = np.zeros(d_max + 1)
    a2 = np.zeros(d_max + 1)
    for lead in range(first.size):                                   # D = 0: A = L_0
        c = 1 - zs - lead
        ok = c >= 0
        if not ok.any():
            continue
        w = pz[ok] * first[lead] * cdf_t[np.minimum(c[ok], cdf_t.size - 1)]
        p[0] += w.sum()
        a1[0] += w.sum() * lead
        a2[0] += w.sum() * lead * lead
    lead_pmf = first                                                 # index i holds L_d = i - d
    for d in range(1, d_max + 1):
        lead_pmf = np.convolve(lead_pmf, step)
        idx = 1 - zs + d
        ok = (idx >= 0) & (idx < lead_pmf.size)
        w = pz[ok] * lead_pmf[idx[ok]] * step[0] * stay
        a = d + 1 - zs[ok]
        p[d] = w.sum()
        a1[d] = float(np.sum(w * a))
        a2[d] = float(np.sum(w * a * a))
    return p, a1, a2


def blocks_pmf(slots: int, f: float, alpha: float, growth: float | None = None,
               delta: int | None = None) -> np.ndarray:
    """The pmf of the canonical honest blocks in ``slots`` slots that start at a block: the
    ``n``-th block arrives once ``n`` gaps, each the dead time plus a geometric number of slots,
    have passed. A window that starts anywhere holds at least as many, since the first gap is
    then no longer than a whole one; under random delay it is the binomial law itself."""
    _, h, dead, _ = _rates(f, alpha, growth, delta)
    n = np.arange(slots // (dead + 1) + 2)
    at_least = np.concatenate(([1.0], stats.nbinom.cdf(slots - n[1:] * (dead + 1), n[1:], h)))
    return np.diff(np.concatenate((at_least, [0.0]))) * -1.0


def blocks_below(slots: int, n_lo: int, f: float, alpha: float, growth: float | None = None,
                 delta: int | None = None) -> float:
    """An upper bound on ``P(N < n_lo)`` for the canonical honest blocks ``N`` of a window of
    ``slots`` slots, from ``blocks_pmf``."""
    _, h, dead, _ = _rates(f, alpha, growth, delta)
    return float(stats.nbinom.sf(slots - n_lo * (dead + 1), n_lo, h))


def _previous_law(step, stay, o_lo, o_max, depth):
    """For each offset ``o`` from ``o_lo`` to ``o_max``, row ``o - o_lo``: the pmf of ``D_1``, the deepest
    feasible fork counted back from the previous sub-window's last block, at ``j = 0..depth``. The walk
    from the boundary is ``V_j = Y_0 + ... + Y_j - j``, the first gap taken whole; a fork from ``j``
    wins when ``o + V_j >= 1``, and ``D_1 = j`` when ``o + V_j = 1``, the next gap holds no win and the
    walk never rises again. A row sums to the chance that the fork crosses at all, one for ``o >= 1``."""
    os_ = np.arange(o_lo, o_max + 1)
    q = np.zeros((os_.size, depth + 1))
    lead = step.copy()                                                # Y_0 + ... + Y_j at index v + j
    for j in range(depth + 1):
        if j:
            lead = np.convolve(lead, step)
        idx = 1 - os_ + j
        ok = (idx >= 0) & (idx < lead.size)
        q[ok, j] = lead[idx[ok]] * step[0] * stay
    return os_, q


def _crossing_parts(f, alpha, sub_slots, n_lo, growth, delta, floor, harmonic, c):
    """The pieces of ``_crossing``: the offsets ``o`` and, at each, ``phi``, the bound on the previous
    sub-window's factor times the chance that the fork crosses, and that chance; the laws of ``Z``, of
    the sub-window's blocks ``N`` and of the coalition's wins ``A_0`` in it (values and weights)."""
    a, _, _, _ = _rates(f, alpha, growth, delta)
    _, step = walk(f, alpha, growth, delta)
    pz = post_cutoff(f, alpha, growth, delta, floor=floor)
    pm = _renewal(_ladder(step, floor))
    stay = float(pm[0])
    p_n = blocks_pmf(sub_slots, f, alpha, growth, delta)
    p_w = stats.binom.pmf(np.arange(sub_slots + 1), sub_slots, a)
    keep = np.nonzero(p_w > 1e-18)[0]
    p_w, ws = p_w[keep], keep
    o_max = int(ws.max() + pz.size)
    rises = np.cumsum(np.convolve(step, pm)[::-1])[::-1]              # P(Y_0 + M >= t)
    o_lo = 1 - int(np.nonzero(rises > 1e-18)[0].max())
    p_low = blocks_below(sub_slots, n_lo, f, alpha, growth, delta)
    os_, q = _previous_law(step, stay, o_lo, o_max, 4 * n_lo)
    js = np.arange(q.shape[1])
    a1 = np.maximum(js[None, :] + 1 - os_[:, None], 0)               # A_1 given D_1 = j
    short = js < n_lo
    val = np.where(short[None, :],
                   1.0 + harmonic[n_lo] - harmonic[n_lo - np.minimum(js, n_lo)][None, :]
                   + a1 / (n_lo - np.minimum(js, n_lo) + 1)[None, :],
                   (c + a1) ** 2)
    mass = q.sum(axis=1)
    phi = (q * val).sum(axis=1) + (c + n_lo) ** 2 * np.minimum(p_low, mass)
    return os_, phi, mass, pz, p_n, ws, p_w


def _crossing_sum(os_, values, pz, p_n, ws, p_w, weight):
    """``sum over A_0, Z, N of P(A_0) P(Z) P(N) weight(A_0) values[A_0 + Z - N]``, zero below ``os_[0]``."""
    total = 0.0
    ns = np.arange(p_n.size)
    zs = np.arange(pz.size)
    for w, pw in zip(ws, p_w):
        o = w + zs[:, None] - ns[None, :] - os_[0]
        inside = o >= 0
        v = np.where(inside, values[np.clip(o, 0, values.size - 1)], 0.0)
        total += pw * weight(w) * float(np.sum(pz[:, None] * p_n[None, :] * v))
    return total


def _emptied(c):
    """The bound on the factor of a sub-window the fork empties, as a function of the coalition's
    wins ``A_0`` in it: ``c`` for the minima of its honest blocks and one per win."""
    return lambda w: c + w


def _crossing(f, alpha, sub_slots, n_lo, growth, delta, floor, harmonic, c):
    """``E[G_min; the deepest fork reaches the previous sub-window]`` from above.

    The fork crosses when the coalition's wins in the sub-window, ``A_0``, its lead after the cut-off
    ``Z`` and the previous sub-window's walk reach the sub-window's blocks ``N``: with the offset
    ``o = A_0 + Z - N``, when ``o + max_j V_j >= 1`` (``_previous_law``), which a positive offset
    always meets and a negative one through the previous sub-window's wins. ``A_0``, ``Z`` and ``N``
    are independent. The emptied sub-window's factor is at most ``c + A_0``, every win being below a
    floor of nothing. In the previous sub-window the deepest feasible fork ``D_1`` and the wins after
    it, ``A_1 = D_1 + 1 - o``, follow ``_previous_law``; its factor is bounded as the main term bounds
    the last sub-window's, with a square beyond ``n_lo`` blocks."""
    os_, phi, _, pz, p_n, ws, p_w = _crossing_parts(f, alpha, sub_slots, n_lo, growth, delta, floor,
                                                     harmonic, c)
    return _crossing_sum(os_, phi, pz, p_n, ws, p_w, _emptied(c))


def crossing_chance(f: float, alpha: float, sub_slots: int, growth: float | None = None,
                    delta: int | None = None, floor: int = 200) -> float:
    """P(the deepest feasible fork empties a sub-window of ``sub_slots`` slots), from the law the
    crossing term uses: exact under random delay, from above under a worst case."""
    _, _, dead, rate = _rates(f, alpha, growth, delta)
    n_lo = max(1, int(0.7 * sub_slots * rate))
    n_max = sub_slots // (dead + 1) + 1 if dead else sub_slots
    harmonic = np.concatenate(([0.0], np.cumsum(1.0 / np.arange(1, n_max + 2))))
    os_, _, mass, pz, p_n, ws, p_w = _crossing_parts(f, alpha, sub_slots, n_lo, growth, delta, floor,
                                                      harmonic, 1.0 + harmonic[n_max])
    return _crossing_sum(os_, mass, pz, p_n, ws, p_w, lambda w: 1.0)


def gmin_bound(f: float, alpha: float, sub_slots: int, n_lo: int, growth: float | None = None,
               delta: int | None = None, d_max: int = 800, floor: int = 200,
               n_lo_prev: int | None = None) -> dict:
    """An upper bound on ``E[G_min]`` for a sub-window of ``sub_slots`` slots, split at ``n_lo``
    blocks: the main term on ``N >= n_lo, D < n_lo``; the forks of ``D >= n_lo``, linear; the
    windows of ``N < n_lo``, linear; and the forks that cross into the previous sub-window, whose
    blocks are split at ``n_lo_prev`` (``n_lo`` by default; the two splits are chosen apart); with
    ``E[D]`` and ``E[A]``."""
    p, a1, a2 = deepest_fork(f, alpha, growth, delta, d_max=d_max, floor=floor)
    _, _, dead, _ = _rates(f, alpha, growth, delta)
    n_max = sub_slots // (dead + 1) + 1 if dead else sub_slots
    harmonic = np.concatenate(([0.0], np.cumsum(1.0 / np.arange(1, n_max + 2))))
    ds = np.arange(n_lo)
    main = float(np.sum(p[:n_lo] * (harmonic[n_lo] - harmonic[n_lo - ds]) + a1[:n_lo] / (n_lo - ds + 1)))
    c = 1.0 + harmonic[n_max]
    tail_d = float(np.sum(p[n_lo:] * (c - 1.0) + a1[n_lo:]))
    p_low = blocks_below(sub_slots, n_lo, f, alpha, growth, delta)
    tail_n = (c - 1.0 + n_lo) * p_low
    cross = _crossing(f, alpha, sub_slots, n_lo if n_lo_prev is None else n_lo_prev, growth, delta,
                      floor, harmonic, c)
    return dict(bound=1.0 + main + tail_d + tail_n + cross, main=main, tail_d=tail_d, tail_n=tail_n,
                cross=cross, p_low=p_low, e_d=float(np.sum(np.arange(p.size) * p)),
                e_a=float(a1.sum()), mass=float(p.sum()))


@njit(cache=True)
def _conditional_choices(canon, adv, feasible, far_h, sub):
    """``E[G_min | slots]``, counting a change of the kept minimum at every dropped block, and the
    deepest feasible fork; the arguments are ``_choices_min``'s."""
    n = canon.size
    n_sub = (n - 2) // sub + 1
    nh, nw = 0, 0
    for t in range(n - 1, 0, -1):
        if canon[t]:
            nh += 1
        if adv[t]:
            nw += 1
    sub_of = np.empty(nh, np.int64)
    w_after = np.empty(nw, np.int64)
    w_sub = np.empty(nw, np.int64)
    blocks = np.zeros(n_sub, np.int64)
    i_h, i_w = 0, 0
    for t in range(n - 1, 0, -1):
        i = (n - 1 - t) // sub
        if canon[t]:
            sub_of[i_h] = i
            blocks[i] += 1
            i_h += 1
        if adv[t]:
            w_after[i_w] = i_h
            w_sub[i_w] = i
            i_w += 1
    blocks[n_sub - 1] += far_h
    d_max = 0
    for d in range(nh, -1, -1):
        if feasible[d]:
            d_max = d
            break
    older = np.zeros(n_sub, np.int64)                  # blocks of each sub-window older than block j
    for i in range(n_sub):
        older[i] = blocks[i]
    records = np.zeros(n_sub)
    for j in range(nh):                                # from the cut-off back
        i = sub_of[j]
        older[i] -= 1                                  # blocks of i with index >= j, minus j itself
        if j < d_max:
            records[i] += 1.0 / (older[i] + 1)         # j is the smallest of the blocks of i at or beyond it
    kept = np.zeros(n_sub, np.int64)
    for i in range(n_sub):
        kept[i] = blocks[i]
    for j in range(min(d_max, nh)):
        kept[sub_of[j]] -= 1
    below = np.zeros(n_sub)
    for w in range(nw):
        if w_after[w] <= d_max:
            below[w_sub[w]] += 1.0 / (kept[w_sub[w]] + 1)
    top = sub_of[d_max] if d_max < nh else n_sub - 1
    g = 1.0
    for i in range(top + 1):
        g *= 1.0 + records[i] + below[i]
    return g, d_max


@njit(cache=True)
def _conditional_sample(n_samples, h, a, dead, near_slots, sub, far_h, seed):
    np.random.seed(seed)
    cond = np.empty(n_samples)
    drawn = np.empty(n_samples)
    canon = np.zeros(near_slots, np.bool_)
    adv = np.zeros(near_slots, np.bool_)
    feasible = np.zeros(near_slots + 1, np.bool_)
    for s in range(n_samples):
        last = 0
        nh, nw = 0, 0
        for t in range(1, near_slots):
            canon[t] = np.random.random() < h and t - last > dead
            if canon[t]:
                last = t
                nh += 1
            adv[t] = np.random.random() < a
            if adv[t]:
                nw += 1
        lead, z, t = 0, 0, near_slots
        while lead > -60:
            if np.random.random() < a:
                lead += 1
                z = max(z, lead)
            if np.random.random() < h and t - last > dead:
                last = t
                lead -= 1
            t += 1
        _feasible(canon, adv, z, feasible)
        far_min = np.inf if far_h == 0 else 1.0 - np.random.random() ** (1.0 / far_h)
        g, _ = _choices_min(canon, adv, feasible, np.random.random(nh), np.random.random(nw), far_min, sub)
        drawn[s] = g
        cond[s], _ = _conditional_choices(canon, adv, feasible, far_h, sub)
    return cond, drawn


@njit(cache=True)
def _structure_sample(n_samples, h, a, dead, near_slots, seed):
    """The deepest feasible fork, the wins after its fork point and the lead after the cut-off of
    ``n_samples`` windows drawn as ``_conditional_sample`` draws them."""
    np.random.seed(seed)
    d_out = np.empty(n_samples, np.int64)
    a_out = np.empty(n_samples, np.int64)
    z_out = np.empty(n_samples, np.int64)
    canon = np.zeros(near_slots, np.bool_)
    adv = np.zeros(near_slots, np.bool_)
    feasible = np.zeros(near_slots + 1, np.bool_)
    for s in range(n_samples):
        last = 0
        for t in range(1, near_slots):
            canon[t] = np.random.random() < h and t - last > dead
            if canon[t]:
                last = t
            adv[t] = np.random.random() < a
        lead, z, t = 0, 0, near_slots
        while lead > -60:
            if np.random.random() < a:
                lead += 1
                z = max(z, lead)
            if np.random.random() < h and t - last > dead:
                last = t
                lead -= 1
            t += 1
        nh = _feasible(canon, adv, z, feasible)
        d_max = 0
        for d in range(nh, -1, -1):
            if feasible[d]:
                d_max = d
                break
        wins, d = 0, 0
        for tt in range(near_slots - 1, 0, -1):
            if canon[tt]:
                d += 1
            if adv[tt] and d <= d_max:
                wins += 1
        d_out[s], a_out[s], z_out[s] = d_max, wins, z
    return d_out, a_out, z_out


def fork_sample(f: float, alpha: float, n_samples: int, seed: int, growth: float | None = None,
                delta: int | None = None, near_slots: int = 20_000):
    """Sampled ``(D, A, Z)`` of ``deepest_fork``'s law, one triple per window."""
    a, h, dead, _ = _rates(f, alpha, growth, delta)
    return _structure_sample(n_samples, h, a, dead, near_slots, seed)


def conditional_mean(f: float, alpha: float, window_slots: int, n_samples: int, seed: int,
                     sub_windows: int = 1, growth: float | None = None, delta: int | None = None,
                     near_slots: int = 20_000) -> tuple[np.ndarray, np.ndarray]:
    """For ``n_samples`` windows drawn as ``nonce.min_rule_choices`` draws them: ``E[G_min | slots]``
    and the ``G_min`` the sampler counts on the same window."""
    a, h, dead, rate = _rates(f, alpha, growth, delta)
    sub = window_slots // sub_windows
    near = min(near_slots, window_slots)
    far_slots = min(((near - 2) // sub + 1) * sub, window_slots) - near + 1
    return _conditional_sample(n_samples, h, a, dead, near, sub, int(round(far_slots * rate)), seed)
