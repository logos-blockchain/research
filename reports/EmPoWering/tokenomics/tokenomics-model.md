# EmPoWering — tokenomics model, closed-form results, and simulations

## What this document is

> **Location.** This report lives in `reports/EmPoWering/tokenomics/`; the simulations backing it live in `simulations/EmPoWering/` and regenerate every current number via `make all` (and `make verify`, `make check LIPS=…`). The report was authored alongside logos-lips PR #400 and moved here when that work closed.

## How to read this — and a warning about its shape

*In plain words: this document works out the numbers behind the on-ramp — how big the launch fund should be, what one piece of mining work should pay, and whether the whole thing can eventually pay for itself out of ordinary transaction fees. It is the most technical document in the set, and it is **not** the place to start.*

**Where to start instead.** For the mechanism explained from scratch with no arithmetic, read `reports/EmPoWering/denovo/design-comparison.md` §0. For the decision and the recommendation, read `reports/EmPoWering/denovo/SUMMARY.md`. Come here when you need a specific number and want to see how it was derived.

**The shape is unusual, and knowing that saves confusion.** This document grew by addendum rather than rewrite, so that its corrections stay auditable:

- **§§0.0–0.5 are addenda, newest first.** Each records a decision that landed *after* the body was written and says which of the body's conclusions it changes. **Read §0.5 first** — it is the most recent, and it states which parts of everything below still stand.
- **The body (Backgrounds A–C, then §§1–9) is the original analysis.** Where an addendum contradicts it, the addendum wins; the body is kept as the record of what was derived when.
- **§§4.5 and 4.6 sit at the very end, after §9**, out of numerical order. That is an artefact of how they were added, not a hint about their importance.
- **Line references to the specifications** (`block-rewards.md:206` and the like) point at the revision the analysis was derived against, and will drift as those documents change. They are provenance, not live links.

**If you are new to this, read in this order:** Background A (what the mechanism is) → Background C (the glossary) → the Epistemic legend (which tells you how much to trust each number) → §0.5 → then whichever numbered section holds the figure you came for.

**The epistemic legend matters more than usual here.** Section headings carry tags — `DERIVED`, `SIMULATED`, `OPEN` — that say whether a result is arithmetic, a measurement, or an unresolved question. A `DERIVED` figure is as reliable as its inputs; a `SIMULATED` one carries the assumptions of the run; an `OPEN` one is a question, not an answer. The legend at §"Epistemic legend" defines them precisely, and skipping it makes the rest look more settled than it is.

## 0.5 Addendum — the substrate moves to pooling/distributing/releasing (lips PR 375; 2026-08-24, latest)

Lips PR 375 (`block-rewards.md` 1.1.0, with `execution-market.md`, `storage-markets.md` and the overview propagating; open, one research approval in, planned against head `2b3b698`) replaces the burn/mint substrate this document was written on: fees route **in full into a pending rewards pool** instead of burning, rewards **distribute from that pool topped up by a metered release** from a finite genesis reserve (`B_0 = I_max·S_cap·Y = 10⁹ LGO`, `Y = 10` years) instead of minting, the recycled term becomes the **windowed average** of pooled fees over `T = 120` blocks instead of the latest block's, `S_tge` is removed in favour of the hard cap `S_cap` (numerically identical at 10¹⁰), and the three stocks conserve: `ΔS + ΔP + ΔB = 0`.

**This document is not rewritten under it, and deliberately** — its sections cite `master`'s text and line numbers verbatim and carry their own correction history, which a sweep would destroy. Instead this addendum states the translation once, and what survives it:

- **Read every "burnt/burned/destroyed" below as "routed to the pending rewards pool": removed from *circulation*, not from existence.** Every argument in this document that runs on fees leaving circulation survives unchanged, because pooling removes them from circulation exactly as burning did; what changes is that the removal is banked and reversible rather than final.
- **§3.4 and §4.4.2 survive with their conclusion re-founded.** The two-regime answer to *who pays* is intact: at `A_t → 1` the diversion is borne by the supply side — now "circulating supply contracts less than it would have" rather than "less is destroyed" — and at `A_t → 0` it comes out of Blend and leader distribution one for one, exactly as written. The sentence "mining slows the deflation rather than adding to inflation" becomes "mining slows the circulating-supply contraction rather than adding release", and §3.4 still comes out clean.
- **The ratio arguments are untouched.** `reward_over_fee`, the builder edge, the break-even load, the claim-share ceiling and the subordination cap all compare quantities on the same fee flow, which PR 375 reroutes without resizing — the fee-computation formulas of both markets are explicitly unchanged.
- **The `pow_share` funding question of §4.4.2 gains a decided answer.** PR 375's routing says fees enter the pool "in full", which contradicted the diversion as specified; **decided 2026-08-24: the pool's routing stands and the EmPoWering share is the pool's first outflow** — a carve-out from the pooled reward flow, same magnitude, recorded with its accounting consequences as contradiction 4.13 in the strategy simulator's `CONTRADICTIONS.md`. §1.5 of the EmPoWering RFC itself already describes fee funding in pooling terms ("fees are not burned, and rewards are not minted out of thin air"), so the two RFCs agree in direction; PR 375 supplies the general machinery that prose gestures at.
- **One mechanism change is real but out of this document's scope**: the windowed recycled term alters the block reward only when `A_t < 1` *and* fees vary within the hour, a regime none of this document's results occupy. It is implemented and gated in the strategy simulator (`emission.py`, contradiction 4.12 for the PR's own real/integer divergence).
- **Line citations** such as `block-rewards.md:206` ("burned when the block is proposed") and `:178` are to `master` = 1.0.0 and will drift when the PR merges; they are left as the record of what this document was derived against.

**What "in sync" covers, precisely.** The *reward rule* is implemented and exercised by the simulations themselves — every published figure runs through it. The *stock accounting* (`P_t`, `B_t`, the conservation identity, the depletion fallback) is implemented and gated but **not carried through a simulation run**: no study here tracks the pool and reserve block by block, because the reserve outlives every horizon these documents model by construction (`B_0` funds the release cap for exactly 10 years, and nothing here runs that long at `A_t = 1`). So the stocks are checked for fidelity to the RFC, not integrated into results — a boundary worth stating rather than leaving to be discovered.

The claim "in sync" is checked, not asserted: `make check` now passes against **both** trees — the EmPoWering RFC baseline (42 checks) and that baseline with PR 375's `block-rewards.md` overlaid (43 checks, the added one pinning the reserve lifetime `Y = 10`) — so whichever merges first, drift lands as a gate failure here rather than as stale prose.

## 0.4 Addendum — `EPOCH_POW_DISTRIBUTION_RATE` moves to 1/200 (2026-08-14)

The specification adopts **`distribution_rate` = 1/200** (was 1/100), on this document's own analysis; every other constant stands. The selection criterion was robustness at unchanged economics, and the candidates were the two routes §4.11 identified: (T, `pow_share`) = (11, 11 %) and `distribution_rate` = 1/200. The second dominates:

- **It closes §3.8's within-epoch drain by construction** — 2,000 claims per block against a `MAX_BLOCK_TXS` of 1,024 — and stays closed up to a doubling of block capacity, where the (11, 11 %) route reopens at 1,101. What was the one controller-dependent guarantee in the design is now structural.
- **It improves bootstrap security**: the same endowment distributes at half the rate, so the peak adversarial stake share falls from 0.51 % to **0.42 %** (`adversary_hashrate = 0.33`, `initial_stake = 30 %`), and the opening over-payment halves (`opening_reward` = 173,681× the fee, was 347,361×).
- **It spends no live margin**: `reward_over_fee` = 5.02, the builder edge, the break-even load and the claim-share ceiling are all `distribution_rate`-free; `pow_share` stays at 10 %, keeping the subordination headroom and no reliance on the unset leader share; `target_claims_per_block` stays at 10, keeping every §4.4.1 argument.
- **Its one cost is the response lag**, 2.1 → 4.1 years — and the lag binds only once the pool is fee-funded, which at the specified endowment and resting prices is ~43 years out (§4.7.1). The spec's other two stated costs of a smaller `distribution_rate` (reserve and floor, once ~1 % of supply) were voided by the Units decision: both are now ~10⁻⁷ of supply at either value.

Consequences worth naming: the pool's half-life is 138 epochs ≈ 2.8 years (was 69 ≈ 1.4); the reserve `steady_pool` is 1,446 LGO and the floor `pool_floor` 288; the descent to the fee-funded regime takes ~43 years at the resting price (0.3 at the deflation threshold); the endowment sustains claiming for ~49 years with no traffic at all; and §4.11's window becomes (5.12, 11.76], which **contains the specified T = 10** — the (11, 11 %) observation is discharged rather than adopted. Figures in §§0.0–0.3 are at the pre-change 1/100 and are kept as the historical record.

## 0.3 Addendum — three conclusions the Units decision inverted (2026-08-13; figures herein at the then-specified `distribution_rate` = 1/100)

§0.1 settled the denomination at 1 LOGOS = 10⁹ lepta. That moved `claim_fee`, and with it the pool's fixed point `steady_pool = pow_share * blocks_per_epoch * txs_per_block * avg_tx_fee/distribution_rate`, down by six orders of magnitude — while `genesis_pool` stayed a fraction of *supply* and did not move at all. §0.1 records the immediate consequence in one line ("at floor prices `genesis_pool` vastly exceeds `steady_pool` and the reward decays from a generous opening"). **This addendum works out what that does to three sections whose conclusions were computed when `genesis_pool` sat at the fixed point.** All three now say the opposite of what the model gives. The mechanism is unchanged; only the parameter set moved beneath them.

`genesis_pool/steady_pool = 69,153` at the resting price, against the `genesis_pool ≈ steady_pool` §3.7 assumes.

**§3.7's worked example is superseded.** Its conclusion — "no decay, no stranded residual worth remarking on, and a per-claim reward the same in year ten as in week one" — held when the endowment was sized at the fixed point. It is not:

| epoch | years | $\sigma_e$ (lepta) | × fee |
| --- | --- | --- | --- |
| 0 | 0.00 | 2,314,814,815 | 347,361× |
| 100 | 2.05 | 847,318,308 | 127,149× |
| 299 | 6.14 | 114,699,077 | 17,212× |
| 973 | 19.99 | 164,559 | 24.7× |
| 1460 | 30.00 | 34,456 | 5.17× |
| ∞ | — | 33,474 | **5.02×** |

The reward opens at 347,361× the fee and decays to 5.02×, reaching within a factor of two of the fixed point after about 23 years (§4.7.1, which also shows the descent is a property of the *price level* — 2.3 years at the deflation-threshold price — rather than of the mechanism). §3.7's structural results are untouched and still hold: `target_claims_per_block` and `blocks_per_epoch` vanish from the pool dynamics, `steady_reward` contains no `distribution_rate`, and `distribution_rate` sets the speed and never the destination.

**§4.2's builder-edge shape is inverted.** §4.2(c) reasons that the endowment "sits below" the fixed point, so the reward climbs and the edge *falls* — 1.349× at launch to 1.124× at steady state — concluding that "the worst moment is therefore the first epoch" and that this "improves rather than degrades as the network matures". With `genesis_pool` above the fixed point the reward falls and the edge **rises**:

| | $\sigma_e/\varphi$ | builder edge |
| --- | --- | --- |
| launch | 347,361× | **1.0000×** |
| 10 years | 2,632× | 1.0002× |
| 20 years | 24.7× | 1.0211× |
| 30 years | 5.2× | 1.1199× |
| steady state | 5.02× | **1.1243×** |

**The worst moment is the steady state, not the first epoch**, and the shape is the slow-onset one §4.2 credits fee funding with removing. What does *not* change is the magnitude: the edge is bounded by 1.124× on either reading, because that bound is set by `reward_over_fee`, which the denomination decision left alone. So this is a correction to when the advantage peaks and to §4.2's comparative argument, not to how large it gets. §4.2(a) and (b) are unaffected — the reward pays a key the builder does not hold, and at 1 % of block capacity censorship still buys nothing.

**§4.1's security figures move down by a factor of two to five.** The pool distributes **0.48 %** of supply over 6.1 years, not the 2.59 % §4.1 carried, and every cell of its table moved with it (§4.1 is now corrected in place):

| `initial_stake` (% of supply) | h=0.10 | h=0.33 | h=0.50 |
| --- | --- | --- | --- |
| **0.5 %** | 4.9–6.2 % | 16.1–19.2 % | 24.4–27.7 % |
| **5 %** | 0.9 % | 2.9–3.0 % | 4.3–4.4 % |
| **30 %** (the staking target) | 0.2 % | 0.5 % | 0.8 % |

(ranges span honest miners staking 100 % vs 50 % of winnings)

The direction is favourable, and one specific warning lapses with it: §4.1 says that at `initial_stake = 0.5 %` a one-third attacker "exceeds the safety threshold" within six years if honest miners stake only half their winnings. At 19.2 % it does not, and no cell in the table now crosses one third at that horizon. **§4.1's qualitative argument is otherwise unaffected**: the refill never stops, so these remain six-year figures rather than lifetime ones, and the asymptote `adversary_hashrate / (adversary_hashrate + (1 - adversary_hashrate) * honest_stake_frac)` contains no parameter that moved — it is still 33 % at `adversary_hashrate = 0.33` with full honest staking, and still the artefact of fixed `initial_stake` that §4.1 correctly names.

**§4.4.3's reserve column is stale in the same way.** Its table priced the standing reserve and the endowment floor as fractions of supply — 1.03 % and 0.21 % at the specified `distribution_rate` — which were `steady_pool / launch_supply` and `pool_floor / launch_supply` computed before the denomination moved (§4.4.3 is now corrected in place). The model now gives **7.23×10⁻⁶ %** and **1.44×10⁻⁶ %**: the reserve is 723 LGO and the floor 144 LGO, not a hundredth of the supply. The `distribution_rate` *comparison* the table exists to make is unaffected, because all three quantities go as `1 / distribution_rate` and the ratios between rows are unchanged; what has moved is only their absolute scale. The drain column is correct as written — the hard edge at `distribution_rate < target_claims_per_block / MAX_BLOCK_TXS = 0.977 %` is denomination-free, and `distribution_rate = 1 %` does sit on the reachable side of it.

**Why this was not caught by the gates.** `make check` ties the config to the specification and `make verify` ties the model to its closed forms; nothing tied this document's prose to either. The three sections above were arithmetically correct for the parameter set they were run against and simply went stale in place. A `report-numbers` gate — regenerating every quoted figure from the model, as the Blend report does — is the fix, and is not yet built.

## 0.0 Addendum — the nonce-based PoW branch, circuit v0.5.6 (2026-08-12)

Implementation PR #3305 replaces the Blend puzzle's secret key and key derivation with a single private **`pow_nonce`**, and gives the ticket its own domain separation tag: `ticket = zkhash(BLEND_POW_V1, pol_epoch_nonce, pow_nonce)`. The specifications now match circuit v0.5.6. Consequences for this report:

- **The "no DST" caveat the body records is withdrawn** — the implementation added the tag, resolving the shared-hash-domain concern in the direction the body flagged.
- **The Blend candidate is one 3-input hash**: measured 14.9 μs naive / 8.2 μs with the constant `(dst, epoch_nonce)` prefix precomputed — an algorithmic edge of **1.81×** (was 1.40×), since the constant prefix is now half the naive work. Re-deriving `BLEND_DIFFICULTY_BASE` at the cheaper candidate **leaves `p/2²²` in place**: 62 s of one M4 core per message, ~1,400 messages a day, still 4–8× slower on the Pi 5 pending its measurement.
- **The reward candidate now costs more than the Blend candidate** (26.6 μs — the claim's ticket keeps its key, since the note must pay to a public key): the two paths' work costs have formally diverged, and §4.5/§4.6 figures split accordingly (`make blend` vs `make exhaustion`).
- **The Pi 5 measurement is in, and the threshold is calibrated on it.** Six runs on the target board (spreads ≤ 0.1 %, no throttling): a blend candidate costs 94.2 μs — 6.3× the desktop figure, inside the 4–8× band the model carried as an estimate. The reference basis is decided as **one core of the target**, and `BLEND_DIFFICULTY_BASE` moves `p/2²²` → **`p/2¹⁹`**: ~50 s and ~1,750 messages/day per core, 4× on the board, optimiser's edge 1.94×. §4.5's every remaining estimate is thereby replaced by measurement. The genesis reward target keeps `p/2²⁶` (a seed, not a price), now ~3 hours per solution and ~3,700 target-cores at the target rate.
- **Review round one** (logos-lips PR #400): the nullifier cache is written only after proof verification — deduplication reads it but never populates it, closing a poisoning race the review found. And `difficulty_blend` for an epoch is fixed at the same snapshot as that epoch's nonce, during the epoch before it, from the load of the epoch before that — one further epoch of controller lag, absorbed by the clamp, in exchange for the precomputation window having every public input. Epochs 0–1 use the base value.
- `PowTarget` arithmetic is now normatively defined over **canonical integer representatives** — no field division or modular wraparound anywhere in the controllers — with both results capped below `field_modulus`.

## 0.1 Addendum — Units and Precision (2026-08-12, superseding §0.2 below)

The *Logos Token: Units and Precision* specification settles the unit system, and it settles it the other way from the interim position §0.2 records: **the indivisible unit is the lepton, with 1 LOGOS = 10⁹ lepta (`decimals = 9`), and the supply stays at the original 10¹⁰.** The precision is the unique value admitted by representability above (10¹⁹ lepta against `uint64`'s 1.84×10¹⁹) and price resolution below (a coarser unit prices permanent storage above a \$5/GiB target inside the plausible token-price range; the derivation saturates at \$4.66 per LOGOS).

What this undoes and what it restores:

- **The supply resize is withdrawn** — `block-rewards.md` is back at its published form. The resize's justification assumed one LGO was indivisible, which made the fee floor overwhelm the emission cap; with the floor at one *lepton* the original supply works, and the deflationary phase is reached through ordinary price discovery (a full block's burn matches the emission cap at ~116,562 lepta/gas, 16,652× the resting level and far under #393's `MAX_PRICE`).
- **§0.2's trajectory-inversion bullet is void with it.** `genesis_pool` vs `steady_pool` again depends on the discovered price level: at floor prices `genesis_pool` vastly exceeds `steady_pool` and the reward decays from a generous opening, which is the body's original qualitative picture.
- **The body's price-level framing is vindicated.** §4.4.4's correction — that the endowment turns on the *price level*, not the denomination — was right, and is now the operative frame: `claim_fee` at the resting floor is 6,664 lepta ≈ 6.7×10⁻⁶ LGO, under 10⁻¹⁵ of supply, and the genesis fee ceiling of `1.157×10⁻¹⁰` of supply (unchanged, having been stated supply-relative) binds only if discovered prices rise about five orders of magnitude above the floor.
- **Every ratio stands, again**: `fee_ratio` = 0.837, `reward_over_fee` = 5.02 at reference traffic, the 1.124× builder edge, `target_claims_per_block`↔`pow_share`, the 1,000-claims drain margin, the 5.75×10⁻⁵-of-pool genesis-error cost. The whole calibration of §§4.4.1–4.4.3 is untouched.
- The open policy question sharpens into the Units doc's own terms: the storage floor exceeds \$5/GiB once LOGOS trades above **\$4.66**, and no admissible precision fixes that — the remedy lies in the Permanent Storage Gas unit, outside this proposal.

`make all` in `simulations/EmPoWering/` regenerates everything at `decimals = 9`, printing lepta as the primary unit, and `make lepta` confirms the mechanism at lepton granularity in exact integer arithmetic — conservation to the lepton, checked `uint64` throughout, the `reward_per_claim` cliff at its exact boundary, and the canonical parse/format round-trip — something the float engine structurally cannot do. **Terminology**: where the body says "base units", read *lepta*; where it prices in LGO, the figures are pre-resize/pre-lepton absolutes superseded per §0.2 and this section.

## 0.2 Addendum — the TGE supply resize (2026-08-11, superseded by §0.1 above)

After this report reached its present form, the analysis it contains led to one further specification change that **supersedes every LGO-denominated figure in the body**: `launch_supply` was raised from 10¹⁰ to **3×10¹⁴ LGO**, sized so that the emission model's deflationary phase begins exactly at the fee market's target utilisation (see `block-rewards.md`, *Sizing the TGE supply*). One LGO is the smallest representable amount — the divisibility question §4.4.4 carries is thereby resolved the other way, by scaling the supply rather than subdividing the token.

Consequences for reading this document:

- **Every ratio stands.** `fee_ratio` = 0.837, `reward_over_fee` = 5.02 at the reference traffic, the 1.124× builder edge, the `target_claims_per_block`↔`pow_share` trade, the fee-overhead identity, the stopping conditions, and every argument built on them are supply-free and unchanged.
- **The fee is now determined, not assumed.** The body treats `claim_fee` = 0.952 LGO as a price-level assumption (§5.1). It is now `(306 + 646) × 7 = 6,664 LGO` at the resting price — a consequence of the fee schedule and the indivisible LGO, with no free parameter left.
- **Supply-relative figures scale by ×0.233** (`claim_fee`/S fell from 9.52×10⁻¹¹ to 2.22×10⁻¹¹): `pool_floor` 0.206 % → **0.048 %**, `steady_pool` 1.03 % → **0.241 %**, the 5-year ramp 0.34 % → **0.080 %**, the 10-year ramp 0.60 % → **0.140 %** of supply.
- **The specified `genesis_pool = 0.5 %` now opens at 10.4× the fee** (was 2.4×) and covers the 10-year ramp several times over. It is over-provisioned by about 4×; reducing it toward 0.2 % is an open token-allocation question, not a viability one.
- `make all` in `simulations/EmPoWering/` prints all of the above from `configs/specified.toml`.
- The resize also closes items the body leaves open: §4.4.4's denomination question is settled (one LGO is the smallest unit, workable at the sized supply), and §10's "launch fee level" ceiling is now met with a factor of five in hand rather than being a target for governance to hit. §10.2's standing-reserve question is now about a reserve of ~0.24 % of supply at the reference traffic, not ~1 %.
- **The trajectory direction in §3.7 and §4.2 is inverted at the current parameters.** Those sections describe the endowment sitting *below* the pool's fixed point, the reward climbing, and the builder edge shrinking — so the worst moment for self-dealing was the first epoch. After the resize, `genesis_pool` (0.5 % of supply) sits *above* `steady_pool` (0.241 % at the reference traffic): the reward **decays** from 10.4× the fee toward 5.0×, and the edge **grows** from 1.05× toward 1.12×. Both endpoints are comfortably inside the design margins, but the qualitative conclusion flips — the worst moment for self-dealing is the steady state again, at a still-benign 1.124×, and the open allocation question (trimming `genesis_pool` toward `steady_pool`) would flatten the trajectory rather than raise it.

The body below is retained as written, including its §4.4.4 treatment of the denomination as an open question, because the reasoning there is what produced the resolution.

---

EmPoWering lets someone earn their first Logos tokens by mining — running a computer to solve a puzzle — instead of buying them. This document works out the economics: how much a miner earns, how that changes over time, whether the scheme is stable, and whether an attacker could mine their way to dangerous influence over the network.

**Self-contained.** Background A–C describe the mechanism, its funding, and the vocabulary, so this can be read without the specification tree to hand.

**Measured, not assumed — but on the wrong machine.** `bench-poseidon2/` times the real Poseidon2 crate, so §4.5's Blend threshold rests on a measurement rather than an estimate. It was taken on an Apple M4 Pro; deployment targets a Raspberry Pi 5, several times slower per core, and the threshold should be re-derived once it has been run there.

**Sequencing.** This proposal merges *after* the in-flight fee-market change, so that change's findings are treated as the baseline here — in particular the resting price of 7 used throughout §4.3. The two touch no file in common.

**Sync is checked, not asserted.** `make check LIPS=<path-to-logos-lips>` in `simulations/EmPoWering/` reads the constants back out of the specification tree — and recomputes the derived margins the specifications state in prose — comparing both against the config the simulations run from; it exits non-zero on any drift. Run it after every specification change.

**In sync with PR #400** as of 2026-08-12, at commit `85ece929`. Where the specification has been decided since the proposal was written, this document follows the specification — the differences are listed in *What changed since the proposal* below.

**Headline results.** Of the eight economic questions the proposal's §2.3 says must be answered, **seven have answers**: items 1, 2, 5 and 6 in closed form (§3), items 3, 4 and 7 by simulation and derivation (§3.5, §4.1, §4.2). Item 8, difficulty decoupling, is settled by the specification's construction rather than by analysis and is not modelled here. §4.4 additionally sizes the genesis endowment, which the proposal leaves `TBD`.

**The condition self-funding turns on** is a transaction count, not a price. The pool is refilled from a share of the fees a block collects, and the fee a claim pays is set by the same prices, so those prices appear on both sides of the comparison and cancel: a claim pays for itself iff `txs_per_block > target_claims_per_block / (fee_ratio * pow_share)`, where `fee_ratio` ≈ 0.837 is the average transaction's fee over a claim's (§4.3). At the specified `target_claims_per_block = 10` that needs about 120 transactions per block at a 10 % share, or 60 at 20 %, comfortably inside what a block can carry at every share worth considering. Before that point the genesis endowment carries the reward.

**The endowment reduces to one unknown, and it is not the one it looked like.** `genesis_pool / launch_supply = opening_multiple * (claim_fee / launch_supply) * target_claims_per_block * blocks_per_epoch / distribution_rate` — everything but the claim fee as a fraction of supply is fixed by the specification. That fraction turns on the **price level the fee markets are initialised at**, not on the denomination, which §4.4.4 separates out after an earlier revision of this document conflated them. `genesis_pool` is specified at **0.5 % of the launch supply**, and the constraint it hands to genesis governance is a ceiling on the launch fee of **`1.157×10⁻¹⁰` of supply — about 34,700 LGO at the sized supply** — for the opening reward to be twice it; the fee markets' resting prices meet it with a factor of five in hand.

**The claim target is overhead, not throughput.** Each claim pays a fee out of its own reward, so an epoch delivers `blocks_per_epoch * claim_fee * (fee_ratio * pow_share * txs_per_block - target_claims_per_block)` net — `target_claims_per_block` enters with a minus sign. At the earlier `target_claims_per_block = 50` half of everything the pool distributed was returned as fees on the claims themselves. `target_claims_per_block = 10` cuts that to a tenth at the same share, and §4.4.1 works through why the intuition that a higher target onboards more people is backwards.

## What changed since the proposal

The specification has moved. This document models the specification, not the proposal text, and these are the differences that bear on economics:

| | Proposal | Specification (PR #400) |
| --- | --- | --- |
| Claim acceptance window | `WINDOW` slots, TBD | `claim_window_blocks / block_rate` — **10 blocks ≈ 300 slots**, derived from the block rate |
| Epoch nonce accepted | current **or previous** epoch | **current only** |
| Pool arithmetic | unstated | **checked** — must not saturate |
| Pool funding | **the proposal says both** — see below | **a share of the fees collected**, diverted from the burn |
| Genesis per-claim reward | separate constant | **derived** from the seeded pool |
| Blend quota | `pow_quota`, 20-bit, TBD | **$Q_W$ = `blend_ops_per_message`** — one solution buys one message |
| Target claim rate | `target_claims_per_block = 10` (code ships 100) | **`target_claims_per_block = 10`** — agrees with the proposal; §4.4.1 gives the reasoning |

**The funding source is the one place the proposal contradicts itself**, and it is worth setting out because the specification had to pick a side.

Its prose section §1.5 describes fee funding: *"the pool is replenished from transaction fees. Fees are not burned, and rewards are not minted out of thin air. Instead, transaction fees are tracked in a separate accounting system outside the UTXO ledger and distributed across the network's reward pools — the Blend reward pool, the PoS reward pool, and the PoW reward pool. A fixed slice of that flow tops up the PoW pool each epoch."*

Its normative section §5.8 describes something else — a three-way split of the **block reward**, with `block_reward_blend_share + block_reward_leader_share + block_reward_pow_share = 1` and `distribute_block_reward(block)` taking `reward = get_block_rewards(block)`, illustrated at 59/39/2 of 100.

These are not the same mechanism. A share of the block reward is bounded by the emission cap; a slice of the fee flow is not. §4.3 shows the difference decides whether a claim can ever pay its own fee. **The specification follows §1.5**, and §5.8's construction is not adopted.

Only the first four and the last touch this model. `blend_ops_per_message` governs Blend admission, not minting, so it does not enter the reward economics; it is noted because it was an open item and is now closed.

The target claim rate remains an **absolute count per block**, as in both the proposal and the implementation. A transaction-relative alternative is analysed in §4.3 and carried in §9; it is not part of the base.

## Epistemic legend

Every parameter, equation and result carries one of these tags, because several headline results are exact consequences of assumptions that have never been tested. **§8 consolidates everything that is not `KNOWN`.**

| Tag | Meaning |
| --- | --- |
| **`KNOWN`** | Read from the specification or the merged code, with a citation. Not in dispute. |
| **`DERIVED`** | Mathematics applied to `KNOWN` facts and `ASSUMED` models. Check the algebra, not the world. |
| **`ASSUMED`** | A modelling choice made here, not stated by the specification. §2.6 explains each and what would falsify it. |
| **`SIMULATED`** | Established by a run in §4, conditional on the assumptions it declares. |
| **`UNKNOWN`** | A quantity nobody has determined. Not a disagreement; a hole. |
| **`OPEN`** | A decision the project must make. |

## Background A — the mechanism being modelled

EmPoWering adds proof of work in two roles. Only the second has economics.

**Blend admission (no economics).** Logos routes messages through a privacy layer that hides who sent what. To send, you attach a proof that you are entitled to. Before EmPoWering there were two ways to qualify: be an established node with locked stake, or be a block proposer. EmPoWering adds a third: show you did computational work. **No tokens are created on this path.** It appears here only because it competes for the same hardware.

**Token minting (the economics).** A new operation, `CLAIM_POW_REWARD`, pays a miner from a pool:

1. **A pool is created.** At launch, `POW_REWARD_POOL_GENESIS` tokens are set aside — *existing* tokens from the initial distribution, not newly printed. This is what keeps the scheme outside the inflation envelope (§3.4).
2. **A fixed price per win is set, once per epoch.** An epoch is 7.5 days. At its start the protocol computes `reward_per_claim`, the amount every winner receives during that epoch. Holding it fixed is not a convenience — it is what lets a wallet compute the reward note's identifier *before* the transaction is mined, which is what makes step 5 possible.
3. **Miners grind.** A miner hashes candidate keys until one lands below the difficulty target. Guess-and-check, which is the point: it costs electricity.
4. **A winner submits a claim.** The credential goes on-chain carrying no signature and no proof — **the work is the authorisation**. The network checks the pool can cover it, the anchoring block is recent and canonical, the epoch nonce is current, the ticket clears the threshold, and nobody has claimed it before.
5. **The reward pays its own fee.** Every transaction costs a fee, so normally you need tokens before you can act — a chicken-and-egg problem for a new user. Here the transaction says, in effect: *mint me `reward_per_claim`, and here is me spending some of it to pay for this transaction*. The user starts with nothing.
6. **The pool drains and refills.** Each payout shrinks it; each epoch boundary tops it up with a share of the fees the epoch's transactions paid — fees that would otherwise have been burnt — and recomputes `reward_per_claim`.
7. **Difficulty retargets every block**, aiming for a steady claim count regardless of how many miners appear.

## Background B — where the money comes from

The refill `F` is the most important quantity here: §3.1 shows the long-run reward depends on it alone.

Every transaction pays two fees — one for the bytes it stores forever, one for the computation it costs — and both are normally burnt. EmPoWering diverts a fixed share `pow_share` of that flow into the mining pool before it is burnt. So

| **the epoch refill** |
| --- |
| $F = \beta\cdot N_b\cdot n_\text{tx}\cdot \bar{\varphi}$ |
| `epoch_refill = pow_share * blocks_per_epoch * txs_per_block * avg_tx_fee` |
for `blocks_per_epoch` blocks in an epoch, `txs_per_block` transactions in a block and `avg_tx_fee` the average fee one pays. **Nothing in that expression is the block reward**, and nothing in it involves the protocol's emission controller. That is the point of the choice, and it is worth spelling out why the alternative fails.

The block reward is capped: the protocol will not mint faster than `I_max` a year, which works out at `62500/657 ≈ 95.13` LGO per block. Fees are not capped — they rise with congestion, without limit. Had the pool been funded from a share of the block reward, the reward per claim would have sat near a fixed ceiling however busy the network became, while the fee a claim itself must pay kept climbing. Past some level of usage a claim would cost more than it pays, and the mechanism would switch itself off precisely when the network was most valuable to join. Funding from the fee flow puts the same quantity on both sides, so their ratio depends on the parameters rather than on how busy the day is.

**It also takes the emission controller out of the model entirely.** An earlier revision had to carry a dial `A_t` — the protocol's blend of freshly minted tokens and recycled fees — through every comparison, and could not close the endowment question because the dial's trajectory is exogenous. Under fee funding that dependence is gone; `A_t` appears nowhere below.

The cost is borne by the burn, not by issuance: the tokens the pool distributes were paid as fees and were on their way to destruction. Mining therefore slows the deflation rather than adding to inflation, which is why §3.4 comes out clean.

## Background C — glossary

| Term | Meaning |
| --- | --- |
| **slot** | One second. |
| **block** | Produced in ~1 slot in 30, so ~30 s apart. |
| **epoch** | 648,000 slots = **7.5 days** ≈ 21,600 blocks. |
| **note** | A coin: a value and an owner. Minting a reward creates one. |
| **claim** | One successful payout; mints exactly $\sigma_e$. |
| **ticket** | The puzzle output. You win if it comes out small enough. |
| **difficulty / target** | The threshold a ticket must fall below. **Smaller = harder.** Win chance is target ÷ number-space. |
| **pool** | The reserve claims are paid from. |
| **refill** | The top-up the pool gets each epoch boundary. |
| **base unit** | Smallest representable amount. Undefined tree-wide — see §5.1. |

## 0. A warning about the letter T

The proposal and `block-rewards.md` both use **`target_claims_per_block`** for different things. Here: `target_claims_per_block` is the target claims **per block**; `W` is the fee-average look-back window (120 blocks), which `block-rewards.md` calls `target_claims_per_block`.

## 1. Parameters

### 1.0 Notation

Prose and code spans in this document use **self-describing names**; equations use the conventional **symbols**, because a formula wants short ones. The two are strictly interchangeable — every symbol below has exactly one name and every name exactly one symbol — and neither form ever appears in the other's place. Concretely: a backtick span holds only names, never a symbol; a symbol appears only inside math; prose names a quantity rather than abbreviating it, so `distribution_rate` is never written $\rho$ mid-sentence; and every equation, whether displayed or inline, is followed by its code sibling, so no relation is stated in one form alone. `make notation` enforces all of it. This table is the mapping, and it is the only translation a reader should ever need. Where the specification names a constant, that name is authoritative and the row says so.

| name used here | symbol | specification constant | what it is |
| --- | --- | --- | --- |
| `target_claims_per_block` | $T$ | `TARGET_CLAIMS_PER_BLOCK` | claims per block the difficulty controller steers toward |
| `pow_share` | $\beta$ | `POW_SHARE` / `SHARE_DEN` | fraction of collected fees diverted into the reward pool |
| `distribution_rate` | $\rho$ | `EPOCH_POW_DISTRIBUTION_RATE` | fraction of the pool an epoch's reward is sized from |
| `genesis_pool` | $R_0$ | `POW_REWARD_POOL_GENESIS` | the pool's endowment at launch |
| `blocks_per_epoch` | $N_b$ | — (21,600) | blocks in one epoch |
| `smoothing_factor` / `smoothing_precision` | $F_\text{ema}$ / $P_\text{ema}$ | `EMA_SMOOTHING_FACTOR` / `_PRECISION` | the retarget's EMA weight, as the ratio $F_\text{ema}/P_\text{ema}$ (§3.6) |
| `pool` | $R$ | `pow_reward_pool` | the reserve claims are paid from, at a given moment |
| `reward_per_claim` | $\sigma_e$ | `epoch_pow_reward` | what one successful claim mints, fixed for the epoch |
| `claim_fee` | $\varphi$ | — | what a claim transaction costs to submit |
| `steady_reward` / `steady_pool` | $\sigma^\ast$ / $R^\ast$ | — | where reward and pool settle once fee refill balances payout |
| `pool_floor` | $R_\text{min}$ | — | pool below which a claim no longer beats its own fee |
| `reward_over_fee` | $\sigma^\ast/\varphi$ | — | **the margin that decides whether mining pays at all** |
| `txs_per_block` | $n_\text{tx}$ | — | transactions a block carries (exogenous; §4.9 removes it) |
| `fee_ratio` | $\psi$ | — | average transaction's fee over a claim's (§4.3) |
| `fee_load` | $\hat\Phi$ | — | a block's fee revenue counted in claim fees (§4.9) |
| `adversary_hashrate` | $h$ | — | share of mining power an attacker holds |
| `initial_stake` | $D_0$ | — | stake already securing the chain at launch |
| `leader_fee_share` | $L$ | — (**unset**, §10.1) | share of undiverted fees reaching block leaders |

Quantities that appear only inside equations, for completeness of the mapping:

| name used here | symbol | what it is |
| --- | --- | --- |
| `epoch_refill` | $F$ | fees diverted into the pool at one epoch boundary |
| `avg_tx_fee` | $\bar\varphi$ | fee the average transaction pays |
| `opening_reward` | $\sigma_0$ | `reward_per_claim` in the first epoch |
| `claims_paid` | $c_e$ | claims actually paid in an epoch |
| `claims_in_block` | $c_n$ | claims landing in one block |
| `difficulty_target` | $d$ | the threshold a ticket must fall below (smaller = harder) |
| `expected_claims` | $x$ | claims a block is expected to draw at the current target (§3.6) |
| `demand_est` | $\widehat{\text{dem}}$ | the retarget's smoothed demand estimate (§3.6) |
| `smoothing` | $q$ | the EMA weight, `smoothing_factor / smoothing_precision` |
| `hashrate` / `equilibrium_hashrate` | $H$ / $H^\ast$ | mining power; the level free entry drives it to |
| `equilibrium_difficulty` | $d^\ast$ | the target free entry settles on (§3.5) |
| `opening_multiple` | $m$ | how many claim fees the endowment's first reward is worth (§4.12) |
| `claims_so_far` / `claims_to_exhaust` | $k$ | claims paid since the epoch opened; the count that empties the pool (§3.8) |
| `epoch` / `epochs` | $e$ / $E$ | an epoch index; a count of epochs |
| `break_even_load` | $\hat\Phi_\text{min}$ | fee load at which a claim exactly repays its own fee (§4.9) |
| `self_funding` | — | the predicate `steady_reward > claim_fee`, written out (§4.3) |
| `next_difficulty_target` / `next_expected_claims` | $d_{n+1}$ / $x_{n+1}$ | the retarget's outputs for the following block (§3.6) |
| `observed_txs_per_block` | — | transactions a block actually carried, as the fee market measures it |
| `max_minted_per_block` | — | emission cap converted to LGO per block (§4.4.2) |
| `claim_window_blocks` / `block_rate` | $W_b$ / $f$ | blocks a claim stays acceptable; blocks per slot (§1.5) |
| `base_units_per_lgo` | $u$ | base units in one LGO — the denomination (§0.2) |
| `cost_per_guess` | $\kappa$ | a miner's cost per candidate (**unknown**, §1) |
| `field_modulus` | $p$ | size of the space a ticket is drawn from |
| `block_seconds` | $\Delta_b$ | expected seconds per block |
| `claim_share` | $v$ | claims as a fraction of a block's transactions (§4.7.2) |
| `block_fee_revenue` | $\Phi_b$ | total fees one block collects |
| `equilibrium_claim_rate` | $\lambda^\ast$ | rate the retarget actually settles at (§4.8) |
| `honest_stake_frac` | $s$ | share of winnings honest miners stake |
| `net_per_epoch` | $\text{net}_e$ | refill minus the epoch's fee cost of the claims it pays (§4.3) |
| `cumulative_distributed` | $C_E$ | LGO the pool has paid out after $E$ epochs (§3.7) |
| `opening_reward_over_fee` | $\sigma_0/\varphi$ | the first epoch's reward against a claim's own fee |
| `launch_supply` | $S_\text{tge}$ | token supply at the generation event |

Names appearing only in §1.5 — `block_reward_blend_share`, `block_reward_pow_share`, `pow_quota`, `difficulty_blend` and the rest — are quoted from the proposal's own identifier inventory and belong to it, not to this model; they are listed there and used nowhere else. Two of them look like names above and are not: `pow_share` is the **fee** diversion this model turns on, whereas proposal §5.8's `block_reward_pow_share` is one leg of a three-way split of the **block reward**. Likewise $F$ is the epoch refill and $F_\text{ema}$ the retarget's smoothing weight — unrelated quantities that the source material both wrote as $F$.

### 3.1 Reward trajectory — item 1 ✅ `DERIVED`

**Intuition.** A bucket with a hole proportional to how full it is, plus a hose adding a fixed amount. It empties fast, then slower, and settles where the two balance.

**Step 1 — the payout is a fixed fraction.** At the target rate, $c_e\,\sigma_e = T N_b \cdot R\rho/(T N_b) = \rho R$ — `claims_paid * reward_per_claim == distribution_rate * pool`. The central identity: **`target_claims_per_block` and `blocks_per_epoch` vanish from the pool dynamics entirely.**

**Step 2 — solve.** $R_{e+1} = (1-\rho)R_e + F$ — `pool = (1 - distribution_rate) * pool + epoch_refill`, an affine map with fixed point $R^\ast = F/\rho$ — `steady_pool = epoch_refill / distribution_rate`, giving

| **the reward trajectory** |
| --- |
| $\sigma_e = \sigma^\ast + (\sigma_0 - \sigma^\ast)(1-\rho)^e$ |
| `reward_per_claim(epoch) = steady_reward + (opening_reward - steady_reward) * (1 - distribution_rate)**epoch` |
| $\sigma^\ast = \dfrac{F}{T\,N_b}$ |
| `steady_reward = epoch_refill / (target_claims_per_block * blocks_per_epoch)` |
| $\sigma_0 = \dfrac{\rho\,R_0}{T\,N_b}$ |
| `opening_reward = distribution_rate * genesis_pool / (target_claims_per_block * blocks_per_epoch)` |
At `distribution_rate` = 0.5 %: half-life **138 epochs ≈ 2.84 years**; annual decay **−21.6 %**. That is the rate at which any gap between the opening reward and the settled one closes — and under fee funding the endowment can be sized so there is no gap to close (§3.7), in which case the trajectory is flat and the half-life never comes into play.

**The counterintuitive part.** `steady_reward` contains no `distribution_rate`. **The payout rate sets how fast you reach the destination, never the destination.** Drain 1 % and the pool settles at 100× the refill, paying out exactly the refill; drain 2 % and it settles at 50×, still paying the refill. In the long run the scheme distributes only what flows in. `distribution_rate` does have one lasting effect, though it is not on the reward: it sets $R_\text{min} = \varphi T N_b/\rho$ — `pool_floor = claim_fee * target_claims_per_block * blocks_per_epoch / distribution_rate`, the pool size below which claiming stops being worthwhile at all (§4.3), so a slower payout rate demands a proportionately larger pool to sustain the same per-claim reward.

### 3.2 Pool stability — item 2 ✅ `DERIVED`

Shrink-and-add: one fixed point, **monotone convergence, oscillation impossible**. The real failure is §2.3's cliff, reachable only if an epoch's refill `epoch_refill = pow_share * blocks_per_epoch * block_fee_revenue` falls below `target_claims_per_block * blocks_per_epoch` base units. **Mining survives long-run iff one epoch's refill exceeds `target_claims_per_block * blocks_per_epoch`** — 216,000 base units at `target_claims_per_block = 10`, which any fee revenue worth diverting clears by a wide margin. Under fee funding the binding constraint is not this cliff but §4.3's self-funding condition, which bites far earlier.

This is the *across-epochs* stopping condition. There is a second, *within-epoch* one — see §3.8.

### 3.3 Where the endowment ends up `DERIVED`

`cumulative_distributed(epochs) = epochs * epoch_refill + (genesis_pool - steady_pool) * (1 - (1 - distribution_rate)**epochs)`. Under block-reward funding, where `genesis_pool >> steady_pool`, this read as "the endowment is fully distributed except `steady_pool = epoch_refill / distribution_rate`, held forever". Under fee funding the first term dominates instead: **the pool distributes the fee inflow indefinitely**, and the endowment's contribution is the second term, positive or negative according to whether `genesis_pool` was set above or below the fixed point. At the §3.7 parameter set `genesis_pool ≈ steady_pool`, so the endowment contributes essentially nothing to what is distributed — its whole job is to be *present*, keeping the pool above `pool_floor` from the first epoch rather than waiting for the inflow to build it. §4.1 revisits what an unbounded distribution means for security.

### 3.4 Inflation — item 5 ✅ `DERIVED`, conditionally

Two sources, easily conflated. The **refill** is a slice of fees that would otherwise be burnt — tokens already in circulation, redirected rather than created. The **endowment** is carved from the initial distribution; those tokens already exist too.

**So mining adds no inflation — provided the endowment comes from existing supply rather than being printed.** That proviso does all the work; the specification states it. The emission cap is untouched in every regime.

What mining changes is either the *burn* or the *block reward*, depending on where the emission controller sits, and §4.4.2 works this out in full because it is what bounds `pow_share`. In brief: the controller mints against the fees actually burnt, so diverting a share before the burn lowers that measurement. Early, when emission is minting-dominated, the burn does not feed back into the block reward, so the diversion shows up purely as a smaller burn and the supply ends up higher than it would have been — a reduction in deflationary pressure, not an increase in issuance. Later, when emission is recycling-dominated, the block reward *is* the burn, so the diversion lowers the block reward by the same share and the supply is untouched.

**The earlier version of this section said the pool "distributes tokens that were already on their way to being destroyed" without qualification. That is the first regime only.** In the second the tokens would have been destroyed *and reminted*, so what the pool takes comes out of Blend and leader rewards rather than out of the burn.

### 3.5 Miner entry — item 4 ✅ `DERIVED` from A3

Two sides have to agree. **Protocol side:** the thermostat holds claims at `target_claims_per_block` whatever hashrate appears, so `hashrate * block_seconds * equilibrium_difficulty / field_modulus = target_claims_per_block`. **Miner side:** the expected cost of one win is `(field_modulus / difficulty_target) * cost_per_guess` for a cost-per-guess `cost_per_guess`, and free entry drives the marginal miner's margin to zero, so `reward_per_claim - claim_fee = (field_modulus / equilibrium_difficulty) * cost_per_guess`.

Combining, the field order cancels:

| **equilibrium hashrate** |
| --- |
| $H^\ast = \dfrac{T\,(\sigma_e - \varphi)}{\Delta_b\,\kappa}$ |
| `equilibrium_hashrate = target_claims_per_block * (reward_per_claim - claim_fee) / (block_seconds * cost_per_guess)` |
**Equilibrium hashrate does not depend on difficulty or field size** — those are the dial. It depends on money-per-block over cost-per-work.

`equilibrium_hashrate > 0` requires `reward_per_claim > claim_fee`. **The on-ramp survives long-run iff `epoch_refill / (target_claims_per_block * blocks_per_epoch) > claim_fee`.**

Substituting the refill, `steady_reward > claim_fee` becomes `fee_ratio * pow_share * txs_per_block / target_claims_per_block > 1` — §4.3's condition, reached from the miner's side rather than the pool's. The on-ramp and the pool's solvency turn out to be the same inequality.

### 3.6 Controller stability — item 6 ✅ `DERIVED`

Write `expected_claims` for the expected claims a block draws at target `difficulty_target` — the substitution that removes hashrate and field size from the recurrence, leaving the controller's own map.

| the substitution, and the map it produces |
| --- |
| $x_n = H\,\Delta_b\,d_n/p \quad\Longrightarrow\quad x_{n+1} = g(x_n) = \dfrac{T\,P_\text{ema}\,x_n}{(P_\text{ema}-F_\text{ema})\,x_n + F_\text{ema}\,T}$ |
| `expected_claims = hashrate * block_seconds * difficulty_target / field_modulus` → `next_expected_claims = target_claims_per_block * smoothing_precision * expected_claims / ((smoothing_precision - smoothing_factor) * expected_claims + smoothing_factor * target_claims_per_block)` |

The map carries neither `hashrate` nor `field_modulus`, so its behaviour is a property of the controller alone. Its fixed points solve $x(x-T) = 0$, and the slopes there settle the question:

| at the target | at the empty state |
| --- | --- |
| $g'(T) = F_\text{ema}/P_\text{ema} = 0.9$ | $g'(0) = P_\text{ema}/F_\text{ema} = 1.11$ |
| `smoothing_factor / smoothing_precision = 0.9` | `smoothing_precision / smoothing_factor = 1.11` |
| **stable** — below one, so the target attracts; time constant about ten blocks | **repelling** — above one, so the no-claims state pushes away |

The deadlock concern is therefore unfounded: the only state a stalled chain could settle into is the one the map drives away from.

![retarget return map](figures/14_retarget_map.png)
*Fig 14 — the same argument as a picture. The return map is concave with slope > 1 at the origin and < 1 at `target_claims_per_block`, so cobwebs from either side walk monotonically home: overshoot decays, silence escapes, and oscillation has nowhere to come from.*

**The retarget in EMA form — and why there is nothing left to simplify.** The natural "clean" controller one would design from scratch is: normalize each block's count by the target that produced it (a hashrate estimate), smooth that with an EMA, and set the next target so the smoothed demand yields `target_claims_per_block`:

| **the reward difficulty retarget** |
| --- |
| $\widehat{\text{dem}}_{n+1} = (1-q)\,\dfrac{c_n}{d_n} + q\,\widehat{\text{dem}}_n$ |
| `demand_est = (1 - smoothing) * (claims_in_block / difficulty_target) + smoothing * demand_est` |
| $d_{n+1} = \dfrac{T}{\widehat{\text{dem}}_{n+1}}$ |
| `difficulty_target = target_claims_per_block / demand_est` |
**The specified retarget is this controller, exactly.** The invariant $\widehat{\text{dem}} = T/d$ — `demand_est = target_claims_per_block / difficulty_target` — holds from genesis (one initialization sets both), and substituting it gives $\widehat{\text{dem}}' = [(1-q)c + qT]/d$, hence $d' = T\,d/[(1-q)c + qT]$ — `next_difficulty_target = target_claims_per_block * difficulty_target / ((1 - smoothing) * claims_in_block + smoothing * target_claims_per_block)` — the spec's map with **`smoothing = smoothing_factor / smoothing_precision`**. Verified numerically: 9.7×10⁻¹⁴ worst relative divergence over 20,000 shared-noise blocks (`make verify`). So the two smoothing constants are **one dial**: `smoothing = 9/10`, with `P` merely the integer precision its name declares. The spec's one-state form is the *reduced* notation — it stores the smoothed estimate inside the target itself, carrying one state variable and one rounding site where the explicit-EMA form carries two of each. "Memoryless" was always a misnomer: the memory is in `difficulty_target`.

### 3.7 Worked example

> **Corrected in place 2026-08-13; §0.3 records what moved and why.** This section was computed when `genesis_pool` sat at the pool's fixed point; it now sits far above it, so the reward decays.


`distribution_rate`=0.5 %, `target_claims_per_block`=10, `pow_share`=10 %, `genesis_pool`=5×10⁷ LGO (0.5 % of supply), 600 tx/block, `claim_fee`=6,664 lepta — the specified parameter set. `genesis_pool` sits **far above** the pool's fixed point, which is what makes the trajectory a decay rather than a plateau.

**Refill** `0.10 × 21,600 × 600 × 5,579 = 7,230,384,000` lepta/epoch = 7.23 LGO — note it contains no `target_claims_per_block`. **Steady state** `steady_pool` = 1,446 LGO, likewise independent of `target_claims_per_block`. The endowment is **34,576×** that, so `reward_per_claim` decays across decades rather than sitting flat:

| epoch | years | $\sigma_e$ (lepta) | × fee |
| --- | --- | --- | --- |
| 0 | 0.00 | 1,157,407,407 | 173,681× |
| 100 | 2.05 | 701,136,387 | 105,213× |
| 299 | 6.14 | 258,601,512 | 38,806× |
| 1460 | 30.00 | 801,139 | 120.2× |
| 2433 | 49.99 | 39,322 | 5.90× |
| ∞ | — | 33,474 | **5.02×** |

Fee funding *could* size the endowment at the fixed point and hold the reward flat from the first epoch. The specified set does not: `genesis_pool` is a distribution budget (§4.12), five orders of magnitude above anything the reward economics needs, so the reward opens at 173,681× the fee and decays toward 5.02× over about 43 years at the resting price (§4.7.1). **The steady state is what the system converges to, not what it launches with.**

The flip side is that a decaying `reward_over_fee` means the builder's self-dealing edge **grows** rather than shrinking (§4.2): 1.0000× at genesis, where the reward dwarfs the fee, approaching **1.124×** as the reward settles. **The two properties are the same fact seen twice** — a reward that decays is a margin that widens. The endpoint is benign, and it is the worst moment, not the first epoch.

**Cost to the network.** In the steady state the pool distributes `distribution_rate * steady_pool = epoch_refill = 7.23` LGO per epoch, which is 10 % of the fee revenue by construction (far more than that while the endowment is still draining). Of that, a fifth returns immediately as the claims' own transaction fees and four fifths reaches claimants — at `target_claims_per_block = 50` the split would have been all and nothing (§4.4.1). It is a permanent transfer, not a taper, and §4.4.2 sets out who bears it: the supply early, Blend and the leaders once emission is recycling-dominated.

### 3.8 What stops claiming, and how it restarts `DERIVED`

Two distinct conditions stop claiming, on different timescales, and only one of them is permanent. The distinction was not drawn in earlier revisions of this document or of the specification, and both now state it.

**`distribution_rate` is not a spending cap.** This is the point everything else follows from. `reward_per_claim = distribution_rate * pool / (target_claims_per_block * blocks_per_epoch)` divides the pool by the number of claims an epoch is *expected* to accept; it does not limit how many are accepted. Nothing caps claims per block, and nothing caps payout per epoch. Claims are paid one after another for as long as the pool covers the next one. The identity in §3.1 — that an epoch distributes exactly `distribution_rate` of the pool — holds **only at the target rate**, which is an assumption about the controller, not a rule the protocol enforces.

**Condition 1 — within an epoch: `pool < reward_per_claim`.** `reward_per_claim` is frozen at the epoch boundary while the pool drains with every claim, so after `claims_so_far` claims the pool is `genesis_pool - claims_so_far * reward_per_claim` and the guard fails at

| **claims needed to exhaust the pool within an epoch** |
| --- |
| $k > \dfrac{R_0}{\sigma_e} - 1 = \dfrac{T\,N_b}{\rho} - 1$ |
| `claims_to_exhaust = pool // reward_per_claim  # = target_claims_per_block * blocks_per_epoch / distribution_rate` |
which is `1 / distribution_rate` times the epoch's target claim count — **43,200,000 claims against a target of 216,000** at the specified values. Per block that is `target_claims_per_block/distribution_rate = 2000` claims, against `MAX_BLOCK_TXS = 1024`.

**That is 195 % of block capacity — impossible by construction.** No sequence of valid blocks can carry the required rate, whatever happens to the difficulty controller, and it stays impossible up to a doubling of `MAX_BLOCK_TXS`. It was not always so: at `distribution_rate` = 1/100 the figure was 1,000 against 1,024 — 97.7 % of capacity, thin, and resting entirely on the controller — and at the earlier `target_claims_per_block = 50` it was 5,000, unreachable for the other reason. Lowering `target_claims_per_block` to 10 had quietly moved the drain from impossible to merely very hard; **moving `distribution_rate` to a two-hundredth (§0.4) restored the structural guarantee without giving back any of what the smaller `target_claims_per_block` bought.** The controller still holds the actual rate two orders of magnitude below even the old threshold, now as defence in depth; the guard remains what makes any future re-opening degrade gracefully rather than catastrophically.

**Condition 2 — across epochs: `reward_per_claim = 0`.** The pool decays over many epochs until `distribution_rate * pool / (target_claims_per_block * blocks_per_epoch)` floors to zero, at `pool < target_claims_per_block * blocks_per_epoch / distribution_rate` base units. This is §3.2's cliff, and it is the permanent one.

**Semantics, confirmed (2026-08-14).** To pin what the paragraphs above imply, since it decides how the pool must be modelled: the reward `reward_per_claim` is computed **per epoch**, but there is **no per-epoch pool, budget, or claim quota** — each epoch draws on the *whole* pool, claim by claim, until it cannot cover the next full reward. That claim is rejected (the transaction is invalid whole), the sub-`reward_per_claim` remainder **stays in the pool** rather than being paid or lost, and at the boundary the refill is credited and `reward_per_claim` recomputed from what stands. Rewarding halts within an epoch when `pool < reward_per_claim` — not at literally zero — and halts *permanently* only at condition 2's cliff. Both engines implement this: the sampled engine pays `min(claims_in_block, pool // reward_per_claim)` per block, and the mean-field engines may use an epoch-level guard only because at the target rate the epoch's drain is `(distribution_rate * pool) <= pool`, so the per-claim guard cannot bind there — both facts are gated in `make verify`.

**Recovery.** Condition 1 is self-healing and condition 2 is not. If the pool is drained mid-epoch, claiming stops for the remainder of that epoch; at the next boundary the refill is credited and `reward_per_claim` is recomputed from the refilled pool, so a drained pool yields a proportionately smaller reward and claiming resumes at that lower value. **The mechanism degrades to a smaller reward rather than stopping.** It stops for good only under condition 2, when the recomputed reward rounds down to zero — and because that is a floor rather than a taper, it stops abruptly.

**Where the interleaving comes in — and where it does not.** Interleaved validate-then-execute exists so that a note created by one Operation is spendable by a later one in the same transaction, which is what makes a claim self-funding (`bedrock-v1.1-mantle-specification.md`, *Validation*). That is its reason, and it is not the pool guard. But it has a real second effect here: a transaction carrying several claims has each checked against the pool *net of its predecessors*, rather than all of them checked against the pool as it stood before the transaction began. Under the previous batch ordering every such claim would have passed a check the pool could not satisfy, and the shortfall would have surfaced only as a failed subtraction during execution. Across transactions the pool is sequential anyway, so this matters only within one. It is a consequence of interleaving, not a motivation for it.

## 4. Simulation results

Run against the `empowering` package (`make all`), whose self-checks pass: **20 gates** in `make verify` — the trajectory tracks §3.1's closed form to 3.5×10⁻¹¹, the target is an exact controller fixed point, the pool never goes negative, the claim-share identity of §4.7.2 holds across traffic and `pow_share` — plus **8 exact-integer confirmations** in `make lepta`, which the float engine structurally cannot provide.

### 4.1 Bootstrap security — item 3 ✅ `SIMULATED`

> **Corrected in place 2026-08-13; §0.3 records what moved and why.** The figures below are recomputed; the qualitative argument and the asymptote are unchanged.


An adversary with hashrate share `adversary_hashrate` captures `adversary_hashrate` of claims (A8) and stakes them; honest miners stake a fraction. Mined coins age one epoch before counting (`cryptarchia-v1-protocol.md:157`). `initial_stake` is the honest stake already securing the chain.

Adversarial share of total stake **after 6.14 years** at the §3.7 parameters, over which the pool distributes **0.39 %** of supply:

| `initial_stake` (% of supply) | h=0.10 | h=0.33 | h=0.50 |
| --- | --- | --- | --- |
| **0.5 %** | 4.4–5.4 % | 14.4–16.9 % | 21.9–24.5 % |
| **5 %** | 0.7 % | 2.4 % | 3.6–3.7 % |
| **30 %** (the staking target) | 0.1 % | 0.4 % | 0.6 % |

(ranges span honest miners staking 100 % vs 50 % of winnings)

![adversary share over time](figures/13_adversary_over_time.png)
*Fig 13 — the same answer as a trajectory: the share rises while the endowment drains, then flattens once the refill (tiny against the stake base) is all that remains. The "peak" is a horizon figure; the fixed-`initial_stake` asymptote is centuries away, which is why this section calls it an artefact rather than a prediction.*

**Fee funding changes the shape of this result, and not for the better.** Under block-reward funding the pool held a fixed endowment, distributed it, and stopped: there was a genuine *peak*, and the answer was "risk is a function of the endowment relative to pre-existing stake". Under fee funding **the refill never stops**, so the amount distributed grows linearly with the horizon and the figures above are six-year numbers rather than lifetime ones. With `initial_stake` held fixed the adversary's share rises without bound toward

| **the fixed-D₀ asymptote (an artefact, not a prediction)** |
| --- |
| $\dfrac{h}{h + (1-h)\,s}$ |
| `asymptote = adversary_hashrate / (adversary_hashrate + (1 - adversary_hashrate) * honest_stake_frac)` |
where `honest_stake_frac` is the fraction of winnings honest miners stake — **33 % at h=0.33 with full honest staking, 49.6 % if honest miners stake only half**. There is no horizon at which it turns around.

**That asymptote is an artefact worth naming, not a prediction.** It follows from holding `initial_stake` fixed forever while mining accumulates, and that double counts: the tokens the pool pays out were paid *as fees* by holders, so mining shifts ownership rather than creating stake. A model that let `initial_stake` decline by the fees paid and grow by ordinary staking would not produce it. But the model does not have that, so the honest statement is: **the six-year figures are sound, the asymptote is a modelling artefact, and the long-run security question is genuinely open under fee funding in a way it was not under block-reward funding.**

The near-term condition is comfortable at the specified endowment: **no cell crosses one third** at the six-year horizon. The worst is `initial_stake = 0.5 %` with a one-half attacker at 24.5 %, and at the 30 % staking target a one-third attacker reaches 0.4 %. That headroom is a consequence of `genesis_pool`, not of the reward parameters — §4.12 shows the endowment is what sets the distributed amount, and §4.10.2 prices the trade across its range. §4.4.2 shows this bound does not select `pow_share` — the share sets how fast the limit is approached, not the limit.

### 4.2 Builder self-dealing — item 7 ✅ `SIMULATED`

> **Part (c) corrected in place 2026-08-13; §0.3 records what moved and why.** The edge rises from 1.0000× to 1.124× rather than falling. The bound and parts (a) and (b) are unchanged.


Three candidate advantages:

**(a) Stealing another miner's claim — impossible by construction.** The reward pays `claim.public_key`, fixed in the payload, whose secret key the builder does not hold. Including someone else's claim pays *them*. Front-running is pointless.

**(b) Censoring rivals in its own blocks — worthless unless block space is contested.**

| `target_claims_per_block` | claims as % of block | advantage (h=$\beta$=0.33) |
| --- | --- | --- |
| **10** (specified) | **1.0 %** | **1.00×** |
| 50 | 4.9 % | **1.00×** |
| 100 | 9.8 % | **1.00×** |
| 1024 | 100 % | 1.67× |

At `target_claims_per_block = 10` claims occupy one percent of a block, so every valid solution is included somewhere and censorship yields nothing. **A10 is what makes this safe**, and it would stop being safe if `target_claims_per_block` approached block capacity.

**(c) Recovering the tip on its own claims — real, and it grows as the reward decays.** Fees are burnt but tips go to the leader, so a builder including its own claim pays itself the tip.

| $\sigma_e$ relative to fee | builder edge |
| --- | --- |
| **173,681× — the specified launch value** | **1.0000×** |
| 100× | 1.005× |
| 10× | 1.06× |
| **5.02× — the specified steady state** | **1.124×** |
| 2× | 1.50× |
| 1.5× | 2.00× |
| 1.2× | 3.50× |

**The trajectory depends on where the endowment sits relative to the pool's fixed point**, and at the specified parameters it sits far *above* it (`genesis_pool/steady_pool = 34,576`, §4.12), so the reward decays and **the edge grows**: 1.0000× at launch, 1.0211× at twenty years, 1.124× at the steady state (§3.7, §4.7.1).

**The worst moment is therefore the steady state, decades out — not the first epoch.** What makes this benign is not the shape but the bound: the edge is capped by `1 + tip_fraction / (reward_over_fee - 1)` at the settled margin, and 1.124× is small. The shape does mean the concern arrives slowly and cannot be checked against launch behaviour, which is the argument for treating `reward_over_fee` rather than `opening_reward_over_fee` as the number that matters.

There is no bootstrap grace period any more. Whatever headroom is chosen is the headroom the network lives with, so the choice of `pow_share` and `target_claims_per_block` together is directly a choice about how much of an advantage block builders hold over other miners.

**Design implication, and where it landed.** `reward_over_fee` at 2 gives a 1.5× edge; bringing it below 1.1× needs `reward_over_fee ≳ 6`. At the earlier `target_claims_per_block = 50` that would have required `pow_share ≈ 60 %` — implausibly large — so a permanent 1.5× edge looked unavoidable and was recorded here as a cost of the high claim target. **Lowering `target_claims_per_block` to 10 largely removes it**: at the specified 10 % share the headroom is 5× and the edge **1.124×**. The 1.1× aspiration is missed by a whisker, and §4.4.2 explains why it is not chased further — reaching it needs `pow_share` ≥ 11.9 %, above the ceiling that keeping mining subordinate to staking imposes.

## 4.3 Calibration — the constraint set `DERIVED`

Two prices set every fee: `P_STR` per stored byte and `b_exec` per unit of execution gas. Both are controlled by markets that round their updates upward, which puts a hard floor of **one unit** under each (`storage-markets.md:224`, `execution-market.md:206`) — **but neither rests there.** An in-flight change to both market specifications documents that the downward step `ceil(price * 7/8)` has fixed points at every `price in {1, ..., 7}`, so under sustained downward adjustment a price comes to rest at **7**, not 1. Figures below use the resting level. The unit itself is undefined tree-wide — see §5.1 — so everything is stated per unit of price, and converted only under an explicit assumption.

### What a claim actually costs `DERIVED`

Nothing in the specification tree states this, so `make fee` builds it from the payload definitions, the bincode wire format (`network-wire-format.md:82`) and the gas table (`analysis-gas-cost-determination.md:69-79`).

A claim transaction is **not** a bare `CLAIM_POW_REWARD`. A bare claim mints `reward_per_claim` into the transaction balance, pays the fee out of it, and — by the Mantle rule that any leftover balance becomes an execution tip — hands the entire remainder to the block leader. To keep the reward, a miner must attach a `TRANSFER` that spends the reward note into one of their own. The gas analysis assumes exactly this composition.

| Component | Size | Gas |
| --- | --- | --- |
| `CLAIM_POW_REWARD` payload — nonce, block hash, public key | 96 B | 56 |
| `TRANSFER` payload — one input id, one output note | 74 B | 590 |
| `ZkSignature` on the transfer | 128 B | — |
| bincode framing — vector lengths, opcodes, enum tags | 8 B | — |
| **encoded `SignedMantleTx`** | **306 B** | **646** |

At the resting price that is `306 * 7 + 646 * 7 = 6,664` price units — or 952 at the bare floor, which the markets reach only transiently. An ordinary one-in one-out `TRANSFER` comes to 207 B and 590 gas, or 5,579 units at rest, so

| **the fee ratio** |
| --- |
| $\psi = \dfrac{\bar\varphi}{\varphi_\text{claim}} \approx 0.837$ |
| `fee_ratio = avg_tx_fee / claim_fee  # 0.837` |
— a claim costs slightly **more** than the average transaction, because it carries a transfer plus its own payload and gas on top. **`fee_ratio` is independent of the price level**, since both markets scale together, so the resting-level correction does not move it. It enters every ratio below and mildly tightens each one.

### The self-funding condition

The pool settles where the refill and the payout balance, and at that point the reward per claim is just the refill divided by the claims an epoch expects — $\sigma^\ast = F/(T N_b)$ — `steady_reward = epoch_refill / (target_claims_per_block * blocks_per_epoch)`. Substituting the refill from Background B:

| **the self-funding condition** |
| --- |
| $\dfrac{\sigma^\ast}{\varphi} = \dfrac{\beta\, n_\text{tx}\, \psi}{T}$ |
| `reward_over_fee = pow_share * txs_per_block * fee_ratio / target_claims_per_block` |
| $\text{self-funding} \iff n_\text{tx} > \dfrac{T}{\psi\,\beta}$ |
| `self_funding = txs_per_block > target_claims_per_block / (fee_ratio * pow_share)` |
**Both prices cancel**, and with them the denomination: the condition is a transaction count and nothing else. The distribution rate `distribution_rate` cancels too — it governs how fast the pool converges, never where it converges to (§3.1).

At the specified `target_claims_per_block = 10` (`make rewards`, §4):

| `pow_share` | `txs_per_block` for `steady_reward = claim_fee` | `txs_per_block` for `steady_reward = 2 * claim_fee` |
| --- | --- | --- |
| 5 % | 239 | 478 |
| 10 % | 119 | 239 |
| 20 % | 60 | 119 |
| 33 % | 36 | 72 |
| 50 % | 24 | 48 |

Nothing here is out of reach: every share from 5 % up self-funds with 2× headroom on a block less than half full. **That was not true at the previous `target_claims_per_block = 50`**, where the same table read 1,194 transactions at a 5 % share — beyond `MAX_BLOCK_TXS = 1024` and therefore unreachable at any traffic — and put a floor of 20 % under the share. The claim target, not the share, was what made the constraint bind. §4.4.1 works through the choice.

Read the other way, at the specified 10 % share and 600 transactions per block:

| `target_claims_per_block` | claims as % of a full block | `reward_over_fee` | noise, `1 / sqrt(target_claims_per_block)` |
| --- | --- | --- | --- |
| 1 | 0.1 % | 50.2 | 100 % |
| **10** | **1.0 %** | **5.02** | **32 %** |
| 50 | 4.9 % | 1.00 | 14 % |
| 100 | 9.8 % | 0.50 | 10 % |
| 500 | 48.8 % | 0.10 | 4.5 % |

`target_claims_per_block` buys precision in the claim count and pays for it in self-funding headroom, one for one.

### Why the endowment exists

The condition above is about the *steady state*. During bootstrap the network is quiet — twenty or a hundred transactions a block, not six hundred — so the fee inflow is small, `steady_reward` is far below the fee, and no one would claim. The endowment is what holds `reward_per_claim` above the fee until traffic grows into the condition.

Its floor follows directly. Claiming is worth doing while `reward_per_claim >= claim_fee`, and `reward_per_claim = distribution_rate * pool / (target_claims_per_block * blocks_per_epoch)`, so

| **the endowment floor** |
| --- |
| $R \ge R_\text{min} = \dfrac{\varphi\, T\, N_b}{\rho}$ |
| `pool >= pool_floor = claim_fee * target_claims_per_block * blocks_per_epoch / distribution_rate` |
At `target_claims_per_block = 10`, `blocks_per_epoch = 21,600`, `distribution_rate = 1 %` this is `2.16e7 * claim_fee`. **The pool must hold 21.6 million times a single claim's fee** for one claim to be worth submitting — because it pays out only 1 % of itself per epoch, spread over 216,000 claims. It scales linearly with `target_claims_per_block`, so this floor was five times higher before.

## 4.4 Sizing the endowment `DERIVED` + `SIMULATED`

Not one of §2.3's eight numbered items — the proposal leaves `POW_REWARD_POOL_GENESIS` as `TBD` in Appendix A and folds its consequences into item 1. It is treated separately here because it turns out to be the parameter the whole calibration hinges on.

The opening reward is `opening_reward = distribution_rate * genesis_pool / (target_claims_per_block * blocks_per_epoch)`, so an endowment opening at `opening_multiple` times the fee is `genesis_pool = opening_multiple * claim_fee * target_claims_per_block * blocks_per_epoch / distribution_rate`. Everything on the right except `claim_fee` is fixed by the specification, so as a fraction of supply

| **sizing the genesis pool** |
| --- |
| $\dfrac{R_0}{S} = m\cdot\dfrac{\varphi}{S}\cdot\dfrac{T\,N_b}{\rho}$ |
| `genesis_pool / launch_supply = opening_multiple * (claim_fee / launch_supply) * target_claims_per_block * blocks_per_epoch / distribution_rate` |
**and the whole question reduces to one number: the claim fee as a fraction of total supply.** That number is a *price-level* question rather than a *denomination* question — §4.4.4 corrects an earlier reading of this table that conflated the two. The table below slides the fee across nine orders of magnitude by holding both market prices pinned at their floor of one base unit and varying the denomination underneath, which is a legitimate scenario but not the only way the fee can move. At `target_claims_per_block = 10`, `distribution_rate = 1 %`, opening at twice the fee:

| base units per LGO | $\varphi$ (LGO) | $\varphi$/S | `genesis_pool/S` | verdict |
| --- | --- | --- | --- | --- |
| 1 | 952 | 9.5×10⁻⁸ | **411 %** | impossible |
| 10³ | 0.952 | 9.5×10⁻¹¹ | **0.41 %** | affordable |
| 10⁶ | 9.5×10⁻⁴ | 9.5×10⁻¹⁴ | 0.0004 % | negligible |
| 10⁹ | 9.5×10⁻⁷ | 9.5×10⁻¹⁷ | ~0 | negligible |

**Nine orders of magnitude in the fee, and therefore in the endowment.** What the table really shows is how sharply the sizing depends on the launch fee level, whatever sets it. Every entry scales linearly with `target_claims_per_block`, so the move to `target_claims_per_block = 10` divided this table by five without changing its shape, and the top row — a fee of 952 LGO — remains impossible at any endowment. §4.4.4 restates this as the constraint it actually is: a ceiling of about 1.157 LGO on the launch fee, for the specified endowment to open at twice it.

### Sized against an adoption ramp `SIMULATED`

The single-point view answers "what opens at *m* fees". The question the endowment exists to answer is different: **how large must the pool be so that claiming stays worthwhile for the whole time it takes the network to grow into self-funding?** `make rewards` ramps traffic logistically from 20 to 1024 transactions per block over a stated horizon and binary-searches the smallest `genesis_pool` keeping `reward_per_claim >= claim_fee` throughout, at `target_claims_per_block = 10`, `distribution_rate = 1 %` and the settled denomination of 10⁹ lepta per LGO (§0.1).

| `pow_share` | 1-year ramp | 2-year | 5-year | 10-year |
| --- | --- | --- | --- | --- |
| 5 % | 3.09×10⁻⁸ | 3.31×10⁻⁸ | 4.08×10⁻⁸ | 5.85×10⁻⁸ |
| **10 %** | **3.02×10⁻⁸** | **3.17×10⁻⁸** | **3.68×10⁻⁸** | **4.77×10⁻⁸** |
| 20 % | 2.96×10⁻⁸ | 3.03×10⁻⁸ | 3.29×10⁻⁸ | 3.80×10⁻⁸ |
| 33 % | 2.91×10⁻⁸ | 2.94×10⁻⁸ | 3.03×10⁻⁸ | 3.20×10⁻⁸ |
| 50 % | 2.88×10⁻⁸ | 2.88×10⁻⁸ | 2.88×10⁻⁸ | 2.89×10⁻⁸ |

(as a fraction of total supply. The specified `genesis_pool = 5 * 10⁻³` is five orders of magnitude above every cell — §4.12 explains what actually sizes it.)

Three things fall out.

**The floor is `pool_floor` = 2.88×10⁻⁸ of supply**, shared by every column — the pool must hold that much for a claim to beat its own fee at all, whatever the traffic. Nothing below it is a viable endowment.

**Slower adoption costs more, and superlinearly.** Doubling the ramp from five years to ten roughly doubles the excess over the floor at a 5 % share, because the pool drains at `distribution_rate` for the whole time the fee inflow is short. A larger `pow_share` is not merely a bigger subsidy, it is insurance against adoption being slower than hoped.

**Every share now works.** The previous `target_claims_per_block = 50` produced *never* across the whole 5 % row — no endowment of any size kept claiming alive — and required 1.14–7.88 % of supply elsewhere. At `target_claims_per_block = 10` the entire table fits between 2.88×10⁻⁸ and 5.85×10⁻⁸ of supply, and the choice of share is a preference about robustness to slow adoption rather than a viability constraint.

### 4.4.1 Choosing the target claim rate `DERIVED` + `SIMULATED`

`target_claims_per_block` was 50 in an earlier revision of the specification, chosen as roughly one twentieth of a full block on the reasoning that a larger count is a less noisy count. That reasoning is sound but it prices only one side. `make sweeps` prices the other, and the specification now sets `target_claims_per_block = 10`.

**The identity everything follows from.** §3.1 showed that an epoch running at the target rate distributes the fraction `distribution_rate` of the pool *whatever `target_claims_per_block` is* — `target_claims_per_block` and `blocks_per_epoch` cancel out of the pool dynamics. So `target_claims_per_block` does not decide how much is distributed. It decides how many parts it is divided into, and therefore how much of it survives being divided, because **each claim pays a fee out of its own reward**. Writing the epoch's refill as `epoch_refill = pow_share * blocks_per_epoch * txs_per_block * fee_ratio * claim_fee`, the amount actually delivered net of the claims' own fees is

| **the network's net cost per epoch** |
| --- |
| $\text{net per epoch} = F - T\,N_b\,\varphi = N_b\,\varphi\,\bigl(\psi\,\beta\, n_\text{tx} - T\bigr)$ |
| `net_per_epoch = epoch_refill - target_claims_per_block * blocks_per_epoch * claim_fee` |
**`target_claims_per_block` enters with a minus sign.** At a chosen share it is pure overhead: every unit of `target_claims_per_block` subtracts `blocks_per_epoch * claim_fee` from what reaches claimants. And the same expression gives the ceiling — at `target_claims_per_block = fee_ratio * pow_share * txs_per_block` the reward equals the fee, delivery is zero, and claiming stops.

**Where `target_claims_per_block = 50` sat.** At `pow_share` = 20 % on 600-transaction blocks the ceiling with the 2× headroom §4.2 wants is exactly `fee_ratio * pow_share * txs_per_block/2 = 50`. `target_claims_per_block = 50` was not near the ceiling; it *was* the ceiling, which is why §4.3's table found `pow_share` = 20 % to be the minimum viable share. Half of everything the pool distributed was being returned as fees on the claims themselves.

**Holding the share fixed at 20 %, lowering `target_claims_per_block`:**

| `target_claims_per_block` | $\sigma^\ast/\varphi$ | eaten by fees | reaches miners | builder edge | noise | `genesis_pool` (5-yr ramp) | nodes onboarded/epoch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 100.5 | 1 % | 99 % | 1.01× | 100 % | 0.02 % | 20.5 |
| 5 | 20.1 | 5 % | 95 % | 1.03× | 45 % | 0.11 % | 19.6 |
| **10** | **10.05** | **10 %** | **90 %** | **1.06×** | **32 %** | **0.27 %** | **18.6** |
| 25 | 4.02 | 25 % | 75 % | 1.17× | 20 % | 0.91 % | 15.5 |
| 50 | 2.01 | 50 % | 50 % | 1.50× | 14 % | 2.24 % | 10.4 |
| 100 | 1.00 | 100 % | 0 % | 109× | 10 % | 5.54 % | 0.1 |

The onboarding column is measured against the thing being onboarded *to*: the minimum stake for a Blend service node is `0.001 % * launch_supply = 100,000` LGO (`analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:57-62`), and the column is the epoch's net delivery divided by it. **Claim count is a bad proxy for onboarding.** `target_claims_per_block = 50` pays 1,080,000 claims an epoch, but at 0.96 LGO net each it takes 104,000 of them to reach minimum stake; `target_claims_per_block = 10` pays a fifth as many claims and onboards nearly twice as many participants.

**A correction against an intermediate reading of this result.** Because §4.3 showed `target_claims_per_block` and `pow_share` locked together at fixed headroom — `pow_share = 2T/(fee_ratio * txs_per_block)` — it is tempting to read the move to `target_claims_per_block = 10` as also licensing `pow_share` = 4 %, cutting the fee diversion fivefold at no cost. **It does not.** Those are two different policies and they cannot be combined:

| policy | `target_claims_per_block` | $\beta$ | $\sigma^\ast/\varphi$ | fee overhead | nodes onboarded/epoch |
| --- | --- | --- | --- | --- | --- |
| the earlier base | 50 | 20 % | 2.01 | 50 % | 10.4 |
| **lower `target_claims_per_block`, hold the share** | **10** | **20 %** | **10.05** | **10 %** | **18.6** |
| lower `target_claims_per_block`, hold the headroom | 10 | 4 % | 2.00 | 50 % | 2.1 |
| lower `target_claims_per_block`, hold the headroom | 5 | 2 % | 2.00 | 50 % | 1.0 |

Cutting `pow_share` to 4 % shrinks the refill fivefold, and since the fee overhead stays at 50 % the delivered amount shrinks fivefold too. That row is not `target_claims_per_block = 10` done more cheaply; it is a fifth-sized programme. **`pow_share` is the budget and `target_claims_per_block` is overhead against it.** Lowering `target_claims_per_block` is a free efficiency gain at a fixed budget; it is not a way to reduce the budget while keeping the benefit.

**What lowering `target_claims_per_block` costs.** Only variance, `1 / sqrt(target_claims_per_block)` — 32 % at `target_claims_per_block = 10` against 14 % at 50. Worth being precise about what that does and does not affect. The memoryless controller's step is scale-free: it moves the target by `+11 %` on a block with no claims and `-9 %` on a block with twice the target, at every `target_claims_per_block`. What changes with `target_claims_per_block` is how often a large *relative* deviation is sampled. The resulting jitter changes **which blocks carry claims and when a given miner wins**, not what a win is worth — `reward_per_claim` is fixed for the whole epoch and is independent of any block's realised count. Nothing else degrades: claims fall from 4.9 % to 1.0 % of a full block, so §4.2's censorship result and assumption A10 both get *safer*, and §3.2's cliff threshold `target_claims_per_block * blocks_per_epoch` falls with `target_claims_per_block`.

**Robustness.** The `target_claims_per_block`↔`pow_share` relation and the fee-overhead expression are both ratios in which `P_STR` and `b_exec` cancel, so they are independent of the denomination (§5.1). The endowment column is not, and assumes 10³ base units per LGO.

### 4.4.2 Choosing the share `DERIVED` + `SIMULATED`

`pow_share` was the last free parameter. `make sweeps` fixes it at **a tenth**, and the reasoning turns on a fact about incidence that this model had wrong until now.

#### Who actually pays — and it is not the burn, at least not forever

`block-rewards.md:206` defines `R_block` as *"the total amount of Execution base fees and Storage fees that are **burned** when the block is proposed"*, and the block reward is `r_b = A_t * (minting cap) + (1-A_t) * R_block`. Diverting `pow_share` of the fees **before** the burn therefore lowers `R_block` to `(1-pow_share)` of what it would have been. What that costs depends entirely on where `A_t` sits, and the two answers are opposite:

| regime | block reward | Blend and leaders | supply | **who pays** |
| --- | --- | --- | --- | --- |
| `A_t → 1` — bootstrap, staking far below target | minting-capped, unaffected by the burn | **unaffected** | higher than it would have been | **the supply** |
| `A_t → 0` — the design's stated long-run target | equals `R_block`, so falls by $\beta$ | **fall by $\beta$**, in the 60/40 proportion | **unaffected** | **Blend and the leaders** |

The first row is `block-rewards.md:178` verbatim: *"The amount of tokens burned does not impact the block rewards in this situation."* The second follows from `α_a = 1`, documented as *"It must be one-to-one"* (`:162`), and from the design goal that *"in the long run, Logos Blockchain should mint only enough tokens to compensate for the burned transaction fees"* (`:367`).

**So `pow_share` is not free money from the burn.** An earlier revision of §3.4 and of the specification said the pool "distributes tokens that were already on their way to being destroyed", which is true only in the first regime. In the mature network the pool is a **third claim on the same flow that funds the privacy layer and consensus** — which is what the proposal's own §5.8 assumed, reached by a different route. The difference that still matters is the *base*: a share of the **fees**, which are uncapped, rather than of the **block reward**, which is capped at `r_max`. That is what makes self-funding reachable at all (§4.3), and it is the whole reason for the funding-source change.

The incidence therefore **migrates over the network's life**, from the supply to Blend and the leaders, without `pow_share` changing. Choosing `pow_share` is choosing both. The specification now states this in [Who bears the cost of the diversion](../docs/blockchain/raw/overview-cryptoeconomics.md).

#### The constraint set

**From below — self-funding**, `pow_share >= headroom * target_claims_per_block / (fee_ratio * txs_per_block)`:

| `txs_per_block` | break-even | 2× headroom | 6× (builder edge ≤ 1.1×) |
| --- | --- | --- | --- |
| 100 | 11.9 % | 23.9 % | 71.7 % |
| 300 | 4.0 % | 8.0 % | 23.9 % |
| **600** | **2.0 %** | **4.0 %** | **11.9 %** |
| 1024 | 1.2 % | 2.3 % | 7.0 % |

The endowment covers the low-traffic rows during bootstrap (§4.4), so the row to choose against is the traffic the network expects to *sustain*, not its first year.

**From above — PoS must remain the better path.** The proposal is explicit: EmPoWering *"is not a PoS replacement"* and *"PoS participation remains the most strongly incentivized path"* (§1.5). At `A_t = 0` that becomes checkable, because the mature fee flow splits three ways:

| `pow_share` | PoW | Blend | leaders | PoW as % of the leader share |
| --- | --- | --- | --- | --- |
| 2 % | 2 % | 58.8 % | 39.2 % | 5 % |
| 5 % | 5 % | 57.0 % | 38.0 % | 13 % |
| **10 %** | **10 %** | **54.0 %** | **36.0 %** | **28 %** |
| 15 % | 15 % | 51.0 % | 34.0 % | 44 % |
| 20 % | 20 % | 48.0 % | 32.0 % | 62 % |
| 33 % | 33 % | 40.2 % | 26.8 % | 123 % |

Reading "clearly subordinate" as the mining share staying at or below a third of the leader share gives **`pow_share` ≤ 11.8 %**; at or below half gives 16.7 %.

**The two bounds nearly touch.** At the reference traffic the builder-edge target wants `pow_share` ≥ 11.9 % and subordination wants `pow_share` ≤ 11.8 %. There is no value satisfying both, so one has to give, and it is the builder edge — it is a preference about margin, whereas subordination is a stated design goal of the proposal.

#### Subordination is a share cap; the flows take decades to match it

The cap above is stated on *fee shares*, and in the steady state that is the whole story. At genesis it is not, because both sides live on non-fee income (**Fig 12**). The pool's epoch-0 distribution is `distribution_rate * genesis_pool` = **250,000 LGO**, against leader *fee* income of `leader_fee_share * (1 - pow_share)` of an epoch's fees — about **26 LGO**. On fees alone, mining out-earns the leader path **9,605-fold**, and its flow stays above a third of leader fee income for roughly **42 years** of the endowment's decay. What keeps the launch-era flows in proportion is the leaders' *minted* income: at the emission cap they receive ≈ 2.05 M LGO per epoch, against which the pool's 250,000 is **12.2 %** — under the one-third reading, but on the strength of block rewards, not fees. **The fee-share cap is therefore a statement about the mature network**; during bootstrap, subordination in flow terms is underwritten by the emission schedule, and would need re-examining if the block reward were ever much smaller at launch. (This is the flow-level counterpart of §4.12: `genesis_pool` is a distribution budget, and while it drains, *both* sides' fee arithmetic is dwarfed by their non-fee income.)

![funding flows](figures/12_funding_flows.png)

**Security does not select a `pow_share`.** §4.1's construction gives an adversary with hashrate share `adversary_hashrate` exactly `adversary_hashrate` of whatever the pool paid out, so its share of total stake converges to `adversary_hashrate / (adversary_hashrate + (1 - adversary_hashrate) * honest_stake_frac)` **whatever `pow_share` is**. `pow_share` sets how fast that limit is approached, not the limit. At `adversary_hashrate = 1/3` with honest miners staking their winnings the limit is 33 % and the threshold is never crossed at any `pow_share`; it is crossed only when honest miners largely do not stake, and there `pow_share` merely changes the date. This is a genuine finding and a slightly disappointing one: the parameter that looked like it should be bounded by security is not.

#### What each share buys, at 600 transactions per block

| `pow_share` | $\sigma^\ast/\varphi$ | builder edge | reaching claimants | nodes onboarded/epoch | `genesis_pool` (5-yr ramp) |
| --- | --- | --- | --- | --- | --- |
| 2 % | 1.00 | 109× | 0 % | 0.0 | 0.55 % |
| 5 % | 2.51 | 1.331× | 60 % | 3.1 | 0.42 % |
| **10 %** | **5.02** | **1.124×** | **80 %** | **8.3** | **0.34 %** |
| 20 % | 10.05 | 1.055× | 90 % | 18.6 | 0.27 % |
| 33 % | 16.58 | 1.032× | 94 % | 32.0 | 0.23 % |

Note the top row: **the proposal's illustrative 2 % lands exactly on break-even** at this traffic — the reward equals the fee, nothing reaches a claimant, and the builder edge diverges. Its 2 % was a share of the *block reward*, a different and much smaller base, so the figure does not transfer.

#### The choice

**`pow_share = 10 %`**, as `POW_SHARE = 10` over `SHARE_DEN = 100`. It clears 2× headroom from 240 transactions per block, reaches 5× at the reference 600, holds the builder edge at 1.124× against a 1.1× aspiration, keeps mining at 28 % of the leader share, and needs an endowment of 0.34 % of supply to cover a five-year ramp. A denominator of 100 leaves one-percentage-point granularity for later adjustment.

Going to 20 % would halve the builder edge and double the onboarding rate, at the cost of taking mining to 62 % of the leader share — which is no longer "clearly subordinate", and is the reading of the proposal's §1.5 that decides this.

**What would change the answer.** A lower expected sustained traffic pushes the lower bound up quickly — at 300 transactions per block the 2× requirement is already 8 %, leaving almost no room under the subordination ceiling. If the network is expected to settle below about 250 transactions per block, `target_claims_per_block` should come down further rather than `pow_share` going up, because `target_claims_per_block` and `pow_share` trade one-for-one on this constraint (§4.4.1) and only `pow_share` is bounded above.

### 4.4.3 Choosing the distribution rate and the genesis seed `DERIVED` + `SIMULATED`

The last two, from `make sweeps`. **`distribution_rate = 1/100` and `genesis_pool = 0.5 %` of the launch supply.**

#### `distribution_rate` sets the reserve, not the reward

§3.1's result is easy to misread: `steady_reward = epoch_refill / (target_claims_per_block * blocks_per_epoch)` contains **no `distribution_rate`**. The distribution rate does not set what a claim pays. What it sets is the **size of the standing reserve**, because the pool settles at `steady_pool = epoch_refill / distribution_rate` — that is, at `1 / distribution_rate` epochs' worth of distribution. Everything else follows from that one fact.

| `distribution_rate` | reserve `steady_pool`/supply | epochs held | `pool_floor`/supply | response lag | exhaustion, claims/block |
| --- | --- | --- | --- | --- | --- |
| 0.2 % | 3.62×10⁻⁷ | 500 | 7.20×10⁻⁸ | 10.3 yr | 5,000 — unreachable |
| 0.5 % | 1.45×10⁻⁷ | 200 | 2.88×10⁻⁸ | 4.1 yr | 2,000 — unreachable |
| **1 %** | **7.23×10⁻⁸** | **100** | **1.44×10⁻⁸** | **2.1 yr** | **1,000 — just reachable** |
| 2 % | 3.62×10⁻⁸ | 50 | 7.20×10⁻⁹ | 1.0 yr | 500 — reachable at half-full blocks |
| 5 % | 1.45×10⁻⁸ | 20 | 2.88×10⁻⁹ | 0.4 yr | 200 — routinely reachable |

**Three considerations once pushed `distribution_rate` up, one pushes it down — and the Units decision changed the weights.** A larger `distribution_rate` shrinks the reserve and the endowment floor `pool_floor = claim_fee * target_claims_per_block * blocks_per_epoch / distribution_rate`; at the settled denomination both are ~10⁻⁷ of supply at either candidate value, so neither discriminates any longer. It also shortens the fee-tracking lag, which is real but binds only in the fee-funded era (§4.7.1: ~43 years out at resting prices). A smaller `distribution_rate` widens the margin against §3.8's within-epoch drain, which needs `T/distribution_rate` claims per block — and slows the endowment's distribution, which §4.1 shows is a bootstrap-security *gain*.

**The drain margin has a hard edge**, at `distribution_rate < target_claims_per_block / MAX_BLOCK_TXS = 0.977 %`, and it is the edge that decided the value (§0.4). `distribution_rate = 1 %` sits just the wrong side of it — 1,000 claims per block against 1,024, a 2.4 % margin resting on the difficulty controller — while **`distribution_rate = 0.5 %` sits the right side: 2,000 against 1,024, impossible by construction**, and remaining so up to a doubling of block capacity. A fifth of a percent would harden nothing further while stretching the lag to a decade; a percent gives back the structural guarantee; two percent brings the drain within reach of half-full blocks, which is not acceptable.

**So `distribution_rate = 1/200`** — adopted 2026-08-14 on this analysis (§0.4), superseding the proposal's hundredth. It is where the pressures now meet, not an inherited default.

The one uncomfortable consequence worth naming: a **4.1-year response lag**. The pool tracks a moving `F` with a time constant of `1 / distribution_rate` epochs, so during a growth phase the reward reflects fee revenue from roughly four years earlier. This is smoothing rather than error — it makes the reward predictable and conservative while traffic is rising — but it means the model's steady-state figures describe where the mechanism is heading, not where it will be at any given moment during adoption.

#### The genesis seed

Two floors and one landmark:

| | as a fraction of launch supply |
| --- | --- |
| `pool_floor` — below this a claim no longer beats its own fee | 2.88×10⁻⁸ |
| covers a 1-year adoption ramp | 3.02×10⁻⁸ |
| covers a 2-year ramp | 3.17×10⁻⁸ |
| covers a 5-year ramp | 3.68×10⁻⁸ |
| covers a 10-year ramp | 4.77×10⁻⁸ |
| `steady_pool` at the reference traffic | 1.45×10⁻⁷ |
| **the specified `genesis_pool`** | **5.00×10⁻³** — 135,949× the 5-year ramp (§4.12) |

| `genesis_pool` | in LGO | `opening_reward` | × fee | epochs to `pool_floor` with **no traffic at all** |
| --- | --- | --- | --- | --- |
| 0.2 % | 2.0×10⁷ | 462,962,963 | 69,472× | 2,224 ≈ 46 yr |
| **0.5 %** | **5.0×10⁷** | **1,157,407,407** | **173,681×** | **2,407 ≈ 49 yr** |
| 1.0 % | 1.0×10⁸ | 2,314,814,815 | 347,361× | 2,545 ≈ 52 yr |
| 2.0 % | 2.0×10⁸ | 4,629,629,630 | 694,722× | 2,684 ≈ 55 yr |

**`genesis_pool = 0.5 %`.** At the settled denomination this is not a marginal choice against the ramp — it clears a five-year ramp by 135,949× and opens at 173,681× the fee, sustaining claiming for about 49 years on the endowment alone even with no traffic at all. **The reward-economics constraints do not select it; §4.12 shows what does.** Matching `steady_pool` for elegance, so the reward would be flat from the first epoch, would mean an endowment of 1.45×10⁻⁷ of supply — four to five orders of magnitude smaller, and a mechanism with no bootstrap subsidy at all. The gap between those two readings is the whole of the allocation question.

For scale: the minimum-stake analysis sizes staking around 1,000 nodes at 0.001 % of supply each, i.e. 1 % of supply. A 0.5 % onboarding endowment is proportionate to that rather than large against it.

#### The denomination constraint this finally makes actionable

§4.4 found the endowment undeterminable without the denomination. Stating `genesis_pool` as a *fraction of supply* inverts the problem into something useful. `opening_reward = distribution_rate * genesis_pool / (target_claims_per_block * blocks_per_epoch)` depends only on denomination-free quantities; the fee `claim_fee` is a fixed **952 base units**. So a chosen `genesis_pool` implies a **floor under the denomination**:

| `genesis_pool` | min base units per LGO for `opening_reward >= claim_fee` | for `opening_reward >= 2 * claim_fee` |
| --- | --- | --- |
| 0.2 % | 7,197 | 14,394 |
| **0.5 %** | **2,879** | **5,758** |
| 1.0 % | 1,439 | 2,879 |
| 2.0 % | 720 | 1,439 |

**At `genesis_pool = 0.5 %` the denomination must be at least ~5,758 base units to the token** for the opening reward to be twice the fee *when the markets are at rest*. Any of the plausible candidates — `10⁶`, `10⁸` — clears it by orders of magnitude, so this is a weak constraint in practice, but it is a real one and it is what makes an indivisible LGO impossible rather than merely awkward. The specifications state it in the price-level form, `claim_fee <= 1.157 * 10⁻¹⁰` of supply, so that it holds whatever denomination is settled on.

### 4.4.4 The denomination — a constraint, not a decision for this proposal `DERIVED` + `OPEN`

**Scope.** An in-flight fee-market change carries an explicit note that *"the LGO atomic-unit / precision redefinition ... is deliberately excluded — it touches many documents and will land as its own PR to avoid confusion"*, and its change log records the deferral. That PR has not been opened. **The denomination therefore has an owner-designated vehicle, and EmPoWering is not it.** This section states what EmPoWering *requires* of it and what the evidence rules out, and stops short of setting the value. A suggestion for whoever takes it is recorded below.

The more useful output of working it through is that **§4.4 and §5.1 were wrong about what the denomination was blocking.**

#### The correction

Both sections said the endowment "turns entirely on one unknown: the claim fee as a fraction of total supply", and that this was undeterminable "because the denomination is undefined". The first clause is right. The second is not.

The fee is `claim_fee = 306 * P_STR + 646 * b_exec` **base units**, where `P_STR` and `b_exec` are the two markets' prices. In LGO that is `claim_fee = (306 * P_STR + 646 * b_exec) / base_units_per_lgo`. Only the **ratio** of price level to denomination matters economically, and the price level is a market outcome whose initial value genesis governance sets — `storage-markets.md:230` says so explicitly. So:

- the **denomination** fixes how finely a price can be expressed and how large a value can be represented;
- the **price level** fixes what a transaction costs.

Everything this document computes in LGO — `steady_reward`, `opening_reward`, `pool_floor`, `genesis_pool`, the ramp table, `steady_pool` — is unaffected by `base_units_per_lgo`. What §4.4's nine-orders-of-magnitude table actually varied was the *fee level*, by holding both prices pinned at their floor of one base unit and sliding `base_units_per_lgo` underneath. That is a legitimate scenario (it is what a quiet market does) but it is not "the denomination decides the endowment". **Defining `base_units_per_lgo` does not unblock the endowment; initialising the prices does.**

The constraint is therefore restated: the specified `genesis_pool` opens at twice the fee for as long as the **launch fee is at most `opening_reward/2 = 1.157` LGO**, or `1.157×10⁻¹⁰` of the launch supply. That is a target for genesis governance to hit with `P_STR(0)` and `b_exec(0)`, and it is checkable on the day. It is now stated in both the Mantle and genesis specifications in that form.

#### What EmPoWering requires of it

With the fee question separated out, EmPoWering's requirements are narrow: a bound above, and the ruling-out of the degenerate case below. Both belong in the specification because the mechanism depends on them; the value between them does not.

**Above — representability.** `TokenValue` is `uint64`, so the largest representable amount is `2**64 - 1` ≈ 1.84×10¹⁹ base units. Against a launch supply of `10¹⁰` LGO:

| `base_units_per_lgo` | supply, base units | headroom before a `TokenValue` cannot hold the supply | at 1 %/yr growth |
| --- | --- | --- | --- |
| 10⁶ | 10¹⁶ | 1,845× | 752 years |
| **10⁸** | **10¹⁸** | **18.4×** | **291 years** |
| 10⁹ | 10¹⁹ | 1.84× | 61 years |
| 1.84×10⁹ | 1.84×10¹⁹ | 1.0× | 0 — at the limit today |

`10⁹` leaves under a factor of two, and therefore under a century at the maximum emission rate, for a quantity that cannot be changed after genesis.

**Below — granularity.** Both fee markets round price updates upwards, giving an effective floor of one base unit per unit of gas (`storage-markets.md:224`, `execution-market.md:206`), and rest a little above it. That floor exists to stop zero becoming an absorbing state; it should sit far enough below any discoverable price that it never binds, which argues for the denomination being generous. **A suggestion, not a decision made here:** `10⁸` — eight decimal places, Bitcoin's choice — leaves an eighteenfold margin below the `uint64` bound and puts the smallest expressible fee some five orders of magnitude below a fee level of order one LGO.

#### Is 1 LGO the smallest unit by design? — the evidence says it cannot be

This is worth settling explicitly, because the tree reads as though it might be. `storage-markets.md` states in three places that the price floor and the initial price are *"1 LGO/gas"*, *"1 LGO per Permanent Storage Gas"* and *"a cost of 1 LGO per permanently stored byte"*. Nothing anywhere states a subdivision. On the face of it, `TokenValue` counts whole LGO.

It cannot, and three independent arguments say so — the first of which has nothing to do with EmPoWering.

**1. The block reward is already fractional.** The maximum minted per block is derived in `block-rewards.md:463` as

| **the maximum minted per block** |
| --- |
| $\dfrac{I_{\max}\, S_\text{tge}\, \Delta_t}{f} = \dfrac{10^{-2}\cdot 10^{10}}{365\cdot 2880} = \dfrac{62500}{657} = 95.129376\ldots$ |
| `max_minted_per_block = max_emission_per_year * launch_supply / blocks_per_year  # 95.129376... LGO` |
kept deliberately as an exact fraction, with `block_rewards()` returning a `float`. An indivisible LGO would force this to floor to 95, and no specification says it does. The emission model is already written in a unit finer than one LGO.

**2. One transaction would cost tens of times the entire maximum block reward.** At a floor of 1 LGO per byte and per gas, the claim transaction of §4.3 — 306 bytes, 646 gas — costs **952 LGO** against a maximum block reward of 95.13 LGO. A single transaction at the cheapest price either market can *ever* offer would burn ten blocks' worth of maximum issuance. And the markets do not sit at that floor: they rest at 7 (§4.3), making the everyday figure **6,664 LGO, or seventy times the maximum block reward**. For scale, a Blend node's entire 100,000 LGO minimum stake would buy fifteen transactions.

**3. EmPoWering could not work at all.** `pool_floor = claim_fee * target_claims_per_block * blocks_per_epoch / distribution_rate` is **206 % of the total token supply** at the bare floor and **1,439 %** at the resting price. The pool would have to be many times the entire supply for a claim to beat its own fee. This is not "expensive"; it is impossible at any endowment.

**Conclusion.** The "1 LGO" language was written before the tree had a word for the base unit, and means one unit of the smallest representable amount. That is the ambiguity an undefined denomination allowed to persist, and defining it forces the correction — made in place in `storage-markets.md`, along with the initial-price row.

**If that reading is wrong** and an indivisible LGO is genuinely intended, the consequence is far larger than a parameter choice: EmPoWering cannot be made to work at any endowment, and the fee markets need rescaling against the emission model regardless. That would be a finding about the token design rather than about this proposal, and it should be raised as one.

### The constraints, symbolically

1. **Steady-state self-funding, with headroom.** `fee_ratio * pow_share * txs_per_block / target_claims_per_block > 2`. At the specified `target_claims_per_block = 10` and `pow_share = 10 %` this holds from 240 transactions per block up, and the realised headroom at the reference 600 is 5× with a builder edge of 1.124×. The factor of two is §4.2's.
2. **Solvency across the ramp.** `genesis_pool` at least the ramp table's entry for the adoption horizon being planned for — and never below `pool_floor = claim_fee * target_claims_per_block * blocks_per_epoch / distribution_rate`.
3. **No cliff.** `epoch_refill > target_claims_per_block * blocks_per_epoch` base units, so `reward_per_claim` never floors to zero (§3.2). Implied by constraint 2 whenever `claim_fee >= 1` base unit.
4. **Bootstrap security.** `genesis_pool` small relative to the honest stake securing the chain while it is distributed (§4.1).
5. **Denomination.** `genesis_pool` is now fixed as a *fraction of supply*, which turns this from a blocker into a constraint running the other way: the chosen `genesis_pool` puts a **floor of ~823 base units per LGO** under the denomination for the opening reward to be twice the fee (§4.4.3).
6. **Noise.** Relative variation in claims per block is `1 / sqrt(target_claims_per_block)` (A2), which argues for larger `target_claims_per_block` — directly against constraint 1.

The complete specified set, at `10³` base units per LGO: **`target_claims_per_block = 10`, `pow_share = 10 %`, `distribution_rate = 1/100`, `genesis_pool = 0.5 %` of launch supply.** It opens at `opening_reward = 2.31` LGO against a `0.952` LGO fee — 2.4× — and settles at `steady_reward = 4.78` LGO, 5×, at 600 transactions per block, with a 1.124× builder edge throughout. Nothing in the mechanism is now unparameterised.

## 4.7 Validation figures `SIMULATED`

**What these are for.** A parameter set can be arithmetically correct and still behave badly. The reward could dip below what a claim costs somewhere along the way; the margin could be comfortable at the traffic we assumed and gone at half of it. Tables cannot show either, because both are questions about a *path* or about *how much room there is*. These eight pictures ask them: four trace what happens over time, three map where the set works and where it stops, and one re-reads an assumption against the right yardstick.

Eight figures from `make plots`, rendered from the same `Params` the tables use, so a config edit moves them with everything else. Four trace behaviour over time; three map where the parameter set works and where it stops working; one re-reads an assumption.

### 4.7.1 The pool spends decades on its endowment

**Intuition.** A bath filled at the start, with a tap running and a plug hole that drains a fixed share of whatever is in it. The starting water is vastly more than the tap delivers, so for a very long time the level is falling from where it began rather than rising to where the tap would hold it. The reward tracks the level, so it starts enormous and shrinks for decades.

![pool trajectory](figures/01_pool_trajectory.png)

`genesis_pool` is 5×10⁷ LGO and `steady_pool` is 1,446 LGO — more than four orders of magnitude apart — so the fixed point that §4.4.3 solves for is not a description of the near term. The gap closes at `(1 - distribution_rate)**epoch`, which puts the pool **within a factor of two of `steady_pool` only after about 43 years**. For the whole of that descent the reward per claim is set by the decaying endowment, not by the fee refill, and it falls about 34,600× along the way. It never crosses the floor: `steady_pool` (1,446) sits above `pool_floor` (288), so the steady state clears break-even by design and every point on the path to it clears it by more.

**This is the figure to read before treating `reward_over_fee = 5.02` as the operating number.** It is the number the system converges to, not the one it launches with.

**The descent time is a property of the price level, not of the mechanism.** `reward_over_fee` is price-independent — both fee markets scale together, so the ratio §4.3 derives is untouched — but `genesis_pool` is a fraction of *supply* while `steady_pool` scales with the *fee*, so the gap between them, and the time to close it, is not:

| price level | vs resting | `steady_pool` (LGO) | `genesis_pool/steady_pool` | years to within 2× of `steady_pool` |
| --- | --- | --- | --- | --- |
| 7 (resting) | 1× | 1,446 | 34,576 | **42.8** |
| 700 | 100× | 144,608 | 346 | 24.0 |
| 7,000 | 1,000× | 1,446,077 | 34.6 | 14.4 |
| 116,564 (deflation threshold, §3.4) | 16,652× | 24,080,071 | 2.1 | 0.3 |

So "decades on the endowment" is the *resting-price* case, which is the conservative one and the one the figure plots. At discovered prices a few orders of magnitude above the floor the system reaches its fee-funded regime within a decade and a half, and almost immediately at the deflation threshold. Both readings share the same `reward_over_fee`, so nothing about the self-funding margin depends on which obtains — only the shape of the approach does.

### 4.7.2 The claim share of traffic, and its ceiling

**Intuition.** A claim is a transaction too, and pays a fee like any other. That makes two different questions, easily confused. *Do claims fit in a block?* — yes, easily. *Do they earn more than they cost?* — that depends on how much fee revenue there is to share out. If claims are too large a fraction of the traffic, they are mostly paying themselves, and the mechanism is running on its endowment rather than on fees.

![claim share vs traffic](figures/02_claim_share_vs_traffic.png)

Assumption A10 checks the claim load against `MAX_BLOCK_TXS` and finds 1.0 %, "comfortable with room to spare". That is the right test for whether claims *fit*, and it passes. It is not the test for whether they *pay*, because the reward per claim is funded by the fees actual traffic collects, not by the fees capacity could collect.

Against traffic the two quantities are one identity. With `claim_share = target_claims_per_block / txs_per_block` the claim share of a block's transactions,

| **the claim-share identity** |
| --- |
| $v = \dfrac{T}{n_\text{tx}}$ |
| `claim_share = target_claims_per_block / txs_per_block` |
| $v \cdot \dfrac{\sigma^\ast}{\varphi} = \psi\,\beta$ |
| `claim_share * reward_over_fee == fee_ratio * pow_share  # invariant` |
so at break-even the claim share is exactly `fee_ratio * pow_share`, and that is the **ceiling**: if claims are more than `fee_ratio * pow_share = 8.37 %` of transactions, a claim earns less than the fee it pays. It depends on `pow_share` and nothing else — `target_claims_per_block` cancels, and so does the traffic level. At the specified set the network operates at `claim_share = 1.67 %`, a **5.02× margin** below the ceiling, and the break-even traffic is 119 tx/block.

Both numbers are gated in `make verify`.

### 4.7.3 What `pow_share` actually buys

**Intuition.** `pow_share` is the slice of fees the pool takes. Raising it does *not* mean more people mine: the difficulty controller holds the number of winners at `target_claims_per_block` whatever happens. It means each winner is paid more — which is the same thing as saying the network can be quieter before mining stops being worth doing.

![beta relation](figures/03_beta_relation.png)

**Raising `pow_share` does not put more claims in a block.** The difficulty controller holds the claim count at `target_claims_per_block` whatever `pow_share` is, so the claim share of transaction volume is invariant in `pow_share` — the identity above moves the *ceiling*, not the operating point. What `pow_share` buys is traffic headroom: the floor below which mining stops funding itself is `target_claims_per_block / (fee_ratio * pow_share)`, which the specified tenth puts at 119 tx/block.

The sweep in §4.4.2 is worth re-reading against this. **At the proposal's original 2 % example the break-even traffic is 597 tx/block against a reference of 600** — `reward_over_fee = 1.00`, no headroom at all. The move to a tenth is what converts the mechanism from marginal to funded.

### 4.7.4 The endowment against an adoption ramp

**Intuition.** The endowment exists to pay miners before there is enough fee income to pay them. So the test is simple: start with little traffic, grow it, and check the reward never falls below the claim's own fee along the way. The specified endowment turns out to be so much larger than that test needs that the test never binds.

![endowment ramp](figures/04_endowment_ramp.png)

Each ramp is plotted at *its own* minimum endowment, where each just grazes the floor — which is what makes the test legible. At the specified `genesis_pool` all four curves lie on top of one another, because the endowment is **135,949× the 5-year minimum** and the ramp shape disappears beneath it.

That ratio is itself a finding: `genesis_pool = 0.5 %` of supply is not sized by the `reward_per_claim` ≥ `claim_fee` constraint, which 3.7×10⁻⁸ of supply would satisfy. Whatever justifies half a percent, it is not this floor, and §10.2's standing-reserve question is really a question about `genesis_pool` and its multi-decade decay rather than about `steady_pool`.

### 4.7.5 The reward controller is asymmetric

**Intuition.** If the opening puzzle is too easy, lots of people win immediately and the controller tightens fast, because every block tells it something. If it is too hard, almost nobody wins — and a block with no winners is nearly silent. Learning from silence is slow, so recovering from "too hard" takes two to three times as long as recovering from "too easy".

![reward controller](figures/05_reward_controller.png)

A mis-set genesis target recovers in about 20 blocks when it is too permissive and in 38 to 60 when it is too hard, because a too-hard target produces blocks with **zero** claims, and a block with no claims carries no information beyond the fixed `P/F` loosening step. §4.6's asymmetry — "too permissive over-pays, bounded; too hard costs only time" — is right in direction, and the time is longer than the permissive side by a factor of two to three.

### 4.7.6 Where the parameter set works

**Intuition.** Two things can go wrong, from opposite directions. Take too small a slice of fees and mining does not cover its own costs. Take too large a slice and mining stops being the junior earner alongside staking, which is not what this mechanism is for. A workable setting lives in the corridor between, and it is worth seeing how wide that corridor is.

![operating envelope](figures/06_operating_envelope.png)

Two independent walls bound `pow_share` from opposite sides, and the specified point sits between them. Below, `reward_over_fee < 1` and a claim earns less than its own fee. Above, `pow_share > 11.8 %` and mining stops being subordinate to the leader path. At the reference traffic the admissible band is **`pow_share in [4.0 %, 11.8 %]`** for a 2× fee margin, and the specified tenth sits in it — nearer the subordination wall than the funding one.

![drain margin](figures/07_drain_margin.png)

Draining the pool inside one epoch needs `T/distribution_rate` claims in every block for a whole epoch: 2,000 against a `MAX_BLOCK_TXS` of 1,024. **Since §0.4 the specified point is on the impossible side of that boundary, with 95 % headroom** — the block format itself forbids the required rate, up to a doubling of capacity. The map below is what motivated the change: the earlier `distribution_rate = 1/100` sat on the reachable side by 2.4 %, prevented only by the difficulty controller, and this report twice flagged that as the design's one controller-dependent guarantee. The guard remains, so any future constant change that reopened the path would degrade gracefully — claiming stops rather than the pool going negative.

![blend envelope](figures/08_blend_envelope.png)

The design target — about a minute of one core per message, of order a thousand messages a day — is met at `p/2¹⁹` **on the one-core basis the specification adopts**. On the whole-board basis the same threshold costs 12.3 s and falls out of the band; matching the target there would need `p/2²¹`. §10.1's open question "one core or the whole board?" is exactly those two exponents, and the figure is the argument for settling it explicitly rather than by default.

## 4.8 Sampled arrivals — A2, run `SIMULATED`

**Intuition.** Winners arrive at random, like raindrops: a block that averages ten might get six, or fifteen. The model so far has used the average everywhere, which raises a fair objection — does the randomness matter? Two places it might. It could make the pool's income lumpy. And it could, on a bad day, land so many claims at once that the pool empties early. The way to find out is to stop averaging and actually roll the dice, with the difficulty controller reacting as it would in production.

A2 replaces the arrival process with its mean and says so plainly: "the simulator uses the mean, not samples, so it understates variance." It also calls the `1 / sqrt(target_claims_per_block)` spread — **32 % at `target_claims_per_block = 10`** — "the whole quantitative case for a larger `target_claims_per_block`". That left the case argued but never tested, against a margin that is live: §3.8's drain guard sits 2.4 % under the block cap.

`make sampled` runs the mechanism block by block with Poisson arrivals and the **real memoryless retarget in the loop**, so the controller reacts to noise as it would in production. 1,036,800 blocks, four seeds × twelve epochs.

![sampled arrivals](figures/09_sampled_arrivals.png)

| | measured | predicted | |
| --- | --- | --- | --- |
| claims per block, mean | **10.0525** | 10.0500 | `target_claims_per_block + (smoothing_precision - smoothing_factor) / (2 * smoothing_precision)` |
| relative spread | **32.3 %** | 32.4 % | `sqrt(2 * smoothing_precision / ((smoothing_precision + smoothing_factor) * target_claims_per_block))` |
| — bare Poisson, what A2 quotes | | 31.6 % | `1 / sqrt(target_claims_per_block)` |
| controller amplification | **1.023×** | 1.026× | `sqrt(2 * smoothing_precision / (smoothing_precision + smoothing_factor))` |
| epoch total, relative spread | **0.0070 %** | | over 48 epochs |
| — if arrivals were uncorrelated | | 0.2152 % | `1 / sqrt(target_claims_per_block * blocks_per_epoch)` |
| busiest block in 1.04 M | **31** | | drain needs 2,000 |

**A2's number is right, and it does not reach the pool.** The per-block spread is 32.3 % against the 31.6 % A2 quotes; the controller widens it by 2.3 %, which is the AR(1) the retarget introduces on top of the arrival noise and is negligible.

**What stops it reaching the pool is not averaging, it is correction.** The retarget is an *integrator* on the cumulative claim count: a block that runs hot is answered by the blocks after it. Substituting the AR(1) into the epoch total, the arrival noise and the controller's response to it cancel term by term, leaving a spread that is **independent of epoch length**. Measured, an epoch's total lands within **0.0070 %** of its mean — **31× tighter than an uncorrelated Poisson sum of the same blocks**. So §3.1's mean-field pool model is on firmer ground than A2's caveat implies: the noise is not averaged away over 21,600 blocks, it is actively removed.

**The drain margin is not a sampling question.** The busiest block in 1.04 million was 31 claims, against the 2,000 per block the within-epoch drain needs, sustained for 7.5 days — **613 standard deviations away**. The pool guard never bound once. Since §0.4 the drain is impossible by construction, so this measurement is no longer load-bearing — but it was run when the margin was 2.4 % and controller-dependent, and it established that chance contributed nothing even then.

**One thing the mean-field model cannot see: the retarget overshoots its target.** The equilibrium claim rate is **10.05, not 10**. `target_claims_per_block` is the fixed point of the retarget applied to the *mean*, but the map divides by the observed count and is therefore convex, so under Poisson arrivals the rate drifts up until log-stationarity holds. Expanding to second order,

| **the retarget's equilibrium rate** |
| --- |
| $\lambda^\ast = T + \dfrac{P_\text{ema} - F_\text{ema}}{2P_\text{ema}}$ |
| `equilibrium_claim_rate = target_claims_per_block + (smoothing_precision - smoothing_factor) / (2 * smoothing_precision)` |
an **absolute** overshoot of 0.05 claims per block, so the relative one goes as `1/T`: **+0.50 % at `target_claims_per_block = 10`, +0.10 % at `target_claims_per_block = 50`**. Confirmed against simulation across `target_claims_per_block in {5, 10, 25, 50}` and `(smoothing_precision, smoothing_factor) in {(10,9), (10,8), (100,99)}`.

The consequence is small and one-signed: the pool distributes about half a percent more than §3.1 says, and every figure derived from the mean-field rate is high by that much at `target_claims_per_block = 10`. It is well inside the tolerances this document quotes. But it belongs on the ledger with the other costs of a small `target_claims_per_block` — the per-block variance A2 names, the builder edge of §4.2, and the drain margin of §3.8 — because like them it is a `1/T` effect, and unlike them it was invisible until the arrivals were sampled.

## 4.9 The working fee range — one axis instead of two `DERIVED`

**Intuition.** We have been describing traffic two ways at once: how many transactions a block carries, and how expensive each one is. But the pool takes a cut of the *money*, not of the count — and a claim's own cost rises with prices too. So doubling every price changes nothing real: the pool earns twice as much and the claim costs twice as much. The only thing that actually matters is **how much a block collects compared with what one claim costs**. That is one number instead of two, and it turns the question "is there enough traffic?" into a single threshold that needs no forecast of either prices or volumes.

This document carries traffic as a transaction count (`txs_per_block`, `UNKNOWN`, an adoption question) and the fee level as a separate unknown (A9, §5.1). **Neither is identified on its own, and the model never needed both.**

What the refill takes is a share of a block's fee *revenue*. What decides whether mining pays is that revenue against the claim's own fee — which moves with the price level too. The two scalings cancel, leaving one dimensionless quantity: a block's revenue counted in claim fees.

| **the collapsed fee axis** |
| --- |
| $\hat\Phi = \dfrac{\Phi_b}{\varphi} = \psi\, n_\text{tx}$ |
| `fee_load = block_fee_revenue / claim_fee  # == fee_ratio * txs_per_block` |
| $\dfrac{\sigma^\ast}{\varphi} = \dfrac{\beta\,\hat\Phi}{T}$ |
| `reward_over_fee = pow_share * fee_load / target_claims_per_block` |
Sweeping `fee_load` says everything the `(txs_per_block, price)` plane says, on one axis, without committing to a price level. And the working range reduces to a single number:

> **A block must collect `T/pow_share` claim fees for mining to fund itself — 100 at the specified set.**

![working fee range](figures/10_fee_range.png)

| `fee_load` (claim fees/block) | `reward_over_fee` | verdict | lepta/block at rest | ≈ `txs_per_block` at any price |
| --- | --- | --- | --- | --- |
| 25 | 0.25 | under water | 166,600 | 30 |
| 50 | 0.50 | under water | 333,200 | 60 |
| **100** | **1.00** | **break-even** `T/pow_share` | 666,400 | 119 |
| 200 | 2.00 | works, 2× margin | 1,332,800 | 239 |
| **502** | **5.02** | **specified** | 3,345,328 | 600 |
| 857 | 8.57 | full block | 5,711,048 | 1,024 |
| 2,000 | 20.00 | ample | 13,328,000 | 2,389 |

The specified set collects **502 claim fees per block against a break-even of 100** — the same 5.02× margin §4.3 derives, reached without an estimate of either traffic or price. Read as a count that is 600 ordinary transfers at the resting level; read as a price level it is anything at all. **That invariance is the substance, not a presentational convenience**: it is why §4.3's ratios survive a repricing, and why the "the on-ramp closes when the network is busiest" failure mode does not exist under fee funding. `make verify` checks it across five decades of price.

Two things this axis does better than the count.

**It removes a constant.** `fee_ratio` exists only to convert a transaction count into units of the claim fee. On the fee axis it is gone: `reward_over_fee = pow_share * fee_load / target_claims_per_block` needs `pow_share`, `target_claims_per_block` and nothing else. `fee_ratio` reappears only when a reader wants the last column of the table above.

**It is exact where the count form is not.** Pricing every transaction as an ordinary transfer understates the refill by 0.32 % (§4.7.2), because `target_claims_per_block` of them are claims paying more. Revenue per block makes no assumption about composition, so that correction disappears rather than being carried and apologised for.

### 4.9.1 What a load looks like as transactions

**Intuition.** The same amount of money in a block could be a handful of expensive transactions or a great many cheap ones. The natural worry is that a block full of the cheapest possible traffic would not raise enough. It turns out not to matter much: what moves the margin is how *full* blocks are, not what is in them.

A fee load is a revenue figure, so it maps to many mixes. A few, to make it concrete — not an inventory. Gas is the specification's (`analysis-gas-cost-determination.md`); the byte counts for the last two shapes are **assumed and illustrative**, since the model does not otherwise carry them.

| shape | bytes | gas | claim fees each | to break even | a full block of them |
| --- | --- | --- | --- | --- | --- |
| ordinary transfer | 207 | 590 | 0.837 | 119 | 857 |
| PoW claim (+ transfer) | 306 | 646 | 1.000 | 100 | 1,024 |
| SDP declare | *250* | 646 | 0.941 | 106 | 964 |
| channel inscribe (cheapest Operation) | *130* | 56 | 0.195 | 512 | 200 |

and some blocks:

| mix | load | `reward_over_fee` | |
| --- | --- | --- | --- |
| 600 transfers | 502 | 5.02 | the reference |
| 10 claims + 590 transfers | 504 | 5.04 | the realistic block — and the 0.32 % §4.7.2 flags, made concrete |
| a full block of transfers | 857 | 8.57 | |
| a full block of the cheapest Operation | 200 | 2.00 | |
| half a block, half inscribes | 264 | 2.64 | |

**The composition barely matters; the fill does.** A full block needs only `(target_claims_per_block / pow_share) / MAX_BLOCK_TXS` = **0.098 claim fees per transaction** to break even, which at the cheapest Operation's 56 gas is about **37 encoded bytes each** — smaller than any signed transaction can be, since the claim's signature alone is 128 B. So every full block clears break-even whatever is in it, and even a block filled entirely with the cheapest Operation lands at twice the floor. What moves the margin is how *full* blocks are, and the specified 5.02× corresponds to blocks a little under 60 % full of transfers.

That is the useful form of the answer to "what traffic does this need?": not a transaction count, and not a price, but **roughly half-full blocks**.

What the axis does *not* decide is `pow_share`, which is still walled from above by subordination (§4.7.6) — that constraint is on the share, not on the revenue, and no amount of fee income relaxes it.

## 4.10 The sweep programme, run `SIMULATED`

**Intuition.** Everything so far describes one parameter set. The natural next question is how much of it was luck: change a dial and does the picture hold, or was the specified point sitting on a knife edge? This runs §6's list — every axis, and in every cell the six things §6 asks for — so the answer is a table rather than an argument. `make sweeps-full`.

Three columns turn out to be **flat everywhere**, and that is a result rather than an absence of one:

- **Reconvergence is 22 blocks in every cell.** §3.6 predicted "~22" for a tenfold hashrate step from the pole `F/P`; the simulation gives exactly 22, and it does not move with `target_claims_per_block`, `pow_share`, `distribution_rate` or `genesis_pool`, because the controller's normalised dynamics contain none of them. (Recovery is asymmetric, as §4.7.5 shows: a tenfold step *down* takes 42 blocks.)
- **The security column does not move with `target_claims_per_block`.** An epoch distributes `distribution_rate * pool` whatever `target_claims_per_block` is — `target_claims_per_block` cancels out of `target_claims_per_block * blocks_per_epoch * reward_per_claim` — so the attacker's share is a property of the pool and the horizon, not of the claim target. This is §3.1's identity showing up where it should.
- **`reward_over_fee` does not move with `distribution_rate` or `genesis_pool`.** The steady state is `epoch_refill / (target_claims_per_block * blocks_per_epoch)`, which contains neither. §3.1's "`distribution_rate` sets the speed, never the destination" holds numerically.

### 4.10.1 The claim target

| `target_claims_per_block` | `reward_over_fee` | ramp cover | peak adv | builder edge | drain/block | break-even load | claim share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **10** (specified) | **5.02** | 135,949× | 0.42 % | **1.124×** | 2,000 | 100 | 1.7 % |
| 50 | 1.00 | 16,377× | 0.42 % | **109×** | 10,000 | 500 | 8.3 % |
| 100 | 0.50 | never | 0.42 % | n/a | 20,000 | 1,000 | 16.7 % |
| 500 | 0.10 | never | 0.42 % | n/a | 100,000 | 5,000 | 83.3 % |

(Since §0.4 the drain is out of reach at every `target_claims_per_block` shown: `target_claims_per_block / distribution_rate > MAX_BLOCK_TXS` from `target_claims_per_block = 6` up.)

**`target_claims_per_block = 50` lands almost exactly on break-even at the reference load, and that is where the builder edge explodes.** `reward_over_fee = 1.00`, and since the edge is `1 + tip_fraction / (reward_over_fee - 1)` it goes to **109×** — a builder recovering the tip on its own claims earns two orders of magnitude more than an outside miner. The edge is not a smooth cost of a larger `target_claims_per_block`; it is a pole, and `target_claims_per_block = 50` sits next to it. That is a sharper argument for the move to 10 than §4.2's, which put the earlier value's edge at 2.5× on a traffic assumption the current set does not carry.

Above 100 the mechanism is simply under water: `reward_over_fee < 1` at the reference load, no endowment covers an adoption ramp, and at 500 claims would need to be **83 % of every block**. When this sweep was first run at `distribution_rate = 1/100`, raising `target_claims_per_block` bought the one thing the specified set then lacked — `T/distribution_rate` passed `MAX_BLOCK_TXS` between 10 and 50, closing the within-epoch drain structurally — at the cost of everything else. **§0.4 took the other route to the same guarantee**: `distribution_rate` = 1/200 closes the drain at `target_claims_per_block = 10`, so a larger `target_claims_per_block` now buys nothing at all, and the specified 10 keeps its margin everywhere.

The two `1/T` effects run the other way and are small: arrival noise falls from 31.6 % to 4.5 % (§4.8's A2 case), and the retarget's overshoot from 0.50 % to 0.01 %.

### 4.10.2 The other axes

| axis | `reward_over_fee` | peak adv | builder edge | note |
| --- | --- | --- | --- | --- |
| `pow_share` 5 → 50 % | 2.51 → 25.12 | 0.42 % flat | 1.331 → 1.021× | linear in `pow_share`; the burn diversion *is* `pow_share` |
| `distribution_rate` 1/500 → 1/50 | 5.02 flat | 0.35 → 0.54 % | 1.124× flat | only the drain moves: 5,000 → 500 per block; **1/200 specified** |
| `genesis_pool` 0.5 → 10 % | 5.02 flat | **0.42 → 6.79 %** | 1.124× flat | the one axis where generosity costs security |
| ramp 1 → 10 yr | — | — | — | endowment needed 1.59 → 4.19 ×10⁻⁸ of supply |
| `initial_stake` 0.5 → 30 % | — | **14.4 → 0.42 %** at `adversary_hashrate = 0.33` | — | dominates the security answer, as §4.1 says |

**`genesis_pool` is the only dial that trades generosity against security**, and §6 anticipated exactly that. Ten times the endowment is roughly sixteen times the attacker's peak share (0.42 % → 6.79 % at `adversary_hashrate = 0.33`, `initial_stake = 30 %`), because a larger pool is distributed faster in absolute terms and so more of it can be mined inside the horizon. Nothing else on the list moves it. That sharpens §10.2's open question about the size of `genesis_pool`: the cost of a larger endowment is not dilution, it is bootstrap security.

And `initial_stake` still dominates everything: at `adversary_hashrate = 0.33` the peak runs 14.4 % at a half-percent of supply staked against 0.42 % at the 30 % staking target — a factor of thirty, against the factor of sixteen `genesis_pool` buys across its whole range.

## 4.11 `target_claims_per_block` and `pow_share` are one dial, not two `DERIVED`

**Intuition.** The claim target and the fee share look like independent knobs, and §4.4.1, §4.4.2 and §4.10 sweep them as if they were — each holding the other fixed. They are not. Halving how many winners share the pot and halving the pot are the same thing to a miner, so what the economics sees is only the *ratio*. Everything that decides whether mining pays is unchanged along that ratio. What is *not* unchanged is the two separate walls: the drain margin wants `target_claims_per_block` large, and subordination wants `pow_share` small. Those walls are what pick a point on the ray, and they leave a surprisingly short stretch of it.

Every quantity in §4.3's constraint set contains the two only as `T/pow_share`:

| **what the ratio T/β fixes** |
| --- |
| $\dfrac{\sigma^\ast}{\varphi} = \dfrac{\hat\Phi}{T/\beta}$ |
| `reward_over_fee = fee_load / (target_claims_per_block / pow_share)` |
| $\text{break-even load} = \dfrac{T}{\beta}$ |
| `break_even_load = target_claims_per_block / pow_share` |
| $\text{builder edge} = 1 + \dfrac{\text{tip}}{\sigma^\ast/\varphi - 1}$ |
| `builder_edge = 1 + tip_fraction / (reward_over_fee - 1)` |
so along `target_claims_per_block/pow_share = 100` the margin is 5.02, the edge 1.124× and the break-even load 100 claim fees — at `target_claims_per_block = 5, pow_share = 5 %` exactly as at `target_claims_per_block = 50, pow_share = 50 %`.

![the T–`pow_share` plane](figures/11_T_beta_plane.png)

**What breaks the degeneracy.** Three things bind `target_claims_per_block` or `pow_share` alone, and only one of them is not already comfortable at the specified point:

| binds | quantity | at `target_claims_per_block = 10, pow_share = 10 %` |
| --- | --- | --- |
| `target_claims_per_block` alone | within-epoch drain, `T/distribution_rate` vs `MAX_BLOCK_TXS` | 1,000 vs 1,024 — **reachable** |
| `target_claims_per_block` alone | arrival noise `1 / sqrt(target_claims_per_block)`, retarget overshoot `(smoothing_precision - smoothing_factor) / (2 * smoothing_precision * target_claims_per_block)` | 31.6 %, 0.50 % |
| `pow_share` alone | subordination, PoW ≤ ⅓ of the leader share | 27.8 % of the cap |
| `pow_share` alone | standing reserve `steady_pool` ∝ `pow_share`; floor `pool_floor` ∝ `target_claims_per_block` | 1,446 and 288 LGO |

Moving *up* the ray raises `target_claims_per_block`, which is what pushes the drain out of reach — it becomes impossible by construction once `target_claims_per_block > MAX_BLOCK_TXS * distribution_rate`. At the original `distribution_rate = 1/100` that threshold was 10.24, just above the specified `target_claims_per_block = 10`; subordination capped the ray at `target_claims_per_block <= 11.76`. So, as first found:

> **At `distribution_rate` = 1/100 the window that kept the economics *and* closed the drain was `target_claims_per_block in (10.24, 11.76]` — one whole number, `target_claims_per_block = 11`.** §0.4 discharged it from the other side: at `distribution_rate` = 1/200 the drain-safe threshold falls to `target_claims_per_block > 5.12`, the window becomes `(5.12, 11.76]`, **and the specified `target_claims_per_block = 10` already sits inside it.** The (11, 11 %) move is moot rather than rejected.

The route mattered even so. At `target_claims_per_block = 11, pow_share = 11 %` the economics would have been bit-for-bit the same while the drain needed 1,100 against 1,024 — closed, but by 7.5 %, and re-opening at any block-capacity increase past 1,100. The `distribution_rate` route closes it at 2,000, holds to a full doubling of capacity, spends no subordination headroom, and improves bootstrap security besides (§0.4). Choosing between two routes to the same structural guarantee is exactly what this section's degeneracy analysis exists for.

**This is offered as an observation, not a recommendation.** §3.8 argues the drain is adequately prevented by the controller, and §4.8 confirms that arrival noise contributes nothing to reaching it — a burst would have to be 305 standard deviations. So nothing here says the specified set is unsafe. What it says is that the one structural gap the report flags twice (§3.8's "the margin is thin", §4.7.6's "a controller guarantee and not a structural one") appears to be closeable **for free**, by moving one unit along a direction the economics cannot see. That is worth knowing before the constants are frozen, and it is exactly the kind of thing sweeping `target_claims_per_block` and `pow_share` independently cannot reveal.

**The upper wall, stated without the assumption.** The subordination cap is `pow_share <= subordination_ratio * leader_fee_share / (1 + subordination_ratio * leader_fee_share)` for a leader fee share `leader_fee_share` and a juniority ratio `subordination_ratio`. A search of the specification tree finds **no leader-share constant anywhere** — `POW_SHARE`/`SHARE_DEN` are the only fee-share constants it defines — so `L` cannot be grounded, and the 11.76 % cap it implies is a modelling choice rather than a derived bound.

That is worth stating, but it does not leave the finding conditional, because the wall can be written in the specification's own units instead. Along the ray, `target_claims_per_block = 11` **is** `pow_share = 11 %`. So:

> **The move is available if and only if `POW_SHARE = 11` is acceptable instead of 10.**

That is a one-percentage-point policy question about a constant the specification already defines, not a question about an unspecified fee split. Whatever `L` turns out to be, it enters only by deciding whether 11 % is still "junior" — and at the assumed `leader_fee_share = 0.4` it is (30.9 % of the leader share, against a ⅓ cap). The `[economics]` values are configured so that reading can be re-tested when the split is pinned down: at `leader_fee_share = 0.5` the cap is 14.3 %, at `leader_fee_share = 0.3` it is 9.1 % and 11 % would be too much.

This is also why `L` belongs in §10.1's list of unset constants rather than buried in a simulator default. (And note the cap is a steady-state statement in a second sense too — §4.4.2's flow comparison: during the endowment's decay, PoW out-earns the leader *fee* flow by four orders of magnitude, and launch-era proportionality rests on the leaders' minted income.)

The window is also a warning in the other direction: it is *short*. Any future change that raises `target_claims_per_block` without raising `pow_share`, or lowers `pow_share` without lowering `target_claims_per_block`, moves off the ray and costs margin directly. The two constants should be revisited together or not at all.

## 4.12 What sizes `genesis_pool` `DERIVED`

**Intuition.** §4.4 sizes the endowment by asking "is it big enough to keep mining worth doing while traffic grows?" — and the answer is yes by a factor of two hundred thousand, which means that question did not choose the number. Something else did. Inverting each candidate objective for the `genesis_pool` it would imply says which.

| objective | implied `genesis_pool`/supply | vs the specified 0.5 % |
| --- | --- | --- |
| hold `reward_per_claim >= claim_fee` across a 5-year ramp (§4.4) | 2.39×10⁻⁸ | 0.0000× |
| hold `reward_per_claim >= claim_fee` across a 10-year ramp | 4.19×10⁻⁸ | 0.0000× |
| sit at the fee-funded fixed point `steady_pool` | 7.23×10⁻⁸ | 0.0000× |
| keep the pool above `pool_floor` from epoch 0 | 1.44×10⁻⁸ | 0.0000× |
| open at `opening_reward_over_fee` = 100 | 1.44×10⁻⁶ | 0.0003× |
| **distribute ~0.5 % of supply over the 6.2-year horizon** | **6.4×10⁻³** | **1.29×** |
| **cap the peak adversary share at 0.5 %** (`adversary_hashrate = 0.33`, `initial_stake=30 %`) | **5.94×10⁻³** | **1.19×** |
| cap the peak adversary share at 1.0 % | 1.19×10⁻² | 2.38× |

**Every reward-economics objective misses by five or six orders of magnitude.** The floor, the ramp, the fixed point and any plausible opening reward all sit near 10⁻⁸ of supply. None of them chose 0.5 %.

**The two that land on it are the same constraint seen twice.** Over the 300-epoch horizon the pool pays out `(1 - (1 - distribution_rate)**epochs)` of its endowment — 78 % of it at the adopted `distribution_rate` = 1/200 — so "distribute half a percent of supply to miners over six years" and "`genesis_pool` = 0.5 % of supply" are nearly the same statement. And the peak adversary share follows directly: an attacker with hashrate `adversary_hashrate` takes `adversary_hashrate` of what is distributed, against the stake already securing the chain, so

| **peak adversarial stake share** |
| --- |
| $\text{peak} \approx \dfrac{h \cdot (\text{distributed}/S)}{D_0} = \dfrac{0.33 \times 0.39\,\%}{30\,\%} \approx 0.43\,\%$ |
| `peak_adversary_share = adversary_hashrate * (distributed / launch_supply) / initial_stake` |
which is the 0.42 % §4.1 measures. **So `genesis_pool` is a distribution budget, and its binding consequence is a security one.** The right question about it is not "is it large enough for the mechanism to work" — it is enormously large enough — but "is half a percent of supply the intended bootstrap subsidy, given that it lands a one-third attacker at ~0.4 % of stake?"

That is a policy question, and §10.2 should ask it in those terms. It also explains §4.10.2's finding that `genesis_pool` is the only dial trading generosity against security: it is the *only* one of the six axes that moves the distributed amount at all, because §3.1's identity removes `target_claims_per_block` and `blocks_per_epoch` from the pool dynamics and `distribution_rate` sets only the speed.

**What this does not settle.** Whether 0.5 % is right depends on the token allocation as a whole, which is outside this model. What the model can say is the exchange rate: **each additional 0.5 % of supply in the endowment adds about 0.4 % to a one-third attacker's peak share of stake at the 30 % staking target**, and roughly ten times that if only 5 % of supply is staked. §4.10.2's table is that trade priced across the range.

## 5. Simulator

The `empowering` package in `simulations/EmPoWering/`, one module per concern and one `make` target per report section: `make fee` (the claim's fee, §4.3), `make emission` (§3.4), `make rewards` (§4.3–§4.4), `make blend` (§4.5), `make exhaustion` (§3.8, §4.6), `make security` (§4.1), `make volume` (§4.7.2), `make sweeps` (§4.4.1–§4.4.3) and `make plots` (§4.7). Every number lives in `configs/specified.toml`, annotated KNOWN / DERIVED / MEASURED / ASSUMED with citations into the specification tree; nothing is hardcoded in the modules, so a specification change is a one-line edit. `make lepta` re-runs the mechanism in exact integer arithmetic at lepton granularity; `make check LIPS=…` compares the config against the specification tree, constants and prose margins alike. Mirrors the merged code, not the proposal.

### 5.1 The denomination, and what it is not `OPEN`

**Settled by §0.1** at 1 LOGOS = 10⁹ lepta; this section records the reasoning from when it was open. `uint64` caps it at `1.84×10¹⁹` lepta against a `10¹⁰` LGO supply, which is the bound the settled value respects. What EmPoWering needs from it is in §4.4.4 and in the specification: the bound above, and that one LGO cannot itself be the smallest unit.

**An earlier revision of this section, and of §4.4, called the undefined denomination "the single quantity standing between the model and a numeric recommendation". That was wrong**, and §4.4.4 sets out why. The denomination fixes representability and granularity; what a transaction *costs* is the price level the two fee markets are initialised at and then discover. Every figure this document states in LGO is unaffected by the denomination. The quantity that was actually missing is the **launch fee level**, which remains a genesis governance decision — now expressed as a target it must hit rather than an unknown blocking everything (§4.4.4).

The simulations use `claim_fee = 0.952` LGO throughout. That is a **price-level assumption**, equivalent to both markets opening at `10⁵` base units per unit of gas. It is not a consequence of the denomination, and every ratio in §4.3 is independent of it.

### 5.2 Validation — run and passing

Re-run 2026-08-11 under fee-inflow funding, at the §3.7 parameter set.

| Check | Result |
| --- | --- |
| Tracks the §3.1 closed form | ✅ worst error **2.2×10⁻⁴** (win-count rounding, not currency flooring) |
| At target, difficulty unchanged | ✅ exact |
| Pool never negative | ✅ min 205,960,458 LGO over 300 epochs |
| Steady state matches the closed form | ✅ R\*=206,536,781 LGO, $\sigma$\*=1.9124 LGO |
| Self-funding holds | ✅ $\sigma$\*/$\varphi$ = 2.009 |

## 6. What to sweep

| Axis | Values | Why |
| --- | --- | --- |
| ~~base units per LGO~~ | ~~1, 10³, 10⁶, 10⁹~~ | settled at 10⁹ by §0.1; no longer an axis |
| `pow_share` | 5 %, 10 %, 20 %, 33 %, 50 % | sets $\sigma^\ast/\varphi$, hence self-funding, the endowment and the builder edge |
| `txs_per_block` ramp | 1, 2, 5, 10-year horizons | the endowment must cover the ramp, superlinearly (§4.4) |
| `genesis_pool`/supply | 1 %, 2 %, 5 %, 10 % | generosity vs **§4.1's security bound** |
| `distribution_rate` | 0.5 %, 1 %, 2 % | speed only, never destination — but it scales `pool_floor` inversely |
| `initial_stake` | 0.5 %, 5 %, 30 % | honest stake at launch — **§4.1 shows this dominates security** |

**This programme is now run — see §4.10** (`make sweeps-full`), which reports every cell on every axis. `target_claims_per_block` is swept there too, over {10, 50, 100, 500}: the specification sets 10, but the consequences of the earlier values are worth seeing rather than asserting, and §4.10.1 finds a pole in the builder edge next to `target_claims_per_block = 50` that the prose estimate had missed.

**Report per cell:** `reward_over_fee`; whether the ramp is covered and with what margin; peak attacker share and the §4.1 asymptote; builder edge at steady state (§4.2); blocks to reconverge after a 10× hashrate step (§3.6 predicts ~22); the fraction of fee revenue diverted from the burn (§3.4).

## 7. What this model does not capture

Traffic and the fee level are exogenous (A5, A9), so the model cannot say when adoption arrives — only what happens at each level of it, which is why §4.4 has to be read as a family of answers indexed by the ramp. Free entry with one cost (A3, A4) makes hashrate a floor. Randomness is replaced by its mean, understating variance. `initial_stake` is held fixed while mining accumulates, which is what produces §4.1's spurious asymptote. And **the feature ships switched off**, so every number is counterfactual.

## 8. Epistemic register

**Known.** The dynamics of §2, verified against `ledger/src/mantle/pow/` and `core/src/mantle/ops/pow.rs`; the fixed constants; that the feature is inert.

**Assumed.** Ten models (§2.6). Highest risk: A3 (fails in bootstrap), A5 (linear in the result), A8 (now quantified by §4.2). A9's risk dropped from high to medium when the funding source changed, because the fee now appears on both sides.

**Needs validating.** Stochastic controller behaviour (the simulator uses means); step response; the bincode framing behind §4.3's 306-byte figure, which was reasoned from the payload definitions rather than measured; that the transcription matches the running ledger — a test vector reproducing §3.7 would settle it.

**Unknown.** The launch fee level, i.e. what genesis governance initialises the two market prices to — this is what §4.4's table was really varying, and §4.4.4 restates it as a ceiling governance must hit rather than an open unknown. `cost_per_guess`. The adoption rate, which §4.4 handles by parameterising rather than guessing.

**Open.** Whether a tenth of fee revenue is the intended scale of the programme, given that in the mature network it comes out of Blend and leader funding rather than out of the burn (§4.4.2) — a policy judgement the model can frame but not make. Whether a standing reserve of about 1 % of supply, held permanently out of circulation, is acceptable (§4.4.3). And the denomination, which `genesis_pool` now constrains from below rather than merely depending on.

**Settled.** `target_claims_per_block = 10`, `pow_share = 10 %`, `distribution_rate = 1/100`, `genesis_pool = 0.5 %` of launch supply (§4.4.1–§4.4.3); the four Blend controller constants and its genesis value (§4.5); the reward controller's smoothing and genesis target (§4.6). **Every parameter EmPoWering introduces now has a value.** What remains is listed in §10. §3.1, §3.2, §3.4, §3.6 in closed form; §4.1, §4.2 and §4.4 by simulation; `claim_fee` up to the denomination (§4.3).

## 9. Candidate changes — NOT part of the base

Not used in §§1–8. Held above the line until the base is approved.

1. **Align the implementation's `target_claims_per_block`.** The specification now says 50; the merged code ships 100 and the proposal said 10.
2. **The stranded reserve** `steady_pool = epoch_refill / distribution_rate`, never distributed (§3.3). Much less pressing under fee funding, where the endowment can be sized *at* `steady_pool` rather than far above it (§3.7), so nothing is stranded in the first place.
3. **The `reward_per_claim = 0` cliff** — claiming stops dead rather than degrading (§2.3).
4. **Make "the endowment comes from existing supply" enforceable**; §3.4 depends on it entirely and it is currently only prose.
5. **A difficulty floor of 1** — closes the absorbing state at zero (§3.6). Unreachable in practice; free.
6. *(folded into item 11 below)*
7. **Endogenise traffic** (A5, A9) — the refill now moves with usage, so an adoption model would replace §4.4's family of ramps with a single answer.
8. **Make the target claim rate a fraction of transaction volume** rather than an absolute count. **Intended for a future revision** — deferred 2026-08-11 in favour of keeping the specification simple and aligned with the implementation, which uses an absolute count. `target_claims_per_block = 10` is specified for now (§4.4.1).

   **For.** It scales throughput with usage and makes steady-state self-funding load-independent: with `target_claims_per_block = ratio * txs_per_block`, the count cancels and `reward_over_fee = fee_ratio * pow_share/ratio`, so the condition is simply `pow_share > ratio/fee_ratio` at every level of traffic. Under fee funding this is a stronger argument than it was: it also makes the *endowment* requirement independent of the adoption ramp, dissolving §4.4's superlinear penalty for slow adoption, because a quiet network mints proportionately fewer claims.

   **Against.** §3.1's clean drain result is lost, since the pool becomes sensitive to the *rate of change* of usage. A zero target is an absorbing state needing a floor. §3.6's fixed-point analysis assumes a fixed reference. And it couples issuance to congestion, since claims compete for the space that sets their own allowance.

   **If adopted**, the ratio and `pow_share` are locked together by `reward_over_fee = fee_ratio * pow_share/ratio`: a 5 % ratio needs `pow_share ≈ 12 %` for the §4.2 headroom.
9. **Keep `reward_over_fee` above ~2** (§4.2) — below that the builder edge grows sharply while the on-ramp margin thins. Under fee funding this is a permanent property rather than an end-state one, so it binds from launch.

10. *(resolved 2026-08-11 — `target_claims_per_block` was moved from 50 to 10; the analysis is now §4.4.1 rather than a candidate change.)*

11. *(resolved 2026-08-11 — the denomination is specified at `10⁸`, and §4.4.4 shows it was not in fact the blocker this item claimed. What remains is the launch fee level, which is a genesis governance decision with a stated ceiling rather than an open question.)*

## 4.5 The Blend admission threshold `DERIVED` + `OPEN`

The four constants of the Blend difficulty controller, from `make blend`. This governs admission to the privacy layer rather than minting, so nothing here touches §§3–4.4; it is the other half of what EmPoWering does.

| **the Blend admission threshold** |
| --- |
| $\text{target} = \dfrac{\texttt{BLEND\_DIFFICULTY\_BASE}}{\text{load}^{\alpha}}$ |
| `blend_target = BLEND_DIFFICULTY_BASE / load**damping` |
| $\text{load} = \dfrac{\text{observed txs per block}}{\texttt{TARGET\_TXS\_PER\_BLOCK}}$ |
| `load = observed_txs_per_block / TARGET_TXS_PER_BLOCK` |
**Three of the four have anchors already in the tree.**

`TARGET_TXS_PER_BLOCK = 512`, half of `MAX_BLOCK_TXS`, mirroring the execution market's target of half its per-block gas limit. Defining the reference load any other way would leave the two markets disagreeing about what "busy" means.

`α = 1/2`, as `BLEND_DAMPING_NUM = 1` over `BLEND_DAMPING_DEN = 2`. The specification already argues for this: quadrupling the load only doubles the threshold, so each attacker-funded transaction buys less effect than the last at the same cost.

`BLEND_MAX_STEP = 2`. At `α = 1/2` a factor of two in the threshold is a factor of four in load, so the clamp does not bind on ordinary variation. A sustained hundredfold load change is tracked over four epochs — a month.

**The fourth has no anchor, and that is the finding.**

`BLEND_DIFFICULTY_BASE` fixes what a message *costs*, and nothing in the tree states that. The obvious approach is parity with the other two quotas — make a solution cost about what the stake or leadership path costs per message — and **it cannot be done today**: $Q_C = C(\beta_C + R_C \beta_C)/N$ needs `F_C` and `N`, and $Q_L = \beta_D(1 + R_D)$ needs `R_D`, none of which has a value anywhere. Parity is the right anchor in principle and unavailable in practice; it should be revisited when those land.

So it is derived instead from the work itself — **measured**, in `bench-poseidon2/`, against the real `logos-blockchain-poseidon2` crate.

**What the measurement changed.** A candidate is two `zkhash` calls, and an earlier revision of this section costed that as two Poseidon2 invocations at an assumed 2 μs. Both halves were wrong. `Digest::digest` absorbs every input *and* a padding element through a width-3 sponge, so a two-input hash is **three permutations, not one** — six per candidate. And one permutation measures **3,350 ns**, not 2,000. The estimate was between four and six times too fast.

| | measured | per second |
| --- | --- | --- |
| one permutation | 3,350 ns | 298,536 |
| `zkhash` of 2 inputs | 11,582 ns | 86,339 |
| **candidate, naive (6 perms)** | **23,346 ns** | **42,833** |
| candidate, prefixes precomputed (4 perms) | 16,481 ns | 60,677 |

(Apple M4 Pro performance core, release build with LTO.) The constant first input of each hash — the `KDF` tag, and the epoch nonce, fixed for the epoch — can be absorbed once and reused, which is the only algorithmic optimisation available and worth just **1.40×**.

Re-derived on those numbers:

| threshold | expected candidates | one core | msgs/day, 1 core | msgs/day, 10k cores |
| --- | --- | --- | --- | --- |
| `p/2²⁰` | 1,048,576 | 24.5 s | 3,529 | 35 M |
| **`p/2²²`** | **4,194,304** | **97.9 s** | **882** | **8.8 M** |
| `p/2²⁴` | 16,777,216 | 6.5 min | 221 | 2.2 M |
| `p/2²⁶` | 67,108,864 | 26.1 min | 55 | 0.55 M |

**`BLEND_DIFFICULTY_BASE = field_modulus / 2**22`.** The design target was unchanged — about a minute of one core per message, of order a thousand messages a day — but measurement moves it two exponents down from where the estimate put it. Below about `2²⁰` the work stops being a meaningful cost; above about `2²⁶` a participant on one core manages a message every half hour, which is not an on-ramp.

#### The reference machine is not the target machine

**Measured on an Apple M4 Pro. Deployment targets a Raspberry Pi 5.** Those are not close: four Cortex-A76 cores at 2.4 GHz against an M4 Pro performance core at roughly 4.4 GHz with much higher IPC on the 64×64→128 multiply-and-carry sequences BN254 arithmetic consists of. Clock explains about 1.8× of the gap and microarchitecture the rest, putting the band at **four to eight times slower per core**. That is an estimate; it has not been measured.

| threshold | M4 Pro | Pi 5 @4× | Pi 5 @6× | Pi 5 @8× | msgs/day, 1 Pi 5 core @6× | all 4 cores |
| --- | --- | --- | --- | --- | --- | --- |
| `p/2¹⁹` | 12 s | 49 s | 73 s | 98 s | 1,176 | 4,706 |
| `p/2²⁰` | 24 s | 98 s | 2.4 min | 3.3 min | 588 | 2,353 |
| **`p/2²²`** (specified) | **98 s** | **6.5 min** | **9.8 min** | **13.1 min** | **147** | **588** |

**The specified `p/2²²` meets the design target on the machine it was measured on and overshoots it five- to eightfold on the machine it is for.** A message costs closer to ten minutes than to ninety seconds, and a participant with one Pi 5 core sends 147 messages a day rather than 882. Matching the intended cost on one Pi 5 core puts the threshold near `p/2¹⁹`; on all four cores, near `p/2²¹`.

**Two decisions follow, and neither is made here.** Whether the reference is one core or the whole board — a factor of four. And the threshold itself, which should be re-derived against a measurement on the target hardware rather than against the scaling estimate above. `bench-poseidon2/` runs on the Pi as it stands.

**What else remains unmeasured.** One implementation, no assembly and no batching. More importantly for §4.5.1, the 1.40× above bounds only the *algorithmic* headroom — implementation headroom from assembly field arithmetic, batching or GPU is not measured and could be considerably larger, which would widen an adversary's advantage over an honest participant beyond what that figure suggests. Note that this cuts the opposite way from the hardware gap: the honest participant is on the slowest plausible machine and the adversary on the fastest.

### 4.5.1 What the threshold cannot do

It sets a **price per message, not a ceiling on the rate**:

| | messages/second |
| --- | --- |
| one laptop core | 0.010 |
| one 64-core server | 0.65 |
| 10,000 cores | 102 |
| 1,000,000 cores | 10,212 |

Against an honest data-message rate of `F_D = 1/30` per round — **0.033 messages a second network-wide**, one per block.

So a resourced adversary exceeds the honest rate by four to six orders of magnitude, **at any threshold cheap enough to be an on-ramp**. Raising it to prevent that puts the on-ramp out of reach of the people it exists for and still does not bound an adversary willing to spend more. This is not a calibration failure; it is the structural property `blend-protocol.md:659` already states — *"The rate at which this branch admits messages cannot be bounded in the way the other two are."*

What bounds the damage sits elsewhere, and all three are in this PR: proof-of-quota verification **before** relaying rather than after, so an invalid message dies at the first hop; the nullifier cache sized against `d_blend` rather than a node count; and the flood costing energy continuously for as long as it runs. **The difficulty sets the price. It cannot set a ceiling, and the specification now says so rather than implying the controller is a flood defence.**

## 4.6 The reward controller's smoothing and genesis target `DERIVED` + `SIMULATED`

The last two unset constants, and both turn out to be low-stakes for the same reason: they seed a controller that re-derives its target every block.

**Smoothing: `smoothing_factor = 9`, `smoothing_precision = 10`.** The same ratio the execution market uses. §3.6 showed the response has slope `F/P` at the target — below one, hence stable, with a time constant of about ten blocks — and slope `P/F` at zero claims, above one, so the no-claims state repels rather than traps. **Both signs hold for any `smoothing_factor < smoothing_precision`**, so the pair chooses response *speed*, not stability. Nine in ten places the response an order of magnitude slower than the block rate: fast enough to track a hashrate change within minutes, slow enough that one unusual block barely moves the target. It also matches what the merged code ships, so this is transcription with a reason attached rather than a fresh choice.

**Genesis target: `p/2²⁶`.** What matters here is not the value but the **asymmetry of being wrong**, simulated against the actual controller:

| genesis target vs. correct | blocks to within 10 % | excess claims paid | cost |
| --- | --- | --- | --- |
| 100× too permissive | 20 | 1,243 | ~2,900 LGO |
| 10× too permissive | 19 | 267 | ~620 LGO |
| 10× too hard | 38 | 0 | nothing |
| 100× too hard | 60 | 0 | nothing |

Against a pool of `5×10⁷` LGO, even the worst row is **0.006 % of the endowment**. Being too permissive over-pays a little; being too hard costs only time, because with no claims arriving the target rises by `smoothing_precision / smoothing_factor = 1.11` each block and a hundredfold error corrects within an hour.

Since one direction costs tokens and the other costs minutes, **the genesis value is set on the hard side.** At `p/2²⁶` a solution is about twenty-five minutes of one core (§4.5's measurement), so hitting the target claim rate needs some **five hundred cores** of honest mining network-wide — deliberately more than a launch is likely to attract, so the controller's first move is to loosen. It is set independently of, and more conservatively than, the Blend threshold, because the two answer different questions: one is a price participants live with, the other only a seed the controller corrects within the hour.

## 10. What is still to be settled

Audited against the branch on 2026-08-11. The reward economics are complete; what remains is in four groups, and only the first two block the proposal.

### 10.1 Unset constants, in the specification `OPEN`

| Constant | Where | State |
| --- | --- | --- |
| `EMA_SMOOTHING_FACTOR` (F), `EMA_SMOOTHING_PRECISION` (P) | Mantle, *Reward Difficulty* | **Set** to 9 and 10, matching the execution market's EMA and the merged code. §3.6's signs hold for any `smoothing_factor < smoothing_precision`, so the pair sets response speed rather than stability |
| `difficulty_reward` genesis value | Mantle, *Reward Difficulty* | **Set** to `p/2²⁶`, deliberately on the hard side — see §4.6 |
| `BLEND_DIFFICULTY_BASE`, `TARGET_TXS_PER_BLOCK`, damping ratio α, `BLEND_MAX_STEP` | Mantle, *Blend Difficulty* | **Set** — §4.5. Three from anchors already in the tree, the fourth from the work cost, resting on an unmeasured hash rate |
| `difficulty_blend` genesis value | Genesis Block | **Set** to `BLEND_DIFFICULTY_BASE` |
| Poseidon2 throughput on the **target** hardware | `bench-poseidon2/` | **Measured on an M4 Pro, but deployment targets a Raspberry Pi 5** — estimated 4–8× slower per core. At the middle of that band the specified threshold overshoots its design target fivefold (§4.5). Re-run on the Pi and re-derive |
| Reference machine: one core or the whole board? | — | A factor of four in the threshold, undecided |
| Leader fee share `L` | — | **Unset, and nowhere in the tree.** `POW_SHARE`/`SHARE_DEN` are its only fee-share constants. `L` fixes how much PoW share counts as "junior" (§4.4.2, §4.11); the model assumes 0.4. Only needed to *interpret* a `POW_SHARE` value, not to compute one |

The first two rows are small and mechanical. The Blend group is now set but rests on the last row.

### 10.2 Decisions the model can frame but not make `OPEN`

**Is a tenth of fee revenue the intended scale?** §4.4.2 shows that in the mature network the diversion is borne by the Blend service and the leaders one for one, not by the burn. A tenth leaves mining at 28 % of the leader share. Whether that is the right size for a bootstrapping mechanism is a policy judgement.

**Is half a percent of supply the intended bootstrap subsidy?** §4.12 shows that no reward-economics objective picks `genesis_pool = 0.5 %` — the floor, the ramp and the fixed point all sit near 10⁻⁸ of supply, so the endowment is over-provisioned for its stated purpose by five orders of magnitude. What does pick it is a distribution budget, and its binding consequence is security: at the adopted `distribution_rate` = 1/200 about 0.39 % of supply is distributed over six years, landing a one-third attacker at ~0.42 % of stake at the 30 % staking target. The question is therefore about the token allocation and the security appetite, not about viability.

**The launch fee level.** Genesis governance initialises both market prices. The constraint is `claim_fee <= 1.157 * 10⁻¹⁰` of the launch supply for the specified endowment to open at twice the fee — comfortably satisfied at the denomination now set, but it should be checked against the prices actually chosen rather than assumed.

### 10.3 Deliberately out of scope for this revision

Recorded so they are not mistaken for oversights. **ASIC resistance and the Equi-X transition**, and **splitting the two proof of work designs** — both excluded by decision; the same construction is reused for admission and for minting for now. **Making the claim target a fraction of transaction volume** (§9 item 8) — analysed, deferred, and now a weaker case than it was, since `target_claims_per_block = 10` removed most of what it would have bought.

### 10.4 Not settled by specification at all

**Implementation.** The feature ships inert: `PowInputs::unwired_placeholder()` returns zeros at every production call site, so the Blend proof of work branch is unprovable, and there is no `provers/pow`, no `d_blend` controller, no pre-relay verification, no transaction payload variant. The specification leads the code here throughout, and §9's list is the delta.

**A Phase 2 ceremony.** The Proof of Quota circuit changed, so the trusted setup must be re-run before deployment. Operational, with real lead time, and on nobody's critical path yet.

**Benchmarks.** No proof of work branch benchmark exists, and the two published figures are not like-for-like (different statistic, sample count and thread range). Since all three branches are evaluated for every proof, per-proof cost is not expected to differ by branch — but that has not been measured.
