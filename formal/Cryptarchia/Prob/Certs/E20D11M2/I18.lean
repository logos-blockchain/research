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

/-! # E20D11M2: tables for index 18 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ18 : xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18 = castX (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 18) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 18

/-- Phase expectation 18 over the integers. -/
def X18 : PhZ := PhZ.ofQ (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 18)

theorem X18R : X18.Rep (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 18).1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 18).2.1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 18).2.2 := by decide +kernel

/-- Each member's post-switch seeds, by Newton's method from the previous member's, at
elaboration time. -/
def sd18 : List (List ℤ) :=
  eval% seedsZ DZ 11 X18 SZ (gFloorZ X18 SZ) (2 ^ 32) (2 ^ 8) 3 2 200 ((List.finRange 32).map famZ) [gFloorZ X18 SZ 0 0 true, gFloorZ X18 SZ 0 1 true, gFloorZ X18 SZ 0 2 true]

/-- Each member's pre-switch seeds, from `vmax`'s, at elaboration time. -/
def psd18 : List (List ℤ) := eval% preSeedsZ ((List.finRange 32).map famZ) DZ 11 X18 SZ (2 ^ 32) (2 ^ 8) 0 200 sd18

def postTop18 (k : Fin 32) : Fin 3 → ℤ := seedL (sd18.getD k.val [])
def preTop18 (k : Fin 32) : Fin 3 → ℤ := seedL (psd18.getD k.val [])

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up, at
elaboration time. -/
def eInL18 : List ℚ := eval% eInListQ ((List.finRange 32).map famZ) DZ 11 X18 SZ 13 sd18

def eIn18 (k : Fin 32) : ℚ := eInL18.getD k.val 0

theorem chkE18 : (List.finRange 32).all (chkOneF famZ DZ 11 X18 SZ postTop18 preTop18 eIn18 (1000000000009 / 1000000000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vmax18 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (vmaxF famZ DZ 11 X18 SZ postTop18))
noncomputable def vpreI18 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (preF famZ DZ 11 X18 SZ postTop18 preTop18 k))
noncomputable def vpostI18 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (postF famZ DZ 11 X18 SZ postTop18 k))

theorem solE18 : AutoSolE fam 11 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18).2.2 vpreI18 vpostI18 vmax18 := by
  rw [xgQ18]; exact (oneSwitchF_sound famR famA DZ_pos X18R SZ_pos chkE18).1

theorem heEall18 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18).2.2 (vpreI18 k) ≤ (1000000000009 / 1000000000000 : ℝ) := by
  rw [xgQ18]; exact fun k => ((oneSwitchF_sound famR famA DZ_pos X18R SZ_pos chkE18).2.2 k).trans_eq (by push_cast; ring)

theorem heIn18 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 18).2.2 (vpostI18 k) ≤ (eIn18 k : ℝ) := by
  rw [xgQ18]; exact (oneSwitchF_sound famR famA DZ_pos X18R SZ_pos chkE18).2.1

end Cryptarchia.Prob.Certs.E20D11M2
