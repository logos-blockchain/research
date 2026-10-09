"""A network partition (config.partition_*): one side's blocks reach the other at the span's end."""

import numpy as np

from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask, _partition_mask
from tsi_sim.stake import make_stake
from tsi_sim.topology import _blend_arrival_column, arrival_column


def _config(**kw) -> SimConfig:
    base = dict(n_nodes=40, topology="full_mesh", k=16, epochs=1, f=1 / 30)
    base.update(kw)
    return SimConfig(**base)


def test_the_partition_enters_the_key_only_when_set():
    base = _config()
    assert _config(partition_share=0.0, partition_start=0, partition_slots=0).key() == base.key()
    assert _config(partition_share=0.3, partition_slots=100).key() != base.key()
    assert _config(partition_start=5).key() != base.key()
    assert _config(partition_slots=5).key() != base.key()


def test_one_side_holds_the_share_of_stake_asked_and_no_coalition_node():
    cfg = _config(n_nodes=200, stake_dist="pareto", adversary_frac=0.3, adversary_strategy="withhold",
                  partition_share=0.35, partition_start=10, partition_slots=100)
    stake = make_stake(cfg, np.random.default_rng(1))
    adv = _adversary_mask(cfg, stake)
    side = _partition_mask(cfg, stake, adv)
    share = stake[side].sum() / stake.sum()
    assert 0.35 <= share <= 0.35 + stake[side].max() / stake.sum()    # reaches the target by one node
    assert not np.any(side & adv)
    assert np.array_equal(side, _partition_mask(cfg, stake, adv))      # deterministic
    assert _partition_mask(_config(n_nodes=200), stake, None) is None


def test_an_arrival_across_the_cut_waits_for_the_span_to_end():
    n = 6
    path = np.full((n, n), 0.5)
    np.fill_diagonal(path, 0.0)
    cfg = _config(n_nodes=n, partition_share=0.5, partition_start=100, partition_slots=50)
    side = np.array([True, True, True, False, False, False])
    rng = np.random.default_rng(0)
    col = arrival_column(path, 0, 110, cfg, rng, None, side)
    assert np.allclose(col[1:3], 110.5) and np.allclose(col[3:], 150.5) and col[0] == 110.0
    col = arrival_column(path, 0, 90, cfg, rng, None, side)              # before the span
    assert np.allclose(col[1:], 90.5)
    col = arrival_column(path, 0, 160, cfg, rng, None, side)             # after it
    assert np.allclose(col[1:], 160.5)
    col = arrival_column(path, 0, 149, cfg, rng, None, side)             # the last cut slot
    assert np.allclose(col[1:3], 149.5) and np.allclose(col[3:], 150.5)
    same = arrival_column(path, 0, 110, _config(n_nodes=n), np.random.default_rng(0), None, None)
    assert np.allclose(same[1:], 110.5)


def test_a_blend_copy_through_a_relay_across_the_cut_is_lost():
    n = 40
    path = np.zeros((n, n))
    cfg = SimConfig(n_nodes=n, topology="blend", degree=6, blend_hops=3, blend_delay_max=3.0,
                    blend_delay_dist="rounds", k=16, epochs=1, f=1 / 30,
                    partition_share=0.1, partition_start=100, partition_slots=50)
    alone = np.zeros(n, dtype=bool)
    alone[0] = True                                          # the producer is cut off from every relay
    for seed in range(5):
        col = _blend_arrival_column(path, 0, 110, cfg, np.random.default_rng(seed), None, alone)
        assert np.all(col == 110 + 16.0)                     # every copy lost: the fallback
        col = arrival_column(path, 0, 110, cfg, np.random.default_rng(seed), None, alone)
        assert col[0] == 110.0 and np.all(col[1:] == 150.0)  # and across the cut, the span's end
    together = np.ones(n, dtype=bool)                        # every relay on the producer's side
    col = _blend_arrival_column(path, 0, 110, cfg, np.random.default_rng(3), None, together)
    assert 113.0 <= col[1] <= 119.0
