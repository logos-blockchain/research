# SipHash vs Blake2b for keyed transaction short IDs

**Decision input for the Revised Block Proposal Compression RFC.**
Benchmark: `simulations/block-proposal/bench-shortid` (pure-Rust crates only).
Host: Apple M4 Pro, Darwin arm64, rustc 1.97.1. 2026-08-20.

## Question

The revised proposal replaces the 16-byte unkeyed transaction-hash prefixes of
the current RFC with BIP-152-style **keyed 64-bit short IDs**:
`shortid = H_key(mantle_txhash)`, with a proposal-specific key that is
unpredictable before the proposal exists. The security argument moves from the
hash's length to the key's freshness, which is what lets the reference shrink
from 16 bytes to 8.

The cost profile also changes: short IDs cannot be cached across blocks
(the key changes every block — that is the point), so **every validator
recomputes the short ID of every mempool transaction once per received
proposal**. The candidate hash is evaluated on that workload: keyed hashing of
32-byte inputs (the full transaction hash), `M` times per proposal, where `M`
is the mempool size. BIP-152 uses SipHash-2-4 for exactly this role; the
codebase's existing hash is Blake2b (`crypto.rs`:
`pub type Hasher = blake2::Blake2b<U32>`). The question is whether reusing
Blake2b is worth it, or whether SipHash earns its place as a second primitive.

## Results

Median of 5 runs × 2,000,000 hashes, 32-byte inputs, three archived runs
(`results/mac-m4pro-20260820-run{1,2,3}.txt`, spread < 7%):

| Function | ns/hash | Mh/s | mempool M = 10⁵ | mempool M = 10⁶ |
| --- | ---: | ---: | ---: | ---: |
| **SipHash-2-4** (`siphasher`) | **13.0** | **77** | **1.3 ms** | **13 ms** |
| SipHash-1-3 (`siphasher`) | 6.5 | 153 | 0.7 ms | 6.5 ms |
| Blake2b-512/trunc8 (`blake2`) | 81–86 | 12 | 8.1 ms | 81–86 ms |
| Blake2bMac-8 keyed (`blake2`) | 159 | 6.3 | 15.9 ms | 159 ms |

Two observations that will replicate on any host:

* **SipHash-2-4 is ~6.4× faster than the best Blake2b shape.** SipHash's whole
  state is four 64-bit words updated with ARX operations; a 32-byte input is
  4 rounds of message absorption plus finalization. Blake2b pays a full
  1-block compression (12 rounds over a 128-byte block) regardless of how
  short the input is. The ratio is architectural, not an artifact of this CPU.
* **Blake2b's *proper* keyed mode is the worst option, not the best.** With a
  16-byte key and a 32-byte message, `Blake2bMac` processes the padded key
  block *and* the message block — two compressions — whereas absorbing the key
  as an input prefix fits key+message into one 128-byte block. Reusing the
  codebase's Blake2b in MAC form doubles the cost of an already-slow option.

`blake2b_simd` (SIMD-tuned Blake2b) could not be included: every version of
its `arrayref ^0.3.5` dependency is currently yanked from crates.io, so the
crate does not build. Its own published numbers put single-input short-message
latency in the same order as RustCrypto's `blake2`; it would not close a 6×
gap that comes from compression-block granularity.

## Interpretation

**Defender's cost.** At M = 10⁶ mempool transactions, the per-proposal rehash
is 13 ms with SipHash-2-4 against 81–86 ms with the best Blake2b variant — on
a fast desktop core. On modest validator hardware (×3–5), Blake2b lands in the
250–400 ms range per proposal, which starts to matter under adversarial
conditions: an equivocating leader can emit several distinct valid proposals
for one slot, each triggering a fresh rehash (each has a distinct `block_id`,
so duplicate suppression does not collapse them). SipHash keeps even that
worst case in the tens of milliseconds.

**Attacker's cost is not lowered by picking the faster hash.** To grind a
transaction whose short ID collides with a referenced one, an attacker must
produce a *new valid transaction* per attempt — each attempt pays a Blake2b
hash of the whole transaction (`mantle_txhash`) before the SipHash evaluation
even happens. The attacker's cost is dominated by the transaction hash we
already have; the defender's cost is dominated by the short-ID hash, which is
the one being chosen here. The asymmetry means choosing the fast function for
short IDs speeds up the defender ~6× while leaving the attacker's grind cost
essentially unchanged.

**Security margin.** A 64-bit keyed tag is not, and does not need to be, a
collision-resistant hash. The RFC's security argument is that the key does not
exist before the proposal does, so no useful precomputation is possible, and
the post-broadcast window (propagation, seconds) is far too short for the
2⁶⁴/N targeted grind. What the tag function must provide is PRF security — no
way to predict or bias outputs without the key. SipHash-2-4 was designed as
exactly this: a keyed PRF for short inputs, built to stop hash-flooding DoS —
the same attack shape this RFC defends against — and its best published
distinguishers do not reach the full 2-4 rounds. SipHash-1-3 (2× faster
still) is what Rust's own `HashMap` ships, but its margin is thinner and the
13 ms full-mempool cost of 2-4 leaves no performance reason to spend that
margin. BIP-152's field record — a decade of SipHash-2-4 short IDs at 48 bits
without a practical break of the mechanism — is directly transferable, and we
run it at 64 bits.

## Recommendation

**SipHash-2-4**, keyed with `(k0, k1)` = the first 16 bytes of a
domain-separated Blake2b hash of proposal-header fields (so Blake2b remains
the only *cryptographic* primitive; SipHash is a performance component keyed
from it, exactly as in BIP-152, which derives its SipHash keys from SHA256 of
the header). Use the full 64-bit output as the short ID — no truncation, so
the ID is a native little-endian `u64` on the wire.

Costs at the recommended parameters, per received proposal: builder ~M
SipHashes once at construction; validator ~M SipHashes plus one `u64`-keyed
hash-map build; 1024 lookups for resolution. All well under the existing
per-proposal verification budget (a single Groth16 PoL verification costs more
than the entire M = 10⁵ rehash).

## Caveats

* Single host (Apple M4 Pro, aarch64). The 6× ordering is architectural (see
  above) and will hold on x86-64; absolute times scale with the core.
* Pure-Rust implementations only, per the task constraint: `siphasher` 1.0.3 and
  `blake2` 0.10.6 (RustCrypto — the crate logos-blockchain already uses), pinned by
  the committed `Cargo.lock`.
* Measured on 32-byte inputs only. Hashing raw transactions instead of their
  hashes would flip nothing (it makes Blake2b relatively worse, multi-block),
  and the RFC hashes `mantle_txhash`, which is cached in every mempool.
