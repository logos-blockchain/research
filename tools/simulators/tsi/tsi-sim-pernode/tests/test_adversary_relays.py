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
