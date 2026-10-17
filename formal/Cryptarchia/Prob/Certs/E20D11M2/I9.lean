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

/-! # E20D11M2: tables for index 9 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ9 : xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9 = castX (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 9) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 9

/-- Phase expectation 9 over the integers. -/
def X9 : PhZ := ⟨25032843, 25000000, 1, 1,
  fun a b u => [149521171239, 149521171239, 149325000000, 250000000000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  149521171239⟩

theorem X9R : X9.Rep (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 9).1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 9).2.1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 9).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax9Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [21151048124160253345, 30843030323449280104, 0, 0, 0, 0, 20964074387024792762, 30843030323412386616, 0, 0, 0, 0, 20766793893305011277, 30843030323393939871, 0, 0, 0, 0, 20558638492433023696, 30843030323357046383, 0, 0, 0, 0, 20339008715087983688, 30843030323338599639, 0, 0, 0, 0, 20107272046728412444, 30843030323320152895, 0, 0, 0, 0, 19862761106068455111, 30843030323283259407, 0, 0, 0, 0, 19604771722964041804, 30843030323264812663, 0, 0, 0, 0, 19332560910617651813, 30843030323227919175, 0, 0, 0, 0, 19045344725719107570, 30843030323209472431, 0, 0, 0, 0, 18742296010767014202, 30843030323191025687, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop9 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![30843030323449280104, 0, 0]
  | 1 => ![30843030323449280104, 0, 0]
  | 2 => ![30843030323449280104, 0, 0]
  | 3 => ![30843030323449280104, 0, 0]
  | 4 => ![30843030323449280104, 0, 0]
  | 5 => ![30843030323449280104, 0, 0]
  | 6 => ![30843030323449280104, 0, 0]
  | 7 => ![30843030323449280104, 0, 0]
  | 8 => ![30843030323449280104, 0, 0]
  | 9 => ![30843030323449280104, 0, 0]
  | 10 => ![30843030323449280104, 0, 0]
  | 11 => ![30843030323449280104, 0, 0]
  | 12 => ![30843030323449280104, 0, 0]
  | 13 => ![30843030323449280104, 0, 0]
  | 14 => ![30843030323449280104, 0, 0]
  | 15 => ![30843030323449280104, 0, 0]
  | 16 => ![30843030323449280104, 0, 0]
  | 17 => ![30843030323449280104, 0, 0]
  | 18 => ![30843030323449280104, 0, 0]
  | 19 => ![30843030323449280104, 0, 0]
  | 20 => ![30843030323449280104, 0, 0]
  | 21 => ![30843030323449280104, 0, 0]
  | 22 => ![30843030323449280104, 0, 0]
  | 23 => ![30843030323449280104, 0, 0]
  | 24 => ![30843030323449280104, 0, 0]
  | 25 => ![30843030323449280104, 0, 0]
  | 26 => ![30843030323449280104, 0, 0]
  | 27 => ![30843030323449280104, 0, 0]
  | 28 => ![30843030323449280104, 0, 0]
  | 29 => ![30843030323449280104, 0, 0]
  | 30 => ![30843030323449280104, 0, 0]
  | _ => ![30843030323449280104, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop9 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![30843030323523067080, 0, 0]
  | 1 => ![30843030323523067080, 0, 0]
  | 2 => ![30843030323523067080, 0, 0]
  | 3 => ![30843030323523067080, 0, 0]
  | 4 => ![30843030323523067080, 0, 0]
  | 5 => ![30843030323523067080, 0, 0]
  | 6 => ![30843030323523067080, 0, 0]
  | 7 => ![30843030323523067080, 0, 0]
  | 8 => ![30843030323523067080, 0, 0]
  | 9 => ![30843030323523067080, 0, 0]
  | 10 => ![30843030323523067080, 0, 0]
  | 11 => ![30843030323523067080, 0, 0]
  | 12 => ![30843030323523067080, 0, 0]
  | 13 => ![30843030323523067080, 0, 0]
  | 14 => ![30843030323523067080, 0, 0]
  | 15 => ![30843030323523067080, 0, 0]
  | 16 => ![30843030323523067080, 0, 0]
  | 17 => ![30843030323523067080, 0, 0]
  | 18 => ![30843030323523067080, 0, 0]
  | 19 => ![30843030323523067080, 0, 0]
  | 20 => ![30843030323523067080, 0, 0]
  | 21 => ![30843030323523067080, 0, 0]
  | 22 => ![30843030323523067080, 0, 0]
  | 23 => ![30843030323523067080, 0, 0]
  | 24 => ![30843030323523067080, 0, 0]
  | 25 => ![30843030323523067080, 0, 0]
  | 26 => ![30843030323523067080, 0, 0]
  | 27 => ![30843030323523067080, 0, 0]
  | 28 => ![30843030323523067080, 0, 0]
  | 29 => ![30843030323523067080, 0, 0]
  | 30 => ![30843030323523067080, 0, 0]
  | _ => ![30843030323523067080, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn9 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (2490410347663 / 2500000000000 : ℚ)
  | 1 => (1992258436961 / 2000000000000 : ℚ)
  | 2 => (249023668899 / 250000000000 : ℚ)
  | 3 => (398424216587 / 400000000000 : ℚ)
  | 4 => (4980134240049 / 5000000000000 : ℚ)
  | 5 => (9959936279983 / 10000000000000 : ℚ)
  | 6 => (9959609150697 / 10000000000000 : ℚ)
  | 7 => (1991857487443 / 2000000000000 : ℚ)
  | 8 => (1991794298619 / 2000000000000 : ℚ)
  | 9 => (9958661680443 / 10000000000000 : ℚ)
  | 10 => (1991671673971 / 2000000000000 : ℚ)
  | 11 => (199161238807 / 200000000000 : ℚ)
  | 12 => (2489443194819 / 2500000000000 : ℚ)
  | 13 => (9957491282203 / 10000000000000 : ℚ)
  | 14 => (995721785279 / 1000000000000 : ℚ)
  | 15 => (4978476451317 / 5000000000000 : ℚ)
  | 16 => (1991339370219 / 2000000000000 : ℚ)
  | 17 => (1244556265637 / 1250000000000 : ℚ)
  | 18 => (9956213158899 / 10000000000000 : ℚ)
  | 19 => (4977993196927 / 5000000000000 : ℚ)
  | 20 => (2488942569531 / 2500000000000 : ℚ)
  | 21 => (9955565266371 / 10000000000000 : ℚ)
  | 22 => (398214872777 / 400000000000 : ℚ)
  | 23 => (995519040391 / 1000000000000 : ℚ)
  | 24 => (9955021491851 / 10000000000000 : ℚ)
  | 25 => (2488716390057 / 2500000000000 : ℚ)
  | 26 => (1990944618103 / 2000000000000 : ℚ)
  | 27 => (1244324321021 / 1250000000000 : ℚ)
  | 28 => (9954480482083 / 10000000000000 : ℚ)
  | 29 => (9954381324011 / 10000000000000 : ℚ)
  | 30 => (311071799623 / 312500000000 : ℚ)
  | _ => (1990845953881 / 2000000000000 : ℚ)

def post9Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X9 SZ (gFloorZ X9 SZ) (postTop9 k)
def pre9Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X9 SZ vmax9Z (preTop9 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE9Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X9 SZ (post9Z k) && leTabZ 11 (post9Z k) vmax9Z &&
    preSolZ (famZ k) DZ 11 X9 SZ vmax9Z (pre9Z k) &&
    decide ((autoBoundZ (famZ k) DZ X9 SZ (post9Z k) : ℚ) ≤ eIn9 k * (X9.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X9 SZ (pre9Z k) : ℚ) ≤ (9974176775889 / 10000000000000 : ℚ) * (X9.M DZ * SZ : ℤ))

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

theorem solE9 : AutoSolE fam 11 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9).2.2 vpreI9 vpostI9 vmax9 := by
  rw [xgQ9]; exact (oneSwitchZ_sound famR famA DZ_pos X9R SZ_pos chkE9).1

theorem heEall9 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9).2.2 (vpreI9 k) ≤ (9974176775889 / 10000000000000 : ℝ) := by
  rw [xgQ9]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X9R SZ_pos chkE9).2.2 k).trans_eq (by push_cast; ring)

theorem heIn9 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 9).2.2 (vpostI9 k) ≤ (eIn9 k : ℝ) := by
  rw [xgQ9]; exact (oneSwitchZ_sound famR famA DZ_pos X9R SZ_pos chkE9).2.1

end Cryptarchia.Prob.Certs.E20D11M2
