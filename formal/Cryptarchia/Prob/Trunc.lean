module

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
public import Cryptarchia.Prob.Phases
public import Cryptarchia.Proof.FinalE
import Cryptarchia.Prob.Final

/-!
# The good event, cut at a horizon

The greedy phase ends `gend Δ M` cap the last phase at `M`. Below a smaller cap `Ms`
the ends agree with those for any larger cap `Mb` (`gend_agree`), and past it the
smaller cap's end is `Ms`, at most the larger cap's. So the lottery's good event with
the larger cap implies the one with the smaller cap (`good_trunc`), and with the smaller
cap the event is determined by the first `Ms` slots (`good_congr_cap`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open Settle

variable {Δ : ℕ} {w : CStr}

theorem nextE_agree {Ms Mb m : ℕ} (hm : m < Ms) (hMs : Ms ≤ Mb)
    (h : nextE Δ Ms w m < Ms ∨ nextE Δ Mb w m < Ms) : nextE Δ Ms w m = nextE Δ Mb w m := by
  classical
  unfold nextE at h ⊢
  by_cases hs : ∃ j, m < j ∧ j < Ms ∧ Quiet Δ w j
  · have hb : ∃ j, m < j ∧ j < Mb ∧ Quiet Δ w j :=
      ⟨Nat.find hs, (Nat.find_spec hs).1, lt_of_lt_of_le (Nat.find_spec hs).2.1 hMs, (Nat.find_spec hs).2.2⟩
    rw [dif_pos hs, dif_pos hb]
    have h1 : Nat.find hb ≤ Nat.find hs :=
      Nat.find_min' hb ⟨(Nat.find_spec hs).1, lt_of_lt_of_le (Nat.find_spec hs).2.1 hMs, (Nat.find_spec hs).2.2⟩
    have h2 : Nat.find hs ≤ Nat.find hb :=
      Nat.find_min' hs ⟨(Nat.find_spec hb).1, lt_of_le_of_lt h1 (Nat.find_spec hs).2.1, (Nat.find_spec hb).2.2⟩
    exact le_antisymm h2 h1
  · exfalso
    rw [dif_neg hs] at h
    by_cases hb : ∃ j, m < j ∧ j < Mb ∧ Quiet Δ w j
    · rw [dif_pos hb] at h
      rcases h with h | h
      · have := le_max_left Ms (m + 1); omega
      · exact hs ⟨Nat.find hb, (Nat.find_spec hb).1, h, (Nat.find_spec hb).2.2⟩
    · rw [dif_neg hb] at h
      rcases h with h | h
      · have := le_max_left Ms (m + 1); omega
      · have := le_max_left Mb (m + 1); omega

/-- **The phase ends agree below the smaller cap.** -/
theorem gend_agree {Ms Mb : ℕ} (hMs : Ms ≤ Mb) :
    ∀ k, (gend Δ Ms w k < Ms ∨ gend Δ Mb w k < Ms) → ∀ j ≤ k, gend Δ Ms w j = gend Δ Mb w j
  | 0, _, j, hj => by rw [Nat.le_zero.1 hj]; rfl
  | k + 1, h, j, hj => by
    have hs := gend_lt_succ (Δ := Δ) (M := Ms) (w := w) k
    have hb := gend_lt_succ (Δ := Δ) (M := Mb) (w := w) k
    have ih := gend_agree hMs k (by omega)
    have hk := ih k le_rfl
    rcases Nat.lt_or_ge j (k + 1) with hj' | hj'
    · exact ih j (by omega)
    · have : j = k + 1 := by omega
      subst this
      rw [gend_succ, gend_succ, hk]
      refine nextE_agree (by omega) hMs ?_
      rw [gend_succ, gend_succ, hk] at h
      exact h

/-- Past the smaller cap, its phase end is the cap, at most the larger cap's. -/
theorem gend_cap {Ms Mb : ℕ} (hMs : Ms ≤ Mb) {k : ℕ} (hk : gend Δ Ms w k < Ms)
    (h : Ms ≤ gend Δ Ms w (k + 1)) : gend Δ Ms w (k + 1) = Ms ∧ Ms ≤ gend Δ Mb w (k + 1) := by
  have hag := gend_agree (w := w) (Δ := Δ) hMs k (Or.inl hk) k le_rfl
  have h1 : gend Δ Ms w (k + 1) ≤ Ms := by rw [gend_succ]; exact nextE_le hk
  refine ⟨le_antisymm h1 h, ?_⟩
  by_contra hlt; push Not at hlt
  have := gend_agree (w := w) (Δ := Δ) hMs (k + 1) (Or.inr hlt) (k + 1) le_rfl
  omega

variable (E : Env)

/-- **The good event with the larger cap implies the one with the smaller cap**, for a
horizon below the smaller cap whose growth witnesses lie below it too. -/
theorem good_trunc {N Lw r G Ms Mb : ℕ} (hNs : N < Ms) (hMs : Ms ≤ Mb)
    (hgr : ∀ ep, 1 ≤ ep → E.c.fix ep ≤ N → E.c.cut ep + G < Ms)
    (hg : GoodLS E w N Lw (gend E.Δ Mb w) ∧ GrowthS E w (gend E.Δ Mb w) N r G) :
    GoodLS E w N Lw (gend E.Δ Ms w) ∧ GrowthS E w (gend E.Δ Ms w) N r G := by
  obtain ⟨⟨h0, -, hq, -, hcold, hwin⟩, hgr'⟩ := hg
  have hag : ∀ k, (gend E.Δ Ms w k < Ms ∨ gend E.Δ Mb w k < Ms) → ∀ j ≤ k, gend E.Δ Ms w j = gend E.Δ Mb w j :=
    gend_agree hMs
  refine ⟨⟨rfl, gend_mono, ?_, gend_unb, ?_, hwin⟩, ?_⟩
  · intro k hk
    rw [hag k (Or.inl (by omega)) k le_rfl]
    exact hq k (by rw [← hag k (Or.inl (by omega)) k le_rfl]; exact hk)
  · intro t k h1 h2 h3 h4
    have hk : gend E.Δ Ms w k < Ms := by omega
    have hagk := hag k (Or.inl hk)
    have hb : bnd E.Δ w (t - Lw) (gend E.Δ Ms w) k = bnd E.Δ w (t - Lw) (gend E.Δ Mb w) k :=
      bnd_congr2 (w' := w) gend_mono k hagk (fun _ _ _ => ⟨Iff.rfl, Iff.rfl, rfl⟩)
    rw [hb, hagk k le_rfl]
    by_cases hk1 : gend E.Δ Ms w (k + 1) < Ms
    · rw [hag (k + 1) (Or.inl hk1) (k + 1) le_rfl]
      exact hcold t k h1 h2 (by rw [← hagk k le_rfl]; exact h3) (by rw [← hag (k + 1) (Or.inl hk1) (k + 1) le_rfl]; exact h4)
    · push Not at hk1
      obtain ⟨he, hle⟩ := gend_cap hMs hk hk1
      have := hcold t k h1 h2 (by rw [← hagk k le_rfl]; exact h3) (by omega)
      have hadv : (advCnt w (gend E.Δ Mb w k) (gend E.Δ Ms w (k + 1)) : ℤ) ≤
          advCnt w (gend E.Δ Mb w k) (gend E.Δ Mb w (k + 1)) := by
        exact_mod_cast advCnt_mono_right (by omega)
      linarith
  · intro ep hep hfix
    obtain ⟨j, j1, j2, j3, j4⟩ := hgr' ep hep hfix
    have hj : gend E.Δ Mb w j < Ms := lt_of_le_of_lt j2 (hgr ep hep hfix)
    have hagj := hag j (Or.inr hj)
    refine ⟨j, by rw [hagj j le_rfl]; exact j1, by rw [hagj j le_rfl]; exact j2, ?_, j4⟩
    rw [bnd_congr2 (w' := w) gend_mono j hagj (fun _ _ _ => ⟨Iff.rfl, Iff.rfl, rfl⟩)]
    exact j3

/-- **`good_congr` with the horizon's growth witnesses bounded**: the good event with
cap `M` is determined by the first `M` slots, given `N < M` and growth witnesses below
`M`. -/
theorem good_congr_cap (hΔ : E.Δ = Δ) {w w' : CStr} {M : ℕ} (h : SimOn w w' 0 M)
    {N Lw r G : ℕ} (hNM : N < M) (hgr : ∀ ep, 1 ≤ ep → E.c.fix ep ≤ N → E.c.cut ep + G < M)
    (hg : GoodLS E w N Lw (gend Δ M w) ∧ GrowthS E w (gend Δ M w) N r G) :
    GoodLS E w' N Lw (gend Δ M w') ∧ GrowthS E w' (gend Δ M w') N r G := by
  have he : gend Δ M w = gend Δ M w' := funext (gend_congr_all h)
  rw [← he]
  obtain ⟨⟨h0, hmono, hq, hunb, hcold, hwin⟩, hgr'⟩ := hg
  refine ⟨⟨h0, hmono, ?_, hunb, ?_, ?_⟩, ?_⟩
  · intro k hk
    have := hq k hk
    rw [hΔ] at this ⊢
    exact (quiet_congr (h.mono (Nat.zero_le _) (by omega))).1 this
  · intro t k h1 h2 h3 h4
    have := hcold t k h1 h2 h3 h4
    have hk1 : gend Δ M w (k + 1) ≤ M := by
      rw [gend_succ]; exact nextE_le (by omega)
    rw [hΔ] at this ⊢
    rw [← bnd_congr gend_mono k (h.mono le_rfl (by have := gend_mono (Δ := Δ) (M := M) (w := w) k; omega)),
      ← advCnt_congr (h.mono (Nat.zero_le _) hk1)]
    exact this
  · intro t ht
    rw [← occCnt_congr (h.mono (Nat.zero_le _) (by omega))]
    exact hwin t ht
  · intro ep hep hfix
    obtain ⟨j, h1, h2, h3, h4⟩ := hgr' ep hep hfix
    have hcg := hgr ep hep hfix
    refine ⟨j, h1, h2, ?_, ?_⟩
    · rw [hΔ] at h3 ⊢
      rw [← bnd_congr gend_mono j (h.mono le_rfl (by omega))]
      exact h3
    · rw [hΔ] at h4 ⊢
      rw [← hD_congr (h.mono (Nat.zero_le _) (by unfold Config.fix at hfix ⊢; omega))]
      exact h4

end Cryptarchia.Prob
