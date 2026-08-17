"""Who mines, and who stops: participation decided by whether the work pays.

The simulator does not import the cost estimator. It takes the two numbers it needs per
device class as data -- how fast that class searches, and what one candidate costs it -- so
the estimator can move, be replaced, or be measured better without this module changing.
:func:`from_powcost` builds that data from the estimator when it is on the path, and is the
only place the two ever meet.

**The participation rule is the free-entry condition applied one miner at a time.** A miner
mines while the reward it keeps exceeds what the search costs it:

    reward_per_claim - claim_fee  >  candidates_per_claim * cost_per_candidate

No fixed point is needed, because the condition does not reference the miner's share of the
field -- only the difficulty, which the controller supplies. That is also what makes the
population mixed rather than degenerate: two miners facing the same difficulty differ in
``cost_per_candidate``, so the cheap one stays in after the expensive one leaves.

**The loop this closes.** Miners leaving cuts the hashrate; the controller answers by
relaxing the target; a relaxed target means fewer candidates per claim, so the work costs
less and the miner who just left can afford to return. The difficulty therefore settles
where the *cheapest available* class breaks even, and every costlier class is excluded while
the network sits in equilibrium. That is the affordability floor, and it is a property of the
frontier rather than of any protocol bound.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import FIELD_MODULUS, Config


@dataclass(frozen=True)
class DeviceClass:
    """What the simulator needs to know about a device bucket. Two numbers and a name."""

    key: str
    candidates_per_second: float      # all usable cores of one machine
    cost_per_candidate_usd: float     # at a stated electricity price and power basis
    basis: str = "total"
    note: str = ""


def from_powcost(puzzle: str, electricity_price_per_kwh: float,
                 basis: str = "total", tools_dir: str | None = None) -> list[DeviceClass]:
    """Build device classes from the cost estimator, for buckets it can actually price.

    Buckets with no measured rate are **omitted rather than imputed**, so a mix built here
    covers only what has been measured. That is a real limitation of any conclusion drawn
    from it and callers should say which classes were available.
    """
    import sys
    from pathlib import Path

    root = Path(tools_dir) if tools_dir else Path(__file__).resolve().parents[5] / "tools"
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from powcost import kernel, profiles                      # noqa: PLC0415
    from powcost.kernel import PowerBasis                     # noqa: PLC0415
    from powcost.rates import TABLE, MissingRate              # noqa: PLC0415

    want = PowerBasis.TOTAL if basis == "total" else PowerBasis.MARGINAL
    out = []
    for bucket in profiles.BUCKETS:
        rate = TABLE.get((puzzle, bucket))
        if rate is None:
            continue
        try:
            cost = kernel.cost_per_candidate(puzzle, bucket, electricity_price_per_kwh, want)
        except (MissingRate, KeyError):
            continue
        out.append(DeviceClass(
            key=bucket,
            candidates_per_second=rate.cores_usable / rate.seconds_per_candidate,
            cost_per_candidate_usd=cost,
            basis=basis,
            note=rate.source,
        ))
    return out


def candidates_per_claim(difficulty_target: int) -> float:
    """Expected candidates per winning claim at the current target."""
    if difficulty_target <= 0:
        return float("inf")
    return FIELD_MODULUS / difficulty_target


def work_cost_per_claim_usd(difficulty_target: int, cost_per_candidate_usd: np.ndarray
                            ) -> np.ndarray:
    """What winning one claim costs each miner in electricity."""
    return candidates_per_claim(difficulty_target) * cost_per_candidate_usd


def mines(cfg: Config, reward_per_claim: int, difficulty_target: int,
          cost_per_candidate_usd: np.ndarray, token_price_usd: float) -> np.ndarray:
    """Which miners find the work worth doing, one entry per node.

    The reward is a token quantity and the cost is a currency quantity, so the two only meet
    through a token price. That price is the one exogenous input the affordability question
    cannot avoid, which is why it is a scenario axis here and reported as a break-even
    everywhere else.
    """
    net_tokens = max(0, reward_per_claim - cfg.claim_fee) / cfg.base_units_per_lgo
    if net_tokens <= 0 or token_price_usd <= 0:
        return np.zeros(cost_per_candidate_usd.shape, dtype=bool)
    net_usd = net_tokens * token_price_usd
    return work_cost_per_claim_usd(difficulty_target, cost_per_candidate_usd) < net_usd


def break_even_token_price(cfg: Config, reward_per_claim: int, difficulty_target: int,
                           cost_per_candidate_usd: float) -> float:
    """Token price below which this class stops mining at this difficulty.

    | ``break_even_token_price = candidates_per_claim * cost_per_candidate / (reward_per_claim - claim_fee)``

    The inversion the report prefers: rather than assume what a token is worth, state the
    value at which the conclusion changes.
    """
    net_tokens = max(0, reward_per_claim - cfg.claim_fee) / cfg.base_units_per_lgo
    if net_tokens <= 0:
        return float("inf")
    return candidates_per_claim(difficulty_target) * cost_per_candidate_usd / net_tokens


def affordability_floor_target(cfg: Config, reward_per_claim: int,
                               cheapest_cost_per_candidate_usd: float,
                               token_price_usd: float) -> float:
    """The difficulty target free entry settles on, given the cheapest class available.

    | ``equilibrium_difficulty = field_modulus * cost_per_candidate / (reward_per_claim - claim_fee)``

    Expressed as a target rather than a bound: the controller can relax no further than the
    point where the cheapest miner breaks even, because past it that miner re-enters and
    pushes back. Everything costlier than the cheapest class is excluded there.
    """
    net_tokens = max(0, reward_per_claim - cfg.claim_fee) / cfg.base_units_per_lgo
    if net_tokens <= 0 or token_price_usd <= 0:
        return float("inf")
    net_usd = net_tokens * token_price_usd
    return FIELD_MODULUS * cheapest_cost_per_candidate_usd / net_usd
