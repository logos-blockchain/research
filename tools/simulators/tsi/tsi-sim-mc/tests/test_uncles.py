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


def _wide_orphan_tree():
    # canonical 1(0)->6(6); orphans 2,3,4,5 at slots 1,2,3,4 (all within window of block6)
    tree = make_tree(
        slots=[-1, 0, 1, 2, 3, 4, 6],
        parents=[-1, 0, 0, 0, 0, 0, 1],
        heights=[0, 1, 1, 1, 1, 1, 2],
        leaders=[-1, 0, 1, 2, 3, 4, 0],
    )
    return tree, [6, 1]  # tip-first


def test_random_strategy_deterministic_and_capped():
    import numpy as np
    tree_a, canon = _wide_orphan_tree()
    tree_b, _ = _wide_orphan_tree()
    cfg = SimConfig(max_uncles=2, uncle_window=300, uncle_strategy="random", uncle_random_p=0.5)
    annotate_uncles(tree_a, canon, cfg, np.random.default_rng(7))
    annotate_uncles(tree_b, canon, cfg, np.random.default_rng(7))
    assert tree_a.uncles == tree_b.uncles                 # same seed -> identical
    total = sum(len(tree_a.uncles[b]) for b in canon)
    assert total <= cfg.max_uncles                        # capped


def test_random_p_one_matches_oldest():
    import numpy as np
    tree_r, canon = _wide_orphan_tree()
    tree_o, _ = _wide_orphan_tree()
    annotate_uncles(tree_r, canon, SimConfig(max_uncles=2, uncle_strategy="random",
                                             uncle_random_p=1.0), np.random.default_rng(1))
    annotate_uncles(tree_o, canon, SimConfig(max_uncles=2, uncle_strategy="oldest"),
                    np.random.default_rng(1))
    assert tree_r.uncles == tree_o.uncles     # p=1 deterministically takes oldest-first


def test_random_p_zero_selects_nothing():
    import numpy as np
    tree, canon = _wide_orphan_tree()
    annotate_uncles(tree, canon, SimConfig(max_uncles=4, uncle_strategy="random",
                                           uncle_random_p=0.0), np.random.default_rng(1))
    assert all(tree.uncles[b] == () for b in canon)


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
