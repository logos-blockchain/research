"""Gates for grinding the epoch nonce (src/finality_sim/grinding.py)."""

import math

import numpy as np
import pytest

from finality_sim.grinding import (PER_BIT, _choices, _max_tail, _max_tail_mixed, _place, _table,
                                   _union, _union_before, _ztable, bounds, factors, lead_pmf,
                                   pair_bounds, post_cutoff, simulate, tail, walk)

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
    """At the cut-off, and with the forks the coalition completes after it, the simulated chance
    lies between the bounds; the later forks take it above the bound that leaves them out. Each
    lower bound is E[min(1, uM)] on a grid of 1/16 bit, from below; with the later forks that is
    tight only where the lead after the cut-off is exact, under random delay."""
    kw, log2g, log2m, log2gz, log2mz = run[0], run[2], run[3], run[4], run[6]
    ts, lower, upper, _ = bounds(F, ALPHA, budget_bits=40, **kw)
    _, lower_at, upper_at, _ = bounds(F, ALPHA, budget_bits=40, after_cutoff=False, **kw)
    assert np.all(lower <= upper) and np.all(lower_at <= lower) and np.all(upper_at <= upper)
    for t in (4, 8, 12):
        i = int(np.searchsorted(ts, t))
        for lo, up, lg, lm, tight in ((lower_at, upper_at, log2g, log2m, True),
                                      (lower, upper, log2gz, log2mz, "growth" in kw)):
            g = np.minimum(1.0, 2.0 ** (lg - t))
            se = g.std() / math.sqrt(g.size)
            assert lo[i] - 4 * se <= g.mean() <= up[i] + 4 * se
            m = np.where(np.isfinite(lm), np.minimum(1.0, 2.0 ** (lm - t)), 0.0)
            se_m = m.std() / math.sqrt(m.size)
            assert lo[i] - 4 * se_m <= m.mean()
            if tight:
                assert m.mean() <= lo[i] * 2 ** (1 / PER_BIT) + 4 * se_m
        if t == 8:                                   # where the later forks are clearly seen
            after = np.minimum(1.0, 2.0 ** (log2gz - t))
            assert after.mean() > upper_at[i] + 4 * after.std() / math.sqrt(after.size)


def test_the_pair_bounds_hold_two_simulated_epochs(run):
    """Two independent histories, one per cut-off: the chance against a schedule that needs both
    nonces lies between the pair's bounds, and above what one epoch's upper bound allows."""
    kw, log2gz, log2mz = run[0], run[4], run[6]
    h = log2gz.size // 2
    ts, _, upper, lower2, upper2 = pair_bounds(F, ALPHA, budget_bits=40, **kw)
    assert np.all(lower2 <= upper2)
    m = np.maximum(0.0, np.nan_to_num(log2mz, neginf=0.0))   # log2 max(1, M)
    for t in (10, 14, 18):
        i = int(np.searchsorted(ts, t))
        after = np.minimum(1.0, 2.0 ** (log2gz[:h] + log2gz[h:] - t))
        se = after.std() / math.sqrt(h)
        assert lower2[i] - 4 * se <= after.mean() <= upper2[i] + 4 * se
        assert after.mean() > upper[i] + 4 * se
        # the lower bound is E[min(1, u max(1, M) max(1, M'))] on the grid, from below
        mm = np.minimum(1.0, 2.0 ** (m[:h] + m[h:] - t))
        se_m = mm.std() / math.sqrt(h)
        assert lower2[i] - 4 * se_m <= mm.mean()
        if "growth" in kw:                           # the lead after the cut-off is exact
            assert mm.mean() <= lower2[i] * 2 ** (2 / PER_BIT) + 4 * se_m


def test_the_lead_after_the_cut_off_is_the_forward_walk(run):
    kw, zs = run[0], run[5]
    pz, pz_lo = post_cutoff(F, ALPHA, **kw), post_cutoff(F, ALPHA, lower=True, **kw)
    for z in (1, 2, 3):
        want, low = pz[z:].sum(), pz_lo[z:].sum()
        got = (zs >= z).mean()
        se = math.sqrt(want * (1 - want) / zs.size)
        if "growth" in kw:                           # memoryless gaps: exact
            assert got == pytest.approx(want, abs=4 * se) and low == want
        else:                                        # the first gap taken whole, and left out
            assert low - 4 * se <= got <= want + 4 * se and low < want


def test_the_truncation_of_the_walk_moves_no_bound():
    kw = MODELS["worst"]
    a = bounds(F, 0.3, budget_bits=40, per_bit=4, **kw)
    b = bounds(F, 0.3, budget_bits=40, per_bit=4, floor=200, cap=400, **kw)
    for x, y in zip(a[1:3], b[1:3]):
        assert np.allclose(x, y, rtol=1e-9, atol=0)


def test_two_nonces_never_exceed_the_budget_squared():
    """min(G, B) min(G', B) <= B^2, so the pair bound is at most u B^2."""
    ts, _, _, _, upper2 = pair_bounds(F, 1 / 3, budget_bits=1, per_bit=4, **MODELS["worst"])
    cap = 2.0 ** -ts * 4.0
    assert np.all(upper2 <= np.minimum(1.0, cap) + 1e-12)
    assert np.any(np.isclose(upper2[cap < 1], cap[cap < 1], rtol=1e-9))   # the cap binds somewhere


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
    ts, lower, _, _ = bounds(F, ALPHA, budget_bits=40, after_cutoff=False, **kw)
    for t in (6, 8):
        n = np.arange(1, 2 ** t + 1)
        exact = 2.0 ** -t * tail(F, ALPHA, np.log2(n), **kw).sum()
        low = lower[int(np.searchsorted(ts, t))]
        assert low <= exact * (1 + 1e-12) and exact <= 1.1 * low, (t, low, exact)


def test_the_shifted_table_counts_the_choices_after_the_cut_off():
    """log2 S_d given Z = z, by depth and lead, against the choices counted directly."""
    depths, cap, floor = 40, 60, 30
    for z in (0, 1, 3, 7):
        tab = _ztable(_table(depths, cap + z), z, depths, cap, floor)
        for d in range(depths + 1):
            for lead in range(-floor, cap + 1):
                wins = lead + d
                want = _choices(wins, d, z) if wins >= 0 else 0.0
                got = tab[d, lead + floor]
                if want == 0.0:
                    assert got == -np.inf, (z, d, lead)
                else:
                    assert got == pytest.approx(math.log2(want), rel=1e-9, abs=1e-9), (z, d, lead)


@pytest.mark.parametrize("model", list(MODELS))
def test_one_walk_mixes_the_leads_after_the_cut_off(model):
    """P(M >= 2^x) and the union's sums mixed over Z, against a walk for each Z on its own table.
    The union's terms above every threshold are left out: there the truncations differ."""
    kw = MODELS[model]
    depths, cap, floor, xs = 2000, 80, 60, np.arange(41) / 2
    first, step = walk(F, ALPHA, **kw)
    pz = post_cutoff(F, ALPHA, **kw)[:12]
    zmax = pz.size - 1
    base = _table(depths, cap + zmax)
    tab = _ztable(base, 0, depths, cap + zmax, floor)
    got, reach = _max_tail_mixed(first, step, base, tab, xs, floor, cap, pz)
    d_before, m_before, init = _union_before(first, step, base, xs, floor, cap, pz)
    d_after, m_after, reach_u = _union(init, 0.0, step, tab, xs)
    assert max(reach, reach_u) <= depths
    want, diff, mass = np.zeros(xs.size), np.zeros(xs.size + 1), np.zeros(xs.size)
    for z, w in enumerate(pz):
        tz = _ztable(base, z, depths, cap, floor)
        init_z, over_z = _place(first, floor, tz.shape[1])
        t, r = _max_tail(init_z, over_z, step, tz, xs)
        dz, mz, ru = _union(init_z, over_z, step, tz, xs)
        assert max(r, ru) <= depths
        want, diff, mass = want + w * t, diff + w * dz, mass + w * mz
    assert np.allclose(got, want, rtol=1e-9, atol=0)
    assert np.allclose((d_before + d_after)[:-1], diff[:-1], rtol=1e-9, atol=0)
    assert np.allclose(m_before + m_after, mass, rtol=1e-9, atol=0)
