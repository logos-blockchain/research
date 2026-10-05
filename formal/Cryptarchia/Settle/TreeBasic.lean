import Cryptarchia.Settle.Tree

/-!
# PoS trees: basic structure

Ancestry, depths along chains, the honest-depth function `hd`, and the two
counting facts every settlement argument rests on:

* `hd_growth`: after a quiet period, honest depth grows by at least `h_Δ`;
* `adv_path_le`: a chain segment with no honest vertex is no longer than the
  number of adversarial slots it spans (labels strictly increase, and each
  adversarial vertex needs an adversarial slot).
-/

namespace Cryptarchia.Settle

open Finset

variable {Δ : ℕ} {w : CStr}

/-! ## Counting adversarial slots -/

theorem advCnt_add {a b c : ℕ} (hab : a ≤ b) (hbc : b ≤ c) :
    advCnt w a b + advCnt w b c = advCnt w a c := by
  unfold advCnt
  rw [← card_union_of_disjoint, ← filter_union, Ioc_union_Ioc_eq_Ioc hab hbc]
  exact disjoint_filter_filter (Ioc_disjoint_Ioc_of_le le_rfl)

theorem advCnt_mono_right {a b c : ℕ} (hbc : b ≤ c) : advCnt w a b ≤ advCnt w a c :=
  card_le_card (filter_subset_filter _ (Ioc_subset_Ioc le_rfl hbc))

theorem advCnt_mono_left {a b c : ℕ} (hab : a ≤ b) : advCnt w b c ≤ advCnt w a c :=
  card_le_card (filter_subset_filter _ (Ioc_subset_Ioc hab le_rfl))

theorem advCnt_self (a : ℕ) : advCnt w a a = 0 := by
  unfold advCnt; simp

/-- One more adversarial slot. -/
theorem advCnt_succ_of {a b c : ℕ} (hab : a ≤ b) (hbc : b < c) (hc : (w c).2 = true) :
    advCnt w a b + 1 ≤ advCnt w a c := by
  unfold advCnt
  have : insert c ((Ioc a b).filter (fun j => (w j).2 = true)) ⊆
      (Ioc a c).filter (fun j => (w j).2 = true) := by
    intro j hj
    simp only [mem_insert, mem_filter, mem_Ioc] at hj ⊢
    rcases hj with rfl | hj
    · exact ⟨⟨by omega, le_rfl⟩, hc⟩
    · exact ⟨⟨hj.1.1, by omega⟩, hj.2⟩
  have h := card_le_card this
  rw [card_insert_of_notMem (by simp only [mem_filter, mem_Ioc]; omega)] at h
  exact h

/-- Occupied slots in `(a, b]`: slots with an honest or an adversarial success. -/
def occCnt (w : CStr) (a b : ℕ) : ℕ :=
  ((Finset.Ioc a b).filter (fun j => 1 ≤ (w j).1 ∨ (w j).2 = true)).card

theorem occCnt_succ_of {a b c : ℕ} (hab : a ≤ b) (hbc : b < c) (hc : 1 ≤ (w c).1 ∨ (w c).2 = true) :
    occCnt w a b + 1 ≤ occCnt w a c := by
  unfold occCnt
  have : insert c ((Ioc a b).filter (fun j => 1 ≤ (w j).1 ∨ (w j).2 = true)) ⊆
      (Ioc a c).filter (fun j => 1 ≤ (w j).1 ∨ (w j).2 = true) := by
    intro j hj
    simp only [mem_insert, mem_filter, mem_Ioc] at hj ⊢
    rcases hj with rfl | hj
    · exact ⟨⟨by omega, le_rfl⟩, hc⟩
    · exact ⟨⟨hj.1.1, by omega⟩, hj.2⟩
  have h := card_le_card this
  rw [card_insert_of_notMem (by simp only [mem_filter, mem_Ioc]; omega)] at h
  exact h

theorem occCnt_mono {a b c d : ℕ} (hac : c ≤ a) (hbd : b ≤ d) : occCnt w a b ≤ occCnt w c d :=
  card_le_card (filter_subset_filter _ (Ioc_subset_Ioc hac hbd))

namespace PTree

variable {F : PTree} {n : ℕ}

theorem anc_refl (v : ℕ) : F.Anc v v := ⟨le_rfl, by simp⟩

theorem anc_trans {u x v : ℕ} (h1 : F.Anc u x) (h2 : F.Anc x v) : F.Anc u v := by
  refine ⟨le_trans h1.1 h2.1, ?_⟩
  have : F.dep v - F.dep u = (F.dep x - F.dep u) + (F.dep v - F.dep x) := by
    have := h1.1; have := h2.1; omega
  rw [this, Function.iterate_add_apply, h2.2, h1.2]

/-- An ancestor with the same depth is the vertex itself. -/
theorem anc_eq_of_dep {u v : ℕ} (h : F.Anc u v) (hd : F.dep u = F.dep v) : u = v := by
  have := h.2; rw [hd, Nat.sub_self, Function.iterate_zero_apply] at this; exact this.symm

/-- Two ancestors of the same vertex are ordered. -/
theorem anc_total {x y v : ℕ} (hx : F.Anc x v) (hy : F.Anc y v) : F.Anc x y ∨ F.Anc y x := by
  rcases le_total (F.dep x) (F.dep y) with h | h
  · left
    refine ⟨h, ?_⟩
    have e : F.dep v - F.dep x = (F.dep y - F.dep x) + (F.dep v - F.dep y) := by
      have := hx.1; have := hy.1; omega
    have := hx.2
    rwa [e, Function.iterate_add_apply, hy.2] at this
  · right
    refine ⟨h, ?_⟩
    have e : F.dep v - F.dep y = (F.dep x - F.dep y) + (F.dep v - F.dep x) := by
      have := hx.1; have := hy.1; omega
    have := hy.2
    rwa [e, Function.iterate_add_apply, hx.2] at this

/-- `∼ℓ` passes to descendants. -/
theorem sim_of_anc {ℓ u u' v v' : ℕ} (hu : F.Anc u u') (hv : F.Anc v v') (h : F.Sim ℓ u v) :
    F.Sim ℓ u' v' := by
  obtain ⟨x, hx, h1, h2, h3⟩ := h
  exact ⟨x, hx, anc_trans h1 hu, anc_trans h2 hv, h3⟩

namespace Valid

variable (hF : F.Valid Δ w n)
include hF

theorem iter_mem {v : ℕ} (hv : v ∈ F.V) (j : ℕ) : F.par^[j] v ∈ F.V := by
  induction j generalizing v with
  | zero => exact hv
  | succ j ih => rw [Function.iterate_succ_apply]; exact ih (hF.par_mem v hv)

theorem dep_eq_zero {v : ℕ} (hv : v ∈ F.V) : F.dep v = 0 ↔ v = 0 := by
  constructor
  · intro h; by_contra hne; rw [hF.dep_succ v hv hne] at h; omega
  · rintro rfl; exact hF.root_dep

theorem dep_iter {v : ℕ} (hv : v ∈ F.V) (j : ℕ) : F.dep (F.par^[j] v) = F.dep v - j := by
  induction j generalizing v with
  | zero => simp
  | succ j ih =>
    rw [Function.iterate_succ_apply, ih (hF.par_mem v hv)]
    by_cases h0 : v = 0
    · subst h0; rw [hF.root_par, hF.root_dep]; simp
    · rw [hF.dep_succ v hv h0]; omega

theorem lab_par_le {v : ℕ} (hv : v ∈ F.V) : F.lab (F.par v) ≤ F.lab v := by
  by_cases h0 : v = 0
  · subst h0; rw [hF.root_par]
  · exact (hF.lab_lt v hv h0).le

theorem lab_iter_le {v : ℕ} (hv : v ∈ F.V) (j : ℕ) : F.lab (F.par^[j] v) ≤ F.lab v := by
  induction j generalizing v with
  | zero => simp
  | succ j ih =>
    rw [Function.iterate_succ_apply]
    exact le_trans (ih (hF.par_mem v hv)) (hF.lab_par_le hv)

theorem lab_iter_lt {v : ℕ} (hv : v ∈ F.V) {j : ℕ} (hj0 : 0 < j) (hj : j ≤ F.dep v) :
    F.lab (F.par^[j] v) < F.lab v := by
  obtain ⟨j, rfl⟩ : ∃ i, j = i + 1 := ⟨j - 1, by omega⟩
  rw [Function.iterate_succ_apply']
  have hm := hF.iter_mem hv j
  have hne : F.par^[j] v ≠ 0 := by
    intro h; have := hF.dep_iter hv j; rw [h, hF.root_dep] at this; omega
  exact lt_of_lt_of_le (hF.lab_lt _ hm hne) (hF.lab_iter_le hv j)

theorem anc_iter {v : ℕ} (hv : v ∈ F.V) {j : ℕ} (hj : j ≤ F.dep v) : F.Anc (F.par^[j] v) v := by
  refine ⟨by rw [hF.dep_iter hv]; omega, ?_⟩
  rw [hF.dep_iter hv]; congr 1; omega

theorem anc_mem {u v : ℕ} (h : F.Anc u v) (hv : v ∈ F.V) : u ∈ F.V := by
  rw [← h.2]; exact hF.iter_mem hv _

theorem anc_lab_le {u v : ℕ} (h : F.Anc u v) (hv : v ∈ F.V) : F.lab u ≤ F.lab v := by
  rw [← h.2]; exact hF.lab_iter_le hv _

theorem anc_par {v : ℕ} (hv : v ∈ F.V) : F.Anc (F.par v) v := by
  have := hF.anc_iter hv (j := 1)
  by_cases h0 : v = 0
  · subst h0; rw [hF.root_par]; exact anc_refl 0
  · have hd : 1 ≤ F.dep v := by
      rw [hF.dep_succ v hv h0]; omega
    simpa using this hd

theorem anc_root {v : ℕ} (hv : v ∈ F.V) : F.Anc 0 v := by
  have := hF.anc_iter hv (j := F.dep v) le_rfl
  have h0 : F.par^[F.dep v] v = 0 := by
    rw [← hF.dep_eq_zero (hF.iter_mem hv _), hF.dep_iter hv]; simp
  rwa [h0] at this

/-! ## Honest depth -/

theorem le_hd {v m : ℕ} (hv : v ∈ F.V) (hh : F.hon v = true) (hl : F.lab v ≤ m) : F.dep v ≤ F.hd m :=
  le_sup (f := F.dep) (by simp only [mem_filter]; exact ⟨hv, hh, hl⟩)

theorem hd_mono {m m' : ℕ} (h : m ≤ m') : F.hd m ≤ F.hd m' := by
  unfold hd
  apply sup_mono
  intro v hv
  simp only [mem_filter] at hv ⊢
  exact ⟨hv.1, hv.2.1, hv.2.2.trans h⟩

theorem hd_exists (m : ℕ) : ∃ v ∈ F.V, F.hon v = true ∧ F.lab v ≤ m ∧ F.dep v = F.hd m := by
  have hne : (F.V.filter (fun v => F.hon v = true ∧ F.lab v ≤ m)).Nonempty :=
    ⟨0, by simp only [mem_filter]; exact ⟨hF.root_mem, hF.root_hon, by rw [hF.root_lab]; omega⟩⟩
  obtain ⟨v, hv, he⟩ := exists_mem_eq_sup _ hne F.dep
  simp only [mem_filter] at hv
  exact ⟨v, hv.1, hv.2.1, hv.2.2, he.symm⟩

/-- An honest vertex with label in `1 … n` means the slot has an honest success. -/
theorem hon_slot {v : ℕ} (hv : v ∈ F.V) (hh : F.hon v = true) (h0 : v ≠ 0) :
    1 ≤ (w (F.lab v)).1 := by
  have hl := hF.lab_pos v hv h0
  rw [← hF.honCount (F.lab v) hl (hF.lab_le v hv)]
  exact card_pos.2 ⟨v, mem_filter.2 ⟨hv, hh, rfl⟩⟩

/-- **A quiet period does not change honest depth.** -/
theorem hd_quiet {m : ℕ} (hq : Quiet Δ w m) : F.hd (m - Δ) = F.hd m := by
  apply le_antisymm (hF.hd_mono (Nat.sub_le m Δ))
  obtain ⟨v, hv, hh, hl, he⟩ := hF.hd_exists m
  rw [← he]
  apply hF.le_hd hv hh
  by_contra hlt
  push Not at hlt
  have h0 : v ≠ 0 := by rintro rfl; rw [hF.root_lab] at hlt; omega
  have := hF.hon_slot hv hh h0
  rw [hq (F.lab v) hlt hl (hF.lab_pos v hv h0)] at this
  omega

/-- An honest non-root vertex is deeper than every honest vertex more than `Δ`
slots older (or than genesis). -/
theorem hd_lt {m v : ℕ} (hv : v ∈ F.V) (hh : F.hon v = true) (h0 : v ≠ 0)
    (hm : m + Δ < F.lab v ∨ m = 0) : F.hd m < F.dep v := by
  obtain ⟨u, hu, huh, hul, he⟩ := hF.hd_exists m
  rw [← he]
  by_cases hu0 : u = 0
  · subst hu0; rw [hF.root_dep, hF.dep_succ v hv h0]; omega
  · have := hF.lab_pos u hu hu0
    rcases hm with hm | hm
    · exact hF.A2 u hu v hv huh hh (by omega)
    · omega

/-- **An honest vertex after a quiet period is deeper than every earlier honest
vertex.** -/
theorem dep_gt_hd {m v : ℕ} (hq : Quiet Δ w m) (hv : v ∈ F.V) (hh : F.hon v = true)
    (hl : m < F.lab v) : F.hd m < F.dep v := by
  rw [← hF.hd_quiet hq]
  have h0 : v ≠ 0 := by rintro rfl; rw [hF.root_lab] at hl; omega
  exact hF.hd_lt hv hh h0 (by omega)

/-- **Honest depth grows by `h_Δ`.** After a quiet period ending at `a`, honest
depth at `b` exceeds honest depth at `a` by at least `h_Δ` of the slots `(a, b]`. -/
theorem hd_growth {a : ℕ} (hq : Quiet Δ w a) :
    ∀ b, a ≤ b → b ≤ n → F.hd a + hD Δ w a b ≤ F.hd b := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    intro hab hbn
    rw [hD]
    by_cases hb : b ≤ a
    · rw [dif_pos hb]; have : b = a := by omega
      subst this; simp
    rw [dif_neg hb]
    by_cases hw : (w b).1 = 0
    · rw [if_pos hw]
      exact le_trans (ih (b - 1) (by omega) (by omega) (by omega)) (hF.hd_mono (Nat.sub_le b 1))
    rw [if_neg hw]
    -- an honest vertex with label `b`
    have hcnt := hF.honCount b (by omega) hbn
    obtain ⟨v, hvm⟩ : (F.V.filter (fun v => F.hon v = true ∧ F.lab v = b)).Nonempty := by
      rw [← card_pos, hcnt]; omega
    simp only [mem_filter] at hvm
    obtain ⟨hv, hh, hl⟩ := hvm
    have hvb : F.dep v ≤ F.hd b := hF.le_hd hv hh hl.le
    -- it is deeper than every honest vertex with label `≤ b - Δ - 1`
    have hdeep : F.hd (b - Δ - 1) < F.dep v := by
      have h0 : v ≠ 0 := by rintro rfl; rw [hF.root_lab] at hl; omega
      exact hF.hd_lt hv hh h0 (by omega)
    by_cases hc : b - Δ - 1 ≤ a
    · have h0 : hD Δ w a (b - Δ - 1) = 0 := by rw [hD, dif_pos hc]
      rw [h0]
      -- `hd a = hd (a - Δ) ≤ hd (b - Δ - 1)`
      have : F.hd a ≤ F.hd (b - Δ - 1) := by
        rw [← hF.hd_quiet hq]; exact hF.hd_mono (by omega)
      omega
    · have := ih (b - Δ - 1) (by omega) (by omega) (by omega)
      omega

/-! ## Adversarial segments -/

/-- **An adversarial segment is short.** If every vertex on the chain from `v`
up to (not including) its ancestor `u` is adversarial, the segment has at most
as many vertices as there are adversarial slots in `(lab u, lab v]`. -/
theorem adv_path_le : ∀ (k : ℕ) (u v : ℕ), v ∈ F.V → F.Anc u v → F.dep v - F.dep u = k →
    (∀ j < k, F.hon (F.par^[j] v) = false) → k ≤ advCnt w (F.lab u) (F.lab v) := by
  intro k
  induction k with
  | zero => intros; omega
  | succ k ih =>
    intro u v hv hanc hk hadv
    have h0 : v ≠ 0 := by
      intro h; subst h; rw [hF.root_dep] at hk; omega
    have hpar := ih u (F.par v) (hF.par_mem v hv)
      ⟨by rw [hF.dep_succ v hv h0] at hk; omega, by
        rw [← Function.iterate_succ_apply]
        have : (F.dep (F.par v) - F.dep u).succ = F.dep v - F.dep u := by
          rw [hF.dep_succ v hv h0] at hk ⊢; omega
        rw [this]; exact hanc.2⟩
      (by rw [hF.dep_succ v hv h0] at hk; omega)
      (fun j hj => by rw [← Function.iterate_succ_apply]; exact hadv (j + 1) (by omega))
    have hvadv : F.hon v = false := hadv 0 (by omega)
    have hlu : F.lab u ≤ F.lab (F.par v) :=
      (hF.lab_iter_le (hF.par_mem v hv) (F.dep (F.par v) - F.dep u)).trans' (by
        have : F.par^[F.dep (F.par v) - F.dep u] (F.par v) = u := by
          rw [← Function.iterate_succ_apply]
          have : (F.dep (F.par v) - F.dep u).succ = F.dep v - F.dep u := by
            rw [hF.dep_succ v hv h0] at hk ⊢; omega
          rw [this]; exact hanc.2
        rw [this])
    have := advCnt_succ_of (w := w) hlu (hF.lab_lt v hv h0) (hF.advSlot v hv hvadv)
    omega

/-- **A chain segment is no longer than the occupied slots it spans**: labels
strictly increase, and every vertex's label is an occupied slot. -/
theorem seg_le_occ : ∀ (k : ℕ) (u v : ℕ), v ∈ F.V → F.Anc u v → F.dep v - F.dep u = k →
    k ≤ occCnt w (F.lab u) (F.lab v) := by
  intro k
  induction k with
  | zero => intros; omega
  | succ k ih =>
    intro u v hv hanc hk
    have h0 : v ≠ 0 := by
      intro h; subst h; rw [hF.root_dep] at hk; omega
    have hpeq : F.par^[F.dep (F.par v) - F.dep u] (F.par v) = u := by
      rw [← Function.iterate_succ_apply]
      have : (F.dep (F.par v) - F.dep u).succ = F.dep v - F.dep u := by
        rw [hF.dep_succ v hv h0] at hk ⊢; omega
      rw [this]; exact hanc.2
    have hpar := ih u (F.par v) (hF.par_mem v hv)
      ⟨by rw [hF.dep_succ v hv h0] at hk; omega, hpeq⟩ (by rw [hF.dep_succ v hv h0] at hk; omega)
    have hlu : F.lab u ≤ F.lab (F.par v) := by
      have := hF.lab_iter_le (hF.par_mem v hv) (F.dep (F.par v) - F.dep u)
      rwa [hpeq] at this
    have hocc : 1 ≤ (w (F.lab v)).1 ∨ (w (F.lab v)).2 = true := by
      by_cases hh : F.hon v = true
      · exact Or.inl (hF.hon_slot hv hh h0)
      · exact Or.inr (hF.advSlot v hv (by simpa using hh))
    have := occCnt_succ_of (w := w) hlu (hF.lab_lt v hv h0) hocc
    omega

/-- The **last honest ancestor** of a vertex: an honest ancestor such that every
vertex after it on the chain is adversarial. -/
theorem last_honest {v : ℕ} (hv : v ∈ F.V) :
    ∃ u, F.hon u = true ∧ F.Anc u v ∧ ∀ j < F.dep v - F.dep u, F.hon (F.par^[j] v) = false := by
  induction h : F.dep v generalizing v with
  | zero =>
    have := (hF.dep_eq_zero hv).1 h; subst this
    exact ⟨0, hF.root_hon, anc_refl 0, by intro j hj; omega⟩
  | succ d ih =>
    by_cases hh : F.hon v = true
    · exact ⟨v, hh, anc_refl v, by intro j hj; omega⟩
    have h0 : v ≠ 0 := by rintro rfl; rw [hF.root_hon] at hh; simp at hh
    have hdp : F.dep (F.par v) = d := by rw [hF.dep_succ v hv h0] at h; omega
    obtain ⟨u, hu, hanc, hadv⟩ := ih (hF.par_mem v hv) hdp
    refine ⟨u, hu, anc_trans hanc (hF.anc_par hv), ?_⟩
    intro j hj
    rcases j with _ | j
    · simpa using hh
    · rw [Function.iterate_succ_apply]
      apply hadv j
      omega

end Valid

end PTree

end Cryptarchia.Settle
