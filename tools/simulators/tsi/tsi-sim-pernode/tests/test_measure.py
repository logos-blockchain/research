"""The optimised measurement must be bit-identical to the naive per-node reference."""

from collections import Counter

import numpy as np
import pytest

from tsi_sim import lottery, topology, tsi
from tsi_sim.blocktree import build_tree_pernode, tips_for_all_nodes
from tsi_sim.config import SimConfig
from tsi_sim.measure import measure


def _build(cfg, rep=0):
    root = np.random.SeedSequence(abs(hash((cfg.key(), rep))) % (2**63))
    ch = root.spawn(4)
    stake = np.ones(cfg.n_nodes) * (cfg.total_stake / cfg.n_nodes)
    pl = topology.build_path_latency(cfg, np.random.default_rng(ch[1]))
    d = np.full(cfg.n_nodes, cfg.genesis_d_factor * cfg.total_stake)
    ws, wn = lottery.sample_wins(lottery.win_probs(stake, d, cfg.f), cfg.epoch_len,
                                 np.random.default_rng(ch[2]))
    active, groups = lottery.group_by_slot(ws, wn)
    tree, A = build_tree_pernode(active, groups, pl, cfg, np.random.default_rng(ch[3]))
    return tree, A, active


def _reference(tree, A, active_slots, T, cutoff):
    """Original naive per-node measurement (the ground truth)."""
    tips = tips_for_all_nodes(tree, A, cutoff)   # A may be a full matrix or a pruned SlidingArrival
    n = tips.shape[0]
    n_real = tree.n_blocks - 1
    m = np.empty(n, np.int64)
    q = np.empty(n)
    qe = np.empty(n)
    orp = np.empty(n)
    fps = []
    for i in range(n):
        canon = tree.ancestors(int(tips[i]))
        m[i] = tsi.density_m(tree, canon, T)
        ss = tsi.slot_stats(tree, canon, tsi.referenced_uncle_ids(tree, canon), active_slots, T)
        q[i], qe[i] = ss.q, ss.q_eff
        orp[i] = (n_real - len(canon)) / n_real if n_real else 0.0
        fps.append(tuple(sorted(b for b in canon if 0 <= tree.slot[b] < T)))
    aw = Counter(fps).most_common(1)[0][1] / n
    at = Counter(tips.tolist()).most_common(1)[0][1] / n
    return m, q, qe, orp, aw, at


@pytest.mark.parametrize("kw", [
    dict(topology="full_mesh", latency=0, max_uncles=0),
    dict(topology="full_mesh", latency=4, max_uncles=2),
    dict(topology="regular", degree=6, link_latency_mean=3.0, max_uncles=4),
    dict(topology="regular", degree=2, link_latency_mean=6.0, max_uncles=2),  # low agreement
    dict(topology="regular", degree=8, link_latency_mean=1.0, max_uncles=0),
])
def test_measure_matches_reference(kw):
    cfg = SimConfig(n_nodes=150, k=10, **kw)
    tree, A, active = _build(cfg)
    T, E = cfg.period_T, cfg.epoch_len
    ref_m, ref_q, ref_qe, ref_orp, ref_aw, ref_at = _reference(tree, A, active, T, E)
    got = measure(tree, A, active, T, E)

    np.testing.assert_array_equal(got.m, ref_m)
    np.testing.assert_allclose(got.q, ref_q, equal_nan=True)
    np.testing.assert_allclose(got.q_eff, ref_qe, equal_nan=True)
    np.testing.assert_allclose(got.orphan_rate, ref_orp)
    assert got.agreement_window == pytest.approx(ref_aw)
    assert got.agreement_tip == pytest.approx(ref_at)


def test_numba_and_python_kernels_agree():
    cfg = SimConfig(n_nodes=150, topology="regular", degree=4, link_latency_mean=4.0,
                    max_uncles=3, k=10)
    tree, A, active = _build(cfg)
    a = measure(tree, A, active, cfg.period_T, cfg.epoch_len, use_numba=True)
    b = measure(tree, A, active, cfg.period_T, cfg.epoch_len, use_numba=False)
    np.testing.assert_array_equal(a.m, b.m)
    np.testing.assert_allclose(a.q_eff, b.q_eff, equal_nan=True)
    assert a.agreement_window == b.agreement_window
