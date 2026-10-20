"""Phase J, J.3: the region the convergence-opportunity technique certifies on the slot lottery
(PLAN.md J.3, DAG.md J.3).

Kiffer, Rajaraman and shelat (CCS 2018; ePrint 2022/601) prove GHOST consistent while convergence
opportunities outnumber the adversary's blocks (Theorem 4.4, Corollary 6.4). An opportunity is
``Delta`` slots without an honest block, one slot with exactly one, and ``Delta`` more without:
every honest party then follows the same heaviest path, and the adversary must spend a block to
break it. Gaži, Motaqy and Russell (ePrint 2024/1830, revision 2025-02-20, p. 2) put the region
this technique gives at ``rho_a < rho_h exp(-2 rho_h Delta)`` in continuous time.

On Cryptarchia's per-note lottery a slot holds a Poisson number of honest wins, at rate
``-(1 - alpha) ln(1 - f)``, and of adversarial wins, at ``-alpha ln(1 - f)``; with one weight per
win (E3) the adversary spends one win per opportunity it breaks. A slot opens an opportunity with
probability ``lam_h exp(-(2 Delta + 1) lam_h)``.
"""

from __future__ import annotations

import math

import numpy as np

from finality_sim.balance import phase_stats


def rate(f: float, alpha: float, delta: int) -> float:
    """Convergence opportunities per slot."""
    lam_h = -(1.0 - alpha) * math.log(1.0 - f)
    return lam_h * math.exp(-(2 * delta + 1) * lam_h)


def edge(f: float, delta: int, events: int = 1) -> float:
    """The largest adversary share whose wins per slot, ``events`` changes each, stay below the
    opportunities per slot."""
    lam = -math.log(1.0 - f)
    lo, hi = 0.0, 0.5
    for _ in range(100):
        mid = (lo + hi) / 2
        if events * mid * lam < rate(f, mid, delta):
            lo = mid
        else:
            hi = mid
    return lo


def retraction_threshold(f: float, delta: int, ties: str) -> float:
    """The balancing attack's edge when every win moves the balance twice, once when placed and
    once when a second copy on the other side retracts it (J.1): the smallest share with
    ``2 E[#a] >= P(the phase costs a move)``, a move per odd phase with ties steered and per
    phase holding an honest block with a fixed rule (``finality_sim.balance``)."""
    def gain(alpha):
        a, odd, busy = phase_stats(f, alpha, delta)
        return 2.0 * a - (odd if ties == "adversarial" else busy)

    lo, hi = 1e-9, 0.5
    for _ in range(100):
        mid = (lo + hi) / 2
        if gain(mid) < 0:
            lo = mid
        else:
            hi = mid
    return lo


def simulated_rate(f: float, alpha: float, delta: int, n_slots: int, seed: int) -> tuple[float, int]:
    """Opportunities per slot counted on a drawn honest lottery, and their number."""
    rng = np.random.default_rng(seed)
    honest = rng.poisson(-(1.0 - alpha) * math.log(1.0 - f), n_slots)
    busy = np.concatenate(([0], np.cumsum(honest > 0)))
    s = np.arange(delta, n_slots - delta)
    quiet_before = busy[s] - busy[s - delta] == 0
    quiet_after = busy[s + delta + 1] - busy[s + 1] == 0
    count = int(np.count_nonzero(quiet_before & (honest[s] == 1) & quiet_after))
    return count / s.size, count
