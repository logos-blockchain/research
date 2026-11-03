"""Gates for Phase L's gadget on block trees (src/finality_sim/gadget.py)."""

import math

import numpy as np
import pytest

from finality_sim.gadget import block_final_times, run_gadget


class Tree:
    """A block tree from parent ids and slots; block 0 is genesis at slot -1."""

    def __init__(self, parent, slot):
        self.parent = np.asarray(parent, dtype=np.int64)
        self.slot = np.asarray(slot, dtype=np.int64)
        h = np.zeros(self.parent.size, dtype=np.int64)
        for b in range(1, self.parent.size):
            h[b] = h[self.parent[b]] + 1
        self.height = h

    @property
    def n_blocks(self):
        return self.slot.size

    def canonical_chain(self):
        best = max(range(self.n_blocks), key=lambda b: (self.height[b], -self.slot[b], -b))
        out = []
        while best > 0:
            out.append(best)
            best = int(self.parent[best])
        return out


def chain(slots: int) -> Tree:
    """A block in every slot from 0 to ``slots - 1``: block ``s + 1`` at slot ``s``."""
    return Tree([-1] + list(range(slots)), [-1] + list(range(slots)))


def test_an_agreed_chain_is_final_at_l_plus_three_halves_r():
    """Every node holds every block at its slot and every vote at once. Block b at slot s is
    first held by round r = ⌈(s + L)/R⌉, at least 1, and final at the next round's start, so the
    mean over whole cycles of R slots is L + (R − 1)/2 + R."""
    R, L, T, n = 30, 30, 1200, 9
    tree = chain(T)
    arrival = np.tile(tree.slot.astype(float), (n, 1))
    delay = np.zeros((n, n))
    run = run_gadget(tree, arrival, delay, np.arange(n), range(R, T, R), L, n)
    assert run.justified_rounds == len(run.rounds) and run.restricted == 0
    blocks = np.arange(1, T - 3 * R - L)
    out = block_final_times(tree, run, blocks)
    s = tree.slot[blocks]
    expect = R * (np.maximum(np.ceil((s + L) / R), 1) + 1)
    assert np.all(out == expect[:, None])
    whole = (s >= R) & (s < R + 10 * R)
    assert (expect[whole] - s[whole]).mean() == pytest.approx(L + (R - 1) / 2 + R)


def test_justification_needs_one_source():
    """Votes on one target from two sources are two links. Five nodes still hold round 1 unjustified
    at round 2 (its votes reach them late), so round 2 splits five to four and nothing is
    justified, though all nine vote the same block."""
    R, L, T, n = 30, 0, 300, 9
    tree = chain(T)
    arrival = np.tile(tree.slot.astype(float), (n, 1))
    delay = np.zeros((n, n))
    delay[:, :5] = 100.0
    np.fill_diagonal(delay, 0.0)
    run = run_gadget(tree, arrival, delay, np.arange(n), [R, 2 * R], L, n)
    assert run.per_round == [1, 0]
    assert run.checkpoints[1].final is None


def test_finalization_needs_the_next_rounds_link():
    """Round 2 splits on its target, so round 3's link from round 1 skips a round: it justifies
    round 3 but finalizes nothing. Round 4's link from round 3 finalizes round 3."""
    R, L, T, n = 30, 0, 300, 9
    tree = chain(T)
    arrival = np.tile(tree.slot.astype(float), (n, 1))
    late = tree.slot >= 2 * R - 1                      # blocks from slot 59 reach nodes 0-4 late
    arrival[:5, late] = np.maximum(tree.slot[late], 2 * R + 5)
    delay = np.zeros((n, n))
    run = run_gadget(tree, arrival, delay, np.arange(n), [R, 2 * R, 3 * R, 4 * R], L, n)
    assert run.per_round == [1, 0, 1, 1]
    c1, c3 = run.checkpoints[1], run.checkpoints[2]
    assert (c1.round, c3.round, c3.source) == (1, 3, 1)
    assert c1.final is None and c3.final is not None
    out = block_final_times(tree, run, np.array([int(c1.block)]))
    assert np.all(out == 4 * R)                        # held by round 3, final at round 4


def test_votes_follow_the_chain_of_the_justified_checkpoint():
    """Chain A has a block in every slot from 0 to 60, chain B forks at genesis and has one in
    every slot from 50 to 200. Round 1 justifies A's block at slot 30. At round 2, slot 120, B is
    the longer chain, but every node votes on the best chain that holds the justified checkpoint,
    A's, as Casper FFG's fork choice has it."""
    parent, slot = [-1], [-1]
    for s in range(61):
        parent.append(0 if s == 0 else len(parent) - 1)
        slot.append(s)
    a_tip = len(parent) - 1
    for s in range(50, 201):
        parent.append(0 if s == 50 else len(parent) - 1)
        slot.append(s)
    tree = Tree(parent, slot)
    n = 9
    arrival = np.tile(tree.slot.astype(float), (n, 1))
    run = run_gadget(tree, arrival, np.zeros((n, n)), np.arange(n), [30, 120], 0, n)
    assert run.per_round == [1, 1] and run.restricted == n
    assert tree.slot[run.checkpoints[1].block] == 30 and run.checkpoints[2].block == a_tip
    assert run.checkpoints[1].final is not None
    # both justified blocks lie on A, which the longest chain, B, leaves: departures from round 1
    assert run.off_chain == 2 and run.first_off == 1


def test_a_target_never_falls_below_its_source():
    """A source younger than the lag: the vote targets the source's block itself."""
    from finality_sim.gadget import vote_target
    tree = chain(200)
    root, tip = 96, 101                                # blocks at slots 95 and 100
    assert vote_target(tree, tip, root, 100.0, 30) == root
    assert vote_target(tree, tip, 41, 100.0, 30) == 71  # an older source: the block at slot 70


def test_the_best_descendant_is_the_brute_forces():
    """On random trees, the best held block among a root and its descendants is the one a scan of
    every held block finds, ranked by height, then earlier slot, then lower id."""
    from finality_sim.gadget import best_descendant, descends
    rng = np.random.default_rng(7)
    for _ in range(200):
        n = int(rng.integers(5, 60))
        parent = [-1] + [int(rng.integers(0, b)) for b in range(1, n)]
        slot = [-1]
        for b in range(1, n):
            slot.append(slot[parent[b]] + 1 + int(rng.integers(0, 4)))
        tree = Tree(parent, slot)
        row = rng.uniform(0, 100, n)
        t = float(rng.uniform(0, 100))
        root = int(rng.integers(0, n))
        best, key = root, (tree.height[root], -tree.slot[root], -root)
        for b in range(n):
            k = (tree.height[b], -tree.slot[b], -b)
            if row[b] <= t and k > key and descends(tree, b, root):
                best, key = b, k
        assert best_descendant(tree, row, t, root) == best


def two_sides(n_a: int, n_b: int, slots: int) -> tuple[Tree, np.ndarray]:
    """Two chains forked at genesis: side A's nodes hold only chain A, side B's only chain B."""
    parent, slot = [-1], [-1]
    for s in range(slots):
        parent.append(0 if s == 0 else len(parent) - 2)
        slot.append(s)
        parent.append(0 if s == 0 else len(parent) - 2)
        slot.append(s)
    tree = Tree(parent, slot)
    n = n_a + n_b
    arrival = np.full((n, tree.n_blocks), np.inf)
    a_blocks = np.arange(1, tree.n_blocks, 2)
    b_blocks = np.arange(2, tree.n_blocks, 2)
    arrival[:n_a][:, a_blocks] = tree.slot[a_blocks]
    arrival[n_a:][:, b_blocks] = tree.slot[b_blocks]
    arrival[:, 0] = -1
    return tree, arrival


@pytest.mark.parametrize("n_a, n_b, coalition, both, one",
                         [(5, 5, 4, False, False), (5, 5, 5, True, True), (5, 5, 7, True, True),
                          (7, 3, 4, False, True)])
def test_two_sides_finalize_only_from_a_third(n_a, n_b, coalition, both, one):
    """Honest declarations on two sides of a cut no vote crosses; the coalition signs on both.
    Five and five with four of its declarations: the quorum is 10 of 14 and neither side reaches
    it. With five it is 10 of 15, a third of the weight the coalition's, and both sides finalize.
    Seven and three with four: the larger side finalizes alone, and nothing conflicts."""
    tree, arrival = two_sides(n_a, n_b, 300)
    side = np.array([0] * n_a + [1] * n_b)
    delay = np.where(side[:, None] == side[None, :], 0.0, np.inf)
    total = n_a + n_b + coalition
    run = run_gadget(tree, arrival, delay, np.arange(n_a + n_b), range(30, 300, 30), 0, total,
                     coalition=coalition)
    assert (run.finalized_conflicts > 0) == both
    assert (run.conflicts > 0) == both
    assert (run.finalized_rounds > 0) == one
    assert math.ceil(2 / 3 * total - 1e-9) <= n_a + coalition or run.justified_rounds == 0


def test_a_cut_holds_votes_and_two_links_finalize_at_the_earlier():
    """A common block at slot 30, then two branches, a cut from the start that votes cross at slot
    1,000, and a coalition of a third. Round 1 justifies the common block; round 2 justifies a link
    from it on each side, so both finalize it, and each side holds it final when its own link
    reaches it, at slot 60. A side holds the other side's checkpoint only once the cut lets the
    votes over, at 1,000."""
    n_a = n_b = 5
    parent, slot = [-1], [-1]
    for s in range(41):                                   # the common prefix, slots 0 to 40
        parent.append(len(parent) - 1)
        slot.append(s)
    fork = len(parent) - 1
    for s in range(41, 200):                              # the two branches
        parent.append(fork if s == 41 else len(parent) - 2)
        slot.append(s)
        parent.append(fork if s == 41 else len(parent) - 2)
        slot.append(s)
    tree = Tree(parent, slot)
    n = n_a + n_b
    arrival = np.full((n, tree.n_blocks), np.inf)
    common = np.arange(0, fork + 1)
    a_blocks = np.arange(fork + 1, tree.n_blocks, 2)
    b_blocks = np.arange(fork + 2, tree.n_blocks, 2)
    arrival[:, common] = tree.slot[common]
    arrival[:n_a][:, a_blocks] = tree.slot[a_blocks]
    arrival[n_a:][:, b_blocks] = tree.slot[b_blocks]
    side = np.array([0] * n_a + [1] * n_b)
    across = side[:, None] != side[None, :]
    delay = np.zeros((n, n))

    def cut(t):
        return np.where(across, 1000.0, np.inf) if t < 1000 else None

    run = run_gadget(tree, arrival, delay, np.arange(n), [30, 60], 0, n + 5, coalition=5, cut=cut)
    c1 = run.checkpoints[1]
    assert tree.slot[c1.block] == 30 and run.per_round == [1, 2]
    assert np.all(c1.final == 60)
    a2, b2 = run.checkpoints[2], run.checkpoints[3]
    if side[np.nonzero(arrival[:, a2.block] < np.inf)[0][0]] == 1:
        a2, b2 = b2, a2
    assert np.all(a2.held[:n_a] == 60) and np.all(a2.held[n_a:] == 1000)
    assert np.all(b2.held[n_a:] == 60) and np.all(b2.held[:n_a] == 1000)
