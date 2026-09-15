"""Mining against staking: when does a node stop working and start merely holding?

Two questions live here and they are not the same one.

**Does adding mining to a position pay?** That is marginal, and it is already answered by the
participation rule in :mod:`empowering_sim.market`: mine while the reward covers the
electricity. A node with stake does not face a choice between mining and staking -- it can do
both, and it should mine whenever mining alone is profitable.

**Which income dominates?** That is the question this module answers, and it is the one that
says what the on-ramp is *for*. Early, when the endowment is draining, a claim is worth more
than a thousand times the fee and mining swamps staking. Late, when the reward has settled
onto fee funding, a minimum stake earns more in a week than mining earns in years. Somewhere
between, the two cross, and that crossing is the moment the mechanism stops being a way to
earn and becomes a way to have earned.

**A comparison that has to be made carefully.** Mining income is a return on operating
expense; staking income is a return on capital already held. Collapsing them into one number
needs a discount rate, and there is none here. So both are reported as tokens per epoch for a
*specific node* -- one holding a given stake and running given hardware -- which is a
comparison of two cash flows that node actually faces, and is meaningful without a discount
rate. It says which stream is larger, not which is the better investment.

**What is not specified.** The share of a block's distributed reward reaching its leader is not
fixed anywhere in the specification tree. Everything below scales linearly in it, and it is a
parameter rather than a constant for that reason.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import consensus, economics
from .config import Config


@dataclass(frozen=True)
class Position:
    """One node's economic position: what it holds and what it runs."""

    stake: int                    # base units held and staked
    hashrate_share: float         # share of network mining power
    cost_per_candidate_usd: float = 0.0
    label: str = ""


def staking_income_per_epoch(cfg: Config, stake: int, staked_fraction: float,
                             txs_per_block: int | None = None) -> float:
    """Base units a staker earns in one epoch, from the reward distribution and from leader fees.

    | ``stake_share = stake / (staked_fraction * launch_supply)``

    ``staked_fraction`` is the share of supply staked network-wide, which sets how thin the
    competition is. The report treats it as an axis rather than a constant and so does this.
    """
    staked_total = staked_fraction * cfg.launch_supply * cfg.base_units_per_lgo
    if staked_total <= 0:
        return 0.0
    return consensus.leader_income_per_epoch(cfg, stake / staked_total, txs_per_block)


def mining_income_per_epoch(cfg: Config, hashrate_share: float,
                            reward_per_claim: int) -> float:
    """Base units a miner earns in one epoch, net of the fees it pays to claim."""
    return consensus.mining_income_per_epoch(cfg, hashrate_share, reward_per_claim)


def mining_cost_per_epoch_usd(cfg: Config, hashrate_share: float,
                              difficulty_target: int,
                              cost_per_candidate_usd: float) -> float:
    """Electricity a miner burns in one epoch.

    Cost follows the candidates tried, and at equilibrium the network tries
    ``target_claims_per_block * blocks_per_epoch`` claims' worth of them, so a miner's share
    of the spend is its share of the hashrate.
    """
    from .market import candidates_per_claim               # noqa: PLC0415
    claims = cfg.target_claims_per_block * cfg.blocks_per_epoch
    candidates = claims * candidates_per_claim(difficulty_target)
    return hashrate_share * candidates * cost_per_candidate_usd


def compare(cfg: Config, position: Position, pool: int, difficulty_target: int,
            staked_fraction: float, token_price_usd: float,
            txs_per_block: int | None = None) -> dict:
    """Both income streams for one node at one moment, in tokens per epoch."""
    reward = economics.reward_per_claim(pool, cfg)
    mining = mining_income_per_epoch(cfg, position.hashrate_share, reward)
    staking = staking_income_per_epoch(cfg, position.stake, staked_fraction, txs_per_block)
    cost_usd = mining_cost_per_epoch_usd(cfg, position.hashrate_share, difficulty_target,
                                         position.cost_per_candidate_usd)
    cost_tokens = (cost_usd / token_price_usd * cfg.base_units_per_lgo
                   if token_price_usd > 0 else float("inf"))
    return dict(
        reward_per_claim=reward,
        mining_gross_lgo=cfg.to_lgo(mining),
        mining_cost_lgo=cfg.to_lgo(cost_tokens),
        mining_net_lgo=cfg.to_lgo(mining - cost_tokens),
        staking_lgo=cfg.to_lgo(staking),
        mining_over_staking=(mining - cost_tokens) / staking if staking > 0 else float("inf"),
        mining_pays=(mining - cost_tokens) > 0,
        staking_dominates=staking > (mining - cost_tokens),
    )


def leader_overtakes_mining(cfg: Config, hashrate_share: float, pool: int | None = None,
                            staked_fraction: float | None = None,
                            emission_factor: float = 1.0, horizon: int = 6000) -> dict:
    """When a miner's LEADER income overtakes its mining income.

    The corrected crossover, and the one that matters. Leader rewards carry no minimum: a
    miner earns them on its whole aged balance from the first claim, so the comparison is
    between a growing stock and the flow that builds it, not between a flow and a threshold.

    | ``crossing when balance * apy_per_epoch > hashrate_share * distribution_rate * pool``

    **The field share and the pool size cancel; the distribution rate does not.** The flow a
    miner races is `distribution_rate * pool`, and the pool decays at exactly that rate, so a
    faster drain ends the race sooner: measured at epoch 570 -- 11.71 years -- at the 0.4
    leader share, identical at every field share, and moving with rho (354 epochs at 1/100,
    868 at 1/400). An earlier revision froze the pool, which made everything cancel and gave
    1,013 epochs; the closed form below is how that error was caught.
    """
    pool = float(cfg.genesis_pool if pool is None else pool)
    apy_epoch = consensus.validation_apy(cfg, staked_fraction, emission_factor) \
        / cfg.epochs_per_year
    if pool <= 0 or hashrate_share <= 0 or apy_epoch <= 0:
        return dict(epoch=None, years=None)

    refill = economics.epoch_refill(cfg)
    balance = 0.0
    for e in range(horizon):
        # The mining flow must be recomputed from the CURRENT pool. An earlier version of
        # this function hoisted it out of the loop and never decayed the pool, which silently
        # solved the rho -> 0 case and returned 1,013 epochs instead of 392 -- see the closed
        # form below, whose rho -> 0 limit is exactly ln(2)/ln(1+apy).
        flow = hashrate_share * cfg.distribution_rate * pool
        if balance * apy_epoch > flow:
            return dict(epoch=e, years=e / cfg.epochs_per_year,
                        balance_lgo=cfg.to_lgo(balance),
                        mining_lgo=cfg.to_lgo(flow))
        balance += flow + balance * apy_epoch
        pool += refill - cfg.distribution_rate * pool
    return dict(epoch=None, years=None, note="no crossing inside the horizon")


def leader_overtakes_mining_closed_form(cfg: Config, staked_fraction: float | None = None,
                                        emission_factor: float = 1.0) -> dict:
    """The crossing in closed form, ignoring the fee refill.

    With the pool decaying, a miner's balance solves
    ``B(t) = flow_0 * [(1+a)^t - (1-rho)^t] / (a + rho)``, and setting ``B(t)*a`` equal to
    the decayed flow gives

    | ``crossing_epochs = ln(2 + distribution_rate / apy_per_epoch) / ln((1 + apy_per_epoch) / (1 - distribution_rate))``

    The field share and the pool size cancel; the distribution rate does not. Its ``rho -> 0``
    limit is ``ln(2)/ln(1 + apy)``, which is the frozen-pool answer -- a useful check, since
    that is the number a hoisted flow silently produces.
    """
    import math
    a = consensus.validation_apy(cfg, staked_fraction, emission_factor) / cfg.epochs_per_year
    rho = cfg.distribution_rate
    if a <= 0 or rho <= 0 or rho >= 1:
        return dict(epochs=float("inf"), years=float("inf"))
    epochs = math.log(2 + rho / a) / math.log((1 + a) / (1 - rho))
    return dict(epochs=epochs, years=epochs / cfg.epochs_per_year,
                frozen_pool_limit_epochs=math.log(2) / math.log(1 + a))


def permanent_mining_dominance(cfg: Config, pow_share_of_block_reward: float,
                               leader_share_of_block_reward: float = 1.0) -> float:
    """The whole mining field's income over one minimum stake's leader income, forever.

    | ``dominance = pow_share * stake_target / (leader_share * min_stake_fraction)``

    Both legs are shares of the *same* block reward, so the emission factor, the maximum
    emission rate, the traffic, the fee level and the token price all cancel. What is left is
    a quotient of four protocol constants and no time at all -- which makes this the
    **permanent** term of the goal-1 gap, where the pool's decay is only the transient one.

    At the illustrated 2% proof-of-work leg this is 600, or 1,538 if leaders take 39%.
    """
    if leader_share_of_block_reward <= 0 or cfg.min_stake_fraction <= 0:
        return float("inf")
    return (pow_share_of_block_reward * cfg.stake_target
            / (leader_share_of_block_reward * cfg.min_stake_fraction))


def crossover_epoch(cfg: Config, position: Position, staked_fraction: float,
                    horizon: int = 3000, txs_per_block: int | None = None) -> dict:
    """The epoch at which staking income first exceeds mining income.

    Uses the pool's closed-form trajectory rather than a simulation, because the crossing is
    driven by the reward decaying onto its steady state and that decay is exact while every
    claim is paid. Electricity is excluded here: including it moves the crossing earlier, so
    this is the *latest* the crossing can occur.
    """
    staking = staking_income_per_epoch(cfg, position.stake, staked_fraction, txs_per_block)
    if staking <= 0:
        return dict(epoch=None, years=None, staking_lgo=0.0)
    # Staked proceeds do not earn from the moment they are mined: a note must be held for a
    # minimum period and appear in a frozen stake-distribution snapshot before it can win a
    # slot. So the comparison cannot begin before the aging has elapsed.
    for e in range(cfg.stake_aging_epochs, horizon):
        reward = economics.reward_at_epoch(cfg, e, txs_per_block)
        mining = position.hashrate_share * cfg.target_claims_per_block * cfg.blocks_per_epoch \
            * max(0.0, reward - cfg.claim_fee)
        if staking > mining:
            return dict(epoch=e, years=e / cfg.epochs_per_year,
                        staking_lgo=cfg.to_lgo(staking),
                        mining_lgo=cfg.to_lgo(mining))
    return dict(epoch=None, years=None, staking_lgo=cfg.to_lgo(staking),
                note="staking never overtakes inside the horizon")


def service_ceiling(cfg: Config) -> dict:
    """Positions the endowment can bootstrap into SERVICE provision.

    The threshold, and therefore this ceiling, belong to the service layer. Consensus
    participation has no threshold at all, so it is neither bounded by the endowment nor in
    need of an on-ramp -- which is the single most important consequence of separating the
    two participation classes.
    """
    return dict(
        service_positions=cfg.genesis_pool / cfg.min_stake,
        consensus_positions=float("inf"),
        consensus_gate=f"{cfg.stake_aging_epochs} epochs of note aging, no minimum",
        service_gate=f"{cfg.to_lgo(cfg.min_stake):,.0f} LGO locked",
    )


# ------------------------------------------------------------------ interpreting min_stake

def min_stake_reading(cfg: Config, min_stake_lgo: float, hashrate_share: float,
                      staked_fraction: float, txs_per_block: int | None = None) -> dict:
    """What one choice of minimum stake implies, on every axis it touches at once.

    The specified value is a given; what it is not is self-evidently right, and it pulls in
    two directions that have to be weighed together:

    - **lower** seats more participants and seats them sooner, because the ceiling is the
      endowment over the threshold and the wait is the threshold over the payout rate;
    - **higher** makes graduating worth something, because a stake earns in proportion to its
      size and a trivial stake earns trivially.

    A threshold that seats a thousand people into positions that pay nothing has not built an
    on-ramp, and neither has one that seats five people handsomely.
    """
    stake = round(min_stake_lgo * cfg.base_units_per_lgo)
    ceiling = cfg.genesis_pool / stake if stake else float("inf")
    # Time to reach it, from the closed form: threshold over what the pool pays this node.
    epochs = (stake / (cfg.distribution_rate * cfg.genesis_pool * hashrate_share)
              if hashrate_share > 0 else float("inf"))
    staking = staking_income_per_epoch(cfg, stake, staked_fraction, txs_per_block)
    return dict(
        min_stake_lgo=min_stake_lgo,
        fraction_of_supply=stake / (cfg.launch_supply * cfg.base_units_per_lgo),
        graduates_the_endowment_funds=ceiling,
        epochs_to_graduate=epochs,
        years_to_graduate=epochs / cfg.epochs_per_year,
        staking_lgo_per_epoch=cfg.to_lgo(staking),
        staking_lgo_per_year=cfg.to_lgo(staking) * cfg.epochs_per_year,
        # What the position yields annually against what it cost to reach it.
        annual_yield_on_stake=(cfg.to_lgo(staking) * cfg.epochs_per_year / min_stake_lgo
                               if min_stake_lgo else float("inf")),
    )


def conservation_product(cfg: Config, pool: int, hashrate_share: float, min_stake: int,
                         staked_fraction: float, txs_per_block: int | None = None) -> dict:
    """Graduation time times mining dominance -- a constant, and the design's obstacle.

    | ``graduation_epochs * mining_dominance = staked_total / released_per_epoch``

    Both factors are proportional to ``hashrate_share * distribution_rate * pool``, one in a
    numerator and one in a denominator, so it cancels -- and so does the threshold. The
    product is one over the staking yield and nothing else.

    Its consequence is that **fast onboarding and a staking-favoured endpoint are the same
    dial pulled in opposite directions**. Staking can only pay more than mining at the moment
    of graduation if graduation takes longer than the reciprocal of the staking yield, which
    at the specified parameters is seventy-five years (the reciprocal of the 1.33% leader-leg
    yield; thirty would be the whole-emission reading the config does not carry). No endowment size, distribution rate, claim
    target or minimum stake escapes it; only a change of mechanism does.
    """
    staked_total = staked_fraction * cfg.launch_supply * cfg.base_units_per_lgo
    released = consensus.max_block_reward_base_units(cfg) * cfg.blocks_per_epoch \
        * cfg.leader_reward_share
    payout = cfg.distribution_rate * pool                     # base units the pool pays/epoch
    if hashrate_share <= 0 or payout <= 0 or released <= 0 or staked_total <= 0:
        return dict(graduation_epochs=float("inf"), mining_dominance=0.0, product=float("nan"))

    graduation = min_stake / (hashrate_share * payout)
    dominance = (hashrate_share * payout) * staked_total / (min_stake * released)
    return dict(
        graduation_epochs=graduation,
        graduation_years=graduation / cfg.epochs_per_year,
        mining_dominance=dominance,
        product=graduation * dominance,
        expected=staked_total / released,
        staking_yield_per_year=released / staked_total * cfg.epochs_per_year,
    )


def minimal_reward_base_units(cfg: Config, inscription_bytes: int = 1024) -> int:
    """A transfer plus an inscription, at the resting price: the target for the steady reward.

    | ``minimal_reward = transfer_fee + inscription_fee``

    Defined as a bundle of transactions rather than as a share of fee revenue, so that it
    tracks the fee market instead of floating with traffic. That distinction is the whole of
    the second design goal: the current steady reward is close to this level by accident and
    is not pinned to it by construction.
    """
    transfer = (cfg.transfer_tx_bytes + cfg.transfer_tx_gas) * cfg.price_resting
    inscription = (inscription_bytes + cfg.inscribe_gas) * cfg.price_resting
    return transfer + inscription


def boosted_apy_for_dominance(graduation_years: float) -> float:
    """Yield an onboarded staker needs for staking to match mining at graduation.

    | ``boosted_apy = 1 / graduation_years``

    Independent of the base yield, because the boost multiplies out whatever the base was --
    which is why the cost of supplying it lands on the same figure at every reading of who
    receives the emission. At the design point's 4.11 years it is 24.3% a year.
    """
    return 1.0 / graduation_years if graduation_years > 0 else float("inf")


def pow_share_of_block_reward_for(cfg: Config, reward_per_claim_base_units: int,
                                  emission_factor: float = 1.0) -> float:
    """Leg of the block reward that would pay a stated reward per claim.

    | ``pow_share = claims_per_epoch * reward_per_claim / block_reward_per_epoch``

    The proposal already gives proof of work a leg of the block reward. Sizing that leg to
    the minimal transaction bundle is what delivers the second design goal without an
    endowment and without floating with fee revenue -- and it comes out at about 1.4 parts
    per million, against the 2% the proposal illustrates.
    """
    per_epoch = (consensus.max_block_reward(cfg) * emission_factor
                 * cfg.blocks_per_epoch * cfg.base_units_per_lgo)
    if per_epoch <= 0:
        return float("inf")
    claims = cfg.target_claims_per_block * cfg.blocks_per_epoch
    return claims * reward_per_claim_base_units / per_epoch


def min_stake_for_participants(cfg: Config, participants: int) -> float:
    """The threshold that would let the endowment seat exactly ``participants``, in LGO.

    | ``min_stake = genesis_pool / participants``

    The inverse of the ceiling, and the form the policy question wants: choose how many
    people the on-ramp is meant to carry and this is the threshold that carries them.
    """
    if participants <= 0:
        return float("inf")
    return cfg.to_lgo(cfg.genesis_pool / participants)
