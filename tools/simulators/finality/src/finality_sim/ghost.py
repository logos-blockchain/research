"""Phase C3: the consistency regions of GHOST and of the longest-chain rule (PLAN.md C3).

Gaži, Motaqy, Russell, "A Tight Analysis of GHOST Consistency", ePrint 2024/1830 (revision
2026-09-11, p. 3): honest and adversarial blocks arrive as Poisson processes of rates ``rho_h``
and ``rho_a`` per unit time (the paper's lambda_h and lambda_a), and the adversary delays honest
blocks by up to ``Delta``. The regions are its inequality on p. 3 and equations (1) and (2):

- Longest-chain rule: consistent exactly when ``rho_a < 1 / (Delta + 1/rho_h)``.
- GHOST, deterministic tie-breaking: ``rho_a < rho_h exp(-rho_h Delta)``.
- GHOST, adversarial tie-breaking: ``rho_a < rho_h exp(-rho_h Delta) / (2 - exp(-rho_h Delta))``.

The analysis is for proof of work. For proof of stake the paper notes that GHOST "provides no
security (for any parameters) with unconstrained equivocation" (p. 8), so these regions apply to
Cryptarchia only if one lottery win can add weight once.
"""

from __future__ import annotations

import math


def lcr(rho_h: float, delta: float) -> float:
    return 1.0 / (delta + 1.0 / rho_h)


def ghost_deterministic(rho_h: float, delta: float) -> float:
    return rho_h * math.exp(-rho_h * delta)


def ghost_adversarial(rho_h: float, delta: float) -> float:
    e = math.exp(-rho_h * delta)
    return rho_h * e / (2.0 - e)


RULES = {"longest chain": lcr, "GHOST, deterministic ties": ghost_deterministic,
         "GHOST, adversarial ties": ghost_adversarial}


def max_share(rule, f: float, delta: float) -> float:
    """Largest adversary stake share ``b`` with ``b f < rule((1 - b) f, Delta)``."""
    lo, hi = 0.0, 0.5
    for _ in range(100):
        mid = (lo + hi) / 2
        if mid * f < rule((1 - mid) * f, delta):
            lo = mid
        else:
            hi = mid
    return lo
