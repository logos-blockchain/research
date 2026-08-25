"""Consensus: who leads a block, and what leading is worth.

Modelled at the same fidelity as the work process and for the same reason -- the question
here is what a staker *earns*, not whether the chain is safe, so the lottery is replaced by
its distribution rather than executed.

**What this deliberately does not model.** Empty slots, forks, and the difference between a
slot and a block: the epoch is taken to contain exactly ``blocks_per_epoch`` blocks, which is
what the parameter means and what the tokenomics model assumes throughout. Nothing here is a
statement about consensus security; it exists so a node that has graduated has something to
graduate *into*, and so the crossover between mining and staking can be priced.

**What is not specified.** The share of a block's reward reaching its leader is not fixed
anywhere in the specification tree -- the report records the leader fee share as unset and
carries 0.4 as a modelling choice. Every figure downstream of :func:`leader_income_per_epoch`
is conditional on that choice, and says so.
"""
from __future__ import annotations

import numpy as np

from .config import Config


def max_block_reward(cfg: Config) -> float:
    """The emission cap, in LGO per block.

    | ``max_minted_per_block = max_emission_per_year * launch_supply / blocks_per_year``

    A ceiling rather than a payment. The specification's block reward is

        A_t * I_max * S_tge * dt / f  +  (1 - A_t) * R_block

    (`block-rewards.md`), so this function is the first term at ``A_t = 1`` -- the emission
    rate factor at its maximum. The second term recycles burnt fees and grows as ``A_t``
    falls.
    """
    return cfg.max_emission_per_year * cfg.launch_supply / cfg.blocks_per_year


def block_reward(cfg: Config, emission_factor: float, burnt_fees_per_block: float) -> float:
    """The specification's block reward, both terms, in LGO per block.

    | ``block_reward = emission_factor * max_minted_per_block + (1 - emission_factor) * burnt_fees``

    ``emission_factor`` is the specification's ``A_t``, bounded in [0, 1] and driven by two
    key performance indicators -- how far inferred total stake sits from its target, and the
    moving average of the burn rate. The specification's own account of the regimes:

    - **far from target**, ``A_t -> 1``: emission is maximised and burnt fees are not minted
      back. This is the bootstrap phase, and it is the regime the on-ramp operates in, which
      is why the analysis here runs at ``A_t = 1``.
    - **close to target**, ``A_t -> 0``: emission from inflation is minimised and most of the
      burnt fees are minted back instead.
    """
    factor = min(1.0, max(0.0, emission_factor))
    return factor * max_block_reward(cfg) + (1 - factor) * burnt_fees_per_block


def validation_apy(cfg: Config, staked_fraction: float | None = None,
                   emission_factor: float = 1.0) -> float:
    """Annual yield on staked tokens, at the maximum emission regime.

    | ``validation_apy = emission_factor * max_emission_per_year * leader_reward_share / staked_fraction``

    **The leader share is applied**, so this returns 1.333% at the defaults, not the 3.33%
    the specification's calibration narrative quotes. `block-rewards.md` calibrates
    ``I_max = 1%`` so the yield lands near 3.33% at the 30% stake target -- a figure that
    holds only if validators take the WHOLE emission, while `overview-cryptoeconomics.md`
    states as code that they take 0.4 of it. The config carries 0.4, this function follows
    the config, and the gate reproduces 3.33% only by explicitly setting the share to one.
    The direction matters: the lower yield makes the on-ramp's obstacle worse, not better.
    """
    frac = cfg.stake_target if staked_fraction is None else staked_fraction
    if frac <= 0:
        return float("inf")
    return emission_factor * cfg.max_emission_per_year * cfg.leader_reward_share / frac


def max_block_reward_base_units(cfg: Config) -> int:
    return round(max_block_reward(cfg) * cfg.base_units_per_lgo)


def blocks_led(rng: np.random.Generator, stake: np.ndarray,
               blocks: int) -> np.ndarray:
    """Deal an epoch's blocks out to stakers in proportion to stake.

    The same exactness argument as claim attribution in :mod:`empowering_sim.nodes`: each
    slot is won independently with probability proportional to stake, so over an epoch the
    counts are multinomial in the stake shares. One draw per epoch rather than one per slot.

    Stake below the minimum does not enter -- a balance that cannot be staked wins nothing,
    which is the whole point of the threshold, so callers must zero those entries first.
    """
    if blocks <= 0 or stake.size == 0:
        return np.zeros(stake.size, dtype=np.int64)
    total = stake.sum()
    if total <= 0:
        return np.zeros(stake.size, dtype=np.int64)
    return rng.multinomial(blocks, stake / total).astype(np.int64)


def lottery_weight(balance: np.ndarray, aged: np.ndarray) -> np.ndarray:
    """Weight a holder brings to the leadership lottery: its aged balance, whatever the size.

    **There is no minimum.** The specification is explicit: a node must have held stake as a
    note for a minimum *time* period, and "the weight of the coin is proportional to the value
    of your note" (`cryptarchia-v1-protocol.md`). Aging is the gate, not size. So a miner is a
    consensus participant from its very first aged note, with no threshold to cross and no
    accumulation required.

    This corrects an earlier model in this simulator which gated all staking income at the
    minimum stake. That gate is real but it belongs to service provision, below.
    """
    return np.where(aged, balance, 0)


def service_eligible(balance: np.ndarray, min_stake: int) -> np.ndarray:
    """Balances that can be locked to declare a service. **This** is what the minimum gates.

    `bedrock-service-declaration-protocol.md`: "The minimum stake is a global value that
    defines the minimum stake a node must have to perform any service", proven by locking a
    note. So the threshold, and the ceiling it implies on how many positions an endowment can
    bootstrap, apply to the service layer alone -- not to consensus, which is unbounded.
    """
    return np.where(balance >= min_stake, balance, 0)


def leader_income_from_balance(cfg: Config, balance: float, staked_fraction: float | None = None,
                               emission_factor: float = 1.0) -> float:
    """Leader income for an aged balance of any size, per epoch, in the same units.

    | ``leader_income = balance * validation_apy / epochs_per_year``

    Proportional to what is held, with no threshold, which is what makes the on-ramp into
    consensus immediate rather than something to be earned.
    """
    apy = validation_apy(cfg, staked_fraction, emission_factor)
    return balance * apy / cfg.epochs_per_year


def leader_income_per_epoch(cfg: Config, stake_share: float,
                            txs_per_block: int | None = None) -> float:
    """What a staker holding ``stake_share`` of stake earns in one epoch, in base units.

    Two streams, and the report treats them separately because only one is specified:

    - **minted**, bounded by the emission cap, of which the leader takes
      ``leader_reward_share``;
    - **fees**, of which leaders take ``leader_fee_share`` of what is not diverted into the
      proof-of-work pool.

    Both shares are modelling choices rather than specified constants, so this figure is
    conditional. It is reported per epoch to sit beside mining income on the same clock.
    """
    n = cfg.txs_per_block if txs_per_block is None else txs_per_block
    blocks = cfg.blocks_per_epoch

    minted = max_block_reward_base_units(cfg) * blocks * cfg.leader_reward_share
    undiverted = (1 - cfg.pow_share) * blocks * n * cfg.avg_tx_fee
    fees = undiverted * cfg.leader_fee_share
    return stake_share * (minted + fees)


def mining_income_per_epoch(cfg: Config, hashrate_share: float,
                            reward_per_claim: int) -> float:
    """What a miner holding ``hashrate_share`` of the hashrate earns in one epoch.

    Net of the fee each claim pays to submit, and before electricity -- which is the cost
    estimator's part, and the reason this figure alone cannot settle the crossover.
    """
    claims = cfg.target_claims_per_block * cfg.blocks_per_epoch * hashrate_share
    return claims * max(0, reward_per_claim - cfg.claim_fee)


def crossover_stake_share(cfg: Config, hashrate_share: float, reward_per_claim: int,
                          txs_per_block: int | None = None) -> float:
    """Stake share at which leading pays as much as mining does, before electricity.

    Solves ``leader_income_per_epoch(share) == mining_income_per_epoch(hashrate_share)``.

    **Read this as a lower bound on the crossover, not the crossover.** Mining carries an
    electricity cost that staking does not, so the true crossover sits below this: the
    marginal miner is indifferent sooner than the gross figures suggest. Closing that gap is
    what the cost estimator is for. It is also a comparison of a return on operating expense
    against a return on capital, which cannot be collapsed into one number without a
    discount rate -- so treat it as a scale, not a verdict.
    """
    mining = mining_income_per_epoch(cfg, hashrate_share, reward_per_claim)
    unit = leader_income_per_epoch(cfg, 1.0, txs_per_block)
    return mining / unit if unit > 0 else float("inf")
