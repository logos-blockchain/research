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
| logos-lips | `origin/master` `949faa95` | Cryptarchia 1.2.5 (`cryptarchia-v1-protocol.md`), Proof of Leadership (`cryptarchia-proof-of-leadership.md`), Block Execution (`bedrock-v1.1-block-construction.md`), Synchronization (`cryptarchia-v1-bootstr-sync.md`), `proof-of-quota.md`, `payload-formatting.md`, `blend-protocol.md`, `bedrock-service-reward-distribution.md`, `trusted-setup-ceremony.md` |
| logos-lips, in flight | branch `Bedrock-RFC-Eras` | rev 1.3.0 adds `era(sl_U) = era(sl_A)`; a deeper rule inherits it |
| logos-blockchain | `670f95653` (`origin/master` when pinned) | `services/chain/chain-service/src/uncle.rs`, `services/chain/chain-leader/src/leadership.rs`, `consensus/cryptarchia-engine/src/lib.rs`, `ledger/src/lib.rs`, `services/chain/chain-service/src/sync/block_provider.rs`, `services/tx-service/src/backend/pool.rs`, `services/tx-service/src/backend/policy/powclaim.rs`; deployment `uncle_reference_window_in_block: 12`, proof-of-work `slot_window: 300` |
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
| C. snapshot-only references | A reference's PoL is verified against the epoch state of its slot and against a `ledger_LATEST` that the entry carries and no node checks. The count then rests only on the lottery: a note of the stake snapshot won the slot. No chain state is read, so the ancestry condition can go and every depth counts. The window can be measured to the entry's own slot: the parent anchor exists to bound the state the check reads (`cryptarchia-v1-protocol.md:327`). | The circuit is unchanged. Each entry carries its root, +32 bytes, so every Blend message grows by 128 bytes: 19 318 → 19 446, +0.66 %. A spent note keeps counting until its snapshot expires. The snapshot of epoch `ep` is the note set at the start of epoch `ep − 1` (`:220`), so that is up to two epochs after the spend: 1 296 000 slots, 15 days at 1 s per slot. Under 1.2.5 the limit is under `W·f⁻¹` = 360 slots after the spend, through a self-signed uncle whose parent precedes the spend (`:327`, `:331`). The rule cannot stay a cousin rule: a spent note's win can name any counted uncle in the window as its parent. Whoever holds the key of a spent snapshot note can add that stake's wins to the count: its former owner, or anyone the owner sells the key to. D̂ rises by that stake (β = 1). If it is a share σ of the snapshot, the block rate falls to about `f(1 − σ)`. Eligibility (`:168`) requires an unspent note, so references need their own definition. The PoL owners must accept an unchecked `ledger_LATEST` for references. Proof of quota already skips the unspent check (`proof-of-quota.md:46`, `:118`). | pays over re-rooting under overload (Phase 2c) and against a selfish coalition (Phase 4); nothing bounds the spent stake, which can leave the snapshot phase short of `k` blocks (Phase 4); needs the PoL owners (§6, question 4) |
| C′. compact entries | An entry carries only what the PoL check reads: the slot, `P_LEAD`, `ρ_LEAD` and the proof, plus the parent (1.2.5) or the root (route C). It carries no signature. | An entry shrinks from 361 to 232 bytes (8 + 32 + 32 + 32 + 128). The maximum proposal falls by 4 × 129 = 516 bytes to 17 676, and every Blend message by the same: 19 318 → 18 802, −2.7 %. This holds at depth 1 too. Anyone who has seen a proof can build an entry from it. The count is per slot, so that adds no slot (`:331`). The block ID of a referenced block can no longer be derived (`:315`). Only the not-on-the-chain rule (`:326`) and the selection tie-break (`:366`) read it. Per-slot counting makes the first redundant, and the second can order by the proof. | independent of depth; price with route C |
| D. no PoL check | Count `C` without verifying its proof. | Fabricated headers inflate the count at will. | rejected |
| E. re-rooting | The leader of an orphaned block `X` at depth ≥ 2 proves its win at `sl_X` again, against the state of the fork point `G`. It publishes a header at `sl_X` with parent `G`. That header is the first block of a fork, so the 1.2.5 rules accept it as an uncle (`cryptarchia-v1-protocol.md:325–329`). The spec records that a note owner can self-sign such a header later (`:331`). Header validation bounds a header's slot only by the current slot (step 6) and its height only by the latest immutable block (step 8). | No consensus, header, circuit or per-message change. Each re-rooted block costs one proving run, off the critical path, and one Blend message. On a core node that message takes the place of a cover message (`blend-protocol.md:244`). The slot's leadership quota went to the original proposal (`Q_L = β_D(1 + R_D)`, and the key nullifier binds the note key, the index and the slot, `proof-of-quota.md:197–204`). So the message needs core or proof-of-work quota. It covers every depth. Its gain is at most the Phase 2 ceiling. Two things reduce it: the delay to detect the orphaning, prove and propagate, all within `W·f⁻¹` slots of `G`; and leaders that do not re-root, since uncles earn nothing (`:380`, `:386`). | recovers the depth-2 gain when all the stake re-roots within 10 slots; the gain scales with the share that re-roots (Phase 2b); against a selfish coalition it recovers as much as depth 2 (Phase 4) |
| F. cousin parents' bodies | A cousin `C` with parent `U` is verified against the state its leader proved against: the state of the fork point `G` after `U`'s transactions, validated as a block's are. A node that accepted `U` already holds that state. Every accepted block was executed (`cryptarchia-v1-protocol.md:463`), and the node keeps a ledger state per block until the block is pruned (`ledger/src/lib.rs:149`). A fork is pruned once it diverges below the latest immutable block (`:499`), which lies at least `k` blocks, so at least 2 160 slots, below the tip (`:124`). The window spans 360 slots. So a node that validates `A` within `k − W·f⁻¹` = 1 800 slots of `sl_A` still holds `U` if it accepted it. A validator that lacks `U` downloads it, as it downloads an orphan's missing ancestors (`cryptarchia-v1-bootstr-sync.md:97`, `:180`). Peers serve any block of their block tree (`block_provider.rs:136`). The stored block that carries `C` also carries `U`'s uncle headers and transactions, for nodes that synchronise after `U` is pruned. `U`'s `body_root` commits to them, so the proposal, the header and the block ID of `A` do not change. | No PoL, circuit, header or proposal change, so no Blend change. No spent note gains eligibility. The stored block grows by one body per cousin parent: up to `MAX_BLOCK_SIZE` plus 1 445 bytes of uncle headers. Transactions the chain already holds could be stored by reference. Bodies are needed for at most the depth-2 share of §4: 0.07 % of occupied slots at ρ ≈ 0.36, 1.3 % at ρ ≈ 0.96. A node that holds none of the parents executes up to `1 + MAX_UNCLES` blocks to validate one. A validator that receives `A` before `U` cannot validate `A` until it has `U` (Phase 2d). It records no verdict meanwhile, as for an unresolved reference (`bedrock-v1.1-block-construction.md:334`). The mempool matters only for the first acceptance of `U`, as for any block. The node keeps a transaction 10 minutes after a chain block includes it, so that a competing proposal still resolves (`pool.rs:31`, `:89`). It keeps a pending transaction 1 hour by default (`pool.rs:35`, configurable), and a proof-of-work claim 600 slots past its 300-slot acceptance window (`powclaim.rs:30–31`). Each exceeds the window. None is specified. Depth 3 needs two bodies, executed in order. Changes: the uncle rules and the counted set (Cryptarchia); the stored block and "the carried `uncle_headers` are not executed" (Block Construction `:211–216`, `:397`); downloading a cousin's parent (Synchronization); in the node, `uncle.rs:116–122` and `:131–134`. | sound, no per-message cost; adds to re-rooting only where little of the stake re-roots, or late (Phases 2b and 2d, §6 questions 5 and 6) |

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
    the ancestry condition. Phase 2c: the window measured to the fork point binds them.
- **Phase 2b — re-rooting in the simulator (route E).** *Done.*
  - Model (`SimConfig.reroot_share`, `reroot_delay`):
    - Nodes holding a share of the stake re-root. The set is drawn once per replicate, so every
      arm of a replicate has the same set.
    - A re-rooting leader watches each of its blocks `X` whose parent is not genesis. Its view
      puts `X` at depth ≥ 2 from the moment its best tip leaves the subtree of `X`'s parent. The
      watch replays the leader's arrivals in time order, so the detection time is exact.
    - The leader publishes a copy `reroot_delay` slots later. The copy has the slot `sl_X`, and
      its parent is the fork point of `X` and that tip. It travels like a block, on its own
      random stream. It joins the uncle candidates of every later block, and fork choice never
      sees it. The spec 1.2.5 rule counts it as the first block of a fork.
    - One copy per block. The watch stops `W·f⁻¹` slots after `sl_X`, when no copy can enter a
      window any more.
    - Re-rooting runs on the full arrival matrix, because the watch reads the leader's arrivals
      and the prune drops them. Both matrices give the same tree (`test_pernode` parity).
  - Gates (`tests/test_reroot.py`):
    - the watch on a hand-built fork: a sibling of `X` keeps it at depth 1; a branch outside the
      parent's subtree puts it at depth 2, including one produced before `X`; simultaneous
      arrivals are taken by rank;
    - the watch against a brute-force replay of every leader's view on simulated epochs: the
      same copies, fork points and detection times;
    - a hand-built tree pins which copies count, in the oracle and both kernels, and a counted
      copy covers its slot in `lost_slots`;
    - selection takes a copy in view in age order, and only inside the window;
    - a zero share is the spec arm, key included; copies that arrive too late change no other
      column; counting rejects no copy that selection emits;
    - `test_lost_slots_match_the_measured_count` extended to re-rooting;
    - 34 mutations of the Phase 2b and 2d code each fail a gate, and every gate passes without
      them.
  - Sweep: `configs/reroot-overload-paired.yaml`, the Phase 2 overload grid (k = 2160) at
    U = 1 / 2 / 4, with 20 paired replicates: 2 160 trajectories. Arms: depth 1, depth 2, the
    ceiling, and re-rooting by half or all of the stake at a delay of 0, 10 or 60 slots.
    Analysis: `scripts/reroot_analysis.py`. Its 216 paired gaps, each re-rooting arm against
    depth 1, depth 2 and the ceiling, form one family. The Bonferroni threshold is |t| = 4.53.
  - Checks:
    - The depth arms reproduce the Phase 2 overload run in every column of all 12 980 epoch
      rows.
    - Counting rejected no entry that selection emitted, in any trajectory
      (`deep_ref_share` = 0).
    - No arm sits above D̂/D = 1 beyond noise (largest z = 1.52 over 108 cells).
  - Share of the depth-2 gain that re-rooting recovers, `(arm − depth 1) / (depth 2 − depth 1)`,
    by the share of the stake that re-roots and the delay in slots (* the gap to depth 2 is
    resolved):

    | ρ | U | depth 2 − 1 | all, 0 | all, 10 | all, 60 | half, 0 | half, 10 | half, 60 |
    |---|---|---|---|---|---|---|---|---|
    | 0.96 | 2 | +0.0120 | 1.07 | 1.04 | 1.05 | 0.56 * | 0.55 * | 0.52 * |
    | 0.96 | 4 | +0.0125 | 0.99 | 0.99 | 1.01 | 0.55 * | 0.57 * | 0.54 * |
    | 1.76 | 2 | +0.0348 | 1.02 | 0.96 | 0.75 * | 0.54 * | 0.51 * | 0.39 * |
    | 1.76 | 4 | +0.0400 | 1.01 | 0.96 | 0.72 * | 0.54 * | 0.53 * | 0.39 * |

  - Reading:
    - Re-rooting by all the stake within 10 slots recovers the depth-2 gain. No gap to depth 2
      is resolved there. The largest is −0.0017 ± 0.0007 (|t| = 2.3, ρ ≈ 1.76, U = 4,
      10 slots). At ρ ≈ 1.76 and U = 4, the 0-slot arm gives D̂/D = 0.9896, against 0.9892 at
      depth 2 and 0.9492 at depth 1.
    - A 60-slot delay costs a quarter of the gain at ρ ≈ 1.76: −0.0088 ± 0.0007 (U = 2) and
      −0.0110 ± 0.0010 (U = 4) against depth 2. At ρ ≈ 0.96 it costs nothing resolved.
    - Half the stake recovers about half the gain: 0.51–0.57 at a delay of 10 slots or less
      (U ≥ 2). At ρ ≈ 1.76 a 60-slot delay brings that to 0.39.
    - Copies also cover depth ≥ 3. At ρ ≈ 1.76 and U = 4, all the stake at 0 slots leaves
      0.09 pp of occupied slots lost at depth ≥ 3, against 0.24 pp at depth 2 and 0.05 pp for
      the ceiling. It leaves 0.45 pp lost at depth 2, against 0.27 pp for depth 2 and the
      ceiling. That share grows with the delay: 0.54 pp at 10 slots and 1.47 pp at 60. Net,
      re-rooting is level with depth 2 and 0.0023 ± 0.0004 below the ceiling (|t| = 5.3).
    - A leader detects the orphaning 14–15 slots after the block's slot on average at
      ρ ≈ 0.96, and 28–29 slots after it at ρ ≈ 1.76.
    - At ρ ≈ 0.56 all the stake gains +0.0028 to +0.0035 at U ≥ 2, resolved and level with
      the ceiling. At ρ ≈ 0.36 no gap to depth 1 is resolved (largest |t| = 2.1). Both gains
      stay under 0.4 pp, below the ±0.9 % per-epoch noise.
    - At U = 1 and ρ ≈ 0.96 all the stake gains +0.0067 to +0.0070, level with the ceiling
      (largest |t| = 0.4). At ρ ≈ 1.76 no rule gains more than +0.0020, and re-rooting gains at
      most +0.0018 (|t| ≤ 2.5). Depth-1 loss is 31 % of occupied slots there: the single entry
      per block binds before any depth does. All the stake makes copies for 12.1 % of occupied
      slots, and 0.6 % count.
    - Copies made by all the stake: 0.07–0.08 % of occupied slots at ρ ≈ 0.36, 0.30–0.32 % at
      ρ ≈ 0.56, 1.2–1.4 % at ρ ≈ 0.96 and 4.7–5.4 % at ρ ≈ 1.76 (U ≥ 2). Half the stake makes
      about half as many. Each costs one proving run and one Blend message (§3.2).
- **Phase 2c — snapshot-only references in the simulator (route C).** *Done.*
  - Model:
    - Route C counts an entry by its lottery win alone: `uncle_depth = 0` (any depth, no
      ancestry condition) with `uncle_window_anchor = "uncle"` (the window measured to the
      entry's own slot) and `uncle_order = "uncle"`. The simulator already had every piece.
    - Spent stake (`SimConfig.spent_share`): every holder has spent the share σ of its notes, and
      a coalition holds their keys. Each note runs its own lottery, so the two parts of a holder
      win independently, and together they win the slots the holder wins without spent stake
      (`lottery.spent_codes`). A win of spent notes makes no block. It becomes an entry at its
      slot, which names the tip the holder would have extended, travels as that block would
      have, and joins the uncle candidates of every later block. A slot that both parts win
      makes a block and an entry. Spent stake is defined under route C only.
    - A spent share drawn as a set of holders failed. In the Pareto stake draws of the sweep one
      holder held up to 92 % of the stake. 25 of the 480 sets missed their share by more than
      0.01, and 6 of the 120 sets at σ = 0.75 took every holder, which stopped the chain.
    - New columns: `block_rate` (window slots that hold a block, per slot), `spent_win_rate`
      (window slots that only spent notes won, per slot) and `spent_counted_share` (the share of
      those the count covers). The entry store is guarded like the arrival matrix.
  - Gates (`tests/test_spent.py`):
    - the split of a win between the two parts, at both cuts and at σ = 0;
    - a hand-built tree pins which spent wins count, in the oracle and both kernels, under both
      anchors; a counted spent win covers its slot in `lost_slots` and marks no block in `p_ref`;
    - selection takes a spent win in view in age order, at any depth, and only inside the window;
    - end to end: a win of unspent notes is a block, a win of spent notes is an entry on the tip
      its holder extends, and a slot both parts win holds both; a block whose parent arrived as
      in the honest arm arrives as in the honest arm, also after a slot both parts won; counting
      rejects no entry that selection emits; the active stake is 1 − σ;
    - `test_lost_slots_match_the_measured_count` extended to route C with and without spent
      stake: occupied − lost + the counted slots that only spent notes won equals every node's
      `m`;
    - 33 mutations of the Phase 2c code each fail a gate, and the 34 of Phases 2b and 2d still
      do. Every gate passes without them. One mutation, which sizes the arrays for every win,
      makes a gate loop; the harness counts a run past 300 seconds as a failure.
  - Sweeps, each paired with the runs it is compared against (`scripts/route_c_analysis.py`):
    - route C on the three Phase 2 grids: `configs/routec-overload-paired.yaml`,
      `configs/routec-rho-boundary-paired.yaml` and `configs/routec-fine-paired.yaml`, 1 220
      trajectories;
    - route C's window with entries taken by their fork point first (C/fp), as the ceiling takes
      them: `configs/routec-order-overload-paired.yaml` and
      `configs/routec-order-rho-boundary-paired.yaml`, 840 trajectories;
    - spent stake: `configs/routec-spent-paired.yaml`, σ = 0 / 0.1 / 0.25 / 0.5 / 0.75 at
      ρ ≈ 0.36 and 0.96, U = 1 / 2 / 4, 600 trajectories.
  - Checks:
    - In epoch 0 every arm of a replicate builds the tree that route C builds: the columns that
      read only the tree agree in all 5 960 rows.
    - At U = 0 route C agrees with depths 1, 2, 3 and the ceiling in every column both runs
      record (5 476 rows).
    - The depth arms of the Phase 2 and 2b runs agree in every column both record (12 980 rows).
    - The σ = 0 rows reproduce route C in all 80 columns (2 191 rows).
    - Counting rejected no entry that selection emitted (`deep_ref_share` = 0). No route C cell
      sits above D̂/D = 1 beyond noise (largest z = 1.54 over 129 cells).
  - Equilibrium D̂/D on the overload grid, with the paired gaps of route C (mean ± SEM;
    * resolved, by Bonferroni over 48 gaps to the depth arms, |t| = 3.87, and over 72 gaps to
    the re-rooting arms, |t| = 4.04):

    | ρ | U | depth 1 | depth 2 | ceiling | route C | C − ceiling | C − re-rooting by all, 10 slots |
    |---|---|---|---|---|---|---|---|
    | 0.96 | 1 | 0.9549 | 0.9612 | 0.9617 | 0.9772 | +0.0155 ± 0.0012 * | +0.0156 ± 0.0012 * |
    | 0.96 | 2 | 0.9861 | 0.9981 | 0.9984 | 1.0002 | +0.0018 ± 0.0005 * | +0.0015 ± 0.0004 |
    | 0.96 | 4 | 0.9868 | 0.9993 | 0.9993 | 1.0002 | +0.0009 ± 0.0005 | +0.0011 ± 0.0005 |
    | 1.76 | 1 | 0.5815 | 0.5835 | 0.5834 | 0.5862 | +0.0028 ± 0.0007 * | +0.0029 ± 0.0009 |
    | 1.76 | 2 | 0.9220 | 0.9568 | 0.9586 | 0.9939 | +0.0352 ± 0.0028 * | +0.0383 ± 0.0028 * |
    | 1.76 | 4 | 0.9492 | 0.9892 | 0.9919 | 0.9999 | +0.0080 ± 0.0009 * | +0.0124 ± 0.0012 * |

  - Reading, honest stake:
    - The window makes the difference, not the order: no gap of route C to C/fp is resolved on
      either grid (largest |t| = 2.2).
    - The fork-point window causes the Phase 2 residual. At ρ ≈ 1.76 and U = 4 route C leaves
      0.00 pp of depth-2 slots lost and 0.02 pp of depth-1 slots, against 0.27 and 0.57 pp for
      the ceiling.
    - Under the fork-point window an entry leaves the window `W·f⁻¹` slots after its fork point.
      Under route C it leaves `W·f⁻¹` slots after its own slot, which is later. Depth-1 loss
      falls most: at ρ ≈ 0.96 and U = 1, from 3.43 % to 2.09 % of occupied slots. An entry that
      waits for a free place in a block stays in the window longer.
    - Over the ceiling, route C gains at U = 1 from ρ ≈ 0.76 to 1.36 (+0.0063 to +0.0207,
      boundary grid) and by +0.0028 at ρ ≈ 1.76. It gains at U = 2 by +0.0018 at ρ ≈ 0.96
      (overload grid) and by +0.0115 to +0.0644 from ρ ≈ 1.36, at U = 3 only at ρ ≈ 1.96
      (+0.0296), and at U = 4 only at ρ ≈ 1.76 (+0.0080).
    - In the design band it gains nothing resolved: no gap at ρ ≈ 0.21–0.41 (fine grid, largest
      |t| = 2.8 against 3.66) or at ρ ≈ 0.36. At ρ ≈ 0.56 it gains +0.0040 over depth 1 at
      U ≤ 2, resolved, and nothing resolved over the ceiling.
    - Against re-rooting by all the stake within 10 slots (Phase 2b), the gain of route C passes
      the ±0.9 % per-epoch noise at ρ ≈ 1.76 with U ≥ 2 (+0.0124 at U = 4, +0.0383 at U = 2),
      and at ρ ≈ 0.96 only with U = 1 (+0.0156). Against half the stake within 10 slots it is
      +0.0064 at ρ ≈ 0.96 and +0.0296 at ρ ≈ 1.76 (U = 4), both resolved. At ρ ≤ 0.56 it is at
      most +0.0031.
  - Spent stake at U = 4 (* the paired gap in D̂/D to σ = 0 is resolved, by Bonferroni over 24
    gaps, |t| = 3.56):

    | ρ | σ | D̂/D | D̂ / active stake | 1 / (1 − σ) | block rate / f | slots only spent notes won, counted |
    |---|---|---|---|---|---|---|
    | 0.36 | 0.1 | 1.0003 | 1.1115 | 1.1111 | 0.901 | 99.99 % |
    | 0.36 | 0.25 | 1.0002 | 1.3335 | 1.3333 | 0.753 | 99.97 % |
    | 0.36 | 0.5 | 0.9979 | 1.9958 | 2.0000 | 0.505 | 99.59 % |
    | 0.36 | 0.75 | 0.9139 * | 3.6557 | 4.0000 | 0.277 | 88.82 % |
    | 0.96 | 0.1 | 1.0000 | 1.1111 | 1.1111 | 0.901 | 99.98 % |
    | 0.96 | 0.25 | 0.9998 | 1.3331 | 1.3333 | 0.753 | 99.95 % |
    | 0.96 | 0.5 | 0.9954 * | 1.9908 | 2.0000 | 0.506 | 99.28 % |
    | 0.96 | 0.75 | 0.8819 * | 3.5275 | 4.0000 | 0.287 | 85.18 % |

  - Reading, spent stake:
    - Where the cap carries the spent wins, route C counts the spent stake as active stake. D̂
      stays at the snapshot's stake, so D̂ against the active stake is 1 / (1 − σ), and the block
      rate falls to (1 − σ)f. At U = 4 that holds up to σ = 0.5 (D̂/D ≥ 0.995).
    - At σ = 0.75 the cap binds even at U = 4: 85–89 % of the slots that only spent notes won
      count, D̂/D is 0.88–0.91, and the block rate is 0.28–0.29 f.
    - Smaller caps bind sooner. At U = 2, D̂ stays within 0.002 of the snapshot's stake up to
      σ = 0.25, and falls to 0.94–0.99 of it at σ = 0.5. At U = 1 and ρ ≈ 0.36, D̂/D is 0.9986
      at σ = 0.1, 0.9943 at σ = 0.25 and 0.83 at σ = 0.5. At U = 1 and ρ ≈ 0.96 it falls to
      0.948 at σ = 0.1 and 0.29 at σ = 0.75, and the block rate stays at 0.86–0.95 f.
    - Under 1.2.5 a spent note is not eligible (`cryptarchia-v1-protocol.md:168`). Its win counts
      only through an uncle whose parent precedes the spend, so for under `W·f⁻¹` slots after
      the spend (§3.2). Beyond that, D̂ follows the active stake and the block rate stays at f.
- **Phase 2d — the live path of route F in the simulator.** *Done.*
  - Route F counts what depth 2 counts, so Phase 2 already measured its gain.
  - Metric (`BlockTree.parent_wait`, `fork.parent_wait`), under any deeper rule: per block, the
    nodes that receive it before they hold every off-chain parent of its entries, their total
    wait and the longest. It is read over the canonical window blocks of the depth-2 arm of the
    Phase 2b sweep. Those nodes must download `U` before they validate `A`.
  - The simulator makes a block usable at a node only after its parent (`blocktree.py:699`),
    so the proposer that carries `C` holds `U`. The wait runs until `U` arrives by broadcast.
    The simulator models neither the download nor its effect on fork choice, so the metric is a
    static price.
  - Gates (`tests/test_reroot.py`): hand-built parents and arrival columns pin the wait, with
    two off-chain parents and with a pruned one; it matches a recount from the full matrix in
    every block; the pruned and full matrices give the same rows.
  - Results (`scripts/reroot_analysis.py`; `scripts/parent_wait_blocks.py` re-runs the
    trajectories with a wait and lists the blocks):
    - Blocks with an entry whose parent is off the chain: 0.08–0.10 % of canonical window
      blocks at ρ ≈ 0.36, 0.38–0.42 % at ρ ≈ 0.56, 1.6–1.9 % at ρ ≈ 0.96, and 6.6–6.8 % at
      ρ ≈ 1.76 (1.6 % at U = 1).
    - A node waits in 6 of the 4 345 epochs of the 240 trajectories, burn-in included. Each
      time one block makes it wait.
    - In all six, the leader of `A` also produced `U` and `C`, and `A` carried both. The nodes
      that wait received `A` before `U`, although `U` was produced 5 to 39 slots before `A`.
    - In three of them, 999 of the 1 000 nodes wait: 2.4 slots on average (3.8 at most) at
      ρ ≈ 0.96, and 1.9 (3.1) and 12.7 (13.95) slots at ρ ≈ 1.76. In the other three, 9 to
      53 nodes wait at most 0.52 slots.
- **Phase 3 — the minimal rule set for route A.**
  - The parent rule at maximum depth 2.
  - The lag `L = 1` as one constant, with its constraint where it is defined:
    `L ≥ max depth − 1`. If `L` is smaller, the deepest entries cannot be verified.
  - Every place that reads `ledger_LATEST`: PoL input 5, header validation step 9,
    `valid_uncle`, the node's prover and verifier.
  - Route B priced.
- **Phase 4 — security.** *Done.*
  - Model:
    - Re-rooting runs against a selfish or a withholding coalition. The coalition never
      re-roots, so the re-rooting share is a share of the honest stake (`engine._reroot_mask`).
      A private block reaches an honest leader only when the coalition releases it, and the
      release reaches the leader's watch (`_Watch.renote`).
    - The lost slots are split (`fork.lost_slots`). One part holds an honest block, filed under
      the smallest depth among the honest blocks. The other holds only blocks that reached no
      node outside the coalition. Four columns record them.
    - The selfish-mining MDP of the report's §6.6 reads what a cousin rule counts: the first
      two blocks of every chain the policy discards (`OptimalPolicyStats.counted`,
      `recovery`; `reorg.countable_recovery_from_depths`). The MDP has no window.
    - A sweep can vary `adversary_frac`. An empty axis takes its value from `base`, so a config
      that sets the adversary there keeps it.
    - Every adversary but a suppressing one is sized for the full arrival matrix, which it uses.
  - Gates (`tests/test_adversary_routes.py`, `tests/test_reroot.py`):
    - a release reaches the watch on a hand-built fork, and a release after the watch expires
      is never replayed;
    - the watch against a brute-force replay of every honest leader's view under a selfish
      coalition: the same copies, fork points and detection times, some of them caused by a
      release;
    - the coalition never re-roots, and the half share is half the honest stake;
    - a hand-built tree pins the split, with a slot that holds two honest blocks; end to end,
      the split reads the measured count under a selfish coalition, with re-rooting, under
      route C, and under a withholding coalition with re-rooting;
    - the MDP counts `min(h, 2)` blocks of a discarded chain of `h` on a hand-built transition
      table; on the revenue-optimal policy depth 2 counts more than depth 1 and less than every
      block, of the honest chains and of the attacker's;
    - re-rooting is accepted against a selfish or a withholding coalition only; an empty sweep
      axis takes the base value; adversaries are sized for the full matrix;
    - 27 mutations of the Phase 4 code each fail a gate, and the 67 of Phases 2b–2d still do.
      Every gate passes without them, and again after the run. One mutation first survived:
      a re-rooting share of all the stake instead of the honest stake. The Pareto tolerance of
      its gate, the largest honest holder's share, absorbed the difference. An equal-stake case
      now fills the half exactly and fails it.
  - The mutation harness had reused stale bytecode. A mutation, its gate and the restore can
    fall within one second and keep the file's size. Python then takes the mutated `.pyc` as
    valid. A gate that failed on unmutated code showed it. Every gate run now starts from
    empty bytecode and numba caches, and the 67 earlier mutations were re-run that way.
  - Regression: the code reproduces 1 432 rows of the Phase 2, 2b and 2c runs in every column
    they record, but `parent_wait_mean` of the Phase 2b run. That run predates e1a4c4a, which
    made the mean wait NaN, not 0, where no node waits.
  - Sweeps: k = 256, the geometry of the report's selfish runs; the spec 1.2.5 rule;
    N = 1 000, Blend with 3 hops; 20 paired replicates; δ_max = 4 and 8 (ρ ≈ 0.36 and 0.56
    without a coalition). Analysis: `scripts/adversary_analysis.py`.
    - `configs/selfish-depth-paired.yaml`: an SM1 coalition of α = 0 / 0.2 / 0.3 at
      U = 2 / 4. Arms: depth 1, depth 2, the ceiling, and re-rooting by half or all of the
      honest stake 10 slots after detection. 1 200 trajectories.
    - `configs/selfish-routec-paired.yaml`: route C on the same cells and streams. 240
      trajectories.
    - `configs/withhold-depth-paired.yaml`: a withholding coalition of α = 0 / 0.2 / 0.4 at
      U = 4. Arms: depth 1, depth 2, the ceiling, and re-rooting by all the honest stake. 480
      trajectories.
  - Exclusions: in the Pareto stake draws one holder can hold most of the stake, so some draws
    leave no node set near the coalition's share. Six draws miss it by more than 0.01, by up to
    0.13, and their replicates are dropped from every arm. 14 half-share re-rooting arms miss
    half the honest stake by more than 0.01 and are dropped.
  - Checks: in epoch 0 every arm of a replicate builds the tree depth 1 builds (1 200 rows
    against SM1, 360 against withholding). Counting rejected no entry that selection emitted.
  - Equilibrium D̂/D against an SM1 coalition at U = 4, with paired gaps (mean ± SEM;
    * resolved, by Bonferroni over the 84 gaps of both caps, |t| = 4.11):

    | ρ | α | depth 1 | depth 2 | ceiling | route C | re-rooting by all | depth 2 − 1 | re-rooting by all − 1 | route C − 1 | route C − re-rooting by all |
    |---|---|---|---|---|---|---|---|---|---|---|
    | 0.36 | 0.2 | 0.9194 | 0.9643 | 0.9701 | 0.9902 | 0.9651 | +0.0449 ± 0.0027 * | +0.0457 ± 0.0021 * | +0.0708 ± 0.0018 * | +0.0251 ± 0.0014 * |
    | 0.36 | 0.3 | 0.8158 | 0.8644 | 0.8830 | 0.9481 | 0.8748 | +0.0486 ± 0.0019 * | +0.0590 ± 0.0021 * | +0.1323 ± 0.0029 * | +0.0733 ± 0.0026 * |
    | 0.56 | 0.2 | 0.9041 | 0.9541 | 0.9611 | 0.9871 | 0.9544 | +0.0500 ± 0.0021 * | +0.0503 ± 0.0021 * | +0.0830 ± 0.0027 * | +0.0327 ± 0.0016 * |
    | 0.56 | 0.3 | 0.7789 | 0.8336 | 0.8562 | 0.9311 | 0.8400 | +0.0546 ± 0.0024 * | +0.0611 ± 0.0026 * | +0.1522 ± 0.0036 * | +0.0911 ± 0.0034 * |

  - Reading, selfish mining:
    - Without a coalition no gap is resolved (largest |t| = 2.4), as in Phase 2.
    - Against an SM1 coalition every rule gains far more than the ±0.9 % per-epoch noise.
      Depth 2 gains 4.5–5.5 pp of D̂/D, and re-rooting by all the honest stake within 10 slots
      4.6–6.1 pp. The ceiling gains 5.1–7.7 pp, and route C 7.1–15.2 pp. Re-rooting by half
      the honest stake gains 2.6–3.2 pp. At U = 2 every gain is within 1.5 pp of its value at
      U = 4.
    - Under depth 1 the honest loss sits deep. At ρ ≈ 0.56 and α = 0.3, slots held by an
      uncounted honest block make up 2.0 % of the occupied slots at depth 1, 6.1 % at depth 2
      and 10.8 % at depth ≥ 3. Depth 2 brings the depth-2 share to 1.6 %. The ceiling and
      re-rooting leave 8.6–8.9 % at depth ≥ 3. An override discards a branch whose fork point
      lies long before its last blocks, and both measure the window to the fork point. Route C
      measures it to each entry's own slot and leaves 3.0 %.
    - Slots whose blocks the coalition never published make up at most 0.3 % of the occupied
      slots. SM1 releases its chain in a match race, so it seldom abandons one.
    - Re-rooting by all the honest stake makes copies for 6.5–7.5 % of the occupied slots at
      α = 0.2, and for 13–15 % at α = 0.3. Each costs a proving run and a Blend message (§3.2).
    - The coalition's share of the canonical blocks moves by at most 0.7 pp under every rule
      but route C, and no such gap is resolved. Route C lowers it from 0.383 to 0.365 at
      ρ ≈ 0.56, α = 0.3 and U = 4 (−0.0177 ± 0.0042, resolved). At α = 0.3 the share is
      0.34–0.40 in every arm, so the attack pays under every rule.
  - The revenue-optimal policy of the MDP (γ = 0, lead cap 64, p_ref = 1; the depth-1 values
    are the report's §6.6 values):

    | α | η, depth 1 | η, depth 2 | D̂/D*, depth 1 | D̂/D*, depth 2 | D̂/D*, every block | attacker's η, depth 1 | attacker's η, depth 2 |
    |---|---|---|---|---|---|---|---|
    | 0.34 | 0.585 | 0.753 | 0.856 | 0.884 | 0.926 | 0.774 | 0.947 |
    | 0.40 | 0.441 | 0.588 | 0.811 | 0.846 | 0.945 | 0.750 | 0.926 |
    | 0.46 | 0.105 | 0.210 | 0.619 | 0.658 | 0.955 | 0.476 | 0.747 |

    - Depth 2 closes 40 %, 26 % and 12 % of the gap in D̂/D* between depth 1 and counting
      every block. The optimal policy waits longer as α grows, so its discarded chains outgrow
      two blocks.
    - For the depth-maximising adversary of the report's §6.10, η rises from 0.52 to 0.72 at
      α = 0.3 with an honest fork rate of 0.35, and from 0.67 to 0.87 without honest forks.
  - Withholding (U = 4): D̂/D sits on the active-stake line 1 − α in every arm, at
    0.7963–0.8024 for α = 0.2 and 0.5957–0.5996 for α = 0.4. The deeper rules and re-rooting
    add at most +0.0050 ± 0.0014, at ρ ≈ 0.56, from the honest forks of the raised load. The
    coalition publishes nothing, so no rule counts its wins.
  - Route A, one block of spent-note eligibility (L = 1):
    - A note spent in block `X` is unspent in the state of `X`'s parent. Under `L = 1` a block
      whose parent is `X` proves against that state, so the note can still win `X`'s
      children. Under 1.2.5 it can win only forks off `X`'s parent.
    - Under the spec rule the mean gap between consecutive canonical blocks is 40, 45, 52 and
      67 slots at ρ ≈ 0.36, 0.56, 0.96 and 1.76 (the Phase 2 run, k = 2160, U = 4;
      `scripts/adversary_analysis.py growth`). A note holding a share `w/D` of the stake wins a
      slot with probability about `f·w/D`, so it wins about 1.3–2.2·`w/D` slots in that gap.
      Spending the whole stake once in an epoch adds one or two such wins, against about
      21 600 wins in an epoch.
    - Such a win can be a chain block, so it carries a leader voucher for whoever holds the key
      (`bedrock-anonymous-leaders-reward.md:61–72`).
    - An entry proves against the state of its parent's parent. A spent note's entries
      therefore count for under `W·f⁻¹` slots after the spend block, instead of after its
      parent.
  - Route C, spent stake and the epoch schedule:
    - The stake snapshot must be `k` blocks deep after the `s = 3⌊k/f⌋` slots of its phase
      (`cryptarchia-v1-protocol.md:112`, `:150`). Route C counts the wins of spent notes, but
      only unspent notes make chain blocks. The chain therefore grows more slowly as σ grows.
      Once every block carries `U` counted entries, the controller holds the counted slots at
      `f` per slot, and the chain grows by `f / (1 + U)` per slot.
    - Measured on the Phase 2c run (k = 2160, U = 4; `scripts/route_c_analysis.py spent`):

      | ρ | σ | chain growth / f | blocks in the snapshot phase / k |
      |---|---|---|---|
      | 0.36 | 0 | 0.756 | 2.27 |
      | 0.36 | 0.25 | 0.605 | 1.81 |
      | 0.36 | 0.5 | 0.434 | 1.30 |
      | 0.36 | 0.75 | 0.254 | 0.76 |
      | 0.96 | 0 | 0.572 | 1.72 |
      | 0.96 | 0.25 | 0.476 | 1.43 |
      | 0.96 | 0.5 | 0.360 | 1.08 |
      | 0.96 | 0.75 | 0.232 | 0.69 |

    - At σ = 0.75 the snapshot phase holds 0.69–0.76 `k` blocks, so the snapshot is not final
      when the buffer phase starts (`:151`). At U = 1 the chain sits on its floor of 0.5 f from
      σ = 0.5, and at U = 2 on its floor of f/3 at σ = 0.75. At `MAX_UNCLES` = 4 the floor is
      0.2 f, which leaves the phase 0.6 `k` blocks.
    - Whoever holds the keys of spent snapshot notes holds σ. A spent note's key is worth
      nothing to its owner, so an adversary can collect such keys cheaply. The snapshot of
      epoch `ep` is the note set at the start of epoch `ep − 1` (`:220`). So σ is the share of
      that set spent within up to two epochs whose keys one party holds. No rule bounds it.
    - The adversary's own stake adds to σ. Under 1.2.5 a coalition can already hold D̂ at its
      stake while it adds no chain block. It publishes each win as a block whose parent lies
      behind the tip, and honest blocks reference that block as an uncle (`:325–331`). This
      costs it its block rewards (`:386`). Under route C a spent note costs nothing, and a
      coalition can sell its stake after the snapshot and keep its keys.
  - Route F, withholding `U`:
    - The adversary can withhold the body of a cousin parent `U` it produced. A validator that
      lacks `U` waits for an honest holder (Phase 2d). An honest proposer that carried `C`
      validated it against the state after `U`, so it holds `U` and serves it
      (`block_provider.rs:136`).
    - Withholding `U` therefore delays a block the adversary proposes itself, or one whose
      honest proposer received `U` while most nodes did not. The first is a late release of
      the adversary's own block, which the selfish model covers. The second slows an honest
      block: each validator fetches `U` and executes it before it can validate `A`.
    - Each such cousin costs the adversary two wins, `U` and `C`. Validating one block then
      takes up to `1 + MAX_UNCLES` executions, each of a body of up to `MAX_BLOCK_SIZE`
      (`:103`). One cousin parent per block, or cousin parents counted in the `MAX_BLOCK_SIZE`
      of `A`, keeps it near one.
  - The self-signed caveat (`:331`) at every depth:
    - Every rule counts per slot, and every entry stands for a genuine win at its slot. So a
      late or repeated entry adds no slot beyond the wins, at any depth.
    - Re-rooting uses the caveat on purpose: the leader self-signs a header at its slot with
      the fork point as parent.
    - An entry can stand for a win its leader never published. It then counts a slot the
      leader withheld. Under route C it can stand for a spent note's win, which is the exposure
      above.
  - Uncle rewards, if ever added:
    - The farming bound `w_u + w_n < 1` of the report's §6.7(a) holds per slot at every depth.
      A self-orphaned branch of two blocks, counted as an uncle and a cousin, pays
      `2(w_u + w_n)` for two wins, against 2 as chain blocks.
    - A deeper rule pays an attacker for more of a failed private chain. In the MDP the
      attacker's recoverable share rises from 0.750 to 0.926 at α = 0.4. That lowers the cost
      of a failed attempt and widens the backfire of the report's §6.7(3).
    - Re-rooting does the same at depth 1 today: a coalition can re-root every block of its
      own abandoned chain.
  - What the report's §6.4 and §6.6 assume:
    - §6.4's coalition publishes nothing, so no rule can count it. The sweep keeps D̂/D on
      1 − α in every arm.
    - §6.6 and §6.8 read the first-fork ceiling as a property of the counting rule: an
      override discards a chain, and the rule counts one block of it. Under 1.2.5 every honest
      block of that chain can count, by re-rooting. The ceiling holds only while leaders do not
      re-root (§7).
- **Phase 5 — cost.**
  - Node changes: a referenced-entry index in `verify_uncles_ancestry`; a deeper entry
    verified against the state of the fork point.
  - The prover proves against the lagged root.
  - Whether the lag takes proving off the critical path (unmeasured).
  - Re-rooting: leader-side logic only. It detects the orphaning, proves again, and publishes
    under core or proof-of-work quota.
  - Route F: the stored-block format; downloading a cousin's parent; validating `U` against
    the state of `G` on a node that did not accept `U`; `uncle.rs` reading the state of `U`
    where it now panics (`:131–134`).
- **Phase 6 — decision.**
  - Depth 2 goes to an RFC only if the PoL owners accept `L = 1` and its gain clears the
    ±0.9 % per-epoch noise at the ρ projected for production (§3.7).
    - Phase 4: against an SM1 coalition of 0.2–0.3 at ρ ≈ 0.36–0.56 it gains 4.5–5.5 pp. The
      gate as written reads the honest gain only (§6, question 7).
  - Re-rooting changes no rule. It is proposed as leader behaviour next to Uncle Selection if
    its gain clears the same noise at the production ρ. Phase 2b: by all the stake within
    10 slots it clears the noise wherever depth 2 does on the overload grid, at ρ ≈ 0.96 and
    1.76 with U ≥ 2. Half the stake gains 0.63–0.71 pp at ρ ≈ 0.96, under the noise, and
    1.4–2.2 pp at ρ ≈ 1.76.
    - Phase 4: against the same coalition, re-rooting by all the honest stake gains 4.6–6.1 pp,
      and by half of it 2.6–3.2 pp.
  - Route C goes to an RFC only if the PoL owners accept the unchecked root, Phase 4 bounds the
    spent stake, and Phase 2c shows a gain over re-rooting that clears the same noise.
    - Phase 2c: over re-rooting by all the stake within 10 slots, the gain clears the noise at
      ρ ≈ 1.76 with U ≥ 2 (+0.0124 at U = 4) and at ρ ≈ 0.96 only with U = 1. At ρ ≤ 0.56 it is
      at most +0.0031.
    - Phase 2c: wherever the cap carries their wins, spent notes holding a share σ of a snapshot
      cut the block rate to (1 − σ)f, up to σ = 0.5 at U = 4.
    - Phase 4: nothing bounds the spent stake, so the condition is not met. At σ = 0.75 and
      U = 4 the snapshot phase holds 0.69–0.76 `k` blocks.
    - Phase 4: against an SM1 coalition route C gains 7.1–15.2 pp over depth 1, and 2.5–9.1 pp
      over re-rooting by all the honest stake.
  - Route F needs no PoL change. It goes to an RFC only if depth 2 clears the same noise at the
    production ρ, and re-rooting leaves a share of that gain which clears it too.
    - Phase 2b: all the stake within 10 slots leaves no share resolved. Half the stake leaves
      0.53–0.58 pp at ρ ≈ 0.96 and 1.6–2.5 pp at ρ ≈ 1.76. A 60-slot delay leaves 0.9–1.1 pp
      at ρ ≈ 1.76. The case for route F therefore rests on §6, question 6.
    - Phase 2d: a validator waits for `U` only when the leader of `A` produced it, in 6 of
      4 345 epochs.
  - Depth 3 needed its gain over depth 2 to clear that noise. It did not (Phase 2).
  - A depth that fails is recorded in the report as an overload contingency (§8.3).

## 6. Open questions

1. Is a one-block lag of `ledger_LATEST` (`L = 1`) acceptable to the PoL owners? This blocks
   route A from Phase 3 on. Re-rooting (Phase 2b) does not depend on it.
2. What ρ does production expect (Blend budget, N, peering degree)? Depth 2 gains under
   0.4 pp up to ρ ≈ 0.56. At U ≥ 2 it passes the ±0.9 % per-epoch noise from ρ ≈ 0.9
   (Phase 2). Re-rooting by all the stake recovers the same gain (Phase 2b).
3. ~~Should the simulator defaults move to the spec 1.2.5 rule?~~ Decided 2026-10-19: not on
   this branch. Its configs set the spec rule explicitly. Moving the defaults is a separate
   task, done together with re-pinning the report to 1.2.5 (§7).
4. Would the PoL owners accept an unchecked `ledger_LATEST` for references (route C)? A
   spent snapshot note would then count for up to two epochs after the spend. In Phase 2c a
   spent share σ counts as active stake at U = 4 up to σ = 0.5, and the block rate falls to
   (1 − σ)f. In Phase 4 nothing bounds σ, and at σ = 0.75 the stake snapshot phase holds
   fewer than `k` blocks.
5. Route F puts a cousin's inputs in the stored block but not in the proposal. A validator that
   lacks `U` waits for it, as one that lacks a transaction does. Would the Block Construction
   owners accept that? Cryptarchia 1.2.0 made uncle availability structural
   (`cryptarchia-v1-protocol.md:392`); route F gives that up for cousins on the proposal path.
   In Phase 2d a node waited in 6 of 4 345 epochs, at most 13.95 slots, each time for a `U`
   that the leader of `A` produced.
6. How much of the stake would re-root, and how soon after detecting the orphaning? Uncles earn
   nothing (`cryptarchia-v1-protocol.md:380`, `:386`), so re-rooting is node behaviour without
   an incentive. Its gain scales with the share that re-roots, and a 60-slot delay costs a
   quarter of it at ρ ≈ 1.76 (Phase 2b). The answer decides between re-rooting alone and
   route F.
7. Should the Phase 6 gate count the gain against a selfish coalition? Against SM1 at
   α = 0.2–0.3 and ρ ≈ 0.36–0.56, depth 2 gains 4.5–5.5 pp and re-rooting by all the honest
   stake 4.6–6.1 pp (Phase 4). Their honest gain there is under 0.4 pp (Phases 2 and 2b).

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
- **The report, §6.6–§6.8:** the first-fork ceiling is read as a property of the counting rule,
  and the honest blocks behind the first of an override as unreachable by any valid block.
  Under 1.2.5 the leader of each can re-root it (`cryptarchia-v1-protocol.md:325–331`), and a
  coalition can re-root its own abandoned chain. The attacker's own ceiling, 0.750 at α = 0.4
  in §6.6, is then 1 in the MDP, which has no window.
- **The report, §6.3–§6.5:** no study covers a coalition that publishes its wins as uncles. It
  holds D̂ at its stake while only honest blocks extend the chain, at the cost of its block
  rewards (Phase 4).
- **Configs:** `configs/reorg-depth.yaml` sets `adversary_strategy: private_chain`, which
  `SimConfig` rejects.
- **Lint:** an unused `dataclasses` import in `tests/test_multi_coalition.py`, and an unused
  `numpy` import in `scripts/w_pairing_analysis.py`.
- **Cryptarchia, the note at `:390`:** it argues that a candidate within the window is still in
  the block tree because the latest immutable block is "at most `s` slots back". The claim
  needs a lower bound on that distance instead. `k` blocks occupy at least `k` slots, so it
  holds always when `W·f⁻¹ ≤ k`, that is `W ≤ k·f` = 72. Up to the virtual bound `⌊0.6k⌋` =
  1 296 (38 880 slots) it holds only while `k` blocks take longer than the window: likely, not
  certain.
- **Node, mempool settings:** `pow_claim_grace_slots` (default 0,
  `nodes/node/binary/src/config/mempool/serde.rs:22`) is never read. The pool uses twice the
  acceptance window (`powclaim.rs:30–31`).
- **Analysis grouping:** fixed on this branch (Phase 0).
