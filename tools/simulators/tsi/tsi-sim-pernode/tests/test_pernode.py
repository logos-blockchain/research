import numpy as np
import pandas as pd
import pytest

from tsi_sim import constants, lottery, topology, tsi
from tsi_sim.blocktree import GENESIS, build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.engine import run_trajectory


def _build(cfg, replicate=0):
    """Build one epoch's (tree, A, path_latency) for a config."""
    root = np.random.SeedSequence(abs(hash((cfg.key(), replicate))) % (2**63))
    ch = root.spawn(4)
    stake = np.ones(cfg.n_nodes) * (cfg.total_stake / cfg.n_nodes)
    pl = topology.build_path_latency(cfg, np.random.default_rng(ch[1]))
    d = np.full(cfg.n_nodes, cfg.genesis_d_factor * cfg.total_stake)
    p = lottery.win_probs(stake, d, cfg.f)
    ws, wn = lottery.sample_wins(p, cfg.epoch_len, np.random.default_rng(ch[2]))
    active, groups = lottery.group_by_slot(ws, wn)
    tree, A = build_tree_pernode(active, groups, pl, cfg, np.random.default_rng(ch[3]))
    return tree, A, pl


# --- topology ---------------------------------------------------------------
def test_full_mesh_path_latency():
    cfg = SimConfig(n_nodes=50, topology="full_mesh", latency=5)
    pl = topology.build_path_latency(cfg, np.random.default_rng(0))
    assert pl.shape == (50, 50)
    assert np.all(np.diag(pl) == 0)
    off = pl[~np.eye(50, dtype=bool)]
    assert np.all(off == 5)


def test_geo_link_latency_mean_preserved_and_banded():
    # "geo" draws real-world geographic latency bands but rescales them so the configured
    # link_latency_mean stays the single mean-latency knob.
    cfg = SimConfig(n_nodes=300, topology="regular", degree=8,
                    link_latency_mean=0.08, link_latency_dist="geo")
    w = topology._sample_link_latencies(50_000, cfg, np.random.default_rng(3))
    assert abs(w.mean() - cfg.link_latency_mean) < 0.02 * cfg.link_latency_mean  # E[w] == mean
    scale = cfg.link_latency_mean / constants.GEO_LATENCY_MEAN_SLOTS
    expected = {round(b * scale, 9) for b in constants.GEO_LATENCY_BANDS_SLOTS}
    assert {round(x, 9) for x in np.unique(w)} == expected                       # exact bands
    # realistic direct-gossip: end-to-end (multi-hop) propagation stays a fraction of a slot
    pl = topology.build_path_latency(cfg, np.random.default_rng(4))
    assert float(pl[~np.eye(cfg.n_nodes, dtype=bool)].mean()) < 1.0


def test_regular_graph_connected_symmetric_and_degree():
    cfg = SimConfig(n_nodes=100, topology="regular", degree=6, link_latency_mean=1.0)
    pl = topology.build_path_latency(cfg, np.random.default_rng(1))
    assert np.all(np.diag(pl) == 0)
    assert np.allclose(pl, pl.T)                       # undirected
    assert np.all(np.isfinite(pl)) and pl.max() < cfg.epoch_len   # connected
    # direct neighbours (latency == link mean 1) — each node has exactly `degree` of them
    neigh = (pl == 1).sum(axis=1)
    assert np.all(neigh == 6)


# --- blend mixnet topology --------------------------------------------------
def test_blend_reuses_the_regular_graph():
    # blend transport runs over the SAME weighted d-regular graph as `regular`.
    common = dict(n_nodes=120, degree=6, link_latency_mean=1.0, link_latency_dist="fixed",
                  graph_seed=7)
    plr = topology.build_path_latency(SimConfig(topology="regular", **common),
                                      np.random.default_rng(0))
    plb = topology.build_path_latency(SimConfig(topology="blend", **common),
                                      np.random.default_rng(0))
    np.testing.assert_array_equal(plr, plb)


def test_blend_arrival_bounded_and_producer_instant():
    # inspects the raw (N x n_blocks) arrival matrix, so keep it (prune stores a sliding buffer)
    cfg = SimConfig(n_nodes=120, topology="blend", degree=6, link_latency_mean=1.0,
                    blend_hops=3, blend_delay_max=3.0, k=8, max_uncles=0, prune_arrival=False)
    tree, A, pl = _build(cfg)
    # hard cascade bound used by the windowed horizon: (hops+1) transport legs + hops mix delays
    H = (cfg.blend_hops + 1) * float(pl.max()) + cfg.blend_hops * cfg.blend_delay_max
    assert np.all(A[:, GENESIS] == 0)
    for b in range(1, tree.n_blocks):
        s = float(tree.slot[b])
        v = int(tree.leader[b])
        assert A[v, b] == max(s, float(A[v, int(tree.parent[b])]))   # producer sees own instantly
        assert np.all(A[:, b] - s <= H + 1e-9)                        # nobody exceeds the bound
        assert np.all(A[:, b] >= A[:, int(tree.parent[b])])          # never before parent


def test_blend_mixing_delay_increases_arrival():
    def mean_rel_arrival(delay_max):
        cfg = SimConfig(n_nodes=120, topology="blend", degree=6, link_latency_mean=1.0,
                        blend_hops=3, blend_delay_max=delay_max, k=8, max_uncles=0,
                        prune_arrival=False)
        tree, A, _ = _build(cfg)
        rel = [float((np.delete(A[:, b], int(tree.leader[b])) - float(tree.slot[b])).mean())
               for b in range(1, tree.n_blocks)]
        return float(np.mean(rel))
    # more mixing delay per hop => strictly later visibility on average
    assert mean_rel_arrival(0.0) < mean_rel_arrival(6.0)


# --- arrival matrix invariants ----------------------------------------------
def test_arrival_clamp_and_genesis():
    cfg = SimConfig(n_nodes=60, topology="regular", degree=6, link_latency_mean=2.0,
                    k=8, max_uncles=0, prune_arrival=False)   # inspects the raw arrival matrix
    tree, A, _ = _build(cfg)
    assert np.all(A[:, GENESIS] == 0)                  # genesis seen by all at slot 0
    for b in range(1, tree.n_blocks):
        p = int(tree.parent[b])
        assert np.all(A[:, b] >= A[:, p])              # never arrive before parent
        v = int(tree.leader[b])
        # producer sees its own block at its slot (sub-slot/float arrivals)
        assert A[v, b] == max(float(tree.slot[b]), float(A[v, p]))


def test_full_mesh_zero_divergence_parity():
    # Full mesh L=0: identical views -> identical per-node D_est -> range 0, agreement 1.
    df = pd.DataFrame(run_trajectory(SimConfig(
        n_nodes=200, topology="full_mesh", latency=0, max_uncles=0, k=16, epochs=16)))
    assert (df["range_ratio"] == 0.0).all()
    assert (df["agreement_window"] == 1.0).all()
    assert abs(df["mean_ratio"].iloc[-4:].mean() - 1.0) < 0.1


def test_regular_graph_window_agreement_holds():
    # Even under a graph, the settled window agrees -> zero D_est spread.
    df = pd.DataFrame(run_trajectory(SimConfig(
        n_nodes=200, topology="regular", degree=6, link_latency_mean=3.0,
        max_uncles=2, k=12, epochs=10)))
    assert (df["range_ratio"] < 1e-9).all()
    assert (df["agreement_window"] > 0.999).all()


def test_topology_shifts_mean_accuracy():
    def mean_ratio(**kw):
        vals = [pd.DataFrame(run_trajectory(SimConfig(
            n_nodes=200, topology="regular", max_uncles=0, k=12, epochs=12, replicate=r, **kw)
            ))["mean_ratio"].iloc[6:].mean() for r in range(4)]
        return float(np.mean(vals))
    sparse = mean_ratio(degree=2, link_latency_mean=6.0)
    dense = mean_ratio(degree=16, link_latency_mean=1.0)
    assert sparse < dense                              # more forks -> lower estimate


# --- windowed fork choice ---------------------------------------------------
@pytest.mark.parametrize("kw", [
    dict(topology="regular", degree=6, link_latency_mean=3.0, max_uncles=4),
    dict(topology="regular", degree=2, link_latency_mean=8.0, max_uncles=2),  # sparse: big H
    dict(topology="full_mesh", latency=5, max_uncles=2),
    dict(topology="full_mesh", latency=0, max_uncles=0),
    # blend: mixing delays are Uniform-bounded, so the windowed horizon stays exact
    dict(topology="blend", degree=6, link_latency_mean=1.0, blend_hops=3, blend_delay_max=3.0,
         max_uncles=4),
    dict(topology="blend", degree=4, link_latency_mean=2.0, blend_hops=2, blend_delay_max=5.0,
         max_uncles=2),
])
def test_windowed_fork_choice_matches_full_scan(kw):
    # Deterministic latency (jitter=0): the windowed horizon must be BIT-IDENTICAL to a full scan.
    # windowed_fork_choice is not in key(), so both share the same seed/inputs. prune_arrival is
    # disabled here so both keep a full matrix A (the pruned==full parity is test_prune_* below).
    tw, Aw, _ = _build(SimConfig(n_nodes=150, k=10, windowed_fork_choice=True,
                                 prune_arrival=False, **kw))
    tf, Af, _ = _build(SimConfig(n_nodes=150, k=10, windowed_fork_choice=False,
                                 prune_arrival=False, **kw))
    np.testing.assert_array_equal(tw.parent, tf.parent)
    np.testing.assert_array_equal(tw.height, tf.height)
    np.testing.assert_array_equal(Aw, Af)
    assert tw.uncles == tf.uncles


def test_jitter_warns_under_windowed():
    cfg = SimConfig(n_nodes=80, topology="regular", degree=6, link_latency_mean=2.0,
                    jitter_mean=1.0, k=8)
    with pytest.warns(RuntimeWarning, match="windowed_fork_choice"):
        _build(cfg)


def test_windowed_never_builds_on_unreceived_block_under_jitter():
    # jitter > 0 disables pruning (falls back to the full matrix), whose safety clamp keeps the
    # tree valid even under the windowed approximation.
    cfg = SimConfig(n_nodes=80, topology="regular", degree=6, link_latency_mean=2.0,
                    jitter_mean=2.0, k=8, max_uncles=2)
    with pytest.warns(RuntimeWarning):
        tree, A, _ = _build(cfg)
    for b in range(1, tree.n_blocks):
        v = int(tree.leader[b])
        assert A[v, int(tree.parent[b])] <= int(tree.slot[b])   # producer had the parent


# --- sliding-window prune ---------------------------------------------------
@pytest.mark.parametrize("kw", [
    dict(topology="full_mesh", latency=3, max_uncles=2),
    dict(topology="regular", degree=8, link_latency_mean=1.0, max_uncles=3),
    dict(topology="regular", degree=4, link_latency_mean=0.1, max_uncles=2,
         uncle_strategy="random"),
    # blend deg4 (small graph horizon, W-dominated keepspan -> heavy compaction) caught an
    # off-by-one in the finalize boundary; low gdf forces many compactions.
    dict(topology="blend", degree=4, link_latency_mean=0.1, blend_hops=3, blend_delay_max=2.0,
         max_uncles=2, genesis_d_factor=0.05, uncle_strategy="oldest"),
    dict(topology="blend", degree=4, link_latency_mean=0.1, blend_hops=3, blend_delay_max=2.0,
         max_uncles=3, genesis_d_factor=0.05, uncle_strategy="random", init_dest="heterogeneous"),
])
def test_prune_matches_full_matrix(kw):
    # prune_arrival is a pure memory optimisation: at jitter=0 the pruned build must reproduce the
    # full matrix's per-epoch rows BIT-FOR-BIT (it is excluded from key(), so seeds match).
    common = dict(n_nodes=120, k=64, epochs=6, stake_dist="pareto", link_latency_dist="geo",
                  init_spread=0.5)
    df_prune = pd.DataFrame(run_trajectory(SimConfig(**common, **kw, prune_arrival=True)))
    df_full = pd.DataFrame(run_trajectory(SimConfig(**common, **kw, prune_arrival=False)))
    pd.testing.assert_frame_equal(df_prune, df_full)


def test_prune_returns_small_sliding_buffer():
    # The collapsed regime that OOM-froze the full matrix: pruning must keep only a keep-span
    # window, not all n_blocks.
    from tsi_sim.blocktree import SlidingArrival
    cfg = SimConfig(n_nodes=100, k=64, stake_dist="pareto", genesis_d_factor=0.02,
                    topology="regular", degree=8, link_latency_mean=0.1)
    tree, arr, _ = _build(cfg)
    assert isinstance(arr, SlidingArrival)
    assert arr.buf.shape[1] < tree.n_blocks           # buffer far narrower than the block count


# --- update_D_vec -----------------------------------------------------------
def test_update_D_vec_matches_scalar():
    f, T = 1 / 30, 3000
    d = np.array([1000.0, 500.0, 2000.0])
    m = np.array([90, 100, 110])
    got = tsi.update_D_vec(d, m, T, f, beta=1.0)
    exp = np.array([tsi.update_D(float(d[i]), int(m[i]), T, f, 1.0) for i in range(3)])
    np.testing.assert_allclose(got, exp)


# --- adversarial grinding (uncle suppression) -------------------------------
def test_adversary_frac_zero_is_noop():
    # adversary_frac=0 -> mask None -> identical to a plain honest run (bit-for-bit rows).
    kw = dict(n_nodes=150, k=16, epochs=6, stake_dist="pareto", topology="blend", degree=6,
              link_latency_dist="geo", link_latency_mean=0.5, blend_hops=3, blend_delay_max=8.0,
              max_uncles=2, genesis_d_factor=0.5)
    a = pd.DataFrame(run_trajectory(SimConfig(**kw)))
    b = pd.DataFrame(run_trajectory(SimConfig(**kw, adversary_frac=0.0)))
    pd.testing.assert_frame_equal(a, b)


def test_adversary_uncle_suppression_deflates_and_is_deterministic():
    kw = dict(n_nodes=200, k=32, epochs=8, stake_dist="pareto", topology="blend", degree=6,
              link_latency_dist="geo", link_latency_mean=0.5, blend_hops=3, blend_delay_max=24.0,
              max_uncles=2, uncle_window=300, genesis_d_factor=0.5)
    honest = pd.DataFrame(run_trajectory(SimConfig(**kw)))
    adv = pd.DataFrame(run_trajectory(SimConfig(**kw, adversary_frac=0.4)))

    def tail(df):
        return df[df.epoch >= df.epochs * 0.5].mean_ratio.mean()

    assert tail(adv) < tail(honest) - 0.02        # grinding deflates D_hat (raises win rate)
    adv2 = pd.DataFrame(run_trajectory(SimConfig(**kw, adversary_frac=0.4)))
    pd.testing.assert_frame_equal(adv, adv2)      # deterministic


def test_adversary_withhold_deflates_far_more_than_suppress():
    # Withholding orphans the adversary's own blocks (won slots wasted), so counted density drops
    # ~beta and D_hat deflates toward the active stake (1-beta)*D — much stronger than suppression.
    kw = dict(n_nodes=300, k=64, epochs=12, stake_dist="pareto", topology="regular", degree=8,
              link_latency_mean=0.3, link_latency_dist="geo", max_uncles=2, uncle_window=300,
              genesis_d_factor=0.5, windowed_fork_choice=False)
    def settled(**extra):
        rows = pd.DataFrame(run_trajectory(SimConfig(**kw, **extra)))
        return rows[lambda d: d.epoch >= 6].mean_ratio.mean()

    honest = settled()
    supp = settled(adversary_frac=0.3, adversary_strategy="suppress")
    wh = settled(adversary_frac=0.3, adversary_strategy="withhold")
    assert supp > 0.95 * honest          # suppression barely moves it on sub-slot direct gossip
    assert wh < 0.8 * honest             # withholding deflates toward (1-0.3) = 0.7


def test_reward_attribution_backward_compat():
    # adversary_frac == 0 leaves the sim bit-identical and credits no adversary blocks.
    kw = dict(n_nodes=200, k=32, epochs=6, stake_dist="uniform", topology="regular", degree=6,
              link_latency_mean=0.3, link_latency_dist="geo", max_uncles=1)
    rows = pd.DataFrame(run_trajectory(SimConfig(**kw)))
    assert (rows.adv_blocks == 0).all() and (rows.adv_block_share == 0.0).all()
    assert (rows.honest_blocks > 0).all()


def test_dynamic_withhold_schedule_gates_and_is_unprofitable():
    # Equal stakes -> coalition_frac == beta exactly. A withhold-then-rejoin grinder deflates D_hat
    # only on its withhold epochs and earns canonical blocks only on its rejoin epochs; because it
    # forfeits whole epochs to depress a difficulty that helps everyone, it earns strictly LESS
    # than its stake share (reward/stake < 1) — dynamic withholding is self-punishing like static.
    beta_adv = 0.3
    kw = dict(n_nodes=1000, k=64, epochs=20, stake_dist="uniform", topology="regular", degree=8,
              link_latency_mean=0.3, link_latency_dist="geo", max_uncles=2, uncle_window=300,
              genesis_d_factor=0.5, windowed_fork_choice=False, adversary_frac=beta_adv,
              adversary_strategy="withhold")
    dyn = pd.DataFrame(run_trajectory(
        SimConfig(**kw, adversary_period=2, adversary_withhold_epochs=1)))
    tail = dyn[dyn.epoch >= 10]
    wh = tail[tail.adversary_withholding]
    rj = tail[~tail.adversary_withholding]
    # schedule alternates; withhold epochs deflate toward active stake, rejoin epochs recover
    assert wh.mean_ratio.mean() < 0.85 and rj.mean_ratio.mean() > 0.90
    # coalition earns ~0 while withholding, ~beta while rejoined
    assert wh.adv_block_share.mean() < 0.02
    assert abs(rj.adv_block_share.mean() - beta_adv) < 0.05
    # profitability: realized share of ALL canonical blocks over the run, vs stake share beta
    total_blocks = (tail.adv_blocks + tail.honest_blocks).sum()
    reward_over_stake = tail.adv_blocks.sum() / (beta_adv * total_blocks)
    assert reward_over_stake < 1.0        # strictly unprofitable for a minority coalition
