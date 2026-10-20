"""Gates for the partition on the engine (src/finality_sim/partition.py)."""

import hashlib

import numpy as np
import pytest
from tsi_sim.config import SimConfig

from finality_sim.partition import best_tip, chain_slots, measure
from finality_sim.race import _tree, partition_tree, withhold_timelines

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
    assert m["density_a"] <= m["occupied_a"] <= m["made_a"] and m["density_b"] <= m["occupied_b"] <= m["made_b"]
    assert m["fork"] == np.unique(tree.slot[mask[tree.leader.clip(min=0)] & (tree.slot >= 500) & (tree.slot < end)]).size
    assert 0.35 <= m["share_a"] < 0.40 and m["share_a"] + m["share_b"] + m["alpha"] == pytest.approx(1.0)


def test_a_side_counts_the_blocks_and_slots_its_leaders_made_in_the_span():
    # A brute-force count, block by block, at a block rate high enough that a side's leaders share
    # some slots, so that blocks made and slots occupied differ.
    for where in ("rest", "side"):
        cfg = SimConfig(**{**BASE, "k": 64, "f": 0.2}, adversary_frac=0.3, replicate=4, partition_share=0.35,
                        partition_start=100, partition_slots=3_000, partition_adversary_side=where)
        tree, arrival, stake, mask, side, public = partition_tree(cfg)
        m = measure(cfg)
        for name, nodes in (("a", side & ~mask), ("b", ~side & ~mask)):
            made, slots = 0, set()
            for b in range(1, tree.n_blocks):
                leader = int(tree.leader[b])
                if 100 <= tree.slot[b] < 3_100 and nodes[leader]:
                    made += 1
                    slots.add(int(tree.slot[b]))
            assert m[f"made_{name}"] == made and m[f"occupied_{name}"] == len(slots)
            assert made > len(slots)
            assert m[f"share_{name}"] == pytest.approx(stake[nodes].sum() / stake.sum())
        assert (side & mask).any() == (where == "side")             # the coalition sits where asked


# withhold_timelines at commit 4670c52, before the partition mode and the refactor into _tree:
# the canonical slots and the coalition's slots (SHA-1 of both as int64), their counts and the
# honest orphan share.
GOLDEN = [
    (dict(adversary_frac=0.3, replicate=1), 113, 57, 0.13076923076923075, "0205c0647fb54883"),
    (dict(adversary_frac=0.3, replicate=2, blend_adversary_relays=True, blend_adversary_action="drop",
          blend_copies=2), 86, 37, 0.16504854368932043, "d337aa3d73bfbb3a"),
    (dict(adversary_frac=0.25, replicate=3, blend_copies=2), 98, 39, 0.11711711711711714, "101317a6046e7b87"),
]


@pytest.mark.parametrize("cell,canonical,adversary,orphan,digest", GOLDEN)
def test_without_a_partition_the_tree_is_the_engines_before_the_partition_mode(
        cell, canonical, adversary, orphan, digest):
    canon, adv, got = withhold_timelines(SimConfig(**BASE, **cell))
    assert (canon.size, adv.size, got) == (canonical, adversary, orphan)
    assert hashlib.sha1(np.asarray(canon, np.int64).tobytes()
                        + np.asarray(adv, np.int64).tobytes()).hexdigest()[:16] == digest


def test_without_a_partition_there_is_no_side():
    cfg = SimConfig(**BASE, adversary_frac=0.3, replicate=1)
    assert _tree(cfg)[4] is None
    with pytest.raises(ValueError):
        partition_tree(cfg)
    honest = SimConfig(**BASE, adversary_frac=0.0, replicate=1, partition_share=0.5,
                       partition_start=500, partition_slots=1_000)
    m = measure(honest)
    assert m["fork"] == 0 and m["alpha"] == 0.0
