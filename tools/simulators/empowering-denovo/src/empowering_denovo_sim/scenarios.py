"""The Phase D scenario matrix: cohort-typed draws, the whale, and the oscillation probe."""
from __future__ import annotations

import numpy as np

from . import arrivals as arr
from . import engine
from . import power
from .params import Derived


class CohortDraw:
    """A hashrate draw that knows the arrival schedule.

    The engine calls the draw once per epoch THAT SEATS ANYONE, in order -- epochs with no
    arrivals do not call it. ``specials`` is therefore keyed by seating ORDINAL, not by
    epoch; callers with gappy schedules must translate (see `whale_run`). A first version
    keyed by epoch and was correct only for gapless backgrounds.
    """

    def __init__(self, base_draw, specials: dict[int, float] | None = None):
        self.base = base_draw
        self.specials = specials or {}          # seating-call index -> absolute rate
        self.calls = 0

    def __call__(self, n: int) -> np.ndarray:
        out = self.base(n)
        if self.calls in self.specials:
            out[0] = self.specials[self.calls]
        self.calls += 1
        return out


def whale_run(d: Derived, per_epoch: int, whale_epoch: int, whale_multiple: float,
              epochs: int, seed: int = 70_001):
    """Uniform background plus one actor holding ``whale_multiple`` times **the field it
    meets** -- the honest baseline: the expected aggregate rate of everyone seated before it.
    An earlier version scaled against the run's eventual field, which overstated a "1x" whale
    by the ratio of the horizons."""
    cfg = d.cfg
    floor_rate = power.board(cfg).candidates_per_second
    base = arr.pi5_pareto(np.random.default_rng(2), floor_rate)
    mean_rate = floor_rate * (1 + 1 / (1.16 - 1))            # Pareto mean at the study shape
    field_met = max(1, per_epoch * whale_epoch) * mean_rate
    a = arr.uniform(epochs, per_epoch)
    a[whale_epoch] += 1
    ordinal = int(np.count_nonzero(a[:whale_epoch]))     # == whale_epoch for this background,
    draw = CohortDraw(base, specials={ordinal: whale_multiple * field_met})  # but computed
    return engine.run(d, a, draw, epochs=epochs, seed=seed)


def elastic_run(d: Derived, per_epoch: int, epochs: int, threshold_lepta: int,
                eta: float, seed: int = 70_001):
    """MODEL.md 8.1: participation responds to the posted reward.

    ``eta`` is the elasticity: participation = min(1, (reward / threshold) ** eta). A step
    (large eta) is the worst case for the demand-indexed reward's feedback loop.
    """
    cfg = d.cfg
    draw = arr.pi5_pareto(np.random.default_rng(2), 1 / cfg.seconds_per_candidate_reward)

    def participation(reward: int, _e: int) -> float:
        return min(1.0, (reward / threshold_lepta) ** eta)

    return engine.run(d, arr.uniform(epochs, per_epoch), draw, epochs=epochs, seed=seed,
                      participation=participation)


def amplitude(rows, start: int, stop: int) -> float:
    """Detrended relative oscillation amplitude of the claim series over a window.

    A linear trend is removed first: the raw range-over-mean conflates the field's growth
    (arrivals keep coming) and one-off transients with the cycle the probe is after, and an
    earlier version of this metric reported a 7x "oscillation" that was mostly ramp.
    """
    x = np.array([q.claims_paid for q in rows[start:stop]], dtype=float)
    if x.size < 4 or x.mean() <= 0:
        return 0.0
    t = np.arange(x.size, dtype=float)
    resid = x - np.polyval(np.polyfit(t, x, 1), t)
    return float((resid.max() - resid.min()) / x.mean())
