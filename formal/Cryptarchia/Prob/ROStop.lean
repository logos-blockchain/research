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
import Cryptarchia.Prob.WorstStop

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
theorem lottery_law_epoch_dec (hA : Assm E) (es : Ω → List Event) {M : ℕ} (hM : 0 < M)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
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
  have hslots : ∀ ω, slots (lotStr (E.withO (O ω)) (es ω)) M = List.ofFn (fun k : Fin M => X k ω) := hslotsN M
  have hm : ∀ n, hist O σ n ≤ ‹MeasurableSpace Ω› := fun n =>
    sup_le (iSup₂_le fun j _ => (hO.meas j).comap_le) (iSup₂_le fun j _ => (hσm j).comap_le)
  have hTh : ∀ n j, j < n → Measurable[hist O σ n] (tk O j) := fun n j hj =>
    (comap_measurable (tk O j)).mono (le_sup_of_le_left (le_iSup₂_of_le j (Finset.mem_range.2 hj) le_rfl)) le_rfl
  have hσh : ∀ n j, j ≤ n → Measurable[hist O σ n] (fun ω => σ ω j) := fun n j hj =>
    (comap_measurable (fun ω => σ ω j)).mono
      (le_sup_of_le_right (le_iSup₂_of_le j (Finset.mem_range.2 (by omega)) le_rfl)) le_rfl
  have hXm : ∀ j, Measurable (X j) := fun j =>
    (measurable_slotOut₂ E (j + 1)).comp ((hO.meas (j + 1)).prodMk (hσm (j + 1)))
  have hXh : ∀ n j, j < n → Measurable[hist O σ (n + 1)] (X j) := fun n j hj =>
    (measurable_slotOut₂ E (j + 1)).comp ((hTh (n + 1) (j + 1) (by omega)).prodMk (hσh (n + 1) (j + 1) (by omega)))
  set ok : ℕ → Ω → Prop := fun n ω => SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σ ω (n + 1)))) E (n + 1) (σ ω (n + 1)) with hok
  rw [show {ω | slots (lotStr (E.withO (O ω)) (es ω)) M ∈ S ∧ ∀ n < M,
      SlotBand (fam (pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1)))) E (n + 1)
        (σE (E.withO (O ω)) (es ω) (n + 1)) ∨ Decided S M (slots (lotStr (E.withO (O ω)) (es ω)) n)} =
      {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧ ∀ n < M, ok n ω ∨ Decided S M (List.ofFn fun k : Fin n => X k ω)} by
    ext ω; simp only [Set.mem_setOf_eq, hslots ω, hslotsN]; exact Iff.rfl]
  exact law_le_epoch_dec μ hP hM X hXm (fun n => hist O σ (n + 1)) (fun n => hm _)
    (fun j n hjn => hist_mono O σ (by omega)) hXh
    (fun n ω => qhRO E (n + 1) (σ ω (n + 1))) (fun n ω => qaRO E.c (σ ω (n + 1)))
    (fun n ω => pick ((n + 1) / E.c.epochLength) (σ ω (n + 1))) ok
    (fun n _ => (hσh (n + 1) (n + 1) le_rfl) (MeasurableSet.of_discrete
      (s := {s : EpochState | SlotBand (fam (pick ((n + 1) / E.c.epochLength) s)) E (n + 1) s})))
    (fun n hn ω hb => ⟨hb.hon, by unfold qaRO; linarith [loss_le_one hO.pos (σ ω (n + 1)) (advNotes (σ ω (n + 1)))],
        hb.adv⟩)
    (fun n _ => (measurable_of_countable (pick ((n + 1) / E.c.epochLength))).comp (hσh (n + 1) (n + 1) le_rfl))
    (fun n ω hc => by
      show pick ((n + 2) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 2)) =
        pick ((n + 1) / E.c.epochLength) (σE (E.withO (O ω)) (es ω) (n + 1))
      rw [σE_succ (E.withO (O ω)) (es ω) hc, div_succ_of_mod hc])
    (fun n _ o => (measurable_of_countable fun s : EpochState =>
      ENNReal.ofReal (prodLaw (qhRO E (n + 1) s) (qaRO E.c s) o)).comp (hσh (n + 1) (n + 1) le_rfl))
    (fun n hn f hf hf0 o => by
      have h := freeze (m := hist O σ (n + 1)) (μ := μ) (hm _) (hσh (n + 1) (n + 1) le_rfl) (hO.meas (n + 1))
        (hfresh (n + 1)) (g := fun s T => slotOut E (n + 1) s T) (fun s => measurable_slotOut E (n + 1) s) o hf
      refine h.trans (lintegral_congr fun ω => ?_)
      by_cases hω : ok n ω
      · rw [slot_law hO hA.nodup (n + 1) (σ ω (n + 1)) hω.nodup o]
      · rw [hf0 ω hω, zero_mul, zero_mul])
    hS hG

end Cryptarchia.Prob
