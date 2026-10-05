import StochasticRecurrence.Lottery

/-!
# Binomial distribution facts

`binExp T p G = ∑_{k=0}^T C(T,k) p^k (1-p)^{T-k} G(k)` is the expectation of
`G(k)` for `k ∼ Bin(T, p)`. We prove:

* `sum_pi_count`: counting the coordinates with a property among `T` i.i.d.
  coordinates gives a binomial count (the step `[P(0) + (1-P(0))e^{…}]^T = ∑_k …`
  in the proof of Prop. 2.1);
* the binomial mean and variance (eqs. `eq:eta_mean`, `eq:eta_variance`).
-/

open Finset

namespace SRE

/-- The binomial weight `C(T,k) p^k (1-p)^{T-k}`. -/
noncomputable def binW (T : ℕ) (p : ℝ) (k : ℕ) : ℝ := T.choose k * p ^ k * (1 - p) ^ (T - k)

/-- `E[G(k)]` for `k ∼ Bin(T, p)`. -/
noncomputable def binExp (T : ℕ) (p : ℝ) (G : ℕ → ℝ) : ℝ := ∑ k ∈ range (T + 1), binW T p k * G k

theorem binW_nonneg {T : ℕ} {p : ℝ} (h0 : 0 ≤ p) (h1 : p ≤ 1) (k : ℕ) : 0 ≤ binW T p k := by
  unfold binW; have : 0 ≤ 1 - p := by linarith
  positivity

theorem binExp_const (T : ℕ) (p c : ℝ) : binExp T p (fun _ => c) = c := by
  unfold binExp binW
  rw [← sum_mul]
  have h := add_pow p (1 - p) T
  simp only [add_sub_cancel, one_pow] at h
  rw [show ∑ k ∈ range (T + 1), (T.choose k : ℝ) * p ^ k * (1 - p) ^ (T - k) = 1 from by
    exact (sum_congr rfl fun k _ => by ring).trans h.symm]
  ring

theorem binExp_add (T : ℕ) (p : ℝ) (F G : ℕ → ℝ) :
    binExp T p (fun k => F k + G k) = binExp T p F + binExp T p G := by
  simp [binExp, mul_add, sum_add_distrib]

theorem binExp_mul_const (T : ℕ) (p c : ℝ) (F : ℕ → ℝ) :
    binExp T p (fun k => F k * c) = binExp T p F * c := by
  simp [binExp, sum_mul, mul_assoc]

theorem binExp_mono {T : ℕ} {p : ℝ} (h0 : 0 ≤ p) (h1 : p ≤ 1) {F G : ℕ → ℝ}
    (h : ∀ k ≤ T, F k ≤ G k) : binExp T p F ≤ binExp T p G :=
  sum_le_sum fun k hk =>
    mul_le_mul_of_nonneg_left (h k (Nat.lt_succ_iff.mp (mem_range.mp hk))) (binW_nonneg h0 h1 k)

/-- Pascal's rule for the binomial expectation: one more trial is a first trial
(success with probability `p`) followed by `T` trials. -/
theorem binExp_succ (T : ℕ) (p : ℝ) (G : ℕ → ℝ) :
    binExp (T + 1) p G = p * binExp T p (fun k => G (k + 1)) + (1 - p) * binExp T p G := by
  unfold binExp binW
  have h := Finset.sum_choose_succ_mul (fun i j => p ^ i * ((1 - p) ^ j * G i)) T
  simp only [mul_assoc] at h ⊢
  rw [h, add_comm, mul_sum, mul_sum]
  congr 1
  · exact sum_congr rfl fun i _ => by ring
  · refine sum_congr rfl fun i hi => ?_
    have : T + 1 - i = T - i + 1 := by have := mem_range.mp hi; omega
    rw [this]; ring

/-- **Counting i.i.d. coordinates is binomial.** Let `S(1), …, S(T)` be i.i.d. with
law `μ` on a finite type, and `a = μ{π}`. Then the number of `t` with `π(S(t))` is
`Bin(T, a)`: for every test function `G`,
`∑_S ∏_t μ(S t) · G(#{t | π (S t)}) = E_{k ∼ Bin(T,a)} G(k)`. -/
theorem sum_pi_count {Y : Type*} [Fintype Y] (μ : Y → ℝ) (hμ : ∑ y, μ y = 1)
    (π : Y → Prop) [DecidablePred π] :
    ∀ (T : ℕ) (G : ℕ → ℝ),
      ∑ S : Fin T → Y, (∏ t, μ (S t)) * G #{t | π (S t)}
        = binExp T (∑ y with π y, μ y) G := by
  set a := ∑ y with π y, μ y
  have hb : ∑ y with ¬π y, μ y = 1 - a := by
    rw [← hμ, ← sum_filter_add_sum_filter_not univ π μ]; ring
  intro T
  induction T with
  | zero =>
    intro G
    simp [binExp, binW]
  | succ T ih =>
    intro G
    rw [binExp_succ, ← ih, ← ih]
    rw [← (Fin.consEquiv (fun _ => Y)).sum_comp, Fintype.sum_prod_type]
    simp only [Fin.consEquiv_apply, Fin.prod_univ_succ, Fin.cons_zero, Fin.cons_succ,
      Fin.card_filter_univ_succ]
    have : ∀ y : Y, ∑ S : Fin T → Y,
        μ y * (∏ t, μ (S t)) * G (if π y then #{t | π (S t)} + 1 else #{t | π (S t)})
        = if π y then μ y * ∑ S : Fin T → Y, (∏ t, μ (S t)) * G (#{t | π (S t)} + 1)
          else μ y * ∑ S : Fin T → Y, (∏ t, μ (S t)) * G #{t | π (S t)} := by
      intro y
      split_ifs <;> rw [mul_sum] <;> exact sum_congr rfl fun _ _ => by ring
    simp_rw [this]
    rw [sum_ite, ← sum_mul, ← sum_mul, hb]

/-- The binomial mean: `E[k/T] = p`. -/
theorem binExp_mean {T : ℕ} (hT : T ≠ 0) (p : ℝ) :
    binExp T p (fun k => (k : ℝ) / T) = p := by
  obtain ⟨n, rfl⟩ := Nat.exists_eq_succ_of_ne_zero hT
  -- `E[k] = T p` by Pascal: `E_{n+1}[k] = p E_n[k+1] + (1-p) E_n[k] = p + E_n[k]`.
  have key : ∀ n : ℕ, binExp n p (fun k => (k : ℝ)) = n * p := by
    intro n
    induction n with
    | zero => simp [binExp, binW]
    | succ n ih =>
      rw [binExp_succ]
      have : binExp n p (fun k => ((k + 1 : ℕ) : ℝ)) = binExp n p (fun k => (k : ℝ)) + 1 := by
        have := binExp_add n p (fun k => (k : ℝ)) (fun _ => 1)
        rw [binExp_const] at this
        rw [← this]; simp
      rw [this, ih]; push_cast; ring
  have : binExp (n + 1) p (fun k => (k : ℝ) / ((n + 1 : ℕ) : ℝ))
      = binExp (n + 1) p (fun k => (k : ℝ)) * (1 / ((n + 1 : ℕ) : ℝ)) := by
    rw [← binExp_mul_const]; simp [div_eq_mul_inv]
  rw [this, key]; field_simp

/-- **The binomial variance** (eq. `eq:eta_variance`): for `k ∼ Bin(T,p)`,
`E[(k/T - p)²] = p(1-p)/T`. -/
theorem binExp_var {T : ℕ} (hT : T ≠ 0) {p : ℝ} (h0 : 0 ≤ p) (h1 : p ≤ 1) :
    binExp T p (fun k => ((k : ℝ) / T - p) ^ 2) = p * (1 - p) / T := by
  have h := bernstein.variance hT ⟨p, h0, h1⟩
  rw [← h]
  unfold binExp binW
  rw [← Fin.sum_univ_eq_sum_range (fun k => (T.choose k : ℝ) * p ^ k * (1 - p) ^ (T - k)
    * ((k : ℝ) / T - p) ^ 2) (T + 1)]
  refine sum_congr rfl fun k _ => ?_
  simp only [bernstein_apply, bernstein.z]
  ring

/-- `p(1-p)/T ≤ 1/(4T)` (eq. `eq:eta_variance_bound`). -/
theorem binExp_var_le {T : ℕ} (hT : T ≠ 0) {p : ℝ} (h0 : 0 ≤ p) (h1 : p ≤ 1) :
    binExp T p (fun k => ((k : ℝ) / T - p) ^ 2) ≤ 1 / (4 * T) := by
  rw [binExp_var hT h0 h1]
  have hT' : (0 : ℝ) < T := by positivity
  rw [div_le_div_iff₀ hT' (by positivity)]
  nlinarith [sq_nonneg (p - 1 / 2)]

end SRE
