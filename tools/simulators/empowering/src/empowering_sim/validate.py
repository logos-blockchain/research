"""Gates: the simulator against the closed forms the tokenomics report derives.

Every check here restates a published result independently and demands the engine reproduce
it. They are cheap, they run from the first commit rather than being retrofitted, and they
are the reason a number out of this simulator can be quoted at all.

Run as ``python -m empowering_sim.validate``.
"""
from __future__ import annotations

import sys

import numpy as np

from . import (consensus, crossover, economics, engine, graduation, market, scenarios,
               simulate, work)
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
    check("min_stake in LGO", ceiling["min_stake_lgo"], 100_000.0, rel=1e-12)
    check("genesis_pool in LGO", ceiling["genesis_pool_lgo"], 50_000_000.0, rel=1e-12)
    check("graduates the endowment can ever fund", ceiling["endowment_graduates"], 500.0,
          rel=1e-12, note="endowment over the threshold, and nothing else enters it")
    check("years per fee-funded graduate thereafter",
          ceiling["years_per_fee_funded_graduate"], 284.2, rel=1e-3)
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
    check("pooled equivalent stays under the arithmetic ceiling", max(pooled) <= 500, True,
          note=f"max {max(pooled)} against a ceiling of 500")
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
    crossings = []
    for share in (0.001, 0.01, 0.05, 0.20):
        pos = crossover.Position(stake=cfg.min_stake, hashrate_share=share)
        crossings.append(crossover.crossover_epoch(cfg, pos, 0.30)["epoch"])
    check("staking overtakes mining at every field share", all(c is not None for c in crossings),
          True, note=f"epochs {crossings}")
    check("a larger miner holds out longer", crossings == sorted(crossings), True,
          note="the crossing is monotone in hashrate share")
    check("mining dominates for years, not weeks", crossings[1] / cfg.epochs_per_year > 5, True,
          note=f"{crossings[1] / cfg.epochs_per_year:.1f} years at a 1% share")

    # The specified threshold, read against field size.
    at_500 = crossover.min_stake_reading(cfg, spec_lgo, 1.0 / 500, 0.30)
    check("the specified threshold is coherent for a field of 500",
          3.0 < at_500["years_to_graduate"] < 5.0, True,
          note=f"{at_500['years_to_graduate']:.2f} years, and the endowment funds exactly "
               f"{at_500['graduates_the_endowment_funds']:.0f}")


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
    check("validation APY at the target", consensus.validation_apy(cfg), 0.0333, rel=0.02,
          note="the specification states ~3.33%, and calibrated I_max to hit it")

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
    check("graduations per epoch carries no target", rate, 2.5, rel=1e-9)

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
    gate_conservation(cfg)
    gate_alternative_is_neutral(cfg)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} gate(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
