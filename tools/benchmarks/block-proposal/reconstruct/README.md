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

Phase B is swept over `C ∈ {1, 2, 8, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192}` — up to
`MAX_RECONSTRUCTION_COMBINATIONS = 8192` itself, so the chosen cap and any
alternative below it can be read off rather than guessed — and always measured in the **worst case**: the
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

**Phase C — equivocation.** Because the reference key derives from
`(parent, slot, leader_key, entropy_contribution)` and not from the proposal,
every variant a leader mints within one slot shares a key, so the short-ID
index is a pure function of (key, mempool) and can be reused across all of
them. Phase C measures E variants both ways — rebuilding the index per variant
against building it once and sharing it — and asserts the reuse is *correct*,
not merely faster: every variant must still resolve to its own committed
assignment from the single shared index.

## Caveats

* Phase A uses a plain `HashMap<u64, Vec<u32>>`, which allocates a `Vec` per
  distinct short ID. That is the naive implementation, not a tuned one; a real
  node would avoid the per-entry allocation and use a faster hasher for `u64`
  keys. Phase A is therefore an upper bound on the index-building cost, and
  the gap against the `shortid` benchmark's hashing-only figure is the cost of the
  map, not of the hash.
* **Phase A stops the clock before the index is dropped**, so it measures the
  build alone. Phase C includes the drop, and freeing a 10⁶-entry map with a
  `Vec` per entry is not free: Phase C at E = 1 exceeds Phase A by 12% on an
  M4 Pro and by 24% single-core on a Pi 5 (57% across its four). **Phase C at
  E = 1 is therefore the figure to quote for a complete reconstruction**, and
  the Phase A + Phase B totals understate it by that margin. Both numbers are
  wanted, so Phase A is left as it is: a validator that caches the index pays
  the build and not the teardown, one that does not pays both.
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
