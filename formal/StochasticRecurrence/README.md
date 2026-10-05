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
| §2, `1 - P(0|D) = φ(W/D)` | `prod_one_sub_φ` | `∏ (1 - φ(w_i/D)) = 1 - φ(∑ w_i / D)` |
| §2, logistic form | `bern_logistic` | `P(s|D) = e^{s η}/(1 + e^η)` |
| **Prop. 2.1** | **`binomial_reduction`** | For every `L`, `D₀` and test function `Φ` of `(D_0, …, D_L)`, `sChain` and `kChain` give the same expectation |
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
| eqs. `eq:contractive_region`, `eq:Lg_less_1` | `contraction` | `D_c < a` ⟹ `g` is `g'(a)`-Lipschitz on `[a, b]`, with `0 < g'(a) < 1` |
| **Thm. 2.1 as stated** | **`theorem_2_1`** | under `hf < 1` and `D_min > D_c`: all three bounds with `K = h²D_max²/(1-L_g²) · L/4` |
| App. A, product formula | `traj_prod` | `D_ℓ = D_0 ∏_{r<ℓ}(1 - h(f - 1 + k_r/T))` |
| App. A, convexity | `tangent_le`, `jensen` | `⟨D(1-φ(W/D))⟩ ≥ ⟨D⟩(1 - φ(W/⟨D⟩))` |
| (new) | `E_step_le_g`, `mean_le_mf` | `E[D_{ℓ+1}] ≤ g(E[D_ℓ])`, and so `E[D_ℓ] ≤ d_ℓ` for **every** `T` |
| eq. `eq:Dc_numerical` | `Dc_ratio` | at `f = 1/30`: `0.119 < D_c/W < 0.1205` |
| App. B | `concentration`, `Kc_le_contractive` | same proof, with `L_g < 1` as a hypothesis |

## Differences from the paper

1. **Contraction is not needed for Theorem 2.1.** For a fixed horizon `L`, `concentration` holds for *any* Lipschitz constant `L_g` of `g` on `[D_min, D_max]`. Such a constant always exists, because `g` is C¹ there. The constant `K` uses `∑_{m<L} L_g^{2m}` in place of `1/(1 - L_g²)`. The condition `D_min > D_c` only improves `K`, and it matters only for bounds that are uniform in `L`. Since `D_max` grows geometrically in `L`, the paper's bound is not uniform in `L` either way.
2. **`D_c/W` at `f = 1/30` is about 0.1196, not 0.121.** `Dc_ratio` proves `0.119 < D_c/W < 0.1205`. The conclusion it supports still holds.
3. **The saddle-point equation (eq. `eq:MF`) is not an identity at finite `T`.** It is the limit `mean_tendsto`. At finite `T` it is an inequality: `E[D_{ℓ+1}] ≤ g(E[D_ℓ])` (`E_step_le_g`). This follows from the convexity remark in Appendix A, and gives `E[D_ℓ] ≤ d_ℓ` (`mean_le_mf`).
4. **Prop. 2.1 is proved by counting, not by Fourier representations of `δ`.** The statement is an identity of finite sums for every test function of the trajectory. The proof is the core of the paper's computation: `[P(0) + (1-P(0))e^{…}]^T` expands binomially (`sum_pi_count`).

## Not formalized

- The saddle-point derivation itself (§2.2): Fourier integrals of `δ` and a `T → ∞` Laplace argument. It is replaced by its rigorous counterpart, `mean_tendsto` together with `E_step_le_g`.
- The asymptotic `D_c/W ∼ √(f/2)` as `f → 0` (eq. `eq:Dc_asymptotic`). It is correct numerically: the ratio to `√(f/2)` is 0.957, 0.986 and 0.995 at `f = 10⁻², 10⁻³, 10⁻⁴`.

## Layout

| File | Contents |
|---|---|
| `Lottery.lean` | §1: `φ`, independent Bernoulli expectations, leader mean and variance, empty-slot probability |
| `Binomial.lean` | binomial expectation, Pascal's rule, counting i.i.d. coordinates, mean and variance |
| `Reduction.lean` | the chain model, `sChain`, `kChain`, Prop. 2.1 |
| `Concentration.lean` | Theorem 2.1 for any Lipschitz constant: second moment, `O_P`, mean |
| `MeanField.lean` | `g'`, `q`, `D_c`, the Lambert form, contraction, Theorem 2.1 as stated |
| `Average.lean` | Appendix A: product formula, Jensen, `E[D_ℓ] ≤ d_ℓ` |
| `Numerics.lean` | the bracket for `D_c/W` at `f = 1/30` |
