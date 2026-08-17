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

## 2. Ground the reward formulas first

Two of the four streams are not yet in the model at all, and a simulator that invents them is
worse than none. A spec-extraction pass is running now over the specification tree, verified
against the source, producing a **reward model of record**: formula, exact integer arithmetic,
every parameter with its citation, eligibility, and timing.

| stream | state |
| --- | --- |
| proof-of-work claims | modelled and gated; confirm constant names against the Mantle spec |
| leader reward | share now grounded at **0.4** of the block reward (`overview-cryptoeconomics.md`, as code); lottery, aging and slot-to-block rate to confirm |
| emission rate factor | **missing** — the control function for `A_t` from the two KPIs |
| service reward | **missing entirely** — formula, eligibility, timing, whether it scales with stake |

Nothing downstream is worth building until that lands.

### A contradiction already found, and it is load-bearing

`block-rewards.md` calibrates `I_max = 1%` so that "the APY for validation is ~3.33%", which
holds only if validators receive the whole emission. `overview-cryptoeconomics.md` gives
leaders `0.4 * get_block_rewards(b)`, with Blend taking the other 0.6. Both cannot be true.

Taking the stated 0.4, the validator yield at the 30% stake target is **1.33%**, not 3.33% —
and the mining-to-leading hand-off moves from 8.05 years to **11.69 years**. The config now
carries 0.4 with the tension recorded. Which document governs is a question for the
specifications and it moves every result in this study.

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
