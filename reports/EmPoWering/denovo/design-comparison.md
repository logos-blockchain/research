# Two designs for the same job — the current EmPoWering against the de-novo redesign

## What this document is

A side-by-side of the mechanism as currently specified — measured in the strategy report and its simulator on the `EmPoWering-simulator` branch, including its recent §7 arrivals-as-process study — against the de-novo redesign of this branch, measured in `denovo-report.md`. Both simulators share the fee model, the transaction sizes, the device data and the ledger arithmetic, so where the numbers differ it is the mechanisms differing, not the instruments.

The one-sentence version: **the current design rations a fixed flow and therefore has a best adoption speed, a closing door and a point of no return; the redesign spends a budget wherever the crowd actually shows up, has none of those three, and pays for it with a first-come exposure the rationing never had.**

## 0. In plain words, for anyone

**What the mechanism is for.** Somebody who owns no tokens should be able to join the network by doing useful computation, be paid for it, and eventually save enough to put down the deposit that lets them run a paid service. That path — work, save, join — is the whole point. Both designs are attempts at it, and they differ in how the money for it is handed out.

**How the current design hands it out.** The protocol pays a fixed number of prizes per block, forever, and adjusts the puzzle's difficulty so that number never changes no matter how many people are competing. The prize itself starts small and shrinks steadily. So the pot is a slow, unchanging dribble, shared among however many people turn up.

That has an awkward consequence. **If a lot of people arrive at once, nobody gets turned away — but everybody's share gets thinner**, and the newcomers take proportionally longer to save up. The simulations show what that means in practice: there is a *best speed* for people to arrive (too few and the money goes unused, too many and nobody saves enough), and there is a point after which the queue of people waiting is bigger than every deposit the remaining money could ever fund. Past that point, arriving is pointless — and the date it happens can be worked out in advance from the size of the pot alone.

**How the redesign hands it out.** Instead of a dribble, it sets a **budget**: "we intend to bring in this many people, over this many years, using this much money." Divide the money by the years and you get what each period may spend. Pay whoever shows up out of that period's budget — and if an unexpected crowd arrives, **keep paying them out of the money set aside for later periods** rather than making everyone wait.

That removes all three problems above. There is no best speed, no closing door, and no point of no return, because the money follows the people rather than the people competing over a fixed trickle. The simulations bear it out: whether newcomers arrive steadily, or a hundred times over in a single week, or all at the end, roughly the same number get in.

**What it costs.** Money that follows the people can be followed by the wrong people. One very large operator arriving early can take a great deal of the fund quickly, because the mechanism has no way to say "you have had enough" — the current design's slow dribble prevents that by accident, simply by never handing out much at once. This was a deliberate choice rather than an oversight: the same rule that lets a genuine crowd in is the rule that lets a big player take a lot.

**The catch that affects both, and it is the important one.** Both designs quote their headline numbers assuming that once somebody has saved enough and joined, they *stop* competing for the prizes and leave the rest for newcomers. Nothing pays anyone to do that, and joining does not switch their computer off — so the realistic expectation is that they carry on. When everyone carries on, **both designs bring in roughly a third of the people their headline numbers promise.** That is not an attack; it is what ordinary self-interest produces, and it means the headline numbers of both designs are best read as the optimistic end of a range.

**What actually has to be decided.** Whether the network wants a mechanism that treats everyone who turns up the same regardless of when they come (the redesign) or one that cannot be drained quickly by any single participant (the current design). The simulations can say what each one does; they cannot say which of those two properties matters more, and that is the decision in front of you. Either way, the numbers should be re-struck on the assumption that joiners keep mining, because that is what they will do.

## 1. What each design fixes, and what it lets move

| | current | de novo |
| --- | --- | --- |
| fixed by the protocol | the claim count (10/block, held by the difficulty against a measured 380× load change) and the pool's outflow rate (`distribution_rate = 1/200`) | the budget schedule (`endowment / epochs_left`) and the reward's floor (the anchor) |
| left to demand | who gets the fixed flow | how fast the budget converts, and when the phase ends |
| parameters someone must defend | `distribution_rate`, `target_claims_per_block`, pool % | pool %, `expected_nodes`, `expected_years` — with the consistency identity checked before anything runs |
| the pool's end | never — geometric decay, 4.866% left after 12.3 years, exact to four figures across all arrival rates | epoch 195 exactly on the reference triple; earlier under spikes, later at the nominal-rate tail under weak interest |

The current design's two rate constants are the ones its own report could only defend by simulation. The redesign's three are statements of intent, and the identity `implied_efficiency = nodes × min_stake / endowment` prices a triple against the measured 11.4–51.9% conversion band at parameterisation time — a check the rate form cannot even express.

## 2. Arrivals: the strongest measured contrast

The strategy report's §7 replaces constant arrivals with a Poisson process and measures the consequences of rationing. Set those against the de-novo matrix directly:

| question | current (§7 of the strategy report) | de novo |
| --- | --- | --- |
| does adoption speed matter? | **a hump**: 951 elevated at 2/epoch, ~6,100 near 100/epoch, 5,001 at 500 — the worst rate elevates a sixth of the best | **no**: 24,723 / 26,031 / 25,537 bonds under uniform, ×10 and ×100 arrivals — the outcome moves by 5% while the schedule absorbs the difference |
| is there a closing door? | **yes**: the last cohort with even odds of bonding arrives at epoch 270 (10/epoch), 83 (50/epoch), 34 (100/epoch), 6 (250/epoch) | **no**: the ×100 cohort — 13,000 nodes in one epoch — bonds 100%, median 39 epochs, and the phase still ends on schedule — the amortisation re-spreads the borrow rather than moving its own deadline |
| a point of no return? | **yes, computable from the pool alone**: the waiting queue passes every bond the endowment can still fund at epoch 212 (100/epoch), 119 (250), 72 (500) | **none exists**: the queue cannot outgrow the budget because the budget is spent on whoever is present; under total silence the Q7 tail holds the offer at the nominal rate until claimed |
| does timing matter on a fixed population? | **1.64× between best and worst**; the early burst *loses* to flat and the late ramp loses 38% — the mechanism rewards arriving at a rate it can meter | **within noise inside the window** (all shapes 24.7k–28.6k); late arrival costs time, not conversion — back-loaded converts 76–100% on the tail |
| does the mechanism ever keep up? | at ≥ 25/epoch it is behind from the first epoch and never once catches up | keeping up is not the frame: saturation is routine, bounded, and repaid by the schedule |

This is the R5 requirement seen from both sides. The current controller holds the claim count flat, so a cohort's arrival only thins every share — §7's window, hump and no-return point are the three faces of that one fact. The redesign inverts it: the claim count is a consequence, the budget borrows forward, and a spike costs the schedule rather than the cohort.

Where the two agree is as instructive: the current §7's *retirement* column reaches 100% absorption up to 25/epoch and peaks at 28,023 elevated — and the de-novo reference triple presumes exactly that behaviour (implied efficiency 50%, at the retiring edge of the band). **Neither design pays for that behaviour**, which the adversarial analysis prices at a third to two thirds of onboarding; both sets of headline figures should be read against the persistent edge instead. **The current design achieves at its single best amplitude, with retirement, roughly what the redesign achieves at every arrival shape tried.** The redesign does not create conversion the old mechanism lacked; it removes the requirement that adoption arrive at the one speed the rationing can meter.

## 3. The reward: emergent against defined

| | current | de novo |
| --- | --- | --- |
| opening reward | 1.157 LGO, decaying geometrically (half-life 138 epochs) | 11.87 LGO — ten times higher, because a four-year linear spend outpaces a 1/200 geometric one — demand-indexed downward from there |
| steady state | emergent: the refill spread over a fixed claim count, ≈ 3× the anchor at reference traffic | defined: the anchor exactly — a transfer plus an inscription, tracking the fee market by construction |
| claims to a bond at open | ≈ 865 | 85 |
| self-funding claim | preserved | preserved (Q5) |
| fee drag at steady state | ≈ 20% of the reward | 59.7% — the post-phase pays its stated bundle and little more, by design |

The current steady reward happens to cover a useful bundle with margin; the redesign's *is* the bundle. Which is preferable is R8's intent question, not a simulation's.

## 4. What each design concedes

**The current design cannot be drained and cannot be rushed** — the controller fixes the outflow against any actor, whale included; a large miner captures a share of a fixed flow, never more flow. The price is everything in §2: doors, humps, queues.

**The redesign cannot turn anyone away and therefore can be drained.** The measured whale takes 17% / 52% / 83% of the endowment at 1× / 3× / 10× the field it meets, inside the index's one-epoch lag — accepted as documented, gated properties under Q8/Q9's R6-literal reading: the endowment is first-come. The rationing the old design uses as an accidental whale defence is exactly the behaviour R5 rejects, so this trade is not an oversight in either direction; it is the design choice, made explicitly.

Both designs are attacked concretely in `adversarial-analysis.md`. It finds the redesign's two novel surfaces closed by measurement (withholding and cliff-harvesting both lose money), the redesign markedly *more* sybil-resistant at moderate flooding (3.5% of honest bonds denied against 48.4%, at a doubled field), and — the finding that bears on both — that the retiring behaviour both designs' headline numbers assume is not incentivised, costing a third to two thirds of onboarding when it fails. Two exposures are shared and unchanged by the redesign, and honesty requires saying so. The service stream's flat split dilutes with success in both worlds — the strategy report measures 6,185 LGO per provider per epoch at two hundred providers and 166 at seven and a half thousand, and nothing in the redesign touches that arithmetic. And both mechanisms pay claims in proportion to hashrate within an epoch, so neither has any per-identity defence beyond the claim fee — accepted deliberately, since proof of work is sheer power and any remedy would make it something else.

## 5. What the comparison cannot settle

The conversion-efficiency band the redesign's identity check leans on was measured under the *current* reward dynamics; re-measuring it under the demand-indexed reward is the natural next study, and the de-novo report lists it as its first limitation. The current design's §7 numbers come from Poisson arrivals over a 600-epoch horizon; the de-novo matrix uses shaped arrivals over 220–420 epochs with equal totals — the qualitative contrasts of §2 are far outside either study's seed noise (the current report bounds its own at ~13%, the de-novo pins its headline counts exactly), but individual counts should not be read to the last digit across the two. And neither simulator models the leadership lottery or the emission side differently: everything downstream of the block reward is common ground.

## 6. The verdict, requirement by requirement

| requirement (the de-novo brief) | current design | de novo |
| --- | --- | --- |
| R1 minimal parameters | two rate constants defensible only by simulation | three intent parameters plus an upfront feasibility check |
| R4 pool / nodes / years as the definition | inexpressible — nodes and years are outcomes discovered afterwards | the definition |
| R5 spikes absorbed | the door closes at epoch 34 at 100 arrivals/epoch | the ×100 cohort bonds 100%, median 39 epochs |
| R6 saturation semantics | exhaustion excluded by construction, margin ~2,000 vs 1,024 | saturation routine, bounded, measured at 86–111× budget for the ×100 spike |
| R7 fee-funded, even post-phase | no post-phase concept; the pool never ends | budget = last epoch's fees; saturation in the epoch's last half-percent |
| R8 reward = transfer + inscription | emergent, ≈ 3× the target bundle | the anchor, by definition |
| whale resistance | inherent, via the rationing R5 rejects | conceded and documented (Q8), bounded per-epoch by block space × reward |

On its own brief the redesign wins every row except the last, and the last is the one it conceded deliberately. On the old design's implicit brief — hold the outflow invariant against everything — the current mechanism remains the correct answer. The two briefs cannot both be wanted at once, which is what made the de-novo exercise worth running.
