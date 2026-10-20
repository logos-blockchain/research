"""The total-stake inference as a lever (FURTHER.md, G7).

The inference sets the next epoch's lottery thresholds from the occupied slots of the previous
period, ``PERIOD = 6⌊k/f⌋`` slots, with a full correction (``beta = 1``): a coalition that withholds
every block it wins for a period lowers the inferred stake by its share ``α`` and raises every
threshold by ``1/(1 − α)``. The honest stake alone then occupies slots at ``f``, the coalition at
``1 − (1 − f)^(α/(1−α))``, and a worst case of ``Δ`` slots reads as one of ``Δ/(1 − α)`` at the
old rates. Under random delay the honest chain then grows as it does with everyone producing at
``f``. In the convention's model, which reads that growth for every race, ``q`` is unchanged; on
the engine the honest growth falls from the withheld race's to every node producing's, and the
depth rises past the convention (FURTHER.md G7). The engine plays it with every estimate deflated
(``finality_sim.race.withhold_tree``, ``stake_scale = 1 − α``).

Withholding fewer blocks gives a smaller raise, and the coalition can choose among the nested
schedules the raise levels give its own wins; the honest nodes' outputs stay unknown to it. The
most it can gain is the largest excess of its own extra wins over their mean along the levels,
about ``sqrt(2M/π)`` for ``M`` extra wins at the full raise.
"""

from __future__ import annotations

import math

import numpy as np

from finality_sim.recovery import occupancy


def raise_factor(alpha: float) -> float:
    """The factor every lottery threshold gains after a period in which the coalition withheld
    every block it won."""
    return 1.0 / (1.0 - alpha)


def deflated_delay(delta_s: float, alpha: float) -> float:
    """The delay at the old rates that reads as ``delta_s`` at the raised ones."""
    return delta_s * raise_factor(alpha)


def raised_rates(f: float, alpha: float) -> tuple[float, float]:
    """The honest and the coalition's slot occupancy at the raised thresholds."""
    return occupancy(f, 1.0), occupancy(f, alpha / (1.0 - alpha))


def extra_wins(f: float, alpha: float, epoch_slots: int) -> float:
    """The coalition's expected extra wins over an epoch at the full raise."""
    return epoch_slots * (occupancy(f, alpha / (1.0 - alpha)) - occupancy(f, alpha))


def selection_excess(m: float, levels: int, n_paths: int, seed: int) -> tuple[float, float]:
    """The expected largest excess of the coalition's extra wins over their mean across ``levels``
    nested raise levels that reach ``m`` extra wins in all: the Brownian value ``sqrt(2m/π)`` and a
    Monte Carlo of the Poisson path."""
    rng = np.random.default_rng(seed)
    step = m / levels
    inc = rng.poisson(step, size=(n_paths, levels)) - step
    excess = np.maximum(np.max(np.cumsum(inc, axis=1), axis=1), 0.0)
    return math.sqrt(2.0 * m / math.pi), float(excess.mean())


def periods_to_deflate(alpha: float, cap: float) -> int:
    """The periods a coalition needs to lower the inferred stake by its share when the inference
    lowers it by at most ``cap`` a period."""
    return math.ceil(math.log(1.0 - alpha) / math.log(1.0 - cap))
