from pd.config import SimConfig
from pd.rng import (
    graph_seedseq,
    responsive_seedseq,
    rng_for,
    round_seedseq,
    seedseq_for,
)


def test_deterministic():
    c = SimConfig(n_nodes=1000, degree=8, graph_seed=3)
    assert seedseq_for(c).entropy == seedseq_for(c).entropy
    a = rng_for(c).integers(0, 10**9, size=5)
    b = rng_for(c).integers(0, 10**9, size=5)
    assert list(a) == list(b)


def test_graph_seed_is_topology_only():
    base = SimConfig(n_nodes=1000, degree=8, graph_seed=3, f_adv=0.0, blend_hops=2)
    same_topo = SimConfig(n_nodes=1000, degree=8, graph_seed=3, f_adv=0.4, blend_hops=5,
                          adversary_mode="worstcase_coverage", n_rounds=999)
    assert graph_seedseq(base).entropy == graph_seedseq(same_topo).entropy
    diff_topo = SimConfig(n_nodes=1000, degree=8, graph_seed=4)
    assert graph_seedseq(base).entropy != graph_seedseq(diff_topo).entropy


def test_responsive_seed_depends_on_frac_only():
    c = SimConfig(n_nodes=1000, degree=8, graph_seed=3)
    # fixed per (topology, unresponsive_frac); different frac -> different responsive draw
    assert responsive_seedseq(c, 0.1).entropy == responsive_seedseq(c, 0.1).entropy
    assert responsive_seedseq(c, 0.1).entropy != responsive_seedseq(c, 0.2).entropy


def test_round_seed_includes_unresponsive_frac():
    c = SimConfig(n_nodes=1000, degree=8, graph_seed=3)
    a = round_seedseq(c, blend_hops=3, max_blend_delay=3, unresponsive_frac=0.0)
    b = round_seedseq(c, blend_hops=3, max_blend_delay=3, unresponsive_frac=0.2)
    assert a.entropy != b.entropy
