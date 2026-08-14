# Choosing `REFERENCE_PREFIX_LENGTH` from measurement

**Subject:** the reference prefix length for the compressed block proposal, [logos-lips#389].
**Question:** is 16 bytes too conservative, and what does the measured data say the parameter should be?
**Answer in one line:** the data supports **16 bytes**; the crossover where the attack stops being economically rational sits between 14 and 16, and 14 is affordable at roughly $4k of rented GPU time.

Everything below is measured against the real `logos-blockchain` code at commit
[`40e76c8`], not a model of it. The benchmark suite is in
[`tools/benchmarks/reference-prefix`](../../tools/benchmarks/reference-prefix/),
and every number in this report can be re-derived by running it.

> **Status of the RPi5 columns.** macOS (Apple M3) is the development baseline
> and is complete. The Raspberry Pi 5 is the target validator class and its
> numbers are what the recommendation must ultimately rest on; those cells are
> marked **_(pending)_** and are filled by running the identical suite on the
> Pi. The conclusion below is stated in a form that the RPi5 data can only
> **strengthen**, because the Pi is slower than the M3 on the defending side —
> see [what the RPi5 data will change](#what-the-rpi5-data-will-change).

---

## 1. Threat model

Two costs set this parameter and they must be priced separately, because they
differ by many orders of magnitude and only one of them is a real bound.

### 1a. Generation — the cost that sets the prefix length

An adversary grinds candidate transactions locally and computes
`prefix(mantle_txhash(tx), L)` for each. This is **offline** and needs no
signature, proof, network, or stake, because of a specific property of the hash:

```rust
// core/src/mantle/transactions/mantle_tx.rs
impl Hashable for RawMantleTx {
    const HASHER: hashable::Hasher<Self> = |tx| {
        let bytes: [u8; 32] = Hasher::digest(tx.as_signing()).into();
        TxHash::from(bytes)
    };
    fn as_signing(&self) -> Vec<u8> {
        let mut buffer = MANTLE_TX_HASH_V1_BYTES.to_vec();  // b"MANTLE_TXHASH_V1"
        buffer.extend(self.encode());                        // the MantleTx only
        buffer
    }
}
```

`mantle_txhash` covers the `MantleTx` and **not** the `op_proofs`. So the cost
of one candidate is *encode + Blake2b-256* — no cryptography beyond a hash.
Measured below at **6.19 × 10⁶ candidates/s on a single M3 core**, which is
within 3% of the machine's raw Blake2b rate. Grinding candidates *is* hashing.

The relevant event is a **birthday self-collision**: any two of the adversary's
own candidates sharing a prefix. They need no fixed target, so this costs
≈ 2^(b/2), not the ≈ 2^b of a targeted match. This is the quantity that governs
`L`, and [§3](#3-the-birthday-model-is-measured-not-assumed) measures that the
model is correct rather than assuming it.

### 1b. Propagation — noted, then set aside

To do damage, the colliding candidates must reach validators' mempools. It is
tempting to treat mempool ingest throughput as a protective bound. **We
deliberately do not**, because it is not one: an adversary can precompute
candidates offline and inject them from many nodes in parallel, so the ceiling
is their node count and bandwidth, not any single node's ingest rate. Treating
a per-node figure as a global bound would overstate the margin.

The generation argument in this report therefore stands **on its own**.
Propagation only makes the attack easier than generation alone implies.

### 1c. Success condition

Cause reconstruction ambiguity on an **honest** proposal: place two
transactions sharing a referenced prefix into a validator's mempool, so one
reference resolves to two candidates. Then scale it until the validator either

* exceeds the block-production interval (the slot) while searching, or
* trips a cap and drops the honest proposal outright.

Both are liveness failures. Neither is a safety failure: `header.block_root`
commits to the **full** 32-byte hashes, so a wrong resolution cannot be accepted
as a valid block — it can only waste time or fail.

One step is required that the cost tables below do not price. A self-collision
gives the adversary two transactions, A and B, sharing a prefix; both go into
mempools, and the reference only becomes ambiguous once an honest proposer
includes **one of them** in a block. So the adversary must also get their
transactions selected, which means paying fees and competing for block space.
This is a **linear** overhead — generate somewhat more than `k` pairs, pay `k`
transactions' worth of fees — against an attack whose generation cost is
exponential in `L`. It shifts none of the conclusions, and it is omitted from
the tables precisely so the generation bound stands unaided.

---

## 2. What the code actually does

Four facts from the implementation shape everything that follows.

**The hash is Blake2b-256** (`core/src/crypto.rs`: `pub type Hasher = blake2::Blake2b<U32>`).

**The merged implementation is at 8 bytes, not 16.**

```rust
// core/src/mantle/transactions/hash.rs
const REFERENCE_PREFIX_BYTES: usize = 8;
```

The specification PR argues for 16; the code on `master` is at 8. That gap is
the single most urgent finding here, because [§5](#5-the-cost-of-manufacturing-a-collision)
prices an 8-byte prefix at **under a second of GPU time** per colliding pair.

**Reconstruction is a cartesian-product search.** From
`services/chain/chain-network/src/lib.rs`:

```rust
candidates
    .into_iter()
    .multi_cartesian_product()
    .find_map(try_rebuild_with_txs)
    .ok_or(Error::NoMatchingReconstruction)
```

with two caps applied before the search starts:

```rust
// core/src/block/mod.rs
pub const MAX_CANDIDATES_PER_REFERENCE: usize = 8;
pub const MAX_RECONSTRUCTION_COMBINATIONS: usize = 32;
```

Note that #389 v3 argues these can be **deleted**, on the grounds that at 16
bytes ambiguity cannot be manufactured at all. Both policies are measured
separately in [§6](#6-reconstruction-latency-the-defenders-side).

**Each combination re-hashes the whole block.** `Block::reconstruct` validates
the size of every transaction and then recomputes the Merkle root, and
`calculate_block_root` hashes every transaction from scratch on every call:

```rust
// core/src/utils/merkle.rs
let mut leaves: Vec<_> = transactions.iter().map(Hashable::hash).collect();
```

So per-combination cost is O(n) in the block's transaction count, not O(1).
This is why the defender's curve is so much steeper than the attacker's.

**The slot is 1 second** (`DEFAULT_SLOT_TIME_IN_SECS = 1`, matching
`slot_duration: '1.000000000'` in the standalone deployment config). That is
the deadline reconstruction must fit inside.

---

## 3. The birthday model is measured, not assumed

The whole parameter choice rests on the claim that *any* two colliding
candidates cost ≈ 2^(b/2). Rather than assert it, the harness grinds real
`mantle_txhash` output at prefix lengths short enough to collide in seconds and
compares the observed count against the prediction
sqrt(π/2) · 2^(b/2) ≈ 1.2533 · 2^(b/2).

**mac** — 24 trials per row:

| prefix | b (bits) | predicted N | measured N | ratio ± SE |
|---|---|---|---|---|
| 2 B | 16 | 321 | 349 | 1.088 ± 0.092 |
| 3 B | 24 | 5,134 | 4,948 | 0.964 ± 0.100 |
| 4 B | 32 | 82,137 | 84,013 | 1.023 ± 0.104 |
| 5 B | 40 | 1,314,195 | 1,104,775 | 0.841 ± 0.107 |

Every ratio is consistent with 1.0 within ~1.5 standard errors, across 24 bits
of doubling. The first-collision distribution is strongly right-skewed, so this
spread is expected; the standard error is what matters, and it is reported
rather than hidden. **The 2^(b/2) model holds on real transaction hashes**, so
extrapolating to b = 64 and b = 128 needs only the grinding rate.

_(RPi5 rows: **_(pending)_** — the model is hardware-independent, so these are a
cross-check, not an input to the decision.)_

---

## 4. Candidate-generation rate (R_gen)

Three rates, because the difference between them is itself the point.

| machine | node path | attacker (patched) | raw Blake2b | aggregate (all cores) |
|---|---|---|---|---|
| **mac** (Apple M3, 4P+4E) | 2.42 × 10⁶ /s | **6.19 × 10⁶ /s** | 5.89 × 10⁶ /s | **3.34 × 10⁷ /s** (8 threads, 5.39×) |
| **rpi5** | _(pending)_ | _(pending)_ | _(pending)_ | _(pending)_ |

Sample transaction: the smallest valid `MantleTx` — a single `Transfer`, one
input, one output — **76 bytes encoded, 92 bytes hashed** including the
16-byte domain prefix. Larger transactions hash slightly slower, so this is the
adversary-favourable choice; at 92 bytes the preimage still fits in a single
Blake2b compression, so a 2× larger transaction would cost roughly 2×.

* **node path** builds the operation structure and reallocates per candidate —
  what a node does per transaction.
* **attacker (patched)** encodes once and overwrites only the varying bytes.
  This is the rate the security margin is computed from, because no adversary
  would do more work than this. `cargo test` asserts byte-for-byte that it
  produces the same hashes as the real path.
* **raw Blake2b** is the bare hash over a buffer of the same size, with no
  transaction work at all. The attacker path and the bare hash are within 3% of
  each other — indistinguishable at this measurement's precision. That is the
  substantive result: **grinding candidates is pure hashing**, the transaction
  machinery contributes nothing measurable once the encoding is hoisted out of
  the loop, and there is no software headroom left for a defender to rely on.

Aggregate scaling is **measured, not multiplied**: 8 threads on the M3 give
**5.39×**, not 8×, because four of those cores are efficiency cores. Assuming
linear scaling would have understated the time an adversary needs by about 48%
— in the direction that flatters the defender, which is the wrong way to be
wrong.

---

## 5. The cost of manufacturing a collision

Candidates needed for one colliding pair, and the wall-clock at each rate.
GPU column assumes an **RTX 4090 at 10¹⁰ H/s** — the figure #389 argues from,
and roughly 2× above published hashcat Blake2b throughput for a single 4090, so
deliberately generous to the attacker. Parallel collision search
(van Oorschot–Wiener) is memoryless and embarrassingly parallel, so aggregate
hash rate is the honest cost basis and a 100-GPU farm really is 100× faster.

| L (bytes) | b (bits) | candidates N | 1 core (mac) | 1 machine (mac) | 1 GPU (RTX 4090) | 100 GPUs |
|---|---|---|---|---|---|---|
| **8** | 64 | 5.38 × 10⁹ | 14.5 min | 2.9 min | **0.54 s** | 5 ms |
| **10** | 80 | 1.38 × 10¹² | 3 days | 12.5 h | 2.3 min | 1.4 s |
| **12** | 96 | 3.53 × 10¹⁴ | 659 days | 133 days | 9.8 h | 5.9 min |
| **14** | 112 | 9.03 × 10¹⁶ | 462 years | 93 years | 105 days | 25.1 h |
| **16** | 128 | 2.31 × 10¹⁹ | 118,000 years | 23,800 years | **73 years** | 268 days |

_(RPi5 columns are omitted deliberately: an adversary is not going to grind on a
Pi. Pricing the generating side with strong hardware is the conservative
direction, and the RPi5's role in this report is as the **defender**.)_

### Consistency with #389

#389 states 16 bytes gives "about 58 years on one GPU at 10¹⁰ H/s, ~214 days
against a 100× adversary". Those are 2^64 / rate exactly. This report gets
**73 years** and **268 days** because it includes the sqrt(π/2) ≈ 1.2533 factor
in the expected first-collision count — validated empirically in §3.

**This is a refinement in the safe direction, not a contradiction**: #389's
figures are ~22% *lower* than the corrected ones, i.e. #389 slightly
understates the attacker's cost. No revision to #389's conclusion is needed, but
if those two numbers are quoted anywhere normative they should become 73 years
and 268 days.

---

## 6. Reconstruction latency — the defender's side

This is where the asymmetry lives. Manufacturing `k` colliding pairs costs the
attacker only ~sqrt(k) times one pair, because collisions accumulate as N²/2^(b+1)
as the search runs. An **uncapped** validator must walk ∏|Cᵢ| = 2^k combinations,
each of which re-encodes and re-hashes every transaction in the block.

![Reconstruction latency vs. collision multiplicity](figures/reconstruction-latency.png)

**mac** (Apple M3), full block of 1024 transactions, uncapped policy:

| k | combinations | median | vs. 1 s slot |
|---|---|---|---|
| 0 | 1 | 1.4 ms | within |
| 4 | 16 | 17 ms | within |
| 6 | 64 | 68 ms | within |
| 8 | 256 | 286 ms | within |
| 9 | 512 | 559 ms | within |
| **10** | **1,024** | **1.19 s** | **over slot** |
| 12 | 4,096 | 4.5 s | over slot |
| 15 | 32,768 | 35.5 s | over slot |

Per-combination cost ≈ **1.2 ms** at n = 1024 and ≈ **190 µs** at n = 128,
scaling with block size as the O(n) re-hash predicts. A 128-transaction block
crosses the slot at k = 13 instead of k = 10. Note what the k = 0 row means in
isolation: with no ambiguity at all, reconstruction costs 1.4 ms against a
1,000 ms budget, so normal operation has roughly **700× of headroom**. The
entire risk is in how fast that headroom is consumed — one doubling per
colliding pair.

**rpi5**: **_(pending)_** — paste the `results/rpi5/reconstruction.csv` rows here.
Expect the crossover at a **lower** k, since the per-combination cost is higher.

### The two policies differ in failure mode, not in whether they fail

| | uncapped (#389 v3) | capped (merged today) |
|---|---|---|
| k ≤ 5 | searches, ≤ 34 ms | identical — searches |
| k ≥ 6 | searches, cost doubles per k | **refuses instantly**, drops the proposal |
| failure at scale | slot overrun → block production stalls | honest proposal discarded → block lost |

The caps bound CPU cost but do not remove the liveness failure — they convert a
slow reconstruction into a dropped honest block, and they do so at **k = 6**,
which is *cheaper for the attacker* than the k = 10 needed to stall the M3.
So the caps do not soften the requirement on `L`; if anything they tighten it.

Either way the conclusion is the same: **`L` must be large enough that
manufacturing ~6–10 collisions is infeasible.** That requirement is robust to
which policy ships, which is what makes it a sound basis for the parameter.

---

## 7. Decision table

Cost to manufacture enough colliding pairs to break one validator, at
$0.50/GPU-hour on the RTX 4090 assumption above. `k` is taken from the measured
crossover in §6; the sqrt(k) scaling means the choice of `k` moves these numbers
far less than the choice of `L` does.

| L (bytes) | proposal max | vs. master | GPU-hours, 1 pair | $ for 1 pair | $ to stall **mac** (k=10) | $ to stall **rpi5** | pairs $10k buys |
|---|---|---|---|---|---|---|---|
| **8** | 8,555 B | 3.87× | ~0 | <$0.01 | **<$0.01** | _(pending)_ | 1.8 × 10¹⁶ |
| **10** | 10,603 B | 3.12× | 0.04 | $0.02 | **$0.06** | _(pending)_ | 2.7 × 10¹¹ |
| **12** | 12,651 B | 2.62× | 9.8 | $4.90 | **$15.49** | _(pending)_ | 4.2 × 10⁶ |
| **14** | 14,699 B | 2.25× | 2,509 | $1,254 | **$3,966** | _(pending)_ | **64** |
| **16** | 16,747 B | 1.98× | 642,210 | $321,105 | **$1.0M** | _(pending)_ | **0.001 — not even one** |

The last column is the clearest statement of the margin: how many colliding
pairs a $10,000 adversary can afford, against the **10** they need. It is the
same data as the `$ to stall` column, inverted, and it locates the crossover
without needing a judgement call — **L = 16 is the first row where a serious
budget cannot buy even a single collision**, and L = 14 is the last row where it
buys six times more than the attack requires.

Two independent checks that the size column is right: at L = 8 it reproduces
**8,555 bytes**, the value pinned in the implementation's own
`maximum_proposal_matches_the_specified_size` test; at L = 16 it reproduces
**16,747 bytes**, the figure in #389. The compression ratio is against master's
33,129-byte fixed proposal.

### What the RPi5 data will change

The pending cells move the argument in one direction only. The RPi5's
per-combination cost is higher than the M3's, so its slot crossover `k` is
**lower**, so the `$ to stall rpi5` column will be **lower** than the mac
column at every `L` — the attack gets *cheaper*, never dearer. The RPi5 data can
therefore strengthen the case for a longer prefix but cannot weaken it. The
recommendation below is safe to act on now and should be re-checked, not
re-derived, once the Pi numbers land.

---

## 8. Recommendation

**Keep `REFERENCE_PREFIX_LENGTH = 16`, and raise the implementation from 8 to
match.**

The crossover sits between 14 and 16:

* **L ≤ 12 is not defensible.** At 12 bytes, stalling a validator costs about
  **$15** of rented GPU time. At 8 bytes — *what is merged today* — it costs
  less than a cent and takes under a second per pair.
* **L = 14 is affordable to a motivated adversary.** ~$4k for a sustained stall
  is within reach of anyone with a reason to censor, and a $10k budget buys 64
  colliding pairs where 10 suffice — a 6× surplus, not a margin. It also has no
  headroom against hardware improvement: this parameter is a consensus constant
  that will outlive several GPU generations, and every 4× improvement in hash
  rate cuts that figure fourfold.
* **L = 16 is where the attack stops being rational.** 73 GPU-years for a single
  pair, ~$1M for a sustained stall, and 268 days even for a 100-GPU adversary.

The cost of that choice is modest and bounded: 16,747 bytes versus 14,699 at
L = 14 — **2 KB on the maximum proposal**, still a 1.98× reduction against
master's 33,129 bytes. Trading a further 12% of compression for a ~250× increase
in attack cost is the right side of that curve.

### On "16 is too conservative"

The reviewer's instinct is reasonable and the measurements do partly support it:
the *targeted* 2^128 framing does overstate the threat, and 14 bytes is not
absurd. But the birthday cost is the one that binds, and at 14 bytes it lands at
a few thousand dollars — close enough to the affordable range that it leaves no
headroom for a better GPU, a cheaper spot price, or a smarter grinding loop. The
margin at 16 costs 2 KB; the margin at 14 costs a re-run of this analysis every
time hardware moves.

**`L` can always be shortened later** if the analysis supports it — shortening
is a clean parameter change. Lengthening it after mainnet is a breaking wire
change under adversarial pressure. Being conservative now is cheap; being wrong
later is not.

### Action items

1. **Raise `REFERENCE_PREFIX_BYTES` from 8 to 16** in
   `core/src/mantle/transactions/hash.rs`. The merged implementation is
   currently at the one value this analysis rules out outright. This is the
   highest-priority item in this report.
2. **Correct the two figures in #389** from 58 years / 214 days to **73 years /
   268 days** (§5). Same conclusion, arithmetic that survives review.
3. **Decide the cap question explicitly.** #389 v3 deletes
   `MAX_RECONSTRUCTION_COMBINATIONS` and `MAX_CANDIDATES_PER_REFERENCE`; they are
   still in the merged code. At L = 16 either is defensible, but the spec and the
   implementation should not disagree about which. Note that keeping the caps
   means a `k = 6` collision set drops honest proposals, which is *cheaper* to
   provoke than the `k = 10` stall — so if they stay, they should be documented
   as a liveness trade rather than a DoS defence.
4. **Re-run on the RPi5** and fill the pending columns before this is treated as
   final.

---

## Appendix — reproducing this

```bash
cd tools/benchmarks/reference-prefix
./scripts/run_all.sh mac      # or: rpi5
python3 scripts/analyse.py    # regenerates every table and the figure above
```

Assumptions, all changeable at the top of `scripts/analyse.py`: GPU model and
hash rate (`RTX 4090`, 10¹⁰ H/s), GPU price ($0.50/hour), and the proposal
layout constants. Hardware and toolchain for each run are recorded in
`results/<machine>/machine.txt` and `toolchain.txt`.

Measured on: Apple M3, 8 cores (4P + 4E), 16 GB, macOS 25.3.0, rustc 1.97.1.

[logos-lips#389]: https://github.com/logos-co/logos-lips/pull/389
[`40e76c8`]: https://github.com/logos-blockchain/logos-blockchain/commit/40e76c8e32934f14c3370621db9bda9f14d50dc7
