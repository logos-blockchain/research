"""Gates for Areon-Base's DAG and the private attack on it (src/finality_sim/areon.py)."""

import numpy as np
import pytest
from tsi_sim.config import SimConfig

from finality_sim.areon import Dag, build_dag, dag_race, race_weights
from finality_sim.race import race


def _cfg(**kw):
    base = dict(n_nodes=200, topology="blend", degree=6, link_latency_dist="geo",
                link_latency_mean=0.1, blend_hops=3, blend_delay_max=3.0,
                blend_delay_dist="rounds", k=64, f=0.25, max_uncles=0, prune_arrival=False,
                stake_dist="uniform")
    base.update(kw)
    return SimConfig(**base)


@pytest.fixture(scope="module")
def dag():
    return build_dag(_cfg(), window=30, keep_arrival=True)


def test_honest_blocks_reference_the_tips_they_see(dag):
    refs = [dag.refs[dag.ref_ptr[b]:dag.ref_ptr[b + 1]] for b in range(dag.n_blocks)]
    checked = 0
    for b in range(50, dag.n_blocks, 11):
        t, v = dag.slot[b], dag.producer[b]
        held = [x for x in range(1, b) if dag.slot[x] < t and dag.arrival[v, x] <= t]
        window = [x for x in held if dag.slot[x] >= t - 30]
        if not window:
            continue
        children = {q for x in window for q in refs[x].tolist()}
        tips = sorted(x for x in window if x not in children)
        assert refs[b].tolist() == tips
        checked += 1
    assert checked > 20


def test_heights_and_arrivals_follow_the_parents(dag):
    for b in range(1, dag.n_blocks):
        parents = dag.refs[dag.ref_ptr[b]:dag.ref_ptr[b + 1]]
        assert dag.height[b] == dag.height[parents].max() + 1
        assert np.all(dag.arrival[:, b] >= dag.arrival[:, parents].max(axis=1))
        assert np.all(dag.slot[parents] < dag.slot[b])


def test_without_delay_a_block_references_the_last_occupied_slot():
    d = build_dag(_cfg(topology="full_mesh", latency=0.0), window=30)
    for b in range(2, d.n_blocks):
        parents = d.refs[d.ref_ptr[b]:d.ref_ptr[b + 1]]
        earlier = d.slot[:b][d.slot[:b] < d.slot[b]]
        last = earlier.max()
        if d.slot[b] - last > 30:
            continue
        assert sorted(parents.tolist()) == np.nonzero(d.slot[:b] == last)[0].tolist()


def test_a_full_mesh_delivers_every_block_after_its_latency():
    d = build_dag(_cfg(topology="full_mesh", latency=7.0), window=30, keep_arrival=True)
    late = d.arrival[:, 1:] - d.slot[1:][None, :]
    own = d.producer[1:][None, :] == np.arange(d.arrival.shape[0])[:, None]
    assert np.all(late[own] == 0) and np.all(late[~own] == 7.0)


def _chain(n_slots, p_h, p_a, seed):
    rng = np.random.default_rng(seed)
    hs = np.nonzero(rng.random(n_slots) < p_h)[0].astype(np.int64)
    adv = np.nonzero(rng.random(n_slots) < p_a)[0].astype(np.int64)
    n = hs.size + 1
    slot = np.concatenate(([-1], hs))
    refs = np.arange(n - 1, dtype=np.int64)                 # block b references b - 1
    ref_ptr = np.concatenate(([0, 0], np.arange(1, n, dtype=np.int64)))
    return Dag(slot=slot, height=np.arange(n, dtype=np.int64), producer=np.zeros(n, np.int64),
               ref_ptr=ref_ptr, refs=refs, long_ref=np.zeros(n, dtype=bool), adv_slots=adv,
               tips_seen=np.ones(n, np.int64)), hs, adv


@pytest.mark.parametrize("premine,win_at", [(True, 1), (False, 0)])
def test_race_on_a_chain_is_the_chain_race(premine, win_at):
    d, hs, adv = _chain(200_000, 0.03, 0.012, 3)
    got, n_got = dag_race(d, 12, window=10**9, premine=premine, win_at=win_at,
                          last=hs.size - 12)
    ref, n_ref = race(hs, adv, 12, premine=premine, win_at=win_at)
    assert n_got == n_ref
    assert got.tolist() == ref.tolist()


def test_recent_window_scores_only_the_last_w_slots():
    """Honest blocks every 10 slots; the coalition wins slots 201-203 only. Against the block at
    slot 150, three wins outweigh the single honest block of any 10-slot window that holds them,
    up to depth 6 (slot 210), and never once the whole race counts."""
    hs = np.arange(10, 310, 10, dtype=np.int64)
    n = hs.size + 1
    d = Dag(slot=np.concatenate(([-1], hs)), height=np.arange(n, dtype=np.int64),
            producer=np.zeros(n, np.int64),
            ref_ptr=np.concatenate(([0, 0], np.arange(1, n, dtype=np.int64))),
            refs=np.arange(n - 1, dtype=np.int64), long_ref=np.zeros(n, dtype=bool),
            adv_slots=np.array([201, 202, 203], np.int64), tips_seen=np.ones(n, np.int64))
    recent, _ = dag_race(d, 10, window=30, premine=False, recent=10, first=15, last=16)
    whole, _ = dag_race(d, 10, window=30, premine=False, first=15, last=16)
    assert recent.tolist() == [1, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    assert whole.tolist() == [0] * 10


def test_blocks_without_a_short_reference_weigh_nothing():
    d, _, _ = _chain(2000, 0.03, 0.02, 5)
    d.long_ref[3] = True
    weight, _ = race_weights(d)
    assert weight[0] == 0 and weight[3] == 0 and weight[1:3].tolist() == [1, 1]
    # an honest chain of long references never gains weight, so a single win displaces anything
    long_only = Dag(**{**d.__dict__, "long_ref": np.ones(d.n_blocks, dtype=bool),
                       "adv_slots": np.array([5], np.int64)})
    succ, scored = dag_race(long_only, 5, window=30, premine=True, first=1, last=10)
    assert scored > 0 and succ.tolist() == [scored] * 5


@pytest.mark.parametrize("premine", [False, True])
def test_a_win_weighs_one_within_the_window_of_its_side(premine):
    """Honest blocks every 10 slots; the target at slot 100, its parent at 90; window 2. The
    coalition wins slots 5, 92 and 94. The latest block on its side at slot 92 is the fork point
    at 90, or, premining with no lead, the public tip at 90; both wins lie exactly the window after
    a block on that side, so both weigh one and tie the target's child at 110. Weighed from the win
    at 5, the first would weigh nothing."""
    hs = np.arange(10, 310, 10, dtype=np.int64)
    n = hs.size + 1
    d = Dag(slot=np.concatenate(([-1], hs)), height=np.arange(n, dtype=np.int64),
            producer=np.zeros(n, np.int64),
            ref_ptr=np.concatenate(([0, 0], np.arange(1, n, dtype=np.int64))),
            refs=np.arange(n - 1, dtype=np.int64), long_ref=np.zeros(n, dtype=bool),
            adv_slots=np.array([5, 92, 94], np.int64), tips_seen=np.ones(n, np.int64))
    succ, scored = dag_race(d, 1, window=2, premine=premine, win_at=0, first=10, last=11)
    assert scored == 1 and succ.tolist() == [1]


def test_concurrent_honest_blocks_can_be_left_out():
    """Two honest branches: block 2 (slot 20) does not descend from the target, block 1 (slot 10);
    block 3 (slot 30) descends from both. One coalition win at slot 25 ties the target's own
    descendants (blocks 1 and 3 against 1 + 1) only when block 2 counts for neither side."""
    slot = np.array([-1, 10, 20, 30, 40, 50], np.int64)
    refs = [[], [0], [0], [1, 2], [3], [4]]
    ref_ptr = np.concatenate(([0], np.cumsum([len(r) for r in refs]))).astype(np.int64)
    d = Dag(slot=slot, height=np.array([0, 1, 1, 2, 3, 4], np.int64),
            producer=np.zeros(6, np.int64), ref_ptr=ref_ptr,
            refs=np.array([x for r in refs for x in r], np.int64),
            long_ref=np.zeros(6, dtype=bool), adv_slots=np.array([5, 25], np.int64),
            tips_seen=np.ones(6, np.int64))
    all_count, _ = dag_race(d, 1, window=100, premine=True, win_at=0, first=1, last=2)
    descendants, _ = dag_race(d, 1, window=100, premine=True, win_at=0, first=1, last=2,
                              descendants_only=True)
    assert all_count.tolist() == [0] and descendants.tolist() == [1]
