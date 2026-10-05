import Cryptarchia.Prob.Stake
import Cryptarchia.Prob.ROEpoch
import Cryptarchia.Prob.InferClose

/-!
# The stake estimate stays in band, from the random oracle

Every epoch state a slot's lottery runs under must be within the band
(`final_bimm_ro_epoch_ok` pays for the states that are not). This file bounds the
probability that some epoch's estimate leaves the band.

* **Chernoff with predictable rates** (`chernoff_mg`, `chernoff_lo`, `chernoff_hi`):
  if each slot's outcome has, given the past, a known law (the random oracle's
  `slot_law` under fresh lotteries), then a count of slots whose outcome lies in a
  set `A` concentrates around the sum of the slots' rates, even though the rates
  depend on the past (on the epoch state). The bounds are the multiplicative
  Chernoff exponents `m δ²/2` (below) and `m δ² (1/2 - 2δ/9)` (above), for any
  lower bound `m` on the sum of the rates.
* **The band step** (`band_step`): if epoch `e` is in band, its window's counts are
  within `δ` of their rates, the next estimate is the specification's update of a
  count between `(1 - μ)` times the honest occupied slots and all occupied slots,
  and the stake path satisfies `StakePath`, then epoch `e + 1` is in band.
* **`prob_out_of_band`**: the probability that some epoch before `Ne` is out of band
  is at most `Ne · (exp(-m δ²/2) + exp(-m δ² (1/2 - 2δ/9)))`.
-/

namespace Cryptarchia.Prob

open MeasureTheory ProbabilityTheory Finset Real
open scoped ENNReal

/-! ## Chernoff bounds with predictable rates -/

/-- `e^s - 1 ≤ s + s²/2 + (2/9) s³` for `0 ≤ s ≤ 1` (from `Real.exp_bound`). -/
theorem exp_sub_one_le_cubic {s : ℝ} (h0 : 0 ≤ s) (h1 : s ≤ 1) :
    Real.exp s - 1 ≤ s + s ^ 2 / 2 + 2 / 9 * s ^ 3 := by
  have hb := Real.exp_bound (x := s) (by rw [abs_of_nonneg h0]; exact h1) (n := 3) (by norm_num)
  simp only [Finset.sum_range_succ, Finset.sum_range_zero, Nat.factorial, Nat.cast_ofNat,
    pow_zero, pow_one, abs_of_nonneg h0] at hb
  have := (abs_le.1 hb).2
  norm_num at this
  nlinarith [this]


section Chernoff

variable {Ω : Type*} [mΩ : MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ]

/-- The indicator of a set of outcomes, as a real. -/
def indA (A : Out → Prop) [DecidablePred A] (o : Out) : ℝ := if A o then 1 else 0

/-- The probability of `A` under a law. -/
noncomputable def rateA (A : Out → Prop) [DecidablePred A] (law : Out → ℝ) : ℝ := ∑ o, law o * indA A o

theorem indA_nonneg (A : Out → Prop) [DecidablePred A] (o : Out) : 0 ≤ indA A o := by
  unfold indA; split_ifs <;> norm_num

theorem exp_indA (A : Out → Prop) [DecidablePred A] (t : ℝ) (o : Out) :
    exp (t * indA A o) = 1 + (exp t - 1) * indA A o := by
  unfold indA; split_ifs <;> simp

/-- One slot's factor: `exp(t·1_A(o) - (eᵗ - 1)·rate)` has mean at most `1` under a
law with that rate. -/
theorem step_le_one (A : Out → Prop) [DecidablePred A] (t : ℝ) (law : Out → ℝ) (h0 : ∀ o, 0 ≤ law o)
    (h1 : ∑ o, law o = 1) :
    ∑ o, ENNReal.ofReal (exp (t * indA A o - (exp t - 1) * rateA A law)) * ENNReal.ofReal (law o) ≤ 1 := by
  rw [← ENNReal.ofReal_one]
  have e1 : ∀ o, ENNReal.ofReal (exp (t * indA A o - (exp t - 1) * rateA A law)) * ENNReal.ofReal (law o) =
      ENNReal.ofReal (exp (-((exp t - 1) * rateA A law)) * (law o * exp (t * indA A o))) := by
    intro o
    rw [← ENNReal.ofReal_mul (exp_pos _).le]
    congr 1
    rw [sub_eq_add_neg, exp_add]; ring
  simp only [e1]
  rw [← ENNReal.ofReal_sum_of_nonneg (fun o _ => mul_nonneg (exp_pos _).le (mul_nonneg (h0 o) (exp_pos _).le))]
  apply ENNReal.ofReal_le_ofReal
  rw [← Finset.mul_sum]
  have hs : ∑ o, law o * exp (t * indA A o) = 1 + (exp t - 1) * rateA A law := by
    simp only [exp_indA, mul_add, mul_one, Finset.sum_add_distrib, h1, rateA, Finset.mul_sum]
    congr 1; exact Finset.sum_congr rfl fun o _ => by ring
  rw [hs]
  have := add_one_le_exp ((exp t - 1) * rateA A law)
  have hpos := exp_pos (-((exp t - 1) * rateA A law))
  calc exp (-((exp t - 1) * rateA A law)) * (1 + (exp t - 1) * rateA A law)
      ≤ exp (-((exp t - 1) * rateA A law)) * exp ((exp t - 1) * rateA A law) :=
        mul_le_mul_of_nonneg_left (by linarith) hpos.le
    _ = 1 := by rw [← exp_add]; simp

variable {μ}

/-- **The exponential supermartingale.** Slot `k`'s outcome `X k` has law `law k ω`
given what is known before it (`F k`, which knows the earlier outcomes and the law
itself). Then for every finite set of slots `W` and every `t`,
`E[∏_{k ∈ W} exp(t·1_A(X k) - (eᵗ - 1)·rate k)] ≤ 1`. -/
theorem chernoff_mg (X : ℕ → Ω → Out) (hXm : ∀ k, Measurable (X k))
    (F : ℕ → MeasurableSpace Ω) (hF : ∀ n, F n ≤ mΩ) (hFmono : ∀ j n, j ≤ n → F j ≤ F n)
    (hXF : ∀ n j, j < n → Measurable[F n] (X j))
    (law : ℕ → Ω → Out → ℝ) (hlaw0 : ∀ n ω o, 0 ≤ law n ω o) (hlaw1 : ∀ n ω, ∑ o, law n ω o = 1)
    (hlawm : ∀ n o, Measurable[F n] fun ω => law n ω o)
    (hfr : ∀ n (f : Ω → ℝ≥0∞), Measurable[F n] f → ∀ o,
      ∫⁻ ω, f ω * (if X n ω = o then 1 else 0) ∂μ = ∫⁻ ω, f ω * ENNReal.ofReal (law n ω o) ∂μ)
    (A : Out → Prop) [DecidablePred A] (t : ℝ) (W : Finset ℕ) :
    ∫⁻ ω, ∏ k ∈ W, ENNReal.ofReal (exp (t * indA A (X k ω) - (exp t - 1) * rateA A (law k ω))) ∂μ ≤ 1 := by
  -- measurability of the factors
  have hrate : ∀ k, Measurable[F k] fun ω => rateA A (law k ω) := fun k =>
    Finset.measurable_sum _ fun o _ => (hlawm k o).mul_const _
  have hfac : ∀ n k, k < n → Measurable[F n] fun ω =>
      ENNReal.ofReal (exp (t * indA A (X k ω) - (exp t - 1) * rateA A (law k ω))) := by
    intro n k hk
    have h1 : Measurable[F n] fun ω => indA A (X k ω) :=
      (measurable_of_countable (indA A)).comp (hXF n k hk)
    have h2 : Measurable[F n] fun ω => rateA A (law k ω) := (hrate k).mono (hFmono k n hk.le) le_rfl
    exact ENNReal.measurable_ofReal.comp (measurable_exp.comp ((h1.const_mul t).sub (h2.const_mul _)))
  induction W using Finset.induction_on_max with
  | empty => simp
  | insert a W hlt ih =>
    refine le_trans ?_ ih
    have haW : a ∉ W := fun h => lt_irrefl a (hlt a h)
    simp only [Finset.prod_insert haW]
    set G : Ω → ℝ≥0∞ := fun ω => ∏ k ∈ W, ENNReal.ofReal (exp (t * indA A (X k ω) - (exp t - 1) * rateA A (law k ω)))
      with hGdef
    have hG : Measurable[F a] G := Finset.measurable_prod _ fun k hk => hfac a k (hlt k hk)
    set g : Ω → Out → ℝ≥0∞ := fun ω o => ENNReal.ofReal (exp (t * indA A o - (exp t - 1) * rateA A (law a ω)))
      with hgdef
    have hgm : ∀ o, Measurable[F a] fun ω => g ω o := fun o =>
      ENNReal.measurable_ofReal.comp (measurable_exp.comp (measurable_const.sub ((hrate a).const_mul _)))
    have hpt : ∀ ω, ENNReal.ofReal (exp (t * indA A (X a ω) - (exp t - 1) * rateA A (law a ω))) * G ω =
        ∑ o, (G ω * g ω o) * (if X a ω = o then 1 else 0) := by
      intro ω
      simp only [mul_ite, mul_one, mul_zero, Finset.sum_ite_eq, Finset.mem_univ, ↓reduceIte, hgdef]
      ring
    calc ∫⁻ ω, ENNReal.ofReal (exp (t * indA A (X a ω) - (exp t - 1) * rateA A (law a ω))) * G ω ∂μ
        = ∑ o, ∫⁻ ω, (G ω * g ω o) * (if X a ω = o then 1 else 0) ∂μ := by
          simp only [hpt]
          refine lintegral_finset_sum _ fun o _ => ?_
          exact ((hG.mul (hgm o)).mono (hF a) le_rfl).mul
            (Measurable.ite ((hXm a) (measurableSet_singleton o)) measurable_const measurable_const)
      _ = ∑ o, ∫⁻ ω, (G ω * g ω o) * ENNReal.ofReal (law a ω o) ∂μ :=
          Finset.sum_congr rfl fun o _ => hfr a _ (hG.mul (hgm o)) o
      _ = ∫⁻ ω, G ω * ∑ o, g ω o * ENNReal.ofReal (law a ω o) ∂μ := by
          have hmo : ∀ o ∈ (Finset.univ : Finset Out), Measurable fun ω => G ω * g ω o * ENNReal.ofReal (law a ω o) :=
            fun o _ => ((hG.mul (hgm o)).mono (hF a) le_rfl).mul
              (ENNReal.measurable_ofReal.comp ((hlawm a o).mono (hF a) le_rfl))
          rw [← lintegral_finset_sum _ hmo]
          refine lintegral_congr fun ω => ?_
          rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun o _ => by ring
      _ ≤ ∫⁻ ω, G ω ∂μ := by
          refine lintegral_mono fun ω => ?_
          calc G ω * ∑ o, g ω o * ENNReal.ofReal (law a ω o) ≤ G ω * 1 :=
                mul_le_mul_right (step_le_one A t (law a ω) (hlaw0 a ω) (hlaw1 a ω)) _
            _ = G ω := mul_one _

/-- **Markov on the supermartingale.** An event on which the exponent is at least `r`
has probability at most `e^{-r}`. -/
theorem chernoff_tail (X : ℕ → Ω → Out) (hXm : ∀ k, Measurable (X k))
    (F : ℕ → MeasurableSpace Ω) (hF : ∀ n, F n ≤ mΩ) (hFmono : ∀ j n, j ≤ n → F j ≤ F n)
    (hXF : ∀ n j, j < n → Measurable[F n] (X j))
    (law : ℕ → Ω → Out → ℝ) (hlaw0 : ∀ n ω o, 0 ≤ law n ω o) (hlaw1 : ∀ n ω, ∑ o, law n ω o = 1)
    (hlawm : ∀ n o, Measurable[F n] fun ω => law n ω o)
    (hfr : ∀ n (f : Ω → ℝ≥0∞), Measurable[F n] f → ∀ o,
      ∫⁻ ω, f ω * (if X n ω = o then 1 else 0) ∂μ = ∫⁻ ω, f ω * ENNReal.ofReal (law n ω o) ∂μ)
    (A : Out → Prop) [DecidablePred A] (t : ℝ) (W : Finset ℕ) (r : ℝ) (S : Set Ω)
    (hS : ∀ ω ∈ S, r ≤ t * ∑ k ∈ W, indA A (X k ω) - (exp t - 1) * ∑ k ∈ W, rateA A (law k ω)) :
    μ S ≤ ENNReal.ofReal (exp (-r)) := by
  set Z : Ω → ℝ≥0∞ := fun ω =>
    ∏ k ∈ W, ENNReal.ofReal (exp (t * indA A (X k ω) - (exp t - 1) * rateA A (law k ω))) with hZ
  have hZm : Measurable Z := by
    refine Finset.measurable_prod _ fun k _ => ENNReal.measurable_ofReal.comp (measurable_exp.comp ?_)
    exact (((measurable_of_countable (indA A)).comp (hXm k)).const_mul t).sub
      ((Finset.measurable_sum _ fun o _ => ((hlawm k o).mono (hF k) le_rfl).mul_const _).const_mul _)
  have hZe : ∀ ω, Z ω = ENNReal.ofReal (exp (t * ∑ k ∈ W, indA A (X k ω) - (exp t - 1) * ∑ k ∈ W, rateA A (law k ω))) := by
    intro ω
    simp only [hZ]
    rw [← ENNReal.ofReal_prod_of_nonneg (fun k _ => (exp_pos _).le), ← exp_sum, Finset.mul_sum, Finset.mul_sum,
      ← Finset.sum_sub_distrib]
  have hsub : S ⊆ {ω | ENNReal.ofReal (exp r) ≤ Z ω} := by
    intro ω hω
    simp only [Set.mem_setOf_eq, hZe]
    exact ENNReal.ofReal_le_ofReal (exp_le_exp.2 (hS ω hω))
  calc μ S ≤ μ {ω | ENNReal.ofReal (exp r) ≤ Z ω} := measure_mono hsub
    _ ≤ (∫⁻ ω, Z ω ∂μ) / ENNReal.ofReal (exp r) :=
        meas_ge_le_lintegral_div hZm.aemeasurable (by simp [exp_pos]) ENNReal.ofReal_ne_top
    _ ≤ 1 / ENNReal.ofReal (exp r) :=
        ENNReal.div_le_div_right (chernoff_mg X hXm F hF hFmono hXF law hlaw0 hlaw1 hlawm hfr A t W) _
    _ = ENNReal.ofReal (exp (-r)) := by
        rw [one_div, ← ENNReal.ofReal_inv_of_pos (exp_pos r), exp_neg]

/-- **Lower tail**: the count falls below `(1 - δ)` times the sum of the rates, while
that sum is at least `m`, with probability at most `exp(-m δ²/2)`. -/
theorem chernoff_lo (X : ℕ → Ω → Out) (hXm : ∀ k, Measurable (X k))
    (F : ℕ → MeasurableSpace Ω) (hF : ∀ n, F n ≤ mΩ) (hFmono : ∀ j n, j ≤ n → F j ≤ F n)
    (hXF : ∀ n j, j < n → Measurable[F n] (X j))
    (law : ℕ → Ω → Out → ℝ) (hlaw0 : ∀ n ω o, 0 ≤ law n ω o) (hlaw1 : ∀ n ω, ∑ o, law n ω o = 1)
    (hlawm : ∀ n o, Measurable[F n] fun ω => law n ω o)
    (hfr : ∀ n (f : Ω → ℝ≥0∞), Measurable[F n] f → ∀ o,
      ∫⁻ ω, f ω * (if X n ω = o then 1 else 0) ∂μ = ∫⁻ ω, f ω * ENNReal.ofReal (law n ω o) ∂μ)
    (A : Out → Prop) [DecidablePred A] (W : Finset ℕ) {δ m : ℝ} (hδ : 0 ≤ δ) (S : Set Ω)
    (hS : ∀ ω ∈ S, ∑ k ∈ W, indA A (X k ω) < (1 - δ) * ∑ k ∈ W, rateA A (law k ω) ∧
      m ≤ ∑ k ∈ W, rateA A (law k ω)) :
    μ S ≤ ENNReal.ofReal (exp (-(m * δ ^ 2 / 2))) := by
  refine chernoff_tail X hXm F hF hFmono hXF law hlaw0 hlaw1 hlawm hfr A (-δ) W _ S fun ω hω => ?_
  obtain ⟨h1, h2⟩ := hS ω hω
  set c := ∑ k ∈ W, indA A (X k ω)
  set R := ∑ k ∈ W, rateA A (law k ω)
  have hq := exp_neg_le_quad' hδ
  have hd2 : 0 ≤ δ ^ 2 / 2 := by positivity
  -- `-δ c + (1 - e^{-δ}) R ≥ R (1 - e^{-δ} - δ + δ²) ≥ R δ²/2 ≥ m δ²/2`
  have hR : 0 ≤ R := Finset.sum_nonneg fun k _ =>
    Finset.sum_nonneg fun o _ => mul_nonneg (hlaw0 k ω o) (indA_nonneg A o)
  have : -(exp (-δ) - 1) * R ≥ (δ - δ ^ 2 / 2) * R := mul_le_mul_of_nonneg_right (by linarith) hR
  nlinarith [mul_le_mul_of_nonneg_right h2 hd2]

/-- **Upper tail**: the count exceeds `(1 + δ)` times the sum of the rates, while that
sum is at least `m`, with probability at most `exp(-m δ² (1/2 - 2δ/9))` (`δ ≤ 1`). -/
theorem chernoff_hi (X : ℕ → Ω → Out) (hXm : ∀ k, Measurable (X k))
    (F : ℕ → MeasurableSpace Ω) (hF : ∀ n, F n ≤ mΩ) (hFmono : ∀ j n, j ≤ n → F j ≤ F n)
    (hXF : ∀ n j, j < n → Measurable[F n] (X j))
    (law : ℕ → Ω → Out → ℝ) (hlaw0 : ∀ n ω o, 0 ≤ law n ω o) (hlaw1 : ∀ n ω, ∑ o, law n ω o = 1)
    (hlawm : ∀ n o, Measurable[F n] fun ω => law n ω o)
    (hfr : ∀ n (f : Ω → ℝ≥0∞), Measurable[F n] f → ∀ o,
      ∫⁻ ω, f ω * (if X n ω = o then 1 else 0) ∂μ = ∫⁻ ω, f ω * ENNReal.ofReal (law n ω o) ∂μ)
    (A : Out → Prop) [DecidablePred A] (W : Finset ℕ) {δ m : ℝ} (hδ0 : 0 ≤ δ) (hδ1 : δ ≤ 1) (S : Set Ω)
    (hS : ∀ ω ∈ S, (1 + δ) * ∑ k ∈ W, rateA A (law k ω) < ∑ k ∈ W, indA A (X k ω) ∧
      m ≤ ∑ k ∈ W, rateA A (law k ω)) :
    μ S ≤ ENNReal.ofReal (exp (-(m * δ ^ 2 * (1 / 2 - 2 / 9 * δ)))) := by
  refine chernoff_tail X hXm F hF hFmono hXF law hlaw0 hlaw1 hlawm hfr A δ W _ S fun ω hω => ?_
  obtain ⟨h1, h2⟩ := hS ω hω
  set c := ∑ k ∈ W, indA A (X k ω)
  set R := ∑ k ∈ W, rateA A (law k ω)
  have hq := exp_sub_one_le_cubic hδ0 hδ1
  have hk : 0 ≤ δ ^ 2 * (1 / 2 - 2 / 9 * δ) := mul_nonneg (by positivity) (by linarith)
  have hR : 0 ≤ R := Finset.sum_nonneg fun k _ =>
    Finset.sum_nonneg fun o _ => mul_nonneg (hlaw0 k ω o) (indA_nonneg A o)
  have : (exp δ - 1) * R ≤ (δ + δ ^ 2 / 2 + 2 / 9 * δ ^ 3) * R := mul_le_mul_of_nonneg_right hq hR
  have : δ * ((1 + δ) * R) ≤ δ * c := mul_le_mul_of_nonneg_left h1.le hδ0
  nlinarith [mul_le_mul_of_nonneg_right h2 hk]

end Chernoff

/-! ## The slot law's rates -/

section Rates

variable {E : Env}

theorem qhRO_nonneg (hp : 0 < E.c.p) (hnd : E.nodes.Nodup) (i : ℕ) (s : EpochState) (h : Fin 3) :
    0 ≤ qhRO E i s h := by
  have hnl0 : ∀ j, 0 < nodeLoss E i s j := fun j => loss_pos hp s _
  have hnl1 : ∀ j, nodeLoss E i s j ≤ 1 := fun j => loss_le_one hp s _
  have hP0 : pZero E i s = (E.nodes.map (nodeLoss E i s)).prod := loss_honNotes_prod i s _ hnd
  have hpos : 0 < pZero E i s := loss_pos hp s _
  have hle : pZero E i s ≤ 1 := loss_le_one hp s _
  have h1 : 0 ≤ pOne E i s := by
    rw [pOne_eq hnd]
    have := exactly_one_ge (nodeLoss E i s) hnl0 E.nodes
    rw [← hP0] at this ⊢
    have hl := Real.log_nonpos hpos.le hle
    have : 0 ≤ -(pZero E i s * Real.log (pZero E i s)) := by nlinarith
    linarith
  have h2 : 0 ≤ 1 - pZero E i s - pOne E i s := by
    rw [pOne_eq hnd, hP0]; exact two_or_more_nonneg _ (fun j => (hnl0 j).le) hnl1 _ hnd
  unfold qhRO; split_ifs
  · exact hpos.le
  · exact h1
  · exact h2

theorem qaRO_nonneg (hp : 0 < E.c.p) (s : EpochState) : 0 ≤ qaRO E.c s := by
  unfold qaRO; linarith [loss_le_one hp s (advNotes s)]

theorem qaRO_le_one (hp : 0 < E.c.p) (s : EpochState) : qaRO E.c s ≤ 1 := by
  unfold qaRO; linarith [loss_nonneg hp s (advNotes s)]

/-- Slot `i`'s law under state `s`. -/
noncomputable def lawS (E : Env) (i : ℕ) (s : EpochState) : Out → ℝ := prodLaw (qhRO E i s) (qaRO E.c s)

theorem lawS_nonneg (hp : 0 < E.c.p) (hnd : E.nodes.Nodup) (i : ℕ) (s : EpochState) (o : Out) :
    0 ≤ lawS E i s o :=
  prodLaw_nonneg (qhRO_nonneg hp hnd i s) (qaRO_nonneg hp s) (qaRO_le_one hp s) o

theorem lawS_sum (i : ℕ) (s : EpochState) : ∑ o, lawS E i s o = 1 :=
  sum_prodLaw_one (by simp [qhRO]) _

/-- Some honest leader. -/
def honA (o : Out) : Prop := o.hon ≠ 0

/-- The slot is occupied: some honest or adversarial leader. -/
def occA (o : Out) : Prop := o.hon ≠ 0 ∨ o.adv = true

instance : DecidablePred honA := fun o => inferInstanceAs (Decidable (o.hon ≠ 0))
instance : DecidablePred occA := fun o => inferInstanceAs (Decidable (o.hon ≠ 0 ∨ o.adv = true))

theorem rate_hon (i : ℕ) (s : EpochState) : rateA honA (lawS E i s) = 1 - pZero E i s := by
  unfold rateA lawS
  rw [sum_prodLaw, Fin.sum_univ_three]
  simp [indA, honA, qhRO]

theorem rate_occ (i : ℕ) (s : EpochState) :
    rateA occA (lawS E i s) = 1 - pZero E i s * loss E.c s (advNotes s) := by
  unfold rateA lawS
  rw [sum_prodLaw, Fin.sum_univ_three]
  simp [indA, occA, qhRO, qaRO]; ring

end Rates

/-! ## The band and the band step -/

/-- The constants of the band: the estimate keeps `λ V / D` in `[ℓlo, ℓhi]` for the
visible stake `V`, a fraction `μ` of honest wins may go uncounted, the adversary
holds at most a fraction `β` of the participating stake, counts are within `δ` of
their rates, and `η`, `ζ` are the lottery-constant and small-stake errors. -/
structure TBand where
  ℓlo : ℝ
  ℓhi : ℝ
  μ : ℝ
  β : ℝ
  δ : ℝ
  η : ℝ
  ζ : ℝ

namespace TBand

variable (T : TBand)

/-- The largest honest exponent in band. -/
noncomputable def Yh : ℝ := T.ℓhi / (1 - T.μ)

/-- The largest adversarial exponent in band. -/
noncomputable def Ya : ℝ := T.β / (1 - T.β) * T.Yh

/-- The smallest honest exponent in band. -/
noncomputable def ylo : ℝ := (1 - T.β) * T.ℓlo

/-- The honest rate's relative shortfall from `λ H / D`. -/
noncomputable def clo : ℝ := 1 - T.Yh / 2 - 2 * errHi T.η T.ζ T.Yh / T.ylo

/-- The occupied rate's relative excess over `λ S / D`. -/
noncomputable def chi : ℝ := 1 + (errLo T.η T.ζ T.Yh + errLo T.η T.ζ T.Ya) / T.ℓlo

/-- The band's constants are consistent. -/
structure OK : Prop where
  lo_pos : 0 < T.ℓlo
  hi0 : 0 ≤ T.ℓhi
  μ0 : 0 ≤ T.μ
  μ1 : T.μ < 1
  β0 : 0 ≤ T.β
  β1 : T.β < 1
  δ0 : 0 < T.δ
  δ1 : T.δ ≤ 1
  η0 : 0 ≤ T.η
  ζ0 : 0 ≤ T.ζ
  Yh_le : T.Yh ≤ 1 / 2
  Ya_le : T.Ya ≤ 1 / 2
  eHi : errHi T.η T.ζ T.Yh ≤ 1
  eLoH : errLo T.η T.ζ T.Yh ≤ 1
  eLoA : errLo T.η T.ζ T.Ya ≤ 1
  clo0 : 0 ≤ T.clo

end TBand

section Band

variable {E : Env} {T : TBand}

/-- The honest stake online at slot `i` under `s`. -/
noncomputable def hstake (E : Env) (i : ℕ) (s : EpochState) : ℝ := (stakeOf (honNotes E i s E.nodes) : ℝ)

/-- The adversary's stake under `s`. -/
noncomputable def astake (s : EpochState) : ℝ := (stakeOf (advNotes s) : ℝ)

/-- **Slot `i` is in band under `s`**: `λ (1-μ) H ≤ ℓhi D` and `ℓlo D ≤ λ (H + A)`.
This is the estimate condition of `StakeTSI` when the adversary withholds
everything (`w = 1`). -/
def SlotIn (E : Env) (T : TBand) (i : ℕ) (s : EpochState) : Prop :=
  (1 - T.μ) * (lam0 E.c * hstake E i s) ≤ T.ℓhi * s.D ∧ T.ℓlo * s.D ≤ lam0 E.c * (hstake E i s + astake s)

/-- **What a state must satisfy regardless of its estimate**: distinct note
identifiers, small notes, and the adversary's stake share at most `β`. -/
structure StateOK (E : Env) (T : TBand) (i : ℕ) (s : EpochState) : Prop where
  nodup : (s.lead.map Note.id).Nodup
  smallH : Small E.c s (honNotes E i s E.nodes) T.ζ
  smallA : Small E.c s (advNotes s) T.ζ
  frac : (1 - T.β) * astake s ≤ T.β * hstake E i s

theorem lam0_nonneg (c : Config) : 0 ≤ lam0 c := by unfold lam0; positivity

theorem hstake_nonneg (E : Env) (i : ℕ) (s : EpochState) : 0 ≤ hstake E i s := by unfold hstake; positivity

theorem astake_nonneg (s : EpochState) : 0 ≤ astake s := by unfold astake; positivity

/-- The honest exponent of an in-band slot lies in `[ylo, Yh]`. -/
theorem expo_range (hT : T.OK) {i : ℕ} {s : EpochState} (hst : StateOK E T i s) (hin : SlotIn E T i s) :
    T.ylo ≤ expo E.c s (honNotes E i s E.nodes) ∧ expo E.c s (honNotes E i s E.nodes) ≤ T.Yh ∧
      expo E.c s (advNotes s) ≤ T.Ya := by
  have hD : (0 : ℝ) < s.D := by have := hst.smallH.D_pos; exact_mod_cast (by omega : 0 < s.D)
  have hH := hstake_nonneg E i s
  have hA := astake_nonneg s
  have hl0 := lam0_nonneg E.c
  have hμ : 0 < 1 - T.μ := by linarith [hT.μ1]
  have hβ : 0 < 1 - T.β := by linarith [hT.β1]
  have eH : expo E.c s (honNotes E i s E.nodes) = lam0 E.c * hstake E i s / s.D := rfl
  have eA : expo E.c s (advNotes s) = lam0 E.c * astake s / s.D := rfl
  obtain ⟨h1, h2⟩ := hin
  have hfr := hst.frac
  have hHi : lam0 E.c * hstake E i s / s.D ≤ T.Yh := by
    unfold TBand.Yh; rw [div_le_div_iff₀ hD hμ]; linarith
  refine ⟨?_, ?_, ?_⟩
  · rw [eH, le_div_iff₀ hD]; unfold TBand.ylo
    have : (1 - T.β) * (hstake E i s + astake s) ≤ hstake E i s := by linarith
    nlinarith [mul_le_mul_of_nonneg_left this hl0, mul_le_mul_of_nonneg_left h2 hβ.le]
  · rw [eH]; exact hHi
  · rw [eA]; unfold TBand.Ya
    have hAH : lam0 E.c * astake s / s.D ≤ T.β / (1 - T.β) * (lam0 E.c * hstake E i s / s.D) := by
      rw [div_mul_div_comm, div_le_div_iff₀ hD (mul_pos hβ hD)]
      nlinarith [mul_le_mul_of_nonneg_left hfr (mul_nonneg hl0 hD.le)]
    exact le_trans hAH (mul_le_mul_of_nonneg_left hHi (div_nonneg hT.β0 hβ.le))

/-- **The honest rate of an in-band slot**: `D · P(some honest leader) ≥ λ H · clo`. -/
theorem rate_hon_ge (hc : LotConsts E.c T.η) (hT : T.OK) {i : ℕ} {s : EpochState}
    (hst : StateOK E T i s) (hin : SlotIn E T i s) :
    lam0 E.c * hstake E i s * T.clo ≤ s.D * rateA honA (lawS E i s) := by
  obtain ⟨hlo, hhi, -⟩ := expo_range hT hst hin
  have hD : (0 : ℝ) < s.D := by have := hst.smallH.D_pos; exact_mod_cast (by omega : 0 < s.D)
  set y := expo E.c s (honNotes E i s E.nodes) with hy
  have hylo : 0 < T.ylo := mul_pos (by linarith [hT.β1]) hT.lo_pos
  have hy0 : 0 ≤ y := by linarith
  have hLH : s.D * y = lam0 E.c * hstake E i s := by rw [hy]; unfold expo hstake; field_simp
  set eH := errHi T.η T.ζ T.Yh
  have heH0 : 0 ≤ eH := errHi_nonneg hT.η0 hT.ζ0 (by linarith)
  have hP0 : pZero E i s ≤ exp (-y) * exp (errHi T.η T.ζ y) :=
    loss_hi hc hT.η0 hst.smallH (le_trans hhi hT.Yh_le)
  have he1 : exp (errHi T.η T.ζ y) ≤ 1 + 2 * eH :=
    le_trans (exp_le_exp.2 (errHi_mono hT.η0 hy0 hhi)) (exp_le_one_add_two heH0 hT.eHi)
  have hey : exp (-y) ≤ 1 := by rw [exp_le_one_iff]; linarith
  have hq := exp_neg_le_quad' hy0
  have hP0' : pZero E i s ≤ 1 - y + y ^ 2 / 2 + 2 * eH := by
    have := mul_le_mul_of_nonneg_left he1 (exp_pos (-y)).le
    nlinarith
  rw [rate_hon]
  have hDy : s.D * T.ylo ≤ lam0 E.c * hstake E i s := by rw [← hLH]; exact mul_le_mul_of_nonneg_left hlo hD.le
  have hDle : (s.D : ℝ) ≤ lam0 E.c * hstake E i s / T.ylo := by rw [le_div_iff₀ hylo]; linarith
  have hLH0 : 0 ≤ lam0 E.c * hstake E i s := mul_nonneg (lam0_nonneg _) (hstake_nonneg _ _ _)
  have k1 : s.D * (y - y ^ 2 / 2 - 2 * eH) ≤ s.D * (1 - pZero E i s) :=
    mul_le_mul_of_nonneg_left (by linarith) hD.le
  have k2 : s.D * (y ^ 2 / 2) ≤ lam0 E.c * hstake E i s * (T.Yh / 2) := by
    have : s.D * (y ^ 2 / 2) = lam0 E.c * hstake E i s * (y / 2) := by rw [← hLH]; ring
    rw [this]; exact mul_le_mul_of_nonneg_left (by linarith) hLH0
  have k3 : s.D * (2 * eH) ≤ lam0 E.c * hstake E i s * (2 * eH / T.ylo) := by
    have := mul_le_mul_of_nonneg_right hDle (by linarith : (0 : ℝ) ≤ 2 * eH)
    calc s.D * (2 * eH) ≤ lam0 E.c * hstake E i s / T.ylo * (2 * eH) := this
      _ = _ := by ring
  have : lam0 E.c * hstake E i s * T.clo =
      lam0 E.c * hstake E i s - lam0 E.c * hstake E i s * (T.Yh / 2) - lam0 E.c * hstake E i s * (2 * eH / T.ylo) := by
    unfold TBand.clo; ring
  rw [this]
  have : s.D * (y - y ^ 2 / 2 - 2 * eH) = lam0 E.c * hstake E i s - s.D * (y ^ 2 / 2) - s.D * (2 * eH) := by
    rw [← hLH]; ring
  linarith

/-- **The occupied rate of an in-band slot**: `D · P(occupied) ≤ λ (H + A) · chi`. -/
theorem rate_occ_le (hc : LotConsts E.c T.η) (hT : T.OK) {i : ℕ} {s : EpochState}
    (hst : StateOK E T i s) (hin : SlotIn E T i s) :
    s.D * rateA occA (lawS E i s) ≤ lam0 E.c * (hstake E i s + astake s) * T.chi := by
  obtain ⟨hlo, hhi, hA⟩ := expo_range hT hst hin
  have hD : (0 : ℝ) < s.D := by have := hst.smallH.D_pos; exact_mod_cast (by omega : 0 < s.D)
  have hp := hc.p_pos
  set y := expo E.c s (honNotes E i s E.nodes) with hy
  set ya := expo E.c s (advNotes s) with hya
  have hylo : 0 < T.ylo := mul_pos (by linarith [hT.β1]) hT.lo_pos
  have hy0 : 0 ≤ y := by linarith
  have hya0 : 0 ≤ ya := by rw [hya]; unfold expo; have := lam0_nonneg E.c; positivity
  have hLS : s.D * (y + ya) = lam0 E.c * (hstake E i s + astake s) := by
    rw [hy, hya]; unfold expo hstake astake; field_simp
  set a := errLo T.η T.ζ T.Yh
  set b := errLo T.η T.ζ T.Ya
  have ha0 : 0 ≤ a := by unfold a errLo; have := hT.η0; have := hT.ζ0; positivity
  have hb0 : 0 ≤ b := by unfold b errLo; have := hT.η0; have := hT.ζ0; positivity
  have hay : errLo T.η T.ζ y ≤ a := errLo_mono hT.η0 hy0 hhi
  have hbya : errLo T.η T.ζ ya ≤ b := errLo_mono hT.η0 hya0 hA
  have hP0 : exp (-y) * (1 - errLo T.η T.ζ y) ≤ pZero E i s :=
    loss_lo hc hT.η0 hst.smallH (le_trans hhi hT.Yh_le) (le_trans hay hT.eLoH)
  have hLA : exp (-ya) * (1 - errLo T.η T.ζ ya) ≤ loss E.c s (advNotes s) :=
    loss_lo hc hT.η0 hst.smallA (le_trans hA hT.Ya_le) (le_trans hbya hT.eLoA)
  have h1 : exp (-y) * (1 - a) ≤ pZero E i s :=
    le_trans (mul_le_mul_of_nonneg_left (by linarith) (exp_pos _).le) hP0
  have h2 : exp (-ya) * (1 - b) ≤ loss E.c s (advNotes s) :=
    le_trans (mul_le_mul_of_nonneg_left (by linarith) (exp_pos _).le) hLA
  have h1a : 0 ≤ exp (-y) * (1 - a) := mul_nonneg (exp_pos _).le (by linarith [hT.eLoH])
  have h2b : 0 ≤ exp (-ya) * (1 - b) := mul_nonneg (exp_pos _).le (by linarith [hT.eLoA])
  have hprod : exp (-y) * (1 - a) * (exp (-ya) * (1 - b)) ≤ pZero E i s * loss E.c s (advNotes s) :=
    mul_le_mul h1 h2 h2b (loss_nonneg hp s _)
  have hexp : exp (-y) * exp (-ya) = exp (-(y + ya)) := by rw [← exp_add]; ring_nf
  set Y := y + ya
  have hY0 : 0 ≤ Y := by linarith
  have heY : exp (-Y) ≤ 1 := by rw [exp_le_one_iff]; linarith
  have h1e := add_one_le_exp (-Y)
  have hab : exp (-Y) * (1 - a - b) ≤ exp (-y) * (1 - a) * (exp (-ya) * (1 - b)) := by
    have : exp (-y) * (1 - a) * (exp (-ya) * (1 - b)) = exp (-Y) * ((1 - a) * (1 - b)) := by
      rw [← hexp]; ring
    rw [this]
    exact mul_le_mul_of_nonneg_left (by nlinarith) (exp_pos _).le
  have hrate : 1 - pZero E i s * loss E.c s (advNotes s) ≤ Y + a + b := by
    nlinarith [mul_le_mul_of_nonneg_right heY (add_nonneg ha0 hb0)]
  rw [rate_occ]
  have hDle : (s.D : ℝ) ≤ lam0 E.c * (hstake E i s + astake s) / T.ℓlo := by
    rw [le_div_iff₀ hT.lo_pos]; linarith [hin.2]
  have hS0 : 0 ≤ lam0 E.c * (hstake E i s + astake s) :=
    mul_nonneg (lam0_nonneg _) (add_nonneg (hstake_nonneg _ _ _) (astake_nonneg _))
  calc s.D * (1 - pZero E i s * loss E.c s (advNotes s)) ≤ s.D * (Y + a + b) :=
        mul_le_mul_of_nonneg_left hrate hD.le
    _ = lam0 E.c * (hstake E i s + astake s) + s.D * (a + b) := by rw [← hLS]; ring
    _ ≤ lam0 E.c * (hstake E i s + astake s) + lam0 E.c * (hstake E i s + astake s) / T.ℓlo * (a + b) := by
        have := mul_le_mul_of_nonneg_right hDle (add_nonneg ha0 hb0); linarith
    _ = lam0 E.c * (hstake E i s + astake s) * T.chi := by unfold TBand.chi; ring

/-- The honest rate of an in-band slot is at least `ylo · clo`. -/
theorem rate_hon_lo (hc : LotConsts E.c T.η) (hT : T.OK) {i : ℕ} {s : EpochState}
    (hst : StateOK E T i s) (hin : SlotIn E T i s) : T.ylo * T.clo ≤ rateA honA (lawS E i s) := by
  obtain ⟨hlo, -, -⟩ := expo_range hT hst hin
  have hD : (0 : ℝ) < s.D := by have := hst.smallH.D_pos; exact_mod_cast (by omega : 0 < s.D)
  have h := rate_hon_ge hc hT hst hin
  have hLH : lam0 E.c * hstake E i s = s.D * expo E.c s (honNotes E i s E.nodes) := by
    unfold expo hstake; field_simp
  rw [hLH] at h
  have : s.D * (T.ylo * T.clo) ≤ s.D * rateA honA (lawS E i s) := by
    nlinarith [mul_le_mul_of_nonneg_right hlo hT.clo0, mul_le_mul_of_nonneg_left
      (mul_le_mul_of_nonneg_right hlo hT.clo0) hD.le]
  exact le_of_mul_le_mul_left this hD

theorem rate_hon_le_occ (hp : 0 < E.c.p) (i : ℕ) (s : EpochState) :
    rateA honA (lawS E i s) ≤ rateA occA (lawS E i s) := by
  rw [rate_hon, rate_occ]
  have := loss_le_one hp s (advNotes s)
  have := loss_nonneg hp s (advNotes s)
  have := (loss_pos hp s (honNotes E i s E.nodes)).le
  unfold pZero; nlinarith

end Band


section Step

variable (E : Env) (T : TBand) (σ : ℕ → EpochState) (X : ℕ → Out)

/-- The observation window of epoch `e`, as the indices `k` of slots `k + 1`
(slot `0` is genesis). -/
def win (e : ℕ) : Finset ℕ :=
  Ico (e * E.c.epochLength - 1) (e * E.c.epochLength + E.c.period - 1)

/-- **Epoch `e` is in band**: every slot of it. -/
def InB (e : ℕ) : Prop :=
  ∀ i, e * E.c.epochLength ≤ i → i < (e + 1) * E.c.epochLength → SlotIn E T i (σ i)

/-- Honest occupied slots in epoch `e`'s window. -/
noncomputable def hcnt (e : ℕ) : ℝ := ∑ k ∈ win E e, indA honA (X k)

/-- Occupied slots in epoch `e`'s window. -/
noncomputable def wcnt (e : ℕ) : ℝ := ∑ k ∈ win E e, indA occA (X k)

/-- The sum of the honest rates over epoch `e`'s window. -/
noncomputable def hrate (e : ℕ) : ℝ := ∑ k ∈ win E e, rateA honA (lawS E (k + 1) (σ (k + 1)))

/-- The sum of the occupied rates over epoch `e`'s window. -/
noncomputable def wrate (e : ℕ) : ℝ := ∑ k ∈ win E e, rateA occA (lawS E (k + 1) (σ (k + 1)))

/-- The window's counts are within `δ` of their rates. -/
def Typical (e : ℕ) : Prop :=
  (1 - T.δ) * hrate E σ e ≤ hcnt E X e ∧ wcnt E X e ≤ (1 + T.δ) * wrate E σ e

/-- **The estimate's update.** Epoch `e + 1`'s estimate is the specification's update
of epoch `e`'s by a count of at least `(1 - μ)` times the window's honest occupied
slots (honest wins may be lost to forks that are never referenced as uncles) and at
most all its occupied slots plus genesis. -/
def Recur (e : ℕ) : Prop :=
  ∃ N : ℕ, (σ ((e + 1) * E.c.epochLength)).D = infer E.c (σ (e * E.c.epochLength)).D N ∧
    (1 - T.μ) * hcnt E X e ≤ N ∧ (N : ℝ) ≤ wcnt E X e + 1

/-- `1 / (PERIOD · f_p)`, `f_p = fP / PRECISION`. -/
noncomputable def Kc (c : Config) : ℝ := (c.precision : ℝ) / (c.period * c.fP)

/-- **What the stake path must satisfy** from epoch `e` to `e + 1`: the honest stake
at each slot of epoch `e + 1` is covered by an estimate from epoch `e`'s window that
misses a fraction `μ` of honest wins and a fraction `δ` to sampling (`up`), and the
total stake at each slot of epoch `e + 1` covers an estimate that counts every win,
with a fraction `δ` extra (`lo`). The constants `2`, `3` and the genesis term are
the fixed-point rounding and the genesis slot. -/
structure StakePath (e : ℕ) : Prop where
  up : ∀ j, (e + 1) * E.c.epochLength ≤ j → j < (e + 2) * E.c.epochLength →
    (1 - T.μ) * (lam0 E.c * hstake E j (σ j)) + 2 * T.ℓhi ≤
      T.ℓhi * (Kc E.c * ((1 - T.μ) * (1 - T.δ) * T.clo *
        (lam0 E.c * ∑ k ∈ win E e, hstake E (k + 1) (σ (k + 1)))))
  lo : ∀ j, (e + 1) * E.c.epochLength ≤ j → j < (e + 2) * E.c.epochLength →
    T.ℓlo * (Kc E.c * ((1 + T.δ) * T.chi *
        (lam0 E.c * ∑ k ∈ win E e, (hstake E (k + 1) (σ (k + 1)) + astake (σ (k + 1)))) +
      lam0 E.c * (hstake E (e * E.c.epochLength) (σ (e * E.c.epochLength)) +
        astake (σ (e * E.c.epochLength))) / T.ℓlo) + 3) ≤
      lam0 E.c * (hstake E j (σ j) + astake (σ j))

variable {E T σ X}

theorem mem_win {e k : ℕ} (hP1 : 1 ≤ E.c.period) (hPEL : E.c.period ≤ E.c.epochLength) (hk : k ∈ win E e) :
    e * E.c.epochLength ≤ k + 1 ∧ k + 1 < (e + 1) * E.c.epochLength := by
  simp only [win, mem_Ico] at hk
  rw [add_mul, one_mul]
  omega

theorem card_win (e : ℕ) : E.c.period - 1 ≤ (win E e).card := by
  simp only [win, Nat.card_Ico]; omega

/-- **The band step.** If epoch `e` is in band, its window's counts are typical, the
estimate follows the update, and the stake path allows it, epoch `e + 1` is in band. -/
theorem band_step (hc : LotConsts E.c T.η) (hT : T.OK) (hb : E.c.betaP = E.c.precision)
    (hprec : 0 < E.c.precision) (hPf : 0 < E.c.period * E.c.fP) (hP1 : 1 ≤ E.c.period)
    (hPEL : E.c.period ≤ E.c.epochLength)
    (hconst : ∀ i, σ i = σ (i / E.c.epochLength * E.c.epochLength)) (hst : ∀ i, StateOK E T i (σ i))
    {e : ℕ} (hin : InB E T σ e) (hty : Typical E T σ X e) (hrec : Recur E T σ X e)
    (hpath : StakePath E T σ e) : InB E T σ (e + 1) := by
  set EL := E.c.epochLength with hELdef
  have hEL : 0 < EL := by omega
  have hσk : ∀ k ∈ win E e, σ (k + 1) = σ (e * EL) := by
    intro k hk
    obtain ⟨h1, h2⟩ := mem_win hP1 hPEL hk
    rw [hconst (k + 1), Nat.div_eq_of_lt_le h1 h2]
  set s0 := σ (e * EL) with hs0
  have hEL1 : e * EL < (e + 1) * EL := by rw [add_mul, one_mul]; omega
  have hin0 : SlotIn E T (e * EL) s0 := hin (e * EL) le_rfl hEL1
  have hink : ∀ k ∈ win E e, SlotIn E T (k + 1) (σ (k + 1)) := fun k hk =>
    hin (k + 1) (mem_win hP1 hPEL hk).1 (mem_win hP1 hPEL hk).2
  have hD0 : (0 : ℝ) < s0.D := by
    have h1 : 1 ≤ s0.D := (hst (e * EL)).smallH.D_pos
    exact_mod_cast (show 0 < s0.D by omega)
  -- the window's rates against its stake
  have hH : T.clo * (lam0 E.c * ∑ k ∈ win E e, hstake E (k + 1) (σ (k + 1))) ≤ s0.D * hrate E σ e := by
    unfold hrate
    rw [Finset.mul_sum, Finset.mul_sum, Finset.mul_sum]
    refine Finset.sum_le_sum fun k hk => ?_
    have := rate_hon_ge hc hT (hst (k + 1)) (hink k hk)
    rw [hσk k hk] at this ⊢
    linarith
  have hW : s0.D * wrate E σ e ≤
      T.chi * (lam0 E.c * ∑ k ∈ win E e, (hstake E (k + 1) (σ (k + 1)) + astake (σ (k + 1)))) := by
    unfold wrate
    rw [Finset.mul_sum, Finset.mul_sum, Finset.mul_sum]
    refine Finset.sum_le_sum fun k hk => ?_
    have := rate_occ_le hc hT (hst (k + 1)) (hink k hk)
    rw [hσk k hk] at this ⊢
    linarith
  -- the update
  obtain ⟨N, hD', hN1, hN2⟩ := hrec
  have hcl := infer_close E.c s0.D N hb hprec hPf
  set x : ℝ := (s0.D : ℝ) * N * E.c.precision / (E.c.period * E.c.fP) with hxdef
  have hK : 0 < Kc E.c := by unfold Kc; have : (0 : ℝ) < E.c.period * E.c.fP := by exact_mod_cast hPf
                             exact div_pos (by exact_mod_cast hprec) this
  have hxK : x = Kc E.c * (s0.D * N) := by rw [hxdef]; unfold Kc; ring
  set D' : ℝ := ((σ ((e + 1) * EL)).D : ℝ) with hD'def
  have hD'e : D' = ((infer E.c s0.D N : ℕ) : ℝ) := by rw [hD'def, hD']
  have hD'lo : x - 2 ≤ D' := by
    rw [hD'e]; have := (abs_le.1 hcl).1; have := le_max_right 1 x; linarith
  have hx0 : 0 ≤ x := by rw [hxK]; positivity
  have hD'hi : D' ≤ x + 3 := by
    rw [hD'e]; have := (abs_le.1 hcl).2; have : max 1 x ≤ 1 + x := max_le (by linarith) (by linarith)
    linarith
  have hμ : 0 ≤ 1 - T.μ := by linarith [hT.μ1]
  have hδ : 0 ≤ 1 - T.δ := by linarith [hT.δ1]
  have hxlo : Kc E.c * ((1 - T.μ) * (1 - T.δ) * T.clo *
      (lam0 E.c * ∑ k ∈ win E e, hstake E (k + 1) (σ (k + 1)))) ≤ x := by
    rw [hxK]
    refine mul_le_mul_of_nonneg_left ?_ hK.le
    have h1 : (1 - T.μ) * ((1 - T.δ) * hrate E σ e) ≤ N :=
      le_trans (mul_le_mul_of_nonneg_left hty.1 hμ) hN1
    have h2 := mul_le_mul_of_nonneg_left h1 hD0.le
    have h3 := mul_le_mul_of_nonneg_left hH (mul_nonneg hμ hδ)
    nlinarith
  have hxhi : x ≤ Kc E.c * ((1 + T.δ) * T.chi *
        (lam0 E.c * ∑ k ∈ win E e, (hstake E (k + 1) (σ (k + 1)) + astake (σ (k + 1)))) +
      lam0 E.c * (hstake E (e * EL) s0 + astake s0) / T.ℓlo) := by
    rw [hxK]
    refine mul_le_mul_of_nonneg_left ?_ hK.le
    have h1 : (N : ℝ) ≤ (1 + T.δ) * wrate E σ e + 1 := by linarith [hty.2]
    have h2 := mul_le_mul_of_nonneg_left h1 hD0.le
    have h3 := mul_le_mul_of_nonneg_left hW (by linarith [hT.δ0] : (0 : ℝ) ≤ 1 + T.δ)
    have h4 : (s0.D : ℝ) ≤ lam0 E.c * (hstake E (e * EL) s0 + astake s0) / T.ℓlo := by
      rw [le_div_iff₀ hT.lo_pos]; linarith [hin0.2]
    nlinarith
  -- every slot of epoch `e + 1`
  intro j hj1 hj2
  have hσj : σ j = σ ((e + 1) * EL) := by rw [hconst j, Nat.div_eq_of_lt_le hj1 hj2]
  have hup := hpath.up j hj1 hj2
  have hlo := hpath.lo j hj1 hj2
  have hDj : ((σ j).D : ℝ) = D' := by rw [hσj]
  refine ⟨?_, ?_⟩
  · rw [hDj]
    have := mul_le_mul_of_nonneg_left (le_trans (sub_le_sub_right hxlo 2) hD'lo) hT.hi0
    linarith
  · rw [hDj]
    have := mul_le_mul_of_nonneg_left (le_trans hD'hi (add_le_add hxhi le_rfl : x + 3 ≤ _ + 3)) hT.lo_pos.le
    linarith

end Step


/-! ## Out of band, from the random oracle -/

section RO

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
  {E : Env} {T : TBand}

/-- A slot's epoch state is its epoch's. -/
theorem σE_const (E : Env) (es : List Event) (hEL : 0 < E.c.epochLength) (i : ℕ) :
    σE E es i = σE E es (i / E.c.epochLength * E.c.epochLength) := by
  unfold σE Config.epochOf
  rw [Nat.mul_div_cancel _ hEL]

/-- The chance of leaving the band in one epoch's window, below or above. -/
noncomputable def bandEps (T : TBand) (P : ℕ) : ℝ :=
  exp (-(((P : ℝ) - 1) * (T.ylo * T.clo) * T.δ ^ 2 / 2)) +
    exp (-(((P : ℝ) - 1) * (T.ylo * T.clo) * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)))

open Classical in
/-- **The estimate stays in band.** Under a random oracle with fresh lotteries, if
every state satisfies `StateOK`, the genesis epoch is in band, every update follows
`Recur` and the stake path satisfies `StakePath`, then the probability that some
epoch before `Ne` is out of band is at most `Ne · bandEps`. The adversary's strategy
(`es ω`) is arbitrary: it chooses which wins to publish, and so the count, within
`Recur`. -/
theorem prob_out_of_band (hA : Assm E) (es : Ω → List Event)
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    (hc : LotConsts E.c T.η) (hT : T.OK) (hb : E.c.betaP = E.c.precision)
    (hprec : 0 < E.c.precision) (hPf : 0 < E.c.period * E.c.fP) (hP1 : 1 ≤ E.c.period)
    (hPEL : E.c.period ≤ E.c.epochLength)
    (hst : ∀ ω i, StateOK E T i (σE (E.withO (O ω)) (es ω) i))
    (h0 : ∀ ω, InB E T (σE (E.withO (O ω)) (es ω)) 0) {Ne : ℕ}
    (hrec : ∀ ω e, e + 1 < Ne → Recur E T (σE (E.withO (O ω)) (es ω))
      (fun k => slotOut E (k + 1) (σE (E.withO (O ω)) (es ω) (k + 1)) (tk O (k + 1) ω)) e)
    (hpath : ∀ ω e, e + 1 < Ne → StakePath E T (σE (E.withO (O ω)) (es ω)) e) :
    μ {ω | ∃ e < Ne, ¬ InB E T (σE (E.withO (O ω)) (es ω)) e} ≤ Ne * ENNReal.ofReal (bandEps T E.c.period) := by
  set σ : Ω → ℕ → EpochState := fun ω => σE (E.withO (O ω)) (es ω) with hσ
  set X : ℕ → Ω → Out := fun k ω => slotOut E (k + 1) (σ ω (k + 1)) (tk O (k + 1) ω) with hX
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
  set law : ℕ → Ω → Out → ℝ := fun n ω => lawS E (n + 1) (σ ω (n + 1)) with hlaw
  have hFm : ∀ j n, j ≤ n → hist O σ (j + 1) ≤ hist O σ (n + 1) := fun j n h => hist_mono O σ (by omega)
  have hlaw0 : ∀ n ω o, 0 ≤ law n ω o := fun n ω o => lawS_nonneg hO.pos hA.nodup _ _ o
  have hlaw1 : ∀ n ω, ∑ o, law n ω o = 1 := fun n ω => lawS_sum _ _
  have hlawm : ∀ n o, Measurable[hist O σ (n + 1)] fun ω => law n ω o := fun n o =>
    (measurable_of_countable fun s : EpochState => lawS E (n + 1) s o).comp (hσh (n + 1) (n + 1) le_rfl)
  have hfr : ∀ n (f : Ω → ℝ≥0∞), Measurable[hist O σ (n + 1)] f → ∀ o,
      ∫⁻ ω, f ω * (if X n ω = o then 1 else 0) ∂μ = ∫⁻ ω, f ω * ENNReal.ofReal (law n ω o) ∂μ := by
    intro n f hf o
    have h := freeze (m := hist O σ (n + 1)) (μ := μ) (hm _) (hσh (n + 1) (n + 1) le_rfl) (hO.meas (n + 1))
      (hfresh (n + 1)) (g := fun s T => slotOut E (n + 1) s T) (fun s => measurable_slotOut E (n + 1) s) o hf
    refine h.trans (lintegral_congr fun ω => ?_)
    rw [slot_law hO hA.nodup (n + 1) (σ ω (n + 1)) (hst ω (n + 1)).nodup o]
    rfl
  have hEL : 0 < E.c.epochLength := by omega
  have hconst : ∀ ω i, σ ω i = σ ω (i / E.c.epochLength * E.c.epochLength) := fun ω i =>
    σE_const (E.withO (O ω)) (es ω) hEL i
  -- the rates' lower bound in band
  set m : ℝ := ((E.c.period : ℝ) - 1) * (T.ylo * T.clo) with hmdef
  have hyc : 0 ≤ T.ylo * T.clo := mul_nonneg (mul_nonneg (by linarith [hT.β1]) hT.lo_pos.le) hT.clo0
  have hmH : ∀ ω e, InB E T (σ ω) e → m ≤ hrate E (σ ω) e := by
    intro ω e he
    unfold hrate
    calc m ≤ ((win E e).card : ℝ) * (T.ylo * T.clo) := by
          refine mul_le_mul_of_nonneg_right ?_ hyc
          have := card_win (E := E) e
          have : ((E.c.period - 1 : ℕ) : ℝ) ≤ (win E e).card := by exact_mod_cast this
          rw [Nat.cast_sub hP1] at this; simpa using this
      _ = ∑ k ∈ win E e, T.ylo * T.clo := by rw [Finset.sum_const, nsmul_eq_mul]
      _ ≤ _ := Finset.sum_le_sum fun k hk =>
          rate_hon_lo hc hT (hst ω (k + 1)) (he (k + 1) (mem_win hP1 hPEL hk).1 (mem_win hP1 hPEL hk).2)
  have hmW : ∀ ω e, InB E T (σ ω) e → m ≤ wrate E (σ ω) e := fun ω e he =>
    le_trans (hmH ω e he) (Finset.sum_le_sum fun k _ => rate_hon_le_occ hO.pos _ _)
  -- the first epoch out of band follows an atypical window
  set Lo : ℕ → Set Ω := fun e => {ω | InB E T (σ ω) e ∧ ¬ (1 - T.δ) * hrate E (σ ω) e ≤ hcnt E (fun k => X k ω) e}
  set Hi : ℕ → Set Ω := fun e => {ω | InB E T (σ ω) e ∧ ¬ wcnt E (fun k => X k ω) e ≤ (1 + T.δ) * wrate E (σ ω) e}
  have hsub : {ω | ∃ e < Ne, ¬ InB E T (σ ω) e} ⊆ ⋃ e ∈ Finset.range Ne, (Lo e ∪ Hi e) := by
    intro ω hω
    have hex : ∃ e, e < Ne ∧ ¬ InB E T (σ ω) e := hω
    obtain ⟨h1, h2⟩ := Nat.find_spec hex
    have hmin : ∀ e < Nat.find hex, ¬ (e < Ne ∧ ¬ InB E T (σ ω) e) := fun e he => Nat.find_min hex he
    obtain ⟨e, he⟩ : ∃ e, Nat.find hex = e + 1 := by
      rcases hz : Nat.find hex with _ | e
      · rw [hz] at h2; exact absurd (h0 ω) h2
      · exact ⟨e, rfl⟩
    rw [he] at h1 h2 hmin
    have hin : InB E T (σ ω) e := by
      by_contra h; exact hmin e (by omega) ⟨by omega, h⟩
    simp only [Set.mem_iUnion, Finset.mem_range]
    refine ⟨e, by omega, ?_⟩
    by_contra hno
    simp only [Set.mem_union, Lo, Hi, Set.mem_setOf_eq, not_or, not_and, not_not] at hno
    exact h2 (band_step hc hT hb hprec hPf hP1 hPEL (hconst ω) (hst ω) hin ⟨hno.1 hin, hno.2 hin⟩
      (hrec ω e (by omega)) (hpath ω e (by omega)))
  have hLo : ∀ e, μ (Lo e) ≤ ENNReal.ofReal (exp (-(m * T.δ ^ 2 / 2))) := fun e =>
    chernoff_lo X hXm (fun n => hist O σ (n + 1)) (fun n => hm _) hFm hXh law hlaw0 hlaw1 hlawm hfr honA
      (win E e) hT.δ0.le (Lo e) fun ω ⟨hin, hno⟩ => ⟨lt_of_not_ge hno, hmH ω e hin⟩
  have hHi : ∀ e, μ (Hi e) ≤ ENNReal.ofReal (exp (-(m * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)))) := fun e =>
    chernoff_hi X hXm (fun n => hist O σ (n + 1)) (fun n => hm _) hFm hXh law hlaw0 hlaw1 hlawm hfr occA
      (win E e) hT.δ0.le hT.δ1 (Hi e) fun ω ⟨hin, hno⟩ => ⟨lt_of_not_ge hno, hmW ω e hin⟩
  calc μ {ω | ∃ e < Ne, ¬ InB E T (σ ω) e} ≤ μ (⋃ e ∈ Finset.range Ne, (Lo e ∪ Hi e)) := measure_mono hsub
    _ ≤ ∑ e ∈ Finset.range Ne, μ (Lo e ∪ Hi e) := measure_biUnion_finset_le _ _
    _ ≤ ∑ e ∈ Finset.range Ne, ENNReal.ofReal (bandEps T E.c.period) := by
        refine Finset.sum_le_sum fun e _ => (measure_union_le _ _).trans ?_
        unfold bandEps
        rw [ENNReal.ofReal_add (exp_pos _).le (exp_pos _).le]
        exact add_le_add (hLo e) (hHi e)
    _ = Ne * ENNReal.ofReal (bandEps T E.c.period) := by rw [Finset.sum_const, Finset.card_range, nsmul_eq_mul]

end RO


end Cryptarchia.Prob
