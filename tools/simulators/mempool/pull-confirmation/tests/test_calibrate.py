"""Calibration must return something that actually meets the targets it was given.

The search bisects on an assumption — that *stable* feasibility, once reached, is
not lost by sampling more — so that assumption is tested here rather than
trusted, alongside the reason the weaker assumption it replaced is false.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from pull_confirmation.calibrate import (
    Target,
    calibrate,
    feasible_thresholds,
    first_feasible_sample,
)
from pull_confirmation.model import Parameters, liveness_failure, security_failure


def base(**overrides) -> Parameters:
    kwargs = dict(
        n_providers=1000,
        adversarial_fraction=0.33,
        sample_size=1,
        max_rounds=1,
        threshold=1,
        hold_probability=0.99,
    )
    kwargs.update(overrides)
    return Parameters(**kwargs)


TARGET = Target(1e-9, 1e-6)


def test_result_meets_both_targets():
    result = calibrate(base(), TARGET)
    assert result is not None
    assert result.security_failure <= TARGET.max_security_failure
    assert result.liveness_failure <= TARGET.max_liveness_failure


def test_result_is_the_smallest_stable_sample():
    result = calibrate(base(), TARGET, stability_window=4)
    assert result is not None
    smaller = replace(base(), sample_size=result.params.total_sampled - 1)
    assert feasible_thresholds(smaller, TARGET) == []


@pytest.mark.parametrize("withholds", [False, True])
def test_raw_feasibility_is_not_monotone(withholds):
    # This is why calibrate() bisects on stability rather than on feasibility.
    # Both bounds are thresholds on an integer count and they step at different
    # sample sizes, so where the window first opens it can close again for a
    # step. Documented as a test because it looks like a bug when first met.
    params = base(adversary_withholds=withholds)
    seen_feasible = False
    holes = []
    for total in range(1, 260):
        probe = replace(params, sample_size=total)
        ok = bool(feasible_thresholds(probe, TARGET))
        if ok:
            seen_feasible = True
        elif seen_feasible:
            holes.append(total)
    assert holes, "expected at least one isolated infeasible sample above the first feasible one"


@pytest.mark.parametrize("withholds", [False, True])
def test_stable_feasibility_is_monotone(withholds):
    # calibrate() bisects on this predicate, so it must not lose feasibility once
    # gained — otherwise the bisection could return a sample that is not minimal.
    params = base(adversary_withholds=withholds)

    def stable(total: int) -> bool:
        return all(
            bool(feasible_thresholds(replace(params, sample_size=total + offset), TARGET))
            for offset in range(4)
        )

    first_stable = None
    for total in range(1, 256):
        ok = stable(total)
        if ok and first_stable is None:
            first_stable = total
        if first_stable is not None:
            assert ok, f"stable feasibility lost again at sample {total}"
    assert first_stable is not None


def test_the_stable_answer_is_at_least_the_first_feasible_one():
    stable = calibrate(base(), TARGET)
    first = first_feasible_sample(base(), TARGET)
    assert stable is not None and first is not None
    assert stable.total_queries >= first


@pytest.mark.parametrize("providers", [60, 100, 120])
def test_feasible_regions_near_the_ceiling_are_found(providers):
    # Regression: the doubling bracket used to test only powers of two and
    # treated any probe beyond the ceiling as infeasible, so a first stable
    # sample between the last power of two and the set size was reported as
    # None even though a scan finds it.
    params = base(n_providers=providers, adversary_withholds=True)
    first = first_feasible_sample(params, TARGET)
    result = calibrate(params, TARGET)
    if first is None:
        assert result is None
    else:
        assert result is not None, f"calibrate missed feasible samples at N={providers}"
        assert result.total_queries >= first


def test_the_result_never_exceeds_the_set_size():
    result = calibrate(base(n_providers=120, adversary_withholds=True), TARGET)
    assert result is not None
    assert result.total_queries <= 120


def test_withholding_costs_more_than_cooperation():
    cooperating = calibrate(base(), TARGET)
    withholding = calibrate(base(adversary_withholds=True), TARGET)
    assert cooperating is not None and withholding is not None
    assert withholding.total_queries > cooperating.total_queries


def test_a_majority_adversary_is_infeasible():
    # Above one half there is no window: the threshold cannot be both above what
    # the adversary alone can supply and below what the honest set can.
    assert calibrate(base(adversarial_fraction=0.6, adversary_withholds=True), TARGET) is None


def test_cost_grows_with_the_adversarial_fraction():
    costs = []
    for fraction in (0.10, 0.20, 0.33, 0.40):
        result = calibrate(base(adversarial_fraction=fraction), TARGET)
        assert result is not None
        costs.append(result.total_queries)
    assert costs == sorted(costs)


def test_a_slower_network_costs_more():
    # A lower hold probability means honest providers are more often asked
    # before the transaction reached them, which eats the liveness margin.
    fast = calibrate(base(hold_probability=0.99), TARGET)
    slow = calibrate(base(hold_probability=0.80), TARGET)
    assert fast is not None and slow is not None
    assert slow.total_queries > fast.total_queries


def test_feasible_thresholds_is_contiguous():
    probe = replace(base(), sample_size=60)
    options = feasible_thresholds(probe, TARGET)
    assert options == list(range(options[0], options[-1] + 1))


def test_reported_probabilities_match_a_fresh_evaluation():
    result = calibrate(base(), TARGET)
    assert result is not None
    assert result.security_failure == pytest.approx(security_failure(result.params))
    assert result.liveness_failure == pytest.approx(liveness_failure(result.params))
