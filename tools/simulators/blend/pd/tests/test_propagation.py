import numpy as np

from pd.graph import Graph
from pd.propagation import assign_responsive, blend_round


def _k4(p):
    """Complete graph on 4 nodes (degree 3), base latency 10 ms on every link, node lags `p`."""
    indptr = np.array([0, 3, 6, 9, 12], dtype=np.int64)
    indices = np.array([1, 2, 3, 0, 2, 3, 0, 1, 3, 0, 1, 2], dtype=np.int64)
    base = np.full(12, 10.0)
    src = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3], dtype=np.int64)
    return Graph(n=4, degree=3, indptr=indptr, indices=indices, base=base, src=src,
                 p=np.asarray(p, dtype=float))


def test_single_relay_delay_with_node_lags():
    # jitter=0, max_blend_delay=0. Directed edge (u->v) = base(10) + p(u).
    g = _k4([1.0, 2.0, 3.0, 4.0])
    rng = np.random.default_rng(0)
    r = blend_round(g, sender=0, relays=np.array([1]), jitter_mean_ms=0.0,
                    max_blend_delay=0, rng=rng, coverage_pcts=(50.0, 90.0, 99.0))
    # leg 0->1 = 10 + p(0) = 11 ; broadcast from 1 to farthest = 10 + p(1) = 12
    assert r["path"] == 11.0
    assert r["broadcast"] == 12.0
    assert r["full"] == 23.0
    assert r["frac_reached"] == 1.0


def test_two_relay_path_sums_legs():
    g = _k4([1.0, 2.0, 3.0, 4.0])
    rng = np.random.default_rng(0)
    r = blend_round(g, sender=0, relays=np.array([1, 2]), jitter_mean_ms=0.0,
                    max_blend_delay=0, rng=rng, coverage_pcts=(50.0,))
    # legs: 0->1 = 11, 1->2 = 10 + p(1) = 12  => path 23 ; broadcast from 2 = 10 + p(2) = 13
    assert r["path"] == 23.0
    assert r["broadcast"] == 13.0
    assert r["full"] == 36.0


def test_mixing_adds_positive_delay():
    g = _k4([0.0, 0.0, 0.0, 0.0])
    rng = np.random.default_rng(1)
    no_mix = blend_round(g, 0, np.array([1]), 0.0, 0, rng, (50.0,))["full"]
    mixed = np.mean([blend_round(g, 0, np.array([1]), 0.0, 5, rng, (50.0,))["full"]
                     for _ in range(500)])
    assert mixed > no_mix  # the free-running clock adds a positive mixing residual


def _path4():
    """Line graph 0-1-2-3 (base 10 ms each way, no node lags)."""
    indptr = np.array([0, 1, 3, 5, 6], dtype=np.int64)
    indices = np.array([1, 0, 2, 1, 3, 2], dtype=np.int64)
    base = np.full(6, 10.0)
    src = np.array([0, 1, 1, 2, 2, 3], dtype=np.int64)
    return Graph(n=4, degree=2, indptr=indptr, indices=indices, base=base, src=src,
                 p=np.zeros(4))


def test_assign_responsive_count_and_edges():
    rng = np.random.default_rng(0)
    mask = assign_responsive(1000, 0.3, rng)
    assert mask.dtype == bool
    assert int(mask.sum()) == 700                      # exactly 30% dropped
    assert assign_responsive(1000, 0.0, rng).all()     # frac 0 -> everyone responsive


def test_unresponsive_final_relay_drops_message():
    # final relay (node 1) unresponsive -> it receives but cannot flood: not delivered.
    g = _k4([0.0, 0.0, 0.0, 0.0])
    responsive = np.array([True, False, True, True])
    r = blend_round(g, sender=0, relays=np.array([1]), jitter_mean_ms=0.0, max_blend_delay=0,
                    rng=np.random.default_rng(0), coverage_pcts=(50.0,), responsive=responsive)
    assert r["delivered"] is False
    assert np.isnan(r["full"])


def test_unresponsive_intermediate_relay_drops_message():
    # first relay (node 1) unresponsive -> the second leg 1->2 is inf: not delivered.
    g = _k4([0.0, 0.0, 0.0, 0.0])
    responsive = np.array([True, False, True, True])
    r = blend_round(g, sender=0, relays=np.array([1, 2]), jitter_mean_ms=0.0, max_blend_delay=0,
                    rng=np.random.default_rng(0), coverage_pcts=(50.0,), responsive=responsive)
    assert r["delivered"] is False


def test_unresponsive_node_strands_flood_pocket():
    # path 0-1-2-3; relay 1 is responsive so the message is delivered, but node 2 is a routing hole
    # so node 3 (only reachable through 2) never receives the flood.
    g = _path4()
    responsive = np.array([True, True, False, True])
    r = blend_round(g, sender=0, relays=np.array([1]), jitter_mean_ms=0.0, max_blend_delay=0,
                    rng=np.random.default_rng(0), coverage_pcts=(50.0,), responsive=responsive)
    assert r["delivered"] is True
    assert r["frac_reached"] == 0.75                   # node 3 stranded behind unresponsive node 2
