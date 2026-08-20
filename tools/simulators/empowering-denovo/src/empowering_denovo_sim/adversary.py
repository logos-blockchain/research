"""Adversarial analysis of the de-novo mechanism, by simulation.

Each attack is a concrete run with a hostile actor, measured against the honest baseline. The
engine's admission rules are reused faithfully -- F-first draw, room cap, borrow-forward,
the epoch-fixed reward -- so an attack that the model resists resists it for the model's own
reasons, not a simplification's.

Threats considered:

* **the whale** -- one actor with a large hashrate share, extracting the endowment through the
  borrow-forward inside the demand index's one-epoch repricing lag (MODEL 8.2; the accepted
  Q8 exposure). Here: how much, and does arrival timing help it.
* **the pump** -- an actor that WITHHOLDS its claims one epoch to shrink `claims_prev`, then
  floods the next epoch at the inflated `budget / claims_prev` reward. Tests whether the
  reward cap `max(claims_prev, blocks_per_epoch)` defeats a *minority* pump.
* **the manufactured cliff** -- an elastic actor that enters only when the reward clears a
  threshold, deliberately driving the period-2 cycle (MODEL 8.1) to harvest the high epochs.

The whale and the cliff are documented, accepted properties (Q8, Q9); the analysis quantifies
the accepted exposure. The pump is the one that could be a surprise, so it is tested hardest.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from empowering_sim import work

from . import power
from .params import Derived


@dataclass
class TwoPopRow:
    epoch: int
    bootstrap: bool
    reward: int
    claims_prev: int
    honest_paid: int
    adv_paid: int
    adv_active: bool
    endowment: int


def two_population_run(d: Derived, honest_rate: float, adv_rate: float, adv_active,
                       epochs: int, seed: int = 90_001, txs_per_block: int | None = None,
                       deterministic: bool = False) -> list[TwoPopRow]:
    """Advance the chain with an honest field and one adversary whose participation toggles.

    ``adv_active(epoch, last_reward) -> bool`` decides whether the adversary offers claims
    this epoch. Both populations offer Poisson claims at the floor difficulty (bootstrap) or
    the throttled difficulty (post); paid claims split by hashrate weight. Reward and budget
    follow MODEL exactly, so `claims_prev` is the previous epoch's TOTAL paid, which is the
    quantity the adversary is trying to move.
    """
    cfg = d.cfg
    rng = np.random.default_rng(seed)
    txs = cfg.txs_per_block if txs_per_block is None else txs_per_block

    endowment = d.endowment_genesis
    fee_bucket = 0
    claims_prev = 0
    floor = cfg.genesis_difficulty_target
    difficulty = floor
    diverted = txs * cfg.avg_tx_fee * cfg.pow_share_num // cfg.pow_share_den

    honest_balance = 0
    adv_balance = 0
    rows: list[TwoPopRow] = []
    last_reward = 0

    for e in range(epochs):
        if endowment > 0:
            if e < d.bootstrap_epochs:
                sub = endowment // (d.bootstrap_epochs - e)
            else:
                sub = min(endowment, d.endowment_genesis // d.bootstrap_epochs)
            budget = sub + fee_bucket
            reward = max(d.anchor, budget // max(claims_prev, cfg.blocks_per_epoch))
            if endowment < reward:
                fee_bucket += endowment
                endowment = 0
        if endowment == 0:
            budget = fee_bucket
            reward = d.anchor
        bootstrap = endowment > 0

        active = bool(adv_active(e, last_reward))
        h_mu = work.expected_claims(honest_rate, difficulty, cfg)
        a_mu = work.expected_claims(adv_rate, difficulty, cfg) if active else 0.0

        capacity = None if bootstrap else budget // reward
        spent = 0
        h_paid = a_paid = 0
        for _ in range(cfg.blocks_per_epoch):
            ho = int(round(h_mu)) if deterministic else int(rng.poisson(h_mu)) if h_mu else 0
            ao = int(round(a_mu)) if deterministic else int(rng.poisson(a_mu)) if a_mu else 0
            ho = min(ho, cfg.max_block_txs)
            ao = min(ao, max(0, cfg.max_block_txs - ho))
            offered = ho + ao
            if bootstrap:
                room = (fee_bucket + endowment) // reward if reward else 0
            else:
                room = (budget - spent) // reward if reward else 0
            paid = min(offered, max(0, room))
            if paid:
                # split the paid claims between the two populations by their offered shares
                a_here = int(rng.hypergeometric(ao, ho, paid)) if (ao and paid < offered) else \
                    (paid if ho == 0 else min(ao, paid))
                h_here = paid - a_here
                take = paid * reward
                draw_f = min(take, fee_bucket)
                fee_bucket -= draw_f
                endowment -= take - draw_f
                spent += take
                h_paid += h_here
                a_paid += a_here
            if not bootstrap:
                # throttle only while admitting (the MODEL 4.2 rule)
                if spent + reward <= budget:
                    tgt = max(1, capacity // cfg.blocks_per_epoch)
                    difficulty = _retarget(difficulty, paid, tgt, cfg)
        if bootstrap:
            difficulty = floor

        net = max(0, reward - cfg.claim_fee)
        honest_balance += h_paid * net
        adv_balance += a_paid * net
        rows.append(TwoPopRow(e, bootstrap, reward, claims_prev, h_paid, a_paid, active,
                              endowment))
        fee_bucket += diverted * cfg.blocks_per_epoch
        claims_prev = h_paid + a_paid
        last_reward = reward
    return rows, honest_balance, adv_balance


def _retarget(difficulty, claims, target, cfg):
    from empowering_sim.config import FIELD_MODULUS
    demand = max(1, (cfg.smoothing_precision - cfg.smoothing_factor) * claims
                 + cfg.smoothing_factor * target)
    return min((target * difficulty * cfg.smoothing_precision) // demand, FIELD_MODULUS - 1)


# --------------------------------------------------------------------- the pump

def pump_vs_honest(d: Derived, control_fraction: float, epochs: int = 60,
                   seed: int = 90_001) -> dict:
    """Does an actor controlling ``control_fraction`` of hashrate profit by withholding?

    The attacker withholds on even epochs (shrinking `claims_prev`) and floods on odd ones
    (claiming at the raised reward). Compared against the same actor mining honestly every
    epoch. The reward cap should keep the pump from paying: withholding forfeits a whole
    epoch's claims to raise the next reward by a factor the cap bounds.
    """
    # A thousand committed miners at the honest board basis. The pump's outcome is a RATIO
    # against the same actor mining honestly, so the absolute field cancels -- shown robust
    # across three orders of magnitude in the report.
    field = power.board(d.cfg).candidates_per_second * 1000
    c = control_fraction
    honest_rate = field * (1 - c)
    adv_rate = field * c

    # honest baseline: the attacker mines every epoch
    _, _, adv_honest = two_population_run(
        d, honest_rate, adv_rate, lambda e, r: True, epochs, seed)
    # the pump: withhold on even epochs, flood on odd
    rows, _, adv_pump = two_population_run(
        d, honest_rate, adv_rate, lambda e, r: e % 2 == 1, epochs, seed)

    return dict(
        control_fraction=c,
        adv_balance_honest=adv_honest,
        adv_balance_pump=adv_pump,
        pump_advantage=adv_pump / adv_honest if adv_honest else float("inf"),
        rewards=[r.reward for r in rows[:8]],
    )


def main() -> int:
    from .params import Triple
    from . import scenarios
    d = Triple().derived().check()

    print("The pump: withhold to inflate the reward, then flood")
    for c in (0.10, 0.25, 0.50, 0.75, 0.90):
        r = pump_vs_honest(d, c, epochs=40)
        print(f"  {c:>5.0%} of the field: {r['pump_advantage']:.2f}x of mining honestly")

    print("\nThe whale: when to arrive")
    for we in (2, 20, 50, 100, 150):
        r = scenarios.whale_run(d, 130, whale_epoch=we, whale_multiple=10.0, epochs=220)
        print(f"  epoch {we:>3}: {r.pop.balance.max() / d.endowment_genesis:>4.0%} of the "
              f"endowment, phase ends {r.transition_epoch}")

    print("\nThe manufactured cliff: mine only above a threshold")
    field = power.board(d.cfg).candidates_per_second * 1000
    _, _, always = two_population_run(d, field * 0.7, field * 0.3, lambda e, r: True, 60)
    for thr in (3e9, 5e9, 8e9):
        _, _, picky = two_population_run(d, field * 0.7, field * 0.3,
                                         lambda e, r, T=thr: r >= T, 60)
        print(f"  threshold {thr / 1e9:>4.0f} LGO: {picky / always:.2f}x of always-on")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
