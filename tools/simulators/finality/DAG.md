# The multi-proposer DAG (Areon)

Phase E of `PLAN.md`. Paper: Castro-Castilla, Pawlowski, Zhou, "Areon: Latency-Friendly and
Resilient Multi-Proposer Consensus", arXiv 2511.23025v1. Simulator: `~/Logos/areon-simulations`,
commit `4230a92`, notebook `areon-full.ipynb` (Q9). The notebook was read, not modified. The audit
worked on copies under the session scratchpad.

Status: E0 done. E1–E6 wait on the decision at the end of this note.

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

H7 cannot be judged from the paper's numbers. E1 therefore changes from "reproduce" to "build":
an implementation of Areon-Base's fork choice (Alg. 5–7). It would be built on the TSI engine's
network, Blend delays and private lottery, with the paper's Theorem 5.6 depth and §5.6 procedure
as the measurements, and attacked by the same private-chain race as B3, extended to the DAG.

The other route is that the paper's authors repair the notebook first. That is the owner's call.
