# HashWX: measurements and studies for the move off Equi-X

HashWX v1.0.0, commit `74b567a3`, run on 2026-11-06.

Equi-X's author deprecated it on 2026-10-15 in favour of HashWX. This report holds what the Logos specifications need to make that move: what HashWX costs, whether the Blend edge door still works when priced in it, and whether the reward retarget works at its scale.

**Status.** Only an Apple M4 Pro has been measured. The Raspberry Pi 5 and the Intel 285HX set the protocol's values and are still to run. Every Pi 5 figure below is an estimate, and each is marked as one.

To measure a machine, from `tools/benchmarks/Equi-X`:

```sh
make hashwx OUT=results
```

It needs a C compiler, CMake and Python 3.11 or later. It takes about 3 minutes on the M4 Pro, and I expect 10 to 20 on a Pi 5. Results land in `results/hashwx`. The runner is `runners/hashwx-c`, and its header gives how the harness's operations map onto HashWX. In `results.csv`, a `solve` is one function's work, one build and 463 hashes, so hashes per second is 463 times `solves_per_sec`. The `hashes_per_sec` column assumes Equi-X and does not apply. `report.md` keeps Equi-X's wording.

## 1. What HashWX is

A nonce `N` satisfies a target `T` for a challenge `C` when `H(N) < T`, where `H = hashwx_make(Hash(C || LE64(N // 463)))`. `Hash` is BLAKE2b-256, in place of the README's SHA-256, since the library takes any 32-byte seed. The solver sends 8 bytes, the nonce. An attempt is one hash, so a target `T` costs `2^64 / T` hashes in expectation.

## 2. Cost, M4 Pro

`results` under [`benchmark-results/MacBookProM4ProC14-48GB/main`](benchmark-results/MacBookProM4ProC14-48GB/main). The machine was running other work during the run, with a load average of 6 to 7, so the whole-machine rate is conservative.

| Measure | Compiled | Interpreted |
| --- | --- | --- |
| One check: seed hash, build, one hash, comparison. Median, then p95 | 11.0 µs, 13.5 µs | 17.5 µs, 18.8 µs |
| Build a function | 7.8 µs | 1.8 µs |
| One hash, the first after a build | 3.1 µs | 15.1 µs |
| Mining rate, one core, 463 nonces per seed | 487,000 hashes/s | 140,000 hashes/s |

- The whole machine mines 5.0 to 6.0 MH/s over 14 cores, which is 360,000 to 430,000 hashes/s per core. The lower figure is from wall-clock time and the upper from the harness's pooled attempts.
- Building a function costs 0.8% of mining at 463 nonces per seed, as the author intends.
- Attempts per second stay flat within noise from a target of 30,000 to 1,000,000, so cost is linear in the target. Token times have a coefficient of variation of 0.9 to 1.0, as a geometric search should.
- The solver sends 8 bytes at every target.
- Compiled and interpreted modes gave the same hash sum over 100,000 seeds.
- Peak memory is about 2 MB per process, which is the process itself. The function's own scratchpad is 16 KB.

**Against Equi-X on the same machine.** Equi-X's check took 26.6 µs in C, interpreted because its C JIT is blocked there, and 34.7 µs in Rust, compiled. The fastest HashWX check is therefore 2.4 times cheaper than the fastest Equi-X check, and interpreted against interpreted it is 1.5 times cheaper. It is not the factor of 5 that comparing Zen 2 with a Pi 5 suggests.

**Against a GPU.** The author reports 5.6 MH/s on an RTX 5060 Ti at 180 W, from a private solver that nobody has reproduced, and 2,200 MH/s for HashX. This M4 Pro does about the same as that GPU's HashWX figure.

## 3. Estimates for a Pi 5

These come from the M4 Pro and Equi-X's per-core ratios between the two machines, 2.3 for verification and 4.6 for solving. They are not measurements.

| Quantity | Estimate |
| --- | --- |
| Hashes per second, one core | 1.1 to 2.1·10⁵ |
| Hashes per second, whole machine | 4.3 to 8.5·10⁵ |
| One check, compiled | 25 to 51 µs, against Equi-X's 54.7 µs |
| One check, interpreted | 40 to 80 µs, against Equi-X's 64.5 µs |
| One check against a header verification of 6.388 ms | 80 to 255 times cheaper, against Equi-X's 117 |

## 4. The door, priced in HashWX

`equix_bench.blend_admission` runs the door's exact rules. It now prices a nonce at `d` hashes. The bounds derive as the specification states them: twenty fastest cores fill the edge share at the floor, `price^Min = 20 * R_F // r_E`, and three solves on a whole Pi 5 take half of the message traversal time on average at the ceiling, `price^Max = T_M * HASHWX_MACHINE_RATE // 6`. The code still calls them `D_EDGE_MIN` and `D_EDGE_MAX`. A check costs 80 µs, the upper estimate. The fastest core is taken at 4·10⁵ hashes/s from the M4 Pro. Results are given at both ends of the Pi 5 estimate. Studies 3 and 5 read the load, not the door, and are not repeated. The Equi-X column is from [the earlier study](../blend-admission/simulation.md).

| Result | Equi-X | HashWX, Pi 5 at 4.3·10⁵ | HashWX, Pi 5 at 8.5·10⁵ |
| --- | --- | --- | --- |
| `price^Min`, `price^Max` | 300, 1,000 | 333,333, 1,065,000 | 333,333, 2,117,500 |
| Cores to fill the share, to trip a raise, to hold the ceiling | 19, 38, 124 | 20, 40, 128 | 20, 40, 254 |
| 200-core flood: rounds to the ceiling, rounds home | 60, 150 | 60, 150 | 90, 210 |
| 200-core flood: peak CPU of one Pi 5 core | 33% | 34% | 35% |
| 60-core flood: share the attacker holds, honest offers refused | 93%, 19% | 93%, 25% | 93%, 18% |
| Adaptive attacker: core-seconds per message, against a constant flood | 2.6, 2.8 | 2.6, 2.7 | 2.6, 2.8 |
| Solvers stranded through the floods | 0 | 0 | 0 |
| One core at the ceiling, worst case stranded | 0.17% | 0.25% | 0.25% |
| Pre-mining duty at the ceiling | 1.18% | 1.25% | 1.25% |
| Three solves at slot time miss 15 s, at the ceiling | 4.8% | 6.2% | 6.2% |

The door behaves as it did. Its time budgets set its behaviour, and the rates only move its range. `G = 60` still clears its constraint: the 95th percentile of a solve at the ceiling on one core is 30 s.

With the author's GPU figure, a floor-price share takes about 1.4 such GPUs per node and a raise about 2.9.

To rerun:

```sh
HASHWX_R_PI5_MACHINE=<measured> HASHWX_R_ATTACKER_CORE=<measured> HASHWX_T_VERIFY=<measured> \
  PYTHONPATH=harness python3 -m equix_bench.blend_admission --out results/door
```

## 5. The reward retarget, in target form

`equix_bench.hashwx_retarget` runs the retarget of `proof-of-work.md`, with `ticket < T` and `T` a 64-bit integer, at three settings. The caps keep the time on a whole Pi 5 that the `zkhash` caps give. Results are at a Pi 5 of 4.3·10⁵ hashes/s.

| Setting | Target rate, claims a block | Cap | Widest value | Steady rate | Tenfold jump settles in |
| --- | --- | --- | --- | --- | --- |
| Smoothing 9/10, 10 claims a block | 10 | 2^34.6 | 42 bits | 10.58 | 96 blocks |
| Bootstrap, reward 100 LOGOS, smoothing 999/1000 | 0.9353 | 2^29.1 | 97 bits | 0.936 | 1,675 blocks |
| After the bootstrap, 1M LOGOS in the pool | 0.6477 | 2^32.1 | 92 bits | 0.6488 | 1,880 blocks |

- An effort form, as the Equi-X RFC used, behaves the same within noise and reaches 133 bits or more at its hardest end during the bootstrap.
- The product fits 128 bits while the caps stay below 2⁵⁴, because the pool can be 64 bits and `P` is about 2¹⁰.
- The floor derivation holds. A block without claims leaves 8 at 8 and raises 9 to 10 at smoothing 9/10, and leaves 998 at 998 and raises 999 to 1000 at 999/1000.
- The steady error in the claim rate from integer rounding is about 500/T at smoothing 999/1000. That is 0.1% at T = 500,000, about 1.9 million boards at the bootstrap's rate, and 1% at T = 50,000, about 19 million boards.
- At smoothing 9/10 the retarget settles 6% above its target rate in either form. This comes from the update rule with exponential block gaps, not from the puzzle.

## 6. Implementing it from the specification

`equix_bench/hashwx_ref.py` is HashWX written from `doc/specification.md`. It reproduced upstream's four vectors on its first run, and it matches the library in both modes at nonces 0, 462, 463, 2³² + 7 and 2⁶⁴ − 1. So the specification is enough to write an independent implementation, which bears on the node's licence policy: `.cargo-deny.toml` allows no LGPL licence, and the two implementations found are LGPL. This one is not a clean-room implementation, because its author had read parts of the library's `src/hashwx.c`. Whether a permissive implementation is possible is a legal question this does not answer.

## 7. Not measured

- The Pi 5 and the 285HX.
- A rented vCPU. HashWX is built to run two threads per core, so the assumption that a vCPU is worth 1.5 Pi 5 cores needs checking.
- Any GPU. The author's solver is private.
- Execution Gas, which has to come from the method and machine of the gas analysis.
