"""Service provision rewards: flat per active provider, gated by a locked minimum stake.

**The single most consequential fact about this stream: it carries no stake term.**
`blend-protocol.md:1106-1126` splits the service income across providers holding a true
activity proof -- ``R = I / (B + P)``, doubled for those at minimal Hamming distance -- and
stake appears nowhere in it. A provider at the bare minimum earns exactly what a whale earns.
Stake is a binary admission gate and nothing else.

**What is modelled and what is not.** The reward stream is modelled because it is the largest
on the chain. Blend's network mechanics -- mixing, cover traffic, delay -- are not, by
instruction. On an honest chain every declared provider is active and submits a valid proof, so
the activity lottery collapses to "a declared provider is paid". That is an assumption, stated
here rather than buried: it removes the variance a real Hamming lottery would introduce, and
the doubling for minimal distance is not modelled either, so every provider earns the base
share. Both simplifications affect dispersion, not the mean.
"""
from __future__ import annotations

import numpy as np

from .config import Config

# `blend-protocol.md:1110`, `:150`. Below this the service does not pay at all AND halts.
MIN_PROVIDERS = 32

# `bedrock-service-declaration-protocol.md:127-130`: a declaration enters the snapshot taken
# at the last block of `current_epoch - 2`, so it takes effect two epochs after it is sent.
DECLARATION_LAG_EPOCHS = 2

# `bedrock-service-reward-distribution.md:49`: the epoch-N reward is paid in the first block
# of epoch N+2 (contradiction 4.4, resolved by precedence).
PAYOUT_LAG_EPOCHS = 2


def service_active(n_providers: int) -> bool:
    """Whether the service pays at all this epoch.

    A hard floor, not a taper: below thirty-two unique providers the specification says
    rewards *"are not calculated"* and nodes must bypass the Blend network entirely. A study
    whose groups are smaller than this measures a chain on which the stream does not exist.
    """
    return n_providers >= MIN_PROVIDERS


def reward_per_provider(blend_pool_lgo: float, n_providers: int) -> float:
    """What one active provider earns from an epoch's service income.

    | ``reward_per_provider = blend_pool / providers``

    Flat. The whole point: it does not scale with stake, so the marginal value of holding more
    than the threshold is zero for this stream, and the marginal value of *reaching* the
    threshold is the entire per-provider share.
    """
    if not service_active(n_providers) or n_providers <= 0:
        return 0.0
    return blend_pool_lgo / n_providers


def eligible(balance: np.ndarray, min_stake: int, declared_epoch: np.ndarray,
             epoch: int) -> np.ndarray:
    """Providers whose declaration is live this epoch and whose bond still clears the minimum.

    Two conditions, both required: the stake is locked at or above the threshold, and the
    declaration has aged into the snapshot the epoch reads.
    """
    bonded = balance >= min_stake
    live = (declared_epoch >= 0) & (declared_epoch + DECLARATION_LAG_EPOCHS <= epoch)
    return bonded & live


def locked_stake(balance: np.ndarray, providing: np.ndarray, min_stake: int) -> np.ndarray:
    """The portion of a provider's balance bonded to its declaration.

    A declaration proves a **locked** note. Whether a locked note still carries leadership
    weight is not stated anywhere, and it decides whether providing a service costs a staker
    lottery income or is free on top of it. The simulator carries it as a switch --
    ``cfg.service_bond_counts_for_lottery`` -- defaulting to counting it, and the alternative
    is a sweep rather than an assumption.
    """
    return np.where(providing, np.minimum(balance, min_stake), 0)


def blend_pool_from_blocks(block_rewards_lgo: np.ndarray, cfg: Config) -> float:
    """Blend's 60% of an epoch's block rewards, floored per block."""
    from . import emission                                    # noqa: PLC0415
    return float(sum(emission.split(r, cfg)[0] for r in block_rewards_lgo))
