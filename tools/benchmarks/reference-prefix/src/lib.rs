//! Fixtures and harness code for the `REFERENCE_PREFIX_LENGTH` security-margin
//! study.
//!
//! Everything measured here runs the real `logos-blockchain` code, pinned by
//! commit in `Cargo.toml`. The transaction encoding, the transaction hash, the
//! Merkle block root and the block-reconstruction check are all called, never
//! reimplemented. What this crate supplies is the scaffolding: how to build a
//! smallest valid transaction, how to arrange a mempool that contains prefix
//! collisions, and how to drive the reconstruction search.
//!
//! Two things *are* reproduced rather than called, and both are called out
//! where they appear:
//!
//! 1. [`search_reconstruction`] reproduces the candidate-combination loop of
//!    `reconstruct_block_from_proposal`
//!    (`services/chain/chain-network/src/lib.rs`), because that function is a
//!    private `async fn` reachable only through a running service. The
//!    per-combination work it performs — `Block::reconstruct` — is the real
//!    function, and that is where essentially all of the time goes.
//! 2. [`AttackerHasher`] is a deliberately *faster-than-the-node* grinding
//!    loop, used to price the attacker generously. See its documentation.

use std::{sync::LazyLock, time::Duration};

use lb_codec::{BinaryDecode as _, BinaryEncode as _};
use lb_core::{
    block::{Block, BlockTransactions, Proposal},
    codec::{DeserializeOp as _, SerializeOp as _},
    crypto::{Digest as _, Hasher},
    header::Header,
    mantle::{
        Note, NoteId, Op, OpProof, SignedMantleTx, TxHash, Utxo,
        ledger::{Inputs, Outputs},
        ops::transfer::TransferOp,
        traits::Hashable as _,
        transactions::{mantle_tx::RawMantleTx, states::Preverified},
    },
    proofs::leader_proof::Groth16LeaderProof,
};
use lb_cryptarchia_engine::Slot;
use lb_key_management_system_keys::keys::{
    Ed25519Key, Ed25519Signature, ZkKey, ZkPublicKey, ZkSignature,
};

/// `COMPRESSED_PROOF_SIZE` — the compressed Groth16 proof inside a
/// `Groth16LeaderProof`.
const POL_PROOF_SIZE: usize = 128;

/// The concrete mempool transaction type used throughout the harness.
pub type Tx = SignedMantleTx<Preverified>;

/// Cryptarchia's default slot time — `DEFAULT_SLOT_TIME_IN_SECS` in
/// `tools/config/src/time.rs`, matching the `slot_duration` in
/// `nodes/node/standalone-deployment-config.yaml`.
///
/// This is the deadline reconstruction has to fit inside: a validator that
/// takes longer than one slot to turn a proposal back into a block has already
/// lost the slot.
pub const SLOT_DURATION: Duration = Duration::from_secs(1);

/// `MAX_BLOCK_TRANSACTIONS` in `core/src/block/mod.rs`, and therefore the
/// largest number of references a proposal can carry.
pub const MAX_BLOCK_TRANSACTIONS: usize = 1024;

/// `MAX_CANDIDATES_PER_REFERENCE` in `core/src/block/mod.rs`.
pub const MAX_CANDIDATES_PER_REFERENCE: usize = 8;

/// `MAX_RECONSTRUCTION_COMBINATIONS` in `core/src/block/mod.rs`.
pub const MAX_RECONSTRUCTION_COMBINATIONS: usize = 32;

/// The prefix lengths, in bytes, that the study prices.
pub const PREFIX_LENGTHS: [usize; 5] = [8, 10, 12, 14, 16];

// ---------------------------------------------------------------------------
// The candidate transaction
// ---------------------------------------------------------------------------

/// The secret key whose note the sample transaction spends. Fixed so that every
/// run on every machine grinds byte-identical transactions.
fn input_key() -> ZkKey {
    ZkKey::from(num_bigint::BigUint::from(1u8))
}

/// The UTXO the sample transaction consumes.
///
/// A `Transfer` must consume at least one note — `logos-blockchain` rejects
/// empty inputs in every note-consuming operation — so this is what makes the
/// transaction below the *smallest valid* one rather than merely the smallest.
///
/// The note id is cached because deriving it is a Poseidon2 hash, and it is the
/// *same* input note for every candidate. An adversary grinding candidates
/// derives it once; charging it per candidate would overstate their cost by
/// more than two orders of magnitude, which is the wrong direction for a
/// security margin.
static INPUT_NOTE_ID: LazyLock<NoteId> =
    LazyLock::new(|| Utxo::new([1u8; 32], 0, Note::new(1_000_000, input_key().to_public_key())).id());

/// The smallest valid `MantleTx`: a single `Transfer` operation, one input and
/// one output.
///
/// `nonce` varies the output note's value. That is the cheapest edit an
/// attacker can make that still leaves a valid, differently-hashing
/// transaction, so grinding over it is the attacker-favourable choice.
#[must_use]
pub fn minimal_transfer_tx(nonce: u64) -> RawMantleTx {
    RawMantleTx(
        [Op::Transfer(TransferOp::new(
            Inputs::new([*INPUT_NOTE_ID]),
            Outputs::new([Note::new(
                // Never zero: zero-valued outputs are rejected.
                nonce.wrapping_add(1),
                ZkPublicKey::zero(),
            )]),
        ))]
        .into(),
    )
}

/// `mantle_txhash(tx)` — the real hash, via `Hashable` on `RawMantleTx`.
///
/// This is `blake2b-256(b"MANTLE_TXHASH_V1" || encode(tx))`, and it covers the
/// `MantleTx` only, never the `op_proofs`. That is precisely why an attacker can
/// grind candidates offline without ever producing a signature or a proof.
#[must_use]
pub fn mantle_txhash(tx: &RawMantleTx) -> TxHash {
    tx.hash()
}

/// `prefix(mantle_txhash(tx), length)`, as the proposal would carry it.
#[must_use]
pub fn reference_prefix(tx: &RawMantleTx, length: usize) -> Vec<u8> {
    mantle_txhash(tx).0[..length].to_vec()
}

/// The encoded size, in bytes, of the sample transaction — reported alongside
/// every generation rate so a reviewer can scale the numbers to other sizes.
#[must_use]
pub fn sample_tx_encoded_len() -> usize {
    minimal_transfer_tx(0).encode().len()
}

/// The size of the full hash preimage, `b"MANTLE_TXHASH_V1" || encode(tx)`.
#[must_use]
pub fn sample_preimage_len() -> usize {
    minimal_transfer_tx(0).as_signing().len()
}

// ---------------------------------------------------------------------------
// Pricing the attacker generously
// ---------------------------------------------------------------------------

/// A grinding loop that is strictly faster than anything the node does, used so
/// that the attack is priced in the attacker's favour.
///
/// The node's own path — [`minimal_transfer_tx`] followed by [`mantle_txhash`] —
/// rebuilds the operation structure and reallocates the encoding buffer for
/// every candidate. An attacker has no reason to do either. Since the nonce
/// only varies a `u64` inside an otherwise fixed encoding, they can encode
/// once, then per candidate overwrite those bytes and hash the buffer.
///
/// The byte range to patch is *discovered* rather than hardcoded, by encoding
/// two transactions that differ only in the nonce and diffing them. If the
/// Mantle encoding ever changes shape this keeps working, or panics loudly; it
/// cannot silently grind the wrong bytes.
pub struct AttackerHasher {
    preimage: Vec<u8>,
    patch_offset: usize,
    patch_len: usize,
}

impl Default for AttackerHasher {
    fn default() -> Self {
        Self::new()
    }
}

impl AttackerHasher {
    /// # Panics
    ///
    /// If the nonce does not map to a single contiguous byte range in the
    /// encoding, which would mean the transaction layout has changed in a way
    /// this shortcut no longer models.
    #[must_use]
    pub fn new() -> Self {
        // The probes are chosen so that every byte of the varying field
        // differs: value 1 (0x01,0,0,0,0,0,0,0) against value u64::MAX
        // (0xFF x8). Probing with a small value instead would leave the high
        // bytes equal in both encodings and silently under-detect the field.
        let a = minimal_transfer_tx(0).as_signing();
        let b = minimal_transfer_tx(u64::MAX - 1).as_signing();
        assert_eq!(
            a.len(),
            b.len(),
            "nonce must not change the encoded length, or the shortcut is invalid"
        );

        let first = (0..a.len())
            .find(|&i| a[i] != b[i])
            .expect("the nonce must change the encoding");
        let last = (0..a.len())
            .rfind(|&i| a[i] != b[i])
            .expect("the nonce must change the encoding");
        let patch_len = last - first + 1;
        assert!(
            patch_len <= 8,
            "the nonce must occupy one contiguous u64 field; it spans {patch_len} bytes, \
             so the transaction layout has changed and this shortcut no longer models it"
        );

        Self {
            preimage: a,
            patch_offset: first,
            patch_len,
        }
    }

    /// Hash one candidate, reusing the buffer. Returns the full 32-byte hash;
    /// truncating it to `L` bytes is free and so is not modelled separately.
    #[must_use]
    pub fn hash_candidate(&mut self, nonce: u64) -> [u8; 32] {
        let value = nonce.wrapping_add(1).to_le_bytes();
        self.preimage[self.patch_offset..self.patch_offset + self.patch_len]
            .copy_from_slice(&value[..self.patch_len]);
        Hasher::digest(&self.preimage).into()
    }

    /// The preimage this hashes, for reporting.
    #[must_use]
    pub fn preimage_len(&self) -> usize {
        self.preimage.len()
    }

    /// Cross-check that the shortcut agrees with the real code path over a
    /// spread of nonces. Any divergence would invalidate the generation rate,
    /// so this runs as a test *and* at the start of the grinding harness.
    ///
    /// # Panics
    ///
    /// If the shortcut and the real path disagree on any nonce.
    pub fn verify_against_real_path(&mut self) {
        let top = self.max_nonce();
        for nonce in [
            0u64,
            1,
            2,
            255,
            4096,
            u64::from(u32::MAX) - 1,
            top / 2,
            top - 1,
            top,
        ] {
            let shortcut = self.hash_candidate(nonce);
            let real = mantle_txhash(&minimal_transfer_tx(nonce)).0;
            assert_eq!(
                shortcut, real,
                "attacker shortcut diverged from the real hash path at nonce {nonce}"
            );
        }
    }

    /// The largest nonce the shortcut can represent without overflowing the
    /// patched field.
    #[must_use]
    pub fn max_nonce(&self) -> u64 {
        if self.patch_len >= 8 {
            u64::MAX
        } else {
            (1u64 << (self.patch_len * 8)) - 2
        }
    }
}

// ---------------------------------------------------------------------------
// Blocks, proposals and the mempool
// ---------------------------------------------------------------------------

/// The block producer's signing key, which must match the leader key inside the
/// proof of leadership.
fn leader_key() -> Ed25519Key {
    Ed25519Key::from_bytes(&[7u8; 32])
}

/// A structurally valid proof of leadership carrying our leader key.
///
/// Decoded from its wire form rather than proved. `Block::reconstruct` never
/// verifies the Groth16 proof — it checks the slot, the total transaction size,
/// the block root and the header signature — so proving here would add minutes
/// of setup to every run without changing a single measured nanosecond. The
/// proof is still the real 224-byte structure produced by the real decoder, so
/// header encoding and signing cost exactly what they cost in production.
///
/// The wire layout is the one `BinaryEncode for Groth16LeaderProof` writes
/// (`core/src/proofs/leader_proof.rs`): `proof (128) || entropy_contribution
/// (32) || leader_key (32) || voucher_cm (32)`.
///
/// # Panics
///
/// If the encoding no longer decodes, i.e. the layout above has changed.
fn proof_of_leadership() -> Groth16LeaderProof {
    let mut bytes = Vec::with_capacity(POL_PROOF_SIZE + 32 * 3);
    bytes.extend_from_slice(&[0u8; POL_PROOF_SIZE]); // proof
    bytes.extend_from_slice(&[0u8; 32]); // entropy_contribution = 0
    bytes.extend_from_slice(leader_key().public_key().as_bytes()); // leader_key
    bytes.extend_from_slice(&[0u8; 32]); // voucher_cm = 0

    let (rest, proof) = Groth16LeaderProof::decode(&bytes, &())
        .expect("the proof-of-leadership wire layout must still decode");
    assert!(rest.is_empty(), "proof of leadership must consume exactly");
    proof
}

/// One genuine `ZkSig` over a sample transaction, to be cloned into every
/// mempool entry.
///
/// # Panics
///
/// If signing fails.
#[must_use]
pub fn sample_op_proof() -> OpProof {
    let tx = minimal_transfer_tx(0);
    let signature = ZkKey::multi_sign(&[input_key()], &tx.hash().to_fr())
        .expect("signing the sample transaction must succeed");
    OpProof::ZkSig(signature)
}

/// A mempool transaction: the sample `MantleTx` plus a proof, as a validator
/// holds it.
///
/// The proof is real in shape and size — produced once by [`sample_op_proof`]
/// and cloned — but is not re-verified per transaction. Reconstruction never
/// inspects `op_proofs`, so this affects no measurement. It does affect
/// `storage_size`, which the block's size check reads, and that is identical
/// either way because the proof is the genuine encoded structure.
#[must_use]
pub fn signed_tx(nonce: u64, proof: &OpProof) -> Tx {
    SignedMantleTx::new_trusted(minimal_transfer_tx(nonce), [proof.clone()].into())
}

/// An honest block over `n` distinct transactions, and the proposal a producer
/// would broadcast for it.
///
/// # Panics
///
/// If `n` exceeds `MAX_BLOCK_TRANSACTIONS`, or block construction fails.
#[must_use]
pub fn honest_block_and_proposal(n: usize) -> (Vec<Tx>, Proposal, Header) {
    let proof = sample_op_proof();
    let transactions: Vec<_> = (0..n as u64).map(|nonce| signed_tx(nonce, &proof)).collect();

    let block = Block::create(
        [0u8; 32].into(),
        Slot::from(42u64),
        proof_of_leadership(),
        BlockTransactions::<Tx>::try_from(transactions.clone()).expect("n within MAX_BLOCK_TRANSACTIONS"),
        &leader_key(),
    )
    .expect("valid block");

    let header = block.header().clone();
    let proposal = block.to_proposal();

    (transactions, proposal, header)
}

// ---------------------------------------------------------------------------
// Mempool admission — what a node pays per incoming transaction
// ---------------------------------------------------------------------------

/// One sample transaction serialized exactly as it crosses the wire.
///
/// # Panics
///
/// If serialization fails.
#[must_use]
pub fn wire_encoded_tx() -> Vec<u8> {
    let tx = signed_tx(0, &sample_op_proof());
    tx.to_bytes()
        .expect("a sample transaction must serialize")
        .to_vec()
}

/// The pieces needed to verify the sample transaction's ZK multi-signature.
///
/// # Panics
///
/// If signing fails.
#[must_use]
pub fn signature_verification_inputs() -> (Vec<ZkPublicKey>, lb_groth16::Fr, ZkSignature) {
    let tx = minimal_transfer_tx(0);
    let signature = ZkKey::multi_sign(&[input_key()], &tx.hash().to_fr())
        .expect("signing the sample transaction must succeed");
    (vec![input_key().to_public_key()], tx.hash().to_fr(), signature)
}

/// Verify the sample transaction's ZK multi-signature — the most expensive
/// per-transaction cryptography in the pipeline.
///
/// This is what `TransferOp::verify` calls
/// (`ZkPublicKey::verify_multi`). It runs at block application rather than at
/// mempool admission, so it is not part of [`admit_tx`]; it is measured
/// separately so that the *upper* bound on per-transaction protocol cost is
/// known, not just the admission cost.
#[must_use]
pub fn verify_signature(pks: &[ZkPublicKey], hash: &lb_groth16::Fr, sig: &ZkSignature) -> bool {
    ZkPublicKey::verify_multi(pks, hash, sig)
}

/// Admit one transaction to the mempool, from wire bytes.
///
/// This is the real ingest path: the mempool's item type is
/// `SignedMantleTx<Preverified>`, and that type's `Deserialize` impl decodes the
/// transaction and then runs `preverify()` — which checks proof/op arity,
/// computes `mantle_txhash`, and runs each operation's stateless checks.
///
/// Worth being precise about what this does *not* include, because it bounds
/// what the number can be used to argue. Signature verification is **not** on
/// this path: for a `Transfer`, `preverify` only validates structure, and the
/// ZK multi-signature is checked later by the stateful `verify`
/// (`ZkPublicKey::verify_multi`), which needs the UTXO set and runs at block
/// application. So this measures admission cost, not total validation cost.
///
/// # Panics
///
/// If the bytes do not deserialize, which would mean the wire format changed.
pub fn admit_tx(bytes: &[u8]) -> Tx {
    Tx::from_bytes(bytes).expect("a sample transaction must deserialize and preverify")
}

// ---------------------------------------------------------------------------
// Reconstruction
// ---------------------------------------------------------------------------

/// The candidate sets a validator's mempool would hand back for a proposal of
/// `n` references, of which the first `k` are ambiguous.
///
/// Each ambiguous reference resolves to two transactions: a decoy, and the one
/// the proposer actually meant. The decoy is placed **first**, so the search
/// has to exhaust every wrong combination before reaching the right one. That
/// is the worst case, and it is the case an attacker gets to choose, since the
/// mempool stream is explicitly documented as unordered.
///
/// How the collisions came to exist does not affect what reconstruction costs —
/// only how many candidates each reference has does. So the sets are built
/// directly, which lets the latency curve be measured at any `k` without first
/// spending 2^(b/2) work to manufacture real collisions at the deployed prefix
/// length. The `birthday` harness measures that manufacturing cost separately.
#[must_use]
pub fn candidate_sets(
    transactions: &[Tx],
    k: usize,
    proof: &OpProof,
) -> Vec<Vec<Tx>> {
    transactions
        .iter()
        .enumerate()
        .map(|(index, tx)| {
            if index < k {
                // A decoy that is not in the block, tried before the real one.
                let decoy = signed_tx(u64::MAX - index as u64, proof);
                vec![decoy, tx.clone()]
            } else {
                vec![tx.clone()]
            }
        })
        .collect()
}

/// The outcome of a reconstruction attempt.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Reconstruction {
    /// The block was rebuilt, after trying `attempts` combinations.
    Rebuilt { attempts: u64 },
    /// No combination reproduced `block_root`.
    Failed { attempts: u64 },
    /// The combination product exceeded `MAX_RECONSTRUCTION_COMBINATIONS`, so
    /// the node refused to search at all and the proposal is dropped.
    RefusedTooManyCombinations { combinations: u64 },
    /// Some reference had more than `MAX_CANDIDATES_PER_REFERENCE` candidates.
    RefusedAmbiguousReference,
}

/// Whether the merged node would even begin the search, applying the two caps
/// from `candidates_for_proposal` in
/// `services/chain/chain-network/src/lib.rs`.
#[must_use]
pub fn caps_verdict<T>(candidates: &[Vec<T>]) -> Option<Reconstruction> {
    let mut combinations: u64 = 1;
    for set in candidates {
        if set.len() > MAX_CANDIDATES_PER_REFERENCE {
            return Some(Reconstruction::RefusedAmbiguousReference);
        }
        combinations = combinations.saturating_mul(set.len() as u64);
        if combinations > MAX_RECONSTRUCTION_COMBINATIONS as u64 {
            return Some(Reconstruction::RefusedTooManyCombinations { combinations });
        }
    }
    None
}

/// Run the reconstruction search over `candidates`.
///
/// This reproduces the loop in `reconstruct_block_from_proposal`
/// (`services/chain/chain-network/src/lib.rs`): take the cartesian product of
/// the per-reference candidate sets and return the first combination that
/// `Block::reconstruct` accepts. `Block::reconstruct` is the real function, and
/// it is where the cost is — per combination it re-encodes every transaction
/// for the size check and re-hashes every transaction for the Merkle root.
///
/// `enforce_caps` selects which policy is measured:
///
/// * `true` — the caps as merged in `logos-blockchain` today.
/// * `false` — the uncapped deterministic lookup that logos-lips#389 v3
///   specifies, on the argument that at a long enough prefix collisions cannot
///   be manufactured and so the caps are unnecessary.
pub fn search_reconstruction(
    header: &Header,
    signature: &Ed25519Signature,
    candidates: Vec<Vec<Tx>>,
    enforce_caps: bool,
) -> Reconstruction {
    use itertools::Itertools as _;

    if enforce_caps && let Some(verdict) = caps_verdict(&candidates) {
        return verdict;
    }

    let mut attempts: u64 = 0;
    for combination in candidates.into_iter().multi_cartesian_product() {
        attempts += 1;
        let Ok(transactions) = BlockTransactions::<Tx>::try_from(combination) else {
            continue;
        };
        if Block::reconstruct(header.clone(), transactions, *signature).is_ok() {
            return Reconstruction::Rebuilt { attempts };
        }
    }

    Reconstruction::Failed { attempts }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sample_transaction_is_the_smallest_valid_transfer() {
        let tx = minimal_transfer_tx(0);
        assert_eq!(tx.0.len(), 1, "one operation");
        match &tx.0[0] {
            Op::Transfer(transfer) => {
                assert_eq!(transfer.inputs.len(), 1);
                assert_eq!(transfer.outputs.len(), 1);
            }
            other => panic!("expected a Transfer, got {other:?}"),
        }
    }

    #[test]
    fn distinct_nonces_give_distinct_hashes() {
        assert_ne!(
            mantle_txhash(&minimal_transfer_tx(0)),
            mantle_txhash(&minimal_transfer_tx(1))
        );
    }

    #[test]
    fn attacker_shortcut_agrees_with_the_real_hash_path() {
        AttackerHasher::new().verify_against_real_path();
    }

    #[test]
    fn honest_proposal_reconstructs_when_unambiguous() {
        let (transactions, proposal, header) = honest_block_and_proposal(8);
        let proof = sample_op_proof();
        let candidates = candidate_sets(&transactions, 0, &proof);

        assert_eq!(
            search_reconstruction(&header, proposal.signature(), candidates, true),
            Reconstruction::Rebuilt { attempts: 1 }
        );
    }

    #[test]
    fn ambiguity_forces_the_search_to_exhaust_wrong_combinations_first() {
        let (transactions, proposal, header) = honest_block_and_proposal(8);
        let proof = sample_op_proof();
        let k = 3;
        let candidates = candidate_sets(&transactions, k, &proof);

        // Decoys are tried first at every ambiguous position, so the correct
        // combination is the last of the 2^k.
        assert_eq!(
            search_reconstruction(&header, proposal.signature(), candidates, false),
            Reconstruction::Rebuilt { attempts: 1 << k }
        );
    }

    #[test]
    fn the_merged_caps_refuse_the_proposal_past_five_collisions() {
        let (transactions, proposal, header) = honest_block_and_proposal(8);
        let proof = sample_op_proof();
        // 2^6 = 64 > MAX_RECONSTRUCTION_COMBINATIONS = 32.
        let candidates = candidate_sets(&transactions, 6, &proof);

        assert!(matches!(
            search_reconstruction(&header, proposal.signature(), candidates, true),
            Reconstruction::RefusedTooManyCombinations { .. }
        ));
    }

    #[test]
    fn proposal_carries_one_reference_per_transaction() {
        let (transactions, proposal, _) = honest_block_and_proposal(16);
        assert_eq!(proposal.mempool_transactions().len(), transactions.len());
    }
}
