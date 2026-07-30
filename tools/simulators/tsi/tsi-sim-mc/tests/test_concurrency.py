import numpy as np

from tsi_sim import concurrency
from tsi_sim.config import SimConfig


def test_window_counts_partitions_all_proposals():
    ws = np.array([0, 1, 2, 5, 5, 9], dtype=np.int64)
    counts = concurrency.window_counts(ws, epoch_len=10, bucket=5)
    assert counts.tolist() == [3, 3]          # slots 0-4 -> 3, slots 5-9 -> 3
    assert counts.sum() == ws.size


def test_window_counts_bucket_one_is_per_slot():
    ws = np.array([0, 0, 3], dtype=np.int64)
    counts = concurrency.window_counts(ws, epoch_len=4, bucket=1)
    assert counts.tolist() == [2, 0, 0, 1]    # slot 0 has 2 concurrent, slot 3 has 1


def test_window_counts_empty():
    assert concurrency.window_counts(np.empty(0, np.int64), 10, 2).tolist() == [0, 0, 0, 0, 0]


def test_concurrency_stats_scale_with_latency():
    # Bigger latency bucket => more proposals per bucket (max/mean grow roughly with L).
    small = concurrency.concurrency_stats(SimConfig(n_nodes=1000, latency=2, k=32, epochs=1))
    large = concurrency.concurrency_stats(SimConfig(n_nodes=1000, latency=20, k=32, epochs=1))
    assert large["mean"] > small["mean"]
    assert large["max"] >= small["max"]
    # mean per bucket ~ bucket * (-ln(1-f))
    expected = large["bucket"] * (-np.log(1 - 1 / 30))
    assert abs(large["mean"] - expected) < 0.25 * expected


def test_proposal_slots_reproducible_and_sorted():
    cfg = SimConfig(n_nodes=500, latency=4, k=16, epochs=1)
    a = concurrency.proposal_slots(cfg, replicate=0)
    b = concurrency.proposal_slots(cfg, replicate=0)
    np.testing.assert_array_equal(a, b)
    assert np.all(np.diff(a) >= 0)
