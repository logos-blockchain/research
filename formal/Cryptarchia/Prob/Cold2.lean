module

public import Cryptarchia.Prob.Potential2
public import Cryptarchia.Prob.Cold
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Algebra.Order.Ring.Star
import Mathlib.Algebra.Order.Star.Real
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.Int.Star
import Mathlib.Data.NNRat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.Height.NumberField
import Mathlib.NumberTheory.Height.Projectivization
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.SelbergSieve
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.RingTheory.WittVector.IsPoly
import Mathlib.Tactic.ENatToNat
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
import Mathlib.Tactic.Polynomial.Basic
import Mathlib.Tactic.ReduceModChar
import Mathlib.Topology.Sheaves.Init
import Std.Tactic.BVDecide.Normalize.BitVec
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# The cold condition, sharper

The same bad event as `Cold.lean` (a margin that is not cold), bounded with the
two-term potential `V2` and with expectations over a phase taken through the
automaton of `Auto.lean`. The potential contracts by `λp` per phase in every state
(`ex_post2`), checked state class by state class: warm with positive or zero
reach, and cold with reach `0, 1, 2, ≥ 3` and margin `-1` or `≤ -2`.

The certificate (`Cert2`) holds the parameters and, for each of 19 expectations
over one phase, a solution of the automaton recursion.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle

/-- A terminal table by the adversarial count: `t0`, `t1`, `t2` for `min(A, 2)`. -/
def gtab (t0 t1 t2 : Bool → Bool → ℝ) : Fin 3 → Bool → Bool → ℝ := fun a b u =>
  if a.val = 0 then t0 b u else if a.val = 1 then t1 b u else t2 b u

/-- The 19 expectations over one phase, by number: adversary factor `x`, tilt `θ`, table `g`. -/
noncomputable def xgN (c z s d τ : ℝ) : ℕ → ℝ × ℝ × (Fin 3 → Bool → Bool → ℝ)
  -- warm, positive reach; and the reach recursion
  | 0 => (c, 1, gtab (fun b _ => if b then c⁻¹ else 1) (fun b _ => if b then c⁻¹ else 1) (fun b _ => if b then c⁻¹ else 1))
  -- warm, zero reach; and the reach recursion from zero
  | 1 => (c, 1, fun _ _ _ => 1)
  -- the next phase's adversarial slots, if it is not empty
  | 2 => (z, 1, gtab (fun b _ => if b then 1 else 0) (fun _ _ => 1) (fun _ _ => 1))
  -- cold, margin -1, term a, reach 0 / ≥ 1
  | 3 => (c, 1, gtab (fun b _ => if b then z⁻¹ else 1) (fun _ _ => z / s) (fun _ _ => z / s))
  | 4 => (c, 1, gtab (fun b _ => if b then (c * z)⁻¹ else 1) (fun _ _ => z / s) (fun _ _ => z / s))
  -- cold, margin ≤ -2, term a, reach 0 / ≥ 1
  | 5 => (c * z, 1, gtab (fun b _ => if b then z⁻¹ else 1) (fun b _ => if b then z⁻¹ else 1) (fun b _ => if b then s⁻¹ else 1))
  | 6 => (c * z, 1, gtab (fun b _ => if b then (c * z)⁻¹ else 1) (fun b _ => if b then (c * z)⁻¹ else 1)
      (fun b _ => if b then s⁻¹ else 1))
  -- cold, margin -1, term b, reach 0, 1, 2, ≥ 3
  | 7 => (d * z, 1, gtab (fun b _ => if b then z⁻¹ else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 8 => (d * z, 1, gtab (fun b _ => if b then (d * z)⁻¹ else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 9 => (d * z, 1, gtab (fun b u => if b then (if u then (d * d * z)⁻¹ else (d * z)⁻¹) else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 10 => (d * z, 1, gtab (fun b u => if u then 0 else if b then (d * z)⁻¹ else 1) (fun _ _ => 0) (fun _ _ => 0))
  -- cold, margin ≤ -2, term b, reach 0, 1, 2, ≥ 3
  | 11 => (d * z, 1, fun _ b _ => if b then z⁻¹ else 1)
  | 12 => (d * z, 1, fun _ b _ => if b then (d * z)⁻¹ else 1)
  | 13 => (d * z, 1, fun _ b u => if b then (if u then (d * d * z)⁻¹ else (d * z)⁻¹) else 1)
  | 14 => (d * z, 1, fun _ b u => if u then 0 else if b then (d * z)⁻¹ else 1)
  -- cold, reach ≥ 3, the absolute part (two honest slots), margin -1 / ≤ -2
  | 15 => (z, 1, gtab (fun _ u => if u then z⁻¹ else 0) (fun _ _ => 0) (fun _ _ => 0))
  | 16 => (z, 1, fun _ _ u => if u then z⁻¹ else 0)
  -- phase length, for the span
  | 17 => (1, τ, fun _ _ _ => 1)
  | _ => (1, 1, fun _ _ _ => 1)

/-- The 19 expectations over one phase. -/
noncomputable def xg (c z s d τ : ℝ) (i : Fin 19) : ℝ × ℝ × (Fin 3 → Bool → Bool → ℝ) := xgN c z s d τ i.val

/-- **The certificate.** -/
structure Cert2 (B : Band) (Δ : ℕ) where
  c : ℝ
  z : ℝ
  s : ℝ
  κ : ℝ
  d : ℝ
  τ : ℝ
  lp : ℝ
  lr : ℝ
  b : ℝ
  /-- solutions of the automaton recursions -/
  v : Fin 19 → ℕ → Fin 3 → Bool → ℝ
  /-- the expectations they give -/
  e : Fin 19 → ℝ
  hc : 1 ≤ c
  hz : 1 ≤ z
  hs : 1 ≤ s
  hκ : 0 ≤ κ
  hd0 : 0 < d
  hd1 : d ≤ 1
  hsz : s + κ ≤ z
  hτ : 1 ≤ τ
  hlp0 : 0 ≤ lp
  hlp : lp < 1
  hlr0 : 0 ≤ lr
  hlr1 : lr < 1
  hb1 : 1 ≤ b
  helo : 0 ≤ B.elo
  hΔ : 0 < Δ
  /-- the family of bands the automaton bounds cover; `B` is weaker than each -/
  Bs : List Band
  weak : ∀ B' ∈ Bs, B.Weaker B'
  sol : ∀ i, ∀ B' ∈ Bs, AutoSol B' Δ (xg c z s d τ i).1 (xg c z s d τ i).2.1 (xg c z s d τ i).2.2 (v i)
  he : ∀ i, ∀ B' ∈ Bs, autoBound B' (xg c z s d τ i).1 (xg c z s d τ i).2.1 (xg c z s d τ i).2.2 (v i) ≤ e i
  /-- the span base is at least one -/
  he17 : 1 ≤ e 17
  /-- reach recursion -/
  hlr : e 0 ≤ lr
  hb : e 1 ≤ b
  /-- warm, positive reach -/
  w1 : e 0 ≤ lp
  /-- warm, zero reach: a crossing has probability at least the pattern's -/
  w0 : e 1 - (1 - (s + κ) * z⁻¹) * (B.slo * B.elo ^ Δ) ≤ lp
  /-- cold classes, margin -1, reach 0, 1, 2 -/
  m1r0 : s * (e 3 - lp) + κ * (e 7 - lp) ≤ 0
  m1r1 : s * c * (e 4 - lp) + κ * d * (e 8 - lp) ≤ 0
  m1r2 : s * c ^ 2 * (e 4 - lp) + κ * d ^ 2 * (e 9 - lp) ≤ 0
  /-- cold, margin -1, reach ≥ 3 -/
  m1r3a : e 4 ≤ lp
  m1r3 : s * c ^ 3 * (e 4 - lp) + κ * d ^ 3 * max (e 10 - lp) 0 + κ * e 15 ≤ 0
  /-- cold classes, margin ≤ -2 -/
  m2r0 : s * (e 5 - lp) + κ * (e 11 - lp) ≤ 0
  m2r1 : s * c * (e 6 - lp) + κ * d * (e 12 - lp) ≤ 0
  m2r2 : s * c ^ 2 * (e 6 - lp) + κ * d ^ 2 * (e 13 - lp) ≤ 0
  m2r3a : e 6 ≤ lp
  m2r3 : s * c ^ 3 * (e 6 - lp) + κ * d ^ 3 * max (e 14 - lp) 0 + κ * e 16 ≤ 0

/-! ## Pointwise bounds -/

theorem Wt2_one (x : ℝ) (g : Fin 3 → Bool → Bool → ℝ) (m : ℕ) (h : List Out) :
    Wt2 x 1 g m h = x ^ advCnt (strOf h) m h.length *
      g (acap (advCnt (strOf h) m h.length)) (decide (1 ≤ honCnt (strOf h) m h.length))
        (decide (2 ≤ honCnt (strOf h) m h.length)) := by
  unfold Wt2; rw [one_pow, one_mul]

/-- The reach bound after a phase, as a shift: `ρ' = ρ + A - min(H, ρ)`. -/
theorem max_shift (ρ A H : ℤ) (hρ : 0 ≤ ρ) (hH : 0 ≤ H) :
    max (ρ + A - H) A = ρ + (A - min H ρ) := by
  rcases le_total H ρ with h | h
  · rw [min_eq_left h, max_eq_left (by omega)]; ring
  · rw [min_eq_right h, max_eq_right (by omega)]; ring

theorem zpow_shift {x : ℝ} (hx : 0 < x) (ρ A H : ℤ) (hρ : 0 ≤ ρ) (hH : 0 ≤ H) :
    x ^ (max (ρ + A - H) A) = x ^ ρ * x ^ (A - min H ρ) := by
  rw [max_shift ρ A H hρ hH, zpow_add₀ hx.ne']

theorem acap_two {n : ℕ} (h : 2 ≤ n) : (acap n).val = 2 := by unfold acap; simp; omega
theorem acap_pos {n : ℕ} (h : 1 ≤ n) : (acap n).val ≠ 0 := by unfold acap; simp; omega

/-! ### Factor inequalities -/

section Factors

/-- Honest-depth credit: `c^(-min(H, ρ)) z^(-H) ≤ B ? (c^[ρ ≥ 1] z)⁻¹ : 1`. -/
theorem credit_le {c z : ℝ} (hc : 1 ≤ c) (hz : 1 ≤ z) {H nh : ℕ} {ρ : ℤ} (hρ : 0 ≤ ρ) (hHn : H ≤ nh)
    (hHb : 1 ≤ nh → 1 ≤ H) :
    c ^ (-(min (H : ℤ) ρ)) * z ^ (-(H : ℤ)) ≤
      (if 1 ≤ nh then (if 1 ≤ ρ then (c * z)⁻¹ else z⁻¹) else 1) := by
  have hc0 : 0 < c := by linarith
  have hz0 : 0 < z := by linarith
  split_ifs with hb hr
  · have h1 : c ^ (-(min (H : ℤ) ρ)) ≤ c⁻¹ := by
      rw [← zpow_neg_one]; exact zpow_le_zpow_right₀ hc (by have := hHb hb; omega)
    have h2 : z ^ (-(H : ℤ)) ≤ z⁻¹ := by
      rw [← zpow_neg_one]; exact zpow_le_zpow_right₀ hz (by have := hHb hb; omega)
    rw [mul_inv]
    exact mul_le_mul h1 h2 (by positivity) (by positivity)
  · have h1 : c ^ (-(min (H : ℤ) ρ)) ≤ 1 := zpow_le_one_of_nonpos₀ hc (by omega)
    have h2 : z ^ (-(H : ℤ)) ≤ z⁻¹ := by
      rw [← zpow_neg_one]; exact zpow_le_zpow_right₀ hz (by have := hHb hb; omega)
    calc c ^ (-(min (H : ℤ) ρ)) * z ^ (-(H : ℤ)) ≤ 1 * z⁻¹ := mul_le_mul h1 h2 (by positivity) zero_le_one
      _ = z⁻¹ := one_mul _
  · have hH0 : H = 0 := by omega
    rw [hH0, Nat.cast_zero, neg_zero, zpow_zero, mul_one, min_eq_left hρ, neg_zero, zpow_zero]

end Factors

/-- The weight of expectation `i` at a history, for a phase started at `m`. -/
noncomputable def WP {B : Band} {Δ : ℕ} (P : Cert2 B Δ) (i : Fin 19) (m : ℕ) (h : List Out) : ℝ :=
  Wt2 (xg P.c P.z P.s P.d P.τ i).1 (xg P.c P.z P.s P.d P.τ i).2.1 (xg P.c P.z P.s P.d P.τ i).2.2 m h

/-- Term `a` of a cold class. -/
def iaOf (st : ℤ × ℤ) : Fin 19 := if st.2 = -1 then (if st.1 = 0 then 3 else 4) else (if st.1 = 0 then 5 else 6)

/-- Term `b` of a cold class. -/
def ibOf (st : ℤ × ℤ) : Fin 19 :=
  if st.2 = -1 then (if st.1 = 0 then 7 else if st.1 = 1 then 8 else if st.1 = 2 then 9 else 10)
  else (if st.1 = 0 then 11 else if st.1 = 1 then 12 else if st.1 = 2 then 13 else 14)

/-- The absolute term of a cold class with reach at least 3. -/
def iabsOf (st : ℤ × ℤ) : Fin 19 := if st.2 = -1 then 15 else 16

variable {B : Band} {Δ : ℕ}

/-- The bound for the potential after one phase. -/
noncomputable def postB2 (P : Cert2 B Δ) (st : ℤ × ℤ) (m : ℕ) (h : List Out) : ℝ :=
  if 1 ≤ st.1 ∧ st.2 = st.1 then P.c ^ st.1 * WP P 0 m h
  else if st.2 < 0 then
    P.s * P.c ^ st.1 * P.z ^ st.2 * WP P (iaOf st) m h + P.κ * P.d ^ st.1 * P.z ^ st.2 * WP P (ibOf st) m h +
      (if 3 ≤ st.1 then P.κ * P.z ^ st.2 * WP P (iabsOf st) m h else 0)
  else WP P 1 m h - (1 - (P.s + P.κ) * P.z⁻¹) * crossG 1 m h

theorem WP_nonneg (P : Cert2 B Δ) (i : Fin 19) (m : ℕ) (h : List Out) (hi : i ≠ 17) : 0 ≤ WP P i m h := by
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have hs0 : 0 < P.s := by linarith [P.hs]
  have hd0 : 0 < P.d := P.hd0
  unfold WP Wt2
  fin_cases i <;> simp only [xg, xgN, gtab] <;> first | (exact absurd rfl hi) | (split_ifs <;> positivity) | positivity

theorem WP_val (P : Cert2 B Δ) (i : Fin 19) (m : ℕ) (h : List Out) (hi : i ≠ 17) :
    WP P i m h = (xg P.c P.z P.s P.d P.τ i).1 ^ advCnt (strOf h) m h.length *
      (xg P.c P.z P.s P.d P.τ i).2.2 (acap (advCnt (strOf h) m h.length))
        (decide (1 ≤ honCnt (strOf h) m h.length)) (decide (2 ≤ honCnt (strOf h) m h.length)) := by
  unfold WP
  have : (xg P.c P.z P.s P.d P.τ i).2.1 = 1 := by
    fin_cases i <;> first | rfl | exact absurd rfl hi
  rw [this, Wt2_one]

/-- The factor of term `b`: `d^(-min(H, ρ)) z^(-H)`, by reach class. -/
theorem dterm_le {d z : ℝ} (hd0 : 0 < d) (hd1 : d ≤ 1) (hz : 1 ≤ z) {H nh : ℕ} {ρ : ℤ} (hρ : 0 ≤ ρ)
    (hHn : H ≤ nh) (hHb : 1 ≤ nh → 1 ≤ H) (h3 : 3 ≤ ρ → nh ≤ 1) :
    d ^ (-(min (H : ℤ) ρ)) * z ^ (-(H : ℤ)) ≤
      (if ρ = 0 then (if 1 ≤ nh then z⁻¹ else 1)
       else if ρ = 1 then (if 1 ≤ nh then (d * z)⁻¹ else 1)
       else if ρ = 2 then (if 1 ≤ nh then (if 2 ≤ nh then (d * d * z)⁻¹ else (d * z)⁻¹) else 1)
       else (if 1 ≤ nh then (d * z)⁻¹ else 1)) := by
  have hz0 : 0 < z := by linarith
  have hzH : ∀ k : ℕ, k ≤ H → z ^ (-(H : ℤ)) ≤ (z ^ k)⁻¹ := by
    intro k hk; rw [← zpow_natCast, ← zpow_neg]; exact zpow_le_zpow_right₀ hz (by omega)
  have hdm : ∀ k : ℕ, (min (H : ℤ) ρ) ≤ k → d ^ (-(min (H : ℤ) ρ)) ≤ (d ^ k)⁻¹ := by
    intro k hk; rw [← zpow_natCast, ← zpow_neg]; exact zpow_le_zpow_right_of_le_one₀ hd0 hd1 (by omega)
  by_cases hb : 1 ≤ nh
  · have hH1 := hHb hb
    split_ifs with r0 r1 r2 u2
    · subst r0; simp only [min_eq_right (show (0 : ℤ) ≤ H by positivity), neg_zero, zpow_zero, one_mul]
      simpa using hzH 1 hH1
    · subst r1
      have e : min (H : ℤ) 1 = 1 := min_eq_right (by exact_mod_cast hH1)
      rw [e, mul_inv, zpow_neg_one]
      exact mul_le_mul_of_nonneg_left (by simpa using hzH 1 hH1) (by positivity)
    · subst r2
      calc d ^ (-(min (H : ℤ) 2)) * z ^ (-(H : ℤ)) ≤ (d ^ 2)⁻¹ * (z ^ 1)⁻¹ :=
            mul_le_mul (hdm 2 (min_le_right _ _)) (hzH 1 hH1) (by positivity) (by positivity)
        _ = (d * d * z)⁻¹ := by rw [pow_one, pow_two]; field_simp
    · subst r2
      have hH1' : H = 1 := by
        have := hHn; omega
      calc d ^ (-(min (H : ℤ) 2)) * z ^ (-(H : ℤ)) ≤ (d ^ 1)⁻¹ * (z ^ 1)⁻¹ :=
            mul_le_mul (hdm 1 (by rw [hH1']; simp)) (hzH 1 hH1) (by positivity) (by positivity)
        _ = (d * z)⁻¹ := by rw [pow_one, pow_one, mul_inv]
    · have hρ3 : 3 ≤ ρ := by omega
      have hH1' : H = 1 := by have := h3 hρ3; omega
      calc d ^ (-(min (H : ℤ) ρ)) * z ^ (-(H : ℤ)) ≤ (d ^ 1)⁻¹ * (z ^ 1)⁻¹ :=
            mul_le_mul (hdm 1 (by rw [hH1']; simp)) (hzH 1 hH1) (by positivity) (by positivity)
        _ = (d * z)⁻¹ := by rw [pow_one, pow_one, mul_inv]
  · have hH0 : H = 0 := by omega
    simp only [hH0, Nat.cast_zero, min_eq_left hρ, neg_zero, zpow_zero, mul_one, hb, ↓reduceIte]
    split_ifs <;> rfl

theorem xg_0 (c z s d τ : ℝ) : xg c z s d τ 0 = xgN c z s d τ 0 := rfl
theorem xg_1 (c z s d τ : ℝ) : xg c z s d τ 1 = xgN c z s d τ 1 := rfl
theorem xg_2 (c z s d τ : ℝ) : xg c z s d τ 2 = xgN c z s d τ 2 := rfl
theorem xg_3 (c z s d τ : ℝ) : xg c z s d τ 3 = xgN c z s d τ 3 := rfl
theorem xg_4 (c z s d τ : ℝ) : xg c z s d τ 4 = xgN c z s d τ 4 := rfl
theorem xg_5 (c z s d τ : ℝ) : xg c z s d τ 5 = xgN c z s d τ 5 := rfl
theorem xg_6 (c z s d τ : ℝ) : xg c z s d τ 6 = xgN c z s d τ 6 := rfl
theorem xg_7 (c z s d τ : ℝ) : xg c z s d τ 7 = xgN c z s d τ 7 := rfl
theorem xg_8 (c z s d τ : ℝ) : xg c z s d τ 8 = xgN c z s d τ 8 := rfl
theorem xg_9 (c z s d τ : ℝ) : xg c z s d τ 9 = xgN c z s d τ 9 := rfl
theorem xg_10 (c z s d τ : ℝ) : xg c z s d τ 10 = xgN c z s d τ 10 := rfl
theorem xg_11 (c z s d τ : ℝ) : xg c z s d τ 11 = xgN c z s d τ 11 := rfl
theorem xg_12 (c z s d τ : ℝ) : xg c z s d τ 12 = xgN c z s d τ 12 := rfl
theorem xg_13 (c z s d τ : ℝ) : xg c z s d τ 13 = xgN c z s d τ 13 := rfl
theorem xg_14 (c z s d τ : ℝ) : xg c z s d τ 14 = xgN c z s d τ 14 := rfl
theorem xg_15 (c z s d τ : ℝ) : xg c z s d τ 15 = xgN c z s d τ 15 := rfl
theorem xg_16 (c z s d τ : ℝ) : xg c z s d τ 16 = xgN c z s d τ 16 := rfl
theorem xg_17 (c z s d τ : ℝ) : xg c z s d τ 17 = xgN c z s d τ 17 := rfl

theorem zpow_le_one' {a : ℝ} {n : ℤ} (h0 : 0 ≤ a) (h1 : a ≤ 1) (hn : 0 ≤ n) : a ^ n ≤ 1 := by
  obtain ⟨k, hk⟩ := Int.eq_ofNat_of_zero_le hn
  rw [hk, zpow_natCast]; exact pow_le_one₀ h0 h1

theorem acap_eq0 : acap 0 = 0 := rfl

/-- **The potential after one phase is at most `postB2`.** -/
theorem post2_le (P : Cert2 B Δ) {st : ℤ × ℤ} (hst : Inv st) (m : ℕ) (h : List Out) (hm : m ≤ h.length) :
    V2 P.c P.z P.s P.κ P.d (step Δ (strOf h) 0 m h.length st) ≤ postB2 P st m h := by
  classical
  have hc := P.hc; have hz := P.hz; have hs := P.hs; have hκ := P.hκ
  have hd0 := P.hd0; have hd1 := P.hd1
  have hc0 : 0 < P.c := by linarith
  have hz0 : 0 < P.z := by linarith
  have hs0 : 0 < P.s := by linarith
  have hsz : P.s ≤ P.z := by linarith [P.hsz]
  obtain ⟨h0, h1, h2⟩ := hst
  obtain ⟨A, hA⟩ : ∃ A, advCnt (strOf h) m h.length = A := ⟨_, rfl⟩
  obtain ⟨H, hH⟩ : ∃ H, hD Δ (strOf h) m h.length = H := ⟨_, rfl⟩
  obtain ⟨nh, hnh⟩ : ∃ nh, honCnt (strOf h) m h.length = nh := ⟨_, rfl⟩
  have hHn : H ≤ nh := by rw [← hH, ← hnh]; exact hD_le_honCnt _
  have hHb : 1 ≤ nh → 1 ≤ H := fun hb => by
    rw [← hH]; exact one_le_hD _ ((honIn_iff_honCnt).2 (by rw [hnh]; exact hb))
  have hHnn : (0 : ℤ) ≤ H := by positivity
  have WPe : ∀ i : Fin 19, i ≠ 17 → WP P i m h = (xg P.c P.z P.s P.d P.τ i).1 ^ A *
      (xg P.c P.z P.s P.d P.τ i).2.2 (acap A) (decide (1 ≤ nh)) (decide (2 ≤ nh)) := by
    intro i hi; rw [WP_val P i m h hi, hA, hnh]
  unfold postB2
  by_cases hwarm : 1 ≤ st.1 ∧ st.2 = st.1
  · rw [if_pos hwarm]
    obtain ⟨hρ, hμ⟩ := hwarm
    have hst : st = (st.1, st.1) := by ext <;> simp [hμ]
    have := V2_warm_step (Δ := Δ) (w := strOf h) (ℓ := 0) (a := m) (b := h.length) (z := P.z) (s := P.s)
      (κ := P.κ) (d := P.d) hc hρ
    rw [← hst, zpow_sub_ind hc0, hA] at this
    refine this.trans (le_of_eq ?_)
    rw [WPe 0 (by decide), xg_0]
    simp only [xgN, gtab]
    have hiff : HonIn (strOf h) m h.length ↔ 1 ≤ nh := by rw [← hnh]; exact honIn_iff_honCnt
    by_cases hb : 1 ≤ nh
    · rw [if_pos (hiff.2 hb)]; simp [hb]
    · rw [if_neg (fun h' => hb (hiff.1 h'))]; simp [hb]
  · rw [if_neg hwarm]
    by_cases hneg : st.2 < 0
    · rw [if_pos hneg]
      have hWb := WP_nonneg P (ibOf st) m h (by unfold ibOf; split_ifs <;> decide)
      have hsc : 0 ≤ P.s * P.c ^ st.1 * P.z ^ st.2 := by positivity
      have hkd : 0 ≤ P.κ * P.d ^ st.1 * P.z ^ st.2 := by positivity
      have hWabs : 0 ≤ (if 3 ≤ st.1 then P.κ * P.z ^ st.2 * WP P (iabsOf st) m h else 0) := by
        split_ifs
        · exact mul_nonneg (by positivity) (WP_nonneg P _ m h (by unfold iabsOf; split_ifs <;> decide))
        · exact le_rfl
      by_cases hstay : st.2 < -(A : ℤ)
      · have hstay' : st.2 < -(advCnt (strOf h) m h.length : ℤ) := by rw [hA]; exact hstay
        rw [V2_stay (by omega) hstay', hA, hH, zpow_shift hc0 _ _ _ h0 hHnn, zpow_shift hd0 _ _ _ h0 hHnn]
        have hzs : P.z ^ (st.2 + (A : ℤ) - H) = P.z ^ st.2 * (P.z ^ (A : ℤ) * P.z ^ (-(H : ℤ))) := by
          rw [← zpow_add₀ hz0.ne', ← zpow_add₀ hz0.ne']; ring_nf
        have hcs : P.c ^ ((A : ℤ) - min (H : ℤ) st.1) = P.c ^ (A : ℤ) * P.c ^ (-(min (H : ℤ) st.1)) := by
          rw [← zpow_add₀ hc0.ne']; ring_nf
        have hds : P.d ^ ((A : ℤ) - min (H : ℤ) st.1) = P.d ^ (A : ℤ) * P.d ^ (-(min (H : ℤ) st.1)) := by
          rw [← zpow_add₀ hd0.ne']; ring_nf
        rw [hzs, hcs, hds]
        have hcr := credit_le hc hz (H := H) (nh := nh) h0 hHn hHb
        -- term a
        have ta : P.c ^ (A : ℤ) * P.c ^ (-(min (H : ℤ) st.1)) * (P.z ^ (A : ℤ) * P.z ^ (-(H : ℤ))) ≤
            WP P (iaOf st) m h := by
          rw [WPe _ (by unfold iaOf; split_ifs <;> decide)]
          have hre : P.c ^ (A : ℤ) * P.c ^ (-(min (H : ℤ) st.1)) * (P.z ^ (A : ℤ) * P.z ^ (-(H : ℤ))) =
              (P.c * P.z) ^ A * (P.c ^ (-(min (H : ℤ) st.1)) * P.z ^ (-(H : ℤ))) := by
            rw [← zpow_natCast, mul_zpow]; ring
          rw [hre]
          unfold iaOf
          by_cases hm1 : st.2 = -1
          · have hA0 : A = 0 := by omega
            subst hA0
            rw [if_pos hm1]
            simp only [pow_zero, one_mul, acap_eq0]
            by_cases hr0 : st.1 = 0
            · rw [if_pos hr0, xg_3]; simp only [xgN, gtab, Fin.val_zero, ↓reduceIte]
              refine hcr.trans (le_of_eq ?_); simp [hr0]
            · rw [if_neg hr0, xg_4]; simp only [xgN, gtab, Fin.val_zero, ↓reduceIte]
              refine hcr.trans (le_of_eq ?_)
              have : 1 ≤ st.1 := by omega
              simp [this]
          · rw [if_neg hm1]
            have hge : (P.c * P.z)⁻¹ ≤ P.z⁻¹ := inv_anti₀ hz0 (by nlinarith)
            have hge2 : P.z⁻¹ ≤ P.s⁻¹ := inv_anti₀ hs0 hsz
            have hr1 : (if 1 ≤ nh then (if 1 ≤ st.1 then (P.c * P.z)⁻¹ else P.z⁻¹) else 1) ≤
                (if decide (1 ≤ nh) = true then P.s⁻¹ else 1) := by
              simp only [decide_eq_true_eq]
              split_ifs <;> linarith
            by_cases hr0 : st.1 = 0
            · rw [if_pos hr0, xg_5]; simp only [xgN]
              rw [mul_pow]
              apply mul_le_mul_of_nonneg_left _ (by positivity)
              refine hcr.trans ?_
              unfold gtab
              by_cases ha0 : (acap A).val = 0
              · simp [ha0, hr0]
              · by_cases ha1 : (acap A).val = 1
                · simp [ha1, hr0]
                · simp only [ha0, ha1, ↓reduceIte]; refine le_trans (le_of_eq ?_) hr1
                  simp [hr0]
            · rw [if_neg hr0, xg_6]; simp only [xgN]
              rw [mul_pow]
              apply mul_le_mul_of_nonneg_left _ (by positivity)
              refine hcr.trans ?_
              have hr1' : 1 ≤ st.1 := by omega
              unfold gtab
              by_cases ha0 : (acap A).val = 0
              · simp [ha0, hr1']
              · by_cases ha1 : (acap A).val = 1
                · simp [ha1, hr1']
                · simp only [ha0, ha1, ↓reduceIte]; exact hr1
        -- term b, and the absolute term
        by_cases hU : 3 ≤ st.1 ∧ 2 ≤ nh
        · rw [if_pos hU.1]
          have hdle : P.d ^ st.1 * P.d ^ (A : ℤ) * P.d ^ (-(min (H : ℤ) st.1)) ≤ 1 := by
            rw [← zpow_add₀ hd0.ne', ← zpow_add₀ hd0.ne']
            apply zpow_le_one' hd0.le hd1
            have : min (H : ℤ) st.1 ≤ st.1 := min_le_right _ _
            omega
          have hzle : P.z ^ (A : ℤ) * P.z ^ (-(H : ℤ)) ≤ P.z ^ A * P.z⁻¹ := by
            rw [zpow_natCast]
            apply mul_le_mul_of_nonneg_left _ (by positivity)
            rw [← zpow_neg_one]; exact zpow_le_zpow_right₀ hz (by have := hHb (by omega); omega)
          have hU2 : decide (2 ≤ nh) = true := by simpa using hU.2
          have tabs : P.κ * P.d ^ st.1 * (P.d ^ (A : ℤ) * P.d ^ (-(min (H : ℤ) st.1))) *
              (P.z ^ st.2 * (P.z ^ (A : ℤ) * P.z ^ (-(H : ℤ)))) ≤ P.κ * P.z ^ st.2 * WP P (iabsOf st) m h := by
            rw [WPe _ (by unfold iabsOf; split_ifs <;> decide)]
            calc P.κ * P.d ^ st.1 * (P.d ^ (A : ℤ) * P.d ^ (-(min (H : ℤ) st.1))) *
                (P.z ^ st.2 * (P.z ^ (A : ℤ) * P.z ^ (-(H : ℤ))))
                = P.κ * P.z ^ st.2 * ((P.d ^ st.1 * P.d ^ (A : ℤ) * P.d ^ (-(min (H : ℤ) st.1))) *
                    (P.z ^ (A : ℤ) * P.z ^ (-(H : ℤ)))) := by ring
              _ ≤ P.κ * P.z ^ st.2 * (1 * (P.z ^ A * P.z⁻¹)) := by
                  apply mul_le_mul_of_nonneg_left _ (by positivity)
                  exact mul_le_mul hdle hzle (by positivity) zero_le_one
              _ = _ := by
                  rw [one_mul]
                  unfold iabsOf
                  by_cases hm1 : st.2 = -1
                  · have hA0 : A = 0 := by omega
                    subst hA0
                    rw [if_pos hm1, xg_15]; simp [xgN, gtab, acap_eq0, hU2]
                  · rw [if_neg hm1, xg_16]; simp [xgN, hU2]
          have tb0 := mul_nonneg hkd hWb
          have ta' := mul_le_mul_of_nonneg_left ta hsc
          nlinarith
        · have h3 : 3 ≤ st.1 → nh ≤ 1 := fun h3 => by by_contra hc'; exact hU ⟨h3, by omega⟩
          have hdt := dterm_le hd0 hd1 hz (H := H) (nh := nh) h0 hHn hHb h3
          have tb : P.d ^ (A : ℤ) * P.d ^ (-(min (H : ℤ) st.1)) * (P.z ^ (A : ℤ) * P.z ^ (-(H : ℤ))) ≤
              WP P (ibOf st) m h := by
            rw [WPe _ (by unfold ibOf; split_ifs <;> decide)]
            have hre : P.d ^ (A : ℤ) * P.d ^ (-(min (H : ℤ) st.1)) * (P.z ^ (A : ℤ) * P.z ^ (-(H : ℤ))) =
                (P.d * P.z) ^ A * (P.d ^ (-(min (H : ℤ) st.1)) * P.z ^ (-(H : ℤ))) := by
              rw [← zpow_natCast, mul_zpow]; ring
            rw [hre]
            unfold ibOf
            by_cases hm1 : st.2 = -1
            · have hA0 : A = 0 := by omega
              subst hA0
              rw [if_pos hm1]
              simp only [pow_zero, one_mul, acap_eq0]
              refine hdt.trans (le_of_eq ?_)
              by_cases r0 : st.1 = 0
              · simp [r0, xg_7, xgN, gtab]
              · by_cases r1 : st.1 = 1
                · simp [r1, xg_8, xgN, gtab]
                · by_cases r2 : st.1 = 2
                  · simp [r2, xg_9, xgN, gtab]
                  · have hn1 : ¬ 2 ≤ nh := fun h2' => hU ⟨by omega, h2'⟩
                    simp [r0, r1, r2, xg_10, xgN, gtab, hn1]
            · rw [if_neg hm1]
              refine (mul_le_mul_of_nonneg_left hdt (by positivity)).trans (le_of_eq ?_)
              by_cases r0 : st.1 = 0
              · simp [r0, xg_11, xgN]
              · by_cases r1 : st.1 = 1
                · simp [r1, xg_12, xgN]
                · by_cases r2 : st.1 = 2
                  · simp [r2, xg_13, xgN]
                  · have hn1 : ¬ 2 ≤ nh := fun h2' => hU ⟨by omega, h2'⟩
                    simp [r0, r1, r2, xg_14, xgN, hn1]
          have ta' := mul_le_mul_of_nonneg_left ta hsc
          have tb' := mul_le_mul_of_nonneg_left tb hkd
          nlinarith
      · -- rewarm
        push Not at hstay
        have hstay' : -(advCnt (strOf h) m h.length : ℤ) ≤ st.2 := by rw [hA]; exact hstay
        rw [V2_rewarm (by omega) hneg hstay', hA, hH]
        have hρ' : max (st.1 + (A : ℤ) - H) A ≤ st.1 + A := by apply max_le <;> omega
        have hcA : P.c ^ (max (st.1 + (A : ℤ) - H) A) ≤ P.c ^ st.1 * P.c ^ A := by
          rw [← zpow_natCast, ← zpow_add₀ hc0.ne']; exact zpow_le_zpow_right₀ hc hρ'
        have ta : P.c ^ st.1 * P.c ^ A ≤ P.s * P.c ^ st.1 * P.z ^ st.2 * WP P (iaOf st) m h := by
          rw [WPe _ (by unfold iaOf; split_ifs <;> decide)]
          unfold iaOf
          by_cases hm1 : st.2 = -1
          · have hA1 : 1 ≤ A := by omega
            have hap := acap_pos hA1
            rw [if_pos hm1, hm1]
            have key : P.s * P.c ^ st.1 * P.z ^ (-1 : ℤ) * (P.c ^ A * (P.z / P.s)) = P.c ^ st.1 * P.c ^ A := by
              rw [zpow_neg_one]; field_simp
            by_cases hr0 : st.1 = 0
            · rw [if_pos hr0, xg_3]; simp only [xgN, gtab, hap, ↓reduceIte]
              by_cases ha1 : (acap A).val = 1 <;> simp only [ha1, ↓reduceIte] <;> rw [key]
            · rw [if_neg hr0, xg_4]; simp only [xgN, gtab, hap, ↓reduceIte]
              by_cases ha1 : (acap A).val = 1 <;> simp only [ha1, ↓reduceIte] <;> rw [key]
          · rw [if_neg hm1]
            have hA2 : 2 ≤ A := by omega
            have ha2 := acap_two hA2
            have hzA : 1 ≤ P.z ^ st.2 * P.z ^ A := by
              rw [← zpow_natCast, ← zpow_add₀ hz0.ne']; exact one_le_zpow₀ hz (by omega)
            have hy : P.s⁻¹ ≤ (if decide (1 ≤ nh) = true then P.s⁻¹ else 1) := by
              split_ifs
              · exact le_rfl
              · exact inv_le_one_of_one_le₀ hs
            have main : P.c ^ st.1 * P.c ^ A ≤ P.s * P.c ^ st.1 * P.z ^ st.2 *
                ((P.c * P.z) ^ A * (if decide (1 ≤ nh) = true then P.s⁻¹ else 1)) :=
              calc P.c ^ st.1 * P.c ^ A ≤ P.c ^ st.1 * P.c ^ A * (P.z ^ st.2 * P.z ^ A) :=
                    le_mul_of_one_le_right (by positivity) hzA
                _ = P.s * P.c ^ st.1 * P.z ^ st.2 * ((P.c * P.z) ^ A * P.s⁻¹) := by
                    rw [mul_pow]; field_simp
                _ ≤ _ := by
                    apply mul_le_mul_of_nonneg_left _ hsc
                    exact mul_le_mul_of_nonneg_left hy (by positivity)
            have hv : ∀ t0 t1 : Bool → Bool → ℝ, gtab t0 t1 (fun b _ => if b then P.s⁻¹ else 1) (acap A)
                (decide (1 ≤ nh)) (decide (2 ≤ nh)) = (if decide (1 ≤ nh) = true then P.s⁻¹ else 1) := by
              intro t0 t1; unfold gtab; simp [ha2]
            by_cases hr0 : st.1 = 0
            · rw [if_pos hr0, xg_5]; simp only [xgN]; rw [hv]; exact main
            · rw [if_neg hr0, xg_6]; simp only [xgN]; rw [hv]; exact main
        have tb0 := mul_nonneg hkd hWb
        nlinarith
    · -- warm, zero reach
      rw [if_neg hneg]
      push Not at hneg
      have hμ : st.2 = st.1 := by rcases h1 with h1 | h1 <;> [exact h1; omega]
      have hρ0 : st.1 = 0 := by by_contra hne; exact hwarm ⟨by omega, hμ⟩
      have hst : st = (0, 0) := by ext <;> simp [hρ0, hμ]
      rw [hst]
      have := V2_warm_zero (Δ := Δ) (w := strOf h) (ℓ := 0) (a := m) (b := h.length) (c := P.c) (z := P.z)
        (s := P.s) (κ := P.κ) (d := P.d)
      refine this.trans (le_of_eq ?_)
      rw [WPe 1 (by decide), xg_1, hA]
      unfold crossG
      simp only [xgN, mul_one, one_pow, one_mul, zpow_natCast]
      split_ifs <;> ring

variable {κ : Kern} {M : ℕ}

theorem xg_nonneg (P : Cert2 B Δ) (i : Fin 19) :
    0 ≤ (xg P.c P.z P.s P.d P.τ i).1 ∧ 0 ≤ (xg P.c P.z P.s P.d P.τ i).2.1 := by
  have hc0 : 0 ≤ P.c := by linarith [P.hc]
  have hz0 : 0 ≤ P.z := by linarith [P.hz]
  have hd0 : 0 ≤ P.d := P.hd0.le
  have hτ : 0 ≤ P.τ := by linarith [P.hτ]
  fin_cases i <;> simp only [xg, xgN] <;> constructor <;> first | positivity | norm_num | assumption

end Cryptarchia.Prob
