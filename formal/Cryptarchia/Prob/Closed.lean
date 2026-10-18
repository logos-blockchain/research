module

public import Cryptarchia.Prob.Tail3E
public import Cryptarchia.Prob.TSIRO

/-!
# Closed-form bounds in the horizon and the depth

The settlement bound `settleEps3E` and the estimate's band `bandEps` depend on the depth
`k` and the horizon `N` only through lengths that grow with them. With the window,
span, empty-run and reach lengths proportional to `t = ⌊k/m⌋`, every term is
`(N + c) · A · qᵗ` for constants `A`, `q` fixed by finitely many numeric facts
(`settleEps3E_closed`, `bandEps_closed`). `Config.specK k` is the specification's
configuration with depth `k`.
-/

@[expose] public section

namespace Cryptarchia

namespace Config

theorem specK_kf (k : ℕ) : (specK k).kf = 30 * k := by
  simp [kf, specK, spec]; ring
theorem specK_epochLength (k : ℕ) : (specK k).epochLength = 300 * k := by
  simp [epochLength, specK_kf]; ring
theorem specK_period (k : ℕ) : (specK k).period = 180 * k := by
  simp [period, specK_kf]; ring
theorem specK_nonceOffset (k : ℕ) : (specK k).nonceOffset = 180 * k := by
  simp [nonceOffset, s, specK_kf]; ring
theorem specK_uncleWindow (k : ℕ) : (specK k).uncleWindow = 360 := by
  simp [uncleWindow, specK, spec]

theorem specK_sane {k : ℕ} (hk : 3 ≤ k) : (specK k).Sane :=
  ⟨by rw [specK_period, specK_nonceOffset], by rw [specK_nonceOffset, specK_epochLength]; omega,
    by rw [specK_uncleWindow, specK_nonceOffset, specK_epochLength]; omega,
    by rw [specK_nonceOffset]; omega, by rw [specK_nonceOffset, specK_epochLength]; omega⟩

end Config

namespace Prob

open Real

set_option maxHeartbeats 1000000 in
/-- **The settlement bound in closed form.** With `G' = g t`, `J = j t`, `Lw = w t`,
`r = ρ t`, `m t ≤ k < m (t + 1)` and `nbD ≥ nb t - nb0`, each term of `settleEps3E` is
at most a constant times `qᵗ`, given bounds on its bases. -/
theorem settleEps3E_closed (E : Env) (B : Band) {Δ : ℕ} (P : Cert2 B Δ) {lpi : ℝ}
    {Ccap N G G' J Lw r T t g j w ρ m nb nb0 : ℕ} {x yy : ℝ}
    (hG' : G' = g * t) (hJ : J = j * t) (hLw : Lw = w * t) (hr : r = ρ * t)
    (hk1 : m * t ≤ E.c.k) (hk2 : E.c.k + 1 ≤ m * (t + 1)) (hnb : nb * t ≤ nbD E Δ G T + nb0)
    (hhi0 : 0 ≤ B.hhi) (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1)
    (hx : 1 ≤ x) (hyy0 : 0 < yy) (hyy1 : yy ≤ 1) (hlpi : 0 < lpi) (he2 : 0 ≤ P.e 2)
    {A1 q2 A3 q3 A4 q4 A5 q5 A6 q6 A7 q7 : ℝ}
    (h1 : (1 - (1 - B.hhi) ^ Δ) ^ (G / Δ) ≤ A1)
    (h2 : (1 - B.hlo) ^ g ≤ q2)
    (h3a : P.e 17 / P.τ ≤ A3) (h3 : P.e 17 ^ j / P.τ ^ w ≤ q3)
    (h4a : (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) ≤ A4) (h4 : lpi ^ j ≤ q4)
    (h5a : 1 / x ≤ A5) (h5 : (1 + (x - 1) * (1 - B.elo)) ^ w / x ^ m ≤ q5)
    (h6a : (1 + (P.b - 1) / (1 - P.lr)) / P.c ≤ A6) (h6 : 1 / P.c ^ ρ ≤ q6)
    (hb0 : 0 < 1 + (yy - 1) * PT 1 yy B.hlo B.hhi T)
    (h7a : (1 / (1 + (yy - 1) * PT 1 yy B.hlo B.hhi T)) ^ nb0 * (1 / yy) ^ m ≤ A7)
    (h7 : (1 + (yy - 1) * PT 1 yy B.hlo B.hhi T) ^ nb / yy ^ (m + ρ) ≤ q7) :
    settleEps3E E B P lpi Ccap N G G' J Lw r T x yy ≤
      ((N : ℝ) + G' + 1) * A1 + ((N : ℝ) + 1) * q2 ^ t + ((N : ℝ) + G' + 1) * (A3 * q3 ^ t) +
        ((N : ℝ) + G' + 1) * (A4 * q4 ^ t) + ((N : ℝ) + 1) * (A5 * q5 ^ t) + ((N : ℝ) + G + 1) * (A6 * q6 ^ t) +
        (nEp E N : ℝ) * (A7 * q7 ^ t) := by
  have hc := P.hc
  have hτ := P.hτ
  have he17 := P.he17
  have hlr : P.lr < 1 := P.hlr1
  have hb1 := P.hb1
  have hlr0 : 0 < 1 - P.lr := by linarith
  have hstat : 0 ≤ 1 + (P.b - 1) / (1 - P.lr) := by
    have : 0 ≤ P.b - 1 := by linarith
    positivity
  have hN0 : (0 : ℝ) ≤ N := Nat.cast_nonneg _
  have hNG : (0 : ℝ) ≤ (N : ℝ) + G' + 1 := by positivity
  have hN1 : (0 : ℝ) ≤ (N : ℝ) + 1 := by positivity
  have hNGG : (0 : ℝ) ≤ (N : ℝ) + G + 1 := by positivity
  unfold settleEps3E
  -- long phases
  have e1 := mul_le_mul_of_nonneg_left h1 hNG
  -- long empty runs
  have e2 : ((N : ℝ) + 1) * (1 - B.hlo) ^ G' ≤ ((N : ℝ) + 1) * q2 ^ t := by
    rw [hG', pow_mul]
    exact mul_le_mul_of_nonneg_left (pow_le_pow_left₀ (pow_nonneg (by linarith) _) h2 _) hN1
  -- spans
  have e3 : ((N : ℝ) + G' + 1) * (P.e 17 ^ (J + 1) / P.τ ^ (Lw + 1)) ≤ ((N : ℝ) + G' + 1) * (A3 * q3 ^ t) := by
    refine mul_le_mul_of_nonneg_left ?_ hNG
    have : P.e 17 ^ (J + 1) / P.τ ^ (Lw + 1) = P.e 17 / P.τ * (P.e 17 ^ j / P.τ ^ w) ^ t := by
      rw [hJ, hLw, pow_succ, pow_succ, pow_mul, pow_mul, div_pow]; field_simp
    rw [this]
    exact mul_le_mul h3a (pow_le_pow_left₀ (by positivity) h3 _) (by positivity) (le_trans (by positivity) h3a)
  -- failed checks
  have e4 : ((N : ℝ) + G' + 1) * (lpi ^ J * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr))) ≤
      ((N : ℝ) + G' + 1) * (A4 * q4 ^ t) := by
    refine mul_le_mul_of_nonneg_left ?_ hNG
    have hX : 0 ≤ (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) := by
      have := P.hlp0; positivity
    calc lpi ^ J * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr))
        = (lpi ^ j) ^ t * ((P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr))) := by
          rw [hJ, pow_mul]; ring
      _ ≤ q4 ^ t * A4 := mul_le_mul (pow_le_pow_left₀ (by positivity) h4 _) h4a hX
          (pow_nonneg (le_trans (by positivity) h4) _)
      _ = A4 * q4 ^ t := by ring
  -- crowded windows
  have e5 : ((N : ℝ) + 1) * ((1 + (x - 1) * (1 - B.elo)) ^ Lw / x ^ (E.c.k + 1)) ≤ ((N : ℝ) + 1) * (A5 * q5 ^ t) := by
    refine mul_le_mul_of_nonneg_left ?_ hN1
    have hx0 : 0 < x := by linarith
    have hw0 : 0 ≤ 1 + (x - 1) * (1 - B.elo) := by nlinarith
    have hxk : x ^ (m * t + 1) ≤ x ^ (E.c.k + 1) := pow_le_pow_right₀ hx (by omega)
    calc (1 + (x - 1) * (1 - B.elo)) ^ Lw / x ^ (E.c.k + 1)
        ≤ (1 + (x - 1) * (1 - B.elo)) ^ Lw / x ^ (m * t + 1) :=
          div_le_div_of_nonneg_left (pow_nonneg hw0 _) (by positivity) hxk
      _ = 1 / x * ((1 + (x - 1) * (1 - B.elo)) ^ w / x ^ m) ^ t := by
          rw [hLw, pow_mul, pow_succ, pow_mul, div_pow]; field_simp
      _ ≤ A5 * q5 ^ t := mul_le_mul h5a (pow_le_pow_left₀ (by positivity) h5 _) (by positivity)
          (le_trans (by positivity) h5a)
  -- large reach
  have e6 : ((N : ℝ) + G + 1) * ((1 + (P.b - 1) / (1 - P.lr)) / P.c ^ (r + 1)) ≤ ((N : ℝ) + G + 1) * (A6 * q6 ^ t) := by
    refine mul_le_mul_of_nonneg_left ?_ hNGG
    have hc0 : 0 < P.c := by linarith
    calc (1 + (P.b - 1) / (1 - P.lr)) / P.c ^ (r + 1)
        = (1 + (P.b - 1) / (1 - P.lr)) / P.c * (1 / P.c ^ ρ) ^ t := by
          rw [hr, pow_succ, mul_comm ρ t, pow_mul', div_pow, one_pow]; field_simp
      _ ≤ A6 * q6 ^ t := mul_le_mul h6a (pow_le_pow_left₀ (by positivity) h6 _) (by positivity)
          (le_trans (by positivity) h6a)
  -- slow growth
  have e7 : (nEp E N : ℝ) * ((1 + (yy - 1) * PT 1 yy B.hlo B.hhi T) ^ nbD E Δ G T / yy ^ (E.c.k + r)) ≤
      (nEp E N : ℝ) * (A7 * q7 ^ t) := by
    refine mul_le_mul_of_nonneg_left ?_ (Nat.cast_nonneg _)
    set bs := 1 + (yy - 1) * PT 1 yy B.hlo B.hhi T with hbs
    have hPT01 : 0 ≤ PT 1 yy B.hlo B.hhi T ∧ PT 1 yy B.hlo B.hhi T ≤ 1 := by
      unfold PT; split_ifs
      · have h0 := pow_nonneg (by linarith : 0 ≤ 1 - B.hhi) T
        have h1 := pow_le_one₀ (n := T) (by linarith : 0 ≤ 1 - B.hhi) (by linarith)
        constructor <;> linarith
      · have h0 := pow_nonneg (by linarith : 0 ≤ 1 - B.hlo) T
        have h1 := pow_le_one₀ (n := T) (by linarith : 0 ≤ 1 - B.hlo) (by linarith)
        constructor <;> linarith
    have hbs1 : bs ≤ 1 := by
      have : (yy - 1) * PT 1 yy B.hlo B.hhi T ≤ 0 := mul_nonpos_of_nonpos_of_nonneg (by linarith) hPT01.1
      simp only [hbs]; linarith
    have hpow : bs ^ nbD E Δ G T * bs ^ nb0 ≤ bs ^ (nb * t) := by
      rw [← pow_add]; exact pow_le_pow_of_le_one hb0.le hbs1 hnb
    have hb' : bs ^ nbD E Δ G T ≤ (1 / bs) ^ nb0 * (bs ^ nb) ^ t := by
      rw [← pow_mul, div_pow, one_pow, div_mul_eq_mul_div, one_mul, le_div_iff₀ (by positivity)]
      exact hpow
    have hyk : yy ^ ((m + ρ) * t + (m - 1)) ≤ yy ^ (E.c.k + r) :=
      pow_le_pow_of_le_one hyy0.le hyy1 (by
        rw [hr]
        have e1 : (m + ρ) * t = m * t + ρ * t := by ring
        have e2 : m * (t + 1) = m * t + m := by ring
        omega)
    calc bs ^ nbD E Δ G T / yy ^ (E.c.k + r)
        ≤ (1 / bs) ^ nb0 * (bs ^ nb) ^ t / yy ^ ((m + ρ) * t + (m - 1)) :=
          div_le_div₀ (by positivity) hb' (by positivity) hyk
      _ = ((1 / bs) ^ nb0 * (1 / yy) ^ (m - 1)) * (bs ^ nb / yy ^ (m + ρ)) ^ t := by
          rw [pow_add, pow_mul, div_pow (bs ^ nb), div_pow (1 : ℝ) yy, one_pow]; field_simp
      _ ≤ A7 * q7 ^ t := by
          have hm1 : (1 / yy) ^ (m - 1) ≤ (1 / yy) ^ m :=
            pow_le_pow_right₀ (by rw [le_div_iff₀ hyy0]; linarith) (by omega)
          have h7a' : (1 / bs) ^ nb0 * (1 / yy) ^ (m - 1) ≤ A7 :=
            le_trans (mul_le_mul_of_nonneg_left hm1 (by positivity)) h7a
          exact mul_le_mul h7a' (pow_le_pow_left₀ (by positivity) h7 _) (by positivity)
            (le_trans (by positivity) h7a')
  linarith

/-- **The estimate's band in closed form**: with the period at least `p0 t`, each of the
two Chernoff terms is at most `exp(a) · exp(-p0 a)ᵗ`. -/
theorem bandEps_closed (T : TBand) {P t p0 : ℕ} (hP : p0 * t ≤ P) (hT : 0 ≤ T.ylo * T.clo) (hδ1 : T.δ ≤ 1) :
    bandEps T P ≤ exp (T.ylo * T.clo * T.δ ^ 2 / 2) * exp (-(p0 * (T.ylo * T.clo * T.δ ^ 2 / 2))) ^ t +
      exp (T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)) *
        exp (-(p0 * (T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)))) ^ t := by
  unfold bandEps
  have hP' : ((p0 * t : ℕ) : ℝ) ≤ P := by exact_mod_cast hP
  push_cast at hP'
  have ha1 : 0 ≤ T.ylo * T.clo * T.δ ^ 2 / 2 := by positivity
  have ha2 : 0 ≤ T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ) := by
    have : 0 ≤ 1 / 2 - 2 / 9 * T.δ := by linarith
    positivity
  have key : ∀ a : ℝ, 0 ≤ a → exp (-(((P : ℝ) - 1) * a)) ≤ exp a * exp (-(p0 * a)) ^ t := by
    intro a ha
    rw [← exp_nat_mul, ← exp_add]
    apply exp_le_exp.2
    nlinarith
  refine add_le_add ?_ ?_
  · have := key _ ha1; convert this using 2; ring
  · have := key _ ha2; convert this using 2; ring

/-! ## The configuration family's derived constants -/

theorem Kc_specK (k : ℕ) : Kc (Config.specK k) = 1000 / ((180 * k : ℝ) * 33) := by
  unfold Kc; rw [Config.specK_period]; simp [Config.specK, Config.spec]

theorem lam0_specK (k : ℕ) : lam0 (Config.specK k) = lam0 Config.spec := rfl

/-- The upper drift condition at depth `k0` gives it at every larger depth: `Kc · (P - 1)`
grows with the period. -/
theorem hup_of_k0 {L C : ℝ} {k k0 : ℕ} (hk : k0 ≤ k) (hk0 : 1 ≤ k0) (hC : 0 ≤ C)
    (h : L ≤ C * (1000 / ((180 * k0 : ℝ) * 33)) * ((180 * k0 : ℝ) - 1)) :
    L ≤ C * Kc (Config.specK k) * (((Config.specK k).period : ℝ) - 1) := by
  rw [Kc_specK, Config.specK_period]
  push_cast
  have hk0' : (1 : ℝ) ≤ k0 := by exact_mod_cast hk0
  have hkk : (k0 : ℝ) ≤ k := by exact_mod_cast hk
  have e : ∀ x : ℝ, 0 < x → 1000 / (180 * x * 33) * (180 * x - 1) = 1000 / 33 * (1 - 1 / (180 * x)) := by
    intro x hx; field_simp
  rw [mul_assoc, e (k : ℝ) (by linarith)]
  rw [mul_assoc, e (k0 : ℝ) (by linarith)] at h
  refine h.trans (mul_le_mul_of_nonneg_left ?_ hC)
  have : 1 / (180 * (k : ℝ)) ≤ 1 / (180 * k0) := by
    apply one_div_le_one_div_of_le (by positivity); linarith
  nlinarith

/-- The lower drift condition at depth `k0` gives it at every larger depth: `Kc · P` is
constant and `Kc` falls with the period. -/
theorem hdn_of_k0 {a b c : ℝ} {k k0 : ℕ} (hk : k0 ≤ k) (hk0 : 1 ≤ k0) (hb : 0 ≤ b)
    (h : a * (1000 / 33) + 1000 / ((180 * k0 : ℝ) * 33) * b + c ≤ 1) :
    a * Kc (Config.specK k) * ((Config.specK k).period : ℝ) + Kc (Config.specK k) * b + c ≤ 1 := by
  rw [Kc_specK, Config.specK_period]
  push_cast
  have hk0' : (1 : ℝ) ≤ k0 := by exact_mod_cast hk0
  have hkk : (k0 : ℝ) ≤ k := by exact_mod_cast hk
  have hk' : (0 : ℝ) < k := by linarith
  have e1 : a * (1000 / (180 * (k : ℝ) * 33)) * (180 * k) = a * (1000 / 33) := by field_simp
  have e2 : 1000 / (180 * (k : ℝ) * 33) ≤ 1000 / (180 * k0 * 33) := by
    apply div_le_div_of_nonneg_left (by norm_num) (by positivity); nlinarith
  rw [e1]
  nlinarith [mul_le_mul_of_nonneg_right e2 hb]

/-- **A geometric term under a slower rate**: from `t0` on, `A qᵗ ≤ R Qᵗ` when `q ≤ Q` and
`R` bounds `A (q / Q)^t0`. -/
theorem geom_le_of {A q Q R : ℝ} {t0 t : ℕ} (hA : 0 ≤ A) (hq : 0 ≤ q) (hQ : 0 < Q) (hqQ : q ≤ Q)
    (ht : t0 ≤ t) (hR : A * (q ^ t0 / Q ^ t0) ≤ R) : A * q ^ t ≤ R * Q ^ t := by
  obtain ⟨s, rfl⟩ := Nat.exists_eq_add_of_le ht
  have hQ0 : 0 < Q ^ t0 := pow_pos hQ _
  calc A * q ^ (t0 + s) = A * (q ^ t0 / Q ^ t0) * (Q ^ t0 * q ^ s) := by
        rw [pow_add]; field_simp
    _ ≤ R * (Q ^ t0 * Q ^ s) :=
        mul_le_mul hR (mul_le_mul_of_nonneg_left (pow_le_pow_left₀ hq hqQ s) hQ0.le)
          (by positivity) ((mul_nonneg hA (by positivity)).trans hR)
    _ = R * Q ^ (t0 + s) := by rw [pow_add]

/-- The epochs an execution up to `N` reaches, with the analysis' margin. -/
theorem div_lt_add_two {a b c : ℕ} (hb : b < c) : (a + b) / c < a / c + 2 := by
  have hc : 0 < c := by omega
  have : (a + b) / c ≤ (a + c) / c := Nat.div_le_div_right (by omega)
  rw [Nat.add_div_right _ hc] at this
  omega

/-- The lottery constants of the family are the specification's. -/
theorem lotConsts_specK {η : ℝ} (h : LotConsts Config.spec η) (k : ℕ) : LotConsts (Config.specK k) η :=
  ⟨h.p_pos, h.t0_pos, h.t1_le, h.a1_le, h.a1_near⟩

end Prob

end Cryptarchia
