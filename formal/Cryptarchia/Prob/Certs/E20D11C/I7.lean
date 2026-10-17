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

/-! # E20D11C: tables for index 7 -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0


theorem xgQ7 : xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7 = castX (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 7) :=
  xg_ofQ (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by norm_num) 7

/-- Phase expectation 7 over the integers. -/
def X7 : PhZ := ⟨17849851, 20000000, 1, 1,
  fun a b u => [16361, 16361, 10000, 10000, 0, 0, 0, 0, 0, 0, 0, 0].getD (4 * a.val + (if b then 2 else 0) + if u then 1 else 0) 0,
  16361⟩

theorem X7R : X7.Rep (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 7).1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 7).2.1 (xgNQ (11619 / 10000 : ℚ) (16361 / 10000 : ℚ) (669 / 625 : ℚ) (1091 / 2000 : ℚ) (51 / 50 : ℚ) 7).2.2 := by decide +kernel

/-- The largest post-switch table, listed by `(q, a, u)`. -/
def vmax7Z : ℕ → Fin 3 → Bool → ℤ := tabZ
  [11274826767157612383, 11274826767157612383, 0, 0, 0, 0, 11274826767157612383, 11274826767157612383, 0, 0, 0, 0, 11274826767155767709, 11274826767155767709, 0, 0, 0, 0, 11274826767155767709, 11274826767155767709, 0, 0, 0, 0, 11274826767153923035, 11274826767153923035, 0, 0, 0, 0, 11274826767153923035, 11274826767153923035, 0, 0, 0, 0, 11274826767152078360, 11274826767152078360, 0, 0, 0, 0, 11274826767152078360, 11274826767152078360, 0, 0, 0, 0, 11274826767150233686, 11274826767150233686, 0, 0, 0, 0, 11274826767150233686, 11274826767150233686, 0, 0, 0, 0, 11274826767148389011, 11274826767148389011, 0, 0, 0, 0]

/-- Each member's post-switch table at `(0, a, true)`. -/
def postTop7 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![11274826767157612383, 0, 0]
  | 1 => ![11274826767157612383, 0, 0]
  | 2 => ![11274826767157612383, 0, 0]
  | 3 => ![11274826767157612383, 0, 0]
  | 4 => ![11274826767157612383, 0, 0]
  | 5 => ![11274826767157612383, 0, 0]
  | 6 => ![11274826767157612383, 0, 0]
  | 7 => ![11274826767157612383, 0, 0]
  | 8 => ![11274826767157612383, 0, 0]
  | 9 => ![11274826767157612383, 0, 0]
  | 10 => ![11274826767157612383, 0, 0]
  | 11 => ![11274826767157612383, 0, 0]
  | 12 => ![11274826767157612383, 0, 0]
  | 13 => ![11274826767157612383, 0, 0]
  | 14 => ![11274826767157612383, 0, 0]
  | 15 => ![11274826767157612383, 0, 0]
  | 16 => ![11274826767157612383, 0, 0]
  | 17 => ![11274826767157612383, 0, 0]
  | 18 => ![11274826767157612383, 0, 0]
  | 19 => ![11274826767157612383, 0, 0]
  | 20 => ![11274826767157612383, 0, 0]
  | 21 => ![11274826767157612383, 0, 0]
  | 22 => ![11274826767157612383, 0, 0]
  | 23 => ![11274826767157612383, 0, 0]
  | 24 => ![11274826767157612383, 0, 0]
  | 25 => ![11274826767157612383, 0, 0]
  | 26 => ![11274826767157612383, 0, 0]
  | 27 => ![11274826767157612383, 0, 0]
  | 28 => ![11274826767157612383, 0, 0]
  | 29 => ![11274826767157612383, 0, 0]
  | 30 => ![11274826767157612383, 0, 0]
  | _ => ![11274826767157612383, 0, 0]

/-- Each member's pre-switch table at `(0, a, true)`. -/
def preTop7 : Fin 32 → Fin 3 → ℤ := fun k =>
  match k.val with
  | 0 => ![11274826767181593151, 0, 0]
  | 1 => ![11274826767181593151, 0, 0]
  | 2 => ![11274826767181593151, 0, 0]
  | 3 => ![11274826767181593151, 0, 0]
  | 4 => ![11274826767181593151, 0, 0]
  | 5 => ![11274826767181593151, 0, 0]
  | 6 => ![11274826767181593151, 0, 0]
  | 7 => ![11274826767181593151, 0, 0]
  | 8 => ![11274826767181593151, 0, 0]
  | 9 => ![11274826767181593151, 0, 0]
  | 10 => ![11274826767181593151, 0, 0]
  | 11 => ![11274826767181593151, 0, 0]
  | 12 => ![11274826767181593151, 0, 0]
  | 13 => ![11274826767181593151, 0, 0]
  | 14 => ![11274826767181593151, 0, 0]
  | 15 => ![11274826767181593151, 0, 0]
  | 16 => ![11274826767181593151, 0, 0]
  | 17 => ![11274826767181593151, 0, 0]
  | 18 => ![11274826767181593151, 0, 0]
  | 19 => ![11274826767181593151, 0, 0]
  | 20 => ![11274826767181593151, 0, 0]
  | 21 => ![11274826767181593151, 0, 0]
  | 22 => ![11274826767181593151, 0, 0]
  | 23 => ![11274826767181593151, 0, 0]
  | 24 => ![11274826767181593151, 0, 0]
  | 25 => ![11274826767181593151, 0, 0]
  | 26 => ![11274826767181593151, 0, 0]
  | 27 => ![11274826767181593151, 0, 0]
  | 28 => ![11274826767181593151, 0, 0]
  | 29 => ![11274826767181593151, 0, 0]
  | 30 => ![11274826767181593151, 0, 0]
  | _ => ![11274826767181593151, 0, 0]

/-- Each member's in-epoch phase bound. -/
def eIn7 : Fin 32 → ℚ := fun k =>
  match k.val with
  | 0 => (1969396078201 / 2000000000000 : ℚ)
  | 1 => (4922115082633 / 5000000000000 : ℚ)
  | 2 => (4920715613331 / 5000000000000 : ℚ)
  | 3 => (9838582740063 / 10000000000000 : ℚ)
  | 4 => (9835683857119 / 10000000000000 : ℚ)
  | 5 => (9832733716101 / 10000000000000 : ℚ)
  | 6 => (9829731441733 / 10000000000000 : ℚ)
  | 7 => (9826676145033 / 10000000000000 : ℚ)
  | 8 => (4911783461573 / 5000000000000 : ℚ)
  | 9 => (4910201429593 / 5000000000000 : ℚ)
  | 10 => (9817183022069 / 10000000000000 : ℚ)
  | 11 => (9813906466359 / 10000000000000 : ℚ)
  | 12 => (98105722321 / 100000000000 : ℚ)
  | 13 => (1961435868933 / 2000000000000 : ℚ)
  | 14 => (9803726814593 / 10000000000000 : ℚ)
  | 15 => (1225026704679 / 1250000000000 : ℚ)
  | 16 => (979663879359 / 1000000000000 : ℚ)
  | 17 => (9793001248179 / 10000000000000 : ℚ)
  | 18 => (1957859990173 / 2000000000000 : ℚ)
  | 19 => (9785533835717 / 10000000000000 : ℚ)
  | 20 => (2445425455267 / 2500000000000 : ℚ)
  | 21 => (1222225351171 / 1250000000000 : ℚ)
  | 22 => (9773835687043 / 10000000000000 : ℚ)
  | 23 => (2442449831091 / 2500000000000 : ℚ)
  | 24 => (610355785957 / 625000000000 : ℚ)
  | 25 => (1220189284681 / 1250000000000 : ℚ)
  | 26 => (609828953237 / 625000000000 : ℚ)
  | 27 => (609558643919 / 625000000000 : ℚ)
  | 28 => (4874269108883 / 5000000000000 : ℚ)
  | 29 => (9744061767681 / 10000000000000 : ℚ)
  | 30 => (9739507706163 / 10000000000000 : ℚ)
  | _ => (2433718692461 / 2500000000000 : ℚ)

def post7Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X7 SZ (gFloorZ X7 SZ) (postTop7 k)
def pre7Z (k : Fin 32) : ℕ → Fin 3 → Bool → ℤ := fillZ (famZ k) DZ 11 X7 SZ vmax7Z (preTop7 k)

/-- Every check of member `k`, as one Boolean. -/
def chkE7Q (k : Fin 32) : Bool :=
  autoSolZ (famZ k) DZ 11 X7 SZ (post7Z k) && leTabZ 11 (post7Z k) vmax7Z &&
    preSolZ (famZ k) DZ 11 X7 SZ vmax7Z (pre7Z k) &&
    decide ((autoBoundZ (famZ k) DZ X7 SZ (post7Z k) : ℚ) ≤ eIn7 k * (X7.M DZ * SZ : ℤ)) &&
    decide ((autoBoundZ (famZ k) DZ X7 SZ (pre7Z k) : ℚ) ≤ (1969396078201 / 2000000000000 : ℚ) * (X7.M DZ * SZ : ℤ))

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

theorem solE7 : AutoSolE fam 11 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7).2.2 vpreI7 vpostI7 vmax7 := by
  rw [xgQ7]; exact (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).1

theorem heEall7 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpreI7 k) ≤ (1969396078201 / 2000000000000 : ℝ) := by
  rw [xgQ7]; exact fun k => ((oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.2 k).trans_eq (by push_cast; ring)

theorem heIn7 : ∀ k, autoBound (fam k) (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7).1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7).2.1 (xg (11619 / 10000 : ℝ) (16361 / 10000 : ℝ) (669 / 625 : ℝ) (1091 / 2000 : ℝ) (51 / 50 : ℝ) 7).2.2 (vpostI7 k) ≤ (eIn7 k : ℝ) := by
  rw [xgQ7]; exact (oneSwitchZ_sound famR famA DZ_pos X7R SZ_pos chkE7).2.1

end Cryptarchia.Prob.Certs.E20D11C
