module

public import Cryptarchia.Prob.Certs.E20D11M2.Fam
meta import Cryptarchia.Prob.Certs.E20D11M2.Fam
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

/-! # E20D11M2: tables for index 2 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ2 : xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 2 = castX (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 2) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 2

/-- Phase expectation 2 over the integers. -/
def X2 : PhZ := PhZ.ofQ (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 2)

theorem X2R : X2.Rep (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 2).1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 2).2.1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 2).2.2 := by decide +kernel

/-- The switching table's seeds, by Newton's method at elaboration time. -/
def vsTop2 : Fin 3 → ℤ :=
  seedL (eval% solveSeedsZ ((List.finRange 32).map famZ) DZ 11 X2 SZ (gFloorZ X2 SZ) (2 ^ 32) (2 ^ 8) 3 200 [gFloorZ X2 SZ 0 0 true, gFloorZ X2 SZ 0 1 true, gFloorZ X2 SZ 0 2 true])

theorem chkS2 : (List.finRange 32).all (chkSwF famZ DZ 11 X2 SZ vsTop2 fun _ => (1602799891219 / 25000000000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vs2 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (fillAllZ ((List.finRange 32).map famZ) DZ 11 X2 SZ (gFloorZ X2 SZ) vsTop2))

theorem solS2 : ∀ k, AutoSol (fam k) 11 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchF_sound famR famA DZ_pos X2R SZ_pos chkS2).1

theorem heS2 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (1602799891219 / 25000000000000 : ℝ) := by
  rw [xgQ2]
  exact fun k => ((switchF_sound famR famA DZ_pos X2R SZ_pos chkS2).2 k).trans_eq (by push_cast; ring)

end Cryptarchia.Prob.Certs.E20D11M2
