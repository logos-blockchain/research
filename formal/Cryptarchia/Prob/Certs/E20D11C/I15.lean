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

/-! # E20D11C: tables for index 15 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ15 : xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15 = castX (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 15) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 15

/-- Phase expectation 15 over the integers. -/
def X15 : PhZ := PhZ.ofQ (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 15)

theorem X15R : X15.Rep (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 15).1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 15).2.1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 15).2.2 := by decide +kernel

/-- Each member's post-switch seeds, by Newton's method from the previous member's, at
elaboration time. -/
def sd15 : List (List ℤ) :=
  eval% seedsZ DZ 11 X15 SZ (gFloorZ X15 SZ) (2 ^ 32) (2 ^ 8) 3 2 200 ((List.finRange 32).map famZ) [gFloorZ X15 SZ 0 0 true, gFloorZ X15 SZ 0 1 true, gFloorZ X15 SZ 0 2 true]

/-- Each member's pre-switch seeds, from `vmax`'s, at elaboration time. -/
def psd15 : List (List ℤ) := eval% preSeedsZ ((List.finRange 32).map famZ) DZ 11 X15 SZ (2 ^ 32) (2 ^ 8) 0 200 sd15

def postTop15 (k : Fin 32) : Fin 3 → ℤ := seedL (sd15.getD k.val [])
def preTop15 (k : Fin 32) : Fin 3 → ℤ := seedL (psd15.getD k.val [])

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up, at
elaboration time. -/
def eInL15 : List ℚ := eval% eInListQ ((List.finRange 32).map famZ) DZ 11 X15 SZ 13 sd15

def eIn15 (k : Fin 32) : ℚ := eInL15.getD k.val 0

theorem chkE15 : (List.finRange 32).all (chkOneF famZ DZ 11 X15 SZ postTop15 preTop15 eIn15 (4506980511537 / 500000000000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vmax15 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (vmaxF famZ DZ 11 X15 SZ postTop15))
noncomputable def vpreI15 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (preF famZ DZ 11 X15 SZ postTop15 preTop15 k))
noncomputable def vpostI15 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (postF famZ DZ 11 X15 SZ postTop15 k))

theorem solE15 : AutoSolE fam 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.2 vpreI15 vpostI15 vmax15 := by
  rw [xgQ15]; exact (oneSwitchF_sound famR famA DZ_pos X15R SZ_pos chkE15).1

theorem heEall15 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpreI15 k) ≤ (4506980511537 / 500000000000000 : ℝ) := by
  rw [xgQ15]; exact fun k => ((oneSwitchF_sound famR famA DZ_pos X15R SZ_pos chkE15).2.2 k).trans_eq (by push_cast; ring)

theorem heIn15 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 k) ≤ (eIn15 k : ℝ) := by
  rw [xgQ15]; exact (oneSwitchF_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1

end Cryptarchia.Prob.Certs.E20D11C
