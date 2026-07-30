"""Configuration dataclasses for single runs and parameter sweeps."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from . import constants

StakeDist = Literal["uniform", "pareto"]
UncleStrategy = Literal["oldest", "random"]


@dataclass(frozen=True)
class SimConfig:
    """A single fully-specified simulation run (one grid cell, one replicate)."""

    # --- network / stake ---
    n_nodes: int = 1000
    stake_dist: StakeDist = "uniform"
    pareto_shape: float = 1.16          # Pareto (Lomax) tail index; ~80/20 by default
    uniform_random: bool = False        # if True, draw i.i.d. uniform stakes; else equal
    total_stake: float = 1.0e9          # FIXED across distributions for comparability

    # --- network latency (slots) ---
    latency: int = 0                    # L: block visible to others at t + L
    latency_stochastic: bool = False    # if True, L is the mean of a stochastic model

    # --- uncle references ---
    uncle_window: int = constants.W_DEFAULT   # W
    max_uncles: int = 0                       # U (0 = baseline, no uncles)
    uncle_strategy: UncleStrategy = "oldest"
    uncle_random_p: float = 0.5               # coin-flip inclusion prob (random strategy)

    # --- consensus / TSI ---
    f: float = constants.F
    beta: float = constants.BETA_DEFAULT
    k: int = 64                          # scaled by default; full scale = 2160
    genesis_d_factor: float = 0.5        # genesis D = factor * true total stake
    epochs: int = 40
    per_node_dest: bool = False          # Phase-2 hook: per-node D_est (unused in reduced model)

    # --- bookkeeping ---
    replicate: int = 0
    root_seed: int = 12345

    # derived geometry -------------------------------------------------------
    @property
    def epoch_len(self) -> int:
        return constants.epoch_len(self.k, self.f)

    @property
    def period_T(self) -> int:
        return constants.period_T(self.k, self.f)

    def key(self) -> tuple:
        """Hashable identity used to seed the RNG deterministically."""
        return (
            self.n_nodes, self.stake_dist, self.pareto_shape, self.uniform_random,
            self.total_stake, self.latency, self.latency_stochastic, self.uncle_window,
            self.max_uncles, self.uncle_strategy, self.uncle_random_p, self.f, self.beta,
            self.k, self.genesis_d_factor, self.epochs, self.per_node_dest, self.replicate,
        )


@dataclass
class SweepConfig:
    """A cartesian grid of runs plus replicates, all sharing ``base`` settings."""

    n_nodes: list[int] = field(default_factory=lambda: [1000])
    stake_dist: list[StakeDist] = field(default_factory=lambda: ["uniform", "pareto"])
    latency: list[int] = field(default_factory=lambda: [0, 1, 2, 4, 8])
    max_uncles: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    uncle_strategy: list[UncleStrategy] = field(default_factory=lambda: ["oldest", "random"])
    f: list[float] = field(default_factory=lambda: [constants.F])
    replicates: int = 8
    base: dict[str, Any] = field(default_factory=dict)

    def expand(self) -> list[SimConfig]:
        """Materialise every ``SimConfig`` in the grid × replicates."""
        base = SimConfig(**self.base)
        cells: list[SimConfig] = []
        axes = itertools.product(
            self.n_nodes, self.stake_dist, self.latency, self.max_uncles,
            self.uncle_strategy, self.f,
        )
        for n, dist, lat, u, strat, fval in axes:
            # U=0 is strategy-independent; keep only one strategy to avoid duplicate work.
            if u == 0 and strat != self.uncle_strategy[0]:
                continue
            for rep in range(self.replicates):
                cells.append(
                    replace(
                        base,
                        n_nodes=n,
                        stake_dist=dist,
                        latency=lat,
                        max_uncles=u,
                        uncle_strategy=strat,
                        f=fval,
                        replicate=rep,
                    )
                )
        return cells

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SweepConfig:
        d = dict(d)
        base = d.pop("base", {})
        known = {
            "n_nodes", "stake_dist", "latency", "max_uncles",
            "uncle_strategy", "f", "replicates",
        }
        kwargs = {k: v for k, v in d.items() if k in known}
        return cls(base=base, **kwargs)
