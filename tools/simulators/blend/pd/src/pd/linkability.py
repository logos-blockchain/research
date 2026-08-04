"""Linkability over time: how long an adversary needs to link a node to a message (identity), and
how long to certify the node's *stake*, given the structural deanonymization rates.

**Emission model.** Every ``slot_seconds`` (default 30 s) a single node network-wide emits, chosen
with probability proportional to stake, so a node of stake fraction ``s`` emits with probability
``s`` per slot. A node that has >=1 adversarial peer -- the *linkable* set, a fraction
``observed_frac = 1-(1-f_adv)^degree`` of nodes -- has each emission captured **and attributed**
(full deanonymization) with probability ``q = 1-(1-f_adv**blend_hops)**R`` per emission, where ``R``
is the messaging redundancy (R independent cascades, captured if *any* is whole-path-adversarial).
Nodes with no adversarial peer are structurally unlinkable via this mechanism.

Attributable observations therefore arrive as a Bernoulli(``s*q``)-per-slot process:

* **time to link** -- the first attributable observation -- is ``Geometric(s*q)``;
* **time to learn stake** -- accumulate ``N`` attributable observations to estimate the emission
  rate (hence the stake) to relative precision ``~1/sqrt(N)`` -- is the sum of ``N`` such waits,
  mean ``N/(s*q)`` slots.

Linking (identity) is the ``N = 1`` special case of stake learning. Redundancy ``R`` multiplies the
per-emission capture probability from ``d1`` to ``1-(1-d1)**R`` (``~ R*d1`` when ``d1`` is small),
so it cuts every one of these times by roughly ``R``.
"""

from __future__ import annotations

import math

SLOT_SECONDS = 30.0


def redundant(x: float, R: int) -> float:
    """Probability at least one of ``R`` independent trials succeeds: ``1-(1-x)**R``."""
    return 1.0 - (1.0 - x) ** int(R)


def capture_prob(deanon_single: float, observed_frac: float = 1.0, redundancy: int = 1) -> float:
    """Per-emission probability an emission is captured **and** attributed to its sender.

    ``deanon_single`` is the single-cascade whole-path-adversarial prob ``f_adv**blend_hops``.
    For a *linkable* node (already known to have an adversary peer) pass ``observed_frac = 1``; pass
    the population ``observed_frac`` to average over the (unlinkable) nodes with no adversary peer.
    """
    return observed_frac * redundant(deanon_single, redundancy)


def time_to_link_seconds(stake: float, q: float, alpha: float,
                         slot_seconds: float = SLOT_SECONDS) -> float:
    """Time until the node is linked with probability ``alpha`` -- the first attributable
    observation. Exact geometric: ``P(linked by n slots) = 1-(1-s*q)**n``, so
    ``n = ceil(ln(1-alpha)/ln(1-s*q))``. Returns ``inf`` for an unlinkable node (``s*q <= 0``)."""
    p = stake * q
    if p <= 0.0:
        return math.inf
    if p >= 1.0:
        return slot_seconds
    n = math.ceil(math.log(1.0 - alpha) / math.log(1.0 - p))
    return n * slot_seconds


def time_to_stake_seconds(threshold_stake: float, q: float, n_obs: int,
                          slot_seconds: float = SLOT_SECONDS) -> float:
    """Expected time to accumulate ``n_obs`` attributable observations for a node whose stake sits
    at ``threshold_stake`` -- enough to estimate its stake to relative precision ``~1/sqrt(n_obs)``
    and so certify it holds at least that much. Mean of ``n_obs`` Geometric(``theta*q``) waits,
    ``n_obs/(theta*q)`` slots. Returns ``inf`` when the node is unlinkable."""
    p = threshold_stake * q
    if p <= 0.0:
        return math.inf
    return n_obs / p * slot_seconds


def obs_for_precision(rel_precision: float) -> int:
    """Attributable observations needed to estimate the stake to relative std error ``eps``: a count
    of ``N`` events has relative error ``1/sqrt(N)``, so ``N = ceil(1/eps**2)``."""
    return max(1, math.ceil(1.0 / (rel_precision * rel_precision)))


def stake_rel_precision(n_obs: int) -> float:
    """Relative std error of the stake estimate after ``n_obs`` attributable observations."""
    return 1.0 / math.sqrt(n_obs) if n_obs > 0 else math.inf
