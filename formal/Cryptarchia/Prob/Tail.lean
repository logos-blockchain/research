module

public import Cryptarchia.Prob.Kernel
public import Cryptarchia.Settle.Tree
import Cryptarchia.Prob.Potential
public import Cryptarchia.Proof.FinalE
public import Cryptarchia.Prob.Next
import Cryptarchia.Settle.Mono
import Std.Tactic.BVDecide.Normalize.Prop
import Mathlib.Data.Nat.Choose.Multinomial

/-!
# The bad events as block products

On a full sampled history, bad events of the settlement bound as products over blocks of
slots, whose expectations `blocks_le` bounds: long phases (`longF`; a phase that starts by
`N` is short when every `G` slots hold a quiet slot, `phase_short`), crowded windows
(`winF`) and slow growth (`depthF`, over the growth blocks `nbD`).
-/

@[expose] public section

namespace Cryptarchia.Prob

/-!
## Products over blocks of slots

A generic Chernoff-type bound. Cut the slots after `y` into `nb` consecutive
blocks of `Lb` slots, and call block `k` a **success** if one of its first `T`
slots satisfies `Q`. If every slot satisfies `Q` with conditional probability at
most `qhi` (or at least `qlo`), then for weights `g true = a1`, `g false = a0`,

  `E[∏_k g(success_k)] ≤ β^nb`,   `β = a0 + (a1 - a0) · P_T`,

with `P_T = 1 - (1 - qhi)^T` if `a1 ≥ a0` and `1 - (1 - qlo)^T` otherwise
(`blocks_le`). Instances: long phases (no block of `Δ` slots free of honest
leaders), the occupancy window, and honest-depth growth.
-/

section

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

end

/-!
## Honest depth over blocks

Honest depth `hD a b` (Def. 6 of Gaži–Ren–Russell: the greedy count of honest
slots more than `Δ` apart in `(a, b]`) is monotone in `b` (`hD_mono`) and
superadditive across a gap of `Δ` slots (`hD_super`). So over blocks of `T` slots
separated by gaps of `Δ`, it is at least the number of blocks with an honest
success (`hD_blocks`).
-/

section

open Finset Settle

variable {Δ : ℕ} {w : CStr}

/-- Monotone in the right end, and a window of at most `Δ + 1` slots adds at most one. -/
theorem hD_mono_aux (a : ℕ) : ∀ b, (∀ b' ≤ b, hD Δ w a b' ≤ hD Δ w a b) ∧
    (∀ d ≤ Δ + 1, hD Δ w a b ≤ hD Δ w a (b - d) + 1) := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    -- the window property at `b`
    have hL : ∀ d ≤ Δ + 1, hD Δ w a b ≤ hD Δ w a (b - d) + 1 := by
      intro d hd
      rcases Nat.eq_zero_or_pos d with rfl | hd0
      · simp
      unfold hD
      by_cases hb : b ≤ a
      · simp only [hb, ↓reduceDIte]; omega
      · simp only [hb, ↓reduceDIte]
        by_cases hw : (w b).1 = 0
        · simp only [hw, ↓reduceIte]
          have := (ih (b - 1) (by omega)).2 (d - 1) (by omega)
          rw [show b - 1 - (d - 1) = b - d by omega] at this
          conv_rhs => rw [← hD.eq_def]
          exact this
        · simp only [hw, ↓reduceIte]
          have hm := (ih (b - d) (by omega)).1 (b - Δ - 1) (by omega)
          conv_rhs => rw [← hD.eq_def]
          omega
    refine ⟨?_, hL⟩
    intro b' hb'
    rcases Nat.eq_or_lt_of_le hb' with rfl | hlt
    · exact le_rfl
    · -- `b' ≤ b - 1 < b`
      have h1 := (ih (b - 1) (by omega)).1 b' (by omega)
      have h2 : hD Δ w a (b - 1) ≤ hD Δ w a b := by
        conv_rhs => unfold hD
        by_cases hb : b ≤ a
        · have : hD Δ w a (b - 1) = 0 := by unfold hD; simp [show b - 1 ≤ a by omega]
          simp [hb, this]
        · simp only [hb, ↓reduceDIte]
          by_cases hw : (w b).1 = 0
          · simp only [hw, ↓reduceIte, le_refl]
          · simp only [hw, ↓reduceIte]
            have := (ih (b - 1) (by omega)).2 Δ (by omega)
            rw [show b - 1 - Δ = b - Δ - 1 by omega] at this
            exact this
      omega

theorem hD_mono {a b b' : ℕ} (h : b' ≤ b) : hD Δ w a b' ≤ hD Δ w a b := (hD_mono_aux a b).1 b' h

/-- **Superadditivity across a gap of `Δ` slots.** -/
theorem hD_super {a m : ℕ} (ham : a ≤ m) : ∀ b, m + Δ ≤ b →
    hD Δ w a m + hD Δ w (m + Δ) b ≤ hD Δ w a b := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    intro hb
    by_cases hbm : b ≤ m + Δ
    · have : b = m + Δ := by omega
      subst this
      have h0 : hD Δ w (m + Δ) (m + Δ) = 0 := by unfold hD; simp
      rw [h0, add_zero]; exact hD_mono (by omega)
    · conv_lhs => arg 2; unfold hD
      conv_rhs => unfold hD
      have hb1 : ¬ b ≤ m + Δ := hbm
      have hb2 : ¬ b ≤ a := by omega
      simp only [hb1, hb2, ↓reduceDIte]
      by_cases hw : (w b).1 = 0
      · simp only [hw, ↓reduceIte]
        exact ih (b - 1) (by omega) (by omega)
      · simp only [hw, ↓reduceIte]
        by_cases hc : m + Δ ≤ b - Δ - 1
        · have := ih (b - Δ - 1) (by omega) hc
          omega
        · have h0 : hD Δ w (m + Δ) (b - Δ - 1) = 0 := by unfold hD; simp [show b - Δ - 1 ≤ m + Δ by omega]
          rw [h0]
          have := hD_mono (Δ := Δ) (w := w) (a := a) (show m ≤ b - Δ - 1 by omega)
          omega

/-- An honest success in block `i`: some slot among the first `T` after `y + i Lb`. -/
def blockHon (w : CStr) (y Lb T i : ℕ) : Prop := ∃ j, y + i * Lb < j ∧ j ≤ y + i * Lb + T ∧ (w j).1 ≠ 0

/-- **Honest depth over blocks.** With blocks of `T` slots followed by gaps of `Δ`
(`Lb = T + Δ`), honest depth over the first `n` blocks is at least the number of
blocks with an honest success. -/
theorem hD_blocks {y T Lb : ℕ} (hLb : Lb = T + Δ) [DecidablePred fun i => blockHon w y Lb T i] :
    ∀ n, ((Finset.range (n + 1)).filter fun i => blockHon w y Lb T i).card ≤
      hD Δ w y (y + n * Lb + T) := by
  intro n
  induction n with
  | zero =>
    simp only [zero_add, Finset.range_one, Finset.filter_singleton, zero_mul, add_zero]
    split_ifs with hh
    · obtain ⟨j, h1, h2, h3⟩ := hh
      simp only [Finset.card_singleton]
      exact one_le_hD _ ⟨j, by simpa using h1, by simpa using h2, h3⟩
    · simp
  | succ n ih =>
    rw [Finset.range_add_one, Finset.filter_insert]
    have hsup := hD_super (Δ := Δ) (w := w) (a := y) (m := y + n * Lb + T) (by omega)
      (y + (n + 1) * Lb + T) (by rw [hLb]; ring_nf; omega)
    have hstart : y + n * Lb + T + Δ = y + (n + 1) * Lb := by rw [hLb]; ring
    rw [hstart] at hsup
    split_ifs with hh
    · have hnot : n + 1 ∉ (Finset.range (n + 1)).filter fun i => blockHon w y Lb T i := by simp
      rw [Finset.card_insert_of_notMem hnot]
      have h1 : 1 ≤ hD Δ w (y + (n + 1) * Lb) (y + (n + 1) * Lb + T) := by
        obtain ⟨j, h1, h2, h3⟩ := hh
        exact one_le_hD _ ⟨j, h1, h2, h3⟩
      omega
    · omega

end

section

open Finset Settle

variable {Δ M N W : ℕ}

/-- A phase that starts by `N` ends within `G` slots. -/
theorem phase_short {w : CStr} {G : ℕ} (hNG : N + G < M)
    (hq : ∀ y ≤ N, ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ w m) {j : ℕ} (hj : gend Δ M w j ≤ N) :
    gend Δ M w (j + 1) ≤ gend Δ M w j + G := by
  obtain ⟨m, h1, h2, h3⟩ := hq _ hj
  rw [gend_succ]
  exact le_trans (nextE_le_of_quiet h1 (by omega) h3) h2

theorem gend_pidx_M {w : CStr} : gend Δ M w (pidx Δ M w M) = M :=
  gend_pidx_of_end (Or.inr (Or.inl rfl))

end

open Finset Settle

/-- Some honest leader. -/
def honQ (o : Out) : Prop := o.hon ≠ 0

/-- An occupied slot. -/
def occQ (o : Out) : Prop := o.hon ≠ 0 ∨ o.adv = true

instance : DecidablePred honQ := fun o => inferInstanceAs (Decidable (o.hon ≠ 0))
instance : DecidablePred occQ := fun o => inferInstanceAs (Decidable (o.hon ≠ 0 ∨ o.adv = true))

theorem strOf_fst (l : List Out) {i : ℕ} (hi : 1 ≤ i) : (strOf l i).1 = (l.getD (i - 1) Out.empty).hon.val := by
  have hi0 : i ≠ 0 := by omega
  unfold strOf; simp [hi0, Out.toPair]

theorem strOf_snd (l : List Out) {i : ℕ} (hi : 1 ≤ i) : (strOf l i).2 = (l.getD (i - 1) Out.empty).adv := by
  have hi0 : i ≠ 0 := by omega
  unfold strOf; simp [hi0, Out.toPair]

theorem honQ_iff (l : List Out) {i : ℕ} (hi : 1 ≤ i) : honQ (l.getD (i - 1) Out.empty) ↔ (strOf l i).1 ≠ 0 := by
  rw [strOf_fst l hi]; unfold honQ; constructor
  · intro h h'; exact h (Fin.ext h')
  · intro h h'; exact h (by rw [h']; rfl)

theorem occQ_iff (l : List Out) {i : ℕ} (hi : 1 ≤ i) :
    occQ (l.getD (i - 1) Out.empty) ↔ (1 ≤ (strOf l i).1 ∨ (strOf l i).2 = true) := by
  have h1 := honQ_iff l hi
  unfold honQ at h1; unfold occQ
  rw [strOf_snd l hi, h1, Nat.one_le_iff_ne_zero]

theorem prod_ite_pow {a : ℝ} (P : ℕ → Prop) [DecidablePred P] (n : ℕ) :
    ∏ i ∈ Finset.range n, (if P i then a else 1) = a ^ ((Finset.range n).filter P).card := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Finset.prod_range_succ, ih, Finset.range_add_one, Finset.filter_insert]
    split_ifs with h
    · rw [Finset.card_insert_of_notMem (by simp), pow_succ]
    · rw [mul_one]

theorem occCnt_succ (w : CStr) {a b : ℕ} (hab : a ≤ b) :
    occCnt w a (b + 1) = occCnt w a b + (if 1 ≤ (w (b + 1)).1 ∨ (w (b + 1)).2 = true then 1 else 0) := by
  unfold occCnt
  rw [show Finset.Ioc a (b + 1) = insert (b + 1) (Finset.Ioc a b) by
    ext i; simp only [Finset.mem_Ioc, Finset.mem_insert]; omega, Finset.filter_insert]
  split_ifs with h
  · rw [Finset.card_insert_of_notMem (by simp)]
  · rw [add_zero]

theorem occ_count (l : List Out) (y : ℕ) : ∀ n,
    ((Finset.range n).filter fun k => occQ (l.getD (y + k) Out.empty)).card = occCnt (strOf l) y (y + n) := by
  intro n
  induction n with
  | zero => simp [occCnt]
  | succ n ih =>
    rw [Finset.range_add_one, Finset.filter_insert, show y + (n + 1) = (y + n) + 1 by omega,
      occCnt_succ _ (by omega), ← ih]
    have := occQ_iff l (i := y + n + 1) (by omega)
    rw [show y + n + 1 - 1 = y + n by omega] at this
    split_ifs with h1 h2 h2
    · rw [Finset.card_insert_of_notMem (by simp)]
    · exact absurd (this.1 h1) h2
    · exact absurd (this.2 h2) h1
    · rw [add_zero]

variable {B : Band} {Δ M : ℕ} {κ : Kern}

theorem pr_occ_le (hB : κ.Within B) (l : List Out) : κ.pr l occQ ≤ 1 - B.elo := by
  have hsum := κ.sum_one l
  have he := hB.elo l
  have h1 : ∑ o, κ.p l o = κ.pr l occQ + ∑ o, (if occQ o then 0 else κ.p l o) := by
    unfold Kern.pr; rw [← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl fun o _ => by split_ifs <;> ring
  have h2 : κ.p l ⟨0, false⟩ ≤ ∑ o, (if occQ o then 0 else κ.p l o) := by
    have := Finset.single_le_sum (f := fun o => if occQ o then 0 else κ.p l o)
      (fun o _ => by split_ifs <;> linarith [κ.nonneg l o]) (Finset.mem_univ (⟨0, false⟩ : Out))
    simpa [occQ] using this
  linarith

/-! ## The bad events as products -/

variable (Δ) in
/-- Every block of `Δ` slots after `y` (up to `G`) has an honest leader. -/
noncomputable def longF (G y : ℕ) (h : List Out) : ℝ :=
  ∏ k ∈ Finset.range (G / Δ), blockG honQ 0 1 y Δ Δ k h

/-- `x` to the number of occupied slots in the window before `t`. -/
noncomputable def winF (Lw : ℕ) (x : ℝ) (t : ℕ) (h : List Out) : ℝ :=
  ∏ k ∈ Finset.range (t - (t - Lw)), blockG occQ 1 x (t - Lw) 1 1 k h

/-- `yy` to the number of blocks with an honest leader. -/
noncomputable def depthF (yy : ℝ) (a Lb T nb : ℕ) (h : List Out) : ℝ :=
  ∏ i ∈ Finset.range nb, blockG honQ 1 yy a Lb T i h

open Classical in
theorem blockG_cases (Q : Out → Prop) [DecidablePred Q] (a0 a1 : ℝ) (y Lb T k : ℕ) (h : List Out) :
    blockG Q a0 a1 y Lb T k h = if hitIn Q (y + k * Lb) T h then a1 else a0 := by
  unfold blockG; rfl

theorem longF_one {G y : ℕ} {h : List Out} (hno : ¬ ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ (strOf h) m) :
    longF Δ G y h = 1 := by
  classical
  unfold longF
  apply Finset.prod_eq_one
  intro k hk
  rw [Finset.mem_range] at hk
  rw [blockG_cases, if_pos]
  by_contra hnot
  apply hno
  refine ⟨y + k * Δ + Δ, ?_, ?_, ?_⟩
  · rcases Nat.eq_zero_or_pos Δ with h0 | h0
    · simp [h0] at hk
    · omega
  · have : (k + 1) * Δ ≤ G := by
      have := Nat.div_mul_le_self G Δ
      nlinarith [Nat.mul_le_mul_right Δ (show k + 1 ≤ G / Δ by omega)]
    nlinarith
  · intro i h1 h2 h3
    have := honQ_iff h h3
    by_contra hne
    exact hnot ⟨i, by omega, by omega, this.2 hne⟩

theorem winF_eq {Lw : ℕ} {x : ℝ} (t : ℕ) (h : List Out) :
    winF Lw x t h = x ^ occCnt (strOf h) (t - Lw) t := by
  classical
  unfold winF
  simp only [blockG_cases]
  have : ∀ k, hitIn occQ (t - Lw + k * 1) 1 h ↔ occQ (h.getD (t - Lw + k) Out.empty) := by
    intro k; unfold hitIn; constructor
    · rintro ⟨i, h1, h2, h3⟩
      have : i = t - Lw + k + 1 := by omega
      subst this; simpa using h3
    · intro hq; exact ⟨t - Lw + k + 1, by omega, by omega, by simpa using hq⟩
  simp only [this]
  rw [prod_ite_pow, occ_count, show t - Lw + (t - (t - Lw)) = t by omega]

theorem depthF_eq {yy : ℝ} {a Lb T nb : ℕ} (h : List Out) [DecidablePred fun i => blockHon (strOf h) a Lb T i] :
    depthF yy a Lb T nb h = yy ^ ((Finset.range nb).filter fun i => blockHon (strOf h) a Lb T i).card := by
  classical
  unfold depthF
  simp only [blockG_cases]
  have : ∀ i, hitIn honQ (a + i * Lb) T h ↔ blockHon (strOf h) a Lb T i := by
    intro i; unfold hitIn blockHon; constructor
    · rintro ⟨j, h1, h2, h3⟩; exact ⟨j, h1, h2, (honQ_iff h (by omega)).1 h3⟩
    · rintro ⟨j, h1, h2, h3⟩; exact ⟨j, h1, h2, (honQ_iff h (by omega)).2 h3⟩
  simp only [this]
  rw [prod_ite_pow]

/-! ## The bad indicator -/

/-- The slots of the growth window of an epoch, after the first `G`. -/
def growLen (E : Env) (Δ G : ℕ) : ℕ := E.c.epochLength - E.c.nonceOffset - Δ - 3 - G

/-- The number of depth blocks in an epoch's growth window. -/
def nbD (E : Env) (Δ G T : ℕ) : ℕ := (growLen E Δ G + Δ) / (T + Δ)

/-- The epochs whose state is fixed by `N`. -/
def nEp (E : Env) (N : ℕ) : ℕ := (N + 2) / E.c.epochLength

theorem blockG_nonneg (Q : Out → Prop) [DecidablePred Q] {a0 a1 : ℝ} (h0 : 0 ≤ a0) (h1 : 0 ≤ a1)
    (y Lb T k : ℕ) (h : List Out) : 0 ≤ blockG Q a0 a1 y Lb T k h := by
  rw [blockG_cases]; split_ifs <;> assumption

/-! ## The bound -/

theorem Ex_div (n : ℕ) (F : List Out → ℝ) (a : ℝ) (l : List Out) :
    Ex κ n (fun x => F x / a) l = Ex κ n F l / a := by
  simp only [div_eq_mul_inv]
  rw [show (fun x => F x * a⁻¹) = (fun x => a⁻¹ * F x) by ext; ring, Ex_mul_const]; ring

end Cryptarchia.Prob
