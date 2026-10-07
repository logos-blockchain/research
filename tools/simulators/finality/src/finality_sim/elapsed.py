"""Phase B4: a confirmation rule that reads elapsed time (PLAN.md B4; Grunspan and Pérez-Marco,
"Double spend races", 2018).

The private race of B5's depth table (``scripts/b5_what_k_holds.py``): the coalition wins a slot
at rate ``a``; the canonical chain grows at rate ``h``. Just before the target's parent appears the
coalition's lead over the public chain is stationary, geometric with ratio ``rho = a/h`` (B3's
premined race); the parent takes one block from it, or none if it had none. When the ``n``-th
canonical block counting the target appears ``t`` slots after the parent, the coalition holds that
lead plus ``M ~ Poisson(a·t)`` blocks, whatever the times of the honest blocks. It displaces the
target if it is ever strictly ahead, so with lead ``l`` it fails with probability

    P(n, t | l) = P(M ≥ n + 1 − l) + Σ_{m < n + 1 − l} P(M = m) · rho^(n + 1 − l − m),

and ``P(n, t)`` averages this over the lead. Averaged over the time of the ``n``-th block,
``t ~ Gamma(n, h)``, it is the depth table's closed form. The rule accepts the target at the first
canonical block with ``P(n, t) ≤ ε``. Given the honest history the coalition's wins are still
Poisson and its lead independent, so the rule holds ``ε`` for every history, where the depth rule
holds it on average over histories. Without ``lead`` the coalition forks at the parent.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit
from scipy import special, stats


def log_fail(n: int, t: float, a: float, h: float, lead: bool = True) -> float:
    """log P(n, t)."""
    log_rho = math.log(a / h)
    m = np.arange(n + 1)
    log_pm = stats.poisson.logpmf(m, a * t)
    if not lead:
        terms = log_pm + (n + 1 - m) * log_rho
        return float(np.logaddexp(stats.poisson.logsf(n, a * t), special.logsumexp(terms)))
    j = m + 1                                      # the deficit the lead must cover, 1..n + 1
    # sum_{i < j} P(M = i) rho^(j - i), by one accumulation in log space
    log_t = np.logaddexp.accumulate(log_pm - m * log_rho) + j * log_rho
    log_s = np.logaddexp(stats.poisson.logsf(j - 1, a * t), log_t)
    lead_l = n + 1 - j                             # the lead after the parent, n..0
    rho = a / h
    log_pl = np.where(lead_l == 0, math.log1p(-rho * rho),
                      math.log(1 - rho) + (lead_l + 1) * log_rho)
    return float(np.logaddexp((n + 2) * log_rho, special.logsumexp(log_pl + log_s)))


def deadlines(a: float, h: float, eps: float, n_max: int) -> np.ndarray:
    """For n = 1..n_max (index n), the latest t after the parent at which the n-th canonical block
    still settles the target: P(n, t) ≤ eps. -1 where no t does. P(n, t) rises with t."""
    out = np.full(n_max + 1, -1.0)
    target = math.log(eps)
    for n in range(1, n_max + 1):
        if log_fail(n, 0.0, a, h) > target:
            continue
        lo, hi = 0.0, 1.0
        while log_fail(n, hi, a, h) <= target:
            hi *= 2
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if log_fail(n, mid, a, h) <= target else (lo, mid)
        out[n] = lo
    return out


@njit(cache=True)
def settle(canon, deadline, depth):
    """For each target canonical block i (with a parent): the confirmations at which the elapsed-time
    rule and the depth rule accept it, and the slots from the target to each acceptance. -1 where
    the chain ends first."""
    n_c, n_max = canon.size, deadline.size - 1
    k_time = np.full(n_c, -1, np.int64)
    t_time = np.full(n_c, -1, np.int64)
    t_depth = np.full(n_c, -1, np.int64)
    for i in range(1, n_c):
        if i + depth < n_c:
            t_depth[i] = canon[i + depth] - canon[i]
        for n in range(1, n_max + 1):                  # n-th canonical block counting the target
            j = i + n - 1
            if j >= n_c:
                break
            if deadline[n] >= 0 and canon[j] - canon[i - 1] <= deadline[n]:
                k_time[i] = n - 1
                t_time[i] = canon[j] - canon[i]
                break
    return k_time, t_time, t_depth
