module

public import Cryptarchia.Prob.Certs.E20D11.Fam
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

/-! # E20D11: tables for index 9 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ9 : xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9 = castX (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 9) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 9

/-- Phase expectation 9 over the integers. -/
def X9 : PhZ := ⟨31226787, 50000000, 1, 1,
  fun a b u => [55552454073, 55552454073, 88950000000, 250000000000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  55552454073⟩

theorem X9R : X9.Rep (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 9).1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 9).2.1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 9).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax9Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [45408582562435534232, 83014982784738285665, 0, 0, 0, 0, 44309808892051722724, 83014982784664498689, 0, 0, 0, 0, 43152602575757632877, 83014982784609158456, 0, 0, 0, 0, 41933856172740564196, 83014982784535371480, 0, 0, 0, 0, 40650296988912599751, 83014982784461584504, 0, 0, 0, 0, 39298478288734155517, 83014982784387797528, 0, 0, 0, 0, 37874770039670821845, 83014982784332457295, 0, 0, 0, 0, 36375349164564860042, 83014982784258670319, 0, 0, 0, 0, 34796189275431829536, 83014982784184883343, 0, 0, 0, 0, 33133049861528738369, 83014982784111096366, 0, 0, 0, 0, 31381464902252713477, 83014982784055756134, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop9 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![83014982784738285665, 0, 0]
  | 1 => ![83014982784738285665, 0, 0]
  | 2 => ![83014982784738285665, 0, 0]
  | 3 => ![83014982784738285665, 0, 0]
  | 4 => ![83014982784738285665, 0, 0]
  | 5 => ![83014982784738285665, 0, 0]
  | 6 => ![83014982784738285665, 0, 0]
  | 7 => ![83014982784738285665, 0, 0]
  | 8 => ![83014982784738285665, 0, 0]
  | 9 => ![83014982784738285665, 0, 0]
  | 10 => ![83014982784738285665, 0, 0]
  | 11 => ![83014982784738285665, 0, 0]
  | 12 => ![83014982784738285665, 0, 0]
  | 13 => ![83014982784738285665, 0, 0]
  | 14 => ![83014982784738285665, 0, 0]
  | 15 => ![83014982784738285665, 0, 0]
  | 16 => ![83014982784738285665, 0, 0]
  | 17 => ![83014982784738285665, 0, 0]
  | 18 => ![83014982784738285665, 0, 0]
  | 19 => ![83014982784738285665, 0, 0]
  | 20 => ![83014982784738285665, 0, 0]
  | 21 => ![83014982784738285665, 0, 0]
  | 22 => ![83014982784738285665, 0, 0]
  | 23 => ![83014982784738285665, 0, 0]
  | 24 => ![83014982784738285665, 0, 0]
  | 25 => ![83014982784738285665, 0, 0]
  | 26 => ![83014982784738285665, 0, 0]
  | 27 => ![83014982784738285665, 0, 0]
  | 28 => ![83014982784738285665, 0, 0]
  | 29 => ![83014982784738285665, 0, 0]
  | 30 => ![83014982784738285665, 0, 0]
  | _ => ![83014982784738285665, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop9 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![83014982784922753106, 0, 0]
  | 1 => ![83014982784922753106, 0, 0]
  | 2 => ![83014982784922753106, 0, 0]
  | 3 => ![83014982784922753106, 0, 0]
  | 4 => ![83014982784922753106, 0, 0]
  | 5 => ![83014982784922753106, 0, 0]
  | 6 => ![83014982784922753106, 0, 0]
  | 7 => ![83014982784922753106, 0, 0]
  | 8 => ![83014982784922753106, 0, 0]
  | 9 => ![83014982784922753106, 0, 0]
  | 10 => ![83014982784922753106, 0, 0]
  | 11 => ![83014982784922753106, 0, 0]
  | 12 => ![83014982784922753106, 0, 0]
  | 13 => ![83014982784922753106, 0, 0]
  | 14 => ![83014982784922753106, 0, 0]
  | 15 => ![83014982784922753106, 0, 0]
  | 16 => ![83014982784922753106, 0, 0]
  | 17 => ![83014982784922753106, 0, 0]
  | 18 => ![83014982784922753106, 0, 0]
  | 19 => ![83014982784922753106, 0, 0]
  | 20 => ![83014982784922753106, 0, 0]
  | 21 => ![83014982784922753106, 0, 0]
  | 22 => ![83014982784922753106, 0, 0]
  | 23 => ![83014982784922753106, 0, 0]
  | 24 => ![83014982784922753106, 0, 0]
  | 25 => ![83014982784922753106, 0, 0]
  | 26 => ![83014982784922753106, 0, 0]
  | 27 => ![83014982784922753106, 0, 0]
  | 28 => ![83014982784922753106, 0, 0]
  | 29 => ![83014982784922753106, 0, 0]
  | 30 => ![83014982784922753106, 0, 0]
  | _ => ![83014982784922753106, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn9 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (1022038477539 / 1000000000000 : ℚ)
  | 1 => (511302451293 / 500000000000 : ℚ)
  | 2 => (25579654869 / 25000000000 : ℚ)
  | 3 => (204756545041 / 200000000000 : ℚ)
  | 4 => (256098718199 / 250000000000 : ℚ)
  | 5 => (1025023024211 / 1000000000000 : ℚ)
  | 6 => (256416893501 / 250000000000 : ℚ)
  | 7 => (1026328924677 / 1000000000000 : ℚ)
  | 8 => (1027007486739 / 1000000000000 : ℚ)
  | 9 => (513851839383 / 500000000000 : ℚ)
  | 10 => (1028417927461 / 1000000000000 : ℚ)
  | 11 => (1029150667691 / 1000000000000 : ℚ)
  | 12 => (1029902342541 / 1000000000000 : ℚ)
  | 13 => (1030673403343 / 1000000000000 : ℚ)
  | 14 => (1031464309707 / 1000000000000 : ℚ)
  | 15 => (1032275529543 / 1000000000000 : ℚ)
  | 16 => (516553769539 / 500000000000 : ℚ)
  | 17 => (1033960822861 / 1000000000000 : ℚ)
  | 18 => (1034835873763 / 1000000000000 : ℚ)
  | 19 => (517866596483 / 500000000000 : ℚ)
  | 20 => (1036653289943 / 1000000000000 : ℚ)
  | 21 => (1037596682433 / 1000000000000 : ℚ)
  | 22 => (1038563896397 / 1000000000000 : ℚ)
  | 23 => (519777732987 / 500000000000 : ℚ)
  | 24 => (520285966709 / 500000000000 : ℚ)
  | 25 => (41664553961 / 40000000000 : ℚ)
  | 26 => (260670442763 / 250000000000 : ℚ)
  | 27 => (52188813281 / 50000000000 : ℚ)
  | 28 => (208979581321 / 200000000000 : ℚ)
  | 29 => (1046047275517 / 1000000000000 : ℚ)
  | 30 => (13090312017 / 12500000000 : ℚ)
  | _ => (1048431560487 / 1000000000000 : ℚ)

def post9Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X9 SZ (gFloorZ X9 SZ) (postTop9 k)
def pre9Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X9 SZ vmax9Z (preTop9 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE9Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X9 SZ (post9Z k) && leTabZ 11 (post9Z k) vmax9Z &&
    preSolZ (famZ k) DZ 11 X9 SZ vmax9Z (pre9Z k) &&
    decide ((autoBoundZ (famZ k) DZ X9 SZ (post9Z k) : ℚ) ≤ eIn9 k * (X9.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X9 SZ (pre9Z k) : ℚ) ≤ (1048431560487 / 1000000000000 : ℚ) * (X9.M DZ * SZ : ℤ))

theorem chkE9_0 : chkE9Q 0 = true := by decide +kernel
theorem chkE9_1 : chkE9Q 1 = true := by decide +kernel
theorem chkE9_2 : chkE9Q 2 = true := by decide +kernel
theorem chkE9_3 : chkE9Q 3 = true := by decide +kernel
theorem chkE9_4 : chkE9Q 4 = true := by decide +kernel
theorem chkE9_5 : chkE9Q 5 = true := by decide +kernel
theorem chkE9_6 : chkE9Q 6 = true := by decide +kernel
theorem chkE9_7 : chkE9Q 7 = true := by decide +kernel
theorem chkE9_8 : chkE9Q 8 = true := by decide +kernel
theorem chkE9_9 : chkE9Q 9 = true := by decide +kernel
theorem chkE9_10 : chkE9Q 10 = true := by decide +kernel
theorem chkE9_11 : chkE9Q 11 = true := by decide +kernel
theorem chkE9_12 : chkE9Q 12 = true := by decide +kernel
theorem chkE9_13 : chkE9Q 13 = true := by decide +kernel
theorem chkE9_14 : chkE9Q 14 = true := by decide +kernel
theorem chkE9_15 : chkE9Q 15 = true := by decide +kernel
theorem chkE9_16 : chkE9Q 16 = true := by decide +kernel
theorem chkE9_17 : chkE9Q 17 = true := by decide +kernel
theorem chkE9_18 : chkE9Q 18 = true := by decide +kernel
theorem chkE9_19 : chkE9Q 19 = true := by decide +kernel
theorem chkE9_20 : chkE9Q 20 = true := by decide +kernel
theorem chkE9_21 : chkE9Q 21 = true := by decide +kernel
theorem chkE9_22 : chkE9Q 22 = true := by decide +kernel
theorem chkE9_23 : chkE9Q 23 = true := by decide +kernel
theorem chkE9_24 : chkE9Q 24 = true := by decide +kernel
theorem chkE9_25 : chkE9Q 25 = true := by decide +kernel
theorem chkE9_26 : chkE9Q 26 = true := by decide +kernel
theorem chkE9_27 : chkE9Q 27 = true := by decide +kernel
theorem chkE9_28 : chkE9Q 28 = true := by decide +kernel
theorem chkE9_29 : chkE9Q 29 = true := by decide +kernel
theorem chkE9_30 : chkE9Q 30 = true := by decide +kernel
theorem chkE9_31 : chkE9Q 31 = true := by decide +kernel

theorem chkE9 : ∀ k, chkE9Q k = true := fun k => by
  fin_cases k; exacts [chkE9_0, chkE9_1, chkE9_2, chkE9_3, chkE9_4, chkE9_5, chkE9_6, chkE9_7, chkE9_8, chkE9_9, chkE9_10, chkE9_11, chkE9_12, chkE9_13, chkE9_14, chkE9_15, chkE9_16, chkE9_17, chkE9_18, chkE9_19, chkE9_20, chkE9_21, chkE9_22, chkE9_23, chkE9_24, chkE9_25, chkE9_26, chkE9_27, chkE9_28, chkE9_29, chkE9_30, chkE9_31]

noncomputable def vmax9 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax9Z)
noncomputable def vpreI9 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre9Z k))
noncomputable def vpostI9 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post9Z k))

theorem solE9 : AutoSolE fam 11 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9).2.2 vpreI9 vpostI9 vmax9 := by
  rw [xgQ9]; exact (oneSwitchZ_sound famR famA DZ_pos X9R SZ_pos chkE9).1

theorem heEall9 : ∀ k, autoBound (fam k) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9).2.2 (vpreI9 k) ≤ (1048431560487 / 1000000000000 : ℝ) := by
  rw [xgQ9]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X9R SZ_pos chkE9).2.2 k).trans_eq (by push_cast; ring)

theorem heIn9 : ∀ k, autoBound (fam k) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 9).2.2 (vpostI9 k) ≤ (eIn9 k : ℝ) := by
  rw [xgQ9]; exact (oneSwitchZ_sound famR famA DZ_pos X9R SZ_pos chkE9).2.1

end Cryptarchia.Prob.Certs.E20D11
