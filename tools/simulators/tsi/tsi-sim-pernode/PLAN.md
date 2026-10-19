# Deeper uncle references — investigation plan

Branch `tsi-cousins`. Working document: it records the question, what is known, and what is
left to measure. It is not part of the report in [`reports/tsi`](../../../../reports/tsi).

## 1. The question

The countable rule lets a block reference only the **first block of a fork**: a block whose
parent lies on the referencing chain (the spec's "uncle"). The question is whether a block
should also reference:

- **cousins** (depth 2): blocks whose parent is an uncle;
- **children of cousins** (depth 3): blocks whose parent is a cousin.

Both are covered by one recursive rule: the parent of an entry carried by block `A` either
lies on the chain of `A`, or is an entry referenced by that chain or carried by `A`. The
maximum depth is the only parameter. A deeper entry counts exactly as an uncle does: its slot
joins the occupied-slot count of the Total Stake Inference (TSI).

## 2. Pins

| source | revision | read |
|---|---|---|
| logos-lips | `origin/master` `949faa95` | Cryptarchia 1.2.5 (`cryptarchia-v1-protocol.md`), Proof of Leadership (`cryptarchia-proof-of-leadership.md`), Block Execution (`bedrock-v1.1-block-construction.md`), `proof-of-quota.md` |
| logos-lips, in flight | branch `Bedrock-RFC-Eras` | rev 1.3.0 adds `era(sl_U) = era(sl_A)`; a deeper rule inherits it |
| logos-blockchain | `origin/master` `670f95653` | `services/chain/chain-service/src/uncle.rs`; deployment `uncle_reference_window_in_block: 12` |
| this repository | `origin/master` `5a26561` | branch base |

The spec 1.2.5 rule, as the simulator expresses it, is the arm
`uncle_window_anchor="parent"`, `window_absorption=12`, `uncle_order="parent"`,
`ref_scope="window"`. Only `ref_scope` is at its spec value by default (see §7).

## 3. Feasibility

### 3.1 The blocker: the ledger root of the Proof of Leadership

A Proof of Leadership (PoL) proves that the winning note is in `ledger_AGED` (the stake
snapshot) and in `ledger_LATEST` (it is unspent). For a block, `ledger_LATEST` is the note
root after its parent was executed. For a cousin `C` with parent `U`, that is the root after
`U` was executed.

No node can derive that root from chain data:

- The transactions of a referenced uncle are never executed (Block Execution).
- The header carries no state root.

The node shows the same dependency: `verify_uncle_pol` reads `ledger.state(uncle.parent)`. For
`C` that is the state of `U`, which exists only on nodes that received and executed `U`. A
validity rule built on it would depend on each node's block tree, which the spec rules out.

### 3.2 Routes

| route | how | cost | verdict |
|---|---|---|---|
| A. lag | Every PoL proves against the root of the block `L` levels above its parent. Depth up to `L + 1` is then verifiable from the referencing chain: depth 2 needs `L = 1`, depth 3 needs `L = 2`. | The circuit is unchanged (`ledger_LATEST` is a public input). The PoL input definition, header validation step 9, the leader's prover and the node's verifier change. A spent note stays eligible for `L` more blocks. | the only general route |
| B. empty parents | Allow `C` only when `U` carries no transactions and no uncles. `U.body_root` is then a constant, and the state of `U` follows from the state of its parent through Block Execution steps 1–2. | No PoL change. Its value is the share of such `U`, which depends on transaction load. The simulator does not model load. | narrow; price in Phase 3 |
| C. claimed root | `U`'s header carries its post-state root. | The root cannot be checked, so spent notes from the stake snapshot would count. | rejected |
| D. no PoL check | Count `C` without verifying its proof. | Fabricated headers inflate the count at will. | rejected |

Blend's proof of quota reads `ledger_AGED` only, so route A does not touch it.

### 3.3 What carries over unchanged

- **Epoch state.** The epoch state of a deeper entry's slot, derived on its own branch, equals
  the one derived on the referencing chain. This holds when every block of the branch lies
  after the stake snapshot, the nonce point and the TSI window of that epoch. The branch starts
  after the fork point, which lies at most `W·f⁻¹` slots before `A`. So the condition is
  `W·f⁻¹ ≤ 4⌊k/f⌋`, about `W ≤ 4k`. The spec's bound `W ≤ ⌊0.6k⌋` implies it.
- **The count.** `N_BLOCKS` already counts the slots of every carried entry. Deduplication is
  per slot.
- **Agreement.** The recursive rule reads only the chain of `A` and the carried entries.
- **Size.** If deeper entries share `MAX_UNCLES`, proposal size does not change. Blend pads
  every proposal to the maximum, so a separate cap would add one entry (361 bytes at rev 1.2.5)
  to every proposal.
- **Retention.** Anchored at the fork point, the window bounds how far back the chain must be
  reached, as it does for uncles.

What changes for the proposer: a deeper entry counts only if its ancestry is referenced. The
current selector skips an uncle whose slot is already occupied, so it may never reference the
parent of a cousin. A deeper rule needs the selector to carry such a parent when that unlocks
a new slot: up to two entries per slot at depth 2, three at depth 3.

## 4. Pilot: the most a deeper rule could recover

`scripts/depth_profile.py` uses the spec 1.2.5 rule (N = 1 000, Blend, 3 hops, degree 6). It
reads the engine's lost-slot shares (`fork.lost_slots`, Phase 1). Every epoch these file the
occupied window slots that the count misses under the smallest fork depth among their blocks.
Each trajectory runs 8 epochs, and its post-burn-in epochs are averaged. k = 256 has 10
replicates; the k = 2160 rows have 2. Values are % of occupied slots, mean (SEM over
replicates).

| k | U | δ_max | ρ | lost | depth 1 | depth 2 | depth 2, parent referenced | depth 3 | depth ≥ 4 |
|---|---|---|---|---|---|---|---|---|---|
| 256 | 4 | 4 | ≈ 0.36 | 0.09 (0.02) | 0.02 | 0.07 | 0.07 | 0.00 | 0.00 |
| 256 | 4 | 8 | ≈ 0.56 | 0.31 (0.02) | 0.05 | 0.25 | 0.23 | 0.00 | 0.00 |
| 256 | 4 | 16 | ≈ 0.96 | 1.39 (0.11) | 0.10 | 1.27 | 1.19 | 0.01 | 0.00 |
| 256 | 4 | 32 | ≈ 1.76 | 5.60 (0.19) | 0.59 | 4.75 | 4.55 | 0.25 | 0.00 |
| 2160 | 4 | 16 | ≈ 0.96 | 1.40 (0.09) | 0.04 | 1.33 | 1.25 | 0.03 | 0.00 |
| 2160 | 4 | 32 | ≈ 1.76 | 4.95 (0.66) | 0.40 | 4.25 | 4.10 | 0.28 | 0.02 |
| 256 | 2 | 16 | ≈ 0.96 | 1.50 (0.07) | 0.16 | 1.31 | 1.25 | 0.03 | 0.00 |
| 256 | 2 | 32 | ≈ 1.76 | 7.77 (0.41) | 2.68 | 4.81 | 4.63 | 0.26 | 0.02 |
| 256 | 1 | 16 | ≈ 0.96 | 4.83 (0.28) | 3.46 | 1.36 | 1.27 | 0.02 | 0.00 |

Reading:

- At U = 4, 77–95 % of the loss sits at depth 2, and 89–96 % of that has a referenced parent.
  The depth-2 ceiling is about 0.07 pp at ρ ≈ 0.36, 0.23 pp at ρ ≈ 0.56, 1.2 pp at ρ ≈ 1 and
  4.1–4.6 pp at ρ ≈ 1.8.
- Depth 3 holds at most 0.03 pp at ρ ≈ 1 and 0.28 pp at ρ ≈ 1.8 (U ≥ 2). Depth ≥ 4 holds at
  most 0.02 pp.
- At ρ ≤ 1 the lost shares agree with the report's countable–unrestricted gaps at U = 4
  (§3.2: 0.09, 0.31, 1.19 pp). At ρ ≈ 1.8 they run 0.3–0.9 pp above §3.2's 4.66 pp, which was
  measured under the uncle anchor at W = 10. The extra is depth 1 (0.4–0.6 pp), which is
  where the parent anchor's window binds.
- At U ≤ 2 under overload, depth-1 loss appears: capacity and the window bind.

Caveats:

- The classification is static. It ignores the feedback through the estimate D̂.
- "Parent referenced" reflects today's selector.
- One topology only.

Run: `python scripts/depth_profile.py`.

## 5. Phases

Every gate must be shown to fail under a mutation of the code it guards before it counts.

- **Phase 0 — spec 1.2.5 baseline.** *Done.*
  - Upstream already has the parent anchor, W = 12 and the window scope. Missing was the spec's
    selection order `(sl_parent, sl_U, id)`: the simulator ordered by `(sl_U, id)` under
    either anchor.
  - Added: `uncle_order`, default `"uncle"`, so that every committed key and number is
    unchanged.
  - Gates (each fails under its mutation):
    - `test_parent_order_takes_the_oldest_parent_first`;
    - `test_parent_anchor_rejects_a_stale_tip_fork` — no test covered the parent anchor before;
    - `test_uncle_order_key_is_tagged_and_paired`;
    - `test_every_sweep_axis_is_recorded_and_grouped`.
  - Found and fixed: `equilibrium()` grouped trajectories by `CONFIG_COLS`, which lacked
    `uncle_window_anchor`, `uncle_order` and `ref_scope`; `ref_scope` was not recorded at all.
    A sweep over any of them came back as the mean of its arms. No committed script analyses
    the anchor sweeps through `equilibrium()` (`w_pairing_analysis.py` groups by the anchor
    itself), so no published number is shown to be affected. Report §9 names that script for
    the §6.12 knee and cap tables too. But it reads only `pref-window-anchor*` sweeps and
    computes the W crossing. Those two tables have no committed analysis, so whether they went
    through `equilibrium()` could not be checked.
  - Measurement: `configs/spec-order-paired.yaml` (k = 2160, 20 paired replicates, parent
    anchor, W = 12), analysed by `scripts/spec_order_analysis.py`. The spec order moves nothing
    measurable:
    - U = 0 is bit-identical in all 80 pairs (the identity check);
    - every U ≥ 1 pair is bit-identical at ρ ≤ 0.56, and 221 of 240 are overall;
    - the largest gap is −0.0007 ± 0.0003 (t = 2.2) at δ_max = 32, U = 2. It does not
      survive the Bonferroni threshold of 2.87 for 12 cells.

    The order matters only when the cap binds and the parent order differs from the slot
    order. So the parent-arm results stand at W = 12. The W sweeps of §6.12 (the knee table and
    the W crossing) were not re-run under the spec order.
  - Equilibrium D̂/D under the spec rule, U = 4: 0.9999 / 0.9968 / 0.9868 / 0.9492 at
    δ_max = 4 / 8 / 16 / 32. This is the depth-1 baseline for Phase 2.
- **Phase 1 — depth metric in the engine.** *Done.*
  - `fork.lost_slots` classifies the occupied window slots, next to `deep_orphan_share`. That
    metric is a block share at depth ≥ 2; the new one is the lost slots by depth.
  - It shares `canonical_and_depth` with `fork_stats`, so the chain and depth rules exist
    once.
  - `EpochResult`, the result rows and `equilibrium()` carry five shares: depth 1, 2, 2 with a
    counted parent, 3, and ≥ 4.
  - `scripts/depth_profile.py` now reads them, instead of keeping its own classifier.
  - Gates:
    - `test_lost_slots_match_the_measured_count`: on an epoch with deep forks,
      `occupied − lost` equals every node's measured `m`, exactly. This holds under the
      countable model in both scopes, and under `--old`.
    - `test_lost_slots_by_depth_and_scope`: a hand-built tree pins the buckets, the
      shallowest-block rule, the scope and the parent mark.
    - Six mutations of `lost_slots` each fail one of the two tests.
  - Cost: 4 ms on a 22 000-block epoch at k = 2160 (0.45 % of the epoch).
- **Phase 2 — deeper references in the simulator.**
  - `max_depth` ∈ {1, 2, 3}, where 1 is today's rule. Add a ceiling arm: any depth, slot
    deduplication, no ancestry condition. It replaces `--old`, which deduplicates by block
    and differs at U = 1 (§3.2).
  - The window is anchored at the fork point, and the cap is shared. The selector may carry an
    unreferenced ancestor to unlock a deeper slot. The counting checks in `measure.py` accept
    the same entries.
  - Sweeps, all paired: the `countable-vs-old-paired` grid, `fine-delay-paired`,
    `rho-boundary`, and the §3.7 N-scaling. U = 0 is the identity check.
  - Output: D̂/D at equilibrium for each depth. Report whether depth 3 pushes cap use high
    enough that depth-1 loss returns at U = 4.
- **Phase 3 — the minimal rule set for route A.**
  - The recursive parent rule.
  - The lag `L` as one constant, with its constraint where it is defined: `L ≥ max depth − 1`.
    If `L` is smaller, the deepest entries cannot be verified.
  - Every place that reads `ledger_LATEST`: PoL input 5, header validation step 9,
    `valid_uncle`, the node's prover and verifier.
  - Route B priced.
- **Phase 4 — security.**
  - What `L` blocks of spent-note eligibility cost, for `L` = 1 and 2.
  - §6.4 (withholding) and §6.6 (selfish mining) re-run with deeper references. With them, the
    first `max_depth` blocks of a released branch count.
  - If uncle rewards are ever added: `w_u + w_n < 1`, extended to self-orphaning `max_depth`
    blocks.
  - The spec's "self-signed later" caveat, applied at every depth.
- **Phase 5 — cost.**
  - Node changes: a referenced-entry index in `verify_uncles_ancestry`; a deeper entry
    verified against the state of the fork point.
  - The prover proves against the lagged root.
  - Whether the lag takes proving off the critical path (unmeasured).
  - Cap pressure, by depth.
- **Phase 6 — decision, one depth at a time.**
  - Depth 2 goes to an RFC only if the PoL owners accept `L = 1` and its gain clears the
    ±0.9 % per-epoch noise at the ρ projected for production (§3.7).
  - Depth 3 additionally needs its gain over depth 2 to clear that noise, and `L = 2` accepted.
  - A depth that fails is recorded in the report as an overload contingency (§8.3).

## 6. Open questions

1. Is a lag of `ledger_LATEST` acceptable to the PoL owners, at `L = 1` and at `L = 2`? This
   blocks Phase 3 onward.
2. What ρ does production expect (Blend budget, N, peering degree)? Up to ρ ≈ 0.56 the
   depth-2 ceiling is under 0.25 pp, well inside the ±0.9 % per-epoch noise.
3. ~~Should the simulator defaults move to the spec 1.2.5 rule?~~ Decided 2026-10-19: not on
   this branch. Its configs set the spec rule explicitly. Moving the defaults is a separate
   task, done together with re-pinning the report to 1.2.5 (§7).

## 7. Drift found outside this study

Not fixed on this branch.

- **Simulator defaults** are the rule before Cryptarchia 1.2.0: uncle anchor, W = 10, order
  by uncle slot. `scripts/spec_point.py` and `scripts/spec_jitter.py` label the uncle anchor
  "SPEC AS DEPLOYED". Spec 1.2.0–1.2.5 and the node use the parent anchor at W = 12. To move
  together with the report re-pin below.
- **The report, §6.12 and §8.5:** §8.5 is measured against rev 1.2.1, and lists the uncle
  anchor and W = 10 as the current spec. §6.12 calls the uncle anchor at W = 10 "today's
  recipe".
- **The report, §2.1:** the countable bullet gives `W_abs = 10` and says references "never
  affect a block's validity". The bullet before it says the spec rejects a block that carries
  an invalid entry.
- **The report, §3.2:** it says the residual cannot be split into first-fork and capacity
  loss. §4 above splits it.
- **Lint:** an unused `dataclasses` import in `tests/test_multi_coalition.py`.
- **Analysis grouping:** fixed on this branch (Phase 0).
