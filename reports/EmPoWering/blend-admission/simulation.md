# Blend load-driven admission — the calibration studies

Simulations of the admission mechanisms specified in `blend-protocol.md` 1.7.0
(logos-lips branch `docs/blend-load-driven-admission`): the per-node edge door
(`Edge Difficulty`) and the consensus threshold (`Blend Difficulty`), run as
written — exact integer rules, real BN254 modulus — against the measured Equi-X
curves. Five studies. Regenerate with:

```bash
cd tools/benchmarks/Equi-X
PYTHONPATH=harness python3 -m equix_bench.blend_admission --out <dir>
PYTHONPATH=harness python3 -m pytest harness/tests/test_blend_admission.py
```

**The rules as measured here.** Load is the share of the per-round envelope a
node's arrivals occupy: `ℓ_n = A_n/(A^Max·r_n)` with `A^Max = Φ_CC^Max·M_1^Max +
Λ_E = 108`, quantized to sixteen levels; `A_n` counts core arrivals plus
**accepted** edge connections. `d_blend = BASE·ℓ*/max(L^Min, median)` with
`ℓ* = ⌊8·60/108⌋ = 4` and `L^Min = ⌈ℓ*/F_W^Max⌉ = 2`. The door retargets on
**presentations** `P_n` — tokens passing acceptance checks 1–3, accepted or
refused — raising above `2·Λ_E·r_n` and decaying below `Λ_E·r_n`.

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

The door's signal is edge presentations, not load, so its trip point is fixed in
tokens rather than in traffic: the raise fires above `2·Λ_E = 24` presentations
per round, which at the floor price costs **~19 of the fastest measured cores**
— a figure that holds only because a token counts towards `P_n` once, which the
specification states and the model here assumes.
Below that the defence is the acceptance rate and redundancy, not escalation.

![door under a 60-core flood](img/door_flood.png)

A 60-core flood escalates floor→ceiling in two retargets (60 rounds), **holds
the ceiling for the whole flood**, and decays home in five retargets (150
rounds). A 28-core flood — just above the trip point — flutters between 750 and
1000, since minting is priced at the grace floor, which lags each move by up to
`G` rounds. Peak CPU on the defending node: 35% of one Pi 5 core. The attacker
takes ~98% of the acceptance rate during the flood, and 85% of honest offers are
refused per round (they retry; study 2 shows none are stranded).

### 1c. Core traffic cannot hold the price up

![the same flood over the sized core ambient](img/door_equilibrium.png)

The door reads only edge presentations, so core traffic at the sized operating
point (48 arrivals/round) never enters its signal and the price decays to the
floor exactly as over a quiet network. This is what separating the two signals
buys: a load-driven door could be held up by core traffic it has no power to
shed.

### 1b. Adaptive attackers flutter one step

![door vs an adaptive attacker](img/door_adaptive.png)

An attacker that pauses above a give-up price produces no sawtooth — with
minting priced at the grace floor, which lags each move by up to `G` rounds, the
excursion is bounded to adjacent steps (750↔1000). The occupation is priced
either way: ~92% attack duty, ~90% of the acceptance rate at 40 cores.
Just-below-trip pressure costs ~19 fastest cores at the floor and scales roughly
linearly with the price sustained (~48 at 750) — the floor figure is the
attacker's cost-minimizing bound. What the price cannot do is hand the occupied
service back; that is the acceptance rate's and redundancy's job.

## 2. The grace window `G = 60` strands nobody who matters

Worst case — the price steps up the instant after the quote — an exponential
solve outlives the 60 s grace with probability:

| device | at the floor (300) | at the ceiling (1000) |
| --- | --- | --- |
| Pi 5, 4 cores | 4.5e-37 | 8.8e-12 |
| Pi 5, 1 core | 8.2e-10 | **0.17%** |

Replayed through the 60-core flood trace (price stepping ×2 twice), 0 of
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
mean per-epoch multiplier 0.75 tightening / 1.36 loosening at `N = 100`). The
rule is a pure re-anchor to `BASE·ℓ*/max(L^Min, median)` — a shifted median is a
bounded bias with **no memory**: it vanishes the epoch capture ends. Influence
is per declaration, so it is priced by the SDP minimum stake.

Two findings feed back into the specification:

- **The zero-median branch was the one unbounded path.** Under the original
  recursive rule, a sustained median of 0 doubled the threshold each epoch and
  reached free admission — every ticket satisfying it — in exactly **19
  epochs** from `BASE` (`BASE = p/2¹⁹`; ~20 weeks). The rule is now stateless
  and floors the median at `L^Min = 2`, so a zero median sits at `2·BASE`
  instantly and reversibly. The floor is derived, not chosen: it is where the
  drain condition stops holding.
- **Sixteen levels are a bucket list, not a ranking:** 88% of 100
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

## 5. The control loop, closed

The earlier rounds never closed the loop `F_W → load → median → d_blend → F_W`;
this study iterates it from all sixteen starting levels, for every peering degree
and edge-traffic combination.

| `Φ_CC` | edge 0 | edge 6 | edge 12 |
| --- | --- | --- | --- |
| 6 | cycle {2,4}, fixed [3] | fixed [3] | cycle {3,4} |
| 7 | fixed [3] | cycle {3,4} | fixed [4] |
| 8 | cycle {3,4} | fixed [4] | **fixed [4]** |

The design point — full peering with the edge allowance used — is an **exact
fixed point** at level 4, arrivals 60, `d = BASE`, `F_W = 1`. Every attractor is
bounded: each cycle visits two levels at most, the realized `F_W` never exceeds
`F_W^Max = 2`, and the drain condition `3.0 + 6 < 12` holds throughout. The sized
traffic sits **44% into its quantization band** `[54, 67.5)`; under the previous
denominator it sat 5.7% into its band, which is what made it flap.

One corner is **bistable**: `Φ_CC^Min` with no edge traffic admits both a fixed
point at level 3 and a 2↔4 cycle, depending on where the network starts. Bounded
and drain-safe, but the only configuration without a unique attractor — stated
rather than smoothed over.

## What went back into the specification

1. **Load counts only priced connections.** The first run of study 1 showed the
   raise rule fed by raw offers: a costless connect-flood (no valid token)
   could move a node's price and, through the reported median, tighten
   `d_blend` network-wide for free. The door now checks the token first and
   the rate cap last, and `A_n` counts an edge connection only when its token
   passed — a connection must cost work to move the load.
2. **The zero-median runaway is closed by flooring the median** (study 3):
   the loosening never passes the floor's fixed point. *Superseded by 11 — the
   floor became `L^Min = 2`, derived from the drain condition rather than set
   at level 1.*
3. **The adaptive-attacker residual is a stable occupation or a one-step
   flutter, not a wide sawtooth** (study 1b) — the PR's open question is
   rephrased accordingly.
4. **`ℓ*` became a derivation rather than a bare value.** The branch review
   (R1) found it stated as a result the reader had to trust. *Superseded by 9 —
   the derivation was against per-node hardware, which does not close; against
   the envelope it is `ℓ* = 4` and the cache floor is 187 MB.*
5. **The door thresholds sit above the set point** (`raise > ℓ*+2`,
   `decay < ℓ*+1`, study 1c) — sharing the naive `ℓ*±1` deadband would freeze
   every door at the equilibrium the consensus controller steers to (R2).
   *Superseded by 10 — the door left the load signal entirely for `P_n`.*
6. **The edge node need not await the quote** — a serialized quote round trip
   would not fit `T_E`'s own derivation on a slow link (R3).
7. **A token moves the load once.** The priced-offer rule alone left rate-refused
   tokens replayable into the load signal at zero marginal cost (a ~6×
   understatement of the trip cost); the spec now records priced pairs and
   counts each token once, which also makes this module's
   fresh-mint-per-offer model exact.
8. **The Blend difficulty became a pure function of one epoch's reports** — no
   step clamp, no hold-on-empty; a checkpoint-bootstrapped node computes it from
   carried ledger state alone.
9. **Load is measured against the protocol's per-round envelope, not against
   self-measured hardware.** The earlier denominator was the operator's
   provisioning choice: the same traffic reported level 3 on a one-core node and
   level 0 on a four-core one, so `d_blend` pinned at its loosest value on any
   multi-core network. `V_n` is deleted and the loop closes (study 5).
10. **The door reads presentations, not load** — with load counting only
   accepted connections, a load-driven door would be inert against any flood.
11. **The loosening stops at `L^Min = ⌈ℓ*/F_W^Max⌉ = 2`**, derived from the drain
   condition, and the nullifier cache floor is evaluated at `F_W^Max = 2`
   (187 MB) rather than at the sized rate.
12. **A token counts once towards the price it sets.** Deleting the priced-pair
   record alongside the load change left `P_n` counting every presentation, and
   a token refused at the acceptance cap never enters the spent-token cache —
   so a stock mined once would hold a node's ceiling for the cost of the `Λ_E`
   tokens accepted per round, about **one** fastest core rather than the ~19
   this report's study 1 prices. `P_n` now counts distinct tokens.

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
