"""Gates for what votes leak and what an opt-in committee needs (src/finality_sim/privacy.py)."""

import math
import pathlib
import sys

import numpy as np
import pytest

from finality_sim.privacy import (attribution_days, confidence, holders_needed, spec_confidence,
                                  split, volunteer_share)

Q = 0.2 ** 3                                      # the Blend report's f_adv = 0.2, 3 hops


def test_the_blend_reports_stake_times_are_reproduced():
    """reports/blend/README.md §3.7, as printed (days): identity, ±10 % and ±5 %."""
    assert round(attribution_days(0.05, 1, Q), 1) == 0.9
    assert round(attribution_days(0.05, 100, Q), 1) == 86.8
    assert round(attribution_days(0.01, 400, Q)) == 1736
    assert round(attribution_days(0.001, 100, Q)) == 4340
    assert round(attribution_days(0.001, 1, Q), 1) == 43.4
    assert round(attribution_days(0.0001, 400, Q)) == 173611


def test_the_specifications_example_is_reproduced():
    """analysis-cryptarchia-de-anonymisation-of-relative-stake.md: confidence about 0.824 for a
    1.26 % holder, and five nodes to bring it below 0.5. At its large counts the exact Poisson
    confidence agrees with the analysis' Gaussian one."""
    def conf(a):
        return spec_confidence(a, 0.1, 432_000, 0.657, 0.05)
    assert round(conf(0.0126), 3) == 0.824
    assert split(0.0126, 0.5, conf) == 5
    assert confidence(0.0126, 0.1, 432_000, 0.657, 0.05) == pytest.approx(conf(0.0126), abs=0.02)


def test_votes_sample_stake_at_the_emission_multiple():
    """Attributed alike, votes speed sizing by D0's multiples at a quarter of the stake
    (CERTIFIED.md D0): ×269 at 10 min, ×1,786 at 90 s."""
    for round_s, multiple in ((600, 269), (90, 1786)):
        ratio = attribution_days(0.001, 100, Q) / attribution_days(
            0.001, 100, Q, seats=5355, round_s=round_s, q_votes=Q)
        assert ratio == pytest.approx(1 + 5355 * 30 / round_s, rel=5e-3)
        assert round(ratio) == multiple


def test_votes_come_at_round_starts():
    """One attribution, blocks negligible: half a round to the first round start, then a round
    per batch that is not attributed."""
    for mu in (0.3, 1.0, 3.0):
        stake = mu / (5355 * Q)
        got = attribution_days(stake, 1, 1e-12, seats=5355, round_s=600, q_votes=Q) * 86400
        want = 300 + 600 * math.exp(-mu) / (1 - math.exp(-mu))
        assert got == pytest.approx(want, rel=2e-3)
    many = attribution_days(0.001, 1, Q, seats=5355, round_s=600, q_votes=Q, notes=1e9)
    assert many == pytest.approx(attribution_days(0.001, 1, Q, seats=5355, round_s=600, q_votes=Q),
                                 rel=1e-6)


@pytest.mark.parametrize("notes", [math.inf, 10])
def test_the_confidence_is_that_of_the_estimate(notes):
    """Draw the attributed count, solve for the stake, and count estimates within ±10 %."""
    T, f, alpha, seats = 648_000, 1 / 30, 0.0126, 5355
    qb = 1 - (1 - Q) ** 2

    def lam(a):
        votes = seats * a if math.isinf(notes) else notes * (1 - math.exp(-seats * a / notes))
        return T * qb * (1 - (1 - f) ** a) + T / 600 * Q * votes

    rng = np.random.default_rng(3)
    counts = rng.poisson(lam(alpha), 20_000)
    grid = np.linspace(0.5 * alpha, 1.6 * alpha, 4001)
    lams = np.array([lam(a) for a in grid])
    est = grid[np.clip(np.searchsorted(lams, counts), 0, grid.size - 1)]
    hit = np.mean(np.abs(est / alpha - 1) <= 0.1)
    c = confidence(alpha, 0.1, T, qb, f, seats=seats, round_slots=600, q_votes=Q, notes=notes)
    assert hit == pytest.approx(c, abs=4 * math.sqrt(c * (1 - c) / counts.size) + 2e-3)


def test_the_committee_frontier_is_where_safety_and_liveness_meet():
    for alpha in (0.1, 0.25):
        for uptime in (1.0, 0.95):
            v = volunteer_share(alpha, uptime) * (1 + 1e-9)
            declared = alpha + v * (1 - alpha)
            assert alpha / declared < 1 / 3                                     # safety
            assert uptime * v * (1 - alpha) == pytest.approx(2 / 3 * declared)  # liveness, tight
            w = v * (1 - 1e-6)
            assert uptime * w * (1 - alpha) < 2 / 3 * (alpha + w * (1 - alpha))
    assert math.isinf(volunteer_share(0.3, 0.95))
    assert math.isfinite(volunteer_share(0.3, 0.96))
    assert math.isinf(volunteer_share(1 / 3, 1.0))


def test_the_largest_holders_are_counted():
    stakes = np.array([2.0, 5.0, 3.0])
    assert holders_needed(stakes, 0.5) == 1
    assert holders_needed(stakes, 0.51) == 2
    assert holders_needed(stakes, 1.0) == 3
    assert holders_needed(stakes, 1.2) is None


def test_the_sized_share_is_the_largest_held_at_even_odds():
    """scripts/d5_privacy.py: every share above the one returned is sized at better than even
    odds; a dip below even odds above an edge moves the share up to it."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
    from d5_privacy import GRID, sized_above
    edge = 0.0123
    assert sized_above(lambda s: 0.9 if s > edge else 0.4) == GRID[GRID <= edge].max()
    dip = sized_above(lambda s: 0.4 if s <= edge or 0.2 < s <= 0.25 else 0.9)
    assert dip == GRID[GRID <= 0.25].max()
    assert sized_above(lambda s: 0.9) == 0.0
