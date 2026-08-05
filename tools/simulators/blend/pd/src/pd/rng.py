"""Deterministic, order-independent RNG derivation (blake2b -> SeedSequence).

Three independent seed streams so that graph, propagation and adversary randomness are
reproducible and separable:
- ``graph_seedseq`` depends ONLY on the topology fields, so the peer graph + per-node
  processing lags are a pure function of the global seed (the "consensus topology" property)
  and are IDENTICAL across every ``f_adv``/``adversary_mode`` cell that shares the topology;
- ``round_seedseq`` seeds the per-round sender/relay/jitter/mix draws;
- ``placement_seedseq`` seeds the adversary placement, independent of the graph/rounds.
"""

from __future__ import annotations

import hashlib

import numpy as np

from .config import SimConfig


def _digest(*parts: object) -> int:
    payload = repr(parts).encode()
    return int.from_bytes(hashlib.blake2b(payload, digest_size=16).digest(), "big")


def seedseq_for(config: SimConfig) -> np.random.SeedSequence:
    """Full-key root SeedSequence for this exact config (parity with the sibling sims)."""
    return np.random.SeedSequence(_digest(config.root_seed, config.key()))


def rng_for(config: SimConfig) -> np.random.Generator:
    return np.random.default_rng(seedseq_for(config))


def graph_seedseq(config: SimConfig) -> np.random.SeedSequence:
    """Topology-only seed: peer graph + processing lags depend on these fields alone."""
    return np.random.SeedSequence(_digest(
        config.root_seed, "graph", config.n_nodes, config.degree, config.graph_seed,
        config.n_regions, config.region_locality,
        config.link_latency_dist, config.link_latency_mean_ms,
        config.processing_lags_ms, config.processing_lag_probs,
    ))


def responsive_seedseq(config: SimConfig, unresponsive_frac: float,
                       churn_mode: str = "uniform") -> np.random.SeedSequence:
    """Which nodes are responsive: fixed per (topology, unresponsive_frac, churn_mode)."""
    return np.random.SeedSequence(_digest(
        config.root_seed, "responsive", config.n_nodes, config.degree, config.graph_seed,
        unresponsive_frac, churn_mode, config.n_regions,
    ))


def round_seedseq(config: SimConfig, blend_hops: int, max_blend_delay: int,
                  unresponsive_frac: float, redundancy: int = 1) -> np.random.SeedSequence:
    """Per-cell propagation seed (senders/relays/jitter/mix over n_rounds)."""
    return np.random.SeedSequence(_digest(
        config.root_seed, "rounds", config.n_nodes, config.degree, config.graph_seed,
        blend_hops, max_blend_delay, unresponsive_frac, redundancy, config.n_rounds,
        config.transport_jitter_mean_ms,
    ))


def placement_seedseq(config: SimConfig, f_adv: float, mode: str,
                      placement_rep: int) -> np.random.SeedSequence:
    """Adversary-placement seed, independent of the graph draw and the rounds."""
    return np.random.SeedSequence(_digest(
        config.root_seed, "place", config.n_nodes, config.degree, config.graph_seed,
        f_adv, mode, placement_rep,
    ))
