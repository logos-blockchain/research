module

public import Cryptarchia.Prob.Burst
public import Mathlib.MeasureTheory.Integral.Lebesgue.Basic
public import Mathlib.MeasureTheory.Measure.Typeclasses.Probability
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
# From conditional slot laws to a kernel

The lottery string of an execution is not sampled by one fixed kernel: the next
slot's law depends on the epoch state, which depends on everything the adversary
did. This file turns per-slot conditional laws into the kernel form the bounds
use.

Suppose that, given the past, each slot's outcome has the law `qh ⊗ Bern(qa)`: an
honest part `qh` in the band's honest polytope (`HB`) and, independently, an
adversarial win with probability `qa ≤ amax` (`hcond` in `law_le`). Take an event
`S` about the first `M` slots that is closed under adding adversarial slots
(`UpClosed`). Then `S` is at most as likely as under the **worst-case kernel**
(`worstK`), which at each history plays the honest law in `HB` that maximizes the
probability of `S` from there, with the adversary winning with probability
exactly `amax`. That kernel is within the band (`worstK_within`).

The worst case is a backward recursion (`Wv`): a maximum over the compact set
`HB`, attained (`Wv_attain`). It is monotone in adversarial slots (`Wv_mono`),
which is why an adversary winning less often than `amax` only helps.
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory Finset

instance : MeasurableSpace Out := ⊤

instance : MeasurableSingletonClass Out := ⟨fun _ => trivial⟩

/-- `o'` has the same honest leaders as `o`, and an adversarial win wherever `o` has one. -/
def OutLe (o o' : Out) : Prop := o.hon = o'.hon ∧ (o.adv = true → o'.adv = true)

theorem OutLe.refl (o : Out) : OutLe o o := ⟨rfl, id⟩

theorem OutLe.trans {o o' o'' : Out} (h : OutLe o o') (h' : OutLe o' o'') : OutLe o o'' :=
  ⟨h.1.trans h'.1, fun x => h'.2 (h.2 x)⟩

/-- A set of histories closed under adding adversarial slots. -/
def UpClosed (S : Set (List Out)) : Prop := ∀ l l', List.Forall₂ OutLe l l' → l ∈ S → l' ∈ S

theorem forall₂_refl (l : List Out) : List.Forall₂ OutLe l l := by
  induction l with
  | nil => exact List.Forall₂.nil
  | cons o l ih => exact List.Forall₂.cons (OutLe.refl o) ih

theorem forall₂_trans {l l' l'' : List Out} (h : List.Forall₂ OutLe l l') (h' : List.Forall₂ OutLe l' l'') :
    List.Forall₂ OutLe l l'' := by
  induction h generalizing l'' with
  | nil => cases h'; exact List.Forall₂.nil
  | cons ho _ ih =>
    cases h' with
    | cons ho' ht' => exact List.Forall₂.cons (ho.trans ho') (ih ht')

theorem forall₂_append {l l' m m' : List Out} (h : List.Forall₂ OutLe l l') (hm : List.Forall₂ OutLe m m') :
    List.Forall₂ OutLe (l ++ m) (l' ++ m') := List.rel_append h hm

/-- **`x` decides `S` at length `M`**: every continuation of `x` to length `M` lies in `S`. -/
def Decided (S : Set (List Out)) (M : ℕ) (x : List Out) : Prop :=
  ∀ y : List Out, x.length + y.length = M → x ++ y ∈ S

theorem Decided.append {S : Set (List Out)} {M : ℕ} {x : List Out} (h : Decided S M x) (z : List Out) :
    Decided S M (x ++ z) := fun y hy => by
  rw [List.append_assoc]; exact h _ (by simp only [List.length_append] at hy ⊢; omega)

theorem Decided.mem {S : Set (List Out)} {M : ℕ} {x : List Out} (h : Decided S M x) (hx : x.length = M) :
    x ∈ S := by
  simpa using h [] (by simpa using hx)

/-- Sums over outcomes. -/
theorem sum_out {β : Type*} [AddCommMonoid β] (f : Out → β) :
    ∑ o, f o = ∑ h : Fin 3, (f ⟨h, false⟩ + f ⟨h, true⟩) := by
  let e : Out ≃ Fin 3 × Bool := ⟨fun o => (o.hon, o.adv), fun p => ⟨p.1, p.2⟩, fun _ => rfl, fun _ => rfl⟩
  rw [← e.symm.sum_comp, Fintype.sum_prod_type]
  refine Finset.sum_congr rfl fun h _ => ?_
  rw [Fintype.sum_bool, add_comm]
  rfl

/-! ## The honest polytope and product laws -/

/-- **The honest polytope** of a band: laws of the honest part (no leader, one, two
or more) consistent with the band when the adversary wins with probability `amax`,
independently. -/
def HB (B : Band) : Set (Fin 3 → ℝ) :=
  {q | (∀ h, 0 ≤ q h) ∧ q 0 + q 1 + q 2 = 1 ∧ B.hlo ≤ q 1 + q 2 ∧ q 1 + q 2 ≤ B.hhi ∧
    B.slo ≤ q 1 * (1 - B.amax) ∧ B.hnlo ≤ (q 1 + q 2) * (1 - B.amax) ∧ B.elo ≤ q 0 * (1 - B.amax)}

/-- The law of a slot: honest part `q`, and independently an adversarial win with
probability `a`. -/
def prodLaw (q : Fin 3 → ℝ) (a : ℝ) (o : Out) : ℝ := q o.hon * (if o.adv then a else 1 - a)

/-- The band facts the worst-case kernel needs. -/
structure Band.Prod (B : Band) : Prop where
  a0 : 0 ≤ B.amax
  a1 : B.amax ≤ 1
  alo : B.alo ≤ B.amax
  hahi : B.hhi * B.amax ≤ B.hahi
  halo : B.halo ≤ B.hlo * B.amax

variable {B : Band}

theorem prodLaw_nonneg {q : Fin 3 → ℝ} (hq : ∀ h, 0 ≤ q h) {a : ℝ} (ha0 : 0 ≤ a) (ha1 : a ≤ 1) (o : Out) :
    0 ≤ prodLaw q a o := by
  unfold prodLaw; split_ifs <;> exact mul_nonneg (hq _) (by linarith)

theorem sum_prodLaw (q : Fin 3 → ℝ) (a : ℝ) (W : Out → ℝ) :
    ∑ o, prodLaw q a o * W o = ∑ h : Fin 3, q h * ((1 - a) * W ⟨h, false⟩ + a * W ⟨h, true⟩) := by
  rw [sum_out]
  refine Finset.sum_congr rfl fun h _ => ?_
  simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]
  ring

theorem sum_prodLaw_one {q : Fin 3 → ℝ} (hq : q 0 + q 1 + q 2 = 1) (a : ℝ) : ∑ o, prodLaw q a o = 1 := by
  have := sum_prodLaw q a (fun _ => 1)
  simp only [mul_one] at this
  rw [this, Fin.sum_univ_three]
  linear_combination hq

theorem HB_isCompact : IsCompact (HB B) := by
  apply Metric.isCompact_of_isClosed_isBounded
  · have e : HB B = (⋂ h, {q : Fin 3 → ℝ | 0 ≤ q h}) ∩ ({q | q 0 + q 1 + q 2 = 1} ∩
        ({q | B.hlo ≤ q 1 + q 2} ∩ ({q | q 1 + q 2 ≤ B.hhi} ∩ ({q | B.slo ≤ q 1 * (1 - B.amax)} ∩
          ({q | B.hnlo ≤ (q 1 + q 2) * (1 - B.amax)} ∩ {q | B.elo ≤ q 0 * (1 - B.amax)}))))) := by
      ext q; simp [HB, Set.mem_iInter]
    rw [e]
    exact (isClosed_iInter fun h => isClosed_le continuous_const (continuous_apply h)).inter
      ((isClosed_eq (by fun_prop) continuous_const).inter
      ((isClosed_le continuous_const (by fun_prop)).inter
      ((isClosed_le (by fun_prop) continuous_const).inter
      ((isClosed_le continuous_const (by fun_prop)).inter
      ((isClosed_le continuous_const (by fun_prop)).inter
      (isClosed_le continuous_const (by fun_prop)))))))
  · refine (Metric.isBounded_closedBall (x := (0 : Fin 3 → ℝ)) (r := 1)).subset ?_
    intro q hq
    obtain ⟨h0, hs, -⟩ := hq
    rw [Metric.mem_closedBall, dist_zero_right, pi_norm_le_iff_of_nonneg zero_le_one]
    intro h
    rw [Real.norm_eq_abs, abs_le]
    have := h0 0; have := h0 1; have := h0 2
    fin_cases h <;> simp <;> constructor <;> linarith

/-! ## The worst case -/

variable {Bs : List Band}

/-! ## The worst-case kernel -/

theorem pr_prodLaw (q : Fin 3 → ℝ) (a : ℝ) (P : Out → Prop) [DecidablePred P] :
    ∑ o, (if P o then prodLaw q a o else 0) =
      ∑ h : Fin 3, ((if P ⟨h, false⟩ then q h * (1 - a) else 0) + (if P ⟨h, true⟩ then q h * a else 0)) := by
  rw [sum_out]
  refine Finset.sum_congr rfl fun h _ => ?_
  simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]

/-- A kernel whose next slot after `l` has the law `qh ⊗ Bern(amax)` with `qh` in the
band's polytope is within the band there. -/
theorem bandAt_prodLaw {κ : Kern} {l : List Out} {B : Band} (hB : B.Prod) {q : Fin 3 → ℝ} (mem : q ∈ HB B)
    (pk : ∀ o, κ.p l o = prodLaw q B.amax o) : κ.BandAt B l := by
  have ha0 := hB.a0
  have prh : κ.pr l (fun o => o.hon ≠ 0) = q 1 + q 2 := by
    unfold Kern.pr; simp only [pk]; rw [pr_prodLaw, Fin.sum_univ_three]; simp; ring
  have pra : κ.pr l (fun o => o.adv = true) = B.amax := by
    unfold Kern.pr; simp only [pk]; rw [pr_prodLaw, Fin.sum_univ_three]; simp
    have := mem.2.1
    linear_combination B.amax * this
  have prha : κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) = (q 1 + q 2) * B.amax := by
    unfold Kern.pr; simp only [pk]; rw [pr_prodLaw, Fin.sum_univ_three]; simp; ring
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · rw [prh]; exact mem.2.2.2.1
  · rw [prh]; exact mem.2.2.1
  · rw [pra]
  · rw [prha]; exact le_trans (mul_le_mul_of_nonneg_right mem.2.2.2.1 ha0) hB.hahi
  · rw [pk]; simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]; exact mem.2.2.2.2.1
  · rw [pk, pk]; simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]
    have := mem.2.2.2.2.2.1; linarith
  · rw [pk]; simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]; exact mem.2.2.2.2.2.2
  · rw [pra]; exact hB.alo
  · rw [prha]; exact le_trans hB.halo (mul_le_mul_of_nonneg_right mem.2.2.1 ha0)

/-! ## Conditional laws to the worst-case kernel -/

open scoped ENNReal

end Cryptarchia.Prob
