"""The two fee markets, and the question they decide.

The emission control function stops releasing from the reserve once staked value reaches
its target, after which the block reward is exactly the fees the block pools. So whether the mechanism pays anyone
anything in its equilibrium era turns entirely on where the fee markets settle -- and that is
not something the block reward can answer about itself.

Both update rules are transcribed from their specifications in exact integer arithmetic,
including the rounding directions, which are load-bearing in both: each rounds the price
UPWARDS and the usage average DOWNWARDS, and `storage-markets.md` explains that reversing the
first would make zero an absorbing state.

**The execution market is EIP-1559 with an exponential moving average**, adopted over classic
EIP-1559 to blunt base-fee manipulation by non-myopic builders. Its consequence here is the
one that matters: under sustained saturation the base fee does not approach a ceiling, it
**compounds** -- up to 12.5% per block, without bound.
"""
from __future__ import annotations

from dataclasses import dataclass

# --- execution market, `execution-market.md:186-200` -------------------------------------
G_TARGET = 1_596_730                    # half of G_max; the usage the market steers toward
G_MAX = 3_193_460
EMA_DENOMINATOR = 10                    # q = 9/10
EMA_PREV_WEIGHT = 9
BASE_FEE_NUMERATOR = 11_177_110         # 7 * G_target
BASE_FEE_DENOMINATOR = 12_773_840       # 8 * G_target

# --- storage market, `storage-markets.md:192-201` ----------------------------------------
STR_EMA_DENOMINATOR = 2                 # 1/beta
STR_CLAMP_DENOMINATOR = 8
STR_CLAMP_DOWN = 7                      # 1 - alpha
STR_CLAMP_UP = 9                        # 1 + alpha


def ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def update_g_avg(prev_g_avg: int, block_gas_used: int) -> int:
    """The usage EMA, rounded DOWN -- it is a measurement, not a price."""
    return (block_gas_used + EMA_PREV_WEIGHT * prev_g_avg) // EMA_DENOMINATOR


def next_base_fee(base_fee: int, g_avg: int) -> int:
    """| ``b[s+1] = ceil( b[s] * (7*G_target + g_avg) / (8*G_target) )``

    Stationary exactly at ``g_avg == G_target``; multiplies by 9/8 at a full block and by 7/8
    at an empty one. **Nothing bounds it above.** A market held at saturation compounds at
    12.5% a block, so the reachable price is a question about demand rather than about the
    mechanism.
    """
    return ceil_div(base_fee * (BASE_FEE_NUMERATOR + g_avg), BASE_FEE_DENOMINATOR)


def next_storage_price(price: int, gas_used: int, usage: int) -> int:
    """The storage market's clamped proportional update, rounded up."""
    if usage == 0:
        return price
    if STR_CLAMP_DENOMINATOR * gas_used <= STR_CLAMP_DOWN * usage:
        return ceil_div(price * STR_CLAMP_DOWN, STR_CLAMP_DENOMINATOR)
    if STR_CLAMP_DENOMINATOR * gas_used >= STR_CLAMP_UP * usage:
        return ceil_div(price * STR_CLAMP_UP, STR_CLAMP_DENOMINATOR)
    return ceil_div(price * gas_used, usage)


def update_storage_usage(gas_used: int, prev_usage: int) -> int:
    return (gas_used + prev_usage) // STR_EMA_DENOMINATOR


@dataclass
class ExecutionMarket:
    base_fee: int = 7                   # the resting level both markets settle to
    g_avg: int = G_TARGET

    def step(self, gas_used: int) -> "ExecutionMarket":
        g = update_g_avg(self.g_avg, gas_used)
        return ExecutionMarket(next_base_fee(self.base_fee, g), g)


def blocks_to_reach(target_price: int, fill: float = 1.0, start: int = 7,
                    limit: int = 100_000) -> int | None:
    """Blocks of demand at ``fill`` of capacity needed to drive the base fee to a level.

    ``fill = 1.0`` is a persistently full block, which is the fastest the market can move.
    Returns None if the fill is at or below target, where the price is stationary or falling.
    """
    m = ExecutionMarket(base_fee=start)
    gas = int(fill * G_MAX)
    for n in range(limit):
        if m.base_fee >= target_price:
            return n
        nxt = m.step(gas)
        if nxt.base_fee <= m.base_fee and n > 50:
            return None                 # stationary or falling: it will never get there
        m = nxt
    return None


def price_for_block_pool(target_pool_lepta: int, txs_per_block: int,
                         units_per_tx: int, pow_share: float) -> float:
    """The price at which a block's pooled fees reach a stated size.

    | ``price = target_pool / (txs * units_per_tx * (1 - pow_share))``

    The proof-of-work share is carved out of the pooled flow (decided 2026-08-24: fees enter
    the pending rewards pool in full and the EmPoWering share is its first outflow), so only
    the remainder is what the emission model measures and distributes against.
    """
    pooled_units = txs_per_block * units_per_tx * (1 - pow_share)
    return target_pool_lepta / pooled_units if pooled_units else float("inf")
