# EmPoWering tokenomics simulations

The models behind `reports/EmPoWering/tokenomics/` and behind the parameter values in
logos-lips PR #400: the proof-of-work reward pool, its two difficulty controllers, the
claim fee, the endowment sizing, bootstrap security, and the supply-vs-fee-schedule
check that resized `S_tge`.

Every number lives in `configs/specified.toml`, annotated KNOWN / DERIVED / MEASURED /
ASSUMED with citations into the specification tree. The modules take a config; nothing
is hardcoded, so a specification change is a one-line edit and the gates below say what
moved.

```
make all         # every analysis section
make rewards     # one section (fee, emission, rewards, blend, exhaustion, security)
make verify      # closed forms vs simulation, and the config's own invariants
make check LIPS=~/Logos/logos-lips   # config vs the specification tree, 19 checks
make bench-poseidon2                 # measure the candidate rate (Rust; see below)
```

`make all CONFIG=configs/other.toml` compares parameter sets by running the same code
twice.

## Layout

| | |
| --- | --- |
| `configs/specified.toml` | the parameter set as specified, one value per line, cited |
| `src/empowering/params.py` | config loader; all derived quantities in one place |
| `src/empowering/core.py` | pool dynamics, controllers, endowment-for-ramp search |
| `src/empowering/analyses.py` | one function per report section |
| `src/empowering/verify.py` | self-test: simulation vs closed forms |
| `src/empowering/spec_sync.py` | drift gate against the logos-lips tree |
| `bench-poseidon2/` | Rust benchmark of the puzzle candidate rate |

## The one measurement that still needs taking

`[work]` in the config was measured on an Apple M4 Pro. The deployment target is a
Raspberry Pi 5, estimated 4–8× slower per core and **not measured**. The Blend
admission threshold is calibrated against this number, so run `make bench-poseidon2`
on the target board, put the result into the config, and re-run `make blend` before
that threshold is relied upon. The benchmark needs a `logos-blockchain` checkout as a
sibling of this repository (path dependency in `bench-poseidon2/Cargo.toml`).
