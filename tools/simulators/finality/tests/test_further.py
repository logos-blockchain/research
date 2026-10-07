"""Gates for the further routes (src/finality_sim/further.py)."""

import math

import numpy as np
import pytest

from finality_sim.further import density_depth, lead_lasts
from finality_sim.grinding import post_cutoff
from finality_sim.nonce import _rates
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


def test_without_the_density_test_the_rule_is_the_depth_table():
    g, eps = 0.845, 1e-6
    d, w = density_depth(0.30, g, eps, F, test=False)
    assert d == strict_depth(0.30 / (0.30 + 0.70 * g), math.log(eps)) and w == 0.30


def test_the_density_test_settles_sooner_and_holds_every_share():
    """At the accepted depth no share up to the bound gets more than eps; one block earlier some
    share does."""
    g, eps, alpha = 0.845, 1e-6, 0.30
    plain = int(strict_depth(alpha / (alpha + (1 - alpha) * g), math.log(eps)))
    d, w = density_depth(alpha, g, eps, F)
    assert d < plain and 0 < w <= alpha
    lam = -math.log(1 - F)

    def worst(depth):
        n = depth + 1
        t = n / (g * lam)
        out = -np.inf
        for s in np.append(np.arange(0.01, alpha, 0.01), alpha):
            q = s / (s + (1 - s) * g)
            from scipy import stats
            out = max(out, log_strict(q, n) + float(stats.poisson.logsf(n - 1, (1 - s) * g * lam * t)))
        return out
    assert worst(d) <= math.log(eps) < worst(d - 1)
