"""Phase B7: an epoch nonce taken from the smallest contributions (PLAN.md, B7).

Today's epoch nonce is a hash chain over the blocks before the cut-off, so a coalition that
withholds its wins picks among every chain it can end there (``finality_sim.grinding``). The rule
studied here splits the window before the cut-off into ``m`` sub-windows of equal length, counted
back from the cut-off, and takes the smallest contribution ``rho_LEAD`` among the canonical blocks
of each: ``eta_e = H(eta_(e-1) || mu_1 || ... || mu_m)``. Contributions are independent and
uniform.

At the cut-off the coalition knows every contribution. It can fork from the honest block ``d``
canonical blocks before the cut-off when its wins since then and its lead after the cut-off outnumber
the honest blocks it drops (``L_d + Z >= 1``, as in ``finality_sim.grinding``), and it may place any
of its wins after the fork point. The deepest such fork point bounds what it can still change at the
cut-off: every contribution before it, its own included, is fixed by then. In each sub-window after
that point, ``mu`` is one of

- the minima over the honest blocks each feasible fork keeps there, or none;
- the coalition's contributions after the deepest fork point, below the largest of those minima.

``G_min``, the product over those sub-windows of the number of these values, bounds the nonces the
coalition can reach at the cut-off. With ``m = 1`` it equals the number this enumeration reaches.
Decisions the coalition takes before the cut-off, to publish or withhold a block whose contribution
may end as a minimum, are not counted.

The window's last ``near_slots`` slots are drawn slot by slot under the delay models of
``finality_sim.grinding``. The rest of the oldest sub-window they reach holds the expected number of
canonical honest blocks.
"""

from __future__ import annotations

import numpy as np
from numba import njit

from finality_sim.recovery import occupancy


@njit(cache=True)
def _feasible(canon, adv, z, feasible):
    """Back from the cut-off, as ``grinding._simulate``: the number ``d`` of canonical honest blocks,
    and whether a fork from each depth ``0..d`` wins; depth 0, the honest chain itself, always does."""
    wins, d = 0, 0
    for t in range(canon.size - 1, 0, -1):
        if canon[t]:
            feasible[d] = d == 0 or wins - d + z >= 1
            d += 1
        if adv[t]:
            wins += 1
    feasible[d] = d == 0 or wins - d + z >= 1
    return d


@njit(cache=True)
def _choices_min(canon, adv, feasible, h_rho, w_rho, far_min, sub):
    """``G_min`` and the deepest feasible fork point. Slots ``1..n-1`` precede the cut-off at ``n``;
    ``h_rho`` and ``w_rho`` hold the contributions of the canonical honest blocks and of the
    coalition's wins, the latest first; ``far_min`` is the smallest over the honest blocks of the
    oldest sub-window before slot 1, ``inf`` for none; a sub-window is ``sub`` slots long."""
    n = canon.size
    n_sub = (n - 2) // sub + 1
    sub_of = np.empty(h_rho.size, np.int64)
    w_after = np.empty(w_rho.size, np.int64)           # honest blocks between a win and the cut-off
    w_sub = np.empty(w_rho.size, np.int64)
    nh, nw = 0, 0
    for t in range(n - 1, 0, -1):
        i = (n - 1 - t) // sub
        if canon[t]:
            sub_of[nh] = i
            nh += 1
        if adv[t]:
            w_after[nw] = nh
            w_sub[nw] = i
            nw += 1
    cur = np.full(n_sub, np.inf)                       # the kept minimum of each sub-window
    cur[n_sub - 1] = far_min
    last = np.empty(n_sub)
    theta = np.empty(n_sub)
    count = np.zeros(n_sub, np.int64)
    d_max = -1
    for d in range(nh, -1, -1):                        # deepest first: the kept blocks grow
        if d < nh and h_rho[d] < cur[sub_of[d]]:
            cur[sub_of[d]] = h_rho[d]
        if feasible[d]:
            for i in range(n_sub):
                if d_max < 0:
                    count[i] = 1
                    theta[i] = cur[i]
                    last[i] = cur[i]
                elif cur[i] != last[i]:
                    count[i] += 1
                    last[i] = cur[i]
            if d_max < 0:
                d_max = d
    below = np.zeros(n_sub, np.int64)
    for w in range(nw):
        if w_after[w] <= d_max and w_rho[w] < theta[w_sub[w]]:
            below[w_sub[w]] += 1
    top = sub_of[d_max] if d_max < nh else n_sub - 1
    g = 1.0
    for i in range(top + 1):
        g *= count[i] + below[i]
    return g, d_max


@njit(cache=True)
def _sample(n_samples, h, a, dead, near_slots, sub, far_h, seed):
    np.random.seed(seed)
    out = np.empty(n_samples)
    deep = 0
    canon = np.zeros(near_slots, np.bool_)
    adv = np.zeros(near_slots, np.bool_)
    feasible = np.zeros(near_slots + 1, np.bool_)
    for s in range(n_samples):
        last = 0                                       # a canonical honest block at slot 0
        nh, nw = 0, 0
        for t in range(1, near_slots):
            canon[t] = np.random.random() < h and t - last > dead
            if canon[t]:
                last = t
                nh += 1
            adv[t] = np.random.random() < a
            if adv[t]:
                nw += 1
        lead, z, t = 0, 0, near_slots                  # the most the private chain leads after the cut-off
        while lead > -60:
            if np.random.random() < a:                 # wins count first within a slot
                lead += 1
                z = max(z, lead)
            if np.random.random() < h and t - last > dead:
                last = t
                lead -= 1
            t += 1
        _feasible(canon, adv, z, feasible)
        far_min = np.inf if far_h == 0 else 1.0 - np.random.random() ** (1.0 / far_h)
        g, d_max = _choices_min(canon, adv, feasible, np.random.random(nh), np.random.random(nw),
                                far_min, sub)
        if nh >= 1 and d_max == nh:                    # a fork from before the near slots wins
            deep += 1
        out[s] = g
    return out, deep


def _rates(f: float, alpha: float, growth: float | None, delta: int | None):
    if (growth is None) == (delta is None):
        raise ValueError("set exactly one of growth and delta")
    a = occupancy(f, alpha)
    ph = occupancy(f, 1.0 - alpha)
    h, dead = (growth * ph, 0) if growth is not None else (ph, delta)
    return a, h, dead, (h if growth is not None else 1.0 / (dead + 1.0 / h))


def min_rule_choices(f: float, alpha: float, window_slots: int, n_samples: int, seed: int,
                     sub_windows: int = 1, growth: float | None = None, delta: int | None = None,
                     near_slots: int = 10_000) -> tuple[np.ndarray, float]:
    """``G_min`` for ``n_samples`` windows of ``window_slots`` slots split into ``sub_windows``, and
    the share of them in which a fork from before the near slots would win (the near slots are then
    too few)."""
    a, h, dead, rate = _rates(f, alpha, growth, delta)
    sub = window_slots // sub_windows
    near = min(near_slots, window_slots)
    far_slots = min(((near - 2) // sub + 1) * sub, window_slots) - near + 1
    g, deep = _sample(n_samples, h, a, dead, near, sub, int(round(far_slots * rate)), seed)
    return g, deep / n_samples


def own_share(f: float, alpha: float, growth: float | None = None,
              delta: int | None = None) -> float:
    """The chance that the smallest contribution of a long sub-window is one of the coalition's wins
    when it withholds none: ``a / (a + h_c)``, with ``h_c`` the rate of canonical honest blocks."""
    a, _, _, rate = _rates(f, alpha, growth, delta)
    return a / (a + rate)
