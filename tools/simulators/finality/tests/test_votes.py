"""Gates for the vote model of D6 (src/finality_sim/votes.py)."""

import numpy as np
import pytest
from tsi_sim.config import SimConfig

from finality_sim.baseline import build_epoch
from finality_sim.votes import certificate_times, local_tips, vote_targets


@pytest.fixture(scope="module")
def epoch():
    cfg = SimConfig(n_nodes=200, topology="blend", degree=6, link_latency_dist="geo",
                    link_latency_mean=0.1, blend_hops=3, blend_delay_max=3.0,
                    blend_delay_dist="rounds", k=32, f=1 / 30, max_uncles=0, prune_arrival=False)
    return build_epoch(cfg)


def test_tips_are_the_best_received_blocks(epoch):
    tree, arrival = epoch
    rank = list(zip(tree.height, -tree.slot, -np.arange(tree.slot.size)))
    for t in (500.0, 3000.0, 7000.0):
        tips = local_tips(tree, arrival, t)
        for i in range(0, 200, 7):
            got = tips[i]
            assert arrival[i, got] <= t
            held = np.nonzero(arrival[i] <= t)[0]
            assert rank[got] == max(rank[b] for b in held)


def test_every_node_ends_on_the_canonical_tip(epoch):
    tree, arrival = epoch
    tips = local_tips(tree, arrival, np.inf)
    assert np.all(tips == tree.canonical_chain()[0])


def test_target_is_the_latest_block_old_enough(epoch):
    tree, _ = epoch
    chain = np.asarray(tree.canonical_chain()[::-1])           # genesis side first
    tip = np.array([chain[-1]])
    for lag in (30, 60):
        for b in chain[5:40:5]:
            t = float(tree.slot[b] + lag)                       # b sits exactly lag slots back
            assert vote_targets(tree, tip, t, lag)[0] == b


def test_certificate_needs_the_quorum_on_one_block():
    arrival = np.array([[10.0, 1.0], [5.0, 2.0], [7.0, 3.0], [0.0, 50.0]])
    seats = np.array([2, 3, 4, 10])
    targets = np.array([5, 5, 5, 6])
    assert certificate_times(arrival, seats, targets, 7).tolist() == [0.0, 3.0]
    assert certificate_times(arrival, seats, targets, 9).tolist() == [0.0, 3.0]
    assert certificate_times(arrival, seats, targets, 10).tolist() == [0.0, 50.0]
    assert certificate_times(arrival[:3], seats[:3], targets[:3], 7).tolist() == [7.0, 3.0]
    assert np.isinf(certificate_times(arrival[:3], seats[:3], targets[:3], 10)).all()
