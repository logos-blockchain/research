# EmPoWering network simulator — plan

Two deliverables on this branch, in dependency order:

1. **`tools/powcost/`** — a standalone proof-of-work cost estimator. No dependencies, no
   imports from any simulator. Answers: what does executing this puzzle, at this difficulty,
   on this class of machine, cost in seconds, joules and money?
2. **`tools/simulators/empowering-strategies/`** — a network simulator for the EmPoWering mechanism:
   consensus, minting, the reward pool, and the on-ramp from proof-of-work into proof-of-stake.
   Consumes (1).

Both are new. Conventions are borrowed from `blend` and `tsi`; code is not.

## Notation

This document follows the tokenomics report's contract: prose and code spans carry
**self-describing names**, equations carry **symbols**, the two are strictly interchangeable,
and every equation is followed by its code sibling. `make notation` enforces it there and the
same gate should cover this document once the work lands.

Names taken from the report's section 1.0 table are used unchanged — `reward_per_claim`,
`claim_fee`, `distribution_rate`, `target_claims_per_block`, `genesis_pool`, `pool`,
`difficulty_target`, `equilibrium_difficulty`, `hashrate`, `equilibrium_hashrate`,
`cost_per_candidate`, `field_modulus`, `block_seconds`, `blocks_per_epoch`, `pow_share`,
`claims_in_block`, `smoothing`, `fee_ratio`, `txs_per_block`, `initial_stake`,
`launch_supply`.

**New quantities this work introduces**, to be added to that table when the branch lands:

| name | symbol | meaning |
| --- | --- | --- |
| `candidates_per_claim` | $A$ | expected candidates a miner tries per winning claim |
| `seconds_per_candidate` | $s$ | wall time for one candidate, on one core of a bucket |
| `joules_per_candidate` | $\varepsilon$ | energy for one candidate, on a stated power basis |
| `work_cost_per_claim` | $W$ | money burnt winning one claim |
| `electricity_price` | $P_\text{kWh}$ | tariff, swept as a band rather than a point |
| `break_even_token_price` | $\pi^\ast$ | token price below which mining stops paying |
| `marginal_watts` / `total_watts` | — | draw above idle; whole-platform draw at the wall |
| `utilization` / `platform_watts` / `psu_efficiency` | — | the three corrections between a datasheet and a joule |
| `device_bucket` | — | Raspberry Pi 5, Apple M3/M4 Mac, Intel PC, GPU rig |
| `hashrate_share` | — | one node's share of network mining power |
| `claims_to_graduate` / `graduation_epochs` | — | claims and time to reach the minimum stake |
| `joiner_rate` | — | candidate nodes arriving per epoch (a scenario input) |

A naming collision between the notation table and the config is **settled**: a unit of
proof-of-work search is a **candidate**, and the tokenomics branch has renamed the table's
entry for what one costs to `cost_per_candidate`. The config's existing
`seconds_per_candidate` therefore stands, and everything the estimator adds follows the same
word — `candidates_per_claim`, `joules_per_candidate`.

---

## Part 1 — the cost estimator

### The split

| layer | owns | changes when |
| --- | --- | --- |
| puzzle | what one unit of work is; how difficulty maps to units | you add a proof-of-work |
| profile | what a machine costs to run | you add a device bucket |
| rate table | `seconds_per_candidate` for a `(puzzle, device_bucket)` pair | you measure something |
| kernel | joules, money, `cost_per_candidate`, break-even | never |

Puzzles and profiles meet only in the rate table. Adding a proof-of-work is one puzzle
definition plus one rate measurement per bucket, with the rest flagged as estimated.

### Puzzle interface

- **`candidates_per_claim(difficulty_target)`** — for a threshold puzzle this is the field over
  the target:

  $$A \;=\; \frac{p}{d}$$

  | `candidates_per_claim = field_modulus / difficulty_target` |
  | --- |

  Equi-X does not follow it: a solve yields about two solutions per attempt
  (`solutions_mean` 1.97–2.17 in the benchmark data), so effort and attempt count differ by
  two to three times.
- **`distribution`** — geometric for a threshold puzzle, which is what supplies the p50, p95
  and p99 tail. Not every scheme is geometric.
- **`setup_per_challenge`** — Equi-X compiles a program per challenge; Poseidon2 does not.
  This is what amortises differently at low difficulty.
- **`parallel_model`** — Poseidon2 grinding is embarrassingly parallel; Equi-X carries
  per-attempt memory and its measured `scaling_efficiency` runs 0.75 to 1.24; a verifiable
  delay function gets nothing from cores at all.
- **`cost_shape`** — everything above assumes energy is spent *per candidate*. Proof-of-space is
  not: a held plot draws watts per terabyte per hour regardless of activity. Two variants are
  declared now and only the per-candidate one implemented, so the kernel need not be rewritten
  later.
- **`verify_cost`** — cheap to carry, and it prices what it costs the *network* to reject a
  flood, not only what it costs an attacker to send one.

### Device profiles

A thermal design point is a cooling specification, not a draw. Three corrections sit between
a datasheet number and a joule:

| term | why |
| --- | --- |
| `utilization` | a latency-bound hash loop can sit at 40–60% of the rated point; a turbo-happy desktop part exceeds its base power for minutes |
| `platform_watts` | a 125 W processor lives in a machine pulling over 200 W at the wall |
| `psu_efficiency` | datasheets are measured on the direct-current side; electricity bills are on the alternating-current side |

Each profile carries its core count, rated power, those three corrections, a duration derate
and a provenance tag per field. Two bases are computed side by side:

| `marginal_watts = utilization * rated_watts / psu_efficiency` |
| --- |
| `total_watts = (utilization * rated_watts + platform_watts) / psu_efficiency` |

`marginal_watts` is the honest participant whose machine was already running; `total_watts` is
the dedicated miner and the attacker farm.

### Difficulty is a multiplier, not an index

Time to a claim factorises into a count set by difficulty and a rate set by the machine:

$$t \;=\; A(d)\cdot s$$

| `seconds_per_claim = candidates_per_claim * seconds_per_candidate` |
| --- |

Checked against the mining benchmark over a thirty-fold effort range:

| device | effort 100 | 300 | 1000 | 3000 | drift |
| --- | --- | --- | --- | --- | --- |
| RPi5-16GB | 19.42 ms | 20.55 | 22.04 | 22.42 | +15%, monotone |
| RPi5-8GB | 19.37 | 20.50 | 21.98 | 22.38 | +15%, monotone |
| Intel 285HX | 3.33 | 4.03 | 4.79 | 3.92 | ±20%, non-monotone |
| M4 Pro | 3.67 | 4.33 | 5.08 | 4.26 | ±25%, non-monotone |

Absolutes drift 15 to 25%; **device ratios drift under 2%** — Pi over M4 moves 5.29 to 5.26,
Pi over Intel 5.84 to 5.71. All four devices share an identical coefficient of variation per
effort level (84.3, 111.1, 97.9, 81.1%), so these runs used common random draws: absolute means
carry 12 to 16% standard error, but the paired ratios are far better determined than that.

Since the efficiency frontier is a ratio, it is difficulty-invariant to within noise.
Difficulty therefore enters as a swept variable plus a duration derate, never as a table axis.

### The sparse-rate problem

|  | Pi 5 | M4 | Intel | GPU rig |
| --- | --- | --- | --- | --- |
| Poseidon2 | measured | measured | **empty** | **empty** |
| Equi-X | measured, twice | measured | measured | **empty** |

The estimator prints a **coverage matrix** and tags every cell measured, scaled or estimated.
Filling an empty cell from a measured one by a device-class factor is licensed **within a row**
— that is what the 2% ratio invariance above buys. It is not licensed across rows: the Pi over
M4 ratio is 5.3 on Equi-X and 6.8 on Poseidon2, so cross-puzzle propagation would import a 30%
error silently. The kernel refuses it rather than documenting it.

### Three inversions

No assumed token price, no guessed graphics-processor throughput, no assumed device mix. Each
is reported as the threshold at which the answer changes:

- **token price** → `break_even_token_price`, below which mining stops paying
- **graphics-processor throughput** → the efficiency at which each processor bucket is priced out
- **device mix** → an output of the frontier, not an input

### Layout

```
tools/powcost/
  puzzles.py    # Poseidon2, Equi-X, registry
  profiles.py   # buckets, rated power to watts, derate
  rates.py      # (puzzle, bucket) to seconds_per_candidate, provenance, coverage
  kernel.py     # joules, seconds, money per claim; tail quantiles; cost_per_candidate
  vector.py     # the only module importing numpy
```

---

## Part 2 — the network simulator

### 2.1 Consensus and proof-of-work, simulated but not executed

No grinding. Proof-of-work is a **Poisson process**: a node with candidate rate `candidate_rate` at
the current target finds claims at

$$\lambda_i \;=\; r_i\,\frac{d}{p}$$

| `node_claim_rate = candidate_rate * difficulty_target / field_modulus` |
| --- |

**The performance decision.** Do not sample per node per block — a million nodes over 21,600
blocks is two times ten to the tenth draws. Instead:

1. draw the block's claim count once,

   $$c_n \sim \mathrm{Poisson}\!\left(H\,\Delta_b\,\frac{d}{p}\right)$$

   | `claims_in_block ~ Poisson(hashrate * block_seconds * difficulty_target / field_modulus)` |
   | --- |

2. attribute those claims to nodes by a multinomial over `hashrate_share`.

This is **exact in distribution**, not an approximation: a superposition of independent Poisson
processes is Poisson, and conditional on the total, the allocation is multinomial. Cost falls to
the number of blocks plus the number of claims. Per-node claim counts fall out directly, which
is what the graduation study needs.

Consensus uses the same trick: one leader drawn per slot, weighted by stake.

The retarget is reproduced in **exact integer arithmetic**, matching the specification's
one-state form

$$d_{n+1} \;=\; \frac{T\,d_n}{(1-q)\,c_n + q\,T}$$

| `next_difficulty_target = target_claims_per_block * difficulty_target / ((1 - smoothing) * claims_in_block + smoothing * target_claims_per_block)` |
| --- |

with `smoothing = smoothing_factor / smoothing_precision`, which the report shows equals 9/10.

**Granularity is block-level throughout**, and `distribution_rate` is a free parameter.

One consequence to keep in view: `distribution_rate` governs how fast the pool converges, never
where — but the claim rate is pinned at `target_claims_per_block` regardless. So raising it
compresses the decay while leaving graduation's claim requirement untouched. High values are
therefore a **different regime, not a fast-forward** of low ones, and cannot be used to shorten
runs. At the specified 1/200 a full trajectory is about 2,085 epochs, roughly **45 million
sequential blocks**, and the retarget cannot be vectorised because each target depends on the
previous block's count.

The inner loop is therefore compiled, with a plain-Python implementation of the same step kept
alongside and gated to agree — the two-engines discipline the repo already applies to float
against integer, and to Python against JavaScript.

### 2.2 Economics and the pool

Pool state in exact integers, following the existing integer engine's precedent:

| `next_pool = pool - payout + epoch_refill` |
| --- |
| `reward_per_claim = distribution_rate * pool / (target_claims_per_block * blocks_per_epoch)` |
| `epoch_refill = pow_share * blocks_per_epoch * txs_per_block * avg_tx_fee` |

`claim_fee` comes from the claim transaction's bytes and gas at the resting price, as the
report's fee section derives it.

**Validation gate.** The simulator must reproduce the closed forms already derived in
`reports/EmPoWering/tokenomics/tokenomics-model.md`: the reward trajectory, pool stability, the
stranded reserve, the controller's fixed points and time constant, and the worked example.
Those are free correctness tests and they should be wired in from the first commit rather than
retrofitted.

Protocol constants come from a **snapshot of `configs/specified.toml` copied into this
simulator**, so the branch is self-contained and any divergence from the tokenomics config is
explicit in git history.

### 2.3 Scenarios and working regions

Axes: network use pattern, token valuation, and the parameter set — `target_claims_per_block`,
`pow_share`, `distribution_rate`, `genesis_pool`, `initial_stake`.

Node arrivals are **exogenous** — `joiner_rate` is the network-use-pattern axis — while
**participation is endogenous**: a candidate mines only if its bucket clears break-even at the
current target and token price. That is what connects the scenario axis to the affordability
study, and what produces a mixed population rather than a single winner.

Output: two-dimensional feasibility maps shaded by which constraint binds —

| `self_funding = txs_per_block > target_claims_per_block / (fee_ratio * pow_share)` |
| --- |
| `claiming_continues = reward_per_claim > claim_fee` |
| `affordable = reward_per_claim - claim_fee > work_cost_per_claim` |

together with the builder-edge and attacker-share bounds the report already derives, and
whether graduation completes inside the horizon.

### 2.4 Graduation — the on-ramp metric

A node accumulates `reward_per_claim` per claim and graduates when its balance reaches the
minimum stake, which the config sets at ten to the minus fifth of `launch_supply`, that is
**100,000 LGO**.

| `claims_to_graduate = min_stake / reward_per_claim` |
| --- |
| `graduation_epochs = claims_to_graduate / (target_claims_per_block * blocks_per_epoch * hashrate_share)` |

From the specified parameter set, as a prediction to test rather than a result: the opening
`reward_per_claim` is 1.157 LGO, so **86,400 claims** are needed, against a network minting
216,000 claims per epoch.

| `hashrate_share` | epochs | years |
| --- | --- | --- |
| 10% | 4 | 0.08 |
| 1% | 40 | 0.82 |
| 0.1% | 400 | 8.2 |

And `reward_per_claim` decays: by epoch 1460, thirty years in, it is 8.0 times ten to the minus
four LGO, so graduation then needs about 125 million claims and is unreachable.

**So the on-ramp has a closing window, and its width is set by `genesis_pool` and
`distribution_rate`.** Measuring that window is the single most valuable output of this
simulator, and it speaks directly to the report's open policy question about whether half a
percent of supply is the intended bootstrap subsidy.

Two events, measured separately — they are not the same:

- **graduation** — balance reaches the minimum stake, so the node can begin staking and
  providing service
- **mining exit** — mining stops paying relative to staking alone

A graduated node may rationally keep mining. Service provision may carry thresholds distinct
from the staking minimum; those need confirming against the specification tree.

### 2.5 The proof-of-work against proof-of-stake crossover

The comparison needs care and the simulator should not paper over it: **a mining margin is a
return on operating expense**, electricity, while **staking is a return on capital**, tokens
held, with an opportunity cost. They are not directly comparable without a discount rate.

The measurable form: for a node holding stake and running one device bucket, LGO per day from
staking against LGO per day from mining net of electricity. The crossover is where *adding*
mining capacity stops paying — a marginal question, not an average one.

### 2.6 Affordability and the difficulty floor

Under free entry the target settles where the marginal miner breaks even:

$$\sigma_e - \varphi \;=\; \frac{p}{d^\ast}\,\kappa
\qquad\Longrightarrow\qquad
d^\ast \;=\; \frac{p\,\kappa}{\sigma_e - \varphi}$$

| `equilibrium_difficulty = field_modulus * cost_per_candidate / (reward_per_claim - claim_fee)` |
| --- |

As the reward decays the target **relaxes proportionally**, holding the cost of a win pinned to
the reward. Two boundaries follow, different in kind:

- **Lower** — when the margin falls to one candidate's cost, `candidates_per_claim` approaches one and
  a single hash wins. Proof-of-work is then free and proves nothing. This is the real floor and
  it arrives long before any protocol bound on the target.
- **Upper** — when the reward falls below the fee, claiming stops outright; the report's
  stopping condition already models this.

The finding to measure is per bucket, not global. **The target settles at the cheapest bucket's
break-even, and every more expensive bucket is excluded** — a Raspberry Pi's cost per win
exceeds the margin while the network sits in equilibrium. That is the decentralisation
statement.

What softens it is the two power bases: a Pi on an already-running machine paying only
`marginal_watts` may still clear a bar set by a graphics-processor farm paying `total_watts`
plus capital recovery. That is why both are carried, and it is what makes a mixed population
possible rather than a degenerate single-winner one.

### 2.7 ALTERNATIVE — claim capacity that accommodates joiners

**Held clearly separate from the base**, following the report's convention of keeping candidate
changes above the line. Not part of any base result, reported in its own section, never mixed
into the feasibility maps without a label.

The proposal: `target_claims_per_block` is not a fixed target but responds to `joiner_rate`.

**The objection to resolve first.** Total payout per epoch is `distribution_rate * pool`
regardless of the target, and the reward is that payout divided by the epoch's claims. So the
target does not change the money — **it changes only how the same money is split**. Raising it
to accommodate more joiners lowers each claim proportionally, and since graduation requires
about 86,400 claims at the opening reward, splitting makes per-node graduation *slower*, not
faster. If the goal is to pay joiners more, the target is the wrong dial; `distribution_rate`
or the refill is.

**Where the proposal does have force.** The target is a limit on *participant throughput*, not
only on granularity: at ten claims a block only 216,000 claims exist per epoch, so the channel
bounds how many distinct nodes can be served per unit time regardless of how much money is
available. If the binding constraint on the on-ramp is participant slots rather than value per
slot, raising the target helps and the objection does not apply.

**So the study's first question is which constraint actually binds** — money or slots. The
simulator can settle that, and the answer determines whether this alternative is worth pursuing
at all.

Further consequences to analyse:

- The clean drain result assumes a fixed target and is lost.
- The controller's fixed-point analysis assumes a fixed reference.
- **Sybil exposure**: joiner count is forgeable. Under a fixed target the per-epoch payout is
  bounded by construction; under a joiner-responsive target the *number of claims* becomes
  attacker-influenced. Since the payout is still the budget this does not drain the pool faster,
  but it does let an attacker dilute honest claimants and capture a larger share of the same
  payout. This is the main attack and it should be measured, not argued.

### Layout

```
tools/simulators/empowering-strategies/
  config.py     # frozen dataclass, validated in __post_init__ (blend convention)
  rng.py        # seeded, common random numbers for paired scenarios (tsi convention)
  consensus.py  # slot lottery, stake
  work.py       # Poisson and multinomial claim attribution, integer retarget
  economics.py  # pool, reward, fees, exact-integer engine
  nodes.py      # population, device buckets, balances, graduation, exit
  scenarios.py  # traffic patterns, token valuations
  sweep.py      # expansion, parallel execution, persistence (tsi convention)
  metrics.py    # config recorded into every output row (blend convention)
  alternative/  # section 2.7, physically separated from the base model
```

---

## Phases — status

| # | phase | state |
| --- | --- | --- |
| 0 | device profiles: rated power, `utilization`, the Intel Poseidon2 gap | **partial** — four buckets sourced with citations, two audited; Pi 5 and Intel audits never ran, Intel and accelerator rates still absent |
| 1 | simulator skeleton: work process, economics, gated against the closed forms | **done** — reproduces the report's decay table digit for digit |
| 2 | `powcost` kernel, puzzles, rates, coverage matrix, propagation rule | **done** |
| 3 | `powcost` vector layer and per-node bucket assignment | **done differently** — bucket assignment landed in the simulator; the vector layer was never needed, because participation turned out to depend only on the target and the token price, so it is decided per device class rather than per node |
| 4 | node population, graduation, the crossover | **two thirds** — population and graduation done and gated; the mining-against-staking crossover has its arithmetic in `consensus.py` and has never been run |
| 5 | scenarios, sweeps, working-region maps | **done** |
| 6 | affordability against the difficulty floor | **done** — subsumed by the frontier: the exclusion band came out of phase 5 rather than needing its own study |
| 7 | ALTERNATIVE, separated | **done** — the claim target is neutral to the on-ramp; block space and the steady margin are what it costs |
| 8 | duration derate measurement | **blocked** — needs an hour of Raspberry Pi hardware |

## What is next

Ordered by what would change a conclusion, not by what is easiest.

**A. The mining-against-staking crossover.** The one explicit requirement still unmeasured:
at what point does a graduated node stop mining and simply stake? `consensus.py` carries the
arithmetic and says honestly that it is a lower bound, since mining pays an electricity cost
staking does not and the two are a return on operating expense against a return on capital.
It has never been exercised. Everything it needs now exists.

**B. Ground the minimum stake in the specification.** The whole ceiling result rests on
`min_stake` being the threshold a miner must actually reach, and on whether providing service
carries a different one. This has been flagged since the finding appeared and is still open;
the specification tree is available locally, so it is a reading task rather than a blocked one.

**C. Run a full horizon.** Everything measured so far spans 40 to 600 epochs of a trajectory
that takes about 2,085 to drain. The window-closing and near-saturation claims are consistent
across the runs done but are extrapolations, and the fee-funded era — where the steady margin
binds and the ALTERNATIVE actually bites — has never been simulated at all.

**D. The compiled inner loop.** Pure Python runs about 3.5 seconds per forty epochs, so a full
horizon is roughly three minutes and a sweep over it is hours. C is uncomfortable without this
and cheap with it. The plain-Python engine stays as the oracle either way.

**E. Figures, then a written document.** Nothing here is legible to anyone who has not read the
code. The repo convention is that every figure carries the command that regenerates it.

## Open inputs

- Power-counter readings to calibrate `utilization`: `powermetrics` on the Mac, RAPL on the
  Fedora box. Both need root, so they are the user's runs to make. This is what would let the
  Apple bucket report a marginal draw at all.
- The Intel Poseidon2 rate, from the existing benchmark on the Fedora machine. The rate table
  refuses to infer it from the Equi-X figure and will keep refusing.
- An accelerator rate for any puzzle. The largest single gap, and the class most likely to
  dominate an arithmetic hash. Inverted for now into a break-even efficiency.
- Sustained-load derate: an hour of pinned Raspberry Pi 5 grinding with rate logged over time.
  It matters more for mining, which is fully duty-cycled by construction, than for admission,
  and the benchmark data tops out at 29 seconds against a reward puzzle that runs for hours.
- Whether service provision carries stake thresholds distinct from the staking minimum.
