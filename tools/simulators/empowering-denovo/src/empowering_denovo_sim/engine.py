"""The two-bucket engine: MODEL.md sections 3-5, executable.

Integer arithmetic in lepta throughout. The per-block loop is deliberate -- the saturation
point and the throttle's convergence are within-epoch phenomena, and this simulator exists to
measure them.

Two difficulty regimes, per the amended Q4: a constant floor during bootstrap (admission
control is economic), the existing EMA retarget with a derived target after the transition.
The retarget implementation is `empowering_sim.work.next_difficulty_target`, unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from empowering_sim import work
from empowering_sim.config import Config

from .params import Derived

NOT_SET = -1


@dataclass
class Population:
    """Miners: arrival epoch, hashrate, balance, bond. Grown by the arrival process."""

    hashrate: np.ndarray            # candidates/second
    arrived: np.ndarray             # epoch seated; NOT_SET if not yet
    balance: np.ndarray             # lepta, accumulated net rewards
    bonded_at: np.ndarray           # epoch the bond was reached; NOT_SET otherwise

    @classmethod
    def empty(cls, capacity: int) -> "Population":
        return cls(hashrate=np.zeros(capacity),
                   arrived=np.full(capacity, NOT_SET, dtype=np.int32),
                   balance=np.zeros(capacity, dtype=np.int64),
                   bonded_at=np.full(capacity, NOT_SET, dtype=np.int32))

    def live_mask(self, retire_on_bond: bool) -> np.ndarray:
        m = self.arrived >= 0
        if retire_on_bond:
            m &= self.bonded_at == NOT_SET
        return m


@dataclass
class EpochRow:
    epoch: int
    bootstrap: bool
    endowment: int
    fee_bucket_opening: int
    budget: int
    reward: int
    claims_paid: int
    spent: int
    saturation_block: int           # NOT_SET if the budget was never exceeded/stopped short
    max_block_claims: int           # the fullest block's paid claims -- the block-space question
    bonds_total: int
    bonds_new: int
    miners_live: int
    difficulty_target: int
    endowment_drawn: int            # what this epoch took from the endowment bucket


@dataclass
class Result:
    rows: list[EpochRow]
    pop: Population
    transition_epoch: int           # NOT_SET if bootstrap never ended in-horizon
    final_endowment: int = 0        # buckets at the end, for conservation gating
    final_fee_bucket: int = 0
    total_diverted: int = 0
    total_paid: int = 0
    d: Derived = field(repr=False, default=None)

    def bonds_by_cohort(self) -> dict[int, int]:
        """Arrival epoch -> bonds reached. The R5 admission metric."""
        got = self.pop.bonded_at != NOT_SET
        out: dict[int, int] = {}
        for a in np.unique(self.pop.arrived[got]):
            out[int(a)] = int((self.pop.arrived[got] == a).sum())
        return out


def run(d: Derived, arrivals: np.ndarray, hashrate_draw, epochs: int,
        retire_on_bond: bool = True, txs_per_block: int | None = None,
        seed: int = 70_001, deterministic: bool = False,
        participation=None) -> Result:
    """Advance the chain.

    ``arrivals[e]`` miners are seated at epoch ``e`` with hashrates from ``hashrate_draw(n)``.
    ``deterministic`` replaces Poisson draws with their expectation (for gating closed forms).

    ``participation(reward_lepta, epoch) -> [0, 1]`` scales the epoch's active search power --
    the elasticity hook for MODEL.md section 8.1's oscillation probe. Miners see the epoch's
    posted reward at the boundary and respond as one body; attribution still draws over the
    whole live set, which is second-order for the aggregate dynamics the probe measures.
    """
    cfg = d.cfg
    rng = np.random.default_rng(seed)
    txs = cfg.txs_per_block if txs_per_block is None else txs_per_block

    total = int(arrivals.sum())
    pop = Population.empty(total)
    seated = 0

    # ---- consensus state (MODEL.md section 2)
    endowment = d.endowment_genesis
    fee_bucket = 0
    claims_prev = 0
    floor_target = cfg.genesis_difficulty_target
    difficulty = floor_target

    fees_per_block = txs * cfg.avg_tx_fee
    diverted_per_block = fees_per_block * cfg.pow_share_num // cfg.pow_share_den

    rows: list[EpochRow] = []
    transition_epoch = NOT_SET

    for e in range(epochs):
        # ---- seat arrivals
        n = int(arrivals[e]) if e < len(arrivals) else 0
        if n:
            pop.hashrate[seated:seated + n] = hashrate_draw(n)
            pop.arrived[seated:seated + n] = e
            seated += n

        # ---- epoch boundary (MODEL.md section 3)
        # Price the epoch as bootstrap first; the dust fold then asks whether the endowment
        # can fund even one claim AT THAT PRICE. An anchor-scale threshold misses the
        # weak-interest tail, where the remainder-dump reward is thousands of LGO and a
        # room-locked residual of hundreds of LGO would hold the regime open forever.
        if endowment > 0:
            if e < d.bootstrap_epochs:
                sub_pool = endowment // (d.bootstrap_epochs - e)
            else:
                # Q7, the nominal-rate tail: past the deadline the schedule continues at the
                # planned per-epoch rate until the money is gone. The whole-remainder dump
                # this replaces handed 50M LGO to the first 1,300 claimants at 2.6%
                # conversion and stranded everyone after them at the anchor.
                sub_pool = min(endowment, d.endowment_genesis // d.bootstrap_epochs)
            budget = sub_pool + fee_bucket
            reward = max(d.anchor, budget // max(claims_prev, cfg.blocks_per_epoch))
            if endowment < reward:
                fee_bucket += endowment
                endowment = 0

        bootstrap = endowment > 0
        if not bootstrap and transition_epoch == NOT_SET:
            transition_epoch = e

        if not bootstrap:
            budget = fee_bucket
            reward = d.anchor
        fee_opening = fee_bucket

        # ---- the epoch, block by block (MODEL.md section 4)
        live = pop.live_mask(retire_on_bond)
        rate = float(pop.hashrate[live].sum())
        if participation is not None:
            rate *= float(np.clip(participation(reward, e), 0.0, 1.0))
        idx = np.flatnonzero(live)
        weights = pop.hashrate[idx]
        wsum = weights.sum()

        capacity = budget // reward if reward else 0
        target = max(1, capacity // cfg.blocks_per_epoch)

        spent = 0
        paid_total = 0
        endowment_drawn = 0
        saturation = NOT_SET
        won = np.zeros(idx.size, dtype=np.int64)
        fee_accrual = diverted_per_block * cfg.blocks_per_epoch

        if bootstrap:
            # The difficulty is a constant floor, so the whole epoch vectorises exactly:
            # admission is a running-total cutoff against what the pool can cover, and the
            # F-first draw order aggregates to a single min().
            mu = work.expected_claims(rate, difficulty, cfg) if rate > 0 else 0.0
            if deterministic:
                offered = np.full(cfg.blocks_per_epoch, int(round(mu)), dtype=np.int64)
            else:
                offered = rng.poisson(mu, cfg.blocks_per_epoch).astype(np.int64)
            np.minimum(offered, cfg.max_block_txs, out=offered)
            room = (fee_bucket + endowment) // reward if reward else 0
            cum = np.cumsum(offered)
            paid_per_block = np.minimum(offered,
                                        np.maximum(0, room - (cum - offered)))
            paid_total = int(paid_per_block.sum())
            max_block_claims = int(paid_per_block.max()) if paid_per_block.size else 0
            spent = paid_total * reward
            over = np.flatnonzero(np.cumsum(paid_per_block) * reward > budget)
            saturation = int(over[0]) if over.size else NOT_SET
            draw_f = min(spent, fee_bucket)
            fee_bucket -= draw_f
            endowment_drawn = spent - draw_f
            endowment -= endowment_drawn
            if paid_total and wsum > 0:
                won = rng.multinomial(paid_total, weights / wsum).astype(np.int64)
        else:
            # The throttle feeds back per block, so the loop is real -- but admission within
            # a block is batch arithmetic, not a per-claim loop.
            max_block_claims = 0
            for b in range(cfg.blocks_per_epoch):
                if rate > 0:
                    mu = work.expected_claims(rate, difficulty, cfg)
                    offered_b = int(round(mu)) if deterministic else int(rng.poisson(mu))
                else:
                    offered_b = 0
                offered_b = min(offered_b, cfg.max_block_txs)
                room = (budget - spent) // reward if reward else 0
                paid = min(offered_b, max(0, room))
                if paid:
                    max_block_claims = max(max_block_claims, paid)
                    take = paid * reward
                    draw_f = min(take, fee_bucket)
                    fee_bucket -= draw_f
                    spent += take
                    paid_total += paid
                if spent + reward > budget and saturation == NOT_SET:
                    saturation = b
                # Blocks past the saturation point carry no demand signal -- admission is
                # closed, not demand absent. Feeding their zero counts to the retarget eased
                # it to the 2^26 cap across every epoch tail, so each next epoch opened at
                # everyone-wins difficulty with a 1024-claim burst: a per-epoch limit cycle
                # that violated R7b at both epoch edges. The retarget updates only while the
                # budget still admits claims.
                if spent + reward <= budget:
                    difficulty = _retarget(difficulty, paid, target, cfg)
            # One multinomial for the epoch: sums of multinomials over the same weights ARE
            # the multinomial of the summed count, so per-block draws would buy nothing but
            # twenty-one thousand RNG calls.
            if paid_total and wsum > 0:
                won = rng.multinomial(paid_total, weights / wsum).astype(np.int64)

        # ---- settle balances and bonds
        bonds_before = int((pop.bonded_at != NOT_SET).sum())
        if paid_total:
            net = max(0, reward - cfg.claim_fee)
            pop.balance[idx] += won * net
            newly = (pop.bonded_at[idx] == NOT_SET) & (pop.balance[idx] >= cfg.min_stake)
            pop.bonded_at[idx[newly]] = e
        bonds_total = int((pop.bonded_at != NOT_SET).sum())

        rows.append(EpochRow(
            epoch=e, bootstrap=bootstrap, endowment=endowment,
            fee_bucket_opening=fee_opening, budget=budget, reward=reward,
            claims_paid=paid_total, spent=spent, saturation_block=saturation,
            max_block_claims=max_block_claims, bonds_total=bonds_total, bonds_new=bonds_total - bonds_before,
            miners_live=int(live.sum()), difficulty_target=difficulty,
            endowment_drawn=endowment_drawn))

        # boundary rollover: unspent F stays; the epoch's accrual joins it (MODEL.md section 3)
        fee_bucket = fee_bucket + fee_accrual
        claims_prev = paid_total

    return Result(rows=rows, pop=pop, transition_epoch=transition_epoch,
                  final_endowment=endowment, final_fee_bucket=fee_bucket,
                  total_diverted=diverted_per_block * cfg.blocks_per_epoch * epochs,
                  total_paid=sum(r.spent for r in rows), d=d)


def _retarget(difficulty: int, claims_in_block: int, target: int, cfg: Config) -> int:
    """The spec's EMA retarget against an arbitrary target -- the same arithmetic as
    `work.next_difficulty_target`, which hardcodes the config's constant target."""
    from empowering_sim.config import FIELD_MODULUS
    demand = max(1, (cfg.smoothing_precision - cfg.smoothing_factor) * claims_in_block
                 + cfg.smoothing_factor * target)
    stepped = (target * difficulty * cfg.smoothing_precision) // demand
    return min(stepped, FIELD_MODULUS - 1)
