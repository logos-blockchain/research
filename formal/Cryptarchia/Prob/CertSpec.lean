module

public import Cryptarchia.Prob.CertGen
public import Cryptarchia.Prob.Finality
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.NNRat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.Height.NumberField
import Mathlib.NumberTheory.Height.Projectivization
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.SelbergSieve
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.Tactic.Echelon.Zsqrtd
import Mathlib.Tactic.NormNum.Irrational
import Mathlib.Tactic.NormNum.IsCoprime
import Mathlib.Tactic.NormNum.IsSquare
import Mathlib.Tactic.NormNum.LegendreSymbol
import Mathlib.Tactic.NormNum.ModEq
import Mathlib.Tactic.NormNum.NatFib
import Mathlib.Tactic.NormNum.NatLog
import Mathlib.Tactic.NormNum.NatSqrt
import Mathlib.Tactic.NormNum.Ordinal
import Mathlib.Tactic.NormNum.Parity
import Mathlib.Tactic.NormNum.Prime
import Mathlib.Tactic.NormNum.RealSqrt
import Mathlib.Topology.Sheaves.Init
import Mathlib.Algebra.Order.Ring.Star

/-!
# Certificates at the specification's parameters

`FamCfg.finality_spec` is the finality theorem (`Prob.finality`) for a certificate given as data
(`CertGen.lean`), at `Config.spec`: every numeric condition, the settlement and band bounds
included, is one check over `ℚ` (`finChkSpec`), so a certificate's final theorem is a single
application of it.
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory

/-! ## The estimate's band over `ℚ` -/

namespace TBandQ

variable (T : TBandQ)

def Ya : ℚ := T.β / (1 - T.β) * T.Yh

def chi : ℚ := 1 + (errLoQ T.η T.ζ T.Yh + errLoQ T.η T.ζ T.Ya) / T.ℓlo

theorem Yh_cast : (T.Yh : ℝ) = T.toTBand.Yh := by simp only [Yh, TBand.Yh, toTBand]; push_cast; ring

theorem Ya_cast : (T.Ya : ℝ) = T.toTBand.Ya := by
  simp only [Ya, TBand.Ya, ← Yh_cast]; simp only [toTBand]; push_cast; ring

theorem chi_cast : (T.chi : ℝ) = T.toTBand.chi := by
  simp only [chi, TBand.chi, ← Yh_cast, ← Ya_cast]; simp only [toTBand]; push_cast
  rw [errLoQ_cast, errLoQ_cast]

/-- `TBand.OK`, as a check. -/
def okQ : Bool :=
  decide (0 < T.ℓlo) && decide (0 ≤ T.ℓhi) && decide (0 ≤ T.μ) && decide (T.μ < 1) && decide (0 ≤ T.β) &&
    decide (T.β < 1) && decide (0 < T.δ) && decide (T.δ ≤ 1) && decide (0 ≤ T.η) && decide (0 ≤ T.ζ) &&
    decide (T.Yh ≤ 1 / 2) && decide (T.Ya ≤ 1 / 2) && decide (errHiQ T.η T.ζ T.Yh ≤ 1) &&
    decide (errLoQ T.η T.ζ T.Yh ≤ 1) && decide (errLoQ T.η T.ζ T.Ya ≤ 1) && decide (0 ≤ T.clo)

theorem ok_of {T : TBandQ} (h : T.okQ = true) : T.toTBand.OK := by
  simp only [okQ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩, h7⟩, h8⟩, h9⟩, h10⟩, h11⟩, h12⟩, h13⟩, h14⟩, h15⟩, h16⟩ := h
  have half : (1 / 2 : ℝ) = ((1 / 2 : ℚ) : ℝ) := by norm_num
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · simp only [toTBand]; exact_mod_cast h1
  · simp only [toTBand]; exact_mod_cast h2
  · simp only [toTBand]; exact_mod_cast h3
  · simp only [toTBand]; exact_mod_cast h4
  · simp only [toTBand]; exact_mod_cast h5
  · simp only [toTBand]; exact_mod_cast h6
  · simp only [toTBand]; exact_mod_cast h7
  · simp only [toTBand]; exact_mod_cast h8
  · simp only [toTBand]; exact_mod_cast h9
  · simp only [toTBand]; exact_mod_cast h10
  · rw [← Yh_cast, half]; exact_mod_cast h11
  · rw [← Ya_cast, half]; exact_mod_cast h12
  · rw [← Yh_cast]; simp only [toTBand]; rw [← errHiQ_cast]; exact_mod_cast h13
  · rw [← Yh_cast]; simp only [toTBand]; rw [← errLoQ_cast]; exact_mod_cast h14
  · rw [← Ya_cast]; simp only [toTBand]; rw [← errLoQ_cast]; exact_mod_cast h15
  · rw [← clo_cast]; exact_mod_cast h16

end TBandQ

/-! ## The specification's constants over `ℚ` -/

def lam0Q (c : Config) : ℚ := (c.t0Const : ℚ) / c.p

def KcQ (c : Config) : ℚ := (c.precision : ℚ) / (c.period * c.fP)

theorem lam0Q_cast (c : Config) : (lam0Q c : ℝ) = lam0 c := by unfold lam0Q lam0; push_cast; ring

theorem KcQ_cast (c : Config) : (KcQ c : ℝ) = Kc c := by unfold KcQ Kc; push_cast; ring

/-- The lottery constants of the specification. -/
theorem lot_spec : LotConsts Config.spec (1 / 10 ^ 70) where
  p_pos := by norm_num [Config.spec]
  t0_pos := by norm_num [Config.spec]
  t1_le := by norm_num [Config.spec]
  a1_le := by unfold lam0; norm_num [Config.spec]
  a1_near := by unfold lam0; rw [abs_le]; constructor <;> norm_num [Config.spec]

/-- The band's drift and genesis conditions (`hup`, `hdn`, `hg1`, `hg2` of `Prob.finality`). -/
def driftChkQ (c : Config) (T : TBandQ) (ρ Hmin : ℚ) : Bool :=
  decide ((1 - T.μ) + 2 * T.ℓhi / (lam0Q c * Hmin) ≤
      T.ℓhi * KcQ c * (1 - T.μ) * (1 - T.δ) * T.clo * ((c.period : ℚ) - 1) / ρ) &&
    decide (T.ℓlo * KcQ c * (1 + T.δ) * T.chi * c.period * ρ + KcQ c * ρ + 3 * T.ℓlo / (lam0Q c * Hmin) ≤ 1) &&
    decide (T.ℓlo ≤ lam0Q c) && decide ((1 - T.μ) * lam0Q c ≤ T.ℓhi) && decide (0 < ρ) && decide (0 < Hmin)

/-! ## The final checks -/

/-- **A certificate's chosen numbers** beyond the family and the potential's parameters. -/
structure SpecData where
  /-- the potential's weight of the cold potential's second term -/
  κ : ℚ
  /-- the horizon: executions up to slot `N` -/
  N : ℕ
  /-- the slots of a span and of a crowded window, and the growth block -/
  Lw : ℕ
  T : ℕ
  /-- the crowded-window and slow-growth tilts -/
  x : ℚ
  yy : ℚ
  /-- the share of the main terms each lesser term may take (`SpecData.derive`) -/
  ε : ℚ
  /-- the stake drift per epoch and the minimum honest stake -/
  ρ : ℚ
  Hmin : ℚ

/-- **A certificate's derived numbers** (`SpecData.derive`). -/
structure SpecDerived where
  /-- the phases of a span, where the span term reaches the failed-checks term -/
  J : ℕ
  /-- the phase cut, the longest empty run and the reach bound: each the least making its term at most
  `ε` times the main terms -/
  G : ℕ
  G' : ℕ
  r : ℕ
  /-- the slots the analysis covers, and the epochs they span -/
  M : ℕ
  Ne : ℕ
  /-- the potential's contraction per phase, and inside an epoch -/
  lp : ℚ
  lpi : ℚ
  /-- the bounds: settlement, leaving the band in one epoch, and a finality violation -/
  tgt : ℚ
  bx : ℚ
  fin : ℚ
deriving DecidableEq

namespace FamCfg

/-- The least `n` in `[lo, hi]` with `P n`, by binary search with fuel `f` (for `P` monotone); `hi` if
there is none. -/
def leastTrue (P : ℕ → Bool) : ℕ → ℕ → ℕ → ℕ
  | 0, lo, _ => lo
  | f + 1, lo, hi =>
    if lo < hi then
      if P ((lo + hi) / 2) then leastTrue P f lo ((lo + hi) / 2) else leastTrue P f ((lo + hi) / 2 + 1) hi
    else lo

/-- The growth window's depth blocks at the specification (`nbD`). -/
def nbSpec (Δ G T : ℕ) : ℕ :=
  (Config.spec.epochLength - Config.spec.nonceOffset - Δ - 3 - G + Δ) / (T + Δ)

/-- **The derived numbers**: the slots and epochs the analysis covers, the contractions from the tables'
bounds (`lpOf`, `lpiOf`), the settlement and band bounds rounded up to 2 and 4 digits, and their sum
over the epochs rounded up to 2 digits. -/
def _root_.Cryptarchia.Prob.SpecData.derive (p : SpecData) (F : FamCfg) (Bq : BandR) (dat : Fin 19 → IdxData)
    (T : TBandQ) : SpecDerived :=
  let lp := F.lpOf Bq p.κ dat
  let lpi := F.lpiOf p.κ dat
  let stat := 1 + (bOf dat - 1) / (1 - lrOf dat)
  -- the main terms: spans, failed checks (without the phase cut's factor) and crowded windows
  let span := fun J : ℕ => (p.N + 1 : ℚ) * powUpQ 14 (eOf dat 17) (J + 1) / powDnQ 14 F.τ (p.Lw + 1)
  let fail := fun J : ℕ => (p.N + 1 : ℚ) * powUpQ 14 lpi J * eOf dat 2 * stat
  let win := (p.N + 1 : ℚ) * powUpQ 14 (1 + (p.x - 1) * (1 - Bq.elo)) p.Lw / powDnQ 14 p.x (Config.spec.k + 1)
  let J := leastTrue (fun j => decide (fail j ≤ span j)) 64 1 (2 ^ 15)
  let m0 := span J + fail J + win
  -- the lesser terms, each at most `ε · m0`
  let G' := leastTrue (fun n => decide ((p.N + 1 : ℚ) * powUpQ 14 (1 - Bq.hlo) n ≤ p.ε * m0)) 64 1 (2 ^ 14)
  let mG := leastTrue (fun n => decide ((p.N + 1 : ℚ) * powUpQ 14 (1 - (1 - Bq.hhi) ^ F.Δ) n ≤ p.ε * m0)) 64 1 (2 ^ 10)
  let G := max (2 * F.Δ) (F.Δ * mG + F.Δ)
  let r := leastTrue (fun n => decide ((p.N + G + 1 : ℚ) * stat / powDnQ 14 F.c (n + 1) ≤ p.ε * m0)) 64 0 (2 ^ 12)
  let M := p.N + G + G' + F.Δ + 2
  let Ne := M / Config.spec.epochLength + 1
  let tgt := rupQ 2 (settleEps3EQ 14 F.Δ Bq (eOf dat 17) F.τ lp (eOf dat 2) (bOf dat) (lrOf dat) F.c lpi p.x p.yy
    Config.spec.k ((p.N + 2) / Config.spec.epochLength) (nbSpec F.Δ G p.T) G p.N G G' J p.Lw r p.T)
  let bx := rupQ 4 (bandEpsQ 14 4096 T Config.spec.period)
  ⟨J, G, G', r, M, Ne, lp, lpi, tgt, bx, rupQ 2 (tgt + Ne * bx)⟩

/-- **Every numeric condition of the finality theorem at the specification**: the settlement bound
below `tgt`, the band's below `bx`, `tgt + Ne · bx ≤ fin`, and the conditions of `Prob.finality`. -/
def finChkSpec (F : FamCfg) (Bq : BandR) (dat : Fin 19 → IdxData) (T : TBandQ) (p : SpecData) (q : SpecDerived) :
    Bool :=
  let ⟨_, N, Lw, Tg, x, yy, _, ρ, Hmin⟩ := p
  let ⟨J, G, G', r, M, Ne, lp, lpi, tgt, bx, fin⟩ := q
  settleChkQ 14 F.Δ Bq (eOf dat 17) F.τ lp (eOf dat 2) (bOf dat) (lrOf dat) F.c lpi x yy Config.spec.k G Lw r Tg &&
    decide (settleEps3EQ 14 F.Δ Bq (eOf dat 17) F.τ lp (eOf dat 2) (bOf dat) (lrOf dat) F.c lpi x yy Config.spec.k
      ((N + 2) / Config.spec.epochLength) (nbSpec F.Δ G Tg) G N G G' J Lw r Tg ≤ tgt) &&
    bandChkQ 14 4096 T Config.spec.period && decide (bandEpsQ 14 4096 T Config.spec.period ≤ bx) && decide (tgt + Ne * bx ≤ fin) &&
    decide (0 ≤ tgt) && decide (0 ≤ bx) &&
    decide (1 ≤ x) && decide (0 < yy) && decide (yy ≤ 1) && decide (1 ≤ Tg) && decide (N + G + G' + F.Δ + 2 ≤ M) &&
    decide (Bq.hhi ≤ 1) && decide (0 ≤ Bq.hlo) && decide (Bq.hlo ≤ 1) && decide (Bq.elo ≤ 1) &&
    decide (Lw + G < Config.spec.epochLength) && decide (Config.spec.nonceOffset + G + 2 ≤ Config.spec.epochLength) && decide (M / Config.spec.epochLength < Ne) &&
    decide (F.Δ + 1 ≤ G) && decide (G + 1 < Config.spec.epochLength) && T.okQ && driftChkQ Config.spec T ρ Hmin &&
    decide (F.S.η = T.η) && decide (F.S.ζ = T.ζ) && decide (F.S.β = T.β) && decide (T.η = 1 / 10 ^ 70) &&
    decide (F.S.ys.getD 0 0 ≤ T.ylo) && decide (T.Yh ≤ F.S.ys.getD F.S.K 0)

/-- The conditions `finChkSpec` checks, by name. -/
structure SpecFacts (F : FamCfg) (Bq : BandR) (lp lpi : ℚ) (dat : Fin 19 → IdxData) (T : TBandQ)
    (N M Ne G G' J Lw r Tg : ℕ) (x yy ρ Hmin tgt bx fin : ℚ) : Prop where
  eps : settleChkQ 14 F.Δ Bq (eOf dat 17) F.τ lp (eOf dat 2) (bOf dat) (lrOf dat) F.c lpi x yy Config.spec.k G Lw r Tg = true
  epsle : settleEps3EQ 14 F.Δ Bq (eOf dat 17) F.τ lp (eOf dat 2) (bOf dat) (lrOf dat) F.c lpi x yy Config.spec.k
      ((N + 2) / Config.spec.epochLength) (nbSpec F.Δ G Tg) G N G G' J Lw r Tg ≤ tgt
  band : bandChkQ 14 4096 T Config.spec.period = true
  bandle : bandEpsQ 14 4096 T Config.spec.period ≤ bx
  fin : tgt + Ne * bx ≤ fin
  tgt0 : 0 ≤ tgt
  bx0 : 0 ≤ bx
  hx : 1 ≤ x
  hyy0 : 0 < yy
  hyy1 : yy ≤ 1
  hT : 1 ≤ Tg
  hNM : N + G + G' + F.Δ + 2 ≤ M
  hhi1 : Bq.hhi ≤ 1
  hlo0 : 0 ≤ Bq.hlo
  hlo1 : Bq.hlo ≤ 1
  helo1 : Bq.elo ≤ 1
  hLw : Lw + G < Config.spec.epochLength
  hOG : Config.spec.nonceOffset + G + 2 ≤ Config.spec.epochLength
  hNe : M / Config.spec.epochLength < Ne
  hG1 : F.Δ + 1 ≤ G
  hGEL : G + 1 < Config.spec.epochLength
  ok : T.okQ = true
  drift : driftChkQ Config.spec T ρ Hmin = true
  hη : F.S.η = T.η
  hζ : F.S.ζ = T.ζ
  hβ : F.S.β = T.β
  hηlot : T.η = 1 / 10 ^ 70
  cov0 : F.S.ys.getD 0 0 ≤ T.ylo
  cov1 : T.Yh ≤ F.S.ys.getD F.S.K 0

theorem finChkSpec.facts {F : FamCfg} {Bq : BandR} {κ lp lpi : ℚ} {dat : Fin 19 → IdxData} {T : TBandQ}
    {N M Ne G G' J Lw r Tg : ℕ} {x yy ρ Hmin tgt bx fin : ℚ}
    {ε : ℚ} (h : finChkSpec F Bq dat T ⟨κ, N, Lw, Tg, x, yy, ε, ρ, Hmin⟩ ⟨J, G, G', r, M, Ne, lp, lpi, tgt, bx, fin⟩ = true) :
    SpecFacts F Bq lp lpi dat T N M Ne G G' J Lw r Tg x yy ρ Hmin tgt bx fin := by
  simp only [finChkSpec, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨eps, epsle⟩, band⟩, bandle⟩, fin⟩, tgt0⟩, bx0⟩, hx⟩, hyy0⟩, hyy1⟩, hT⟩, hNM⟩, hhi1⟩, hlo0⟩, hlo1⟩, helo1⟩, hLw⟩, hOG⟩, hNe⟩, hG1⟩, hGEL⟩, ok⟩, drift⟩, hη⟩, hζ⟩, hβ⟩, hηlot⟩, cov0⟩, cov1⟩ := h
  exact ⟨eps, epsle, band, bandle, fin, tgt0, bx0, hx, hyy0, hyy1, hT, hNM, hhi1, hlo0, hlo1, helo1, hLw, hOG, hNe, hG1, hGEL, ok, drift, hη, hζ, hβ, hηlot, cov0, cov1⟩

/-- **Finality at the specification, from a certificate's data.** The index checks (`idxChk`), the
family's (`FamSpec.chk`), the main file's (`mainChk`) and the numeric conditions (`finChkSpec`)
give the finality bound `fin` under the execution assumptions. -/
theorem finality_spec {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
    {E : Env} (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} (p : SpecData) (q : SpecDerived)
    (hM : F.mainChk Bq p.κ q.lp q.lpi dat = true) (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D)
    (hBq : Bq = F.S.weakest) (hidx : ∀ i : Fin 19, F.idxChk i (dat i) = true) {n : ℕ} (hK : F.S.K = n + 1)
    (T : TBandQ) (hfin : finChkSpec F Bq dat T p q = true)
    (hc : E.c = Config.spec) (hΔ : E.Δ = F.Δ) (es : Ω → List Event) (hMod : Model μ O E es)
    (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ p.N) (hG : GenesisOK E)
    (hSt : ∀ ω, Exec.StakeOK E (O ω) (es ω) T.β T.ζ) (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) T.μ q.Ne)
    (hDr : ∀ ω, Exec.StakeDrift E (O ω) (es ω) p.ρ q.Ne) (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) p.Hmin) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal q.fin := by
  obtain ⟨κ, N, Lw, Tg, x, yy, ε, ρ, Hmin⟩ := p
  obtain ⟨J, G, G', r, M, Ne, lp, lpi, tgt, bx, fin⟩ := q
  have f := finChkSpec.facts hfin
  obtain ⟨⟨Δ, c, z, s, d', τ⟩, ⟨η, ζ, β, d, dy, K, ys⟩, famZL, Dz⟩ := F
  simp only at hK
  subst hK
  have hEL : E.c.epochLength = Config.spec.epochLength := by rw [hc]
  have hP : E.c.period = Config.spec.period := by rw [hc]
  have hδ := f.drift
  simp only [driftChkQ, Bool.and_eq_true, decide_eq_true_eq] at hδ
  obtain ⟨⟨⟨⟨⟨hup, hdn⟩, hg1⟩, hg2⟩, hρ⟩, hHm⟩ := hδ
  have hβ1 : β < 1 := by
    have h := (TBandQ.ok_of f.ok).β1
    simp only [TBandQ.toTBand] at h
    have hb := f.hβ
    simp only at hb
    rw [hb]; exact_mod_cast h
  have hb := Prob.finality (M := M) (Ne := Ne) (Tb := T.toTBand) es hMod hN hΔ
    (cert3E hM hS hD hBq hidx E.c.epochLength G f.hG1 (by rw [hEL]; exact f.hGEL)) (FamSpec.prod hS)
    (G' := G') (J := J) (Lw := Lw) (r := r) (T := Tg) (x := x) (yy := yy)
    (by exact_mod_cast f.hx) (by exact_mod_cast f.hyy0) (by exact_mod_cast f.hyy1) f.hT f.hNM
    (by simp only [BandR.toBand_hhi]; exact_mod_cast f.hhi1) (by simp only [BandR.toBand_hlo]; exact_mod_cast f.hlo0)
    (by simp only [BandR.toBand_hlo]; exact_mod_cast f.hlo1) (by simp only [BandR.toBand_elo]; exact_mod_cast f.helo1)
    (by rw [hEL]; exact f.hLw)
    (by rw [hc]; exact f.hOG)
    (by rw [hc]; simp only [TBandQ.toTBand, f.hηlot]; convert lot_spec using 2; norm_num)
    (TBandQ.ok_of f.ok) (by rw [hc]; rfl) (by rw [hc]; decide) (by rw [hc]; decide)
    (by rw [hP]; decide) (by rw [hP, hEL]; decide) (by rw [hEL]; exact f.hNe)
    (mem := FamSpec.mem ⟨η, ζ, β, d, dy, n + 1, ys⟩) (fun k => rfl)
    (fun k => by have := FamSpec.ok hS k; simp only [TBandQ.toTBand, ← f.hη, ← f.hζ]; exact this)
    (cover_of_chain (by simpa using FamSpec.chained ⟨η, ζ, β, d, dy, n + 1, ys⟩ rfl)
      (by rw [← TBandQ.ylo_cast]; simp only [FamSpec.mem, FamSpec.mQ, MemberQ.toMember_ylo, memberOfQ_ylo,
        Fin.val_zero]; exact_mod_cast f.cov0)
      (by rw [← TBandQ.Yh_cast]; simp only [FamSpec.mem, FamSpec.mQ, MemberQ.toMember_yhi, memberOfQ_yhi,
        Fin.val_last]; exact_mod_cast f.cov1))
    (fun k => memberOfQ_adv hβ1 (by have hb := f.hβ; simp only at hb; simp only [TBandQ.toTBand, hb]))
    (ρ := ρ) (Hmin := Hmin) (by exact_mod_cast hρ) (by exact_mod_cast hHm)
    (by rw [hc, ← lam0Q_cast, ← KcQ_cast, ← TBandQ.clo_cast]; simp only [TBandQ.toTBand]; exact_mod_cast hup)
    (by rw [hc, ← lam0Q_cast, ← KcQ_cast, ← TBandQ.chi_cast]; simp only [TBandQ.toTBand]; exact_mod_cast hdn)
    (by rw [hc, ← lam0Q_cast]; simp only [TBandQ.toTBand]; exact_mod_cast hg1)
    (by rw [hc, ← lam0Q_cast]; simp only [TBandQ.toTBand]; exact_mod_cast hg2)
    hG hSt hQ hDr hH
  rw [hP] at hb
  have hk : E.c.k = Config.spec.k := by rw [hc]
  have hne : nEp E N = (N + 2) / Config.spec.epochLength := by unfold nEp; rw [hEL]
  have hnb : nbD E Δ G Tg = nbSpec Δ G Tg := by
    unfold nbD growLen nbSpec; rw [hc]
  have h1 := (settleEps3E_le_Q (d := 14) (lpi := lpi) (x := x) (yy := yy) (Ccap := G) (N := N) (G := G) (G' := G')
    (J := J) (Lw := Lw) (r := r) (T := Tg) (cert2 hM) Bq rfl rfl rfl rfl rfl rfl rfl rfl hk hne hnb f.eps).trans
    (Rat.cast_le.2 f.epsle)
  have h2 := (bandEps_le_Q f.band).trans (Rat.cast_le.2 f.bandle)
  refine hb.trans ((add_le_add (ENNReal.ofReal_le_ofReal h1) (mul_le_mul_right (ENNReal.ofReal_le_ofReal h2) _)).trans ?_)
  have ht : (0 : ℝ) ≤ tgt := by exact_mod_cast f.tgt0
  have hx : (0 : ℝ) ≤ bx := by exact_mod_cast f.bx0
  rw [← ENNReal.ofReal_natCast, ← ENNReal.ofReal_mul (by positivity), ← ENNReal.ofReal_add ht (by positivity)]
  exact ENNReal.ofReal_le_ofReal (by exact_mod_cast f.fin)

end FamCfg

end Cryptarchia.Prob
