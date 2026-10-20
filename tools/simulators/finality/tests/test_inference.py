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


def test_after_deflation_the_honest_stake_alone_fills_slots_at_f_and_the_race_reads_the_convention():
    """On the engine's tree with every estimate at ``1 - α`` of the true stake while the coalition
    withholds: the honest stake alone occupies slots at ``f`` and the coalition at the raised
    threshold, which are the lottery's identities, and the canonical growth per honest win is the
    one everyone producing at ``f`` gives (A1's measure, the report's convention), well below the
    growth of the chain withheld from at the true thresholds."""
    from tsi_sim.config import SimConfig

    from finality_sim.baseline import run
    from finality_sim.race import withhold_tree
    alpha, reps = 1 / 3, 8
    base = dict(n_nodes=1000, stake_dist="uniform", topology="blend", degree=6, link_latency_dist="geo",
                k=256, epochs=1, f=F, max_uncles=0, prune_arrival=False, adversary_strategy="withhold",
                blend_hops=3, blend_delay_max=3.0, blend_delay_dist="rounds", link_latency_mean=0.1)
    lam = -math.log(1 - F)
    slots = honest = coalition = canon_deflated = canon_withheld = 0
    for rep in range(reps):
        cfg = SimConfig(**base, adversary_frac=alpha, replicate=rep)
        tree, _, mask, public, canonical = withhold_tree(cfg, 1 - alpha)
        slots += cfg.epoch_len
        honest += np.unique(tree.slot[public]).size
        coalition += np.unique(tree.slot[mask[tree.leader.clip(min=0)] & (tree.slot >= 0)]).size
        canon_deflated += int(canonical.sum())
        canon_withheld += int(withhold_tree(cfg)[4].sum())

    def sd(p):
        return math.sqrt(p * (1 - p) / slots)
    assert abs(honest / slots - F) < 4 * sd(F)
    assert abs(coalition / slots - occupancy(F, 0.5)) < 4 * sd(occupancy(F, 0.5))
    everyone = np.mean([run(SimConfig(**base, adversary_frac=0.0, replicate=rep)).growth_rate
                        for rep in range(reps)]) / lam
    deflated, withheld = canon_deflated / slots / lam, canon_withheld / slots / ((1 - alpha) * lam)
    assert abs(deflated - everyone) < 0.03 * everyone and withheld - deflated > 0.04


def test_a_cap_on_the_correction_multiplies_the_periods():
    assert periods_to_deflate(1 / 3, 0.05) == 8 and periods_to_deflate(1 / 3, 0.10) == 4
    assert periods_to_deflate(0.30, 0.05) == 7 and periods_to_deflate(0.25, 0.20) == 2
    assert periods_to_deflate(1 / 3, 1 / 3) == 1
