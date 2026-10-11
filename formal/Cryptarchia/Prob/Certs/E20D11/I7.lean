module

public import Cryptarchia.Prob.Certs.E20D11.Fam
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

/-! # E20D11: tables for index 7 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ7 : xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7 = castX (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 7) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 7

/-- Phase expectation 7 over the integers. -/
def X7 : PhZ := ⟨31226787, 50000000, 1, 1,
  fun a b u => [17553, 17553, 10000, 10000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  17553⟩

theorem X7R : X7.Rep (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 7).1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 7).2.1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 7).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax7Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [10509168845068271943, 10509168845068271943, 0, 0, 0, 0, 10509168845066427268, 10509168845066427268, 0, 0, 0, 0, 10509168845066427268, 10509168845066427268, 0, 0, 0, 0, 10509168845064582594, 10509168845064582594, 0, 0, 0, 0, 10509168845064582594, 10509168845064582594, 0, 0, 0, 0, 10509168845064582594, 10509168845064582594, 0, 0, 0, 0, 10509168845062737919, 10509168845062737919, 0, 0, 0, 0, 10509168845062737919, 10509168845062737919, 0, 0, 0, 0, 10509168845060893245, 10509168845060893245, 0, 0, 0, 0, 10509168845060893245, 10509168845060893245, 0, 0, 0, 0, 10509168845059048571, 10509168845059048571, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop7 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![10509168845068271943, 0, 0]
  | 1 => ![10509168845068271943, 0, 0]
  | 2 => ![10509168845068271943, 0, 0]
  | 3 => ![10509168845068271943, 0, 0]
  | 4 => ![10509168845068271943, 0, 0]
  | 5 => ![10509168845068271943, 0, 0]
  | 6 => ![10509168845068271943, 0, 0]
  | 7 => ![10509168845068271943, 0, 0]
  | 8 => ![10509168845068271943, 0, 0]
  | 9 => ![10509168845068271943, 0, 0]
  | 10 => ![10509168845068271943, 0, 0]
  | 11 => ![10509168845068271943, 0, 0]
  | 12 => ![10509168845068271943, 0, 0]
  | 13 => ![10509168845068271943, 0, 0]
  | 14 => ![10509168845068271943, 0, 0]
  | 15 => ![10509168845068271943, 0, 0]
  | 16 => ![10509168845068271943, 0, 0]
  | 17 => ![10509168845068271943, 0, 0]
  | 18 => ![10509168845068271943, 0, 0]
  | 19 => ![10509168845068271943, 0, 0]
  | 20 => ![10509168845068271943, 0, 0]
  | 21 => ![10509168845068271943, 0, 0]
  | 22 => ![10509168845068271943, 0, 0]
  | 23 => ![10509168845068271943, 0, 0]
  | 24 => ![10509168845068271943, 0, 0]
  | 25 => ![10509168845068271943, 0, 0]
  | 26 => ![10509168845068271943, 0, 0]
  | 27 => ![10509168845068271943, 0, 0]
  | 28 => ![10509168845068271943, 0, 0]
  | 29 => ![10509168845068271943, 0, 0]
  | 30 => ![10509168845068271943, 0, 0]
  | _ => ![10509168845068271943, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop7 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![10509168845090408036, 0, 0]
  | 1 => ![10509168845090408036, 0, 0]
  | 2 => ![10509168845090408036, 0, 0]
  | 3 => ![10509168845090408036, 0, 0]
  | 4 => ![10509168845090408036, 0, 0]
  | 5 => ![10509168845090408036, 0, 0]
  | 6 => ![10509168845090408036, 0, 0]
  | 7 => ![10509168845090408036, 0, 0]
  | 8 => ![10509168845090408036, 0, 0]
  | 9 => ![10509168845090408036, 0, 0]
  | 10 => ![10509168845090408036, 0, 0]
  | 11 => ![10509168845090408036, 0, 0]
  | 12 => ![10509168845090408036, 0, 0]
  | 13 => ![10509168845090408036, 0, 0]
  | 14 => ![10509168845090408036, 0, 0]
  | 15 => ![10509168845090408036, 0, 0]
  | 16 => ![10509168845090408036, 0, 0]
  | 17 => ![10509168845090408036, 0, 0]
  | 18 => ![10509168845090408036, 0, 0]
  | 19 => ![10509168845090408036, 0, 0]
  | 20 => ![10509168845090408036, 0, 0]
  | 21 => ![10509168845090408036, 0, 0]
  | 22 => ![10509168845090408036, 0, 0]
  | 23 => ![10509168845090408036, 0, 0]
  | 24 => ![10509168845090408036, 0, 0]
  | 25 => ![10509168845090408036, 0, 0]
  | 26 => ![10509168845090408036, 0, 0]
  | 27 => ![10509168845090408036, 0, 0]
  | 28 => ![10509168845090408036, 0, 0]
  | 29 => ![10509168845090408036, 0, 0]
  | 30 => ![10509168845090408036, 0, 0]
  | _ => ![10509168845090408036, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn7 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (4918610260267 / 5000000000000 : ℚ)
  | 1 => (491723749403 / 500000000000 : ℚ)
  | 2 => (614480239953 / 625000000000 : ℚ)
  | 3 => (9828846341257 / 10000000000000 : ℚ)
  | 4 => (982596175041 / 1000000000000 : ℚ)
  | 5 => (1964605862413 / 2000000000000 : ℚ)
  | 6 => (1964009652099 / 2000000000000 : ℚ)
  | 7 => (4908508909383 / 5000000000000 : ℚ)
  | 8 => (9813937198609 / 10000000000000 : ℚ)
  | 9 => (4905402800151 / 5000000000000 : ℚ)
  | 10 => (9807622212547 / 10000000000000 : ℚ)
  | 11 => (9804386212347 / 10000000000000 : ℚ)
  | 12 => (1225137095611 / 1250000000000 : ℚ)
  | 13 => (9797753023419 / 10000000000000 : ℚ)
  | 14 => (979435412913 / 1000000000000 : ℚ)
  | 15 => (9790899211039 / 10000000000000 : ℚ)
  | 16 => (2446846846469 / 2500000000000 : ℚ)
  | 17 => (2445954439491 / 2500000000000 : ℚ)
  | 18 => (9780189419109 / 10000000000000 : ℚ)
  | 19 => (9776501448489 / 10000000000000 : ℚ)
  | 20 => (1954550582509 / 2000000000000 : ℚ)
  | 21 => (9768942864871 / 10000000000000 : ℚ)
  | 22 => (9765070346111 / 10000000000000 : ℚ)
  | 23 => (610070898991 / 625000000000 : ℚ)
  | 24 => (2439283498137 / 2500000000000 : ℚ)
  | 25 => (152391690209 / 156250000000 : ℚ)
  | 26 => (9748935914189 / 10000000000000 : ℚ)
  | 27 => (48723680947 / 50000000000 : ℚ)
  | 28 => (9740467959907 / 10000000000000 : ℚ)
  | 29 => (9736130173 / 10000000000 : ℚ)
  | 30 => (9731721762293 / 10000000000000 : ℚ)
  | _ => (9727241647643 / 10000000000000 : ℚ)

def post7Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X7 SZ (gFloorZ X7 SZ) (postTop7 k)
def pre7Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X7 SZ vmax7Z (preTop7 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE7Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X7 SZ (post7Z k) && leTabZ 11 (post7Z k) vmax7Z &&
    preSolZ (famZ k) DZ 11 X7 SZ vmax7Z (pre7Z k) &&
    decide ((autoBoundZ (famZ k) DZ X7 SZ (post7Z k) : ℚ) ≤ eIn7 k * (X7.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X7 SZ (pre7Z k) : ℚ) ≤ (4918610260267 / 5000000000000 : ℚ) * (X7.M DZ * SZ : ℤ))

theorem chkE7_0 : chkE7Q 0 = true := by decide +kernel
theorem chkE7_1 : chkE7Q 1 = true := by decide +kernel
theorem chkE7_2 : chkE7Q 2 = true := by decide +kernel
theorem chkE7_3 : chkE7Q 3 = true := by decide +kernel
theorem chkE7_4 : chkE7Q 4 = true := by decide +kernel
theorem chkE7_5 : chkE7Q 5 = true := by decide +kernel
theorem chkE7_6 : chkE7Q 6 = true := by decide +kernel
theorem chkE7_7 : chkE7Q 7 = true := by decide +kernel
theorem chkE7_8 : chkE7Q 8 = true := by decide +kernel
theorem chkE7_9 : chkE7Q 9 = true := by decide +kernel
theorem chkE7_10 : chkE7Q 10 = true := by decide +kernel
theorem chkE7_11 : chkE7Q 11 = true := by decide +kernel
theorem chkE7_12 : chkE7Q 12 = true := by decide +kernel
theorem chkE7_13 : chkE7Q 13 = true := by decide +kernel
theorem chkE7_14 : chkE7Q 14 = true := by decide +kernel
theorem chkE7_15 : chkE7Q 15 = true := by decide +kernel
theorem chkE7_16 : chkE7Q 16 = true := by decide +kernel
theorem chkE7_17 : chkE7Q 17 = true := by decide +kernel
theorem chkE7_18 : chkE7Q 18 = true := by decide +kernel
theorem chkE7_19 : chkE7Q 19 = true := by decide +kernel
theorem chkE7_20 : chkE7Q 20 = true := by decide +kernel
theorem chkE7_21 : chkE7Q 21 = true := by decide +kernel
theorem chkE7_22 : chkE7Q 22 = true := by decide +kernel
theorem chkE7_23 : chkE7Q 23 = true := by decide +kernel
theorem chkE7_24 : chkE7Q 24 = true := by decide +kernel
theorem chkE7_25 : chkE7Q 25 = true := by decide +kernel
theorem chkE7_26 : chkE7Q 26 = true := by decide +kernel
theorem chkE7_27 : chkE7Q 27 = true := by decide +kernel
theorem chkE7_28 : chkE7Q 28 = true := by decide +kernel
theorem chkE7_29 : chkE7Q 29 = true := by decide +kernel
theorem chkE7_30 : chkE7Q 30 = true := by decide +kernel
theorem chkE7_31 : chkE7Q 31 = true := by decide +kernel

theorem chkE7 : ∀ k, chkE7Q k = true := fun k => by
  fin_cases k; exacts [chkE7_0, chkE7_1, chkE7_2, chkE7_3, chkE7_4, chkE7_5, chkE7_6, chkE7_7, chkE7_8, chkE7_9, chkE7_10, chkE7_11, chkE7_12, chkE7_13, chkE7_14, chkE7_15, chkE7_16, chkE7_17, chkE7_18, chkE7_19, chkE7_20, chkE7_21, chkE7_22, chkE7_23, chkE7_24, chkE7_25, chkE7_26, chkE7_27, chkE7_28, chkE7_29, chkE7_30, chkE7_31]

noncomputable def vmax7 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax7Z)
noncomputable def vpreI7 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre7Z k))
noncomputable def vpostI7 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post7Z k))

theorem solE7 : AutoSolE fam 11 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 vpreI7 vpostI7 vmax7 := by
  rw [xgQ7]; exact (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).1

theorem heEall7 : ∀ k, autoBound (fam k) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpreI7 k) ≤ (4918610260267 / 5000000000000 : ℝ) := by
  rw [xgQ7]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.2 k).trans_eq (by push_cast; ring)

theorem heIn7_0 : autoBound (fam 0) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 0) ≤ (4918610260267 / 5000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 0; rw [show eIn7 0 = (4918610260267 / 5000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_1 : autoBound (fam 1) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 1) ≤ (491723749403 / 500000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 1; rw [show eIn7 1 = (491723749403 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_2 : autoBound (fam 2) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 2) ≤ (614480239953 / 625000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 2; rw [show eIn7 2 = (614480239953 / 625000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_3 : autoBound (fam 3) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 3) ≤ (9828846341257 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 3; rw [show eIn7 3 = (9828846341257 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_4 : autoBound (fam 4) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 4) ≤ (982596175041 / 1000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 4; rw [show eIn7 4 = (982596175041 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_5 : autoBound (fam 5) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 5) ≤ (1964605862413 / 2000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 5; rw [show eIn7 5 = (1964605862413 / 2000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_6 : autoBound (fam 6) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 6) ≤ (1964009652099 / 2000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 6; rw [show eIn7 6 = (1964009652099 / 2000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_7 : autoBound (fam 7) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 7) ≤ (4908508909383 / 5000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 7; rw [show eIn7 7 = (4908508909383 / 5000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_8 : autoBound (fam 8) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 8) ≤ (9813937198609 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 8; rw [show eIn7 8 = (9813937198609 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_9 : autoBound (fam 9) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 9) ≤ (4905402800151 / 5000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 9; rw [show eIn7 9 = (4905402800151 / 5000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_10 : autoBound (fam 10) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 10) ≤ (9807622212547 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 10; rw [show eIn7 10 = (9807622212547 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_11 : autoBound (fam 11) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 11) ≤ (9804386212347 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 11; rw [show eIn7 11 = (9804386212347 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_12 : autoBound (fam 12) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 12) ≤ (1225137095611 / 1250000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 12; rw [show eIn7 12 = (1225137095611 / 1250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_13 : autoBound (fam 13) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 13) ≤ (9797753023419 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 13; rw [show eIn7 13 = (9797753023419 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_14 : autoBound (fam 14) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 14) ≤ (979435412913 / 1000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 14; rw [show eIn7 14 = (979435412913 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_15 : autoBound (fam 15) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 15) ≤ (9790899211039 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 15; rw [show eIn7 15 = (9790899211039 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_16 : autoBound (fam 16) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 16) ≤ (2446846846469 / 2500000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 16; rw [show eIn7 16 = (2446846846469 / 2500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_17 : autoBound (fam 17) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 17) ≤ (2445954439491 / 2500000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 17; rw [show eIn7 17 = (2445954439491 / 2500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_18 : autoBound (fam 18) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 18) ≤ (9780189419109 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 18; rw [show eIn7 18 = (9780189419109 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_19 : autoBound (fam 19) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 19) ≤ (9776501448489 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 19; rw [show eIn7 19 = (9776501448489 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_20 : autoBound (fam 20) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 20) ≤ (1954550582509 / 2000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 20; rw [show eIn7 20 = (1954550582509 / 2000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_21 : autoBound (fam 21) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 21) ≤ (9768942864871 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 21; rw [show eIn7 21 = (9768942864871 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_22 : autoBound (fam 22) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 22) ≤ (9765070346111 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 22; rw [show eIn7 22 = (9765070346111 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_23 : autoBound (fam 23) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 23) ≤ (610070898991 / 625000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 23; rw [show eIn7 23 = (610070898991 / 625000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_24 : autoBound (fam 24) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 24) ≤ (2439283498137 / 2500000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 24; rw [show eIn7 24 = (2439283498137 / 2500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_25 : autoBound (fam 25) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 25) ≤ (152391690209 / 156250000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 25; rw [show eIn7 25 = (152391690209 / 156250000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_26 : autoBound (fam 26) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 26) ≤ (9748935914189 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 26; rw [show eIn7 26 = (9748935914189 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_27 : autoBound (fam 27) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 27) ≤ (48723680947 / 50000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 27; rw [show eIn7 27 = (48723680947 / 50000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_28 : autoBound (fam 28) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 28) ≤ (9740467959907 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 28; rw [show eIn7 28 = (9740467959907 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_29 : autoBound (fam 29) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 29) ≤ (9736130173 / 10000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 29; rw [show eIn7 29 = (9736130173 / 10000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_30 : autoBound (fam 30) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 30) ≤ (9731721762293 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 30; rw [show eIn7 30 = (9731721762293 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn7_31 : autoBound (fam 31) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 31) ≤ (9727241647643 / 10000000000000 : ℝ) := by
  rw [xgQ7]; have h := (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1 31; rw [show eIn7 31 = (9727241647643 / 10000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

end Cryptarchia.Prob.Certs.E20D11
