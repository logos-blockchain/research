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

/-! # E20D11C: tables for index 14 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ14 : xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14 = castX (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 14) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 14

/-- Phase expectation 14 over the integers. -/
def X14 : PhZ := ⟨17849851, 20000000, 1, 1,
  fun a b u => [17849851, 0, 20000000, 0, 17849851, 0, 20000000, 0, 17849851, 0, 20000000, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  17849851⟩

theorem X14R : X14.Rep (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 14).1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 14).2.1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 14).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax14Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340348712369, 0, 20668793340330265625, 0, 20668793340330265625, 0, 20668793340330265625, 0, 20668793340330265625, 0, 20668793340330265625, 0, 20668793340330265625, 0, 20668793340330265625, 0, 20668793340330265625, 0, 20668793340330265625, 0]

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
  | 0 => (200451881081 / 200000000000 : ℚ)
  | 1 => (1002299902043 / 1000000000000 : ℚ)
  | 2 => (125292639063 / 125000000000 : ℚ)
  | 3 => (250595762233 / 250000000000 : ℚ)
  | 4 => (1002425723663 / 1000000000000 : ℚ)
  | 5 => (125308643653 / 125000000000 : ℚ)
  | 6 => (50125666917 / 50000000000 : ℚ)
  | 7 => (1002558303933 / 1000000000000 : ℚ)
  | 8 => (1002604059123 / 1000000000000 : ℚ)
  | 9 => (250662654309 / 250000000000 : ℚ)
  | 10 => (501348995901 / 500000000000 : ℚ)
  | 11 => (501373098279 / 500000000000 : ℚ)
  | 12 => (1002795245451 / 1000000000000 : ℚ)
  | 13 => (1566945551 / 1562500000 : ℚ)
  | 14 => (501447966251 / 500000000000 : ℚ)
  | 15 => (1002947599627 / 1000000000000 : ℚ)
  | 16 => (501500084413 / 500000000000 : ℚ)
  | 17 => (501526827567 / 500000000000 : ℚ)
  | 18 => (1003108073809 / 1000000000000 : ℚ)
  | 19 => (200632688067 / 200000000000 : ℚ)
  | 20 => (1003219770427 / 1000000000000 : ℚ)
  | 21 => (100327708003 / 100000000000 : ℚ)
  | 22 => (250833846331 / 250000000000 : ℚ)
  | 23 => (40135788109 / 40000000000 : ℚ)
  | 24 => (125431881111 / 125000000000 : ℚ)
  | 25 => (1003516440707 / 1000000000000 : ℚ)
  | 26 => (501789447661 / 500000000000 : ℚ)
  | 27 => (250910607529 / 250000000000 : ℚ)
  | 28 => (3136584571 / 3125000000 : ℚ)
  | 29 => (200754562203 / 200000000000 : ℚ)
  | 30 => (1003839693133 / 1000000000000 : ℚ)
  | _ => (1003907727463 / 1000000000000 : ℚ)

def post14Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X14 SZ (gFloorZ X14 SZ) (postTop14 k)
def pre14Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X14 SZ vmax14Z (preTop14 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE14Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X14 SZ (post14Z k) && leTabZ 11 (post14Z k) vmax14Z &&
    preSolZ (famZ k) DZ 11 X14 SZ vmax14Z (pre14Z k) &&
    decide ((autoBoundZ (famZ k) DZ X14 SZ (post14Z k) : ℚ) ≤ eIn14 k * (X14.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X14 SZ (pre14Z k) : ℚ) ≤ (1003907727463 / 1000000000000 : ℚ) * (X14.M DZ * SZ : ℤ))

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

theorem solE14 : AutoSolE fam 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14).2.2 vpreI14 vpostI14 vmax14 := by
  rw [xgQ14]; exact (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).1

theorem heEall14 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpreI14 k) ≤ (1003907727463 / 1000000000000 : ℝ) := by
  rw [xgQ14]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.2 k).trans_eq (by push_cast; ring)

theorem heIn14 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 k) ≤ (eIn14 k : ℝ) := by
  rw [xgQ14]; exact (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1

end Cryptarchia.Prob.Certs.E20D11C
