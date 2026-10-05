"""Gates for Phase A1 (src/finality_sim/baseline.py) and the engine's Blend delay option."""

import numpy as np
import pytest
from tsi_sim import fork, topology
from tsi_sim.config import SimConfig

from finality_sim.baseline import build_epoch, measure_epoch


def _blend(**kw):
    base = dict(n_nodes=200, topology="blend", degree=6, link_latency_dist="fixed",
                link_latency_mean=0.0, blend_hops=1, blend_delay_max=3.0, k=16, f=1 / 30,
                max_uncles=0, prune_arrival=False)
    base.update(kw)
    return SimConfig(**base)


def _hop_delays(config, n=400):
    pl = topology.build_path_latency(config, np.random.default_rng(1))
    rng = np.random.default_rng(2)
    out = []
    for i in range(n):
        col = topology.arrival_column(pl, producer=0, slot=10 * i, config=config, rng=rng)
        out.append(col[1:] - 10 * i)
    return np.concatenate(out)


def test_rounds_delays_are_whole_rounds_from_one_to_max():
    d = _hop_delays(_blend(blend_delay_dist="rounds"))
    assert set(np.unique(d)) == {1.0, 2.0, 3.0}


def test_continuous_delays_stay_continuous():
    d = _hop_delays(_blend())
    assert d.min() >= 0.0 and d.max() <= 3.0
    assert np.unique(d).size > 100


def test_rounds_rejects_fractional_max():
    with pytest.raises(ValueError):
        _blend(blend_delay_dist="rounds", blend_delay_max=2.5)


@pytest.mark.parametrize("tail", [0.1, 0.3])
def test_orphan_share_matches_engine_fork_rate(tail):
    """The A1 orphan share equals the engine's own fork rate on the same tree and window."""
    cfg = _blend(n_nodes=400, link_latency_dist="geo", link_latency_mean=0.5, blend_hops=3,
                 blend_delay_max=8.0, k=64)
    tree, arrival = build_epoch(cfg)
    m = measure_epoch(tree, arrival, cfg.epoch_len, tail=tail)
    cut = int(cfg.epoch_len * (1 - tail))
    fork_rate = fork.fork_stats(tree, arrival, T=cut, cutoff=cfg.epoch_len)[0]
    assert m.orphan_share == pytest.approx(fork_rate, abs=1e-12)


def test_depth_time_counts_canonical_successors():
    cfg = _blend(n_nodes=300, link_latency_dist="geo", link_latency_mean=0.5, blend_hops=3,
                 blend_delay_max=3.0, k=32)
    tree, arrival = build_epoch(cfg)
    m = measure_epoch(tree, arrival, cfg.epoch_len, depths=(1, 5))
    chain = np.asarray(tree.canonical_chain())[::-1]
    gaps = np.diff(tree.slot[chain]).astype(float)
    n1 = m.depth_chain[1].size
    np.testing.assert_array_equal(m.depth_chain[1], gaps[:n1])
    five = np.convolve(gaps, np.ones(5), mode="valid")[: m.depth_chain[5].size]
    np.testing.assert_allclose(m.depth_chain[5], five)
