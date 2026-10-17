module

public import Cryptarchia.Prob.Certs.E20D11C.Fam
meta import Cryptarchia.Prob.Certs.E20D11C.Fam
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

/-! # E20D11C: tables for index 1 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ1 : xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1 = castX (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 1) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 1

/-- Phase expectation 1 over the integers. -/
def X1 : PhZ := PhZ.ofQ (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 1)

theorem X1R : X1.Rep (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 1).1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 1).2.1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 1).2.2 := by decide +kernel

/-- The switching table's seeds, by Newton's method at elaboration time. -/
def vsTop1 : Fin 3 → ℤ :=
  seedL (eval% solveSeedsZ ((List.finRange 32).map famZ) DZ 11 X1 SZ (gFloorZ X1 SZ) (2 ^ 32) (2 ^ 8) 3 200 [gFloorZ X1 SZ 0 0 true, gFloorZ X1 SZ 0 1 true, gFloorZ X1 SZ 0 2 true])

theorem chkS1 : (List.finRange 32).all (chkSwF famZ DZ 11 X1 SZ vsTop1 fun _ => (125348315253 / 125000000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vs1 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (fillAllZ ((List.finRange 32).map famZ) DZ 11 X1 SZ (gFloorZ X1 SZ) vsTop1))

theorem solS1 : ∀ k, AutoSol (fam k) 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.2 vs1 := by
  rw [xgQ1]; exact (switchF_sound famR famA DZ_pos X1R SZ_pos chkS1).1

theorem heS1 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.2 vs1 ≤ (125348315253 / 125000000000 : ℝ) := by
  rw [xgQ1]
  exact fun k => ((switchF_sound famR famA DZ_pos X1R SZ_pos chkS1).2 k).trans_eq (by push_cast; ring)

/-- Each member's post-switch seeds, by Newton's method from the previous member's, at
elaboration time. -/
def sd1 : List (List ℤ) :=
  eval% seedsZ DZ 11 X1 SZ (gFloorZ X1 SZ) (2 ^ 32) (2 ^ 8) 3 2 200 ((List.finRange 32).map famZ) [gFloorZ X1 SZ 0 0 true, gFloorZ X1 SZ 0 1 true, gFloorZ X1 SZ 0 2 true]

/-- Each member's pre-switch seeds, from `vmax`'s, at elaboration time. -/
def psd1 : List (List ℤ) := eval% preSeedsZ ((List.finRange 32).map famZ) DZ 11 X1 SZ (2 ^ 32) (2 ^ 8) 0 200 sd1

def postTop1 (k : Fin 32) : Fin 3 → ℤ := seedL (sd1.getD k.val [])
def preTop1 (k : Fin 32) : Fin 3 → ℤ := seedL (psd1.getD k.val [])

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up, at
elaboration time. -/
def eInL1 : List ℚ := eval% eInListQ ((List.finRange 32).map famZ) DZ 11 X1 SZ 13 sd1

def eIn1 (k : Fin 32) : ℚ := eInL1.getD k.val 0

theorem chkE1 : (List.finRange 32).all (chkOneF famZ DZ 11 X1 SZ postTop1 preTop1 eIn1 (125348315253 / 125000000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vmax1 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (vmaxF famZ DZ 11 X1 SZ postTop1))
noncomputable def vpreI1 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (preF famZ DZ 11 X1 SZ postTop1 preTop1 k))
noncomputable def vpostI1 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (postF famZ DZ 11 X1 SZ postTop1 k))

theorem solE1 : AutoSolE fam 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.2 vpreI1 vpostI1 vmax1 := by
  rw [xgQ1]; exact (oneSwitchF_sound famR famA DZ_pos X1R SZ_pos chkE1).1

theorem heEall1 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.2 (vpreI1 k) ≤ (125348315253 / 125000000000 : ℝ) := by
  rw [xgQ1]; exact fun k => ((oneSwitchF_sound famR famA DZ_pos X1R SZ_pos chkE1).2.2 k).trans_eq (by push_cast; ring)

theorem heIn1 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 1).2.2 (vpostI1 k) ≤ (eIn1 k : ℝ) := by
  rw [xgQ1]; exact (oneSwitchF_sound famR famA DZ_pos X1R SZ_pos chkE1).2.1

end Cryptarchia.Prob.Certs.E20D11C
