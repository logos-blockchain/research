import Cryptarchia.Prob.RO

/-!
# The band condition from stake fractions and the stake estimate

`SlotBand` (`Prob/RO.lean`) is a condition on each epoch state a slot's lottery
runs under. This file derives it from:

* **stake fractions**: the adversary holds at most a fraction `β` of the
  participating stake (online honest nodes' notes plus the adversary's notes);
* **the stake estimate** (TSI): `λ·V/D` is in `[ℓlo, ℓhi]` for some visible stake
  `V` between `(1-μ)` times the honest stake plus `(1-w)` times the adversary's
  stake (honest wins missed by uncles, adversarial stake withheld) and the total;
* the spec's lottery constants (`t0Const/p = λ`, `t1Const/p = λ²/2`) and stake
  amounts far below the field size.

**The lottery.** A note with relative stake `x = v/D` wins with probability
`w = threshold/p ≈ y - y²/2`, `y = λx`: the second-order expansion of
`1 - e^{-y}`. The per-note error is cubic (`note_lose_lo`, `note_lose_hi`),
so a list of notes with total exponent `Y = λ·S/D` all lose with probability
within `e^{-Y}·(1 ± O(Y³ + rounding))` (`loss_lo`, `loss_hi`), however the stake
is split. Exactly one honest node wins with probability at least `-P₀ ln P₀`,
the Poisson value (`pOne_ge`).
-/

namespace Cryptarchia.Prob

open Real

/-! ## Analytic facts -/

theorem exp_neg_le_quad' {t : ℝ} (ht : 0 ≤ t) : exp (-t) ≤ 1 - t + t ^ 2 / 2 := by
  have h1 := Real.quadratic_le_exp_of_nonneg ht
  have hpos : 0 < 1 + t + t ^ 2 / 2 := by positivity
  have h2 : exp (-t) = 1 / exp t := by rw [Real.exp_neg, one_div]
  rw [h2, div_le_iff₀ (Real.exp_pos t)]
  have h3 : 1 ≤ (1 - t + t ^ 2 / 2) * (1 + t + t ^ 2 / 2) := by nlinarith [sq_nonneg (t ^ 2)]
  have h4 : 0 ≤ 1 - t + t ^ 2 / 2 := by nlinarith [sq_nonneg (t - 1)]
  nlinarith [mul_le_mul_of_nonneg_left h1 h4]

/-- `1 - t + t²/2 ≤ e^{-t} + (2/9) t³` for `0 ≤ t ≤ 1`. -/
theorem quad_le_exp_neg {t : ℝ} (h0 : 0 ≤ t) (h1 : t ≤ 1) : 1 - t + t ^ 2 / 2 ≤ exp (-t) + 2 / 9 * t ^ 3 := by
  have hb := Real.exp_bound (x := -t) (by rw [abs_neg, abs_of_nonneg h0]; exact h1) (n := 3) (by norm_num)
  simp only [Finset.sum_range_succ, Finset.sum_range_zero, Nat.factorial, Nat.cast_ofNat,
    pow_zero, pow_one, abs_neg, abs_of_nonneg h0] at hb
  have := (abs_le.1 hb).1
  norm_num at this
  nlinarith [this]

/-- `e^{-t} ≥ 1 - t + t²/2 - (2/9) t³` for `0 ≤ t ≤ 1`. -/
theorem exp_neg_ge_cubic {t : ℝ} (h0 : 0 ≤ t) (h1 : t ≤ 1) : 1 - t + t ^ 2 / 2 - 2 / 9 * t ^ 3 ≤ exp (-t) := by
  linarith [quad_le_exp_neg h0 h1]

/-- `e^x ≤ 1 + 2x` for `0 ≤ x ≤ 1`. -/
theorem exp_le_one_add_two {x : ℝ} (h0 : 0 ≤ x) (h1 : x ≤ 1) : exp x ≤ 1 + 2 * x := by
  have hb := Real.exp_bound (x := x) (by rw [abs_of_nonneg h0]; exact h1) (n := 2) (by norm_num)
  simp only [Finset.sum_range_succ, Finset.sum_range_zero, Nat.factorial, Nat.cast_ofNat,
    pow_zero, pow_one, abs_of_nonneg h0] at hb
  have := (abs_le.1 hb).2
  norm_num at this
  nlinarith [this]

theorem exp_half_le_two : exp (1 / 2) ≤ 2 := by
  have := exp_le_one_add_two (x := 1 / 2) (by norm_num) (by norm_num)
  linarith

/-- `∏ (1 - uᵢ) ≥ 1 - ∑ uᵢ` for `uᵢ ∈ [0, 1]`. -/
theorem prod_one_sub_ge {ι : Type*} (L : List ι) (u : ι → ℝ) (h0 : ∀ i ∈ L, 0 ≤ u i) (h1 : ∀ i ∈ L, u i ≤ 1) :
    1 - (L.map u).sum ≤ (L.map fun i => 1 - u i).prod := by
  induction L with
  | nil => simp
  | cons a L ih =>
    simp only [List.map_cons, List.sum_cons, List.prod_cons]
    have ha0 := h0 a (by simp); have ha1 := h1 a (by simp)
    have ih' := ih (fun i hi => h0 i (by simp [hi])) (fun i hi => h1 i (by simp [hi]))
    have hs : 0 ≤ (L.map u).sum := List.sum_nonneg fun x hx => by
      obtain ⟨i, hi, rfl⟩ := List.mem_map.1 hx; exact h0 i (by simp [hi])
    nlinarith [mul_le_mul_of_nonneg_left ih' (by linarith : (0 : ℝ) ≤ 1 - u a)]

/-- `∏ (1 + uᵢ) ≤ exp (∑ uᵢ)` for `uᵢ ≥ 0`. -/
theorem prod_one_add_le {ι : Type*} (L : List ι) (u : ι → ℝ) (h0 : ∀ i ∈ L, 0 ≤ u i) :
    (L.map fun i => 1 + u i).prod ≤ exp (L.map u).sum := by
  induction L with
  | nil => simp
  | cons a L ih =>
    simp only [List.map_cons, List.sum_cons, List.prod_cons, Real.exp_add]
    have ih' := ih (fun i hi => h0 i (by simp [hi]))
    have hp : 0 ≤ (L.map fun i => 1 + u i).prod := List.prod_nonneg fun x hx => by
      obtain ⟨i, hi, rfl⟩ := List.mem_map.1 hx; linarith [h0 i (by simp [hi])]
    have := Real.add_one_le_exp (u a)
    calc (1 + u a) * (L.map fun i => 1 + u i).prod ≤ exp (u a) * (L.map fun i => 1 + u i).prod :=
          mul_le_mul_of_nonneg_right (by linarith) hp
      _ ≤ exp (u a) * exp (L.map u).sum := mul_le_mul_of_nonneg_left ih' (Real.exp_pos _).le

theorem list_prod_le_prod {ι : Type*} (L : List ι) {f g : ι → ℝ} (hf : ∀ i ∈ L, 0 ≤ f i) (hfg : ∀ i ∈ L, f i ≤ g i) :
    (L.map f).prod ≤ (L.map g).prod := by
  induction L with
  | nil => simp
  | cons a L ih =>
    simp only [List.map_cons, List.prod_cons]
    have ih' := ih (fun i hi => hf i (by simp [hi])) (fun i hi => hfg i (by simp [hi]))
    have hp : 0 ≤ (L.map f).prod := List.prod_nonneg fun x hx => by
      obtain ⟨i, hi, rfl⟩ := List.mem_map.1 hx; exact hf i (by simp [hi])
    exact mul_le_mul (hfg a (by simp)) ih' hp (le_trans (hf a (by simp)) (hfg a (by simp)))

theorem list_prod_mul {ι : Type*} (L : List ι) (f g : ι → ℝ) :
    (L.map fun i => f i * g i).prod = (L.map f).prod * (L.map g).prod := by
  induction L with
  | nil => simp
  | cons a L ih => simp only [List.map_cons, List.prod_cons, ih]; ring

theorem list_prod_exp {ι : Type*} (L : List ι) (f : ι → ℝ) :
    (L.map fun i => exp (f i)).prod = exp (L.map f).sum := by
  induction L with
  | nil => simp
  | cons a L ih => simp only [List.map_cons, List.prod_cons, List.sum_cons, ih, Real.exp_add]

theorem sum_sq_le_sq_sum {ι : Type*} (L : List ι) (f : ι → ℝ) (h0 : ∀ i ∈ L, 0 ≤ f i) :
    (L.map fun i => f i ^ 2).sum ≤ (L.map f).sum ^ 2 := by
  induction L with
  | nil => simp
  | cons a L ih =>
    simp only [List.map_cons, List.sum_cons]
    have ih' := ih (fun i hi => h0 i (by simp [hi]))
    have hs : 0 ≤ (L.map f).sum := List.sum_nonneg fun x hx => by
      obtain ⟨i, hi, rfl⟩ := List.mem_map.1 hx; exact h0 i (by simp [hi])
    nlinarith [h0 a (by simp)]

theorem sum_cube_le_cube_sum {ι : Type*} (L : List ι) (f : ι → ℝ) (h0 : ∀ i ∈ L, 0 ≤ f i) :
    (L.map fun i => f i ^ 3).sum ≤ (L.map f).sum ^ 3 := by
  induction L with
  | nil => simp
  | cons a L ih =>
    simp only [List.map_cons, List.sum_cons]
    have ih' := ih (fun i hi => h0 i (by simp [hi]))
    have hs : 0 ≤ (L.map f).sum := List.sum_nonneg fun x hx => by
      obtain ⟨i, hi, rfl⟩ := List.mem_map.1 hx; exact h0 i (by simp [hi])
    have ha := h0 a (by simp)
    nlinarith [mul_nonneg ha hs, mul_nonneg (mul_nonneg ha hs) hs, mul_nonneg (mul_nonneg ha ha) hs]

/-! ## One note -/

/-- `λ` as the spec's lottery constant: `t0Const / p`. -/
noncomputable def lam0 (c : Config) : ℝ := (c.t0Const : ℝ) / c.p

/-- The lottery constants are the expansion of `1 - e^{-λx}`: `t1Const/p` is
`λ²/2` up to a relative error `η`. -/
structure LotConsts (c : Config) (η : ℝ) : Prop where
  p_pos : 0 < c.p
  t0_pos : 0 < c.t0Const
  t1_le : c.t1Const ≤ c.p
  a1_le : (c.t1Const : ℝ) / c.p ≤ lam0 c ^ 2
  a1_near : |(c.t1Const : ℝ) / c.p - lam0 c ^ 2 / 2| ≤ η * lam0 c ^ 2

theorem natdiv_ge (m n : ℕ) (hn : 0 < n) : (m : ℝ) / n - 1 ≤ ((m / n : ℕ) : ℝ) := by
  have h := Nat.div_add_mod m n
  have hlt := Nat.mod_lt m hn
  have hnr : (0 : ℝ) < n := by exact_mod_cast hn
  rw [div_sub_one hnr.ne', div_le_iff₀ hnr]
  have : (m : ℝ) = n * ((m / n : ℕ) : ℝ) + ((m % n : ℕ) : ℝ) := by exact_mod_cast h.symm
  have : ((m % n : ℕ) : ℝ) ≤ n - 1 := by
    have : m % n + 1 ≤ n := hlt
    have : ((m % n : ℕ) : ℝ) + 1 ≤ n := by exact_mod_cast this
    linarith
  nlinarith

variable {c : Config} {η : ℝ}

set_option maxHeartbeats 1000000 in
/-- **One note's win probability**: `w = y - y²/2` up to `η y² + v/p + v²/p`, for
`y = λ v/D ≤ 1/2`. -/
theorem note_w (hc : LotConsts c η) {D v : ℕ} (hD : 1 ≤ D) (hD2 : 2 * D ≤ c.t0Const)
    (hy : lam0 c * v / D ≤ 1 / 2) :
    |(threshold c D v : ℝ) / c.p - (lam0 c * v / D - (lam0 c * v / D) ^ 2 / 2)| ≤
      η * (lam0 c * v / D) ^ 2 + (v : ℝ) / c.p + (v : ℝ) ^ 2 / c.p := by
  have hp : (0 : ℝ) < c.p := by exact_mod_cast hc.p_pos
  have hDr : (0 : ℝ) < D := by exact_mod_cast hD
  have hDr1 : (1 : ℝ) ≤ D := by exact_mod_cast hD
  have hD2r : 2 * (D : ℝ) ≤ c.t0Const := by exact_mod_cast hD2
  set T0 := t0 c D with hT0
  set U := c.t1Const / D ^ 2 with hU
  have hT0le : (T0 : ℝ) ≤ c.t0Const / D := Nat.cast_div_le
  have hT0ge : (c.t0Const : ℝ) / D - 1 ≤ T0 := natdiv_ge _ _ (by omega)
  have hUle : (U : ℝ) ≤ c.t1Const / (D : ℝ) ^ 2 := by
    have := Nat.cast_div_le (α := ℝ) (m := c.t1Const) (n := D ^ 2); push_cast at this; exact this
  have hUge : (c.t1Const : ℝ) / (D : ℝ) ^ 2 - 1 ≤ U := by
    have := natdiv_ge c.t1Const (D ^ 2) (by positivity); push_cast at this; exact this
  have hl0 : lam0 c = (c.t0Const : ℝ) / c.p := rfl
  have hl0pos : 0 < lam0 c := by rw [hl0]; exact div_pos (by exact_mod_cast hc.t0_pos) hp
  have hv0 : (0 : ℝ) ≤ v := by positivity
  set y := lam0 c * v / D with hy'
  have hy0 : 0 ≤ y := by positivity
  -- `t1Const/D² · v ≤ T0`: no underflow
  have hUv : (U : ℝ) * v ≤ T0 := by
    have h1 : (U : ℝ) * v ≤ c.t1Const / (D : ℝ) ^ 2 * v := mul_le_mul_of_nonneg_right hUle hv0
    have h2 : (c.t1Const : ℝ) / (D : ℝ) ^ 2 * v ≤ c.p * lam0 c ^ 2 * v / D ^ 2 := by
      have := hc.a1_le
      rw [div_le_iff₀ hp] at this
      rw [div_mul_eq_mul_div, div_le_div_iff_of_pos_right (by positivity)]
      nlinarith
    have h3 : (c.p : ℝ) * lam0 c ^ 2 * v / D ^ 2 = c.p * lam0 c * y / D := by
      rw [hy']; field_simp
    have h4 : (c.p : ℝ) * lam0 c * y / D ≤ c.t0Const / (2 * D) := by
      rw [div_le_div_iff₀ hDr (by positivity)]
      have : (c.p : ℝ) * lam0 c = c.t0Const := by rw [hl0]; field_simp
      rw [this]
      have h0 : (0 : ℝ) ≤ c.t0Const * D := by positivity
      have e : (c.t0Const : ℝ) * y * (2 * D) = (c.t0Const * D) * (2 * y) := by ring
      rw [e]; nlinarith
    have h5 : (c.t0Const : ℝ) / (2 * D) ≤ c.t0Const / D - 1 := by
      rw [div_sub_one hDr.ne', div_le_div_iff₀ (by positivity) hDr]; nlinarith
    linarith
  have hle : v * U * v ≤ v * T0 := by
    have : U * v ≤ T0 := by exact_mod_cast hUv
    calc v * U * v = v * (U * v) := by ring
      _ ≤ v * T0 := Nat.mul_le_mul_left _ this
  have hvT0 : (v : ℝ) * T0 ≤ c.p * y := by
    calc (v : ℝ) * T0 ≤ v * (c.t0Const / D) := mul_le_mul_of_nonneg_left hT0le hv0
      _ = c.p * y := by rw [hy', hl0]; field_simp
  have hlt : v * T0 - v * U * v < c.p := by
    have h1 : v * T0 - v * U * v ≤ v * T0 := Nat.sub_le _ _
    have h2 : ((v * T0 : ℕ) : ℝ) < c.p := by push_cast; nlinarith
    have : v * T0 < c.p := by exact_mod_cast h2
    omega
  have hthr := threshold_eq c D v (by simpa [hT0, hU] using hle) (by simpa [hT0, hU] using hlt)
    (le_trans (Nat.div_le_self _ _) hc.t1_le)
  rw [hthr, Nat.cast_sub (by simpa [hT0, hU] using hle)]
  push_cast
  rw [← hT0, ← hU]
  -- the two terms
  have hA1 : (v : ℝ) * T0 / c.p ≤ y := by rw [div_le_iff₀ hp]; linarith
  have hA2 : y - v / c.p ≤ (v : ℝ) * T0 / c.p := by
    rw [le_div_iff₀ hp]
    have : (v : ℝ) * (c.t0Const / D - 1) ≤ v * T0 := mul_le_mul_of_nonneg_left hT0ge hv0
    have e : y * c.p = v * (c.t0Const / D) := by rw [hy', hl0]; field_simp
    rw [sub_mul, div_mul_cancel₀ _ hp.ne', e]; nlinarith
  set a1 := (c.t1Const : ℝ) / c.p with ha1
  have hB1 : (v : ℝ) * U * v / c.p ≤ a1 * (v / D) ^ 2 := by
    rw [div_le_iff₀ hp]
    have : (v : ℝ) * U * v ≤ v * (c.t1Const / (D : ℝ) ^ 2) * v :=
      mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hUle hv0) hv0
    have e : a1 * (v / D) ^ 2 * c.p = v * (c.t1Const / (D : ℝ) ^ 2) * v := by
      rw [ha1]; field_simp
    linarith
  have hB2 : a1 * (v / D) ^ 2 - (v : ℝ) ^ 2 / c.p ≤ (v : ℝ) * U * v / c.p := by
    rw [le_div_iff₀ hp]
    have : (v : ℝ) * (c.t1Const / (D : ℝ) ^ 2 - 1) * v ≤ v * U * v :=
      mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hUge hv0) hv0
    have e : (a1 * (v / D) ^ 2 - (v : ℝ) ^ 2 / c.p) * c.p = v * (c.t1Const / (D : ℝ) ^ 2 - 1) * v := by
      rw [ha1]; field_simp
    linarith
  have hnear : |a1 * (v / D) ^ 2 - y ^ 2 / 2| ≤ η * y ^ 2 := by
    have h := hc.a1_near
    rw [← ha1] at h
    have e1 : a1 * (v / D) ^ 2 - y ^ 2 / 2 = (a1 - lam0 c ^ 2 / 2) * (v / D) ^ 2 := by rw [hy']; ring
    have e2 : η * y ^ 2 = η * lam0 c ^ 2 * (v / D) ^ 2 := by rw [hy']; ring
    rw [e1, e2, abs_mul, abs_of_nonneg (by positivity : (0 : ℝ) ≤ (v / D) ^ 2)]
    exact mul_le_mul_of_nonneg_right h (by positivity)
  have hsplit : ((v : ℝ) * T0 - v * U * v) / c.p = v * T0 / c.p - v * U * v / c.p := by ring
  rw [hsplit, abs_le]
  have hn := abs_le.1 hnear
  have hvp : 0 ≤ (v : ℝ) / c.p := by positivity
  have hv2p : 0 ≤ (v : ℝ) ^ 2 / c.p := by positivity
  constructor <;> nlinarith [hn.1, hn.2]

/-! ## A list of notes -/

theorem lsum_add {ι : Type*} (L : List ι) (f g : ι → ℝ) :
    (L.map fun i => f i + g i).sum = (L.map f).sum + (L.map g).sum := by
  induction L with
  | nil => simp
  | cons a L ih => simp only [List.map_cons, List.sum_cons, ih]; ring

theorem lsum_mul_left {ι : Type*} (L : List ι) (a : ℝ) (f : ι → ℝ) :
    (L.map fun i => a * f i).sum = a * (L.map f).sum := by
  induction L with
  | nil => simp
  | cons b L ih => simp only [List.map_cons, List.sum_cons, ih]; ring

theorem lsum_div {ι : Type*} (L : List ι) (f : ι → ℝ) (d : ℝ) :
    (L.map fun i => f i / d).sum = (L.map f).sum / d := by
  induction L with
  | nil => simp
  | cons b L ih => simp only [List.map_cons, List.sum_cons, ih]; ring

theorem lsum_neg {ι : Type*} (L : List ι) (f : ι → ℝ) : (L.map fun i => -f i).sum = -(L.map f).sum := by
  induction L with
  | nil => simp
  | cons b L ih => simp only [List.map_cons, List.sum_cons, ih]; ring


/-- The lower error of a list with exponent `Y` (`ζ` bounds `S/p + S²/p`). -/
noncomputable def errLo (η ζ Y : ℝ) : ℝ := 2 * (η * Y ^ 2 + ζ)

/-- The upper error of a list with exponent `Y`. -/
noncomputable def errHi (η ζ Y : ℝ) : ℝ := 2 * (2 / 9 * Y ^ 3 + η * Y ^ 2 + ζ)

/-- The stake of a list of notes. -/
def stakeOf (L : List Note) : ℕ := (L.map Note.value).sum

theorem lsum_cast (L : List Note) : (L.map fun n => (n.value : ℝ)).sum = (stakeOf L : ℝ) := by
  unfold stakeOf; rw [Nat.cast_list_sum, List.map_map]; rfl

/-- The exponent of a list of notes under a state: `λ S / D`. -/
noncomputable def expo (c : Config) (s : EpochState) (L : List Note) : ℝ := lam0 c * stakeOf L / s.D

/-- Smallness of a list's stake against the field. -/
structure Small (c : Config) (s : EpochState) (L : List Note) (ζ : ℝ) : Prop where
  D_pos : 1 ≤ s.D
  D_le : 2 * s.D ≤ c.t0Const
  S_small : (stakeOf L : ℝ) / c.p + (stakeOf L : ℝ) ^ 2 / c.p ≤ ζ

theorem expo_eq_sum (c : Config) (s : EpochState) (L : List Note) :
    expo c s L = (L.map fun n => lam0 c * n.value / s.D).sum := by
  unfold expo stakeOf
  induction L with
  | nil => simp
  | cons a L ih => simp only [List.map_cons, List.sum_cons, Nat.cast_add, ← ih]; push_cast; ring

theorem note_le_expo (c : Config) (s : EpochState) {L : List Note} (hc : 0 ≤ lam0 c) {n : Note} (hn : n ∈ L) :
    lam0 c * n.value / s.D ≤ expo c s L := by
  rw [expo_eq_sum]
  exact List.single_le_sum (fun x hx => by obtain ⟨m, -, rfl⟩ := List.mem_map.1 hx; positivity)
    _ (List.mem_map_of_mem hn)

theorem value_le_stake {L : List Note} {n : Note} (hn : n ∈ L) : n.value ≤ stakeOf L := by
  unfold stakeOf; exact List.single_le_sum (fun _ _ => Nat.zero_le _) _ (List.mem_map_of_mem hn)

/-- **All notes of a list lose**, from below: `e^{-Y} (1 - errLo)`. -/
theorem loss_lo (hc : LotConsts c η) (hη : 0 ≤ η) {s : EpochState} {L : List Note} {ζ : ℝ}
    (hsm : Small c s L ζ) (hY : expo c s L ≤ 1 / 2) (herr : errLo η ζ (expo c s L) ≤ 1) :
    exp (-expo c s L) * (1 - errLo η ζ (expo c s L)) ≤ loss c s L := by
  have hp : (0 : ℝ) < c.p := by exact_mod_cast hc.p_pos
  have hl0 : 0 ≤ lam0 c := by unfold lam0; positivity
  set y : Note → ℝ := fun n => lam0 c * n.value / s.D with hydef
  set e : Note → ℝ := fun n => η * y n ^ 2 + (n.value : ℝ) / c.p + (n.value : ℝ) ^ 2 / c.p with hedef
  have hy0 : ∀ n, 0 ≤ y n := fun n => by simp only [hydef]; positivity
  have he0 : ∀ n, 0 ≤ e n := fun n => by simp only [hedef]; have := hy0 n; positivity
  have hyle : ∀ n ∈ L, y n ≤ 1 / 2 := fun n hn => le_trans (note_le_expo c s hl0 hn) hY
  -- sums
  have hsy : (L.map y).sum = expo c s L := (expo_eq_sum c s L).symm
  have hse : (L.map fun n => 2 * e n).sum ≤ errLo η ζ (expo c s L) := by
    have h1 : (L.map fun n => y n ^ 2).sum ≤ expo c s L ^ 2 := hsy ▸ sum_sq_le_sq_sum L y fun n _ => hy0 n
    have h2 : (L.map fun n => (n.value : ℝ)).sum = stakeOf L := lsum_cast L
    have h3 : (L.map fun n => (n.value : ℝ) ^ 2).sum ≤ (stakeOf L : ℝ) ^ 2 :=
      h2 ▸ sum_sq_le_sq_sum L (fun n => (n.value : ℝ)) fun n _ => by positivity
    have e1 : (L.map fun n => 2 * e n).sum = 2 * (η * (L.map fun n => y n ^ 2).sum +
        (L.map fun n => (n.value : ℝ)).sum / c.p + (L.map fun n => (n.value : ℝ) ^ 2).sum / c.p) := by
      rw [lsum_mul_left]
      simp only [hedef]
      rw [lsum_add, lsum_add, lsum_mul_left, lsum_div, lsum_div]
    rw [e1, h2]
    unfold errLo
    have := hsm.S_small
    have h4 : (L.map fun n => (n.value : ℝ) ^ 2).sum / c.p ≤ (stakeOf L : ℝ) ^ 2 / c.p :=
      div_le_div_of_nonneg_right h3 hp.le
    nlinarith [mul_le_mul_of_nonneg_left h1 hη]
  -- per note
  have hnote : ∀ n ∈ L, exp (-y n) * (1 - 2 * e n) ≤ 1 - wn c s n := by
    intro n hn
    have hw := note_w hc hsm.D_pos hsm.D_le (hyle n hn)
    have hw' := (abs_le.1 hw).2
    have hq := exp_neg_le_quad' (hy0 n)
    have hexp : 1 / 2 ≤ exp (-y n) := by
      have := Real.exp_le_exp.2 (show -(1 / 2 : ℝ) ≤ -y n by linarith [hyle n hn])
      have h2 : exp (-(1 / 2 : ℝ)) = 1 / exp (1 / 2) := by rw [Real.exp_neg, inv_eq_one_div]
      have h3 : 1 / 2 ≤ 1 / exp (1 / 2 : ℝ) := one_div_le_one_div_of_le (Real.exp_pos _) exp_half_le_two
      linarith
    unfold wn
    simp only [hedef, hydef] at hw' ⊢
    nlinarith [he0 n]
  have hsum_le : ∀ n ∈ L, 2 * e n ≤ 1 := fun n hn => by
    have := List.single_le_sum (fun x hx => by
      obtain ⟨m, -, rfl⟩ := List.mem_map.1 hx; have := he0 m; positivity) _
      (List.mem_map_of_mem (f := fun n => 2 * e n) hn)
    linarith
  calc exp (-expo c s L) * (1 - errLo η ζ (expo c s L))
      ≤ exp (-expo c s L) * (1 - (L.map fun n => 2 * e n).sum) :=
        mul_le_mul_of_nonneg_left (by linarith) (Real.exp_pos _).le
    _ ≤ exp (-expo c s L) * (L.map fun n => 1 - 2 * e n).prod :=
        mul_le_mul_of_nonneg_left (prod_one_sub_ge L _ (fun n _ => by have := he0 n; positivity) hsum_le)
          (Real.exp_pos _).le
    _ = (L.map fun n => exp (-y n) * (1 - 2 * e n)).prod := by
        rw [list_prod_mul, list_prod_exp, lsum_neg, hsy]
    _ ≤ (L.map fun n => 1 - wn c s n).prod :=
        list_prod_le_prod L (fun n hn => mul_nonneg (Real.exp_pos _).le (by linarith [hsum_le n hn])) hnote
    _ = loss c s L := rfl

/-- **All notes of a list lose**, from above: `e^{-Y} e^{errHi}`. -/
theorem loss_hi (hc : LotConsts c η) (hη : 0 ≤ η) {s : EpochState} {L : List Note} {ζ : ℝ}
    (hsm : Small c s L ζ) (hY : expo c s L ≤ 1 / 2) :
    loss c s L ≤ exp (-expo c s L) * exp (errHi η ζ (expo c s L)) := by
  have hp : (0 : ℝ) < c.p := by exact_mod_cast hc.p_pos
  have hl0 : 0 ≤ lam0 c := by unfold lam0; positivity
  set y : Note → ℝ := fun n => lam0 c * n.value / s.D with hydef
  set e : Note → ℝ := fun n => 2 * (2 / 9 * y n ^ 3 + η * y n ^ 2 + (n.value : ℝ) / c.p +
    (n.value : ℝ) ^ 2 / c.p) with hedef
  have hy0 : ∀ n, 0 ≤ y n := fun n => by simp only [hydef]; positivity
  have he0 : ∀ n, 0 ≤ e n := fun n => by simp only [hedef]; have := hy0 n; positivity
  have hyle : ∀ n ∈ L, y n ≤ 1 / 2 := fun n hn => le_trans (note_le_expo c s hl0 hn) hY
  have hsy : (L.map y).sum = expo c s L := (expo_eq_sum c s L).symm
  have hse : (L.map e).sum ≤ errHi η ζ (expo c s L) := by
    have h1 : (L.map fun n => y n ^ 2).sum ≤ expo c s L ^ 2 := hsy ▸ sum_sq_le_sq_sum L y fun n _ => hy0 n
    have h1' : (L.map fun n => y n ^ 3).sum ≤ expo c s L ^ 3 := hsy ▸ sum_cube_le_cube_sum L y fun n _ => hy0 n
    have h2 : (L.map fun n => (n.value : ℝ)).sum = stakeOf L := lsum_cast L
    have h3 : (L.map fun n => (n.value : ℝ) ^ 2).sum ≤ (stakeOf L : ℝ) ^ 2 :=
      h2 ▸ sum_sq_le_sq_sum L (fun n => (n.value : ℝ)) fun n _ => by positivity
    have e1 : (L.map e).sum = 2 * (2 / 9 * (L.map fun n => y n ^ 3).sum + η * (L.map fun n => y n ^ 2).sum +
        (L.map fun n => (n.value : ℝ)).sum / c.p + (L.map fun n => (n.value : ℝ) ^ 2).sum / c.p) := by
      simp only [hedef]
      rw [lsum_mul_left, lsum_add, lsum_add, lsum_add, lsum_mul_left, lsum_mul_left, lsum_div, lsum_div]
    rw [e1, h2]
    unfold errHi
    have := hsm.S_small
    have h4 : (L.map fun n => (n.value : ℝ) ^ 2).sum / c.p ≤ (stakeOf L : ℝ) ^ 2 / c.p :=
      div_le_div_of_nonneg_right h3 hp.le
    nlinarith [mul_le_mul_of_nonneg_left h1 hη]
  have hnote : ∀ n ∈ L, 1 - wn c s n ≤ exp (-y n) * (1 + e n) := by
    intro n hn
    have hw := note_w hc hsm.D_pos hsm.D_le (hyle n hn)
    have hw' := (abs_le.1 hw).1
    have hq := quad_le_exp_neg (hy0 n) (by linarith [hyle n hn])
    have hexp : 1 / 2 ≤ exp (-y n) := by
      have := Real.exp_le_exp.2 (show -(1 / 2 : ℝ) ≤ -y n by linarith [hyle n hn])
      have h2 : exp (-(1 / 2 : ℝ)) = 1 / exp (1 / 2) := by rw [Real.exp_neg, inv_eq_one_div]
      have h3 : 1 / 2 ≤ 1 / exp (1 / 2 : ℝ) := one_div_le_one_div_of_le (Real.exp_pos _) exp_half_le_two
      linarith
    have hu0 : 0 ≤ 2 / 9 * y n ^ 3 + η * y n ^ 2 + (n.value : ℝ) / c.p + (n.value : ℝ) ^ 2 / c.p := by
      have := hy0 n; positivity
    have key := mul_le_mul_of_nonneg_left (show (1 : ℝ) ≤ 2 * exp (-y n) by linarith) hu0
    unfold wn
    simp only [hedef, hydef] at hw' hq key hu0 ⊢
    nlinarith
  have hw1 : ∀ n, 0 ≤ 1 - wn c s n := fun n => by linarith [wn_le_one hc.p_pos s n]
  calc loss c s L = (L.map fun n => 1 - wn c s n).prod := rfl
    _ ≤ (L.map fun n => exp (-y n) * (1 + e n)).prod := list_prod_le_prod L (fun n _ => hw1 n) hnote
    _ = exp (-expo c s L) * (L.map fun n => 1 + e n).prod := by
        rw [list_prod_mul, list_prod_exp, lsum_neg, hsy]
    _ ≤ exp (-expo c s L) * exp (L.map e).sum :=
        mul_le_mul_of_nonneg_left (prod_one_add_le L e fun n _ => he0 n) (Real.exp_pos _).le
    _ ≤ exp (-expo c s L) * exp (errHi η ζ (expo c s L)) :=
        mul_le_mul_of_nonneg_left (Real.exp_le_exp.2 hse) (Real.exp_pos _).le

/-! ## Honest nodes -/

theorem wn_lt_one {c : Config} (hp : 0 < c.p) (s : EpochState) (n : Note) : wn c s n < 1 := by
  unfold wn
  rw [div_lt_one (by exact_mod_cast hp)]
  exact_mod_cast threshold_lt c hp s.D n.value

theorem loss_pos {c : Config} (hp : 0 < c.p) (s : EpochState) (L : List Note) : 0 < loss c s L := by
  unfold loss
  induction L with
  | nil => simp
  | cons a L ih =>
    simp only [List.map_cons, List.prod_cons]
    exact mul_pos (by linarith [wn_lt_one hp s a]) ih

theorem loss_filter_or (c : Config) (s : EpochState) (L : List Note) (p q : Note → Bool)
    (hd : ∀ n, ¬ (p n = true ∧ q n = true)) :
    loss c s (L.filter fun n => p n || q n) = loss c s (L.filter p) * loss c s (L.filter q) := by
  unfold loss
  induction L with
  | nil => simp
  | cons a L ih =>
    by_cases hp : p a = true <;> by_cases hq : q a = true
    · exact absurd ⟨hp, hq⟩ (hd a)
    · simp [List.filter_cons, hp, hq, ih]; ring
    · simp [List.filter_cons, hp, hq, ih]; ring
    · simp [List.filter_cons, hp, hq, ih]

variable {E : Env}

/-- The loss of one honest node's notes (none if it is offline). -/
noncomputable def nodeLoss (E : Env) (i : ℕ) (s : EpochState) (j : ℕ) : ℝ := loss E.c s (honNotes E i s [j])

theorem loss_honNotes_cons (i : ℕ) (s : EpochState) {a : ℕ} {K : List ℕ} (ha : a ∉ K) :
    loss E.c s (honNotes E i s (a :: K)) = nodeLoss E i s a * loss E.c s (honNotes E i s K) := by
  unfold nodeLoss honNotes
  have e : (fun n : Note => (a :: K).any fun j => E.online j i && decide (n.owner = .honest j)) =
      fun n => ([a].any fun j => E.online j i && decide (n.owner = .honest j)) ||
        (K.any fun j => E.online j i && decide (n.owner = .honest j)) := by
    funext n; simp [List.any_cons]
  rw [e, loss_filter_or]
  intro n ⟨h1, h2⟩
  simp only [List.any_cons, List.any_nil, Bool.or_false, Bool.and_eq_true, decide_eq_true_eq,
    List.any_eq_true] at h1 h2
  obtain ⟨j, hj, -, hj'⟩ := h2
  rw [h1.2] at hj'
  cases hj'
  exact ha hj

theorem loss_honNotes_prod (i : ℕ) (s : EpochState) : ∀ K : List ℕ, K.Nodup →
    loss E.c s (honNotes E i s K) = (K.map (nodeLoss E i s)).prod
  | [], _ => by simp [honNotes, loss]
  | a :: K, h => by
    rw [List.nodup_cons] at h
    rw [loss_honNotes_cons i s h.1, loss_honNotes_prod i s K h.2, List.map_cons, List.prod_cons]

/-- `1 - ∏ - ∑ (∏ without j - ∏) ≥ 0` for factors in `(0, 1]`: the probability of
two or more successes is nonnegative. -/
theorem two_or_more_nonneg (f : ℕ → ℝ) (h0 : ∀ j, 0 ≤ f j) (h1 : ∀ j, f j ≤ 1) : ∀ K : List ℕ, K.Nodup →
    0 ≤ 1 - (K.map f).prod - (K.map fun j => ((K.erase j).map f).prod - (K.map f).prod).sum
  | [], _ => by simp
  | a :: K, h => by
    rw [List.nodup_cons] at h
    have ih := two_or_more_nonneg f h0 h1 K h.2
    have hP : 0 ≤ (K.map f).prod := List.prod_nonneg fun x hx => by
      obtain ⟨j, -, rfl⟩ := List.mem_map.1 hx; exact h0 j
    have hQ : 0 ≤ (K.map fun j => ((K.erase j).map f).prod - (K.map f).prod).sum := by
      refine List.sum_nonneg fun x hx => ?_
      obtain ⟨j, hj, rfl⟩ := List.mem_map.1 hx
      have := List.prod_map_erase f hj
      have hE : 0 ≤ ((K.erase j).map f).prod := List.prod_nonneg fun y hy => by
        obtain ⟨k, -, rfl⟩ := List.mem_map.1 hy; exact h0 k
      nlinarith [h1 j, h0 j]
    have hsum : ((a :: K).map fun j => (((a :: K).erase j).map f).prod - ((a :: K).map f).prod).sum =
        ((K.map f).prod - f a * (K.map f).prod) +
          f a * (K.map fun j => ((K.erase j).map f).prod - (K.map f).prod).sum := by
      simp only [List.map_cons, List.sum_cons, List.erase_cons_head, List.prod_cons]
      congr 1
      rw [← lsum_mul_left]
      refine congrArg List.sum (List.map_congr_left fun j hj => ?_)
      have hja : j ≠ a := fun e => h.1 (e ▸ hj)
      rw [List.erase_cons_tail (by simpa using hja.symm), List.map_cons, List.prod_cons]; ring
    rw [hsum]
    simp only [List.map_cons, List.prod_cons]
    have := mul_le_mul_of_nonneg_right (h1 a) hQ
    linarith

theorem log_list_prod (f : ℕ → ℝ) (hpos : ∀ j, 0 < f j) (K : List ℕ) :
    Real.log (K.map f).prod = (K.map fun j => Real.log (f j)).sum := by
  induction K with
  | nil => simp
  | cons a K ih =>
    simp only [List.map_cons, List.prod_cons, List.sum_cons]
    rw [Real.log_mul (hpos a).ne' (List.prod_pos fun x hx => by
      obtain ⟨j, -, rfl⟩ := List.mem_map.1 hx; exact hpos j).ne', ih]

/-- **Exactly one success**, Poisson bound: `∑ (∏ without j - ∏) ≥ -∏ ln ∏`. -/
theorem exactly_one_ge (f : ℕ → ℝ) (hpos : ∀ j, 0 < f j) (K : List ℕ) :
    -((K.map f).prod * Real.log (K.map f).prod) ≤
      (K.map fun j => ((K.erase j).map f).prod - (K.map f).prod).sum := by
  classical
  rw [log_list_prod f hpos, mul_comm, ← neg_mul, ← lsum_neg, ← List.sum_map_mul_right]
  refine List.sum_le_sum fun j hj => ?_
  have he := List.prod_map_erase f hj
  have hE : 0 < ((K.erase j).map f).prod := List.prod_pos fun y hy => by
    obtain ⟨k, -, rfl⟩ := List.mem_map.1 hy; exact hpos k
  have hl := Real.one_sub_inv_le_log_of_pos (hpos j)
  rw [← he]
  have hfj := hpos j
  have : ((K.erase j).map f).prod - f j * ((K.erase j).map f).prod =
      f j * ((K.erase j).map f).prod * ((f j)⁻¹ - 1) := by field_simp
  rw [this]
  have hP : 0 < f j * ((K.erase j).map f).prod := mul_pos hfj hE
  nlinarith [mul_le_mul_of_nonneg_left hl hP.le]

/-! ## The band condition from exponent ranges -/

/-- `e^{-y}` from below, polynomially (`y ∈ [0, 1]`). -/
noncomputable def Elo (y : ℝ) : ℝ := 1 - y + y ^ 2 / 2 - 2 / 9 * y ^ 3

/-- `e^{-y}` from above, polynomially (`y ≥ 0`). -/
noncomputable def Ehi (y : ℝ) : ℝ := 1 - y + y ^ 2 / 2

/-- **A band for a range of exponents**: honest exponent in `[ylo, yhi]`,
adversarial exponent at most `ahi`. -/
structure Member where
  ylo : ℝ
  yhi : ℝ
  ahi : ℝ
  B : Band

/-- The band of a member covers its exponent range (polynomial conditions,
checked by `norm_num` in a certificate). -/
structure Member.OK (m : Member) (η ζ : ℝ) : Prop where
  ylo0 : 0 ≤ m.ylo
  le : m.ylo ≤ m.yhi
  yhi : m.yhi ≤ 1 / 2
  ahi0 : 0 ≤ m.ahi
  ahi : m.ahi ≤ 1 / 2
  eLoH : errLo η ζ m.yhi ≤ 1
  eLoA : errLo η ζ m.ahi ≤ 1
  eHi : errHi η ζ m.yhi ≤ 1
  pos1 : errHi η ζ m.yhi ≤ m.ylo
  hhi : 1 - Elo m.yhi * (1 - errLo η ζ m.yhi) ≤ m.B.hhi
  hlo : m.B.hlo ≤ 1 - Ehi m.ylo * (1 + 2 * errHi η ζ m.yhi)
  amax : 1 - Elo m.ahi * (1 - errLo η ζ m.ahi) ≤ m.B.amax
  amax1 : m.B.amax ≤ 1
  slo : m.B.slo ≤ Elo m.yhi * (1 - errLo η ζ m.yhi) * (m.ylo - errHi η ζ m.yhi) * (1 - m.B.amax)
  hnlo : m.B.hnlo ≤ m.B.hlo * (1 - m.B.amax)
  elo : m.B.elo ≤ Elo m.yhi * (1 - errLo η ζ m.yhi) * (1 - m.B.amax)

theorem errLo_mono {η ζ Y Y' : ℝ} (hη : 0 ≤ η) (h0 : 0 ≤ Y) (h : Y ≤ Y') : errLo η ζ Y ≤ errLo η ζ Y' := by
  unfold errLo; nlinarith [mul_le_mul_of_nonneg_left (pow_le_pow_left₀ h0 h 2) hη]

theorem errHi_mono {η ζ Y Y' : ℝ} (hη : 0 ≤ η) (h0 : 0 ≤ Y) (h : Y ≤ Y') : errHi η ζ Y ≤ errHi η ζ Y' := by
  unfold errHi; nlinarith [mul_le_mul_of_nonneg_left (pow_le_pow_left₀ h0 h 2) hη, pow_le_pow_left₀ h0 h 3]

theorem errHi_nonneg {η ζ Y : ℝ} (hη : 0 ≤ η) (hζ : 0 ≤ ζ) (h0 : 0 ≤ Y) : 0 ≤ errHi η ζ Y := by
  unfold errHi; positivity

theorem pOne_eq (hnd : E.nodes.Nodup) (i : ℕ) (s : EpochState) :
    pOne E i s = (E.nodes.map fun j => ((E.nodes.erase j).map (nodeLoss E i s)).prod -
      (E.nodes.map (nodeLoss E i s)).prod).sum := by
  unfold pOne pZero
  refine congrArg List.sum (List.map_congr_left fun j _ => ?_)
  rw [loss_honNotes_prod i s _ (hnd.erase j), loss_honNotes_prod i s _ hnd]

/-- **The band condition for a member.** If the state's honest exponent is in the
member's range and the adversary's below its bound, slot `i` is within its band. -/
theorem slotBand_of_member (hc : LotConsts E.c η) (hη : 0 ≤ η) (hnd : E.nodes.Nodup) {i : ℕ}
    {s : EpochState} (hs : (s.lead.map Note.id).Nodup) {ζ : ℝ} (hζ : 0 ≤ ζ)
    (hsH : Small E.c s (honNotes E i s E.nodes) ζ) (hsA : Small E.c s (advNotes s) ζ)
    {m : Member} (hm : m.OK η ζ)
    (hH1 : m.ylo ≤ expo E.c s (honNotes E i s E.nodes)) (hH2 : expo E.c s (honNotes E i s E.nodes) ≤ m.yhi)
    (hA : expo E.c s (advNotes s) ≤ m.ahi) : SlotBand m.B E i s := by
  have hp := hc.p_pos
  set yH := expo E.c s (honNotes E i s E.nodes) with hyH
  set yA := expo E.c s (advNotes s) with hyA
  have hl0 : 0 ≤ lam0 E.c := by unfold lam0; positivity
  have hyH0 : 0 ≤ yH := by rw [hyH]; unfold expo; positivity
  have hyA0 : 0 ≤ yA := by rw [hyA]; unfold expo; positivity
  have hyHh : yH ≤ 1 / 2 := le_trans hH2 hm.yhi
  have hyAh : yA ≤ 1 / 2 := le_trans hA hm.ahi
  set P0 := pZero E i s with hP0
  have hP0pos : 0 < P0 := loss_pos hp s _
  -- `P0` from below
  have eL := errLo_mono (ζ := ζ) hη hyH0 hH2
  have hElo0 : 0 ≤ Elo m.yhi := by unfold Elo; nlinarith [hm.yhi, hm.ylo0, hm.le]
  have hP0lo : Elo m.yhi * (1 - errLo η ζ m.yhi) ≤ P0 := by
    have h1 := loss_lo hc hη hsH hyHh (le_trans eL hm.eLoH)
    have h2 : Elo m.yhi ≤ exp (-yH) := le_trans (exp_neg_ge_cubic (by linarith [hm.ylo0, hm.le])
      (by linarith [hm.yhi])) (Real.exp_le_exp.2 (by linarith))
    calc Elo m.yhi * (1 - errLo η ζ m.yhi) ≤ exp (-yH) * (1 - errLo η ζ yH) :=
          mul_le_mul h2 (by linarith) (by linarith [hm.eLoH]) (Real.exp_pos _).le
      _ ≤ P0 := h1
  -- `P0` from above
  have eH := errHi_mono (ζ := ζ) hη hyH0 hH2
  have heH0 := errHi_nonneg (η := η) hη hζ hyH0
  have hP0e : P0 ≤ exp (-yH) * exp (errHi η ζ yH) := loss_hi hc hη hsH hyHh
  have hP0hi : P0 ≤ Ehi m.ylo * (1 + 2 * errHi η ζ m.yhi) := by
    calc P0 ≤ exp (-yH) * exp (errHi η ζ yH) := hP0e
      _ ≤ exp (-m.ylo) * exp (errHi η ζ m.yhi) :=
          mul_le_mul (Real.exp_le_exp.2 (by linarith)) (Real.exp_le_exp.2 eH) (Real.exp_pos _).le
            (Real.exp_pos _).le
      _ ≤ Ehi m.ylo * (1 + 2 * errHi η ζ m.yhi) :=
          mul_le_mul (exp_neg_le_quad' hm.ylo0) (exp_le_one_add_two (by linarith) hm.eHi)
            (Real.exp_pos _).le (by unfold Ehi; nlinarith [hm.ylo0, hm.le, hm.yhi])
  -- `-ln P0 ≥ ylo - errHi`
  have hlog : m.ylo - errHi η ζ m.yhi ≤ -Real.log P0 := by
    have : Real.log P0 ≤ -yH + errHi η ζ yH := by
      rw [← Real.exp_add] at hP0e
      have := Real.log_le_log hP0pos hP0e
      rwa [Real.log_exp] at this
    linarith
  -- the honest node losses
  have hnl0 : ∀ j, 0 < nodeLoss E i s j := fun j => loss_pos hp s _
  have hnl1 : ∀ j, nodeLoss E i s j ≤ 1 := fun j => loss_le_one hp s _
  have hP0prod : P0 = (E.nodes.map (nodeLoss E i s)).prod := loss_honNotes_prod i s _ hnd
  have h1ge : P0 * (m.ylo - errHi η ζ m.yhi) ≤ pOne E i s := by
    rw [pOne_eq hnd]
    have := exactly_one_ge (nodeLoss E i s) hnl0 E.nodes
    rw [← hP0prod] at this ⊢
    nlinarith [mul_le_mul_of_nonneg_left hlog hP0pos.le]
  have h2ge : 0 ≤ 1 - P0 - pOne E i s := by
    rw [pOne_eq hnd, hP0prod]
    exact two_or_more_nonneg _ (fun j => (hnl0 j).le) hnl1 _ hnd
  have hfac : 0 ≤ m.ylo - errHi η ζ m.yhi := by linarith [hm.pos1]
  have hq1 : Elo m.yhi * (1 - errLo η ζ m.yhi) * (m.ylo - errHi η ζ m.yhi) ≤ pOne E i s :=
    le_trans (mul_le_mul_of_nonneg_right hP0lo hfac) h1ge
  have ham : 0 ≤ 1 - m.B.amax := by linarith [hm.amax1]
  -- the adversary
  have hqa : qaRO E.c s ≤ m.B.amax := by
    unfold qaRO
    have h1 := loss_lo hc hη hsA hyAh (le_trans (errLo_mono hη hyA0 hA) hm.eLoA)
    have h2 : Elo m.ahi ≤ exp (-yA) := le_trans (exp_neg_ge_cubic hm.ahi0 (by linarith [hm.ahi]))
      (Real.exp_le_exp.2 (by linarith))
    have hEa : 0 ≤ Elo m.ahi := by unfold Elo; nlinarith [hm.ahi, hm.ahi0]
    have h3 : Elo m.ahi * (1 - errLo η ζ m.ahi) ≤ exp (-yA) * (1 - errLo η ζ yA) :=
      mul_le_mul h2 (by linarith [errLo_mono (ζ := ζ) hη hyA0 hA]) (by linarith [hm.eLoA]) (Real.exp_pos _).le
    linarith [hm.amax]
  refine ⟨hs, ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩, hqa⟩
  · intro h
    have := mul_nonneg hP0pos.le hfac
    fin_cases h <;> simp [qhRO] <;> linarith
  · simp [qhRO]
  · simp only [qhRO]; norm_num; linarith [hm.hlo]
  · simp only [qhRO]; norm_num; linarith [hm.hhi]
  · simp only [qhRO]; norm_num
    exact le_trans hm.slo (mul_le_mul_of_nonneg_right hq1 ham)
  · simp only [qhRO]; norm_num
    exact le_trans hm.hnlo (mul_le_mul_of_nonneg_right (by linarith [hm.hlo]) ham)
  · simp only [qhRO]; norm_num
    exact le_trans hm.elo (mul_le_mul_of_nonneg_right hP0lo ham)

/-! ## From stake fractions and the stake estimate -/

/-- **Stake fractions and the stake estimate** at slot `i` under state `s`. The
adversary holds at most a fraction `β` of the participating stake (online honest
plus adversarial). The estimate `D` puts `λ·V/D` in `[ℓlo, ℓhi]` for a visible
stake `V` between `(1-μ)·H + (1-w)·A` and `H + A`: a fraction `μ` of honest stake
may go unseen (wins lost without uncle references), and a fraction `w` of the
adversary's (withheld branches). -/
structure StakeTSI (E : Env) (i : ℕ) (s : EpochState) (β ℓlo ℓhi μ w : ℝ) : Prop where
  frac : (1 - β) * (stakeOf (advNotes s) : ℝ) ≤ β * stakeOf (honNotes E i s E.nodes)
  tsi : ∃ V : ℝ, (1 - μ) * (stakeOf (honNotes E i s E.nodes) : ℝ) + (1 - w) * stakeOf (advNotes s) ≤ V ∧
    V ≤ stakeOf (honNotes E i s E.nodes) + stakeOf (advNotes s) ∧
    ℓlo * s.D ≤ lam0 E.c * V ∧ lam0 E.c * V ≤ ℓhi * s.D

/-- Members cover consecutive ranges of the honest exponent. -/
def Chained : Member → List Member → Prop
  | _, [] => True
  | a, b :: ms => a.yhi = b.ylo ∧ Chained b ms

theorem cover_chain (y : ℝ) : ∀ (a : Member) (ms : List Member), Chained a ms → a.ylo ≤ y →
    y ≤ ((a :: ms).getLast (List.cons_ne_nil a ms)).yhi → ∃ m ∈ a :: ms, m.ylo ≤ y ∧ y ≤ m.yhi
  | a, [], _, h1, h2 => ⟨a, List.mem_singleton_self a, h1, by simpa using h2⟩
  | a, b :: ms, hc, h1, h2 => by
    by_cases hy : y ≤ a.yhi
    · exact ⟨a, List.mem_cons_self, h1, hy⟩
    · obtain ⟨m, hm, hm1, hm2⟩ := cover_chain y b ms hc.2 (by rw [← hc.1]; linarith)
        (by simpa [List.getLast_cons] using h2)
      exact ⟨m, List.mem_cons_of_mem a hm, hm1, hm2⟩

/-- The adversary's bound in a member follows from the stake fractions or from the
estimate. -/
def Member.AdvOK (m : Member) (β ℓhi μ w : ℝ) : Prop :=
  β * m.yhi ≤ (1 - β) * m.ahi ∨ (0 < 1 - w ∧ ℓhi - (1 - μ) * m.ylo ≤ (1 - w) * m.ahi)

/-- **The band condition from stake fractions and the stake estimate.** If the
members' ranges cover the honest exponents the stake fractions and the estimate
allow, slot `i` is within the band of some member. -/
theorem slotBand_of_stake (hc : LotConsts E.c η) (hη : 0 ≤ η) (hnd : E.nodes.Nodup) {i : ℕ}
    {s : EpochState} (hs : (s.lead.map Note.id).Nodup) {ζ : ℝ} (hζ : 0 ≤ ζ)
    (hsH : Small E.c s (honNotes E i s E.nodes) ζ) (hsA : Small E.c s (advNotes s) ζ)
    {β ℓlo ℓhi μ w : ℝ} (hβ0 : 0 ≤ β) (hβ1 : β < 1) (hμ : μ < 1) (hw0 : 0 ≤ w) (hw1 : w ≤ 1)
    (hst : StakeTSI E i s β ℓlo ℓhi μ w) {a : Member} {ms : List Member} (hch : Chained a ms)
    (hlo : a.ylo ≤ (1 - β) * ℓlo) (hhi : ℓhi ≤ (1 - μ) * ((a :: ms).getLast (List.cons_ne_nil a ms)).yhi)
    (hok : ∀ m ∈ a :: ms, m.OK η ζ) (hadv : ∀ m ∈ a :: ms, m.AdvOK β ℓhi μ w) :
    ∃ m ∈ a :: ms, SlotBand m.B E i s := by
  obtain ⟨V, hV1, hV2, hV3, hV4⟩ := hst.tsi
  set H : ℝ := (stakeOf (honNotes E i s E.nodes) : ℝ) with hH
  set A : ℝ := (stakeOf (advNotes s) : ℝ) with hA
  have hH0 : 0 ≤ H := by positivity
  have hA0 : 0 ≤ A := by positivity
  have hD : (0 : ℝ) < s.D := by have := hsH.D_pos; exact_mod_cast (by omega : 0 < s.D)
  have hl0 : 0 ≤ lam0 E.c := by unfold lam0; positivity
  have hyH : expo E.c s (honNotes E i s E.nodes) = lam0 E.c * H / s.D := rfl
  have hyA : expo E.c s (advNotes s) = lam0 E.c * A / s.D := rfl
  have hfrac := hst.frac
  -- the honest exponent's range
  have hY1 : (1 - β) * ℓlo ≤ expo E.c s (honNotes E i s E.nodes) := by
    rw [hyH, le_div_iff₀ hD]
    have h1 : (1 - β) * (H + A) ≤ H := by linarith
    have h2 : ℓlo * s.D ≤ lam0 E.c * (H + A) := le_trans hV3 (mul_le_mul_of_nonneg_left hV2 hl0)
    nlinarith [mul_le_mul_of_nonneg_left h1 hl0]
  have hY2 : (1 - μ) * expo E.c s (honNotes E i s E.nodes) + (1 - w) * expo E.c s (advNotes s) ≤ ℓhi := by
    rw [hyH, hyA]
    have e : (1 - μ) * (lam0 E.c * H / s.D) + (1 - w) * (lam0 E.c * A / s.D) =
        lam0 E.c * ((1 - μ) * H + (1 - w) * A) / s.D := by field_simp
    rw [e, div_le_iff₀ hD]
    have := mul_le_mul_of_nonneg_left hV1 hl0
    nlinarith
  have hYA0 : 0 ≤ expo E.c s (advNotes s) := by rw [hyA]; positivity
  have hY3 : expo E.c s (honNotes E i s E.nodes) ≤ ((a :: ms).getLast (List.cons_ne_nil a ms)).yhi := by
    have : (1 - μ) * expo E.c s (honNotes E i s E.nodes) ≤ (1 - μ) * ((a :: ms).getLast (List.cons_ne_nil a ms)).yhi := by
      nlinarith [mul_nonneg (by linarith : (0 : ℝ) ≤ 1 - w) hYA0]
    exact le_of_mul_le_mul_left this (by linarith)
  obtain ⟨m, hm, hm1, hm2⟩ := cover_chain _ a ms hch (le_trans hlo hY1) hY3
  refine ⟨m, hm, slotBand_of_member hc hη hnd hs hζ hsH hsA (hok m hm) hm1 hm2 ?_⟩
  -- the adversary's exponent
  have hfr : (1 - β) * expo E.c s (advNotes s) ≤ β * expo E.c s (honNotes E i s E.nodes) := by
    rw [hyH, hyA, mul_div_assoc', mul_div_assoc', div_le_div_iff_of_pos_right hD]
    nlinarith [mul_le_mul_of_nonneg_left hfrac hl0]
  rcases hadv m hm with h | ⟨hw, h⟩
  · have : (1 - β) * expo E.c s (advNotes s) ≤ (1 - β) * m.ahi := by nlinarith
    exact le_of_mul_le_mul_left this (by linarith)
  · have : (1 - w) * expo E.c s (advNotes s) ≤ (1 - w) * m.ahi := by
      nlinarith [mul_le_mul_of_nonneg_left hm1 (by linarith : (0 : ℝ) ≤ 1 - μ)]
    exact le_of_mul_le_mul_left this hw

/-! ## The first epoch -/

/-- In the first epoch, every slot's lottery runs under the genesis state. -/
theorem σE_epoch0 (E : Env) (es : List Event) {i : ℕ} (hi : i < E.c.epochLength) : σE E es i = es0 E := by
  unfold σE CS Config.epochOf
  rw [Nat.div_eq_of_lt hi, if_pos rfl]

/-- The genesis state does not involve the oracle. -/
theorem es0_withO (E : Env) (O : Oracle) : es0 (E.withO O) = es0 E := rfl

theorem any_congr' {α : Type*} (K : List α) (f g : α → Bool) (h : ∀ x ∈ K, f x = g x) : K.any f = K.any g := by
  induction K with
  | nil => rfl
  | cons a K ih =>
    simp only [List.any_cons]
    rw [h a (by simp), ih fun x hx => h x (by simp [hx])]

theorem honNotes_congr {i i' : ℕ} (s : EpochState) {K : List ℕ} (h : ∀ j ∈ K, E.online j i = E.online j i') :
    honNotes E i s K = honNotes E i' s K := by
  unfold honNotes
  congr 1
  funext n
  exact any_congr' K _ _ fun j hj => by rw [h j hj]

theorem qhRO_congr {i i' : ℕ} (s : EpochState) (h : ∀ j ∈ E.nodes, E.online j i = E.online j i') :
    qhRO E i s = qhRO E i' s := by
  have hK : ∀ K : List ℕ, (∀ j ∈ K, j ∈ E.nodes) → honNotes E i s K = honNotes E i' s K :=
    fun K hK => honNotes_congr s fun j hj => h j (hK j hj)
  have hz : pZero E i s = pZero E i' s := by unfold pZero; rw [hK E.nodes fun _ hj => hj]
  have ho : pOne E i s = pOne E i' s := by
    unfold pOne
    rw [hz]
    exact congrArg List.sum (List.map_congr_left fun j _ => by
      rw [hK (E.nodes.erase j) fun _ hk => List.mem_of_mem_erase hk])
  unfold qhRO
  rw [hz, ho]

theorem slotBand_congr {B : Band} {i i' : ℕ} {s : EpochState} (h : ∀ j ∈ E.nodes, E.online j i = E.online j i')
    (hb : SlotBand B E i s) : SlotBand B E i' s :=
  ⟨hb.nodup, qhRO_congr s h ▸ hb.hon, hb.adv⟩

/-- **The genesis band.** If every honest node is online throughout the first epoch,
the adversary holds at most `β` of the genesis stake, and all genesis stake is
participating (`H + A = D`), then one member's band holds at every slot of the
first epoch. -/
theorem genesis_member (hc : LotConsts E.c η) (hη : 0 ≤ η) (hnd : E.nodes.Nodup) {ζ : ℝ} (hζ : 0 ≤ ζ)
    (hEL' : 0 < E.c.epochLength) (hon : ∀ j ∈ E.nodes, ∀ i < E.c.epochLength, E.online j i = true)
    (hs : ((es0 E).lead.map Note.id).Nodup)
    (hsH : Small E.c (es0 E) (honNotes E 0 (es0 E) E.nodes) ζ) (hsA : Small E.c (es0 E) (advNotes (es0 E)) ζ)
    {β : ℝ} (hβ0 : 0 ≤ β) (hβ1 : β < 1)
    (hfrac : (1 - β) * (stakeOf (advNotes (es0 E)) : ℝ) ≤ β * stakeOf (honNotes E 0 (es0 E) E.nodes))
    (hall : stakeOf (honNotes E 0 (es0 E) E.nodes) + stakeOf (advNotes (es0 E)) = (es0 E).D)
    {a : Member} {ms : List Member} (hch : Chained a ms)
    (hlo : a.ylo ≤ (1 - β) * lam0 E.c) (hhi : lam0 E.c ≤ ((a :: ms).getLast (List.cons_ne_nil a ms)).yhi)
    (hok : ∀ m ∈ a :: ms, m.OK η ζ) (hadv : ∀ m ∈ a :: ms, m.AdvOK β (lam0 E.c) 0 0) :
    ∃ m ∈ a :: ms, ∀ i < E.c.epochLength, SlotBand m.B E i (es0 E) := by
  have hEL : 0 < E.c.epochLength := hEL'
  have hst : StakeTSI E 0 (es0 E) β (lam0 E.c) (lam0 E.c) 0 0 := by
    refine ⟨hfrac, (es0 E).D, ?_, ?_, le_rfl, le_rfl⟩
    · have : ((stakeOf (honNotes E 0 (es0 E) E.nodes) + stakeOf (advNotes (es0 E)) : ℕ) : ℝ) = (es0 E).D := by
        exact_mod_cast hall
      push_cast at this; linarith
    · have : ((stakeOf (honNotes E 0 (es0 E) E.nodes) + stakeOf (advNotes (es0 E)) : ℕ) : ℝ) = (es0 E).D := by
        exact_mod_cast hall
      push_cast at this; linarith
  obtain ⟨m, hm, hsb⟩ := slotBand_of_stake hc hη hnd hs hζ hsH hsA hβ0 hβ1 (by norm_num) le_rfl (by norm_num)
    hst hch hlo (by simpa using hhi) hok hadv
  exact ⟨m, hm, fun i hi => slotBand_congr (fun j hj => by rw [hon j hj 0 hEL, hon j hj i hi]) hsb⟩

end Cryptarchia.Prob
