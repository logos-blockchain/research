"""Gates for the inference lever (src/finality_sim/inference.py)."""

import math

import numpy as np
import pytest

from finality_sim.inference import (deflated_delay, extra_wins, periods_to_deflate, raise_factor,
                                    raised_rates, selection_excess)
from finality_sim.recovery import occupancy

F = 1 / 30


def test_a_period_of_withholding_raises_every_threshold_by_the_share_withheld():
    # the honest stake alone fills slots at f; the worst case of 10 s reads as 15 s against a third
    h, a = raised_rates(F, 1 / 3)
    assert h == pytest.approx(F) and a == pytest.approx(occupancy(F, 0.5))
    assert deflated_delay(10.0, 1 / 3) == pytest.approx(15.0)
    assert deflated_delay(10.0, 0.3) == pytest.approx(10 / 0.7)
    assert raise_factor(0.25) == pytest.approx(4 / 3)
    # the catch-up ratio barely moves: the raise scales both sides
    assert a / h == pytest.approx(occupancy(F, 1 / 3) / occupancy(F, 2 / 3), rel=0.01)


def test_the_selection_excess_is_the_brownian_maximum():
    m = extra_wins(F, 1 / 3, 10 * math.floor(2160 / F))
    assert m == pytest.approx(648_000 * (occupancy(F, 0.5) - occupancy(F, 1 / 3)))
    brown, mc = selection_excess(m, 4_370, 4_000, 3)
    assert brown == pytest.approx(math.sqrt(2 * m / math.pi))
    assert mc == pytest.approx(brown, rel=0.05)
    assert mc < 0.02 * 648_000 * occupancy(F, 0.5)          # under two percent of its wins


def test_a_cap_on_the_correction_multiplies_the_periods():
    assert periods_to_deflate(1 / 3, 0.05) == 8 and periods_to_deflate(1 / 3, 0.10) == 4
    assert periods_to_deflate(0.30, 0.05) == 7 and periods_to_deflate(0.25, 0.20) == 2
    assert periods_to_deflate(1 / 3, 1 / 3) == 1
