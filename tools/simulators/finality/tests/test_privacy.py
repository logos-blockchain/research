"""Gates for what votes leak and what an opt-in committee needs (src/finality_sim/privacy.py)."""

import math

import numpy as np
import pytest
from scipy import stats

from finality_sim.privacy import (confidence, holders_needed, spec_confidence, split, stake_days,
                                  volunteer_share)

Q = 0.2 ** 3                                      # the Blend report's f_adv = 0.2, 3 hops


def test_the_blend_reports_stake_times_are_reproduced():
    """reports/blend/README.md §3.7, as printed (days): identity, ±10 % and ±5 %."""
    assert round(stake_days(0.05, 1, Q), 1) == 0.9
    assert round(stake_days(0.05, 100, Q), 1) == 86.8
    assert round(stake_days(0.01, 400, Q)) == 1736
    assert round(stake_days(0.001, 100, Q)) == 4340
    assert round(stake_days(0.001, 1, Q), 1) == 43.4
    assert round(stake_days(0.0001, 400, Q)) == 173611


def test_the_specifications_example_is_reproduced():
    """analysis-cryptarchia-de-anonymisation-of-relative-stake.md: confidence about 0.824 for a
    1.26 % holder, and five nodes to bring it below 0.5."""
    def conf(a):
        return spec_confidence(a, 0.1, 432_000, 0.657, 0.05)
    assert round(conf(0.0126), 3) == 0.824
    assert split(0.0126, 0.5, conf) == 5
    assert confidence(0.0126, 0.1, 432_000, 0.657, 0.05) == pytest.approx(conf(0.0126), abs=1e-9)


def test_votes_sample_stake_at_the_emission_multiple():
    """D0's cover multiples at a quarter of the stake (CERTIFIED.md D0): ×269 at 10 min, ×1,786
    at 90 s."""
    for round_s, multiple in ((600, 269), (90, 1786)):
        ratio = stake_days(0.001, 100, Q) / stake_days(0.001, 100, Q, seats=5355, round_s=round_s,
                                                       q_votes=Q)
        assert ratio == pytest.approx(1 + 5355 * 30 / round_s)
        assert round(ratio) == multiple


def test_a_vote_count_has_the_confidence_the_formula_gives():
    """With the blocks unobserved, the confidence is that of a Poisson count of the votes."""
    T, round_slots, seats, alpha = 64_800, 600, 5355, 400 / (108 * 5355)
    c = confidence(alpha, 0.1, T, 1e-12, 1 / 30, seats=seats, round_slots=round_slots, q_votes=1.0)
    mean = T / round_slots * seats * alpha                     # 400 votes
    exact = stats.poisson.cdf(math.floor(1.1 * mean), mean) - stats.poisson.cdf(
        math.ceil(0.9 * mean) - 1, mean)
    assert c == pytest.approx(exact, abs=0.01)


def test_the_committee_frontier_is_where_safety_and_liveness_meet():
    for alpha in (0.1, 0.25):
        for uptime in (1.0, 0.95):
            v = volunteer_share(alpha, uptime)
            declared = alpha + v * (1 - alpha)
            assert alpha / declared <= 1 / 3 + 1e-12                       # safety
            assert uptime * v * (1 - alpha) == pytest.approx(2 / 3 * declared)  # liveness, tight
            w = v * (1 - 1e-6)
            assert uptime * w * (1 - alpha) < 2 / 3 * (alpha + w * (1 - alpha))
    assert math.isinf(volunteer_share(0.3, 0.95))
    assert math.isinf(volunteer_share(1 / 3, 1.0))


def test_the_largest_holders_are_counted():
    stakes = np.array([2.0, 5.0, 3.0])
    assert holders_needed(stakes, 0.5) == 1
    assert holders_needed(stakes, 0.51) == 2
    assert holders_needed(stakes, 1.0) == 3
    assert holders_needed(stakes, 1.2) is None
