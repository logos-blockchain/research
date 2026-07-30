"""Stake distribution generation.

Total stake is held FIXED across distributions (via renormalisation) so that accuracy
comparisons between ``uniform`` and ``pareto`` isolate the *shape* effect on the lottery
(winner multiplicity / forking), not a difference in aggregate stake.
"""

from __future__ import annotations

import numpy as np

from .config import SimConfig


def make_stake(config: SimConfig, rng: np.random.Generator) -> np.ndarray:
    """Return an ``(n_nodes,)`` non-negative stake vector summing to ``total_stake``."""
    n = config.n_nodes
    if config.stake_dist == "uniform":
        if config.uniform_random:
            w = rng.random(n)
        else:
            w = np.ones(n)
    elif config.stake_dist == "pareto":
        # numpy.pareto draws Lomax = Pareto(shape) - 1, heavy-tailed for small shape.
        w = rng.pareto(config.pareto_shape, n) + 1.0
    else:  # pragma: no cover - guarded by Literal typing
        raise ValueError(f"unknown stake_dist: {config.stake_dist}")

    total = w.sum()
    if total <= 0:  # pragma: no cover - degenerate
        raise ValueError("stake vector summed to zero")
    return w * (config.total_stake / total)
