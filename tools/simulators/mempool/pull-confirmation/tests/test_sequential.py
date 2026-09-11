"""The sequential rule is what the specification states; these pin what it gives."""

from __future__ import annotations

import pytest

from pull_confirmation.model import (
    Parameters,
    liveness_failure,
    majority_parameters,
    security_failure,
    sequential_confirmation_by_round,
    specification_parameters,
)
from pull_confirmation.simulate import simulate, within_three_sigma

TRIALS = 40_000


def test_a_single_check_reduces_to_the_fixed_majority_rule():
    # Eight rounds of sixteen reach the floor of 128 exactly at the last
    # round, so the only check is the fixed rule's, and the two must agree.
    fixed = majority_parameters(5000, 0.33333334, 16, 8, 0.99, True)
    seq = specification_parameters(5000, 0.33333334, 16, 8, 128, 0.99, True)
    assert security_failure(seq) == pytest.approx(security_failure(fixed), rel=1e-9)
    assert liveness_failure(seq) == pytest.approx(liveness_failure(fixed), rel=1e-9)


def test_the_operating_point_reproduces():
    p = specification_parameters(5000, 0.33333334, 16, 16, 128, 0.99, True)
    assert p.threshold == 65
    assert security_failure(p) == pytest.approx(3.15e-5, rel=2e-2)
    assert liveness_failure(p) == pytest.approx(1.41e-8, rel=5e-2)


def test_more_rounds_cost_security_and_buy_liveness():
    eight = specification_parameters(5000, 0.33333334, 16, 8, 128, 0.90, True)
    sixteen = specification_parameters(5000, 0.33333334, 16, 16, 128, 0.90, True)
    assert security_failure(sixteen) > security_failure(eight)
    assert liveness_failure(sixteen) < liveness_failure(eight) / 10


def test_liveness_no_longer_hinges_on_the_hold_probability():
    # Under the fixed rule a point of hold probability costs an order of
    # magnitude; under the sequential rule later draws outvote early refusals.
    fixed = [
        liveness_failure(majority_parameters(5000, 0.33333334, 16, 8, h, True))
        for h in (0.99, 0.90)
    ]
    seq = [
        liveness_failure(specification_parameters(5000, 0.33333334, 16, 16, 128, h, True))
        for h in (0.99, 0.90)
    ]
    assert fixed[1] / fixed[0] > 50
    assert seq[1] < fixed[1] / 50


def test_the_floor_caps_at_the_set():
    p = specification_parameters(90, 1 / 3, 16, 16, 128, 0.99, True)
    assert p.floor == 90
    assert p.threshold == 46


def test_threshold_must_be_the_majority_of_the_floor():
    with pytest.raises(ValueError):
        Parameters(5000, 1 / 3, 16, 16, 70, 0.99, True, min_sample=128)


def test_confirmation_by_round_sums_to_the_confirm_probability():
    p = specification_parameters(1000, 0.33333334, 16, 16, 128, 0.90, True)
    by_round = sequential_confirmation_by_round(p)
    assert len(by_round) == 16
    assert sum(by_round) == pytest.approx(1.0 - liveness_failure(p), rel=1e-9)
    # Nothing can fire before the majority of the floor is reachable.
    assert all(v == 0.0 for v in by_round[:4])


@pytest.mark.parametrize("tagged", [True, False])
def test_the_walk_matches_the_urn_simulation(tagged):
    p = specification_parameters(300, 0.33, 8, 10, 40, 0.85, True)
    analytic = security_failure(p) if tagged else 1.0 - liveness_failure(p)
    result = simulate(p, tagged=tagged, trials=TRIALS, seed=17)
    assert within_three_sigma(result.confirm_rate, analytic, TRIALS)


def test_as_specified_a_tagged_transaction_is_no_easier_than_the_walk_says():
    # Fresh draws each round with re-asks: a repeat adversarial draw adds no
    # new attester, so re-asking cannot help the attack.
    p = specification_parameters(300, 0.33, 8, 10, 40, 0.85, True)
    result = simulate(p, tagged=True, trials=TRIALS, seed=19, resample_each_round=True)
    assert result.confirm_rate <= security_failure(p) + 3 * (security_failure(p) / TRIALS) ** 0.5 + 3 / TRIALS


def test_as_specified_a_refusal_is_asked_again():
    # With a low hold probability and a tiny set, every provider is re-asked
    # until it attests, so the protocol as specified confirms where a single
    # pass over the set would not.
    p = specification_parameters(12, 0.25, 4, 16, 12, 0.5, True)
    result = simulate(p, tagged=False, trials=5_000, seed=23, resample_each_round=True)
    assert result.confirm_rate > 0.95
    assert result.mean_queries > 12
