# Mining-funded onboarding (Lean 4 + Mathlib)

A machine-checked version of [`reports/mining_funded_onboarding.tex`](../../reports/mining_funded_onboarding.tex), plus a computable calculator and simulator for exploring the onboarding design.

- **Status:** no `sorry`s, no warnings, only the standard axioms (`propext`, `Classical.choice`, `Quot.sound`).
- **Check** (from `formal/`): `lake build`; `lake env lean MiningOnboardingTest/Axioms.lean` prints the axioms; `lake env lean MiningOnboardingTest/Report.lean` checks the calculator against every number in §12.
- **Explore:** `lake env lean MiningOnboardingTest/Experiments.lean` (edit the scenarios there).

## The model

`Model.lean` gives the closed forms as functions of `(S₀, P_L, M, t)`:
`Stot`, `pool`, `g`, `A`, `stake`, `unlocked`, `locked`. The immediately unlocked fraction `β` is included throughout; `β = 0` is the all-locked baseline. `IsSolution` is the §4 ODE system for a finite set of miners `ι` with non-mining incumbents `S_E`. Solutions only need to be continuous on `[0, ∞)` and differentiable on `(0, ∞)`.

## Results

| Report | Lean | Statement |
|---|---|---|
| §§5–7, boxed | **`fixedPopulation_solution`** | every solution of the ODE system is the closed form: `S_tot = S₀ + (M+P_L)t`, `R = R₀ - Mt`, `S_E = S_E(0) g`, `s_i = a_i g + m_i t + (m_i/M)A`, `b_i = a_i g + β m_i t + (m_i/M)A`. Positivity of `S_tot` is derived |
| §§5–7 | `closedForm_isSolution` | the closed forms solve the system (so `IsSolution` is not vacuous) |
| §7, interpretation of `A` | `A_eq_interp` | `A = P_L t - S₀(g - 1)` |
| App., `t`-dependence | `A_pos`, `A_lt`, `hasDerivAt_A`, `A_strictMonoOn`, `A_strictConvexOn` | `0 < A < P_L t`; `A' = P_L[1 - (1+kt)^{r-1}]`; strictly increasing and strictly convex |
| App., `S₀`-dependence | `A_strictAntiOn_S0`, `tendsto_A_S0_atTop`, `tendsto_A_S0_zero` | strictly decreasing in `S₀`, from `P_L t` to `0` |
| (new) | `A_strictMonoOn_M`, `A_continuousOn_M`, `tendsto_A_M_atTop` | `A(t; ·)` is continuous, strictly increasing in `M`, and tends to `P_L t` |
| §8 | `newcomer_unlocked_share`, `newcomers_unlocked_sum`, `unlocked_eq_bEq` | `b_i = β m_i t + γ w_i A`; `B_N = β M_N t + γA`; equal incomes `b = β m t + (γ/N) A(t; Nm/γ)` |
| §9, boxed | `qualify_iff`, `qualify_iff_beta`, `all_qualify` | `b_i(T) ≥ K_B ⟺ m_i ≥ M K_B / A(T;M)` (and the `β` form) |
| §9, feasibility box | `feasibility_necessary` | qualifying at any finite rate ⇒ `γ P_L T > N K_B` |
| §9, `m_min` | **`exists_unique_mmin`**, **`qualify_iff_ge_mmin`**, **`feasible_iff`** | if `γ P_L T > N K_B` there is exactly one `m_min`, and a newcomer qualifies iff `m ≥ m_min`; so the feasibility condition is also sufficient |
| §9, budget | `pool_nonneg_iff` | `R(T) ≥ 0 ⟺ MT ≤ R₀` |
| §10, `O(ε²)` expansion | `A_le_quadratic`, `quadratic_correction_le_A` | `(M P_L t²/2S₀)[1 - (2M+P_L)t/3S₀] ≤ A ≤ M P_L t²/2S₀` for **all** `t ≥ 0` |
| §10, leading estimate | `m0_le_of_qualifies`, `qualifies_of_ge` | `m₀ ≤ m_req ≤ m₀/(1-δ)` with `δ = (2M+P_L)T/3S₀`: `m₀` always underestimates |
| §11 | `income_threshold`, `total_income_threshold`, `newcomer_income`, `threshold_le_iff`, `threshold_mul_reward` | `d = p m⋆/(h_min w)` gives `m_i = m⋆ h_i/h_min ≥ m⋆`, `M = m⋆ H/h_min`; feasible iff `m⋆ ≤ h_min w`; threshold scales as `1/w` |
| §14, boxed | `Stot_integral`, `pool_integral` | `S_tot = S₀ + ∫(M + P_L)`, `R = R₀ - ∫M` |
| §16, boxed | `stakeInt_solves`, **`stakeInt_unique`**, `hasDerivAt_unlockedPre` | `s_i = ∫ m e^{∫r}` is the unique solution; `b_i = ∫ m[e^{∫r} - (1-β)]` |
| §17, boxed | `lockedBal_eq`, `hasDerivAt_unlockedBal`, `stake_eq_locked_add_unlockedBal` | `k = (1-β)∫_{max(tᵢ,t-L)}^t m`; `b' = βm + rs + 1{t ≥ tᵢ+L}(1-β)m(t-L)` for `t ≠ tᵢ+L` |
| §18 | `cohort_exact` | identical members equal the representative |
| §19, boxed | `tau`, `tau_lt_iff`, `Qe`, `Qe_identical`, `qualified_mono` | `τ ∈ ℝ≥0∞`; `τ < L ⟺ ∃ a < L, b(tᵢ+a) ≥ K_B`; identical cohorts have `Q_e ∈ {0,1}` |
| (new) pool depletion | `exists_depleted_iff` | the pool runs out by `T` iff the total spend before `T` exceeds `R₀` |
| (new) | `depletion_le_mgf`, `depletion_le_bennett` | independent attempts winning w.p. `q_i` with rewards `σ_i ≤ σ̄`, expected spend `E = ∑ q_i σ_i`: `P(spend ≥ R₀) ≤ exp((E/σ̄)(e^{λσ̄}-1) - λR₀)` for all `λ ≥ 0`, and `≤ exp(-(k log(k/μ) - k + μ))`, `μ = E/σ̄`, `k = R₀/σ̄` |
| (new) | **`depletion_le_of_buffer`** | `R₀ ≥ E + √(2σ̄EL) + σ̄L` ⇒ `P(depletion) ≤ e^{-L}`; `L = 28` gives `< 10⁻¹²` (`exp_neg_28_lt`) |
| (new) | `reference_depletion` | `R₀ = 50·10⁶`, `E ≤ 48·10⁶`, `σ̄ ≤ 1000` ⇒ `P(depletion) < 10⁻¹²` |
| §6 vs §16 | `stakeInt_eq_stake` | cross-check: the integral formula reduces to the closed form for constant rates |

## Differences from the report

1. **`m_min` exists, is unique, and characterises qualification.** The report defines `m_min` as "the solution" and proves the feasibility condition necessary. The M-dependence of `A` (not in the report) makes it sufficient: `feasible_iff`.
2. **§10 is two-sided bounds, not `O(ε²)`.** The remainders have a definite sign, so the leading estimate `m₀` is a strict lower bound on the required rate, and `m₀/(1-δ)` is a sufficient rate.
3. **The §17 boxed `db/dt` fails at `t = tᵢ + L`** (a kink in `k` when income starts at arrival), and with piecewise-constant `m_i(t)` the §§14–18 ODEs hold only between arrivals. The integral formulas are the exact statement; the Lean versions allow countably many exceptional times.
4. §9's hypothesis `A(T;M) > 0` always holds for positive parameters (`A_pos`).
5. The report `\input`s `unlocked-mining.tex` (§`sec:beta`), which is not in the repository. The `β` extension here follows the later sections and the appendix (`b = β m t + (m/M) A`).

## Not formalized

- Monotonicity of `A` in `P_L` and its `P_L` limits (App.); the small-`P_L` expansion.
- The first-corrected formula `m_min ≈ m₀[1 + 4N K_B/(3γP_L T) + P_L T/(3S₀)]` (heuristic; the rigorous bounds are above).
- §3's derivation of the linearised leadership share (`φ(α) ≈ cα`); the model takes `E[I_i^L] = P_L s_i/S_tot` as given.
- Continuing entry: positivity of `S_tot` is assumed rather than derived, and there is no coupled-system uniqueness statement (the leadership return `r = P_L/S_tot` is taken as given).

## Exploration (`Explore.lean`)

Computable `Float` code, not proven, checked against the report in `MiningOnboardingTest/Report.lean`:

- **Calculator** (`Net`, `reference`): `A`, `unlocked`, `stake`, `mReq`, `mMin`, `qualTime`, `gammaMin`, `m0`, `m1`.
- **Pool depletion**: `depletionBound`, `depletionBuffer`, `maxClaimReward`, `safeHorizon`.
- **Simulator** (`Scenario`, `simulate`): cohorts arriving every epoch, a `Policy` (`fixedTotal M hC h` split by hashrate, or `fixedIndividual m mC`), pro-rata payout at pool exhaustion, `β`, and maturation after `L`. Each cohort is followed for its full window. Results per cohort: `γ_e` at arrival, `τ_e`, `Q_e`, `b` at age `L`, mining by age `L`.

## Layout

| File | Contents |
|---|---|
| `Model.lean` | closed forms, derivatives, uniqueness, the ODE system and its solution |
| `AFunction.lean` | Appendix: properties of `A(t;M)` in `t`, `S₀` and `M` |
| `Qualification.lean` | §§8–9: payout shares, qualification, `m_min`, feasibility |
| `SmallGrowth.lean` | §10: two-sided Taylor bounds, `m₀` |
| `Difficulty.lean` | §11: mining income from difficulty |
| `ContinuingEntry.lean` | §§13–19: time-dependent rates, integral solution, delayed unlocking, cohorts, `τ`, `Q_e` |
| `PoolDepletion.lean` | probability of depleting the pool under random claims (Chernoff/Bennett) |
| `Explore.lean` | calculator and simulator (`Float`) |
