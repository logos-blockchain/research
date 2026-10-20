"""Hostile relays hold a block for the longest mixing delay (config.blend_adversary_relays)."""

import numpy as np
import pytest

from tsi_sim import lottery
from tsi_sim.blocktree import build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask
from tsi_sim.stake import make_stake
from tsi_sim.topology import DEADLINE_MARGIN, _blend_arrival_column, build_path_latency


def _config(**kw) -> SimConfig:
    return SimConfig(n_nodes=40, topology="blend", degree=6, blend_hops=3, blend_delay_max=3.0,
                     blend_delay_dist="rounds", k=16, epochs=1, f=1 / 30, **kw)


def test_hostile_relays_add_the_longest_delay_and_honest_ones_draw_theirs():
    n = 40
    path = np.zeros((n, n))                                  # no transport: only mixing delays remain
    all_adv = np.ones(n, dtype=bool)
    cfg = _config(blend_adversary_relays=True)
    for seed in range(5):
        col = _blend_arrival_column(path, 0, 100, cfg, np.random.default_rng(seed), all_adv)
        assert np.all(col == 100 + 3 * 3.0)                  # three relays, each the maximum
    none = np.zeros(n, dtype=bool)
    seen = {float(_blend_arrival_column(path, 0, 100, cfg, np.random.default_rng(s), none)[1])
            for s in range(200)}
    assert min(seen) >= 103.0 and max(seen) <= 109.0 and len(seen) > 3     # uniform draws on 1..3


def test_without_the_flag_the_mask_changes_nothing():
    n = 40
    path = np.zeros((n, n))
    all_adv = np.ones(n, dtype=bool)
    cfg = _config()
    for seed in range(5):
        a = _blend_arrival_column(path, 0, 100, cfg, np.random.default_rng(seed), all_adv)
        b = _blend_arrival_column(path, 0, 100, cfg, np.random.default_rng(seed), None)
        assert np.array_equal(a, b)
    assert cfg.key() == _config(blend_adversary_relays=False).key()
    assert _config(blend_adversary_relays=True).key() != cfg.key()


def test_dropping_relays_leave_the_block_to_the_senders_fallback():
    n = 40
    path = np.zeros((n, n))
    all_adv = np.ones(n, dtype=bool)
    for copies in (1, 2):
        cfg = _config(blend_adversary_relays=True, blend_adversary_action="drop", blend_copies=copies)
        for seed in range(5):
            col = _blend_arrival_column(path, 0, 100, cfg, np.random.default_rng(seed), all_adv)
            assert np.all(col == 100 + 1 + 15.0)          # released next round, lost after T_M
    cfg = _config(blend_adversary_relays=True, blend_adversary_action="drop", blend_fallback_slots=4.0)
    col = _blend_arrival_column(path, 0, 100, cfg, np.random.default_rng(1), all_adv)
    assert np.all(col == 105.0)
    # one hostile relay among forty: a copy survives when none of its three relays is hostile
    one = np.zeros(n, dtype=bool)
    one[7] = True
    cfg = _config(blend_adversary_relays=True, blend_adversary_action="drop")
    arrivals = [float(_blend_arrival_column(path, 0, 100, cfg, np.random.default_rng(s), one)[1])
                for s in range(300)]
    assert 103.0 <= min(arrivals) and max(arrivals) == 116.0 and 0 < arrivals.count(116.0) < 300


def test_two_copies_arrive_with_the_first_cascade():
    n = 40
    path = np.zeros((n, n))
    pool = np.delete(np.arange(n), 0)
    cfg = _config(blend_copies=2)
    for seed in range(20):
        rng = np.random.default_rng(seed)
        sums = []
        for _ in range(2):                                   # the same draws, in the same order
            rng.choice(pool, size=3, replace=False)
            sums.append(sum(int(rng.integers(1, 4)) for _ in range(3)))
        col = _blend_arrival_column(path, 0, 100, cfg, np.random.default_rng(seed), None)
        assert np.all(col == 100 + min(sums))


def test_the_new_knobs_enter_the_key_only_when_set():
    base = _config()
    assert _config(blend_copies=1, blend_fallback_slots=15.0, blend_adversary_action="hold").key() == base.key()
    assert _config(blend_copies=2).key() != base.key()
    assert _config(blend_fallback_slots=16.0).key() != base.key()
    hold = _config(blend_adversary_relays=True)
    drop = _config(blend_adversary_relays=True, blend_adversary_action="drop")
    assert hold.key() != drop.key() and hold.key() != base.key()
    assert _config(blend_adversary_action="drop").key() != base.key()   # non-default, so distinct


def test_the_cascade_starts_a_round_late_when_released_at_the_next_round():
    n = 40
    path = np.zeros((n, n))
    late = _config(blend_release_next_round=True)
    for seed in range(5):
        a = _blend_arrival_column(path, 0, 100, _config(), np.random.default_rng(seed), None)
        b = _blend_arrival_column(path, 0, 100, late, np.random.default_rng(seed), None)
        assert np.array_equal(b, a + 1.0)                    # the same draws, one round later
    all_adv = np.ones(n, dtype=bool)
    drop = _config(blend_release_next_round=True, blend_adversary_relays=True,
                   blend_adversary_action="drop")
    col = _blend_arrival_column(path, 0, 100, drop, np.random.default_rng(1), all_adv)
    assert np.all(col == 100 + 1 + 15.0)                     # the fallback's deadline does not move
    assert _config(blend_release_next_round=False).key() == _config().key()
    assert late.key() != _config().key()


def test_a_hostile_last_relay_holds_the_block_to_the_senders_deadline():
    n = 40
    path = np.full((n, n), 0.25)
    np.fill_diagonal(path, 0.0)
    deadline = _config(blend_adversary_relays=True, blend_adversary_action="deadline")
    all_adv = np.ones(n, dtype=bool)
    for seed in range(5):
        col = _blend_arrival_column(path, 0, 100, deadline, np.random.default_rng(seed), all_adv)
        assert col[0] == pytest.approx(100 + 1 + 15.0 - DEADLINE_MARGIN)   # the sender, just in time
        assert col.max() < 100 + 1 + 15.0
    third = np.zeros(n, dtype=bool)
    third[1::3] = True                                       # 13 of the 39 possible relays
    hold = _config(blend_adversary_relays=True)
    differ = 0
    for s in range(300):
        a = _blend_arrival_column(path, 0, 100, hold, np.random.default_rng(s), third)
        b = _blend_arrival_column(path, 0, 100, deadline, np.random.default_rng(s), third)
        assert np.all(b >= a)                                # the same draws, held no shorter
        if not np.array_equal(a, b):
            differ += 1
            assert b[0] == pytest.approx(100 + 1 + 15.0 - DEADLINE_MARGIN)
    assert 60 < differ < 140                                 # the last relay is hostile in a third
    assert deadline.key() != hold.key()


def _tree(windowed: bool, **kw):
    base = dict(n_nodes=150, topology="blend", degree=6, link_latency_dist="geo", link_latency_mean=0.1,
                blend_hops=3, blend_delay_max=3.0, blend_delay_dist="rounds", k=10, epochs=1, f=1 / 30,
                adversary_frac=0.3, adversary_strategy="suppress", prune_arrival=False, replicate=3)
    cfg = SimConfig(**{**base, **kw}, windowed_fork_choice=windowed)
    ch = np.random.SeedSequence(7).spawn(4)
    stake = make_stake(cfg, np.random.default_rng(ch[0]))
    mask = _adversary_mask(cfg, stake)
    path = build_path_latency(cfg, np.random.default_rng(ch[1]))
    p = lottery.win_probs(stake, np.full(cfg.n_nodes, float(stake.sum())), cfg.f)
    active, groups = lottery.group_by_slot(*lottery.sample_wins(p, cfg.epoch_len,
                                                                np.random.default_rng(ch[2])))
    return build_tree_pernode(active, groups, path, cfg, np.random.default_rng(ch[3]),
                              adversary_mask=mask)


@pytest.mark.parametrize("kw", [
    dict(blend_adversary_relays=True, blend_adversary_action="drop"),
    dict(blend_adversary_relays=True, blend_adversary_action="deadline"),
    # every pair adjacent at a fixed latency and one relay of one round: every block arrives at the
    # cascade's bound, so a horizon short of the release round's extra round is seen
    dict(blend_release_next_round=True, n_nodes=7, link_latency_dist="fixed", f=0.3, blend_hops=1,
         blend_delay_max=1.0),
])
def test_the_windowed_fork_choice_is_the_full_scan_in_every_relay_mode(kw):
    tw, aw = _tree(True, **kw)
    tf, af = _tree(False, **kw)
    assert tw.n_blocks > 50
    np.testing.assert_array_equal(tw.parent, tf.parent)
    np.testing.assert_array_equal(aw, af)
