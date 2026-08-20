# Attacking both designs — an adversarial analysis by simulation

## What this document is

Concrete attacks, run in the simulators, against both the currently specified EmPoWering mechanism and the de-novo redesign. Every number comes from a run with a hostile actor in it, measured against the honest baseline of the same configuration — not from reasoning about what an attacker might achieve. The de-novo attacks use `empowering_denovo_sim.adversary`, which reuses the engine's admission rules exactly, so an attack the model resists it resists for the model's reasons rather than a simplification's. The current-design attacks drive `empowering_sim.elevation` unmodified.

Costs are priced from the standalone estimator at a Raspberry Pi 5's measured Poseidon2 rate, whole-platform, 20 cents a kilowatt-hour.

**The power assumption, stated because it decides the answers.** An attacker is assumed to commit **100% of its hardware to mining** — every core, full duty — on the best class with a *measured* Poseidon2 rate, which is 3.45× a Pi 5 board per unit cost. The honest field is a whole four-core board per node, 24,146 candidates a second, which is also what the strategy study has always used; the *minimal* commitment a participant can make and still be mining is one pinned core, a quarter of that. All three bases are in `power.py`, and results are given across the bracket wherever it changes them.

**What is not bounded.** The classes with measured rates are a Raspberry Pi 5 and an Apple M-series part. A GPU rig is the true adversarial ceiling and its Poseidon2 rate has never been benchmarked — the estimator carries the profile and refuses to invent the rate. **Every adversarial figure here is therefore a lower bound on a well-equipped attacker**, and the gap is unmeasured rather than argued to be small.

**The most important finding is not an attack at all.** Both designs' onboarding targets assume that miners stop mining once they have bonded, and that assumption is not incentivised — continuing to mine is individually rational, and bonding does not stop the hardware. The behaviour both designs need in order to hit their numbers is the behaviour neither pays for. Everything else below is secondary to that.

*Revision notes.* (1) A first version compared the two designs' sybil-flood resistance at different honest baselines and over different windows and concluded they were comparably vulnerable; normalised, they are not, and §4 carries the corrected measurement. (2) Every figure here was recomputed after the power basis was corrected from one Raspberry Pi 5 core to a whole four-core board — the basis the strategy study had always used. That moved the pump, whale and cliff tables materially, and the numbers below are the post-correction ones. Where a figure differs from an earlier draft, the earlier draft was measuring a field four times weaker than a committed miner actually fields.

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
| 10% | 1,228,962 LGO | 544,998 LGO | **0.44×** |
| 25% | 3,066,177 | 1,642,410 | **0.54×** |
| 50% | 6,133,475 | 4,884,645 | **0.80×** |
| 75% | 9,188,985 | 13,579,211 | 1.48× |
| 90% | 11,025,370 | 30,863,255 | **2.80×** |

**Withholding loses money for any minority**, and the result is robust twice over. Across field *sizes* — 0.51×, 0.64× and 0.35× at a quarter of the field, over fields of 100, 1,000 and 10,000 boards. And across the power *bracket*, where it gets stronger the better equipped the attacker is: 0.64× at the minimal basis, 0.50× at the board, **0.28× at the worst measured**. A stronger attacker forfeits more by sitting out, so the defence tightens exactly where it needs to.

The defence is the reward's own cap. `epoch_reward = max(anchor, budget // max(claims_prev, blocks_per_epoch))` floors the divisor at the block count, so however far a minority shrinks `claims_prev`, the reward cannot rise past one block's budget share — measured, it oscillates 8.76 / 4.40 / 8.77 / 4.36 LGO, a factor of two, against forfeiting an entire epoch's claims.

That cap was written for a different problem: at genesis `claims_prev` is zero and something must stop one claim taking the whole sub-pool. It is the manipulation defence as well, which is the happiest accident in the design — and it is now gated, so it cannot be removed as dead weight.

Past half the field the pump does pay, and it pays *well* — 1.48× at three quarters of the field and **2.80× at nine tenths**, which is worse than an earlier revision of this document reported. That is not a new exposure, since an actor holding three quarters of the hashrate *is* the whale of §3.3 and Q8 accepts that case explicitly, but it is worth stating at its true size: **a supermajority miner does not merely capture the endowment, it can nearly triple what honest mining would have paid it** by withholding. Below half the field the defence is intact and the numbers above are the measurement of it.

### 3.2 The manufactured cliff — harvest the period-2 cycle. **Unprofitable.**

Q9 accepts a documented hazard: a sharp participation threshold at the operating reward drives a period-2 cycle. The attack is to *be* that threshold — mine only above a bar, harvesting the high epochs:

| attacker's entry threshold | against always-on | near-zero epochs in a 16-epoch window |
| --- | --- | --- |
| 0.5 LGO — below the operating reward | 0.86× | 1 |
| 1.0 LGO — at it | 0.59× | **8** |
| 2.0 LGO — above it | 0.31× | **8** |
| 4.5 LGO — far above | 0.02× | **8** |

**Being picky costs more than it harvests, at every threshold**, for the same reason the pump fails: skipped epochs forfeit more than elevated rewards return. But the *cycle itself is real and easy to trigger* — any threshold at or above the operating reward produces the period-2 alternation, eight near-zero epochs out of sixteen. It needs a growing field to appear; against a static one the index is stable and no threshold induces it. So Q9's cycle is a user-experience hazard — a badly-chosen wallet default could make a *population* oscillate to everyone's detriment — but not an exploit anyone profits from.

### 3.3 The whale — conceded in the base design, and addressed in **de novo\*** (§3.4)

Q8 keeps the borrow-forward unbounded, so a large actor can draw the endowment through the demand index's one-epoch lag. When it should arrive:

Against a realistically-spread field (Pareto, floored at a whole board):

| whale arrives at epoch | endowment captured (10× the field it meets) | phase ends |
| --- | --- | --- |
| 2 | 21% | 196 |
| **20** | **55%** | 197 |
| 50 | 44% | 196 |
| 100 | 5% | 196 |
| 150 | 19% | 153 |

And against a *homogeneous* field of identical boards — no distributional assumption, which is the bounded worst case rather than the expected one:

| the field's power basis | endowment captured | phase ends |
| --- | --- | --- |
| minimal (one core) | 37% | 197 |
| board (four cores) | **89%** | 23 |
| worst measured (3.45× a board) | 88% | 24 |

**The two fields answer different questions and the difference is instructive.** Against a Pareto field the whale takes 55% at its best moment, because a heavy-tailed honest population contains fast miners that compete with it. Against a homogeneous field of identical boards it takes 89% and collapses the phase from 195 epochs to 23, because nobody present can keep up. The realistic figure is the former; the latter is the bound. Both are reported because a design should be sized against the bound and expected to experience the mean.

**And the exposure saturates**: once the attacker has board-class hardware, more does not help it, because block space rather than search power is what limits an epoch's extraction. That is a genuine bound — the unmeasured GPU gap above does not widen this particular attack, though it widens the others.

**The danger window is early but not immediate.** At genesis the whale takes only 20%, because `claims_prev = 0` caps the reward at one block's share. By epoch 20 the honest field has established a `claims_prev` large enough to price the epoch generously while the endowment is still 90% intact — 88% capture, and the bootstrap collapses from 195 epochs to 23. By epoch 100 the endowment is half spent and the exposure falls back.

This sharpens the accepted risk rather than changing it — and §3.4 now addresses it, because the obvious mitigation turned out not to be the workable one.

### 3.4 **de novo\*** — bounding the draw, and what it costs

The whale is the base design's one accepted weakness, so it is worth asking what closing it takes. The answer is one parameter and a deferral, and the route to it is not the obvious one.

**The obvious cap does not work.** Bound the borrow itself — no epoch may spend more than `m` budgets. One budget is about `1/195` of the endowment, and the honest ×100 cohort borrows about **97** of them, so a cap loose enough to admit the very cohort R5 exists to protect already permits half the endowment to leave in one epoch. Honest crowd and hostile whale are the same shape to the mechanism, and a flat cap cannot tell them apart. *(An earlier draft of this document recommended `m ≈ 3` on the strength of a mis-measured 2.6× figure for that cohort; at the true ~97 that cap would have rationed it savagely. The recommendation is withdrawn.)*

**What works is bounding the endowment draw as a fraction of what remains**, and only the part *beyond* the epoch's own scheduled sub-pool:

| `drawable = sub_pool + draw_cap_fraction × endowment_at_epoch_start` |
| --- |

The point is not the ceiling but what it converts. Past the cap the epoch stops admitting — but the claimants have not left, and they claim again next epoch, by which time `claims_prev` has exploded and the reward has fallen. **The cap turns instant extraction into metered extraction, which is exactly the interval the demand index needs to reprice.** Bounding the *whole* draw instead also throttles the ordinary spend-down, and the endowment then never empties — measured, the transition simply stopped firing at every cap tested.

Measured, at a 10% cap:

| | base | de novo\* (10%) |
| --- | --- | --- |
| whale capture, 10× at epoch 20 | **55%** | **9%** |
| whale capture, 3× / 30× / 100× at epoch 20 | 33% / 56% / 56% | 9% / 9% / 9% |
| ×100 honest cohort bonded, retiring | 100% | 100% |
| its median time to bond, retiring | 43 epochs | **59 epochs** |
| ×100 cohort bonded, persistent | 24% | 24% |
| its median time to bond, persistent | 69 epochs | **69 epochs — unchanged** |
| uniform onboarding | 24,707 | 24,782 |
| phase ends | 196 | 197 |

Across the cap sweep the whale falls 55% → 18% → 9% → 5% → 2% at caps of 20%, 10%, 5% and 2%, while onboarding drifts *up* slightly and the phase length does not move. **The variant converts a size-dependent exposure into a flat ceiling**: under the base design a whale's take rises with its hashrate, and under the cap a 3× and a 100× whale take the same 9%, because what binds is the cap and the repricing rather than the attacker's power.

**What it costs, honestly.** One parameter, against R1 — and it is a parameter with no natural value, since 20%/10%/5%/2% are all defensible. It softens R6's letter: the pool no longer pays purely until exhausted *within an epoch*, though nothing is refused permanently and no money is destroyed. And in the *retiring* regime it defers the very cohorts R5 protects by about 40% in time-to-bond, 43 epochs to 59. **Under persistence — the regime incentives actually produce — it costs nothing at all**: 24% bonded at a median 69 epochs with the cap and without it. The deferral is a cost the variant only incurs where the mechanism was already converting quickly.

**What it does not cost** is the thing worth noting: not onboarding, not the phase length, and not R5's guarantee. This is the cheapest of the mitigations considered anywhere in this analysis, and the only one that closes an accepted exposure without opening another.

Q8 was settled as unbounded, so this is recorded as an **alternative design** rather than a correction — the decision is the design owner's, and §6 states it as such.

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

One asymmetry favours the redesign throughout. **An arrival flood cannot accelerate its drain**: the transition holds at epoch 195–197 at every flood rate tested, because the budget schedule governs what an epoch may spend. Nor can an arrival spike: measured across seeds, uniform and ×100 both end at 195–196. Only a *hashrate* whale shortens the phase (§3.3), and only because it drains the endowment outright rather than merely claiming from it. The redesign therefore separates two attacks the current design conflates — many small identities dilute the on-ramp but cannot shorten it, while one large actor can shorten it but is visible in a way many small ones are not.

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

**For the redesign.** Both of its novel surfaces are closed by measurement rather than argument, and gated. The whale exposure is real, accepted, concentrated in the first quarter of the phase — **and now shown to be closable**: §3.4's `de novo*` bounds it from 55% to 9%, flat across whale size, for one parameter and a 40% deferral of spike cohorts' time-to-bond, with no cost to onboarding, phase length or R5. Whether to buy that is a decision rather than a finding, and it is the one open item this analysis leaves. Its sybil resistance at moderate flooding is markedly better than the current design's, which is a point in its favour that the first version of this analysis missed.

**For the current design.** Its immunity to reward manipulation is structural — a pool-determined reward cannot be pumped — and worth counting as the redesign's opportunity cost. Its flow cap makes it undrainable by any actor.

**For the protocol — decided, not open.** The sybil flood is cheap relative to what it denies and neither design addresses it, because neither has a notion of identity beyond a keypair and a claim fee. The design owner's position, taken 2026-08-20, is that **this is accepted and not to be mitigated: proof of work is sheer power, and a participant who buys more of it is entitled to more of the reward, whether they present as one identity or a thousand.** Every candidate remedy — a bond to mine, proof of personhood, a per-identity rate limit — would make the mechanism something other than proof of work, so none is pursued.

That makes the flood a property to size rather than a hole to plug, and the sizing is in §4: a quarter-million devices and $20M of hardware before electricity, which is the same barrier that stands in front of any attack on any proof-of-work chain. It is worth noting only that the *denial* is cheaper than the *capture* — an attacker who merely wants to keep others out spends the same and needs no strategy at all.

## 7. Reproducing this

```
cd tools/simulators/empowering-denovo
make validate                     # the adversarial findings are gated
PYTHONPATH="src:../empowering/src" python3 -m empowering_denovo_sim.adversary
```

The pump, the cliff and the two-population engine are in `adversary.py`; the retirement-denial run uses `engine.run(..., refuse_fraction=)`; the whale timing sweep uses `scenarios.whale_run`; the current-design runs drive `empowering_sim.elevation` with no modifications.
