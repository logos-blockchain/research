"""Gates for grinding the epoch nonce (src/finality_sim/grinding.py)."""

import math

import numpy as np
import pytest

from finality_sim.grinding import PER_BIT, bounds, factors, lead_pmf, simulate, tail

F, ALPHA = 1 / 30, 0.25
MODELS = {"random": dict(growth=0.845), "worst": dict(delta=10)}


@pytest.fixture(scope="module", params=list(MODELS))
def run(request):
    kw = MODELS[request.param]
    leads, log2g, log2m = simulate(F, ALPHA, 100_000, 3000, 30, 17 + len(request.param), **kw)
    assert np.all(leads[:, 30] > -(1 << 39))         # every history reaches 30 blocks back
    return kw, leads, log2g, log2m


def test_the_walk_matches_a_slot_by_slot_simulation(run):
    kw, leads, _, _ = run
    for d in (0, 15, 30):
        p, low = lead_pmf(F, ALPHA, d, **kw)
        lead = np.arange(p.size) + low
        sim = leads[:, d]
        assert sim.mean() == pytest.approx((lead * p).sum(), abs=4 * sim.std() / math.sqrt(sim.size))
        if d < 30:
            q = p[lead >= 3].sum()
            assert (sim >= 3).mean() == pytest.approx(q, abs=4 * math.sqrt(q * (1 - q) / sim.size))


def test_the_largest_choice_matches_the_simulation(run):
    """P(M >= 2^x), M the most nonces one fork point offers."""
    kw, _, _, log2m = run
    xs = np.array([0.0, 2.5, 6.5, 10.5])              # S is an integer: no rounding at these
    for x, p in zip(xs, tail(F, ALPHA, xs, **kw)):
        assert (log2m >= x).mean() == pytest.approx(p, abs=4 * math.sqrt(p * (1 - p) / log2m.size))


def test_the_bounds_hold_the_simulated_chance(run):
    kw, _, log2g, _ = run
    ts, lower, upper, _ = bounds(F, ALPHA, budget_bits=40, **kw)
    assert np.all(lower <= upper)
    for t in (6, 10, 14):
        i = int(np.searchsorted(ts, t))
        x = np.minimum(1.0, 2.0 ** (log2g - t))
        se = x.std() / math.sqrt(x.size)
        assert lower[i] - 4 * se <= x.mean() <= upper[i] + 4 * se


def test_the_truncation_of_the_walk_moves_no_bound():
    kw = MODELS["worst"]
    a = bounds(F, 0.3, budget_bits=40, **kw)
    b = bounds(F, 0.3, budget_bits=40, floor=200, cap=400, **kw)
    for x, y in zip(a[1:3], b[1:3]):
        assert np.allclose(x, y, rtol=1e-9, atol=0)


def test_without_a_choice_the_factor_is_one():
    ts, lower, upper, p = bounds(F, 1e-6, budget_bits=40, **MODELS["random"])
    lo, hi = factors(ts, lower, upper, 1e-9)
    assert p < 1e-5 and lo == 1 and hi < 2 ** (1 / PER_BIT)     # one step of the grid
