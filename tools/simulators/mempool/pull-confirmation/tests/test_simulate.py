"""The simulator runs the protocol; the closed forms claim to describe it."""

from __future__ import annotations

import random

import pytest

from pull_confirmation.model import Parameters, liveness_failure, security_failure
from pull_confirmation.simulate import (
    _Population,
    simulate,
    simulate_run,
    within_three_sigma,
)

TRIALS = 40_000


def base(**overrides) -> Parameters:
    kwargs = dict(
        n_providers=300,
        adversarial_fraction=0.33,
        sample_size=8,
        max_rounds=5,
        threshold=14,
        hold_probability=0.99,
    )
    kwargs.update(overrides)
    return Parameters(**kwargs)


@pytest.mark.parametrize("fraction,threshold", [(0.33, 14), (0.50, 20), (0.20, 8)])
def test_tagged_confirm_rate_matches_the_security_bound(fraction, threshold):
    params = base(adversarial_fraction=fraction, threshold=threshold)
    result = simulate(params, tagged=True, trials=TRIALS, seed=7)
    assert within_three_sigma(result.confirm_rate, security_failure(params), TRIALS)


@pytest.mark.parametrize(
    "hold,withholds,threshold", [(0.70, False, 28), (0.99, True, 24), (0.85, True, 18)]
)
def test_broadcast_confirm_rate_matches_the_liveness_bound(hold, withholds, threshold):
    params = base(hold_probability=hold, adversary_withholds=withholds, threshold=threshold)
    result = simulate(params, tagged=False, trials=TRIALS, seed=11)
    expected = 1.0 - liveness_failure(params)
    assert within_three_sigma(result.confirm_rate, expected, TRIALS)


def test_early_stopping_saves_queries_without_changing_the_outcome():
    # A generous threshold is met in the first round or two, so a run should
    # cost far fewer queries than the round budget allows — while still
    # confirming as often as the closed form says.
    params = base(threshold=6)
    result = simulate(params, tagged=False, trials=5_000, seed=3)
    assert result.mean_queries < params.total_sampled
    assert within_three_sigma(result.confirm_rate, 1.0 - liveness_failure(params), 5_000)


def test_a_run_never_queries_a_provider_twice():
    params = base(threshold=999_999, sample_size=8, max_rounds=5)
    # Threshold is unreachable, so the run uses its whole budget: the number of
    # queries is exactly the number of distinct providers it was allowed.
    rng = random.Random(0)
    outcome = simulate_run(params, tagged=False, rng=rng)
    assert outcome.queries == params.total_sampled
    assert not outcome.confirmed


def test_the_urn_is_restored_between_trials():
    params = base(n_providers=50)
    urn = _Population(params.n_providers, params.n_adversarial)
    before = list(urn._slots)
    rng = random.Random(0)
    for _ in range(20):
        simulate_run(params, tagged=False, rng=rng, population=urn)
    assert urn._slots == before


def test_an_inconsistent_urn_is_rejected():
    # Attestation decisions read the urn's adversary count while analytics read
    # params; letting them disagree would silently simulate a different threat
    # model than the closed forms are compared against.
    params = base(n_providers=50)
    assert params.n_adversarial != 20
    with pytest.raises(ValueError):
        simulate_run(
            params, tagged=True, rng=random.Random(0), population=_Population(50, 20)
        )


def test_results_are_reproducible_from_the_seed():
    params = base()
    first = simulate(params, tagged=True, trials=2_000, seed=42)
    second = simulate(params, tagged=True, trials=2_000, seed=42)
    assert first == second


def test_an_honest_network_never_confirms_a_tagged_transaction():
    params = base(adversarial_fraction=0.0)
    assert simulate(params, tagged=True, trials=2_000, seed=5).confirmed == 0
