module

public import Cryptarchia.Prob.TSIRO
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
# Bounded stake drift

`StakePath`, the condition the band step needs on how stake moves between epochs, is
stated in the band's derived constants. Here it follows from a plain one
(`stakePath_of_drift`): from epoch `e` to `e + 1` stake moves by at most a factor `ρ`
(`StakeDrift`), and honest online stake is never below `Hmin` (`MinStake`), which
absorbs the fixed-point rounding. A certificate checks the two numeric conditions
linking `ρ` and `Hmin` to its band.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset

variable {E : Env} {T : TBand} {σ : ℕ → EpochState}

/-- All stake under `s` that slot `i`'s lottery counts: online honest and adversarial. -/
noncomputable def tstake (E : Env) (i : ℕ) (s : EpochState) : ℝ := hstake E i s + astake s

/-- **Stake drifts by at most a factor `ρ` from epoch `e` to `e + 1`.** At every slot of
epoch `e + 1`, honest online stake is at most `ρ` times that at any slot of epoch `e`'s
window, and all participating stake is at least `1/ρ` times that at any slot of the
window and at the epoch's first slot. -/
structure StakeDrift (E : Env) (σ : ℕ → EpochState) (ρ : ℝ) (e : ℕ) : Prop where
  hon : ∀ j, (e + 1) * E.c.epochLength ≤ j → j < (e + 2) * E.c.epochLength → ∀ k ∈ win E e,
    hstake E j (σ j) ≤ ρ * hstake E (k + 1) (σ (k + 1))
  tot : ∀ j, (e + 1) * E.c.epochLength ≤ j → j < (e + 2) * E.c.epochLength → ∀ k ∈ win E e,
    tstake E (k + 1) (σ (k + 1)) ≤ ρ * tstake E j (σ j)
  tot0 : ∀ j, (e + 1) * E.c.epochLength ≤ j → j < (e + 2) * E.c.epochLength →
    tstake E (e * E.c.epochLength) (σ (e * E.c.epochLength)) ≤ ρ * tstake E j (σ j)

/-- **Honest online stake is at least `Hmin`** at every slot. -/
def MinStake (E : Env) (σ : ℕ → EpochState) (Hmin : ℝ) : Prop := ∀ j, Hmin ≤ hstake E j (σ j)

theorem card_win_le (e : ℕ) : (win E e).card ≤ E.c.period := by
  simp only [win, Nat.card_Ico]; omega

/-- **`StakePath` from bounded drift.** -/
theorem stakePath_of_drift (hT : T.OK) (hl : 0 < lam0 E.c) (hK : 0 < Kc E.c) (hP1 : 1 ≤ E.c.period)
    {ρ Hmin : ℝ} (hρ : 0 < ρ) (hH : 0 < Hmin) {e : ℕ} (hd : StakeDrift E σ ρ e) (hm : MinStake E σ Hmin)
    (hup : (1 - T.μ) + 2 * T.ℓhi / (lam0 E.c * Hmin) ≤
      T.ℓhi * Kc E.c * (1 - T.μ) * (1 - T.δ) * T.clo * ((E.c.period : ℝ) - 1) / ρ)
    (hlo : T.ℓlo * Kc E.c * (1 + T.δ) * T.chi * E.c.period * ρ + Kc E.c * ρ + 3 * T.ℓlo / (lam0 E.c * Hmin) ≤ 1) :
    StakePath E T σ e := by
  have hμ : 0 < 1 - T.μ := by linarith [hT.μ1]
  have hδ : 0 ≤ 1 - T.δ := by linarith [hT.δ1]
  have hclo := hT.clo0
  have hchi : 0 ≤ T.chi := by
    unfold TBand.chi
    have : 0 ≤ errLo T.η T.ζ T.Yh + errLo T.η T.ζ T.Ya := by
      unfold errLo; have := hT.η0; have := hT.ζ0; positivity
    have := hT.lo_pos; positivity
  have hlH : 0 < lam0 E.c * Hmin := mul_pos hl hH
  refine ⟨fun j h1 h2 => ?_, fun j h1 h2 => ?_⟩
  · -- the honest stake: the window's sum is at least `(P - 1) · H_j / ρ`
    set Hj := hstake E j (σ j)
    have hHj : Hmin ≤ Hj := hm j
    have hsum : ((E.c.period : ℝ) - 1) * (Hj / ρ) ≤ ∑ k ∈ win E e, hstake E (k + 1) (σ (k + 1)) := by
      have hc : ((E.c.period : ℝ) - 1) ≤ (win E e).card := by
        have := card_win (E := E) e
        have : ((E.c.period - 1 : ℕ) : ℝ) ≤ (win E e).card := by exact_mod_cast this
        rw [Nat.cast_sub hP1] at this; simpa using this
      calc ((E.c.period : ℝ) - 1) * (Hj / ρ) ≤ (win E e).card * (Hj / ρ) :=
            mul_le_mul_of_nonneg_right hc (div_nonneg (by linarith) hρ.le)
        _ = ∑ k ∈ win E e, Hj / ρ := by rw [sum_const, nsmul_eq_mul]
        _ ≤ _ := sum_le_sum fun k hk => by
            rw [div_le_iff₀ hρ, mul_comm]; exact hd.hon j h1 h2 k hk
    have hlHj : lam0 E.c * Hmin ≤ lam0 E.c * Hj := mul_le_mul_of_nonneg_left hHj hl.le
    have h2l : 2 * T.ℓhi ≤ 2 * T.ℓhi / (lam0 E.c * Hmin) * (lam0 E.c * Hj) := by
      rw [div_mul_eq_mul_div, le_div_iff₀ hlH]
      exact mul_le_mul_of_nonneg_left hlHj (by linarith [hT.hi0])
    have hA : 0 ≤ T.ℓhi * Kc E.c * (1 - T.μ) * (1 - T.δ) * T.clo := by
      have := hT.hi0; positivity
    calc (1 - T.μ) * (lam0 E.c * Hj) + 2 * T.ℓhi
        ≤ ((1 - T.μ) + 2 * T.ℓhi / (lam0 E.c * Hmin)) * (lam0 E.c * Hj) := by nlinarith
      _ ≤ T.ℓhi * Kc E.c * (1 - T.μ) * (1 - T.δ) * T.clo * ((E.c.period : ℝ) - 1) / ρ * (lam0 E.c * Hj) :=
          mul_le_mul_of_nonneg_right hup (mul_nonneg hl.le (by linarith))
      _ = T.ℓhi * Kc E.c * (1 - T.μ) * (1 - T.δ) * T.clo * lam0 E.c * (((E.c.period : ℝ) - 1) * (Hj / ρ)) := by
          field_simp
      _ ≤ T.ℓhi * Kc E.c * (1 - T.μ) * (1 - T.δ) * T.clo * lam0 E.c *
            ∑ k ∈ win E e, hstake E (k + 1) (σ (k + 1)) :=
          mul_le_mul_of_nonneg_left hsum (mul_nonneg hA hl.le)
      _ = T.ℓhi * (Kc E.c * ((1 - T.μ) * (1 - T.δ) * T.clo *
            (lam0 E.c * ∑ k ∈ win E e, hstake E (k + 1) (σ (k + 1))))) := by ring
  · -- all participating stake: the window's sum is at most `P · ρ · S_j`
    set Sj := hstake E j (σ j) + astake (σ j)
    have hSj : Hmin ≤ Sj := by have := hm j; have := astake_nonneg (σ j); simp only [Sj]; linarith
    have hsum : ∑ k ∈ win E e, (hstake E (k + 1) (σ (k + 1)) + astake (σ (k + 1))) ≤ E.c.period * (ρ * Sj) := by
      calc ∑ k ∈ win E e, (hstake E (k + 1) (σ (k + 1)) + astake (σ (k + 1)))
          ≤ ∑ k ∈ win E e, ρ * Sj := sum_le_sum fun k hk => hd.tot j h1 h2 k hk
        _ = (win E e).card * (ρ * Sj) := by rw [sum_const, nsmul_eq_mul]
        _ ≤ E.c.period * (ρ * Sj) := by
            refine mul_le_mul_of_nonneg_right ?_ (mul_nonneg hρ.le (by linarith))
            exact_mod_cast card_win_le e
    have h0 : hstake E (e * E.c.epochLength) (σ (e * E.c.epochLength)) + astake (σ (e * E.c.epochLength)) ≤
        ρ * Sj := hd.tot0 j h1 h2
    have hlSj : lam0 E.c * Hmin ≤ lam0 E.c * Sj := mul_le_mul_of_nonneg_left hSj hl.le
    have h3l : 3 * T.ℓlo ≤ 3 * T.ℓlo / (lam0 E.c * Hmin) * (lam0 E.c * Sj) := by
      rw [div_mul_eq_mul_div, le_div_iff₀ hlH]
      exact mul_le_mul_of_nonneg_left hlSj (by linarith [hT.lo_pos])
    have hlo0 := hT.lo_pos
    have hδ1 : 0 ≤ 1 + T.δ := by linarith [hT.δ0]
    have e1 : T.ℓlo * (Kc E.c * ((1 + T.δ) * T.chi *
        (lam0 E.c * ∑ k ∈ win E e, (hstake E (k + 1) (σ (k + 1)) + astake (σ (k + 1)))) +
        lam0 E.c * (hstake E (e * E.c.epochLength) (σ (e * E.c.epochLength)) +
          astake (σ (e * E.c.epochLength))) / T.ℓlo) + 3) =
        T.ℓlo * Kc E.c * (1 + T.δ) * T.chi * lam0 E.c *
          ∑ k ∈ win E e, (hstake E (k + 1) (σ (k + 1)) + astake (σ (k + 1))) +
        Kc E.c * lam0 E.c * (hstake E (e * E.c.epochLength) (σ (e * E.c.epochLength)) +
          astake (σ (e * E.c.epochLength))) + 3 * T.ℓlo := by
      field_simp
    rw [e1]
    have hc1 : 0 ≤ T.ℓlo * Kc E.c * (1 + T.δ) * T.chi * lam0 E.c := by positivity
    have hc2 : 0 ≤ Kc E.c * lam0 E.c := by positivity
    calc T.ℓlo * Kc E.c * (1 + T.δ) * T.chi * lam0 E.c *
          ∑ k ∈ win E e, (hstake E (k + 1) (σ (k + 1)) + astake (σ (k + 1))) +
        Kc E.c * lam0 E.c * (hstake E (e * E.c.epochLength) (σ (e * E.c.epochLength)) +
          astake (σ (e * E.c.epochLength))) + 3 * T.ℓlo
        ≤ T.ℓlo * Kc E.c * (1 + T.δ) * T.chi * lam0 E.c * (E.c.period * (ρ * Sj)) +
          Kc E.c * lam0 E.c * (ρ * Sj) + 3 * T.ℓlo / (lam0 E.c * Hmin) * (lam0 E.c * Sj) := by
          gcongr
      _ = (T.ℓlo * Kc E.c * (1 + T.δ) * T.chi * E.c.period * ρ + Kc E.c * ρ +
            3 * T.ℓlo / (lam0 E.c * Hmin)) * (lam0 E.c * Sj) := by ring
      _ ≤ 1 * (lam0 E.c * Sj) := mul_le_mul_of_nonneg_right hlo (mul_nonneg hl.le (by linarith))
      _ = lam0 E.c * (hstake E j (σ j) + astake (σ j)) := by rw [one_mul]

end Cryptarchia.Prob
