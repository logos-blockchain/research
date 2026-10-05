import Cryptarchia.Proof.Lca
import Cryptarchia.Spec.ForkChoice
import Cryptarchia.Spec.Node

/-!
# Pruning and the fork-choice loop

* `mem_prune`: pruning never removes a block that is comparable with the pruning
  point (an ancestor or a descendant of it).
* `fc_inv`, `fc_height_mono`, `fc_reaches`: the online fork-choice loop, for any
  order of the tips, preserves any property of the running choice that switches
  preserve, never decreases height, and reaches the height of any strictly longer
  tip that is within `k` of every intermediate choice.
-/

namespace Cryptarchia

variable {st : Store}

/-- In a chain split as `A ++ B`, blocks in `A` are strictly higher than those in `B`. -/
theorem height_lt_of_split (hS : StoreOK st) {t x d : ℕ} (ht : Rooted st t) {A B : List ℕ}
    (hsplit : chainIds st t = A ++ B) (hx : x ∈ A) (hd : d ∈ B) : height st d < height st x := by
  set f := fun j => (parentOf st)^[j] t with hf
  have heq := chainIds_eq hS ht
  have hlen : (chainIds st t).length = height st t + 1 := by rw [heq]; simp
  obtain ⟨i, hi, hxi⟩ := List.getElem_of_mem hx
  obtain ⟨j, hj, hdj⟩ := List.getElem_of_mem hd
  have hx' : (chainIds st t)[i]? = some x := by
    rw [hsplit, List.getElem?_append_left hi, List.getElem?_eq_getElem hi, hxi]
  have hd' : (chainIds st t)[A.length + j]? = some d := by
    rw [hsplit, List.getElem?_append_right (by omega), Nat.add_sub_cancel_left,
      List.getElem?_eq_getElem hj, hdj]
  rw [heq, List.getElem?_map] at hx' hd'
  have hl2 : A.length + j < height st t + 1 := by
    rw [hsplit] at hlen; simp at hlen; omega
  rw [List.getElem?_range (by omega)] at hx' hd'
  simp only [Option.map_some, Option.some.injEq] at hx' hd'
  have h1 := (height_iter hS ht i).2
  have h2 := (height_iter hS ht (A.length + j)).2
  rw [hx'] at h1; rw [hd'] at h2
  omega

/-- A block before `d` in `t`'s chain (tip first) is strictly higher than `d`. -/
theorem height_lt_of_takeWhile (hS : StoreOK st) {t x d : ℕ} (ht : Rooted st t)
    (hd : d ∈ chainIds st t) (hx : x ∈ (chainIds st t).takeWhile (fun y => y ≠ d)) :
    height st d < height st x := by
  have hsplit := (List.takeWhile_append_dropWhile (p := fun y => decide (y ≠ d))
    (l := chainIds st t)).symm
  have hdn : d ∉ (chainIds st t).takeWhile (fun y => y ≠ d) := by
    intro h
    have := List.mem_takeWhile_imp h
    simp at this
  have hdB : d ∈ (chainIds st t).dropWhile (fun y => y ≠ d) := by
    have := hd; rw [hsplit] at this
    rcases List.mem_append.1 this with h | h
    · exact absurd h hdn
    · exact h
  exact height_lt_of_split hS ht hsplit hx hdB

/-- **Pruning keeps what is comparable with the pruning point.** -/
theorem mem_prune (hS : StoreOK st) {T : List ℕ} {B x : ℕ} (hT : ∀ y ∈ T, Rooted st y)
    (hB : Rooted st B) (hx : x ∈ T) (hcmp : B ∈ chainIds st x ∨ x ∈ chainIds st B) :
    x ∈ pruneForks st T B := by
  unfold pruneForks
  rw [List.mem_filter]
  refine ⟨hx, ?_⟩
  suffices hnot : ∀ t ∈ tips st T, x ∉ (let d := lca st t B;
      if d = B then [] else (chainIds st t).takeWhile (· ≠ d)) by
    have : x ∉ (tips st T).flatMap (fun t => let d := lca st t B;
        if d = B then [] else (chainIds st t).takeWhile (· ≠ d)) := by
      rw [List.mem_flatMap]; rintro ⟨t, ht, hxt⟩; exact hnot t ht hxt
    simpa using this
  intro t htip
  have ht : Rooted st t := hT t (List.mem_of_mem_filter htip)
  obtain ⟨hla, hlb, hlmax⟩ := lca_spec hS ht hB
  dsimp only
  split
  · simp
  · rename_i hne
    intro hxt
    have hlt := height_lt_of_takeWhile hS ht hla hxt
    have hxc : x ∈ chainIds st t := (List.takeWhile_sublist _).subset hxt
    rcases hcmp with hBx | hxB
    · -- `B` is below `x`, so on `t`'s chain: then `lca t B = B`
      have hBt := chainIds_trans hS ht hxc hBx
      have hBl := hlmax B hBt (self_mem_chainIds hS hB)
      obtain ⟨-, h1, -⟩ := anc_height hS hB hlb
      obtain ⟨-, h2, h3⟩ := anc_height hS (anc_height hS ht hla).1 hBl
      apply hne
      have : height st (lca st t B) = height st B := by omega
      rw [this, Nat.sub_self, Function.iterate_zero_apply] at h3
      obtain ⟨-, -, h4⟩ := anc_height hS hB hlb
      rw [this, Nat.sub_self, Function.iterate_zero_apply] at h4
      exact h4.symm
    · -- `x` is a common ancestor, so no higher than `lca t B`
      have hxl := hlmax x hxc hxB
      have := (anc_height hS (anc_height hS ht hla).1 hxl).2.1
      omega

/-! ## The fork-choice loop -/

/-- An online-rule step either keeps the running choice or switches to the fork. -/
theorem onlineStep_eq (k c f : ℕ) : onlineStep st k c f = c ∨ onlineStep st k c f = f := by
  unfold onlineStep; dsimp only; split <;> [split <;> simp; simp]

/-- A switch means: the fork diverges at most `k` blocks below `c`, and is longer. -/
theorem onlineStep_switch (hS : StoreOK st) {k c f : ℕ} (hc : Rooted st c) (hf : Rooted st f)
    (h : onlineStep st k c f ≠ c) :
    onlineStep st k c f = f ∧ height st c - height st (lca st c f) ≤ k ∧ height st c < height st f := by
  unfold onlineStep commonPrefixDepth at *
  simp only at *
  obtain ⟨hl1, hl2, -⟩ := lca_spec hS hc hf
  have h1 := (anc_height hS hc hl1).2.1
  have h2 := (anc_height hS hf hl2).2.1
  split at h
  · split at h
    · rename_i hk hlt
      refine ⟨by simp [hk, hlt], hk, by omega⟩
    · exact absurd rfl h
  · exact absurd rfl h

/-- **Invariant of the loop.** -/
theorem fc_inv (P : ℕ → Prop) (k : ℕ) (forks : List ℕ) :
    ∀ c, P c → (∀ c' f, P c' → f ∈ forks → onlineStep st k c' f ≠ c' → P f) →
      P (forks.foldl (onlineStep st k) c) := by
  induction forks with
  | nil => intro c hc _; exact hc
  | cons f fs ih =>
    intro c hc hstep
    simp only [List.foldl_cons]
    apply ih
    · rcases onlineStep_eq (st := st) k c f with h | h
      · rw [h]; exact hc
      · by_cases hne : onlineStep st k c f = c
        · rw [hne]; exact hc
        · rw [h]; exact hstep c f hc (List.mem_cons_self) hne
    · intro c' f' hc' hf' hne; exact hstep c' f' hc' (List.mem_cons_of_mem _ hf') hne

/-- **Height never decreases** through the loop, provided the forks are rooted. -/
theorem fc_height (hS : StoreOK st) (k : ℕ) (forks : List ℕ) (hr : ∀ f ∈ forks, Rooted st f) :
    ∀ c, Rooted st c → Rooted st (forks.foldl (onlineStep st k) c) ∧
      height st c ≤ height st (forks.foldl (onlineStep st k) c) := by
  induction forks with
  | nil => intro c hc; exact ⟨hc, le_rfl⟩
  | cons f fs ih =>
    intro c hc
    simp only [List.foldl_cons]
    have hf := hr f List.mem_cons_self
    have hstep : Rooted st (onlineStep st k c f) ∧ height st c ≤ height st (onlineStep st k c f) := by
      by_cases hne : onlineStep st k c f = c
      · rw [hne]; exact ⟨hc, le_rfl⟩
      · obtain ⟨he, -, hlt⟩ := onlineStep_switch hS hc hf hne
        rw [he]; exact ⟨hf, hlt.le⟩
    obtain ⟨h1, h2⟩ := ih (fun g hg => hr g (List.mem_cons_of_mem _ hg)) _ hstep.1
    exact ⟨h1, le_trans hstep.2 h2⟩

/-- **The loop reaches a strictly longer fork** that is within `k` of every
running choice satisfying the loop invariant `P`. -/
theorem fc_reaches (hS : StoreOK st) (P : ℕ → Prop) (k : ℕ) (forks : List ℕ)
    (hr : ∀ f ∈ forks, Rooted st f) {f₀ : ℕ} (hf₀ : f₀ ∈ forks)
    (hnear : ∀ c, P c → Rooted st c → height st c < height st f₀ →
      height st c - height st (lca st c f₀) ≤ k) :
    ∀ c, P c → Rooted st c → (∀ c' f, P c' → f ∈ forks → onlineStep st k c' f ≠ c' → P f) →
      height st f₀ ≤ height st (forks.foldl (onlineStep st k) c) := by
  induction forks with
  | nil => simp at hf₀
  | cons f fs ih =>
    intro c hc hcr hstep
    simp only [List.foldl_cons]
    have hf := hr f List.mem_cons_self
    set c' := onlineStep st k c f with hc'
    have hc'P : P c' := by
      rcases onlineStep_eq (st := st) k c f with h | h
      · rw [hc', h]; exact hc
      · by_cases hne : onlineStep st k c f = c
        · rw [hc', hne]; exact hc
        · rw [hc', h]; exact hstep c f hc List.mem_cons_self hne
    have hc'r : Rooted st c' := by
      by_cases hne : onlineStep st k c f = c
      · rw [hc', hne]; exact hcr
      · rw [hc', (onlineStep_switch hS hcr hf hne).1]; exact hf
    have hstep' : ∀ c' f, P c' → f ∈ fs → onlineStep st k c' f ≠ c' → P f :=
      fun c' f hc hf hne => hstep c' f hc (List.mem_cons_of_mem _ hf) hne
    have hmono := fc_height hS k fs (fun g hg => hr g (List.mem_cons_of_mem _ hg)) c' hc'r
    rcases List.mem_cons.1 hf₀ with rfl | hmem
    · -- visiting `f₀` now
      by_cases hle : height st f₀ ≤ height st c
      · have : height st c ≤ height st c' := by
          by_cases hne : onlineStep st k c f₀ = c
          · rw [hc', hne]
          · rw [hc', (onlineStep_switch hS hcr hf hne).1]; exact (onlineStep_switch hS hcr hf hne).2.2.le
        omega
      · push Not at hle
        have hk := hnear c hc hcr hle
        have : c' = f₀ := by
          rw [hc']
          unfold onlineStep commonPrefixDepth
          simp only
          obtain ⟨hl1, hl2, -⟩ := lca_spec hS hcr hf
          have := (anc_height hS hcr hl1).2.1
          have := (anc_height hS hf hl2).2.1
          rw [if_pos hk, if_pos (by omega)]
        rw [this] at hmono ⊢
        exact hmono.2
    · exact ih (fun g hg => hr g (List.mem_cons_of_mem _ hg)) hmem c' hc'P hc'r hstep'

end Cryptarchia
