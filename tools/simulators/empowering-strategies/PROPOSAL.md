> # SUPERSEDED — do not quote
>
> This document was written before three corrections that invalidate most of it. It is kept
> because its *method* is still the right one and because the record of what was wrong is
> worth more than a deletion. **Six of its seven load-bearing claims do not survive.**
>
> | claim | status |
> | --- | --- |
> | the minimum stake gates all staking income | **false** — it gates SERVICES only; the leadership lottery has no minimum, only note aging |
> | the on-ramp ceiling is 500 positions | superseded — 50,000 at the settled threshold, and it bounds services rather than consensus |
> | mining is out-earned by leading only after 20.8 years | superseded — 11.7 years, after a frozen-pool bug and with the leader share at 0.4 rather than 1.0 |
> | the yield boost costs exactly the endowment | derived from that bug; its base case was a singular point |
> | work should substitute for stake | moot for consensus — there is no threshold to substitute for |
> | the permanent gap is 600× at a 2% block-reward leg | moot — that leg does not exist; funding is fee-based |
> | goal 2's target is 13,139 base units | **stands** |
>
> What replaces it: `docs/CONTRADICTIONS.md` for the settled readings and decisions,
> `docs/REWARD-MODEL.md` for the grounded formulas, and
> `reports/EmPoWering/strategies/` for what the mechanism actually pays.

# Making EmPoWering do what it is for — a plan

*Revised after grounding the staking side in `block-rewards.md`. The obstacle is larger than
the first draft said, one of the three options is cheaper than it said, and the second goal
turns out to have a mechanism for it already in the proposal.*

Two goals, stated by the design:

1. **Proof of work is an on-ramp to proof of stake during bootstrap**, and once a node has
   onboarded, **staking must be the more affordable path** — it should not stay cheaper to
   keep mining.
2. **After bootstrap, proof of work still pays, but minimally** — of order the cost of a
   transfer plus a one-kilobyte inscription.

The current mechanism achieves neither, and the reason it fails the first is structural
rather than a matter of tuning. That has to be established first, because it rules out most
of the obvious changes.

---

## 1. The obstacle: a conservation law

Write `hashrate_share` for a miner's share of the field. Then

| `mining_income_per_epoch = hashrate_share * distribution_rate * pool` |
| --- |
| `staking_income_per_epoch = (min_stake / staked_total) * minted_per_epoch` |
| `graduation_epochs = min_stake / (hashrate_share * distribution_rate * pool)` |
| `mining_dominance = mining_income_per_epoch / staking_income_per_epoch` |

Multiplying the last two,

$$
G \cdot X \;=\; \frac{\text{staked\_total}}{\text{minted\_per\_epoch}} \;=\; \frac{1}{\text{validation\_apy}}
$$

| `graduation_epochs * mining_dominance = 1 / validation_apy` |
| --- |

**`hashrate_share`, `pool`, `distribution_rate` and `min_stake` all cancel.** The product is
one over the staking yield and nothing else — gated across a ten-thousandfold range of field
share and of pool, a hundredfold range of threshold, and a tenfold change of distribution
rate, with a relative spread of three parts in ten thousand billion.

### Its size depends on an unresolved question in the specifications

`block-rewards.md` calibrates `I_max = 1%` so that the validation yield lands near **3.33%**
once inferred total stake reaches its 30% target. That figure is the yield on the *whole*
emission. The EmPoWering proposal separately splits the block reward three ways between
Blend, leaders and proof of work, illustrated at **59/39/2**. The two cannot both hold.

| who receives the emission | validation APY | product | dominance at a 4.11-year graduation |
| --- | --- | --- | --- |
| whole emission (`block-rewards.md`'s calibration) | 3.33% | 30.0 yr | **7.3×** |
| leaders' 39% leg (proposal §5.8's illustration) | 1.30% | 76.9 yr | **18.7×** |

So staking can only pay more than mining at graduation if graduation takes longer than thirty
years — or seventy-seven, if the split lands. **Every other figure in this document is quoted
at the favourable reading.** Which of the two is intended is a question for the specifications
and it changes the answer by a factor of two and a half.

At the parameter set's own design point — about five hundred miners, which is also the most
the endowment can seat — mining pays between seven and nineteen times what the resulting
stake pays. The intended hand-off never happens on its own.

---

## 2. What can break it

### A. Raise the graduate's yield — and it costs exactly the endowment

Give proof-of-work-onboarded stake a **yield boost** that decays. Graduation time is
untouched; mining dominance falls by the multiplier.

The requirement has a clean closed form. To bring dominance to one at a graduation time of
$G$ years, the boosted yield must satisfy

| `boosted_apy = 1 / graduation_years` |
| --- |

— **independent of the base yield**, because the boost multiplies out whatever the base was.
At the design point's 4.11 years that is **24.3% a year**, whether the base is 3.33% or
1.30%. And the cost is the same either way:

| base APY | boost needed | boosted APY | cost | endowment |
| --- | --- | --- | --- | --- |
| 3.33% | 7.3× | 24.3%/yr | **50.0M LGO** | 50M |
| 1.30% | 18.7× | 24.3%/yr | **50.0M LGO** | 50M |

The cost lands on the endowment exactly, at both readings, because the boost is replacing the
same income stream it is competing with. **This is a pure reallocation, not a new subsidy** —
the first draft called it a second mechanism bolted on, and that was wrong about the cost.

*Against:* it is circular in *funding*, not in logic. The endowment can pay for the
accumulation that gets a miner to the threshold, or for the boost that makes the threshold
worth reaching, but not for both. Something else must fund whichever leg it does not.

### B. Let proof of work substitute for stake, rather than buy it

The minimum stake bounds who may validate. Work is another way to demonstrate commitment.
Let a node that sustains work **validate with less than the minimum stake**.

This dissolves the conservation rather than paying to overcome it: graduation stops being an
accumulation problem, so the on-ramp's duration becomes a difficulty choice independent of
what any pool pays. The endpoint follows by construction — stake costs nothing to hold and
work costs electricity continuously, so a node that can stake outright prefers to.

**It is also the only option indifferent to the unresolved split**, since it never references
the staking yield. Given that the split moves every other answer by 2.5×, that robustness is
worth a great deal.

Calibration should be stated as a ratio rather than a number, because the number moves with
both the token price and the unresolved split:

| `work_substitution: annual electricity cost of the work == annual opportunity cost of the stake it replaces` |
| --- |

Evaluated, that ratio spans **8 to 216 Raspberry Pi equivalents** per minimum stake replaced
across the plausible range of token price and yield — which is exactly why the rule belongs
in the specification as a ratio the protocol can re-derive, not as a constant.

*Against:* the largest specification change, and it touches consensus security directly. The
share of validating weight that work may substitute for has to be capped, or the sybil bound
the minimum stake provides is lost. **This is the open question, and it is the reason B is a
proposal rather than a recommendation to adopt.**

### C. Pay in locked, staking-eligible balance

Claims mint locked stake instead of spendable tokens, so mining and staking stop being
alternatives. *Against:* a locked token earns the same yield as an unlocked one, so the
conservation still binds exactly. It improves the framing and does not deliver goal 1.

---

## 3. Goal 2 already has a mechanism, and it is mis-sized by four orders of magnitude

The target is a transfer plus a one-kilobyte inscription:

| `minimal_reward = transfer_fee + inscription_fee = 5,579 + 7,560 = 13,139 base units` |
| --- |

The proposal's §5.8 already gives proof of work a leg of the block reward,
`block_reward_pow_share`, illustrated at 2%. **That leg is the natural home for goal 2** — it
is permanent, it needs no endowment, and it tracks the emission schedule rather than floating
with fee revenue as the current pool-funded reward does.

But the illustrated size is wrong for this purpose by a wide margin:

| | per claim |
| --- | --- |
| goal 2's target | 13,139 base units = 1.97 claim fees |
| what a **2%** leg would pay | 190,258,752 base units = **28,550 claim fees** |
| ratio | **14,480×** |

The share that delivers goal 2 is **1.38 parts per million** of the block reward, not two
percent. So §5.8's split is calibrated for some other purpose, and if goal 2 is what the
proof-of-work leg is for, that leg is four orders of magnitude too large.

---

## 4. The single coherent mechanism

Changes B and §3 compose into one rule with no bootstrap regime and no steady-state regime:

> **A claim always pays a fixed leg of the block reward, sized to a reference transaction
> bundle. Sustained work substitutes for stake in validating weight, up to a capped share.**

- **Goal 1** holds by construction: work costs electricity continuously and stake costs
  nothing to hold, so any node able to stake outright prefers to. No crossover has to be
  arranged and no yield has to be subsidised.
- **Goal 2** holds by definition: the payment *is* the bundle, in every era.
- **The endowment is no longer needed.** It was funding an accumulation race to a threshold
  that work now substitutes for directly. Half a percent of supply is freed, and §10.2's
  question about whether that is the right size dissolves rather than being answered.

One mechanism, one payment rule, one parameter with a stated derivation. If B's security
question cannot be closed, the fallback is A for goal 1 plus the resized block-reward leg for
goal 2 — two mechanisms, both fully costed above, with the endowment paying for the yield
boost rather than for mining rewards.

---

## 5. What to build, in order

**5.1 Settle the emission question first.** Whether validators receive the whole emission or
a 39% leg changes every number here by 2.5×, and it is a reading of the specifications rather
than a simulation. Nothing downstream is worth refining until it is answered.

**5.2 The sybil bound on B.** Now the binding question. A validating-weight model in which
work and stake both contribute, with a cap on the work share, and a demonstration that the
bound survives an attacker splitting across identities. Until this exists B is not
recommendable.

**5.3 Re-derive the minimal reward from the specification's own fee schedule.** The 13,139
figure uses the resting price and an assumed inscription size; both should come from the tree,
and the reward should be *defined* as the bundle so it tracks the fee market.

**5.4 Price A and B on the same axes** as the base, through the existing working-region
sweep: graduation time, dominance at graduation, participants seated, and which device classes
stay in the field.

**5.5 Re-run the affordability frontier under B.** If work substitutes for stake the incentive
to mine becomes continuous rather than decaying, which changes who is priced out and for how
long. It should not be assumed to carry over.

**5.6 Retire the endowment sizing study, or re-pose it.** Under the unified mechanism the
endowment has no job. That is a larger change to the proposal than anything else here and
should be stated plainly rather than discovered later.

---

## 6. What is uncertain

- **The reading of goal 1.** "Staking must be the more affordable path" is taken to mean
  economically preferable once onboarded. Under the weaker reading — merely cheaper to
  operate — it already holds, and only goal 2 needs work.
- **Who receives the emission**, per §1. The single largest uncertainty, and the one that
  makes every figure here a favourable case.
- **B's security bound**, per §5.2. Unquantified.
- **Aging under B.** Mined proceeds are not staking-eligible on arrival: a note must be held
  for a minimum period and appear in a frozen stake-distribution snapshot before it can win a
  slot, and the service declaration protocol reads `finalized_epoch = current_epoch - 2`. That
  is now modelled, at two epochs, and it is immaterial to everything above — one percent of a
  two-hundred-epoch graduation. **But it is not immaterial to B.** If sustained work
  substitutes for stake, work-derived weight needs its own eligibility rule, and it cannot
  simply inherit the note's: work is continuous where a note is discrete, so "held for a
  minimum period" has to be restated as something like a trailing window of demonstrated work.
  Getting that wrong is a grinding surface — an attacker who can make weight count sooner than
  honest participants can gains exactly the advantage the aging exists to deny.
- **The token price**, which sets B's calibration in absolute terms. Handled by stating the
  rule as a ratio, but the ratio still has to be evaluated somewhere to be checked.
