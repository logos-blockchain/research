module

public import Cryptarchia.Prob.Fail3E

/-!
# A table potential for failed checks

The certificates' two-term potential `V2` (`Cold2.lean`) is an exponential in the reach and margin
bounds. A table matches the true value function near reach zero, where crossings happen, much more
closely. `TabPot` holds one: warm values `w ρ` and cold values `c ρ j` (margin `-(j + 1)`) on a box
`ρ ≤ R`, `j < M`, extended geometrically outside it: by `cw` per unit of reach past `R`, and by
`zc⁻¹` per unit of margin below `-M`.

A phase moves the state through `stepO` (`step` with its adversarial count `A`, honest depth `H`
and crossing flag spelled out, `step_eq_stepO`). The shape conditions (`TabPot.Shape`, finitely many
inequalities on the box) make the potential nondecreasing in the reach and the margin (`V_mono`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle

/-- **One phase of the bounds**, from its adversarial count `A`, honest depth `H` and whether it is a
crossing (`step_cases`). -/
def stepO (st : ℤ × ℤ) (A H : ℤ) (X : Bool) : ℤ × ℤ :=
  (max (st.1 + A - H) A,
    if st.2 < -A then st.2 + A - H else if X then st.1 - H else max (st.1 + A - H) A)

open Classical in
theorem step_eq_stepO {Δ : ℕ} {w : CStr} (ℓ e0 e1 : ℕ) (st : ℤ × ℤ) (hst : st.2 ≤ st.1) :
    step Δ w ℓ e0 e1 st = stepO st (advCnt w e0 e1) (hD Δ w e0 e1) (decide (Cross w ℓ e0 e1)) := by
  rw [step_cases ℓ e0 e1 st hst]
  unfold stepO
  by_cases hx : Cross w ℓ e0 e1 <;> simp [hx]

/-- **A table potential**: warm values `w ρ` and cold values `c ρ j` (margin `-(j + 1)`) for
`ρ ≤ R`, `j < M`, extended by `cw` per unit of reach and `zc⁻¹` per unit of margin. -/
structure TabPot where
  R : ℕ
  M : ℕ
  cw : ℝ
  zc : ℝ
  /-- the automaton's factor per adversarial slot -/
  x : ℝ
  w : ℕ → ℝ
  c : ℕ → ℕ → ℝ

namespace TabPot

variable (T : TabPot)

/-- The depth index of a cold margin: `j = -μ - 1`. -/
def dep (μ : ℤ) : ℕ := (-μ - 1).toNat

/-- **The potential.** -/
noncomputable def V (st : ℤ × ℤ) : ℝ :=
  if 0 ≤ st.2 then T.w (min st.1.toNat T.R) * T.cw ^ (st.1.toNat - T.R)
  else T.c (min st.1.toNat T.R) (min (dep st.2) (T.M - 1)) * T.cw ^ (st.1.toNat - T.R) *
    T.zc⁻¹ ^ (dep st.2 - (T.M - 1))

/-- **The shape conditions**, all on the box: positive values, extension factors at least one,
nondecreasing in the reach, each unit of margin worth at least `zc`, a warm value at least `zc`
times the margin `-1` value, warm values growing by at most `cw` per unit of reach, and the
automaton's factor at least `cw · zc`. -/
structure Shape : Prop where
  M_pos : 0 < T.M
  cw1 : 1 ≤ T.cw
  zc1 : 1 ≤ T.zc
  w_pos : ∀ r ≤ T.R, 0 < T.w r
  c_pos : ∀ r ≤ T.R, ∀ j < T.M, 0 < T.c r j
  w_mono : ∀ r < T.R, T.w r ≤ T.w (r + 1)
  c_mono : ∀ r < T.R, ∀ j < T.M, T.c r j ≤ T.c (r + 1) j
  c_decay : ∀ r ≤ T.R, ∀ j, j + 1 < T.M → T.zc * T.c r (j + 1) ≤ T.c r j
  top : ∀ r ≤ T.R, T.zc * T.c r 0 ≤ T.w r
  w_grow : ∀ r < T.R, T.w (r + 1) ≤ T.cw * T.w r
  x_ge : T.cw * T.zc ≤ T.x

variable {T}

theorem V_pos (hS : T.Shape) (st : ℤ × ℤ) : 0 < T.V st := by
  have hcw : 0 < T.cw := by linarith [hS.cw1]
  have hzc : 0 < T.zc⁻¹ := inv_pos.2 (by linarith [hS.zc1])
  unfold V
  split_ifs
  · exact mul_pos (hS.w_pos _ (min_le_right _ _)) (pow_pos hcw _)
  · exact mul_pos (mul_pos (hS.c_pos _ (min_le_right _ _) _ (by have := hS.M_pos; omega)) (pow_pos hcw _))
      (pow_pos hzc _)

/-- The warm value at reach `ρ`. -/
noncomputable def Wv (ρ : ℕ) : ℝ := T.w (min ρ T.R) * T.cw ^ (ρ - T.R)

/-- The cold value at reach `ρ` and depth `j` (margin `-(j + 1)`). -/
noncomputable def Cv (ρ j : ℕ) : ℝ := T.c (min ρ T.R) (min j (T.M - 1)) * T.cw ^ (ρ - T.R) * T.zc⁻¹ ^ (j - (T.M - 1))

theorem V_warm {st : ℤ × ℤ} (h : 0 ≤ st.2) : T.V st = T.Wv st.1.toNat := by unfold V Wv; rw [if_pos h]

theorem V_cold {st : ℤ × ℤ} (h : st.2 < 0) : T.V st = T.Cv st.1.toNat (dep st.2) := by
  unfold V Cv; rw [if_neg (by omega)]

theorem Wv_succ (hS : T.Shape) (ρ : ℕ) : T.Wv ρ ≤ T.Wv (ρ + 1) := by
  unfold Wv
  have hcw := hS.cw1
  rcases Nat.lt_or_ge ρ T.R with h | h
  · rw [min_eq_left h.le, min_eq_left h, Nat.sub_eq_zero_of_le h.le, Nat.sub_eq_zero_of_le h, pow_zero,
      mul_one, mul_one]
    exact hS.w_mono ρ h
  · rw [min_eq_right h, min_eq_right (by omega), show ρ + 1 - T.R = (ρ - T.R) + 1 by omega, pow_succ]
    have := hS.w_pos T.R le_rfl
    have : 0 ≤ T.cw ^ (ρ - T.R) := pow_nonneg (by linarith) _
    nlinarith [mul_le_mul_of_nonneg_left hcw (mul_nonneg (hS.w_pos T.R le_rfl).le this)]

theorem Cv_succ (hS : T.Shape) (ρ j : ℕ) : T.Cv ρ j ≤ T.Cv (ρ + 1) j := by
  unfold Cv
  have hcw := hS.cw1
  have hz : 0 ≤ T.zc⁻¹ ^ (j - (T.M - 1)) := pow_nonneg (inv_nonneg.2 (by linarith [hS.zc1])) _
  have hjM : min j (T.M - 1) < T.M := by have := hS.M_pos; omega
  rcases Nat.lt_or_ge ρ T.R with h | h
  · rw [show min ρ T.R = ρ from min_eq_left h.le, show min (ρ + 1) T.R = ρ + 1 from min_eq_left h,
      Nat.sub_eq_zero_of_le h.le, Nat.sub_eq_zero_of_le h, pow_zero, mul_one, mul_one]
    exact mul_le_mul_of_nonneg_right (hS.c_mono ρ h _ hjM) hz
  · rw [show min ρ T.R = T.R from min_eq_right h, show min (ρ + 1) T.R = T.R from min_eq_right (by omega),
      show ρ + 1 - T.R = (ρ - T.R) + 1 by omega, pow_succ]
    have h0 := (hS.c_pos T.R le_rfl _ hjM).le
    have h1 : 0 ≤ T.cw ^ (ρ - T.R) := pow_nonneg (by linarith) _
    have := mul_le_mul_of_nonneg_left hcw (mul_nonneg h0 h1)
    rw [← mul_assoc]
    exact mul_le_mul_of_nonneg_right (by linarith) hz

theorem Cv_deeper (hS : T.Shape) (ρ j : ℕ) : T.Cv ρ (j + 1) ≤ T.Cv ρ j := by
  unfold Cv
  have hcw : 0 ≤ T.cw ^ (ρ - T.R) := pow_nonneg (by linarith [hS.cw1]) _
  have hzc := hS.zc1
  have hzi0 : 0 ≤ T.zc⁻¹ := inv_nonneg.2 (by linarith)
  have hzi1 : T.zc⁻¹ ≤ 1 := inv_le_one_of_one_le₀ hzc
  have hr : min ρ T.R ≤ T.R := min_le_right _ _
  rcases Nat.lt_or_ge (j + 1) T.M with h | h
  · rw [min_eq_left (by omega : j + 1 ≤ T.M - 1), min_eq_left (by omega : j ≤ T.M - 1),
      Nat.sub_eq_zero_of_le (by omega : j + 1 ≤ T.M - 1), Nat.sub_eq_zero_of_le (by omega : j ≤ T.M - 1),
      pow_zero, mul_one, mul_one]
    have hd := hS.c_decay _ hr j h
    have hp := (hS.c_pos _ hr (j + 1) h).le
    have : T.c (min ρ T.R) (j + 1) ≤ T.c (min ρ T.R) j := by nlinarith
    exact mul_le_mul_of_nonneg_right this hcw
  · have hM := hS.M_pos
    rw [min_eq_right (by omega : T.M - 1 ≤ j + 1), min_eq_right (by omega : T.M - 1 ≤ j),
      show j + 1 - (T.M - 1) = (j - (T.M - 1)) + 1 by omega, pow_succ]
    have hp := (hS.c_pos _ hr (T.M - 1) (by omega)).le
    have hz : 0 ≤ T.zc⁻¹ ^ (j - (T.M - 1)) := pow_nonneg hzi0 _
    have := mul_nonneg (mul_nonneg hp hcw) hz
    nlinarith [mul_le_mul_of_nonneg_left hzi1 this]

theorem Cv_le_Wv (hS : T.Shape) (ρ j : ℕ) : T.Cv ρ j ≤ T.Wv ρ := by
  have h0 : T.Cv ρ j ≤ T.Cv ρ 0 := by
    induction j with
    | zero => exact le_rfl
    | succ j ih => exact (Cv_deeper hS ρ j).trans ih
  refine h0.trans ?_
  unfold Cv Wv
  have hr : min ρ T.R ≤ T.R := min_le_right _ _
  have hM := hS.M_pos
  rw [min_eq_left (Nat.zero_le _), Nat.zero_sub, pow_zero, mul_one]
  have hcw : 0 ≤ T.cw ^ (ρ - T.R) := pow_nonneg (by linarith [hS.cw1]) _
  have htop := hS.top _ hr
  have hp := (hS.c_pos _ hr 0 hM).le
  have : T.c (min ρ T.R) 0 ≤ T.w (min ρ T.R) := by nlinarith [hS.zc1]
  exact mul_le_mul_of_nonneg_right this hcw

theorem Wv_mono (hS : T.Shape) : Monotone T.Wv := monotone_nat_of_le_succ (Wv_succ hS)

theorem Cv_mono_rho (hS : T.Shape) (j : ℕ) : Monotone (fun ρ => T.Cv ρ j) :=
  monotone_nat_of_le_succ fun ρ => Cv_succ hS ρ j

theorem Cv_anti_dep (hS : T.Shape) (ρ : ℕ) : Antitone (T.Cv ρ) := antitone_nat_of_succ_le (Cv_deeper hS ρ)

/-- **The potential is nondecreasing** in the reach and the margin, between states with margin at
most reach. -/
theorem V_mono (hS : T.Shape) {a b : ℤ × ℤ} (ha : a.2 ≤ a.1) (h1 : a.1 ≤ b.1) (h2 : a.2 ≤ b.2) :
    T.V a ≤ T.V b := by
  have hρ : a.1.toNat ≤ b.1.toNat := Int.toNat_le_toNat h1
  by_cases hb : 0 ≤ b.2
  · rw [V_warm hb]
    by_cases ha' : 0 ≤ a.2
    · rw [V_warm ha']; exact Wv_mono hS hρ
    · rw [V_cold (by omega)]; exact (Cv_le_Wv hS _ _).trans (Wv_mono hS hρ)
  · have ha' : a.2 < 0 := by omega
    rw [V_cold ha', V_cold (by omega)]
    have hd : dep b.2 ≤ dep a.2 := by unfold dep; omega
    exact (Cv_anti_dep hS _ hd).trans (Cv_mono_rho hS _ hρ)

/-! ## The extension -/

/-- Past `R`, the warm value grows by exactly `cw` per unit of reach. -/
theorem Wv_add {ρ : ℕ} (h : T.R ≤ ρ) (d : ℕ) : T.Wv (ρ + d) = T.cw ^ d * T.Wv ρ := by
  unfold Wv
  rw [min_eq_right (by omega : T.R ≤ ρ + d), min_eq_right h, show ρ + d - T.R = (ρ - T.R) + d by omega, pow_add]
  ring

/-- Past `R`, the cold value grows by exactly `cw` per unit of reach. -/
theorem Cv_add {ρ : ℕ} (h : T.R ≤ ρ) (d j : ℕ) : T.Cv (ρ + d) j = T.cw ^ d * T.Cv ρ j := by
  unfold Cv
  rw [min_eq_right (by omega : T.R ≤ ρ + d), min_eq_right h, show ρ + d - T.R = (ρ - T.R) + d by omega, pow_add]
  ring

/-- Below `-M`, the cold value shrinks by exactly `zc⁻¹` per unit of margin. -/
theorem Cv_deep_eq {j : ℕ} (h : T.M - 1 ≤ j) (ρ d : ℕ) : T.Cv ρ (j + d) = T.zc⁻¹ ^ d * T.Cv ρ j := by
  unfold Cv
  rw [min_eq_right (by omega : T.M - 1 ≤ j + d), min_eq_right h, show j + d - (T.M - 1) = (j - (T.M - 1)) + d by omega,
    pow_add]
  ring

/-- Each unit of depth costs at least `zc`, everywhere. -/
theorem Cv_deep_le (hS : T.Shape) (ρ j d : ℕ) : T.Cv ρ (j + d) ≤ T.zc⁻¹ ^ d * T.Cv ρ j := by
  have hzc := hS.zc1
  have hzi0 : 0 ≤ T.zc⁻¹ := inv_nonneg.2 (by linarith)
  induction d with
  | zero => simp
  | succ d ih =>
    have h1 : T.Cv ρ (j + d + 1) ≤ T.zc⁻¹ * T.Cv ρ (j + d) := by
      unfold Cv
      have hcw : 0 ≤ T.cw ^ (ρ - T.R) := pow_nonneg (by linarith [hS.cw1]) _
      have hr : min ρ T.R ≤ T.R := min_le_right _ _
      have hM := hS.M_pos
      rcases Nat.lt_or_ge (j + d + 1) T.M with hlt | hge
      · rw [min_eq_left (by omega : j + d + 1 ≤ T.M - 1), min_eq_left (by omega : j + d ≤ T.M - 1),
          Nat.sub_eq_zero_of_le (by omega : j + d + 1 ≤ T.M - 1), Nat.sub_eq_zero_of_le (by omega : j + d ≤ T.M - 1),
          pow_zero, mul_one, mul_one]
        have hd := hS.c_decay _ hr (j + d) hlt
        have hp := (hS.c_pos _ hr (j + d + 1) hlt).le
        have hz0 : 0 < T.zc := by linarith
        have : T.c (min ρ T.R) (j + d + 1) ≤ T.zc⁻¹ * T.c (min ρ T.R) (j + d) := by
          rw [inv_mul_eq_div, le_div_iff₀ hz0]; linarith
        calc T.c (min ρ T.R) (j + d + 1) * T.cw ^ (ρ - T.R) ≤ T.zc⁻¹ * T.c (min ρ T.R) (j + d) * T.cw ^ (ρ - T.R) :=
              mul_le_mul_of_nonneg_right this hcw
          _ = _ := by ring
      · rw [min_eq_right (by omega : T.M - 1 ≤ j + d + 1), min_eq_right (by omega : T.M - 1 ≤ j + d),
          show j + d + 1 - (T.M - 1) = (j + d - (T.M - 1)) + 1 by omega, pow_succ]
        ring_nf; exact le_rfl
    calc T.Cv ρ (j + (d + 1)) = T.Cv ρ (j + d + 1) := by rw [Nat.add_assoc]
      _ ≤ T.zc⁻¹ * T.Cv ρ (j + d) := h1
      _ ≤ T.zc⁻¹ * (T.zc⁻¹ ^ d * T.Cv ρ j) := mul_le_mul_of_nonneg_left ih hzi0
      _ = _ := by rw [pow_succ]; ring

/-! ## A phase -/

theorem stepO_inv {st : ℤ × ℤ} (hst : Inv st) {A H : ℤ} (hA : 0 ≤ A) (hH : 0 ≤ H) {X : Bool}
    (hX : X = true → A = 0) : (stepO st A H X).2 ≤ (stepO st A H X).1 := by
  obtain ⟨h0, h1, h2⟩ := hst
  unfold stepO
  simp only
  split_ifs with hc hx
  · omega
  · have := hX hx; subst this; omega
  · exact le_rfl

/-- A larger honest depth only lowers the bounds after a phase. -/
theorem stepO_anti_H (st : ℤ × ℤ) {A H H' : ℤ} (h : H ≤ H') (X : Bool) :
    (stepO st A H' X).1 ≤ (stepO st A H X).1 ∧ (stepO st A H' X).2 ≤ (stepO st A H X).2 := by
  unfold stepO
  simp only
  constructor
  · exact max_le_max (by omega) le_rfl
  · split_ifs
    · omega
    · omega
    · exact max_le_max (by omega) le_rfl

/-! ## Representatives -/

/-- Warm values grow by at most `cw` per unit of reach. -/
theorem Wv_le_add (hS : T.Shape) (ρ d : ℕ) : T.Wv (ρ + d) ≤ T.cw ^ d * T.Wv ρ := by
  have hcw := hS.cw1
  induction d with
  | zero => simp
  | succ d ih =>
    have h1 : T.Wv (ρ + d + 1) ≤ T.cw * T.Wv (ρ + d) := by
      rcases Nat.lt_or_ge (ρ + d) T.R with h | h
      · unfold Wv
        rw [show min (ρ + d) T.R = ρ + d from min_eq_left h.le,
          show min (ρ + d + 1) T.R = ρ + d + 1 from min_eq_left h, Nat.sub_eq_zero_of_le h.le,
          Nat.sub_eq_zero_of_le h, pow_zero, mul_one, mul_one]
        exact hS.w_grow _ h
      · rw [Wv_add h 1, pow_one]
    calc T.Wv (ρ + (d + 1)) = T.Wv (ρ + d + 1) := by rw [Nat.add_assoc]
      _ ≤ T.cw * T.Wv (ρ + d) := h1
      _ ≤ T.cw * (T.cw ^ d * T.Wv ρ) := mul_le_mul_of_nonneg_left ih (by linarith)
      _ = _ := by rw [pow_succ]; ring

/-- The margin `-1` value is at most `zc⁻¹` times the warm value. -/
theorem Cv_zero_le (hS : T.Shape) (ρ : ℕ) : T.Cv ρ 0 ≤ T.zc⁻¹ * T.Wv ρ := by
  unfold Cv Wv
  have hr : min ρ T.R ≤ T.R := min_le_right _ _
  have hM := hS.M_pos
  rw [min_eq_left (Nat.zero_le _), Nat.zero_sub, pow_zero, mul_one]
  have hcw : 0 ≤ T.cw ^ (ρ - T.R) := pow_nonneg (by linarith [hS.cw1]) _
  have hz0 : 0 < T.zc := by linarith [hS.zc1]
  have : T.c (min ρ T.R) 0 ≤ T.zc⁻¹ * T.w (min ρ T.R) := by
    rw [inv_mul_eq_div, le_div_iff₀ hz0]; linarith [hS.top _ hr]
  calc T.c (min ρ T.R) 0 * T.cw ^ (ρ - T.R) ≤ T.zc⁻¹ * T.w (min ρ T.R) * T.cw ^ (ρ - T.R) :=
        mul_le_mul_of_nonneg_right this hcw
    _ = _ := by ring

/-- **The representative** of a state: the reach cut at `R + 1` and a cold margin at `-(M + 1)`;
every state outside the box is its representative scaled by `fac`. -/
def rep (st : ℤ × ℤ) : ℤ × ℤ :=
  if 0 ≤ st.2 then (min st.1 (T.R + 1), min st.1 (T.R + 1)) else (min st.1 (T.R + 1), max st.2 (-(T.M + 1 : ℤ)))

/-- The scale of a state over its representative. -/
noncomputable def fac (st : ℤ × ℤ) : ℝ :=
  T.cw ^ (st.1.toNat - (T.R + 1)) * (if 0 ≤ st.2 then 1 else T.zc⁻¹ ^ (dep st.2 - T.M))

theorem fac_nonneg (hS : T.Shape) (st : ℤ × ℤ) : 0 ≤ T.fac st := by
  unfold fac
  have : 0 ≤ T.zc⁻¹ := inv_nonneg.2 (by linarith [hS.zc1])
  have : 0 ≤ T.cw := by linarith [hS.cw1]
  split_ifs <;> positivity

/-- **A state is its representative, scaled.** -/
theorem V_rep (hS : T.Shape) {st : ℤ × ℤ} (h0 : 0 ≤ st.1) (hm : st.2 ≤ st.1) :
    T.V st = T.fac st * T.V (T.rep st) := by
  have hM := hS.M_pos
  unfold rep fac
  by_cases hw : 0 ≤ st.2
  · rw [if_pos hw, if_pos hw, mul_one, V_warm hw, V_warm (show (0 : ℤ) ≤ (min st.1 (T.R + 1), min st.1 (T.R + 1)).2 by
      simp only; omega)]
    simp only
    rcases le_or_gt st.1 (T.R + 1) with h | h
    · rw [min_eq_left h, show st.1.toNat - (T.R + 1) = 0 by omega, pow_zero, one_mul]
    · rw [min_eq_right h.le, show ((T.R : ℤ) + 1).toNat = T.R + 1 by omega]
      have := Wv_add (T := T) (ρ := T.R + 1) (by omega) (st.1.toNat - (T.R + 1))
      rw [show T.R + 1 + (st.1.toNat - (T.R + 1)) = st.1.toNat by omega] at this
      exact this
  · rw [if_neg hw, if_neg hw, V_cold (by omega), V_cold (show (min st.1 (T.R + 1), max st.2 (-(T.M + 1 : ℤ))).2 < 0 by
      simp only; omega)]
    simp only
    have hρ : T.Cv st.1.toNat (dep st.2) = T.cw ^ (st.1.toNat - (T.R + 1)) * T.Cv (min st.1 (T.R + 1)).toNat (dep st.2) := by
      rcases le_or_gt st.1 (T.R + 1) with h | h
      · rw [min_eq_left h, show st.1.toNat - (T.R + 1) = 0 by omega, pow_zero, one_mul]
      · rw [min_eq_right h.le, show ((T.R : ℤ) + 1).toNat = T.R + 1 by omega]
        have := Cv_add (T := T) (ρ := T.R + 1) (by omega) (st.1.toNat - (T.R + 1)) (dep st.2)
        rw [show T.R + 1 + (st.1.toNat - (T.R + 1)) = st.1.toNat by omega] at this
        exact this
    have hμ : T.Cv (min st.1 (T.R + 1)).toNat (dep st.2) =
        T.zc⁻¹ ^ (dep st.2 - T.M) * T.Cv (min st.1 (T.R + 1)).toNat (dep (max st.2 (-(T.M + 1 : ℤ)))) := by
      rcases le_or_gt (-(T.M + 1 : ℤ)) st.2 with h | h
      · rw [max_eq_left h, show dep st.2 - T.M = 0 by unfold dep; omega, pow_zero, one_mul]
      · rw [max_eq_right h.le, show dep (-(T.M + 1 : ℤ)) = T.M by unfold dep; omega]
        have := Cv_deep_eq (T := T) (j := T.M) (by omega) (min st.1 (T.R + 1)).toNat (dep st.2 - T.M)
        rw [show T.M + (dep st.2 - T.M) = dep st.2 by unfold dep; omega] at this
        exact this
    rw [hρ, hμ]; ring

/-! ## The terminal table and the bound after a phase -/

/-- Adversarial counts the terminal table tabulates: past `R + M + 2`, a phase from a state with margin
at least `-(M + 1)` ends warm past the box (`tail_le`). -/
def AX : ℕ := T.R + T.M + 2

/-- The honest-depth stand-in of a phase: `1` with an honest success, `0` without. -/
def bI (b : Bool) : ℤ := if b then 1 else 0

/-- The terminal entry for two or more adversarial slots: the largest `V(next) / x^A` over
`2 ≤ A ≤ AX`. -/
noncomputable def gmax (s : ℤ × ℤ) (b : ℤ) : ℝ :=
  (Finset.Icc 2 T.AX).sup' ⟨2, by simp [AX]⟩ (fun A => T.V (stepO s A b false) / T.x ^ A)

/-- **The terminal table** of a state, for the automaton: `V` after the phase over `x^A`, by `min(A, 2)`
and whether the phase has an honest success. -/
noncomputable def gT (s : ℤ × ℤ) : Fin 3 → Bool → Bool → ℝ := fun a b _ =>
  if a.val = 0 then T.V (stepO s 0 (bI b) false)
  else if a.val = 1 then T.V (stepO s 1 (bI b) false) / T.x
  else T.gmax s (bI b)

/-- **The crossing's credit** at a state: what a crossing saves against the same phase without it. -/
noncomputable def crT (s : ℤ × ℤ) : ℝ := T.V (stepO s 0 1 false) - T.V (stepO s 0 1 true)

/-- The bound after a phase from a representative: the automaton's weight less the crossing's credit. -/
noncomputable def post0 (s : ℤ × ℤ) (m : ℕ) (h : List Out) : ℝ :=
  Wt2 T.x 1 (T.gT s) m h - T.crT s * crossG 1 m h

/-- **The bound after a phase**: the representative's, scaled. -/
noncomputable def post (st : ℤ × ℤ) (m : ℕ) (h : List Out) : ℝ := T.fac st * T.post0 (T.rep st) m h

theorem le_gmax {s : ℤ × ℤ} {b : ℤ} {A : ℕ} (h2 : 2 ≤ A) (hA : A ≤ T.AX) :
    T.V (stepO s A b false) / T.x ^ A ≤ T.gmax s b := by
  unfold gmax
  exact Finset.le_sup' (fun A : ℕ => T.V (stepO s A b false) / T.x ^ A) (Finset.mem_Icc.2 ⟨h2, hA⟩)

theorem x_pos (hS : T.Shape) : 0 < T.x := by
  have := hS.x_ge; have := hS.cw1; have := hS.zc1; nlinarith

theorem cw_le_x (hS : T.Shape) : T.cw ≤ T.x := by
  have := hS.x_ge; have := hS.cw1; have := hS.zc1; nlinarith

/-- **The tail**: from a state with reach at least `0` and margin at least `-(M + 1)`, every count of
two or more adversarial slots is covered by the terminal entry. -/
theorem tail_le (hS : T.Shape) {s : ℤ × ℤ} (h0 : 0 ≤ s.1) (hμ : -(T.M + 1 : ℤ) ≤ s.2) {b : ℤ} (hb0 : 0 ≤ b)
    (hb1 : b ≤ 1) {A : ℕ} (h2 : 2 ≤ A) : T.V (stepO s A b false) ≤ T.x ^ A * T.gmax s b := by
  have hx := x_pos hS
  have hxA : 0 < T.x ^ A := pow_pos hx A
  rcases le_or_gt A T.AX with hA | hA
  · have := le_gmax (T := T) (s := s) (b := b) h2 hA
    rw [div_le_iff₀ hxA] at this; linarith
  · -- past AX: the phase ends warm past the box, and each slot more is a factor cw ≤ x
    have hw : ∀ B : ℕ, T.AX ≤ B →
        T.V (stepO s (B : ℤ) b false) = T.Wv (B + (max (s.1 - b) 0).toNat) := by
      intro B hB
      have hc : ¬ s.2 < -(B : ℤ) := by unfold AX at hB; omega
      unfold stepO
      rw [V_warm (by simp only [if_neg hc, Bool.false_eq_true, ↓reduceIte]; omega)]
      congr 1
      simp only
      omega
    have hR : T.R ≤ T.AX + (max (s.1 - b) 0).toNat := by unfold AX; omega
    have hAX2 : 2 ≤ T.AX := by unfold AX; omega
    have h1 : T.V (stepO s (A : ℤ) b false) = T.x ^ 0 * T.cw ^ (A - T.AX) * T.V (stepO s (T.AX : ℤ) b false) := by
      rw [hw A hA.le, hw T.AX le_rfl, pow_zero, one_mul,
        show A + (max (s.1 - b) 0).toNat = T.AX + (max (s.1 - b) 0).toNat + (A - T.AX) by omega, Wv_add hR]
    have hcx : T.cw ^ (A - T.AX) ≤ T.x ^ (A - T.AX) := pow_le_pow_left₀ (by linarith [hS.cw1]) (cw_le_x hS) _
    have hVp := (V_pos hS (stepO s (T.AX : ℤ) b false)).le
    have h2' := le_gmax (T := T) (s := s) (b := b) hAX2 le_rfl
    rw [div_le_iff₀ (pow_pos hx _)] at h2'
    calc T.V (stepO s (A : ℤ) b false) = T.cw ^ (A - T.AX) * T.V (stepO s (T.AX : ℤ) b false) := by
          rw [h1, pow_zero, one_mul]
      _ ≤ T.x ^ (A - T.AX) * T.V (stepO s (T.AX : ℤ) b false) := mul_le_mul_of_nonneg_right hcx hVp
      _ ≤ T.x ^ (A - T.AX) * (T.gmax s b * T.x ^ T.AX) := mul_le_mul_of_nonneg_left h2' (pow_nonneg hx.le _)
      _ = T.x ^ A * T.gmax s b := by
        conv_rhs => rw [show A = (A - T.AX) + T.AX by omega, pow_add]
        ring

/-- The reach-reduced state: reach `R + 1`, the same cold margin (or warm). -/
def redR (st : ℤ × ℤ) : ℤ × ℤ := if 0 ≤ st.2 then (T.R + 1, T.R + 1) else (T.R + 1, st.2)

/-- **Past `R`, a phase scales exactly**: a state with reach past `R + 1` ends where its reduced state
ends, shifted in reach, so its value is the reduced one's times `cw` per unit. -/
theorem V_stepO_redR (hS : T.Shape) {st : ℤ × ℤ} (h0 : (T.R : ℤ) + 1 ≤ st.1) (hm : st.2 ≤ st.1) (A : ℕ) {b : ℤ}
    (hb0 : 0 ≤ b) (hb1 : b ≤ 1) (X : Bool) :
    T.V (stepO st A b X) = T.cw ^ (st.1.toNat - (T.R + 1)) * T.V (stepO (T.redR st) A b X) := by
  obtain ⟨d, hρ⟩ : ∃ d : ℕ, st.1 = (T.R : ℤ) + 1 + d := ⟨(st.1 - (T.R + 1)).toNat, by omega⟩
  rw [show st.1.toNat - (T.R + 1) = d by omega]
  have hc1 : ¬ ((T.R : ℤ) + 1 < -(A : ℤ)) := by omega
  unfold redR stepO
  by_cases hw : 0 ≤ st.2
  · have hc0 : ¬ st.2 < -(A : ℤ) := by omega
    simp only [hw, ↓reduceIte, hc0, hc1]
    have hR : T.R ≤ (max ((T.R : ℤ) + 1 + A - b) A).toNat := by omega
    by_cases hX : X = true
    · simp only [hX, ↓reduceIte]
      rw [V_warm (by simp only; omega), V_warm (by simp only; omega)]
      simp only
      have hR' : T.R ≤ ((T.R : ℤ) + 1 - b).toNat := by omega
      rw [show (max (st.1 + A - b) A).toNat = ((T.R : ℤ) + 1 - b).toNat + (d + A) by omega,
        show (max ((T.R : ℤ) + 1 + A - b) A).toNat = ((T.R : ℤ) + 1 - b).toNat + A by omega,
        Wv_add hR', Wv_add hR', pow_add]
      ring
    · simp only [Bool.not_eq_true] at hX
      simp only [hX, Bool.false_eq_true, ↓reduceIte]
      rw [V_warm (by simp only; omega), V_warm (by simp only; omega)]
      simp only
      rw [show (max (st.1 + A - b) A).toNat = (max ((T.R : ℤ) + 1 + A - b) A).toNat + d by omega, Wv_add hR]
  · simp only [hw, ↓reduceIte]
    have hR : T.R ≤ (max ((T.R : ℤ) + 1 + A - b) A).toNat := by omega
    by_cases hc : st.2 < -(A : ℤ)
    · simp only [hc, ↓reduceIte]
      rw [V_cold (by simp only; omega), V_cold (by simp only; omega)]
      simp only
      rw [show (max (st.1 + A - b) A).toNat = (max ((T.R : ℤ) + 1 + A - b) A).toNat + d by omega, Cv_add hR]
    · simp only [hc, ↓reduceIte]
      by_cases hX : X = true
      · simp only [hX, ↓reduceIte]
        rw [V_warm (by simp only; omega), V_warm (by simp only; omega)]
        simp only
        have hR' : T.R ≤ ((T.R : ℤ) + 1 - b).toNat := by omega
        rw [show (max (st.1 + A - b) A).toNat = ((T.R : ℤ) + 1 - b).toNat + (d + A) by omega,
          show (max ((T.R : ℤ) + 1 + A - b) A).toNat = ((T.R : ℤ) + 1 - b).toNat + A by omega,
          Wv_add hR', Wv_add hR', pow_add]
        ring
      · simp only [Bool.not_eq_true] at hX
        simp only [hX, Bool.false_eq_true, ↓reduceIte]
        rw [V_warm (by simp only; omega), V_warm (by simp only; omega)]
        simp only
        rw [show (max (st.1 + A - b) A).toNat = (max ((T.R : ℤ) + 1 + A - b) A).toNat + d by omega, Wv_add hR]

theorem Wv_nonneg (hS : T.Shape) (ρ : ℕ) : 0 ≤ T.Wv ρ :=
  mul_nonneg (hS.w_pos _ (min_le_right _ _)).le (pow_nonneg (by linarith [hS.cw1]) _)

/-- `cw ≤ zc⁻¹ x`, to each power. -/
theorem cw_pow_le (hS : T.Shape) (e : ℕ) : T.cw ^ e ≤ T.zc⁻¹ ^ e * T.x ^ e := by
  rw [← mul_pow]
  have hz0 : 0 < T.zc := by linarith [hS.zc1]
  apply pow_le_pow_left₀ (by linarith [hS.cw1])
  rw [inv_mul_eq_div, le_div_iff₀ hz0]; linarith [hS.x_ge]

/-- The margin-reduced state of a deep cold state: margin `-(M + 1)`. -/
def redM (s : ℤ × ℤ) : ℤ × ℤ := (s.1, -(T.M + 1 : ℤ))

/-- **A deep cold state, with at most `M` adversarial slots**: both it and its margin-reduced state stay
cold, and each unit of depth costs at least `zc`. -/
theorem V_stepO_redM_cold (hS : T.Shape) {s : ℤ × ℤ} (h0 : 0 ≤ s.1) (hμ : s.2 < -(T.M + 1 : ℤ)) {b : ℤ}
    (hb0 : 0 ≤ b) (hb1 : b ≤ 1) {A : ℕ} (hA : A ≤ T.M) :
    T.V (stepO s A b false) ≤ T.zc⁻¹ ^ (dep s.2 - T.M) * T.V (stepO (T.redM s) A b false) := by
  unfold redM stepO
  simp only
  have hc0 : s.2 < -(A : ℤ) := by omega
  have hc1 : -(T.M + 1 : ℤ) < -(A : ℤ) := by omega
  simp only [hc0, hc1, ↓reduceIte]
  rw [V_cold (by simp only; omega), V_cold (by simp only; omega)]
  simp only
  have hdep : dep (s.2 + A - b) = dep (-(T.M + 1 : ℤ) + A - b) + (dep s.2 - T.M) := by unfold dep; omega
  rw [hdep]
  exact Cv_deep_le hS _ _ _

/-- **A deep cold state, with two or more adversarial slots**: covered by its margin-reduced state's
terminal entry, scaled by `zc⁻¹` per unit of depth. -/
theorem V_stepO_redM_two (hS : T.Shape) {s : ℤ × ℤ} (h0 : 0 ≤ s.1) (hμ : s.2 < -(T.M + 1 : ℤ)) {b : ℤ}
    (hb0 : 0 ≤ b) (hb1 : b ≤ 1) {A : ℕ} (h2 : 2 ≤ A) :
    T.V (stepO s A b false) ≤ T.zc⁻¹ ^ (dep s.2 - T.M) * (T.x ^ A * T.gmax (T.redM s) b) := by
  have hM := hS.M_pos
  have hx := x_pos hS
  have hz0 : 0 < T.zc := by linarith [hS.zc1]
  have hzi0 : 0 ≤ T.zc⁻¹ := inv_nonneg.2 hz0.le
  have hcw0 : 0 ≤ T.cw := by linarith [hS.cw1]
  set d := dep s.2 - T.M with hd
  have hr0 : 0 ≤ (T.redM s).1 := h0
  have hrμ : -(T.M + 1 : ℤ) ≤ (T.redM s).2 := le_rfl
  have hg0 : 0 ≤ T.gmax (T.redM s) b :=
    le_trans (div_nonneg (V_pos hS _).le (pow_nonneg hx.le _)) (le_gmax (T := T) (A := 2) le_rfl (by unfold AX; omega))
  rcases le_or_gt A T.M with hA | hA
  · -- both stay cold
    refine (V_stepO_redM_cold hS h0 hμ hb0 hb1 hA).trans ?_
    exact mul_le_mul_of_nonneg_left (tail_le hS hr0 hrμ hb0 hb1 h2) (pow_nonneg hzi0 _)
  · obtain ⟨e, he⟩ : ∃ e : ℕ, A = T.M + 1 + e := ⟨A - (T.M + 1), by omega⟩
    by_cases hcatch : s.2 < -(A : ℤ)
    · -- the state stays cold; its reduced state catches up at `M + 1` slots
      have hde : e < d := by rw [hd]; unfold dep; omega
      have hst : stepO s A b false = (max (s.1 + A - b) A, s.2 + A - b) := by
        unfold stepO; simp only [hcatch, ↓reduceIte]
      have hr1 : stepO (T.redM s) ((T.M + 1 : ℕ) : ℤ) b false =
          (max (s.1 + (T.M + 1 : ℕ) - b) (T.M + 1 : ℕ), max (s.1 + (T.M + 1 : ℕ) - b) (T.M + 1 : ℕ)) := by
        unfold stepO redM; simp only [show ¬ (-(T.M + 1 : ℤ) < -((T.M + 1 : ℕ) : ℤ)) by push_cast; omega,
          ↓reduceIte, Bool.false_eq_true]
      have ht := tail_le hS hr0 hrμ hb0 hb1 (A := T.M + 1) (by omega)
      rw [hr1, V_warm (by simp only; omega)] at ht
      simp only at ht
      rw [hst, V_cold (by simp only; omega)]
      simp only
      set ρ0 := (max (s.1 + (T.M + 1 : ℕ) - b) (T.M + 1 : ℕ)).toNat with hρ0
      have hρ : (max (s.1 + A - b) A).toNat = ρ0 + e := by rw [hρ0, he]; push_cast; omega
      have hj : dep (s.2 + A - b) = 0 + (d - e + b.toNat - 1) := by rw [hd]; unfold dep; omega
      rw [hρ, hj]
      have hb' : b.toNat ≤ 1 := by omega
      calc T.Cv (ρ0 + e) (0 + (d - e + b.toNat - 1))
          ≤ T.zc⁻¹ ^ (d - e + b.toNat - 1) * T.Cv (ρ0 + e) 0 := Cv_deep_le hS _ _ _
        _ ≤ T.zc⁻¹ ^ (d - e + b.toNat - 1) * (T.zc⁻¹ * T.Wv (ρ0 + e)) :=
            mul_le_mul_of_nonneg_left (Cv_zero_le hS _) (pow_nonneg hzi0 _)
        _ = T.zc⁻¹ ^ (d - e + b.toNat) * T.Wv (ρ0 + e) := by
            rw [← mul_assoc, ← pow_succ, show d - e + b.toNat - 1 + 1 = d - e + b.toNat by omega]
        _ ≤ T.zc⁻¹ ^ (d - e) * T.Wv (ρ0 + e) := by
            apply mul_le_mul_of_nonneg_right _ (Wv_nonneg hS _)
            rw [pow_add]
            exact mul_le_of_le_one_right (pow_nonneg hzi0 _) (pow_le_one₀ hzi0 (inv_le_one_of_one_le₀ hS.zc1))
        _ ≤ T.zc⁻¹ ^ (d - e) * (T.cw ^ e * T.Wv ρ0) :=
            mul_le_mul_of_nonneg_left (Wv_le_add hS _ _) (pow_nonneg hzi0 _)
        _ ≤ T.zc⁻¹ ^ (d - e) * (T.zc⁻¹ ^ e * T.x ^ e * (T.x ^ (T.M + 1) * T.gmax (T.redM s) b)) := by
            apply mul_le_mul_of_nonneg_left _ (pow_nonneg hzi0 _)
            exact mul_le_mul (cw_pow_le hS e) ht (Wv_nonneg hS ρ0) (mul_nonneg (pow_nonneg hzi0 _) (pow_nonneg hx.le _))
        _ = T.zc⁻¹ ^ d * (T.x ^ A * T.gmax (T.redM s) b) := by
            have hsplit : T.zc⁻¹ ^ d = T.zc⁻¹ ^ (d - e) * T.zc⁻¹ ^ e := by
              rw [← pow_add, Nat.sub_add_cancel hde.le]
            rw [hsplit, he, pow_add, pow_add]; ring
    · -- the state catches up too, with `d` more slots than its reduced state needs
      push Not at hcatch
      have hdA : d ≤ A := by rw [hd]; unfold dep; omega
      have hst : stepO s A b false = (max (s.1 + A - b) A, max (s.1 + A - b) A) := by
        unfold stepO; simp only [show ¬ s.2 < -(A : ℤ) by omega, ↓reduceIte, Bool.false_eq_true]
      have hr1 : stepO (T.redM s) ((A - d : ℕ) : ℤ) b false =
          (max (s.1 + (A - d : ℕ) - b) (A - d : ℕ), max (s.1 + (A - d : ℕ) - b) (A - d : ℕ)) := by
        unfold stepO redM; simp only [show ¬ (-(T.M + 1 : ℤ) < -((A - d : ℕ) : ℤ)) by
          rw [hd] at hdA ⊢; unfold dep at hdA ⊢; push_cast; omega, ↓reduceIte, Bool.false_eq_true]
      have hA2 : 2 ≤ A - d := by rw [hd]; unfold dep; omega
      have ht := tail_le hS hr0 hrμ hb0 hb1 hA2
      rw [hr1, V_warm (by simp only; omega)] at ht
      simp only at ht
      rw [hst, V_warm (by simp only; omega)]
      simp only
      set ρ1 := (max (s.1 + (A - d : ℕ) - b) (A - d : ℕ)).toNat with hρ1
      have hρ : (max (s.1 + A - b) A).toNat = ρ1 + d := by rw [hρ1]; push_cast; omega
      rw [hρ]
      calc T.Wv (ρ1 + d) ≤ T.cw ^ d * T.Wv ρ1 := Wv_le_add hS _ _
        _ ≤ T.zc⁻¹ ^ d * T.x ^ d * (T.x ^ (A - d) * T.gmax (T.redM s) b) :=
            mul_le_mul (cw_pow_le hS d) ht (Wv_nonneg hS ρ1) (mul_nonneg (pow_nonneg hzi0 _) (pow_nonneg hx.le _))
        _ = T.zc⁻¹ ^ d * (T.x ^ A * T.gmax (T.redM s) b) := by
            conv_rhs => rw [show A = d + (A - d) by omega, pow_add]
            ring

theorem bI_nonneg (b : Bool) : 0 ≤ bI b := by unfold bI; split_ifs <;> norm_num

theorem bI_le_one (b : Bool) : bI b ≤ 1 := by unfold bI; split_ifs <;> norm_num

/-- **At a representative**, the terminal table covers every adversarial count. -/
theorem V_stepO_le_gT (hS : T.Shape) {s : ℤ × ℤ} (h0 : 0 ≤ s.1) (hμ : -(T.M + 1 : ℤ) ≤ s.2) (bb : Bool) (A : ℕ) :
    T.V (stepO s A (bI bb) false) ≤ T.x ^ A * T.gT s (acap A) bb false := by
  have hx := x_pos hS
  unfold gT
  rcases Nat.lt_or_ge A 2 with h | h
  · rcases (by omega : A = 0 ∨ A = 1) with rfl | rfl
    · have ha : (acap 0).val = 0 := rfl
      simp only [ha, ↓reduceIte, pow_zero, one_mul, Nat.cast_zero]
      exact le_rfl
    · have ha : (acap 1).val = 1 := rfl
      simp only [ha, one_ne_zero, ↓reduceIte, pow_one, Nat.cast_one]
      rw [mul_div_cancel₀ _ hx.ne']
  · have ha : (acap A).val = 2 := acap_two h
    simp only [ha, show (2 : ℕ) ≠ 0 by norm_num, show (2 : ℕ) ≠ 1 by norm_num, ↓reduceIte]
    exact tail_le hS h0 hμ (bI_nonneg bb) (bI_le_one bb) h

/-- **Domination by the representative**: a phase without a crossing ends at most the representative's
terminal entry, scaled by `fac`. -/
theorem V_stepO_le_fac (hS : T.Shape) {st : ℤ × ℤ} (hst : Inv st) (bb : Bool) (A : ℕ) :
    T.V (stepO st A (bI bb) false) ≤ T.fac st * (T.x ^ A * T.gT (T.rep st) (acap A) bb false) := by
  obtain ⟨h0, h1, h2⟩ := hst
  have hx := x_pos hS
  have hb0 := bI_nonneg bb
  have hb1 := bI_le_one bb
  have hzi0 : 0 ≤ T.zc⁻¹ := inv_nonneg.2 (by linarith [hS.zc1])
  have hM := hS.M_pos
  -- the reach reduction
  set st1 : ℤ × ℤ := if (T.R : ℤ) + 1 ≤ st.1 then T.redR st else st with hst1
  have hred : T.V (stepO st A (bI bb) false) = T.cw ^ (st.1.toNat - (T.R + 1)) * T.V (stepO st1 A (bI bb) false) := by
    rw [hst1]
    split_ifs with hR
    · exact V_stepO_redR hS hR h2 A hb0 hb1 false
    · rw [show st.1.toNat - (T.R + 1) = 0 by omega, pow_zero, one_mul]
  have hcw : 0 ≤ T.cw ^ (st.1.toNat - (T.R + 1)) := pow_nonneg (by linarith [hS.cw1]) _
  have hs1 : st1.1 = min st.1 (T.R + 1) := by
    by_cases hR : (T.R : ℤ) + 1 ≤ st.1 <;> by_cases hw0 : 0 ≤ st.2 <;>
      simp only [hst1, redR, hR, hw0, ↓reduceIte] <;> omega
  have hs2 : st1.2 = if 0 ≤ st.2 then min st.1 (T.R + 1) else st.2 := by
    by_cases hR : (T.R : ℤ) + 1 ≤ st.1 <;> by_cases hw0 : 0 ≤ st.2 <;>
      simp only [hst1, redR, hR, hw0, ↓reduceIte] <;> omega
  rw [hred]
  unfold fac rep
  by_cases hw : 0 ≤ st.2
  · -- warm: the representative is the reduced state
    simp only [hw, ↓reduceIte, mul_one]
    have hr : st1 = (min st.1 (T.R + 1), min st.1 (T.R + 1)) := by
      ext
      · exact hs1
      · rw [hs2, if_pos hw]
    rw [← hr]
    refine mul_le_mul_of_nonneg_left (V_stepO_le_gT hS ?_ ?_ bb A) hcw
    · rw [hs1]; omega
    · rw [hs2, if_pos hw]; omega
  · simp only [hw, ↓reduceIte]
    by_cases hd : -(T.M + 1 : ℤ) ≤ st.2
    · -- a cold state within the box's margins
      rw [max_eq_left hd, show dep st.2 - T.M = 0 by unfold dep; omega, pow_zero, mul_one]
      have hr : st1 = (min st.1 (T.R + 1), st.2) := by
        ext
        · exact hs1
        · rw [hs2, if_neg hw]
      rw [← hr]
      refine mul_le_mul_of_nonneg_left (V_stepO_le_gT hS ?_ ?_ bb A) hcw
      · rw [hs1]; omega
      · rw [hs2, if_neg hw]; exact hd
    · -- a deep cold state: the margin reduction
      push Not at hd
      rw [max_eq_right hd.le]
      have hr : T.redM st1 = (min st.1 (T.R + 1), -(T.M + 1 : ℤ)) := by
        unfold redM; ext
        · exact hs1
        · rfl
      have h10 : 0 ≤ st1.1 := by rw [hs1]; omega
      have h1μ : st1.2 < -(T.M + 1 : ℤ) := by rw [hs2, if_neg hw]; exact hd
      have hdep : dep st1.2 = dep st.2 := by rw [hs2, if_neg hw]
      rw [← hr, mul_assoc]
      refine mul_le_mul_of_nonneg_left ?_ hcw
      rcases Nat.lt_or_ge A 2 with hA | hA
      · have hAM : A ≤ T.M := by omega
        have := V_stepO_redM_cold hS h10 h1μ hb0 hb1 hAM
        rw [hdep] at this
        refine this.trans (mul_le_mul_of_nonneg_left ?_ (pow_nonneg hzi0 _))
        exact V_stepO_le_gT hS (s := T.redM st1) h10 le_rfl bb A
      · have := V_stepO_redM_two hS h10 h1μ hb0 hb1 hA
        rw [hdep] at this
        refine this.trans (le_of_eq ?_)
        unfold gT
        have ha : (acap A).val = 2 := acap_two hA
        simp only [ha, show (2 : ℕ) ≠ 0 by norm_num, show (2 : ℕ) ≠ 1 by norm_num, ↓reduceIte]

/-- **A crossing**, against the representative's. -/
theorem V_stepO_cross_le (hS : T.Shape) {st : ℤ × ℤ} (hst : Inv st) :
    T.V (stepO st 0 1 true) ≤ T.fac st * T.V (stepO (T.rep st) 0 1 true) := by
  obtain ⟨h0, h1, h2⟩ := hst
  by_cases hw : 0 ≤ st.2
  · have hμ : st.2 = st.1 := by rcases h1 with h1 | h1 <;> [exact h1; omega]
    unfold fac rep
    simp only [hw, ↓reduceIte, mul_one]
    by_cases hR : (T.R : ℤ) + 1 ≤ st.1
    · have e := V_stepO_redR hS hR h2 0 (b := 1) (by norm_num) (by norm_num) true
      rw [Nat.cast_zero] at e
      have : T.redR st = (min st.1 (T.R + 1), min st.1 (T.R + 1)) := by
        unfold redR; rw [if_pos hw, min_eq_right hR]
      rw [e, this]
    · push Not at hR
      rw [min_eq_left hR.le, show st.1.toNat - (T.R + 1) = 0 by omega, pow_zero, one_mul]
      have : st = (st.1, st.1) := by ext <;> simp [hμ]
      rw [← this]
  · -- a cold state: a phase with no adversarial slot keeps it cold, crossing or not
    have hc : ∀ s : ℤ × ℤ, s.2 < 0 → stepO s 0 1 true = stepO s 0 1 false := by
      intro s hs; unfold stepO; simp only [show s.2 < -(0 : ℤ) by omega, ↓reduceIte]
    have hrep : (T.rep st).2 < 0 := by unfold rep; rw [if_neg hw]; simp only; omega
    rw [hc st (by omega), hc _ hrep]
    have := V_stepO_le_fac hS ⟨h0, h1, h2⟩ true 0
    simpa [gT, bI, acap] using this

open Classical in
/-- **The pointwise bound after a phase.** -/
theorem post_le (hS : T.Shape) {Δ : ℕ} {st : ℤ × ℤ} (hst : Inv st) (m : ℕ) (h : List Out) :
    T.V (step Δ (strOf h) 0 m h.length st) ≤ T.post st m h := by
  obtain ⟨A, hA⟩ : ∃ A, advCnt (strOf h) m h.length = A := ⟨_, rfl⟩
  obtain ⟨H, hH⟩ : ∃ H, hD Δ (strOf h) m h.length = H := ⟨_, rfl⟩
  obtain ⟨nh, hnh⟩ : ∃ nh, honCnt (strOf h) m h.length = nh := ⟨_, rfl⟩
  have hfac := fac_nonneg hS st
  rw [step_eq_stepO 0 m h.length st hst.2.2, hA, hH]
  unfold post post0
  rw [Wt2_one, hA, hnh]
  unfold crossG
  rw [one_pow, one_mul]
  by_cases hX : Cross (strOf h) 0 m h.length
  · have hA0 : A = 0 := by rw [← hA]; exact hX.1
    have hH1 : H = 1 := by rw [← hH]; exact hD_of_cross hX
    have hn1 : 1 ≤ nh := by rw [← hnh]; exact (honIn_iff_honCnt).1 (honIn_of_cross hX)
    subst hA0 hH1
    simp only [hX, decide_true, ↓reduceIte, mul_one, pow_zero, one_mul, Nat.cast_zero, Nat.cast_one]
    have hg : T.gT (T.rep st) (acap 0) (decide (1 ≤ nh)) (decide (2 ≤ nh)) = T.V (stepO (T.rep st) 0 1 false) := by
      unfold gT bI; simp [hn1, acap]
    rw [hg]
    unfold crT
    rw [show T.V (stepO (T.rep st) 0 1 false) - (T.V (stepO (T.rep st) 0 1 false) - T.V (stepO (T.rep st) 0 1 true)) =
      T.V (stepO (T.rep st) 0 1 true) by ring]
    exact V_stepO_cross_le hS hst
  · simp only [hX, decide_false, Bool.false_eq_true, ↓reduceIte, mul_zero, sub_zero]
    -- an honest depth at least the stand-in only lowers the bounds
    set bb := decide (1 ≤ nh) with hbb
    have hbH : bI bb ≤ (H : ℤ) := by
      unfold bI; rw [hbb]
      by_cases hn : 1 ≤ nh
      · simp only [hn, decide_true, ↓reduceIte]
        have : 1 ≤ H := by rw [← hH]; exact one_le_hD _ ((honIn_iff_honCnt).2 (by rw [hnh]; exact hn))
        exact_mod_cast this
      · simp only [hn, decide_false, Bool.false_eq_true, ↓reduceIte]; positivity
    have hmono := stepO_anti_H st (A := A) hbH false
    have hinv := stepO_inv hst (A := A) (H := H) (by positivity) (by positivity) (X := false) (by simp)
    have h1 := V_mono hS hinv hmono.1 hmono.2
    refine h1.trans ((V_stepO_le_fac hS hst bb A).trans (le_of_eq ?_))
    rfl

/-! ## The failed-check potential -/

/-- **A representative state**: reach at most `R + 1`, warm or with margin at least `-(M + 1)`. The
contraction checks are made at these finitely many states. -/
def IsRep (s : ℤ × ℤ) : Prop :=
  0 ≤ s.1 ∧ s.1 ≤ T.R + 1 ∧ ((s.2 = s.1) ∨ (-(T.M + 1 : ℤ) ≤ s.2 ∧ s.2 < 0))

theorem isRep_rep {st : ℤ × ℤ} (hst : Inv st) : T.IsRep (T.rep st) := by
  obtain ⟨h0, h1, h2⟩ := hst
  unfold IsRep rep
  have hm1 : min st.1 (T.R + 1) ≤ T.R + 1 := min_le_right _ _
  have hm0 : 0 ≤ min st.1 (T.R + 1) := le_min h0 (by omega)
  split_ifs with hw
  · exact ⟨hm0, hm1, Or.inl rfl⟩
  · exact ⟨hm0, hm1, Or.inr ⟨le_max_right _ _, max_lt (by omega) (by omega)⟩⟩

theorem truncG_mul (m G : ℕ) (a : ℝ) (f : List Out → ℝ) :
    truncG m G (fun h => a * f h) = fun h => a * truncG m G f h := by
  funext h; unfold truncG; split_ifs <;> ring

variable {B : Band} {Δ : ℕ}

/-- The conditions tying a table to a certificate's reach potential `c^ρ` (where a check starts) and its
check base `z` (what a check whose margin catches up costs). -/
structure Ties (P : Cert2 B Δ) : Prop where
  w_le : ∀ r ≤ T.R, T.w r ≤ P.c ^ r
  cw_le : T.cw ≤ P.c
  w0 : 1 ≤ T.w 0
  c_ge : ∀ j < T.M, 1 ≤ T.c 0 j * P.z ^ (j + 1)
  zc_le : T.zc ≤ P.z

theorem Wv_le_c (hS : T.Shape) {P : Cert2 B Δ} (hT : T.Ties P) (ρ : ℕ) : T.Wv ρ ≤ P.c ^ ρ := by
  have hc1 := P.hc
  unfold Wv
  rcases Nat.lt_or_ge ρ T.R with h | h
  · rw [min_eq_left h.le, Nat.sub_eq_zero_of_le h.le, pow_zero, mul_one]; exact hT.w_le ρ h.le
  · rw [min_eq_right h]
    calc T.w T.R * T.cw ^ (ρ - T.R) ≤ P.c ^ T.R * P.c ^ (ρ - T.R) :=
          mul_le_mul (hT.w_le _ le_rfl) (pow_le_pow_left₀ (by linarith [hS.cw1]) hT.cw_le _)
            (pow_nonneg (by linarith [hS.cw1]) _) (pow_nonneg (by linarith) _)
      _ = P.c ^ ρ := by rw [← pow_add, Nat.add_sub_cancel' h]

theorem one_le_Cv (hS : T.Shape) {P : Cert2 B Δ} (hT : T.Ties P) (ρ j : ℕ) : 1 ≤ T.Cv ρ j * P.z ^ (j + 1) := by
  have hz1 := P.hz
  have hz0 : 0 < P.z := by linarith
  have hM := hS.M_pos
  have h0 : T.Cv 0 j ≤ T.Cv ρ j := Cv_mono_rho hS j (Nat.zero_le ρ)
  refine le_trans ?_ (mul_le_mul_of_nonneg_right h0 (pow_nonneg hz0.le _))
  unfold Cv
  rw [min_eq_left (Nat.zero_le _), Nat.zero_sub, pow_zero, mul_one]
  rcases Nat.lt_or_ge j T.M with h | h
  · rw [min_eq_left (by omega : j ≤ T.M - 1), Nat.sub_eq_zero_of_le (by omega : j ≤ T.M - 1), pow_zero, mul_one]
    exact hT.c_ge j h
  · rw [min_eq_right (by omega : T.M - 1 ≤ j)]
    have hc := hT.c_ge (T.M - 1) (by omega)
    rw [show T.M - 1 + 1 = T.M by omega] at hc
    have hzc0 : 0 < T.zc := by linarith [hS.zc1]
    -- `zc⁻¹ ≥ z⁻¹`, so each unit of depth past the box costs at most `z`
    have hq : P.z⁻¹ ^ (j - (T.M - 1)) ≤ T.zc⁻¹ ^ (j - (T.M - 1)) :=
      pow_le_pow_left₀ (inv_nonneg.2 hz0.le) (inv_anti₀ hzc0 hT.zc_le) _
    have hzj : P.z ^ (j + 1) = P.z ^ T.M * P.z ^ (j - (T.M - 1)) := by rw [← pow_add]; congr 1; omega
    have hcp := (hS.c_pos 0 (Nat.zero_le _) (T.M - 1) (by omega)).le
    calc (1 : ℝ) ≤ T.c 0 (T.M - 1) * P.z ^ T.M := hc
      _ = T.c 0 (T.M - 1) * P.z⁻¹ ^ (j - (T.M - 1)) * P.z ^ (j + 1) := by
          rw [hzj, inv_pow]; field_simp
      _ ≤ T.c 0 (T.M - 1) * T.zc⁻¹ ^ (j - (T.M - 1)) * P.z ^ (j + 1) :=
          mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hq hcp) (pow_nonneg hz0.le _)

variable {κ : Kern} {M G : ℕ}

/-- **A check starts below the reach potential.** -/
theorem V_warm_le (hS : T.Shape) {P : Cert2 B Δ} (hT : T.Ties P) (ρ : ℤ) (hρ : 0 ≤ ρ) : T.V (ρ, ρ) ≤ P.c ^ ρ := by
  rw [V_warm (show (0 : ℤ) ≤ (ρ, ρ).2 from hρ)]
  simp only
  have := Wv_le_c hS hT ρ.toNat
  rwa [← zpow_natCast, Int.toNat_of_nonneg hρ] at this

/-- **A failed check costs at least `z^-A`.** -/
theorem one_le_V_z (hS : T.Shape) {P : Cert2 B Δ} (hT : T.Ties P) (st : ℤ × ℤ) (A : ℕ) (hA : -(A : ℤ) ≤ st.2) :
    1 ≤ T.V st * P.z ^ A := by
  have hz0 : 0 < P.z := by linarith [P.hz]
  by_cases hw : 0 ≤ st.2
  · rw [V_warm hw]
    have h1 : 1 ≤ T.Wv st.1.toNat := le_trans (by unfold Wv; simpa using hT.w0) (Wv_mono hS (Nat.zero_le _))
    calc (1 : ℝ) = 1 * 1 := by ring
      _ ≤ T.Wv st.1.toNat * P.z ^ A := mul_le_mul h1 (one_le_pow₀ P.hz) zero_le_one (by linarith)
  · rw [V_cold (by omega)]
    have hj : dep st.2 + 1 ≤ A := by unfold dep; omega
    refine (one_le_Cv hS hT st.1.toNat (dep st.2)).trans ?_
    exact mul_le_mul_of_nonneg_left (pow_le_pow_right₀ P.hz hj) (V_pos hS st |>.le.trans_eq (V_cold (by omega)))

/-- **The table as a failed-check potential**, from the contraction checks at the representatives:
`lp` for any phase, `lpi` for one that starts outside `Sw`. -/
noncomputable def toFailPot (hS : T.Shape) (P : Cert2 B Δ) (hT : T.Ties P) {Sw : ℕ → Prop} {lp lpi : ℝ}
    (hlpi : 0 < lpi) (hle : lpi ≤ lp)
    (hex : ∀ s, T.IsRep s → ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (T.post0 s h.length)) h ≤ lp * T.V s)
    (hexIn : ∀ s, T.IsRep s → ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M → ¬ Sw h.length →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (T.post0 s h.length)) h ≤ lpi * T.V s) :
    FailPot κ M G P Sw where
  V := fun _ => T.V
  post := T.post
  lp := lp
  lpi := lpi
  cs := 1
  hlpi := hlpi
  hle := hle
  hcs := zero_le_one
  nonneg _ st := (V_pos hS st).le
  warm _ ρ hρ := by
    rw [one_mul, V_warm (show (0 : ℤ) ≤ (ρ, ρ).2 from hρ)]
    simp only
    have := Wv_le_c hS hT ρ.toNat
    rwa [← zpow_natCast, Int.toNat_of_nonneg hρ] at this
  fail _ st hst A hA := by
    have hz0 : 0 < P.z := by linarith [P.hz]
    by_cases hw : 0 ≤ st.2
    · rw [V_warm hw]
      have h1 : 1 ≤ T.Wv st.1.toNat := le_trans (by unfold Wv; simpa using hT.w0) (Wv_mono hS (Nat.zero_le _))
      calc (1 : ℝ) = 1 * 1 := by ring
        _ ≤ T.Wv st.1.toNat * P.z ^ A := mul_le_mul h1 (one_le_pow₀ P.hz) zero_le_one (by linarith)
    · rw [V_cold (by omega)]
      have hj : dep st.2 + 1 ≤ A := by unfold dep; omega
      refine (one_le_Cv hS hT st.1.toNat (dep st.2)).trans ?_
      exact mul_le_mul_of_nonneg_left (pow_le_pow_right₀ P.hz hj) (V_pos hS st |>.le.trans_eq (V_cold (by omega)))
  post_le st hst m h _ := post_le hS hst m h
  ex st hst h hpe hlM := by
    unfold post
    rw [truncG_mul, ExPh_mul_const, V_rep hS hst.1 hst.2.2]
    rw [mul_left_comm]
    exact mul_le_mul_of_nonneg_left (hex _ (isRep_rep hst) h hpe hlM) (fac_nonneg hS st)
  exIn st hst h hpe hlM hsw := by
    unfold post
    rw [truncG_mul, ExPh_mul_const, V_rep hS hst.1 hst.2.2]
    rw [mul_left_comm]
    exact mul_le_mul_of_nonneg_left (hexIn _ (isRep_rep hst) h hpe hlM hsw) (fac_nonneg hS st)

end TabPot

end Cryptarchia.Prob
