"""The active stake as a share of the supply (SIGNERS.md M.7).

Cryptarchia's lottery weighs a note against the total active stake, which every node infers from the
chain's growth (`cryptarchia-total-stake-inference.md`), so every share in the study is a share of
the active stake. With the active stake at most a share of the supply, as the block rewards' target
of 30 % puts it, stake outside it can enter the lottery without notice, and until the inference's
next correction the true active stake exceeds the inferred by a factor ``x``. The sets whose quorum
reads the inference, the anonymous seats and the slot rule's lottery, see ``x``; a counted
committee and a declared or tallied weight do not.
"""

from __future__ import annotations

import math

from finality_sim import committee as cm
from finality_sim import netcert as nc

F = 1 / 30


def supply_share(alpha: float, active: float = nc.STAKED_SHARE) -> float:
    """The most of the supply a coalition holding ``alpha`` of the active stake can hold."""
    return alpha * active


def entering(alpha: float) -> float:
    """The true over the inferred active stake once the coalition's stake enters from outside.

    The inference then holds the honest stake ``H`` alone, as after a deflation (FURTHER.md G7),
    and the coalition holds ``alpha`` of the true stake: ``(H + A)/H`` with ``A = alpha (H + A)``.
    """
    return 1 / (1 - alpha)


def seats_edge() -> float:
    """The least coalition against which no anonymous committee exists once its stake enters.

    ``committee.smallest_committee`` has none once ``1 − α ≤ x(1 + α)/2``; at ``x = 1/(1 − α)``
    that is ``2α² − 5α + 1 ≤ 0``, whose lower root this is.
    """
    return (5 - math.sqrt(17)) / 4


def honest_entry_break(alpha: float, eps: float, sized: float = 1.05, hi: float = 4.0,
                       tol: float = 1e-6) -> float:
    """The least ``x`` from honest stake entering at which the anonymous committee sized against
    ``alpha`` for an inference error up to ``sized`` no longer holds safety at ``eps``.

    The coalition keeps its stake, so it holds ``alpha/x`` of the true stake, and every honest seat
    counts for safety, as D2 counts it."""
    n, q = cm.smallest_committee(alpha, eps, inflation=sized)

    def safe(x: float) -> bool:
        return cm.safety_tail(n, alpha / x, 2 * q, x) <= eps

    lo = 1.0
    if not safe(lo) or safe(hi):
        raise ValueError("the bracket does not hold the edge")
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if safe(mid):
            lo = mid
        else:
            hi = mid
    return hi


def lottery_chance(x: float, f: float = F) -> float:
    """The chance that a slot is won when the true active stake is ``x`` times the inferred."""
    return 1 - (1 - f) ** x


def least_inferred(edge: float, active: float = nc.STAKED_SHARE) -> float:
    """The least inferred active stake, as a share of the supply, at which the true active stake,
    at most ``active`` of the supply, stays within ``edge`` times it."""
    return active / edge


def declarations_cap(active: float = nc.STAKED_SHARE,
                     minimum: float = nc.MIN_STAKE_SHARE) -> int:
    """The most declarations the active stake can make, each holding at least the minimum stake."""
    return math.floor(active / minimum + 1e-9)
