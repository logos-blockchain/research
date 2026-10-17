module

import Cryptarchia.Prob.Occupied
import Cryptarchia.Proof.Recur
import Cryptarchia.Prob.WorstE
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
public import Cryptarchia.Prob.Final3E
public import Cryptarchia.Prob.Pick

/-!
# Finality over many epochs, from plain assumptions

`finality`: a finality violation has probability at most `settleEps3E + Ne · bandEps`,
with the assumptions as named, readable conditions on the model and the executions:

* `Model`: tickets are a random oracle, each slot's lottery is fresh, honest blocks are
  delivered within `Δ`, nodes only crash, go offline only at epoch boundaries, and some
  honest node is always online;
* `GenesisOK`: the genesis stake estimate is the genesis stake, all of it online;
* `Exec.StakeOK β ζ`: the adversary holds at most a fraction `β` of the participating
  stake, notes are small (`ζ`), note identifiers are distinct;
* `Exec.ChainQuality μ`: at least a fraction `1 - μ` of each epoch window's honestly won
  slots end up on the canonical chain, as blocks or uncles;
* `Exec.StakeDrift ρ`, `Exec.MinStake Hmin`: stake moves by at most a factor `ρ` per
  epoch, and honest online stake is at least `Hmin`.

The remaining hypotheses are numeric facts about a certificate's constants, which a
generated certificate checks.

The member assignment is constructed (`slotBand_pickM`), genesis is in band for every
execution (`inB0_of_genesis`), the estimate's update is proven from the canonical chain
(`recur_of`, `occupied_le_wcnt`), and the canonical
prefixes' consistency is proven: each epoch's split, cut at its horizon, is a robust
failure of the lottery's good event (`split_up`) that decides the finality failure
(`lift_bad`). The splits need the band only up to their own horizons, and one kernel
bound with the band needed only until the event is decided (`lottery_law_epoch_dec`)
covers them and the finality failure together; epochs out of band cost `Ne · bandEps`
(`prob_out_of_band_cover`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory Settle
open scoped ENNReal

section

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
  {E : Env}

open Classical in
/-- **The lottery law over many epochs, with the band needed only until the event is
decided.** Slot `n + 1` needs to be in band only while the first `n` slots do not yet
decide the event. -/
theorem lottery_law_epoch_dec (es : Ω → List Event) {M : ℕ} (hM : 0 < M)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω)) (hAd : SlotLaws μ O E fun ω => σE (E.withO (O ω)) (es ω))
    {K : ℕ} {fam : Fin K → Band} (hP : ∀ b, (fam b).Prod) (pick : ℕ → EpochState → Fin K)
    (hG : (goodB fam).Nonempty) {S : Set (List Out)} (hS : UpClosed S) :
    ∃ κ : Kern, κ.EpochFam E.c.epochLength fam ∧
      μ {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S ∧ ∀ n < M,
        SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
          (σE (E.withO (O ω)) (es ω) (n + 1)) ∨ Decided S M (slots (lotStr (E.withO (O ω)) (es ω)) n)} ≤
        ENNReal.ofReal (Ex κ M (S.indicator 1) []) := by
  set σ : Ω → ℕ → EpochState := fun ω => σE (E.withO (O ω)) (es ω) with hσ
  set X : ℕ → Ω → Out := fun k ω => slotOut E (k + 1) (σ ω (k + 1)) (tk O (k + 1) ω) with hX
  have hslotsN : ∀ n ω, slots (lotStr (E.withO (O ω)) (es ω)) n = List.ofFn (fun k : Fin n => X k ω) := by
    intro n ω
    apply List.ext_getElem (by simp [slots_length])
    intro k h1 h2
    rw [slots_get, List.getElem_ofFn]
    exact enc_lotStr (hdel ω) (k + 1)
  set ok : ℕ → Ω → Prop := fun n ω => SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σ ω (n + 1)))) E (n + 1) (σ ω (n + 1)) with hok
  rw [show {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S ∧ ∀ n < M,
      SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
        (σE (E.withO (O ω)) (es ω) (n + 1)) ∨ Decided S M (slots (lotStr (E.withO (O ω)) (es ω)) n)} =
      {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧ ∀ n < M, ok n ω ∨ Decided S M (List.ofFn fun k : Fin n => X k ω)} by
    ext ω; simp only [Set.mem_setOf_eq, hslotsN]; exact Iff.rfl]
  exact law_le_epoch_dec μ hP hM hAd
    (fun n ω => pick ((n + 1) / E.c.epochLength) (σ ω (n + 1))) ok
    (fun n _ => (measurable_hist_σ O σ (n + 1)) (MeasurableSet.of_discrete
      (s := {s : EpochState | SlotBand (fam (pick ((n + 1) / E.c.epochLength) s)) E (n + 1) s})))
    (fun n _ ω hb => ⟨hb.hon, hb.adv⟩)
    (fun n _ => (measurable_of_countable (pick ((n + 1) / E.c.epochLength))).comp (measurable_hist_σ O σ (n + 1)))
    (fun n ω hc => by
      show pick ((n + 2) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 2)) =
        pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1))
      rw [σE_succ (E.withO (O ω)) (es ω) hc, div_succ_of_mod hc])
    hS hG

end

variable {Ω : Type*} [MeasurableSpace Ω]

/-- **The execution model.** Each `ω` fixes the oracle `O ω` and the execution `es ω`. -/
structure Model (μ : Measure Ω) (O : Ω → Oracle) (E : Env) (es : Ω → List Event) : Prop where
  /-- honest nodes follow the protocol, only crash, have distinct ids; the configuration is sane -/
  assm : Assm E
  /-- honest blocks reach every honest node online throughout the next `Δ` slots -/
  delivery : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω)
  /-- lottery tickets are a random oracle -/
  oracle : RandomOracle μ O E.c.p
  /-- each slot's epoch state is a measurable function of the randomness -/
  measurable : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i
  /-- each slot's tickets are independent of everything before it (no grinding) -/
  fresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω)
  /-- honest nodes go online or offline only at epoch boundaries -/
  onlineEpoch : OnlineEpoch E
  /-- some honest node is online at every slot -/
  live : ∀ t, ∃ j ∈ E.nodes, E.online j t = true

/-- **The genesis estimate is the genesis stake**, all of it online at the first slot. -/
def GenesisOK (E : Env) : Prop :=
  stakeOf (honNotes E 0 (es0 E) E.nodes) + stakeOf (advNotes (es0 E)) = (es0 E).D

namespace Exec

/-- **Honest majority of stake** in every slot's epoch state: the adversary holds at
most a fraction `β` of the participating stake, honest and adversarial notes are small
(`ζ`), and lead note identifiers are distinct. -/
def StakeOK (E : Env) (o : Oracle) (es : List Event) (β ζ : ℝ) : Prop :=
  ∀ i, StateOK E β ζ i (σE (E.withO o) es i)

/-- **Chain quality for the stake estimate**: in each of the first `Ne - 1` epochs, the
canonical chain counts (as block or uncle slots) at least a fraction `1 - μ` of the
window's slots that an online honest node won. -/
def ChainQuality (E : Env) (o : Oracle) (es : List Event) (μ : ℝ) (Ne : ℕ) : Prop :=
  ∀ e, e + 1 < Ne → (1 - μ) *
    hcnt E (fun k => slotOut E (k + 1) (σE (E.withO o) es (k + 1)) (fun η id => o.ticket η (k + 1) id)) e ≤
      (occupied E.c (CP (E.withO o) es (e + 1)) e : ℝ)

/-- **Stake drifts by at most a factor `ρ` per epoch**, over the first `Ne` epochs. -/
def StakeDrift (E : Env) (o : Oracle) (es : List Event) (ρ : ℝ) (Ne : ℕ) : Prop :=
  ∀ e, e + 1 < Ne → Prob.StakeDrift E (σE (E.withO o) es) ρ e

/-- **Honest online stake is at least `Hmin`** at every slot. -/
def MinStake (E : Env) (o : Oracle) (es : List Event) (Hmin : ℝ) : Prop := Prob.MinStake E (σE (E.withO o) es) Hmin

end Exec

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

/-- **Genesis in band, for every execution**: the first epoch runs under the genesis
state, whatever the oracle and the execution. -/
theorem inB0_of_genesis {E : Env} {Tb : TBand} {o : Oracle} {es : List Event}
    (h0 : InB E Tb (fun _ => es0 E) 0) : InB E Tb (σE (E.withO o) es) 0 := by
  intro i h1 h2
  rw [zero_add, one_mul] at h2
  rw [σE_epoch0 (E.withO o) es (by exact h2), es0_withO]
  exact h0 i h1 (by rw [zero_add, one_mul]; exact h2)

/-- **Genesis in band**, from the genesis estimate being the genesis stake. -/
theorem inB0_of_genesisOK {E : Env} {T : TBand} (hon : OnlineEpoch E) (hg : GenesisOK E)
    (hμ : T.μ ≤ 1) (h1 : T.ℓlo ≤ lam0 E.c) (h2 : (1 - T.μ) * lam0 E.c ≤ T.ℓhi) :
    InB E T (fun _ => es0 E) 0 := by
  intro i _ hi
  rw [zero_add, one_mul] at hi
  have hH : hstake E i (es0 E) = hstake E 0 (es0 E) := by
    unfold hstake
    rw [honNotes_congr (i' := 0) (es0 E) fun j hj => by rw [hon j hj i, Nat.div_eq_of_lt hi, zero_mul]]
  have hD : hstake E 0 (es0 E) + astake (es0 E) = (es0 E).D := by
    unfold hstake astake; exact_mod_cast hg
  have hA := astake_nonneg (es0 E)
  have hl := lam0_nonneg E.c
  have hD0 : (0 : ℝ) ≤ (es0 E).D := Nat.cast_nonneg _
  refine ⟨?_, ?_⟩
  · rw [hH]
    calc (1 - T.μ) * (lam0 E.c * hstake E 0 (es0 E)) ≤ (1 - T.μ) * (lam0 E.c * (es0 E).D) :=
          mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_left (by linarith) hl) (by linarith)
      _ = (1 - T.μ) * lam0 E.c * (es0 E).D := by ring
      _ ≤ T.ℓhi * (es0 E).D := mul_le_mul_of_nonneg_right h2 hD0
  · rw [hH, hD]
    exact mul_le_mul_of_nonneg_right h1 hD0

/-- **Probabilistic finality over many epochs, from plain assumptions.** Under the
execution model, executions up to slot `N`, the genesis condition, honest majority of
stake `β`, chain quality `μ`, stake drift `ρ` and minimum honest stake `Hmin`, a finality
violation has probability at most `settleEps3E + Ne · bandEps`, for any
certificate (`D`, the band `Tb`, the members `mem`) whose numeric conditions hold. -/
theorem finality {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle} {E : Env}
    (es : Ω → List Event) (hM : Model μ O E es) {N : ℕ} (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    -- the certificate
    {M : ℕ} {B : Band} {Δ K G : ℕ} {fam : Fin (K + 1) → Band} (hΔ : E.Δ = Δ) (D : Cert3E B Δ fam E.c.epochLength G)
    (hP : ∀ k, (fam k).Prod)
    {G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + G' + Δ + 2 ≤ M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1)
    (hLw : Lw + G < E.c.epochLength) (hOG : E.c.nonceOffset + G + 2 ≤ E.c.epochLength)
    {Tb : TBand} (hc : LotConsts E.c Tb.η) (hTb : Tb.OK) (hb : E.c.betaP = E.c.precision)
    (hprec : 0 < E.c.precision) (hPf : 0 < E.c.period * E.c.fP) (hP1 : 1 ≤ E.c.period)
    (hPEL : E.c.period ≤ E.c.epochLength) {Ne : ℕ} (hNe : M / E.c.epochLength < Ne)
    {mem : Fin (K + 1) → Member} (hfam : ∀ k, (mem k).B = fam k) (hok : ∀ k, (mem k).OK Tb.η Tb.ζ)
    (hcov : ∀ y, Tb.ylo ≤ y → y ≤ Tb.Yh → ∃ k, (mem k).ylo ≤ y ∧ y ≤ (mem k).yhi)
    (hadv : ∀ k, Tb.β * (mem k).yhi ≤ (1 - Tb.β) * (mem k).ahi)
    {ρ Hmin : ℝ} (hρ : 0 < ρ) (hHm : 0 < Hmin)
    (hup : (1 - Tb.μ) + 2 * Tb.ℓhi / (lam0 E.c * Hmin) ≤
      Tb.ℓhi * Kc E.c * (1 - Tb.μ) * (1 - Tb.δ) * Tb.clo * ((E.c.period : ℝ) - 1) / ρ)
    (hdn : Tb.ℓlo * Kc E.c * (1 + Tb.δ) * Tb.chi * E.c.period * ρ + Kc E.c * ρ + 3 * Tb.ℓlo / (lam0 E.c * Hmin) ≤ 1)
    (hg1 : Tb.ℓlo ≤ lam0 E.c) (hg2 : (1 - Tb.μ) * lam0 E.c ≤ Tb.ℓhi)
    -- the assumptions on the executions
    (hG : GenesisOK E) (hS : ∀ ω, Exec.StakeOK E (O ω) (es ω) Tb.β Tb.ζ)
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) Tb.μ Ne)
    (hD : ∀ ω, Exec.StakeDrift E (O ω) (es ω) ρ Ne) (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) Hmin) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps3E E B D.C.P D.lpi G N G G' J Lw r T x yy) +
      Ne * ENNReal.ofReal (bandEps Tb E.c.period) := by
  classical
  obtain ⟨hA, hdel, hO, hσm, hfresh, hon, hlive⟩ := hM
  have hAd := SlotLaws.ofRO hA.nodup hO hσm hfresh fun ω i => (hS ω i).nodup
  have hEL : 0 < E.c.epochLength := hA.sane.epochLength_pos
  have hl : 0 < lam0 E.c := by unfold lam0; have := hc.p_pos; have := hc.t0_pos; positivity
  have hK : 0 < Kc E.c := by
    unfold Kc; have : (0 : ℝ) < E.c.period * E.c.fP := by exact_mod_cast hPf
    exact div_pos (by exact_mod_cast hprec) this
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
    exact slotBand_pickM hc hTb hA.nodup hon hok hcov hadv (hS ω (n + 1)) (hin (n + 1) h1 h2)
  -- the events on outcome lists: the main failure, decided by any epoch's split
  set S := RBad E N M Lw r G
  set Nh : ℕ → ℕ := fun e => min (E.c.fix (e + 1)) N with hNh
  have hgr : ∀ e, ∀ ep, 1 ≤ ep → E.c.fix ep ≤ Nh e → E.c.cut ep + G < Nh e + 1 :=
    fun e => cut_add_lt hA.sane hOG (Nat.lt_succ_self _)
  have hNhe : ∀ e, Nh e = min (E.c.fix (e + 1)) N := fun e => rfl
  have hNM' : ∀ e, Nh e + 1 ≤ M := fun e => by have := min_le_right (E.c.fix (e + 1)) N; rw [hNhe]; omega
  have hdec : ∀ e w, slots w (Nh e + 1) ∈ RBad E (Nh e) (Nh e + 1) Lw r G →
      ∀ n, Nh e + 1 ≤ n → Decided S M (slots w n) := fun e w h n hn => by
    rw [← List.take_append_drop (Nh e + 1) (slots w n), slots_take _ hn]
    exact (lift_bad E (min_le_right _ _) (Nat.lt_succ_self _) (hNM' e) (hgr e) (slots_length _ _) h).append _
  -- the update holds off the split sets
  set Bad : ℕ → Set Ω := fun e => {ω | 1 ≤ e ∧
    prefixBelow (CP (E.withO (O ω)) (es ω) (e + 1)) (E.c.cut e) ≠ CP (E.withO (O ω)) (es ω) e} with hBad
  have hrec : ∀ ω e, e + 1 < Ne → ω ∉ Bad e →
      Recur E Tb (σE (E.withO (O ω)) (es ω))
        (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e := by
    intro ω e he hB
    have hc' : 1 ≤ e → prefixBelow (CP (E.withO (O ω)) (es ω) (e + 1)) (E.c.cut e) = CP (E.withO (O ω)) (es ω) e :=
      fun h1 => by by_contra hne; exact hB ⟨h1, hne⟩
    exact recur_of hA _ hc' (hQ ω e he) (occupied_le_wcnt (hA.withO (O ω)) hc')
  set Tset : Set Ω := {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S ∧ ∀ n < M, band ω n} with hTset
  -- an unsafe execution: the main event in band, or some epoch out of band
  have h1 : {ω | Unsafe (E.withO (O ω)) (es ω)} ⊆ Tset ∪ {ω | ∃ e < Ne, ¬ InB E Tb (σE (E.withO (O ω)) (es ω)) e} := by
    intro ω hU
    by_cases hb : ∀ n < M, band ω n
    · exact Or.inl ⟨unsafe_up E hA (hN ω) (by omega) hU, hb⟩
    · refine Or.inr ?_
      push Not at hb
      obtain ⟨n, hn, hnb⟩ := hb
      exact ⟨(n + 1) / E.c.epochLength, lt_of_le_of_lt (Nat.div_le_div_right (by omega)) hNe,
        fun hin => hnb (hbandOf ω n hin)⟩
  refine (measure_mono h1).trans ((prob_out_of_band_cover es hAd hc hTb hb hprec hPf hP1 hPEL hS
    (fun ω => inB0_of_genesis (inB0_of_genesisOK hon hG (by linarith [hTb.μ1]) hg1 hg2)) Bad hrec
    (fun ω e he => stakePath_of_drift hTb hl hK hP1 hρ hHm (hD ω e he) (hH ω) hup hdn) Tset).trans
    (add_le_add ?_ le_rfl))
  -- the main event and the splits, in band until decided
  by_cases hgood : (goodB fam).Nonempty
  · obtain ⟨κ, hκ, hbound⟩ := lottery_law_epoch_dec (M := M) es (by omega) hdel hAd hP (pickM E mem) hgood
      (RBad.upClosed E)
    refine (measure_mono ?_).trans (hbound.trans (ENNReal.ofReal_le_ofReal ?_))
    · rintro ω (⟨hS, hb⟩ | hω)
      · exact ⟨hS, fun n hn => Or.inl (hb n hn)⟩
      · simp only [Set.mem_iUnion, Finset.mem_range] at hω
        obtain ⟨e, -, ⟨h1e, hsp⟩, hin⟩ := hω
        have hsplit := split_up E hA hlive (Lw := Lw) (r := r) (hN ω) h1e (Nat.lt_succ_self _) (hgr e) hsp
        refine ⟨(hdec e _ hsplit M (hNM' e)).mem (slots_length _ _), fun n hn => ?_⟩
        by_cases hns : n < Nh e + 1
        · left
          have hfx : E.c.fix (e + 1) + 2 ≤ (e + 1) * E.c.epochLength := (hA.sane.fix_ok (e + 1) (by omega)).2
          have hmin := min_le_left (E.c.fix (e + 1)) N
          have hlt : n + 1 < (e + 1) * E.c.epochLength := by rw [hNhe] at hns; omega
          have hm : (n + 1) / E.c.epochLength ≤ e := by
            have := (Nat.div_lt_iff_lt_mul hEL).2 hlt
            omega
          exact hbandOf ω n (hin _ hm)
        · exact Or.inr (hdec e _ hsplit n (by omega))
    refine le_trans ?_ (settle_bound3E E rfl hA.sane D.C.P (D.C.within hκ) D.C.hG (D.bounds hκ) (D.inEpoch hκ hLw)
      hx hyy0 hyy1 hT hNM hhi1 hlo0 hlo1 helo1)
    apply Ex_mono_len
    intro t _
    simp only [List.nil_append]
    by_cases ht : t ∈ S
    · rw [Set.indicator_of_mem ht, if_neg (ht t (forall₂_refl t))]; rfl
    · rw [Set.indicator_of_notMem ht]
      split_ifs <;> norm_num
  · -- no member has a nonempty polytope: nothing is in band, not even slot `1`
    have hnone : ∀ ω, ¬ band ω 0 := fun ω hb => hgood ⟨_, mem_goodB.2 ⟨_, hb.hon⟩⟩
    refine (measure_mono (t := ∅) fun ω hω => ?_).trans (by rw [measure_empty]; exact zero_le)
    rcases hω with ⟨-, hb⟩ | hω
    · exact hnone ω (hb 0 (by omega))
    · simp only [Set.mem_iUnion, Finset.mem_range] at hω
      obtain ⟨e, -, -, hin⟩ := hω
      exact hnone ω (hbandOf ω 0 (by rw [Nat.div_eq_of_lt (by omega)]; exact hin 0 (Nat.zero_le _)))

end Cryptarchia.Prob
