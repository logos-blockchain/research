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

/-! # E20D11M2: tables for index 17 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ17 : xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17 = castX (xgNQ (11531 / 10000 : ℚ) (3899 / 2500 : ℚ) (529 / 500 : ℚ) (3577 / 5000 : ℚ) (51 / 50 : ℚ) 17) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 17

def vs17Q : ℕ → Fin 3 → Bool → ℚ := tabL
  [(267187218499 / 200000000000 : ℚ),
   (267187218499 / 200000000000 : ℚ),
   (267187218499 / 200000000000 : ℚ),
   (267187218499 / 200000000000 : ℚ),
   (267187218499 / 200000000000 : ℚ),
   (267187218499 / 200000000000 : ℚ),
   (654313186187 / 500000000000 : ℚ),
   (654313186187 / 500000000000 : ℚ),
   (654313186187 / 500000000000 : ℚ),
   (654313186187 / 500000000000 : ℚ),
   (654313186187 / 500000000000 : ℚ),
   (654313186187 / 500000000000 : ℚ),
   (320178145387 / 250000000000 : ℚ),
   (320178145387 / 250000000000 : ℚ),
   (320178145387 / 250000000000 : ℚ),
   (320178145387 / 250000000000 : ℚ),
   (320178145387 / 250000000000 : ℚ),
   (320178145387 / 250000000000 : ℚ),
   (626090679211 / 500000000000 : ℚ),
   (626090679211 / 500000000000 : ℚ),
   (626090679211 / 500000000000 : ℚ),
   (626090679211 / 500000000000 : ℚ),
   (626090679211 / 500000000000 : ℚ),
   (626090679211 / 500000000000 : ℚ),
   (611509522927 / 500000000000 : ℚ),
   (611509522927 / 500000000000 : ℚ),
   (611509522927 / 500000000000 : ℚ),
   (611509522927 / 500000000000 : ℚ),
   (611509522927 / 500000000000 : ℚ),
   (611509522927 / 500000000000 : ℚ),
   (1193211684613 / 1000000000000 : ℚ),
   (1193211684613 / 1000000000000 : ℚ),
   (1193211684613 / 1000000000000 : ℚ),
   (1193211684613 / 1000000000000 : ℚ),
   (1193211684613 / 1000000000000 : ℚ),
   (1193211684613 / 1000000000000 : ℚ),
   (581372503351 / 500000000000 : ℚ),
   (581372503351 / 500000000000 : ℚ),
   (581372503351 / 500000000000 : ℚ),
   (581372503351 / 500000000000 : ℚ),
   (581372503351 / 500000000000 : ℚ),
   (581372503351 / 500000000000 : ℚ),
   (70725276783 / 62500000000 : ℚ),
   (70725276783 / 62500000000 : ℚ),
   (70725276783 / 62500000000 : ℚ),
   (70725276783 / 62500000000 : ℚ),
   (70725276783 / 62500000000 : ℚ),
   (70725276783 / 62500000000 : ℚ),
   (274943760979 / 250000000000 : ℚ),
   (274943760979 / 250000000000 : ℚ),
   (274943760979 / 250000000000 : ℚ),
   (274943760979 / 250000000000 : ℚ),
   (274943760979 / 250000000000 : ℚ),
   (274943760979 / 250000000000 : ℚ),
   (533620808491 / 500000000000 : ℚ),
   (533620808491 / 500000000000 : ℚ),
   (533620808491 / 500000000000 : ℚ),
   (533620808491 / 500000000000 : ℚ),
   (533620808491 / 500000000000 : ℚ),
   (533620808491 / 500000000000 : ℚ),
   (1033988574831 / 1000000000000 : ℚ),
   (1033988574831 / 1000000000000 : ℚ),
   (1033988574831 / 1000000000000 : ℚ),
   (1033988574831 / 1000000000000 : ℚ),
   (1033988574831 / 1000000000000 : ℚ),
   (1033988574831 / 1000000000000 : ℚ)]

noncomputable def vs17 : ℕ → Fin 3 → Bool → ℝ := castT vs17Q

theorem solS17_0 : AutoSol f0 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f0A (v := vs17Q) (by decide +kernel)

theorem heS17_0 : autoBound f0 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (205778441767 / 200000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f0A (v := vs17Q) (e := (205778441767 / 200000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_1 : AutoSol f1 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f1A (v := vs17Q) (by decide +kernel)

theorem heS17_1 : autoBound f1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (514869074969 / 500000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f1A (v := vs17Q) (e := (514869074969 / 500000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_2 : AutoSol f2 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f2A (v := vs17Q) (by decide +kernel)

theorem heS17_2 : autoBound f2 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (1030663292841 / 1000000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f2A (v := vs17Q) (e := (1030663292841 / 1000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_3 : AutoSol f3 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f3A (v := vs17Q) (by decide +kernel)

theorem heS17_3 : autoBound f3 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (41266991967 / 40000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f3A (v := vs17Q) (e := (41266991967 / 40000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_4 : AutoSol f4 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f4A (v := vs17Q) (by decide +kernel)

theorem heS17_4 : autoBound f4 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (516390213913 / 500000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f4A (v := vs17Q) (e := (516390213913 / 500000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_5 : AutoSol f5 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f5A (v := vs17Q) (by decide +kernel)

theorem heS17_5 : autoBound f5 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (1033988574717 / 1000000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f5A (v := vs17Q) (e := (1033988574717 / 1000000000000 : ℚ)) (by norm_num) (by decide +kernel)

end Cryptarchia.Prob.Certs.E20D11M2
