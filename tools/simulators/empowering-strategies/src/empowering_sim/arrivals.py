"""Who turns up, when, and what the timing decides.

The elevation study of `elevation.py` seats a fixed number of miners every epoch. That is an
arrival **budget**, not an arrival **process**: it has no variance, no waves and no notion of
adoption, so every run of it is the same run and every cohort is the same cohort. It answers
what the pool *spends*. It cannot answer how fast the mechanism *absorbs* people, because
absorption is a rate against a rate, and a rate that never moves has nothing to be measured
against.

This module supplies the process. Arrivals in an epoch are Poisson with a mean this module
shapes over the horizon:

| ``arrivals(epoch) ~ Poisson(amplitude * profile(epoch))`` |
| --- |

Poisson is the right law here rather than a convenient one. Joiners decide independently and
each one's chance of deciding in any particular epoch is small, which is exactly the limit a
Poisson count describes; it is also the same law the claim process already obeys, one level
down (`work.py`). The amplitude is the knob: it is the mean number of new miners an epoch,
and it is the only thing about arrivals a designer can plausibly have an opinion on.

**Every shape is normalised to the same horizon total**, so a comparison across shapes holds
the population fixed and varies only *when* it turns up. That is the point of having shapes:
the pool's price per claim decays geometrically, so arriving early is worth more than arriving
in numbers, and only a matched-volume comparison can separate the two.

The measures at the bottom are the study's outputs. Two of them are clocks and they must not
be confused:

- the **drain clock** -- when the pool empties -- is a property of `distribution_rate` alone
  and no arrival process touches it (`elevation.py`, and section 1.3 of the report);
- the **saturation clock** -- when arrivals start outrunning elevations -- is set by the
  amplitude and by nothing else.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .config import Config

FLAT = "flat"
WAVE = "wave"
BURST = "burst"
RAMP = "ramp"
SHAPES = (FLAT, WAVE, BURST, RAMP)

# `elevation.NOT_SET`, restated rather than imported: importing elevation here would close a
# cycle, since elevation takes its arrival counts from this module.
NOT_SET_SENTINEL = -1


@dataclass(frozen=True)
class Arrivals:
    """A Poisson arrival process for miners, with a mean that may move over the horizon.

    ``amplitude`` is the mean arrivals per epoch averaged over the whole run; every shape is
    renormalised to hold that, so two shapes at one amplitude seat the same expected number of
    miners in total and differ only in when.
    """

    amplitude: float = 50.0
    shape: str = FLAT
    stochastic: bool = True

    # -- shape parameters. Defaults chosen to be legible rather than fitted to anything:
    # a wave of about a year, a burst inside the first year, a ramp maturing at four.
    wave_period: float = 48.0             # epochs; roughly a year at 7.5-day epochs
    wave_depth: float = 0.9               # 0 is flat, 1 touches zero at the trough
    burst_centre: float = 0.15            # as a fraction of the horizon
    burst_width: float = 0.05             # standard deviation, same units
    ramp_epochs: float = 200.0            # logistic midpoint, in epochs

    def __post_init__(self) -> None:
        if self.shape not in SHAPES:
            raise ValueError(f"unknown arrival shape {self.shape!r}; have {list(SHAPES)}")
        if self.amplitude < 0:
            raise ValueError("amplitude is a mean count and cannot be negative")
        if not 0.0 <= self.wave_depth <= 1.0:
            raise ValueError("wave_depth runs from 0 (flat) to 1 (touching zero)")

    @property
    def label(self) -> str:
        return f"{self.shape}@{self.amplitude:g}"

    # ------------------------------------------------------------------ the mean

    def profile(self, epochs: int) -> np.ndarray:
        """Mean arrivals per epoch, of length ``epochs``.

        Normalised so the mean over the horizon is exactly ``amplitude`` whatever the shape.
        A shape is therefore a redistribution of one fixed population over time and never a
        change of population size -- without that, every shape comparison would confound
        timing with volume.
        """
        e = np.arange(epochs, dtype=float)
        if self.shape == FLAT:
            w = np.ones(epochs)
        elif self.shape == WAVE:
            w = 1.0 + self.wave_depth * np.sin(2 * np.pi * e / max(1e-9, self.wave_period))
        elif self.shape == BURST:
            c, s = self.burst_centre * epochs, max(1e-9, self.burst_width * epochs)
            w = np.exp(-0.5 * ((e - c) / s) ** 2)
        elif self.shape == RAMP:
            # Logistic adoption: the same S-curve `scenarios.logistic_ramp` uses for traffic,
            # so a growth story here and one there are the same story.
            w = 1.0 / (1.0 + np.exp(-12.0 * (e - self.ramp_epochs) / max(1e-9, self.ramp_epochs)))
        total = float(w.sum())
        if total <= 0:
            raise ValueError(f"shape {self.shape!r} has no mass over {epochs} epochs")
        return self.amplitude * epochs * w / total

    # ------------------------------------------------------------------ one realisation

    def draw(self, rng: np.random.Generator, epochs: int) -> np.ndarray:
        """One realisation: the miners actually seated in each epoch.

        With ``stochastic`` off this is the mean rounded by the same fractional carry the
        fixed study uses, which makes the process's own contribution -- the variance -- the
        only difference between the two, rather than the variance plus a rounding rule.
        """
        lam = self.profile(epochs)
        if self.stochastic:
            return rng.poisson(lam).astype(np.int64)
        return carry_counts(lam)


def carry_counts(rate) -> np.ndarray:
    """Turn a fractional per-epoch rate into whole arrivals, carrying the remainder.

    Accepts a scalar rate or a per-epoch vector. This is the rule `elevation.run` has always
    used for its fixed arrivals, lifted out so the deterministic and the stochastic paths seat
    people the same way.
    """
    lam = np.asarray(rate, dtype=float)
    out = np.empty(lam.size, dtype=np.int64)
    owed = 0.0
    for i in range(lam.size):
        owed += float(lam[i])
        take = int(owed)
        owed -= take
        out[i] = take
    return out


def fixed_counts(rate: float, epochs: int) -> np.ndarray:
    """The fixed study's arrivals: ``rate`` an epoch, remainder carried."""
    return carry_counts(np.full(epochs, float(rate)))


# ------------------------------------------------------------------ what the pool can fund

def capacity_bonds(pool_lgo: float, cfg: Config) -> float:
    """Bonds an epoch's payout could fund if every lepton of it landed on a miner at the bond.

    | ``capacity_bonds = distribution_rate * pool / min_stake`` |

    The ceiling on elevation in one epoch, and a generous one: it assumes no claim is paid to
    a miner that is already bonded and none lands in a balance that never reaches the bond.
    Section 6 measures the real conversion at 11.4% of it, or 51.9% if bonded miners retire.
    """
    return cfg.distribution_rate * pool_lgo / cfg.min_stake_lgo


def saturation_epoch_closed_form(amplitude: float, cfg: Config,
                                 conversion: float = 1.0) -> float:
    """When the pool's capacity falls below the arrival rate, before any simulation.

    | ``saturation_epoch = log(conversion * capacity_at_genesis / amplitude) / log(1 / (1 - distribution_rate))`` |

    The pool decays geometrically at `distribution_rate`, so its capacity does too, and it
    crosses any fixed arrival rate exactly once. At ``conversion = 1`` this is the arithmetic
    bound; passing the measured conversion of section 6 gives the bound a run should be near.
    Returns 0 when the rate is already past capacity at genesis, and infinity when the pool
    never falls to it -- which cannot happen for a positive amplitude, but says so rather than
    dividing by zero.
    """
    genesis = capacity_bonds(cfg.to_lgo(cfg.genesis_pool), cfg) * conversion
    if amplitude <= 0:
        return math.inf
    if amplitude >= genesis:
        return 0.0
    return math.log(genesis / amplitude) / math.log(1.0 / (1.0 - cfg.distribution_rate))


# ------------------------------------------------------------------ reading a run

# Cohorts inside this many epochs of the horizon are not asked whether they were absorbed.
# A miner seated at epoch 590 of 600 has not failed to reach the bond, it has not had the
# chance to; counting it as a failure would let the horizon manufacture the result.
RUNWAY_EPOCHS = 120


def _smooth(x: np.ndarray, window: int) -> np.ndarray:
    """Centred moving average, edges held rather than tapered."""
    if window <= 1:
        return np.asarray(x, dtype=float)
    x = np.asarray(x, dtype=float)
    pad = window // 2
    padded = np.concatenate([np.full(pad, x[0]), x, np.full(window - 1 - pad, x[-1])])
    return np.convolve(padded, np.ones(window) / window, mode="valid")


def arrivals_per_epoch(result, epochs: int) -> np.ndarray:
    """Miners seated in each epoch, counted from the per-miner record.

    Taken from ``seated_epoch`` rather than by differencing the cumulative count, which cannot
    recover the first epoch: the row carries a total, and epoch 0's total is its own arrivals
    plus whatever was seated at genesis.
    """
    s = result.seated_epoch
    return np.bincount(s[s >= 0], minlength=epochs)[:epochs].astype(np.int64)


def by_cohort(result, epochs: int) -> tuple[np.ndarray, np.ndarray]:
    """Per arrival cohort: the share that ever reached the bond, and the median wait to it.

    A queue is read by when you joined it, and this is that reading. Cohorts with nobody
    elevated carry ``nan`` for the wait rather than a large number, because an infinite wait
    is not a slow one and averaging it as though it were would flatter the mechanism.
    """
    share, wait = np.zeros(epochs), np.full(epochs, np.nan)
    for e in range(epochs):
        seated = result.seated_epoch == e
        if not seated.any():
            continue
        got = seated & (result.bond_epoch != NOT_SET_SENTINEL)
        share[e] = got.sum() / seated.sum()
        if got.any():
            wait[e] = float(np.median(result.bond_epoch[got] - e))
    return share, wait


@dataclass
class Absorption:
    """What one run absorbed, when it stopped keeping up, and when it stopped being possible.

    Three different questions, deliberately kept apart:

    - ``keeps_up_until`` is a **rate** answer -- the last epoch at which elevations still came
      as fast as arrivals. It is ``None`` when the mechanism was behind from the first epoch.
    - ``door_epoch`` is an **odds** answer -- the last cohort more likely than not to reach the
      bond eventually. It is what a prospective joiner would want to know.
    - ``no_return_epoch`` is an **arithmetic** answer and carries no behavioural assumption:
      the first epoch at which the miners already waiting outnumber every bond the remaining
      pool could ever fund. Past it the queue cannot be cleared by any conversion, any
      retirement rule, or any amount of further mining.
    """

    amplitude: float
    seated: int
    elevated: int
    settled_seated: int                   # cohorts with a full runway ahead of them
    settled_elevated: int
    keeps_up_until: int | None
    door_epoch: int | None
    no_return_epoch: int | None
    median_wait: float                    # epochs from seating to the bond, elevated only

    @property
    def absorbed(self) -> float:
        """Share of the arrivals that reached the bond, over cohorts that had the runway."""
        return self.settled_elevated / self.settled_seated if self.settled_seated else 0.0


def absorption(result, cfg: Config, window: int = 9,
               runway: int = RUNWAY_EPOCHS) -> Absorption:
    """Measure one run of the dynamic study.

    ``keeps_up_until`` takes the **last** crossing rather than the first: the opening epochs
    are a transient in which nobody has had time to reach the bond, so the elevation rate
    starts at zero and crosses the arrival rate from below before it decays back through it
    for good. The first crossing would time the transient; the last one times the mechanism.
    """
    epochs = len(result.rows)
    seated = np.array([r.miners_seated for r in result.rows], dtype=np.int64)
    elevated = np.array([r.miners_elevated for r in result.rows], dtype=np.int64)
    per_in = arrivals_per_epoch(result, epochs)
    per_up = np.array([r.elevated_this_epoch for r in result.rows], dtype=np.int64)

    keeping = np.flatnonzero(_smooth(per_up, window) >= _smooth(per_in, window))
    share, _ = by_cohort(result, epochs)
    settled = max(1, epochs - runway)
    odds = _smooth(share[:settled], 15)
    open_door = np.flatnonzero(odds >= 0.5)

    backlog = seated - elevated
    pool = np.array([r.pool_lgo for r in result.rows], dtype=float)
    beyond = np.flatnonzero(backlog > pool / cfg.min_stake_lgo)

    in_time = (result.seated_epoch >= 0) & (result.seated_epoch < settled)
    waits = result.time_to_elevate()
    return Absorption(
        amplitude=float(per_in.mean()),
        seated=int(seated[-1]), elevated=int(elevated[-1]),
        settled_seated=int(in_time.sum()),
        settled_elevated=int((in_time & (result.bond_epoch != NOT_SET_SENTINEL)).sum()),
        keeps_up_until=int(keeping[-1]) if keeping.size else None,
        door_epoch=int(open_door[-1]) if open_door.size else None,
        no_return_epoch=int(beyond[0]) if beyond.size else None,
        median_wait=float(np.median(waits)) if waits.size else float("nan"),
    )


# ------------------------------------------------------------------ one run of the study

@dataclass
class DynamicRun:
    """One realisation, with the per-epoch series the figures read."""

    arrivals: Arrivals
    seed: int
    retire: bool
    epochs: int
    per_epoch_in: np.ndarray
    per_epoch_up: np.ndarray
    pool_pct: np.ndarray                  # remaining, as a percentage of the genesis pool
    capacity: np.ndarray                  # bonds the epoch's payout could fund
    providers: np.ndarray
    service_lgo: np.ndarray               # per provider, per epoch
    cohort_share: np.ndarray
    cohort_wait: np.ndarray
    absorption: Absorption

    @property
    def label(self) -> str:
        return self.arrivals.label


def run_dynamic(cfg: Config, process: Arrivals, *, epochs: int = 600, seed: int = 40_001,
                retire: bool = False, endowed_per_epoch: float = 2.0,
                endowed_at_genesis: int = 100) -> DynamicRun:
    """Seat Poisson arrivals against the elevation engine and measure what it absorbed.

    The arrival draw takes its own generator stream, seeded from ``seed`` but separate from
    the chain's, so two runs at the same seed differ in exactly one thing when the amplitude
    changes: who turned up. The endowed cohort keeps the fixed study's settings -- it is here
    to hold the thirty-two-provider floor while the miners climb (section 5), not as a study
    axis.
    """
    from . import elevation as el                             # noqa: PLC0415  (cycle)

    counts = process.draw(np.random.default_rng([seed, 1]), epochs)
    result = el.run(cfg, el.ElevationConfig(
        epochs=epochs, seed=seed, miner_arrivals=counts, retire_on_bond=retire,
        endowed_per_epoch=endowed_per_epoch, endowed_at_genesis=endowed_at_genesis))
    share, wait = by_cohort(result, epochs)
    pool = np.array([r.pool_lgo for r in result.rows], dtype=float)
    return DynamicRun(
        arrivals=process, seed=seed, retire=retire, epochs=epochs,
        per_epoch_in=arrivals_per_epoch(result, epochs),
        per_epoch_up=np.array([r.elevated_this_epoch for r in result.rows], dtype=np.int64),
        pool_pct=pool / cfg.to_lgo(cfg.genesis_pool) * 100.0,
        capacity=capacity_bonds(pool, cfg),
        providers=np.array([r.providers for r in result.rows], dtype=np.int64),
        service_lgo=np.array([r.service_per_provider_lgo for r in result.rows], dtype=float),
        cohort_share=share, cohort_wait=wait,
        absorption=absorption(result, cfg),
    )
