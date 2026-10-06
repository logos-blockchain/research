"""Anonymous-seat committees and their Blend emission cost (PLAN.md D0, D2).

Seats are a private lottery: one seat per note per round, Poisson in number. Honest seats vote
once; adversarial seats vote for both sides. Two conflicting quorums of ``Q`` need
``H + 2A >= 2Q``, counting every honest seat: honest votes split between the two sides still fill
both. A round stalls when the honest votes that count for one side, a share ``awake`` of the honest
seats, fall short of ``Q``. Expected seats are ``n`` times ``D/D̂``, the true over the inferred
stake; ``Q`` must hold safety at the largest ``D/D̂`` it is sized for (``inflation``), and liveness
at ``D/D̂ = 1``, the fewest seats. At ``awake = inflation = 1`` the tails are the ones gated in
``firstlook.py``, restated here so that the package does not depend on that script.

The emission cost: every vote is a lottery win, so votes multiply a node's lottery emissions by
``1 + n / (R f)`` for ``n`` expected seats per round of ``R`` slots (``reports/blend`` §3.10).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special, stats


def safety_tail(n: float, alpha: float, q2: int, inflation: float = 1.0) -> float:
    """P(H + 2A >= q2), every honest seat voting, with ``n`` scaled by ``inflation``."""
    mu_h, mu_a = inflation * (1 - alpha) * n, inflation * alpha * n
    a_max = int(mu_a + 60 * math.sqrt(mu_a + 1) + 60)
    a = np.arange(a_max + 1)
    need = q2 - 2 * a
    log_sf = np.where(need <= 0, 0.0, stats.poisson.logsf(need - 1, mu_h))
    return float(np.exp(special.logsumexp(stats.poisson.logpmf(a, mu_a) + log_sf)))


def liveness_tail(n: float, alpha: float, quorum: int, awake: float = 1.0) -> float:
    """P(the honest votes that count for one side fall short of the quorum)."""
    return float(stats.poisson.cdf(quorum - 1, awake * (1 - alpha) * n))


def smallest_committee(alpha: float, eps: float, awake: float = 1.0,
                       inflation: float = 1.0) -> tuple[int, int] | None:
    """Smallest expected committee n, with its quorum Q, holding both tails at or below eps.

    For large n the quorum must exceed ``inflation (1 + alpha) n / 2`` and stay below
    ``awake (1 - alpha) n``, so no committee exists once ``awake (1 - alpha)`` falls to
    ``inflation (1 + alpha) / 2``.
    """
    if awake * (1 - alpha) <= inflation * (1 + alpha) / 2:
        return None

    def quorum_for(n: int) -> int:
        lo, hi = 0, 2 * n + 10
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if safety_tail(n, alpha, 2 * mid, inflation) <= eps:
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


# Blend at logos-lips 47a73cdc (blend-protocol.md, Global Parameters and Expected Traffic): cover,
# block-proposal and transaction messages per round network-wide, their replications, blending
# operations per message, the messages a node reads from a core connection per round, and the
# verifications per second of the slowest node the protocol targets.
F_C, F_D, F_T = 1.0, 1 / 30, 130 / 30
R_C, R_D = 0, 1
BETA_MAX, R_1, V = 3, 20, 156


def blend_load(votes: float, cover_multiple: float | None = None) -> tuple[float, float]:
    """``F_1``, the messages a core connection carries per round, and the verifications a node
    makes per round: a header for every novel message and a proof for every vote.

    Votes are Blend messages that are not replicated, ``votes`` per round network-wide. Without
    ``cover_multiple`` they come on top of today's cover, and the quota ceiling falls (D0). With it,
    the cover rate rises by that multiple and carries the votes.
    """
    if cover_multiple is None:
        cover, extra = F_C * (1 + R_C), votes
    else:
        cover, extra = cover_multiple * F_C * (1 + R_C), 0.0
    f1 = (max(cover, F_D * (1 + R_D)) + F_T + extra) * BETA_MAX
    return f1, f1 + votes
