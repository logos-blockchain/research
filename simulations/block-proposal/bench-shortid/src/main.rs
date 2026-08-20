//! Short-ID hash benchmark: SipHash vs Blake2b over 32-byte transaction hashes.
//!
//! Context: the Revised Block Proposal Compression RFC derives per-block keyed
//! 64-bit short IDs from full transaction hashes (BIP-152 style). Every
//! validator recomputes shortid(key, txhash) for its whole mempool once per
//! proposal, so the operational cost is `mempool_size * per-hash cost` on a
//! 32-byte input. This binary measures exactly that.
//!
//! Candidates (pure-Rust implementations only):
//!   - SipHash-2-4  (`siphasher`)          — BIP-152's choice
//!   - SipHash-1-3  (`siphasher`)          — faster variant, std HashMap's default
//!   - Blake2b-512 truncated to 8 bytes (`blake2`, RustCrypto)  — key mixed as prefix
//!   - Blake2bMac, keyed mode, native 8-byte output (`blake2`)
//!
//! `blake2b_simd` was considered as a SIMD-tuned upper bound for Blake2b but
//! is currently unbuildable from crates.io (its `arrayref ^0.3.5` dependency
//! has had every matching version yanked). The `blake2` crate is the
//! decision-relevant implementation regardless: it is what logos-blockchain's
//! `crypto.rs` (`pub type Hasher = blake2::Blake2b<U32>`) already uses.

use std::hash::Hasher as _;
use std::hint::black_box;
use std::time::Instant;

use blake2::digest::{consts::U8, KeyInit, Mac};
use blake2::{Blake2b512, Blake2bMac, Digest};
use siphasher::sip::{SipHasher13, SipHasher24};

const INPUT_LEN: usize = 32; // a full transaction hash
const WARMUP_ITERS: usize = 200_000;
const MEASURE_ITERS: usize = 2_000_000;
const RUNS: usize = 5;

/// Deterministic xorshift so runs are reproducible without pulling in a RNG crate.
struct XorShift64(u64);
impl XorShift64 {
    fn next(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.0 = x;
        x
    }
}

fn gen_inputs(n: usize, seed: u64) -> Vec<[u8; INPUT_LEN]> {
    let mut rng = XorShift64(seed | 1);
    (0..n)
        .map(|_| {
            let mut buf = [0u8; INPUT_LEN];
            for chunk in buf.chunks_mut(8) {
                chunk.copy_from_slice(&rng.next().to_le_bytes()[..chunk.len()]);
            }
            buf
        })
        .collect()
}

fn shortid_siphash24(k0: u64, k1: u64, input: &[u8]) -> u64 {
    let mut h = SipHasher24::new_with_keys(k0, k1);
    h.write(input);
    h.finish()
}

fn shortid_siphash13(k0: u64, k1: u64, input: &[u8]) -> u64 {
    let mut h = SipHasher13::new_with_keys(k0, k1);
    h.write(input);
    h.finish()
}

fn shortid_blake2b512_trunc(key: &[u8; 16], input: &[u8]) -> u64 {
    // Unkeyed Blake2b-512 with the key absorbed as a prefix, truncated to 8
    // bytes — the shape an implementation reusing the existing `Hasher` type
    // (blake2::Blake2b) would most likely pick.
    let mut h = Blake2b512::new();
    Digest::update(&mut h, key);
    Digest::update(&mut h, input);
    let out = h.finalize();
    u64::from_le_bytes(out[..8].try_into().unwrap())
}

fn shortid_blake2bmac8(key: &[u8; 16], input: &[u8]) -> u64 {
    // Blake2b's native keyed mode with an 8-byte output parameter block —
    // the "proper" way to build a 64-bit keyed tag from Blake2b.
    let mut h = <Blake2bMac<U8> as KeyInit>::new_from_slice(key).unwrap();
    Mac::update(&mut h, input);
    let out = h.finalize().into_bytes();
    u64::from_le_bytes(out[..].try_into().unwrap())
}

/// Measure `f` applied to every input, RUNS times; report per-hash ns (median
/// and min across runs) plus the projected cost of rehashing a mempool.
fn bench(name: &str, inputs: &[[u8; INPUT_LEN]], mut f: impl FnMut(&[u8]) -> u64) {
    // Warmup.
    let mut acc = 0u64;
    for input in inputs.iter().cycle().take(WARMUP_ITERS) {
        acc = acc.wrapping_add(f(black_box(input)));
    }

    let mut per_hash_ns = Vec::with_capacity(RUNS);
    for _ in 0..RUNS {
        let start = Instant::now();
        for input in inputs.iter().cycle().take(MEASURE_ITERS) {
            acc = acc.wrapping_add(f(black_box(input)));
        }
        let elapsed = start.elapsed();
        per_hash_ns.push(elapsed.as_nanos() as f64 / MEASURE_ITERS as f64);
    }
    black_box(acc);

    per_hash_ns.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let median = per_hash_ns[RUNS / 2];
    let min = per_hash_ns[0];
    let hps = 1e9 / median;
    println!(
        "{name:<28} {median:>8.2} ns/hash (min {min:>6.2})  {:>7.1} Mh/s   M=1e5: {:>7.2} ms   M=1e6: {:>7.2} ms",
        hps / 1e6,
        median * 1e5 / 1e6,
        median * 1e6 / 1e6,
    );
}

fn main() {
    println!("shortid-bench: 64-bit keyed short IDs over {INPUT_LEN}-byte inputs");
    println!(
        "iters/run: {MEASURE_ITERS}, runs: {RUNS} (median reported), warmup: {WARMUP_ITERS}\n"
    );

    let inputs = gen_inputs(4096, 0x5eed_cafe_f00d_beef);
    let k0 = 0x0123_4567_89ab_cdefu64;
    let k1 = 0xfedc_ba98_7654_3210u64;
    let key16: [u8; 16] = {
        let mut k = [0u8; 16];
        k[..8].copy_from_slice(&k0.to_le_bytes());
        k[8..].copy_from_slice(&k1.to_le_bytes());
        k
    };

    bench("SipHash-2-4", &inputs, |d| shortid_siphash24(k0, k1, d));
    bench("SipHash-1-3", &inputs, |d| shortid_siphash13(k0, k1, d));
    bench("Blake2b-512/trunc8", &inputs, |d| shortid_blake2b512_trunc(&key16, d));
    bench("Blake2bMac-8 (keyed)", &inputs, |d| shortid_blake2bmac8(&key16, d));

    // Sanity: distinct keys must disagree; the same key must agree.
    let a = shortid_siphash24(k0, k1, &inputs[0]);
    let b = shortid_siphash24(k0, k1, &inputs[0]);
    let c = shortid_siphash24(k0 ^ 1, k1, &inputs[0]);
    assert_eq!(a, b);
    assert_ne!(a, c);
    println!("\nsanity: keyed determinism ok, key sensitivity ok");
}
