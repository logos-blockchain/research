"""Gates for the active stake as a share of the supply (SIGNERS.md M.7)."""

from __future__ import annotations

import numpy as np
import pytest

from finality_sim.active import (declarations_cap, entering, honest_entry_break, least_inferred,
                                 lottery_chance, seats_edge, supply_share)
from finality_sim.committee import safety_tail, smallest_committee
from finality_sim.waitbound import wait_curve

F = 1 / 30
EPS = 1e-9


def test_a_coalition_entering_from_outside_is_a_deflation():
    """With the inference at the honest stake alone, a coalition whose stake enters holds ``α`` of
    the true stake, and the true over the inferred stake is the deflation's ``1/(1 − α)``."""
    rng = np.random.default_rng(7)
    for _ in range(200):
        honest, alpha = rng.uniform(0.1, 10.0), rng.uniform(0.01, 0.49)
        coalition = alpha * honest / (1 - alpha)
        assert coalition / (honest + coalition) == pytest.approx(alpha, rel=1e-12)
        assert entering(alpha) == pytest.approx((honest + coalition) / honest, rel=1e-12)


def test_the_supply_share_scales_by_the_active_stake():
    assert supply_share(0.30, 0.30) == pytest.approx(0.09, rel=1e-12)
    assert supply_share(1 / 3, 0.30) == pytest.approx(0.10, rel=1e-12)
    assert supply_share(0.25, 0.20) == pytest.approx(0.05, rel=1e-12)


def test_no_anonymous_committee_exists_from_the_seats_edge():
    """Once the coalition's stake enters, D2's committee exists just below the edge and not from
    it on."""
    edge = seats_edge()
    above, below = edge + 1e-9, edge - 0.01
    assert smallest_committee(above, EPS, inflation=entering(above)) is None
    assert smallest_committee(below, EPS, inflation=entering(below)) is not None


def test_honest_stake_entering_breaks_the_committee_at_the_edge():
    """The committee sized against 10 % for an inference error up to 1.05 holds safety just below
    the edge and loses it at the edge, with the coalition diluted to ``α/x`` of the true stake.
    Diluted, it outlasts an error of 1.05 in both shares."""
    alpha = 0.10
    n, q = smallest_committee(alpha, EPS, inflation=1.05)
    x = honest_entry_break(alpha, EPS)
    assert x > 1.05
    assert safety_tail(n, alpha / x, 2 * q, x) > EPS
    assert safety_tail(n, alpha / (x - 1e-5), 2 * q, x - 1e-5) <= EPS


@pytest.mark.parametrize("x", [1.0, 1 / 0.7, 2.0, 10 / 3])
def test_a_larger_true_stake_is_the_lottery_at_a_higher_chance(x):
    """Notes holding ``x`` times the inferred stake, split at random, win a slot with the chance
    ``1 − (1 − f)^x``, and the wait bound at that chance equals the bound with both rates scaled
    by ``x``."""
    rng = np.random.default_rng(int(1000 * x))
    for _ in range(20):
        shares = rng.dirichlet(np.ones(50)) * x
        none_wins = np.prod((1 - F) ** shares)
        assert lottery_chance(x) == pytest.approx(1 - none_wins, rel=1e-12)
    if x > 1:
        assert np.allclose(wait_curve(3_000, 1 / 3, 10, scale=x),
                           wait_curve(3_000, 1 / 3, 10, lottery_chance(x)), rtol=1e-12)


def test_the_least_inferred_stake_keeps_the_true_stake_within_the_edge():
    """With the true active stake at most 30 % of the supply, an inferred stake at the least
    share lets it reach the edge exactly, and any lower one lets it pass the edge."""
    for edge in (1.5, 1.92, 2.6):
        least = least_inferred(edge, 0.30)
        assert 0.30 / least == pytest.approx(edge, rel=1e-12)
        assert 0.30 / (least * 0.999) > edge


def test_the_active_stake_caps_the_declarations():
    """Each declaration holds at least the minimum stake, so the active stake makes at most its
    share over the minimum, rounded down."""
    assert declarations_cap(0.30, 1e-5) == 30_000
    assert declarations_cap(0.30, 7e-5) == 4_285
    assert declarations_cap(0.09, 1e-5) == 9_000
