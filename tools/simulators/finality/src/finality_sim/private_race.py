"""The private race under random delay, in closed form (PLAN.md B3–B5).

On a timeline where each chain-extending block is the attacker's with probability ``q``, the
attacker displaces a target once its private chain is strictly longer than the public one
(Cryptarchia's tie rule keeps the first-seen chain). Its lead just before the target is stationary,
geometric with ratio ``rho = q / (1 - q)`` (B3's premined race, ``finality_sim.race``), and its wins
over the ``n - 1`` blocks on top of the target are negative binomial. A deficit of ``j`` is made up
with probability ``rho^j``. Without the lead the attacker forks at the target's parent, and its wins
over all ``n`` blocks counting the target are negative binomial.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special, stats


def log_strict(q: float, n: int, lead: bool = True) -> float:
    """log P(attacker ever strictly ahead) after n honest blocks counting the target."""
    p = 1 - q
    log_rho = math.log(q / p)
    if not lead:
        m = np.arange(n + 1)
        terms = stats.nbinom.logpmf(m, n, p) + (n + 1 - m) * log_rho
        return float(np.logaddexp(stats.nbinom.logsf(n, n, p), special.logsumexp(terms)))
    k, m = n - 1, np.arange(n + 1)
    j = m + 1                                      # the deficit the lead must cover, 1..n + 1
    if k == 0:
        log_s = j * log_rho                        # no blocks on top: no wins there either
    else:
        log_pmf = stats.nbinom.logpmf(m, k, p)
        # sum_{i < j} P(M = i) rho^(j - i), by one accumulation in log space
        log_t = np.logaddexp.accumulate(log_pmf - m * log_rho) + j * log_rho
        log_s = np.logaddexp(stats.nbinom.logsf(j - 1, k, p), log_t)
    lead_l = n + 1 - j                             # a lead of n + 1 - j leaves a deficit of j
    terms = math.log(1 - q / p) + lead_l * log_rho + log_s
    return float(np.logaddexp((n + 1) * log_rho, special.logsumexp(terms)))


def strict_depth(q: float, log_eps: float, lead: bool = True) -> float:
    """The smallest depth at which the private race's closed form is at most exp(log_eps)."""
    if q >= 0.5:
        return math.inf
    lo, hi = 0, 1
    while log_strict(q, hi + 1, lead) > log_eps:
        lo, hi = hi, 2 * hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if log_strict(q, mid + 1, lead) > log_eps else (lo, mid)
    return float(hi)
