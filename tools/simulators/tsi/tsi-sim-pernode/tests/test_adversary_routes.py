"""The deeper rules and re-rooting against an adversary (PLAN.md Phase 4).

Re-rooting runs under a selfish or a withholding coalition, which never re-roots. A private
block reaches an honest leader only when it is released, and the release must reach the
leader's watch. The lost slots are split into those an honest block holds and those whose
blocks reached no node. The selfish-mining MDP reads what a cousin rule counts: the first two
blocks of every discarded chain.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from tsi_sim import sweep
from tsi_sim.blocktree import BlockTree, _fork_point
from tsi_sim.config import SimConfig, SweepConfig
from tsi_sim.fork import lost_slots


# --- end to end -------------------------------------------------------------------------------
def _cfg(**kw):
    base = dict(n_nodes=300, stake_dist="pareto", topology="blend", degree=6,
                link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                blend_delay_max=8.0, max_uncles=4, uncle_window_anchor="parent",
                window_absorption=12.0, uncle_order="parent", k=64, epochs=3,
                genesis_d_factor=1.0, paired_streams=True, adversary_frac=0.3,
                adversary_strategy="selfish")
    return SimConfig(**{**base, **kw})


def _capture(monkeypatch, **kw):
    import tsi_sim.engine as engine
    import tsi_sim.epoch as ep
    from tsi_sim.engine import run_trajectory

    seen: list = []
    build, sim = ep.build_tree_pernode, engine.simulate_epoch

    def capture_tree(*a, **k):
        tree, A = build(*a, **k)
        seen.append({"active": a[0], "tree": tree, "A": A, "adv": k.get("adversary_mask"),
                     "reroot": k.get("reroot_mask")})
        return tree, A

    def capture_result(*a, **k):
        er = sim(*a, **k)
        seen[-1]["er"] = er
        return er

    monkeypatch.setattr(ep, "build_tree_pernode", capture_tree)
    monkeypatch.setattr(engine, "simulate_epoch", capture_result)
    cfg = _cfg(**kw)
    run_trajectory(cfg)
    return cfg, seen


def _is_under(tree, p, b):
    while tree.height[b] > tree.height[p]:
        b = int(tree.parent[b])
    return b == p


def test_the_watch_matches_a_brute_force_replay_under_a_selfish_coalition(monkeypatch):
    """Every copy, and only those, where a replay of an honest leader's view on the final arrival
    matrix first leaves the subtree of its block's parent: some of them because a release did."""
    cfg, seen = _capture(monkeypatch, reroot_share=1.0, reroot_delay=3.0)
    w = cfg.effective_uncle_window
    n_copies = by_release = 0
    for ep in seen:
        active, tree, A, adv, rr = ep["active"], ep["tree"], ep["A"], ep["adv"], ep["reroot"]
        assert adv is not None and adv.any() and not (rr & adv).any()
        nb = tree.n_blocks
        key = (tree.height * (nb + 1) * (cfg.epoch_len + 2) - tree.slot * (nb + 1)
               - np.arange(nb))
        want = {}
        for x in range(1, nb):
            p, v = int(tree.parent[x]), int(tree.leader[x])
            if p == 0 or not rr[v]:
                continue
            sx = int(tree.slot[x])
            last = active[active <= sx + w]
            horizon = float(last.max()) if last.size else -1.0   # the last check before expiry
            best = None
            for b in np.lexsort((-key, A[v])):
                if A[v, b] > horizon:
                    break
                if best is None or key[b] > key[best]:
                    best = int(b)
                    if A[v, b] > sx and not _is_under(tree, p, best):
                        want[x] = (best, float(A[v, b]))
                        break
        got = {int(x): (g, float(pub) - cfg.reroot_delay)
               for x, g, pub in zip(tree.copy_of, tree.copy_parent, tree.copy_pub, strict=True)}
        assert set(got) == set(want)
        for x, (b, tau) in want.items():
            assert got[x][0] == _fork_point(tree.parent, tree.height, x, b)
            assert got[x][1] == pytest.approx(tau)
            by_release += bool(adv[int(tree.leader[b])])
        n_copies += len(got)
    assert by_release > 0 and n_copies > by_release


@pytest.mark.parametrize("kw", [dict(), dict(reroot_share=1.0),
                                dict(adversary_strategy="withhold", reroot_share=1.0),
                                dict(uncle_depth=0, uncle_window_anchor="uncle",
                                     uncle_order="uncle")])
def test_the_split_of_the_lost_slots_reads_the_measured_count(monkeypatch, kw):
    _, seen = _capture(monkeypatch, **kw)
    for ep in seen:
        tree, A, er, adv = ep["tree"], ep["A"], ep["er"], ep["adv"]
        cfg = _cfg(**kw)
        lost = lost_slots(tree, A, cfg.period_T, cfg.epoch_len, coalition_mask=adv)
        assert np.all(er.m == lost.occupied - lost.lost)
        coalition_only = lost.lost - sum(lost.honest)
        assert 0 <= lost.unpublished <= coalition_only
        if kw.get("adversary_strategy") == "withhold":     # it publishes nothing
            assert 0 < lost.unpublished == coalition_only
        occ = lost.occupied
        assert (er.lost_honest_d1_share, er.lost_honest_d2_share, er.lost_honest_d3plus_share,
                er.lost_unpublished_share) == (lost.honest[0] / occ, lost.honest[1] / occ,
                                               (lost.honest[2] + lost.honest[3]) / occ,
                                               lost.unpublished / occ)
    if kw.get("reroot_share"):
        assert any(ep["er"].rerooted_share > 0 for ep in seen)


def test_without_a_coalition_every_lost_slot_is_honest():
    from tsi_sim.engine import run_trajectory

    for r in run_trajectory(_cfg(adversary_frac=0.0, blend_delay_max=32.0)):
        assert (r["lost_honest_d1_share"], r["lost_honest_d2_share"]) == (r["lost_d1_share"],
                                                                          r["lost_d2_share"])
        assert r["lost_honest_d3plus_share"] == pytest.approx(r["lost_d3_share"]
                                                              + r["lost_d4plus_share"])
        assert r["lost_unpublished_share"] == 0.0


# --- the lost slots, by hand --------------------------------------------------------------------
# canonical 1(s0) 2(s2) 6(s5) 10(s9) 12(s12) 13(s14); block 6 carries uncle 3.
# Honest fork off 2: 3(s3, d1) -> 4(s4, d2) -> 7(s6, d3), and 14(s6, off 6, d1) shares slot 6
# with 7. The coalition (node 1): 5(s4, off 2, d1, withheld) shares slot 4 with 4; 8(s7, off 6,
# d1, held by the coalition only) -> 9(s8, d2, withheld); 11(s10, off 10, d1), published.
def _split_tree():
    #                        id: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14
    tree = BlockTree(slot=np.array([-1, 0, 2, 3, 4, 4, 5, 6, 7, 8, 9, 10, 12, 14, 6], np.int64),
                     parent=np.array([-1, 0, 1, 2, 3, 2, 2, 4, 6, 8, 6, 10, 10, 12, 6],
                                     np.int64),
                     height=np.array([0, 1, 2, 3, 4, 3, 3, 5, 4, 5, 4, 5, 5, 6, 4], np.int64),
                     leader=np.array([-1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0], np.int64),
                     uncles=[() for _ in range(15)])
    tree.uncles[6] = (3,)
    A = np.zeros((2, 15))
    A[:, [5, 8, 9]] = 101.0                            # past the cutoff: reached no node
    A[1, 8] = 7.5                                      # ...but the coalition holds 8
    return tree, A


def test_lost_slots_split_honest_and_unpublished():
    tree, A = _split_tree()
    coalition = np.array([False, True])
    lost = lost_slots(tree, A, T=20, cutoff=100, coalition_mask=coalition)
    assert lost.occupied == 12
    assert lost.by_depth == (4, 1, 0, 0)               # s4 (via 5), s6 (via 14), s7, s10; s8
    assert lost.honest == (1, 1, 0, 0)                 # s6 via 14 (d1), s4 via 4 (d2)
    assert lost.unpublished == 2                       # s7, s8: s4 holds the published 4
    plain = lost_slots(tree, A, T=20, cutoff=100)      # every node is honest: 8 reached one
    assert plain.honest == plain.by_depth and plain.unpublished == 1


# --- configuration ------------------------------------------------------------------------------
@pytest.mark.parametrize("strategy", ["selfish", "withhold"])
def test_rerooting_runs_against_a_selfish_or_withholding_coalition(strategy):
    SimConfig(reroot_share=0.5, adversary_frac=0.2, adversary_strategy=strategy)


@pytest.mark.parametrize("strategy", ["suppress", "deep_parent"])
def test_rerooting_is_not_defined_against_the_other_adversaries(strategy):
    with pytest.raises(ValueError):
        SimConfig(reroot_share=0.5, adversary_frac=0.2, adversary_strategy=strategy)


@pytest.mark.parametrize("dist", ["uniform", "pareto"])
def test_a_coalition_never_reroots(dist):
    from tsi_sim.engine import _adversary_mask, _reroot_mask
    from tsi_sim.stake import make_stake

    cfg = SimConfig(n_nodes=500, stake_dist=dist, reroot_share=0.5, adversary_frac=0.3,
                    adversary_strategy="selfish")
    stake = make_stake(cfg, np.random.default_rng(1))
    adv = _adversary_mask(cfg, stake)
    mask = _reroot_mask(cfg, stake, adv)
    assert adv.any() and not (mask & adv).any()
    honest = float(stake[~adv].sum())
    # Equal stakes fill the half exactly; a heavy tail can miss it by one holder.
    tol = 1e-12 if dist == "uniform" else stake[~adv].max() / honest
    assert abs(stake[mask].sum() / honest - 0.5) <= tol
    np.testing.assert_array_equal(_reroot_mask(dataclasses.replace(cfg, reroot_share=1.0), stake,
                                               adv), ~adv)


def test_an_empty_axis_takes_the_base_value():
    kept = SweepConfig(max_uncles=[2], replicates=1, base=dict(adversary_frac=0.3)).expand()
    assert [c.adversary_frac for c in kept] == [0.3]
    swept = SweepConfig(max_uncles=[2], replicates=1, adversary_frac=[0.0, 0.2],
                        base=dict(adversary_strategy="selfish")).expand()
    assert [c.adversary_frac for c in swept] == [0.0, 0.2]


@pytest.mark.parametrize("strategy", ["selfish", "withhold"])
def test_adversaries_are_sized_for_the_full_matrix(strategy):
    # Same key, so the same stake draw: only the matrix path differs.
    cell = SimConfig(n_nodes=1000, k=2160, stake_dist="pareto", adversary_frac=0.3,
                     adversary_strategy=strategy)
    full = dataclasses.replace(cell, prune_arrival=False)
    assert sweep.estimate_worker_bytes(cell) == sweep.estimate_worker_bytes(full)
    suppress = dataclasses.replace(cell, adversary_strategy="suppress")
    assert (sweep.estimate_worker_bytes(suppress)
            < sweep.estimate_worker_bytes(dataclasses.replace(suppress, prune_arrival=False)))


# --- the MDP --------------------------------------------------------------------------------------
def test_the_policy_rates_count_the_first_two_blocks_of_every_chain():
    from tsi_sim.selfish_mdp import _policy_rates

    shape = (4, 1, 3)
    probs, ohon, oadv = np.zeros(shape), np.zeros(shape), np.zeros(shape)
    probs[0, 0] = (0.5, 0.3, 0.2)
    ohon[0, 0] = (1, 3, 0)
    oadv[0, 0] = (0, 0, 4)
    pc = (probs, np.zeros(shape, np.int64), np.zeros(shape), np.zeros(shape), ohon, oadv,
          np.ones((4, 1), bool))
    r = _policy_rates(pc, np.array([0]), np.array([1.0]))
    assert (r["orphan_hon_blocks"], r["orphan_hon_runs"], r["orphan_hon_d2"]) == pytest.approx(
        (1.4, 0.8, 1.1))
    assert (r["orphan_adv_blocks"], r["orphan_adv_runs"], r["orphan_adv_d2"]) == pytest.approx(
        (0.8, 0.2, 0.4))


def test_cousins_count_more_of_what_the_optimal_policy_buries():
    from tsi_sim.selfish_mdp import optimal_policy_stats

    s = optimal_policy_stats(0.4, 0.0, cap=16, iters=1500)
    assert s.counted(1) == s.orphan_hon_runs
    assert s.countable_recovery == s.recovery(1)
    assert s.countable_recovery_adv == s.recovery(1, adv=True)
    assert s.recovery(1) < s.recovery(2) < 1.0
    assert s.recovery(1, adv=True) < s.recovery(2, adv=True) <= 1.0
    assert (s.dhat_ratio(1.0) < s.dhat_ratio(1.0, max_depth=2)
            < s.dhat_ratio(1.0, countable=False))
    with pytest.raises(ValueError):
        s.recovery(3)


def test_below_the_threshold_cousins_count_what_honest_mining_leaves():
    from tsi_sim.selfish_mdp import optimal_policy_stats

    s = optimal_policy_stats(0.25, 0.0, cap=16, iters=1500)
    assert not s.deviates and s.dhat_ratio(1.0, max_depth=2) == 1.0 == s.recovery(2)


def test_reorg_recovery_counts_the_first_two_blocks():
    from tsi_sim.reorg import countable_recovery_from_depths

    assert countable_recovery_from_depths(np.array([3, 1, 2]), max_depth=2) == 5 / 6
    assert countable_recovery_from_depths(np.array([1, 1, 1]), max_depth=2) == 1.0
    assert countable_recovery_from_depths(np.array([10]), max_depth=2) == 0.2
