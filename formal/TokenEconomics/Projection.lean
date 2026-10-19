import TokenEconomics.Pools

/-!
# The 10-year supply projection

Block Rewards, *Annex: Supply Projection*. The projection is a simulation with behavioral
assumptions and noise, whose 20 runs give a net circulating growth of `3.00%` of `S_cap` after
10 years (`2.81%` to `3.18%`). A simulation's outcome cannot be proven; what can:

* **`reserve_drain_le`**: whatever the stake and the fees, the reserve releases at most
  `MAX_RELEASE · N` units over `N` blocks, so below `10%` of `S_cap` over 10 years
  (`reserve_drain_ten_years`), and it is never exhausted within them;
* **`net_growth_le`**: from a state with an empty pool and nothing pending, as at Genesis, the
  net circulating growth of a run (leader shares and pending Blend share, less pooled fees) is at
  most what the reserve released; block by block it is not (`block_growth_exceeds_release`);
* **`steady_growth`**: with the stake and the pooled fees `D` per block constant, the circulating
  supply grows by `A (I_max S_cap Δ - D)` per block; at the target stake with fees pooled at
  `0.5%` a year, `A = 1/2` and the growth is `0.25%` of `S_cap` a year (`steady_quarter`), as the
  annex says;
* **`clip_symmetric`**: with a noise symmetric around `0` added to an emission factor of `1/2`,
  the clipped factor still averages exactly `1/2`, which is why the noise of the inferred stake,
  large as it is (25 units of `A` per unit of deviation), leaves the long-run average at one half;
* **`noiseFree_growth`**: the scenario of the annex without noise, `δ(t) = 10^{-t}` (time in
  years: `e^{-t/τ}` with `τ = 2/ln 100`) and fees pooled at `0.5% (1 - 10^{-t})` a year, with the
  continuous approximation `R̄ = D`, grows the circulating supply by
  `∫₀¹⁰ min(1, 1/2 + 24.5·10^{-t}) (1% - 0.5% (1 - 10^{-t})) dt ∈ (3.246%, 3.248%)` of `S_cap`.
  The annex's `3.00%` (all 20 runs below `3.18%`) is therefore the effect of its noise, which
  lowers the growth by about a quarter of a point, as the annex states (`3.25%` without the
  noise, `3.10%` with half of it, `2.94%` with twice as much).
-/

namespace TokenEconomics

open Real MeasureTheory

/-! ## Any run -/

/-- A run of blocks: the stake and the pooled fees of each block. -/
def runRewards (st : RewardState) : List (ℕ × ℕ) → RewardState
  | [] => st
  | b :: bs => runRewards (rewardStep st b.1 b.2).1 bs

/-- **The reserve releases at most `MAX_RELEASE` units per block**, whatever the stake and the
fees. -/
theorem reserve_drain_le (st : RewardState) (bs : List (ℕ × ℕ)) :
    st.reserve ≤ (runRewards st bs).reserve + MAX_RELEASE * bs.length ∧
      (runRewards st bs).reserve ≤ st.reserve := by
  induction bs generalizing st with
  | nil => simp [runRewards]
  | cons b bs ih =>
    obtain ⟨h1, h2⟩ := reserve_step (st := st) b.1 b.2
    obtain ⟨i1, i2⟩ := ih (rewardStep st b.1 b.2).1
    simp only [runRewards, List.length_cons, Nat.mul_succ]
    generalize MAX_RELEASE * bs.length = k at i1 ⊢
    constructor <;> omega

/-- Over 10 years of blocks, at most `999,999,999,996,912,000` units leave the reserve, less than
the `10¹⁸` of the reserve (`10%` of `S_cap`), which is never exhausted. -/
theorem reserve_drain_ten_years :
    MAX_RELEASE * (10 * BLOCKS_PER_YEAR) = 999_999_999_996_912_000 ∧
      999_999_999_996_912_000 < 10 ^ 18 := by decide

/-- The leader shares of a run of blocks. -/
def runLeader (st : RewardState) : List (ℕ × ℕ) → ℕ
  | [] => 0
  | b :: bs => leaderShare (rewardStep st b.1 b.2).2 + runLeader (rewardStep st b.1 b.2).1 bs

/-- The fees pooled in a run of blocks. -/
def runPooled (bs : List (ℕ × ℕ)) : ℕ := (bs.map Prod.snd).sum

/-- A run moves tokens between the stocks: what leaves the reserve and the pool, with the fees
pooled in the run, is the leader shares and the growth of the pending Blend share. -/
theorem runRewards_conserves {st : RewardState} (I : PoolInv st) (bs : List (ℕ × ℕ)) :
    (runRewards st bs).reserve + (runRewards st bs).pool + (runRewards st bs).pending +
        runLeader st bs = st.reserve + st.pool + st.pending + runPooled bs := by
  induction bs generalizing st with
  | nil => simp [runRewards, runLeader, runPooled]
  | cons b bs ih =>
    have h1 := rewardStep_conserves I b.1 b.2
    have h2 := ih (poolInv_rewardStep I b.1 b.2)
    simp only [runRewards, runLeader, runPooled, List.map_cons, List.sum_cons] at h2 ⊢
    omega

/-- **Net circulating growth is at most what leaves the reserve**: from a state with an empty
pool and nothing pending, as at Genesis, the leader shares of a run and the Blend share pending
at its end, less the fees pooled in it, are at most what the reserve released, so at most
`MAX_RELEASE` units per block. The bound holds over a run from such a state, not block by block
(`block_growth_exceeds_release`); the proof of work pool, which drains into circulation too, is
not counted. -/
theorem net_growth_le {st : RewardState} (I : PoolInv st) (hp : st.pool = 0)
    (he : st.pending = 0) (bs : List (ℕ × ℕ)) :
    ((runLeader st bs + (runRewards st bs).pending : ℕ) : ℤ) - runPooled bs ≤
        (st.reserve : ℤ) - (runRewards st bs).reserve ∧
      st.reserve ≤ (runRewards st bs).reserve + MAX_RELEASE * bs.length := by
  have h := runRewards_conserves I bs
  refine ⟨?_, (reserve_drain_le st bs).1⟩
  rw [hp, he] at h
  push_cast
  omega

/-- One block can put far more than `MAX_RELEASE` into circulation, from the pool: at a stake
above its target with fees in the window, nothing is released and the pool pays the average
pooled fee, here more than ten times `MAX_RELEASE`. -/
theorem block_growth_exceeds_release :
    PoolInv ⟨10 ^ 18, 120 * 10 ^ 12, 0, List.replicate 120 (10 ^ 12)⟩ ∧
      (rewardStep ⟨10 ^ 18, 120 * 10 ^ 12, 0, List.replicate 120 (10 ^ 12)⟩ (10 ^ 19) 0).1.reserve =
        10 ^ 18 ∧
      10 * MAX_RELEASE < (rewardStep ⟨10 ^ 18, 120 * 10 ^ 12, 0, List.replicate 120 (10 ^ 12)⟩
        (10 ^ 19) 0).2 := by
  refine ⟨⟨by decide +kernel, by decide +kernel⟩, by decide +kernel, by decide +kernel⟩

/-! ## The steady state -/

/-- **Steady growth.** With the stake fixed and the pooled fees `D` of every block of the window,
the reward is `A m + (1 - A) D`, so the circulating supply grows by `A (m - D)` per block. -/
theorem steady_growth (D0 D : ℝ) :
    reward D0 (T * D) - D = emissionFactor D0 (T * D) * (maxRelease - D) := by
  simp only [reward, avgPooled, T]
  field_simp
  ring

/-- **At the target stake with fees pooled at `0.5%` of `S_cap` a year, `A = 1/2` and the
supply grows by `0.25%` of `S_cap` a year.** -/
theorem steady_quarter :
    let D : ℝ := 0.005 * S_CAP / BLOCKS_PER_YEAR
    emissionFactor D0_TARGET (T * D) = 1 / 2 ∧
      (reward D0_TARGET (T * D) - D) * BLOCKS_PER_YEAR / S_CAP = 0.0025 := by
  intro D
  have hA : emissionFactor D0_TARGET (T * D) = 1 / 2 := by
    simp only [emissionFactor, stakeDeviation, poolingRate, D, D0_TARGET, D1_TARGET, DELTA,
      ALPHA_D, ALPHA_A, I_MIN, I_MAX, T, S_CAP, BLOCKS_PER_YEAR]
    norm_num
  refine ⟨hA, ?_⟩
  rw [steady_growth, hA]
  simp only [maxRelease, D, I_MAX, S_CAP, DELTA, BLOCKS_PER_YEAR]
  norm_num

/-! ## Symmetric noise -/

/-- The emission factor clipped to `[0, 1]`. -/
noncomputable def clip (x : ℝ) : ℝ := min 1 (max 0 x)

theorem clip_add_clip (x : ℝ) : clip (1 / 2 + x) + clip (1 / 2 - x) = 1 := by
  unfold clip
  rcases le_total x (-1 / 2) with h | h
  · rw [max_eq_left (by linarith), min_eq_right (by linarith), max_eq_right (by linarith),
      min_eq_left (by linarith)]
    norm_num
  rcases le_total x (1 / 2) with h' | h'
  · rw [max_eq_right (by linarith), min_eq_right (by linarith), max_eq_right (by linarith),
      min_eq_right (by linarith)]
    ring
  · rw [max_eq_right (by linarith), min_eq_left (by linarith), max_eq_left (by linarith),
      min_eq_right (by linarith)]
    norm_num

theorem continuous_clip : Continuous clip :=
  continuous_const.min (continuous_const.max continuous_id)

/-- **A symmetric noise leaves an emission factor of `1/2` at `1/2` on average**: for a noise
`X` whose law `μ` is symmetric, `E[clip(1/2 + X)] = 1/2`. -/
theorem clip_symmetric (μ : Measure ℝ) [IsProbabilityMeasure μ] (hμ : μ.map Neg.neg = μ) :
    ∫ x, clip (1 / 2 + x) ∂μ = 1 / 2 := by
  have hb : ∀ x, |clip x| ≤ 1 := by
    intro x; unfold clip
    rw [abs_le]; constructor
    · exact le_trans (by norm_num) (le_min (by norm_num) (le_max_left _ _))
    · exact min_le_left _ _
  have hi : ∀ g : ℝ → ℝ, Continuous g → Integrable (fun x => clip (g x)) μ := by
    intro g hg
    refine Integrable.of_bound (Continuous.aestronglyMeasurable (continuous_clip.comp hg)) 1
      (Filter.Eventually.of_forall fun x => ?_)
    simpa [Real.norm_eq_abs] using hb (g x)
  have hp := hi (fun x => 1 / 2 + x) (by fun_prop)
  have hm := hi (fun x => 1 / 2 - x) (by fun_prop)
  have hneg : ∫ x, clip (1 / 2 - x) ∂μ = ∫ x, clip (1 / 2 + x) ∂μ := by
    conv_rhs => rw [← hμ]
    rw [integral_map measurable_neg.aemeasurable
      (Continuous.aestronglyMeasurable (f := fun x => clip (1 / 2 + x))
        (continuous_clip.comp (by fun_prop)))]
    simp [sub_eq_add_neg]
  have hsum : ∫ x, (clip (1 / 2 + x) + clip (1 / 2 - x)) ∂μ = 1 := by
    have : ∀ x, clip (1 / 2 + x) + clip (1 / 2 - x) = 1 := clip_add_clip
    simp only [this]
    simp
  rw [integral_add hp hm, hneg] at hsum
  linarith

/-! ## The scenario without noise -/

/-- The stake deviation and the fraction of the remaining pooling of the scenario at `t` years:
`e^{-t/τ} = 10^{-t}`. -/
noncomputable def decay (t : ℝ) : ℝ := exp (-(t * log 10))

/-- The scenario's growth rate of the circulating supply, in fractions of `S_cap` a year: the
emission factor `min(1, 25 δ + p / 1%)` times `1% - p`, the fees pooled being
`p = 0.5% (1 - δ)`. -/
noncomputable def growthRate (t : ℝ) : ℝ :=
  min 1 (25 * decay t + (0.005 * (1 - decay t)) / 0.01) * (0.01 - 0.005 * (1 - decay t))

/-- The year at which the emission factor leaves `1`: `10^{-T₁} = 1/49`. -/
noncomputable def T1 : ℝ := log 49 / log 10

theorem decay_pos (t : ℝ) : 0 < decay t := exp_pos _

theorem decay_T1 : decay T1 = 1 / 49 := by
  unfold decay T1
  rw [div_mul_cancel₀ _ (log_pos (by norm_num : (1 : ℝ) < 10)).ne', exp_neg, exp_log (by norm_num)]
  norm_num

theorem decay_ten : decay 10 = 1 / 10 ^ 10 := by
  unfold decay
  rw [exp_neg, show 10 * log 10 = log (10 ^ 10) by rw [log_pow]; norm_num, exp_log (by norm_num)]
  norm_num

theorem decay_anti {s t : ℝ} (h : s ≤ t) : decay t ≤ decay s := by
  unfold decay
  apply exp_le_exp.2
  have := log_pos (by norm_num : (1 : ℝ) < 10)
  nlinarith

theorem hasDerivAt_decay (t : ℝ) : HasDerivAt decay (-(log 10) * decay t) t := by
  unfold decay
  have h := (((hasDerivAt_id t).mul_const (log 10)).neg).exp
  refine h.congr_deriv ?_
  simp only [Pi.neg_apply, id, one_mul]
  ring

@[fun_prop] theorem continuous_decay : Continuous decay := by
  unfold decay; fun_prop

theorem continuous_growthRate : Continuous growthRate := by
  unfold growthRate
  exact (continuous_const.min (by fun_prop)).mul (by fun_prop)

/-- The rate on each side of `T₁`. -/
theorem growthRate_early {t : ℝ} (h : t ≤ T1) :
    growthRate t = 0.005 + 0.005 * decay t := by
  have : decay T1 ≤ decay t := decay_anti h
  rw [decay_T1] at this
  unfold growthRate
  have e : 25 * decay t + 0.005 * (1 - decay t) / 0.01 = 0.5 + 24.5 * decay t := by ring
  rw [e, min_eq_left (by linarith)]
  ring

theorem growthRate_late {t : ℝ} (h : T1 ≤ t) :
    growthRate t = 0.005 * (0.5 + 25 * decay t + 24.5 * decay t ^ 2) := by
  have : decay t ≤ decay T1 := decay_anti h
  rw [decay_T1] at this
  unfold growthRate
  have e : 25 * decay t + 0.005 * (1 - decay t) / 0.01 = 0.5 + 24.5 * decay t := by ring
  rw [e, min_eq_right (by linarith)]
  ring

/-- The antiderivatives of the two phases. -/
noncomputable def F1 (t : ℝ) : ℝ := 0.005 * t - 0.005 * decay t / log 10
noncomputable def F2 (t : ℝ) : ℝ :=
  0.005 * (0.5 * t - 25 * decay t / log 10 - 24.5 * decay t ^ 2 / (2 * log 10))

theorem hasDerivAt_F1 (t : ℝ) : HasDerivAt F1 (0.005 + 0.005 * decay t) t := by
  have hl := (log_pos (by norm_num : (1 : ℝ) < 10)).ne'
  unfold F1
  have h := ((hasDerivAt_id t).const_mul (0.005 : ℝ)).sub
    (((hasDerivAt_decay t).const_mul (0.005 : ℝ)).div_const (log 10))
  exact h.congr_deriv (by field_simp; ring)

theorem hasDerivAt_F2 (t : ℝ) :
    HasDerivAt F2 (0.005 * (0.5 + 25 * decay t + 24.5 * decay t ^ 2)) t := by
  have hl := (log_pos (by norm_num : (1 : ℝ) < 10)).ne'
  unfold F2
  have h1 := ((hasDerivAt_decay t).const_mul (25 : ℝ)).div_const (log 10)
  have h2 := (((hasDerivAt_decay t).pow 2).const_mul (24.5 : ℝ)).div_const (2 * log 10)
  have h := ((((hasDerivAt_id t).const_mul (0.5 : ℝ)).sub h1).sub h2).const_mul (0.005 : ℝ)
  exact h.congr_deriv (by field_simp; ring)

/-- The closed form of the growth over 10 years. -/
theorem noiseFree_eq :
    ∫ t in (0 : ℝ)..10, growthRate t = (F1 T1 - F1 0) + (F2 10 - F2 T1) := by
  have hT1 : 0 ≤ T1 := div_nonneg (log_nonneg (by norm_num)) (log_nonneg (by norm_num))
  have hT10 : T1 ≤ 10 := by
    unfold T1
    rw [div_le_iff₀ (log_pos (by norm_num))]
    have : log 49 ≤ log (10 ^ 10) := log_le_log (by norm_num) (by norm_num)
    rw [log_pow] at this; push_cast at this; linarith
  have hi : ∀ a b : ℝ, IntervalIntegrable growthRate volume a b :=
    fun a b => continuous_growthRate.intervalIntegrable a b
  rw [← intervalIntegral.integral_add_adjacent_intervals (hi 0 T1) (hi T1 10)]
  congr 1
  · rw [intervalIntegral.integral_congr (g := fun t => 0.005 + 0.005 * decay t) (by
      intro t ht; rw [Set.uIcc_of_le hT1] at ht; exact growthRate_early ht.2)]
    exact intervalIntegral.integral_eq_sub_of_hasDerivAt (fun t _ => hasDerivAt_F1 t)
      ((continuous_const.add (continuous_const.mul continuous_decay)).intervalIntegrable _ _)
  · rw [intervalIntegral.integral_congr (g := fun t => 0.005 * (0.5 + 25 * decay t +
        24.5 * decay t ^ 2)) (by
      intro t ht; rw [Set.uIcc_of_le hT10] at ht; exact growthRate_late ht.1)]
    exact intervalIntegral.integral_eq_sub_of_hasDerivAt (fun t _ => hasDerivAt_F2 t)
      (by apply Continuous.intervalIntegrable; fun_prop)

theorem log_bounds_aux {x : ℝ} (hx0 : 0 ≤ x) (hx1 : x < 1) :
    |(∑ i ∈ Finset.range 8, x ^ (i + 1) / (i + 1)) + log (1 - x)| ≤ x ^ 9 / (1 - x) := by
  have := abs_log_sub_add_sum_range_le (x := x) (by rw [abs_of_nonneg hx0]; exact hx1) 8
  rwa [abs_of_nonneg hx0] at this

/-- **Without noise, the scenario grows the circulating supply by `3.247%` of `S_cap` over
10 years.** -/
theorem noiseFree_growth :
    0.03246 < ∫ t in (0 : ℝ)..10, growthRate t ∧ ∫ t in (0 : ℝ)..10, growthRate t < 0.03248 := by
  rw [noiseFree_eq]
  simp only [F1, F2, decay_T1, decay_ten]
  have h0 : decay 0 = 1 := by simp [decay]
  rw [h0]
  -- log 10 = 3 log 2 - log (1 - 1/5), log 49 = 2 (3 log 2 + log (1 - 1/8))
  have l2a := log_two_gt_d9
  have l2b := log_two_lt_d9
  have h5 := log_bounds_aux (x := (1 / 5 : ℝ)) (by norm_num) (by norm_num)
  have h8 := log_bounds_aux (x := (1 / 8 : ℝ)) (by norm_num) (by norm_num)
  simp only [Finset.sum_range_succ, Finset.sum_range_zero] at h5 h8
  rw [abs_le] at h5 h8
  norm_num at h5 h8
  have e10 : log 10 = 3 * log 2 - log (4 / 5) := by
    rw [show (10 : ℝ) = 2 ^ 3 / (4 / 5) by norm_num, log_div (by norm_num) (by norm_num),
      log_pow]; push_cast; ring
  have e49 : log 49 = 2 * (3 * log 2 + log (7 / 8)) := by
    rw [show (49 : ℝ) = (2 ^ 3 * (7 / 8)) ^ 2 by norm_num, log_pow, log_mul (by norm_num)
      (by norm_num), log_pow]; push_cast; ring
  have hL : 2.302 < log 10 ∧ log 10 < 2.303 := by
    rw [e10]; constructor <;> nlinarith [h5.1, h5.2]
  have hT : 1.6901 < T1 ∧ T1 < 1.6903 := by
    unfold T1
    rw [e49, e10]
    constructor
    · rw [lt_div_iff₀ (by nlinarith [h5.1, h5.2])]; nlinarith [h5.1, h5.2, h8.1, h8.2]
    · rw [div_lt_iff₀ (by nlinarith [h5.1, h5.2])]; nlinarith [h5.1, h5.2, h8.1, h8.2]
  obtain ⟨hL1, hL2⟩ := hL
  obtain ⟨hT1, hT2⟩ := hT
  have hLp : 0 < log 10 := by linarith
  constructor
  · rw [← sub_pos]
    have : (0 : ℝ) < 1 := one_pos
    field_simp
    nlinarith
  · rw [← sub_pos]
    field_simp
    nlinarith

end TokenEconomics
