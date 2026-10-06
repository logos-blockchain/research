import StochasticRecurrence.Binomial

/-!
# §2 The stochastic recurrence and its binomial reduction (Proposition 2.1)

The recurrence (eq. `eq:SRE`) is a Markov chain on the estimate `D`. At step `ℓ`
the leader configuration `S(ℓ) = (s^ℓ(1), …, s^ℓ(T))`, `s^ℓ(t) ∈ {0,1}^N`, is drawn
given `D_ℓ` with independent entries `s^ℓ_i(t) ∼ Bernoulli(φ(w_i/D_ℓ))`
(eq. `def:Prob-S`), and

  `D_{ℓ+1} = D_ℓ - h D_ℓ (f - (1/T) ∑_t 1[∑_i s^ℓ_i(t) ≥ 1])`.

**Model of the path law.** `chainE κ next x₀ L D₀ F` is the expectation of a
function `F` of the noise sequence over the first `L` steps, started at `D₀`, where
the noise of each step is drawn by the kernel `κ D` (given as an expectation
operator) and the state moves by `next`. This is the path measure
(eq. `def:prob-path`) written as iterated sums; coordinates after `L` are set to
`x₀`, so `F` should only depend on the first `L` of them. The law of the
trajectory `(D_0, …, D_L)` is `Φ ↦ chainE … (fun xs => Φ (D_0, …, D_L))`, which is
the paper's `P[D_L, …, D_1 | D_0]` (eq. `def:prob-path-D`) tested against `Φ`.

**Proposition (Binomial reduction)**, `prop:D-distr`. Given `D_ℓ`, the step is
determined by the number of empty slots `k_ℓ`:

* `empty_slot_prob`: a slot is empty with probability `1 - φ(W/D)`, `W = ∑ w_i`
  (eq. `eq:empty_probability`);
* `nEmpty_pmf`: `k_ℓ | D_ℓ ∼ Bin(T, 1 - φ(W/D_ℓ))` (eq. `eq:k_distribution_prop`),
  via `sum_pi_count`: the slots are independent given `D_ℓ`;
* `nonempty_count`: the number of non-empty slots is `T - k_ℓ` (eq. `eq:nonempty_count`);
* `stepS_eq`: hence `D_{ℓ+1} = D_ℓ - h D_ℓ (f - 1 + k_ℓ/T)` (eq. `eq:SRE_binomial`).

`binomial_reduction_step` states these together, as the proposition does. The
proposition's "consequently, eq. `eq:SRE` is exactly equivalent" is
`binomial_reduction`: the trajectory laws of the two chains agree over any horizon.
The paper's earlier proof through Fourier representations of `δ` (now its appendix)
is not formalized; the counting proof here is the one in the main text.
-/

open Finset

namespace SRE

/-- Prepend `x` to the sequence `xs`. -/
def scons {X : Type*} (x : X) (xs : ℕ → X) (n : ℕ) : X :=
  match n with
  | 0 => x
  | n + 1 => xs n

/-- The trajectory `D_0 = D₀, D_{n+1} = next D_n x_n` driven by the noise `xs`. -/
def traj {X : Type*} (next : (D : ℝ) → (x : X) → ℝ) (D₀ : ℝ) (xs : ℕ → X) (ℓ : ℕ) : ℝ :=
  match ℓ with
  | 0 => D₀
  | ℓ + 1 => next (traj next D₀ xs ℓ) (xs ℓ)

theorem traj_scons {X : Type*} (next : ℝ → X → ℝ) (D₀ : ℝ) (x : X) (xs : ℕ → X) (n : ℕ) :
    traj next D₀ (scons x xs) (n + 1) = traj next (next D₀ x) xs n := by
  induction n with
  | zero => rfl
  | succ n ih => simp only [traj] at ih ⊢; rw [ih]; rfl

theorem traj_scons_fin {X : Type*} (next : ℝ → X → ℝ) (D₀ : ℝ) (x : X) (xs : ℕ → X) (L : ℕ) :
    (fun i : Fin (L + 2) => traj next D₀ (scons x xs) i)
      = Fin.cons D₀ (fun j : Fin (L + 1) => traj next (next D₀ x) xs j) := by
  funext i
  refine Fin.cases ?_ (fun j => ?_) i
  · rfl
  · simp only [Fin.cons_succ, Fin.val_succ]
    exact traj_scons next D₀ x xs j

/-- The expectation of `F` over the first `L` steps of the chain (see the module doc). -/
noncomputable def chainE {X : Type*} (κ : (D : ℝ) → (G : X → ℝ) → ℝ)
    (next : (D : ℝ) → (x : X) → ℝ) (x₀ : X) (L : ℕ) (D : ℝ) (F : (ℕ → X) → ℝ) : ℝ :=
  match L with
  | 0 => F (fun _ => x₀)
  | L + 1 => κ D (fun x => chainE κ next x₀ L (next D x) (fun xs => F (scons x xs)))

section Model

variable (f h : ℝ) (T : ℕ)

/-- The binomial form of one step: `D - hD(f - 1 + k/T)`. -/
noncomputable def step (D : ℝ) (k : ℕ) : ℝ := D - h * D * (f - 1 + k / T)

/-- The probability that a slot is empty, `1 - φ(W/D)`. -/
noncomputable def pEmpty (W D : ℝ) : ℝ := 1 - φ f (W / D)

/-- **The binomial chain** (the right-hand side of Prop. 2.1).

At each step the number of empty slots is drawn given the current estimate,
`k_ℓ | D_ℓ ∼ Bin(T, 1 - φ(W/D_ℓ))`, and the estimate moves by
`D_{ℓ+1} = D_ℓ - h D_ℓ (f - 1 + k_ℓ/T)` (`step`).

`kChain f h T W L D₀ F` is the expectation of `F` over the first `L` steps, started
at `D₀`:
* `W` is the total stake `∑ w_i`; only the total matters for this chain;
* `L : ℕ` is the horizon (number of steps);
* `D₀ : ℝ` is the initial estimate;
* `F : (ℕ → ℕ) → ℝ` is a function of the noise path `ks`, where `ks ℓ = k_ℓ`.
  Entries after `L` are set to `0`, so `F` should only look at `ks 0, …, ks (L-1)`.

To get a function of the estimates, compose with the trajectory: `F ks` is
typically `Φ (fun i => traj (step f h T) D₀ ks i)`, so `D_ℓ = traj … ks ℓ`. -/
noncomputable def kChain (W : ℝ) (L : ℕ) (D₀ : ℝ) (F : (ℕ → ℕ) → ℝ) : ℝ :=
  chainE (fun D G => binExp T (pEmpty f W D) G) (step f h T) 0 L D₀ F

variable {N : ℕ}

/-- `P(S | D) = ∏_t ∏_i P(s_i(t) | D)` (eq. `def:Prob-S`). -/
noncomputable def probS (w : Fin N → ℝ) (D : ℝ) (S : Fin T → Fin N → Bool) : ℝ :=
  ∏ t, ∏ i, bern (φ f (w i / D)) (S t i)

/-- One step of the recurrence (eq. `eq:SRE`), driven by the leader configuration `S`. -/
noncomputable def stepS (D : ℝ) (S : Fin T → Fin N → Bool) : ℝ :=
  D - h * D * (f - (1 / T) * ∑ t, (if ∃ i, S t i then 1 else 0))

/-- **The chain of eq. `eq:SRE`** (the left-hand side of Prop. 2.1), driven by the
full leader configurations.

At each step a configuration `S : Fin T → Fin N → Bool` is drawn given the current
estimate: `S t i` says whether node `i` is a leader in slot `t`, and the entries are
independent with `P(S t i = true) = φ(w_i/D_ℓ)` (`probS`). The estimate then moves by
`D_{ℓ+1} = D_ℓ - h D_ℓ (f - (1/T) ∑_t 1[slot t has a leader])` (`stepS`).

`sChain f h T w L D₀ F` is the expectation of `F` over the first `L` steps, started
at `D₀`:
* `w : Fin N → ℝ` gives the stakes, `w i` being node `i`'s stake;
* `L : ℕ` is the horizon (number of steps);
* `D₀ : ℝ` is the initial estimate;
* `F : (ℕ → (Fin T → Fin N → Bool)) → ℝ` is a function of the path of configurations
  `Ss`, where `Ss ℓ = S(ℓ)`. Entries after `L` are set to the all-`false`
  configuration, so `F` should only look at `Ss 0, …, Ss (L-1)`.

`binomial_reduction` shows that functions of the estimates `D_0, …, D_L` have the
same expectation under `sChain f h T w` and `kChain f h T (∑ i, w i)`. -/
noncomputable def sChain (w : Fin N → ℝ) (L : ℕ) (D₀ : ℝ)
    (F : (ℕ → (Fin T → Fin N → Bool)) → ℝ) : ℝ :=
  chainE (fun D G => ∑ S, probS f T w D S * G S) (stepS f h T) (fun _ _ => false) L D₀ F

/-- The number of empty slots. -/
def nEmpty (S : Fin T → Fin N → Bool) : ℕ := #{t | ∀ i, S t i = false}

variable {f h T}

/-- **The number of non-empty slots** is `T - k` (eq. `eq:nonempty_count`). -/
theorem nonempty_count (S : Fin T → Fin N → Bool) :
    ∑ t, (if ∃ i, S t i then (1 : ℝ) else 0) = T - nEmpty T S := by
  unfold nEmpty
  have hc := card_filter_add_card_filter_not (s := (univ : Finset (Fin T)))
    (fun t => ∀ i, S t i = false)
  simp only [card_univ, Fintype.card_fin] at hc
  have hs : ∑ t, (if ∃ i, S t i then (1 : ℝ) else 0)
      = #{t | ¬ ∀ i, S t i = false} := by
    rw [sum_boole]; congr 2; ext t; simp
  have hc' : (#{t | ∀ i, S t i = false} : ℝ) + #{t | ¬ ∀ i, S t i = false} = T := by
    exact_mod_cast hc
  rw [hs]; linarith

/-- `D_{ℓ+1}[S]` depends on `S` only through the number of empty slots
(eq. `eq:binomial_recurrence`). -/
theorem stepS_eq (hT : 0 < T) (D : ℝ) (S : Fin T → Fin N → Bool) :
    stepS f h T D S = step f h T D (nEmpty T S) := by
  unfold stepS step
  rw [nonempty_count]
  have hT' : (T : ℝ) ≠ 0 := by positivity
  field_simp; ring

/-- **The empty-slot probability** (eq. `eq:empty_probability`): a single slot
`s ∈ {0,1}^N`, with independent `s_i ∼ Bernoulli(φ(w_i/D))`, is empty with
probability `∏ (1 - φ(w_i/D)) = 1 - φ(W/D)`. -/
theorem empty_slot_prob (hf : f < 1) (w : Fin N → ℝ) (D : ℝ) :
    ∑ s : Fin N → Bool, (∏ i, bern (φ f (w i / D)) (s i)) * (if ∀ i, s i = false then 1 else 0)
      = pEmpty f (∑ i, w i) D := by
  rw [pEmpty, ← prod_one_sub_φ hf, ← bexp_empty]
  exact sum_congr rfl fun s _ => by congr

/-- **One step of the reduction.** Under `P(S | D)`, the number of empty slots is
`Bin(T, 1 - φ(W/D))`. -/
theorem sum_probS_nEmpty (hf : f < 1) (w : Fin N → ℝ) (D : ℝ) (G : ℕ → ℝ) :
    ∑ S, probS f T w D S * G (nEmpty T S) = binExp T (pEmpty f (∑ i, w i) D) G := by
  have hμ : ∑ s : Fin N → Bool, ∏ i, bern (φ f (w i / D)) (s i) = 1 := by
    simpa [bexp] using bexp_one (fun i => φ f (w i / D))
  have h := sum_pi_count (fun s : Fin N → Bool => ∏ i, bern (φ f (w i / D)) (s i)) hμ
    (fun s => ∀ i, s i = false) T G
  have ha : ∑ s : Fin N → Bool with ∀ i, s i = false, ∏ i, bern (φ f (w i / D)) (s i)
      = pEmpty f (∑ i, w i) D := by
    rw [sum_filter, pEmpty, ← prod_one_sub_φ hf, ← bexp_empty]
    simp [bexp]
  rw [ha] at h
  exact h

/-- **The law of the number of empty slots** (eq. `eq:k_distribution_prop`):
`P[k = j | D] = C(T,j) (1 - φ(W/D))^j φ(W/D)^{T-j}` for `j ≤ T`. -/
theorem nEmpty_pmf (hf : f < 1) (w : Fin N → ℝ) (D : ℝ) {j : ℕ} (hj : j ≤ T) :
    ∑ S, probS f T w D S * (if nEmpty T S = j then 1 else 0)
      = T.choose j * (1 - φ f ((∑ i, w i) / D)) ^ j * φ f ((∑ i, w i) / D) ^ (T - j) := by
  rw [sum_probS_nEmpty hf w D (fun k => if k = j then 1 else 0)]
  unfold binExp binW pEmpty
  simp only [mul_ite, mul_one, mul_zero, sum_ite_eq', mem_range,
    show j < T + 1 by omega, ↓reduceIte, sub_sub_cancel]

/-- **Proposition (Binomial reduction)** (`prop:D-distr`), as stated in the paper.
Given `D`, the number of empty slots `k` is `Bin(T, 1 - φ(W/D))`, and the step of
eq. `eq:SRE` is `D - hD(f - 1 + k/T)`. -/
theorem binomial_reduction_step (hf : f < 1) (hT : 0 < T) (w : Fin N → ℝ) (D : ℝ) :
    (∀ j ≤ T, ∑ S, probS f T w D S * (if nEmpty T S = j then 1 else 0)
        = T.choose j * (1 - φ f ((∑ i, w i) / D)) ^ j * φ f ((∑ i, w i) / D) ^ (T - j)) ∧
    (∀ S : Fin T → Fin N → Bool, stepS f h T D S = D - h * D * (f - 1 + nEmpty T S / T)) :=
  ⟨fun _ hj => nEmpty_pmf hf w D hj, fun S => stepS_eq hT D S⟩

/-- **Binomial reduction for the whole trajectory** (the proposition's
"consequently, eq. `eq:SRE` is exactly equivalent to eq. `eq:SRE_binomial`"). For every horizon `L`, initial value
`D₀` and test function `Φ` of the trajectory `(D_0, …, D_L)`, the chain of
eq. `eq:SRE` and the binomial chain give the same expectation:
`P[D_L, …, D_1 | D_0]` is the same for both. -/
theorem binomial_reduction (hf : f < 1) (hT : 0 < T) (w : Fin N → ℝ) :
    ∀ (L : ℕ) (D₀ : ℝ) (Φ : (Fin (L + 1) → ℝ) → ℝ),
      sChain f h T w L D₀ (fun Ss => Φ (fun i => traj (stepS f h T) D₀ Ss i))
        = kChain f h T (∑ i, w i) L D₀ (fun ks => Φ (fun i => traj (step f h T) D₀ ks i)) := by
  intro L
  induction L with
  | zero =>
    intro D₀ Φ
    have h1 : ∀ {X : Type} (next : ℝ → X → ℝ) (xs : ℕ → X),
        (fun i : Fin 1 => traj next D₀ xs i) = fun _ => D₀ := by
      intro X next xs; funext i; rw [Fin.fin_one_eq_zero i]; rfl
    simp only [sChain, kChain, chainE, h1]
  | succ L ih =>
    intro D₀ Φ
    simp only [sChain, kChain, chainE] at ih ⊢
    simp_rw [traj_scons_fin]
    have : ∀ S : Fin T → Fin N → Bool,
        chainE (fun D G => ∑ S, probS f T w D S * G S) (stepS f h T) (fun _ _ => false) L
          (stepS f h T D₀ S)
          (fun Ss => Φ (Fin.cons D₀ fun j : Fin (L + 1) => traj (stepS f h T) (stepS f h T D₀ S) Ss j))
        = (fun k => chainE (fun D G => binExp T (pEmpty f (∑ i, w i) D) G) (step f h T) 0 L
            (step f h T D₀ k)
            (fun ks => Φ (Fin.cons D₀ fun j : Fin (L + 1) => traj (step f h T) (step f h T D₀ k) ks j)))
          (nEmpty T S) := by
      intro S
      rw [ih (stepS f h T D₀ S) (fun ψ => Φ (Fin.cons D₀ ψ)), stepS_eq hT]
    simp_rw [this]
    exact sum_probS_nEmpty hf w D₀ (fun k =>
      chainE (fun D G => binExp T (pEmpty f (∑ i, w i) D) G) (step f h T) 0 L (step f h T D₀ k)
        fun ks => Φ (Fin.cons D₀ fun j : Fin (L + 1) => traj (step f h T) (step f h T D₀ k) ks j))

end Model

end SRE
