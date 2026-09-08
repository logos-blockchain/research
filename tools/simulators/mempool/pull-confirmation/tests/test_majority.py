"""The majority rule is what the specification states; these pin what it gives."""

from __future__ import annotations

import pytest

from pull_confirmation.calibrate import Target, calibrate_sample
from pull_confirmation.model import (
    Parameters,
    liveness_failure,
    majority_parameters,
    majority_threshold,
    security_failure,
)
from pull_confirmation.simulate import simulate


@pytest.mark.parametrize("sample,expected", [(1, 1), (2, 2), (127, 64), (128, 65), (300, 151)])
def test_majority_threshold_is_more_than_half(sample, expected):
    assert majority_threshold(sample) == expected
    assert majority_threshold(sample) > sample / 2
    assert majority_threshold(sample) - 1 <= sample / 2


def test_majority_parameters_cap_the_sample_at_the_set():
    p = majority_parameters(90, 1 / 3, 16, 8, 0.99, True)
    assert p.total_sampled == 90
    assert p.threshold == 46


def test_the_operating_point_reproduces():
    p = majority_parameters(5000, 0.33333334, 16, 8, 0.99, True)
    assert p.threshold == 65
    assert security_failure(p) == pytest.approx(2.755e-5, rel=1e-2)
    assert liveness_failure(p) == pytest.approx(1.151e-4, rel=1e-2)


def test_a_smaller_set_is_no_worse():
    # 128 of 300 is nearly a census, so both bounds tighten.
    large = majority_parameters(5000, 0.33333334, 16, 8, 0.99, True)
    small = majority_parameters(300, 0.33333334, 16, 8, 0.99, True)
    assert security_failure(small) < security_failure(large)
    assert liveness_failure(small) < liveness_failure(large)


def test_calibrate_sample_meets_its_targets():
    base = Parameters(5000, 0.33333334, 1, 1, 1, 0.99, True)
    target = Target(3e-5, 2e-4)
    result = calibrate_sample(base, target)
    assert result is not None
    assert result.security_failure <= target.max_security_failure
    assert result.liveness_failure <= target.max_liveness_failure
    assert result.params.threshold == majority_threshold(result.params.total_sampled)


def test_resampling_each_round_confirms_less_often_on_a_small_set():
    # The sampling an earlier specification described: draws are not distinct,
    # so a small set is asked far fewer distinct providers than the budget.
    # Under the majority rule the loss is modest — a few tenths of a percent
    # at N=500 — where the earlier absolute threshold of 133 lost a third of
    # all transactions there. The window rule is kept because it makes the
    # closed forms exact, not because the majority rule cannot survive without it.
    p = majority_parameters(500, 0.33333334, 16, 8, 0.99, True)
    urn = simulate(p, tagged=False, trials=20000, seed=5)
    again = simulate(p, tagged=False, trials=20000, seed=5, resample_each_round=True)
    assert again.confirm_rate < urn.confirm_rate
    assert again.mean_queries < urn.mean_queries
