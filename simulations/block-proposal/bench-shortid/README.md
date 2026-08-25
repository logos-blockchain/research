# bench-shortid

Measures candidate keyed hash functions for the 64-bit transaction short IDs of
the Revised Block Proposal Compression RFC (BIP-152-style compact proposals).

Every validator recomputes `shortid(key, mantle_txhash)` over its whole mempool
once per received proposal (the key is proposal-specific), so the operational
number is `mempool_size × per-hash cost` on 32-byte inputs. That is what this
binary measures — not bulk-data throughput, which favors different functions.

Candidates (pure-Rust implementations only):

* **SipHash-2-4** (`siphasher`) — what BIP-152 uses
* **SipHash-1-3** (`siphasher`) — the faster variant used by Rust's std `HashMap`
* **Blake2b-512 truncated to 8 bytes** (`blake2`) — key absorbed as an input
  prefix; the shape closest to reusing logos-blockchain's existing
  `Hasher = blake2::Blake2b<U32>`
* **Blake2bMac with 8-byte output** (`blake2`) — Blake2b's native keyed mode

`blake2b_simd` was intended as the SIMD-tuned Blake2b upper bound but is
unbuildable from crates.io at the time of writing: every version matching its
`arrayref ^0.3.5` requirement is yanked.

## What is measured

Three figures per candidate, all medians of 5 runs over deterministic inputs:

1. **cache-resident ns/hash** — a 4,096-entry set (128 KB) cycled in L1/L2,
   isolating the cost of the hash function itself.
2. **single-core ns/hash and total** — one pass over a real 10^6-entry array
   (30 MB), so the mempool total is *measured*, not extrapolated from (1).
   The gap between (1) and (2) is the memory cost a micro-benchmark hides.
3. **multi-core ns/hash, total and speedup** — the same pass partitioned
   across `available_parallelism()` cores with `std::thread::scope`. The
   rehash is embarrassingly parallel — every transaction is independent — so
   this is what a validator that threads the work would see.

Hashing only: the map insert that a real `resolve_candidates` performs per
transaction is not included, so these are lower bounds on the full step.

## Run

```
cargo run --release
```

Results are archived under `results/<host>-<date>-runN.txt`; the ones checked
in were produced on an Apple M4 Pro (14 cores, Darwin arm64, rustc 1.97.1).

## Summary

See `reports/block-proposal/SipHash-vs-Blake2b-Short-IDs.md` for the analysis
and the recommendation (SipHash-2-4).
