"""What a mining node actually is, stated rather than assumed.

Every claim-rate figure in these studies rests on an assumption about how much silicon one
"node" commits, and that assumption was previously implicit and *inconsistent between the two
simulators*: `empowering_sim.elevation` seats nodes at 24,146 candidates a second — a whole
four-core Raspberry Pi 5 board — while the de-novo engine seated them at 6,037, one pinned
core. A factor of four, in studies whose numbers are compared against each other.

This module fixes the basis and makes the bracket explicit.

**The credibility problem with the synthetic field.** The studies draw hashrates from
``Pareto(1.16)`` floored at a Pi 5. The shape is not measured: 1.16 is the "80/20 rule" index
(`log 5 / log 4`), a folk constant from *wealth* distributions, applied here to hardware. That
is a leap. Wealth compounds; hardware is bought. Real mining populations are concentrated, but
by pooling and capital access rather than by the mechanism a Pareto describes, and no
measurement of a Logos mining population exists to fit against — the network has not launched.

So the synthetic draw is best read as *a* plausible spread rather than *the* expected one, and
anything that depends on its exact shape should be treated as indicative. What follows instead
are two bounds that do not depend on the shape at all:

* ``MINIMAL`` — one pinned core of a Raspberry Pi 5. The least a participant can commit and
  still be mining: a spare core on a board bought for something else. This is the "barely
  profitable" end, and at the bootstrap difficulty floor it is profitable at any plausible
  token price, so it is a floor on commitment rather than on viability.
* ``WORST`` — every core of the most efficient hardware measured, at full duty. This is the
  adversarial assumption: an attacker buys the best available and runs it flat out.

**What is NOT bounded, and it matters.** The worst case here is the best *measured* class, and
the classes with measured Poseidon2 rates are a Raspberry Pi 5 and an Apple M-series part. A
GPU rig would be faster per unit of cost and is the true adversarial ceiling; its Poseidon2
rate has not been benchmarked (the cost estimator carries the profile but no rate, and says
so). **Every adversarial number in these reports is therefore a lower bound on what a
well-equipped attacker achieves**, and the gap is unmeasured rather than small.
"""
from __future__ import annotations

from dataclasses import dataclass

from empowering_sim.config import Config

PI5_CORES = 4                     # protocol-snapshot.toml, [work] pi5_cores


@dataclass(frozen=True)
class PowerBasis:
    """One node's committed search rate, and where the figure comes from."""

    key: str
    candidates_per_second: float
    note: str


def minimal(cfg: Config) -> PowerBasis:
    """One pinned core of a Pi 5 — the least commitment that is still mining."""
    return PowerBasis("minimal-1-core", 1.0 / cfg.seconds_per_candidate_reward,
                      "one pinned core of a Raspberry Pi 5, measured")


def board(cfg: Config) -> PowerBasis:
    """A whole Pi 5, all cores, full duty — the honest default for a committed miner.

    This is what `empowering_sim.elevation` has always used, so it is also the basis that
    makes the de-novo figures comparable with the strategy study's.
    """
    return PowerBasis("board-4-core", PI5_CORES / cfg.seconds_per_candidate_reward,
                      "all four cores of a Raspberry Pi 5, measured, at full duty")


def worst(cfg: Config, efficiency_ratio: float = 3.45) -> PowerBasis:
    """The adversarial assumption: the best measured hardware, every core, full duty.

    ``efficiency_ratio`` is the Apple class's cost advantage per candidate over the Pi 5 in
    the estimator (2.025e-11 against 5.864e-12 USD). Applied to the rate as a stand-in for a
    faster part, since the Apple class's own candidate rate is not separately benchmarked.
    A GPU rig would exceed this and is unmeasured; see the module docstring.
    """
    return PowerBasis("worst-measured",
                      efficiency_ratio * PI5_CORES / cfg.seconds_per_candidate_reward,
                      f"best measured class, all cores, full duty -- {efficiency_ratio:.2f}x a "
                      f"Pi 5 board; a GPU rig would exceed this and is unbenchmarked")


def homogeneous(basis: PowerBasis):
    """A draw with no distributional assumption at all: every node identical.

    Used for the adversarial bounds, where a synthetic spread would only add unexamined
    variance to a number meant to bracket rather than to predict.
    """
    import numpy as np

    def draw(n: int) -> np.ndarray:
        return np.full(n, basis.candidates_per_second, dtype=float)
    return draw
