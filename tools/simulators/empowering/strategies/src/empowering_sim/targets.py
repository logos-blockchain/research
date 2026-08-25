"""Stating the outcome and deriving the parameters, instead of the other way round.

The mechanism is specified as rates and shares -- `distribution_rate`, `pow_share`,
`genesis_pool_fraction` -- whose consequences appear only after a simulation. Nobody can defend
`distribution_rate = 1/200` directly. This module inverts three of them onto quantities a
designer can hold an opinion about:

| you state | it determines |
| --- | --- |
| `nodes_to_onboard` | how long onboarding takes |
| `bootstrap_years` | `distribution_rate` |
| `inscription_bytes` | `pow_share` |

Each inversion is closed form. See `docs/TARGET-PARAMETERISATION.md` for the argument; this is
the arithmetic, with the constraints attached so a target that cannot be met says so rather
than returning a number that quietly does not work.

The first inversion rests on the endowment being what funds onboarding, and it is: at the
resting fee level `epoch_refill` is 7.23 LGO an epoch, which is 0.007 of a single bond, against
the 250 bonds an epoch the endowment itself funds at genesis. Fees are a rounding error on this
question during bootstrap.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import economics, inscription
from .config import Config

# `mantle:1858` states the bound as a fraction of launch supply so that it is unit-independent:
# below it, "an opening reward that exceeds twice the claim's fee". Past it, claiming stops
# paying for itself and the mechanism does not onboard anyone.
SPEC_FEE_CEILING_FRACTION = 1.157e-10

# Measured by the elevation study at 400 epochs and 100 arrivals an epoch, as fractions of the
# `genesis_pool / min_stake` ceiling. Most of what the pool pays lands in balances that never
# reach the bond, and the gap between these two is a behaviour the specification does not
# address: whether a miner that has crossed the bond keeps mining. It is worth 4.5x.
CONVERSION_RETIRING = 0.519
CONVERSION_PERSISTENT = 0.114


@dataclass(frozen=True)
class Onboarding:
    nodes: int
    pool_retiring_lgo: float
    pool_persistent_lgo: float
    ceiling_at_current_pool: float


def endowment_for(cfg: Config, nodes_to_onboard: int) -> Onboarding:
    """| ``genesis_pool = nodes_to_onboard * min_stake / conversion_efficiency``

    What a node target costs, in tokens. Both conversion efficiencies are returned because the
    switch between them is unspecified and worth a factor of four and a half -- which is the
    single strongest argument for parameterising this way, since the current form hides that
    behaviour inside a pool size chosen as a round fraction of supply.
    """
    need = nodes_to_onboard * cfg.min_stake
    return Onboarding(
        nodes=nodes_to_onboard,
        pool_retiring_lgo=cfg.to_lgo(need / CONVERSION_RETIRING),
        pool_persistent_lgo=cfg.to_lgo(need / CONVERSION_PERSISTENT),
        ceiling_at_current_pool=cfg.genesis_pool / cfg.min_stake,
    )


def distribution_rate_for(cfg: Config, bootstrap_years: float,
                          remaining_fraction: float = 0.10) -> dict:
    """| ``distribution_rate = 1 - remaining_fraction ** (1 / bootstrap_epochs)``

    The rate at which the endowment would be spent down to `remaining_fraction` over the stated
    period, were it not refilled. It still sets the *pace* at which the pool converts into
    bonds even though the pool no longer depletes, because the payout is `distribution_rate`
    times the pool however the pool is funded.

    Carries its own constraint. The within-epoch drain is closed by construction only while
    `target_claims_per_block / distribution_rate > max_block_txs`, which floors the bootstrap
    period independently of anything economic.
    """
    epochs = bootstrap_years * cfg.epochs_per_year
    rate = 1.0 - remaining_fraction ** (1.0 / epochs)
    headroom = cfg.target_claims_per_block / rate
    return dict(
        bootstrap_years=bootstrap_years,
        distribution_rate=rate,
        denominator=round(1.0 / rate),
        drain_headroom=headroom,
        drain_safe=headroom > cfg.max_block_txs,
    )


def min_bootstrap_years(cfg: Config, remaining_fraction: float = 0.10) -> float:
    """The floor the drain-safety condition puts under any bootstrap period.

    Below it the epoch's payout no longer fits in the blocks available to carry it, and the
    only way further down is to raise `target_claims_per_block` in step -- which thins the
    self-funding margin one for one.
    """
    rate = cfg.target_claims_per_block / cfg.max_block_txs
    import math
    return math.log(remaining_fraction) / math.log(1.0 - rate) / cfg.epochs_per_year


def pow_share_for(cfg: Config, inscription_bytes: int) -> dict:
    """| ``pow_share = bundle_fee * target_claims_per_block / (txs_per_block * avg_tx_fee)``

    The share of fees the pool must divert for a steady claim to cover a transfer carrying an
    inscription of the stated size.

    This inversion is tightly constrained, which is easy to miss. The reachable inscription is
    capped at `inscription.max_inscription_bytes` -- 3,929 bytes at the resting prices -- so
    choosing a target above that is not a choice about `pow_share` at all, and the function
    reports it as unreachable rather than returning a share that cannot deliver it.
    """
    claims = cfg.target_claims_per_block * cfg.blocks_per_epoch
    fee_revenue = cfg.blocks_per_epoch * cfg.txs_per_block * cfg.avg_tx_fee
    share = cfg.bundle_fee(inscription_bytes) * claims / fee_revenue
    ceiling = inscription.max_inscription_bytes(cfg)
    return dict(
        inscription_bytes=inscription_bytes,
        pow_share=share,
        against_current=share / cfg.pow_share,
        ceiling_bytes=ceiling,
        reachable=inscription_bytes < ceiling,
        headroom=ceiling / inscription_bytes if inscription_bytes else float("inf"),
    )


def affordable(cfg: Config) -> dict:
    """Whether a claim pays for itself, against the bound the specification states itself.

    `mantle:1858` puts the ceiling at `1.157e-10` of launch supply. It is worth checking
    separately from everything above because it is the one constraint that can be violated
    without any of the inversions noticing: they all balance fees against fees, and this one
    balances a fee against the pool.
    """
    ceiling = SPEC_FEE_CEILING_FRACTION * cfg.launch_supply
    fee = cfg.to_lgo(cfg.claim_fee)
    return dict(
        claim_fee_lgo=fee,
        spec_ceiling_lgo=ceiling,
        ratio=fee / ceiling,
        affordable=fee <= ceiling,
        max_storage_price_lepta=inscription.affordable_storage_price(cfg),
    )
