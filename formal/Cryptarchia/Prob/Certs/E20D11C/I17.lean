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

/-! # E20D11C: tables for index 17 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ17 : xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 17 = castX (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 17) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 17

/-- Phase expectation 17 over the integers. -/
def X17 : PhZ := ⟨1, 1, 51, 50,
  fun a b u => [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  1⟩

theorem X17R : X17.Rep (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 17).1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 17).2.1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 17).2.2 := by decide +kernel

/-- The switching table, from its entries at `(0, a, true)`. -/
def vs17Z : ℕ → Fin 3 → Bool → ℤ :=
  fillAllZ ((List.finRange 32).map famZ) DZ 11 X17 SZ (fun _ _ _ => 0) ![24707963122088427572, 24707963122088427572, 24707963122088427572]

theorem chkS17 : ∀ k, (autoSolZ (famZ k) DZ 11 X17 SZ vs17Z &&
    decide ((autoBoundZ (famZ k) DZ X17 SZ vs17Z : ℚ) ≤ (1034545073821 / 1000000000000 : ℚ) * (X17.M DZ * SZ : ℤ))) = true := by
  decide +kernel

noncomputable def vs17 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vs17Z)

theorem solS17 : ∀ k, AutoSol (fam k) 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]; exact (switchZ_sound (eS := fun _ => (1034545073821 / 1000000000000 : ℚ)) famR famA DZ_pos X17R SZ_pos chkS17).1

theorem heS17 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (1034545073821 / 1000000000000 : ℝ) := by
  rw [xgQ17]
  exact fun k => ((switchZ_sound (eS := fun _ => (1034545073821 / 1000000000000 : ℚ)) famR famA DZ_pos X17R SZ_pos chkS17).2 k).trans_eq
    (by push_cast; ring)

end Cryptarchia.Prob.Certs.E20D11C
