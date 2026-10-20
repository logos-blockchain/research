"""The coalition's adaptive play against the observed counting rule (DESIGNS.md, H.3).

``counting_observed_logp`` charges the coalition's wins ``A(t)`` as Poisson, independent of what the
client sees. Under a worst case of ``Δ`` the coalition also chooses when the client's count reaches
the rule's threshold: it signs a win on the client's chain as well as on its own, delays honest
blocks, and publishes forks. So the bound is not the risk given the client's view. The guarantee is
per target: the chance that the rule accepts the target and the target later falls, with acceptance
a stopping time of the coalition's choosing. This module computes that chance by backward induction.

Without forks the client accepts at the first slot ``t`` after the parent at which it holds ``N(t)``
blocks, ``N(t)`` the least ``n`` whose deadline is at least ``t``. At acceptance with ``n`` blocks
the competing chain holds the lead ``L`` before the parent, the coalition's wins ``A``, and the honest
blocks of the last ``Δ`` slots ``H``, Poisson at ``p_h Δ`` as the rule charges them. It is
``x = n + 1 - L - A - H`` blocks short of overtaking and wins later with chance ``c(x)``.

Two laws for ``L`` and ``c`` (``laws``):
- ``"bound"``: the rule's own, both geometric at the counting ratio ``rho``;
- ``"renewal"``: the worst-case renewal walk. The canonical chain gains one block per cycle of a
  geometric wait for an honest win and ``Δ`` slots more; the competing chain gains the coalition's
  wins of the cycle and the honest wins of its last ``Δ`` slots, ``U = A + W``. No schedule within
  ``Δ`` grows the canonical chain slower or the competing chain faster, so this law bounds every
  strategy's lead and catch-up from above. ``L`` is the walk's stationary lead, ``c`` its chance of
  ever gaining ``x``.

Three plays, each conditioned on ``L``, which the coalition knows:
- ``induction``: each win is kept private or signed on both chains when it falls, and the honest
  part of the client's chain grows at the worst-case rate ``h_w``, one block every ``1 / h_w``
  slots. A class of strategies, so a lower bound on the coalition's best.
- ``free_timing``: every win private, and the coalition places the acceptance at any slot between
  the arrival of the full-rate path and of the worst-case path at ``N(t)``.
- ``upper_bound``: the coalition accepts at any slot it chooses, paying as if the client then held
  exactly the blocks the threshold asks. The client's chain grows no slower than the renewal walk's
  canonical chain, so the client accepts at the latest when that chain alone reaches the threshold.
  The coalition postpones that by one block for each fork it publishes, and a fork costs it one
  block of the shortfall, since the client then needs one block more. This bounds every strategy
  that keeps the competing chain private until acceptance.
"""

from __future__ import annotations

import functools
import math

import numpy as np
from scipy import optimize, special, stats

from finality_sim.further import counting_observed_deadlines, counting_observed_logp, counting_ratio
from finality_sim.recovery import occupancy


def second_leader(alpha: float, f: float = 1 / 30) -> float:
    """The chance that a slot the honest stake wins has a second honest leader, with the stake
    spread over many holders, the most it can be: the winners are Poisson at ``-(1 - α) ln(1 - f)``."""
    lam = -(1 - alpha) * math.log(1 - f)
    return (1 - math.exp(-lam) - lam * math.exp(-lam)) / (1 - math.exp(-lam))


def cycle_pmf(p_a: float, p_h: float, delta: int, size: int = 400, honest: bool = True,
              second: float = 0.0) -> np.ndarray:
    """The law of ``U``, the competing chain's gain in one cycle of the worst-case walk: the
    coalition's wins over ``Δ + G`` slots, ``G`` geometric at ``p_h``, plus the honest wins of the
    ``Δ`` slots after the honest win that ends the wait (``honest=False`` drops them), plus with
    chance ``second`` the block of a second honest leader of that slot."""
    out = np.zeros(size)
    g = 1
    while True:
        pg = p_h * (1 - p_h) ** (g - 1)
        if pg < 1e-20:
            break
        slots = delta + g
        a = stats.binom.pmf(np.arange(min(slots, size - 1) + 1), slots, p_a)
        out[:a.size] += pg * a
        g += 1
    if honest:
        out = np.convolve(out, stats.binom.pmf(np.arange(delta + 1), delta, p_h))[:size]
    if second:
        out = (1 - second) * out + second * np.concatenate([[0.0], out[:-1]])
    return out


def walk_lead(u: np.ndarray, size: int) -> tuple[np.ndarray, np.ndarray]:
    """``P(L = l)`` and ``P(L >= l)``, ``l < size``, for the stationary lead of the walk
    ``L' = max(0, L + U - 1)``: the competing chain's lead over the canonical chain, maximised over
    the fork point."""
    pmf = np.zeros(size)
    pmf[0] = 1.0
    for _ in range(1_000_000):
        y = np.convolve(pmf, u)[:size + 1]
        new = np.empty(size)
        new[0] = y[0] + y[1]
        new[1:] = y[2:size + 1]
        new /= new.sum()
        if np.abs(new - pmf).sum() < 1e-16:
            pmf = new
            break
        pmf = new
    return pmf, np.cumsum(pmf[::-1])[::-1]


def catch_up(u: np.ndarray, tail: np.ndarray) -> np.ndarray:
    """``c(x)``, ``x = 0..``: the chance that a competing chain ``x`` blocks short of overtaking
    ever overtakes, from the start of a cycle. It overtakes within a cycle, before the canonical
    chain's block, so ``c(x) = P(max_k S_k >= x - 1)`` for the walk ``S`` of ``U - 1``: the
    stationary lead's tail for ``x >= 2``, and for ``x = 1`` a gain in the first cycle or a return
    from one below."""
    c = np.empty(tail.size + 1)
    c[0] = 1.0
    c[1] = (1.0 - u[0]) + u[0] * tail[1]
    c[2:] = tail[1:]
    return c


def decay(u: np.ndarray) -> float:
    """``e^(-θ*)``, the factor by which the stationary lead's tail falls per block, with ``θ*`` the
    positive root of ``E[e^(θ(U - 1))] = 1`` (Lundberg's exponent)."""
    k = np.nonzero(u > 0)[0]
    lu = np.log(u[k])

    def f(th):
        return float(special.logsumexp(lu + th * k)) - th
    hi = 0.05
    while f(hi) < 0:
        hi *= 2
    return math.exp(-optimize.brentq(f, 1e-9, hi, xtol=1e-14))


def laws(alpha: float, delta: int, model: str, size: int, f: float = 1 / 30):
    """``(P(L = l), c(x))`` for ``l, x < size`` under ``model``: ``"bound"``, or ``"renewal"``, the
    walk with a second honest leader's block in the competing chain at ``second_leader``'s chance."""
    if model == "bound":
        rho = counting_ratio(alpha, delta, f)
        return (1 - rho) * rho ** np.arange(size), rho ** np.arange(size)
    u = cycle_pmf(occupancy(f, alpha), occupancy(f, 1 - alpha), delta,
                  second=second_leader(alpha, f))
    pmf, tail = walk_lead(u, size)
    return pmf, catch_up(u, tail)[:size]


def law_logp(n: int, t: float, alpha: float, delta: int, lead: np.ndarray, c: np.ndarray,
             ties_to_coalition: bool = False, f: float = 1 / 30) -> float:
    """``counting_observed_logp`` with no forks under the lead's law ``lead`` and the catch-up
    ``c``; ``lead`` and ``c`` must reach ``n + 1``."""
    a, h = occupancy(f, alpha), occupancy(f, 1 - alpha)
    need = n + 1 - int(ties_to_coalition)
    top = need + 1
    x = np.convolve(stats.poisson.pmf(np.arange(top), a * t),
                    stats.poisson.pmf(np.arange(top), h * delta))[:top]
    below = np.convolve(x, lead[:top])[:need]
    reach = max(0.0, 1.0 - float(below.sum()))
    return math.log(max(reach + float(np.sum(below * c[need - np.arange(need)])), 1e-300))


def law_depth(alpha: float, delta: int, eps: float, rate: float, lead: np.ndarray, c: np.ndarray,
              ties_to_coalition: bool = False, f: float = 1 / 30) -> int:
    """``counting_observed_depth`` with no forks under ``lead`` and ``c``; -1 if none they reach."""
    for d in range(1, min(lead.size, c.size) - 2):
        n = d + 1
        if law_logp(n, n / rate, alpha, delta, lead, c, ties_to_coalition, f) <= math.log(eps):
            return d
    return -1


def payoff(alpha: float, delta: int, model: str, size: int, f: float = 1 / 30) -> np.ndarray:
    """``E_H[c(x - H)]`` for ``x = 0..size - 1``, with ``c = 1`` at or below zero: the coalition's
    chance once the client accepts with the competing chain ``x`` blocks short of overtaking before
    the honest blocks of the last ``Δ`` slots."""
    _, c = laws(alpha, delta, model, size + 1, f)
    h = stats.poisson.pmf(np.arange(40), occupancy(f, 1 - alpha) * delta)
    x = np.arange(size)[:, None] - np.arange(40)[None, :]
    return (np.where(x <= 0, 1.0, c[np.clip(x, 0, size)]) * h).sum(axis=1) + max(0.0, 1.0 - h.sum())


@functools.lru_cache(maxsize=32)
def threshold(alpha: float, delta: int, eps: float, n_max: int, f: float = 1 / 30) -> np.ndarray:
    """``N(t)`` for ``t = 0..``, the least ``n`` whose deadline is at least ``t``, up to the deadline
    of ``n_max``: the blocks the client must hold at slot ``t`` after the parent, with no forks."""
    dl = counting_observed_deadlines(alpha, delta, eps, n_max, (0,), f)[:, 0]
    first = int(np.nonzero(dl >= 0)[0][0])
    ts = np.arange(int(dl[-1]))
    return first + np.searchsorted(dl[first:], ts, side="left")


def _rates(alpha: float, delta: int, f: float):
    p_a, p_h = occupancy(f, alpha), occupancy(f, 1 - alpha)
    return p_a, p_h, 1.0 / (delta + 1.0 / p_h)


def induction(alpha: float, delta: int, eps: float, model: str, n_max: int, f: float = 1 / 30,
              policy: bool = False):
    """The ``induction`` play's value per target, with the slot ``t_end`` at which the honest part
    alone reaches the threshold and the value of keeping every win private until then, the rule's
    own case. With ``policy``, also the slots' thresholds and for each slot the states ``(b, p)``,
    ``b`` signed wins and ``p`` private wins plus the lead, in which a win is signed."""
    p_a, p_h, h_w = _rates(alpha, delta, f)
    ns = threshold(alpha, delta, eps, n_max, f)
    ts = np.arange(ns.size)
    nh = np.floor(h_w * ts).astype(np.int64)
    t_end = int(np.nonzero(nh >= ns)[0][0])
    kb = ns - nh                                         # signed wins that trigger acceptance
    b_max = int(kb[:t_end + 1].max()) + 1
    lead, _ = laws(alpha, delta, model, 4 * int(ns[t_end]) + 400, f)
    l_max = int(np.nonzero(np.cumsum(lead[::-1])[::-1] < 1e-18)[0][0])  # the lead's tail beyond is below 1e-18
    p_max = int(p_a * t_end + 8 * math.sqrt(p_a * t_end) + 20) + l_max
    pay = payoff(alpha, delta, model, int(nh[t_end]) + 2 + p_max, f)
    ps = np.arange(p_max + 1)

    def paid(t):                                         # short of overtaking: nh + 1 - p
        return pay[np.clip(nh[t] + 1 - ps, 0, pay.size - 1)]
    v = np.tile(paid(t_end), (b_max + 1, 1))
    signs = []
    for t in range(t_end - 1, -1, -1):
        both = np.vstack([v[1:], v[-1:]])
        priv = np.hstack([v[:, 1:], v[:, -1:]])
        if policy:
            signs.append(both > priv)
        cont = (1 - p_a) * v + p_a * np.maximum(both, priv)
        acc = max(int(kb[t]), 0)
        if acc <= b_max:
            cont[acc:, :] = paid(t)[None, :]
        v = cont
    lw = lead[:l_max + 1] / lead[:l_max + 1].sum()
    value = float((lw * v[0, :l_max + 1]).sum())
    a_end = stats.binom.pmf(np.arange(p_max + 1), t_end, p_a)
    own = float(sum(lw[ell] * (a_end[:p_max + 1 - ell] * paid(t_end)[ell:]).sum() for ell in range(l_max + 1)))
    out = dict(value=value, own=own, t_end=t_end, n_end=int(ns[t_end]))
    if policy:
        out.update(kb=kb[:t_end + 1], nh=nh[:t_end + 1], signs=signs[::-1], pay=pay, lead=lw)
    return out


def free_timing(alpha: float, delta: int, eps: float, model: str, n_max: int,
                f: float = 1 / 30) -> dict:
    """The ``free_timing`` play's value per target: optimal stopping of ``L + A(t)`` over the slots
    from ``t0``, where the full-rate path ``f t`` reaches ``N(t)``, to ``t1``, where the worst-case
    path ``h_w t`` does, paying ``E_H[c(N(t) + 1 - L - A(t) - H)]``."""
    p_a, p_h, h_w = _rates(alpha, delta, f)
    ns = threshold(alpha, delta, eps, n_max, f)
    ts = np.arange(ns.size)
    t0 = int(np.nonzero(f * ts >= ns)[0][0])
    t1 = int(np.nonzero(h_w * ts >= ns)[0][0])
    top = int(ns[t1]) + 80
    lead, _ = laws(alpha, delta, model, top + 1, f)
    pay = payoff(alpha, delta, model, top + 2, f)
    xs = np.arange(top + 1)

    def paid(t):
        return pay[np.clip(ns[t] + 1 - xs, 0, pay.size - 1)]
    x0 = np.convolve(lead, stats.binom.pmf(xs, t0, p_a))[:top + 1]
    x0[-1] += max(0.0, 1.0 - x0.sum())
    v = paid(t1)
    for t in range(t1 - 1, t0 - 1, -1):
        cont = (1 - p_a) * v
        cont[:-1] += p_a * v[1:]
        cont[-1] += p_a * v[-1]
        v = np.maximum(paid(t), cont)
    return dict(value=float((x0 * v).sum()), t0=t0, t1=t1)


def upper_bound(alpha: float, delta: int, eps: float, model: str, n_max: int, f: float = 1 / 30,
                horizon: float = 2.0, slack: int = 60) -> dict:
    """The ``upper_bound`` play's value per target, by backward induction over the slots up to
    ``horizon`` times the slot at which the worst-case path reaches the threshold.

    State at a slot: the renewal phase (waiting for an honest win, or ``d`` slots before the
    pending block lands), the shortfall ``y = N(t) + F - A - L`` the competing chain would have if
    the client accepted now holding the ``N(t) + F`` blocks it needs with ``F`` forks, and the slack
    ``s = N(t) + F - R(t)`` before the walk's canonical chain ``R(t)`` forces acceptance. Each slot
    the threshold's step raises both, a coalition win lowers ``y``, and a landing lowers ``s``. The
    coalition stops for ``E_H[c(y + 1 - H)]`` whenever it likes; at ``s = 0`` it stops or publishes
    a fork, ``y`` and ``s`` one up."""
    p_a, p_h, h_w = _rates(alpha, delta, f)
    ns = threshold(alpha, delta, eps, n_max, f)
    t1 = int(np.nonzero(h_w * np.arange(ns.size) >= ns)[0][0])
    t_max = min(int(horizon * t1), ns.size - 2)
    first = int(ns[0])
    pay = payoff(alpha, delta, model, 4 * first + 400, f)
    y_hi = int(np.nonzero(pay < eps * 1e-9)[0][0])       # values above are capped at y_hi's
    ys = np.arange(-1, y_hi + 1)                         # c = 1 at y = -1 and below: stop
    stop = np.where(ys < 0, 1.0, pay[np.clip(ys + 1, 0, pay.size - 1)])[None, :, None]
    v = np.broadcast_to(stop, (delta + 1, ys.size, first + slack + 1)).copy()
    v = upper_bound_sweep(v, stop, ns[:t_max + 1], p_a, p_h)
    lead, _ = laws(alpha, delta, model, first + y_hi + 3, f)
    at = first - np.arange(lead.size) + 1                # index of y0 = N(0) - L
    got = np.where(at < 0, 1.0, v[0, np.clip(at, 0, ys.size - 1), first])
    return dict(value=float((lead * got).sum() + max(0.0, 1.0 - lead.sum())), t1=t1, t_max=t_max)


def upper_bound_sweep(v: np.ndarray, stop: np.ndarray, ns: np.ndarray, p_a: float,
                      p_h: float) -> np.ndarray:
    """The backward sweep of ``upper_bound`` from the last slot of ``ns`` to slot 0. ``v`` holds
    the values at the last slot over (phase, y from -1, s from 0), phase 0 waiting for an honest
    win and phase ``d`` with ``d`` slots before the pending block lands; ``stop`` the stopping
    value over y. Values above the grid's top are capped at the top's."""
    delta = v.shape[0] - 1
    for t in range(ns.size - 2, -1, -1):
        step = int(ns[t + 1] - ns[t])
        if step:                                         # the threshold's step raises y and s
            v = np.concatenate([v[:, step:], np.repeat(v[:, -1:], step, axis=1)], axis=1)
            v = np.concatenate([v[:, :, step:], np.repeat(v[:, :, -1:], step, axis=2)], axis=2)
        won = (1 - p_a) * v                              # a coalition win lowers y
        won[:, 1:] += p_a * v[:, :-1]
        won[:, 0] += p_a
        cont = np.empty_like(v)
        cont[0] = (1 - p_h) * won[0] + p_h * won[delta]
        cont[2:] = won[1:delta]
        cont[1, :, 1:] = won[0, :, :-1]                  # a landing lowers s
        cont[1, :, 0] = won[0, :, 0]
        v = np.maximum(stop, cont)
        fork = np.concatenate([cont[:, 1:, 1], cont[:, -1:, 1]], axis=1)
        v[:, :, 0] = np.maximum(stop[:, :, 0], fork)      # at s = 0: stop, or a fork
    return v


def view_risk(alpha: float, delta: int, eps: float, n_max: int, f: float = 1 / 30,
              floor: float = 1e-12) -> dict:
    """A realizable play that breaks the bound per view: the coalition signs every win on its
    private chain and on the client's, and delays honest blocks so that the honest part grows at
    ``h_w``. The client accepts at the first slot it holds ``N(t)``; its competing chain then holds
    only the coalition's blocks, so given the view the target falls with chance
    ``E[c(n_h + 1 - L)]`` under the walk of the coalition's wins alone. Returns the likeliest view
    accepted with that chance above ``eps``, with the rule's own bound there and the view's
    chance; the view that fails most often among those of chance at least ``floor``; the chance of
    all views above ``eps``; the largest honest part among them; and the chance per target."""
    p_a, p_h, h_w = _rates(alpha, delta, f)
    u = cycle_pmf(p_a, p_h, delta, honest=False)
    pmf, tail = walk_lead(u, 800)
    c = catch_up(u, tail)

    def given(nh):
        x = nh + 1 - np.arange(pmf.size)
        return float((pmf * np.where(x <= 0, 1.0, c[np.clip(x, 0, c.size - 1)])).sum())
    ns = threshold(alpha, delta, eps, n_max, f)
    ts = np.arange(ns.size)
    nh = np.floor(h_w * ts).astype(np.int64)
    t_end = int(np.nonzero(nh >= ns)[0][0])
    dist = np.zeros(int(ns[t_end]) + 2)
    dist[0] = 1.0
    per_target, likeliest, worst, above, worst_nh = 0.0, None, None, 0.0, -1
    for t in range(1, t_end + 1):
        nd = dist * (1 - p_a)
        nd[1:] += dist[:-1] * p_a
        dist = nd
        k = max(int(ns[t] - nh[t]), 0)
        m = float(dist[k:].sum())
        if m <= 0:
            continue
        risk = given(int(nh[t]))
        per_target += m * risk
        if risk > eps:
            above += m
            worst_nh = int(nh[t])
            n = int(ns[t])
            view = dict(n=n, t=t, honest=int(nh[t]), coalition=n - int(nh[t]), risk=risk,
                        bound=math.exp(counting_observed_logp(n, float(t), 0, alpha, delta, f)), chance=m)
            if likeliest is None or m > likeliest["chance"]:
                likeliest = view
            if m >= floor and (worst is None or risk > worst["risk"]):
                worst = view
        dist[k:] = 0.0
    return dict(likeliest=likeliest, worst=worst, above=above, worst_honest=worst_nh,
                per_target=per_target)
