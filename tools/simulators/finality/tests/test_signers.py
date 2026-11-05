"""Gates for Phase M's closed forms (src/finality_sim/signers.py)."""

import math

import numpy as np
import pytest

from finality_sim import committee as cm
from finality_sim import signers as sg
from finality_sim.gadget import descends, run_gadget
from finality_sim.netcert import holds, live
from finality_sim.privacy import volunteer_share


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


def test_the_delegated_share_counts_the_operators_weight():
    """Holders choose one at a time: the coalition's holders delegate to the coalition's
    operators, each honest holder to an honest operator, to one of the coalition's, or not at
    all. The coalition's share of the delegated weight is the closed form at the honest shares
    the choices realize."""
    rng = np.random.default_rng(7)
    for _ in range(200):
        honest = rng.pareto(1.5, 300) + 0.01
        coalition = rng.pareto(1.5, 40) + 0.01
        choice = rng.choice(3, size=honest.size, p=rng.dirichlet([1.0, 1.0, 1.0]))
        alpha = coalition.sum() / (honest.sum() + coalition.sum())
        held = coalition.sum() + honest[choice == 2].sum()
        weight = coalition.sum() + honest[choice > 0].sum()
        v = honest[choice > 0].sum() / honest.sum()
        c = honest[choice == 2].sum() / honest.sum()
        assert sg.delegated_share(alpha, v, c) == pytest.approx(held / weight, rel=1e-12)


@pytest.mark.parametrize("alpha", [0.1, 0.2, 0.25, 0.3])
@pytest.mark.parametrize("uptime", [1.0, 0.95, 0.9])
def test_no_honest_stake_at_the_coalitions_operators_is_d1bs_frontier(alpha, uptime):
    """With none of the honest stake on the coalition's operators, the set holds exactly from D1b's
    share of the honest stake delegated: just above it some may be attracted, just below none."""
    v = volunteer_share(alpha, uptime)
    if math.isinf(v):
        assert sg.largest_attracted(alpha, uptime, 1.0) is None
        return
    assert sg.largest_attracted(alpha, uptime, min(1.0, v * (1 + 1e-6))) is not None
    assert sg.largest_attracted(alpha, uptime, v * (1 - 1e-6)) is None


@pytest.mark.parametrize("alpha", [0.1, 0.2, 0.25, 0.3])
@pytest.mark.parametrize("uptime", [1.0, 0.95, 0.9])
@pytest.mark.parametrize("q", [2 / 3, 0.6, 0.75])
def test_the_largest_attracted_share_is_the_edge(alpha, uptime, q):
    """With every note delegating, the set holds just below the largest attracted share and fails
    just above it. At ``q = 2/3`` safety and liveness meet at full uptime; below it safety binds
    first, above it liveness."""
    c = sg.largest_attracted(alpha, uptime, q=q)
    if c is None:
        assert not holds(sg.delegated_share(alpha, 1.0, 0.0), uptime, q)
        return
    assert holds(sg.delegated_share(alpha, 1.0, c * (1 - 1e-6)), uptime, q)
    assert not holds(sg.delegated_share(alpha, 1.0, c * (1 + 1e-6) + 1e-9), uptime, q)


@pytest.mark.parametrize("alpha", [0.05, 0.1])
@pytest.mark.parametrize("uptime", [1.0, 0.95])
@pytest.mark.parametrize("delegated", [0.5, 0.8])
def test_the_largest_attracted_share_with_part_delegated_is_a_scans(alpha, uptime, delegated):
    """With only part of the honest stake delegated, the largest attracted share is the largest
    the set holds at, found by a scan."""
    grid = np.linspace(0.0, delegated, 40001)
    held = [c for c in grid if holds(sg.delegated_share(alpha, delegated, float(c)), uptime)]
    c = sg.largest_attracted(alpha, uptime, delegated)
    if not held:
        assert c is None
        return
    assert c == pytest.approx(max(held), abs=2 * delegated / 40000)


@pytest.mark.parametrize("alpha", [0.1, 0.25, 0.3])
def test_every_leading_note_declared_weighs_the_stake_share(alpha):
    """With every note's weight in the set and none attracted, the coalition holds its stake
    share, and the set is live from the least uptime and not below it."""
    assert sg.delegated_share(alpha, 1.0, 0.0) == pytest.approx(alpha, rel=1e-12)
    u = sg.least_uptime(alpha)
    assert live(alpha, u) and not live(alpha, u * (1 - 1e-9))


def test_thirty_percent_needs_95_2_percent_online():
    assert sg.least_uptime(0.3) == pytest.approx(0.952381, abs=1e-6)
    assert math.isinf(sg.least_uptime(0.34))


def _binom_tail_ge(n, p, k):
    """P(Bin(n, p) ≥ k), summed exactly."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(max(k, 0), n + 1))


def _direct_known_committee(alpha, eps, uptime):
    """The fewest wins any quorum serves, by a direct scan over every n and every quorum."""
    for n in range(1, 2000):
        for quorum in range(n + 1):
            safe = _binom_tail_ge(n, alpha, 2 * quorum - n) <= eps
            short = 1 - _binom_tail_ge(n, (1 - alpha) * uptime, quorum)
            if safe and short <= eps:
                return n
    return None


@pytest.mark.parametrize("alpha, eps, uptime", [(0.1, 1e-3, 1.0), (0.1, 1e-4, 1.0),
                                                (0.2, 1e-3, 1.0), (0.1, 1e-3, 0.9)])
def test_the_known_committee_is_a_direct_counts(alpha, eps, uptime):
    """The smallest counted committee equals a direct scan over every size and quorum, with the
    binomial tails summed term by term. Its quorum is safe and live, and one vote fewer is not
    safe."""
    n, quorum = sg.known_committee(alpha, eps, uptime)
    assert n == _direct_known_committee(alpha, eps, uptime)
    assert _binom_tail_ge(n, alpha, 2 * quorum - n) <= eps
    assert 1 - _binom_tail_ge(n, (1 - alpha) * uptime, quorum) <= eps
    assert _binom_tail_ge(n, alpha, 2 * (quorum - 1) - n) > eps
    assert sg.leaders_window(n) == pytest.approx(n * 30)


def test_no_counted_committee_holds_a_third():
    assert sg.known_committee(1 / 3, 1e-9) is None
    assert sg.known_committee(0.3, 1e-9, 0.9) is None


def test_the_votes_take_the_drain_headroom():
    """Today a core connection carries the specification's 16 messages a round against a read
    limit of 20. Votes at each mode's rate fill exactly that headroom, which kept for the backlog
    is 40 of the 130 transaction messages Blend carries per 30 slots."""
    assert cm.blend_load(0.0)[0] == pytest.approx(16.0, rel=1e-12)
    assert cm.blend_load(sg.vote_rate("on top"))[0] == pytest.approx(cm.R_1, rel=1e-12)
    for n in (443, 5355, 33473):
        r = sg.shortest_round(n, "raised")
        x = cm.emission_multiplier(n, r, sg.F)
        assert cm.blend_load(0.0, x)[0] == pytest.approx(cm.R_1, rel=1e-12)
        assert sg.shortest_round(n, "on top") == pytest.approx(0.75 * n, rel=1e-12)
    assert sg.transaction_share(sg.headroom()) == pytest.approx(40 / 130, rel=1e-12)


@pytest.mark.parametrize("rounds", [1, 2])
@pytest.mark.parametrize("withheld", [0, 3])
def test_the_time_to_finality_is_the_gadgets(rounds, withheld):
    """On an agreed chain, with the honest votes of a round leaving evenly over it and the
    coalition's withheld, a block is held justified once the quorum's last vote arrives, after the
    first round whose target holds it, and final one round later. Over whole cycles of ``R``
    slots the mean time from its slot, and the longest, are the closed forms, for one round and
    for two, with a lag and a round that differ."""
    R, L, T, n = 90, 30, 3600, 12
    honest = n - withheld
    tree = chain(T)
    arrival = np.tile(tree.slot.astype(float), (n, 1))
    delay = np.repeat(((np.arange(n) + 1) * R / honest)[:, None], n, axis=1)
    run = run_gadget(tree, arrival, delay, np.arange(honest), range(R, T, R), L, n)
    need = math.ceil(2 * n / 3)
    blocks = np.arange(1, T - 3 * R - L)
    times = []
    for b in blocks.tolist():
        c = next(c for c in run.checkpoints[1:] if descends(tree, c.block, b))
        t = c.held if rounds == 1 else c.final
        times.append(float(t.max()) - float(tree.slot[b]))
    s = tree.slot[blocks]
    whole = (s >= R) & (s < R + 10 * R)
    emit = sg.emission_time(need, honest, R)
    assert np.mean(np.asarray(times)[whole]) == pytest.approx(sg.finality_time(L, R, rounds, emit))
    assert np.max(np.asarray(times)[whole]) == pytest.approx(sg.latest_time(L, R, rounds, emit))


def test_the_vote_budget_fills_spare_cover_then_the_headroom():
    """With equal stakes every vote first takes its node's spare cover, and the budget is the cover
    less the proposals plus the headroom. With all stake on one node no vote fits a cover, and the
    budget is the headroom. Any other spread lies between, and Cardano's pools lie between."""
    assert sg.vote_budget(np.ones(1000)) == pytest.approx(1 - 2 / 30 + 4 / 3, rel=1e-9)
    one = np.zeros(1000)
    one[0] = 1.0
    assert sg.vote_budget(one) == pytest.approx(4 / 3, rel=1e-9)
    rng = np.random.default_rng(3)
    for _ in range(5):
        v = sg.vote_budget(rng.pareto(1.2, 1000) + 1e-3)
        assert 4 / 3 - 1e-9 <= v <= 1 - 2 / 30 + 4 / 3 + 1e-9


def test_a_leaders_win_is_tied_to_its_node():
    """A proposal goes out twice, so alone it is attributed as D5 counts it. A leader that also
    votes in every round of its window sends 40 votes a win on top of today's cover, and a direct
    draw of attributions agrees with the closed form."""
    q = 0.2 ** 3
    assert sg.link_chance(2, q) == pytest.approx(1 - (1 - q) ** 2, rel=1e-12)
    assert sg.leader_votes("on top") == pytest.approx(40.0, rel=1e-12)
    assert sg.leader_votes("raised") == pytest.approx(4 / 3, rel=1e-12)
    rng = np.random.default_rng(11)
    m = 2 + int(sg.leader_votes("on top"))
    linked = (rng.random((200_000, m)) < q).any(axis=1).mean()
    p = sg.link_chance(m, q)
    assert abs(linked - p) < 4 * math.sqrt(p * (1 - p) / 200_000)
