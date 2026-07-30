import numpy as np

from tsi_sim.blocktree import BlockTree
from tsi_sim.config import SimConfig
from tsi_sim.uncles import annotate_uncles


def make_tree(slots, parents, heights, leaders):
    n = len(slots)
    return BlockTree(
        slot=np.array(slots, np.int64),
        parent=np.array(parents, np.int64),
        height=np.array(heights, np.int64),
        leader=np.array(leaders, np.int64),
        uncles=[() for _ in range(n)],
    )


def _canonical_and_orphan_tree():
    # genesis(0); canonical chain 1(slot0)->3(slot3)->4(slot5); orphan 2(slot1)
    tree = make_tree(
        slots=[-1, 0, 1, 3, 5],
        parents=[-1, 0, 0, 1, 3],
        heights=[0, 1, 1, 2, 3],
        leaders=[-1, 0, 1, 2, 3],
    )
    canonical = [4, 3, 1]  # tip-first
    return tree, canonical


def test_oldest_selection_and_window():
    tree, canonical = _canonical_and_orphan_tree()
    cfg = SimConfig(max_uncles=1, uncle_window=300, uncle_strategy="oldest")
    annotate_uncles(tree, canonical, cfg, np.random.default_rng(0))
    # orphan 2 (slot1) is within window of block 3 (slot3) -> referenced there
    referenced = {u for b in canonical for u in tree.uncles[b]}
    assert referenced == {2}


def test_no_uncles_when_u_zero():
    tree, canonical = _canonical_and_orphan_tree()
    cfg = SimConfig(max_uncles=0)
    annotate_uncles(tree, canonical, cfg, np.random.default_rng(0))
    assert all(tree.uncles[b] == () for b in canonical)


def test_window_excludes_out_of_range_orphan():
    tree, canonical = _canonical_and_orphan_tree()
    cfg = SimConfig(max_uncles=1, uncle_window=1, uncle_strategy="oldest")
    annotate_uncles(tree, canonical, cfg, np.random.default_rng(0))
    # orphan 2 at slot1; nearest canonical after it is block3 at slot3 -> gap 2 > W=1
    referenced = {u for b in canonical for u in tree.uncles[b]}
    assert referenced == set()


def test_dedup_across_ancestors():
    # Two canonical blocks both within window of the single orphan: only one references it.
    tree = make_tree(
        slots=[-1, 0, 1, 2, 3],
        parents=[-1, 0, 0, 1, 3],
        heights=[0, 1, 1, 2, 3],
        leaders=[-1, 0, 9, 2, 3],
    )
    canonical = [4, 3, 1]
    cfg = SimConfig(max_uncles=4, uncle_window=300, uncle_strategy="oldest")
    annotate_uncles(tree, canonical, cfg, np.random.default_rng(0))
    counts = sum(len(tree.uncles[b]) for b in canonical)
    assert counts == 1  # orphan 2 referenced exactly once despite two eligible blocks
