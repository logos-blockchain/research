"""Per-link base latencies (ms) and per-node processing lags (ms)."""

from __future__ import annotations

import numpy as np

from . import constants
from .config import SimConfig


def sample_link_latencies(n_edges: int, config: SimConfig, rng: np.random.Generator) -> np.ndarray:
    """Per-(undirected-)edge one-way base latency in ms.

    ``geo`` draws each link from the real-world geographic band mixture (used as-is, in ms);
    ``fixed``/``uniform``/``exp`` have mean ``link_latency_mean_ms``.
    """
    dist = config.link_latency_dist
    if dist == "geo":
        bands = np.asarray(constants.GEO_LATENCY_BANDS_MS, dtype=float)
        weights = np.asarray(constants.GEO_LATENCY_WEIGHTS, dtype=float)
        idx = rng.choice(bands.shape[0], size=n_edges, p=weights)
        return bands[idx]
    mean = config.link_latency_mean_ms
    if dist == "fixed":
        return np.full(n_edges, mean, dtype=float)
    if dist == "uniform":
        return rng.uniform(0.0, 2.0 * mean, size=n_edges)
    if dist == "exp":
        return rng.exponential(mean, size=n_edges)
    raise ValueError(f"unknown link_latency_dist {dist!r}")


def assign_processing_lags(n_nodes: int, config: SimConfig, rng: np.random.Generator) -> np.ndarray:
    """Per-node fixed processing lag (ms): a categorical draw over ``processing_lags_ms`` with
    weights ``processing_lag_probs`` (e.g. {10,50,100} ms at {0.5,0.4,0.1})."""
    lags = np.asarray(config.processing_lags_ms, dtype=float)
    probs = np.asarray(config.processing_lag_probs, dtype=float)
    idx = rng.choice(lags.shape[0], size=n_nodes, p=probs)
    return lags[idx]
