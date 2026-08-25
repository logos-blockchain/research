"""Protocol constants and epoch/window geometry.

All slot geometry derives from the pair ``(k, f)`` so a scaled-down ``k`` (used for
parameter sweeps) automatically shrinks the epoch and measurement window. See
``cryptarchia-v1-protocol.md`` and ``cryptarchia-total-stake-inference.md``.
"""

from __future__ import annotations

# --- True protocol values (full scale) -------------------------------------
K_TRUE = 2160          # security parameter (blocks)
F = 1.0 / 30.0         # slot activation coefficient (default; configurable per run)
W_DEFAULT = 300        # old model: uncle reference window w_u (slots), set directly (--old)
BETA_DEFAULT = 1.0     # TSI learning rate
SLOT_SECONDS = 1       # slot length (seconds) — so 1 slot == 1 s

# --- Countable uncle model (cryptarchia-v1-protocol.md, uncle references) ---
# The spec derives the uncle reference window from the *window absorption parameter* W:
# w_u = W * f^-1 slots, i.e. W expected block-intervals. W is bounded by 1 <= W <= 0.6*k,
# equivalently w_u <= 0.6*k/f = s/5, keeping the window strictly inside the finalization
# window. The default W = 10 reproduces w_u = 300 slots at f = 1/30.
W_ABS_DEFAULT = 10.0       # window absorption parameter W (expected block-intervals)
W_ABS_MAX_FACTOR = 0.6     # bound: W <= W_ABS_MAX_FACTOR * k


def uncle_window_slots(w_abs: float, f: float = F) -> int:
    """Derived uncle reference window ``w_u = floor(W / f)`` in slots (countable model).

    The spec writes this as a **floor** (``w_u := ⌊W·f⁻¹⌋``, cryptarchia-v1-protocol.md
    Constants). At the defaults (W = 10, f = 1/30) the quotient is exactly 300 either way, so no
    committed result moves — but ``configs/absorption-window.yaml`` sweeps ``W`` and
    ``configs/block-rate.yaml`` sweeps ``f``, and at a non-integer ``W/f`` rounding would put the
    derived window a slot above the spec's.
    """
    return max(1, int(w_abs / f))


# --- Real-world inter-node network latency (per gossip link) ---------------
# A slot is SLOT_SECONDS = 1 s, so measured internet latencies (tens–hundreds of ms) are
# FRACTIONS of a slot. The values below are one-way, application-level latencies between two
# directly-peered nodes, bucketed by the geographic relationship of the peers — in a globally
# distributed node set a random peer is usually on another continent. (≈ RTT/2 from public
# latency measurements plus a little gossip processing/serialization overhead.) A block
# gossip-floods over the peering graph, so its end-to-end delay to a far node is the sum of
# a few such per-link latencies along the fastest path (Dijkstra) — see topology.py.
GEO_LATENCY_BANDS_SLOTS = (
    0.015,   # metro / same country            (~15 ms one-way)
    0.040,   # same continent, e.g. EU↔EU      (~40 ms)
    0.090,   # transatlantic, e.g. EU↔US-East  (~90 ms)
    0.200,   # antipodal, e.g. EU↔AU / EU↔JP   (~200 ms)
)
# Share of random peer links falling in each band for a globally distributed node set
# (NA/EU/Asia-weighted). Most peer pairs are cross-continent, hence the long-latency mass.
GEO_LATENCY_WEIGHTS = (0.15, 0.35, 0.35, 0.15)
# Mean one-way latency of a random global peer link under the mixture above (~0.078 slot,
# i.e. ~78 ms). Used to rescale the "geo" link-latency distribution to a requested mean.
GEO_LATENCY_MEAN_SLOTS = sum(
    b * w for b, w in zip(GEO_LATENCY_BANDS_SLOTS, GEO_LATENCY_WEIGHTS, strict=True)
)


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
