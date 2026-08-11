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

Result on an Apple M4 Pro performance core, release build with LTO:

| | ns | per second |
| --- | --- | --- |
| one permutation | 3,350 | 298,536 |
| `zkhash` of 2 inputs | 11,582 | 86,339 |
| candidate, naive (6 perms) | 23,346 | 42,833 |
| candidate, precomputed prefixes (4 perms) | 16,481 | 60,677 |

The optimising miner's edge is only **1.40x**, but that is *algorithmic* headroom alone.
Implementation headroom — assembly field arithmetic, batching, GPU — is not measured
here and could be considerably larger.

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

Re-run this benchmark on the target hardware before the value is fixed. A Pi 5 has four
cores, so a participant willing to use all of them divides the wall-clock figures by
four; whether the reference should be one core or the whole board is itself a decision.
