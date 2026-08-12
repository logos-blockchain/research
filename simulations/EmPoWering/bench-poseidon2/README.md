# Poseidon2 candidate-rate benchmark

Measures the cost of one EmPoWering proof-of-work candidate against the real
`logos-blockchain-poseidon2` crate, so the Blend threshold in the model's section 4.5
rests on a measurement rather than an estimate.

    cargo run --release

Expects `logos-blockchain` checked out as a sibling of `logos-lips`; adjust the path
dependency in `Cargo.toml` otherwise.

A candidate is two `zkhash` calls (`proof-of-quota.md:204-205`). `Digest::digest`
absorbs every input *and* a padding element, so a two-input hash is three permutations,
not one — six per candidate naive, four if the constant first input of each hash is
precomputed.

Result on an Apple M4 Pro performance core, release build with LTO. As of circuit
v0.5.6 (`pow_nonce`), the Blend candidate is ONE 3-input hash with a domain tag, and
only the reward candidate still derives a key:

| | ns | per second |
| --- | --- | --- |
| one permutation | 3,299 | 303,149 |
| **blend candidate v0.5.6, naive (4 perms)** | **14,855** | **67,318** |
| blend candidate v0.5.6, prefix precomputed (2 perms) | 8,203 | 121,910 |
| reward candidate, naive (kdf + ticket, 7 perms) | 26,602 | 37,591 |
| reward candidate, prefixes precomputed (4 perms) | 16,413 | 60,927 |

**Measured on the Raspberry Pi 5 target** (Model B Rev 1.1, one pinned core, six runs
across two sessions, spreads ≤ 0.1 %, 46–57 °C — raw runs in `results/`):

| | Pi 5 | M4 Pro | ratio |
| --- | --- | --- | --- |
| one permutation | 22,813 ns | 3,299 ns | 6.9× |
| blend candidate, naive | 94,158 ns | 14,855 ns | 6.3× |
| blend candidate, prefix precomputed | 48,472 ns | 8,203 ns | 5.9× |
| reward candidate, naive | 165,658 ns | 26,602 ns | 6.2× |

The estimate band (4–8×) held. **The reference basis is one core of the Pi 5**, and
`BLEND_DIFFICULTY_BASE` is calibrated on it at `p/2¹⁹` — about 50 s per message,
~1,750/day per core, four times that on the whole board. The blend optimiser's edge is
**1.94×** on the Pi — algorithmic headroom alone; implementation headroom (assembly,
batching, GPU) is not measured here and could be considerably larger.

## The reference machine is not the target machine

**Measured on an Apple M4 Pro. The intended deployment target is a Raspberry Pi 5.**

Those are very different: a Pi 5 runs four Cortex-A76 cores at 2.4 GHz against an M4 Pro
performance core at roughly 4.4 GHz with substantially higher IPC on the 64x64->128
multiply-and-carry sequences that dominate BN254 field arithmetic. Clock accounts for
about 1.8x of the gap and microarchitecture for the rest, putting the plausible band at
**four to eight times slower per core**, with the middle of that band the best guess.

That has not been measured, and it should be, because the Blend threshold is calibrated
against it. Scaling the M4 Pro figure:

| threshold | M4 Pro | Pi 5 @4x | Pi 5 @6x | Pi 5 @8x | msgs/day, 1 Pi 5 core @6x |
| --- | --- | --- | --- | --- | --- |
| `p/2^19` | 12 s | 49 s | 73 s | 98 s | 1,176 |
| `p/2^20` | 24 s | 98 s | 2.4 min | 3.3 min | 588 |
| `p/2^22` | 98 s | 6.5 min | 9.8 min | 13.1 min | 147 |

The specification currently sets `p/2^22`, which meets the design target of roughly a
minute per message on an M4 Pro core and **overshoots it by five to eight times on a
Pi 5**. Hitting the same target on a Pi 5 core would put the threshold near `p/2^19`.

Re-run this benchmark on the target hardware before the value is fixed.

## Running on the Raspberry Pi 5 — one command

64-bit OS. Everything else — Rust, the sibling `logos-blockchain` clone, the
pinned and thermally guarded triple run, median extraction, the generated
`configs/pi5.toml`, the threshold re-derivation table, and a results commit on a
dated branch — is handled by:

```bash
sudo apt install -y git build-essential python3-venv curl
git clone https://github.com/logos-blockchain/research.git ~/Logos/research
cd ~/Logos/research && git checkout EmPoWering-tokenomics
cd simulations/EmPoWering && make pi5
```

The script (`scripts/run_pi5.sh`) pins the benchmark to one core, waits for the
board to cool below 65 °C before each run, discards any run that finishes above
80 °C, takes the median of three valid runs and flags any metric whose spread
exceeds five percent. It writes the raw runs and log under
`bench-poseidon2/results/`, generates `configs/pi5.toml` with the measured
`[work]` values (retiring the 4–8× estimate band), prints seconds-per-message
and the suggested exponent for both reference bases — one core and the whole
board — and commits the results on a `pi5-measurement-<date>` branch. All git steps are
non-interactive: the repositories are public so nothing before the final push
needs credentials, and the push — which always does — fails cleanly with
instructions rather than prompting. To have it land in the same run,
authenticate first with `gh auth login && gh auth setup-git` (device flow, no
password typed on the Pi). Knobs: `RUNS`, `CORE`, `TEMP_LIMIT_C`, `COOL_TO_C`;
`PI5_DEV=1` runs the pipeline on a development machine without the Pi checks or
the commit.

What remains a human decision, printed at the end of the run: the reference
basis (one core vs the whole board, a factor of four) and, from it, whether
`BLEND_DIFFICULTY_BASE` moves in the Mantle specification.
 A Pi 5 has four
cores, so a participant willing to use all of them divides the wall-clock figures by
four; whether the reference should be one core or the whole board is itself a decision.
