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
