module

public import Cryptarchia.Prob.Blocks
public import Cryptarchia.Prob.Depth
public import Cryptarchia.Prob.Next
import Cryptarchia.Settle.Mono
public import Cryptarchia.Proof.FinalE
import Cryptarchia.Prob.Good
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Algebra.Order.Ring.Star
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
import Mathlib.Tactic.ReduceModChar
import Mathlib.Topology.Sheaves.Init
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# The probability that the good event fails

`settle_bound`: under any kernel within the band, the probability that the good
event `GoodLS` or the growth condition `GrowthS` fails on the sampled string (with
the greedy phase ends) is at most

  `εLong + εCold + εWin + εReach + εDepth`

(`settleEps`). Each term bounds one bad event of `good_of`; the bad indicator is at
most a sum of nonnegative block products, failure counts, and reach moments
(`bad_le`), whose expectations are bounded by `blocks_le`, `cold_anchor` and
`reach_tail`.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle

/-- Some honest leader. -/
def honQ (o : Out) : Prop := o.hon ≠ 0

/-- An occupied slot. -/
def occQ (o : Out) : Prop := o.hon ≠ 0 ∨ o.adv = true

instance : DecidablePred honQ := fun o => inferInstanceAs (Decidable (o.hon ≠ 0))
instance : DecidablePred occQ := fun o => inferInstanceAs (Decidable (o.hon ≠ 0 ∨ o.adv = true))

theorem strOf_fst (l : List Out) {i : ℕ} (hi : 1 ≤ i) : (strOf l i).1 = (l.getD (i - 1) Out.empty).hon.val := by
  have hi0 : i ≠ 0 := by omega
  unfold strOf; simp [hi0, Out.toPair]

theorem strOf_snd (l : List Out) {i : ℕ} (hi : 1 ≤ i) : (strOf l i).2 = (l.getD (i - 1) Out.empty).adv := by
  have hi0 : i ≠ 0 := by omega
  unfold strOf; simp [hi0, Out.toPair]

theorem honQ_iff (l : List Out) {i : ℕ} (hi : 1 ≤ i) : honQ (l.getD (i - 1) Out.empty) ↔ (strOf l i).1 ≠ 0 := by
  rw [strOf_fst l hi]; unfold honQ; constructor
  · intro h h'; exact h (Fin.ext h')
  · intro h h'; exact h (by rw [h']; rfl)

theorem occQ_iff (l : List Out) {i : ℕ} (hi : 1 ≤ i) :
    occQ (l.getD (i - 1) Out.empty) ↔ (1 ≤ (strOf l i).1 ∨ (strOf l i).2 = true) := by
  have h1 := honQ_iff l hi
  unfold honQ at h1; unfold occQ
  rw [strOf_snd l hi, h1, Nat.one_le_iff_ne_zero]

theorem prod_ite_pow {a : ℝ} (P : ℕ → Prop) [DecidablePred P] (n : ℕ) :
    ∏ i ∈ Finset.range n, (if P i then a else 1) = a ^ ((Finset.range n).filter P).card := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Finset.prod_range_succ, ih, Finset.range_add_one, Finset.filter_insert]
    split_ifs with h
    · rw [Finset.card_insert_of_notMem (by simp), pow_succ]
    · rw [mul_one]

theorem occCnt_succ (w : CStr) {a b : ℕ} (hab : a ≤ b) :
    occCnt w a (b + 1) = occCnt w a b + (if 1 ≤ (w (b + 1)).1 ∨ (w (b + 1)).2 = true then 1 else 0) := by
  unfold occCnt
  rw [show Finset.Ioc a (b + 1) = insert (b + 1) (Finset.Ioc a b) by
    ext i; simp only [Finset.mem_Ioc, Finset.mem_insert]; omega, Finset.filter_insert]
  split_ifs with h
  · rw [Finset.card_insert_of_notMem (by simp)]
  · rw [add_zero]

theorem occ_count (l : List Out) (y : ℕ) : ∀ n,
    ((Finset.range n).filter fun k => occQ (l.getD (y + k) Out.empty)).card = occCnt (strOf l) y (y + n) := by
  intro n
  induction n with
  | zero => simp [occCnt]
  | succ n ih =>
    rw [Finset.range_add_one, Finset.filter_insert, show y + (n + 1) = (y + n) + 1 by omega,
      occCnt_succ _ (by omega), ← ih]
    have := occQ_iff l (i := y + n + 1) (by omega)
    rw [show y + n + 1 - 1 = y + n by omega] at this
    split_ifs with h1 h2 h2
    · rw [Finset.card_insert_of_notMem (by simp)]
    · exact absurd (this.1 h1) h2
    · exact absurd (this.2 h2) h1
    · rw [add_zero]

variable {B : Band} {Δ M : ℕ} {κ : Kern}

theorem pr_occ_le (hB : κ.Within B) (l : List Out) : κ.pr l occQ ≤ 1 - B.elo := by
  have hsum := κ.sum_one l
  have he := hB.elo l
  have h1 : ∑ o, κ.p l o = κ.pr l occQ + ∑ o, (if occQ o then 0 else κ.p l o) := by
    unfold Kern.pr; rw [← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl fun o _ => by split_ifs <;> ring
  have h2 : κ.p l ⟨0, false⟩ ≤ ∑ o, (if occQ o then 0 else κ.p l o) := by
    have := Finset.single_le_sum (f := fun o => if occQ o then 0 else κ.p l o)
      (fun o _ => by split_ifs <;> linarith [κ.nonneg l o]) (Finset.mem_univ (⟨0, false⟩ : Out))
    simpa [occQ] using this
  linarith

/-! ## The bad events as products -/

variable (Δ) in
/-- Every block of `Δ` slots after `y` (up to `G`) has an honest leader. -/
noncomputable def longF (G y : ℕ) (h : List Out) : ℝ :=
  ∏ k ∈ Finset.range (G / Δ), blockG honQ 0 1 y Δ Δ k h

/-- `x` to the number of occupied slots in the window before `t`. -/
noncomputable def winF (Lw : ℕ) (x : ℝ) (t : ℕ) (h : List Out) : ℝ :=
  ∏ k ∈ Finset.range (t - (t - Lw)), blockG occQ 1 x (t - Lw) 1 1 k h

/-- `yy` to the number of blocks with an honest leader. -/
noncomputable def depthF (yy : ℝ) (a Lb T nb : ℕ) (h : List Out) : ℝ :=
  ∏ i ∈ Finset.range nb, blockG honQ 1 yy a Lb T i h

open Classical in
theorem blockG_cases (Q : Out → Prop) [DecidablePred Q] (a0 a1 : ℝ) (y Lb T k : ℕ) (h : List Out) :
    blockG Q a0 a1 y Lb T k h = if hitIn Q (y + k * Lb) T h then a1 else a0 := by
  unfold blockG; rfl

theorem longF_one {G y : ℕ} {h : List Out} (hno : ¬ ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ (strOf h) m) :
    longF Δ G y h = 1 := by
  classical
  unfold longF
  apply Finset.prod_eq_one
  intro k hk
  rw [Finset.mem_range] at hk
  rw [blockG_cases, if_pos]
  by_contra hnot
  apply hno
  refine ⟨y + k * Δ + Δ, ?_, ?_, ?_⟩
  · rcases Nat.eq_zero_or_pos Δ with h0 | h0
    · simp [h0] at hk
    · omega
  · have : (k + 1) * Δ ≤ G := by
      have := Nat.div_mul_le_self G Δ
      nlinarith [Nat.mul_le_mul_right Δ (show k + 1 ≤ G / Δ by omega)]
    nlinarith
  · intro i h1 h2 h3
    have := honQ_iff h h3
    by_contra hne
    exact hnot ⟨i, by omega, by omega, this.2 hne⟩

theorem winF_eq {Lw : ℕ} {x : ℝ} (t : ℕ) (h : List Out) :
    winF Lw x t h = x ^ occCnt (strOf h) (t - Lw) t := by
  classical
  unfold winF
  simp only [blockG_cases]
  have : ∀ k, hitIn occQ (t - Lw + k * 1) 1 h ↔ occQ (h.getD (t - Lw + k) Out.empty) := by
    intro k; unfold hitIn; constructor
    · rintro ⟨i, h1, h2, h3⟩
      have : i = t - Lw + k + 1 := by omega
      subst this; simpa using h3
    · intro hq; exact ⟨t - Lw + k + 1, by omega, by omega, by simpa using hq⟩
  simp only [this]
  rw [prod_ite_pow, occ_count, show t - Lw + (t - (t - Lw)) = t by omega]

theorem depthF_eq {yy : ℝ} {a Lb T nb : ℕ} (h : List Out) [DecidablePred fun i => blockHon (strOf h) a Lb T i] :
    depthF yy a Lb T nb h = yy ^ ((Finset.range nb).filter fun i => blockHon (strOf h) a Lb T i).card := by
  classical
  unfold depthF
  simp only [blockG_cases]
  have : ∀ i, hitIn honQ (a + i * Lb) T h ↔ blockHon (strOf h) a Lb T i := by
    intro i; unfold hitIn blockHon; constructor
    · rintro ⟨j, h1, h2, h3⟩; exact ⟨j, h1, h2, (honQ_iff h (by omega)).1 h3⟩
    · rintro ⟨j, h1, h2, h3⟩; exact ⟨j, h1, h2, (honQ_iff h (by omega)).2 h3⟩
  simp only [this]
  rw [prod_ite_pow]

/-! ## The bad indicator -/

/-- The slots of the growth window of an epoch, after the first `G`. -/
def growLen (E : Env) (Δ G : ℕ) : ℕ := E.c.epochLength - E.c.nonceOffset - Δ - 3 - G

/-- The number of depth blocks in an epoch's growth window. -/
def nbD (E : Env) (Δ G T : ℕ) : ℕ := (growLen E Δ G + Δ) / (T + Δ)

/-- The epochs whose state is fixed by `N`. -/
def nEp (E : Env) (N : ℕ) : ℕ := (N + 2) / E.c.epochLength

theorem blockG_nonneg (Q : Out → Prop) [DecidablePred Q] {a0 a1 : ℝ} (h0 : 0 ≤ a0) (h1 : 0 ≤ a1)
    (y Lb T k : ℕ) (h : List Out) : 0 ≤ blockG Q a0 a1 y Lb T k h := by
  rw [blockG_cases]; split_ifs <;> assumption

/-! ## The bound -/

theorem Ex_div (n : ℕ) (F : List Out → ℝ) (a : ℝ) (l : List Out) :
    Ex κ n (fun x => F x / a) l = Ex κ n F l / a := by
  simp only [div_eq_mul_inv]
  rw [show (fun x => F x * a⁻¹) = (fun x => a⁻¹ * F x) by ext; ring, Ex_mul_const]; ring

end Cryptarchia.Prob
