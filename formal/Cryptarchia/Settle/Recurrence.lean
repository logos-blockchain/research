import Cryptarchia.Settle.TreeBasic

/-!
# Phase recurrences for reach and margin

Gaži–Ren–Russell, Theorem 2 (the PoS phase recurrences), upper bounds:
Lemmas 11/12 (reach), 14 (margin in the cold region), 15 (crossing zero), and a
lemma the paper does not state: **no violation inside a phase** whose margin
starts cold (`no_violation`). The paper checks margin at phase ends only; a
violation, two diverging chains that honest parties may adopt, can happen at any
time, and `no_violation` rules it out for every time within the phase.

Everything is stated for one tree `F`, a PoS tree for the first `n` slots, looked
at the ends `n0 ≤ n1` of consecutive phases (both followed by `Δ` quiet slots).
The quantities at time `m` only involve vertices with label `≤ m`, so the tree of
the whole execution serves for every time.

* `RB R m F`: every chain of `F` with last label `≤ m` has reach at most `R` at `m`.
* `MB ℓ M m F`: every two such chains that do not share a vertex with label
  `≥ ℓ` have the smaller reach at most `M` at `m` (margin).
-/

namespace Cryptarchia.Settle

open Finset PTree

variable {Δ : ℕ} {w : CStr}

/-- Reach bound at time `m`. -/
def RB (Δ : ℕ) (w : CStr) (R : ℤ) (m : ℕ) (F : PTree) : Prop :=
  ∀ u ∈ F.V, F.lab u ≤ m → reach Δ w F m u ≤ R

/-- Margin bound at time `m`, for divergence before slot `ℓ`. -/
def MB (Δ : ℕ) (w : CStr) (ℓ : ℕ) (M : ℤ) (m : ℕ) (F : PTree) : Prop :=
  ∀ u₁ ∈ F.V, ∀ u₂ ∈ F.V, F.lab u₁ ≤ m → F.lab u₂ ≤ m → ¬ F.Sim ℓ u₁ u₂ →
    min (reach Δ w F m u₁) (reach Δ w F m u₂) ≤ M

namespace PTree.Valid

variable {F : PTree} {n : ℕ} (hF : F.Valid Δ w n)
include hF

/-- Reach does not grow along an adversarial segment. -/
theorem reach_le_of_adv {u v m : ℕ} (hv : v ∈ F.V) (hanc : F.Anc u v) (hlv : F.lab v ≤ m)
    (hadv : ∀ j < F.dep v - F.dep u, F.hon (F.par^[j] v) = false) :
    reach Δ w F m v ≤ reach Δ w F m u := by
  have hlen := hF.adv_path_le _ u v hv hanc rfl hadv
  have hlu := hF.anc_lab_le hanc hv
  have hsplit := advCnt_add (w := w) hlu hlv
  unfold reach
  have := hanc.1
  push_cast
  omega

/-- The last honest ancestor with label at most `m`: every honest vertex after
it on the chain has a later label. -/
theorem last_honest_le (m : ℕ) {v : ℕ} (hv : v ∈ F.V) :
    ∃ z, F.hon z = true ∧ F.lab z ≤ m ∧ F.Anc z v ∧
      ∀ j < F.dep v - F.dep z, F.hon (F.par^[j] v) = true → m < F.lab (F.par^[j] v) := by
  induction h : F.dep v generalizing v with
  | zero =>
    have := (hF.dep_eq_zero hv).1 h; subst this
    exact ⟨0, hF.root_hon, by rw [hF.root_lab]; omega, anc_refl 0, by intro j hj; omega⟩
  | succ d ih =>
    by_cases hh : F.hon v = true ∧ F.lab v ≤ m
    · exact ⟨v, hh.1, hh.2, anc_refl v, by intro j hj; omega⟩
    have h0 : v ≠ 0 := by
      rintro rfl; exact hh ⟨hF.root_hon, by rw [hF.root_lab]; omega⟩
    have hdp : F.dep (F.par v) = d := by rw [hF.dep_succ v hv h0] at h; omega
    obtain ⟨z, hz, hzl, hanc, hafter⟩ := ih (hF.par_mem v hv) hdp
    refine ⟨z, hz, hzl, anc_trans hanc (hF.anc_par hv), ?_⟩
    intro j hj hhon
    rcases j with _ | j
    · simp only [Function.iterate_zero_apply] at hhon ⊢
      by_contra hle; exact hh ⟨hhon, by omega⟩
    · rw [Function.iterate_succ_apply] at hhon ⊢
      exact hafter j (by omega) hhon

/-- **The core counting step.** Let `z` be the last honest ancestor of `v` with
label at most `n0`, the end of a phase (followed by a quiet period), and let
`lab v ≤ m`. If `z`'s reach at `n0` is below `-advCnt (n0, m]`, then no honest
vertex follows `z` on `v`'s chain, and `v` is at most as deep as `z` plus the
adversarial slots after `z` up to `m`. -/
theorem core {n0 m z v : ℕ} (hq : Quiet Δ w n0) (hn0m : n0 ≤ m) (hv : v ∈ F.V)
    (hlv : F.lab v ≤ m) (hz : F.hon z = true) (hzl : F.lab z ≤ n0) (hanc : F.Anc z v)
    (hafter : ∀ j < F.dep v - F.dep z, F.hon (F.par^[j] v) = true → n0 < F.lab (F.par^[j] v))
    (hr : reach Δ w F n0 z < -(advCnt w n0 m : ℤ)) :
    (∀ j < F.dep v - F.dep z, F.hon (F.par^[j] v) = false) ∧
      F.dep v ≤ F.dep z + advCnt w (F.lab z) n0 + advCnt w n0 m := by
  have hsplit (b : ℕ) (hb1 : n0 ≤ b) (hb2 : b ≤ m) :
      advCnt w (F.lab z) b ≤ advCnt w (F.lab z) n0 + advCnt w n0 m := by
    rw [← advCnt_add hzl hb1]; have := advCnt_mono_right (w := w) (a := n0) hb2; omega
  have hsplit' (b : ℕ) (hb2 : b ≤ m) :
      advCnt w (F.lab z) b ≤ advCnt w (F.lab z) n0 + advCnt w n0 m := by
    rcases le_total b n0 with hb | hb
    · have := advCnt_mono_right (w := w) (a := F.lab z) hb; omega
    · exact hsplit b hb hb2
  have hadv : ∀ j < F.dep v - F.dep z, F.hon (F.par^[j] v) = false := by
    by_contra hcon
    push Not at hcon
    -- the honest vertex after `z` closest to `z`
    let S := (range (F.dep v - F.dep z)).filter (fun j => F.hon (F.par^[j] v) = true)
    have hS : S.Nonempty := by
      obtain ⟨j, hj, hjh⟩ := hcon
      exact ⟨j, mem_filter.2 ⟨mem_range.2 hj, by simpa using hjh⟩⟩
    set k := S.max' hS with hk
    have hkS := S.max'_mem hS
    rw [← hk] at hkS
    simp only [S, mem_filter, mem_range] at hkS
    obtain ⟨hkr, hkh⟩ := hkS
    have hmax : ∀ j, k < j → j < F.dep v - F.dep z → F.hon (F.par^[j] v) = false := by
      intro j hkj hj
      by_contra hne
      have : j ∈ S := mem_filter.2 ⟨mem_range.2 hj, by simpa using hne⟩
      have := S.le_max' j this
      omega
    set y := F.par^[k] v with hy
    have hym : y ∈ F.V := hF.iter_mem hv k
    have hyl : n0 < F.lab y := hafter k hkr hkh
    have hy0 : y ≠ 0 := by rintro h; rw [h, hF.root_lab] at hyl; omega
    -- `y` is deeper than every honest vertex up to `n0`
    have hdeep := hF.dep_gt_hd hq hym hkh hyl
    -- the segment from `par y` down to `z` is adversarial
    have hdv := hanc.1
    have hdepk : F.dep y = F.dep v - k := hF.dep_iter hv k
    have hpy : F.par y = F.par^[k + 1] v := by rw [hy, Function.iterate_succ_apply']
    have hdpy : F.dep (F.par y) = F.dep v - (k + 1) := by rw [hpy, hF.dep_iter hv]
    have hancz : F.Anc z (F.par y) := by
      refine ⟨by omega, ?_⟩
      rw [hpy, ← Function.iterate_add_apply]
      have : F.dep (F.par^[k + 1] v) - F.dep z + (k + 1) = F.dep v - F.dep z := by
        rw [hF.dep_iter hv]; omega
      rw [this]; exact hanc.2
    have hseg := hF.adv_path_le _ z (F.par y) (hF.par_mem y hym) hancz rfl (by
      intro j hj
      rw [hpy, ← Function.iterate_add_apply]
      exact hmax (j + (k + 1)) (by omega) (by rw [hdpy] at hj; omega))
    have hlpy : F.lab (F.par y) ≤ m := by
      have := hF.lab_iter_le hv (k + 1); rw [← hpy] at this; omega
    have := hsplit' (F.lab (F.par y)) hlpy
    rw [hF.dep_succ y hym hy0] at hdeep
    unfold reach at hr
    rw [hF.hd_quiet hq] at hr
    push_cast at hr
    omega
  refine ⟨hadv, ?_⟩
  have hlen := hF.adv_path_le _ z v hv hanc rfl hadv
  have := hsplit' (F.lab v) hlv
  have := hanc.1
  omega

variable {n0 n1 : ℕ} (hq0 : Quiet Δ w n0) (hq1 : Quiet Δ w n1) (h01 : n0 ≤ n1) (h1n : n1 ≤ n)
include hq0 hq1 h01 h1n

/-- Honest depth at the end of the phase. -/
theorem hd_phase : F.hd (n0 - Δ) + hD Δ w n0 n1 ≤ F.hd (n1 - Δ) := by
  rw [hF.hd_quiet hq0, hF.hd_quiet hq1]
  exact hF.hd_growth hq0 n1 h01 h1n

/-- A chain that ends before the phase: its reach changes by `A - H` at most. -/
theorem reach_old {u : ℕ} (hlu : F.lab u ≤ n0) :
    reach Δ w F n1 u ≤ reach Δ w F n0 u + advCnt w n0 n1 - hD Δ w n0 n1 := by
  have h := hF.hd_phase hq0 hq1 h01 h1n
  have hs := advCnt_add (w := w) hlu h01
  unfold reach
  push_cast
  omega

omit hq0 in
/-- A chain whose last honest vertex is inside the phase has reach at most `A`. -/
theorem reach_new {u : ℕ} (hu : u ∈ F.V) (hh : F.hon u = true) (hlu : n0 < F.lab u)
    (hlu1 : F.lab u ≤ n1) : reach Δ w F n1 u ≤ advCnt w n0 n1 := by
  have hd := hF.le_hd hu hh hlu1
  rw [← hF.hd_quiet hq1] at hd
  have := advCnt_mono_left (w := w) (c := n1) hlu.le
  unfold reach
  omega

/-- **Reach recurrence** (Lemmas 11–12, upper bounds). -/
theorem reach_step {R : ℤ} (hR : RB Δ w R n0 F) :
    RB Δ w (max (R + advCnt w n0 n1 - hD Δ w n0 n1) (advCnt w n0 n1)) n1 F := by
  intro v hv hlv
  obtain ⟨u, hu, hanc, hadv⟩ := hF.last_honest hv
  have h1 := hF.reach_le_of_adv hv hanc hlv hadv
  have hum := hF.anc_mem hanc hv
  rcases le_or_gt (F.lab u) n0 with hl | hl
  · have := hF.reach_old hq0 hq1 h01 h1n hl
    have := hR u hum hl
    exact le_trans h1 (le_trans (by omega) (le_max_left _ _))
  · have := hF.reach_new hq1 h01 h1n hum hu hl ((hF.anc_lab_le hanc hv).trans hlv)
    exact le_trans h1 (le_trans this (le_max_right _ _))

/-- **Margin in the cold region** (Lemma 14). -/
theorem margin_cold {ℓ : ℕ} {M : ℤ} (hM : MB Δ w ℓ M n0 F) (hcold : M < -(advCnt w n0 n1 : ℤ)) :
    MB Δ w ℓ (M + advCnt w n0 n1 - hD Δ w n0 n1) n1 F := by
  intro v₁ hv₁ v₂ hv₂ hl₁ hl₂ hns
  obtain ⟨z₁, hz₁, hzl₁, hanc₁, haft₁⟩ := hF.last_honest_le n0 hv₁
  obtain ⟨z₂, hz₂, hzl₂, hanc₂, haft₂⟩ := hF.last_honest_le n0 hv₂
  have hns' : ¬ F.Sim ℓ z₁ z₂ := fun h => hns (sim_of_anc hanc₁ hanc₂ h)
  have hmin := hM z₁ (hF.anc_mem hanc₁ hv₁) z₂ (hF.anc_mem hanc₂ hv₂) hzl₁ hzl₂ hns'
  -- the chain whose restriction is behind gets no honest extension
  have key : ∀ {z v : ℕ}, v ∈ F.V → F.lab v ≤ n1 → F.hon z = true → F.lab z ≤ n0 → F.Anc z v →
      (∀ j < F.dep v - F.dep z, F.hon (F.par^[j] v) = true → n0 < F.lab (F.par^[j] v)) →
      reach Δ w F n0 z ≤ M → reach Δ w F n1 v ≤ M + advCnt w n0 n1 - hD Δ w n0 n1 := by
    intro z v hv hlv hz hzl hanc haft hr
    obtain ⟨hadv, -⟩ := hF.core hq0 h01 hv hlv hz hzl hanc haft (by omega)
    have := hF.reach_le_of_adv hv hanc hlv hadv
    have := hF.reach_old hq0 hq1 h01 h1n hzl
    omega
  rcases le_total (reach Δ w F n0 z₁) (reach Δ w F n0 z₂) with h | h
  · rw [min_eq_left h] at hmin
    exact le_trans (min_le_left _ _) (key hv₁ hl₁ hz₁ hzl₁ hanc₁ haft₁ hmin)
  · rw [min_eq_right h] at hmin
    exact le_trans (min_le_right _ _) (key hv₂ hl₂ hz₂ hzl₂ hanc₂ haft₂ hmin)

/-- **Crossing zero** (Lemma 15, generalized). A phase with no adversarial slot
and a single honest vertex, in a slot `≥ ℓ`: every pair of diverging chains has
one chain entirely before the phase, whose reach drops by `h_Δ ≥ 1`. -/
theorem margin_cross {ℓ s : ℕ} {R : ℤ} (hR : RB Δ w R n0 F) (hA : advCnt w n0 n1 = 0)
    (hs : n0 < s ∧ s ≤ n1) (hsℓ : ℓ ≤ s) (hs1 : (w s).1 = 1)
    (hothers : ∀ i, n0 < i → i ≤ n1 → i ≠ s → (w i).1 = 0) :
    MB Δ w ℓ (R - hD Δ w n0 n1) n1 F := by
  -- the phase holds exactly one vertex: the honest vertex in slot `s`
  have hnew : ∀ v ∈ F.V, n0 < F.lab v → F.lab v ≤ n1 → F.hon v = true ∧ F.lab v = s := by
    intro v hv hl1 hl2
    by_cases hh : F.hon v = true
    · have h0 : v ≠ 0 := by rintro rfl; rw [hF.root_lab] at hl1; omega
      have := hF.hon_slot hv hh h0
      refine ⟨hh, ?_⟩
      by_contra hne
      exact absurd (hothers _ hl1 hl2 hne) (by omega)
    · exfalso
      have hadv := hF.advSlot v hv (by simpa using hh)
      have : 0 < advCnt w n0 n1 := by
        unfold advCnt
        exact card_pos.2 ⟨F.lab v, mem_filter.2 ⟨mem_Ioc.2 ⟨hl1, hl2⟩, hadv⟩⟩
      omega
  have huniq : ∀ v ∈ F.V, ∀ v' ∈ F.V, n0 < F.lab v → F.lab v ≤ n1 → n0 < F.lab v' →
      F.lab v' ≤ n1 → v = v' := by
    intro v hv v' hv' h1 h2 h1' h2'
    obtain ⟨hh, hl⟩ := hnew v hv h1 h2
    obtain ⟨hh', hl'⟩ := hnew v' hv' h1' h2'
    have hc := hF.honCount s (by omega) (by omega)
    rw [hs1] at hc
    obtain ⟨x, hx⟩ := card_eq_one.1 hc
    have e1 : v ∈ F.V.filter (fun v => F.hon v = true ∧ F.lab v = s) := mem_filter.2 ⟨hv, hh, hl⟩
    have e2 : v' ∈ F.V.filter (fun v => F.hon v = true ∧ F.lab v = s) := mem_filter.2 ⟨hv', hh', hl'⟩
    rw [hx] at e1 e2
    rw [mem_singleton] at e1 e2
    rw [e1, e2]
  -- a chain that is not a descendant of the new vertex ends before the phase
  have hold : ∀ v ∈ F.V, F.lab v ≤ n1 → (∀ y ∈ F.V, n0 < F.lab y → ¬ F.Anc y v) →
      F.lab v ≤ n0 := by
    intro v hv hl hno
    by_contra hgt
    push Not at hgt
    exact hno v hv hgt (anc_refl v)
  have hH : 1 ≤ hD Δ w n0 n1 := by
    have hq : Quiet Δ w n0 := hq0
    -- `h_Δ` counts the honest slot `s`
    have hgrowth : ∀ b, s ≤ b → b ≤ n1 → 1 ≤ hD Δ w n0 b := by
      intro b
      induction b using Nat.strong_induction_on with
      | _ b ih =>
        intro hsb hb1
        rw [hD, dif_neg (by omega)]
        by_cases hw : (w b).1 = 0
        · rw [if_pos hw]
          have hbs : b ≠ s := by rintro rfl; omega
          exact ih (b - 1) (by omega) (by omega) (by omega)
        · rw [if_neg hw]; omega
    exact hgrowth n1 hs.2 le_rfl
  intro v₁ hv₁ v₂ hv₂ hl₁ hl₂ hns
  -- at most one of the two chains contains a vertex of the phase
  by_cases h₁ : ∃ y ∈ F.V, n0 < F.lab y ∧ F.Anc y v₁
  · obtain ⟨y, hy, hyl, hyanc⟩ := h₁
    have h₂ : ∀ y' ∈ F.V, n0 < F.lab y' → ¬ F.Anc y' v₂ := by
      intro y' hy' hyl' hanc'
      have hyl1 : F.lab y ≤ n1 := (hF.anc_lab_le hyanc hv₁).trans hl₁
      have hyl1' : F.lab y' ≤ n1 := (hF.anc_lab_le hanc' hv₂).trans hl₂
      have := huniq y hy y' hy' hyl hyl1 hyl' hyl1'
      subst this
      exact hns ⟨y, hy, hyanc, hanc', by rw [(hnew y hy hyl hyl1).2]; exact hsℓ⟩
    have hl := hold v₂ hv₂ hl₂ h₂
    have := hF.reach_old hq0 hq1 h01 h1n hl
    have := hR v₂ hv₂ hl
    exact le_trans (min_le_right _ _) (by omega)
  · push Not at h₁
    have hl := hold v₁ hv₁ hl₁ (fun y hy hyl => h₁ y hy hyl)
    have := hF.reach_old hq0 hq1 h01 h1n hl
    have := hR v₁ hv₁ hl
    exact le_trans (min_le_left _ _) (by omega)

omit hq1 h01 h1n in
/-- **No violation inside a cold phase.** If the margin at the start `n0` of a
phase is below `-advCnt (n0, m]`, then no two chains with last labels `≤ m` that
diverge before slot `ℓ` are both at least as deep as the honest depth at the start
of the phase, `hd (n0 - Δ)`. (In particular, not both dominant at any time
`m' ∈ [n0, m]`, since `hd (n0 - Δ) ≤ hd (m' - Δ)`.) -/
theorem no_violation {ℓ m : ℕ} {M : ℤ} (hM : MB Δ w ℓ M n0 F) (hn0m : n0 ≤ m)
    (hcold : M < -(advCnt w n0 m : ℤ)) {v₁ v₂ : ℕ} (hv₁ : v₁ ∈ F.V) (hv₂ : v₂ ∈ F.V)
    (hl₁ : F.lab v₁ ≤ m) (hl₂ : F.lab v₂ ≤ m) (hns : ¬ F.Sim ℓ v₁ v₂)
    (hd₁ : F.hd (n0 - Δ) ≤ F.dep v₁) (hd₂ : F.hd (n0 - Δ) ≤ F.dep v₂) : False := by
  obtain ⟨z₁, hz₁, hzl₁, hanc₁, haft₁⟩ := hF.last_honest_le n0 hv₁
  obtain ⟨z₂, hz₂, hzl₂, hanc₂, haft₂⟩ := hF.last_honest_le n0 hv₂
  have hns' : ¬ F.Sim ℓ z₁ z₂ := fun h => hns (sim_of_anc hanc₁ hanc₂ h)
  have hmin := hM z₁ (hF.anc_mem hanc₁ hv₁) z₂ (hF.anc_mem hanc₂ hv₂) hzl₁ hzl₂ hns'
  have key : ∀ {z v : ℕ}, v ∈ F.V → F.lab v ≤ m → F.hon z = true → F.lab z ≤ n0 → F.Anc z v →
      (∀ j < F.dep v - F.dep z, F.hon (F.par^[j] v) = true → n0 < F.lab (F.par^[j] v)) →
      reach Δ w F n0 z ≤ M → F.dep v < F.hd (n0 - Δ) := by
    intro z v hv hlv hz hzl hanc haft hr
    obtain ⟨-, hdep⟩ := hF.core hq0 hn0m hv hlv hz hzl hanc haft (by omega)
    unfold reach at hr
    omega
  rcases le_total (reach Δ w F n0 z₁) (reach Δ w F n0 z₂) with h | h
  · rw [min_eq_left h] at hmin
    have := key hv₁ hl₁ hz₁ hzl₁ hanc₁ haft₁ hmin; omega
  · rw [min_eq_right h] at hmin
    have := key hv₂ hl₂ hz₂ hzl₂ hanc₂ haft₂ hmin; omega

end PTree.Valid

end Cryptarchia.Settle
