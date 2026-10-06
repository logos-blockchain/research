"""Gates for grinding the epoch nonce (src/finality_sim/grinding.py)."""

import math

import numpy as np
import pytest

from finality_sim.grinding import (PER_BIT, bounds, factors, lead_pmf, pair_bounds, post_cutoff,
                                   simulate, tail)

F, ALPHA = 1 / 30, 0.25
MODELS = {"random": dict(growth=0.845), "worst": dict(delta=10)}


@pytest.fixture(scope="module", params=list(MODELS))
def run(request):
    kw = MODELS[request.param]
    out = simulate(F, ALPHA, 100_000, 4000, 30, 17 + len(request.param), **kw)
    assert np.all(out[0][:, 30] > -(1 << 39))        # every history reaches 30 blocks back
    return (kw,) + out


def test_the_walk_matches_a_slot_by_slot_simulation(run):
    kw, leads = run[:2]
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
    kw, log2m = run[0], run[3]
    xs = np.array([0.0, 2.5, 6.5, 10.5])              # S is an integer: no rounding at these
    for x, p in zip(xs, tail(F, ALPHA, xs, **kw)):
        assert (log2m >= x).mean() == pytest.approx(p, abs=4 * math.sqrt(p * (1 - p) / log2m.size))


def test_the_bounds_hold_the_simulated_chance(run):
    """The lower bound holds the choices complete at the cut-off; the upper bound also those the
    coalition completes after it, which exceed what the cut-off alone allows."""
    kw, log2g, log2m, log2gz = run[0], run[2], run[3], run[4]
    ts, lower, upper, _ = bounds(F, ALPHA, budget_bits=40, **kw)
    _, _, upper_at_cutoff, _ = bounds(F, ALPHA, budget_bits=40, after_cutoff=False, **kw)
    assert np.all(lower <= upper)
    for t in (4, 8, 12):
        i = int(np.searchsorted(ts, t))
        at, after = np.minimum(1.0, 2.0 ** (log2g - t)), np.minimum(1.0, 2.0 ** (log2gz - t))
        se_at, se_after = at.std() / math.sqrt(at.size), after.std() / math.sqrt(after.size)
        assert lower[i] - 4 * se_at <= at.mean() <= upper_at_cutoff[i] + 4 * se_at
        assert after.mean() <= upper[i] + 4 * se_after
        if t == 8:                                   # where the later forks are clearly seen
            assert after.mean() > upper_at_cutoff[i] + 4 * se_after
        # the lower bound is E[min(1, uM)] on a grid of 1/16 bit, from below
        m = np.where(np.isfinite(log2m), np.minimum(1.0, 2.0 ** (log2m - t)), 0.0)
        se_m = m.std() / math.sqrt(m.size)
        assert lower[i] - 4 * se_m <= m.mean() <= lower[i] * 2 ** (1 / PER_BIT) + 4 * se_m


def test_the_pair_bounds_hold_two_simulated_epochs(run):
    """Two independent histories, one per cut-off: the chance against a schedule that needs both
    nonces lies between the pair's bounds, and above what one epoch's upper bound allows."""
    kw, log2g, log2gz = run[0], run[2], run[4]
    h = log2g.size // 2
    ts, _, upper, lower2, upper2 = pair_bounds(F, ALPHA, budget_bits=40, **kw)
    assert np.all(lower2 <= upper2)
    for t in (10, 14, 18):
        i = int(np.searchsorted(ts, t))
        at = np.minimum(1.0, 2.0 ** (log2g[:h] + log2g[h:] - t))
        after = np.minimum(1.0, 2.0 ** (log2gz[:h] + log2gz[h:] - t))
        se_at, se_after = at.std() / math.sqrt(h), after.std() / math.sqrt(h)
        assert lower2[i] - 4 * se_at <= at.mean()
        assert after.mean() <= upper2[i] + 4 * se_after
        assert after.mean() > upper[i] + 4 * se_after


def test_the_lead_after_the_cut_off_is_the_forward_walk(run):
    kw, zs = run[0], run[5]
    pz = post_cutoff(F, ALPHA, **kw)
    for z in (1, 2, 3):
        want = pz[z:].sum()
        got = (zs >= z).mean()
        se = math.sqrt(want * (1 - want) / zs.size)
        if "growth" in kw:                           # memoryless gaps: exact
            assert got == pytest.approx(want, abs=4 * se)
        else:                                        # the first gap taken whole: from above
            assert got <= want + 4 * se


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


def test_the_factors_bracket_where_the_bounds_cross_eps():
    eps = 1e-9
    ts, lower, upper, _ = bounds(F, ALPHA, budget_bits=40, **MODELS["random"])
    lo, hi = factors(ts, lower, upper, eps)
    u = 2.0 ** -ts
    i = int(np.argmin(np.abs(u - eps / lo)))
    assert lower[i] > eps >= lower[i + 1]             # the lower bound fails at eps / lo, not below
    j = int(np.argmin(np.abs(u - eps / hi)))
    assert upper[j] <= eps < upper[j - 1]             # the upper bound holds at eps / hi, not above


def test_the_lower_bound_is_below_its_integral():
    """M is an integer, so E[min(1, uM)] = u (P(M >= 1) + ... + P(M >= 1/u)) exactly; the lower
    bound integrates the same tail on a grid of 1/16 bit, from below."""
    kw = MODELS["random"]
    ts, lower, _, _ = bounds(F, ALPHA, budget_bits=40, **kw)
    for t in (6, 8):
        n = np.arange(1, 2 ** t + 1)
        exact = 2.0 ** -t * tail(F, ALPHA, np.log2(n), **kw).sum()
        low = lower[int(np.searchsorted(ts, t))]
        assert low <= exact * (1 + 1e-12) and exact <= 1.1 * low, (t, low, exact)
