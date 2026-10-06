# pol-proving

How long the node takes to prove leadership on a given machine. A vote's proof is the proof of
leadership under a vote domain (`tools/simulators/finality/CERTIFIED.md`, D1), so this is what a
seat costs its holder once per round. The reference hardware is a Raspberry Pi 5
(`tools/simulators/finality/PLAN.md`, Q7).

## Usage

Self-contained: `make` fetches and builds `logos-blockchain` itself. A fresh Raspberry Pi needs
`make`, a C toolchain, `git`, `curl`, `unzip`, `cargo`/`rustc` and `python3`; `make check` names
what is missing.

```
make check     # read-only: is the toolchain here?
make smoke     # end-to-end check that the pipeline works, not a measurement
make run       # the measurement
make clean     # drop build output, keep the checkout
make distclean # drop the checkout too
```

Neither `clean` nor `distclean` touches measured results; `make clean-results` discards them.

| variable | default | meaning |
| --- | --- | --- |
| `REF` | `4e0405d5…` | logos-blockchain commit to measure, the finality study's |
| `REPEATS` | `3` | repeats of each configuration |
| `SAMPLE_COUNT` | `20` | proofs per repeat |
| `RESULTS` | `reports/finality/pol-proving` | where results are written |
| `ARGS` | — | passed to the wrapper, e.g. `ARGS="--label pi5-fan"` |

## What is measured

The `prove` divan benchmark of logos-blockchain (`zk/proofs/pol/benches/prove.rs`), with its
fixed inputs: one call to `prove` per sample, witness generation and the rapidsnark Groth16 proof
together.

| configuration | how |
| --- | --- |
| all cores | rapidsnark sizes its thread pool from the machine's core count |
| one core | `taskset -c 0`; the pool's threads share that core (Linux only) |

## Output

`results-<label>.json` and `results-<label>.csv` in `RESULTS`, the label naming the machine: the
machine, its frequency governor, the SoC temperature and throttling flags around every run, the
commit measured, and divan's fastest, slowest, median and mean for every repeat.

## Running on a Raspberry Pi 5

- **64-bit Raspberry Pi OS.** The circuit artefacts and rapidsnark ship prebuilt for
  `linux-aarch64`; a 32-bit system has neither.
- **Governor.** `make check` reports it. On anything but `performance` the times are a ceiling:
  `sudo cpupower frequency-set -g performance` if the tooling is installed.
- **Cooling.** The run reads `vcgencmd get_throttled` around every repeat and warns if the board
  throttled during it; a throttled run overstates the proving time. The flags it reads from boot
  are kept apart from those a run sets.
- **First build.** Compiling the dependencies takes a while on a Pi; `make smoke` first shows how
  long.
