import MiningOnboarding.Model

/-!
# §§13–18 Continuing entry: cohorts, time-dependent incomes, delayed unlocking

From §13 on, `t = 0` may be the arrival of a cohort rather than genesis, newcomers arrive
every epoch (§14), and mining income `m_i(t)` and the leadership pot `P_L(t)` depend on
time. Mining income is piecewise constant under either allocation policy of §15 (it jumps
when a cohort arrives), so here it is only assumed integrable on bounded intervals
(`LocInt`) and continuous off a countable set `D` of times (e.g. the epoch boundaries).
The equations then hold off `D`. The leadership return per unit stake
`r(t) = P_L(t) / S_tot(t)` is a given continuous function.

* `Stot_integral`, `pool_integral`: `S_tot(t) = S₀ + ∫₀ᵗ (M + P_L)` and
  `R(t) = R₀ - ∫₀ᵗ M` (§14, boxed), from the summed equations (`sum_hasDerivAt`).
* `stakeInt`: `s_i(t) = ∫_{t_i}^t m_i(u) exp(∫_u^t r) du` (§16, boxed).
  `stakeInt_solves` and **`stakeInt_unique`**: it solves `ds/dt = m + r s`, `s(t_i) = 0`,
  and is the only solution.
* `unlockedPre_eq`: before mining unlocks,
  `b_i(t) = ∫_{t_i}^t m_i(u)[exp(∫_u^t r) - (1 - β)] du` (§16, boxed), and
  `hasDerivAt_unlockedPre`: `db/dt = β m + r s`.
* `lockedBal`, `unlockedBal`: `k_i(t) = (1 - β) ∫_{max(t_i, t-L)}^t m_i` and `b = s - k` (§17).
  `hasDerivAt_unlockedBal`: `db/dt = β m(t) + r s + 1{t ≥ t_i + L}(1 - β) m(t - L)` (§17,
  boxed), for `t ≠ t_i + L`. `unlockedBal_eq_pre`: no maturation before `t_i + L`.
* `cohort_exact`: identical members of a cohort follow the representative, so the cohort
  contributes `n_e s_e` to stake and `n_e m_e` to payout (§18).
* `tau`, `tau_lt_iff`: `τ_i = inf{a ≥ 0 : b_i(t_i + a) ≥ K_B}`, `∞` if never (§19, boxed);
  `τ_i < L ⟺ ∃ a < L, b_i(t_i + a) ≥ K_B`. `unlockedPre_monotoneOn`: the balance before
  maturation is nondecreasing, so qualification persists until maturation (`qualified_mono`).
* `Qe`, `Qe_identical`: `Q_e = (1/n_e) ∑ 1{τ_i < L}` (§19, boxed) is `0` or `1` for
  identical members.
* **`stakeInt_eq_stake`**: consistency with §§6–7. For a cohort at `t = 0` with constant
  `m`, `M`, `P_L`, the integral formula is the closed form `stake`, and the unlocked
  balance is `unlocked`.
-/

open Real Set MeasureTheory intervalIntegral
open scoped ENNReal NNReal

namespace Onboarding

/-! ## Calculus helpers -/

/-- Integrable on every bounded interval. -/
def LocInt (m : ℝ → ℝ) : Prop := ∀ a b, IntervalIntegrable m volume a b

theorem LocInt.smaf {m : ℝ → ℝ} (hm : LocInt m) (t : ℝ) :
    StronglyMeasurableAtFilter m (nhds t) volume :=
  ⟨Ioc (t - 1) (t + 1), Ioc_mem_nhds (by linarith) (by linarith),
    (hm (t - 1) (t + 1)).1.aestronglyMeasurable⟩

theorem LocInt.hasDerivAt_primitive {m : ℝ → ℝ} (hm : LocInt m) (a : ℝ) {t : ℝ}
    (hct : ContinuousAt m t) : HasDerivAt (fun t => ∫ u in a..t, m u) (m t) t :=
  integral_hasDerivAt_right (hm a t) (hm.smaf t) hct

theorem LocInt.continuous_primitive {m : ℝ → ℝ} (hm : LocInt m) (a : ℝ) :
    Continuous (fun t => ∫ u in a..t, m u) :=
  intervalIntegral.continuous_primitive hm a

theorem LocInt.mul_continuous {m c : ℝ → ℝ} (hm : LocInt m) (hc : Continuous c) :
    LocInt (fun u => m u * c u) := fun a b => (hm a b).mul_continuousOn hc.continuousOn

/-- Fundamental theorem of calculus with countably many exceptional times: a function
continuous on `[t₀, ∞)` with derivative `φ` on `(t₀, ∞) \ D` is `f(t₀) + ∫_{t₀}^t φ`. -/
theorem eq_integral_of_hasDerivAt {f φ : ℝ → ℝ} {t0 : ℝ} {D : Set ℝ} (hD : D.Countable)
    (hc : ContinuousOn f (Ici t0)) (hφ : LocInt φ) (hd : ∀ t ∈ Ioi t0 \ D, HasDerivAt f (φ t) t) :
    ∀ t ≥ t0, f t = f t0 + ∫ u in t0..t, φ u := by
  intro t ht
  have := integral_eq_of_hasDerivAt_off_countable_of_le f φ ht hD
    (hc.mono Icc_subset_Ici_self) (fun x hx => hd x ⟨hx.1.1, hx.2⟩) (hφ t0 t)
  linarith

/-- Constant on `[t₀, ∞)` if the derivative vanishes off a countable set. -/
theorem const_of_hasDerivAt_zero {f : ℝ → ℝ} {t0 : ℝ} {D : Set ℝ} (hD : D.Countable)
    (hc : ContinuousOn f (Ici t0)) (hd : ∀ t ∈ Ioi t0 \ D, HasDerivAt f 0 t) :
    ∀ t ≥ t0, f t = f t0 := by
  intro t ht
  have := eq_integral_of_hasDerivAt hD hc (fun a b => intervalIntegrable_const) hd t ht
  simpa using this

/-! ## §14 Aggregate stake and pool -/

/-- Summing the stake equations: off `D`, `S_tot = S_E + ∑ s_i` has derivative
`M(t) + P_L(t)` wherever `S_tot ≠ 0`, with `M(t) = ∑ m_i(t)`. -/
theorem sum_hasDerivAt {ι : Type*} [Fintype ι] {PL SE : ℝ → ℝ} {m s : ι → ℝ → ℝ} {t : ℝ}
    (hs : ∀ i, HasDerivAt (s i) (m i t + PL t * s i t / (SE t + ∑ j, s j t)) t)
    (hSE : HasDerivAt SE (PL t * SE t / (SE t + ∑ j, s j t)) t)
    (hpos : SE t + ∑ j, s j t ≠ 0) :
    HasDerivAt (fun t => SE t + ∑ j, s j t) (∑ i, m i t + PL t) t := by
  convert hSE.add (HasDerivAt.fun_sum (u := Finset.univ) fun i _ => hs i) using 1
  rw [Finset.sum_add_distrib, ← Finset.sum_div, ← Finset.mul_sum]
  field_simp
  ring

/-- §14: `S_tot(t) = S₀ + ∫₀ᵗ [M(u) + P_L(u)] du`. -/
theorem Stot_integral {S M PL : ℝ → ℝ} {D : Set ℝ} (hD : D.Countable)
    (hc : ContinuousOn S (Ici 0)) (hMP : LocInt fun u => M u + PL u)
    (hd : ∀ t ∈ Ioi 0 \ D, HasDerivAt S (M t + PL t) t) :
    ∀ t ≥ 0, S t = S 0 + ∫ u in (0 : ℝ)..t, (M u + PL u) :=
  eq_integral_of_hasDerivAt hD hc hMP hd

/-- §14: `R(t) = R₀ - ∫₀ᵗ M(u) du`. The pool is shared across cohorts and never reset. -/
theorem pool_integral {R M : ℝ → ℝ} {D : Set ℝ} (hD : D.Countable)
    (hc : ContinuousOn R (Ici 0)) (hM : LocInt M) (hd : ∀ t ∈ Ioi 0 \ D, HasDerivAt R (-M t) t) :
    ∀ t ≥ 0, R t = R 0 - ∫ u in (0 : ℝ)..t, M u := by
  intro t ht
  have := eq_integral_of_hasDerivAt hD hc (fun a b => (hM a b).neg) hd t ht
  simp only [Pi.neg_apply, intervalIntegral.integral_neg] at this
  linarith

/-! ## §16 The integrating-factor solution -/

variable {r m : ℝ → ℝ} {ti : ℝ}

/-- The integrating factor `G(t) = exp(∫_{t_i}^t r)`. -/
noncomputable def growth (r : ℝ → ℝ) (ti t : ℝ) : ℝ := exp (∫ v in ti..t, r v)

/-- §16: `s_i(t) = ∫_{t_i}^t m_i(u) exp(∫_u^t r(v) dv) du`. A mining payment received at
`u` is amplified by the leadership income it earns between `u` and `t`. -/
noncomputable def stakeInt (r m : ℝ → ℝ) (ti t : ℝ) : ℝ :=
  ∫ u in ti..t, m u * exp (∫ v in u..t, r v)

theorem growth_pos (r : ℝ → ℝ) (ti t : ℝ) : 0 < growth r ti t := exp_pos _

theorem hasDerivAt_growth (hr : Continuous r) (ti t : ℝ) :
    HasDerivAt (growth r ti) (r t * growth r ti t) t := by
  have := ((hr.integral_hasStrictDerivAt ti t).hasDerivAt).exp
  unfold growth; convert this using 1; ring

theorem continuous_growth (hr : Continuous r) (ti : ℝ) : Continuous (growth r ti) :=
  continuous_iff_continuousAt.mpr fun t => (hasDerivAt_growth hr ti t).continuousAt

theorem continuous_growth_inv (hr : Continuous r) (ti : ℝ) :
    Continuous fun u => (growth r ti u)⁻¹ :=
  (continuous_growth hr ti).inv₀ fun u => (growth_pos r ti u).ne'

/-- `exp(∫_u^t r) = G(t)/G(u)`. -/
theorem exp_integral_eq (hr : Continuous r) (ti u t : ℝ) :
    exp (∫ v in u..t, r v) = growth r ti t / growth r ti u := by
  rw [growth, growth, ← exp_sub,
    integral_interval_sub_left (hr.intervalIntegrable _ _) (hr.intervalIntegrable _ _)]

/-- `s(t) = G(t) ∫_{t_i}^t m/G`. -/
theorem stakeInt_eq (hr : Continuous r) (ti t : ℝ) :
    stakeInt r m ti t = growth r ti t * ∫ u in ti..t, m u * (growth r ti u)⁻¹ := by
  unfold stakeInt
  simp_rw [exp_integral_eq hr ti]
  rw [← intervalIntegral.integral_const_mul]
  congr 1; funext u; ring

theorem stakeInt_self : stakeInt r m ti ti = 0 := by simp [stakeInt]

theorem continuous_stakeInt (hr : Continuous r) (hm : LocInt m) (ti : ℝ) :
    Continuous (stakeInt r m ti) := by
  have : stakeInt r m ti = fun t => growth r ti t * ∫ u in ti..t, m u * (growth r ti u)⁻¹ :=
    funext (stakeInt_eq hr ti)
  rw [this]
  exact (continuous_growth hr ti).mul
    ((hm.mul_continuous (continuous_growth_inv hr ti)).continuous_primitive ti)

/-- `ds/dt = m(t) + r(t) s(t)` wherever `m` is continuous. -/
theorem hasDerivAt_stakeInt (hr : Continuous r) (hm : LocInt m) {t : ℝ}
    (hct : ContinuousAt m t) :
    HasDerivAt (stakeInt r m ti) (m t + r t * stakeInt r m ti t) t := by
  have hG := hasDerivAt_growth hr ti t
  have hGi := continuous_growth_inv hr ti
  have hH := (hm.mul_continuous hGi).hasDerivAt_primitive ti (hct.mul hGi.continuousAt)
  have heq : stakeInt r m ti = fun t => growth r ti t * ∫ u in ti..t, m u * (growth r ti u)⁻¹ :=
    funext (stakeInt_eq hr ti)
  rw [heq]
  convert hG.mul hH using 1
  have := (growth_pos r ti t).ne'
  field_simp
  ring

/-- §16, existence: the integral formula solves the newcomer's stake equation
`ds/dt - r(t) s = m(t)`, `s(t_i) = 0`, off the discontinuities of `m`. -/
theorem stakeInt_solves (hr : Continuous r) (hm : LocInt m) {D : Set ℝ}
    (hmc : ∀ t ∉ D, ContinuousAt m t) :
    ContinuousOn (stakeInt r m ti) (Ici ti) ∧
      (∀ t ∈ Ioi ti \ D, HasDerivAt (stakeInt r m ti) (m t + r t * stakeInt r m ti t) t) ∧
      stakeInt r m ti ti = 0 :=
  ⟨(continuous_stakeInt hr hm ti).continuousOn,
    fun t ht => hasDerivAt_stakeInt hr hm (hmc t ht.2), stakeInt_self⟩

/-- **§16, uniqueness.** Every solution of `ds/dt = m(t) + r(t) s` on `[t_i, ∞)` (off a
countable set) with `s(t_i) = 0` is the integral formula. -/
theorem stakeInt_unique (hr : Continuous r) (hm : LocInt m) {D : Set ℝ} (hD : D.Countable)
    (hmc : ∀ t ∉ D, ContinuousAt m t) {f : ℝ → ℝ} (hc : ContinuousOn f (Ici ti))
    (hd : ∀ t ∈ Ioi ti \ D, HasDerivAt f (m t + r t * f t) t) (h0 : f ti = 0) :
    ∀ t ≥ ti, f t = stakeInt r m ti t := by
  have hq := const_of_hasDerivAt_zero (f := fun t => (f t - stakeInt r m ti t) / growth r ti t)
    hD ((hc.sub (continuous_stakeInt hr hm ti).continuousOn).div
      (continuous_growth hr ti).continuousOn fun t _ => (growth_pos r ti t).ne')
    (fun t ht => by
      have := ((hd t ht).fun_sub (hasDerivAt_stakeInt (ti := ti) hr hm (hmc t ht.2))).fun_div
        (hasDerivAt_growth hr ti t) (growth_pos r ti t).ne'
      convert this using 1
      have := (growth_pos r ti t).ne'
      field_simp
      ring)
  intro t ht
  have := hq t ht
  simp only [h0, stakeInt_self, sub_self, zero_div] at this
  have := (div_eq_zero_iff.mp this).resolve_right (growth_pos r ti t).ne'
  linarith

theorem stakeInt_nonneg (hm0 : ∀ u ≥ ti, 0 ≤ m u) {t : ℝ} (ht : ti ≤ t) :
    0 ≤ stakeInt r m ti t :=
  intervalIntegral.integral_nonneg ht fun u hu => mul_nonneg (hm0 u hu.1) (exp_pos _).le

/-! ## §16 The unlocked balance before maturation -/

/-- Cumulative mining income since arrival, `∫_{t_i}^t m`. -/
noncomputable def mined (m : ℝ → ℝ) (ti t : ℝ) : ℝ := ∫ u in ti..t, m u

/-- Unlocked balance before the first locked reward matures: total stake minus the locked
mining principal, `b(t) = s(t) - (1 - β) ∫_{t_i}^t m`. -/
noncomputable def unlockedPre (β : ℝ) (r m : ℝ → ℝ) (ti t : ℝ) : ℝ :=
  stakeInt r m ti t - (1 - β) * mined m ti t

theorem continuous_exp_integral_left (hr : Continuous r) (t : ℝ) :
    Continuous fun u => exp (∫ v in u..t, r v) := by
  simp_rw [intervalIntegral.integral_symm t]
  exact ((intervalIntegral.continuous_primitive (fun a b => hr.intervalIntegrable a b) t).neg).rexp

/-- §16, boxed: `b_i(t) = ∫_{t_i}^t m_i(u)[exp(∫_u^t r) - (1 - β)] du`. Subtracting `1 - β`
removes only the locked mining principal. -/
theorem unlockedPre_eq (hr : Continuous r) (hm : LocInt m) (β ti t : ℝ) :
    unlockedPre β r m ti t = ∫ u in ti..t, m u * (exp (∫ v in u..t, r v) - (1 - β)) := by
  have h1 := hm.mul_continuous (continuous_exp_integral_left hr t) ti t
  have h2 := (hm ti t).mul_const (1 - β)
  rw [show (∫ u in ti..t, m u * (exp (∫ v in u..t, r v) - (1 - β))) =
      ∫ u in ti..t, (m u * exp (∫ v in u..t, r v) - m u * (1 - β)) by
    congr 1; funext u; ring]
  rw [intervalIntegral.integral_sub h1 h2, intervalIntegral.integral_mul_const]
  unfold unlockedPre stakeInt mined; ring

/-- §16: `db/dt = β m(t) + r(t) s(t)` before maturation. -/
theorem hasDerivAt_unlockedPre (hr : Continuous r) (hm : LocInt m) (β : ℝ) {t : ℝ}
    (hct : ContinuousAt m t) :
    HasDerivAt (unlockedPre β r m ti) (β * m t + r t * stakeInt r m ti t) t := by
  have := (hasDerivAt_stakeInt (ti := ti) hr hm hct).sub
    ((hm.hasDerivAt_primitive ti hct).const_mul (1 - β))
  unfold unlockedPre mined; convert this using 1; ring

/-- Before maturation the unlocked balance is nondecreasing: `db/dt = β m + r s ≥ 0` for
`β ≥ 0`, `m ≥ 0`, `r ≥ 0` (since then `s ≥ 0`). -/
theorem unlockedPre_monotoneOn (hr : Continuous r) (hm : LocInt m) {D : Set ℝ}
    (hD : D.Countable) (hmc : ∀ t ∉ D, ContinuousAt m t) {β : ℝ} (hβ : 0 ≤ β)
    (hm0 : ∀ u ≥ ti, 0 ≤ m u) (hr0 : ∀ u, 0 ≤ r u) :
    MonotoneOn (unlockedPre β r m ti) (Ici ti) := by
  intro x hx y _ hxy
  have hφ : LocInt fun t => β * m t + r t * stakeInt r m ti t := fun a b =>
    ((hm a b).const_mul β).add ((hr.mul (continuous_stakeInt hr hm ti)).intervalIntegrable a b)
  have hcont : ContinuousOn (unlockedPre β r m ti) (Ici x) :=
    ((continuous_stakeInt hr hm ti).sub
      (continuous_const.mul (hm.continuous_primitive ti))).continuousOn
  have := eq_integral_of_hasDerivAt hD hcont hφ
    (fun t ht => hasDerivAt_unlockedPre hr hm β (hmc t ht.2)) y hxy
  rw [this]
  have hx' : ti ≤ x := hx
  refine le_add_of_nonneg_right (intervalIntegral.integral_nonneg hxy fun u hu => ?_)
  have := stakeInt_nonneg (r := r) (hm0 := hm0) (le_trans hx' hu.1)
  have := hm0 u (le_trans hx' hu.1)
  have := hr0 u
  positivity

/-! ## §17 Unlocking after `L` epochs -/

/-- §17, boxed: the remaining locked balance `k_i(t) = (1 - β) ∫_{max(t_i, t-L)}^t m_i`. -/
noncomputable def lockedBal (β : ℝ) (m : ℝ → ℝ) (ti L t : ℝ) : ℝ :=
  (1 - β) * ∫ u in max ti (t - L)..t, m u

/-- §17: `b_i(t) = s_i(t) - k_i(t)`. -/
noncomputable def unlockedBal (β : ℝ) (r m : ℝ → ℝ) (ti L t : ℝ) : ℝ :=
  stakeInt r m ti t - lockedBal β m ti L t

/-- Unlocking changes the classification of holdings, not total stake: `s = k + b`. -/
theorem stake_eq_locked_add_unlockedBal (β ti L t : ℝ) :
    stakeInt r m ti t = lockedBal β m ti L t + unlockedBal β r m ti L t := by
  unfold unlockedBal; ring

theorem lockedBal_eq (hm : LocInt m) (β ti L t : ℝ) :
    lockedBal β m ti L t = (1 - β) * (mined m ti t - mined m ti (max ti (t - L))) := by
  unfold lockedBal mined; rw [integral_interval_sub_left (hm _ _) (hm _ _)]

/-- Nothing matures before `t_i + L`: there `b` is `unlockedPre`. -/
theorem unlockedBal_eq_pre (β L : ℝ) {t : ℝ} (ht : t ≤ ti + L) :
    unlockedBal β r m ti L t = unlockedPre β r m ti t := by
  unfold unlockedBal unlockedPre lockedBal mined
  rw [max_eq_left (by linarith)]

/-- §17, boxed: `db/dt = β m(t) + P_L(t) s/S_tot + 1{t ≥ t_i + L}(1 - β) m(t - L)`: direct
unlocked mining, leadership income, and maturation of the income received one lock period
earlier. Holds at `t ≠ t_i + L` where `m` is continuous at `t` and, after maturation
starts, at `t - L`. -/
theorem hasDerivAt_unlockedBal (hr : Continuous r) (hm : LocInt m) (β L : ℝ) {t : ℝ}
    (hne : t ≠ ti + L) (hct : ContinuousAt m t) (hctL : ti + L < t → ContinuousAt m (t - L)) :
    HasDerivAt (unlockedBal β r m ti L)
      (β * m t + r t * stakeInt r m ti t + if ti + L ≤ t then (1 - β) * m (t - L) else 0) t := by
  have hs := hasDerivAt_stakeInt (ti := ti) hr hm hct
  have hK := hm.hasDerivAt_primitive ti hct
  rcases lt_or_gt_of_ne hne with hlt | hgt
  · -- Before maturation: `max t_i (u - L) = t_i` near `t`.
    simp only [not_le.mpr hlt, ↓reduceIte]
    have hev : unlockedBal β r m ti L =ᶠ[nhds t] unlockedPre β r m ti :=
      Filter.eventually_of_mem (Iio_mem_nhds hlt) fun u hu =>
        unlockedBal_eq_pre β L (le_of_lt hu)
    exact (hasDerivAt_unlockedPre hr hm β hct).congr_of_eventuallyEq hev |>.congr_deriv (by ring)
  · -- After maturation starts: `max t_i (u - L) = u - L` near `t`.
    simp only [hgt.le, ↓reduceIte]
    have hKL := ((hm.hasDerivAt_primitive ti (hctL hgt)).comp_sub_const t L)
    have hev : unlockedBal β r m ti L =ᶠ[nhds t]
        fun u => stakeInt r m ti u - (1 - β) * (mined m ti u - mined m ti (u - L)) :=
      Filter.eventually_of_mem (Ioi_mem_nhds hgt) fun u hu => by
        have hu : ti + L < u := hu
        simp only [unlockedBal, lockedBal_eq hm, max_eq_right (by linarith : ti ≤ u - L)]
    refine HasDerivAt.congr_of_eventuallyEq ?_ hev
    have := hs.sub ((hK.sub hKL).const_mul (1 - β))
    unfold mined; convert this using 1; ring

/-! ## §18 Cohort aggregation -/

/-- §18: identical members of a cohort (same mining income `m_e`, same arrival `e`, starting
from zero) all follow the representative `s_e`, so the cohort contributes `n_e s_e(t)` to
total stake and `n_e m_e(t)` to total mining payout. Exact within the deterministic model. -/
theorem cohort_exact {ι : Type*} [Fintype ι] (hr : Continuous r) (hm : LocInt m)
    {D : Set ℝ} (hD : D.Countable) (hmc : ∀ t ∉ D, ContinuousAt m t) {s : ι → ℝ → ℝ}
    (hc : ∀ i, ContinuousOn (s i) (Ici ti))
    (hd : ∀ i, ∀ t ∈ Ioi ti \ D, HasDerivAt (s i) (m t + r t * s i t) t)
    (h0 : ∀ i, s i ti = 0) :
    ∀ t ≥ ti, (∀ i, s i t = stakeInt r m ti t) ∧
      ∑ i, s i t = Fintype.card ι * stakeInt r m ti t ∧
      ∑ _i : ι, m t = Fintype.card ι * m t := by
  intro t ht
  have h := fun i => stakeInt_unique hr hm hD hmc (hc i) (hd i) (h0 i) t ht
  refine ⟨h, ?_, by simp⟩
  simp [h]

/-! ## §19 Measuring success by cohort -/

/-- §19, boxed: waiting time to qualification `τ_i = inf{a ≥ 0 : b_i(t_i + a) ≥ K_B}`, with
`τ_i = ∞` if qualification never occurs. -/
noncomputable def tau (b : ℝ → ℝ) (ti KB : ℝ) : ℝ≥0∞ :=
  ⨅ (a : ℝ≥0) (_ : KB ≤ b (ti + a)), (a : ℝ≥0∞)

/-- Qualifying before the first anniversary: `τ_i < L` iff the balance reaches `K_B` at
some age `a < L`. -/
theorem tau_lt_iff {b : ℝ → ℝ} {KB : ℝ} {L : ℝ≥0} :
    tau b ti KB < L ↔ ∃ a : ℝ≥0, a < L ∧ KB ≤ b (ti + a) := by
  simp only [tau, iInf_lt_iff, ENNReal.coe_lt_coe]
  exact ⟨fun ⟨a, h, ha⟩ => ⟨a, ha, h⟩, fun ⟨a, ha, h⟩ => ⟨a, h, ha⟩⟩

theorem tau_eq_top_iff {b : ℝ → ℝ} {KB : ℝ} :
    tau b ti KB = ⊤ ↔ ∀ a : ℝ≥0, b (ti + a) < KB := by
  simp [tau, iInf_eq_top, not_le]

/-- Once qualified, a newcomer stays qualified while the balance is nondecreasing; by
`unlockedPre_monotoneOn` and `unlockedBal_eq_pre` this holds up to maturation. -/
theorem qualified_mono {b : ℝ → ℝ} {KB : ℝ} (hb : MonotoneOn b (Ici ti)) {a a' : ℝ}
    (ha : 0 ≤ a) (haa' : a ≤ a') (hq : KB ≤ b (ti + a)) : KB ≤ b (ti + a') :=
  hq.trans (hb (by simp [ha]) (by simp; linarith) (by linarith))

/-- §19, boxed: the fraction of cohort `e` qualifying before its first anniversary,
`Q_e = (1/n_e) ∑_{i ∈ 𝒩_e} 1{τ_i < L}`. -/
noncomputable def Qe {ι : Type*} [Fintype ι] (τ : ι → ℝ≥0∞) (L : ℝ≥0) : ℝ :=
  ((Finset.univ.filter fun i => τ i < L).card : ℝ) / Fintype.card ι

theorem Qe_mem_Icc {ι : Type*} [Fintype ι] (τ : ι → ℝ≥0∞) (L : ℝ≥0) : Qe τ L ∈ Icc 0 1 := by
  unfold Qe
  refine ⟨by positivity, div_le_one_of_le₀ ?_ (by positivity)⟩
  exact_mod_cast Finset.card_le_univ _

/-- Identical deterministic members qualify together, so `Q_e ∈ {0, 1}`. -/
theorem Qe_identical {ι : Type*} [Fintype ι] [Nonempty ι] {τ : ι → ℝ≥0∞} {L : ℝ≥0}
    (h : ∀ i j, τ i = τ j) : Qe τ L = 0 ∨ Qe τ L = 1 := by
  obtain ⟨i0⟩ := ‹Nonempty ι›
  unfold Qe
  by_cases hq : τ i0 < L
  · right
    rw [Finset.filter_true_of_mem fun i _ => h i i0 ▸ hq, Finset.card_univ]
    exact div_self (by exact_mod_cast Fintype.card_ne_zero)
  · left
    rw [Finset.filter_false_of_mem fun i _ => h i i0 ▸ hq]
    simp

/-! ## Consistency with the fixed-population solution -/

/-- `r(t) = P_L / S_tot(t)`, extended by its value at `0` to `t < 0` so that it is
continuous on all of `ℝ`. -/
noncomputable def rConst (S0 PL M : ℝ) (t : ℝ) : ℝ := PL / Stot S0 PL M (max t 0)

theorem continuous_rConst {S0 PL M : ℝ} (hS0 : 0 < S0) (hMP : 0 ≤ M + PL) :
    Continuous (rConst S0 PL M) := by
  unfold rConst Stot
  refine continuous_const.div (by fun_prop) fun t => ?_
  have := le_max_right t 0
  have : 0 ≤ (M + PL) * max t 0 := by positivity
  linarith

/-- **Consistency with §§6–7.** For a cohort arriving at `t = 0` with constant mining income
`m`, total payout `M > 0` and leadership pot `P_L ≥ 0`, the integral formula of §16 is the
closed form: `s(t) = m t + (m/M) A(t; M)` and `b(t) = β m t + (m/M) A(t; M)`. -/
theorem stakeInt_eq_stake {S0 PL M : ℝ} (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 ≤ PL)
    (β m : ℝ) {t : ℝ} (ht : 0 ≤ t) :
    stakeInt (rConst S0 PL M) (fun _ => m) 0 t = stake S0 PL M 0 m t ∧
      unlockedPre β (rConst S0 PL M) (fun _ => m) 0 t = unlocked S0 PL M β 0 m t := by
  have hMP : 0 < M + PL := by linarith
  have hr := continuous_rConst hS0 hMP.le
  have hm : LocInt fun _ => m := fun a b => intervalIntegrable_const
  have hpos : ∀ t ≥ 0, 0 < Stot S0 PL M t := fun t ht => Stot_pos hS0 hMP.le ht
  have hs : stakeInt (rConst S0 PL M) (fun _ => m) 0 t = stake S0 PL M 0 m t := by
    refine (linear_unique (m := m) hS0 hMP (continuous_stakeInt hr hm 0).continuousOn
      (fun t ht => (hasDerivAt_stake hS0 hM hPL (hpos t ht) 0 m).continuousAt.continuousWithinAt)
      (fun t ht => ?_) (fun t ht => hasDerivAt_stake hS0 hM hPL (hpos t ht.le) 0 m)
      (by simp [stakeInt_self, stake, g_zero, A_zero]) t ht)
    have := hasDerivAt_stakeInt (ti := 0) hr hm (continuousAt_const (y := m) (x := t))
    simp only [rConst, max_eq_left ht.le] at this
    convert this using 2; ring
  refine ⟨hs, ?_⟩
  unfold unlockedPre mined
  rw [hs]
  simp [stake, unlocked]
  ring

end Onboarding
