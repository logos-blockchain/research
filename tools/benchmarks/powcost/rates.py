"""The rate table: seconds per candidate for a (puzzle, bucket) pair.

The one place puzzles and profiles meet. Everything else in this package treats them as
independent, which is what lets a new proof-of-work arrive as a definition plus measurements
rather than as a change to the cost arithmetic.

**The propagation rule, and why it is enforced rather than documented.** The table is sparse
and always will be -- nobody is going to benchmark every scheme on every machine. An empty
cell may be filled from a measured one in the SAME ROW by a device-class factor, because
device ratios were shown to be stable to within about 2% across a thirty-fold difficulty
range on the Equi-X data. It may NOT be filled across rows: the Pi-to-Apple ratio is 5.3 on
Equi-X and 6.2 on Poseidon2, so borrowing one for the other imports a 17% error with no
warning attached. :func:`seconds_per_candidate` therefore refuses a cross-puzzle fill instead
of performing one.
"""
from __future__ import annotations

from dataclasses import dataclass

from .profiles import BUCKETS
from .puzzles import PUZZLES


@dataclass(frozen=True)
class Rate:
    seconds_per_candidate: float   # one core, or one accelerator for the rig bucket
    cores_usable: int
    measured: bool
    source: str
    note: str = ""


# (puzzle key, bucket key) -> Rate. Absent means absent; nothing is imputed at import time.
TABLE: dict[tuple[str, str], Rate] = {
    ("poseidon2_reward", "rpi5"): Rate(
        165.658e-6, 4, True,
        "poseidon2, six runs on the target board, spreads under 0.1%, no throttling",
        "The calibration basis: one core of the deployment target."),
    ("poseidon2_reward", "apple"): Rate(
        26.6e-6, 10, True,
        "poseidon2 on an M4 Pro performance core, release build with link-time "
        "optimisation",
        "Performance cores only; a miner would not schedule onto the efficiency cores."),

    ("poseidon2_blend", "rpi5"): Rate(
        94.158e-6, 4, True,
        "poseidon2 on the target board",
        "The figure the admission threshold is calibrated against."),
    ("poseidon2_blend", "apple"): Rate(
        14.9e-6, 10, True,
        "poseidon2 on an M4 Pro performance core",
        "Naive; about 8.2 microseconds with the constant prefix precomputed."),

    ("equix", "rpi5"): Rate(
        22.4e-3, 4, True,
        "Equi-X benchmark, mining.csv, effort 3000",
        "Per attempt, not per solution: a solve yields about two."),
    ("equix", "apple"): Rate(
        4.26e-3, 10, True,
        "Equi-X benchmark on an M4 Pro, mining.csv, effort 3000", ""),
    ("equix", "intel"): Rate(
        3.92e-3, 24, True,
        "Equi-X benchmark on a Core Ultra 9 285HX, mining.csv, effort 3000", ""),

    # ESTIMATED, not measured -- `measured=False`, so anything that requires a benchmark
    # will still refuse this cell. Derived rather than guessed, and the derivation is:
    #
    #   Poseidon2 over BN254 at the specified parameters (rate 1, capacity 3, so state width
    #   t = 4; 8 external and 56 internal rounds; S-box x^5) costs 8*4 + 56 = 88 S-boxes at
    #   three multiplications each, plus 4 constant-multiplications per internal round for the
    #   diagonal linear layer: about 488 field multiplications per permutation. A reward
    #   candidate is seven permutations, so about 3,400 BN254 multiplications.
    #
    #   Published GPU throughput for BN254 is the input that matters, and it is poor: client
    #   GPUs fall BELOW 1 G BN254-ops/s, against >100 Gops/s for small fields such as M31,
    #   because a 254-bit non-special-form modulus maps badly onto GPU ALUs. Taking 1 Gops/s
    #   as the central case and 3 Gops/s as optimistic gives 293k-878k candidates a second per
    #   card, hence the 3.4e-6 s/candidate below (central case, per accelerator).
    #
    #   The cross-check that matters is ENERGY, not speed. At 450 W a card doing 293k
    #   candidates a second spends 1.54e-3 J per candidate against a Raspberry Pi 5 board's
    #   measured 3.65e-4 J -- so a GPU is roughly FOUR TIMES WORSE per candidate, and only
    #   beats the Pi 5 under an implausible 6 Gops/s. **A GPU rig is faster in absolute terms
    #   and not cheaper per unit of work**, which is the opposite of the usual assumption and
    #   follows from the curve choice rather than from anything in the mechanism.
    #
    #   Sources: Ingonyama ICICLE docs (Poseidon2 GPU implementation and "hash-many" mode);
    #   moven0831/field-ops-benchmarks (BN254 below 1 Gops/s client-side, M31 above 100);
    #   NVIDIA developer forum thread on a compute-bound 256-bit modular kernel reaching 82.5%
    #   SM throughput on sm_89; Poseidon2 paper (eprint 2023/323) for the round structure.
    #   REPLACE THIS with a real benchmark before relying on it: `make poseidon2` on a
    #   CUDA host is the missing measurement.
    ("poseidon2_reward", "gpurig"): Rate(
        3.4e-6, 6, False,
        "ESTIMATED from published BN254 field-multiplication throughput; see the derivation "
        "in rates.py. NOT a benchmark.",
        "About 12x a Raspberry Pi 5 board per accelerator in raw rate (73x for the six-card "
        "rig), and about 4x WORSE per "
        "joule. The estimate exists so the adversarial analysis can bound a GPU attacker "
        "rather than leave the cell empty; it must not be quoted as measured."),
}


class MissingRate(LookupError):
    """No rate for this pair, and none may honestly be invented for it."""


def seconds_per_candidate(puzzle_key: str, bucket_key: str,
                          allow_scaled: bool = True) -> tuple[float, str]:
    """Look a cell up, filling within the row if permitted. Returns (seconds, provenance).

    Raises :class:`MissingRate` rather than guessing, and returns the provenance alongside the
    figure so a caller can refuse an estimate where it needs a measurement.

    The accelerator bucket cannot acquire a rate by PROPAGATION -- no processor ratio predicts
    an accelerator. It now carries one for `poseidon2_reward` that was derived from published
    BN254 field-multiplication throughput instead, and it is flagged `measured=False`; see the
    derivation beside it in `TABLE`. Other accelerator cells remain absent.
    """
    if puzzle_key not in PUZZLES:
        raise KeyError(f"unknown puzzle {puzzle_key!r}")
    if bucket_key not in BUCKETS:
        raise KeyError(f"unknown bucket {bucket_key!r}")

    hit = TABLE.get((puzzle_key, bucket_key))
    if hit is not None:
        return hit.seconds_per_candidate, "measured" if hit.measured else "estimated"

    if not allow_scaled:
        raise MissingRate(f"no measured rate for {puzzle_key} on {bucket_key}")

    # Fill from another bucket in the SAME row, via a device factor taken from a row where
    # both buckets are measured. Never across rows.
    for other_puzzle in PUZZLES:
        if other_puzzle == puzzle_key:
            continue
        here = TABLE.get((other_puzzle, bucket_key))
        if here is None:
            continue
        for donor_bucket in BUCKETS:
            same_row = TABLE.get((puzzle_key, donor_bucket))
            other_row = TABLE.get((other_puzzle, donor_bucket))
            if same_row is None or other_row is None:
                continue
            # This IS a cross-puzzle inference, and it is exactly what the rule forbids.
            raise MissingRate(
                f"no rate for {puzzle_key} on {bucket_key}. A fill from {other_puzzle} is "
                f"available but is forbidden: device ratios differ between puzzles (5.3 "
                f"against 6.2 for Pi over Apple), so it would import a silent error. Measure "
                f"it, or invert the question into a break-even.")
    raise MissingRate(f"no rate for {puzzle_key} on {bucket_key}, and nothing to fill from")


def coverage_matrix() -> list[dict]:
    """Which cells are measured, which are empty. Printed at the point of use."""
    rows = []
    for pk in PUZZLES:
        row = {"puzzle": pk}
        for bk in BUCKETS:
            hit = TABLE.get((pk, bk))
            row[bk] = "measured" if hit and hit.measured else ("estimated" if hit else "--")
        rows.append(row)
    return rows
