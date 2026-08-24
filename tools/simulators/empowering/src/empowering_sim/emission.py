"""The KPI-driven block reward, the pool and reserve stocks, and the stake estimate.

Transcribed from `block-rewards.md`'s normative form and
`cryptarchia-total-stake-inference.md`'s estimator, with the decisions in
`docs/CONTRADICTIONS.md` applied: the deviation coefficient is 1/4 (4.2), the split is floored
per block (4.6), and the genesis stake estimate is the total distributed at genesis (4.3).

**Pooling, not burning (lips PR 375, `block-rewards.md` 1.1.0).** Fees are routed into a
pending rewards pool rather than burned, and rewards are distributed from that pool plus a
metered release from a finite genesis reserve rather than minted. Three consequences land
here: the recycled term of the block reward is the WINDOWED AVERAGE of pooled fees, not the
latest block's (`block_reward_lgo`); the pool and reserve are explicit stocks with a
conservation identity (`Stocks`); and the vocabulary is pooled, not burnt. The PR's own
integer section is flagged "Rederivation required" -- its Rust body still uses the
single-block fee -- so the superseded form is kept callable as
`block_reward_lgo_single_block` for parity with `master`, and the divergence is recorded as
contradiction 4.12.

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
STAKE_TARGET_LGO = 3_000_000_000          # D_0,target = 30% of S_cap (10^10 LGO, the hard cap)
POOL_WINDOW = 120                          # T, the look-back in blocks

# The rewards reserve (PR 375): pre-allocated at genesis from the cap, drawn down by the
# release, never refilled. B_0 = I_max * S_cap * Y with Y = 10 years: 1% of 10^10 over ten
# years is 10^9 LGO, a tenth of the cap. The release cap per block is the familiar
# 62500/657 = 95.1294 LGO -- the reserve funds it for exactly Y years at A_t = 1, longer
# whenever A_t < 1.
RESERVE_LIFETIME_YEARS = 10
RESERVE_GENESIS_LGO = 1_000_000_000.0


def emission_factor_scaled(total_stake_lgo: float, pooled_window_lgo: list[float]) -> int:
    """``A_t'``, the emission rate factor before scaling. Integer, as the consensus rule is.

    | ``A_t' = min(A_SCALE, max(0, STAKE_TARGET - total_stake + FEE_AVG_NUMERATOR * sum(pooled_window)))``

    The first term is the stake deviation and the second the pooling-rate average. Both are
    read in LGO. Clamped to ``[0, A_SCALE]`` on both sides, so it saturates rather than
    inverting. Unchanged by PR 375 -- this KPI was windowed all along.
    """
    raw = (STAKE_TARGET_LGO - total_stake_lgo
           + FEE_AVG_NUMERATOR * sum(pooled_window_lgo[-POOL_WINDOW:]))
    return int(min(A_SCALE, max(0, raw)))


def emission_factor(total_stake_lgo: float, pooled_window_lgo: list[float]) -> float:
    """``A_t`` in [0, 1]: one is maximum reserve release, zero is pure fee recycling."""
    return emission_factor_scaled(total_stake_lgo, pooled_window_lgo) / A_SCALE


def windowed_average_lgo(pooled_window_lgo: list[float]) -> float:
    """``R-bar``: the moving average of pooled fees over the look-back window.

    | ``R_bar = sum(window[-T:]) / T`` -- always divided by T

    The window-boundary rule, decided here because the specification's sum runs from
    ``t - T + 1`` without saying what pre-genesis entries are: they are zero. A shorter
    history therefore averages against the full T, ramping the recycled term in smoothly
    from genesis instead of letting one early fee spike masquerade as a hot hour.
    """
    return sum(pooled_window_lgo[-POOL_WINDOW:]) / POOL_WINDOW


def block_reward_lgo(total_stake_lgo: float, pooled_window_lgo: list[float]) -> float:
    """Total reward distributed for one block, in LGO. PR 375's equation (1).

    | ``reward = (62500 * A_t' + 657 * (A_SCALE - A_t') * R_bar) / (657 * A_SCALE)``

    At ``A_t = 1`` this is 62500/657 = 95.1294 LGO -- the reserve-release cap -- and the fees
    do not enter. At ``A_t = 0`` it is the windowed average of pooled fees, distributed back.
    The single-block form this replaces is `block_reward_lgo_single_block`.
    """
    a = emission_factor_scaled(total_stake_lgo, pooled_window_lgo)
    r_bar = windowed_average_lgo(pooled_window_lgo)
    return ((INFLATION_NUMERATOR * a + INFLATION_DENOMINATOR * (A_SCALE - a) * r_bar)
            / (INFLATION_DENOMINATOR * A_SCALE))


def block_reward_lgo_single_block(total_stake_lgo: float,
                                  pooled_window_lgo: list[float]) -> float:
    """The superseded recycled term: the LATEST block's fee, not the windowed average.

    This is `master`'s rule, and it is also what PR 375's own integer section and Rust
    reference still compute -- the PR flags that section "Rederivation required" rather than
    fixing it, so until the rederivation lands the specification's real-valued rule and its
    consensus-level reference disagree (contradiction 4.12). Kept callable so the parity gate
    can pin the divergence instead of letting it hide.
    """
    a = emission_factor_scaled(total_stake_lgo, pooled_window_lgo)
    fee_now = pooled_window_lgo[-1] if pooled_window_lgo else 0.0
    return ((INFLATION_NUMERATOR * a + INFLATION_DENOMINATOR * (A_SCALE - a) * fee_now)
            / (INFLATION_DENOMINATOR * A_SCALE))


@dataclass
class Stocks:
    """The pending rewards pool and the genesis reserve, as explicit state (PR 375).

    The RFC's conservation identity is the point: with ``S`` the circulating supply,
    ``delta_S + delta_P + delta_B = 0`` at every step -- tokens move between circulation,
    the pool and the reserve, and none are created or destroyed. `step` returns the reward
    paid and the class keeps the running residual so a gate can assert it is identically
    zero rather than trusting the algebra.

    ``guard_pool`` is the RFC's one open boundary question, made runnable. The specification
    states ``P_t >= 0`` but the early-life regime can violate it: after a fee spike falls
    silent, the windowed average keeps distributing history the pool never banked (a spike
    then silence at ``A_t = 0`` drives the unguarded balance negative -- measured in the
    gate). Guarded, the distribution is clipped to what the pool actually holds, which is
    this simulator's boundary treatment and the shape of an answer to the open question:
    the same move the de-novo engine's room cap makes.
    """

    reserve_lgo: float = RESERVE_GENESIS_LGO
    pool_lgo: float = 0.0
    guard_pool: bool = True
    conservation_residual_lgo: float = 0.0

    def step(self, total_stake_lgo: float, pooled_window_lgo: list[float]) -> float:
        """Advance one block: route the fee in, release and distribute, return the reward."""
        fee_in = pooled_window_lgo[-1] if pooled_window_lgo else 0.0
        a = emission_factor(total_stake_lgo, pooled_window_lgo)
        r_bar = windowed_average_lgo(pooled_window_lgo)

        release = min(a * INFLATION_NUMERATOR / INFLATION_DENOMINATOR, self.reserve_lgo)
        distribution = (1.0 - a) * r_bar
        if self.guard_pool:
            distribution = min(distribution, self.pool_lgo + fee_in)

        reward = distribution + release
        d_supply = reward - fee_in
        d_pool = fee_in - distribution
        d_reserve = -release
        self.pool_lgo += d_pool
        self.reserve_lgo += d_reserve
        self.conservation_residual_lgo += d_supply + d_pool + d_reserve
        return reward


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

    **The real estimator is biased low; this one is not, and deliberately.** On the real
    network the estimate converges to roughly 0.847 of true stake (slot coefficient 1/30, 85%
    honest slot utilisation), a persistent underestimate and therefore persistently more
    emission than the target intends. The bias comes from missed slots and forks -- exactly
    what this simulator's ideal chain (section 1.4 of the report: no forks, no churn, every
    provider honest) does not have. So HERE the estimate converges to true stake, the bias is
    identically one, and the real network's extra late-era emission is recorded as a
    limitation in the report's final section rather than reproduced. An earlier revision
    carried a ``bias = 0.847`` field that nothing ever read, while this docstring claimed the
    bias was "modelled explicitly"; the field is gone and the claim was false.

    **The observation window is widened.** `cryptarchia-total-stake-inference.md` observes
    ``PERIOD`` = 388,800 slots (12,960 expected blocks); this class uses the whole epoch's
    density. At the specified beta = 1 the update rule reduces to the same one-step scaling
    either way and the fixed point is identical -- the widening only smooths the noise the
    shorter window would carry.
    """

    value_lgo: float

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
        return StakeEstimate(max(1.0, self.value_lgo * blocks_seen / expected))

    @classmethod
    def at_genesis(cls, cfg: Config) -> "StakeEstimate":
        return cls(cfg.genesis_stake_estimate)
