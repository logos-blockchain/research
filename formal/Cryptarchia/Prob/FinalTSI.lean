module

public import Cryptarchia.Prob.Final3E
public import Cryptarchia.Prob.Pick
import Cryptarchia.Proof.Recur
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
import Cryptarchia.Prob.Occupied

/-!
# Probabilistic finality over many epochs, with the stake estimate's concentration

`final_bimm_ro_tsi` joins `final_bimm_ro_epoch_ok` (finality while every slot's
epoch state is within its member's band) and `prob_out_of_band` (the estimate stays
in band except with probability `Ne · bandEps`). The link is `hpick`: a slot whose
epoch is in band (`InB`) is within the band of the member `pick` assigns to its
state, which a certificate checks from the members' exponent ranges
(`slotBand_of_stake`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory ProbabilityTheory
open scoped ENNReal

/-- **Probabilistic finality over many epochs from a random oracle, with the
estimate's concentration.** A finality violation has probability at most
`settleEps2E + Ne · bandEps`. -/
theorem final_bimm_ro_tsi {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {O : Ω → Oracle} {E : Env} (hA : Assm E) (es : Ω → List Event) {N M : ℕ}
    (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {B : Band} {Δ K G : ℕ} {fam : Fin K → Band} (hΔ : E.Δ = Δ) (C : Cert2E B Δ fam E.c.epochLength G)
    (hP : ∀ k, (fam k).Prod) (pick : ℕ → EpochState → Fin K)
    {G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + G' + Δ + 2 ≤ M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1)
    -- the estimate
    {Tb : TBand} (hc : LotConsts E.c Tb.η) (hTb : Tb.OK) (hb : E.c.betaP = E.c.precision)
    (hprec : 0 < E.c.precision) (hPf : 0 < E.c.period * E.c.fP) (hP1 : 1 ≤ E.c.period)
    (hPEL : E.c.period ≤ E.c.epochLength)
    (hst : ∀ ω i, StateOK E Tb i (σE (E.withO (O ω)) (es ω) i))
    (h0 : ∀ ω, InB E Tb (σE (E.withO (O ω)) (es ω)) 0) {Ne : ℕ} (hNe : M / E.c.epochLength < Ne)
    (hrec : ∀ ω e, e + 1 < Ne → Recur E Tb (σE (E.withO (O ω)) (es ω))
      (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e)
    (hpath : ∀ ω e, e + 1 < Ne → StakePath E Tb (σE (E.withO (O ω)) (es ω)) e)
    (hpick : ∀ ω n, n < M → InB E Tb (σE (E.withO (O ω)) (es ω)) ((n + 1) / E.c.epochLength) →
      SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1))) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps2E E B C.P N G G' J Lw r T x yy) +
      Ne * ENNReal.ofReal (bandEps Tb E.c.period) := by
  refine (final_bimm_ro_epoch_ok hA es hNF hdel hO hσm hfresh hΔ C hP pick hx hyy0 hyy1 hT hNM
    hhi1 hlo0 hlo1 helo1).trans (add_le_add le_rfl ?_)
  refine le_trans (measure_mono ?_) (prob_out_of_band hA es hO hσm hfresh hc hTb hb hprec hPf hP1 hPEL hst h0
    hrec hpath)
  rintro ω ⟨n, hn, hnb⟩
  refine ⟨(n + 1) / E.c.epochLength, lt_of_le_of_lt (Nat.div_le_div_right (by omega)) hNe, fun hin => ?_⟩
  exact hnb (hpick ω n hn hin)

/-- **As `final_bimm_ro_tsi`, with an in-epoch contraction** (`Cert3E`): a finality
violation has probability at most `settleEps3E + Ne · bandEps`. -/
theorem final_bimm_ro_tsi3 {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {O : Ω → Oracle} {E : Env} (hA : Assm E) (es : Ω → List Event) {N M : ℕ}
    (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {B : Band} {Δ K G : ℕ} {fam : Fin K → Band} (hΔ : E.Δ = Δ) (D : Cert3E B Δ fam E.c.epochLength G)
    (hP : ∀ k, (fam k).Prod) (pick : ℕ → EpochState → Fin K)
    {G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + G' + Δ + 2 ≤ M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1)
    (hLw : Lw + G < E.c.epochLength)
    -- the estimate
    {Tb : TBand} (hc : LotConsts E.c Tb.η) (hTb : Tb.OK) (hb : E.c.betaP = E.c.precision)
    (hprec : 0 < E.c.precision) (hPf : 0 < E.c.period * E.c.fP) (hP1 : 1 ≤ E.c.period)
    (hPEL : E.c.period ≤ E.c.epochLength)
    (hst : ∀ ω i, StateOK E Tb i (σE (E.withO (O ω)) (es ω) i))
    (h0 : ∀ ω, InB E Tb (σE (E.withO (O ω)) (es ω)) 0) {Ne : ℕ} (hNe : M / E.c.epochLength < Ne)
    (hrec : ∀ ω e, e + 1 < Ne → Recur E Tb (σE (E.withO (O ω)) (es ω))
      (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e)
    (hpath : ∀ ω e, e + 1 < Ne → StakePath E Tb (σE (E.withO (O ω)) (es ω)) e)
    (hpick : ∀ ω n, n < M → InB E Tb (σE (E.withO (O ω)) (es ω)) ((n + 1) / E.c.epochLength) →
      SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1))) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) +
      Ne * ENNReal.ofReal (bandEps Tb E.c.period) := by
  refine (final_bimm_ro_epoch3_ok hA es hNF hdel hO hσm hfresh hΔ D hP pick hx hyy0 hyy1 hT hNM
    hhi1 hlo0 hlo1 helo1 hLw).trans (add_le_add le_rfl ?_)
  refine le_trans (measure_mono ?_) (prob_out_of_band hA es hO hσm hfresh hc hTb hb hprec hPf hP1 hPEL hst h0
    hrec hpath)
  rintro ω ⟨n, hn, hnb⟩
  refine ⟨(n + 1) / E.c.epochLength, lt_of_le_of_lt (Nat.div_le_div_right (by omega)) hNe, fun hin => ?_⟩
  exact hnb (hpick ω n hn hin)

/-- **`Recur` from the canonical chain.** If the canonical prefixes are consistent and
the canonical chain's occupied-slot count in epoch `e`'s window lies between `(1 - μ)`
times the honest occupied slots and all occupied slots plus genesis, the estimate's
update satisfies `Recur` (part 1, `cs_succ_D`). -/
theorem recur_of {E : Env} {es : List Event} {O : Oracle} (hA : Assm E) {Tb : TBand} (X : ℕ → Out) {e : ℕ}
    (hcons : 1 ≤ e → prefixBelow (CP (E.withO O) es (e + 1)) (E.c.cut e) = CP (E.withO O) es e)
    (hlo : (1 - Tb.μ) * hcnt E X e ≤ (occupied E.c (CP (E.withO O) es (e + 1)) e : ℝ))
    (hhi : (occupied E.c (CP (E.withO O) es (e + 1)) e : ℝ) ≤ wcnt E X e + 1) :
    Recur E Tb (σE (E.withO O) es) X e := by
  refine ⟨occupied E.c (CP (E.withO O) es (e + 1)) e, ?_, hlo, hhi⟩
  have hEL : 0 < E.c.epochLength := hA.sane.epochLength_pos
  have h1 : σE (E.withO O) es ((e + 1) * E.c.epochLength) = CS (E.withO O) es (e + 1) := by
    show CS (E.withO O) es ((e + 1) * E.c.epochLength / E.c.epochLength) = _
    rw [Nat.mul_div_cancel _ hEL]
  have h0 : σE (E.withO O) es (e * E.c.epochLength) = CS (E.withO O) es e := by
    show CS (E.withO O) es (e * E.c.epochLength / E.c.epochLength) = _
    rw [Nat.mul_div_cancel _ hEL]
  rw [h1, h0]
  exact cs_succ_D (hA.withO O) hcons

/-- **As `final_bimm_ro_tsi3`, with `Recur` replaced by statements about the canonical
chain:** consistent canonical prefixes (`hcons`; proven on the good event by
`cp_consistent`) and the canonical chain's occupied-slot count between `(1 - μ)` times
the honest occupied slots and all occupied slots plus genesis (`hlo`, `hhi`). -/
theorem final_bimm_ro_tsi4 {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
    {O : Ω → Oracle} {E : Env} (hA : Assm E) (es : Ω → List Event) {N M : ℕ}
    (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {B : Band} {Δ K G : ℕ} {fam : Fin K → Band} (hΔ : E.Δ = Δ) (D : Cert3E B Δ fam E.c.epochLength G)
    (hP : ∀ k, (fam k).Prod) (pick : ℕ → EpochState → Fin K)
    {G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + G' + Δ + 2 ≤ M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1)
    (hLw : Lw + G < E.c.epochLength)
    -- the estimate
    {Tb : TBand} (hc : LotConsts E.c Tb.η) (hTb : Tb.OK) (hb : E.c.betaP = E.c.precision)
    (hprec : 0 < E.c.precision) (hPf : 0 < E.c.period * E.c.fP) (hP1 : 1 ≤ E.c.period)
    (hPEL : E.c.period ≤ E.c.epochLength)
    (hst : ∀ ω i, StateOK E Tb i (σE (E.withO (O ω)) (es ω) i))
    (h0 : ∀ ω, InB E Tb (σE (E.withO (O ω)) (es ω)) 0) {Ne : ℕ} (hNe : M / E.c.epochLength < Ne)
    (hcons : ∀ ω e, e + 1 < Ne → 1 ≤ e →
      prefixBelow (CP (E.withO (O ω)) (es ω) (e + 1)) (E.c.cut e) = CP (E.withO (O ω)) (es ω) e)
    (hlo : ∀ ω e, e + 1 < Ne → (1 - Tb.μ) *
      hcnt E (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e ≤
        (occupied E.c (CP (E.withO (O ω)) (es ω) (e + 1)) e : ℝ))
    (hhi : ∀ ω e, e + 1 < Ne → (occupied E.c (CP (E.withO (O ω)) (es ω) (e + 1)) e : ℝ) ≤
      wcnt E (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e + 1)
    (hpath : ∀ ω e, e + 1 < Ne → StakePath E Tb (σE (E.withO (O ω)) (es ω)) e)
    (hpick : ∀ ω n, n < M → InB E Tb (σE (E.withO (O ω)) (es ω)) ((n + 1) / E.c.epochLength) →
      SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1))) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) +
      Ne * ENNReal.ofReal (bandEps Tb E.c.period) := by
  exact final_bimm_ro_tsi3 hA es hNF hdel hO hσm hfresh hΔ D hP pick hx hyy0 hyy1 hT hNM hhi1 hlo0 hlo1 helo1
    hLw hc hTb hb hprec hPf hP1 hPEL hst h0 hNe
    (fun ω e he => recur_of hA _ (hcons ω e he) (hlo ω e he) (hhi ω e he)) hpath hpick

/-- **Genesis in band, for every execution**: the first epoch runs under the genesis
state, whatever the oracle and the execution. -/
theorem inB0_of_genesis {E : Env} {Tb : TBand} {o : Oracle} {es : List Event}
    (h0 : InB E Tb (fun _ => es0 E) 0) : InB E Tb (σE (E.withO o) es) 0 := by
  intro i h1 h2
  rw [zero_add, one_mul] at h2
  rw [σE_epoch0 (E.withO o) es (by exact h2), es0_withO]
  exact h0 i h1 (by rw [zero_add, one_mul]; exact h2)

/-- Some epoch's canonical prefix, cut at the previous epoch's cut, is not the previous
epoch's canonical prefix. -/
def PrefixesSplit (E : Env) (es : List Event) (Ne : ℕ) : Prop :=
  ∃ e, e + 1 < Ne ∧ 1 ≤ e ∧ prefixBelow (CP E es (e + 1)) (E.c.cut e) ≠ CP E es e

/-- **Probabilistic finality over many epochs, with `hpick`, `hhi` and `hcons` removed.**

As `final_bimm_ro_tsi4`, but:
* the member assignment is constructed (`pickM`): the members' honest-exponent ranges
  cover the estimate's band (`hcov`), each member covers its range (`Member.OK`) with
  room for the adversary (`hadv`), and the honest nodes' online status changes only at
  epoch boundaries (`OnlineEpoch`);
* the canonical chain's occupied-slot count is at most the window's occupied lottery
  slots plus genesis (`occupied_le_wcnt`);
* consistent canonical prefixes are not assumed: the probability that they split,
  `P(PrefixesSplit)`, is a term of the bound;
* genesis being in band is a check on the genesis state alone.

If the canonical prefixes never split, the last term is `0` and the bound is that of
`final_bimm_ro_tsi4`. -/
theorem final_bimm_ro_tsi5 {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ]
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
    (hLw : Lw + G < E.c.epochLength)
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
    (hon : OnlineEpoch E) {mem : Fin (K + 1) → Member} (hfam : ∀ k, (mem k).B = fam k)
    (hok : ∀ k, (mem k).OK Tb.η Tb.ζ)
    (hcov : ∀ y, Tb.ylo ≤ y → y ≤ Tb.Yh → ∃ k, (mem k).ylo ≤ y ∧ y ≤ (mem k).yhi)
    (hadv : ∀ k, Tb.β * (mem k).yhi ≤ (1 - Tb.β) * (mem k).ahi) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) +
      (Ne * ENNReal.ofReal (bandEps Tb E.c.period) + μ {ω | PrefixesSplit (E.withO (O ω)) (es ω) Ne}) := by
  refine (final_bimm_ro_epoch3_ok hA es hNF hdel hO hσm hfresh hΔ D hP (pickM E mem) hx hyy0 hyy1 hT hNM
    hhi1 hlo0 hlo1 helo1 hLw).trans (add_le_add le_rfl ?_)
  have hrec : ∀ ω e, e + 1 < Ne → ω ∉ {ω | PrefixesSplit (E.withO (O ω)) (es ω) Ne} →
      Recur E Tb (σE (E.withO (O ω)) (es ω))
        (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e := by
    intro ω e he hB
    have hc' : 1 ≤ e → prefixBelow (CP (E.withO (O ω)) (es ω) (e + 1)) (E.c.cut e) = CP (E.withO (O ω)) (es ω) e :=
      fun h1 => by by_contra hne; exact hB ⟨e, he, h1, hne⟩
    exact recur_of hA _ hc' (hlo ω e he) (occupied_le_wcnt (hA.withO (O ω)) hc')
  refine le_trans (measure_mono ?_) (prob_out_of_band_bad hA es hO hσm hfresh hc hTb hb hprec hPf hP1 hPEL hst
    (fun ω => inB0_of_genesis h0) _ hrec hpath)
  rintro ω ⟨n, hn, hnb⟩
  refine ⟨(n + 1) / E.c.epochLength, lt_of_le_of_lt (Nat.div_le_div_right (by omega)) hNe, fun hin => ?_⟩
  apply hnb
  have hEL : 0 < E.c.epochLength := hA.sane.epochLength_pos
  have h1 : (n + 1) / E.c.epochLength * E.c.epochLength ≤ n + 1 := Nat.div_mul_le_self _ _
  have h2 : n + 1 < ((n + 1) / E.c.epochLength + 1) * E.c.epochLength := by
    rw [add_mul, one_mul]
    have := Nat.lt_div_mul_add (a := n + 1) hEL
    linarith
  rw [← hfam]
  exact slotBand_pickM hc hTb hA.nodup hon hok hcov hadv (hst ω (n + 1)) (hin (n + 1) h1 h2)

end Cryptarchia.Prob
