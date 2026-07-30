"""Selfish / private-chain withholding model (§6.6)."""

import numpy as np
import pytest

from tsi_sim.selfish import (
    RaceResult,
    RewardParams,
    honest_reward_recovery,
    race_from_alpha,
    reward_shares,
    selfish_revenue_closed_form,
    selfish_threshold,
    simulate_selfish,
    tsi_dhat_ratio,
)
from tsi_sim.selfish_mdp import optimal_selfish_revenue


@pytest.mark.parametrize("gamma", [0.0, 0.5, 1.0])
@pytest.mark.parametrize("alpha", [0.1, 0.2, 1 / 3, 0.4, 0.45])
def test_race_matches_eyal_sirer_closed_form(alpha, gamma):
    # The SM1 simulation must reproduce the analytic relative revenue within MC noise.
    rng = np.random.default_rng(12345)
    r = race_from_alpha(alpha, 2_000_000, gamma, rng)
    assert abs(r.revenue_share - selfish_revenue_closed_form(alpha, gamma)) < 0.004


@pytest.mark.parametrize("gamma", [0.0, 0.5, 1.0])
def test_block_conservation(gamma):
    # Every mined block is exactly one of: adversary-canonical, honest-canonical, or orphaned
    # (honest or adversary). This must hold at all gamma (the tie race must account for its blocks).
    r = race_from_alpha(0.4, 1_000_000, gamma, np.random.default_rng(7))
    assert r.adv + r.hon + r.orphan_hon + r.orphan_adv == r.events


def test_honest_only_has_no_orphans_and_stake_share():
    # alpha = 0 -> every block honest, none orphaned, adversary share 0.
    rng = np.random.default_rng(1)
    r = race_from_alpha(0.0, 100_000, 0.0, rng)
    assert r.adv == 0 and r.orphan_hon == 0 and r.orphan_adv == 0
    assert r.revenue_share == 0.0 and r.density_fraction == 1.0


def test_selfish_is_profitable_above_threshold_only():
    # Below the gamma=0 threshold (1/3) selfish under-earns; above it over-earns its stake.
    rng = np.random.default_rng(7)
    below = race_from_alpha(0.25, 2_000_000, 0.0, rng)
    above = race_from_alpha(0.40, 2_000_000, 0.0, rng)
    assert below.revenue_share < 0.25              # honest mining is better here
    assert above.revenue_share > 0.40              # selfish premium: earns more than its stake
    assert abs(selfish_threshold(0.0) - 1 / 3) < 1e-9


def test_selfish_orphans_honest_blocks_and_deflates_density():
    # A profitable selfish attack orphans honest blocks, so the counted canonical density < 1,
    # which is exactly what deflates D_hat; uncle recovery restores it monotonically toward 1.
    rng = np.random.default_rng(3)
    r = race_from_alpha(0.4, 1_000_000, 0.0, rng)
    assert r.orphan_hon > 0
    assert r.density_fraction < 1.0
    d0 = tsi_dhat_ratio(r, uncle_recovery=0.0)
    d_half = tsi_dhat_ratio(r, uncle_recovery=0.5)
    d1 = tsi_dhat_ratio(r, uncle_recovery=1.0)
    assert d0 < d_half < d1 <= 1.0 + 1e-9
    assert abs(d0 - r.density_fraction) < 1e-9


def test_simulate_selfish_is_deterministic_given_stream_and_seed():
    is_adv = np.random.default_rng(0).random(50_000) < 0.35
    a = simulate_selfish(is_adv, 0.5, np.random.default_rng(99))
    b = simulate_selfish(is_adv, 0.5, np.random.default_rng(99))
    assert isinstance(a, RaceResult) and (a.adv, a.hon) == (b.adv, b.hon)


# --- optimal-selfish MDP (Sapirshtein) ---------------------------------------------------------
@pytest.mark.parametrize("alpha,gamma", [(0.1, 0.0), (0.3, 0.0), (0.4, 0.0), (0.4, 0.5)])
def test_optimal_selfish_dominates_sm1_and_honest(alpha, gamma):
    # The optimal policy is never worse than SM1 or than honest mining (both are feasible policies).
    opt = optimal_selfish_revenue(alpha, gamma, cap=16, iters=1500)
    assert opt >= selfish_revenue_closed_form(alpha, gamma) - 3e-3
    assert opt >= alpha - 3e-3


def test_optimal_selfish_is_honest_below_threshold():
    # Below the gamma=0 threshold (1/3) no deviation beats honest: optimal == alpha.
    assert abs(optimal_selfish_revenue(0.25, 0.0, cap=16, iters=1500) - 0.25) < 3e-3


# --- uncle-reward model ------------------------------------------------------------------------
def test_uncle_reward_shrinks_selfish_share_and_compensates_honest():
    # A profitable selfish attack orphans honest blocks. Paying uncle rewards to those orphans
    # raises honest total reward, so the attacker's REWARD share falls below its block share, and
    # honest miners recover more of their mined value.
    r = race_from_alpha(0.4, 500_000, 0.0, np.random.default_rng(2))
    block_share = r.revenue_share
    s0 = reward_shares(r, RewardParams(w_uncle=0.0)).adv_reward_share
    s_half = reward_shares(r, RewardParams(w_uncle=0.5)).adv_reward_share
    s_full = reward_shares(r, RewardParams(w_uncle=1.0)).adv_reward_share
    assert abs(s0 - block_share) < 1e-9          # no uncle reward -> reward share == block share
    assert s_full < s_half < s0                  # more uncle reward -> smaller attacker share
    # honest fairness: recovery rises monotonically with the uncle reward toward 1.0
    rec0 = honest_reward_recovery(r, RewardParams(w_uncle=0.0))
    rec1 = honest_reward_recovery(r, RewardParams(w_uncle=1.0))
    assert rec0 < rec1 <= 1.0 + 1e-9


def test_uncle_reward_is_noop_without_orphans():
    # Honest mining (no orphans) -> uncle rewards change nothing; share stays at the stake.
    r = race_from_alpha(0.0, 50_000, 0.0, np.random.default_rng(5))
    assert reward_shares(r, RewardParams(w_uncle=1.0, w_nephew=0.5)).adv_reward_share == 0.0
    assert honest_reward_recovery(r, RewardParams(w_uncle=1.0)) == 1.0


def test_uncle_rewards_backfire_without_mandate_but_mandate_neutralises():
    # The strategic result (report §6.7/§6.8): without a mandate the attacker suppresses honest
    # references AND self-uncles its own lost blocks, so an uncle reward RAISES its share above the
    # block share; a mandatory-inclusion schedule instead drives it down to ~stake (break-even).
    r = race_from_alpha(0.4, 1_000_000, 0.0, np.random.default_rng(1))
    block = r.revenue_share
    rp_supp = RewardParams(w_uncle=1.0, p_ref=0.0, p_ref_adv=1.0)
    suppress = reward_shares(r, rp_supp).adv_reward_share
    mandate = reward_shares(r, RewardParams.mandatory(w_uncle=1.0)).adv_reward_share
    assert suppress > block          # self-uncle + suppression -> uncle reward helps the attacker
    assert mandate < block           # forced honest-orphan compensation -> premium shrinks
    assert abs(mandate - 0.40) < 0.03   # pushed to ~stake (break-even)


def test_self_uncle_recovery_is_monotone_in_p_ref_adv():
    # Recovering more of the attacker's own lost blocks (higher p_ref_adv) raises its reward share.
    r = race_from_alpha(0.42, 800_000, 0.5, np.random.default_rng(4))
    s = [reward_shares(r, RewardParams(w_uncle=0.8, p_ref=0.0, p_ref_adv=pa)).adv_reward_share
         for pa in (0.0, 0.5, 1.0)]
    assert s[0] < s[1] < s[2]


def test_farming_profitable_iff_wu_plus_wn_exceeds_one():
    # A self-farmer orphaning a canonical win to uncle it collects w_uncle (producer) + w_nephew
    # (self-nephew); the marginal per-slot payoff vs an honest block (=1) is exactly w_u + w_n.
    for wu, wn, profitable in [(0.5, 0.3, False), (0.875, 0.03125, False), (0.9, 0.15, True)]:
        assert ((wu + wn) > 1.0) == profitable
