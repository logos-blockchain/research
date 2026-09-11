"""Monte-Carlo simulation of the round-based pull protocol.

The closed forms in :mod:`.model` collapse a run into a single draw of
``sample_size * max_rounds`` providers. The protocol does not actually work that
way: it queries in rounds, accumulates attestations across them, and stops as
soon as the threshold is met. This module runs the protocol as written, so that
the analytic model is checked against the mechanism rather than against itself.

Early stopping cannot change *whether* a run confirms — a run confirms iff its
draws contain enough attesters, and stopping early only skips draws that were
never going to be needed. It does change how many queries a run costs, which is
the number the deployment cares about and which the closed form does not give.

The sequential rule (``Parameters.min_sample > 0``) is also run as written:
after every round the run confirms when more than half of everyone asked so
far attests, the denominator floored at ``min_sample``, and a provider that
refused may be asked again when the sampling draws it again.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .model import Parameters

__all__ = ["RunOutcome", "SimulationResult", "simulate_run", "simulate", "within_three_sigma"]


def within_three_sigma(observed: float, expected: float, trials: int) -> bool:
    """Whether a simulated proportion agrees with an analytic one.

    Three sigma of a binomial proportion, floored at ``3 / trials`` so that a
    comparison against a near-zero analytic value does not demand an exactness
    the trial count cannot deliver. This predicate is the single acceptance
    criterion for model-vs-simulator agreement — ``make verify`` and the test
    suite both import it, so a change to the tolerance changes both together.
    """
    sigma = (max(expected, 1e-9) * (1 - min(expected, 1.0)) / trials) ** 0.5
    return abs(observed - expected) <= max(3 * sigma, 3.0 / trials)


@dataclass(frozen=True)
class RunOutcome:
    confirmed: bool
    attestations: int
    queries: int
    rounds: int


@dataclass(frozen=True)
class SimulationResult:
    trials: int
    confirmed: int
    mean_queries: float
    mean_rounds: float

    @property
    def confirm_rate(self) -> float:
        return self.confirmed / self.trials if self.trials else 0.0


class _Population:
    """A reusable urn supporting sampling without replacement in O(drawn).

    A trial only ever queries ``total_sampled`` providers, so shuffling the whole
    declaration set per trial would spend O(n_providers) to look at a few tens of
    them — at realistic set sizes that dominates the run. Instead a partial
    Fisher-Yates pass draws exactly what is asked for, and :meth:`reset` undoes
    the swaps in reverse so the same array serves every trial.

    Provider ``i`` is adversarial iff ``i < n_adversarial``. Which indices those
    are does not matter, only how many are drawn, because providers are
    exchangeable under uniform sampling.
    """

    __slots__ = ("_slots", "_swaps", "_drawn", "n_adversarial")

    def __init__(self, n_providers: int, n_adversarial: int) -> None:
        self._slots = list(range(n_providers))
        self._swaps: list[tuple[int, int]] = []
        self._drawn = 0
        self.n_adversarial = n_adversarial

    def __len__(self) -> int:
        return len(self._slots)

    def draw(self, count: int, rng: random.Random) -> list[int]:
        """Draw the next ``count`` providers, continuing where the last draw left off.

        Successive calls within one trial keep drawing without replacement, so a
        round-by-round caller pays only for the providers it actually queries —
        a trial that confirms in round one does one round's worth of urn work.
        """
        drawn = []
        size = len(self._slots)
        start = self._drawn
        for i in range(start, min(start + count, size)):
            j = rng.randrange(i, size)
            if i != j:
                self._slots[i], self._slots[j] = self._slots[j], self._slots[i]
                self._swaps.append((i, j))
            drawn.append(self._slots[i])
        self._drawn += len(drawn)
        return drawn

    def reset(self) -> None:
        for i, j in reversed(self._swaps):
            self._slots[i], self._slots[j] = self._slots[j], self._slots[i]
        self._swaps.clear()
        self._drawn = 0

    def is_adversarial(self, provider: int) -> bool:
        return provider < self.n_adversarial


def simulate_run(
    params: Parameters,
    *,
    tagged: bool,
    rng: random.Random,
    population: _Population | None = None,
    resample_each_round: bool = False,
) -> RunOutcome:
    """One node's attempt to confirm one transaction.

    ``tagged`` selects the scenario. Under a tagged transaction the adversary
    delivered it to this node alone, so no honest provider holds it and only
    adversarial providers can attest. Otherwise the transaction was genuinely
    broadcast, and any provider holds it with ``hold_probability`` — subject to
    the adversary withholding, if that is being modelled.

    ``population`` may be supplied to reuse the urn across trials; it is reset
    before returning either way.

    ``resample_each_round`` draws afresh from the whole set every round, which
    is what the specification says. Under the fixed rule a provider drawn twice
    is not asked again, so the draws are not distinct and the effective sample
    shrinks with the set — the closed forms assume the urn and overstate
    liveness, which this mode measures. Under the sequential rule a provider
    that refused is asked again when it is drawn again and rolls its hold
    afresh, as the specification's re-query does; the urn is then the model's
    approximation and this mode is the protocol.
    """
    if population is not None and (
        len(population) != params.n_providers
        or population.n_adversarial != params.n_adversarial
    ):
        raise ValueError(
            "population urn disagrees with params: "
            f"urn ({len(population)}, {population.n_adversarial}) vs "
            f"params ({params.n_providers}, {params.n_adversarial}); "
            "attestation decisions would silently use a different adversary share"
        )

    urn = population if population is not None else _Population(
        params.n_providers, params.n_adversarial
    )

    attestations = 0
    queries = 0
    rounds_used = 0

    asked: set[int] = set()
    attested: set[int] = set()
    try:
        # Providers are drawn without replacement across the whole run — a node
        # does not re-query one it has already asked about this transaction —
        # and one round's batch at a time, so early stopping skips urn work for
        # providers that were never going to be queried.
        for round_index in range(1, params.max_rounds + 1):
            if resample_each_round:
                batch = rng.sample(range(params.n_providers), min(params.sample_size, params.n_providers))
            else:
                remaining = params.total_sampled - queries
                if remaining <= 0:
                    break
                batch = urn.draw(min(params.sample_size, remaining), rng)
            if not batch:
                break
            rounds_used = round_index

            for provider in batch:
                if resample_each_round:
                    # The fixed rule never re-asks; the sequential rule re-asks
                    # anyone who has not attested, as the specification does.
                    if provider in (attested if params.sequential else asked):
                        continue
                    asked.add(provider)
                queries += 1
                is_adversarial = urn.is_adversarial(provider)
                if tagged:
                    # Only the adversary holds it, and it always answers: making
                    # the transaction confirm is the whole objective.
                    attests = is_adversarial
                elif is_adversarial and params.adversary_withholds:
                    attests = False
                else:
                    attests = rng.random() < params.hold_probability
                if attests:
                    attested.add(provider)
                    attestations = len(attested) if resample_each_round else attestations + 1
                    if not params.sequential and attestations >= params.threshold:
                        return RunOutcome(True, attestations, queries, round_index)

            if params.sequential:
                # The specification's test, applied once a round to the
                # answers in hand: more than half of everyone who answered,
                # the denominator floored at PULL_SAMPLE. Confirmation is
                # recorded and never revisited.
                answered = len(asked) if resample_each_round else queries
                if 2 * attestations > max(answered, params.floor):
                    return RunOutcome(True, attestations, queries, round_index)

        return RunOutcome(False, attestations, queries, rounds_used)
    finally:
        urn.reset()


def simulate(
    params: Parameters,
    *,
    tagged: bool,
    trials: int,
    seed: int = 0,
    resample_each_round: bool = False,
) -> SimulationResult:
    """Repeat :func:`simulate_run` and summarise.

    The seed is explicit and the generator is local, so a result is reproducible
    from the parameters and the seed alone.
    """
    rng = random.Random(seed)
    urn = _Population(params.n_providers, params.n_adversarial)
    confirmed = 0
    total_queries = 0
    total_rounds = 0

    for _ in range(trials):
        outcome = simulate_run(
            params, tagged=tagged, rng=rng, population=urn,
            resample_each_round=resample_each_round,
        )
        confirmed += outcome.confirmed
        total_queries += outcome.queries
        total_rounds += outcome.rounds

    return SimulationResult(
        trials=trials,
        confirmed=confirmed,
        mean_queries=total_queries / trials if trials else 0.0,
        mean_rounds=total_rounds / trials if trials else 0.0,
    )
