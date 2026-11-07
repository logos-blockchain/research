"""Gates for stake counted in anonymous units (UNITS.md N.1, N.2)."""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from finality_sim import units as un
from finality_sim.committee import smallest_committee
from finality_sim.signers import known_committee

EPS = 1e-9
F = 1 / 30


def test_the_hypergeometric_pmf_is_scipys():
    for n, units, adv in ((5602, 30000, 9000), (300, 1000, 333), (50, 60, 30)):
        mine = un.hyper_pmf(n, units, adv)
        ref = stats.hypergeom.pmf(np.arange(n + 1), units, adv, n)
        big = ref > 1e-250
        assert np.allclose(mine[big], ref[big], rtol=1e-8)
        assert mine[~big].max(initial=0.0) < 1e-240


def test_the_public_quorum_against_a_direct_count():
    """On a small registry the quorum is the least ``Q`` whose conflicting certificates, which
    need ``2Q − n`` coalition units in the draw, have probability at most ``eps``, counted
    directly with binomial coefficients."""
    units, adv, n, eps = 200, 60, 100, 1e-3

    def tail(need):
        return sum(math.comb(adv, a) * math.comb(units - adv, n - a)
                   for a in range(max(need, 0), min(adv, n) + 1)) / math.comb(units, n)

    q = next(q for q in range(n // 2 + 1, n + 1) if tail(2 * q - n) <= eps)
    ok, got = un.public_holds(n, units, adv, eps)
    assert got == q
    honest_short = sum(math.comb(adv, a) * math.comb(units - adv, n - a)
                       for a in range(0, min(adv, n) + 1) if n - a < q) / math.comb(units, n)
    assert ok == (honest_short <= eps)


def test_the_public_draw_tends_to_the_binomial_count():
    """Drawn without replacement from many units, the committee is M.1's binomial count; from
    30,000 it is smaller, the draw's variance falling by ``(U − n)/(U − 1)``."""
    big = un.public_draw(0.25, EPS, 1_000_000)
    count = known_committee(0.25, EPS)
    assert abs(big[0] - count[0]) / count[0] < 0.01
    small = un.public_draw(0.25, EPS, 30_000)
    assert small[0] < big[0]
    assert un.public_draw(0.30, EPS, 30_000)[0] < known_committee(0.30, EPS)[0]


def test_the_scan_finds_the_lattice_minimum():
    """Bisection alone stops above the fewest units that hold; the scan below it finds the
    full scan's answer."""
    alpha, units, eps = 0.30, 5000, 1e-6
    adv = un.coalition_units(alpha, units)
    first = next(n for n in range(1, units + 1) if un.public_holds(n, units, adv, eps)[0])
    assert un.public_draw(alpha, eps, units)[0] == first


def test_every_unit_voting_is_the_public_draw_of_all_units():
    for alpha, uptime in ((0.30, 1.0), (0.30, 0.95), (0.30, 0.93), (0.25, 0.9)):
        units = 30_000
        adv = un.coalition_units(alpha, units)
        ok, q = un.public_holds(units, units, adv, EPS, uptime)
        every = un.every_unit(alpha, EPS, units, uptime)
        assert ok == (every is not None)
        assert q == (units + adv) // 2 + 1
        if every is not None:
            assert every == (units, q)
        assert 2 * q - units > adv >= 2 * (q - 1) - units


def test_every_unit_voting_tends_to_its_closed_form():
    """The least uptime at which every unit voting holds falls to ``(1 + a)/(2(1 − a))`` as the
    units grow; with 30,000 units it holds 30 % at 95 % and not at 90 %."""
    for alpha in (0.10, 0.30):
        assert un.every_unit_uptime(alpha, EPS, 10_000_000) == pytest.approx(
            un.every_unit_limit(alpha), rel=2e-3)
    assert un.every_unit(0.30, EPS, 30_000, 0.95) is not None
    assert un.every_unit(0.30, EPS, 30_000, 0.90) is None
    assert un.every_unit(1 / 3, EPS, 30_000, 1.0) is None


def test_the_private_draw_tends_to_poissons_seats():
    """A private draw over many counted units is D0's Poisson committee without its margin; over
    30,000 units the binomial count's smaller variance shrinks it."""
    poisson = smallest_committee(0.10, EPS)
    many = un.private_draw(0.10, EPS, 2_000_000)
    assert abs(many[0] - poisson[0]) / poisson[0] < 0.01
    assert un.private_draw(0.10, EPS, 30_000)[0] < poisson[0]


def test_the_rounding_against_a_count_over_sampled_notes():
    """The coalition sizes its notes in whole units and the honest notes fall where they fall:
    the coalition's share of the units is ``unit_share`` at the honest stake's measured loss, which
    stays below one unit a note."""
    rng = np.random.default_rng(11)
    unit = 1000                                                    # base units in one unit
    for alpha in (0.10, 0.30):
        honest = rng.integers(1, 200 * unit, size=4000)
        total_honest = int(honest.sum())
        coalition = rng.integers(1, 200, size=800) * unit
        coalition = coalition * (alpha / (1 - alpha) * total_honest / coalition.sum())
        coalition = np.round(coalition / unit).astype(np.int64) * unit
        alpha_true = coalition.sum() / (coalition.sum() + total_honest)
        h_units = int(un.units_held(honest, unit).sum())
        c_units = int(un.units_held(coalition, unit).sum())
        assert h_units == int((honest // unit).sum())
        assert c_units * unit == coalition.sum()
        loss = 1 - h_units * unit / total_honest
        assert 0 < loss < honest.size * unit / total_honest
        assert c_units / (c_units + h_units) == pytest.approx(un.unit_share(alpha_true, loss),
                                                              rel=1e-12)


def test_the_registry_counts_and_window():
    assert un.registered_units() == 30_000
    assert un.registration_bytes() == 196
    assert un.registrations_per_s(30_000) == pytest.approx(30_000 / (2 * 64_800), rel=1e-12)
    assert un.EPOCH_SLOTS == 648_000


@pytest.mark.parametrize("alpha,uptime", [(0.30, 1.0), (0.30, 0.95), (1 / 3, 0.9), (0.10, 2 / 3)])
def test_the_registered_lottery_keeps_the_coalitions_rate(alpha, uptime):
    """With the lottery dividing by the registered stake, the coalition's rate is its stake's and
    the honest rate falls with its uptime; the inference instead restores the full rate. Online
    notes split at random win a slot with the chance ``1 − (1 − f)^online``."""
    a, scale = un.registered_rates(alpha, uptime)
    assert a * scale == pytest.approx(alpha, rel=1e-12)
    assert (1 - a) * scale == pytest.approx((1 - alpha) * uptime, rel=1e-12)
    ai, si = un.inferred_rates(alpha, uptime)
    assert ai == pytest.approx(a, rel=1e-12) and si == 1.0
    rng = np.random.default_rng(int(100 * alpha + 1000 * uptime))
    for _ in range(50):
        shares = rng.dirichlet(np.ones(int(rng.integers(2, 60))))
        notes = shares * scale
        win = 1 - np.prod((1 - F) ** notes)
        assert 1 / win == pytest.approx(un.block_interval(scale), rel=1e-12)
    if uptime == 1.0:
        assert (a, scale) == pytest.approx((alpha, 1.0), rel=1e-12)
