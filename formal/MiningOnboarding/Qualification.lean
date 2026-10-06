import MiningOnboarding.AFunction

/-!
# §§8–9 Newcomer payout share, qualification, and minimum mining income

Miners `ι` with incomes `m_i`, `M = ∑ m_i`; newcomers `N ⊆ ι` (tokenless, `a_i = 0`),
`M_N = ∑_{i ∈ N} m_i`, payout share `γ = M_N / M`, weights `w_i = m_i / M_N`.

* `m_eq_gamma_w`: `m_i = γ w_i M`;
* `newcomer_unlocked_share`: `b_i = β m_i t + γ w_i A(t; M)` (`β = 0`: `b_i = γ w_i A`);
* `newcomers_unlocked_sum`: `B_N(t) = ∑_{i ∈ N} b_i(t) = β M_N t + γ A(t; M)`;
* `unlocked_eq_bEq`: with `n` equal incomes `m`, `M = n m/γ` and
  `b(t) = β m t + (γ/n) A(t; n m/γ)` (`bEq`).

Qualification by deadline `T` (`b_i(T) ≥ K_B`), all-locked case `β = 0` unless stated:

* `qualify_iff`: at fixed total payout `M > 0`, `b_i(T) ≥ K_B ↔ m_i ≥ m_req = M K_B / A(T; M)`;
* `qualify_iff_beta`: for any `β`, `b_i(T) ≥ K_B ↔ m_i (β T + A(T; M)/M) ≥ K_B`;
* `all_qualify`: every newcomer qualifies if `m_low = min_{i ∈ N} m_i ≥ m_req`;
* `feasibility_necessary`: an equal-income newcomer qualifies only if `γ P_L T > n K_B`
  (box "Leadership-income feasibility");
* **`exists_unique_mmin`**: conversely, if `γ P_L T > n K_B` there is exactly one
  `m_min > 0` with `(γ/n) A(T; n m_min/γ) = K_B` (the report's defining equation);
* **`qualify_iff_ge_mmin`**: and an equal-income newcomer with `m ≥ 0` qualifies iff
  `m ≥ m_min`;
* `feasible_iff`: some income qualifies iff `γ P_L T > n K_B`;
* `pool_nonneg_iff`: the pool funds payouts through `T` iff `M T ≤ R₀` (budget condition).

The report states `m_min` "solves" its equation; existence and uniqueness rest on
`A(T; M)` being continuous and strictly increasing in `M` with limit `P_L T`
(`AFunction.lean`), which the report does not prove.
-/

open Real Set Filter Topology

namespace Onboarding

/-! ## Payout shares -/

section Shares

variable {ι : Type*} [Fintype ι] (N : Finset ι) (m : ι → ℝ)

/-- `m_i = γ w_i M` with `γ = M_N/M`, `w_i = m_i/M_N`. -/
theorem m_eq_gamma_w (hM : ∑ j, m j ≠ 0) (hMN : ∑ j ∈ N, m j ≠ 0) (i : ι) :
    m i = (∑ j ∈ N, m j) / (∑ j, m j) * (m i / ∑ j ∈ N, m j) * ∑ j, m j := by
  field_simp

/-- A newcomer's unlocked balance in terms of the payout share and its weight:
`b_i(t) = β m_i t + γ w_i A(t; M)`. -/
theorem newcomer_unlocked_share (hMN : ∑ j ∈ N, m j ≠ 0) (S0 PL β t : ℝ) (i : ι) :
    unlocked S0 PL (∑ j, m j) β 0 (m i) t
      = β * m i * t + (∑ j ∈ N, m j) / (∑ j, m j) * (m i / ∑ j ∈ N, m j)
          * A S0 PL (∑ j, m j) t := by
  unfold unlocked; field_simp; ring

/-- The combined newcomer unlocked balance: `B_N(t) = β M_N t + γ A(t; M)`. -/
theorem newcomers_unlocked_sum (S0 PL β t : ℝ) :
    ∑ i ∈ N, unlocked S0 PL (∑ j, m j) β 0 (m i) t
      = β * (∑ j ∈ N, m j) * t + (∑ j ∈ N, m j) / (∑ j, m j) * A S0 PL (∑ j, m j) t := by
  simp only [unlocked, zero_mul, zero_add, Finset.sum_add_distrib, ← Finset.sum_mul,
    ← Finset.mul_sum, ← Finset.sum_div]

end Shares

/-- Unlocked balance of each of `n` equal-income newcomers with income `m`, taking payout share
`γ` (so total payout `M = n m / γ`): `b(t) = β m t + (γ/n) A(t; n m/γ)`. -/
noncomputable def bEq (S0 PL γ n β m t : ℝ) : ℝ := β * m * t + γ / n * A S0 PL (n * m / γ) t

/-- With `n` equal incomes `m` and payout share `γ`, `M = n m/γ` and `b = bEq`. -/
theorem unlocked_eq_bEq {S0 PL γ n β m t : ℝ} (hm : m ≠ 0) (hn : n ≠ 0) :
    unlocked S0 PL (n * m / γ) β 0 m t = bEq S0 PL γ n β m t := by
  unfold unlocked bEq; field_simp; ring

/-! ## Qualification at fixed total payout -/

/-- Required mining income at fixed total payout `M`: `m_req(T; M) = M K_B / A(T; M)`. -/
noncomputable def mreq (S0 PL M KB T : ℝ) : ℝ := M * KB / A S0 PL M T

variable {S0 PL M KB T : ℝ}

/-- `b_i(T) ≥ K_B ↔ m_i ≥ m_req(T; M)` (all-locked, `M > 0`, `A(T; M) > 0`). -/
theorem qualify_iff (hM : 0 < M) (hA : 0 < A S0 PL M T) (m : ℝ) :
    KB ≤ unlocked S0 PL M 0 0 m T ↔ mreq S0 PL M KB T ≤ m := by
  unfold unlocked mreq
  rw [div_le_iff₀ hA, show 0 * g S0 PL M T + 0 * m * T + m / M * A S0 PL M T
    = m * A S0 PL M T / M by ring, le_div_iff₀ hM, mul_comm KB]

/-- With immediately unlocked fraction `β`: `b_i(T) ≥ K_B ↔ m_i (β T + A(T; M)/M) ≥ K_B`. -/
theorem qualify_iff_beta (β m : ℝ) :
    KB ≤ unlocked S0 PL M β 0 m T ↔ KB ≤ m * (β * T + A S0 PL M T / M) := by
  unfold unlocked; constructor <;> intro h <;> linarith [show
    0 * g S0 PL M T + β * m * T + m / M * A S0 PL M T = m * (β * T + A S0 PL M T / M) by ring]

/-- Every newcomer qualifies if the lowest newcomer income is at least `m_req`. -/
theorem all_qualify {ι : Type*} (N : Finset ι) (hN : N.Nonempty) (m : ι → ℝ) (hM : 0 < M)
    (hA : 0 < A S0 PL M T) (h : mreq S0 PL M KB T ≤ N.inf' hN m) :
    ∀ i ∈ N, KB ≤ unlocked S0 PL M 0 0 (m i) T :=
  fun _ hi => (qualify_iff hM hA _).mpr (h.trans (Finset.inf'_le m hi))

/-- Budget condition: the pool stays nonnegative through `T` iff `M T ≤ R₀`. -/
theorem pool_nonneg_iff (R0 : ℝ) : 0 ≤ pool R0 M T ↔ M * T ≤ R0 := by
  unfold pool; constructor <;> intro h <;> linarith

/-! ## Equal incomes: the minimum mining income -/

variable {γ n : ℝ}

theorem bEq_zero_beta (m : ℝ) : bEq S0 PL γ n 0 m T = γ / n * A S0 PL (n * m / γ) T := by
  simp [bEq]

/-- **Leadership-income feasibility.** If an equal-income newcomer with `m ≥ 0` qualifies by
`T > 0`, then `γ P_L T > n K_B`. -/
theorem feasibility_necessary (hS0 : 0 < S0) (hPL : 0 < PL) (hT : 0 < T) (hγ : 0 < γ)
    (hn : 0 < n) {m : ℝ} (hm : 0 ≤ m) (hq : KB ≤ bEq S0 PL γ n 0 m T) : n * KB < γ * PL * T := by
  rw [bEq_zero_beta] at hq
  have hlt := A_lt hS0 (M := n * m / γ) (by positivity) hPL hT
  have : γ / n * A S0 PL (n * m / γ) T < γ / n * (PL * T) :=
    mul_lt_mul_of_pos_left hlt (by positivity)
  have : n * KB < n * (γ / n * (PL * T)) := mul_lt_mul_of_pos_left (by linarith) hn
  rw [show n * (γ / n * (PL * T)) = γ * PL * T by field_simp] at this
  exact this

/-- `m ↦ bEq(m)` is strictly increasing on `[0, ∞)`. -/
theorem bEq_strictMonoOn (hS0 : 0 < S0) (hPL : 0 < PL) (hT : 0 < T) (hγ : 0 < γ) (hn : 0 < n) :
    StrictMonoOn (fun m => bEq S0 PL γ n 0 m T) (Ici 0) := by
  intro m1 h1 m2 h2 h12
  have h1' : (0 : ℝ) ≤ m1 := h1
  have h2' : (0 : ℝ) ≤ m2 := h2
  simp only [bEq_zero_beta]
  refine mul_lt_mul_of_pos_left ?_ (by positivity)
  refine A_strictMonoOn_M hS0 hPL hT (by simp only [mem_Ici]; positivity)
    (by simp only [mem_Ici]; positivity) ?_
  exact div_lt_div_of_pos_right (mul_lt_mul_of_pos_left h12 hn) hγ

theorem bEq_continuousOn (hS0 : 0 < S0) (hPL : 0 < PL) (hT : 0 < T) (hγ : 0 < γ) (hn : 0 < n) :
    ContinuousOn (fun m => bEq S0 PL γ n 0 m T) (Ici 0) := by
  simp only [bEq_zero_beta]
  refine continuousOn_const.mul ((A_continuousOn_M hS0 hT.le).comp (by fun_prop) ?_)
  intro m hm
  have : (0 : ℝ) ≤ m := hm
  simp only [mem_Ioi]
  have : 0 ≤ n * m / γ := by positivity
  linarith

/-- **Existence and uniqueness of `m_min`.** If `γ P_L T > n K_B`, exactly one `m_min > 0`
solves `(γ/n) A(T; n m_min/γ) = K_B`. -/
theorem exists_unique_mmin (hS0 : 0 < S0) (hPL : 0 < PL) (hT : 0 < T) (hγ : 0 < γ) (hn : 0 < n)
    (hKB : 0 < KB) (hfeas : n * KB < γ * PL * T) :
    ∃! m, 0 < m ∧ bEq S0 PL γ n 0 m T = KB := by
  set F := fun m => bEq S0 PL γ n 0 m T
  have hF0 : F 0 = 0 := by simp [F, bEq_zero_beta, A_M_zero hS0]
  -- `F → (γ/n) P_L T > K_B` as `m → ∞`.
  have hlim : Tendsto F atTop (𝓝 (γ / n * (PL * T))) := by
    have hM : Tendsto (fun m => n * m / γ) atTop atTop :=
      (tendsto_id.const_mul_atTop hn).atTop_div_const hγ
    have := ((tendsto_A_M_atTop hS0 hPL hT).comp hM).const_mul (γ / n)
    refine this.congr' (Eventually.of_forall fun m => ?_)
    simp [F, bEq_zero_beta]
  have hgt : KB < γ / n * (PL * T) := by
    rw [show γ / n * (PL * T) = γ * PL * T / n by ring, lt_div_iff₀ hn]; linarith
  obtain ⟨m2, hm2, hm2pos⟩ :=
    ((hlim.eventually (lt_mem_nhds hgt)).and (eventually_gt_atTop 0)).exists
  obtain ⟨m, hm, hFm⟩ := intermediate_value_Icc hm2pos.le
    ((bEq_continuousOn hS0 hPL hT hγ hn).mono Icc_subset_Ici_self)
    (⟨by rw [hF0]; exact hKB.le, hm2.le⟩ : KB ∈ Icc (F 0) (F m2))
  have hmpos : 0 < m := lt_of_le_of_ne hm.1 (by rintro rfl; have : F 0 = KB := hFm; rw [hF0] at this; linarith)
  refine ⟨m, ⟨hmpos, hFm⟩, fun m' ⟨hm', hFm'⟩ => ?_⟩
  exact (bEq_strictMonoOn hS0 hPL hT hγ hn).injOn (mem_Ici.mpr hm'.le) (mem_Ici.mpr hmpos.le)
    (hFm'.trans hFm.symm)

/-- **Qualification iff `m ≥ m_min`.** An equal-income newcomer with income `m ≥ 0`
qualifies by `T` exactly when `m ≥ m_min`. -/
theorem qualify_iff_ge_mmin (hS0 : 0 < S0) (hPL : 0 < PL) (hT : 0 < T) (hγ : 0 < γ)
    (hn : 0 < n) {mmin : ℝ} (hmin : 0 < mmin) (hF : bEq S0 PL γ n 0 mmin T = KB) {m : ℝ}
    (hm : 0 ≤ m) : KB ≤ bEq S0 PL γ n 0 m T ↔ mmin ≤ m := by
  rw [← hF]
  exact (bEq_strictMonoOn hS0 hPL hT hγ hn).le_iff_le (mem_Ici.mpr hmin.le) (mem_Ici.mpr hm)

/-- Some nonnegative income qualifies equal-income newcomers by `T` iff `γ P_L T > n K_B`. -/
theorem feasible_iff (hS0 : 0 < S0) (hPL : 0 < PL) (hT : 0 < T) (hγ : 0 < γ) (hn : 0 < n)
    (hKB : 0 < KB) : (∃ m, 0 ≤ m ∧ KB ≤ bEq S0 PL γ n 0 m T) ↔ n * KB < γ * PL * T := by
  constructor
  · rintro ⟨m, hm, hq⟩; exact feasibility_necessary hS0 hPL hT hγ hn hm hq
  · intro h
    obtain ⟨m, ⟨hm, hF⟩, -⟩ := exists_unique_mmin hS0 hPL hT hγ hn hKB h
    exact ⟨m, hm.le, hF.ge⟩

end Onboarding
