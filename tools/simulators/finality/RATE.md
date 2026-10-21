# Rate and forks

Phase C of `PLAN.md`, with the Phase A1 baseline it builds on. Every table is generated from
`runs/` by `scripts/tables.py`; the runs come from `scripts/a1_baseline.py`, `scripts/c1_rate.py`,
`scripts/c1_settle_surface.py`, `scripts/c3_ghost.py` and `scripts/c4_taktikos.py`, and Phase K's
from `scripts/k5_rate.py`.

## The engine and its calibration

The TSI per-node engine builds one epoch for 1,000 nodes on a degree-6 peering graph with
geographic link latencies. Every node's stake estimate is held at the true stake, the
equilibrium that uncle references give the inference. Uncle references never touch fork choice,
so none are selected. Blend's mixing delay is drawn per hop either as the engine always did,
uniform on `(0, δ)` ("continuous"), or as the node's release delayer does, a whole number of
1-slot rounds uniform on `[1, Δ_max]` ("rounds"). The second mode was added for this study;
continuous runs keep their historical seeds and results.

At the TSI report's points (3 hops, continuous, 0.5 s links, Pareto stake) the engine reproduces
the report's orphan shares of 0.20, 0.35 and 0.60:

| per-hop delay (s) | orphan share | ± SEM | mean delay (s) |
| --- | --- | --- | --- |
| 2.0 | 0.206 | 0.003 | 8.1 |
| 8.0 | 0.341 | 0.015 | 17.1 |
| 32.0 | 0.606 | 0.007 | 53.1 |

At 3 hops, 2 rounds per hop and 0.1 s links the orphan share is 0.154 at a 5.5 s mean delay. The
specification's stake-inference analysis measured 0.15 at 3 hops, 2 s per hop and a 6 s mean
delay (`analysis-total-stake-inference.md`, `q = 0.85`).

## A1 — the baseline over the delay axis

`f = 1/30`, Pareto stake, 8 replicates per row. "growth / f" is canonical blocks per slot over
`f`; "p99 full delay" is the 99th percentile of the time until every node holds a block.

| hops | Δ_max (rounds) | link (s) | orphan share | growth / f | mean delay (s) | p99 full delay (s) | 30 deep, p50 (min) | 100 deep, p50 (min) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 0.1 | 0.042 | 0.971 | 1.5 | 1.8 | 15.4 | 51.6 |
| 1 | 2 | 0.1 | 0.056 | 0.961 | 2.0 | 2.8 | 15.5 | 51.9 |
| 1 | 3 | 0.1 | 0.077 | 0.943 | 2.5 | 3.8 | 15.7 | 52.8 |
| 1 | 5 | 0.1 | 0.096 | 0.918 | 3.5 | 5.8 | 16.1 | 54.0 |
| 1 | 8 | 0.1 | 0.139 | 0.878 | 5.0 | 8.8 | 16.9 | 56.9 |
| 1 | 12 | 0.1 | 0.183 | 0.826 | 7.0 | 12.7 | 18.0 | 60.3 |
| 3 | 1 | 0.1 | 0.113 | 0.904 | 4.0 | 4.4 | 16.4 | 55.0 |
| 3 | 2 | 0.1 | 0.154 | 0.860 | 5.5 | 7.3 | 17.3 | 58.1 |
| 3 | 3 | 0.1 | 0.179 | 0.845 | 7.0 | 10.2 | 17.6 | 59.1 |
| 3 | 5 | 0.1 | 0.237 | 0.769 | 10.0 | 15.4 | 19.4 | 64.7 |
| 3 | 8 | 0.1 | 0.297 | 0.720 | 14.5 | 23.4 | 20.8 | 70.1 |
| 3 | 12 | 0.1 | 0.387 | 0.620 | 20.5 | 34.0 | 24.1 | 80.8 |
| 1 | 1 | 0.5 | 0.105 | 0.914 | 3.5 | 5.1 | 16.3 | 54.4 |
| 1 | 2 | 0.5 | 0.107 | 0.922 | 4.1 | 6.0 | 16.1 | 54.1 |
| 1 | 3 | 0.5 | 0.127 | 0.893 | 4.5 | 6.9 | 16.7 | 56.0 |
| 1 | 5 | 0.5 | 0.151 | 0.866 | 5.5 | 8.8 | 17.1 | 57.1 |
| 1 | 8 | 0.5 | 0.175 | 0.833 | 7.0 | 11.8 | 17.8 | 59.7 |
| 1 | 12 | 0.5 | 0.223 | 0.787 | 9.0 | 15.7 | 18.9 | 63.2 |
| 3 | 1 | 0.5 | 0.214 | 0.803 | 8.0 | 10.0 | 18.6 | 61.9 |
| 3 | 2 | 0.5 | 0.234 | 0.783 | 9.5 | 12.5 | 19.1 | 63.8 |
| 3 | 3 | 0.5 | 0.265 | 0.746 | 11.0 | 15.1 | 19.9 | 67.1 |
| 3 | 5 | 0.5 | 0.282 | 0.731 | 14.1 | 20.4 | 20.6 | 69.6 |
| 3 | 8 | 0.5 | 0.369 | 0.643 | 18.6 | 28.3 | 23.1 | 77.7 |
| 3 | 12 | 0.5 | 0.422 | 0.579 | 24.5 | 38.6 | 25.8 | 86.2 |

The reference points of Q3, at 0.1 s links: testnet 0.3.0's Blend (1 hop, 1 round) gives an
orphan share of 0.042; the specification's (3 hops, up to 3 rounds) gives 0.179. The time to depth
is the canonical chain's: with no attack, 30 blocks take 15–25 minutes and 100 blocks 50–90
minutes across the table.

**The release round.** The engine starts a block's cascade at the block's slot. The Blend
specification releases every generated message at the next round, one round later
(`tsi_sim`, `blend_release_next_round`). The study keeps the engine's release: it is the
convention of the specification's stake-inference analysis, whose 0.15 the engine reproduces
above, and of the TSI report. Measured on the specification's row
(`scripts/a1_baseline.py release`, `runs/a1/release.csv`), with both releases of a run drawing the
same stake, graph, lottery and mixing delays ("paired"), and on A1's own seeds:

| seeds | runs | released | orphan share ± sem | growth / f ± sem | change, run by run | depth at 1e-9: 25 % / 30 % / a third |
| --- | --- | --- | --- | --- | --- | --- |
| A1's, its row | 8 | at the slot | 0.179 ± 0.005 | 0.845 ± 0.007 | – | 88 / 165 / 276 |
| A1's | 32 | at the slot | 0.182 ± 0.002 | 0.834 ± 0.004 | – | 91 / 172 / 291 |
| paired | 32 | at the slot | 0.180 ± 0.004 | 0.832 ± 0.005 | – | 91 / 173 / 294 |
| paired | 32 | at the next round | 0.199 ± 0.004 | 0.812 ± 0.005 | -0.0196 ± 0.0007 | 96 / 186 / 324 |

The depth is B5's closed form at the growth, the report's convention. On B3's settings, with a
coalition withholding and honest relays, as G6 plays the race, 64 paired runs a cell:

| α | copies | runs | orphans: at the slot / next round | growth / win: at the slot / next round | change, run by run | depth at 1e-9 |
| --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 1 | 64 | 0.150 / 0.168 | 0.846 / 0.829 | -0.0176 ± 0.0004 | 88 / 92 (+5%) |
| 0.30 | 1 | 64 | 0.142 / 0.159 | 0.853 / 0.836 | -0.0171 ± 0.0004 | 160 / 170 (+6%) |
| 0.33 | 1 | 64 | 0.137 / 0.153 | 0.863 / 0.846 | -0.0164 ± 0.0004 | 255 / 274 (+7%) |
| 0.25 | 2 | 64 | 0.135 / 0.153 | 0.862 / 0.844 | -0.0180 ± 0.0004 | 84 / 88 (+5%) |
| 0.30 | 2 | 64 | 0.128 / 0.145 | 0.867 / 0.850 | -0.0172 ± 0.0003 | 153 / 162 (+6%) |
| 0.33 | 2 | 64 | 0.122 / 0.139 | 0.878 / 0.860 | -0.0174 ± 0.0004 | 240 / 258 (+7%) |

- **The engine's release is a round optimistic.** Released at the next round, every block waits
  one round more: the honest orphan share rises by about two points and the growth falls by
  0.016–0.020, measured run by run to within 0.001. The depth at `1e-9` grows by 5–7 % against a
  withholding coalition and by 5–10 % at the convention's growth, most against a third: 294 to
  324 blocks.
- **Eight runs leave the convention's growth a sampling error of about 0.007.** A1's eight runs
  of the specification's row give 0.845; the same seeds over 32 runs give 0.834, and 32 other
  runs 0.832. With them the convention's depths are 172–173 and 291–294 blocks against 30 % and
  a third, where 0.845 gives 165 and 276. Read as the depth of a chain on which every node
  produces, A1's growth is therefore low by about 5 % from sampling, and by 5–10 % more from the
  release round.

**The convention, and the attack it stands for.** The report's random-delay depths read B5's
closed form at A1's growth, eight runs on Pareto stakes, canonical blocks per slot over `f`: the
report's convention, 165 / 276 blocks against 30 % / a third. G6 and G7 read the same form at the
growth per honest win on B3's engine, whose stakes are equal. Per win takes the adversary's rate
as `α·λ`, with `λ = −ln(1 − f) = 1.017·f`, where per `f` takes `α·f`; its exact rate,
`1 − (1 − f)^α`, lies between. With every node producing, one copy released at the slot
(`scripts/a1_convention.py`, `runs/a1/convention.csv`):

| setting | runs | orphan share ± sem | growth / f ± sem | growth / win | depth at 1e-9, 30 %: per f / exact / per win | depth at 1e-9, a third: per f / exact / per win |
| --- | --- | --- | --- | --- | --- | --- |
| A1, Pareto stakes | 8 | 0.179 ± 0.005 | 0.845 ± 0.007 | 0.831 | 165 / 170 / 173 | 276 / 288 / 294 |
| A1, Pareto stakes | 32 | 0.182 ± 0.002 | 0.834 ± 0.004 | 0.820 | 172 / 178 / 181 | 291 / 304 / 311 |
| A1's seeds, equal stakes | 32 | 0.191 ± 0.001 | 0.819 ± 0.003 | 0.805 | 181 / 188 / 191 | 313 / 328 / 336 |
| B3's engine, equal stakes | 64 | 0.192 ± 0.001 | 0.822 ± 0.002 | 0.808 | 179 / 186 / 189 | 307 / 322 / 329 |

- **Three things lower the growth the convention reads, each worth 5–8 % of depth against a
  third:** more runs, 0.845 to 0.834 per `f` and 276 to 291 blocks; equal stakes on the same
  seeds, 0.834 to 0.819 and 291 to 313; and the unit, 313 per `f`, 328 at the exact rate and 336
  per win. B3's engine with every node producing gives 329 per win, about a standard error from
  A1's seeds on equal stakes, and 337 with the specification's two copies released a round later
  (`FURTHER.md` G7). The engine's arms of G6 and G7 are read per win, which overstates the
  adversary's rate by 0.6 %.
- **The attack the convention stands for needs less.** A coalition that withholds every win
  orphans no honest block with its own, so the chain it withholds from grows faster than one on
  which every node produces. With honest relays its race needs 158 / 257 blocks with one copy
  released at the slot and 160 / 261 with the specification's two copies released a round later
  (`FURTHER.md` G7; 162 / 258 in the paired runs above). The convention covers the private attack
  in both setups. It does not cover a chain under a deflated inference, on which the honest stake
  alone produces as every node does here, nor relays that hold or drop blocks (`FURTHER.md` G6,
  G7).

## C1 — block rate against delay

Orphan share · growth / f, 0.1 s links, 8 replicates per cell, by block interval:

| hops | Δ_max | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 0.022 · 0.983 | 0.031 · 0.983 | 0.042 · 0.971 | 0.070 · 0.944 | 0.085 · 0.928 | 0.135 · 0.918 |
| 3 | 1 | 0.058 · 0.944 | 0.079 · 0.933 | 0.113 · 0.904 | 0.146 · 0.869 | 0.198 · 0.827 | 0.271 · 0.766 |
| 3 | 3 | 0.107 · 0.903 | 0.130 · 0.882 | 0.179 · 0.845 | 0.260 · 0.758 | 0.310 · 0.710 | 0.412 · 0.618 |
| 3 | 8 | 0.182 · 0.829 | 0.222 · 0.776 | 0.297 · 0.720 | 0.389 · 0.624 | 0.474 · 0.548 | 0.558 · 0.463 |

Minutes to settle under random Blend delays. Depth is that of the private race with a premined
lead and Cryptarchia's strict tie rule (`SETTLEMENT.md`, B5's closed form), at the attacker's share
of chain-extending blocks `q = α / (α + (1 − α) · growth / f)`. Time per canonical block is the honest
chain's while the coalition withholds: the interval over `(1 − α) · growth / f`. A dash marks more
than 5,000 blocks.

α = 0.10, ε = 1e-9

| hops | Δ_max | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 19 | 14 | 10 | 7 | 5 | 4 |
| 3 | 1 | 20 | 16 | 11 | 8 | 7 | 5 |
| 3 | 3 | 22 | 17 | 12 | 10 | 9 | 8 |
| 3 | 8 | 27 | 23 | 17 | 15 | 15 | 15 |

α = 0.25, ε = 1e-9

| hops | Δ_max | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 88 | 66 | 46 | 33 | 26 | 18 |
| 3 | 1 | 99 | 77 | 56 | 42 | 37 | 32 |
| 3 | 3 | 114 | 91 | 69 | 66 | 62 | 72 |
| 3 | 8 | 148 | 137 | 119 | 138 | 187 | 338 |

α = 0.30, ε = 1e-9

| hops | Δ_max | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 160 | 120 | 84 | 62 | 49 | 34 |
| 3 | 1 | 185 | 145 | 107 | 83 | 76 | 70 |
| 3 | 3 | 217 | 177 | 139 | 147 | 150 | 219 |
| 3 | 8 | 300 | 297 | 281 | 413 | 824 | – |

α = 0.33, ε = 1e-9

| hops | Δ_max | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 253 | 190 | 133 | 100 | 80 | 56 |
| 3 | 1 | 299 | 235 | 179 | 143 | 136 | 136 |
| 3 | 3 | 360 | 301 | 245 | 290 | 327 | 689 |
| 3 | 8 | 537 | 569 | 598 | 1,256 | – | – |

What the surface says:

- **On testnet's Blend, faster blocks settle sooner.** Against 25 % of the stake at `1e-9`, 10 s
  blocks settle in 18 minutes against 46 at 30 s. The race on the engine's timelines needs within
  a few blocks of the same depths at 30, 20 and 15 s (`DAG.md`, E2).
- **On the specification's Blend the closed form over-asks as orphans rise.** B3 checked it at
  30 s blocks only. At 30, 20 and 15 s it needs 88, 113 and 133 blocks, where the race needs 77,
  88 and 92: 69, 66 and 62 minutes against the race's 59, 48 and 40. The chain keeps gaining at
  least to 15 s blocks.
- **With 3 hops of up to 8 rounds the closed form slows as blocks speed up,** from 119 minutes at
  30 s to 338 at 10 s. The race was not run there.
- **From 30 % of the stake faster blocks gain little on the specification's Blend.** The closed
  form needs 139, 147 and 150 minutes against 30 % at 30, 20 and 15 s, and 245, 290 and 327
  against a third. The race, fitted in E2, needs 160, 153 and 144 minutes against a third
  (`DAG.md`). The race is the better estimate at this orphan share; the closed form is the
  conservative side the client rule uses (`SETTLEMENT.md`, B4).
- **H3 holds.** At 30 s blocks the time to settle against a quarter of the stake grows faster than
  `1/(1 − o)` with the orphan share: from testnet's to the specification's Blend, `1/(1 − o)` rises
  by a factor of 1.17, the race's time by 1.29 and the closed form's by 1.5.
- These are random-delay numbers. Under a delay chosen by an adversary, the bounds of Phase B2
  apply instead (`SETTLEMENT.md`).

## C2 — which Blend parameters set the delay

A Blend setting delivers a delay `Δ` when its p99 full delay in A1 is at most `Δ`. Testnet's
Blend, 1 hop of 1 round, delivers 1.8 s. The specification's, 3 hops of up to 3 rounds, delivers
10.2 s, within the 13 s up to which `k = 2160` holds a third of the stake without grinding
(`SETTLEMENT.md`, B2). The trade between privacy and delay is the Blend owners'.

## C3 — a fork choice that weighs referenced uncles

Gaži, Motaqy and Russell give the exact consistency regions of GHOST and of the longest-chain rule
when an adversary delays honest blocks by up to `Δ` (ePrint 2024/1830, revision 2026-09-11, p. 3
and equations (1) and (2)).
Translated into the largest tolerable stake share at `f = 1/30`, the lottery's wins Poisson at
`−ln(1 − f)` per slot:

| rule | 1 s | 2 s | 3 s | 5 s | 8 s | 10 s | 15 s | 20 s | 30 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| longest chain | 0.4958 | 0.4915 | 0.4873 | 0.4788 | 0.4663 | 0.4579 | 0.4374 | 0.4176 | 0.3802 |
| GHOST, deterministic ties | 0.4957 | 0.4914 | 0.4870 | 0.4779 | 0.4637 | 0.4538 | 0.4278 | 0.3996 | 0.3377 |
| GHOST, adversarial ties | 0.4915 | 0.4828 | 0.4740 | 0.4560 | 0.4282 | 0.4093 | 0.3613 | 0.3140 | 0.2280 |

The longest-chain row equals the private-attack threshold of Dembo et al. (gated). GHOST never
tolerates more. The analysis is for proof of work. For proof of stake the paper adds that GHOST
"provides no security (for any parameters) with unconstrained equivocation". Cryptarchia's lottery
lets one win sign blocks on any branch, so a weighted fork choice would also need each win to add
weight once. The win tag `ρ_LEAD` counts a win once on a side (`DAG.md` E3), but no rule every
node applies alike stops a second copy on the other side from moving the balance again (`DAG.md`
J.1). H4 is refuted for a delay chosen by an adversary. Under random delay it was not tested on the chain; E2's DAG, which weighs
every honest block, settles sooner than the chain at the same block rate (`DAG.md`).

**With one weight per win, the depth (`DAG.md` J.2).** The chain with GHOST's weight, each win
weighing once and uncles carrying the orphans, is variant (a) of phase J; its attacks are the
DAG's. If each withheld win moves the balance once, the strongest attack within `Δ` against a
third at `1e-9`, under J.1's fixed tie rule, needs 2.8 hours at 1 s and 5.0 at 10 s, where the
longest-chain rule's attack needs 3.5 and 6.8 (B2). With ties the adversary steers, as the Online
rule's first-seen choice lets it, it needs 17.1 hours at 10 s. But a tag found on both sides weighs
on neither, so a placed win can be retracted by a second copy on the other side and move the
balance twice. The balance's edge at today's block rate then falls to 0.326 of the stake at 1 s
and 0.279 at 10 s under the fixed rule, and a third holds the balance for ever with positive
chance at every delay: no depth holds against it.

## C4 — Ouroboros Taktikos

Taktikos (Schutza, Behrens, Duong and Aman, BlockSys 2023) makes the lottery coefficient a function
`f(δ)` of the slots `δ` since the parent. The paper is behind a paywall. The curve here is Topl's
"snowplow" (wiki.topl.co, Taktikos Proof-of-Stake, archived 2023-03-23): zero up to a gap, a ramp
up to a cutoff, and a low baseline after it. Topl's example has no gap, a cutoff at 40 slots, a
ramp to 0.4 and a baseline of 0.05.

**The proof of leadership needs no new circuit.** The lottery constants `t0` and `t1` are public
inputs computed outside the circuit (`cryptarchia-proof-of-leadership.md`, Circuit Public Inputs).
A verifier would compute them from `f(δ)`, with `δ` read from the header's slot and its parent's.
Four things change all the same:

- A win is valid only on branches whose tip leaves a `δ` with a high enough coefficient.
- The stake inference assumes a constant coefficient, so its estimator must be derived again.
- The lottery approximation is checked at `f = 1/30` and must be checked at the curve's peak.
- B2's bounds assume a constant coefficient; no bound covers a curve.

**The engine.** `src/finality_sim/taktikos.py` builds the block tree as the engine does, and draws
each winner's eligibility from the `δ` to the parent it extends. Gates (`tests/test_taktikos.py`):
with a constant curve the builder reproduces the engine's orphan share, and the curve, its
interval distribution and the renewal draws match direct computation. Four mutations fail them.

The first five curves give the whole stake, producing alone without delay, a block every 30 slots
on average (`scripts/c4_taktikos.py`, `runs/c4/curves.csv`). Eight runs per row, as in A1:

| curve | Blend | orphan share | canonical growth / f | blocks made / f | interval p50 / p99 (s) |
| --- | --- | --- | --- | --- | --- |
| constant | testnet | 0.042 | 0.971 | 1.01 | 22 / 137 |
| constant | specification | 0.177 | 0.847 | 1.03 | 27 / 139 |
| Topl-shaped | testnet | 0.062 | 1.001 | 1.07 | 28 / 72 |
| Topl-shaped | specification | 0.278 | 0.968 | 1.34 | 29 / 72 |
| short cutoff | testnet | 0.084 | 1.002 | 1.09 | 19 / 366 |
| short cutoff | specification | 0.350 | 0.942 | 1.45 | 20 / 405 |
| short cutoff, gap 10 | testnet | 0.123 | 0.991 | 1.13 | 24 / 253 |
| short cutoff, gap 10 | specification | 0.440 | 1.024 | 1.83 | 23 / 225 |
| gap 10 | testnet | 0.061 | 1.000 | 1.06 | 24 / 100 |
| gap 10 | specification | 0.247 | 1.013 | 1.35 | 24 / 98 |
| constant, 20 s | testnet | 0.061 | 1.434 | 1.53 | 15 / 91 |
| constant, 20 s | specification | 0.244 | 1.178 | 1.56 | 20 / 94 |
| constant, 15 s | testnet | 0.082 | 1.904 | 2.07 | 11 / 69 |
| constant, 15 s | specification | 0.303 | 1.442 | 2.07 | 17 / 74 |

- **No curve lowers the orphan share.** Every one raises it, to 0.25–0.44 on the specification's
  Blend. A node that has not yet received the latest block sees a larger `δ` and wins more often.
  The curves therefore also make more blocks: 1.06–1.13 per `1/f` slots on testnet's Blend and
  1.34–1.83 on the specification's, against 1.01 and 1.03 for today's lottery.
- **The intervals become regular** under Topl's shape and a plain 10-slot gap: the 99th
  percentile falls from 139 s to 72–100 s. The short cutoffs stall the chain instead.

The private race of B3 against 25 % and a third of the stake, at the share of targets it
displaces: the depth, and the time to it at the honest chain's rate. 64 runs per point, about
`1e5` targets, so a depth at `1e-4` rests on about ten successes. The coalition's chain is drawn
from its own last block, while a coalition that falls back to the public tip would restart its
interval there. For the 10-slot gap, whose coefficient only rises, these numbers therefore favour
the attacker. For the curves that fall after their cutoff, Topl's shape and the short cutoffs,
they favour the honest side.

| curve | Blend | α = 0.25: 1e-3 / 1e-4 | α = 0.33: 1e-3 / 1e-4 |
| --- | --- | --- | --- |
| constant | testnet | 19 (13 min) / 27 (18 min) | 48 (37 min) / 59 (45 min) |
| constant | specification | 23 (18 min) / 32 (25 min) | 58 (50 min) / > 60 |
| Topl-shaped | testnet | 20 (12 min) / 31 (18 min) | 49 (30 min) / > 60 |
| Topl-shaped | specification | 20 (12 min) / 28 (17 min) | > 60 / > 60 |
| short cutoff | testnet | 15 (13 min) / 22 (19 min) | 56 (63 min) / > 60 |
| short cutoff | specification | 23 (21 min) / 33 (30 min) | 56 (66 min) / > 60 |
| short cutoff, gap 10 | testnet | 20 (15 min) / 28 (21 min) | > 60 / > 60 |
| short cutoff, gap 10 | specification | 20 (15 min) / 23 (18 min) | 56 (54 min) / > 60 |
| gap 10 | testnet | 19 (12 min) / 25 (15 min) | 49 (32 min) / > 60 |
| gap 10 | specification | 19 (12 min) / 25 (15 min) | 41 (27 min) / 52 (34 min) |
| constant, 20 s | testnet | 19 (9 min) / 27 (12 min) | 50 (26 min) / > 60 |
| constant, 20 s | specification | 26 (14 min) / 34 (19 min) | > 60 / > 60 |
| constant, 15 s | testnet | 20 (7 min) / 27 (9 min) | 49 (19 min) / > 60 |
| constant, 15 s | specification | 28 (12 min) / 37 (16 min) | > 60 / > 60 |

- **On the specification's Blend, Topl's shape and the 10-slot gap settle against 25 % in 12
  minutes at `1e-3`**, against 18 for today's lottery. A constant lottery at 20 s blocks takes 14
  minutes and makes more blocks (1.56 per `1/f` slots against 1.34–1.35).
- **On testnet's Blend, where forks are rare, the gain is small:** 12 minutes against 13 at
  `1e-3`.
- **The short cutoffs** cut a lone coalition's rate to a quarter of today's (0.065 against 0.25 of
  `f` at 25 %). The honest chain stalls too, and they settle no faster than Topl's shape.
- **Topl's shape raises a lone coalition's rate** to 0.378 of `f` against 0.253 at 25 %
  (`runs/c4/curves.csv`). Against a third on the specification's Blend it does not reach `1e-3`
  within 60 blocks, where today's lottery needs 58.
- **L3 through Taktikos:** fewer orphans fails. What remains is a regular block interval that,
  on the specification's Blend, settles against a quarter of the stake in two thirds of the time,
  at the cost of more blocks. It needs a new stake inference and has no worst-case bound.

## Counted in slots (Phase K)

With `k` counted in slots (`SLOTS.md` K.0), k-finality lasts `K` slots at any block rate. Counted
in blocks, `k = 2160` lasts 18 hours at 30 s blocks with no forks and 9 hours at 15 s. What a
faster block rate can still change is the `K` that holds a share. At `ε = 1e-9`, on the
specification's Blend, against each share: B5's closed form at C1's growth on C1's clock and the
wait `slots.wait_needed` gives under random delay; B2's upper bound at `Δ = 10` s on the worst-case
clock `Δ + 1/p_h`, and the wait `slots.worst_needed` bounds. B2's port counts time in block
intervals, `D = f·Δ`, so at `Δ = 10` s 20 s blocks read the bound 30 s blocks read at 15 s, and
15 s blocks the bound they read at 20 s (`scripts/k5_rate.py`):

| block interval | α | random delay: B5's depth | random delay: a wait | worst, 10 s: B2's depth | worst, 10 s: a wait, bound |
| --- | --- | --- | --- | --- | --- |
| 30 s | 0.25 | 88 (1.2 h) | 1.7 h | 474 (6.6 h) | 8.3 h |
| 30 s | 0.30 | 165 (2.3 h) | 3.1 h | 892 (13.0 h) | 15.5 h |
| 30 s | 0.33 | 276 (4.1 h) | 5.1 h | 1,510 (23.0 h) | 26.3 h |
| 20 s | 0.25 | 113 (1.1 h) | 1.5 h | 661 (6.7 h) | 8.1 h |
| 20 s | 0.30 | 234 (2.4 h) | 3.1 h | 1,325 (14.1 h) | 16.1 h |
| 20 s | 0.33 | 440 (4.8 h) | 5.7 h | 2,426 (26.8 h) | 29.6 h |
| 15 s | 0.25 | 133 (1.0 h) | 1.4 h | 971 (8.0 h) | 9.2 h |
| 15 s | 0.30 | 298 (2.5 h) | 3.0 h | 2,105 (18.2 h) | 20.1 h |
| 15 s | 0.33 | 620 (5.5 h) | 6.2 h | 4,282 (38.4 h) | 41.1 h |

- **Under the worst case a faster block rate needs a longer `K`.** A fixed delay costs more block
  intervals as blocks speed up. Against a third the wait grows from 26.3 hours at 30 s blocks to
  29.6 at 20 s and 41.1 at 15 s, and against 30 % from 15.5 to 16.1 and 20.1. Against a quarter it
  moves within an hour, 8.3, 8.1 and 9.2 hours.
- **Under random delay a faster rate shortens the wait against a quarter only.** In B5's closed
  form the wait falls from 1.7 to 1.4 hours against a quarter, holds at 3.0–3.1 against 30 %, and
  grows from 5.1 to 6.2 against a third. The closed form over-asks as orphans rise; the race fitted
  in E2 gains 10 % against a third at 15 s blocks (C1), so the growth there is the closed form's.
- **`k` counted in slots takes the block rate out of finality's time.** Counted in blocks, faster
  blocks shorten k-finality in proportion; counted in slots they shorten it only through the `K`
  the worst case allows, and at `Δ = 10` s that `K` grows.
