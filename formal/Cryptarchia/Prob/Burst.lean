module

public import Cryptarchia.Prob.Potential
public import Cryptarchia.Prob.Kernel
public import Cryptarchia.Prob.Phases
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
# Expectations over one phase

From a phase end `m` (a quiet slot, or genesis), the next phase is either one slot
with no honest success, or a **burst**: it starts at an honest slot and ends after
`Δ` slots with no honest success (or at the horizon `M`). We bound, under any
kernel within a band of per-slot probabilities (`Band`, `Kern.Within`):

* `phase_upper`: `E[θ^L · x^A · y^B]` from above (`L` the phase length, `A` its
  adversarial slots, `B` whether it has an honest success), through a solution `u`
  of the burst recursion (`BurstSol`);
* `phase_lower`: the probability of one fixed pattern (one honest slot, no
  adversary, then `Δ` empty slots) from below. It is a crossing, and a phase with
  no adversarial slot.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle

/-! ## Bands of per-slot probabilities -/

/-- Bounds on the next slot's distribution, valid after every history. -/
structure Band where
  /-- `P(some honest leader) ≤ hhi` -/
  hhi : ℝ
  /-- `P(some honest leader) ≥ hlo` -/
  hlo : ℝ
  /-- `P(adversary wins) ≤ amax` -/
  amax : ℝ
  /-- `P(some honest leader and the adversary wins) ≤ hahi` -/
  hahi : ℝ
  /-- `P(exactly one honest leader, adversary does not win) ≥ slo` -/
  slo : ℝ
  /-- `P(some honest leader, adversary does not win) ≥ hnlo` -/
  hnlo : ℝ
  /-- `P(empty slot) ≥ elo` -/
  elo : ℝ
  /-- `P(adversary wins) ≥ alo` -/
  alo : ℝ := 0
  /-- `P(some honest leader and the adversary wins) ≥ halo` -/
  halo : ℝ := 0

/-- The kernel is within the band after every history. -/
structure Kern.Within (κ : Kern) (B : Band) : Prop where
  hhi : ∀ l, κ.pr l (fun o => o.hon ≠ 0) ≤ B.hhi
  hlo : ∀ l, B.hlo ≤ κ.pr l (fun o => o.hon ≠ 0)
  amax : ∀ l, κ.pr l (fun o => o.adv = true) ≤ B.amax
  hahi : ∀ l, κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) ≤ B.hahi
  slo : ∀ l, B.slo ≤ κ.p l ⟨1, false⟩
  hnlo : ∀ l, B.hnlo ≤ κ.p l ⟨1, false⟩ + κ.p l ⟨2, false⟩
  elo : ∀ l, B.elo ≤ κ.p l ⟨0, false⟩
  alo : ∀ l, B.alo ≤ κ.pr l (fun o => o.adv = true)
  halo : ∀ l, B.halo ≤ κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true)

variable {κ : Kern} {B : Band}

/-- The next slot's law after history `l` is within the band. -/
structure Kern.BandAt (κ : Kern) (B : Band) (l : List Out) : Prop where
  hhi : κ.pr l (fun o => o.hon ≠ 0) ≤ B.hhi
  hlo : B.hlo ≤ κ.pr l (fun o => o.hon ≠ 0)
  amax : κ.pr l (fun o => o.adv = true) ≤ B.amax
  hahi : κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) ≤ B.hahi
  slo : B.slo ≤ κ.p l ⟨1, false⟩
  hnlo : B.hnlo ≤ κ.p l ⟨1, false⟩ + κ.p l ⟨2, false⟩
  elo : B.elo ≤ κ.p l ⟨0, false⟩
  alo : B.alo ≤ κ.pr l (fun o => o.adv = true)
  halo : B.halo ≤ κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true)

/-- **A family of bands**: after every history, the next slot's law is within one
of the bands (which one may depend on the history). -/
def Kern.Fam (κ : Kern) (Bs : List Band) : Prop := ∀ l, ∃ B ∈ Bs, κ.BandAt B l

theorem Kern.Within.at {κ : Kern} {B : Band} (h : κ.Within B) (l : List Out) : κ.BandAt B l :=
  ⟨h.hhi l, h.hlo l, h.amax l, h.hahi l, h.slo l, h.hnlo l, h.elo l, h.alo l, h.halo l⟩

theorem Kern.Within.fam {κ : Kern} {B : Band} (h : κ.Within B) : κ.Fam [B] :=
  fun l => ⟨B, List.mem_singleton_self B, h.at l⟩

/-- `H` is weaker than `B` in every bound: a law within `B` is within `H`. -/
structure Band.Weaker (H B : Band) : Prop where
  hhi : B.hhi ≤ H.hhi
  hlo : H.hlo ≤ B.hlo
  amax : B.amax ≤ H.amax
  hahi : B.hahi ≤ H.hahi
  slo : H.slo ≤ B.slo
  hnlo : H.hnlo ≤ B.hnlo
  elo : H.elo ≤ B.elo
  alo : H.alo ≤ B.alo
  halo : H.halo ≤ B.halo

theorem Band.Weaker.refl (B : Band) : B.Weaker B :=
  ⟨le_rfl, le_rfl, le_rfl, le_rfl, le_rfl, le_rfl, le_rfl, le_rfl, le_rfl⟩

/-- A kernel within a family is within any band weaker than all of its members. -/
theorem Kern.Fam.within {κ : Kern} {Bs : List Band} {H : Band} (hF : κ.Fam Bs)
    (hw : ∀ B ∈ Bs, H.Weaker B) : κ.Within H := by
  refine ⟨fun l => ?_, fun l => ?_, fun l => ?_, fun l => ?_, fun l => ?_, fun l => ?_, fun l => ?_,
    fun l => ?_, fun l => ?_⟩ <;> obtain ⟨B, hB, hl⟩ := hF l <;> have w := hw B hB
  · exact hl.hhi.trans w.hhi
  · exact w.hlo.trans hl.hlo
  · exact hl.amax.trans w.amax
  · exact hl.hahi.trans w.hahi
  · exact w.slo.trans hl.slo
  · exact w.hnlo.trans hl.hnlo
  · exact w.elo.trans hl.elo
  · exact w.alo.trans hl.alo
  · exact w.halo.trans hl.halo

theorem pr_le_one (l : List Out) (P : Out → Prop) [DecidablePred P] : κ.pr l P ≤ 1 := by
  unfold Kern.pr
  calc ∑ o, (if P o then κ.p l o else 0) ≤ ∑ o, κ.p l o :=
        Finset.sum_le_sum fun o _ => by split_ifs <;> linarith [κ.nonneg l o]
    _ = 1 := κ.sum_one l

theorem pr_nonneg (l : List Out) (P : Out → Prop) [DecidablePred P] : 0 ≤ κ.pr l P := by
  unfold Kern.pr
  exact Finset.sum_nonneg fun o _ => by split_ifs <;> linarith [κ.nonneg l o]

/-! ## Phase ends as a stopping rule -/

/-- A history ends a phase: it reaches the horizon, or its last slot is quiet. -/
def PE (Δ M : ℕ) (x : List Out) : Prop :=
  x.length = M ∨ (x.length < M ∧ Quiet Δ (strOf x) x.length)

noncomputable instance (Δ M : ℕ) : DecidablePred (PE Δ M) := Classical.decPred _

variable {Δ M : ℕ}

theorem advCnt_succ (w : CStr) {a b : ℕ} (hab : a ≤ b) :
    advCnt w a (b + 1) = advCnt w a b + (if (w (b + 1)).2 = true then 1 else 0) := by
  have h := advCnt_add (w := w) hab (show b ≤ b + 1 by omega)
  have h1 : advCnt w b (b + 1) = (if (w (b + 1)).2 = true then 1 else 0) := by
    unfold advCnt
    rw [show Finset.Ioc b (b + 1) = {b + 1} by ext; simp only [Finset.mem_Ioc, Finset.mem_singleton]; omega]
    by_cases hb : (w (b + 1)).2 = true <;> simp [Finset.filter_singleton, hb]
  omega

theorem strOf_sim (x t : List Out) (a : ℕ) : SimOn (strOf (x ++ t)) (strOf x) a x.length :=
  SimOn.of_eq fun i _ hi => strOf_append_of_le hi

theorem advCnt_snoc (x : List Out) (o : Out) {m : ℕ} (hm : m ≤ x.length) :
    advCnt (strOf (x ++ [o])) m (x.length + 1) =
      advCnt (strOf x) m x.length + (if o.adv = true then 1 else 0) := by
  rw [advCnt_succ _ hm, advCnt_congr (strOf_sim x [o] m), strOf_last]
  rfl

/-- In a burst: the last honest slot is `p > m`, followed by `q` slots with none. -/
structure InBurst (m : ℕ) (h : List Out) (q : ℕ) : Prop where
  p_gt : m + q < h.length
  hon : (strOf h (h.length - q)).1 ≠ 0
  quiet : ∀ i, h.length - q < i → i ≤ h.length → (strOf h i).1 = 0

theorem InBurst.honIn {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) :
    HonIn (strOf h) m h.length := ⟨h.length - q, by have := hb.p_gt; omega, by omega, hb.hon⟩

theorem InBurst.not_quiet {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) (hq : q < Δ) :
    ¬ Quiet Δ (strOf h) h.length := by
  intro hQ
  have := hb.p_gt
  exact hb.hon (hQ _ (by omega) (by omega) (by have := hb.p_gt; omega))

theorem InBurst.quiet_of {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) (hq : Δ ≤ q) :
    Quiet Δ (strOf h) h.length := fun i h1 h2 _ => hb.quiet i (by omega) h2

theorem InBurst.snoc_hon {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) (o : Out) (ho : o.hon ≠ 0) :
    InBurst m (h ++ [o]) 0 := by
  refine ⟨by simp; have := hb.p_gt; omega, ?_, ?_⟩
  · simp only [List.length_append, List.length_singleton, Nat.sub_zero]
    rw [strOf_last]; simp only [Out.toPair]; intro h'; exact ho (Fin.ext h')
  · intro i h1 h2; simp at h1 h2; omega

theorem InBurst.snoc_empty {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) (o : Out) (ho : o.hon = 0) :
    InBurst m (h ++ [o]) (q + 1) := by
  have hp := hb.p_gt
  refine ⟨by simp; omega, ?_, ?_⟩
  · simp only [List.length_append, List.length_singleton]
    rw [show h.length + 1 - (q + 1) = h.length - q by omega, strOf_append_of_le (by omega)]
    exact hb.hon
  · intro i h1 h2
    simp only [List.length_append, List.length_singleton] at h1 h2
    rcases Nat.lt_or_ge i (h.length + 1) with hi | hi
    · rw [strOf_append_of_le (by omega)]; exact hb.quiet i (by omega) (by omega)
    · have : i = h.length + 1 := by omega
      subst this; rw [strOf_last]; simp [Out.toPair, ho]

/-- A phase start: genesis, or a quiet slot. -/
def Start (Δ : ℕ) (l : List Out) : Prop := l.length = 0 ∨ Quiet Δ (strOf l) l.length

theorem start_snoc_empty {l : List Out} (hl : Start Δ l) (o : Out) (ho : o.hon = 0) :
    Quiet Δ (strOf (l ++ [o])) (l.length + 1) := by
  intro i h1 h2 h3
  rcases Nat.lt_or_ge i (l.length + 1) with hi | hi
  · rw [strOf_append_of_le (by omega)]
    rcases hl with h0 | hq
    · omega
    · exact hq i (by omega) (by omega) h3
  · have : i = l.length + 1 := by omega
    subst this; rw [strOf_last]; simp [Out.toPair, ho]

/-! ## A fixed pattern, from below -/

theorem ExU_ge_snoc {S : List Out → Prop} [DecidablePred S] {G : List Out → ℝ} (hG : ∀ h, 0 ≤ G h)
    {h : List Out} (hS : ¬ S h) (n : ℕ) (o : Out) :
    κ.p h o * ExU (κ := κ) S n G (h ++ [o]) ≤ ExU (κ := κ) S (n + 1) G h := by
  rw [ExU_go S n G hS]
  exact Finset.single_le_sum (f := fun o => κ.p h o * ExU (κ := κ) S n G (h ++ [o]))
    (fun o _ => mul_nonneg (κ.nonneg h o) (ExU_nonneg S n hG _)) (Finset.mem_univ o)

/-- The pattern: an honest slot `o1`, then `Δ` empty slots. -/
def pat (o1 : Out) (i : ℕ) : List Out := o1 :: List.replicate i Out.empty

theorem strOf_pat_first (l : List Out) (o1 : Out) (i : ℕ) :
    strOf (l ++ pat o1 i) (l.length + 1) = o1.toPair := by
  unfold strOf pat
  simp

theorem strOf_pat_after (l : List Out) (o1 : Out) (i j : ℕ) (hj1 : l.length + 1 < j) :
    (strOf (l ++ pat o1 i) j).1 = 0 ∧ (strOf (l ++ pat o1 i) j).2 = false := by
  unfold strOf pat
  have hj0 : j ≠ 0 := by omega
  simp only [hj0, ↓reduceIte]
  rw [List.getD_append_right _ _ _ _ (by omega)]
  rw [show j - 1 - l.length = (j - 2 - l.length) + 1 by omega, List.getD_cons_succ]
  rcases Nat.lt_or_ge (j - 2 - l.length) i with hi | hi
  · rw [List.getD_eq_getElem _ _ (by simpa using hi)]; simp [Out.empty, Out.toPair]
  · rw [List.getD_eq_default _ _ (by simpa using hi)]; simp [Out.empty, Out.toPair]

theorem pat_snoc (o1 : Out) (i : ℕ) : pat o1 i ++ [Out.empty] = pat o1 (i + 1) := by
  unfold pat; simp [List.replicate_succ']

/-- **One pattern, from below.** For `G ≥ 0`, the expectation over the next phase
is at least the probability of the pattern times `G` at its end. -/
theorem phase_lower (hB : κ.Within B) (helo : 0 ≤ B.elo) (hΔ : 0 < Δ) {l : List Out} (hlM : l.length + Δ + 1 ≤ M)
    {G : List Out → ℝ} (hG : ∀ h, 0 ≤ G h) (o1 : Out) (ho1 : o1.hon ≠ 0) :
    κ.p l o1 * B.elo ^ Δ * G (l ++ pat o1 Δ) ≤ ExPh (κ := κ) (PE Δ M) (M - l.length - 1) G l := by
  have hlen : ∀ i, (l ++ pat o1 i).length = l.length + 1 + i := fun i => by simp [pat]; omega
  -- not a phase end before the pattern finishes
  have hnot : ∀ i < Δ, ¬ PE Δ M (l ++ pat o1 i) := by
    intro i hi
    rintro (h1 | ⟨-, h2⟩)
    · rw [hlen] at h1; omega
    · have := h2 (l.length + 1) (by rw [hlen]; omega) (by rw [hlen]; omega) (by omega)
      rw [strOf_pat_first] at this
      exact ho1 (Fin.ext (by simpa [Out.toPair] using this))
  have hend : PE Δ M (l ++ pat o1 Δ) := by
    by_cases hM : (l ++ pat o1 Δ).length = M
    · exact Or.inl hM
    · refine Or.inr ⟨by rw [hlen] at hM ⊢; omega, ?_⟩
      intro j h1 h2 _
      rw [hlen] at h1 h2
      exact (strOf_pat_after l o1 Δ j (by omega)).1
  -- backward induction along the pattern
  have key : ∀ j ≤ Δ, B.elo ^ j * G (l ++ pat o1 Δ) ≤
      ExU (κ := κ) (PE Δ M) (M - l.length - 1 - (Δ - j)) G (l ++ pat o1 (Δ - j)) := by
    intro j hj
    induction j with
    | zero => simp only [pow_zero, one_mul, Nat.sub_zero]; rw [ExU_stop _ _ _ hend]
    | succ j ih =>
      have ih' := ih (by omega)
      have hfuel : M - l.length - 1 - (Δ - (j + 1)) = (M - l.length - 1 - (Δ - j)) + 1 := by omega
      rw [hfuel]
      have hs := ExU_ge_snoc (κ := κ) hG (hnot (Δ - (j + 1)) (by omega))
        (M - l.length - 1 - (Δ - j)) Out.empty
      rw [List.append_assoc, pat_snoc, show Δ - (j + 1) + 1 = Δ - j by omega] at hs
      have he := hB.elo (l ++ pat o1 (Δ - (j + 1)))
      have hU := ExU_nonneg (κ := κ) (PE Δ M) (M - l.length - 1 - (Δ - j)) hG (l ++ pat o1 (Δ - j))
      have he0 : 0 ≤ B.elo ^ j * G (l ++ pat o1 Δ) := mul_nonneg (pow_nonneg helo _) (hG _)
      calc B.elo ^ (j + 1) * G (l ++ pat o1 Δ) = B.elo * (B.elo ^ j * G (l ++ pat o1 Δ)) := by ring
        _ ≤ κ.p (l ++ pat o1 (Δ - (j + 1))) Out.empty *
            ExU (κ := κ) (PE Δ M) (M - l.length - 1 - (Δ - j)) G (l ++ pat o1 (Δ - j)) := by
            apply mul_le_mul he ih' he0 (κ.nonneg _ _)
        _ ≤ _ := hs
  have h0 := key Δ le_rfl
  simp only [Nat.sub_self, Nat.sub_zero] at h0
  unfold ExPh
  have hsingle : κ.p l o1 * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o1]) ≤
      ∑ o, κ.p l o * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o]) :=
    Finset.single_le_sum (f := fun o => κ.p l o * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o]))
      (fun o _ => mul_nonneg (κ.nonneg l o) (ExU_nonneg _ _ hG _)) (Finset.mem_univ o1)
  have hp0 : pat o1 0 = [o1] := rfl
  rw [hp0] at h0
  calc κ.p l o1 * B.elo ^ Δ * G (l ++ pat o1 Δ) = κ.p l o1 * (B.elo ^ Δ * G (l ++ pat o1 Δ)) := by ring
    _ ≤ κ.p l o1 * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o1]) :=
        mul_le_mul_of_nonneg_left h0 (κ.nonneg l o1)
    _ ≤ _ := hsingle

/-- The pattern is a crossing, with no adversarial slot and an honest success. -/
theorem pat_cross (l : List Out) (o1 : Out) (ho1 : o1.hon = 1) (ha : o1.adv = false) :
    Cross (strOf (l ++ pat o1 Δ)) 0 l.length (l.length + 1 + Δ) := by
  refine ⟨?_, l.length + 1, by omega, by omega, Nat.zero_le _, ?_, ?_⟩
  · unfold advCnt
    rw [Finset.card_eq_zero, Finset.filter_eq_empty_iff]
    intro i hi
    rw [Finset.mem_Ioc] at hi
    rcases Nat.lt_or_ge (l.length + 1) i with h | h
    · simp [(strOf_pat_after l o1 Δ i h).2]
    · have : i = l.length + 1 := by omega
      subst this; rw [strOf_pat_first]; simp [Out.toPair, ha]
  · rw [strOf_pat_first]; simp [Out.toPair, ho1]
  · intro i h1 h2 h3
    exact (strOf_pat_after l o1 Δ i (by omega)).1

end Cryptarchia.Prob
