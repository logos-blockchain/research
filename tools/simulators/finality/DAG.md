# The multi-proposer DAG (Areon)

Phase E of `PLAN.md`. Paper: Castro-Castilla, Pawlowski, Zhou, "Areon: Latency-Friendly and
Resilient Multi-Proposer Consensus", arXiv 2511.23025v1. Simulator: `~/Logos/areon-simulations`,
commit `4230a92`, notebook `areon-full.ipynb` (Q9). The notebook was read, not modified. The audit
worked on copies under the session scratchpad.

Status: E0–E6 done. The owner chose to build Areon-Base on the TSI engine (E1).

## E0 — the audit

Each item below is marked by how it was established:

- **[verified]** read again in the notebook source for this note;
- **[audit]** established by the audit's re-runs and measurements, which this note has not
  repeated;
- **[preliminary]** an audit experiment too small to rely on.

Cell and line numbers are the notebook's.

**What the simulator models.**

- **No fork choice runs.** [verified] The Areon cells hold no closest-common-ancestor comparison,
  no conflicted-tips resolution and no preferred frontier; "conflict" appears only in a
  docstring. Honest blocks reference the maximum antichain of the visible blocks in the window.
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
  drift argument (Def. 5.3, Lemma 5.5) needs the subDAG between the closest common ancestor and the
  tip. That subDAG is weighed here.
- **Unit.** §2.2.3 counts a block's short references; §5.3 counts each block once (`wref ∈ {0,
  1}`). Here each block with a short reference counts once, and a block with only a long reference
  counts nothing. Counting references would let a coalition shape its private DAG wide: `m` blocks
  each referencing the same `m` others give `m²` references for `2m` blocks.
- **Horizon.** §5.3 says only references of the last `w` slots count; the drift argument
  accumulates the gap since the fork. Both are measured.
- **References.** Alg. 5 references a maximum antichain of the windowed DAG. Here an honest block
  references every tip of its view in the window, the coverage `q = 1` of §4.1.1, and only tips of
  its preferred frontier, so a defeated subDAG receives no honest reference (E4).
- **Depth.** The height of a block's descendants above it, along references (Def. 5.1).
- **Wins.** Each lottery win makes one block (E3).

The race: a coalition holding `α` withholds its wins and builds a private subDAG that conflicts
with the target. It may hold a premined lead. Honest blocks that do not descend from the target
count for neither side, because the coalition could reference them. The receiver accepts the
target at depth `K`; the attack succeeds if the coalition's weight then exceeds the honest weight.

Gates (`tests/test_areon.py`): honest blocks reference exactly the tips their producer holds, and
heights and arrivals follow the parents. A full mesh delays each block by its latency, and without
delay a block references the last occupied slot. On a chain-shaped DAG the race equals B3's chain
race, count for count. The weight rules and the recent-window score match hand-counted cases. Nine
mutations fail them.

## E2 — at Cryptarchia's parameters

The production coefficient `f_A` runs from Cryptarchia's `1/30` to the paper's 0.25. The window is
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
- **The DAG is narrow.** A block references 1.0–3.2 tips on average, and about 7 at the 99th
  percentile.

The private race, about 60,000 targets per point: the depth in layers (DAG) or blocks (chain) at
which the share of displaced targets falls to `1e-3` / `1e-4`, with the time to that depth in
minutes. The chain rows are C4's constant lotteries (`RATE.md`), raced the same way:

| structure | f | Blend | α = 0.10 | α = 0.25 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| DAG | 0.0333 | testnet | 3 (1.7) / 5 (2.9) | 16 (10.8) / 20 (13.5) | 40 (30.4) / 52 (39.5) |
| DAG | 0.0333 | specification | 3 (2.0) / 6 (4.0) | 15 (11.6) / 19 (14.7) | 39 (33.2) / 48 (40.9) |
| DAG | 0.05 | testnet | 3 (1.2) / 4 (1.5) | 17 (7.8) / 24 (11.0) | 45 (23.1) / 54 (27.7) |
| DAG | 0.05 | specification | 3 (1.4) / 7 (3.4) | 15 (8.3) / 19 (10.5) | 36 (21.7) / 44 (26.6) |
| DAG | 0.0667 | testnet | 4 (1.2) / 6 (1.8) | 16 (5.5) / 19 (6.6) | 48 (18.6) / 57 (22.1) |
| DAG | 0.0667 | specification | 3 (1.1) / 7 (2.7) | 16 (7.0) / 19 (8.3) | 36 (17.1) / 41 (19.5) |
| DAG | 0.1 | testnet | 3 (0.6) / 6 (1.2) | 16 (3.8) / 26 (6.1) | 39 (10.2) / 45 (11.7) |
| DAG | 0.1 | specification | 3 (0.9) / 5 (1.5) | 14 (4.6) / 18 (5.9) | 35 (12.3) / 43 (15.1) |
| DAG | 0.25 | testnet | 3 (0.3) / 5 (0.4) | 14 (1.4) / 22 (2.3) | 42 (4.7) / 53 (5.9) |
| DAG | 0.25 | specification | 3 (0.5) / 5 (0.9) | 10 (1.9) / 12 (2.3) | 28 (5.6) / 39 (7.8) |
| chain | 0.0333 | testnet | 4 (2.3) / 6 (3.4) | 19 (13.0) / 27 (18.4) | 48 (36.5) / 59 (44.9) |
| chain | 0.0333 | specification | 4 (2.6) / 6 (4.0) | 23 (17.7) / 32 (24.6) | 58 (49.6) / > 60 |
| chain | 0.05 | testnet | 4 (1.5) / 6 (2.3) | 19 (8.7) / 27 (12.4) | 50 (25.6) / > 60 |
| chain | 0.05 | specification | 4 (1.9) / 7 (3.3) | 26 (14.2) / 34 (18.6) | > 60 / > 60 |
| chain | 0.0667 | testnet | 4 (1.2) / 6 (1.8) | 20 (7.0) / 27 (9.4) | 49 (19.0) / > 60 |
| chain | 0.0667 | specification | 5 (1.9) / 8 (3.1) | 28 (12.2) / 37 (16.2) | > 60 / > 60 |

- **At the same block rate the DAG settles faster than the chain.** Against 25 % on the
  specification's Blend at `f = 1/30`, 15 layers (11.6 minutes) against 23 blocks (17.7). Against
  a third, 33 minutes against 50. No honest block is wasted, while the chain discards its orphans.
- **Raising the block rate keeps paying on the DAG.** Against 25 % on the specification's Blend:
  4.6 minutes at `f_A = 0.1` and 1.9 at 0.25. The chain's gain flattens: C1 finds its best
  interval at 15–20 s on that Blend.

The paper's §5.6 procedure fits `P(d) ≈ A·e^{−ϱd}` to each curve and reads
`d*(ε) = ln(A/ε)/ϱ`. Extrapolated to `ε = 1e-9`, the depth and, in brackets, the minutes
(`scripts/e2_fit.py`, `runs/e2/fit.csv`; the same fit is applied to the chain):

| structure | f | Blend | α = 0.10 | α = 0.25 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| DAG | 0.0333 | testnet | 15 (9) | 56 (37) | 132 (100) |
| DAG | 0.0333 | specification | 16 (10) | 49 (38) | 124 (106) |
| DAG | 0.05 | testnet | 11 (4) | 57 (26) | 150 (77) |
| DAG | 0.05 | specification | 15 (7) | 52 (29) | 112 (68) |
| DAG | 0.0667 | testnet | 19 (5) | 55 (19) | 161 (62) |
| DAG | 0.0667 | specification | 18 (7) | 54 (24) | 116 (55) |
| DAG | 0.1 | testnet | 15 (3) | 65 (15) | 122 (32) |
| DAG | 0.1 | specification | 15 (4) | 47 (15) | 110 (39) |
| DAG | 0.25 | testnet | 15 (1) | 57 (6) | 141 (16) |
| DAG | 0.25 | specification | 12 (2) | 30 (6) | 100 (20) |
| chain | 0.0333 | testnet | 16 (9) | 67 (46) | 152 (116) |
| chain | 0.0333 | specification | 18 (12) | 77 (59) | 188 (160) |
| chain | 0.05 | testnet | 15 (6) | 69 (32) | 175 (89) |
| chain | 0.05 | specification | 18 (9) | 88 (48) | 254 (153) |
| chain | 0.0667 | testnet | 17 (5) | 69 (24) | 166 (64) |
| chain | 0.0667 | specification | 20 (8) | 92 (40) | 302 (144) |

Against 25 % on the specification's Blend, the DAG reaches `1e-9` in 38 minutes at Cryptarchia's
block rate, against 59 for the chain, and in 15 and 6 minutes at ×3.2 and ×8.6 the blocks.

**The paper's prose horizon gives no finality.** Counting only the last `w` slots, the share of
targets the coalition displaces at depth 10 / 40 (premining, strictly heavier):

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

The share does not fall with depth: a coalition that keeps its private subDAG alive eventually
outweighs the honest side in some window. Theorem 5.6 holds only for the weight accumulated since
the fork.

## E3 — private eligibility

- **One win must weigh once.** Cryptarchia's ticket does not depend on the parent, so one win can
  sign several blocks. In a chain those blocks compete; in a DAG they can sit side by side in one
  subDAG and add weight each. The weight must therefore count each `ρ_LEAD` once: a second block
  with the same tag may stay valid but weighs nothing. Without that rule one win buys any weight.
- **A split coalition gets exactly its share.** Under the per-note lottery a coalition's blocks
  per slot are proportional to its stake: their ratio to honest blocks was within 2 % of
  `α/(1 − α)` at every `f_A` (`runs/e2/race.csv`). The single-identity bias of the paper's §6.3
  does not arise.

## E4 — the ledger

- **Order.** Mantle executes transactions in order. A total order over `Anc*(F_t)` can be
  topological, with ties broken by `(slot, y)`; a transaction that conflicts with an earlier one is
  skipped.
- **Conflicts.** The fork choice must have settled every conflict before the order is read. Alg. 5
  as written references a maximum antichain of the whole windowed DAG, defeated subDAGs included.
  Honest blocks would then merge both sides of a double spend, and the order alone would decide
  which one stands. Honest blocks must reference only their preferred frontier, as E1 does.
- **Stake inference.** No honest block is orphaned, so the inference can count blocks instead of
  occupied slots. Their expectation, `−s·ln(1 − f_A)` per slot for participating share `s`, is
  linear in `s`.

## E5 — delay chosen by an adversary

A full mesh whose links take `Δ` slots delivers every honest block exactly `Δ` late
(`scripts/e5_delay.py`; the race of E2, the window at least `Δ + 1`). The depth at which the
displaced share falls to `1e-3`, with minutes:

| f | Δ | s per layer | α = 0.10 | α = 0.25 | α = 0.33 |
| --- | --- | --- | --- | --- | --- |
| 0.0333 | 1 s | 38.7 | 3 (1.7) | 19 (12.6) | 42 (31.5) |
| 0.0333 | 5 s | 42.6 | 3 (1.9) | 16 (11.6) | 34 (27.5) |
| 0.0333 | 10 s | 47.7 | 3 (2.1) | 14 (11.4) | 39 (34.8) |
| 0.0333 | 20 s | 57.7 | 3 (2.6) | 13 (12.7) | 38 (40.0) |
| 0.25 | 1 s | 5.0 | 3 (0.2) | 18 (1.5) | 42 (4.0) |
| 0.25 | 5 s | 9.1 | 3 (0.4) | 13 (2.0) | 35 (5.7) |
| 0.25 | 10 s | 14.0 | 3 (0.7) | 11 (2.6) | 21 (5.2) |
| 0.25 | 20 s | 23.9 | 5 (1.9) | 15 (6.0) | 32 (13.1) |

The delay widens each layer, but the time to settle against 25 % stays at 11–13 minutes for
`Δ` from 1 to 20 s at `f_A = 1/30`. Every honest block still counts, so delay costs the honest
side a lag of about `Δ`, not a share of its rate. On the chain the same delay is what B3's
two-chain attack uses: against 25 % at `Δ = 10` s it needs 45 blocks for `1e-3`, against 23
under random delay. The DAG analog of that attack, an adversary that splits honest views between
two subDAGs, is not modeled here.

## E6 — the cost

- **Emissions.** Every block is a lottery win and so a Blend emission. The cover rate must rise
  with the blocks per slot: ×1 at `f_A = 1/30`, ×3.2 at 0.1, ×8.6 at 0.25 (E2). Votes cost ×34 to
  ×1,786 (`CERTIFIED.md`, D0).
- **References.** 1.0–3.2 per block on average, and about 7 at the 99th percentile. A header grows
  by 32 bytes per reference.
- **Computation.** Referencing the tips of the window needs one pass over its blocks. The maximum
  antichain of Alg. 5 is not needed.

## H7

H7 holds for the weight accumulated since the fork, with each `ρ_LEAD` counted once. Against 25 %
at `ε = 1e-9` the DAG settles in 38 minutes at Cryptarchia's block rate, against 59 on the chain,
and faster still at more blocks. Under the paper's prose horizon it fails: no depth settles. The
emission budget is the owner's line (Q7). The evidence is the private race; no worst-case bound
covers the DAG.
