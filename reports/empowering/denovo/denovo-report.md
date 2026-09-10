# EmPoWering from base principles — the model, and what the simulations say about it

## The problem, in one paragraph

A new blockchain has a chicken-and-egg problem. To earn from it you generally need to own some of its tokens first — but a newcomer owns nothing. **EmPoWering is the on-ramp that solves this**: you do computational work (mining), you get paid in tokens, you save until you have enough to put down a deposit, and that deposit lets you run a paid service on the network. Work, save, join. This document redesigns how the money for that on-ramp is handed out, and reports what happened when we simulated it.

## What this document is

A redesign of the EmPoWering mechanism from eight stated principles, simulated, and validated against those principles by number. It is not an amendment to the current specification: the design was derived from the principles first and mapped back onto the existing machinery afterwards (`MAPPING.md`), so that every part of the old mechanism had to re-justify itself or go. The model is specified normatively in `MODEL.md`; this report explains it, shows what the simulations measured, and puts the open decisions where they can be seen.

### How to read this

Each section opens with a short *plain-words* paragraph explaining what it is about and why it matters, before any arithmetic. You can read only those and get the whole argument.

| if you want… | read |
| --- | --- |
| the decision and the recommendation | `SUMMARY.md`, next door |
| the choice between designs, no arithmetic at all | `design-comparison.md` §0 |
| how the redesign works and whether it does what was asked | **this document**, §§2–7 |
| what happens when someone attacks it | `adversarial-analysis.md` |
| the exact rules, for implementing | `MODEL.md` |

**The shape of what follows.** §1 lists what the design was asked to do. §2 explains how it works. §§3–6 are the simulations, in order of how hard they push: an ordinary run, then a sudden crowd, then the awkward edges, then what happens after the money runs out. §7 gives the two things that went wrong, §§8–9 the open questions and the roads not taken, and §§10–11 the scorecard and the honest limits.

### The words you need

Everything else is explained where it appears; these six recur throughout.

| term | what it means |
| --- | --- |
| **epoch** | the network's accounting period — about five and a half days here. Budgets are set and rewards fixed once per epoch |
| **claim** | one successful piece of mining work, submitted to be paid. The unit of "getting paid" throughout |
| **the bond** (`min_stake`) | the deposit — 1,000 tokens — that lets a node run a paid service. The finish line of the on-ramp |
| **the endowment** | the pot of tokens set aside at launch to pay for all this. It only ever goes down |
| **the fee bucket** | a second, smaller pot, refilled from a slice of everyone's transaction fees |
| **TGE** | "token generation event" — the network's launch, when the initial tokens are created |

Notation follows the house convention: prose and code spans carry self-describing names, so `epoch_budget` here is the same quantity as `epoch_budget` in the model document and the simulator.

Regenerate every figure with (from `tools/simulators/empowering/denovo`):

```
PYTHONPATH="src:../empowering/src" python3 -m empowering_denovo_sim.plots \
    --out ../../../reports/empowering/denovo/figures
PYTHONPATH="src:../empowering/src" python3 -m empowering_denovo_sim.validate
```

## 1. The requirements

*In plain words: this is the brief. Someone said what the mechanism must do, in eight numbered points, before any design existed. Everything later in this document is checked back against these — §10 is the scorecard. The point of writing them down first is that the design cannot quietly change what it was trying to achieve.*

Stated by the design owner on 2026-08-18, and used as the report's checklist:

| # | requirement |
| --- | --- |
| R1 | as few parameters as possible; the design as simple as possible |
| R2 | two regimes — bootstrapping and post-bootstrapping — with distinct purposes |
| R3 | the bootstrap exists to onboard nodes into PoS: PoW mining → `min_stake` → service provision |
| R4 | the bootstrap is defined by three parameters: the pool (% of TGE), the expected nodes, the expected duration |
| R5 | spikes of interest are absorbed, not pushed away; arrivals are not assumed uniform |
| R6 | rewards are paid until the pool is exhausted — no money is created; fee refill accounted per epoch; the reward is fixed for each epoch; a saturated sub-pool keeps paying from further pool funds (the saturation point) |
| R7 | post-bootstrap: (a) rewards come from the previous epoch's fees; (b) claims spread evenly, with the saturation point near the epoch end |
| R8 | one reward pays for a transfer plus an inscription (transfer ≈ inscription); larger during bootstrap, subsidised from TGE |

## 2. How the mechanism works

*In plain words: the whole design is "decide a budget, then spend it on whoever shows up".*

*Picture a fund set aside at launch to bring newcomers in, and a plan to spend it over four years. Divide the money by the time and you get what each period may spend. Then pay whoever turns up out of that period's share — and if an unexpected crowd arrives, keep paying them out of money earmarked for later periods rather than making anyone wait. The price paid per piece of work adjusts automatically: busier periods pay less per person, quiet ones more, because the budget is what's fixed, not the price.*

*That is the entire idea. The rest of this section is the bookkeeping that makes it precise — two pots of money, two numbers fixed at the start of each period, and three rules for the awkward moments (a crowd arriving, the money running low, and the last few coins).*

The mechanism keeps two buckets of tokens. The **endowment** is the TGE allocation — it only ever goes down. The **fee bucket** holds the diverted share of transaction fees, accounted with a one-epoch delay. Which regime the chain is in is not a stored flag; it is a question about the endowment: while it holds anything, the chain is bootstrapping.

Each epoch opens by fixing two numbers. The **budget** is what this epoch intends to spend: during bootstrap, an equal share of the remaining endowment — `endowment / epochs_left` inside the expected window, capped at the nominal per-epoch rate in the Q7 tail beyond it — plus whatever fees arrived last epoch; afterwards, the fees alone. The **reward** is what one claim pays, fixed for the whole epoch so a wallet can build a self-funding claim before submitting. During bootstrap it is demand-indexed — the budget divided by how many claims came last epoch — and afterwards it is the **anchor**: the cost of a transfer plus an inscription, read off the fee markets, `anchor = 2 * tx_fee(transfer)` under the stated transfer ≈ inscription assumption. The bootstrap reward is floored at the anchor and capped at one block's budget share, so a quiet epoch cannot hand the whole sub-pool to a single claim.

| `epoch_budget = endowment // (bootstrap_epochs - e) + fee_bucket` — while `e < bootstrap_epochs` |
| --- |
| `epoch_budget = min(endowment, endowment_genesis // bootstrap_epochs) + fee_bucket` — the Q7 tail, past the deadline |
| `epoch_reward = max(anchor, epoch_budget // max(claims_prev, blocks_per_epoch))` — bootstrap |
| `epoch_reward = anchor` — post-bootstrap |

Claims are then paid at that reward until the money runs out. During bootstrap "the money" is the whole pool, not the budget: if a large cohort arrives and the epoch's budget is spent mid-epoch — the **saturation point** — payment continues, drawing the undivided endowment forward. The spike thins every later sub-pool through the schedule's recomputation, which is precisely what keeps the phase's end where it was. That is the R5 mechanism in one sentence: a cohort costs the schedule, never the cohort. Post-bootstrap there is nothing to borrow from, and stopping at the budget is the point.

The difficulty splits by regime. During bootstrap it is a constant floor — spam protection, nothing more, because admission control is economic and a cohort must not be met with a rising work price. After the transition the existing EMA retarget (an exponentially-weighted moving average — a smoothed running average that discounts older observations) wakes with a derived target, `capacity / blocks_per_epoch` where `capacity = epoch_budget // epoch_reward`, and its job is R7b: spread the claims so the saturation point lands at the epoch's end.

The transition needs no parameter and no governance. The endowment is monotone, so `endowment == 0` fires once and never reverses. One subtlety earned its place in the model the hard way: payments draw the fee bucket first, so the endowment's last remainder is always smaller than one reward, and without a rule it would hold the regime open forever. The **dust fold** closes it — an endowment that cannot fund one claim at the epoch's own price folds into the fee bucket and the epoch runs as post-bootstrap. The simulator found both halves of this: the deadlock on its first full run, and, in the back-loaded scenario, that the threshold must be the epoch's reward rather than the anchor.

### 2.1 What became of the old parameters (R1)

*In plain words: the old design had knobs nobody could set without a simulation. This is the tally of which survived, which were deleted, and which are new — and the point is that the two we deleted were the two nobody could justify, while the two we added are the two anyone can argue about in a sentence.*

| current design | here |
| --- | --- |
| `genesis_pool_fraction` | kept — the triple's pool term |
| `distribution_rate` (1/200) | **deleted** — the budget replaces the rate; the phase has an end |
| `target_claims_per_block` (10) | **deleted** as a constant — the claim count is a consequence, `capacity`, and only the post-phase throttle target is derived from it |
| smoothing `F/P`, genesis difficulty | kept — the retarget implementation is unchanged; the genesis value becomes the bootstrap floor |
| `pow_share` (10%) | kept — the one fee parameter |
| — | `expected_nodes`, `expected_years` — the two new parameters, both statements of intent |

The two deleted parameters are exactly the two nobody could defend without running a simulation. The two added ones are the two a designer can argue about in a sentence.

### 2.2 The consistency identity

*In plain words: the three settings you choose are not independent. Say how much money, how many people, and over how long, and you have implicitly claimed a **conversion rate** — how much of every token paid out actually ends up as somebody crossing the finish line, rather than leaking away in fees or going to people who were already across. This section works out that implied rate and checks whether it is achievable. It is the single most useful thing in the design, because it catches an impossible plan before anyone runs anything.*

The three R4 parameters carry an internal check, and the model applies it before anything runs:

| `implied_efficiency = expected_nodes * min_stake / endowment` |
| --- |

Every onboarded node costs one bond, so a triple silently asserts that this fraction of what the pool pays out actually reaches bonds. The prior branch's elevation study measured a band of **11.4%** to **51.9%** for *its* mechanism; this one has been re-measured in the redesign and is not one band but two regimes (§4.2): **15% when nobody retires, flat in the arrival rate**, and **25–74% when they do, rising with it**. The simulator checks a triple against both and reports which regime it needs. The reference triple used throughout — pool 0.5% of TGE, 25,000 nodes, 4 years — implies exactly 50%: comfortably satisfiable if miners retire, and **more than three times what persistence delivers** if they do not. That is a bet on behaviour, and §8 recommends re-striking it.

**Retirement is a regime, not a caveat, and every figure below is given in both.** The band's upper edge describes bonded miners retiring, and nothing pays them to: a bonded node can provide service *and* keep mining, and the marginal claim is profitable at any plausible token price (`adversarial-analysis.md` §2). Measuring this mechanism's own conversion — rather than importing the prior branch's — shows the two regimes are not one quantity at two values but two different shapes:

| arrivals an epoch | 65 | 130 | 260 |
| --- | --- | --- | --- |
| **persistent** (nobody retires) | 13.9% | 15.9% | 14.6% |
| **retiring** | 24.9% | 49.4% | 74.1% |

Under persistence the efficiency is **flat**: everyone keeps mining, so the field grows with the arrival rate and dilution cancels the gain. Under retirement it **rises with the rate**, because each departure frees claim share for the next cohort. So a triple's feasibility is a property of the triple alone in one regime and depends on adoption speed in the other.

**Which regime obtains is now measured, not assumed** (`adversarial-analysis.md` §2.3). Letting each bonded miner re-decide every epoch — weighing its income, its electricity, and the dividend it earns by suppressing the on-ramp — produces **100% persistence through every epoch of the scheduled bootstrap and 100% retirement the epoch it ends**, for 7,643 nodes: the persistent column exactly. Both regimes are still reported below, because the retiring column is what the reference triple was struck against and the comparison is the point, but **only one of them is a behaviour anyone would choose.** The token price is what moves it, and dearer is worse: above roughly $0.20 incumbents mine the whole phase, and the retiring figure needs a token worth under a cent.

The consequence for the reference triple is blunt. It implies 50%, which is reachable only if miners retire *and* arrive fast — a bet on two behaviours. The feasibility check now defaults to the persistent reading and reports the optimistic one beside it, so the bet is visible rather than assumed.

## 3. The reference run (R2, R4, R6)

*In plain words: the ordinary case, with nothing unusual happening. Newcomers arrive at a steady rate for four years. This is the baseline everything later is compared against — does the money last exactly as long as planned, does every token get accounted for, and how many people actually get in?*

![one run, two regimes](figures/two_regimes.png)

Uniform arrivals, 130 miners an epoch, bonded miners retiring. The endowment spends on its linear schedule and hits zero at epoch **195 exactly** — the expected duration of the four-year triple, `195 = round(4.0 * 48.667)`. The regime flips once and never back. Every lepton is accounted: endowment in, fees in, payments out, buckets held — the conservation gate closes to zero. During bootstrap the fee bucket never clears 0.02% of the endowment, which settles empirically what the model asserted: fees are a rounding error during bootstrap, and the endowment is what onboarding spends.

The reward opens at **11.87 LGO** — the opening sub-pool of 256,410 LGO spread over one claim per block, because at genesis there is no previous epoch to index on — and glides down as participation grows, cliffing to the anchor at the transition. At the opening reward a bond costs 85 claims.

The run lands **24,674 bonds against the 25,000 intent** if bonded miners retire — within 1.3% of target, at the very edge of the band it presumes. **If they do not, the same triple delivers 7,643 — under a third.** Both are the same mechanism on the same parameters; the difference is entirely a behaviour nothing in the design pays for.

## 4. The spike, measured (R5)

*In plain words: the stress test, and the reason the redesign exists. A hundred times the normal crowd shows up in a single week — the kind of surge a popular launch or a viral moment produces. The old design would have thinned everyone's share and stretched everyone's wait. The question here is whether the new one absorbs the crowd without punishing them, without punishing the people who came before, and without blowing the schedule. It mostly does — and the one place it did not, block space, is now protected by the §8.3 reservation rule this section describes.*

![the hundredfold cohort](figures/spike_absorption.png)

This requirement is the reason the design exists, so it gets the sharpest test: a cohort of **13,000 nodes — a hundred times the background arrival rate — lands in one epoch**. The epoch saturates at block 481 of 21,600, and the borrow-forward pays **about forty-five times the epoch's budget** — median 45×, ranging 29× to 58× across seven seeds as the heavy tail of the hardware distribution (a Pareto draw — many small machines, a few very large ones, the shape hardware fleets tend to have) falls differently among 13,000 mining rates. A ×10 cohort still borrows about its multiple (median 9.3×, ranging 5.3× to 11.6×), but the ×100 no longer can: **on the three-permutation mining basis the 1,024-transaction block cannot physically pay a hundred budgets inside one epoch, so block space truncates the borrow-forward itself** — the same cap §8.3 is about, doing accidental service. What is borrowed is re-spread by the schedule: **the phase still ends about when it was going to.** Measured across three seeds, uniform ends at 196/196/181 and the ×100 spike at 197/198/196 — a spike delays the end by an epoch or two at most, and none shortens it. The index reprices the next epoch.

**Block space is now protected by rule — §8.3 is resolved (2026-09-05).** The rule gives ordinary transactions priority: claims fill only the space they leave, `max(32, 1,024 − ordinary)` a block — **424 at the reference 600** — with no tuned fraction, because the reservation is whatever ordinary demand actually is. It closes two things at once: the crowding defect, and the model's own inconsistency (its fee flow always assumed 600 ordinary transactions in every block while its old clip let claims take all 1,024 — the mechanism was displacing the very traffic that funds it). Measured on the spec's three-permutation basis: a ×100 spike epoch still *offers* 1,769–1,837 claims a block, and now *pays* **exactly 424 in every draw — the reference traffic rides through untouched** (gated: `the reservation rule holds: claims never displace ordinary traffic`). The price falls on the crunch that causes it: the ×100 borrow-forward truncates at ~19 budgets (median 18.6×, range 11.8–23.9 across seven seeds; ~45× under the raw clip, ~97× on the naive basis), the cohort's bond median stretches to 64 epochs, and the loaded arrival shapes stay space-rationed — front-loaded **5,084 of its 28,600 arrivals**, back-loaded 12–23% across draws — which is now the rule working, not the defect. The room also does something nobody asked of it: **it bounds the well-timed whale at ~9% of the endowment by itself** (adversarial analysis §3.3–3.4), superseding the de novo\* cap's defence at its default setting. The paragraph's superseded readings stay named: 190/240 at one core, 730–759 (83–84%) on the naive miner, a misquoted shared-draw "958", and the pegged 1,024 that forced the rule.

**The acceptance window prices the crunch — and under the reservation rule the price is steep, on exactly the right people.** Every claim is anchored to a recent block and dies if not included within `W = 10` blocks (mantle's grinding defence; since the 2026-09 revision a claim may also straddle one epoch boundary, which is exactly the inclusion semantics this model's persistent queue assumed). Modelled exactly — a FIFO inclusion queue at the *unclipped* demand, served at the claim room — the regime that retires stays free: worst epoch inflation 1.000×, expiry 0.00%. The crunches pay hard. The ×100 spike epoch loses **76.9% of its solutions** to the window and burns ×4.33 energy per paid claim: 1,837 offered a block queue for 424 of room. The late persistent-regime bootstrap is worse still — epoch 100 expires 77.1% at ×4.38, and epoch 194: 3,483 offered a block, **87.8% of solutions expire**, energy per paid claim ×8.21. Closed through the retirement decision (`window.congested_price_curve`), the tax is now a first-order term with an unexpected sign: wasted energy pushes incumbents out early, so **the taxed persistent field retires sooner and onboards more** — at $1 persistence ends at epoch 160 instead of 195 (bonds 7,643 → 9,617), at $0.10 at epoch 59 instead of 108 (14,181 → 16,844), at $0.05 at 42 instead of 65; only $0.01 is already too cheap to care. The post-phase saturation tail keeps its standing fee (§6). The superseded readings — 0% spike expiry on the naive basis; 44.2%/×1.79 and one moved threshold under the raw clip — are kept in the gates' notes.

![the acceptance window, priced](figures/window_tax.png)

The cohort itself: **100% bonded, median 58 epochs to the bond** — if bonded miners retire, with the five cohorts after the spike also bonding completely. **Under persistence only 22% of it reaches the bond**, at a median 70 epochs, with the neighbours behind it landing at 13–28%, and that distinction is worth being exact about. R5 asks that a cohort not be *pushed away*, and it is not: every one of those 13,000 nodes is admitted and paid, in both regimes, which is precisely what the current design's closed door denies them. But being admitted and reaching the bond are different things, and under the regime the incentives actually deliver, a big cohort competes forever against a field that never shrinks, so most of its members never cross. **R5 holds in both regimes; the onboarding it buys does not.** Under the previous design's controller, which holds the claim count fixed against any load, this cohort would have thinned everyone's share a hundredfold and stretched every time-to-bond with it; here it costs the schedule nothing at all — the phase ends at 196 with the spike and 196 without it.

For contrast, and in both regimes — uniform, ×10 and ×100 arrivals all land in the same place:

| arrival shape | retiring | persistent |
| --- | --- | --- |
| uniform | 24,674 | 7,643 |
| ×10 spike | 25,971 | 7,634 |
| ×100 spike | 37,811 | 7,007 |
| front-loaded | 5,084 | 2,812 |
| back-loaded | 4,935 | 2,751 |

**Timing insensitivity survives only where block space is not contended.** Uniform and spiky arrivals still land together in each regime — R5's claim, for the shapes it was made about — and the ×100 spike now *over*-delivers under retiring (33,882: the pegged cap pays claims flat-out for the whole epoch while retirement keeps freeing share). But the loaded shapes collapse in both regimes: a front- or back-loaded field piles a big cohort onto the floored difficulty for many consecutive epochs, offered demand exceeds what 1,024 transactions a block can pay, and what the cap clips cannot bond. On the naive-miner basis these rows read 28,600 (complete) retiring and ~6,100 persistent; the collapse to ~5,000 and ~2,800 is the §8.3 defect measured from another side, and one more reason the reservation rule must come first.

## 5. The window's edges (R4, and a question)

*In plain words: the two worst-shaped futures. What if everyone turns up immediately, and what if nobody turns up until the very end? These are not attacks — just unlucky timing — and a design that only works when interest is steady is not much of a design. One of these two exposed a genuine flaw, which is fixed here.*

![five arrival shapes](figures/arrival_shapes.png)

The two pathological shapes mark the design's honest edges.

**Front-loaded** — the whole field inside the first tenth of the window — converts **100% of arrivals** (28,600 bonds) using about two thirds of the endowment, and the remaining 36% then sits armed: the transition never fires, because money remains and nobody is left mining. This is correct behaviour under the principles — an endowment that remains is onboarding capacity that remains, available to whoever arrives next — but it means "the bootstrap phase" can outlive its expected duration indefinitely when interest came early and cheap.

**Back-loaded** — the whole field in the window's last tenth — exposed the design's one sharp corner, and settling it is this report's Q7. Under the schedule's naive form, the first epoch past the expected duration with claimants present received the *entire remaining endowment* as its sub-pool: 1,300 first-comers split 50M LGO at a 2,315-LGO reward, the epoch converted at 2.6%, and the 27,300 nodes arriving afterwards met the anchor — **1,293 bonds out of 28,600 arrivals**. The settled rule is the **nominal-rate tail**: past the deadline, each epoch's sub-pool caps at `endowment_genesis // bootstrap_epochs`, the planned per-epoch rate, until the money is gone. Zero new parameters, and late cohorts meet the same regime on-time cohorts did. Measured: the same back-loaded field now converts **76–100% across draws** (21,692–28,600 bonds), and the run ends either with the endowment still armed for later arrivals or spent and transitioned — which of the two is draw-dependent; the legality is not. The expected duration is thereby asymmetric, and deliberately so: **weak interest extends the phase at the planned pace, while a spike does not shorten it** — the borrow-forward pulls later sub-pools forward and the schedule re-spreads what remains, so the deadline holds (§4).

## 6. After the endowment (R7, R8)

*In plain words: what happens when the launch fund runs out. Mining does not stop — it switches to being paid from a slice of ordinary transaction fees, at a much smaller reward pegged to what a transaction actually costs. This section works out what that steady state looks like, and it is deliberately modest: after the fund is spent, mining pays for itself and very little more.*

![the post-phase](figures/post_phase.png)

The post-phase budget is the previous epoch's diverted fees, raw; the reward is the anchor exactly; and the capacity has a closed form worth framing: `capacity = pow_share * txs_per_epoch / (1 + claim_fee/tx_fee)` at the re-struck anchor — still **independent of the fee level**, which cancels between the budget and the anchor, though no longer of the fee *ratio*. At the reference 600 transactions a block that is about 428,400 claims an epoch, roughly twenty a block, and the simulated count tracks it to within the rollover lepton (the old two-transfer anchor's tidier "exactly half the diverted count, 648,000" died with that anchor; both are gated against the engine's realised set).

*Where those diverted fees now come from.* The tokenomic substrate has changed under this design: lips PR 375 (`block-rewards.md` 1.1.0) routes all fees into a **pending rewards pool** instead of burning them, and the `pow_share` diversion is now that pool's first outflow — a carve-out from the pooled reward flow, decided 2026-08-24 and recorded as contradiction 4.13. Nothing in this section's arithmetic moves (the diverted amount is identical; the reward rule reads the pool's inflow net of it), but the provenance does: the post-phase is a distribution *from the pool the whole network's rewards now live in*, and the design as a whole maps onto the RFC's own pattern term for term — the endowment is a genesis-minted sub-reserve, the schedule a metered release, the dust fold its depletion fallback (`MAPPING.md` §1.1). Verified against the revised emission machinery: the settled blend pool is unchanged to the LGO, so every service-income and retirement figure in this report stands.

The throttle wakes at the transition — the same EMA retarget the current specification ships, handed the derived target instead of a constant — and walks the difficulty from the bootstrap floor to the fee-budget equilibrium within two epochs, then tracks the live field with no special-case rule. One rule earned its place here the same way the dust fold did, by the simulator catching its absence: **the retarget updates only while the budget still admits claims.** A block past the saturation point carries no demand signal — admission is closed, not demand absent — and feeding its zero count to the controller eased the target to its 2²⁶ cap across every epoch's tail, so each next epoch opened at everyone-wins difficulty with a 1,024-claim burst before slamming back: a once-per-epoch limit cycle that quietly violated R7b at both epoch edges while every aggregate still looked right. With the rule in place, settled saturation points sit inside the epoch's **last half-percent** (worst observed: block 21,558 of 21,600) and no settled block carries more than about twice the 30-claim target. At sparse traffic — twenty transactions a block, capacity exactly one claim per block — the saturation point can only be approached from below and settles near block 20,530 — 95% of the epoch: the requirement degrades gracefully rather than failing, and the retarget-freeze rule is what lifted this case too (it sat near 16,600 while the tail-easing cycle ran).

One standing cost the throttle's own success creates, now priced: a solution found after the saturation point waits for the next epoch's budget, and the acceptance window (`W = 10` blocks) forgives only the final ten blocks of that wait — everything found between saturation and that grace strip expires and must be re-mined. Measured: **1.05% of a settled post-phase epoch's solutions**, per epoch (`window.post_tail_loss`, gated). It was 0.137% under the old anchor, whose two-transfer strike happened to make the throttle's per-block target an exact 30; the re-struck anchor gives 19.83, the target rounds up to 20 so that saturation stays reliable (MODEL §4.2), and the ~1% offer overshoot is re-mined. Real, modest, and worth knowing it is the price of R7b's predictable admission window at an anchor that no longer divides the epoch evenly.

R8 holds by construction in both regimes — the reward is floored at the anchor during bootstrap and equals it afterwards. The 2026-09 upstream change briefly broke the arithmetic underneath it: the claim gained a ZkSignature and 590 execution gas, its fee (11,298 lepta) overtook the old two-transfer anchor (11,158) by 140 lepta, and R1's self-funding margin vanished exactly where the design leans on it. **Re-struck by the design owner, 2026-09-05: the anchor is now the claim's own fee plus one average transfer — 16,877 lepta at the resting prices.** The surplus is one transaction *by construction*, so no future movement of the claim's fee ratio can reopen the break — which is precisely how the old strike failed, its margin being a coincidence of a ratio that upstream then moved. At the anchor the claim's own fee consumes **66.9%** of the payout (59.7% under the old pair); the post-phase pays for its stated bundle and not much more, which is R8's letter and its intent. Both the definition and its clearance are gated (`the anchor is the claim's own fee plus one transfer`).

## 7. The two findings (MODEL §8, measured)

*In plain words: the two ways this design can be exploited or misbehave, both found by simulation rather than argument. Both come from the same root — the price adjusts based on last week's demand, so there is always a one-week window in which someone can act before the price catches up. One is a large actor draining the fund; the other is an oscillation where everyone mines, then nobody, then everyone. Neither breaks a stated requirement, and both were put to the design owner as explicit choices.*

![the whale, and the cliff](figures/adversarial.png)

Both findings are the same mechanism seen from two sides: **the demand index reprices with a one-epoch lag, and the lag is a window.**

**The whale.** One actor bringing a multiple of the field it meets, at the bootstrap's floored difficulty: at 1× it captures 17% of the endowment, at 3× it captures 50%, at 10× it captures 56%. **It does not shorten the phase** — 196 / 196 / 197 against the uniform run's 196. (An earlier draft published 52% / 83% and a collapse to epoch 33; those were the one-core-basis figures, and the collapse never happened on any basis against a realistically-spread field. A *homogeneous* field of identical boards is the worst case, and there the whale takes 89% and the phase does collapse, to epoch 23 — that bound is reported in `adversarial-analysis.md` §3.3 and is the number to quote for a worst case.) The per-epoch extraction is bounded — block space times the reward is the ceiling on what any epoch can pay — and the index's response is real: the whale takes its haul in its arrival epoch, the next epoch's reward crashes by two orders of magnitude, and its ongoing rate dies. What the index cannot do is act inside the epoch. Everything a burst extracts, it extracts inside the lag.

**The participation cliff.** With participation inelastic near the operating reward, the index is stable — the live field self-regulates to about two cohorts (bonded miners retire; the claim flow equilibrates to the bond flow), and the only excursions are Pareto-tail hardware bursts, which cost everyone one epoch of ninefold-reduced reward and are gone. But a sharp participation threshold sitting exactly at the operating reward produces a hard period-2 cycle: everyone mines, the reward halves below the threshold, no one mines, the reward recovers, everyone mines. Claims alternate 0 / 70,930 / 30 / 80,091 — measured, reproducible.

**The whale is closable, and cheaply — `de novo*`.** Since Q8 was settled the exposure has been addressed by a variant, specified in `MODEL.md` §8.5 and measured in `adversarial-analysis.md` §3.4: bound what the endowment may give up in one epoch to a fraction of what remains, *beyond* the epoch's own scheduled share. At a 10% bound the whale's take falls from 21% to **9%**, and stays flat in the whale's size — a 3× and a 100× actor take the same, because what binds is the cap and the repricing rather than the attacker's power. (On the naive mining basis the base take was 55% and size-dependent; block space now flattens it at 21% before the cap halves it again.) Onboarding does not move (24,745 against 24,674), the phase does not lengthen (196 either way), the ×100 cohort still bonds completely, the result is neutral to the retirement regime, and it does not reintroduce sybil fragility. What it costs depends on the regime, and in the one that matters it costs nothing: under persistence a ×100 cohort bonds at 22% and a median 70 epochs **with or without the cap**. The ~10% longer wait — 58 epochs to 64 — appears only in the retiring regime, where the cap slows a cohort that was converting quickly anyway. So the honest price of `de novo*` is one parameter with no natural value and a softening of R6's letter within an epoch; the deferral it was supposed to cost is a retiring-regime artefact. Everyone still gets in; they get in later. It is carried as an alternative rather than folded into the design, because Q8's decision stands and this is the design owner's to take.

Neither finding breaks a stated requirement, and both were put to the design owner as explicit decisions (Q8, Q9). **The settled position is the literal one: no cap, no damping.** R6 means what it says — the pool pays until exhausted, and a whale is a claimant like any other; the endowment is first-come by design. The index stays raw because its one-epoch crash *is* the burst response, and zero state is worth more than a softer landing. Both exposures therefore ship as documented, gated properties rather than mitigated ones: the capture curve above is the design's answer to "what can one actor take", and the cliff cycle is the design's answer to "what does a participation threshold at the operating reward do". The rejected mitigations are in §9's table with the measurements that priced them.

## 8. Open questions raised by the simulations

*In plain words: three questions the simulations raised that the design owner had to decide rather than the model settle, plus one corner still left open. Recorded here so the decisions are visible as decisions, not buried as assumptions.*

All three questions the simulations raised are settled, completing the design:

- **Q7 — the post-deadline remainder: the nominal-rate tail** (§5). Zero new parameters; back-loaded conversion went from 4.5% to 76–100%.
- **Q8 — the burst window: unbounded**, R6 read literally. The whale capture curve of §7 is a documented, gated property; the endowment is first-come. **Reopenable at low cost**: `de novo*` (MODEL §8.5) bounds it to 9% for one parameter and a deferral, and the decision now has a price attached where before it had only a concession.
- **Q9 — index damping: raw `claims_prev`.** The one-epoch crash is the burst response; the cliff cycle of §7 is a documented, gated hazard, real only when a sharp entry threshold sits exactly at the operating reward.

One residual corner is documented rather than decided, because it sits outside Q7's settled scope: *inside* the window, linear amortisation's endpoint still means the last scheduled epochs offer everything that remains, so a field completely silent until epoch 194 would meet the same whole-remainder dump Q7 removed from the tail. The trigger — total prior silence through 98% of the window — is strictly narrower than the back-loaded scenario, and the candidate one-line extension (cap the sub-pool at the nominal rate whenever `claims_prev == 0`) awaits the design owner if the corner is judged worth closing.

## 9. Alternatives considered and rejected

*In plain words: the roads not taken, and why. Every entry here is a design that looked reasonable and lost for a measurable reason — recorded so that anyone tempted by one of them can see it was considered and what it cost.*

Recorded with their reasons, as instructed:

| decision | rejected alternative | why it lost |
| --- | --- | --- |
| Q1 bootstrap reward | fixed subsidy multiple `c × anchor` | one more parameter; a wrong `c` either exhausts the pool early or onboards too slowly; every cohort earning identically was its one virtue |
| Q1 bootstrap reward | time-to-bond anchor for a reference device | no free parameter and the strongest onboarding story, but it couples the reward to the difficulty and field size — the entanglement this redesign removes |
| Q2 saturation source | next epoch's sub-pool explicitly | a dim epoch after every bright one, and a wait-it-out oscillation incentive |
| Q2 saturation source | hard cap at the sub-pool | rationing; a large cohort hitting the cap is the push-away R5 forbids |
| Q3 post budget | EMA of diverted fees | one more state variable; the epoch-fixed reward already insulates claimants, and the throttle absorbs the swing |
| Q4 difficulty | one throttle in both phases | formalisation showed it composes badly with Q1: a throttle at `capacity / blocks` pins admissions at the previous epoch's level, the spike is never admitted, and R6's saturation semantics become dead code |
| Q4 difficulty | floor plus mild smoothing | the phase-switch discontinuity without the openness; worth revisiting only if the floor shows admission problems it has not shown |
| Q5 reward fixity | recompute at the saturation point | breaks the self-funding claim for exactly the cohort R5 protects |
| Q7 post-deadline tail | keep the whole-remainder dump | R6-literal but measured at 2.6% conversion: a 50M LGO windfall to a random first cohort, everyone later stranded at the anchor |
| Q7 post-deadline tail | fold the remainder to fees at the deadline | a hard end and a clean two-phase story, but the remainder then drains as anchor-sized claims and the onboarding purpose of that money is abandoned |
| Q8 burst window | cap the borrow at 3× (or 2×) the epoch budget | bounds a 10× whale's drain to ~65 (~100) epochs, but adds a constant against R1, softens R6's letter, and at 2× would already queue the measured honest ×100 cohort |
| Q9 index damping | EMA the demand index at β = 1/2 | kills the period-2 cliff cycle and softens burst punishment, but widens the whale's repricing window — affordable only with the Q8 cap that was itself rejected |
| Q6 transition | single bucket with a level test | fee noise near the boundary can flap regimes, demanding a hysteresis band — a parameter guarding a problem the two-bucket form cannot have |

## 10. Requirements, validated

*In plain words: the scorecard. Each of the eight requirements from §1, with what the simulations found and whether it holds. This is where to look if you want the short answer to "did it do what it was asked?"*

| requirement | where | result |
| --- | --- | --- |
| R1 minimality | §2.1 | two rate parameters deleted, two intent parameters added, zero added elsewhere; every remaining constant inherited |
| R2 two regimes | §3, fig. 1 | automatic, parameter-free, one-way transition at epoch 195 exactly |
| R3 onboarding | §3 | 24,674 bonds against a 25,000 intent at the band-edge triple, **if miners retire**; 7,635 if they do not |
| R4 three parameters | §2.2, §5 | the triple defines the phase; its identity check rejects unsatisfiable triples before running |
| R5 spike tolerance | §4, fig. 2 | ×100 cohort **admitted and paid in both regimes**; it *bonds* completely only under retirement (median 43 epochs), against 24% under persistence (median 69). The phase is not shortened: 196 against uniform's 196 — measured, gated |
| R6 pool integrity | §3 | conservation to the lepton; endowment monotone; saturation semantics exercised at ~97× budget (a ×k spike borrows about k budgets) |
| R7a fees, one-epoch delay | §6 | post budget = previous epoch's diverted fees, raw |
| R7b even spread | §6, fig. 4 | saturation steered into the epoch's last 2% at reference traffic; graceful degradation quantified at sparse traffic |
| R8 reward anchor | §6 | floored at the anchor in bootstrap, equal to it after; fee-drag at the anchor stated (59.7%) |

### 10.1 How much to believe the mining field

*In plain words: every number in this report depends on an assumption about what hardware people bring. This section states that assumption plainly, says which parts of it are measured and which are guesswork, and gives the range within which the conclusions hold. It matters because a study that hides its assumptions looks more certain than it is.*

Every claim-rate figure rests on an assumption about what one node commits, and that assumption deserves stating plainly because it was previously implicit — and wrong.

**The basis is now a whole four-core Raspberry Pi 5 board, 24,146 candidates a second**, measured. The de-novo engine previously seated nodes at one pinned core, 6,037, while `empowering_sim.elevation` — whose numbers this report compares itself against — had always used the board. A factor of four, between two simulators being read side by side. Corrected; and the correction moves bonds by less than 0.1% (25,191 against 25,179 on the uniform run) because the budget governs the payout, not the hashrate, which is itself the strongest evidence that these results do not rest on the field's size.

**The spread, though, is not measured.** Hashrates are drawn from `Pareto(1.16)` floored at a board, and 1.16 is the "80/20" index — a folk constant from *wealth* distributions applied to hardware. Wealth compounds; hardware is bought. Real mining populations are concentrated, but through pooling and capital access rather than the process a Pareto describes, and there is no Logos mining population to fit against because the network has not launched. **Treat the synthetic spread as one plausible shape rather than the expected one**, and treat anything that turns on its exact tail — the ×100 spike's borrow multiple, which ranges 58× to 125× across seeds — as indicative rather than precise.

The bounds that do not depend on the shape are in `power.py`: a minimal basis of one core, the board basis used here, and an adversarial basis of the best measured hardware at full duty. Section 7's attacks are run against the last of those.

## 11. Limitations

*In plain words: what this study does not cover, stated so nobody mistakes its silence for a clean bill of health.*

The simulator models the pool, the claims and the bonds; it does not model the leadership lottery, service income, or the emission side — those are the prior branch's machinery and nothing here changes them. Participation is exogenous except in the elasticity probe. The conversion-efficiency band is imported from the prior branch's elevation study rather than re-measured under the new reward dynamics; re-measuring it here, with the demand-indexed reward in place, is the natural next study, and if the band moves, the identity check's goalposts move with it. The whale analysis assumes one actor and honest blocks; a block-building whale that also orders transactions is outside scope. Fee prices are held at the resting level; the anchor tracks the fee market by construction, but no scenario here moves the market.
