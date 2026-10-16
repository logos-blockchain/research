# Mantle with private notes and programs (Lean 4 + Mathlib)

A machine-checked model of Mantle 2.1.0 as specified by [logos-lips#480](https://github.com/logos-co/logos-lips/pull/480) (RFC-480, *Private UTXO ledger*) and [logos-lips#481](https://github.com/logos-co/logos-lips/pull/481) (RFC-481, *Programs governing channel notes*, stacked on #480), at `tl/program_notes` 9e14358.

- **Status:** no `sorry`s, no warnings, only the standard axioms (`propext`, `Classical.choice`, `Quot.sound`).
- **Check** (from `formal/`): `lake build Mantle`; `lake env lean MantleTest/Axioms.lean` prints the axioms of the main results; `lake env lean MantleTest/Vectors.lean` checks the encoder and BLAKE2b against every test vector of Mantle.

## The model

- **Assumptions are hypotheses, never axioms**, each stated only by the theorems that use it (table below). Field elements are naturals.
- **The circuits are transcribed** (`Circuits.lean`): the ZkTransfer derives its input and output commitments with `program = data = 0`, the ZkProgramSpend with the program's identifier for its inputs and for its flagged outputs, and `0` for the others.
- **The ledger is transcribed** (`Ledger.lean`): every Operation's validation and execution, the inscription steps (user steps, payments, program spends, openings), `mandatory_fees`, `release_withdrawals` and SDP Epoch Finalization. A failed `assert` is `none`. Classical hashes, Ed25519, encodings and the Blend activity rule are abstract functions (`Prims`), about which nothing is assumed.
- **Value** (`Supply.lean`, `Conservation.lean`): a commitment opens to at most one note, so `cmValue` and the nullifier its holder derives (`cmNf`) are functions of the hash. The value of a note set is the total value of its *distinct* unspent commitments; the value of a state adds the notes withdrawn SDP declarations will release and the proof of work pool.
- **Capacity** (`Cap`): theorems that use Merkle membership assume every note set holds fewer than `2^31` commitments, so the trees a proof refers to stay within depth `32`.

## Assumptions

| Hypothesis | Meaning | Used by |
|---|---|---|
| `Hash` (fields `injective`, `ne_zero`) | the ZK hash is idealized as collision free and never `0` (the symbolic model of a collision-resistant hash; satisfiable, `Hash.model`, on the naturals, not on `𝔽_p`) | every theorem that binds a commitment, a nullifier, a key or a Merkle root |
| `Prims.ZkTransferSound` | knowledge soundness of the ZkTransfer: a verified proof has a witness of the circuit | conservation (`applyTx_value`, `executeChain_total`), step validation, program guarantees |
| `Prims.ZkProgramSpendSound` | knowledge soundness of the ZkProgramSpend | conservation, step validation, program guarantees |
| `Prims.ProofBinding` | a proof verifies for at most one statement | only `payment_proof_bound`, `step_proof_not_payment`, `spend_proof_bound` |
| `Cap` | every note set holds fewer than `2^31` commitments | theorems using Merkle membership in a state |

The three proof hypotheses hold together, with verifiers accepting every true statement (`Prims.symbolic`, `symbolic_complete`), so no theorem assuming them is vacuous. Nothing is assumed about Groth16 program proofs, Ed25519, the classical hashes, the encodings in the ledger model, or the gas prices (`0` is allowed, though the base fee never goes below `1`). No assumption at all is used by the MMR, IMT, root-window, Merkle-completeness, lottery, codec and gas results, nor by the token economics outside `Supply.lean`.

## Results

| Specification | Lean | Statement |
|---|---|---|
| Mantle, *Commitment MMR*: "the root of the depth-32 Merkle tree whose leaves are the commitments" | **`mmrRoot_mmrPeaks`** | `mmr_append` and `mmr_root` compute the depth-32 root of the commitments padded with `0`, for fewer than `2^32` of them |
| Merkle paths, leaf level up, selectors = index bits | `rootFromPath_pathOf`, **`rootFromPath_eq_subtree`**, `mem_of_mmrRoot` | every leaf has a path; a path proves exactly the leaf at the index its selectors spell |
| *Nullifier IMT*: sorted linked list, non-membership criterion | **`inv_insertNullifier`**, **`not_mem_iff`**, `not_mem_of_path` | `insert_nullifier` keeps the sorted list of exactly the inserted nullifiers; `nf ∉ S` iff a leaf `low` has `low.nf < nf < low.next_nf` or `low.next_nf = 0`; the circuit form is sound because empty positions hold `0` |
| (new) the ledger never inserts a duplicate into an IMT | `SetInv.imt`, `Fresh` | every nullifier inserted is fresh and non-zero, which `insert_nullifier` assumes silently |
| `record_cm_root`: the last 1024 roots, a repeated root kept | **`windowInv_recordCmRoot`** | the dictionary holds exactly the roots of `recent_cm_root_blocks`, at most 1024, each with the peaks of a prefix of the commitments |
| `tx_cm_root` with `buffered` | `mem_of_txCmRoot`, **`txCmRoot_of_prefix`** | a proven commitment is in the set or the covered buffer; the root depends on the first `buffered` commitments only |
| Block Construction: a note cannot be consumed by a later transaction of its block | `not_provable_of_fresh` | a commitment newer than every recorded root and absent from the buffer has no path |
| What enforces what: **no value is created** | **`applyTx_value`**, `applyOp_spec` | from a well-formed state, a valid Mantle Transaction leaves a well-formed state whose value plus the mandatory fee and the tip is at most the value before |
| | `ZkTransfer.consumed`, `validateSteps_spec`, `supply_spend_append_le` | the pieces: a ZkTransfer consumes distinct unspent notes of its set worth its outputs plus its excess; the steps of an inscription balance exactly, payments into the program spend |
| Block Execution: withdrawals, SDP finalization, roots | `releaseWithdrawals_value`, `finalizeDeclarations_value`, `recordCmRoots_value` | none creates value |
| RFC-480 §2: two steps cannot consume the same note | `validateSteps_nodup` | |
| RFC-480 §2, mini-blocks: steps proven against the same root "hold at any position" and are "ordered freely among themselves" | **`validateSteps_users_iff`**, **`validateSteps_users_perm`** | user steps covering at most the buffer they start from validate together iff each validates alone and no two share a note; so any reordering validates |
| `CHANNEL_WITHDRAW`: forced exit, cancelled by a step, no fee | `releaseOne_not_due`, **`releaseOne_cancelled`**, `releaseOne_applied`, `not_spendable_of_mem`, `applyChannelWithdraw_fee` | |
| RFC-480 §3: the eligible root; "both checks name the same set" | `pathIndex_eq_of_selectors`, **`pol_sound`**, `pol_sound_of_inv` | a Proof of Leadership proves a note of some set `i` in the aged snapshot whose nullifier is unspent in set `i` in the latest snapshot |
| RFC-481: program notes do not lead | `pol_user_note`, `pol_not_program_note` | |
| RFC-481, what enforces what: a program note moves only with its program's proof | `ZkTransfer.not_program_input`, `ZkTransfer.not_program_output`, **`program_note_created`**, **`program_note_consumed`** | a ZkTransfer never touches a program note; a note of program `P` is created or consumed only by a program step of `P` whose program proof verified under `P`'s registered key |
| RFC-481: the opening of every program note is published | `validateSteps_program_outputs` | every created program note has its checked opening |
| RFC-481: a payment pays only its program, for its intent | **`payment_proof_bound`**, `step_proof_not_payment`, `paymentMsg_inj`, `spend_proof_bound` | |
| Gas tables of RFC-480/481, Execution Gas limit | `transfer_gas_eq`, `program_proof_gas_eq`, `program_register_gas_eq`, **`limit_eq`**, `transfers_per_block` | every constant from its measured cycles; `G_max = 3,192,483`, `G_target = 1,596,241`; 5,157 transfers per block |
| Channels | `roundRobin_lt`, `multiSigOk_nodup`, `createChannel_null`, `validateInscribe_no_set` | |
| PoL, *Lottery Approximation*: `φ_f(α) = 1-(1-f)^α` approximated by `α(c - c²α/2)` | **`approx2_le_phi`**, **`phi_sub_approx2_le`**, `phi_le_approx1`, `phi_add` | the order-2 threshold never exceeds `φ`, with error at most `c³α³/6`; the order-1 one always exceeds it; splitting a stake leaves `φ` unchanged |
| PoL constants `t0_constant`, `t1_constant` | **`constants_exact`** | the hexadecimal constants are exactly `⌊-p ln(29/30)⌋` and `⌊p ln²(29/30)/2⌋` (53-term log series, checked by the kernel) |
| PoL threshold in `𝔽_p` | **`win_prob_le`**, `threshold_no_wrap`, `threshold_wrap` | with a uniform ticket, a note wins with probability at most `φ_f(v/S) + 2v²/p`; past the zero crossing the threshold wraps near `p` (the corner case) |
| (new) stake splitting under the approximation | **`split_advantage`** | two notes of stakes `a, b` win more often than one of stake `a + b`, by `c³ab(a+b)/2 - c⁴a²b²/4 > 0` |
| Mantle Transaction Encoding, "guarantee a canonical encoding" | **`signedTx_canonical`**, `signedTx_encode_injective`, `mantleTx_encode_injective`, `Codec.decodeAll_iff` | every production is a verified codec (`Codec.lean`): a byte string decodes to a signed transaction iff it is its encoding; distinct transactions have distinct encodings |
| Mantle *Test Vectors* | `MantleTest/Vectors.lean` | the 10 `op_id` vectors, the 2 transaction hashes and the `declaration_id` decode, re-encode to themselves, and match BLAKE2b-256 (`Blake2b.lean`, checked against RFC 7693); `mantleTxHash` gives their reduction modulo `p` |
| SDP Epoch Finalization: "ascending lexicographic order of the 32 bytes of `declare_id`" | `releaseOrder`, `declIdLe` | the due declarations are released in the byte order of their ids, first byte first (`Vectors.lean` checks `00…01` before `01…00`) |

## Differences from the specification

1. **`round_robin` divides by zero.** A new channel has `posting_timeframe = 0` ("infinity") and `posting_timeout = 0`, so the `else` branch computes `tip_sequencer_duration // channel.posting_timeframe`. Execution step 3 of `CHANNEL_INSCRIBE` calls `round_robin` on every inscription, the one creating the channel included, so in Python every inscription to a channel whose `posting_timeframe` is `0` raises `ZeroDivisionError`. Lean's `n / 0 = 0` gives the intended meaning, no rotation; the pseudocode should special-case `0`.
2. **`mandatory_fees` sees the final state.** Validation calls `mandatory_fees(signed_tx, ledger, channels, ...)` after every Operation has executed, so `execution_gas(op, ledger, channels)` reads the state after the transaction, while its comment and `CHANNEL_CONFIG` ("`0` for a channel that does not exist yet") require the state each Operation is validated against: a configuration creating a channel would be charged `59 × threshold` instead of `0`. The model follows the text (`executionGas` per Operation, in `applyOps`).
3. **A note set holds `2^32 - 1` commitments, and can fill.** With exactly `2^32`, `mmr_root` ends at height 33 (`mmrRoot_full`), a root no depth-32 path matches. At the Execution Gas limit a block can append `5,157 × 8 = 41,256` commitments to one set, which fills it in about 104,000 blocks, 36 days of full blocks (`blocks_to_fill_set`; the 2 MiB block size, not modelled, may bind first, at the same order of magnitude). The specification does not say what happens to a full set.
4. **The lottery's error table is computed for `f = 1/20`.** The text says `f = 1/30`, and the constants are those of `1/30` (`constants_exact`), but at a stake equal to the inferred total stake the order-1 and order-2 errors are `1.70%` and `-0.019%` for `1/30` (`error_table_f30`), and the table's `2.59%` and `-0.0444%` are those of `1/20` (`error_table_f20`); the other rows follow the same pattern.
5. **The order-2 threshold rewards splitting stake.** Unlike `φ`, the approximation gives two notes of stakes `a` and `b` a higher chance than one note of `a + b` (`split_advantage`). The effect is third order (`c³ab(a+b)/2` with `c ≈ 0.034`), negligible for realistic notes, but it is an incentive the specification does not mention.
6. **A `FieldElement` has up to 5 encodings.** It is any 32 bytes; the specification does not require the decoder to reject values `≥ p`, so `x` and `x + p` (for `x < 2^256 - p`) are both accepted (`fieldElement_not_canonical_mod_p`). The encoding is canonical as bytes (`signedTx_canonical`) but not modulo `p`: two encodings of the same field elements give different transaction hashes and `op_id`s, against the stated goal of a canonical encoding. Requiring `< p` fixes it.
7. **The threshold's zero crossing is at `v ≈ 59 S`**, `2/c = 58.99` (`parabola_peak_zero`, `constants_ratio`), where the corner-case section says 58; the peak, `≈ 29.5 S`, is as stated.
8. **Value can be lost, never created.** Any output whose fields equal those of an existing note shares its commitment and nullifier, and only one can be spent. RFC-480 states this for two leader rewards under one `reward_key`; it holds for every note, so conservation is an inequality.
9. **`mantle_txhash` is used both raw and reduced.** The prose requires reducing it modulo `p` before any ZK use (*Mantle Transaction*), but `mantle_txhash()` returns the raw digest, Validation passes it on unreduced, and the Operations type it `zkhash` and give it to `verify_transfer` directly; no step says where the reduction happens. The model's `Prims.txHash` is the value the proofs receive; `Encoding.mantleTxHash` is the specification's reduced value, checked on both transaction vectors.
10. **What Ed25519 signs is unstated.** `InscribeProof.signature` is "over the mantle_txhash": the 32-byte digest or the reduced field element give different signatures. Nothing is assumed about `ed25519Verify`, so the theorems hold either way.
11. **Gas amounts have no integer type.** *Arithmetic* requires every operation on gas amounts to be checked on "the stated integer type", but `tx_execution_gas` has none and its sums in `mandatory_fees` are unchecked; the product with the price is bounded only through the base fee's floor of `1` (Execution Market). The model's gas prices are any naturals, `0` included; no theorem needs the floor.
12. **Nothing is said to bound `TokenValue`.** "Token value is supposed to never exceed the precision of `TokenValue`" names no component that guarantees it, and the specification does not state the denomination of `TokenValue` against LGO, so whether the supply cap fits in `2^64` base units cannot be checked from it.
13. **Typo.** "`p ≈ 2^{-254}`" (`op_id`, *Operation Identifier*) should be `2^{254}`.

Confirmed as stated: the hexadecimal lottery constants, every test vector of Mantle, the integrity of the 1024-root window with repeated roots, the soundness of the IMT non-membership proof, the eligible root's set binding, the buffer semantics of `buffered`, the cancellation of withdrawals, and the RFC-481 "What enforces what" rows the ledger enforces.

## Not formalized

- Zero knowledge and privacy, Groth16 and BN254, Ed25519 unforgeability: the theorems rest on the soundness hypotheses above, and hold for every signature check.
- The ticket's uniformity (`win_prob_le` reads `threshold / p` as the winning probability), the entropy contribution, Cryptarchia and the Proof of Quota, the PoW difficulty and window maintenance, the Blend activity rule.
- The BLAKE2b implementation is tested (RFC 7693 and the specification's vectors), not proven; the 2 MiB block size and the 1024-transaction limit are not modelled.
- The row "a program step serves the intents over the assets of the zone", which the ledger does not check.

## Layout

| File | Contents |
|---|---|
| `Crypto.lean` | idealized hash, notes, commitments, nullifiers, keys, openings |
| `Merkle.lean` | Merkle trees and paths |
| `MMR.lean` | `mmr_append`, `mmr_root` and their correctness |
| `IMT.lean` | the nullifier IMT |
| `NoteSet.lean` | note sets, the root window, `tx_cm_root` |
| `Circuits.lean` | the ZkTransfer and ZkProgramSpend relations, Groth16 program proofs |
| `Gas.lean` | Execution Gas constants and limit |
| `Ledger.lean` | the state, every Operation, transactions, withdrawals, finalization |
| `Supply.lean`, `Conservation.lean` | the value of a note set and of a state, the invariant |
| `NoValueCreated.lean` | one theorem per Operation, `applyTx_value` |
| `Block.lean` | the block-level steps of Mantle |
| `Leadership.lean` | the eligible root and the Proof of Leadership |
| `Programs.lean` | the program guarantees |
| `Channels.lean` | steps, mini-blocks, withdrawals, sequencing |
| `Lottery.lean` | the leadership lottery: approximation bounds, constants, threshold in `𝔽_p` |
| `Codec.lean` | verified codecs and their combinators |
| `Encoding.lean` | Mantle Transaction Encoding |
| `Blake2b.lean` | BLAKE2b, for the test vectors |
