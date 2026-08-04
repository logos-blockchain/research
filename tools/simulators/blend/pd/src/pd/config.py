"""Configuration dataclasses for single runs and parameter sweeps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from . import constants

LatencyDist = Literal["geo", "fixed", "uniform", "exp"]
AdversaryMode = Literal[
    "random", "worstcase_coverage", "worstcase_eclipse", "worstcase_degree"
]
_DISTS = ("geo", "fixed", "uniform", "exp")
_MODES = ("random", "worstcase_coverage", "worstcase_eclipse", "worstcase_degree")
WORSTCASE_MODES = ("worstcase_coverage", "worstcase_eclipse", "worstcase_degree")


@dataclass(frozen=True)
class SimConfig:
    """A single fully-specified graph cell (one topology + one propagation/adversary setting)."""

    # --- network ---
    n_nodes: int = 1000                 # must be even (matching-union construction)
    degree: int = 8                     # peering degree — the primary study axis

    # --- propagation (Blend cascade, delays in ms) ---
    blend_hops: int = 3                 # relay-path length (swept)
    max_blend_delay: int = 3            # free-running release-clock max interval, whole SECONDS
    unresponsive_frac: float = 0.0      # ratio of nodes that do NOT relay any messages (swept)
    redundancy: int = 1                 # copies per emission via R independent cascades (swept)
    n_rounds: int = 200                 # random-sender rounds per topology
    transport_jitter_mean_ms: float = 5.0
    processing_lags_ms: tuple[float, ...] = (10.0, 50.0, 100.0)
    processing_lag_probs: tuple[float, ...] = (0.5, 0.4, 0.1)
    link_latency_dist: LatencyDist = "geo"
    link_latency_mean_ms: float = constants.GEO_LATENCY_MEAN_MS   # only used by non-geo dists
    coverage_pcts: tuple[float, ...] = (50.0, 90.0, 99.0)

    # --- adversary ---
    f_adv: float = 0.0
    adversary_mode: AdversaryMode = "random"
    n_placements: int = 4               # random-placement sub-replicates (worstcase -> 1)
    worstcase_max_n: int = 100_000      # cap greedy worst-case strategies above this N

    # --- bookkeeping ---
    graph_seed: int = 0                 # the "global seed" / topology-ensemble index
    replicate: int = 0
    root_seed: int = 12345

    def __post_init__(self) -> None:
        if self.n_nodes % 2 != 0:
            raise ValueError(f"n_nodes must be even, got {self.n_nodes}")
        if not (1 <= self.degree < self.n_nodes):
            raise ValueError(f"need 1 <= degree < n_nodes ({self.degree} vs {self.n_nodes})")
        if not (1 <= self.blend_hops < self.n_nodes):
            raise ValueError(f"need 1 <= blend_hops < n_nodes, got {self.blend_hops}")
        if self.max_blend_delay < 0:
            raise ValueError("max_blend_delay must be >= 0 (whole seconds)")
        if not (0.0 <= self.unresponsive_frac < 1.0):
            raise ValueError(f"need 0 <= unresponsive_frac < 1, got {self.unresponsive_frac}")
        if self.redundancy < 1:
            raise ValueError(f"redundancy must be >= 1, got {self.redundancy}")
        if not (0.0 <= self.f_adv < 1.0):
            raise ValueError(f"need 0 <= f_adv < 1, got {self.f_adv}")
        if self.n_rounds < 1 or self.n_placements < 1:
            raise ValueError("n_rounds and n_placements must be >= 1")
        if len(self.processing_lags_ms) != len(self.processing_lag_probs):
            raise ValueError("processing_lags_ms and processing_lag_probs must have equal length")
        if abs(sum(self.processing_lag_probs) - 1.0) > 1e-9:
            raise ValueError(
                f"processing_lag_probs must sum to 1, got {sum(self.processing_lag_probs)}")
        if any(p < 0 for p in self.processing_lag_probs):
            raise ValueError("processing_lag_probs must be non-negative")
        if self.link_latency_dist not in _DISTS:
            raise ValueError(f"link_latency_dist must be one of {_DISTS}")
        if self.adversary_mode not in _MODES:
            raise ValueError(f"adversary_mode must be one of {_MODES}")

    @property
    def n_adv(self) -> int:
        return int(round(self.f_adv * self.n_nodes))

    @property
    def n_honest(self) -> int:
        return self.n_nodes - self.n_adv

    def key(self) -> tuple:
        """Hashable identity used to seed RNGs deterministically."""
        return (
            self.n_nodes, self.degree, self.blend_hops, self.max_blend_delay,
            self.unresponsive_frac, self.redundancy, self.n_rounds,
            self.transport_jitter_mean_ms, self.processing_lags_ms, self.processing_lag_probs,
            self.link_latency_dist, self.link_latency_mean_ms, self.coverage_pcts,
            self.f_adv, self.adversary_mode, self.n_placements, self.worstcase_max_n,
            self.graph_seed, self.replicate, self.root_seed,
        )


_TUPLE_FIELDS = ("processing_lags_ms", "processing_lag_probs", "coverage_pcts")


@dataclass
class SweepConfig:
    """Grids for a sweep: topologies (n x degree x graph_seed) plus the propagation and
    adversary sub-grids that every topology is measured over."""

    n_nodes: list[int] = field(default_factory=lambda: [1000])
    degree: list[int] = field(default_factory=lambda: [3, 4, 6, 8, 12, 16])
    blend_hops: list[int] = field(default_factory=lambda: [3])
    max_blend_delay: list[int] = field(default_factory=lambda: [3])
    unresponsive_frac: list[float] = field(default_factory=lambda: [0.0])
    redundancy: list[int] = field(default_factory=lambda: [1])
    f_adv: list[float] = field(default_factory=lambda: [0.1, 0.2, 0.33, 0.5])
    adversary_mode: list[str] = field(default_factory=lambda: ["random"])
    seeds: int = 8                       # number of graph_seed values (topology ensemble)
    base: dict[str, Any] = field(default_factory=dict)

    def base_config(self, n_nodes: int, degree: int, graph_seed: int) -> SimConfig:
        b = dict(self.base)
        for k in _TUPLE_FIELDS:
            if k in b and b[k] is not None:
                b[k] = tuple(b[k])
        b.pop("n_nodes", None)
        b.pop("degree", None)
        b.pop("graph_seed", None)
        return SimConfig(n_nodes=n_nodes, degree=degree, graph_seed=graph_seed, **b)

    def graph_cells(self) -> list[tuple[int, int, int]]:
        """Distinct topologies to build: (n_nodes, degree, graph_seed)."""
        return [(n, d, g) for n in self.n_nodes for d in self.degree for g in range(self.seeds)]

    def prop_grid(self) -> list[tuple[int, int]]:
        """(blend_hops, max_blend_delay) settings each topology is measured over."""
        return [(bh, md) for bh in self.blend_hops for md in self.max_blend_delay]

    def adv_grid(self) -> list[tuple[float, str]]:
        """(f_adv, adversary_mode) settings; f_adv==0 keeps only one (mode-irrelevant) row."""
        out: list[tuple[float, str]] = []
        for f in self.f_adv:
            modes = self.adversary_mode if f > 0 else self.adversary_mode[:1]
            for m in modes:
                out.append((f, m))
        return out

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SweepConfig:
        d = dict(d)
        base = d.pop("base", {})
        known = {"n_nodes", "degree", "blend_hops", "max_blend_delay", "unresponsive_frac",
                 "redundancy", "f_adv", "adversary_mode", "seeds"}
        unknown = set(d) - known
        if unknown:
            raise ValueError(f"unknown sweep keys: {sorted(unknown)}")
        return cls(base=base, **{k: v for k, v in d.items() if k in known})
