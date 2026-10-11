module

public import Cryptarchia.Prob.Certs.E20D11M2.Fam
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

/-! # E20D11M2: tables for index 10 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ10 : xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10 = castX (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 10) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 10

/-- Phase expectation 10 over the integers. -/
def X10 : PhZ := ⟨31226787, 50000000, 1, 1,
  fun a b u => [31226787, 0, 50000000, 0, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  31226787⟩

theorem X10R : X10.Rep (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 10).1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 10).2.1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 10).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax10Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [29536730874285489067, 0, 0, 0, 0, 0, 29536730874285489067, 0, 0, 0, 0, 0, 29536730874285489067, 0, 0, 0, 0, 0, 29536730874285489067, 0, 0, 0, 0, 0, 29536730874267042323, 0, 0, 0, 0, 0, 29536730874267042323, 0, 0, 0, 0, 0, 29536730874267042323, 0, 0, 0, 0, 0, 29536730874267042323, 0, 0, 0, 0, 0, 29536730874267042323, 0, 0, 0, 0, 0, 29536730874267042323, 0, 0, 0, 0, 0, 29536730874267042323, 0, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop10 : Fin 32 → Fin 3 → ℤ := fun k =>
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
def preTop10 : Fin 32 → Fin 3 → ℤ := fun k =>
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
def eIn10 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (1008357331547 / 1000000000000 : ℚ)
  | 1 => (504247995533 / 500000000000 : ℚ)
  | 2 => (1008636877379 / 1000000000000 : ℚ)
  | 3 => (126097502963 / 125000000000 : ℚ)
  | 4 => (1008925463663 / 1000000000000 : ℚ)
  | 5 => (1009073231287 / 1000000000000 : ℚ)
  | 6 => (1009223361017 / 1000000000000 : ℚ)
  | 7 => (126171985963 / 125000000000 : ℚ)
  | 8 => (1009530846611 / 1000000000000 : ℚ)
  | 9 => (201937654683 / 200000000000 : ℚ)
  | 10 => (1009848204207 / 1000000000000 : ℚ)
  | 11 => (1010010675493 / 1000000000000 : ℚ)
  | 12 => (505087862097 / 500000000000 : ℚ)
  | 13 => (1010343387647 / 1000000000000 : ℚ)
  | 14 => (202102740721 / 200000000000 : ℚ)
  | 15 => (505343355119 / 500000000000 : ℚ)
  | 16 => (1010862446131 / 1000000000000 : ℚ)
  | 17 => (252760237571 / 250000000000 : ℚ)
  | 18 => (1011222262113 / 1000000000000 : ℚ)
  | 19 => (202281284289 / 200000000000 : ℚ)
  | 20 => (505796734261 / 500000000000 : ℚ)
  | 21 => (252945860999 / 250000000000 : ℚ)
  | 22 => (15812131077 / 15625000000 : ℚ)
  | 23 => (1012172344787 / 1000000000000 : ℚ)
  | 24 => (253092838361 / 250000000000 : ℚ)
  | 25 => (126571682147 / 125000000000 : ℚ)
  | 26 => (1012778698657 / 1000000000000 : ℚ)
  | 27 => (202597424191 / 200000000000 : ℚ)
  | 28 => (253299691883 / 250000000000 : ℚ)
  | 29 => (1013413682239 / 1000000000000 : ℚ)
  | 30 => (1013631909307 / 1000000000000 : ℚ)
  | _ => (1013853493349 / 1000000000000 : ℚ)

def post10Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X10 SZ (gFloorZ X10 SZ) (postTop10 k)
def pre10Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X10 SZ vmax10Z (preTop10 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE10Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X10 SZ (post10Z k) && leTabZ 11 (post10Z k) vmax10Z &&
    preSolZ (famZ k) DZ 11 X10 SZ vmax10Z (pre10Z k) &&
    decide ((autoBoundZ (famZ k) DZ X10 SZ (post10Z k) : ℚ) ≤ eIn10 k * (X10.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X10 SZ (pre10Z k) : ℚ) ≤ (1013853493349 / 1000000000000 : ℚ) * (X10.M DZ * SZ : ℤ))

theorem chkE10_0 : chkE10Q 0 = true := by decide +kernel
theorem chkE10_1 : chkE10Q 1 = true := by decide +kernel
theorem chkE10_2 : chkE10Q 2 = true := by decide +kernel
theorem chkE10_3 : chkE10Q 3 = true := by decide +kernel
theorem chkE10_4 : chkE10Q 4 = true := by decide +kernel
theorem chkE10_5 : chkE10Q 5 = true := by decide +kernel
theorem chkE10_6 : chkE10Q 6 = true := by decide +kernel
theorem chkE10_7 : chkE10Q 7 = true := by decide +kernel
theorem chkE10_8 : chkE10Q 8 = true := by decide +kernel
theorem chkE10_9 : chkE10Q 9 = true := by decide +kernel
theorem chkE10_10 : chkE10Q 10 = true := by decide +kernel
theorem chkE10_11 : chkE10Q 11 = true := by decide +kernel
theorem chkE10_12 : chkE10Q 12 = true := by decide +kernel
theorem chkE10_13 : chkE10Q 13 = true := by decide +kernel
theorem chkE10_14 : chkE10Q 14 = true := by decide +kernel
theorem chkE10_15 : chkE10Q 15 = true := by decide +kernel
theorem chkE10_16 : chkE10Q 16 = true := by decide +kernel
theorem chkE10_17 : chkE10Q 17 = true := by decide +kernel
theorem chkE10_18 : chkE10Q 18 = true := by decide +kernel
theorem chkE10_19 : chkE10Q 19 = true := by decide +kernel
theorem chkE10_20 : chkE10Q 20 = true := by decide +kernel
theorem chkE10_21 : chkE10Q 21 = true := by decide +kernel
theorem chkE10_22 : chkE10Q 22 = true := by decide +kernel
theorem chkE10_23 : chkE10Q 23 = true := by decide +kernel
theorem chkE10_24 : chkE10Q 24 = true := by decide +kernel
theorem chkE10_25 : chkE10Q 25 = true := by decide +kernel
theorem chkE10_26 : chkE10Q 26 = true := by decide +kernel
theorem chkE10_27 : chkE10Q 27 = true := by decide +kernel
theorem chkE10_28 : chkE10Q 28 = true := by decide +kernel
theorem chkE10_29 : chkE10Q 29 = true := by decide +kernel
theorem chkE10_30 : chkE10Q 30 = true := by decide +kernel
theorem chkE10_31 : chkE10Q 31 = true := by decide +kernel

theorem chkE10 : ∀ k, chkE10Q k = true := fun k => by
  fin_cases k; exacts [chkE10_0, chkE10_1, chkE10_2, chkE10_3, chkE10_4, chkE10_5, chkE10_6, chkE10_7, chkE10_8, chkE10_9, chkE10_10, chkE10_11, chkE10_12, chkE10_13, chkE10_14, chkE10_15, chkE10_16, chkE10_17, chkE10_18, chkE10_19, chkE10_20, chkE10_21, chkE10_22, chkE10_23, chkE10_24, chkE10_25, chkE10_26, chkE10_27, chkE10_28, chkE10_29, chkE10_30, chkE10_31]

noncomputable def vmax10 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax10Z)
noncomputable def vpreI10 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre10Z k))
noncomputable def vpostI10 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post10Z k))

theorem solE10 : AutoSolE fam 11 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10).2.2 vpreI10 vpostI10 vmax10 := by
  rw [xgQ10]; exact (oneSwitchZ_sound famR famA DZ_pos X10R SZ_pos chkE10).1

theorem heEall10 : ∀ k, autoBound (fam k) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10).2.2 (vpreI10 k) ≤ (1013853493349 / 1000000000000 : ℝ) := by
  rw [xgQ10]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X10R SZ_pos chkE10).2.2 k).trans_eq (by push_cast; ring)

theorem heIn10 : ∀ k, autoBound (fam k) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 10).2.2 (vpostI10 k) ≤ (eIn10 k : ℝ) := by
  rw [xgQ10]; exact (oneSwitchZ_sound famR famA DZ_pos X10R SZ_pos chkE10).2.1

end Cryptarchia.Prob.Certs.E20D11M2
