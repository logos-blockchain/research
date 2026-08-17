# Making EmPoWering do what it is for — a plan

Two goals, stated by the design:

1. **Proof of work is an on-ramp to proof of stake during bootstrap**, and once a node has
   onboarded, **staking must be the more affordable path** — it should not stay cheaper to
   keep mining.
2. **After bootstrap, proof of work still pays, but minimally** — of order the cost of a
   transfer plus a one-kilobyte inscription.

The current mechanism achieves neither, and the reason it fails the first is structural
rather than a matter of tuning. That has to be established before any change is proposed,
because it rules out most of the obvious ones.

---

## 1. The obstacle: a conservation law

Write `hashrate_share` for a miner's share of the field. Then

| `mining_income_per_epoch = hashrate_share * distribution_rate * pool` |
| --- |
| `staking_income_per_epoch = (min_stake / staked_total) * minted_per_epoch` |
| `graduation_epochs = min_stake / (hashrate_share * distribution_rate * pool)` |
| `mining_dominance = mining_income_per_epoch / staking_income_per_epoch` |

Multiply the last two:

$$
G \cdot X \;=\; \frac{\text{staked\_total}}{\text{minted\_per\_epoch}}
$$

| `graduation_epochs * mining_dominance = staked_total / minted_per_epoch` |
| --- |

**`hashrate_share`, `pool`, `distribution_rate` and `min_stake` all cancel.** The product is
one over the staking yield, and nothing else. Measured, it is 1,460 epochs — thirty years:

| miners | share each | graduation | mining dominance | product |
| --- | --- | --- | --- | --- |
| 100 | 1% | 0.82 yr | 36.5× | 1,460 |
| 500 | 0.2% | 4.11 yr | 7.3× | 1,460 |
| 5,000 | 0.02% | 41.1 yr | 0.73× | 1,460 |
| 80,000 | 0.00125% | 658 yr | 0.046× | 1,460 |

So **staking can only dominate at graduation if graduation takes longer than thirty years.**
Fast onboarding and a staking-favoured endpoint are the same dial pulled in opposite
directions, and no choice of endowment size, distribution rate, claim target or minimum
stake escapes it. The mechanism cannot be tuned into its own goal; a term in that product
has to be broken.

### What this says about the current design

At the parameter set's own design point — about five hundred miners, which is also the most
the endowment can seat — mining pays **7.3×** what the resulting stake pays. A graduate has
every reason to keep mining, and the design's intended hand-off never happens on its own.

---

## 2. What can break it

The product is fixed because mining income and graduation time are both proportional to the
same quantity, `hashrate_share * distribution_rate * pool`. Three families of change break
different terms; each is a real mechanism, not a parameter.

### A. Raise the graduate's yield, not the miner's income

Give proof-of-work-onboarded stake a **bootstrap yield multiplier** that decays. Graduation
time is untouched; mining dominance falls by the multiplier.

To make staking dominate at a four-year graduation needs roughly a **7.5× boost**, so about
25% a year against the base 3.33%. Costing it: 500 graduates × 100,000 LGO × 25% × 4 years
is **50 million LGO — exactly the endowment**. The same 0.5% of supply, spent as a yield
subsidy rather than as mining rewards, buys precisely the missing factor.

*Against:* it is a second mechanism bolted beside the first, and it is circular — a miner
still has to accumulate the minimum stake by mining before the boost can apply to anything.

### B. Let proof of work substitute for stake, rather than buy it

The minimum stake exists to bound who may validate. Proof of work is another way to
demonstrate commitment. Let a node that sustains work **validate with less than the minimum
stake**, with the work standing in for the missing capital.

This dissolves the conservation entirely, because graduation stops being an accumulation
problem: the on-ramp's duration becomes a difficulty choice, independent of what the pool
pays. And the endpoint follows by construction — holding stake costs nothing to maintain
while work costs electricity continuously, so any node that can stake outright prefers to.

The natural calibration anchor already exists: work should cost about what the stake it
replaces costs to hold. The minimum stake's opportunity cost is 3,333 LGO a year; a
Raspberry Pi's electricity is roughly 77 kWh a year. At the same token and electricity
prices those meet at **about twenty Pi-equivalents of continuous work per minimum stake
replaced** — a number the cost estimator produces and that can be re-derived whenever
prices move.

*Against:* the largest specification change of the three, and it touches consensus
security directly. The share of validating weight that work may substitute for has to be
capped, or the sybil bound the minimum stake provides is lost.

### C. Pay in stake rather than in liquid tokens

Claims mint **locked, staking-eligible** balance instead of spendable tokens. Mining and
staking stop being alternatives and become one position that grows two ways.

*Against:* it changes what a claim *is* without changing the arithmetic. The conservation
still binds, because a locked token earns the same yield as an unlocked one. It improves the
framing and the incentives at the margin, and it does not by itself deliver goal 1.

---

## 3. Goal 2, and where it unifies with goal 1

The target is a transfer plus a one-kilobyte inscription:

| `minimal_reward = transfer_fee + inscription_fee = 5,579 + 7,560 = 13,139 base units` |
| --- |

which is **1.97 claim fees**. The current steady reward is 33,474 base units, or 5.02 claim
fees — only 2.55× the target, so the *level* is nearly right already. What is wrong is the
*definition*: the steady reward is `pow_share * fee_revenue / target_claims_per_block`, so it
floats with traffic and with the fee market, where goal 2 asks for it to be pinned to a
stated bundle of transactions.

**This is where a single mechanism becomes possible.** Under change B the endowment is no
longer spent buying anyone their minimum stake, because work substitutes for it directly. Its
only remaining job is to pay the minimal reward — and at 13,139 base units a claim, fifty
million LGO funds **about 3.8 billion claims, some 360 years** of it. So one pool, one
payment rule, no bootstrap regime and no steady-state regime:

> A claim always pays the cost of a reference transaction bundle. Sustained work substitutes
> for stake up to a capped share of validating weight. The endowment exists to fund the
> payment, and it is large enough to do so for centuries.

Goal 1 holds because staking is free to maintain and work is not. Goal 2 holds because the
payment is the bundle, by definition, in every era. There is no decaying reward, no
crossover to arrange, and no second mechanism.

---

## 4. What to build, and in what order

Each step answers something the step after it depends on.

**4.1 Gate the conservation law.** It is the load-bearing claim and it should fail loudly if a
future change makes it false. One test: vary share, pool, distribution rate and minimum stake
independently and demand the product does not move.

**4.2 Price the three changes on the same axes.** Extend the existing sweep so each candidate
is run through the same working-region tests as the base — graduation time, mining dominance
at graduation, participants seated, and which device classes stay in the field. Nothing here
should be argued that can be measured.

**4.3 Model change B properly**, since it is the recommendation. Three things it needs that
the simulator does not yet have:
- a validating-weight model in which work and stake both contribute, with a cap on the work
  share;
- the sybil question, which is now the binding security question rather than an aside: the
  cap must be shown to bound an attacker who splits across identities;
- a calibration for how much work substitutes for how much stake, from the cost estimator
  rather than assumed.

**4.4 Re-derive the minimal reward against the specification's own fee schedule.** The 13,139
figure uses the resting price and an assumed inscription size. Both should come from the
specification tree, and the reward should be defined in terms of the bundle so it tracks the
fee market instead of being restated whenever prices move.

**4.5 Re-run the endowment sizing.** Under B the endowment stops being a bootstrap subsidy and
becomes a very long-lived payment fund, so the question "is half a percent of supply the right
size?" changes meaning completely and should be asked again in the new terms.

**4.6 Check what B does to the affordability frontier.** If sustained work substitutes for
stake, the incentive to mine becomes continuous rather than decaying, which changes who is
priced out and for how long. The frontier study should be re-run, not assumed to carry over.

---

## 5. What is uncertain

- **The reading of goal 1.** "Staking must be the more affordable path" is taken here to mean
  staking should be economically preferable once onboarded, not merely cheaper to operate. If
  the weaker reading is intended, it holds already — staking burns no electricity — and only
  goal 2 needs work.
- **The staking yield is grounded, and the split is not.** The 3.33% a year is the
  specification's own figure: `block-rewards.md` calibrates `I_max = 1%` precisely so that the
  validation yield lands near 3.33% when inferred total stake reaches its 30% target, and
  `analysis-block-reward-parameter-calibration.md` sets that target. This simulator computes
  3.33% independently from those two constants and the agreement is gated.

  Two qualifications on it, both stated by the source material. The specification's block
  reward is `A_t * I_max * S_tge * dt / f + (1 - A_t) * R_block`, so the figure above is the
  `A_t = 1` case -- maximum emission, which the specification calls the bootstrap phase and
  which is exactly the regime the on-ramp operates in. And the yield is on the *whole*
  emission, whereas the EmPoWering proposal separately splits the block reward three ways
  between Blend, leaders and proof of work, illustrated at 59/39/2. If that split lands a
  validator receives only its leg and the yield falls to roughly 1.3%, which raises the
  conservation product from thirty years to about seventy-seven. **The obstacle gets worse,
  not better** -- so the figures here are the favourable case for the current design.
- **The security bound on change B** is unquantified and is the reason it is a proposal rather
  than a recommendation to adopt. The minimum stake is a sybil bound; anything that lets work
  stand in for it must show the bound survives.
