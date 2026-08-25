//! Short-ID hash benchmark: SipHash vs Blake2b over 32-byte transaction hashes.
//!
//! Context: the Revised Block Proposal Compression RFC derives per-block keyed
//! 64-bit short IDs from full transaction hashes (BIP-152 style). Every
//! validator recomputes shortid(key, txhash) for its whole mempool once per
//! proposal — the key changes every block, so nothing can be cached across
//! proposals. The operational cost is therefore `mempool_size * per-hash cost`
//! on 32-byte inputs, and that is what this binary measures.
//!
//! Three measurements are reported for each candidate:
//!
//!   1. **cache-resident per-hash** — a small input set cycled in L1/L2. This
//!      isolates the cost of the hash function itself.
//!   2. **single-core, full mempool** — one pass over a real MEMPOOL-element
//!      array (32 MB at 10^6), so the total is *measured* rather than
//!      extrapolated from (1). The gap between (1) and (2) is the memory
//!      cost that a cache-resident micro-benchmark hides.
//!   3. **multi-core, full mempool** — the same pass partitioned across all
//!      available cores. The rehash is embarrassingly parallel (every
//!      transaction is independent), so this is the figure a validator that
//!      threads the work would actually see.
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
//!
//! Note: this measures the hashing only. A real `resolve_candidates` also
//! inserts each short ID into a map; that cost is not included here.

use std::hash::Hasher as _;
use std::hint::black_box;
use std::thread;
use std::time::Instant;

use blake2::digest::{consts::U8, KeyInit, Mac};
use blake2::{Blake2b512, Blake2bMac, Digest};
use siphasher::sip::{SipHasher13, SipHasher24};

const INPUT_LEN: usize = 32; // a full transaction hash
const MEMPOOL: usize = 1_000_000; // the headline mempool size
const CACHE_SET: usize = 4_096; // inputs for the cache-resident measurement
const MICRO_ITERS: usize = 2_000_000;
const WARMUP_ITERS: usize = 200_000;
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

fn median(mut xs: Vec<f64>) -> f64 {
    xs.sort_by(|a, b| a.partial_cmp(b).unwrap());
    xs[xs.len() / 2]
}

/// (1) Cache-resident per-hash cost: a small input set cycled in L1/L2.
fn bench_cache_resident(inputs: &[[u8; INPUT_LEN]], f: &(dyn Fn(&[u8]) -> u64 + Sync)) -> f64 {
    let mut acc = 0u64;
    for input in inputs.iter().cycle().take(WARMUP_ITERS) {
        acc = acc.wrapping_add(f(black_box(input)));
    }
    let mut per_hash = Vec::with_capacity(RUNS);
    for _ in 0..RUNS {
        let start = Instant::now();
        for input in inputs.iter().cycle().take(MICRO_ITERS) {
            acc = acc.wrapping_add(f(black_box(input)));
        }
        per_hash.push(start.elapsed().as_nanos() as f64 / MICRO_ITERS as f64);
    }
    black_box(acc);
    median(per_hash)
}

/// (2) One single-threaded pass over the whole mempool. Returns ns/hash.
fn bench_single(inputs: &[[u8; INPUT_LEN]], f: &(dyn Fn(&[u8]) -> u64 + Sync)) -> f64 {
    let mut per_hash = Vec::with_capacity(RUNS);
    for _ in 0..RUNS {
        let start = Instant::now();
        let mut acc = 0u64;
        for input in inputs {
            acc = acc.wrapping_add(f(black_box(input)));
        }
        black_box(acc);
        per_hash.push(start.elapsed().as_nanos() as f64 / inputs.len() as f64);
    }
    median(per_hash)
}

/// (3) The same pass partitioned across `threads` cores. Returns effective
/// ns/hash, i.e. wall-clock time divided by the whole mempool.
fn bench_multi(
    inputs: &[[u8; INPUT_LEN]],
    f: &(dyn Fn(&[u8]) -> u64 + Sync),
    threads: usize,
) -> f64 {
    let chunk = inputs.len().div_ceil(threads);
    let mut per_hash = Vec::with_capacity(RUNS);
    for _ in 0..RUNS {
        let start = Instant::now();
        thread::scope(|s| {
            for part in inputs.chunks(chunk) {
                s.spawn(move || {
                    let mut acc = 0u64;
                    for input in part {
                        acc = acc.wrapping_add(f(black_box(input)));
                    }
                    black_box(acc);
                });
            }
        });
        per_hash.push(start.elapsed().as_nanos() as f64 / inputs.len() as f64);
    }
    median(per_hash)
}

fn main() {
    let threads = thread::available_parallelism().map_or(1, |n| n.get());

    println!("shortid-bench: 64-bit keyed short IDs over {INPUT_LEN}-byte inputs");
    println!(
        "mempool: {MEMPOOL} entries ({} MB), runs: {RUNS} (median), cores: {threads}",
        MEMPOOL * INPUT_LEN / (1024 * 1024)
    );
    println!(
        "cache-resident set: {CACHE_SET} entries ({} KB), {MICRO_ITERS} iters/run\n",
        CACHE_SET * INPUT_LEN / 1024
    );

    let small = gen_inputs(CACHE_SET, 0x5eed_cafe_f00d_beef);
    let mempool = gen_inputs(MEMPOOL, 0x0dd_f00d_1234_5678);

    let k0 = 0x0123_4567_89ab_cdefu64;
    let k1 = 0xfedc_ba98_7654_3210u64;
    let key16: [u8; 16] = {
        let mut k = [0u8; 16];
        k[..8].copy_from_slice(&k0.to_le_bytes());
        k[8..].copy_from_slice(&k1.to_le_bytes());
        k
    };

    let candidates: Vec<(&str, Box<dyn Fn(&[u8]) -> u64 + Sync>)> = vec![
        ("SipHash-2-4", Box::new(move |d: &[u8]| shortid_siphash24(k0, k1, d))),
        ("SipHash-1-3", Box::new(move |d: &[u8]| shortid_siphash13(k0, k1, d))),
        ("Blake2b-512/trunc8", Box::new(move |d: &[u8]| shortid_blake2b512_trunc(&key16, d))),
        ("Blake2bMac-8 (keyed)", Box::new(move |d: &[u8]| shortid_blake2bmac8(&key16, d))),
    ];

    println!(
        "{:<22} | {:>9} | {:>9} {:>11} | {:>9} {:>11} {:>8}",
        "", "cache-res", "1-core", "1-core", &format!("{threads}-core"), &format!("{threads}-core"), ""
    );
    println!(
        "{:<22} | {:>9} | {:>9} {:>11} | {:>9} {:>11} {:>8}",
        "function", "ns/hash", "ns/hash", "total(1e6)", "ns/hash", "total(1e6)", "speedup"
    );
    println!("{}", "-".repeat(96));

    for (name, f) in &candidates {
        let cache = bench_cache_resident(&small, f.as_ref());
        let one = bench_single(&mempool, f.as_ref());
        let many = bench_multi(&mempool, f.as_ref(), threads);
        println!(
            "{name:<22} | {cache:>9.2} | {one:>9.2} {:>8.2} ms | {many:>9.2} {:>8.2} ms {:>7.1}x",
            one * MEMPOOL as f64 / 1e6,
            many * MEMPOOL as f64 / 1e6,
            one / many,
        );
    }

    // Sanity: distinct keys must disagree; the same key must agree.
    let a = shortid_siphash24(k0, k1, &small[0]);
    let b = shortid_siphash24(k0, k1, &small[0]);
    let c = shortid_siphash24(k0 ^ 1, k1, &small[0]);
    assert_eq!(a, b);
    assert_ne!(a, c);
    println!("\nsanity: keyed determinism ok, key sensitivity ok");
    println!("note: hashing only; the map insert of a real resolve_candidates is not included.");
}
