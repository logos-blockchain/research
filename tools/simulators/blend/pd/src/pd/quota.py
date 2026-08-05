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

import numpy as np
from scipy.stats import poisson


def assign_stake(n_nodes: int, dist: str, rng: np.random.Generator,
                 zipf_a: float = 1.0) -> np.ndarray:
    """Per-node **true** relative stake ``s = sigma/D``, summing to 1.

    ``uniform`` gives every node ``1/n_nodes`` -- the case where the quota binds on nobody until
    the network is small. ``zipf`` makes stake heavy-tailed (``s ~ 1/rank**zipf_a``), which is what
    real stake looks like and what makes the ceiling bite: the head of the distribution sits orders
    of magnitude above it while the tail sits far below.
    """
    if n_nodes < 1:
        raise ValueError("n_nodes must be >= 1")
    if dist == "uniform":
        s = np.full(n_nodes, 1.0 / n_nodes)
    elif dist == "zipf":
        if zipf_a <= 0:
            raise ValueError("zipf_a must be > 0")
        ranks = np.arange(1, n_nodes + 1, dtype=float)
        s = ranks ** (-zipf_a)
        s = s / s.sum()
        rng.shuffle(s)                       # stake is not correlated with node id
    else:
        raise ValueError(f"unknown stake distribution {dist!r}")
    return s


def quota_summary(stake: np.ndarray, f: float, n_nodes: int, slots_per_epoch: int,
                  rng: np.random.Generator, stake_inference_ratio: float = 1.0,
                  cover_rate_mult: float = 1.0) -> dict:
    """Scalar view of :func:`simulate_epoch_emissions`, for a result row.

    Reports the measured ceiling (where compliance actually breaks) beside the predicted one, so a
    run can be checked against the closed form rather than asked to be believed.
    """
    r = simulate_epoch_emissions(stake, f, n_nodes, slots_per_epoch, rng,
                                 stake_inference_ratio, cover_rate_mult)
    return {
        "quota_per_epoch": float(r["quota"]),
        "compliant_frac": r["compliant_frac"],
        "max_compliant_stake": r["max_compliant_stake"],
        "min_overrun_stake": r["min_overrun_stake"],
        "total_overrun": int(r["overrun"].sum()),
        "top_stake": float(np.max(r["stake"])),
        "alpha_max_predicted": alpha_max(n_nodes, f, cover_rate_mult),
        "s_max_predicted": s_max_true(n_nodes, f, stake_inference_ratio, cover_rate_mult),
        "alpha_max_99": max_alpha_for_confidence(f, n_nodes, slots_per_epoch, 0.99,
                                                 cover_rate_mult),
    }


def inferred_alpha(stake: np.ndarray, stake_inference_ratio: float = 1.0) -> np.ndarray:
    """Convert true relative stake to the **inferred** relative stake the lottery actually uses.

    The threshold is derived from ``D_hat``, so a node's lottery weight is ``sigma/D_hat``, i.e.
    ``s * D/D_hat = s / stake_inference_ratio``. An estimator that runs low makes every node win
    more often, which is why it tightens the true-stake ceiling.
    """
    if stake_inference_ratio <= 0.0:
        raise ValueError("stake_inference_ratio must be > 0")
    return np.asarray(stake, dtype=float) / stake_inference_ratio


def simulate_epoch_emissions(stake: np.ndarray, f: float, n_nodes: int, slots_per_epoch: int,
                             rng: np.random.Generator, stake_inference_ratio: float = 1.0,
                             cover_rate_mult: float = 1.0) -> dict:
    """Measure the quota over one epoch: who wins more proposals than their emission budget.

    Needs no graph -- only the counts matter. Each node's proposals are Binomial over the epoch's
    slots at its lottery probability; a proposal cancels the next scheduled cover, so a node stays
    at exactly its quota while its wins fit inside it and **overruns** once they do not. An
    overrunning node emits more often than everybody else, which is precisely the signal cover
    traffic exists to suppress.
    """
    alpha = inferred_alpha(stake, stake_inference_ratio)
    phi = 1.0 - (1.0 - f) ** alpha
    blocks = rng.binomial(slots_per_epoch, phi)
    quota = quota_per_epoch(n_nodes, slots_per_epoch, cover_rate_mult)
    overrun = np.maximum(0, blocks - math.floor(quota))
    compliant = overrun == 0
    return {
        "stake": np.asarray(stake, dtype=float),
        "alpha": alpha,
        "blocks": blocks,
        "quota": quota,
        "overrun": overrun,
        "compliant": compliant,
        "emissions": np.where(compliant, math.floor(quota), blocks),
        "compliant_frac": float(compliant.mean()),
        "max_compliant_stake": float(stake[compliant].max()) if compliant.any() else 0.0,
        "min_overrun_stake": float(stake[~compliant].min()) if (~compliant).any() else float("nan"),
    }


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

    Uses scipy's survival function rather than summing the series by hand: ``exp(-lam)`` underflows
    to zero past ``lam ~ 745``, which silently collapses a hand-rolled CDF to 0 and reports every
    node as exceeding. That regime is reached as soon as the cover rate is raised (the quota, and
    with it the tolerable block count, grows in proportion).
    """
    lam = expected_blocks_per_epoch(alpha, f, slots_per_epoch)
    quota = quota_per_epoch(n_nodes, slots_per_epoch, cover_rate_mult)
    if lam <= 0.0:
        return 0.0
    return float(poisson.sf(math.floor(quota), lam))


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
