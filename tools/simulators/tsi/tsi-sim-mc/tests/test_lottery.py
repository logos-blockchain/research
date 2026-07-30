import numpy as np

from tsi_sim import lottery


def test_phi_bounds():
    f = 1 / 30
    assert lottery.phi(f, 0.0) == 0.0
    # a single all-stake node (alpha=1) wins at exactly rate f
    assert abs(lottery.phi(f, 1.0) - f) < 1e-12


def test_win_probs_monotone_in_stake():
    stake = np.array([1.0, 2.0, 3.0])
    p = lottery.win_probs(stake, d_est=6.0, f=1 / 30)
    assert np.all(np.diff(p) > 0)


def test_sample_wins_sorted_and_rate():
    rng = np.random.default_rng(0)
    n, slots = 500, 4000
    p = np.full(n, 0.001)
    ws, wn = lottery.sample_wins(p, slots, rng, chunk=512)
    assert np.all(np.diff(ws) >= 0)                     # sorted by slot
    assert ws.shape == wn.shape
    assert np.all((wn >= 0) & (wn < n))
    # expected wins ~ n * slots * p
    assert abs(ws.size - n * slots * 0.001) < 4 * np.sqrt(n * slots * 0.001)


def test_group_by_slot():
    ws = np.array([0, 0, 2, 5, 5, 5])
    wn = np.array([3, 7, 1, 2, 4, 9])
    active, groups = lottery.group_by_slot(ws, wn)
    assert list(active) == [0, 2, 5]
    assert [g.tolist() for g in groups] == [[3, 7], [1], [2, 4, 9]]


def test_group_by_slot_empty():
    active, groups = lottery.group_by_slot(np.empty(0, int), np.empty(0, int))
    assert active.size == 0 and groups == []


def test_sparse_per_node_distinct_slots():
    # Each node wins any slot at most once (independent Bernoulli-per-slot invariant).
    rng = np.random.default_rng(1)
    p = np.full(300, 0.05)
    ws, wn = lottery.sample_wins(p, 2000, rng)
    for node in np.unique(wn):
        slots = ws[wn == node]
        assert slots.size == np.unique(slots).size       # no duplicate (node, slot)


def test_sparse_preserves_multiwinner_slots():
    # With high p, some slots have >1 distinct winner (guaranteed forks) — must be possible.
    rng = np.random.default_rng(2)
    p = np.full(50, 0.3)
    ws, _ = lottery.sample_wins(p, 500, rng)
    _, counts = np.unique(ws, return_counts=True)
    assert counts.max() >= 2


def test_chunked_matches_serial_distribution():
    # Chunked sampler is deterministic given (seedseq, n_chunks) and statistically matches
    # serial. NOTE: SeedSequence.spawn is stateful, so each call needs a FRESH SeedSequence.
    p = np.full(400, 0.02)
    a_s, a_n = lottery.sample_wins_chunked(p, 100000, np.random.SeedSequence(123), 4, n_jobs=1)
    b_s, b_n = lottery.sample_wins_chunked(p, 100000, np.random.SeedSequence(123), 4, n_jobs=1)
    np.testing.assert_array_equal(a_s, b_s)              # deterministic
    np.testing.assert_array_equal(a_n, b_n)
    assert np.all(np.diff(a_s) >= 0)                    # sorted
    for node in np.unique(a_n):                         # per-node distinct slots preserved
        s = a_s[a_n == node]
        assert s.size == np.unique(s).size
    serial_n = lottery.sample_wins(p, 100000, np.random.default_rng(7))[0].size
    assert abs(a_s.size - serial_n) < 6 * np.sqrt(serial_n)  # same rate

