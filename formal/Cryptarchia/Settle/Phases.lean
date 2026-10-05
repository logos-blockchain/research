import Cryptarchia.Settle.Recurrence

/-!
# Settlement from the phase recurrences

A **phase decomposition** of the characteristic string is an increasing sequence
of slots `e 0 = 0 ≤ e 1 ≤ …`, each followed by `Δ` quiet slots. Along it we
compute, from the string alone, an upper bound on reach and on margin
(`bnd`): the recurrences of Theorem 2 of Gaži–Ren–Russell, using whichever of the
proven upper bounds applies in each phase.

`bnd_sound`: the bounds hold for every PoS tree of the string.
`settled`: if the margin bound is cold at the start of a phase (below minus
the phase's adversarial slots), then at every time in that phase all dominant
chains share a vertex with label at least `ℓ`.
-/

namespace Cryptarchia.Settle

open Finset PTree

variable (Δ : ℕ) (w : CStr)

/-- The crossing-zero pattern in `(e0, e1]`: no adversarial slot, and a single
honest success, in a slot `≥ ℓ`. -/
def Cross (ℓ e0 e1 : ℕ) : Prop :=
  advCnt w e0 e1 = 0 ∧ ∃ s, e0 < s ∧ s ≤ e1 ∧ ℓ ≤ s ∧ (w s).1 = 1 ∧
    ∀ i, e0 < i → i ≤ e1 → i ≠ s → (w i).1 = 0

open Classical in
/-- One phase of the recurrences: `(reach bound, margin bound)` at `e0` ↦ at `e1`. -/
noncomputable def step (ℓ e0 e1 : ℕ) (b : ℤ × ℤ) : ℤ × ℤ :=
  let A : ℤ := advCnt w e0 e1
  let H : ℤ := hD Δ w e0 e1
  let ρ' := max (b.1 + A - H) A
  let μc := if b.2 < -A then b.2 + A - H else ρ'
  let μx := if Cross w ℓ e0 e1 then b.1 - H else ρ'
  (ρ', min ρ' (min μc μx))

/-- The bounds at the end of phase `k`. -/
noncomputable def bnd (ℓ : ℕ) (e : ℕ → ℕ) : ℕ → ℤ × ℤ
  | 0 => (0, 0)
  | k + 1 => step Δ w ℓ (e k) (e (k + 1)) (bnd ℓ e k)

variable {Δ w}

namespace PTree.Valid

variable {F : PTree} {n : ℕ} (hF : F.Valid Δ w n)
include hF

theorem RB_zero : RB Δ w 0 0 F := by
  intro u hu hl
  have hu0 : u = 0 := by
    by_contra h; have := hF.lab_pos u hu h; omega
  subst hu0
  have : F.hd (0 - Δ) = 0 := by
    apply le_antisymm _ (Nat.zero_le _)
    obtain ⟨v, hv, -, hlv, he⟩ := hF.hd_exists (0 - Δ)
    rw [← he]
    have : v = 0 := by by_contra h; have := hF.lab_pos v hv h; omega
    subst this; rw [hF.root_dep]
  unfold reach
  rw [hF.root_dep, this, hF.root_lab, advCnt_self]
  simp

theorem MB_of_RB {ℓ m : ℕ} {R : ℤ} (hR : RB Δ w R m F) : MB Δ w ℓ R m F :=
  fun u₁ hu₁ _ _ hl₁ _ _ => le_trans (min_le_left _ _) (hR u₁ hu₁ hl₁)

open Classical in
/-- **The bounds are sound**: at the end of every phase that the tree covers,
reach and margin are bounded by `bnd`. -/
theorem bnd_sound (ℓ : ℕ) (e : ℕ → ℕ) (he0 : e 0 = 0) (hmono : ∀ k, e k ≤ e (k + 1))
    (hq : ∀ k, e k ≤ n → Quiet Δ w (e k)) :
    ∀ k, e k ≤ n → RB Δ w (bnd Δ w ℓ e k).1 (e k) F ∧ MB Δ w ℓ (bnd Δ w ℓ e k).2 (e k) F := by
  intro k
  induction k with
  | zero =>
    intro _
    rw [he0]
    exact ⟨hF.RB_zero, hF.MB_of_RB hF.RB_zero⟩
  | succ k ih =>
    intro hk
    obtain ⟨hR, hM⟩ := ih (le_trans (hmono k) hk)
    have hqk := hq k (le_trans (hmono k) hk)
    have hqk1 := hq (k + 1) hk
    have hR' := hF.reach_step hqk hqk1 (hmono k) hk hR
    simp only [bnd, step]
    refine ⟨hR', ?_⟩
    set b := bnd Δ w ℓ e k
    -- the margin bound is the least of the applicable bounds
    have h1 : MB Δ w ℓ (max (b.1 + advCnt w (e k) (e (k + 1)) - hD Δ w (e k) (e (k + 1)))
        (advCnt w (e k) (e (k + 1)))) (e (k + 1)) F := hF.MB_of_RB hR'
    have h2 : MB Δ w ℓ (if b.2 < -(advCnt w (e k) (e (k + 1)) : ℤ) then
        b.2 + advCnt w (e k) (e (k + 1)) - hD Δ w (e k) (e (k + 1)) else
        max (b.1 + advCnt w (e k) (e (k + 1)) - hD Δ w (e k) (e (k + 1)))
          (advCnt w (e k) (e (k + 1)))) (e (k + 1)) F := by
      split
      · exact hF.margin_cold hqk hqk1 (hmono k) hk hM (by assumption)
      · exact h1
    have h3 : MB Δ w ℓ (if Cross w ℓ (e k) (e (k + 1)) then b.1 - hD Δ w (e k) (e (k + 1)) else
        max (b.1 + advCnt w (e k) (e (k + 1)) - hD Δ w (e k) (e (k + 1)))
          (advCnt w (e k) (e (k + 1)))) (e (k + 1)) F := by
      split
      · rename_i hc
        obtain ⟨hA, s, hs0, hs1, hsℓ, hsw, hoth⟩ := hc
        exact hF.margin_cross hqk hqk1 (hmono k) hk hR hA ⟨hs0, hs1⟩ hsℓ hsw hoth
      · exact h1
    intro u₁ hu₁ u₂ hu₂ hl₁ hl₂ hns
    have := h1 u₁ hu₁ u₂ hu₂ hl₁ hl₂ hns
    have := h2 u₁ hu₁ u₂ hu₂ hl₁ hl₂ hns
    have := h3 u₁ hu₁ u₂ hu₂ hl₁ hl₂ hns
    simp only [le_min_iff]
    omega

/-- A vertex is **dominant at time `m`** if it is at least as deep as every
honest vertex at least `Δ` slots old: what an honest party at the end of slot
`m` may be made to adopt. -/
def Dom (F : PTree) (Δ m v : ℕ) : Prop := v ∈ F.V ∧ F.lab v ≤ m ∧ F.hd (m - Δ) ≤ F.dep v

omit hF in
/-- **Settlement within a cold phase.** If the margin bound at the start of phase
`k` is below minus the phase's adversarial slots, then any two chains with last
labels up to the end of the phase that are at least as deep as the honest depth
at the start of the phase, `hd (e k - Δ)`, share a vertex with label at least
`ℓ`. This covers every chain dominant at any time of the phase. -/
theorem settled (hF : F.Valid Δ w n) (ℓ : ℕ) (e : ℕ → ℕ) (he0 : e 0 = 0)
    (hmono : ∀ k, e k ≤ e (k + 1)) (hq : ∀ k, e k ≤ n → Quiet Δ w (e k)) (k m : ℕ) (hkm : e k ≤ m)
    (hm1 : m ≤ e (k + 1)) (hmn : m ≤ n)
    (hcold : (bnd Δ w ℓ e k).2 < -(advCnt w (e k) (e (k + 1)) : ℤ)) {v₁ v₂ : ℕ}
    (hv₁ : v₁ ∈ F.V) (hv₂ : v₂ ∈ F.V) (hl₁ : F.lab v₁ ≤ m) (hl₂ : F.lab v₂ ≤ m)
    (hd₁ : F.hd (e k - Δ) ≤ F.dep v₁) (hd₂ : F.hd (e k - Δ) ≤ F.dep v₂) : F.Sim ℓ v₁ v₂ := by
  by_contra hns
  obtain ⟨-, hM⟩ := hF.bnd_sound ℓ e he0 hmono hq k (le_trans hkm hmn)
  have hA : advCnt w (e k) m ≤ advCnt w (e k) (e (k + 1)) := advCnt_mono_right hm1
  exact hF.no_violation (hq k (le_trans hkm hmn)) hM hkm (by omega) hv₁ hv₂ hl₁ hl₂ hns hd₁ hd₂

omit hF in
/-- The same, for chains dominant at a time `m` of the phase. -/
theorem settled_dom (hF : F.Valid Δ w n) (ℓ : ℕ) (e : ℕ → ℕ) (he0 : e 0 = 0)
    (hmono : ∀ k, e k ≤ e (k + 1)) (hq : ∀ k, e k ≤ n → Quiet Δ w (e k)) (k m : ℕ) (hkm : e k ≤ m)
    (hm1 : m ≤ e (k + 1)) (hmn : m ≤ n)
    (hcold : (bnd Δ w ℓ e k).2 < -(advCnt w (e k) (e (k + 1)) : ℤ)) {v₁ v₂ : ℕ}
    (h₁ : Dom F Δ m v₁) (h₂ : Dom F Δ m v₂) : F.Sim ℓ v₁ v₂ := by
  have hhd : F.hd (e k - Δ) ≤ F.hd (m - Δ) := hF.hd_mono (by omega)
  exact settled hF ℓ e he0 hmono hq k m hkm hm1 hmn hcold h₁.1 h₂.1 h₁.2.1 h₂.2.1
    (hhd.trans h₁.2.2) (hhd.trans h₂.2.2)

end PTree.Valid

end Cryptarchia.Settle
