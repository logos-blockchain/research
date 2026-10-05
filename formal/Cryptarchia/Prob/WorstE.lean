import Cryptarchia.Prob.Worst

/-!
# From conditional slot laws to a kernel, with one band per epoch

`law_le` lets the worst case pick a band member at every slot. In the protocol,
the band a slot runs under is set by its epoch's state (stake snapshot and stake
estimate), so it is fixed within an epoch and changes only when a new epoch starts.

Here the members of a family are `fam : Fin K → Band`, and slot `n + 1` runs under
member `Bsel n`, which is known before the slot (`hBm`) and changes only when slot
`n + 2` starts a new epoch of length `EL` (`hBc`). The worst case then picks a member
at each epoch start and keeps it for the epoch (`worstKE`, a kernel within the family
per epoch: `Kern.EpochFam`), and bounds every event closed under adding adversarial
slots (`law_le_epoch`).
-/

namespace Cryptarchia.Prob

open MeasureTheory Finset
open scoped ENNReal

/-- **A kernel within a family, one member per epoch.** The next slot after `l` is within
member `mem l`, which stays the same unless that slot starts a new epoch. -/
def Kern.EpochFam (κ : Kern) (EL : ℕ) {K : ℕ} (fam : Fin K → Band) : Prop :=
  ∃ mem : List Out → Fin K, (∀ l, κ.BandAt (fam (mem l)) l) ∧
    ∀ l o, (l.length + 2) % EL ≠ 0 → mem (l ++ [o]) = mem l

theorem Kern.EpochFam.fam {κ : Kern} {EL K : ℕ} {fam : Fin K → Band} (h : κ.EpochFam EL fam) :
    κ.Fam (List.ofFn fam) := by
  obtain ⟨mem, hb, -⟩ := h
  exact fun l => ⟨fam (mem l), List.mem_ofFn.2 ⟨mem l, rfl⟩, hb l⟩

variable {K : ℕ} (fam : Fin K → Band) (EL : ℕ) (F : List Out → ℝ)

open Classical in
/-- The members whose honest polytope is not empty. -/
noncomputable def goodB : Finset (Fin K) := Finset.univ.filter fun b => (HB (fam b)).Nonempty

variable {fam} (hG : (goodB fam).Nonempty)

/-- The value after a slot: at an epoch start, the worst member; otherwise the same. -/
noncomputable def nextV (V : List Out → Fin K → ℝ) (l : List Out) (b : Fin K) : ℝ :=
  if (l.length + 1) % EL = 0 then (goodB fam).sup' hG fun b' => V l b' else V l b

/-- **The worst case with one member per epoch**, with `n` slots to go, history `l`,
and current member `b`. -/
noncomputable def VE : ℕ → List Out → Fin K → ℝ
  | 0, l, _ => F l
  | n + 1, l, b => sSup ((fun q => ∑ o, prodLaw q (fam b).amax o * nextV EL hG (VE n) (l ++ [o]) b) '' HB (fam b))

variable {EL F hG}

theorem mem_goodB {b : Fin K} : b ∈ goodB fam ↔ (HB (fam b)).Nonempty := by
  classical
  unfold goodB; simp

theorem VE_attain {b : Fin K} (hb : b ∈ goodB fam) (n : ℕ) (l : List Out) :
    ∃ q ∈ HB (fam b), VE EL F hG (n + 1) l b = ∑ o, prodLaw q (fam b).amax o * nextV EL hG (VE EL F hG n) (l ++ [o]) b ∧
      ∀ q' ∈ HB (fam b), ∑ o, prodLaw q' (fam b).amax o * nextV EL hG (VE EL F hG n) (l ++ [o]) b ≤
        VE EL F hG (n + 1) l b := by
  set φ : (Fin 3 → ℝ) → ℝ := fun q => ∑ o, prodLaw q (fam b).amax o * nextV EL hG (VE EL F hG n) (l ++ [o]) b
  have hc : Continuous φ := by
    refine continuous_finsetSum _ fun o _ => ?_
    unfold prodLaw
    exact ((continuous_apply o.hon).mul continuous_const).mul continuous_const
  obtain ⟨q, hq, hmax⟩ := HB_isCompact.exists_isMaxOn (mem_goodB.1 hb) hc.continuousOn
  have hg : IsGreatest (φ '' HB (fam b)) (φ q) := ⟨⟨q, hq, rfl⟩, by rintro _ ⟨q', hq', rfl⟩; exact hmax hq'⟩
  have hW : VE EL F hG (n + 1) l b = φ q := hg.csSup_eq
  exact ⟨q, hq, hW, fun q' hq' => hW ▸ hmax hq'⟩

theorem VE_bad {b : Fin K} (hb : b ∉ goodB fam) (n : ℕ) (l : List Out) : VE EL F hG (n + 1) l b = 0 := by
  have : HB (fam b) = ∅ := by
    rw [mem_goodB, Set.not_nonempty_iff_eq_empty] at hb; exact hb
  show sSup _ = 0
  rw [this, Set.image_empty, Real.sSup_empty]

section Mono

variable (hP : ∀ b, (fam b).Prod)
include hP

omit hP in
theorem nextV_nonneg {V : List Out → Fin K → ℝ} (hV : ∀ l b, 0 ≤ V l b) (l : List Out) (b : Fin K) :
    0 ≤ nextV EL hG V l b := by
  unfold nextV
  split_ifs
  · obtain ⟨b0, hb0⟩ := hG
    exact le_trans (hV l b0) (Finset.le_sup' (fun b' => V l b') hb0)
  · exact hV l b

theorem VE_nonneg (hF : ∀ l, 0 ≤ F l) : ∀ n l b, 0 ≤ VE EL F hG n l b
  | 0, l, _ => hF l
  | n + 1, l, b => by
    by_cases hb : b ∈ goodB fam
    · obtain ⟨q, hq, hW, -⟩ := VE_attain (F := F) (EL := EL) (hG := hG) hb n l
      rw [hW]
      exact Finset.sum_nonneg fun o _ => mul_nonneg (prodLaw_nonneg hq.1 (hP b).a0 (hP b).a1 o)
        (nextV_nonneg (VE_nonneg hF n) _ _)
    · rw [VE_bad hb]

omit hP in
theorem nextV_mono {V : List Out → Fin K → ℝ} (hV : ∀ l l' b, List.Forall₂ OutLe l l' → V l b ≤ V l' b)
    {l l' : List Out} (h : List.Forall₂ OutLe l l') (b : Fin K) : nextV EL hG V l b ≤ nextV EL hG V l' b := by
  unfold nextV
  rw [h.length_eq]
  split_ifs
  · exact Finset.sup'_le _ _ fun b' hb' => le_trans (hV l l' b' h) (Finset.le_sup' (fun b' => V l' b') hb')
  · exact hV l l' b h

/-- **The worst case is monotone in adversarial slots.** -/
theorem VE_mono (hF : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l') :
    ∀ n l l' b, List.Forall₂ OutLe l l' → VE EL F hG n l b ≤ VE EL F hG n l' b
  | 0, l, l', _, h => hF l l' h
  | n + 1, l, l', b, h => by
    by_cases hb : b ∈ goodB fam
    · obtain ⟨q, hq, hW, -⟩ := VE_attain (F := F) (EL := EL) (hG := hG) hb n l
      obtain ⟨-, -, -, hmax'⟩ := VE_attain (F := F) (EL := EL) (hG := hG) hb n l'
      rw [hW]
      refine le_trans (Finset.sum_le_sum fun o _ => ?_) (hmax' q hq)
      exact mul_le_mul_of_nonneg_left
        (nextV_mono (VE_mono hF n) (forall₂_append h (List.Forall₂.cons (OutLe.refl o) List.Forall₂.nil)) b)
        (prodLaw_nonneg hq.1 (hP b).a0 (hP b).a1 o)
    · rw [VE_bad hb, VE_bad hb]

/-- **One slot of the true law** under member `b` is at most the worst case. -/
theorem stepE_le (hF : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l') {b : Fin K} {q : Fin 3 → ℝ}
    (hq : q ∈ HB (fam b)) {a : ℝ} (ha : a ≤ (fam b).amax) (n : ℕ) (l : List Out) :
    ∑ o, prodLaw q a o * nextV EL hG (VE EL F hG n) (l ++ [o]) b ≤ VE EL F hG (n + 1) l b := by
  have hb : b ∈ goodB fam := mem_goodB.2 ⟨q, hq⟩
  obtain ⟨-, -, -, hmax⟩ := VE_attain (F := F) (EL := EL) (hG := hG) hb n l
  refine le_trans ?_ (hmax q hq)
  rw [sum_prodLaw, sum_prodLaw]
  refine Finset.sum_le_sum fun h _ => mul_le_mul_of_nonneg_left ?_ (hq.1 h)
  have hm := nextV_mono (EL := EL) (hG := hG) (VE_mono (EL := EL) (hG := hG) hP hF n) (l := l ++ [⟨h, false⟩]) (l' := l ++ [⟨h, true⟩])
    (forall₂_append (forall₂_refl l) (List.Forall₂.cons ⟨rfl, fun x => absurd x (by simp)⟩ List.Forall₂.nil)) b
  nlinarith

end Mono

/-! ## The worst-case kernel, one member per epoch -/

variable (EL F hG) in
/-- The worst member for history `l`, with `n` slots to go. -/
noncomputable def argB (n : ℕ) (l : List Out) : Fin K :=
  Classical.choose (Finset.exists_max_image (goodB fam) (fun b => VE EL F hG n l b) hG)

theorem argB_mem (n : ℕ) (l : List Out) : argB EL F hG n l ∈ goodB fam :=
  (Classical.choose_spec (Finset.exists_max_image (goodB fam) (fun b => VE EL F hG n l b) hG)).1

theorem sup'_eq_argB (n : ℕ) (l : List Out) :
    (goodB fam).sup' hG (fun b => VE EL F hG n l b) = VE EL F hG n l (argB EL F hG n l) :=
  le_antisymm (Finset.sup'_le _ _
    (Classical.choose_spec (Finset.exists_max_image (goodB fam) (fun b => VE EL F hG n l b) hG)).2)
    (Finset.le_sup' (fun b => VE EL F hG n l b) (argB_mem n l))

variable (EL F hG) in
/-- **The member the worst case plays after `l`**: chosen at each epoch start
(and at the beginning), then kept. -/
noncomputable def memE (M : ℕ) (l : List Out) : Fin K :=
  if l = [] ∨ (l.length + 1) % EL = 0 then argB EL F hG (M - l.length) l else memE M l.dropLast
termination_by l.length
decreasing_by
  have hl : l ≠ [] := fun h' => by simp_all
  rw [List.length_dropLast]
  exact Nat.sub_lt (List.length_pos_of_ne_nil hl) one_pos

theorem memE_good (M : ℕ) : ∀ l : List Out, memE EL F hG M l ∈ goodB fam := by
  intro l
  induction h : l.length using Nat.strong_induction_on generalizing l with
  | _ n ih =>
    rw [memE]
    split_ifs with hc
    · exact argB_mem _ _
    · have hl : l ≠ [] := fun h' => hc (Or.inl h')
      exact ih _ (by rw [← h, List.length_dropLast]; exact Nat.sub_lt (List.length_pos_of_ne_nil hl) one_pos) _ rfl

theorem memE_snoc (M : ℕ) (l : List Out) (o : Out) :
    memE EL F hG M (l ++ [o]) = if (l.length + 2) % EL = 0 then argB EL F hG (M - (l.length + 1)) (l ++ [o])
      else memE EL F hG M l := by
  rw [memE]
  simp only [List.append_eq_nil_iff, List.cons_ne_nil, and_false, false_or, List.length_append,
    List.length_singleton, List.dropLast_concat]

variable (EL F hG) in
/-- The worst-case honest law after `l`. -/
noncomputable def qE (M : ℕ) (l : List Out) : Fin 3 → ℝ :=
  Classical.choose (VE_attain (F := F) (EL := EL) (hG := hG) (memE_good (EL := EL) (F := F) (hG := hG) M l) (M - l.length - 1) l)

theorem qE_mem (M : ℕ) (l : List Out) : qE EL F hG M l ∈ HB (fam (memE EL F hG M l)) :=
  (Classical.choose_spec (VE_attain (F := F) (EL := EL) (hG := hG) (memE_good (EL := EL) (F := F) (hG := hG) M l) (M - l.length - 1) l)).1

theorem qE_val (M : ℕ) (l : List Out) :
    VE EL F hG (M - l.length - 1 + 1) l (memE EL F hG M l) =
      ∑ o, prodLaw (qE EL F hG M l) (fam (memE EL F hG M l)).amax o *
        nextV EL hG (VE EL F hG (M - l.length - 1)) (l ++ [o]) (memE EL F hG M l) :=
  (Classical.choose_spec (VE_attain (F := F) (EL := EL) (hG := hG) (memE_good (EL := EL) (F := F) (hG := hG) M l) (M - l.length - 1) l)).2.1

variable (EL F hG) in
/-- **The worst-case kernel, one member per epoch.** -/
noncomputable def worstKE (hP : ∀ b, (fam b).Prod) (M : ℕ) : Kern where
  p l o := prodLaw (qE EL F hG M l) (fam (memE EL F hG M l)).amax o
  nonneg l o := prodLaw_nonneg (qE_mem (EL := EL) (F := F) (hG := hG) M l).1 (hP _).a0 (hP _).a1 o
  sum_one l := sum_prodLaw_one (qE_mem (EL := EL) (F := F) (hG := hG) M l).2.1 _

theorem worstKE_Ex (hP : ∀ b, (fam b).Prod) {M : ℕ} : ∀ n (l : List Out), l.length + n = M →
    Ex (worstKE EL F hG hP M) n F l = VE EL F hG n l (memE EL F hG M l)
  | 0, l, _ => rfl
  | n + 1, l, h => by
    rw [Ex_succ]
    have e : M - l.length - 1 = n := by omega
    have hv := qE_val (F := F) (EL := EL) (hG := hG) M l
    rw [e] at hv
    rw [hv]
    refine Finset.sum_congr rfl fun o _ => ?_
    rw [worstKE_Ex hP n (l ++ [o]) (by simp; omega)]
    congr 1
    rw [memE_snoc]
    unfold nextV
    simp only [List.length_append, List.length_singleton]
    split_ifs with hc
    · rw [show M - (l.length + 1) = n by omega, sup'_eq_argB]
    · rfl

/-- **The worst-case kernel keeps one member per epoch.** -/
theorem worstKE_epochFam (hP : ∀ b, (fam b).Prod) (M : ℕ) : (worstKE EL F hG hP M).EpochFam EL fam :=
  ⟨memE EL F hG M, fun l => bandAt_prodLaw (hP _) (qE_mem (EL := EL) (F := F) (hG := hG) M l) fun _ => rfl,
    fun l o hc => by rw [memE_snoc, if_neg hc]⟩

/-! ## Conditional laws to the per-epoch worst-case kernel -/

set_option maxHeartbeats 800000 in
/-- **From conditional slot laws to a kernel, one member per epoch.** As `law_le`, but
slot `n + 1` runs under member `Bsel n`: known before the slot (`hBm`), and the same
for consecutive slots of one epoch (`hBc`). Then every event closed under adding
adversarial slots is at most as likely as under a kernel that keeps one member per
epoch. -/
theorem law_le_epoch {Ω : Type*} [mΩ : MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ]
    {K : ℕ} {fam : Fin K → Band} (hP : ∀ b, (fam b).Prod) {EL M : ℕ} (hM : 0 < M)
    (X : ℕ → Ω → Out) (hXm : ∀ j, Measurable (X j))
    (m : ℕ → MeasurableSpace Ω) (hm : ∀ n, m n ≤ mΩ) (hX : ∀ n j, j < n → Measurable[m n] (X j))
    (qh : ℕ → Ω → Fin 3 → ℝ) (qa : ℕ → Ω → ℝ) (Bsel : ℕ → Ω → Fin K)
    (hQ : ∀ n < M, ∀ ω, qh n ω ∈ HB (fam (Bsel n ω)) ∧ 0 ≤ qa n ω ∧ qa n ω ≤ (fam (Bsel n ω)).amax)
    (hBm : ∀ n < M, Measurable[m n] (Bsel n))
    (hBc : ∀ n ω, (n + 2) % EL ≠ 0 → Bsel (n + 1) ω = Bsel n ω)
    (hQm : ∀ n < M, ∀ o, Measurable[m n] fun ω => ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o))
    (hcond : ∀ n < M, ∀ f : Ω → ℝ≥0∞, Measurable[m n] f → ∀ o,
      ∫⁻ ω, f ω * (if X n ω = o then 1 else 0) ∂μ =
        ∫⁻ ω, f ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ)
    {S : Set (List Out)} (hS : UpClosed S) :
    ∃ κ : Kern, κ.EpochFam EL fam ∧
      μ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} ≤ ENNReal.ofReal (Ex κ M (S.indicator 1) []) := by
  classical
  obtain ⟨ω0⟩ := nonempty_of_prob μ
  have hG : (goodB fam).Nonempty := ⟨Bsel 0 ω0, mem_goodB.2 ⟨qh 0 ω0, (hQ 0 hM ω0).1⟩⟩
  set F : List Out → ℝ := S.indicator 1 with hFdef
  have hF0 : ∀ l, 0 ≤ F l := fun l => Set.indicator_nonneg (fun _ _ => zero_le_one) l
  have hFm : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l' := by
    intro l l' h
    by_cases hl : l ∈ S
    · rw [hFdef, Set.indicator_of_mem hl, Set.indicator_of_mem (hS l l' h hl)]; exact le_rfl
    · rw [hFdef, Set.indicator_of_notMem hl]; exact hF0 l'
  refine ⟨worstKE EL F hG hP M, worstKE_epochFam hP M, ?_⟩
  set I : ℕ → ℝ≥0∞ := fun n =>
    ∫⁻ ω, ENNReal.ofReal (VE EL F hG (M - n) (List.ofFn fun k : Fin n => X k ω) (Bsel n ω)) ∂μ with hI
  have hvec : ∀ n, Measurable[m n] (fun ω (k : Fin n) => X k ω) :=
    fun n => by letI := m n; exact measurable_pi_iff.mpr fun k : Fin n => hX n k.val k.2
  have hstep : ∀ n, n < M → I (n + 1) ≤ I n := by
    intro n hn
    obtain ⟨k, hk⟩ : ∃ k, M - n = k + 1 := ⟨M - (n + 1), by omega⟩
    have hk' : M - (n + 1) = k := by omega
    set f : Out → Ω → ℝ≥0∞ := fun o ω =>
      ENNReal.ofReal (nextV EL hG (VE EL F hG k) ((List.ofFn fun j : Fin n => X j ω) ++ [o]) (Bsel n ω)) with hf
    have hpair : Measurable[m n] (fun ω => ((fun k : Fin n => X k ω), Bsel n ω)) := by
      letI := m n; exact (hvec n).prodMk (hBm n (by omega))
    have hfm : ∀ o, Measurable[m n] (f o) := fun o => by
      letI := m n
      exact (measurable_of_countable (fun p : (Fin n → Out) × Fin K =>
        ENNReal.ofReal (nextV EL hG (VE EL F hG k) (List.ofFn p.1 ++ [o]) p.2))).comp hpair
    have hind : ∀ o, Measurable fun ω => (if X n ω = o then (1 : ℝ≥0∞) else 0) := fun o =>
      (measurable_of_countable (fun x : Out => if x = o then (1 : ℝ≥0∞) else 0)).comp (hXm n)
    -- the member of the next slot: the same, or a new epoch where the worst case maximizes
    have hnext : ∀ ω, ENNReal.ofReal (VE EL F hG (M - (n + 1)) (List.ofFn fun j : Fin (n + 1) => X j ω) (Bsel (n + 1) ω)) ≤
        ∑ o, f o ω * (if X n ω = o then 1 else 0) := by
      intro ω
      have hsum : ∑ o, f o ω * (if X n ω = o then 1 else 0) = f (X n ω) ω := by
        simp only [mul_ite, mul_one, mul_zero, Finset.sum_ite_eq, Finset.mem_univ, ↓reduceIte]
      rw [hsum, hk', List.ofFn_succ_last]
      simp only [hf, Fin.coe_castSucc, Fin.val_last]
      refine ENNReal.ofReal_le_ofReal ?_
      unfold nextV
      simp only [List.length_append, List.length_ofFn, List.length_singleton]
      split_ifs with hc
      · obtain ⟨b0, hb0⟩ := id hG
        cases k with
        | zero => exact Finset.le_sup' (fun b' => VE EL F hG 0 _ b') hb0
        | succ k =>
        by_cases hgood : Bsel (n + 1) ω ∈ goodB fam
        · exact Finset.le_sup' (fun b' => VE EL F hG (k + 1) _ b') hgood
        · have : VE EL F hG (k + 1) (List.ofFn (fun j : Fin n => X j ω) ++ [X n ω]) (Bsel (n + 1) ω) ≤ 0 := by
            rw [VE_bad hgood]
          exact le_trans this (le_trans (VE_nonneg hP hF0 (k + 1) _ b0)
            (Finset.le_sup' (fun b' => VE EL F hG (k + 1) _ b') hb0))
      · rw [hBc n ω (by omega)]
    calc I (n + 1) ≤ ∫⁻ ω, ∑ o, f o ω * (if X n ω = o then 1 else 0) ∂μ := by
          simp only [hI]; exact lintegral_mono fun ω => hnext ω
      _ = ∑ o, ∫⁻ ω, f o ω * (if X n ω = o then 1 else 0) ∂μ :=
          lintegral_finsetSum _ fun o _ => ((hfm o).mono (hm n) le_rfl).mul (hind o)
      _ = ∑ o, ∫⁻ ω, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ :=
          Finset.sum_congr rfl fun o _ => hcond n (by omega) (f o) (hfm o) o
      _ = ∫⁻ ω, ∑ o, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ :=
          (lintegral_finsetSum _ fun o _ => (((hfm o).mul (hQm n (by omega) o))).mono (hm n) le_rfl).symm
      _ ≤ I n := by
          simp only [hI]
          refine lintegral_mono fun ω => ?_
          obtain ⟨hq, ha0, ha⟩ := hQ n (by omega) ω
          have ha1 : qa n ω ≤ 1 := le_trans ha (hP _).a1
          have hnn : ∀ o, 0 ≤ prodLaw (qh n ω) (qa n ω) o *
              nextV EL hG (VE EL F hG k) ((List.ofFn fun j : Fin n => X j ω) ++ [o]) (Bsel n ω) :=
            fun o => mul_nonneg (prodLaw_nonneg hq.1 ha0 ha1 o) (nextV_nonneg (VE_nonneg hP hF0 k) _ _)
          calc ∑ o, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o)
              = ENNReal.ofReal (∑ o, prodLaw (qh n ω) (qa n ω) o *
                  nextV EL hG (VE EL F hG k) ((List.ofFn fun j : Fin n => X j ω) ++ [o]) (Bsel n ω)) := by
                rw [ENNReal.ofReal_sum_of_nonneg fun o _ => hnn o]
                refine Finset.sum_congr rfl fun o _ => ?_
                rw [hf, mul_comm, ENNReal.ofReal_mul (prodLaw_nonneg hq.1 ha0 ha1 o)]
            _ ≤ ENNReal.ofReal (VE EL F hG (M - n) (List.ofFn fun j : Fin n => X j ω) (Bsel n ω)) := by
                rw [hk]
                exact ENNReal.ofReal_le_ofReal (stepE_le hP hFm hq ha k _)
  have hchain : ∀ n ≤ M, I n ≤ I 0 := by
    intro n hn
    induction n with
    | zero => exact le_rfl
    | succ n ih => exact (hstep n (by omega)).trans (ih (by omega))
  have h0 : I 0 ≤ ENNReal.ofReal (Ex (worstKE EL F hG hP M) M F []) := by
    rw [worstKE_Ex hP M [] (by simp)]
    simp only [hI, Nat.sub_zero, List.ofFn_zero]
    calc ∫⁻ ω, ENNReal.ofReal (VE EL F hG M [] (Bsel 0 ω)) ∂μ
        ≤ ∫⁻ _, ENNReal.ofReal (VE EL F hG M [] (memE EL F hG M [])) ∂μ := by
          refine lintegral_mono fun ω => ENNReal.ofReal_le_ofReal ?_
          have hg : Bsel 0 ω ∈ goodB fam := mem_goodB.2 ⟨_, (hQ 0 hM ω).1⟩
          have hmem : memE EL F hG M [] = argB EL F hG M [] := by rw [memE]; simp
          rw [hmem, ← sup'_eq_argB]
          exact Finset.le_sup' (fun b => VE EL F hG M [] b) hg
      _ = _ := by rw [lintegral_const, measure_univ, mul_one]
  have hMeq : I M = μ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} := by
    have hv : Measurable (fun ω (k : Fin M) => X k ω) := measurable_pi_iff.mpr fun k : Fin M => hXm k.val
    have hms : MeasurableSet {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} :=
      hv (Set.toFinite {v : Fin M → Out | List.ofFn v ∈ S}).measurableSet
    rw [← lintegral_indicator_one hms]
    simp only [hI, Nat.sub_self]
    refine lintegral_congr fun ω => ?_
    simp only [VE, hFdef, Set.indicator, Set.mem_setOf_eq, Pi.one_apply]
    split_ifs <;> simp
  rw [← hMeq]
  exact (hchain M le_rfl).trans h0

set_option maxHeartbeats 1600000 in
/-- **From conditional slot laws to a kernel, one member per epoch, while in band.**
As `law_le_epoch`, but the slot laws are known only while `ok` holds (for example,
while every epoch state is within a band of the family). Then an event closed under
adding adversarial slots, intersected with "`ok` at every slot", is at most as likely
as under a kernel with one member per epoch. -/
theorem law_le_epoch_ok {Ω : Type*} [mΩ : MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ]
    {K : ℕ} {fam : Fin K → Band} (hP : ∀ b, (fam b).Prod) {EL M : ℕ} (hM : 0 < M)
    (X : ℕ → Ω → Out) (hXm : ∀ j, Measurable (X j))
    (m : ℕ → MeasurableSpace Ω) (hm : ∀ n, m n ≤ mΩ) (hmono : ∀ j n, j ≤ n → m j ≤ m n)
    (hX : ∀ n j, j < n → Measurable[m n] (X j))
    (qh : ℕ → Ω → Fin 3 → ℝ) (qa : ℕ → Ω → ℝ) (Bsel : ℕ → Ω → Fin K)
    (ok : ℕ → Ω → Prop) (hokm : ∀ n < M, MeasurableSet[m n] {ω | ok n ω})
    (hQ : ∀ n < M, ∀ ω, ok n ω → qh n ω ∈ HB (fam (Bsel n ω)) ∧ 0 ≤ qa n ω ∧ qa n ω ≤ (fam (Bsel n ω)).amax)
    (hBm : ∀ n < M, Measurable[m n] (Bsel n))
    (hBc : ∀ n ω, (n + 2) % EL ≠ 0 → Bsel (n + 1) ω = Bsel n ω)
    (hQm : ∀ n < M, ∀ o, Measurable[m n] fun ω => ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o))
    (hcond : ∀ n < M, ∀ f : Ω → ℝ≥0∞, Measurable[m n] f → (∀ ω, ¬ ok n ω → f ω = 0) → ∀ o,
      ∫⁻ ω, f ω * (if X n ω = o then 1 else 0) ∂μ =
        ∫⁻ ω, f ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ)
    {S : Set (List Out)} (hS : UpClosed S) (hG : (goodB fam).Nonempty) :
    ∃ κ : Kern, κ.EpochFam EL fam ∧
      μ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧ ∀ n < M, ok n ω} ≤
        ENNReal.ofReal (Ex κ M (S.indicator 1) []) := by
  classical
  set F : List Out → ℝ := S.indicator 1 with hFdef
  have hF0 : ∀ l, 0 ≤ F l := fun l => Set.indicator_nonneg (fun _ _ => zero_le_one) l
  have hFm : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l' := by
    intro l l' h
    by_cases hl : l ∈ S
    · rw [hFdef, Set.indicator_of_mem hl, Set.indicator_of_mem (hS l l' h hl)]; exact le_rfl
    · rw [hFdef, Set.indicator_of_notMem hl]; exact hF0 l'
  refine ⟨worstKE EL F hG hP M, worstKE_epochFam hP M, ?_⟩
  set A : ℕ → Set Ω := fun n => {ω | ∀ j < n, ok j ω} with hAdef
  have hAm : ∀ n, n ≤ M → MeasurableSet[m n] (A n) := by
    intro n hn
    have : A n = ⋂ j ∈ Finset.range n, {ω | ok j ω} := by ext ω; simp [hAdef]
    rw [this]
    exact Finset.measurableSet_biInter _ fun j hj =>
      hmono j n (Finset.mem_range.1 hj).le _ (hokm j (by have := Finset.mem_range.1 hj; omega))
  have hAsucc : ∀ n, A (n + 1) = A n ∩ {ω | ok n ω} := by
    intro n; ext ω; simp only [hAdef, Set.mem_setOf_eq, Set.mem_inter_iff]
    constructor
    · intro h; exact ⟨fun j hj => h j (by omega), h n (by omega)⟩
    · rintro ⟨h1, h2⟩ j hj
      rcases Nat.lt_or_ge j n with h | h
      · exact h1 j h
      · rw [show j = n by omega]; exact h2
  set V : ℕ → Ω → ℝ≥0∞ := fun n ω =>
    ENNReal.ofReal (VE EL F hG (M - n) (List.ofFn fun k : Fin n => X k ω) (Bsel n ω)) with hVdef
  set I : ℕ → ℝ≥0∞ := fun n => ∫⁻ ω, (A n).indicator (V n) ω ∂μ with hI
  have hvec : ∀ n, Measurable[m n] (fun ω (k : Fin n) => X k ω) :=
    fun n => by letI := m n; exact measurable_pi_iff.mpr fun k : Fin n => hX n k.val k.2
  have hstep : ∀ n, n < M → I (n + 1) ≤ I n := by
    intro n hn
    obtain ⟨k, hk⟩ : ∃ k, M - n = k + 1 := ⟨M - (n + 1), by omega⟩
    have hk' : M - (n + 1) = k := by omega
    have hAn := hAm n hn.le
    have hokn := hokm n hn
    set f : Out → Ω → ℝ≥0∞ := fun o ω => (A n ∩ {ω | ok n ω}).indicator (fun ω =>
      ENNReal.ofReal (nextV EL hG (VE EL F hG k) ((List.ofFn fun j : Fin n => X j ω) ++ [o]) (Bsel n ω))) ω with hf
    have hpair : Measurable[m n] (fun ω => ((fun k : Fin n => X k ω), Bsel n ω)) := by
      letI := m n; exact (hvec n).prodMk (hBm n hn)
    have hfm : ∀ o, Measurable[m n] (f o) := fun o => by
      letI := m n
      exact ((measurable_of_countable (fun p : (Fin n → Out) × Fin K =>
        ENNReal.ofReal (nextV EL hG (VE EL F hG k) (List.ofFn p.1 ++ [o]) p.2))).comp hpair).indicator
        (hAn.inter hokn)
    have hf0 : ∀ o ω, ¬ ok n ω → f o ω = 0 := fun o ω hω => by
      simp only [hf, Set.indicator, Set.mem_inter_iff, Set.mem_setOf_eq]; rw [if_neg (fun h => hω h.2)]
    have hind : ∀ o, Measurable fun ω => (if X n ω = o then (1 : ℝ≥0∞) else 0) := fun o =>
      (measurable_of_countable (fun x : Out => if x = o then (1 : ℝ≥0∞) else 0)).comp (hXm n)
    have hnext : ∀ ω, (A (n + 1)).indicator (V (n + 1)) ω ≤ ∑ o, f o ω * (if X n ω = o then 1 else 0) := by
      intro ω
      have hsum : ∑ o, f o ω * (if X n ω = o then 1 else 0) = f (X n ω) ω := by
        simp only [mul_ite, mul_one, mul_zero, Finset.sum_ite_eq, Finset.mem_univ, ↓reduceIte]
      rw [hsum, hAsucc]
      by_cases hω : ω ∈ A n ∩ {ω | ok n ω}
      · rw [Set.indicator_of_mem hω]
        simp only [hf, Set.indicator_of_mem hω, hVdef]
        rw [hk', List.ofFn_succ_last]
        simp only [Fin.coe_castSucc, Fin.val_last]
        refine ENNReal.ofReal_le_ofReal ?_
        unfold nextV
        simp only [List.length_append, List.length_ofFn, List.length_singleton]
        split_ifs with hc
        · obtain ⟨b0, hb0⟩ := id hG
          cases k with
          | zero => exact Finset.le_sup' (fun b' => VE EL F hG 0 _ b') hb0
          | succ k =>
          by_cases hgood : Bsel (n + 1) ω ∈ goodB fam
          · exact Finset.le_sup' (fun b' => VE EL F hG (k + 1) _ b') hgood
          · have : VE EL F hG (k + 1) (List.ofFn (fun j : Fin n => X j ω) ++ [X n ω]) (Bsel (n + 1) ω) ≤ 0 := by
              rw [VE_bad hgood]
            exact le_trans this (le_trans (VE_nonneg hP hF0 (k + 1) _ b0)
              (Finset.le_sup' (fun b' => VE EL F hG (k + 1) _ b') hb0))
        · rw [hBc n ω (by omega)]
      · rw [Set.indicator_of_notMem hω]; positivity
    calc I (n + 1) ≤ ∫⁻ ω, ∑ o, f o ω * (if X n ω = o then 1 else 0) ∂μ := by
          simp only [hI]; exact lintegral_mono fun ω => hnext ω
      _ = ∑ o, ∫⁻ ω, f o ω * (if X n ω = o then 1 else 0) ∂μ :=
          lintegral_finsetSum _ fun o _ => ((hfm o).mono (hm n) le_rfl).mul (hind o)
      _ = ∑ o, ∫⁻ ω, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ :=
          Finset.sum_congr rfl fun o _ => hcond n hn (f o) (hfm o) (hf0 o) o
      _ = ∫⁻ ω, ∑ o, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ :=
          (lintegral_finsetSum _ fun o _ => (((hfm o).mul (hQm n hn o))).mono (hm n) le_rfl).symm
      _ ≤ I n := by
          simp only [hI]
          refine lintegral_mono fun ω => ?_
          by_cases hω : ω ∈ A n ∩ {ω | ok n ω}
          · obtain ⟨hq, ha0, ha⟩ := hQ n hn ω hω.2
            have ha1 : qa n ω ≤ 1 := le_trans ha (hP _).a1
            have hnn : ∀ o, 0 ≤ prodLaw (qh n ω) (qa n ω) o *
                nextV EL hG (VE EL F hG k) ((List.ofFn fun j : Fin n => X j ω) ++ [o]) (Bsel n ω) :=
              fun o => mul_nonneg (prodLaw_nonneg hq.1 ha0 ha1 o) (nextV_nonneg (VE_nonneg hP hF0 k) _ _)
            rw [Set.indicator_of_mem hω.1]
            calc ∑ o, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o)
                = ENNReal.ofReal (∑ o, prodLaw (qh n ω) (qa n ω) o *
                    nextV EL hG (VE EL F hG k) ((List.ofFn fun j : Fin n => X j ω) ++ [o]) (Bsel n ω)) := by
                  rw [ENNReal.ofReal_sum_of_nonneg fun o _ => hnn o]
                  refine Finset.sum_congr rfl fun o _ => ?_
                  show (A n ∩ {ω | ok n ω}).indicator _ ω * _ = _
                  rw [Set.indicator_of_mem hω, mul_comm, ENNReal.ofReal_mul (prodLaw_nonneg hq.1 ha0 ha1 o)]
              _ ≤ V n ω := by
                  simp only [hVdef]
                  rw [hk]
                  exact ENNReal.ofReal_le_ofReal (stepE_le hP hFm hq ha k _)
          · have : ∀ o, f o ω = 0 := fun o => by simp only [hf]; rw [Set.indicator_of_notMem hω]
            simp only [this, zero_mul, Finset.sum_const_zero]
            positivity
  have hchain : ∀ n ≤ M, I n ≤ I 0 := by
    intro n hn
    induction n with
    | zero => exact le_rfl
    | succ n ih => exact (hstep n (by omega)).trans (ih (by omega))
  have h0 : I 0 ≤ ENNReal.ofReal (Ex (worstKE EL F hG hP M) M F []) := by
    rw [worstKE_Ex hP M [] (by simp)]
    have hA0 : A 0 = Set.univ := by ext ω; simp [hAdef]
    simp only [hI, hA0, Set.indicator_univ, hVdef, Nat.sub_zero, List.ofFn_zero]
    calc ∫⁻ ω, ENNReal.ofReal (VE EL F hG M [] (Bsel 0 ω)) ∂μ
        ≤ ∫⁻ _, ENNReal.ofReal (VE EL F hG M [] (memE EL F hG M [])) ∂μ := by
          refine lintegral_mono fun ω => ENNReal.ofReal_le_ofReal ?_
          have hmem : memE EL F hG M [] = argB EL F hG M [] := by rw [memE]; simp
          rw [hmem, ← sup'_eq_argB]
          by_cases hg : Bsel 0 ω ∈ goodB fam
          · exact Finset.le_sup' (fun b => VE EL F hG M [] b) hg
          · obtain ⟨b0, hb0⟩ := id hG
            obtain ⟨M', rfl⟩ : ∃ M', M = M' + 1 := ⟨M - 1, by omega⟩
            rw [VE_bad hg]
            exact le_trans (VE_nonneg hP hF0 _ _ b0) (Finset.le_sup' (fun b => VE EL F hG (M' + 1) [] b) hb0)
      _ = _ := by rw [lintegral_const, measure_univ, mul_one]
  have hMeq : I M = μ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧ ∀ n < M, ok n ω} := by
    have hv : Measurable (fun ω (k : Fin M) => X k ω) := measurable_pi_iff.mpr fun k : Fin M => hXm k.val
    have hms1 : MeasurableSet {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} :=
      hv (Set.toFinite {v : Fin M → Out | List.ofFn v ∈ S}).measurableSet
    have hms : MeasurableSet {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧ ∀ n < M, ok n ω} :=
      hms1.inter ((hm M) _ (hAm M le_rfl))
    rw [← lintegral_indicator_one hms]
    have hV0 : ∀ l b, VE EL F hG 0 l b = F l := fun _ _ => rfl
    simp only [hI, hVdef, Nat.sub_self, hV0]
    refine lintegral_congr fun ω => ?_
    simp only [hFdef, Set.indicator, Set.mem_setOf_eq, Pi.one_apply, hAdef]
    split_ifs <;> simp_all
  rw [← hMeq]
  exact (hchain M le_rfl).trans h0

end Cryptarchia.Prob
