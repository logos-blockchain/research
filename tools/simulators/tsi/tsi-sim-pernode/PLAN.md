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

Depth 3 is out of scope from Phase 3 on (decided 2026-10-19). Phase 2 measured its gain over
depth 2, and the gain fails the Phase 6 gate at every load.

## 2. Pins

| source | revision | read |
|---|---|---|
| logos-lips | `origin/master` `949faa95` | Cryptarchia 1.2.5 (`cryptarchia-v1-protocol.md`), Proof of Leadership (`cryptarchia-proof-of-leadership.md`), Block Execution (`bedrock-v1.1-block-construction.md`), `proof-of-quota.md`, `payload-formatting.md`, `blend-protocol.md`, `bedrock-service-reward-distribution.md`, `trusted-setup-ceremony.md` |
| logos-lips, in flight | branch `Bedrock-RFC-Eras` | rev 1.3.0 adds `era(sl_U) = era(sl_A)`; a deeper rule inherits it |
| logos-blockchain | `670f95653` (`origin/master` when pinned) | `services/chain/chain-service/src/uncle.rs`, `services/chain/chain-leader/src/leadership.rs`, `consensus/cryptarchia-engine/src/lib.rs`; deployment `uncle_reference_window_in_block: 12` |
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
| A. lag | Every PoL proves against the root of the block `L` levels above its parent. Depth up to `L + 1` is then verifiable from the referencing chain: depth 2 needs `L = 1`, depth 3 needs `L = 2`. | The circuit is unchanged (`ledger_LATEST` is a public input). The PoL input definition, header validation step 9, the leader's prover and the node's verifier change. A spent note stays eligible for `L` more blocks. Those are chain blocks, so they earn a reward and fork-choice weight. An uncle's proof reads the state of its parent's parent: one chain block beyond the window, which is anchored to the parent to bound retention (`cryptarchia-v1-protocol.md:327`). | general; needs the PoL owners (§6, question 1) |
| A′. dual proof | Every header carries a second PoL, from the same circuit, against the state of its grandparent. The chain checks only the first proof. A cousin is checked only by its second proof. It then proves what an uncle at its slot with parent `G` proves. | +128 bytes per header. Blend pads every message to the maximum proposal (§3.3), which holds 5 headers, so every Blend message grows by 640 bytes: 19 318 → 19 958, +3.3 %. Storage grows by 128 bytes per stored header. Every block needs a second proving run. Proving is benchmarked only on a 24-core laptop (678 ms on one thread, PoL Benchmarks); Blend sizes for a Raspberry Pi 5 (`blend-protocol.md:481`). Three rules are needed. Header validation enforces the second proof: an unchecked one earns nothing (`:380`), and the node makes a fresh `P_LEAD` on every proving call (`leadership.rs:194–195`). The block-ID preimage absorbs the second proof (`:272`, `:274–288`). `sl_U < sl_C` is stated, and `U` is read from `uncle_headers` of `A`'s chain, never from the block tree. Enforcement must handle a child of genesis, and a grandparent older than the snapshot after a halt longer than an epoch. One proof over both roots would add 32 bytes per header instead, but it is a new circuit and needs a new Groth16 phase 2 (`trusted-setup-ceremony.md:66`). | sound; costs every Blend message |
| B. unchanged parents | Verify `C`'s own PoL against the state of `U`'s parent. It verifies exactly when `U` changed no note. That holds when `U` carries no transactions (its uncles are never executed) and is not the first block of an epoch that distributes service rewards (`bedrock-service-reward-distribution.md:53`). | No PoL change. Its value is the share of such `U`, which depends on transaction load. The simulator does not model load. | narrow; price in Phase 3 |
| C. claimed root | `U`'s header carries its post-state root. | The root cannot be checked, so spent notes from the stake snapshot would count. | rejected |
| D. no PoL check | Count `C` without verifying its proof. | Fabricated headers inflate the count at will. | rejected |
| E. re-rooting | The leader of an orphaned block `X` at depth ≥ 2 proves its win at `sl_X` again, against the state of the fork point `G`. It publishes a header at `sl_X` with parent `G`. That header is the first block of a fork, so the 1.2.5 rules accept it as an uncle (`cryptarchia-v1-protocol.md:325–329`). The spec records that a note owner can self-sign such a header later (`:331`). Header validation bounds a header's slot only by the current slot (step 6) and its height only by the latest immutable block (step 8). | No consensus, header, circuit or per-message change. Each re-rooted block costs one proving run, off the critical path, and one Blend message. The slot's leadership quota went to the original proposal (`Q_L = β_D(1 + R_D)`, and the key nullifier binds the note key, the index and the slot, `proof-of-quota.md:197–204`). So the message needs core or proof-of-work quota. It covers every depth. Its gain is at most the Phase 2 ceiling. Two things reduce it: the delay to detect the orphaning, prove and propagate, all within `W·f⁻¹` slots of `G`; and leaders that do not re-root, since uncles earn nothing (`:380`, `:386`). | lead candidate; measure (Phase 2b) |

Blend's proof of quota reads `ledger_AGED` only, so route A does not touch it.

Node work for any route that carries cousins: `uncle.rs:116–122` rejects an entry whose parent is off the chain, `uncle.rs:131–134` panics when the parent's state is missing, and the engine records only the slots of referenced uncles, not their IDs (`cryptarchia-engine/src/lib.rs:180–182`). Re-rooting needs none of it.

### 3.3 What carries over unchanged

- **Epoch state.** The epoch state of a deeper entry's slot, derived on its own branch, equals
  the one derived on the referencing chain. This holds when every block of the branch lies
  after the stake snapshot, the nonce point and the TSI window of that epoch. The branch starts
  after the fork point, which lies at most `W·f⁻¹` slots before `A`. So the condition is
  `W·f⁻¹ ≤ 4⌊k/f⌋`, about `W ≤ 4k`. The spec's bound `W ≤ ⌊0.6k⌋` implies it.
- **The count.** `N_BLOCKS` already counts the slots of every carried entry. Deduplication is
  per slot.
- **Agreement.** The recursive rule reads only the chain of `A` and the carried entries.
- **Size.** If deeper entries share `MAX_UNCLES`, the maximum proposal does not change. Blend
  pads every message, not only proposals, to that maximum (`Max_Body_Length`,
  `payload-formatting.md:78–82`). A separate cap would add one 361-byte entry to every Blend
  message: 19 318 → 19 679 bytes, +1.9 %.
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
      survive the Bonferroni threshold of 3.25 for 12 cells (Student t, 19 degrees of
      freedom).

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
- **Phase 2 — deeper references in the simulator.** *Done.*
  - Model: `SimConfig.uncle_depth` is 1 (the spec), 2 (cousins), 3 (children of cousins) or
    0 (the ceiling: any depth, slot deduplication, no ancestry condition). The ceiling stands
    in for `--old`, which deduplicates by block and differs at U = 1 (§3.2).
  - Rule: every fork block between an entry and the chain is referenced by the chain or
    carried in the same block. The window is measured to the fork point, and the cap is
    shared. The selector carries a missing fork block first when the cap, its view and the
    window allow it; otherwise it takes a cheaper entry. `tsi.countable_refs` and both kernels
    in `measure.py` accept the same entries.
  - Gates:
    - `tests/test_deeper_refs.py`: the oracle and both kernels on a hand-built fork (depths
      1–4, every depth setting, both anchors); the kernels against the oracle on simulated
      trees; selection and counting agree end to end; the selector unlocks, skips and orders
      as specified.
    - `test_lost_slots_match_the_measured_count` extended to depth 2 and the ceiling.
    - Thirteen mutations each fail a test. Depth 1 reproduces three Phase 0 cells bit for bit.
  - Sweeps: 20 paired replicates, the spec 1.2.5 rule, N = 1 000, Blend with 3 hops. ρ comes
    from `rho_for`. Analysis: `scripts/depth_analysis.py`.
    - `configs/depth-overload-paired.yaml`: k = 2160, ρ ≈ 0.36 / 0.56 / 0.96 / 1.76,
      U = 0 / 1 / 2 / 4, depths 1 / 2 / 3 / 0.
    - `configs/depth-rho-boundary-paired.yaml`: k = 256, ten loads from ρ ≈ 0.56 to 1.96,
      U = 1 / 2 / 3, depths 1 / 2 / 0.
    - `configs/depth-fine-paired.yaml`: k = 2160, ρ ≈ 0.21–0.41, U = 1 / 2 / 4, depths 1 / 0.
    - The §3.7 N-scaling was not run. N moves accuracy only through ρ, which the boundary
      sweep covers directly.
  - Checks:
    - U = 0 is bit-identical in all 80 pairs of every deeper arm.
    - Counting rejected no entry that selection emitted, in any of the 3 680 trajectories
      (`deep_ref_share` = 0).
    - The δ_max = 4 cells of the overload and fine sweeps agree in every column of every
      epoch row.
    - No arm sits above D̂/D = 1 beyond noise (largest z = 1.97 over 184 cells).
  - Significance: the U ≥ 1 gaps of each printed table form one family, tested by Bonferroni
    at 5 % with the Student t quantile at 19 degrees of freedom (thresholds 3.35–3.96).
  - Equilibrium D̂/D on the overload grid, with paired gaps (mean ± SEM; * resolved):

    | ρ | U | depth 1 | depth 2 | depth 2 − 1 | depth 3 − 2 | ceiling − depth 2 |
    |---|---|---|---|---|---|---|
    | 0.36 | 2 | 0.9975 | 0.9991 | +0.0016 ± 0.0006 | −0.0003 ± 0.0004 | −0.0003 ± 0.0004 |
    | 0.36 | 4 | 0.9999 | 1.0001 | +0.0003 ± 0.0006 | +0.0001 ± 0.0003 | +0.0001 ± 0.0003 |
    | 0.56 | 2 | 0.9960 | 0.9998 | +0.0037 ± 0.0005 * | −0.0005 ± 0.0004 | −0.0003 ± 0.0005 |
    | 0.56 | 4 | 0.9967 | 0.9986 | +0.0019 ± 0.0006 | +0.0009 ± 0.0007 | +0.0011 ± 0.0006 |
    | 0.96 | 2 | 0.9861 | 0.9981 | +0.0120 ± 0.0009 * | −0.0001 ± 0.0007 | +0.0002 ± 0.0005 |
    | 0.96 | 4 | 0.9868 | 0.9993 | +0.0125 ± 0.0009 * | +0.0002 ± 0.0006 | +0.0001 ± 0.0005 |
    | 1.76 | 2 | 0.9220 | 0.9568 | +0.0348 ± 0.0014 * | +0.0017 ± 0.0005 | +0.0018 ± 0.0003 * |
    | 1.76 | 4 | 0.9492 | 0.9892 | +0.0400 ± 0.0022 * | +0.0017 ± 0.0006 | +0.0027 ± 0.0006 * |

  - Reading:
    - Up to ρ ≈ 0.96 depth 2 recovers what the ceiling recovers: no ceiling − depth 2 gap is
      resolved there (largest |t| = 1.8). On the boundary grid (k = 256) none is resolved up
      to ρ ≈ 1.96 (largest |t| = 1.9).
    - At ρ ≈ 1.76 the slots beyond depth 2 are worth +0.0018 ± 0.0003 (U = 2) and
      +0.0027 ± 0.0006 (U = 4), both resolved. Depth 3 alone gains +0.0017 in both cells,
      from about 0.17 pp of depth-3 slots, and is not resolved (|t| = 3.1–3.2 against 3.74).
      Either way the gain beyond depth 2 is under a third of the ±0.9 % per-epoch noise, so
      depth 3 fails the accuracy part of the Phase 6 gate at every load measured.
    - Depth 2 is not resolved at ρ ≈ 0.36. On the overload grid at ρ ≈ 0.56 it gains
      0.19–0.37 pp, resolved at U = 1 and 2. At U ≥ 2 its gain passes the ±0.9 % per-epoch
      noise from ρ ≈ 0.9: on the boundary grid at U = 2 it is +0.0086 at ρ ≈ 0.76 and +0.0106
      at ρ ≈ 0.91.
    - At U = 4, depth 2 keeps D̂/D at 0.9986 or above up to ρ ≈ 0.96. At ρ ≈ 1.76 it gives
      0.9892, against 0.9492 at depth 1. At U = 3 on the boundary grid it gives 0.9932 at
      ρ ≈ 1.56 and 0.9669 at ρ ≈ 1.96, against 0.9581 and 0.9173.
    - At U = 1, depth 2 gains at most +0.0104 ± 0.0021 (ρ ≈ 1.16), and under 0.005 past
      ρ ≈ 1.2, where depth-1 loss reaches 16–33 %. An entry whose parent is not yet
      referenced costs two entries, which U = 1 cannot carry.
    - In the design band (fine sweep, ρ ≈ 0.21–0.41) the ceiling gains at most
      +0.0015 ± 0.0004 (ρ ≈ 0.41, U = 4, |t| = 4.1, the only resolved cell). That is a sixth
      of the per-epoch noise.
    - The §4 pilot predicted the gain. Its depth-2 ceiling at U = 4 was 0.07 / 0.23 / 1.2 /
      4.1–4.6 pp. The measured depth-2 gains are 0.03 / 0.19 / 1.25 / 4.00 pp.
  - Cap pressure: at U = 4 every deeper arm raises depth-1 loss at ρ ≈ 1.76, by
    +0.101 ± 0.014 pp (depth 2), +0.110 ± 0.010 (depth 3) and +0.109 ± 0.011 (ceiling). At
    ρ ≤ 0.96 the rise is at most 0.007 pp and not resolved. Under overload at U = 1 and 2 it
    is 0.27–0.48 pp at ρ ≈ 1.76. The D̂/D gains above are net of it.
  - Residual: at ρ ≈ 1.76 and U = 4, depth 2 and the ceiling leave the same 0.27 pp of
    depth-2 slots uncounted. The window, the cap and the proposer's view bind those slots, not
    the ancestry condition.
- **Phase 2b — re-rooting in the simulator (route E).** *Next.*
  - Model: a leader whose block `X` sits at depth ≥ 2 in its own view publishes a copy of `X`
    at `sl_X` with parent the fork point `G`. It does so after a delay for detecting the
    orphaning and proving. The copy then travels like a block, and the spec 1.2.5 rule counts
    it as an uncle. Two parameters: the share of leaders that re-root, and the delay.
  - Re-rooting adds no rule per depth, so it re-roots every depth ≥ 2. The analysis reports
    depth 2 and depth ≥ 3 apart.
  - Arms, paired: depth 1 (the spec), depth 2, the ceiling, and re-rooting from full
    participation at zero delay down to partial participation at realistic delays.
  - Gates: at zero participation, re-rooting is bit-identical to depth 1; counting rejects no
    copy that selection emits; a hand-built tree pins which copies count.
- **Phase 3 — the minimal rule set for route A.**
  - The parent rule at maximum depth 2.
  - The lag `L = 1` as one constant, with its constraint where it is defined:
    `L ≥ max depth − 1`. If `L` is smaller, the deepest entries cannot be verified.
  - Every place that reads `ledger_LATEST`: PoL input 5, header validation step 9,
    `valid_uncle`, the node's prover and verifier.
  - Route B priced.
- **Phase 4 — security.**
  - What one block of spent-note eligibility costs (`L = 1`).
  - §6.4 (withholding) and §6.6 (selfish mining) re-run with cousins. With them, the first
    two blocks of a released branch count.
  - Whether those analyses assume that only the first block of a released branch can count.
    Under 1.2.5 every block of it can, by re-rooting.
  - If uncle rewards are ever added: `w_u + w_n < 1`, extended to self-orphaning two blocks.
  - The spec's "self-signed later" caveat, applied at every depth.
- **Phase 5 — cost.**
  - Node changes: a referenced-entry index in `verify_uncles_ancestry`; a deeper entry
    verified against the state of the fork point.
  - The prover proves against the lagged root.
  - Whether the lag takes proving off the critical path (unmeasured).
  - Re-rooting: leader-side logic only. It detects the orphaning, proves again, and publishes
    under core or proof-of-work quota.
- **Phase 6 — decision.**
  - Depth 2 goes to an RFC only if the PoL owners accept `L = 1` and its gain clears the
    ±0.9 % per-epoch noise at the ρ projected for production (§3.7).
  - Re-rooting changes no rule. If Phase 2b shows a gain that clears the same noise, it is
    proposed as leader behaviour next to Uncle Selection.
  - Depth 3 needed its gain over depth 2 to clear that noise. It did not (Phase 2).
  - A depth that fails is recorded in the report as an overload contingency (§8.3).

## 6. Open questions

1. Is a one-block lag of `ledger_LATEST` (`L = 1`) acceptable to the PoL owners? This blocks
   route A from Phase 3 on. Re-rooting (Phase 2b) does not depend on it.
2. What ρ does production expect (Blend budget, N, peering degree)? Depth 2 gains under
   0.4 pp up to ρ ≈ 0.56. At U ≥ 2 it passes the ±0.9 % per-epoch noise from ρ ≈ 0.9
   (Phase 2).
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
