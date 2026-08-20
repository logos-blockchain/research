"""Gates: MODEL.md's closed forms and invariants, checked against the engine.

Same discipline as `empowering_sim.validate`: every published number is pinned to the run
that produces it, and a FAIL is a defect in either the model or the engine — the gate does
not care which, it cares that they agree.
"""
from __future__ import annotations

import sys

import numpy as np

from . import arrivals, engine
from .params import (EFFICIENCY_PERSISTENT, EFFICIENCY_RETIRING_FAST, Triple,
                     UnsatisfiableTriple)

FAILURES: list[str] = []


def check(label: str, got, want=True, rel: float | None = None, note: str = "") -> None:
    ok = (abs(got - want) <= rel * max(abs(want), 1e-300)) if rel is not None else got == want
    tag = "ok  " if ok else "FAIL"
    if not ok:
        FAILURES.append(label)
    extra = f"   -- {note}" if note else ""
    print(f"  [{tag}] {label}: {got}" + ("" if ok else f" vs {want}") + extra)


def main() -> int:
    d = Triple().derived().check()
    cfg = d.cfg

    print("The triple, and what it derives")
    check("bootstrap epochs", d.bootstrap_epochs, 195)
    check("endowment, lepta", d.endowment_genesis, 50_000_000 * cfg.base_units_per_lgo)
    check("implied conversion efficiency", round(d.implied_efficiency, 3), 0.5,
          note=f"{d.regime_note}")
    check("the reference triple is NOT feasible on incentives alone",
          d.satisfiable, False,
          note=f"it asserts 50% where persistence delivers "
               f"{EFFICIENCY_PERSISTENT:.0%} -- a bet on retirement, now explicit")
    check("but is feasible if bonded miners do retire", d.satisfiable_if_retiring, True)
    check("the anchor is two transfers", d.anchor, 2 * cfg.avg_tx_fee)
    check("and clears the claim's own fee", d.anchor > cfg.claim_fee, True,
          note=f"{d.anchor:,} against {cfg.claim_fee:,}")
    check("opening sub-pool, LGO", d.opening_sub_pool() // cfg.base_units_per_lgo, 256_410)
    check("opening reward, LGO", round(d.opening_reward() / cfg.base_units_per_lgo, 2), 11.87)
    check("claims to a bond at the opening reward",
          -(-cfg.min_stake // (d.opening_reward() - cfg.claim_fee)), 85)
    for nodes, side in ((40_000, "above"), (5_000, "below")):
        try:
            Triple(expected_nodes=nodes).derived().check()
            ok = side != "above"      # a low triple over-funds; that is not infeasible
            check(f"a triple {side} the band behaves correctly", True, ok)
        except UnsatisfiableTriple:
            check(f"a triple {side} the band behaves correctly", side == "above", True)

    print("\nThe reference run: uniform arrivals, retirement on")
    # ONE draw object is reused across every run below, so its rng state advances run by
    # run and every pinned constant depends on the ORDER of the gates. Reordering runs, or
    # inserting one, legitimately moves heavy-tail-sensitive numbers (the x100 borrow ratio
    # spans 86-111x across paths) -- re-pin deliberately, never relax.
    draw = arrivals.pi5_pareto(np.random.default_rng(2),
                               floor_rate=1 / cfg.seconds_per_candidate_reward)
    r = engine.run(d, arrivals.uniform(220, 130), draw, epochs=220)
    rows = r.rows

    endow = [q.endowment for q in rows]
    check("the endowment is monotone non-increasing",
          all(a >= b for a, b in zip(endow, endow[1:])), True)
    boot = [q.bootstrap for q in rows]
    check("the regime flips exactly once",
          sum(1 for a, b in zip(boot, boot[1:]) if a != b), 1)
    check("and never back", all(not b for b in boot[r.transition_epoch:]), True)
    check("the transition lands at the expected duration exactly",
          r.transition_epoch, 195,
          note="the earlier 195-199 drift was the anchor-scale dust fold failing to fire")
    check("after it the endowment is exactly zero",
          all(q.endowment == 0 for q in rows[r.transition_epoch:]), True,
          note="the dust fold -- without it the regime deadlocks one reward short")
    check("value is conserved to the lepton",
          d.endowment_genesis + r.total_diverted
          - r.final_endowment - r.final_fee_bucket - r.total_paid, 0)
    check("every bootstrap reward is at least the anchor",
          all(q.reward >= d.anchor for q in rows if q.bootstrap), True)
    check("every post-phase reward is exactly the anchor",
          all(q.reward == d.anchor for q in rows if not q.bootstrap), True)
    check("genesis saturates -- claims_prev = 0 budgets one claim per block",
          rows[0].saturation_block != engine.NOT_SET, True,
          note=f"block {rows[0].saturation_block:,}; the borrow-forward absorbs the opening")
    check("bonds land at the target under the regime the triple bets on",
          abs(rows[-1].bonds_total - 25_000) < 2_000, True,
          note=f"{rows[-1].bonds_total:,} against 25,000 -- but only while miners retire; "
               f"the persistent regime delivers about a third of it")
    _persist = engine.run(d, arrivals.uniform(220, 130), draw, epochs=360,
                          retire_on_bond=False)
    check("and the same triple under persistence delivers about a third",
          0.20 <= _persist.rows[-1].bonds_total / 25_000 <= 0.40, True,
          note=f"{_persist.rows[-1].bonds_total:,} bonds -- both regimes are reported "
               f"throughout rather than one being presumed")

    post = [q for q in rows if not q.bootstrap][5:]          # let the throttle settle
    check("post-phase claims hit the capacity identity exactly",
          {q.claims_paid for q in post} == {cfg.pow_share_num * cfg.txs_per_block
                                            * cfg.blocks_per_epoch
                                            // (cfg.pow_share_den * 2)}, True,
          note="capacity = pow_share * txs_per_epoch / 2 -- independent of the fee level")
    sat = [q.saturation_block for q in post]
    check("and the saturation point sits in the epoch's last half-percent (R7b)",
          all(s == engine.NOT_SET or s >= 21_500 for s in sat), True,
          note=f"worst settled saturation at block {min(s for s in sat if s != engine.NOT_SET):,}"
          if any(s != engine.NOT_SET for s in sat) else "never saturated")
    check("no settled post block carries more than a few times the target",
          max(q.max_block_claims for q in post) <= 4 * (648_000 // cfg.blocks_per_epoch),
          True, note=f"fullest {max(q.max_block_claims for q in post)} against target 30 -- "
                     f"before the retarget was frozen past the saturation point, every epoch "
                     f"opened with a 1,024-claim burst off the eased-to-cap tail")

    print("\nThe spike: ten times the background, one epoch (R5)")
    r10 = engine.run(d, arrivals.spike(220, 130, at=30, factor=10), draw, epochs=220)
    q30 = r10.rows[30]
    # The spike lands mid-epoch as hashrate, so the epoch saturates early and borrows.
    check("the spike epoch saturates",
          q30.saturation_block != engine.NOT_SET, True,
          note=f"block {q30.saturation_block:,} of {cfg.blocks_per_epoch:,}")
    check("no claim in the spike epoch went unpaid for budget reasons",
          q30.spent >= q30.budget, True,
          note=f"spent {q30.spent / q30.budget:.2f}x the budget -- the borrow-forward at work")
    check("the schedule absorbs the spike: the phase still ends near its deadline",
          abs(r10.transition_epoch - d.bootstrap_epochs) <= 25, True,
          note=f"transition {r10.transition_epoch} against a {d.bootstrap_epochs}-epoch "
               f"deadline and uniform's {r.transition_epoch}; across seeds uniform gives "
               f"195/196/181 and x100 gives 196/196/196, so no spike shortens anything -- "
               f"an earlier revision claimed a (k-1)-epoch shortening and was wrong")

    print("\nThe nominal-rate tail (Q7): late interest meets the planned regime")
    rbl = engine.run(d, arrivals.back_loaded(220, 220 * 130), draw, epochs=420)
    check("a wholly back-loaded field converts like an on-time one",
          rbl.rows[-1].bonds_total >= 20_000, True,
          note=f"{rbl.rows[-1].bonds_total:,} of 28,600 -- 76-100% across draws, against "
               f"1,293 (4.5%) under the whole-remainder dump this replaces")
    nominal = d.endowment_genesis // d.bootstrap_epochs
    tail = [q for q in rbl.rows if q.epoch >= d.bootstrap_epochs and q.bootstrap]
    check("no tail epoch offers more than the nominal sub-pool plus fees",
          all(q.budget <= nominal + q.fee_bucket_opening for q in tail), True,
          note=f"{len(tail)} tail epochs, capped at {nominal / 1e18:.4f}e9 LGO each")
    last = rbl.rows[-1]
    check("the tail ends in a legal state: armed, or spent and transitioned",
          last.endowment > 0 or (last.endowment == 0 and not last.bootstrap), True,
          note=f"endowment {last.endowment / d.endowment_genesis:.0%}, "
               f"bootstrap={last.bootstrap} -- which branch is draw-dependent, the legality "
               f"is not")
    r100 = engine.run(d, arrivals.spike(220, 130, at=30, factor=100), draw, epochs=220)
    check("the block-space cap never binds, even in the spike epoch",
          r100.rows[30].max_block_claims < cfg.max_block_txs, True,
          note=f"peak {r100.rows[30].max_block_claims} of {cfg.max_block_txs} -- ordinary "
               f"transactions are never crowded out (MODEL 8.3, resolved)")
    ratio100 = r100.rows[30].spent / r100.rows[30].budget
    check("a xk spike borrows on the order of k budgets",
          20 <= ratio100 <= 200, True,
          note=f"{ratio100:.0f}x here; across seven independent seeds the x100 median is 97x "
               f"(58-125) and the x10 median is 10x (6-13). Single-draw figures of 2.6x and "
               f"86-111x were quoted before this was measured properly -- do not re-quote one "
               f"draw as the law")
    check("front-loaded arrivals convert completely",
          engine.run(d, arrivals.front_loaded(220, 220 * 130), draw,
                     epochs=220).rows[-1].bonds_total, 28_600,
          note="every arrival bonds; the surplus endowment stays armed")

    # R5's admission metric: the spike cohort reaches bonds like its neighbours do.
    bonds = r10.bonds_by_cohort()
    spike_frac = bonds.get(30, 0) / (130 * 10)
    neigh = [bonds.get(e, 0) / 130 for e in (27, 28, 29, 33, 34, 35)]
    check("the spike cohort's bond rate is within the neighbours' range",
          0.5 * min(neigh) <= spike_frac <= 1.5 * max(neigh), True,
          note=f"{spike_frac:.1%} against neighbours {min(neigh):.1%}..{max(neigh):.1%}")

    print("\nThe accepted properties (Q8 unbounded, Q9 raw), pinned so they cannot drift")
    from . import scenarios                                   # noqa: PLC0415
    caps = []
    for mult in (1.0, 3.0, 10.0):
        rw = scenarios.whale_run(d, 130, whale_epoch=30, whale_multiple=mult, epochs=220)
        caps.append(rw.pop.balance.max() / d.endowment_genesis)
    check("the whale's capture curve is monotone in its size",
          caps[0] < caps[1] < caps[2], True,
          note=f"{caps[0]:.0%} / {caps[1]:.0%} / {caps[2]:.0%} at 1x / 3x / 10x -- the "
               f"documented first-come property of an unbounded borrow")
    check("and even at 10x the pool never goes negative anywhere",
          min(q.endowment for q in rw.rows) >= 0, True)
    rc = scenarios.elastic_run(d, 130, epochs=120, threshold_lepta=4_500_000_000, eta=8.0)
    tail = [q.claims_paid for q in rc.rows[100:116]]
    lows = sum(1 for c in tail if c < 1_000)
    highs = sum(1 for c in tail if c > 20_000)
    check("a participation cliff at the operating reward period-2 cycles",
          lows >= 6 and highs >= 6, True,
          note=f"{lows} near-zero and {highs} full epochs in a 16-epoch window -- the "
               f"documented hazard of the raw index")

    print("\nAdversarial: what the mechanism resists, and what it concedes")
    from . import adversary as adv                            # noqa: PLC0415

    # The reward cap max(claims_prev, blocks_per_epoch) is what makes withholding lose.
    for frac, want_lose in ((0.10, True), (0.25, True), (0.50, True)):
        pr = adv.pump_vs_honest(d, frac, epochs=40)
        check(f"withholding loses money at {frac:.0%} of the field",
              pr["pump_advantage"] < 1.0, want_lose,
              note=f"{pr['pump_advantage']:.2f}x of mining honestly -- the reward cap bounds "
                   f"what a shrunk claims_prev can buy back")
    pr75 = adv.pump_vs_honest(d, 0.75, epochs=40)
    check("and only pays once the attacker IS the field",
          pr75["pump_advantage"] > 1.0, True,
          note=f"{pr75['pump_advantage']:.2f}x at 75% -- above half the field the pump is "
               f"the whale renamed, and Q8 already accepts that")

    # An elastic attacker cannot harvest the Q9 cliff: being picky costs more than it takes.
    field = 1.0 / cfg.seconds_per_candidate_reward * 1000
    _, _, always = adv.two_population_run(d, field * 0.7, field * 0.3,
                                          lambda e, r: True, 60)
    _, _, picky = adv.two_population_run(d, field * 0.7, field * 0.3,
                                         lambda e, r: r >= 5e9, 60)
    check("harvesting the participation cliff loses money", picky < always, True,
          note=f"{picky / always:.2f}x of always-on -- Q9's cycle is a UX hazard, not an "
               f"exploit")

    # The assumption both designs' targets rest on, and what it costs when it fails.
    from . import arrivals as _arr                             # noqa: PLC0415
    from . import study as _st                                 # noqa: PLC0415

    _base = engine.run(d, _arr.uniform(220, 130), _st.hashrate_draw(cfg), epochs=360)
    _quarter = engine.run(d, _arr.uniform(220, 130), _st.hashrate_draw(cfg), epochs=360,
                          refuse_fraction=0.25)
    _all = engine.run(d, _arr.uniform(220, 130), _st.hashrate_draw(cfg), epochs=360,
                      refuse_fraction=1.0)
    ratio_q = _quarter.rows[-1].bonds_total / _base.rows[-1].bonds_total
    ratio_a = _all.rows[-1].bonds_total / _base.rows[-1].bonds_total
    check("a quarter of the field refusing to retire costs about a third of onboarding",
          0.58 <= ratio_q <= 0.68, True,
          note=f"{_quarter.rows[-1].bonds_total:,} against {_base.rows[-1].bonds_total:,} -- "
               f"and it costs the coalition nothing, they keep earning")
    check("the whole field refusing costs about two thirds", 0.28 <= ratio_a <= 0.38, True,
          note="the persistent regime the identity band's low edge describes")
    check("and retiring is not incentivised: mining still pays after bonding",
          d.opening_reward() - cfg.claim_fee > 0, True,
          note="a bonded node can provide service AND mine; the marginal claim is profitable "
               "at any plausible token price, so the retiring figure is an assumption about "
               "behaviour rather than about incentives")

    print("\nde novo* -- the asterisked variant that bounds the endowment draw")
    from . import variant                                       # noqa: PLC0415

    base = variant.evaluate(d, 0.0, "base")
    capped = variant.evaluate(d, variant.DEFAULT_CAP, "capped")
    check("the base design concedes most of the endowment to a well-timed whale",
          base.whale_capture > 0.4, True, note=f"{base.whale_capture:.0%} at epoch 20")
    check("the variant bounds it to under a tenth",
          capped.whale_capture < 0.12, True,
          note=f"{capped.whale_capture:.0%} -- and flat across whale size: 3x/10x/30x/100x "
               f"all land near 9%, where the base ranges 33-56%")
    check("and R5 survives: the x100 cohort still bonds completely",
          capped.spike_bonded_fraction, 1.0,
          note=f"median time-to-bond {capped.spike_median_epochs:.0f} epochs against the "
               f"base's {base.spike_median_epochs:.0f} -- a deferral, not a denial")
    check("onboarding is not paid for",
          capped.uniform_bonds >= base.uniform_bonds * 0.98, True,
          note=f"{capped.uniform_bonds:,} against {base.uniform_bonds:,}")
    check("nor is the phase length",
          abs(capped.transition - base.transition) <= 3, True,
          note=f"transition {capped.transition} against {base.transition}; the cap bounds the "
               f"BORROW only -- capping the whole draw stopped the endowment ever emptying")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES")
        return 1
    print("all gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
