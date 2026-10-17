module

public import Cryptarchia.Prob.WorstE
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

/-!
# The per-epoch worst case, with the band needed only until the event is decided

`law_le_epoch_dec`: suppose that, given the past, each slot's outcome has the law
`qh ⊗ Bern(qa)`, with `qh` in the honest polytope and `qa ≤ amax` of a family member
that is known before the slot and changes only at epoch starts. Then every event `S`
closed under adding adversarial slots is at most as likely as under the per-epoch
worst-case kernel (`worstKE`). The band condition is needed at slot `n` only while the
event is still undecided: once the first `n` outcomes decide `S` (`Decided`), the
indicator is `1` whatever happens next, so no law is needed for the remaining slots.

This lets one kernel bound cover events that each need the band only up to their own
horizon: the per-epoch consistency failures and the final finality failure together.
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory Finset
open scoped ENNReal

/-- **The worst case of an event certain from `l` is at least one.** -/
theorem VE_ge_one {K : ℕ} {fam : Fin K → Band} {EL : ℕ} {F : List Out → ℝ} {hG : (goodB fam).Nonempty}
    (hP : ∀ b, (fam b).Prod) :
    ∀ n (l : List Out) (b : Fin K), b ∈ goodB fam → (∀ y : List Out, y.length = n → 1 ≤ F (l ++ y)) →
      1 ≤ VE EL F hG n l b
  | 0, l, _, _, h => by show 1 ≤ F l; simpa using h [] rfl
  | n + 1, l, b, hb, h => by
    obtain ⟨q, hq, hW, -⟩ := VE_attain (F := F) (EL := EL) (hG := hG) hb n l
    rw [hW]
    have hnext : ∀ o, 1 ≤ nextV EL hG (VE EL F hG n) (l ++ [o]) b := by
      intro o
      have hih : ∀ b', b' ∈ goodB fam → 1 ≤ VE EL F hG n (l ++ [o]) b' := fun b' hb' =>
        VE_ge_one (hG := hG) hP n (l ++ [o]) b' hb' fun y hy => by
          have := h (o :: y) (by simp [hy]); simpa using this
      unfold nextV
      split_ifs
      · obtain ⟨b0, hb0⟩ := id hG
        exact le_trans (hih b0 hb0) (Finset.le_sup' (fun b' => VE EL F hG n (l ++ [o]) b') hb0)
      · exact hih b hb
    calc (1 : ℝ) = ∑ o, prodLaw q (fam b).amax o * 1 := by
          simp only [mul_one]; exact (sum_prodLaw_one hq.2.1 _).symm
      _ ≤ _ := Finset.sum_le_sum fun o _ =>
          mul_le_mul_of_nonneg_left (hnext o) (prodLaw_nonneg hq.1 (hP b).a0 (hP b).a1 o)

set_option maxHeartbeats 1600000 in
/-- **From conditional slot laws to a kernel, with the band needed only until the event
is decided.** The condition at slot `n` is `ok n` or that the first `n` outcomes already
decide the event. -/
theorem law_le_epoch_dec {Ω : Type*} [mΩ : MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ]
    {K : ℕ} {fam : Fin K → Band} (hP : ∀ b, (fam b).Prod) {EL M : ℕ} (hM : 0 < M)
    (X : ℕ → Ω → Out) (hXm : ∀ j, Measurable (X j))
    (m : ℕ → MeasurableSpace Ω) (hm : ∀ n, m n ≤ mΩ) (hmono : ∀ j n, j ≤ n → m j ≤ m n)
    (hX : ∀ n j, j < n → Measurable[m n] (X j))
    (qh : ℕ → Ω → Fin 3 → ℝ) (qa : ℕ → Ω → ℝ) (Bsel : ℕ → Ω → Fin K)
    (ok : ℕ → Ω → Prop) (hokm : ∀ n < M, MeasurableSet[m n] {ω | ok n ω})
    (hQ : ∀ n < M, ∀ ω, ok n ω → qh n ω ∈ HB (fam (Bsel n ω)) ∧ 0 ≤ qa n ω ∧ qa n ω ≤ (fam (Bsel n ω)).amax)
    (hBm : ∀ n < M, Measurable[m n] (Bsel n))
    (hBc : ∀ n ω, (n + 2) % EL ≠ 0 → Bsel (n + 1) ω = Bsel n ω)
    (hQm : ∀ n < M, ∀ o, Measurable[m n] fun ω => ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o))
    (hcond : ∀ n < M, ∀ f : Ω → ℝ≥0∞, Measurable[m n] f → (∀ ω, ¬ ok n ω → f ω = 0) → ∀ o,
      ∫⁻ ω, f ω * (if X n ω = o then 1 else 0) ∂μ =
        ∫⁻ ω, f ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ)
    {S : Set (List Out)} (hS : UpClosed S) (hG : (goodB fam).Nonempty) :
    ∃ κ : Kern, κ.EpochFam EL fam ∧
      μ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧
          ∀ n < M, ok n ω ∨ Decided S M (List.ofFn fun k : Fin n => X k ω)} ≤
        ENNReal.ofReal (Ex κ M (S.indicator 1) []) := by
  classical
  set Dd : List Out → Prop := Decided S M with hDd
  set F : List Out → ℝ := S.indicator 1 with hFdef
  have hF0 : ∀ l, 0 ≤ F l := fun l => Set.indicator_nonneg (fun _ _ => zero_le_one) l
  have hFm : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l' := by
    intro l l' h
    by_cases hl : l ∈ S
    · rw [hFdef, Set.indicator_of_mem hl, Set.indicator_of_mem (hS l l' h hl)]; exact le_rfl
    · rw [hFdef, Set.indicator_of_notMem hl]; exact hF0 l'
  refine ⟨worstKE EL F hG hP M, worstKE_epochFam hP M, ?_⟩
  set pre : ℕ → Ω → List Out := fun n ω => List.ofFn fun k : Fin n => X k ω with hpre
  have hpre_succ : ∀ n ω, pre (n + 1) ω = pre n ω ++ [X n ω] := by
    intro n ω; simp only [hpre]; rw [List.ofFn_succ_last]; simp
  have hpre_len : ∀ n ω, (pre n ω).length = n := fun n ω => by simp [hpre]
  -- a decided prefix of length `n`: every continuation to length `M` lies in `S`
  have hD1 : ∀ n ω, n ≤ M → Dd (pre n ω) → ∀ y : List Out, y.length = M - n → 1 ≤ F (pre n ω ++ y) := by
    intro n ω hn hd y hy
    rw [hFdef, Set.indicator_of_mem (hd y (by rw [hpre_len]; omega))]; simp
  set A : ℕ → Set Ω := fun n => {ω | ∀ j < n, ok j ω ∨ Dd (pre j ω)} with hAdef
  have hvec : ∀ n, Measurable[m n] (fun ω (k : Fin n) => X k ω) :=
    fun n => by letI := m n; exact measurable_pi_iff.mpr fun k : Fin n => hX n k.val k.2
  have hDm : ∀ n, MeasurableSet[m n] {ω | Dd (pre n ω)} := by
    intro n
    have : {ω | Dd (pre n ω)} = (fun ω (k : Fin n) => X k ω) ⁻¹' {v | Dd (List.ofFn v)} := rfl
    rw [this]
    exact hvec n (Set.toFinite _).measurableSet
  have hAm : ∀ n, n ≤ M → MeasurableSet[m n] (A n) := by
    intro n hn
    have : A n = ⋂ j ∈ Finset.range n, ({ω | ok j ω} ∪ {ω | Dd (pre j ω)}) := by ext ω; simp [hAdef]
    rw [this]
    exact Finset.measurableSet_biInter _ fun j hj => by
      have hj' := Finset.mem_range.1 hj
      exact (hmono j n hj'.le _ (hokm j (by omega))).union (hmono j n hj'.le _ (hDm j))
  have hAsucc : ∀ n, A (n + 1) = A n ∩ ({ω | ok n ω} ∪ {ω | Dd (pre n ω)}) := by
    intro n; ext ω; simp only [hAdef, Set.mem_setOf_eq, Set.mem_inter_iff, Set.mem_union]
    constructor
    · intro h; exact ⟨fun j hj => h j (by omega), h n (by omega)⟩
    · rintro ⟨h1, h2⟩ j hj
      rcases Nat.lt_or_ge j n with h | h
      · exact h1 j h
      · rw [show j = n by omega]; exact h2
  -- the value: one once decided, the worst case otherwise
  set V : ℕ → Ω → ℝ≥0∞ := fun n ω => if Dd (pre n ω) then 1 else
    ENNReal.ofReal (VE EL F hG (M - n) (pre n ω) (Bsel n ω)) with hVdef
  set I : ℕ → ℝ≥0∞ := fun n => ∫⁻ ω, (A n).indicator (V n) ω ∂μ with hI
  have hstep : ∀ n, n < M → I (n + 1) ≤ I n := by
    intro n hn
    obtain ⟨k, hk⟩ : ∃ k, M - n = k + 1 := ⟨M - (n + 1), by omega⟩
    have hk' : M - (n + 1) = k := by omega
    have hAn := hAm n hn.le
    have hokn := hokm n hn
    have hDn := hDm n
    set U : Set Ω := A n ∩ {ω | ok n ω} ∩ {ω | Dd (pre n ω)}ᶜ with hU
    have hUm : MeasurableSet[m n] U := (hAn.inter hokn).inter hDn.compl
    set f : Out → Ω → ℝ≥0∞ := fun o ω => U.indicator (fun ω =>
      ENNReal.ofReal (nextV EL hG (VE EL F hG k) (pre n ω ++ [o]) (Bsel n ω))) ω with hf
    have hpair : Measurable[m n] (fun ω => ((fun k : Fin n => X k ω), Bsel n ω)) := by
      letI := m n; exact (hvec n).prodMk (hBm n hn)
    have hfm : ∀ o, Measurable[m n] (f o) := fun o => by
      letI := m n
      exact ((measurable_of_countable (fun p : (Fin n → Out) × Fin K =>
        ENNReal.ofReal (nextV EL hG (VE EL F hG k) (List.ofFn p.1 ++ [o]) p.2))).comp hpair).indicator hUm
    have hf0 : ∀ o ω, ¬ ok n ω → f o ω = 0 := fun o ω hω => by
      simp only [hf, Set.indicator, hU, Set.mem_inter_iff, Set.mem_setOf_eq]; rw [if_neg (fun h => hω h.1.2)]
    have hind : ∀ o, Measurable fun ω => (if X n ω = o then (1 : ℝ≥0∞) else 0) := fun o =>
      (measurable_of_countable (fun x : Out => if x = o then (1 : ℝ≥0∞) else 0)).comp (hXm n)
    set W : Set Ω := A n ∩ {ω | Dd (pre n ω)} with hW
    have hWm : MeasurableSet W := (hm n) _ (hAn.inter hDn)
    -- pointwise: the decided part carries over; the rest is bounded through the law
    have hnext : ∀ ω, (A (n + 1)).indicator (V (n + 1)) ω ≤
        W.indicator (V n) ω + ∑ o, f o ω * (if X n ω = o then 1 else 0) := by
      intro ω
      have hsum : ∑ o, f o ω * (if X n ω = o then 1 else 0) = f (X n ω) ω := by
        simp only [mul_ite, mul_one, mul_zero, Finset.sum_ite_eq, Finset.mem_univ, ↓reduceIte]
      rw [hsum]
      by_cases hd : Dd (pre n ω)
      · -- decided: the value stays one
        have hd' : Dd (pre (n + 1) ω) := by rw [hpre_succ]; exact Decided.append hd _
        by_cases hA : ω ∈ A n
        · have hA1 : ω ∈ A (n + 1) := by rw [hAsucc]; exact ⟨hA, Or.inr hd⟩
          rw [Set.indicator_of_mem hA1, Set.indicator_of_mem (show ω ∈ W from ⟨hA, hd⟩)]
          simp only [hVdef, if_pos hd', if_pos hd]
          exact le_self_add
        · have hA1 : ω ∉ A (n + 1) := by rw [hAsucc]; exact fun h => hA h.1
          rw [Set.indicator_of_notMem hA1]; exact zero_le
      · by_cases hω : ω ∈ U
        · have hA1 : ω ∈ A (n + 1) := by rw [hAsucc]; exact ⟨hω.1.1, Or.inl hω.1.2⟩
          rw [Set.indicator_of_mem hA1]
          refine le_trans ?_ le_add_self
          simp only [hf, Set.indicator_of_mem hω]
          have hgood : Bsel n ω ∈ goodB fam := mem_goodB.2 ⟨_, (hQ n hn ω hω.1.2).1⟩
          by_cases hd1 : Dd (pre (n + 1) ω)
          · -- decided at the next slot: the worst case is at least one
            simp only [hVdef, if_pos hd1]
            rw [← ENNReal.ofReal_one]
            refine ENNReal.ofReal_le_ofReal ?_
            have hone : ∀ b', b' ∈ goodB fam → 1 ≤ VE EL F hG k (pre n ω ++ [X n ω]) b' := fun b' hb' =>
              VE_ge_one hP k _ b' hb' fun y hy => by
                rw [← hpre_succ]; exact hD1 (n + 1) ω (by omega) hd1 y (by omega)
            unfold nextV
            split_ifs
            · exact le_trans (hone _ hgood) (Finset.le_sup' (fun b' => VE EL F hG k _ b') hgood)
            · exact hone _ hgood
          · simp only [hVdef, if_neg hd1]
            rw [hk', hpre_succ]
            refine ENNReal.ofReal_le_ofReal ?_
            unfold nextV
            simp only [List.length_append, hpre_len, List.length_singleton]
            split_ifs with hc
            · obtain ⟨b0, hb0⟩ := id hG
              cases k with
              | zero => exact Finset.le_sup' (fun b' => VE EL F hG 0 _ b') hb0
              | succ k =>
              by_cases hgood' : Bsel (n + 1) ω ∈ goodB fam
              · exact Finset.le_sup' (fun b' => VE EL F hG (k + 1) _ b') hgood'
              · have : VE EL F hG (k + 1) (pre n ω ++ [X n ω]) (Bsel (n + 1) ω) ≤ 0 := by
                  rw [VE_bad hgood']
                exact le_trans this (le_trans (VE_nonneg hP hF0 (k + 1) _ b0)
                  (Finset.le_sup' (fun b' => VE EL F hG (k + 1) _ b') hb0))
            · rw [hBc n ω (by omega)]
        · have hA1 : ω ∉ A (n + 1) := by
            rw [hAsucc]; rintro ⟨hA, h | h⟩
            · exact hω ⟨⟨hA, h⟩, hd⟩
            · exact hd h
          rw [Set.indicator_of_notMem hA1]; exact zero_le
    calc I (n + 1) ≤ ∫⁻ ω, (W.indicator (V n) ω + ∑ o, f o ω * (if X n ω = o then 1 else 0)) ∂μ := by
          simp only [hI]; exact lintegral_mono fun ω => hnext ω
      _ = ∫⁻ ω, W.indicator (V n) ω ∂μ + ∫⁻ ω, ∑ o, f o ω * (if X n ω = o then 1 else 0) ∂μ := by
          refine lintegral_add_right _ ?_
          exact Finset.measurable_sum _ fun o _ => ((hfm o).mono (hm n) le_rfl).mul (hind o)
      _ = ∫⁻ ω, W.indicator (V n) ω ∂μ + ∑ o, ∫⁻ ω, f o ω * (if X n ω = o then 1 else 0) ∂μ := by
          congr 1
          exact lintegral_finsetSum _ fun o _ => ((hfm o).mono (hm n) le_rfl).mul (hind o)
      _ = ∫⁻ ω, W.indicator (V n) ω ∂μ + ∑ o, ∫⁻ ω, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ := by
          congr 1
          exact Finset.sum_congr rfl fun o _ => hcond n hn (f o) (hfm o) (hf0 o) o
      _ = ∫⁻ ω, W.indicator (V n) ω ∂μ + ∫⁻ ω, ∑ o, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ := by
          congr 1
          exact (lintegral_finsetSum _ fun o _ => (((hfm o).mul (hQm n hn o))).mono (hm n) le_rfl).symm
      _ ≤ ∫⁻ ω, W.indicator (V n) ω ∂μ + ∫⁻ ω, U.indicator (V n) ω ∂μ := by
          gcongr with ω
          by_cases hω : ω ∈ U
          · obtain ⟨hq, ha0, ha⟩ := hQ n hn ω hω.1.2
            have ha1 : qa n ω ≤ 1 := le_trans ha (hP _).a1
            have hnn : ∀ o, 0 ≤ prodLaw (qh n ω) (qa n ω) o *
                nextV EL hG (VE EL F hG k) (pre n ω ++ [o]) (Bsel n ω) :=
              fun o => mul_nonneg (prodLaw_nonneg hq.1 ha0 ha1 o) (nextV_nonneg (VE_nonneg hP hF0 k) _ _)
            rw [Set.indicator_of_mem hω]
            calc ∑ o, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o)
                = ENNReal.ofReal (∑ o, prodLaw (qh n ω) (qa n ω) o *
                    nextV EL hG (VE EL F hG k) (pre n ω ++ [o]) (Bsel n ω)) := by
                  rw [ENNReal.ofReal_sum_of_nonneg fun o _ => hnn o]
                  refine Finset.sum_congr rfl fun o _ => ?_
                  simp only [hf, Set.indicator_of_mem hω]
                  rw [mul_comm, ENNReal.ofReal_mul (prodLaw_nonneg hq.1 ha0 ha1 o)]
              _ ≤ V n ω := by
                  have hnd : ¬ Dd (pre n ω) := hω.2
                  show _ ≤ (if Dd (pre n ω) then 1 else ENNReal.ofReal (VE EL F hG (M - n) (pre n ω) (Bsel n ω)))
                  rw [if_neg hnd, hk]
                  exact ENNReal.ofReal_le_ofReal (stepE_le hP hFm hq ha k _)
          · have : ∀ o, f o ω = 0 := fun o => by simp only [hf]; rw [Set.indicator_of_notMem hω]
            simp only [this, zero_mul, Finset.sum_const_zero]
            exact zero_le
      _ = ∫⁻ ω, (W ∪ U).indicator (V n) ω ∂μ := by
          have hdisj : Disjoint W U := by
            rw [Set.disjoint_left]; intro ω h1 h2; exact h2.2 h1.2
          rw [Set.indicator_union_of_disjoint hdisj, lintegral_add_left]
          exact (measurable_of_countable (fun p : (Fin n → Out) × Fin K => (if Dd (List.ofFn p.1) then (1 : ℝ≥0∞)
            else ENNReal.ofReal (VE EL F hG (M - n) (List.ofFn p.1) p.2)))).comp
              (hpair.mono (hm n) le_rfl) |>.indicator hWm
      _ ≤ I n := by
          simp only [hI]
          refine lintegral_mono fun ω => Set.indicator_le_indicator_of_subset ?_ (fun _ => zero_le) ω
          rintro ω (h | h)
          · exact h.1
          · exact h.1.1
  have hchain : ∀ n ≤ M, I n ≤ I 0 := by
    intro n hn
    induction n with
    | zero => exact le_rfl
    | succ n ih => exact (hstep n (by omega)).trans (ih (by omega))
  have h0 : I 0 ≤ ENNReal.ofReal (Ex (worstKE EL F hG hP M) M F []) := by
    rw [worstKE_Ex hP M [] (by simp)]
    have hA0 : A 0 = Set.univ := by ext ω; simp [hAdef]
    have hmem : memE EL F hG M [] = argB EL F hG M [] := by rw [memE]; simp
    have hsup : ∀ b, b ∈ goodB fam → VE EL F hG M [] b ≤ VE EL F hG M [] (memE EL F hG M []) := fun b hb => by
      rw [hmem, ← sup'_eq_argB]; exact Finset.le_sup' (fun b => VE EL F hG M [] b) hb
    simp only [hI, hA0, Set.indicator_univ, hVdef, Nat.sub_zero]
    have hpre0 : ∀ ω, pre 0 ω = [] := fun ω => by simp [hpre]
    calc ∫⁻ ω, (if Dd (pre 0 ω) then 1 else ENNReal.ofReal (VE EL F hG M (pre 0 ω) (Bsel 0 ω))) ∂μ
        ≤ ∫⁻ _, ENNReal.ofReal (VE EL F hG M [] (memE EL F hG M [])) ∂μ := by
          refine lintegral_mono fun ω => ?_
          rw [hpre0]
          obtain ⟨b0, hb0⟩ := id hG
          split_ifs with hd
          · rw [← ENNReal.ofReal_one]
            refine ENNReal.ofReal_le_ofReal (le_trans (VE_ge_one hP M [] b0 hb0 fun y hy => ?_) (hsup b0 hb0))
            have := hD1 0 ω (Nat.zero_le _) (by rw [hpre0]; exact hd) y (by omega)
            rwa [hpre0] at this
          · refine ENNReal.ofReal_le_ofReal ?_
            by_cases hg : Bsel 0 ω ∈ goodB fam
            · exact hsup _ hg
            · obtain ⟨M', rfl⟩ : ∃ M', M = M' + 1 := ⟨M - 1, by omega⟩
              rw [VE_bad hg]
              exact le_trans (VE_nonneg hP hF0 _ _ b0) (hsup b0 hb0)
      _ = _ := by rw [lintegral_const, measure_univ, mul_one]
  have hMle : μ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧
      ∀ n < M, ok n ω ∨ Dd (List.ofFn fun k : Fin n => X k ω)} ≤ I M := by
    have hv : Measurable (fun ω (k : Fin M) => X k ω) := measurable_pi_iff.mpr fun k : Fin M => hXm k.val
    have hms1 : MeasurableSet {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} :=
      hv (Set.toFinite {v : Fin M → Out | List.ofFn v ∈ S}).measurableSet
    have hms : MeasurableSet {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧
        ∀ n < M, ok n ω ∨ Dd (List.ofFn fun k : Fin n => X k ω)} :=
      hms1.inter ((hm M) _ (hAm M le_rfl))
    rw [← lintegral_indicator_one hms]
    simp only [hI]
    refine lintegral_mono fun ω => ?_
    by_cases hω : List.ofFn (fun k : Fin M => X k ω) ∈ S ∧ ∀ n < M, ok n ω ∨ Dd (List.ofFn fun k : Fin n => X k ω)
    · rw [Set.indicator_of_mem (show ω ∈ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧
          ∀ n < M, ok n ω ∨ Dd (List.ofFn fun k : Fin n => X k ω)} from hω), Set.indicator_of_mem (show ω ∈ A M from hω.2)]
      simp only [Pi.one_apply, hVdef, Nat.sub_self]
      split_ifs
      · exact le_rfl
      · show (1 : ℝ≥0∞) ≤ ENNReal.ofReal (F (pre M ω))
        rw [hFdef, Set.indicator_of_mem hω.1]; simp
    · rw [Set.indicator_of_notMem (show ω ∉ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S ∧
          ∀ n < M, ok n ω ∨ Dd (List.ofFn fun k : Fin n => X k ω)} from hω)]; exact zero_le
  exact hMle.trans ((hchain M le_rfl).trans h0)

end Cryptarchia.Prob
