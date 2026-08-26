# Validating the fork-loss claims in `analysis-total-stake-inference.md`

*A section quantifying what uncle references buy — § **Effect of Uncle References on Honest Slot Utilization** — was added to `docs/blockchain/raw/analysis-total-stake-inference.md` on the `analysis-fork-loss-in-tsi` branch of `logos-lips` (commit `d6fd7648`), produced by a quick standalone simulation. Several of its numbers conflict with [the TSI report](README.md) in this folder, which comes from a per-node network simulator. This document settles each claim at the **deployed spec's own operating point** — the one cell neither the section nor the report measured directly — and gives the numbers the section should carry.*

*Measurements: `tools/simulators/tsi/tsi-sim-pernode`, run 2026-08-06 against spec revision `d6fd7648`. Every figure below is reproducible from a committed script or config; sources are named per experiment and collected at the end.*

---

## Verdict

**The section's headline is wrong by ~17×, and it is concerned with the wrong bias.** The residual it attributes to deep forks is 0.08 pp, not 1.4 %. Meanwhile the deployed estimator carries a **+1.0 % bias of the opposite sign** that the section does not mention — from the on-chain rounding of `f`, not from forks. Rewriting the section around the second number rather than the first is the substantive change.

The no-uncle loss is also **understated, not overstated**: 33 % at the operating point, not 18.7 %, and it deepens with network size. The section undersells what uncle references buy by roughly half.

**But the section's number is not an arithmetic error, and experiment 5 identifies what it is.** It is what this model produces once *per-recipient* delay spread reaches ~8 slots — about 16× what Blend's cascade actually delivers. The cascade's variance is per **block** (every recipient moved together, harmless to the estimate); the standalone simulation's was per **recipient** (divergent, and the only kind that manufactures unrecoverable forks). That distinction is the whole disagreement, and it belongs in the rewritten section.

## Summary of measurements

```
1  the deployed operating point:  δ_max = 4    D_vis = 8 s    ρ = 0.27

2  at ρ = 0.27, N = 1000, 40 replicates, k = 2160, PAIRED
     D̂/D  U=0: 0.6677 ± 0.0044    U=1: 0.9985    U=2: 0.9986    U=4: 0.9997
     countable − ceiling, pooled U≥1:  0.00080 ± 0.00026  (t = 3.08)
     U=0 negative control:  0.00000 ± 0.00000  (exact — shared random streams)
   at N = 5000, 12 replicates, UNPAIRED
     D̂/D  U=0: 0.6537 ± 0.0251    U=1: 0.9997    U=2: 0.9979    U=4: 0.9996
     U=0 negative-control noise floor: ±0.027 → no first-fork cost resolvable at this N

3  largest ρ with U=4 ≥ 0.98:  > 1.87 (U=3 already suffices there)   margin: ~7× the deployment
4  D̂/D vs W_abs {1,2,3,5,7,10,15,20}:
     0.854 / 0.938 / 0.967 / 0.992 / 0.999 / 0.998 / 0.999 / 1.000
     knee at W_abs ≈ 5;  spec's W = 10 sits ~2× above it
5  per-recipient jitter {0,1,2,4,8} slots, δ_max = 4, U=1, exact oracle, 12 reps:
     D̂/D              0.9983 / 0.9992 / 0.9991 / 0.9971 / 0.9871
     depth≥2 orphans   0.25 % / 0.38 % / 0.53 % / 1.20 % / 3.30 %
     consensus         range_ratio = 0 and agreement = 1.000 in all 480 runs
     → the section's 0.986 is reproducible, at ~8 slots of per-recipient variance
6  f-precision, exact / 1e3 / 1e6:  0.99997 / 1.01026 / 0.99990  (closed form 1.000 / 1.0101 / 1.00001)
```

## Claim by claim

| # | Claim in the added section | Measured | Verdict |
|---|---|---|---|
| 1 | With uncles, the residual underestimate is **1.4 %** (`q` 0.813 → 0.986) | 0.03–0.15 % at every `U ≥ 1` cell | **Refuted.** Replace with "no residual resolvable in the design regime". |
| 2 | The residual is **deep-fork blocks** (the first-fork restriction) | Paired gap **0.08 pp ± 0.03** pooled (t = 3.08) | **Mechanism right, size ~17× overstated.** It is real and now resolved — but it is 0.0008, not 0.014. |
| 3 | Without uncles the loss is **18.7 %** (`q` = 0.813) | **33.2 %** at N = 1000, **34.6 %** at N = 5000 (42 % / 49.5 % at δ_max = 8) | **Refuted, in the unfavourable direction.** |
| 4 | `MAX_UNCLES` = 4 **never binds** (max 3 candidates observed) | `U = 3` still recovers at ρ = 1.87, the largest measured | **Corroborated,** with ~7× margin over the deployment's ρ = 0.27. |
| 5 | `w_u` = 300 **never binds** (median lag 34, max 197) | Knee at `W_abs ≈ 5`; spec's 10 is ~2× above it | **Right in effect, wrong in wording.** Say "≈ 2× above the measured knee at the deployment's load". |
| 6 | *(not mentioned)* | `PRECISION = 1e3` → **D̂/D = 1.01026 ± 0.00056** | **The section's main omission.** Larger than everything else it discusses, and opposite in sign. |

---

## 1. The deployed operating point

Every number the section quotes is stated at an operating point nobody had pinned down, so this comes first — it decides which measurements are even relevant.

`analysis-block-times-blend-network.md` sets `blending_delay = 3` s as *"seconds spent in each Blend node"* — a **fixed per-hop dwell**, neither the mean of a distribution nor a bound. The max-delay arithmetic confirms it: `3δ + 5` gives 14 s at δ = 3 and 11 s at δ = 2, matching that document's prose exactly. The profile it selects is 2 s.

The simulator's per-hop delay is `Uniform(0, δ_max)` with mean `δ_max/2`, and the design laws reach latency only through the mean, so the matching value is:

> **`δ_max = 4`**, giving `D_vis = 3·2 + 4·0.5 = 8 s` and **`ρ = f·D_vis = 0.27`**.

(Charging the spec's 1 s Proof-of-Leadership time as well gives ρ ≈ 0.30; nothing below changes.) This lands inside the report's committed 40-replicate paired design-band grid, so claims 1–3 are answered from data of record rather than fresh runs.

## 2. Accuracy and the first-fork cost

At ρ = 0.27 every `U ≥ 1` cell sits at **0.9985–0.9997**. The section's 1.4 % residual is not there.

What *is* there, now that a paired design resolves it: a first-fork cost of **0.08 pp pooled** (95 % CI [0.03, 0.13], t = 3.08). The section's *mechanism* is correct — deep-fork blocks cannot be referenced, because only the first block of a fork has a parent on the referencing chain — but at the deployment's load the effect is two orders of magnitude below the claim.

The `U = 0` negative control is **exactly 0.00000 ± 0.00000**. With no uncle slots the restricted and unrestricted rules are identical by construction, and because the two arms share stake draws, peering graph and lottery outcomes, they agree bit-for-bit. That is the strongest available evidence that the 0.08 pp is signal and not seed noise — an unpaired comparison at this size cannot resolve anything below ~0.15 pp.

At N = 5000 the runs are unpaired and that same control reads ±0.027, so nothing below ~2.7 pp is resolvable there. The N = 5000 row is an exclusion bound, not a measurement.

## 3. Is `MAX_UNCLES = 4` slack?

Yes, by a wide margin. A dedicated load sweep takes `U = 3` to `ρ = 1.87` — roughly **7× the deployment's ρ = 0.27** — and it still recovers to within noise of 1.0 across the whole range. `U = 4` is bounded below by `U = 3`, so the spec's cap does not become the binding constraint anywhere near the deployment. Claim 4 stands as written.

## 4. Is `w_u = 300` adequate?

At the deployment's operating point, sweeping the window with a single uncle slot (so the window is the only thing that can bind):

| `W_abs` (block-intervals) | 1 | 2 | 3 | 5 | 7 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|---|---|
| `D̂/D` | 0.854 | 0.938 | 0.967 | 0.992 | 0.999 | 0.998 | 0.999 | 1.000 |

The recovery knee is at `W_abs ≈ 5` and everything above ~7 is flat. The spec's `W = 10` (`w_u = 300` slots) therefore sits about **2× above the knee** — real margin, but a margin, not an absence of a constraint. "Never binds" overstates it; "≈ 2× above the measured knee at the deployment's load" is what the data supports. This matters because the window floor is set by block *spacing* rather than by network delay, so it does not shrink as the deployment's delay shrinks.

## 5. Per-recipient delay variance — where the section's number comes from

This is the experiment that could have invalidated the *report* rather than the section. It does not — but it does something more useful than refuting the section: it says exactly what the section's number assumes.

The two simulations differ in transport. The standalone drew an **independent propagation delay per (block, recipient)**; the per-node simulator runs a cascade of Blend relays and then floods network-wide **from the last relay**, so nodes receive a block at nearly the same time and their views stay synchronised. Independent per-recipient draws maximise view divergence, which is exactly what manufactures forks deeper than one block — the orphans no counting rule can recover.

Adding per-(block, node) arrival jitter on top of the cascade interpolates between the two models:

| jitter (slots) | 0 | 1 | 2 | 4 | 8 |
|---|---|---|---|---|---|
| `D̂/D` at `U = 1` | 0.9983 | 0.9992 | 0.9991 | 0.9971 | **0.9871** |
| orphans below their fork's first block | 0.25 % | 0.38 % | 0.53 % | 1.20 % | **3.30 %** |
| fork rate | 0.266 | 0.272 | 0.275 | 0.310 | 0.366 |

Accuracy is flat to ~2 slots, then bends. At 8 slots it lands on **0.9871** — essentially the section's 0.986 — with deep orphans at 3.3 %. So the standalone result is not an arithmetic error; it is what this model produces once per-recipient spread reaches roughly eight seconds.

That converts the disagreement into a question with a checkable answer: **does Blend deliver ~8 slots of per-recipient spread?** Under the spec's own model it cannot come close. The blending delay is a fixed per-hop dwell, and the cascade's final step is a network-wide gossip flood from the last relay, so what varies per *recipient* is only that flood — measured at `ℓ_mean ≈ 0.5` slot over a degree-6 graph. Eight slots is ~16× that.

The distinction is worth stating explicitly in the rewritten section, because the two are easy to conflate:

> **Variance in *when a block becomes public* is harmless to the estimate. Variance in *when each node sees it* is what manufactures unrecoverable forks.** Blend's cascade produces a lot of the first and very little of the second; the standalone model charged the second.

Consensus is untouched throughout — `range_ratio = 0` and `agreement_window = 1.000` in all 480 runs, at every jitter level — so this is an accuracy sensitivity only, never a safety one.

## 6. The bias the section missed

Three arms, identical but for how the estimator quantises its target rate:

| arm | `D̂/D` | closed form |
|---|---|---|
| exact `f` (the report's convention) | 0.99997 ± 0.00060 | 1.00000 |
| **the spec today, `PRECISION = 1e3`** | **1.01026 ± 0.00056** | 1.01010 |
| recommended, `PRECISION = 1e6` | 0.99990 ± 0.00061 | 1.00001 |

`cryptarchia-total-stake-inference.md` carries `const PRECISION: u64 = 1e3`, so the estimator drives density to `f_p = 0.033` rather than `1/30` and the chain reads **1.0 % high** — measured in the full per-node dynamics, matching the closed form to within one standard error.

This is **~13× the first-fork cost the section is concerned with**, opposite in sign, and removed entirely by a one-constant change. If any single number from this exercise belongs in the section, it is this one.

## Two things the simulator needed, and one the report did

Recorded because they change how a run must be configured, not just what it reports.

- **`f_precision` is now a config field.** It had been a module constant pinned at the *recommended* `1e6`, which is why nobody had measured what the deployed chain would read. The report's default remains exact `f` — the right choice for a design question, since it isolates the mechanism under test — but any run answering *"what will the deployed chain read"* must set `fixed_point: true, f_precision: 1000`. Both arms are run side by side by `scripts/spec_point.py`.
- **The derived window now floors rather than rounds**, matching the spec's `w_u := ⌊W·f⁻¹⌋`. No committed result moves — at `W = 10, f = 1/30` the quotient is exactly 300 either way — but it matters for the `W` and `f` sweeps, where the quotient is not an integer.
- **The unrestricted arm is a *ceiling*, not a candidate design.** The spec gates uncle validity: a block carrying an entry that fails the counting rules is rejected outright (*Block Header Validation*, step 10), so a chain in which deep-fork orphans are referenced cannot exist. Every "restricted vs unrestricted" comparison here and in the report should be read as "what the deployed rule recovers, against the most any rule could recover".

## The validity change does not disturb the incentive results

The same spec revision made uncle *content* a validity condition, which is worth checking against the report's incentive analysis rather than assuming. It holds, because **inclusion stayed soft**: a proposer *"may reference fewer uncles than it could, or pass over a candidate for another, and its block remains valid"*, and the selection procedure is *"a recommendation for filling the entries well, not a consensus rule."* Therefore:

- The report's recommendation of a **soft, reward-weighted** inclusion rule — never a validity rule — is still satisfied. What became validity-gated is the *content* of a reference, not whether one is made.
- The argument against a hard inclusion mandate still applies to a rule the spec did not adopt.
- The uncle-suppression adversary — produce blocks, reference nothing — remains a legal strategy, so those results stand unchanged.
- The restricted model's selection-time filter is now *exactly* what the protocol requires, rather than a faithful approximation of it.

One live consequence for the reward recommendation: the spec still argues that *"because uncle references carry no fork-choice weight and grant no reward, a proposer has no incentive to deviate"*. That clause survives in the current revision, and paying uncles — which the report recommends — removes its premise. The report already tracks this as an open spec-level item.

The one genuinely new consequence of the validity change: referencing an ineligible orphan now costs a proposer its whole block rather than merely failing to count. No modelled strategy does this, so no result moves — but it makes such a strategy self-defeating rather than merely ineffective, which is worth stating if junk-reference griefing is ever modelled.

## Reproducing these numbers

| § | source | data |
|---|---|---|
| 1 | `analysis-block-times-blend-network.md` (no simulation) | — |
| 2 | `configs/fine-delay-paired.yaml` run twice (default and `--old`); `configs/spec-point-n5000.yaml` likewise | `runs/*fine-paired-*`, `runs/*spec-n5000*` |
| 3 | `configs/rho-boundary.yaml` | `runs/*rho-boundary` |
| 4 | `configs/spec-point-window.yaml` | `runs/*spec-window` |
| 5 | `scripts/spec_jitter.py`, `configs/spec-point-jitter.yaml` | `runs/spec_jitter.parquet` |
| 6 | `scripts/spec_point.py` | `runs/spec_point.parquet` |

All under `tools/simulators/tsi/tsi-sim-pernode`. Run directories are dated; the ones cited here are the latest of each label.
