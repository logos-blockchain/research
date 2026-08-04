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
    # OLD model: uncle_window is read directly. (The countable model ignores uncle_window
    # and derives the window from window_absorption — see the countable twin below.)
    tree, canonical = _canonical_and_orphan_tree()
    cfg = SimConfig(max_uncles=1, uncle_window=1, uncle_strategy="oldest", uncle_model="old")
    annotate_uncles(tree, canonical, cfg, np.random.default_rng(0))
    # orphan 2 at slot1; nearest canonical after it is block3 at slot3 -> gap 2 > W=1
    referenced = {u for b in canonical for u in tree.uncles[b]}
    assert referenced == set()


def test_countable_window_is_derived_from_absorption():
    # countable: w_u = round(W / f). With f=0.5 and W=1, w_u = 2 slots: the orphan at slot1
    # is out of range of the canonical block at slot5 (gap 4) and of slot3 (gap 2 <= 2 OK).
    tree, canonical = _canonical_and_orphan_tree()
    cfg = SimConfig(max_uncles=1, f=0.5, window_absorption=1.0)
    assert cfg.effective_uncle_window == 2
    annotate_uncles(tree, canonical, cfg, np.random.default_rng(0))
    referenced = {u for b in canonical for u in tree.uncles[b]}
    assert referenced == {2}                       # block3 (slot3) still reaches it
    # shrink f so the derived window rounds to 1 slot: gap 2 > 1 -> excluded
    tree2, canonical2 = _canonical_and_orphan_tree()
    cfg2 = SimConfig(max_uncles=1, f=0.9, window_absorption=1.0)
    assert cfg2.effective_uncle_window == 1
    annotate_uncles(tree2, canonical2, cfg2, np.random.default_rng(0))
    assert {u for b in canonical2 for u in tree2.uncles[b]} == set()


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


# --- countable model (spec counting rules) ---------------------------------------------


def _deep_fork_tree():
    # canonical 1(slot0)->5(slot5); orphan branch 2(slot1,parent=1)->3(slot2,parent=2);
    # orphan 4(slot3, parent=1). Blocks 2,4 are FIRST fork blocks; 3 is deep.
    tree = make_tree(
        slots=[-1, 0, 1, 2, 3, 5],
        parents=[-1, 0, 1, 2, 1, 1],
        heights=[0, 1, 2, 3, 2, 2],
        leaders=[-1, 0, 1, 2, 3, 4],
    )
    return tree, [5, 1]  # tip-first


def test_countable_excludes_deep_fork_blocks():
    tree, canonical = _deep_fork_tree()
    cfg = SimConfig(max_uncles=4)
    annotate_uncles(tree, canonical, cfg, np.random.default_rng(0))
    referenced = {u for b in canonical for u in tree.uncles[b]}
    assert referenced == {2, 4}                    # deep block 3 (parent is an orphan) excluded


def test_old_model_still_references_deep_fork_blocks():
    tree, canonical = _deep_fork_tree()
    cfg = SimConfig(max_uncles=4, uncle_model="old", uncle_window=300)
    annotate_uncles(tree, canonical, cfg, np.random.default_rng(0))
    referenced = {u for b in canonical for u in tree.uncles[b]}
    assert referenced == {2, 3, 4}                 # --old: fork depth ignored


def test_countable_excludes_occupied_slots_and_dedups_per_slot():
    # canonical 1(slot0)->5(slot4); orphans: 2 at slot0 (canonical-occupied), 3/4 at slot2.
    tree = make_tree(
        slots=[-1, 0, 0, 2, 2, 4],
        parents=[-1, 0, 0, 1, 1, 1],
        heights=[0, 1, 1, 2, 2, 2],
        leaders=[-1, 0, 1, 2, 3, 4],
    )
    canonical = [5, 1]
    cfg = SimConfig(max_uncles=4)
    annotate_uncles(tree, canonical, cfg, np.random.default_rng(0))
    referenced = {u for b in canonical for u in tree.uncles[b]}
    # slot0 is canonical-occupied -> orphan 2 excluded; slot2 pair -> exactly one picked
    assert referenced == {3}


def test_production_selection_countable_rules():
    from tsi_sim.uncles import select_uncles_at_production

    # 0 genesis; 1 canonical slot0; 2 first-fork slot1 (parent 1); 3 deep slot2 (parent 2);
    # 4/5 same-slot first-forks at slot3 (parent 1).
    slot = np.array([-1, 0, 1, 2, 3, 3], np.int64)
    parent = np.array([-1, 0, 1, 2, 1, 1], np.int64)
    uncles: list = [() for _ in range(6)]
    arrival = np.zeros(6)                          # everything arrived immediately
    cfg = SimConfig(max_uncles=4)
    sel = select_uncles_at_production(
        slot, parent, uncles, arrival, nb=6, parent_id=1, t=5, config=cfg,
        rng=np.random.default_rng(0))
    assert sel == (2, 4)                           # deep 3 excluded; one per slot at slot3

    old = SimConfig(max_uncles=4, uncle_model="old", uncle_window=300)
    sel_old = select_uncles_at_production(
        slot, parent, uncles, arrival, nb=6, parent_id=1, t=5, config=old,
        rng=np.random.default_rng(0))
    assert sel_old == (2, 3, 4, 5)                 # --old: depth and slot-dedup ignored
