# Mantle with private notes and programs (Lean 4 + Mathlib)

A machine-checked model of Mantle 2.1.0 as specified by [logos-lips#480](https://github.com/logos-co/logos-lips/pull/480) (RFC-480, *Private UTXO ledger*) and [logos-lips#481](https://github.com/logos-co/logos-lips/pull/481) (RFC-481, *Programs governing channel notes*, stacked on #480), at `tl/program_notes` 35e3c1c (RFC-480 v8, Mantle 2.0.0/2.1.0 as revised on 2026-10-19).

- **Status:** no `sorry`s, no warnings, only the standard axioms (`propext`, `Classical.choice`, `Quot.sound`).
- **Check** (from `formal/`): `lake build` builds the library and its tests: `MantleTest/Axioms.lean` fails the build if any declaration of `Mantle` uses a `sorry` or another axiom, and `MantleTest/Vectors.lean` checks the encoder and BLAKE2b against every test vector of Mantle.

## The model

- **Assumptions are hypotheses, never axioms**, each stated only by the theorems that use it (table below). Field elements are naturals.
- **The circuits are transcribed** (`Circuits.lean`): the ZkTransfer derives its input and output commitments with `program = data = 0`, the ZkProgramSpend with the program's identifier for its inputs and for its flagged outputs, and `0` for the others; every public key, of an active or an inactive input, is derived from its secret key.
- **The ledger is transcribed** (`Ledger.lean`): every Operation's validation and execution, the inscription steps (user steps, payments, program spends, openings), `mandatory_fees`, `release_withdrawals` and SDP Epoch Finalization. A failed `assert` is `none`. Classical hashes, Ed25519, encodings, `validate_multiaddr` and the Blend activity rule are abstract functions (`Prims`), about which nothing is assumed; `Prims.opId` stands for `op_id` reduced modulo `p`, as every use takes it.
- **Value** (`Supply.lean`, `Conservation.lean`): a commitment opens to at most one note, so `cmValue` and the nullifier its holder derives (`cmNf`) are functions of the hash. The value of a note set is the total value of its *distinct* unspent commitments; the value of a state adds the notes withdrawn SDP declarations will release and the proof of work pool.
- **Capacity** (`Cap`): theorems that use Merkle membership in a state assume every note set holds fewer than `2^31` commitments. This is a convenience of the proof, not a property of the specification: the invariant bounds the tree under `tx_cm_root` by twice the set, where in the specification it never exceeds the set. The results say nothing about sets of `2^31` to `2^32 - 1` commitments. `pol_sound_of_inv` needs only fewer than `2^32`.
- **Transaction hash**: `Prims.txHash` is the 32-byte `mantle_txhash` the Ed25519 signatures sign; the ZK proofs receive `toFr` of it, `mantle_txhash_fr`, and the proof of work ticket the block hash reduced the same way.
- **Initial state**: no Genesis state is built; the results hold for any valid Genesis. The invariants the proofs carry (`Inv`, `ChanInv`) are not assumed of it: `State.IsGenesis` states only what any valid Genesis visibly leaves (`Genesis.lean`): note sets that are empty sets to which commitments were appended and distinct non-zero nullifiers spent, their roots recorded; declarations with distinct ids, service notes in the SDP set, and nothing released; no pending channel withdrawal; and channels without note sets, each with a key, its tip sequencer one of them and a `uint16` threshold (the null channel). `Inv.of_genesis` and `ChanInv.of_genesis` derive the invariants, and `isGenesis_exists` shows the conditions satisfiable.

## Assumptions

| Hypothesis | Meaning | Used by |
|---|---|---|
| `Hash` (fields `injective`, `ne_zero`) | the ZK hash is idealized as collision free and never `0` (the symbolic model of a collision-resistant hash; satisfiable, `Hash.model`, on the naturals, not on `𝔽_p`) | every theorem that binds a commitment, a nullifier, a key or a Merkle root, including `mem_of_mmrRoot`, `mem_of_txCmRoot` and `not_mem_of_path` |
| `Prims.ZkTransferSound` | knowledge soundness of the ZkTransfer: a verified proof has a witness of the circuit | conservation (`applyTx_value`, `executeChain_total`), step validation, program guarantees |
| `Prims.ZkProgramSpendSound` | knowledge soundness of the ZkProgramSpend | conservation, step validation, program guarantees |
| `Prims.ProofBinding` | a proof verifies for at most one statement | only `payment_proof_bound`, `step_proof_not_payment`, `spend_proof_bound` |
| `Cap` | every note set holds fewer than `2^31` commitments | theorems using Merkle membership in a state |

The three proof hypotheses hold together, with verifiers accepting every true statement (`Prims.symbolic`, `symbolic_complete`), so no theorem assuming them is vacuous. Nothing is assumed about Groth16 program proofs, Ed25519, the classical hashes, the encodings in the ledger model, or the gas prices (`0` is allowed); `tx_balance` and `tx_execution_gas` are checked `uint64` sums, as *Arithmetic* and Validation require. No assumption at all is used by the MMR root computation (`mmrRoot_mmrPeaks`), the IMT invariant (`inv_insertNullifier`, `not_mem_iff`), the root window, Merkle completeness, the lottery, the codecs and the gas results, nor by the token economics outside `Supply.lean`.

## Results

| Specification | Lean | Statement |
|---|---|---|
| Mantle, *Commitment MMR*: "the root of the depth-32 Merkle tree whose leaves are the commitments" | **`mmrRoot_mmrPeaks`** | `mmr_append` and `mmr_root` compute the depth-32 root of the commitments padded with `0`, for fewer than `2^32` of them |
| Merkle paths, leaf level up, selectors = index bits | `rootFromPath_pathOf`, **`rootFromPath_eq_subtree`**, `mem_of_mmrRoot` | every leaf has a path; under `Hash`, a path proves exactly the leaf at the index its selectors spell |
| *Nullifier IMT*: sorted linked list, non-membership criterion | **`inv_insertNullifier`**, **`not_mem_iff`**, `not_mem_of_path` | `insert_nullifier` keeps the sorted list of exactly the inserted nullifiers; `nf ∉ S` iff a leaf `low` has `low.nf < nf < low.next_nf` or `low.next_nf = 0`; under `Hash`, the circuit form is sound because empty positions hold `0` |
| (new) the ledger never inserts a duplicate into an IMT | `SetInv.imt`, `Fresh` | every nullifier inserted is fresh and non-zero, which `insert_nullifier` assumes silently |
| `record_cm_root`: the last 1024 roots, a repeated root kept | **`windowInv_recordCmRoot`** | the dictionary holds exactly the roots of `recent_cm_root_blocks`, at most 1024, each with the peaks of a prefix of the commitments |
| `tx_cm_root` with `buffered` | `mem_of_txCmRoot`, **`txCmRoot_of_prefix`** | a proven commitment is in the set or the covered buffer; the root depends on the first `buffered` commitments only |
| Block Construction: "a note cannot be consumed by a later transaction of the block that creates it" | `not_provable_of_fresh`, **`fresh_not_provable_in_block`** (`TokenEconomics/Supply.lean`), `applyTx_keepsRoots` | the transactions and the steps before them keep the recorded roots, so at the start of a transaction a commitment its set did not hold when the previous block ended has no path under any `tx_cm_root` |
| What enforces what: **no value is created** | **`applyTx_value`**, `applyOp_spec` | from a well-formed state, a valid Mantle Transaction leaves a well-formed state whose value plus the mandatory fee and the tip is at most the value before |
| | `ZkTransfer.consumed`, `validateSteps_spec`, `supply_spend_append_le` | the pieces: a ZkTransfer consumes distinct unspent notes of its set worth its outputs plus its excess; the steps of an inscription balance exactly, payments into the program spend |
| Validation: `tx_balance = checked_uint64(...)` | `balance_check_holds` | the check never rejects a transaction of a state worth less than `2^64`: `fee + tx_balance` is at most the value of the state |
| Block Execution: withdrawals, SDP finalization, roots | `releaseWithdrawals_value`, `finalizeDeclarations_value`, `recordCmRoots_value` | none creates value |
| `SDP_DECLARE`, "verified according to [Declare]" | `applyDeclare` | the service type is `BN = 0`, every locator passes `validate_multiaddr`, and the `provider_id` and the `zk_id` are each unused in the service (the Mantle pseudocode omits these checks, see below) |
| RFC-480 §2: two steps cannot consume the same note | `validateSteps_nodup` | |
| RFC-480 §2, mini-blocks: steps proven against the same root "hold at any position" and are "ordered freely among themselves" | **`validateSteps_users_iff`**, **`validateSteps_users_perm`** | user steps covering at most the buffer they start from validate together iff each validates alone and no two share a note; so any reordering validates |
| `CHANNEL_WITHDRAW`: forced exit, cancelled by a step, no fee | `releaseOne_not_due`, **`releaseOne_cancelled`**, `releaseOne_applied`, `not_spendable_of_mem`, `applyChannelWithdraw_fee` | |
| RFC-480 §3: the eligible root; "both checks name the same set" | `pathIndex_eq_of_selectors`, **`pol_sound`**, `pol_sound_of_inv` | a Proof of Leadership proves a note of some set `i` in the aged snapshot whose nullifier is unspent in set `i` in the latest snapshot |
| RFC-481: program notes do not lead | `pol_user_note`, `pol_not_program_note` | |
| RFC-481, what enforces what: a program note moves only with its program's proof | `ZkTransfer.not_program_input`, `ZkTransfer.not_program_output`, **`program_note_created`**, **`program_note_consumed`** | per Operation and per inscription: a ZkTransfer never touches a program note, and a note of program `P` an inscription creates or consumes comes from a program step of `P` whose program proof verified under `P`'s registered key. No theorem composes these over a chain, through the withdrawals and SDP releases that add notes outside a step |
| RFC-481: every program step carries its program proof | **`validateSteps_program_proven`** | every program step of a valid inscription, whether or not it touches a note of its program |
| RFC-481: the opening of every program note is published | `validateSteps_program_outputs` | every created program note has its checked opening |
| RFC-481: a payment pays only its program, for its intent | **`payment_proof_bound`**, `step_proof_not_payment`, `paymentMsg_inj`, `spend_proof_bound` | the ZkProgramSpend, not the program proof, is shown bound to the `op_id` |
| Gas tables of RFC-480/481, Execution Gas limit | `transfer_gas_eq`, `program_proof_gas_eq`, `program_register_gas_eq`, **`limit_eq`**, `transfers_per_block` | every constant from its measured cycles; `G_max = 3,192,483`, `G_target = 1,596,241`; 5,157 transfers per block |
| `round_robin`: "an infinite timeframe never rotates: the tip sequencer keeps its turn" | **`roundRobin_infinite`**, `roundRobin_lt`, **`ChanInv.applyTx`**, `ChanInv.executeChain` | with `posting_timeframe = 0` and no timeout due, the sequencer and its starting slot are unchanged; every valid transaction and every block keep every channel with at least one key, its tip sequencer one of them and a `uint16` threshold (`ChanInv`), so the round robin always names an accredited key |
| Validation: `tx_execution_gas = checked_uint64(...)` | `applyOps_gas_lt`, **`gas_check_holds`**, `executionGas_le`, `mantleTx_ops_le` | the gas of a valid transaction is below `2^64`; from a state satisfying `ChanInv` (Genesis has no channel, `chanInv_of_none`), the check never rejects an encodable transaction: at most `255` Operations of at most `MAX_OP_GAS ≈ 1.05·10¹⁰` each (`GasBound.lean`) |
| Channels | `multiSigOk_nodup`, `createChannel_null`, `validateInscribe_no_set` | |
| PoL, *Lottery Approximation*: `φ_f(α) = 1-(1-f)^α` approximated by `α(c - c²α/2)` | **`approx2_le_phi`**, **`phi_sub_approx2_le`**, `phi_le_approx1`, `phi_add` | the order-2 approximation never exceeds `φ`, with error at most `c³α³/6`; the order-1 one always exceeds it; splitting a stake leaves `φ` unchanged |
| PoL constants `t0_constant`, `t1_constant` | **`constants_exact`** | the hexadecimal constants are exactly `⌊-p ln(29/30)⌋` and `⌊p ln²(29/30)/2⌋` (53-term log series, checked by the kernel) |
| PoL error table, `f = 1/30` | **`error_table_f30_all`**, `error_table_f30` | every row of the table, both errors to the digits shown: `1 - e^{-cα}` enclosed by its order-6 Taylor polynomial, `c` to ten decimals |
| PoL corner case: peak near `29`, zero crossing near `59` | `approx2_le_peak`, `parabola_peak_zero`, `constants_ratio` | `ψ` reaches its maximum `1/2` at `1/c ∈ (29.4, 29.6)` and returns to `0` at `2/c ∈ (58.9, 59.1)` |
| PoL threshold in `𝔽_p` | **`win_prob_le`**, `threshold_no_wrap`, `threshold_wrap` | below the zero crossing, with a uniform ticket, a note wins with probability at most `φ_f(v/S) + 2v²/p`; past it the threshold wraps near `p` and the note wins almost surely (the corner case) |
| PoL: "the order 2 expansion slightly rewards splitting stake … by `c³ab(a+b)/2 - c⁴a²b²/4`" | **`split_advantage`** | the identity, and the advantage is positive whenever `c b ≤ 1` |
| Mantle Transaction Encoding, "guarantee a canonical encoding" | **`signedTx_canonical`**, `signedTx_encode_injective`, `mantleTx_encode_injective`, `Codec.decodeAll_iff` | every production is a verified codec (`Codec.lean`): a byte string decodes to a signed transaction iff it is its encoding; distinct transactions have distinct encodings, so distinct `mantle_txhash` preimages |
| Encoding choice 4: "a `FieldElement` not less than `p` is rejected, so every field element has a single encoding" | **`fe_canonical_mod_p`**, `fe_rejects` | two byte strings decoding to the same element of `𝔽_p` are equal; `p` itself is rejected (`Vectors.lean` checks `p - 1` and `p` in a `TRANSFER`); a `ServiceType` other than `0` is rejected too |
| Mantle *Test Vectors* | `MantleTest/Vectors.lean` | the 10 `op_id` vectors and the 2 transaction hashes decode (every `FieldElement` in them is below `p`), re-encode to themselves, and match BLAKE2b-256 (`Blake2b.lean`, checked against RFC 7693); the `declaration_id` preimage, built from the decoded `SDP_DECLARE` vector (`declarationIdPreimage`), is the table's and hashes to its id; the transaction with one Operation of each kind, signed with a proof of every variant (step proofs, payment proofs, openings, a multisig), round-trips |
| SDP Epoch Finalization: "ascending lexicographic order of the 32 bytes of `declare_id`" | `releaseOrder`, `declIdLe` | the due declarations are released in the byte order of their ids, first byte first (`Vectors.lean` checks `00…01` before `01…00`) |

## Differences from the specification

Of the 13 differences reported against 9e14358, the revision of 2026-10-19 resolves 11 (`round_robin` with an infinite timeframe, per-Operation gas, the error table, splitting stake, the field element encoding, the zero crossing, the raw and reduced `mantle_txhash`, what Ed25519 signs, typed gas sums, the `TokenValue` denomination and bound, the typo). The model follows each resolution. Remaining, and found since:

1. **A note set holds `2^32 - 1` commitments, not `2^32`.** The *Commitment MMR* now states that a set "holds at most `2^32` commitments" and leaves a full set unspecified. With exactly `2^32`, `mmr_root` ends one level too high, at `zkhash(root_32, empty_root(32))` (`mmrRoot_full`). Under a collision-resistant hash this differs from the depth-32 root the paths are checked against, so appending the `2^32`-th commitment already breaks the set (no theorem proves the inequality: the idealized `Hash` alone does not exclude a fixed point). The gas-priced Operations of a full block can append `5,157 × 8 = 41,256` commitments to one set, which fills it in about 104,000 blocks, 36 days (`blocks_to_fill_set`).
2. **Value can be lost, never created.** Any output whose fields equal those of an existing note of the same set shares its commitment and nullifier, and only one of them can be spent in that set (each set has its own IMT). Block Construction states this for two leader rewards under one `reward_key`; it holds for every note, so conservation is an inequality.
3. **`SDP_DECLARE`'s pseudocode omits checks of the protocol it cites.** Its Validate block says the declaration "is verified according to [Declare]", which requires a defined `ServiceType`, valid locators (`validate_multiaddr`) and a `provider_id` and a `zk_id` each unique in the service ("The SDP must reject such declarations regardless"), but its four numbered steps check none of them. The model adds the three checks.
4. **`op_id` is not unique across Operations.** *Note Commitment and Nullifier* derives note nonces from `op_id` because "every Operation that output notes have a unique payload", but `derive_op_id` hashes the payload without its opcode, and payloads of different opcodes coincide: a 128-byte `SDP_DECLARE` payload is also a `CLAIM_POW_REWARD` payload, both deriving a note nonce from `op_id`, and a 352-byte `CHANNEL_DEPOSIT` payload a `PROGRAM_REGISTER` one (`Vectors.lean`). Hashing the opcode too fixes it (and changes the test vectors).
5. **RFC-480 and Mantle disagree on a channel being created.** RFC-480 §2 says "A channel being created carries no step"; Mantle validates the steps of the creating inscription against an empty set and applies them to the new set. The model follows Mantle.
6. **`MultiEd25519_verify` still types its message `zkhash`**, while every Ed25519 signature now signs the 32-byte `mantle_txhash` digest (*Mantle Transaction*) and every caller passes it. The model passes the digest.

Confirmed as stated: the hexadecimal lottery constants and the `f = 1/30` error table, the split advantage and the corner case's `29` and `59`, every test vector of Mantle, the single encoding of a field element, the integrity of the 1024-root window with repeated roots, the soundness of the IMT non-membership proof, the eligible root's set binding, the buffer semantics of `buffered`, the cancellation of withdrawals, the infinite posting timeframe, the checked gas and balance sums, and the RFC-481 "What enforces what" rows the ledger enforces.

## Not formalized

- Zero knowledge and privacy, Groth16 and BN254, Ed25519 unforgeability: the theorems rest on the soundness hypotheses above, and hold for every signature check.
- The ticket's uniformity (`win_prob_le` reads `threshold / p` as the winning probability), the entropy contribution, Cryptarchia and the Proof of Quota, the PoW difficulty and window maintenance, the Blend activity rule, `validate_multiaddr` (abstract).
- A particular Genesis state (the results hold for any valid Genesis, `State.IsGenesis`), and the composition of the per-inscription program guarantees over a chain.
- The BLAKE2b implementation is tested (RFC 7693 and the specification's vectors), not proven; the 2 MiB block size and the 1024-transaction limit are not modelled.
- The row "a program step serves the intents over the assets of the zone", which the ledger does not check.

## Layout

| File | Contents |
|---|---|
| `Crypto.lean` | idealized hash, notes, commitments, nullifiers, keys, openings, `toFr` |
| `Merkle.lean` | Merkle trees and paths |
| `MMR.lean` | `mmr_append`, `mmr_root` and their correctness |
| `IMT.lean` | the nullifier IMT |
| `NoteSet.lean` | note sets, the root window, `tx_cm_root` |
| `Circuits.lean` | the ZkTransfer and ZkProgramSpend relations, Groth16 program proofs |
| `Gas.lean` | Execution Gas constants and limit |
| `Ledger.lean` | the state, every Operation, transactions, withdrawals, finalization |
| `Supply.lean`, `Conservation.lean` | the value of a note set and of a state, the invariant |
| `NoValueCreated.lean` | one theorem per Operation, `applyTx_value`, `balance_check_holds`, `KeepsRoots` |
| `Block.lean` | the block-level steps of Mantle |
| `Genesis.lean` | what any valid Genesis leaves, and the invariants it satisfies |
| `Leadership.lean` | the eligible root and the Proof of Leadership |
| `Programs.lean` | the program guarantees |
| `Channels.lean` | steps, mini-blocks, withdrawals, sequencing, the channel invariant |
| `GasBound.lean` | the gas check against the encoding's bounds |
| `Lottery.lean` | the leadership lottery: approximation bounds, constants, error table, threshold in `𝔽_p` |
| `Codec.lean` | verified codecs and their combinators |
| `Encoding.lean` | Mantle Transaction Encoding, `declaration_id` |
| `Blake2b.lean` | BLAKE2b, for the test vectors |
