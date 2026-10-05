import Cryptarchia.Prob.Final2E
import Cryptarchia.Prob.Tail3E

/-!
# Probabilistic finality over many epochs, with an in-epoch contraction

`Cert3E` adds to a `Cert2E` an in-epoch contraction `lpi`: for each member, phase bounds
`ei k` from its own tables (`vpost`, no switch) and a crossing bound `pat0 k` from its own
band, meeting the class conditions with `lpi`. Phases that start more than `G` slots before an epoch boundary use them; the
others pay `(lp / lpi)` each, at most `G` times per check window (`swCnt_noSw_le`,
for `Lw + G < EL`). `final_bimm_ro_epoch3_ok` is `final_bimm_ro_epoch_ok` with the
failed-checks term `lpi^J · (lp/lpi)^G · e₂ · stat`.
-/

namespace Cryptarchia.Prob

open Finset Settle MeasureTheory

variable {B : Band} {Δ M : ℕ} {κ : Kern}

/-- **A certificate with an in-epoch contraction.** -/
structure Cert3E (B : Band) (Δ : ℕ) {K : ℕ} (fam : Fin K → Band) (EL G : ℕ) where
  C : Cert2E B Δ fam EL G
  lpi : ℝ
  ei : Fin K → Fin 19 → ℝ
  pat0 : Fin K → ℝ
  hcl : ∀ k, ClassOK C.P lpi (ei k) (pat0 k)
  hlpi0 : 0 < lpi
  hlpi : lpi ≤ C.P.lp
  hpat : ∀ k, pat0 k ≤ (fam k).slo * (fam k).elo ^ Δ
  helo : ∀ k, 0 ≤ (fam k).elo
  heIn : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ k, autoBound (fam k) (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).1
    (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).2.1 (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).2.2 (C.vpost i k) ≤ ei k i

/-- **At most `G` switching slots in a window** of `L` slots, if `L + G < EL`: they lie
within `G` slots before the window's only boundary. -/
theorem swCnt_noSw_le {EL G L : ℕ} (hEL : 0 < EL) (hL : L + G < EL) (t : ℕ) :
    swCnt (fun s => ¬ NoSw EL G s) t (t + L) ≤ G := by
  classical
  unfold swCnt
  have key : ∀ a b, (a + 1) % EL = 0 → (b + 1) % EL = 0 → a < b → EL ≤ b - a := by
    intro a b ha hb hab
    have h3 : EL ∣ (b + 1) - (a + 1) := Nat.dvd_sub (Nat.dvd_of_mod_eq_zero hb) (Nat.dvd_of_mod_eq_zero ha)
    rw [show (b + 1) - (a + 1) = b - a by omega] at h3
    exact Nat.le_of_dvd (by omega) h3
  by_cases hex : ∃ s, t ≤ s ∧ s < t + L ∧ ¬ NoSw EL G s
  · obtain ⟨s0, hs0a, hs0b, hn0⟩ := hex
    unfold NoSw at hn0; push Not at hn0
    obtain ⟨j0, hj0a, hj0b, hj0c⟩ := hn0
    refine le_trans (Finset.card_le_card (t := Finset.Ico (j0 - G) j0) ?_) (by rw [Nat.card_Ico]; omega)
    intro s hs
    simp only [Finset.mem_filter, Finset.mem_Ico] at hs
    obtain ⟨⟨hsa, hsb⟩, hn⟩ := hs
    unfold NoSw at hn; push Not at hn
    obtain ⟨j, hja, hjb, hjc⟩ := hn
    have hjj : j = j0 := by
      rcases lt_trichotomy j j0 with h | h | h
      · have := key j j0 hjc hj0c h; omega
      · exact h
      · have := key j0 j hj0c hjc h; omega
    subst hjj
    rw [Finset.mem_Ico]; omega
  · refine le_trans (Finset.card_le_card (t := ∅) ?_) (by simp)
    intro s hs
    simp only [Finset.mem_filter, Finset.mem_Ico] at hs
    exact absurd ⟨s, hs.1.1, hs.1.2, hs.2⟩ hex

section Derive

variable {K EL G : ℕ} {fam : Fin K → Band} (D : Cert3E B Δ fam EL G) (hκ : κ.EpochFam EL fam)
include D hκ

/-- **A phase inside an epoch**: the starting member's class conditions, crossing bound
and own-table phase bounds. -/
theorem Cert3E.inEpoch : ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M → ¬ ¬ NoSw EL G h.length →
    ∃ (e : Fin 19 → ℝ) (pat : ℝ), ClassOK D.C.P D.lpi e pat ∧
      pat ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG 1 h.length)) h ∧
      ∀ i : Fin 19, i ≠ 2 → i ≠ 17 →
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP D.C.P i h.length)) h ≤ e i := by
  intro h hpe hlM hnb
  obtain ⟨mem, hband, hmem⟩ := hκ
  have hG1 : 1 ≤ G := by have := D.C.hG; have := D.C.P.hΔ; omega
  refine ⟨D.ei (mem h), D.pat0 (mem h), D.hcl (mem h),
    ex_cross_truncIn mem hband hmem (D.hpat (mem h)) D.helo D.C.P.hΔ hlM D.C.hG (not_not.1 hnb), fun i h2 h17 => ?_⟩
  have hx := xg_nonneg D.C.P i
  exact phase_autoIn (D.C.solE i h2 h17).post (xg_g_nonneg D.C.P i) mem hband hmem hx.1 hx.2 hG1
    (D.heIn i h2 h17 (mem h)) D.C.P.hΔ (start_of_pe hpe (by omega)) (by omega) (not_not.1 hnb)

end Derive

/-- **Probabilistic finality over many epochs, from a random oracle, with the band
condition only where it holds.** A finality violation has probability at most
`settleEps2E` plus the probability that some slot's epoch state is outside the band
of its member. The second term is where the stake estimate's concentration enters. -/
theorem final_bimm_ro_epoch3_ok {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {O : Ω → Oracle} {E : Env} (hA : Assm E) (es : Ω → List Event) {N M : ℕ}
    (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {Δ K G : ℕ} {fam : Fin K → Band} (hΔ : E.Δ = Δ) (D : Cert3E B Δ fam E.c.epochLength G)
    (hP : ∀ k, (fam k).Prod) (pick : EpochState → Fin K)
    {G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + G' + Δ + 2 ≤ M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1)
    (hLw : Lw + G < E.c.epochLength) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤
      ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) +
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
    have hEL : 0 < E.c.epochLength := by omega
    refine le_trans ?_ (settle_bound3E E rfl hA.sane D.C.P (D.C.within hκ) D.C.hG
      (D.C.anyPhase hκ 0 (by decide) D.C.heS0) (D.C.anyPhase hκ 1 (by decide) D.C.heS1)
      (D.C.anyPhase hκ 2 (by decide) D.C.heS2) (D.C.anyPhase hκ 17 (by decide) D.C.heS17) (D.C.truncPhase hκ)
      D.hlpi0 D.hlpi (fun t => ¬ NoSw E.c.epochLength G t) (swCnt_noSw_le hEL hLw) (D.inEpoch hκ) hx hyy0 hyy1 hT hNM hhi1 hlo0 hlo1 helo1)
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
