import Cryptarchia.Prob.Tail2E
import Cryptarchia.Prob.ROEpoch

/-!
# Probabilistic finality over many epochs

`final_bimm_ro_epoch`: under a random oracle, fresh lotteries and Δ-delivery, if every
epoch state is within the band of a member of a family (`pick`), a finality
violation has probability at most `settleEps2E`, for any certificate `Cert2E` of the
family. The member may differ from epoch to epoch.

`Cert2E` holds a potential certificate `P` (its constants and class conditions,
with `P.e i` the bounds for phases cut at `G` slots and `P.lr`, `P.b`, `P.e 2`,
`P.e 17` bounds for any phase), automaton solutions that switch member at any slot
for the reach, the checked phase and spans (`vs`), and one-switch automaton
solutions for the contraction (`vpre`, `vpost`, `vmax`).
-/

namespace Cryptarchia.Prob

open Finset Settle MeasureTheory

/-- **A certificate for a family of bands with one member per epoch.** -/
structure Cert2E (B : Band) (Δ : ℕ) {K : ℕ} (fam : Fin K → Band) (EL G : ℕ) where
  P : Cert2 B Δ
  weakF : ∀ k, B.Weaker (fam k)
  hG : Δ + 1 ≤ G
  hGEL : G + 1 < EL
  /-- tables for phases of any length, switching member at any slot -/
  vs : Fin 19 → ℕ → Fin 3 → Bool → ℝ
  solS : ∀ i : Fin 19, (i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 17) → ∀ k,
    AutoSol (fam k) Δ (xg P.c P.z P.s P.d P.τ i).1 (xg P.c P.z P.s P.d P.τ i).2.1 (xg P.c P.z P.s P.d P.τ i).2.2 (vs i)
  heS0 : ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ 0).1 (xg P.c P.z P.s P.d P.τ 0).2.1
    (xg P.c P.z P.s P.d P.τ 0).2.2 (vs 0) ≤ P.lr
  heS1 : ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ 1).1 (xg P.c P.z P.s P.d P.τ 1).2.1
    (xg P.c P.z P.s P.d P.τ 1).2.2 (vs 1) ≤ P.b
  heS2 : ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ 2).1 (xg P.c P.z P.s P.d P.τ 2).2.1
    (xg P.c P.z P.s P.d P.τ 2).2.2 (vs 2) ≤ P.e 2
  heS17 : ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ 17).1 (xg P.c P.z P.s P.d P.τ 17).2.1
    (xg P.c P.z P.s P.d P.τ 17).2.2 (vs 17) ≤ P.e 17
  /-- one-switch tables for phases cut at `G` slots -/
  vpre : Fin 19 → Fin K → ℕ → Fin 3 → Bool → ℝ
  vpost : Fin 19 → Fin K → ℕ → Fin 3 → Bool → ℝ
  vmax : Fin 19 → ℕ → Fin 3 → Bool → ℝ
  solE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → AutoSolE fam Δ (xg P.c P.z P.s P.d P.τ i).1 (xg P.c P.z P.s P.d P.τ i).2.1
    (xg P.c P.z P.s P.d P.τ i).2.2 (vpre i) (vpost i) (vmax i)
  heE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ i).1
    (xg P.c P.z P.s P.d P.τ i).2.1 (xg P.c P.z P.s P.d P.τ i).2.2 (vpre i k) ≤ P.e i

variable {B : Band} {Δ M : ℕ} {κ : Kern}

theorem xg_g_nonneg (P : Cert2 B Δ) (i : Fin 19) (a : Fin 3) (b u : Bool) :
    0 ≤ (xg P.c P.z P.s P.d P.τ i).2.2 a b u := by
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have hs0 : 0 < P.s := by linarith [P.hs]
  have hd0 : 0 < P.d := P.hd0
  fin_cases i <;> simp only [xg, xgN, gtab] <;> first | positivity | (split_ifs <;> positivity)

section Derive

variable {K EL G : ℕ} {fam : Fin K → Band} (C : Cert2E B Δ fam EL G) (hκ : κ.EpochFam EL fam)
include C hκ

theorem Cert2E.within : κ.Within B :=
  hκ.fam.within fun B' hB' => by
    obtain ⟨k, rfl⟩ := List.mem_ofFn.1 hB'
    exact C.weakF k

theorem Cert2E.anyPhase (i : Fin 19) (hi : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 17) {e : ℝ}
    (he : ∀ k, autoBound (fam k) (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).1 (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).2.1
      (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).2.2 (C.vs i) ≤ e) :
    ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP C.P i h.length) h ≤ e := by
  intro h hpe hlM
  have hx := xg_nonneg C.P i
  exact phase_auto hκ.fam hx.1 hx.2 (fun B' hB' => by obtain ⟨k, rfl⟩ := List.mem_ofFn.1 hB'; exact C.solS i hi k)
    (fun B' hB' => by obtain ⟨k, rfl⟩ := List.mem_ofFn.1 hB'; exact he k) C.P.hΔ (start_of_pe hpe hlM) hlM

theorem Cert2E.truncPhase : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ h, PE Δ M h → h.length < M →
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP C.P i h.length)) h ≤ C.P.e i := by
  intro i h2 h17 h hpe hlM
  obtain ⟨mem, hband, hmem⟩ := hκ
  have hx := xg_nonneg C.P i
  have hEL : 0 < EL := by have := C.hGEL; omega
  have hG1 : 1 ≤ G := by have := C.hG; omega
  exact phase_autoE (C.solE i h2 h17) (xg_g_nonneg C.P i) mem hband hmem hx.1 hx.2 hEL C.hGEL hG1
    (C.heE i h2 h17) C.P.hΔ (start_of_pe hpe hlM) hlM

end Derive

/-- **Probabilistic finality over many epochs, from a random oracle.** -/
theorem final_bimm_ro_epoch {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {O : Ω → Oracle} {E : Env} (hA : Assm E) (es : Ω → List Event) {N M : ℕ}
    (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {Δ K G : ℕ} {fam : Fin K → Band} (hΔ : E.Δ = Δ) (C : Cert2E B Δ fam E.c.epochLength G)
    (hP : ∀ k, (fam k).Prod) (pick : EpochState → Fin K)
    (hband : ∀ ω i, 1 ≤ i → i ≤ M →
      SlotBand (fam (pick (σE (E.withO (O ω)) (es ω) i))) E i (σE (E.withO (O ω)) (es ω) i))
    {G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + G' + Δ + 2 ≤ M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps2E E B C.P N G G' J Lw r T x yy) := by
  classical
  subst hΔ
  set Bad : Set (List Out) := {l | ¬ (GoodLS E (strOf l) N Lw (gend E.Δ M (strOf l)) ∧
    GrowthS E (strOf l) (gend E.Δ M (strOf l)) N r G)} with hBad
  set S : Set (List Out) := {l | ∀ l', List.Forall₂ OutLe l l' → l' ∈ Bad} with hSdef
  have hS : UpClosed S := fun l l2 h hl l' h' => hl l' (forall₂_trans h h')
  have hsub : {ω | Unsafe (E.withO (O ω)) (es ω)} ⊆ {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S} := by
    intro ω hU
    simp only [Set.mem_setOf_eq, hSdef]
    intro l' hl'
    simp only [hBad, Set.mem_setOf_eq]
    intro hg
    exact unsafe_up (E.withO (O ω)) (hA.withO (O ω)) (Lw := Lw) (r := r) (G := G) (hNF ω) (by omega) hU hl'
      ⟨goodLS_withO hg.1, hg.2⟩
  obtain ⟨κ, hκ, hbound⟩ := lottery_law_epoch hA es (by omega) hdel hO hσm hfresh hP pick hband hS
  refine (measure_mono hsub).trans (hbound.trans (ENNReal.ofReal_le_ofReal ?_))
  refine le_trans ?_ (settle_bound2E E rfl hA.sane C.P (C.within hκ) C.hG
    (C.anyPhase hκ 0 (by decide) C.heS0) (C.anyPhase hκ 1 (by decide) C.heS1)
    (C.anyPhase hκ 2 (by decide) C.heS2) (C.anyPhase hκ 17 (by decide) C.heS17) (C.truncPhase hκ)
    hx hyy0 hyy1 hT hNM hhi1 hlo0 hlo1 helo1)
  apply Ex_mono_len
  intro t _
  simp only [List.nil_append]
  by_cases ht : t ∈ S
  · have hb : t ∈ Bad := ht t (forall₂_refl t)
    rw [Set.indicator_of_mem ht]
    simp only [hBad, Set.mem_setOf_eq] at hb
    rw [if_neg hb]; rfl
  · rw [Set.indicator_of_notMem ht]
    split_ifs <;> norm_num

/-- **Probabilistic finality over many epochs, from a random oracle, with the band
condition only where it holds.** A finality violation has probability at most
`settleEps2E` plus the probability that some slot's epoch state is outside the band
of its member. The second term is where the stake estimate's concentration enters. -/
theorem final_bimm_ro_epoch_ok {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {O : Ω → Oracle} {E : Env} (hA : Assm E) (es : Ω → List Event) {N M : ℕ}
    (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {Δ K G : ℕ} {fam : Fin K → Band} (hΔ : E.Δ = Δ) (C : Cert2E B Δ fam E.c.epochLength G)
    (hP : ∀ k, (fam k).Prod) (pick : EpochState → Fin K)
    {G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + G' + Δ + 2 ≤ M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps2E E B C.P N G G' J Lw r T x yy) +
      μ {ω | ∃ n < M, ¬ SlotBand (fam (pick (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
        (σE (E.withO (O ω)) (es ω) (n + 1))} := by
  classical
  subst hΔ
  set okAll : Set Ω := {ω | ∀ n < M, SlotBand (fam (pick (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
    (σE (E.withO (O ω)) (es ω) (n + 1))} with hokAll
  have hcompl : {ω | ∃ n < M, ¬ SlotBand (fam (pick (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
      (σE (E.withO (O ω)) (es ω) (n + 1))} = okAllᶜ := by
    ext ω; simp [hokAll]
  rw [hcompl]
  by_cases hG : (goodB fam).Nonempty
  · set Bad : Set (List Out) := {l | ¬ (GoodLS E (strOf l) N Lw (gend E.Δ M (strOf l)) ∧
      GrowthS E (strOf l) (gend E.Δ M (strOf l)) N r G)} with hBad
    set S : Set (List Out) := {l | ∀ l', List.Forall₂ OutLe l l' → l' ∈ Bad} with hSdef
    have hS : UpClosed S := fun l l2 h hl l' h' => hl l' (forall₂_trans h h')
    have hsub : {ω | Unsafe (E.withO (O ω)) (es ω)} ⊆
        {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S ∧ ω ∈ okAll} ∪ okAllᶜ := by
      intro ω hU
      by_cases hω : ω ∈ okAll
      · refine Or.inl ⟨?_, hω⟩
        simp only [Set.mem_setOf_eq, hSdef]
        intro l' hl'
        simp only [hBad, Set.mem_setOf_eq]
        intro hg
        exact unsafe_up (E.withO (O ω)) (hA.withO (O ω)) (Lw := Lw) (r := r) (G := G) (hNF ω) (by omega) hU hl'
          ⟨goodLS_withO hg.1, hg.2⟩
      · exact Or.inr hω
    obtain ⟨κ, hκ, hbound⟩ := lottery_law_epoch_ok (M := M) hA es (by omega) hdel hO hσm hfresh hP pick hG hS
    refine (measure_mono hsub).trans ((measure_union_le _ _).trans (add_le_add ?_ le_rfl))
    refine hbound.trans (ENNReal.ofReal_le_ofReal ?_)
    refine le_trans ?_ (settle_bound2E E rfl hA.sane C.P (C.within hκ) C.hG
      (C.anyPhase hκ 0 (by decide) C.heS0) (C.anyPhase hκ 1 (by decide) C.heS1)
      (C.anyPhase hκ 2 (by decide) C.heS2) (C.anyPhase hκ 17 (by decide) C.heS17) (C.truncPhase hκ)
      hx hyy0 hyy1 hT hNM hhi1 hlo0 hlo1 helo1)
    apply Ex_mono_len
    intro t _
    simp only [List.nil_append]
    by_cases ht : t ∈ S
    · have hb : t ∈ Bad := ht t (forall₂_refl t)
      rw [Set.indicator_of_mem ht]
      simp only [hBad, Set.mem_setOf_eq] at hb
      rw [if_neg hb]; rfl
    · rw [Set.indicator_of_notMem ht]
      split_ifs <;> norm_num
  · -- no member has a nonempty polytope: no epoch state is in band
    have hempty : okAll = ∅ := by
      ext ω
      simp only [hokAll, Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false]
      intro h
      exact hG ⟨_, mem_goodB.2 ⟨_, (h 0 (by omega)).hon⟩⟩
    have : {ω | Unsafe (E.withO (O ω)) (es ω)} ⊆ okAllᶜ := by
      rw [hempty, Set.compl_empty]; exact Set.subset_univ _
    exact (measure_mono this).trans le_add_self

end Cryptarchia.Prob
