from itertools import combinations

import numpy as np

from pd.adversary import _greedy_coverage, adversary_metrics, place_adversary
from pd.config import SimConfig
from pd.graph import Graph, build_graph


def _cycle4():
    indptr = np.array([0, 2, 4, 6, 8], dtype=np.int64)
    indices = np.array([1, 3, 0, 2, 1, 3, 0, 2], dtype=np.int64)
    return Graph(n=4, degree=2, indptr=indptr, indices=indices,
                 base=np.ones(8), src=np.array([0, 0, 1, 1, 2, 2, 3, 3]), p=np.zeros(4))


def test_coverage_eclipse_hand_checked():
    g = _cycle4()  # 0-1-2-3-0
    m = adversary_metrics(g, np.array([False, True, False, True]))  # adv {1,3}
    assert m["observed_count"] == 2 and m["eclipsed_count"] == 2   # honest {0,2} fully surrounded
    m = adversary_metrics(g, np.array([False, True, False, False]))  # adv {1}
    assert m["observed_count"] == 2 and m["eclipsed_count"] == 0    # {0,2} observed, none eclipsed


def test_random_closed_form():
    g = build_graph(SimConfig(n_nodes=5000, degree=6, graph_seed=0))
    rng = np.random.default_rng(0)
    def _obs():
        return adversary_metrics(g, place_adversary(g, 0.2, "random", rng, 10**9))["observed_frac"]
    obs = np.mean([_obs() for _ in range(5)])
    assert abs(obs - (1 - 0.8 ** 6)) < 0.02


def test_worstcase_coverage_is_an_envelope():
    g = build_graph(SimConfig(n_nodes=400, degree=4, graph_seed=0))
    rng = np.random.default_rng(0)
    rand = adversary_metrics(g, place_adversary(g, 0.2, "random", rng, 10**9))["observed_frac"]
    wc = adversary_metrics(
        g, place_adversary(g, 0.2, "worstcase_coverage", rng, 10**9))["observed_frac"]
    assert wc >= rand - 1e-9


def test_greedy_coverage_near_optimal():
    g = build_graph(SimConfig(n_nodes=10, degree=3, graph_seed=0))
    best = max(adversary_metrics(g, _mask(10, c))["observed_count"]
               for c in combinations(range(10), 2))
    idx = _greedy_coverage(g, 2, np.random.default_rng(0))
    got = adversary_metrics(g, _mask(10, idx))["observed_count"]
    assert got >= (1 - 1 / np.e) * best - 1e-9


def _mask(n, idx):
    m = np.zeros(n, dtype=bool)
    m[list(idx)] = True
    return m


def test_worstcase_cap_raises():
    import pytest
    g = build_graph(SimConfig(n_nodes=200, degree=4))
    with pytest.raises(ValueError):
        place_adversary(g, 0.2, "worstcase_coverage", np.random.default_rng(0), worstcase_max_n=100)
