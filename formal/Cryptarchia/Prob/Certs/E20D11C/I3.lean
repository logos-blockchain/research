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

/-! # E20D11C: tables for index 3 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ3 : xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3 = castX (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 3) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 3

/-- Phase expectation 3 over the integers. -/
def X3 : PhZ := PhZ.ofQ (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 3)

theorem X3R : X3.Rep (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 3).1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 3).2.1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 3).2.2 := by decide +kernel

/-- Each member's post-switch seeds, by Newton's method from the previous member's, at
elaboration time. -/
def sd3 : List (List ℤ) :=
  eval% seedsZ DZ 11 X3 SZ (gFloorZ X3 SZ) (2 ^ 32) (2 ^ 8) 3 2 200 ((List.finRange 32).map famZ) [gFloorZ X3 SZ 0 0 true, gFloorZ X3 SZ 0 1 true, gFloorZ X3 SZ 0 2 true]

/-- Each member's pre-switch seeds, from `vmax`'s, at elaboration time. -/
def psd3 : List (List ℤ) := eval% preSeedsZ ((List.finRange 32).map famZ) DZ 11 X3 SZ (2 ^ 32) (2 ^ 8) 0 200 sd3

def postTop3 (k : Fin 32) : Fin 3 → ℤ := seedL (sd3.getD k.val [])
def preTop3 (k : Fin 32) : Fin 3 → ℤ := seedL (psd3.getD k.val [])

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up, at
elaboration time. -/
def eInL3 : List ℚ := eval% eInListQ ((List.finRange 32).map famZ) DZ 11 X3 SZ 13 sd3

def eIn3 (k : Fin 32) : ℚ := eInL3.getD k.val 0

theorem chkE3 : (List.finRange 32).all (chkOneF famZ DZ 11 X3 SZ postTop3 preTop3 eIn3 (1999057995773 / 2000000000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vmax3 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (vmaxF famZ DZ 11 X3 SZ postTop3))
noncomputable def vpreI3 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (preF famZ DZ 11 X3 SZ postTop3 preTop3 k))
noncomputable def vpostI3 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (postF famZ DZ 11 X3 SZ postTop3 k))

theorem solE3 : AutoSolE fam 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3).2.2 vpreI3 vpostI3 vmax3 := by
  rw [xgQ3]; exact (oneSwitchF_sound famR famA DZ_pos X3R SZ_pos chkE3).1

theorem heEall3 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3).2.2 (vpreI3 k) ≤ (1999057995773 / 2000000000000 : ℝ) := by
  rw [xgQ3]; exact fun k => ((oneSwitchF_sound famR famA DZ_pos X3R SZ_pos chkE3).2.2 k).trans_eq (by push_cast; ring)

theorem heIn3 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 3).2.2 (vpostI3 k) ≤ (eIn3 k : ℝ) := by
  rw [xgQ3]; exact (oneSwitchF_sound famR famA DZ_pos X3R SZ_pos chkE3).2.1

end Cryptarchia.Prob.Certs.E20D11C
