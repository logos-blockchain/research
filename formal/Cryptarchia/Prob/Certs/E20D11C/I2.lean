module

public import Cryptarchia.Prob.Certs.E20D11C.Fam
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

/-! # E20D11C: tables for index 2 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ2 : xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2 = castX (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 2) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 2

/-- Phase expectation 2 over the integers. -/
def X2 : PhZ := ⟨17137, 10000, 1, 1,
  fun a b u => [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  1⟩

theorem X2R : X2.Rep (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 2).1 (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 2).2.1 (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 2).2.2 := by decide +kernel

/-- The switching table, from its entries at `(0, a, true)`. -/
def vs2Z : ℕ → Fin 3 → Bool → ℤ :=
  fillAllZ ((List.finRange 32).map famZ) DZ 11 X2 SZ (fun _ _ _ => 0) ![20493565983494711950, 20493565983494711950, 20493565983494711950]

def eS2 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (93043182889 / 2500000000000 : ℚ)
  | 1 => (118266339917 / 3125000000000 : ℚ)
  | 2 => (769672666769 / 20000000000000 : ℚ)
  | 3 => (3913265573353 / 100000000000000 : ℚ)
  | 4 => (3979246740203 / 100000000000000 : ℚ)
  | 5 => (2023162119023 / 50000000000000 : ℚ)
  | 6 => (411451573313 / 10000000000000 : ℚ)
  | 7 => (418383915773 / 10000000000000 : ℚ)
  | 8 => (212715635671 / 5000000000000 : ℚ)
  | 9 => (2162977437277 / 50000000000000 : ℚ)
  | 10 => (549848048947 / 12500000000000 : ℚ)
  | 11 => (4472820294541 / 100000000000000 : ℚ)
  | 12 => (28425511853 / 625000000000 : ℚ)
  | 13 => (2312294398437 / 50000000000000 : ℚ)
  | 14 => (73474388831 / 1562500000000 : ℚ)
  | 15 => (597677293033 / 12500000000000 : ℚ)
  | 16 => (972356330781 / 20000000000000 : ℚ)
  | 17 => (4943471594381 / 100000000000000 : ℚ)
  | 18 => (125662731247 / 2500000000000 : ℚ)
  | 19 => (255545800609 / 5000000000000 : ℚ)
  | 20 => (5196713584079 / 100000000000000 : ℚ)
  | 21 => (5283923982989 / 100000000000000 : ℚ)
  | 22 => (335785596533 / 6250000000000 : ℚ)
  | 23 => (5462672926077 / 100000000000000 : ℚ)
  | 24 => (5554257110321 / 100000000000000 : ℚ)
  | 25 => (5647345408853 / 100000000000000 : ℚ)
  | 26 => (1148392293151 / 20000000000000 : ℚ)
  | 27 => (2919064630573 / 50000000000000 : ℚ)
  | 28 => (148396827869 / 2500000000000 : ℚ)
  | 29 => (377201105597 / 6250000000000 : ℚ)
  | 30 => (3068093997611 / 50000000000000 : ℚ)
  | _ => (249552375671 / 4000000000000 : ℚ)

theorem chkS2 : ∀ k, (autoSolZ (famZ k) DZ 11 X2 SZ vs2Z &&
    decide ((autoBoundZ (famZ k) DZ X2 SZ vs2Z : ℚ) ≤ eS2 k * (X2.M DZ * SZ : ℤ))) = true := by
  decide +kernel

noncomputable def vs2 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vs2Z)

theorem solS2_0 : AutoSol (fam 0) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 0

theorem heS2_0 : autoBound (fam 0) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (93043182889 / 2500000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 0; rw [show eS2 0 = (93043182889 / 2500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_1 : AutoSol (fam 1) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 1

theorem heS2_1 : autoBound (fam 1) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (118266339917 / 3125000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 1; rw [show eS2 1 = (118266339917 / 3125000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_2 : AutoSol (fam 2) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 2

theorem heS2_2 : autoBound (fam 2) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (769672666769 / 20000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 2; rw [show eS2 2 = (769672666769 / 20000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_3 : AutoSol (fam 3) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 3

theorem heS2_3 : autoBound (fam 3) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (3913265573353 / 100000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 3; rw [show eS2 3 = (3913265573353 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_4 : AutoSol (fam 4) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 4

theorem heS2_4 : autoBound (fam 4) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (3979246740203 / 100000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 4; rw [show eS2 4 = (3979246740203 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_5 : AutoSol (fam 5) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 5

theorem heS2_5 : autoBound (fam 5) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (2023162119023 / 50000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 5; rw [show eS2 5 = (2023162119023 / 50000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_6 : AutoSol (fam 6) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 6

theorem heS2_6 : autoBound (fam 6) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (411451573313 / 10000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 6; rw [show eS2 6 = (411451573313 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_7 : AutoSol (fam 7) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 7

theorem heS2_7 : autoBound (fam 7) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (418383915773 / 10000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 7; rw [show eS2 7 = (418383915773 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_8 : AutoSol (fam 8) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 8

theorem heS2_8 : autoBound (fam 8) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (212715635671 / 5000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 8; rw [show eS2 8 = (212715635671 / 5000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_9 : AutoSol (fam 9) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 9

theorem heS2_9 : autoBound (fam 9) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (2162977437277 / 50000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 9; rw [show eS2 9 = (2162977437277 / 50000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_10 : AutoSol (fam 10) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 10

theorem heS2_10 : autoBound (fam 10) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (549848048947 / 12500000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 10; rw [show eS2 10 = (549848048947 / 12500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_11 : AutoSol (fam 11) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 11

theorem heS2_11 : autoBound (fam 11) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (4472820294541 / 100000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 11; rw [show eS2 11 = (4472820294541 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_12 : AutoSol (fam 12) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 12

theorem heS2_12 : autoBound (fam 12) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (28425511853 / 625000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 12; rw [show eS2 12 = (28425511853 / 625000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_13 : AutoSol (fam 13) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 13

theorem heS2_13 : autoBound (fam 13) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (2312294398437 / 50000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 13; rw [show eS2 13 = (2312294398437 / 50000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_14 : AutoSol (fam 14) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 14

theorem heS2_14 : autoBound (fam 14) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (73474388831 / 1562500000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 14; rw [show eS2 14 = (73474388831 / 1562500000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_15 : AutoSol (fam 15) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 15

theorem heS2_15 : autoBound (fam 15) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (597677293033 / 12500000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 15; rw [show eS2 15 = (597677293033 / 12500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_16 : AutoSol (fam 16) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 16

theorem heS2_16 : autoBound (fam 16) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (972356330781 / 20000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 16; rw [show eS2 16 = (972356330781 / 20000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_17 : AutoSol (fam 17) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 17

theorem heS2_17 : autoBound (fam 17) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (4943471594381 / 100000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 17; rw [show eS2 17 = (4943471594381 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_18 : AutoSol (fam 18) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 18

theorem heS2_18 : autoBound (fam 18) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (125662731247 / 2500000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 18; rw [show eS2 18 = (125662731247 / 2500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_19 : AutoSol (fam 19) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 19

theorem heS2_19 : autoBound (fam 19) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (255545800609 / 5000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 19; rw [show eS2 19 = (255545800609 / 5000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_20 : AutoSol (fam 20) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 20

theorem heS2_20 : autoBound (fam 20) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (5196713584079 / 100000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 20; rw [show eS2 20 = (5196713584079 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_21 : AutoSol (fam 21) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 21

theorem heS2_21 : autoBound (fam 21) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (5283923982989 / 100000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 21; rw [show eS2 21 = (5283923982989 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_22 : AutoSol (fam 22) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 22

theorem heS2_22 : autoBound (fam 22) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (335785596533 / 6250000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 22; rw [show eS2 22 = (335785596533 / 6250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_23 : AutoSol (fam 23) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 23

theorem heS2_23 : autoBound (fam 23) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (5462672926077 / 100000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 23; rw [show eS2 23 = (5462672926077 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_24 : AutoSol (fam 24) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 24

theorem heS2_24 : autoBound (fam 24) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (5554257110321 / 100000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 24; rw [show eS2 24 = (5554257110321 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_25 : AutoSol (fam 25) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 25

theorem heS2_25 : autoBound (fam 25) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (5647345408853 / 100000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 25; rw [show eS2 25 = (5647345408853 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_26 : AutoSol (fam 26) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 26

theorem heS2_26 : autoBound (fam 26) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (1148392293151 / 20000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 26; rw [show eS2 26 = (1148392293151 / 20000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_27 : AutoSol (fam 27) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 27

theorem heS2_27 : autoBound (fam 27) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (2919064630573 / 50000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 27; rw [show eS2 27 = (2919064630573 / 50000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_28 : AutoSol (fam 28) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 28

theorem heS2_28 : autoBound (fam 28) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (148396827869 / 2500000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 28; rw [show eS2 28 = (148396827869 / 2500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_29 : AutoSol (fam 29) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 29

theorem heS2_29 : autoBound (fam 29) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (377201105597 / 6250000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 29; rw [show eS2 29 = (377201105597 / 6250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_30 : AutoSol (fam 30) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 30

theorem heS2_30 : autoBound (fam 30) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (3068093997611 / 50000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 30; rw [show eS2 30 = (3068093997611 / 50000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem solS2_31 : AutoSol (fam 31) 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 := by
  rw [xgQ2]; exact (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).1 31

theorem heS2_31 : autoBound (fam 31) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 2).2.2 vs2 ≤ (249552375671 / 4000000000000 : ℝ) := by
  rw [xgQ2]; have h := (switchZ_sound famR famA DZ_pos X2R SZ_pos chkS2).2 31; rw [show eS2 31 = (249552375671 / 4000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

end Cryptarchia.Prob.Certs.E20D11C
