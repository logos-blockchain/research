import Cryptarchia.Prob.Tail

/-!
# Probabilistic finality

The lottery string of an execution, cut to its first `M` slots and with honest
leader counts capped at two, is a list of outcomes (`slots`). The good event
`GoodLS` and the growth condition `GrowthS` see the string only through that list
(`good_congr`). So if the law of the list is (at most) that of a kernel within a
band, the deterministic finality theorem `final_bimm_epochs` and the bound
`settle_bound` give probabilistic finality (`final_bimm_prob`).
-/

namespace Cryptarchia.Prob

open Finset Settle MeasureTheory

/-- A slot of a characteristic string as an outcome, capping honest leaders at two. -/
def enc (p : ℕ × Bool) : Out := ⟨if p.1 = 0 then 0 else if p.1 = 1 then 1 else 2, p.2⟩

/-- **The first `M` slots of a characteristic string.** -/
def slots (w : CStr) (M : ℕ) : List Out := (List.range M).map fun i => enc (w (i + 1))

theorem slots_length (w : CStr) (M : ℕ) : (slots w M).length = M := by simp [slots]

theorem sim_slots (w : CStr) (M : ℕ) : SimOn (strOf (slots w M)) w 0 M := by
  intro i h1 h2
  have hi : i - 1 < M := by omega
  have hs : strOf (slots w M) i = (enc (w i)).toPair := by
    unfold strOf slots
    rw [if_neg (by omega), List.getD_eq_getElem _ _ (by simpa using hi)]
    simp [show i - 1 + 1 = i by omega]
  rw [hs]
  unfold enc Out.toPair
  refine ⟨?_, ?_, rfl⟩ <;> split_ifs <;> simp_all <;> omega

variable {Δ M : ℕ}

/-- Strings that agree up to the horizon have the same phase ends. -/
theorem gend_congr_all {w w' : CStr} (h : SimOn w w' 0 M) : ∀ k, gend Δ M w k = gend Δ M w' k := by
  intro k
  induction k with
  | zero => rfl
  | succ k ih =>
    by_cases hk : gend Δ M w (k + 1) ≤ M
    · exact gend_congr (h.mono le_rfl le_rfl) (k + 1) hk
    · rw [gend_succ, gend_succ, ← ih]
      by_cases hm : gend Δ M w k < M
      · have := nextE_le (Δ := Δ) (w := w) hm
        rw [gend_succ] at hk; omega
      · push Not at hm
        rw [nextE_of_ge hm, nextE_of_ge hm]

/-- **The good event sees the string only up to the horizon.** -/
theorem good_congr (E : Env) (hΔ : E.Δ = Δ) (hsane : E.c.Sane) {w w' : CStr} (h : SimOn w w' 0 M)
    {N Lw r G : ℕ} (hNM : N + G < M)
    (hg : GoodLS E w N Lw (gend Δ M w) ∧ GrowthS E w (gend Δ M w) N r G) :
    GoodLS E w' N Lw (gend Δ M w') ∧ GrowthS E w' (gend Δ M w') N r G := by
  have he : gend Δ M w = gend Δ M w' := funext (gend_congr_all h)
  rw [← he]
  obtain ⟨⟨h0, hmono, hq, hunb, hcold, hwin⟩, hgr⟩ := hg
  refine ⟨⟨h0, hmono, ?_, hunb, ?_, ?_⟩, ?_⟩
  · intro k hk
    have := hq k hk
    rw [hΔ] at this ⊢
    exact (quiet_congr (h.mono (Nat.zero_le _) (by omega))).1 this
  · intro t k h1 h2 h3 h4
    have := hcold t k h1 h2 h3 h4
    have hk1 : gend Δ M w (k + 1) ≤ M := by
      rw [gend_succ]; exact nextE_le (by omega)
    rw [hΔ] at this ⊢
    rw [← bnd_congr gend_mono k (h.mono le_rfl (by have := gend_mono (Δ := Δ) (M := M) (w := w) k; omega)),
      ← advCnt_congr (h.mono (Nat.zero_le _) hk1)]
    exact this
  · intro t ht
    rw [← occCnt_congr (h.mono (Nat.zero_le _) (by omega))]
    exact hwin t ht
  · intro ep hep hfix
    obtain ⟨j, h1, h2, h3, h4⟩ := hgr ep hep hfix
    have hcf := (hsane.fix_ok ep hep).1
    refine ⟨j, h1, h2, ?_, ?_⟩
    · rw [hΔ] at h3 ⊢
      rw [← bnd_congr gend_mono j (h.mono le_rfl (by omega))]
      exact h3
    · rw [hΔ] at h4 ⊢
      rw [← hD_congr (h.mono (Nat.zero_le _) (by unfold Config.fix at hfix ⊢; omega))]
      exact h4

/-- The lottery string of an execution. -/
noncomputable abbrev lotStr (E : Env) (es : List Event) : CStr := lotStrS E (σE E es) (lateAt E es)

/-- **A finality violation**: a block an honest node had as `B_imm` is missing from
an honest node's chain at a later point where both are online. -/
def Unsafe (E : Env) (es : List Event) : Prop :=
  ∃ n n' i j, n ≤ n' ∧ n' ≤ es.length ∧ i ∈ E.nodes ∧ j ∈ E.nodes ∧
    E.online i (wAt E es n').now = true ∧ E.online j (wAt E es n').now = true ∧
    ((wAt E es n).node i).bimm ∉ chainIds (wAt E es n').st ((wAt E es n').node j).cloc

/-- The deterministic theorem, as a statement about `Unsafe`. -/
theorem not_unsafe (E : Env) {es : List Event} (hA : Assm E) {N Lw r G : ℕ} (hNF : (wF E es).now ≤ N)
    (hg : GoodLS E (lotStr E es) N Lw (gend E.Δ M (lotStr E es)) ∧
      GrowthS E (lotStr E es) (gend E.Δ M (lotStr E es)) N r G) :
    ¬ Unsafe E es := by
  rintro ⟨n, n', i, j, hnn, hn', hi, hj, hio, hjo, hb⟩
  exact hb (final_bimm_epochs hA hNF hg.1 hg.2 hnn hn' hi hj hio hjo)

/-- **Probabilistic finality.**

Let the adversary's strategy and the randomness be anything: a probability space `Ω`
and, for each outcome, an execution `es ω`, all of whose clocks stay below `N`. Let
the first `M` slots of the lottery string have the law of a kernel `κ` within the
band `B` (`hlaw`: for every event about those slots, its probability is at most the
kernel's). Then the probability of a finality violation is at most `settleEps`,
for any certificate `P` and any choice of the analysis parameters. -/
theorem final_bimm_prob {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω)
    (E : Env) (hA : Assm E) (es : Ω → List Event) {N M : ℕ} (hNF : ∀ ω, (wF E (es ω)).now ≤ N)
    {κ : Kern} {B : Band} (hB : κ.Within B)
    (hlaw : ∀ S : Set (List Out), μ {ω | slots (lotStr E (es ω)) M ∈ S} ≤
      ENNReal.ofReal (Ex κ M (S.indicator 1) []))
    {Δ : ℕ} (hΔ : E.Δ = Δ) (P : ColdCert B Δ) {W G Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + Δ + 2 ≤ M) (hW : W + 2 * G ≤ Lw) (hGL : G ≤ Lw)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (helo1 : B.elo ≤ 1) :
    μ {ω | Unsafe E (es ω)} ≤ ENNReal.ofReal (settleEps E B P N W G Lw r T x yy) := by
  classical
  subst hΔ
  set Bad : Set (List Out) := {l | ¬ (GoodLS E (strOf l) N Lw (gend E.Δ M (strOf l)) ∧
    GrowthS E (strOf l) (gend E.Δ M (strOf l)) N r G)} with hBad
  have hsub : {ω | Unsafe E (es ω)} ⊆ {ω | slots (lotStr E (es ω)) M ∈ Bad} := by
    intro ω hω
    simp only [Set.mem_setOf_eq, hBad, not_not] at hω ⊢
    intro hg
    exact not_unsafe E hA (M := M) (hNF ω)
      (good_congr E rfl hA.sane (sim_slots (lotStr E (es ω)) M) (by omega) hg) hω
  refine (measure_mono hsub).trans ((hlaw Bad).trans (ENNReal.ofReal_le_ofReal ?_))
  refine le_trans ?_ (settle_bound E rfl hA.sane hB P hx hyy0 hyy1 hT hNM hW hGL hhi1 hlo0 helo1)
  apply Ex_mono_len
  intro t ht
  simp only [List.nil_append, Set.indicator, hBad, Set.mem_setOf_eq, Pi.one_apply]
  split_ifs <;> simp_all

end Cryptarchia.Prob
