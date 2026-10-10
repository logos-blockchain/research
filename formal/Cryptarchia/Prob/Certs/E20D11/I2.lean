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

/-! # E20D11: tables for index 2 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ2 : xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2 = castX (xgNQ (1161 / 1000 : ℚ) (2001 / 1250 : ℚ) (5351 / 5000 : ℚ) (6209 / 10000 : ℚ) (51 / 50 : ℚ) 2) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 2

def vs2Q : ℕ → Fin 3 → Bool → ℚ := tabL
  [(136495584887 / 125000000000 : ℚ),
   (136495584887 / 125000000000 : ℚ),
   (136495584887 / 125000000000 : ℚ),
   (136495584887 / 125000000000 : ℚ),
   (136495584887 / 125000000000 : ℚ),
   (136495584887 / 125000000000 : ℚ),
   (271248334587 / 250000000000 : ℚ),
   (271248334587 / 250000000000 : ℚ),
   (271248334587 / 250000000000 : ℚ),
   (271248334587 / 250000000000 : ℚ),
   (271248334587 / 250000000000 : ℚ),
   (271248334587 / 250000000000 : ℚ),
   (538886445909 / 500000000000 : ℚ),
   (538886445909 / 500000000000 : ℚ),
   (538886445909 / 500000000000 : ℚ),
   (538886445909 / 500000000000 : ℚ),
   (538886445909 / 500000000000 : ℚ),
   (538886445909 / 500000000000 : ℚ),
   (4281177753 / 4000000000 : ℚ),
   (4281177753 / 4000000000 : ℚ),
   (4281177753 / 4000000000 : ℚ),
   (4281177753 / 4000000000 : ℚ),
   (4281177753 / 4000000000 : ℚ),
   (4281177753 / 4000000000 : ℚ),
   (1062548758321 / 1000000000000 : ℚ),
   (1062548758321 / 1000000000000 : ℚ),
   (1062548758321 / 1000000000000 : ℚ),
   (1062548758321 / 1000000000000 : ℚ),
   (1062548758321 / 1000000000000 : ℚ),
   (1062548758321 / 1000000000000 : ℚ),
   (42181052131 / 40000000000 : ℚ),
   (42181052131 / 40000000000 : ℚ),
   (42181052131 / 40000000000 : ℚ),
   (42181052131 / 40000000000 : ℚ),
   (42181052131 / 40000000000 : ℚ),
   (42181052131 / 40000000000 : ℚ),
   (65388573947 / 62500000000 : ℚ),
   (65388573947 / 62500000000 : ℚ),
   (65388573947 / 62500000000 : ℚ),
   (65388573947 / 62500000000 : ℚ),
   (65388573947 / 62500000000 : ℚ),
   (65388573947 / 62500000000 : ℚ),
   (259402788649 / 250000000000 : ℚ),
   (259402788649 / 250000000000 : ℚ),
   (259402788649 / 250000000000 : ℚ),
   (259402788649 / 250000000000 : ℚ),
   (259402788649 / 250000000000 : ℚ),
   (259402788649 / 250000000000 : ℚ),
   (41147904329 / 40000000000 : ℚ),
   (41147904329 / 40000000000 : ℚ),
   (41147904329 / 40000000000 : ℚ),
   (41147904329 / 40000000000 : ℚ),
   (41147904329 / 40000000000 : ℚ),
   (41147904329 / 40000000000 : ℚ),
   (254866388889 / 250000000000 : ℚ),
   (254866388889 / 250000000000 : ℚ),
   (254866388889 / 250000000000 : ℚ),
   (254866388889 / 250000000000 : ℚ),
   (254866388889 / 250000000000 : ℚ),
   (254866388889 / 250000000000 : ℚ),
   (31559487983 / 31250000000 : ℚ),
   (31559487983 / 31250000000 : ℚ),
   (31559487983 / 31250000000 : ℚ),
   (31559487983 / 31250000000 : ℚ),
   (31559487983 / 31250000000 : ℚ),
   (31559487983 / 31250000000 : ℚ)]

noncomputable def vs2 : ℕ → Fin 3 → Bool → ℝ := castT vs2Q

theorem solS2_0 : AutoSol f0 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f0A (v := vs2Q) (by decide +kernel)

theorem heS2_0 : autoBound f0 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (973312001357 / 25000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f0A (v := vs2Q) (e := (973312001357 / 25000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_1 : AutoSol f1 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f1A (v := vs2Q) (by decide +kernel)

theorem heS2_1 : autoBound f1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (424892728903 / 10000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f1A (v := vs2Q) (e := (424892728903 / 10000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_2 : AutoSol f2 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f2A (v := vs2Q) (by decide +kernel)

theorem heS2_2 : autoBound f2 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (579567464303 / 12500000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f2A (v := vs2Q) (e := (579567464303 / 12500000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_3 : AutoSol f3 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f3A (v := vs2Q) (by decide +kernel)

theorem heS2_3 : autoBound f3 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (1264711331267 / 25000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f3A (v := vs2Q) (e := (1264711331267 / 25000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_4 : AutoSol f4 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f4A (v := vs2Q) (by decide +kernel)

theorem heS2_4 : autoBound f4 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (5518822435647 / 100000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f4A (v := vs2Q) (e := (5518822435647 / 100000000000000 : ℚ)) (by norm_num) (by decide +kernel)

theorem solS2_5 : AutoSol f5 11 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]
  exact autoSol_ofQ f5A (v := vs2Q) (by decide +kernel)

theorem heS2_5 : autoBound f5 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (1161 / 1000 : ℝ) (2001 / 1250 : ℝ) (5351 / 5000 : ℝ) (6209 / 10000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (3009840523241 / 50000000000000 : ℝ) := by
  rw [xgQ2]
  exact autoBound_le_ofQ f5A (v := vs2Q) (e := (3009840523241 / 50000000000000 : ℚ)) (by norm_num) (by decide +kernel)

end Cryptarchia.Prob.Certs.E20D11
