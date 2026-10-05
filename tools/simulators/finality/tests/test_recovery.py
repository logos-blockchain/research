"""Gates for the density test of automatic recovery (src/finality_sim/recovery.py)."""

import math

import numpy as np
import pytest

from finality_sim.recovery import honest_logpmf, log_failure, occupancy, window_needed

F = 1 / 30


def _renewal_pmf(w: int, ph: float, delta: int) -> np.ndarray:
    """N_h slot by slot: delta dead slots, then each live slot counts a win with probability ph."""
    cur = np.zeros((delta + 1, w + 2))
    cur[delta, 0] = 1.0
    for _ in range(w):
        nxt = np.zeros_like(cur)
        nxt[:-1] += cur[1:]                              # a dead slot passes
        nxt[0, :] += cur[0, :] * (1 - ph)                # a live slot without a win
        nxt[delta, 1:] += cur[0, :-1] * ph               # a counted win starts the dead time
        cur = nxt
    return cur.sum(axis=0)[:w + 1]


@pytest.mark.parametrize("delta", [0, 3, 7])
def test_worst_case_count_matches_slot_by_slot_process(delta):
    w, ph = 400, 0.06
    exact = _renewal_pmf(w, ph, delta)
    got = honest_logpmf(w, ph, delta=delta)
    keep = exact > 1e-250
    assert np.all(np.isneginf(got[~keep]) | (got[~keep] < math.log(1e-240)))
    assert np.allclose(got[keep], np.log(exact[keep]), rtol=0, atol=1e-8)


def test_delta_zero_is_the_unthinned_binomial():
    for w, a in ((300, 0.2), (2000, 0.3)):
        assert log_failure(w, a, F, delta=0) == pytest.approx(log_failure(w, a, F, growth=1.0),
                                                               rel=1e-10)


def _renewal_counts(wins: np.ndarray, delta: int) -> np.ndarray:
    dead = np.full(wins.shape[0], delta)
    count = np.zeros(wins.shape[0], dtype=np.int64)
    for t in range(wins.shape[1]):
        live = dead == 0
        hit = live & wins[:, t]
        count += hit
        dead = np.where(hit, delta, np.where(live, 0, dead - 1))
    return count


@pytest.mark.parametrize("model", [dict(growth=0.85), dict(delta=5)])
def test_failure_matches_monte_carlo(model):
    w, a, n = 300, 0.3, 200_000
    rng = np.random.default_rng(7)
    pa, ph = occupancy(F, a), occupancy(F, 1 - a)
    n_a = rng.binomial(w, pa, size=n)
    if "growth" in model:
        n_h = rng.binomial(w, model["growth"] * ph, size=n)
    else:
        n_h = _renewal_counts(rng.random((n, w)) < ph, model["delta"])
    p_mc = np.mean(n_a > n_h)
    se = math.sqrt(p_mc * (1 - p_mc) / n)
    assert math.exp(log_failure(w, a, F, **model)) == pytest.approx(p_mc, abs=4 * se)


def test_window_needed_is_the_smallest_window():
    for model in (dict(growth=0.845), dict(delta=10)):
        w = window_needed(0.25, 1e-9, F, **model)
        assert log_failure(w, 0.25, F, **model) <= math.log(1e-9)
        assert log_failure(w - 1, 0.25, F, **model) > math.log(1e-9)


def test_worst_case_pmf_holds_at_the_longest_window():
    """At 4 floor(k/f) slots for k = 2160 the lower tail leaves the float range without NaN."""
    lp = honest_logpmf(259_200, occupancy(F, 0.9), delta=1)
    assert not np.isnan(lp).any()
    assert np.exp(lp).sum() == pytest.approx(1.0, abs=1e-9)


def test_bought_keys_raise_the_fork_without_lowering_the_honest_chain():
    w, f = 3000, 1 / 30
    base = log_failure(w, 0.25, f, growth=0.845)
    assert log_failure(w, 0.25, f, growth=0.845, honest=0.75) == pytest.approx(base, rel=1e-12)
    bought = log_failure(w, 0.35, f, growth=0.845, honest=0.75)
    # worse than the fork alone, better than an adversary that holds 0.35 of the stake outright
    assert base < bought < log_failure(w, 0.35, f, growth=0.845)
