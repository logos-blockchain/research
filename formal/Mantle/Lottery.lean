import Mathlib

/-!
# The leadership lottery

Proof of Leadership, *Lottery Approximation*. A note of relative stake `α` should win a slot
with the probability of Ouroboros Crypsinous, `φ_f(α) = 1 - (1 - f)^α`, where `f = 1/30` is the
probability that some leader wins. The circuit cannot compute it, and uses the order-2 Taylor
expansion `ψ(α) = α (c - c² α / 2)`, `c = -ln(1 - f)`, the order-1 one being `c α`.

* `phi_eq`: `φ_f(α) = 1 - e^{-c α}`; `phi_add`: splitting a stake into two notes leaves the
  probability that one of them wins unchanged, which is why `φ` is used;
* **`approx2_le_phi`**, **`phi_sub_approx2_le`**: `ψ(α) ≤ φ(α) ≤ ψ(α) + c³α³/6` for `α ≥ 0`:
  the circuit's threshold never favours a note, and its error is third order;
  `phi_le_approx1`: the order-1 expansion always overestimates;
* **`split_advantage`**: under `ψ`, splitting a note into two of relative stakes `a, b > 0`
  (with `c b ≤ 1`, far beyond any real note) raises the probability that one of them wins, by
  `c³ab(a+b)/2 - c⁴a²b²/4 > 0`: a third-order incentive to split stake, which `φ` does not have;
* the specification's error table: **`error_table_f30_all`** proves every row of the table for
  `f = 1/30`, both errors to the digits shown; `error_table_f30` the last row with plain bounds
  (`error_table_f20`: the `2.59%` and `-0.0444%` of `f = 1/20`, which the table gave before
  Mantle 2.0.0 v8);
* the threshold in `𝔽_p` (`threshold`, with the constants `t₀ = t0_constant / S` and
  `t₁ = p - t1_constant / S²`): `threshold_no_wrap` gives the integer value
  `v t₀ - v² ⌊t1_constant/S²⌋` below the zero crossing, `threshold_wrap` the near-`p` value
  past it (the corner case of the specification); **`constants_exact`**: the hexadecimal
  constants are exactly `⌊-p ln(1-f)⌋` and `⌊p ln²(1-f)/2⌋` for `f = 1/30` (a 53-term log
  series, checked by the kernel); **`win_prob_le`**: so a note never wins with probability
  above `φ_f(v/S) + 2v²/p`; `parabola_peak_zero`: for `f = 1/30` the peak
  of `ψ` is at `α = 1/c ≈ 29.5` and its zero at `α = 2/c ≈ 59.0`.
-/

namespace Mantle.Lottery

open Real

noncomputable section

/-- `φ_f(α) = 1 - (1 - f)^α`. -/
def phi (f α : ℝ) : ℝ := 1 - (1 - f) ^ α

/-- `c = -ln(1 - f)`. -/
def rate (f : ℝ) : ℝ := -log (1 - f)

/-- The order-1 expansion `c α`. -/
def approx1 (f α : ℝ) : ℝ := rate f * α

/-- The order-2 expansion `α (c - c² α / 2)`, the circuit's threshold over `p`. -/
def approx2 (f α : ℝ) : ℝ := α * (rate f - rate f ^ 2 / 2 * α)

variable {f : ℝ}

theorem rate_pos (h0 : 0 < f) (h1 : f < 1) : 0 < rate f := by
  unfold rate
  have : log (1 - f) < 0 := log_neg (by linarith) (by linarith)
  linarith

theorem phi_eq (h1 : f < 1) (α : ℝ) : phi f α = 1 - exp (-(rate f * α)) := by
  rw [phi, rpow_def_of_pos (by linarith), rate]
  ring_nf

/-- **Splitting a stake leaves `φ` unchanged**: the probability that one of two notes of
relative stakes `a` and `b` wins is `φ(a + b)`. -/
theorem phi_add (h1 : f < 1) (a b : ℝ) : 1 - (1 - phi f a) * (1 - phi f b) = phi f (a + b) := by
  simp only [phi_eq h1, sub_sub_cancel, ← exp_add]
  ring_nf

/-! ## Bounds on `e^{-y}` -/

theorem exp_neg_le_quadratic {y : ℝ} (hy : 0 ≤ y) : exp (-y) ≤ 1 - y + y ^ 2 / 2 := by
  let g : ℝ → ℝ := fun y => 1 - y + y ^ 2 / 2 - exp (-y)
  have hd : ∀ x, HasDerivAt g (-1 + x + exp (-x)) x := by
    intro x
    have h1 : HasDerivAt (fun x : ℝ => 1 - x) (-1) x := by
      simpa using (hasDerivAt_id x).const_sub 1
    have h2 : HasDerivAt (fun x : ℝ => x ^ 2 / 2) x x := by
      simpa using (hasDerivAt_pow 2 x).div_const 2
    have h3 : HasDerivAt (fun x : ℝ => exp (-x)) (-exp (-x)) x := by
      simpa using (hasDerivAt_neg x).exp
    convert (h1.add h2).sub h3 using 1
    ring
  have hmono : MonotoneOn g (Set.Ici 0) := by
    apply monotoneOn_of_hasDerivWithinAt_nonneg (convex_Ici 0)
      (fun x _ => (hd x).continuousAt.continuousWithinAt)
      (fun x _ => (hd x).hasDerivWithinAt)
    intro x _
    have := one_sub_le_exp_neg x
    linarith
  have := hmono ((Set.mem_Ici.2 le_rfl)) hy hy
  simp only [g, neg_zero, exp_zero] at this
  linarith

theorem cubic_le_exp_neg {y : ℝ} (hy : 0 ≤ y) :
    1 - y + y ^ 2 / 2 - y ^ 3 / 6 ≤ exp (-y) := by
  let g : ℝ → ℝ := fun y => exp (-y) - (1 - y + y ^ 2 / 2 - y ^ 3 / 6)
  have hd : ∀ x, HasDerivAt g (1 - x + x ^ 2 / 2 - exp (-x)) x := by
    intro x
    have h1 : HasDerivAt (fun x : ℝ => 1 - x) (-1) x := by
      simpa using (hasDerivAt_id x).const_sub 1
    have h2 : HasDerivAt (fun x : ℝ => x ^ 2 / 2) x x := by
      simpa using (hasDerivAt_pow 2 x).div_const 2
    have h3 : HasDerivAt (fun x : ℝ => exp (-x)) (-exp (-x)) x := by
      simpa using (hasDerivAt_neg x).exp
    have h4 : HasDerivAt (fun x : ℝ => x ^ 3 / 6) (x ^ 2 / 2) x := by
      convert (hasDerivAt_pow 3 x).div_const 6 using 1; push_cast; ring
    convert h3.sub ((h1.add h2).sub h4) using 1
    ring
  have hmono : MonotoneOn g (Set.Ici 0) := by
    apply monotoneOn_of_hasDerivWithinAt_nonneg (convex_Ici 0)
      (fun x _ => (hd x).continuousAt.continuousWithinAt)
      (fun x _ => (hd x).hasDerivWithinAt)
    intro x hx
    have := exp_neg_le_quadratic (interior_subset hx : x ∈ Set.Ici 0)
    linarith
  have := hmono ((Set.mem_Ici.2 le_rfl)) hy hy
  simp only [g, neg_zero, exp_zero] at this
  linarith

/-! ## The approximations -/

/-- **The order-2 threshold never exceeds the probability of Crypsinous.** -/
theorem approx2_le_phi (h0 : 0 < f) (h1 : f < 1) {α : ℝ} (hα : 0 ≤ α) :
    approx2 f α ≤ phi f α := by
  have hy : 0 ≤ rate f * α := mul_nonneg (rate_pos h0 h1).le hα
  rw [phi_eq h1, approx2]
  have := exp_neg_le_quadratic hy
  nlinarith

/-- **Its error is third order.** -/
theorem phi_sub_approx2_le (h0 : 0 < f) (h1 : f < 1) {α : ℝ} (hα : 0 ≤ α) :
    phi f α - approx2 f α ≤ rate f ^ 3 * α ^ 3 / 6 := by
  have hy : 0 ≤ rate f * α := mul_nonneg (rate_pos h0 h1).le hα
  rw [phi_eq h1, approx2]
  have := cubic_le_exp_neg hy
  nlinarith

/-- The order-1 expansion always overestimates. -/
theorem phi_le_approx1 (h1 : f < 1) (α : ℝ) : phi f α ≤ approx1 f α := by
  rw [phi_eq h1, approx1]
  have := one_sub_le_exp_neg (rate f * α)
  linarith

/-- **Splitting a note raises its chance under the order-2 threshold**: two notes of relative
stakes `a, b > 0` win (at least one of them) with probability higher than one note of stake
`a + b`, by `c³ab(a+b)/2 - c⁴a²b²/4`, positive while `c b ≤ 1`. -/
theorem split_advantage (h0 : 0 < f) (h1 : f < 1) {a b : ℝ} (ha : 0 < a) (hb : 0 < b)
    (hcb : rate f * b ≤ 1) :
    (1 - (1 - approx2 f a) * (1 - approx2 f b)) - approx2 f (a + b) =
        rate f ^ 3 * a * b * (a + b) / 2 - rate f ^ 4 * a ^ 2 * b ^ 2 / 4 ∧
      0 < (1 - (1 - approx2 f a) * (1 - approx2 f b)) - approx2 f (a + b) := by
  have hc := rate_pos h0 h1
  have e : (1 - (1 - approx2 f a) * (1 - approx2 f b)) - approx2 f (a + b) =
      rate f ^ 3 * a * b * (a + b) / 2 - rate f ^ 4 * a ^ 2 * b ^ 2 / 4 := by
    simp only [approx2]; ring
  refine ⟨e, ?_⟩
  rw [e]
  have hab : 0 < rate f ^ 3 * a * b := by positivity
  have key : rate f * a * b ≤ (a + b) := by nlinarith
  nlinarith [mul_pos hab (add_pos ha hb)]

/-! ## The specification's error table -/

/-- `c` for a given `f`, enclosed by the alternating log series to order 6. -/
theorem rate_bounds {x : ℝ} (hx0 : 0 ≤ x) (hx1 : x < 1) :
    |rate x - ∑ i ∈ Finset.range 6, x ^ (i + 1) / (i + 1)| ≤ x ^ 7 / (1 - x) := by
  have := abs_log_sub_add_sum_range_le (x := x) (by rw [abs_of_nonneg hx0]; exact hx1) 6
  rw [abs_of_nonneg hx0] at this
  rw [rate, show -log (1 - x) - ∑ i ∈ Finset.range 6, x ^ (i + 1) / (i + 1) =
    -((∑ i ∈ Finset.range 6, x ^ (i + 1) / (i + 1)) + log (1 - x)) by ring, abs_neg]
  exact this

/-- At `α = 1`, `φ_f(1) = f`: the relative errors are `c/f - 1` and `(c - c²/2)/f - 1`. -/
theorem phi_one : phi f 1 = f := by simp [phi]

/-- **For `f = 1/30`**, at a stake equal to the inferred total stake, the order-1 error is
`1.70%` and the order-2 error `-0.0193%`, to the digits of the table's last row. -/
theorem error_table_f30 :
    0.01695 < approx1 (1 / 30) 1 / phi (1 / 30) 1 - 1 ∧
      approx1 (1 / 30) 1 / phi (1 / 30) 1 - 1 < 0.01705 ∧
      -0.0001935 < approx2 (1 / 30) 1 / phi (1 / 30) 1 - 1 ∧
      approx2 (1 / 30) 1 / phi (1 / 30) 1 - 1 < -0.0001925 := by
  have hb := rate_bounds (x := 1 / 30) (by norm_num) (by norm_num)
  rw [phi_one]
  simp only [approx1, approx2, mul_one, one_mul]
  simp only [Finset.sum_range_succ, Finset.sum_range_zero] at hb
  rw [abs_le] at hb
  norm_num at hb
  obtain ⟨hl, hu⟩ := hb
  refine ⟨by nlinarith, by nlinarith, by nlinarith, by nlinarith⟩

/-- **For `f = 1/20`** the same errors are the table's `2.59%` and `-0.0444%`. -/
theorem error_table_f20 :
    0.0258 < approx1 (1 / 20) 1 / phi (1 / 20) 1 - 1 ∧
      approx1 (1 / 20) 1 / phi (1 / 20) 1 - 1 < 0.0259 ∧
      -0.000445 < approx2 (1 / 20) 1 / phi (1 / 20) 1 - 1 ∧
      approx2 (1 / 20) 1 / phi (1 / 20) 1 - 1 < -0.000443 := by
  have hb := rate_bounds (x := 1 / 20) (by norm_num) (by norm_num)
  rw [phi_one]
  simp only [approx1, approx2, mul_one, one_mul]
  simp only [Finset.sum_range_succ, Finset.sum_range_zero] at hb
  rw [abs_le] at hb
  norm_num at hb
  obtain ⟨hl, hu⟩ := hb
  refine ⟨by nlinarith, by nlinarith, by nlinarith, by nlinarith⟩

/-- For `f = 1/30` the parabola `ψ` peaks at `α = 1/c ∈ (29.4, 29.6)` and returns to `0` at
`α = 2/c ∈ (58.9, 59.1)`, the specification's 29 and 59. -/
theorem parabola_peak_zero :
    (29.4 < 1 / rate (1 / 30) ∧ 1 / rate (1 / 30) < 29.6) ∧
      (58.9 < 2 / rate (1 / 30) ∧ 2 / rate (1 / 30) < 59.1) ∧
      approx2 (1 / 30) (2 / rate (1 / 30)) = 0 := by
  have hb := rate_bounds (x := 1 / 30) (by norm_num) (by norm_num)
  have hc : 0 < rate (1 / 30) := rate_pos (by norm_num) (by norm_num)
  simp only [Finset.sum_range_succ, Finset.sum_range_zero] at hb
  rw [abs_le] at hb
  norm_num at hb
  obtain ⟨hl, hu⟩ := hb
  refine ⟨⟨?_, ?_⟩, ⟨?_, ?_⟩, ?_⟩
  · rw [lt_div_iff₀ hc]; nlinarith
  · rw [div_lt_iff₀ hc]; nlinarith
  · rw [lt_div_iff₀ hc]; nlinarith
  · rw [div_lt_iff₀ hc]; nlinarith
  · simp only [approx2]; field_simp; ring

/-! ## The whole error table

`1 - e^{-x}` is enclosed by its order-6 Taylor polynomial (`Real.exp_bound`), evaluated term by
term on an enclosure of `x = c α` (`expLo`, `expHi`), with `c` known to ten decimals
(`rate30_mem`). Each row is then a set of rational inequalities, checked by `norm_num`. -/

/-- A lower bound of `1 - e^{-x}` for `x ∈ [a, b] ⊆ [0, 1]`. -/
def expLo (a b : ℝ) : ℝ := a - b ^ 2 / 2 + a ^ 3 / 6 - b ^ 4 / 24 + a ^ 5 / 120 - 7 * b ^ 6 / 4320
/-- An upper bound of `1 - e^{-x}` for `x ∈ [a, b] ⊆ [0, 1]`. -/
def expHi (a b : ℝ) : ℝ := b - a ^ 2 / 2 + b ^ 3 / 6 - a ^ 4 / 24 + b ^ 5 / 120 + 7 * b ^ 6 / 4320

theorem one_sub_exp_neg_mem {a b x : ℝ} (ha : 0 ≤ a) (hax : a ≤ x) (hxb : x ≤ b) (hb : b ≤ 1) :
    expLo a b ≤ 1 - exp (-x) ∧ 1 - exp (-x) ≤ expHi a b := by
  have hx0 : 0 ≤ x := ha.trans hax
  have hx1 : |-x| ≤ 1 := by rw [abs_neg, abs_of_nonneg hx0]; linarith
  have h := Real.exp_bound hx1 (n := 6) (by norm_num)
  rw [abs_neg, abs_of_nonneg hx0, abs_le] at h
  simp only [Finset.sum_range_succ, Finset.sum_range_zero, Nat.factorial] at h
  norm_num at h
  obtain ⟨hl, hu⟩ := h
  have n3 : (-x) ^ 3 = -x ^ 3 := by ring
  have n5 : (-x) ^ 5 = -x ^ 5 := by ring
  rw [n3, n5] at hl hu
  have p2 := pow_le_pow_left₀ ha hax 2
  have p3 := pow_le_pow_left₀ ha hax 3
  have p4 := pow_le_pow_left₀ ha hax 4
  have p5 := pow_le_pow_left₀ ha hax 5
  have q2 := pow_le_pow_left₀ hx0 hxb 2
  have q3 := pow_le_pow_left₀ hx0 hxb 3
  have q4 := pow_le_pow_left₀ hx0 hxb 4
  have q5 := pow_le_pow_left₀ hx0 hxb 5
  have q6 := pow_le_pow_left₀ hx0 hxb 6
  unfold expLo expHi
  constructor
  · linarith
  · linarith

/-- `c = ln(30/29)` to ten decimals. -/
theorem rate30_mem : 0.0339015516 ≤ rate (1 / 30) ∧ rate (1 / 30) ≤ 0.0339015518 := by
  have hb := rate_bounds (x := 1 / 30) (by norm_num) (by norm_num)
  simp only [Finset.sum_range_succ, Finset.sum_range_zero] at hb
  rw [abs_le] at hb
  norm_num at hb
  obtain ⟨hl, hu⟩ := hb
  constructor
  · linarith
  · linarith

/-- The error of the two expansions at stake `α` for `f = 1/30`, from an enclosure of `c α`. -/
theorem error_row {α L1 U1 L2 U2 : ℝ} (hα : 0 < α)
    (hL1 : 0 ≤ L1 + 1) (hL2 : 0 ≤ L2 + 1) (hlo : 0 < expLo (0.0339015516 * α) (0.0339015518 * α))
    (hb : 0.0339015518 * α ≤ 1)
    (h1 : (L1 + 1) * expHi (0.0339015516 * α) (0.0339015518 * α) < 0.0339015516 * α)
    (h2 : 0.0339015518 * α < (U1 + 1) * expLo (0.0339015516 * α) (0.0339015518 * α))
    (h3 : (L2 + 1) * expHi (0.0339015516 * α) (0.0339015518 * α) <
      0.0339015516 * α - (0.0339015518 * α) ^ 2 / 2)
    (h4 : 0.0339015518 * α - (0.0339015516 * α) ^ 2 / 2 <
      (U2 + 1) * expLo (0.0339015516 * α) (0.0339015518 * α)) :
    (L1 < approx1 (1 / 30) α / phi (1 / 30) α - 1 ∧ approx1 (1 / 30) α / phi (1 / 30) α - 1 < U1) ∧
      (L2 < approx2 (1 / 30) α / phi (1 / 30) α - 1 ∧
        approx2 (1 / 30) α / phi (1 / 30) α - 1 < U2) := by
  obtain ⟨hcl, hcu⟩ := rate30_mem
  have hxl : 0.0339015516 * α ≤ rate (1 / 30) * α := mul_le_mul_of_nonneg_right hcl hα.le
  have hxu : rate (1 / 30) * α ≤ 0.0339015518 * α := mul_le_mul_of_nonneg_right hcu hα.le
  obtain ⟨φl, φu⟩ := one_sub_exp_neg_mem (by positivity) hxl hxu hb
  have a2 : approx2 (1 / 30) α = rate (1 / 30) * α - (rate (1 / 30) * α) ^ 2 / 2 := by
    unfold approx2
    ring
  rw [phi_eq (by norm_num), a2, show approx1 (1 / 30) α = rate (1 / 30) * α from rfl]
  generalize rate (1 / 30) * α = x at *
  generalize 1 - exp (-x) = φ at *
  generalize expLo (0.0339015516 * α) (0.0339015518 * α) = lo at *
  generalize expHi (0.0339015516 * α) (0.0339015518 * α) = hi at *
  have hφ : 0 < φ := hlo.trans_le φl
  have s1 := pow_le_pow_left₀ (by positivity) hxl 2
  have s2 := pow_le_pow_left₀ (le_trans (by positivity) hxl) hxu 2
  have hU1 : 0 < U1 + 1 := by nlinarith
  have hU2 : 0 < U2 + 1 := by nlinarith
  have e1 := mul_le_mul_of_nonneg_left φu hL1
  have e2 := mul_le_mul_of_nonneg_left φl hU1.le
  have e3 := mul_le_mul_of_nonneg_left φu hL2
  have e4 := mul_le_mul_of_nonneg_left φl hU2.le
  refine ⟨⟨?_, ?_⟩, ?_, ?_⟩
  · rw [lt_sub_iff_add_lt, lt_div_iff₀ hφ]
    linarith
  · rw [sub_lt_iff_lt_add, div_lt_iff₀ hφ]
    linarith
  · rw [lt_sub_iff_add_lt, lt_div_iff₀ hφ]
    linarith
  · rw [sub_lt_iff_lt_add, div_lt_iff₀ hφ]
    linarith

/-- A row of the error table of *Lottery Approximation*: at a relative stake `α`, the order-1 and
order-2 errors, in percent, are `e₁` and `e₂` to within `h₁` and `h₂`, half a unit of the last
digit shown. -/
def TableRow (α e₁ h₁ e₂ h₂ : ℝ) : Prop :=
  |100 * (approx1 (1 / 30) α / phi (1 / 30) α - 1) - e₁| < h₁ ∧
    |100 * (approx2 (1 / 30) α / phi (1 / 30) α - 1) - e₂| < h₂

theorem tableRow_of {α e₁ h₁ e₂ h₂ : ℝ} (hα : 0 < α)
    (hL1 : 0 ≤ (e₁ - h₁) / 100 + 1) (hL2 : 0 ≤ (e₂ - h₂) / 100 + 1)
    (hlo : 0 < expLo (0.0339015516 * α) (0.0339015518 * α)) (hb : 0.0339015518 * α ≤ 1)
    (h1 : ((e₁ - h₁) / 100 + 1) * expHi (0.0339015516 * α) (0.0339015518 * α) <
      0.0339015516 * α)
    (h2 : 0.0339015518 * α <
      ((e₁ + h₁) / 100 + 1) * expLo (0.0339015516 * α) (0.0339015518 * α))
    (h3 : ((e₂ - h₂) / 100 + 1) * expHi (0.0339015516 * α) (0.0339015518 * α) <
      0.0339015516 * α - (0.0339015518 * α) ^ 2 / 2)
    (h4 : 0.0339015518 * α - (0.0339015516 * α) ^ 2 / 2 <
      ((e₂ + h₂) / 100 + 1) * expLo (0.0339015516 * α) (0.0339015518 * α)) :
    TableRow α e₁ h₁ e₂ h₂ := by
  obtain ⟨⟨a, b⟩, c, d⟩ := error_row hα hL1 hL2 hlo hb h1 h2 h3 h4
  unfold TableRow
  rw [abs_sub_lt_iff, abs_sub_lt_iff]
  refine ⟨⟨?_, ?_⟩, ?_, ?_⟩ <;> linarith

/-- **The error table of *Lottery Approximation*, every row**, for `f = 1/30`. -/
theorem error_table_f30_all :
      TableRow 0.05 0.08 0.005 (-0.00005) 0.000005 ∧
      TableRow 0.10 0.17 0.005 (-0.0002) 0.00005 ∧
      TableRow 0.15 0.25 0.005 (-0.0004) 0.00005 ∧
      TableRow 0.20 0.34 0.005 (-0.0008) 0.00005 ∧
      TableRow 0.25 0.42 0.005 (-0.0012) 0.00005 ∧
      TableRow 0.30 0.51 0.005 (-0.0017) 0.00005 ∧
      TableRow 0.35 0.59 0.005 (-0.0024) 0.00005 ∧
      TableRow 0.40 0.68 0.005 (-0.0031) 0.00005 ∧
      TableRow 0.45 0.76 0.005 (-0.0039) 0.00005 ∧
      TableRow 0.50 0.85 0.005 (-0.0048) 0.00005 ∧
      TableRow 0.55 0.94 0.005 (-0.0058) 0.00005 ∧
      TableRow 0.60 1.02 0.005 (-0.0069) 0.00005 ∧
      TableRow 0.65 1.11 0.005 (-0.0081) 0.00005 ∧
      TableRow 0.70 1.19 0.005 (-0.0094) 0.00005 ∧
      TableRow 0.75 1.28 0.005 (-0.0108) 0.00005 ∧
      TableRow 0.80 1.36 0.005 (-0.0123) 0.00005 ∧
      TableRow 0.85 1.45 0.005 (-0.0139) 0.00005 ∧
      TableRow 0.90 1.53 0.005 (-0.0156) 0.00005 ∧
      TableRow 0.95 1.62 0.005 (-0.0174) 0.00005 ∧
      TableRow 1.00 1.70 0.005 (-0.0193) 0.00005 := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
    apply tableRow_of <;> norm_num [expLo, expHi]

end

/-! ## The threshold in `𝔽_p` -/

/-- The order `p` of the scalar field of BN254. -/
def P : ℕ := 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001
/-- `t0_constant`. -/
def T0C : ℕ := 0x1a3fb997fd5838f2a1585ee090a95c88129ab25cc4d2e2d28f1a95f81d85465
/-- `t1_constant`. -/
def T1C : ℕ := 0x71e790b4199113a9a00298d823c5716ddac764a110a45fe3b770bbb3e8a57

/-- `lottery_constants(inferred_total_stake)`. -/
def constants (S : ℕ) : ℕ × ℕ := (T0C / S, P - T1C / S ^ 2)

/-- `threshold = value * (t0 + t1 * value)`, computed in `𝔽_p`. -/
def threshold (S v : ℕ) : ℕ := (v * ((constants S).1 + (constants S).2 * v)) % P

/-- The magnitude of the order-2 term, `⌊t1_constant / S²⌋`. -/
def quad (S : ℕ) : ℕ := T1C / S ^ 2

theorem quad_lt (S : ℕ) : quad S < P :=
  lt_of_le_of_lt (Nat.div_le_self _ _) (by decide)

theorem threshold_eq (S v : ℕ) :
    threshold S v = (v * (T0C / S) + v ^ 2 * P - v ^ 2 * quad S) % P := by
  have hq := quad_lt S
  unfold threshold constants
  congr 1
  simp only [quad] at hq ⊢
  have : v ^ 2 * (T1C / S ^ 2) ≤ v ^ 2 * P := Nat.mul_le_mul_left _ hq.le
  rw [Nat.mul_add, Nat.mul_comm (P - _) v, ← Nat.mul_assoc, Nat.mul_sub, ← sq, Nat.add_sub_assoc]
  · exact Nat.mul_le_mul_left _ hq.le

/-- **Below the zero crossing the threshold is the integer `v t₀ - v² ⌊t1_constant/S²⌋`.** -/
theorem threshold_no_wrap {S v : ℕ} (h : v ^ 2 * quad S ≤ v * (T0C / S))
    (hp : v * (T0C / S) < P) : threshold S v = v * (T0C / S) - v ^ 2 * quad S := by
  rw [threshold_eq]
  rw [show v * (T0C / S) + v ^ 2 * P - v ^ 2 * quad S = (v * (T0C / S) - v ^ 2 * quad S) +
    v ^ 2 * P by omega, Nat.add_mul_mod_self_right, Nat.mod_eq_of_lt (by omega)]

/-- **Past the zero crossing it wraps to `p` minus the deficit: nearly every ticket wins**
(the corner case of the specification). -/
theorem threshold_wrap {S v : ℕ} (h : v * (T0C / S) < v ^ 2 * quad S)
    (hp : v ^ 2 * quad S - v * (T0C / S) < P) (hv : 0 < v) :
    threshold S v = P - (v ^ 2 * quad S - v * (T0C / S)) := by
  rw [threshold_eq]
  have hv2 : 1 ≤ v ^ 2 := Nat.one_le_pow _ _ hv
  have hq := quad_lt S
  rw [show v * (T0C / S) + v ^ 2 * P - v ^ 2 * quad S =
      (P - (v ^ 2 * quad S - v * (T0C / S))) + (v ^ 2 - 1) * P by
    have : v ^ 2 * P = (v ^ 2 - 1) * P + P := by
      rw [Nat.sub_mul, one_mul, Nat.sub_add_cancel (Nat.le_mul_of_pos_left _ (by omega))]
    omega, Nat.add_mul_mod_self_right, Nat.mod_eq_of_lt (by omega)]

/-- The log series of `c = -ln(29/30)` to 53 terms, and its error bound. -/
def S53 : ℚ := ∑ i ∈ Finset.range 53, (1 / 30 : ℚ) ^ (i + 1) / (i + 1)
def E53 : ℚ := (1 / 30 : ℚ) ^ 54 / (1 - 1 / 30)

set_option maxRecDepth 100000 in
theorem S53_bounds :
    (P : ℚ) * (S53 + E53) < T0C + 1 ∧ (T0C : ℚ) ≤ P * (S53 - E53) ∧
      (P : ℚ) * (S53 + E53) ^ 2 / 2 < T1C + 1 ∧ (T1C : ℚ) ≤ P * (S53 - E53) ^ 2 / 2 ∧
      0 ≤ S53 - E53 := by
  decide +kernel

/-- **The specification's constants are exact for `f = 1/30`**: `t0_constant = ⌊-p ln(1-f)⌋`
and `t1_constant = ⌊p ln²(1-f) / 2⌋`. -/
theorem constants_exact :
    T0C = ⌊(P : ℝ) * rate (1 / 30)⌋₊ ∧ T1C = ⌊(P : ℝ) * rate (1 / 30) ^ 2 / 2⌋₊ := by
  have hb := abs_log_sub_add_sum_range_le (x := (1 / 30 : ℝ)) (by norm_num) 53
  have hS : (∑ i ∈ Finset.range 53, (1 / 30 : ℝ) ^ (i + 1) / (i + 1)) = (S53 : ℝ) := by
    simp only [S53]; push_cast; rfl
  have hE : |(1 / 30 : ℝ)| ^ (53 + 1) / (1 - |(1 / 30 : ℝ)|) = (E53 : ℝ) := by
    simp only [E53]; push_cast; norm_num
  rw [hS, hE, abs_le] at hb
  have hc1 : (S53 : ℝ) - E53 ≤ rate (1 / 30) := by unfold rate; norm_num at hb ⊢; linarith
  have hc2 : rate (1 / 30) ≤ (S53 : ℝ) + E53 := by unfold rate; norm_num at hb ⊢; linarith
  obtain ⟨h1, h2, h3, h4, h5⟩ := S53_bounds
  have h1' : (P : ℝ) * ((S53 : ℝ) + E53) < (T0C : ℝ) + 1 := by exact_mod_cast h1
  have h2' : (T0C : ℝ) ≤ P * ((S53 : ℝ) - E53) := by exact_mod_cast h2
  have h3' : (P : ℝ) * ((S53 : ℝ) + E53) ^ 2 / 2 < (T1C : ℝ) + 1 := by exact_mod_cast h3
  have h4' : (T1C : ℝ) ≤ P * ((S53 : ℝ) - E53) ^ 2 / 2 := by exact_mod_cast h4
  have h5' : (0 : ℝ) ≤ (S53 : ℝ) - E53 := by exact_mod_cast h5
  have hP : (0 : ℝ) ≤ P := by positivity
  have hc0 : 0 ≤ rate (1 / 30) := h5'.trans hc1
  constructor
  · symm; rw [Nat.floor_eq_iff (mul_nonneg hP hc0)]
    constructor
    · nlinarith
    · nlinarith
  · symm; rw [Nat.floor_eq_iff (by positivity)]
    have hsq1 : ((S53 : ℝ) - E53) ^ 2 ≤ rate (1 / 30) ^ 2 := pow_le_pow_left₀ h5' hc1 2
    have hsq2 : rate (1 / 30) ^ 2 ≤ ((S53 : ℝ) + E53) ^ 2 :=
      pow_le_pow_left₀ (h5'.trans hc1) hc2 2
    constructor
    · nlinarith
    · nlinarith

/-- **A note never wins more often than with Crypsinous**, up to `2 v² / p`: with a ticket
uniform on `[0, p)`, the probability `threshold / p` that a note of value `v` wins, for an
inferred total stake `S`, is at most `φ_f(v / S) + 2 v² / p` (below the zero crossing). For a
`uint64` value the slack is below `2^{-124}`. -/
theorem win_prob_le {S v : ℕ} (hS : 0 < S) (h : v ^ 2 * quad S ≤ v * (T0C / S))
    (hp : v * (T0C / S) < P) :
    (threshold S v : ℝ) / P ≤ phi (1 / 30) ((v : ℝ) / S) + 2 * (v : ℝ) ^ 2 / P := by
  obtain ⟨hT0, hT1⟩ := constants_exact
  have hP : (0 : ℝ) < P := by norm_num [P]
  have hSr : (1 : ℝ) ≤ S := by exact_mod_cast hS
  have hc : 0 < rate (1 / 30) := rate_pos (by norm_num) (by norm_num)
  have hψ := approx2_le_phi (f := 1 / 30) (by norm_num) (by norm_num)
    (α := (v : ℝ) / S) (by positivity)
  rw [approx2] at hψ
  set c := rate (1 / 30)
  -- the constants against `p c` and `p c² / 2`
  have e0 : (T0C : ℝ) ≤ P * c := by rw [hT0]; exact Nat.floor_le (by positivity)
  have e1 : (P : ℝ) * c ^ 2 / 2 < T1C + 1 := by rw [hT1]; exact Nat.lt_floor_add_one _
  have d0 : ((T0C / S : ℕ) : ℝ) ≤ P * c / S := by
    calc ((T0C / S : ℕ) : ℝ) ≤ (T0C : ℝ) / S := Nat.cast_div_le
      _ ≤ P * c / S := by gcongr
  have d1 : (T1C : ℝ) / S ^ 2 - 1 ≤ (quad S : ℝ) := by
    have := Nat.lt_div_mul_add (a := T1C) (b := S ^ 2) (by positivity)
    have h' : (T1C : ℝ) < (quad S : ℝ) * S ^ 2 + S ^ 2 := by
      unfold quad; exact_mod_cast this
    rw [div_sub_one (by positivity), div_le_iff₀ (by positivity)]
    linarith
  rw [threshold_no_wrap h hp, Nat.cast_sub h, div_le_iff₀ hP]
  push_cast
  have hv : (0 : ℝ) ≤ v := by positivity
  have k0 : (v : ℝ) * ((T0C / S : ℕ) : ℝ) ≤ P * c * ((v : ℝ) / S) := by
    calc (v : ℝ) * ((T0C / S : ℕ) : ℝ) ≤ v * (P * c / S) := by gcongr
      _ = P * c * ((v : ℝ) / S) := by ring
  have k1 : (P : ℝ) * c ^ 2 / 2 * ((v : ℝ) / S) ^ 2 - 2 * (v : ℝ) ^ 2 ≤
      (v : ℝ) ^ 2 * (quad S : ℝ) := by
    have hq : (P : ℝ) * c ^ 2 / 2 / S ^ 2 - 1 / S ^ 2 - 1 ≤ (quad S : ℝ) := by
      have : (P : ℝ) * c ^ 2 / 2 / S ^ 2 - 1 / S ^ 2 ≤ (T1C : ℝ) / S ^ 2 := by
        rw [← sub_div]; gcongr; linarith
      linarith
    have hS2 : (v : ℝ) ^ 2 / S ^ 2 ≤ (v : ℝ) ^ 2 := by
      apply div_le_self (by positivity); nlinarith
    have e1 : (P : ℝ) * c ^ 2 / 2 * ((v : ℝ) / S) ^ 2 = (v : ℝ) ^ 2 * (P * c ^ 2 / 2 / S ^ 2) := by
      ring
    have e2 : (v : ℝ) ^ 2 * ((P : ℝ) * c ^ 2 / 2 / S ^ 2 - 1 / S ^ 2 - 1) =
        (v : ℝ) ^ 2 * (P * c ^ 2 / 2 / S ^ 2) - (v : ℝ) ^ 2 / S ^ 2 - (v : ℝ) ^ 2 := by ring
    have e3 := mul_le_mul_of_nonneg_left hq (sq_nonneg (v : ℝ))
    linarith
  have : (P : ℝ) * (((v : ℝ) / S) * (c - c ^ 2 / 2 * ((v : ℝ) / S))) =
      P * c * ((v : ℝ) / S) - P * c ^ 2 / 2 * ((v : ℝ) / S) ^ 2 := by ring
  have hdiv : 2 * (v : ℝ) ^ 2 / P * P = 2 * (v : ℝ) ^ 2 := div_mul_cancel₀ _ hP.ne'
  have := mul_le_mul_of_nonneg_left hψ hP.le
  nlinarith

/-- The constants satisfy `t0_constant / t1_constant ∈ (58.98, 59.0)`, so the integer
threshold returns to `0` near `v = 59 S`, as `2/c` does. -/
theorem constants_ratio : 5898 * T1C < 100 * T0C ∧ 100 * T0C < 5900 * T1C := by decide

end Mantle.Lottery
