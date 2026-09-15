"""How many nodes can the mechanism elevate into service provision?

A focused study. Two strategies only, both of which end up providing service, but by opposite
routes:

- **endowed providers** arrive already holding more than the bond, so they are elevated by
  their own capital as soon as the declaration lag clears;
- **mining providers** arrive with hardware and nothing else, and must earn the bond out of
  the proof-of-work pool.

Only the second is *elevated by the mechanism*. The first is counted because it decides
whether the thirty-two-provider floor is cleared while the second is still climbing.

**The ceiling, before any simulation.** The pool is the only source of a miner's first tokens,
and every elevation costs one bond:

| ``elevation_ceiling = genesis_pool / min_stake`` |
| --- |
| ``elevations_per_epoch = distribution_rate * pool / min_stake`` |

At the settled parameters that is 50,000 in total and 250 an epoch at genesis, falling as the
pool drains. The simulation's job is to find where reality falls short of that, and why.

New arrivals are seated every epoch, so the field grows and each miner's share of a fixed
claim flow shrinks. That is the effect the arithmetic above cannot see.

**Who arrives is an input, not a fixture.** By default the study seats the same number of
miners every epoch -- an arrival *budget*, with no variance and no adoption curve, which is
all that is needed to answer what the pool spends. Hand it ``miner_arrivals`` instead and it
seats whatever sequence it is given; `arrivals.py` builds Poisson ones, and the difference
between the two is the whole of the dynamic-arrivals study. This module stays the thing that
runs a chain and never becomes the thing that decides who turns up.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import arrivals, economics, emission, engine, services, work
from .config import Config

NOT_SET = -1


@dataclass
class ElevationConfig:
    """One run of the study."""

    endowed_per_epoch: float = 2.0        # arrive already above the bond
    miners_per_epoch: float = 50.0        # arrive with hardware only
    endowed_at_genesis: int = 100         # seeded so the floor is cleared from the start
    miners_at_genesis: int = 0
    epochs: int = 600

    endowed_stake_lgo: float = 5_000.0    # what an endowed arrival brings, above the bond
    hashrate_pareto_shape: float = 1.16
    pi5_rate: float = 0.0                 # floor of the hashrate draw; 0 -> derived from
                                          # the config's candidate cost (a whole board), so
                                          # the basis tracks the spec's 3-permutation
                                          # attempt instead of the stale 24,146 hardcode

    txs_per_block: int = 600
    seed: int = 40_001

    # A realised arrival sequence, one count per epoch, which overrides ``miners_per_epoch``
    # when supplied. A plain vector rather than a process object, for the reason in the module
    # docstring. ``None`` is the fixed study: the same number every epoch, remainder carried.
    miner_arrivals: np.ndarray | None = field(default=None, compare=False, repr=False)

    # Does a miner keep mining once it has crossed the bond? Rationally it should not: its
    # service income is orders of magnitude larger and its continued mining only takes claims
    # from miners still trying to cross. Nothing in the protocol makes it stop, so both are
    # modelled and the difference is the study's main lever.
    retire_on_bond: bool = False

    def miner_counts(self) -> np.ndarray:
        """Miners seated in each epoch: the supplied sequence, or the fixed rate carried."""
        if self.miner_arrivals is None:
            return arrivals.fixed_counts(self.miners_per_epoch, self.epochs)
        counts = np.asarray(self.miner_arrivals, dtype=np.int64)
        if counts.size < self.epochs:
            raise ValueError(f"miner_arrivals covers {counts.size} epochs and the run is "
                             f"{self.epochs}; a short sequence would silently seat nobody "
                             f"for the rest of the run")
        return counts[:self.epochs]

    def total_miners(self) -> int:
        if self.miner_arrivals is not None:
            return self.miners_at_genesis + int(self.miner_counts().sum())
        return self.miners_at_genesis + int(np.ceil(self.miners_per_epoch * self.epochs))

    def total_endowed(self) -> int:
        return self.endowed_at_genesis + int(np.ceil(self.endowed_per_epoch * self.epochs))


@dataclass
class ElevationRow:
    epoch: int
    years: float
    miners_seated: int
    miners_elevated: int
    endowed_seated: int
    providers: int
    service_active: bool
    reward_per_claim: int
    pool_lgo: float
    difficulty_target: int
    hashrate: float
    claims_paid: int
    elevated_this_epoch: int
    service_per_provider_lgo: float


@dataclass
class ElevationResult:
    rows: list[ElevationRow]
    bond_epoch: np.ndarray        # per miner: epoch it crossed the bond, or NOT_SET
    seated_epoch: np.ndarray      # per miner: epoch it arrived
    balance: np.ndarray           # per miner, base units
    hashrate: np.ndarray
    cfg: Config = field(repr=False, default=None)

    @property
    def elevated(self) -> int:
        return int((self.bond_epoch != NOT_SET).sum())

    def time_to_elevate(self) -> np.ndarray:
        got = self.bond_epoch != NOT_SET
        return (self.bond_epoch[got] - self.seated_epoch[got]).astype(np.int64)


def ceiling(cfg: Config) -> dict:
    """What the arithmetic allows, before the field's growth is taken into account."""
    per_epoch = cfg.distribution_rate * cfg.genesis_pool / cfg.min_stake
    refill = economics.epoch_refill(cfg) / cfg.min_stake
    return dict(
        total=cfg.genesis_pool / cfg.min_stake,
        per_epoch_at_genesis=per_epoch,
        fee_funded_per_epoch=refill,
        epochs_to_exhaust=cfg.genesis_pool / cfg.min_stake / per_epoch,
    )


def run(cfg: Config, ecfg: ElevationConfig) -> ElevationResult:
    """Seat arrivals every epoch and count who reaches the bond."""
    rng = np.random.default_rng(ecfg.seed)

    n_m, n_e = ecfg.total_miners(), ecfg.total_endowed()
    floor = ecfg.pi5_rate or (cfg.reference_cores / cfg.seconds_per_candidate_reward)
    hashrate = floor * (1.0 + rng.pareto(ecfg.hashrate_pareto_shape, size=max(1, n_m)))
    m_balance = np.zeros(n_m, dtype=np.int64)
    m_seated = np.full(n_m, NOT_SET, dtype=np.int32)
    m_bond = np.full(n_m, NOT_SET, dtype=np.int32)
    m_declared = np.full(n_m, NOT_SET, dtype=np.int32)
    e_seated = np.full(n_e, NOT_SET, dtype=np.int32)
    endowed_units = round(ecfg.endowed_stake_lgo * cfg.base_units_per_lgo)

    m_count, e_count = ecfg.miners_at_genesis, ecfg.endowed_at_genesis
    m_seated[:m_count] = 0
    e_seated[:e_count] = 0

    state = engine.genesis_state(cfg)
    est = emission.StakeEstimate.at_genesis(cfg)
    slots_per_epoch = 648_000            # 21,600 blocks at f = 1/30, as in strategies.py
    fees = ecfg.txs_per_block * cfg.avg_tx_fee
    # The carve-out convention lives in `emission.pooled_inflow_lgo` -- fees pool in full and
    # the EmPoWering share is the first outflow, so the window carries what remains.
    pooled_window = [emission.pooled_inflow_lgo(cfg, ecfg.txs_per_block)] * emission.POOL_WINDOW

    rows: list[ElevationRow] = []
    seat_m = ecfg.miner_counts()
    seat_e = arrivals.fixed_counts(ecfg.endowed_per_epoch, ecfg.epochs)
    for e in range(ecfg.epochs):
        if seat_m[e]:
            hi = min(n_m, m_count + int(seat_m[e]))
            m_seated[m_count:hi] = e
            m_count = hi
        if seat_e[e]:
            hi = min(n_e, e_count + int(seat_e[e]))
            e_seated[e_count:hi] = e
            e_count = hi

        reward = economics.reward_per_claim(state.pool, cfg)
        net = max(0, reward - cfg.claim_fee)

        # --- the chain: claims flow at the target rate whatever the field size
        live = m_seated[:m_count] >= 0
        if ecfg.retire_on_bond:
            live &= m_bond[:m_count] == NOT_SET
        rate = float(hashrate[:m_count][live].sum()) if live.any() else 0.0
        target, pool, paid = state.difficulty_target, state.pool, 0
        for _ in range(cfg.blocks_per_epoch):
            n = int(rng.poisson(work.expected_claims(rate, target, cfg))) if rate > 0 else 0
            inc = min(n, cfg.max_block_txs)
            pool, settled = economics.pay_claims(pool, reward, inc)
            paid += settled
            target = work.next_difficulty_target(target, inc, cfg)
        pool += economics.epoch_refill(cfg, ecfg.txs_per_block)
        state = engine.State(pool=pool, difficulty_target=target)

        # --- attribute claims and record who crosses the bond
        elevated_now = 0
        if paid and rate > 0:
            idx = np.flatnonzero(live)
            w = hashrate[:m_count][live]
            won = rng.multinomial(paid, w / w.sum())
            m_balance[idx] += won * net
            newly = (m_bond[idx] == NOT_SET) & (m_balance[idx] >= cfg.min_stake)
            m_bond[idx[newly]] = e
            m_declared[idx[newly]] = e
            elevated_now = int(newly.sum())

        # --- providers: endowed are bonded on arrival, miners once they have crossed
        e_live = int(((e_seated >= 0) & (e_seated + services.DECLARATION_LAG_EPOCHS <= e)).sum())
        m_live = int(((m_declared >= 0)
                      & (m_declared + services.DECLARATION_LAG_EPOCHS <= e)).sum())
        providers = e_live + m_live

        # The estimator corrects on the shortfall between the blocks the lottery yields at
        # its current estimate and the epoch's expectation -- feeding it the expectation
        # itself (a previous revision did) pins it at the 1e10 genesis seed forever, holds the
        # emission factor at zero, and understates service income by four orders of magnitude.
        # The study's staked value is what its participants have locked: the endowed arrivals'
        # stake and one bond per elevated miner.
        true_staked_lgo = (e_count * ecfg.endowed_stake_lgo
                           + int((m_bond != NOT_SET).sum()) * cfg.min_stake_lgo)
        blocks = est.blocks_produced(true_staked_lgo, cfg, slots_per_epoch)

        blk = emission.block_reward_lgo(est.value_lgo, pooled_window)
        blend, _ = emission.split(blk, cfg)
        per_prov = services.reward_per_provider(blend * blocks, providers)

        rows.append(ElevationRow(
            epoch=e, years=e / cfg.epochs_per_year,
            miners_seated=m_count, miners_elevated=int((m_bond != NOT_SET).sum()),
            endowed_seated=e_count, providers=providers,
            service_active=services.service_active(providers),
            reward_per_claim=reward, pool_lgo=cfg.to_lgo(state.pool),
            difficulty_target=state.difficulty_target, hashrate=rate,
            claims_paid=paid,
            elevated_this_epoch=elevated_now, service_per_provider_lgo=per_prov,
        ))
        est = est.update(blocks, cfg)

    return ElevationResult(rows=rows, bond_epoch=m_bond[:m_count],
                           seated_epoch=m_seated[:m_count], balance=m_balance[:m_count],
                           hashrate=hashrate[:m_count], cfg=cfg)
