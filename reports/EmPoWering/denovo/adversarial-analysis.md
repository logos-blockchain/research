# Attacking both designs — an adversarial analysis by simulation

## What this document is

Concrete attacks, run in the simulators, against both the currently specified EmPoWering mechanism and the de-novo redesign. Every number below comes from a run with a hostile actor in it, measured against the honest baseline of the same configuration — not from reasoning about what an attacker might achieve. The de-novo attacks use `empowering_denovo_sim.adversary`, which reuses the engine's own admission rules, so an attack the model resists it resists for the model's reasons rather than a simplification's. The current-design attacks drive `empowering_sim.elevation` unmodified.

Costs are priced from the standalone estimator at a Raspberry Pi 5's measured Poseidon2 rate, whole-platform, 20 cents a kilowatt-hour.

The headline: **each design resists what the other concedes, and both fall to the same attack.** The redesign's demand-indexed reward turns out to defend itself better than expected — the cap that exists for the genesis epoch also defeats manipulation — while the property both designs share, no defence against identity multiplication, is the one that actually denies honest users the on-ramp.

## 1. The threat model

An attacker with hashrate and the ability to create identities freely, who may withhold or time its participation, and who is content to spend money to deny others (griefing) as well as to profit. It cannot break the puzzle, forge a claim, or violate consensus. Both mechanisms pay claims in proportion to hashrate within an epoch and gate service provision on a locked bond, so the attack surface is economic throughout.

## 2. The redesign under attack

### 2.1 The pump — withhold to inflate the reward, then flood. **Defeated below half the field.**

The de-novo reward is `budget / claims_prev` during bootstrap, which invites an obvious manipulation: mine nothing this epoch so `claims_prev` collapses, then claim everything next epoch at the inflated price. Run it — the attacker withholds on even epochs and floods on odd ones, against the same actor mining honestly throughout:

| attacker's share of the field | balance, mining honestly | balance, pumping | advantage |
| --- | --- | --- | --- |
| 10% | 1,062,468 LGO | 566,776 LGO | **0.53×** |
| 25% | 2,650,814 | 1,700,500 | **0.64×** |
| 50% | 5,299,253 | 4,986,983 | **0.94×** |
| 75% | 7,952,245 | 9,887,684 | 1.24× |
| 90% | 9,540,992 | 11,991,523 | 1.26× |

**Withholding loses money for any minority.** The reason is the reward's own cap. `epoch_reward = max(anchor, budget // max(claims_prev, blocks_per_epoch))` floors the divisor at the block count, so however far a minority shrinks `claims_prev`, the reward cannot rise past one block's budget share — measured, it oscillates 8.76 / 4.40 / 8.77 / 4.36 LGO, a factor of two, against forfeiting an entire epoch's claims. The trade is never worth it.

That cap was written for a different problem: at genesis `claims_prev` is zero and something must stop one claim taking the whole sub-pool. It turns out to be the manipulation defence as well, which is the happiest accident in the design — and it is now gated, so it cannot be removed as dead weight.

Past half the field the pump does pay, at 1.24×. That is not a new exposure: an actor holding three quarters of the hashrate *is* the whale of §2.2, and Q8 accepts that case explicitly.

### 2.2 The whale — and the timing that makes it worst. **Conceded, and now bounded in time.**

Q8 keeps the borrow-forward unbounded, so a large actor can draw the endowment through the demand index's one-epoch repricing lag. The report measured the capture curve; the question left open was when the whale should arrive:

| whale arrives at epoch | endowment captured (10× the field it meets) | phase ends | honest bonds |
| --- | --- | --- | --- |
| 2 | 20% | 196 | 24,554 |
| **20** | **88%** | **23** | **2,544** |
| 50 | 72% | 54 | 6,382 |
| 100 | 22% | 196 | 20,644 |
| 150 | 19% | 153 | 19,191 |

**The danger window is early but not immediate.** At genesis the whale takes only 20%, because `claims_prev = 0` caps the reward at one block's share and the sub-pool is one epoch's worth. By epoch 20 the honest field has established a `claims_prev` large enough to price the epoch generously while the endowment is still 90% intact — 88% capture, and the bootstrap collapses from 195 epochs to 23. By epoch 100 the endowment is half spent and the exposure falls back to 22%.

This sharpens the accepted risk rather than changing it. A design owner choosing to keep Q8 unbounded should know the exposure is concentrated in roughly the first quarter of the phase, which is also where a cap would cost the least in spike tolerance — the ×100 honest cohort in the report arrives at epoch 30 and needs 86–111× its budget.

### 2.3 The manufactured cliff — harvest the period-2 cycle. **Unprofitable.**

Q9 accepts a documented hazard: a sharp participation threshold sitting at the operating reward drives a period-2 cycle. The attack is to *be* that threshold deliberately — mine only when the reward clears a bar, harvesting the high epochs and sitting out the low ones:

| attacker's entry threshold | balance | against always-on |
| --- | --- | --- |
| 3 LGO | 4,542,257 | 0.96× |
| 5 LGO | 2,775,770 | 0.59× |
| 8 LGO | 109,539 | **0.02×** |

**Being picky costs more than it harvests, at every threshold.** The mechanism is the same as the pump's: the epochs skipped are worth more in forfeited claims than the elevated reward in the epochs taken. Q9's cycle is therefore a user-experience hazard — a badly-set wallet default could make a *population* oscillate to everyone's detriment — but not an exploit anyone profits from. That distinction is worth having explicitly, and it is gated.

## 3. The current design under attack

### 3.1 Structural immunity to both manipulations

The current reward is `distribution_rate * pool / (target_claims * blocks)` — it does not reference demand at all. Withholding therefore changes nothing about the price, and there is no cliff to harvest, so §2.1 and §2.3 have no analogue here. This is a genuine advantage of a pool-determined reward and should be recorded as one.

### 3.2 The whale is capped by the flow, not by the pool

Because the controller holds the claim count flat against any load, no actor can accelerate the outflow. Driving the arrival rate up twentyfold barely moves what the mechanism ever elevates:

| arrivals an epoch (bonded miners keep mining) | elevated over 600 epochs |
| --- | --- |
| 50 | 5,708 |
| 250 | 5,647 |
| 1,000 | 4,462 |

The endowment cannot be drained faster than the schedule by anyone, which is the property the redesign trades away.

## 4. The attack both designs share, and neither resists

Neither mechanism has any defence against one actor presenting as many. So the strongest attack against both is not extraction but **denial**: flood the field with sybils, take a share of the on-ramp proportional to the identities you can afford, and leave the honest joiners with the remainder.

**The current design**, honest baseline 50 arrivals an epoch with retirement, 20,306 honest elevations:

| attacker adds | total elevated | honest elevations | honest denied |
| --- | --- | --- | --- |
| — | 20,306 | 20,306 | — |
| 50/epoch | 27,645 | 13,822 | 6,484 |
| 200/epoch | 25,247 | 5,049 | 15,257 |
| 450/epoch | 15,275 | 1,528 | **18,778 (92.5%)** |

**The redesign**, honest baseline 130 arrivals an epoch, 24,723 honest bonds:

| attacker adds | total bonds | honest bonds | honest denied |
| --- | --- | --- | --- |
| — | 24,723 | 24,723 | — |
| 130/epoch | 39,390 | 19,695 | 5,028 |
| 520/epoch | 18,214 | 3,643 | 21,080 |
| 1,170/epoch | 11,874 | 1,187 | **23,536 (95.2%)** |

Both collapse to near-total denial, and both do so while the *attacker's own* take shrinks at the extreme — this is griefing, not extraction. The difference in shape is instructive: at moderate flooding the redesign's total onboarding **rises** (39,390 against 24,723) because the budget converts whoever is present, while the current design's total is flow-capped. Past that, both fall as the payout strands below the bond.

What it costs, at the flood rates that achieve ~95% denial:

| design | flood | sybils | window | electricity | denied | USD per denial |
| --- | --- | --- | --- | --- | --- | --- |
| current | 450/epoch | 270,000 | 600 epochs | $12.8M | 18,778 | $683 |
| de novo | 1,170/epoch | 257,400 | 220 epochs | $4.5M | 23,536 | **$191** |

**The redesign is roughly three times cheaper to grief**, and the reason is its own virtue: the bootstrap is 195 epochs rather than an endowment that lasts past 600, so the attacker sustains the flood for a third as long. Both attacks need on the order of a quarter-million devices, which at Pi 5 prices is $20M or more in capital before any electricity — the real barrier in both cases is hardware, not power.

One asymmetry favours the redesign. **An arrival flood does not accelerate its drain**: the transition lands at epoch 195–197 at every flood rate tested, because the budget schedule governs what an epoch may spend. Only a *hashrate* whale accelerates it (§2.2, collapsing the phase to epoch 23). The redesign therefore separates two attacks the current design conflates: many small identities dilute the on-ramp but cannot shorten it, while one large actor can shorten it but is visible in a way many small ones are not.

## 5. What follows

**For the redesign.** Two of its three novel surfaces are closed by measurement rather than by argument — the pump and the cliff both lose money, and both are gated. The whale exposure is real, accepted, and now known to concentrate in the first quarter of the phase; if the Q8 cap is ever revisited, a bound that applies only to the early epochs would buy most of the protection at the least cost to R5, since the honest spike that needed 86–111× its budget arrived at epoch 30.

**For the current design.** Its immunity to reward manipulation is structural and worth keeping in mind as the redesign's opportunity cost. Its flow cap makes it undrainable. Neither property helps against the denial attack.

**For both.** The sybil flood is the mechanism's real adversarial exposure, it is cheap relative to what it denies, and neither design addresses it — because neither has a notion of identity beyond a keypair and a claim fee. Anything that would help (a bond to mine, proof of personhood, a per-identity rate limit) is outside both designs as specified, and outside the eight principles the redesign was built from. It belongs on the record as the open problem it is rather than as a defect of either mechanism.

## 6. Reproducing this

```
cd tools/simulators/empowering-denovo
make validate                     # the adversarial findings are gated
PYTHONPATH="src:../empowering/src" python3 -m empowering_denovo_sim.adversary
```

The pump, the cliff and the two-population engine are in `adversary.py`; the whale timing sweep uses `scenarios.whale_run`; the current-design runs drive `empowering_sim.elevation` with no modifications.
