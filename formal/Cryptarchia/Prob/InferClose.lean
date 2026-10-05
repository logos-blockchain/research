import Cryptarchia.Spec.StakeInference

/-!
# The specification's stake-inference update, against exact arithmetic

`infer_close`: with learning rate `β = 1` (`betaP = PRECISION`), the fixed-point
`infer` (Rust's truncating division throughout) is within two stake units of the
exact update `max 1 (D · N / (PERIOD · f_p))`.
-/

namespace Cryptarchia

theorem tdiv_close (a b : ℤ) (hb : 0 < b) : |((a.tdiv b : ℤ) : ℝ) - (a : ℝ) / b| < 1 := by
  have h1 := Int.lt_tmod_of_pos a hb
  have h2 := Int.tmod_lt_of_pos a hb
  rw [Int.tmod_def] at h1 h2
  have hb' : (0 : ℝ) < b := by exact_mod_cast hb
  have e1 : ((-b : ℤ) : ℝ) < (a : ℝ) - b * (a.tdiv b : ℤ) := by exact_mod_cast h1
  have e2 : (a : ℝ) - b * (a.tdiv b : ℤ) < (b : ℝ) := by exact_mod_cast h2
  push_cast at e1
  set t : ℝ := ((a.tdiv b : ℤ) : ℝ)
  have l1 : ((a : ℝ) - b) / b < t := by rw [div_lt_iff₀ hb']; linarith
  have l2 : t < ((a : ℝ) + b) / b := by rw [lt_div_iff₀ hb']; linarith
  have e3 : ((a : ℝ) - b) / b = a / b - 1 := by field_simp
  have e4 : ((a : ℝ) + b) / b = a / b + 1 := by field_simp
  rw [abs_lt]; constructor <;> linarith

/-- **The specification's update is the exact one up to two stake units.** With
learning rate `β = 1` (`betaP = PRECISION`), the fixed-point `infer` (Rust's
truncating division throughout) differs from `max 1 (D · N / (PERIOD · f_p))`,
`f_p = fP / PRECISION`, by at most `1 + 1/PRECISION ≤ 2` units. The band
theorem is stated for the exact update; stake is counted in base units, so the
difference is a relative `2 / D`. -/
theorem infer_close (c : Config) (D N : ℕ) (hb : c.betaP = c.precision) (hp : 0 < c.precision)
    (hE : 0 < c.period * c.fP) :
    |((infer c D N : ℕ) : ℝ) - max 1 ((D : ℝ) * N * c.precision / (c.period * c.fP))| ≤ 2 := by
  unfold infer
  simp only
  set tseP : ℤ := D * c.precision
  set expP : ℤ := c.period * c.fP
  set diffP : ℤ := expP - N * c.precision
  set errP : ℤ := Int.tdiv (tseP * diffP) expP with herr
  have hexp : (0 : ℤ) < expP := by simp only [expP]; exact_mod_cast hE
  have hprec : (0 : ℤ) < c.precision := by exact_mod_cast hp
  have hcorr : Int.tdiv (c.betaP * errP) c.precision = errP := by
    rw [hb]; exact Int.mul_tdiv_cancel_left errP (by omega)
  rw [hcorr]
  set newD : ℤ := Int.tdiv (tseP - errP) c.precision with hnew
  have c1 := tdiv_close (tseP * diffP) expP hexp
  have c2 := tdiv_close (tseP - errP) c.precision hprec
  rw [← herr] at c1
  rw [← hnew] at c2
  have c2' : |(newD : ℝ) - ((tseP - errP : ℤ) : ℝ) / (c.precision : ℝ)| < 1 := by
    have e : ((c.precision : ℤ) : ℝ) = (c.precision : ℝ) := by norm_cast
    rw [e] at c2; exact c2
  have hexpR : (0 : ℝ) < (expP : ℝ) := by exact_mod_cast hexp
  have hpR : (0 : ℝ) < (c.precision : ℝ) := by exact_mod_cast hp
  -- the exact value
  have hE' : (c.period : ℝ) * c.fP ≠ 0 := by
    have : (0 : ℝ) < (c.period : ℝ) * c.fP := by exact_mod_cast hE
    exact this.ne'
  have hexact : ((tseP - (tseP * diffP : ℤ) / expP : ℝ)) / c.precision =
      (D : ℝ) * N * c.precision / (c.period * c.fP) := by
    have hp1 : (c.period : ℝ) ≠ 0 := by intro h; apply hE'; rw [h, zero_mul]
    have hf1 : (c.fP : ℝ) ≠ 0 := by intro h; apply hE'; rw [h, mul_zero]
    simp only [tseP, diffP, expP]; push_cast
    field_simp
    ring
  have hnear : |(newD : ℝ) - (D : ℝ) * N * c.precision / (c.period * c.fP)| ≤ 2 := by
    rw [← hexact]
    have e : ((tseP - errP : ℤ) : ℝ) / c.precision - (tseP - (tseP * diffP : ℤ) / expP : ℝ) / c.precision =
        ((tseP * diffP : ℤ) / expP - errP : ℝ) / c.precision := by push_cast; ring
    have hq : |(((tseP * diffP : ℤ) : ℝ) / expP - errP) / c.precision| ≤ 1 := by
      rw [abs_div, abs_of_pos hpR, div_le_one hpR]
      have : (1 : ℝ) ≤ c.precision := by exact_mod_cast hp
      have c1' : |((tseP * diffP : ℤ) : ℝ) / expP - errP| < 1 := by rw [abs_sub_comm]; exact c1
      linarith
    calc |(newD : ℝ) - (tseP - (tseP * diffP : ℤ) / expP : ℝ) / c.precision|
        = |((newD : ℝ) - ((tseP - errP : ℤ) : ℝ) / c.precision) +
            (((tseP * diffP : ℤ) : ℝ) / expP - errP) / c.precision| := by rw [← e]; ring_nf
      _ ≤ |(newD : ℝ) - ((tseP - errP : ℤ) : ℝ) / c.precision| +
            |(((tseP * diffP : ℤ) : ℝ) / expP - errP) / c.precision| := abs_add_le _ _
      _ ≤ 2 := by linarith
  -- the clamp
  have hmax : (((max newD 1).toNat : ℕ) : ℝ) = max (newD : ℝ) 1 := by
    have h0 : ((max newD 1).toNat : ℤ) = max newD 1 := Int.toNat_of_nonneg (le_trans zero_le_one (le_max_right _ _))
    have : (((max newD 1).toNat : ℕ) : ℝ) = (((max newD 1).toNat : ℤ) : ℝ) := by norm_cast
    rw [this, h0]; push_cast; rfl
  rw [hmax]
  have hl : |max (newD : ℝ) 1 - max 1 ((D : ℝ) * N * c.precision / (c.period * c.fP))| ≤
      |(newD : ℝ) - (D : ℝ) * N * c.precision / (c.period * c.fP)| := by
    rw [max_comm (1 : ℝ)]; exact abs_max_sub_max_le_abs _ _ _
  linarith

end Cryptarchia
