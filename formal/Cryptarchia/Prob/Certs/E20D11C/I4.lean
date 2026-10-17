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

/-! # E20D11C: tables for index 4 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ4 : xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4 = castX (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 4) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 4

/-- Phase expectation 4 over the integers. -/
def X4 : PhZ := PhZ.ofQ (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 4)

theorem X4R : X4.Rep (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 4).1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 4).2.1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 4).2.2 := by decide +kernel

/-- Each member's post-switch seeds, by Newton's method from the previous member's, at
elaboration time. -/
def sd4 : List (List ℤ) :=
  eval% seedsZ DZ 11 X4 SZ (gFloorZ X4 SZ) (2 ^ 32) (2 ^ 8) 3 2 200 ((List.finRange 32).map famZ) [gFloorZ X4 SZ 0 0 true, gFloorZ X4 SZ 0 1 true, gFloorZ X4 SZ 0 2 true]

/-- Each member's pre-switch seeds, from `vmax`'s, at elaboration time. -/
def psd4 : List (List ℤ) := eval% preSeedsZ ((List.finRange 32).map famZ) DZ 11 X4 SZ (2 ^ 32) (2 ^ 8) 0 200 sd4

def postTop4 (k : Fin 32) : Fin 3 → ℤ := seedL (sd4.getD k.val [])
def preTop4 (k : Fin 32) : Fin 3 → ℤ := seedL (psd4.getD k.val [])

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up, at
elaboration time. -/
def eInL4 : List ℚ := eval% eInListQ ((List.finRange 32).map famZ) DZ 11 X4 SZ 13 sd4

def eIn4 (k : Fin 32) : ℚ := eInL4.getD k.val 0

theorem chkE4 : (List.finRange 32).all (chkOneF famZ DZ 11 X4 SZ postTop4 preTop4 eIn4 (997800110073 / 1000000000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vmax4 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (vmaxF famZ DZ 11 X4 SZ postTop4))
noncomputable def vpreI4 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (preF famZ DZ 11 X4 SZ postTop4 preTop4 k))
noncomputable def vpostI4 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (postF famZ DZ 11 X4 SZ postTop4 k))

theorem solE4 : AutoSolE fam 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4).2.2 vpreI4 vpostI4 vmax4 := by
  rw [xgQ4]; exact (oneSwitchF_sound famR famA DZ_pos X4R SZ_pos chkE4).1

theorem heEall4 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4).2.2 (vpreI4 k) ≤ (997800110073 / 1000000000000 : ℝ) := by
  rw [xgQ4]; exact fun k => ((oneSwitchF_sound famR famA DZ_pos X4R SZ_pos chkE4).2.2 k).trans_eq (by push_cast; ring)

theorem heIn4 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 4).2.2 (vpostI4 k) ≤ (eIn4 k : ℝ) := by
  rw [xgQ4]; exact (oneSwitchF_sound famR famA DZ_pos X4R SZ_pos chkE4).2.1

end Cryptarchia.Prob.Certs.E20D11C
