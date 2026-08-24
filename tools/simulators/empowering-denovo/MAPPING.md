# Mapping the de-novo model onto the existing machinery

Phase B of `PLAN.md`. Mechanism by mechanism: what survives untouched, what changes meaning,
what is deleted, and which specification document each change lands in. This is what makes
the redesign adoptable rather than academic.

## How to read this

*In plain words: this design was worked out from first principles, deliberately ignoring how
the current system is built. That is useful for thinking and useless for shipping — so this
document does the reconciliation. It answers one question per row: for each piece of the
existing specification, does the redesign keep it, change it, or delete it?*

*Read §1 to see how little actually changes: most of the machinery is reused untouched, and
the genuinely new rules are few enough to list. §2 covers the pieces whose meaning shifts even
though their name does not — the easiest kind of change to miss when implementing.*

## 1. Untouched — consumed as-is

| mechanism | where it lives | note |
| --- | --- | --- |
| claim operation `CLAIM_POW_REWARD` | `mantle` §Proof of Work Operations | payload, ticket derivation, nullifier, acceptance window, Groth16 proof — byte-for-byte |
| self-funding claim | `mantle` (interleaving + epoch-fixed reward) | preserved by Q5: the reward is still known at claim-construction time |
| fee diversion (`POW_SHARE`) | `overview-cryptoeconomics` §PoW Reward Pool; under lips PR 375, a carve-out from `block-rewards`' pending rewards pool | same 10%, same per-block flooring; lands in `fee_accrual`. **Decided 2026-08-24**: fees enter the pool in full and this is the pool's first outflow, not an interception ahead of it (contradiction 4.13) |
| retarget implementation | `mantle` `compute_new_reward_difficulty` | the function is reused verbatim; only its target argument and *when it runs* change |
| SDP / `min_stake` bond | `bedrock-service-declaration-protocol` | the onboarding destination; untouched |
| service rewards, 60/40 split, release control | `block-rewards` 1.1.0, `bedrock-service-reward-distribution` | the reward *level* this design reads is unchanged (the release cap, 95.13 LGO/block at `A_t = 1`); the substrate under it is PR 375's — see §1.1 |
| both fee markets | `execution-market` 1.2.0, `storage-markets` | pricing formulas untouched, so the anchor still *reads* their epoch-boundary prices; their fees now route to the pending rewards pool rather than burning, which is where the carve-out above draws from |
| units | *Logos Token: Units and Precision* | everything in lepta, as before |

### 1.1 The substrate is the RFC's own pattern

Lips PR 375 (`block-rewards.md` 1.1.0) replaces burning/minting with
pooling/distributing/releasing, and this design — written against the burn/mint model — maps
onto it term for term rather than needing an exception from it:

| PR 375 | this design |
| --- | --- |
| genesis-minted reserve `B_0`, pre-allocated from the cap | the endowment: a genesis-minted **sub-reserve** — our term for the analogy; the RFC specifies one undivided `B_t` and says nothing about subdividing it |
| metered release `ι_t = min(schedule, B_{t−1})` | `sub_pool = endowment // (B − e)`, the linear amortisation |
| reserve "lasts Y years at max rate, longer when `A_t < 1`" | Q7's nominal-rate tail |
| depleted-reserve fallback to recycled fees | the dust fold, then the fee-bucket post-phase |
| pending rewards pool `P_t` | `fee_bucket`: the PoW-share view of a draw against `P_t` |
| conservation `ΔS + ΔP + ΔB = 0` | the conservation-to-the-lepton gate |

So the adoption pitch under the new substrate is not "a mechanism beside the reward system"
but **a second metered release from a dedicated sub-reserve, with its own schedule and its
own demand index** — the same shape the reward system itself now has.

## 2. Changed meaning

**The pool.** `pow_reward_pool: TokenValue` becomes two components,
`endowment` + `fee_bucket` (+ `fee_accrual` within the epoch). Total value is conserved
identically; the split exists so the regime test `endowment > 0` is monotone (Q6). Spec
change: the consensus-state block in `mantle` §Proof of Work Operations.

**`compute_epoch_pow_reward`.** Replaced by the boundary rules of `MODEL.md` §3: budget from
linear amortisation plus fees, reward demand-indexed with the anchor floor (bootstrap) or the
anchor exactly (post). Same call site, same "runs at the epoch boundary, fixes the epoch's
value" contract.

**The pool guard in claim validation.** Today: pool covers the reward, net of predecessors.
New: the regime-aware guard of `MODEL.md` §4.1 — bootstrap admits while the *pool* covers it
(budget overrun draws the endowment: the saturation semantics), post admits while the
*budget* does. Same interleaved-validation structure `mantle` §217 already mandates.

**The retarget's target and schedule.** `TARGET_CLAIMS_PER_BLOCK` stops being a constant.
Bootstrap: the retarget does not run; the difficulty holds at the genesis seed, which is
repurposed as the spam floor. Post: the retarget runs every block as today, against the
derived `max(1, capacity // BLOCKS_PER_EPOCH)` recomputed each epoch boundary.

**Genesis parameters.** `POW_REWARD_POOL_GENESIS` (a fraction of launch supply) carries over
as `ENDOWMENT_GENESIS` = `POOL_FRACTION`. Two genesis values join it: `EXPECTED_NODES` and
`EXPECTED_YEARS` — with the consistency identity checked at genesis-parameter time
(`bedrock-genesis-block`).

## 3. Deleted

| constant / concept | why it goes |
| --- | --- |
| `EPOCH_POW_DISTRIBUTION_RATE_NUM/_DEN` (ρ = 1/200) | the rate is replaced by the budget; the phase now *ends* |
| `TARGET_CLAIMS_PER_BLOCK = 10` as an economic constant | the claim count is a consequence (`capacity`), not a target; survives only as the post-phase *derived* target |
| the claim count as the difficulty's objective during bootstrap | R5: admission control is economic; the difficulty is a floor |
| the "reward decays geometrically forever" regime | replaced by two regimes with an automatic, irreversible transition |

Everything the deleted constants used to justify (drain-safety `T/ρ > max_block_txs`, the
within-epoch exhaustion margin) must be re-derived for the budget design in the report — the
exhaustion question in particular becomes the saturation point, which is now a *feature* with
defined semantics rather than a hazard to be excluded.

## 4. Specification documents touched, and how much

| document | change |
| --- | --- |
| `mantle` §Proof of Work Operations | the substantive rewrite: consensus state, boundary rules, admission guard, retarget schedule. The operation itself, ticket, nullifier and window sections stand |
| `bedrock-genesis-block` | `ENDOWMENT_GENESIS` + the two new genesis values + the identity check |
| `overview-cryptoeconomics` §PoW Reward Pool | narrative: budgets and two regimes instead of ρ-decay; the diversion section stands |
| everything else | no change |

### 4.1 What **de novo\*** would additionally change

The asterisked variant (MODEL §8.5) touches exactly one rule and adds exactly one constant, which is the main argument for it being adoptable at all:

| document | change |
| --- | --- |
| `mantle` §Proof of Work Operations | the admission guard gains a per-epoch bound: an epoch may draw `sub_pool + draw_cap_fraction * endowment` from the endowment, no more. The guard's structure, the interleaving, and the saturation-point semantics are unchanged |
| `bedrock-genesis-block` | one new genesis constant, `draw_cap_fraction` |
| everything else | no change — the reward rule, the schedule, the transition, the retarget and the fee plumbing are all untouched |

Nothing is refused permanently under the bound and no money is destroyed: claims beyond the cap are made by the same nodes in later epochs. So the variant does not disturb the conservation argument, and the "pays until exhausted" language in `overview-cryptoeconomics` would need one qualifying clause rather than a rewrite.

## 5. Simulator reuse map (Phase C)

| existing verified component | role in `empowering_denovo_sim` |
| --- | --- |
| `empowering_sim.config` + `txsize` | fee model, lepta arithmetic, transaction sizes — the anchor is computed from them |
| `empowering_sim.work.next_difficulty_target` | the post-phase throttle, called with the derived target |
| `empowering_sim.work` Poisson/multinomial machinery | claim arrivals and attribution, unchanged reasoning |
| `powcost` (via `empowering_sim.market`) | device classes, electricity, break-evens for the whale/spike scenarios |
| `empowering_sim.elevation` patterns | arrival processes and conversion tracking (retire / persist brackets) |
| `empowering_sim.economics.pay_claims` | **replaced** by the two-bucket engine — the one genuinely new core |
| gate style (`validate.py`) | reproduced: every closed form of `MODEL.md` §6 becomes a gate |
