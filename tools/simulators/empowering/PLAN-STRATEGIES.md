# Strategy comparison — plan

Simulate five participation strategies **at the same time, on one honest chain**, and measure
what each accumulates. No Blend, no network delay, no adversary: the question is which
strategy pays, on a chain where everyone behaves.

| # | strategy | mines | lottery | services |
| --- | --- | --- | --- | --- |
| 1 | proof-of-work miner | yes | no | no |
| 2 | miner and staker | yes | yes, on what it mines | no |
| 3 | miner, staker and service provider | yes | yes | yes, on reaching the minimum |
| 4 | stakeholder | no | yes, on initial stake | no |
| 5 | stakeholder and service provider | no | yes | yes |

Every group is independently switchable, and any combination must run.

---

## 1. The measurement problem, before the mechanics

**Groups 1–3 start with nothing and bring hardware. Groups 4–5 start with 5% of supply
each and bring capital.** At the defaults that is 5×10⁸ LGO across 100 nodes — five million
LGO apiece — against miners who start at zero and share a 5×10⁷ LGO endowment three hundred
ways. A raw comparison of accumulated rewards therefore answers "who was given more at
genesis", which is not the question.

So the runs report three things, and the plan treats the third as the headline:

| measure | what it answers |
| --- | --- |
| **accumulated reward per node** | what the user asked for; dominated by the initial endowment |
| **reward per unit of resource brought** | reward per LGO staked, reward per candidate-per-second of hashrate |
| **reward relative to doing nothing** | what the strategy ADDS over simply holding — the only measure comparable across groups without a token price |

Strategy 4 is the natural baseline: holding stake and doing nothing but the lottery. Every
other strategy is then reported as its increment over that.

**One genuinely unresolvable comparison** is flagged rather than papered over: miners spend
electricity and stakeholders do not, so a complete answer needs a token price and a tariff.
The cost estimator supplies both as a band; the plan reports rewards gross and net, and says
which is which.

---

## 2. The reward model, now grounded — and it reorders the strategies

The extraction pass is complete and verified against the source. Two findings change the
study before it is built.

### Service rewards are FLAT per provider, with no stake term at all

`blend-protocol.md:1106-1126`: the service income `I` is split `R = I/(B+P)` across providers
with a true activity proof, doubled for those at minimal Hamming distance. **The formula
contains no stake term.** Stake is a binary admission gate — `assert note.value >=
min_stake.stake_threshold` — and nothing more. A provider at the bare minimum earns exactly
what a whale earns.

### What each stream actually pays one node, per epoch

At maximum emission, the block reward is 62500/657 = 95.1294 LGO per block — 2,054,795 per
epoch, split **60% Blend / 40% leaders** (`overview-cryptoeconomics.md:142-145`).

| stream | per node, per epoch |
| --- | --- |
| service provision, flat, 100 providers | **12,329 LGO** |
| staking 5,000,000 LGO (of 10% of supply staked) | 4,110 LGO |
| mining, one of 300 equal miners, at genesis | 833 LGO |
| staking the bare minimum, 100,000 LGO | 82 LGO |

**Service provision pays three times what a five-million-LGO stake pays, and it is flat.**
So the ordering is 5 > 3 > 4 > 1,2 — and the entire value of the on-ramp is not the mining
reward at all, it is *reaching the threshold that unlocks flat service income*. That reframes
the earlier 500-position ceiling: it bounds access to the most lucrative stream on the chain.

### Consequences for the build

- **Service rewards must be modelled even though Blend must not be.** The only service type
  is `ServiceType.BN`, so the service stream *is* the Blend stream. Its network mechanics —
  mixing, cover traffic, delay — stay out; its reward does not, because it dominates.
  On an honest chain every declared provider is active, so the Hamming lottery collapses to
  "an active provider is paid", which is stated as a modelling assumption, not hidden.
- **A hard gate at 32 unique providers**: below it, `blend-protocol.md:1110`, rewards *"are
  not calculated"* at all and the service halts. Group sizes must clear it.
- **Leader payment is not a function of the block proposed.** Winning mints a *voucher*;
  the payment is `floor(leader_rewards / (voucher_cm - voucher_nf))` at claim time
  (`bedrock-anonymous-leaders-reward.md:93-98`). The claiming policy is UNSET, so the
  simulator assumes prompt honest claiming and says so.
- **The emission control function is fully specified** in normative integer form,
  `A_t' = min(12e7, max(0, 3e9 - D_0t + 10512 * sum_{119}(D_1)))` with `STAKE_TARGET = 3e9`
  — confirming the 30% target and the 95.1294 LGO block reward independently.
- **`min_stake.stake_threshold` is UNSET in the specification.** Only an analysis derives it.
  It is therefore a sweep axis, not a constant — and since it gates the most valuable stream,
  it is the most consequential axis in the study.

The extraction also lists eleven contradictions between documents, several load-bearing. The
APY one is already gated here; the others need reading before they can be ranked.

---

## 3. Population and draws

**Paired draws, so the comparison is of strategies and not of luck.**

- **Hashrate**: one Pareto sample, minimum set to a Raspberry Pi 5's measured rate
  (24,146 candidates/s — four cores at the measured 165.658 µs), drawn once and **reused
  identically by groups 1, 2 and 3**.
- **Stake**: one Pareto sample scaled so the group totals 5% of launch supply, drawn once and
  **reused identically by groups 4 and 5**.
- Groups 2 and 3 hold no initial stake; theirs accrues from mining.
- Draws are keyed to a fixed seed per vector, **not** per enabled group, so switching a group
  off does not change what the others see.

Shape parameters for both Pareto distributions are configuration, with the tail index stated
rather than defaulted silently — it controls concentration, and concentration is exactly what
the earlier work showed drives the on-ramp's conversion efficiency.

---

## 4. What the chain does each epoch

1. **Proof of work.** Claims drawn once at the network rate and dealt multinomially — exact,
   as already gated. Only groups 1–3 contribute hashrate.
2. **Leadership.** `blocks_per_epoch` leaders drawn multinomially over **aged** stake, which
   is exact for the same reason. Aging is two epochs. Any aged balance carries weight, with no
   minimum: that is the corrected reading, and groups 2 and 3 therefore enter the lottery as
   soon as their first mined notes age.
3. **Emission.** The block reward is `A_t · I_max · S_tge · Δt / f + (1 − A_t) · R_block`,
   with `A_t` from the KPI control function. The staked fraction is an OUTPUT here, not an
   input: at the defaults only 10% of supply is staked, far below the 30% target, so `A_t`
   sits near 1 and the yield is correspondingly high. As groups 2 and 3 accumulate, the
   fraction moves and the emission responds. That feedback is the point of modelling it.
4. **Services.** Groups 3 and 5 declare once eligible, subject to the declaration lag; group 3
   only after accumulating the minimum.
5. **Accounting.** Every reward credited to a node by source.

**An interaction to resolve from the spec, not assumed:** a service declaration proves a
**locked** note. If locking removes it from the lottery, a service provider trades leader
weight for service income and strategies 3 and 5 are not strictly dominant over 2 and 4. The
extraction pass is asked this directly.

---

## 5. Outputs

**Headline.** Accumulated reward per node, per strategy, over the run — as a distribution
rather than a mean, since the earlier work showed dispersion is where the interesting
behaviour lives. Plotted against the resource each node brought, so level and concentration
are both visible.

**Per-strategy summary.** Total and median accumulated reward; reward per unit of resource;
increment over the strategy-4 baseline; and for mining strategies, the same net of electricity
at a stated tariff and token price.

**Distributions of the proof-of-work reward**, which the user asked for specifically:
a histogram per block and a histogram per epoch. The per-block one is the claim count times a
reward fixed within the epoch, so its shape is the arrival process; the per-epoch one carries
the reward's decay as well. Both are recorded from the engine rather than reconstructed.

Every figure carries the command that regenerates it, per the repo's convention.

---

## 6. Build order

| # | step | depends on |
| --- | --- | --- |
| 1 | reward model of record, from the specs, verified | extraction pass (running) |
| 2 | config: five groups, counts, enable flags, Pareto shapes, tariff and token price | 1 |
| 3 | paired Pareto samplers, keyed per vector | 2 |
| 4 | leadership lottery and the emission control function | 1 |
| 5 | service declaration, eligibility and reward | 1 |
| 6 | per-node, per-source reward accounting | 3, 4, 5 |
| 7 | per-block and per-epoch reward recording | 6 |
| 8 | gates | 6 |
| 9 | figures and the summary table | 7 |

**Gates that must exist before any number is quoted:**
- conservation — every LGO credited traces to a pool payout or a mint, and the totals reconcile
- the shared draws are bit-identical across the groups that share them
- switching a group off does not perturb the others
- each group runs alone, and every pair runs
- the staked fraction, the emission factor and the yield agree with the closed forms
- the strategy-4 baseline reproduces the analytic yield on its own stake

---

## 7. What this deliberately does not model

No Blend network, no network delay, no propagation, no forks, no adversary, no churn. Every
node behaves honestly and stays for the whole run. Traffic and the fee level remain exogenous.
The point is a clean comparison of strategies on an honest chain; anything that would blur
that is out.
