# blend-header-verification

How many Blend public-header verifications per second a node sustains.

The Blend protocol's connection monitoring bounds how many messages a connection
may carry in an observation window (`⌈M₁⌉^W`). Since header verification —
signature *and* proof of quota — now happens on the relay path, before a message
is released, a node cannot accept messages faster than it can verify headers.
That makes the divergence controller `κ_max` an empirical question about the
slowest hardware the protocol targets, not a purely analytical one. This tool
answers it.

It wraps the `verify_public_header` divan benchmark from `logos-blockchain` and
converts its per-operation latencies into throughput, single-threaded and across
all cores, then prints the `κ_max` ceiling those numbers imply.

## Usage

Self-contained: `make` fetches and builds `logos-blockchain` itself. A fresh
Raspberry Pi needs only `git`, `cargo`/`rustc` and `python3` — the default remote
is anonymous HTTPS, so no credentials and no SSH key.

```
make check     # read-only: is the toolchain here?
make smoke     # ~1 min end-to-end proof the pipeline works
make run       # the measurement
make clean     # drop build output, keep the 95 MB checkout
make distclean # drop the checkout too, forcing a re-fetch
```

Neither `clean` nor `distclean` touches measured results — a results tree is
sometimes the only copy of a run on hardware that is not to hand. Discarding it
is opt-in, via `make clean-results`.

`make help` lists every target. `make where` prints the paths in use.

Useful variables:

| variable | default | meaning |
| --- | --- | --- |
| `REF` | `master` | branch, tag or commit of logos-blockchain to measure |
| `REPEATS` | `5` | repeats of each configuration |
| `SAMPLE_COUNT` | `200` | divan samples per benchmark |
| `RESULTS` | `reports/blend/header-verification` | where results are written |
| `ARGS` | — | passed through to the wrapper, e.g. `ARGS=--no-pin` |

```
make run REPEATS=3 REF=v1.2.0
make run ARGS="--phi-max 16 --window 60"
```

## What is measured

Three slices, so the cost is attributable rather than just totalled:

| benchmark | what it covers |
| --- | --- |
| `bench_verify_header_signature` | Ed25519 signature check alone |
| `bench_verify_proof_of_quota` | Groth16 PoQ check alone |
| `bench_verify_public_header_complete` | both — the per-message relay cost |

The last one is what bounds `κ_max`.

### Proving is excluded, in both senses

The fixture proves a PoQ before anything can be verified, and proving is orders
of magnitude slower than verifying. It is kept out of the result twice over:

- **Out of the latency.** Divan times only the benchmarked closure. The fixture
  is a process-wide `LazyLock` built before the first sample, so no reported
  duration contains any proving.
- **Out of the contention.** The all-cores figure uses divan's `--threads N`
  rather than one process per core. Because the fixture is process-wide, the
  proof is built once and every thread verifies against it, and divan holds the
  threads on a barrier so each sample starts on all of them together. A process
  per core would instead have each core prove its own fixture, and cores that
  finished proving early would be measured against neighbours still proving —
  contention against proving work, not against verification.

`--threads N` also matches the deployed shape: one node process verifying on N
threads, not N independent nodes sharing a board.

Wall-clock per phase *does* include the one-off proving. It is reported as
`wall_s` for information and is never an input to a throughput figure.

## Reading the output

Beyond the per-benchmark throughput and latency, the run prints the scaling from
one thread to N — how much of the ideal `N×` the board's memory bandwidth and
thermal headroom actually deliver — and then the implied protocol bound:

```
  headers verifiable per 30-round window   ->  divided across Φ_CC^Max connections
  ... against the expected honest traffic  ->  κ_max ceiling from CPU capacity
```

`κ_max` must sit **below** that ceiling and **above** the ≈3.87 floor set by
connection-level duplication (×2) compounding with the bootstrapping rise of
`F_D` toward `F_C` (×1.94). If the ceiling falls under the floor, the hardware
cannot verify every message the protocol would let it accept.

The protocol-side assumptions are all overridable, so the bound can be recomputed
without re-measuring: `--window`, `--round-seconds`, `--phi-max`, `--f1`.

## Output

Written to `reports/blend/header-verification/`:

- `results.json` — full detail: every run, per-benchmark stats, machine
  description, thermals, and the logos-blockchain commit measured
- `results.csv` — one row per (mode, repeat, benchmark)

## Running on a Raspberry Pi

Two things distort results on a Pi, and both are recorded:

- **Governor.** `make check` reports it. On `powersave` the numbers are a floor.
  `sudo cpupower frequency-set -g performance` if the tooling is installed.
- **Throttling.** The run samples SoC temperature and `vcgencmd get_throttled`
  around every phase, and prints an explicit warning if the board throttled.
  A throttled run understates the hardware; treat it as a lower bound.

Proving still heats the SoC before each measured phase, so on a board near its
thermal limit the first samples can be biased — the throttle warning is what
tells you whether that happened.

Start with `make smoke` to confirm the pipeline, then `make run REPEATS=2` to
gauge how long a phase takes on your board before committing to a longer run.
