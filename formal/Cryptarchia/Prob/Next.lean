import Cryptarchia.Prob.Burst

/-!
# The next phase, as the sampled histories see it

Sampling over one phase from a phase end `h` reaches histories `h'` that are the
**first** phase end after `h` (`FirstPE`). At such an `h'`, the greedy phase ends of
`strOf h'` agree with those of `strOf h` up to `h`'s index `j`, and the next one is
`h'` itself, with index `j + 1` (`firstPE_gend`). So the bound process at `h'` is
one `step` of the one at `h` (`bnd_next`, `runFrom_next`).
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {κ : Kern} {Δ M : ℕ}

/-- **Monotonicity on reached histories.** -/
theorem ExU_mono_on (S : List Out → Prop) [DecidablePred S] :
    ∀ (n : ℕ) (x : List Out) {F G : List Out → ℝ},
      (∀ t : List Out, t.length ≤ n → (∀ k < t.length, ¬ S (x ++ t.take k)) →
        (S (x ++ t) ∨ t.length = n) → F (x ++ t) ≤ G (x ++ t)) →
      ExU (κ := κ) S n F x ≤ ExU (κ := κ) S n G x
  | 0, x, F, G, h => by simpa [ExU_zero] using h [] le_rfl (by simp) (Or.inr rfl)
  | n + 1, x, F, G, h => by
    by_cases hS : S x
    · rw [ExU_stop S _ F hS, ExU_stop S _ G hS]
      simpa using h [] (by simp) (by simp) (Or.inl (by simpa using hS))
    · rw [ExU_go S n F hS, ExU_go S n G hS]
      refine Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left ?_ (κ.nonneg x o)
      apply ExU_mono_on S n (x ++ [o])
      intro t ht hk hend
      have := h (o :: t) (by simp; omega) ?_ ?_
      · simpa using this
      · intro k hk'
        cases k with
        | zero => simpa using hS
        | succ k =>
          have := hk k (by simp at hk'; omega)
          simpa [List.take_succ_cons] using this
      · rcases hend with h1 | h1
        · left; simpa using h1
        · right; simp [h1]

theorem ExPh_mono_on (S : List Out → Prop) [DecidablePred S] (n : ℕ) (x : List Out)
    {F G : List Out → ℝ}
    (h : ∀ (o : Out) (t : List Out), t.length ≤ n → (∀ k < t.length, ¬ S (x ++ [o] ++ t.take k)) →
      (S (x ++ [o] ++ t) ∨ t.length = n) → F (x ++ [o] ++ t) ≤ G (x ++ [o] ++ t)) :
    ExPh (κ := κ) S n F x ≤ ExPh (κ := κ) S n G x := by
  unfold ExPh
  exact Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left
    (ExU_mono_on S n (x ++ [o]) (h o)) (κ.nonneg x o)

theorem ExPh_add (S : List Out → Prop) [DecidablePred S] (n : ℕ) (F G : List Out → ℝ) (x : List Out) :
    ExPh (κ := κ) S n (fun y => F y + G y) x = ExPh (κ := κ) S n F x + ExPh (κ := κ) S n G x := by
  unfold ExPh
  simp only [ExU_add, mul_add, Finset.sum_add_distrib]

theorem ExPh_mul_const (S : List Out → Prop) [DecidablePred S] (n : ℕ) (a : ℝ) (F : List Out → ℝ)
    (x : List Out) : ExPh (κ := κ) S n (fun y => a * F y) x = a * ExPh (κ := κ) S n F x := by
  unfold ExPh
  simp only [ExU_mul_const, Finset.mul_sum]
  exact Finset.sum_congr rfl fun o _ => by ring

theorem ExPh_const (S : List Out → Prop) [DecidablePred S] (n : ℕ) (a : ℝ) (x : List Out) :
    ExPh (κ := κ) S n (fun _ => a) x = a := by
  unfold ExPh
  simp only [ExU_const]
  rw [← Finset.sum_mul, κ.sum_one, one_mul]

theorem ExPh_sub (S : List Out → Prop) [DecidablePred S] (n : ℕ) (F G : List Out → ℝ) (x : List Out) :
    ExPh (κ := κ) S n (fun y => F y - G y) x = ExPh (κ := κ) S n F x - ExPh (κ := κ) S n G x := by
  have h := ExPh_add (κ := κ) S n (fun y => F y - G y) G x
  simp only [sub_add_cancel] at h
  linarith

theorem ExPh_nonneg (S : List Out → Prop) [DecidablePred S] (n : ℕ) {F : List Out → ℝ}
    (hF : ∀ y, 0 ≤ F y) (x : List Out) : 0 ≤ ExPh (κ := κ) S n F x := by
  unfold ExPh
  exact Finset.sum_nonneg fun o _ => mul_nonneg (κ.nonneg x o) (ExU_nonneg S n hF _)

/-! ## The first phase end after a history -/

/-- `h'` is the first phase end after `h`. -/
structure FirstPE (Δ M : ℕ) (h h' : List Out) : Prop where
  pre : h <+: h'
  lt : h.length < h'.length
  pe : PE Δ M h'
  first : ∀ p, h.length < p → p < h'.length → ¬ PE Δ M (h'.take p)

/-- The histories reached over one phase are first phase ends. -/
theorem firstPE_of_reached {h : List Out} (hlM : h.length < M) (o : Out) (t : List Out)
    (ht : t.length ≤ M - h.length - 1)
    (hk : ∀ k < t.length, ¬ PE Δ M (h ++ [o] ++ t.take k))
    (hend : PE Δ M (h ++ [o] ++ t) ∨ t.length = M - h.length - 1) :
    FirstPE Δ M h (h ++ [o] ++ t) := by
  refine ⟨⟨[o] ++ t, by simp⟩, by simp, ?_, ?_⟩
  · rcases hend with h1 | h1
    · exact h1
    · left; simp; omega
  · intro p h1 h2
    have hp : (h ++ [o] ++ t).take p = h ++ [o] ++ t.take (p - h.length - 1) := by
      rw [List.append_assoc, List.take_append, List.take_of_length_le (by omega)]
      simp only [List.length_append, List.length_singleton, List.append_assoc]
      congr 1
      rw [show p - h.length = (p - h.length - 1) + 1 by omega]
      simp
    rw [hp]
    exact hk _ (by simp at h2; omega)

theorem start_of_pe {h : List Out} (hpe : PE Δ M h) (hlM : h.length < M) : Start Δ h := by
  rcases hpe with h1 | ⟨-, h2⟩
  · omega
  · exact Or.inr h2

theorem pe_nil (hM : 0 < M) : PE Δ M [] := by
  right; refine ⟨by simpa using hM, ?_⟩
  intro i h1 h2 h3; simp at h2; omega

/-- A phase end's index. -/
theorem gend_pidx_pe {h : List Out} (hpe : PE Δ M h) :
    gend Δ M (strOf h) (pidx Δ M (strOf h) h.length) = h.length := by
  apply gend_pidx_of_end
  rcases hpe with h1 | ⟨h1, h2⟩
  · exact Or.inr (Or.inl h1)
  · exact Or.inr (Or.inr ⟨h1, h2⟩)

theorem simOn_prefix {h h' : List Out} (hp : h <+: h') (a : ℕ) :
    SimOn (strOf h') (strOf h) a h.length := by
  obtain ⟨t, rfl⟩ := hp
  exact strOf_sim h t a

/-- **The phase structure at the next phase end.** -/
theorem firstPE_gend {h h' : List Out} (hpe : PE Δ M h) (hlM : h.length < M) (hf : FirstPE Δ M h h') :
    (∀ i ≤ pidx Δ M (strOf h) h.length, gend Δ M (strOf h') i = gend Δ M (strOf h) i) ∧
      gend Δ M (strOf h') (pidx Δ M (strOf h) h.length + 1) = h'.length ∧
      pidx Δ M (strOf h') h'.length = pidx Δ M (strOf h) h.length + 1 := by
  set j := pidx Δ M (strOf h) h.length with hj
  have hej := gend_pidx_pe hpe
  rw [← hj] at hej
  have hsim : SimOn (strOf h) (strOf h') 0 h.length := (simOn_prefix hf.pre 0).symm
  have hagree : ∀ i ≤ j, gend Δ M (strOf h') i = gend Δ M (strOf h) i := by
    intro i hi
    have hle : gend Δ M (strOf h) i ≤ h.length := by
      rw [← hej]; exact gend_strictMono.monotone hi
    exact (gend_congr hsim i hle).symm
  have hh'M : h'.length ≤ M := by
    rcases hf.pe with h1 | h1
    · omega
    · omega
  -- no quiet slot strictly between
  have hnq : ∀ p, h.length < p → p < h'.length → p < M → ¬ Quiet Δ (strOf h') p := by
    intro p h1 h2 hpM hq
    apply hf.first p h1 h2
    right
    have hlen : (h'.take p).length = p := by simp; omega
    refine ⟨by omega, ?_⟩
    rw [hlen]
    have hs : SimOn (strOf h') (strOf (h'.take p)) (p - Δ) p := by
      have := simOn_prefix (List.take_prefix p h') (p - Δ)
      rwa [hlen] at this
    exact (quiet_congr hs).1 hq
  have hnext : gend Δ M (strOf h') (j + 1) = h'.length := by
    rw [gend_succ, hagree j le_rfl, hej]
    apply le_antisymm
    · rcases hf.pe with h1 | ⟨h1, h2⟩
      · rw [h1]; exact nextE_le hlM
      · exact nextE_le_of_quiet hf.lt h1 h2
    · by_contra hlt
      push Not at hlt
      have hgt := nextE_gt (Δ := Δ) (M := M) (w := strOf h') h.length
      have hle := nextE_le (Δ := Δ) (w := strOf h') hlM
      have hM' : nextE Δ M (strOf h') h.length < M := by omega
      exact hnq _ hgt hlt hM' (nextE_quiet hM')
  refine ⟨hagree, hnext, ?_⟩
  apply le_antisymm
  · exact pidx_le_of (le_of_eq hnext.symm)
  · by_contra hlt
    push Not at hlt
    have h1 := le_gend_pidx (Δ := Δ) (M := M) (w := strOf h') h'.length
    rw [hagree _ (by omega)] at h1
    have h2 : gend Δ M (strOf h) (pidx Δ M (strOf h') h'.length) ≤ h.length := by
      rw [← hej]; exact gend_strictMono.monotone (by omega)
    have := hf.lt
    omega

/-! ## The bound process along agreeing phase ends -/

theorem bnd_congr2 {w w' : CStr} {ℓ : ℕ} {e e' : ℕ → ℕ} (hmono : ∀ k, e k ≤ e (k + 1)) :
    ∀ k, (∀ i ≤ k, e i = e' i) → SimOn w w' 0 (e k) → bnd Δ w ℓ e k = bnd Δ w' ℓ e' k
  | 0, _, _ => rfl
  | k + 1, he, h => by
    simp only [bnd]
    rw [bnd_congr2 hmono k (fun i hi => he i (by omega)) (h.mono le_rfl (hmono k)),
      step_congr (h.mono (Nat.zero_le _) le_rfl), he k (by omega), he (k + 1) le_rfl]

theorem runFrom_congr2 {w w' : CStr} {ℓ : ℕ} {e e' : ℕ → ℕ} (hmono : ∀ k, e k ≤ e (k + 1)) (k0 : ℕ)
    (b0 : ℤ × ℤ) : ∀ j, (∀ i ≤ k0 + j, e i = e' i) → SimOn w w' 0 (e (k0 + j)) →
      runFrom (Δ := Δ) (w := w) ℓ e k0 b0 j = runFrom (Δ := Δ) (w := w') ℓ e' k0 b0 j
  | 0, _, _ => rfl
  | j + 1, he, h => by
    simp only [runFrom]
    rw [runFrom_congr2 hmono k0 b0 j (fun i hi => he i (by omega))
      (h.mono le_rfl (by rw [← Nat.add_assoc]; exact hmono _)),
      step_congr (h.mono (Nat.zero_le _) (by rw [Nat.add_assoc])), he (k0 + j) (by omega),
      he (k0 + j + 1) (by omega)]

end Cryptarchia.Prob
