"""Gates: MODEL.md's closed forms and invariants, checked against the engine.

Same discipline as `empowering_sim.validate`: every published number is pinned to the run
that produces it, and a FAIL is a defect in either the model or the engine — the gate does
not care which, it cares that they agree.
"""
from __future__ import annotations

import sys

import numpy as np

from . import arrivals, engine
from .params import EFFICIENCY_RETIRING, Triple, UnsatisfiableTriple

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
          note="satisfiable only in the retiring regime -- the triple's built-in assumption")
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
            check(f"a triple {side} the band is rejected", False, True)
        except UnsatisfiableTriple:
            check(f"a triple {side} the band is rejected", True, True)

    print("\nThe reference run: uniform arrivals, retirement on")
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
    check("bonds land at the target's efficiency reading",
          abs(rows[-1].bonds_total - 25_000) < 1_500, True,
          note=f"{rows[-1].bonds_total:,} bonds against 25,000 expected at 50% implied, "
               f"inside the {EFFICIENCY_RETIRING:.1%} band edge")

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
    check("the borrow cannot lengthen the phase",
          r10.transition_epoch <= r.transition_epoch, True,
          note=f"transition {r10.transition_epoch} against uniform {r.transition_epoch}")

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
    check("the x100 epoch's borrow runs two orders deeper than the x10's",
          50 <= ratio100 <= 200, True,
          note=f"{ratio100:.0f}x the budget against the x10's 2.6x -- the exact multiplier "
               f"is Pareto-tail luck (86-111 across seeds) and the report says so; the two "
               f"figures must not be conflated again")
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

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES")
        return 1
    print("all gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
