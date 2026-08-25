# Equi-X Benchmark Report

- Generated: 2026-07-28T11:07:49+00:00
- Config: `configs/full.toml`
- Devices (CPUs): raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712
    - `raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712`: Raspberry Pi 5 Model B Rev 1.1 (aarch64, cpu)
- `equix-c`: version 1.0.0, commit b7bb7d9, built with gcc-14.2.0
- `equix-rust`: version 0.7.0, commit crate-0.7.0, built with rustc

## Correctness cross-check (interop gate)

**Overall: PASS ✅**

| kind | detail | result |
|------|--------|--------|
| interop | equix-c->equix-rust: all 4 solutions for deadbeef verify OK | PASS |
| interop | equix-c->equix-rust: all 2 solutions for cafe verify OK | PASS |
| interop | equix-c->equix-rust: all 3 solutions for 0000000000000002 verify OK | PASS |
| interop | equix-rust->equix-c: all 4 solutions for deadbeef verify OK | PASS |
| interop | equix-rust->equix-c: all 2 solutions for cafe verify OK | PASS |
| interop | equix-rust->equix-c: all 3 solutions for 0000000000000002 verify OK | PASS |
| effort-agreement | effort (attempts, achieved) across impls: {'equix-c': (114, 1922), 'equix-rust': (114, 1922)} -- AGREE | PASS |

## DoS-protection effectiveness (this system)

Equi-X defends by making requesters *solve* (expensive) while the service only *verifies* (cheap). Protection factor = measured attacker time to craft one accepted token at a given effort ÷ measured verify time. Judged **effective** when ≥ 10000× on every measured point.

**Verdict: EFFECTIVE ✅** (effective from — `raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712`: effort ≥ 1000).

At effort 10000, an attacker needs ~13.3s (impl `equix-rust`) to craft one accepted request, while the defender verifies in ~54.69µs (**243,170×** asymmetry; one core screens ~18,284 requests/s vs the attacker's ~0.08 tokens/s).

| device | effort | attacker time/token | attacker impl | verify time | protection factor | verify/s | attacker tokens/s |
|---|---|---|---|---|---|---|---|
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 100 | 84.328 ms | equix-rust | 54.693 µs | 1,542× | 18,284 | 11.858 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 1000 | 2.408 s | equix-rust | 54.693 µs | 44,033× | 18,284 | 0.415 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 10000 | 13.300 s | equix-rust | 54.693 µs | 243,170× | 18,284 | 0.075 |

## Sustained throughput under concurrency (measured)

The DoS section above reports **per-core** capacity as 1/latency from a single serial op. This section instead **measures** aggregate throughput with *N* worker processes running at once (N stepping up to the core count), so it captures real memory-bandwidth contention. It is additive — the per-core figures above are unchanged.

Measured on up to **4** concurrent workers. *Peak* is the best aggregate ops/s observed; *knee* is the worker count where it peaks (adding workers past it stops helping). *Naïve N×* is the per-core figure multiplied by the core count — what a linear extrapolation would (over)predict; the *efficiency* column is measured peak ÷ naïve N×.

| impl | operation | 1 worker (per-core) | knee | measured peak | naïve N× | scaling efficiency |
|---|---|---|---|---|---|---|
| equix-c | solve | 47 ops/s | 4 workers | **187 ops/s** | 189 ops/s | 99% |
| equix-rust | solve | 47 ops/s | 4 workers | **185 ops/s** | 189 ops/s | 98% |
| equix-c | verify | 23,715 ops/s | 4 workers | **92,572 ops/s** | 94,861 ops/s | 98% |
| equix-rust | verify | 17,988 ops/s | 4 workers | **67,632 ops/s** | 71,950 ops/s | 94% |

### solve: throughput vs. concurrency

| impl | workers | ok | aggregate ops/s | per-worker ops/s | scaling eff. | peak RSS |
|---|---|---|---|---|---|---|
| equix-c | 1 | 1 | 47 | 47 | 100% | 69 MB |
| equix-c | 2 | 2 | 94 | 47 | 100% | 139 MB |
| equix-c | 4 | 4 | 187 | 47 | 99% | 277 MB |
| equix-rust | 1 | 1 | 47 | 47 | 100% | 4 MB |
| equix-rust | 2 | 2 | 94 | 47 | 100% | 8 MB |
| equix-rust | 4 | 4 | 185 | 46 | 98% | 15 MB |

### verify: throughput vs. concurrency

| impl | workers | ok | aggregate ops/s | per-worker ops/s | scaling eff. | peak RSS |
|---|---|---|---|---|---|---|
| equix-c | 1 | 1 | 23,715 | 23,715 | 100% | 70 MB |
| equix-c | 2 | 2 | 46,989 | 23,495 | 99% | 156 MB |
| equix-c | 4 | 4 | 92,572 | 23,143 | 98% | 344 MB |
| equix-rust | 1 | 1 | 17,988 | 17,988 | 100% | 3 MB |
| equix-rust | 2 | 2 | 35,282 | 17,641 | 98% | 5 MB |
| equix-rust | 4 | 4 | 67,632 | 16,908 | 94% | 11 MB |

## Mining rate vs difficulty (measured)

How many effort-qualified tokens can be minted per second at a given difficulty. The **whole-machine** rate is the reliable figure: it averages one streaming search per core over independent nonce ranges. Per-core is that rate divided by the core count (token-find time is heavy-tailed, so the separately-sampled single-core mean is noisier and can even exceed the machine rate ÷ cores at low sample counts — prefer the derived per-core). Mint rate falls ~1/effort, so difficulty sets the rate directly.

**`equix-rust`** on `raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712` (base `abcd`), whole-machine = 4 cores:

| difficulty (effort) | mean attempts/token | tokens/s [4 cores] | tokens/s [1 core, ÷4] |
|---|---|---|---|
| 100 | 35 | **4.45** | 1.113 |
| 300 | 125 | **1.40** | 0.349 |
| 1000 | 494 | **0.42** | 0.106 |
| 3000 | 1,288 | **0.17** | 0.043 |

**Message sizes (measured from every minted token):** 
E=100: solution 16 B + nonce 8 B; E=300: solution 16 B + nonce 8 B; E=1000: solution 16 B + nonce 8 B; E=3000: solution 16 B + nonce 8 B.
Token size is **constant in difficulty**: every token at every measured E is exactly 16 B solution + 8 B nonce — raising E raises solve cost, never message size.

> Over a 30× rise in difficulty (100→3000), the machine mint rate fell 26× — ~1/effort, so halving the target roughly doubles the mint rate.

## Comparison plots (every plot compares C vs Rust; with multiple CPUs each plot is faceted per CPU and `xdev_*` charts compare CPUs directly)

### Solve Time By Runtime

![solve_time_by_runtime.png](plots/solve_time_by_runtime.png)

### Throughput

![throughput.png](plots/throughput.png)

### Jit Speedup

![jit_speedup.png](plots/jit_speedup.png)

### Peak Rss

![peak_rss.png](plots/peak_rss.png)

### Solve Distribution

![solve_distribution.png](plots/solve_distribution.png)

### Verify Time

![verify_time.png](plots/verify_time.png)

### Compile Overhead

![compile_overhead.png](plots/compile_overhead.png)

### Effort Attempts

![effort_attempts.png](plots/effort_attempts.png)

### Effort Time

![effort_time.png](plots/effort_time.png)

### Dos Protection

![dos_protection.png](plots/dos_protection.png)

### Concurrency Solve

![concurrency_solve.png](plots/concurrency_solve.png)

### Concurrency Verify

![concurrency_verify.png](plots/concurrency_verify.png)

### Mining Rate

![mining_rate.png](plots/mining_rate.png)

## solve results

| device | challenge | impl | runtime | median | p95 | solves/s | hashes/s | sols/solve | RSS(KB) |
|---|---|---|---|---|---|---|---|---|---|
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-c | interpreted | 121.602 ms | 122.096 ms | 8.2 | 538,940 | 2.01 | 68368 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-c | compiled | 21.214 ms | 21.297 ms | 47.1 | 3,089,247 | 2.01 | 68880 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-c | compiled | 21.210 ms | 21.291 ms | 47.1 | 3,089,871 | 2.01 | 68368 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-rust | interpreted | 116.190 ms | 116.642 ms | 8.6 | 564,043 | 2.01 | 3840 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-rust | compiled | 21.153 ms | 21.250 ms | 47.3 | 3,098,168 | 2.01 | 3840 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-rust | compiled | 21.161 ms | 21.248 ms | 47.3 | 3,097,033 | 2.01 | 3856 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-c | interpreted | 121.572 ms | 121.912 ms | 8.2 | 539,071 | 2.17 | 68368 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-c | compiled | 21.207 ms | 21.292 ms | 47.2 | 3,090,332 | 2.17 | 68880 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-c | compiled | 21.214 ms | 21.292 ms | 47.1 | 3,089,280 | 2.17 | 68368 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-rust | interpreted | 116.218 ms | 116.624 ms | 8.6 | 563,904 | 2.17 | 3840 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-rust | compiled | 21.143 ms | 21.235 ms | 47.3 | 3,099,650 | 2.17 | 3856 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-rust | compiled | 21.148 ms | 21.244 ms | 47.3 | 3,098,957 | 2.17 | 3856 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-c | interpreted | 121.527 ms | 121.951 ms | 8.2 | 539,271 | 1.98 | 68368 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-c | compiled | 21.221 ms | 21.299 ms | 47.1 | 3,088,194 | 1.98 | 68880 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-c | compiled | 21.214 ms | 21.292 ms | 47.1 | 3,089,291 | 1.98 | 68368 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-rust | interpreted | 116.116 ms | 116.628 ms | 8.6 | 564,402 | 1.98 | 3856 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-rust | compiled | 21.143 ms | 21.231 ms | 47.3 | 3,099,609 | 1.98 | 3856 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-rust | compiled | 21.140 ms | 21.239 ms | 47.3 | 3,100,043 | 1.98 | 3856 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-c | interpreted | 121.568 ms | 121.918 ms | 8.2 | 539,090 | 1.97 | 68368 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-c | compiled | 21.220 ms | 21.308 ms | 47.1 | 3,088,476 | 1.97 | 68368 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-c | compiled | 21.215 ms | 21.306 ms | 47.1 | 3,089,127 | 1.97 | 68368 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-rust | interpreted | 116.246 ms | 116.788 ms | 8.6 | 563,772 | 1.97 | 3840 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-rust | compiled | 21.148 ms | 21.234 ms | 47.3 | 3,098,865 | 1.97 | 3840 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-rust | compiled | 21.152 ms | 21.238 ms | 47.3 | 3,098,287 | 1.97 | 3856 |

## verify results

| device | challenge | impl | runtime | median | p95 | result | RSS(KB) |
|---|---|---|---|---|---|---|---|
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-c | interpreted | 64.471 µs | 65.684 µs | OK | 68880 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-c | compiled | 55.248 µs | 56.313 µs | OK | 69392 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-c | compiled | 54.896 µs | 55.665 µs | OK | 68880 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-rust | interpreted | 81.516 µs | 82.905 µs | OK | 3872 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-rust | compiled | 80.062 µs | 84.294 µs | OK | 3872 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0000000000000002 | equix-rust | compiled | 79.516 µs | 84.609 µs | OK | 3872 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-c | interpreted | 65.192 µs | 66.628 µs | OK | 68880 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-c | compiled | 54.989 µs | 56.184 µs | OK | 69392 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-c | compiled | 55.331 µs | 56.795 µs | OK | 68880 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-rust | interpreted | 81.081 µs | 83.053 µs | OK | 3856 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-rust | compiled | 79.470 µs | 86.757 µs | OK | 3872 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | cafe | equix-rust | compiled | 80.535 µs | 84.923 µs | OK | 3872 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-c | interpreted | 64.535 µs | 65.758 µs | OK | 68880 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-c | compiled | 54.693 µs | 55.702 µs | OK | 69392 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-c | compiled | 55.553 µs | 56.572 µs | OK | 68880 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-rust | interpreted | 80.979 µs | 82.497 µs | OK | 3856 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-rust | compiled | 79.553 µs | 84.646 µs | OK | 3872 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-rust | compiled | 80.784 µs | 84.775 µs | OK | 3872 |

## hashx_compile results

| device | challenge | impl | runtime | median compile | median exec | RSS(KB) |
|---|---|---|---|---|---|---|
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-c | interpreted | 46.212 µs | 4.166 µs | 69392 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-c | compiled | 52.248 µs | 333 ns | 69392 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-rust | interpreted | 62.989 µs | 4.222 µs | 2000 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | 0102030405060708 | equix-rust | compiled | 75.905 µs | 352 ns | 2016 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-c | interpreted | 46.758 µs | 4.157 µs | 69392 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-c | compiled | 52.536 µs | 333 ns | 69392 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-rust | interpreted | 63.081 µs | 4.241 µs | 1984 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | deadbeef | equix-rust | compiled | 76.100 µs | 352 ns | 2000 |

## effort results

| device | base | target | impl | runtime | mean attempts | median time | mean achieved |
|---|---|---|---|---|---|---|---|
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | abcd | 10000 | equix-c | compiled | 629.0 | 13.339 s | 11898 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | abcd | 10000 | equix-rust | compiled | 629.0 | 13.300 s | 11898 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | abcd | 1000 | equix-c | compiled | 114.0 | 2.416 s | 1922 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | abcd | 1000 | equix-rust | compiled | 114.0 | 2.408 s | 1922 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | abcd | 100 | equix-c | compiled | 4.0 | 84.764 ms | 141 |
| raspberry-pi-5-model-b-rev-1-1-6-18-34-rpt-rpi-2712 | abcd | 100 | equix-rust | compiled | 4.0 | 84.328 ms | 141 |

---
_See `results.csv` for the full flat dataset and `raw/results.json` for per-rep data._