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

/-! # E20D11: tables for index 14 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ14 : xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14 = castX (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 14) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 14

/-- Phase expectation 14 over the integers. -/
def X14 : PhZ := ⟨25032843, 25000000, 1, 1,
  fun a b u => [25032843, 0, 25000000, 0, 25032843, 0, 25000000, 0, 25032843, 0, 25000000, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  25032843⟩

theorem X14R : X14.Rep (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 14).1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 14).2.1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 14).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax14Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [18422542011856229862, 0, 18422542011856229862, 0, 18422542011856229862, 0, 18422542011854385188, 0, 18422542011854385188, 0, 18422542011854385188, 0, 18422542011852540513, 0, 18422542011852540513, 0, 18422542011852540513, 0, 18422542011850695839, 0, 18422542011850695839, 0, 18422542011850695839, 0, 18422542011848851164, 0, 18422542011848851164, 0, 18422542011848851164, 0, 18422542011847006490, 0, 18422542011847006490, 0, 18422542011847006490, 0, 18422542011847006490, 0, 18422542011847006490, 0, 18422542011847006490, 0, 18422542011845161816, 0, 18422542011845161816, 0, 18422542011845161816, 0, 18422542011843317141, 0, 18422542011843317141, 0, 18422542011843317141, 0, 18422542011841472467, 0, 18422542011841472467, 0, 18422542011841472467, 0, 18422542011839627792, 0, 18422542011839627792, 0, 18422542011839627792, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop14 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![0, 0, 0]
  | 1 => ![0, 0, 0]
  | 2 => ![0, 0, 0]
  | 3 => ![0, 0, 0]
  | 4 => ![0, 0, 0]
  | 5 => ![0, 0, 0]
  | 6 => ![0, 0, 0]
  | 7 => ![0, 0, 0]
  | 8 => ![0, 0, 0]
  | 9 => ![0, 0, 0]
  | 10 => ![0, 0, 0]
  | 11 => ![0, 0, 0]
  | 12 => ![0, 0, 0]
  | 13 => ![0, 0, 0]
  | 14 => ![0, 0, 0]
  | 15 => ![0, 0, 0]
  | 16 => ![0, 0, 0]
  | 17 => ![0, 0, 0]
  | 18 => ![0, 0, 0]
  | 19 => ![0, 0, 0]
  | 20 => ![0, 0, 0]
  | 21 => ![0, 0, 0]
  | 22 => ![0, 0, 0]
  | 23 => ![0, 0, 0]
  | 24 => ![0, 0, 0]
  | 25 => ![0, 0, 0]
  | 26 => ![0, 0, 0]
  | 27 => ![0, 0, 0]
  | 28 => ![0, 0, 0]
  | 29 => ![0, 0, 0]
  | 30 => ![0, 0, 0]
  | _ => ![0, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop14 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![0, 0, 0]
  | 1 => ![0, 0, 0]
  | 2 => ![0, 0, 0]
  | 3 => ![0, 0, 0]
  | 4 => ![0, 0, 0]
  | 5 => ![0, 0, 0]
  | 6 => ![0, 0, 0]
  | 7 => ![0, 0, 0]
  | 8 => ![0, 0, 0]
  | 9 => ![0, 0, 0]
  | 10 => ![0, 0, 0]
  | 11 => ![0, 0, 0]
  | 12 => ![0, 0, 0]
  | 13 => ![0, 0, 0]
  | 14 => ![0, 0, 0]
  | 15 => ![0, 0, 0]
  | 16 => ![0, 0, 0]
  | 17 => ![0, 0, 0]
  | 18 => ![0, 0, 0]
  | 19 => ![0, 0, 0]
  | 20 => ![0, 0, 0]
  | 21 => ![0, 0, 0]
  | 22 => ![0, 0, 0]
  | 23 => ![0, 0, 0]
  | 24 => ![0, 0, 0]
  | 25 => ![0, 0, 0]
  | 26 => ![0, 0, 0]
  | 27 => ![0, 0, 0]
  | 28 => ![0, 0, 0]
  | 29 => ![0, 0, 0]
  | 30 => ![0, 0, 0]
  | _ => ![0, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn14 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (249994205897 / 250000000000 : ℚ)
  | 1 => (2499941021907 / 2500000000000 : ℚ)
  | 2 => (9999759866601 / 10000000000000 : ℚ)
  | 3 => (78123090403 / 78125000000 : ℚ)
  | 4 => (499987560067 / 500000000000 : ℚ)
  | 5 => (9999746754617 / 10000000000000 : ℚ)
  | 6 => (9999742230143 / 10000000000000 : ℚ)
  | 7 => (2499934406657 / 2500000000000 : ℚ)
  | 8 => (1999946588553 / 2000000000000 : ℚ)
  | 9 => (399989127089 / 400000000000 : ℚ)
  | 10 => (1249965416083 / 1250000000000 : ℚ)
  | 11 => (9999718395717 / 10000000000000 : ℚ)
  | 12 => (9999713377001 / 10000000000000 : ℚ)
  | 13 => (4999854135557 / 5000000000000 : ℚ)
  | 14 => (4999851538317 / 5000000000000 : ℚ)
  | 15 => (9999697792121 / 10000000000000 : ℚ)
  | 16 => (1999938483223 / 2000000000000 : ℚ)
  | 17 => (9999686947137 / 10000000000000 : ℚ)
  | 18 => (9999681383687 / 10000000000000 : ℚ)
  | 19 => (9999675724249 / 10000000000000 : ℚ)
  | 20 => (9999669967283 / 10000000000000 : ℚ)
  | 21 => (4999832055617 / 5000000000000 : ℚ)
  | 22 => (399986326181 / 400000000000 : ℚ)
  | 23 => (249991302389 / 250000000000 : ℚ)
  | 24 => (2499911483181 / 2500000000000 : ℚ)
  | 25 => (9999639664381 / 10000000000000 : ℚ)
  | 26 => (4999816644439 / 5000000000000 : ℚ)
  | 27 => (4999813402271 / 5000000000000 : ℚ)
  | 28 => (9999620209679 / 10000000000000 : ℚ)
  | 29 => (9999613502579 / 10000000000000 : ℚ)
  | 30 => (9999606681511 / 10000000000000 : ℚ)
  | _ => (4999799872363 / 5000000000000 : ℚ)

def post14Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X14 SZ (gFloorZ X14 SZ) (postTop14 k)
def pre14Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X14 SZ vmax14Z (preTop14 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE14Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X14 SZ (post14Z k) && leTabZ 11 (post14Z k) vmax14Z &&
    preSolZ (famZ k) DZ 11 X14 SZ vmax14Z (pre14Z k) &&
    decide ((autoBoundZ (famZ k) DZ X14 SZ (post14Z k) : ℚ) ≤ eIn14 k * (X14.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X14 SZ (pre14Z k) : ℚ) ≤ (9999768235881 / 10000000000000 : ℚ) * (X14.M DZ * SZ : ℤ))

theorem chkE14_0 : chkE14Q 0 = true := by decide +kernel
theorem chkE14_1 : chkE14Q 1 = true := by decide +kernel
theorem chkE14_2 : chkE14Q 2 = true := by decide +kernel
theorem chkE14_3 : chkE14Q 3 = true := by decide +kernel
theorem chkE14_4 : chkE14Q 4 = true := by decide +kernel
theorem chkE14_5 : chkE14Q 5 = true := by decide +kernel
theorem chkE14_6 : chkE14Q 6 = true := by decide +kernel
theorem chkE14_7 : chkE14Q 7 = true := by decide +kernel
theorem chkE14_8 : chkE14Q 8 = true := by decide +kernel
theorem chkE14_9 : chkE14Q 9 = true := by decide +kernel
theorem chkE14_10 : chkE14Q 10 = true := by decide +kernel
theorem chkE14_11 : chkE14Q 11 = true := by decide +kernel
theorem chkE14_12 : chkE14Q 12 = true := by decide +kernel
theorem chkE14_13 : chkE14Q 13 = true := by decide +kernel
theorem chkE14_14 : chkE14Q 14 = true := by decide +kernel
theorem chkE14_15 : chkE14Q 15 = true := by decide +kernel
theorem chkE14_16 : chkE14Q 16 = true := by decide +kernel
theorem chkE14_17 : chkE14Q 17 = true := by decide +kernel
theorem chkE14_18 : chkE14Q 18 = true := by decide +kernel
theorem chkE14_19 : chkE14Q 19 = true := by decide +kernel
theorem chkE14_20 : chkE14Q 20 = true := by decide +kernel
theorem chkE14_21 : chkE14Q 21 = true := by decide +kernel
theorem chkE14_22 : chkE14Q 22 = true := by decide +kernel
theorem chkE14_23 : chkE14Q 23 = true := by decide +kernel
theorem chkE14_24 : chkE14Q 24 = true := by decide +kernel
theorem chkE14_25 : chkE14Q 25 = true := by decide +kernel
theorem chkE14_26 : chkE14Q 26 = true := by decide +kernel
theorem chkE14_27 : chkE14Q 27 = true := by decide +kernel
theorem chkE14_28 : chkE14Q 28 = true := by decide +kernel
theorem chkE14_29 : chkE14Q 29 = true := by decide +kernel
theorem chkE14_30 : chkE14Q 30 = true := by decide +kernel
theorem chkE14_31 : chkE14Q 31 = true := by decide +kernel

theorem chkE14 : ∀ k, chkE14Q k = true := fun k => by
  fin_cases k; exacts [chkE14_0, chkE14_1, chkE14_2, chkE14_3, chkE14_4, chkE14_5, chkE14_6, chkE14_7, chkE14_8, chkE14_9, chkE14_10, chkE14_11, chkE14_12, chkE14_13, chkE14_14, chkE14_15, chkE14_16, chkE14_17, chkE14_18, chkE14_19, chkE14_20, chkE14_21, chkE14_22, chkE14_23, chkE14_24, chkE14_25, chkE14_26, chkE14_27, chkE14_28, chkE14_29, chkE14_30, chkE14_31]

noncomputable def vmax14 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax14Z)
noncomputable def vpreI14 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre14Z k))
noncomputable def vpostI14 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post14Z k))

theorem solE14 : AutoSolE fam 11 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14).2.2 vpreI14 vpostI14 vmax14 := by
  rw [xgQ14]; exact (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).1

theorem heEall14 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpreI14 k) ≤ (9999768235881 / 10000000000000 : ℝ) := by
  rw [xgQ14]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.2 k).trans_eq (by push_cast; ring)

theorem heIn14 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 k) ≤ (eIn14 k : ℝ) := by
  rw [xgQ14]; exact (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1

end Cryptarchia.Prob.Certs.E20D11
