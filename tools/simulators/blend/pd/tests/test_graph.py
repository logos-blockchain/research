import numpy as np
import pytest

from pd.config import SimConfig
from pd.graph import build_graph, build_regular_edges


@pytest.mark.parametrize("n,degree", [(10, 1), (10, 2), (10, 3), (100, 4), (100, 7),
                                      (1000, 8), (500, 16), (256, 15)])
def test_exactly_d_regular_simple_undirected(n, degree):
    rng = np.random.default_rng(0)
    edges = build_regular_edges(n, degree, rng)
    deg = np.bincount(edges.ravel(), minlength=n)
    assert np.all(deg == degree), "every node must have exactly `degree` peers"
    assert np.all(edges[:, 0] < edges[:, 1]), "no self-loops; canonical u<v"
    # no duplicate undirected edges
    keys = edges[:, 0] * n + edges[:, 1]
    assert len(np.unique(keys)) == len(keys), "graph must be simple"
    assert edges.shape[0] == n * degree // 2


def test_graph_symmetric_and_connected():
    g = build_graph(SimConfig(n_nodes=2000, degree=6))
    assert np.all(np.diff(g.indptr) == g.degree)
    csr = g.weighted_csr(np.ones_like(g.base))
    assert (csr != csr.T).nnz == 0, "adjacency must be symmetric"
    from scipy.sparse.csgraph import connected_components
    ncomp, _ = connected_components(csr, directed=False)
    assert ncomp == 1, "degree>=3 random d-regular should be connected"


def test_reconstructible_from_seed():
    a = build_graph(SimConfig(n_nodes=1000, degree=8, graph_seed=7))
    b = build_graph(SimConfig(n_nodes=1000, degree=8, graph_seed=7))
    assert np.array_equal(a.indptr, b.indptr)
    assert np.array_equal(a.indices, b.indices)
    assert np.array_equal(a.base, b.base)
    assert np.array_equal(a.p, b.p)
    c = build_graph(SimConfig(n_nodes=1000, degree=8, graph_seed=8))
    assert not np.array_equal(a.indices, c.indices), "different seed -> different topology"


def test_topology_invariant_to_adversary_and_blend_fields():
    a = build_graph(SimConfig(n_nodes=800, degree=6, graph_seed=1, f_adv=0.0, blend_hops=2))
    b = build_graph(SimConfig(n_nodes=800, degree=6, graph_seed=1, f_adv=0.4,
                              blend_hops=5, adversary_mode="worstcase_coverage"))
    assert np.array_equal(a.indices, b.indices)
    assert np.array_equal(a.p, b.p)


def test_processing_lags_follow_distribution():
    g = build_graph(SimConfig(n_nodes=20000, degree=6,
                              processing_lags_ms=(10.0, 50.0, 100.0),
                              processing_lag_probs=(0.5, 0.4, 0.1)))
    for lag, prob in zip((10.0, 50.0, 100.0), (0.5, 0.4, 0.1), strict=True):
        frac = np.mean(g.p == lag)
        assert abs(frac - prob) < 0.03, f"lag {lag}: {frac:.3f} vs {prob}"
