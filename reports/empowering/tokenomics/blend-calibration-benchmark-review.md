# Review: the Blend calibration benchmark (2026-09-09)

**Scope.** Everything the calibration of `BLEND_DIFFICULTY_BASE` rests on in this
repository: the Poseidon2 candidate benchmark (`tools/benchmarks/empowering/`), its
Raspberry Pi 5 runner (`tools/simulators/empowering/tokenomics/scripts/run_pi5.sh`),
the `[work]` section of `configs/specified.toml`, the `blend` analysis, and the report's
addenda §0.0 and §0.6. Reviewed against the specification as of logos-lips PR #400 at
`0efda516` (Proof of Quota 1.2.0, Proof of Work 1.0.0): the Blend ticket is
`zkhash(pow_nonce, pol_epoch_nonce)`, the searched nonce first, no domain separation tag.

**Purpose.** Give whoever updates the calibration a checked account of what the number
means, what it does not cover, and what remains to measure. Findings are numbered; each
says what was found, what it implies for the calibration, and whether this change
already acts on it.

## 1. What the calibration rests on

```
proof-of-work.md            BLEND_DIFFICULTY_BASE = p // 2**19
                            "about fifty seconds per solution on one core of the target machine"
        ^
configs/specified.toml      [blend] difficulty_base_exp = 19
                            [work]  seconds_per_candidate  (the measured cost of one candidate)
        ^
run_pi5.sh                  pinned single-core runs on the Pi 5, medians, spreads, thermal guards
        ^
tools/benchmarks/empowering pow-bench: Poseidon2 (jf-poseidon2, pinned rev) through the node's
                            own sponge (logos-blockchain-poseidon2::Digest::digest)
```

`seconds per solution = 2^k × seconds_per_candidate`, on one core, in expectation. The
model (`make blend`) and the report gate (`make report-numbers`) both derive from the
config, so a change to `[work]` propagates and is checked; nothing derives from the
specification's sentence itself.

## 2. Findings

### F1. The calibration sentence prices the old ticket (this change updates the model; the sentence needs a decision)

The 50 s figure was computed from 94.2 μs per candidate, measured on the Pi 5 for the
circuit v0.5.6 form `zkhash(BLEND_POW_V1, pol_epoch_nonce, pow_nonce)`: three inputs
plus padding, four permutations. The specification now defines a two-input ticket:
three permutations. The same Pi 5 runs timed a two-input `zkhash` at **71,318 ns**
(median of six, spread 0.05 %), and the cost of a Poseidon2 sponge does not depend on
which input is the searched one, so the current candidate is measured, not derived.
`[work]` now carries it. At `p/2^19`:

| | one Pi 5 core |
| --- | --- |
| expected time per solution | 37.4 s |
| median | 26 s |
| 95th percentile | 112 s |
| messages per day | 2,311 |
| whole board (÷ measured scaling; ÷4 until the Pi run) | ~9.3 s |

The sentence in `proof-of-work.md` overstates the price by a quarter. Two ways to close
it: keep the exponent and restate the sentence at about 37 s, or move to `p/2^20` for
about 75 s. A non-power-of-two base would land nearer 50 s but breaks the
`p // 2**k` form every controller and gate assumes; not recommended. See §3.

### F2. The benchmark measures what the specification defines (verified)

- Hash: `Poseidon2Bn254Hasher::digest` from `logos-blockchain/zk/poseidon2`, the node's
  `zkhash`; the permutation is `jf-poseidon2` at the revision pinned in `Cargo.toml`.
  Mining happens outside the circuit, in a prover's native code, so the native hash is the
  right object to time; the circuit only verifies the ticket.
- Permutation counts match the sponge: on the Pi, 2-input = 3.13 permutations,
  3-input = 4.13, reward (2-input + 3-input) = 7.26. The excess over the integer is the
  sponge's fixed overhead per call.
- Input order is irrelevant to cost, and the new form is a proper subset of the old
  measurement's work. The Pi's ratio between the two forms, 94.2 / 71.3 = 1.32, is what
  four versus three permutations predicts; today's desktop runs give 1.21 because the
  desktop's per-call overhead is proportionally larger and the machine was loaded.
- Nonces are sequential small integers in the loop; field arithmetic is constant-time,
  so this does not bias the figure.
- What a miner also does per candidate, and the benchmark omits: compare the ticket's
  canonical representative against the target. Negligible against a permutation.

### F3. Results carried no provenance (fixed in tooling)

The August result files record neither the board revision, the OS, the `rustc`, nor the
`logos-blockchain` and `jellyfish` revisions the binary was built from. The poseidon2
crate last changed on 2026-06-10 (`66c1307`, the arkworks 0.5 bump), so every run in
`results/` used the same code, but that is known only by inspection. `run_pi5.sh` now
writes a provenance line as the first line of every result file, and result files from a
development machine are named `dev-*` instead of `pi5-*`.

### F4. The whole-board basis was an assumed ÷4 (fixed in tooling; Pi figure pending)

The board-level figures divided the one-core time by four. Poseidon2 is compute-bound
and should scale nearly linearly, but a Pi 5 running four field-arithmetic threads may
clock lower under sustained load. The benchmark gains a `THREADS=n` aggregate run and
`run_pi5.sh` runs it on every core after the pinned runs, reporting the measured scaling
and using it in the board column. On the M4 Pro four threads sustain 3.97× one thread;
the Pi's own figure is produced by the next `make pi5`.

### F5. The calibration prices the puzzle, not the message (open; needs a Pi measurement)

A message costs one solution **and** `β_max = 3` proofs of quota, one per encapsulation.
The proof cost is branch-independent (every branch is evaluated in every proof) and is
not measured on the Pi anywhere in this repository or in the node; the node's
`zk/proofs/poq/benches/prove.rs` benchmarks the core and leader provers on whatever
machine runs it. A desktop figure exists since 2026-09-09: the Proof of Quota
specification's new benchmark figure gives about 630 ms per proof on one thread of an
i9-13980HX (median of ten runs), about 125 ms on eight threads. A Pi 5 core is five to
eight times slower than a desktop core on this kind of arithmetic, so a proof there is
of the order of three to five seconds single-threaded, and a message's three proofs ten
to fifteen seconds: a third to a half of the puzzle's 37 s, not a rounding error. The
calibration target ("what a message ought to cost") should be stated against the sum.
Action: run the PoQ prove benchmark on the Pi, single-threaded, and record it beside
the candidate cost; the exponent decision (keep `2^19`) was taken with this estimate.

### F6. Implementation headroom is unbounded and unmeasured (open; a property, not a defect)

The figure is the cost on the reference implementation: portable Rust field arithmetic,
no assembly, no batching, one hash at a time. A miner with a hand-optimised NEON or
x86 permutation, batched Montgomery arithmetic, or a GPU obtains candidates at rates
orders of magnitude above one Pi core, and none of that is measured here. The threshold
therefore sets the price an honest participant pays on the target hardware and does not
bound what an adversary can generate; the specification and the PR description already
frame it that way, and the calibration should keep saying so. Measuring a GPU
implementation would bound the ratio; it would not change the honest-user calibration.

### F7. "Seconds per solution" is an expectation (fixed in tooling text; the spec sentence should say so)

The number of candidates to a solution is geometric with mean `2^k`, so the wait has
median 0.69× and 95th percentile 3.0× the expectation: at `p/2^19` a user waits more
than 112 s one time in twenty. "About fifty seconds per solution" reads as a typical
wait. The benchmark's table and the runner's summary now state the distribution; the
specification's sentence should say "in expectation".

### F8. Statistics: sound on the Pi, indicative on the desktop (fixed: dev runs labelled)

The Pi protocol (one pinned core, cooling to 65 °C before each run, discarding runs that
end above 80 °C, medians of three, spreads flagged above 5 %) produced spreads of 0.1 %
across six runs in two sessions. Desktop runs are single, unpinned and unguarded, and
moved by 10 % on the same machine between 2026-08-12 and today. They are for comparing
hash forms on one machine, never for calibration, and the `dev-*` naming keeps them out
of the Pi record.

### F9. The drift gates followed the specification split (fixed)

`make check` read every proof-of-work constant from the Mantle file; since 2026-09-09
they live in `proof-of-work.md`. `spec_sync.py` now reads them from that document when
it exists and from Mantle otherwise, and no longer requires the withdrawn `BLEND_POW_V1`
tag; it requires the two-input ticket instead. Against the stacked #443 tree (floor and
refill) all 48 checks pass. Against the #400 tree alone six fail by design, all items
#443 carries: `POW_SHARE`, `SHARE_DEN`, `REWARD_TARGET_FLOOR`, the floored return, and
the two Block Rewards conservation phrases. `make report-numbers` gates the report's
§0.6 figures (2,300 messages/day, edge 1.00×) against the config; 72/72 pass.

### F10. The Equi-X alternative (context)

logos-lips PR #440, stacked on #400, proposes Equi-X for Blend admission and removes the
Poseidon2 Blend difficulty; this repository carries Equi-X benchmarks on the same Pi 5
under `reports/empowering/Equi-X/`. If #440 lands, this calibration is superseded and
the Equi-X findings become the basis. Until then the Poseidon2 figure is the one the
specification states.

### F11. Minor

- `run_pi5.sh` suggests an exponent for "~60 s per message"; at 71.3 μs that rounds to
  `p/2^20` (74.8 s). The suggestion is a rounding of a target no document states.
- The runner's log file is not committed with the runs; the provenance line now carries
  what the log held that mattered.
- The reward candidate's cost is unchanged by the ticket change (seven permutations;
  only the `KDF` tag is precomputable, one permutation). The genesis reward exponent is a
  seed the controller corrects, so no re-measurement is needed there.

## 3. The decision the calibration needs

| option | expected per message, one Pi 5 core | messages/day per core | what changes |
| --- | --- | --- | --- |
| keep `p/2^19`, restate the sentence | 37.4 s | 2,311 | one sentence in `proof-of-work.md` |
| move to `p/2^20` | 74.8 s | 1,155 | the constant, the sentence, `difficulty_base_exp`, report §0.6 and its gate |

Recommendation: keep `p/2^19` and restate the sentence as about 37 seconds in
expectation on one core, pending F5. The old target was "roughly a minute" for the
puzzle alone; once proving on the Pi is measured, the puzzle plus three proofs will sit
near that minute at `2^19`, and `2^20` would put the on-ramp at two minutes or more.

## 4. On the Pi, in order

1. `git checkout EmPoWering-pooling-rewards`, then `make pi5` from the tokenomics
   directory. Read the `blend_naive_ns` median (expected near 71 μs) and the board
   scaling line.
2. In the node repository, `cargo bench -p logos-blockchain-poq` pinned to one core, and
   record the proving time per proof (F5).
3. Decide the exponent (§3). Update `proof-of-work.md`'s constant and sentence,
   `configs/specified.toml` (`difficulty_base_exp`, and `[work]` from `configs/pi5.toml`),
   report §0.6, and the two `report_numbers.py` claims that quote it.
4. `make verify report-numbers web` and `make check LIPS=<the #443 tree>`.
