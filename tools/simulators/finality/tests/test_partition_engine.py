"""Gates for the partition on the engine (src/finality_sim/partition.py)."""

import numpy as np
import pytest
from tsi_sim.config import SimConfig

from finality_sim.partition import best_tip, chain_slots, measure
from finality_sim.race import _tree, partition_tree, withhold_tree

BASE = dict(n_nodes=60, stake_dist="uniform", topology="blend", degree=6, link_latency_dist="geo",
            link_latency_mean=0.1, blend_hops=3, blend_delay_max=3.0, blend_delay_dist="rounds",
            k=16, epochs=1, f=1 / 30, max_uncles=0, prune_arrival=False, adversary_strategy="withhold")


def test_no_block_crosses_the_cut_before_the_span_ends_and_the_sides_diverge():
    cfg = SimConfig(**BASE, adversary_frac=0.3, replicate=2, partition_share=0.35,
                    partition_start=500, partition_slots=2_000)
    tree, arrival, stake, mask, side, public = partition_tree(cfg)
    end = 2_500
    a_nodes, b_nodes = np.nonzero(side)[0], np.nonzero(~side & ~mask)[0]
    in_span = (tree.slot >= 500) & (tree.slot < end) & public
    made_a = in_span & side[tree.leader.clip(min=0)]
    made_b = in_span & (~side & ~mask)[tree.leader.clip(min=0)]
    assert made_a.sum() > 5 and made_b.sum() > 5
    assert np.all(arrival[np.ix_(b_nodes, np.nonzero(made_a)[0])] >= end)
    assert np.all(arrival[np.ix_(a_nodes, np.nonzero(made_b)[0])] >= end)
    tip_a, tip_b = best_tip(tree, arrival, a_nodes, end - 1), best_tip(tree, arrival, b_nodes, end - 1)
    assert tip_a != tip_b
    sa, sb = set(chain_slots(tree, tip_a).tolist()), set(chain_slots(tree, tip_b).tolist())
    assert not (sa & sb & set(range(500, end)))                    # no block of the span in both
    m = measure(cfg)
    assert m["density_a"] <= m["made_a"] and m["density_b"] <= m["made_b"]
    assert m["fork"] == np.unique(tree.slot[mask[tree.leader.clip(min=0)] & (tree.slot >= 500) & (tree.slot < end)]).size
    assert 0.35 <= m["share_a"] < 0.40 and m["share_a"] + m["share_b"] + m["alpha"] == pytest.approx(1.0)


def test_without_a_partition_the_tree_is_the_withholding_one():
    cfg = SimConfig(**BASE, adversary_frac=0.3, replicate=1)
    tree, arrival, stake, mask, side, public = _tree(cfg)
    tree2, arrival2, mask2, public2, canonical = withhold_tree(cfg)
    assert side is None and np.array_equal(tree.slot, tree2.slot) and np.array_equal(tree.parent, tree2.parent)
    assert np.array_equal(arrival, arrival2) and np.array_equal(public, public2)
    with pytest.raises(ValueError):
        partition_tree(cfg)
    honest = SimConfig(**BASE, adversary_frac=0.0, replicate=1, partition_share=0.5,
                       partition_start=500, partition_slots=1_000)
    m = measure(honest)
    assert m["fork"] == 0 and m["alpha"] == 0.0
