# Rate and forks

Phase C of `PLAN.md`, with the Phase A1 baseline it builds on. Every table is generated from
`runs/` by `scripts/tables.py`; the runs come from `scripts/a1_baseline.py`, `scripts/c1_rate.py`,
`scripts/c1_settle_surface.py`, `scripts/c3_ghost.py` and `scripts/c4_taktikos.py`.

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

## C1 — block rate against delay

Orphan share · growth / f, 0.1 s links, 8 replicates per cell, by block interval:

| hops | Δ_max | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 0.022 · 0.983 | 0.031 · 0.983 | 0.042 · 0.971 | 0.070 · 0.944 | 0.085 · 0.928 | 0.135 · 0.918 |
| 3 | 1 | 0.058 · 0.944 | 0.079 · 0.933 | 0.113 · 0.904 | 0.146 · 0.869 | 0.198 · 0.827 | 0.271 · 0.766 |
| 3 | 3 | 0.107 · 0.903 | 0.130 · 0.882 | 0.179 · 0.845 | 0.260 · 0.758 | 0.310 · 0.710 | 0.412 · 0.618 |
| 3 | 8 | 0.182 · 0.829 | 0.222 · 0.776 | 0.297 · 0.720 | 0.389 · 0.624 | 0.474 · 0.548 | 0.558 · 0.463 |

Minutes to settle under random Blend delays. Depth is that of the private race from the target's
parent, without a premined lead, and Cryptarchia's strict tie rule, at the attacker's share of
chain-extending blocks `q = α / (α + (1 − α) · growth / f)`. Time per canonical block is the honest
chain's while the coalition withholds: the interval over `(1 − α) · growth / f`.

α = 0.1, ε = 1e-9

| hops | Δ_max | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 19 | 14 | 10 | 7 | 5 | 4 |
| 3 | 1 | 20 | 15 | 11 | 8 | 6 | 5 |
| 3 | 3 | 22 | 17 | 12 | 10 | 9 | 8 |
| 3 | 8 | 25 | 23 | 17 | 15 | 15 | 15 |

α = 0.25, ε = 1e-9

| hops | Δ_max | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 87 | 65 | 45 | 32 | 26 | 18 |
| 3 | 1 | 97 | 76 | 55 | 42 | 36 | 31 |
| 3 | 3 | 111 | 90 | 68 | 64 | 61 | 70 |
| 3 | 8 | 145 | 134 | 117 | 135 | 182 | 329 |

What the surface says:

- **On testnet's Blend, faster blocks settle sooner.** Against 25 % of the stake at `1e-9`, 10 s
  blocks settle in 18 minutes against 45 at 30 s. The race on the engine's timelines needs within
  two blocks of the same depths at 30, 20 and 15 s (`DAG.md`, E2).
- **On the specification's Blend the closed form over-asks as orphans rise.** B3 checked it at
  30 s blocks only. At 30, 20 and 15 s it needs 86, 110 and 130 blocks, where the race needs 77,
  88 and 92: 68, 64 and 61 minutes against the race's 59, 48 and 40. The chain keeps gaining at
  least to 15 s blocks.
- **With 3 hops of up to 8 rounds the closed form slows as blocks speed up,** from 117 minutes at
  30 s to 329 at 10 s. The race was not run there.
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
weight once (`PLAN.md` E3 names the tag that could enforce it, `ρ_LEAD`). H4 is refuted for a delay
chosen by an adversary. Under random delay it was not tested on the chain; E2's DAG, which weighs
every honest block, settles sooner than the chain at the same block rate (`DAG.md`).

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
