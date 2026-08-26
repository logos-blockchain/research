"""Proof of work, simulated rather than executed, and the retarget that steers it.

No grinding happens here. A miner's search is a Bernoulli trial per candidate with success
probability ``difficulty_target / field_modulus``, so over a block the claims a node finds
are Poisson. That is the whole model, and it is exact: nothing is approximated by replacing
the search with its distribution, because the search *is* that distribution.

The retarget is transcribed from the specification's integer arithmetic, not re-derived in
floats, because the controller's behaviour near its bounds depends on the flooring.
"""
from __future__ import annotations

import numpy as np

from .config import FIELD_MODULUS, Config


def expected_claims(hashrate: float, difficulty_target: int, cfg: Config) -> float:
    """Claims a block is expected to draw at the current target.

    | ``expected_claims = hashrate * block_seconds * difficulty_target / field_modulus``

    ``hashrate`` counts candidates per second across the whole network.
    """
    return hashrate * cfg.block_seconds * (difficulty_target / FIELD_MODULUS)


def next_difficulty_target(difficulty_target: int, claims_in_block: int, cfg: Config) -> int:
    """The per-block retarget, in the specification's exact integer form.

    | ``next_difficulty_target = target_claims_per_block * difficulty_target / ((1 - smoothing) * claims_in_block + smoothing * target_claims_per_block)``

    The report shows this one-state map is exactly a normalised exponential moving average of
    demand with weight ``smoothing``, storing the smoothed estimate inside the target itself.
    The ``max`` guards a block that draws no claims at all from dividing by zero, and the
    ``min`` keeps the target inside the field.
    """
    demand = max(1, (cfg.smoothing_precision - cfg.smoothing_factor) * claims_in_block
                 + cfg.smoothing_factor * cfg.target_claims_per_block)
    stepped = (cfg.target_claims_per_block * difficulty_target * cfg.smoothing_precision) // demand
    return min(stepped, FIELD_MODULUS - 1)


def draw_claims_in_block(rng: np.random.Generator, hashrate: float,
                         difficulty_target: int, cfg: Config) -> int:
    """How many claims the whole network finds in one block.

    Drawn once for the network rather than once per node. This is **exact, not an
    approximation**: independent Poisson processes superpose into a Poisson process whose
    rate is the sum of theirs, so a single draw at the aggregate rate has precisely the
    distribution that summing a million per-node draws would have -- and costs one draw
    instead of a million.
    """
    return int(rng.poisson(expected_claims(hashrate, difficulty_target, cfg)))


def attribute(rng: np.random.Generator, claims: int, hashrate_share: np.ndarray) -> np.ndarray:
    """Split a block's claims across nodes, in proportion to the power each brings.

    The companion to :func:`draw_claims_in_block`, and exact for the same reason: conditional
    on the total of independent Poisson counts, the split across sources is multinomial with
    the sources' rate shares. So drawing the total and then dealing it out reproduces the
    per-node joint distribution exactly, at a cost set by the number of claims rather than
    the number of nodes.
    """
    if claims <= 0 or hashrate_share.size == 0:
        return np.zeros(hashrate_share.size, dtype=np.int64)
    total = hashrate_share.sum()
    if total <= 0:
        return np.zeros(hashrate_share.size, dtype=np.int64)
    return rng.multinomial(claims, hashrate_share / total).astype(np.int64)


def equilibrium_difficulty(reward_per_claim: float, claim_fee: float,
                           cost_per_candidate: float) -> float:
    """The target free entry settles on, given what a candidate costs the marginal miner.

    | ``equilibrium_difficulty = field_modulus * cost_per_candidate / (reward_per_claim - claim_fee)``

    As the reward decays this relaxes proportionally, holding the cost of a win pinned to the
    reward. Returns infinity when the margin is not positive: nobody enters, and the target
    is then set by the controller chasing a rate no one supplies rather than by economics.
    """
    margin = reward_per_claim - claim_fee
    if margin <= 0:
        return float("inf")
    return FIELD_MODULUS * cost_per_candidate / margin


def equilibrium_hashrate(reward_per_claim: float, claim_fee: float,
                         cost_per_candidate: float, cfg: Config) -> float:
    """Mining power free entry drives the network to.

    | ``equilibrium_hashrate = target_claims_per_block * (reward_per_claim - claim_fee) / (block_seconds * cost_per_candidate)``

    Independent of the difficulty and of the field size -- those are the dial, not the
    driver. What sets it is money per block over cost per candidate.
    """
    if cost_per_candidate <= 0:
        return float("inf")
    margin = reward_per_claim - claim_fee
    if margin <= 0:
        return 0.0
    return cfg.target_claims_per_block * margin / (cfg.block_seconds * cost_per_candidate)
