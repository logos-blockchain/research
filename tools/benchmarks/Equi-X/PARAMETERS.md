# Equi-X Benchmark Parameters

This document describes **every parameter** the benchmarking framework exposes,
what it controls, and its implications for **execution time, memory, and cost**.
Parameters are set in a TOML config (see `configs/`) and travel to each runner as
the JSON job-spec (see `adapters/README.md`).

Equi-X itself is a fixed puzzle: **Equihash(n=60, k=3)** over the **HashX**
pseudo-random hash function. The algorithm constants (n, k, solution size = 8×
16-bit indices, hash size) are **not** tunable — they define the puzzle. What the
framework varies is *how* the puzzle is executed and measured, plus the Tor-style
*effort* layer stacked on top.

---

## 1. `operation` — what is being measured

| value | what it does | dominant cost |
|-------|--------------|---------------|
| `solve` | Generate the HashX program from the challenge, then run the Equihash solver to find all solutions. | **Milliseconds.** The headline PoW cost. ~1.7 solutions/challenge on average. |
| `verify` | Check that a given solution is valid for a challenge (index ordering + partial/final XOR sums). | **Microseconds.** ~1000× cheaper than solving — this asymmetry is the whole point of a client puzzle. |
| `effort` | Repeatedly solve over an incrementing nonce until a solution meets a target *effort* (difficulty). | **Scales with `target_effort`** (see §5). Models the real cost of producing a PoW at a difficulty. |
| `hashx_compile` | Isolate HashX **program generation + compilation** (`hashx_make` / `EquiXBuilder::build`) from execution, using the HashX API directly. | **Microseconds.** The only clean way to measure JIT/compile cost (see §3). |

**Implication:** `solve` and `verify` are the two faces of an asymmetric PoW;
report them together to show the work/verify ratio. `effort` is the attacker/
client cost model. `hashx_compile` explains *why* compiled mode is faster.

---

## 2. `runtime` — HashX execution backend

HashX generates a unique straight-line program per challenge and can either
**interpret** it or **JIT-compile** it to native code.

| value | meaning | implication |
|-------|---------|-------------|
| `interpret` | Force the pure interpreter; never compile. | Portable, no executable memory. **~9× slower solve** in practice (measured ~68 ms vs ~7.6 ms). |
| `try-compile` | Compile if supported, else fall back to the interpreter. **Default.** | Best speed where a JIT exists (x86-64/aarch64); safe elsewhere. `runtime_effective` reports which path ran. |
| `must-compile` | Require the JIT; **fail** if unsupported. | Use to guarantee you are measuring compiled performance; errors out on unsupported targets instead of silently interpreting. |

- C mapping: `interpret` → `equix_alloc(SOLVE)`; compiled → `equix_alloc(SOLVE | COMPILE)`. Unsupported JIT returns the `EQUIX_NOTSUPP` sentinel.
- Rust mapping: `RuntimeOption::InterpretOnly` / `TryCompile` / `CompileOnly`.

**Cost implication:** compiling adds a one-off ~50–80 µs per program (see
`hashx_compile`), amortized across the millions of HashX evaluations in a solve —
so compiled mode wins decisively for `solve`, is marginal for a single `verify`.

---

## 3. Compile-time isolation (why `hashx_compile` exists)

The HashX program is seeded by the **challenge**, so in the C library the program
is (re)generated *inside* `equix_solve` — libequix's public API cannot separate
"compile" from "solve". Rust *can* (build vs solve are distinct calls), but to
keep C and Rust comparable, **both** runners implement a dedicated
`hashx_compile` operation that times `hashx_make` (program-gen + JIT) separately
from one `hashx_exec`. Treat the `compile_ns` field as meaningful **only** for the
`hashx_compile` operation; it is `0` for `solve`/`verify`.

---

## 4. Challenge parameters

| parameter | applies to | meaning |
|-----------|-----------|---------|
| `challenges` (`challenge_hex`) | solve, verify, hashx_compile | Hex-encoded challenge bytes. The challenge is the HashX seed — **each distinct challenge is a different one-way function**. |
| `bases` (`challenge_base_hex`) | effort, hashx_compile | Fixed prefix; the runner appends a nonce to form each attempt's challenge. |
| `nonce_bytes` | effort | Width of the little-endian nonce counter appended to the base (`challenge = base ‖ LE(nonce)`). Must be ≤ 8. |
| `nonce_start` | effort, hashx_compile | Starting nonce value (reproducibility / sharding the search space). |
| `solution_hex` | verify | 16-byte packed solution (8× uint16 LE). The harness auto-fills this from a `solve` of the same challenge. |

**Edge case — invalid programs:** roughly **1 in 2^k** challenges produce a HashX
program that fails validation (by design). The runner treats this as a valid
*measured outcome* (`solutions: 0`, verify → `CHALLENGE`), not an error; the
effort search simply advances the nonce. Some perfectly valid challenges also
have **0 Equihash solutions** — e.g. the all-zero challenge — so pick challenges
with known solutions for solve/verify cells.

---

## 5. Effort / difficulty parameters (Tor proposal 327)

The effort layer sits **above** Equi-X. For a solved `(challenge, solution)`:

```
hash32   = first 32 bits (big-endian) of BLAKE2b-256(challenge ‖ solution_bytes)
achieved = floor((2^32 - 1) / hash32)          # "how hard was this solution"
valid at effort E  ⇔  hash32 · E ≤ 2^32 - 1     ⇔  achieved ≥ E
```

| parameter | meaning | implication |
|-----------|---------|-------------|
| `targets` (`target_effort`) | Difficulty to reach: stop when a solution's `achieved ≥ target`. | Cost grows **~linearly** with target — a 10× harder target costs ~10× more work. Each solution meets effort `E` with probability `1/E`; a solve yields ~1.7 solutions, so expected solves ≈ `E / 1.7`. |
| `max_attempts` | Safety cap on the nonce search per repetition. | Bounds worst-case runtime; if hit before the target, `achieved` reports the best found. Set comfortably above the target. |

The preimage layout and byte order are **identical in C and Rust** — the
cross-check asserts both produce the same `achieved` effort for a fixed input, so
a mismatch (a broken port) fails the build rather than silently skewing results.
(Verified against Python's standard `hashlib.blake2b(digest_size=32)`.)

**Notes:**
- This models Tor-327's effort *concept* (a difficulty proxy for benchmarking); the
  preimage is `challenge ‖ solution_bytes` with standard BLAKE2b-256, a
  simplification of Tor's production wire layout (which folds in seed/nonce/
  personalization fields), so values are not byte-compatible with a live Tor PoW.
- The search is **deterministic** given `(base, nonce_start)`: every repetition
  runs the same nonce sequence, so `repetitions` measures timing variance of the
  same search, not a difficulty distribution. Vary `nonce_start`/`bases` to sample
  different searches.

---

## 6. Measurement parameters

| parameter | meaning | implication |
|-----------|---------|-------------|
| `repetitions` | Number of **timed** iterations per cell. | More reps → tighter median/p95, longer runs. The report uses median + p95 + stddev because there is no `perf`/`taskset` here, so noise is real. |
| `warmup` | Untimed iterations run **before** timing. | Excludes cold caches, first-touch paging, and initial JIT warmth from the measurement. Warmups are never counted in `runs[]`. |
| `seed` | Optional RNG seed for reproducible challenge generation (reserved for generators). | Reproducibility. |
| `impls` | Which implementations to run (must match adapter manifest names). | Determines what appears on every comparison plot — needs ≥2 for the C-vs-Rust figures. |

---

## 7. Metrics reported (and their units)

| metric | source | notes |
|--------|--------|-------|
| `wall_ns` | `clock_gettime(CLOCK_MONOTONIC)` (C) / `Instant` (Rust) | Per-rep solve/verify/effort time. |
| `compile_ns` | `hashx_make` / `EquiXBuilder::build` timing | Meaningful only for `hashx_compile`. |
| `solves_per_sec`, `hashes_per_sec` | derived from median solve time | Throughput; hash-rate = solves/sec × the per-solve HashX count (2^16, the equix 16-bit index space; both impls use the same constant so comparisons are exact). |
| `peak_rss_kb` | `getrusage.ru_maxrss` (C) / `/proc/self/status VmHWM` (Rust) | Always **kilobytes** (Linux reports KB; macOS reports bytes and the runner converts). One process per cell keeps this attributable. |
| `attempts`, `achieved_effort` | effort search | Attacker/client cost at a difficulty. |
| `verify_result` | `equix_verify` result enum | `OK` / `CHALLENGE` / `ORDER` / `PARTIAL_SUM` / `FINAL_SUM`. |
| `protection_factor` | DoS analysis (§9) | attacker time/token ÷ defender verify time — the core DoS asymmetry. |
| `verify_per_sec`, `attacker_tokens_per_sec` | DoS analysis (§9) | defender screening capacity vs attacker output, per core. |

---

## 8. Device / CPU tracking & multi-CPU figures

Every run records the **device** it executed on — the runner self-reports
`env.cpu` (model), `env.arch`, and `env.device` (`cpu`/`gpu`), which the harness
turns into a device record `{type, name, arch, label}` carried on every result
(and in `results.csv` / `run_meta.json`).

| parameter | meaning | implication |
|-----------|---------|-------------|
| `--device-label` (a.k.a. `--cpu-label`) | Human label for the executing device. | Defaults to a slug of the **CPU model + OS/kernel version** (e.g. `intel-xeon-2-80ghz-6-18-5`); override to disambiguate machines that still collide (e.g. `--device-label ryzen-9950x`). |

**Reflecting the CPU on plots:** with a single device, the CPU is shown in each
plot's title and the report header. To compare **multiple CPUs**, run on each
machine and merge the outputs:

```bash
python -m equix_bench run --config configs/full.toml --out runA/ --device-label host-a
python -m equix_bench run --config configs/full.toml --out runB/ --device-label host-b
python -m equix_bench combine --inputs runA runB --out combined/
```

`combine` re-aggregates the saved per-run data (no re-benchmarking) and renders:
- **faceted plots** — one subplot per CPU, C-vs-Rust compared within each; and
- **`xdev_*` cross-CPU charts** — x=CPU, series=implementation — for headline
  metrics (solve throughput, solve time, peak RSS, verify time).

### GPU

**Equi-X is not benchmarked on GPU, and no GPU implementation is bundled.** HashX
(the hash Equi-X is built on) is deliberately designed to resist GPU/ASIC
acceleration — it depends on branch prediction and out-of-order execution that
favor general-purpose CPUs — so a GPU solver would be far slower and none exists in
practice. The framework is nonetheless **GPU-ready**: a runner that reports
`device: "gpu"` plugs in through the adapter protocol and appears on all figures as
another device, with no harness change.

## 9. DoS-protection effectiveness

Equi-X is a client puzzle for DoS defense: a requester must **solve** (expensive)
before a service acts, while the service only **verifies** (cheap). Any run that
includes both the `effort` and `verify` operations gets a DoS-protection section
(and `dos_protection.png`) computed from **measured** numbers on the running system.

| quantity | definition |
|----------|------------|
| `attacker_s(E)` | measured median time to craft one accepted token at effort `E` (the `effort` op), using the fastest impl |
| `defender_s` | measured fastest median `verify` time on that device |
| **`protection_factor(E)`** | `attacker_s(E) / defender_s` — how many verifies the defender does in the time the attacker needs for one accepted request |
| `verify_per_sec` | `1 / defender_s` — defender screening capacity per core |
| `attacker_tokens_per_sec` | `1 / attacker_s(E)` — attacker output per core |
| **verdict** | *effective* if some tested effort reaches the threshold; the report states the **minimum effort** `E*` from which protection holds on this system |

The threshold defaults to **10 000×** (`dosprotect.DEFAULT_THRESHOLD`). Run it with:

```bash
python -m equix_bench run --config configs/dos_protection.toml --out results/
```

Because it uses measured attacker cost, the answer is specific to the CPU it runs
on — the same effort gives a different protection factor on a fast vs slow machine.

## 10. Compiler-flag variants (performance vs build flags)

The same C implementation can be built under different compiler/optimization flags
and compared as separate impls. `scripts/build_variants.sh` builds a matrix
(`gcc -O0/-O2/-O3`, `-march=native`, `-flto`, `clang -O3`, …), writing one
`equix-c-<name>` manifest per variant to `adapters/generated/` (loaded alongside the
built-in adapters). The flags apply to the whole `libequix`+`hashx`+runner build, so
they affect the Equihash solver and the HashX interpreter (the JIT executes the same
generated machine code regardless).

```bash
./scripts/build_variants.sh
python -m equix_bench run --config configs/compiler_flags.toml --out results/
```

Every comparison plot then compares the flag variants; all variants produce
identical solutions, so the interop cross-check still holds.

## 11. Not benchmarked by default (and why)

- **HugePages** (`EQUIX_CTX_HUGEPAGES`): off by default; it changes RSS accounting
  and requires host configuration, which would distort memory comparisons.
- **Threads / multi-core solving**: the framework measures single-thread cost per
  cell for clean per-implementation comparison; parallel scaling is orthogonal.
- **HW performance counters** (cycles, cache misses): `perf` is unavailable in the
  reference environment, so cost is reported as wall-time + RSS.
