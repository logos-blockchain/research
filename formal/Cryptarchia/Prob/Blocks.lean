import Cryptarchia.Prob.Kernel

/-!
# Products over blocks of slots

A generic Chernoff-type bound. Cut the slots after `y` into `nb` consecutive
blocks of `Lb` slots, and call block `k` a **success** if one of its first `T`
slots satisfies `Q`. If every slot satisfies `Q` with conditional probability at
most `qhi` (or at least `qlo`), then for weights `g true = a1`, `g false = a0`,

  `E[∏_k g(success_k)] ≤ β^nb`,   `β = a0 + (a1 - a0) · P_T`,

with `P_T = 1 - (1 - qhi)^T` if `a1 ≥ a0` and `1 - (1 - qlo)^T` otherwise
(`blocks_le`). Instances: long phases (no block of `Δ` slots free of honest
leaders), the occupancy window, and honest-depth growth.
-/

namespace Cryptarchia.Prob

open Finset

variable {κ : Kern}

theorem Ex_split : ∀ (a b : ℕ) (F : List Out → ℝ) (l : List Out),
    Ex κ (a + b) F l = Ex κ a (fun l' => Ex κ b F l') l
  | 0, b, F, l => by simp [Ex_zero]
  | a + 1, b, F, l => by
    rw [show a + 1 + b = (a + b) + 1 by omega, Ex_succ, Ex_succ]
    exact Finset.sum_congr rfl fun o _ => by rw [Ex_split a b F]

/-- A factor fixed by the history so far comes out of the expectation. -/
theorem Ex_mul_fixed (n : ℕ) {c : List Out → ℝ} {F : List Out → ℝ} (l : List Out)
    (hc : ∀ t : List Out, t.length = n → c (l ++ t) = c l) :
    Ex κ n (fun x => c x * F x) l = c l * Ex κ n F l := by
  rw [← Ex_mul_const]
  apply le_antisymm
  · apply Ex_mono_len; intro t ht; rw [hc t ht]
  · apply Ex_mono_len; intro t ht; rw [hc t ht]

variable (Q : Out → Prop) [DecidablePred Q]

/-- Some slot in `(s, s + T]` satisfies `Q`. -/
def hitIn (s T : ℕ) (l : List Out) : Prop := ∃ i, s < i ∧ i ≤ s + T ∧ Q (l.getD (i - 1) Out.empty)

theorem hitIn_append {s T : ℕ} {l t : List Out} (hl : s + T ≤ l.length) :
    hitIn Q s T (l ++ t) ↔ hitIn Q s T l := by
  unfold hitIn
  constructor
  · rintro ⟨i, h1, h2, h3⟩
    exact ⟨i, h1, h2, by rwa [List.getD_append _ _ _ _ (by omega)] at h3⟩
  · rintro ⟨i, h1, h2, h3⟩
    exact ⟨i, h1, h2, by rwa [List.getD_append _ _ _ _ (by omega)]⟩

/-- The probability bound of a block of `T` slots. -/
noncomputable def PT (a0 a1 qlo qhi : ℝ) (T : ℕ) : ℝ :=
  if a0 ≤ a1 then 1 - (1 - qhi) ^ T else 1 - (1 - qlo) ^ T

/-- **One block.** -/
theorem block_le {a0 a1 qlo qhi : ℝ} (ha0 : 0 ≤ a0) (ha1 : 0 ≤ a1)
    (hhi : ∀ l, κ.pr l Q ≤ qhi) (hlo : ∀ l, qlo ≤ κ.pr l Q) (hq1 : qhi ≤ 1) (hq0 : 0 ≤ qlo) :
    ∀ (r : ℕ) (s : ℕ) (l : List Out), s ≤ l.length →
      (∀ i, s < i → i ≤ l.length → ¬ Q (l.getD (i - 1) Out.empty)) →
      Ex κ r (fun x => by classical exact if hitIn Q s (l.length - s + r) x then a1 else a0) l ≤
        a0 + (a1 - a0) * PT a0 a1 qlo qhi r := by
  classical
  intro r
  induction r with
  | zero =>
    intro s l hs hno
    rw [Ex_zero]
    have : ¬ hitIn Q s (l.length - s + 0) l := by
      rintro ⟨i, h1, h2, h3⟩; exact hno i h1 (by omega) h3
    rw [if_neg this]; unfold PT; split_ifs <;> simp
  | succ r ih =>
    intro s l hs hno
    rw [Ex_succ]
    -- after the next slot
    have hcont : ∀ o, Ex κ r (fun x => if hitIn Q s (l.length - s + (r + 1)) x then a1 else a0) (l ++ [o]) ≤
        if Q o then a1 else a0 + (a1 - a0) * PT a0 a1 qlo qhi r := by
      intro o
      have hT : l.length - s + (r + 1) = (l ++ [o]).length - s + r := by simp; omega
      rw [hT]
      by_cases hQ : Q o
      · rw [if_pos hQ]
        have hhit : ∀ x : List Out, x.length = r → hitIn Q s ((l ++ [o]).length - s + r) ((l ++ [o]) ++ x) := by
          intro x hx
          refine ⟨l.length + 1, by omega, by simp only [List.length_append, List.length_singleton]; omega, ?_⟩
          rw [List.getD_append _ _ _ _ (by simp), Nat.add_sub_cancel, List.getD_append_right _ _ _ _ le_rfl]
          simpa using hQ
        have := Ex_mono_len (κ := κ) r (F := fun x => if hitIn Q s ((l ++ [o]).length - s + r) x then a1 else a0)
          (G := fun _ => a1) (l ++ [o]) (fun x hx => by rw [if_pos (hhit x hx)])
        rwa [Ex_const] at this
      · rw [if_neg hQ]
        apply ih s (l ++ [o]) (by simp; omega)
        intro i h1 h2
        simp only [List.length_append, List.length_singleton] at h2
        rcases Nat.lt_or_ge i (l.length + 1) with hi | hi
        · rw [List.getD_append _ _ _ _ (by omega)]; exact hno i h1 (by omega)
        · have : i = l.length + 1 := by omega
          subst this
          rw [Nat.add_sub_cancel, List.getD_append_right _ _ _ _ le_rfl]; simpa using hQ
    have hsum : ∑ o, κ.p l o * (if Q o then a1 else a0 + (a1 - a0) * PT a0 a1 qlo qhi r) =
        a0 + (a1 - a0) * PT a0 a1 qlo qhi r + (a1 - a0) * (1 - PT a0 a1 qlo qhi r) * κ.pr l Q := by
      have : ∀ o, κ.p l o * (if Q o then a1 else a0 + (a1 - a0) * PT a0 a1 qlo qhi r) =
          κ.p l o * (a0 + (a1 - a0) * PT a0 a1 qlo qhi r) +
            (a1 - a0) * (1 - PT a0 a1 qlo qhi r) * (if Q o then κ.p l o else 0) := by
        intro o; split_ifs <;> ring
      simp only [this, Finset.sum_add_distrib, ← Finset.sum_mul, ← Finset.mul_sum, κ.sum_one, one_mul]
      rfl
    calc ∑ o, κ.p l o * Ex κ r (fun x => if hitIn Q s (l.length - s + (r + 1)) x then a1 else a0) (l ++ [o])
        ≤ ∑ o, κ.p l o * (if Q o then a1 else a0 + (a1 - a0) * PT a0 a1 qlo qhi r) :=
          Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (hcont o) (κ.nonneg l o)
      _ = _ := hsum
      _ ≤ a0 + (a1 - a0) * PT a0 a1 qlo qhi (r + 1) := by
          have hh := hhi l
          have hl := hlo l
          unfold PT
          split_ifs with h
          · have hp : 0 ≤ (1 - qhi) ^ r := pow_nonneg (by linarith) r
            have : (a1 - a0) * (1 - (1 - (1 - qhi) ^ r)) * κ.pr l Q ≤
                (a1 - a0) * (1 - (1 - (1 - qhi) ^ r)) * qhi :=
              mul_le_mul_of_nonneg_left hh (mul_nonneg (by linarith) (by linarith))
            rw [pow_succ]; nlinarith
          · push Not at h
            have hp : 0 ≤ (1 - qlo) ^ r := by
              rcases le_or_gt qlo 1 with h1 | h1
              · exact pow_nonneg (by linarith) r
              · -- `qlo > 1` cannot happen: probabilities are at most one
                have := pr_le_one' l
                linarith
            have : (a1 - a0) * (1 - (1 - (1 - qlo) ^ r)) * κ.pr l Q ≤
                (a1 - a0) * (1 - (1 - (1 - qlo) ^ r)) * qlo :=
              mul_le_mul_of_nonpos_left hl (mul_nonpos_of_nonpos_of_nonneg (by linarith) (by linarith))
            rw [pow_succ]; nlinarith
where
  pr_le_one' (l : List Out) : qlo ≤ 1 := le_trans (hlo l) (by
    unfold Kern.pr
    calc ∑ o, (if Q o then κ.p l o else 0) ≤ ∑ o, κ.p l o :=
          Finset.sum_le_sum fun o _ => by split_ifs <;> linarith [κ.nonneg l o]
      _ = 1 := κ.sum_one l)

/-- A function of the first slots only is fixed by them. -/
theorem Ex_det (m : ℕ) {F : List Out → ℝ} (l : List Out) (hF : ∀ t : List Out, t.length = m → F (l ++ t) = F l) :
    Ex κ m F l = F l := by
  have : Ex κ m F l = Ex κ m (fun _ => F l) l := by
    apply le_antisymm
    · apply Ex_mono_len; intro t ht; rw [hF t ht]
    · apply Ex_mono_len; intro t ht; rw [hF t ht]
  rw [this, Ex_const]

/-- The weight of block `k`. -/
noncomputable def blockG (a0 a1 : ℝ) (y Lb T k : ℕ) (l : List Out) : ℝ := by
  classical exact if hitIn Q (y + k * Lb) T l then a1 else a0

theorem blockG_append (a0 a1 : ℝ) {y Lb T k : ℕ} {l : List Out} (t : List Out) (hl : y + k * Lb + T ≤ l.length) :
    blockG Q a0 a1 y Lb T k (l ++ t) = blockG Q a0 a1 y Lb T k l := by
  classical
  unfold blockG
  by_cases h : hitIn Q (y + k * Lb) T l
  · rw [if_pos ((hitIn_append Q hl).2 h), if_pos h]
  · rw [if_neg (fun h' => h ((hitIn_append Q hl).1 h')), if_neg h]

/-- **Many blocks.** -/
theorem blocks_le {a0 a1 qlo qhi : ℝ} (ha0 : 0 ≤ a0) (ha1 : 0 ≤ a1)
    (hhi : ∀ l, κ.pr l Q ≤ qhi) (hlo : ∀ l, qlo ≤ κ.pr l Q) (hq1 : qhi ≤ 1) (hq0 : 0 ≤ qlo)
    {y Lb T nb M : ℕ} (hT : T ≤ Lb) (hM : y + nb * Lb ≤ M) :
    Ex κ M (fun x => ∏ k ∈ Finset.range nb, blockG Q a0 a1 y Lb T k x) [] ≤
      (a0 + (a1 - a0) * PT a0 a1 qlo qhi T) ^ nb := by
  classical
  set β := a0 + (a1 - a0) * PT a0 a1 qlo qhi T with hβ
  set F : List Out → ℝ := fun x => ∏ k ∈ Finset.range nb, blockG Q a0 a1 y Lb T k x with hF
  have hg0 : ∀ k x, 0 ≤ blockG Q a0 a1 y Lb T k x := fun k x => by
    unfold blockG; split_ifs <;> assumption
  -- one block
  have hone : ∀ (k : ℕ) (l : List Out), l.length = y + k * Lb →
      Ex κ Lb (blockG Q a0 a1 y Lb T k) l ≤ β := by
    intro k l hl
    rw [show Ex κ Lb (blockG Q a0 a1 y Lb T k) l = Ex κ (T + (Lb - T)) (blockG Q a0 a1 y Lb T k) l by
      rw [Nat.add_sub_cancel' hT], Ex_split]
    have : Ex κ T (fun l1 => Ex κ (Lb - T) (blockG Q a0 a1 y Lb T k) l1) l =
        Ex κ T (blockG Q a0 a1 y Lb T k) l := by
      apply le_antisymm
      · apply Ex_mono_len; intro t ht
        rw [Ex_det _ _ fun t' _ => blockG_append Q a0 a1 t' (by simp; omega)]
      · apply Ex_mono_len; intro t ht
        rw [Ex_det _ _ fun t' _ => blockG_append Q a0 a1 t' (by simp; omega)]
    rw [this]
    have hb := block_le (κ := κ) Q ha0 ha1 hhi hlo hq1 hq0 T l.length l le_rfl (fun i h1 h2 => by omega)
    unfold blockG
    simpa [hl] using hb
  -- backward over blocks
  have key : ∀ j ≤ nb, ∀ l : List Out, l.length = y + (nb - j) * Lb →
      Ex κ (j * Lb) F l ≤ (∏ k ∈ Finset.range (nb - j), blockG Q a0 a1 y Lb T k l) * β ^ j := by
    intro j
    induction j with
    | zero =>
      intro _ l hl
      simp only [Nat.zero_mul, Ex_zero, Nat.sub_zero, pow_zero, mul_one, hF, le_refl]
    | succ j ih =>
      intro hj l hl
      rw [show (j + 1) * Lb = Lb + j * Lb by ring, Ex_split]
      have hk : nb - j = (nb - (j + 1)) + 1 := by omega
      calc Ex κ Lb (fun l' => Ex κ (j * Lb) F l') l
          ≤ Ex κ Lb (fun l' => (∏ k ∈ Finset.range (nb - j), blockG Q a0 a1 y Lb T k l') * β ^ j) l := by
            apply Ex_mono_len
            intro t ht
            exact ih (by omega) _ (by simp [ht, hl]; rw [hk]; ring)
        _ = (∏ k ∈ Finset.range (nb - (j + 1)), blockG Q a0 a1 y Lb T k l) * β ^ j *
              Ex κ Lb (blockG Q a0 a1 y Lb T (nb - (j + 1))) l := by
            rw [hk]
            have : ∀ l', (∏ k ∈ Finset.range (nb - (j + 1) + 1), blockG Q a0 a1 y Lb T k l') * β ^ j =
                ((∏ k ∈ Finset.range (nb - (j + 1)), blockG Q a0 a1 y Lb T k l') * β ^ j) *
                  blockG Q a0 a1 y Lb T (nb - (j + 1)) l' := by
              intro l'; rw [Finset.prod_range_succ]; ring
            simp only [this]
            rw [Ex_mul_fixed]
            intro t ht
            congr 1
            apply Finset.prod_congr rfl
            intro k hk'
            rw [Finset.mem_range] at hk'
            apply blockG_append
            rw [hl]
            have : (k + 1) * Lb ≤ (nb - (j + 1)) * Lb := Nat.mul_le_mul_right _ (by omega)
            nlinarith
        _ ≤ (∏ k ∈ Finset.range (nb - (j + 1)), blockG Q a0 a1 y Lb T k l) * β ^ j * β := by
            apply mul_le_mul_of_nonneg_left (hone _ l hl)
            apply mul_nonneg (Finset.prod_nonneg fun k _ => hg0 k l)
            have hβ0 : 0 ≤ β := by
              have := Ex_nonneg (κ := κ) Lb (fun x => hg0 0 x) (List.replicate y Out.empty)
              have h1 := hone 0 (List.replicate y Out.empty) (by simp)
              linarith
            exact pow_nonneg hβ0 _
        _ = _ := by ring
  have hβ0 : 0 ≤ β := by
    have := Ex_nonneg (κ := κ) Lb (fun x => hg0 0 x) (List.replicate y Out.empty)
    have h1 := hone 0 (List.replicate y Out.empty) (by simp)
    linarith
  rw [show M = y + (nb * Lb + (M - y - nb * Lb)) by omega, Ex_split]
  have hdet : ∀ l : List Out, l.length = y + nb * Lb →
      Ex κ (M - y - nb * Lb) F l = F l := fun l hl =>
    Ex_det _ l fun t _ => Finset.prod_congr rfl fun k hk => blockG_append Q a0 a1 t (by
      rw [Finset.mem_range] at hk
      have : (k + 1) * Lb ≤ nb * Lb := Nat.mul_le_mul_right _ (by omega)
      rw [hl]; nlinarith)
  calc Ex κ y (fun l => Ex κ (nb * Lb + (M - y - nb * Lb)) F l) []
      ≤ Ex κ y (fun _ => β ^ nb) [] := by
        apply Ex_mono_len
        intro t ht
        simp only [List.nil_append]
        rw [Ex_split]
        calc Ex κ (nb * Lb) (fun l' => Ex κ (M - y - nb * Lb) F l') t
            = Ex κ (nb * Lb) F t := by
              apply le_antisymm <;> apply Ex_mono_len <;> intro t' ht' <;>
                rw [hdet _ (by simp [ht, ht'])]
          _ ≤ (∏ k ∈ Finset.range (nb - nb), blockG Q a0 a1 y Lb T k t) * β ^ nb :=
              key nb le_rfl t (by simp [ht])
          _ = β ^ nb := by simp
    _ = β ^ nb := Ex_const _ _ _

end Cryptarchia.Prob
