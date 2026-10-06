"""Gates for Phase C3 (src/finality_sim/ghost.py)."""

import math

import pytest

from finality_sim.ghost import ghost_adversarial, ghost_deterministic, lcr, max_share


def dembo_threshold(x: float) -> float:
    """Dembo et al. eq. (2) at equality, x = f Delta (as gated in firstlook.py)."""
    return ((2 + x) - math.sqrt(4 + x * x)) / (2 * x)


@pytest.mark.parametrize("delta", [1, 5, 10, 20, 30])
def test_longest_chain_region_is_the_private_attack_threshold(delta):
    f = 1 / 30
    assert max_share(lcr, f, delta) == pytest.approx(dembo_threshold(f * delta), abs=1e-9)


@pytest.mark.parametrize("rho_h_delta,want", [
    # (rho_h Delta) -> rho_a Delta bounds LCR / GHOST-det / GHOST-adv: the inequality on p. 3 and
    # equations (2) and (1) of revision 2026-09-11 at the middle of its Fig. 1 axis
    (1.0, (0.5, math.exp(-1), math.exp(-1) / (2 - math.exp(-1)))),
])
def test_region_formulas_at_unit_honest_load(rho_h_delta, want):
    rho_h, delta = rho_h_delta, 1.0
    got = (lcr(rho_h, delta) * delta, ghost_deterministic(rho_h, delta) * delta,
           ghost_adversarial(rho_h, delta) * delta)
    assert got == pytest.approx(want, rel=1e-12)


def test_ghost_never_beats_longest_chain():
    f = 1 / 30
    for delta in (1, 2, 5, 10, 20, 30, 60):
        lc = max_share(lcr, f, delta)
        assert max_share(ghost_deterministic, f, delta) <= lc
        assert max_share(ghost_adversarial, f, delta) <= lc
