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
forward** — the saturation point is recorded. A spike is absorbed by borrowing against later
epochs, not by pricing out the cohort. It does **not** shorten the phase: the schedule
re-spreads whatever remains over the epochs still left, so the deadline holds (measured: a ×100
spike ends at 196 against uniform's 196). The expected duration is exactly that — an
expectation, not a guarantee — but a spike is not what moves it.

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

**One throttle, both phases** (settled at §3 Q4, superseding an earlier two-role sketch). The
existing EMA retarget runs unchanged in both regimes against a derived per-epoch target:

| `claims_target_per_block(e) = capacity_e / blocks_per_epoch`  where  `capacity_e = epoch_budget_e / reward_e` |
| --- |

The machinery is reused; only the target stops being a constant. Its job is R7b's evenness --
steering the saturation point toward the epoch end -- in *both* phases, and it is no longer an
economic controller at all: the difficulty cannot change a node's share of claims, only their
granularity, so spike absorption is carried entirely by the demand-indexed reward and the
borrow-forward. The phases differ in nothing but budget source and reward level.

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
of what the pool pays out actually reaches bonds — so the model *validates triples*: a triple
whose implied efficiency exceeds what the mechanism actually converts is unsatisfiable, and the
design says so at parameterisation time rather than after a simulation. This is the strongest
single result carried over from the target-parameterisation work.

The ceiling was originally imported from the elevation study's **11.4% / 51.9%**. It has since
been re-measured *in this mechanism* and is not one band but two regimes: **15% when nobody
retires**, flat in the arrival rate, and **25–74% when they do**, rising with it. `params.py`
reports both verdicts separately, because a triple above 15% is satisfiable only on an
assumption about behaviour that nothing in the mechanism pays for.

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

## 3. Design questions — all settled

Q1-Q6 settled 2026-08-18 (Q4 amended same day, see MODEL.md section 9). Simulation raised
three more; Q7 settled 2026-08-19, Q8/Q9 pending as a coupled pair:

7. **The post-deadline remainder** — SETTLED 2026-08-19: **the nominal-rate tail**. Past the
   expected duration each epoch's sub-pool caps at `endowment_genesis // bootstrap_epochs`
   until spent. Zero new parameters; back-loaded conversion went from 4.5% to 76-100% across
   draws. Rejected: the whole-remainder dump (measured 2.6% conversion), folding to fees at
   the deadline (abandons the onboarding purpose of the remainder).
8. **The burst window** — SETTLED 2026-08-19: **unbounded**, R6 read literally. *(2026-08-20:
   the simulations later showed the exposure is closable at low cost -- see MODEL.md 8.5, the
   asterisked `de novo*` variant -- so the decision stands but is now an informed one rather
   than a concession made blind. The flat-budget cap this entry rejected was rejected for the
   right reason; the workable form bounds the draw as a fraction of the remaining endowment.)* The pool
   pays until exhausted and a whale is a claimant like any other; the endowment is
   first-come by design and the 17%/50%/56% capture at 1x/3x/10x ships as a documented,
   gated property. Rejected: caps at 3x or 2x budget per epoch (one constant against R1,
   softens R6, and the 2x cap would already queue the measured honest x100 cohort).
9. **Index damping** — SETTLED 2026-08-19: **raw claims_prev**. Zero state, and the index's
   one-epoch crash IS the whale response (reward /120 after a burst). The period-2 cycle
   under a participation cliff at the operating reward ships as a documented, gated hazard.
   Rejected: the beta = 1/2 EMA (kills the cycle but widens the whale window, only
   affordable with a Q8 cap that was itself rejected).


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
3. **Post-phase budget source** — SETTLED 2026-08-18: **the previous epoch's diverted fees,
   raw**. `budget_e = fees_diverted(e-1)`; zero extra state, R7a verbatim, and the epoch-fixed
   reward already insulates claimants from within-epoch noise — a quiet epoch simply funds a
   small next one and the throttle absorbs the swing. The EMA variant is recorded as an
   alternative, to be revisited only if simulations show raw budgets whipsawing the throttle.
4. **The difficulty's role** — SETTLED 2026-08-18 as "one throttle, both phases", then
   **AMENDED same day** (MODEL.md §9): formalising the rules showed the unified throttle
   composes badly with Q1 — a throttle at `capacity / blocks` with the demand-indexed reward
   pins admissions at the previous epoch's level, so a spike is never admitted and the
   cohort is rationed indefinitely, which is exactly what R5 rejects and would leave R6's
   saturation semantics dead code. Amended to: **one retarget implementation, two targets** —
   a constant floor during bootstrap (admission control is economic there), the derived
   `capacity / blocks` target after the transition. The unified-throttle variant goes in the
   report's alternatives table with this failure mode as its description. Original entry
   kept below for the audit trail.

   Originally: **one throttle, both phases**, superseding
   this plan's own two-role sketch in §1.4. The same EMA retarget runs in both regimes with
   the derived target `capacity_e / blocks_per_epoch`, `capacity = budget / reward`. The
   phases differ only in budget source and reward level; there is no per-phase difficulty
   logic and no discontinuity at the transition. Spike absorption is fully economic
   (demand-indexed reward + borrow-forward) — the difficulty never changes a node's SHARE of
   claims, only their granularity — and claims spread evenly in both phases. The static spam
   floor (spikes bunch the epoch's capacity into its first blocks, contending for block
   space, plus a step at the transition) and the floor-with-mild-smoothing middle ground go
   in the report as alternatives.
5. **Epoch-fixed reward** — SETTLED 2026-08-18: **kept**. Under Q1-Q4 it is one division at
   the epoch boundary, and fixity is what lets a wallet construct a self-funding claim before
   submitting -- the property the existing claim format is built around. Recomputing at the
   saturation point (stretching borrowed funds at a reduced reward) is recorded as an
   alternative; it breaks claim self-funding for exactly the cohort R5 protects.
6. **Transition** — SETTLED 2026-08-18: **component accounting, no hysteresis**. The pool
   tracks the TGE endowment and the fee inflow as separate buckets; the endowment is only
   ever drawn down (sub-pools and Q2's borrow-forward both charge it), so the regime test
   `endowment == 0` is monotone, fires once, and is irreversible by construction. No guard
   band exists because the flapping it would guard against cannot occur. The single-bucket
   level test, which would need one, is recorded as the alternative it replaces.

---

# Revision plan: the pooling/distributing/releasing substrate (logos-lips PR 375)

*Planned 2026-08-22 against PR head `2b3b698` (branch `pooling-distributing`). Status at
planning time: thomaslavaur APPROVED after changes, madxor's review pending, the Verified
checklist open. The PR is still moving; every step below re-checks against the head it lands
on, and this section records the head it was planned against.*

## What the RFC changes

`block-rewards.md` 1.1.0 (with `execution-market.md` 1.2.0, `storage-markets.md`, and the
overview propagating): fees are no longer burned and rewards no longer minted. All Execution
base fees and Permanent Storage fees route into a **pending rewards pool** `P_t`; block
rewards distribute the *windowed average* of pooled fees (`R̄_t` over `T = 120` blocks, not
the latest block's fee) topped up by a **release** `ι_t` from a finite genesis reserve
`B_0 = I_max · S_cap · Y = 10⁹ LGO`; `S_tge` is removed and everything anchors to `S_cap`;
and the whole system carries a conservation identity `ΔS + ΔP + ΔB = 0`. Storage-markets
gains a Fee Routing subsection decomposing the pool inflow as
`R_block = R̂_STR + R̂_pooled` — the first formal reconciliation of the two fee markets.

## 0. The verdict first — what actually moves here (measured before planning)

**No headline number in the de-novo reports moves.** Verified by execution before writing
this plan:

- `A_t` saturates at 1 over every horizon we simulate (min 0 only inside the estimator's
  genesis-seed window, where the blend pool was ~0 anyway), so the recycled term — the one
  term whose *mechanics* change (single-block → windowed) — never engages at a magnitude
  that matters. The steady block reward is the release-cap term, 95.13 LGO/block, and
  `S_tge → S_cap` is numerically identity (both 10¹⁰ LGO).
- The blend pool therefore stays at the measured 1,235,274 LGO/epoch; `retirement.py`'s
  constant, the service-dilution figures (6,185 / 155 / 50 LGO per provider), and every
  retirement conclusion stand.
- The fee-computation formulas of both markets are untouched by the RFC, so the anchor
  (11,158 lepta), the claim fee (6,664), the fee drag (59.7%), and every de-novo closed form
  stand.
- The reserve's depletion horizon is ≥ Y = 10 years at maximum release; our longest run is
  ~7.4 years. Depletion dynamics are new honesty for long horizons, not a correction to any
  published figure.

The revision is therefore structural and terminological — plus **one genuine cross-spec
collision** and **one genuine opportunity**, which are the substance of this plan.

## 1. The collision: `POW_SHARE` against "routed in full"

Our fee diversion (10% of fees into the PoW `fee_accrual`, MAPPING row 13) anchors to
`overview-cryptoeconomics` §PoW Reward Pool and intercepts fees *before* their old
disposition (burning). The RFC now states — twice, normatively — that fees are routed **in
full** into the pending rewards pool (`storage-markets.md` Fee Routing; `execution-market.md`
closing derivation), and its `R_block = R̂_STR + R̂_pooled` decomposition has no PoW term.
As specified, PR 375 and the EmPoWering fee diversion cannot both be true.

**DECIDED 2026-08-24 (design owner): the pool's routing stands and EmPoWering carves its
share out of the pooled reward flow** — resolution (ii). Fees enter the pending rewards pool
in full, the RFC's sentences stay true, and the `POW_SHARE` is the pool's first outflow. The
reward rule's window reads the pool's distributable inflow (fees net of the carve-out — the
same value the pre-pooling code computed, so no figure moves), and `fee_bucket` becomes the
EmPoWering-side view of a draw against the pending rewards pool. Recorded with the accounting
consequences as contradiction 4.13; the one remaining upstream ask is a sentence in the RFC
acknowledging the carve-out as a pool outflow. The options as drafted, for the record:

- **(i) Pre-pool carve-out.** EmPoWering intercepts its 10% at inclusion time; the RFC's
  "in full" gains a qualifier and the decomposition gains a term
  (`R_block = R̂_STR + R̂_pooled − R̂_POW`, or the diversion is listed as a routing
  exception). Smallest change to us; an upstream wording ask; keeps EmPoWering independent
  of pool state.
- **(ii) Distribution from the pool** *(recommended)*. The PoW fee component becomes a
  fourth outflow of the pending rewards pool: `diverted = POW_SHARE × R_block`, drawn from
  `P_t` at the epoch boundary. Same magnitude, cleaner provenance (the decomposition gives
  us `R_block` exactly), no routing exception needed, and EmPoWering becomes *native* to the
  RFC's structure rather than grandfathered beside it. Cost: a dependency on `P_t ≥ 0` —
  which is trivially satisfied in every regime we run, because `A_t = 1` means the pool
  retains all fees while EmPoWering draws 10% of them; the check becomes a gate, not an
  assumption.

Under either resolution the de-novo engine's arithmetic is unchanged — `diverted` has the
same value; what changes is which stock it is accounted against and what the docs cite.

## 2. The opportunity: EmPoWering is already an instance of the RFC's pattern

The structural rhyme is exact, and the RFC's author has already introduced the vocabulary we
need — the review thread says the reserve is modelled with **sub-pools "for accountability
purposes"**. Then:

| RFC concept | de-novo concept, already built and gated |
| --- | --- |
| genesis-minted reserve `B_0`, pre-allocated from the cap | the EmPoWering endowment: a genesis-minted sub-reserve |
| metered release `ι_t = min(schedule, B_{t−1})` | `sub_pool = endowment // (B − e)`, the linear amortisation |
| "lasts Y years at max rate, longer when `A_t < 1`" | Q7's nominal-rate tail, verbatim in spirit |
| depleted-reserve fallback to recycled fees | the dust fold and the fee-bucket post-phase |
| pending rewards pool `P_t` | `fee_bucket` (the PoW-share view of it, under 1.ii) |
| `ΔS + ΔP + ΔB = 0` | our conservation-to-the-lepton gate |

The revision rewrites MAPPING.md's framing around this table: EmPoWering stops being a
mechanism bolted beside the reward system and becomes *a second metered release from a
dedicated sub-reserve, with its own schedule and its own demand index*. That is a materially
stronger adoption argument than "orthogonal to the pool redesign" (the current MAPPING row,
which the RFC has made false anyway).

## 3. Code changes

1. **`emission.py` (strategy sim):** implement the RFC's real-valued rule — recycled term
   from the 120-block windowed `R̄_t` — while keeping the single-block form callable for
   master-parity gating. NOTE: the PR itself flags its integer section "Rederivation
   required" (the Rust body still uses the single-block fee), so the spec's real and integer
   rules currently disagree; we implement the real rule as the stated intent and record the
   gap in `CONTRADICTIONS.md` with the PR's own prescription as the resolution.
2. **Pool and reserve stocks:** add `P_t`, `B_t`, `ι_t`, `B_0 = 10⁹ LGO` to the emission
   model; depletion fallback; conservation gate `ΔS + ΔP + ΔB = 0` per step. The RFC's
   Implementation checklist is a ready-made gate menu (window-boundary correctness, pool
   non-negativity in the low-inflow regime, depleted-reserve fallback, integer-vs-real
   cross-check) — take it wholesale.
3. **Terminology in code:** `burnt_window` → `pooled_window`, docstrings burn/mint →
   pool/distribute/release. Mechanical; gates re-pinned only where a note quotes the word.
4. **De-novo `diverted` provenance:** re-derive against `R_block = R̂_STR + R̂_pooled`
   (same value, spec-exact decomposition), accounted per §1's resolution.
5. **`retirement.py`:** re-measure `BLEND_POOL_LGO_PER_EPOCH` after (1)–(2) and gate it
   (expected unchanged: 1,235,274).

## 4. Documentation changes

- **MAPPING.md:** replace the "orthogonal / untouched" rows for `block-rewards` and the fee
  markets with the §2 table and the §1 resolution; adopt "pending rewards pool" naming.
- **MODEL.md §1:** the inherited row for `pow_share` gains its new anchor; a paragraph notes
  the endowment is a sub-reserve in the RFC's sense.
- **CONTRADICTIONS.md:** two entries — the PR's flagged integer/real divergence (with its
  prescribed fix), and the "in full" vs `POW_SHARE` collision (with the §1 options and the
  owner's decision once taken).
- **denovo-report.md / SUMMARY.md:** one paragraph each: the substrate changed under the
  design and what that does (nothing, measured) and what it offers (the §2 reframing);
  post-phase "fees in, anchor out" language checked against pool routing (our de-novo docs
  are already burn/mint-free — verified by grep; only `empowering_sim` code and the
  acceleration survey carry the old vocabulary).
- **Terminology sweep** of `empowering_sim` docstrings and the survey.

## 5. Upstream contributions (outward-facing — each needs an explicit go)

1. **Answer the PR's open question with our machinery.** The PR asks for "explicit boundary
   treatment" of the early-life regime where `R̄_t` exceeds cumulative inflows (`P_t ≥ 0`).
   That is precisely the boundary class our dust fold and Q7 tail solved, and our engine can
   measure their proposed rule in an afternoon. A comment with a small simulation attached
   would close their one flagged review item.
2. **The §1 collision** needs raising on the PR (or in the EmPoWering RFC) whichever
   resolution is chosen — as written, the two specs contradict each other the day both merge.
3. **The leader-incentive concern** (thomaslavaur, block-rewards.md:262: pool retention when
   `A_t → 1` "making leaders not interested in tips during the adoption phase") is
   quantifiable in the strategy sim if wanted.

## 6. Order of work

§1 decision (blocks the doc framing, not the code) → §3.1–3.3 with gates green after each →
§3.4–3.5 → §4 → re-run both suites, selfcheck, blend-pool re-measure → §5 items on approval.
Nothing in the plan moves a published number; anything that does move one is a finding, not
a revision, and stops the line.
