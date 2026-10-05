import Cryptarchia.Prob.WorstE
import Cryptarchia.Prob.RO

/-!
# The lottery law over many epochs

Under a random oracle, fresh lotteries and Δ-delivery (`Prob/RO.lean`), suppose every
epoch state a slot can run under is within the band of a member of a family, chosen
by a fixed rule from the state (`pick`). A slot's epoch state depends only on its
epoch (`σE`), so the member is the same for all slots of an epoch and known before
each of them. `lottery_law_epoch` then bounds every event about the lottery string
that is closed under adding adversarial slots by a kernel that keeps one member per
epoch (`Kern.EpochFam`).
-/

namespace Cryptarchia.Prob

open MeasureTheory ProbabilityTheory Finset Settle
open scoped ENNReal

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
  {E : Env}

/-- Consecutive slots of one epoch run under the same epoch state. -/
theorem σE_succ (E : Env) (es : List Event) {n : ℕ} (h : (n + 2) % E.c.epochLength ≠ 0) :
    σE E es (n + 2) = σE E es (n + 1) := by
  unfold σE Config.epochOf
  congr 1
  rw [show n + 2 = (n + 1) + 1 by omega, Nat.succ_div, if_neg (fun hd => h (Nat.mod_eq_zero_of_dvd hd)), add_zero]

/-- **The lottery law over many epochs, from a random oracle.** If each slot's epoch
state is within the band of the member `pick` assigns to it, every event about the
first `M` slots that is closed under adding adversarial slots is at most as likely as
under a kernel with one member per epoch. -/
theorem lottery_law_epoch (hA : Assm E) (es : Ω → List Event) {M : ℕ} (hM : 0 < M)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {K : ℕ} {fam : Fin K → Band} (hP : ∀ b, (fam b).Prod) (pick : EpochState → Fin K)
    (hband : ∀ ω i, 1 ≤ i → i ≤ M →
      SlotBand (fam (pick (σE (E.withO (O ω)) (es ω) i))) E i (σE (E.withO (O ω)) (es ω) i))
    {S : Set (List Out)} (hS : UpClosed S) :
    ∃ κ : Kern, κ.EpochFam E.c.epochLength fam ∧
      μ {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S} ≤ ENNReal.ofReal (Ex κ M (S.indicator 1) []) := by
  classical
  set σ : Ω → ℕ → EpochState := fun ω => σE (E.withO (O ω)) (es ω) with hσ
  set X : ℕ → Ω → Out := fun k ω => slotOut E (k + 1) (σ ω (k + 1)) (tk O (k + 1) ω) with hX
  have hslots : ∀ ω, slots (lotStr (E.withO (O ω)) (es ω)) M = List.ofFn (fun k : Fin M => X k ω) := by
    intro ω
    apply List.ext_getElem (by simp [slots_length])
    intro k h1 h2
    rw [slots_get, List.getElem_ofFn]
    exact enc_lotStr (hdel ω) (k + 1)
  have hm : ∀ n, hist O σ n ≤ ‹MeasurableSpace Ω› := fun n =>
    sup_le (iSup₂_le fun j _ => (hO.meas j).comap_le) (iSup₂_le fun j _ => (hσm j).comap_le)
  have hTh : ∀ n j, j < n → Measurable[hist O σ n] (tk O j) := fun n j hj =>
    (comap_measurable (tk O j)).mono (le_sup_of_le_left (le_iSup₂_of_le j (Finset.mem_range.2 hj) le_rfl)) le_rfl
  have hσh : ∀ n j, j ≤ n → Measurable[hist O σ n] (fun ω => σ ω j) := fun n j hj =>
    (comap_measurable (fun ω => σ ω j)).mono
      (le_sup_of_le_right (le_iSup₂_of_le j (Finset.mem_range.2 (by omega)) le_rfl)) le_rfl
  have hXm : ∀ j, Measurable (X j) := fun j =>
    (measurable_slotOut₂ E (j + 1)).comp ((hO.meas (j + 1)).prodMk (hσm (j + 1)))
  have hXh : ∀ n j, j < n → Measurable[hist O σ (n + 1)] (X j) := fun n j hj =>
    (measurable_slotOut₂ E (j + 1)).comp ((hTh (n + 1) (j + 1) (by omega)).prodMk (hσh (n + 1) (j + 1) (by omega)))
  rw [show {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S} = {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} by
    ext ω; rw [Set.mem_setOf_eq, Set.mem_setOf_eq, hslots ω]]
  exact law_le_epoch μ hP hM X hXm (fun n => hist O σ (n + 1)) (fun n => hm _) hXh
    (fun n ω => qhRO E (n + 1) (σ ω (n + 1))) (fun n ω => qaRO E.c (σ ω (n + 1)))
    (fun n ω => pick (σ ω (n + 1)))
    (fun n hn ω => by
      have hb := hband ω (n + 1) (by omega) (by omega)
      exact ⟨hb.hon, by unfold qaRO; linarith [loss_le_one hO.pos (σ ω (n + 1)) (advNotes (σ ω (n + 1)))], hb.adv⟩)
    (fun n _ => (measurable_of_countable pick).comp (hσh (n + 1) (n + 1) le_rfl))
    (fun n ω hc => by
      show pick (σE (E.withO (O ω)) (es ω) (n + 2)) = pick (σE (E.withO (O ω)) (es ω) (n + 1))
      rw [σE_succ (E.withO (O ω)) (es ω) hc])
    (fun n _ o => (measurable_of_countable fun s : EpochState =>
      ENNReal.ofReal (prodLaw (qhRO E (n + 1) s) (qaRO E.c s) o)).comp (hσh (n + 1) (n + 1) le_rfl))
    (fun n hn f hf o => by
      have h := freeze (m := hist O σ (n + 1)) (μ := μ) (hm _) (hσh (n + 1) (n + 1) le_rfl) (hO.meas (n + 1))
        (hfresh (n + 1)) (g := fun s T => slotOut E (n + 1) s T) (fun s => measurable_slotOut E (n + 1) s) o hf
      refine h.trans (lintegral_congr fun ω => ?_)
      rw [slot_law hO hA.nodup (n + 1) (σ ω (n + 1)) (hband ω (n + 1) (by omega) (by omega)).nodup o])
    hS

theorem hist_mono (O : Ω → Oracle) (σ : Ω → ℕ → EpochState) {j n : ℕ} (h : j ≤ n) : hist O σ j ≤ hist O σ n :=
  sup_le_sup (iSup₂_le fun i hi => le_iSup₂_of_le i (Finset.mem_range.2 (by have := Finset.mem_range.1 hi; omega)) le_rfl)
    (iSup₂_le fun i hi => le_iSup₂_of_le i (Finset.mem_range.2 (by have := Finset.mem_range.1 hi; omega)) le_rfl)

open Classical in
/-- **The lottery law over many epochs, while in band.** As `lottery_law_epoch`, with the
band condition only where it holds: the event, intersected with "every slot's epoch
state is within its member's band", is at most as likely as under a kernel with one
member per epoch. -/
theorem lottery_law_epoch_ok (hA : Assm E) (es : Ω → List Event) {M : ℕ} (hM : 0 < M)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {K : ℕ} {fam : Fin K → Band} (hP : ∀ b, (fam b).Prod) (pick : EpochState → Fin K)
    (hG : (goodB fam).Nonempty) {S : Set (List Out)} (hS : UpClosed S) :
    ∃ κ : Kern, κ.EpochFam E.c.epochLength fam ∧
      μ {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S ∧ ∀ n < M,
        SlotBand (fam (pick (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1))} ≤
        ENNReal.ofReal (Ex κ M (S.indicator 1) []) := by
  set σ : Ω → ℕ → EpochState := fun ω => σE (E.withO (O ω)) (es ω) with hσ
  set X : ℕ → Ω → Out := fun k ω => slotOut E (k + 1) (σ ω (k + 1)) (tk O (k + 1) ω) with hX
  have hslots : ∀ ω, slots (lotStr (E.withO (O ω)) (es ω)) M = List.ofFn (fun k : Fin M => X k ω) := by
    intro ω
    apply List.ext_getElem (by simp [slots_length])
    intro k h1 h2
    rw [slots_get, List.getElem_ofFn]
    exact enc_lotStr (hdel ω) (k + 1)
  have hm : ∀ n, hist O σ n ≤ ‹MeasurableSpace Ω› := fun n =>
    sup_le (iSup₂_le fun j _ => (hO.meas j).comap_le) (iSup₂_le fun j _ => (hσm j).comap_le)
  have hTh : ∀ n j, j < n → Measurable[hist O σ n] (tk O j) := fun n j hj =>
    (comap_measurable (tk O j)).mono (le_sup_of_le_left (le_iSup₂_of_le j (Finset.mem_range.2 hj) le_rfl)) le_rfl
  have hσh : ∀ n j, j ≤ n → Measurable[hist O σ n] (fun ω => σ ω j) := fun n j hj =>
    (comap_measurable (fun ω => σ ω j)).mono
      (le_sup_of_le_right (le_iSup₂_of_le j (Finset.mem_range.2 (by omega)) le_rfl)) le_rfl
  have hXm : ∀ j, Measurable (X j) := fun j =>
    (measurable_slotOut₂ E (j + 1)).comp ((hO.meas (j + 1)).prodMk (hσm (j + 1)))
  have hXh : ∀ n j, j < n → Measurable[hist O σ (n + 1)] (X j) := fun n j hj =>
    (measurable_slotOut₂ E (j + 1)).comp ((hTh (n + 1) (j + 1) (by omega)).prodMk (hσh (n + 1) (j + 1) (by omega)))
  set ok : ℕ → Ω → Prop := fun n ω => SlotBand (fam (pick (σ ω (n + 1)))) E (n + 1) (σ ω (n + 1)) with hok
  rw [show {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S ∧ ∀ n < M,
      SlotBand (fam (pick (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1))} =
      {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧ ∀ n < M, ok n ω} by
    ext ω; rw [Set.mem_setOf_eq, Set.mem_setOf_eq, hslots ω]]
  exact law_le_epoch_ok μ hP hM X hXm (fun n => hist O σ (n + 1)) (fun n => hm _)
    (fun j n hjn => hist_mono O σ (by omega)) hXh
    (fun n ω => qhRO E (n + 1) (σ ω (n + 1))) (fun n ω => qaRO E.c (σ ω (n + 1)))
    (fun n ω => pick (σ ω (n + 1))) ok
    (fun n _ => (hσh (n + 1) (n + 1) le_rfl) (MeasurableSet.of_discrete
      (s := {s : EpochState | SlotBand (fam (pick s)) E (n + 1) s})))
    (fun n hn ω hb => ⟨hb.hon, by unfold qaRO; linarith [loss_le_one hO.pos (σ ω (n + 1)) (advNotes (σ ω (n + 1)))],
        hb.adv⟩)
    (fun n _ => (measurable_of_countable pick).comp (hσh (n + 1) (n + 1) le_rfl))
    (fun n ω hc => by
      show pick (σE (E.withO (O ω)) (es ω) (n + 2)) = pick (σE (E.withO (O ω)) (es ω) (n + 1))
      rw [σE_succ (E.withO (O ω)) (es ω) hc])
    (fun n _ o => (measurable_of_countable fun s : EpochState =>
      ENNReal.ofReal (prodLaw (qhRO E (n + 1) s) (qaRO E.c s) o)).comp (hσh (n + 1) (n + 1) le_rfl))
    (fun n hn f hf hf0 o => by
      have h := freeze (m := hist O σ (n + 1)) (μ := μ) (hm _) (hσh (n + 1) (n + 1) le_rfl) (hO.meas (n + 1))
        (hfresh (n + 1)) (g := fun s T => slotOut E (n + 1) s T) (fun s => measurable_slotOut E (n + 1) s) o hf
      refine h.trans (lintegral_congr fun ω => ?_)
      by_cases hω : ok n ω
      · rw [slot_law hO hA.nodup (n + 1) (σ ω (n + 1)) hω.nodup o]
      · rw [hf0 ω hω, zero_mul, zero_mul])
    hS hG

end Cryptarchia.Prob
