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

/-! # E20D11M2: tables for index 14 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ14 : xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14 = castX (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 14) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 14

/-- Phase expectation 14 over the integers. -/
def X14 : PhZ := ⟨31226787, 50000000, 1, 1,
  fun a b u => [31226787, 0, 50000000, 0, 31226787, 0, 50000000, 0, 31226787, 0, 50000000, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  31226787⟩

theorem X14R : X14.Rep (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 14).1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 14).2.1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 14).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax14Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874285489067, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0, 29536730874267042323, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop14 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![0, 0, 0]
  | 1 => ![0, 0, 0]
  | 2 => ![0, 0, 0]
  | 3 => ![0, 0, 0]
  | 4 => ![0, 0, 0]
  | 5 => ![0, 0, 0]
  | 6 => ![0, 0, 0]
  | 7 => ![0, 0, 0]
  | 8 => ![0, 0, 0]
  | 9 => ![0, 0, 0]
  | 10 => ![0, 0, 0]
  | 11 => ![0, 0, 0]
  | 12 => ![0, 0, 0]
  | 13 => ![0, 0, 0]
  | 14 => ![0, 0, 0]
  | 15 => ![0, 0, 0]
  | 16 => ![0, 0, 0]
  | 17 => ![0, 0, 0]
  | 18 => ![0, 0, 0]
  | 19 => ![0, 0, 0]
  | 20 => ![0, 0, 0]
  | 21 => ![0, 0, 0]
  | 22 => ![0, 0, 0]
  | 23 => ![0, 0, 0]
  | 24 => ![0, 0, 0]
  | 25 => ![0, 0, 0]
  | 26 => ![0, 0, 0]
  | 27 => ![0, 0, 0]
  | 28 => ![0, 0, 0]
  | 29 => ![0, 0, 0]
  | 30 => ![0, 0, 0]
  | _ => ![0, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop14 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![0, 0, 0]
  | 1 => ![0, 0, 0]
  | 2 => ![0, 0, 0]
  | 3 => ![0, 0, 0]
  | 4 => ![0, 0, 0]
  | 5 => ![0, 0, 0]
  | 6 => ![0, 0, 0]
  | 7 => ![0, 0, 0]
  | 8 => ![0, 0, 0]
  | 9 => ![0, 0, 0]
  | 10 => ![0, 0, 0]
  | 11 => ![0, 0, 0]
  | 12 => ![0, 0, 0]
  | 13 => ![0, 0, 0]
  | 14 => ![0, 0, 0]
  | 15 => ![0, 0, 0]
  | 16 => ![0, 0, 0]
  | 17 => ![0, 0, 0]
  | 18 => ![0, 0, 0]
  | 19 => ![0, 0, 0]
  | 20 => ![0, 0, 0]
  | 21 => ![0, 0, 0]
  | 22 => ![0, 0, 0]
  | 23 => ![0, 0, 0]
  | 24 => ![0, 0, 0]
  | 25 => ![0, 0, 0]
  | 26 => ![0, 0, 0]
  | 27 => ![0, 0, 0]
  | 28 => ![0, 0, 0]
  | 29 => ![0, 0, 0]
  | 30 => ![0, 0, 0]
  | _ => ![0, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn14 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (1012225591689 / 1000000000000 : ℚ)
  | 1 => (1012431122607 / 1000000000000 : ℚ)
  | 2 => (253160012087 / 250000000000 : ℚ)
  | 3 => (506426211461 / 500000000000 : ℚ)
  | 4 => (253267075281 / 250000000000 : ℚ)
  | 5 => (20265754771 / 20000000000 : ℚ)
  | 6 => (1013510791599 / 1000000000000 : ℚ)
  | 7 => (1013737517489 / 1000000000000 : ℚ)
  | 8 => (1013967974261 / 1000000000000 : ℚ)
  | 9 => (253550555197 / 250000000000 : ℚ)
  | 10 => (101444031679 / 100000000000 : ℚ)
  | 11 => (253670580709 / 250000000000 : ℚ)
  | 12 => (1014928300357 / 1000000000000 : ℚ)
  | 13 => (507589155827 / 500000000000 : ℚ)
  | 14 => (507716209953 / 500000000000 : ℚ)
  | 15 => (507845344591 / 500000000000 : ℚ)
  | 16 => (1015953184447 / 1000000000000 : ℚ)
  | 17 => (1016219971573 / 1000000000000 : ℚ)
  | 18 => (31765347417 / 31250000000 : ℚ)
  | 19 => (101676668947 / 100000000000 : ℚ)
  | 20 => (1017046756593 / 1000000000000 : ℚ)
  | 21 => (203466277659 / 200000000000 : ℚ)
  | 22 => (101762065511 / 100000000000 : ℚ)
  | 23 => (63619664283 / 62500000000 : ℚ)
  | 24 => (509106690503 / 500000000000 : ℚ)
  | 25 => (127314623247 / 125000000000 : ℚ)
  | 26 => (509412758927 / 500000000000 : ℚ)
  | 27 => (509569526023 / 500000000000 : ℚ)
  | 28 => (1019457664959 / 1000000000000 : ℚ)
  | 29 => (203956286801 / 200000000000 : ℚ)
  | 30 => (1020110437613 / 1000000000000 : ℚ)
  | _ => (1020444755233 / 1000000000000 : ℚ)

def post14Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X14 SZ (gFloorZ X14 SZ) (postTop14 k)
def pre14Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X14 SZ vmax14Z (preTop14 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE14Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X14 SZ (post14Z k) && leTabZ 11 (post14Z k) vmax14Z &&
    preSolZ (famZ k) DZ 11 X14 SZ vmax14Z (pre14Z k) &&
    decide ((autoBoundZ (famZ k) DZ X14 SZ (post14Z k) : ℚ) ≤ eIn14 k * (X14.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X14 SZ (pre14Z k) : ℚ) ≤ (510222377617 / 500000000000 : ℚ) * (X14.M DZ * SZ : ℤ))

theorem chkE14_0 : chkE14Q 0 = true := by decide +kernel
theorem chkE14_1 : chkE14Q 1 = true := by decide +kernel
theorem chkE14_2 : chkE14Q 2 = true := by decide +kernel
theorem chkE14_3 : chkE14Q 3 = true := by decide +kernel
theorem chkE14_4 : chkE14Q 4 = true := by decide +kernel
theorem chkE14_5 : chkE14Q 5 = true := by decide +kernel
theorem chkE14_6 : chkE14Q 6 = true := by decide +kernel
theorem chkE14_7 : chkE14Q 7 = true := by decide +kernel
theorem chkE14_8 : chkE14Q 8 = true := by decide +kernel
theorem chkE14_9 : chkE14Q 9 = true := by decide +kernel
theorem chkE14_10 : chkE14Q 10 = true := by decide +kernel
theorem chkE14_11 : chkE14Q 11 = true := by decide +kernel
theorem chkE14_12 : chkE14Q 12 = true := by decide +kernel
theorem chkE14_13 : chkE14Q 13 = true := by decide +kernel
theorem chkE14_14 : chkE14Q 14 = true := by decide +kernel
theorem chkE14_15 : chkE14Q 15 = true := by decide +kernel
theorem chkE14_16 : chkE14Q 16 = true := by decide +kernel
theorem chkE14_17 : chkE14Q 17 = true := by decide +kernel
theorem chkE14_18 : chkE14Q 18 = true := by decide +kernel
theorem chkE14_19 : chkE14Q 19 = true := by decide +kernel
theorem chkE14_20 : chkE14Q 20 = true := by decide +kernel
theorem chkE14_21 : chkE14Q 21 = true := by decide +kernel
theorem chkE14_22 : chkE14Q 22 = true := by decide +kernel
theorem chkE14_23 : chkE14Q 23 = true := by decide +kernel
theorem chkE14_24 : chkE14Q 24 = true := by decide +kernel
theorem chkE14_25 : chkE14Q 25 = true := by decide +kernel
theorem chkE14_26 : chkE14Q 26 = true := by decide +kernel
theorem chkE14_27 : chkE14Q 27 = true := by decide +kernel
theorem chkE14_28 : chkE14Q 28 = true := by decide +kernel
theorem chkE14_29 : chkE14Q 29 = true := by decide +kernel
theorem chkE14_30 : chkE14Q 30 = true := by decide +kernel
theorem chkE14_31 : chkE14Q 31 = true := by decide +kernel

theorem chkE14 : ∀ k, chkE14Q k = true := fun k => by
  fin_cases k; exacts [chkE14_0, chkE14_1, chkE14_2, chkE14_3, chkE14_4, chkE14_5, chkE14_6, chkE14_7, chkE14_8, chkE14_9, chkE14_10, chkE14_11, chkE14_12, chkE14_13, chkE14_14, chkE14_15, chkE14_16, chkE14_17, chkE14_18, chkE14_19, chkE14_20, chkE14_21, chkE14_22, chkE14_23, chkE14_24, chkE14_25, chkE14_26, chkE14_27, chkE14_28, chkE14_29, chkE14_30, chkE14_31]

noncomputable def vmax14 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax14Z)
noncomputable def vpreI14 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre14Z k))
noncomputable def vpostI14 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post14Z k))

theorem solE14 : AutoSolE fam 11 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 vpreI14 vpostI14 vmax14 := by
  rw [xgQ14]; exact (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).1

theorem heEall14 : ∀ k, autoBound (fam k) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpreI14 k) ≤ (510222377617 / 500000000000 : ℝ) := by
  rw [xgQ14]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.2 k).trans_eq (by push_cast; ring)

theorem heIn14_0 : autoBound (fam 0) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 0) ≤ (1012225591689 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 0; rw [show eIn14 0 = (1012225591689 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_1 : autoBound (fam 1) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 1) ≤ (1012431122607 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 1; rw [show eIn14 1 = (1012431122607 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_2 : autoBound (fam 2) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 2) ≤ (253160012087 / 250000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 2; rw [show eIn14 2 = (253160012087 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_3 : autoBound (fam 3) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 3) ≤ (506426211461 / 500000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 3; rw [show eIn14 3 = (506426211461 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_4 : autoBound (fam 4) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 4) ≤ (253267075281 / 250000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 4; rw [show eIn14 4 = (253267075281 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_5 : autoBound (fam 5) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 5) ≤ (20265754771 / 20000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 5; rw [show eIn14 5 = (20265754771 / 20000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_6 : autoBound (fam 6) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 6) ≤ (1013510791599 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 6; rw [show eIn14 6 = (1013510791599 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_7 : autoBound (fam 7) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 7) ≤ (1013737517489 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 7; rw [show eIn14 7 = (1013737517489 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_8 : autoBound (fam 8) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 8) ≤ (1013967974261 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 8; rw [show eIn14 8 = (1013967974261 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_9 : autoBound (fam 9) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 9) ≤ (253550555197 / 250000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 9; rw [show eIn14 9 = (253550555197 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_10 : autoBound (fam 10) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 10) ≤ (101444031679 / 100000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 10; rw [show eIn14 10 = (101444031679 / 100000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_11 : autoBound (fam 11) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 11) ≤ (253670580709 / 250000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 11; rw [show eIn14 11 = (253670580709 / 250000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_12 : autoBound (fam 12) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 12) ≤ (1014928300357 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 12; rw [show eIn14 12 = (1014928300357 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_13 : autoBound (fam 13) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 13) ≤ (507589155827 / 500000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 13; rw [show eIn14 13 = (507589155827 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_14 : autoBound (fam 14) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 14) ≤ (507716209953 / 500000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 14; rw [show eIn14 14 = (507716209953 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_15 : autoBound (fam 15) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 15) ≤ (507845344591 / 500000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 15; rw [show eIn14 15 = (507845344591 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_16 : autoBound (fam 16) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 16) ≤ (1015953184447 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 16; rw [show eIn14 16 = (1015953184447 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_17 : autoBound (fam 17) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 17) ≤ (1016219971573 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 17; rw [show eIn14 17 = (1016219971573 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_18 : autoBound (fam 18) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 18) ≤ (31765347417 / 31250000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 18; rw [show eIn14 18 = (31765347417 / 31250000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_19 : autoBound (fam 19) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 19) ≤ (101676668947 / 100000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 19; rw [show eIn14 19 = (101676668947 / 100000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_20 : autoBound (fam 20) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 20) ≤ (1017046756593 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 20; rw [show eIn14 20 = (1017046756593 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_21 : autoBound (fam 21) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 21) ≤ (203466277659 / 200000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 21; rw [show eIn14 21 = (203466277659 / 200000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_22 : autoBound (fam 22) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 22) ≤ (101762065511 / 100000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 22; rw [show eIn14 22 = (101762065511 / 100000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_23 : autoBound (fam 23) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 23) ≤ (63619664283 / 62500000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 23; rw [show eIn14 23 = (63619664283 / 62500000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_24 : autoBound (fam 24) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 24) ≤ (509106690503 / 500000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 24; rw [show eIn14 24 = (509106690503 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_25 : autoBound (fam 25) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 25) ≤ (127314623247 / 125000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 25; rw [show eIn14 25 = (127314623247 / 125000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_26 : autoBound (fam 26) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 26) ≤ (509412758927 / 500000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 26; rw [show eIn14 26 = (509412758927 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_27 : autoBound (fam 27) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 27) ≤ (509569526023 / 500000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 27; rw [show eIn14 27 = (509569526023 / 500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_28 : autoBound (fam 28) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 28) ≤ (1019457664959 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 28; rw [show eIn14 28 = (1019457664959 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_29 : autoBound (fam 29) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 29) ≤ (203956286801 / 200000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 29; rw [show eIn14 29 = (203956286801 / 200000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_30 : autoBound (fam 30) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 30) ≤ (1020110437613 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 30; rw [show eIn14 30 = (1020110437613 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn14_31 : autoBound (fam 31) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 14).2.2 (vpostI14 31) ≤ (1020444755233 / 1000000000000 : ℝ) := by
  rw [xgQ14]; have h := (oneSwitchZ_sound famR famA DZ_pos X14R SZ_pos chkE14).2.1 31; rw [show eIn14 31 = (1020444755233 / 1000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

end Cryptarchia.Prob.Certs.E20D11M2
