"""The block loop: the reference implementation, in plain Python.

This is the oracle. It is written for legibility rather than speed, and the compiled loop
that replaces it in sweeps is gated to agree with it step for step -- the same two-engines
discipline the tokenomics package already applies to float against integer.

One epoch is 21,600 blocks and a full trajectory at the specified distribution rate is about
2,085 epochs, so a complete horizon is roughly 45 million sequential steps. Sequential is not
an implementation choice: each target depends on the previous block's count, so the loop
cannot be vectorised, only compiled.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import economics, work
from .config import FIELD_MODULUS, Config


@dataclass
class EpochRow:
    """What one epoch looked like. The unit results are reported in."""

    epoch: int
    years: float
    pool_open: int
    reward_per_claim: int
    claims_found: int
    claims_paid: int
    claims_dropped: int
    refill: int
    difficulty_target_open: int
    difficulty_target_close: int
    paying: bool

    @property
    def unpaid(self) -> int:
        """Claims found that the pool could not cover. Nonzero means the pool ran dry."""
        return self.claims_found - self.claims_paid - self.claims_dropped


def run(cfg: Config, hashrate: float, epochs: int | None = None,
        rng: np.random.Generator | None = None,
        deterministic: bool = False) -> list[EpochRow]:
    """Simulate the pool and the retarget block by block, reporting once per epoch.

    ``deterministic`` replaces each block's Poisson draw by its mean, which is what the
    closed forms assume; it exists so the stochastic engine and the analytic one can be
    compared without sampling noise standing between them.
    """
    horizon = cfg.horizon_epochs if epochs is None else epochs
    rng = np.random.default_rng(cfg.seed) if rng is None else rng

    pool = cfg.genesis_pool
    target = cfg.genesis_difficulty_target
    per_block_refill = economics.block_refill(cfg)
    per_epoch_refill = economics.epoch_refill(cfg)

    rows: list[EpochRow] = []
    for epoch in range(horizon):
        # The reward is fixed for the epoch, computed from the pool as the epoch opens.
        reward = economics.reward_per_claim(pool, cfg)
        pool_open, target_open = pool, target
        found = paid = dropped = refilled = 0

        for _ in range(cfg.blocks_per_epoch):
            expected = work.expected_claims(hashrate, target, cfg)
            n = int(round(expected)) if deterministic else int(rng.poisson(expected))
            found += n

            # Claims are transactions and compete for block space like any other.
            included = min(n, cfg.max_block_txs)
            dropped += n - included

            pool, settled = economics.pay_claims(pool, reward, included)
            paid += settled

            # The controller sees what the block carried, not what was found: a claim that
            # never lands is invisible to it. This matters only once the block cap binds.
            target = work.next_difficulty_target(target, included, cfg)

            if cfg.refill_timing == "block":
                pool += per_block_refill
                refilled += per_block_refill

        if cfg.refill_timing == "epoch":
            pool += per_epoch_refill
            refilled = per_epoch_refill

        rows.append(EpochRow(
            epoch=epoch, years=epoch / cfg.epochs_per_year,
            pool_open=pool_open, reward_per_claim=reward,
            claims_found=found, claims_paid=paid, claims_dropped=dropped,
            refill=refilled,
            difficulty_target_open=target_open, difficulty_target_close=target,
            paying=reward > 0 and pool_open >= reward,
        ))
    return rows


def reconvergence_blocks(cfg: Config, step: float = 10.0, tol: float = 0.1,
                         limit: int = 400) -> int | None:
    """Blocks for the target to recover after the hashrate jumps by ``step``.

    Mean-field, matching the report's derivation: arrivals are taken at their expectation, so
    this measures the controller's own response rather than arrival noise. The report derives
    a pole equal to the smoothing weight and predicts about 22 blocks for a tenfold step.
    """
    equilibrium = cfg.genesis_difficulty_target
    target = equilibrium
    for n in range(limit):
        # Hashrate sits at ``step`` times the level the genesis target was set for.
        expected = step * cfg.target_claims_per_block * target / equilibrium
        if abs(expected - cfg.target_claims_per_block) <= tol * cfg.target_claims_per_block:
            return n
        target = work.next_difficulty_target(target, expected, cfg)
    return None


def hashrate_for_target_rate(cfg: Config, difficulty_target: int | None = None) -> float:
    """The hashrate at which a given target yields exactly the target claim rate.

    The natural starting point for a run that should open in equilibrium rather than walk
    into one.
    """
    d = cfg.genesis_difficulty_target if difficulty_target is None else difficulty_target
    return cfg.target_claims_per_block * FIELD_MODULUS / (cfg.block_seconds * d)
