"""The reward pool: what a claim pays, what refills the pool, and where it settles.

Exact integer arithmetic in base units throughout, because the ledger's is. The pool opens
around five times ten to the sixteenth base units, which is past the point where a float
carries every value exactly, so a float engine would round in a way the protocol does not.

Closed forms live here beside the recursions they describe, so the simulator's own
trajectory can be gated against them rather than against a second implementation of itself.
"""
from __future__ import annotations

from .config import Config


# ---------------------------------------------------------------- per-epoch quantities

def reward_per_claim(pool: int, cfg: Config) -> int:
    """What one successful claim pays out of the pool, fixed for the epoch it opens.

    | ``reward_per_claim = distribution_rate * pool / (target_claims_per_block * blocks_per_epoch)``

    Floor division, matching the protocol's integer computation: the pool never pays out a
    fraction of a base unit, and the remainder stays in the pool.
    """
    return (pool * cfg.distribution_rate_num) // (
        cfg.distribution_rate_den * cfg.target_claims_per_block * cfg.blocks_per_epoch)


def epoch_refill(cfg: Config, txs_per_block: int | None = None) -> int:
    """Fees diverted into the pool over one epoch, in base units.

    | ``epoch_refill = pow_share * blocks_per_epoch * txs_per_block * avg_tx_fee``

    The average transaction is taken as an ordinary transfer at the resting price. This
    understates the refill slightly, because some of those transactions are claims paying
    more than a transfer; the report's fee-load axis is the form that carries no such
    assumption.
    """
    n = cfg.txs_per_block if txs_per_block is None else txs_per_block
    return (cfg.pow_share_num * cfg.blocks_per_epoch * n * cfg.avg_tx_fee) // cfg.pow_share_den


def block_refill(cfg: Config, txs_per_block: int | None = None) -> int:
    """The same diversion accrued per block rather than at the epoch boundary.

    Fees are collected block by block in reality, so this is the faithful timing; the
    epoch-boundary form is what the closed forms assume. The two agree over a whole epoch up
    to floor division -- the specification floors the share per block, the epoch form floors
    once, and the gap is bounded by one base unit per block, under 21,600 lepta an epoch
    against a refill of trillions -- and differ within one only in *when* the pool grows,
    which matters once the pool is near its floor and a claim may or may not clear it.
    """
    n = cfg.txs_per_block if txs_per_block is None else txs_per_block
    return (cfg.pow_share_num * n * cfg.avg_tx_fee) // cfg.pow_share_den


def pay_claims(pool: int, reward: int, claims: int) -> tuple[int, int]:
    """Pay up to ``claims`` claims out of ``pool``, one at a time.

    Returns the pool that remains and how many were actually paid. The protocol has no
    per-epoch budget: claims draw on the whole pool one by one until what is left will not
    cover another reward. At the target rate this is indistinguishable from draining the
    epoch's share in one step, which is why the epoch-level closed form is exact there -- but
    it is not indistinguishable once arrivals run hot, and that is the case this models.
    """
    if reward <= 0:
        return pool, 0
    affordable = min(claims, pool // reward)
    return pool - affordable * reward, affordable


# ---------------------------------------------------------------- closed forms

def steady_pool(cfg: Config, txs_per_block: int | None = None) -> float:
    """Where the pool settles once refill balances payout: refill over the rate."""
    return epoch_refill(cfg, txs_per_block) / cfg.distribution_rate


def steady_reward(cfg: Config, txs_per_block: int | None = None) -> float:
    """The reward that settles with it: the refill spread over an epoch's claims."""
    return epoch_refill(cfg, txs_per_block) / (
        cfg.target_claims_per_block * cfg.blocks_per_epoch)


def reward_over_fee(cfg: Config, txs_per_block: int | None = None) -> float:
    """The margin that decides whether mining pays at all.

    | ``reward_over_fee = fee_ratio * pow_share * txs_per_block / target_claims_per_block``

    Both market prices cancel, and with them the denomination: the steady-state margin is a
    transaction count and nothing else.
    """
    n = cfg.txs_per_block if txs_per_block is None else txs_per_block
    return cfg.fee_ratio * cfg.pow_share * n / cfg.target_claims_per_block


def pool_floor(cfg: Config) -> float:
    """Pool below which a claim no longer beats its own fee.

    | ``pool_floor = claim_fee * target_claims_per_block * blocks_per_epoch / distribution_rate``
    """
    return (cfg.claim_fee * cfg.target_claims_per_block * cfg.blocks_per_epoch
            / cfg.distribution_rate)


def self_funding_txs(cfg: Config, ratio: float = 1.0) -> float:
    """Transactions a block must carry for the steady reward to reach ``ratio`` fees.

    | ``self_funding = txs_per_block > target_claims_per_block / (fee_ratio * pow_share)``
    """
    if cfg.pow_share <= 0:
        return float("inf")                    # the feature ships off: it never self-funds
    return ratio * cfg.target_claims_per_block / (cfg.fee_ratio * cfg.pow_share)


def reward_at_epoch(cfg: Config, epoch: int, txs_per_block: int | None = None) -> float:
    """The reward trajectory in closed form, for gating the simulated one.

    | ``reward_per_claim(epoch) = steady_reward + (opening_reward - steady_reward) * (1 - distribution_rate)**epoch``

    A geometric decay from the opening reward onto the steady one, at the distribution rate.
    Exact only while every claim is paid -- that is, while the pool clears the reward and
    arrivals sit at the target.
    """
    opening = cfg.genesis_pool * cfg.distribution_rate / (
        cfg.target_claims_per_block * cfg.blocks_per_epoch)
    settled = steady_reward(cfg, txs_per_block)
    return settled + (opening - settled) * (1 - cfg.distribution_rate) ** epoch
