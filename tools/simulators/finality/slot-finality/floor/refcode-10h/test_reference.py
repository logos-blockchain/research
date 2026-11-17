# Tests of the reference code, with mutations that each test must catch.
#   python3 test_reference.py
import random
import sys
import traceback

import reference as R
from reference import Block

ORIGINAL = {n: getattr(R, n) for n in dir(R) if callable(getattr(R, n)) and not n.startswith("__")}


def chain(parent, start, stop, step, uncles=None):
    out, x = [], parent
    for sl in range(start, stop, step):
        x = Block(x, sl, (uncles or {}).get(sl, ()))
        out.append(x)
    return out


# ---- constants


def test_constants():
    assert R.KK == 36000
    assert 3 * R.U == 194400 and 6 * R.U == 388800 and 10 * R.U == 648000
    assert 3 * R.U >= R.KK               # each phase that waits for a value to finalize
    assert R.S_GEN == 16200
    assert 2 * R.S_GEN <= R.KK           # two density windows within the finality window
    assert 12 * 30 < R.KK                # the uncle window
    assert 20 * 60 < R.KK                # T_offline


def test_floor_values():
    assert R.finality_floor(64800, 1 / 30, 15, 1e-9) == 1291
    assert R.finality_floor(64800, 1 / 30, 10, 1e-9) == 1443   # so 1,291 holds at 10 s too
    assert R.finality_floor(36000, 1 / 30, 15, 1e-9) == 689    # the window of #533
    assert R.finality_floor(36000, 1 / 30, 10, 1e-9) == 768   # so 689 holds at 10 s too
    assert R.finality_floor(R.KK, R.f, R.T_M, R.EPSILON) == 689


def test_floor_is_the_edge():
    at = R.blocks_short(1291, 64800, 1 / 30, 15)
    past = R.blocks_short(1292, 64800, 1 / 30, 15)
    assert 9.9e-10 < at < 1e-9, at
    assert past > 1e-9, past
    at = R.blocks_short(689, 36000, 1 / 30, 15)
    past = R.blocks_short(690, 36000, 1 / 30, 15)
    assert at <= 1e-9 < past, (at, past)


def test_floor_against_a_second_form():
    # P(sum of n gaps > K) directly from the geometric's distribution, on a small case.
    K, f, delta = 900, 1 / 30, 15
    p = f
    for n in (3, 8, 12):
        # dp over the sum of n geometric waits, truncated at the budget
        budget = K - n * delta
        dist = [0.0] * (budget + 1)
        dist[0] = 1.0
        for _ in range(n):
            new = [0.0] * (budget + 1)
            for s, m in enumerate(dist):
                if m == 0.0:
                    continue
                w, q = 1, p
                while s + w <= budget:
                    new[s + w] += m * q
                    q *= 1 - p
                    w += 1
            dist = new
        direct = 1 - sum(dist)
        assert abs(direct - R.blocks_short(n, K, f, delta)) < 1e-9, (n, direct)


# ---- density_over_slots and the floor's first slot


def test_density_over_slots_range():
    g = Block(None, 0)
    xs = chain(g, 10, 110, 10)  # slots 10..100
    assert R.density_over_slots(xs[-1], 11, 90) == 9        # [11, 101): 20..100
    assert R.density_over_slots(xs[-1], 10, 91) == 10       # [10, 101)
    assert R.density_over_slots(xs[-1], 20, 10) == 1        # [20, 30)


def test_floor_counts_after_C_up_to_the_tip():
    g = Block(None, 0)
    xs = chain(g, 10, 110, 10)
    C, tip = xs[0], xs[-1]
    # C's own slot is out, the tip's slot is in
    assert R.density_over_slots(tip, C.slot + 1, tip.slot - C.slot) == 9


def test_uncle_rules_of_the_count():
    g = Block(None, 0)
    a = Block(g, 100)
    u_before = Block(g, 50)
    u_in = Block(a, 150)
    u_dup = Block(a, 150)
    u_same = Block(a, 200)
    b = Block(a, 200, [u_before, u_in, u_dup, u_same])
    c = Block(b, 300)
    # [101, 301): blocks at 200, 300; uncle at 150; the uncle at 50 is out of range; 200 and 150 once
    assert R.density_over_slots(c, 101, 200) == 3
    # a block out of range brings no uncle: [101, 200) holds the uncle's slot, its referencer is out
    assert R.density_over_slots(c, 101, 99) == 0


# ---- commit


def online(K, phi, g):
    return R.State(g, K, K // 4, phi, "ONLINE")


def test_K_boundary():
    g = Block(None, 0)
    xs = chain(g, 10, 2000, 10)
    st = online(300, 1, g)
    for x in xs[:29]:  # slots 10..290: nothing is 300 old
        R.on_block(st, x)
    assert st.B_imm is g
    tip = xs[29]       # slot 300: g is 300 behind, and the child at slot 10 is 290 behind
    R.on_block(st, tip)
    assert st.B_imm is g
    R.on_block(st, xs[30])  # slot 310: the block at slot 10 is exactly 300 behind
    assert st.B_imm is xs[0], st.B_imm


def test_floor_holds_on_a_sparse_chain():
    g = Block(None, 0)
    xs = chain(g, 1000, 1000 + 7 * 500, 500)  # slots 1000, 1500, ... 4000
    st = online(300, 4, g)
    for x in xs:
        R.on_block(st, x)
    # every block but the last is 300 behind; the floor wants 4 occupied slots after it
    assert st.B_imm is xs[2], st.B_imm
    assert st.c_loc.height - st.B_imm.height == 4


def test_floor_exact_count():
    g = Block(None, 0)
    a = Block(g, 1000)
    rest = chain(a, 1100, 1400, 100)   # 1100, 1200, 1300
    for phi, expect in ((3, a), (4, g)):
        st = online(300, phi, g)
        for x in [a] + rest:
            R.on_block(st, x)
        assert st.B_imm is expect, (phi, st.B_imm)


def test_uncle_counts_for_the_floor():
    g = Block(None, 0)
    a = Block(g, 1000)
    b = Block(a, 1100)
    u = Block(b, 1150)
    c = Block(b, 1200, [u])
    d = Block(c, 1300)
    # after a: 1100, 1150 (uncle), 1200, 1300 = 4 occupied slots
    st = online(300, 4, g)
    for x in (a, b, u, c, d):
        R.on_block(st, x)
    assert st.B_imm is a, st.B_imm


def test_B_imm_never_moves_back():
    g = Block(None, 0)
    xs = chain(g, 10, 1000, 10)
    st = online(300, 1, g)
    for x in xs:
        R.on_block(st, x)
    before = st.B_imm
    # a longer fork above B_imm whose tip's slot is lower than the old tip's
    fork_at = xs[-5]
    f1 = Block(fork_at, fork_at.slot + 1)
    f2 = Block(f1, fork_at.slot + 2)
    f3 = Block(f2, fork_at.slot + 3)
    f4 = Block(f3, fork_at.slot + 4)
    f5 = Block(f4, fork_at.slot + 5)
    for x in (f1, f2, f3, f4, f5):
        R.on_block(st, x)
    assert st.c_loc is f5
    assert st.c_loc.slot < xs[-1].slot
    assert st.B_imm is before and R.is_ancestor(before, st.c_loc)


def test_commit_reads_only_its_arguments():
    # The same inputs give the same output, and no slot tick exists: B_imm moves only on commit.
    g = Block(None, 0)
    xs = chain(g, 10, 1000, 10)
    T = {g, *xs}
    a = R.commit(T, xs[-1], g, 300, 1)[1]
    b = R.commit(T, xs[-1], g, 300, 1)[1]
    assert a is b


# ---- pruning


def test_prune_removes_every_fork_below():
    g = Block(None, 0)
    xs = chain(g, 30, 3000, 30)
    f1 = chain(xs[9], xs[9].slot + 1, xs[9].slot + 500, 50)
    f2 = chain(xs[19], xs[19].slot + 1, xs[19].slot + 300, 50)
    f3 = chain(g, 1, 400, 50)
    above = chain(xs[-3], xs[-3].slot + 1, xs[-3].slot + 3, 1)
    T = {g, *xs, *f1, *f2, *f3, *above}
    B = xs[50]
    Tp = R.prune_forks(T, B)
    for x in f1 + f2 + f3:
        assert x not in Tp, x
    for x in above + xs + [g]:
        assert x in Tp, x


def test_prune_shared_path():
    g = Block(None, 0)
    xs = chain(g, 30, 3000, 30)
    stem = chain(xs[4], xs[4].slot + 1, xs[4].slot + 200, 50)
    b1 = chain(stem[-1], stem[-1].slot + 1, stem[-1].slot + 100, 50)
    b2 = chain(stem[-1], stem[-1].slot + 2, stem[-1].slot + 100, 50)
    T = {g, *xs, *stem, *b1, *b2}
    Tp = R.prune_forks(T, xs[50])
    for x in stem + b1 + b2:
        assert x not in Tp
    assert Tp == {g, *xs}


# ---- fork choice


def fork_pair(gap_slot, K_top_offset):
    """Two chains from D; returns D, x, y with y the fork."""
    g = Block(None, 0)
    D = Block(g, gap_slot)
    x = chain(D, gap_slot + 30, gap_slot + K_top_offset + 1, 30)
    y = chain(D, gap_slot + 7, gap_slot + K_top_offset - 20, 60)
    return D, x, y


def test_bootstrap_boundary():
    K, sg = 900, 225
    g = Block(None, 0)
    D = Block(g, 100)
    # dense early, then short: the longer chain must win by length only below the boundary
    dense = chain(D, 110, 100 + sg, 10)            # dense in the window, then stops
    dense_tip = Block(dense[-1], 100 + K - 1)      # keeps the top at sl_D + K - 1
    sparse = chain(D, 100 + sg + 1, 100 + K - 1, 2)  # empty window, then many blocks; longer overall
    assert sparse[-1].height > dense_tip.height
    # sl_D = sl_top - K + 1: younger than K, so length
    assert sparse[-1].slot < 100 + K
    assert R.bootstrap_fork_choice(dense_tip, [dense_tip, sparse[-1]], K, sg, g) is sparse[-1]
    # one more slot makes sl_D = sl_top - K: density
    top = Block(sparse[-1], 100 + K)
    assert R.bootstrap_fork_choice(dense_tip, [dense_tip, top], K, sg, g) is dense_tip


def test_bootstrap_same_from_either_branch():
    rng = random.Random(7)
    K, sg = 900, 225
    decided = 0
    for _ in range(600):
        g = Block(None, 0)
        D = Block(g, rng.randint(1, 500))
        def grow(step):
            x, sl, out = D, D.slot, []
            end = D.slot + rng.randint(100, 2000)
            while True:
                sl += rng.randint(1, step)
                if sl > end:
                    return out
                x = Block(x, sl)
                out.append(x)
        a, b = grow(rng.randint(5, 60)), grow(rng.randint(5, 60))
        if not a or not b:
            continue
        a, b = a[-1], b[-1]
        w1 = R.bootstrap_fork_choice(a, [a, b], K, sg, g)
        w2 = R.bootstrap_fork_choice(b, [a, b], K, sg, g)
        d = R.common_prefix_depth(a, b)
        tied = (d[0] == d[1]) if D.slot > max(a.slot, b.slot) - K else (
            R.density(a, d[0], sg) == R.density(b, d[1], sg))
        if tied:
            assert w1 is a and w2 is b
        else:
            assert w1 is w2
            decided += 1
    assert decided > 300


def test_bootstrap_same_blocks_any_delivery_order():
    # A chain chosen by length while D is young must not keep c_loc past K with no comparison.
    K, sg, phi = 36000, 16200, 689
    g = Block(None, 0)
    D = Block(g, 1000)
    F = chain(D, 1020, 17201, 20)              # 810 blocks, all in the window, then it stops
    A = chain(D, 1200, 17201, 200)             # 81 blocks in the window
    A += chain(A[-1], 17240, 66310, 40)        # longer overall, its tip past D + K
    assert len(F) == 810 and A[-1].slot >= D.slot + K and len(A) > len(F)

    def deliver(order):
        st = R.State(g, K, sg, phi, "BOOTSTRAP")
        for b in [D] + order:
            R.on_block(st, b)
        return st.c_loc

    assert deliver(F + A) is F[-1]
    assert deliver(A + F) is F[-1]


def test_bootstrap_fixed_order():
    # Three forks whose comparisons form a cycle:
    # X beats Y by length, Y beats Z by density, Z beats X by density. Visited in list
    # order, [X, Y, Z] ends on Z and [X, Z, Y] on Y; visited by block ID, both agree.
    K, sg = 40, 10
    g = Block(None, 0)
    S = Block(g, 1)
    z = chain(S, 2, 6, 1)
    z.append(Block(z[-1], 20))
    z.append(Block(z[-1], 45))
    D = Block(S, 6)
    y = chain(D, 7, 11, 1)
    x = chain(D, 15, 31, 1)
    X, Y, Z = x[-1], y[-1], z[-1]
    beats = lambda a, b: R.bootstrap_fork_choice(b, [a], K, sg, g) is a
    assert beats(X, Y) and beats(Y, Z) and beats(Z, X)
    w1 = R.bootstrap_fork_choice(X, [X, Y, Z], K, sg, g)
    w2 = R.bootstrap_fork_choice(X, [X, Z, Y], K, sg, g)
    assert w1 is w2


def test_bootstrap_ignores_a_fork_below_B_imm_when_not_pruned():
    K, sg = 36000, 16200
    g = Block(None, 0)
    pre = chain(g, 30, 30001, 30)
    D = pre[-1]
    left = chain(D, 30005, 38001, 5)           # denser than main in the window
    main = chain(D, 30030, 170001, 30)
    B_imm = main[(105180 - 30030) // 30]
    assert R.density(left[-1], len(left), sg) > R.density(main[-1], len(main), sg)
    assert R.bootstrap_fork_choice(main[-1], [main[-1], left[-1]], K, sg, B_imm) is main[-1]


def test_density_counts_blocks_not_uncles():
    g = Block(None, 0)
    u = Block(g, 5)
    a = Block(g, 10, [u])
    assert R.density(a, 1, 100) == 1


def test_online_ignores_a_fork_below_B_imm_when_not_pruned():
    g = Block(None, 0)
    xs = chain(g, 10, 1000, 10)
    longer = chain(g, 1, 3000, 1)
    B_imm = xs[50]
    assert longer[-1].height > xs[-1].height
    assert R.online_fork_choice(xs[-1], [xs[-1], longer[-1]], B_imm) is xs[-1]


def test_online_longest_among_descendants():
    g = Block(None, 0)
    xs = chain(g, 10, 1000, 10)
    f = chain(xs[60], xs[60].slot + 1, xs[60].slot + 80, 1)
    assert f[-1].height > xs[-1].height
    assert R.online_fork_choice(xs[-1], [xs[-1], f[-1]], xs[50]) is f[-1]
    # a tie keeps the first seen
    shorter = chain(xs[-11], xs[-11].slot + 1, xs[-11].slot + 11, 1)
    assert shorter[-1].height == xs[-1].height
    assert R.online_fork_choice(xs[-1], [xs[-1], shorter[-1]], xs[50]) is xs[-1]


def test_online_fixed_order():
    # Two forks of equal length, both longer than the local chain, as can stand in the tree at
    # the first block after the switch. The result must not depend on the order of the list.
    g = Block(None, 0)
    xs = chain(g, 10, 200, 10)
    picks = set()
    for _ in range(40):
        a = chain(xs[5], xs[5].slot + 1, xs[5].slot + 40, 1)
        b = chain(xs[5], xs[5].slot + 2, xs[5].slot + 41, 1)
        assert a[-1].height == b[-1].height > xs[-1].height
        one = R.online_fork_choice(xs[-1], [xs[-1], a[-1], b[-1]], g)
        two = R.online_fork_choice(xs[-1], [b[-1], a[-1], xs[-1]], g)
        assert one is two
        assert one is min((a[-1], b[-1]), key=R.block_id)
        picks.add(one is a[-1])
    assert picks == {True, False}        # the block ID decides, not the order of creation


def test_common_prefix_depth_examples():
    g = Block(None, 0)
    a = chain(g, 1, 6, 1)
    assert R.common_prefix_depth(a[0], a[4]) == (0, 4)
    b2 = chain(a[1], 10, 12, 1)
    b5 = chain(a[1], 20, 23, 1)
    assert R.common_prefix_depth(b2[-1], b5[-1]) == (2, 3)


# ---- the switch


def switch_setup():
    K, sg, phi = 36000, 16200, 689
    g = Block(None, 0)
    pre = chain(g, 30, 1001, 30)
    D = pre[-1]
    x = chain(D, D.slot + 30, 120000, 30)                 # honest
    y = chain(D, D.slot + 300, D.slot + sg + 1, 300)      # sparse in the window
    y += chain(y[-1], y[-1].slot + 20, 119990, 20)        # longer overall
    st = R.State(g, K, sg, phi, "BOOTSTRAP")
    for b in pre + x + y:
        R.on_block(st, b)
    return st, D, x, y


def test_bootstrap_rejects_and_freezes():
    st, D, x, y = switch_setup()
    assert y[-1].height > x[-1].height
    assert st.c_loc is x[-1]
    assert st.B_imm.slot == 0


def test_switch_prunes_what_bootstrap_rejected():
    st, D, x, y = switch_setup()
    R.switch_to_online(st)
    assert R.is_ancestor(D, st.B_imm) and st.B_imm is not D
    assert y[-1] not in st.T
    nb = Block(y[-1], 120005)
    R.on_block(st, nb)                                    # its parent is gone: rejected
    assert st.c_loc is x[-1]
    assert R.is_ancestor(x[0], st.B_imm)


def test_without_commit_at_the_switch_the_attacker_wins():
    # The negative control: this is the attack the rule closes.
    st, D, x, y = switch_setup()
    st.rule = "ONLINE"
    nb = Block(y[-1], 120005)
    R.on_block(st, nb)
    assert st.c_loc is nb
    assert R.is_ancestor(y[0], st.B_imm)


def lag_setup():
    # The relaying peers withheld the honest chain after slot 20, so the node's tip lags.
    # The fork loses by density under the Bootstrap rule, and is longer than what the node holds.
    K, sg, phi = 40, 10, 4
    g = Block(None, 0)
    D = Block(g, 1)
    h = chain(D, 2, 7, 1)
    h.append(Block(h[-1], 20))                  # the last honest block relayed to the node
    rest = [Block(h[-1], 30)]
    for sl in (45, 60):
        rest.append(Block(rest[-1], sl))        # what the last round has to fetch
    f = [Block(D, 8)]
    f += chain(f[-1], 25, 41, 1)
    for sl in (50, 55, 62):
        f.append(Block(f[-1], sl))
    fx = Block(f[-1], 63)
    st = R.State(g, K, sg, phi, "BOOTSTRAP")
    for b in [D] + h + f:
        R.on_block(st, b)
    assert st.c_loc is h[-1]                    # the fork loses by density
    return st, g, h, rest, f, fx


def fork_wins(st, f, fx):
    R.switch_to_online(st)
    R.on_block(st, fx)
    return st.c_loc is fx and R.is_ancestor(f[0], st.B_imm)


def test_last_round_before_the_switch():
    # Without the last round, the fork the Bootstrap rule rejected wins after the switch. With
    # it, one honest peer's tip brings the node up to date, and commit at the switch prunes the
    # fork.
    st, g, h, rest, f, fx = lag_setup()
    assert fork_wins(st, f, fx)
    st, g, h, rest, f, fx = lag_setup()
    R.last_round(st, [R.Peer(rest[-1])], 100)
    assert not fork_wins(st, f, fx)
    assert st.c_loc is rest[-1] and f[0] not in st.T


def test_last_round_takes_a_tip_from_the_peer_that_returned_it():
    # The peers that fill the node's connections answer every request for blocks with one
    # invalid block. The honest peer still delivers its own tip, whatever the order of the peers.
    def poison(target, known):
        return [Block(target, target.slot)]     # fails rule 5: its slot does not follow its parent's

    for order in (0, 1):
        st, g, h, rest, f, fx = lag_setup()
        bad = [R.Peer(f[-1], poison), R.Peer(rest[-1], poison)]
        good = [R.Peer(rest[-1])]
        R.last_round(st, bad + good if order == 0 else good + bad, 100)
        assert rest[-1] in st.T
        assert not fork_wins(st, f, fx)


def test_last_round_runs_its_downloads_in_parallel():
    # A peer that returns a tip on a long valid fork must not keep the honest peer waiting.
    st, g, h, rest, f, fx = lag_setup()
    long_fork = chain(g, 12, 2000, 1)           # empty in the density window, so it loses
    R.last_round(st, [R.Peer(long_fork[-1]), R.Peer(rest[-1])], 100)
    assert rest[-1] in st.T and st.c_loc is rest[-1]
    assert not fork_wins(st, f, fx)


def test_last_round_is_limited():
    # The round ends after its limit even if a download has not returned, and the node switches.
    st, g, h, rest, f, fx = lag_setup()
    long_fork = chain(g, 12, 2000, 1)
    R.last_round(st, [R.Peer(long_fork[-1])], 100)
    assert sum(1 for b in long_fork if b in st.T) == 100
    R.switch_to_online(st)
    assert st.rule == "ONLINE"


def test_last_round_waits_for_an_ibd_peer():
    # A download from an IBD peer is not cancelled at the limit. A connected peer's is.
    st, g, h, rest, f, fx = lag_setup()
    R.last_round(st, [R.Peer(rest[-1], ibd=True)], 2)
    assert rest[-1] in st.T
    assert not fork_wins(st, f, fx)
    st, g, h, rest, f, fx = lag_setup()
    R.last_round(st, [R.Peer(rest[-1])], 2)
    assert rest[1] in st.T and rest[-1] not in st.T


def test_last_round_keeps_an_ibd_peer_that_resends_held_blocks():
    # An IBD peer that does not hold the node's tip starts its stream far below it. The blocks
    # it sends first are held already. It is not given up while it delivers them.
    st, g, h, rest, f, fx = lag_setup()
    whole = [b for b in reversed(list(R.ancestors(rest[-1]))) if b is not g]
    assert sum(1 for b in whole if b in st.T) > 3
    R.last_round(st, [R.Peer(rest[-1], lambda target, known: whole, ibd=True)], 3)
    assert rest[-1] in st.T
    assert not fork_wins(st, f, fx)


def test_last_round_gives_up_an_ibd_peer_that_adds_no_block():
    # An IBD peer that keeps answering with the same blocks is given up after the limit.
    st, g, h, rest, f, fx = lag_setup()
    calls = []

    def stale(target, known):
        calls.append(1)
        return list(h)

    R.last_round(st, [R.Peer(rest[-1], stale, ibd=True)], 20)
    assert rest[-1] not in st.T
    assert len(calls) <= 20


def test_last_round_gives_up_an_ibd_peer_that_sends_invalid_blocks():
    # An IBD peer that answers every request with a new invalid block is given up after the
    # limit: a block that fails validation is no progress.
    st, g, h, rest, f, fx = lag_setup()
    calls = []

    def poison(target, known):
        calls.append(1)
        assert len(calls) <= 500, "the round does not end"
        return [Block(target, target.slot)]         # a new block each time, and it fails rule 5

    R.last_round(st, [R.Peer(rest[-1], poison, ibd=True)], 20)
    assert rest[-1] not in st.T
    assert len(calls) <= 21


def test_last_round_starts_a_failed_download_again():
    # A download that returns without its tip is started again while the limit lasts.
    st, g, h, rest, f, fx = lag_setup()
    calls = []

    def flaky(target, known):
        calls.append(1)
        if len(calls) == 1:
            return [Block(target, target.slot)]     # the first request fails
        return list(rest)

    R.last_round(st, [R.Peer(rest[-1], flaky)], 100)
    assert rest[-1] in st.T and len(calls) == 2


def test_last_round_with_no_answer():
    # No peer returns a tip: the round ends at its limit, and the node is not terminated.
    st, g, h, rest, f, fx = lag_setup()
    R.last_round(st, [R.Peer(None), R.Peer(None, ibd=True)], 100)
    assert st.c_loc is h[-1]


def test_last_round_asks_a_tip_again():
    # A tip request that fails is sent again.
    st, g, h, rest, f, fx = lag_setup()
    R.last_round(st, [R.Peer(None, tips=[None, None, rest[-1]])], 100)
    assert rest[-1] in st.T
    assert not fork_wins(st, f, fx)


def test_last_round_follows_a_tip_that_moves():
    # The peer's chain grows while the node downloads. The node asks the tip again after each
    # download, as Initial Block Download does in each of its rounds.
    st, g, h, rest, f, fx = lag_setup()
    R.last_round(st, [R.Peer(None, tips=[rest[0], rest[-1]], ibd=True)], 5)
    assert rest[-1] in st.T
    assert not fork_wins(st, f, fx)


def eclipse_setup():
    # The node completed Initial Block Download on the honest chain at slot 100, and recorded the
    # block K behind its tip. Its peers then withheld the honest chain and fed it a fork from
    # slot 95, which has been its local chain for more than K slots.
    K, sg, phi = 40, 10, 4
    g = Block(None, 0)
    H = chain(g, 1, 147, 1)                         # the honest chain: every slot up to 146
    st = R.State(g, K, sg, phi, "BOOTSTRAP", t_off=2)
    for b in H[:100]:
        R.on_block(st, b)
    R.start_bootstrap_period(st)
    assert st.recorded is H[59]                     # the block of slot 60
    F = chain(H[94], 96, 147, 2)                    # the fork: every second slot from 96 to 146
    for b in F:
        R.on_block(st, b)
    assert st.c_loc is F[-1]
    named = R.blocks_behind_tip(st, [st.t_off, st.s_gen, st.K])
    assert len(named) == 3 and all(R.is_ancestor(F[0], b) for b in named)   # the fork made all three
    return st, g, H, F


def test_last_round_names_the_recorded_block():
    # A fork that has been the local chain for more than K slots made every ancestor of the local
    # tip that the requests name. The recorded block lets an honest peer start its stream K below
    # the tip the node held when the period started, and the download fits the limit.
    st, g, H, F = eclipse_setup()
    R.last_round(st, [R.Peer(H[-1])], 100)
    assert st.c_loc is H[-1]
    R.switch_to_online(st)
    assert F[0] not in st.T


def test_last_round_names_ancestors_of_the_local_tip():
    # One private block on the node's tip makes that tip unknown to an honest peer. The latest
    # block T_offline behind it is on the honest chain, so the stream is short.
    K, sg, phi = 40, 10, 4
    g = Block(None, 0)
    H = chain(g, 1, 301, 1)                         # the honest chain: every slot up to 300
    st = R.State(g, K, sg, phi, "BOOTSTRAP", t_off=2)
    for b in H[:100]:
        R.on_block(st, b)
    R.start_bootstrap_period(st)                    # records the block of slot 60
    for b in H[100:290]:
        R.on_block(st, b)
    X = Block(H[289], 291)                          # private, on the node's tip of slot 290
    R.on_block(st, X)
    assert st.c_loc is X
    R.last_round(st, [R.Peer(H[-1])], 30)
    assert st.c_loc is H[-1]


def test_last_round_resumes_from_the_last_delivered_block():
    # An honest IBD peer whose connection breaks once. The download that is started again names
    # the last block the peer delivered, so the peer does not send again blocks that no longer
    # count, and it is not given up while it sends them.
    st, g, H, F = eclipse_setup()
    peer = R.Peer(H[-1], ibd=True)
    calls = []

    def breaks_once(target, known):
        calls.append(1)
        if len(calls) == 1:
            return peer.stream(target, known)[:30]  # the stream breaks after 30 blocks
        if len(calls) == 2:
            return []                               # and the next request fails
        return peer.stream(target, known)

    peer._serve = breaks_once
    R.last_round(st, [peer], 20)
    assert st.c_loc is H[-1]
    R.switch_to_online(st)
    assert F[0] not in st.T


def test_last_round_names_the_recorded_block_when_the_peer_left_a_branch():
    # The peer leaves the branch whose blocks it delivered, and no longer holds the last of them.
    # The node's tip is on that branch too. The recorded block still lets the peer start its
    # stream K below the tip the node held when the period started, and not at B_imm.
    st, g, H, F = eclipse_setup()
    S = Block(H[109], 111)                          # a branch of one block on the block of slot 110
    peer = R.Peer(None, tips=[S, H[-1]])
    R.last_round(st, [peer], 150)
    assert st.c_loc is H[-1]


def test_last_round_requests_stay_within_the_limit():
    # No request names more than 5 additional blocks, also in a download that is started again
    # from a peer that returns its blocks in batches.
    st, g, H, F = eclipse_setup()
    peer = R.Peer(H[-1], ibd=True, batch=10)
    sizes = []

    def watched(target, known):
        sizes.append(len(known))
        if len(sizes) == 3:
            return []                               # one request fails
        return peer.stream(target, known)

    peer._serve = watched
    R.last_round(st, [peer], 20)
    assert st.c_loc is H[-1]
    assert max(sizes) == 2 + R.MAX_ADDITIONAL_BLOCKS


def test_a_hold_does_not_help_without_commit():
    # The hold of the node's draft: B_imm stays, nothing is pruned, the fork wins by length.
    st, D, x, y = switch_setup()
    st.rule = "ONLINE"
    T = st.T | {Block(y[-1], 120005)}
    c = R.online_fork_choice(st.c_loc, R.tips(T), st.B_imm)
    assert R.is_ancestor(y[0], c)                         # B_imm held at genesis, the fork still wins


# ---- the offline grace period


def test_restart_example():
    # The node stops on the honest chain. The fork diverged almost K before the stop and is a
    # little shorter. It grows while the node is away, and passes the node's stale chain.
    K, sg, phi, off = 3600, 900, 4, 1200
    g = Block(None, 0)
    D = Block(g, 100)
    stop = D.slot + K - off // 2
    x = chain(D, D.slot + 60, stop, 60)
    y = chain(D, D.slot + 61, stop + off + 1, 60)
    st = R.State(g, K, sg, phi, "ONLINE")
    for b in [D] + x:
        R.on_block(st, b)
    assert st.c_loc is x[-1]
    assert st.B_imm is g or R.is_ancestor(st.B_imm, D)
    assert y[-1].height > x[-1].height
    assert y[-1].slot - D.slot >= K and x[-1].slot - D.slot < K
    for b in y:
        R.on_block(st, b)
    assert st.c_loc is y[-1]
    assert R.is_ancestor(y[0], st.B_imm)                   # immutable on the fork
    assert x[-1] not in st.T                               # the honest branch is gone


# ---- the uncle window


def test_candidate_parent_stays_above_B_imm():
    # W/f < K, so a candidate's parent is above the proposer's B_imm whatever the chain does.
    rng = random.Random(11)
    K, phi, window = 300, 4, 299
    checked = 0
    for seed in range(20):
        rng.seed(seed)
        g = Block(None, 0)
        st = R.State(g, K, K // 4, phi, "ONLINE")
        seen, clock = [g], 0
        for _ in range(1500):
            clock += rng.randint(1, 8)
            cands = [b for b in st.T if b.height >= st.B_imm.height]
            p = rng.choice(R.tips(st.T)) if rng.random() < 0.7 else rng.choice(cands)
            sl = max(p.slot + 1, clock - rng.randint(0, 60))
            if sl > clock:
                continue
            n = Block(p, sl)
            R.on_block(st, n)
            seen.append(n)
            sb = clock + 1
            on_chain = {id(x) for x in R.ancestors(st.c_loc)}
            for U in seen[-300:]:
                if U.parent and id(U.parent) in on_chain and id(U) not in on_chain \
                        and U.slot < sb and sb - U.parent.slot <= window:
                    assert U.parent.slot > st.B_imm.slot or U.parent is st.B_imm
                    assert U in st.T, "candidate pruned"
                    checked += 1
    assert checked > 1000


# ---- randomized invariants


def test_invariants():
    moves = reorgs = 0
    for seed in range(30):
        r = random.Random(seed)
        K, phi = 300, 4
        g = Block(None, 0)
        st = R.State(g, K, K // 4, phi, "ONLINE")
        clock = 0
        for _ in range(1500):
            clock += r.randint(1, 8)
            cands = [b for b in st.T if b.height >= st.B_imm.height]
            p = r.choice(R.tips(st.T)) if r.random() < 0.7 else r.choice(cands)
            sl = max(p.slot + 1, clock - r.randint(0, 60))
            if sl > clock:
                continue
            uncles = [u for u in cands if u.parent is not None and u is not p and u.slot < sl][:1] \
                if r.random() < 0.1 else []
            n = Block(p, sl, uncles)
            old_c, old_b = st.c_loc, st.B_imm
            R.on_block(st, n)
            assert R.is_ancestor(old_b, st.B_imm), "B_imm moved back"
            assert R.is_ancestor(st.B_imm, st.c_loc), "B_imm off the chain"
            if st.B_imm is not old_b:
                moves += 1
                assert st.B_imm.slot <= st.c_loc.slot - K
                assert R.density_over_slots(st.c_loc, st.B_imm.slot + 1, st.c_loc.slot - st.B_imm.slot) >= phi
            if st.c_loc is not old_c and st.c_loc.parent is not old_c:
                reorgs += 1
            for t in R.tips(st.T):
                assert R.is_ancestor(st.B_imm, t) or t.height <= st.B_imm.height and R.is_ancestor(t, st.B_imm)
    assert moves > 500 and reorgs > 200, (moves, reorgs)


TESTS = [v for n, v in sorted(globals().items()) if n.startswith("test_")]


def run_all(quiet=False, only=""):
    failed = []
    for t in TESTS:
        if only not in t.__name__:
            continue
        try:
            t()
            if not quiet:
                print(f"  ok    {t.__name__}")
        except Exception:
            failed.append(t.__name__)
            if not quiet:
                print(f"  FAIL  {t.__name__}")
                traceback.print_exc()
    return failed


# ---- mutations: each breaks one rule, and the tests must notice


def _m_no_floor():
    orig = ORIGINAL["commit"]
    def commit(T, c, B, K, phi):
        return orig(T, c, B, K, 0)
    R.commit = commit


def _m_no_window():
    def commit(T, c_loc, B_imm, K, phi):
        B = B_imm
        while B is not c_loc:
            C = R.child_on_chain(B, c_loc)
            if R.density_over_slots(c_loc, C.slot + 1, c_loc.slot - C.slot) < phi:
                break
            B = C
        return R.prune_forks(T, B), B
    R.commit = commit


def _m_window_off_by_one():
    def commit(T, c_loc, B_imm, K, phi):
        B = B_imm
        while B is not c_loc:
            C = R.child_on_chain(B, c_loc)
            if C.slot >= c_loc.slot - K or R.density_over_slots(c_loc, C.slot + 1, c_loc.slot - C.slot) < phi:
                break
            B = C
        return R.prune_forks(T, B), B
    R.commit = commit


def _m_floor_counts_C():
    def commit(T, c_loc, B_imm, K, phi):
        B = B_imm
        while B is not c_loc:
            C = R.child_on_chain(B, c_loc)
            if C.slot > c_loc.slot - K or R.density_over_slots(c_loc, C.slot, c_loc.slot - C.slot + 1) < phi:
                break
            B = C
        return R.prune_forks(T, B), B
    R.commit = commit


def _m_floor_excludes_tip():
    def commit(T, c_loc, B_imm, K, phi):
        B = B_imm
        while B is not c_loc:
            C = R.child_on_chain(B, c_loc)
            if C.slot > c_loc.slot - K or R.density_over_slots(c_loc, C.slot + 1, c_loc.slot - C.slot - 1) < phi:
                break
            B = C
        return R.prune_forks(T, B), B
    R.commit = commit


def _m_prune_restarts():
    def prune_forks(T, B):
        Tp = set(T)
        for B_tip in R.tips(T):
            B_div = R.common_ancestor(B_tip, B)
            if B_div is not B:
                Tp = R.prune_blocks(B_tip, B_div, T)
        return Tp
    R.prune_forks = prune_forks


def _m_no_commit_at_switch():
    def switch_to_online(st):
        st.rule = "ONLINE"
    R.switch_to_online = switch_to_online


def _m_online_no_descent_check():
    def online_fork_choice(c_local, forks, B_imm):
        c_max = c_local
        for c_fork in forks:
            depth_max, depth_fork = R.common_prefix_depth(c_max, c_fork)
            if depth_max < depth_fork:
                c_max = c_fork
        return c_max
    R.online_fork_choice = online_fork_choice


def _m_online_unordered():
    def online_fork_choice(c_local, forks, B_imm):
        c_max = c_local
        for c_fork in forks:
            if not R.is_ancestor(B_imm, c_fork):
                continue
            depth_max, depth_fork = R.common_prefix_depth(c_max, c_fork)
            if depth_max < depth_fork:
                c_max = c_fork
        return c_max
    R.online_fork_choice = online_fork_choice


def _m_last_round_first_answer_wins():
    # The round as first written: the blocks of a tip come from the first peer that answers.
    def last_round(st, peers, limit):
        steps = 0
        for tip in [p.tip for p in peers if p.tip is not None and p.tip not in st.T]:
            for _ in R.download_blocks(st, tip, peers[0]):
                steps += 1
                if steps >= limit:
                    return
    R.last_round = last_round


def _m_last_round_sequential():
    # The peers are handled one after another.
    R.last_round = _last_round_variant(sequential=True)


def _last_round_variant(idle_factor=1, retry=True, by_tree=False, recorded=True, behind=True,
                        resume=True, both=False, only_last=False, tip_again=True, tip_fresh=True,
                        sequential=False):
    """The round of the reference code with one rule changed. With no argument it is the round
    itself, which `variant_is_the_round` checks."""
    def last_round(st, peers, limit):
        handled = [(p, None, 0, set(), None, None) for p in peers]
        step = 0
        while handled:
            still = []
            for i, (p, download, idle, seen, last, first_tip) in enumerate(handled):
                if sequential and i > 0:
                    still.append((p, download, idle, seen, last, first_tip))    # it waits its turn
                    continue
                if (idle >= limit * idle_factor) if p.ibd else (step >= limit):
                    continue
                counts = False
                if download is None:
                    tip = p.get_tip() if tip_fresh or first_tip is None else first_tip
                    if tip is None and not tip_again:
                        continue
                    if tip is not None and tip in st.T:
                        continue
                    if tip is not None:
                        first_tip = first_tip or tip
                        anchor = [st.recorded] if recorded else []
                        named = R.blocks_behind_tip(st, [st.t_off, st.s_gen, st.K]) if behind else []
                        if last is not None and both:
                            known = anchor + [last] + named
                        elif last is not None and only_last:
                            known = [last]
                        elif last is not None and resume:
                            known = anchor + [last]
                        else:
                            known = anchor + named
                        download = R.download_blocks(st, tip, p, known)
                if download is not None:
                    held = len(st.T)
                    b = next(download, None)
                    if b is None:
                        download = None
                        if not retry:
                            continue
                    else:
                        last = b
                        counts = len(st.T) > held if by_tree else b not in seen
                        seen.add(b)
                still.append((p, download, 0 if counts else idle + 1, seen, last, first_tip))
            handled, step = still, step + 1
    return last_round


def variant_is_the_round():
    """The variant with no rule changed passes every test, so a variant that fails a test fails
    it for the rule it changes."""
    R.last_round = _last_round_variant()
    failed = run_all(quiet=True, only="last_round")
    restore()
    return not failed


def _m_last_round_no_limit():
    # A connected peer is handled as an IBD peer: its download is not cancelled while it adds blocks.
    def last_round(st, peers, limit):
        for p in peers:
            p.ibd = True
        ORIGINAL["last_round"](st, peers, limit)
    R.last_round = last_round


def _m_last_round_one_limit():
    # One limit for every peer: a download from an IBD peer is cancelled too.
    def last_round(st, peers, limit):
        for p in peers:
            p.ibd = False
        ORIGINAL["last_round"](st, peers, limit)
    R.last_round = last_round


def _m_last_round_no_retry():
    R.last_round = _last_round_variant(retry=False)


def _m_last_round_patient_with_an_idle_ibd_peer():
    R.last_round = _last_round_variant(idle_factor=50)


def _m_last_round_counts_only_blocks_new_to_the_tree():
    R.last_round = _last_round_variant(by_tree=True)


def _m_last_round_counts_invalid_blocks():
    # A block that fails validation is reported as delivered before the download ends.
    def download_blocks(st, target, peer, known=()):
        latest = None
        while True:
            if target in st.T:
                return
            additional = list(known) + ([latest] if latest is not None else [])
            received = 0
            for b in peer.serve(target, [st.c_loc, st.B_imm] + additional):
                received += 1
                latest = b
                R.on_block(st, b)
                yield b
                if b not in st.T or b is target:
                    return
            if received == 0:
                return
    R.download_blocks = download_blocks


def _m_last_round_without_the_recorded_block():
    R.last_round = _last_round_variant(recorded=False)


def _m_last_round_names_only_the_recorded_block():
    R.last_round = _last_round_variant(behind=False)


def _m_last_round_starts_again_from_the_named_blocks():
    # A download that is started again does not name the last block the peer delivered.
    R.last_round = _last_round_variant(resume=False)


def _m_last_round_names_too_many_blocks():
    # The last delivered block is named beside the other blocks, which passes the limit of 5.
    R.last_round = _last_round_variant(both=True)


def _m_last_round_names_only_the_last_delivered_block():
    # A download that is started again does not name the recorded block.
    R.last_round = _last_round_variant(only_last=True)


def _m_last_round_asks_a_tip_once():
    R.last_round = _last_round_variant(tip_again=False)


def _m_last_round_keeps_the_first_tip():
    R.last_round = _last_round_variant(tip_fresh=False)


def _m_bootstrap_unordered():
    def bootstrap_fork_choice(c_local, forks, K, s_gen, B_imm):
        c_max = c_local
        for c_fork in forks:
            if not R.is_ancestor(B_imm, c_fork):
                continue
            depth_max, depth_fork = R.common_prefix_depth(c_max, c_fork)
            sl_div = R.grandparent(c_max, depth_max).slot
            sl_top = max(c_max.slot, c_fork.slot)
            if sl_div + K > sl_top:
                if depth_max < depth_fork:
                    c_max = c_fork
            else:
                if R.density(c_max, depth_max, s_gen) < R.density(c_fork, depth_fork, s_gen):
                    c_max = c_fork
        return c_max
    R.bootstrap_fork_choice = bootstrap_fork_choice


def _m_bootstrap_reads_local_tip_only():
    def bootstrap_fork_choice(c_local, forks, K, s_gen, B_imm):
        c_max = c_local
        for c_fork in sorted(forks, key=R.block_id):
            if not R.is_ancestor(B_imm, c_fork):
                continue
            depth_max, depth_fork = R.common_prefix_depth(c_max, c_fork)
            sl_div = R.grandparent(c_max, depth_max).slot
            if sl_div + K > c_max.slot:
                if depth_max < depth_fork:
                    c_max = c_fork
            else:
                if R.density(c_max, depth_max, s_gen) < R.density(c_fork, depth_fork, s_gen):
                    c_max = c_fork
        return c_max
    R.bootstrap_fork_choice = bootstrap_fork_choice


def _m_bootstrap_boundary():
    def bootstrap_fork_choice(c_local, forks, K, s_gen, B_imm):
        c_max = c_local
        for c_fork in sorted(forks, key=R.block_id):
            if not R.is_ancestor(B_imm, c_fork):
                continue
            depth_max, depth_fork = R.common_prefix_depth(c_max, c_fork)
            sl_div = R.grandparent(c_max, depth_max).slot
            sl_top = max(c_max.slot, c_fork.slot)
            if sl_div + K >= sl_top:
                if depth_max < depth_fork:
                    c_max = c_fork
            else:
                if R.density(c_max, depth_max, s_gen) < R.density(c_fork, depth_fork, s_gen):
                    c_max = c_fork
        return c_max
    R.bootstrap_fork_choice = bootstrap_fork_choice


def _m_density_loose_uncles():
    def density_over_slots(c, s, p):
        occupied = set()
        for x in R.ancestors(c):
            if s <= x.slot < s + p:
                occupied.add(x.slot)
            occupied.update(u.slot for u in x.uncles if s <= u.slot < s + p)
        return len(occupied)
    R.density_over_slots = density_over_slots


def _m_commit_under_bootstrap():
    orig = ORIGINAL["on_block"]
    def on_block(st, B):
        orig(st, B)
        st.T, st.B_imm = R.commit(st.T, st.c_loc, st.B_imm, st.K, st.phi)
    R.on_block = on_block


def _m_floor_wrong_rate():
    # the rate of the honest stake while a third withholds, as the floor was derived before
    def blocks_short(n, K, f, t_m):
        return ORIGINAL["blocks_short"](n, K, 1 - (1 - f) ** (2 / 3), t_m)
    R.blocks_short = blocks_short


def _m_floor_no_delay():
    def blocks_short(n, K, f, t_m):
        return ORIGINAL["blocks_short"](n, K, f, 0)
    R.blocks_short = blocks_short


def _m_bootstrap_no_descent_check():
    orig = ORIGINAL["bootstrap_fork_choice"]
    def bootstrap_fork_choice(c_local, forks, K, s_gen, B_imm):
        genesis = list(R.ancestors(c_local))[-1]
        return orig(c_local, forks, K, s_gen, genesis)
    R.bootstrap_fork_choice = bootstrap_fork_choice


def _m_bootstrap_skips_when_extending():
    def on_block(st, B):
        if B in st.T or B.parent not in st.T or B.slot <= B.parent.slot or B.height <= st.B_imm.height:
            return
        T = st.T | {B}
        if B.parent is st.c_loc:
            c = B
        elif st.rule == "BOOTSTRAP":
            c = R.bootstrap_fork_choice(st.c_loc, R.tips(T), st.K, st.s_gen, st.B_imm)
        else:
            c = R.online_fork_choice(st.c_loc, R.tips(T), st.B_imm)
        st.c_loc, st.T = c, T
        if st.rule == "ONLINE":
            st.T, st.B_imm = R.commit(st.T, st.c_loc, st.B_imm, st.K, st.phi)
    R.on_block = on_block


MUTATIONS = [v for n, v in sorted(globals().items()) if n.startswith("_m_")]


def restore():
    for n, v in ORIGINAL.items():
        setattr(R, n, v)


if __name__ == "__main__":
    failed = run_all()
    print(f"\n{len(TESTS) - len(failed)} of {len(TESTS)} tests pass")
    if failed:
        sys.exit(1)
    assert variant_is_the_round()
    print("the variant of the last round with no rule changed passes its tests")
    print("\nmutations, each must be caught:")
    survivors = []
    for m in MUTATIONS:
        restore()
        m()
        caught = run_all(quiet=True)
        restore()
        print(f"  {m.__name__:38s} caught by {len(caught)}: {', '.join(c[5:] for c in caught[:3])}")
        if not caught:
            survivors.append(m.__name__)
    print(f"\n{len(MUTATIONS) - len(survivors)} of {len(MUTATIONS)} mutations caught")
    if survivors:
        print("survivors:", survivors)
        sys.exit(1)
