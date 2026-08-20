# Attacking both designs — an adversarial analysis by simulation

## What this document is

Concrete attacks, run in the simulators, against both the currently specified EmPoWering mechanism and the de-novo redesign. Every number comes from a run with a hostile actor in it, measured against the honest baseline of the same configuration — not from reasoning about what an attacker might achieve. The de-novo attacks use `empowering_denovo_sim.adversary`, which reuses the engine's admission rules exactly, so an attack the model resists it resists for the model's reasons rather than a simplification's. The current-design attacks drive `empowering_sim.elevation` unmodified.

Costs are priced from the standalone estimator at a Raspberry Pi 5's measured Poseidon2 rate, whole-platform, 20 cents a kilowatt-hour.

**The most important finding is not an attack at all.** Both designs' onboarding targets assume that miners stop mining once they have bonded, and that assumption is not incentivised — continuing to mine is individually rational, and bonding does not stop the hardware. The behaviour both designs need in order to hit their numbers is the behaviour neither pays for. Everything else below is secondary to that.

*Revision note.* A first version of this analysis compared the two designs' sybil-flood resistance at different honest baselines and over different windows, and concluded they were comparably vulnerable. Normalised — same honest arrival rate, same window — they are not, and the redesign is markedly the more resistant at moderate flooding. §4 carries the corrected measurement.

## 1. The threat model

An attacker with hashrate and the ability to create identities freely, who may withhold or time its participation, and who is content to spend money to deny others as well as to profit. It cannot break the puzzle, forge a claim, or violate consensus. Both mechanisms pay claims in proportion to hashrate within an epoch and gate service provision on a locked bond, so the attack surface is economic throughout.

## 2. The assumption underneath both designs

### 2.1 Nothing pays anyone to retire

Both designs quote two onboarding numbers, one assuming bonded miners keep mining and one assuming they retire, and both lean on the retiring figure. The strategy report measures 11.4% against 51.9% of the elevation ceiling; the de-novo consistency identity takes that as its band, and its reference triple implies exactly 50% — the retiring edge.

The justification on record is that a bonded node's service income dwarfs what more mining would add. That is true and beside the point. A node decides whether to keep mining by comparing the *marginal* revenue of another claim against its *marginal* cost, and having a larger income elsewhere does not enter that comparison. Nor is there any capacity conflict to force a choice: **a bonded node can provide service and go on mining with the same hardware.**

Priced at the de-novo bootstrap reward:

| | net revenue per claim | electricity per claim (Pi 5) | keeps mining while a token is worth more than |
| --- | --- | --- | --- |
| bootstrap, opening reward | 11.87 LGO | $0.00136 | **$0.000114** |
| post-phase, at the anchor | 4.494 × 10⁻⁶ LGO | $0.00136 | $302 |

**During bootstrap, continuing to mine is rational at any plausible token price.** The retiring assumption is therefore an assumption about altruism or inattention, not about incentives — and it is the assumption both designs' headline numbers rest on. (Post-phase the sign flips and mining stops paying, which is §5.)

### 2.2 What it costs when the assumption fails

Modelled in the de-novo engine as a coalition that bonds and keeps mining anyway:

| coalition refusing to retire | total bonds | against the honest baseline | cost to the coalition |
| --- | --- | --- | --- |
| none | 24,723 | 1.00× | — |
| 10% | 20,150 | 0.82× | none — they keep earning |
| 25% | 15,562 | **0.63×** | none — they keep earning |
| 50% | 11,555 | 0.47× | none — they keep earning |
| everyone | 8,140 | **0.33×** | none — they keep earning |

A quarter of the field behaving this way costs the mechanism 37% of its onboarding; the whole field behaving this way costs two thirds. **This is the cheapest and most damaging attack in either design, it requires no coordination, and an attacker cannot be distinguished from a participant who simply never turned its miner off.** The same arithmetic applies to the current design, where the identical behaviour is what separates its 11.4% and 51.9% figures.

The remedy is not in either mechanism as specified. Making retirement rational needs something that prices continued mining after bonding — a declining per-identity reward, a bond that competes with hashrate, or an explicit exit incentive — and all of those are new mechanism. **What both designs can do immediately is stop quoting the retiring figure as the expected case.** Under the persistent regime the de-novo reference triple implies an efficiency of 50% against an achievable 11.4%, which its own feasibility check would reject.

## 3. The redesign's novel surfaces — both close by measurement

### 3.1 The pump — withhold to inflate the reward, then flood. **Defeated below half the field.**

The de-novo bootstrap reward is `budget / claims_prev`, which invites the obvious manipulation: mine nothing this epoch so the denominator collapses, then claim everything next epoch at the inflated price. The attacker withholds on even epochs and floods on odd ones, against the same actor mining honestly throughout:

| attacker's share of the field | balance, mining honestly | balance, pumping | advantage |
| --- | --- | --- | --- |
| 10% | 1,062,468 LGO | 566,776 LGO | **0.53×** |
| 25% | 2,650,814 | 1,700,500 | **0.64×** |
| 50% | 5,299,253 | 4,986,983 | **0.94×** |
| 75% | 7,952,245 | 9,887,684 | 1.24× |
| 90% | 9,540,992 | 11,991,523 | 1.26× |

**Withholding loses money for any minority**, and the result is robust to the assumed field size — at a quarter of the field the pump returns 0.51×, 0.64× and 0.35× of honest mining across fields of 100, 1,000 and 10,000 Pi 5s.

The defence is the reward's own cap. `epoch_reward = max(anchor, budget // max(claims_prev, blocks_per_epoch))` floors the divisor at the block count, so however far a minority shrinks `claims_prev`, the reward cannot rise past one block's budget share — measured, it oscillates 8.76 / 4.40 / 8.77 / 4.36 LGO, a factor of two, against forfeiting an entire epoch's claims.

That cap was written for a different problem: at genesis `claims_prev` is zero and something must stop one claim taking the whole sub-pool. It is the manipulation defence as well, which is the happiest accident in the design — and it is now gated, so it cannot be removed as dead weight.

Past half the field the pump does pay, at 1.24×. That is not a new exposure: an actor holding three quarters of the hashrate *is* the whale of §3.3, and Q8 accepts that case explicitly.

### 3.2 The manufactured cliff — harvest the period-2 cycle. **Unprofitable.**

Q9 accepts a documented hazard: a sharp participation threshold at the operating reward drives a period-2 cycle. The attack is to *be* that threshold — mine only above a bar, harvesting the high epochs:

| attacker's entry threshold | against always-on |
| --- | --- |
| 3 LGO | 0.96× |
| 5 LGO | 0.59× |
| 8 LGO | **0.02×** |

**Being picky costs more than it harvests, at every threshold**, for the same reason the pump fails: skipped epochs forfeit more than elevated rewards return. Q9's cycle is a user-experience hazard — a badly-chosen wallet default could make a *population* oscillate to everyone's detriment — but not an exploit anyone profits from.

### 3.3 The whale — conceded, and now bounded in time

Q8 keeps the borrow-forward unbounded, so a large actor can draw the endowment through the demand index's one-epoch lag. When it should arrive:

| whale arrives at epoch | endowment captured (10× the field it meets) | phase ends | honest bonds |
| --- | --- | --- | --- |
| 2 | 20% | 196 | 24,554 |
| **20** | **88%** | **23** | **2,544** |
| 50 | 72% | 54 | 6,382 |
| 100 | 22% | 196 | 20,644 |
| 150 | 19% | 153 | 19,191 |

**The danger window is early but not immediate.** At genesis the whale takes only 20%, because `claims_prev = 0` caps the reward at one block's share. By epoch 20 the honest field has established a `claims_prev` large enough to price the epoch generously while the endowment is still 90% intact — 88% capture, and the bootstrap collapses from 195 epochs to 23. By epoch 100 the endowment is half spent and the exposure falls back.

This sharpens the accepted risk rather than changing it. If the Q8 cap is ever revisited, a bound applying only to the early epochs would buy most of the protection at the least cost to R5 — the honest ×100 cohort that needs 86–111× its budget arrives at epoch 30.

## 4. The sybil flood — and the correction

Neither mechanism has any defence against one actor presenting as many, so the strongest denial attack on both is to flood the field with identities and take a share of the on-ramp proportional to what you can afford. Measured at the **same honest arrival rate and the same window** for both designs — 100 honest arrivals an epoch, 400 epochs, retirement on:

| flood, × the honest rate | honest elevations denied, current | honest bonds denied, de novo |
| --- | --- | --- |
| 1× (baseline) | — | — |
| 2× | **48.4%** | **3.5%** |
| 5× | 88.9% | 76.2% |
| 10× | 96.3% | 92.8% |

*Baselines: 25,934 honest elevations in the current design, 19,082 honest bonds in the redesign.*

**At moderate flooding the redesign is an order of magnitude more resistant** — doubling the field costs honest joiners 3.5% of their bonds against 48.4%. The reason is structural: the current design's claim flow is fixed, so twice the field is half the share each, while the redesign's budget converts whoever is present, so a doubled field simply converts faster. At extreme flooding both collapse, because there the binding constraint is the same in both — the payout strands below the bond faster than anyone crosses it.

A first version of this document measured the two designs at different honest rates and over different windows, and concluded they were comparably vulnerable. That was an artefact of the mismatch; the corrected comparison above is the one to use.

What the extreme case costs the attacker, at flood rates achieving ~95% denial: on the order of a quarter-million devices in both designs — $20M or more of hardware capital before any electricity, which is the real barrier — with electricity of $12.8M (current, 600 epochs) against $4.5M (de novo, 220 epochs). The redesign is cheaper to besiege in absolute terms only because its bootstrap is shorter, which is the same property that makes it converge faster.

One asymmetry favours the redesign throughout. **An arrival flood cannot accelerate its drain**: the transition holds at epoch 195–197 at every flood rate tested, because the budget schedule governs what an epoch may spend. Only a *hashrate* whale shortens the phase (§3.3). The redesign therefore separates two attacks the current design conflates — many small identities dilute the on-ramp but cannot shorten it, while one large actor can shorten it but is visible in a way many small ones are not.

## 5. What the redesign converges to, and whether it matters

Post-phase, the anchor nets 4.494 × 10⁻⁶ LGO per claim after the claim's own fee, against $0.00136 of electricity. Mining therefore stops paying, and the field shrinks until it does — the self-correcting equilibrium:

| token price | equilibrium mining field |
| --- | --- |
| $0.01 | 0.4 Pi 5-equivalents |
| $1.00 | 37 |
| $100 | 3,677 |

**Proof of work becomes vestigial once the endowment is spent**, supporting a field of tens of devices at plausible token prices. That is R8 working as specified rather than a defect — the brief asked that the post-phase pay "a very minimal amount", and a reward defined as exactly one transfer plus one inscription delivers exactly that. It is worth stating plainly because it means the post-phase provides no security and should not be relied on for any: whatever the chain needs proof of work *for* after bootstrap, this reward will not fund it.

## 6. What follows

**For both designs, and first.** The retiring assumption is not incentivised, costs a third to two thirds of onboarding when it fails, and is indistinguishable from ordinary inattention. Either stop quoting the retiring figure as the expected case — which makes the de-novo reference triple infeasible by its own check and should move the triple — or add a mechanism that prices continued mining after bonding. This is the one finding here that should change a decision.

**For the redesign.** Both of its novel surfaces are closed by measurement rather than argument, and gated. The whale exposure is real, accepted, and concentrated in the first quarter of the phase. Its sybil resistance at moderate flooding is markedly better than the current design's, which is a point in its favour that the first version of this analysis missed.

**For the current design.** Its immunity to reward manipulation is structural — a pool-determined reward cannot be pumped — and worth counting as the redesign's opportunity cost. Its flow cap makes it undrainable by any actor.

**For the protocol.** The sybil flood is cheap relative to what it denies and neither design addresses it, because neither has a notion of identity beyond a keypair and a claim fee. Every candidate remedy — a bond to mine, proof of personhood, a per-identity rate limit — is outside both designs and outside the eight principles the redesign was built from. It belongs on the record as an open problem of the protocol rather than a defect of either mechanism.

## 7. Reproducing this

```
cd tools/simulators/empowering-denovo
make validate                     # the adversarial findings are gated
PYTHONPATH="src:../empowering/src" python3 -m empowering_denovo_sim.adversary
```

The pump, the cliff and the two-population engine are in `adversary.py`; the retirement-denial run uses `engine.run(..., refuse_fraction=)`; the whale timing sweep uses `scenarios.whale_run`; the current-design runs drive `empowering_sim.elevation` with no modifications.
