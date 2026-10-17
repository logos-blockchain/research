module

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
public import Cryptarchia.Prob.RO
public import Cryptarchia.Prob.WorstE
import Cryptarchia.Prob.ROEpoch
public import Cryptarchia.Prob.TSIRO

/-!
# The lottery law over many epochs, with the band needed only until decided

`lottery_law_epoch_dec`: `law_le_epoch_dec` for the lottery string under a random oracle,
fresh lotteries and Δ-delivery (`Prob/RO`), with slot `n + 1` in the band of the member a
fixed rule picks from its epoch and state (`pick`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory ProbabilityTheory Finset Settle
open scoped ENNReal

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

end Cryptarchia.Prob
