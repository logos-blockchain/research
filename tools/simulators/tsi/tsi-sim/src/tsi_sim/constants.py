"""Protocol constants and epoch/window geometry.

All slot geometry derives from the pair ``(k, f)`` so a scaled-down ``k`` (used for
parameter sweeps) automatically shrinks the epoch and measurement window. See
``cryptarchia-v1-protocol.md`` and ``cryptarchia-total-stake-inference.md``.
"""

from __future__ import annotations

# --- True protocol values (full scale) -------------------------------------
K_TRUE = 2160          # security parameter (blocks)
F = 1.0 / 30.0         # slot activation coefficient (fixed; never tuned)
W_DEFAULT = 300        # uncle reference window w_u (slots)
BETA_DEFAULT = 1.0     # TSI learning rate
SLOT_SECONDS = 1       # slot length


def floor_k_over_f(k: int, f: float = F) -> int:
    """``floor(k / f)`` — the base quantum of the epoch schedule."""
    return int(k / f)


def epoch_len(k: int, f: float = F) -> int:
    """Epoch length in slots: ``10 * floor(k/f)``."""
    return 10 * floor_k_over_f(k, f)


def period_T(k: int, f: float = F) -> int:
    """TSI measurement window length ``T`` in slots: ``6 * floor(k/f)``.

    This is the first ``6*floor(k/f)`` slots of the (previous) epoch over which the
    block density is measured.
    """
    return 6 * floor_k_over_f(k, f)


def expected_blocks_in_window(k: int, f: float = F) -> float:
    """Expected honest-chain block count in the measurement window at equilibrium."""
    return period_T(k, f) * f
