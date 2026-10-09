"""Gates for the bound on the choices at the cut-off (src/finality_sim/fork_bound.py)."""

import math

import numpy as np
import pytest

from finality_sim.fork_bound import (blocks_below, blocks_pmf, conditional_mean, deepest_fork,
                                     fork_sample, gmin_bound)
from finality_sim.nonce import _rates, min_rule_choices

F = 1 / 30
WINDOW = 6 * math.floor(2160 / F)


@pytest.mark.parametrize("kw", [dict(growth=0.845), dict(delta=10)])
def test_the_fork_law_matches_the_windows_drawn_slot_by_slot(kw):
    """P(D = d) sums to one, and E[D], E[A] and P(D >= 1) match sampled windows."""
    p, a1, a2 = deepest_fork(F, 1 / 3, **kw)
    assert p.sum() == pytest.approx(1.0, abs=1e-9)
    d, a, z = fork_sample(F, 1 / 3, 20_000, 5, **kw)
    sem = lambda x: x.std() / math.sqrt(x.size)
    e_d, e_a = float(np.sum(np.arange(p.size) * p)), float(a1.sum())
    if "growth" in kw:                                      # Z is exact under random delay
        assert e_d == pytest.approx(d.mean(), abs=4 * sem(d))
        assert e_a == pytest.approx(a.mean(), abs=4 * sem(a))
        assert 1.0 - p[0] == pytest.approx(np.mean(d >= 1), abs=0.01)
    else:                                                   # and from above under a worst case
        assert d.mean() - 2 * sem(d) <= e_d <= 1.1 * d.mean()
        assert a.mean() - 2 * sem(a) <= e_a <= 1.1 * a.mean()
        assert np.mean(d >= 1) - 0.01 <= 1.0 - p[0] <= np.mean(d >= 1) + 0.04
    assert float(np.sum(a2) - a1.sum() ** 2) == pytest.approx(a.var(), rel=0.15)
    assert np.all(a <= d + 1)                              # A = D + 1 - Z, and L_0 <= 1 when D = 0


def test_the_conditional_expectation_averages_to_the_sampled_choices():
    cond, drawn = conditional_mean(F, 1 / 3, WINDOW, 4_000, 11, sub_windows=25, delta=10)
    assert cond.mean() == pytest.approx(drawn.mean(), abs=3 * drawn.std() / math.sqrt(drawn.size))
    assert cond.std() < drawn.std() / 2                     # the contributions' noise is gone
    g, _ = min_rule_choices(F, 1 / 3, WINDOW, 4_000, 11, sub_windows=25, delta=10, near_slots=20_000)
    assert np.array_equal(g, drawn)                         # the same windows, the same count


def test_the_block_count_law_is_the_renewal_count():
    for kw in (dict(growth=0.845), dict(delta=10)):
        pmf = blocks_pmf(15_552, F, 1 / 3, **kw)
        _, h, dead, rate = _rates(F, 1 / 3, kw.get("growth"), kw.get("delta"))
        assert pmf.sum() == pytest.approx(1.0, abs=1e-9)
        assert float(np.sum(np.arange(pmf.size) * pmf)) == pytest.approx(15_552 * rate, rel=0.01)
        assert blocks_below(15_552, 200, F, 1 / 3, **kw) == pytest.approx(pmf[:200].sum(), rel=1e-6)
    # a window of slots starting anywhere holds at least as many blocks as one starting at a block
    _, h, dead, _ = _rates(F, 1 / 3, None, 10)
    rng = np.random.default_rng(2)
    counts = []
    for _ in range(400):
        t, last, n = 0, -10_000, 0
        while t < 40_000:
            if rng.random() < h and t - last > dead:
                last = t
                if t >= 20_000:
                    n += 1
            t += 1
        counts.append(n)
    assert np.mean(counts) >= float(np.sum(np.arange(blocks_pmf(20_000, F, 1 / 3, delta=10).size)
                                           * blocks_pmf(20_000, F, 1 / 3, delta=10))) - 1.0


def test_the_bound_lies_above_the_conditional_mean_and_adds_up():
    sub = WINDOW // 25
    b = gmin_bound(F, 1 / 3, sub, 227, delta=10)
    cond, _ = conditional_mean(F, 1 / 3, WINDOW, 3_000, 17, sub_windows=25, delta=10)
    assert b["bound"] >= cond.mean() + 3 * cond.std() / math.sqrt(cond.size)
    assert b["bound"] < 1.15 and b["mass"] == pytest.approx(1.0, abs=1e-9)
    # the main term from the fork law directly
    p, a1, _ = deepest_fork(F, 1 / 3, delta=10)
    harm = np.concatenate(([0.0], np.cumsum(1.0 / np.arange(1, 3000))))
    main = sum(p[d] * (harm[227] - harm[227 - d]) + a1[d] / (227 - d + 1) for d in range(227))
    assert b["main"] == pytest.approx(main, rel=1e-9)
    assert b["bound"] == pytest.approx(1 + b["main"] + b["tail_d"] + b["tail_n"] + b["cross"], rel=1e-12)
    # a shorter sub-window crosses more often, and the bound follows the sampled mean up
    short = gmin_bound(F, 1 / 3, 2_880, 40, delta=10)
    g, _ = min_rule_choices(F, 1 / 3, 77_760, 3_000, 3, sub_windows=27, delta=10, near_slots=10_000)
    assert short["cross"] > 10 * b["cross"] and short["bound"] >= g.mean()
    # the crossing term is the sum its pieces describe: the emptied sub-window's factor c + A_0,
    # weighted by the previous sub-window's bound at the offset A_0 + Z - N, where that is positive
    from finality_sim.fork_bound import _crossing, _crossing_parts
    n_max = 2_880 // 11 + 1
    harm = np.concatenate(([0.0], np.cumsum(1.0 / np.arange(1, n_max + 2))))
    c = 1.0 + harm[n_max]
    phi, pz, p_n, ws, p_w = _crossing_parts(F, 1 / 3, 2_880, 40, None, 10, 200, harm, c)
    total = 0.0
    for w, pw in zip(ws, p_w):
        for z, pzz in enumerate(pz):
            for n, pn in enumerate(p_n):
                o = w + z - n
                if o >= 1:
                    total += pw * pzz * pn * (c + w) * phi[min(o, phi.size - 1)]
    assert _crossing(F, 1 / 3, 2_880, 40, None, 10, 200, harm, c) == pytest.approx(total, rel=1e-9)
