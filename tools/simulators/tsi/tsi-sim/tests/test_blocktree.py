import numpy as np

from tsi_sim.blocktree import build_tree
from tsi_sim.latency import FixedSlotLatency


def _winners(*groups):
    return [np.array(g, dtype=np.int64) for g in groups]


def test_latency_induces_fork_and_longest_chain():
    # L=2. slot0: node0; slot1: node1 (can't see block1 yet -> forks on genesis);
    # slot3: node2 (sees both, builds on the earlier-slot tip -> block1).
    active = np.array([0, 1, 3], dtype=np.int64)
    winners = _winners([0], [1], [2])
    tree = build_tree(active, winners, FixedSlotLatency(2), np.random.default_rng(0))

    assert tree.n_blocks == 4                      # genesis + 3
    assert tree.height.tolist() == [0, 1, 1, 2]
    # block 3 built on block 1 (earlier slot wins the height-1 tie)
    assert tree.parent[3] == 1
    assert tree.canonical_chain() == [3, 1]        # tip-first
    # block 2 is the orphan
    canon = set(tree.canonical_chain())
    orphans = [b for b in range(1, tree.n_blocks) if b not in canon]
    assert orphans == [2]


def test_same_slot_multiwinner_forks_even_at_zero_latency():
    active = np.array([0, 1], dtype=np.int64)
    winners = _winners([0, 1], [2])   # two winners in slot 0 -> guaranteed fork
    tree = build_tree(active, winners, FixedSlotLatency(0), np.random.default_rng(0))
    # blocks 1 and 2 are siblings at height 1 on genesis
    assert tree.parent[1] == 0 and tree.parent[2] == 0
    assert tree.height[1] == 1 and tree.height[2] == 1
    # block 3 at slot 1 extends one of them (height 2)
    assert tree.height[3] == 2
    assert len(tree.canonical_chain()) == 2


def test_self_extension_within_latency():
    # A single node winning consecutive slots builds on its own block despite latency.
    active = np.array([0, 1], dtype=np.int64)
    winners = _winners([5], [5])
    tree = build_tree(active, winners, FixedSlotLatency(10), np.random.default_rng(0))
    assert tree.parent[2] == 1          # node 5 self-extends
    assert tree.height.tolist() == [0, 1, 2]


def test_ancestors():
    active = np.array([0, 1, 2], dtype=np.int64)
    winners = _winners([0], [0], [0])   # one node, clean chain
    tree = build_tree(active, winners, FixedSlotLatency(0), np.random.default_rng(0))
    assert tree.ancestors(3) == [3, 2, 1]
