import Mathlib

/-!
# §§2–7 The fixed-population model and its exact solution

A population of miners `ι` (newcomers and capitalised miners together) and non-mining
incumbents with aggregate stake `S_E`. Miner `i` has total stake `s_i`, unlocked balance
`b_i`, constant mining income `m_i` and genesis allocation `a_i`. The leadership pot is
`P_L`, total mining payout `M = ∑ m_i`, active stake at genesis `S₀`, initial pool `R₀`.

A fraction `β` of each mining reward is unlocked immediately (§`sec:beta`); `β = 0` is the
all-locked baseline of §§4–12. The equations hold before the locked mining rewards mature
and before the pool is exhausted (assumption 10 of §2.3).

Closed forms (the report's boxed equations):

* `Stot`:     `S_tot(t) = S₀ + (M + P_L) t`                              (eq. `eq:Stot`)
* `pool`:     `R(t) = R₀ - M t`
* `g`:        `g(t) = (1 + (M + P_L) t / S₀)^{P_L/(M + P_L)}`
* `A`:        `A(t; M) = S₀ + P_L t - S₀ g(t)`                          (eq. `def:A`)
* `stake`:    `s_i(t) = a_i g(t) + m_i t + (m_i/M) A(t; M)`
* `unlocked`: `b_i(t) = a_i g(t) + β m_i t + (m_i/M) A(t; M)`

Main result: **`fixedPopulation_solution`**. Every solution of the ODE system (`IsSolution`)
is given by these closed forms. Solutions are only assumed continuous on `[0, ∞)` and
differentiable on `(0, ∞)`; nothing is assumed about `S_tot` staying positive.
-/

open Real Set

namespace Onboarding

/-! ## Closed forms -/

/-- Total active stake, eq. `eq:Stot`: `S_tot(t) = S₀ + (M + P_L) t`. -/
def Stot (S0 PL M t : ℝ) : ℝ := S0 + (M + PL) * t

/-- Remaining reward pool, `R(t) = R₀ - M t`. -/
def pool (R0 M t : ℝ) : ℝ := R0 - M * t

/-- Homogeneous growth factor of initially staked tokens through reinvested leadership
income: `g(t) = (1 + (M + P_L) t / S₀)^{P_L/(M + P_L)}`. -/
noncomputable def g (S0 PL M t : ℝ) : ℝ := (1 + (M + PL) * t / S0) ^ (PL / (M + PL))

/-- `A(t; M) = S₀ + P_L t - S₀ g(t)` (eq. `def:A`): the leadership income attributable to
mining-funded stake, including reinvestment, excluding mining principal. -/
noncomputable def A (S0 PL M t : ℝ) : ℝ := S0 + PL * t - S0 * g S0 PL M t

/-- Total stake of a miner with genesis allocation `a` and mining income `m`:
`s(t) = a g(t) + m t + (m/M) A(t; M)`. -/
noncomputable def stake (S0 PL M a m t : ℝ) : ℝ :=
  a * g S0 PL M t + m * t + m / M * A S0 PL M t

/-- Unlocked balance of the same miner, before mining unlocks:
`b(t) = a g(t) + β m t + (m/M) A(t; M)`. -/
noncomputable def unlocked (S0 PL M β a m t : ℝ) : ℝ :=
  a * g S0 PL M t + β * m * t + m / M * A S0 PL M t

/-- Locked balance before mining unlocks: `k(t) = (1 - β) m t`. -/
def locked (β m t : ℝ) : ℝ := (1 - β) * m * t

/-! ## Elementary identities -/

variable {S0 PL M t : ℝ}

theorem Stot_pos (hS0 : 0 < S0) (hMP : 0 ≤ M + PL) (ht : 0 ≤ t) : 0 < Stot S0 PL M t := by
  unfold Stot; positivity

/-- The base of `g` is `S_tot / S₀`. -/
theorem g_base (hS0 : 0 < S0) : 1 + (M + PL) * t / S0 = Stot S0 PL M t / S0 := by
  unfold Stot; field_simp

theorem g_zero : g S0 PL M 0 = 1 := by simp [g]

theorem g_pos (hS0 : 0 < S0) (hMP : 0 ≤ M + PL) (ht : 0 ≤ t) : 0 < g S0 PL M t := by
  unfold g; rw [g_base hS0]; exact rpow_pos_of_pos (div_pos (Stot_pos hS0 hMP ht) hS0) _

theorem A_zero : A S0 PL M 0 = 0 := by simp [A, g_zero]

/-- Interpretation of `A`: total leadership income `P_L t` minus the leadership income
`S₀ (g(t) - 1)` attributable to genesis-funded stake. -/
theorem A_eq_interp : A S0 PL M t = PL * t - S0 * (g S0 PL M t - 1) := by unfold A; ring

/-- `s(t) = a g(t) + (m/M)[S₀ + (M + P_L) t - S₀ g(t)]` for `M ≠ 0`: the report's form. -/
theorem stake_eq (hM : M ≠ 0) (a m : ℝ) :
    stake S0 PL M a m t = a * g S0 PL M t + m / M * (S0 + (M + PL) * t - S0 * g S0 PL M t) := by
  unfold stake A; field_simp; ring

/-- Unlocked plus locked is total stake: `s = k + b`. -/
theorem stake_eq_locked_add_unlocked (β a m : ℝ) :
    stake S0 PL M a m t = locked β m t + unlocked S0 PL M β a m t := by
  unfold stake locked unlocked; ring

/-- Tokenless newcomers (`a = 0`): `b(t) = β m t + (m/M) A(t; M)`, `s(t) = m t + (m/M) A`. -/
theorem newcomer (β m : ℝ) :
    unlocked S0 PL M β 0 m t = β * m * t + m / M * A S0 PL M t ∧
      stake S0 PL M 0 m t = m * t + m / M * A S0 PL M t := by
  unfold unlocked stake; constructor <;> ring

/-- `M = 0` makes `A` vanish: with no mining-funded stake there is no leadership income
attributable to it. -/
theorem A_M_zero (hS0 : 0 < S0) : A S0 PL 0 t = 0 := by
  rcases eq_or_ne PL 0 with rfl | hPL
  · simp [A, g]
  · simp only [A, g, zero_add, div_self hPL, rpow_one]
    field_simp; ring

/-! ## Derivatives -/

/-- `g' = (P_L / S_tot) g`. -/
theorem hasDerivAt_g (hS0 : 0 < S0) (hMP : 0 < M + PL) (hpos : 0 < Stot S0 PL M t) :
    HasDerivAt (g S0 PL M) (PL / Stot S0 PL M t * g S0 PL M t) t := by
  have hbase : 0 < 1 + (M + PL) * t / S0 := by rw [g_base hS0]; exact div_pos hpos hS0
  have hlin : HasDerivAt (fun t => 1 + (M + PL) * t / S0) ((M + PL) / S0) t := by
    simpa using ((hasDerivAt_id t).const_mul (M + PL)).div_const S0 |>.const_add 1
  have := hlin.rpow_const (p := PL / (M + PL)) (Or.inl hbase.ne')
  show HasDerivAt (fun y => (1 + (M + PL) * y / S0) ^ (PL / (M + PL))) _ t
  convert this using 1
  rw [rpow_sub_one hbase.ne', g, g_base hS0]
  rw [g_base hS0] at hbase
  field_simp

theorem hasDerivAt_Stot : HasDerivAt (Stot S0 PL M) (M + PL) t := by
  show HasDerivAt (fun t => S0 + (M + PL) * t) _ t
  convert ((hasDerivAt_id' t).const_mul (M + PL)).const_add S0 using 1; ring

theorem hasDerivAt_pool (R0 : ℝ) : HasDerivAt (pool R0 M) (-M) t := by
  show HasDerivAt (fun t => R0 - M * t) _ t
  convert ((hasDerivAt_id' t).const_mul M).const_sub R0 using 1; ring

/-- The closed-form stake solves `ds/dt = m + P_L s / S_tot`. -/
theorem hasDerivAt_stake (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 ≤ PL)
    (hpos : 0 < Stot S0 PL M t) (a m : ℝ) :
    HasDerivAt (stake S0 PL M a m)
      (m + PL * stake S0 PL M a m t / Stot S0 PL M t) t := by
  have hg := hasDerivAt_g hS0 (by linarith) hpos
  have h : HasDerivAt (fun t => a * g S0 PL M t + m / M * (S0 + (M + PL) * t - S0 * g S0 PL M t))
      (a * (PL / Stot S0 PL M t * g S0 PL M t)
        + m / M * ((M + PL) - S0 * (PL / Stot S0 PL M t * g S0 PL M t))) t := by
    have hlin : HasDerivAt (fun t => S0 + (M + PL) * t) (M + PL) t := hasDerivAt_Stot
    exact (hg.const_mul a).add (((hlin.sub (hg.const_mul S0))).const_mul (m / M))
  have heq : stake S0 PL M a m = fun t =>
      a * g S0 PL M t + m / M * (S0 + (M + PL) * t - S0 * g S0 PL M t) := by
    funext t; exact stake_eq hM.ne' a m
  rw [heq]
  convert h using 1
  have hS := hpos.ne'
  unfold Stot at hS ⊢
  field_simp
  ring

/-- The closed-form unlocked balance solves `db/dt = β m + P_L s / S_tot`. -/
theorem hasDerivAt_unlocked (hS0 : 0 < S0) (hM : 0 < M) (hPL : 0 ≤ PL)
    (hpos : 0 < Stot S0 PL M t) (β a m : ℝ) :
    HasDerivAt (unlocked S0 PL M β a m)
      (β * m + PL * stake S0 PL M a m t / Stot S0 PL M t) t := by
  have hs := hasDerivAt_stake hS0 hM hPL hpos a m
  have hk : HasDerivAt (locked β m) ((1 - β) * m) t := by
    show HasDerivAt (fun t => (1 - β) * m * t) _ t
    convert (hasDerivAt_id' t).const_mul ((1 - β) * m) using 1; ring
  have heq : unlocked S0 PL M β a m = fun t => stake S0 PL M a m t - locked β m t := by
    funext t; rw [stake_eq_locked_add_unlocked β]; ring
  rw [heq]; convert hs.sub hk using 1; ring

/-! ## Uniqueness -/

/-- A function continuous on `[0, ∞)` with zero derivative on `(0, ∞)` is constant there. -/
theorem eq_zero_of_hasDerivAt_zero {f : ℝ → ℝ} (hc : ContinuousOn f (Ici 0))
    (hd : ∀ t > 0, HasDerivAt f 0 t) : ∀ t ≥ 0, f t = f 0 := by
  have hdiff : DifferentiableOn ℝ f (interior (Ici 0)) := by
    rw [interior_Ici]; exact fun t ht => (hd t ht).differentiableAt.differentiableWithinAt
  have hderiv : ∀ t ∈ interior (Ici (0 : ℝ)), deriv f t = 0 := by
    rw [interior_Ici]; exact fun t ht => (hd t ht).deriv
  have hmono := monotoneOn_of_deriv_nonneg (convex_Ici 0) hc hdiff (fun t ht => (hderiv t ht).ge)
  have hanti := antitoneOn_of_deriv_nonpos (convex_Ici 0) hc hdiff (fun t ht => (hderiv t ht).le)
  intro t ht
  exact le_antisymm (hanti ((mem_Ici.mpr le_rfl)) ht ht) (hmono (mem_Ici.mpr le_rfl) ht ht)

/-- Two functions continuous on `[0, ∞)` with the same derivative on `(0, ∞)` and the same
value at `0` agree on `[0, ∞)`. -/
theorem eqOn_of_hasDerivAt {f F : ℝ → ℝ} {f' : ℝ → ℝ} (hc : ContinuousOn f (Ici 0))
    (hC : ContinuousOn F (Ici 0)) (hd : ∀ t > 0, HasDerivAt f (f' t) t)
    (hD : ∀ t > 0, HasDerivAt F (f' t) t) (h0 : f 0 = F 0) : ∀ t ≥ 0, f t = F t := by
  intro t ht
  have := eq_zero_of_hasDerivAt_zero (f := fun t => f t - F t) (hc.sub hC)
    (fun t ht => by simpa using (hd t ht).fun_sub (hD t ht)) t ht
  simp only [h0, sub_self] at this; linarith

theorem continuousOn_g (hS0 : 0 < S0) (hMP : 0 < M + PL) : ContinuousOn (g S0 PL M) (Ici 0) :=
  fun _ ht => (hasDerivAt_g hS0 hMP (Stot_pos hS0 hMP.le ht)).continuousAt.continuousWithinAt

/-- Uniqueness for the linear equation `ds/dt = m + (P_L / S_tot) s`: a solution is fixed
by its value at `0`. -/
theorem linear_unique (hS0 : 0 < S0) (hMP : 0 < M + PL) {m : ℝ} {f F : ℝ → ℝ}
    (hc : ContinuousOn f (Ici 0)) (hC : ContinuousOn F (Ici 0))
    (hd : ∀ t > 0, HasDerivAt f (m + PL * f t / Stot S0 PL M t) t)
    (hD : ∀ t > 0, HasDerivAt F (m + PL * F t / Stot S0 PL M t) t)
    (h0 : f 0 = F 0) : ∀ t ≥ 0, f t = F t := by
  -- `(f - F)/g` has zero derivative.
  have hgpos : ∀ t ≥ 0, 0 < g S0 PL M t := fun t ht => g_pos hS0 hMP.le ht
  have hq := eq_zero_of_hasDerivAt_zero (f := fun t => (f t - F t) / g S0 PL M t)
    ((hc.sub hC).div (continuousOn_g hS0 hMP) (fun t ht => (hgpos t ht).ne'))
    (fun t ht => by
      have hpos := Stot_pos hS0 hMP.le ht.le
      have := ((hd t ht).fun_sub (hD t ht)).fun_div (hasDerivAt_g hS0 hMP hpos) (hgpos t ht.le).ne'
      convert this using 1
      have := (hgpos t ht.le).ne'
      field_simp
      ring)
  intro t ht
  have := hq t ht
  simp only [h0, sub_self, zero_div, g_zero] at this
  have := (div_eq_zero_iff.mp this).resolve_right (hgpos t ht).ne'
  linarith

/-! ## The ODE system -/

/-- A solution on `[0, ∞)` of the fixed-population ODE system of §4, with immediately
unlocked fraction `β`, before mining unlocks and before pool exhaustion:

* `ds_i/dt = m_i + P_L s_i / S_tot`,
* `db_i/dt = β m_i + P_L s_i / S_tot`,
* `dS_E/dt = P_L S_E / S_tot`,
* `dR/dt = -M`,

with `S_tot = S_E + ∑ s_i`, `s_i(0) = b_i(0) = a_i` and `S_E(0) + ∑ a_i = S₀`. -/
structure IsSolution {ι : Type*} [Fintype ι] (PL β R0 : ℝ) (m a : ι → ℝ)
    (s b : ι → ℝ → ℝ) (SE R : ℝ → ℝ) : Prop where
  cont_s : ∀ i, ContinuousOn (s i) (Ici 0)
  cont_b : ∀ i, ContinuousOn (b i) (Ici 0)
  cont_SE : ContinuousOn SE (Ici 0)
  cont_R : ContinuousOn R (Ici 0)
  deriv_s : ∀ i, ∀ t > 0, HasDerivAt (s i)
    (m i + PL * s i t / (SE t + ∑ j, s j t)) t
  deriv_b : ∀ i, ∀ t > 0, HasDerivAt (b i)
    (β * m i + PL * s i t / (SE t + ∑ j, s j t)) t
  deriv_SE : ∀ t > 0, HasDerivAt SE (PL * SE t / (SE t + ∑ j, s j t)) t
  deriv_R : ∀ t > 0, HasDerivAt R (-∑ i, m i) t
  init_s : ∀ i, s i 0 = a i
  init_b : ∀ i, b i 0 = a i
  init_R : R 0 = R0

variable {ι : Type*} [Fintype ι] {PL β R0 : ℝ} {m a : ι → ℝ} {s b : ι → ℝ → ℝ}
  {SE R : ℝ → ℝ}

/-- §5: summing the stake equations, `S_tot(t) = S₀ + (M + P_L) t`. The positivity of
`S_tot`, needed to cancel `S_tot / S_tot`, is derived rather than assumed. -/
theorem IsSolution.Stot_eq (sol : IsSolution PL β R0 m a s b SE R) (hPL : 0 ≤ PL)
    (hM : 0 ≤ ∑ i, m i) (hS0 : 0 < SE 0 + ∑ i, a i) :
    ∀ t ≥ 0, SE t + ∑ j, s j t = Stot (SE 0 + ∑ i, a i) PL (∑ i, m i) t := by
  set S := fun t => SE t + ∑ j, s j t with hSdef
  have hcont : ContinuousOn S (Ici 0) :=
    sol.cont_SE.add (continuousOn_finsetSum _ fun i _ => sol.cont_s i)
  have hderiv : ∀ t > 0, HasDerivAt S
      (∑ i, m i + PL * (S t / S t)) t := by
    intro t ht
    have := (sol.deriv_SE t ht).add (HasDerivAt.fun_sum (u := Finset.univ) fun i _ => sol.deriv_s i t ht)
    convert this using 1
    simp only [hSdef, Finset.sum_add_distrib, ← Finset.sum_div, ← Finset.mul_sum]
    ring
  have hS0' : S 0 = SE 0 + ∑ i, a i := by
    simp only [hSdef, Finset.sum_congr rfl fun i _ => sol.init_s i]
  -- `S' ≥ 0`, so `S ≥ S(0) > 0`, so `S' = M + P_L`.
  have hmono : MonotoneOn S (Ici 0) := by
    refine monotoneOn_of_deriv_nonneg (convex_Ici 0) hcont ?_ ?_
    · rw [interior_Ici]; exact fun t ht => (hderiv t ht).differentiableAt.differentiableWithinAt
    · rw [interior_Ici]; intro t ht
      rw [(hderiv t ht).deriv]
      rcases eq_or_ne (S t) 0 with h | h
      · simp [h, hM]
      · rw [div_self h]; linarith
  have hpos : ∀ t ≥ 0, 0 < S t := fun t ht =>
    lt_of_lt_of_le (hS0'.symm ▸ hS0) (hmono (mem_Ici.mpr le_rfl) ht ht)
  refine eqOn_of_hasDerivAt hcont (fun t _ => hasDerivAt_Stot.continuousAt.continuousWithinAt)
    (fun t ht => by simpa [div_self (hpos t ht.le).ne'] using hderiv t ht)
    (fun t _ => hasDerivAt_Stot) (by
      simp only [Stot, mul_zero, add_zero, Finset.sum_congr rfl fun i _ => sol.init_s i])

/-- **The fixed-population solution** (§§5–7). Write `S₀ = S_E(0) + ∑ a_i` and
`M = ∑ m_i > 0`. Every solution of the ODE system is, for `t ≥ 0`:

* `S_tot(t) = S₀ + (M + P_L) t`, `R(t) = R₀ - M t`, `S_E(t) = S_E(0) g(t)`,
* `s_i(t) = a_i g(t) + m_i t + (m_i/M) A(t; M)`,
* `b_i(t) = a_i g(t) + β m_i t + (m_i/M) A(t; M)`. -/
theorem fixedPopulation_solution (sol : IsSolution PL β R0 m a s b SE R) (hPL : 0 ≤ PL)
    (hM : 0 < ∑ i, m i) (hS0 : 0 < SE 0 + ∑ i, a i) :
    let S0 := SE 0 + ∑ i, a i
    let M := ∑ i, m i
    ∀ t ≥ 0, SE t + ∑ j, s j t = Stot S0 PL M t ∧ R t = pool R0 M t ∧
      SE t = SE 0 * g S0 PL M t ∧
      (∀ i, s i t = stake S0 PL M (a i) (m i) t) ∧
      (∀ i, b i t = unlocked S0 PL M β (a i) (m i) t) := by
  intro S0 M
  have hMP : 0 < M + PL := by linarith
  have hStot := sol.Stot_eq hPL hM.le hS0
  -- Replace `S_E + ∑ s_j` by the closed form in every equation.
  have hds : ∀ i, ∀ t > 0, HasDerivAt (s i) (m i + PL * s i t / Stot S0 PL M t) t :=
    fun i t ht => by rw [← hStot t ht.le]; exact sol.deriv_s i t ht
  have hpos : ∀ t ≥ 0, 0 < Stot S0 PL M t := fun t ht => Stot_pos hS0 hMP.le ht
  have hs : ∀ i, ∀ t ≥ 0, s i t = stake S0 PL M (a i) (m i) t := fun i =>
    linear_unique hS0 hMP (sol.cont_s i)
      (fun t ht => (hasDerivAt_stake hS0 hM hPL (hpos t ht) _ _).continuousAt.continuousWithinAt)
      (hds i) (fun t ht => hasDerivAt_stake hS0 hM hPL (hpos t ht.le) _ _)
      (by simp [stake, sol.init_s, g_zero, A_zero])
  refine fun t ht => ⟨hStot t ht, ?_, ?_, fun i => hs i t ht, fun i => ?_⟩
  · exact eqOn_of_hasDerivAt sol.cont_R
      (fun t _ => (hasDerivAt_pool R0).continuousAt.continuousWithinAt)
      sol.deriv_R (fun t _ => hasDerivAt_pool R0) (by simp [pool, sol.init_R]) t ht
  · refine linear_unique (m := 0) (F := fun t => SE 0 * g S0 PL M t) hS0 hMP sol.cont_SE
      (continuousOn_const.mul (continuousOn_g hS0 hMP)) (fun t ht => ?_) (fun t ht => ?_)
      (by simp [g_zero]) t ht
    · rw [← hStot t ht.le, zero_add]; exact sol.deriv_SE t ht
    · have := (hasDerivAt_g hS0 hMP (hpos t ht.le)).const_mul (SE 0)
      convert this using 1; ring
  · -- `s_i - b_i` has derivative `(1 - β) m_i` and starts at `0`.
    have hk := eqOn_of_hasDerivAt (f := fun t => s i t - b i t) (F := locked β (m i))
      ((sol.cont_s i).sub (sol.cont_b i)) (fun t _ => by unfold locked; fun_prop)
      (f' := fun _ => (1 - β) * m i)
      (fun t ht => by convert (sol.deriv_s i t ht).sub (sol.deriv_b i t ht) using 1; ring)
      (fun t _ => by
        show HasDerivAt (fun t => (1 - β) * m i * t) _ t
        convert (hasDerivAt_id' t).const_mul ((1 - β) * m i) using 1; ring)
      (by simp [locked, sol.init_s, sol.init_b]) t ht
    have := stake_eq_locked_add_unlocked (S0 := S0) (PL := PL) (M := M) (t := t) β (a i) (m i)
    linarith [hs i t ht]

/-- The closed forms do solve the system (existence), so `IsSolution` is not vacuous:
with `S₀ = S_E(0) + ∑ a_i > 0`, `M = ∑ m_i > 0`, `P_L ≥ 0`. -/
theorem closedForm_isSolution (hPL : 0 ≤ PL) (hM : 0 < ∑ i, m i) (SE0 : ℝ)
    (hS0 : 0 < SE0 + ∑ i, a i) :
    IsSolution PL β R0 m a
      (fun i => stake (SE0 + ∑ i, a i) PL (∑ i, m i) (a i) (m i))
      (fun i => unlocked (SE0 + ∑ i, a i) PL (∑ i, m i) β (a i) (m i))
      (fun t => SE0 * g (SE0 + ∑ i, a i) PL (∑ i, m i) t) (pool R0 (∑ i, m i)) := by
  set S0 := SE0 + ∑ i, a i
  set M := ∑ i, m i
  have hMP : 0 < M + PL := by linarith
  have hpos : ∀ t ≥ 0, 0 < Stot S0 PL M t := fun t ht => Stot_pos hS0 hMP.le ht
  -- The total is `S_tot`.
  have htot : ∀ t ≥ 0, SE0 * g S0 PL M t + ∑ j, stake S0 PL M (a j) (m j) t = Stot S0 PL M t := by
    intro t ht
    simp only [stake, Finset.sum_add_distrib, ← Finset.sum_mul, ← Finset.sum_div]
    rw [div_self hM.ne']
    simp only [Stot, A]; ring
  refine ⟨fun i t ht => ?_, fun i t ht => ?_, fun t ht => ?_, fun t _ => ?_,
    fun i t ht => ?_, fun i t ht => ?_, fun t ht => ?_, fun t _ => ?_, fun i => ?_, fun i => ?_,
    by simp [pool]⟩
  · exact (hasDerivAt_stake hS0 hM hPL (hpos t ht) _ _).continuousAt.continuousWithinAt
  · exact (hasDerivAt_unlocked hS0 hM hPL (hpos t ht) β _ _).continuousAt.continuousWithinAt
  · exact ((hasDerivAt_g hS0 hMP (hpos t ht)).const_mul SE0).continuousAt.continuousWithinAt
  · exact (hasDerivAt_pool R0).continuousAt.continuousWithinAt
  · rw [htot t ht.le]; exact hasDerivAt_stake hS0 hM hPL (hpos t ht.le) _ _
  · rw [htot t ht.le]; exact hasDerivAt_unlocked hS0 hM hPL (hpos t ht.le) β _ _
  · rw [htot t ht.le]
    convert (hasDerivAt_g hS0 hMP (hpos t ht.le)).const_mul SE0 using 1; ring
  · exact hasDerivAt_pool R0
  · simp [stake, g_zero, A_zero]
  · simp [unlocked, g_zero, A_zero]

end Onboarding
