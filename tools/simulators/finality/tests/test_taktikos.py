"""Gates for the Taktikos lottery and its block-tree builder (src/finality_sim/taktikos.py)."""

import math

import numpy as np
import pytest
from tsi_sim.config import SimConfig

from finality_sim.baseline import build_epoch as engine_epoch
from finality_sim.baseline import measure_epoch
from finality_sim.taktikos import Curve, build_epoch, constant, mean_interval, win_prob

F = 1 / 30


def test_constant_curve_interval_is_geometric():
    for share in (1.0, 0.25):
        assert mean_interval(constant(F), share) == pytest.approx(
            1 / (1 - (1 - F) ** share), rel=1e-9)


def test_snowplow_interval_matches_a_slot_by_slot_draw():
    curve = Curve(gap=5, cutoff=60, amp=0.2, base=0.03)
    rng = np.random.default_rng(5)
    n, delta = 200_000, np.zeros(200_000, np.int64)
    done = np.zeros(n, dtype=bool)
    d = 0
    while not done.all():
        d += 1
        hit = ~done & (rng.random(n) < win_prob(curve, 0.4, d))
        delta[hit] = d
        done |= hit
    se = delta.std() / math.sqrt(n)
    assert mean_interval(curve, 0.4) == pytest.approx(delta.mean(), abs=4 * se)


def _cfg(rep):
    return SimConfig(n_nodes=300, stake_dist="pareto", topology="blend", degree=6,
                     link_latency_dist="geo", link_latency_mean=0.1, blend_hops=3,
                     blend_delay_max=3.0, blend_delay_dist="rounds", k=64, f=F, max_uncles=0,
                     prune_arrival=False, replicate=rep)


def test_constant_curve_reproduces_the_engine_orphan_share():
    mine = [measure_epoch(*build_epoch(_cfg(r), constant(F)), _cfg(r).epoch_len).orphan_share
            for r in range(8)]
    ref = [measure_epoch(*engine_epoch(_cfg(r)), _cfg(r).epoch_len).orphan_share
           for r in range(8)]
    se = math.sqrt(np.var(mine, ddof=1) / 8 + np.var(ref, ddof=1) / 8)
    assert np.mean(mine) == pytest.approx(np.mean(ref), abs=3 * se)


def test_snowplow_shape():
    c = Curve(gap=10, cutoff=50, amp=0.2, base=0.03)
    assert c([1, 10, 30, 50, 51, 500]).tolist() == pytest.approx([0, 0, 0.1, 0.2, 0.03, 0.03])
    assert constant(F)([1, 7, 1000]).tolist() == pytest.approx([F, F, F])


def test_renewal_slots_keep_the_mean_interval():
    from finality_sim.taktikos import renewal_slots
    curve = Curve(gap=0, cutoff=40, amp=0.15, base=0.004)
    t = renewal_slots(curve, 0.25, 3_000_000, np.random.default_rng(2))
    gaps = np.diff(t)
    se = gaps.std() / math.sqrt(gaps.size)
    assert gaps.mean() == pytest.approx(mean_interval(curve, 0.25), abs=4 * se)
