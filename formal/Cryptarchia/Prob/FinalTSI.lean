import Cryptarchia.Prob.Final2E
import Cryptarchia.Prob.Final3E
import Cryptarchia.Prob.TSIRO

/-!
# Probabilistic finality over many epochs, with the stake estimate's concentration

`final_bimm_ro_tsi` joins `final_bimm_ro_epoch_ok` (finality while every slot's
epoch state is within its member's band) and `prob_out_of_band` (the estimate stays
in band except with probability `Ne · bandEps`). The link is `hpick`: a slot whose
epoch is in band (`InB`) is within the band of the member `pick` assigns to its
state, which a certificate checks from the members' exponent ranges
(`slotBand_of_stake`).
-/

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
    (hP : ∀ k, (fam k).Prod) (pick : EpochState → Fin K)
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
      SlotBand (fam (pick (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1))) :
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
    (hP : ∀ k, (fam k).Prod) (pick : EpochState → Fin K)
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
      SlotBand (fam (pick (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1) (σE (E.withO (O ω)) (es ω) (n + 1))) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) +
      Ne * ENNReal.ofReal (bandEps Tb E.c.period) := by
  refine (final_bimm_ro_epoch3_ok hA es hNF hdel hO hσm hfresh hΔ D hP pick hx hyy0 hyy1 hT hNM
    hhi1 hlo0 hlo1 helo1 hLw).trans (add_le_add le_rfl ?_)
  refine le_trans (measure_mono ?_) (prob_out_of_band hA es hO hσm hfresh hc hTb hb hprec hPf hP1 hPEL hst h0
    hrec hpath)
  rintro ω ⟨n, hn, hnb⟩
  refine ⟨(n + 1) / E.c.epochLength, lt_of_le_of_lt (Nat.div_le_div_right (by omega)) hNe, fun hin => ?_⟩
  exact hnb (hpick ω n hn hin)

end Cryptarchia.Prob
