"""Network latency models.

Latency ``L`` is the number of slots between a block being produced and it becoming
visible to the rest of the network. ``L`` is deliberately named to avoid clashing with
``D`` (the stake estimate). A leader at slot ``t`` can only build on blocks whose
``visible_at <= t`` (its own block is visible to itself immediately), which is what
produces latency-induced forks.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class LatencyModel(Protocol):
    def visible_at(self, produced_slot: int, rng: np.random.Generator) -> int:
        """Slot at which a block produced at ``produced_slot`` becomes visible to others."""
        ...


class FixedSlotLatency:
    """Deterministic integer-slot latency: visible to all others at ``t + L``."""

    def __init__(self, latency: int) -> None:
        self.latency = int(latency)

    def visible_at(self, produced_slot: int, rng: np.random.Generator) -> int:
        return produced_slot + self.latency


class RealisticLatency:
    """Stochastic latency with mean ``L`` slots (optional sensitivity model).

    Rounds an exponential draw (mean ``L``) up to whole slots. A stand-in for the
    reference notebook's blend/broadcast delay model; not used by the primary sweep.
    """

    def __init__(self, mean_latency: float) -> None:
        self.mean_latency = float(mean_latency)

    def visible_at(self, produced_slot: int, rng: np.random.Generator) -> int:
        if self.mean_latency <= 0:
            return produced_slot
        draw = rng.exponential(self.mean_latency)
        return produced_slot + int(np.ceil(draw))


def make_latency(config) -> LatencyModel:  # noqa: ANN001 - avoid import cycle with config
    """Build the latency model for a config."""
    if config.latency_stochastic:
        return RealisticLatency(config.latency)
    return FixedSlotLatency(config.latency)
