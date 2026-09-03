# blend-header-verification

How many Blend public-header verifications per second a node sustains.

The Blend protocol bounds how many messages a node may receive in a round:
`M_N^Max = (Φ_CC^Max + 1) · M_1^Max`, one share per neighbour it may hold plus one for
the edge nodes it serves. Header verification — signature *and* proof of quota —
happens on the relay path, before a message is released, so that budget is also a
verification budget. Whether the slowest hardware the protocol targets can sustain
it is an empirical question. This tool answers it.

Only a *first sighting* costs a verification: the relaying logic discards a
duplicate before checking the proof of quota. The budget is therefore the
adversarial ceiling, reached only if every neighbour fills its share with messages
the node has not seen, while the honest load is `F_1`, the rate at which the
network emits distinct message instances.

It wraps the `verify_public_header` divan benchmark from `logos-blockchain` and
converts its per-operation latencies into throughput, single-threaded and across
all cores, then compares both against that budget.

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
make run ARGS="--phi-cc-max 16 --m1-max 24"
```

## What is measured

Three slices, so the cost is attributable rather than just totalled:

| benchmark | what it covers |
| --- | --- |
| `bench_verify_header_signature` | Ed25519 signature check alone |
| `bench_verify_proof_of_quota` | Groth16 PoQ check alone |
| `bench_verify_public_header_complete` | both — the per-message relay cost |

The last one is the per-message cost the budget is measured against.

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
  measured verifications/s  ->  vs the budget (Φ_CC^Max + 1) · M_1^Max per round
                            ->  headroom, and the largest M_1^Max this rate supports
```

Hardware that cannot sustain the budget cannot verify every message the protocol
would let it accept. The honest load is far below it, so a shortfall bounds the
adversarial case rather than normal operation.

The protocol-side assumptions are all overridable, so the bound can be recomputed
without re-measuring: `--round-seconds`, `--phi-cc-max`, `--m1-max`, `--f1`.

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
