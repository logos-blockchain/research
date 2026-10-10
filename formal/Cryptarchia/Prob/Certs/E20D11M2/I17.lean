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


theorem xgQ17 : xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17 = castX (xgNQ (1161 / 1000 : ℚ) (2001 / 1250 : ℚ) (5351 / 5000 : ℚ) (6209 / 10000 : ℚ) (51 / 50 : ℚ) 17) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 17

def vs17Q : ℕ → Fin 3 → Bool → ℚ := tabL
  [(166843595859 / 125000000000 : ℚ),
   (166843595859 / 125000000000 : ℚ),
   (166843595859 / 125000000000 : ℚ),
   (166843595859 / 125000000000 : ℚ),
   (166843595859 / 125000000000 : ℚ),
   (166843595859 / 125000000000 : ℚ),
   (261494990809 / 200000000000 : ℚ),
   (261494990809 / 200000000000 : ℚ),
   (261494990809 / 200000000000 : ℚ),
   (261494990809 / 200000000000 : ℚ),
   (261494990809 / 200000000000 : ℚ),
   (261494990809 / 200000000000 : ℚ),
   (1279609752571 / 1000000000000 : ℚ),
   (1279609752571 / 1000000000000 : ℚ),
   (1279609752571 / 1000000000000 : ℚ),
   (1279609752571 / 1000000000000 : ℚ),
   (1279609752571 / 1000000000000 : ℚ),
   (1279609752571 / 1000000000000 : ℚ),
   (625570169571 / 500000000000 : ℚ),
   (625570169571 / 500000000000 : ℚ),
   (625570169571 / 500000000000 : ℚ),
   (625570169571 / 500000000000 : ℚ),
   (625570169571 / 500000000000 : ℚ),
   (625570169571 / 500000000000 : ℚ),
   (305513403099 / 250000000000 : ℚ),
   (305513403099 / 250000000000 : ℚ),
   (305513403099 / 250000000000 : ℚ),
   (305513403099 / 250000000000 : ℚ),
   (305513403099 / 250000000000 : ℚ),
   (305513403099 / 250000000000 : ℚ),
   (1192336186889 / 1000000000000 : ℚ),
   (1192336186889 / 1000000000000 : ℚ),
   (1192336186889 / 1000000000000 : ℚ),
   (1192336186889 / 1000000000000 : ℚ),
   (1192336186889 / 1000000000000 : ℚ),
   (1192336186889 / 1000000000000 : ℚ),
   (232394877387 / 200000000000 : ℚ),
   (232394877387 / 200000000000 : ℚ),
   (232394877387 / 200000000000 : ℚ),
   (232394877387 / 200000000000 : ℚ),
   (232394877387 / 200000000000 : ℚ),
   (232394877387 / 200000000000 : ℚ),
   (565477120157 / 500000000000 : ℚ),
   (565477120157 / 500000000000 : ℚ),
   (565477120157 / 500000000000 : ℚ),
   (565477120157 / 500000000000 : ℚ),
   (565477120157 / 500000000000 : ℚ),
   (565477120157 / 500000000000 : ℚ),
   (6870384199 / 6250000000 : ℚ),
   (6870384199 / 6250000000 : ℚ),
   (6870384199 / 6250000000 : ℚ),
   (6870384199 / 6250000000 : ℚ),
   (6870384199 / 6250000000 : ℚ),
   (6870384199 / 6250000000 : ℚ),
   (1066881496793 / 1000000000000 : ℚ),
   (1066881496793 / 1000000000000 : ℚ),
   (1066881496793 / 1000000000000 : ℚ),
   (1066881496793 / 1000000000000 : ℚ),
   (1066881496793 / 1000000000000 : ℚ),
   (1066881496793 / 1000000000000 : ℚ),
   (1033799414207 / 1000000000000 : ℚ),
   (1033799414207 / 1000000000000 : ℚ),
   (1033799414207 / 1000000000000 : ℚ),
   (1033799414207 / 1000000000000 : ℚ),
   (1033799414207 / 1000000000000 : ℚ),
   (1033799414207 / 1000000000000 : ℚ)]

noncomputable def vs17 : ℕ → Fin 3 → Bool → ℝ := castT vs17Q

theorem solS17_0 : AutoSol f0 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f0A (v := vs17Q) (by decide +kernel)

theorem heS17_0 : autoBound f0 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (1028919089889 / 1000000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f0A (v := vs17Q) (e := (1028919089889 / 1000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_1 : AutoSol f1 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f1A (v := vs17Q) (by decide +kernel)

theorem heS17_1 : autoBound f1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (514867481747 / 500000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f1A (v := vs17Q) (e := (514867481747 / 500000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_2 : AutoSol f2 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f2A (v := vs17Q) (by decide +kernel)

theorem heS17_2 : autoBound f2 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (103062428677 / 100000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f2A (v := vs17Q) (e := (103062428677 / 100000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_3 : AutoSol f3 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f3A (v := vs17Q) (by decide +kernel)

theorem heS17_3 : autoBound f3 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (257898361559 / 250000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f3A (v := vs17Q) (e := (257898361559 / 250000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_4 : AutoSol f4 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f4A (v := vs17Q) (by decide +kernel)

theorem heS17_4 : autoBound f4 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (516324670357 / 500000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f4A (v := vs17Q) (e := (516324670357 / 500000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS17_5 : AutoSol f5 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 := by
  rw [xgQ17]
  exact autoSol_ofQ f5A (v := vs17Q) (by decide +kernel)

theorem heS17_5 : autoBound f5 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 17).2.2 vs17 ≤ (258449853549 / 250000000000 : ℝ) := by
  rw [xgQ17]
  exact autoBound_le_ofQ f5A (v := vs17Q) (e := (258449853549 / 250000000000 : ℚ)) (by norm_num) (by decide +kernel)

end Cryptarchia.Prob.Certs.E20D11M2
