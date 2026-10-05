import Cryptarchia.Settle.Reduce
import Cryptarchia.Prob.Kernel

/-!
# The greedy phase decomposition

The settlement recurrences run along a phase decomposition: slots `e 0 = 0 < e 1 <
…`, each quiet (no honest success in the `Δ` slots before it). We take **every
quiet slot** as a phase end, up to a horizon `M` (`gend`): the next phase ends at
the first quiet slot after the current end, or at `M` if there is none before it.
A phase is then a single slot with no honest success, or a burst that starts at an
honest slot and ends after `Δ` slots with none.

The phase structure, and the reach and margin bounds along it, depend on the
string only through the slots seen so far, and only through whether each slot has
no honest leader, exactly one, or more (`SimOn`). So they can be computed from a
prefix of the sampled outcomes.
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {Δ : ℕ}

/-! ## Strings that agree as the analysis sees them -/

/-- `w` and `w'` agree on slots `(a, b]` up to the number of honest leaders beyond
one. -/
def SimOn (w w' : CStr) (a b : ℕ) : Prop :=
  ∀ i, a < i → i ≤ b → ((w i).1 = 0 ↔ (w' i).1 = 0) ∧ ((w i).1 = 1 ↔ (w' i).1 = 1) ∧
    (w i).2 = (w' i).2

theorem SimOn.mono {w w' : CStr} {a b a' b' : ℕ} (h : SimOn w w' a b) (ha : a ≤ a') (hb : b' ≤ b) :
    SimOn w w' a' b' := fun i h1 h2 => h i (by omega) (by omega)

theorem SimOn.symm {w w' : CStr} {a b : ℕ} (h : SimOn w w' a b) : SimOn w' w a b := fun i h1 h2 =>
  ⟨(h i h1 h2).1.symm, (h i h1 h2).2.1.symm, (h i h1 h2).2.2.symm⟩

theorem SimOn.of_eq {w w' : CStr} {a b : ℕ} (h : ∀ i, a < i → i ≤ b → w i = w' i) : SimOn w w' a b :=
  fun i h1 h2 => by rw [h i h1 h2]; exact ⟨Iff.rfl, Iff.rfl, rfl⟩

theorem advCnt_congr {w w' : CStr} {a b : ℕ} (h : SimOn w w' a b) : advCnt w a b = advCnt w' a b := by
  unfold advCnt
  congr 1
  apply Finset.filter_congr
  intro j hj
  rw [Finset.mem_Ioc] at hj
  rw [(h j hj.1 hj.2).2.2]

theorem occCnt_congr {w w' : CStr} {a b : ℕ} (h : SimOn w w' a b) : occCnt w a b = occCnt w' a b := by
  unfold occCnt
  congr 1
  apply Finset.filter_congr
  intro j hj
  rw [Finset.mem_Ioc] at hj
  obtain ⟨h0, -, h2⟩ := h j hj.1 hj.2
  rw [h2]
  constructor
  · rintro (h | h)
    · left; by_contra hc; push Not at hc; exact absurd (h0.2 (by omega)) (by omega)
    · exact Or.inr h
  · rintro (h | h)
    · left; by_contra hc; push Not at hc; exact absurd (h0.1 (by omega)) (by omega)
    · exact Or.inr h

theorem hD_congr {w w' : CStr} {a b : ℕ} (h : SimOn w w' a b) : hD Δ w a b = hD Δ w' a b := by
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    unfold hD
    by_cases hb : b ≤ a
    · simp only [hb, ↓reduceDIte]
    · simp only [hb, ↓reduceDIte]
      have hz := (h b (by omega) le_rfl).1
      by_cases hw : (w b).1 = 0
      · have hw' : (w' b).1 = 0 := hz.1 hw
        simp only [hw, hw', ↓reduceIte]
        exact ih (b - 1) (by omega) (h.mono le_rfl (by omega))
      · have hw' : ¬ (w' b).1 = 0 := fun h' => hw (hz.2 h')
        simp only [hw, hw', ↓reduceIte]
        rw [ih (b - Δ - 1) (by omega) (h.mono le_rfl (by omega))]

theorem quiet_congr {w w' : CStr} {m : ℕ} (h : SimOn w w' (m - Δ) m) : Quiet Δ w m ↔ Quiet Δ w' m := by
  unfold Quiet
  constructor
  · intro hq j h1 h2 h3; exact (h j h1 h2).1.1 (hq j h1 h2 h3)
  · intro hq j h1 h2 h3; exact (h j h1 h2).1.2 (hq j h1 h2 h3)

theorem cross_congr {w w' : CStr} {ℓ a b : ℕ} (h : SimOn w w' a b) : Cross w ℓ a b ↔ Cross w' ℓ a b := by
  unfold Cross
  rw [advCnt_congr h]
  constructor
  · rintro ⟨hA, s, h1, h2, h3, h4, h5⟩
    exact ⟨hA, s, h1, h2, h3, (h s h1 h2).2.1.1 h4, fun i hi1 hi2 hi3 => (h i hi1 hi2).1.1 (h5 i hi1 hi2 hi3)⟩
  · rintro ⟨hA, s, h1, h2, h3, h4, h5⟩
    exact ⟨hA, s, h1, h2, h3, (h s h1 h2).2.1.2 h4, fun i hi1 hi2 hi3 => (h i hi1 hi2).1.2 (h5 i hi1 hi2 hi3)⟩

theorem step_congr {w w' : CStr} {ℓ a b : ℕ} (h : SimOn w w' a b) (s : ℤ × ℤ) :
    step Δ w ℓ a b s = step Δ w' ℓ a b s := by
  classical
  unfold step
  rw [advCnt_congr h, hD_congr h]
  simp only [show Cross w ℓ a b = Cross w' ℓ a b from propext (cross_congr h)]

/-- The bounds depend on the string only through the phases up to `k`. -/
theorem bnd_congr {w w' : CStr} {ℓ : ℕ} {e : ℕ → ℕ} (hmono : ∀ k, e k ≤ e (k + 1)) :
    ∀ k, SimOn w w' 0 (e k) → bnd Δ w ℓ e k = bnd Δ w' ℓ e k
  | 0, _ => rfl
  | k + 1, h => by
    simp only [bnd]
    rw [bnd_congr hmono k (h.mono le_rfl (hmono k)), step_congr (h.mono (Nat.zero_le _) le_rfl)]

theorem runFrom_congr {w w' : CStr} {ℓ : ℕ} {e : ℕ → ℕ} (hmono : ∀ k, e k ≤ e (k + 1)) (k0 : ℕ)
    (b0 : ℤ × ℤ) : ∀ j, SimOn w w' 0 (e (k0 + j)) →
      runFrom (Δ := Δ) (w := w) ℓ e k0 b0 j = runFrom (Δ := Δ) (w := w') ℓ e k0 b0 j
  | 0, _ => rfl
  | j + 1, h => by
    simp only [runFrom]
    rw [runFrom_congr hmono k0 b0 j (h.mono le_rfl (by rw [← Nat.add_assoc]; exact hmono _)),
      step_congr (h.mono (Nat.zero_le _) (by rw [Nat.add_assoc]))]

/-! ## Phase ends -/

open Classical in
/-- The next phase end after `m`: the first quiet slot in `(m, M)`, or `M` if there
is none (and `m + 1` once past the horizon). -/
noncomputable def nextE (Δ M : ℕ) (w : CStr) (m : ℕ) : ℕ :=
  if h : ∃ j, m < j ∧ j < M ∧ Quiet Δ w j then Nat.find h else max M (m + 1)

/-- **The greedy phase ends** up to the horizon `M`. -/
noncomputable def gend (Δ M : ℕ) (w : CStr) : ℕ → ℕ
  | 0 => 0
  | k + 1 => nextE Δ M w (gend Δ M w k)

variable {M : ℕ} {w : CStr}

theorem nextE_gt (m : ℕ) : m < nextE Δ M w m := by
  classical
  unfold nextE
  split_ifs with h
  · exact (Nat.find_spec h).1
  · omega

theorem nextE_quiet {m : ℕ} (h : nextE Δ M w m < M) : Quiet Δ w (nextE Δ M w m) := by
  classical
  unfold nextE at h ⊢
  split_ifs at h ⊢ with hx
  · exact (Nat.find_spec hx).2.2
  · omega

/-- No quiet slot is skipped. -/
theorem nextE_min {m j : ℕ} (h1 : m < j) (h2 : j < nextE Δ M w m) (hjM : j < M) : ¬ Quiet Δ w j := by
  classical
  intro hq
  unfold nextE at h2
  split_ifs at h2 with hx
  · exact Nat.find_min hx h2 ⟨h1, hjM, hq⟩
  · exact hx ⟨j, h1, hjM, hq⟩

theorem nextE_le {m : ℕ} (hm : m < M) : nextE Δ M w m ≤ M := by
  classical
  unfold nextE
  split_ifs with h
  · exact (Nat.find_spec h).2.1.le
  · omega

theorem nextE_of_ge {m : ℕ} (hm : M ≤ m) : nextE Δ M w m = m + 1 := by
  classical
  unfold nextE
  rw [dif_neg (by rintro ⟨j, h1, h2, -⟩; omega)]
  omega

/-- If a quiet slot lies in `(m, j]` with `j < M`, the next end is at most `j`. -/
theorem nextE_le_of_quiet {m j : ℕ} (h1 : m < j) (hjM : j < M) (hq : Quiet Δ w j) :
    nextE Δ M w m ≤ j := by
  by_contra h
  exact nextE_min h1 (by omega) hjM hq

theorem gend_zero : gend Δ M w 0 = 0 := rfl

theorem gend_succ (k : ℕ) : gend Δ M w (k + 1) = nextE Δ M w (gend Δ M w k) := rfl

theorem gend_lt_succ (k : ℕ) : gend Δ M w k < gend Δ M w (k + 1) := nextE_gt _

theorem gend_mono : ∀ k, gend Δ M w k ≤ gend Δ M w (k + 1) := fun k => (gend_lt_succ k).le

theorem gend_strictMono : StrictMono (gend Δ M w) := strictMono_nat_of_lt_succ gend_lt_succ

theorem le_gend (k : ℕ) : k ≤ gend Δ M w k := gend_strictMono.le_apply

theorem gend_quiet : ∀ k, gend Δ M w k < M → Quiet Δ w (gend Δ M w k)
  | 0, _ => by intro j h1 h2 h3; simp [gend_zero] at h2; omega
  | k + 1, h => nextE_quiet h

theorem gend_unb (t : ℕ) : ∃ k, t ≤ gend Δ M w k := ⟨t, le_gend t⟩

open Classical in
/-- The index of the first phase end at or after `m`. -/
noncomputable def pidx (Δ M : ℕ) (w : CStr) (m : ℕ) : ℕ := Nat.find (gend_unb (Δ := Δ) (M := M) (w := w) m)

theorem le_gend_pidx (m : ℕ) : m ≤ gend Δ M w (pidx Δ M w m) := by
  classical
  exact Nat.find_spec (gend_unb (Δ := Δ) (M := M) (w := w) m)

theorem gend_lt_of_lt_pidx {m k : ℕ} (hk : k < pidx Δ M w m) : gend Δ M w k < m := by
  classical
  have := Nat.find_min (gend_unb (Δ := Δ) (M := M) (w := w) m) hk
  omega

theorem pidx_le_of {m k : ℕ} (h : m ≤ gend Δ M w k) : pidx Δ M w m ≤ k := by
  classical
  exact Nat.find_min' _ h

/-- A quiet slot before the horizon, or the horizon itself, is a phase end. -/
theorem gend_pidx_of_end {m : ℕ} (hm : m = 0 ∨ m = M ∨ (m < M ∧ Quiet Δ w m)) :
    gend Δ M w (pidx Δ M w m) = m := by
  classical
  have hle := le_gend_pidx (Δ := Δ) (M := M) (w := w) m
  rcases Nat.eq_zero_or_pos (pidx Δ M w m) with h0 | hpos
  · rw [h0, gend_zero] at hle ⊢; omega
  · obtain ⟨k, hk⟩ : ∃ k, pidx Δ M w m = k + 1 := ⟨_, (Nat.succ_pred_eq_of_pos hpos).symm⟩
    have hlt := gend_lt_of_lt_pidx (Δ := Δ) (M := M) (w := w) (m := m) (k := k) (by omega)
    rw [hk, gend_succ] at hle ⊢
    by_contra hne
    have hgt : m < nextE Δ M w (gend Δ M w k) := by omega
    rcases hm with h0 | hM | ⟨hmM, hq⟩
    · omega
    · have := nextE_le (Δ := Δ) (w := w) (by omega : gend Δ M w k < M); omega
    · exact nextE_min hlt hgt hmM hq

/-- The phase ends below `m`, and the phase structure up to the first end at or
after `m`, depend only on the slots `≤ m`. -/
theorem gend_congr {w w' : CStr} {m : ℕ} (h : SimOn w w' 0 m) :
    ∀ k, gend Δ M w k ≤ m → gend Δ M w k = gend Δ M w' k
  | 0, _ => rfl
  | k + 1, hk => by
    have hk' : gend Δ M w k ≤ m := le_trans (gend_mono k) hk
    have ih := gend_congr h k hk'
    rw [gend_succ] at hk
    rw [gend_succ, gend_succ, ← ih]
    -- the quiet tests up to `m` agree
    have hq : ∀ j, j ≤ m → (Quiet Δ w j ↔ Quiet Δ w' j) := fun j hj =>
      quiet_congr (h.mono (Nat.zero_le _) hj)
    classical
    unfold nextE at hk ⊢
    by_cases hx : ∃ j, gend Δ M w k < j ∧ j < M ∧ Quiet Δ w j
    · rw [dif_pos hx] at hk
      have hfm := Nat.find_spec hx
      have hx' : ∃ j, gend Δ M w k < j ∧ j < M ∧ Quiet Δ w' j :=
        ⟨_, hfm.1, hfm.2.1, (hq _ hk).1 hfm.2.2⟩
      rw [dif_pos hx, dif_pos hx']
      apply le_antisymm
      · apply Nat.find_min'
        obtain ⟨h1, h2, h3⟩ := Nat.find_spec hx'
        refine ⟨h1, h2, ?_⟩
        by_cases hjm : Nat.find hx' ≤ m
        · exact (hq _ hjm).2 h3
        · exfalso
          have : Nat.find hx' ≤ Nat.find hx :=
            Nat.find_min' hx' ⟨hfm.1, hfm.2.1, (hq _ hk).1 hfm.2.2⟩
          omega
      · apply Nat.find_min'
        exact ⟨hfm.1, hfm.2.1, (hq _ hk).1 hfm.2.2⟩
    · rw [dif_neg hx] at hk ⊢
      have hx' : ¬ ∃ j, gend Δ M w k < j ∧ j < M ∧ Quiet Δ w' j := by
        rintro ⟨j, h1, h2, h3⟩
        by_cases hjm : j ≤ m
        · exact hx ⟨j, h1, h2, (hq j hjm).2 h3⟩
        · -- then `max M (gend + 1) ≤ m < j < M`: impossible
          omega
      rw [dif_neg hx']

end Cryptarchia.Prob
