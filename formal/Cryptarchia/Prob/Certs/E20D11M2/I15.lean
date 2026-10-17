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

/-! # E20D11M2: tables for index 15 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ15 : xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15 = castX (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 15) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 15

/-- Phase expectation 15 over the integers. -/
def X15 : PhZ := ⟨4191, 2500, 1, 1,
  fun a b u => [0, 2500, 0, 2500, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  4191⟩

theorem X15R : X15.Rep (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 15).1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 15).2.1 (xgNQ (2927 / 2500 : ℚ) (4191 / 2500 : ℚ) (1363 / 1250 : ℚ) (5973 / 10000 : ℚ) (51 / 50 : ℚ) 15).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax15Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [3903534735018790000, 11003784343879375581, 0, 0, 0, 0, 3636040931658164955, 11003784343870152209, 0, 0, 0, 0, 3353801776550687787, 11003784343860928837, 0, 0, 0, 0, 3056004445636082245, 11003784343851705465, 0, 0, 0, 0, 2741791308675637078, 11003784343842482093, 0, 0, 0, 0, 2410257459345699703, 11003784343833258721, 0, 0, 0, 0, 2060448109184975242, 11003784343824035349, 0, 0, 0, 0, 1691355837892786699, 11003784343814811977, 0, 0, 0, 0, 1301917692042322517, 11003784343805588605, 0, 0, 0, 0, 891012123869467459, 11003784343796365232, 0, 0, 0, 0, 457455761313585710, 11003784343787141860, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop15 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![11003784343681995419, 0, 0]
  | 1 => ![11003784343879375581, 0, 0]
  | 2 => ![11003784343681995419, 0, 0]
  | 3 => ![11003784343681995419, 0, 0]
  | 4 => ![11003784343681995419, 0, 0]
  | 5 => ![11003784343681995419, 0, 0]
  | 6 => ![11003784343681995419, 0, 0]
  | 7 => ![11003784343879375581, 0, 0]
  | 8 => ![11003784343879375581, 0, 0]
  | 9 => ![11003784343681995419, 0, 0]
  | 10 => ![11003784343879375581, 0, 0]
  | 11 => ![11003784343681995419, 0, 0]
  | 12 => ![11003784343681995419, 0, 0]
  | 13 => ![11003784343879375581, 0, 0]
  | 14 => ![11003784343879375581, 0, 0]
  | 15 => ![11003784343879375581, 0, 0]
  | 16 => ![11003784343681995419, 0, 0]
  | 17 => ![11003784343681995419, 0, 0]
  | 18 => ![11003784343879375581, 0, 0]
  | 19 => ![11003784343681995419, 0, 0]
  | 20 => ![11003784343879375581, 0, 0]
  | 21 => ![11003784343879375581, 0, 0]
  | 22 => ![11003784343879375581, 0, 0]
  | 23 => ![11003784343879375581, 0, 0]
  | 24 => ![11003784343681995419, 0, 0]
  | 25 => ![11003784343681995419, 0, 0]
  | 26 => ![11003784343879375581, 0, 0]
  | 27 => ![11003784343681995419, 0, 0]
  | 28 => ![11003784343879375581, 0, 0]
  | 29 => ![11003784343879375581, 0, 0]
  | 30 => ![11003784343879375581, 0, 0]
  | _ => ![11003784343879375581, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop15 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![11003784343901511674, 0, 0]
  | 1 => ![11003784343901511674, 0, 0]
  | 2 => ![11003784343901511674, 0, 0]
  | 3 => ![11003784343901511674, 0, 0]
  | 4 => ![11003784343901511674, 0, 0]
  | 5 => ![11003784343901511674, 0, 0]
  | 6 => ![11003784343901511674, 0, 0]
  | 7 => ![11003784343901511674, 0, 0]
  | 8 => ![11003784343901511674, 0, 0]
  | 9 => ![11003784343901511674, 0, 0]
  | 10 => ![11003784343901511674, 0, 0]
  | 11 => ![11003784343901511674, 0, 0]
  | 12 => ![11003784343901511674, 0, 0]
  | 13 => ![11003784343901511674, 0, 0]
  | 14 => ![11003784343901511674, 0, 0]
  | 15 => ![11003784343901511674, 0, 0]
  | 16 => ![11003784343901511674, 0, 0]
  | 17 => ![11003784343901511674, 0, 0]
  | 18 => ![11003784343901511674, 0, 0]
  | 19 => ![11003784343901511674, 0, 0]
  | 20 => ![11003784343901511674, 0, 0]
  | 21 => ![11003784343901511674, 0, 0]
  | 22 => ![11003784343901511674, 0, 0]
  | 23 => ![11003784343901511674, 0, 0]
  | 24 => ![11003784343901511674, 0, 0]
  | 25 => ![11003784343901511674, 0, 0]
  | 26 => ![11003784343901511674, 0, 0]
  | 27 => ![11003784343901511674, 0, 0]
  | 28 => ![11003784343901511674, 0, 0]
  | 29 => ![11003784343901511674, 0, 0]
  | 30 => ![11003784343901511674, 0, 0]
  | _ => ![11003784343901511674, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn15 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (3280587124721 / 1000000000000000 : ℚ)
  | 1 => (1695006684277 / 500000000000000 : ℚ)
  | 2 => (3502891740871 / 1000000000000000 : ℚ)
  | 3 => (3619320935287 / 1000000000000000 : ℚ)
  | 4 => (3739401943077 / 1000000000000000 : ℚ)
  | 5 => (772647616063 / 200000000000000 : ℚ)
  | 6 => (3990935012827 / 1000000000000000 : ℚ)
  | 7 => (4122600780037 / 1000000000000000 : ℚ)
  | 8 => (4258345816599 / 1000000000000000 : ℚ)
  | 9 => (1099570743493 / 250000000000000 : ℚ)
  | 10 => (4542527539499 / 1000000000000000 : ℚ)
  | 11 => (4691197251781 / 1000000000000000 : ℚ)
  | 12 => (605551539791 / 125000000000000 : ℚ)
  | 13 => (1250573856689 / 250000000000000 : ℚ)
  | 14 => (2582485877881 / 500000000000000 : ℚ)
  | 15 => (5332568984583 / 1000000000000000 : ℚ)
  | 16 => (275260864887 / 50000000000000 : ℚ)
  | 17 => (5683049389501 / 1000000000000000 : ℚ)
  | 18 => (2933100231497 / 500000000000000 : ℚ)
  | 19 => (6054808227487 / 1000000000000000 : ℚ)
  | 20 => (312450644743 / 50000000000000 : ℚ)
  | 21 => (3224478583681 / 500000000000000 : ℚ)
  | 22 => (6654786227651 / 1000000000000000 : ℚ)
  | 23 => (686664772143 / 100000000000000 : ℚ)
  | 24 => (708469173759 / 100000000000000 : ℚ)
  | 25 => (7309070785143 / 1000000000000000 : ℚ)
  | 26 => (471246235253 / 62500000000000 : ℚ)
  | 27 => (1944363983101 / 250000000000000 : ℚ)
  | 28 => (1604355774497 / 200000000000000 : ℚ)
  | 29 => (1654614089027 / 200000000000000 : ℚ)
  | 30 => (8531494746759 / 1000000000000000 : ℚ)
  | _ => (4398609028231 / 500000000000000 : ℚ)

def post15Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X15 SZ (gFloorZ X15 SZ) (postTop15 k)
def pre15Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X15 SZ vmax15Z (preTop15 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE15Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X15 SZ (post15Z k) && leTabZ 11 (post15Z k) vmax15Z &&
    preSolZ (famZ k) DZ 11 X15 SZ vmax15Z (pre15Z k) &&
    decide ((autoBoundZ (famZ k) DZ X15 SZ (post15Z k) : ℚ) ≤ eIn15 k * (X15.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X15 SZ (pre15Z k) : ℚ) ≤ (8797218056499 / 1000000000000000 : ℚ) * (X15.M DZ * SZ : ℤ))

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

theorem solE15 : AutoSolE fam 11 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15).2.2 vpreI15 vpostI15 vmax15 := by
  rw [xgQ15]; exact (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).1

theorem heEall15 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpreI15 k) ≤ (8797218056499 / 1000000000000000 : ℝ) := by
  rw [xgQ15]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.2 k).trans_eq (by push_cast; ring)

theorem heIn15 : ∀ k, autoBound (fam k) (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (2927 / 2500 : ℝ) (4191 / 2500 : ℝ) (1363 / 1250 : ℝ) (5973 / 10000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 k) ≤ (eIn15 k : ℝ) := by
  rw [xgQ15]; exact (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1

end Cryptarchia.Prob.Certs.E20D11M2
