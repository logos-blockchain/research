"""Finality counted in slots: settlement after a wait of ``T`` slots (SLOTS.md, K.1).

Phases A–J count ``k`` in blocks. Here a client, or the protocol's ``B_imm``, accepts the prefix up
to a target's slot once ``T`` slots have passed since that slot. Both delay models of the study:

- **Random delay.** The private race with a premined lead, in B4's model: per slot the coalition
  wins at ``a = α·λ`` and the canonical chain grows at ``h = (1 − α)·g·λ``, ``λ = −ln(1 − f)``.
  B4's exact chance ``P(n, t)``, with ``n`` canonical blocks counting the target ``t`` slots after
  the target's parent, is averaged over the blocks the wait holds and over the gap from the parent
  to the target (``wait_logfail``). ``race_wait`` plays the race on timelines, scored ``T`` slots
  after the target.
- **A worst case of ``Δ``.** Once the prefix up to the target's slot lies ``D`` deep in an honest
  chain, B2's upper bound holds its displacement. After a wait of ``T`` slots it lies at least
  ``N − W − 2`` deep: ``N`` counts the honest renewals of the wait, honest wins at least ``Δ``
  apart, each delivered within it (B5's law, ``recovery.honest_logpmf``), started ``2Δ`` late so
  that it does not depend on the past; ``W`` is the coalition's private lead at the target's slot,
  the largest excess of its wins over the honest renewals since any earlier slot, the stationary
  law of a reflected walk (``lead_law``). ``worst_logbound`` takes the best ``D``:
  ``P ≤ min_D [UB(D) + P(N − W − 2 < D)]``.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit
from scipy import special, stats

from .adaptive import cycle_pmf, walk_lead
from .recovery import honest_logpmf, occupancy

F = 1 / 30
GAP_NODES = 40          # Gauss–Laguerre nodes for the gap from the parent to the target


def rates(alpha: float, g: float, f: float = F) -> tuple[float, float]:
    """B4's per-slot rates: the coalition's wins ``a`` and the canonical chain's growth ``h``."""
    lam = -math.log(1 - f)
    return alpha * lam, (1 - alpha) * g * lam


def log_fail_all(n_max: int, t: float, a: float, h: float) -> np.ndarray:
    """``elapsed.log_fail(n, t, a, h)`` for every ``n = 1..n_max`` (index ``n``; index 0 unused).

    With ``ρ = a/h`` and ``s(j) = P(M ≥ j) + Σ_{i<j} P(M = i)·ρ^(j−i)``, ``M`` Poisson at ``a·t``,
    the chance is ``ρ^(n+2) + (1 − ρ²)·s(n+1) + Σ_{j≤n} (1 − ρ)·ρ^(n+2−j)·s(j)``: the stationary lead
    after the parent, ``n + 1 − j``, weighs each deficit ``j``.
    """
    log_rho = math.log(a / h)
    rho = a / h
    m = np.arange(n_max + 1)
    log_pm = stats.poisson.logpmf(m, a * t)
    j = m + 1                                                    # j = 1..n_max + 1
    log_t = np.logaddexp.accumulate(log_pm - m * log_rho) + j * log_rho
    log_s = np.logaddexp(stats.poisson.logsf(j - 1, a * t), log_t)      # s(j) at index j - 1
    n = np.arange(1, n_max + 1)
    # sum over j = 1..n of s(j) rho^-j, accumulated
    acc = np.logaddexp.accumulate(log_s[:n_max] - j[:n_max] * log_rho)
    log_c = math.log(1 - rho) + (n + 2) * log_rho + acc
    head = math.log1p(-rho * rho) + log_s[1:n_max + 1]
    out = np.full(n_max + 1, -np.inf)
    out[1:] = np.logaddexp((n + 2) * log_rho, np.logaddexp(head, log_c))
    return out


def wait_logfail(T: float, alpha: float, g: float, f: float = F,
                 nodes: int = GAP_NODES) -> float:
    """log of the private race's chance against a wait of ``T`` slots after the target's slot.

    The gap from the parent to the target is exponential at ``h`` (Gauss–Laguerre), and the
    canonical blocks after the target within the wait are Poisson at ``h·T``.
    """
    a, h = rates(alpha, g, f)
    mu = h * T
    n_max = int(mu + 14 * math.sqrt(mu + 1) + 40)
    n = np.arange(1, n_max + 1)
    log_pn = stats.poisson.logpmf(n - 1, mu)                    # n counts the target
    x, w = np.polynomial.laguerre.laggauss(nodes)
    terms = [math.log(wt) + special.logsumexp(log_pn + log_fail_all(n_max, xi / h + T, a, h)[1:])
             for xi, wt in zip(x, w)]
    return float(special.logsumexp(terms))


def wait_needed(alpha: float, eps: float, g: float, f: float = F, t_max: int = 2_000_000) -> int:
    """The shortest wait, in slots, whose chance is at most ``eps``; -1 past ``t_max``."""
    target = math.log(eps)
    if wait_logfail(t_max, alpha, g, f) > target:
        return -1
    lo, hi = 0, t_max
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if wait_logfail(mid, alpha, g, f) <= target else (mid, hi)
    return hi


@njit(cache=True)
def _race_wait(canon, adv, waits, give_up, premine, win_at):
    """Successes per wait, the number of scored targets, and for each target the longest wait it
    beats (0 if none, -1 if not scored). A wait ``T`` accepts the target at slot ``canon[i] + T``;
    the race beats it if the coalition's lead after the target's parent reaches ``win_at`` at that
    moment or at any later event."""
    n_c, n_a, n_w = canon.size, adv.size, waits.size
    succ = np.zeros(n_w, np.int64)
    longest = np.full(n_c, -1, np.int64)
    scored = 0
    lead_before = np.zeros(n_c, np.int64)
    since_parent = np.zeros(n_c, np.int64)
    lead, ia = 0, 0
    for i in range(n_c):
        wins = 0
        while ia < n_a and adv[ia] <= canon[i]:
            lead += 1
            wins += 1
            ia += 1
        lead_before[i] = lead
        since_parent[i] = wins
        lead = lead - 1 if lead > 0 else 0
    w_max = waits[n_w - 1]
    ja0 = 0
    for i in range(n_c):
        start = lead_before[i] if premine else since_parent[i]
        r = start - 1
        while ja0 < n_a and adv[ja0] <= canon[i]:
            ja0 += 1
        ja, ic = ja0, i + 1
        best = np.full(n_w, -(1 << 30), np.int64)
        accepted = np.zeros(n_w, np.bool_)
        truncated = False
        while True:
            next_adv = adv[ja] if ja < n_a else np.int64(1 << 62)
            next_can = canon[ic] if ic < n_c else np.int64(1 << 62)
            nxt = min(next_adv, next_can)
            # every wait whose acceptance falls before the next event accepts now, at lead r
            for kk in range(n_w):
                if not accepted[kk] and canon[i] + waits[kk] < nxt:
                    accepted[kk] = True
                    if r > best[kk]:
                        best[kk] = r
            if nxt == (1 << 62):
                truncated = True
                break
            if next_adv <= next_can:
                r += 1
                ja += 1
            else:
                r -= 1
                ic += 1
            for kk in range(n_w):
                if accepted[kk] and r > best[kk]:
                    best[kk] = r
            if r < -give_up and accepted[n_w - 1]:
                break
        if truncated and canon[i] + w_max >= canon[n_c - 1]:
            continue
        scored += 1
        longest[i] = 0
        for kk in range(n_w):
            if best[kk] >= win_at:
                succ[kk] += 1
                longest[i] = waits[kk]
    return succ, scored, longest


def race_wait(canon_slots: np.ndarray, adv_slots: np.ndarray, waits, give_up: int = 60,
              premine: bool = True, win_at: int = 1) -> tuple[np.ndarray, int]:
    """Attack successes against each wait (ascending, in slots), and the number of scored targets:
    ``race.race`` with the acceptance at a slot instead of a depth."""
    w = np.asarray(sorted(waits), np.int64)
    succ, scored, _ = _race_wait(np.asarray(canon_slots, np.int64),
                                 np.asarray(adv_slots, np.int64), w, give_up, premine, win_at)
    return succ, scored


def race_wait_longest(canon_slots: np.ndarray, adv_slots: np.ndarray, waits, give_up: int = 60,
                      premine: bool = True, win_at: int = 1) -> np.ndarray:
    """For each canonical block, the longest of ``waits`` the race beats: 0 if none, -1 if the
    block is not scored. ``race.race_depths`` with waits for depths."""
    w = np.asarray(sorted(waits), np.int64)
    return _race_wait(np.asarray(canon_slots, np.int64), np.asarray(adv_slots, np.int64), w,
                      give_up, premine, win_at)[2]


def lead_law(p_a: float, p_h: float, delta: int, size: int = 400) -> np.ndarray:
    """An upper bound in law on ``W``, ``P(W = z)`` for ``z < size``: the largest excess of the
    coalition's wins over the honest renewals since any earlier slot, at a slot.

    Per slot the excess moves as the walk ``W' = max(0, W + A − R)``, ``A`` a coalition win at
    ``p_a`` and ``R`` a renewal, an honest win at ``p_h`` at least ``Δ`` slots after the last. Just
    after a renewal it is H.3's stationary lead ``V`` of the cycle walk (``adaptive.walk_lead``),
    each cycle ``Δ`` dead slots and a geometric wait at ``p_h``. A slot falls ``J`` slots into its
    cycle, ``P(J = j) = P(L ≥ j)/E[L]`` for the cycle's length ``L``, and ``W ≤ V + Bin(J, p_a)``.
    """
    v, _ = walk_lead(cycle_pmf(p_a, p_h, delta, size, honest=False), size)
    mean_len = delta + 1.0 / p_h
    part = np.zeros(size)
    j = 1
    while True:
        tail = 1.0 if j <= delta + 1 else (1 - p_h) ** (j - delta - 1)
        weight = tail / mean_len
        if j > delta + 1 and weight < 1e-22:
            break
        b = stats.binom.pmf(np.arange(min(j, size - 1) + 1), j, p_a)
        part[:b.size] += weight * b
        j += 1
    out = np.convolve(v, part)[:size]
    return out / out.sum()


def worst_logbound(T: int, alpha: float, delta: int, log_ub: np.ndarray, f: float = F,
                   w_law: np.ndarray | None = None) -> tuple[float, int]:
    """log of ``min_D [UB(D) + P(N − W − 2 < D)]`` for a wait of ``T`` slots, and the ``D`` that
    attains it (0 if no depth helps). ``log_ub[D - 1]`` is log B2's upper bound at depth ``D``.

    ``N`` counts the renewals of ``T − 2Δ`` slots from a live start: ``P(N ≤ n)`` is
    ``P(Bin(w − (n + 1)Δ, p_h) ≤ n)``, B5's law. ``W`` follows ``lead_law``, independent of ``N``."""
    p_h, p_a = occupancy(f, 1 - alpha), occupancy(f, alpha)
    w = max(T - 2 * delta, 0)
    pz = lead_law(p_a, p_h, delta) if w_law is None else w_law
    d_max = log_ub.size
    n = np.arange(d_max + pz.size + 2)
    trials = w - (n + 1) * delta
    ok = trials >= n + 1
    log_cdf = np.zeros(n.size)
    log_cdf[ok] = stats.binom.logcdf(n[ok], trials[ok], p_h)
    # P(N - W - 2 < D) = sum_z P(W = z) P(N <= D + z + 1), for D = 1..d_max
    short = np.correlate(np.exp(log_cdf), pz, "valid")[2:d_max + 2]
    val = np.logaddexp(log_ub, np.log(np.maximum(short, 1e-300)))
    i = int(np.argmin(val))
    return (float(val[i]), i + 1) if val[i] < 0 else (0.0, 0)


def worst_needed(alpha: float, eps: float, delta: int, log_ub: np.ndarray, f: float = F,
                 t_max: int = 6_000_000) -> int:
    """The shortest wait whose worst-case bound is at most ``eps``; -1 past ``t_max``."""
    target = math.log(eps)
    p_h, p_a = occupancy(f, 1 - alpha), occupancy(f, alpha)
    w_law = lead_law(p_a, p_h, delta)
    clock = delta + 1.0 / p_h
    d_eps = int(np.argmax(log_ub <= target)) + 1 if (log_ub <= target).any() else log_ub.size
    hi = int(d_eps * clock) + 4 * delta + 100
    while worst_logbound(hi, alpha, delta, log_ub, f, w_law)[0] > target:
        hi *= 2
        if hi > t_max:
            return -1
    lo = 0
    while hi - lo > 1:
        mid = (lo + hi) // 2
        ok = worst_logbound(mid, alpha, delta, log_ub, f, w_law)[0] <= target
        lo, hi = (lo, mid) if ok else (mid, hi)
    return hi
