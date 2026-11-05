"""Phase M: certificates from other signers (PLAN.md Phase M).

Closed forms that set the signer sets beside one another.

**What each set holds (M.1).** A certificate needs a quorum of the signing weight. The coalition
holds a share ``α`` of the active stake and a share ``a`` of the weight.

- *Delegated weight.* Every note may delegate its voting weight to a declared operator. The
  coalition delegates all of its stake to its own operators. Honest holders delegate a share ``v``
  of the honest stake, of which a share ``c`` reaches the coalition's operators, so
  ``a = (α + (1 − α)c) / (α + (1 − α)v)``. With ``c = 0`` this is D1b's opt-in committee, and with
  ``v = 1`` and ``c = 0`` it is every leading note declared, ``a = α``.
- Safety needs ``a < 2q − 1``, and liveness ``u(1 − a) ≥ q`` for a share ``u`` of the honest
  weight online (``netcert.safe`` and ``netcert.live``).
- *The chain's own leaders.* The committee is the lottery wins a finalized window of the chain
  records, canonical or referenced as uncles, one weight per distinct win tag ``ρ_LEAD``. Every node
  counts them, so the quorum ``Q`` is set from the count ``n``. If the coalition keeps no honest win
  out of the record, its wins are ``A ~ Bin(n, α)``. Two conflicting certificates need
  ``A ≥ 2Q − n``, and a round stalls when the honest wins online, ``Bin(n, (1 − α)u)``, fall short
  of ``Q``. Anonymous seats differ: nobody counts them, so D0 sizes their quorum against a Poisson
  number of seats.

**How fast (M.2).** With rounds of ``R`` slots and a lag ``L``, a block at slot ``s`` first lies in
a round's target at the first round start ``t ≥ s + L``. A single certificate holds it once the
quorum's votes have arrived, and the checkpoint gadget finalizes it one round later. Averaged over a
round that is ``L + (R − 1)/2`` and ``L + (R − 1)/2 + R`` slots, plus the time the quorum's votes take.

Votes through Blend take Blend's budget (D3; ``committee.blend_load``). A Blend round is one second.
Today a core connection carries ``F_1 = (max(F_C(1 + R_C), F_D(1 + R_D)) + F_T)·β_max = 16``
messages a round, which the specification sizes so that a backlog drains, against a read limit
``r_1 = 20``. A won slot takes its node's next scheduled cover message, which the ``max`` reads, and a
vote can do the same. On top of today's cover, a vote that fits its node's cover adds nothing, and
the votes beyond each node's cover must fit the headroom between the two, ``4/3`` messages a second:
the budget lies between ``4/3`` votes a second, when no vote fits a node's cover, and
``F_C(1 + R_C) − F_D(1 + R_D) + 4/3`` with equal stakes (``vote_budget``). With the cover raised by
the emission multiple ``x = 1 + n/(R·f)`` to keep today's quota ceiling, a vote costs ``1/f`` cover
messages. Keeping the headroom for the backlog instead means taking the same number of messages from
the transactions, ``F_T``. Blend carries the votes evenly over a round, so the quorum's last vote
leaves ``R·Q/H`` into it, for ``H`` honest votes when the coalition withholds its own.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from finality_sim import committee as cm
from finality_sim.netcert import Q, holds

F = 1 / 30


def delegated_share(alpha: float, delegated: float = 1.0, attracted: float = 0.0) -> float:
    """The coalition's share of the delegated weight: its own stake ``alpha``, all of it on its own
    operators, and the share ``attracted`` of the honest stake its operators hold, over the
    coalition's stake and the share ``delegated`` of the honest stake delegated at all."""
    if not 0.0 <= attracted <= delegated <= 1.0:
        raise ValueError("needs 0 <= attracted <= delegated <= 1")
    return (alpha + (1 - alpha) * attracted) / (alpha + (1 - alpha) * delegated)


def largest_attracted(alpha: float, uptime: float = 1.0, delegated: float = 1.0,
                      q: float = Q) -> float | None:
    """The share of the honest stake below which the coalition's operators may hold delegation and
    leave the set safe and live; ``None`` when the set fails with none of it. Safety is lost at
    the value itself, liveness just above it."""
    if not holds(delegated_share(alpha, delegated, 0.0), uptime, q):
        return None
    total = alpha + (1 - alpha) * delegated
    c_safe = ((2 * q - 1) * total - alpha) / (1 - alpha)          # a < 2q − 1
    c_live = delegated - q * total / (uptime * (1 - alpha))       # u(1 − a) ≥ q
    return min(c_safe, c_live)


def least_uptime(alpha: float, q: float = Q) -> float:
    """The least share of the honest weight online that keeps a set live when the coalition holds
    the share ``alpha`` of the weight, ``q / (1 − alpha)``; ``inf`` above one."""
    u = q / (1 - alpha)
    return u if u <= 1 + 1e-12 else math.inf


def known_committee(alpha: float, eps: float, uptime: float = 1.0) -> tuple[int, int] | None:
    """The fewest wins ``n``, with the quorum ``Q``, of a committee whose size every node counts:
    the coalition's wins are ``Bin(n, alpha)``; two conflicting certificates need ``2Q − n`` of them,
    with probability at most ``eps``; the honest wins online, ``Bin(n, (1 − alpha)·uptime)``, fall
    short of ``Q`` with probability at most ``eps``. ``None`` where no committee exists: the
    quorum must exceed ``(1 + alpha)·n/2`` and stay below ``(1 − alpha)·uptime·n``."""
    p_on = (1 - alpha) * uptime
    if p_on <= (1 + alpha) / 2:
        return None

    def quorum_for(n: int) -> int | None:
        """The smallest quorum that keeps two conflicting certificates within ``eps``; the
        safety tail falls as the quorum rises."""
        qs = np.arange(n // 2, n + 1)
        safe = stats.binom.sf(2 * qs - n - 1, n, alpha) <= eps
        return int(qs[np.argmax(safe)]) if safe.any() else None

    def ok(n: int) -> bool:
        qn = quorum_for(n)
        return qn is not None and stats.binom.cdf(qn - 1, n, p_on) <= eps

    hi = 8
    while not ok(hi):
        hi *= 2
        if hi > 2 ** 22:
            return None
    for n in range(1, hi + 1):          # the lattice makes ``ok`` uneven in n: scan, do not bisect
        if ok(n):
            return n, quorum_for(n)
    return None


def leaders_window(n_wins: float, f: float = F) -> float:
    """The slots in which the chain records ``n_wins`` lottery wins at the rate ``f``."""
    return n_wins / f


def headroom() -> float:
    """The messages a second, network-wide, that take a core connection from today's ``F_1`` to its
    read limit ``r_1``: 4/3 at the specification's parameters."""
    return (cm.R_1 / cm.BETA_MAX - max(cm.F_C * (1 + cm.R_C), cm.F_D * (1 + cm.R_D))
            - cm.F_T)


def cover_room() -> float:
    """``x − 1`` for the largest emission multiple ``x`` a raised cover can take with every core
    connection within ``r_1``: 4/3 at the specification's parameters."""
    return (cm.R_1 / cm.BETA_MAX - cm.F_T) / (cm.F_C * (1 + cm.R_C)) - 1


def vote_rate(cover: str = "on top", f: float = F) -> float:
    """The votes a second, network-wide, that fill the headroom: one message a vote on top of
    today's cover, ``1/f`` cover messages a vote with the cover raised."""
    if cover == "on top":
        return headroom()
    if cover == "raised":
        return f * cover_room()
    raise ValueError(f"unknown cover mode {cover!r}")


def vote_budget(stakes, tol: float = 1e-12) -> float:
    """The votes a second, network-wide, that Blend carries when a vote takes its node's next
    scheduled cover message, as a won slot does, and only a node's emissions beyond its cover add
    load. Node ``i`` of ``N`` holds the share ``s_i`` of the stake and emits cover at
    ``F_C(1 + R_C)/N`` a second, proposals at ``F_D(1 + R_D)·s_i`` and votes at ``v·s_i``. The budget
    is the largest ``v`` whose added emissions fit the headroom: ``4/3`` when no vote fits a node's
    cover, and ``F_C(1 + R_C) − F_D(1 + R_D) + 4/3`` with equal stakes."""
    s = np.asarray(stakes, dtype=float)
    s = s / s.sum()
    q = cm.F_C * (1 + cm.R_C) / s.size
    prop = cm.F_D * (1 + cm.R_D) * s
    today = np.maximum(q, prop).sum()

    def added(v: float) -> float:
        return float(np.maximum(q, prop + v * s).sum() - today)

    room = headroom()
    lo, hi = 0.0, 1.0
    while added(hi) <= room:
        lo, hi = hi, 2 * hi
    while hi - lo > tol:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if added(mid) <= room else (lo, mid)
    return lo


def transaction_share(messages_per_s: float) -> float:
    """The share of Blend's transaction messages that ``messages_per_s`` take, if the headroom is
    kept for the backlog."""
    return messages_per_s / cm.F_T


def shortest_round(n_seats: float, cover: str = "on top", f: float = F) -> float:
    """The shortest round, in slots of one second, in which ``n_seats`` votes fit the headroom:
    ``n / (4/3)`` on top of today's cover, ``n / (f·4/3)`` with the cover raised."""
    return n_seats / vote_rate(cover, f)


def emission_time(quorum: float, honest: float, round_slots: float) -> float:
    """When the quorum's last honest vote leaves, into a round over which Blend carries the votes
    evenly: ``R·Q/H`` for ``H`` honest votes."""
    return round_slots * quorum / honest


def finality_time(lag: float, round_slots: float, rounds: int = 2,
                  delivery: float = 0.0) -> float:
    """The mean slots from a block's slot until it is final: the lag, the wait for the next round
    start, ``(R − 1)/2`` on average, ``rounds − 1`` further rounds, and the time the quorum's votes
    take to leave and arrive. ``rounds`` is 2 for the checkpoint gadget and 1 for a single
    certificate."""
    return lag + (round_slots - 1) / 2 + (rounds - 1) * round_slots + delivery


def latest_time(lag: float, round_slots: float, rounds: int = 2, delivery: float = 0.0) -> float:
    """The slots until final for the block placed worst in a round, one slot past a round's target,
    which waits ``R − 1`` slots for the next round start."""
    return lag + (round_slots - 1) + (rounds - 1) * round_slots + delivery


def link_chance(messages: float, q: float) -> float:
    """The chance that at least one of ``messages`` messages is attributed to its sender's node,
    each with ``q``."""
    return 1 - (1 - q) ** messages


def leader_votes(cover: str = "on top", f: float = F, rate: float | None = None) -> float:
    """The votes a leader casts for one win while the win sits in the committee: the window,
    ``n/f`` slots, over rounds of ``n / rate`` slots, at ``rate`` votes a second or the mode's."""
    return (vote_rate(cover, f) if rate is None else rate) / f
