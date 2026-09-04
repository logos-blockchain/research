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
| Pi 5 whole-machine mint, tokens/s | 4.45 @ 100 · 1.40 @ 300 · 0.42 @ 1000 · 0.17 @ 3000 | `benchmark-results/RPi5-16GB/main/mining.csv`, pooled |
| Fastest attacker core (285HX, Rust-JIT), tokens/s | 3.55 @ 100 · 1.27 @ 300 · 0.39 @ 1000 · 0.11 @ 3000 | `benchmark-results/FedoraIntel285HX24C-256GB/main/mining.csv`, pooled ÷ 24 |
| Public header verification, Pi 5, one core | 157/s (6.4 ms) | `tools/benchmarks/blend-header-verification` |
| Equi-X verify, cold, Pi 5 | 54.7 µs | `benchmark-findings/findings.md` §3 |

Between measured efforts the curves interpolate log-log; outside, they
extrapolate as 1/E (the `difficulty_control` model).

## 1. The door under flood

A quiet node sits at load level ~1.3 (24 core-relay arrivals + 2 honest edge
offers against V = 157), so the door rests at the floor. The raise rule trips
when priced arrivals cross level 5 — **98/round, which an attacker at the floor
price needs ~57 fastest cores to generate**. Below that, the price never moves,
and the defense against door occupation is the acceptance-rate cap plus
redundancy: 32 fastest cores saturate one door's `Λ_E` at the floor while the
node feels nothing, but doing that to every door of an `N`-node network costs
`N` times ~9.5 cores, forever.

Above the trip point the controller does its job:

![door under a 120-core flood](img/door_flood.png)

A 120-core flood escalates floor→600→ceiling in two retargets (60 rounds),
**holds the ceiling for the whole flood** — the load lands inside the deadband,
so there is no decay-under-fire — and decays home in five retargets (150
rounds) once the flood stops. Peak CPU on the defending node: 37% of one Pi 5
core. During the flood the attacker takes ~96% of the acceptance rate and 75%
of honest offers are refused per round (they retry; study 2 shows none are
stranded).

## 1b. The adaptive attacker does not sawtooth

The generic exponential-gain controller oscillated against an attacker that
pauses above a give-up price (`difficulty-control.md` run 4). The specified
integer rule does not:

![door vs an adaptive attacker](img/door_adaptive.png)

With a give-up of 800, the price climbs and **settles at 750 — the one value
just below the give-up — and holds**, because the attacker's own presence keeps
the load inside the deadband. The equilibrium is a stable, priced occupation:
98% attack duty, ~97% of the acceptance rate, at a sustained cost the attacker
cannot lower — just-below-trip pressure is ~57 fastest cores whatever price it
settles at. The ×2-up/×¾-down asymmetry and the hold-inside-deadband together
replace the sawtooth with a flat price; what they cannot do is hand the door
back, which is the acceptance-rate cap's job and the PR's open question on
door-occupation economics.

## 2. The grace window `G = 60` strands nobody who matters

Worst case — the price steps up the instant after the quote — an exponential
solve outlives the 60 s grace with probability:

| device | at the floor (300) | at the ceiling (1000) |
| --- | --- | --- |
| Pi 5, 4 cores | 4.5e-37 | 1e-11 |
| Pi 5, 1 core | 9e-10 | **0.17%** |

Replayed through the 120-core flood trace (price stepping ×2 twice), 0 of
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
mean per-epoch multiplier 0.74 tightening / 1.39 loosening at `N = 100`), and
the controller re-anchors to `BASE·4/median` each epoch — a shifted median is a
bounded bias, not a compounding drift. Influence is per declaration, so it is
priced by the SDP minimum stake.

Two findings feed back into the specification:

- **The zero-median branch was the one unbounded path.** Uncapped, a sustained
  median of 0 doubles the threshold each epoch and reaches free admission —
  every ticket satisfying it — in exactly **19 epochs** from `BASE`
  (`BASE = p/2¹⁹`; ~20 weeks). Reachable only past 50% collusion or on a
  genuinely idle network, but free admission is precisely wrong for an idle
  network. The rule now caps the loosening at the level-1 fixed point
  `4·BASE`, where a sustained zero median settles and stays; the cap also
  makes the old below-`p` cap unreachable.
- **Sixteen levels are a bucket list, not a ranking:** 89% of 100
  heterogeneous reporters share their level with another, so the on-chain load
  report ranks doors only coarsely — the targeting-oracle residual the PR
  records.

## 4. The edge leader pre-mines for 1.2% of a Pi 5

| price | pre-mine duty (3 tokens per 600 s rotation) | P(3 slot-time solves > 15 s) | > 30 s |
| --- | --- | --- | --- |
| 300 (floor) | 0.36% | ~2e-7 | ~3e-13 |
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
2. **The loosening is capped at `4·BASE`** (study 3's runaway).
3. **The adaptive-attacker residual is a stable occupation, not a sawtooth**
   (study 1b) — the PR's open question is rephrased accordingly.

## Not covered here

- The header-verification figure (157/s) predates no circuit change we know of,
  but re-measuring on the Pi 5 against the circuit with the proof of work
  branch needs the hardware; open.
- Honest clients giving up under high prices, mixed device fleets beyond the
  two Pi profiles, and door-selection strategies smarter than uniform are not
  modeled.
