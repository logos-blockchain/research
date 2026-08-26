"""What a claim has to be worth, and whether the mechanism can be worth it.

The self-sustaining goal is that after the pool is spent, one claim still pays for something
useful: a transfer carrying a small inscription. This module prices that bundle and asks two
questions of it -- can the fee-funded steady state cover it, and can a miner afford to claim
at all.

**Fees have two prices, not one.** Execution gas is charged per Operation; permanent storage
gas is charged on the encoded size of the whole signed transaction, one gas per byte
(`mantle:71`, `mantle:148`). They discover their prices independently, so they are modelled
separately -- but both floor at one lepton and an idle market settles at 7, which is why
`mantle:1858` can state a claim's fee as 6,664 lepta: that is `(306 + 646) * 7`, the claim's
bytes and its gas at the same resting level.

`storage-markets.md:124-126` reads "1 LGO per permanently stored byte". That is superseded --
it predates the denomination being fixed, and *Logos Token: Units and Precision*, which
`mantle:2119` defers to by name, prices storage in lepta per gas unit with a one-lepton floor.
See `CONTRADICTIONS.md` 4.8.

**What the sweep is for.** Ask what inscription the fee-funded steady state can afford. A
steady claim is worth `pow_share * txs_per_block / target_claims_per_block` ordinary
transactions' fees -- six, at the settled parameters -- and has to pay for its own transfer out
of those six before it can inscribe anything. That is where most of the bound comes from, and
it puts the ceiling at **3,929 bytes** at the resting prices. Every size this module sweeps
clears it, 1 kB by 2.55x.

The storage price does not decide that, but it does decide affordability: a claim stops
covering its own fee once storage passes 3,782,362 lepta a byte, 540,000 times its resting
level.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import economics
from .config import Config

SIZES = (4, 8, 16, 32, 64, 128, 256, 512, 1024)



def max_inscription_bytes(cfg: Config) -> float:
    """The largest inscription the fee-funded steady state can carry.

    | ``max_bytes = (fee_multiple * avg_tx_fee - transfer_tx_bytes * storage_price
                     - (transfer_tx_gas + inscribe_gas) * price_resting) / storage_price``

    where ``fee_multiple = pow_share * txs_per_block / target_claims_per_block`` is how many
    ordinary transactions' fees one steady claim is worth -- six, at the settled parameters.

    The claim has to pay for its own transfer out of that six before it can inscribe anything,
    which is where most of the bound comes from. At the resting prices, where storage and
    execution both sit at 7 lepta, the answer is **3,929 bytes**.

    It is NOT independent of the price ratio, though an earlier revision of this module said
    so. That claim was true only in the limit where storage dominates the fee completely: there
    the execution terms vanish and the bound collapses to
    ``(fee_multiple - 1) * transfer_tx_bytes``. The two markets rest at the same level, so the
    execution terms are the same order as the storage ones and the general form is needed.
    """
    multiple = cfg.pow_share * cfg.txs_per_block / cfg.target_claims_per_block
    head = (multiple * cfg.avg_tx_fee
            - cfg.transfer_tx_bytes * cfg.storage_price
            - (cfg.transfer_tx_gas + cfg.inscribe_gas) * cfg.price_resting)
    return head / cfg.storage_price


def steady_reward(cfg: Config, txs_per_block: int | None = None) -> int:
    """The per-claim reward once the pool is a fixed point: the refill spread over the claims."""
    txs = cfg.txs_per_block if txs_per_block is None else txs_per_block
    refill = cfg.blocks_per_epoch * txs * cfg.avg_tx_fee * cfg.pow_share_num // cfg.pow_share_den
    return refill // (cfg.target_claims_per_block * cfg.blocks_per_epoch)


def affordable_storage_price(cfg: Config) -> float:
    """Storage price, in LEPTA per byte, above which a genesis claim costs more than it pays.

    During bootstrap the reward is set by the pool and does not move with the fee level, while
    the claim's own fee is almost entirely storage. Past this price the miner pays to mine.
    """
    opening = economics.reward_per_claim(cfg.genesis_pool, cfg)
    head = opening - cfg.claim_tx_gas * cfg.price_resting
    return max(0.0, head / cfg.claim_tx_bytes)


@dataclass(frozen=True)
class Row:
    inscription_bytes: int
    bundle: int                  # base units
    inscription_share: float     # of the bundle -- the transfer's own encoding is the floor
    steady_reward: int
    covered: bool
    margin: float                # steady reward over bundle


def sweep(cfg: Config, sizes=SIZES, txs_per_block: int | None = None) -> list[Row]:
    reward = steady_reward(cfg, txs_per_block)
    out = []
    for n in sizes:
        bundle = cfg.bundle_fee(n)
        out.append(Row(
            inscription_bytes=n, bundle=bundle,
            inscription_share=n * cfg.storage_price / bundle,
            steady_reward=reward, covered=reward >= bundle,
            margin=reward / bundle,
        ))
    return out


def price_sweep(cfg: Config, prices_lepta, sizes=SIZES) -> list[dict]:
    """The same sweep across storage prices, which is what the bootstrap side turns on."""
    from dataclasses import replace
    out = []
    for p in prices_lepta:
        c = replace(cfg, storage_price_lepta=int(round(p)))
        opening = economics.reward_per_claim(c.genesis_pool, c)
        tx_per_year = c.blocks_per_year * c.txs_per_block
        out.append(dict(
            price_lepta=p,
            claim_fee=c.claim_fee,
            opening_reward=opening,
            genesis_net=opening - c.claim_fee,
            mining_pays=opening > c.claim_fee,
            pooled_per_year_lgo=c.to_lgo(tx_per_year * c.avg_tx_fee),
            rows=sweep(c, sizes),
        ))
    return out
