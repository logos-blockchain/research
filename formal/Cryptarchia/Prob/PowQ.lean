module

public import Cryptarchia.Prob.FamQ
public import Cryptarchia.Prob.Tail3E
public import Cryptarchia.Prob.TSIRO
public import Cryptarchia.Prob.ExpBound
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.NNRat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.Height.NumberField
import Mathlib.NumberTheory.Height.Projectivization
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.SelbergSieve
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.Tactic.Echelon.Zsqrtd
import Mathlib.Tactic.NormNum.Irrational
import Mathlib.Tactic.NormNum.IsCoprime
import Mathlib.Tactic.NormNum.IsSquare
import Mathlib.Tactic.NormNum.LegendreSymbol
import Mathlib.Tactic.NormNum.ModEq
import Mathlib.Tactic.NormNum.NatFib
import Mathlib.Tactic.NormNum.NatLog
import Mathlib.Tactic.NormNum.NatSqrt
import Mathlib.Tactic.NormNum.Ordinal
import Mathlib.Tactic.NormNum.Parity
import Mathlib.Tactic.NormNum.Prime
import Mathlib.Tactic.NormNum.RealSqrt
import Mathlib.Topology.Sheaves.Init

/-!
# Numeric bounds by computation

A certificate bounds large powers (`β ^ n` with `n` up to about `10 ^ 5`). `powUpQ` and `powDnQ`
compute them by binary powering, rounding every step outward to `d` significant digits, so
the numbers stay short; each is a bound on the exact power (`pow_le_powUpQ`, `powDnQ_le_pow`).
`settleEps3EQ` is `settleEps3E` with these bounds for its powers, and `settleEps3E_le_Q` bounds
one by the other once a few signs check (`settleChkQ`); likewise `bandEpsQ` for the estimate's
band (`bandEps_le_Q`). A certificate's bounds are then kernel evaluations, with no chain of
numeric steps.
-/

@[expose] public section

namespace Cryptarchia.Prob

theorem rdnQ_nonneg (d : ℕ) {x : ℚ} (hx : 0 ≤ x) : 0 ≤ rdnQ d x := by
  unfold rdnQ
  split_ifs with h
  · exact le_rfl
  · have hq : (0 : ℚ) < 10 ^ (flog10Q x - d + 1) := zpow_pos (by norm_num) _
    exact mul_nonneg (by exact_mod_cast Int.floor_nonneg.2 (div_nonneg hx hq.le)) hq.le

/-! ## Powers by binary powering, rounded outward -/

/-- `x ^ n` from above: binary powering with fuel `f`, each step rounded up to `d` digits
(the exact power once the fuel runs out). -/
def powUpF (d : ℕ) (x : ℚ) : ℕ → ℕ → ℚ
  | 0, n => x ^ n
  | f + 1, n =>
    if n = 0 then 1 else
      rupQ d (powUpF d x f (n / 2) * powUpF d x f (n / 2) * (if n % 2 = 1 then x else 1))

/-- `x ^ n` from below, likewise. -/
def powDnF (d : ℕ) (x : ℚ) : ℕ → ℕ → ℚ
  | 0, n => x ^ n
  | f + 1, n =>
    if n = 0 then 1 else
      rdnQ d (powDnF d x f (n / 2) * powDnF d x f (n / 2) * (if n % 2 = 1 then x else 1))

/-- `x ^ n` from above, to `d` significant digits. -/
def powUpQ (d : ℕ) (x : ℚ) (n : ℕ) : ℚ := powUpF d x 64 n

/-- `x ^ n` from below, to `d` significant digits. -/
def powDnQ (d : ℕ) (x : ℚ) (n : ℕ) : ℚ := powDnF d x 64 n

theorem pow_split (x : ℚ) (n : ℕ) : x ^ n = x ^ (n / 2) * x ^ (n / 2) * (if n % 2 = 1 then x else 1) := by
  rw [← pow_add]
  split_ifs with h
  · rw [← pow_succ]; congr 1; omega
  · rw [mul_one]; congr 1; omega

theorem pow_le_powUpF (d : ℕ) {x : ℚ} (hx : 0 ≤ x) : ∀ f n, x ^ n ≤ powUpF d x f n
  | 0, n => le_rfl
  | f + 1, n => by
    unfold powUpF
    by_cases h0 : n = 0
    · subst h0; simp
    · rw [if_neg h0]
      have ih := pow_le_powUpF d hx f (n / 2)
      have h1 : 0 ≤ x ^ (n / 2) := pow_nonneg hx _
      have h2 : (0 : ℚ) ≤ if n % 2 = 1 then x else 1 := by split_ifs <;> linarith
      rw [pow_split x n]
      exact le_trans (mul_le_mul_of_nonneg_right (mul_le_mul ih ih h1 (h1.trans ih)) h2) (le_rupQ d _)

theorem powDnF_le_pow (d : ℕ) {x : ℚ} (hx : 0 ≤ x) : ∀ f n, 0 ≤ powDnF d x f n ∧ powDnF d x f n ≤ x ^ n
  | 0, n => ⟨pow_nonneg hx n, le_rfl⟩
  | f + 1, n => by
    unfold powDnF
    by_cases h0 : n = 0
    · subst h0; simp
    · rw [if_neg h0]
      obtain ⟨ih0, ih⟩ := powDnF_le_pow d hx f (n / 2)
      have h2 : (0 : ℚ) ≤ if n % 2 = 1 then x else 1 := by split_ifs <;> linarith
      refine ⟨rdnQ_nonneg d (mul_nonneg (mul_nonneg ih0 ih0) h2), ?_⟩
      rw [pow_split x n]
      exact le_trans (rdnQ_le d _) (mul_le_mul_of_nonneg_right (mul_le_mul ih ih ih0 (ih0.trans ih)) h2)

theorem pow_le_powUpQ (d : ℕ) {x : ℚ} (hx : 0 ≤ x) (n : ℕ) : (x : ℝ) ^ n ≤ (powUpQ d x n : ℝ) := by
  exact_mod_cast pow_le_powUpF d hx 64 n

theorem powDnQ_le_pow (d : ℕ) {x : ℚ} (hx : 0 ≤ x) (n : ℕ) : (powDnQ d x n : ℝ) ≤ (x : ℝ) ^ n := by
  exact_mod_cast (powDnF_le_pow d hx 64 n).2

/-! ## The settlement bound -/

/-- `settleEps3E` over `ℚ`, its powers bounded outward to `d` digits: `k` the depth, `ne` and `nb`
the values of `nEp` and `nbD`. -/
def settleEps3EQ (d Δ : ℕ) (Bq : BandR) (e17 τ lp e2 b lr c lpi x yy : ℚ) (k ne nb Ccap N G G' J Lw r T : ℕ) : ℚ :=
  (N + G' + 1) * powUpQ d (1 - (1 - Bq.hhi) ^ Δ) (G / Δ) +
  (N + 1) * powUpQ d (1 - Bq.hlo) G' +
  (N + G' + 1) * (powUpQ d e17 (J + 1) / powDnQ d τ (Lw + 1)) +
  (N + G' + 1) * (powUpQ d lpi J * powUpQ d (lp / lpi) Ccap * e2 * (1 + (b - 1) / (1 - lr))) +
  (N + 1) * (powUpQ d (1 + (x - 1) * (1 - Bq.elo)) Lw / powDnQ d x (k + 1)) +
  (N + G + 1) * ((1 + (b - 1) / (1 - lr)) / powDnQ d c (r + 1)) +
  ne * (powUpQ d (1 + (yy - 1) * (if 1 ≤ yy then 1 - (1 - Bq.hhi) ^ T else 1 - (1 - Bq.hlo) ^ T)) nb /
    powDnQ d yy (k + r))

/-- The signs `settleEps3E_le_Q` needs. -/
def settleChkQ (d Δ : ℕ) (Bq : BandR) (e17 τ lp e2 b lr c lpi x yy : ℚ) (k Ccap Lw r T : ℕ) : Bool :=
  decide (0 ≤ 1 - (1 - Bq.hhi) ^ Δ) && decide (0 ≤ 1 - Bq.hlo) && decide (0 ≤ e17) &&
    decide (0 < powDnQ d τ (Lw + 1)) && decide (0 ≤ lpi) && decide (0 ≤ lp / lpi) && decide (0 ≤ e2) &&
    decide (0 ≤ 1 + (b - 1) / (1 - lr)) && decide (0 ≤ 1 + (x - 1) * (1 - Bq.elo)) &&
    decide (0 < powDnQ d x (k + 1)) && decide (0 < powDnQ d c (r + 1)) &&
    decide (0 ≤ 1 + (yy - 1) * (if 1 ≤ yy then 1 - (1 - Bq.hhi) ^ T else 1 - (1 - Bq.hlo) ^ T)) &&
    decide (0 ≤ yy) && decide (0 < powDnQ d yy (k + r)) && decide (0 ≤ τ) && decide (0 ≤ x) && decide (0 ≤ c)

theorem div_le_div_of_bounds {a A b B : ℝ} (ha : 0 ≤ a) (hA : a ≤ A) (hB0 : 0 < B) (hB : B ≤ b) : a / b ≤ A / B :=
  div_le_div₀ (ha.trans hA) hA hB0 hB

/-- **The settlement bound, bounded by computation.** -/
theorem settleEps3E_le_Q {Δ : ℕ} {E : Env} {B : Band} (P : Cert2 B Δ) (Bq : BandR) (hB : B = Bq.toBand)
    {d : ℕ} {e17 τ lp e2 b lr c lpi x yy : ℚ} (h17 : P.e 17 = e17) (hτ : P.τ = τ) (hlp : P.lp = lp)
    (h2 : P.e 2 = e2) (hb : P.b = b) (hlr : P.lr = lr) (hc : P.c = c) {k ne nb Ccap N G G' J Lw r T : ℕ}
    (hk : E.c.k = k) (hne : nEp E N = ne) (hnb : nbD E Δ G T = nb)
    (hchk : settleChkQ d Δ Bq e17 τ lp e2 b lr c lpi x yy k Ccap Lw r T = true) :
    settleEps3E E B P lpi Ccap N G G' J Lw r T x yy ≤
      (settleEps3EQ d Δ Bq e17 τ lp e2 b lr c lpi x yy k ne nb Ccap N G G' J Lw r T : ℝ) := by
  simp only [settleChkQ, Bool.and_eq_true, decide_eq_true_eq] at hchk
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨c1, c2⟩, c3⟩, c4⟩, c5⟩, c6⟩, c7⟩, c8⟩, c9⟩, c10⟩, c11⟩, c12⟩, c13⟩, c14⟩, c15⟩, c16⟩, c17⟩ := hchk
  subst hB
  unfold settleEps3E PT settleEps3EQ
  rw [hk, hne, hnb, h17, hτ, hlp, h2, hb, hlr, hc]
  simp only [BandR.toBand_hhi, BandR.toBand_hlo, BandR.toBand_elo]
  set ptQ : ℚ := if (1 : ℚ) ≤ yy then 1 - (1 - Bq.hhi) ^ T else 1 - (1 - Bq.hlo) ^ T with hptQ
  have hpt : (if (1 : ℝ) ≤ yy then 1 - (1 - (Bq.hhi : ℝ)) ^ T else 1 - (1 - (Bq.hlo : ℝ)) ^ T) = (ptQ : ℝ) := by
    rw [hptQ]
    by_cases h : (1 : ℚ) ≤ yy
    · have hR : (1 : ℝ) ≤ yy := by exact_mod_cast h
      rw [if_pos hR, if_pos h]; push_cast; ring
    · have hR : ¬ (1 : ℝ) ≤ yy := by exact_mod_cast h
      rw [if_neg hR, if_neg h]; push_cast; ring
  rw [hpt]
  have hF : (0 : ℝ) ≤ 1 + ((b : ℝ) - 1) / (1 - lr) := by exact_mod_cast c8
  have e2n : (0 : ℝ) ≤ e2 := by exact_mod_cast c7
  -- each term
  have t1 := pow_le_powUpQ d c1 (G / Δ)
  have t2 := pow_le_powUpQ d c2 G'
  have t3 := div_le_div_of_bounds (pow_nonneg (by exact_mod_cast c3) _) (pow_le_powUpQ d c3 (J + 1))
    (by exact_mod_cast c4) (powDnQ_le_pow d c15 (Lw + 1))
  have t4a := pow_le_powUpQ d c5 J
  have t4b := pow_le_powUpQ d c6 Ccap
  have hl : (0 : ℝ) ≤ (lpi : ℝ) ^ J := pow_nonneg (by exact_mod_cast c5) _
  have hr : (0 : ℝ) ≤ ((lp / lpi : ℚ) : ℝ) ^ Ccap := pow_nonneg (by exact_mod_cast c6) _
  have t4 := mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right (mul_le_mul t4a t4b hr (hl.trans t4a)) e2n) hF
  have t5 := div_le_div_of_bounds (pow_nonneg (by exact_mod_cast c9) _) (pow_le_powUpQ d c9 Lw)
    (by exact_mod_cast c10) (powDnQ_le_pow d c16 (k + 1))
  have t6 := div_le_div_of_nonneg_left hF (by exact_mod_cast c11) (powDnQ_le_pow d c17 (r + 1))
  have t7 := div_le_div_of_bounds (pow_nonneg (by exact_mod_cast c12) _) (pow_le_powUpQ d c12 nb)
    (by exact_mod_cast c14) (powDnQ_le_pow d c13 (k + r))
  push_cast at t1 t2 t3 t4 t5 t6 t7 ⊢
  gcongr
  all_goals first
    | exact t1 | exact t2 | exact t3 | exact t4 | exact t5 | exact t6 | exact t7

/-! ## The estimate's band -/

/-- `TBand` with rational constants. -/
structure TBandQ where
  ℓlo : ℚ
  ℓhi : ℚ
  μ : ℚ
  β : ℚ
  δ : ℚ
  η : ℚ
  ζ : ℚ

noncomputable def TBandQ.toTBand (T : TBandQ) : TBand := ⟨T.ℓlo, T.ℓhi, T.μ, T.β, T.δ, T.η, T.ζ⟩

namespace TBandQ

variable (T : TBandQ)

def Yh : ℚ := T.ℓhi / (1 - T.μ)

def ylo : ℚ := (1 - T.β) * T.ℓlo

def clo : ℚ := 1 - T.Yh / 2 - 2 * errHiQ T.η T.ζ T.Yh / T.ylo

theorem ylo_cast : (T.ylo : ℝ) = T.toTBand.ylo := by
  simp only [ylo, TBand.ylo, toTBand]; push_cast; ring

theorem clo_cast : (T.clo : ℝ) = T.toTBand.clo := by
  simp only [clo, TBand.clo, TBand.Yh, TBand.ylo, Yh, ylo, toTBand]; push_cast; rw [errHiQ_cast]; push_cast; ring

/-- The exponents of `bandEps`. -/
def a1 (P : ℕ) : ℚ := ((P : ℚ) - 1) * (T.ylo * T.clo) * T.δ ^ 2 / 2

def a2 (P : ℕ) : ℚ := ((P : ℚ) - 1) * (T.ylo * T.clo) * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)

end TBandQ

/-- `bandEps` from above: `exp (-a) ≤ 1 / (1 + a / n) ^ n`, the power bounded below to `d` digits. -/
def bandEpsQ (d n : ℕ) (T : TBandQ) (P : ℕ) : ℚ :=
  1 / powDnQ d (1 + T.a1 P / n) n + 1 / powDnQ d (1 + T.a2 P / n) n

/-- The signs `bandEps_le_Q` needs. -/
def bandChkQ (d n : ℕ) (T : TBandQ) (P : ℕ) : Bool :=
  decide (0 < n) && decide (0 ≤ T.a1 P) && decide (0 ≤ T.a2 P) && decide (0 < powDnQ d (1 + T.a1 P / n) n) &&
    decide (0 < powDnQ d (1 + T.a2 P / n) n)

/-- **The estimate's band, bounded by computation.** -/
theorem bandEps_le_Q {d n : ℕ} {T : TBandQ} {P : ℕ} (h : bandChkQ d n T P = true) :
    bandEps T.toTBand P ≤ (bandEpsQ d n T P : ℝ) := by
  simp only [bandChkQ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨hn, h1⟩, h2⟩, h3⟩, h4⟩ := h
  have e1 : ∀ a : ℚ, 0 ≤ a → 0 < powDnQ d (1 + a / n) n →
      Real.exp (-(a : ℝ)) ≤ ((1 / powDnQ d (1 + a / n) n : ℚ) : ℝ) := fun a ha hp => by
    have hb : (0 : ℚ) ≤ 1 + a / n := by positivity
    have := exp_neg_le_of (a := a) (a0 := a) (Q := (powDnQ d (1 + a / n) n : ℝ)) n hn (by exact_mod_cast ha) le_rfl (by exact_mod_cast hp)
      (by have := powDnQ_le_pow d hb n; push_cast at this; exact this)
    push_cast; exact this
  unfold bandEps bandEpsQ
  push_cast
  have q1 := e1 _ h1 h3
  have q2 := e1 _ h2 h4
  simp only [TBandQ.a1, TBandQ.a2] at q1 q2
  push_cast at q1 q2
  rw [← T.ylo_cast, ← T.clo_cast]
  have hδ : T.toTBand.δ = (T.δ : ℝ) := rfl
  rw [hδ]
  exact add_le_add q1 q2

/-! ## Single powers -/

/-- `b ^ n ≤ q'`, from `powUpQ`. -/
theorem pow_le_of_powUpQ {b q' : ℝ} {bq q : ℚ} (d n : ℕ) (hb : b = bq) (hq : (q : ℝ) = q') (h0 : 0 ≤ bq)
    (h : powUpQ d bq n ≤ q) : b ^ n ≤ q' := by
  subst hb hq
  exact (pow_le_powUpQ d h0 n).trans (by exact_mod_cast h)

/-- `q' ≤ b ^ n`, from `powDnQ`. -/
theorem le_pow_of_powDnQ {b q' : ℝ} {bq q : ℚ} (d n : ℕ) (hb : b = bq) (hq : (q : ℝ) = q') (h0 : 0 ≤ bq)
    (h : q ≤ powDnQ d bq n) : q' ≤ b ^ n := by
  subst hb hq
  exact (show ((q : ℚ) : ℝ) ≤ powDnQ d bq n by exact_mod_cast h).trans (powDnQ_le_pow d h0 n)
