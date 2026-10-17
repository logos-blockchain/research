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

/-! # E20D11M2: tables for index 0 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ0 : xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0 = castX (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 0) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 0

/-- Phase expectation 0 over the integers. -/
def X0 : PhZ := PhZ.ofQ (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 0)

theorem X0R : X0.Rep (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 0).1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 0).2.1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 0).2.2 := by decide +kernel

/-- The switching table's seeds, by Newton's method at elaboration time. -/
def vsTop0 : Fin 3 → ℤ :=
  seedL (eval% solveSeedsZ ((List.finRange 32).map famZ) DZ 11 X0 SZ (gFloorZ X0 SZ) (2 ^ 32) (2 ^ 8) 3 200 [gFloorZ X0 SZ 0 0 true, gFloorZ X0 SZ 0 1 true, gFloorZ X0 SZ 0 2 true])

theorem chkS0 : (List.finRange 32).all (chkSwF famZ DZ 11 X0 SZ vsTop0 fun _ => (62381919583 / 62500000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vs0 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (fillAllZ ((List.finRange 32).map famZ) DZ 11 X0 SZ (gFloorZ X0 SZ) vsTop0))

theorem solS0 : ∀ k, AutoSol (fam k) 11 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.2 vs0 := by
  rw [xgQ0]; exact (switchF_sound famR famA DZ_pos X0R SZ_pos chkS0).1

theorem heS0 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.2 vs0 ≤ (62381919583 / 62500000000 : ℝ) := by
  rw [xgQ0]
  exact fun k => ((switchF_sound famR famA DZ_pos X0R SZ_pos chkS0).2 k).trans_eq (by push_cast; ring)

/-- Each member's post-switch seeds, by Newton's method from the previous member's, at
elaboration time. -/
def sd0 : List (List ℤ) :=
  eval% seedsZ DZ 11 X0 SZ (gFloorZ X0 SZ) (2 ^ 32) (2 ^ 8) 3 2 200 ((List.finRange 32).map famZ) [gFloorZ X0 SZ 0 0 true, gFloorZ X0 SZ 0 1 true, gFloorZ X0 SZ 0 2 true]

/-- Each member's pre-switch seeds, from `vmax`'s, at elaboration time. -/
def psd0 : List (List ℤ) := eval% preSeedsZ ((List.finRange 32).map famZ) DZ 11 X0 SZ (2 ^ 32) (2 ^ 8) 0 200 sd0

def postTop0 (k : Fin 32) : Fin 3 → ℤ := seedL (sd0.getD k.val [])
def preTop0 (k : Fin 32) : Fin 3 → ℤ := seedL (psd0.getD k.val [])

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up, at
elaboration time. -/
def eInL0 : List ℚ := eval% eInListQ ((List.finRange 32).map famZ) DZ 11 X0 SZ 13 sd0

def eIn0 (k : Fin 32) : ℚ := eInL0.getD k.val 0

theorem chkE0 : (List.finRange 32).all (chkOneF famZ DZ 11 X0 SZ postTop0 preTop0 eIn0 (62381919583 / 62500000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vmax0 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (vmaxF famZ DZ 11 X0 SZ postTop0))
noncomputable def vpreI0 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (preF famZ DZ 11 X0 SZ postTop0 preTop0 k))
noncomputable def vpostI0 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (postF famZ DZ 11 X0 SZ postTop0 k))

theorem solE0 : AutoSolE fam 11 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.2 vpreI0 vpostI0 vmax0 := by
  rw [xgQ0]; exact (oneSwitchF_sound famR famA DZ_pos X0R SZ_pos chkE0).1

theorem heEall0 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.2 (vpreI0 k) ≤ (62381919583 / 62500000000 : ℝ) := by
  rw [xgQ0]; exact fun k => ((oneSwitchF_sound famR famA DZ_pos X0R SZ_pos chkE0).2.2 k).trans_eq (by push_cast; ring)

theorem heIn0 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 0).2.2 (vpostI0 k) ≤ (eIn0 k : ℝ) := by
  rw [xgQ0]; exact (oneSwitchF_sound famR famA DZ_pos X0R SZ_pos chkE0).2.1

end Cryptarchia.Prob.Certs.E20D11M2
