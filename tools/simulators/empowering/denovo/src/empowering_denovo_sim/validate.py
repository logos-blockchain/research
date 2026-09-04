"""Gates: MODEL.md's closed forms and invariants, checked against the engine.

Same discipline as `empowering_sim.validate`: every published number is pinned to the run
that produces it, and a FAIL is a defect in either the model or the engine — the gate does
not care which, it cares that they agree.
"""
from __future__ import annotations

import sys

import numpy as np

from . import arrivals, engine, power
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
    # The persistent ceiling itself, pinned two ways. A 2026-08-25 mutation test moved it
    # from 15% to 25% and NOTHING failed: the reference triple implies 50%, which is above
    # both, so every satisfiability gate read the same either way. The published 15% -- the
    # number the whole re-strike recommendation rests on -- was unpinned.
    check("the persistent conversion ceiling is the measured 15%",
          EFFICIENCY_PERSISTENT, 0.15,
          note="what this mechanism converts when nobody retires; the re-strike arithmetic "
               "in SUMMARY section 4 is computed against exactly this")
    _straddle = Triple(expected_nodes=10_000).derived()      # implies exactly 20%
    check("and a triple that straddles it is judged against it",
          (round(_straddle.implied_efficiency, 3),
           _straddle.satisfiable, _straddle.satisfiable_if_retiring),
          (0.2, False, True),
          note="20% is above what persistence delivers and below what retirement does, so "
               "this triple distinguishes the two ceilings where the reference one cannot")
    check("the anchor is two transfers", d.anchor, 2 * cfg.avg_tx_fee)
    # An OPEN DESIGN BREAK, pinned as the true state rather than papered over: the anchor
    # was sized at two average transfers when a claim cost 1.19 of one -- self-funding plus
    # ~0.8 transfers of surplus. The 2026-09 upstream change (ZkSignature proof, gas 590)
    # made a claim cost 2.03 transfers, so the two-transfer anchor now falls 140 lepta
    # SHORT of the claim's own fee and R1's self-funding margin is gone at the anchor.
    # The re-strike (three transfers, or claim_fee + one transfer) is a design decision for
    # the owner; until it is taken, this gate records the violation so it cannot be shipped
    # silently. SUMMARY and the report carry the same warning.
    check("the anchor NO LONGER clears the claim's own fee (2026-09 upstream fee change)",
          (d.anchor > cfg.claim_fee, d.anchor, cfg.claim_fee),
          (False, 11_158, 11_298),
          note="short by 140 lepta; a claim at the anchor mines at a small loss -- the "
               "anchor re-strike is the open design decision this leaves")
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
    # The basis is a whole four-core board, per `power.py` -- the same one `study.py` and the
    # reports use. This gate suite seated nodes at one core until 2026-08-20, which left the
    # transition pinned at 195 against the reports' 196 and made the block-space gate below
    # measure a quarter of the occupancy a spike actually produces.
    draw = arrivals.pi5_pareto(np.random.default_rng(2),
                               floor_rate=power.board(cfg).candidates_per_second)
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
          r.transition_epoch, 196,
          note="one past the 195-epoch schedule: the last epoch's dust is folded and spent. "
               "This read 195 while the suite seated nodes at one core")
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
    # FLIPPED 2026-09 by the 3-permutation hashrate basis: the late big-field's offered
    # demand now exceeds block space, and what the cap clips cannot bond. On the naive
    # basis this converted 76-100% across draws and the gate asserted parity with an
    # on-time field; that reading is preserved below as history, not as the claim.
    check("a wholly back-loaded field is now rationed by block space, not the endowment",
          3_000 <= rbl.rows[-1].bonds_total <= 8_000, True,
          note=f"{rbl.rows[-1].bonds_total:,} of 28,600 on this path -- 12-23% across "
               f"fresh draws (was 76-100% on the naive-miner basis; and 1,293 under the "
               f"whole-remainder dump both replaced). Q7's answer flips: late interest "
               f"meets the SPACE cap, and MODEL 8.3's reservation rule gains a second "
               f"reason")
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
    # MODEL 8.3 is REOPENED by this gate, not closed by it. On the one-core basis the spike
    # epoch peaked at 240 of 1,024 and the question looked settled; on the board basis the cap
    # binds outright. The mechanism has no reservation for ordinary traffic -- the engine clips
    # claims at `max_block_txs` alone -- so a spike epoch does crowd the block.
    check("the block-space cap DOES bind in a x100 spike epoch",
          r100.rows[30].max_block_claims >= cfg.max_block_txs, True,
          note=f"peak {r100.rows[30].max_block_claims} of {cfg.max_block_txs}, mean "
               f"{r100.rows[30].claims_paid // cfg.blocks_per_epoch} -- ordinary transactions "
               f"ARE crowded out, and MODEL 8.3 needs a reservation rule rather than a note")
    ratio100 = r100.rows[30].spent / r100.rows[30].budget
    ratio10 = r10.rows[30].spent / r10.rows[30].budget
    check("a x10 spike borrows ~k budgets; block space now caps the x100's borrow",
          (3 <= ratio10 <= 15, ratio100 <= 60), (True, True),
          note=f"x10 {ratio10:.1f}x and x100 {ratio100:.0f}x on this path; across seven "
               f"fresh seeds the x10 median is 9.3x (5.3-11.6) but the x100 median is only "
               f"45x (29-58) -- on the 3-permutation basis a 1,024-tx block cannot pay a "
               f"hundred budgets in an epoch, so the cap truncates the borrow-forward "
               f"itself. The x100 median was 97x (58-125) on the naive basis; do not "
               f"re-quote one draw as the law")
    # A FRESH draw: this gate asserts a property of the arrival shape, so it must not inherit
    # the shared draw's rng position -- on the shared object it reads 16,922 and measures where
    # in the stream we happen to be rather than whether the shape converts.
    # FLIPPED 2026-09, same cause as the back-loaded gate: a 28,600-board field on the
    # 3-permutation basis offers more claims than block space can pay, and the cap -- not
    # the endowment -- decides who bonds. "Complete conversion" was the naive-basis result.
    check("front-loaded arrivals are now rationed by block space",
          engine.run(d, arrivals.front_loaded(220, 220 * 130),
                     arrivals.pi5_pareto(np.random.default_rng(2),
                                         floor_rate=power.board(cfg).candidates_per_second),
                     epochs=220).rows[-1].bonds_total, 5_069,
          note="of 28,600 arrivals -- the mean claim rate pegs the 1,024 cap from epoch 9 "
               "to 16 and single blocks hit it across 190 epochs; on the naive basis every "
               "arrival bonded. MODEL 8.3, again")

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
    # elastic_run seats arrivals, so the field GROWS -- which the cycle needs. Against a
    # static field (adversary.two_population_run) the index is stable and no threshold
    # induces it, which is worth knowing when reading the hazard.
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
    pr90 = adv.pump_vs_honest(d, 0.90, epochs=40)
    check("and only pays once the attacker IS the field",
          pr75["pump_advantage"] > 1.0, True,
          note=f"{pr75['pump_advantage']:.2f}x at 75%, {pr90['pump_advantage']:.2f}x at 90% "
               f"-- over a 40-epoch window; see the horizon gate below before quoting these")

    # `pump_advantage` is a ratio of CUMULATIVE balances, so over a window shorter than the
    # phase it reports how much FASTER the pump drained a fixed pool, not how much more it
    # earned. The supermajority figure decays to nothing once the window covers the phase; the
    # minority result does not, which is why the minority result is the one the report leans on.
    _decay = [(h, adv.pump_vs_honest(d, 0.90, epochs=h)["pump_advantage"])
              for h in (40, 80, 150, 190)]
    check("the supermajority pump's advantage is a truncation artifact",
          _decay[-1][1] < 1.15, True,
          note="90% of the field: " + ", ".join(f"{v:.2f}x at {h} epochs" for h, v in _decay)
               + " -- it converges on parity once the window covers the 196-epoch phase, so "
                 "'a supermajority nearly triples its take' was an artifact of measuring 40 "
                 "epochs of a fixed-pool extraction race")
    _min_long = adv.pump_vs_honest(d, 0.10, epochs=190)["pump_advantage"]
    check("while the minority result survives the same widening",
          _min_long < 1.0, True,
          note=f"{_min_long:.2f}x at 10% over 190 epochs against 0.64x over 40 -- withholding "
               f"still loses, which is the load-bearing conclusion")

    # An elastic attacker cannot harvest the Q9 cliff: being picky costs more than it takes.
    field = power.board(cfg).candidates_per_second * 1000
    _, _, always = adv.two_population_run(d, field * 0.7, field * 0.3,
                                          lambda e, r: True, 60)
    _, _, picky = adv.two_population_run(d, field * 0.7, field * 0.3,
                                         lambda e, r: r >= 5e9, 60)
    check("harvesting the participation cliff loses money", picky < always, True,
          note=f"{picky / always:.2f}x of always-on -- Q9's cycle is a UX hazard, not an "
               f"exploit")

    # Every attack above is measured in `two_population_run`, so it is only evidence about
    # THIS mechanism if that harness reproduces the engine. It did not, past the transition,
    # until 2026-08-21: expected claims were computed once per epoch, leaving the post-phase
    # throttle open-loop within the epoch, so a burst at the transition ratcheted the
    # difficulty and the run then sat at zero claims forever. Nothing tested past the
    # transition, so nothing caught it. This does.
    _hon, _, _ = adv.two_population_run(
        d, power.board(cfg).candidates_per_second * 1000, 0.0, lambda e, r: False, 240)
    _h_post = [q.honest_paid for q in _hon if not q.bootstrap][1:]
    _e_post = [q.claims_paid for q in r.rows if not q.bootstrap][1:]
    check("the adversarial harness does not stall after the transition",
          min(_h_post) > 0, True,
          note=f"{len(_h_post)} post-phase epochs, all paying; the open-loop throttle used to "
               f"collapse this to zero claims and never recover")
    check("and it reproduces the engine's post-phase steady state exactly",
          sorted(set(_h_post)), sorted(set(_e_post)),
          note=f"{_h_post[0]:,} claims an epoch at the anchor in both -- budget // reward, "
               f"the post-phase capacity")

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
    # The 3-permutation basis SOFTENS this finding: block space now rations the whale as
    # well, so the base concession fell from 33-56% (naive basis) to a flat 21% at every
    # whale size tested -- the cap, not the whale's size, binds. (A first re-measure read
    # 12.6-21% across sizes; that spread was a stale 24,146 board rate hardcoded in
    # variant.whale_run shrinking the whale relative to the field, fixed 2026-09.)
    check("the base design concedes about a fifth of the endowment to a well-timed whale",
          0.15 <= base.whale_capture <= 0.25, True,
          note=f"{base.whale_capture:.0%} at epoch 20; 21% flat across 3x/10x/30x/100x "
               f"whales, saturating at block space. Was 33-56% before block space bound")
    check("the variant still bounds it to under a tenth",
          capped.whale_capture < 0.12, True,
          note=f"{capped.whale_capture:.0%} -- and flat across whale size: 3x/10x/30x/100x "
               f"all land at 9%, where the base sits at 21%")
    check("and R5 survives: the x100 cohort still bonds completely",
          capped.spike_bonded_fraction, 1.0,
          note=f"median time-to-bond {capped.spike_median_epochs:.0f} epochs against the "
               f"base's {base.spike_median_epochs:.0f} -- a deferral, not a denial")
    check("onboarding is not paid for",
          capped.uniform_bonds >= base.uniform_bonds * 0.98, True,
          note=f"{capped.uniform_bonds:,} against {base.uniform_bonds:,}")
    # Independent draws: this gate measures whether the CAP moves the outcome, so both runs
    # must see the same hardware. A shared draw advances between them and the comparison
    # becomes a measurement of the rng position instead.
    def _fresh():
        return arrivals.pi5_pareto(np.random.default_rng(2),
                                   floor_rate=4 / cfg.seconds_per_candidate_reward)

    _cap_persist = engine.run(d, arrivals.uniform(220, 130), _fresh(), epochs=360,
                              retire_on_bond=False,
                              draw_cap_fraction=variant.DEFAULT_CAP)
    _base_persist = engine.run(d, arrivals.uniform(220, 130), _fresh(), epochs=360,
                               retire_on_bond=False)
    check("the cap is neutral to the retirement regime",
          abs(_cap_persist.rows[-1].bonds_total
              - _base_persist.rows[-1].bonds_total) < 500, True,
          note=f"{_cap_persist.rows[-1].bonds_total:,} against "
               f"{_base_persist.rows[-1].bonds_total:,} under persistence")
    # This was `check(..., True, True, note=<hand-typed figures>)` until 2026-08-20 -- a gate
    # that compared True to True and measured nothing, carrying the only occurrence of these
    # figures anywhere in the simulator. Now measured.
    _syb_base = adv.sybil_denial(d, cap=0.0)
    _syb_cap = adv.sybil_denial(d, cap=variant.DEFAULT_CAP)
    _fmt = lambda rows: "/".join(f"{r['denied']:.1%}" for r in rows[1:])   # noqa: E731
    check("and does not reintroduce sybil fragility",
          max(abs(a["denied"] - b["denied"])
              for a, b in zip(_syb_cap[1:], _syb_base[1:])) < 0.05, True,
          note=f"a cap is a form of rationing, which is what makes the CURRENT design "
               f"flood-fragile -- measured, denial at 2x/5x/10x floods is {_fmt(_syb_cap)} "
               f"against the base's {_fmt(_syb_base)}: unchanged, because the cap defers "
               f"rather than denies")
    check("the redesign is an order of magnitude more flood-resistant at 2x",
          _syb_base[1]["denied"] < 0.10, True,
          note=f"{_syb_base[1]['denied']:.1%} of honest bonds denied at a doubled field, "
               f"against the current design's 48.4% -- a fixed claim flow halves every share, "
               f"a budget just converts faster")
    check("and both collapse at 10x, where the payout strands below the bond",
          _syb_base[3]["denied"] > 0.90, True,
          note=f"{_syb_base[3]['denied']:.1%} -- the binding constraint there is the same in "
               f"both designs")
    check("nor is the phase length",
          abs(capped.transition - base.transition) <= 3, True,
          note=f"transition {capped.transition} against {base.transition}; the cap bounds the "
               f"BORROW only -- capping the whole draw stopped the endowment ever emptying")

    # ---------------------------------------------------------------- retirement, decided
    print("\nRetirement as a decision rather than a regime")
    from . import retirement as ret                             # noqa: PLC0415
    from . import study as _st2                                 # noqa: PLC0415

    _A = arrivals.uniform(220, 130)
    _dec = engine.run(d, _A, _st2.hashrate_draw(cfg), epochs=240,
                      retirement_policy=ret.Rational())
    # Inside the SCHEDULE (e < bootstrap_epochs). Epoch 195 is still `bootstrap` by the
    # endowment test but is already in Q7's nominal-rate tail, where the budget drops and the
    # decision flips -- which is the next gate.
    _boot = [q for q in _dec.rows if q.epoch < d.bootstrap_epochs and q.bonds_total > 0]
    check("every bonded miner keeps mining, every epoch of the scheduled bootstrap",
          min(q.persisting for q in _boot), 1.0,
          note=f"not an assumption: each re-decides each epoch against its own income and "
               f"electricity, and mining wins in all {len(_boot)} of them")
    check("and they all stop within an epoch of the schedule ending",
          max(q.persisting for q in _dec.rows if q.epoch >= d.bootstrap_epochs) < 0.001, True,
          note="the budget collapses to the fee bucket, the anchor cannot pay for the "
               "grinding, and the field goes home -- the post-phase is vestigial by design. "
               "The residue is one miner that bonds in the final epoch and never re-decides")
    check("so the DECIDED outcome is the persistent regime, not the retiring one",
          _dec.rows[-1].bonds_total, 7_635,
          note="against 24,707 if they retired -- the retiring figure is not a behaviour "
               "anyone would choose, so it should not be quoted as an expectation. Read "
               "7,963 until the 2026-09 claim fee thinned the margins")

    _no_x = engine.run(d, _A, _st2.hashrate_draw(cfg), epochs=240,
                       retirement_policy=ret.Rational(count_exclusion=False))
    check("the exclusion dividend changes no decision at the measured pot and reference price",
          _no_x.rows[-1].bonds_total, _dec.rows[-1].bonds_total,
          note="suppressing the on-ramp IS worth something -- every 1,000 LGO mined is one "
               "bond that never happens -- but at $1 it only reinforces a decision mining "
               "wins outright. Near the break-even price it perturbs the oscillation's phase "
               "and moves bonds by a few per cent; it never changes the regime at any price")

    _curve = ret.price_curve(d, prices=(1.0, 0.10, 0.01))
    check("a HIGHER token price suppresses onboarding, not a lower one",
          [c["bonds"] for c in _curve], sorted(c["bonds"] for c in _curve),
          note=f"income is in LGO and electricity in dollars, so a dearer token keeps "
               f"incumbents mining longer: persists to epoch "
               f"{'/'.join(str(c['persists_until']) for c in _curve)} and onboards "
               f"{'/'.join(format(c['bonds'], ',') for c in _curve)} at $1.00/$0.10/$0.01")

    # ---------------------------------------------------------------- the window, priced
    print("\nThe acceptance window, priced (W = 10 blocks)")
    from . import window as win                                # noqa: PLC0415

    _wref = engine.run(d, arrivals.uniform(220, 130), _st2.hashrate_draw(cfg), epochs=220)
    _wprof = win.congestion_profile(_wref.rows, cfg)
    check("the window is free where the field stays small",
          max(c.inflation for c in _wprof) < 1.001, True,
          note="reference retiring run: worst epoch inflation 1.000x, expiry 0.00% -- "
               "offered demand never nears block space, so nothing waits and nothing dies. "
               "The one regime the window never taxes, on either hashrate basis")
    _wspk = engine.run(d, arrivals.spike(220, 130, at=30, factor=100),
                       _st2.hashrate_draw(cfg), epochs=35)
    _cs = win.congestion_profile(_wspk.rows, cfg)[30]
    # FLIPPED 2026-09: on the naive basis the spike offered 759 a block, cleared inside
    # the window and lost nothing. On the 3-permutation basis it offers 1,837 against
    # 1,024 of space and the window kills what cannot fit.
    check("and it now taxes the x100 spike, which the naive basis acquitted",
          (round(_cs.expiry_fraction, 3), round(_cs.inflation, 3)), (0.442, 1.794),
          note=f"{_cs.offered / cfg.blocks_per_epoch:.0f} offered a block against 1,024 of "
               f"space: 44.2% of the spike's solutions expire and its energy per paid "
               f"claim inflates x1.79 -- the spike epoch pegs the cap outright in every "
               f"draw, and MODEL 8.3's reservation rule is now non-negotiable")
    _wper = engine.run(d, arrivals.uniform(220, 130), _st2.hashrate_draw(cfg), epochs=220,
                       retire_on_bond=False)
    _cp = win.congestion_profile(_wper.rows, cfg)[194]
    check("the tax dominates the late persistent endgame",
          (round(_cp.inflation, 2), round(_cp.expiry_fraction, 3)), (3.4, 0.706),
          note="epoch 194 of the never-shrinking field: 3,483 offered a block, 70.6% of "
               "solutions expire, energy per paid claim x3.40 (epoch 100 already runs "
               "44.8% expiry at x1.81) -- the floored difficulty meets finite block "
               "space, and the window collects the difference. Read (1.41, 0.288) on "
               "the naive basis")
    check("the post-phase saturation tail loses a tenth of a percent",
          round(win.post_tail_loss(_wref.rows, cfg), 5), 0.00137,
          note="solutions found between saturation and the window's grace strip expire and "
               "re-mine next epoch -- R7b's only hidden fee, 0.137% per settled epoch")
    check("and the window bounds any stockpile to ten blocks of the attacker's own rate",
          round(win.stockpile_bound(d, 10 * 1000 * power.board(cfg).candidates_per_second), 1),
          2612.7,
          note="a 10x-the-field whale holds at most ~2,613 claims ready against an epoch "
               "capacity of 648,000 -- the grinding defence, quantified; and why the "
               "adversary harness's live-rate limit was never an understatement")
    _wcurve = win.congested_price_curve(d, prices=(0.10,))
    # FLIPPED 2026-09: the naive basis found the tax moved no threshold at any price,
    # because congestion lived only where no decision was marginal. On the 3-permutation
    # basis congestion arrives ~90 epochs earlier and reaches the $0.10 margin.
    check("the congestion tax now moves the $0.10 retirement threshold",
          (_wcurve[0]["persists_until"], _wcurve[0]["persists_until_taxed"]), (107, 88),
          note="19 epochs earlier with the tax closed through the decision; $1 (never "
               "marginal) and $0.05/$0.01 (field too small to congest at the margin) "
               "stay unmoved, with bond totals shifting about 1%")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES")
        return 1
    print("all gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
