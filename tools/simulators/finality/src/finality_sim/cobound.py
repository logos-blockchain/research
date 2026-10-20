"""Phase J, J.3.2: the convergence-opportunity bound on the slot lottery (DAG.md J.3).

**The bound.** By the lemma of DAG.md J.3, a block of slot ``s_B`` that a client accepts ``T``
slots later is displaced afterwards, at its fork point ``c``, only if for some slot
``u >= s_B + T``

    C(s_c, u - Δ] <= e·A(s_c, u] + 1,

with ``C`` the convergence opportunities by their slot, ``A`` the coalition's wins after ``c`` and
``e`` the events one win can cause in the comparison: 2 under J.1's rule, whose second copy of a
win retracts the first, and 1 if a win could change it once. An opportunity is confirmed ``Δ``
slots after its slot, and at most one falls in any ``Δ`` slots, so it suffices that some
``v < s_B`` and ``u >= s_B + T`` have ``Y(v, u) >= -2``, where the walk ``Y`` adds ``e`` for each
win and takes one for each opportunity in the slot that confirms it.

**The chain.** A slot holds a Poisson number of honest blocks, of which none, one and more matter,
and a Poisson number of coalition wins (``finality_sim.balance``). The state is ``(z, q, p)``:
``z`` the walk, ``q`` the quiet slots since the last honest block, at most ``Δ``, and ``p`` whether
that block was alone in its slot after ``Δ`` quiet slots, an opportunity awaiting confirmation.
Before the target the walk is reflected at zero, ``max_v Y(v, s_B - 1)``, in its stationary law:
the premined lead over every fork point. The target's slot holds at least one honest block, and
the walk then runs free. ``error(T) = P(z >= -2 at s_B + T) + E[h(state); z < -2]``, with ``h``
the chance that the free walk reaches ``-2`` at a later slot. The stationary law and ``h`` are
solved as linear systems; the walk from the target is followed slot by slot.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.stats import poisson

from finality_sim import convergence


def rates(f: float, alpha: float) -> tuple[float, float]:
    lam = -math.log(1.0 - f)
    return (1.0 - alpha) * lam, alpha * lam


def drift(f: float, alpha: float, delta: int, events: int) -> float:
    """The walk's mean step a slot: ``e`` per win, less the opportunities."""
    return events * rates(f, alpha)[1] - convergence.rate(f, alpha, delta)


def exponent(f: float, alpha: float, delta: int, events: int) -> float:
    """``θ > 0`` with ``λ_a (e^{eθ} - 1) + λ_c (e^{-θ} - 1) = 0``: the walk's tail exponent."""
    lam_a = rates(f, alpha)[1]
    lam_c = convergence.rate(f, alpha, delta)
    lo, hi = 1e-12, 50.0
    for _ in range(300):
        mid = (lo + hi) / 2
        if lam_a * math.expm1(events * mid) + lam_c * math.expm1(-mid) < 0:
            lo = mid
        else:
            hi = mid
    return lo


@njit(cache=True)
def _step(q, p, h, delta):
    """The next ``(q, p)`` and the opportunities confirmed in a slot with ``h`` honest blocks
    (``h = 2`` stands for two or more)."""
    if delta == 0:
        return 0, 0, 1 if h == 1 else 0
    if h == 0:
        if p == 1 and q + 1 == delta:
            return delta, 0, 1
        return min(q + 1, delta), p, 0
    return 0, 1 if (h == 1 and q == delta) else 0, 0


@njit(cache=True)
def _edges(z_lo, z_hi, delta, events, ph, pa, reflect):
    """The slot's transitions as (from, to, probability), over ``z`` in ``z_lo..z_hi``; a step
    below ``z_lo`` goes to -1, one above ``z_hi`` stays at ``z_hi``."""
    nq = delta + 1
    n = (z_hi - z_lo + 1) * nq * 2
    m = n * 3 * pa.size
    src = np.empty(m, np.int64)
    dst = np.empty(m, np.int64)
    val = np.empty(m)
    k = 0
    for zi in range(z_hi - z_lo + 1):
        z = z_lo + zi
        for q in range(nq):
            for p in range(2):
                s = (zi * nq + q) * 2 + p
                for h in range(3):
                    if ph[h] == 0.0:
                        continue
                    q2, p2, dec = _step(q, p, h, delta)
                    for a in range(pa.size):
                        z2 = z + events * a - dec
                        if reflect and z2 < 0:
                            z2 = 0
                        if z2 > z_hi:
                            z2 = z_hi
                        src[k] = s
                        dst[k] = -1 if z2 < z_lo else ((z2 - z_lo) * nq + q2) * 2 + p2
                        val[k] = ph[h] * pa[a]
                        k += 1
    return src[:k], dst[:k], val[:k]


@njit(cache=True)
def _forward(dist, src, dst, val):
    out = np.zeros_like(dist)
    for k in range(src.size):
        if dst[k] >= 0:
            out[dst[k]] += dist[src[k]] * val[k]
    return out


def _laws(f, alpha, tail=1e-18):
    """``(none, one, more)`` honest blocks and the wins, a slot."""
    lam_h, lam_a = rates(f, alpha)
    p0 = math.exp(-lam_h)
    p1 = lam_h * p0
    ph = np.array([p0, p1, 1.0 - p0 - p1])
    a_max = 1
    while poisson.sf(a_max, lam_a) > tail:
        a_max += 1
    pa = poisson.pmf(np.arange(a_max + 1), lam_a)
    pa[-1] += poisson.sf(a_max, lam_a)
    return ph, pa


def _states(z_lo, z_hi, delta):
    nq = delta + 1
    z = np.repeat(np.arange(z_lo, z_hi + 1), nq * 2)
    q = np.tile(np.repeat(np.arange(nq), 2), z_hi - z_lo + 1)
    p = np.tile(np.arange(2), (z_hi - z_lo + 1) * nq)
    return z, q, p


def premined(f, alpha, delta, events, z_hi):
    """The stationary law of the reflected walk over ``z = 0..z_hi`` and its state."""
    ph, pa = _laws(f, alpha)
    src, dst, val = _edges(0, z_hi, delta, events, ph, pa, True)
    n = (z_hi + 1) * (delta + 1) * 2
    p = sparse.csr_matrix((val, (dst, src)), shape=(n, n))
    a = (p - sparse.identity(n)).tolil()
    a[0, :] = 1.0
    b = np.zeros(n)
    b[0] = 1.0
    pi = np.clip(spsolve(a.tocsr(), b), 0.0, None)
    return pi / pi.sum()


def catch_up(f, alpha, delta, events, depth_max):
    """``h`` over ``z = -3 - depth_max .. -3``: the chance that the free walk reaches ``-2`` at a
    later slot's end; a walk that falls below the range counts as never reaching it."""
    ph, pa = _laws(f, alpha)
    lo, top = -3 - depth_max, -3 + events * (pa.size - 1)
    src, dst, val = _edges(lo, top, delta, events, ph, pa, False)
    n_t = (depth_max + 1) * (delta + 1) * 2
    inside = src < n_t
    src, dst, val = src[inside], dst[inside], val[inside]
    win = dst >= n_t
    stay = (dst >= 0) & ~win
    m = sparse.csr_matrix((val[stay], (src[stay], dst[stay])), shape=(n_t, n_t))
    r = np.bincount(src[win], weights=val[win], minlength=n_t)
    return np.clip(spsolve((sparse.identity(n_t) - m).tocsc(), r), 0.0, 1.0)


def error_curve(f: float, alpha: float, delta: int, events: int, horizon: int,
                opens_phase: bool = False, stop: float = 0.0) -> np.ndarray:
    """The bound on the chance that a block accepted ``T`` slots after its own is displaced
    afterwards, for ``T = 0..horizon``: all ones when the walk does not drift down. With
    ``opens_phase`` the target follows ``Δ`` quiet slots, as J.2's targets do. The curve ends
    early once it falls below ``stop``."""
    if drift(f, alpha, delta, events) >= 0:
        return np.ones(horizon + 1)
    theta = exponent(f, alpha, delta, events)
    z_hi = int(45.0 / theta) + 10
    depth_max = int(50.0 / theta) + 10
    ph, pa = _laws(f, alpha)
    pi = premined(f, alpha, delta, events, z_hi)
    if opens_phase:
        pi = np.where(_states(0, z_hi, delta)[1] == delta, pi, 0.0)
        pi /= pi.sum()
    h = catch_up(f, alpha, delta, events, depth_max)
    lo, top = -3 - depth_max, z_hi + events * (pa.size - 1)
    nq = delta + 1
    dist = np.zeros((top - lo + 1) * nq * 2)
    target = np.array([0.0, ph[1], ph[2]]) / (ph[1] + ph[2])     # the target's slot
    zs, qs, ps = _states(0, z_hi, delta)
    for i in np.nonzero(pi > 0.0)[0]:
        for hc in (1, 2):
            q2, p2, dec = _step(qs[i], ps[i], hc, delta)
            for a in range(pa.size):
                z2 = zs[i] + events * a - dec
                dist[((z2 - lo) * nq + q2) * 2 + p2] += pi[i] * target[hc] * pa[a]
    src, dst, val = _edges(lo, top, delta, events, ph, pa, False)
    zf = _states(lo, top, delta)[0]
    hit = (zf >= -2).astype(float)
    hit[: h.size] = h
    out = np.empty(horizon + 1)
    for t in range(horizon + 1):
        out[t] = min(1.0, float(dist @ hit))
        if out[t] < stop:
            return out[: t + 1]
        if t < horizon:
            dist = _forward(dist, src, dst, val)
    return out


def depth(values: np.ndarray, eps: float) -> int | None:
    """The first ``T`` from which ``values`` stays at or below ``eps``, or None if the curve
    never falls to it."""
    above = np.nonzero(values > eps)[0]
    if above.size == 0:
        return 0
    if above[-1] == values.size - 1:
        return None
    return int(above[-1] + 1)
