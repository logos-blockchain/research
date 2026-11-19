"""Shared setup for the scripts of PROOF.md.

GENESIS's code is imported read-only from its folder. Nothing is written there: bytecode writing is
off, numba's cache is this folder's .cache/numba, and the settlement curves U are read from GENESIS's
.cache with np.load only (a missing curve is an error, never a recomputation).
"""
from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["NUMBA_CACHE_DIR"] = os.path.join(HERE, ".cache", "numba")
GEN = os.path.normpath(os.path.join(HERE, "..", "..", "genesis"))
if GEN not in sys.path:
    sys.path.insert(0, GEN)

import numpy as np  # noqa: E402

from common_g import EPS, H, S_GEN, YEAR, U_at, Window, p_of  # noqa: E402,F401

K = 36_000                       # protocol 105 (branch Bedrock-RFC-Shorter-Epoch, 83596b6e)
F = 1 / 30                       # protocol 103
F_HAT = 33 / 1000                # truncate(f * PRECISION) / PRECISION, inference 77
S = S_GEN                        # fork choice 80: floor(k / (4 f)) = 16,200
T_MAX = 160_000                  # length of GENESIS's cached curves

# Schedules: (name, G, snapshot phase = observation PERIOD, or None when the task leaves it free)
SCHEDULES = [
    ("(i) least G with s + K <= G + 1", 52_199, None),
    ("(ii) two phases of 1.5 K", 54_000, 54_000),
]
REFERENCE_G = [
    ("GENESIS's G (base schedule, 7f3cf149)", 259_200),
    ("current branch, two phases of 2 K", 72_000),
    ("least G of 7.5 (K - 1)", K - 1),
]

# The K row's states as REVIEW.md 5.9 maps them, against 30 % (GENESIS g07_states.py, unchanged):
# name, honest share of D, coalition share of D, Delta, (alpha, scale) of the cached curve U
STATES = [
    ("no disturbance", 0.7, 0.3, 10, (0.3, 1.0)),
    ("every block T_M late", 0.7, 0.3, 15, (0.3, 1.0)),
    ("a tenth offline, inference corrected", 0.63 / 0.93, 0.3 / 0.93, 10, (0.3 / 0.93, 1.0)),
    ("a tenth offline, before the correction", 0.63, 0.3, 10, (0.3 / 0.93, 0.93)),
    ("D equals the honest stake online", 1.0, 0.3 / 0.7, 10, (0.3, 1 / 0.7)),
]


def load_U(alpha: float, delta: int, scale: float = 1.0) -> np.ndarray:
    """GENESIS's cached settlement curve: U[w - 1] bounds P(mu_l >= 0 at some slot >= l + w)."""
    name = os.path.join(GEN, ".cache", f"U_a{alpha:.6f}_d{delta}_t{T_MAX}_s{scale:.6f}.npy")
    if not os.path.exists(name):
        raise FileNotFoundError(name)
    return np.load(name)
