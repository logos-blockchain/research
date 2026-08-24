# The eleven contradictions, resolved

The reward extraction found eleven places where the specifications disagree. Each is settled
below, with the rule used and the consequence. **All eleven are now settled: ten resolve from
the documents, and one — 4.3 — cannot be settled by them and is DECIDED as a parameter** (the
genesis rule, `D = 10^10`). Its four-orders-of-magnitude table is the gap between the two
readings at launch, not the study's error bar: the estimator converges in about five epochs,
so the decided reading costs a launch transient, negligible over a multi-year horizon.

## The precedence rule

Every document carries a `Category` field. Where two disagree, **Standards Track governs
Informational**. Two further rules were needed:

- **Within one document, executable text governs prose.** A reference implementation is what
  an implementer follows; a justification column is commentary.
- **A document that explicitly defers to another is not authority against it**, whatever its
  own category.

Relevant classifications, since one is counter-intuitive:

| Standards Track | Informational |
| --- | --- |
| `block-rewards`, `bedrock-genesis-block`, `bedrock-service-reward-distribution`, `bedrock-service-declaration-protocol`, `execution-market`, `storage-markets`, `bedrock-anonymous-leaders-reward`, `blend-protocol`, `cryptarchia-proof-of-leadership`, `common-cryptographic-components` | `overview-cryptoeconomics`, **`bedrock-v1.1-mantle-specification`**, all three `analysis-*` |

---

## 4.1 The validator APY — 3.33% or 1.33%

`block-rewards.md:167` justifies `I_max = 1%` as giving "the APY for validation is ~3.33%",
which requires validators to receive the whole emission. The **same document**, at `:497-498`,
implements `leader_reward = reward_numerator * 4 // (reward_denominator * 10)` — a 40% share.

**Resolved: 1.33%.** Executable text governs prose within one document, and the split is
independently corroborated by `execution-market.md:62` (Standards Track).

**Consequence, and it is a defect worth reporting upstream:** `I_max` was calibrated to hit a
number the mechanism does not deliver. To give validators 3.33% at the 30% target, `I_max`
would have to be **2.5%**, not 1%. The participation incentive the entire stake-KPI control
loop is built around is 2.5× weaker than its own calibration assumed.

## 4.2 `α_d` — 1/4 or 1/6

`block-rewards.md` (Standards Track) says 1/4 twice and builds the normative integer form on
it. `analysis-block-reward-parameter-calibration.md:80` (Informational) says 1/6.

**Resolved: 1/4**, by precedence.

**Note:** neither value reproduces the rationale the analysis gives for it. Saturation ends at
`δ = I_max/α_d`, which is 4% at 1/4 and 6% at 1/6 — not the 16.6% claimed. A separate
documentation defect; it does not change which value governs.

## 4.3 `D` at genesis — **DECIDED: the genesis rule, D = 10^10**

Both documents are Standards Track and they disagree directly.

- `bedrock-genesis-block.md:317`: *"D: The initial estimate of total stake will be the total
  tokens distributed at genesis."* — on the order of 10¹⁰ LGO.
- `block-rewards.md:357`: *"when the blockchain starts, D₀,t|t=0 is very likely a small number
  compared to the target. Therefore, the equation above tilts towards 1."*

There is a reading that makes both coherent: the genesis rule seeds the *estimator*, which
then converges down to actual staked value. But the seed is what the chain launches with, and
it inverts the launch regime:

| reading | δ at genesis | `A_t` | block reward | service reward, 100 providers |
| --- | --- | --- | --- | --- |
| genesis rule, D = 10¹⁰ | −2.33 | **0.00** | 0.00335 LGO | **0.43 LGO/epoch** |
| bootstrap narrative, D = 10⁸ | +0.97 | **1.00** | 95.129 LGO | **12,329 LGO/epoch** |

**Four orders of magnitude, in every stream the block reward funds** — which is leader income
and service income both, so four of the five strategies. Under the genesis rule the chain
opens with *zero* minted emission and pure fee recycling, which is the exact opposite of the
bootstrap story and of the APY-attracts-validators argument the calibration rests on.

**Decided in favour of the genesis rule: `D` is seeded at 10^10.** The documents cannot settle
it, so it is a parameter, and this is the value chosen.

**It is far less alarming than the table suggests, because it is a transient.** The estimator
updates each epoch by the ratio of observed to expected block density
(`cryptarchia-total-stake-inference.md:59-83`; at the specified beta = 1 it collapses to
`D_ep = D_prev * N_BLOCKS / (PERIOD * f)`), reaching steady state after about **five epochs**
and recovering from massive shocks within two. So the chain opens on pure fee recycling for
roughly the first month and the emission factor then rises to one -- negligible against a
multi-year study, though the launch weeks produce very few blocks and very little reward, which
the simulator should reproduce rather than smooth away.

One standing consequence: the estimator is **biased low by construction**, converging to about
0.847 of true stake at f = 1/30 and 85% honest slot utilisation. A persistent underestimate of
stake is a persistent positive deviation, hence persistently *more* emission than intended.
That is a real-network property: the bias comes from missed slots and forks, which the
simulator's ideal chain does not have, so the simulator's estimator converges to true stake
and the extra late-era emission is recorded as a limitation rather than reproduced.

## 4.4 Service payout lag — e+2 or e−1

`bedrock-service-reward-distribution.md:49` and `blend-protocol.md:1136` (both Standards
Track) say the epoch-N reward is paid in the first block of **N+2**.
`overview-cryptoeconomics.md:228` (Informational) says e−1.

**Resolved: e+2**, by precedence, and the dissent is internal to an Informational overview
that elsewhere agrees with e+2.

## 4.5 Execution tips — all to leaders, or split 60/40

`overview-cryptoeconomics.md:171` (Informational) adds tips to `leader_rewards` *on top of*
the 40% share. `execution-market.md:62` (Standards Track): the priority fee *"is directed into
the block builders reward stream. 40% of the rewards will be allocated to block builders and
the remaining 60% to Blend nodes."*

**Resolved: tips are split 40/60**, by precedence and by the plainer reading — the tip enters
the stream *before* the split, not after it.

## 4.6 The split — per-block integers or per-epoch floats

`block-rewards.md:497-498` (Standards Track) floors each share per block.
`overview-cryptoeconomics.md:158-171` (Informational) sums float shares over the epoch.

**Resolved: per-block integer floors.** Over 21,600 blocks the two differ by up to ~21,600
units per pool.

**Still open, and genuinely unspecified:** the two floors do not sum to the total, and unlike
the leader pool and the PoW diversion, no document says where the residue goes. The simulator
must choose; it will retain it in the pool, matching the leader pool's stated treatment, and
say so.

## 4.7 Units — LGO or lepta

`bedrock-v1.1-mantle-specification.md:2119` states `TokenValue` counts lepta.
`block-rewards.md`'s reference implementation works in LGO — `STAKE_TARGET = int(3e9)` is
3 billion *LGO*, and `A_t'` adds `3e9 − D₀,t` to a burn sum, so both inputs must share that
unit.

**Resolved: not a contradiction but an unspecified boundary.** The block-reward function is
denominated in LGO; ledger quantities are lepta. **No conversion rule is stated anywhere.**
Feeding lepta into that function unchanged is wrong by 10⁹. The simulator converts at the
function boundary and gates the conversion.

## 4.8 Storage price floor — 1 LGO or 1 lepton

`storage-markets.md:224` (Standards Track): *"Rounding upwards makes 1 LGO per Permanent
Storage Gas the effective floor"*, in a document whose latest revision is 2026-07-28 and whose
own text sets `P_STR(0) = 1` — one *unit*.
`bedrock-v1.1-mantle-specification.md:2119`: the fee markets *"price in whole lepta per unit of
gas and can never go below one"*, and it **defers explicitly to *Logos Token: Units and
Precision***.

**Resolved: one lepton — and confirmed by the governing units document.**

This entry has been resolved twice and reversed once, so the evidence is set out in full.

*Logos Token: Units and Precision* (Standards Track, rev 1.0.0, **2026-08-11**) is the document
`mantle:2119` defers to by name for the unit system. It settles this on four independent
points. It tabulates `P_STR(s)` in **"LEPTA per Storage Gas unit"**. It states that the
execution base fee and the permanent storage price "are integers with an effective floor of
**one base unit** per gas unit". It computes the consequence itself: *"Storing one GiB
permanently costs at least 2^30 = 1,073,741,824 **LEPTA**, which is 1.0737 LOGOS."* And its
entire lower-bound derivation — the argument that fixes precision at `d = 9` — rests on that
floor, since it asks what precision keeps a GiB of storage under a target of a few dollars.

`storage-markets.md` was last revised **2026-07-28**, two weeks before the denomination was
fixed, so its "1 LGO per Permanent Storage Gas" is a figure from before there was a lepton to
state it in. `mantle:2119` says as much in general terms: *"amounts written in LGO here are a
display convenience for 10^9 lepta."*

**Why the reversal happened, and what it cost.** The middle resolution read
`storage-markets.md:112-126` closely, found the value stated with a full paragraph of economic
reasoning behind it, and concluded it was deliberate rather than presentational. That reading
of *that document* is right; the error was resolving a units question without consulting the
units document, which is both newer and explicitly deferred to. The check that would have
caught it immediately is arithmetic: at 1 LGO per byte a gigabyte costs 1.07 **billion** LOGOS,
a tenth of the entire supply, and `mantle:1858`'s own stated claim fee of 6,664 lepta becomes
unreproducible. At the resting price of 7 it reproduces exactly, as `(306 + 646) * 7`.

**The lasting consequence is not the number but the structure.** The two markets are charged on
different things — execution gas per Operation, permanent storage gas on the encoded size of
the whole signed transaction, one gas per byte (`mantle:71`, `mantle:148`) — and they discover
their prices independently. They happen to share a floor of one lepton and a resting level of
7, which is why a single-price model got the right answers. The simulator now prices them
separately regardless, so that a divergence between the two markets shows up rather than being
absorbed silently.

## 4.9 `S_TGE` — 10¹⁰ or 10⁸

`block-rewards.md:160` (Standards Track): 10 billion LGO.
`analysis-static-minimum-stake…:151` (Informational): assumes `S_TGE = S_max = 10⁸`.

**Resolved: 10¹⁰**, by precedence.

**Consequence, and it is serious:** the minimum stake was derived as 0.001% of `S_TGE` in the
analysis that assumed 10⁸, giving 1,000 LGO. At the governing supply the same rule gives
**100,000 LGO** — a hundredfold difference in the gate on the most valuable reward stream on
the chain. **The derivation of `min_stake` is invalid as it stands and needs redoing at the
correct supply.** The value itself is nonetheless SETTLED for this study: 1,000 LGO, fixed and
not a study axis (config.py records the decision and its rationale). What this entry keeps
alive is that the settled number rests on a derivation whose supply assumption is wrong by a
hundred — a defect to report upstream, not an open input.

## 4.10 `ServiceType` — `BN` or `BLEND`

`bedrock-service-declaration-protocol.md:80-82` defines `ServiceType.BN`;
`bedrock-genesis-block.md:102` constructs `ServiceType.BLEND`. Both Standards Track.

**Resolved: `BN`**, on the defining-document rule — the SDP defines the enum, the genesis
document consumes it. Not cosmetic: the service payout `op_id` is `hash(ServiceType || epoch)`.

## 4.11 The field modulus `p`

`bedrock-v1.1-mantle-specification.md:1634` points at *Common Cryptographic Components*, which
names BN254 but states no modulus. The only numeric value in the tree is at
`cryptarchia-proof-of-leadership.md:219`.

**Resolved: use the stated value** — a documentation gap rather than a contradiction. It is
the standard BN254 scalar field modulus and matches what this simulator already uses.

## 4.12 The block reward's recycled term — windowed or single-block (lips PR 375)

`block-rewards.md` 1.1.0 (PR 375, `pooling-distributing`, head `2b3b698` at the time of this
entry) changes the recycled term of the reward equation from the latest block's pooled fee to
the **moving average over the look-back window T** — a genuine mechanism change, motivated as
removing single-block volatility and the incentive to time transactions against one block.
The same PR's integer derivation and Rust reference still compute the single-block form; the
branch flags the section "**Rederivation required**" rather than fixing it, so the
specification's real-valued rule and its consensus-level reference implementation disagree
*within the same document*.

**Resolved: the windowed rule**, as the stated intent, with the PR's own prescription (reuse
the window sum already maintained for the pooling-rate KPI, divided by T). `emission.py`
implements it as `block_reward_lgo` and keeps the superseded form callable as
`block_reward_lgo_single_block`; the parity gate pins the divergence (a lone 12-LGO block in
a quiet window: 0.1 LGO windowed against 12 single-block) so the rederivation landing upstream
moves a gate here instead of passing silently. One boundary the specification leaves unstated
is decided here: pre-genesis window entries are zero, so a short history divides by the full
T. **No figure in these studies moves** — every run holds fees flat, where the two rules are
identical, and `A_t` saturates at 1 over every horizon anyway; pinned by the flat-window gate.

Side effect on 4.9: the PR removes `S_tge` entirely and anchors every constant to `S_cap`
(numerically the same 10¹⁰), which dissolves 4.9's *anchor* question — but not its
consequence, since the `min_stake` derivation assumed 10⁸ whatever the anchor is called.

## 4.13 Fee routing "in full" against the EmPoWering `POW_SHARE` — cross-RFC, decided

PR 375's `storage-markets.md` Fee Routing subsection routes each storage fee "**in full**"
into the pending rewards pool, `execution-market.md` routes the entire base fee likewise, and
the decomposition `R_block = R̂_STR + R̂_pooled` has no proof-of-work term. The EmPoWering
design diverts `POW_SHARE` (10%) of fees to the PoW pool. As written, the two specifications
cannot both be true on the day both merge.

**Decided by the design owner, 2026-08-24: the pool's routing stands, and EmPoWering carves
its share out of the pooled reward flow.** Fees enter the pending rewards pool in full — the
RFC's sentences stay true — and the PoW share is the pool's *first outflow*, taken from the
pooled flow before the reward rule distributes the remainder. Accounting consequences, all
implemented: the pool balance stays non-negative in every regime including `A_t = 0`, and the
de-novo `fee_bucket` becomes the EmPoWering-side view of a draw against the pending rewards
pool rather than an interception ahead of it.

**One sub-decision the first implementation buried, surfaced by the 2026-08-25 review.** The
carve-out leaves `R_block` ambiguous: the RFC defines it as the fees *routed to the pool*,
which under "in full" routing is **gross**, while `emission.py` feeds the window the **net**
figure — fees after the carve-out, which is what the pre-pooling code measured and what makes
the recycled term equal what is actually distributable. The alternative is defensible and
arguably more literal, since KPI-2 measures the *pooling rate*: the factor could read gross
while the recycled term distributes net. **Resolved: net**, and the cost of the choice is now
gated rather than assumed — identical at `A_t = 1` (fees do not enter a release-capped
reward, which is where every published figure sits), 0.0005% apart near the target, and
`1/(1 − pow_share)` = 11.1% apart only in the genesis-seed transient at `A_t = 0`, where the
absolute figure is ~0.0003 LGO a block. Nothing published moves either way; the entry exists
so the reading can be revisited on evidence rather than rediscovered. The remaining upstream ask is one sentence in the RFC
acknowledging the carve-out as a pool outflow, so "in full" and `POW_SHARE` stop reading as
a contradiction — drafted, with the other pending upstream items, in
`reports/EmPoWering/UPSTREAM-PENDING.md`.

---

## What changed, and what is still blocked

| # | resolution | changes a number here? |
| --- | --- | --- |
| 4.1 | leaders take 40%; APY 1.33% | yes — already applied and gated |
| 4.2 | `α_d = 1/4` | no — not yet modelled |
| **4.3** | **DECIDED: genesis rule, `D = 10¹⁰`** | a ~5-epoch launch transient; the 10⁴× gap is between readings at launch, not over the study |
| 4.4 | e+2 | no |
| 4.5 | tips split 40/60 | yes — leader income lower than assumed |
| 4.6 | per-block integer floors | marginal |
| 4.7 | convert at the function boundary | guards a 10⁹ error |
| 4.8 | one lepton | confirmed against *Units and Precision*, which is newer than `storage-markets.md` and deferred to by `mantle:2119` |
| 4.9 | `S_TGE = 10¹⁰` | **invalidates the `min_stake` derivation** |
| 4.10 | `BN` | no |
| 4.11 | use the stated modulus | no |
| 4.12 | windowed recycled term, per PR 375's stated intent | no — flat fees and `A_t = 1` make the rules coincide here; the divergence is gated |
| 4.13 | **DECIDED: carve-out from the pooled flow** | no — same value, new accounting; one upstream wording ask remains |

**Both items the documents could not supply are now decided as parameters:** `D` seeded at
10^10 per the genesis rule, and `min_stake` at 1,000 LGO per the static minimum stake analysis.
Neither is a reading of the specification -- both are choices, recorded here so any figure
resting on them traces to the decision rather than to a source.
