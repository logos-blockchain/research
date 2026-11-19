"""Shared constants and helpers for PROOF.md (attempt A).

The specification is read with git from a clone of logos-lips named by LIPS_REPO, at commit
83596b6e (`git show 83596b6e:docs/blockchain/raw/<path>`). GENESIS's code (common_g.py) is imported
read-only from its folder; nothing is written there: bytecode writing is off and numba's cache is this
folder's .cache/numba (set NUMBA_CACHE_DIR before running; the run_all.sh script does).
"""
from __future__ import annotations

import math
import os
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("NUMBA_CACHE_DIR", os.path.join(HERE, ".cache", "numba"))
GENESIS_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "genesis"))
if GENESIS_DIR not in sys.path:
    sys.path.insert(0, GENESIS_DIR)
import common_g as cg  # noqa: E402  (read-only import)

import numpy as np  # noqa: E402

SPEC_REPO = os.environ.get("LIPS_REPO", "")  # a clone of logos-lips that holds SPEC_REF
SPEC_REF = "83596b6e"

F = 1 / 30                 # protocol 103
K_SEC = 2160               # protocol 104
K = 36_000                 # protocol 105
S = K_SEC * 30 // 4        # s_gen = floor(k / (4 f)), fork choice 80: 16,200
F_HAT = 33 / 1000          # truncate(f * PRECISION) / PRECISION, inference 77
W_UNCLE = 360              # W f^-1, protocol 110
EPS = 1e-9
H = 3600

# schedules: name -> (snapshot phase P = PERIOD, gap G = Lottery Constants Finalization phase)
SCHEDULES = {
    "(i) G = s + K - 1": (None, S + K - 1),          # 52,199; the snapshot phase is not fixed by (i)
    "(ii) 1.5K + 1.5K": (54_000, 54_000),
}
SPEC_SCHEDULE = (2 * K, 2 * K)                         # protocol 154-159 at 83596b6e
GENESIS_G = 259_200                                    # GENESIS's gap (4 floor(k/f))

# the K row's states, as REVIEW.md 5.9 maps them and GENESIS g07_states.py encodes them:
# name, honest share of D, coalition share of D, Delta, (alpha, scale) of the cached curve U
STATES = [
    ("no disturbance", 0.7, 0.3, 10, (0.3, 1.0)),
    ("every block T_M late", 0.7, 0.3, 15, (0.3, 1.0)),
    ("a tenth offline, inference corrected", 0.63 / 0.93, 0.3 / 0.93, 10, (0.3 / 0.93, 1.0)),
    ("a tenth offline, before the correction", 0.63, 0.3, 10, (0.3 / 0.93, 0.93)),
    ("D equals the honest stake online", 1.0, 0.3 / 0.7, 10, (0.3, 1 / 0.7)),
]
T_MAX = 160_000


def git_show(path: str, ref: str = SPEC_REF) -> list[str]:
    if not SPEC_REPO:
        raise SystemExit(f"set LIPS_REPO to a clone of logos-lips that holds {ref}")
    out = subprocess.run(["git", "-C", SPEC_REPO, "show", f"{ref}:docs/blockchain/raw/{path}"],
                         check=True, capture_output=True, text=True).stdout
    return out.split("\n")


def line(path: str, n: int) -> str:
    return git_show(path)[n - 1]


def U_curve(alpha: float, delta: int, scale: float) -> np.ndarray:
    """The study's settlement curve as GENESIS cached it (read-only; raises if it is not cached)."""
    name = os.path.join(GENESIS_DIR, ".cache", f"U_a{alpha:.6f}_d{delta}_t{T_MAX}_s{scale:.6f}.npy")
    if not os.path.exists(name):
        raise FileNotFoundError(name)
    return np.load(name)


def U_at(curve: np.ndarray, w: int) -> float:
    return cg.U_at(curve, w)


def p_of(share: float) -> float:
    return cg.p_of(share)
