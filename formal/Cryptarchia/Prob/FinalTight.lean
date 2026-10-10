module

public import Cryptarchia.Prob.Final3E
public import Cryptarchia.Prob.Pick
import Cryptarchia.Prob.EpochInd
import Cryptarchia.Prob.Trunc
import Cryptarchia.Prob.Occupied
import Cryptarchia.Prob.FinalTSI
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
import Cryptarchia.Prob.ROStop

/-!
# Finality over many epochs, with one settlement bound

`finality_tight`: finality over many epochs with the stake estimate, with the bound
`settleEps3E + Ne · bandEps`. The member assignment is constructed (`slotBand_pickM`),
the estimate's update is proven from the canonical chain (`recur_of`,
`occupied_le_wcnt`), and the canonical prefixes' consistency is proven: the
per-epoch consistency failures and the finality failure are all failures of the
lottery's good event: each epoch's failure, cut at its horizon, implies the good event's
failure up to `N` (`lift_bad`). They need the band only up to their own horizons, and the
kernel bound with the band needed only until the event is decided
(`lottery_law_epoch_dec`) covers them together.
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory Settle
open scoped ENNReal

theorem slots_take (w : CStr) {m n : ℕ} (h : m ≤ n) : (slots w n).take m = slots w m := by
  unfold slots
  rw [← List.map_take, List.take_range, min_eq_left h]

/-- **The good event at a horizon implies it at an earlier one.** -/
theorem good_horizon_mono (E : Env) {w : CStr} {N N' Lw r G : ℕ} {e : ℕ → ℕ} (hN : N' ≤ N)
    (hg : GoodLS E w N Lw e ∧ GrowthS E w e N r G) : GoodLS E w N' Lw e ∧ GrowthS E w e N' r G := by
  obtain ⟨⟨h0, hm, hq, hu, hc, hw⟩, hgr⟩ := hg
  exact ⟨⟨h0, hm, fun k hk => hq k (by omega), hu, fun t k h1 h2 h3 h4 => hc t k h1 (by omega) h3 h4,
    fun t ht => hw t (by omega)⟩, fun ep hep hf => hgr ep hep (by omega)⟩

/-- **A failure cut at a horizon is a failure up to `N`.** If the first `Ms` outcomes of
`l` (of length `M`) fail, robustly, the good event up to `Ne < Ms` cut at `Ms`, then `l`
fails, robustly, the good event up to `N ≥ Ne` cut at `M`. -/
theorem lift_bad (E : Env) {N Ne Ms M Lw r G : ℕ} (hNe : Ne ≤ N) (hNs : Ne < Ms) (hMs : Ms ≤ M)
    (hgr : ∀ ep, 1 ≤ ep → E.c.fix ep ≤ Ne → E.c.cut ep + G < Ms) {l : List Out} (hl : l.length = M)
    (h : ∀ l', List.Forall₂ OutLe (l.take Ms) l' → ¬ (GoodLS E (strOf l') Ne Lw (gend E.Δ Ms (strOf l')) ∧
      GrowthS E (strOf l') (gend E.Δ Ms (strOf l')) Ne r G)) :
    ∀ l', List.Forall₂ OutLe l l' → ¬ (GoodLS E (strOf l') N Lw (gend E.Δ M (strOf l')) ∧
      GrowthS E (strOf l') (gend E.Δ M (strOf l')) N r G) := by
  intro l' hl' hg
  have hlen := hl'.length_eq
  have hgs := good_trunc E (Ms := Ms) (Mb := M) hNs hMs hgr (good_horizon_mono E hNe hg)
  have hsim : SimOn (strOf l') (strOf (l'.take Ms)) 0 Ms := by
    intro i _ h2
    have : strOf l' i = strOf (l'.take Ms) i := by
      conv_lhs => rw [← List.take_append_drop Ms l']
      exact strOf_append_of_le (by rw [List.length_take]; omega)
    rw [this]; exact ⟨Iff.rfl, Iff.rfl, rfl⟩
  exact h _ (List.forall₂_take Ms hl') (good_congr_cap E rfl hsim hNs hgr hgs)

/-- **Finality over many epochs, with the stake estimate.** A finality violation has
probability at most `settleEps3E + Ne · bandEps`. -/
theorem finality_tight {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {O : Ω → Oracle} {E : Env} (hA : Assm E) (es : Ω → List Event) {N M : ℕ}
    (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {B : Band} {Δ K G : ℕ} {fam : Fin (K + 1) → Band} (hΔ : E.Δ = Δ) (D : Cert3E B Δ fam E.c.epochLength G)
    (hP : ∀ k, (fam k).Prod)
    {G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + G' + Δ + 2 ≤ M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1)
    (hLw : Lw + G < E.c.epochLength) (hOG : E.c.nonceOffset + G + 2 ≤ E.c.epochLength)
    -- the estimate
    {Tb : TBand} (hc : LotConsts E.c Tb.η) (hTb : Tb.OK) (hb : E.c.betaP = E.c.precision)
    (hprec : 0 < E.c.precision) (hPf : 0 < E.c.period * E.c.fP) (hP1 : 1 ≤ E.c.period)
    (hPEL : E.c.period ≤ E.c.epochLength)
    (hst : ∀ ω i, StateOK E Tb i (σE (E.withO (O ω)) (es ω) i))
    (h0 : InB E Tb (fun _ => es0 E) 0) {Ne : ℕ} (hNe : M / E.c.epochLength < Ne)
    (hlo : ∀ ω e, e + 1 < Ne → (1 - Tb.μ) *
      hcnt E (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e ≤
        (occupied E.c (CP (E.withO (O ω)) (es ω) (e + 1)) e : ℝ))
    (hpath : ∀ ω e, e + 1 < Ne → StakePath E Tb (σE (E.withO (O ω)) (es ω)) e)
    -- the members
    (hon : OnlineEpoch E) (hlive : ∀ t, ∃ j ∈ E.nodes, E.online j t = true) {mem : Fin (K + 1) → Member} (hfam : ∀ k, (mem k).B = fam k)
    (hok : ∀ k, (mem k).OK Tb.η Tb.ζ)
    (hcov : ∀ y, Tb.ylo ≤ y → y ≤ Tb.Yh → ∃ k, (mem k).ylo ≤ y ∧ y ≤ (mem k).yhi)
    (hadv : ∀ k, Tb.β * (mem k).yhi ≤ (1 - Tb.β) * (mem k).ahi) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) +
      Ne * ENNReal.ofReal (bandEps Tb E.c.period) := by
  classical
  have hEL : 0 < E.c.epochLength := hA.sane.epochLength_pos
  have hEL3 : 3 ≤ E.c.epochLength := by have := hA.sane.fix_le; have := hA.sane.offset_pos; omega
  subst hΔ
  set band : Ω → ℕ → Prop := fun ω n => SlotBand (fam (pickM E mem ((n + 1) / E.c.epochLength)
    (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1)) with hband
  -- a slot of an in-band epoch is within its member's band
  have hbandOf : ∀ ω n, InB E Tb (σE (E.withO (O ω)) (es ω)) ((n + 1) / E.c.epochLength) → band ω n := by
    intro ω n hin
    have h1 : (n + 1) / E.c.epochLength * E.c.epochLength ≤ n + 1 := Nat.div_mul_le_self _ _
    have h2 : n + 1 < ((n + 1) / E.c.epochLength + 1) * E.c.epochLength := by
      rw [add_mul, one_mul]
      have := Nat.lt_div_mul_add (a := n + 1) hEL
      linarith
    show SlotBand _ _ _ _
    rw [← hfam]
    exact slotBand_pickM hc hTb hA.nodup hon hok hcov hadv (hst ω (n + 1)) (hin (n + 1) h1 h2)
  -- the events on outcome lists
  set Bad_main : Set (List Out) := {l | ¬ (GoodLS E (strOf l) N Lw (gend E.Δ M (strOf l)) ∧
    GrowthS E (strOf l) (gend E.Δ M (strOf l)) N r G)} with hBad_main
  set S_main : Set (List Out) := {l | ∀ l', List.Forall₂ OutLe l l' → l' ∈ Bad_main} with hS_main
  have hSm : UpClosed S_main := fun l l2 h hl l' h' => hl l' (forall₂_trans h h')
  set Nh : ℕ → ℕ := fun e => min (E.c.fix (e + 1)) N with hNh
  set S_s : ℕ → Set (List Out) := fun e => {l | ∀ l', List.Forall₂ OutLe l l' →
    ¬ (GoodLS E (strOf l') (Nh e) Lw (gend E.Δ (Nh e + 1) (strOf l')) ∧
      GrowthS E (strOf l') (gend E.Δ (Nh e + 1) (strOf l')) (Nh e) r G)} with hS_s
  have hgr : ∀ e, ∀ ep, 1 ≤ ep → E.c.fix ep ≤ Nh e → E.c.cut ep + G < Nh e + 1 :=
    fun e => cut_add_lt hA.sane hOG (Nat.lt_succ_self _)
  have hNhe : ∀ e, Nh e = min (E.c.fix (e + 1)) N := fun e => rfl
  have hNM' : ∀ e, Nh e + 1 ≤ M := fun e => by have := min_le_right (E.c.fix (e + 1)) N; rw [hNhe]; omega
  have hlift : ∀ e (x : List Out), x.length = M → x.take (Nh e + 1) ∈ S_s e → x ∈ S_main :=
    fun e x hx hS l' hl' => lift_bad E (min_le_right _ _) (Nat.lt_succ_self _) (hNM' e) (hgr e) hx hS l' hl'
  set Dd : List Out → Prop := fun x => ∃ e, 1 ≤ e ∧ Nh e + 1 ≤ x.length ∧ x.take (Nh e + 1) ∈ S_s e with hDd
  have hDmono : ∀ x o, Dd x → Dd (x ++ [o]) := by
    rintro x o ⟨e, h1, h3, h4⟩
    refine ⟨e, h1, by simp; omega, ?_⟩
    rwa [List.take_append_of_le_length h3]
  have hDS : ∀ x y : List Out, Dd x → x.length + y.length = M → x ++ y ∈ S_main := by
    rintro x y ⟨e, -, h3, h4⟩ hl
    apply hlift e _ (by simp; omega)
    rwa [List.take_append_of_le_length h3]
  -- the update holds off the split sets
  set Bad : ℕ → Set Ω := fun e => {ω | 1 ≤ e ∧
    prefixBelow (CP (E.withO (O ω)) (es ω) (e + 1)) (E.c.cut e) ≠ CP (E.withO (O ω)) (es ω) e} with hBad
  have hrec : ∀ ω e, e + 1 < Ne → ω ∉ Bad e →
      Recur E Tb (σE (E.withO (O ω)) (es ω))
        (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e := by
    intro ω e he hB
    have hc' : 1 ≤ e → prefixBelow (CP (E.withO (O ω)) (es ω) (e + 1)) (E.c.cut e) = CP (E.withO (O ω)) (es ω) e :=
      fun h1 => by by_contra hne; exact hB ⟨h1, hne⟩
    exact recur_of hA _ hc' (hlo ω e he) (occupied_le_wcnt (hA.withO (O ω)) hc')
  set Tset : Set Ω := {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S_main ∧ ∀ n < M, band ω n} with hTset
  -- an unsafe execution: the main event in band, or some epoch out of band
  have h1 : {ω | Unsafe (E.withO (O ω)) (es ω)} ⊆ Tset ∪ {ω | ∃ e < Ne, ¬ InB E Tb (σE (E.withO (O ω)) (es ω)) e} := by
    intro ω hU
    by_cases hb : ∀ n < M, band ω n
    · refine Or.inl ⟨?_, hb⟩
      intro l' hl' hg
      exact unsafe_up (E.withO (O ω)) (hA.withO (O ω)) (Lw := Lw) (r := r) (G := G) (hNF ω) (by omega) hU hl'
        ⟨goodLS_withO hg.1, hg.2⟩
    · refine Or.inr ?_
      push Not at hb
      obtain ⟨n, hn, hnb⟩ := hb
      exact ⟨(n + 1) / E.c.epochLength, lt_of_le_of_lt (Nat.div_le_div_right (by omega)) hNe,
        fun hin => hnb (hbandOf ω n hin)⟩
  refine (measure_mono h1).trans ((prob_out_of_band_cover hA es hO hσm hfresh hc hTb hb hprec hPf hP1 hPEL hst
    (fun ω => inB0_of_genesis h0) Bad hrec hpath Tset).trans (add_le_add ?_ le_rfl))
  -- the main event and the splits, in band until decided
  by_cases hG : (goodB fam).Nonempty
  · have hsub3 : Tset ∪ ⋃ e ∈ Finset.range Ne, (Bad e ∩ {ω | ∀ e' ≤ e, InB E Tb (σE (E.withO (O ω)) (es ω)) e'}) ⊆
        {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S_main ∧ ∀ n < M,
          SlotBand (fam (pickM E mem ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
            (σE (E.withO (O ω)) (es ω) (n + 1)) ∨ Dd (slots (lotStr (E.withO (O ω)) (es ω)) n)} := by
      rintro ω (⟨hS, hb⟩ | hω)
      · exact ⟨hS, fun n hn => Or.inl (hb n hn)⟩
      · simp only [Set.mem_iUnion, Finset.mem_range] at hω
        obtain ⟨e, -, ⟨h1e, hsp⟩, hin⟩ := hω
        have hsplit : slots (lotStr (E.withO (O ω)) (es ω)) (Nh e + 1) ∈ S_s e := fun l' hl' hg =>
          split_up (E.withO (O ω)) (hA.withO (O ω)) hlive (hNF ω) h1e (Nat.lt_succ_self _) (hgr e) hsp hl'
            ⟨goodLS_withO hg.1, hg.2⟩
        refine ⟨hlift e _ (slots_length _ _) (by rw [slots_take _ (hNM' e)]; exact hsplit), fun n hn => ?_⟩
        by_cases hns : n < Nh e + 1
        · left
          have hfx : E.c.fix (e + 1) + 2 ≤ (e + 1) * E.c.epochLength := (hA.sane.fix_ok (e + 1) (by omega)).2
          have hmin := min_le_left (E.c.fix (e + 1)) N
          have hlt : n + 1 < (e + 1) * E.c.epochLength := by rw [hNhe] at hns; omega
          have hm : (n + 1) / E.c.epochLength ≤ e := by
            have := (Nat.div_lt_iff_lt_mul hEL).2 hlt
            omega
          exact hbandOf ω n (hin _ hm)
        · right
          exact ⟨e, h1e, by rw [slots_length]; omega, by rw [slots_take _ (by omega)]; exact hsplit⟩
    obtain ⟨κ, hκ, hbound⟩ := lottery_law_epoch_dec (M := M) hA es (by omega) hdel hO hσm hfresh hP (pickM E mem) hG
      hSm Dd hDmono hDS
    refine (measure_mono hsub3).trans (hbound.trans (ENNReal.ofReal_le_ofReal ?_))
    refine le_trans ?_ (settle_bound3E E rfl hA.sane D.C.P (D.C.within hκ) D.C.hG
      (D.C.anyPhase hκ 0 (by decide) D.C.heS0) (D.C.anyPhase hκ 1 (by decide) D.C.heS1)
      (D.C.anyPhase hκ 2 (by decide) D.C.heS2) (D.C.anyPhase hκ 17 (by decide) D.C.heS17) (D.C.truncPhase hκ)
      D.hlpi0 D.hlpi (fun t => ¬ NoSw E.c.epochLength G t) (swCnt_noSw_le hEL hLw) (D.inEpoch hκ) hx hyy0 hyy1 hT
      hNM hhi1 hlo0 hlo1 helo1)
    apply Ex_mono_len
    intro t _
    simp only [List.nil_append]
    by_cases ht : t ∈ S_main
    · have hb : t ∈ Bad_main := ht t (forall₂_refl t)
      rw [Set.indicator_of_mem ht]
      simp only [hBad_main, Set.mem_setOf_eq] at hb
      rw [if_neg hb]; rfl
    · rw [Set.indicator_of_notMem ht]
      split_ifs <;> norm_num
  · -- no member has a nonempty polytope: nothing is in band
    have hnone : ∀ ω n, ¬ band ω n := fun ω n hb => hG ⟨_, mem_goodB.2 ⟨_, hb.hon⟩⟩
    have hempty : Tset ∪ ⋃ e ∈ Finset.range Ne, (Bad e ∩ {ω | ∀ e' ≤ e, InB E Tb (σE (E.withO (O ω)) (es ω)) e'}) = ∅ := by
      ext ω
      simp only [Set.mem_union, Set.mem_iUnion, Finset.mem_range, Set.mem_inter_iff, Set.mem_empty_iff_false,
        iff_false, not_or, not_exists, not_and]
      refine ⟨fun h => hnone ω 0 (h.2 0 (by omega)), fun e _ _ hin => hnone ω 0 (hbandOf ω 0 ?_)⟩
      rw [Nat.div_eq_of_lt (by omega)]; exact hin 0 (Nat.zero_le _)
    rw [hempty, measure_empty]; exact zero_le

end Cryptarchia.Prob
