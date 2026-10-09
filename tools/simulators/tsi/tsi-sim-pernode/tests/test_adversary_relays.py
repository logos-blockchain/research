"""Hostile relays hold a block for the longest mixing delay (config.blend_adversary_relays)."""

import numpy as np

from tsi_sim.config import SimConfig
from tsi_sim.topology import _blend_arrival_column


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
