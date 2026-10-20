"""Gates for phase J's attacks within Δ (src/finality_sim/delayfc.py, PLAN.md J.2)."""

import math

import numpy as np
import pytest

from finality_sim import delayfc as d
from finality_sim.areon import Dag, dag_race
from finality_sim.balance import threshold
from finality_sim.race import race


# --- the construction, with explicit blocks and views ------------------------------------------

def _explicit(h, a, delta, fixed):
    """The balance played with explicit blocks and views. A producer at slot ``t`` sees every
    block of the conflict older than ``t - delta``; the adversary may show it or not the honest
    blocks of slots ``t - delta .. t - 1`` and its own wins placed from slot ``t - delta`` on; it
    cannot see honest blocks of its own slot. It prefers the heavier side; a tie goes where the
    adversary steers it, or to X under a fixed rule. The adversary aims the j-th block of a phase
    at the side the phase starts on (X, or Y while Y leads by one under a fixed rule) for odd j
    and at the other for even j, and spends its withheld wins as the construction says. Every
    aimed block must be feasible from some view the delay allows.

    Returns, for each slot that closes a phase or ends a balance, ``(slot, reserve, stood)``. A
    balance that fails is begun afresh, with an empty reserve, when the next phase opens.
    """
    out = []
    reserve, alive = 0, True
    forced = {+1: 0, -1: 0}                   # the conflict's blocks every view holds
    recent = []                               # (slot, side, honest) not yet in every view
    phase = []                                # sides of the open phase's honest blocks
    first, quiet = +1, 0
    for t in range(len(h)):
        if not phase and h[t] > 0 and not alive:
            reserve, alive = 0, True
            forced, recent = {+1: 0, -1: 0}, []
        keep = []
        for s, side, honest in recent:
            if s <= t - delta - 1:
                forced[side] += 1
            else:
                keep.append((s, side, honest))
        recent = keep
        if alive:
            reserve += a[t]
        if h[t] > 0 and not phase:             # every block of the conflict is public by now
            lead = forced[+1] - forced[-1] + sum(side for _, side, _ in recent)
            first = +1 if (not fixed or lead >= 0) else -1
        for _ in range(h[t]):
            j = len(phase) + 1
            aim = first if j % 2 == 1 else -first
            if alive and fixed and j == 2:
                if reserve >= 1:
                    reserve -= 1
                    recent.append((t, -first, False))
                else:
                    alive = False
                    out.append((t, 0, False))
            if alive:
                opt = {+1: 0, -1: 0}
                for s, side, honest in recent:
                    if s < t or not honest:
                        opt[side] += 1
                if aim == +1:
                    assert forced[+1] + opt[+1] - forced[-1] >= 0, (t, j, phase)
                else:
                    assert forced[-1] + opt[-1] - forced[+1] >= (1 if fixed else 0), (t, j, phase)
            phase.append(aim)
            recent.append((t, aim, True))
        if h[t] > 0:
            quiet = 0
        elif phase:
            quiet += 1
        if phase and (quiet >= delta if delta > 0 else h[t] > 0):
            if alive:
                x = forced[+1] + sum(1 for _, s, _ in recent if s == +1)
                y = forced[-1] + sum(1 for _, s, _ in recent if s == -1)
                diff = x - y
                if (not fixed and diff != 0) or (fixed and len(phase) == 1):
                    if reserve >= 1:
                        reserve -= 1
                        recent.append((t, -1 if diff > 0 else +1, False))
                        diff += -1 if diff > 0 else 1
                    else:
                        alive = False
                        out.append((t, 0, False))
                if alive:
                    assert diff in ((0, -1) if fixed else (0,)), (t, phase, diff)
                    out.append((t, reserve, True))
            phase, quiet = [], 0
    return out


def _module(h, a, delta, fixed, unit=False, realised=False):
    """The module's walk on the same draws, restarted the same way: ``(slot, s, r, stood)`` at
    each close and each failure."""
    out = []
    s, r, q, ps, u = 0, 0, 0, 0, 0
    open_phase, quiet = False, 0
    for t in range(len(h)):
        if not open_phase and h[t] > 0 and u == 2:
            s, r, q, ps, u = 0, 0, 0, 0, 0
        was_alive = u != 2
        s = d._wins(s, u, int(a[t]), d.BALANCE, unit)
        s, r, q, ps, u = d._honest(s, r, q, ps, u, int(h[t]), delta, fixed, d.BALANCE, unit,
                                   realised, -1)
        if h[t] > 0:
            open_phase, quiet = True, 0
        elif open_phase:
            quiet += 1
        closes = open_phase and (quiet >= delta if delta > 0 else h[t] > 0)
        if was_alive and u == 2:
            out.append((t, 0, 0, False))
        elif u != 2 and closes:
            out.append((t, s, r, True))
        if closes:
            open_phase, quiet = False, 0
    return out


@pytest.mark.parametrize("fixed", [False, True])
@pytest.mark.parametrize("delta", [0, 1, 5])
@pytest.mark.parametrize("alpha", [0.1, 0.3])
def test_the_balance_is_realised_with_explicit_views(fixed, delta, alpha):
    """Fast blocks, so that phases are long: the walk's reserve after every close, and every
    failure, are those of the construction, and every block the construction aims is feasible
    within the delay. Against 10 % the reserve runs out often, against 30 % it grows."""
    lam_h, lam_a = d.rates(0.25, alpha)
    h, a = d.draws(60_000, lam_h, lam_a, 31 + delta)
    got = _module(h, a, delta, fixed)
    ref = [(t, r, 0, ok) for t, r, ok in _explicit(h, a, delta, fixed)]
    assert len(ref) > 2_000
    assert alpha > 0.2 or sum(1 for x in ref if not x[3]) > 100
    assert got == ref


def _explicit_retract(h, a, delta, fixed):
    """The balance with retraction, played on blocks that carry win tags (GHOST with tags, E3): a
    side weighs its honest blocks and the tags found on it and not on the other side. A producer
    at slot ``t`` sees every block older than ``t - delta``, may be shown or not the honest blocks
    of slots ``t - delta .. t - 1`` and the copies released from slot ``t - delta`` on, and cannot
    see honest blocks of its own slot; the adversary chooses, tag by tag, the copies that serve
    the aim. The schedule is the walk's: each move retracts a placement on the side the move
    leaves, by a copy on the other, if there is one, else places a withheld win; with ties
    steered each phase starts on a side holding a placement; under a fixed rule a close passes
    to the other balanced state by the walk's rule. Every aimed block must be feasible.

    Returns ``(slot, s, r, stood)`` at each close and each failure, ``s`` and ``r`` as the walk
    counts them; a failed balance is begun afresh when the next phase opens.
    """
    out = []
    fresh, alive = 0, True
    honest = []                               # (slot, side) of the conflict's honest blocks
    copies = []                               # (release slot, side, tag)
    placed = {+1: [], -1: []}                 # tags placed on a side and not retracted
    phase, quiet, first, tags = [], 0, +1, 0

    def lead():                               # X - Y over everything released
        on = {}
        for _, side, tag in copies:
            on.setdefault(tag, set()).add(side)
        w = sum(s for _, s in honest)
        return w + sum(next(iter(v)) for v in on.values() if len(v) == 1)

    def counts():
        if not fixed:
            return 2 * fresh + len(placed[+1]) + len(placed[-1]), 0
        cur = +1 if lead() == 0 else -1       # the side a move in this state takes weight from
        return fresh, len(placed[cur]) - len(placed[-cur])

    def move(toward, t):
        """One move toward ``toward``: retract a placement on the other side, else place."""
        nonlocal fresh, tags
        if placed[-toward]:
            tag = placed[-toward].pop()
            copies.append((t, toward, tag))
            return True
        if fresh >= 1:
            fresh -= 1
            copies.append((t, toward, tags))
            placed[toward].append(tags)
            tags += 1
            return True
        return False

    def feasible(t, aim):
        need = 1 if (fixed and aim == -1) else 0
        diff = 0
        for s, side in honest:                # honest blocks: shown when they help, if allowed
            if s <= t - delta - 1:
                diff += side * aim
            elif s < t and side == aim:
                diff += 1
        on = {}
        for rel, side, tag in copies:
            on.setdefault(tag, {})[side] = rel
        for sides in on.values():             # per tag: show the aim's copy, hide the other's
            def can_show(side):
                return side in sides and sides[side] <= t
            def must_show(side):
                return side in sides and sides[side] <= t - delta - 1
            if can_show(aim) and not must_show(-aim):
                diff += 1
            elif not can_show(aim) and must_show(-aim):
                diff -= 1
        return diff >= need

    for t in range(len(h)):
        if not phase and h[t] > 0 and not alive:
            fresh, alive, honest, copies, placed = 0, True, [], [], {+1: [], -1: []}
        if alive:
            fresh += a[t]
        if h[t] > 0 and not phase:
            if fixed:
                first = +1 if lead() == 0 else -1
            else:
                first = +1 if placed[+1] or not placed[-1] else -1
        for _ in range(h[t]):
            j = len(phase) + 1
            aim = first if j % 2 == 1 else -first
            if alive and fixed and j == 2 and not move(-first, t):
                alive = False
                out.append((t, 0, 0, False))
            if alive:
                assert feasible(t, aim), (t, j, phase)
            phase.append(aim)
            honest.append((t, aim))
        if h[t] > 0:
            quiet = 0
        elif phase:
            quiet += 1
        if phase and (quiet >= delta if delta > 0 else h[t] > 0):
            if alive:
                due = (len(phase) == 1) if fixed else (len(phase) % 2 == 1)
                if due and not move(-first, t):
                    alive = False
                    out.append((t, 0, 0, False))
            if alive:
                assert lead() in ((0, -1) if fixed else (0,)), (t, phase, lead())
                s, r = counts()
                if fixed and r <= -max(1, s // 2) and s >= 1:
                    move(-1 if lead() == 0 else +1, t)
                    s, r = counts()
                out.append((t, s, r, True))
            phase, quiet = [], 0
    return out


@pytest.mark.parametrize("fixed", [False, True])
@pytest.mark.parametrize("delta", [0, 1, 5])
@pytest.mark.parametrize("alpha", [0.04, 0.3])
def test_retraction_is_realised_with_explicit_tags(fixed, delta, alpha):
    """The retraction walk (ties steered: two moves a win in either direction; a fixed rule:
    placements kept with their direction, and the rule's passes between states) against the
    construction on tagged blocks: the same counts after every close and every failure, and every
    aimed block feasible."""
    lam_h, lam_a = d.rates(0.25, alpha)
    h, a = d.draws(40_000, lam_h, lam_a, 77 + delta)
    got = _module(h, a, delta, fixed, unit=not fixed, realised=fixed)
    ref = _explicit_retract(h, a, delta, fixed)
    assert len(ref) > 1_500
    assert alpha > 0.2 or sum(1 for x in ref if not x[3]) > 30
    assert got == ref


# --- the exact curves against the walk sampled ----------------------------------------------

REALISED = dict(moves=2, s_lo=-40, s_hi=60, r_max=24)
CASES = [("balance", "steered", False, 0.35, {}), ("balance", "fixed", False, 0.35, {}),
         ("attack", "steered", True, 0.35, {}), ("attack", "fixed", True, 0.35, {}),
         ("attack", "fixed", False, 0.35, {}), ("private", "fixed", True, 0.35, {}),
         ("balance", "steered", False, 0.20, dict(moves=2)),
         ("attack", "steered", True, 0.20, dict(moves=2)),
         ("balance", "fixed", False, 0.22, dict(moves=2, relaxed=True)),
         ("attack", "fixed", True, 0.22, dict(moves=2, relaxed=True)),
         ("balance", "fixed", False, 0.22, REALISED),
         ("attack", "fixed", False, 0.22, REALISED)]


@pytest.mark.parametrize("mode,ties,premined,alpha,kw", CASES)
def test_exact_curves_match_the_sampled_walk(mode, ties, premined, alpha, kw):
    """Sixteen independent runs of 1.5 million slots against the exact distribution, at depths
    where the success is between 1e-4 and 1, with the standard error taken across the runs: one
    move per win against 35 %, and with retraction below its edge."""
    f, delta, k_max = 1 / 30, 10, 1800
    c = d.curve(f, alpha, delta, ties, mode, k_max, premined=premined, stop=0.0, **kw)
    key = "hold" if mode == "balance" else "ever"
    seeds = np.random.SeedSequence(2026).generate_state(16)
    runs = [d.play(f, alpha, delta, ties, mode, 1_500_000, k_max, int(s), extra=8000,
                   premined=premined, **kw) for s in seeds]
    for k in (0, 300, 900, 1800):
        for name, idx in ((key, 1), ("at", 0)):
            if mode == "balance" and name == "at":
                continue
            x = np.array([r[idx][k] / r[2] for r in runs])
            se = x.std(ddof=1) / math.sqrt(x.size)
            exact = c[name][k]
            assert abs(x.mean() - exact) <= 4.5 * se + 1e-4 * exact, (name, k, x.mean(), exact, se)


# --- the private race is B3's and E2's ----------------------------------------------------------

def test_private_race_on_a_chain_is_b3s_race():
    """At most one honest block and one win a slot, no delay: the weight race is the chain race,
    count for count."""
    rng = np.random.default_rng(5)
    h = (rng.random(300_000) < 0.03).astype(np.int64)
    a = (rng.random(300_000) < 0.014).astype(np.int64)
    k_max = 12
    ref, n_ref = race(np.nonzero(h)[0], np.nonzero(a)[0], k_max)
    got, n_got = d.private_race_blocks(h, a, k_max, 60, 1, 0, int(h.sum()) - k_max - 1)
    assert n_got == n_ref and got.tolist() == ref.tolist()


def _dag_without_delay(h, a):
    """Areon-Base without delay: each block references every block of the previous occupied
    slot."""
    slot, height, refs = [-1], [0], [[]]
    prev, layer = [0], 0
    for t in np.nonzero(h)[0]:
        layer += 1
        ids = list(range(len(slot), len(slot) + int(h[t])))
        for _ in ids:
            slot.append(int(t))
            height.append(layer)
            refs.append(list(prev))
        prev = ids
    n = len(slot)
    ref_ptr = np.concatenate(([0], np.cumsum([len(r) for r in refs]))).astype(np.int64)
    return Dag(slot=np.array(slot, np.int64), height=np.array(height, np.int64),
               producer=np.zeros(n, np.int64), ref_ptr=ref_ptr,
               refs=np.array([x for r in refs for x in r], np.int64),
               long_ref=np.zeros(n, dtype=bool),
               adv_slots=np.repeat(np.arange(a.size), a).astype(np.int64),
               tips_seen=np.array([max(len(r), 1) for r in refs], np.int64))


@pytest.mark.parametrize("win_at", [0, 1])
def test_private_race_without_delay_is_e2s_race(win_at):
    """Several honest blocks and wins a slot, no delay: the race equals E2's on the DAG, with
    the target's siblings counting for neither side, count for count."""
    lam_h, lam_a = d.rates(0.25, 0.3)
    h, a = d.draws(20_000, lam_h, lam_a, 9)
    dag = _dag_without_delay(h, a)
    k_max, last = 10, dag.n_blocks - 40
    ref, n_ref = dag_race(dag, k_max, window=10 ** 9, premine=True, win_at=win_at, first=1,
                          last=last, descendants_only=True)
    got, n_got = d.private_race_blocks(h, a, k_max, 60, win_at, 0, last - 1)
    assert n_got == n_ref > 1_000 and got.tolist() == ref.tolist()
    assert (h > 1).sum() > 200


# --- the edge, and the shape of the curves -----------------------------------------------------

@pytest.mark.parametrize("ties,rule", [("steered", "adversarial"), ("fixed", "deterministic")])
def test_the_balance_ends_below_the_edge_and_may_last_above_it(ties, rule):
    """E5's edge: below it the balance's chance of standing falls toward zero, above it toward a
    positive limit."""
    f, delta = 0.25, 5
    edge = threshold(f, delta, rule)
    below = d.curve(f, edge - 0.03, delta, ties, "balance", 20_000, premined=False, stop=0.0)
    above = d.curve(f, edge + 0.03, delta, ties, "balance", 20_000, premined=False, stop=0.0)
    assert below["hold"][-1] < 1e-3 * below["hold"][100]
    assert above["hold"][-1] > 0.5 * above["hold"][10_000] > 0.01


@pytest.mark.parametrize("mode,ties", [("attack", "steered"), ("attack", "fixed"),
                                       ("private", "fixed"), ("balance", "fixed")])
def test_success_falls_with_depth(mode, ties):
    c = d.curve(1 / 30, 1 / 3, 10, ties, mode, 6 * 3600, stop=0.0)
    v = c["hold" if mode == "balance" else "ever"]
    assert np.all(np.diff(v) <= 1e-15) and v[-1] < 0.5 * v[0]


# --- retraction: the edges, the best switches ------------------------------------------------

JT = {1: (0.3184, 0.3258), 2: (0.3085, 0.3207), 5: (0.2797, 0.3052), 10: (0.2352, 0.2789),
      20: (0.1623, 0.2260)}


@pytest.mark.parametrize("delta", sorted(JT))
def test_retraction_edges_are_jts(delta):
    """Two moves a win against a move a phase: the edges equal ``convergence``'s, written for
    J.1, and the four-digit values JT reported, at today's block rate."""
    from finality_sim.convergence import retraction_threshold
    for i, (ties, rule) in enumerate((("steered", "adversarial"), ("fixed", "deterministic"))):
        mine = d.edge(1 / 30, delta, ties, 2)
        assert mine == pytest.approx(retraction_threshold(1 / 30, delta, rule), abs=1e-12)
        assert round(mine, 4) == JT[delta][i]
        assert d.edge(1 / 30, delta, ties, 1) == pytest.approx(threshold(1 / 30, delta, rule),
                                                               abs=1e-12)


@pytest.mark.parametrize("ties,kw", [("steered", dict(moves=2)),
                                     ("fixed", dict(moves=2, relaxed=True)),
                                     ("fixed", dict(policy="best", **REALISED))])
def test_the_retraction_walks_end_below_their_edge_and_may_last_above_it(ties, kw):
    """The walks' own drift changes sign at the edge of two moves a win: below it the balance's
    chance of standing falls toward zero, above it toward a positive limit, the realised rule's
    passes between states included."""
    f, delta = 0.25, 5
    edge = d.edge(f, delta, ties, 2)
    below = d.curve(f, edge - 0.02, delta, ties, "balance", 20_000, premined=False, stop=0.0,
                    **kw)["hold"]
    above = d.curve(f, edge + 0.02, delta, ties, "balance", 20_000, premined=False, stop=0.0,
                    **kw)["hold"]
    assert below[-1] < 1e-4 * below[100]
    assert above[-1] > 0.95 * above[10_000] > 0.005


@pytest.mark.parametrize("mode", ["balance", "attack"])
def test_the_best_switches_lie_between_the_rule_and_the_relaxed_count(mode):
    """A realised fixed rule that chooses its passes between states best does at least as well as
    the rule and no better than two moves a win in a free direction, at every depth."""
    f, alpha, delta, k = 1 / 30, 0.25, 2, 3600
    key = "hold" if mode == "balance" else "ever"
    rule = d.curve(f, alpha, delta, "fixed", mode, k, premined=False, stop=0.0, **REALISED)[key]
    best = d.curve(f, alpha, delta, "fixed", mode, k, premined=False, stop=0.0, policy="best",
                   **REALISED)[key]
    relaxed = d.curve(f, alpha, delta, "fixed", mode, k, premined=False, stop=0.0, moves=2,
                      relaxed=True)[key]
    assert np.all(rule <= best * (1 + 1e-9) + 1e-300)
    assert np.all(best <= relaxed * (1 + 1e-9) + 1e-300)
    assert best[-1] > 1.5 * rule[-1] and relaxed[-1] > 1.5 * best[-1]


def test_after_the_race_the_wins_left_are_two_moves_each():
    """Hand-counted: the target's side leads by two, so ``s = -2``; five wins arrive, ``s = 3``;
    when the phase closes the coalition places two wins on the other side and keeps three: six
    moves with ties steered, and three withheld wins with no placement under a realised fixed
    rule."""
    for fixed, unit, realised, want in ((False, True, False, (6, 0)), (True, False, True, (3, 0))):
        s, r, q, ps, u = -2, 0, 0, 2, 1
        s = d._wins(s, u, 5, d.ATTACK, unit)
        for _ in range(3):
            s, r, q, ps, u = d._honest(s, r, q, ps, u, 0, 3, fixed, d.ATTACK, unit, realised, -1)
        assert (s, r, u) == (*want, 0)
