//! R_gen — the rate at which an adversary can turn out candidate
//! transactions reduced to a reference prefix.
//!
//! Three rates are measured, and the difference between them is the point:
//!
//! * `node_path` — build a valid `MantleTx`, encode it, hash it. This is what a
//!   node does per transaction, and it is the *slowest* honest estimate.
//! * `attacker_patched` — encode once, then per candidate overwrite the varying
//!   bytes and hash. No attacker would do less than this, so it is the rate the
//!   security margin should be computed from.
//! * `blake2b_only` — Blake2b-256 over the same fixed preimage, with no
//!   transaction work at all. This is the floor: no implementation of this
//!   attack, on this CPU, can beat it.
//!
//! Truncating the 32-byte hash to `L` bytes is a slice and costs nothing
//! measurable, so R_gen does not depend on `L`. `L` enters the model only
//! through the number of candidates needed, 2^(8L/2).

use criterion::{Criterion, Throughput, criterion_group, criterion_main};
use reference_prefix_bench::{
    AttackerHasher, admit_tx, mantle_txhash, minimal_transfer_tx, sample_preimage_len,
    sample_tx_encoded_len, signature_verification_inputs, verify_signature, wire_encoded_tx,
};
use std::hint::black_box;

fn candidate_generation(c: &mut Criterion) {
    // Print the sizes the rates are relative to, so a reviewer reading the
    // criterion output alone can re-derive them.
    eprintln!(
        "sample MantleTx: {} bytes encoded, {} bytes hashed (b\"MANTLE_TXHASH_V1\" || encode(tx))",
        sample_tx_encoded_len(),
        sample_preimage_len()
    );

    let mut group = c.benchmark_group("candidate_generation");
    group.throughput(Throughput::Elements(1));

    group.bench_function("node_path", |b| {
        let mut nonce = 0u64;
        b.iter(|| {
            nonce = nonce.wrapping_add(1);
            let tx = minimal_transfer_tx(black_box(nonce));
            black_box(mantle_txhash(&tx))
        });
    });

    group.bench_function("attacker_patched", |b| {
        let mut hasher = AttackerHasher::new();
        hasher.verify_against_real_path();
        let max = hasher.max_nonce();
        let mut nonce = 0u64;
        b.iter(|| {
            nonce = if nonce >= max { 0 } else { nonce + 1 };
            black_box(hasher.hash_candidate(black_box(nonce)))
        });
    });

    group.bench_function("blake2b_only", |b| {
        use lb_core::crypto::{Digest as _, Hasher};
        let preimage = vec![0u8; sample_preimage_len()];
        b.iter(|| {
            let digest: [u8; 32] = Hasher::digest(black_box(&preimage)).into();
            black_box(digest)
        });
    });

    group.finish();
}

/// What a validator actually pays to admit one transaction to its mempool.
///
/// This exists to test a specific claim rather than to set the parameter: an
/// earlier experiment measured mempool flooding at ~0.3 tx/s, and it is worth
/// knowing whether the protocol's own per-transaction cost can account for
/// that. It cannot be a reproduction of that experiment — no node, network or
/// harness is involved here — but it does bound the CPU side of it.
fn mempool_admission(c: &mut Criterion) {
    let bytes = wire_encoded_tx();
    eprintln!("wire-encoded SignedMantleTx: {} bytes", bytes.len());

    let mut group = c.benchmark_group("mempool_admission");
    group.throughput(Throughput::Elements(1));

    group.bench_function("deserialize_and_preverify", |b| {
        b.iter(|| black_box(admit_tx(black_box(&bytes))));
    });

    // Not on the admission path — this runs at block application — but it is
    // the most expensive per-transaction cryptography in the pipeline, so it
    // bounds the protocol's per-transaction cost from above.
    let (pks, hash, sig) = signature_verification_inputs();
    group.bench_function("zk_multisig_verify", |b| {
        b.iter(|| black_box(verify_signature(black_box(&pks), &hash, &sig)));
    });

    group.finish();
}

criterion_group!(benches, candidate_generation, mempool_admission);
criterion_main!(benches);
