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

/-! # E20D11C: tables for index 8 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ8 : xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8 = castX (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 8) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 8

/-- Phase expectation 8 over the integers. -/
def X8 : PhZ := ⟨31000833, 50000000, 1, 1,
  fun a b u => [31000833, 31000833, 50000000, 50000000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  31000833⟩

theorem X8R : X8.Rep (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 8).1 (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 8).2.1 (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 8).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax8Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [29752013556780870845, 29752013556780870845, 0, 0, 0, 0, 29752013556780870845, 29752013556780870845, 0, 0, 0, 0, 29752013556780870845, 29752013556780870845, 0, 0, 0, 0, 29752013556780870845, 29752013556780870845, 0, 0, 0, 0, 29752013556780870845, 29752013556780870845, 0, 0, 0, 0, 29752013556780870845, 29752013556780870845, 0, 0, 0, 0, 29752013556762424101, 29752013556762424101, 0, 0, 0, 0, 29752013556762424101, 29752013556762424101, 0, 0, 0, 0, 29752013556762424101, 29752013556762424101, 0, 0, 0, 0, 29752013556762424101, 29752013556762424101, 0, 0, 0, 0, 29752013556762424101, 29752013556762424101, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop8 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![29752013556780870845, 0, 0]
  | 1 => ![29752013556780870845, 0, 0]
  | 2 => ![29752013556780870845, 0, 0]
  | 3 => ![29752013556780870845, 0, 0]
  | 4 => ![29752013556780870845, 0, 0]
  | 5 => ![29752013556780870845, 0, 0]
  | 6 => ![29752013556780870845, 0, 0]
  | 7 => ![29752013556780870845, 0, 0]
  | 8 => ![29752013556780870845, 0, 0]
  | 9 => ![29752013556780870845, 0, 0]
  | 10 => ![29752013556780870845, 0, 0]
  | 11 => ![29752013556780870845, 0, 0]
  | 12 => ![29752013556780870845, 0, 0]
  | 13 => ![29752013556780870845, 0, 0]
  | 14 => ![29752013556780870845, 0, 0]
  | 15 => ![29752013556780870845, 0, 0]
  | 16 => ![29752013556780870845, 0, 0]
  | 17 => ![29752013556780870845, 0, 0]
  | 18 => ![29752013556780870845, 0, 0]
  | 19 => ![29752013556780870845, 0, 0]
  | 20 => ![29752013556780870845, 0, 0]
  | 21 => ![29752013556780870845, 0, 0]
  | 22 => ![29752013556780870845, 0, 0]
  | 23 => ![29752013556780870845, 0, 0]
  | 24 => ![29752013556780870845, 0, 0]
  | 25 => ![29752013556780870845, 0, 0]
  | 26 => ![29752013556780870845, 0, 0]
  | 27 => ![29752013556780870845, 0, 0]
  | 28 => ![29752013556780870845, 0, 0]
  | 29 => ![29752013556780870845, 0, 0]
  | 30 => ![29752013556780870845, 0, 0]
  | _ => ![29752013556780870845, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop8 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![29752013556854657821, 0, 0]
  | 1 => ![29752013556854657821, 0, 0]
  | 2 => ![29752013556854657821, 0, 0]
  | 3 => ![29752013556854657821, 0, 0]
  | 4 => ![29752013556854657821, 0, 0]
  | 5 => ![29752013556854657821, 0, 0]
  | 6 => ![29752013556854657821, 0, 0]
  | 7 => ![29752013556854657821, 0, 0]
  | 8 => ![29752013556854657821, 0, 0]
  | 9 => ![29752013556854657821, 0, 0]
  | 10 => ![29752013556854657821, 0, 0]
  | 11 => ![29752013556854657821, 0, 0]
  | 12 => ![29752013556854657821, 0, 0]
  | 13 => ![29752013556854657821, 0, 0]
  | 14 => ![29752013556854657821, 0, 0]
  | 15 => ![29752013556854657821, 0, 0]
  | 16 => ![29752013556854657821, 0, 0]
  | 17 => ![29752013556854657821, 0, 0]
  | 18 => ![29752013556854657821, 0, 0]
  | 19 => ![29752013556854657821, 0, 0]
  | 20 => ![29752013556854657821, 0, 0]
  | 21 => ![29752013556854657821, 0, 0]
  | 22 => ![29752013556854657821, 0, 0]
  | 23 => ![29752013556854657821, 0, 0]
  | 24 => ![29752013556854657821, 0, 0]
  | 25 => ![29752013556854657821, 0, 0]
  | 26 => ![29752013556854657821, 0, 0]
  | 27 => ![29752013556854657821, 0, 0]
  | 28 => ![29752013556854657821, 0, 0]
  | 29 => ![29752013556854657821, 0, 0]
  | 30 => ![29752013556854657821, 0, 0]
  | _ => ![29752013556854657821, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn8 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (1008637367279 / 1000000000000 : ℚ)
  | 1 => (100878075239 / 100000000000 : ℚ)
  | 2 => (1008926442487 / 1000000000000 : ℚ)
  | 3 => (252268618007 / 250000000000 : ℚ)
  | 4 => (1009224875893 / 1000000000000 : ℚ)
  | 5 => (100937768939 / 100000000000 : ℚ)
  | 6 => (504766474127 / 500000000000 : ℚ)
  | 7 => (126211336081 / 125000000000 : ℚ)
  | 8 => (31557842099 / 31250000000 : ℚ)
  | 9 => (25250344021 / 25000000000 : ℚ)
  | 10 => (252544791781 / 250000000000 : ℚ)
  | 11 => (202069440783 / 200000000000 : ℚ)
  | 12 => (1010517909541 / 1000000000000 : ℚ)
  | 13 => (1010691322767 / 1000000000000 : ℚ)
  | 14 => (1010867482793 / 1000000000000 : ℚ)
  | 15 => (202209285851 / 200000000000 : ℚ)
  | 16 => (40449128089 / 40000000000 : ℚ)
  | 17 => (101141284221 / 100000000000 : ℚ)
  | 18 => (1011600390153 / 1000000000000 : ℚ)
  | 19 => (1011790887431 / 1000000000000 : ℚ)
  | 20 => (505992187927 / 500000000000 : ℚ)
  | 21 => (1012180897663 / 1000000000000 : ℚ)
  | 22 => (1012380495531 / 1000000000000 : ℚ)
  | 23 => (506291606279 / 500000000000 : ℚ)
  | 24 => (1012789092271 / 1000000000000 : ℚ)
  | 25 => (50649908931 / 50000000000 : ℚ)
  | 26 => (126651314497 / 125000000000 : ℚ)
  | 27 => (1013426149127 / 1000000000000 : ℚ)
  | 28 => (253411280819 / 250000000000 : ℚ)
  | 29 => (253466871009 / 250000000000 : ℚ)
  | 30 => (63380829839 / 62500000000 : ℚ)
  | _ => (50716127493 / 50000000000 : ℚ)

def post8Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X8 SZ (gFloorZ X8 SZ) (postTop8 k)
def pre8Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X8 SZ vmax8Z (preTop8 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE8Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X8 SZ (post8Z k) && leTabZ 11 (post8Z k) vmax8Z &&
    preSolZ (famZ k) DZ 11 X8 SZ vmax8Z (pre8Z k) &&
    decide ((autoBoundZ (famZ k) DZ X8 SZ (post8Z k) : ℚ) ≤ eIn8 k * (X8.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X8 SZ (pre8Z k) : ℚ) ≤ (50716127493 / 50000000000 : ℚ) * (X8.M DZ * SZ : ℤ))

theorem chkE8_0 : chkE8Q 0 = true := by decide +kernel
theorem chkE8_1 : chkE8Q 1 = true := by decide +kernel
theorem chkE8_2 : chkE8Q 2 = true := by decide +kernel
theorem chkE8_3 : chkE8Q 3 = true := by decide +kernel
theorem chkE8_4 : chkE8Q 4 = true := by decide +kernel
theorem chkE8_5 : chkE8Q 5 = true := by decide +kernel
theorem chkE8_6 : chkE8Q 6 = true := by decide +kernel
theorem chkE8_7 : chkE8Q 7 = true := by decide +kernel
theorem chkE8_8 : chkE8Q 8 = true := by decide +kernel
theorem chkE8_9 : chkE8Q 9 = true := by decide +kernel
theorem chkE8_10 : chkE8Q 10 = true := by decide +kernel
theorem chkE8_11 : chkE8Q 11 = true := by decide +kernel
theorem chkE8_12 : chkE8Q 12 = true := by decide +kernel
theorem chkE8_13 : chkE8Q 13 = true := by decide +kernel
theorem chkE8_14 : chkE8Q 14 = true := by decide +kernel
theorem chkE8_15 : chkE8Q 15 = true := by decide +kernel
theorem chkE8_16 : chkE8Q 16 = true := by decide +kernel
theorem chkE8_17 : chkE8Q 17 = true := by decide +kernel
theorem chkE8_18 : chkE8Q 18 = true := by decide +kernel
theorem chkE8_19 : chkE8Q 19 = true := by decide +kernel
theorem chkE8_20 : chkE8Q 20 = true := by decide +kernel
theorem chkE8_21 : chkE8Q 21 = true := by decide +kernel
theorem chkE8_22 : chkE8Q 22 = true := by decide +kernel
theorem chkE8_23 : chkE8Q 23 = true := by decide +kernel
theorem chkE8_24 : chkE8Q 24 = true := by decide +kernel
theorem chkE8_25 : chkE8Q 25 = true := by decide +kernel
theorem chkE8_26 : chkE8Q 26 = true := by decide +kernel
theorem chkE8_27 : chkE8Q 27 = true := by decide +kernel
theorem chkE8_28 : chkE8Q 28 = true := by decide +kernel
theorem chkE8_29 : chkE8Q 29 = true := by decide +kernel
theorem chkE8_30 : chkE8Q 30 = true := by decide +kernel
theorem chkE8_31 : chkE8Q 31 = true := by decide +kernel

theorem chkE8 : ∀ k, chkE8Q k = true := fun k => by
  fin_cases k; exacts [chkE8_0, chkE8_1, chkE8_2, chkE8_3, chkE8_4, chkE8_5, chkE8_6, chkE8_7, chkE8_8, chkE8_9, chkE8_10, chkE8_11, chkE8_12, chkE8_13, chkE8_14, chkE8_15, chkE8_16, chkE8_17, chkE8_18, chkE8_19, chkE8_20, chkE8_21, chkE8_22, chkE8_23, chkE8_24, chkE8_25, chkE8_26, chkE8_27, chkE8_28, chkE8_29, chkE8_30, chkE8_31]

noncomputable def vmax8 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax8Z)
noncomputable def vpreI8 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre8Z k))
noncomputable def vpostI8 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post8Z k))

theorem solE8 : AutoSolE fam 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 vpreI8 vpostI8 vmax8 := by
  rw [xgQ8]; exact (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).1

theorem heEall8 : ∀ k, autoBound (fam k) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpreI8 k) ≤ (50716127493 / 50000000000 : ℝ) := by
  rw [xgQ8]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.2 k).trans_eq (by push_cast; ring)

theorem heIn8_0 : autoBound (fam 0) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 0) ≤ (1008637367279 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 0; rw [show eIn8 0 = (1008637367279 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_1 : autoBound (fam 1) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 1) ≤ (100878075239 / 100000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 1; rw [show eIn8 1 = (100878075239 / 100000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_2 : autoBound (fam 2) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 2) ≤ (1008926442487 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 2; rw [show eIn8 2 = (1008926442487 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_3 : autoBound (fam 3) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 3) ≤ (252268618007 / 250000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 3; rw [show eIn8 3 = (252268618007 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_4 : autoBound (fam 4) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 4) ≤ (1009224875893 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 4; rw [show eIn8 4 = (1009224875893 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_5 : autoBound (fam 5) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 5) ≤ (100937768939 / 100000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 5; rw [show eIn8 5 = (100937768939 / 100000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_6 : autoBound (fam 6) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 6) ≤ (504766474127 / 500000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 6; rw [show eIn8 6 = (504766474127 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_7 : autoBound (fam 7) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 7) ≤ (126211336081 / 125000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 7; rw [show eIn8 7 = (126211336081 / 125000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_8 : autoBound (fam 8) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 8) ≤ (31557842099 / 31250000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 8; rw [show eIn8 8 = (31557842099 / 31250000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_9 : autoBound (fam 9) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 9) ≤ (25250344021 / 25000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 9; rw [show eIn8 9 = (25250344021 / 25000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_10 : autoBound (fam 10) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 10) ≤ (252544791781 / 250000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 10; rw [show eIn8 10 = (252544791781 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_11 : autoBound (fam 11) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 11) ≤ (202069440783 / 200000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 11; rw [show eIn8 11 = (202069440783 / 200000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_12 : autoBound (fam 12) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 12) ≤ (1010517909541 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 12; rw [show eIn8 12 = (1010517909541 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_13 : autoBound (fam 13) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 13) ≤ (1010691322767 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 13; rw [show eIn8 13 = (1010691322767 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_14 : autoBound (fam 14) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 14) ≤ (1010867482793 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 14; rw [show eIn8 14 = (1010867482793 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_15 : autoBound (fam 15) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 15) ≤ (202209285851 / 200000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 15; rw [show eIn8 15 = (202209285851 / 200000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_16 : autoBound (fam 16) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 16) ≤ (40449128089 / 40000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 16; rw [show eIn8 16 = (40449128089 / 40000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_17 : autoBound (fam 17) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 17) ≤ (101141284221 / 100000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 17; rw [show eIn8 17 = (101141284221 / 100000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_18 : autoBound (fam 18) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 18) ≤ (1011600390153 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 18; rw [show eIn8 18 = (1011600390153 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_19 : autoBound (fam 19) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 19) ≤ (1011790887431 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 19; rw [show eIn8 19 = (1011790887431 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_20 : autoBound (fam 20) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 20) ≤ (505992187927 / 500000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 20; rw [show eIn8 20 = (505992187927 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_21 : autoBound (fam 21) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 21) ≤ (1012180897663 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 21; rw [show eIn8 21 = (1012180897663 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_22 : autoBound (fam 22) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 22) ≤ (1012380495531 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 22; rw [show eIn8 22 = (1012380495531 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_23 : autoBound (fam 23) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 23) ≤ (506291606279 / 500000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 23; rw [show eIn8 23 = (506291606279 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_24 : autoBound (fam 24) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 24) ≤ (1012789092271 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 24; rw [show eIn8 24 = (1012789092271 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_25 : autoBound (fam 25) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 25) ≤ (50649908931 / 50000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 25; rw [show eIn8 25 = (50649908931 / 50000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_26 : autoBound (fam 26) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 26) ≤ (126651314497 / 125000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 26; rw [show eIn8 26 = (126651314497 / 125000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_27 : autoBound (fam 27) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 27) ≤ (1013426149127 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 27; rw [show eIn8 27 = (1013426149127 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_28 : autoBound (fam 28) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 28) ≤ (253411280819 / 250000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 28; rw [show eIn8 28 = (253411280819 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_29 : autoBound (fam 29) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 29) ≤ (253466871009 / 250000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 29; rw [show eIn8 29 = (253466871009 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_30 : autoBound (fam 30) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 30) ≤ (63380829839 / 62500000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 30; rw [show eIn8 30 = (63380829839 / 62500000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_31 : autoBound (fam 31) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 31) ≤ (50716127493 / 50000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 31; rw [show eIn8 31 = (50716127493 / 50000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

end Cryptarchia.Prob.Certs.E20D11C
