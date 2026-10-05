import Mathlib

/-!
# §1 Statistics of the leader election

`reports/analysis_of_stochastic_recurrence_equation.tex`, Section 1.

The leaders of one slot form a vector `s ∈ {0,1}^N` of independent Bernoulli
variables, `P(s_i = 1) = φ(α_i)` with `φ(α) = 1 - (1-f)^α`. We prove the mean
(eq. `eqn:aver`) and variance (eq. `eqn:Var`) of the number of leaders, and the
fact used by the binomial reduction of §2: the probability that a slot is empty,
`∏ (1 - φ(w_i/D))`, is `1 - φ(W/D)` with `W = ∑ w_i`.
-/

open Finset

namespace SRE

/-- The leader lottery `φ(α) = 1 - (1-f)^α` (real power). -/
noncomputable def φ (f α : ℝ) : ℝ := 1 - (1 - f) ^ α

/-- The probability of outcome `b` of a Bernoulli(`p`) variable:
`p·δ_{1;b} + (1-p)·δ_{0;b}` (eq. `def:Prob-s`). -/
def bern (p : ℝ) : Bool → ℝ
  | true => p
  | false => 1 - p

/-- The expectation `⟨F⟩` when the `s i` are independent, `s i ∼ Bernoulli(p i)`. -/
noncomputable def bexp {ι : Type*} [Fintype ι] [DecidableEq ι] (p : ι → ℝ) (F : (ι → Bool) → ℝ) : ℝ :=
  ∑ s, (∏ i, bern (p i) (s i)) * F s

/-- The `0/1` value of a Boolean, as a real. -/
def ind (b : Bool) : ℝ := if b then 1 else 0

section Bernoulli

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- Independence: the expectation of a product of functions of distinct
coordinates factorises. -/
theorem bexp_prod (p : ι → ℝ) (G : ι → Bool → ℝ) :
    bexp p (fun s => ∏ i, G i (s i)) = ∏ i, (p i * G i true + (1 - p i) * G i false) := by
  unfold bexp
  simp_rw [← Finset.prod_mul_distrib]
  rw [← Fintype.prod_sum (fun i b => bern (p i) b * G i b)]
  congr 1; funext i
  simp [bern]

theorem bexp_one (p : ι → ℝ) : bexp p (fun _ => 1) = 1 := by
  have := bexp_prod p (fun _ _ => 1)
  simp only [prod_const_one, mul_one, add_sub_cancel] at this
  exact this

theorem bexp_add (p : ι → ℝ) (F G : (ι → Bool) → ℝ) :
    bexp p (fun s => F s + G s) = bexp p F + bexp p G := by
  simp [bexp, mul_add, sum_add_distrib]

theorem bexp_const_mul (p : ι → ℝ) (c : ℝ) (F : (ι → Bool) → ℝ) :
    bexp p (fun s => c * F s) = c * bexp p F := by
  simp [bexp, mul_sum, mul_left_comm]

theorem bexp_sum {κ : Type*} (p : ι → ℝ) (t : Finset κ) (F : κ → (ι → Bool) → ℝ) :
    bexp p (fun s => ∑ j ∈ t, F j s) = ∑ j ∈ t, bexp p (F j) := by
  unfold bexp
  simp_rw [mul_sum]
  exact sum_comm

/-- `⟨s_j⟩ = p_j`. -/
theorem bexp_coord (p : ι → ℝ) (j : ι) : bexp p (fun s => ind (s j)) = p j := by
  have h := bexp_prod p (fun i b => if i = j then ind b else 1)
  simp only [prod_ite_eq', mem_univ, ↓reduceIte] at h
  rw [h]
  rw [Finset.prod_eq_single j (fun i _ hij => by simp [hij])  (by simp)]
  simp [ind]

/-- `⟨s_i s_j⟩ = δ_{ij} p_i + (1 - δ_{ij}) p_i p_j`. -/
theorem bexp_pair (p : ι → ℝ) (i j : ι) :
    bexp p (fun s => ind (s i) * ind (s j)) = if i = j then p i else p i * p j := by
  by_cases hij : i = j
  · subst hij
    have : (fun s : ι → Bool => ind (s i) * ind (s i)) = fun s => ind (s i) := by
      funext s; cases s i <;> simp [ind]
    simp [this, bexp_coord]
  · have h := bexp_prod p (fun k b => (if k = i then ind b else 1) * (if k = j then ind b else 1))
    simp only [prod_mul_distrib, prod_ite_eq', mem_univ, ↓reduceIte] at h
    rw [h]; simp only [hij, ↓reduceIte]
    have hf : ∀ k, p k * ((if k = i then ind true else 1) * (if k = j then ind true else 1))
        + (1 - p k) * ((if k = i then ind false else 1) * (if k = j then ind false else 1))
        = (if k = i then p k else 1) * (if k = j then p k else 1) := by
      intro k
      by_cases hi : k = i <;> by_cases hj : k = j <;> simp_all [ind]
    simp only [hf, prod_mul_distrib, prod_ite_eq', mem_univ, ↓reduceIte]

/-- **Average number of leaders** (eq. `eqn:aver`): `⟨∑ s_i⟩ = ∑ p_i`. -/
theorem mean_leaders (p : ι → ℝ) : bexp p (fun s => ∑ i, ind (s i)) = ∑ i, p i := by
  rw [bexp_sum]; simp [bexp_coord]

/-- The second moment: `⟨(∑ s_i)²⟩ = ∑ p_i + (∑ p_i)² - ∑ p_i²`. -/
theorem second_moment_leaders (p : ι → ℝ) :
    bexp p (fun s => (∑ i, ind (s i)) ^ 2) = ∑ i, p i + (∑ i, p i) ^ 2 - ∑ i, p i ^ 2 := by
  have hsq : (fun s : ι → Bool => (∑ i, ind (s i)) ^ 2)
      = fun s => ∑ i, ∑ j, ind (s i) * ind (s j) := by
    funext s; rw [sq, sum_mul_sum]
  rw [hsq, bexp_sum]
  simp_rw [bexp_sum, bexp_pair]
  have : ∀ i j : ι, (if i = j then p i else p i * p j)
      = p i * p j + (if i = j then p i - p i ^ 2 else 0) := by
    intro i j; split_ifs with h <;> [subst h; skip] <;> ring
  simp only [this, sum_add_distrib, sum_ite_eq, mem_univ, ↓reduceIte]
  rw [← sum_mul_sum]
  simp only [sum_sub_distrib]
  ring

/-- **Variance of the number of leaders** (eq. `eqn:Var`):
`Var[∑ s_i] = ∑ p_i (1 - p_i)`. -/
theorem var_leaders (p : ι → ℝ) :
    bexp p (fun s => (∑ i, ind (s i)) ^ 2) - (bexp p (fun s => ∑ i, ind (s i))) ^ 2
      = ∑ i, p i * (1 - p i) := by
  rw [second_moment_leaders, mean_leaders]
  simp only [mul_sub, mul_one, sum_sub_distrib, sq]
  ring

/-- The probability that no node is a leader: `P(0) = ∏ (1 - p_i)`. -/
theorem bexp_empty (p : ι → ℝ) :
    bexp p (fun s => if ∀ i, s i = false then 1 else 0) = ∏ i, (1 - p i) := by
  have h := bexp_prod p (fun _ b => if b = false then 1 else 0)
  simp only [prod_boole, mem_univ, true_implies] at h
  rw [h]
  simp

end Bernoulli

/-- The empty-slot probability in closed form:
`∏ (1 - φ(w_i/D)) = 1 - φ(∑ w_i / D)`, i.e. `1 - P(0|D) = φ(W/D)`. -/
theorem prod_one_sub_φ {ι : Type*} [Fintype ι] {f : ℝ} (hf : f < 1) (w : ι → ℝ) (D : ℝ) :
    ∏ i, (1 - φ f (w i / D)) = 1 - φ f ((∑ i, w i) / D) := by
  simp only [φ, sub_sub_cancel]
  rw [Finset.sum_div, Real.rpow_sum_of_pos (by linarith)]

/-- **Expected number of leaders per slot**, in the paper's notation:
`⟨∑ s_i⟩ = ∑ φ(α_i)` and `Var[∑ s_i] = ∑ φ(α_i)(1 - φ(α_i))`. -/
theorem leaders_mean_var {ι : Type*} [Fintype ι] [DecidableEq ι] (f : ℝ) (α : ι → ℝ) :
    bexp (fun i => φ f (α i)) (fun s => ∑ i, ind (s i)) = ∑ i, φ f (α i) ∧
    bexp (fun i => φ f (α i)) (fun s => (∑ i, ind (s i)) ^ 2)
      - (bexp (fun i => φ f (α i)) (fun s => ∑ i, ind (s i))) ^ 2
      = ∑ i, φ f (α i) * (1 - φ f (α i)) :=
  ⟨mean_leaders _, var_leaders _⟩

/-- The logistic form of `P(s_i | D)`: for `0 < φ < 1`,
`P(s) = e^{s·η}/(1 + e^η)` with `η = log(φ/(1-φ))`. -/
theorem bern_logistic {p : ℝ} (h0 : 0 < p) (h1 : p < 1) (b : Bool) :
    bern p b = Real.exp (ind b * Real.log (p / (1 - p))) / (1 + Real.exp (Real.log (p / (1 - p)))) := by
  have hq : 0 < 1 - p := by linarith
  rw [Real.exp_log (div_pos h0 hq)]
  have : 1 + p / (1 - p) = 1 / (1 - p) := by field_simp; ring
  rw [this]
  cases b
  · simp [bern, ind]
  · simp [bern, ind, Real.exp_log (div_pos h0 hq)]; field_simp

end SRE
