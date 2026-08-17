"""The endogenous run: arrivals are exogenous, participation is not.

The difference from :mod:`empowering_sim.graduation` is one decision per node per epoch --
whether the work pays -- and everything that follows from it. Miners who cannot cover their
electricity stop, the hashrate falls, the controller relaxes the target, the work gets
cheaper, and some of them come back. The difficulty settles where the cheapest class
available breaks even.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import economics, engine, market
from .config import Config
from .nodes import NOT_GRADUATED, Population
from .scenarios import Scenario


@dataclass
class EpochOutcome:
    epoch: int
    years: float
    miners: int
    mining: int
    hashrate: float
    txs_per_block: int
    token_price: float
    reward_per_claim: int
    claims_paid: int
    difficulty_target: int
    candidates_per_claim: float
    graduated_total: int
    pool_open: int
    active_by_class: tuple[int, ...]
    # Fraction of the epoch's blocks each class could afford the work. A class at 1.0 is
    # comfortably in the field and at 0.0 is priced out; anything between is MARGINAL, which
    # is where the difficulty settles -- the controller relaxes until the cheapest class is
    # indifferent, so that class spends part of its time in and part out. Reporting this as a
    # boolean would hide the equilibrium the whole study is about.
    active_fraction_by_class: tuple[float, ...]
    break_even_price: float          # for the cheapest class, at this epoch's difficulty


def run(cfg: Config, scenario: Scenario,
        rng: np.random.Generator | None = None) -> tuple[Population, list[EpochOutcome]]:
    """Advance pool, difficulty and a population whose members choose whether to mine."""
    rng = np.random.default_rng(cfg.seed) if rng is None else rng
    probs = scenario.arrival_probabilities()
    rates, costs = scenario.rates(), scenario.costs()
    n_classes = len(scenario.classes)

    capacity = int(np.ceil(scenario.joiners_per_epoch * scenario.epochs)) + 1
    pop = Population.empty(capacity)
    state = engine.genesis_state(cfg)

    out: list[EpochOutcome] = []
    owed = 0.0
    for e in range(scenario.epochs):
        owed += scenario.joiners_per_epoch
        n_new = int(owed)
        if n_new:
            owed -= n_new
            ids = rng.choice(n_classes, size=n_new, p=probs).astype(np.int32)
            pop.arrive_classed(n_new, e, ids, rates, costs)

        txs = scenario.traffic(cfg, e)
        price = scenario.token_price(cfg, e)

        # The reward this epoch will pay is fixed the moment it opens, so participation is
        # decided against it rather than against the previous epoch's.
        reward = economics.reward_per_claim(state.pool, cfg)
        live = slice(0, pop.count)
        classes_live = pop.device_class[live]
        members = np.array([int((classes_live == k).sum()) for k in range(n_classes)])
        net_tokens = max(0, reward - cfg.claim_fee) / cfg.base_units_per_lgo
        net_usd = net_tokens * price

        def hashrate_fn(target: int, _members=members, _net=net_usd) -> tuple:
            """Power each class contributes at this target. Re-evaluated every block,
            because the controller moves every block and a class that cannot pay for the
            work stops immediately rather than at the next epoch boundary."""
            per_claim = market.candidates_per_claim(target)
            mining = (per_claim * costs) < _net if _net > 0 else np.zeros(n_classes, bool)
            per_group = np.where(mining, _members * rates, 0.0)
            return float(per_group.sum()), per_group

        row, state = engine.step_epoch(cfg, state, hashrate_fn, e, rng, txs_per_block=txs)

        net = max(0, row.reward_per_claim - cfg.claim_fee)
        credit = row.group_credit if row.group_credit is not None else np.zeros(n_classes)
        pop.credit_groups(rng, credit, net, e, cfg.min_stake)

        # Report each class by the share of the epoch it was able to mine, which carries
        # more than a boolean: a class can be marginal and in the field only part of the time.
        blocks = row.active_blocks if row.active_blocks is not None else np.zeros(n_classes)
        frac = tuple(float(blocks[k]) / cfg.blocks_per_epoch for k in range(n_classes))
        by_class = tuple(int(members[k]) if frac[k] > 0.5 else 0 for k in range(n_classes))
        pop.active[live] = np.isin(classes_live,
                                   [k for k in range(n_classes) if frac[k] > 0.5])

        out.append(EpochOutcome(
            epoch=e, years=e / cfg.epochs_per_year,
            miners=pop.count, mining=int(pop.active[live].sum()),
            hashrate=row.hashrate, txs_per_block=txs, token_price=price,
            reward_per_claim=row.reward_per_claim, claims_paid=row.claims_paid,
            difficulty_target=row.difficulty_target_close,
            candidates_per_claim=market.candidates_per_claim(row.difficulty_target_close),
            graduated_total=pop.graduated, pool_open=row.pool_open,
            active_by_class=by_class, active_fraction_by_class=frac,
            break_even_price=market.break_even_token_price(
                cfg, row.reward_per_claim, row.difficulty_target_close,
                scenario.cheapest_cost()),
        ))
    return pop, out


# ------------------------------------------------------------------ working-region tests

def constraints(cfg: Config, pop: Population, out: list[EpochOutcome],
                scenario: Scenario) -> dict:
    """Which of the model's conditions a scenario satisfies.

    A working region is where all of them hold at once, so each is reported separately and
    the conjunction is taken by the caller. Reporting only the conjunction hides *which*
    constraint bound, which is the part that tells you what to change.
    """
    if not out:
        return {}
    last = out[-1]
    # Only epochs that have miners at all. Before the first arrival seats, the fraction is
    # zero because the population is empty, which is not the same as mining having stopped --
    # counting the startup transient as a failure marked every slow-arrival scenario dead.
    mining_frac = [o.mining / o.miners for o in out if o.miners > 0]
    if not mining_frac:
        mining_frac = [0.0]

    self_funding_need = economics.self_funding_txs(cfg)
    mean_txs = float(np.mean([o.txs_per_block for o in out]))

    return dict(
        # The pool sustains itself once traffic is heavy enough.
        self_funding=mean_txs > self_funding_need,
        self_funding_margin=mean_txs / self_funding_need if self_funding_need else float("inf"),
        # Claiming is worth doing at all.
        claiming_continues=last.reward_per_claim > cfg.claim_fee,
        # Somebody can afford the work, throughout.
        mining_never_died=min(mining_frac) > 0.0,
        min_mining_fraction=float(min(mining_frac)),
        final_mining_fraction=mining_frac[-1],
        # The on-ramp actually seats people.
        graduates=pop.graduated,
        graduated_any=pop.graduated > 0,
        pooled_equivalent=int(pop.balance[:pop.count].sum()) // cfg.min_stake,
        # The class the design targets is still in the field at the end.
        classes=scenario.class_keys,
        active_by_class_final=last.active_by_class,
        active_fraction_final=last.active_fraction_by_class,
        break_even_price_final=last.break_even_price,
    )


def excluded_classes(pop: Population, out: list[EpochOutcome],
                     scenario: Scenario) -> list[str]:
    """Device classes that end the run unable to mine. The decentralisation reading."""
    if not out:
        return []
    return [scenario.class_keys[k]
            for k, f in enumerate(out[-1].active_fraction_by_class) if f <= 0.01]
