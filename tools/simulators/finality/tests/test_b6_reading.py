"""Gates for how B6 reads the grinding bounds (scripts/b6_grinding.py, scripts/b5_what_k_holds.py)."""

import math
import pathlib
import sys

import numpy as np
import pytest

from finality_sim.grinding import PER_BIT

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from b5_recovery_sweep import STEP_DAYS, at  # noqa: E402
from b5_what_k_holds import GRID, held_worst, max_alpha  # noqa: E402
from b6_grinding import ground_chance, held_random, lookup  # noqa: E402

TS = np.arange(200 * PER_BIT + 1) / PER_BIT
IDENTITY = 2.0 ** -TS                                 # phi(u) = u: an honest nonce
NEVER = np.zeros_like(TS)
RATE = 1e-6                                           # chance per day of age


def flat(days: float = 400.0) -> np.ndarray:
    return RATE * STEP_DAYS * np.arange(int(days / STEP_DAYS) + 1)


def test_the_upper_bound_is_read_at_the_next_larger_u():
    u = np.array([0.0, 2.0 ** -5, 2.0 ** -5.01, 3.0])
    got = lookup(IDENTITY, u)
    assert got[0] == 0.0 and got[1] == 2.0 ** -5 and got[3] == 1.0
    assert u[2] <= got[2] <= u[2] * 2 ** (1 / PER_BIT)


@pytest.mark.parametrize("phase", [0.0, 1.3, 6.9])
def test_every_age_is_read_once(phase):
    """With honest nonces in both groups the sum is the plain one, within a grid step."""
    acc, epoch, window, h = flat(), 7.5, 1 / 3, 100.0
    plain = float(at(acc, h))
    got = ground_chance(acc, h, phase, epoch, window, IDENTITY, IDENTITY)
    assert plain <= got <= plain * 2 ** (1 / PER_BIT)


def test_the_spill_is_the_youngest_window_of_each_epoch():
    """Three whole epochs: each spills its youngest window into the next epoch."""
    acc, epoch, window = flat(), 0.4, 1 / 6
    inside = ground_chance(acc, 3 * epoch, 0.0, epoch, window, IDENTITY, NEVER)
    want = RATE * 3 * (epoch - window)
    assert want * (1 - 1e-9) <= inside <= want * 2 ** (1 / PER_BIT)
    spill = ground_chance(acc, 3 * epoch, 0.0, epoch, window, NEVER, IDENTITY)
    want = RATE * 3 * window
    assert want * (1 - 1e-9) <= spill <= want * 2 ** (1 / PER_BIT)


def test_without_a_factor_the_share_is_b5s():
    grid = np.round(np.arange(0.05, 0.4301, 0.01), 4)
    for k in (120, 432, 2160):
        assert held_random(grid, np.zeros(grid.size), 0.845, k) == pytest.approx(
            max_alpha(k, 0.845, 1e-9), abs=1e-9)


def test_the_worst_case_share_is_the_crossing():
    a0, eps = 0.2123, 1e-9
    logs = 40.0 * (GRID - a0) + math.log(eps)
    assert held_worst(logs, eps) == pytest.approx(a0, abs=1e-12)
    assert held_worst(logs, eps, 40.0 * 0.01) == pytest.approx(a0 - 0.01, abs=1e-12)
    assert math.isnan(held_worst(logs + 100.0, eps))
    assert math.isinf(held_worst(logs - 100.0, eps))
