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

/-! # E20D11C: tables for index 15 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ15 : xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15 = castX (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 15) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 15

/-- Phase expectation 15 over the integers. -/
def X15 : PhZ := ⟨16361, 10000, 1, 1,
  fun a b u => [0, 10000, 0, 10000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  16361⟩

theorem X15R : X15.Rep (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 15).1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 15).2.1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 15).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax15Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [3999695546038926473, 11274826767360526568, 0, 0, 0, 0, 3725612499242621525, 11274826767351303196, 0, 0, 0, 0, 3436420821888560517, 11274826767342079824, 0, 0, 0, 0, 3131287661600207490, 11274826767332856452, 0, 0, 0, 0, 2809334255611559283, 11274826767323633080, 0, 0, 0, 0, 2469633399990073101, 11274826767314409708, 0, 0, 0, 0, 2111206779359781386, 11274826767305186336, 0, 0, 0, 0, 1733022149409427731, 11274826767295962964, 0, 0, 0, 0, 1333990364106134408, 11274826767286739592, 0, 0, 0, 0, 912962239024875137, 11274826767277516220, 0, 0, 0, 0, 468725241777537979, 11274826767268292848, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop15 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![11274826767157612383, 0, 0]
  | 1 => ![11274826767157612383, 0, 0]
  | 2 => ![11274826767157612383, 0, 0]
  | 3 => ![11274826767157612383, 0, 0]
  | 4 => ![11274826767157612383, 0, 0]
  | 5 => ![11274826767157612383, 0, 0]
  | 6 => ![11274826767360526568, 0, 0]
  | 7 => ![11274826767360526568, 0, 0]
  | 8 => ![11274826767360526568, 0, 0]
  | 9 => ![11274826767157612383, 0, 0]
  | 10 => ![11274826767360526568, 0, 0]
  | 11 => ![11274826767360526568, 0, 0]
  | 12 => ![11274826767360526568, 0, 0]
  | 13 => ![11274826767157612383, 0, 0]
  | 14 => ![11274826767157612383, 0, 0]
  | 15 => ![11274826767157612383, 0, 0]
  | 16 => ![11274826767157612383, 0, 0]
  | 17 => ![11274826767360526568, 0, 0]
  | 18 => ![11274826767360526568, 0, 0]
  | 19 => ![11274826767360526568, 0, 0]
  | 20 => ![11274826767360526568, 0, 0]
  | 21 => ![11274826767157612383, 0, 0]
  | 22 => ![11274826767157612383, 0, 0]
  | 23 => ![11274826767157612383, 0, 0]
  | 24 => ![11274826767360526568, 0, 0]
  | 25 => ![11274826767157612383, 0, 0]
  | 26 => ![11274826767360526568, 0, 0]
  | 27 => ![11274826767157612383, 0, 0]
  | 28 => ![11274826767157612383, 0, 0]
  | 29 => ![11274826767360526568, 0, 0]
  | 30 => ![11274826767360526568, 0, 0]
  | _ => ![11274826767157612383, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop15 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![11274826767384507336, 0, 0]
  | 1 => ![11274826767384507336, 0, 0]
  | 2 => ![11274826767384507336, 0, 0]
  | 3 => ![11274826767384507336, 0, 0]
  | 4 => ![11274826767384507336, 0, 0]
  | 5 => ![11274826767384507336, 0, 0]
  | 6 => ![11274826767384507336, 0, 0]
  | 7 => ![11274826767384507336, 0, 0]
  | 8 => ![11274826767384507336, 0, 0]
  | 9 => ![11274826767384507336, 0, 0]
  | 10 => ![11274826767384507336, 0, 0]
  | 11 => ![11274826767384507336, 0, 0]
  | 12 => ![11274826767384507336, 0, 0]
  | 13 => ![11274826767384507336, 0, 0]
  | 14 => ![11274826767384507336, 0, 0]
  | 15 => ![11274826767384507336, 0, 0]
  | 16 => ![11274826767384507336, 0, 0]
  | 17 => ![11274826767384507336, 0, 0]
  | 18 => ![11274826767384507336, 0, 0]
  | 19 => ![11274826767384507336, 0, 0]
  | 20 => ![11274826767384507336, 0, 0]
  | 21 => ![11274826767384507336, 0, 0]
  | 22 => ![11274826767384507336, 0, 0]
  | 23 => ![11274826767384507336, 0, 0]
  | 24 => ![11274826767384507336, 0, 0]
  | 25 => ![11274826767384507336, 0, 0]
  | 26 => ![11274826767384507336, 0, 0]
  | 27 => ![11274826767384507336, 0, 0]
  | 28 => ![11274826767384507336, 0, 0]
  | 29 => ![11274826767384507336, 0, 0]
  | 30 => ![11274826767384507336, 0, 0]
  | _ => ![11274826767384507336, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn15 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (3360853304369 / 1000000000000000 : ℚ)
  | 1 => (3472976509181 / 1000000000000000 : ℚ)
  | 2 => (897159390537 / 250000000000000 : ℚ)
  | 3 => (1853968813153 / 500000000000000 : ℚ)
  | 4 => (1915490110493 / 500000000000000 : ℚ)
  | 5 => (494733906107 / 125000000000000 : ℚ)
  | 6 => (15971558679 / 3906250000000 : ℚ)
  | 7 => (1055908571193 / 250000000000000 : ℚ)
  | 8 => (2181365119673 / 500000000000000 : ℚ)
  | 9 => (70408165067 / 15625000000000 : ℚ)
  | 10 => (2326964718069 / 500000000000000 : ℚ)
  | 11 => (4806271544651 / 1000000000000000 : ℚ)
  | 12 => (4963272110473 / 1000000000000000 : ℚ)
  | 13 => (1281264224307 / 250000000000000 : ℚ)
  | 14 => (5291754223669 / 1000000000000000 : ℚ)
  | 15 => (2731747485547 / 500000000000000 : ℚ)
  | 16 => (2820206295063 / 500000000000000 : ℚ)
  | 17 => (5822643104109 / 1000000000000000 : ℚ)
  | 18 => (1202065021729 / 200000000000000 : ℚ)
  | 19 => (6203599770117 / 1000000000000000 : ℚ)
  | 20 => (6402610819123 / 1000000000000000 : ℚ)
  | 21 => (6607504541049 / 1000000000000000 : ℚ)
  | 22 => (6818429764203 / 1000000000000000 : ℚ)
  | 23 => (351776892093 / 50000000000000 : ℚ)
  | 24 => (7258982633079 / 1000000000000000 : ℚ)
  | 25 => (7488920476493 / 1000000000000000 : ℚ)
  | 26 => (3862755082259 / 500000000000000 : ℚ)
  | 27 => (498057056637 / 62500000000000 : ℚ)
  | 28 => (4109646146699 / 500000000000000 : ℚ)
  | 29 => (2119203563911 / 250000000000000 : ℚ)
  | 30 => (2185411753143 / 250000000000000 : ℚ)
  | _ => (9013961022891 / 1000000000000000 : ℚ)

def post15Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X15 SZ (gFloorZ X15 SZ) (postTop15 k)
def pre15Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X15 SZ vmax15Z (preTop15 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE15Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X15 SZ (post15Z k) && leTabZ 11 (post15Z k) vmax15Z &&
    preSolZ (famZ k) DZ 11 X15 SZ vmax15Z (pre15Z k) &&
    decide ((autoBoundZ (famZ k) DZ X15 SZ (post15Z k) : ℚ) ≤ eIn15 k * (X15.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X15 SZ (pre15Z k) : ℚ) ≤ (4506980511537 / 500000000000000 : ℚ) * (X15.M DZ * SZ : ℤ))

theorem chkE15_0 : chkE15Q 0 = true := by decide +kernel
theorem chkE15_1 : chkE15Q 1 = true := by decide +kernel
theorem chkE15_2 : chkE15Q 2 = true := by decide +kernel
theorem chkE15_3 : chkE15Q 3 = true := by decide +kernel
theorem chkE15_4 : chkE15Q 4 = true := by decide +kernel
theorem chkE15_5 : chkE15Q 5 = true := by decide +kernel
theorem chkE15_6 : chkE15Q 6 = true := by decide +kernel
theorem chkE15_7 : chkE15Q 7 = true := by decide +kernel
theorem chkE15_8 : chkE15Q 8 = true := by decide +kernel
theorem chkE15_9 : chkE15Q 9 = true := by decide +kernel
theorem chkE15_10 : chkE15Q 10 = true := by decide +kernel
theorem chkE15_11 : chkE15Q 11 = true := by decide +kernel
theorem chkE15_12 : chkE15Q 12 = true := by decide +kernel
theorem chkE15_13 : chkE15Q 13 = true := by decide +kernel
theorem chkE15_14 : chkE15Q 14 = true := by decide +kernel
theorem chkE15_15 : chkE15Q 15 = true := by decide +kernel
theorem chkE15_16 : chkE15Q 16 = true := by decide +kernel
theorem chkE15_17 : chkE15Q 17 = true := by decide +kernel
theorem chkE15_18 : chkE15Q 18 = true := by decide +kernel
theorem chkE15_19 : chkE15Q 19 = true := by decide +kernel
theorem chkE15_20 : chkE15Q 20 = true := by decide +kernel
theorem chkE15_21 : chkE15Q 21 = true := by decide +kernel
theorem chkE15_22 : chkE15Q 22 = true := by decide +kernel
theorem chkE15_23 : chkE15Q 23 = true := by decide +kernel
theorem chkE15_24 : chkE15Q 24 = true := by decide +kernel
theorem chkE15_25 : chkE15Q 25 = true := by decide +kernel
theorem chkE15_26 : chkE15Q 26 = true := by decide +kernel
theorem chkE15_27 : chkE15Q 27 = true := by decide +kernel
theorem chkE15_28 : chkE15Q 28 = true := by decide +kernel
theorem chkE15_29 : chkE15Q 29 = true := by decide +kernel
theorem chkE15_30 : chkE15Q 30 = true := by decide +kernel
theorem chkE15_31 : chkE15Q 31 = true := by decide +kernel

theorem chkE15 : ∀ k, chkE15Q k = true := fun k => by
  fin_cases k; exacts [chkE15_0, chkE15_1, chkE15_2, chkE15_3, chkE15_4, chkE15_5, chkE15_6, chkE15_7, chkE15_8, chkE15_9, chkE15_10, chkE15_11, chkE15_12, chkE15_13, chkE15_14, chkE15_15, chkE15_16, chkE15_17, chkE15_18, chkE15_19, chkE15_20, chkE15_21, chkE15_22, chkE15_23, chkE15_24, chkE15_25, chkE15_26, chkE15_27, chkE15_28, chkE15_29, chkE15_30, chkE15_31]

noncomputable def vmax15 : ℕ → Fin 3 → Bool → ℝ := castT (castZ SZ vmax15Z)
noncomputable def vpreI15 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (pre15Z k))
noncomputable def vpostI15 : Fin 32 → ℕ → Fin 3 → Bool → ℝ := fun k => castT (castZ SZ (post15Z k))

theorem solE15 : AutoSolE fam 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.2 vpreI15 vpostI15 vmax15 := by
  rw [xgQ15]; exact (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).1

theorem heEall15 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpreI15 k) ≤ (4506980511537 / 500000000000000 : ℝ) := by
  rw [xgQ15]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.2 k).trans_eq (by push_cast; ring)

theorem heIn15 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 k) ≤ (eIn15 k : ℝ) := by
  rw [xgQ15]; exact (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1

end Cryptarchia.Prob.Certs.E20D11C
