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
# The member of an epoch, from its state

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
  refine slotBand_of_member hc hT.η0 hnd hst.nodup hT.ζ0 hst.smallH hst.smallA (hok k) hspec.1 hspec.2 ?_
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

end Cryptarchia.Prob
