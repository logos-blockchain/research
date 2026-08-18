# EmPoWering, from base principles — the plan

A de-novo redesign of the mechanism. Not an amendment to the current specification: the design
starts from eight stated principles and is mapped back onto the existing tokenomic machinery
afterwards, so that every piece of the old design must re-justify itself or go.

The branch is based on `EmPoWering-simulator` deliberately: the fee model (`txsize`,
lepta-denominated two-market pricing), the cost estimator (`powcost`), the emission and
service machinery, and 196 validation gates are verified components this work consumes rather
than rebuilds.

## 0. The principles, as requirements

Stated by the design owner, 2026-08-18. The report validates against these by number.

- **R1 — Minimality.** As few parameters as possible; the design as simple as possible.
- **R2 — Two regimes.** A bootstrapping phase and a post-bootstrapping phase, serving
  different purposes, explicitly defined.
- **R3 — Bootstrap purpose.** Onboard as many nodes as possible into PoS along the path
  PoW mining → `min_stake` → service provision.
- **R4 — Bootstrap parameterisation.** Exactly three parameters: the PoW rewards pool
  (% of TGE), the expected number of onboarded nodes, and the expected duration (years).
- **R5 — Spike tolerance.** Large cohorts arriving together must not be pushed away.
  Arrivals are not assumed uniform over the phase.
- **R6 — Pool integrity and epoch accounting.** Rewards are paid until the pool is
  exhausted — no money is created. The pool refills from transaction fees, accounted
  per epoch. The reward value is known and fixed for each epoch (revisitable if it
  proves complex). If an epoch's sub-pool saturates, payment continues from further
  pool funds; the moment is the **(sub)pool saturation point**.
- **R7 — Post-bootstrap objective.** (a) Rewards are paid from the previous epoch's
  fees; (b) claims spread evenly across the epoch — the saturation point lands as close
  to the epoch end as possible.
- **R8 — Reward anchor.** Post-bootstrap, one reward pays for a transfer plus an
  inscription (transfer ≈ inscription assumed). During bootstrap the reward is larger,
  subsidised from the TGE pool.

## 1. The model the principles force

Working through the requirements yields a shape rather than a menu. Most of it is determined;
the genuinely open choices are pulled out into §3.

### 1.1 Budgets, not rates

The current mechanism is **rate-based**: `distribution_rate` fixes the fraction of the pool an
epoch pays, and the difficulty controller fixes the claim count, so the pool decays
geometrically and never actually ends. R4 and R6 replace this with a **budget**:

| `epoch_budget = tge_endowment / bootstrap_epochs + fees_diverted_last_epoch` |
| --- |

A per-epoch sub-pool. Linear amortisation of the endowment over the expected duration, plus
the fee refill accounted with the one-epoch delay R6 allows. The endowment part hits zero at
exactly the expected duration if arrivals match expectations — the phase has an *end*, which
the geometric design never had.

### 1.2 Saturation, not rationing (R5)

Claims are paid at the epoch's fixed reward until the sub-pool is spent. If a large cohort
arrives and the sub-pool saturates mid-epoch, **payment continues, drawing the remaining pool
forward** — the saturation point is recorded, and the effective end of bootstrap moves earlier.
A spike is absorbed by shortening the phase, not by pricing out the cohort. The expected
duration is exactly that — an expectation, not a guarantee.

This inverts the current design's central behaviour, where the controller holds the claim
count flat against a 380-fold load change and a cohort's arrival only thins everyone's slice.

### 1.3 The reward is set by purpose, not by the pool (R8)

Post-bootstrap: `reward = fee(transfer) + fee(inscription) ≈ 2 × fee(transfer)` — measured in
the fee market's own units, so it tracks the fee level by construction and needs no parameter.
Bootstrap: the same anchor times a subsidy factor (the one genuinely open design choice, §3
Q1). The reward is fixed for the epoch (R6), which preserves the property the current
specification is built around: a wallet can construct a self-funding claim before submitting.

With the reward set by purpose and the budget set by the endowment, **the claim count is a
consequence**: `capacity = epoch_budget / reward`. Nothing targets it.

### 1.4 The difficulty becomes a throttle, not an economic controller

With no claim-count target, the retarget's job changes by regime:

- **Bootstrap:** difficulty is a spam floor only. Claims are welcome at any rate; saturation
  handles the economics. (The existing EMA machinery survives with a permissive target.)
- **Post-bootstrap (R7b):** the difficulty *is* the even-spreading mechanism. Target the
  saturation point at the epoch end: if the budget ran out early, tighten; if budget was left
  over, relax. The existing EMA retarget maps onto this with a derived per-epoch target,
  `capacity / blocks_per_epoch` — the machinery is reused, only the target stops being a
  constant.

### 1.5 The transition is automatic (R2)

Bootstrap ends when the TGE endowment component of the pool reaches zero — by schedule at the
expected duration, earlier under spikes. Post-bootstrap begins the next epoch: budget = last
epoch's diverted fees (R7a), reward drops from the subsidised to the anchor level. No
transition parameter, no governance action.

### 1.6 The consistency identity, and what it exposes

The three R4 parameters are not independent — they carry an internal consistency check:

| `implied_conversion_efficiency = expected_nodes * min_stake / tge_endowment` |
| --- |

Every elevation costs one bond, so a `(pool, N, T)` triple silently asserts that this fraction
of what the pool pays out actually reaches bonds. The elevation study measured **11.4%** when
bonded miners keep mining and **51.9%** when they retire — so the model *validates triples*:
a triple whose implied efficiency exceeds the achievable band is unsatisfiable and the design
says so at parameterisation time, not after a simulation. This is the strongest single result
carried over from the target-parameterisation work.

Duration enters separately: `T` fixes the per-epoch budget and therefore the onboarding
*pace*; `pool` and `N` fix the *total*. Fee drag couples them: each claim pays its own fee, so
smaller rewards mean more claims per bond and more of the pool leaking to fees — quantified in
phase A.

### 1.7 Parameter accounting (R1)

| current design | de-novo |
| --- | --- |
| `genesis_pool_fraction` | **pool % of TGE** (R4) |
| `distribution_rate` (1/200) | — derived: endowment / duration |
| `target_claims_per_block` (10) | — derived: budget / reward |
| `pow_share` (10%) | kept, one parameter (the fee diversion) |
| `smoothing F/P` | kept inside the retarget, unchanged |
| genesis difficulty | kept, seed only |
| — | **expected nodes N** (R4) |
| — | **expected duration T** (R4) |
| reward: emergent from pool | — defined: fee anchor × subsidy (bootstrap), fee anchor (post) |

Net: the two rate parameters that required simulation to defend (`distribution_rate`,
`target_claims_per_block`) are replaced by two parameters a designer can state an intent with
(`N`, `T`), plus the subsidy question of §3 Q1.

## 2. Work plan

### Phase A — the model (docs first, ~no code)

`MODEL.md`: the design of §1 written out normatively — state variables, per-epoch and
per-block transition rules in the specification's integer style, both regimes, the saturation
semantics, the transition rule, and the consistency identity with its efficiency band.
Includes the closed forms: budget trajectory under uniform and under spiky arrivals, expected
saturation point, fee-drag as a function of reward size, time-to-bond for a reference device
(from `powcost`).

Settle the §3 design questions **one at a time** before freezing the model.

### Phase B — the mapping (`MAPPING.md`)

Old machinery → new model, mechanism by mechanism: what survives untouched (SDP/`min_stake`,
service rewards, emission control, both fee markets, claim transaction format, pool-refill
plumbing), what changes meaning (the retarget's target becomes derived; `epoch_pow_reward`
becomes budget-based), what is deleted (`distribution_rate`, the claim-count target as an
economic quantity), and what each spec document would need amended. This is the artefact that
makes the de-novo design adoptable rather than academic.

### Phase C — the simulator

New package `empowering_denovo_sim`, reusing verified components (`txsize`, fee model,
`powcost` adapter, emission, services) as libraries. New core:

- budget/sub-pool engine with saturation and borrow-forward, integer arithmetic, pool ≥ 0 as
  an invariant (R6);
- arrival processes: uniform, Poisson-burst cohorts, heavy-tailed interest spikes (R5);
- the two-regime reward rule and automatic transition (R2, R8);
- the throttle controller for R7b, reusing the EMA retarget with the derived target;
- conversion tracking (balances vs bonds), per-cohort admission metrics.

Validation-gate suite from day one, in the established style.

### Phase D — simulations and the report (`reports/EmPoWering/denovo/`)

Scenario matrix: arrivals {uniform, 10× spike, 100× cohort, front-loaded, back-loaded} ×
triples {satisfiable, marginal, unsatisfiable} × retirement {on, off}. The report validates
each requirement **by number**:

- R4/R6: pool trajectory, never negative, ends when scheduled or earlier under spikes;
- R5: cohort admission — time-to-bond for a spike cohort vs the same nodes arriving uniformly
  (the current design's rationing, reproduced from `EmPoWering-simulator`, as the baseline);
- R7: post-phase saturation-point distribution vs the epoch end; evenness of claims;
- R8: reward vs bundle cost across fee levels, both regimes;
- R1: the parameter table of §1.7, honestly accounted;
- and the consistency identity against the measured efficiency band.

## 3. Design questions (to be settled one by one, before Phase A freezes)

1. **The bootstrap reward rule** — SETTLED 2026-08-18: **demand-indexed**,
   `reward_e = max(anchor, epoch_budget / claims_seen_last_epoch)`. Zero new parameters; quiet
   epochs pay big, spikes dilute per-claim value while everyone is still paid and the budget
   borrows forward; cohorts arriving in different epochs earn at different rates, which the
   report must show honestly. The alternatives are to be RECORDED IN THE REPORT as
   alternatives, with short descriptions: (a) a fixed subsidy multiple `c × anchor` — one new
   parameter, every cohort earns at the same rate for the whole phase, simplest to reason
   about, but `c` needs defending and a badly sized `c` either exhausts the pool early or
   onboards too slowly; (b) a time-to-bond anchor — the reward sized so a reference device
   (Pi 5, from `powcost`) reaches `min_stake` in a target number of epochs, no free parameter
   and the strongest onboarding story, but it couples the reward to the difficulty and field
   size, which is the entanglement this redesign removes.
2. **Borrow-forward semantics** — SETTLED 2026-08-18: **the undivided endowment**. On
   saturation, payment continues from the remaining TGE endowment at large, and every later
   sub-pool is recomputed as `remaining_endowment / remaining_epochs`. A spike therefore thins
   all later epochs slightly and pulls the phase's end earlier — no cliff, no dim-epoch
   oscillation incentive, and the budget formula stays one line. The explicit
   next-epoch-first alternative (legible accounting, but a dim epoch after every bright one
   and a wait-it-out incentive) and the hard cap (rationing — rejected by R5 outright) go in
   the report as alternatives.
3. **Post-phase budget source**: all of the previous epoch's diverted fees, or an EMA of them
   (smoother, one more state variable).
4. **Bootstrap difficulty floor**: pure spam floor, or keep mild within-epoch smoothing.
5. **Epoch-fixed reward** (R6's revisitable clause): keep — it costs nothing in this design
   and preserves the wallet's self-funding claim. Recommend keep; confirm.
6. **Transition hysteresis**: none (recommend), or a guard band so fee noise near the boundary
   cannot flap regimes.
