import numpy as np

from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory
from tsi_sim.rng import rng_for, seedseq_for


def test_seedseq_and_rng_deterministic():
    cfg = SimConfig(k=8, epochs=3)
    a = np.random.default_rng(seedseq_for(cfg)).random(5)
    b = rng_for(cfg).random(5)
    np.testing.assert_array_equal(a, b)


def test_distinct_configs_get_distinct_streams():
    c0 = SimConfig(k=8, epochs=3, latency=0)
    c1 = SimConfig(k=8, epochs=3, latency=1)
    assert not np.array_equal(rng_for(c0).random(4), rng_for(c1).random(4))


def test_trajectory_is_order_independent_and_reproducible():
    cfg = SimConfig(n_nodes=300, topology="regular", degree=8, k=8, epochs=6,
                    link_latency_mean=2.0, max_uncles=2)
    r1 = run_trajectory(cfg)
    r2 = run_trajectory(cfg)
    assert [row["mean_ratio"] for row in r1] == [row["mean_ratio"] for row in r2]


def test_replicates_differ():
    a = run_trajectory(SimConfig(n_nodes=300, topology="regular", k=8, epochs=6,
                                 link_latency_mean=2.0, replicate=0))
    b = run_trajectory(SimConfig(n_nodes=300, topology="regular", k=8, epochs=6,
                                 link_latency_mean=2.0, replicate=1))
    assert a[-1]["mean_ratio"] != b[-1]["mean_ratio"]


def test_paired_streams_shares_the_root_across_uncle_models():
    """Common random numbers: with paired_streams the two arms draw the SAME root seed."""
    from tsi_sim.rng import seedseq_for

    kw = dict(n_nodes=50, max_uncles=2, blend_delay_max=5.0, topology="blend",
              k=32, epochs=2, replicate=3, paired_streams=True)
    c = SimConfig(uncle_model="countable", **kw)
    o = SimConfig(uncle_model="old", **kw)
    assert c.seed_key() == o.seed_key()             # the marker is dropped
    assert c.key() != o.key()                       # ...but identity still distinguishes them
    assert seedseq_for(c).entropy == seedseq_for(o).entropy


def test_unpaired_is_the_default_and_separates_the_models():
    kw = dict(n_nodes=50, max_uncles=2, blend_delay_max=5.0, topology="blend",
              k=32, epochs=2, replicate=3)
    c, o = SimConfig(uncle_model="countable", **kw), SimConfig(uncle_model="old", **kw)
    assert c.paired_streams is False and o.paired_streams is False
    assert c.seed_key() == c.key() and o.seed_key() == o.key()
    assert seedseq_for(c).entropy != seedseq_for(o).entropy


def test_paired_streams_does_not_perturb_unpaired_seeds():
    """The flag must not enter key(): every historical seed stays byte-identical.

    This is what protects --old bit-reproduction of the pre-redesign runs (report §9).
    """
    from tsi_sim.rng import seedseq_for

    for model in ("countable", "old"):
        base = SimConfig(uncle_model=model, n_nodes=50, max_uncles=2, k=32, epochs=2)
        flagged = SimConfig(uncle_model=model, n_nodes=50, max_uncles=2, k=32, epochs=2,
                            paired_streams=False)
        assert base.key() == flagged.key()
        assert seedseq_for(base).entropy == seedseq_for(flagged).entropy
    # and the old model's key is still exactly the base tuple (no marker appended)
    o = SimConfig(uncle_model="old", n_nodes=50, k=32, epochs=2)
    assert o.key() == o._base_key()


def test_paired_streams_gives_both_arms_the_same_stake_and_graph():
    """Pairing must reach the actual shared inputs, not just the root seed."""
    import numpy as np

    from tsi_sim import topology
    from tsi_sim.rng import seedseq_for
    from tsi_sim.stake import make_stake

    kw = dict(n_nodes=60, degree=4, topology="blend", max_uncles=2, k=32, epochs=2,
              blend_delay_max=5.0, replicate=1)
    c = SimConfig(uncle_model="countable", paired_streams=True, **kw)
    o = SimConfig(uncle_model="old", paired_streams=True, **kw)
    kids = {n: seedseq_for(cfg).spawn(cfg.epochs + 3)
            for n, cfg in (("c", c), ("o", o))}
    s_c = make_stake(c, np.random.default_rng(kids["c"][0]))
    s_o = make_stake(o, np.random.default_rng(kids["o"][0]))
    np.testing.assert_array_equal(s_c, s_o)                      # same stake draw
    g_c = topology.build_path_latency(c, np.random.default_rng(kids["c"][1]))
    g_o = topology.build_path_latency(o, np.random.default_rng(kids["o"][1]))
    np.testing.assert_array_equal(g_c, g_o)                      # same peering graph


def test_paired_streams_is_recorded_in_the_output_row():
    """A paired run must be identifiable from its parquet alone.

    scripts/plot_fine_delay.py picks the paired test only when both arms report
    paired_streams; if the flag were missing from the recorded config it would silently fall
    back to the unpaired test and quietly discard the whole point of the paired sweep.
    """
    from tsi_sim.metrics import _CONFIG_FIELDS

    assert "paired_streams" in _CONFIG_FIELDS


def test_whale_selection_does_not_perturb_random_coalition_seeds():
    """A default ("random") coalition's key must stay byte-identical to every historical run's.

    Same protection as test_paired_streams_does_not_perturb_unpaired_seeds gives the uncle model:
    the marker is appended only when non-default, so adding the knob rewrites no existing seed.
    """
    from tsi_sim.rng import seedseq_for

    for model in ("countable", "old"):
        base = SimConfig(uncle_model=model, n_nodes=50, k=32, epochs=2, adversary_frac=0.3)
        explicit = SimConfig(uncle_model=model, n_nodes=50, k=32, epochs=2, adversary_frac=0.3,
                             adversary_selection="random")
        assert base.key() == explicit.key()
        assert seedseq_for(base).entropy == seedseq_for(explicit).entropy
    o = SimConfig(uncle_model="old", n_nodes=50, k=32, epochs=2, adversary_frac=0.3)
    assert o.key() == o._base_key()                    # still exactly the historical tuple
    whale = SimConfig(uncle_model="old", n_nodes=50, k=32, epochs=2, adversary_frac=0.3,
                      adversary_selection="whale")
    assert whale.key() != o.key()                      # ...but the whale arm is its own stream


def test_whale_coalition_takes_the_largest_holders_at_the_same_stake():
    from tsi_sim.engine import _adversary_mask
    from tsi_sim.stake import make_stake

    cfg_r = SimConfig(n_nodes=400, stake_dist="pareto", k=32, epochs=2, adversary_frac=0.3)
    cfg_w = SimConfig(n_nodes=400, stake_dist="pareto", k=32, epochs=2, adversary_frac=0.3,
                      adversary_selection="whale")
    stake = make_stake(cfg_r, rng_for(cfg_r))
    m_r, m_w = _adversary_mask(cfg_r, stake), _adversary_mask(cfg_w, stake)
    total = stake.sum()
    # The point of the knob is concentration at MATCHED stake, so the realised shares must agree
    # closely — a whale arm holding visibly more stake would confound the two.
    assert abs(stake[m_r].sum() / total - 0.3) < 0.01
    assert abs(stake[m_w].sum() / total - 0.3) < 0.01
    # ...and the whales get there with far fewer nodes: that is the variable under test.
    assert m_w.sum() * 5 < m_r.sum()
    # The coalition is drawn from the top of the distribution and dominated by it: the biggest
    # holders are all in, and the small top-up nodes contribute almost none of its stake.
    top3 = np.argsort(-stake)[:3]
    assert m_w[top3].all()
    assert stake[top3].sum() / stake[m_w].sum() > 0.9
