module

public import Cryptarchia.Prob.Worst
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Algebra.Order.Star.Real
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
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# From conditional slot laws to a kernel, with one band per epoch

`law_le` lets the worst case pick a band member at every slot. In the protocol,
the band a slot runs under is set by its epoch's state (stake snapshot and stake
estimate), so it is fixed within an epoch and changes only when a new epoch starts.

Here the members of a family are `fam : Fin K → Band`, and slot `n + 1` runs under
member `Bsel n`, which is known before the slot (`hBm`) and changes only when slot
`n + 2` starts a new epoch of length `EL` (`hBc`). The worst case then picks a member
at each epoch start and keeps it for the epoch (`worstKE`, a kernel within the family
per epoch: `Kern.EpochFam`), and bounds every event closed under adding adversarial
slots (`law_le_epoch`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory Finset
open scoped ENNReal

/-- **A kernel within a family, one member per epoch.** The next slot after `l` is within
member `mem l`, which stays the same unless that slot starts a new epoch. -/
def Kern.EpochFam (κ : Kern) (EL : ℕ) {K : ℕ} (fam : Fin K → Band) : Prop :=
  ∃ mem : List Out → Fin K, (∀ l, κ.BandAt (fam (mem l)) l) ∧
    ∀ l o, (l.length + 2) % EL ≠ 0 → mem (l ++ [o]) = mem l

theorem Kern.EpochFam.fam {κ : Kern} {EL K : ℕ} {fam : Fin K → Band} (h : κ.EpochFam EL fam) :
    κ.Fam (List.ofFn fam) := by
  obtain ⟨mem, hb, -⟩ := h
  exact fun l => ⟨fam (mem l), List.mem_ofFn.2 ⟨mem l, rfl⟩, hb l⟩

variable {K : ℕ} (fam : Fin K → Band) (EL : ℕ) (F : List Out → ℝ)

open Classical in
/-- The members whose honest polytope is not empty. -/
noncomputable def goodB : Finset (Fin K) := Finset.univ.filter fun b => (HB (fam b)).Nonempty

variable {fam} (hG : (goodB fam).Nonempty)

/-- The value after a slot: at an epoch start, the worst member; otherwise the same. -/
noncomputable def nextV (V : List Out → Fin K → ℝ) (l : List Out) (b : Fin K) : ℝ :=
  if (l.length + 1) % EL = 0 then (goodB fam).sup' hG fun b' => V l b' else V l b

/-- **The worst case with one member per epoch**, with `n` slots to go, history `l`,
and current member `b`. -/
noncomputable def VE : ℕ → List Out → Fin K → ℝ
  | 0, l, _ => F l
  | n + 1, l, b => sSup ((fun q => ∑ o, prodLaw q (fam b).amax o * nextV EL hG (VE n) (l ++ [o]) b) '' HB (fam b))

variable {EL F hG}

theorem mem_goodB {b : Fin K} : b ∈ goodB fam ↔ (HB (fam b)).Nonempty := by
  classical
  unfold goodB; simp

theorem VE_attain {b : Fin K} (hb : b ∈ goodB fam) (n : ℕ) (l : List Out) :
    ∃ q ∈ HB (fam b), VE EL F hG (n + 1) l b = ∑ o, prodLaw q (fam b).amax o * nextV EL hG (VE EL F hG n) (l ++ [o]) b ∧
      ∀ q' ∈ HB (fam b), ∑ o, prodLaw q' (fam b).amax o * nextV EL hG (VE EL F hG n) (l ++ [o]) b ≤
        VE EL F hG (n + 1) l b := by
  set φ : (Fin 3 → ℝ) → ℝ := fun q => ∑ o, prodLaw q (fam b).amax o * nextV EL hG (VE EL F hG n) (l ++ [o]) b
  have hc : Continuous φ := by
    refine continuous_finsetSum _ fun o _ => ?_
    unfold prodLaw
    exact ((continuous_apply o.hon).mul continuous_const).mul continuous_const
  obtain ⟨q, hq, hmax⟩ := HB_isCompact.exists_isMaxOn (mem_goodB.1 hb) hc.continuousOn
  have hg : IsGreatest (φ '' HB (fam b)) (φ q) := ⟨⟨q, hq, rfl⟩, by rintro _ ⟨q', hq', rfl⟩; exact hmax hq'⟩
  have hW : VE EL F hG (n + 1) l b = φ q := hg.csSup_eq
  exact ⟨q, hq, hW, fun q' hq' => hW ▸ hmax hq'⟩

theorem VE_bad {b : Fin K} (hb : b ∉ goodB fam) (n : ℕ) (l : List Out) : VE EL F hG (n + 1) l b = 0 := by
  have : HB (fam b) = ∅ := by
    rw [mem_goodB, Set.not_nonempty_iff_eq_empty] at hb; exact hb
  show sSup _ = 0
  rw [this, Set.image_empty, Real.sSup_empty]

section Mono

variable (hP : ∀ b, (fam b).Prod)
include hP

omit hP in
theorem nextV_nonneg {V : List Out → Fin K → ℝ} (hV : ∀ l b, 0 ≤ V l b) (l : List Out) (b : Fin K) :
    0 ≤ nextV EL hG V l b := by
  unfold nextV
  split_ifs
  · obtain ⟨b0, hb0⟩ := hG
    exact le_trans (hV l b0) (Finset.le_sup' (fun b' => V l b') hb0)
  · exact hV l b

theorem VE_nonneg (hF : ∀ l, 0 ≤ F l) : ∀ n l b, 0 ≤ VE EL F hG n l b
  | 0, l, _ => hF l
  | n + 1, l, b => by
    by_cases hb : b ∈ goodB fam
    · obtain ⟨q, hq, hW, -⟩ := VE_attain (F := F) (EL := EL) (hG := hG) hb n l
      rw [hW]
      exact Finset.sum_nonneg fun o _ => mul_nonneg (prodLaw_nonneg hq.1 (hP b).a0 (hP b).a1 o)
        (nextV_nonneg (VE_nonneg hF n) _ _)
    · rw [VE_bad hb]

omit hP in
theorem nextV_mono {V : List Out → Fin K → ℝ} (hV : ∀ l l' b, List.Forall₂ OutLe l l' → V l b ≤ V l' b)
    {l l' : List Out} (h : List.Forall₂ OutLe l l') (b : Fin K) : nextV EL hG V l b ≤ nextV EL hG V l' b := by
  unfold nextV
  rw [h.length_eq]
  split_ifs
  · exact Finset.sup'_le _ _ fun b' hb' => le_trans (hV l l' b' h) (Finset.le_sup' (fun b' => V l' b') hb')
  · exact hV l l' b h

/-- **The worst case is monotone in adversarial slots.** -/
theorem VE_mono (hF : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l') :
    ∀ n l l' b, List.Forall₂ OutLe l l' → VE EL F hG n l b ≤ VE EL F hG n l' b
  | 0, l, l', _, h => hF l l' h
  | n + 1, l, l', b, h => by
    by_cases hb : b ∈ goodB fam
    · obtain ⟨q, hq, hW, -⟩ := VE_attain (F := F) (EL := EL) (hG := hG) hb n l
      obtain ⟨-, -, -, hmax'⟩ := VE_attain (F := F) (EL := EL) (hG := hG) hb n l'
      rw [hW]
      refine le_trans (Finset.sum_le_sum fun o _ => ?_) (hmax' q hq)
      exact mul_le_mul_of_nonneg_left
        (nextV_mono (VE_mono hF n) (forall₂_append h (List.Forall₂.cons (OutLe.refl o) List.Forall₂.nil)) b)
        (prodLaw_nonneg hq.1 (hP b).a0 (hP b).a1 o)
    · rw [VE_bad hb, VE_bad hb]

/-- **One slot of the true law** under member `b` is at most the worst case. -/
theorem stepE_le (hF : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l') {b : Fin K} {q : Fin 3 → ℝ}
    (hq : q ∈ HB (fam b)) {a : ℝ} (ha : a ≤ (fam b).amax) (n : ℕ) (l : List Out) :
    ∑ o, prodLaw q a o * nextV EL hG (VE EL F hG n) (l ++ [o]) b ≤ VE EL F hG (n + 1) l b := by
  have hb : b ∈ goodB fam := mem_goodB.2 ⟨q, hq⟩
  obtain ⟨-, -, -, hmax⟩ := VE_attain (F := F) (EL := EL) (hG := hG) hb n l
  refine le_trans ?_ (hmax q hq)
  rw [sum_prodLaw, sum_prodLaw]
  refine Finset.sum_le_sum fun h _ => mul_le_mul_of_nonneg_left ?_ (hq.1 h)
  have hm := nextV_mono (EL := EL) (hG := hG) (VE_mono (EL := EL) (hG := hG) hP hF n) (l := l ++ [⟨h, false⟩]) (l' := l ++ [⟨h, true⟩])
    (forall₂_append (forall₂_refl l) (List.Forall₂.cons ⟨rfl, fun x => absurd x (by simp)⟩ List.Forall₂.nil)) b
  nlinarith

end Mono

/-! ## The worst-case kernel, one member per epoch -/

variable (EL F hG) in
/-- The worst member for history `l`, with `n` slots to go. -/
noncomputable def argB (n : ℕ) (l : List Out) : Fin K :=
  Classical.choose (Finset.exists_max_image (goodB fam) (fun b => VE EL F hG n l b) hG)

theorem argB_mem (n : ℕ) (l : List Out) : argB EL F hG n l ∈ goodB fam :=
  (Classical.choose_spec (Finset.exists_max_image (goodB fam) (fun b => VE EL F hG n l b) hG)).1

theorem sup'_eq_argB (n : ℕ) (l : List Out) :
    (goodB fam).sup' hG (fun b => VE EL F hG n l b) = VE EL F hG n l (argB EL F hG n l) :=
  le_antisymm (Finset.sup'_le _ _
    (Classical.choose_spec (Finset.exists_max_image (goodB fam) (fun b => VE EL F hG n l b) hG)).2)
    (Finset.le_sup' (fun b => VE EL F hG n l b) (argB_mem n l))

variable (EL F hG) in
/-- **The member the worst case plays after `l`**: chosen at each epoch start
(and at the beginning), then kept. -/
noncomputable def memE (M : ℕ) (l : List Out) : Fin K :=
  if l = [] ∨ (l.length + 1) % EL = 0 then argB EL F hG (M - l.length) l else memE M l.dropLast
termination_by l.length
decreasing_by
  have hl : l ≠ [] := fun h' => by simp_all
  rw [List.length_dropLast]
  exact Nat.sub_lt (List.length_pos_of_ne_nil hl) one_pos

theorem memE_good (M : ℕ) : ∀ l : List Out, memE EL F hG M l ∈ goodB fam := by
  intro l
  induction h : l.length using Nat.strong_induction_on generalizing l with
  | _ n ih =>
    rw [memE]
    split_ifs with hc
    · exact argB_mem _ _
    · have hl : l ≠ [] := fun h' => hc (Or.inl h')
      exact ih _ (by rw [← h, List.length_dropLast]; exact Nat.sub_lt (List.length_pos_of_ne_nil hl) one_pos) _ rfl

theorem memE_snoc (M : ℕ) (l : List Out) (o : Out) :
    memE EL F hG M (l ++ [o]) = if (l.length + 2) % EL = 0 then argB EL F hG (M - (l.length + 1)) (l ++ [o])
      else memE EL F hG M l := by
  rw [memE]
  simp only [List.append_eq_nil_iff, List.cons_ne_nil, and_false, false_or, List.length_append,
    List.length_singleton, List.dropLast_concat]

variable (EL F hG) in
/-- The worst-case honest law after `l`. -/
noncomputable def qE (M : ℕ) (l : List Out) : Fin 3 → ℝ :=
  Classical.choose (VE_attain (F := F) (EL := EL) (hG := hG) (memE_good (EL := EL) (F := F) (hG := hG) M l) (M - l.length - 1) l)

theorem qE_mem (M : ℕ) (l : List Out) : qE EL F hG M l ∈ HB (fam (memE EL F hG M l)) :=
  (Classical.choose_spec (VE_attain (F := F) (EL := EL) (hG := hG) (memE_good (EL := EL) (F := F) (hG := hG) M l) (M - l.length - 1) l)).1

theorem qE_val (M : ℕ) (l : List Out) :
    VE EL F hG (M - l.length - 1 + 1) l (memE EL F hG M l) =
      ∑ o, prodLaw (qE EL F hG M l) (fam (memE EL F hG M l)).amax o *
        nextV EL hG (VE EL F hG (M - l.length - 1)) (l ++ [o]) (memE EL F hG M l) :=
  (Classical.choose_spec (VE_attain (F := F) (EL := EL) (hG := hG) (memE_good (EL := EL) (F := F) (hG := hG) M l) (M - l.length - 1) l)).2.1

variable (EL F hG) in
/-- **The worst-case kernel, one member per epoch.** -/
noncomputable def worstKE (hP : ∀ b, (fam b).Prod) (M : ℕ) : Kern where
  p l o := prodLaw (qE EL F hG M l) (fam (memE EL F hG M l)).amax o
  nonneg l o := prodLaw_nonneg (qE_mem (EL := EL) (F := F) (hG := hG) M l).1 (hP _).a0 (hP _).a1 o
  sum_one l := sum_prodLaw_one (qE_mem (EL := EL) (F := F) (hG := hG) M l).2.1 _

theorem worstKE_Ex (hP : ∀ b, (fam b).Prod) {M : ℕ} : ∀ n (l : List Out), l.length + n = M →
    Ex (worstKE EL F hG hP M) n F l = VE EL F hG n l (memE EL F hG M l)
  | 0, l, _ => rfl
  | n + 1, l, h => by
    rw [Ex_succ]
    have e : M - l.length - 1 = n := by omega
    have hv := qE_val (F := F) (EL := EL) (hG := hG) M l
    rw [e] at hv
    rw [hv]
    refine Finset.sum_congr rfl fun o _ => ?_
    rw [worstKE_Ex hP n (l ++ [o]) (by simp; omega)]
    congr 1
    rw [memE_snoc]
    unfold nextV
    simp only [List.length_append, List.length_singleton]
    split_ifs with hc
    · rw [show M - (l.length + 1) = n by omega, sup'_eq_argB]
    · rfl

/-- **The worst-case kernel keeps one member per epoch.** -/
theorem worstKE_epochFam (hP : ∀ b, (fam b).Prod) (M : ℕ) : (worstKE EL F hG hP M).EpochFam EL fam :=
  ⟨memE EL F hG M, fun l => bandAt_prodLaw (hP _) (qE_mem (EL := EL) (F := F) (hG := hG) M l) fun _ => rfl,
    fun l o hc => by rw [memE_snoc, if_neg hc]⟩

/-! ## Conditional laws to the per-epoch worst-case kernel -/

end Cryptarchia.Prob
