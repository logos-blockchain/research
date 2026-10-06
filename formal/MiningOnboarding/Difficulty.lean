import MiningOnboarding.Model

/-!
# §11 Mining income and mining difficulty

Miner `i` makes `h_i` candidate attempts per epoch. Tickets are approximately uniform on a
space of size `p`, a ticket wins when it falls below the threshold `d`, and each winning
ticket is a paid claim with retained reward `w = σ - φ` (gross reward minus claim fee).

* `income`: `m_i = h_i (d/p) w`;
* `total_income`: `M = H (d/p) w` with `H = ∑ h_i`;
* `threshold`: the threshold `d = p m⋆ / (h_min w)` targeting minimum income `m⋆`;
* `income_threshold`: with it, `m_i = m⋆ h_i / h_min`;
* `total_income_threshold`: and `M = m⋆ H / h_min`;
* `le_income_threshold`: every miner with `h_i ≥ h_min` earns at least `m⋆`;
* `newcomer_income`: with `h_min = min_{i ∈ 𝒩} h_i`, every newcomer earns at least `m⋆`,
  and the slowest earns exactly `m⋆`;
* `threshold_le_iff`: the threshold is feasible (`d ≤ p`, a success probability at most
  one) iff `m⋆ ≤ h_min w`;
* `threshold_mul_reward`: scaling the reward by `c` divides the threshold by `c`: holding
  incomes fixed when the reward changes requires adjusting the threshold.
-/

namespace Onboarding

/-- Retained mining income per epoch, `m = h (d/p) w`. -/
noncomputable def income (h d p w : ℝ) : ℝ := h * (d / p) * w

/-- The threshold targeting a minimum expected income `m⋆`: `d = p m⋆ / (h_min w)`. -/
noncomputable def threshold (p mstar hmin w : ℝ) : ℝ := p * mstar / (hmin * w)

variable {p mstar hmin w : ℝ}

/-- Total retained income `M = H (d/p) w`, `H = ∑ h_i`. -/
theorem total_income {ι : Type*} (s : Finset ι) (h : ι → ℝ) (d : ℝ) :
    ∑ i ∈ s, income (h i) d p w = (∑ i ∈ s, h i) * (d / p) * w := by
  simp only [income, Finset.sum_mul]

/-- With the targeted threshold, `m_i = m⋆ h_i / h_min`. -/
theorem income_threshold (hp : p ≠ 0) (hh : hmin ≠ 0) (hw : w ≠ 0) (h : ℝ) :
    income h (threshold p mstar hmin w) p w = mstar * h / hmin := by
  unfold income threshold; field_simp

/-- With the targeted threshold, `M = m⋆ H / h_min`. -/
theorem total_income_threshold {ι : Type*} (s : Finset ι) (h : ι → ℝ) (hp : p ≠ 0)
    (hh : hmin ≠ 0) (hw : w ≠ 0) :
    ∑ i ∈ s, income (h i) (threshold p mstar hmin w) p w = mstar * (∑ i ∈ s, h i) / hmin := by
  simp only [income_threshold hp hh hw, ← Finset.sum_div, ← Finset.mul_sum]

/-- A miner at least as fast as `h_min` earns at least `m⋆`. -/
theorem le_income_threshold (hp : p ≠ 0) (hh : 0 < hmin) (hw : w ≠ 0) (hm : 0 ≤ mstar)
    {h : ℝ} (hle : hmin ≤ h) : mstar ≤ income h (threshold p mstar hmin w) p w := by
  rw [income_threshold hp hh.ne' hw, le_div_iff₀ hh]
  exact mul_le_mul_of_nonneg_left hle hm

/-- With `h_min = min_{i ∈ 𝒩} h_i > 0`, every newcomer earns at least `m⋆`, and the
slowest newcomer earns exactly `m⋆`. -/
theorem newcomer_income {ι : Type*} {N : Finset ι} (hN : N.Nonempty) (h : ι → ℝ)
    (hpos : 0 < N.inf' hN h) (hp : p ≠ 0) (hw : w ≠ 0) (hm : 0 ≤ mstar) :
    (∀ i ∈ N, mstar ≤ income (h i) (threshold p mstar (N.inf' hN h) w) p w) ∧
      ∃ i ∈ N, income (h i) (threshold p mstar (N.inf' hN h) w) p w = mstar := by
  refine ⟨fun i hi => le_income_threshold hp hpos hw hm (Finset.inf'_le h hi), ?_⟩
  obtain ⟨i, hi, he⟩ := Finset.exists_mem_eq_inf' hN h
  refine ⟨i, hi, ?_⟩
  rw [income_threshold hp hpos.ne' hw, ← he, mul_div_assoc, div_self hpos.ne', mul_one]

/-- The targeted threshold is feasible, `d ≤ p`, iff `m⋆ ≤ h_min w`. -/
theorem threshold_le_iff (hp : 0 < p) (hh : 0 < hmin) (hw : 0 < w) :
    threshold p mstar hmin w ≤ p ↔ mstar ≤ hmin * w := by
  unfold threshold
  rw [div_le_iff₀ (by positivity), mul_le_mul_iff_right₀ hp]

/-- Scaling the retained reward by `c` divides the targeted threshold by `c`. -/
theorem threshold_mul_reward (c : ℝ) :
    threshold p mstar hmin (c * w) = threshold p mstar hmin w / c := by
  unfold threshold
  rw [div_div]; ring_nf

end Onboarding
