# Poseidon2 candidate-rate benchmark

Measures the cost of one EmPoWering proof-of-work candidate against the real
`logos-blockchain-poseidon2` crate, so the Blend threshold in the model's section 4.5
rests on a measurement rather than an estimate.

    cargo run --release            # single core
    THREADS=4 cargo run --release  # plus an aggregate-throughput run on four threads

Expects `logos-blockchain` checked out as a sibling of this repository; adjust the
path dependency in `Cargo.toml` otherwise. The Poseidon2 permutation comes from the
pinned `jf-poseidon2` revision; the sponge (`Digest::digest`) is the node's own.

## What a candidate is

Since 2026-09-09 (logos-lips PR 400, review round two) the two puzzles are:

| | ticket | permutations | precomputable prefix |
| --- | --- | --- | --- |
| Blend admission | `zkhash(pow_nonce, pol_epoch_nonce)` | 3 | none: the nonce is absorbed first |
| Reward claim | `pk = zkhash(KDF, sk)`, then `zkhash(pk, block_hash, epoch_nonce)` | 3 + 4 = 7 | the `KDF` tag, one permutation |

`Digest::digest` absorbs every input *and* a padding element, so a two-input hash is
three permutations and a three-input hash four. Both tickets take the searched input
first, so no sponge state carries from one candidate to the next; the shortcut the
earlier v0.5.6 wiring (`zkhash(BLEND_POW_V1, pol_epoch_nonce, pow_nonce)`) allowed
is withdrawn. That form is kept as a reference line so both can be compared on one
machine.

## Results

**Raspberry Pi 5** (Model B Rev 1.1, one pinned core, six runs across two sessions on
2026-08-12, spreads ≤ 0.1 %, 46–57 °C, raw runs in `results/pi5-*`). The runs predate
the ticket change but already timed the two-input hash, and input order does not change
its cost, so the Blend candidate below is measured, not derived:

| | Pi 5 | permutations |
| --- | --- | --- |
| one permutation | 22,813 ns | 1 |
| **Blend candidate, `zkhash(nonce, epoch)`** | **71,318 ns** | 3 |
| Blend candidate, v0.5.6 form (for reference) | 94,158 ns | 4 |
| reward candidate, naive | 165,658 ns | 7 |
| reward candidate, `KDF` prefix precomputed | ~143,000 ns (derived: one permutation less) | 6 |

**Apple M4 Pro** performance core, two runs on 2026-09-09 (`results/m4pro-*`), five to
six times faster than the Pi and deliberately not the calibration basis:

| | M4 Pro |
| --- | --- |
| one permutation | 3,648 ns |
| Blend candidate, `zkhash(nonce, epoch)` | 13,368 ns |
| Blend candidate, v0.5.6 form | 16,252 ns |
| reward candidate, naive | 30,409 ns |
| reward candidate, `KDF` prefix precomputed | 26,885 ns |
| four threads, Blend candidates | 3.97× one thread |

Desktop figures move by about ten percent between sessions (3,299 ns per permutation
on 2026-08-12 against 3,648 ns today, same machine); the pinned, thermally guarded Pi
runs are the numbers to calibrate on.

## What it means for the threshold

The reference basis is **one core of the Pi 5**. At `BLEND_DIFFICULTY_BASE = p/2^19`
a solution takes 2^19 candidates in expectation:

| threshold | expected, one core | median | 95th percentile | msgs/day, one core |
| --- | --- | --- | --- | --- |
| `p/2^18` | 18.7 s | 13 s | 56 s | 4,622 |
| **`p/2^19`** | **37.4 s** | **26 s** | **112 s** | **2,311** |
| `p/2^20` | 74.8 s | 52 s | 224 s | 1,155 |

The wait for a solution is geometric, so its median is 0.69× and its 95th percentile
3.0× the expectation. The specification's calibration sentence still says "about fifty
seconds", the figure of the four-permutation form; at the same exponent the two-input
ticket costs a quarter less. Whether the exponent stays at 19 (about 37 s) or moves to
20 (about 75 s) is a decision for the RFC. The whole-board figure divides by the
thread scaling that `make pi5` now measures rather than by an assumed four.

The reward candidate is unchanged in cost by the ticket change. At the genesis
`difficulty_reward = p/2^26` it is about 3.1 hours of one Pi 5 core per solution, a
seed the controller corrects every block rather than a price.

## Running on the Raspberry Pi 5 — one command

64-bit OS. Everything else — Rust, the sibling `logos-blockchain` clone, the pinned and
thermally guarded triple run, a whole-board thread run, median extraction, the generated
`configs/pi5.toml`, the threshold re-derivation table, and a results commit on a dated
branch — is handled by:

```bash
sudo apt install -y git build-essential python3-venv curl
git clone https://github.com/logos-blockchain/research.git ~/Logos/research
cd ~/Logos/research && git checkout EmPoWering-pooling-rewards
cd tools/simulators/empowering/tokenomics && make pi5
```

The script (the simulator's `scripts/run_pi5.sh`) pins the benchmark to one core, waits
for the board to cool below 65 °C before each run, discards any run that finishes above
80 °C, takes the median of three valid runs and flags any metric whose spread exceeds
five percent. Every result file starts with a provenance line: board, OS, `rustc`, the
`logos-blockchain` and `jellyfish` revisions, the CPU governor. It then runs the
benchmark once more on every core to measure the board's actual scaling, writes the raw
runs and log under `tools/benchmarks/empowering/results/`, generates `configs/pi5.toml`
with the measured `[work]` values, prints seconds-per-message and the suggested exponent
for both reference bases, and commits the results on a `pi5-measurement-<date>` branch.
All git steps are non-interactive: the repositories are public so nothing before the
final push needs credentials, and the push — which always does — fails cleanly with
instructions rather than prompting. To have it land in the same run, authenticate first
with `gh auth login && gh auth setup-git`. Knobs: `RUNS`, `CORE`, `TEMP_LIMIT_C`,
`COOL_TO_C`; `PI5_DEV=1` runs the pipeline on a development machine without the Pi
checks or the commit, naming its files `dev-*`.

What remains a human decision, printed at the end of the run: the reference basis (one
core vs the whole board) and, from it, whether `BLEND_DIFFICULTY_BASE` moves in
`proof-of-work.md`.
