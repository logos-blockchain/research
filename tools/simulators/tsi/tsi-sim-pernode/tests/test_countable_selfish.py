"""Countable (first-fork) uncle recovery under a selfish adversary (§6.6).

The countable model can reference only the first block of a fork, so a discarded *chain* of
honest blocks yields one countable uncle however long it is. These tests pin the two ends of
that: SM1 never buries a second block (so the restriction costs nothing), while the optimal
policy waits and does (so it costs a factor of ~2 in recoverable orphans).
"""

import numpy as np
import pytest

from tsi_sim.selfish import race_from_alpha, selfish_threshold
from tsi_sim.selfish_mdp import optimal_policy_stats

FAST = dict(cap=16, iters=1500)


@pytest.mark.parametrize("gamma", [0.0, 0.5, 1.0])
@pytest.mark.parametrize("alpha", [0.2, 1 / 3, 0.4, 0.45])
def test_sm1_orphans_are_all_countable(alpha, gamma):
    # SM1 acts as soon as the honest branch reaches length 1, so every orphan it makes is the
    # first block of its fork: the first-fork restriction costs SM1 exactly nothing.
    r = race_from_alpha(alpha, 200_000, gamma, np.random.default_rng(3))
    assert r.orphan_hon_runs == r.orphan_hon
    assert r.countable_recovery == 1.0


@pytest.mark.parametrize("gamma", [0.0, 0.5])
def test_optimal_policy_block_conservation(gamma):
    # Every block-finding event yields exactly one block, which ends up canonical or orphaned.
    # Per-event rates must therefore sum to 1 — the same invariant test_selfish asserts for SM1.
    s = optimal_policy_stats(0.4, gamma, **FAST)
    total = s.density_fraction + s.orphan_hon_blocks + s.orphan_adv_blocks
    assert abs(total - 1.0) < 1e-9


@pytest.mark.parametrize("gamma", [0.0, 0.5])
def test_optimal_policy_buries_orphans(gamma):
    # Above the profitability threshold the optimum waits before overriding, so it discards
    # multi-block honest chains that the first-fork rule cannot recover.
    s = optimal_policy_stats(0.4, gamma, **FAST)
    assert s.deviates
    assert s.orphan_hon_runs < s.orphan_hon_blocks
    assert s.countable_recovery < 0.7          # measured ~0.44 (gamma=0) / ~0.55 (gamma=0.5)


def test_below_threshold_does_not_deviate():
    # Below the threshold the optimum is honest mining; the MDP is indifferent across policies
    # there, so the orphan structure of an arbitrary greedy tie-break must not be reported.
    alpha = 0.25
    assert alpha < selfish_threshold(0.0)
    s = optimal_policy_stats(alpha, 0.0, **FAST)
    assert not s.deviates
    assert s.orphan_hon_blocks == 0.0
    assert s.density_fraction == 1.0


def test_countable_dhat_is_below_unrestricted():
    s = optimal_policy_stats(0.4, 0.0, **FAST)
    # With no references the two models agree; with them, countable recovers strictly less.
    assert s.dhat_ratio(p_ref=0.0, countable=True) == s.dhat_ratio(p_ref=0.0, countable=False)
    assert s.dhat_ratio(p_ref=1.0, countable=True) < s.dhat_ratio(p_ref=1.0, countable=False)
    # and both are bounded by the no-attack value
    assert s.dhat_ratio(p_ref=1.0, countable=False) <= 1.0
    # monotone in the reference rate
    assert (s.dhat_ratio(p_ref=0.0, countable=True)
            < s.dhat_ratio(p_ref=0.5, countable=True)
            < s.dhat_ratio(p_ref=1.0, countable=True))


def test_attacker_self_uncle_is_capped_too():
    # The attacker's abandoned secret chain is also one chain, so it can self-uncle only its
    # first block — the §6.7(a) farming channel is narrower than the block count suggests.
    s = optimal_policy_stats(0.4, 0.0, **FAST)
    assert s.orphan_adv_runs < s.orphan_adv_blocks
    assert 0.5 < s.countable_recovery_adv < 1.0


def test_unconstrained_deflation_optimum_is_abstention():
    # Minimising the estimate with no constraint degenerates: publish nothing, and D-hat lands on
    # exactly 1 - alpha with zero revenue. §6.4 already covers that case and shows it is CORRECT
    # measurement rather than mis-measurement, which is why item 16 needs the paid frontier.
    from tsi_sim.selfish_mdp import deflation_optimal_stats

    for alpha in (0.2, 0.4):
        s = deflation_optimal_stats(alpha, 0.0, cap=16)
        assert abs(s.dhat_ratio(1.0, True) - (1.0 - alpha)) < 1e-6
        assert s.revenue < 1e-9
        assert s.orphan_hon_blocks < 1e-9          # it orphans no honest work at all


def test_deflation_solver_gain_matches_its_stationary_accounting():
    # deflation_optimal_stats raises if the MDP's average gain disagrees with the estimate
    # recomputed from the stationary distribution -- an independent check that the solver and the
    # orphan accounting describe the same policy. Exercise it across a spread of inputs.
    from tsi_sim.selfish_mdp import deflation_optimal_stats

    for alpha in (0.25, 0.35, 0.45):
        for p_ref in (0.0, 0.85, 1.0):
            deflation_optimal_stats(alpha, 0.0, p_ref=p_ref, cap=16)   # no AssertionError


def test_frontier_endpoints_bracket_the_two_pure_objectives():
    from tsi_sim.selfish_mdp import deflation_frontier, deflation_optimal_stats

    alpha = 0.4
    zero = deflation_frontier(alpha, 0.0, 0.0, cap=16)
    pure = deflation_optimal_stats(alpha, 0.0, cap=16)
    assert abs(zero["dhat_countable"] - pure.dhat_ratio(1.0, True)) < 1e-6   # lam=0 is that optimum
    # Selfish mining takes a bigger share of a SMALLER pie, so maximising raw adversary block
    # rate returns to honest mining -- the frontier is not monotone in revenue, by construction.
    far = deflation_frontier(alpha, 0.0, 50.0, cap=16)
    assert abs(far["revenue"] - alpha) < 1e-3
    assert abs(far["dhat_countable"] - 1.0) < 1e-3


def test_a_paid_policy_deflates_further_than_the_revenue_optimum():
    # Item 16's answer: the revenue-optimal adversary is not the estimator's worst case. At
    # alpha = 0.4 a policy exists that pays at least as well as honest mining yet deflates
    # substantially further than the revenue optimum does.
    from tsi_sim.selfish_mdp import deflation_frontier, optimal_policy_stats

    alpha, cap = 0.4, 32
    ro = optimal_policy_stats(alpha, 0.0, cap=cap)
    paid = [deflation_frontier(alpha, 0.0, lam, cap=cap) for lam in (0.4, 0.6, 0.8, 1.0)]
    paid = [p for p in paid if p["reward_per_stake"] >= 1.0 - 1e-9]
    assert paid, "expected at least one break-even-or-better frontier point"
    assert min(p["dhat_countable"] for p in paid) < ro.dhat_ratio(1.0, True) - 0.05


def test_reorg_countable_recovery_from_depths():
    # A depth-d reorg discards one chain of d blocks -> 1 countable uncle: runs / blocks.
    from tsi_sim.reorg import countable_recovery_from_depths

    assert countable_recovery_from_depths(np.array([], dtype=np.int64)) == 1.0
    assert countable_recovery_from_depths(np.array([1, 1, 1])) == 1.0     # SM1-like: all depth-1
    assert countable_recovery_from_depths(np.array([3, 1, 2])) == 0.5     # 3 runs / 6 blocks
    # and it is the depth-weighted harmonic sense of "share": deeper reorgs drag it down
    assert countable_recovery_from_depths(np.array([10])) == 0.1


@pytest.mark.slow
def test_cap_convergence():
    # The orphan shape converges more slowly in cap than the revenue does; check the drift is
    # small where the report quotes numbers.
    a = optimal_policy_stats(0.4, 0.0, cap=48)
    b = optimal_policy_stats(0.4, 0.0, cap=64)
    assert abs(a.countable_recovery - b.countable_recovery) < 2e-3
    assert abs(a.revenue - b.revenue) < 1e-3
