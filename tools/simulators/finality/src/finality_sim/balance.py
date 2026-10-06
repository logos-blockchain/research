"""Phase E5: the balancing attack of Gaži, Motaqy and Russell on the slot lottery (PLAN.md E5).

ePrint 2024/1830 (revision 2025-02-20), §5.1: against GHOST with adversarial tie-breaking, an
adversary that delays each honest block until the next one is produced plays the honest blocks of
a phase alternately into two subtrees, and spends one withheld block of its own whenever a phase
ends with the subtrees one apart. Its reserve follows ``A' = A + #a(phase) - (#h(phase) mod 2)``,
and the subtrees stay balanced, so nothing settles, as long as the reserve never falls below zero.
The attack holds forever with positive probability exactly when
``E[#a(phase)] > P(#h(phase) is odd)``; in continuous time that is
``rho_a > rho_h exp(-rho_h Delta) / (2 - exp(-rho_h Delta))`` (``finality_sim.ghost``).

Here the phases come from Cryptarchia's per-note lottery: a slot holds a Poisson number of honest
and of adversarial blocks, at rates ``-(1 - alpha) ln(1 - f)`` and ``-alpha ln(1 - f)``, and a phase
closes after ``delta`` slots without an honest block. The adversary's blocks of quiet phases go
to its reserve. Each block weighs one, as in the DAG of
``finality_sim.areon``; a win weighs once across both subtrees.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit


@njit(cache=True)
def _phases(n_slots, lam_h, lam_a, delta, seed):
    """Honest and adversarial block counts of each phase of n_slots slots.

    Phases tile time (Definition 9): a phase closes at the first slot that ends ``delta`` slots
    without an honest block, so ``delta`` quiet slots form a phase of their own.
    """
    np.random.seed(seed)
    cap = n_slots // max(delta, 1) + 16
    h_out = np.empty(cap, np.int64)
    a_out = np.empty(cap, np.int64)
    n = 0
    h, a, quiet = 0, 0, 0
    for _ in range(n_slots):
        nh = np.random.poisson(lam_h)
        h += nh
        a += np.random.poisson(lam_a)
        quiet = 0 if nh > 0 else quiet + 1
        if quiet >= delta:
            h_out[n] = h
            a_out[n] = a
            n += 1
            h, a, quiet = 0, 0, 0
    return h_out[:n], a_out[:n]


@njit(cache=True)
def _survival(h, a, starts, cap):
    """For each start, the phases the balance holds from there with an empty reserve (at most
    ``cap``)."""
    out = np.empty(starts.size, np.int64)
    for i in range(starts.size):
        reserve = 0
        n = 0
        for j in range(starts[i], min(starts[i] + cap, h.size)):
            reserve += a[j] - (h[j] % 2)
            if reserve < 0:
                break
            n += 1
        out[i] = n
    return out


def drift(f: float, alpha: float, delta: int, n_slots: int, seed: int) -> tuple[float, int]:
    """E[#a] - P(#h odd) per phase on the slot lottery, and the number of phases drawn."""
    lam = -math.log(1.0 - f)
    h, a = _phases(n_slots, (1.0 - alpha) * lam, alpha * lam, delta, seed)
    return float(a.mean() - (h % 2).mean()), int(h.size)


def hold_shares(f: float, alpha: float, delta: int, horizons: tuple[int, ...], n_slots: int,
                seed: int, starts: int = 1000) -> list[float]:
    """Share of attempts, begun at evenly spaced phases with an empty reserve, that keep the
    balance for each horizon (in phases); every horizon is read off the same attempts."""
    lam = -math.log(1.0 - f)
    h, a = _phases(n_slots, (1.0 - alpha) * lam, alpha * lam, delta, seed)
    cap = max(horizons)
    if h.size <= cap:
        raise ValueError("too few phases for the longest horizon")
    idx = np.linspace(0, h.size - cap - 1, starts).astype(np.int64)
    held = _survival(h, a, idx, cap)
    return [float((held >= k).mean()) for k in horizons]


def phase_stats(f: float, alpha: float, delta: int) -> tuple[float, float, float]:
    """E[#a], P(#h odd) and P(#h > 0) per phase of the slot lottery, in closed form.

    A slot is quiet with probability ``p = exp(-lam_h)``. A phase lasts until ``delta`` quiet slots
    in a row, ``(p**-delta - 1) / (1 - p)`` slots on average, and holds ``B`` busy slots with
    ``P(B = b) = (1 - p**delta)**b p**delta``. A busy slot's honest count is Poisson given at least
    one, whose ``E[(-1)**N]`` is ``-p``; so ``E[(-1)**#h] = p**delta / (1 + (1 - p**delta) p)``.
    """
    lam = -math.log(1.0 - f)
    lam_h, lam_a = (1.0 - alpha) * lam, alpha * lam
    p = math.exp(-lam_h)
    q = p ** delta
    mean_len = (1.0 / q - 1.0) / (1.0 - p)
    sign = q / (1.0 + (1.0 - q) * p)
    return lam_a * mean_len, (1.0 - sign) / 2.0, 1.0 - q


def threshold(f: float, delta: int, ties: str) -> float:
    """The smallest adversary share whose reserve drifts upward: the edge of the safe region.

    ``ties="adversarial"``: a phase costs a block when its honest count is odd (§5.1);
    ``ties="deterministic"``: when it holds any honest block (§5.2).
    """
    def gain(alpha):
        a, odd, busy = phase_stats(f, alpha, delta)
        return a - (odd if ties == "adversarial" else busy)

    lo, hi = 1e-9, 0.5
    for _ in range(100):
        mid = (lo + hi) / 2
        if gain(mid) < 0:
            lo = mid
        else:
            hi = mid
    return lo

