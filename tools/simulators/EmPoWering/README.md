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
make lepta       # exact-integer confirmation at lepton granularity
make sampled     # A2 run: Poisson arrivals with the retarget in the loop
make fees        # the working fee range on one axis, and example tx mixes
make rewards     # one section (fee, emission, rewards, blend, exhaustion, security)
make sweeps      # the parameter sweeps behind report sections 4.4.1-4.4.3
make sweeps-full # section 6's full programme: T, beta, rho, R0, ramp, D0
make web         # regenerate the browser panel's data, cross-check the JS model
make verify      # closed forms vs simulation, and the config's own invariants
make check LIPS=~/Logos/logos-lips   # config vs the spec tree: constants AND prose margins
make report-numbers                  # every number the report quotes, against the model
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
| `tools/benchmarks/EmPoWering/` | Rust benchmark of the puzzle candidate rate (repo path; not inside this directory) |

## Known gap

The report's historical tables were computed before the TGE supply resize and are
superseded by its addendum. `make sweeps` reproduces the three parameter sweeps and
`make exhaustion` the genesis mis-set table at the current parameters, so the only
figures not regenerable from here are the deliberately archival pre-resize ones
(git history of logos-lips PR #400).

`make check` guards two things: the config's constants against the specification tree,
and the **derived margins the specifications state in prose** — sentences like "factor
of five in hand" or "close to five years" are recomputed from the config and fail the
gate if a parameter change leaves them stale. That gate exists because exactly that
happened three times during drafting.

## Two engines, deliberately

The analyses compute in float LGO, which is exact for every dimensionless ratio but
cannot carry the ledger's integers: the pool is ~5×10¹⁶ lepta against float64's 2⁵³
exact-integer ceiling, and the protocol floors where floats keep fractional lepta.
`empowering/lepta.py` therefore re-runs the pool dynamics entirely in integer lepta —
checked `uint64` throughout, exact conservation asserted at every step, the σ cliff
pinned to its boundary, and the float engine's drift bounded at one lepton per claim
and measured rather than assumed. The Units-and-Precision parse/format round-trip is
fuzzed across the full range. `make verify` runs both engines.

## The measurement behind `[work]`

`[work]` in the config is **measured on the deployment target itself** — a Raspberry
Pi 5, one pinned core, with the raw runs archived in
`tools/benchmarks/EmPoWering/results/`. The Blend admission threshold is calibrated
against this number. To re-measure (new board, new library version), run `make pi5`
on the target: it drives the benchmark in `tools/benchmarks/EmPoWering/`, applies
thermal guards, takes medians, and writes `configs/pi5.toml`; then re-run
`make blend`. The benchmark needs a `logos-blockchain` checkout as a sibling of this
repository (path dependency in its `Cargo.toml`).
