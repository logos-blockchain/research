# Proof-system transition with dual-key notes

**Subject:** what happens to notes, note identifiers, zero-knowledge identities and reward vouchers when the hand-written circuits move from Groth16 over BN254 to a STARK-based proof system over the Goldilocks field, given that every note already commits to a STARK-field public key ([logos-lips#442]).
**Question:** can the transition be a deterministic re-keying of public data, with no per-user migration and no foreign-field emulation in the new circuits, and what has to be retained for the one structure that cannot be re-keyed?
**Answer in one line:** yes for everything keyed by a note or a declaration, because the ledger already carries the STARK-field key of every owner; only the reward voucher tree cannot be re-keyed, and it is frozen as a legacy pool with a sunset instead.

> **Status.** Analysis, not a specification. The normative documents in
> `logos-lips` carry only the pre-transition change: the `stark_public_key` of
> every `Note`, the `stark_zk_id` of every declaration, the note identifier that
> binds both keys, and the wallet-side derivation and acceptance rule. This
> document collects what those choices imply for the transition, so that the
> specification of the transition can be written against it. Parameters named
> here (`TRANSITION_EPOCH`, `TRANSITION_NOTICE_EPOCHS`, `LEGACY_CLAIM_EPOCHS`,
> the `StarkProof` format, the full post-transition circuit statements) are
> deliberately left open.

---

## 1. Why a second key, and why now

Every zero-knowledge key in the protocol is a Poseidon2 digest over the BN254 scalar field: the `public_key` of a note, the `zk_id` of a service declaration, and the keys the ZkSignature, the Proof of Leadership and the Proof of Quota prove knowledge of. Groth16 over BN254 is not post-quantum, and the plan is to move the hand-written circuits to a STARK-based system, which proves natively over a small prime field. At the transition every key on the ledger would be foreign to the new proof system, and the choices would be to emulate the BN254 hash inside the STARK for every legacy key, forever, or to make every user rotate to a new key and move their funds.

Measurements taken during the design discussion rule out the two intermediate constructions:

| Construction | Cost | Why it fails |
|---|---|---|
| Derive the key with a Goldilocks hash inside today's Groth16 circuits | 5,622 ms and a 1.32 GB proving key for a 32-key ZkSignature, against 191 ms and 26 MB today; 100,634 constraints for the Proof of Leadership | roughly 40× on the critical path of every transaction, paid before the transition brings any benefit |
| Derive today's key as a BN254 hash of a STARK-field key (layered key) | cheap in Groth16 | only moves the emulation: the Proof of Leadership and the Proof of Quota cannot reveal the intermediate value without identifying the note, so after the transition they would have to prove the BN254 hash inside the STARK |

The adopted construction gives every note two keys, `public_key` (BN254) and `stark_public_key` (four Goldilocks elements), both derived by the wallet from the same leaf, and binds both into the note identifier. Nothing proves the link between them; the wallet checks the pair when it receives a note. Before the transition the second key costs one derivation and 32 bytes per note. At the transition the ledger already holds the new key of every owner, and what follows is a re-keying from public data.

## 2. What the specifications commit to today

- `Note = (value, public_key, stark_public_key)`; `LEADER_CLAIM` outputs and `SDP_DECLARE` carry the second key as well.
- `derive_note_id` absorbs the four Goldilocks elements of `stark_public_key` packed into two BN254 elements, so the identifier commits to both keys and the owner under either proof system is fixed when the note is created.
- Output validation and `SDP_DECLARE` validation reject a non-canonical Goldilocks element, so every key has one byte encoding.
- `stark_zk_id` is carried in `DeclarationMessage` / `DeclarationInfo`, bound by the ZkSignature over the payload and by a per-service uniqueness rule; it is not part of the `declaration_id` preimage.
- The wallet derives `sk_stark` from a BLAKE2b image of the leaf and `stark_public_key = starkhash(STARK_KDF_V1, sk_stark)`; a payment request carries both keys and a note is the wallet's only if both keys are its own.

Two properties of the pre-transition derivation matter later and are recorded here rather than in the specification:

- **Length separation under `NOTE_ID_V1`.** The extended preimage has seven elements, the previous one five. Poseidon2's 10* padding separates inputs of different lengths, so no identifier of the previous derivation can coincide with one of the extended derivation, and the tag did not need to change. A `NOTE_ID_V2` tag would be equally correct and costs one constant; the choice is hygiene, not security.
- **Circuit cost.** The two extra absorbed elements add two Poseidon2 permutations to every in-circuit derivation of a note identifier (Proof of Leadership, Proof of Quota). The ZkSignature does not derive note identifiers and is unchanged. The proving keys of the two circuits must be regenerated, which needs a new phase 2 of the trusted setup.

## 3. Transition point

The transition is fixed by a protocol parameter `TRANSITION_EPOCH`, an `EpochNumber`. Blocks of slots before the first slot of `TRANSITION_EPOCH` follow the pre-transition rules; blocks from that slot on follow the post-transition rules below. The parameter is announced at least `TRANSITION_NOTICE_EPOCHS` epochs in advance so that wallets and leaders can prepare. If the transition takes place before the network launches, the post-transition rules are simply the rules at genesis and the re-keying of §5 is empty.

## 4. Post-transition derivations

**Keys.** The owner of a note is its `stark_public_key`; the `public_key` field is dropped from notes, from the `LEADER_CLAIM` payload and from declarations (§6). The key derivation is the one wallets already perform; the `StarkSecretKey` is the four-element `sk_stark`.

**Encodings.** Integers and classical hash digests become Goldilocks elements without any reduction: `elements_u64(x)` is the pair `(x mod 2^32, floor(x / 2^32))`, and `elements_hash(h)` for a 32-byte digest is its eight 32-bit little-endian words in order. Every such element is below `2^32 < q`, so the encoding is canonical and injective, and unlike a reduction modulo `q` it loses no bits.

**Note identifier.** The same function derives the identifier of every note, whether re-keyed at the transition or created after it:

```python
def derive_note_id_v2(op_id: Hash, output_number: int, note: Note) -> NoteId:
    return starkhash(
        *dst_elements(b"STARK_NOTE_ID_V1"),  # 2 elements
        *elements_hash(op_id),               # 8 elements of 32 bits each
        *elements_u64(output_number),        # 2 elements
        *elements_u64(note.value),           # 2 elements
        *note.stark_public_key.elements(),   # 4 elements
    )
```

A post-transition `NoteId` is a four-element digest (32 bytes). `op_id` keeps its definition: it is a BLAKE2b digest of the operation and does not depend on the proof system.

**Merkle trees.** `starkhash_compress(a, b)`, for two four-element digests, is `starkhash(a_0, …, a_3, b_0, …, b_3)`: the same rule as the modified Poseidon2 compression (a plain hash of the two inputs, no feed-forward); the eight elements fill exactly one rate block, so it costs one permutation. Every tree over identifiers (`ledger_AGED`, `ledger_LATEST`, the core-node tree of the Proof of Quota) uses it as node function with four zero elements as the empty leaf; depths are unchanged.

**ZkSignature.** The statement keeps its shape with the STARK-field objects in place of the BN254 ones:

```python
class ZkSignaturePublic:
    stark_public_keys: list[StarkPublicKey]  # len = 32, padded with the key of the zero secret
    msg: list[GoldilocksElement]             # elements_hash(mantle_txhash), 8 elements

class ZkSignatureWitness:
    stark_secret_keys: list[StarkSecretKey]  # len = 32, four elements each

assert all(
    stark_public_keys[i] == starkhash(*dst_elements(b"STARK_KDF_V1"), *stark_secret_keys[i])
    for i in range(32)
)
```

**Other derivations.** The Proof of Leadership and Proof of Quota hashes that take the note secret key move to `starkhash` under `STARK_`-prefixed tags with `sk_stark` as the secret: the lottery ticket and the entropy contribution (`STARK_LEAD_V1`, `STARK_NONCE_CONTRIB_V1`), the selection randomness and the key nullifier (`STARK_SELECTION_RANDOMNESS_V1`, `STARK_KEY_NULLIFIER_V1`). The reward voucher commitment and nullifier of vouchers created after the transition move to `starkhash` under `STARK_`-prefixed tags as well. The Proof of Leadership statement is otherwise unchanged: the aged and latest roots a post-transition proof refers to are the re-keyed roots, so eligibility is unchanged across the transition. The Proof of Quota builds the core-node tree from the `stark_zk_id` of every declaration, ordered as 256-bit little-endian integers.

## 5. Re-keying at the transition

Before validating the first block of `TRANSITION_EPOCH`, every node applies the following transformation to its state. Every step is a deterministic function of the ledger, so two honest nodes obtain identical state and identical roots.

1. **Notes.** For every note in the ledger (unspent notes, channel notes and service notes alike), `new_id = derive_note_id_v2(op_id, output_number, value, stark_public_key)`, and the `public_key` field is removed. The derivation needs the `op_id` and `output_number` of every note; a node must keep them with the note, or reconstruct them from history, from the moment dual-key notes apply.
2. **Trees.** Every note tree that a post-transition proof may reference is re-keyed leaf-wise: `ledger_LATEST`, and every frozen `ledger_AGED` snapshot taken before the transition that a Proof of Leadership or Proof of Quota of `TRANSITION_EPOCH` or a later epoch refers to. Each leaf is replaced by the new identifier of the same note at the same index, and the root is recomputed with `starkhash_compress`. A node must retain the ordered leaf lists of those snapshots, not only their roots. Because the map is a bijection applied at fixed positions, membership is preserved: a note eligible in the aged snapshot stays eligible, and no note restarts ageing.
3. **References.** `channel_notes`, `service_notes`, the `service_note_id` of every declaration, and every other state keyed by or pointing at a `NoteId` are re-keyed by the same map.
4. **Declarations.** The `zk_id` field is dropped and `stark_zk_id` becomes the identity of the declaration: with declarations keyed by their zero-knowledge identity ([logos-lips#407]), `declarations` is re-keyed from `zk_id` to `stark_zk_id`, every index that maps a `service_note_id` or a `provider_id` to a `zk_id` now maps it to the `stark_zk_id` of the same declaration, and `SDP_ACTIVE` / `SDP_WITHDRAW` address the declaration by `stark_zk_id`. The core-node tree is rebuilt from the `stark_zk_id` values.
5. **Vouchers.** The reward voucher tree and the voucher nullifier set are not re-keyed: their leaves are commitments to secrets only the leaders know, so no node can recompute them. The pre-transition reward state is frozen instead. After the vouchers and the rewards of the last pre-transition epoch have been added, the node keeps the voucher root as `legacy_voucher_root`, the nullifier set as `legacy_voucher_nullifier_set` and the value of `leaders_rewards` as `legacy_leaders_rewards`; `leaders_rewards` restarts at zero, and vouchers created from the transition on go to a new `starkhash` tree with its own nullifier set. A legacy voucher is claimed with a `LEADER_CLAIM` whose Proof of Claim proves the pre-transition statement (one Poseidon2-over-BN254 Merkle path) inside the new proof system against `legacy_voucher_root`; the claim is checked against `legacy_voucher_nullifier_set` and paid from `legacy_leaders_rewards`, with the share formula of the Anonymous Leaders Reward Protocol applied to the legacy sets. Legacy claims are accepted until every legacy voucher is claimed (the number of legacy commitments equals the size of the legacy nullifier set) or until `LEGACY_CLAIM_EPOCHS` epochs have passed since the transition, whichever comes first. At that point the legacy circuit, the legacy sets and the legacy pool are dropped, and any remainder of `legacy_leaders_rewards` is added to `leaders_rewards`.

Why a separate pool: it keeps the share formula intact on each side, since neither pool's share depends on the other's unclaimed count, and the last legacy claim empties the legacy pool exactly. Why a sunset with a deadline: closing on "all claimed" alone would let a single lost voucher secret keep the legacy circuit and sets alive forever. Dropping the legacy nullifier set also resets that ever-growing structure once. The remainder rolls into the live pool rather than being burnt, so the reward supply is unchanged. The anonymity set of the last legacy claims shrinks as the pool empties, which any sunset shares; requiring leaders to claim before the transition would shrink it more, so early claiming is a recommendation, not a rule.

## 6. Wire layout after the transition

The productions below replace the ones of the same name in the Mantle Transaction Encoding; every other production is unchanged. The BN254 key disappears from the wire and a `NoteId` becomes a `starkhash` digest.

```schema
Note        = Value StarkPublicKey
NoteId      = StarkDigest
LeaderClaim = RewardsRoot VoucherNullifier StarkPublicKey
SDPDeclare  = ServiceType Locators ProviderId StarkZkId ServiceNoteId
SDPActive   = StarkZkId Nonce Metadata   ; the declaration is addressed by its STARK-field identity
SDPWithdraw = StarkZkId Nonce            ; shape follows [RFC] SDP Declarations Are Keyed by zk_id

StarkDigest       = 4GoldilocksElement   ; starkhash output, 32 bytes
ZkSignature       = StarkProof
ProofOfClaimProof = StarkProof
StarkProof        = UINT32 *BYTE         ; length-prefixed proof bytes; format to be specified
```

`RewardsRoot` and `VoucherNullifier` keep their 32-byte width; whether they are read as a BN254 field element (a claim against the legacy voucher tree) or as a `StarkDigest` follows the Proof of Claim variant.

## 7. Ownership, legacy proofs, wallets

**Ownership** follows `stark_public_key` uniformly. A note whose two keys were not set by the same party belongs, after the transition, to the holder of the STARK-field secret; the protocol neither detects nor special-cases such notes, and the wallet acceptance rule is the protection. For a correctly formed note no user action is required: the wallet that received it already holds `sk_stark`, and its note keeps its identifier's place in every tree.

**Legacy proofs.** From the first block of `TRANSITION_EPOCH` no Groth16 proof is accepted: not as a ZkSignature, a Proof of Leadership, a Proof of Quota or a Proof of Claim. Transactions in the mempool that carry such proofs are dropped and must be rebuilt by their wallets. The soundness of Groth16 rests on assumptions a quantum adversary breaks; the transition is the point at which the protocol stops relying on them, and accepting legacy proofs beyond it would reopen every note to forgery.

**Wallets** have nothing to migrate: their notes keep their place in the ledger under identifiers re-keyed by the nodes, and `sk_stark` is the witness the new proofs take. A wallet switches to the post-transition encoding and prover from the first block of `TRANSITION_EPOCH`, rebuilds any transaction still pending with pre-transition proofs, and should spend or otherwise deal with any note it holds under the BN254 key only (a note whose `stark_public_key` is not its own) before the transition, since that note is lost to it afterwards.

**Why the second key is not derived from the first.** `stark_public_key` could have been a hash of `k_logos`, but nothing could check that cheaply: the point of a second key is that the STARK-field hash never runs inside a Groth16 circuit, and a link that no circuit verifies is worth no more than two independent derivations. Deriving both from the leaf, through a BLAKE2b image for the STARK side so that the two keys share no input bytes, gives the same recoverability with no link to prove and no cross-exposure if one hash is later found weak.

## 8. Interaction with the one-time-keys standard

The wallet key hierarchy for one-time keys (follow-up to [logos-lips#437]) is written per leaf, so it applies unchanged: a fresh leaf is a fresh key pair, a payment request carries both keys, and recovery scans by index and derives both keys together. Two details follow from this document:

- recovery looks up a leaf by either of its public keys, `public_key` before the transition and `stark_public_key` after it, and a leaf whose BN254 key appeared on chain counts as used for the gap limit even if the note's STARK-field key was not the wallet's;
- the voucher master is a leaf with two field keys, `vm` (BN254) and `vm_stark`; one counter serves both, and recovery scans the legacy voucher set with the BN254 derivation and the live set with the STARK-field derivation.

## 9. Open items

- The Rescue-Prime Optimized instance (parameters, MDS, round constants, absorption rule) and `starkhash` test vectors; confirmed by research before any STARK-field value is fixed in a specification.
- `TRANSITION_EPOCH`, `TRANSITION_NOTICE_EPOCHS`, `LEGACY_CLAIM_EPOCHS`, the `StarkProof` format, and the full post-transition statements of the Proof of Leadership, Proof of Quota and Proof of Claim with their `STARK_`-prefixed tags.
- Whether `stark_zk_id` should also enter the `declaration_id` preimage while that identifier exists ([logos-lips#407] decides whether it survives).
- Retirement of the trusted setup ceremony at the transition, and the new phase 2 the extended Groth16 circuits need before it.

[logos-lips#442]: https://github.com/logos-co/logos-lips/pull/442
[logos-lips#437]: https://github.com/logos-co/logos-lips/pull/437
[logos-lips#407]: https://github.com/logos-co/logos-lips/pull/407
