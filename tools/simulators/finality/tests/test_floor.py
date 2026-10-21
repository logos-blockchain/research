"""Gates for splits and eclipses with finality counted in slots (src/finality_sim/floor.py, K.3)."""

import math

import numpy as np
import pytest
from scipy import stats

from finality_sim.floor import (after_correction, blocks_time, density_fix, floor_for,
                                least_quorum_window, log_cdf, log_reach, provisional_share, quorum,
                                safe_floor)
from finality_sim.further import detector_power
from finality_sim.recovery import honest_logpmf, occupancy

F = 1 / 30
G = 0.845
EPS = 1e-9


@pytest.mark.parametrize("model", [dict(growth=G), dict(delta=10), dict(delta=3)])
def test_the_counts_are_b5s_laws(model):
    """``log_cdf`` is the cumulative sum of B5's pmf in both models."""
    w = 6_000
    for share in (0.3, 2 / 3, 1.0):
        cdf = np.cumsum(np.exp(honest_logpmf(w, occupancy(F, share), **model)))
        for n in (0, 5, 60, 130, 180, 250):
            assert math.exp(log_cdf(n, w, share, F, **model)) == pytest.approx(cdf[n], rel=1e-7,
                                                                                 abs=1e-300)


@pytest.mark.parametrize("model", [dict(growth=G), dict(delta=10)])
def test_the_floor_is_the_largest_the_withheld_chain_reaches(model):
    """``P(N < φ) ≤ ε < P(N < φ + 1)`` for the honest chain a coalition withholds from."""
    for w, alpha in ((64_800, 1 / 3), (194_400, 0.25), (20_000, 0.3)):
        phi = floor_for(w, alpha, EPS, F, **model)
        assert log_cdf(phi - 1, w, 1 - alpha, F, **model) <= math.log(EPS)
        assert log_cdf(phi, w, 1 - alpha, F, **model) > math.log(EPS)


def test_under_random_delay_the_floor_is_the_detectors_threshold():
    """H.1's detector reads the same lower tail of the same count."""
    for w, alpha in ((64_800, 0.3), (129_600, 1 / 3)):
        assert floor_for(w, alpha, EPS, F, growth=G) == detector_power(alpha, G, w, EPS, [0.5])[0]


def test_the_safe_floor_is_the_smallest_a_side_reaches_at_eps():
    for w, share in ((64_800, 0.625), (194_400, 2 / 3)):
        phi = safe_floor(w, share, EPS)
        assert log_reach(w, phi, share) <= math.log(EPS) < log_reach(w, phi - 1, share)


def test_a_provisional_side_reaches_the_floor_at_eps():
    w = 194_400
    phi = floor_for(w, 1 / 3, EPS, F, growth=G)
    s = provisional_share(w, phi, EPS)
    assert log_reach(w, phi, s) <= math.log(EPS) < log_reach(w, phi, s + 1e-3)


@pytest.mark.parametrize("alpha, model", [(0.25, dict(live_growth=G, side_growth=0.863)),
                                          (0.2, dict(live_delta=1)), (0.2, dict(live_delta=5))])
def test_the_least_quorum_window_is_the_first_that_separates(alpha, model):
    """At the window returned, a floor lies at or below the honest chain's lower tail and above a
    side of ``(1 + α)/2``'s upper tail, by direct binomial and renewal tails; one slot less, none."""
    w = least_quorum_window(alpha, EPS, F, **model)
    assert w is not None
    side = (1 + alpha) / 2
    sg = model.get("side_growth", 1.0)

    def separates(w):
        live = floor_for(w, alpha, EPS, F, model.get("live_growth"), model.get("live_delta"))
        upper = stats.binom.logsf(live - 1, w, sg * occupancy(F, side))   # P(side reaches live)
        return upper <= math.log(EPS)

    assert separates(w)
    assert not separates(w - 1)
    assert quorum(w, alpha, EPS, F, **model)[0] >= quorum(w, alpha, EPS, F, **model)[1]


def test_no_window_separates_when_the_side_grows_as_fast():
    """At a third the side ``(1 + α)/2`` holds ``1 − α`` of the stake, and with one block per
    occupied slot it grows faster than the honest chain under either delay model; at a fifth
    under random delay the honest chain is the faster, and a window exists."""
    assert least_quorum_window(1 / 3, EPS, F, live_growth=G) is None
    assert least_quorum_window(1 / 3, EPS, F, live_delta=1) is None
    assert least_quorum_window(0.25, EPS, F, live_delta=10) is None
    assert least_quorum_window(0.2, EPS, F, live_growth=G) is not None


def test_the_eclipse_time_is_the_lower_tail_of_the_blocks():
    for n, share in ((2_161, 0.3), (3_265, 0.05)):
        mean, early = blocks_time(n, share, EPS)
        p = occupancy(F, share)
        assert mean == pytest.approx(n / p)
        assert stats.binom.logsf(n - 1, early, p) >= math.log(EPS)
        assert stats.binom.logsf(n - 1, early - 1, p) < math.log(EPS)


def test_after_the_correction_the_chain_fills_its_slots_at_f():
    """Sampled slot by slot: the share's own occupancy for one epoch, then ``f``."""
    rng = np.random.default_rng(4)
    epoch, share, n = 20_000, 0.2, 500
    p = occupancy(F, share)
    times = []
    for _ in range(400):
        before = rng.random(epoch) < p
        after = rng.random(40_000) < F
        hits = np.concatenate([np.nonzero(before)[0], epoch + np.nonzero(after)[0]])
        times.append(hits[n - 1] + 1)
    assert np.mean(times) == pytest.approx(after_correction(n, share, epoch), rel=0.01)


def test_a_sparse_chain_waits_for_its_inference_under_the_density_form():
    """Below the floor's share a chain is fixed only after the correction; well above it, at ``K``."""
    w, epoch = 194_400, 648_000
    phi = floor_for(w, 1 / 3, EPS, F, delta=10)
    lo10, t = density_fix(0.3, phi, w, epoch, EPS)
    assert lo10 < -9 and t == epoch + w
    lo10, t = density_fix(0.6, phi, w, epoch, EPS)
    assert lo10 > math.log10(0.5) and t == pytest.approx(w + 1 / occupancy(F, 0.6))
    lo10, t = density_fix(0.455, phi, w, epoch, EPS)
    assert math.isnan(t)
