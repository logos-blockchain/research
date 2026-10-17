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
# The member of an epoch from its state, and bounded stake drift

The multi-epoch theorem needs, whenever an epoch is in band, that each of its slots
is within the band of the member `pick` assigns. Here `pick` is constructed
(`pickM`): epoch `e`'s member is the one whose honest-exponent range holds the
honest exponent at the epoch's first slot. The band condition then follows from the
estimate (`SlotIn`), the stake assumption (`StateOK`) and facts a certificate checks
about its members (`Member.OK`, consecutive ranges covering `[ylo, Yh]`, and room for
the adversary), provided the honest nodes' online status changes only at epoch
boundaries (`OnlineEpoch`). A slot's honest exponent counts only the online honest
nodes' notes, so without `OnlineEpoch` a crash inside an epoch could move it to
another member's range; the kernel keeps one member per epoch.

`StakePath`, the condition the band step needs on how stake moves between epochs, is
stated in the band's derived constants. It follows from a plain one
(`stakePath_of_drift`): from epoch `e` to `e + 1` stake moves by at most a factor `ρ`
(`StakeDrift`), and honest online stake is never below `Hmin` (`MinStake`), which
absorbs the fixed-point rounding. A certificate checks the two numeric conditions
linking `ρ` and `Hmin` to its band.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Classical

variable {E : Env} {T : TBand}

/-- **The online schedule changes only at epoch boundaries**: each node's online
status at a slot is its status at the epoch's first slot. -/
def OnlineEpoch (E : Env) : Prop :=
  ∀ j ∈ E.nodes, ∀ i, E.online j i = E.online j (i / E.c.epochLength * E.c.epochLength)

/-- The honest exponent at epoch `e`'s first slot under state `s`. -/
noncomputable def yE (E : Env) (e : ℕ) (s : EpochState) : ℝ :=
  expo E.c s (honNotes E (e * E.c.epochLength) s E.nodes)

/-- **The member of epoch `e` under state `s`**: one whose honest-exponent range
holds `yE e s` (the first member if none does). -/
noncomputable def pickM {K : ℕ} (E : Env) (mem : Fin (K + 1) → Member) (e : ℕ) (s : EpochState) : Fin (K + 1) :=
  if h : ∃ k, (mem k).ylo ≤ yE E e s ∧ yE E e s ≤ (mem k).yhi then Classical.choose h else 0

theorem yE_eq (hon : OnlineEpoch E) (i : ℕ) (s : EpochState) :
    expo E.c s (honNotes E i s E.nodes) = yE E (i / E.c.epochLength) s := by
  unfold yE
  rw [honNotes_congr s fun j hj => hon j hj i]

/-- **The band condition from the estimate.** With the online schedule constant on
epochs, a slot in band under a state satisfying `StateOK` is within the band of the
member `pickM` assigns to its epoch and state. -/
theorem slotBand_pickM (hc : LotConsts E.c T.η) (hT : T.OK) (hnd : E.nodes.Nodup) (hon : OnlineEpoch E)
    {K : ℕ} {mem : Fin (K + 1) → Member} (hok : ∀ k, (mem k).OK T.η T.ζ)
    (hcov : ∀ y, T.ylo ≤ y → y ≤ T.Yh → ∃ k, (mem k).ylo ≤ y ∧ y ≤ (mem k).yhi)
    (hadv : ∀ k, T.β * (mem k).yhi ≤ (1 - T.β) * (mem k).ahi)
    {i : ℕ} {s : EpochState} (hst : StateOK E T.β T.ζ i s) (hin : SlotIn E T i s) :
    SlotBand (mem (pickM E mem (i / E.c.epochLength) s)).B E i s := by
  obtain ⟨hy1, hy2, -⟩ := expo_range hT hst hin
  have hyE := yE_eq hon i s
  rw [hyE] at hy1 hy2
  have hex : ∃ k, (mem k).ylo ≤ yE E (i / E.c.epochLength) s ∧ yE E (i / E.c.epochLength) s ≤ (mem k).yhi :=
    hcov _ hy1 hy2
  set k := pickM E mem (i / E.c.epochLength) s with hk
  have hspec : (mem k).ylo ≤ yE E (i / E.c.epochLength) s ∧ yE E (i / E.c.epochLength) s ≤ (mem k).yhi := by
    rw [hk]; unfold pickM; rw [dite_eq_left_of_eq_true (eq_true hex)]; exact Classical.choose_spec hex
  rw [← hyE] at hspec
  refine slotBand_of_member hc hT.η0 hnd hT.ζ0 hst.smallH hst.smallA (hok k) hspec.1 hspec.2 ?_
  -- the adversary's exponent, from the stake fraction
  have hD : (0 : ℝ) < s.D := by have := hst.smallH.D_pos; exact_mod_cast (by omega : 0 < s.D)
  have hl0 := lam0_nonneg E.c
  have hβ : 0 < 1 - T.β := by linarith [hT.β1]
  have hfr : (1 - T.β) * expo E.c s (advNotes s) ≤ T.β * expo E.c s (honNotes E i s E.nodes) := by
    have h := hst.frac
    unfold astake hstake at h
    have e1 : expo E.c s (advNotes s) = lam0 E.c * (stakeOf (advNotes s) : ℝ) / s.D := rfl
    have e2 : expo E.c s (honNotes E i s E.nodes) = lam0 E.c * (stakeOf (honNotes E i s E.nodes) : ℝ) / s.D := rfl
    rw [e1, e2, mul_div_assoc', mul_div_assoc', div_le_div_iff_of_pos_right hD]
    nlinarith [mul_le_mul_of_nonneg_left h hl0]
  have : (1 - T.β) * expo E.c s (advNotes s) ≤ (1 - T.β) * (mem k).ahi := by
    nlinarith [mul_le_mul_of_nonneg_left hspec.2 hT.β0, hadv k]
  exact le_of_mul_le_mul_left this hβ

/-- **Coverage from consecutive ranges**: members whose ranges chain from below `ylo`
to above `Yh` cover every exponent in between. -/
theorem cover_of_chain {K : ℕ} {mem : Fin (K + 1) → Member}
    (hch : Chained (mem 0) (List.ofFn fun k : Fin K => mem k.succ))
    {lo hi : ℝ} (hlo : (mem 0).ylo ≤ lo) (hhi : hi ≤ (mem (Fin.last K)).yhi) :
    ∀ y, lo ≤ y → y ≤ hi → ∃ k, (mem k).ylo ≤ y ∧ y ≤ (mem k).yhi := by
  intro y h1 h2
  have hl : (mem 0 :: List.ofFn fun k : Fin K => mem k.succ) = List.ofFn mem := (List.ofFn_succ (f := mem)).symm
  have hlast : ((mem 0 :: List.ofFn fun k : Fin K => mem k.succ).getLast (List.cons_ne_nil _ _)) =
      mem (Fin.last K) := by
    simp only [hl, List.getLast_ofFn]
    rfl
  obtain ⟨m, hm, hm1, hm2⟩ := cover_chain y (mem 0) _ hch (by linarith) (by rw [hlast]; linarith)
  rw [hl, List.mem_ofFn] at hm
  obtain ⟨k, rfl⟩ := hm
  exact ⟨k, hm1, hm2⟩

section

open Finset

variable {σ : ℕ → EpochState}

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

end

end Cryptarchia.Prob
