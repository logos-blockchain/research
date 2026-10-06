"""Gates for the balancing attack on the slot lottery (src/finality_sim/balance.py)."""

import math

import numpy as np
import pytest

from finality_sim.balance import _phases, hold_shares, phase_stats, threshold
from finality_sim.ghost import ghost_adversarial, ghost_deterministic


@pytest.mark.parametrize("f,delta,alpha", [(1 / 30, 10, 0.4), (0.25, 5, 0.15), (0.25, 10, 0.05)])
def test_phase_statistics_match_the_closed_form(f, delta, alpha):
    lam = -math.log(1 - f)
    h, a = _phases(20_000_000, (1 - alpha) * lam, alpha * lam, delta, 3)
    ea, odd, busy = phase_stats(f, alpha, delta)
    n = h.size
    assert a.mean() == pytest.approx(ea, abs=4 * a.std() / math.sqrt(n))
    assert (h % 2).mean() == pytest.approx(odd, abs=4 * math.sqrt(odd * (1 - odd) / n))
    assert (h > 0).mean() == pytest.approx(busy, abs=4 * math.sqrt(busy * (1 - busy) / n))


@pytest.mark.parametrize("ties,rule", [("adversarial", ghost_adversarial),
                                       ("deterministic", ghost_deterministic)])
def test_fine_slots_reach_the_continuous_threshold(ties, rule):
    """Slots a hundred times finer give the paper's continuous-time region."""
    f, delta, scale = 0.25, 5, 100
    lam = -math.log(1 - f)
    lo, hi = 0.0, 0.5
    for _ in range(100):
        mid = (lo + hi) / 2
        if mid * lam < rule((1 - mid) * lam, delta):
            lo = mid
        else:
            hi = mid
    fine = threshold(1 - math.exp(-lam / scale), delta * scale, ties)
    assert fine == pytest.approx(lo, rel=0.01)


def test_the_balance_holds_only_above_the_threshold():
    f, delta = 0.25, 5
    t = threshold(f, delta, "adversarial")
    above = hold_shares(f, 1.3 * t, delta, (200, 2000), 4_000_000, 5)
    below = hold_shares(f, 0.7 * t, delta, (200, 2000), 4_000_000, 5)
    assert above[1] > 0.2 and above[0] >= above[1]
    assert below[1] < 0.01
