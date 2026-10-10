module

public import Cryptarchia.Prob.Final3E
import Cryptarchia.Prob.ROEpoch
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.NNRat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.Height.NumberField
import Mathlib.NumberTheory.Height.Projectivization
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.SelbergSieve
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.Tactic.Echelon.Zsqrtd
import Mathlib.Tactic.NormNum.Irrational
import Mathlib.Tactic.NormNum.IsCoprime
import Mathlib.Tactic.NormNum.IsSquare
import Mathlib.Tactic.NormNum.LegendreSymbol
import Mathlib.Tactic.NormNum.ModEq
import Mathlib.Tactic.NormNum.NatFib
import Mathlib.Tactic.NormNum.NatLog
import Mathlib.Tactic.NormNum.NatSqrt
import Mathlib.Tactic.NormNum.Ordinal
import Mathlib.Tactic.NormNum.Parity
import Mathlib.Tactic.NormNum.Prime
import Mathlib.Tactic.NormNum.RealSqrt
import Mathlib.Topology.Sheaves.Init
import Cryptarchia.Prob.Trunc
import Cryptarchia.Proof.Consist

/-!
# The epoch induction

The canonical prefixes are consistent at epoch `e` on the lottery's good event up to
`N_e = min (fix (e + 1)) N`, cut at `N_e + 1`, which is determined by epoch `e`'s and
earlier slots. Its failure while those epochs are in band is at most
`settleEps3E` at horizon `N_e` (`prob_split_epoch`): the kernel bound is taken at the
larger cap and the event marginalized to the first `N_e + 1` slots (`Ex_add_len`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory Settle
open scoped ENNReal

section Kernel

variable (κ : Kern)

/-- **Expectations compose**: `m + n` slots are `m` slots, then `n`. -/
theorem Ex_add_len : ∀ (m n : ℕ) (F : List Out → ℝ) (l : List Out),
    Ex κ (m + n) F l = Ex κ m (fun x => Ex κ n F x) l
  | 0, n, F, l => by rw [Nat.zero_add]; rfl
  | m + 1, n, F, l => by
    rw [show m + 1 + n = (m + n) + 1 by omega, Ex_succ, Ex_succ]
    exact Finset.sum_congr rfl fun o _ => by rw [Ex_add_len m n F]

/-- An event of the first `m` slots has the same probability over more slots: if the
indicator of `S'` over `m + n` slots dominates that of `S` over the first `m`, the
expectation does too. -/
theorem Ex_le_extend {m n : ℕ} {S : Set (List Out)} {S' : Set (List Out)}
    (h : ∀ x : List Out, x.length = m → x ∈ S → ∀ y : List Out, y.length = n → x ++ y ∈ S') :
    Ex κ m (S.indicator 1) [] ≤ Ex κ (m + n) (S'.indicator 1) [] := by
  rw [Ex_add_len]
  refine Ex_mono_len (κ := κ) m [] fun x hx => ?_
  simp only [List.nil_append]
  by_cases hS : x ∈ S
  · rw [Set.indicator_of_mem hS]
    have : Ex κ n (fun _ => (1 : ℝ)) x ≤ Ex κ n (S'.indicator 1) x :=
      Ex_mono_len (κ := κ) n x fun y hy => by
        rw [Set.indicator_of_mem (h x hx hS y hy)]; rfl
    rw [Ex_const] at this
    simpa using this
  · rw [Set.indicator_of_notMem hS]
    exact Ex_nonneg (κ := κ) n (fun l => Set.indicator_nonneg (fun _ _ => zero_le_one) l) x

end Kernel

/-- **`settleEps3E` grows with the horizon.** -/
theorem settleEps3E_mono {E : Env} {B : Band} {Δ : ℕ} (P : Cert2 B Δ) {lpi : ℝ} {Ccap N₁ N₂ G G' J Lw r T : ℕ}
    {x yy : ℝ} (hN : N₁ ≤ N₂) (hhi0 : 0 ≤ B.hhi) (hhi1 : B.hhi ≤ 1) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1)
    (hx : 1 ≤ x) (hyy0 : 0 < yy) (hyy1 : yy ≤ 1) (hlpi : 0 < lpi) (he2 : 0 ≤ P.e 2) :
    settleEps3E E B P lpi Ccap N₁ G G' J Lw r T x yy ≤ settleEps3E E B P lpi Ccap N₂ G G' J Lw r T x yy := by
  have hN' : (N₁ : ℝ) ≤ N₂ := by exact_mod_cast hN
  have h1 : 0 ≤ (1 - (1 - B.hhi) ^ Δ) ^ (G / Δ) := by
    apply pow_nonneg; have := pow_le_one₀ (n := Δ) (by linarith : 0 ≤ 1 - B.hhi) (by linarith); linarith
  have h2 : 0 ≤ (1 - B.hlo) ^ G' := pow_nonneg (by linarith) _
  have he17 : 0 ≤ P.e 17 := by linarith [P.he17]
  have hτ : 0 < P.τ := by linarith [P.hτ]
  have h3 : 0 ≤ P.e 17 ^ (J + 1) / P.τ ^ (Lw + 1) := by positivity
  have hlr : 0 < 1 - P.lr := by linarith [P.hlr1]
  have hbq : 0 ≤ 1 + (P.b - 1) / (1 - P.lr) := by have := P.hb1; positivity
  have h4 : 0 ≤ lpi ^ J * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) := by
    have := P.hlp0; positivity
  have h5 : 0 ≤ (1 + (x - 1) * (1 - B.elo)) ^ Lw / x ^ (E.c.k + 1) := by
    have : 0 ≤ (x - 1) * (1 - B.elo) := mul_nonneg (by linarith) (by linarith)
    have : (0 : ℝ) < x := by linarith
    positivity
  have h6 : 0 ≤ (1 + (P.b - 1) / (1 - P.lr)) / P.c ^ (r + 1) := by have := P.hc; positivity
  have hPT : PT 1 yy B.hlo B.hhi T ≤ 1 := by
    unfold PT
    split_ifs
    · have := pow_nonneg (by linarith : 0 ≤ 1 - B.hhi) T; linarith
    · have := pow_nonneg (by linarith : 0 ≤ 1 - B.hlo) T; linarith
  have h7 : 0 ≤ (1 + (yy - 1) * PT 1 yy B.hlo B.hhi T) ^ nbD E Δ G T / yy ^ (E.c.k + r) := by
    have : 0 ≤ 1 + (yy - 1) * PT 1 yy B.hlo B.hhi T := by nlinarith
    positivity
  have hnEp : (nEp E N₁ : ℝ) ≤ nEp E N₂ := by
    unfold nEp; exact_mod_cast Nat.div_le_div_right (by omega)
  unfold settleEps3E
  gcongr

/-- **A split is a failure of the truncated good event.** If epoch `ep + 1`'s canonical
prefix does not extend epoch `ep`'s, every string dominating the lottery string's first
`Ms` slots fails the good event up to `min (fix (ep + 1)) N`, cut at `Ms`. -/
theorem split_up (E : Env) (hA : Assm E) (hlive : ∀ t, ∃ j ∈ E.nodes, E.online j t = true) {es : List Event}
    {N Ms Lw r G ep : ℕ} (hNF : (wF E es).now ≤ N) (hep : 1 ≤ ep)
    (hMs : min (E.c.fix (ep + 1)) N < Ms)
    (hgr : ∀ ep', 1 ≤ ep' → E.c.fix ep' ≤ min (E.c.fix (ep + 1)) N → E.c.cut ep' + G < Ms)
    (hsplit : prefixBelow (CP E es (ep + 1)) (E.c.cut ep) ≠ CP E es ep) {l' : List Out}
    (hl : List.Forall₂ OutLe (slots (lotStr E es) Ms) l') :
    ¬ (GoodLS E (strOf l') (min (E.c.fix (ep + 1)) N) Lw (gend E.Δ Ms (strOf l')) ∧
      GrowthS E (strOf l') (gend E.Δ Ms (strOf l')) (min (E.c.fix (ep + 1)) N) r G) := by
  classical
  intro hg
  set Ne := min (E.c.fix (ep + 1)) N
  set lot := lotStr E es with hlot
  obtain ⟨hlen, hget⟩ := List.forall₂_iff_get.1 hl
  rw [slots_length] at hlen
  have hdom1 : ∀ i, 1 ≤ i → i ≤ Ms → OutLe (enc (lot i)) (l'.getD (i - 1) Out.empty) := by
    intro i h1 h2
    have hk1 : i - 1 < (slots lot Ms).length := by rw [slots_length]; omega
    have hk2 : i - 1 < l'.length := by omega
    have := hget (i - 1) hk1 hk2
    rw [List.getD_eq_getElem _ _ hk2]
    simp only [List.get_eq_getElem, slots_get, show i - 1 + 1 = i by omega] at this
    exact this
  set w : CStr := fun i => if 1 ≤ i ∧ i ≤ Ms then ((lot i).1, (strOf l' i).2) else lot i with hw
  have hstr : ∀ i, 1 ≤ i → strOf l' i = (l'.getD (i - 1) Out.empty).toPair := by
    intro i hi; unfold strOf; rw [if_neg (by omega)]
  have hdom : AdvLeW Ne lot w := by
    refine ⟨fun i _ _ => by simp only [hw]; split_ifs <;> rfl, fun i hi => ?_⟩
    simp only [hw]
    split_ifs with h
    · rw [hstr i h.1]
      exact (hdom1 i h.1 h.2).2 (by simpa [enc] using hi)
    · exact hi
  have hsim : SimOn (strOf l') w 0 Ms := by
    intro i h1 h2
    have hd := hdom1 i (by omega) h2
    simp only [hw, if_pos (show 1 ≤ i ∧ i ≤ Ms by omega)]
    rw [hstr i (by omega)]
    simp only [Out.toPair]
    rw [← hd.1]
    exact ⟨enc_hon_zero _, enc_hon_one _, trivial⟩
  have hgw := good_congr_cap E rfl hsim hMs hgr hg
  exact hsplit (cons_of_lot hA hlive hep (min_le_min le_rfl hNF) hdom hgw.1 (growthS_on E hgw.2))

/-- Growth witnesses of epochs fixed by a horizon lie before it. -/
theorem cut_add_lt {c : Config} (hc : c.Sane) {G : ℕ} (hOG : c.nonceOffset + G + 2 ≤ c.epochLength)
    {H Ms : ℕ} (hHM : H < Ms) : ∀ ep, 1 ≤ ep → c.fix ep ≤ H → c.cut ep + G < Ms := by
  intro ep hep hfix
  have : c.cut ep + G ≤ c.fix ep := by
    obtain ⟨e0, rfl⟩ : ∃ e0, ep = e0 + 1 := ⟨ep - 1, by omega⟩
    have hs : c.epochStart (e0 + 1) = c.epochStart e0 + c.epochLength := by
      unfold Config.epochStart; ring
    unfold Config.cut Config.fix
    simp only [Nat.add_sub_cancel]
    omega
  omega

/-- **One epoch's split, while in band.** The probability that epoch `ep + 1`'s
canonical prefix does not extend epoch `ep`'s, while every slot up to
`min (fix (ep + 1)) N + 1` is within its member's band, is at most `settleEps3E` at the
horizon `min (fix (ep + 1)) N`. -/
theorem prob_split_epoch {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {O : Ω → Oracle} {E : Env} (hA : Assm E) (hlive : ∀ t, ∃ j ∈ E.nodes, E.online j t = true)
    (es : Ω → List Event) {N : ℕ}
    (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {B : Band} {Δ K G : ℕ} {fam : Fin K → Band} (hΔ : E.Δ = Δ) (D : Cert3E B Δ fam E.c.epochLength G)
    (hP : ∀ k, (fam k).Prod) (pick : ℕ → EpochState → Fin K)
    {G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1)
    (hLw : Lw + G < E.c.epochLength) (hOG : E.c.nonceOffset + G + 2 ≤ E.c.epochLength)
    {ep : ℕ} (hep : 1 ≤ ep) :
    μ {ω | prefixBelow (CP (E.withO (O ω)) (es ω) (ep + 1)) (E.c.cut ep) ≠ CP (E.withO (O ω)) (es ω) ep ∧
      ∀ n < min (E.c.fix (ep + 1)) N + 1,
        SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
          (σE (E.withO (O ω)) (es ω) (n + 1))} ≤
      ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G (min (E.c.fix (ep + 1)) N) G G' J Lw r T x yy) := by
  classical
  subst hΔ
  set Ne := min (E.c.fix (ep + 1)) N with hNe
  set Ms := Ne + 1 with hMsdef
  set Mb := Ne + G + G' + E.Δ + 2 with hMbdef
  have hgr : ∀ H M, H < M → ∀ ep', 1 ≤ ep' → E.c.fix ep' ≤ H → E.c.cut ep' + G < M :=
    fun H M h => cut_add_lt hA.sane hOG h
  set ok : Set Ω := {ω | ∀ n < Ms, SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1))))
    E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1))} with hok
  by_cases hG : (goodB fam).Nonempty
  · set Bad_s : Set (List Out) := {l | ¬ (GoodLS E (strOf l) Ne Lw (gend E.Δ Ms (strOf l)) ∧
      GrowthS E (strOf l) (gend E.Δ Ms (strOf l)) Ne r G)} with hBad_s
    set S_s : Set (List Out) := {l | ∀ l', List.Forall₂ OutLe l l' → l' ∈ Bad_s} with hS_s
    have hSs : UpClosed S_s := fun l l2 h hl l' h' => hl l' (forall₂_trans h h')
    set Bad_b : Set (List Out) := {l | ¬ (GoodLS E (strOf l) Ne Lw (gend E.Δ Mb (strOf l)) ∧
      GrowthS E (strOf l) (gend E.Δ Mb (strOf l)) Ne r G)} with hBad_b
    set S_b : Set (List Out) := {l | ∀ l', List.Forall₂ OutLe l l' → l' ∈ Bad_b} with hS_b
    -- a split, in band, puts the lottery string in `S_s`
    have hsub : {ω | prefixBelow (CP (E.withO (O ω)) (es ω) (ep + 1)) (E.c.cut ep) ≠ CP (E.withO (O ω)) (es ω) ep ∧
        ∀ n < Ne + 1, SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
          (σE (E.withO (O ω)) (es ω) (n + 1))} ⊆
        {ω | slots (lotStr (E.withO (O ω)) (es ω)) Ms ∈ S_s ∧ ∀ n < Ms,
          SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
            (σE (E.withO (O ω)) (es ω) (n + 1))} := by
      rintro ω ⟨hsp, hb⟩
      refine ⟨?_, hb⟩
      intro l' hl' hg
      exact split_up (E.withO (O ω)) (hA.withO (O ω)) hlive (hNF ω) hep (Nat.lt_succ_self _) (hgr Ne Ms (Nat.lt_succ_self _)) hsp hl'
        ⟨goodLS_withO hg.1, hg.2⟩
    obtain ⟨κ, hκ, hbound⟩ := lottery_law_epoch_ok (M := Ms) hA es (by omega) hdel hO hσm hfresh hP pick hG hSs
    refine (measure_mono hsub).trans (hbound.trans (ENNReal.ofReal_le_ofReal ?_))
    -- from the smaller cap to the larger
    have hext : Ex κ Ms (S_s.indicator 1) [] ≤ Ex κ (Ms + (G + G' + E.Δ + 1)) (S_b.indicator 1) [] := by
      refine Ex_le_extend κ fun x hx hxS y _ => ?_
      intro l' hl' hgb
      have hlen := hl'.length_eq
      have htake : List.Forall₂ OutLe x (l'.take Ms) := by
        have := List.forall₂_take Ms hl'
        rwa [List.take_left' hx] at this
      have hts : (l'.take Ms).length = Ms := by
        rw [List.length_take, ← hlen, List.length_append, hx]; omega
      have hgs := good_trunc E (Ms := Ms) (Mb := Mb) (by omega) (by omega) (hgr Ne Ms (by omega)) hgb
      have hsim : SimOn (strOf l') (strOf (l'.take Ms)) 0 Ms := by
        intro i _ h2
        have : strOf l' i = strOf (l'.take Ms) i := by
          conv_lhs => rw [← List.take_append_drop Ms l']
          exact strOf_append_of_le (by omega)
        rw [this]; exact ⟨Iff.rfl, Iff.rfl, rfl⟩
      exact hxS _ htake (good_congr_cap E rfl hsim (by omega) (hgr Ne Ms (by omega)) hgs)
    refine hext.trans ?_
    have hEL : 0 < E.c.epochLength := by omega
    have hMb : Ms + (G + G' + E.Δ + 1) = Mb := by omega
    rw [hMb]
    refine le_trans ?_ (settle_bound3E E rfl hA.sane D.C.P (D.C.within hκ) D.C.hG
      (D.C.anyPhase hκ 0 (by decide) D.C.heS0) (D.C.anyPhase hκ 1 (by decide) D.C.heS1)
      (D.C.anyPhase hκ 2 (by decide) D.C.heS2) (D.C.anyPhase hκ 17 (by decide) D.C.heS17) (D.C.truncPhase hκ)
      D.hlpi0 D.hlpi (fun t => ¬ NoSw E.c.epochLength G t) (swCnt_noSw_le hEL hLw) (D.inEpoch hκ) hx hyy0 hyy1 hT
      (le_refl Mb) hhi1 hlo0 hlo1 helo1)
    apply Ex_mono_len
    intro t _
    simp only [List.nil_append]
    by_cases ht : t ∈ S_b
    · have hb : t ∈ Bad_b := ht t (forall₂_refl t)
      rw [Set.indicator_of_mem ht]
      simp only [hBad_b, Set.mem_setOf_eq] at hb
      rw [if_neg hb]; rfl
    · rw [Set.indicator_of_notMem ht]
      split_ifs <;> norm_num
  · -- no member has a nonempty polytope: no slot is in band
    have hempty : {ω | prefixBelow (CP (E.withO (O ω)) (es ω) (ep + 1)) (E.c.cut ep) ≠ CP (E.withO (O ω)) (es ω) ep ∧
        ∀ n < Ne + 1, SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
          (σE (E.withO (O ω)) (es ω) (n + 1))} = ∅ := by
      ext ω
      simp only [Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false, not_and]
      intro _ h
      exact hG ⟨_, mem_goodB.2 ⟨_, (h 0 (by omega)).hon⟩⟩
    rw [hempty, measure_empty]; exact zero_le'

end Cryptarchia.Prob
