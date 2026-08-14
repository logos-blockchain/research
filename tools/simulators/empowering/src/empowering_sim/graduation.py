"""The on-ramp: how long a miner takes to reach the minimum stake, and how many ever do.

This is the study the simulator exists for. The mechanism's stated purpose is to let someone
with no stake mine their way into the stake-based system, so the question that decides whether
it works is not what the reward is but **how many people it can carry across the threshold,
and by when**.

Two answers live here, and they should be read together because the first bounds the second.
The ceiling is arithmetic and needs no simulation; the trajectory needs the engine.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import economics, engine
from .config import Config
from .nodes import NOT_GRADUATED, Population


# ---------------------------------------------------------------- the arithmetic ceiling

def graduate_ceiling(cfg: Config) -> dict:
    """How many minimum stakes the pool can ever pay out.

    | ``endowment_graduates = genesis_pool / min_stake``

    The pool is a finite endowment plus a fee stream. Every graduate must accumulate
    ``min_stake``, and the pool is the only place that money comes from, so the number of
    graduates the on-ramp can ever produce is bounded by the pool's total lifetime output
    divided by the threshold -- **whatever the distribution rate, the target claim rate, the
    difficulty, or the hardware**. Those parameters set the schedule; they cannot lift the
    ceiling, because none of them changes how much money exists.

    The fee-funded stream continues after the endowment drains, so the ceiling is not
    literally final -- but it arrives at a rate set by fee revenue, which is reported here
    alongside so the two can be compared honestly.
    """
    endowment = cfg.genesis_pool / cfg.min_stake
    per_epoch = economics.epoch_refill(cfg) / cfg.min_stake
    per_year = per_epoch * cfg.epochs_per_year
    return dict(
        endowment_graduates=endowment,
        fee_funded_per_epoch=per_epoch,
        fee_funded_per_year=per_year,
        years_per_fee_funded_graduate=(1.0 / per_year) if per_year > 0 else float("inf"),
        min_stake_lgo=cfg.to_lgo(cfg.min_stake),
        genesis_pool_lgo=cfg.to_lgo(cfg.genesis_pool),
    )


def endowment_fraction_for_graduates(cfg: Config, graduates: int) -> float:
    """The endowment, as a share of launch supply, needed to carry ``graduates`` across.

    The inverse of the ceiling, and the form a policy question wants: if the on-ramp is meant
    to seat a given number of participants, this is what it costs.
    """
    return graduates * cfg.min_stake / (cfg.launch_supply * cfg.base_units_per_lgo)


# ---------------------------------------------------------------- the simulated trajectory

@dataclass
class EpochOutcome:
    epoch: int
    years: float
    miners: int
    hashrate: float
    reward_per_claim: int
    net_per_claim: int
    claims_paid: int
    graduated_new: int
    graduated_total: int
    pool_open: int


def run(cfg: Config, joiners_per_epoch: float, epochs: int,
        units_each: float = 1.0, unit_hashrate: float | None = None,
        rng: np.random.Generator | None = None,
        deterministic: bool = False) -> tuple[Population, list[EpochOutcome]]:
    """Advance the pool and a growing mining population together.

    Arrivals are exogenous -- ``joiners_per_epoch`` is the network-use-pattern axis -- and
    every miner brings ``units_each`` device-equivalents. Participation is not yet endogenous:
    nobody leaves when mining stops paying, because that decision needs the cost estimator.
    Until then this is the *optimistic* case, which is the right way round: a bound that holds
    when everyone stays holds a fortiori when some leave.
    """
    rng = np.random.default_rng(cfg.seed) if rng is None else rng
    if unit_hashrate is None:
        if cfg.seconds_per_candidate_reward <= 0:
            raise ValueError("no measured candidate cost; pass unit_hashrate explicitly")
        unit_hashrate = 1.0 / cfg.seconds_per_candidate_reward

    capacity = int(np.ceil(joiners_per_epoch * epochs)) + 1
    pop = Population.empty(capacity)
    state = engine.genesis_state(cfg)

    out: list[EpochOutcome] = []
    owed = 0.0
    for e in range(epochs):
        owed += joiners_per_epoch
        if owed >= 1.0:
            pop.arrive(int(owed), e, units_each)
            owed -= int(owed)

        hashrate = pop.total_units * unit_hashrate
        row, state = engine.step_epoch(cfg, state, hashrate, e, rng, deterministic)

        # What a miner keeps is the reward less the fee it paid to submit the claim.
        net = max(0, row.reward_per_claim - cfg.claim_fee)
        new_grads = pop.credit(rng, row.claims_paid, net, e, cfg.min_stake)

        out.append(EpochOutcome(
            epoch=e, years=e / cfg.epochs_per_year, miners=pop.count,
            hashrate=hashrate, reward_per_claim=row.reward_per_claim,
            net_per_claim=net, claims_paid=row.claims_paid,
            graduated_new=new_grads, graduated_total=pop.graduated,
            pool_open=row.pool_open,
        ))
    return pop, out


def window_closes(pop: Population, cfg: Config, min_share: float = 0.5) -> dict:
    """The last arrival cohort of which at least ``min_share`` ever graduate.

    "The window" is the span of time during which joining is still worth doing. After it, a
    node that arrives can mine indefinitely and never reach the threshold, because the reward
    has decayed and the field it must share with has grown.
    """
    cohorts = pop.cohort_summary(cfg)
    made = [c for c in cohorts if c["share"] >= min_share]
    if not made:
        return dict(closes_epoch=None, closes_years=None, cohorts=len(cohorts))
    last = max(made, key=lambda c: c["cohort_epoch"])
    return dict(
        closes_epoch=last["cohort_epoch"],
        closes_years=last["cohort_years"],
        cohorts=len(cohorts),
        share_at_close=last["share"],
    )


def summarise(pop: Population, out: list[EpochOutcome], cfg: Config) -> dict:
    """The headline numbers from one run."""
    took = pop.time_to_graduate()
    return dict(
        miners=pop.count,
        graduated=pop.graduated,
        graduated_share=pop.graduated / pop.count if pop.count else 0.0,
        median_epochs_to_graduate=float(np.median(took)) if took.size else float("nan"),
        median_years_to_graduate=float(np.median(took) / cfg.epochs_per_year)
        if took.size else float("nan"),
        distributed_lgo=cfg.to_lgo(sum(o.claims_paid * o.net_per_claim for o in out)),
        final_pool_lgo=cfg.to_lgo(out[-1].pool_open) if out else 0.0,
        never_graduated=int((pop.graduated_epoch[:pop.count] == NOT_GRADUATED).sum()),
    )
