"""What a claim has to be worth, and whether the mechanism can be worth it.

The self-sustaining goal is that after the pool is spent, one claim still pays for something
useful: a transfer carrying a small inscription. This module prices that bundle and asks two
questions of it -- can the fee-funded steady state cover it, and can a miner afford to claim
at all.

**Fees have two prices, not one.** Execution gas is charged per Operation and rests at 7 lepta;
permanent storage gas is charged on the encoded size of the whole signed transaction
(`mantle:71`, `mantle:148`) and `storage-markets.md:126` puts it at **one LGO per stored
byte** -- a billion times more. Storage therefore dominates every fee, and a transaction costs,
to three figures, its byte count in LGO.

That price is not a constant. The same passage calls its precise value "not critical", notes
the market "converges autonomously to the market-clearing price" from any start, and leaves
that clearing price undetermined. So `P_STR` is swept here rather than assumed.

**The result that makes the sweep worth running.** Ask what inscription the steady state can
afford. The refill is a share of the fees the network pays, and those fees are storage-priced;
so is the bundle. The price appears on both sides and cancels:

| ``max_inscription_bytes = (pow_share * txs_per_block / target_claims_per_block - 1) * transfer_tx_bytes`` |
| --- |

At the settled parameters that is ``(0.1 * 600 / 10 - 1) * 207 = 1035`` bytes, **whatever
storage costs**. The steady claim is worth six transfers' fees; one pays for its own transfer
and five are left to inscribe with.

So the ceiling is set by the fee multiple alone, and a 1 kB target sits 1% inside it. What the
storage price does control is the other question -- whether a miner can afford the claim
transaction during bootstrap, when the reward comes from the pool and not from fees.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import economics
from .config import Config

SIZES = (4, 8, 16, 32, 64, 128, 256, 512, 1024)

# What storage-markets.md:126 states. The config does not use it -- see that file.
SPECIFIED_PRICE_LGO = 1.0


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


def self_funding_storage_price(cfg: Config) -> float:
    """The storage price at which the endowment IS the pool's fee-funded fixed point.

    | ``P = (rho * genesis_pool / (blocks_per_epoch * txs_per_block * pow_share)
             - transfer_tx_gas * price_resting) / transfer_tx_bytes``

    Below it the pool drains toward a smaller fixed point, above it the pool grows. At it the
    pool neither depletes nor accumulates, from genesis onwards -- so the depletion horizon
    that dominates this study at a mispriced fee is not a property of the mechanism but of the
    price it is run at.
    """
    per_epoch = (cfg.blocks_per_epoch * cfg.txs_per_block
                 * cfg.pow_share_num / cfg.pow_share_den)
    fee = cfg.distribution_rate * cfg.genesis_pool / per_epoch
    return ((fee - cfg.transfer_tx_gas * cfg.price_resting)
            / cfg.transfer_tx_bytes / cfg.base_units_per_lgo)


def elevations_per_epoch(cfg: Config) -> float:
    """How many bonds the refill alone funds each epoch, indefinitely.

    With fees priced correctly this replaces ``genesis_pool / min_stake`` as the study's
    ceiling: that quantity is what the ENDOWMENT funds, and the endowment is no longer the
    only source.
    """
    return economics.epoch_refill(cfg) / cfg.min_stake


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
            burn_per_year_lgo=c.to_lgo(tx_per_year * c.avg_tx_fee),
            rows=sweep(c, sizes),
        ))
    return out
