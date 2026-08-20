# EmPoWering — where the design stands, and what to do

**Read this first.** It states what the mechanism is for, what the three candidate designs do, what the simulations found, and what I would do. Everything here is measured; the supporting documents carry the workings, and `design-comparison.md` §0 explains the choice in plain language for a reader who wants no arithmetic at all.

---

## 1. The job, in one paragraph

Somebody who owns no tokens should be able to join the network by doing computation, be paid for it, save enough to post the deposit that lets them run a paid service, and so become part of the system that secures it. Work, save, join. Proof of work is the on-ramp; proof of stake is the destination. The design question is how the tokens set aside for that on-ramp should be handed out.

## 2. The three designs

| | **current** | **de novo** | **de novo\*** |
| --- | --- | --- | --- |
| how the money is handed out | a fixed number of prizes per block, forever, at a price that decays geometrically | a per-epoch budget, spent on whoever turns up; a crowd is paid by borrowing against later epochs | the same, with a bound on how much the endowment may give up in one epoch |
| what is fixed | the claim rate and the outflow | the budget schedule and the reward's floor | the same, plus the borrow ceiling |
| parameters to defend | 3 | 3 | 4 |
| status | specified today | this branch's proposal | the proposal plus one mitigation |

The redesign's three parameters are the ones you can hold an opinion about — **how much money, how many nodes, over how long** — and a consistency identity checks the triple before anything runs. The current design's two rate constants (`distribution_rate`, `target_claims_per_block`) are the two nobody could defend without a simulation.

## 3. What the simulations found

Everything below is at the reference parameters (0.5% of TGE, 25,000 nodes, four years), a field of whole Raspberry Pi 5 boards, and both retirement regimes.

### 3.1 Onboarding

| | current | de novo | de novo\* |
| --- | --- | --- | --- |
| nodes onboarded, **retiring** | 25,934 | 24,707 | 24,782 |
| nodes onboarded, **persistent** | 5,682 | 7,963 | 7,963 |
| a ×100 cohort's fate, retiring | door already shut | 100% bonded | 100% bonded |
| a ×100 cohort's fate, persistent | door already shut | 24% bonded | 24% bonded |
| bootstrap ends | never | epoch 196 | epoch 196 |

**All three onboard about the same number of nodes.** The redesign's advantage is not volume — it is that the number does not depend on *when* people arrive.

### 3.2 The three properties the current design has and the redesigns do not

Measured in the strategy report's arrivals study, and absent from both redesigns:

- **A best adoption speed.** Elevation is a hump: 951 nodes at two arrivals an epoch, ~6,100 near a hundred, 5,001 at five hundred. The worst rate onboards a sixth of the best.
- **A closing door.** The last cohort with even odds of ever bonding arrives at epoch 270 at ten arrivals an epoch, epoch 34 at a hundred, epoch 6 at two hundred and fifty.
- **A point of no return.** The waiting queue passes every bond the endowment can still fund at epoch 212 (a hundred an epoch), computable from the pool alone.

All three are the same fact seen three ways: a fixed claim flow means a bigger crowd is a thinner slice each. Neither redesign has any of them, because the budget follows the people.

### 3.3 The whale — the redesigns' cost, and its remedy

| a 10× actor at its best moment (epoch 20) | current | de novo | de novo\* |
| --- | --- | --- | --- |
| endowment captured, realistic field | cannot be drained | **55%** | **9%** |
| against a homogeneous field (the bound) | cannot be drained | 89%, phase collapses to epoch 23 | — |
| capture at 3× / 100× | — | 33% / 56% | 9% / 9%, flat |

The current design cannot be drained by anyone, because its outflow is fixed — a genuine advantage, bought with precisely the rationing that gives it the closing door. `de novo*` recovers most of that protection by bounding what the endowment may give up per epoch *beyond* the scheduled amount, which converts instant extraction into extraction the demand index has time to reprice.

**A flat cap in budgets cannot work** and this is worth knowing: an honest ×100 cohort borrows about 97 budgets, which is already half the endowment, so any cap loose enough to admit the crowd R5 protects admits the whale too. The workable form is a fraction of what remains.

**What `de novo*` costs:** one parameter with no natural value, a softening of "pays until exhausted" within an epoch, and — *only in the retiring regime* — a 40% longer wait for spike cohorts (43 epochs to 59). **Under the persistent regime it costs nothing measurable at all.**

### 3.4 Attacks, all three designs

| | current | de novo | de novo\* |
| --- | --- | --- | --- |
| withholding to inflate the reward | impossible — the reward ignores demand | **loses money below half the field**: 0.44× at 10%, 0.80× at 50%; pays 2.80× at 90% | same |
| harvesting a participation cycle | no cycle exists | unprofitable (0.02–0.86×), but the cycle is real and easy to trigger | same |
| sybil flood, 2× the honest field | **48.4% of honest joiners denied** | **3.5%** | 3.5% |
| sybil flood, 10× | 96.3% | 92.8% | 92.8% |

Two things stand out. The redesigns' one novel attack surface — a demand-indexed reward inviting manipulation — **closes by measurement**, and the defence is an accident: the reward cap written so that genesis could not hand one claim the whole sub-pool also bounds what a shrunk denominator can buy. And at moderate sybil flooding the redesigns are an **order of magnitude** more resistant, because a fixed flow halves every share while a budget just converts faster.

### 3.5 The finding that applies to all three, and matters most

**Nothing pays a bonded miner to stop mining.** Both designs quote their headline numbers assuming they do. A bonded node can run its service *and* keep mining on the same hardware, and the marginal claim is profitable unless a token is worth less than $0.0001.

Measured in this mechanism, retirement is not one number at two values but two different shapes:

| arrivals an epoch | 65 | 130 | 260 |
| --- | --- | --- | --- |
| **persistent** (nobody retires) | 13.9% | 15.9% | 14.6% — flat |
| **retiring** | 24.9% | 49.4% | 74.1% — rises with the rate |

And the arithmetic of why nobody retires: **it costs the individual 6.2% of their income and buys the network 4.5× more onboarding.** A collective-action problem in textbook form. Every headline in every document is therefore given at both ends, and the persistent end is the one to plan against.

### 3.6 What proof of work becomes afterwards

Once the endowment is spent, the reward is one transfer plus one inscription, which nets 4.494 × 10⁻⁶ LGO against $0.00136 of electricity per claim. Mining stops paying and the field shrinks to fit: **0.4, 37 and 3,677 Pi 5-equivalents at $0.01, $1 and $100 a token.** Proof of work becomes vestigial — which is the brief working as written ("pay out, but at a very minimal amount"), not a defect. It does mean the post-phase funds no security and should not be relied on for any.

## 4. Recommendation

**Adopt `de novo*`, with the reference triple re-struck against the persistent regime.**

The reasoning, in order of weight:

1. **The current design's three pathologies are real, measured, and structural.** A best adoption speed, a door that closes inside the first year at plausible adoption, and a computable point of no return are not tuning problems — they follow from rationing a fixed flow, and no parameter choice removes them. For a mechanism whose entire purpose is onboarding, a door that shuts at epoch 34 is disqualifying.

2. **The redesign's cost was the whale, and `de novo*` closes it** for one parameter and a deferral that vanishes in the regime that will actually obtain. 55% to 9%, flat in the attacker's size. Paying one parameter against R1 to remove the design's only serious concession is a good trade, and R1 was always a preference rather than a constraint.

3. **The redesign's novel risks did not survive contact with simulation.** Withholding loses money, the cycle is unprofitable, and sybil resistance is better than the incumbent's. The things I expected to sink it did not.

4. **Re-strike the triple.** At the persistent efficiency (~15%) the reference triple's implied 50% is a bet on two behaviours — retirement *and* fast arrival. The identity puts 25,000 nodes at **1.67% of TGE**, and simulating that triple delivers 20,300 of them; **2% delivers 22,300**, the shortfall being that arrivals must also be fast enough to spend it. So either budget roughly **2% of TGE for a 25,000-node ambition**, or keep 0.5% and state **about 8,000** as its honest expectation. Planning against the optimistic edge is the single most likely way for this design to disappoint in production.

**What I would not do:** add a sybil defence. The design owner's position — proof of work is sheer power, and buying more of it entitles you to more reward however many identities you wear — is coherent, and every remedy would make the mechanism something other than proof of work. The flood is a property to size, and it is sized.

**What remains genuinely unknown**, and is worth closing before launch: the token-price paths behind the profitability view are stylised, not fitted, so any conclusion that turns on price level rather than price *shape* should be re-checked against a real assumption.

The GPU question is now *estimated* rather than open, and the answer is more comfortable than expected. Poseidon2 over BN254 costs ~3,400 field multiplications per candidate, and published GPU throughput for BN254 is below 1 Gops/s — a hundredfold worse than small fields, because a 254-bit non-special modulus suits GPU ALUs badly. A card manages ~294,000 candidates a second, twelve times a Pi 5 board, but spends about **four times more energy per candidate**. So a GPU rig is much faster and no cheaper: the cost-bounded attacks in the analysis are not understated, while the share-bounded ones are. **The mechanism inherits meaningful GPU resistance from the curve choice**, which is worth knowing deliberately rather than by luck. It is still an estimate and should be benchmarked.

## 5. Where the workings are

| document | what it carries |
| --- | --- |
| `design-comparison.md` | the three designs side by side; **§0 is the plain-language explanation** |
| `denovo-report.md` | the redesign in full, validated requirement by requirement |
| `adversarial-analysis.md` | every attack, run in the simulators, both designs |
| `MODEL.md` | the normative specification, including `de novo*` at §8.5 |
| `MAPPING.md` | what each design changes in the specification tree |
| `PLAN.md` | all nine design decisions with their reasoning and audit trail |
| `web/` | three browser pages: the bootstrap calculator, the design comparison, and mining profitability |

Every number in these documents is pinned by the validation suite (`make validate`), so a change that moves one fails a gate rather than drifting quietly.
