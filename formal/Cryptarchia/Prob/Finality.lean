module

public import Cryptarchia.Prob.Drift
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
import Cryptarchia.Prob.FinalTight

/-!
# Finality, from plain assumptions

`finality` restates `finality_tight` with its assumptions as named, readable
conditions on the model and the executions:

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
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory
open scoped ENNReal

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
  ∀ i, StateOK E ⟨0, 0, 0, β, 0, 0, ζ⟩ i (σE (E.withO o) es i)

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

theorem stateOK_of {E : Env} {T : TBand} {i : ℕ} {s : EpochState} (h : StateOK E ⟨0, 0, 0, T.β, 0, 0, T.ζ⟩ i s) :
    StateOK E T i s := ⟨h.nodup, h.smallH, h.smallA, h.frac⟩

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
  have hl : 0 < lam0 E.c := by unfold lam0; have := hc.p_pos; have := hc.t0_pos; positivity
  have hK : 0 < Kc E.c := by
    unfold Kc; have : (0 : ℝ) < E.c.period * E.c.fP := by exact_mod_cast hPf
    exact div_pos (by exact_mod_cast hprec) this
  exact finality_tight hM.assm es hN hM.delivery hM.oracle hM.measurable hM.fresh hΔ D hP hx hyy0 hyy1 hT
    hNM hhi1 hlo0 hlo1 helo1 hLw hOG hc hTb hb hprec hPf hP1 hPEL
    (fun ω i => stateOK_of (E := E) (hS ω i))
    (inB0_of_genesisOK hM.onlineEpoch hG (by linarith [hTb.μ1]) hg1 hg2) hNe (fun ω e he => hQ ω e he)
    (fun ω e he => stakePath_of_drift (E := E) hTb hl hK hP1 hρ hHm (hD ω e he) (hH ω) hup hdn)
    hM.onlineEpoch hM.live hfam hok hcov hadv

end Cryptarchia.Prob
