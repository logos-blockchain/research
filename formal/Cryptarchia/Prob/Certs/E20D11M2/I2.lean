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

/-! # E20D11M2: tables for index 2 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ2 : xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2 = castX (xgNQ (11531 / 10000 : ℚ) (3899 / 2500 : ℚ) (529 / 500 : ℚ) (3577 / 5000 : ℚ) (51 / 50 : ℚ) 2) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 2

def vs2Q : ℕ → Fin 3 → Bool → ℚ := tabL
  [(33954420917 / 31250000000 : ℚ),
   (33954420917 / 31250000000 : ℚ),
   (33954420917 / 31250000000 : ℚ),
   (33954420917 / 31250000000 : ℚ),
   (33954420917 / 31250000000 : ℚ),
   (33954420917 / 31250000000 : ℚ),
   (1080008852981 / 1000000000000 : ℚ),
   (1080008852981 / 1000000000000 : ℚ),
   (1080008852981 / 1000000000000 : ℚ),
   (1080008852981 / 1000000000000 : ℚ),
   (1080008852981 / 1000000000000 : ℚ),
   (1080008852981 / 1000000000000 : ℚ),
   (107323747381 / 100000000000 : ℚ),
   (107323747381 / 100000000000 : ℚ),
   (107323747381 / 100000000000 : ℚ),
   (107323747381 / 100000000000 : ℚ),
   (107323747381 / 100000000000 : ℚ),
   (107323747381 / 100000000000 : ℚ),
   (1066218605207 / 1000000000000 : ℚ),
   (1066218605207 / 1000000000000 : ℚ),
   (1066218605207 / 1000000000000 : ℚ),
   (1066218605207 / 1000000000000 : ℚ),
   (1066218605207 / 1000000000000 : ℚ),
   (1066218605207 / 1000000000000 : ℚ),
   (1058943201597 / 1000000000000 : ℚ),
   (1058943201597 / 1000000000000 : ℚ),
   (1058943201597 / 1000000000000 : ℚ),
   (1058943201597 / 1000000000000 : ℚ),
   (1058943201597 / 1000000000000 : ℚ),
   (1058943201597 / 1000000000000 : ℚ),
   (262850471699 / 250000000000 : ℚ),
   (262850471699 / 250000000000 : ℚ),
   (262850471699 / 250000000000 : ℚ),
   (262850471699 / 250000000000 : ℚ),
   (262850471699 / 250000000000 : ℚ),
   (262850471699 / 250000000000 : ℚ),
   (41743397677 / 40000000000 : ℚ),
   (41743397677 / 40000000000 : ℚ),
   (41743397677 / 40000000000 : ℚ),
   (41743397677 / 40000000000 : ℚ),
   (41743397677 / 40000000000 : ℚ),
   (41743397677 / 40000000000 : ℚ),
   (129435286611 / 125000000000 : ℚ),
   (129435286611 / 125000000000 : ℚ),
   (129435286611 / 125000000000 : ℚ),
   (129435286611 / 125000000000 : ℚ),
   (129435286611 / 125000000000 : ℚ),
   (129435286611 / 125000000000 : ℚ),
   (205416699477 / 200000000000 : ℚ),
   (205416699477 / 200000000000 : ℚ),
   (205416699477 / 200000000000 : ℚ),
   (205416699477 / 200000000000 : ℚ),
   (205416699477 / 200000000000 : ℚ),
   (205416699477 / 200000000000 : ℚ),
   (50918886573 / 50000000000 : ℚ),
   (50918886573 / 50000000000 : ℚ),
   (50918886573 / 50000000000 : ℚ),
   (50918886573 / 50000000000 : ℚ),
   (50918886573 / 50000000000 : ℚ),
   (50918886573 / 50000000000 : ℚ),
   (1009353775547 / 1000000000000 : ℚ),
   (1009353775547 / 1000000000000 : ℚ),
   (1009353775547 / 1000000000000 : ℚ),
   (1009353775547 / 1000000000000 : ℚ),
   (1009353775547 / 1000000000000 : ℚ),
   (1009353775547 / 1000000000000 : ℚ)]

noncomputable def vs2 : ℕ → Fin 3 → Bool → ℝ := castT vs2Q

theorem solS2_0 : AutoSol f0 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f0A (v := vs2Q) (by decide +kernel)

theorem heS2_0 : autoBound f0 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (765340420147 / 20000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f0A (v := vs2Q) (e := (765340420147 / 20000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_1 : AutoSol f1 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f1A (v := vs2Q) (by decide +kernel)

theorem heS2_1 : autoBound f1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (4190244252557 / 100000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f1A (v := vs2Q) (e := (4190244252557 / 100000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_2 : AutoSol f2 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f2A (v := vs2Q) (by decide +kernel)

theorem heS2_2 : autoBound f2 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (4587722942277 / 100000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f2A (v := vs2Q) (e := (4587722942277 / 100000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_3 : AutoSol f3 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f3A (v := vs2Q) (by decide +kernel)

theorem heS2_3 : autoBound f3 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (2511093447227 / 50000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f3A (v := vs2Q) (e := (2511093447227 / 50000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_4 : AutoSol f4 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f4A (v := vs2Q) (by decide +kernel)

theorem heS2_4 : autoBound f4 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (5496935158499 / 100000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f4A (v := vs2Q) (e := (5496935158499 / 100000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_5 : AutoSol f5 11 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f5A (v := vs2Q) (by decide +kernel)

theorem heS2_5 : autoBound f5 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11531 / 10000 : ℝ) (3899 / 2500 : ℝ) (529 / 500 : ℝ) (3577 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (751941626039 / 12500000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f5A (v := vs2Q) (e := (751941626039 / 12500000000000 : ℚ)) (by norm_num) (by decide +kernel)

end Cryptarchia.Prob.Certs.E20D11M2
