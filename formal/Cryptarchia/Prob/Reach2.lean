module

public import Cryptarchia.Prob.Cold2
import Cryptarchia.Prob.Fail2
import Cryptarchia.Settle.Mono
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
import Mathlib.RingTheory.WittVector.IsPoly
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
import Std.Tactic.BVDecide.Normalize.BitVec

/-!
# The reach bound stays small (with the automaton certificate)

`reach_tail2`: at any fixed phase index `j0`, `E[c^ρ] ≤ 1 + b / (1 - λr)`, where `ρ`
is the reach bound there (`c^ρ` is the reach-only part of the cold potential).
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle

variable {B : Band} {Δ M : ℕ} {κ : Kern}

variable (Δ M) in
/-- `c^ρ` at phase `j0`, once the history has reached it. -/
noncomputable def reachH2 (c : ℝ) (j0 : ℕ) (h : List Out) : ℝ :=
  if j0 ≤ pidx Δ M (strOf h) h.length then c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j0).1 else 0

variable (Δ M) in
/-- The potential. -/
noncomputable def Φr2 (P : Cert2 B Δ) (j0 : ℕ) (h : List Out) : ℝ :=
  if pidx Δ M (strOf h) h.length < j0 then
    P.lr ^ (j0 - pidx Δ M (strOf h) h.length) *
      P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) (pidx Δ M (strOf h) h.length)).1 +
      (P.b - P.lr) * ∑ i ∈ Finset.range (j0 - pidx Δ M (strOf h) h.length), P.lr ^ i
  else P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j0).1

theorem phiR2_step (P : Cert2 B Δ)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (j0 : ℕ) {h : List Out}
    (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φr2 Δ M P j0) h ≤ Φr2 Δ M P j0 h := by
  classical
  have hc0 : 0 < P.c := by linarith [P.hc]
  obtain ⟨j, hj⟩ : ∃ j, pidx Δ M (strOf h) h.length = j := ⟨_, rfl⟩
  by_cases hjk : j < j0
  · obtain ⟨ρ, hρ⟩ : ∃ ρ, (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j).1 = ρ := ⟨_, rfl⟩
    have hρ0 : 0 ≤ ρ := by rw [← hρ]; exact bnd_fst_nonneg j
    obtain ⟨n, hn⟩ : ∃ n, j0 - j = n := ⟨_, rfl⟩
    have hn1 : 1 ≤ n := by omega
    have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φr2 Δ M P j0) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => P.lr ^ (n - 1) *
          (if 1 ≤ ρ then P.c ^ ρ * WP P 0 h.length h' else WP P 1 h.length h') +
            (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i) h := by
      refine ExPh_mono_first hlM fun h' hf => ?_
      have hp' := next_pidx hpe hlM hf
      have hbs := next_bnd_succ hpe hlM hf
      rw [hj] at hp' hbs
      obtain ⟨ρ', hρ'⟩ : ∃ ρ', (bnd Δ (strOf h') 0 (gend Δ M (strOf h')) (j + 1)).1 = ρ' := ⟨_, rfl⟩
      have hcr : P.c ^ ρ' ≤ (if 1 ≤ ρ then P.c ^ ρ * WP P 0 h.length h' else WP P 1 h.length h') := by
        have := c_pow_reach (Δ := Δ) (w := strOf h') (ℓ := 0) (a := h.length) (b := h'.length) P.hc
          (st := bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j) (by rw [hρ]; exact hρ0) (bnd_le 0 _ j)
        rw [← hρ', hbs]
        rw [hρ] at this
        obtain ⟨A, hA⟩ : ∃ A, advCnt (strOf h') h.length h'.length = A := ⟨_, rfl⟩
        obtain ⟨nh, hnh⟩ : ∃ nh, honCnt (strOf h') h.length h'.length = nh := ⟨_, rfl⟩
        have hiff : HonIn (strOf h') h.length h'.length ↔ 1 ≤ nh := by rw [← hnh]; exact honIn_iff_honCnt
        rw [hA] at this
        by_cases h1 : 1 ≤ ρ
        · rw [if_pos h1] at this
          rw [if_pos h1, WP_val' P 0 (by decide) h.length h' hA hnh, xg_0]
          refine this.trans (le_of_eq ?_)
          simp only [xgN, gtab]
          by_cases hb : HonIn (strOf h') h.length h'.length
          · rw [if_pos hb, zpow_sub₀ hc0.ne', zpow_natCast, zpow_one, div_eq_mul_inv]
            simp [hiff.1 hb]
          · rw [if_neg hb]; simp [show ¬ 1 ≤ nh from fun h'' => hb (hiff.2 h'')]
        · rw [if_neg h1] at this
          rw [if_neg h1, WP_val' P 1 (by decide) h.length h' hA hnh, xg_1]
          refine this.trans (le_of_eq ?_)
          simp [xgN]
      have hval : Φr2 Δ M P j0 h' ≤ P.lr ^ (n - 1) * P.c ^ ρ' + (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i := by
        unfold Φr2
        rw [hp']
        by_cases hjk' : j + 1 < j0
        · rw [if_pos hjk', show j0 - (j + 1) = n - 1 by omega, hρ']
        · rw [if_neg hjk', show j0 = j + 1 by omega, show n - 1 = 0 by omega, hρ']
          simp
      refine hval.trans ?_
      have := mul_le_mul_of_nonneg_left hcr (pow_nonneg P.hlr0 (n - 1))
      linarith
    refine hle.trans ?_
    have hS : ∑ i ∈ Finset.range n, P.lr ^ i = ∑ i ∈ Finset.range (n - 1), P.lr ^ i + P.lr ^ (n - 1) := by
      rw [show n = (n - 1) + 1 by omega, Finset.sum_range_succ, Nat.add_sub_cancel]
    have hval : Φr2 Δ M P j0 h = P.lr ^ n * P.c ^ ρ + (P.b - P.lr) * ∑ i ∈ Finset.range n, P.lr ^ i := by
      unfold Φr2; rw [hj, if_pos hjk, hn, hρ]
    rw [hval, ExPh_add, ExPh_const, ExPh_mul_const]
    have hcρ : 0 ≤ P.c ^ ρ := zpow_nonneg hc0.le _
    have hlrn : 0 ≤ P.lr ^ (n - 1) := pow_nonneg P.hlr0 _
    have hpow : P.lr ^ n = P.lr ^ (n - 1) * P.lr := by
      rw [← pow_succ, show n - 1 + 1 = n by omega]
    split_ifs with h1
    · rw [ExPh_mul_const]
      have h2 := hR0 h hpe hlM
      have := mul_le_mul_of_nonneg_left h2 hcρ
      have := mul_le_mul_of_nonneg_left this hlrn
      rw [hS, hpow]
      have hbl : 0 ≤ P.b - P.lr := by linarith [P.hb1, P.hlr1]
      nlinarith [mul_nonneg hbl hlrn]
    · have h2 := hR1 h hpe hlM
      have := mul_le_mul_of_nonneg_left h2 hlrn
      have hc1 : P.c ^ ρ = 1 := by rw [show ρ = 0 by omega, zpow_zero]
      rw [hS, hpow, hc1]
      nlinarith
  · push Not at hjk
    refine ExPh_le_first hlM fun h' hf => ?_
    have hp' := next_pidx hpe hlM hf
    have hb := next_bnd hpe hlM hf (i := j0) (by rw [hj]; exact hjk)
    rw [hj] at hp'
    unfold Φr2
    rw [hp', hj, if_neg (by omega), if_neg (by omega), hb]

/-- Before the anchor `j0`, a function at most `F · Φr2` at the next phase end
contracts as `Φr2` does. -/
theorem phiR2_pre (P : Cert2 B Δ)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (j0 : ℕ) {h : List Out} (hpe : PE Δ M h) (hlM : h.length < M) {F : ℝ} (hF : 0 ≤ F) {Φ : List Out → ℝ}
    (hΦ : ∀ h', FirstPE Δ M h h' → Φ h' ≤ F * Φr2 Δ M P j0 h') :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) Φ h ≤ F * Φr2 Δ M P j0 h := by
  refine (ExPh_mono_first hlM hΦ).trans ?_
  rw [ExPh_mul_const]; exact mul_le_mul_of_nonneg_left (phiR2_step P hR0 hR1 j0 hpe hlM) hF

theorem Φr2_nonneg (P : Cert2 B Δ) (j0 : ℕ) (h : List Out) : 0 ≤ Φr2 Δ M P j0 h := by
  have hc0 : 0 < P.c := by linarith [P.hc]
  unfold Φr2; split_ifs
  · apply add_nonneg (mul_nonneg (pow_nonneg P.hlr0 _) (zpow_nonneg hc0.le _))
    exact mul_nonneg (by linarith [P.hb1, P.hlr1]) (Finset.sum_nonneg fun i _ => pow_nonneg P.hlr0 _)
  · exact zpow_nonneg hc0.le _

theorem reachH2_le_phi (P : Cert2 B Δ) (j0 : ℕ) (h : List Out) : reachH2 Δ M P.c j0 h ≤ Φr2 Δ M P j0 h := by
  unfold reachH2
  split_ifs with h1
  · unfold Φr2; rw [if_neg (by omega)]
  · exact Φr2_nonneg P j0 h

/-- The potential at genesis. -/
theorem Φr2_nil_le (P : Cert2 B Δ) (j0 : ℕ) : Φr2 Δ M P j0 [] ≤ 1 + (P.b - 1) / (1 - P.lr) := by
  have hp0 : pidx Δ M (strOf []) ([] : List Out).length = 0 := by
    apply Nat.eq_zero_of_le_zero
    exact pidx_le_of (by simp [gend_zero])
  unfold Φr2
  rw [hp0]
  have hb0 : (bnd Δ (strOf []) 0 (gend Δ M (strOf [])) 0).1 = 0 := rfl
  split_ifs with h1
  · rw [hb0, zpow_zero, mul_one, Nat.sub_zero]
    exact geom_mix P.hlr0 P.hlr1 P.hb1 j0
  · have hj : j0 = 0 := by omega
    subst hj
    rw [hb0, zpow_zero]
    have : 0 ≤ (P.b - 1) / (1 - P.lr) := div_nonneg (by linarith [P.hb1]) (by linarith [P.hlr1])
    linarith

/-- **The reach bound at any phase has a uniform exponential moment.** -/
theorem reach_tail2' (P : Cert2 B Δ)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (hM : 0 < M) (j0 : ℕ) :
    Ex κ M (reachH2 Δ M P.c j0) [] ≤ 1 + (P.b - 1) / (1 - P.lr) := by
  calc Ex κ M (reachH2 Δ M P.c j0) [] ≤ Ex κ M (Φr2 Δ M P j0) [] := Ex_mono M (reachH2_le_phi P j0) []
    _ ≤ Φr2 Δ M P j0 [] := by
        have := Ex_phase (κ := κ) (PE Δ M) (Φ := Φr2 Δ M P j0) (M := M)
          (fun h hpe hlM => phiR2_step P hR0 hR1 j0 hpe hlM) (pe_nil hM) (by simp)
        simpa using this
    _ ≤ _ := Φr2_nil_le P j0

end Cryptarchia.Prob
