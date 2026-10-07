"""Gates for the further routes (src/finality_sim/further.py)."""

import math

import numpy as np
import pytest
from scipy import stats

from finality_sim.further import (delayed_factor, density_chance, density_depth, lead_lasts,
                                  time_rule_depth)
from finality_sim.grinding import post_cutoff
from finality_sim.nonce import _rates, min_rule_choices
from finality_sim.private_race import log_strict, strict_depth

F = 1 / 30


@pytest.mark.parametrize("kw", [dict(growth=0.845), dict(delta=10)])
def test_the_lead_lasts_as_long_as_its_mean_drift_allows(kw):
    """Every lead lasts zero slots; a lead of z lasts z / (h_c - a) slots; longer times need a
    longer lead, so the chance falls."""
    a, _, _, rate = _rates(F, 1 / 3, kw.get("growth"), kw.get("delta"))
    z = post_cutoff(F, 1 / 3, **kw)
    assert lead_lasts(F, 1 / 3, 0, **kw) == pytest.approx(1.0)
    for minutes in (1, 10, 60):
        need = math.ceil(60 * minutes * (rate - a))
        assert lead_lasts(F, 1 / 3, 60 * minutes, **kw) == pytest.approx(z[need:].sum())
    p = [lead_lasts(F, 1 / 3, t, **kw) for t in (60, 600, 3600, 36_000)]
    assert all(x > y for x, y in zip(p, p[1:])) and p[-1] < 1e-6


def test_the_delayed_factor_runs_from_every_choice_to_none():
    """With no delay every choice at the cut-off counts; with a delay the lead cannot outlast, none;
    in between the factor falls with the delay."""
    window, m = 6 * 32_400, 26
    g, _, z = min_rule_choices(F, 1 / 3, window, 4000, 11, sub_windows=m, delta=10,
                               near_slots=20_000, with_lead=True)
    none = delayed_factor(F, 1 / 3, window, m, 0, 4000, 11, delta=10)
    assert none == pytest.approx(g.mean()) and g.mean() > 1.05
    f5, f20 = (delayed_factor(F, 1 / 3, window, m, t, 4000, 11, delta=10) for t in (5, 20))
    assert none > f5 > f20 >= 1.0
    assert delayed_factor(F, 1 / 3, window, m, 24 * 60, 4000, 11, delta=10) == 1.0


def test_the_time_rule_settles_an_unattacked_chain_sooner_and_the_adjusted_rule_later():
    g, eps, alpha = 0.845, 1e-6, 0.30
    plain = int(strict_depth(alpha / (alpha + (1 - alpha) * g), math.log(eps)))
    full, held = time_rule_depth(alpha, g, eps, F), time_rule_depth(alpha, g, eps, F, full_rate=False)
    assert 0 < full < held <= plain
    assert time_rule_depth(alpha, g, eps, F, adjusted=True) > full
    assert time_rule_depth(alpha, g, eps, F, full_rate=False, adjusted=True) > held


def test_without_the_density_test_the_rule_is_the_depth_table():
    g, eps = 0.845, 1e-6
    d, w = density_depth(0.30, g, eps, F, test=False)
    assert d == strict_depth(0.30 / (0.30 + 0.70 * g), math.log(eps)) and w == 0.30


def test_the_density_rule_is_sound_where_it_accepts_and_later_than_the_time_rule():
    """At its acceptance the exact conditional chance is below eps, and B4's elapsed-time rule has
    accepted earlier; one block before, some share exceeds the density rule's own condition."""
    g, eps, alpha = 0.845, 1e-6, 0.30
    d, w = density_depth(alpha, g, eps, F)
    assert density_chance(alpha, g, eps, F) <= math.log(eps)
    assert time_rule_depth(alpha, g, eps, F) < d + 1
    lam = -math.log(1 - F)

    def worst(depth):
        n = depth + 1
        t = n / (g * lam)
        out = -np.inf
        for s in np.append(np.arange(0.01, alpha, 0.01), alpha):
            q = s / (s + (1 - s) * g)
            out = max(out, log_strict(q, n) + float(stats.poisson.logsf(n - 1, (1 - s) * g * lam * t)))
        return out
    assert worst(d) <= math.log(eps) < worst(d - 1) and 0 < w <= alpha
