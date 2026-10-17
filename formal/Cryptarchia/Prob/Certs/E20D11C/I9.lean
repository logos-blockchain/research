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

/-! # E20D11C: tables for index 9 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ9 : xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9 = castX (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 9) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 9

/-- Phase expectation 9 over the integers. -/
def X9 : PhZ := ⟨17849851, 20000000, 1, 1,
  fun a b u => [19474187441, 19474187441, 21820000000, 40000000000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  19474187441⟩

theorem X9R : X9.Rep (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 9).1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 9).2.1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 9).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax9Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [24895659782272643140, 37889630322124475947, 0, 0, 0, 0, 24606009627781554770, 37889630322087582459, 0, 0, 0, 0, 24300392717163871895, 37889630322069135715, 0, 0, 0, 0, 23977928894426351697, 37889630322032242227, 0, 0, 0, 0, 23637689485724251939, 37889630321995348739, 0, 0, 0, 0, 23278694624657227252, 37889630321976901995, 0, 0, 0, 0, 22899910430433994692, 37889630321940008506, 0, 0, 0, 0, 22500246030309585827, 37889630321903115018, 0, 0, 0, 0, 22078550417957257031, 37889630321884668274, 0, 0, 0, 0, 21633609138699259902, 37889630321847774786, 0, 0, 0, 0, 21164140791875037679, 37889630321810881298, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop9 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![37889630322124475947, 0, 0]
  | 1 => ![37889630322124475947, 0, 0]
  | 2 => ![37889630322124475947, 0, 0]
  | 3 => ![37889630322124475947, 0, 0]
  | 4 => ![37889630322124475947, 0, 0]
  | 5 => ![37889630322124475947, 0, 0]
  | 6 => ![37889630322124475947, 0, 0]
  | 7 => ![37889630322124475947, 0, 0]
  | 8 => ![37889630322124475947, 0, 0]
  | 9 => ![37889630322124475947, 0, 0]
  | 10 => ![37889630322124475947, 0, 0]
  | 11 => ![37889630322124475947, 0, 0]
  | 12 => ![37889630322124475947, 0, 0]
  | 13 => ![37889630322124475947, 0, 0]
  | 14 => ![37889630322124475947, 0, 0]
  | 15 => ![37889630322124475947, 0, 0]
  | 16 => ![37889630322124475947, 0, 0]
  | 17 => ![37889630322124475947, 0, 0]
  | 18 => ![37889630322124475947, 0, 0]
  | 19 => ![37889630322124475947, 0, 0]
  | 20 => ![37889630322124475947, 0, 0]
  | 21 => ![37889630322124475947, 0, 0]
  | 22 => ![37889630322124475947, 0, 0]
  | 23 => ![37889630322124475947, 0, 0]
  | 24 => ![37889630322124475947, 0, 0]
  | 25 => ![37889630322124475947, 0, 0]
  | 26 => ![37889630322124475947, 0, 0]
  | 27 => ![37889630322124475947, 0, 0]
  | 28 => ![37889630322124475947, 0, 0]
  | 29 => ![37889630322124475947, 0, 0]
  | 30 => ![37889630322124475947, 0, 0]
  | _ => ![37889630322124475947, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop9 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![37889630322216709668, 0, 0]
  | 1 => ![37889630322216709668, 0, 0]
  | 2 => ![37889630322216709668, 0, 0]
  | 3 => ![37889630322216709668, 0, 0]
  | 4 => ![37889630322216709668, 0, 0]
  | 5 => ![37889630322216709668, 0, 0]
  | 6 => ![37889630322216709668, 0, 0]
  | 7 => ![37889630322216709668, 0, 0]
  | 8 => ![37889630322216709668, 0, 0]
  | 9 => ![37889630322216709668, 0, 0]
  | 10 => ![37889630322216709668, 0, 0]
  | 11 => ![37889630322216709668, 0, 0]
  | 12 => ![37889630322216709668, 0, 0]
  | 13 => ![37889630322216709668, 0, 0]
  | 14 => ![37889630322216709668, 0, 0]
  | 15 => ![37889630322216709668, 0, 0]
  | 16 => ![37889630322216709668, 0, 0]
  | 17 => ![37889630322216709668, 0, 0]
  | 18 => ![37889630322216709668, 0, 0]
  | 19 => ![37889630322216709668, 0, 0]
  | 20 => ![37889630322216709668, 0, 0]
  | 21 => ![37889630322216709668, 0, 0]
  | 22 => ![37889630322216709668, 0, 0]
  | 23 => ![37889630322216709668, 0, 0]
  | 24 => ![37889630322216709668, 0, 0]
  | 25 => ![37889630322216709668, 0, 0]
  | 26 => ![37889630322216709668, 0, 0]
  | 27 => ![37889630322216709668, 0, 0]
  | 28 => ![37889630322216709668, 0, 0]
  | 29 => ![37889630322216709668, 0, 0]
  | 30 => ![37889630322216709668, 0, 0]
  | _ => ![37889630322216709668, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn9 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (200071558881 / 200000000000 : ℚ)
  | 1 => (200083461777 / 200000000000 : ℚ)
  | 2 => (1000479443281 / 1000000000000 : ℚ)
  | 3 => (200108856361 / 200000000000 : ℚ)
  | 4 => (500305955317 / 500000000000 : ℚ)
  | 5 => (40027296717 / 40000000000 : ℚ)
  | 6 => (40030235753 / 40000000000 : ℚ)
  | 7 => (250208107621 / 250000000000 : ℚ)
  | 8 => (1000912122059 / 1000000000000 : ℚ)
  | 9 => (1000995064727 / 1000000000000 : ℚ)
  | 10 => (1001081356683 / 1000000000000 : ℚ)
  | 11 => (500585549071 / 500000000000 : ℚ)
  | 12 => (50063219567 / 50000000000 : ℚ)
  | 13 => (1001361340527 / 1000000000000 : ℚ)
  | 14 => (1001462051961 / 1000000000000 : ℚ)
  | 15 => (10015666339 / 10000000000 : ℚ)
  | 16 => (500837598291 / 500000000000 : ℚ)
  | 17 => (1001787852213 / 1000000000000 : ℚ)
  | 18 => (500952357473 / 500000000000 : ℚ)
  | 19 => (1002025900853 / 1000000000000 : ℚ)
  | 20 => (501075763949 / 500000000000 : ℚ)
  | 21 => (501140857953 / 500000000000 : ℚ)
  | 22 => (1002416586519 / 1000000000000 : ℚ)
  | 23 => (250639065791 / 250000000000 : ℚ)
  | 24 => (501350435497 / 500000000000 : ℚ)
  | 25 => (62678158553 / 62500000000 : ℚ)
  | 26 => (200601077837 / 200000000000 : ℚ)
  | 27 => (125395694753 / 125000000000 : ℚ)
  | 28 => (1003331174877 / 1000000000000 : ℚ)
  | 29 => (250875593169 / 250000000000 : ℚ)
  | 30 => (1003679285689 / 1000000000000 : ℚ)
  | _ => (250965512359 / 250000000000 : ℚ)

def post9Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X9 SZ (gFloorZ X9 SZ) (postTop9 k)
def pre9Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X9 SZ vmax9Z (preTop9 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE9Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X9 SZ (post9Z k) && leTabZ 11 (post9Z k) vmax9Z &&
    preSolZ (famZ k) DZ 11 X9 SZ vmax9Z (pre9Z k) &&
    decide ((autoBoundZ (famZ k) DZ X9 SZ (post9Z k) : ℚ) ≤ eIn9 k * (X9.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X9 SZ (pre9Z k) : ℚ) ≤ (1003862049437 / 1000000000000 : ℚ) * (X9.M DZ * SZ : ℤ))

theorem chkE9_0 : chkE9Q 0 = true := by decide +kernel
theorem chkE9_1 : chkE9Q 1 = true := by decide +kernel
theorem chkE9_2 : chkE9Q 2 = true := by decide +kernel
theorem chkE9_3 : chkE9Q 3 = true := by decide +kernel
theorem chkE9_4 : chkE9Q 4 = true := by decide +kernel
theorem chkE9_5 : chkE9Q 5 = true := by decide +kernel
theorem chkE9_6 : chkE9Q 6 = true := by decide +kernel
theorem chkE9_7 : chkE9Q 7 = true := by decide +kernel
theorem chkE9_8 : chkE9Q 8 = true := by decide +kernel
theorem chkE9_9 : chkE9Q 9 = true := by decide +kernel
theorem chkE9_10 : chkE9Q 10 = true := by decide +kernel
theorem chkE9_11 : chkE9Q 11 = true := by decide +kernel
theorem chkE9_12 : chkE9Q 12 = true := by decide +kernel
theorem chkE9_13 : chkE9Q 13 = true := by decide +kernel
theorem chkE9_14 : chkE9Q 14 = true := by decide +kernel
theorem chkE9_15 : chkE9Q 15 = true := by decide +kernel
theorem chkE9_16 : chkE9Q 16 = true := by decide +kernel
theorem chkE9_17 : chkE9Q 17 = true := by decide +kernel
theorem chkE9_18 : chkE9Q 18 = true := by decide +kernel
theorem chkE9_19 : chkE9Q 19 = true := by decide +kernel
theorem chkE9_20 : chkE9Q 20 = true := by decide +kernel
theorem chkE9_21 : chkE9Q 21 = true := by decide +kernel
theorem chkE9_22 : chkE9Q 22 = true := by decide +kernel
theorem chkE9_23 : chkE9Q 23 = true := by decide +kernel
theorem chkE9_24 : chkE9Q 24 = true := by decide +kernel
theorem chkE9_25 : chkE9Q 25 = true := by decide +kernel
theorem chkE9_26 : chkE9Q 26 = true := by decide +kernel
theorem chkE9_27 : chkE9Q 27 = true := by decide +kernel
theorem chkE9_28 : chkE9Q 28 = true := by decide +kernel
theorem chkE9_29 : chkE9Q 29 = true := by decide +kernel
theorem chkE9_30 : chkE9Q 30 = true := by decide +kernel
theorem chkE9_31 : chkE9Q 31 = true := by decide +kernel

theorem chkE9 : ∀ k, chkE9Q k = true := fun k => by
  fin_cases k; exacts [chkE9_0, chkE9_1, chkE9_2, chkE9_3, chkE9_4, chkE9_5, chkE9_6, chkE9_7, chkE9_8, chkE9_9, chkE9_10, chkE9_11, chkE9_12, chkE9_13, chkE9_14, chkE9_15, chkE9_16, chkE9_17, chkE9_18, chkE9_19, chkE9_20, chkE9_21, chkE9_22, chkE9_23, chkE9_24, chkE9_25, chkE9_26, chkE9_27, chkE9_28, chkE9_29, chkE9_30, chkE9_31]

noncomputable def vmax9 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax9Z)
noncomputable def vpreI9 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre9Z k))
noncomputable def vpostI9 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post9Z k))

theorem solE9 : AutoSolE fam 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9).2.2 vpreI9 vpostI9 vmax9 := by
  rw [xgQ9]; exact (oneSwitchZ_sound famR famA DZ_pos X9R SZ_pos chkE9).1

theorem heEall9 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9).2.2 (vpreI9 k) ≤ (1003862049437 / 1000000000000 : ℝ) := by
  rw [xgQ9]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X9R SZ_pos chkE9).2.2 k).trans_eq (by push_cast; ring)

theorem heIn9 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 9).2.2 (vpostI9 k) ≤ (eIn9 k : ℝ) := by
  rw [xgQ9]; exact (oneSwitchZ_sound famR famA DZ_pos X9R SZ_pos chkE9).2.1

end Cryptarchia.Prob.Certs.E20D11C
