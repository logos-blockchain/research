# The multi-proposer DAG (Areon)

Phase E of `PLAN.md`. Paper: Castro-Castilla, Pawlowski, Zhou, "Areon: Latency-Friendly and
Resilient Multi-Proposer Consensus", arXiv 2511.23025v1. Simulator: `~/Logos/areon-simulations`,
commit `4230a92`, notebook `areon-full.ipynb` (Q9). The notebook was read, not modified. The audit
worked on copies under the session scratchpad.

Status: E0–E6 done. The owner chose to build Areon-Base on the TSI engine (E1). Phase J's J.0–J.3
are done, and the phase stops at J.2: a coalition that retracts its wins holds a third's balance
for ever at every delay (J.1, J.2), so no attack depth and no bound exist against a third (J.3).

## E0 — the audit

Each item below is marked by how it was established:

- **[verified]** read again in the notebook source for this note;
- **[verified, earlier]** read in the notebook source during the audit, and not again;
- **[audit]** established by the audit's re-runs and measurements, which this note has not
  repeated;
- **[preliminary]** an audit experiment too small to rely on.

Cell and line numbers are the notebook's.

**What the simulator models.**

- **No fork choice runs.** [verified] The Areon cells hold no closest-common-ancestor comparison,
  no conflicted-tips resolution and no preferred frontier; "conflict" appears only in a
  docstring and a comment (cell 11, lines 334–335 and 399). Honest blocks reference the maximum antichain of the visible blocks in the window.
  An attack is scored afterwards as a race of cumulative windowed weights, which honest nodes
  never see or react to. The paper's fork choice (§2.2.3, Alg. 7) is therefore not what the
  figures measure.
- **Payload dependencies have no effect.** [verified] Cell 11, line 281:
  `parents = blk.refs if self.params.use_deps else blk.refs`; both branches are the same. No
  conflict predicate exists, though §6.2 says dependencies are enforced.
- **Smaller departures from Alg. 5–7.** [audit]
  - Blocks may reference both a block and its ancestor; Alg. 6 would reject that. At a 10 s mean
    delay this is 6.8 % of honest blocks.
  - Blocks may reference blocks whose parents their producer has not received (14.5 % of short
    references).
  - A long reference is added even when short ones exist.
  - The window is effectively 29 slots, not 30.
- **Arrival times are truncated.** [verified, earlier] Arrivals are stored as `int32`, which
  shifts the delay axis by under one slot. The audit found the Praos baseline truncates the same
  way.
- **Delays are unbounded exponentials.** [verified, earlier] The paper's `w ≥ Δ` therefore holds
  only for the mean delay. [audit] The paper's stated default of 7.5 s appears in no cell. The
  cells use 10 s, sweeps of 2–90 s, 5–60 s and 2–15 s.
- **One adversary identity.** [verified, earlier] It wins at most one block per slot. [audit]
  Because the lottery is concave and honest stake is split across 1,000 nodes, a single identity
  produces fewer blocks than its share: 4.2 % fewer at 30 % stake and `f = 0.25`. The paper's
  §6.3 reads this "parallelism bias" the other way.

**Which attack produced the figures.**

- **Greedy, everywhere.** [verified] Every figure cell attacks through `attack_on_block`, which
  calls the greedy attack. The ILP attack has no caller.
- **The ILP is stronger.** [audit] On 746 targets (`f = 0.25`, 30 % stake, 10 s mean delay,
  800 slots), the ILP found 180 successful attacks against greedy's 112, and 80 of at least 30
  slots against 40. With two one-line repairs to the ILP the counts were 255 and 120. The figures
  therefore understate the attack.

**Where the figures came from.**

- [audit] Only the paper's Fig. 10 matches a committed cell's configuration.
- Figs. 8, 9 and 11–14 differ from the committed cells in grid, run length or values, so the
  notebook as committed does not regenerate them.
- The committed cells' own recorded outputs reproduce bit for bit.

**The comparison with Praos.**

- **Different block rates.** [verified] The headline compares Areon at `f = 0.25` (Fig. 12) with
  Praos at `f = 0.05` (Fig. 11).
- **Different metrics.** [verified] The Praos side (cell 37, lines 229–255) starts a private
  chain from every block, orphans included. It records a reorg event at every active slot where
  that chain would be longer, so one target contributes many events. The Areon side records one
  value per attacked block.
- **No match for one quoted value.** [audit] The quoted "Praos 10-block ≈ 7 × 10⁻¹" matches no
  figure. The audit digitised Fig. 11 at about 0.042 for depth 10.
- **Measured alike.** [preliminary] At equal `f = 0.05`, one value per target, one seed and 935
  Areon targets, Areon showed no advantage. The share of targets with a reorg of at least 300
  slots was 0.187 against Praos's 0.150 at a 10 s delay, and 0.104 against 0.056 at 2 s.

**Units.** [verified, earlier] A "virtual block" is 30 slots (cells 22, 24). [audit] Ten virtual
blocks correspond to 13–28 short-reference hops depending on `f` and the delay. Virtual blocks
are therefore not the `k` of Theorem 5.6.

## What E0 means for Phase E

The notebook cannot serve as a reproduction gate for the paper's figures. Its figures measure a
reference-selection rule and a greedy weight race, not the paper's fork choice. Several of them
do not come from the committed cells. Its comparison with Praos mixes block rates and metrics.
H7 cannot be judged from the paper's numbers, so E1 builds Areon-Base instead of reproducing it.
The owner chose that route.

## E1 — Areon-Base on the engine

`src/finality_sim/areon.py` builds the honest DAG of one epoch from the engine's lottery, topology
and Blend delays, and plays B3's private race on it (`scripts/e2_areon.py`). Where the paper leaves
a rule open, the implementation makes this choice:

- **Weight.** The subDAG weight of §2.2.3 sums over `Desc*(i)`, which for a tip `i` is `{i}`. The
  drift argument (Def. 5.3, Lemma 5.5) needs the weight accumulated since the fork. Here the fork
  point is the target's parent. The honest side weighs the target and the blocks that descend from
  it. The coalition's side weighs its own blocks since the fork, or since its premining began. A
  coalition block that references an honest block does not move that block to its side.
- **Unit.** §2.2.3 counts a block's short references; §5.3 counts each block once (`wref ∈ {0,
  1}`). Here each block with a short reference counts once, and a block with only a long reference
  counts nothing. Counting references would let a coalition shape its private DAG wide: `m` blocks
  each referencing the same `m` others give `m²` references for `2m` blocks. A coalition block
  counts once if the latest block on its side is at most `w` slots older: its previous block, the
  fork point or, while it premines with no lead, the public tip. An honest block references only
  what its producer has seen, so it counts in fewer cases.
- **Horizon.** §5.3 says only references of the last `w` slots count; the drift argument
  accumulates the gap since the fork. Both are measured.
- **References.** Alg. 5 references a maximum antichain of the windowed DAG. Here an honest block
  references every tip of its view in the window, the coverage `q = 1` of §4.1.1, and only tips of
  its preferred frontier, so a defeated subDAG receives no honest reference (E4).
- **Depth.** The height of a block's descendants above it, along references (Def. 5.1).
- **Wins.** Each lottery win makes one block (E3).

The race: a coalition holding `α` withholds its wins and builds a private subDAG that conflicts
with the target. It may hold a premined lead. Honest blocks that do not descend from the target
count for neither side. Counted for the honest side instead, they lower E2's depths by at most 2
layers (`runs/e2/race.csv`). The receiver accepts the target at depth `K`; the attack succeeds if
the coalition's weight then exceeds the honest weight.

Gates (`tests/test_areon.py`): honest blocks reference exactly the tips their producer holds, and
heights and arrivals follow the parents. A full mesh delays each block by its latency, and without
delay a block references the last occupied slot. On a chain-shaped DAG the race equals B3's chain
race, count for count. The weight rules, the coalition's window and the recent-window score match
hand-counted cases. Eleven mutations fail them.

## E2 — at Cryptarchia's parameters

The production coefficient `f_A`, written `f` in the tables, runs from Cryptarchia's `1/30` to the
paper's 0.25. The window is
the paper's 30 slots at 0.25, stretched with the block interval (`w = 7.5/f_A`). Four runs per row,
Pareto stake, 0.1 s links:

| f_A | Blend | window | blocks per slot / Cryptarchia's | s per layer | references mean / p99 | long only, w = 30 / own w |
| --- | --- | --- | --- | --- | --- | --- |
| 0.0333 | testnet | 225 | 1.02 | 30.9 | 1.04 / 2.0 | 0.362 / 0.000 |
| 0.0333 | specification | 225 | 1.01 | 36.9 | 1.24 / 3.0 | 0.456 / 0.000 |
| 0.0333 | heavy | 225 | 1.03 | 43.5 | 1.49 / 3.5 | 0.563 / 0.001 |
| 0.05 | testnet | 150 | 1.53 | 21.1 | 1.07 / 2.0 | 0.229 / 0.000 |
| 0.05 | specification | 150 | 1.56 | 26.3 | 1.36 / 3.0 | 0.298 / 0.000 |
| 0.05 | heavy | 150 | 1.54 | 32.2 | 1.66 / 4.0 | 0.426 / 0.001 |
| 0.0667 | testnet | 112 | 2.05 | 16.1 | 1.10 / 2.0 | 0.132 / 0.000 |
| 0.0667 | specification | 112 | 2.11 | 20.9 | 1.47 / 3.8 | 0.186 / 0.001 |
| 0.0667 | heavy | 112 | 2.09 | 27.9 | 1.94 / 5.0 | 0.318 / 0.001 |
| 0.1 | testnet | 75 | 3.10 | 10.7 | 1.11 / 2.2 | 0.047 / 0.000 |
| 0.1 | specification | 75 | 3.24 | 15.6 | 1.69 / 4.0 | 0.082 / 0.000 |
| 0.1 | heavy | 75 | 3.16 | 21.2 | 2.27 / 5.5 | 0.168 / 0.002 |
| 0.25 | testnet | 30 | 8.53 | 5.0 | 1.44 / 3.5 | 0.000 / 0.000 |
| 0.25 | specification | 30 | 8.59 | 9.9 | 2.83 / 6.5 | 0.001 / 0.001 |
| 0.25 | heavy | 30 | 8.37 | 9.8 | 3.17 / 7.2 | 0.008 / 0.008 |

- **The window must span the block interval, not only `Δ`.** At `f_A = 1/30` a 30-slot window
  leaves 36–56 % of honest blocks with only a long reference, and so without weight.
- **The DAG is narrow.** A block references 1.0–3.2 tips on average, and 2.0–7.2 at the 99th
  percentile.

The private race, 40,720–73,071 targets per point: the depth in layers (DAG) or blocks (chain) at
which the share of displaced targets falls to `1e-3` / `1e-4`, with the time to that depth in
minutes. The chain rows are C4's constant lotteries (`RATE.md`), raced the same way:

| structure | f | Blend | α = 0.10 | α = 0.25 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| DAG | 0.0333 | testnet | 4 (2.3) / 6 (3.4) | 16 (10.8) / 21 (14.2) | 40 (30.4) / 53 (40.3) |
| DAG | 0.0333 | specification | 4 (2.7) / 6 (4.0) | 15 (11.6) / 19 (14.7) | 40 (34.1) / 48 (40.9) |
| DAG | 0.05 | testnet | 3 (1.2) / 5 (1.9) | 17 (7.8) / 24 (11.0) | 46 (23.6) / 54 (27.7) |
| DAG | 0.05 | specification | 4 (1.9) / 7 (3.4) | 15 (8.3) / 19 (10.5) | 36 (21.7) / 45 (27.2) |
| DAG | 0.0667 | testnet | 4 (1.2) / 6 (1.8) | 16 (5.5) / 20 (6.9) | 49 (19.0) / 57 (22.1) |
| DAG | 0.0667 | specification | 4 (1.5) / 7 (2.7) | 16 (7.0) / 19 (8.3) | 37 (17.6) / 42 (20.0) |
| DAG | 0.1 | testnet | 4 (0.8) / 6 (1.2) | 17 (4.0) / 26 (6.1) | 40 (10.4) / 45 (11.7) |
| DAG | 0.1 | specification | 4 (1.2) / 5 (1.5) | 15 (4.9) / 19 (6.2) | 36 (12.7) / 44 (15.5) |
| DAG | 0.25 | testnet | 4 (0.4) / 6 (0.5) | 15 (1.5) / 22 (2.3) | 43 (4.8) / 53 (5.9) |
| DAG | 0.25 | specification | 4 (0.7) / 5 (0.9) | 11 (2.1) / 13 (2.5) | 28 (5.6) / 39 (7.8) |
| chain | 0.0333 | testnet | 4 (2.3) / 6 (3.4) | 19 (13.0) / 27 (18.4) | 48 (36.5) / 59 (44.9) |
| chain | 0.0333 | specification | 4 (2.6) / 6 (4.0) | 23 (17.7) / 32 (24.6) | 58 (49.6) / > 60 |
| chain | 0.05 | testnet | 4 (1.5) / 6 (2.3) | 19 (8.7) / 27 (12.4) | 50 (25.6) / > 60 |
| chain | 0.05 | specification | 4 (1.9) / 7 (3.3) | 26 (14.2) / 34 (18.6) | > 60 / > 60 |
| chain | 0.0667 | testnet | 4 (1.2) / 6 (1.8) | 20 (7.0) / 27 (9.4) | 49 (19.0) / > 60 |
| chain | 0.0667 | specification | 5 (1.9) / 8 (3.1) | 28 (12.2) / 37 (16.2) | > 60 / > 60 |

- **At the same block rate the DAG settles faster than the chain.** Against 25 % on the
  specification's Blend at `f = 1/30`, 15 layers (11.6 minutes) against 23 blocks (17.7). Against
  a third, 34 minutes against 50. No honest block is wasted, while the chain discards its orphans.
- **Raising the block rate pays more on the DAG.** Against 25 % on the specification's Blend, at
  30, 20 and 15 s blocks the DAG needs 11.6, 8.3 and 7.0 minutes and the chain 17.7, 14.2 and
  12.2; the DAG needs 4.9 minutes at `f_A = 0.1` and 2.1 at 0.25.

The paper's §5.6 procedure fits `P(d) ≈ A·e^{−ϱd}` to each curve and reads
`d*(ε) = ln(A/ε)/ϱ`, here over the depths whose share lies in `[1e-4, 1e-1]`. Applied to the
chain's premined race in closed form at B3's measured `q`, the fit lands 3–5 % short of the exact
depth at `1e-9` (`tests/test_e2_fit.py`). At `α = 0.10` each fit rests on 3–7 depths. Extrapolated
to `ε = 1e-9`, the depth and, in brackets, the minutes (`scripts/e2_fit.py`, `runs/e2/fit.csv`; the
same fit is applied to the chain):

| structure | f | Blend | α = 0.10 | α = 0.25 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| DAG | 0.0333 | testnet | 17 (10) | 57 (38) | 132 (101) |
| DAG | 0.0333 | specification | 15 (10) | 49 (38) | 124 (106) |
| DAG | 0.05 | testnet | 12 (5) | 58 (27) | 149 (77) |
| DAG | 0.05 | specification | 16 (8) | 52 (29) | 115 (70) |
| DAG | 0.0667 | testnet | 20 (6) | 55 (19) | 163 (63) |
| DAG | 0.0667 | specification | 19 (7) | 53 (23) | 121 (58) |
| DAG | 0.1 | testnet | 15 (3) | 66 (15) | 123 (32) |
| DAG | 0.1 | specification | 15 (4) | 48 (16) | 111 (39) |
| DAG | 0.25 | testnet | 16 (1) | 59 (6) | 141 (16) |
| DAG | 0.25 | specification | 11 (2) | 31 (6) | 100 (20) |
| chain | 0.0333 | testnet | 16 (9) | 67 (46) | 152 (116) |
| chain | 0.0333 | specification | 18 (12) | 77 (59) | 188 (160) |
| chain | 0.05 | testnet | 15 (6) | 69 (32) | 175 (89) |
| chain | 0.05 | specification | 18 (9) | 88 (48) | 254 (153) |
| chain | 0.0667 | testnet | 17 (5) | 69 (24) | 166 (64) |
| chain | 0.0667 | specification | 20 (8) | 92 (40) | 302 (144) |

Against 25 % on the specification's Blend, the DAG reaches `1e-9` in 38 minutes at Cryptarchia's
block rate, against 59 for the chain, and in 16 and 6 minutes at ×3.2 and ×8.6 the blocks.

**The paper's prose horizon gives no finality.** Counting only the last `w` slots, the share of
targets the coalition displaces at depth 10 / 40 (strictly heavier, concurrent honest blocks
counted for the honest side):

| f | Blend | α = 0.10 | α = 0.25 | α = 0.33 |
| --- | --- | --- | --- | --- |
| 0.0333 | testnet | 0.21 / 0.19 | 0.96 / 0.93 | 1.00 / 0.98 |
| 0.0333 | specification | 0.29 / 0.25 | 0.97 / 0.93 | 1.00 / 0.98 |
| 0.05 | testnet | 0.21 / 0.19 | 0.97 / 0.94 | 1.00 / 0.98 |
| 0.05 | specification | 0.25 / 0.22 | 0.96 / 0.93 | 1.00 / 0.99 |
| 0.0667 | testnet | 0.29 / 0.26 | 0.96 / 0.94 | 1.00 / 0.99 |
| 0.0667 | specification | 0.26 / 0.23 | 0.97 / 0.95 | 1.00 / 0.99 |
| 0.1 | testnet | 0.22 / 0.21 | 0.98 / 0.97 | 1.00 / 0.99 |
| 0.1 | specification | 0.17 / 0.15 | 0.98 / 0.96 | 1.00 / 0.99 |
| 0.25 | testnet | 0.20 / 0.19 | 0.99 / 0.98 | 1.00 / 1.00 |
| 0.25 | specification | 0.22 / 0.18 | 1.00 / 0.99 | 1.00 / 1.00 |

The share does not fall with depth: a coalition that keeps its private subDAG alive outweighs the
honest side in some window of the 60 after the target. Theorem 5.6 holds only for the weight
accumulated since the fork.

## E3 — private eligibility

- **One win must weigh once on a side, and still moves a balance twice.** Cryptarchia's ticket
  does not depend on the parent, so one win can sign several blocks. In a DAG they can sit side by
  side in one subDAG, or one in each of two conflicting subDAGs, and add weight each time. The
  weight must count each
  `ρ_LEAD` once in a subDAG: GHOST "provides no security (for any parameters) with unconstrained
  equivocation" (Gaži, Motaqy and Russell, ePrint 2024/1830, revision 2026-09-11, p. 8). Across
  two conflicting subDAGs no rule every node applies alike makes a win weigh once. If a tag found
  in both weighs in both, the win adds one to each side. If it weighs in neither, the rule this
  note first took, a second copy retracts the first. Either way one win moves the balance twice,
  so it keeps two subDAGs balanced at half the cost of fresh wins (J.1).
- **A coalition in small notes gets its share.** A note holding `s` of the stake wins a slot with
  probability `1 − (1 − f_A)^s`, so many small notes win at `−s·ln(1 − f_A)` per slot, linear in
  `s`. E2's coalition, 0.1 % of the stake per node, made blocks within 3 % of `α/(1 − α)` of the
  honest side's at every `f_A` (`runs/e2/race.csv`). The single-identity bias of the paper's §6.3
  then does not arise.

## E4 — the ledger

- **Order.** Mantle executes transactions in order. A total order over `Anc*(F_t)` can be
  topological, with ties broken by `(slot, y)`; a transaction that conflicts with an earlier one is
  skipped. The order must place a block after every block settled before it was first referenced;
  otherwise a late block with an early slot would skip a transaction already settled.
- **Conflicts.** The fork choice must have settled every conflict before the order is read. Alg. 5
  as written references a maximum antichain of the whole windowed DAG, defeated subDAGs included.
  Honest blocks would then merge both sides of a double spend, and the order alone would decide
  which one stands. Honest blocks must reference only their preferred frontier, as E1 does.
- **Stake inference.** No honest block is orphaned, so the inference can count blocks instead of
  occupied slots. Their expectation, `−s·ln(1 − f_A)` per slot for participating share `s` held in
  small notes, is linear in `s` (E3).

## E5 — delay chosen by an adversary

A full mesh whose links take `Δ` slots delivers every honest block exactly `Δ` late
(`scripts/e5_delay.py`; the race of E2, the window E2's and at least `Δ + 1`, and at `f_A = 0.25`
also `Δ + 30`). The depth at which the displaced share falls to `1e-3`, with minutes:

| f | Δ | window | α = 0.10 | α = 0.25 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| 0.0333 | 1 s | 225 | 4 (2.2) | 19 (12.6) | 42 (31.5) |
| 0.0333 | 5 s | 225 | 4 (2.5) | 16 (11.6) | 34 (27.5) |
| 0.0333 | 10 s | 225 | 4 (2.8) | 15 (12.2) | 39 (34.8) |
| 0.0333 | 20 s | 225 | 4 (3.5) | 13 (12.7) | 38 (40.0) |
| 0.25 | 1 s | 30 | 4 (0.3) | 18 (1.5) | 42 (4.0) |
| 0.25 | 1 s | 31 | 4 (0.3) | 18 (1.5) | 46 (4.4) |
| 0.25 | 5 s | 30 | 3 (0.4) | 13 (2.0) | 35 (5.7) |
| 0.25 | 5 s | 35 | 3 (0.4) | 13 (2.0) | 34 (5.5) |
| 0.25 | 10 s | 30 | 4 (0.9) | 11 (2.6) | 21 (5.2) |
| 0.25 | 10 s | 40 | 4 (0.9) | 11 (2.6) | 19 (4.7) |
| 0.25 | 20 s | 30 | 5 (1.9) | 15 (6.0) | 32 (13.1) |
| 0.25 | 20 s | 50 | 3 (1.2) | 7 (2.8) | 16 (6.6) |

- **At `f_A = 1/30` a uniform delay costs the honest side time, not rate.** The delay widens each
  layer, but the time to settle against 25 % stays at 12–13 minutes for `Δ` from 1 to 20 s.
- **The window must exceed `Δ` by several block intervals.** At `f_A = 0.25` a 30-slot window
  leaves a producer 10 slots of blocks it has seen at `Δ = 20` s, about two honest block
  intervals. The time against 25 % then rises from 1.5 minutes at 1 s to 6.0. A window of
  `Δ + 30` slots brings it to 2.8. The paper's condition `w ≥ Δ` is not enough.
- **A depth in layers holds only at the delay it was set for.** A wider DAG needs fewer layers. At
  `f_A = 1/30` against 25 %, 13 layers hold `1e-3` at `Δ = 20` s and leave `4.7e-3` at 1 s
  (`runs/e5/race.csv`). A depth in layers must be set at the shortest delay.

**The balancing attack.** An adversary that schedules each delay can do far more. Weighing every
honest block of a subDAG is what GHOST does with a subtree, and Gaži, Motaqy and Russell give tight
attacks on GHOST (ePrint 2024/1830, §5). The adversary keeps two conflicting subDAGs at equal
weight: it holds each honest block back until the next one appears, so that the honest blocks of a
phase land alternately on the two sides, and it spends a withheld block of its own when a phase
ends one apart. While the balance holds no block settles, and the adversary chooses which side
wins. A phase closes after `Δ` slots without an honest block. The balance holds forever with
positive probability once the adversary's expected blocks per phase exceed the chance that a phase
costs it one. `src/finality_sim/balance.py` gives that edge in closed form for the slot lottery
(`scripts/e5_balance.py`). Gates (`tests/test_balance.py`): the phase
statistics match a simulation of the lottery, slots a hundred times finer reach the paper's
continuous-time region, and the balance holds only above the edge. Four mutations fail them.

The largest adversary share that cannot hold the balance, with ties steered by the adversary / ties
broken by a fixed rule, beside the longest-chain rule's region at the same block rate:

| f_A | Δ = 1 s | Δ = 2 s | Δ = 5 s | Δ = 10 s | Δ = 20 s |
| --- | --- | --- | --- | --- | --- |
| 0.0333 | 0.487 / 0.494 / 0.496 | 0.478 / 0.489 / 0.492 | 0.451 / 0.476 / 0.479 | 0.404 / 0.451 / 0.458 | 0.309 / 0.397 / 0.418 |
| 0.05 | 0.480 / 0.490 / 0.494 | 0.467 / 0.483 / 0.487 | 0.425 / 0.462 / 0.468 | 0.353 / 0.423 / 0.437 | 0.220 / 0.331 / 0.379 |
| 0.0667 | 0.473 / 0.487 / 0.491 | 0.455 / 0.477 / 0.483 | 0.398 / 0.448 / 0.457 | 0.301 / 0.392 / 0.416 | 0.150 / 0.260 / 0.344 |
| 0.1 | 0.459 / 0.479 / 0.487 | 0.430 / 0.465 / 0.474 | 0.341 / 0.416 / 0.435 | 0.208 / 0.320 / 0.376 | 0.067 / 0.133 / 0.285 |
| 0.25 | 0.383 / 0.440 / 0.464 | 0.303 / 0.393 / 0.430 | 0.125 / 0.228 / 0.339 | 0.026 / 0.055 / 0.239 | 0.001 / 0.003 / 0.144 |

The share of 1,000 attempts, begun with an empty reserve at evenly spaced phases of one draw of
4.8 days, so that they overlap, that keep the balance for an hour / a day,
with ties steered by the adversary:

| f_A | Δ | α = 0.10 | α = 0.25 |
| --- | --- | --- | --- |
| 0.0333 | 5 s | 0.00 / 0.00 | 0.00 / 0.00 |
| 0.0333 | 10 s | 0.00 / 0.00 | 0.00 / 0.00 |
| 0.25 | 5 s | 0.00 / 0.00 | 0.57 / 0.57 |
| 0.25 | 10 s | 0.74 / 0.74 | 0.92 / 0.92 |

- **At today's block rate the attack needs nearly the chain's share:** 0.40–0.45 at `Δ = 10` s,
  against the chain's region of 0.46. The attack bounds the DAG's safe region from above; no proof
  covers the DAG below it.
- **Where the DAG is fast, the region collapses.** At `f_A = 0.25` and `Δ = 10` s an adversary
  with 3–6 % of the stake keeps the balance; with 10 %, three attempts in four hold it for a day.
  At `Δ = 5` s the edge is 12–23 %.
- **The chain loses less.** At the same block rates the longest-chain rule keeps 0.24 at 10 s and
  0.34 at 5 s, in continuous time. Honest blocks that tie split the DAG's weight, while on the
  chain they only waste it.

**These edges count one move per withheld win.** E3's rule, that a tag found on both sides
weighs on neither, lets a placed win be retracted later by a second copy on the other side, so
one win moves the balance twice. The edges then fall below a third at today's block rate, at
every delay. J.2 gives them on this grid, and leaves the table above as it stands.

## E6 — the cost

- **Emissions.** Every block is a lottery win and so a Blend emission. The cover rate must rise
  with the blocks per slot: ×1 at `f_A = 1/30`, ×3.2 at 0.1, ×8.6 at 0.25 (E2). Votes cost ×34 to
  ×1,786 (`CERTIFIED.md`, D0).
- **References.** A header grows by 32 bytes per reference (E2 gives the counts).
- **Computation.** Referencing the tips of the window needs one pass over its blocks. The maximum
  antichain of Alg. 5 is not needed.

## H7

H7 fails by two of its three tests.

- **The safe region (E5).** Under a delay chosen by an adversary, the balancing attack needs no
  more than GHOST's share, less than the chain's region at every block rate. Counting one move per
  win, at today's block rate it needs 0.40–0.45 of the stake at `Δ = 10` s, against the chain's
  0.46, and at `f_A = 0.25` and `Δ = 10` s 3–6 %. A win can be retracted by a second copy on the
  other side, and then the attack needs 0.235–0.279 at today's rate and 10 s and 0.318–0.326 at
  1 s, below a third at every delay and block rate (J.2).
- **One weight per win (E3).** As specified, one win can add weight on both sides of a conflict.
  The `ρ_LEAD` rule of E3 counts a win once on a side, and no rule every node applies alike stops
  a second copy from moving the balance a second time (J.1).
- **The time (E2).** Passed: under random delay the DAG settles against 25 % in 38 minutes at
  `ε = 1e-9`, against 59 for the chain under the same delay and B2's 6.2 hours at `Δ = 10` s.

The weight must also accumulate since the fork: the paper's prose horizon settles no depth (E2).

## J.0 — the readings

Phase J of `PLAN.md` reads Areon's Theorem 5.6 in three places that its text leaves open. The
owner, a co-author, settles them. Until then the phase takes the reading given under each, and
the alternative is priced from Phase E. Quotes are from arXiv 2511.23025v1 (SHA-1 `6b3b4082`), by
printed page.

**1. The adversary of Theorem 5.6.**

- *The text.* The model lets the adversary schedule: "the adversary schedules deliveries at all
  times subject only to the ∆-delay constraint" (§2.1, p. 3). Three steps of the argument assume
  that honest references gather on one side:
  - the drift (4): "Since honest blocks appear with rate λh and reliably reference the preferred
    frontier, the gap has a positive drift" (§5.3, p. 37);
  - the common past of Areon-Base: "the CCAs of the preferred frontiers Ft across honest parties
    move forward monotonically, and any divergence is confined to the last Θ(∆) layers"
    (Theorem 4.10, proof sketch, p. 33);
  - Tip-Boundedness: "honest weight could still be split across a few tips", and with growth and
    quality "it yields eventual honest majority on one subDAG, assuming honest nodes
    cross-reference tips once visible" (§2.3 and Remark 2.22, p. 15).
- *What E5 shows.* A scheduler that holds each honest block until the next one appears plays the
  honest blocks alternately onto two sides. While the balance holds, the gap does not drift and
  the divergence is not confined to `Θ(Δ)` layers. No step of the argument bounds how long the
  balance lasts.
- *The reading without an answer.* The theorem is read against the scheduler of §2.1, and the
  three steps as unproven against balancing. The phase takes no constant from it. `k` comes from
  J.2's attacks and J.3's bound.
- *The alternative.* If the theorem is meant only against delays nobody schedules, it covers E2's
  private race. Against 25 % at `1e-9` the DAG then settles in 38 minutes at today's block rate on
  the specification's Blend, against 59 for the chain. That is a settlement level under random
  delay. It is not a `k`, which must hold under the worst case. Under the scheduler the region is
  at most E5's edge, counting one move per win: 0.404 of the stake at `f_A = 1/30` and `Δ = 10` s
  with the paper's tie rule, which the scheduler steers (J.1), and 0.451 with ties fixed. With the
  retraction of J.1 it is 0.235 and 0.279 (J.2). Either way no `k` comes from Theorem 5.6.

**2. The weight.**

- *The text.* §2.2.3 sums, since the closest common ancestor `c`, each block's short references:
  `SubdagW(i; c, w)` adds `wref(d; w)` over `Desc*(i) ∩ Desc*(c)`, and `wref` counts `d`'s short
  references (Definition 2.1 and §2.2.3, pp. 6–7). The window caps it: "Only short references to
  slots in [t − w, t − 1] contribute to fork-choice scores" (§2.1, p. 5), and the fork choice of
  §5 "counts only short references from the last w slots" (p. 36). The gap of Definition 5.3 counts each
  block once, `wref(d; w) ∈ {0, 1}`, "within the current window of width w" (p. 37).
- *The reading without an answer.* E1's: the weight accumulated since the closest common
  ancestor, one per lottery win (E3, J.1). `Desc*(i)` of a tip is the tip alone, so the sum is
  read over the tip's ancestors since `c`, as the paper's design summary describes it: "blocks that
  are descendants of c and ancestors of the tip" (p. 9).
- *The alternative.* Over the last `w` slots no depth settles. Against 25 % the coalition displaces
  93–99 % of the targets at depth 40, at every block rate and Blend setting E2 measured, and
  against a third 98–100 % (E2): a coalition that keeps its private subDAG alive outweighs the
  honest side in some window. Counting references instead of blocks lets a coalition build its
  subDAG wide, `m²` references from `2m` blocks (E1).

**3. The unit of `k`.**

- *The text.* "B is k-final at time t if B lies at distance at least k beneath Ft when distances
  are measured along short-reference edges" (Definition 5.1, p. 36): `k` counts layers. Corollary
  5.9 maps it to time as "Tfinal(ε) = k · τslot" (p. 39): `k` counts slots.
- *The reading without an answer.* Slots. `B_imm` is the latest block of the preferred ancestry
  made at least `k` slots ago (J.4).
- *The alternative.* The DAG widens with the delay, so a depth in layers holds only at the delay
  it was set for. Against 25 % at `f_A = 1/30`, 13 layers hold `1e-3` at `Δ = 20` s and leave
  `4.7e-3` at 1 s (E5). A `k` in layers must be set at the shortest delay the network shows, and
  its time then moves with the delay. A `k` in slots is a time, which is what the consumers of `k`
  read (`PLAN.md` §6.3).

## J.1 — one weight per win and the tie rule

Both variants of Phase J weigh each side of a fork by the lottery wins it holds since the closest
common ancestor. Three rules set that weight: what names a win, what the nonce's contribution is
bound to, and how equal weights are broken. A fourth question, what a second copy of a win does,
limits all three (below).

**The win tag.** The proof of leadership outputs `ρ_LEAD`: "Compute and output the entropy
contribution ρLEAD := hash(NONCE_CONTRIB_V1 || sl||noteID||sk)"
(`cryptarchia-proof-of-leadership.md` at `logos-lips` `47a73cdc`, Circuit Constraints, item 7).
It depends on the slot, the note and its key, and not on the parent, so every block one win signs
carries the same value. The phase uses it as the win tag:

- the weight of a side counts each tag once;
- a tag found on both sides of a comparison weighs on neither (E3);
- the tie rule below reads it;
- two blocks with one tag are the evidence of an equivocation.

**The nonce's contribution.** H.2 binds the contribution to the parent's contribution, so that a
value exists only once every block before it on its branch does:

`c(b) = hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ ρ_LEAD(b))`.

Bound to the parent's block identifier, a contribution would let a coalition draw one from every
variant of its own blocks, since the identifier hashes the body and the proof. Bound to the
parent's win tag, a win on the coalition's own previous win would have a value known ahead (H.2).
Both inputs of `c` are public, so every node derives it, and the proof of leadership keeps today's
output. The contribution enters only the nonce. The tag enters the weight, the ties, equivocation
and the block's own contribution.

The proof of leadership of `logos-blockchain-circuits` v0.5.6 (`07c43935`, the revision the node
at `4e0405d51` pins), compiled with the build's flags, and the variants that prove one more hash
(`scripts/j1_circuit.py`, `runs/j1/circuit.csv`). Today's constraints, wires and public values are
those of the released proving key (`tests/test_j1_circuit.py`).

| proof of leadership | constraints | added | share of today's | public values | domain |
| --- | --- | --- | --- | --- | --- |
| today | 20,460 | 0 | 0.0 % | 9 | 2^15 |
| the contribution derived by every node | 20,460 | 0 | 0.0 % | 9 | 2^15 |
| the tag bound to the epoch nonce | 20,700 | 240 | 1.2 % | 9 | 2^15 |
| the contribution proved from the tag | 21,180 | 720 | 3.5 % | 11 | 2^15 |
| the contribution proved from the secrets | 21,660 | 1,200 | 5.9 % | 11 | 2^15 |

- **Deriving the contribution costs the proof nothing.** A node hashes three field elements a
  block.
- **Proving it costs 3.5–5.9 % of the circuit and two public values.** A Poseidon2 permutation
  costs 240 constraints: 80 S-boxes of three multiplications. A hash absorbs its domain tag, its
  values and one padding element, a permutation each. The first sees only constants and is folded
  away, so `n` values cost `n + 1` permutations. The proving key's domain stays `2^15` in every
  variant.
- **Binding the tag to the epoch nonce costs 240 constraints, 1.2 %.** It would stop a coalition
  from computing its tags before the nonce is known. The tie rule, the tag's only use where its
  value matters, gains little from that: which slots a note wins depends on the nonce, so a key
  ground in advance cannot place its small tags in the slots it will win. The phase leaves the tag
  as it is.

**Equal weights.** When two sides weigh the same, the side whose first block carries the smaller
win tag is preferred. If both first blocks carry one tag, the smaller block identifier decides. In
(a) a side's first block is the child of the closest common ancestor that roots the side. In (b)
it is the block whose payload starts the conflict on that side.

- *Every node holding the two sides decides alike.* A node attaches a block only after its
  ancestors, so any node that holds a block of a side holds the side's first block. This is the
  deterministic tie-breaking of Gaži, Motaqy and Russell, decided by "an injective “preference
  function” p : V → R" on blocks (ePrint 2024/1830, revision 2025-02-20, Definition 18, p. 18).
  Its region at `f_A = 1/30` and `Δ = 10` s is 0.451 of the stake with one move per win (E5), and
  0.279 with retraction (J.2).
- *The paper's rule reads the tips.* Definition 2.5 breaks a tie by "the tip with larger y(·)"
  (p. 8). Two nodes can hold the same two sides with different tips, since one holds a block the
  other has not yet received. A scheduler decides which tips each node holds, and so how each node
  breaks the tie. That is the same paper's adversarial tie-breaking, 0.404 at the same point with
  one move per win (E5), and 0.235 with retraction (J.2).
- *The paper's `(slot, y)` order,* which it uses to choose the closest common ancestor (Definition
  2.3, p. 7) and the canonical tip of its analysis (§5.3, p. 37), would also decide alike in every
  node if applied to first blocks. But it hands every tie to a withheld block of an earlier slot. A
  coalition that holds a win and releases it when an honest block of a later slot appears in the
  same place displaces that block every time. The tag gives a withheld block the tie only when its
  tag is smaller, once in two against one honest block. A displaced honest block is lost to
  chain quality, and if it held a sub-window's smallest contribution, to the nonce (B7).
- *What the coalition still chooses* is which of its wins starts its side. Starting with a later
  win forgoes the earlier ones, since a block's slot must exceed those it references. J.2 measures
  what the choice buys.

**A repeated tag, and retraction.** Both blocks stay valid and can be referenced, so no rule about
which copy came first splits the honest nodes. The weight rule sets what they carry: one weight on
a side, and none where they sit on both sides of a comparison. That rule lets a win act twice. A
coalition places a copy of a withheld win on one side to answer an honest block. Later it
publishes a second copy of the same win on the other side, and the tag then weighs on neither,
which takes the first copy's weight back. E5's and J.2's balance spend a win on one phase; with
retraction it answers two.

- *A play on explicit blocks shows it* (`tests/test_convergence.py`). With no delay and a fixed
  rule, a coalition keeps a fork within one block for `2n` honest blocks with `n + 1` wins. It
  answers with fresh wins on the trailing side for a stretch. Then, leading the other side by one,
  it retracts them one by one.
- *Every rule tried allows it:*
  - a tag on both sides weighs on both: one win weighs on both sides at once, and GHOST "provides
    no security (for any parameters) with unconstrained equivocation" (Gaži, Motaqy and Russell,
    p. 5);
  - it weighs on neither, J.1's rule: the second copy retracts the first, one move each;
  - it weighs on the side of the copy with the smaller identifier, the earlier parent or any other
    value of the copies: the coalition sets that value when it makes the second copy, choosing its
    body and its parent, so the second copy moves the weight across, two moves at once;
  - it weighs on the side of the copy a node received first: the adversary orders deliveries, so
    the nodes disagree about the tag for good;
  - the note that signed both copies is punished: the tag is anonymous, and linking the copies to
    their note needs a value that links every block of that note, which the proof of leadership
    keeps private.
- *Why no rule every node applies alike blocks it.* Such a rule can read only the two copies, since
  what each node received, and when, differs from node to node. The coalition makes both copies and
  publishes the second whenever it likes. So whatever the rule assigns, the coalition chooses it,
  and the second copy is a move it did not pay for with a new win.
- *What it costs.* The balance holds once `2·E[#a]` per phase exceeds the chance that a phase costs
  a move. Against a third it then holds for ever with a positive chance at every delay from 1 s,
  with either tie rule. With no delay the edge falls from a half to a third (J.3).

## J.2 — every attack within `Δ`

J.2 asks how deep a block must be before every attack within `Δ` has failed at `1e-9`, on a fork
choice that weighs every honest block, at today's block rate `f = 1/30`. It takes J.0's readings:
the adversary schedules every delivery within `Δ`, the weight counts each win once since the
closest common ancestor, and `k` counts slots. It takes J.1's win tag and tie rule. Each attack is
measured twice: with one move per withheld win, and with the second move that E3's rule allows
when a placed win is retracted.

**One model serves both variants.** Each weighs a side by its wins since the closest common
ancestor, one weight per win, and an honest block joins only the side its producer prefers: (a)
extends it, (b) references its frontier (E4). Each honest block then adds one to the side its
producer prefers, and each coalition win one to the side it is placed on. The attacks act on that
weight alone, so they are the same on both variants (`src/finality_sim/delayfc.py`,
`scripts/j2_attacks.py`, `runs/j2/`). The DAG's window of `w` slots changes two rare cases:

- a phase that opens after a quiet stretch longer than `w − Δ` starts with a block that
  references nothing inside the window and weighs nothing, which spares the adversary part of that
  phase's cost;
- a coalition win placed more than `w` slots after the previous block of its private side weighs
  nothing, which slows the private race.

Their shares at E2's window, `w = 225` slots:

| α | Δ | phases opening after a quiet stretch | private wins after a gap |
| --- | --- | --- | --- |
| 30 % | 1 s | 0.49 % | 10.1 % |
| 30 % | 10 s | 0.61 % | 10.1 % |
| 30 % | 20 s | 0.77 % | 10.1 % |
| a third | 1 s | 0.63 % | 7.9 % |
| a third | 10 s | 0.78 % | 7.9 % |
| a third | 20 s | 0.97 % | 7.9 % |

**The lottery and the delay.** A slot holds Poisson numbers of honest blocks and of coalition
wins (`finality_sim.balance`). A block of slot `t` is in every honest view from slot `t + Δ + 1`;
before that the adversary chooses which producers see it. A phase is a run of honest blocks each
at most `Δ` slots after the previous one. It closes `Δ` slots after its last block, when every view
holds it.

**The attacks.**

- **The balance (J.2.1).** Two conflicting sides, balanced. Each producer of a phase is shown
  every block of the phase but the latest, so the phase's honest blocks alternate between the
  sides. With ties the adversary steers, pairs cancel, and a phase with an odd number of blocks
  costs one withheld win, placed on the lighter side when the phase closes. With a fixed rule a
  producer at a tie extends the side the rule favours. The second block of a phase then reaches
  the other side only if its producer is first shown a withheld win there. That is one win for
  every phase that holds an honest block, due when its second block is made, or when it closes if
  it holds one. These are Gaži, Motaqy and Russell's two attacks (J.3). The balance ends when a
  win falls due and the coalition has none.
- **The combined attack (J.2.2).** The balance and a private branch draw on the same wins. While
  the sides are balanced, the coalition's withheld wins are its reserve. When a win falls due and
  it has none, that phase's honest blocks all go to the target's side, and the coalition races as
  in E2 until its withheld wins cover the lead; then it balances again. Before the target it
  balances every conflict it can and starts afresh after each failure, so it may meet the target
  with a reserve. The target opens a phase, and a client accepts it once it is `k` slots old. The
  attack succeeds if, at some slot from then on, the sides are balanced and the reserve covers the
  open phase's cost, with a win to spare under J.1's rule and without one when the adversary
  steers ties. While the sides are balanced the adversary can make any view prefer either side,
  so it can move that client off the target. Success at any later slot is the release at the best
  moment for every depth at once.
- **The tie rule's exploit (J.2.3).** Under J.1's rule the coalition chooses which of its wins
  starts its side. If the rule always favoured that side, a balance with no win to spare would
  already succeed. The difference bounds what the choice buys.
- **The private race** of E2 and E5, never balanced: the honest blocks of the first `Δ` slots after
  the target do not see it, and count for neither side.
- **The chain beside them (J.2.4):** B2's lower bound, which is an attack, and its upper bound, at
  the chain's worst-case clock of `Δ + 1/p_h` seconds a block (`SETTLEMENT.md`, B2).

**Two counts of moves.** A move shifts the difference of the sides by one. Placing a withheld win
is one. E3's rule, that a tag found on both sides of a comparison weighs on neither, gives a second:
a later copy of a placed win on the other side takes the first copy's weight away. So one win can
move the balance twice, once each way.

- *Ties steered.* The adversary steers each phase's first block onto a side that holds a
  placement, so an odd phase can always be paid by retracting it. Every win is worth two moves in
  either direction, exactly.
- *A fixed rule.* The balanced states are the tie, which the rule settles for one side, and the
  other side one ahead. Every move a state needs points the same way, toward the side that is not
  preferred, so a placement made in one state can be retracted only in the other. A phase with an
  even number of blocks passes from one state to the other; otherwise the adversary passes at the
  cost of one more move. Two counts bracket the attack. The *relaxed* count lets every win make two
  moves in any direction: no attack does better. The *best switches* keep the direction, spend
  placements before wins, and choose each pass between the states by backward induction over the
  attack's states: an attack, given without a premined reserve.

The chance of success at each depth is computed exactly, as a distribution over the attack's
states, slot by slot. No depth is extrapolated.

**Gates** (`tests/test_j2_attacks.py`; sixteen mutations in `scripts/check_mutations.py` each
fail one):

- *The construction.* A play with explicit blocks and views: each producer sees what the delay
  forces and what the adversary chooses, and prefers the heavier side. At `f_A = 0.25`, `Δ` of 0,
  1 and 5 slots and 10 % and 30 % of the stake, every block the construction aims is feasible from
  some view, and the attack's reserve after every phase, and every failure, equal the play's.
- *Retraction on tagged blocks.* The same play on blocks that carry win tags, a side weighing its
  honest blocks and the tags found on it alone, the adversary choosing tag by tag which copies a
  producer sees. At the same points, with 4 % and 30 % of the stake, the schedule of placements,
  retractions and passes between states reproduces the count of moves after every close and
  every failure, and every aimed block is feasible.
- *The edges.* Two moves a win against a move a phase give the same edges as
  `convergence.retraction_threshold`, written for J.1, to `1e-12`, and below each edge the
  walks' balance falls toward zero, above it toward a positive limit.
- *The best switches* lie between the rule `max(1, s // 2)` and the relaxed count at every depth.
- *After a race*, the wins left when the coalition catches up are two moves each with ties steered,
  as a hand-counted case shows.
- *Exact against sampled.* Sixteen independent runs of 1.5 million slots, for the balance, the
  combined attack and the private race, with one move a win and with each count of retraction,
  lie within 4.5 standard errors of the exact chance at depths up to 1,800 slots.
- *The private race is E2's and B3's.* Without delay, scored per block and per layer, it equals
  `areon.dag_race` count for count, the target's siblings counting for neither side, and on a
  chain `race.race`.
- *The edge.* Below E5's edge the balance's chance of standing falls toward zero; above it, toward
  a positive limit.
- *Depth.* Every chance of success falls with depth.

**One move per win: the balance's tail.** The chance that a balance begun with nothing withheld,
when the target's phase opens, still stands 1, 6 and 24 hours later, and the hours until that
chance is `1e-9`:

| α | Δ | ties steered: 1 h / 6 h / 24 h | ties steered: hours to 1e-9 | a fixed rule: 1 h / 6 h / 24 h | a fixed rule: hours to 1e-9 |
| --- | --- | --- | --- | --- | --- |
| 25 % | 1 s | 1.7e-10 / < 1e-30 / < 1e-30 | 0.9 | 1.3e-11 / < 1e-30 / < 1e-30 | 0.7 |
| 25 % | 2 s | 1.2e-09 / < 1e-30 / < 1e-30 | 1.0 | 3.5e-11 / < 1e-30 / < 1e-30 | 0.8 |
| 25 % | 5 s | 1.2e-07 / 1.2e-28 / < 1e-30 | 1.5 | 4.5e-10 / < 1e-30 / < 1e-30 | 0.9 |
| 25 % | 10 s | 3.0e-05 / 1.0e-16 / < 1e-30 | 2.9 | 1.8e-08 / < 1e-30 / < 1e-30 | 1.2 |
| 25 % | 20 s | 1.2e-02 / 8.0e-05 / 2.7e-10 | 22.0 | 1.0e-05 / 7.5e-18 / < 1e-30 | 2.6 |
| 30 % | 1 s | 6.3e-08 / 1.4e-27 / < 1e-30 | 1.4 | 8.1e-09 / 1.4e-30 / < 1e-30 | 1.2 |
| 30 % | 2 s | 3.0e-07 / 1.0e-24 / < 1e-30 | 1.7 | 2.0e-08 / 3.5e-29 / < 1e-30 | 1.3 |
| 30 % | 5 s | 1.1e-05 / 1.3e-17 / < 1e-30 | 2.6 | 1.8e-07 / 2.6e-25 / < 1e-30 | 1.6 |
| 30 % | 10 s | 6.9e-04 / 1.9e-09 / 1.2e-26 | 6.3 | 3.5e-06 / 2.4e-19 / < 1e-30 | 2.3 |
| 30 % | 20 s | 4.7e-02 / 1.4e-02 / 3.5e-03 | > 72 | 4.1e-04 / 1.2e-09 / 1.0e-26 | 6.1 |
| a third | 1 s | 1.4e-06 / 5.3e-20 / < 1e-30 | 2.1 | 2.5e-07 / 2.4e-22 / < 1e-30 | 1.7 |
| a third | 2 s | 5.6e-06 / 1.0e-17 / < 1e-30 | 2.5 | 5.8e-07 / 3.6e-21 / < 1e-30 | 1.9 |
| a third | 5 s | 1.2e-04 / 3.5e-12 / < 1e-30 | 4.3 | 4.0e-06 / 5.7e-18 / < 1e-30 | 2.4 |
| a third | 10 s | 3.3e-03 / 3.4e-06 / 1.9e-14 | 13.4 | 5.2e-05 / 3.1e-13 / < 1e-30 | 3.8 |
| a third | 20 s | held for ever with positive chance | none | 2.4e-03 / 3.9e-06 / 1.1e-13 | 14.2 |

- **Inside the edge, a balance still lasts hours.** E5's edges lie above a third at `Δ = 10` s,
  but against a third the balance's chance of standing falls to `1e-9` only after 3.8 hours with
  a fixed rule and 13.4 with ties steered.
- **At 20 s a third is outside the edge with ties steered.** The balance then holds for ever with
  a positive chance. Against 30 % it outlasts 72 hours.

**One move per win: the depth at `1e-9`.** The hours each attack needs, beside the chain's attack
and the chain's bound. "Fixed rule" is the combined attack under J.1's rule, "tie exploit" the same
with every tie
going to the coalition's side, "ties steered" the combined attack with the adversary breaking
ties, and "balance alone" the balance begun with nothing withheld:

| α | Δ | fixed rule | tie exploit | ties steered | balance alone, fixed rule | private race | chain: attack | chain: bound |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 25 % | 1 s | 1.1 | 1.2 | 1.3 | 0.7 | 1.1 | 1.3 | 3.3 |
| 25 % | 2 s | 1.2 | 1.2 | 1.4 | 0.8 | 1.1 | 1.3 | 3.5 |
| 25 % | 5 s | 1.3 | 1.3 | 1.8 | 0.9 | 1.1 | 1.5 | 4.4 |
| 25 % | 10 s | 1.6 | 1.6 | 3.4 | 1.2 | 1.1 | 2.0 | 6.6 |
| 25 % | 20 s | 3.1 | 3.2 | 26.9 | 2.6 | 1.1 | 3.3 | 16.1 |
| 30 % | 1 s | 1.9 | 1.9 | 2.1 | 1.2 | 1.8 | 2.2 | 6.0 |
| 30 % | 2 s | 1.9 | 2.0 | 2.3 | 1.3 | 1.8 | 2.4 | 6.5 |
| 30 % | 5 s | 2.2 | 2.2 | 3.3 | 1.6 | 1.8 | 2.9 | 8.4 |
| 30 % | 10 s | 2.9 | 3.0 | 7.8 | 2.3 | 1.8 | 3.9 | 13.0 |
| 30 % | 20 s | 7.7 | 7.7 | > 72 | 6.1 | 1.8 | 7.7 | 36.6 |
| a third | 1 s | 2.8 | 2.8 | 3.1 | 1.7 | 2.7 | 3.5 | 9.6 |
| a third | 2 s | 2.9 | 2.9 | 3.5 | 1.9 | 2.7 | 3.8 | 10.5 |
| a third | 5 s | 3.4 | 3.4 | 5.6 | 2.4 | 2.7 | 4.7 | 13.9 |
| a third | 10 s | 5.0 | 5.0 | 17.1 | 3.8 | 2.7 | 6.8 | 23.0 |
| a third | 20 s | 18.6 | 18.6 | none | 14.2 | 2.7 | 16.0 | 77.0 |

The same depth under J.1's rule in slots, in hours, and in the honest blocks made in that time,
beside the chain's B2 depths in canonical blocks (`*`: extrapolated, as in B2):

| α | Δ | slots | hours | honest blocks | chain's attack: blocks / hours | chain's bound: blocks / hours |
| --- | --- | --- | --- | --- | --- | --- |
| 30 % | 1 s | 6,741 | 1.87 | 160 | 185* / 2.25 | 495 / 6.00 |
| 30 % | 10 s | 10,602 | 2.94 | 252 | 266* / 3.90 | 892 / 13.04 |
| a third | 1 s | 10,027 | 2.79 | 227 | 278* / 3.54 | 758 / 9.63 |
| a third | 10 s | 17,888 | 4.97 | 404 | 445* / 6.78 | 1,510 / 22.96 |

- **Under J.1's rule the weight's attack takes less time than the chain's, up to 10 s.** Against a
  third it needs 2.8 hours at 1 s and 5.0 at 10 s, where the chain's attack needs 3.5 and 6.8. At
  20 s it needs 18.6 hours, the chain's attack 16.0.
- **Delay still costs the weight nearly as much as it costs the chain.** From 1 s to 10 s the
  attack against a third grows from 2.79 to 4.97 hours, 1.78 times; the chain's from 3.54 to 6.78,
  1.92 times.
- **The balance carries the growth.** The private race needs 2.7 hours against a third at every
  delay, as E5 found for the private attack. The combined attack lasts longer at every delay, and
  the balance alone does from 10 s on.
- **Steered ties are far worse.** With the adversary breaking ties, as it does under a first-seen
  rule or under Areon's tie between tips (J.1), the attack against a third needs 17.1 hours at
  10 s, and at 20 s no depth holds.
- **The tie exploit buys at most 0.03–0.04 hours** against a third (H14's table below).

**One move per win: H14.** Against a third under J.1's rule:

| attack, a fixed rule | hours at 1 s | hours at 10 s | 10 s over 1 s | first part, below 1.25 | chain's attack at 10 s (hours) | second part, below it |
| --- | --- | --- | --- | --- | --- | --- |
| combined | 2.79 | 4.97 | 1.78 | fails | 6.78 | holds |
| with the tie exploit | 2.83 | 5.00 | 1.77 | fails | 6.78 | holds |

With one move per win the first part fails: the strongest attack needs 1.78 times as long at
`Δ = 10` s as at 1 s, where the hypothesis allowed 1.25. The second part holds: 5.0 hours at 10 s
against the chain's 6.8.

**Two moves per win: the edges.** The balance lasts for ever with a positive chance once the moves
a phase brings exceed the moves it costs: `2·E[#a] > P(the phase costs a move)`, a move for an odd
phase with ties steered and for any phase with honest blocks under a fixed rule
(`delayfc.edge`). On E5's grid, ties steered / a fixed rule:

| f_A | Δ = 1 s | Δ = 2 s | Δ = 5 s | Δ = 10 s | Δ = 20 s |
| --- | --- | --- | --- | --- | --- |
| 0.0333 | 0.318 / 0.326 | 0.308 / 0.321 | 0.280 / 0.305 | 0.235 / 0.279 | 0.162 / 0.226 |
| 0.05 | 0.311 / 0.322 | 0.296 / 0.314 | 0.254 / 0.290 | 0.193 / 0.250 | 0.109 / 0.173 |
| 0.0667 | 0.303 / 0.318 | 0.284 / 0.307 | 0.229 / 0.275 | 0.157 / 0.221 | 0.072 / 0.127 |
| 0.1 | 0.288 / 0.310 | 0.259 / 0.293 | 0.185 / 0.244 | 0.102 / 0.166 | 0.032 / 0.062 |
| 0.25 | 0.217 / 0.267 | 0.158 / 0.223 | 0.060 / 0.109 | 0.013 / 0.026 | 0.001 / 0.001 |

- **At today's block rate the edges fall by a third or more.** From E5's 0.487 / 0.494 at 1 s to
  0.318 / 0.326, and from 0.404 / 0.451 at 10 s to 0.235 / 0.279.
- **A third lies outside the edge at every delay and block rate, under either rule.** As the delay
  shrinks, almost every phase holds one honest block and costs a move, so the condition tends to
  `2α > 1 − α`: the edge approaches a third from below.
- **30 % lies outside it** from 5 s with ties steered and from 10 s under a fixed rule, and 25 %
  from 10 s and 20 s.

**Two moves per win: the depth at `1e-9`.** The hours each attack needs, "none" where the share
lies outside the edge. Under a fixed rule each cell reads *best switches – relaxed*, an attack and
the most any attack with retraction can reach. The one-move attack and the chain's beside them:

| α | Δ | balance, ties steered | balance, a fixed rule | combined, ties steered | combined, a fixed rule | tie exploit | one move, a fixed rule | chain: attack |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 25 % | 1 s | 8.1 | 4.3 – 6.1 | 11.6 | 5.7 – 9.1 | 5.7 – 9.2 | 1.1 | 1.3 |
| 25 % | 2 s | 11.5 | 5.1 – 7.2 | 16.1 | 6.5 – 10.5 | 6.5 – 10.5 | 1.2 | 1.3 |
| 25 % | 5 s | 46.6 | 8.6 – 12.3 | 64.7 | 10.2 – 17.4 | 10.2 – 17.4 | 1.3 | 1.5 |
| 25 % | 10 s | none | 28.5 – 45.2 | none | 32.2 – 64.0 | 32.2 – 64.0 | 1.6 | 2.0 |
| 25 % | 20 s | none | none | none | none | none | 3.1 | 3.3 |
| 30 % | 1 s | > 72 | 30.3 – 50.4 | > 72 | 40.7 – > 72 | 40.7 – > 72 | 1.9 | 2.2 |
| 30 % | 2 s | > 72 | 44.0 – > 72 | > 72 | 56.5 – > 72 | 56.5 – > 72 | 1.9 | 2.4 |
| 30 % | 5 s | none | > 72 | none | > 72 | > 72 | 2.2 | 2.9 |
| 30 % | 10 s | none | none | none | none | none | 2.9 | 3.9 |
| 30 % | 20 s | none | none | none | none | none | 7.7 | 7.7 |
| a third | 1 s | none | none | none | none | none | 2.8 | 3.5 |
| a third | 2 s | none | none | none | none | none | 2.9 | 3.8 |
| a third | 5 s | none | none | none | none | none | 3.4 | 4.7 |
| a third | 10 s | none | none | none | none | none | 5.0 | 6.8 |
| a third | 20 s | none | none | none | none | none | 18.6 | 16.0 |

- **Against a third no depth holds,** at any delay, under either rule.
- **Inside the edge retraction multiplies the time.** Against 25 % at 1 s the combined attack
  under a fixed rule needs 5.7–9.1 hours where one move needed 1.1, and against 30 % at 1 s 40.7
  or more where it needed 1.9.
- **A fixed rule still beats steered ties,** and keeping the direction matters: under a fixed rule
  the best switches reach a half to seven tenths of the relaxed count's hours.
- **The tie exploit adds at most 0.1 hours** wherever a depth exists.

**Two moves per win: H14, and the plan's stop.** Against a third:

| attack | ties, count | hours at 1 s | hours at 10 s | first part | chain's attack at 10 s (hours) | below it |
| --- | --- | --- | --- | --- | --- | --- |
| combined | a fixed rule, best switches | none | none | fails | 6.78 | no |
| with the tie exploit | a fixed rule, best switches | none | none | fails | 6.78 | no |
| combined | ties steered, two moves | none | none | fails | 6.78 | no |
| combined | a fixed rule, relaxed | none | none | fails | 6.78 | no |
| with the tie exploit | a fixed rule, relaxed | none | none | fails | 6.78 | no |

**H14 fails, and phase J stops here.** With one move per win only its first part fails. With the
second move that E3's rule allows, both fail: against a third no attack has a depth at any delay,
so no variant beats the chain's attack at `Δ = 10` s, 445 blocks or 6.8 hours, which is the plan's
condition for stopping at J.2. A fork choice that weighs every honest block does not turn a
scheduled delay into time. A coalition holding a third places and retracts its wins and keeps two
sides level for ever with a positive chance, at today's block rate and at every faster one.

## J.3 — a bound

**J.3.1 — the literature.** J.3.1 asks whether a published analysis gives a settlement error
against depth, not only a region, for a weight that counts every honest block, under a delay the
adversary schedules within `Δ`, and whether it treats the balancing attack. Two were read, from the
archive's snapshots of the ePrint PDFs:

- Kiffer, Rajaraman and shelat, "A Better Method to Analyze Blockchain Consistency", CCS 2018,
  ePrint 2022/601 (snapshot `20231202114621`, SHA-1 `32193802`, 16 pages);
- Gaži, Motaqy and Russell, "A Tight Analysis of GHOST Consistency", ePrint 2024/1830, revision
  2025-02-20 (snapshot `20260421005417`, SHA-1 `b1e3648d`, 32 pages). The study's other citations
  are to revision 2026-09-11, read from a download no longer reachable, whose regions, attacks
  and equivocation remark were found unchanged (`RATE.md` C3).

Neither gives an error against depth:

- Kiffer, Rajaraman and shelat prove GHOST consistent where their technique proves Nakamoto
  consensus consistent: "GHOST satisfies consistency under the same bounds of theorem 4.4"
  (Corollary 6.4, p. 14). Theorem 4.4 asks that convergence opportunities outnumber the
  adversary's blocks by a factor `1 + δ` (p. 8). Its concentration holds with probability
  `1 − e^{−Ω(T)}`, "where the hidden constant depends on ∆ and p, factors that determine the
  mixing time of the transformed Markov chain" (p. 7). The constant is not given, so no depth
  follows for an `ε`.
- Gaži, Motaqy and Russell give the exact regions. GHOST is consistent "precisely when
  ρa < ρh · e^{−ρh∆}/(2 − e^{−ρh∆})" with ties steered by the adversary, and "exactly when
  ρa < ρh · e^{−ρh∆}" with ties fixed (equations (1) and (2), p. 2). Theorems 1 and 2 give
  "eventual settlement" with probability 1 (pp. 17 and 19). The proof shows that an advantage
  grows linearly in the phases and closes with the Borel–Cantelli lemma, so it fixes no depth for
  an `ε` either.
- Both use the study's worst case. Kiffer, Rajaraman and shelat's adversary "is able to delay and
  reorder all messages players receive up to a delay of ∆ rounds" (p. 3), and Gaži, Motaqy and
  Russell's "may selectively delay honest block delivery by up to ∆ time" (p. 2). Both analyse
  proof of work, in which a success makes one block for good. Gaži, Motaqy and Russell's proof
  "establishes security even in the face of an adversary with a full view (including the future) of
  the schedule" (p. 5), which covers a lottery's lookahead. They note that GHOST "provides no
  security (for any parameters) with unconstrained equivocation" (p. 5). A lottery win can sign a
  second block, and J.1's retraction is the part of equivocation that one weight per win leaves.
- Neither analyses a DAG weight. Kiffer, Rajaraman and shelat say only that DAG protocols
  "inherit security from GHOST or any other tree-based selection policy underlying it" (p. 8).

Both treat the balancing attack:

- Kiffer, Rajaraman and shelat's balance attack (§6.4, Algorithm 1, p. 14) splits the honest
  blocks evenly between two subtrees and spends withheld blocks to rebalance them. A Markov chain
  gives the chance that the fork lasts `k` blocks, plotted for 49 % and 25 % adversaries (Figure
  11, p. 15). That chance is an attack's, a lower bound on the error. The bound under the attack is
  left open: "obtaining asymptotic bounds under the attack is still open" (p. 15). Gaži, Motaqy and
  Russell read this attack as "a setting in which ties are broken randomly" (p. 5).
- Gaži, Motaqy and Russell's two attacks (§5, pp. 20–23) are the ones E5 ports. With ties steered
  the reserve moves by `#a(Φ) − ⊕(#h Φ)` a phase (p. 21). With ties fixed "each (non-empty) phase
  calls for exposure of exactly one adversarial block" (p. 22). Gambler's ruin shows that each
  attack eventually succeeds outside its region. Neither paper says how long a balance lasts
  inside it, which is J.2's measurement.

Neither holds a bound to port as B1 ported Gaži, Ren and Russell's, so J.3.2 derives one. The
regions each technique can certify, with one move per win as in proof of work, at today's block
rate `f_A = 1/30`, and the same with J.1's retraction, two moves per win: the opportunities' region
with two events a win, and the balance's edge when each phase that costs a move needs half a win
(`scripts/j3_regions.py`, `runs/j3/regions.csv`; GHOST's two edges and the chain's are E5's):

| Δ | convergence opportunities | GHOST, ties steered | GHOST, ties fixed | longest chain |
| --- | --- | --- | --- | --- |
| 1 s | 0.487 | 0.487 | 0.494 | 0.496 |
| 2 s | 0.478 | 0.478 | 0.489 | 0.492 |
| 5 s | 0.449 | 0.451 | 0.476 | 0.479 |
| 10 s | 0.394 | 0.404 | 0.451 | 0.458 |
| 20 s | 0.265 | 0.309 | 0.397 | 0.418 |

| Δ | convergence opportunities, two events a win | balance, ties steered | balance, a fixed rule |
| --- | --- | --- | --- |
| 1 s | 0.318 | 0.318 | 0.326 |
| 2 s | 0.308 | 0.308 | 0.321 |
| 5 s | 0.276 | 0.280 | 0.305 |
| 10 s | 0.223 | 0.235 | 0.279 |
| 20 s | 0.130 | 0.162 | 0.226 |

- **With retraction a third holds the balance for ever at every delay.** Both edges lie below a
  third from 1 s on, so against a third the balance stands for ever with a positive chance, with
  either tie rule (J.1). No analysis can bound the error where an attack never fails.
- **The edges tend to a third as the delay and the slot vanish,** where one move per win gives a
  half (`tests/test_convergence.py`). Against 30 % the balance fails for sure only up to 5 s with a
  fixed rule and 2 s with ties steered; against 25 %, up to 10 s and 5 s.

**J.3.2 — the convergence-opportunity bound.** The terms:

- *Delivery.* An honest block made in slot `u` is held by every honest node at the end of slot
  `u + Δ`. An honest node relays every block it holds, so a block one honest node holds at the end
  of slot `u`, every honest node holds at the end of slot `u + Δ`. The adversary orders every
  delivery within that, and any tie rule applies.
- *Phases.* A phase starts with an honest block made after `Δ` slots without one, at slot `s_j`,
  and ends `Δ` slots after its last honest block. At the end of slot `s_j − 1` every honest node
  holds every honest block made so far. A **convergence opportunity** is a phase with exactly one
  honest block.
- *The margin.* Fix a block `c` and its child `x` on the target's side. For a view `V` and a child
  `z` of `c`, `W_V(z)` counts the win tags under `z` found under no other child of `c` (J.1). The
  margin is `M_V = W_V(x) − max_{y ≠ x} W_V(y)`. `M_j` is the margin over the blocks every honest
  node holds at the end of slot `s_j − 1`.
- *Events.* A win's part in the margin changes when a copy of it reaches every honest node: its
  first copy under a child of `c` adds it to that child, and a copy under a second child takes it
  away from both. A win causes at most two events, and one under a rule that never let a copy
  retract another. `e_j` counts the events of copies first held by an honest node in slots
  `s_j − Δ` to `s_{j+1} − Δ − 1`.

**Lemma.** `|M_{j+1}| ≥ |M_j| + o_j − e_j`, where `o_j` is one if phase `j` is a convergence
opportunity whose block lies under `c`, and zero otherwise.

*Proof.*

1. A producer of phase `j` holds what every node held at `s_j − 1`, some of the phase's earlier
   blocks, and some copies first held by an honest node from `s_j − Δ` on. Each win of the last
   kind moves one child's weight in the producer's view by one against the common view. Each such
   copy reaches every node by `s_{j+1} − 1`, so each such win has an event in the window. The
   producer's view therefore differs from `M_j` by the phase blocks it holds, plus at most `e_j`.
2. If `M_j > e_j`, every producer of the phase sees `x` strictly ahead, by induction over the
   phase's blocks, since a block under `x` only raises the margin. Every block of the phase whose
   producer's chain reaches `c` then lies under `x`, and `M_{j+1} ≥ M_j + o_j − e_j`. If
   `M_j < −e_j`, every producer sees another child ahead. No block lies under `x`, and a lone
   block under `c` raises the heaviest other child by one unless an event in the window moved the
   producer's view, which the same window counts. So `M_{j+1} ≤ M_j − o_j + e_j`.
3. If `|M_j| ≤ e_j`, the claim asks only `|M_{j+1}| ≥ o_j − (e_j − |M_j|)`, which holds unless
   `e_j = |M_j|` and the phase is an opportunity. Its one block then lands on the side its producer
   prefers. If that side agrees with the sign of `M_j`, or `M_j` is zero, `|M|` grows by one. If
   it does not,
   the producer saw at least `|M_j|` wins move its view against `M_j`. Each of those moves the
   common margin the same way once its copy reaches every node, or spends a second event of its
   own. So the margin crosses zero and `|M_{j+1}| ≥ 1`.

*From the lemma to a client.* Sum the lemma from the first phase after `c`. A client accepts the
target at the end of slot `t` and some honest view prefers another child of `c` at a slot after
`t`. Then the margin passes within the events of its window of zero at some phase `i` from `t`
on. Step 2 shows that a margin beyond its window's events keeps its sign through the phase. Every
event is caused by a win made after `c`, at most `e` events each. So for some slot `u ≥ t`,

`C(s_c, u − Δ] ≤ e·A(s_c, u] + 1`,

with `C` the opportunities by their slot and `A` the coalition's wins. The `+ 1` is phase `i`'s own
opportunity, counted before its `Δ` quiet slots close.

*The computation* (`src/finality_sim/cobound.py`, `scripts/j3_bound.py`, `runs/j3/bound.csv`):

- The walk adds `e` for each win and takes one for each opportunity, `Δ` slots after its slot,
  when it is confirmed. At most one opportunity falls in any `Δ` slots, so the condition holds
  only if the walk from some fork point `v < s_B` to some `u ≥ s_B + T` reaches `−2`.
- The chain's state is the walk, the quiet slots since the last honest block, and whether that
  block was a lone block awaiting `Δ` quiet slots. Before the target, the walk reflected at zero is
  the lead over every fork point at once, as B6's walk is, in its stationary law.
- The target's slot holds at least one honest block. After it the walk runs free, and the error at
  `T` is the chance that it stands at `−2` or above at `s_B + T` or ever later. Both laws are
  solved as linear systems, and the walk is followed slot by slot.

**Scope.** The computation counts every opportunity after `c` as one under `c`. That holds while
every honest node's chain runs through `c`, as in every attack of J.2 and of Gaži, Motaqy and
Russell. A coalition that also contests a block above `c` sends an opportunity elsewhere only by
making a sibling of that block at least as heavy, in the producer's view, as everything the
producer holds under `c`. The bound does not cover such nested contests.

**Gates** (`tests/test_convergence.py`, `tests/test_cobound.py`; ten mutations in
`scripts/check_mutations.py` each fail one):

- *The opportunities' rate.* A count on a drawn lottery lies within four standard errors of
  `λ_h e^{−(2Δ+1)λ_h}`. In slots a hundred times finer the region reaches the one Gaži, Motaqy and
  Russell state for the technique, `ρ_a < ρ_h e^{−2ρ_hΔ}` (p. 2), and it lies below their tight
  region with ties steered at every point of E5.
- *Retraction.* The play on explicit blocks of J.1. The edges with two moves a win tend to a third
  in fine slots and lie below the edges with one move a win at every delay.
- *Above every attack.* Every exact attack of J.2 lies below the bound at every depth. With one
  move per win the bound has one event per win, at 30 % and `Δ` of 1 and 5 s: the combined attack
  and the balance with ties steered and with a fixed rule, and the private race. With retraction,
  two moves per win, it has two, at 20 % and 1 s: the combined attack and the balance with ties
  steered, and under the fixed rule with J.2's strongest switches between its balanced states.
- *A slot-level count.* Thirty-two independent draws of 1.5 million slots each lie within four
  standard errors of the chain, with one event per win and with two.
- *No delay.* At `Δ = 0`, in slots fifty times finer, the bound equals the continuous race in
  closed form within 1 %. The walk climbs at the coalition's rate and falls at the honest rate.
  Its premined lead is geometric with ratio `λ_a/λ_h`, and it makes good a deficit `d` with chance
  `(λ_a/λ_h)^d`.

The depth at `1e-9` in slots and hours, with two events a win under J.1's rule, and with one, which
no rule that every node applies alike achieves (J.1):

| α | Δ | two events a win (J.1): slots / hours | one event a win: slots / hours |
| --- | --- | --- | --- |
| 25 % | 1 s | 51,221 / 14.2 | 5,037 / 1.4 |
| 25 % | 2 s | 72,763 / 20.2 | 5,625 / 1.6 |
| 25 % | 5 s | beyond 72 h | 8,205 / 2.3 |
| 25 % | 10 s | none: the walk drifts up | 18,902 / 5.3 |
| 25 % | 20 s | none: the walk drifts up | beyond 72 h |
| 30 % | 1 s | beyond 72 h | 8,288 / 2.3 |
| 30 % | 2 s | beyond 72 h | 9,465 / 2.6 |
| 30 % | 5 s | none: the walk drifts up | 15,057 / 4.2 |
| 30 % | 10 s | none: the walk drifts up | 45,931 / 12.8 |
| 30 % | 20 s | none: the walk drifts up | none: the walk drifts up |
| a third | 1 s | none: the walk drifts up | 12,423 / 3.5 |
| a third | 2 s | none: the walk drifts up | 14,515 / 4.0 |
| a third | 5 s | none: the walk drifts up | 25,361 / 7.0 |
| a third | 10 s | none: the walk drifts up | 112,479 / 31.2 |
| a third | 20 s | none: the walk drifts up | none: the walk drifts up |

- **Against a third there is no finite bound.** The balance itself holds for ever with a positive
  chance at every delay.
- **At 10 s the bound is finite up to 0.223 of the stake** with retraction, the opportunities'
  edge with two events a win. Against 25 % it needs 14.2 hours at 1 s and 20.2 at 2 s, more than
  72 at 5 s, and has no depth from 10 s on. The chain's bound needs 3.3 hours against 25 % at 1 s
  (B2).
- **Without retraction the bound would be the chain's peer only at short delays.** Against a third
  it would need 3.5 hours at 1 s, against the chain's 9.6, and 31.2 at 10 s, against 23.0.

**J.3.3 — Gaži, Motaqy and Russell's machinery.** Under J.1's rule the question has no positive
answer. With retraction a third keeps the balance for ever, so no machinery bounds the error
there. Without retraction, which no rule achieves, a computable error against depth would need
three things:

- the state `(α(C), Γ²(C), …, Γ^{k*}(C))` for each block of the chain being settled, with `k*`
  explicit, where the proof takes any `k*` whose expected change per phase,
  `k* − E[#h] − E[#a]`, is positive;
- the switch between the cold, warm and hot regimes, each with its own recurrence;
- the induction from a settled block to its child, unrolled to the depth, with a union bound over
  the levels.

The recurrences bound each phase's change path by path, so a dominating Markov chain exists in
principle. But its state has one unbounded margin per `Γ^k`, and Proposition 2's condition has to
hold at every phase. It does not close cheaply and is not computed.

**H15 fails.** No bound holds a third within 11.5 hours at `Δ = 10` s under J.1's rule. Retraction
lets the balance stand for ever against a third with a positive chance at every delay from 1 s, so
the error never falls to `1e-9`. Without retraction the opportunity bound would need 31.2 hours,
above the chain's 23.0, and Gaži, Motaqy and Russell's machinery gives no depth.
