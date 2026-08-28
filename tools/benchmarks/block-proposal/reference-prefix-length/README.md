# Block proposal compression — benchmark suite

Measurements behind the choice of `REFERENCE_PREFIX_LENGTH` for the compressed
block proposal ([logos-lips#389]). The report that reads these results is
[`reports/block-proposal/reference-prefix-length.md`](../../../../reports/block-proposal/reference-prefix-length.md),
and its **Notation and terms** section defines every symbol used below
(`L`, `k`, `b`, `n`, `R_gen`).

The crate is named `reference-prefix-bench` because that is what it measures;
the directory is named for the wider topic, so further block-proposal
tools can sit beside it later.

Everything here runs the **real `logos-blockchain` code**, pinned by commit in
`Cargo.toml` — the Mantle transaction encoding, `mantle_txhash` (Blake2b-256),
the Merkle `block_root`, and `Block::reconstruct`. Nothing is reimplemented, so
a rate measured here is a rate the protocol actually achieves. The two places
where the harness supplies its own code rather than calling the node's are
documented inline in `src/lib.rs` and repeated under
[What is real and what is not](#what-is-real-and-what-is-not).

## What gets measured

| Binary / bench | Question it answers |
|---|---|
| `bench candidate_generation` | **R_gen** — how fast can one core turn out candidate transactions reduced to a prefix? |
| `bin throughput` | How does that rate scale across a whole machine? (measured, not multiplied) |
| `bin birthday` | Does the 2^(b/2) birthday model actually hold on real `mantle_txhash` output? |
| `bin reconstruction` | How does a validator's reconstruction latency grow with the number of ambiguous references, and where does it cross the slot deadline? |

## Requirements

* Rust **1.97.1** — pinned in `rust-toolchain.toml`, installed automatically by
  `rustup` on first use.
* A C toolchain and `git` (transitive crates build C).
* Roughly 3 GB of disk for the dependency build, and ~10 minutes for the first
  compile on an RPi5.

No binaries are shipped. Each machine builds from source, from the same pinned
sources, so the comparison is like-for-like.

## (a) macOS — development and validation

```bash
brew install rustup git          # if not already present
rustup-init -y                   # then restart the shell

cd tools/benchmarks/block-proposal/reference-prefix-length
make check     # read-only: what's installed, what's missing
make test      # the gate — asserts the harness matches the real code path
make run       # the full suite -> results/mac/
```

Results land in `results/mac/`.

## (b) Raspberry Pi 5 — the numbers that decide the parameter

The RPi5 is the target validator class, so its reconstruction latency is what
the recommendation is based on. macOS is a development baseline only.

```bash
sudo apt-get update
sudo apt-get install -y build-essential git curl

# rustup, not the distro's rustc: the toolchain must match the pin.
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

git clone https://github.com/logos-blockchain/research.git
cd research/tools/benchmarks/block-proposal/reference-prefix-length   # or: git pull, if already cloned

make check
make run       # MACHINE is detected as rpi5; results land in results/rpi5/
```

Results land in `results/rpi5/`. Commit that directory and the report tables
pick the numbers up.

For a quieter measurement, pin the governor to `performance` first and let the
board settle — an RPi5 under a passive heatsink will thermally throttle during
the longer reconstruction runs, which shows up as a widening gap between the
`min_s` and `max_s` columns:

```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
vcgencmd measure_temp     # keep an eye on this across the run
```

## Reading the results

```bash
make analyse                          # tables + plot, from whatever is in results/
make figures                          # analyse, then copy the plot into the report
```

The analysis needs `matplotlib` for the plot and is meant to run on the
development machine, not the Pi. Recent Pythons refuse a global `pip install`
(PEP 668), so `make venv` builds a local one; every later `make analyse` picks
it up automatically:

```bash
make venv
make analyse
```

Without it the tables still print and only the figure is skipped.

`make help` lists every target, and `make where` prints the exact results and
report directories this tool reads and writes.

It writes the report's cost tables to stdout and the latency plot to
`results/reconstruction-latency.png`. Without `matplotlib` it still prints every
table and simply skips the figure.

## Output layout

```
results/
  mac/
    machine.txt                 label, date, CPU, core count
    toolchain.txt               rustc / cargo versions actually used
    candidate_generation.txt    raw criterion output
    throughput.csv              aggregate candidates/s vs thread count
    birthday.csv                predicted vs measured first-collision counts
    reconstruction.csv          latency vs k, both policies, both block sizes
  rpi5/
    ...same files...
```

## What is real and what is not

Real, called directly from `logos-blockchain`:

* `RawMantleTx` construction and its canonical encoding.
* `mantle_txhash` — `blake2b-256(b"MANTLE_TXHASH_V1" || encode(tx))`.
* `merkle::calculate_block_root` and `Block::reconstruct`, including the
  per-combination re-encode and re-hash of every transaction in the block.
* `Block::create` and `to_proposal`, so proposal sizes are the real sizes.

Supplied by the harness, and why:

* **The reconstruction search loop.** `reconstruct_block_from_proposal` in
  `services/chain/chain-network/src/lib.rs` is a private `async fn` reachable
  only through a running service. `search_reconstruction` reproduces its
  cartesian-product loop and its two caps; the per-combination work it performs
  is the real `Block::reconstruct`, which is where essentially all the time
  goes. The reproduction is asserted against the caps' documented constants in
  the crate's tests.
* **A faster-than-the-node grinding loop** (`AttackerHasher`). The node rebuilds
  and reallocates a transaction per hash; an attacker would encode once and
  patch the varying bytes. Measuring the attacker's real cost means measuring
  the attacker's real loop, and pricing them generously is the conservative
  direction for a security margin. `cargo test` asserts byte-for-byte that this
  shortcut produces the same hashes as the real path, at nine nonces spanning
  the range; if it ever diverges, the suite fails rather than reporting a
  wrong rate.
* **Proofs are constructed, not proved.** The proof of leadership is decoded
  from its wire form and the per-op proof is signed once and cloned.
  `Block::reconstruct` never verifies either, so this changes no measured
  quantity — it only avoids minutes of Groth16 setup per run. Sizes are the
  genuine encoded sizes, so the size check costs what it costs in production.

## Determinism

Every transaction is derived from a fixed key and a `u64` nonce, so both
machines grind byte-identical candidates and the birthday trials are
reproducible. The only machine-dependent inputs are the CPU and the toolchain,
both recorded in `results/<machine>/`.

[logos-lips#389]: https://github.com/logos-co/logos-lips/pull/389
