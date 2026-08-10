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


def stake_for(config) -> np.ndarray:
    """The stake vector a run of ``config`` actually uses.

    The engine draws stake from the **first spawned child** of the config's seed sequence
    (``engine.run_trajectory``, and likewise ``sweep`` and ``concurrency``), *not* from the root
    generator. ``rng_for(config)`` is the root, so ``make_stake(config, rng_for(config))`` returns
    a different vector — a valid stake draw, but not this run's.

    That difference is invisible in aggregate (both are the same distribution) and silent, so an
    analysis script that rebuilds a block tree with the root generator ends up describing a
    *different network* than the trajectory it is being compared against. Use this instead.

    ``SeedSequence.spawn(n)[0]`` is the same child for every ``n >= 1``, so this matches the
    engine's ``spawn(epochs + 3)[0]`` without needing to know the child count.
    """
    from .rng import seedseq_for

    return make_stake(config, np.random.default_rng(seedseq_for(config).spawn(1)[0]))
