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


theorem xgQ15 : xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15 = castX (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 15) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 15

/-- Phase expectation 15 over the integers. -/
def X15 : PhZ := ⟨17137, 10000, 1, 1,
  fun a b u => [0, 10000, 0, 10000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  17137⟩

theorem X15R : X15.Rep (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 15).1 (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 15).2.1 (xgNQ (11833 / 10000 : ℚ) (17137 / 10000 : ℚ) (11 / 10 : ℚ) (1809 / 5000 : ℚ) (51 / 50 : ℚ) 15).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax15Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [3721968436941083550, 10764278505035032394, 0, 0, 0, 0, 3464304929601325865, 10764278505027653696, 0, 0, 0, 0, 3192938861788052225, 10764278505018430324, 0, 0, 0, 0, 2907141530528653006, 10764278505009206952, 0, 0, 0, 0, 2606145480382513764, 10764278504999983580, 0, 0, 0, 0, 2289142442587369392, 10764278504990760208, 0, 0, 0, 0, 1955281164596949659, 10764278504981536836, 0, 0, 0, 0, 1603665124205648125, 10764278504972313464, 0, 0, 0, 0, 1233350122107302924, 10764278504964934766, 0, 0, 0, 0, 843341746417156083, 10764278504955711394, 0, 0, 0, 0, 432592702369511879, 10764278504946488022, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop15 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![10764278504841341581, 0, 0]
  | 1 => ![10764278505035032394, 0, 0]
  | 2 => ![10764278504841341581, 0, 0]
  | 3 => ![10764278504841341581, 0, 0]
  | 4 => ![10764278505035032394, 0, 0]
  | 5 => ![10764278504841341581, 0, 0]
  | 6 => ![10764278504841341581, 0, 0]
  | 7 => ![10764278505035032394, 0, 0]
  | 8 => ![10764278505035032394, 0, 0]
  | 9 => ![10764278504841341581, 0, 0]
  | 10 => ![10764278505035032394, 0, 0]
  | 11 => ![10764278505035032394, 0, 0]
  | 12 => ![10764278505035032394, 0, 0]
  | 13 => ![10764278505035032394, 0, 0]
  | 14 => ![10764278504841341581, 0, 0]
  | 15 => ![10764278505035032394, 0, 0]
  | 16 => ![10764278505035032394, 0, 0]
  | 17 => ![10764278505035032394, 0, 0]
  | 18 => ![10764278504841341581, 0, 0]
  | 19 => ![10764278505035032394, 0, 0]
  | 20 => ![10764278504841341581, 0, 0]
  | 21 => ![10764278505035032394, 0, 0]
  | 22 => ![10764278505035032394, 0, 0]
  | 23 => ![10764278504841341581, 0, 0]
  | 24 => ![10764278505035032394, 0, 0]
  | 25 => ![10764278504841341581, 0, 0]
  | 26 => ![10764278504841341581, 0, 0]
  | 27 => ![10764278505035032394, 0, 0]
  | 28 => ![10764278504841341581, 0, 0]
  | 29 => ![10764278505035032394, 0, 0]
  | 30 => ![10764278505035032394, 0, 0]
  | _ => ![10764278504841341581, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop15 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![10764278505057168487, 0, 0]
  | 1 => ![10764278505057168487, 0, 0]
  | 2 => ![10764278505057168487, 0, 0]
  | 3 => ![10764278505057168487, 0, 0]
  | 4 => ![10764278505057168487, 0, 0]
  | 5 => ![10764278505057168487, 0, 0]
  | 6 => ![10764278505057168487, 0, 0]
  | 7 => ![10764278505057168487, 0, 0]
  | 8 => ![10764278505057168487, 0, 0]
  | 9 => ![10764278505057168487, 0, 0]
  | 10 => ![10764278505057168487, 0, 0]
  | 11 => ![10764278505057168487, 0, 0]
  | 12 => ![10764278505057168487, 0, 0]
  | 13 => ![10764278505057168487, 0, 0]
  | 14 => ![10764278505057168487, 0, 0]
  | 15 => ![10764278505057168487, 0, 0]
  | 16 => ![10764278505057168487, 0, 0]
  | 17 => ![10764278505057168487, 0, 0]
  | 18 => ![10764278505057168487, 0, 0]
  | 19 => ![10764278505057168487, 0, 0]
  | 20 => ![10764278505057168487, 0, 0]
  | 21 => ![10764278505057168487, 0, 0]
  | 22 => ![10764278505057168487, 0, 0]
  | 23 => ![10764278505057168487, 0, 0]
  | 24 => ![10764278505057168487, 0, 0]
  | 25 => ![10764278505057168487, 0, 0]
  | 26 => ![10764278505057168487, 0, 0]
  | 27 => ![10764278505057168487, 0, 0]
  | 28 => ![10764278505057168487, 0, 0]
  | 29 => ![10764278505057168487, 0, 0]
  | 30 => ![10764278505057168487, 0, 0]
  | _ => ![10764278505250859299, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn15 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (3202255383001 / 1000000000000000 : ℚ)
  | 1 => (3302537151373 / 1000000000000000 : ℚ)
  | 2 => (3405789823921 / 1000000000000000 : ℚ)
  | 3 => (3512093203457 / 1000000000000000 : ℚ)
  | 4 => (3621528841001 / 1000000000000000 : ℚ)
  | 5 => (466772506843 / 125000000000000 : ℚ)
  | 6 => (481266493719 / 125000000000000 : ℚ)
  | 7 => (1984735716971 / 500000000000000 : ℚ)
  | 8 => (4092287234441 / 1000000000000000 : ℚ)
  | 9 => (263666869613 / 62500000000000 : ℚ)
  | 10 => (4348711884283 / 1000000000000000 : ℚ)
  | 11 => (560313427421 / 125000000000000 : ℚ)
  | 12 => (4620152667251 / 1000000000000000 : ℚ)
  | 13 => (4761745660343 / 1000000000000000 : ℚ)
  | 14 => (613423290539 / 125000000000000 : ℚ)
  | 15 => (1264294121601 / 250000000000000 : ℚ)
  | 16 => (2605609939641 / 500000000000000 : ℚ)
  | 17 => (1342405536807 / 250000000000000 : ℚ)
  | 18 => (5532490847021 / 1000000000000000 : ℚ)
  | 19 => (5699935449899 / 1000000000000000 : ℚ)
  | 20 => (587206733729 / 100000000000000 : ℚ)
  | 21 => (6048999800541 / 1000000000000000 : ℚ)
  | 22 => (6230848031673 / 1000000000000000 : ℚ)
  | 23 => (3208864558707 / 500000000000000 : ℚ)
  | 24 => (413110126787 / 62500000000000 : ℚ)
  | 25 => (3403533802311 / 500000000000000 : ℚ)
  | 26 => (1752442135289 / 250000000000000 : ℚ)
  | 27 => (180449734229 / 25000000000000 : ℚ)
  | 28 => (7431856433461 / 1000000000000000 : ℚ)
  | 29 => (7651497871257 / 1000000000000000 : ℚ)
  | 30 => (3938521790517 / 500000000000000 : ℚ)
  | _ => (8108625194647 / 1000000000000000 : ℚ)

def post15Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X15 SZ (gFloorZ X15 SZ) (postTop15 k)
def pre15Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X15 SZ vmax15Z (preTop15 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE15Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X15 SZ (post15Z k) && leTabZ 11 (post15Z k) vmax15Z &&
    preSolZ (famZ k) DZ 11 X15 SZ vmax15Z (pre15Z k) &&
    decide ((autoBoundZ (famZ k) DZ X15 SZ (post15Z k) : ℚ) ≤ eIn15 k * (X15.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X15 SZ (pre15Z k) : ℚ) ≤ (8108625195093 / 1000000000000000 : ℚ) * (X15.M DZ * SZ : ℤ))

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

theorem solE15 : AutoSolE fam 11 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 vpreI15 vpostI15 vmax15 := by
  rw [xgQ15]; exact (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).1

theorem heEall15 : ∀ k, autoBound (fam k) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpreI15 k) ≤ (8108625195093 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.2 k).trans_eq (by push_cast; ring)

theorem heIn15_0 : autoBound (fam 0) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 0) ≤ (3202255383001 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 0; rw [show eIn15 0 = (3202255383001 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_1 : autoBound (fam 1) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 1) ≤ (3302537151373 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 1; rw [show eIn15 1 = (3302537151373 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_2 : autoBound (fam 2) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 2) ≤ (3405789823921 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 2; rw [show eIn15 2 = (3405789823921 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_3 : autoBound (fam 3) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 3) ≤ (3512093203457 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 3; rw [show eIn15 3 = (3512093203457 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_4 : autoBound (fam 4) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 4) ≤ (3621528841001 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 4; rw [show eIn15 4 = (3621528841001 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_5 : autoBound (fam 5) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 5) ≤ (466772506843 / 125000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 5; rw [show eIn15 5 = (466772506843 / 125000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_6 : autoBound (fam 6) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 6) ≤ (481266493719 / 125000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 6; rw [show eIn15 6 = (481266493719 / 125000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_7 : autoBound (fam 7) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 7) ≤ (1984735716971 / 500000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 7; rw [show eIn15 7 = (1984735716971 / 500000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_8 : autoBound (fam 8) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 8) ≤ (4092287234441 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 8; rw [show eIn15 8 = (4092287234441 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_9 : autoBound (fam 9) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 9) ≤ (263666869613 / 62500000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 9; rw [show eIn15 9 = (263666869613 / 62500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_10 : autoBound (fam 10) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 10) ≤ (4348711884283 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 10; rw [show eIn15 10 = (4348711884283 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_11 : autoBound (fam 11) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 11) ≤ (560313427421 / 125000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 11; rw [show eIn15 11 = (560313427421 / 125000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_12 : autoBound (fam 12) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 12) ≤ (4620152667251 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 12; rw [show eIn15 12 = (4620152667251 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_13 : autoBound (fam 13) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 13) ≤ (4761745660343 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 13; rw [show eIn15 13 = (4761745660343 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_14 : autoBound (fam 14) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 14) ≤ (613423290539 / 125000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 14; rw [show eIn15 14 = (613423290539 / 125000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_15 : autoBound (fam 15) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 15) ≤ (1264294121601 / 250000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 15; rw [show eIn15 15 = (1264294121601 / 250000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_16 : autoBound (fam 16) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 16) ≤ (2605609939641 / 500000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 16; rw [show eIn15 16 = (2605609939641 / 500000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_17 : autoBound (fam 17) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 17) ≤ (1342405536807 / 250000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 17; rw [show eIn15 17 = (1342405536807 / 250000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_18 : autoBound (fam 18) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 18) ≤ (5532490847021 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 18; rw [show eIn15 18 = (5532490847021 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_19 : autoBound (fam 19) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 19) ≤ (5699935449899 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 19; rw [show eIn15 19 = (5699935449899 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_20 : autoBound (fam 20) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 20) ≤ (587206733729 / 100000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 20; rw [show eIn15 20 = (587206733729 / 100000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_21 : autoBound (fam 21) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 21) ≤ (6048999800541 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 21; rw [show eIn15 21 = (6048999800541 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_22 : autoBound (fam 22) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 22) ≤ (6230848031673 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 22; rw [show eIn15 22 = (6230848031673 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_23 : autoBound (fam 23) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 23) ≤ (3208864558707 / 500000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 23; rw [show eIn15 23 = (3208864558707 / 500000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_24 : autoBound (fam 24) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 24) ≤ (413110126787 / 62500000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 24; rw [show eIn15 24 = (413110126787 / 62500000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_25 : autoBound (fam 25) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 25) ≤ (3403533802311 / 500000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 25; rw [show eIn15 25 = (3403533802311 / 500000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_26 : autoBound (fam 26) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 26) ≤ (1752442135289 / 250000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 26; rw [show eIn15 26 = (1752442135289 / 250000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_27 : autoBound (fam 27) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 27) ≤ (180449734229 / 25000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 27; rw [show eIn15 27 = (180449734229 / 25000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_28 : autoBound (fam 28) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 28) ≤ (7431856433461 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 28; rw [show eIn15 28 = (7431856433461 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_29 : autoBound (fam 29) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 29) ≤ (7651497871257 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 29; rw [show eIn15 29 = (7651497871257 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_30 : autoBound (fam 30) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 30) ≤ (3938521790517 / 500000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 30; rw [show eIn15 30 = (3938521790517 / 500000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

theorem heIn15_31 : autoBound (fam 31) (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11833 / 10000 : ℝ) (17137 / 10000 : ℝ) (11 / 10 : ℝ) (1809 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 31) ≤ (8108625194647 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; have h := (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1 31; rw [show eIn15 31 = (8108625194647 / 1000000000000000 : ℚ) from rfl] at h; exact h.trans_eq (by push_cast; ring)

end Cryptarchia.Prob.Certs.E20D11C
