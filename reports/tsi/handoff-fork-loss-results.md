# Results — fork-loss claims in `analysis-total-stake-inference.md`

*Answers to [`handoff-fork-loss-validation.md`](handoff-fork-loss-validation.md). Simulator: `tools/simulators/tsi/tsi-sim-pernode`. Run 2026-08-06 against spec revision `d6fd7648` (`analysis-fork-loss-in-tsi`).*

---

## Verdict

**The added section's headline is wrong by ~17×, and it is agonising over the wrong bias.** The residual it attributes to deep forks is 0.08 pp, not 1.4 %. Meanwhile the deployed estimator carries a **+1.0 % bias of the opposite sign** that the section does not mention — from the `f` rounding, not from forks. Rewriting the section around the second number rather than the first is the substantive change.

The no-uncle loss is also **understated, not overstated**: 33 % at the operating point, not 18.7 %, and it deepens with network size.

**But the section's number is not an arithmetic error, and E5 identifies what it is.** It is what this model produces once per-recipient delay spread reaches ~8 slots — which is ~16× the gossip spread Blend's cascade actually delivers, because the cascade's variance is per *block* (shared by all recipients, harmless to the estimate) rather than per *recipient* (divergent, and the only kind that manufactures unrecoverable forks). That distinction is the whole disagreement and belongs in the rewritten section.

## The requested table

```
E1  spec Blend profile:  δ_max = 4    D_vis = 8 s    ρ = 0.27

E2  at ρ = 0.27, N = 1000, 40 replicates, k = 2160, PAIRED
      D̂/D  U=0: 0.6677 ± 0.0044    U=1: 0.9985    U=2: 0.9986    U=4: 0.9997
      countable − ceiling, pooled U≥1:  −0.00080 ± 0.00026  (t = 3.08)
      U=0 negative control:  0.00000 ± 0.00000  (exact — paired streams)
    at N = 5000, 12 replicates, UNPAIRED
      D̂/D  U=0: 0.6537 ± 0.0251    U=1: 0.9997    U=2: 0.9979    U=4: 0.9996
      U=0 negative-control noise floor: ±0.027 → no first-fork cost resolvable at this N

E3  largest ρ with U=4 ≥ 0.98:  > 1.87 (U=3 already suffices there)   margin: ~7× the deployment
E4  D̂/D vs W_abs {1,2,3,5,7,10,15,20}:
      0.854 / 0.938 / 0.967 / 0.992 / 0.999 / 0.998 / 0.999 / 1.000
      knee at W_abs ≈ 5;  spec's W = 10 sits ~2× above it
E5  jitter_mean {0,1,2,4,8} slots, δ_max = 4, U=1, exact oracle, 12 reps:
      D̂/D              0.9983 / 0.9992 / 0.9991 / 0.9971 / 0.9871
      depth≥2 orphans   0.25 % / 0.38 % / 0.53 % / 1.20 % / 3.30 %
      consensus         range_ratio = 0 and agreement = 1.000 in all 480 runs
      → the section's 0.986 is reproducible, at ~8 slots of per-recipient variance
E6  fixed_point off / 1e3 / 1e6:  0.99997 / 1.01026 / 0.99990   (predicted 1.000 / 1.0101 / 1.00001)
```

## Claim by claim

| # | Claim | Measured | Verdict |
|---|---|---|---|
| C1 | Residual underestimate **1.4 %** | 0.03–0.15 % at every `U ≥ 1` cell | **Refuted.** Replace with "no residual resolvable in the design regime". |
| C2 | The residual is **deep-fork blocks** | Paired gap **0.08 pp ± 0.03** pooled (t = 3.08) | **Mechanism right, size ~17× overstated.** It is real and now resolved — but it is 0.0008, not 0.014. |
| C3 | Without uncles the loss is **18.7 %** | **33.2 %** at N = 1000, **34.6 %** at N = 5000 (and 42 % / 49.5 % at δ_max = 8) | **Refuted, in the unfavourable direction.** The section understates the value of uncle references by roughly half. |
| C4 | `MAX_UNCLES = 4` never binds | `U = 3` still recovers at ρ = 1.87, the largest measured | **Corroborated,** with ~7× margin over the deployment's ρ = 0.27. |
| C5 | `w_u = 300` never binds | Knee at `W_abs ≈ 5`; spec's 10 is ~2× above it | **Right in effect, wrong in wording.** Say "≈ 2× above the measured knee at the deployment's load", not "never binds". |
| C6 | *(not mentioned)* | `PRECISION = 1e3` → **D̂/D = 1.01026 ± 0.00056** | **The section's main omission.** Larger than everything else it discusses, and opposite in sign. |

### E1 — the operating point

`analysis-block-times-blend-network.md` sets `blending_delay = 3` s as *"seconds spent in each Blend node"* — a **fixed per-hop dwell**, neither a mean of a distribution nor a bound. The max-delay arithmetic confirms it: `3δ + 5` gives 14 s at δ = 3 and 11 s at δ = 2, matching the prose exactly. The chosen profile is 2 s.

The simulator's per-hop delay is `Uniform(0, δ_max)`, mean `δ_max/2`, and the design laws reach latency only through the mean — so the matching value is **`δ_max = 4`**, giving `D_vis = 3·2 + 4·0.5 = 8 s` and **`ρ = 0.27`**. (Charging the spec's 1 s PoL proof time as well would give ρ ≈ 0.30; nothing below changes.)

This lands inside the committed 40-replicate paired design-band grid, so C1–C3 are answered from data of record rather than new runs.

### E2 — accuracy and the first-fork cost

At ρ = 0.27 every `U ≥ 1` cell sits at **0.9985–0.9997**. The section's 1.4 % residual is not there. What *is* there, now that the paired design resolves it: a first-fork cost of **0.08 pp pooled** (95 % CI [0.03, 0.13], t = 3.08). C2's mechanism is correct — it is the deep-fork blocks — but at the deployment's load it is two orders of magnitude below the claim.

The `U = 0` negative control is **exactly 0.00000 ± 0.00000**: with no uncle slots the two models are identical by construction, and under common random numbers they agree bit-for-bit. That is the strongest available check that the 0.08 pp is signal rather than seed noise.

At N = 5000 the runs are unpaired and the same negative control reads ±0.027, so nothing below ~2.7 pp is resolvable there — the N = 5000 row is an exclusion bound, not a measurement.

### E6 — the bias the section missed

Three arms, identical but for the estimator's target-rate quantisation:

| arm | `D̂/D` | closed form |
|---|---|---|
| exact `f` (report convention) | 0.99997 ± 0.00060 | 1.00000 |
| **spec today, `PRECISION = 1e3`** | **1.01026 ± 0.00056** | 1.01010 |
| recommended, `PRECISION = 1e6` | 0.99990 ± 0.00061 | 1.00001 |

The deployed estimator drives density to `f_p = 0.033` instead of `1/30`, so the chain reads **1.0 % high** — measured in the full per-node dynamics, matching `theory.fixed_point_bias` to within one standard error. It is ~13× the first-fork cost the section is concerned with, opposite in sign, and removed entirely by a one-constant change.

### E5 — the diagnostic: the section's number is reproducible, and that pins its hidden assumption

This was the experiment that could have invalidated the *report*. It does not — but it does something more useful than refuting the section: it says exactly what the section's number assumes.

Sweeping per-(block, node) arrival jitter on top of the cascade interpolates between the two delay models — 0 is the report's cascade, large values approach the standalone's independent-per-recipient draws:

| `jitter_mean` (slots) | 0 | 1 | 2 | 4 | 8 |
|---|---|---|---|---|---|
| `D̂/D` at `U = 1` | 0.9983 | 0.9992 | 0.9991 | 0.9971 | **0.9871** |
| depth-≥2 orphans | 0.25 % | 0.38 % | 0.53 % | 1.20 % | **3.30 %** |
| fork rate | 0.266 | 0.272 | 0.275 | 0.310 | 0.366 |

**Both branches of the handoff's pass/fail are true, at different jitter levels.** Up to ~2 slots of per-recipient variance the report is entirely robust: accuracy 0.999, deep orphans half a percent. But at 8 slots accuracy lands on **0.9871** — essentially the section's 0.986 — with deep orphans at 3.3 %. So the standalone result is not arithmetic error; it is what this model produces once per-recipient spread reaches roughly eight seconds.

That converts the disagreement into a question with a checkable answer: **does Blend deliver ~8 slots of per-recipient spread?** Under the spec's own model it cannot come close. The blending delay is a fixed per-hop dwell and the cascade's final step is a network-wide gossip flood from the last relay, so what varies per *recipient* is only that flood — and the report measures the gossip spread at `ℓ_mean ≈ 0.5` slot over a degree-6 graph. Eight slots is ~16× that. Per-*block* delay variance, which the cascade does have and which is large, moves every recipient together and so creates no deep forks at all.

The distinction is the whole disagreement, and it is worth stating in the section: **variance in *when a block becomes public* is harmless to the estimate; variance in *when each node sees it* is what manufactures unrecoverable forks.** The two are easy to conflate and the standalone model charged the second where Blend delivers the first.

Consensus is untouched throughout — `range_ratio = 0` and `agreement_window = 1.000` in all 480 runs, at every jitter level — reconfirming §6.1's structural argument at the deployment's own operating point.

**This also partly closes the report's open item 15** (correlated/heterogeneous latency untested): the report is robust to per-recipient variance up to ~2–4 slots and degrades measurably beyond, which is a bound it did not previously carry. What remains untested there is *spatially correlated* latency — nodes in a region straggling together — which jitter, being i.i.d. per (block, node), does not model.

## Notes on the guide (§4)

- **§4.1 item 1 — done.** `f_precision` is now a config field, so a spec-faithful arm can be run; it was a module constant pinned at the *recommended* 1e6, which is why nobody had measured what the chain would actually read. Default unchanged and appended to the RNG key only when non-default, so no committed run is reseeded.
- **§4.1 item 3 — done.** `uncle_window_slots` now floors rather than rounds, matching `w_u := ⌊W·f⁻¹⌋`. No committed result moves (W = 10, f = 1/30 is exactly 300 either way); it matters only for the `W` and `f` sweeps.
- **§4.1 item 2 — agreed, and the report needs it.** `--old` is no longer a candidate design: a block carrying a deep-fork reference is now *rejected*, so the unrestricted arm is an unreachable ceiling. This document labels it that way throughout; the report still calls it "the unrestricted model" in §2.1/§3.2/§6.6 and needs the same relabel.

### §6's review request — the incentive results survive

The handoff asks for §4.3's argument to be checked by someone who owns the incentive analysis rather than assumed. Checked, and it holds, for the reason given: **inclusion stayed soft.** The spec is explicit — a proposer *"may reference fewer uncles than it could, or pass over a candidate for another, and its block remains valid"*, and selection is *"a recommendation for filling the entries well, not a consensus rule."* So:

- §8.1 row 10 (*soft — never a validity rule*) is still satisfied: what became validity-gated is the **content** of a reference, not whether one is made.
- §6.8's argument against a hard inclusion mandate still applies to a rule the spec did not adopt.
- The `suppress` adversary — produce blocks, reference nothing — remains legal, so §6.3's results stand unchanged.
- The countable model's selection-time filter is now *exactly* what the protocol requires rather than a faithful approximation of it.

One correction to §4.3: it states the *"no incentive to deviate"* sentence "no longer exists in that form". It does — the clause survives verbatim inside a rewritten paragraph. **§8.5's implication (ii) is therefore still live:** the spec's no-deviation rationale rests on uncles granting no reward, and the report's recommendation to pay them removes it.

The one genuinely new consequence: referencing an ineligible orphan now costs a proposer its whole block rather than merely failing to count. No modelled strategy does this, so no result changes — but it makes such a strategy self-defeating rather than merely ineffective, which is worth stating if anyone later models junk-reference griefing.
