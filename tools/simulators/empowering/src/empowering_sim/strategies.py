"""Five participation strategies, simulated together on one honest chain.

The question is which strategy pays. Every group runs at the same time against the same chain,
so they compete for the same claim flow, the same lottery and the same service pool -- which is
the point: a strategy's return depends on who else is playing.

**Paired draws.** One Pareto hashrate vector is shared by every mining group and one Pareto
stake vector by every stakeholder group, keyed to their own seeds rather than to the set of
enabled groups. So switching a group off does not perturb the others, and a difference between
two groups is a difference in strategy rather than in luck.

**What is deliberately absent:** Blend's network, propagation delay, forks, churn, adversaries.
Every node behaves honestly and stays for the whole run.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

import numpy as np

from . import consensus, economics, emission, engine, services, work
from .config import Config

NOT_SET = -1


class Strategy(IntEnum):
    MINER = 0                 # mines; does not stake
    MINER_STAKER = 1          # mines; stakes what it mines
    MINER_STAKER_SERVICE = 2  # mines; stakes; provides service once bonded
    STAKER = 3                # initial stake; lottery only
    STAKER_SERVICE = 4        # initial stake; lottery and service


LABELS = {
    Strategy.MINER: "miner",
    Strategy.MINER_STAKER: "miner+staker",
    Strategy.MINER_STAKER_SERVICE: "miner+staker+service",
    Strategy.STAKER: "staker",
    Strategy.STAKER_SERVICE: "staker+service",
}

MINING = (Strategy.MINER, Strategy.MINER_STAKER, Strategy.MINER_STAKER_SERVICE)
STAKING = (Strategy.MINER_STAKER, Strategy.MINER_STAKER_SERVICE,
           Strategy.STAKER, Strategy.STAKER_SERVICE)
SERVING = (Strategy.MINER_STAKER_SERVICE, Strategy.STAKER_SERVICE)
ENDOWED = (Strategy.STAKER, Strategy.STAKER_SERVICE)


@dataclass
class StrategyConfig:
    """Group sizes, distributions and the study's own settings."""

    nodes_per_group: dict[Strategy, int] = field(
        default_factory=lambda: {s: 100 for s in Strategy})
    enabled: dict[Strategy, bool] = field(
        default_factory=lambda: {s: True for s in Strategy})

    # Each stakeholder group is endowed with this share of launch supply, and the SAME
    # per-node vector is used by every such group.
    tge_stake_share: float = 0.05
    stake_pareto_shape: float = 1.16       # tail index; lower is more concentrated
    hashrate_pareto_shape: float = 1.16

    epochs: int = 120
    txs_per_block: int = 600
    seed_stake: int = 20_001
    seed_hashrate: int = 20_002
    seed_chain: int = 20_003
    slots_per_epoch: int = 648_000   # 21,600 blocks at f = 1/30

    def active(self) -> list[Strategy]:
        return [s for s in Strategy if self.enabled.get(s, False)
                and self.nodes_per_group.get(s, 0) > 0]


@dataclass
class Population:
    """Every node in the study, flat. Rewards are tracked by source, never merged."""

    strategy: np.ndarray          # int8
    hashrate: np.ndarray          # float64, candidates per second; zero for non-miners
    stake: np.ndarray             # int64, base units currently held
    initial_stake: np.ndarray     # int64, what it was endowed with
    stake_aged_at: np.ndarray     # int32, epoch its holdings first become lottery-eligible
    declared_at: np.ndarray       # int32, epoch it declared a service, NOT_SET otherwise
    reward_pow: np.ndarray        # int64, base units, net of the fees paid to claim
    reward_leader: np.ndarray
    reward_service: np.ndarray
    claims: np.ndarray            # int64
    blocks_led: np.ndarray        # int64

    @property
    def n(self) -> int:
        return self.strategy.size

    def total_reward(self) -> np.ndarray:
        return self.reward_pow + self.reward_leader + self.reward_service

    def mask(self, *strategies: Strategy) -> np.ndarray:
        return np.isin(self.strategy, [int(s) for s in strategies])

    def aged_stake(self, epoch: int) -> np.ndarray:
        """Holdings that have aged into the lottery. Any value counts; there is no minimum.

        Aging is tracked per NODE rather than per note, so an increment credited to a node
        that is already aged counts immediately rather than two epochs later. That is a
        two-epoch optimism on income which is itself a small share of a holding, and it is
        immaterial over the horizons this is run at -- but it is an approximation, not the
        protocol.
        """
        eligible = (self.stake_aged_at >= 0) & (self.stake_aged_at <= epoch)
        return np.where(eligible & self.mask(*STAKING), self.stake, 0)


def _pareto(rng: np.random.Generator, n: int, shape: float, minimum: float) -> np.ndarray:
    """Pareto draw with a stated minimum. ``shape`` is the tail index: lower is heavier."""
    return minimum * (1.0 + rng.pareto(shape, size=n))


def build_population(cfg: Config, scfg: StrategyConfig,
                     pi5_candidates_per_second: float = 24_146.0) -> Population:
    """Seat every enabled group, with the shared vectors drawn once and reused.

    The hashrate minimum is a Raspberry Pi 5's measured rate -- four cores at the measured
    165.658 microseconds per candidate -- because the design targets that board and a
    distribution that can fall below it would model machines the on-ramp is not for.
    """
    active = scfg.active()
    biggest_mining = max((scfg.nodes_per_group[s] for s in active if s in MINING), default=0)
    biggest_staking = max((scfg.nodes_per_group[s] for s in active if s in ENDOWED), default=0)

    # Drawn from their own seeds, so enabling or disabling a group cannot move them.
    rng_h = np.random.default_rng(scfg.seed_hashrate)
    rng_s = np.random.default_rng(scfg.seed_stake)
    shared_hashrate = (_pareto(rng_h, biggest_mining, scfg.hashrate_pareto_shape,
                               pi5_candidates_per_second) if biggest_mining else np.array([]))
    if biggest_staking:
        raw = _pareto(rng_s, biggest_staking, scfg.stake_pareto_shape, 1.0)
        target = scfg.tge_stake_share * cfg.launch_supply * cfg.base_units_per_lgo
        shared_stake = np.round(raw / raw.sum() * target).astype(np.int64)
    else:
        shared_stake = np.array([], dtype=np.int64)

    strat, hashr, stake, aged, declared = [], [], [], [], []
    for s in active:
        k = scfg.nodes_per_group[s]
        strat.append(np.full(k, int(s), dtype=np.int8))
        hashr.append(shared_hashrate[:k] if s in MINING else np.zeros(k))
        if s in ENDOWED:
            stake.append(shared_stake[:k])
            # Genesis notes are in the genesis ledger root, so they are lottery-eligible
            # from the first epoch; only mined notes have to age.
            aged.append(np.zeros(k, dtype=np.int32))
        else:
            stake.append(np.zeros(k, dtype=np.int64))
            aged.append(np.full(k, NOT_SET, dtype=np.int32))
        declared.append(np.full(k, NOT_SET, dtype=np.int32))

    n = sum(scfg.nodes_per_group[s] for s in active)
    z = lambda: np.zeros(n, dtype=np.int64)          # noqa: E731
    return Population(
        strategy=np.concatenate(strat) if strat else np.array([], dtype=np.int8),
        hashrate=np.concatenate(hashr) if hashr else np.array([]),
        stake=np.concatenate(stake) if stake else np.array([], dtype=np.int64),
        initial_stake=(np.concatenate(stake) if stake else np.array([], dtype=np.int64)).copy(),
        stake_aged_at=np.concatenate(aged) if aged else np.array([], dtype=np.int32),
        declared_at=np.concatenate(declared) if declared else np.array([], dtype=np.int32),
        reward_pow=z(), reward_leader=z(), reward_service=z(),
        claims=z(), blocks_led=z(),
    )


@dataclass
class EpochRecord:
    epoch: int
    years: float
    stake_estimate_lgo: float
    true_staked_lgo: float
    emission_factor: float
    block_reward_lgo: float
    blocks_produced: int
    blend_pool_lgo: float
    leader_pool_lgo: float
    providers: int
    service_per_provider_lgo: float
    claims_paid: int
    reward_per_claim: int
    pool_lgo: float
    pow_reward_per_block: np.ndarray = field(default=None, repr=False)


def run(cfg: Config, scfg: StrategyConfig) -> tuple[Population, list[EpochRecord]]:
    """Advance the chain, paying all four streams, and record what each node accumulates."""
    pop = build_population(cfg, scfg)
    rng = np.random.default_rng(scfg.seed_chain)
    state = engine.genesis_state(cfg)
    est = emission.StakeEstimate.at_genesis(cfg)

    fees_per_block = scfg.txs_per_block * cfg.avg_tx_fee
    diverted = fees_per_block * cfg.pow_share_num // cfg.pow_share_den
    burnt_per_block_lgo = cfg.to_lgo(fees_per_block - diverted)
    burn_window = [burnt_per_block_lgo] * emission.BURN_WINDOW

    out: list[EpochRecord] = []
    for e in range(scfg.epochs):
        reward_per_claim = economics.reward_per_claim(state.pool, cfg)
        net_per_claim = max(0, reward_per_claim - cfg.claim_fee)

        aged = pop.aged_stake(e)
        true_staked_lgo = cfg.to_lgo(float(aged.sum()))
        blocks = est.blocks_produced(true_staked_lgo, cfg, scfg.slots_per_epoch)

        a_t = emission.emission_factor(est.value_lgo, burn_window)
        blk_lgo = emission.block_reward_lgo(est.value_lgo, burn_window)
        blend_per_block, leader_per_block = emission.split(blk_lgo, cfg)
        blend_pool = blend_per_block * blocks
        leader_pool = leader_per_block * blocks

        # ---- proof of work: the claim flow, block by block, with the retarget in the loop
        hashrate = float(pop.hashrate[pop.mask(*MINING)].sum())
        # int64, not int32: a block's reward is the claim count times a reward of order
        # 10^9 base units, which overflows a 32-bit accumulator at ten claims and wraps
        # NEGATIVE. The histograms rendered symmetric about zero, which is what caught it.
        claims_found = np.zeros(cfg.blocks_per_epoch, dtype=np.int64)
        target = state.difficulty_target
        pool, paid = state.pool, 0
        for b in range(cfg.blocks_per_epoch):
            n = int(rng.poisson(work.expected_claims(hashrate, target, cfg)))
            included = min(n, cfg.max_block_txs)
            pool, settled = economics.pay_claims(pool, reward_per_claim, included)
            claims_found[b] = settled
            paid += settled
            target = work.next_difficulty_target(target, included, cfg)
        pool += economics.epoch_refill(cfg, scfg.txs_per_block)
        state = engine.State(pool=pool, difficulty_target=target)

        # ---- attribute the three streams
        miners = pop.mask(*MINING)
        if paid and pop.hashrate[miners].sum() > 0:
            w = pop.hashrate[miners] / pop.hashrate[miners].sum()
            won = rng.multinomial(paid, w)
            idx = np.flatnonzero(miners)
            pop.claims[idx] += won
            pop.reward_pow[idx] += won * net_per_claim
            newly = (pop.stake_aged_at[idx] == NOT_SET) & (won > 0)
            pop.stake_aged_at[idx[newly]] = e + cfg.stake_aging_epochs
            stakers = np.isin(pop.strategy[idx], [int(s) for s in STAKING])
            pop.stake[idx[stakers]] += (won * net_per_claim)[stakers]

        if aged.sum() > 0 and blocks > 0:
            led = rng.multinomial(blocks, aged / aged.sum())
            pop.blocks_led += led
            per_block = leader_pool / blocks
            paid_lead = np.round(led * per_block * cfg.base_units_per_lgo).astype(np.int64)
            pop.reward_leader += paid_lead
            # Leader income is tokens the node now holds, so it compounds into its stake and
            # thence into its future lottery weight. Omitting this understates the long run
            # badly: minted rewards are what drive total stake toward the 30% target, and
            # reaching that target is what switches the emission off.
            pop.stake[pop.mask(*STAKING)] += paid_lead[pop.mask(*STAKING)]

        # ---- services: declare when bonded, then a flat share of the Blend pool
        wants = pop.mask(*SERVING)
        can = wants & (pop.stake >= cfg.min_stake) & (pop.declared_at == NOT_SET)
        pop.declared_at[can] = e
        providing = services.eligible(pop.stake, cfg.min_stake, pop.declared_at, e) & wants
        n_prov = int(providing.sum())
        per_prov = services.reward_per_provider(blend_pool, n_prov)
        if per_prov > 0:
            paid_svc = round(per_prov * cfg.base_units_per_lgo)
            pop.reward_service[providing] += paid_svc
            pop.stake[providing & pop.mask(*STAKING)] += paid_svc

        out.append(EpochRecord(
            epoch=e, years=e / cfg.epochs_per_year,
            stake_estimate_lgo=est.value_lgo, true_staked_lgo=true_staked_lgo,
            emission_factor=a_t, block_reward_lgo=blk_lgo, blocks_produced=blocks,
            blend_pool_lgo=blend_pool, leader_pool_lgo=leader_pool,
            providers=n_prov, service_per_provider_lgo=per_prov,
            claims_paid=paid, reward_per_claim=reward_per_claim,
            pool_lgo=cfg.to_lgo(state.pool),
            pow_reward_per_block=claims_found * np.int64(reward_per_claim),
        ))
        est = est.update(blocks, cfg)

    return pop, out


def summarise(cfg: Config, pop: Population, scfg: StrategyConfig) -> list[dict]:
    """Per-strategy totals, and the normalisations that make them comparable.

    Raw accumulated reward answers "who was endowed more at genesis", so the increment over
    the plain-stakeholder baseline is reported beside it.
    """
    rows = []
    for s in scfg.active():
        m = pop.mask(s)
        if not m.any():
            continue
        total = pop.total_reward()[m]
        rows.append(dict(
            strategy=LABELS[s], nodes=int(m.sum()),
            initial_stake_lgo=cfg.to_lgo(float(pop.initial_stake[m].sum())),
            reward_pow_lgo=cfg.to_lgo(float(pop.reward_pow[m].sum())),
            reward_leader_lgo=cfg.to_lgo(float(pop.reward_leader[m].sum())),
            reward_service_lgo=cfg.to_lgo(float(pop.reward_service[m].sum())),
            total_lgo=cfg.to_lgo(float(total.sum())),
            median_node_lgo=cfg.to_lgo(float(np.median(total))),
            claims=int(pop.claims[m].sum()), blocks_led=int(pop.blocks_led[m].sum()),
        ))
    return rows
