"""Deterministic, order-independent RNG derivation.

Each ``SimConfig`` maps to an independent NumPy ``Generator`` seeded from a hash of its
identity plus the global root seed. This guarantees a config yields the same random
stream regardless of the order in which parallel workers run it.
"""

from __future__ import annotations

import hashlib

import numpy as np

from .config import SimConfig


def _entropy(config: SimConfig) -> int:
    payload = repr((config.root_seed, config.key())).encode()
    digest = hashlib.blake2b(payload, digest_size=16).digest()
    return int.from_bytes(digest, "big")


def rng_for(config: SimConfig) -> np.random.Generator:
    """Return the reproducible ``Generator`` for this exact config+replicate."""
    seed = np.random.SeedSequence(_entropy(config))
    return np.random.default_rng(seed)
