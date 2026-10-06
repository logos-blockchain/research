import MiningOnboarding.SmallGrowth
import StochasticRecurrence.Lottery

/-!
# Probability of depleting the reward pool

The report models mining payouts as deterministic expected flows (assumption 9 of §2.3),
so the pool is `R(t) = R₀ - M t` and the budget condition is `M T ≤ R₀`. Here the payouts
are random, as in §11: every mining attempt is a ticket that independently wins with
probability `q_i` (`= d/p` in §11) and, if it wins, draws a reward `σ_i ∈ [0, σ̄]` from the
pool.

`ι` indexes all attempts made before the horizon `T`. Probabilities are finite sums over
outcomes `s : ι → Bool`, as in `StochasticRecurrence` (`SRE.bexp`). Nothing requires the
`q_i` or `σ_i` to be equal, so attempts in different epochs may face different thresholds
and rewards, as long as these are fixed in advance (not adapted to past outcomes).

With `E = ∑ q_i σ_i` the expected spend before `T` (`= M T` in the deterministic model):

* `exists_depleted_iff`: the pool runs out at some time `≤ T` iff the total spend before
  `T` exceeds `R₀` (spend is cumulative), so one tail bound covers the whole horizon;
* `depletion_le_mgf`: Chernoff, for every `λ ≥ 0`,
  `P(spend ≥ R₀) ≤ exp((E/σ̄)(e^{λσ̄} - 1) - λ R₀)`;
* `depletion_le_bennett`: with `λ = log(R₀/E)/σ̄`,
  `P(spend ≥ R₀) ≤ exp(-(E/σ̄) h(R₀/E))`, `h(x) = x log x - x + 1`;
* **`depletion_le_of_buffer`**: if the pool holds a buffer above the expected spend,
  `R₀ ≥ E + √(2 σ̄ E L) + σ̄ L`, then `P(spend ≥ R₀) ≤ e^{-L}`. For `e^{-L} ≤ 10⁻¹²` take
  `L = 28` (`exp_neg_28_lt`);
* `reference_depletion`: an instance. With the report's `R₀ = 50·10⁶`, `M = 10⁶` per
  epoch and a 48-epoch horizon, every reward per claim `σ̄ ≤ 1000` gives
  `P(depletion) < 10⁻¹²`.
-/

open Real Finset SRE

namespace Onboarding

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- Total spend from the pool: the sum of the rewards of the winning attempts. -/
def spend (σ : ι → ℝ) (s : ι → Bool) : ℝ := ∑ i, σ i * ind (s i)

/-- `P(R₀ ≤ spend)`, with attempt `i` winning independently with probability `q i`. -/
noncomputable def depletionProb (q σ : ι → ℝ) (R0 : ℝ) : ℝ :=
  bexp q (fun s => if R0 ≤ spend σ s then 1 else 0)

omit [DecidableEq ι] in
/-- If each attempt has a time `τ_i`, the pool at time `t` is `R₀` minus the spend of the
winning attempts made by `t`. It is negative at some `t ≤ T` iff it is negative at `T`. -/
theorem exists_depleted_iff (σ : ι → ℝ) (hσ : ∀ i, 0 ≤ σ i) (τ : ι → ℝ) (s : ι → Bool)
    (R0 T : ℝ) :
    (∃ t ≤ T, R0 < ∑ i ∈ univ.filter (fun i => τ i ≤ t), σ i * ind (s i)) ↔
      R0 < ∑ i ∈ univ.filter (fun i => τ i ≤ T), σ i * ind (s i) := by
  refine ⟨fun ⟨t, ht, h⟩ => h.trans_le ?_, fun h => ⟨T, le_rfl, h⟩⟩
  refine sum_le_sum_of_subset_of_nonneg ?_ fun i _ _ => ?_
  · intro i; simp only [mem_filter, mem_univ, true_and]; exact fun h => h.trans ht
  · unfold ind; split_ifs <;> simp [hσ i]

theorem bexp_mono {q : ι → ℝ} (hq : ∀ i, 0 ≤ q i ∧ q i ≤ 1) {F G : (ι → Bool) → ℝ}
    (h : ∀ s, F s ≤ G s) : bexp q F ≤ bexp q G := by
  unfold bexp
  refine sum_le_sum fun s _ => mul_le_mul_of_nonneg_left (h s) ?_
  refine prod_nonneg fun i _ => ?_
  unfold bern; split <;> linarith [hq i]

/-- The moment generating function of the spend factorises over attempts. -/
theorem mgf_spend (q σ : ι → ℝ) (x : ℝ) :
    bexp q (fun s => exp (x * spend σ s)) = ∏ i, (1 + q i * (exp (x * σ i) - 1)) := by
  have := bexp_prod q (fun i b => exp (x * (σ i * ind b)))
  rw [show ∏ i, (1 + q i * (exp (x * σ i) - 1)) = ∏ i, (q i * exp (x * σ i) + (1 - q i)) from
    prod_congr rfl fun i _ => by ring]
  convert this using 1
  · congr 1; funext s
    rw [spend, mul_sum, exp_sum]
  · simp [ind]

/-- Convexity of `exp`: for `0 ≤ σ ≤ σ̄` and `x ≥ 0`, `e^{xσ} - 1 ≤ (σ/σ̄)(e^{xσ̄} - 1)`. -/
theorem exp_sub_one_le_chord {x σ σbar : ℝ} (h0 : 0 ≤ σ) (h1 : σ ≤ σbar)
    (hb : 0 < σbar) : exp (x * σ) - 1 ≤ σ / σbar * (exp (x * σbar) - 1) := by
  set θ := σ / σbar
  have hθ0 : 0 ≤ θ := div_nonneg h0 hb.le
  have hθ1 : θ ≤ 1 := (div_le_one hb).mpr h1
  have := convexOn_exp.2 (Set.mem_univ 0) (Set.mem_univ (x * σbar)) (sub_nonneg.mpr hθ1) hθ0
    (by ring)
  simp only [smul_eq_mul, mul_zero, zero_add, exp_zero, mul_one] at this
  have hσ : θ * (x * σbar) = x * σ := by simp only [θ]; field_simp
  rw [hσ] at this
  linarith

/-- **Chernoff bound.** For every `λ ≥ 0`, with `E = ∑ q_i σ_i`,
`P(spend ≥ R₀) ≤ exp((E/σ̄)(e^{λσ̄} - 1) - λ R₀)`. -/
theorem depletion_le_mgf {q σ : ι → ℝ} (hq : ∀ i, 0 ≤ q i ∧ q i ≤ 1) {σbar : ℝ}
    (hσ : ∀ i, 0 ≤ σ i ∧ σ i ≤ σbar) (hb : 0 < σbar) (R0 : ℝ) {x : ℝ} (hx : 0 ≤ x) :
    depletionProb q σ R0 ≤
      exp ((∑ i, q i * σ i) / σbar * (exp (x * σbar) - 1) - x * R0) := by
  -- Markov: `1{R₀ ≤ X} ≤ e^{λ(X - R₀)}`.
  have h1 : depletionProb q σ R0 ≤ bexp q (fun s => exp (-(x * R0)) * exp (x * spend σ s)) := by
    refine bexp_mono hq fun s => ?_
    rw [← exp_add]
    split_ifs with h
    · exact one_le_exp (by nlinarith)
    · exact (exp_pos _).le
  rw [bexp_const_mul, mgf_spend] at h1
  refine h1.trans ?_
  rw [sub_eq_neg_add, exp_add]
  refine mul_le_mul_of_nonneg_left ?_ (exp_pos _).le
  -- `1 + q(e^{λσ} - 1) ≤ exp(q (σ/σ̄)(e^{λσ̄} - 1))`
  rw [sum_div, sum_mul, exp_sum]
  refine prod_le_prod₀ (fun i _ => ?_) fun i _ => ?_
  · have := exp_sub_one_le_chord (x := x) (hσ i).1 (hσ i).2 hb
    have : 0 ≤ exp (x * σ i) - 1 := by
      have := one_le_exp (mul_nonneg hx (hσ i).1); linarith
    nlinarith [hq i]
  · have hc := exp_sub_one_le_chord (x := x) (hσ i).1 (hσ i).2 hb
    calc 1 + q i * (exp (x * σ i) - 1)
        ≤ 1 + q i * (σ i / σbar * (exp (x * σbar) - 1)) := by nlinarith [hq i]
      _ ≤ exp (q i * (σ i / σbar * (exp (x * σbar) - 1))) := by
          linarith [add_one_le_exp (q i * (σ i / σbar * (exp (x * σbar) - 1)))]
      _ = exp (q i * σ i / σbar * (exp (x * σbar) - 1)) := by ring_nf

/-- **Bennett form.** For `0 < E ≤ R₀`, with `μ = E/σ̄`, `k = R₀/σ̄`:
`P(spend ≥ R₀) ≤ exp(-(k log(k/μ) - k + μ))`. -/
theorem depletion_le_bennett {q σ : ι → ℝ} (hq : ∀ i, 0 ≤ q i ∧ q i ≤ 1) {σbar : ℝ}
    (hσ : ∀ i, 0 ≤ σ i ∧ σ i ≤ σbar) (hb : 0 < σbar) {R0 : ℝ}
    (hE : 0 < ∑ i, q i * σ i) (hR : ∑ i, q i * σ i ≤ R0) :
    let μ := (∑ i, q i * σ i) / σbar
    let k := R0 / σbar
    depletionProb q σ R0 ≤ exp (-(k * log (k / μ) - k + μ)) := by
  intro μ k
  have hμ : 0 < μ := div_pos hE hb
  have hk : μ ≤ k := div_le_div_of_nonneg_right hR hb.le
  have hx : 0 ≤ log (k / μ) / σbar :=
    div_nonneg (log_nonneg ((one_le_div hμ).mpr hk)) hb.le
  refine (depletion_le_mgf hq hσ hb R0 hx).trans (le_of_eq ?_)
  congr 1
  rw [div_mul_cancel₀ _ hb.ne', exp_log (div_pos (hμ.trans_le hk) hμ)]
  simp only [μ, k]
  field_simp
  ring

/-- `log(1 + ε) ≥ 2ε/(2 + ε)` for `ε ≥ 0`. -/
theorem log_one_add_ge {ε : ℝ} (hε : 0 ≤ ε) : 2 * ε / (2 + ε) ≤ log (1 + ε) := by
  have := nonneg_of_hasDerivAt (f := fun y => log (1 + y) - 2 * y / (2 + y))
    (f' := fun y => 1 / (1 + y) - 4 / (2 + y) ^ 2)
    (fun y hy => by
      have h1 : HasDerivAt (fun y => log (1 + y)) (1 / (1 + y)) y := by
        have := ((hasDerivAt_id' y).const_add 1).log (by positivity)
        simpa using this
      have h2 : HasDerivAt (fun y => 2 * y / (2 + y)) (4 / (2 + y) ^ 2) y := by
        have := ((hasDerivAt_id' y).const_mul 2).div ((hasDerivAt_id' y).const_add 2)
          (by positivity)
        convert this using 1; field_simp; ring
      exact h1.sub h2)
    (fun y hy => by
      rw [sub_nonneg, div_le_div_iff₀ (by positivity) (by positivity)]
      nlinarith [sq_nonneg y])
    (by simp) ε hε
  linarith

/-- **Buffer condition.** If the pool exceeds the expected spend `E = ∑ q_i σ_i` by
`√(2 σ̄ E L) + σ̄ L`, it is depleted with probability at most `e^{-L}`. -/
theorem depletion_le_of_buffer {q σ : ι → ℝ} (hq : ∀ i, 0 ≤ q i ∧ q i ≤ 1) {σbar : ℝ}
    (hσ : ∀ i, 0 ≤ σ i ∧ σ i ≤ σbar) (hb : 0 < σbar) {R0 L : ℝ} (hL : 0 ≤ L)
    (hR : (∑ i, q i * σ i) + √(2 * σbar * (∑ i, q i * σ i) * L) + σbar * L ≤ R0) :
    depletionProb q σ R0 ≤ exp (-L) := by
  set E := ∑ i, q i * σ i
  have hE0 : 0 ≤ E := sum_nonneg fun i _ => mul_nonneg (hq i).1 (hσ i).1
  rcases hE0.eq_or_lt with hE | hE
  · -- No expected spend: every attempt with a positive reward never wins.
    have hzero : ∀ i, q i * σ i = 0 := fun i =>
      (sum_eq_zero_iff_of_nonneg fun i _ => mul_nonneg (hq i).1 (hσ i).1).mp hE.symm i
        (mem_univ i)
    -- Chernoff with `λ = L/R₀` (or trivially if `R₀ ≤ 0` cannot happen unless `L = 0`).
    rcases (show 0 ≤ R0 by nlinarith [sqrt_nonneg (2 * σbar * E * L)]).eq_or_lt with h0 | h0
    · have : L = 0 := by
        have : σbar * L ≤ 0 := by rw [← hE] at hR; simp at hR; linarith
        exact le_antisymm (nonpos_of_mul_nonpos_right this hb |>.trans_eq rfl) hL
      subst this
      simp only [neg_zero, exp_zero]
      refine (bexp_mono hq (G := fun _ => 1) fun s => by split_ifs <;> norm_num).trans ?_
      rw [bexp_one]
    · have := depletion_le_mgf hq hσ hb R0 (div_nonneg hL h0.le)
      have h' : ∑ i, q i * σ i = 0 := hE.symm
      rw [h', zero_div, zero_mul, zero_sub, div_mul_cancel₀ _ h0.ne'] at this
      exact this
  · -- `E > 0`: Bennett, then `h(1 + ε) ≥ ε²/(2 + ε)`.
    have hR' : E ≤ R0 := by nlinarith [sqrt_nonneg (2 * σbar * E * L)]
    refine (depletion_le_bennett hq hσ hb hE hR').trans (exp_le_exp.mpr ?_)
    set μ := E / σbar
    set k := R0 / σbar
    have hμ : 0 < μ := div_pos hE hb
    -- `t = k - μ ≥ √(2μL) + L`
    have hst : √(2 * σbar * E * L) = σbar * √(2 * μ * L) := by
      rw [show 2 * σbar * E * L = σbar ^ 2 * (2 * μ * L) by simp only [μ]; field_simp]
      rw [sqrt_mul (sq_nonneg _), sqrt_sq hb.le]
    have ht : √(2 * μ * L) + L ≤ k - μ := by
      rw [hst] at hR
      have h1 : μ * σbar = E := div_mul_cancel₀ _ hb.ne'
      have h2 : k * σbar = R0 := div_mul_cancel₀ _ hb.ne'
      nlinarith
    set t := k - μ
    set s := √(2 * μ * L)
    have hs2 : s ^ 2 = 2 * μ * L := sq_sqrt (by positivity)
    have hs0 : 0 ≤ s := sqrt_nonneg _
    have ht0 : 0 ≤ t := by linarith
    -- `t² ≥ L(2μ + t)`
    have hquad : L * (2 * μ + t) ≤ t ^ 2 := by nlinarith
    -- `k log(k/μ) - k + μ = μ h(1 + ε) ≥ μ ε²/(2 + ε) = t²/(2μ + t)`, `ε = t/μ`.
    have hε := log_one_add_ge (div_nonneg ht0 hμ.le)
    have hk : k = μ * (1 + t / μ) := by
      rw [mul_add, mul_one, mul_div_cancel₀ _ hμ.ne']; simp only [t]; ring
    have hkμ : k / μ = 1 + t / μ := by rw [hk]; field_simp
    rw [hkμ]
    have hlow : t ^ 2 / (2 * μ + t) ≤ k * log (1 + t / μ) - k + μ := by
      have hkpos : 0 ≤ k := by rw [hk]; positivity
      have := mul_le_mul_of_nonneg_left hε hkpos
      rw [hk] at this ⊢
      have e1 : μ * (1 + t / μ) * (2 * (t / μ) / (2 + t / μ)) = 2 * (μ + t) * t / (2 * μ + t) := by
        field_simp
      have e2 : 2 * (μ + t) * t / (2 * μ + t) - μ * (1 + t / μ) + μ = t ^ 2 / (2 * μ + t) := by
        field_simp; ring
      rw [e1] at this
      linarith
    have : L ≤ t ^ 2 / (2 * μ + t) := by rw [le_div_iff₀ (by positivity)]; linarith
    linarith

/-- `e^{-28} < 10⁻¹²`. -/
theorem exp_neg_28_lt : exp (-28) < 1e-12 := by
  rw [exp_neg, inv_lt_comm₀ (exp_pos _) (by norm_num)]
  have h := exp_one_gt_d9
  have : (2.7182818283 : ℝ) ^ 28 < exp 1 ^ 28 := pow_lt_pow_left₀ h (by norm_num) (by norm_num)
  rw [← exp_nat_mul] at this
  norm_num at this ⊢
  linarith

/-- **An instance.** Reference pool `R₀ = 50·10⁶`, expected spend `E ≤ 48·10⁶` (for
example `M = 10⁶` per epoch for 48 epochs, about 11.8 months), and rewards per claim at most
`σ̄ = 1000`: the pool is depleted with probability below `10⁻¹²`. -/
theorem reference_depletion {q σ : ι → ℝ} (hq : ∀ i, 0 ≤ q i ∧ q i ≤ 1)
    (hσ : ∀ i, 0 ≤ σ i ∧ σ i ≤ 1000) (hE : ∑ i, q i * σ i ≤ 48e6) :
    depletionProb q σ 50e6 < 1e-12 := by
  refine lt_of_le_of_lt (depletion_le_of_buffer hq hσ (by norm_num) (by norm_num : (0:ℝ) ≤ 28)
    ?_) exp_neg_28_lt
  have hE0 : 0 ≤ ∑ i, q i * σ i := sum_nonneg fun i _ => mul_nonneg (hq i).1 (hσ i).1
  -- `√(2·1000·48·10⁶·28) < 1.7·10⁶`
  have : √(2 * 1000 * (∑ i, q i * σ i) * 28) ≤ 1.7e6 := by
    rw [sqrt_le_left (by norm_num)]
    nlinarith
  linarith

end Onboarding
