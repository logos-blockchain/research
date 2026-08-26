"""The block loop: the reference implementation, in plain Python.

This is the oracle. It is written for legibility rather than speed, and the compiled loop
that replaces it in sweeps is gated to agree with it step for step -- the same two-engines
discipline the tokenomics package already applies to float against integer.

One epoch is 21,600 blocks and a full trajectory at the specified distribution rate is about
2,085 epochs, so a complete horizon is roughly 45 million sequential steps. Sequential is not
an implementation choice: each target depends on the previous block's count, so the loop
cannot be vectorised, only compiled.

The epoch is the unit the loop is exposed at, because the reward is constant across one and
so anything that depends on the reward -- crediting miners, deciding who can afford to mine --
can advance one epoch at a time without losing anything. See :mod:`empowering_sim.nodes` for
why per-epoch attribution is exact rather than a convenience.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace

import numpy as np

from . import economics, work
from .config import FIELD_MODULUS, Config


@dataclass(frozen=True)
class State:
    """Everything the loop carries across an epoch boundary."""

    pool: int
    difficulty_target: int


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
    hashrate: float
    paying: bool
    # Present only when participation was evaluated per block: how many of the epoch's
    # claims each device group earned, and how many blocks each spent able to mine.
    group_credit: np.ndarray | None = None
    active_blocks: np.ndarray | None = None

    @property
    def unpaid(self) -> int:
        """Claims found that the pool could not cover. Nonzero means the pool ran dry."""
        return self.claims_found - self.claims_paid - self.claims_dropped


def genesis_state(cfg: Config) -> State:
    return State(pool=cfg.genesis_pool, difficulty_target=cfg.genesis_difficulty_target)


def step_epoch(cfg: Config, state: State, hashrate: float | Callable, epoch: int,
               rng: np.random.Generator, deterministic: bool = False,
               txs_per_block: int | None = None) -> tuple[EpochRow, State]:
    """Run one epoch, block by block, and report it.

    The reward is computed once from the pool as the epoch opens and held fixed for the whole
    epoch, which is what the protocol does and what makes per-epoch crediting exact.

    ``hashrate`` is either a constant or a callable taking the current difficulty target and
    returning ``(total, per_group)``. The callable form exists because **participation has to
    be re-decided at the controller's own granularity**. The retarget acts every block; if
    miners are allowed to react only once an epoch, they respond to a target 21,600 blocks
    stale, and the model produces a two-epoch limit cycle between nobody mining and everybody
    mining. That oscillation is entirely an artefact of the mismatch, and this is the fix for
    it. It stays cheap because the participation rule depends only on the target and the
    token price -- both scalars -- so it is evaluated per device class, not per node.
    """
    reward = economics.reward_per_claim(state.pool, cfg)
    pool, target = state.pool, state.difficulty_target
    pool_open, target_open = pool, target
    found = paid = dropped = refilled = 0

    callable_rate = callable(hashrate)
    group_credit: np.ndarray | None = None
    active_block_count: np.ndarray | None = None
    last_total = 0.0

    per_block_refill = economics.block_refill(cfg, txs_per_block)
    per_epoch_refill = economics.epoch_refill(cfg, txs_per_block)

    for _ in range(cfg.blocks_per_epoch):
        if callable_rate:
            rate_now, per_group = hashrate(target)
            if group_credit is None:
                group_credit = np.zeros(per_group.size, dtype=np.float64)
                active_block_count = np.zeros(per_group.size, dtype=np.int64)
            active_block_count += (per_group > 0)
            last_total = rate_now
        else:
            rate_now, per_group = hashrate, None
        expected = work.expected_claims(rate_now, target, cfg)
        n = int(round(expected)) if deterministic else int(rng.poisson(expected))
        found += n

        # Claims are transactions and compete for block space like any other.
        included = min(n, cfg.max_block_txs)
        dropped += n - included

        pool, settled = economics.pay_claims(pool, reward, included)
        paid += settled

        # Credit each group in proportion to the power it was contributing at the moment the
        # claims were found, not to what it contributes at the epoch boundary.
        if settled and per_group is not None and rate_now > 0:
            group_credit += settled * (per_group / rate_now)

        # The controller sees what the block carried, not what was found: a claim that never
        # lands is invisible to it. This matters only once the block cap binds.
        target = work.next_difficulty_target(target, included, cfg)

        if cfg.refill_timing == "block":
            pool += per_block_refill
            refilled += per_block_refill

    if cfg.refill_timing == "epoch":
        pool += per_epoch_refill
        refilled = per_epoch_refill

    row = EpochRow(
        epoch=epoch, years=epoch / cfg.epochs_per_year,
        pool_open=pool_open, reward_per_claim=reward,
        claims_found=found, claims_paid=paid, claims_dropped=dropped,
        refill=refilled,
        difficulty_target_open=target_open, difficulty_target_close=target,
        hashrate=last_total if callable_rate else hashrate,
        paying=reward > 0 and pool_open >= reward,
        group_credit=group_credit,
        active_blocks=active_block_count,
    )
    return row, replace(state, pool=pool, difficulty_target=target)


def run(cfg: Config, hashrate: float, epochs: int | None = None,
        rng: np.random.Generator | None = None,
        deterministic: bool = False) -> list[EpochRow]:
    """Simulate the pool and the retarget at a fixed hashrate, reporting once per epoch.

    ``deterministic`` replaces each block's Poisson draw by its mean, which is what the
    closed forms assume; it exists so the stochastic engine and the analytic one can be
    compared without sampling noise standing between them.
    """
    horizon = cfg.horizon_epochs if epochs is None else epochs
    rng = np.random.default_rng(cfg.seed) if rng is None else rng
    state = genesis_state(cfg)
    rows = []
    for epoch in range(horizon):
        row, state = step_epoch(cfg, state, hashrate, epoch, rng, deterministic)
        rows.append(row)
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
