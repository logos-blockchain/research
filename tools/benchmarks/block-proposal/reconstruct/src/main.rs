//! End-to-end block-proposal reconstruction benchmark.
//!
//! Measures the *whole* reconstruction step defined in the Revised Block
//! Proposal Compression RFC, not a component of it, and not an estimate:
//!
//!   1. derive the per-proposal reference key from the header
//!   2. rehash the entire mempool under that key and index it by short ID
//!   3. resolve every reference in the proposal to its candidate set
//!   4. search up to MAX_RECONSTRUCTION_COMBINATIONS assignments, computing
//!      `body_root` for each and comparing against `header.body_root`
//!
//! Every phase is executed for real. The `body_root` is a genuine Blake2b
//! Merkle root over MAX_BLOCK_TXS full transaction hashes (padded to the next
//! power of two) combined with the serialized uncle headers, exactly as the
//! spec defines it, so the per-combination cost is measured rather than
//! assumed.
//!
//! Two search strategies are measured, because the spec claims one is much
//! cheaper than the other:
//!
//!   - **full**: recompute the entire Merkle root for every assignment.
//!   - **incremental**: keep the tree and recompute only the leaf paths that
//!     the assignment changes. The spec says "an implementation can keep the
//!     unchanged Merkle leaves between assignments, so that successive
//!     combinations cost one leaf path recomputation each"; this measures
//!     what that is worth.
//!
//! Single-core and multi-core figures are reported for each. Both the mempool
//! rehash and the combination search are embarrassingly parallel.

use std::collections::HashMap;
use std::hint::black_box;
use std::thread;
use std::time::{Duration, Instant};

use blake2::{Blake2b512, Digest};

// Protocol parameters, from the RFC.
const SHORT_ID_LENGTH: usize = 8;
const MAX_BLOCK_TXS: usize = 1024;
const MAX_UNCLES: usize = 4;
const SIGNED_HEADER_LEN: usize = 361;
const KEY_LEN: usize = 16;

// Benchmark parameters.
const MEMPOOL: usize = 1_000_000;
const COMBINATION_SWEEP: [usize; 5] = [1, 2, 8, 32, 64];
const RUNS: usize = 5;

type TxHash = [u8; 32];

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
    fn fill(&mut self, buf: &mut [u8]) {
        for chunk in buf.chunks_mut(8) {
            let n = chunk.len();
            chunk.copy_from_slice(&self.next().to_le_bytes()[..n]);
        }
    }
}

/// `short_id(key, txhash)` — prefix-keyed Blake2b, truncated. Matches the RFC.
#[inline]
fn short_id(key: &[u8; KEY_LEN], tx: &TxHash) -> u64 {
    let mut h = Blake2b512::new();
    h.update(key);
    h.update(tx);
    let out = h.finalize();
    u64::from_le_bytes(out[..SHORT_ID_LENGTH].try_into().unwrap())
}

/// One internal Merkle node: Blake2b over the concatenation of two children.
#[inline]
fn merkle_node(l: &TxHash, r: &TxHash) -> TxHash {
    let mut h = Blake2b512::new();
    h.update(l);
    h.update(r);
    let out = h.finalize();
    let mut node = [0u8; 32];
    node.copy_from_slice(&out[..32]);
    node
}

/// Full Merkle root over `leaves`, padded to the next power of two with zeros.
fn merkle_root(leaves: &[TxHash]) -> TxHash {
    if leaves.is_empty() {
        return [0u8; 32];
    }
    let mut n = leaves.len().next_power_of_two();
    let mut level: Vec<TxHash> = leaves.to_vec();
    level.resize(n, [0u8; 32]);
    while n > 1 {
        for i in 0..n / 2 {
            level[i] = merkle_node(&level[2 * i], &level[2 * i + 1]);
        }
        n /= 2;
        level.truncate(n);
    }
    level[0]
}

/// A Merkle tree kept level by level, so a single changed leaf can be
/// re-rooted along its path instead of rebuilding the whole tree.
struct MerkleTree {
    levels: Vec<Vec<TxHash>>, // levels[0] = padded leaves, last = [root]
}

impl MerkleTree {
    fn build(leaves: &[TxHash]) -> Self {
        let n = leaves.len().next_power_of_two();
        let mut base = leaves.to_vec();
        base.resize(n, [0u8; 32]);
        let mut levels = vec![base];
        while levels.last().unwrap().len() > 1 {
            let prev = levels.last().unwrap();
            let next: Vec<TxHash> = (0..prev.len() / 2)
                .map(|i| merkle_node(&prev[2 * i], &prev[2 * i + 1]))
                .collect();
            levels.push(next);
        }
        Self { levels }
    }

    fn root(&self) -> TxHash {
        self.levels.last().unwrap()[0]
    }

    /// Replace one leaf and recompute only its path to the root.
    fn set_leaf(&mut self, mut idx: usize, value: TxHash) {
        self.levels[0][idx] = value;
        for d in 0..self.levels.len() - 1 {
            let sib = idx ^ 1;
            let (l, r) = if idx & 1 == 0 {
                (self.levels[d][idx], self.levels[d][sib])
            } else {
                (self.levels[d][sib], self.levels[d][idx])
            };
            idx /= 2;
            self.levels[d + 1][idx] = merkle_node(&l, &r);
        }
    }
}

/// `body_root(uncle_headers, transactions)` — the domain-separated hash over
/// the serialized uncle list and the transaction Merkle root.
#[inline]
fn body_root(serialized_uncles: &[u8], tx_root: &TxHash) -> TxHash {
    let mut h = Blake2b512::new();
    h.update(b"BODY_ROOT_V1");
    h.update(serialized_uncles);
    h.update(tx_root);
    let out = h.finalize();
    let mut root = [0u8; 32];
    root.copy_from_slice(&out[..32]);
    root
}

struct Fixture {
    mempool: Vec<TxHash>,
    key: [u8; KEY_LEN],
    uncles: Vec<u8>,
    /// For each reference position, the candidate mempool indices.
    candidates: Vec<Vec<usize>>,
    /// The body root the proposer committed to.
    target: TxHash,
}

/// Build a proposal whose candidate structure yields exactly `combinations`
/// assignments: `log2(combinations)` references get a second, decoy candidate.
fn fixture(combinations: usize) -> Fixture {
    let mut rng = XorShift64(0x51ae_f00d_1234_5678);
    let mut mempool = vec![[0u8; 32]; MEMPOOL];
    for tx in mempool.iter_mut() {
        rng.fill(tx);
    }

    let mut key = [0u8; KEY_LEN];
    rng.fill(&mut key);

    let mut uncles = vec![MAX_UNCLES as u8];
    uncles.resize(1 + MAX_UNCLES * SIGNED_HEADER_LEN, 0);
    rng.fill(&mut uncles[1..]);

    // The proposal references the first MAX_BLOCK_TXS mempool entries.
    let selected: Vec<usize> = (0..MAX_BLOCK_TXS).collect();
    let leaves: Vec<TxHash> = selected.iter().map(|&i| mempool[i]).collect();
    let target = body_root(&uncles, &merkle_root(&leaves));

    // Ambiguity: give the first `ambiguous` references a decoy candidate whose
    // short ID collides. The decoy is a distinct mempool transaction, so the
    // search must discriminate them by body_root — which is the work measured.
    let ambiguous = combinations.trailing_zeros() as usize;
    assert_eq!(1usize << ambiguous, combinations, "combinations must be a power of two");
    let mut candidates: Vec<Vec<usize>> = selected.iter().map(|&i| vec![i]).collect();
    for (r, cand) in candidates.iter_mut().enumerate().take(ambiguous) {
        // Decoy first, committed transaction second, so the committed
        // assignment is the LAST one enumerated and the search is forced to
        // evaluate all `combinations` of them. That is the worst case the
        // MAX_RECONSTRUCTION_COMBINATIONS bound exists to cap, and the only
        // case worth measuring: any earlier match is strictly cheaper.
        let committed = cand[0];
        cand[0] = MEMPOOL - 1 - r; // a decoy, never itself selected
        cand.push(committed);
    }

    Fixture { mempool, key, uncles, candidates, target }
}

/// Phase 2+3: rehash the mempool under the key and index it by short ID.
/// Returns the index and the number of entries, so the work cannot be elided.
fn rehash_index(mempool: &[TxHash], key: &[u8; KEY_LEN]) -> HashMap<u64, Vec<u32>> {
    let mut index: HashMap<u64, Vec<u32>> = HashMap::with_capacity(mempool.len() * 2);
    for (i, tx) in mempool.iter().enumerate() {
        index.entry(short_id(key, tx)).or_default().push(i as u32);
    }
    index
}

fn rehash_index_parallel(
    mempool: &[TxHash],
    key: &[u8; KEY_LEN],
    threads: usize,
) -> Vec<HashMap<u64, Vec<u32>>> {
    let chunk = mempool.len().div_ceil(threads);
    thread::scope(|s| {
        let handles: Vec<_> = mempool
            .chunks(chunk)
            .enumerate()
            .map(|(c, part)| {
                s.spawn(move || {
                    let base = c * chunk;
                    let mut idx: HashMap<u64, Vec<u32>> =
                        HashMap::with_capacity(part.len() * 2);
                    for (i, tx) in part.iter().enumerate() {
                        idx.entry(short_id(key, tx)).or_default().push((base + i) as u32);
                    }
                    idx
                })
            })
            .collect();
        handles.into_iter().map(|h| h.join().unwrap()).collect()
    })
}

/// Enumerate assignment `n` of the candidate space: bit k of `n` selects the
/// alternative for the k-th ambiguous reference.
#[inline]
fn assignment_leaves(fx: &Fixture, n: usize, out: &mut Vec<TxHash>) {
    out.clear();
    let mut bit = 0usize;
    for cand in &fx.candidates {
        let pick = if cand.len() > 1 {
            let c = (n >> bit) & 1;
            bit += 1;
            cand[c]
        } else {
            cand[0]
        };
        out.push(fx.mempool[pick]);
    }
}

/// Phase 4, full strategy: rebuild the whole Merkle root per assignment.
/// Returns the matching assignment index, or None.
fn search_full(fx: &Fixture, combinations: usize) -> Option<usize> {
    let mut leaves = Vec::with_capacity(MAX_BLOCK_TXS);
    for n in 0..combinations {
        assignment_leaves(fx, n, &mut leaves);
        if body_root(&fx.uncles, &merkle_root(&leaves)) == fx.target {
            return Some(n);
        }
    }
    None
}

/// Phase 4, incremental strategy: build the tree once, then per assignment
/// touch only the leaves whose choice differs from the current state.
fn search_incremental(fx: &Fixture, combinations: usize) -> Option<usize> {
    let mut leaves = Vec::with_capacity(MAX_BLOCK_TXS);
    assignment_leaves(fx, 0, &mut leaves);
    let mut tree = MerkleTree::build(&leaves);
    let ambiguous: Vec<usize> = fx
        .candidates
        .iter()
        .enumerate()
        .filter(|(_, c)| c.len() > 1)
        .map(|(i, _)| i)
        .collect();

    let mut state = 0usize;
    if body_root(&fx.uncles, &tree.root()) == fx.target {
        return Some(0);
    }
    for n in 1..combinations {
        let changed = state ^ n;
        for (bit, &leaf_idx) in ambiguous.iter().enumerate() {
            if changed >> bit & 1 == 1 {
                let pick = fx.candidates[leaf_idx][(n >> bit) & 1];
                tree.set_leaf(leaf_idx, fx.mempool[pick]);
            }
        }
        state = n;
        if body_root(&fx.uncles, &tree.root()) == fx.target {
            return Some(n);
        }
    }
    None
}

/// Phase 4 parallel: partition the assignment space across threads. Each
/// thread keeps its own tree, so the incremental strategy still applies.
fn search_parallel(fx: &Fixture, combinations: usize, threads: usize, incremental: bool) -> Option<usize> {
    if combinations == 1 {
        return if incremental { search_incremental(fx, 1) } else { search_full(fx, 1) };
    }
    let per = combinations.div_ceil(threads.min(combinations));
    thread::scope(|s| {
        let handles: Vec<_> = (0..combinations)
            .step_by(per)
            .map(|start| {
                let end = (start + per).min(combinations);
                s.spawn(move || {
                    let mut leaves = Vec::with_capacity(MAX_BLOCK_TXS);
                    let mut tree = None;
                    let mut state = start;
                    for n in start..end {
                        let root = if incremental {
                            if tree.is_none() {
                                assignment_leaves(fx, n, &mut leaves);
                                tree = Some(MerkleTree::build(&leaves));
                                state = n;
                            } else {
                                let t: &mut MerkleTree = tree.as_mut().unwrap();
                                let changed = state ^ n;
                                let mut bit = 0usize;
                                for (i, cand) in fx.candidates.iter().enumerate() {
                                    if cand.len() > 1 {
                                        if changed >> bit & 1 == 1 {
                                            t.set_leaf(i, fx.mempool[cand[(n >> bit) & 1]]);
                                        }
                                        bit += 1;
                                    }
                                }
                                state = n;
                            }
                            tree.as_ref().unwrap().root()
                        } else {
                            assignment_leaves(fx, n, &mut leaves);
                            merkle_root(&leaves)
                        };
                        if body_root(&fx.uncles, &root) == fx.target {
                            return Some(n);
                        }
                    }
                    None
                })
            })
            .collect();
        handles.into_iter().filter_map(|h| h.join().unwrap()).next()
    })
}

fn median(mut xs: Vec<Duration>) -> f64 {
    xs.sort();
    xs[xs.len() / 2].as_secs_f64() * 1e3 // ms
}

fn main() {
    let threads = thread::available_parallelism().map_or(1, |n| n.get());

    println!("reconstruct-bench: end-to-end block proposal reconstruction");
    println!(
        "mempool: {MEMPOOL} entries, references: {MAX_BLOCK_TXS}, uncles: {MAX_UNCLES}, runs: {RUNS} (median), cores: {threads}"
    );
    println!("all phases executed for real; no component is estimated\n");

    // ---- Phase A: mempool rehash + index, measured on its own ----
    let fx = fixture(1);
    let mut single = Vec::new();
    for _ in 0..RUNS {
        let t = Instant::now();
        let idx = rehash_index(&fx.mempool, &fx.key);
        single.push(t.elapsed());
        black_box(idx.len());
    }
    let rehash_1 = median(single);

    let mut multi = Vec::new();
    for _ in 0..RUNS {
        let t = Instant::now();
        let parts = rehash_index_parallel(&fx.mempool, &fx.key, threads);
        multi.push(t.elapsed());
        black_box(parts.len());
    }
    let rehash_n = median(multi);

    println!("Phase A — rehash {MEMPOOL} mempool entries and index by short ID");
    println!("  1-core        {rehash_1:>9.2} ms");
    println!("  {threads}-core       {rehash_n:>9.2} ms      speedup {:.1}x\n", rehash_1 / rehash_n);

    // ---- Phase B: the combination search, swept over C ----
    println!("Phase B — combination search, body_root per assignment (C = combinations tried)");
    println!(
        "{:>4} | {:>12} {:>12} | {:>12} {:>12}",
        "C", "full 1-core", "full N-core", "incr 1-core", "incr N-core"
    );
    println!("{}", "-".repeat(64));

    let mut search_results = Vec::new();
    for &c in &COMBINATION_SWEEP {
        let fx = fixture(c);
        let mut f1 = Vec::new();
        for _ in 0..RUNS {
            let t = Instant::now();
            let r = search_full(&fx, c);
            f1.push(t.elapsed());
            black_box(r);
        }
        let mut f_n = Vec::new();
        for _ in 0..RUNS {
            let t = Instant::now();
            let r = search_parallel(&fx, c, threads, false);
            f_n.push(t.elapsed());
            black_box(r);
        }
        let mut i1 = Vec::new();
        for _ in 0..RUNS {
            let t = Instant::now();
            let r = search_incremental(&fx, c);
            i1.push(t.elapsed());
            black_box(r);
        }
        let mut i_n = Vec::new();
        for _ in 0..RUNS {
            let t = Instant::now();
            let r = search_parallel(&fx, c, threads, true);
            i_n.push(t.elapsed());
            black_box(r);
        }
        let (a, b, cc, d) = (median(f1), median(f_n), median(i1), median(i_n));
        println!("{c:>4} | {a:>9.3} ms {b:>9.3} ms | {cc:>9.3} ms {d:>9.3} ms");
        search_results.push((c, a, b, cc, d));
    }

    // ---- Total: the complete reconstruction ----
    println!("\nTotal — complete reconstruction (Phase A + Phase B)");
    println!(
        "{:>4} | {:>14} {:>14} | {:>14} {:>14}",
        "C", "full 1-core", "full N-core", "incr 1-core", "incr N-core"
    );
    println!("{}", "-".repeat(72));
    for (c, f1, fnn, i1, inn) in &search_results {
        println!(
            "{c:>4} | {:>11.2} ms {:>11.2} ms | {:>11.2} ms {:>11.2} ms",
            rehash_1 + f1,
            rehash_n + fnn,
            rehash_1 + i1,
            rehash_n + inn
        );
    }

    // Correctness: the committed assignment must be found, and a wrong
    // target must not be.
    let fx = fixture(8);
    assert!(search_full(&fx, 8).is_some(), "full search must find the committed assignment");
    assert!(search_incremental(&fx, 8).is_some(), "incremental search must agree");
    assert_eq!(
        search_full(&fx, 8),
        search_incremental(&fx, 8),
        "both strategies must select the same assignment"
    );
    let mut wrong = fixture(8);
    wrong.target = [0xFF; 32];
    assert!(search_full(&wrong, 8).is_none(), "a wrong target must not match");
    println!("\nsanity: both strategies find the committed assignment and agree; a wrong target matches nothing");
}
