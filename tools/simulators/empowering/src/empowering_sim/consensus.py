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

    A ceiling rather than a payment: the protocol mints at most this much per block.
    """
    return cfg.max_emission_per_year * cfg.launch_supply / cfg.blocks_per_year


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


def eligible_stake(balance: np.ndarray, min_stake: int) -> np.ndarray:
    """Balances that clear the minimum, zeroed elsewhere.

    Below the threshold a balance earns nothing from consensus however large the holder's
    ambitions, and this is the line the on-ramp exists to get people across.
    """
    return np.where(balance >= min_stake, balance, 0)


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
