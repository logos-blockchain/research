# Total-Stake-Inference parameter selection — Accuracy and design

*Per-node network simulation of Cryptarchia Total Stake Inference (TSI). Simulator: `tsi-sim-pernode`. All runs at the true security parameter **k = 2160** unless noted; latency is in slots and **1 slot = 1 s**.*

*[Part 1 — Overview & recommendations](tsi-report-1-overview-and-recommendations.md) · [Part 2 — Accuracy & design](tsi-report-2-accuracy-and-design.md) · [Part 3 — Robustness & incentives](tsi-report-3-robustness-and-incentives.md) · [Part 4 — Reproducibility & appendices](tsi-report-4-reproducibility-and-appendices.md) · [Index](README.md)*

*Sections live across the set: [§1](tsi-report-1-overview-and-recommendations.md#s1)/[§7](tsi-report-1-overview-and-recommendations.md#s7)/[§8](tsi-report-1-overview-and-recommendations.md#s8) in Part 1, [§2](#s2)–[§5](#s5) in Part 2, [§6](tsi-report-3-robustness-and-incentives.md#s6) in Part 3, [§9](tsi-report-4-reproducibility-and-appendices.md#s9) and Appendices A–C in Part 4.*

---

<a id="s2"></a>
## 2. Model and method

*In one sentence: we rebuild the network node by node — every block reaches every node late, along realistic message paths, and each node keeps its own chain and runs its own estimator — so if nodes could disagree, this simulation would show it.*

Each of `N` nodes runs TSI on its **own** partial view. A global block tree is built under explicit message propagation: block `b` produced at slot `t` by node `p` becomes usable at node `j` after the propagation delay from `p` to `j`. Every node then computes its own canonical chain (the single chain it accepts as valid via the fork-choice rule; competing blocks become orphans), its own block density, and its own estimate `D̂`. The **primary model throughout this report is Blend** — the deployment target and the regime where the uncle parameters actually matter; direct gossip serves as the light-delay contrast:

- **`blend`** (primary) — a random d-regular peering graph over which a block is first relayed through `hops` random nodes (the Blend cascade (Sphinx-style relays)), each adding a `Uniform(0, δ_max)` blending delay, before a final network-wide gossip. Each cascade leg is a shortest-path hop **over the shared gossip graph** — a random relay is reached *through the network*, not by a direct link — and the final gossip floods to every node from the **last** relay, so a block's visibility is re-centred on a random node each time; the relays are blind forwarders, so only the producer sees its own block early. The dominant delay is the per-hop blending `δ_max` (`blend_delay_max`), in **whole seconds** — this is where forks, and therefore the uncle cap `U` (uncle slots per block; [§3.3](#s3-3)) and the uncle window `W` (how far back a block may reference an orphan, in slots; [§3.4](#s3-4)), matter.
- **`regular`** (contrast, detail) — plain direct gossip over the same graph; a block reaches a node after the shortest weighted path (geographic per-link latency). Realistic links are **sub-slot** (~40–200 ms), so forks are rare and even `U = 0` nearly suffices — the delay-free limit against which blend is judged.

Transport uses the **`geo`** distribution — a real-world geographic band mixture (short intra-region links, long inter-continental ones), the "natural" latency used throughout. The design laws of [§4](#s4) reach transport latency only through its *mean* — it enters solely via the mean path latency `ℓ_mean`, which feeds the mean visibility delay `D_vis = hops·δ_max/2 + (hops+1)·ℓ_mean` that the laws are actually written in ([§3.3](#s3-3)) — and this was tested directly: re-running the N = 1 000/4 000 grid with **exponentially distributed** links at the same mean leaves consensus untouched (spread 0, agreement 1.000) and every `U ≥ 1` cell identical within noise (≈ 0.99–1.01, means 1.001 exp vs 1.001 geo); only the *un-recovered* `U = 0` depth moves a few points (up to +0.09 shallower under exp, whose median link is shorter than its mean). Latency shape is a second-order effect confined to the regime the design avoids anyway. Both distributions draw each link **independently**, so this probes the latency *marginal*, not its spatial structure — geographically **correlated** latency (regional clustering that lets co-located nodes fork as a bloc) is not modelled; in the primary Blend regime the per-hop mixing delay dominates the geographic link term, so this is expected to remain second-order, but it is untested ([§8.3](tsi-report-1-overview-and-recommendations.md#s8-3)). A third topology, **`full_mesh`** (single-hop, uniform latency), reproduces the reduced analytic model (the simplified companion model that collapses the network to one chain and one scalar estimate; [§5](#s5)) inside this engine and was used only for cross-validation — no figure in this report derives from it.

**Who holds the stake.** Real stake is concentrated: a few large holders own most of it. We model this with a **Pareto** ("80/20") distribution — roughly 20 % of nodes hold 80 % of the stake — in every headline sweep, with equal-stake runs as a control. The exact split matters little to TSI, for a simple reason: the lottery hands a set of nodes wins in proportion to their *summed* stake, and TSI counts only the *total* number of blocks — so two different ways of splitting the same total stake produce statistically the same block density. Measured: consensus is identical under equal and Pareto stakes (spread 0, agreement 1.000 in both) and accuracy with uncles is indistinguishable. The equal-stake control (`runs/2026-07-24_090114_default`, N = 400, blend) has no cell-matched Pareto counterpart, so the *un-recovered* `U = 0` level is not compared across stake distributions here; the mechanism argument — concentrated stake means fewer *distinct* simultaneous winners, and a producer that wins twice does not fork with itself — remains untested at matched cells. Tail weight *was* tested at matched cells: re-running the N = 1 000/4 000 grid with a lighter Pareto tail (Lomax index 1.33 instead of 1.16) leaves consensus and every `U ≥ 1` cell unchanged within noise, and moves the *un-recovered* `U = 0` under-count by at most 0.025 (mean |Δ| = 0.012 over the four matched `U = 0` cells, 1.33 marginally *deeper*, each cell within ≈ 1.5 SEM) at k = 256 — less concentration means more *distinct* simultaneous winners, hence more forks to recover. The one place concentration could still matter is adversarial: a *whale* coalition's reward statistics are lumpier than a random coalition's, flagged as untested in [§6.5](tsi-report-3-robustness-and-incentives.md#s6-5).

**How we measure.** Every epoch, every node reports its own estimate. The first epochs of a run are a start-up transient — the estimate walking from its genesis guess to equilibrium — so we **discard the first half of every run ("50 % burn-in") and average over the remaining epochs**; each configuration is then repeated with several independent random seeds ("replicates") and averaged over those too. "Equilibrium" values in this report always mean that double average. *(The burn-in is a **measurement convention, not part of the protocol.** TSI itself just runs its recursion once per epoch, forever — each node's live estimate is simply the latest update, with no discarding or averaging. Burn-in is the standard steady-state-simulation technique of dropping the warm-up transient so a single reported number reflects the estimator's equilibrium, not its cold start; averaging the tail epochs and replicates additionally beats down the ±~0.9 % per-epoch sampling noise of [Appendix B](tsi-report-4-reproducibility-and-appendices.md#sB) to the ±0.1–0.2 % standard errors quoted here. The 50 % cut is deliberately conservative — the estimator actually converges in ~2 epochs, [§3.2](#s3-2).)* Four quantities are tracked:

- `D̂/D` — **accuracy**: the estimate divided by the true active stake. 1.0 = exact. With correct slot-counting ([§2.1](#s2-1)) and enough uncle slots the equilibrium is **1.0**; the only residual is an optional ~1 % from the on-chain integer rounding of `f` ([Appendix A](tsi-report-4-reproducibility-and-appendices.md#sA)).
- `range_ratio` — **disagreement**: the highest minus the lowest node estimate, in `D̂/D` units. 0 means every node holds *exactly* the same value.
- `agreement_window` — **consensus on the measurement**: the fraction of nodes whose finalized measurement window contains exactly the same blocks — i.e., who count the same density. 1.0 = unanimous.
- `agreement_tip` — **consensus on the newest block**: the fraction of nodes currently sitting on the most common chain tip. This can be far below 1 while all of the above are perfect — nodes race over the newest blocks yet have long agreed on the finalized past ([§3.1](#s3-1)).

<a id="s2-1"></a>
### 2.1 The TSI algorithm — before and after uncle references

**The question.** What exactly does TSI compute, and what changed when uncle references were added to the protocol?

**Why it matters.** Everything in this report — the under-count, the recovery, the parameter rules — follows from one design invariant and how the two protocol versions honour it; the report should be readable without the spec at hand.

**The design invariant: one count per slot.** The slot lottery is calibrated so that *slots* activate at rate `f` — the probability a slot produces at least one block is `f`. Crucially a slot can have several winners (two nodes independently win the same slot), and the calibration counts such a slot **once**. TSI must count the same way, or a busy slot with two winners would read as more stake than a slot with one. So the quantity TSI infers stake from is the number of *occupied slots* in the window, not the number of blocks.

**The algorithm.** Once per epoch each node measures the occupied-slot count `m` in the finalized window of `T` slots and nudges its estimate toward the target `f_p` (the block rate `f` as the on-chain integer rounding stores it):

```python
m       = occupied slots counted in the window   (which slots count differs by version — below)
D̂_next  = max(1, D̂ · (1 − β·(f_p − m/T)/f_p))     β = learning rate (deployed: 1)
```

Occupied slots more frequent than the target push the estimate up (the lottery then gets harder); less frequent pulls it down; `m/T = f_p` is the resting point. The two versions differ **only in which slots count**:

- **Before uncle references (spec v1.0):** `m` counts only slots occupied by the *canonical* chain. Under Blend delay roughly a third of honest blocks are orphaned, so their slots vanish from `m`, the resting point sits far below truth (`D̂/D ≈ 0.64–0.74`, deepening with network size), and the deflated estimate makes the network *chronically over-produce* blocks at up to ~2× the target rate ([§3.2](#s3-2), fig1). Pre-uncle TSI is not viable under Blend.
- **After uncle references (spec v1.1):** `m` also counts the *referenced uncles* — orphans pointed at from the canonical chain — which puts the delay-orphaned slots back into the count and lifts the resting point up toward `D`. The spec as written deduplicates uncles by *block identity* (the same orphan referenced by two blocks counts once), recovering the bulk of the orphan loss. **This report recommends one refinement ([§8.5](tsi-report-1-overview-and-recommendations.md#s8-5)):** deduplicate by *slot*, not by block — a referenced uncle that shares a slot with a canonical block, or with another counted uncle, must add nothing. With slot-deduplication the orphaned slots return one-per-slot and the resting point lands at **exactly `D`**.

So the slot-deduplicated uncle rule recovers the orphan-loss the delay caused while preserving the "one count per slot" invariant, and the recovered equilibrium is exactly 1.0 — not a ceiling above it. Counting uncle *blocks* instead — as spec v1.1 is currently written, and as an earlier version of this simulator did — double-counts same-slot co-winners (one canonical, one referenced orphan) and inflates the equilibrium by the fixed multi-winner factor `c(f) ≈ 1.017`. Every result in this report uses the corrected slot count, and [§8.5](tsi-report-1-overview-and-recommendations.md#s8-5) carries the corresponding spec recommendation; the difference is a genuine ~1.7 % accuracy bias in the deployed rule, not merely a fixed simulation bug.

<a id="s2-2"></a>
### 2.2 The equilibrium is bounded by 1

**The question.** Slot-counting settles the resting point at `D` ([§2.1](#s2-1)). Can the estimate sit *above* the true stake — and does the epoch-to-epoch jitter around the resting point cost nodes winning probability?

**Why it matters.** The estimate is the lottery's divisor: each node's per-slot win chance is `φ = 1 − (1−f)^(w_i/D̂)` (`w_i` = the node's stake). Whatever moves `D̂` moves every node's chance of winning slots — and with it block rewards and the pace of the chain.

**It cannot exceed the true stake.** TSI counts *occupied slots*, and a window can hold no more occupied slots than actually occurred, so the counted density is capped at the true rate `f` and the equilibrium `D̂/D` is **bounded by 1** — it recovers *up to* exactly 1 (full uncle recovery) and sits below it when delay orphans slots faster than uncles restore them ([§3.2](#s3-2)). The old `c(f) ≈ 1.017` ceiling above 1 was an artefact of counting uncle *blocks*; slot-counting removes it ([§2.1](#s2-1), [Appendix A](tsi-report-4-reproducibility-and-appendices.md#sA)). Around that bounded equilibrium each epoch's finite-window measurement carries ≈ ±0.9 % sampling noise (`√((1−f)/(f·T))` at k = 2160), which averages out over the burn-in ([Appendix B](tsi-report-4-reproducibility-and-appendices.md#sB)) and is *fairness-neutral* — all nodes share the same `D̂`, so relative win rates are untouched; only the block pace breathes by ±0.9 % epoch to epoch, with no systematic bias.

**The one residual bias is the on-chain rounding of `f`, and it is optional.** The spec stores the target as an integer at three-decimal precision, `f_p = ⌊1000·f⌋/1000 = 0.033` instead of `1/30 = 0.03333…`. Driving the density to `0.033` rather than to `f` leaves the estimate ≈ 1 % high (`f/f_p ≈ 1.010`) — a factor common to every node, so fairness is untouched, but an absolute ~1 % under-delivery of win probability and a ~1 % slow canonical pace. It is removed by carrying `f` at higher precision — **which this report's estimator does**: it drives the density to exact `f = 1/30` (residual 0), even finer than the 10⁻⁶ spec bump it recommends (`f_p = 0.033333`, residual < 10⁻⁵) — so every result here is unbiased. It is a one-constant change with no dynamics cost; the current spec still uses 10⁻³ and should adopt it ([§8](tsi-report-1-overview-and-recommendations.md#s8) row 14; [Appendix A](tsi-report-4-reproducibility-and-appendices.md#sA) quantifies it). This is the *only* systematic offset from 1 that the counting fix leaves.

---


<a id="s3"></a>
## 3. Findings

Seven findings, in the order a designer needs them: nodes agree ([§3.1](#s3-1)); delay biases the estimate low and uncles fix it ([§3.2](#s3-2)); when one uncle is not enough ([§3.3](#s3-3)); how wide the reference window must be ([§3.4](#s3-4)); how the two levers combine ([§3.5](#s3-5)); what changes with the block rate ([§3.6](#s3-6)); and how network size erodes the one-uncle margin ([§3.7](#s3-7)). Each finding is stated first; the tables and figures carry the evidence.

<a id="s3-1"></a>
### 3.1 The per-node estimate is consensus-safe — with and without uncles

**The question.** Do all nodes compute the *same* estimate — including when blocks carry uncle references?

**Why it matters.** If nodes disagreed on `D̂` (the per-node estimate of the active stake), they would disagree on who is allowed to produce blocks — a consensus split; and the uncle mechanism this report recommends must not be able to cause one. This is the precondition every later finding stands on, which is why it comes first.

**Result: agreement is exact, at every uncle cap tested (`U` = 0…3).** At the full security parameter k = 2160, the highest and lowest node estimates are identical (spread exactly 0) and **window agreement** — the fraction of nodes that count *exactly the same finalized blocks* in their measurement window — is 1.000, across all network sizes, block rates (10–30 s), and uncle caps:

| N | 1 000 | 2 000 | 5 000 | 10 000 |
|---|---|---|---|---|
| `range_ratio` (spread of `D̂/D`) | 0 | 0 | 0 | 0 |
| `agreement_window` | 1.000 | 1.000 | 1.000 | 1.000 |

Nodes *do* disagree about the newest blocks (tip agreement dips to ~0.96 in the worst cell) — but TSI never reads the newest blocks: it measures a window buried far past k-finality (blocks deeper than `k` are final — no honest node ever reorganises them), where all honest nodes provably hold identical history, uncle references included. **Consequence:** TSI can be treated as one global estimate, adding uncle references (and paying rewards for them) does not endanger that, and the rest of this report may speak of "the" estimate in the singular. Per-epoch traces at N = 10 000, the tip-agreement detail, and why an injected disagreement would *not* heal itself are in **[Appendix C](tsi-report-4-reproducibility-and-appendices.md#sC)**.

<a id="s3-2"></a>
### 3.2 Latency biases TSI low; uncles recover it to exactly 1

**The question.** How accurate is the agreed-upon estimate — and do uncle references actually earn their place in the protocol?

**Why it matters.** An estimate that is too low makes the lottery too easy — blocks come faster than the target, collide more, and the safety margin erodes; this section measures how much accuracy is lost to network delay and how much of it uncles buy back.

**The mechanism in one line.** When two blocks race, the loser (an "orphan") drops off the chain — and out of the block count that TSI reads — so the network systematically under-counts its own stake; an **uncle reference** lets a later block point at a recent orphan and put it back into the count.

**Result: without uncles the estimate is 26–37 % low; one uncle recovers it fully.** Full-scale measurement under Blend (`D̂/D` = accuracy, the estimate over the true stake; each entry the mean over all sweep cells — every degree × link-latency × blending-delay combination, 6–20 replicates, equilibrium protocol of [§2](#s2); the N = 1 000/2 000 and N = 5 000/10 000 rows are pooled from two sweeps run on *different* grids — link-latency {0.1–1.0} slots × U ≤ 3 for the smaller sizes, {0.5} slot × U ≤ 2 for the larger — so the four rows are not measured on a single common grid, though the monotone deepening also holds on the matched 0.5-slot subgrid, 0.721/0.688/0.650/0.635):

| N | `D̂/D`, U = 0 | `D̂/D`, U ≥ 1 |
|---|---|---|
| 1 000 | 0.739 | 1.000 |
| 2 000 | 0.722 | 1.000 |
| 5 000 | 0.650 | 0.999 |
| 10 000 | 0.635 | 1.000 |

The U = 0 under-count **deepens with N** (more nodes → more concurrent proposals → more orphans). One uncle restores accuracy to **exactly 1** at every size *in this sweep* (`fig2`) — because its delay grid keeps the load `ρ` (blocks produced per propagation delay, [§3.3](#s3-3)) below one; [§3.7](#s3-7) shows that at much larger N, sparse peering pushes `ρ` past what one uncle can drain, and U = 1 stops sufficing.

**Why exactly 1 (and not a ceiling above it):** because TSI counts *occupied slots*, not blocks ([§2.1](#s2-1)). The lottery activates slots at rate `f`; uncles put the delay-orphaned slots back into the count, one per slot, and never double-count a slot that already has a canonical block — so holding the counted slot density at `f` settles the estimate at `D`. Verified in isolation at zero network delay, where the only orphans are same-slot co-winners: the committed `U = 0` series (full mesh, `L = 0`, `runs/fluctuation_u0.parquet`, [Appendix B.2](tsi-report-4-reproducibility-and-appendices.md#sB-2)) sits at `D̂/D = 0.9997 ± 0.0085` (k = 2160, per-epoch σ over 4 × 120 epochs), and a matching `U = 2` arm at the same settings lands at `1.000` — the co-winner slots are counted once, not twice, so no ceiling appears (the `U = 2` arm was run ad hoc and is not committed; recipe in [§9](tsi-report-4-reproducibility-and-appendices.md#s9)). (The remaining ~1 % offset the deployed estimator carries comes only from the on-chain integer rounding of `f`, [§2.2](#s2-2) / [Appendix A](tsi-report-4-reproducibility-and-appendices.md#sA).)

![Fig 2 — per-node D̂/D vs uncle cap U (curves: max blending delay per hop = 1/2/3 slots, averaged over N): without uncles the estimate is biased low — deeper as blending delay grows — and one uncle restores it to exactly 1.](report-figures/fig2_uncle_recovery.png)

**Bootstrap is self-limiting — but only with uncles** (`fig1`; full scale, k = 2160, Blend, N = 1 000 and 5 000, genesis guesses 0.01×–2× the true stake; 0.1×–2× at N = 5 000). With uncles (U = 2, solid lines) the cold start is a non-event: whatever the guess, block production snaps back to the target `f` within ~2–2.5 epochs and the estimate lands on 1.0 by epoch 2 — identically at both network sizes. Without uncles (U = 0, dashed) the system also converges from any guess, **but to the wrong place**: the estimate settles below truth (mean ≈ 0.58× across guesses, ranging ≈0.48–0.85; ≈0.51× at N = 5 000) and the network then *chronically over-produces* blocks at ~1.85× the target rate (~2.0× at N = 5 000) — the [§6.2](tsi-report-3-robustness-and-incentives.md#s6-2) load feedback in the flesh (a low estimate makes the lottery easier, extra blocks orphan, the count stays low). So uncle references are load-bearing from the very first epochs: they are what makes the bootstrap end *at the truth* rather than at a permanently overheated equilibrium.

![Fig 1 — bootstrap at full scale (k=2160, Blend, N=1000): from any genesis guess (0.01×–2×), with uncles (solid, U=2) block production (top) and the estimate (bottom) converge to the target f and D̂/D = 1.0 within ~2–3 epochs (≈2 from a near-correct guess, ~3 from the extreme 0.01× start); without uncles (dashed, U=0) they settle more slowly to a chronically overheated, guess-dependent equilibrium — D̂/D ≈ 0.48–0.85 (mean ≈ 0.58; ≈ 0.51 at N=5000), block rate ≈ 1.2–2.1×f.](report-figures/fig1_bootstrap.png)

<a id="s3-3"></a>
### 3.3 One uncle is not always enough — the load `ρ`

**The question.** [§3.2](#s3-2) showed a single uncle slot sufficing across its delay grid. When does that stop — how much delay can one uncle slot actually handle?

**Why it matters.** Blend's per-hop blending delay is a privacy knob that may be turned up after deployment; the protocol needs to know at which point every extra second of delay demands another uncle slot.

**The intuition.** One uncle slot per block can absorb one orphan per block — so it keeps up only while the network creates orphans no faster than that. The deciding number is the **load** `ρ`: how many blocks the whole network produces during the time one block needs to become visible everywhere. The symbols used below, in one place:

| symbol | meaning |
|---|---|
| `f` | block rate (blocks per slot; `1/30` = one block every 30 s) |
| `ℓ_mean` | mean gossip path latency between two nodes (slots) |
| `hops`, `δ_max` | Blend cascade length and the per-hop blending-delay bound (mean per-hop delay = `δ_max/2`) |
| `D_vis` | mean **visibility delay** = `hops·δ_max/2 + (hops+1)·ℓ_mean` under Blend (plain gossip: just `ℓ_mean`) |
| **`ρ`** | **load** = `f·D_vis` — blocks produced per visibility delay = orphans each canonical block must absorb |
| **`U`** | **uncle cap** = uncle slots per block ([§3.3](#s3-3)) |
| **`W`** | **uncle window** = how far back a block may reference an orphan, in slots ([§3.4](#s3-4)); distinct from `T`, the measurement window of [§2.1](#s2-1) |

**Result: one uncle works up to `ρ ≈ 1`, and nothing else stretches that.** Accuracy at U = 1, plotted against `ρ` for **every** block rate and delay tested, collapses onto a single curve that breaks at `ρ ≈ 1` (`fig6`, right): **U = 1 recovers iff `ρ ≲ 1`.** Two bounds govern the cap: `U < ρ` **never** recovers (orphans arrive faster than they can be referenced; the queue grows without bound and no window helps) — a hard necessary condition; and empirically `U ≈ ⌈ρ⌉` (the load rounded up) *suffices*, with a one-uncle margin needed near integer `ρ` because the true concurrency window is about `2·D_vis`, not `D_vis` (the factor a ≈ 2 in eq. 4′, [§4](#s4)).

Sweeping the delay directly (`fig16`) makes the law visible: accuracy sits at 1.0 until the load crosses the uncle cap, then falls off — `U = 0` collapses immediately, `U = 1` holds to `ρ ≈ 1` (`D_vis ≈ 30` s), `U = 2` to `ρ ≈ 2` (`≈ 60` s), and `U = 3` across the whole tested range.

![Fig 16 — recovered relative stake D̂/D vs mean visibility delay D_vis (Blend, f=1/30; N = 800, degree 8, uniform stake, 5 replicates at a reduced k = 48 so the delay axis could be swept densely): each uncle cap U holds accuracy at 1.0 until ρ=f·D_vis exceeds U, marked at ρ=1, 2. The reduced k widens the per-epoch sampling noise, so a few U ≥ 1 points sit fractionally above the 1.0 line (largest 1.016 ± 0.011 at D_vis ≈ 14 s, < 2 SEM) — the ≤ 1 bound itself is resolved at k = 256 with 20 replicates in `fig26` below.](report-figures/fig16_stake_vs_delay.png)

![Fig 3 — recovery (mean D̂/D) over hops × per-hop blending budget for uncle caps U ∈ {0,1,2,4}: one uncle recovers only while the total delay stays small, and raising the cap restores it. The axes show the per-hop budget; the total mean visibility delay D_vis runs from ≈11 s (3 hops, δ_max=4) to ≈104 s (6 hops, δ_max=32).](report-figures/fig3_hops_delay.png)

The full sweep behind `fig3` spans hops 3–6 × per-hop budget 4–32 s × `U ∈ {0, 1, 2, 4}` at both N = 1 000 and N = 2 000. Note the axes show the *per-hop* budget — the total mean delay is what matters, e.g. 3 hops at `δ_max = 8` mean 3·4 = 12 s of blending plus ≈ 5 s of gossip → `D_vis ≈ 17` s (`ρ ≈ 0.56`), while 6 hops at `δ_max = 32` reach `D_vis ≈ 104` s (`ρ ≈ 3.5`). More hops at a fixed budget raise `D_vis` and degrade U = 1 exactly as the load predicts (at `δ_max = 16`: accuracy 0.96 at 3 hops → 0.52 at 6 hops), and raising the cap restores it up to the longest cascade — U = 2 clears the `0.98` recovery bar ([§3.6](#s3-6)) in every `δ_max ≤ 8` cell (≥ 0.998) and at `δ_max = 16` through 5 hops, but **not at 6 hops**: `1.000 ± 0.001` (3 hops) → `0.962 ± 0.007` (6 hops), a 2.6σ shortfall, and `0.941 ± 0.004` (11σ) at N = 2 000; the hops-average is 0.986. That cell carries `ρ ≈ 1.8` — exactly the load at which [§3.6](#s3-6) finds U = 2 genuinely insufficient. `δ_max = 32` needs U = 4 (hops-averaged 0.983, vs 0.755 at U = 2), and even U = 4 falls to `0.945 ± 0.004` at 6 hops — consistent with `⌈ρ⌉` rising to ~2–4 across the hops axis (U = 3 was not swept). The N = 2 000 half reproduces the same pattern (hops-averaged U = 2: 0.981 at `δ_max ≤ 16`; U = 4: 0.981 at 32, with the same 6-hop shortfalls).

*(Detail — the direct-gossip contrast.)* Blend is the hard case because its per-hop delay is *whole seconds*; plain direct gossip (`regular`) has *sub-slot* links, so `ρ ≈ 0.04` and forks are negligible — even `U = 0` nearly recovers (`fig19`, N = 5 000 and 10 000 pooled): at the tested `0.5`-slot per-link latency `U = 0` alone reaches `0.97` at degree 6 and `0.93` at degree 4, a denser graph recovering better. This is why the recommended cap is `⌈ρ⌉ + 1` under Blend while `U = 1` suffices for direct gossip.

![Fig 19 — direct-gossip (regular, N = 5 000 and 10 000 pooled) accuracy vs mean per-link latency at U=0: at the single tested 0.5-slot per-link latency, U=0 alone recovers 0.97 (degree 6) / 0.93 (degree 4); higher peering degree helps.](report-figures/fig19_accuracy_vs_latency.png)

**The estimator is bounded by 1; the deficit is the signal below the block rate.** Because TSI counts *occupied slots* and a window can hold no more than actually occurred, the equilibrium `D̂/D` **cannot exceed 1** — it recovers *up to* exactly 1 and falls short only when the load outruns the uncle cap ([§2.2](#s2-2)). So the quantity of interest is the **under-count deficit `1 − D̂/D ≥ 0`**. A dedicated ρ-boundary sweep (`configs/rho-boundary.yaml`; hops fixed at 3 so `ρ ∝ δ_max`, N = 1 000, 20 replicates, **scaled `k = 256`** — the deficit mechanics are k-invariant; `k` sets only the per-epoch sampling noise ([Appendix B](tsi-report-4-reproducibility-and-appendices.md#sB)), which 20 replicates beat down; `fig26`) resolves it cleanly: at U = 0 the deficit runs 0.51 → 0.85 across `ρ = 0.56 → 2.0`; one uncle holds the deficit within noise only for `ρ ≲ 0.6` (already 0.034 at `ρ = 0.96`, then steeply to 0.47 by `ρ = 2`); U = 2 stays within noise to `ρ ≈ 1.2` and holds the deficit under 0.6 % out to `ρ ≈ 1.56` (0.0033 ± 0.0018 at `ρ = 1.16`, rising to a resolved-but-negligible 0.0058 ± 0.0023 at `ρ = 1.56`) before breaking to 0.048 at `ρ = 2`; U = 3 stays within noise across the whole range — the `U = ⌈ρ⌉` boundary read straight off the deficit. Across all 40 cells **no equilibrium sits above 1 beyond sampling noise** (max `1.0024 ± 0.0017`), confirming the bound.

![Fig 26 — the region below the block rate: under-count deficit `1 − D̂/D` vs load ρ per uncle cap (left, log-y — the `U = ⌈ρ⌉` boundary; **solid** markers are deficits resolved above their 2·SEM noise level, **open** markers are the 17 cells at or below noise — including 9 where sampling noise puts `D̂/D` a hair above 1 — clamped to the axis floor `3×10⁻⁴` for the log scale, so an open point on the floor is not a measured positive deficit), and accuracy capped at the `D̂/D = 1` bound (right, ±SEM across replicates — the equilibrium sits at or below 1 at every load, U=2/U=3 hugging 1 from below).](report-figures/fig26_deficit_vs_rho.png)

<a id="s3-4"></a>
### 3.4 The uncle window is set by block spacing, not by delay

**The question.** How far back may a block reach when it references an orphan — how large must the uncle window `W` (measured in slots) be?

**Why it matters.** Too small a window silently discards orphans before any block gets a chance to reference them, and the under-count of [§3.2](#s3-2) returns no matter how many uncle slots exist; too large a window only costs a little validation state, so the risk is entirely on the small side.

**Result: the window is sized by block *spacing*, not by network delay.** Sweeping `W` at fixed U = 1 (`fig4`) gave a counter-intuitive result: the critical `W` is **~100–200 slots even for a 2-slot delay**, and barely depends on the delay. The reason is *queueing*: canonical blocks appear only every `1/f = 30` slots, and with U = 1 each references one orphan, so an orphan waits in a FIFO queue drained at ~1 per block interval. The window must span **several block intervals** for a queued orphan to reach a block with a free uncle slot before it ages out. (All runs fill uncle slots **oldest-first** — the FIFO behind this law. A random draw among the queued orphans drains one no faster than oldest-first, so the floor under it is no smaller; the margined `W = 10/f` covers that sensitivity.) Empirically:

> **`W_min ≈ 7/f`** (the measured recovery floor is ≈ 200 slots at f = 1/30 = 6.7 block intervals; rounded design rule 7/f = 210 slots = 7 intervals), roughly constant across delay and U, rising toward ~10/f only as the load approaches the uncle capacity.

So `W` scales with the block interval `1/f`, and the default `W = 300` (= 10 intervals at f = 1/30) sits safely above the floor.

![Fig 4 — accuracy vs uncle window W: the critical W is ~100–200 slots even at a 2-slot delay, and barely depends on the delay (queueing, not propagation).](report-figures/fig4_window.png)

The full `W × delay` picture at `U = 1` (`fig22`) shows both bounds at once: below the `≈ 100`-slot window floor accuracy is lost at *every* delay (rows `W ≤ 50`), and above it accuracy holds only while the delay keeps `ρ ≲ 1` — at `delay = 16` `W = 300` reaches only `0.96` (recovery needs `W ≈ 600`, [§3.5](#s3-5)), and at `delay = 32` (`ρ ≈ 1.7`, past `U = 1`'s capacity) even the widest window recovers only `0.61`. Widening `W` cannot substitute for the extra uncle that `ρ > 1` demands.

![Fig 22 — accuracy over (uncle window W × blending delay) at U=1: a hard window floor (~100 slots) at every delay, and a delay ceiling where U=1 runs out (ρ>1) that no window fixes.](report-figures/fig22_heatmap_window_delay.png)

The N = 2 000 replica of this sweep reproduces the window floor unchanged — in the recovered region (delay ≤ 8 s, W ≥ 200) accuracy matches N = 1 000 within 0.003 — and the U-limited delay-32 plateau is likewise essentially N-invariant (≈ 0.56–0.62 at W = 200–300 for both N = 1 000 and N = 2 000). Together with the (W × U) N = 2 000 run of [§3.5](#s3-5) and the [§3.2](#s3-2) N-deepening of the *un-recovered* under-count (0.739 → 0.635 over N = 1 k → 10 k), this is the direct evidence that the `W`/`U` **thresholds are N-invariant while the un-recovered accuracy is not**.

**At scale, and as a fluctuation buffer** (`fig25`; N = 1 000 vs **10 000**, W up to 600, k = 256). Three results close the window question:

- **The floor's position does not move with N.** At the 8-s budget the recovery knee sits at W ≈ 100–200 slots for both sizes (N = 10 000 is a few points deeper below the floor, consistent with its higher load) — the queueing law is about block *spacing*, and block spacing does not change with N.
- **A wider window buys back the load boundary.** Block production fluctuates, and the window is the buffer that absorbs those bursts: right at `ρ ≈ 1` (the 16-s budget) U = 1 *fails* with the default W = 300 (0.965 at N = 1 000, 0.941 at N = 10 000), and W = 450 is still short of the 0.98 bar (0.979 and 0.963); only **W = 600** clears it at N = 1 000 (0.993) and brings N = 10 000 to within noise of it (0.976 ± 0.005) — twenty block intervals of buffer instead of ten. Because a growing network raises the load toward the boundary ([§3.7](#s3-7)), this is also the answer to "must W grow with N?": *near the boundary, yes, and the width needed grows with N* — W = 600 is the smallest tested width that recovers at N = 1 000, while at N = 10 000 even 600 only approaches the bar, so at scale the `+1` uncle is the reliable lever (U = 2 recovers every W ≥ 200 at both sizes, 0.995–1.000).
- **No window fixes sustained overload.** At the 32-s budget (`ρ ≈ 1.7–1.8 > U = 1`) accuracy stays collapsed at *every* width tested (0.23–0.76): a buffer absorbs variance around a stable queue, but when orphans *arrive* faster than one slot per block can *drain* them, the queue grows without bound and width is irrelevant. U = 2 (dashed) lifts every width above the floor back toward the bar, but clears `0.98` only at **W ≥ 450** (W = 300: 0.972 at N = 1 000, 0.962 at N = 10 000 — still short; W = 450: 0.993 and 0.992) — at `ρ ≈ 1.7` the extra uncle *and* the wider window are both required.

So the two levers separate cleanly: **`U` must cover the average load; `W` must cover the fluctuations around it** — and near `ρ ≈ 1` a window of ~15–20 block intervals (W = 450–600 at f = 1/30) is a cheap alternative to spending the `+1` uncle slot.

![Fig 25 — window sufficiency at scale (N = 1 000 blue vs N = 10 000 orange; U = 1 solid circles / U = 2 dashed squares): the floor position is N-invariant (left), W = 600 buys back the ρ ≈ 1 boundary (middle), and no window fixes ρ > U (right).](report-figures/fig25_window_scale.png)

<a id="s3-5"></a>
### 3.5 The joint (W, U) region — the levers are hierarchical

**The question.** `W` (how far back a block may reference) and `U` (how many uncle slots per block) both fight the same orphan loss — can one substitute for the other?

**Why it matters.** If they were interchangeable, a deployment could just pick whichever is cheaper; the data says they are not, and getting the order of decisions wrong leaves accuracy on the table.

Co-sweeping W × U (`fig5`) shows the two are **not interchangeable**:

- **`W` is first-order.** Below the window floor — ≈ 3/f (100 slots) at low delay, rising to the ≈ 7/f (200 slots) of [§3.4](#s3-4) as load grows — *no* uncle count recovers the estimate (e.g. delay 16, W = 100: even U = 4 reaches only 0.94). The window simply cannot reach the orphans.
- **Above the floor, `W` and `U` trade off**, and then **`U` is set by the load `ρ`** ([§3.3](#s3-3)): delay 8 → U = 1, delay 16 → U = 2, delay 32 → U = 3 (U = 2 stalls at 0.973 even at W = 300, [§3.6](#s3-6)).
- A single uncle slot at the spec window (`U = 1`, `W = 300` = `w_u`) is safe only up to delay ≈ 8 s; beyond that you must **add uncle slots** — the spec's `MAX_UNCLES = 4` allows up to four — not widen the window.

At N = 2 000 the region is unchanged — the U-limited delay-32 row matches N = 1 000 cell for cell (at W = 300, U = 2 reaches `0.973 ± 0.002` at both sizes and U = 3 recovers to ≥ 0.997 at both), so **the `W`/`U` thresholds are N-invariant** ([§3.4](#s3-4)): delay 32 needs U = 3 regardless of N.

![Fig 5 — the joint (W, U) recovery region: W is first-order (a hard floor no U can buy below); above it, U is set by the load ρ.](report-figures/fig5_window_uncles.png)

As a deployment decision chart, `fig20` (also **N = 5 000 and 10 000 pooled**) reads the accuracy straight off `(delay × U)` at a fixed degree: the `U = 0` column is blue (under-count `0.67–0.75`, deeper than at smaller N — the N-scaling of [§3.2](#s3-2)), and a *single* uncle already lifts every tested delay to exactly 1 (`1.00`, bold) — the concrete basis for the `U = ⌈ρ⌉ (+1)` rule, holding at the largest scale.

![Fig 20 — accuracy decision chart D̂/D over (blending delay × uncle cap) at N = 5 000 and 10 000 pooled, degree 6: U=0 under-counts (0.67–0.75), U≥1 recovers to exactly 1.00 across the tested delay range.](report-figures/fig20_heatmap_accuracy.png)

<a id="s3-6"></a>
### 3.6 Block rate `f` moves every threshold predictably

**The question.** Everything above was measured at 30-second blocks (`f = 1/30`). If the protocol ever runs faster blocks, do the rules survive?

**Why it matters.** The block rate is a first-order protocol choice, and a parameter recipe that silently assumed one rate would break the day the rate changes — this section shows every threshold moves *predictably* with `f`, so the recipe transfers.

**Result: the same wall-clock delay weighs more at a faster rate — everything else follows.** Because the load is `ρ = f·D_vis` (blocks produced per visibility delay, [§3.3](#s3-3)), a **faster** block rate makes the *same* wall-clock delay heavier (`fig6`, left): a fixed 8-s delay needs U = 1 at 30 s/20 s blocks but **U = 2 at 15 s and 10 s blocks**. Predicted `U_min = ⌈ρ⌉` vs. the measured smallest U reaching the 0.98 recovery bar (0.98 of the true value 1.0 — slot-counting removed the old `c(f)` ceiling; the sweep tested only **U ≤ 2**):

| propagation delay (s) | block interval 30 s | 20 s | 15 s | 10 s |
|---|---|---|---|---|
| 8  | 1 / 1 | 1 / 1 | 2 / 2 | 2 / 2 |
| 16 | 1 / **2** | 2 / 2 | 2 / 2 | 3 / >2 |
| 32 | 2 / **>2** | 3 / >2 | 4 / >2 | 6 / >2 |

*each cell = predicted `⌈ρ⌉` / smallest measured U reaching the 0.98 recovery bar; `>2` = U = 2 still insufficient (sweep capped at U ≤ 2).*

`⌈ρ⌉` matches in every fully-resolved cell **except two boundary cells** (one near-integer, one censored at U ≤ 2) — and error bars (standard error over replicates) show the two boundary cells are not alike: delay 16 / 30 s (`ρ = 0.96`) fails at U = 1 with `0.962 ± 0.006`, a **robust 3σ** under-shoot that genuinely needs U = 2; and delay 32 / 30 s (`ρ = 1.76`) reaches only `0.973 ± 0.002` at U = 2, a **4σ** shortfall — U = 2 genuinely fails there (matching the table's `>2`). This is why the `U = ⌈ρ⌉ + 1` margin exists and why boundary pass/fail calls must carry error bars. Every other `>2` cell is consistent with the larger `⌈ρ⌉` (the sweep only tested U ≤ 2). Three `f`-effects, all consistent with [§4](#s4) (plus one null result):
- **recovery stays at 1.0** at every rate — slot-counting removes the `c(f)` dependence the block count had (the multi-winner rate `c(f)` = 1.017 → 1.054 from 30 → 10 s no longer appears in the estimate);
- **`U_min` grows ∝ f** (same delay, faster rate ⇒ more uncles);
- **`W_min` shrinks ∝ 1/f** (constant ≈ 7 block intervals);
- *(null result)* **consensus-safety ([§3.1](#s3-1)) is f-independent** — `range_ratio = 0` at all four rates.

![Fig 6 — block rate: a faster f makes the same wall-clock delay heavier (left, U by delay×rate); D̂/D for U=1 collapses onto the load ρ and recovers iff ρ≲1 (right).](report-figures/fig6_block_rate.png)

<a id="s3-7"></a>
### 3.7 Network size erodes the one-uncle margin — through the gossip diameter, and only there

**The question.** [§3.3](#s3-3) fixed the network size and grew the delay; real deployments do the opposite — the blending budget is a design constant while `N` grows. Does a bigger network break `U = 1`, and does the answer depend on the peering degree? We investigate under Blend only, in two cases: **(a)** plain geo link delays, and **(b)** geo delays plus a long-tail model in which 10 % of deliveries straggle by an extra `Poisson(3)`-slot delay.

**Why it matters.** If `U = 1` quietly stops sufficing at large `N`, the under-count of [§3.2](#s3-2) returns — and with it the cheap grinding lever of [§6.3](tsi-report-3-robustness-and-incentives.md#s6-3) (deflating `D̂` to make the lottery easier, attacker included). A deployment sized on small-N evidence would degrade exactly when the network succeeds.

**Result: `N` enters through one number — the gossip path length.** Measured exactly on the simulator's own graph generator up to **N = 10⁶** (`fig24`, right), the mean path latency grows logarithmically, `ℓ_mean ≈ a_d·ln N`, with `a₄ = 0.33`, `a₆ = 0.19`, `a₈ = 0.14` slots — the classic `1/ln(d−1)` diameter law. The direct ladder (N = 1 000 → 32 000, scaled k = 256, δ_max ∈ {4, 8} s, 756 trajectories) confirms the mechanism end-to-end: **consensus stays exact in every cell** (spread 0, agreement 1.000 — long-tail jitter included), accuracy depends on `N` only through the load `ρ = f·D_vis(N, d, δ)` (`fig24`, left), and at the 8-s budget the **degree-4** curve declines monotonically until at N = 32 000 it drops below the recovery bar (the `0.98` criterion of [§3.6](#s3-6)): `0.973 ± 0.007` in case (a) at N = 32 000 (`fig23`) — while **degrees 6 and 8 stay flat near 1.0** through 32 000 (deg 6: 0.988; deg 8: 1.001), and `U = 2` recovers every cell. Extrapolating with the exact probe: **degree 4 reaches the measured `U = 1` failure load (ρ = 0.96, [§3.6](#s3-6)) at N* ≈ 8×10⁵ — one uncle is *not* enough at a million nodes on a degree-4 graph.** Degree 6 would need N ~ 4×10⁹ and degree 8 ≈ 6×10¹² to cross the same line: safe at any realistic size.

![Fig 23 — U=1 accuracy vs network size (blend, δ=8 s, k=256): degree 4 declines below the 0.98 recovery bar by N=32 000 (0.973) while degrees 6/8 track the U=2 control near 1.0; the long-tail case (b) is statistically indistinguishable.](report-figures/fig23_nscaling_u1.png)

**The long-tail jitter changes nothing measurable.** Case (b) shifts the mean visibility delay by only 0.3 slots (10 % of deliveries × 3-slot mean straggle; `ρ` + 0.01) and the measured `U = 1` accuracy by ~0.4 % per cell on average (up to ~1.5 % in the noisiest large-N cell, ~0.03 % pooled — all within the few-replicate SEM); consensus is untouched in all 378 case-(b) trajectories. The stragglers' real cost is the variance channel of [Appendix B](tsi-report-4-reproducibility-and-appendices.md#sB).3 — already absorbed once `U ≥ 1`.

![Fig 24 — left: the whole ladder collapses onto the load law ρ = f·D_vis(N, d, δ) — no other N-dependence; right: the exact probe's ρ(N) per degree to 10⁶ nodes at δ=8 s, with the measured U=1 failure load marked — degree 4 crosses it near N* ≈ 8×10⁵.](report-figures/fig24_nscaling_probe.png)

**Design consequence.** The uncle cap and the peering degree are exchangeable defences against network growth: keep `ρ(N, d, δ) < 1` either by adding an uncle slot or by densifying the graph — and one degree step (4 → 6) buys roughly a **5 000× larger network** at the same blending budget (N*: 8×10⁵ → 4×10⁹). [§8](tsi-report-1-overview-and-recommendations.md#s8) (row 12) turns this into the size-dependent degree rule.

---


<a id="s4"></a>
## 4. Design equations and parameter-selection algorithm

This section turns [§3](#s3) into a recipe: measure the network's propagation delay, compute the load, read off `U` and `W`. The table gives the calibrated design laws, the algorithm walks a deployment through them, and the worked examples cover the Cryptarchia baseline and Blend.

Let `f` = block rate (blocks/slot; block interval `1/f` slots = seconds), and for the propagation model let `ℓ_mean`, `ℓ_max` be the mean / max shortest-path transport latency over the peering graph (for a d-regular geo graph at N ≈ 1 000, deg 6: `ℓ_mean ≈ 1.2`, `ℓ_max ≈ 2.3` slots), `hops` the Blend cascade length and `δ_max` the per-hop blending bound. A denser peering graph shortens `ℓ_mean` and hence `D_vis` and `ρ` — the peering degree is an operator-side lever that buys uncle-cap headroom (fig19: at U = 0, degree 6 stays near-exact where degree 4 dips).

**Derived quantities** (calibrated on N = 1 000 blend). The `U`/`W` *thresholds* are ~N-invariant and were confirmed to hold across f = 1/10…1/30 ([§3.6](#s3-6)); the *U=0 accuracy* (eq 4′) worsens with N ([§3.2](#s3-2)) and is an N ≈ 1000 fit.

| # | quantity | equation | calibration / validity |
|---|---|---|---|
| 1 | mean visibility delay | `D_vis = hops·δ_max/2 + (hops+1)·ℓ_mean`  (direct gossip: `ℓ_mean`) | — |
| 2 | load (orphans / block) | `ρ = f · D_vis` | governs U (fig6 collapse at ρ≈1) |
| 3 | fully-recovered accuracy | `D̂/D = 1` (slot-counting, [§2.1](#s2-1)) | exact at equilibrium; deployed value ≈ `f/f_p` ≈ 1.01 from on-chain `f`-rounding only ([Appendix A](tsi-report-4-reproducibility-and-appendices.md#sA)) |
| 4 | accuracy, orphan-loss factor (U=0) | `D̂/D = ln(1−f)/ln(1−f/q_eff)` = `expected_ratio(f, q_eff)`, where the **effective density** `q_eff ≤ 1` is the fraction of active slots that are *counted* (canonical + recovered-uncle slots) | tight in the **orphan-loss regime** `q_eff < 1` (RMS 2.3e−4 vs the sim's `q_eff`, U=0 sweep); it *saturates at 1* as `q_eff → 1`, so the fully-recovered accuracy is **1.0 (eq 3)** — slot-counting counts each occupied slot once, so there is no multi-winner ceiling above it |
| 4′ | accuracy, no uncles (closed-form stand-in) | `D̂/D(U=0) ≈ 1 / (1 + a·ρ)`, `a ≈ 2` | `a ≈ 2` fit over the N = 1 000, U = 0 blend cells of `blend-hops-delay` + `rho-boundary` + `fullscale-small` (per-run best fits a = 1.4–2.2, pooled a = 1.8), ρ ≳ 0.2 (RMS ≈ 0.07 at `a = 2`, ~250× coarser than eq. 4); worsens with N; ≈ 1 for direct gossip |
| 5 | **uncle cap** | necessary `U ≥ ⌈ρ⌉` (U<ρ **never** recovers); recommend `U = ⌈ρ⌉ + 1` | `⌈ρ⌉` matches emp. within ±1 — under-shoots just below integer ρ |
| 6 | **uncle window** | `W_min ≈ 7/f` (≈ 200 slots @ f=1/30); margin `≈ 10/f` | ~const in delay/U; → ~10/f near uncle capacity |

**Algorithm — choose (W, U) for a deployment**

```python
Inputs:  f (block rate),  propagation profile (hops, δ_max, ℓ_mean),  deployment size
1. Visibility delay:   D_vis = hops·δ_max/2 + (hops+1)·ℓ_mean       # direct gossip: D_vis = ℓ_mean
2. Load:               ρ = f · D_vis
3. Feasibility:        deployment REQUIRES U ≥ ⌈ρ⌉. If that exceeds the protocol's uncle-slot
                       budget, cut propagation delay (fewer hops / less blending) — no window fixes U<ρ.
                       Prefer to keep ρ < 1 with margin regardless: ρ > 1 is both the chronic
                       under-count regime and the cheap grinding lever (§6.2–§6.3).
4. Uncle cap:          if ρ ≪ 1 (direct gossip): U = 1 suffices (U=0 alone already ≈ 0.97)
                       else: U = ⌈ρ⌉ + 1   # recommended; ⌈ρ⌉ is the tight minimum, occasionally
                                            # short by one just below an integer ρ
5. Uncle window:       W = ⌈10/f⌉ slots   # ≥ 7/f floor; set by block SPACING, not by the delay.
                       #   Near the load boundary ρ ≈ 1, widen to 15–20/f (450–600 @ f=1/30)
                       #   as a cheap alternative to the +1 uncle slot (§3.4, §8.1 row 3).
6. Expected accuracy:  with U   D̂/D → 1.0 (bounded by 1; spec 10^-3 f-rounding would add ~1%, App. A)
                       without   ≈ 1/(1+2ρ)  for ρ ≳ 0.2,   ≈ 1  for ρ ≪ 1 (direct gossip)
7. Security k:         set by finality; TSI's per-node agreement held at k=2160, expected any k (§3.1)
8. Learning rate:      β = 1 (one-epoch tracking; time-constant τ = −1/ln(1−β) epochs — §6.5)
```

**Worked examples** (`ℓ_mean ≈ 1.2` slots for the study graph):

- *Blend (primary), 3 hops, δ_max = 8 s, f = 1/30.* `D_vis ≈ 3·4 + 4·1.2 ≈ 17` → `ρ ≈ 0.56`. Tight `⌈ρ⌉ = 1` (empirically suffices, [§3.5](#s3-5)); **recommended `U = 2`** (margin); `W = 300`.
- *Same Blend at f = 1/10 (10 s blocks).* `ρ = 17/10 ≈ 1.7`. Tight `⌈ρ⌉ = 2` (needed, [§3.6](#s3-6)); **recommended `U = 3`**; `W = 10/f = 100`.
- *Direct global gossip (contrast), f = 1/30.* `D_vis = ℓ_mean ≈ 1.2` → `ρ ≈ 0.04`. Forks nearly negligible: `U = 1` (U = 0 alone already reaches `D̂/D ≈ 0.97` at degree 6 / `0.93` at degree 4, [§3.3](#s3-3) — well below where eq. 4′ applies; one uncle closes the last few percent to `1.000 ± 0.001`); `W = 10/f = 300`. → the Cryptarchia defaults (`W = 300` is the spec window `w_u`; the spec's `MAX_UNCLES = 4` sits well above the single uncle slot this regime needs).

---


<a id="s5"></a>
## 5. Discussion and caveats

Read this before using the numbers: the regime they hold in, and the margins that absorb what they do not.

- **Regime of exactness.** [§1](tsi-report-1-overview-and-recommendations.md#s1)–[§5](#s5) are for honest nodes with deterministic latency (`jitter = 0`), the regime in which the windowed/pruned engine is bit-exact; [§6](tsi-report-3-robustness-and-incentives.md#s6) tests the limits. **Open items:** sizing `W`/`U` so the emergent reference rate stays high under adversarial orphaning; the full multi-coalition (`K`-agent, [§6.9](tsi-report-3-robustness-and-incentives.md#s6-9)) selfish equilibrium (below-⅓ joint profitability unaddressed); per-node clock skew; and stochastic-jitter *parameter* tuning.
- **The `ρ ≈ 1` and `W ≈ 7/f` constants (load boundary, window floor) are semi-empirical** — the *functional forms* follow from the orphan-queueing mechanism, the constants are fitted (`a ≈ 2`, pinned only to ~1.8–2.2 by the sweep; `U = ⌈ρ⌉` within ±1). For production use the margined rules `U = ⌈ρ⌉ + 1` and `W = 10/f`.
- **N-scaling.** The U = 0 under-count worsens slowly with N (0.739 → 0.635 over N = 1k → 10k); the recovery thresholds for `U`/`W` are essentially N-invariant ([§3.4](#s3-4)). Size `D_vis`/`ρ` (and add margin to U) for the largest expected deployment; eq. 4′ itself is an N ≈ 1 000 fit.
- **The residual ~1 %.** Slot-counting lands the equilibrium at exactly `D` ([§2.1](#s2-1)); the *only* systematic offset left is the on-chain integer rounding of `f` (`f_p = ⌊f·1000⌋/1000`, the `fixed_point` switch), which leaves the deployed estimate ≈ `f/f_p ≈ 1.01` high — common to every node (fairness untouched), an absolute ~1 % under-delivery of win probability, removed by carrying `f` at higher precision. **No correction exists in the specs today** ([Appendix A](tsi-report-4-reproducibility-and-appendices.md#sA); [§8](tsi-report-1-overview-and-recommendations.md#s8) carries the precision bump as a recommendation).
- **W and U are coupled but not fungible:** you cannot buy below the `~7/f` window floor with any number of uncles, and you cannot buy below `U = ⌈ρ⌉` with any window — though right at the boundary `ρ ≈ 1`, extra window (15–20/f) absorbs the fluctuation bursts that would otherwise need the `+1` uncle ([§3.4](#s3-4), fig25).
- **"Consensus-consistent" ≠ "accurate".** [§3.1](#s3-1) shows nodes agree on one value; that value is only correct once uncles restore it. The reduced (single global `D̂`) analytic model, which [§3.1](#s3-1) validates, is the model that collapses the network to one canonical chain and one scalar estimate.

---
