"""The cost arithmetic: seconds and joules per candidate, per claim, and what they cost.

Owns nothing puzzle-specific and nothing device-specific -- those live in
:mod:`powcost.puzzles` and :mod:`powcost.profiles`, and meet only in :mod:`powcost.rates`.
So this module never changes when a proof-of-work or a machine is added.

Two power bases are carried throughout and are never mixed:

**marginal** -- draw above idle, for a participant whose machine was already running. This
is what the admission on-ramp costs someone who owns a laptop.

**total** -- whole-platform draw at the wall, for a dedicated miner or an attacker, whose
machine exists only to do this. This is what sets the free-entry frontier.

Which one applies is a property of the question, not of the device, so the caller states it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .profiles import BUCKETS, Profile
from .puzzles import PUZZLES, Puzzle
from .rates import MissingRate, seconds_per_candidate

JOULES_PER_KWH = 3.6e6


class PowerBasis(str, Enum):
    MARGINAL = "marginal"
    TOTAL = "total"


@dataclass(frozen=True)
class Cost:
    """What one claim costs on one machine, in every unit that matters."""

    puzzle: str
    bucket: str
    basis: str
    candidates_per_claim: float
    seconds_per_claim_one_core: float
    seconds_per_claim_all_cores: float
    joules_per_candidate: float
    joules_per_claim: float
    money_per_claim: float
    provenance: str

    @property
    def candidates_per_joule(self) -> float:
        """The efficiency frontier's unit. Under free entry this is what decides who mines."""
        return 1.0 / self.joules_per_candidate if self.joules_per_candidate else float("inf")


def _watts(profile: Profile, basis: PowerBasis) -> tuple[float, int, str]:
    """Draw and the core count it corresponds to, for the requested basis."""
    if basis is PowerBasis.MARGINAL:
        watts, why = profile.marginal_watts_per_core()
        if watts is None:
            raise MissingRate(
                f"{profile.key}: no marginal draw available -- {why}. Supply a package-basis "
                f"idle reading rather than substituting a figure from another basis.")
        return watts, 1, f"marginal, {why}"
    total, why = profile.total_watts_all_cores()
    if total is None:
        raise MissingRate(f"{profile.key}: no total draw available -- {why}")
    return total, profile.cores, f"total, {why}"


def cost_per_claim(puzzle_key: str, bucket_key: str, difficulty_target: int,
                   electricity_price_per_kwh: float,
                   basis: PowerBasis = PowerBasis.TOTAL) -> Cost:
    """Seconds, joules and money for one claim, on one bucket, at one difficulty."""
    puzzle: Puzzle = PUZZLES[puzzle_key]
    profile: Profile = BUCKETS[bucket_key]

    per_candidate, rate_prov = seconds_per_candidate(puzzle_key, bucket_key)
    watts, cores_at_that_draw, power_prov = _watts(profile, basis)

    candidates = puzzle.candidates_per_claim(difficulty_target)
    seconds_one = candidates * per_candidate
    seconds_all = seconds_one / max(1, profile.cores)

    # Energy is draw times time on the same number of cores, so the core count cancels for
    # the total basis and does not for the marginal one -- which is the point of carrying both.
    joules_per_candidate = watts * per_candidate / max(1, cores_at_that_draw)
    joules = joules_per_candidate * candidates

    return Cost(
        puzzle=puzzle_key, bucket=bucket_key, basis=basis.value,
        candidates_per_claim=candidates,
        seconds_per_claim_one_core=seconds_one,
        seconds_per_claim_all_cores=seconds_all,
        joules_per_candidate=joules_per_candidate,
        joules_per_claim=joules,
        money_per_claim=joules / JOULES_PER_KWH * electricity_price_per_kwh,
        provenance=f"rate {rate_prov}; power {power_prov}",
    )


def cost_per_candidate(puzzle_key: str, bucket_key: str,
                       electricity_price_per_kwh: float,
                       basis: PowerBasis = PowerBasis.TOTAL) -> float:
    """The tokenomics model's ``cost_per_candidate``: money for one attempt.

    | ``cost_per_candidate = joules_per_candidate / joules_per_kwh * electricity_price``

    This is the quantity the report lists as unknown and the free-entry equilibrium turns on.
    It is independent of difficulty, which is why it is the right thing to hand the model:
    difficulty scales the count of candidates, never the price of one.
    """
    profile = BUCKETS[bucket_key]
    per_candidate, _ = seconds_per_candidate(puzzle_key, bucket_key)
    watts, cores, _ = _watts(profile, basis)
    joules = watts * per_candidate / max(1, cores)
    return joules / JOULES_PER_KWH * electricity_price_per_kwh


def frontier(puzzle_key: str, basis: PowerBasis = PowerBasis.TOTAL) -> list[dict]:
    """Candidates per joule for every bucket that has a rate. Most efficient first.

    Under free entry the cheapest bucket sets the difficulty and every less efficient bucket
    mines at a loss, so this ordering -- not any absolute cost -- is what decides who can
    participate. Buckets with no rate are reported as gaps rather than omitted, because an
    absent row here is a claim the model cannot make, and that should be visible.
    """
    rows = []
    for bucket_key, profile in BUCKETS.items():
        try:
            per_candidate, prov = seconds_per_candidate(puzzle_key, bucket_key)
            watts, cores, power_prov = _watts(profile, basis)
        except (MissingRate, KeyError) as e:
            rows.append(dict(bucket=bucket_key, joules_per_candidate=None,
                             gap=str(e).split(".")[0]))
            continue
        joules = watts * per_candidate / max(1, cores)
        rows.append(dict(bucket=bucket_key, joules_per_candidate=joules,
                         candidates_per_joule=1.0 / joules,
                         provenance=f"{prov}; {power_prov}", gap=None))
    known = [r for r in rows if r["joules_per_candidate"] is not None]
    gaps = [r for r in rows if r["joules_per_candidate"] is None]
    known.sort(key=lambda r: r["joules_per_candidate"])
    if known:
        best = known[0]["joules_per_candidate"]
        for r in known:
            r["times_worse_than_best"] = r["joules_per_candidate"] / best
    return known + gaps


def break_even_accelerator_efficiency(puzzle_key: str, bucket_key: str,
                                      basis: PowerBasis = PowerBasis.TOTAL) -> float:
    """Candidates per joule an unmeasured bucket must reach to price ``bucket_key`` out.

    The accelerator rate is the largest gap in the table and no processor ratio predicts it,
    so it is inverted rather than guessed: instead of asserting what an accelerator achieves,
    state the efficiency at which a given bucket stops being able to compete. The claim then
    rests on a measurement someone can go and take, not on a number invented here.
    """
    profile = BUCKETS[bucket_key]
    per_candidate, _ = seconds_per_candidate(puzzle_key, bucket_key)
    watts, cores, _ = _watts(profile, basis)
    return 1.0 / (watts * per_candidate / max(1, cores))
