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
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .model import Parameters

__all__ = ["RunOutcome", "SimulationResult", "simulate_run", "simulate"]


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

    __slots__ = ("_slots", "_swaps", "n_adversarial")

    def __init__(self, n_providers: int, n_adversarial: int) -> None:
        self._slots = list(range(n_providers))
        self._swaps: list[tuple[int, int]] = []
        self.n_adversarial = n_adversarial

    def draw(self, count: int, rng: random.Random) -> list[int]:
        drawn = []
        size = len(self._slots)
        for i in range(min(count, size)):
            j = rng.randrange(i, size)
            if i != j:
                self._slots[i], self._slots[j] = self._slots[j], self._slots[i]
                self._swaps.append((i, j))
            drawn.append(self._slots[i])
        return drawn

    def reset(self) -> None:
        for i, j in reversed(self._swaps):
            self._slots[i], self._slots[j] = self._slots[j], self._slots[i]
        self._swaps.clear()

    def is_adversarial(self, provider: int) -> bool:
        return provider < self.n_adversarial


def simulate_run(
    params: Parameters,
    *,
    tagged: bool,
    rng: random.Random,
    population: _Population | None = None,
) -> RunOutcome:
    """One node's attempt to confirm one transaction.

    ``tagged`` selects the scenario. Under a tagged transaction the adversary
    delivered it to this node alone, so no honest provider holds it and only
    adversarial providers can attest. Otherwise the transaction was genuinely
    broadcast, and any provider holds it with ``hold_probability`` — subject to
    the adversary withholding, if that is being modelled.

    ``population`` may be supplied to reuse the urn across trials; it is reset
    before returning either way.
    """
    urn = population if population is not None else _Population(
        params.n_providers, params.n_adversarial
    )

    attestations = 0
    queries = 0
    rounds_used = 0

    try:
        # Providers are drawn without replacement across the whole run: a node
        # does not re-query one it has already asked about this transaction.
        order = urn.draw(params.total_sampled, rng)
        cursor = 0

        for round_index in range(1, params.max_rounds + 1):
            if cursor >= len(order):
                break
            rounds_used = round_index
            batch = order[cursor : cursor + params.sample_size]
            cursor += len(batch)

            for provider in batch:
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
                    attestations += 1
                    if attestations >= params.threshold:
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
        outcome = simulate_run(params, tagged=tagged, rng=rng, population=urn)
        confirmed += outcome.confirmed
        total_queries += outcome.queries
        total_rounds += outcome.rounds

    return SimulationResult(
        trials=trials,
        confirmed=confirmed,
        mean_queries=total_queries / trials if trials else 0.0,
        mean_rounds=total_rounds / trials if trials else 0.0,
    )
