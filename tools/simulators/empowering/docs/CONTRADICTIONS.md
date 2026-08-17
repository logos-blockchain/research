# The eleven contradictions, resolved

The reward extraction found eleven places where the specifications disagree. Each is settled
below, with the rule used and the consequence. **Ten resolve. One does not, and it moves every
reward in the study by four orders of magnitude.**

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

## 4.3 `D` at genesis — **UNRESOLVED, and it is the load-bearing one**

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

This cannot be resolved from the documents. It is carried as a **configuration axis with no
default**, and no figure that depends on it may be quoted without stating which reading
produced it.

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
Storage Gas the effective floor"*, in a document whose latest revision is 2026-05-27 and whose
own text sets `P_STR(0) = 1` — one *unit*.
`bedrock-v1.1-mantle-specification.md:2119`: the fee markets *"price in whole lepta per unit of
gas and can never go below one"*, and it **defers explicitly to *Logos Token: Units and
Precision***.

**Resolved: one lepton.** Precedence would say otherwise, but the third rule applies: the
storage document's "1 LGO" is display wording from before the denomination was set, and the
Mantle text is reporting a governing units document rather than competing with it. A factor of
10⁹ that would otherwise have moved every fee in the model.

## 4.9 `S_TGE` — 10¹⁰ or 10⁸

`block-rewards.md:160` (Standards Track): 10 billion LGO.
`analysis-static-minimum-stake…:151` (Informational): assumes `S_TGE = S_max = 10⁸`.

**Resolved: 10¹⁰**, by precedence.

**Consequence, and it is serious:** the minimum stake was derived as 0.001% of `S_TGE` in the
analysis that assumed 10⁸, giving 1,000 LGO. At the governing supply the same rule gives
**100,000 LGO** — a hundredfold difference in the gate on the most valuable reward stream on
the chain. **The derivation of `min_stake` is invalid as it stands and needs redoing at the
correct supply.** Since the specification leaves `min_stake.stake_threshold` UNSET in any case,
the simulator carries it as a sweep axis and this is why.

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

---

## What changed, and what is still blocked

| # | resolution | changes a number here? |
| --- | --- | --- |
| 4.1 | leaders take 40%; APY 1.33% | yes — already applied and gated |
| 4.2 | `α_d = 1/4` | no — not yet modelled |
| **4.3** | **unresolved** | **yes — 10⁴× on four of five strategies** |
| 4.4 | e+2 | no |
| 4.5 | tips split 40/60 | yes — leader income lower than assumed |
| 4.6 | per-block integer floors | marginal |
| 4.7 | convert at the function boundary | guards a 10⁹ error |
| 4.8 | one lepton | confirms the fee model already in use |
| 4.9 | `S_TGE = 10¹⁰` | **invalidates the `min_stake` derivation** |
| 4.10 | `BN` | no |
| 4.11 | use the stated modulus | no |

**Two items need a decision that the documents cannot supply:** the genesis value of `D`
(4.3), and what `min_stake` should be once redone at the governing supply (4.9). Both gate the
strategy study; the first gates every number in it.
