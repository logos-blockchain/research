import numpy as np

from tsi_sim.blocktree import BlockTree
from tsi_sim.tsi import density_m, referenced_uncle_ids, slot_stats, update_D


def make_tree(slots, parents, heights, uncles):
    n = len(slots)
    return BlockTree(
        slot=np.array(slots, np.int64),
        parent=np.array(parents, np.int64),
        height=np.array(heights, np.int64),
        leader=np.zeros(n, np.int64),
        uncles=uncles,
    )


def test_density_counts_honest_plus_deduped_uncles_in_window():
    # canonical 1(slot0),4(slot3); orphans 2(slot1),3(slot2). block4 refs uncles 2 and 3.
    tree = make_tree(
        slots=[-1, 0, 1, 2, 3],
        parents=[-1, 0, 0, 0, 1],
        heights=[0, 1, 1, 1, 2],
        uncles=[(), (), (), (), (2, 3)],
    )
    canonical = [4, 1]  # tip-first
    # window T=10 includes all slots
    assert density_m(tree, canonical, T=10) == 4      # 2 honest (slots 0,3) + 2 uncles (1,2)
    # window T=2 excludes slots 2,3 -> honest {slot0}=1, uncle slot1=1 (slot2 excluded)
    assert density_m(tree, canonical, T=2) == 2


def test_uncle_counted_by_own_slot_and_deduped():
    tree = make_tree(
        slots=[-1, 0, 5, 1],
        parents=[-1, 0, 1, 0],
        heights=[0, 1, 2, 1],
        uncles=[(), (), (3,), ()],   # block2 (slot5) references orphan 3 (slot1)
    )
    canonical = [2, 1]
    assert referenced_uncle_ids(tree, canonical) == {3}
    # uncle counted by its OWN slot (1), so window T=2 includes it
    assert density_m(tree, canonical, T=2) == 2       # honest slot0 + uncle slot1
    # window that excludes the uncle's own slot
    assert density_m(tree, canonical, T=1) == 1       # only honest slot0


def test_slot_stats_q_and_qeff():
    # active slots 0,1,2 in window; honest occupies 0,2; orphan at slot1 recovered by uncle
    tree = make_tree(
        slots=[-1, 0, 1, 2],
        parents=[-1, 0, 0, 1],
        heights=[0, 1, 1, 2],
        uncles=[(), (), (), (2,)],   # block3 refs orphan 2 (slot1)
    )
    canonical = [3, 1]
    active = np.array([0, 1, 2], np.int64)
    ref = referenced_uncle_ids(tree, canonical)
    ss = slot_stats(tree, canonical, ref, active, T=10)
    assert ss.n_active == 3
    assert ss.n_honest == 2            # slots 0 and 2
    assert ss.n_recovered == 1         # slot 1 recovered via uncle
    assert abs(ss.q - 2 / 3) < 1e-9
    assert abs(ss.q_eff - 1.0) < 1e-9


def test_update_D_fixed_point():
    f, T = 1 / 30, 3000
    m = int(round(T * f))              # measured density == f -> D unchanged
    assert abs(update_D(1000.0, m, T, f, beta=1.0) - 1000.0) < 1e-6
    # measured below f -> estimate drops
    assert update_D(1000.0, m - 20, T, f, 1.0) < 1000.0
    # clamp at 1
    assert update_D(1.0, 0, T, f, 1.0) == 1.0


def test_update_D_fixed_point_mode_targets_truncated_f():
    # In fixed-point mode the target rate is int(f*PRECISION)/PRECISION, slightly below f.
    from tsi_sim.tsi import PRECISION
    f, T = 1 / 30, 1_000_000
    f_p = int(f * PRECISION) / PRECISION
    m = 34000
    # For the same measured density, fixed-point (lower target f_p) raises the estimate
    # more than exact-f, i.e. it is systematically higher (now only ~1e-5 at PRECISION=1e6).
    assert (update_D(1000.0, m, T, f, 1.0, fixed_point=True)
            >= update_D(1000.0, m, T, f, 1.0, fixed_point=False))
    # A density of exactly f_p is the fixed-point fixed point (estimate unchanged).
    m_trunc = int(round(f_p * T))    # exact when f_p*T is integral (T=1e6)
    assert abs(update_D(1000.0, m_trunc, T, f, 1.0, fixed_point=True) - 1000.0) < 1e-6
