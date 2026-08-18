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
    check("the transition lands at the expected duration plus the room-lock tail",
          195 <= r.transition_epoch <= 205, True, note=f"epoch {r.transition_epoch}")
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
    check("and the saturation point sits in the epoch's last tenth (R7b)",
          all(s == engine.NOT_SET or s >= 0.9 * cfg.blocks_per_epoch for s in sat), True,
          note=f"worst settled saturation at block {min(s for s in sat if s != engine.NOT_SET):,}"
          if any(s != engine.NOT_SET for s in sat) else "never saturated")

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
    check("the borrow shortens the phase",
          r10.transition_epoch <= r.transition_epoch, True,
          note=f"transition {r10.transition_epoch} against uniform {r.transition_epoch}")
    # R5's admission metric: the spike cohort reaches bonds like its neighbours do.
    bonds = r10.bonds_by_cohort()
    spike_frac = bonds.get(30, 0) / (130 * 10)
    neigh = [bonds.get(e, 0) / 130 for e in (27, 28, 29, 33, 34, 35)]
    check("the spike cohort's bond rate is within the neighbours' range",
          0.5 * min(neigh) <= spike_frac <= 1.5 * max(neigh), True,
          note=f"{spike_frac:.1%} against neighbours {min(neigh):.1%}..{max(neigh):.1%}")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES")
        return 1
    print("all gates pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
