import Cryptarchia.Prob.Fail2E

/-!
# Failed checks with an in-epoch contraction

`Fail2E.lean` contracts the potential by one `lp` per phase, the worst over phases
that may cross an epoch boundary. A phase that starts more than `G` slots before the
next boundary stays in one member, so a smaller in-epoch contraction `lpi` applies
(`phase_autoIn` for the phase bounds, `ex_cross_truncIn` for the crossing pattern).
Phases that start within `G` slots of a boundary (`Sw`) pay the ratio `lp / lpi`.
Within a check's window of `L` slots there are at most `Ccap` such slots, so the
potential carries a weight `(lp / lpi)^c`, with `c` the switching slots left in the
window (`swCnt`); a failed check counts only if the check is within `L` slots of its
anchor (the span term pays for the rest).
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {B : Band} {Δ M : ℕ} {κ : Kern}

/-! ## The crossing pattern inside an epoch -/

theorem phase_lowerL {el : ℝ} (hel0 : 0 ≤ el) (hΔ : 0 < Δ) {l : List Out} (hlM : l.length + Δ + 1 ≤ M)
    {G : List Out → ℝ} (hG : ∀ h, 0 ≤ G h) (o1 : Out) (ho1 : o1.hon ≠ 0)
    (hel : ∀ i < Δ, el ≤ κ.p (l ++ pat o1 i) Out.empty) :
    κ.p l o1 * el ^ Δ * G (l ++ pat o1 Δ) ≤ ExPh (κ := κ) (PE Δ M) (M - l.length - 1) G l := by
  have hlen : ∀ i, (l ++ pat o1 i).length = l.length + 1 + i := fun i => by simp [pat]; omega
  -- not a phase end before the pattern finishes
  have hnot : ∀ i < Δ, ¬ PE Δ M (l ++ pat o1 i) := by
    intro i hi
    rintro (h1 | ⟨-, h2⟩)
    · rw [hlen] at h1; omega
    · have := h2 (l.length + 1) (by rw [hlen]; omega) (by rw [hlen]; omega) (by omega)
      rw [strOf_pat_first] at this
      exact ho1 (Fin.ext (by simpa [Out.toPair] using this))
  have hend : PE Δ M (l ++ pat o1 Δ) := by
    by_cases hM : (l ++ pat o1 Δ).length = M
    · exact Or.inl hM
    · refine Or.inr ⟨by rw [hlen] at hM ⊢; omega, ?_⟩
      intro j h1 h2 _
      rw [hlen] at h1 h2
      exact (strOf_pat_after l o1 Δ j (by omega)).1
  -- backward induction along the pattern
  have key : ∀ j ≤ Δ, el ^ j * G (l ++ pat o1 Δ) ≤
      ExU (κ := κ) (PE Δ M) (M - l.length - 1 - (Δ - j)) G (l ++ pat o1 (Δ - j)) := by
    intro j hj
    induction j with
    | zero => simp only [pow_zero, one_mul, Nat.sub_zero]; rw [ExU_stop _ _ _ hend]
    | succ j ih =>
      have ih' := ih (by omega)
      have hfuel : M - l.length - 1 - (Δ - (j + 1)) = (M - l.length - 1 - (Δ - j)) + 1 := by omega
      rw [hfuel]
      have hs := ExU_ge_snoc (κ := κ) hG (hnot (Δ - (j + 1)) (by omega))
        (M - l.length - 1 - (Δ - j)) Out.empty
      rw [List.append_assoc, pat_snoc, show Δ - (j + 1) + 1 = Δ - j by omega] at hs
      have he := hel (Δ - (j + 1)) (by omega)
      have hU := ExU_nonneg (κ := κ) (PE Δ M) (M - l.length - 1 - (Δ - j)) hG (l ++ pat o1 (Δ - j))
      have he0 : 0 ≤ el ^ j * G (l ++ pat o1 Δ) := mul_nonneg (pow_nonneg hel0 _) (hG _)
      calc el ^ (j + 1) * G (l ++ pat o1 Δ) = el * (el ^ j * G (l ++ pat o1 Δ)) := by ring
        _ ≤ κ.p (l ++ pat o1 (Δ - (j + 1))) Out.empty *
            ExU (κ := κ) (PE Δ M) (M - l.length - 1 - (Δ - j)) G (l ++ pat o1 (Δ - j)) := by
            apply mul_le_mul he ih' he0 (κ.nonneg _ _)
        _ ≤ _ := hs
  have h0 := key Δ le_rfl
  simp only [Nat.sub_self, Nat.sub_zero] at h0
  unfold ExPh
  have hsingle : κ.p l o1 * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o1]) ≤
      ∑ o, κ.p l o * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o]) :=
    Finset.single_le_sum (f := fun o => κ.p l o * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o]))
      (fun o _ => mul_nonneg (κ.nonneg l o) (ExU_nonneg _ _ hG _)) (Finset.mem_univ o1)
  have hp0 : pat o1 0 = [o1] := rfl
  rw [hp0] at h0
  calc κ.p l o1 * el ^ Δ * G (l ++ pat o1 Δ) = κ.p l o1 * (el ^ Δ * G (l ++ pat o1 Δ)) := by ring
    _ ≤ κ.p l o1 * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o1]) :=
        mul_le_mul_of_nonneg_left h0 (κ.nonneg l o1)
    _ ≤ _ := hsingle


theorem ex_cross_truncL {sl el : ℝ} (hel0 : 0 ≤ el) (hΔ : 0 < Δ) {h : List Out}
    (hlM : h.length + Δ + 1 ≤ M) {G : ℕ} (hG : Δ + 1 ≤ G) (hs : sl ≤ κ.p h ⟨1, false⟩)
    (hel : ∀ i < Δ, el ≤ κ.p (h ++ pat ⟨1, false⟩ i) Out.empty) :
    sl * el ^ Δ ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG 1 h.length)) h := by
  classical
  have hG0 : ∀ x, 0 ≤ truncG h.length G (crossG 1 h.length) x :=
    truncG_nonneg (fun x => by unfold crossG; split_ifs <;> positivity)
  have hl := phase_lowerL (κ := κ) hel0 hΔ hlM hG0 ⟨1, false⟩ (by decide) hel
  have hval : truncG h.length G (crossG 1 h.length) (h ++ pat ⟨1, false⟩ Δ) = 1 := by
    have hlen : (h ++ pat ⟨1, false⟩ Δ).length = h.length + 1 + Δ := by simp [pat]; omega
    unfold truncG crossG
    rw [hlen, if_pos (by omega), if_pos (pat_cross h ⟨1, false⟩ rfl rfl)]
    simp
  rw [hval, mul_one] at hl
  have : sl * el ^ Δ ≤ κ.p h ⟨1, false⟩ * el ^ Δ := mul_le_mul_of_nonneg_right hs (by positivity)
  linarith

/-- No epoch boundary within `G` slots after `t`. -/
def NoSw (EL G t : ℕ) : Prop := ∀ j, t < j → j ≤ t + G → (j + 1) % EL ≠ 0

theorem mem_pat {EL K : ℕ} {mem : List Out → Fin K} (hmem : ∀ h o, (h.length + 2) % EL ≠ 0 → mem (h ++ [o]) = mem h)
    {G : ℕ} {l : List Out} (hnb : NoSw EL G l.length) (o1 : Out) : ∀ i, i + 1 ≤ G → mem (l ++ pat o1 i) = mem l
  | 0, _ => by
    show mem (l ++ [o1]) = mem l
    exact hmem l o1 (hnb (l.length + 1) (by omega) (by omega))
  | i + 1, hi => by
    rw [← pat_snoc, ← List.append_assoc]
    have hlen : (l ++ pat o1 i).length = l.length + 1 + i := by simp [pat]; omega
    rw [hmem _ _ (by rw [hlen, show l.length + 1 + i + 2 = (l.length + 2 + i) + 1 by omega]; exact hnb (l.length + 2 + i) (by omega) (by omega)),
      mem_pat hmem hnb o1 i (by omega)]

/-- **The crossing pattern inside an epoch**: at least the member's own pattern. -/
theorem ex_cross_truncIn {EL K : ℕ} {fam : Fin K → Band} (mem : List Out → Fin K)
    (hband : ∀ h, κ.BandAt (fam (mem h)) h) (hmem : ∀ h o, (h.length + 2) % EL ≠ 0 → mem (h ++ [o]) = mem h)
    {pat0 : ℝ} {h : List Out} (hpat : pat0 ≤ (fam (mem h)).slo * (fam (mem h)).elo ^ Δ) (helo : ∀ k, 0 ≤ (fam k).elo)
    (hΔ : 0 < Δ) (hlM : h.length + Δ + 1 ≤ M) {G : ℕ} (hG : Δ + 1 ≤ G)
    (hnb : NoSw EL G h.length) :
    pat0 ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG 1 h.length)) h := by
  refine le_trans hpat (ex_cross_truncL (helo (mem h)) hΔ hlM hG (hband h).slo fun i hi => ?_)
  have := (hband (h ++ pat ⟨1, false⟩ i)).elo
  rwa [mem_pat hmem hnb ⟨1, false⟩ i (by omega)] at this

/-! ## The potential with an in-epoch contraction -/

open Classical in
/-- The slots in `[t, T)` satisfying `Sw` (within `G` slots before an epoch boundary). -/
noncomputable def swCnt (Sw : ℕ → Prop) (t T : ℕ) : ℕ := ((Finset.Ico t T).filter Sw).card

theorem swCnt_anti (Sw : ℕ → Prop) {t t' T : ℕ} (h : t ≤ t') : swCnt Sw t' T ≤ swCnt Sw t T := by
  classical
  unfold swCnt
  exact Finset.card_le_card (Finset.filter_subset_filter _ (Finset.Ico_subset_Ico_left h))

theorem swCnt_succ_pos (Sw : ℕ → Prop) {t T : ℕ} (hs : Sw t) (ht : t < T) :
    swCnt Sw t T = swCnt Sw (t + 1) T + 1 := by
  classical
  unfold swCnt
  rw [← Finset.insert_Ico_add_one_left_eq_Ico ht, Finset.filter_insert, if_pos hs,
    Finset.card_insert_of_notMem (by simp)]

variable (Δ M) in
open Classical in
/-- A failed check at phase `k`, anchored at `k0`, counted only without long phases and
within `L` slots of the anchor. -/
noncomputable def failHE3 (G L Hc k0 k : ℕ) (h : List Out) : ℝ :=
  if NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L then failH Δ M Hc k0 k h
  else 0

variable (Δ M) in
open Classical in
/-- **The potential.** Before the anchor as `ΦfE`, with `lpi` per phase and the full
weight `(lp/lpi)^Ccap`; from the anchor on, `lpi` per remaining phase and the weight of
the switching slots left in the check's window. -/
noncomputable def ΦfE3 (P : Cert2 B Δ) (lpi : ℝ) (Sw : ℕ → Prop) (Ccap G L Hc k0 k : ℕ) (h : List Out) : ℝ :=
  if pidx Δ M (strOf h) h.length < k0 then
    lpi ^ (k - k0) * (P.lp / lpi) ^ Ccap * P.e 2 * (P.lr ^ (k0 - pidx Δ M (strOf h) h.length) *
      P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) (pidx Δ M (strOf h) h.length)).1 +
      (P.b - P.lr) * ∑ i ∈ Finset.range (k0 - pidx Δ M (strOf h) h.length), P.lr ^ i)
  else if pidx Δ M (strOf h) h.length ≤ k then
    (if h.length ≤ Hc ∧ NoLong Δ M G k0 (pidx Δ M (strOf h) h.length) (strOf h) ∧
        h.length ≤ gend Δ M (strOf h) k0 + L then
      lpi ^ (k - pidx Δ M (strOf h) h.length) * (P.lp / lpi) ^ swCnt Sw h.length (gend Δ M (strOf h) k0 + L) *
      P.e 2 * V2 P.c P.z P.s P.κ P.d (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0)) else 0)
  else failHE3 Δ M G L Hc k0 k h

/-- **The potential is a supermartingale over phases.** -/
theorem phiFE3_step (P : Cert2 B Δ) (hW : κ.Within B) {G : ℕ} (hG : Δ + 1 ≤ G)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (hC2 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 2 h.length) h ≤ P.e 2)
    (hE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ h, PE Δ M h → h.length < M →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ P.e i)
    {lpi : ℝ} (hlpi0 : 0 < lpi) (hlpi : lpi ≤ P.lp)
    (Sw : ℕ → Prop) {Ccap L : ℕ} (hcap : ∀ t, swCnt Sw t (t + L) ≤ Ccap)
    (hIn : ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M → ¬ Sw h.length → ∃ (e : Fin 19 → ℝ) (pat : ℝ),
      ClassOK P lpi e pat ∧
      pat ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG 1 h.length)) h ∧
      ∀ i : Fin 19, i ≠ 2 → i ≠ 17 →
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ e i)
    {Hc : ℕ} (hHc : Hc + Δ + 1 ≤ M) {k0 k : ℕ}
    (hk0 : k0 ≤ k) {h : List Out} (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k) h ≤ ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k h := by
  classical
  have hM : 0 < M := by omega
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have he2 : 0 ≤ P.e 2 := le_trans (ExPh_nonneg _ _ (fun y => WP_nonneg P 2 0 y (by decide)) _)
    (hC2 [] (pe_nil hM) (by simpa using hM))
  have hlp := P.hlp0
  have hRg1 : 1 ≤ P.lp / lpi := by rw [le_div_iff₀ hlpi0]; linarith
  have hRg0 : 0 ≤ P.lp / lpi := by linarith
  obtain ⟨j, hj⟩ : ∃ j, pidx Δ M (strOf h) h.length = j := ⟨_, rfl⟩
  have reach : ∀ (o : Out) (t : List Out), t.length ≤ M - h.length - 1 →
      (∀ k' < t.length, ¬ PE Δ M (h ++ [o] ++ t.take k')) →
      (PE Δ M (h ++ [o] ++ t) ∨ t.length = M - h.length - 1) → FirstPE Δ M h (h ++ [o] ++ t) :=
    fun o t ht hk hend => firstPE_of_reached hlM o t ht hk hend
  have hF : 0 ≤ lpi ^ (k - k0) * (P.lp / lpi) ^ Ccap * P.e 2 := by positivity
  by_cases hjk : j < k0
  · -- before the anchor
    obtain ⟨ρ, hρ⟩ : ∃ ρ, (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j).1 = ρ := ⟨_, rfl⟩
    have hρ0 : 0 ≤ ρ := by rw [← hρ]; exact bnd_fst_nonneg j
    obtain ⟨n, hn⟩ : ∃ n, k0 - j = n := ⟨_, rfl⟩
    have hn1 : 1 ≤ n := by omega
    have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => lpi ^ (k - k0) * (P.lp / lpi) ^ Ccap * P.e 2 * (P.lr ^ (n - 1) *
          (if 1 ≤ ρ then P.c ^ ρ * WP P 0 h.length h' else WP P 1 h.length h') +
            (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i)) h := by
      apply ExPh_mono_on
      intro o t ht hk hend
      have hf := reach o t ht hk hend
      generalize hh' : h ++ [o] ++ t = h' at hf ⊢
      have hp' := next_pidx hpe hlM hf
      have hbs := next_bnd_succ hpe hlM hf
      rw [hj] at hp' hbs
      obtain ⟨ρ', hρ'⟩ : ∃ ρ', (bnd Δ (strOf h') 0 (gend Δ M (strOf h')) (j + 1)).1 = ρ' := ⟨_, rfl⟩
      have hρ'0 : 0 ≤ ρ' := by rw [← hρ']; exact bnd_fst_nonneg _
      have hcr : P.c ^ ρ' ≤ (if 1 ≤ ρ then P.c ^ ρ * WP P 0 h.length h' else WP P 1 h.length h') := by
        have := c_pow_reach (Δ := Δ) (w := strOf h') (ℓ := 0) (a := h.length) (b := h'.length) P.hc
          (st := bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j) (by rw [hρ]; exact hρ0) (bnd_le 0 _ j)
        rw [← hρ', hbs]
        rw [hρ] at this
        obtain ⟨A, hA⟩ : ∃ A, advCnt (strOf h') h.length h'.length = A := ⟨_, rfl⟩
        obtain ⟨nh, hnh⟩ : ∃ nh, honCnt (strOf h') h.length h'.length = nh := ⟨_, rfl⟩
        have hiff : HonIn (strOf h') h.length h'.length ↔ 1 ≤ nh := by rw [← hnh]; exact honIn_iff_honCnt
        rw [hA] at this
        by_cases h1 : 1 ≤ ρ
        · rw [if_pos h1] at this
          rw [if_pos h1, WP_val' P 0 (by decide) h.length h' hA hnh, xg_0]
          refine this.trans (le_of_eq ?_)
          simp only [xgN, gtab]
          by_cases hb : HonIn (strOf h') h.length h'.length
          · rw [if_pos hb, zpow_sub₀ hc0.ne', zpow_natCast, zpow_one, div_eq_mul_inv]
            simp [hiff.1 hb]
          · rw [if_neg hb]; simp [show ¬ 1 ≤ nh from fun h'' => hb (hiff.2 h'')]
        · rw [if_neg h1] at this
          rw [if_neg h1, WP_val' P 1 (by decide) h.length h' hA hnh, xg_1]
          refine this.trans (le_of_eq ?_)
          simp [xgN]
      have hval : ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k h' ≤ lpi ^ (k - k0) * (P.lp / lpi) ^ Ccap * P.e 2 *
          (P.lr ^ (n - 1) * P.c ^ ρ' + (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i) := by
        unfold ΦfE3
        rw [hp']
        by_cases hjk' : j + 1 < k0
        · rw [if_pos hjk', show k0 - (j + 1) = n - 1 by omega, hρ']
        · rw [if_neg hjk', if_pos (by omega), show n - 1 = 0 by omega]
          simp only [pow_zero, one_mul, Finset.range_zero, Finset.sum_empty, mul_zero, add_zero]
          have hk0' : k0 = j + 1 := by omega
          have hcnt : swCnt Sw h'.length (gend Δ M (strOf h') k0 + L) ≤ Ccap := by
            have hg : gend Δ M (strOf h') k0 = h'.length := by rw [hk0', ← hp']; exact gend_pidx_pe hf.pe
            rw [hg]; exact hcap _
          split_ifs
          · refine le_trans (mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right
              (mul_le_mul_of_nonneg_left (pow_le_pow_right₀ hRg1 hcnt) (pow_nonneg hlpi0.le _)) he2)
              (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 _).le) ?_
            rw [show k - (j + 1) = k - k0 by omega, show j + 1 - k0 = 0 by omega]
            apply mul_le_mul_of_nonneg_left _ hF
            unfold rf rho0
            simp only [runFrom]
            rw [hk0', hρ', V2_warm (show (0 : ℤ) ≤ (ρ', ρ').2 from hρ'0)]
          · exact mul_nonneg hF (zpow_nonneg hc0.le _)
      refine hval.trans ?_
      apply mul_le_mul_of_nonneg_left _ hF
      have := mul_le_mul_of_nonneg_left hcr (pow_nonneg P.hlr0 (n - 1))
      linarith
    refine hle.trans ?_
    have hS : ∑ i ∈ Finset.range n, P.lr ^ i = ∑ i ∈ Finset.range (n - 1), P.lr ^ i + P.lr ^ (n - 1) := by
      rw [show n = (n - 1) + 1 by omega, Finset.sum_range_succ, Nat.add_sub_cancel]
    have hval : ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k h = lpi ^ (k - k0) * (P.lp / lpi) ^ Ccap * P.e 2 *
        (P.lr ^ n * P.c ^ ρ + (P.b - P.lr) * ∑ i ∈ Finset.range n, P.lr ^ i) := by
      unfold ΦfE3; rw [hj, if_pos hjk, hn, hρ]
    rw [hval, ExPh_mul_const]
    apply mul_le_mul_of_nonneg_left _ hF
    rw [ExPh_add, ExPh_const, ExPh_mul_const]
    have hcρ : 0 ≤ P.c ^ ρ := zpow_nonneg hc0.le _
    have hlrn : 0 ≤ P.lr ^ (n - 1) := pow_nonneg P.hlr0 _
    have hpow : P.lr ^ n = P.lr ^ (n - 1) * P.lr := by
      rw [← pow_succ, show n - 1 + 1 = n by omega]
    have hbl : 0 ≤ P.b - P.lr := by linarith [P.hb1, P.hlr1]
    split_ifs with h1
    · rw [ExPh_mul_const]
      have h2 := hR0 h hpe hlM
      have := mul_le_mul_of_nonneg_left h2 hcρ
      have := mul_le_mul_of_nonneg_left this hlrn
      rw [hS, hpow]
      nlinarith [mul_nonneg hbl hlrn]
    · have h2 := hR1 h hpe hlM
      have := mul_le_mul_of_nonneg_left h2 hlrn
      have hc1 : P.c ^ ρ = 1 := by rw [show ρ = 0 by omega, zpow_zero]
      rw [hS, hpow, hc1]
      nlinarith
  · push Not at hjk
    have hgj : gend Δ M (strOf h) j = h.length := by rw [← hj]; exact gend_pidx_pe hpe
    obtain ⟨T0, hT0⟩ : ∃ T0, gend Δ M (strOf h) k0 + L = T0 := ⟨_, rfl⟩
    by_cases hjk2 : j ≤ k
    · by_cases hHl : h.length ≤ Hc ∧ NoLong Δ M G k0 j (strOf h) ∧ h.length ≤ T0
      · obtain ⟨st, hst⟩ : ∃ st, rf Δ M (strOf h) k0 (j - k0) = st := ⟨_, rfl⟩
        have hinv : Inv st := by rw [← hst]; exact rf_inv _ k0 _
        have hval : ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k h =
            lpi ^ (k - j) * (P.lp / lpi) ^ swCnt Sw h.length T0 * P.e 2 * V2 P.c P.z P.s P.κ P.d st := by
          unfold ΦfE3; rw [hj, if_neg (by omega), if_pos hjk2, hT0, if_pos hHl, hst]
        have hVs : 0 ≤ V2 P.c P.z P.s P.κ P.d st :=
          (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 st).le
        by_cases hjeq : j = k
        · -- the check
          subst hjeq
          have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 j) h ≤
              ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => V2 P.c P.z P.s P.κ P.d st * WP P 2 h.length h') h := by
            apply ExPh_mono_on
            intro o t ht hk hend
            have hf := reach o t ht hk hend
            generalize hh' : h ++ [o] ++ t = h' at hf ⊢
            have hp' := next_pidx hpe hlM hf
            rw [hj] at hp'
            have hfn := next_failC_new (Hc := Hc) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
            rw [hj, hst] at hfn
            have hnl' : NoLong Δ M G k0 j (strOf h') :=
              (noLong_stable hpe hlM hf (by rw [hj])).2 hHl.2.1
            have hns' : gend Δ M (strOf h') j ≤ gend Δ M (strOf h') k0 + L := by
              rw [next_gend hpe hlM hf (show j ≤ _ by rw [hj]), next_gend hpe hlM hf (show k0 ≤ _ by rw [hj]; exact hjk),
                hgj, hT0]
              exact hHl.2.2
            unfold ΦfE3 failHE3 failH
            rw [hp', if_neg (by omega), if_neg (by omega), if_pos ⟨hnl', hns'⟩, if_pos (by omega), hfn]
            obtain ⟨A, hA⟩ : ∃ A, advCnt (strOf h') h.length h'.length = A := ⟨_, rfl⟩
            obtain ⟨nh, hnh⟩ : ∃ nh, honCnt (strOf h') h.length h'.length = nh := ⟨_, rfl⟩
            rw [hA, hnh, WP_val' P 2 (by decide) h.length h' hA hnh, xg_2]
            simp only [xgN]
            have hg : 0 ≤ gtab (fun b _ => if b then (1 : ℝ) else 0) (fun _ _ => 1) (fun _ _ => 1) (acap A)
                (decide (1 ≤ nh)) (decide (2 ≤ nh)) := by
              unfold gtab; split_ifs <;> simp only [decide_eq_true_eq] <;> (try split_ifs) <;> norm_num
            by_cases hcond : h.length ≤ Hc ∧ -(A : ℤ) ≤ st.2 ∧ (1 ≤ A ∨ 1 ≤ nh)
            · rw [if_pos hcond]
              have hg1 : gtab (fun b _ => if b then (1 : ℝ) else 0) (fun _ _ => 1) (fun _ _ => 1) (acap A)
                  (decide (1 ≤ nh)) (decide (2 ≤ nh)) = 1 := by
                unfold gtab
                rcases hcond.2.2 with h1 | h1
                · have := acap_pos h1; simp only [this, ↓reduceIte]; split_ifs <;> rfl
                · by_cases ha0 : (acap A).val = 0
                  · simp [ha0, h1]
                  · simp only [ha0, ↓reduceIte]; split_ifs <;> rfl
              rw [hg1, mul_one]
              have hfl := fail_le2 P.hc P.hz P.hs P.hκ P.hd0 hinv A
              rw [if_pos hcond.2.1, zpow_natCast] at hfl
              exact hfl
            · rw [if_neg hcond]
              exact mul_nonneg hVs (mul_nonneg (pow_nonneg hz0.le _) hg)
          refine hle.trans ?_
          rw [ExPh_mul_const, hval, Nat.sub_self, pow_zero, one_mul]
          have hRc : 1 ≤ (P.lp / lpi) ^ swCnt Sw h.length T0 := one_le_pow₀ hRg1
          calc V2 P.c P.z P.s P.κ P.d st * ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 2 h.length) h
              ≤ V2 P.c P.z P.s P.κ P.d st * P.e 2 := mul_le_mul_of_nonneg_left (hC2 h hpe hlM) hVs
            _ = 1 * (P.e 2 * V2 P.c P.z P.s P.κ P.d st) := by ring
            _ ≤ (P.lp / lpi) ^ swCnt Sw h.length T0 * (P.e 2 * V2 P.c P.z P.s P.κ P.d st) :=
                mul_le_mul_of_nonneg_right hRc (mul_nonneg he2 hVs)
            _ = _ := by ring
        · -- between the anchor and the check
          have hjk3 : j < k := by omega
          by_cases hT : h.length < T0
          · have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k) h ≤
                ExPh (κ := κ) (PE Δ M) (M - h.length - 1)
                  (fun h' => lpi ^ (k - (j + 1)) * (P.lp / lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    truncG h.length G (postB2 P st h.length) h') h := by
              apply ExPh_mono_on
              intro o t ht hk hend
              have hf := reach o t ht hk hend
              generalize hh' : h ++ [o] ++ t = h' at hf ⊢
              have hp' := next_pidx hpe hlM hf
              have hrs := next_rf_succ hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
              rw [hj] at hp' hrs
              rw [hst] at hrs
              have hpost := post2_le (Δ := Δ) P hinv h.length h' hf.lt.le
              have hpb : 0 ≤ postB2 P st h.length h' :=
                le_trans (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 _).le hpost
              have hnn := (noLong_next (G := G) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk))
              rw [hj] at hnn
              have hg0 : gend Δ M (strOf h') k0 = gend Δ M (strOf h) k0 :=
                next_gend hpe hlM hf (by rw [hj]; exact hjk)
              have hcnt : swCnt Sw h'.length T0 ≤ swCnt Sw (h.length + 1) T0 :=
                swCnt_anti Sw (by have := hf.lt; omega)
              have hW0 : 0 ≤ lpi ^ (k - (j + 1)) * (P.lp / lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 := by
                positivity
              unfold ΦfE3
              rw [hp', if_neg (by omega), if_pos (by omega), hg0, hT0]
              split_ifs with hc
              · have hl : h'.length ≤ h.length + G := (hnn.1 hc.2.1).2
                rw [hrs]
                unfold truncG; rw [if_pos hl]
                exact mul_le_mul (mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left
                  (pow_le_pow_right₀ hRg1 hcnt) (pow_nonneg hlpi0.le _)) he2) hpost
                  (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 _).le hW0
              · refine mul_nonneg hW0 ?_
                unfold truncG; split_ifs
                · exact hpb
                · exact le_rfl
            refine hle.trans ?_
            rw [ExPh_mul_const, hval]
            have hw : 0 ≤ lpi ^ (k - (j + 1)) * (P.lp / lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 := by
              positivity
            have hkj : k - j = k - (j + 1) + 1 := by omega
            by_cases hsw : Sw h.length
            · have hpost2 := ex_post2G_at (κ := κ) P hW hG hinv hpe (by omega : h.length + Δ + 1 ≤ M)
                (fun i h2 h17 => hE i h2 h17 h hpe hlM)
              have hc1 : swCnt Sw h.length T0 = swCnt Sw (h.length + 1) T0 + 1 := swCnt_succ_pos Sw hsw hT
              rw [hc1]
              calc lpi ^ (k - (j + 1)) * (P.lp / lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (postB2 P st h.length)) h
                  ≤ lpi ^ (k - (j + 1)) * (P.lp / lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    (P.lp * V2 P.c P.z P.s P.κ P.d st) := mul_le_mul_of_nonneg_left hpost2 hw
                _ = _ := by
                  obtain ⟨R, hR⟩ : ∃ R, P.lp / lpi = R := ⟨_, rfl⟩
                  have hlR : P.lp = lpi * R := by rw [← hR]; field_simp
                  rw [hR, hlR, hkj, pow_succ, pow_succ]; ring
            · obtain ⟨ei, pat0, hcl, hX, hEi⟩ := hIn h hpe (by omega) hsw
              have hpost2 := ex_post2G_gen (κ := κ) P hcl hinv (by omega : h.length + Δ + 1 ≤ M) hX hEi
              have hc1 : swCnt Sw (h.length + 1) T0 ≤ swCnt Sw h.length T0 := swCnt_anti Sw (by omega)
              calc lpi ^ (k - (j + 1)) * (P.lp / lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (postB2 P st h.length)) h
                  ≤ lpi ^ (k - (j + 1)) * (P.lp / lpi) ^ swCnt Sw (h.length + 1) T0 * P.e 2 *
                    (lpi * V2 P.c P.z P.s P.κ P.d st) := mul_le_mul_of_nonneg_left hpost2 hw
                _ ≤ lpi ^ (k - (j + 1)) * (P.lp / lpi) ^ swCnt Sw h.length T0 * P.e 2 *
                    (lpi * V2 P.c P.z P.s P.κ P.d st) :=
                    mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left
                      (pow_le_pow_right₀ hRg1 hc1) (pow_nonneg hlpi0.le _)) he2) (mul_nonneg hlpi0.le hVs)
                _ = _ := by rw [hkj, pow_succ]; ring
          · -- the window is over: nothing more
            have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k) h ≤
                ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => 0) h := by
              apply ExPh_mono_on
              intro o t ht hk hend
              have hf := reach o t ht hk hend
              generalize hh' : h ++ [o] ++ t = h' at hf ⊢
              have hp' := next_pidx hpe hlM hf
              rw [hj] at hp'
              have hg0 : gend Δ M (strOf h') k0 = gend Δ M (strOf h) k0 :=
                next_gend hpe hlM hf (by rw [hj]; exact hjk)
              unfold ΦfE3
              rw [hp', if_neg (by omega), if_pos (by omega), hg0, hT0,
                if_neg (fun hc => by have := hf.lt; have := hc.2.2; omega)]
            refine hle.trans ?_
            rw [ExPh_const, hval]
            positivity
      · -- past the horizon: nothing more
        have hval : ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k h = 0 := by
          unfold ΦfE3; rw [hj, if_neg (by omega), if_pos hjk2, hT0, if_neg hHl]
        rw [hval]
        have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k) h ≤
            ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => 0) h := by
          apply ExPh_mono_on
          intro o t ht hk hend
          have hf := reach o t ht hk hend
          generalize hh' : h ++ [o] ++ t = h' at hf ⊢
          have hp' := next_pidx hpe hlM hf
          rw [hj] at hp'
          have hg0 : gend Δ M (strOf h') k0 = gend Δ M (strOf h) k0 :=
            next_gend hpe hlM hf (by rw [hj]; exact hjk)
          unfold ΦfE3
          rw [hp', if_neg (by omega)]
          by_cases hj' : j + 1 ≤ k
          · rw [if_pos hj']
            have hnn := (noLong_next (G := G) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk))
            rw [hj] at hnn
            rw [hg0, hT0, if_neg (fun hc => hHl ⟨by have := hf.lt; omega, (hnn.1 hc.2.1).1,
              by have := hf.lt; have := hc.2.2; omega⟩)]
          · rw [if_neg hj']
            have hjeq : j = k := by omega
            unfold failHE3
            by_cases hnl : NoLong Δ M G k0 k (strOf h') ∧ gend Δ M (strOf h') k ≤ gend Δ M (strOf h') k0 + L
            · rw [if_pos hnl]
              have hnl0 : NoLong Δ M G k0 j (strOf h) := by
                rw [hjeq]; exact (noLong_stable hpe hlM hf (by rw [hj]; omega)).1 hnl.1
              have hsp : h.length ≤ T0 := by
                have h2 := hnl.2
                rw [next_gend hpe hlM hf (show k ≤ _ by rw [hj]; omega), hg0, ← hjeq, hgj, hT0] at h2
                exact h2
              unfold failH
              rw [hp', if_pos (by omega)]
              have hfn := next_failC_new (Hc := Hc) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
              rw [hj] at hfn
              rw [← hjeq, hfn, if_neg (fun hc => hHl ⟨hc.1, hnl0, hsp⟩)]
            · rw [if_neg hnl]
        exact hle.trans (le_of_eq (ExPh_const _ _ _ _))
    · -- after the check: the failure is fixed
      push Not at hjk2
      have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k) h ≤
          ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k h) h := by
        apply ExPh_mono_on
        intro o t ht hk hend
        have hf := reach o t ht hk hend
        generalize hh' : h ++ [o] ++ t = h' at hf ⊢
        have hp' := next_pidx hpe hlM hf
        rw [hj] at hp'
        have hst' := noLong_stable (G := G) (k0 := k0) (j := k) hpe hlM hf (by rw [hj]; omega)
        have hgk := next_gend hpe hlM hf (i := k) (by rw [hj]; omega)
        have hgk0 := next_gend hpe hlM hf (i := k0) (by rw [hj]; omega)
        have hC : (NoLong Δ M G k0 k (strOf h') ∧ gend Δ M (strOf h') k ≤ gend Δ M (strOf h') k0 + L) ↔
            (NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L) := by
          rw [hgk, hgk0]; exact and_congr_left fun _ => hst'
        have e1 : ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k h' =
            (if NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L then
              failC Δ M Hc k0 k (strOf h') else 0) := by
          unfold ΦfE3 failHE3 failH; rw [hp', if_neg (by omega), if_neg (by omega)]
          by_cases hn : NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L
          · rw [if_pos (hC.2 hn), if_pos hn, if_pos (by omega)]
          · rw [if_neg (fun h'' => hn (hC.1 h'')), if_neg hn]
        have e2 : ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k h =
            (if NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L then
              failC Δ M Hc k0 k (strOf h) else 0) := by
          unfold ΦfE3 failHE3 failH; rw [hj, if_neg (by omega), if_neg (by omega)]
          by_cases hn : NoLong Δ M G k0 k (strOf h) ∧ gend Δ M (strOf h) k ≤ gend Δ M (strOf h) k0 + L
          · rw [if_pos hn, if_pos hn, if_pos (by omega)]
          · rw [if_neg hn, if_neg hn]
        rw [e1, e2, next_failC_old hpe hlM hf (by rw [hj]; exact hjk2) (by omega)]
      exact hle.trans (le_of_eq (ExPh_const _ _ _ _))

theorem failHE3_le_phi (P : Cert2 B Δ) (he2 : 0 ≤ P.e 2) {lpi : ℝ} (hlpi0 : 0 < lpi) (Sw : ℕ → Prop)
    {Ccap G L Hc k0 k : ℕ} (hk0 : k0 ≤ k) (h : List Out) :
    failHE3 Δ M G L Hc k0 k h ≤ ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k h := by
  classical
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have hlp := P.hlp0
  have hRg0 : 0 ≤ P.lp / lpi := div_nonneg hlp hlpi0.le
  by_cases h1 : pidx Δ M (strOf h) h.length < k0
  · have hf : failHE3 Δ M G L Hc k0 k h = 0 := by
      unfold failHE3 failH; split_ifs <;> first | rfl | omega
    rw [hf]; unfold ΦfE3; rw [if_pos h1]
    apply mul_nonneg (by positivity)
    apply add_nonneg (mul_nonneg (pow_nonneg P.hlr0 _) (zpow_nonneg hc0.le _))
    exact mul_nonneg (by linarith [P.hb1, P.hlr1]) (Finset.sum_nonneg fun i _ => pow_nonneg P.hlr0 _)
  · by_cases h2 : pidx Δ M (strOf h) h.length ≤ k
    · have hf : failHE3 Δ M G L Hc k0 k h = 0 := by
        unfold failHE3 failH; split_ifs <;> first | rfl | omega
      rw [hf]; unfold ΦfE3; rw [if_neg h1, if_pos h2]
      split_ifs
      · exact mul_nonneg (by positivity) (V2_pos hc0 hz0 (by linarith [P.hs]) P.hκ P.hd0 _).le
      · exact le_rfl
    · unfold ΦfE3; rw [if_neg h1, if_neg h2]

/-- **A failed check is rare**, with an in-epoch contraction. -/
theorem fail_checkE3 (P : Cert2 B Δ) (hW : κ.Within B) {G : ℕ} (hG : Δ + 1 ≤ G)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (hC2 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 2 h.length) h ≤ P.e 2)
    (hE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ h, PE Δ M h → h.length < M →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ P.e i)
    {lpi : ℝ} (hlpi0 : 0 < lpi) (hlpi : lpi ≤ P.lp)
    (Sw : ℕ → Prop) {Ccap L : ℕ} (hcap : ∀ t, swCnt Sw t (t + L) ≤ Ccap)
    (hIn : ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M → ¬ Sw h.length → ∃ (e : Fin 19 → ℝ) (pat : ℝ),
      ClassOK P lpi e pat ∧
      pat ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG 1 h.length)) h ∧
      ∀ i : Fin 19, i ≠ 2 → i ≠ 17 →
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ e i)
    {Hc : ℕ} (hHc : Hc + Δ + 1 ≤ M) {k0 k : ℕ} (hk0 : k0 ≤ k) :
    Ex κ M (failHE3 Δ M G L Hc k0 k) [] ≤
      lpi ^ (k - k0) * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) := by
  classical
  have hM : 0 < M := by omega
  have hc0 : 0 < P.c := by linarith [P.hc]
  have he2 : 0 ≤ P.e 2 := le_trans (ExPh_nonneg _ _ (fun y => WP_nonneg P 2 0 y (by decide)) _)
    (hC2 [] (pe_nil hM) (by simpa using hM))
  have hlp := P.hlp0
  have hRg1 : 1 ≤ P.lp / lpi := by rw [le_div_iff₀ hlpi0]; linarith
  have hF : 0 ≤ lpi ^ (k - k0) * (P.lp / lpi) ^ Ccap * P.e 2 := by positivity
  calc Ex κ M (failHE3 Δ M G L Hc k0 k) [] ≤ Ex κ M (ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k) [] :=
        Ex_mono M (failHE3_le_phi P he2 hlpi0 Sw hk0) []
    _ ≤ ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k [] := by
        have := Ex_phase (κ := κ) (PE Δ M) (Φ := ΦfE3 Δ M P lpi Sw Ccap G L Hc k0 k) (M := M)
          (fun h hpe hlM => phiFE3_step P hW hG hR0 hR1 hC2 hE hlpi0 hlpi Sw hcap hIn hHc hk0 hpe hlM)
          (pe_nil hM) (by simp)
        simpa using this
    _ ≤ _ := by
        have hp0 : pidx Δ M (strOf []) ([] : List Out).length = 0 := by
          apply Nat.eq_zero_of_le_zero
          exact pidx_le_of (by simp [gend_zero])
        have hb0 : (bnd Δ (strOf []) 0 (gend Δ M (strOf [])) 0).1 = 0 := rfl
        unfold ΦfE3
        rw [hp0]
        by_cases hk : 0 < k0
        · rw [if_pos hk, hb0, zpow_zero, mul_one, Nat.sub_zero]
          exact mul_le_mul_of_nonneg_left (geom_mix P.hlr0 P.hlr1 P.hb1 k0) hF
        · have : k0 = 0 := by omega
          subst this
          have hg00 : gend Δ M (strOf ([] : List Out)) 0 = 0 := gend_zero
          rw [if_neg (by omega), if_pos (Nat.zero_le _), hg00,
            if_pos ⟨by simp, noLong_self G 0 _, by simp⟩]
          unfold rf rho0
          simp only [runFrom, Nat.sub_zero, Nat.sub_self]
          rw [hb0, V2_warm (show (0 : ℤ) ≤ ((0 : ℤ), (0 : ℤ)).2 from le_rfl), zpow_zero, mul_one]
          have hcnt : swCnt Sw ([] : List Out).length (0 + L) ≤ Ccap := by simpa using hcap 0
          have : 0 ≤ (P.b - 1) / (1 - P.lr) := div_nonneg (by linarith [P.hb1]) (by linarith [P.hlr1])
          calc lpi ^ (k - 0) * (P.lp / lpi) ^ swCnt Sw ([] : List Out).length (0 + L) * P.e 2
              ≤ lpi ^ (k - 0) * (P.lp / lpi) ^ Ccap * P.e 2 :=
                mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left (pow_le_pow_right₀ hRg1 hcnt)
                  (pow_nonneg hlpi0.le _)) he2
            _ = lpi ^ (k - 0) * (P.lp / lpi) ^ Ccap * P.e 2 * 1 := by ring
            _ ≤ _ := mul_le_mul_of_nonneg_left (by linarith) hF


end Cryptarchia.Prob
