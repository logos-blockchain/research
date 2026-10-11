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


theorem xgQ15 : xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15 = castX (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 15) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 15

/-- Phase expectation 15 over the integers. -/
def X15 : PhZ := ⟨17553, 10000, 1, 1,
  fun a b u => [0, 10000, 0, 10000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  17553⟩

theorem X15R : X15.Rep (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 15).1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 15).2.1 (xgNQ (11873 / 10000 : ℚ) (17553 / 10000 : ℚ) (11151 / 10000 : ℚ) (1779 / 5000 : ℚ) (51 / 50 : ℚ) 15).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax15Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [3633750015280174384, 10509168845256428732, 0, 0, 0, 0, 3382193428184656039, 10509168845249050035, 0, 0, 0, 0, 3117259093349756625, 10509168845239826663, 0, 0, 0, 0, 2838235583828016939, 10509168845230603291, 0, 0, 0, 0, 2544373639075033431, 10509168845221379918, 0, 0, 0, 0, 2234884152970460785, 10509168845214001221, 0, 0, 0, 0, 1908936054822073426, 10509168845204777849, 0, 0, 0, 0, 1565654077708182274, 10509168845195554477, 0, 0, 0, 0, 1204116408121156342, 10509168845186331105, 0, 0, 0, 0, 823352210624476457, 10509168845178952407, 0, 0, 0, 0, 422339020876221352, 10509168845169729035, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop15 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![10509168845068271943, 0, 0]
  | 1 => ![10509168845068271943, 0, 0]
  | 2 => ![10509168845068271943, 0, 0]
  | 3 => ![10509168845068271943, 0, 0]
  | 4 => ![10509168845256428732, 0, 0]
  | 5 => ![10509168845068271943, 0, 0]
  | 6 => ![10509168845068271943, 0, 0]
  | 7 => ![10509168845256428732, 0, 0]
  | 8 => ![10509168845256428732, 0, 0]
  | 9 => ![10509168845068271943, 0, 0]
  | 10 => ![10509168845068271943, 0, 0]
  | 11 => ![10509168845256428732, 0, 0]
  | 12 => ![10509168845256428732, 0, 0]
  | 13 => ![10509168845068271943, 0, 0]
  | 14 => ![10509168845068271943, 0, 0]
  | 15 => ![10509168845256428732, 0, 0]
  | 16 => ![10509168845068271943, 0, 0]
  | 17 => ![10509168845256428732, 0, 0]
  | 18 => ![10509168845068271943, 0, 0]
  | 19 => ![10509168845068271943, 0, 0]
  | 20 => ![10509168845256428732, 0, 0]
  | 21 => ![10509168845256428732, 0, 0]
  | 22 => ![10509168845256428732, 0, 0]
  | 23 => ![10509168845256428732, 0, 0]
  | 24 => ![10509168845068271943, 0, 0]
  | 25 => ![10509168845068271943, 0, 0]
  | 26 => ![10509168845256428732, 0, 0]
  | 27 => ![10509168845068271943, 0, 0]
  | 28 => ![10509168845256428732, 0, 0]
  | 29 => ![10509168845256428732, 0, 0]
  | 30 => ![10509168845256428732, 0, 0]
  | _ => ![10509168845256428732, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop15 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![10509168845278564825, 0, 0]
  | 1 => ![10509168845278564825, 0, 0]
  | 2 => ![10509168845278564825, 0, 0]
  | 3 => ![10509168845278564825, 0, 0]
  | 4 => ![10509168845278564825, 0, 0]
  | 5 => ![10509168845278564825, 0, 0]
  | 6 => ![10509168845278564825, 0, 0]
  | 7 => ![10509168845278564825, 0, 0]
  | 8 => ![10509168845278564825, 0, 0]
  | 9 => ![10509168845278564825, 0, 0]
  | 10 => ![10509168845278564825, 0, 0]
  | 11 => ![10509168845278564825, 0, 0]
  | 12 => ![10509168845278564825, 0, 0]
  | 13 => ![10509168845278564825, 0, 0]
  | 14 => ![10509168845278564825, 0, 0]
  | 15 => ![10509168845278564825, 0, 0]
  | 16 => ![10509168845278564825, 0, 0]
  | 17 => ![10509168845278564825, 0, 0]
  | 18 => ![10509168845278564825, 0, 0]
  | 19 => ![10509168845278564825, 0, 0]
  | 20 => ![10509168845278564825, 0, 0]
  | 21 => ![10509168845278564825, 0, 0]
  | 22 => ![10509168845278564825, 0, 0]
  | 23 => ![10509168845278564825, 0, 0]
  | 24 => ![10509168845278564825, 0, 0]
  | 25 => ![10509168845278564825, 0, 0]
  | 26 => ![10509168845278564825, 0, 0]
  | 27 => ![10509168845278564825, 0, 0]
  | 28 => ![10509168845278564825, 0, 0]
  | 29 => ![10509168845278564825, 0, 0]
  | 30 => ![10509168845278564825, 0, 0]
  | _ => ![10509168845278564825, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn15 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (1563432900333 / 500000000000000 : ℚ)
  | 1 => (1612384250483 / 500000000000000 : ℚ)
  | 2 => (831392768001 / 250000000000000 : ℚ)
  | 3 => (1714675696207 / 500000000000000 : ℚ)
  | 4 => (1768094523599 / 500000000000000 : ℚ)
  | 5 => (3646165345291 / 1000000000000000 : ℚ)
  | 6 => (939840834761 / 250000000000000 : ℚ)
  | 7 => (3875867839811 / 1000000000000000 : ℚ)
  | 8 => (3995765433831 / 1000000000000000 : ℚ)
  | 9 => (4119144498047 / 1000000000000000 : ℚ)
  | 10 => (4246095213971 / 1000000000000000 : ℚ)
  | 11 => (1094177394911 / 250000000000000 : ℚ)
  | 12 => (2255540710531 / 500000000000000 : ℚ)
  | 13 => (2324653201569 / 500000000000000 : ℚ)
  | 14 => (2395741019219 / 500000000000000 : ℚ)
  | 15 => (308606730851 / 62500000000000 : ℚ)
  | 16 => (5088084594863 / 1000000000000000 : ℚ)
  | 17 => (2621357916991 / 500000000000000 : ℚ)
  | 18 => (108034127351 / 20000000000000 : ℚ)
  | 19 => (5565163020359 / 1000000000000000 : ℚ)
  | 20 => (716649310219 / 125000000000000 : ℚ)
  | 21 => (5905911302319 / 1000000000000000 : ℚ)
  | 22 => (6083425889091 / 1000000000000000 : ℚ)
  | 23 => (78323156209 / 12500000000000 : ℚ)
  | 24 => (258132288681 / 40000000000000 : ℚ)
  | 25 => (6645907967259 / 1000000000000000 : ℚ)
  | 26 => (427735904597 / 62500000000000 : ℚ)
  | 27 => (1761757063093 / 250000000000000 : ℚ)
  | 28 => (1813948148127 / 250000000000000 : ℚ)
  | 29 => (3735096263879 / 500000000000000 : ℚ)
  | 30 => (307614192523 / 40000000000000 : ℚ)
  | _ => (7916407893583 / 1000000000000000 : ℚ)

def post15Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X15 SZ (gFloorZ X15 SZ) (postTop15 k)
def pre15Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X15 SZ vmax15Z (preTop15 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE15Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X15 SZ (post15Z k) && leTabZ 11 (post15Z k) vmax15Z &&
    preSolZ (famZ k) DZ 11 X15 SZ vmax15Z (pre15Z k) &&
    decide ((autoBoundZ (famZ k) DZ X15 SZ (post15Z k) : ℚ) ≤ eIn15 k * (X15.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X15 SZ (pre15Z k) : ℚ) ≤ (1583281578723 / 200000000000000 : ℚ) * (X15.M DZ * SZ : ℤ))

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

theorem solE15 : AutoSolE fam 11 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 vpreI15 vpostI15 vmax15 := by
  rw [xgQ15]; exact (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).1

theorem heEall15 : ∀ k, autoBound (fam k) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpreI15 k) ≤ (1583281578723 / 200000000000000 : ℝ) := by
  rw [xgQ15]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.2 k).trans_eq (by push_cast; ring)

theorem heIn15 : ∀ k, autoBound (fam k) (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15).1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.1 (xg (11873 / 10000 : ℝ) (17553 / 10000 : ℝ) (11151 / 10000 : ℝ) (1779 / 5000 : ℝ) (51 / 50 : ℝ) 15).2.2 (vpostI15 k) ≤ (eIn15 k : ℝ) := by
  rw [xgQ15]; exact (oneSwitchZ_sound famR famA DZ_pos X15R SZ_pos chkE15).2.1

end Cryptarchia.Prob.Certs.E20D11M2
