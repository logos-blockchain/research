"""Puzzles: what one unit of search is, and how difficulty turns into a count of them.

A puzzle owns everything that changes when you swap one proof-of-work for another, so that
the kernel owns nothing that does. Adding a scheme is a definition here plus a rate
measurement per bucket -- not a change to the cost arithmetic.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

FIELD_MODULUS = 21888242871839275222246405745257275088548364400416034343698204186575808495617


class CostShape(str, Enum):
    """Where the energy goes. The kernel implements the first; the second is declared so
    that admitting it later is a new branch rather than a rewrite."""

    PER_CANDIDATE = "per-candidate"   # compute puzzles: energy scales with attempts
    PER_TIME = "per-time"             # proof-of-space: a held plot draws power while idle


class Parallelism(str, Enum):
    LINEAR = "linear"        # attempts are independent; cores multiply throughput
    MEASURED = "measured"    # scaling is sublinear and has been measured per bucket
    NONE = "none"            # inherently sequential; cores do not help at all


@dataclass(frozen=True)
class Puzzle:
    key: str
    label: str
    cost_shape: CostShape
    parallelism: Parallelism
    solutions_per_attempt: float
    setup_per_challenge_seconds: float
    note: str

    def candidates_per_claim(self, difficulty_target: int) -> float:
        """Expected candidates tried per winning claim.

        For a threshold puzzle this is the field over the target. A scheme whose solve
        yields several candidate solutions at once divides that count, which is why
        ``solutions_per_attempt`` is a field rather than an assumption.
        """
        if difficulty_target <= 0:
            return float("inf")
        return (FIELD_MODULUS / difficulty_target) / self.solutions_per_attempt

    @staticmethod
    def quantiles(mean: float) -> dict[str, float]:
        """Where the search actually lands, not just where it lands on average.

        The wait is geometric, so it is near-exponential in the mean: half of all searches
        finish inside 0.69 of it and one in twenty takes three times as long. An affordability
        claim quoted at the mean understates what a participant waiting for one message
        experiences, which is the case the tail exists to describe.
        """
        import math
        return {
            "p50": mean * math.log(2),
            "mean": mean,
            "p95": mean * math.log(20),
            "p99": mean * math.log(100),
        }


POSEIDON2_REWARD = Puzzle(
    key="poseidon2_reward",
    label="Poseidon2 over BN254, reward branch",
    cost_shape=CostShape.PER_CANDIDATE,
    parallelism=Parallelism.LINEAR,
    solutions_per_attempt=1.0,
    setup_per_challenge_seconds=0.0,
    note="The branch that ships. Seven permutations per candidate: the claim's ticket keeps "
         "its key derivation because the note must pay to a public key. An arithmetic hash "
         "with mature accelerator kernels, which is why the accelerator bucket matters most "
         "for this puzzle and least for Equi-X.",
)

POSEIDON2_BLEND = Puzzle(
    key="poseidon2_blend",
    label="Poseidon2 over BN254, admission branch",
    cost_shape=CostShape.PER_CANDIDATE,
    parallelism=Parallelism.LINEAR,
    solutions_per_attempt=1.0,
    setup_per_challenge_seconds=0.0,
    note="One three-input hash. Cheaper than the reward candidate since it derives no key. "
         "A constant prefix can be absorbed once per epoch, worth about 1.8x, which bounds "
         "the ALGORITHMIC edge only -- implementation headroom is unmeasured.",
)

EQUIX = Puzzle(
    key="equix",
    label="Equi-X",
    cost_shape=CostShape.PER_CANDIDATE,
    parallelism=Parallelism.MEASURED,
    solutions_per_attempt=2.0,
    setup_per_challenge_seconds=0.0,
    note="Acceleration-resistant candidate, out of scope for the shipping revision. A solve "
         "yields about two solutions per attempt (measured 1.97-2.17), so effort and attempt "
         "count differ. Compiles a program per challenge, and its multi-core scaling was "
         "measured between 0.75 and 1.24 rather than assumed linear.",
)

PUZZLES: dict[str, Puzzle] = {
    p.key: p for p in (POSEIDON2_REWARD, POSEIDON2_BLEND, EQUIX)
}
