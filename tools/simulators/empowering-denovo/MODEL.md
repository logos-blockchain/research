# The de-novo EmPoWering model — normative

Status: Phase A of `PLAN.md`. The design of the plan's §1 written out as state and transition
rules, in the specification's integer style. Validates against requirements R1–R8 by number.
One settled question is **amended** here with its reasoning on record: §9.

Everything is denominated in **lepta** unless suffixed `_lgo`. Integer arithmetic with stated
flooring, matching the ledger.

## 1. Parameters

The three of R4, plus what is inherited unchanged:

| parameter | meaning | reference value |
| --- | --- | --- |
| `POOL_FRACTION` | TGE endowment of the PoW pool, as a fraction of launch supply | 0.5% |
| `EXPECTED_NODES` | nodes the bootstrap intends to onboard (R3) | 25,000 |
| `EXPECTED_YEARS` | intended bootstrap duration | 4.0 |

Inherited, not free: `min_stake` (1,000 LGO, SDP), `pow_share` (10%, the fee diversion),
`blocks_per_epoch` (21,600), the EMA retarget constants `F/P` (9/10), the genesis difficulty
seed (`p / 2^26`), and the fee model (`txsize`, two markets, lepta).

Derived at genesis, no new information:

```python
BOOTSTRAP_EPOCHS   = round(EXPECTED_YEARS * EPOCHS_PER_YEAR)          # 195 at 4.0 years
ENDOWMENT_GENESIS  = floor(POOL_FRACTION * LAUNCH_SUPPLY * LEPTA)     # 5e16 lepta
```

**The consistency identity (checked at parameterisation, before anything runs):**

| `implied_efficiency = EXPECTED_NODES * min_stake / ENDOWMENT_GENESIS` |
| --- |

must lie inside the measured conversion band **[11.4%, 51.9%]** (elevation study; the ends are
the bonded-miners-keep-mining and bonded-miners-retire behaviours). The reference triple
implies 50% — satisfiable, and only just: it presumes most bonded miners retire. A triple
outside the band is rejected as unsatisfiable at declaration time.

## 2. State

Consensus state, per the component accounting of Q6:

```python
endowment: TokenValue        # E. The TGE bucket. Monotone non-increasing. Genesis: ENDOWMENT_GENESIS.
fee_bucket: TokenValue       # F. Diverted fees available to spend: last epoch's accrual plus rollover.
fee_accrual: TokenValue      # fees diverted DURING this epoch; becomes part of F at the boundary.
claims_prev: uint64          # claims paid in the previous epoch. Genesis: 0.
epoch_budget: TokenValue     # fixed at the boundary
epoch_reward: TokenValue     # fixed at the boundary (R6)
epoch_spent: TokenValue      # paid so far this epoch
saturation_block: uint64     # block index at which epoch_spent first exceeded epoch_budget; unset otherwise
difficulty_target: PowTarget # as today
```

The regime is not stored; it is read: **bootstrap iff `endowment > 0`** (Q6 — `endowment`
only ever falls, so the transition fires once and cannot flap).

## 3. Epoch boundary

```python
def on_epoch_boundary(e):
    fee_bucket   = fee_bucket_remaining + fee_accrual      # unspent F rolls forward; see note
    fee_accrual  = 0

    if endowment > 0:                                      # ---- bootstrap
        epochs_left  = max(1, BOOTSTRAP_EPOCHS - e)
        sub_pool     = endowment // epochs_left            # linear amortisation (plan 1.1)
        epoch_budget = sub_pool + fee_bucket
        epoch_reward = max(anchor(),                       # R8: never below the anchor
                           epoch_budget // max(claims_prev, BLOCKS_PER_EPOCH))
    else:                                                  # ---- post-bootstrap
        epoch_budget = fee_bucket                          # R7a: last epoch's fees, raw (Q3)
        epoch_reward = anchor()                            # R8: the anchor exactly

    epoch_spent  = 0
    claims_prev  = claims_paid_last_epoch
```

**The anchor** (R8, with the stated transfer ≈ inscription assumption):

| `anchor = 2 * tx_fee(transfer_tx_bytes, transfer_tx_gas)` — at the epoch-boundary market prices |
| --- |

At the resting prices this is `2 × 5,579 = 11,158` lepta — above the claim's own fee of 6,664,
so a claim at the anchor is always worth submitting. The anchor moves with the fee markets by
construction; no parameter.

**The bootstrap reward** (Q1, demand-indexed, with two floors made explicit):
`max(claims_prev, BLOCKS_PER_EPOCH)` in the divisor caps the reward at one block's budget
share, so a quiet epoch cannot make a single claim worth the whole sub-pool (`claims_prev = 0`
at genesis); `max(anchor, ·)` keeps R8's ordering — the bootstrap reward is never below the
post-phase one. The reference triple opens at `budget_0 // 21,600 ≈ 1.19e10` lepta ≈ **11.9
LGO per claim** — about ten times the old design's opening, because a four-year linear spend
is faster than a 1/200 geometric one.

**Rollover note.** Q3 says the post-phase budget is the previous epoch's fees, *raw*. When an
epoch under-spends (the throttle overshot), the unspent remainder stays in `fee_bucket` and
joins the next budget rather than being destroyed — R6 forbids destroying pool money, and
sending it to `endowment` would resurrect the bootstrap regime. This is the one refinement of
Q3's letter, and it is forced by R6 + Q6 jointly.

## 4. Per block

### 4.1 Admission and payment

A claim valid under the existing puzzle rules is **paid** iff the pool can cover it, drawing
`fee_bucket` first, then `endowment` (fees are flow-through; the endowment is the subsidy of
last resort — and, past the budget, Q2's borrow source):

```python
def try_pay_claim():
    if endowment > 0:                                     # bootstrap: R6 saturation semantics
        if fee_bucket_remaining + endowment < epoch_reward:
            return REJECTED                               # the pool itself is empty
    else:                                                 # post: the budget is the limit
        if epoch_spent + epoch_reward > epoch_budget:
            return REJECTED                               # saturated; wait for next epoch
    draw = min(epoch_reward, fee_bucket_remaining)
    fee_bucket_remaining -= draw
    endowment            -= epoch_reward - draw           # 0 in the post regime by the guard
    epoch_spent          += epoch_reward
    if epoch_spent > epoch_budget and saturation_block is unset:
        saturation_block = current_block                  # the (sub)pool saturation point
    return PAID
```

Bootstrap admissions past the budget draw the **undivided endowment** (Q2): the spike thins
every later sub-pool through the `endowment // epochs_left` recomputation and pulls the
phase's end earlier. No cliff, no cap, no cohort turned away while the endowment lasts — R5.

Post-bootstrap there is nothing to borrow from — R7a's budget is the limit, and the throttle's
whole job is to make hitting it coincide with the epoch's end.

### 4.2 The difficulty

**Bootstrap: a constant floor.** The difficulty holds at the genesis seed (`p / 2^26`) for the
whole phase. It is spam protection, not a controller: admission control is economic
(saturation + the demand-indexed reward), and a cohort's arrival must not be met with a rising
work price — that is R5, and it is why the retarget is *off* here (§9).

**Post-bootstrap: the existing retarget, with a derived target.**

```python
capacity          = epoch_budget // epoch_reward                    # claims the budget can pay
claims_target     = max(1, capacity // BLOCKS_PER_EPOCH)            # per block
difficulty_target = compute_new_reward_difficulty(claims_in_block, difficulty_target)
                    # the unchanged EMA machinery, against claims_target
```

The machinery is exactly today's; only the target stops being a constant. Its objective is
R7b: claims spread evenly, the saturation point steered toward the epoch end. The `max(1, ·)`
floor matters only while `capacity < 21,600` — a sparsely-funded network — where the epoch
saturates early by necessity; at the reference traffic (600 txs/block) the capacity is
`0.1 · 600 · 21,600 · 5,579 / 11,158 = 648,000` claims, a target of 30 per block, comfortably
interior.

At the transition the difficulty starts from the floor and the EMA walks it to the first
post-phase equilibrium within its usual ~10-block time constant; no special-case rule.

## 5. The regimes, summarised

| | bootstrap (`endowment > 0`) | post (`endowment == 0`) |
| --- | --- | --- |
| purpose | onboard nodes (R3) | sustain claiming from fees (R7) |
| budget | `endowment // epochs_left + fee_bucket` | `fee_bucket` |
| reward | `max(anchor, budget // max(claims_prev, blocks))` | `anchor` |
| on saturation | continue, drawing the endowment (Q2) | stop for the epoch |
| difficulty | constant floor | EMA throttle at `capacity / blocks` |
| ends | endowment exhausted — at `BOOTSTRAP_EPOCHS` on expectation, earlier under spikes, later under weak interest | — |

Weak-interest tail: if the expected duration passes with endowment remaining (arrivals below
expectation), `epochs_left` floors at 1 and each further epoch offers the whole remainder as
its sub-pool until it is claimed. The phase ends when the money is gone, not when the clock
says so — in both directions.

## 6. Closed forms (for gating the simulator)

With `B = BOOTSTRAP_EPOCHS`, `E_0 = ENDOWMENT_GENESIS`, uniform arrivals at the equilibrium:

- **Endowment trajectory, no saturation:** `E_e = E_0 · (1 − e/B)` exactly (linear; floor
  residue rolls forward).
- **Claims to a bond at reward R:** `ceil(min_stake / (R − claim_fee))`. At the opening
  reference reward: `1e12 / (1.19e10 − 6.7e3) ≈ 85` claims.
- **Fee drag:** each claim returns `claim_fee / R` of itself to the fee flow; the pool-to-bond
  conversion is bounded above by `1 − claim_fee / R` before any stranding. At the opening
  reward the drag is ~6e-7 — negligible; it grows as the reward falls toward the anchor,
  reaching `6,664 / 11,158 = 59.7%` at the anchor itself. **The subsidy is what keeps the
  drag small; the post-phase runs hot by construction** and the report must show it.
- **Saturation point under a ×k offered-demand spike (bootstrap):** claims arrive ~k× the
  epoch's expectation, the budget covers `1/k` of them, so
  `saturation_block ≈ BLOCKS_PER_EPOCH / k`, and the endowment draw beyond budget is
  `(k − 1) · sub_pool` for the epoch (all bounded by `endowment`).
- **Phase shortening:** a one-epoch ×k spike consumes ≈ `(k − 1)` extra sub-pools, moving the
  expected end earlier by ≈ `(k − 1)` epochs while thinning later sub-pools by the
  recomputation.
- **Post-phase equilibrium:** `capacity = pow_share · txs_per_epoch · tx_fee / anchor =
  pow_share · txs_per_epoch / 2` — at 600 txs/block, 648,000 claims an epoch, exactly 30 a
  block. Elegant and worth gating: **at the anchor of two transfers, the post-phase capacity
  is half the diverted transaction count, independent of the fee level.**

## 7. Worked reference triple

`(0.5%, 25,000, 4 yr)`: endowment 5e16 lepta (50M LGO), 195 epochs, opening sub-pool
≈ 256,410 LGO/epoch, opening reward ≈ 11.9 LGO falling toward the anchor as participation
grows; implied efficiency 50% — satisfiable only in the retiring regime, which the report must
state as the triple's built-in assumption.

## 8. Analysis obligations (known risks, owned before simulation)

1. **Demand-index oscillation.** `reward_{e+1} = budget / claims_e` with entry/exit elasticity
   can two-cycle: heavy epoch → small reward → exit → light epoch → big reward → re-entry.
   The simulator must test for limit cycles across elasticities; the EMA-smoothed index is the
   recorded fallback (Q3's rejected alternative, same trade).
2. **Whale drain.** With the difficulty floored, nothing rate-limits a single large actor
   converting the endowment to its own balance quickly; R6 accepts this literally (the pool
   pays until exhausted) and the conversion-efficiency band is where it shows. Quantify: end
   date and per-cohort admission under a whale of 10–100× the honest field.
3. **Block-space contention.** Floored difficulty + a spike puts claims in competition with
   ordinary transactions inside `MAX_BLOCK_TXS`; the fee market responds. Quantify the
   crowding at ×10/×100 spikes.
4. **Sparse-capacity regime.** `capacity < blocks_per_epoch` post-phase forces target 1 and
   early saturation; quantify the R7b deviation vs traffic level.

## 9. Amendment to Q4, on the record

Q4 was settled as "one throttle, both phases". Writing §4 formally shows that composes badly
with Q1 and R5/R6: with the reward demand-indexed at `budget / claims_prev`, the interior
capacity is `claims_prev` itself, so a throttle at `capacity / blocks` **pins admissions at
the previous epoch's level** — the spike is never admitted, the index never sees it, the
reward never adjusts, and the cohort is rationed indefinitely. That is exactly the behaviour
R5 rejects, and it would leave R6's saturation semantics dead code (saturation presupposes
claims can exceed the budget).

The amendment keeps the *machinery* unified — one retarget implementation — but the bootstrap
runs it against a **constant floor** rather than a derived target: admission control during
bootstrap is economic (saturation + reward), and mechanical (the throttle) only after the
transition, where rationing to the fee budget is the stated objective (R7b). The plan's Q4
entry is amended with this reasoning; the alternatives table for the report gains the
"unified throttle" as a rejected option with this failure mode as its description.
