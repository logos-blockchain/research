module

public import Cryptarchia.Prob.Next
import Cryptarchia.Settle.Mono
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Algebra.Order.Star.Real
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
import Mathlib.RingTheory.WittVector.IsPoly
import Mathlib.Tactic.ENatToNat
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
import Mathlib.Tactic.Polynomial.Basic
import Mathlib.Tactic.ReduceModChar
import Mathlib.Topology.Sheaves.Init

/-!
# The cold condition fails rarely

Fix an anchor phase `k0`. From `k0` on, run the bound process restarted with
margin = reach (`rf`), as in `cold_of_run`. A **failure** at phase `k ≥ k0` is a
phase that ends before `N`, at least `W` slots after phase `k0`, whose margin is
not cold for the next phase (`failK`).

`cold_anchor`: under a kernel within the band, the expected number of failures
anchored at `k0` is at most `C · (1 + b / (1 - λr))`, with

  `C = mz / (θ^W (1 - λp))`.

The proof is a supermartingale over phases (`Ex_phase`). Before `k0` it tracks
`c^ρ` (the reach bound, which has a stationary bound); after `k0` it tracks
`V(ρ, μ) · θ^(slots since k0)`, which contracts by `λp` per phase in expectation
(`ColdCert`), plus the failures so far.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle

variable {B : Band} {Δ : ℕ}

/-! ## The bound process from the anchor -/

variable (Δ) (M N W : ℕ)

/-- The reach bound at phase `k0`. -/
noncomputable def rho0 (w : CStr) (k0 : ℕ) : ℤ := (bnd Δ w 0 (gend Δ M w) k0).1

/-- The bound process restarted at phase `k0` with margin = reach. -/
noncomputable def rf (w : CStr) (k0 n : ℕ) : ℤ × ℤ :=
  runFrom (Δ := Δ) (w := w) 0 (gend Δ M w) k0 (rho0 Δ M w k0, rho0 Δ M w k0) n

variable {Δ M N W}

theorem bnd_fst_nonneg {w : CStr} {ℓ : ℕ} {e : ℕ → ℕ} : ∀ k, 0 ≤ (bnd Δ w ℓ e k).1
  | 0 => le_rfl
  | k + 1 => by
    simp only [bnd, step]
    exact le_trans (by positivity) (le_max_right _ _)

theorem rf_inv (w : CStr) (k0 : ℕ) : ∀ n, Inv (rf Δ M w k0 n)
  | 0 => inv_start (bnd_fst_nonneg k0)
  | n + 1 => by
    unfold rf at *
    simp only [runFrom]
    exact inv_step (rf_inv w k0 n)

/-! ## At the next phase end -/

section Next

variable {h h' : List Out} (hpe : PE Δ M h) (hlM : h.length < M) (hf : FirstPE Δ M h h')
include hpe hlM hf

theorem next_pidx : pidx Δ M (strOf h') h'.length = pidx Δ M (strOf h) h.length + 1 :=
  (firstPE_gend hpe hlM hf).2.2

theorem next_gend_last : gend Δ M (strOf h') (pidx Δ M (strOf h) h.length + 1) = h'.length :=
  (firstPE_gend hpe hlM hf).2.1

theorem next_gend {i : ℕ} (hi : i ≤ pidx Δ M (strOf h) h.length) :
    gend Δ M (strOf h') i = gend Δ M (strOf h) i :=
  (firstPE_gend hpe hlM hf).1 i hi

theorem next_sim : SimOn (strOf h') (strOf h) 0 h.length := simOn_prefix hf.pre 0

theorem gend_le_len {i : ℕ} (hi : i ≤ pidx Δ M (strOf h) h.length) :
    gend Δ M (strOf h) i ≤ h.length := by
  have := gend_pidx_pe hpe
  rw [← this]; exact gend_strictMono.monotone hi

theorem next_bnd {i : ℕ} (hi : i ≤ pidx Δ M (strOf h) h.length) :
    bnd Δ (strOf h') 0 (gend Δ M (strOf h')) i = bnd Δ (strOf h) 0 (gend Δ M (strOf h)) i := by
  apply bnd_congr2 gend_mono i
  · intro i' hi'; exact next_gend hpe hlM hf (by omega)
  · rw [next_gend hpe hlM hf hi]
    exact (next_sim hpe hlM hf).mono le_rfl (gend_le_len hpe hlM hf hi)

theorem next_bnd_succ :
    bnd Δ (strOf h') 0 (gend Δ M (strOf h')) (pidx Δ M (strOf h) h.length + 1) =
      step Δ (strOf h') 0 h.length h'.length
        (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) (pidx Δ M (strOf h) h.length)) := by
  simp only [bnd]
  rw [next_bnd hpe hlM hf le_rfl, next_gend hpe hlM hf le_rfl, gend_pidx_pe hpe,
    next_gend_last hpe hlM hf]

theorem next_rho0 {k0 : ℕ} (hk : k0 ≤ pidx Δ M (strOf h) h.length) :
    rho0 Δ M (strOf h') k0 = rho0 Δ M (strOf h) k0 := by
  unfold rho0; rw [next_bnd hpe hlM hf hk]

theorem next_rf {k0 n : ℕ} (hk : k0 + n ≤ pidx Δ M (strOf h) h.length) :
    rf Δ M (strOf h') k0 n = rf Δ M (strOf h) k0 n := by
  unfold rf
  rw [next_rho0 hpe hlM hf (by omega)]
  apply runFrom_congr2 gend_mono k0 _ n
  · intro i hi; exact next_gend hpe hlM hf (by omega)
  · rw [next_gend hpe hlM hf hk]
    exact (next_sim hpe hlM hf).mono le_rfl (gend_le_len hpe hlM hf hk)

theorem next_rf_succ {k0 : ℕ} (hk : k0 ≤ pidx Δ M (strOf h) h.length) :
    rf Δ M (strOf h') k0 (pidx Δ M (strOf h) h.length + 1 - k0) =
      step Δ (strOf h') 0 h.length h'.length
        (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0)) := by
  set j := pidx Δ M (strOf h) h.length with hj
  rw [show j + 1 - k0 = (j - k0) + 1 by omega]
  have hrf := next_rf hpe hlM hf (k0 := k0) (n := j - k0) (by omega)
  unfold rf at hrf ⊢
  simp only [runFrom]
  rw [hrf, show k0 + (j - k0) = j by omega, next_gend hpe hlM hf le_rfl, gend_pidx_pe hpe,
    show j + 1 = pidx Δ M (strOf h) h.length + 1 from rfl, next_gend_last hpe hlM hf]

end Next

/-! ## Expectations over the next phase -/

open Classical in
/-- `θ^L` on a crossing phase. -/
noncomputable def crossG (θ : ℝ) (m : ℕ) (h : List Out) : ℝ :=
  θ ^ (h.length - m) * (if Cross (strOf h) 0 m h.length then 1 else 0)

variable {κ : Kern}

/-! ## Pointwise bounds at the next phase end -/

theorem zpow_sub_ind {c : ℝ} (hc : 0 < c) (A : ℕ) (P : Prop) [Decidable P] :
    c ^ ((A : ℤ) - (if P then 1 else 0)) = c ^ A * (if P then c⁻¹ else 1) := by
  split_ifs
  · rw [zpow_sub₀ hc.ne', zpow_natCast, zpow_one, div_eq_mul_inv]
  · simp

theorem geom_le {r : ℝ} (h0 : 0 ≤ r) (h1 : r < 1) (n : ℕ) : ∑ i ∈ Finset.range n, r ^ i ≤ 1 / (1 - r) := by
  rw [geom_sum_eq (by linarith : r ≠ 1)]
  have hr : 0 < 1 - r := by linarith
  rw [show (r ^ n - 1) / (r - 1) = (1 - r ^ n) / (1 - r) by
    rw [← neg_sub, ← neg_sub (1 : ℝ) r, neg_div_neg_eq]]
  apply div_le_div_of_nonneg_right _ hr.le
  linarith [pow_nonneg h0 n]

/-- The pre-stage bound mixes `1` and the stationary bound. -/
theorem geom_mix {r b : ℝ} (h0 : 0 ≤ r) (h1 : r < 1) (hb : 1 ≤ b) (n : ℕ) :
    r ^ n + (b - r) * ∑ i ∈ Finset.range n, r ^ i ≤ 1 + (b - 1) / (1 - r) := by
  have hr : 0 < 1 - r := by linarith
  rw [geom_sum_eq (by linarith : r ≠ 1)]
  have hrn : r ^ n ≤ 1 := pow_le_one₀ h0 h1.le
  have hrn0 : 0 ≤ r ^ n := pow_nonneg h0 n
  rw [show (r ^ n - 1) / (r - 1) = (1 - r ^ n) / (1 - r) by
    rw [← neg_sub, ← neg_sub (1 : ℝ) r, neg_div_neg_eq]]
  have e1 : r ^ n + (b - r) * ((1 - r ^ n) / (1 - r)) = (r ^ n * (1 - r) + (b - r) * (1 - r ^ n)) / (1 - r) := by
    field_simp
  have e2 : 1 + (b - 1) / (1 - r) = (b - r) / (1 - r) := by
    field_simp; ring
  rw [e1, e2, div_le_div_iff_of_pos_right hr]
  nlinarith

end Cryptarchia.Prob
