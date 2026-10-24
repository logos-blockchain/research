# pq-da benchmarks

Measurements quoted in `../README.md` (recommended design, measured costs).

- `hash-da/` — prototype of the proposed scheme: rows RS-extended (rate 1/2) over Goldilocks with
  plonky3 0.7 (`Radix2DitParallel`), BLAKE2b-256 Merkle tree over the 2048 columns, Fiat–Shamir
  challenge in F_{p^2}, published check row. `cargo run --release -- 256 1024 4096` (blob sizes in KiB).
- `kzg-da/` — the first design (spec 148) built from the old `nomos-da/kzgrs` crate at
  logos-blockchain commit 16e93f6 (arkworks 0.4 + blst, BLS12-381, 31-byte chunks, FK20 column
  proofs). `cargo bench --bench da_pipeline [--features parallel] --no-run`, then run the binary
  under `target/release/deps/da_pipeline-*` with the blob sizes. The SRS is random (dev only).

Both use K = 1024 original columns, N = 2048 extended columns (= subnetworks). Timings are medians
of 3–5 encodes; per-column verification is averaged over 100–2000 columns.
