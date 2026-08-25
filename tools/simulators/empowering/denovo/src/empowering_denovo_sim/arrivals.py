"""Arrival processes for R5's scenarios. Each returns miners-per-epoch as an int array."""
from __future__ import annotations

import numpy as np


def uniform(epochs: int, per_epoch: int) -> np.ndarray:
    return np.full(epochs, per_epoch, dtype=np.int64)


def spike(epochs: int, per_epoch: int, at: int, factor: float, width: int = 1) -> np.ndarray:
    """Uniform background with a cohort of ``factor`` times the background at ``at``."""
    a = uniform(epochs, per_epoch)
    a[at:at + width] = int(per_epoch * factor)
    return a


def front_loaded(epochs: int, total: int) -> np.ndarray:
    """Everyone in the first tenth of the horizon."""
    a = np.zeros(epochs, dtype=np.int64)
    head = max(1, epochs // 10)
    a[:head] = total // head
    return a


def back_loaded(epochs: int, total: int) -> np.ndarray:
    a = np.zeros(epochs, dtype=np.int64)
    tail = max(1, epochs // 10)
    a[-tail:] = total // tail
    return a


def pi5_pareto(rng: np.random.Generator, floor_rate: float, shape: float = 1.16):
    """The study's standard hashrate draw: Pareto floored at a Raspberry Pi 5."""
    def draw(n: int) -> np.ndarray:
        return floor_rate * (1.0 + rng.pareto(shape, size=n))
    return draw
