"""Countable-model counting: measurement kernels vs the tsi.py reference oracle.

Hand-built tree exercising every counting rule on baked references:
canonical 1(s0) -> 2(s2) -> 3(s5) -> 4(s10, tip); orphans 5(s1, parent 1, first fork),
6(s6, parent 5, DEEP), 7(s7, parent 1, first fork), 8(s7, parent 2, first fork, same slot
as 7). References: block2 -> (5,), block3 -> (1,) [a canonical block], block4 -> (6, 7, 8).

With w = 5 and T = 20 the countable verdicts are: 5 counted (d=1); 1 skipped (on chain);
6 deep-rejected (parent is an orphan); 7 counted (d=3); 8 counted by id but its slot is
already recovered by 7 (slot dedup). Old model counts every reference.
"""

from __future__ import annotations

import numpy as np
import pytest

from tsi_sim.blocktree import BlockTree
from tsi_sim.measure import measure
from tsi_sim.tsi import countable_refs, density_m

W = 5
T = 20


def _tree() -> BlockTree:
    tree = BlockTree(
        slot=np.array([-1, 0, 2, 5, 10, 1, 6, 7, 7], np.int64),
        parent=np.array([-1, 0, 1, 2, 3, 1, 5, 1, 2], np.int64),
        height=np.array([0, 1, 2, 3, 4, 2, 3, 2, 3], np.int64),
        leader=np.array([-1, 0, 1, 2, 3, 4, 5, 6, 7], np.int64),
        uncles=[() for _ in range(9)],
    )
    tree.uncles[2] = (5,)
    tree.uncles[3] = (1,)
    tree.uncles[4] = (6, 7, 8)
    return tree


CANONICAL = [4, 3, 2, 1]
ACTIVE = np.array([0, 1, 2, 5, 6, 7, 10], np.int64)   # 7 distinct active slots in T


def test_countable_refs_oracle():
    assert countable_refs(_tree(), CANONICAL, W) == {5, 7, 8}


def test_density_m_countable_and_old():
    tree = _tree()
    # countable: honest slots {0,2,5,10} + recovered slots {1, 7} -> 6
    assert density_m(tree, CANONICAL, T, countable=True, w=W) == 6
    # old model: every reference counts -> recovered slots {1, 6, 7} -> 7
    assert density_m(tree, CANONICAL, T) == 7


@pytest.mark.parametrize("use_numba", [False, True])
def test_measure_countable_matches_oracle(use_numba):
    tree = _tree()
    A = np.zeros((2, tree.n_blocks))               # both nodes received everything
    ms = measure(tree, A, ACTIVE, T, cutoff=15, use_numba=use_numba,
                 countable=True, w=W)
    np.testing.assert_array_equal(ms.m, [6, 6])            # = density_m countable
    np.testing.assert_allclose(ms.q, 4 / 7)                # canonical slots / active
    np.testing.assert_allclose(ms.q_eff, 6 / 7)            # + recovered slots
    np.testing.assert_array_equal(ms.ref_total, [5, 5])    # ids 5,1,6,7,8 examined
    np.testing.assert_array_equal(ms.ref_deep, [1, 1])     # id 6 rejected as deep


@pytest.mark.parametrize("use_numba", [False, True])
def test_measure_old_counts_all_refs(use_numba):
    tree = _tree()
    A = np.zeros((2, tree.n_blocks))
    ms = measure(tree, A, ACTIVE, T, cutoff=15, use_numba=use_numba)
    np.testing.assert_array_equal(ms.m, [7, 7])            # = density_m old
    np.testing.assert_allclose(ms.q_eff, 7 / 7)
    np.testing.assert_array_equal(ms.ref_deep, [0, 0])     # no rule to reject on


def test_window_recheck_rejects_stale_reference():
    # A baked reference outside the counting window is uncounted under countable
    # (the old model still counts it): shrink w below block4 -> uncle 7 distance (d=3).
    tree = _tree()
    assert countable_refs(tree, CANONICAL, 2) == {5}       # 7, 8 now out of window (d=3)
    assert density_m(tree, CANONICAL, T, countable=True, w=2) == 5


def test_deep_ref_share_is_zero_end_to_end():
    """The counting-side parent-on-chain re-check must never fire on a real countable run.

    Countable SELECTION already refuses to reference a non-first-fork block, and for a
    block ``b`` on the counting chain the producer's chain below ``b`` IS the counting
    chain below ``b`` (they are the same ancestor path). So ``ref_deep`` is a defensive
    invariant, not a measured rate: any non-zero value means selection and counting have
    drifted apart. The hand-built trees above are the only way to make it fire — they bake
    references selection would never emit.
    """
    import pandas as pd

    from tsi_sim.config import SimConfig
    from tsi_sim.engine import run_trajectory

    # Small but fork-rich: Blend delay spreads proposals over many slots.
    cfg = SimConfig(n_nodes=60, topology="blend", blend_hops=2, blend_delay_max=8.0,
                    degree=4, max_uncles=2, k=32, epochs=3, f=0.1,
                    stake_dist="pareto", init_dest="common")
    df = pd.DataFrame(run_trajectory(cfg))
    assert df.n_blocks.sum() > 0                      # the run actually produced blocks
    assert (df.deep_ref_share == 0.0).all(), (
        f"counting rejected references selection emitted: {df.deep_ref_share.tolist()}")
