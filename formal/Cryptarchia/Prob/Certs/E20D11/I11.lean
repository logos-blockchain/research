module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam
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

/-! # E20D11: tables for index 11 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ11 : xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11 = castX (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 11) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 11

/-- Phase expectation 11 over the integers. -/
def X11 : PhZ := PhZ.ofQ (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 11)

theorem X11R : X11.Rep (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 11).1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 11).2.1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 11).2.2 := by decide +kernel

/-- Each member's post-switch seeds, by Newton's method from the previous member's, at
elaboration time. -/
def sd11 : List (List ℤ) :=
  eval% seedsZ DZ 11 X11 SZ (gFloorZ X11 SZ) (2 ^ 32) (2 ^ 8) 3 2 200 ((List.finRange 32).map famZ) [gFloorZ X11 SZ 0 0 true, gFloorZ X11 SZ 0 1 true, gFloorZ X11 SZ 0 2 true]

/-- Each member's pre-switch seeds, from `vmax`'s, at elaboration time. -/
def psd11 : List (List ℤ) := eval% preSeedsZ ((List.finRange 32).map famZ) DZ 11 X11 SZ (2 ^ 32) (2 ^ 8) 0 200 sd11

def postTop11 (k : Fin 32) : Fin 3 → ℤ := seedL (sd11.getD k.val [])
def preTop11 (k : Fin 32) : Fin 3 → ℤ := seedL (psd11.getD k.val [])

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up, at
elaboration time. -/
def eInL11 : List ℚ := eval% eInListQ ((List.finRange 32).map famZ) DZ 11 X11 SZ 13 sd11

def eIn11 (k : Fin 32) : ℚ := eInL11.getD k.val 0

theorem chkE11 : (List.finRange 32).all (chkOneF famZ DZ 11 X11 SZ postTop11 preTop11 eIn11 (2476033887659 / 2500000000000 : ℚ)) = true := by
  decide +kernel

noncomputable def vmax11 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ (vmaxF famZ DZ 11 X11 SZ postTop11))
noncomputable def vpreI11 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (preF famZ DZ 11 X11 SZ postTop11 preTop11 k))
noncomputable def vpostI11 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (postF famZ DZ 11 X11 SZ postTop11 k))

theorem solE11 : AutoSolE fam 11 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11).2.2 vpreI11 vpostI11 vmax11 := by
  rw [xgQ11]; exact (oneSwitchF_sound famR famA DZ_pos X11R SZ_pos chkE11).1

theorem heEall11 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11).2.2 (vpreI11 k) ≤ (2476033887659 / 2500000000000 : ℝ) := by
  rw [xgQ11]; exact fun k => ((oneSwitchF_sound famR famA DZ_pos X11R SZ_pos chkE11).2.2 k).trans_eq (by push_cast; ring)

theorem heIn11 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 11).2.2 (vpostI11 k) ≤ (eIn11 k : ℝ) := by
  rw [xgQ11]; exact (oneSwitchF_sound famR famA DZ_pos X11R SZ_pos chkE11).2.1

end Cryptarchia.Prob.Certs.E20D11
