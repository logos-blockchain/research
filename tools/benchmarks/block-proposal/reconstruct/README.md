# reconstruct

Measures the **complete** block-proposal reconstruction step of the Revised
Block Proposal Compression RFC, end to end. Nothing is estimated: every phase
runs for real, including genuine Blake2b Merkle roots over `MAX_BLOCK_TXS`
full transaction hashes.

The companion `shortid` benchmark measures the hash function alone. This one
measures what a validator actually spends per proposal.

## What it runs

1. Derive the per-proposal reference key from the header.
2. **Phase A** — rehash the entire mempool under that key and index it by
   short ID.
3. Resolve each of the 1024 references to its candidate set.
4. **Phase B** — search up to `MAX_RECONSTRUCTION_COMBINATIONS` assignments,
   computing `body_root(uncle_headers, assignment)` for each and comparing it
   against the committed root.

Phase B is swept over `C ∈ {1, 2, 8, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192}` — far past
`MAX_RECONSTRUCTION_COMBINATIONS = 64`, so the cost of a different cap can be
read off rather than guessed — and always measured in the **worst case**: the
timed search runs against an unmatchable target, so all `C` assignments are
evaluated regardless of enumeration order. Any search that matches is strictly
cheaper. Correctness is checked separately at every sweep point, with the real
target restored: all three strategies must find the committed assignment and
agree on which it is.

Two search strategies are compared, because the spec asserts one is much
cheaper:

* **full** — recompute the whole Merkle root for every assignment.
* **incremental** — build the tree once, then recompute only the leaf paths the
  assignment changes. Assignments are enumerated in **Gray code** order, so
  consecutive ones differ in exactly one leaf and the spec's "one leaf path
  recomputation each" is literally true; binary counting would average two.

Both are measured single-core and across `available_parallelism()` cores.

## Caveats

* Phase A uses a plain `HashMap<u64, Vec<u32>>`, which allocates a `Vec` per
  distinct short ID. That is the naive implementation, not a tuned one; a real
  node would avoid the per-entry allocation and use a faster hasher for `u64`
  keys. Phase A is therefore an upper bound on the index-building cost, and
  the gap against the `shortid` benchmark's hashing-only figure is the cost of the
  map, not of the hash.
* `mantle_txhash` is assumed already cached per mempool entry, as it is in a
  real mempool.
* Two hosts are checked in: a Raspberry Pi 5 (4× Cortex-A76), which stands in
  for validator-class hardware, and an Apple M4 Pro (14 cores) for contrast.
  Nothing is scaled between them.

The Pi run is the one that matters, and it says something the workstation run
hides: the index, not the hash, is the majority of Phase A there — 440 ms of
657 ms, against 52 ms of 132 ms on the M4 Pro. The map degrades worse than the
hash on modest hardware (5.0× slower per core, against 2.7× for hashing
alone), so a faster hash buys proportionally less than the hash benchmark
alone would suggest.

## Run

```
cargo run --release
```

Results are archived under `results/<host>-<date>-runN.txt`.
