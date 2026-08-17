"""ALTERNATIVE: a claim target that accommodates joiners instead of being fixed.

**Variant. Not part of the base model.** See this package's docstring.

The proposal is that ``target_claims_per_block`` should respond to how many nodes are trying
to join, rather than sitting at a constant, so that a busy on-ramp is not throttled by a
number chosen before anyone arrived.

The study's first question is which constraint the on-ramp is actually against -- the money
available, or the number of claim slots -- because the proposal only helps if it is slots.

**The invariance that decides it.** A node holding hashrate share ``s`` wins ``s`` of every
claim, and needs enough claims to reach the minimum stake:

.. code-block:: text

    claims_to_graduate  = min_stake / reward_per_claim
                        = min_stake * target_claims_per_block * blocks_per_epoch
                          / (distribution_rate * pool)

    claims_won_per_epoch = hashrate_share * target_claims_per_block * blocks_per_epoch

    epochs_to_graduate  = claims_to_graduate / claims_won_per_epoch
                        = min_stake / (distribution_rate * pool * hashrate_share)

``target_claims_per_block`` cancels exactly. It appears in the numerator of what a graduate
needs and in the denominator of what it earns, because the pool pays out
``distribution_rate * pool`` per epoch whatever the target is -- the target divides that sum
into more pieces, it does not enlarge it.

So the on-ramp is against MONEY, not slots, and raising the target does nothing for it. What
raising it does do is spend block space and thin the self-funding margin. Both are measured
below rather than argued.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .. import economics, engine, market
from ..config import Config
from ..nodes import Population
from ..scenarios import Scenario


# ------------------------------------------------------------------ target policies

def fixed_target(value: int):
    """The base mechanism: a constant, whatever arrives."""
    def policy(cfg: Config, epoch: int, joiners_recent: float) -> int:
        return value
    policy.label = f"fixed@{value}"        # type: ignore[attr-defined]
    return policy


def joiner_responsive(claims_per_joiner: float, floor: int = 1, cap: int | None = None):
    """The variant: the target tracks recent arrivals.

    ``cap`` defaults to the block transaction limit, because the target is claims per block
    and a block cannot carry more transactions than that -- past the cap the mechanism is
    not merely aggressive, it is unimplementable.
    """
    def policy(cfg: Config, epoch: int, joiners_recent: float) -> int:
        ceiling = cfg.max_block_txs if cap is None else cap
        return int(max(floor, min(ceiling, round(claims_per_joiner * joiners_recent))))
    policy.label = f"joiners*{claims_per_joiner:g}"   # type: ignore[attr-defined]
    return policy


# ------------------------------------------------------------------ the analytic claim

def epochs_to_graduate(cfg: Config, pool: int, hashrate_share: float,
                       target_claims_per_block: int | None = None) -> float:
    """Epochs a miner needs to reach the minimum stake.

    | ``epochs_to_graduate = min_stake / (distribution_rate * pool * hashrate_share)``

    Takes a target only so a caller can pass different ones and watch the answer not move.
    """
    if hashrate_share <= 0 or pool <= 0:
        return float("inf")
    return cfg.min_stake / (cfg.distribution_rate * pool * hashrate_share)


def graduations_per_epoch(cfg: Config, pool: int) -> float:
    """How many minimum stakes an epoch's payout can fund. Also free of the target.

    | ``graduations_per_epoch = distribution_rate * pool / min_stake``
    """
    return cfg.distribution_rate * pool / cfg.min_stake


def block_space_share(cfg: Config, target_claims_per_block: int) -> float:
    """Fraction of a block's transaction capacity the claims themselves consume."""
    return target_claims_per_block / cfg.max_block_txs


def self_funding_margin(cfg: Config, target_claims_per_block: int,
                        txs_per_block: int | None = None) -> float:
    """The steady-state reward over the claim's own fee, at a given target.

    | ``reward_over_fee = fee_ratio * pow_share * txs_per_block / target_claims_per_block``

    Falls inversely in the target, which is the price the variant pays: a target raised to
    admit joiners thins the margin that decides whether mining pays at all.
    """
    n = cfg.txs_per_block if txs_per_block is None else txs_per_block
    return cfg.fee_ratio * cfg.pow_share * n / target_claims_per_block


def flooring_loss_per_epoch(cfg: Config, pool: int, target_claims_per_block: int) -> int:
    """Base units the pool keeps because the reward floors to an integer.

    Small at the specified target and not small at an aggressive one: the payout is
    ``floor(distribution_rate * pool / (target * blocks_per_epoch))`` per claim, so the
    remainder is lost once per claim and there are more claims.
    """
    denom = target_claims_per_block * cfg.blocks_per_epoch
    exact = cfg.distribution_rate_num * pool / (cfg.distribution_rate_den * denom)
    floored = (pool * cfg.distribution_rate_num) // (cfg.distribution_rate_den * denom)
    return int(round((exact - floored) * denom))


# ------------------------------------------------------------------ the variant, simulated

@dataclass
class VariantOutcome:
    epoch: int
    target: int
    miners: int
    reward_per_claim: int
    claims_paid: int
    graduated_total: int
    pool_open: int
    block_space: float
    margin: float


def run(cfg: Config, scenario: Scenario, target_policy,
        rng: np.random.Generator | None = None,
        window_epochs: int = 10) -> tuple[Population, list[VariantOutcome]]:
    """Run the mechanism with a target set each epoch by ``target_policy``.

    Arrivals and participation behave as in the base model; the only change is that the
    target is re-set at each epoch boundary from the arrivals seen in the recent window.
    """
    rng = np.random.default_rng(cfg.seed) if rng is None else rng
    probs = scenario.arrival_probabilities()
    rates, costs = scenario.rates(), scenario.costs()
    n_classes = len(scenario.classes)

    capacity = int(np.ceil(scenario.joiners_per_epoch * scenario.epochs)) + 1
    pop = Population.empty(capacity)
    state = engine.genesis_state(cfg)

    arrivals: list[int] = []
    out: list[VariantOutcome] = []
    owed = 0.0
    for e in range(scenario.epochs):
        owed += scenario.joiners_per_epoch
        n_new = int(owed)
        if n_new:
            owed -= n_new
            ids = rng.choice(n_classes, size=n_new, p=probs).astype(np.int32)
            pop.arrive_classed(n_new, e, ids, rates, costs)
        arrivals.append(n_new)

        recent = float(np.mean(arrivals[-window_epochs:])) if arrivals else 0.0
        target = target_policy(cfg, e, recent)
        epoch_cfg = replace(cfg, target_claims_per_block=target)

        reward = economics.reward_per_claim(state.pool, epoch_cfg)
        live = slice(0, pop.count)
        classes_live = pop.device_class[live]
        members = np.array([int((classes_live == k).sum()) for k in range(n_classes)])
        net_usd = (max(0, reward - cfg.claim_fee) / cfg.base_units_per_lgo
                   * scenario.token_price(cfg, e))

        def hashrate_fn(t: int, _m=members, _net=net_usd) -> tuple:
            per_claim = market.candidates_per_claim(t)
            mining = (per_claim * costs) < _net if _net > 0 else np.zeros(n_classes, bool)
            group = np.where(mining, _m * rates, 0.0)
            return float(group.sum()), group

        row, state = engine.step_epoch(
            epoch_cfg, state, hashrate_fn, e, rng,
            txs_per_block=scenario.traffic(cfg, e))

        net = max(0, row.reward_per_claim - cfg.claim_fee)
        credit = row.group_credit if row.group_credit is not None else np.zeros(n_classes)
        pop.credit_groups(rng, credit, net, e, cfg.min_stake)

        out.append(VariantOutcome(
            epoch=e, target=target, miners=pop.count,
            reward_per_claim=row.reward_per_claim, claims_paid=row.claims_paid,
            graduated_total=pop.graduated, pool_open=row.pool_open,
            block_space=block_space_share(cfg, target),
            margin=self_funding_margin(cfg, target, scenario.traffic(cfg, e)),
        ))
    return pop, out


def sybil_exposure(cfg: Config, honest_joiners: float, fake_joiners: float,
                   claims_per_joiner: float) -> dict:
    """What an attacker fabricating joiners actually gets.

    The invariance cuts both ways, and this is worth stating plainly because the obvious
    objection to the variant turns out to be the wrong one. Inflating the target does NOT
    drain the pool faster -- the payout is ``distribution_rate * pool`` regardless -- and it
    does not dilute honest claimants either, since claims are won in proportion to hashrate
    and everyone's claim shrinks together. What inflating the target does buy is BLOCK
    SPACE: the claim stream crowds out ordinary transactions, and past the block limit the
    target is not implementable at all. The attack is on throughput, not on the treasury.
    """
    honest_target = max(1, round(claims_per_joiner * honest_joiners))
    attacked_target = max(1, round(claims_per_joiner * (honest_joiners + fake_joiners)))
    capped = min(attacked_target, cfg.max_block_txs)
    return dict(
        honest_target=honest_target,
        attacked_target=attacked_target,
        target_after_cap=capped,
        inflation=attacked_target / honest_target if honest_target else float("inf"),
        block_space_honest=block_space_share(cfg, honest_target),
        block_space_attacked=block_space_share(cfg, capped),
        margin_honest=self_funding_margin(cfg, honest_target),
        margin_attacked=self_funding_margin(cfg, capped),
        payout_changed=False,      # by construction: the payout carries no target
        graduation_rate_changed=False,
    )
