"""Emission budget: how much stake a node can hold and still look like everyone else.

Cover traffic gives every node the **same number of emissions per epoch**. A node emits in a slot
either because a cover slot came up or because it won the block lottery, and a block cancels the
next scheduled cover, so the emission *count* carries no information about who produces blocks --
that uniformity is the anonymity property cover traffic buys.

It only holds while a node's block proposals fit inside its quota. The quota is

    q = cover_rate_mult / n_nodes          emissions per node per slot

and the Cryptarchia lottery gives a node of **inferred** relative stake ``alpha = sigma / D_hat``
a per-slot win probability ``phi(alpha) = 1 - (1-f)**alpha``. Requiring ``phi(alpha) <= q``:

    alpha_max = ln(1 - q) / ln(1 - f)

Note the stake here is relative to the *inferred* total ``D_hat``, not the true total ``D``, because
that is the denominator the lottery threshold is derived from. Converting to true relative stake
``s = sigma / D`` therefore needs the estimator's accuracy ratio: since every node's win rate scales
with ``D/D_hat``, the network's block rate is ``f * D/D_hat`` and

    s_max = (D_hat / D) * alpha_max

so an estimator that runs low tightens the true-stake ceiling in exact proportion. ``D_hat/D`` is an
input here (``stake_inference_ratio``), measured by the consensus-side study, not assumed to be 1.

``alpha_max`` is the *mean* bind. Wins are a Bernoulli process, so a node sitting exactly at it
overruns its quota in about half of all epochs; ``max_alpha_for_confidence`` gives the ceiling that
keeps the quota with a stated probability.
"""

from __future__ import annotations

import math


def emission_quota_per_slot(n_nodes: int, cover_rate_mult: float = 1.0) -> float:
    """Emissions allowed per node per slot. The default rate puts one emission per slot on the
    whole network, so each node gets ``1/n_nodes``."""
    if n_nodes < 1:
        raise ValueError("n_nodes must be >= 1")
    return cover_rate_mult / n_nodes


def win_prob(alpha: float, f: float) -> float:
    """Cryptarchia per-slot block-lottery probability for inferred relative stake ``alpha``."""
    if not (0.0 < f < 1.0):
        raise ValueError("need 0 < f < 1")
    return 1.0 - (1.0 - f) ** alpha


def alpha_max(n_nodes: int, f: float, cover_rate_mult: float = 1.0) -> float:
    """Largest **inferred** relative stake whose expected block rate fits the emission quota.

    Exact bind ``ln(1-q)/ln(1-f)``; the familiar ``q/f`` is a small-q approximation that runs
    about 1.7 % high at f = 1/30 and so overstates the tolerable stake.
    """
    q = emission_quota_per_slot(n_nodes, cover_rate_mult)
    if q >= 1.0:
        return math.inf                      # quota exceeds one emission per slot: never binds
    return math.log1p(-q) / math.log1p(-f)


def s_max_true(n_nodes: int, f: float, stake_inference_ratio: float = 1.0,
               cover_rate_mult: float = 1.0) -> float:
    """The ceiling expressed in **true** relative stake, ``(D_hat/D) * alpha_max``."""
    if stake_inference_ratio <= 0.0:
        raise ValueError("stake_inference_ratio must be > 0")
    return stake_inference_ratio * alpha_max(n_nodes, f, cover_rate_mult)


def expected_blocks_per_epoch(alpha: float, f: float, slots_per_epoch: int) -> float:
    """Expected proposals won by a node of inferred relative stake ``alpha`` over one epoch."""
    return win_prob(alpha, f) * slots_per_epoch


def quota_per_epoch(n_nodes: int, slots_per_epoch: int, cover_rate_mult: float = 1.0) -> float:
    """Emissions a node is allowed in one epoch."""
    return emission_quota_per_slot(n_nodes, cover_rate_mult) * slots_per_epoch


def quota_exceedance_prob(alpha: float, f: float, n_nodes: int, slots_per_epoch: int,
                          cover_rate_mult: float = 1.0) -> float:
    """P(a node of inferred stake ``alpha`` wins more proposals in an epoch than its quota).

    Wins are Binomial(slots_per_epoch, phi(alpha)); the Poisson limit is used, which is accurate
    here because phi is tiny and the epoch is long.
    """
    lam = expected_blocks_per_epoch(alpha, f, slots_per_epoch)
    quota = quota_per_epoch(n_nodes, slots_per_epoch, cover_rate_mult)
    k = math.floor(quota)
    # P(X > k) for X ~ Poisson(lam), summed up from 0 (k is small in every regime of interest)
    if lam <= 0.0:
        return 0.0
    term = math.exp(-lam)
    cdf = term
    for i in range(1, k + 1):
        term *= lam / i
        cdf += term
    return max(0.0, min(1.0, 1.0 - cdf))


def max_alpha_for_confidence(f: float, n_nodes: int, slots_per_epoch: int,
                             confidence: float = 0.99,
                             cover_rate_mult: float = 1.0) -> float:
    """Largest inferred stake that keeps inside the quota with probability ``confidence``.

    Always below :func:`alpha_max`, because a node sitting on the mean bind overruns half the time.
    """
    if not (0.0 < confidence < 1.0):
        raise ValueError("need 0 < confidence < 1")
    lo, hi = 0.0, alpha_max(n_nodes, f, cover_rate_mult)
    if not math.isfinite(hi):
        return hi
    tol = 1.0 - confidence
    for _ in range(80):                      # bisection on a monotone exceedance probability
        mid = 0.5 * (lo + hi)
        p = quota_exceedance_prob(mid, f, n_nodes, slots_per_epoch, cover_rate_mult)
        lo, hi = (mid, hi) if p <= tol else (lo, mid)
    return lo
