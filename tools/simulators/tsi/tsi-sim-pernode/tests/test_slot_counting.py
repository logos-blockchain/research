"""Corrected slot-based density counting: one count per slot, never more."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tsi_sim.blocktree import BlockTree
from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.theory import block_count_ceiling
from tsi_sim.tsi import density_m


def make_tree(slots, parents, heights, uncles):
    n = len(slots)
    return BlockTree(
        slot=np.array(slots, np.int64),
        parent=np.array(parents, np.int64),
        height=np.array(heights, np.int64),
        leader=np.zeros(n, np.int64),
        uncles=uncles,
    )


def test_same_slot_co_winner_uncle_not_counted():
    """An uncle sharing a canonical block's slot must not add a count (slot already won)."""
    # canonical 1(slot0), 3(slot2); orphan 2 ALSO at slot0 (co-winner), referenced by 3.
    tree = make_tree(
        slots=[-1, 0, 0, 2],
        parents=[-1, 0, 0, 1],
        heights=[0, 1, 1, 2],
        uncles=[(), (), (), (2,)],
    )
    canonical = [3, 1]
    assert density_m(tree, canonical, T=10) == 2            # slots {0, 2} — uncle adds nothing
    assert density_m(tree, canonical, T=10, legacy_block_count=True) == 3   # the old bug


def test_multiple_uncles_same_slot_count_once():
    """Two referenced orphans in the same (non-canonical) slot count as one recovered slot."""
    # canonical 1(slot0), 4(slot3); orphans 2 and 3 BOTH at slot1, both referenced.
    tree = make_tree(
        slots=[-1, 0, 1, 1, 3],
        parents=[-1, 0, 0, 0, 1],
        heights=[0, 1, 1, 1, 2],
        uncles=[(), (), (), (), (2, 3)],
    )
    canonical = [4, 1]
    assert density_m(tree, canonical, T=10) == 3            # slots {0, 1, 3}
    assert density_m(tree, canonical, T=10, legacy_block_count=True) == 4   # the old bug


def test_distinct_slot_uncles_still_counted():
    """The fix must not lose genuinely distinct recovered slots."""
    tree = make_tree(
        slots=[-1, 0, 1, 2, 3],
        parents=[-1, 0, 0, 0, 1],
        heights=[0, 1, 1, 1, 2],
        uncles=[(), (), (), (), (2, 3)],
    )
    canonical = [4, 1]
    assert density_m(tree, canonical, T=10) == 4            # slots {0, 1, 2, 3}


def test_zero_delay_equilibrium_is_one_not_ceiling():
    """The c(f) ceiling was the bug: corrected counting equilibrates at 1.0 with uncles."""
    base = dict(n_nodes=300, stake_dist="uniform", topology="full_mesh", latency=0,
                max_uncles=2, uncle_window=300, k=64, epochs=24, genesis_d_factor=1.0)
    tails = []
    for rep in range(3):
        df = pd.DataFrame(run_trajectory(SimConfig(**base, replicate=rep)))
        tails.append(df[df.epoch >= 8].mean_ratio.mean())
    assert abs(np.mean(tails) - 1.0) < 0.015


def test_legacy_flag_reproduces_the_ceiling():
    base = dict(n_nodes=300, stake_dist="uniform", topology="full_mesh", latency=0,
                max_uncles=2, uncle_window=300, k=64, epochs=24, genesis_d_factor=1.0)
    tails = []
    for rep in range(3):
        df = pd.DataFrame(run_trajectory(
            SimConfig(**base, legacy_block_count=True, replicate=rep)))
        tails.append(df[df.epoch >= 8].mean_ratio.mean())
    c = block_count_ceiling(SimConfig().f)
    assert abs(np.mean(tails) - c) < 0.015
