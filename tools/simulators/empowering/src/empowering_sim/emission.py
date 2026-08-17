"""The KPI-driven block reward, and the stake estimate that drives it.

Transcribed from `block-rewards.md`'s normative integer form and
`cryptarchia-total-stake-inference.md`'s estimator, with the decisions in
`docs/CONTRADICTIONS.md` applied: the deviation coefficient is 1/4 (4.2), the split is floored
per block (4.6), and the genesis stake estimate is the total distributed at genesis (4.3).

**Units.** The block-reward function is denominated in LGO -- its literal `3e9` is three
billion LGO -- while ledger quantities are lepta. No conversion rule is stated anywhere
(contradiction 4.7), so the conversion happens here, at the function boundary, and is gated.
Feeding lepta in unchanged is wrong by a factor of a billion.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Config

# `block-rewards.md:477-501`, the reference implementation's constants. All in LGO.
A_SCALE = 120_000_000
INFLATION_NUMERATOR = 62_500
INFLATION_DENOMINATOR = 657
FEE_AVG_NUMERATOR = 10_512
STAKE_TARGET_LGO = 3_000_000_000          # D_0,target = 30% of a 10^10 supply
BURN_WINDOW = 120                          # T, the look-back in blocks


def emission_factor_scaled(total_stake_lgo: float, burnt_window_lgo: list[float]) -> int:
    """``A_t'``, the emission rate factor before scaling. Integer, as the consensus rule is.

    | ``A_t' = min(A_SCALE, max(0, STAKE_TARGET - total_stake + FEE_AVG_NUMERATOR * sum(burnt_window)))``

    The first term is the stake deviation and the second the burn average. Both are read in
    LGO. Clamped to ``[0, A_SCALE]`` on both sides, so it saturates rather than inverting.
    """
    raw = (STAKE_TARGET_LGO - total_stake_lgo
           + FEE_AVG_NUMERATOR * sum(burnt_window_lgo[-BURN_WINDOW:]))
    return int(min(A_SCALE, max(0, raw)))


def emission_factor(total_stake_lgo: float, burnt_window_lgo: list[float]) -> float:
    """``A_t`` in [0, 1]: one is pure minting, zero is pure recycling of the block's burn."""
    return emission_factor_scaled(total_stake_lgo, burnt_window_lgo) / A_SCALE


def block_reward_lgo(total_stake_lgo: float, burnt_window_lgo: list[float]) -> float:
    """Total reward minted for one block, in LGO.

    | ``reward = (62500 * A_t' + 657 * (A_SCALE - A_t') * burnt_this_block) / (657 * A_SCALE)``

    At ``A_t = 1`` this is 62500/657 = 95.1294 LGO and the burn does not enter. At ``A_t = 0``
    it is exactly the block's own burnt fees, minted back.
    """
    a = emission_factor_scaled(total_stake_lgo, burnt_window_lgo)
    burnt_now = burnt_window_lgo[-1] if burnt_window_lgo else 0.0
    return ((INFLATION_NUMERATOR * a + INFLATION_DENOMINATOR * (A_SCALE - a) * burnt_now)
            / (INFLATION_DENOMINATOR * A_SCALE))


def split(reward_lgo: float, cfg: Config) -> tuple[float, float]:
    """Blend's and the leader's shares of one block's reward, floored per block.

    | ``leader = reward * leader_tenths // 10``  and  ``blend = reward * (10 - leader_tenths) // 10``

    At the specified share this is exactly `block-rewards.md`'s `* 4 // 10` and `* 6 // 10`.
    It is written against ``cfg.leader_reward_share`` rather than against the literals because
    the split is CONTESTED -- `block-rewards.md` calibrates I_max for a validator yield that
    only holds if leaders take the whole emission, while `overview-cryptoeconomics.md` gives
    them four tenths. A first version hardcoded the literals here while the crossover module
    read the config, so the two readings produced identical output and the contradiction was
    untestable. It is one number in one place now.

    Per block rather than per epoch (contradiction 4.6). The two floors do not sum to the
    reward; where the residue goes is unspecified anywhere, so it is retained -- matching the
    leader pool's stated treatment of its own remainder -- and the caller is told how much.
    """
    units = round(reward_lgo * cfg.base_units_per_lgo)
    leader_tenths = int(round(cfg.leader_reward_share * 10))
    leader = units * leader_tenths // 10
    blend = units * (10 - leader_tenths) // 10
    return blend / cfg.base_units_per_lgo, leader / cfg.base_units_per_lgo


def split_residue(reward_lgo: float, cfg: Config) -> float:
    """What the two floors leave behind. Strictly under two base units per block."""
    blend, leader = split(reward_lgo, cfg)
    return reward_lgo - blend - leader


# ------------------------------------------------------------------ the stake estimate

@dataclass
class StakeEstimate:
    """The inferred total stake, and the block production it is inferred from.

    Seeded at the total distributed at genesis (`bedrock-genesis-block.md:317`), which is far
    above the target, so the emission factor clamps to zero and the chain opens on pure fee
    recycling. That is a launch transient: the estimator corrects by the ratio of observed to
    expected block density each epoch, so an overestimate of ten times is worked off in about
    one epoch and steady state arrives in about five.

    **The estimator is biased low by construction.** It converges to roughly 0.847 of true
    stake at the specified slot coefficient and 85% honest slot utilisation, so a persistent
    underestimate of stake means a persistent positive deviation -- and persistently more
    emission than the target intends. Modelled explicitly rather than left as an artefact.
    """

    value_lgo: float
    bias: float = 0.847

    def blocks_expected(self, cfg: Config) -> int:
        return cfg.blocks_per_epoch

    def blocks_produced(self, true_staked_lgo: float, cfg: Config, slots_per_epoch: int
                        ) -> int:
        """Blocks an epoch actually yields when the lottery is calibrated against a wrong D.

        The per-slot win probability is set from the estimate, so an estimate ten times the
        truth makes the difficulty ten times too hard and the epoch yields a tenth of the
        blocks. That shortfall is the signal the estimator corrects on.

        **The ratio is not clamped at one.** An estimate BELOW the truth makes the lottery too
        easy and yields MORE blocks than the target, which is how the estimator recovers from
        an undershoot. Clamping it would let the estimate fall and never climb back, and a
        first version of this did exactly that -- the estimate collapsed to 21 LGO and stayed
        there. The real bound is the number of slots: a slot can carry at most one block.
        """
        if self.value_lgo <= 0 or true_staked_lgo <= 0:
            return 1
        ratio = true_staked_lgo / self.value_lgo
        return int(np.clip(round(cfg.blocks_per_epoch * ratio), 1, slots_per_epoch))

    def update(self, blocks_seen: int, cfg: Config) -> "StakeEstimate":
        """One epoch's correction: scale by observed over expected density."""
        expected = self.blocks_expected(cfg)
        if expected <= 0:
            return self
        return StakeEstimate(max(1.0, self.value_lgo * blocks_seen / expected), self.bias)

    @classmethod
    def at_genesis(cls, cfg: Config) -> "StakeEstimate":
        return cls(cfg.genesis_stake_estimate)
