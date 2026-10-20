"""Gates for the forks a client counts beside a target (src/finality_sim/forks.py)."""

from types import SimpleNamespace

import numpy as np

from finality_sim.forks import fork_counts, fork_points
from finality_sim.race import fallback_share


def _tree():
    # 0 genesis; canonical 1-2-3-4; X=5 forks at 1 after 2's slot, Y=6 extends X, Z=7 is 4's
    # sibling, W=8 is 1's sibling at 1's own slot, X'=9 is a second block at X's slot (one win
    # signed twice), V=10 extends W at Z's slot, U=11 is 4's sibling at Y's slot
    slot = np.array([-1, 5, 12, 20, 31, 14, 25, 33, 5, 14, 33, 25])
    parent = np.array([-1, 0, 1, 2, 3, 1, 5, 3, 0, 1, 8, 3])
    height = np.array([0, 1, 2, 3, 4, 2, 3, 4, 1, 2, 2, 4])
    canonical = np.zeros(12, bool)
    canonical[[1, 2, 3, 4]] = True
    public = np.ones(12, bool)
    public[0] = False
    return SimpleNamespace(slot=slot, parent=parent, height=height), public, canonical


def test_fork_counts_on_a_hand_built_tree():
    tree, public, canonical = _tree()
    assert fork_points(tree.parent, canonical).tolist() == [0, 1, 2, 3, 4, 1, 1, 3, 0, 1, 0, 3]
    # target 1 counts the slots of W and V (after genesis, forking below 1), not X, X', Y, Z, U
    # (descendants); target 2 counts slot 14 (X and X' once), slot 25 (through Y, which forks
    # below 2, though U does not) and slot 33 (through V, though Z does not), not W (at its
    # parent's slot); 3 counts the same three; 4 counts slots 25 and 33, each once. A block count
    # would give 2, 4, 4, 4.
    assert fork_counts(tree, public, canonical).tolist() == [2, 3, 3, 2]
    public[[5, 6, 7, 8, 9, 10, 11]] = False
    assert fork_counts(tree, public, canonical).tolist() == [0, 0, 0, 0]


def test_the_fallback_share_reads_the_first_other_arrival():
    tree = SimpleNamespace(leader=np.array([-1, 0, 1, 2]), slot=np.array([-1, 10, 20, 30]))
    arrival = np.array([[0.0, 10.0, 20.5, 46.25],
                        [0.0, 10.5, 20.0, 46.5],
                        [0.0, 26.0, 36.0, 30.0]])          # block 3 reaches the others by the fallback
    public = np.array([False, True, True, True])
    assert fallback_share(tree, arrival, public, 15.0) == 1 / 3
    assert fallback_share(tree, arrival, public, 15.25) == 1 / 3         # 46.25 - 30 = 16.25, exactly
    assert fallback_share(tree, arrival, public, 15.5) == 0.0
