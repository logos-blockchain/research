module

import Cryptarchia.Prob.Occupied
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
public import Cryptarchia.Prob.Final3E
public import Cryptarchia.Prob.Pick
import Cryptarchia.Prob.EpochInd
import Cryptarchia.Prob.FinalTSI

/-!
# Probabilistic finality over many epochs, by induction on the epochs

`finality_core`: finality over many epochs with the stake estimate, with consistent
canonical prefixes proven rather than assumed. Epoch `e`'s prefixes are consistent on the lottery's
good event up to `min (fix (e + 1)) N`, which concerns epochs up to `e` only, so its
failure is charged while those epochs are in band (`prob_out_of_band_seq`) and bounded
by the settlement bound at that horizon (`prob_split_epoch`), at most `settleEps3E` at
`N`. The cost is `Ne` more copies of the settlement bound.
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory
open scoped ENNReal

/-- **Probabilistic finality over many epochs, with consistent canonical prefixes
proven.** With some honest node online at every slot (`hlive`):
a finality violation has probability at most `(Ne + 1) · settleEps3E + Ne · bandEps`. -/
theorem finality_core {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
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
    (hhi0 : 0 ≤ B.hhi) (he2 : 0 ≤ D.C.P.e 2)
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
      (Ne * ENNReal.ofReal (bandEps Tb E.c.period) +
        Ne * ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy)) := by
  classical
  have hEL : 0 < E.c.epochLength := hA.sane.epochLength_pos
  refine (final_bimm_ro_epoch3_ok hA es hNF hdel hO hσm hfresh hΔ D hP (pickM E mem) hx hyy0 hyy1 hT hNM
    hhi1 hlo0 hlo1 helo1 hLw).trans (add_le_add le_rfl ?_)
  set Bad : ℕ → Set Ω := fun e => {ω | 1 ≤ e ∧
    prefixBelow (CP (E.withO (O ω)) (es ω) (e + 1)) (E.c.cut e) ≠ CP (E.withO (O ω)) (es ω) e} with hBad
  have hrec : ∀ ω e, e + 1 < Ne → ω ∉ Bad e →
      Recur E Tb (σE (E.withO (O ω)) (es ω))
        (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e := by
    intro ω e he hB
    have hc' : 1 ≤ e → prefixBelow (CP (E.withO (O ω)) (es ω) (e + 1)) (E.c.cut e) = CP (E.withO (O ω)) (es ω) e :=
      fun h1 => by by_contra hne; exact hB ⟨h1, hne⟩
    exact recur_of hA _ hc' (hlo ω e he) (occupied_le_wcnt (hA.withO (O ω)) hc')
  -- a slot out of its member's band: some epoch out of band
  have hsubS : {ω | ∃ n < M, ¬ SlotBand (fam (pickM E mem ((n + 1) / E.c.epochLength)
      (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1))} ⊆
      {ω | ∃ e < Ne, ¬ InB E Tb (σE (E.withO (O ω)) (es ω)) e} := by
    rintro ω ⟨n, hn, hnb⟩
    refine ⟨(n + 1) / E.c.epochLength, lt_of_le_of_lt (Nat.div_le_div_right (by omega)) hNe, fun hin => ?_⟩
    apply hnb
    have h1 : (n + 1) / E.c.epochLength * E.c.epochLength ≤ n + 1 := Nat.div_mul_le_self _ _
    have h2 : n + 1 < ((n + 1) / E.c.epochLength + 1) * E.c.epochLength := by
      rw [add_mul, one_mul]
      have := Nat.lt_div_mul_add (a := n + 1) hEL
      linarith
    rw [← hfam]
    exact slotBand_pickM hc hTb hA.nodup hon hok hcov hadv (hst ω (n + 1)) (hin (n + 1) h1 h2)
  refine le_trans (measure_mono hsubS) ((prob_out_of_band_seq hA es hO hσm hfresh hc hTb hb hprec hPf hP1 hPEL hst
    (fun ω => inB0_of_genesis h0) Bad hrec hpath).trans (add_le_add le_rfl ?_))
  -- each epoch's split, while in band
  have hone : ∀ e, μ (Bad e ∩ {ω | ∀ e' ≤ e, InB E Tb (σE (E.withO (O ω)) (es ω)) e'}) ≤
      ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) := by
    intro e
    rcases Nat.eq_zero_or_pos e with h0e | hep
    · have : Bad e = ∅ := by ext ω; simp only [hBad, Set.mem_ofPred_eq, Set.mem_empty_iff_false, iff_false]; omega
      rw [this, Set.empty_inter, measure_empty]; exact zero_le
    refine le_trans (measure_mono ?_) ((prob_split_epoch (G' := G') (J := J) (r := r) hA hlive es hNF hdel hO hσm hfresh hΔ D hP (pickM E mem) hx
      hyy0 hyy1 hT hhi1 hlo0 hlo1 helo1 hLw hOG hep).trans (ENNReal.ofReal_le_ofReal ?_))
    · rintro ω ⟨⟨-, hsp⟩, hin⟩
      refine ⟨hsp, fun n hn => ?_⟩
      have hfx : E.c.fix (e + 1) + 2 ≤ (e + 1) * E.c.epochLength := (hA.sane.fix_ok (e + 1) (by omega)).2
      have hmin := min_le_left (E.c.fix (e + 1)) N
      have hlt : n + 1 < (e + 1) * E.c.epochLength := by omega
      have hm : (n + 1) / E.c.epochLength ≤ e := by
        have := (Nat.div_lt_iff_lt_mul hEL).2 hlt
        omega
      have h1 : (n + 1) / E.c.epochLength * E.c.epochLength ≤ n + 1 := Nat.div_mul_le_self _ _
      have h2 : n + 1 < ((n + 1) / E.c.epochLength + 1) * E.c.epochLength := by
        rw [add_mul, one_mul]
        have := Nat.lt_div_mul_add (a := n + 1) hEL
        linarith
      rw [← hfam]
      exact slotBand_pickM hc hTb hA.nodup hon hok hcov hadv (hst ω (n + 1)) (hin _ hm (n + 1) h1 h2)
    · exact settleEps3E_mono D.C.P (min_le_right _ _) hhi0 hhi1 hlo1 helo1 hx hyy0 hyy1 D.hlpi0 he2
  calc ∑ e ∈ Finset.range Ne, μ (Bad e ∩ {ω | ∀ e' ≤ e, InB E Tb (σE (E.withO (O ω)) (es ω)) e'})
      ≤ ∑ e ∈ Finset.range Ne, ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) :=
        Finset.sum_le_sum fun e _ => hone e
    _ = Ne * ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) := by
        rw [Finset.sum_const, Finset.card_range, nsmul_eq_mul]

end Cryptarchia.Prob
