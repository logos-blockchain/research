"""The choices a delayed nonce leaves, counted when each candidate is formed (DESIGNS.md, H.2).

Under the delay of H.2 a candidate nonce's value reaches the coalition ``T_a = W + margin`` after
the candidate is formed, ``W`` the last sub-window. A candidate counts only if its value is seen
while the coalition can still make it the nonce (the lemma's ``r_eval``).

**The open event.** Back from the cut-off, a fork from depth ``d`` needs ``L_d + l >= 1``, with
``L_d`` B6's lead and ``l`` the coalition's lead over the canonical honest blocks after the
cut-off at the moment it publishes. A choice is still open ``T`` slots after the cut-off when
``max_d L_d + max_{s >= T} l(s) >= 1``. ``open_law`` gives its chance under random delay from B6's
walk: ``max_d L_d`` is the first lead plus the walk's all-time maximum, and ``max_{s >= T} l(s)``
is the lead after ``T`` slots plus a post-cut-off maximum ``Z``, all independent.
``formation_counts`` draws it slot by slot under either delay model, and its ``open_factor`` is
``E[1 + (G_min - 1)·1{open at T}]``, the factor of B7's per-win contributions were every candidate
formed at the sub-window's start.

**Formation times.** ``formation_counts`` follows each value the last sub-window's minimum can take
at the cut-off, counts it where the fork that reaches it can still be published when the value is
seen, and averages over windows drawn as ``finality_sim.nonce`` draws them. A fork from depth
``d`` may carry every coalition win after it that the value allows; this bounds the count from
above. A value below the floor ``θ_d``, the smallest honest contribution the fork keeps, counts
with chance ``θ_d``. The values and their formation:

- an honest minimum the fork keeps: when its block arrives;
- per win (B7's contribution, known ahead): at the sub-window's start;
- bound to the parent's win tag: a win on the honest fork point when that block arrives; a win on
  the coalition's own previous win at the sub-window's start, since both tags are known ahead;
- bound to the parent's contribution, chained: every value of a branch when its fork point
  arrives. A branch of two or more wins carries one value per prefix; a coalition with ``E``
  delay evaluators sees at most ``E`` of them, so the count reports the chance ``multi`` that such
  a branch is seen at all, and the factor is ``F + E·multi``.

The default, the honest chain's own minimum, counts too when its value is seen while a branch the
coalition has not seen can still replace it: it keeps the default or switches blind, which doubles
its chance in those windows (the lemma in DESIGNS.md H.2). A window whose deepest fork empties the
last sub-window counts in full, at B7's ``G_min``.

**The enumeration.** ``binding_counts`` counts, at the cut-off with no delay, the distinct values of
the last sub-window's minimum over every feasible fork and every subset of the coalition's wins
after it, under one contribution per win, per parent and per chain prefix.

**The evaluator term from the walk.** A branch is seen only ``W + margin`` after its fork point
arrives, and only if it can still be published then: the coalition's wins over those slots must
outnumber the canonical honest blocks. ``branch_survival`` is that chance; ``evaluator_bound``
takes it over the sub-window's fork points and adds the forks that empty the sub-window.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
from numba import njit
from scipy import stats

from finality_sim.fork_bound import blocks_pmf, crossing_chance
from finality_sim.grinding import _ladder, _renewal, post_cutoff, walk
from finality_sim.nonce import _choices_min, _rates

NONE = -(1 << 40)          # the suffix maximum past the end of a walk


@njit(cache=True)
def _draw(h, a, dead, near, canon, adv, path):
    """A window of ``near`` slots before the cut-off, as ``nonce._sample`` draws it, and the race
    after the cut-off: ``path[i]`` holds the coalition's lead after the win of post-cut-off slot
    ``i``, before its honest block. Returns ``Z`` and the slots followed."""
    last = 0
    for t in range(1, near):
        canon[t] = np.random.random() < h and t - last > dead
        if canon[t]:
            last = t
        adv[t] = np.random.random() < a
    lead, z, t, n = 0, 0, near, 0
    while lead > -60 and n < path.size:
        if np.random.random() < a:
            lead += 1
            z = max(z, lead)
        path[n] = lead
        if np.random.random() < h and t - last > dead:
            last = t
            lead -= 1
        n += 1
        t += 1
    return z, n


@njit(cache=True)
def _suffix_max(path, n, out):
    """``out[i] = max(path[i:n])`` for ``i < n``, and ``NONE`` beyond."""
    m = NONE
    for i in range(n - 1, -1, -1):
        if path[i] > m:
            m = path[i]
        if i < out.size:
            out[i] = m
    for i in range(n, out.size):
        out[i] = NONE


@njit(cache=True)
def _backward(canon, adv, hs, lead, w_after):
    """Back from the cut-off: the slots of the canonical honest blocks, the latest first, ending with
    the block at slot 0; ``lead[d]`` the coalition's wins after block ``d`` minus ``d``; for each win,
    the honest blocks after it. Returns the honest blocks before slot 0 and the wins."""
    nh, nw = 0, 0
    for t in range(canon.size - 1, 0, -1):
        if canon[t]:
            hs[nh] = t
            lead[nh] = nw - nh
            nh += 1
        if adv[t]:
            w_after[nw] = nh
            nw += 1
    hs[nh] = 0
    lead[nh] = nw - nh
    return nh, nw


@njit(cache=True)
def _deepest(suffix_lead, n, thr):
    """The deepest ``d < n`` with ``lead[d] >= thr``, from the suffix maxima of ``lead``; -1 if none."""
    if n == 0 or suffix_lead[0] < thr:
        return -1
    lo, hi = 0, n - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if suffix_lead[mid] >= thr:
            lo = mid
        else:
            hi = mid - 1
    return lo


def open_law(f: float, alpha: float, slots: int, growth: float, floor: int = 200) -> float:
    """P(a choice is still open ``slots`` slots after the cut-off) under random delay: the first
    lead ``L_0`` plus the walk's all-time maximum back from the cut-off, plus the lead after
    ``slots`` slots (a slot adds a win with chance ``a`` and removes a canonical block with chance
    ``h``), plus the maximum after it, distributed as ``Z``, reaching one."""
    a, h, _, _ = _rates(f, alpha, growth, None)
    first, step = walk(f, alpha, growth=growth)
    back = np.convolve(first, _renewal(_ladder(step, floor)))         # max_d L_d, from 0
    z = post_cutoff(f, alpha, growth=growth, floor=floor)              # from 0
    inc = np.array([(1 - a) * h, a * h + (1 - a) * (1 - h), a * (1 - h)])   # -1, 0, +1
    lead = np.array([1.0])                                             # index i holds i - slots
    if slots > 0:
        out, base, e = np.array([1.0]), inc, slots
        while e:                                                       # inc ** slots by squaring
            if e & 1:
                out = np.convolve(out, base)
            base = np.convolve(base, base)
            base[base < 1e-300] = 0.0
            e >>= 1
        lead = out
    up = np.convolve(back, z)                                          # index j holds j >= 0
    # P(up + lead >= 1), lead = i - slots
    cdf_up = np.cumsum(up[::-1])[::-1]                                 # P(up >= j)
    total = 0.0
    for i, p in enumerate(lead):
        need = 1 - (i - slots)
        total += p * (1.0 if need <= 0 else (cdf_up[need] if need < cdf_up.size else 0.0))
    return float(total)


@njit(cache=True)
def _window_counts(canon, adv, sm, near, sub, margins, h_rho, w_rho, far_min, z, feasible, hs,
                   lead, w_after, suffix_lead, theta, holder, wcount, honest_at_start, level=2):
    """For one window: B7's ``G_min``, whether the deepest fork empties the last sub-window, and for
    each margin the open event and the counts (see ``formation_counts``); ``level`` 0 stops after the
    open event, 1 leaves the pairs out."""
    nh, nw = _backward(canon, adv, hs, lead, w_after)
    for d in range(nh + 1):
        feasible[d] = d == 0 or lead[d] + z >= 1
    g, d_max = _choices_min(canon, adv, feasible, h_rho, w_rho, far_min, sub)
    best = NONE
    for d in range(nh + 1):
        best = max(best, lead[d])
    start = near - sub if sub < near else 1
    n0 = 0
    while n0 < nh and hs[n0] >= start:
        n0 += 1
    cross = d_max >= n0
    nm = margins.size
    open_ = np.zeros(nm, np.bool_)
    per_win = np.zeros(nm)
    honest = np.zeros(nm)
    singles = np.zeros(nm)
    pairs_hi = np.zeros(nm)
    pairs_lo = np.zeros(nm)
    multi = np.zeros(nm, np.bool_)
    blind_tag = np.zeros(nm)
    blind_chained = np.zeros(nm)
    for k in range(nm):
        open_[k] = best + sm[margins[k]] >= 1
    if cross or level == 0:
        return (g, cross, open_, per_win, honest, singles, pairs_hi, pairs_lo, multi, blind_tag,
                blind_chained)
    # floors: theta[d] the smallest contribution the fork from depth d keeps, held by holder[d]
    m = 2.0
    for d in range(n0 - 1, -1, -1):
        if h_rho[d] < m:
            m = h_rho[d]
            holder[d] = d
        else:
            holder[d] = holder[d + 1]
        theta[d] = m
    m = NONE
    for d in range(n0 - 1, -1, -1):
        m = max(m, lead[d])
        suffix_lead[d] = m                     # max over depths d..n0-1 of the lead
    w = 0
    for d in range(n0):                        # wcount[d]: the wins after block d
        while w < nw and w_after[w] <= d:
            w += 1
        wcount[d] = w
    w_n0 = wcount[n0 - 1] if n0 > 0 else 0
    for k in range(nm):
        t = margins[k]
        # honest minima: each record beyond the default, seen when its block arrives
        prev = holder[0]
        d = prev + 1
        while d < n0:
            j = holder[d]                      # the record held over depths d..j
            best_d = NONE
            for dd in range(d, j + 1):
                best_d = max(best_d, lead[dd])
            idx = t + (0 if honest_at_start else hs[j] - start)
            if idx < sm.size and best_d + sm[idx] >= 1:
                honest[k] += 1.0
            d = j + 1
        # per win, known ahead: seen at the margin; the deepest fork reachable then
        ds = _deepest(suffix_lead, n0, 1 - sm[t]) if sm[t] > NONE else -1
        if ds >= 0:
            for w in range(nw):
                if w_after[w] <= ds and w_rho[w] < theta[ds]:
                    per_win[k] += 1.0
        # the default, the smallest honest contribution, is seen at idx0; a branch from a fork point
        # newer than its holder that can still be published then, but no longer when its own values
        # are seen, lets the coalition keep the default or switch to a value it has not seen
        j0 = holder[0]
        idx0 = t + (0 if honest_at_start else hs[j0] - start)
        if idx0 < sm.size and sm[idx0] > NONE:
            for d in range(j0):
                w_d = wcount[d]
                idx = t + hs[d] - start
                if w_d == 0 or lead[d] + sm[idx0] < 1 or (idx < sm.size and lead[d] + sm[idx] >= 1):
                    continue
                blind_tag[k] += w_d * theta[0]
                blind_chained[k] += (2.0 ** min(w_d, 60) - 1.0) * theta[0]
            blind_tag[k] = min(1.0, blind_tag[k])
            blind_chained[k] = min(1.0, blind_chained[k])
        # the first win of a branch, on the honest fork point: seen when the fork point arrives
        for d in range(n0):
            idx = t + hs[d] - start
            if idx >= sm.size or sm[idx] == NONE:
                continue
            w_d = wcount[d]
            if w_d == 0 or lead[d] + sm[idx] < 1:
                continue
            # wins 0..i on the fork point d (the latest first): |S| = i + 1, needs i + 1 - d + sm >= 1
            lo_i = max(0, d - sm[idx])
            if lo_i <= w_d - 1:
                singles[k] += (w_d - lo_i) * theta[d]
            if w_d >= 2:
                multi[k] = True
        # a win on the coalition's own previous win (parent tag): known ahead, seen at the margin
        if level >= 2 and sm[t] > NONE:
            for i2 in range(w_n0):                 # the earlier win w' = i2, the later w = i1 < i2
                for i1 in range(i2):
                    gap = i2 - i1 - 1
                    ds2 = _deepest(suffix_lead, n0, 1 + gap - sm[t])
                    if ds2 < 0 or w_after[i2] > ds2:
                        continue
                    th = theta[ds2]
                    pairs_hi[k] += th
                    size = wcount[ds2] - gap
                    pairs_lo[k] += (1.0 - (1.0 - th) ** size) / size
    return (g, cross, open_, per_win, honest, singles, pairs_hi, pairs_lo, multi, blind_tag,
            blind_chained)


@njit(cache=True)
def _formation_sample(n_samples, h, a, dead, near, sub, far_h, margins, seed, honest_at_start, level):
    np.random.seed(seed)
    nm = margins.size
    g_out = np.empty(n_samples)
    cross_out = np.zeros(n_samples, np.bool_)
    open_out = np.zeros((n_samples, nm), np.bool_)
    win_out = np.zeros((n_samples, nm))
    hon_out = np.zeros((n_samples, nm))
    sgl_out = np.zeros((n_samples, nm))
    phi_out = np.zeros((n_samples, nm))
    plo_out = np.zeros((n_samples, nm))
    mul_out = np.zeros((n_samples, nm), np.bool_)
    btg_out = np.zeros((n_samples, nm))
    bch_out = np.zeros((n_samples, nm))
    canon = np.zeros(near, np.bool_)
    adv = np.zeros(near, np.bool_)
    feasible = np.zeros(near + 1, np.bool_)
    path = np.empty(400_000, np.int64)
    span = int(margins.max()) + sub + 2
    sm = np.empty(max(span, 1), np.int64)
    hs = np.empty(near + 1, np.int64)
    lead = np.empty(near + 1, np.int64)
    w_after = np.empty(near, np.int64)
    suffix_lead = np.empty(near + 1, np.int64)
    theta = np.empty(near + 1)
    holder = np.empty(near + 1, np.int64)
    wcount = np.empty(near + 1, np.int64)
    for s in range(n_samples):
        z, n = _draw(h, a, dead, near, canon, adv, path)
        _suffix_max(path, n, sm)
        nh = 0
        nw = 0
        for t in range(1, near):
            if canon[t]:
                nh += 1
            if adv[t]:
                nw += 1
        far_min = np.inf if far_h == 0 else 1.0 - np.random.random() ** (1.0 / far_h)
        h_rho = np.random.random(nh)
        w_rho = np.random.random(nw)
        r = _window_counts(canon, adv, sm, near, sub, margins, h_rho, w_rho, far_min, z, feasible, hs,
                           lead, w_after, suffix_lead, theta, holder, wcount, honest_at_start, level)
        g_out[s], cross_out[s] = r[0], r[1]
        open_out[s], win_out[s], hon_out[s] = r[2], r[3], r[4]
        sgl_out[s], phi_out[s], plo_out[s], mul_out[s] = r[5], r[6], r[7], r[8]
        btg_out[s], bch_out[s] = r[9], r[10]
    return g_out, cross_out, open_out, win_out, hon_out, sgl_out, phi_out, plo_out, mul_out, btg_out, bch_out


def formation_counts(f: float, alpha: float, window_slots: int, sub_windows: int, margins_slots,
                     n_samples: int, seed: int, growth: float | None = None, delta: int | None = None,
                     near_slots: int = 20_000, honest_at_start: bool = False, level: int = 2) -> dict:
    """Per window and margin, as ``formation_counts`` in the module's docstring:

    - ``g``: B7's ``G_min``; ``cross``: the deepest fork empties the last sub-window;
    - ``open``: a choice is still open at the margin;
    - ``open_factor``: ``1 + (G_min - 1)·1{open}``, every value formed at the sub-window's start;
    - ``per_win``, ``tag`` (from above), ``tag_lo`` (each pair with every other admissible win
      above it, and no blind switch), ``chained``: ``1 +`` the values seen while reachable, plus the
      chance of a blind switch, a crossing window at ``G_min``;
    - ``blind_tag``, ``blind_chained``: the chance, by a union bound over the branches' values below
      the default, that the default is seen while a branch the coalition has not seen can still
      replace it;
    - ``multi``: a branch of two or more wins on a fork point of the sub-window is seen while it can
      still be published, or the window crosses.

    ``honest_at_start`` forms the honest minima at the sub-window's start too (for the gates);
    ``level`` 0 computes the open event alone, 1 everything but the pairs."""
    a, h, dead, rate = _rates(f, alpha, growth, delta)
    sub = window_slots // sub_windows
    near = min(near_slots, window_slots)
    far_slots = min(((near - 2) // sub + 1) * sub, window_slots) - near + 1
    ms = np.asarray(margins_slots, dtype=np.int64)
    g, cross, op, win, hon, sgl, phi, plo, mul, btg, bch = _formation_sample(
        n_samples, h, a, dead, near, sub, int(round(far_slots * rate)), ms, seed, honest_at_start, level)
    full = g[:, None]
    c = cross[:, None]
    return dict(g=g, cross=cross, open=op,
                open_factor=1.0 + (full - 1.0) * op,
                per_win=np.where(c, full, 1.0 + hon + win),
                tag=np.where(c, full, 1.0 + hon + sgl + phi + btg),
                tag_lo=np.where(c, full, 1.0 + hon + sgl + plo),
                chained=np.where(c, full, 1.0 + hon + sgl + bch),
                blind_tag=np.where(c, 0.0, btg), blind_chained=np.where(c, 0.0, bch),
                multi=mul | c)


def open_curve(f: float, alpha: float, max_slots: int, n_samples: int, seed: int,
               growth: float | None = None, delta: int | None = None, step: int = 60):
    """The share of ``n_samples`` windows still open ``t`` slots after the cut-off, for ``t`` from 0 to
    ``max_slots`` every ``step`` slots."""
    ts = np.arange(0, max_slots + 1, step)
    r = formation_counts(f, alpha, 25 * 6_000, 25, ts, n_samples, seed, growth=growth, delta=delta,
                         near_slots=6_000, level=0)
    return ts, r["open"].mean(axis=0)


def blind_bound(ts, shares, margin_slots: int, sub_slots: int) -> float:
    """An upper bound on the chance of a blind switch: the default's holder arrives anywhere in the
    sub-window, so its value is seen ``margin + u`` after the cut-off with ``u`` spread evenly over the
    sub-window, and a switch needs a choice still open then. The mean of the open chance over
    ``[margin, margin + sub)``, from ``open_curve``."""
    inside = (ts >= margin_slots) & (ts < margin_slots + sub_slots)
    return float(shares[inside].sum() * (ts[1] - ts[0]) / sub_slots)


def branch_survival(f: float, alpha: float, slots: int, growth: float | None = None,
                    delta: int | None = None, floor: int = 200) -> float:
    """P(a branch from an honest block can still be published ``slots`` slots later): the
    coalition's wins over the slots, less the canonical honest blocks after the block, plus the most
    it gains afterwards, a whole gap's wins and the walk's maximum, reach one."""
    a, _, _, _ = _rates(f, alpha, growth, delta)
    _, step = walk(f, alpha, growth, delta)
    after = np.convolve(step, _renewal(_ladder(step, floor)))
    wins = stats.binom.pmf(np.arange(slots + 1), slots, a)
    up = np.convolve(wins, after)                                     # index j: wins + after = j
    blocks = blocks_pmf(slots, f, alpha, growth, delta)
    tail = np.cumsum(up[::-1])[::-1]                                  # P(up >= j)
    n = np.arange(blocks.size)
    need = n + 1
    ok = need < tail.size
    return float(np.sum(blocks[ok] * tail[need[ok]]))


def evaluator_bound(f: float, alpha: float, sub_slots: int, margin_slots: int,
                    growth: float | None = None, delta: int | None = None) -> dict:
    """An upper bound on ``multi``: every fork point of the sub-window, ``E[N] + 1`` of them, has its
    branch survive ``sub_slots + margin_slots`` slots, or the deepest fork empties the sub-window."""
    _, _, _, rate = _rates(f, alpha, growth, delta)
    survive = branch_survival(f, alpha, sub_slots + margin_slots, growth, delta)
    cross = crossing_chance(f, alpha, sub_slots, growth, delta)
    inside = (sub_slots * rate + 1.0) * survive
    return dict(survive=survive, inside=inside, cross=cross, bound=min(1.0, inside + cross))


# The enumeration at the cut-off.

@njit(cache=True)
def _enumeration_windows(n_samples, h, a, dead, near, sub, seed, max_w):
    """Per window: ``Z``, the deepest feasible fork, the honest blocks of the last sub-window, the
    honest blocks after each coalition win after the deepest fork point, the latest first, and the
    coalition's wins in the last sub-window."""
    np.random.seed(seed)
    zs = np.empty(n_samples, np.int64)
    dmax = np.empty(n_samples, np.int64)
    n0s = np.empty(n_samples, np.int64)
    wafter = np.full((n_samples, max_w), -1, np.int64)
    a0s = np.zeros(n_samples, np.int64)
    canon = np.zeros(near, np.bool_)
    adv = np.zeros(near, np.bool_)
    feasible = np.zeros(near + 1, np.bool_)
    path = np.empty(400_000, np.int64)
    hs = np.empty(near + 1, np.int64)
    lead = np.empty(near + 1, np.int64)
    w_after = np.empty(near, np.int64)
    start = near - sub if sub < near else 1
    for s in range(n_samples):
        z, _ = _draw(h, a, dead, near, canon, adv, path)
        nh, nw = _backward(canon, adv, hs, lead, w_after)
        d_max = 0
        for d in range(nh, -1, -1):
            if d == 0 or lead[d] + z >= 1:
                d_max = d
                break
        n0 = 0
        while n0 < nh and hs[n0] >= start:
            n0 += 1
        zs[s], dmax[s], n0s[s] = z, d_max, n0
        for t in range(start, near):
            a0s[s] += adv[t]
        k = 0
        for w in range(nw):
            if w_after[w] <= d_max and k < max_w:
                wafter[s, k] = w_after[w]
                k += 1
    return zs, dmax, n0s, wafter, a0s


def distinct_minima(z: int, d_max: int, n0: int, w_after, rng, cap: int, any_subset: bool = False):
    """The distinct values of the last sub-window's minimum over every feasible fork and every subset
    of the coalition's wins after it: one contribution per win, per (win, parent) with the parent the
    fork point or the previous win of the subset, and per (win, fork point, earlier wins of the
    subset). ``None`` past ``cap`` subsets, ``"cross"`` when the deepest fork empties the sub-window.
    A fork from depth ``d >= 1`` needs ``j + z >= d + 1`` of its wins; ``any_subset`` drops that, as
    B7's count does."""
    if d_max >= n0:
        return "cross"
    wins = [int(x) for x in w_after if x >= 0]
    feas = [0] + [d for d in range(1, d_max + 1) if sum(1 for x in wins if x <= d) - d + z >= 1]
    total = 0
    for d in feas:
        wd = sum(1 for x in wins if x <= d)
        jmin = 0 if (d == 0 or any_subset) else max(0, d + 1 - z)
        total += sum(math.comb(wd, j) for j in range(jmin, wd + 1))
        if total > cap:
            return None
    rho = rng.random(n0)
    floor = np.minimum.accumulate(rho[::-1])[::-1]                    # kept minimum at each depth
    per_win = {w: rng.random() for w in range(len(wins))}
    per_parent, per_prefix = {}, {}
    out = {"per_win": set(), "per_parent": set(), "per_prefix": set()}
    for d in feas:
        kept = floor[d]
        after = [i for i, x in enumerate(wins) if x <= d][::-1]        # the oldest first
        jmin = 0 if (d == 0 or any_subset) else max(0, d + 1 - z)
        for j in range(jmin, len(after) + 1):
            for chosen in itertools.combinations(after, j):
                m1 = m2 = m3 = kept
                prev = ("h", d)
                for pos, w in enumerate(chosen):
                    m1 = min(m1, per_win[w])
                    m2 = min(m2, per_parent.setdefault((w, prev), rng.random()))
                    m3 = min(m3, per_prefix.setdefault((w, d, chosen[:pos]), rng.random()))
                    prev = ("w", w)
                out["per_win"].add(m1)
                out["per_parent"].add(m2)
                out["per_prefix"].add(m3)
    return {k: len(v) for k, v in out.items()}


def binding_counts(f: float, alpha: float, window_slots: int, sub_windows: int, n_samples: int,
                   seed: int, growth: float | None = None, delta: int | None = None,
                   near_slots: int = 20_000, cap: int = 200_000) -> dict:
    """``distinct_minima`` over ``n_samples`` windows; windows that cross or pass ``cap`` are counted
    apart and left out of the means."""
    a, h, dead, _ = _rates(f, alpha, growth, delta)
    sub = window_slots // sub_windows
    near = min(near_slots, window_slots)
    zs, dmax, n0s, wafter, _ = _enumeration_windows(n_samples, h, a, dead, near, sub, seed, 400)
    rng = np.random.default_rng(seed + 1)
    res = {"per_win": [], "per_parent": [], "per_prefix": []}
    crossed = skipped = 0
    for s in range(n_samples):
        c = distinct_minima(int(zs[s]), int(dmax[s]), int(n0s[s]), wafter[s], rng, cap)
        if c == "cross":
            crossed += 1
        elif c is None:
            skipped += 1
        else:
            for key in res:
                res[key].append(c[key])
    return {k: np.array(v, float) for k, v in res.items()} | dict(crossed=crossed, skipped=skipped)
