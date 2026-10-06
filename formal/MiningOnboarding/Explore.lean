/-!
# Exploration: a calculator and a continuing-entry simulator (`Float`)

Computable counterparts of the model, for exploring the design of mining-funded onboarding.
Nothing here is proven; the proven statements are in the other files, and the test file
`MiningOnboardingTest/Report.lean` checks this code against the report's numbers.

* **Calculator** (fixed population or a single cohort, §§7–12 and §`sec:beta`): the closed
  forms `A`, `b`, `s`, the required rate `mReq`, the equal-newcomer minimum `mMin`, the
  qualification time `qualTime`, and the share threshold `gammaMin`.
* **Simulator** (§§14–19, the report's "next experiment", not yet simulated there): newcomer
  cohorts arrive every epoch; mining is allocated by a `Policy`; payouts stop when the pool
  is exhausted; the locked part `1 - β` of each reward matures `L` epochs after receipt. Each
  cohort is followed for its full window `L` (§19: ending early is not evidence of failure).

Units: balances in LOGOS, time in epochs. `epochsOfMonths q = q · 365 / (12 · 7.5)`.
-/

namespace Onboarding.Explore

/-! ## Units and reference parameters (§12.1) -/

/-- An epoch lasts `7.5` days; `q` months is `q · 365 / (12 · 7.5)` epochs. -/
def epochsOfMonths (q : Float) : Float := q * 365 / (12 * 7.5)

def monthsOfEpochs (t : Float) : Float := t * 12 * 7.5 / 365

/-- Network-level parameters. -/
structure Net where
  /-- Active stake when the cohort arrives (`S₀`). -/
  S0 : Float
  /-- Reward pool remaining when the cohort arrives (`R₀`). -/
  R0 : Float
  /-- Leadership pot per epoch (`P_L`). -/
  PL : Float
  /-- Unlocked balance required for Blend (`K_B`). -/
  KB : Float
  /-- Immediately unlocked mining fraction (`β`); `0` is the all-locked baseline. -/
  β : Float := 0
  /-- Lock duration of each mining reward, in epochs (`L`); one year by default. -/
  L : Float := epochsOfMonths 12
  deriving Repr

/-- §12.1: `S₀ = 99.5·10⁶`, `R₀ = 50·10⁶`, `P_L = 28.92`, `K_B = 1`. -/
def reference : Net := { S0 := 99.5e6, R0 := 50e6, PL := 28.92, KB := 1 }

/-! ## Calculator -/

/-- `A(t; M)`, evaluated without the cancellation in `S₀ + P_L t - S₀ g(t)` for small
`y = (M + P_L) t / S₀`: there `A/S₀ = -∑_{k ≥ 2} C(r, k) y^k` with `r = P_L/(M + P_L)`. -/
def A (n : Net) (M t : Float) : Float :=
  let a := M + n.PL
  if a ≤ 0 || t ≤ 0 then 0 else
  let r := n.PL / a
  let y := a * t / n.S0
  if y < 1e-3 then
    -- `C(r, k) = C(r, k-1) (r - k + 1)/k`
    Id.run do
      let mut c := r
      let mut yk := y
      let mut acc := 0
      for k in [2:8] do
        c := c * (r - k.toFloat + 1) / k.toFloat
        yk := yk * y
        acc := acc - c * yk
      return n.S0 * acc
  else
    n.S0 + n.PL * t - n.S0 * (1 + y) ^ r

/-- `g(t) = (1 + (M + P_L)t/S₀)^{P_L/(M + P_L)}`. -/
def g (n : Net) (M t : Float) : Float :=
  let a := M + n.PL
  if a ≤ 0 then 1 else (1 + a * t / n.S0) ^ (n.PL / a)

/-- Unlocked balance of a tokenless newcomer with income `m` out of total payout `M`, before
mining unlocks: `b(t) = β m t + (m/M) A(t; M)`. -/
def unlocked (n : Net) (M m t : Float) : Float :=
  n.β * m * t + (if M > 0 then m / M * A n M t else 0)

/-- Total stake of the same newcomer: `s(t) = m t + (m/M) A(t; M)`. -/
def stake (n : Net) (M m t : Float) : Float :=
  m * t + (if M > 0 then m / M * A n M t else 0)

/-- Remaining pool `R(t) = R₀ - M t`. -/
def pool (n : Net) (M t : Float) : Float := n.R0 - M * t

/-- Required income at fixed total payout `M` (`β = 0`): `m_req = M K_B / A(T; M)`;
with `β`: `m_req = K_B / (β T + A(T; M)/M)`. -/
def mReq (n : Net) (M T : Float) : Float := n.KB / (n.β * T + A n M T / M)

/-- Bisection for the least `x ∈ [lo, hi]` with `p x`, assuming `p` is monotone. -/
partial def bisect (p : Float → Bool) (lo hi : Float) (iters : Nat := 200) : Float :=
  if iters = 0 || hi - lo ≤ 1e-12 * Float.abs hi then hi else
  let mid := (lo + hi) / 2
  if p mid then bisect p lo mid (iters - 1) else bisect p mid hi (iters - 1)

/-- Equal-income newcomers: `N` newcomers with payout share `γ` receive `m` each, so
`M = N m/γ` and `b(T) = β m T + (γ/N) A(T; N m/γ)`. -/
def equalUnlocked (n : Net) (N γ m T : Float) : Float := unlocked n (N * m / γ) m T

/-- Minimum equal income `m_min(T, γ)` with `b(T) = K_B`, or `none` if none exists below
`mMax`. For `β = 0` it exists iff `γ P_L T > N K_B` (leadership-income feasibility). -/
def mMin (n : Net) (N γ T : Float) (mMax : Float := 1e12) : Option Float :=
  if equalUnlocked n N γ mMax T < n.KB then none
  else some (bisect (fun m => equalUnlocked n N γ m T ≥ n.KB) 0 mMax)

/-- Qualification time of a newcomer at constant `M`, `m`: least `t ≤ tMax` with
`b(t) ≥ K_B` (`b` is increasing in `t`). -/
def qualTime (n : Net) (M m : Float) (tMax : Float := n.L) : Option Float :=
  if unlocked n M m tMax < n.KB then none
  else some (bisect (fun t => unlocked n M m t ≥ n.KB) 0 tMax)

/-- Leading small-growth estimate `m₀(T) = 2 K_B S₀ / (P_L T²)` (§10). A lower bound on the
required rate for `β = 0` (`SmallGrowth.lean`). -/
def m0 (n : Net) (T : Float) : Float := 2 * n.KB * n.S0 / (n.PL * T ^ 2)

/-- First-corrected estimate `m₀(T)[1 + 4 N K_B/(3γ P_L T) + P_L T/(3 S₀)]` (§10). -/
def m1 (n : Net) (N γ T : Float) : Float :=
  m0 n T * (1 + 4 * N * n.KB / (3 * γ * n.PL * T) + n.PL * T / (3 * n.S0))

/-- At fixed total payout `M` and `N` identical newcomers, the least newcomer payout share
`γ` with which they qualify by `T`. -/
def gammaMin (n : Net) (N M T : Float) : Option Float :=
  if unlocked n M (M / N) T < n.KB then none
  else some (bisect (fun γ => unlocked n M (γ * M / N) T ≥ n.KB) 0 1)

/-! ## Pool depletion (`PoolDepletion.lean`)

Random claims: expected spend `E` before the horizon, rewards per claim at most `σ̄`. -/

/-- Bennett bound `exp(-(k log(k/μ) - k + μ))`, `μ = E/σ̄`, `k = R₀/σ̄`, on the probability
that the pool is depleted (`depletion_le_bennett`); `1` if `R₀ ≤ E`. -/
def depletionBound (R0 E σbar : Float) : Float :=
  if R0 ≤ E then 1 else if E ≤ 0 then 0 else
  let μ := E / σbar
  let k := R0 / σbar
  Float.exp (-(k * Float.log (k / μ) - k + μ))

/-- The buffer `√(2 σ̄ E L) + σ̄ L`, `L = log(1/δ)`, above the expected spend that guarantees
depletion probability at most `δ` (`depletion_le_of_buffer`). -/
def depletionBuffer (E σbar δ : Float) : Float :=
  let L := Float.log (1 / δ)
  Float.sqrt (2 * σbar * E * L) + σbar * L

/-- Largest reward per claim `σ̄` with `depletionBound ≤ δ`. -/
def maxClaimReward (R0 E δ : Float) : Float :=
  if R0 ≤ E then 0 else
  -- the bound increases with `σ̄`; find the least failing `σ̄`
  bisect (fun σbar => depletionBound R0 E σbar > δ) 0 R0

/-- Longest horizon (epochs) at expected spend `M` per epoch with `depletionBound ≤ δ`. -/
def safeHorizon (R0 M σbar δ : Float) : Float :=
  bisect (fun T => depletionBound R0 (M * T) σbar > δ) 0 (R0 / M)

/-! ## Continuing-entry simulator -/

/-- How mining income is allocated as the population grows (§15). -/
inductive Policy where
  /-- Total payout `M` per epoch, split in proportion to hashrate: capitalised miners have
  aggregate hashrate `hC`, each newcomer `h`. Dilutes individual income as entry grows. -/
  | fixedTotal (M hC h : Float)
  /-- Every newcomer earns `m` per epoch; capitalised miners together earn `mC`. Protects
  individual income but raises total expenditure and competing stake. -/
  | fixedIndividual (m mC : Float)
  deriving Repr

/-- A continuing-entry scenario. `t = 0` is when arrivals start; `n.S0` is the active stake
then, of which `SC0` is held by capitalised (mining) participants and the rest by non-mining
incumbents. -/
structure Scenario where
  net : Net
  SC0 : Float
  policy : Policy
  /-- Cohort sizes: `arrivals e` newcomers join at the start of epoch `e`, for `e < epochs`. -/
  arrivals : Nat → Nat
  epochs : Nat
  /-- Integration substeps per epoch. -/
  substeps : Nat := 64

/-- Outcome for one cohort. -/
structure CohortResult where
  e : Nat
  size : Nat
  /-- Qualification age `τ_e` (epochs since arrival), if before `L`. -/
  tau : Option Float
  /-- Unlocked balance per member just before age `L`. -/
  bAtL : Float
  /-- Mining income per member over its first `L` epochs. -/
  minedByL : Float
  /-- Newcomers' share of the payout `γ_e` at arrival. -/
  gammaAtArrival : Float
  deriving Repr, Inhabited

/-- `Q_e`: identical deterministic members qualify together, so `Q_e ∈ {0, 1}` (§19). -/
def CohortResult.Q (c : CohortResult) : Float := if c.tau.isSome then 1 else 0

structure Outcome where
  cohorts : Array CohortResult
  /-- Epoch at which the pool ran out, if it did. -/
  exhaustedAt : Option Float
  finalPool : Float
  finalStake : Float

/-- Simulate a scenario (midpoint rule with `substeps` per epoch; each step conserves
`dS_tot = (M + P_L) dt` exactly). Arrivals stop after `epochs`; the run continues until the
last cohort has been followed for `L`.

Per cohort `e` (one representative member, §18): `ds_e = (m_e + P_L s_e/S_tot) dt`,
`db_e = (β m_e + P_L s_e/S_tot) dt + (1 - β) m_e(t - L) dt`. Capitalised miners and
non-mining incumbents are aggregates (exact, since leadership income is linear in stake). -/
def simulate (sc : Scenario) : Outcome := Id.run do
  let n := sc.net
  let K := sc.substeps
  let dt := 1 / K.toFloat
  let lagSteps := (n.L * K.toFloat).round.toUInt64.toNat
  let horizon := sc.epochs * K + lagSteps
  let nC := sc.epochs
  -- per-cohort state
  let mut s : Array Float := Array.replicate nC 0
  let mut b : Array Float := Array.replicate nC 0
  let mut mined : Array Float := Array.replicate nC 0
  let mut tau : Array (Option Float) := Array.replicate nC none
  let mut bAtL : Array Float := Array.replicate nC 0
  let mut minedL : Array Float := Array.replicate nC 0
  let mut gam : Array Float := Array.replicate nC 0
  -- locked mining received per member, per substep, for maturation after `L`
  let mut hist : Array (Array Float) := Array.replicate nC #[]
  let mut SE := n.S0 - sc.SC0
  let mut SC := sc.SC0
  let mut R := n.R0
  let mut exhausted : Option Float := none
  let mut arrived := 0  -- number of cohorts that have arrived
  let mut pop := 0.0    -- newcomers present
  for step in [0:horizon] do
    let t := step.toFloat * dt
    if step % K == 0 && step / K < nC then
      let e := step / K
      arrived := e + 1
      pop := pop + (sc.arrivals e).toFloat
    -- mining allocation
    let (mNew, mCap) := match sc.policy with
      | .fixedTotal M hC h =>
        let H := hC + h * pop
        if H > 0 then (M * h / H, M * hC / H) else (0, 0)
      | .fixedIndividual m mC => (m, mC)
    let Mtot := mNew * pop + mCap
    -- pool exhaustion: pay pro rata from what is left
    let scale := if Mtot * dt ≤ R then 1 else if Mtot > 0 then R / (Mtot * dt) else 0
    if scale < 1 && exhausted.isNone then exhausted := some t
    let mN := mNew * scale
    let mC := mCap * scale
    R := R - Mtot * scale * dt
    let Stot := SE + SC + (Id.run do
      let mut acc := 0
      for e in [0:arrived] do acc := acc + (sc.arrivals e).toFloat * s[e]!
      return acc)
    -- midpoint rule: `S_tot` grows linearly over the substep, each stake by its mining
    let rate := n.PL / (Stot + (Mtot * scale + n.PL) * dt / 2)
    SE := SE + rate * SE * dt
    SC := SC + (mC + rate * (SC + mC * dt / 2)) * dt
    for e in [0:arrived] do
      let age := step - e * K
      if age == 0 then
        gam := gam.set! e (if Mtot > 0 then mNew * pop / Mtot else 0)
      if age < lagSteps then
        -- qualification check at the start of the substep
        if tau[e]!.isNone && b[e]! ≥ n.KB then tau := tau.set! e (some (age.toFloat * dt))
      if age == lagSteps then
        bAtL := bAtL.set! e b[e]!
        minedL := minedL.set! e mined[e]!
      let matured := if age ≥ lagSteps then hist[e]![age - lagSteps]! else 0
      let lead := rate * (s[e]! + mN * dt / 2)
      s := s.set! e (s[e]! + (mN + lead) * dt)
      b := b.set! e (b[e]! + (n.β * mN + lead) * dt + matured)
      mined := mined.set! e (mined[e]! + mN * dt)
      hist := hist.set! e (hist[e]!.push ((1 - n.β) * mN * dt))
  let cohorts := (List.range nC).toArray.map fun e =>
    { e, size := sc.arrivals e, tau := tau[e]!, bAtL := bAtL[e]!, minedByL := minedL[e]!,
      gammaAtArrival := gam[e]! : CohortResult }
  let finalStake := SE + SC + (Id.run do
    let mut acc := 0
    for e in [0:nC] do acc := acc + (sc.arrivals e).toFloat * s[e]!
    return acc)
  return { cohorts, exhaustedAt := exhausted, finalPool := R, finalStake }

/-- Fraction of arriving newcomers (weighted by cohort size) who qualify before age `L`. -/
def Outcome.qualifiedFraction (o : Outcome) : Float :=
  let tot := o.cohorts.foldl (fun acc c => acc + c.size.toFloat) 0
  let q := o.cohorts.foldl (fun acc c => acc + c.size.toFloat * c.Q) 0
  if tot > 0 then q / tot else 0

/-- The first cohort (arrival epoch) that fails to qualify before age `L`, if any. -/
def Outcome.firstFailure (o : Outcome) : Option Nat :=
  (o.cohorts.find? fun c => c.size > 0 && c.tau.isNone).map (·.e)

/-! ## Formatting -/

/-- Round to `k` decimals for display. -/
def round (x : Float) (k : Nat := 3) : Float :=
  let p := (10 : Float) ^ k.toFloat
  (x * p).round / p

def fmtOpt (x : Option Float) (k : Nat := 2) : String :=
  match x with
  | some v => toString (round v k)
  | none => "—"

/-- One line per cohort: arrival epoch, size, `γ_e` at arrival, `τ_e` in months, `Q_e`,
unlocked balance at age `L`, mining by age `L`. -/
def Outcome.table (o : Outcome) (every : Nat := 1) : String := Id.run do
  let mut out := "epoch  size  γ_e     τ_e(months)  Q_e  b(L)        mined(L)\n"
  for c in o.cohorts do
    if c.e % every == 0 then
      out := out ++ s!"{c.e}  {c.size}  {round c.gammaAtArrival}  {fmtOpt (c.tau.map monthsOfEpochs)}  {c.Q}  {round c.bAtL}  {round c.minedByL 0}\n"
  out := out ++ s!"pool exhausted at epoch: {fmtOpt o.exhaustedAt}; final pool {round o.finalPool 0}\n"
  return out

end Onboarding.Explore
