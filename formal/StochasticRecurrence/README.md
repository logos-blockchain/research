# Stochastic recurrence equation (Lean 4 + Mathlib)

A machine-checked version of [`reports/analysis_of_stochastic_recurrence_equation.tex`](../../reports/analysis_of_stochastic_recurrence_equation.tex): the stake-estimate recurrence `D_{ℓ+1} = D_ℓ - h D_ℓ (f - fraction of non-empty slots)`, its binomial reduction, and the concentration of `D_ℓ` around the mean-field recursion.

- **Status:** no `sorry`s, no warnings, only the standard axioms (`propext`, `Classical.choice`, `Quot.sound`).
- **Check** (from `formal/`): `lake build` checks every proof. `lake env lean StochasticRecurrenceTest/Axioms.lean` prints the axioms of the main results.

## The model

Probabilities are finite sums, so nothing is assumed about measure theory. `chainE κ next x₀ L D₀ F` is the expectation of `F` over the first `L` steps of the Markov chain on `D`. At each step the noise is drawn from the kernel `κ D` and the state moves by `next`. This is the paper's path measure (eq. `def:prob-path`) written as iterated sums.

- **`sChain`** is eq. `eq:SRE`. Each step draws the leader configuration `S = (s(1), …, s(T))`, with independent `s_i(t) ∼ Bernoulli(φ(w_i/D))`.
- **`kChain`** is the binomial chain: `k | D ∼ Bin(T, 1 - φ(W/D))` and `D' = D - hD(f - 1 + k/T)`.
- **`Hyp f h W`**: `0 < f < 1`, `0 < h`, `hf < 1` (eq. `eq:h_condition`), `W ≥ 0`.

## Results

| Paper | Lean | Statement |
|---|---|---|
| §1, eqs. `eqn:aver`, `eqn:Var` | `leaders_mean_var` | `⟨∑ s_i⟩ = ∑ φ(α_i)`, `Var = ∑ φ(α_i)(1 - φ(α_i))` |
| §2, logistic form | `bern_logistic` | `P(s|D) = e^{s η}/(1 + e^η)` |
| eq. `eq:empty_probability` | `empty_slot_prob`, `prod_one_sub_φ` | a slot is empty with probability `∏ (1 - φ(w_i/D)) = 1 - φ(W/D)` |
| eq. `eq:k_distribution_prop` | `nEmpty_pmf` | `P[k = j | D] = C(T,j) (1-φ(W/D))^j φ(W/D)^{T-j}` |
| eq. `eq:nonempty_count` | `nonempty_count` | the number of non-empty slots is `T - k` |
| eq. `eq:binomial_recurrence` | `stepS_eq` | `D_{ℓ+1}[S] = D_ℓ - h D_ℓ (f - 1 + k_ℓ/T)` |
| **Prop. (Binomial reduction)**, `prop:D-distr` | **`binomial_reduction_step`** | the two parts together: `k | D ∼ Bin(T, 1 - φ(W/D))`, and the step depends on `S` only through `k` |
| its "consequently … exactly equivalent" | **`binomial_reduction`** | over any horizon `L`, every test function `Φ` of `(D_0, …, D_L)` has the same expectation under `sChain` and `kChain` |
| eqs. `eq:D_interval`, `eq:d_interval` | `traj_mem`, `mf_mem` | `D_ℓ, d_ℓ ∈ [D_min, D_max]` for `ℓ ≤ L` |
| eq. `eq:error_series` | `err_abs_le` | `|ε_ℓ| ≤ h D_max ∑_{r<ℓ} L_g^{ℓ-1-r} |η_r|` |
| eq. `eq:eta_variance_bound` | `E_eta_sq_le` | `E[η_r²] ≤ 1/(4T)` (via the tower property `E_tower`) |
| eq. `eq:e_second_moment` | `E_err_sq_le` | `E[(D_ℓ - d_ℓ)²] ≤ K/T` with `K` independent of `T` |
| **Thm. 2.1**, any Lipschitz `L_g` | **`concentration`** | the second-moment bound; `P(sup_{ℓ≤L} |D_ℓ - d_ℓ| ≥ δ) ≤ (L+1)K/(Tδ²)`; `|m_ℓ - d_ℓ| ≤ √(K/T)` |
| eq. `eq:main_concentration` | `concentration_OP` | `sup_{ℓ≤L} |D_ℓ - d_ℓ| = O_P(T^{-1/2})`, stated with quantifiers |
| eq. `eq:MF` (saddle point) | `mean_tendsto` | `E[D_ℓ] → d_ℓ` as `T → ∞` |
| eqs. `eq:gprime1`–`eq:q_def` | `hasDerivAt_g` | `g'(D) = 1 - hf + h q(W/D)`, `q(u) = 1 - (1 + Au)e^{-Au}` |
| eqs. `eq:qprime`, `eq:gprime_positive` | `q_strictMonoOn`, `gderiv_pos`, `gderiv_anti` | `q` strictly increasing; `g' ≥ 1 - hf > 0`; `g'` decreasing |
| eq. `eq:Dc_definition` | `exists_unique_critical` | exactly one `D_c > 0` with `g'(D_c) = 1` |
| eqs. `eq:z_equation`–`eq:Dc_formula` | `critical_lambert`, `lambert_unique` | `z = 1 + AW/D_c` is the unique `z > 1` with `z e^{-z} = (1-f)/e`, and `D_c = WA/(z-1)`. So `-z = 𝒲₋₁(-(1-f)/e)` |
| eqs. `eq:uc_critical`, `eq:Dc_uc_relation` | `critical_iff` | `D_c/W = 1/u_c`, with `u_c > 0` the root of `q(u_c) = f` |
| **Prop. (Bounds on the critical ratio)**, `prop:Dc_bounds` | **`Dc_bounds`** | for `a, b > 0`: `q(1/b) < f < q(1/a)` ⟹ `a < D_c/W < b` |
| eqs. `eq:contractive_region`, `eq:Lg_less_1` | `contraction` | `D_c < a` ⟹ `g` is `g'(a)`-Lipschitz on `[a, b]`, with `0 < g'(a) < 1` |
| Remark (Role of the contractive regime), "`D_min > D_c`, or equivalently `L_g < 1`" | `contractive_iff` | `g'(D_min) < 1 ⟺ D_min > D_c`; `g'(D_min)` is the sup of `|g'|` on `[D_min, D_max]` |
| same Remark, "not essential … for any finite Lipschitz constant" | `concentration` | Thm. 2.1 with any Lipschitz constant `L_g ≥ 0` |
| **Thm. 2.1 as stated** | **`theorem_2_1`** | under `hf < 1` and `D_min > D_c`: all three bounds with `K = h²D_max²/(1-L_g²) · L/4` |
| App. B, product formula | `traj_prod` | `D_ℓ = D_0 ∏_{r<ℓ}(1 - h(f - 1 + k_r/T))` |
| App. B, convexity | `tangent_le`, `jensen` | `⟨D(1-φ(W/D))⟩ ≥ ⟨D⟩(1 - φ(W/⟨D⟩))` |
| (new) | `E_step_le_g`, `mean_le_mf` | `E[D_{ℓ+1}] ≤ g(E[D_ℓ])`, and so `E[D_ℓ] ≤ d_ℓ` for **every** `T` |
| eq. `eq:Dc_numerical_verification` | `Dc_numerical_verification` | `q_{1/30}(1/0.1205) < 1/30 < q_{1/30}(1/0.119)` |
| eqs. `eq:Dc_certified_bounds`, `eq:Dc_numerical` | `Dc_ratio` | at `f = 1/30`: `0.119 < D_c/W < 0.1205` (from `Dc_bounds`) |
| App. C | `concentration`, `Kc_le_contractive` | same proof, with `L_g < 1` as a hypothesis |

## Differences from the paper

The paper now includes the earlier findings of this formalization: Thm. 2.1 without contraction (the Remark), the bracket `0.119 < D_c/W < 0.1205`, and a counting proof of the binomial reduction. Both statements the paper marks for checking are proven here: the proof of Prop. (Binomial reduction) (`binomial_reduction_step`), and Prop. (Bounds on the critical ratio) (`Dc_bounds`; the hypothesis `0 < a < b` can be weakened to `a, b > 0`).

What remains beyond the paper:

1. **The saddle-point equation (eq. `eq:MF`) is an inequality at finite `T`.** The paper proves the limit `E[D_ℓ] → d_ℓ` (`mean_tendsto`). At every finite `T`, `E[D_{ℓ+1}] ≤ g(E[D_ℓ])` (`E_step_le_g`), from the convexity remark in Appendix B, and so `E[D_ℓ] ≤ d_ℓ` (`mean_le_mf`).
2. **The trajectory-level reduction.** The paper's proposition is about one step given `D_ℓ`. `binomial_reduction` also states the consequence it draws: the laws of the whole trajectories `(D_0, …, D_L)` agree.

## Not formalized

- The saddle-point derivation itself (§2.2), which the paper now calls formal rather than rigorous: Fourier integrals of `δ` and a `T → ∞` Laplace argument. Its rigorous counterpart is `mean_tendsto`, together with `E_step_le_g`.
- The Fourier-transform proof of the binomial reduction (now Appendix A of the paper). The counting proof in the main text is the one formalized.
- The asymptotic `D_c/W ∼ √(f/2)` as `f → 0` (eq. `eq:Dc_asymptotic`). It is correct numerically: the ratio to `√(f/2)` is 0.957, 0.986 and 0.995 at `f = 10⁻², 10⁻³, 10⁻⁴`.

## Layout

| File | Contents |
|---|---|
| `Lottery.lean` | §1: `φ`, independent Bernoulli expectations, leader mean and variance, empty-slot probability |
| `Binomial.lean` | binomial expectation, Pascal's rule, counting i.i.d. coordinates, mean and variance |
| `Reduction.lean` | the chain model, `sChain`, `kChain`, Prop. 2.1 |
| `Concentration.lean` | Theorem 2.1 for any Lipschitz constant: second moment, `O_P`, mean |
| `MeanField.lean` | `g'`, `q`, `D_c`, the Lambert form, contraction, Theorem 2.1 as stated |
| `Average.lean` | Appendix B: product formula, Jensen, `E[D_ℓ] ≤ d_ℓ` |
| `Numerics.lean` | the bracket for `D_c/W` at `f = 1/30` |
