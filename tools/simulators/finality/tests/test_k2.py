"""Gates for K.1 and K.2's readings of the slot rule (scripts/k1_settle.py, scripts/k2_holds.py)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

from finality_sim.recovery import occupancy
from finality_sim.slots import lead_law, rates, wait_logfail, worst_logbound

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from b2_settlement import upper  # noqa: E402
from k2_holds import deflated, held_random  # noqa: E402

F = 1 / 30
G = 0.845


@pytest.mark.parametrize("alpha", [0.25, 1 / 3])
def test_raising_both_rates_shortens_the_wait_by_their_factor(alpha):
    """In B4's model a wait of T at rates c·a and c·h is a wait of c·T at a and h: the reading of a
    deflated inference in the convention's model, where both rates rise by 1/(1 − α)."""
    a, h = rates(alpha, G, F)
    c = 1 / (1 - alpha)
    for t in (2_000, 9_000):
        raised = wait_logfail(t, alpha, G, F, a=c * a, h=c * h)
        assert raised == pytest.approx(wait_logfail(c * t, alpha, G, F), rel=1e-10)
        assert raised < wait_logfail(t, alpha, G, F)


def test_the_occupancies_given_move_the_worst_case_bound():
    """A faster honest chain lowers the bound at a given wait, a faster coalition raises it."""
    alpha, delta, t = 0.3, 10, 30_000
    log_ub = np.log(np.minimum(upper(alpha, delta, 800), 1.0))
    p_h, p_a = occupancy(F, 1 - alpha), occupancy(F, alpha)
    base = worst_logbound(t, alpha, delta, log_ub, F)[0]
    faster = worst_logbound(t, alpha, delta, log_ub, F, lead_law(p_a, 1.2 * p_h, delta), p_h=1.2 * p_h)[0]
    stronger = worst_logbound(t, alpha, delta, log_ub, F, lead_law(1.2 * p_a, p_h, delta), p_a=1.2 * p_a)[0]
    assert faster < base - 1.0
    assert stronger > base + 1e-6


@pytest.mark.parametrize("alpha", [0.25, 0.3, 1 / 3])
def test_a_deflated_inference_is_the_lottery_at_a_raised_rate(alpha):
    """Raising every threshold by 1/(1 − α) is the lottery at f' = 1 − (1 − f)^(1/(1 − α)) with
    the shares unchanged: the honest stake then fills slots at f."""
    f2 = 1 - (1 - F) ** (1 / (1 - alpha))
    p_h, p_a = deflated(alpha)
    assert p_h == pytest.approx(1 - (1 - f2) ** (1 - alpha), rel=1e-12)
    assert p_a == pytest.approx(1 - (1 - f2) ** alpha, rel=1e-12)
    assert p_h == pytest.approx(F, rel=1e-12)


def test_the_share_a_wait_holds_is_where_its_chance_reaches_eps():
    """``held_random`` returns the share at which the wait's chance crosses 1e-9, and a longer
    wait holds a larger share."""
    short, long_ = held_random(20_000, G), held_random(60_000, G)
    assert 0.2 < short < long_ < 0.5
    eps = math.log(1e-9)
    assert wait_logfail(20_000, short, G, F) <= eps < wait_logfail(20_000, short + 1e-4, G, F)


def test_a_deflated_inference_helps_at_one_second_and_costs_at_ten():
    """In slots the raised thresholds speed the honest chain up while the delay, fixed in slots,
    weighs more: against a third the first wins at 1 s and the second at 10 s (``worst_log``)."""
    from k2_holds import worst_log
    third = 1 / 3
    for delta, K, deflation_helps in ((1, 35_000, True), (10, 100_000, False)):
        plain = np.log(np.minimum(upper(third, delta, 2_500), 1.0))
        raised = np.log(np.minimum(upper(third, delta / (1 - third), 2_500), 1.0))
        before = worst_log(third, delta, K, plain, False)
        after = worst_log(third, delta, K, raised, True)
        assert (after < before - 1.0) if deflation_helps else (after > before + 1.0), (delta, before, after)
