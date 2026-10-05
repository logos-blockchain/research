import StochasticRecurrence.Reduction

/-!
# §2.3 Mean-field approximation and concentration (Theorem 2.1, Appendix B)

The binomial chain (`kChain`, Prop. 2.1)

  `D_{ℓ+1} = D_ℓ - h D_ℓ (f - 1 + k_ℓ/T)`,  `k_ℓ | D_ℓ ∼ Bin(T, p(D_ℓ))`,  `p(D) = 1 - φ(W/D)`

against the mean-field recursion `d_{ℓ+1} = g(d_ℓ)`, `g(D) = D - hD(f - φ(W/D))`,
`d_0 = D_0`.

The proof follows the paper, with explicit constants in place of `O(·)`:

* `traj_mem`, `mf_mem`: both stay in `I = [D_min, D_max]` (eqs. `eq:D_interval`, `eq:d_interval`);
* `step_eq_g`: `D_{ℓ+1} = g(D_ℓ) - h D_ℓ η_ℓ` (eq. `eq:D_with_eta`);
* `err_abs_le`: `|ε_ℓ| ≤ h D_max ∑_{r<ℓ} L_g^{ℓ-1-r} |η_r|` (eq. `eq:error_series`);
* `E_eta_sq_le`: `E[η_r²] ≤ 1/(4T)` (eq. `eq:eta_variance_bound`, via the tower property);
* `E_err_sq_le`: `E[ε_ℓ²] ≤ K/T` (eq. `eq:e_second_moment`);
* `concentration`: Chebyshev and a union bound over `ℓ ≤ L` (eq. `eq:main_concentration`),
  and `|m_ℓ - d_ℓ| ≤ √(K/T)` (eq. `eq:mean_estimate`).

The constant `K` depends on `f, h, D_0, L, L_g` but not on `T`. Contraction
(`L_g < 1`) is **not** needed for a fixed horizon: any Lipschitz constant of `g` on
`I` works (`concentration`). `L_g < 1` only improves the constant
(`concentration_contractive`). In `MeanField.lean` the paper's condition
`D_min > D_c` is shown to give such an `L_g < 1`.
-/

open Finset Filter Topology

namespace SRE

/-- The standing assumptions: `0 < f < 1`, `0 < h < 1/f` (eq. `eq:h_condition`), `W ≥ 0`. -/
structure Hyp (f h W : ℝ) : Prop where
  f_pos : 0 < f
  f_lt_one : f < 1
  h_pos : 0 < h
  hf_lt : h * f < 1
  W_nonneg : 0 ≤ W

/-- The mean-field map `g(D) = D - hD(f - φ(W/D))` (eq. `eq:g_def`). -/
noncomputable def g (f h W D : ℝ) : ℝ := D - h * D * (f - φ f (W / D))

/-- The mean-field recursion `d_0 = D₀`, `d_{ℓ+1} = g(d_ℓ)` (eq. `eq:mean_field_recursion`). -/
noncomputable def mf (f h W D₀ : ℝ) : ℕ → ℝ
  | 0 => D₀
  | n + 1 => g f h W (mf f h W D₀ n)

/-- A noise path of the binomial chain is valid if every `k_ℓ ≤ T`. -/
def Bdd (T : ℕ) (ks : ℕ → ℕ) : Prop := ∀ r, ks r ≤ T

/-- `g` is `Lg`-Lipschitz on `[a, b]`. -/
def LipOn (G : ℝ → ℝ) (a b Lg : ℝ) : Prop :=
  ∀ x y, a ≤ x → x ≤ b → a ≤ y → y ≤ b → |G x - G y| ≤ Lg * |x - y|

/-- The probability of an event under the binomial chain, over `L` steps from `D₀`. -/
noncomputable def kProb (f h : ℝ) (T : ℕ) (W : ℝ) (L : ℕ) (D₀ : ℝ) (P : (ℕ → ℕ) → Prop) : ℝ :=
  open Classical in kChain f h T W L D₀ (fun ks => if P ks then 1 else 0)

variable {f h W : ℝ} {T : ℕ}

/-! ### One step -/

theorem pEmpty_eq (D : ℝ) : pEmpty f W D = (1 - f) ^ (W / D) := by simp [pEmpty, φ]

theorem pEmpty_mem (H : Hyp f h W) {D : ℝ} (hD : 0 < D) :
    0 ≤ pEmpty f W D ∧ pEmpty f W D ≤ 1 := by
  rw [pEmpty_eq]
  have h1 : 0 ≤ 1 - f := by linarith [H.f_lt_one]
  exact ⟨Real.rpow_nonneg h1 _,
    Real.rpow_le_one h1 (by linarith [H.f_pos]) (div_nonneg H.W_nonneg hD.le)⟩

theorem step_eq (D : ℝ) (k : ℕ) : step f h T D k = D * (1 - h * (f - 1 + k / T)) := by
  unfold step; ring

/-- One step multiplies `D` by a factor in `[1 - hf, 1 + h(1-f)]` (eq. `eq:D_bounds_step`). -/
theorem step_bounds (H : Hyp f h W) (hT : 0 < T) {D : ℝ} (hD : 0 ≤ D) {k : ℕ} (hk : k ≤ T) :
    D * (1 - h * f) ≤ step f h T D k ∧ step f h T D k ≤ D * (1 + h * (1 - f)) := by
  rw [step_eq]
  have h0 : (0 : ℝ) ≤ k / T := by positivity
  have h1 : (k : ℝ) / T ≤ 1 := by
    rw [div_le_one (by exact_mod_cast hT)]; exact_mod_cast hk
  have := H.h_pos
  constructor <;> apply mul_le_mul_of_nonneg_left _ hD <;> nlinarith

theorem step_pos (H : Hyp f h W) (hT : 0 < T) {D : ℝ} (hD : 0 < D) {k : ℕ} (hk : k ≤ T) :
    0 < step f h T D k :=
  lt_of_lt_of_le (mul_pos hD (by linarith [H.hf_lt])) (step_bounds H hT hD.le hk).1

/-- `D_{ℓ+1} = g(D_ℓ) - h D_ℓ η_ℓ` with `η_ℓ = k_ℓ/T - p(D_ℓ)` (eq. `eq:D_with_eta`). -/
theorem step_eq_g (D : ℝ) (k : ℕ) :
    step f h T D k = g f h W D - h * D * (k / T - pEmpty f W D) := by
  unfold step g pEmpty; ring

theorem g_bounds (H : Hyp f h W) {D : ℝ} (hD : 0 < D) :
    D * (1 - h * f) ≤ g f h W D ∧ g f h W D ≤ D * (1 + h * (1 - f)) := by
  obtain ⟨p0, p1⟩ := pEmpty_mem H hD
  have : g f h W D = D * (1 - h * (f - 1 + pEmpty f W D)) := by unfold g pEmpty; ring
  rw [this]
  have := H.h_pos
  constructor <;> apply mul_le_mul_of_nonneg_left _ hD.le <;> nlinarith

/-! ### The chain expectation -/

theorem kChain_zero (L : ℕ) (D : ℝ) (F : (ℕ → ℕ) → ℝ) (hL : L = 0) :
    kChain f h T W L D F = F (fun _ => 0) := by subst hL; rfl

theorem kChain_succ (L : ℕ) (D : ℝ) (F : (ℕ → ℕ) → ℝ) :
    kChain f h T W (L + 1) D F
      = binExp T (pEmpty f W D) (fun k => kChain f h T W L (step f h T D k) (fun ks => F (scons k ks))) :=
  rfl

theorem E_const : ∀ (L : ℕ) (D c : ℝ), kChain f h T W L D (fun _ => c) = c := by
  intro L
  induction L with
  | zero => intro D c; rfl
  | succ L ih => intro D c; rw [kChain_succ]; simp only [ih]; exact binExp_const T _ c

theorem E_add : ∀ (L : ℕ) (D : ℝ) (F G : (ℕ → ℕ) → ℝ),
    kChain f h T W L D (fun ks => F ks + G ks) = kChain f h T W L D F + kChain f h T W L D G := by
  intro L
  induction L with
  | zero => intro D F G; rfl
  | succ L ih =>
    intro D F G
    simp only [kChain_succ, ih]
    exact binExp_add T _ _ _

theorem E_mul_const : ∀ (L : ℕ) (D : ℝ) (F : (ℕ → ℕ) → ℝ) (c : ℝ),
    kChain f h T W L D (fun ks => F ks * c) = kChain f h T W L D F * c := by
  intro L
  induction L with
  | zero => intro D F c; rfl
  | succ L ih =>
    intro D F c
    simp only [kChain_succ, ih]
    exact binExp_mul_const T _ c _

theorem E_sum {ι : Type*} (s : Finset ι) (L : ℕ) (D : ℝ) (F : ι → (ℕ → ℕ) → ℝ) :
    kChain f h T W L D (fun ks => ∑ i ∈ s, F i ks) = ∑ i ∈ s, kChain f h T W L D (F i) := by
  classical
  induction s using Finset.induction_on with
  | empty => simpa using E_const L D 0
  | insert a s ha ih =>
    simp only [sum_insert ha]
    rw [E_add, ih]

theorem bdd_scons {k : ℕ} (hk : k ≤ T) {ks : ℕ → ℕ} (h : Bdd T ks) : Bdd T (scons k ks) := by
  intro r; cases r with
  | zero => exact hk
  | succ r => exact h r

/-- Monotonicity: the chain only visits valid paths. -/
theorem E_mono (H : Hyp f h W) (hT : 0 < T) :
    ∀ (L : ℕ) (D : ℝ), 0 < D → ∀ (F G : (ℕ → ℕ) → ℝ), (∀ ks, Bdd T ks → F ks ≤ G ks) →
      kChain f h T W L D F ≤ kChain f h T W L D G := by
  intro L
  induction L with
  | zero => intro D _ F G hFG; exact hFG _ fun _ => Nat.zero_le _
  | succ L ih =>
    intro D hD F G hFG
    rw [kChain_succ, kChain_succ]
    obtain ⟨p0, p1⟩ := pEmpty_mem H hD
    exact binExp_mono p0 p1 fun k hk =>
      ih _ (step_pos H hT hD hk) _ _ fun ks hb => hFG _ (bdd_scons hk hb)

/-- `E[X]² ≤ E[X²]`. -/
theorem E_sq_le (H : Hyp f h W) (hT : 0 < T) (L : ℕ) {D : ℝ} (hD : 0 < D) (X : (ℕ → ℕ) → ℝ) :
    (kChain f h T W L D X) ^ 2 ≤ kChain f h T W L D (fun ks => X ks ^ 2) := by
  set m := kChain f h T W L D X
  have h0 : kChain f h T W L D (fun _ => 0) ≤ kChain f h T W L D (fun ks => (X ks - m) ^ 2) :=
    E_mono H hT L D hD _ _ fun ks _ => sq_nonneg _
  have : (fun ks => (X ks - m) ^ 2) = fun ks => (X ks ^ 2 + X ks * (-2 * m)) + m ^ 2 := by
    funext ks; ring
  rw [this, E_add, E_add, E_mul_const, E_const, E_const] at h0
  nlinarith

/-! ### Paths -/

/-- The trajectory of the binomial chain. -/
noncomputable abbrev Dtraj (f h : ℝ) (T : ℕ) (D₀ : ℝ) (ks : ℕ → ℕ) : ℕ → ℝ :=
  traj (step f h T) D₀ ks

/-- The noise `η_ℓ = k_ℓ/T - p(D_ℓ)` (eq. `eq:eta_def`). -/
noncomputable def eta (f h : ℝ) (T : ℕ) (W D₀ : ℝ) (ks : ℕ → ℕ) (ℓ : ℕ) : ℝ :=
  ks ℓ / T - pEmpty f W (Dtraj f h T D₀ ks ℓ)

/-- Eq. `eq:D_bounds_iterated`. -/
theorem traj_bounds (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) {ks : ℕ → ℕ}
    (hb : Bdd T ks) : ∀ ℓ, D₀ * (1 - h * f) ^ ℓ ≤ Dtraj f h T D₀ ks ℓ ∧
      Dtraj f h T D₀ ks ℓ ≤ D₀ * (1 + h * (1 - f)) ^ ℓ := by
  intro ℓ
  induction ℓ with
  | zero => simp [traj]
  | succ ℓ ih =>
    have hpos : 0 ≤ D₀ * (1 - h * f) ^ ℓ := mul_nonneg hD₀.le (pow_nonneg (by linarith [H.hf_lt]) _)
    obtain ⟨l, u⟩ := step_bounds H hT (W := W) (hpos.trans ih.1) (hb ℓ)
    simp only [traj, pow_succ, ← mul_assoc]
    have hf1 : 0 ≤ 1 - h * f := by linarith [H.hf_lt]
    have hf2 : 0 ≤ 1 + h * (1 - f) := by nlinarith [H.h_pos, H.f_lt_one]
    exact ⟨le_trans (mul_le_mul_of_nonneg_right ih.1 hf1) l,
      le_trans u (mul_le_mul_of_nonneg_right ih.2 hf2)⟩

theorem traj_pos (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) {ks : ℕ → ℕ}
    (hb : Bdd T ks) (ℓ : ℕ) : 0 < Dtraj f h T D₀ ks ℓ :=
  lt_of_lt_of_le (mul_pos hD₀ (pow_pos (by linarith [H.hf_lt]) _)) (traj_bounds H hT hD₀ hb ℓ).1

/-- Eq. `eq:d_interval`, iterated form. -/
theorem mf_bounds (H : Hyp f h W) {D₀ : ℝ} (hD₀ : 0 < D₀) :
    ∀ ℓ, D₀ * (1 - h * f) ^ ℓ ≤ mf f h W D₀ ℓ ∧ mf f h W D₀ ℓ ≤ D₀ * (1 + h * (1 - f)) ^ ℓ := by
  intro ℓ
  induction ℓ with
  | zero => simp [mf]
  | succ ℓ ih =>
    have hpos : 0 < D₀ * (1 - h * f) ^ ℓ := mul_pos hD₀ (pow_pos (by linarith [H.hf_lt]) _)
    obtain ⟨l, u⟩ := g_bounds H (lt_of_lt_of_le hpos ih.1)
    simp only [mf, pow_succ, ← mul_assoc]
    have hf1 : 0 ≤ 1 - h * f := by linarith [H.hf_lt]
    have hf2 : 0 ≤ 1 + h * (1 - f) := by nlinarith [H.h_pos, H.f_lt_one]
    exact ⟨le_trans (mul_le_mul_of_nonneg_right ih.1 hf1) l,
      le_trans u (mul_le_mul_of_nonneg_right ih.2 hf2)⟩

/-- `D_min = D₀(1 - hf)^L` (eq. `eq:Dmin_def`). -/
noncomputable def Dmin (f h D₀ : ℝ) (L : ℕ) : ℝ := D₀ * (1 - h * f) ^ L

/-- `D_max = D₀(1 + h(1-f))^L` (eq. `eq:Dmax_def`). -/
noncomputable def Dmax (f h D₀ : ℝ) (L : ℕ) : ℝ := D₀ * (1 + h * (1 - f)) ^ L

theorem Dmin_pos (H : Hyp f h W) {D₀ : ℝ} (hD₀ : 0 < D₀) (L : ℕ) : 0 < Dmin f h D₀ L :=
  mul_pos hD₀ (pow_pos (by linarith [H.hf_lt]) _)

theorem interval_of_bounds (H : Hyp f h W) {D₀ : ℝ} (hD₀ : 0 < D₀) {L ℓ : ℕ} (hℓ : ℓ ≤ L) {x : ℝ}
    (hx : D₀ * (1 - h * f) ^ ℓ ≤ x ∧ x ≤ D₀ * (1 + h * (1 - f)) ^ ℓ) :
    Dmin f h D₀ L ≤ x ∧ x ≤ Dmax f h D₀ L := by
  constructor
  · refine le_trans (mul_le_mul_of_nonneg_left ?_ hD₀.le) hx.1
    exact pow_le_pow_of_le_one (by linarith [H.hf_lt]) (by nlinarith [H.h_pos, H.f_pos]) hℓ
  · refine le_trans hx.2 (mul_le_mul_of_nonneg_left ?_ hD₀.le)
    exact pow_le_pow_right₀ (by nlinarith [H.h_pos, H.f_lt_one]) hℓ

/-- Eq. `eq:D_interval`. -/
theorem traj_mem (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) {ks : ℕ → ℕ}
    (hb : Bdd T ks) {L ℓ : ℕ} (hℓ : ℓ ≤ L) :
    Dmin f h D₀ L ≤ Dtraj f h T D₀ ks ℓ ∧ Dtraj f h T D₀ ks ℓ ≤ Dmax f h D₀ L :=
  interval_of_bounds H hD₀ hℓ (traj_bounds H hT hD₀ hb ℓ)

/-- Eq. `eq:d_interval`. -/
theorem mf_mem (H : Hyp f h W) {D₀ : ℝ} (hD₀ : 0 < D₀) {L ℓ : ℕ} (hℓ : ℓ ≤ L) :
    Dmin f h D₀ L ≤ mf f h W D₀ ℓ ∧ mf f h W D₀ ℓ ≤ Dmax f h D₀ L :=
  interval_of_bounds H hD₀ hℓ (mf_bounds H hD₀ ℓ)

/-! ### The noise -/

/-- **Tower property.** Averaging a function of `(D_ℓ, k_ℓ)` is averaging its
conditional expectation given `D_ℓ`, which is a binomial expectation. -/
theorem E_tower (Ψ : ℝ → ℕ → ℝ) : ∀ (L : ℕ) (D : ℝ) (ℓ : ℕ), ℓ < L →
    kChain f h T W L D (fun ks => Ψ (Dtraj f h T D ks ℓ) (ks ℓ))
      = kChain f h T W L D (fun ks =>
          binExp T (pEmpty f W (Dtraj f h T D ks ℓ)) (Ψ (Dtraj f h T D ks ℓ))) := by
  intro L
  induction L with
  | zero => intro D ℓ hℓ; omega
  | succ L ih =>
    intro D ℓ hℓ
    rw [kChain_succ, kChain_succ]
    cases ℓ with
    | zero =>
      simp only [traj, scons, E_const]
      exact (binExp_const T _ _).symm
    | succ ℓ =>
      simp only [traj_scons, scons]
      congr 1; funext k
      exact ih _ ℓ (by omega)

/-- **The noise variance** (eqs. `eq:eta_mean`–`eq:eta_variance_bound`):
`E[η_ℓ²] ≤ 1/(4T)` for `ℓ < L`. -/
theorem E_eta_sq_le (H : Hyp f h W) (hT : 0 < T) {L ℓ : ℕ} (hℓ : ℓ < L) {D₀ : ℝ} (hD₀ : 0 < D₀) :
    kChain f h T W L D₀ (fun ks => eta f h T W D₀ ks ℓ ^ 2) ≤ 1 / (4 * T) := by
  have := E_tower (f := f) (h := h) (T := T) (W := W)
    (fun x k => ((k : ℝ) / T - pEmpty f W x) ^ 2) L D₀ ℓ hℓ
  simp only [eta]
  rw [this, ← E_const (f := f) (h := h) (T := T) (W := W) L D₀ (1 / (4 * T))]
  refine E_mono H hT L D₀ hD₀ _ _ fun ks hb => ?_
  obtain ⟨p0, p1⟩ := pEmpty_mem H (traj_pos H hT hD₀ hb ℓ)
  exact binExp_var_le hT.ne' p0 p1

/-! ### The error -/

/-- The error recursion bound (eqs. `eq:error_recursion`–`eq:error_series`):
`|ε_ℓ| ≤ h D_max ∑_{r<ℓ} L_g^{ℓ-1-r} |η_r|`. -/
theorem err_abs_le (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) {L : ℕ} {Lg : ℝ}
    (hLg : 0 ≤ Lg) (hLip : LipOn (g f h W) (Dmin f h D₀ L) (Dmax f h D₀ L) Lg)
    {ks : ℕ → ℕ} (hb : Bdd T ks) : ∀ ℓ ≤ L,
      |Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ|
        ≤ h * Dmax f h D₀ L * ∑ r ∈ range ℓ, Lg ^ (ℓ - 1 - r) * |eta f h T W D₀ ks r| := by
  intro ℓ
  induction ℓ with
  | zero => intro _; simp [traj, mf]
  | succ ℓ ih =>
    intro hℓ
    have ih := ih (by omega)
    obtain ⟨tl, tu⟩ := traj_mem H hT hD₀ hb (L := L) (ℓ := ℓ) (by omega)
    obtain ⟨ml, mu⟩ := mf_mem H hD₀ (W := W) (L := L) (ℓ := ℓ) (by omega)
    have htpos : 0 < Dtraj f h T D₀ ks ℓ := traj_pos H hT hD₀ hb ℓ
    have hrec : Dtraj f h T D₀ ks (ℓ + 1) - mf f h W D₀ (ℓ + 1)
        = (g f h W (Dtraj f h T D₀ ks ℓ) - g f h W (mf f h W D₀ ℓ))
          - h * Dtraj f h T D₀ ks ℓ * eta f h T W D₀ ks ℓ := by
      simp only [traj, mf, eta]; rw [step_eq_g (W := W)]; ring
    have hlip := hLip _ _ tl tu ml mu
    have hη : |h * Dtraj f h T D₀ ks ℓ * eta f h T W D₀ ks ℓ|
        ≤ h * Dmax f h D₀ L * |eta f h T W D₀ ks ℓ| := by
      rw [abs_mul, abs_mul, abs_of_pos H.h_pos, abs_of_pos htpos]
      exact mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left tu H.h_pos.le) (abs_nonneg _)
    have hsplit : ∑ r ∈ range (ℓ + 1), Lg ^ (ℓ + 1 - 1 - r) * |eta f h T W D₀ ks r|
        = Lg * ∑ r ∈ range ℓ, Lg ^ (ℓ - 1 - r) * |eta f h T W D₀ ks r|
          + |eta f h T W D₀ ks ℓ| := by
      rw [sum_range_succ, mul_sum]
      congr 1
      · refine sum_congr rfl fun r hr => ?_
        have : ℓ + 1 - 1 - r = (ℓ - 1 - r) + 1 := by have := mem_range.mp hr; omega
        rw [this, pow_succ]; ring
      · simp
    rw [hrec, hsplit]
    calc _ ≤ |g f h W (Dtraj f h T D₀ ks ℓ) - g f h W (mf f h W D₀ ℓ)|
            + |h * Dtraj f h T D₀ ks ℓ * eta f h T W D₀ ks ℓ| := abs_sub _ _
      _ ≤ Lg * |Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ| + h * Dmax f h D₀ L * |eta f h T W D₀ ks ℓ| :=
          add_le_add hlip hη
      _ ≤ Lg * (h * Dmax f h D₀ L * ∑ r ∈ range ℓ, Lg ^ (ℓ - 1 - r) * |eta f h T W D₀ ks r|)
            + h * Dmax f h D₀ L * |eta f h T W D₀ ks ℓ| := by gcongr
      _ = _ := by ring

/-- The geometric constant `(h D_max)² ∑_{m<n} L_g^{2m}`. -/
noncomputable def geomC (f h D₀ : ℝ) (L : ℕ) (Lg : ℝ) (n : ℕ) : ℝ :=
  (h * Dmax f h D₀ L) ^ 2 * ∑ m ∈ range n, (Lg ^ 2) ^ m

/-- Cauchy–Schwarz (eqs. `eq:error_series2`–`eq:geometric_bound`):
`ε_ℓ² ≤ (h D_max)² (∑_{m<ℓ} L_g^{2m}) ∑_{r<ℓ} η_r²`. -/
theorem err_sq_le (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) {L : ℕ} {Lg : ℝ}
    (hLg : 0 ≤ Lg) (hLip : LipOn (g f h W) (Dmin f h D₀ L) (Dmax f h D₀ L) Lg)
    {ks : ℕ → ℕ} (hb : Bdd T ks) {ℓ : ℕ} (hℓ : ℓ ≤ L) :
    (Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ) ^ 2
      ≤ (∑ r ∈ range ℓ, eta f h T W D₀ ks r ^ 2) * geomC f h D₀ L Lg ℓ := by
  have h1 := err_abs_le H hT hD₀ hLg hLip hb ℓ hℓ
  rw [mul_sum] at h1
  have hcs := sum_mul_sq_le_sq_mul_sq (range ℓ) (fun r => h * Dmax f h D₀ L * Lg ^ (ℓ - 1 - r))
    (fun r => |eta f h T W D₀ ks r|)
  have hgeo : ∑ r ∈ range ℓ, (h * Dmax f h D₀ L * Lg ^ (ℓ - 1 - r)) ^ 2 = geomC f h D₀ L Lg ℓ := by
    unfold geomC
    simp_rw [mul_pow, ← mul_sum, pow_right_comm _ _ 2]
    congr 1
    exact sum_range_reflect (fun m => (Lg ^ 2) ^ m) ℓ
  rw [hgeo] at hcs
  simp only [sq_abs] at hcs
  rw [← sq_abs]
  calc |Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ| ^ 2
      ≤ (∑ r ∈ range ℓ, h * Dmax f h D₀ L * Lg ^ (ℓ - 1 - r) * |eta f h T W D₀ ks r|) ^ 2 := by
        gcongr; simpa only [mul_assoc] using h1
    _ ≤ _ := by rw [mul_comm (∑ r ∈ range ℓ, eta f h T W D₀ ks r ^ 2)]; exact hcs

theorem geomC_mono {f h D₀ : ℝ} {L : ℕ} {Lg : ℝ} {m n : ℕ} (hmn : m ≤ n) :
    geomC f h D₀ L Lg m ≤ geomC f h D₀ L Lg n := by
  unfold geomC
  gcongr

/-- The constant `K = (h D_max)² (∑_{m<L} L_g^{2m}) L / 4` of the second-moment bound.
It does not depend on `T`. -/
noncomputable def Kc (f h D₀ : ℝ) (L : ℕ) (Lg : ℝ) : ℝ := geomC f h D₀ L Lg L * L / 4

theorem Kc_nonneg (f h D₀ : ℝ) (L : ℕ) (Lg : ℝ) : 0 ≤ Kc f h D₀ L Lg := by
  unfold Kc geomC; positivity

/-- **Second moment** (eq. `eq:e_second_moment`): `E[ε_ℓ²] ≤ K/T` for `ℓ ≤ L`. -/
theorem E_err_sq_le (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) {L : ℕ} {Lg : ℝ}
    (hLg : 0 ≤ Lg) (hLip : LipOn (g f h W) (Dmin f h D₀ L) (Dmax f h D₀ L) Lg)
    {ℓ : ℕ} (hℓ : ℓ ≤ L) :
    kChain f h T W L D₀ (fun ks => (Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ) ^ 2)
      ≤ Kc f h D₀ L Lg / T := by
  calc _ ≤ kChain f h T W L D₀
        (fun ks => (∑ r ∈ range ℓ, eta f h T W D₀ ks r ^ 2) * geomC f h D₀ L Lg ℓ) :=
        E_mono H hT L D₀ hD₀ _ _ fun ks hb => err_sq_le H hT hD₀ hLg hLip hb hℓ
    _ = (∑ r ∈ range ℓ, kChain f h T W L D₀ (fun ks => eta f h T W D₀ ks r ^ 2))
          * geomC f h D₀ L Lg ℓ := by rw [E_mul_const, E_sum]
    _ ≤ (∑ r ∈ range ℓ, 1 / (4 * (T : ℝ))) * geomC f h D₀ L Lg L := by
        have hg0 : 0 ≤ geomC f h D₀ L Lg ℓ := by unfold geomC; positivity
        refine mul_le_mul (sum_le_sum fun r hr => E_eta_sq_le H hT ?_ hD₀) (geomC_mono hℓ) hg0
          (sum_nonneg fun _ _ => by positivity)
        have := mem_range.mp hr; omega
    _ ≤ Kc f h D₀ L Lg / T := by
        unfold Kc
        rw [sum_const, card_range, nsmul_eq_mul]
        have hg0 : 0 ≤ geomC f h D₀ L Lg L := by unfold geomC; positivity
        have hT' : (0 : ℝ) < T := by exact_mod_cast hT
        have hℓ' : (ℓ : ℝ) ≤ L := by exact_mod_cast hℓ
        rw [show (ℓ : ℝ) * (1 / (4 * T)) * geomC f h D₀ L Lg L
            = (ℓ * geomC f h D₀ L Lg L / 4) / T by field_simp]
        have := mul_le_mul_of_nonneg_right hℓ' hg0
        apply div_le_div_of_nonneg_right _ hT'.le
        linarith

/-! ### Theorem 2.1 -/

/-- **Theorem 2.1 (concentration), explicit form.** Assume `0 < f < 1`,
`0 < h < 1/f`, `W ≥ 0`, `D₀ > 0`, and let `L_g ≥ 0` be a Lipschitz constant of `g`
on `I = [D_min, D_max]`. Then for every `T ≥ 1`, with `K = Kc f h D₀ L L_g`
(independent of `T`):

1. `E[(D_ℓ - d_ℓ)²] ≤ K/T` for all `ℓ ≤ L`;
2. `P(sup_{ℓ≤L} |D_ℓ - d_ℓ| ≥ δ) ≤ (L+1) K / (T δ²)` for all `δ > 0`
   (Chebyshev and a union bound);
3. `|m_ℓ - d_ℓ| ≤ √(K/T)` for all `ℓ ≤ L`, where `m_ℓ = E[D_ℓ]`. -/
theorem concentration (H : Hyp f h W) (hT : 0 < T) {D₀ : ℝ} (hD₀ : 0 < D₀) {L : ℕ} {Lg : ℝ}
    (hLg : 0 ≤ Lg) (hLip : LipOn (g f h W) (Dmin f h D₀ L) (Dmax f h D₀ L) Lg) :
    (∀ ℓ ≤ L, kChain f h T W L D₀ (fun ks => (Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ) ^ 2)
        ≤ Kc f h D₀ L Lg / T) ∧
    (∀ δ > 0, kProb f h T W L D₀ (fun ks => ∃ ℓ ≤ L, δ ≤ |Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ|)
        ≤ (L + 1) * Kc f h D₀ L Lg / (T * δ ^ 2)) ∧
    (∀ ℓ ≤ L, |kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ) - mf f h W D₀ ℓ|
        ≤ √(Kc f h D₀ L Lg / T)) := by
  have hT' : (0 : ℝ) < T := by exact_mod_cast hT
  refine ⟨fun ℓ hℓ => E_err_sq_le H hT hD₀ hLg hLip hℓ, fun δ hδ => ?_, fun ℓ hℓ => ?_⟩
  · -- Chebyshev + union bound
    classical
    unfold kProb
    calc _ ≤ kChain f h T W L D₀ (fun ks =>
            (∑ ℓ ∈ range (L + 1), (Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ) ^ 2) * (1 / δ ^ 2)) := by
          refine E_mono H hT L D₀ hD₀ _ _ fun ks _ => ?_
          split_ifs with hE
          · obtain ⟨ℓ, hℓ, hδℓ⟩ := hE
            have h1 : 1 ≤ (Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ) ^ 2 * (1 / δ ^ 2) := by
              rw [mul_one_div, le_div_iff₀ (by positivity), one_mul]
              calc δ ^ 2 ≤ |Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ| ^ 2 := pow_le_pow_left₀ hδ.le hδℓ 2
                _ = _ := sq_abs _
            refine h1.trans (mul_le_mul_of_nonneg_right ?_ (by positivity))
            exact single_le_sum (f := fun ℓ => (Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ) ^ 2)
              (fun _ _ => sq_nonneg _) (mem_range.mpr (by omega))
          · positivity
      _ = (∑ ℓ ∈ range (L + 1), kChain f h T W L D₀
            (fun ks => (Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ) ^ 2)) * (1 / δ ^ 2) := by
          rw [E_mul_const, E_sum]
      _ ≤ (∑ _ℓ ∈ range (L + 1), Kc f h D₀ L Lg / T) * (1 / δ ^ 2) := by
          gcongr with ℓ hℓ
          exact E_err_sq_le H hT hD₀ hLg hLip (by have := mem_range.mp hℓ; omega)
      _ = _ := by
          rw [sum_const, card_range, nsmul_eq_mul]; push_cast; field_simp
  · -- the mean
    have hm : kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ) - mf f h W D₀ ℓ
        = kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ) := by
      rw [show (fun ks => Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ)
          = fun ks => Dtraj f h T D₀ ks ℓ + (-mf f h W D₀ ℓ) from by funext; ring,
        E_add, E_const]; ring
    rw [hm]
    apply Real.abs_le_sqrt
    exact (E_sq_le H hT L hD₀ _).trans (E_err_sq_le H hT hD₀ hLg hLip hℓ)

/-- **Theorem 2.1, `O_P` form** (eq. `eq:main_concentration`):
`sup_{ℓ≤L} |D_ℓ - d_ℓ| = O_P(T^{-1/2})`. For every `ε > 0` there is `M` such that,
for every `T ≥ 1`, `P(sup_{ℓ≤L} |D_ℓ - d_ℓ| ≥ M/√T) ≤ ε`. -/
theorem concentration_OP (H : Hyp f h W) {D₀ : ℝ} (hD₀ : 0 < D₀) {L : ℕ} {Lg : ℝ}
    (hLg : 0 ≤ Lg) (hLip : LipOn (g f h W) (Dmin f h D₀ L) (Dmax f h D₀ L) Lg) :
    ∀ ε > 0, ∃ M > 0, ∀ T : ℕ, 0 < T →
      kProb f h T W L D₀ (fun ks => ∃ ℓ ≤ L, M / √T ≤ |Dtraj f h T D₀ ks ℓ - mf f h W D₀ ℓ|)
        ≤ ε := by
  intro ε hε
  set K := Kc f h D₀ L Lg
  have hK := Kc_nonneg f h D₀ L Lg
  refine ⟨√(((L + 1) * K + 1) / ε), Real.sqrt_pos.mpr (by positivity), fun T hT => ?_⟩
  have hT' : (0 : ℝ) < T := by exact_mod_cast hT
  refine ((concentration H hT hD₀ hLg hLip).2.1 _ (by positivity)).trans ?_
  rw [div_pow, Real.sq_sqrt (by positivity), Real.sq_sqrt hT'.le,
    mul_div_cancel₀ _ hT'.ne', div_div_eq_mul_div, div_le_iff₀ (by positivity)]
  nlinarith

/-- **Theorem 2.1, the mean** (eq. `eq:mean_estimate`): `m_ℓ → d_ℓ` as `T → ∞`. This
is the rigorous form of the saddle-point mean-field equation (eq. `eq:MF`): the
mean of the stochastic recurrence follows the mean-field recursion in the limit. -/
theorem mean_tendsto (H : Hyp f h W) {D₀ : ℝ} (hD₀ : 0 < D₀) {L : ℕ} {Lg : ℝ}
    (hLg : 0 ≤ Lg) (hLip : LipOn (g f h W) (Dmin f h D₀ L) (Dmax f h D₀ L) Lg)
    {ℓ : ℕ} (hℓ : ℓ ≤ L) :
    Tendsto (fun T : ℕ => kChain f h T W L D₀ (fun ks => Dtraj f h T D₀ ks ℓ)) atTop
      (𝓝 (mf f h W D₀ ℓ)) := by
  rw [tendsto_iff_norm_sub_tendsto_zero]
  have h0 : Tendsto (fun T : ℕ => √(Kc f h D₀ L Lg / T)) atTop (𝓝 0) := by
    have := (tendsto_const_div_atTop_nhds_zero_nat (Kc f h D₀ L Lg)).sqrt
    simpa using this
  refine squeeze_zero' (Eventually.of_forall fun _ => norm_nonneg _) ?_ h0
  filter_upwards [eventually_gt_atTop 0] with T hT
  exact (concentration H hT hD₀ hLg hLip).2.2 ℓ hℓ

/-- With a contraction `L_g < 1` (eq. `eq:Lg_less_1`, Appendix B) the constant is
bounded by the paper's `h² D_max² / (1 - L_g²) · L / 4`. -/
theorem Kc_le_contractive {f h D₀ : ℝ} {L : ℕ} {Lg : ℝ} (hLg0 : 0 ≤ Lg) (hLg1 : Lg < 1) :
    Kc f h D₀ L Lg ≤ (h * Dmax f h D₀ L) ^ 2 / (1 - Lg ^ 2) * L / 4 := by
  unfold Kc geomC
  have hq : Lg ^ 2 < 1 := by nlinarith
  have hq0 : 0 ≤ Lg ^ 2 := sq_nonneg _
  have hgeo : ∑ m ∈ range L, (Lg ^ 2) ^ m ≤ 1 / (1 - Lg ^ 2) := by
    rw [geom_sum_eq hq.ne, le_div_iff₀ (by linarith)]
    rw [div_mul_eq_mul_div, div_le_one_of_neg (by linarith)] <;> [skip]
    · nlinarith [pow_nonneg hq0 L]
  have : (h * Dmax f h D₀ L) ^ 2 * ∑ m ∈ range L, (Lg ^ 2) ^ m
      ≤ (h * Dmax f h D₀ L) ^ 2 / (1 - Lg ^ 2) := by
    rw [div_eq_mul_one_div]; gcongr
  gcongr

end SRE
