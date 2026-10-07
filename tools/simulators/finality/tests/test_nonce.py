"""Gates for the nonce taken from the smallest contributions (src/finality_sim/nonce.py)."""

import itertools
import math

import numpy as np
import pytest
from numba import njit

from finality_sim.grinding import _choices
from finality_sim.nonce import (_choices_min, _feasible, _last_sub_window, _rates, displacement,
                                estimate, last_sub_window, min_rule_choices, own_share,
                                predicted_share)
from finality_sim.recovery import occupancy

F = 1 / 30


def _reachable(canon, adv, feasible, h_rho, w_rho, far_min, sub):
    """By enumeration: from every fork point the flags allow, every subset of the coalition's wins
    after it; the number of distinct tuples of sub-window minima."""
    n = canon.size
    n_sub = (n - 2) // sub + 1
    honest = [t for t in range(n - 1, 0, -1) if canon[t]]
    wins = [t for t in range(n - 1, 0, -1) if adv[t]]
    seen = set()
    for d in range(len(honest) + 1):
        if not feasible[d]:
            continue
        fork = honest[d] if d < len(honest) else 0
        kept = [(honest[j], h_rho[j]) for j in range(d, len(honest))]
        free = [(t, w_rho[w]) for w, t in enumerate(wins) if t > fork]
        for r in range(len(free) + 1):
            for chosen in itertools.combinations(free, r):
                mu = [math.inf] * n_sub
                mu[n_sub - 1] = far_min
                for t, x in kept + list(chosen):
                    i = (n - 1 - t) // sub
                    mu[i] = min(mu[i], x)
                seen.add(tuple(mu))
    return len(seen)


def test_the_count_bounds_the_nonces_the_coalition_can_reach():
    """At least the distinct tuples of minima the forks reach, and exactly them with one sub-window."""
    rng = np.random.default_rng(5)
    singles = multiples = 0
    for _ in range(4000):
        n = int(rng.integers(2, 26))
        canon = rng.random(n) < 0.3
        adv = rng.random(n) < 0.25
        if adv[1:].sum() > 8:
            continue
        nh = int(canon[1:].sum())
        feasible = rng.random(nh + 1) < 0.5
        feasible[0] = True
        h_rho, w_rho = rng.random(nh), rng.random(int(adv[1:].sum()))
        far = float(rng.random()) if rng.random() < 0.7 else math.inf
        sub = int(rng.integers(1, n + 1))
        g, _ = _choices_min(canon, adv, feasible, h_rho, w_rho, far, sub)
        want = _reachable(canon, adv, feasible, h_rho, w_rho, far, sub)
        assert g >= want
        if (n - 2) // sub == 0:
            assert g == want
            singles += 1
        elif want > 4:
            multiples += 1
    assert singles > 500 and multiples > 50


def test_a_fork_wins_where_the_grinding_model_counts_a_choice():
    """For d >= 1 a fork from depth d wins exactly when grinding's S_d, given Z = z, is positive."""
    rng = np.random.default_rng(6)
    for _ in range(500):
        n = int(rng.integers(2, 200))
        canon = rng.random(n) < 0.1
        adv = rng.random(n) < 0.05
        z = int(rng.integers(0, 4))
        feasible = np.zeros(n + 1, dtype=bool)
        d_all = _feasible(canon, adv, z, feasible)
        wins, d = 0, 0
        for t in range(n - 1, 0, -1):
            if canon[t]:
                assert feasible[d] == (d == 0 or _choices(wins, d, z) > 0)
                d += 1
            if adv[t]:
                wins += 1
        assert d == d_all


@njit(cache=True)
def _own(n_rep, h, a, dead, slots, seed):
    np.random.seed(seed)
    total = 0.0
    for _ in range(n_rep):
        last, nh, na = -dead - 1, 0, 0
        for t in range(slots):
            if np.random.random() < h and t - last > dead:
                last = t
                nh += 1
            if np.random.random() < a:
                na += 1
        total += na / (na + nh)
    return total / n_rep


@pytest.mark.parametrize("kw", [dict(growth=0.845), dict(delta=10)])
@pytest.mark.parametrize("alpha", [0.25, 1 / 3])
def test_the_coalition_holds_the_smallest_contribution_in_proportion_to_its_rate(kw, alpha):
    """Slot by slot, the coalition's wins over all contributions of a long sub-window."""
    a, ph = occupancy(F, alpha), occupancy(F, 1 - alpha)
    h, dead = (kw["growth"] * ph, 0) if "growth" in kw else (ph, kw["delta"])
    assert _own(2000, h, a, dead, 40_000, 7) == pytest.approx(own_share(F, alpha, **kw), abs=0.003)


def test_displacement_is_a_race_from_one_behind_plus_the_free_channels():
    """From the rates alone: r^2 under random delay without ties; with ties o r + (1 - o) r^2; under
    a worst case the free channel is a rival or an own win within Delta, then the race."""
    for alpha in (0.30, 1 / 3):
        a, h, _, rate = _rates(F, alpha, 0.845, None)
        r = a / rate
        assert displacement(F, alpha, growth=0.845) == pytest.approx(r * r)
        assert displacement(F, alpha, growth=0.845, orphan=0.18) == pytest.approx(0.18 * r + 0.82 * r * r)
        a, _, _, rate = _rates(F, alpha, None, 10)
        ph = occupancy(F, 1 - alpha)
        free = 1 - ((1 - ph) * (1 - a)) ** 10
        assert displacement(F, alpha, delta=10) == pytest.approx(free + (1 - free) * (a / rate) ** 2)
        assert displacement(F, alpha, delta=10) > displacement(F, alpha, growth=0.845, orphan=0.18)


def test_the_predicted_share_solves_its_recursion():
    for own, coin in ((0.37, 0.35), (0.38, 0.56), (0.1, 0.0)):
        p = predicted_share(own, coin)
        assert p == pytest.approx(own + (1 - own) * coin * p)
    assert predicted_share(0.3809, 0.0) == 0.3809


def test_the_reachable_minima_match_their_closed_forms():
    """Without removals both counts average 1 / (1 - p_own); with them, attempting any honest block
    averages 1 / ((1 - coin)(1 - p_own)); records only reach fewer."""
    a, h, dead, rate = _rates(F, 1 / 3, None, 10)
    own = a / (a + rate)
    none, none_rec = _last_sub_window(3000, h, a, dead, 6000, 0.0, 3)
    assert none.mean() == pytest.approx(1 / (1 - own), rel=0.03)
    assert np.array_equal(none, none_rec)
    coin = displacement(F, 1 / 3, delta=10)
    any_block, records = last_sub_window(F, 1 / 3, 6000, 3000, 4, delta=10)
    assert any_block.mean() == pytest.approx(1 / ((1 - coin) * (1 - own)), rel=0.03)
    assert np.all(records <= any_block) and records.mean() < any_block.mean()
    assert estimate(1.0, 1.0, 0.5) == 1.0 and estimate(1.05, 2.0, 0.5) == pytest.approx(1.05 * 2.0 * 2.0)


def test_forks_near_the_cut_off_add_little():
    """At a third under the worst case at 10 s, over today's window at k = 2160: no fork reaches
    past the near slots, and the count stays close to one."""
    for m, top in ((1, 1.01), (22, 1.1)):
        got, deep = min_rule_choices(F, 1 / 3, 6 * 64_800, 20_000, 4, sub_windows=m, delta=10,
                                     near_slots=20_000)
        assert deep == 0
        assert 1.0 <= got.mean() < top
