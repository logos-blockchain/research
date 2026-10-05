import Cryptarchia.Prob.Burst

/-!
# Phase expectations through a small automaton

A sharper version of `phase_upper`. Over one phase, we bound

  `E[θ^L · x^A · g(min(A, 2), B, U2)]`

for any nonnegative table `g`, where `A` counts adversarial slots, `B` says the phase
has an honest success, and `U2` says it has at least two slots with honest successes.
During a burst the automaton tracks the slots since the last honest success (`q`),
`min(A, 2)` and `U2`; a solution `v` of its recursion (`AutoSol`) bounds the rest of
the phase from every state (`auto_le`, `phase_auto`). Each step is bounded for every
next-slot distribution in the band (`slot_sum4`).
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {κ : Kern} {B : Band}

/-- **One slot, four outcome classes.** `F h a` is the value after a slot with
(`h`) or without an honest success and with (`a`) or without an adversarial one. -/
theorem slot_sum4 {l : List Out} (hB : κ.BandAt B l) (F : Bool → Bool → ℝ) :
    ∑ o, κ.p l o * F (decide (o.hon ≠ 0)) o.adv ≤
      F false false + (F false true - F false false) * (if F false false ≤ F false true then B.amax else B.alo) +
        (F true false - F false false) * (if F false false ≤ F true false then B.hhi else B.hlo) +
        (F true true - F true false - F false true + F false false) *
          (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo) := by
  set c1 := F false true - F false false
  set c2 := F true false - F false false
  set c3 := F true true - F true false - F false true + F false false
  have hsplit : ∀ o, κ.p l o * F (decide (o.hon ≠ 0)) o.adv =
      κ.p l o * F false false + c1 * (if o.adv = true then κ.p l o else 0) +
        c2 * (if o.hon ≠ 0 then κ.p l o else 0) + c3 * (if o.hon ≠ 0 ∧ o.adv = true then κ.p l o else 0) := by
    intro o
    by_cases h1 : o.hon ≠ 0 <;> by_cases h2 : o.adv = true <;> simp [h1, h2, c1, c2, c3] <;> ring
  simp only [hsplit, Finset.sum_add_distrib, ← Finset.mul_sum, ← Finset.sum_mul, κ.sum_one, one_mul]
  have e1 : ∑ o, (if o.adv = true then κ.p l o else 0) = κ.pr l (fun o => o.adv = true) := rfl
  have e2 : ∑ o, (if o.hon ≠ 0 then κ.p l o else 0) = κ.pr l (fun o => o.hon ≠ 0) := rfl
  have e3 : ∑ o, (if o.hon ≠ 0 ∧ o.adv = true then κ.p l o else 0) =
      κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) := rfl
  rw [e1, e2, e3]
  have ha := hB.amax
  have ha0 := pr_nonneg (κ := κ) l (fun o => o.adv = true)
  have hh := hB.hhi
  have hlo := hB.hlo
  have hha := hB.hahi
  have hha0 := pr_nonneg (κ := κ) l (fun o => o.hon ≠ 0 ∧ o.adv = true)
  have t1 : c1 * κ.pr l (fun o => o.adv = true) ≤
      c1 * (if F false false ≤ F false true then B.amax else B.alo) := by
    split_ifs with h
    · exact mul_le_mul_of_nonneg_left ha (by simp only [c1]; linarith)
    · push Not at h; exact mul_le_mul_of_nonpos_left (hB.alo) (by simp only [c1]; linarith)
  have t2 : c2 * κ.pr l (fun o => o.hon ≠ 0) ≤
      c2 * (if F false false ≤ F true false then B.hhi else B.hlo) := by
    split_ifs with h
    · exact mul_le_mul_of_nonneg_left hh (by simp only [c2]; linarith)
    · push Not at h; exact mul_le_mul_of_nonpos_left hlo (by simp only [c2]; linarith)
  have t3 : c3 * κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) ≤
      c3 * (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo) := by
    split_ifs with h
    · exact mul_le_mul_of_nonneg_left hha (by simp only [c3]; linarith)
    · push Not at h; exact mul_le_mul_of_nonpos_left (hB.halo) (by simp only [c3]; linarith)
  linarith

/-- The bound `slot_sum4` gives, as a function. -/
noncomputable def slot4 (B : Band) (F : Bool → Bool → ℝ) : ℝ :=
  F false false + (F false true - F false false) * (if F false false ≤ F false true then B.amax else B.alo) +
    (F true false - F false false) * (if F false false ≤ F true false then B.hhi else B.hlo) +
    (F true true - F true false - F false true + F false false) *
      (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo)

/-! ## The phase summary -/

/-- Honest slots in `(a, b]`. -/
def honCnt (w : CStr) (a b : ℕ) : ℕ := ((Finset.Ioc a b).filter (fun j => (w j).1 ≠ 0)).card

/-- `min(A, 2)`. -/
def acap (n : ℕ) : Fin 3 := ⟨min n 2, by omega⟩

/-- The weight of a history for a phase that started at `m`, with table `g`. -/
noncomputable def Wt2 (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ) (m : ℕ) (h : List Out) : ℝ :=
  θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length *
    g (acap (advCnt (strOf h) m h.length)) (decide (1 ≤ honCnt (strOf h) m h.length))
      (decide (2 ≤ honCnt (strOf h) m h.length))

/-- A solution of the automaton recursion for adversary factor `x`, tilt `θ` and
terminal table `g`: `v q a u2` bounds the rest of a burst `q` slots after its last
honest success, with `min(A, 2) = a` and `U2 = u2` so far. -/
structure AutoSol (B : Band) (Δ : ℕ) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ)
    (v : ℕ → Fin 3 → Bool → ℝ) : Prop where
  /-- a run cut by the horizon is covered -/
  term : ∀ q < Δ, ∀ a u2, g a true u2 ≤ v q a u2
  /-- the recursion -/
  step : ∀ q < Δ, ∀ a u2, θ * slot4 B (fun hh aa =>
    (if aa then x else 1) *
      (if hh then v 0 (acap (a.val + if aa then 1 else 0)) true
        else if q + 1 = Δ then g (acap (a.val + if aa then 1 else 0)) true u2
          else v (q + 1) (acap (a.val + if aa then 1 else 0)) u2)) ≤ v q a u2

variable {Δ M : ℕ}

theorem honCnt_succ (w : CStr) {a b : ℕ} (hab : a ≤ b) :
    honCnt w a (b + 1) = honCnt w a b + (if (w (b + 1)).1 ≠ 0 then 1 else 0) := by
  unfold honCnt
  rw [show Finset.Ioc a (b + 1) = insert (b + 1) (Finset.Ioc a b) by
    ext i; simp only [Finset.mem_Ioc, Finset.mem_insert]; omega, Finset.filter_insert]
  split_ifs with h
  · rw [Finset.card_insert_of_notMem (by simp)]
  · rw [add_zero]

theorem honCnt_congr {w w' : CStr} {a b : ℕ} (h : SimOn w w' a b) : honCnt w a b = honCnt w' a b := by
  unfold honCnt
  congr 1
  apply Finset.filter_congr
  intro j hj
  rw [Finset.mem_Ioc] at hj
  exact not_congr (h j hj.1 hj.2).1

theorem honCnt_snoc (x : List Out) (o : Out) {m : ℕ} (hm : m ≤ x.length) :
    honCnt (strOf (x ++ [o])) m (x.length + 1) = honCnt (strOf x) m x.length + (if o.hon ≠ 0 then 1 else 0) := by
  rw [honCnt_succ _ hm, honCnt_congr (strOf_sim x [o] m), strOf_last]
  congr 1
  simp only [Out.toPair, ne_eq]
  by_cases h : o.hon = 0
  · simp [h]
  · have : ¬ (o.hon.val = 0) := fun h' => h (Fin.ext h')
    simp [h, this]

theorem acap_add (n : ℕ) (b : ℕ) (hb : b ≤ 1) : acap (n + b) = acap ((acap n).val + b) := by
  unfold acap; ext; simp; omega

theorem Wt2_snoc {x θ : ℝ} {g : Fin 3 → Bool → Bool → ℝ} {m : ℕ} (h : List Out) (o : Out) (hm : m ≤ h.length) :
    Wt2 x θ g m (h ++ [o]) =
      θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length * (θ * (if o.adv then x else 1)) *
        g (acap ((acap (advCnt (strOf h) m h.length)).val + if o.adv then 1 else 0))
          (decide (1 ≤ honCnt (strOf h) m h.length + if o.hon ≠ 0 then 1 else 0))
          (decide (2 ≤ honCnt (strOf h) m h.length + if o.hon ≠ 0 then 1 else 0)) := by
  unfold Wt2
  simp only [List.length_append, List.length_singleton]
  rw [advCnt_snoc h o hm, honCnt_snoc h o hm, show h.length + 1 - m = (h.length - m) + 1 by omega,
    pow_succ, ← acap_add _ _ (by split_ifs <;> norm_num)]
  by_cases ha : o.adv = true
  · simp only [ha, ↓reduceIte, pow_succ]; ring
  · simp only [ha, Bool.false_eq_true, ↓reduceIte, add_zero, mul_one]; ring

/-- **Inside a burst, with the automaton.** -/
theorem auto_le {Bs : List Band} (hFam : κ.Fam Bs) {x θ : ℝ} (hx : 0 ≤ x) (hθ : 0 ≤ θ) {g : Fin 3 → Bool → Bool → ℝ}
    {v : ℕ → Fin 3 → Bool → ℝ} (hv : ∀ B ∈ Bs, AutoSol B Δ x θ g v) {m : ℕ} :
    ∀ (n : ℕ) (h : List Out) (q : ℕ), InBurst m h q → q < Δ → h.length + n = M →
      ExU (κ := κ) (PE Δ M) n (Wt2 x θ g m) h ≤
        θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length *
          v q (acap (advCnt (strOf h) m h.length)) (decide (2 ≤ honCnt (strOf h) m h.length))
  | 0, h, q, hb, hq, hn => by
    have hPE : PE Δ M h := Or.inl (by omega)
    rw [ExU_stop _ _ _ hPE]
    have hB1 : 1 ≤ honCnt (strOf h) m h.length := by
      obtain ⟨i, h1, h2, h3⟩ := hb.honIn
      unfold honCnt; exact Finset.card_pos.2 ⟨i, by simp; exact ⟨⟨h1, h2⟩, h3⟩⟩
    unfold Wt2
    rw [show decide (1 ≤ honCnt (strOf h) m h.length) = true by simpa using hB1]
    obtain ⟨B, hBm, -⟩ := hFam h
    exact mul_le_mul_of_nonneg_left ((hv B hBm).term q hq _ _) (by positivity)
  | n + 1, h, q, hb, hq, hn => by
    classical
    have hm : m ≤ h.length := by have := hb.p_gt; omega
    have hnPE : ¬ PE Δ M h := by
      rintro (h1 | ⟨-, h2⟩)
      · omega
      · exact hb.not_quiet hq h2
    rw [ExU_go _ _ _ hnPE]
    obtain ⟨B, hBm, hBh⟩ := hFam h
    have hvB := hv B hBm
    set W0 := θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length with hW0
    have hW0n : 0 ≤ W0 := by positivity
    set a := acap (advCnt (strOf h) m h.length) with ha
    set nh := honCnt (strOf h) m h.length with hnh
    have hnh1 : 1 ≤ nh := by
      obtain ⟨i, h1, h2, h3⟩ := hb.honIn
      simp only [hnh]; unfold honCnt; exact Finset.card_pos.2 ⟨i, by simp; exact ⟨⟨h1, h2⟩, h3⟩⟩
    set F : Bool → Bool → ℝ := fun hh aa => (if aa then x else 1) *
      (if hh then v 0 (acap (a.val + if aa then 1 else 0)) true
        else if q + 1 = Δ then g (acap (a.val + if aa then 1 else 0)) true (decide (2 ≤ nh))
          else v (q + 1) (acap (a.val + if aa then 1 else 0)) (decide (2 ≤ nh))) with hF
    have hcont : ∀ o, ExU (κ := κ) (PE Δ M) n (Wt2 x θ g m) (h ++ [o]) ≤ W0 * θ * F (decide (o.hon ≠ 0)) o.adv := by
      intro o
      have hWo := Wt2_snoc (x := x) (θ := θ) (g := g) h o hm
      rw [← hW0, ← ha, ← hnh] at hWo
      have hlen : (h ++ [o]).length + n = M := by simp; omega
      have hAo : acap (advCnt (strOf (h ++ [o])) m (h ++ [o]).length) =
          acap (a.val + if o.adv then 1 else 0) := by
        simp only [List.length_append, List.length_singleton]
        rw [advCnt_snoc h o hm, acap_add _ _ (by split_ifs <;> norm_num)]
      have hHo : honCnt (strOf (h ++ [o])) m (h ++ [o]).length = nh + if o.hon ≠ 0 then 1 else 0 := by
        simp only [List.length_append, List.length_singleton]; rw [honCnt_snoc h o hm]
      have hpowo : θ ^ ((h ++ [o]).length - m) * x ^ advCnt (strOf (h ++ [o])) m (h ++ [o]).length =
          W0 * (θ * (if o.adv then x else 1)) := by
        simp only [List.length_append, List.length_singleton]
        rw [advCnt_snoc h o hm, show h.length + 1 - m = (h.length - m) + 1 by omega, pow_succ, hW0]
        by_cases hao : o.adv = true
        · simp only [hao, ↓reduceIte, pow_succ]; ring
        · simp only [hao, Bool.false_eq_true, ↓reduceIte, add_zero, mul_one]; ring
      have hxa : 0 ≤ (if o.adv then x else 1) := by split_ifs <;> linarith
      set a' := acap (a.val + if o.adv then 1 else 0) with ha'
      by_cases ho : o.hon ≠ 0
      · have hb' := hb.snoc_hon o ho
        have hdec : decide (o.hon ≠ 0) = true := by simpa using ho
        have hFt : F true o.adv = (if o.adv then x else 1) * v 0 a' true := rfl
        rw [hdec, hFt]
        have hi1 : (if o.hon ≠ 0 then 1 else 0) = 1 := if_pos ho
        rw [hi1] at hWo hHo
        have d1 : decide (1 ≤ nh + 1) = true := decide_eq_true (by omega)
        have d2 : decide (2 ≤ nh + 1) = true := decide_eq_true (by omega)
        by_cases hM : (h ++ [o]).length = M
        · rw [ExU_stop _ _ _ (Or.inl hM), hWo, d1, d2]
          have := hvB.term 0 (by have := hb.p_gt; omega) a' true
          calc W0 * (θ * (if o.adv then x else 1)) * g a' true true
              ≤ W0 * (θ * (if o.adv then x else 1)) * v 0 a' true :=
                mul_le_mul_of_nonneg_left this (by positivity)
            _ = _ := by ring
        · have hΔ0 : 0 < Δ := by omega
          have := auto_le hFam hx hθ hv n (h ++ [o]) 0 hb' hΔ0 hlen
          rw [hpowo, hAo, hHo, d2] at this
          calc _ ≤ W0 * (θ * (if o.adv then x else 1)) * v 0 a' true := this
            _ = _ := by ring
      · push Not at ho
        have hdec : decide (o.hon ≠ 0) = false := by simpa using ho
        have hb' := hb.snoc_empty o ho
        have hi0 : (if o.hon ≠ 0 then 1 else 0) = 0 := if_neg (by simpa using ho)
        rw [hi0, Nat.add_zero] at hWo hHo
        have d1 : decide (1 ≤ nh) = true := decide_eq_true hnh1
        have hFf : F false o.adv = (if o.adv then x else 1) *
            (if q + 1 = Δ then g a' true (decide (2 ≤ nh)) else v (q + 1) a' (decide (2 ≤ nh))) := rfl
        rw [hdec, hFf]
        by_cases hq1 : q + 1 < Δ
        · rw [if_neg (show ¬ (q + 1 = Δ) by omega)]
          by_cases hM : (h ++ [o]).length = M
          · rw [ExU_stop _ _ _ (Or.inl hM), hWo, d1]
            have := hvB.term (q + 1) hq1 a' (decide (2 ≤ nh))
            calc W0 * (θ * (if o.adv then x else 1)) * g a' true (decide (2 ≤ nh))
                ≤ W0 * (θ * (if o.adv then x else 1)) * v (q + 1) a' (decide (2 ≤ nh)) :=
                  mul_le_mul_of_nonneg_left this (by positivity)
              _ = _ := by ring
          · have := auto_le hFam hx hθ hv n (h ++ [o]) (q + 1) hb' hq1 hlen
            rw [hpowo, hAo, hHo] at this
            calc _ ≤ W0 * (θ * (if o.adv then x else 1)) * v (q + 1) a' (decide (2 ≤ nh)) := this
              _ = _ := by ring
        · rw [if_pos (show q + 1 = Δ by omega)]
          have hPE : PE Δ M (h ++ [o]) := by
            by_cases hM : (h ++ [o]).length = M
            · exact Or.inl hM
            · exact Or.inr ⟨by simp at hM ⊢; omega, hb'.quiet_of (by omega)⟩
          rw [ExU_stop _ _ _ hPE, hWo, d1]
          apply le_of_eq; ring
    calc ∑ o, κ.p h o * ExU (κ := κ) (PE Δ M) n (Wt2 x θ g m) (h ++ [o])
        ≤ ∑ o, κ.p h o * (W0 * θ * F (decide (o.hon ≠ 0)) o.adv) :=
          Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (hcont o) (κ.nonneg h o)
      _ = W0 * θ * ∑ o, κ.p h o * F (decide (o.hon ≠ 0)) o.adv := by
          rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun o _ => by ring
      _ ≤ W0 * θ * slot4 B F := mul_le_mul_of_nonneg_left (slot_sum4 hBh F) (by positivity)
      _ = W0 * (θ * slot4 B F) := by ring
      _ ≤ W0 * v q a (decide (2 ≤ nh)) := mul_le_mul_of_nonneg_left (hvB.step q hq a _) hW0n

/-- The bound for one phase from its start. -/
noncomputable def autoBound (B : Band) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ) (v : ℕ → Fin 3 → Bool → ℝ) : ℝ :=
  θ * slot4 B (fun hh aa => (if aa then x else 1) *
    (if hh then v 0 (acap (if aa then 1 else 0)) false else g (acap (if aa then 1 else 0)) false false))

/-- **One phase, with the automaton.** -/
theorem phase_auto {Bs : List Band} (hFam : κ.Fam Bs) {x θ : ℝ} (hx : 0 ≤ x) (hθ : 0 ≤ θ)
    {g : Fin 3 → Bool → Bool → ℝ} {v : ℕ → Fin 3 → Bool → ℝ} (hv : ∀ B ∈ Bs, AutoSol B Δ x θ g v) {e : ℝ}
    (he : ∀ B ∈ Bs, autoBound B x θ g v ≤ e) (hΔ : 0 < Δ) {l : List Out} (hl : Start Δ l)
    (hlM : l.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - l.length - 1) (Wt2 x θ g l.length) l ≤ e := by
  classical
  obtain ⟨B, hBm, hBl⟩ := hFam l
  refine le_trans ?_ (he B hBm)
  set m := l.length with hm
  set F : Bool → Bool → ℝ := fun hh aa => (if aa then x else 1) *
    (if hh then v 0 (acap (if aa then 1 else 0)) false else g (acap (if aa then 1 else 0)) false false) with hF
  have hA0 : advCnt (strOf l) m m = 0 := advCnt_self _
  have hH0 : honCnt (strOf l) m m = 0 := by unfold honCnt; simp
  have hcont : ∀ o, ExU (κ := κ) (PE Δ M) (M - m - 1) (Wt2 x θ g m) (l ++ [o]) ≤ θ * F (decide (o.hon ≠ 0)) o.adv := by
    intro o
    have hWo := Wt2_snoc (x := x) (θ := θ) (g := g) l o (le_of_eq hm.symm)
    rw [← hm, hA0, hH0, Nat.sub_self, pow_zero, pow_zero, one_mul, one_mul] at hWo
    have hacap : acap ((acap 0).val + if o.adv then 1 else 0) = acap (if o.adv then 1 else 0) := by
      unfold acap; ext; simp
    rw [hacap] at hWo
    have hlen : (l ++ [o]).length + (M - m - 1) = M := by simp; omega
    have hxa : 0 ≤ (if o.adv then x else 1) := by split_ifs <;> linarith
    by_cases ho : o.hon ≠ 0
    · have hdec : decide (o.hon ≠ 0) = true := by simpa using ho
      rw [hdec]; simp only [hF, ↓reduceIte]
      have hb : InBurst m (l ++ [o]) 0 := by
        refine ⟨by simp [hm], ?_, ?_⟩
        · simp only [List.length_append, List.length_singleton, Nat.sub_zero]
          rw [strOf_last]; simp only [Out.toPair]; intro h'; exact ho (Fin.ext h')
        · intro i h1 h2; simp at h1 h2; omega
      have hHo : honCnt (strOf (l ++ [o])) m (l ++ [o]).length = 1 := by
        simp only [List.length_append, List.length_singleton]
        rw [honCnt_snoc l o (le_of_eq hm.symm), ← hm, hH0]; simp [ho]
      have hAo : acap (advCnt (strOf (l ++ [o])) m (l ++ [o]).length) = acap (if o.adv then 1 else 0) := by
        simp only [List.length_append, List.length_singleton]
        rw [advCnt_snoc l o (le_of_eq hm.symm), ← hm, hA0, zero_add]
      have hpow : θ ^ ((l ++ [o]).length - m) * x ^ advCnt (strOf (l ++ [o])) m (l ++ [o]).length =
          θ * (if o.adv then x else 1) := by
        simp only [List.length_append, List.length_singleton]
        rw [advCnt_snoc l o (le_of_eq hm.symm), ← hm, hA0, zero_add, show m + 1 - m = 1 by omega, pow_one]
        split_ifs <;> simp
      by_cases hM : (l ++ [o]).length = M
      · rw [ExU_stop _ _ _ (Or.inl hM), hWo]
        simp only [ho, ne_eq, not_false_eq_true, ↓reduceIte, zero_add, le_refl, decide_true,
          Nat.one_lt_ofNat, Nat.not_ofNat_le_one, decide_false]
        have := (hv B hBm).term 0 hΔ (acap (if o.adv then 1 else 0)) false
        calc θ * (if o.adv then x else 1) * g (acap (if o.adv then 1 else 0)) true false
            ≤ θ * (if o.adv then x else 1) * v 0 (acap (if o.adv then 1 else 0)) false :=
              mul_le_mul_of_nonneg_left this (by positivity)
          _ = _ := by ring
      · have := auto_le hFam hx hθ hv _ (l ++ [o]) 0 hb hΔ hlen
        rw [hpow, hAo, hHo] at this
        simp only [Nat.not_ofNat_le_one, decide_false] at this
        calc _ ≤ θ * (if o.adv then x else 1) * v 0 (acap (if o.adv then 1 else 0)) false := this
          _ = _ := by ring
    · push Not at ho
      have hdec : decide (o.hon ≠ 0) = false := by simpa using ho
      rw [hdec]; simp only [hF, Bool.false_eq_true, ↓reduceIte]
      have hPE : PE Δ M (l ++ [o]) := by
        by_cases hM : (l ++ [o]).length = M
        · exact Or.inl hM
        · exact Or.inr ⟨by simp at hM ⊢; omega, by simpa using start_snoc_empty hl o ho⟩
      rw [ExU_stop _ _ _ hPE, hWo]
      simp [ho]
      ring_nf; exact le_refl _
  unfold ExPh autoBound
  calc ∑ o, κ.p l o * ExU (κ := κ) (PE Δ M) (M - m - 1) (Wt2 x θ g m) (l ++ [o])
      ≤ ∑ o, κ.p l o * (θ * F (decide (o.hon ≠ 0)) o.adv) :=
        Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (hcont o) (κ.nonneg l o)
    _ = θ * ∑ o, κ.p l o * F (decide (o.hon ≠ 0)) o.adv := by
        rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun o _ => by ring
    _ ≤ θ * slot4 B F := mul_le_mul_of_nonneg_left (slot_sum4 hBl F) hθ

end Cryptarchia.Prob
