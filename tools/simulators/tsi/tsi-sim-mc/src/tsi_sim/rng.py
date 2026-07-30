"""Deterministic, order-independent RNG derivation.

Each ``SimConfig`` maps to an independent root ``SeedSequence`` seeded from a hash of its
identity plus the global root seed. This guarantees a config yields the same random stream
regardless of the order in which parallel workers run it. The engine ``spawn``\\s children
of this root — one per epoch, and independent sub-streams within an epoch — so every draw
(including the optional parallel chunked lottery) is a deterministic function of the root.
"""

from __future__ import annotations

import hashlib

import numpy as np

from .config import SimConfig


def _entropy(config: SimConfig) -> int:
    payload = repr((config.root_seed, config.key())).encode()
    digest = hashlib.blake2b(payload, digest_size=16).digest()
    return int.from_bytes(digest, "big")


def seedseq_for(config: SimConfig) -> np.random.SeedSequence:
    """Return the reproducible root ``SeedSequence`` for this exact config+replicate."""
    return np.random.SeedSequence(_entropy(config))


def rng_for(config: SimConfig) -> np.random.Generator:
    """Return the reproducible ``Generator`` for this exact config+replicate."""
    return np.random.default_rng(seedseq_for(config))
