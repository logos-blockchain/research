module

public import Cryptarchia.Prob.Certs.E20D11M2.Fam
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

/-! # E20D11M2: tables for index 8 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ8 : xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8 = castX (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 8) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 8

/-- Phase expectation 8 over the integers. -/
def X8 : PhZ := ⟨31226787, 50000000, 1, 1,
  fun a b u => [31226787, 31226787, 50000000, 50000000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  31226787⟩

theorem X8R : X8.Rep (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 8).1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 8).2.1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 8).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax8Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [29536730874285489067, 29536730874285489067, 0, 0, 0, 0, 29536730874285489067, 29536730874285489067, 0, 0, 0, 0, 29536730874285489067, 29536730874285489067, 0, 0, 0, 0, 29536730874285489067, 29536730874285489067, 0, 0, 0, 0, 29536730874267042323, 29536730874267042323, 0, 0, 0, 0, 29536730874267042323, 29536730874267042323, 0, 0, 0, 0, 29536730874267042323, 29536730874267042323, 0, 0, 0, 0, 29536730874267042323, 29536730874267042323, 0, 0, 0, 0, 29536730874267042323, 29536730874267042323, 0, 0, 0, 0, 29536730874267042323, 29536730874267042323, 0, 0, 0, 0, 29536730874267042323, 29536730874267042323, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop8 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![29536730874285489067, 0, 0]
  | 1 => ![29536730874285489067, 0, 0]
  | 2 => ![29536730874285489067, 0, 0]
  | 3 => ![29536730874285489067, 0, 0]
  | 4 => ![29536730874285489067, 0, 0]
  | 5 => ![29536730874285489067, 0, 0]
  | 6 => ![29536730874285489067, 0, 0]
  | 7 => ![29536730874285489067, 0, 0]
  | 8 => ![29536730874285489067, 0, 0]
  | 9 => ![29536730874285489067, 0, 0]
  | 10 => ![29536730874285489067, 0, 0]
  | 11 => ![29536730874285489067, 0, 0]
  | 12 => ![29536730874285489067, 0, 0]
  | 13 => ![29536730874285489067, 0, 0]
  | 14 => ![29536730874285489067, 0, 0]
  | 15 => ![29536730874285489067, 0, 0]
  | 16 => ![29536730874285489067, 0, 0]
  | 17 => ![29536730874285489067, 0, 0]
  | 18 => ![29536730874285489067, 0, 0]
  | 19 => ![29536730874285489067, 0, 0]
  | 20 => ![29536730874285489067, 0, 0]
  | 21 => ![29536730874285489067, 0, 0]
  | 22 => ![29536730874285489067, 0, 0]
  | 23 => ![29536730874285489067, 0, 0]
  | 24 => ![29536730874285489067, 0, 0]
  | 25 => ![29536730874285489067, 0, 0]
  | 26 => ![29536730874285489067, 0, 0]
  | 27 => ![29536730874285489067, 0, 0]
  | 28 => ![29536730874285489067, 0, 0]
  | 29 => ![29536730874285489067, 0, 0]
  | 30 => ![29536730874285489067, 0, 0]
  | _ => ![29536730874285489067, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop8 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![29536730874359276044, 0, 0]
  | 1 => ![29536730874359276044, 0, 0]
  | 2 => ![29536730874359276044, 0, 0]
  | 3 => ![29536730874359276044, 0, 0]
  | 4 => ![29536730874359276044, 0, 0]
  | 5 => ![29536730874359276044, 0, 0]
  | 6 => ![29536730874359276044, 0, 0]
  | 7 => ![29536730874359276044, 0, 0]
  | 8 => ![29536730874359276044, 0, 0]
  | 9 => ![29536730874359276044, 0, 0]
  | 10 => ![29536730874359276044, 0, 0]
  | 11 => ![29536730874359276044, 0, 0]
  | 12 => ![29536730874359276044, 0, 0]
  | 13 => ![29536730874359276044, 0, 0]
  | 14 => ![29536730874359276044, 0, 0]
  | 15 => ![29536730874359276044, 0, 0]
  | 16 => ![29536730874359276044, 0, 0]
  | 17 => ![29536730874359276044, 0, 0]
  | 18 => ![29536730874359276044, 0, 0]
  | 19 => ![29536730874359276044, 0, 0]
  | 20 => ![29536730874359276044, 0, 0]
  | 21 => ![29536730874359276044, 0, 0]
  | 22 => ![29536730874359276044, 0, 0]
  | 23 => ![29536730874359276044, 0, 0]
  | 24 => ![29536730874359276044, 0, 0]
  | 25 => ![29536730874359276044, 0, 0]
  | 26 => ![29536730874359276044, 0, 0]
  | 27 => ![29536730874359276044, 0, 0]
  | 28 => ![29536730874359276044, 0, 0]
  | 29 => ![29536730874359276044, 0, 0]
  | 30 => ![29536730874359276044, 0, 0]
  | _ => ![29536730874359276044, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn8 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (1008357331547 / 1000000000000 : ℚ)
  | 1 => (504247995533 / 500000000000 : ℚ)
  | 2 => (1008636877379 / 1000000000000 : ℚ)
  | 3 => (126097502963 / 125000000000 : ℚ)
  | 4 => (1008925463663 / 1000000000000 : ℚ)
  | 5 => (1009073231287 / 1000000000000 : ℚ)
  | 6 => (1009223361017 / 1000000000000 : ℚ)
  | 7 => (126171985963 / 125000000000 : ℚ)
  | 8 => (1009530846611 / 1000000000000 : ℚ)
  | 9 => (201937654683 / 200000000000 : ℚ)
  | 10 => (1009848204207 / 1000000000000 : ℚ)
  | 11 => (1010010675493 / 1000000000000 : ℚ)
  | 12 => (505087862097 / 500000000000 : ℚ)
  | 13 => (1010343387647 / 1000000000000 : ℚ)
  | 14 => (202102740721 / 200000000000 : ℚ)
  | 15 => (505343355119 / 500000000000 : ℚ)
  | 16 => (1010862446131 / 1000000000000 : ℚ)
  | 17 => (252760237571 / 250000000000 : ℚ)
  | 18 => (1011222262113 / 1000000000000 : ℚ)
  | 19 => (202281284289 / 200000000000 : ℚ)
  | 20 => (505796734261 / 500000000000 : ℚ)
  | 21 => (252945860999 / 250000000000 : ℚ)
  | 22 => (15812131077 / 15625000000 : ℚ)
  | 23 => (1012172344787 / 1000000000000 : ℚ)
  | 24 => (253092838361 / 250000000000 : ℚ)
  | 25 => (126571682147 / 125000000000 : ℚ)
  | 26 => (1012778698657 / 1000000000000 : ℚ)
  | 27 => (202597424191 / 200000000000 : ℚ)
  | 28 => (253299691883 / 250000000000 : ℚ)
  | 29 => (1013413682239 / 1000000000000 : ℚ)
  | 30 => (1013631909307 / 1000000000000 : ℚ)
  | _ => (1013853493349 / 1000000000000 : ℚ)

def post8Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X8 SZ (gFloorZ X8 SZ) (postTop8 k)
def pre8Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X8 SZ vmax8Z (preTop8 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE8Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X8 SZ (post8Z k) && leTabZ 11 (post8Z k) vmax8Z &&
    preSolZ (famZ k) DZ 11 X8 SZ vmax8Z (pre8Z k) &&
    decide ((autoBoundZ (famZ k) DZ X8 SZ (post8Z k) : ℚ) ≤ eIn8 k * (X8.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X8 SZ (pre8Z k) : ℚ) ≤ (1013853493349 / 1000000000000 : ℚ) * (X8.M DZ * SZ : ℤ))

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

theorem solE8 : AutoSolE fam 11 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 vpreI8 vpostI8 vmax8 := by
  rw [xgQ8]; exact (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).1

theorem heEall8 : ∀ k, autoBound (fam k) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpreI8 k) ≤ (1013853493349 / 1000000000000 : ℝ) := by
  rw [xgQ8]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.2 k).trans_eq (by push_cast; ring)

theorem heIn8_0 : autoBound (fam 0) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 0) ≤ (1008357331547 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 0; rw [show eIn8 0 = (1008357331547 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_1 : autoBound (fam 1) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 1) ≤ (504247995533 / 500000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 1; rw [show eIn8 1 = (504247995533 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_2 : autoBound (fam 2) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 2) ≤ (1008636877379 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 2; rw [show eIn8 2 = (1008636877379 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_3 : autoBound (fam 3) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 3) ≤ (126097502963 / 125000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 3; rw [show eIn8 3 = (126097502963 / 125000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_4 : autoBound (fam 4) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 4) ≤ (1008925463663 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 4; rw [show eIn8 4 = (1008925463663 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_5 : autoBound (fam 5) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 5) ≤ (1009073231287 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 5; rw [show eIn8 5 = (1009073231287 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_6 : autoBound (fam 6) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 6) ≤ (1009223361017 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 6; rw [show eIn8 6 = (1009223361017 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_7 : autoBound (fam 7) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 7) ≤ (126171985963 / 125000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 7; rw [show eIn8 7 = (126171985963 / 125000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_8 : autoBound (fam 8) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 8) ≤ (1009530846611 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 8; rw [show eIn8 8 = (1009530846611 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_9 : autoBound (fam 9) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 9) ≤ (201937654683 / 200000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 9; rw [show eIn8 9 = (201937654683 / 200000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_10 : autoBound (fam 10) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 10) ≤ (1009848204207 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 10; rw [show eIn8 10 = (1009848204207 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_11 : autoBound (fam 11) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 11) ≤ (1010010675493 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 11; rw [show eIn8 11 = (1010010675493 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_12 : autoBound (fam 12) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 12) ≤ (505087862097 / 500000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 12; rw [show eIn8 12 = (505087862097 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_13 : autoBound (fam 13) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 13) ≤ (1010343387647 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 13; rw [show eIn8 13 = (1010343387647 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_14 : autoBound (fam 14) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 14) ≤ (202102740721 / 200000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 14; rw [show eIn8 14 = (202102740721 / 200000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_15 : autoBound (fam 15) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 15) ≤ (505343355119 / 500000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 15; rw [show eIn8 15 = (505343355119 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_16 : autoBound (fam 16) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 16) ≤ (1010862446131 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 16; rw [show eIn8 16 = (1010862446131 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_17 : autoBound (fam 17) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 17) ≤ (252760237571 / 250000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 17; rw [show eIn8 17 = (252760237571 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_18 : autoBound (fam 18) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 18) ≤ (1011222262113 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 18; rw [show eIn8 18 = (1011222262113 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_19 : autoBound (fam 19) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 19) ≤ (202281284289 / 200000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 19; rw [show eIn8 19 = (202281284289 / 200000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_20 : autoBound (fam 20) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 20) ≤ (505796734261 / 500000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 20; rw [show eIn8 20 = (505796734261 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_21 : autoBound (fam 21) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 21) ≤ (252945860999 / 250000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 21; rw [show eIn8 21 = (252945860999 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_22 : autoBound (fam 22) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 22) ≤ (15812131077 / 15625000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 22; rw [show eIn8 22 = (15812131077 / 15625000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_23 : autoBound (fam 23) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 23) ≤ (1012172344787 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 23; rw [show eIn8 23 = (1012172344787 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_24 : autoBound (fam 24) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 24) ≤ (253092838361 / 250000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 24; rw [show eIn8 24 = (253092838361 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_25 : autoBound (fam 25) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 25) ≤ (126571682147 / 125000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 25; rw [show eIn8 25 = (126571682147 / 125000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_26 : autoBound (fam 26) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 26) ≤ (1012778698657 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 26; rw [show eIn8 26 = (1012778698657 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_27 : autoBound (fam 27) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 27) ≤ (202597424191 / 200000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 27; rw [show eIn8 27 = (202597424191 / 200000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_28 : autoBound (fam 28) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 28) ≤ (253299691883 / 250000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 28; rw [show eIn8 28 = (253299691883 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_29 : autoBound (fam 29) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 29) ≤ (1013413682239 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 29; rw [show eIn8 29 = (1013413682239 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_30 : autoBound (fam 30) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 30) ≤ (1013631909307 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 30; rw [show eIn8 30 = (1013631909307 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn8_31 : autoBound (fam 31) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 8).2.2 (vpostI8 31) ≤ (1013853493349 / 1000000000000 : ℝ) := by
  rw [xgQ8]; have h := (oneSwitchZ_sound famR famA DZ_pos X8R SZ_pos chkE8).2.1 31; rw [show eIn8 31 = (1013853493349 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

end Cryptarchia.Prob.Certs.E20D11M2
