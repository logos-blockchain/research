module

public import Cryptarchia.Prob.Certs.E20D11C.Fam
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

/-! # E20D11C: tables for index 1 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ1 : xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1 = castX (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 1) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 1

/-- Phase expectation 1 over the integers. -/
def X1 : PhZ := ⟨11833, 10000, 1, 1,
  fun a b u => [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  1⟩

theorem X1R : X1.Rep (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 1).1 (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 1).2.1 (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 1).2.2 := by decide +kernel

/-- The switching table, from its entries at `(0, a, true)`. -/
def vs1Z : ℕ → Fin 3 → Bool → ℤ :=
  fillAllZ ((List.finRange 32).map famZ) DZ 11 X1 SZ (fun _ _ _ => 0) ![18949973187675650583, 18949973187675650583, 18949973187675650583]

theorem chkS1 : ∀ k, (autoSolZ (famZ k) DZ 11 X1 SZ vs1Z &&
    decide ((autoBoundZ (famZ k) DZ X1 SZ vs1Z : ℚ) ≤ (501499444169 / 500000000000 : ℚ) * (X1.M DZ * SZ : ℤ))) = true := by
  decide +kernel

noncomputable def vs1 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vs1Z)

theorem solS1 : ∀ k, AutoSol (fam k) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.2 vs1 := by
  rw [xgQ1]; exact (switchZ_sound (eS := fun _ => (501499444169 / 500000000000 : ℚ)) famR famA DZ_pos X1R SZ_pos chkS1).1

theorem heS1 : ∀ k, autoBound (fam k) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.2 vs1 ≤ (501499444169 / 500000000000 : ℝ) := by
  rw [xgQ1]
  exact fun k => ((switchZ_sound (eS := fun _ => (501499444169 / 500000000000 : ℚ)) famR famA DZ_pos X1R SZ_pos chkS1).2 k).trans_eq
    (by push_cast; ring)

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax1Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [18949973187675650583, 18949973187675650583, 18949973187675650583, 18949973187675650583, 18949973187675650583, 18949973187675650583, 18912727085053088366, 18912727085053088366, 18912727085053088366, 18912727085053088366, 18912727085053088366, 18912727085053088366, 18873978062328213048, 18873978062328213048, 18873978062328213048, 18873978062328213048, 18873978062328213048, 18873978062328213048, 18833665475055119059, 18833665475055119059, 18833665475055119059, 18833665475055119059, 18833665475055119059, 18833665475055119059, 18791726231771959218, 18791726231771959218, 18791726231771959218, 18791726231771959218, 18791726231771959218, 18791726231771959218, 18748094695126396497, 18748094695126396497, 18748094695126396497, 18748094695126396497, 18748094695126396497, 18748094695126396497, 18702702579293260234, 18702702579293260234, 18702702579293260234, 18702702579293260234, 18702702579293260234, 18702702579293260234, 18655478843020323984, 18655478843020323984, 18655478843020323984, 18655478843020323984, 18655478843020323984, 18655478843020323984, 18606349578449778995, 18606349578449778995, 18606349578449778995, 18606349578449778995, 18606349578449778995, 18606349578449778995, 18555237895475595605, 18555237895475595605, 18555237895475595605, 18555237895475595605, 18555237895475595605, 18555237895475595605, 18502063801396964907, 18502063801396964907, 18502063801396964907, 18502063801396964907, 18502063801396964907, 18502063801396964907]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop1 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![18712543038047868238, 18712543038047868238, 18712543038047868238]
  | 1 => ![18717825999957886528, 18717825999957886528, 18717825999957886528]
  | 2 => ![18723227703780868216, 18723227703780868216, 18723227703780868216]
  | 3 => ![18728751319497548647, 18728751319497548647, 18728751319497548647]
  | 4 => ![18734400141364377993, 18734400141364377993, 18734400141364377993]
  | 5 => ![18740177561848271874, 18740177561848271874, 18740177561848271874]
  | 6 => ![18746087079189776428, 18746087079189776428, 18746087079189776428]
  | 7 => ![18752132315480877504, 18752132315480877504, 18752132315480877504]
  | 8 => ![18758317021368920401, 18758317021368920401, 18758317021368920401]
  | 9 => ![18764645064103119708, 18764645064103119708, 18764645064103119708]
  | 10 => ![18771120446276451282, 18771120446276451282, 18771120446276451282]
  | 11 => ![18777747307873240842, 18777747307873240842, 18777747307873240842]
  | 12 => ![18784529935344962052, 18784529935344962052, 18784529935344962052]
  | 13 => ![18791472750652870541, 18791472750652870541, 18791472750652870541]
  | 14 => ![18798580351371225520, 18798580351371225520, 18798580351371225520]
  | 15 => ![18805857486909436670, 18805857486909436670, 18805857486909436670]
  | 16 => ![18813309068639326642, 18813309068639326642, 18813309068639326642]
  | 17 => ![18820940190850632317, 18820940190850632317, 18820940190850632317]
  | 18 => ![18828756138258829654, 18828756138258829654, 18828756138258829654]
  | 19 => ![18836762380526450691, 18836762380526450691, 18836762380526450691]
  | 20 => ![18844964577280597940, 18844964577280597940, 18844964577280597940]
  | 21 => ![18853368617478296235, 18853368617478296235, 18853368617478296235]
  | 22 => ![18861980594761642654, 18861980594761642654, 18861980594761642654]
  | 23 => ![18870806834297819143, 18870806834297819143, 18870806834297819143]
  | 24 => ![18879853899622834567, 18879853899622834567, 18879853899622834567]
  | 25 => ![18889128606974644861, 18889128606974644861, 18889128606974644861]
  | 26 => ![18898638023116437221, 18898638023116437221, 18898638023116437221]
  | 27 => ![18908389494353358537, 18908389494353358537, 18908389494353358537]
  | 28 => ![18918390659353002524, 18918390659353002524, 18918390659353002524]
  | 29 => ![18928649445437614162, 18928649445437614162, 18928649445437614162]
  | 30 => ![18939174096457119992, 18939174096457119992, 18939174096457119992]
  | _ => ![18949973187675650583, 18949973187675650583, 18949973187675650583]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop1 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 1 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 2 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 3 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 4 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 5 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 6 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 7 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 8 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 9 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 10 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 11 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 12 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 13 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 14 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 15 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 16 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 17 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 18 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 19 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 20 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 21 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 22 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 23 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 24 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 25 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 26 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 27 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 28 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 29 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | 30 => ![18949973187730990815, 18949973187730990815, 18949973187730990815]
  | _ => ![18949973187730990815, 18949973187730990815, 18949973187730990815]

/-- Each member's in-epoch phase bound. -/
def eIn1 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (500734168003 / 500000000000 : ℚ)
  | 1 => (200300075327 / 200000000000 : ℚ)
  | 2 => (250383310021 / 250000000000 : ℚ)
  | 3 => (1001566951973 / 1000000000000 : ℚ)
  | 4 => (250400384729 / 250000000000 : ℚ)
  | 5 => (250409257129 / 250000000000 : ℚ)
  | 6 => (200334689883 / 200000000000 : ℚ)
  | 7 => (1001710831363 / 1000000000000 : ℚ)
  | 8 => (62609325329 / 62500000000 : ℚ)
  | 9 => (250447150801 / 250000000000 : ℚ)
  | 10 => (40073162341 / 40000000000 : ℚ)
  | 11 => (1001870605879 / 1000000000000 : ℚ)
  | 12 => (250478320323 / 250000000000 : ℚ)
  | 13 => (500978561099 / 500000000000 : ℚ)
  | 14 => (200400433513 / 200000000000 : ℚ)
  | 15 => (1002048457913 / 1000000000000 : ℚ)
  | 16 => (1002096035393 / 1000000000000 : ℚ)
  | 17 => (1002144943889 / 1000000000000 : ℚ)
  | 18 => (501097614549 / 500000000000 : ℚ)
  | 19 => (501123469299 / 500000000000 : ℚ)
  | 20 => (1002300121927 / 1000000000000 : ℚ)
  | 21 => (1002354830741 / 1000000000000 : ℚ)
  | 22 => (3915668433 / 3906250000 : ℚ)
  | 23 => (62654315147 / 62500000000 : ℚ)
  | 24 => (1002528659757 / 1000000000000 : ℚ)
  | 25 => (200518006419 / 200000000000 : ℚ)
  | 26 => (250663305757 / 250000000000 : ℚ)
  | 27 => (1002718299013 / 1000000000000 : ℚ)
  | 28 => (501392664723 / 500000000000 : ℚ)
  | 29 => (50142719339 / 50000000000 : ℚ)
  | 30 => (250731386677 / 250000000000 : ℚ)
  | _ => (501499444169 / 500000000000 : ℚ)

def post1Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X1 SZ (gFloorZ X1 SZ) (postTop1 k)
def pre1Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X1 SZ vmax1Z (preTop1 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE1Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X1 SZ (post1Z k) && leTabZ 11 (post1Z k) vmax1Z &&
    preSolZ (famZ k) DZ 11 X1 SZ vmax1Z (pre1Z k) &&
    decide ((autoBoundZ (famZ k) DZ X1 SZ (post1Z k) : ℚ) ≤ eIn1 k * (X1.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X1 SZ (pre1Z k) : ℚ) ≤ (501499444169 / 500000000000 : ℚ) * (X1.M DZ * SZ : ℤ))

theorem chkE1_0 : chkE1Q 0 = true := by decide +kernel
theorem chkE1_1 : chkE1Q 1 = true := by decide +kernel
theorem chkE1_2 : chkE1Q 2 = true := by decide +kernel
theorem chkE1_3 : chkE1Q 3 = true := by decide +kernel
theorem chkE1_4 : chkE1Q 4 = true := by decide +kernel
theorem chkE1_5 : chkE1Q 5 = true := by decide +kernel
theorem chkE1_6 : chkE1Q 6 = true := by decide +kernel
theorem chkE1_7 : chkE1Q 7 = true := by decide +kernel
theorem chkE1_8 : chkE1Q 8 = true := by decide +kernel
theorem chkE1_9 : chkE1Q 9 = true := by decide +kernel
theorem chkE1_10 : chkE1Q 10 = true := by decide +kernel
theorem chkE1_11 : chkE1Q 11 = true := by decide +kernel
theorem chkE1_12 : chkE1Q 12 = true := by decide +kernel
theorem chkE1_13 : chkE1Q 13 = true := by decide +kernel
theorem chkE1_14 : chkE1Q 14 = true := by decide +kernel
theorem chkE1_15 : chkE1Q 15 = true := by decide +kernel
theorem chkE1_16 : chkE1Q 16 = true := by decide +kernel
theorem chkE1_17 : chkE1Q 17 = true := by decide +kernel
theorem chkE1_18 : chkE1Q 18 = true := by decide +kernel
theorem chkE1_19 : chkE1Q 19 = true := by decide +kernel
theorem chkE1_20 : chkE1Q 20 = true := by decide +kernel
theorem chkE1_21 : chkE1Q 21 = true := by decide +kernel
theorem chkE1_22 : chkE1Q 22 = true := by decide +kernel
theorem chkE1_23 : chkE1Q 23 = true := by decide +kernel
theorem chkE1_24 : chkE1Q 24 = true := by decide +kernel
theorem chkE1_25 : chkE1Q 25 = true := by decide +kernel
theorem chkE1_26 : chkE1Q 26 = true := by decide +kernel
theorem chkE1_27 : chkE1Q 27 = true := by decide +kernel
theorem chkE1_28 : chkE1Q 28 = true := by decide +kernel
theorem chkE1_29 : chkE1Q 29 = true := by decide +kernel
theorem chkE1_30 : chkE1Q 30 = true := by decide +kernel
theorem chkE1_31 : chkE1Q 31 = true := by decide +kernel

theorem chkE1 : ∀ k, chkE1Q k = true := fun k => by
  fin_cases k; exacts [chkE1_0, chkE1_1, chkE1_2, chkE1_3, chkE1_4, chkE1_5, chkE1_6, chkE1_7, chkE1_8, chkE1_9, chkE1_10, chkE1_11, chkE1_12, chkE1_13, chkE1_14, chkE1_15, chkE1_16, chkE1_17, chkE1_18, chkE1_19, chkE1_20, chkE1_21, chkE1_22, chkE1_23, chkE1_24, chkE1_25, chkE1_26, chkE1_27, chkE1_28, chkE1_29, chkE1_30, chkE1_31]

noncomputable def vmax1 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax1Z)
noncomputable def vpreI1 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre1Z k))
noncomputable def vpostI1 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post1Z k))

theorem solE1 : AutoSolE fam 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.2 vpreI1 vpostI1 vmax1 := by
  rw [xgQ1]; exact (oneSwitchZ_sound famR famA DZ_pos X1R SZ_pos chkE1).1

theorem heEall1 : ∀ k, autoBound (fam k) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.2 (vpreI1 k) ≤ (501499444169 / 500000000000 : ℝ) := by
  rw [xgQ1]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X1R SZ_pos chkE1).2.2 k).trans_eq (by push_cast; ring)

theorem heIn1 : ∀ k, autoBound (fam k) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 1).2.2 (vpostI1 k) ≤ (eIn1 k : ℝ) := by
  rw [xgQ1]; exact (oneSwitchZ_sound famR famA DZ_pos X1R SZ_pos chkE1).2.1

end Cryptarchia.Prob.Certs.E20D11C
