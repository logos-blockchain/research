"""Anonymous-seat committees and their Blend emission cost (PLAN.md D0, D2).

Seats are a private lottery: one seat per note per round, Poisson in number. Honest seats vote
once; adversarial seats vote for both sides; offline honest seats cast nothing. Two conflicting
quorums of ``Q`` need ``H + 2A >= 2Q``; a round stalls when ``H < Q``. The tail functions are
the ones gated in ``firstlook.py``; they are restated here so that the package does not depend
on that script.

The emission cost: every vote is a lottery win, so votes multiply a node's lottery emissions by
``1 + n / (R f)`` for ``n`` expected seats per round of ``R`` slots (``reports/blend`` §3.10).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special, stats


def safety_tail(n: float, alpha: float, q2: int, awake: float = 1.0) -> float:
    mu_h, mu_a = awake * (1 - alpha) * n, alpha * n
    a_max = int(mu_a + 60 * math.sqrt(mu_a + 1) + 60)
    a = np.arange(a_max + 1)
    need = q2 - 2 * a
    log_sf = np.where(need <= 0, 0.0, stats.poisson.logsf(need - 1, mu_h))
    return float(np.exp(special.logsumexp(stats.poisson.logpmf(a, mu_a) + log_sf)))


def liveness_tail(n: float, alpha: float, quorum: int, awake: float = 1.0) -> float:
    return float(stats.poisson.cdf(quorum - 1, awake * (1 - alpha) * n))


def smallest_committee(alpha: float, eps: float, awake: float = 1.0) -> tuple[int, int] | None:
    """Smallest expected committee n, with its quorum Q, holding both tails at or below eps."""
    if alpha >= awake / (2 + awake):
        return None

    def quorum_for(n: int) -> int:
        lo, hi = 0, 2 * n + 10
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if safety_tail(n, alpha, 2 * mid, awake) <= eps:
                hi = mid
            else:
                lo = mid
        return hi

    def ok(n: int) -> bool:
        return liveness_tail(n, alpha, quorum_for(n), awake) <= eps

    hi = 16
    while not ok(hi):
        hi *= 2
        if hi > 2 ** 22:
            return None
    lo = hi // 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi, quorum_for(hi)


def emission_multiplier(n_seats: float, round_slots: float, f: float) -> float:
    """Lottery emissions per unit stake with votes, over blocks alone."""
    return 1.0 + n_seats / (round_slots * f)
