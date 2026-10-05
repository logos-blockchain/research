import Mathlib
import Cryptarchia.Settle.Tree

/-!
# Slot kernels

The probability layer of the settlement theorem. The lottery string is sampled slot
by slot: each slot's outcome is drawn from a distribution that may depend on all
earlier outcomes (a **kernel**). This covers participation and stake that change
over time, and a total-stake estimate that reacts to past outcomes.

* `Out`: the outcome of one slot, as the settlement analysis sees it: no honest
  leader, exactly one, or two or more; and whether the adversary wins.
* `Kern`: the distribution of the next slot given the outcomes so far.
* `Ex κ n F l`: the expectation of `F` after `n` more slots, from history `l`.
* `ExU κ S n G l`: the expectation of `G` when sampling stops at the first history
  satisfying `S` (or after `n` slots).
* `Ex_super`, `Ex_phase`: supermartingale bounds, slot by slot and phase by phase.
-/

namespace Cryptarchia.Prob

open Finset Settle

/-- The outcome of one slot: the number of honest leaders (`0`, `1`, or `2` for two
or more) and whether the adversary wins. -/
structure Out where
  hon : Fin 3
  adv : Bool
  deriving DecidableEq, Fintype

/-- An empty slot. -/
def Out.empty : Out := ⟨0, false⟩

instance : Inhabited Out := ⟨Out.empty⟩

/-- The slot as an entry of a characteristic string. -/
def Out.toPair (o : Out) : ℕ × Bool := (o.hon.val, o.adv)

/-- The characteristic string of a list of outcomes: slot `i ≥ 1` is the `i`-th
outcome; slots past the end are empty. -/
def strOf (l : List Out) : CStr := fun i =>
  if i = 0 then (0, false) else (l.getD (i - 1) Out.empty).toPair

theorem strOf_append_of_le {l m : List Out} {i : ℕ} (hi : i ≤ l.length) :
    strOf (l ++ m) i = strOf l i := by
  unfold strOf
  split_ifs with h0
  · rfl
  · congr 1
    rw [List.getD_append _ _ _ _ (by omega)]

theorem strOf_last (l : List Out) (o : Out) : strOf (l ++ [o]) (l.length + 1) = o.toPair := by
  unfold strOf
  simp

/-- **A slot kernel**: the distribution of the next slot's outcome, as a function of
the outcomes so far (oldest first). -/
structure Kern where
  p : List Out → Out → ℝ
  nonneg : ∀ l o, 0 ≤ p l o
  sum_one : ∀ l, ∑ o, p l o = 1

variable (κ : Kern)

/-- The expectation of `F` after `n` more slots, from history `l`. -/
noncomputable def Ex : ℕ → (List Out → ℝ) → List Out → ℝ
  | 0, F, l => F l
  | n + 1, F, l => ∑ o, κ.p l o * Ex n F (l ++ [o])

/-- The probability of a set of outcomes for the next slot. -/
noncomputable def Kern.pr (l : List Out) (P : Out → Prop) [DecidablePred P] : ℝ :=
  ∑ o, if P o then κ.p l o else 0

/-- The probability of a whole path of outcomes. -/
noncomputable def Kern.path : List Out → ℝ := fun l =>
  ∏ i : Fin l.length, κ.p (l.take i) l[i]

variable {κ}

theorem Ex_zero (F : List Out → ℝ) (l : List Out) : Ex κ 0 F l = F l := rfl

theorem Ex_succ (n : ℕ) (F : List Out → ℝ) (l : List Out) :
    Ex κ (n + 1) F l = ∑ o, κ.p l o * Ex κ n F (l ++ [o]) := rfl

theorem Ex_mono : ∀ (n : ℕ) {F G : List Out → ℝ} (_ : ∀ l, F l ≤ G l) (l : List Out),
    Ex κ n F l ≤ Ex κ n G l
  | 0, _, _, h, l => h l
  | n + 1, _, _, h, l => by
    simp only [Ex_succ]
    exact Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (Ex_mono n h _) (κ.nonneg l o)

/-- Monotonicity, using only the values at the histories actually reached. -/
theorem Ex_mono_len : ∀ (n : ℕ) {F G : List Out → ℝ} (l : List Out)
    (_ : ∀ m : List Out, m.length = n → F (l ++ m) ≤ G (l ++ m)), Ex κ n F l ≤ Ex κ n G l
  | 0, _, _, l, h => by simpa [Ex_zero] using h [] rfl
  | n + 1, _, _, l, h => by
    simp only [Ex_succ]
    refine Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left ?_ (κ.nonneg l o)
    exact Ex_mono_len n _ fun m hm => by
      simpa [List.append_assoc] using h (o :: m) (by simp [hm])

theorem Ex_const : ∀ (n : ℕ) (c : ℝ) (l : List Out), Ex κ n (fun _ => c) l = c
  | 0, _, _ => rfl
  | n + 1, c, l => by
    simp only [Ex_succ, Ex_const n c]
    rw [← Finset.sum_mul, κ.sum_one, one_mul]

theorem Ex_add : ∀ (n : ℕ) (F G : List Out → ℝ) (l : List Out),
    Ex κ n (fun x => F x + G x) l = Ex κ n F l + Ex κ n G l
  | 0, _, _, _ => rfl
  | n + 1, F, G, l => by
    simp only [Ex_succ, Ex_add n F G, mul_add, Finset.sum_add_distrib]

theorem Ex_mul_const : ∀ (n : ℕ) (c : ℝ) (F : List Out → ℝ) (l : List Out),
    Ex κ n (fun x => c * F x) l = c * Ex κ n F l
  | 0, _, _, _ => rfl
  | n + 1, c, F, l => by
    simp only [Ex_succ, Ex_mul_const n c F, Finset.mul_sum]
    exact Finset.sum_congr rfl fun o _ => by ring

theorem Ex_nonneg (n : ℕ) {F : List Out → ℝ} (h : ∀ l, 0 ≤ F l) (l : List Out) : 0 ≤ Ex κ n F l := by
  have := Ex_mono (κ := κ) n (F := fun _ => 0) (G := F) h l
  rwa [Ex_const] at this

theorem Ex_sum {ι : Type*} (s : Finset ι) (n : ℕ) (F : ι → List Out → ℝ) (l : List Out) :
    Ex κ n (fun x => ∑ i ∈ s, F i x) l = ∑ i ∈ s, Ex κ n (F i) l := by
  classical
  induction s using Finset.induction_on with
  | empty => simp [Ex_const]
  | insert a s ha ih =>
    simp only [Finset.sum_insert ha]
    rw [Ex_add, ih]

/-- **Supermartingale bound, slot by slot.** If `Φ` does not increase in expectation
over any one slot before the horizon `M`, its expectation at the horizon is at most
its value now. -/
theorem Ex_super {Φ : List Out → ℝ} {M : ℕ}
    (h : ∀ l : List Out, l.length < M → ∑ o, κ.p l o * Φ (l ++ [o]) ≤ Φ l) :
    ∀ (n : ℕ) (l : List Out), l.length + n ≤ M → Ex κ n Φ l ≤ Φ l
  | 0, _, _ => le_rfl
  | n + 1, l, hl => by
    rw [Ex_succ]
    calc ∑ o, κ.p l o * Ex κ n Φ (l ++ [o])
        ≤ ∑ o, κ.p l o * Φ (l ++ [o]) :=
          Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left
            (Ex_super h n (l ++ [o]) (by simp; omega)) (κ.nonneg l o)
      _ ≤ Φ l := h l (by omega)

/-! ## Sampling until a stopping rule -/

/-- The expectation of `G` when sampling stops at the first history satisfying `S`,
or after `n` slots. -/
noncomputable def ExU (S : List Out → Prop) [DecidablePred S] : ℕ → (List Out → ℝ) → List Out → ℝ
  | 0, G, l => G l
  | n + 1, G, l => if S l then G l else ∑ o, κ.p l o * ExU S n G (l ++ [o])

variable (S : List Out → Prop) [DecidablePred S]

theorem ExU_zero (G : List Out → ℝ) (l : List Out) : ExU (κ := κ) S 0 G l = G l := rfl

theorem ExU_stop (n : ℕ) (G : List Out → ℝ) {l : List Out} (h : S l) : ExU (κ := κ) S n G l = G l := by
  cases n <;> simp [ExU, h]

theorem ExU_go (n : ℕ) (G : List Out → ℝ) {l : List Out} (h : ¬ S l) :
    ExU (κ := κ) S (n + 1) G l = ∑ o, κ.p l o * ExU (κ := κ) S n G (l ++ [o]) := by
  simp [ExU, h]

theorem ExU_mono : ∀ (n : ℕ) {F G : List Out → ℝ} (_ : ∀ l, F l ≤ G l) (l : List Out),
    ExU (κ := κ) S n F l ≤ ExU (κ := κ) S n G l
  | 0, _, _, h, l => h l
  | n + 1, F, G, h, l => by
    by_cases hS : S l
    · rw [ExU_stop S _ F hS, ExU_stop S _ G hS]; exact h l
    · rw [ExU_go S n F hS, ExU_go S n G hS]
      exact Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (ExU_mono n h _) (κ.nonneg l o)

theorem ExU_const : ∀ (n : ℕ) (c : ℝ) (l : List Out), ExU (κ := κ) S n (fun _ => c) l = c
  | 0, _, _ => rfl
  | n + 1, c, l => by
    by_cases hS : S l
    · rw [ExU_stop S _ _ hS]
    · rw [ExU_go S n _ hS]
      simp only [ExU_const n c]
      rw [← Finset.sum_mul, κ.sum_one, one_mul]

theorem ExU_add : ∀ (n : ℕ) (F G : List Out → ℝ) (l : List Out),
    ExU (κ := κ) S n (fun x => F x + G x) l = ExU (κ := κ) S n F l + ExU (κ := κ) S n G l
  | 0, _, _, _ => rfl
  | n + 1, F, G, l => by
    by_cases hS : S l
    · simp only [ExU_stop S _ _ hS]
    · simp only [ExU_go S n _ hS, ExU_add n F G, mul_add, Finset.sum_add_distrib]

theorem ExU_mul_const : ∀ (n : ℕ) (c : ℝ) (F : List Out → ℝ) (l : List Out),
    ExU (κ := κ) S n (fun x => c * F x) l = c * ExU (κ := κ) S n F l
  | 0, _, _, _ => rfl
  | n + 1, c, F, l => by
    by_cases hS : S l
    · simp only [ExU_stop S _ _ hS]
    · simp only [ExU_go S n _ hS, ExU_mul_const n c F, Finset.mul_sum]
      exact Finset.sum_congr rfl fun o _ => by ring

theorem ExU_nonneg (n : ℕ) {F : List Out → ℝ} (h : ∀ l, 0 ≤ F l) (l : List Out) :
    0 ≤ ExU (κ := κ) S n F l := by
  have := ExU_mono (κ := κ) S n (F := fun _ => 0) (G := F) h l
  rwa [ExU_const] at this

/-- The expectation over the next phase from a history `l`: one slot is always
sampled, then sampling stops at the first history satisfying `S`. -/
noncomputable def ExPh (n : ℕ) (G : List Out → ℝ) (l : List Out) : ℝ :=
  ∑ o, κ.p l o * ExU (κ := κ) S n G (l ++ [o])

/-- **Supermartingale bound, phase by phase.** Let `S` mark the phase ends. If `Φ`
does not increase in expectation over any one phase that starts before the
horizon `M`, then its expectation at the horizon is at most its value at the start. -/
theorem Ex_phase {Φ : List Out → ℝ} {M : ℕ}
    (h : ∀ l : List Out, S l → l.length < M → ExPh (κ := κ) S (M - l.length - 1) Φ l ≤ Φ l)
    {l : List Out} (hl : S l) (hlM : l.length ≤ M) :
    Ex κ (M - l.length) Φ l ≤ Φ l := by
  -- the stopped value at every history
  set Ψ : List Out → ℝ := fun x => ExU (κ := κ) S (M - x.length) Φ x with hΨ
  have hstep : ∀ x : List Out, x.length < M → ∑ o, κ.p x o * Ψ (x ++ [o]) ≤ Ψ x := by
    intro x hx
    have hlen : ∀ o : Out, M - (x ++ [o]).length = M - x.length - 1 := fun o => by simp; omega
    have hsplit : M - x.length = (M - x.length - 1) + 1 := by omega
    simp only [hΨ, hlen]
    by_cases hS : S x
    · rw [ExU_stop S _ _ hS]; exact h x hS hx
    · rw [hsplit, ExU_go S _ _ hS]
      simp only [Nat.add_sub_cancel, le_refl]
  have hfin : Ex κ (M - l.length) Φ l = Ex κ (M - l.length) Ψ l := by
    apply le_antisymm
    · apply Ex_mono_len
      intro m hm
      have : M - (l ++ m).length = 0 := by simp; omega
      simp only [hΨ, this, ExU_zero, le_refl]
    · apply Ex_mono_len
      intro m hm
      have : M - (l ++ m).length = 0 := by simp; omega
      simp only [hΨ, this, ExU_zero, le_refl]
  rw [hfin]
  calc Ex κ (M - l.length) Ψ l ≤ Ψ l := Ex_super hstep _ l (by omega)
    _ = Φ l := by simp only [hΨ]; exact ExU_stop S _ _ hl

end Cryptarchia.Prob
