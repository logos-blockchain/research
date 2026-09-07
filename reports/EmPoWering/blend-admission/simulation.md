# Blend load-driven admission — the calibration studies

Simulations of the admission mechanisms specified in `blend-protocol.md` 1.7.0
(logos-lips branch `docs/blend-load-driven-admission`): the per-node edge door
(`Edge Difficulty`) and the consensus threshold (`Blend Difficulty`), run as
written — exact integer rules, real BN254 modulus — against the measured Equi-X
curves. Four studies, one per open calibration question in the specification's
PR. Regenerate with:

```bash
cd tools/benchmarks/Equi-X
PYTHONPATH=harness python3 -m equix_bench.blend_admission --out <dir>
PYTHONPATH=harness python3 -m pytest harness/tests/test_blend_admission.py
```

## Inputs, all measured

| Quantity | Value | Source |
| --- | --- | --- |
| Pi 5 whole-machine mint, tokens/s | 4.45 @ 100 · 1.40 @ 300 · 0.42 @ 1000 · 0.17 @ 3000 | `benchmark-results/RPi5-16GB/main/mining.csv`, pooled; `RPi5-8GB` agrees within 0.5% on every point, and 16GB is the slower board |
| Fastest attacker core (285HX, Rust-JIT), tokens/s | 3.55 @ 100 · 1.27 @ 300 · 0.39 @ 1000 · 0.11 @ 3000 | `benchmark-results/FedoraIntel285HX24C-256GB/main/mining.csv`, pooled ÷ 24 |
| Public header verification, Pi 5, one core | 157/s (6.388 ms; 625/s on four threads, 3.99×) | `reports/blend/header-verification/console-RPi5.txt` — measured at `logos-blockchain 87138d2` (three-branch circuit), performance governor, 56.8 °C peak. Decomposition: signature 275.75 µs + proof of quota 6.116 ms |
| Equi-X verify, cold, Pi 5 | 54.7 µs | `benchmark-findings/findings.md` §3; primary: `results.csv` medians 54.9–55.2 µs (equix-c compiled, varied challenges, both Pi boards) |

Between measured efforts the curves interpolate log-log; outside, they
extrapolate as 1/E (the `difficulty_control` model).

## 1. The door under flood

A quiet node sits at load level ~1.3 (24 core-relay arrivals + 2 honest edge
offers against V = 157), so the door rests at the floor. The raise rule trips
when priced arrivals cross level `ℓ*+2` = 5 — **98/round, which an attacker at
the floor price needs ~57 fastest cores to generate** over a quiet network.
Below that, the price never moves, and the defense against door occupation is
the acceptance-rate cap plus redundancy: 32 fastest cores saturate one door's
`Λ_E` at the floor while the node feels nothing, but doing that to every door
of an `N`-node network costs `N` times ~9.5 cores, forever.

Above the trip point the controller does its job:

![door under a 200-core flood](img/door_flood.png)

A 200-core flood escalates floor→600→ceiling in two retargets (60 rounds),
**holds the ceiling for the whole flood** — its offers keep the load above the
decay threshold — and decays home in five retargets (150 rounds) once the flood
stops. A 120-core flood flutters one step below the ceiling: attacker minting
is priced at the grace floor (acceptance rule 2), which lags each price move by
up to `G` rounds, so mid-size attacks oscillate between adjacent steps rather
than settling. Peak CPU on the defending node: 35% of one Pi 5 core. During
the 200-core flood the attacker takes ~98% of the acceptance rate and 85% of
honest offers are refused per round (they retry; study 2 shows none are
stranded).

### 1c. Decay at the network equilibrium

The door thresholds sit **above** the consensus set point (`raise > ℓ*+2`,
`decay < ℓ*+1`) precisely so that the load Blend Difficulty steers the network
to — level `ℓ*` — stays below the door's deadband:

![the same flood over the PoW-at-sizing ambient](img/door_equilibrium.png)

With ambient at the sized operating point (`Φ_CC^Max·(F_1+F_W·β_max)` = 48
core arrivals/round, level ~2.6), the door still decays fully to the floor 150
rounds after a flood, and the trip point over this ambient is ~38 fastest cores
at the floor. Had the thresholds been the naive `ℓ*±1`, the equilibrium itself
would sit inside the deadband and every attack's price would freeze there —
the interaction the branch review caught (R2).

## 1b. The adaptive attacker does not sawtooth

The generic exponential-gain controller oscillated against an attacker that
pauses above a give-up price (`difficulty-control.md` run 4). The specified
integer rule does not:

![door vs an adaptive attacker](img/door_adaptive.png)

With a give-up of 800, both attacker sizes **flutter one step (750↔1000)**:
minting priced at the grace floor lags each move by up to `G` rounds, so
neither a clean settle nor the generic controller's multi-octave sawtooth
occurs — the excursion is bounded to adjacent steps. The occupation is priced
either way (97% attack duty, ~97% of the acceptance rate at 120 cores), and
its cost scales with the price the attack sustains: **just-below-trip pressure
is ~57 fastest cores at the floor and ~140 at 750** — the floor figure is the
attacker's cost-minimizing bound, not a price-independent constant. Either way
the mechanism cannot hand the occupied service back; that is the
acceptance-rate cap's job and the PR's open question on occupation economics.

## 2. The grace window `G = 60` strands nobody who matters

Worst case — the price steps up the instant after the quote — an exponential
solve outlives the 60 s grace with probability:

| device | at the floor (300) | at the ceiling (1000) |
| --- | --- | --- |
| Pi 5, 4 cores | 4.5e-37 | 8.8e-12 |
| Pi 5, 1 core | 8.2e-10 | **0.17%** |

Replayed through the 200-core flood trace (price stepping ×2 twice), 0 of
3,510 four-core and 0 of 3,606 single-core solvers were stranded. The
constraint the specification states — `G` at least the p95 solve at the ceiling
on the slowest device — holds with a wide margin at (60, 1000); halving `G` to
the observation window `W = 30` would push the single-core worst case to ~4%,
which is why `G` is its own parameter.

## 3. The median moves one level below half collusion

![median shift vs colluding fraction](img/median_shift.png)

With `N ∈ {32, 100, 1000}` reporters, honest loads lognormal around the set
point and quantized to sixteen levels, a colluding fraction reporting the
extreme moves the lower median by one level typically and two at most (at 30%:
mean per-epoch multiplier 0.77 tightening / 1.47 loosening at `N = 100`). The
rule is a pure re-anchor to `BASE·ℓ*/max(1, median)` — a shifted median is a
bounded bias with **no memory**: it vanishes the epoch capture ends. Influence
is per declaration, so it is priced by the SDP minimum stake.

Two findings feed back into the specification:

- **The zero-median branch was the one unbounded path.** Under the original
  recursive rule, a sustained median of 0 doubled the threshold each epoch and
  reached free admission — every ticket satisfying it — in exactly **19
  epochs** from `BASE` (`BASE = p/2¹⁹`; ~20 weeks). The rule is now stateless
  and floors the median at level 1, so a zero median sits at the fixed point
  `ℓ*·BASE` instantly and reversibly — no doubling dynamic exists to cap.
- **Sixteen levels are a bucket list, not a ranking:** 89% of 100
  heterogeneous reporters share their level with another, so the on-chain load
  report ranks doors only coarsely — the targeting-oracle residual the PR
  records.

## 4. The edge leader pre-mines for 1.2% of a Pi 5

| price | pre-mine duty (3 tokens per 600 s rotation) | P(3 slot-time solves > 15 s) | > 30 s |
| --- | --- | --- | --- |
| 300 (floor) | 0.36% | ~2e-7 | ~6e-16 |
| 1000 (ceiling) | 1.18% | **4.8%** | 0.03% |

Solving at slot time is safe at the floor and marginal at the ceiling: 4.8% of
edge leaders would miss the 15-round traversal budget and fall back to a direct
broadcast, surrendering unlinkability. Pre-mining removes the risk for at most
1.2% of a Pi-class machine even at the ceiling — the number that makes the
specification's `d_edge^Max` constraint concrete.

## What went back into the specification

1. **Load counts only priced connections.** The first run of study 1 showed the
   raise rule fed by raw offers: a costless connect-flood (no valid token)
   could move a node's price and, through the reported median, tighten
   `d_blend` network-wide for free. The door now checks the token first and
   the rate cap last, and `A_n` counts an edge connection only when its token
   passed — a connection must cost work to move the load.
2. **The zero-median runaway is closed by flooring the median at level 1**
   (study 3): the loosening never passes the fixed point `ℓ*·BASE`.
3. **The adaptive-attacker residual is a stable occupation or a one-step
   flutter, not a wide sawtooth** (study 1b) — the PR's open question is
   rephrased accordingly.
4. **`ℓ*` is derived, and it is 3.** The branch review (R1) found `ℓ* = 4`
   inconsistent with the `F_W = 1` sizing: the sized traffic (60 arrivals per
   round) is level 3.06 on the reference hardware. The set point is now the
   level of the sized traffic, stated as a derivation at the definition, and
   the 124 MB cache floor is consistent with it.
5. **The door thresholds sit above the set point** (`raise > ℓ*+2`,
   `decay < ℓ*+1`, study 1c) — sharing the naive `ℓ*±1` deadband would freeze
   every door at the equilibrium the consensus controller steers to (R2).
6. **The edge node need not await the quote** — a serialized quote round trip
   would not fit `T_E`'s own derivation on a slow link (R3).
7. **A token moves the load once.** The priced-offer rule alone left rate-refused
   tokens replayable into the load signal at zero marginal cost (a ~6×
   understatement of the trip cost); the spec now records priced pairs and
   counts each token once, which also makes this module's
   fresh-mint-per-offer model exact.
8. **The Blend difficulty became a pure function of one epoch's reports** —
   no step clamp, no hold-on-empty, median floored at level 1. A
   checkpoint-bootstrapped node computes it from carried ledger state alone;
   the attacker model here prices minting at the grace floor (acceptance
   rule 2), which reshaped the flutter results above.

## Not covered here

- The header-verification provenance is closed: the run's console transcript
  is committed at `reports/blend/header-verification/console-RPi5.txt`, and
  the measured ref `logos-blockchain 87138d2` contains the third branch
  (`blend/proofs/src/quota/pow.rs`), so 157/s is the deployed circuit's
  figure. The transcript's "implied bound" section speaks the tool's
  pre-#421 window model; the measured rates are model-independent. The
  board's `results.json`/`results.csv` remain worth committing for
  per-repeat detail.
- Honest clients giving up under high prices, mixed device fleets beyond the
  two Pi profiles, and door-selection strategies smarter than uniform are not
  modeled.
