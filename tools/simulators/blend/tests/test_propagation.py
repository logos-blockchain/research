import numpy as np

from blend.config import SimConfig
from blend.graph import Graph, build_graph
from blend.propagation import assign_responsive, blend_round, propagation_metrics
from blend.rng import responsive_seedseq, round_seedseq


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


# --- arrival times and messaging redundancy -----------------------------------------------------

def test_arrival_is_path_plus_flood_distance():
    """``arrival`` is the absolute per-node arrival time -- what is combined across cascades."""
    g = _k4([1.0, 2.0, 3.0, 4.0])
    r = blend_round(g, sender=0, relays=np.array([1]), jitter_mean_ms=0.0, max_blend_delay=0,
                    rng=np.random.default_rng(0), coverage_pcts=(50.0,))
    arr = r["arrival"]
    assert arr[1] == r["path"]                          # the flooding relay itself, at t = path
    assert float(np.nanmax(arr[np.isfinite(arr)])) == r["full"]   # last arrival == full delay
    assert np.all(arr[[0, 2, 3]] == r["path"] + 12.0)   # 10 ms link + p(1)=2 from the relay


def test_arrival_is_none_when_undelivered():
    g = _k4([0.0, 0.0, 0.0, 0.0])
    responsive = np.array([True, False, True, True])
    r = blend_round(g, 0, np.array([1]), 0.0, 0, np.random.default_rng(0), (50.0,), responsive)
    assert r["delivered"] is False and r["arrival"] is None


def test_stats_false_skips_summary_but_keeps_arrival():
    g = _k4([1.0, 2.0, 3.0, 4.0])
    kw = dict(jitter_mean_ms=0.0, max_blend_delay=0, coverage_pcts=(50.0, 90.0))
    full = blend_round(g, 0, np.array([1]), rng=np.random.default_rng(0), **kw)
    lean = blend_round(g, 0, np.array([1]), rng=np.random.default_rng(0), stats=False, **kw)
    assert "full" in full and "full" not in lean
    assert lean["path"] == full["path"]
    assert np.array_equal(lean["arrival"], full["arrival"])


def _prop(n_nodes, degree, u, blend_hops, R, n_rounds, seed=0):
    cfg = SimConfig(n_nodes=n_nodes, degree=degree, blend_hops=blend_hops, max_blend_delay=0,
                    transport_jitter_mean_ms=0.0, unresponsive_frac=u, redundancy=R,
                    n_rounds=n_rounds, graph_seed=seed)
    g = build_graph(cfg)
    resp = assign_responsive(n_nodes, u, np.random.default_rng(responsive_seedseq(cfg, u)))
    rng = np.random.default_rng(round_seedseq(cfg, blend_hops, 0, u, R))
    return propagation_metrics(g, blend_hops, 0, u, R, resp, cfg, rng)


def test_single_cascade_reduces_to_blend_round_stats():
    """R=1 aggregation over ``arrival`` must reproduce the per-cascade scalar summary exactly."""
    g = _k4([1.0, 2.0, 3.0, 4.0])
    pcts = (50.0, 90.0, 99.0)
    r = blend_round(g, 0, np.array([1]), 0.0, 0, np.random.default_rng(0), pcts)
    arr = r["arrival"]
    finite = np.isfinite(arr)
    reached = arr[finite]
    assert float(reached.max()) == r["full"]                        # full delay
    assert float(reached.max()) - r["path"] == r["broadcast"]       # broadcast phase
    rel = reached - r["path"]
    for pc, c in zip(pcts, r["covers"], strict=True):
        assert abs(float(np.percentile(rel, pc)) - c) < 1e-9        # coverage times
    assert float(finite.mean()) == r["frac_reached"]


def test_redundancy_raises_delivery_monotonically():
    rates = [_prop(2000, 4, 0.3, 3, R, 300)["delivery_rate"] for R in (1, 2, 3)]
    assert all(b >= a for a, b in zip(rates, rates[1:], strict=False))
    assert rates[2] > rates[0] + 0.1        # a real gain, not noise


def test_redundancy_buys_no_coverage_even_when_fragmented():
    """Redundancy raises *delivery*, never *coverage* -- including in the fragmented regime.

    A cascade is delivered only if the sender can route to its relay, so every delivered cascade's
    relay already lies in the sender's reachable set and floods (a subset of) the same component.
    The union over R cascades therefore cannot exceed what one delivered cascade already reaches.
    """
    for degree, u in ((3, 0.5), (8, 0.3)):          # fragmented, then connected
        single = _prop(4000, degree, u, 1, 1, 300)["frac_reached"]
        quad = _prop(4000, degree, u, 1, 4, 300)["frac_reached"]
        assert quad <= single + 0.01, (degree, u, single, quad)


def test_redundant_cascades_flood_the_same_component():
    """Direct check of the mechanism: with several cascades delivered in one round, the union of
    their reached sets equals the largest single one."""
    # u just below degree 3's percolation threshold (0.5): the graph is thinned and lossy, but
    # deliveries are still common enough that the multi-cascade case actually arises.
    n, u = 4000, 0.4
    cfg = SimConfig(n_nodes=n, degree=3, blend_hops=1, max_blend_delay=0,
                    transport_jitter_mean_ms=0.0, unresponsive_frac=u, graph_seed=0)
    g = build_graph(cfg)
    resp = assign_responsive(n, u, np.random.default_rng(responsive_seedseq(cfg, u)))
    rng = np.random.default_rng(5)
    resp_ids = np.where(resp)[0]
    checked = 0
    for _ in range(400):
        s = int(rng.choice(resp_ids))
        masks = []
        for _c in range(4):
            rel = rng.choice(n - 1, size=1, replace=False)
            rel[rel >= s] += 1
            rc = blend_round(g, s, rel, 0.0, 0, rng, (50.0,), resp, stats=False)
            if rc["delivered"]:
                masks.append(np.isfinite(rc["arrival"]))
        if len(masks) < 2:
            continue
        checked += 1
        union = np.logical_or.reduce(masks)
        assert int(union.sum()) == max(int(m.sum()) for m in masks)
    assert checked > 0                               # the multi-delivery case did occur


# --- regional (correlated) churn -----------------------------------------------------------------

def test_regional_churn_drops_whole_regions_and_matches_the_uniform_count():
    """Correlated churn kills failure domains, not scattered nodes -- at the same total count."""
    from blend.graph import region_of
    n, n_regions, u = 1000, 10, 0.3
    rng = np.random.default_rng(0)
    mask = assign_responsive(n, u, rng, "regional", n_regions)
    assert int((~mask).sum()) == 300                      # exactly the same quota as uniform
    region = region_of(n, n_regions)
    dead_per_region = [int((~mask[region == r]).sum()) for r in range(n_regions)]
    # every region is either wholly dead (100) or wholly alive (0), bar at most one trimmed region
    partial = [d for d in dead_per_region if 0 < d < 100]
    assert len(partial) <= 1
    assert sum(1 for d in dead_per_region if d == 100) == 3


def test_uniform_churn_scatters_across_all_regions():
    from blend.graph import region_of
    n, n_regions, u = 1000, 10, 0.3
    mask = assign_responsive(n, u, np.random.default_rng(0), "uniform", n_regions)
    region = region_of(n, n_regions)
    dead_per_region = [int((~mask[region == r]).sum()) for r in range(n_regions)]
    assert all(0 < d < 100 for d in dead_per_region)      # every region damaged, none wiped out


def test_region_locality_keeps_peers_inside_the_region_and_stays_d_regular():
    from blend.graph import build_graph, region_of
    n, n_regions, degree = 2000, 10, 8
    region = region_of(n, n_regions)
    for locality, want in ((0.0, 0.1), (0.5, 0.5), (1.0, 1.0)):
        cfg = SimConfig(n_nodes=n, degree=degree, n_regions=n_regions,
                        region_locality=locality, graph_seed=0)
        g = build_graph(cfg)
        assert np.all(np.diff(g.indptr) == degree)        # exact d-regularity is preserved
        same = float(np.mean(region[g.src] == region[g.indices]))
        assert abs(same - want) < 0.05, (locality, same)


def test_regional_churn_leaves_survivors_better_connected():
    """The point of the correlated model: clustered failure removes whole neighbourhoods and
    leaves the rest intact, so surviving nodes keep more live peers than under scattered failure."""
    from blend.graph import build_graph
    n, n_regions, degree, u = 4000, 20, 8, 0.4
    cfg = SimConfig(n_nodes=n, degree=degree, n_regions=n_regions, region_locality=0.75,
                    graph_seed=0)
    g = build_graph(cfg)
    live_degree = {}
    for mode in ("uniform", "regional"):
        mask = assign_responsive(n, u, np.random.default_rng(1), mode, n_regions)
        live_nbr = mask[g.indices]                        # is each peer alive?
        counts = np.add.reduceat(live_nbr.astype(np.int32), g.indptr[:-1])
        live_degree[mode] = float(counts[mask].mean())    # live peers of a surviving node
    assert live_degree["regional"] > live_degree["uniform"] + 0.5
