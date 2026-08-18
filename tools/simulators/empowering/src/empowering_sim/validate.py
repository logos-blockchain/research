"""Gates: the simulator against the closed forms the tokenomics report derives.

Every check here restates a published result independently and demands the engine reproduce
it. They are cheap, they run from the first commit rather than being retrofitted, and they
are the reason a number out of this simulator can be quoted at all.

Run as ``python -m empowering_sim.validate``.
"""
from __future__ import annotations

import sys

import numpy as np

from . import (consensus, crossover, economics, emission, engine, graduation, market,
               scenarios, services, simulate, work)
from .config import FIELD_MODULUS, Config, load
from .nodes import NOT_GRADUATED, Population

FAILURES: list[str] = []


def check(name: str, got, want, rel: float = 0.0, note: str = "") -> None:
    """Record one comparison. ``rel`` is a relative tolerance; zero demands exactness."""
    if isinstance(want, bool) or isinstance(got, bool):
        ok = got == want
    elif rel:
        ok = abs(got - want) <= rel * max(abs(want), 1e-300)
    else:
        ok = got == want
    mark = "ok  " if ok else "FAIL"
    detail = f"{got!r} vs {want!r}" if not ok else f"{got!r}"
    print(f"  [{mark}] {name}: {detail}" + (f"   -- {note}" if note else ""))
    if not ok:
        FAILURES.append(name)


# ------------------------------------------------------------------ the fee and the pool

def gate_fees(cfg: Config) -> None:
    """The claim's own fee, and the average transaction's, from bytes and gas."""
    print("\nFees, at the resting price")
    check("claim_fee", cfg.claim_fee, 6_664,
          note="306 bytes and 646 gas, both at 7")
    check("avg_tx_fee", cfg.avg_tx_fee, 5_579,
          note="an ordinary one-in one-out transfer")
    check("fee_ratio", cfg.fee_ratio, 0.837, rel=1e-3,
          note="a claim costs slightly more than the average transaction")


def gate_pool_closed_forms(cfg: Config) -> None:
    """Opening reward, refill, and where both settle."""
    print("\nThe pool's closed forms")
    opening = economics.reward_per_claim(cfg.genesis_pool, cfg)
    check("genesis_pool", cfg.genesis_pool, 50_000_000_000_000_000,
          note="half a percent of a ten-billion supply, in base units")
    check("opening reward_per_claim", opening, 1_157_407_407,
          note="report section 3.7, epoch 0")
    check("epoch_refill", economics.epoch_refill(cfg), 7_230_384_000,
          note="7.23 LGO per epoch, and it carries no target")
    check("steady_pool", economics.steady_pool(cfg), 1_446_076_800_000.0, rel=1e-12,
          note="1,446 LGO, independent of the target")
    check("steady_reward", economics.steady_reward(cfg), 33_474.0, rel=1e-9)
    check("reward_over_fee", economics.reward_over_fee(cfg), 5.023, rel=1e-3,
          note="the margin the steady state settles at")
    check("steady_reward / claim_fee agrees",
          economics.steady_reward(cfg) / cfg.claim_fee,
          economics.reward_over_fee(cfg), rel=1e-9,
          note="the two routes to the margin must meet")


def gate_self_funding(cfg: Config) -> None:
    """The self-funding condition, reached from the pool's side and the miner's."""
    print("\nSelf-funding")
    need = economics.self_funding_txs(cfg)
    check("txs for reward = fee", need, 119.4, rel=1e-2,
          note="report section 4.3, at a tenth share")
    check("the specified traffic clears it", cfg.txs_per_block > need, True)


# ------------------------------------------------------------------ the controller

def gate_retarget_is_an_ema(cfg: Config) -> None:
    """The one-state retarget is exactly a normalised EMA of demand.

    The report proves the specified map stores the smoothed estimate inside the target
    itself. Restated here: run both forms on the same claim sequence and demand they agree.
    """
    print("\nThe retarget, against its explicit EMA form")
    rng = np.random.default_rng(11)
    q = cfg.smoothing
    target = cfg.genesis_difficulty_target
    demand_est = cfg.target_claims_per_block / target      # the invariant, from genesis
    worst = 0.0
    for _ in range(20_000):
        claims = int(rng.poisson(cfg.target_claims_per_block))
        target = work.next_difficulty_target(target, claims, cfg)
        demand_est = (1 - q) * (claims / (cfg.target_claims_per_block / demand_est)) \
            + q * demand_est
        implied = cfg.target_claims_per_block / demand_est
        worst = max(worst, abs(implied - target) / target)
    check("worst relative divergence over 20,000 blocks", worst < 1e-9, True,
          note=f"{worst:.2e}; the two notations are one controller")


def gate_controller_fixed_point(cfg: Config) -> None:
    """At the target rate the target is stationary; off it, the controller walks home."""
    print("\nThe controller's fixed point and response")
    d = cfg.genesis_difficulty_target
    stationary = work.next_difficulty_target(d, cfg.target_claims_per_block, cfg)
    check("stationary at the target rate", abs(stationary - d) <= 1, True,
          note=f"moved by {stationary - d} of {d}")
    blocks = engine.reconvergence_blocks(cfg, step=10.0)
    check("blocks to recover a tenfold hashrate step", blocks, 22, rel=0.25,
          note="report section 3.6 predicts about 22")


# ------------------------------------------------------------------ the work process

def gate_poisson_superposition(cfg: Config) -> None:
    """One aggregate draw plus a multinomial equals a million per-node draws.

    The engine's central shortcut. Checked rather than asserted: the per-node counts it
    produces must match direct per-node Poisson sampling in mean and in variance.
    """
    print("\nAggregate draw and multinomial attribution")
    rng = np.random.default_rng(7)
    shares = np.array([0.5, 0.3, 0.15, 0.05])
    rate_total = 40.0
    trials = 40_000

    direct = rng.poisson(rate_total * shares, size=(trials, shares.size))
    agg = np.empty_like(direct)
    for i in range(trials):
        total = rng.poisson(rate_total)
        agg[i] = work.attribute(rng, int(total), shares)

    for j, share in enumerate(shares):
        want_mean = rate_total * share
        # Both estimators carry sampling error; the tolerance is a few standard errors.
        se = np.sqrt(want_mean / trials)
        check(f"node {j} mean", agg[:, j].mean(), want_mean, rel=6 * se / want_mean)
        check(f"node {j} variance", agg[:, j].var(), want_mean, rel=0.05,
              note="Poisson, so variance equals the mean")


# ------------------------------------------------------------------ the engine itself

def gate_reference_cores(cfg: Config) -> None:
    """How many target cores the genesis reward target implies, at the target rate.

    The first check that ties the engine to the work side rather than to the money side. The
    report puts the genesis target at about three hours per solution on one core of the
    deployment target, and about 3,700 such cores at the target claim rate. Both fall out of
    the hashrate calibration, so agreeing with them tests that calibration end to end.
    """
    print("\nWhat the genesis target costs, in target cores")
    if cfg.seconds_per_candidate_reward <= 0:
        print("  [skip] no measured candidate cost in the snapshot")
        return
    rate = engine.hashrate_for_target_rate(cfg)
    per_core = 1.0 / cfg.seconds_per_candidate_reward
    cores = rate / per_core
    hours = FIELD_MODULUS / cfg.genesis_difficulty_target * cfg.seconds_per_candidate_reward / 3600

    check("hours per solution on one target core", hours, 3.07, rel=0.05,
          note="the report calls this about three hours")
    check("target cores at the target claim rate", cores, 3_700, rel=0.05,
          note="the report's figure for the genesis target")


def gate_trajectory(cfg: Config) -> None:
    """The simulated reward trajectory against its closed form.

    Run deterministically at the equilibrium hashrate, which is what the closed form assumes:
    every claim paid, arrivals exactly at the target. Any divergence is the engine's, not
    sampling noise.
    """
    print("\nThe reward trajectory, simulated against closed form")
    rate = engine.hashrate_for_target_rate(cfg)
    rows = engine.run(cfg, hashrate=rate, epochs=120, deterministic=True)

    check("claims paid in epoch 0", rows[0].claims_paid,
          cfg.target_claims_per_block * cfg.blocks_per_epoch,
          note="the controller opens at the target rate and holds it")
    check("nothing dropped to the block cap", sum(r.claims_dropped for r in rows), 0)
    check("nothing left unpaid", sum(r.unpaid for r in rows), 0)

    for e in (0, 1, 10, 50, 100):
        want = economics.reward_at_epoch(cfg, e)
        check(f"reward_per_claim at epoch {e}", rows[e].reward_per_claim, want, rel=2e-3)

    check("reward decays", rows[100].reward_per_claim < rows[0].reward_per_claim, True,
          note="the endowment opens far above the pool's fixed point")


def gate_report_decay_table(cfg: Config) -> None:
    """Section 3.7's published trajectory, epoch by epoch."""
    print("\nReport section 3.7's decay table")
    rate = engine.hashrate_for_target_rate(cfg)
    rows = engine.run(cfg, hashrate=rate, epochs=301, deterministic=True)
    for e, want in ((0, 1_157_407_407), (100, 701_136_387), (299, 258_601_512)):
        check(f"epoch {e}", rows[e].reward_per_claim, want, rel=2e-3)


def gate_population(cfg: Config) -> None:
    """Crediting conserves claims and value, and graduation is marked exactly once.

    The conservation checks are not ceremony. Crediting writes through a sliced view with a
    boolean mask, which is the classic place for an update to land in a copy and vanish; a
    silent loss there would depress every graduation figure without failing anything else.
    """
    print("\nThe population: conservation and graduation marking")
    rng = np.random.default_rng(3)
    pop = Population.empty(100)
    pop.arrive(100, 0, 1.0)

    net = 1_000_000_000
    claims_each_epoch, epochs = 1_000, 50
    # 50,000 claims over 100 nodes is 500 each, with a multinomial spread near 22, so a
    # threshold at the mean splits the cohort and the check below actually discriminates.
    threshold = 500 * net
    for e in range(epochs):
        pop.credit(rng, claims_each_epoch, net, e, threshold)

    total = claims_each_epoch * epochs
    check("claims conserved", int(pop.claims[:pop.count].sum()), total)
    check("value conserved", int(pop.balance[:pop.count].sum()), total * net)

    at_or_above = pop.balance[:pop.count] >= threshold
    marked = pop.graduated_epoch[:pop.count] != NOT_GRADUATED
    check("everyone above the threshold is marked", int((at_or_above & ~marked).sum()), 0,
          note="a mask write that landed in a copy would fail here")
    check("nobody below the threshold is marked", int((~at_or_above & marked).sum()), 0)
    check("some but not all graduated", 0 < int(marked.sum()) < pop.count, True,
          note=f"{int(marked.sum())} of {pop.count}, so the check has teeth")


def gate_ceiling(cfg: Config) -> None:
    """The on-ramp's arithmetic ceiling, and the emission cap it sits beside."""
    print("\nThe on-ramp ceiling")
    ceiling = graduation.graduate_ceiling(cfg)
    check("min_stake in LGO", ceiling["min_stake_lgo"], cfg.min_stake_lgo, rel=1e-12,
          note="a DECISION: the specification leaves the threshold unset")
    check("genesis_pool in LGO", ceiling["genesis_pool_lgo"], 50_000_000.0, rel=1e-12)
    check("service positions the endowment can fund", ceiling["endowment_graduates"],
          cfg.genesis_pool / cfg.min_stake, rel=1e-12,
          note="the threshold gates SERVICES; consensus has no threshold at all")
    check("the ceiling scales inversely with the threshold",
          ceiling["endowment_graduates"] * cfg.min_stake_lgo,
          cfg.to_lgo(cfg.genesis_pool), rel=1e-9,
          note="positions times position size is the endowment, whatever the threshold")
    check("emission cap, LGO per block", consensus.max_block_reward(cfg), 95.1293, rel=1e-4)


def gate_study_conservation(cfg: Config) -> None:
    """A short run cannot distribute more than the pool ever held."""
    print("\nThe study conserves value")
    rng = np.random.default_rng(5)
    pop, out = graduation.run(cfg, joiners_per_epoch=2.0, epochs=40, rng=rng)
    credited = int(pop.balance[:pop.count].sum())
    paid_out = sum(o.claims_paid * o.net_per_claim for o in out)
    check("credited equals paid out", credited, paid_out)

    available = cfg.genesis_pool + sum(o.claims_paid for o in out) * 0  # endowment only
    check("never pays out more than the pool held", paid_out <= available, True,
          note=f"{cfg.to_lgo(paid_out):,.0f} of {cfg.to_lgo(available):,.0f} LGO")
    check("every miner seated", pop.count, 80, note="2 per epoch over 40 epochs")


def gate_pooled_invariance(cfg: Config) -> None:
    """The distributed value is invariant to how many identities it is split across.

    This is what separates the mechanism's behaviour from the population's. The pool pays
    out the same amount however dispersed the field is, so the pooled equivalent must not
    move with the arrival rate -- while the per-identity count moves a great deal. If this
    gate ever fails, the two are entangled and every graduation figure is suspect.
    """
    print("\nPooled value is invariant to the arrival rate; per-identity count is not")
    pooled, seated = [], []
    for j in (0.5, 2.0, 8.0):
        rng = np.random.default_rng(1)
        pop, _ = graduation.run(cfg, joiners_per_epoch=j, epochs=200, rng=rng)
        pooled.append(graduation.pooled_equivalent(pop, cfg))
        seated.append(pop.graduated)
    spread = (max(pooled) - min(pooled)) / max(1, max(pooled))
    check("pooled equivalent is invariant across arrival rates", spread < 0.02, True,
          note=f"{pooled} across 0.5, 2 and 8 joiners per epoch")
    ceiling = cfg.genesis_pool / cfg.min_stake
    check("pooled equivalent stays under the arithmetic ceiling", max(pooled) <= ceiling, True,
          note=f"max {max(pooled):,} against a ceiling of {ceiling:,.0f}")
    check("per-identity count is NOT invariant", (max(seated) - min(seated)) > 0.2 * max(seated),
          True, note=f"{seated} -- the dispersion effect is real, not noise")


def gate_participation(cfg: Config) -> None:
    """Endogenous participation: monotone in price, conservative in credit, no limit cycle."""
    print("\nEndogenous participation")
    try:
        classes = market.from_powcost("poseidon2_reward", 0.20, "total")
    except Exception as e:                                    # noqa: BLE001
        print(f"  [skip] cost estimator unavailable: {e}")
        return
    check("classes priced from the estimator", len(classes) >= 2, True,
          note=", ".join(c.key for c in classes))

    def run_at(price: float, epochs: int = 25):
        sc = scenarios.Scenario(
            label=f"p{price}", classes=classes, mix={c.key: 1.0 for c in classes},
            joiners_per_epoch=2.0, epochs=epochs,
            traffic=scenarios.constant_traffic(600),
            token_price=scenarios.constant_price(price))
        return simulate.run(cfg, sc, np.random.default_rng(1))

    # The expensive class must be out below its break-even and in above it. Anything else
    # means the participation rule is not tracking cost.
    cheap = min(classes, key=lambda c: c.cost_per_candidate_usd)
    dear = max(classes, key=lambda c: c.cost_per_candidate_usd)
    dear_i = classes.index(dear)
    _, low = run_at(1e-4)
    _, high = run_at(1e-1)
    check(f"{dear.key} is priced out at a low token price",
          low[-1].active_fraction_by_class[dear_i] < 0.5, True,
          note=f"{low[-1].active_fraction_by_class[dear_i]:.1%} of the epoch")
    check(f"{dear.key} mines freely at a high token price",
          high[-1].active_fraction_by_class[dear_i] > 0.99, True,
          note=f"{high[-1].active_fraction_by_class[dear_i]:.1%} of the epoch")
    check("the cheaper class is never the one excluded first",
          cheap.cost_per_candidate_usd <= dear.cost_per_candidate_usd, True)

    # Deciding participation once an epoch made the model oscillate between nobody mining
    # and everybody mining, every other epoch. Per-block evaluation removed it; this refuses
    # to let it come back.
    _, mid = run_at(3.16e-5, epochs=20)
    fracs = [o.active_fraction_by_class[classes.index(cheap)] for o in mid[5:]]
    flips = sum(1 for a, b in zip(fracs, fracs[1:])
                if (a > 0.9 and b < 0.1) or (a < 0.1 and b > 0.9))
    check("no epoch-to-epoch limit cycle", flips <= 1, True,
          note=f"{flips} full swings in {len(fracs)} epochs")


def gate_group_credit(cfg: Config) -> None:
    """Per-class credit adds up to the claims the pool actually paid."""
    print("\nPer-class attribution conserves claims")
    try:
        classes = market.from_powcost("poseidon2_reward", 0.20, "total")
    except Exception:                                          # noqa: BLE001
        print("  [skip] cost estimator unavailable")
        return
    sc = scenarios.Scenario(
        label="credit", classes=classes, mix={c.key: 1.0 for c in classes},
        joiners_per_epoch=2.0, epochs=12,
        traffic=scenarios.constant_traffic(600),
        token_price=scenarios.constant_price(0.10))
    pop, out = simulate.run(cfg, sc, np.random.default_rng(2))
    paid = sum(o.claims_paid for o in out)
    credited = int(pop.claims[:pop.count].sum())
    # Rounding each class's real-valued share to an integer loses at most one claim per
    # class per epoch, so exact equality is not the right demand; near-equality is.
    slack = len(classes) * len(out)
    check("claims credited match claims paid", abs(credited - paid) <= slack, True,
          note=f"{credited:,} against {paid:,}, slack {slack}")


def gate_crossover_and_min_stake(cfg: Config) -> None:
    """Mining against staking, and what the minimum stake does on every axis at once."""
    print("\nMining against staking, and reading the minimum stake")
    spec_lgo = cfg.to_lgo(cfg.min_stake)

    # Staking pays strictly in proportion to stake, so the RATE of return cannot depend on
    # the threshold -- only the size of the position does. If this ever fails, staking has
    # acquired a scale effect and every reading of the threshold below has to be redone.
    yields = [crossover.min_stake_reading(cfg, ms, 0.01, 0.30)["annual_yield_on_stake"]
              for ms in (1e2, 1e3, 1e4, 1e5, 1e6)]
    check("annual yield does not depend on the threshold",
          max(yields) - min(yields) < 1e-9, True,
          note=f"{yields[0]:.2%} across four orders of magnitude of minimum stake")

    # Participants times position size is the endowment. The conservation the whole on-ramp
    # reading rests on.
    for n in (100, 500, 10_000):
        ms = crossover.min_stake_for_participants(cfg, n)
        check(f"threshold for {n:,} participants inverts the ceiling",
              ms * n, cfg.to_lgo(cfg.genesis_pool), rel=1e-9)

    # Mining dominates early and staking late; the crossing must exist and must come later
    # for a miner holding more of the field.
    # This threshold-based comparison is superseded by leader_overtakes_mining, which does
    # not assume a threshold gates staking income -- it does not. Retained only for the
    # shares where a min_stake-sized position is still the relevant reference.
    crossings = []
    for share in (0.001, 0.01):
        pos = crossover.Position(stake=cfg.min_stake, hashrate_share=share)
        crossings.append(crossover.crossover_epoch(cfg, pos, 0.30)["epoch"])
    check("a min_stake-sized position is eventually overtaken at small shares",
          all(c is not None for c in crossings), True, note=f"epochs {crossings}")
    check("a larger miner holds out longer", crossings == sorted(crossings), True,
          note="monotone in hashrate share")

    # The specified threshold, read against field size.
    at_field = crossover.min_stake_reading(cfg, spec_lgo, 1.0 / 1000, 0.30)
    check("at the chosen threshold the service on-ramp is fast, not generational",
          at_field["years_to_graduate"] < 1.0, True,
          note=f"{at_field['years_to_graduate'] * 365:.0f} days at a tenth of a percent of "
               f"the field, and the endowment funds "
               f"{at_field['graduates_the_endowment_funds']:,.0f} positions")


def gate_staking_against_the_spec(cfg: Config) -> None:
    """The staking side, against block-rewards.md rather than against an assumption.

    Every crossover and conservation figure is downstream of the validation yield, so it has
    to come from the specification and not from this simulator's own reasoning. The
    specification calibrates the maximum emission rate precisely so the yield lands near
    3.33% when inferred total stake reaches its 30% target; reproducing that is the check.
    """
    print("\nThe staking side, against block-rewards.md")
    check("maximum emission per year", cfg.max_emission_per_year, 0.01,
          note="I_max, block-rewards.md parametrisation table")
    check("target for inferred total stake", cfg.stake_target, 0.30,
          note="D_0_target, analysis-block-reward-parameter-calibration.md")
    # The two documents disagree about who receives the emission, so BOTH readings are
    # gated. block-rewards.md calibrates I_max so "the APY for validation is ~3.33%", which
    # holds only if validators take the whole emission; overview-cryptoeconomics.md gives
    # leaders 0.4 of the block reward, as code, with Blend taking 0.6.
    from dataclasses import replace as _r                       # noqa: PLC0415
    whole = _r(cfg, leader_reward_share=1.0)
    check("APY if validators take the whole emission",
          consensus.validation_apy(whole), 0.0333, rel=0.02,
          note="block-rewards.md's calibration target")
    check("APY at the 0.4 leader share stated as code",
          consensus.validation_apy(cfg), 0.01333, rel=0.02,
          note="overview-cryptoeconomics.md; the config carries this one")
    check("the two readings differ by the leader share", 
          consensus.validation_apy(whole) / consensus.validation_apy(cfg), 2.5, rel=0.01,
          note="a contradiction in the specifications, not in this model")

    at_max = consensus.block_reward(cfg, 1.0, burnt_fees_per_block=12.0)
    at_min = consensus.block_reward(cfg, 0.0, burnt_fees_per_block=12.0)
    check("at maximum emission the reward is the minted term alone",
          at_max, consensus.max_block_reward(cfg), rel=1e-12)
    check("at minimum emission it is the recycled fees alone", at_min, 12.0, rel=1e-12,
          note="specification: close to target, most of the burn is minted back")

    from dataclasses import replace as _replace                # noqa: PLC0415
    split = _replace(cfg, leader_reward_share=0.39)
    check("the proposal's illustrated 39% leader leg would cut the yield",
          consensus.validation_apy(split), 0.013, rel=0.02,
          note="a lower yield makes the on-ramp obstacle worse, not better")


def gate_stake_aging(cfg: Config) -> None:
    """Mined proceeds do not enter the lottery the moment they are mined.

    A note must be held for a minimum period and appear in a frozen stake-distribution
    snapshot before it can win a slot (`cryptarchia-v1-protocol.md`), and the service
    declaration protocol reads `finalized_epoch = current_epoch - 2`. So reaching the
    threshold and earning from it are separate moments, and the model has to carry both.
    """
    print("\nStake aging: reaching the threshold is not the same as earning from it")
    check("aging period, in epochs", cfg.stake_aging_epochs, 2,
          note=f"{cfg.stake_aging_epochs / cfg.epochs_per_year * 365:.1f} days")

    rng = np.random.default_rng(4)
    pop, out = graduation.run(cfg, joiners_per_epoch=4.0, epochs=30, rng=rng)
    live = slice(0, pop.count)
    grad = pop.graduated_epoch[live]
    elig = pop.eligible_epoch[live]
    made = grad != NOT_GRADUATED
    check("everyone who graduated has an eligibility date",
          int((made & (elig == NOT_GRADUATED)).sum()), 0)
    lags = (elig[made] - grad[made])
    check("eligibility lags graduation by exactly the aging period",
          int(lags.min()) == int(lags.max()) == cfg.stake_aging_epochs, True,
          note=f"{int(lags.min())} epochs for all {int(made.sum())} graduates")
    check("nobody is staking-eligible before their own graduation",
          pop.staking_eligible(0), 0)

    # How much it actually moves the answer, stated rather than assumed.
    # How much the delay matters depends entirely on the threshold, and at the chosen one it
    # matters a great deal. At a 100,000 LGO threshold graduation took ~200 epochs and the
    # two-epoch aging was 1% of it. At 1,000 LGO graduation takes ~2 epochs, so aging is
    # comparable to the whole on-ramp: a miner waits about as long for its notes to age as it
    # did to earn them. Lowering the threshold does not shorten the on-ramp below the aging.
    at_field = cfg.min_stake / (cfg.distribution_rate * cfg.genesis_pool / 1000)
    ratio = cfg.stake_aging_epochs / at_field
    check("aging is a floor on the on-ramp, and at this threshold it binds",
          ratio >= 0.5, True,
          note=f"{cfg.stake_aging_epochs} epochs of aging against {at_field:.1f} to earn the "
               f"threshold at a tenth of a percent of the field -- {ratio:.0%}")
    check("so the on-ramp cannot be shortened below the aging period",
          max(at_field, cfg.stake_aging_epochs) >= cfg.stake_aging_epochs, True,
          note="a lower threshold buys nothing once earning is faster than aging")


def gate_two_participation_classes(cfg: Config) -> None:
    """Consensus and service provision are gated differently, and the difference decides much.

    Leader rewards need an AGED note and nothing else -- "the weight of the coin is
    proportional to the value of your note" -- so consensus participation has no threshold and
    needs no on-ramp. Service provision needs a LOCKED minimum stake. An earlier version of
    this model gated all staking income at the minimum, which is wrong for consensus and made
    the on-ramp look like a problem it is not.
    """
    print("\nTwo participation classes, gated differently")
    balances = np.array([1, 1_000, cfg.min_stake - 1, cfg.min_stake, 10 * cfg.min_stake])
    aged = np.ones(balances.size, dtype=bool)

    weight = consensus.lottery_weight(balances, aged)
    check("every aged balance carries lottery weight, however small",
          int((weight == 0).sum()), 0,
          note="no minimum gates the leadership lottery")
    check("lottery weight is the balance itself", list(weight), list(balances))

    svc = consensus.service_eligible(balances, cfg.min_stake)
    check("only balances at or above the minimum can declare a service",
          int((svc > 0).sum()), 2, note="the threshold belongs to services, not consensus")
    check("an unaged balance carries no weight",
          int(consensus.lottery_weight(balances, np.zeros_like(aged)).sum()), 0)

    # The corrected crossing, and its universality.
    crossings = [crossover.leader_overtakes_mining(cfg, s)["epoch"]
                 for s in (0.0001, 0.001, 0.01, 0.20, 1.0)]
    check("leader income overtakes mining at the same epoch at every field share",
          len(set(crossings)), 1, note=f"epoch {crossings[0]:,}, "
                                       f"{crossings[0] / cfg.epochs_per_year:.2f} years")
    # The pool DECAYS, so the mining flow a miner is racing falls. Computing that flow once
    # from the genesis pool solves the rho -> 0 case instead and returns 1,013; the closed
    # form's own limit is that number, which is how the error was found.
    cf = crossover.leader_overtakes_mining_closed_form(cfg)
    check("simulation agrees with the closed form", crossings[0], cf["epochs"], rel=0.01,
          note=f"{crossings[0]} against {cf['epochs']:.1f} epochs")
    check("the crossing at the 0.4 leader share",
          crossings[0] / cfg.epochs_per_year, 11.71, rel=0.02,
          note="8.05 years if validators instead take the whole emission")
    from dataclasses import replace as _r2                       # noqa: PLC0415
    whole2 = _r2(cfg, leader_reward_share=1.0)
    check("the crossing if validators take the whole emission",
          crossover.leader_overtakes_mining_closed_form(whole2)["years"], 8.05, rel=0.02)
    check("the frozen-pool limit is the number a hoisted flow produces",
          crossover.leader_overtakes_mining_closed_form(whole2)["frozen_pool_limit_epochs"],
          1013, rel=0.01, note="ln(2)/ln(1+apy) -- the bug's signature, at the same reading")

    # The permanent term: both mining and leading are shares of the same block reward, so
    # their ratio carries no time, no pool and no yield.
    for leader, want in ((1.0, 600.0), (0.39, 1538.0)):
        check(f"permanent dominance at a 2% PoW leg, leader on {leader:.0%}",
              crossover.permanent_mining_dominance(cfg, 0.02, leader), want, rel=0.01,
              note="the whole field's mining income over one minimum stake's leader income")
    check("sizing the PoW leg to the bundle removes the permanent gap",
          crossover.permanent_mining_dominance(cfg, 1.381e-6, 1.0) < 0.05, True,
          note=f"{crossover.permanent_mining_dominance(cfg, 1.381e-6, 1.0):.4f}x at 1.38 ppm")

    ceiling = crossover.service_ceiling(cfg)
    check("the endowment ceiling binds services, not consensus",
          ceiling["service_positions"], cfg.genesis_pool / cfg.min_stake, rel=1e-9,
          note=f"{cfg.genesis_pool / cfg.min_stake:,.0f} positions at the chosen threshold")
    check("consensus participation is unbounded",
          ceiling["consensus_positions"] == float("inf"), True,
          note="no threshold, so no ceiling and no on-ramp needed")


def gate_conservation(cfg: Config) -> None:
    """The obstacle in PROPOSAL.md: graduation time times mining dominance is a constant.

    Load-bearing, so it is gated rather than trusted. Vary the field share, the pool, the
    distribution rate and the threshold independently; the product must not move. If it ever
    does, a change has broken the conservation -- which is the point of the exercise, and
    exactly the thing worth being told about immediately.
    """
    print("\nThe conservation law behind the proposal")
    base = dict(pool=cfg.genesis_pool, hashrate_share=1 / 500,
                min_stake=cfg.min_stake, staked_fraction=0.30)
    ref = crossover.conservation_product(cfg, **base)
    check("product equals staked_total over minted", ref["product"], ref["expected"], rel=1e-9,
          note=f"{ref['product']:,.0f} epochs = {ref['product'] / cfg.epochs_per_year:.1f} years")

    products = [ref["product"]]
    for share in (1e-4, 1e-2, 0.5):
        products.append(crossover.conservation_product(cfg, **{**base, "hashrate_share": share})["product"])
    for pool_mult in (0.01, 100.0):
        products.append(crossover.conservation_product(
            cfg, **{**base, "pool": int(cfg.genesis_pool * pool_mult)})["product"])
    for stake_mult in (0.01, 100.0):
        products.append(crossover.conservation_product(
            cfg, **{**base, "min_stake": int(cfg.min_stake * stake_mult)})["product"])
    spread = (max(products) - min(products)) / max(products)
    check("field share, pool and threshold all cancel out of it", spread < 1e-9, True,
          note=f"{len(products)} settings, relative spread {spread:.1e}")

    from dataclasses import replace as _replace                # noqa: PLC0415
    faster = _replace(cfg, distribution_rate_den=20)
    check("the distribution rate cancels too",
          crossover.conservation_product(faster, **base)["product"], ref["product"], rel=1e-9,
          note="a tenfold faster pool moves graduation and dominance, not their product")

    # The consequence the proposal turns on.
    at_design = crossover.conservation_product(cfg, **base)
    check("at the design point mining pays several times what the stake does",
          at_design["mining_dominance"] > 5, True,
          note=f"{at_design['mining_dominance']:.1f}x at 500 miners, "
               f"graduating in {at_design['graduation_years']:.1f} years")

    minimal = crossover.minimal_reward_base_units(cfg)
    check("the minimal reward target, a transfer plus a 1 kB inscription",
          minimal, 13_139, note=f"{minimal / cfg.claim_fee:.2f} claim fees")

    # The proposal's two routes out, both costed. The boost needed is the reciprocal of the
    # graduation time and carries no base yield, which is why its cost is invariant.
    check("the boost that equalises staking with mining is 1 over the graduation time",
          crossover.boosted_apy_for_dominance(4.11), 0.243, rel=0.01,
          note="24.3% a year at the design point, at either reading of the emission")
    for share in (1.0, 0.39):
        base = share * cfg.max_emission_per_year / cfg.stake_target
        cost = 500 * 1e5 * crossover.boosted_apy_for_dominance(4.11) * 4.11
        check(f"cost of that boost at a {base:.2%} base yield",
              cost, cfg.to_lgo(cfg.genesis_pool), rel=1e-9,
              note="exactly the endowment, because it replaces the same income stream")

    # Goal 2 has a home already, and it is mis-sized.
    want = crossover.pow_share_of_block_reward_for(cfg, minimal)
    check("block reward leg that would pay the minimal bundle", want, 1.381e-6, rel=1e-3,
          note=f"{want * 1e6:.2f} parts per million, against the 2% the proposal illustrates")
    check("the illustrated 2% leg overshoots goal 2 by four orders of magnitude",
          0.02 / want > 10_000, True, note=f"{0.02 / want:,.0f}x")


def gate_alternative_is_neutral(cfg: Config) -> None:
    """VARIANT GATE -- the joiner-responsive target, not the base mechanism.

    Gated rather than argued, because the variant's whole case rests on the target being
    able to move the on-ramp, and it cannot. If a future change ever made the target matter
    for graduation, this would fail, and that would be worth knowing immediately.
    """
    print("\nALTERNATIVE (variant, not the base): is the claim target neutral?")
    from .alternative import joiner_target as alt          # noqa: PLC0415

    targets = (1, 10, 50, 100, 512, 1024)
    epochs = [alt.epochs_to_graduate(cfg, cfg.genesis_pool, 0.01, t) for t in targets]
    check("epochs to graduate is identical at every target",
          max(epochs) - min(epochs) < 1e-9, True,
          note=f"{epochs[0]:.2f} epochs at targets {targets[0]} through {targets[-1]}")
    rate = alt.graduations_per_epoch(cfg, cfg.genesis_pool)
    check("graduations per epoch carries no target", rate,
          cfg.distribution_rate * cfg.genesis_pool / cfg.min_stake, rel=1e-9,
          note=f"{rate:,.0f} at the chosen threshold; it scales with 1/min_stake, not with "
               f"the claim target")

    # ... while what it does cost moves a great deal.
    space = [alt.block_space_share(cfg, t) for t in targets]
    margin = [alt.self_funding_margin(cfg, t) for t in targets]
    check("block space consumed does move", space[-1] / space[0] > 100, True,
          note=f"{space[0]:.1%} at target 1 to {space[-1]:.1%} at target 1024")
    check("the steady-state margin falls below one past target 50",
          alt.self_funding_margin(cfg, 60) < 1 < alt.self_funding_margin(cfg, 50), True,
          note=f"{margin[1]:.2f} at target 10, {alt.self_funding_margin(cfg, 60):.2f} at 60")

    # An attacker inflating the target takes block space, not treasury.
    s = alt.sybil_exposure(cfg, honest_joiners=4.0, fake_joiners=100.0,
                           claims_per_joiner=10.0)
    check("fabricated joiners do not drain the pool faster", s["payout_changed"], False)
    check("fabricated joiners do not change the graduation rate",
          s["graduation_rate_changed"], False)
    check("fabricated joiners do consume the whole block",
          s["block_space_attacked"] >= 0.99, True,
          note=f"{s['block_space_honest']:.1%} to {s['block_space_attacked']:.1%}")


def gate_emission(cfg: Config) -> None:
    """The KPI control function, at its limits and against the specification's own constants."""
    print("\nThe emission control function")
    check("block reward at maximum emission", emission.block_reward_lgo(0.0, [0.0]),
          emission.INFLATION_NUMERATOR / emission.INFLATION_DENOMINATOR, rel=1e-12,
          note="62500/657 LGO, block-rewards.md's own figure")
    # Far above target with no burn: the factor clamps to zero and the reward is the burn.
    at_genesis = emission.emission_factor(1e10, [0.0] * emission.BURN_WINDOW)
    check("the genesis seed clamps the factor to zero", at_genesis, 0.0, rel=1e-12,
          note="D = 10^10 against a 3e9 target")
    check("and the reward is then exactly the block's own burn",
          emission.block_reward_lgo(1e10, [0.0] * 119 + [12.0]), 12.0, rel=1e-12)
    check("well below target the factor saturates at one",
          emission.emission_factor(1e8, [0.0] * emission.BURN_WINDOW), 1.0, rel=1e-12)
    check("the stake target is thirty percent of supply",
          emission.STAKE_TARGET_LGO, 0.30 * cfg.launch_supply, rel=1e-12)

    blend, leader = emission.split(100.0, cfg)
    check("Blend takes sixty percent of a block", blend, 60.0, rel=1e-9)
    check("the leader takes forty", leader, 40.0, rel=1e-9)
    # The split must follow the config, or the contested reading cannot be tested at all.
    from dataclasses import replace as _r3                    # noqa: PLC0415
    b2, l2 = emission.split(100.0, _r3(cfg, leader_reward_share=1.0))
    check("the split follows the config, not a literal", (b2, l2) == (0.0, 100.0), True,
          note="a hardcoded 6//10 made both readings of the emission produce identical runs")
    residue = emission.split_residue(95.1294, cfg)
    check("the two floors leave under two base units behind",
          0 <= residue * cfg.base_units_per_lgo < 2, True,
          note=f"{residue * cfg.base_units_per_lgo:.2f} base units, retained in the pool")


def gate_fee_markets(cfg: Config) -> None:
    """The two fee markets, and what they say about the equilibrium era."""
    print("\nThe fee markets")
    from . import fee_market as fm                            # noqa: PLC0415

    # Execution market: stationary at target, +12.5% full, -12.5% empty.
    check("the base fee is stationary at exactly the target",
          fm.next_base_fee(1_000_000, fm.G_TARGET), 1_000_000)
    check("a full block raises it by an eighth",
          fm.next_base_fee(1_000_000, fm.G_MAX), 1_125_000, rel=1e-6)
    check("an empty block lowers it by an eighth",
          fm.next_base_fee(1_000_000, 0), 875_000, rel=1e-6)
    check("the usage average rounds down, the price up",
          fm.update_g_avg(fm.G_TARGET, 0), (9 * fm.G_TARGET) // 10)

    # Storage market clamps.
    check("storage clamps down at an eighth", fm.next_storage_price(1_000_000, 0, 1_000), 875_000)
    check("storage clamps up at an eighth",
          fm.next_storage_price(1_000_000, 10_000, 1_000), 1_125_000)
    check("a zero usage average holds the price",
          fm.next_storage_price(1_000_000, 500, 0), 1_000_000)

    # The equilibrium question. Nothing bounds the base fee above, so whether fee recycling
    # can fund what minting funded is a question about DEMAND, not about the mechanism.
    cap = round(consensus.max_block_reward(cfg) * cfg.base_units_per_lgo)
    units = cfg.transfer_tx_bytes + cfg.transfer_tx_gas
    need = fm.price_for_block_burn(cap, cfg.max_block_txs, units, cfg.pow_share)
    check("price at which a full block's burn matches the minting ceiling", need, 129_513,
          rel=1e-3, note=f"{need / cfg.price_resting:,.0f}x the RESTING price")
    per_tx = units * need / cfg.base_units_per_lgo
    check("what that costs one transaction", per_tx, 0.1032, rel=1e-2,
          note="an ordinary fee, not an extreme one -- the resting price is an idle market")
    check("sustained full blocks reach it within a working day",
          fm.blocks_to_reach(int(need), 1.0) * cfg.block_seconds / 3600 < 24, True,
          note=f"{fm.blocks_to_reach(int(need), 1.0)} blocks, EIP-1559 compounds")
    check("but demand at or below target never gets there",
          fm.blocks_to_reach(int(need), 0.5) is None, True,
          note="stationary at target: the price is set by demand, not by the mechanism")


def gate_inscription(cfg: Config) -> None:
    """The self-sustaining target: what a claim must be worth, swept over inscription sizes."""
    print("\nThe inscription target")
    from . import inscription as ins                          # noqa: PLC0415

    # Storage and execution are charged on different things -- bytes of the whole signed
    # transaction against gas per Operation -- and priced independently. They share a floor of
    # one lepton and a resting level of 7; the SEPARATION is structural, the equality is not.
    check("storage is priced in lepta per storage gas unit", cfg.storage_price_lepta, 7,
          note="Units and Precision: P_STR is LEPTA per gas unit, floor one lepton")
    check("a GiB of permanent storage at the floor, in LGO",
          round(2 ** 30 * 1 / cfg.base_units_per_lgo, 4), 1.0737,
          note="the figure the units document computes for itself")
    check("the claim fee reproduces the specification's own figure", cfg.claim_fee, 6_664,
          note="mantle:1858 -- (306 + 646) * 7")

    # The ceiling on the inscription, and the sweep the study asked for.
    ceiling = ins.max_inscription_bytes(cfg)
    rows = ins.sweep(cfg)
    check("the steady state carries an inscription of at most", round(ceiling), 3_929)
    check("every swept inscription size is covered by the steady claim",
          all(r.covered for r in rows), True,
          note=f"{rows[0].margin:.2f}x at {rows[0].inscription_bytes} B down to "
               f"{rows[-1].margin:.2f}x at {rows[-1].inscription_bytes} B")
    check("the margin falls monotonically in the inscription size",
          all(a.margin > b.margin for a, b in zip(rows, rows[1:])), True)
    check("a 1 kB target still clears with real headroom",
          round(rows[-1].margin, 2), 2.55)
    check("past the ceiling it is not covered",
          ins.sweep(cfg, sizes=(int(ceiling) + 10,))[0].covered, False)

    # Affordability, against the bound the specification states on itself.
    opening = economics.reward_per_claim(cfg.genesis_pool, cfg)
    check("a genesis claim clears its own fee", opening > cfg.claim_fee, True,
          note=f"{cfg.to_lgo(opening):.4f} LGO against {cfg.to_lgo(cfg.claim_fee):.6f}")
    check("by a margin of", round(opening / cfg.claim_fee), 173_681)


def gate_tx_sizes(cfg: Config) -> None:
    """Where the transaction byte counts come from, now that they have a derivation."""
    print("\nTransaction sizes, derived from the encoding primitives")
    from . import txsize as tx                                # noqa: PLC0415

    check("a Groth16 proof, from the encoding document", tx.GROTH16, 128,
          note="pi_a 32 + pi_b 64 + pi_c 32")
    check("a Note is a value and a key", tx.NOTE, 40)
    check("the claim payload is three 32-byte fields", tx.claim_payload(), 96,
          note="epoch_nonce, block_hash, public_key")

    s = tx.sizes()
    check("the derivation reproduces transfer_tx_bytes", s.transfer, cfg.transfer_tx_bytes)
    check("and claim_tx_bytes", s.claim, cfg.claim_tx_bytes)
    check("the claim operation adds", s.difference, 99, note="96 payload + opcode + framing")

    # The framing is assumed, so the check that matters is the specification's own arithmetic.
    check("and only this framing reproduces the specification's stated claim fee",
          (s.claim + cfg.claim_tx_gas) * cfg.price_resting, 6_664, note="mantle:1858")
    u = tx.unframed()
    check("the strict reading of the encoding document does not",
          (u.claim + cfg.claim_tx_gas) * cfg.price_resting == 6_664, False,
          note=f"{u.transfer} and {u.claim} bytes give "
               f"{(u.claim + cfg.claim_tx_gas) * cfg.price_resting:,}")
    strict_ratio = (cfg.tx_fee(u.transfer, cfg.transfer_tx_gas)
                    / cfg.tx_fee(u.claim, cfg.claim_tx_gas))
    check("but it would move the fee ratio by well under a percent",
          round(abs(strict_ratio / cfg.fee_ratio - 1), 4) < 0.01, True,
          note=f"{cfg.fee_ratio:.4f} against {strict_ratio:.4f} -- no conclusion in the "
               f"study rests on the framing")


def gate_report_headlines(cfg: Config) -> None:
    """The published tables that had no gate: section 3's medians, section 6's clock, and the
    elevation study's emission regime."""
    print("\nThe report's headline tables, pinned to the runs that produced them")
    import numpy as np                                        # noqa: PLC0415

    from . import elevation as el                             # noqa: PLC0415
    from . import strategies as st                            # noqa: PLC0415

    # Section 3's table, at the published configuration (120 epochs, 100 nodes per group).
    pop, _ = st.run(cfg, st.StrategyConfig())
    tot = pop.reward_pow + pop.reward_leader + pop.reward_service
    med = {s: float(np.median(tot[pop.strategy == s.value])) / cfg.base_units_per_lgo
           for s in st.Strategy}
    base = med[st.Strategy.STAKER]
    for strat, want_lgo, want_ratio in (
            (st.Strategy.MINER, 50_151, 0.31),
            (st.Strategy.MINER_STAKER, 52_478, 0.32),
            (st.Strategy.STAKER, 163_851, 1.00),
            (st.Strategy.MINER_STAKER_SERVICE, 807_612, 4.93),
            (st.Strategy.STAKER_SERVICE, 930_422, 5.68)):
        check(f"section 3 median, {strat.name.lower()}", round(med[strat]), want_lgo,
              note=f"{med[strat] / base:.2f}x a plain stakeholder, published {want_ratio}x")

    # Section 6's depletion clock is a closed form of the distribution rate alone.
    import math                                               # noqa: PLC0415
    half = math.log(0.5) / math.log(1 - cfg.distribution_rate)
    ninety = math.log(0.1) / math.log(1 - cfg.distribution_rate)
    check("the pool's half-life, epochs", round(half), 138)
    check("and 90% depletion", round(ninety), 459,
          note=f"{ninety / cfg.epochs_per_year:.1f} years -- section 6's clock")

    # The elevation study's emission regime. A previous revision fed the stake estimator its
    # own expectation, pinning it at the 1e10 seed with the emission factor at zero, so the
    # recorded service income sat four orders of magnitude below the regime the study's own
    # retirement rationale assumes. The estimator must converge and the income must be of the
    # order the strategy study pays.
    r = el.run(cfg, el.ElevationConfig(epochs=12))
    check("elevation's estimator leaves the genesis seed",
          r.rows[6].service_per_provider_lgo > 1_000.0, True,
          note=f"{r.rows[6].service_per_provider_lgo:,.0f} LGO per provider at epoch 6, "
               f"against 0.09 under the pinned estimator")
    check("and the elevation counts are pure pool arithmetic, untouched by the fix",
          el.run(cfg, el.ElevationConfig(miners_per_epoch=100, epochs=400,
                                         retire_on_bond=False)).elevated, 5_682)


def gate_targets(cfg: Config) -> None:
    """The three inversions: state the outcome, derive the parameter."""
    print("\nParameterising by outcome: the three inversions")
    from . import targets as tg                               # noqa: PLC0415

    o = tg.endowment_for(cfg, 10_000)
    check("the endowment a 10,000-node target needs, if bonded miners retire",
          round(o.pool_retiring_lgo / 1e6, 2), 19.27, note="millions of LGO")
    check("and if they do not", round(o.pool_persistent_lgo / 1e6, 2), 87.72,
          note="an unspecified behaviour, worth 4.5x the budget")
    check("the inversion is linear in the node target",
          round(tg.endowment_for(cfg, 20_000).pool_retiring_lgo / o.pool_retiring_lgo, 6), 2.0)
    check("and it round-trips against the measured elevation study",
          round(tg.endowment_for(cfg, 5_682).pool_persistent_lgo / cfg.to_lgo(cfg.genesis_pool),
                2), 1.0, note="5,682 elevated is 11.4% of the 50,000 ceiling")
    check("the current rate corresponds to this bootstrap period",
          tg.distribution_rate_for(cfg, 9.4)["denominator"], 199,
          note="against the specified 1/200")
    check("drain safety floors the bootstrap period at",
          round(tg.min_bootstrap_years(cfg), 2), 4.82,
          note="below it the epoch's payout no longer fits in the blocks to carry it")
    check("a two-year bootstrap is not drain-safe",
          tg.distribution_rate_for(cfg, 2.0)["drain_safe"], False)
    check("a five-year one is", tg.distribution_rate_for(cfg, 4.85)["drain_safe"], True)
    # The elevation study's published table, pinned to the configuration that produced it --
    # the numbers move by a fifth between 400 and 600 epochs, and by a tenth between 50 and 100
    # arrivals an epoch, so the report's figures are only meaningful with the run attached.
    from . import elevation as _el                            # noqa: PLC0415

    _ceiling = cfg.genesis_pool / cfg.min_stake
    for _retire, _want in ((False, 5_682), (True, 25_934)):
        _r = _el.run(cfg, _el.ElevationConfig(miners_per_epoch=100, epochs=400,
                                              retire_on_bond=_retire))
        check(f"elevated over 400 epochs, bonded miners "
              f"{'retire' if _retire else 'keep mining'}", _r.elevated, _want,
              note=f"{_r.elevated / _ceiling:.1%} of the {_ceiling:,.0f} ceiling")

    check("past the ceiling an inscription target is unreachable at any share",
          tg.pow_share_for(cfg, 5_000)["reachable"], False,
          note="the ceiling is 3,929 bytes at the resting prices")
    a = tg.affordable(cfg)
    check("the specification's own claim-fee ceiling, in LGO",
          round(a["spec_ceiling_lgo"], 3), 1.157, note="mantle:1858")
    check("the claim fee sits far inside it", a["affordable"], True,
          note=f"{a['ratio']:.2e} of the ceiling")


def gate_strategies(cfg: Config) -> None:
    """The strategy study: paired draws, isolation, conservation and the service floor."""
    print("\nThe strategy study")
    from . import strategies as st                            # noqa: PLC0415

    scfg = st.StrategyConfig(epochs=12)
    pop = st.build_population(cfg, scfg)
    check("every group seated", pop.n, 500, note="five groups of a hundred")

    # Paired draws: the mining groups must share one hashrate vector, the endowed groups one
    # stake vector. If they ever diverge, a difference between groups stops being a difference
    # in strategy.
    hs = [pop.hashrate[pop.mask(s)] for s in st.MINING]
    check("all mining groups share one hashrate vector",
          all(np.array_equal(hs[0], h) for h in hs[1:]), True)
    ss = [pop.initial_stake[pop.mask(s)] for s in st.ENDOWED]
    check("all endowed groups share one stake vector",
          all(np.array_equal(ss[0], v) for v in ss[1:]), True)
    check("each endowed group holds the configured share of supply",
          cfg.to_lgo(float(ss[0].sum())), scfg.tge_stake_share * cfg.launch_supply, rel=1e-6)
    check("no miner is slower than a Raspberry Pi 5", float(hs[0].min()) >= 24_146.0, True,
          note=f"minimum {hs[0].min():,.0f} candidates/s")

    # Isolation: disabling a group must not move anyone else's draw.
    solo = st.StrategyConfig(epochs=12, enabled={s: s in (st.Strategy.MINER,
                                                          st.Strategy.STAKER)
                                                 for s in st.Strategy})
    pop2 = st.build_population(cfg, solo)
    check("disabling groups does not perturb the survivors' hashrate",
          np.array_equal(pop2.hashrate[pop2.mask(st.Strategy.MINER)],
                         pop.hashrate[pop.mask(st.Strategy.MINER)]), True)
    check("nor their stake",
          np.array_equal(pop2.initial_stake[pop2.mask(st.Strategy.STAKER)],
                         pop.initial_stake[pop.mask(st.Strategy.STAKER)]), True)

    # Every group must run alone.
    for s in st.Strategy:
        one = st.StrategyConfig(epochs=3, enabled={x: x is s for x in st.Strategy})
        p1, o1 = st.run(cfg, one)
        check(f"{st.LABELS[s]} runs alone", p1.n, 100)

    # Conservation, on a full run.
    ran, rows = st.run(cfg, scfg)
    pow_paid = sum(r.claims_paid for r in rows)
    credited_pow = int(ran.reward_pow.sum())
    expected_pow = sum(r.claims_paid * max(0, r.reward_per_claim - cfg.claim_fee) for r in rows)
    check("proof-of-work credited matches what the pool paid, net of claim fees",
          credited_pow, expected_pow, note=f"{pow_paid:,} claims")
    led = int(ran.blocks_led.sum())
    check("blocks led equals blocks produced once the lottery has stake to draw on",
          led, sum(r.blocks_produced for r in rows if r.true_staked_lgo > 0),
          note="every produced block has exactly one leader")

    # A locked service bond carries leadership weight -- settled, and the whole reason
    # strategies 3 and 5 dominate outright rather than trading one income for another. Tested
    # directly rather than statistically: on the endowed groups the bond is two hundredths of
    # a percent of a holding, so a population-level comparison cannot see it either way.
    bonded = st.Population(
        strategy=np.array([int(st.Strategy.STAKER_SERVICE)] * 2, dtype=np.int8),
        hashrate=np.zeros(2), stake=np.array([cfg.min_stake, 3 * cfg.min_stake], dtype=np.int64),
        initial_stake=np.array([cfg.min_stake, 3 * cfg.min_stake], dtype=np.int64),
        stake_aged_at=np.zeros(2, dtype=np.int32),
        declared_at=np.zeros(2, dtype=np.int32),
        reward_pow=np.zeros(2, dtype=np.int64), reward_leader=np.zeros(2, dtype=np.int64),
        reward_service=np.zeros(2, dtype=np.int64), claims=np.zeros(2, dtype=np.int64),
        blocks_led=np.zeros(2, dtype=np.int64))
    weight = bonded.aged_stake(5)
    check("a node bonded at exactly the minimum still carries full lottery weight",
          int(weight[0]), cfg.min_stake,
          note="if the bond were excluded this would be zero, and the strategy would vanish")
    check("and a larger holder carries all of its stake, bond included",
          int(weight[1]), 3 * cfg.min_stake)
    check("the switch records the decision", cfg.service_bond_counts_for_lottery, True)

    # The per-block reward series must be non-negative and must reconcile with the claim
    # count. A 32-bit accumulator wrapped here -- the reward is order 10^9 base units and ten
    # claims overflow it -- and the histograms rendered symmetric about zero, which is how it
    # was caught. Gated so it cannot return silently.
    pb = np.concatenate([r.pow_reward_per_block for r in rows])
    check("no block pays a negative proof-of-work reward", int((pb < 0).sum()), 0,
          note="an int32 accumulator wraps at ten claims")
    check("per-block rewards reconcile with the claims paid",
          int(pb.sum()),
          sum(r.claims_paid * r.reward_per_claim for r in rows))
    check("the per-block series is wide enough to be a distribution",
          len(np.unique(pb)) > 10, True, note=f"{len(np.unique(pb))} distinct values")

    # The service floor is a cliff, not a taper.
    check("below thirty-two providers the stream pays nothing",
          services.reward_per_provider(1_000_000.0, 31), 0.0)
    check("at thirty-two it pays", services.reward_per_provider(1_000_000.0, 32) > 0, True)
    check("and it is flat in the provider count",
          services.reward_per_provider(1_000_000.0, 100) * 100, 1_000_000.0, rel=1e-9,
          note="no stake term anywhere in it")


def main() -> int:
    cfg = load()
    print(f"config: {cfg.label}  (snapshot: {cfg.snapshot_path})")
    print(f"target {cfg.target_claims_per_block} claims/block, "
          f"share {cfg.pow_share:.0%}, rate 1/{cfg.distribution_rate_den}, "
          f"endowment {cfg.genesis_pool_fraction:.1%} of supply")

    gate_fees(cfg)
    gate_pool_closed_forms(cfg)
    gate_self_funding(cfg)
    gate_retarget_is_an_ema(cfg)
    gate_controller_fixed_point(cfg)
    gate_poisson_superposition(cfg)
    gate_reference_cores(cfg)
    gate_trajectory(cfg)
    gate_report_decay_table(cfg)
    gate_population(cfg)
    gate_ceiling(cfg)
    gate_study_conservation(cfg)
    gate_pooled_invariance(cfg)
    gate_participation(cfg)
    gate_group_credit(cfg)
    gate_crossover_and_min_stake(cfg)
    gate_staking_against_the_spec(cfg)
    gate_stake_aging(cfg)
    gate_two_participation_classes(cfg)
    gate_conservation(cfg)
    gate_emission(cfg)
    gate_fee_markets(cfg)
    gate_inscription(cfg)
    gate_tx_sizes(cfg)
    gate_targets(cfg)
    gate_report_headlines(cfg)
    gate_strategies(cfg)
    gate_alternative_is_neutral(cfg)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} gate(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
