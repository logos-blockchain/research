module

public import Cryptarchia.Prob.Burst
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
import Mathlib.Tactic.Monotonicity.Lemmas
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
import Mathlib.Topology.Sheaves.Presheaf
import Std.Tactic.BVDecide.Normalize.BitVec
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# Phase expectations through a small automaton

A sharper version of `phase_upper`. Over one phase, we bound

  `E[θ^L · x^A · g(min(A, 2), B, U2)]`

for any nonnegative table `g`, where `A` counts adversarial slots, `B` says the phase
has an honest success, and `U2` says it has at least two slots with honest successes.
During a burst the automaton tracks the slots since the last honest success (`q`),
`min(A, 2)` and `U2`; a solution `v` of its recursion (`AutoSol`) bounds the rest of
the phase from every state (`phase_autoT`). Each step is bounded for every
next-slot distribution in the band (`slot_sum4`).
-/

@[expose] public section

namespace Cryptarchia.Prob

section

open Finset Settle

variable {κ : Kern} {B : Band}

/-- **One slot, four outcome classes.** `F h a` is the value after a slot with
(`h`) or without an honest success and with (`a`) or without an adversarial one. -/
theorem slot_sum4 {l : List Out} (hB : κ.BandAt B l) (F : Bool → Bool → ℝ) :
    ∑ o, κ.p l o * F (decide (o.hon ≠ 0)) o.adv ≤
      F false false + (F false true - F false false) * (if F false false ≤ F false true then B.amax else B.alo) +
        (F true false - F false false) * (if F false false ≤ F true false then B.hhi else B.hlo) +
        (F true true - F true false - F false true + F false false) *
          (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo) := by
  set c1 := F false true - F false false
  set c2 := F true false - F false false
  set c3 := F true true - F true false - F false true + F false false
  have hsplit : ∀ o, κ.p l o * F (decide (o.hon ≠ 0)) o.adv =
      κ.p l o * F false false + c1 * (if o.adv = true then κ.p l o else 0) +
        c2 * (if o.hon ≠ 0 then κ.p l o else 0) + c3 * (if o.hon ≠ 0 ∧ o.adv = true then κ.p l o else 0) := by
    intro o
    by_cases h1 : o.hon ≠ 0 <;> by_cases h2 : o.adv = true <;> simp [h1, h2, c1, c2, c3] <;> ring
  simp only [hsplit, Finset.sum_add_distrib, ← Finset.mul_sum, ← Finset.sum_mul, κ.sum_one, one_mul]
  have e1 : ∑ o, (if o.adv = true then κ.p l o else 0) = κ.pr l (fun o => o.adv = true) := rfl
  have e2 : ∑ o, (if o.hon ≠ 0 then κ.p l o else 0) = κ.pr l (fun o => o.hon ≠ 0) := rfl
  have e3 : ∑ o, (if o.hon ≠ 0 ∧ o.adv = true then κ.p l o else 0) =
      κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) := rfl
  rw [e1, e2, e3]
  have ha := hB.amax
  have ha0 := pr_nonneg (κ := κ) l (fun o => o.adv = true)
  have hh := hB.hhi
  have hlo := hB.hlo
  have hha := hB.hahi
  have hha0 := pr_nonneg (κ := κ) l (fun o => o.hon ≠ 0 ∧ o.adv = true)
  have t1 : c1 * κ.pr l (fun o => o.adv = true) ≤
      c1 * (if F false false ≤ F false true then B.amax else B.alo) := by
    split_ifs with h
    · exact mul_le_mul_of_nonneg_left ha (by simp only [c1]; linarith)
    · push Not at h; exact mul_le_mul_of_nonpos_left (hB.alo) (by simp only [c1]; linarith)
  have t2 : c2 * κ.pr l (fun o => o.hon ≠ 0) ≤
      c2 * (if F false false ≤ F true false then B.hhi else B.hlo) := by
    split_ifs with h
    · exact mul_le_mul_of_nonneg_left hh (by simp only [c2]; linarith)
    · push Not at h; exact mul_le_mul_of_nonpos_left hlo (by simp only [c2]; linarith)
  have t3 : c3 * κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) ≤
      c3 * (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo) := by
    split_ifs with h
    · exact mul_le_mul_of_nonneg_left hha (by simp only [c3]; linarith)
    · push Not at h; exact mul_le_mul_of_nonpos_left (hB.halo) (by simp only [c3]; linarith)
  linarith

/-- The bound `slot_sum4` gives, as a function. -/
noncomputable def slot4 (B : Band) (F : Bool → Bool → ℝ) : ℝ :=
  F false false + (F false true - F false false) * (if F false false ≤ F false true then B.amax else B.alo) +
    (F true false - F false false) * (if F false false ≤ F true false then B.hhi else B.hlo) +
    (F true true - F true false - F false true + F false false) *
      (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo)

/-! ## The phase summary -/

/-- Honest slots in `(a, b]`. -/
def honCnt (w : CStr) (a b : ℕ) : ℕ := ((Finset.Ioc a b).filter (fun j => (w j).1 ≠ 0)).card

/-- `min(A, 2)`. -/
def acap (n : ℕ) : Fin 3 := ⟨min n 2, by omega⟩

/-- The weight of a history for a phase that started at `m`, with table `g`. -/
noncomputable def Wt2 (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ) (m : ℕ) (h : List Out) : ℝ :=
  θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length *
    g (acap (advCnt (strOf h) m h.length)) (decide (1 ≤ honCnt (strOf h) m h.length))
      (decide (2 ≤ honCnt (strOf h) m h.length))

/-- One step of the automaton recursion at state `(q, a, u2)`, for adversary factor `x`,
tilt `θ`, terminal table `g` and table `w`: the bound of the next slot's outcomes. -/
noncomputable def stepR (B : Band) (Δ : ℕ) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ) (w : ℕ → Fin 3 → Bool → ℝ)
    (q : ℕ) (a : Fin 3) (u2 : Bool) : ℝ :=
  θ * slot4 B (fun hh aa => (if aa then x else 1) *
    (if hh then w 0 (acap (a.val + if aa then 1 else 0)) true
      else if q + 1 = Δ then g (acap (a.val + if aa then 1 else 0)) true u2
        else w (q + 1) (acap (a.val + if aa then 1 else 0)) u2))

/-- A solution of the automaton recursion for adversary factor `x`, tilt `θ` and
terminal table `g`: `v q a u2` bounds the rest of a burst `q` slots after its last
honest success, with `min(A, 2) = a` and `U2 = u2` so far. -/
structure AutoSol (B : Band) (Δ : ℕ) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ)
    (v : ℕ → Fin 3 → Bool → ℝ) : Prop where
  /-- a run cut by the horizon is covered -/
  term : ∀ q < Δ, ∀ a u2, g a true u2 ≤ v q a u2
  /-- the recursion -/
  step : ∀ q < Δ, ∀ a u2, stepR B Δ x θ g v q a u2 ≤ v q a u2

variable {Δ M : ℕ}

theorem honCnt_succ (w : CStr) {a b : ℕ} (hab : a ≤ b) :
    honCnt w a (b + 1) = honCnt w a b + (if (w (b + 1)).1 ≠ 0 then 1 else 0) := by
  unfold honCnt
  rw [show Finset.Ioc a (b + 1) = insert (b + 1) (Finset.Ioc a b) by
    ext i; simp only [Finset.mem_Ioc, Finset.mem_insert]; omega, Finset.filter_insert]
  split_ifs with h
  · rw [Finset.card_insert_of_notMem (by simp)]
  · rw [add_zero]

theorem honCnt_congr {w w' : CStr} {a b : ℕ} (h : SimOn w w' a b) : honCnt w a b = honCnt w' a b := by
  unfold honCnt
  congr 1
  apply Finset.filter_congr
  intro j hj
  rw [Finset.mem_Ioc] at hj
  exact not_congr (h j hj.1 hj.2).1

theorem honCnt_snoc (x : List Out) (o : Out) {m : ℕ} (hm : m ≤ x.length) :
    honCnt (strOf (x ++ [o])) m (x.length + 1) = honCnt (strOf x) m x.length + (if o.hon ≠ 0 then 1 else 0) := by
  rw [honCnt_succ _ hm, honCnt_congr (strOf_sim x [o] m), strOf_last]
  congr 1
  simp only [Out.toPair, ne_eq]
  by_cases h : o.hon = 0
  · simp [h]
  · have : ¬ (o.hon.val = 0) := fun h' => h (Fin.ext h')
    simp [h, this]

theorem acap_add (n : ℕ) (b : ℕ) (hb : b ≤ 1) : acap (n + b) = acap ((acap n).val + b) := by
  unfold acap; ext; simp; omega

theorem Wt2_snoc {x θ : ℝ} {g : Fin 3 → Bool → Bool → ℝ} {m : ℕ} (h : List Out) (o : Out) (hm : m ≤ h.length) :
    Wt2 x θ g m (h ++ [o]) =
      θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length * (θ * (if o.adv then x else 1)) *
        g (acap ((acap (advCnt (strOf h) m h.length)).val + if o.adv then 1 else 0))
          (decide (1 ≤ honCnt (strOf h) m h.length + if o.hon ≠ 0 then 1 else 0))
          (decide (2 ≤ honCnt (strOf h) m h.length + if o.hon ≠ 0 then 1 else 0)) := by
  unfold Wt2
  simp only [List.length_append, List.length_singleton]
  rw [advCnt_snoc h o hm, honCnt_snoc h o hm, show h.length + 1 - m = (h.length - m) + 1 by omega,
    pow_succ, ← acap_add _ _ (by split_ifs <;> norm_num)]
  by_cases ha : o.adv = true
  · simp only [ha, ↓reduceIte, pow_succ]; ring
  · simp only [ha, Bool.false_eq_true, ↓reduceIte, add_zero, mul_one]; ring

/-- The bound for one phase from its start. -/
noncomputable def autoBound (B : Band) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ) (v : ℕ → Fin 3 → Bool → ℝ) : ℝ :=
  θ * slot4 B (fun hh aa => (if aa then x else 1) *
    (if hh then v 0 (acap (if aa then 1 else 0)) false else g (acap (if aa then 1 else 0)) false false))

end

/-!
## Phases cut at `G` slots, with one band per epoch

`phase_autoT` bounds a phase cut at `G` slots through a table per history, each
satisfying the recursion of the history's band and not increasing along the phase. One
table for every history, cut at the horizon, bounds any phase. With one member per epoch
(`Kern.EpochFam`), a phase can cross an epoch boundary, where the member changes.
Truncated at `G` slots (`G + 1 < EL`), a phase crosses at most one boundary. So a
**one-switch automaton** bounds it (`AutoSolE`): for each member a solution `vpost`
of its own recursion, a table `vmax` above all of them, and for each member a
solution `vpre` of its recursion that also stays above `vmax`, where the phase may
still switch to any member. Phases longer than `G` get weight `0` (`truncG`); the
long-phase term of the settlement bound pays for them.
-/

open Finset Settle

variable {κ : Kern} {Δ M EL K : ℕ} {fam : Fin K → Band}

/-- A pre-switch table of one member: above `vmax`, and its own recursion. -/
structure PreSol (B : Band) (Δ : ℕ) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ)
    (vmax vpre : ℕ → Fin 3 → Bool → ℝ) : Prop where
  dom : ∀ q < Δ, ∀ a u, vmax q a u ≤ vpre q a u
  step : ∀ q < Δ, ∀ a u, stepR B Δ x θ g vpre q a u ≤ vpre q a u

/-- **A one-switch automaton solution** for adversary factor `x`, tilt `θ`, table `g`. -/
structure AutoSolE (fam : Fin K → Band) (Δ : ℕ) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ)
    (vpre vpost : Fin K → ℕ → Fin 3 → Bool → ℝ) (vmax : ℕ → Fin 3 → Bool → ℝ) : Prop where
  /-- after the switch: each member's own recursion -/
  post : ∀ k, AutoSol (fam k) Δ x θ g (vpost k)
  /-- `vmax` is above every member's post-switch table -/
  maxp : ∀ k, ∀ q < Δ, ∀ a u, vpost k q a u ≤ vmax q a u
  /-- before the switch: above `vmax` (a switch may still come), and the member's own recursion -/
  pre : ∀ k, PreSol (fam k) Δ x θ g vmax (vpre k)

/-- A phase function, cut at `G` slots after `m`. -/
noncomputable def truncG (m G : ℕ) (f : List Out → ℝ) (h : List Out) : ℝ := if h.length ≤ m + G then f h else 0

theorem truncG_nonneg {m G : ℕ} {f : List Out → ℝ} (hf : ∀ h, 0 ≤ f h) (h : List Out) : 0 ≤ truncG m G f h := by
  unfold truncG; split_ifs; exacts [hf h, le_rfl]

/-- An epoch boundary between history lengths `m` (exclusive) and `n` (inclusive). -/
def Swtd (EL m n : ℕ) : Prop := ∃ j, m < j ∧ j ≤ n ∧ (j + 1) % EL = 0

theorem swtd_succ {EL m n : ℕ} (hmn : m ≤ n) : Swtd EL m (n + 1) ↔ Swtd EL m n ∨ (n + 2) % EL = 0 := by
  constructor
  · rintro ⟨j, h1, h2, h3⟩
    rcases Nat.lt_or_ge j (n + 1) with h | h
    · exact Or.inl ⟨j, h1, by omega, h3⟩
    · exact Or.inr (by rw [show n + 2 = j + 1 by omega]; exact h3)
  · rintro (⟨j, h1, h2, h3⟩ | h)
    · exact ⟨j, h1, by omega, h3⟩
    · exact ⟨n + 1, by omega, le_rfl, h⟩

/-- Two boundaries are at least `EL` apart. -/
theorem swtd_unique {EL m n : ℕ} (hEL : 0 < EL) (hs : Swtd EL m n) {j : ℕ} (hj1 : m < j)
    (hj2 : j ≤ n + 1) (hj : (j + 1) % EL = 0) (hn : n + 1 < m + EL) : j ≤ n := by
  obtain ⟨i, h1, h2, h3⟩ := hs
  by_contra hc
  have hji : j = n + 1 := by omega
  have ei := Nat.mod_add_div (i + 1) EL
  have ej := Nat.mod_add_div (j + 1) EL
  rw [h3, zero_add] at ei
  rw [hj, zero_add] at ej
  have hq : (i + 1) / EL < (j + 1) / EL := by
    by_contra hq; push Not at hq
    have := Nat.mul_le_mul_left EL hq
    omega
  have := Nat.mul_le_mul_left EL (Nat.succ_le_of_lt hq)
  rw [Nat.mul_succ] at this
  omega

theorem ExU_zero_beyond {S : List Out → Prop} [DecidablePred S] {F : List Out → ℝ} {L : ℕ}
    (hF : ∀ h', L < h'.length → F h' = 0) : ∀ n (h : List Out), L ≤ h.length → ¬ S h →
      ExU (κ := κ) S (n + 1) F h = 0
  | n, h, hl, hs => by
    rw [ExU_go _ _ _ hs]
    refine Finset.sum_eq_zero fun o _ => ?_
    have hl' : L < (h ++ [o]).length := by simp; omega
    cases n with
    | zero => rw [ExU_zero, hF _ hl', mul_zero]
    | succ n =>
      by_cases hs' : S (h ++ [o])
      · rw [ExU_stop _ _ _ hs', hF _ hl', mul_zero]
      · rw [ExU_zero_beyond hF n (h ++ [o]) hl'.le hs', mul_zero]

section AutoT

variable {x θ : ℝ} {g : Fin 3 → Bool → Bool → ℝ} (T : List Out → ℕ → Fin 3 → Bool → ℝ)
  (bandOf : List Out → Band) (hTb : ∀ h, κ.BandAt (bandOf h) h) (hg0 : ∀ a b u, 0 ≤ g a b u) {m G : ℕ}
  (hTnext : ∀ h, m ≤ h.length → h.length + 1 ≤ m + G → ∀ o, ∀ q < Δ, ∀ a u, T (h ++ [o]) q a u ≤ T h q a u)
  (hTstep : ∀ h, m ≤ h.length → h.length < m + G → ∀ q < Δ, ∀ a u, stepR (bandOf h) Δ x θ g (T h) q a u ≤ T h q a u)
  (hTterm : ∀ h, ∀ q < Δ, ∀ a u, g a true u ≤ T h q a u)

include hTb hg0 hTnext hTstep hTterm in
/-- **Inside a burst, with abstract tables**, truncated at `G` slots. -/
theorem auto_leT (hx : 0 ≤ x) (hθ : 0 ≤ θ) :
    ∀ (n : ℕ) (h : List Out) (q : ℕ), InBurst m h q → q < Δ → h.length + n = M → h.length ≤ m + G →
      ExU (κ := κ) (PE Δ M) n (truncG m G (Wt2 x θ g m)) h ≤
        θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length *
          T h q (acap (advCnt (strOf h) m h.length)) (decide (2 ≤ honCnt (strOf h) m h.length))
  | 0, h, q, hb, hq, hn, hG' => by
    have hPE : PE Δ M h := Or.inl (by omega)
    rw [ExU_stop _ _ _ hPE]
    unfold truncG; rw [if_pos hG']
    have hB1 : 1 ≤ honCnt (strOf h) m h.length := by
      obtain ⟨i, h1, h2, h3⟩ := hb.honIn
      unfold honCnt; exact Finset.card_pos.2 ⟨i, by simp; exact ⟨⟨h1, h2⟩, h3⟩⟩
    unfold Wt2
    rw [show decide (1 ≤ honCnt (strOf h) m h.length) = true by simpa using hB1]
    exact mul_le_mul_of_nonneg_left (hTterm h q hq _ _) (by positivity)
  | n + 1, h, q, hb, hq, hn, hG' => by
    classical
    have hm : m ≤ h.length := by have := hb.p_gt; omega
    have hnPE : ¬ PE Δ M h := by
      rintro (h1 | ⟨-, h2⟩)
      · omega
      · exact hb.not_quiet hq h2
    have hvn : ∀ q' < Δ, ∀ a' u', 0 ≤ T h q' a' u' := fun q' hq' a' u' =>
      le_trans (hg0 _ _ _) (hTterm h q' hq' a' u')
    rcases Nat.eq_or_lt_of_le hG' with hGe | hGl
    · -- the truncation: nothing more counts
      rw [ExU_zero_beyond (κ := κ) (L := m + G) (fun h' hl => by unfold truncG; rw [if_neg (by omega)])
        n h (by omega) hnPE]
      exact mul_nonneg (by positivity) (hvn q hq _ _)
    rw [ExU_go _ _ _ hnPE]
    have hBh := hTb h
    have hnext : ∀ o, ∀ q' < Δ, ∀ a' u', T (h ++ [o]) q' a' u' ≤
        T h q' a' u' := fun o q' hq' a' u' =>
      hTnext h hm (show h.length + 1 ≤ m + G by omega) o q' hq' a' u'
    set W0 := θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length with hW0
    have hW0n : 0 ≤ W0 := by positivity
    set a := acap (advCnt (strOf h) m h.length) with ha
    set nh := honCnt (strOf h) m h.length with hnh
    have hnh1 : 1 ≤ nh := by
      obtain ⟨i, h1, h2, h3⟩ := hb.honIn
      simp only [hnh]; unfold honCnt; exact Finset.card_pos.2 ⟨i, by simp; exact ⟨⟨h1, h2⟩, h3⟩⟩
    set v := T h with hvdef
    set F : Bool → Bool → ℝ := fun hh aa => (if aa then x else 1) *
      (if hh then v 0 (acap (a.val + if aa then 1 else 0)) true
        else if q + 1 = Δ then g (acap (a.val + if aa then 1 else 0)) true (decide (2 ≤ nh))
          else v (q + 1) (acap (a.val + if aa then 1 else 0)) (decide (2 ≤ nh))) with hF
    have hcont : ∀ o, ExU (κ := κ) (PE Δ M) n (truncG m G (Wt2 x θ g m)) (h ++ [o]) ≤ W0 * θ * F (decide (o.hon ≠ 0)) o.adv := by
      intro o
      have hWo := Wt2_snoc (x := x) (θ := θ) (g := g) h o hm
      rw [← hW0, ← ha, ← hnh] at hWo
      have hlen : (h ++ [o]).length + n = M := by simp; omega
      have hAo : acap (advCnt (strOf (h ++ [o])) m (h ++ [o]).length) =
          acap (a.val + if o.adv then 1 else 0) := by
        simp only [List.length_append, List.length_singleton]
        rw [advCnt_snoc h o hm, acap_add _ _ (by split_ifs <;> norm_num)]
      have hHo : honCnt (strOf (h ++ [o])) m (h ++ [o]).length = nh + if o.hon ≠ 0 then 1 else 0 := by
        simp only [List.length_append, List.length_singleton]; rw [honCnt_snoc h o hm]
      have hpowo : θ ^ ((h ++ [o]).length - m) * x ^ advCnt (strOf (h ++ [o])) m (h ++ [o]).length =
          W0 * (θ * (if o.adv then x else 1)) := by
        simp only [List.length_append, List.length_singleton]
        rw [advCnt_snoc h o hm, show h.length + 1 - m = (h.length - m) + 1 by omega, pow_succ, hW0]
        by_cases hao : o.adv = true
        · simp only [hao, ↓reduceIte, pow_succ]; ring
        · simp only [hao, Bool.false_eq_true, ↓reduceIte, add_zero, mul_one]; ring
      have hxa : 0 ≤ (if o.adv then x else 1) := by split_ifs <;> linarith
      set a' := acap (a.val + if o.adv then 1 else 0) with ha'
      by_cases ho : o.hon ≠ 0
      · have hb' := hb.snoc_hon o ho
        have hdec : decide (o.hon ≠ 0) = true := by simpa using ho
        have hFt : F true o.adv = (if o.adv then x else 1) * v 0 a' true := rfl
        rw [hdec, hFt]
        have hi1 : (if o.hon ≠ 0 then 1 else 0) = 1 := if_pos ho
        rw [hi1] at hWo hHo
        have d1 : decide (1 ≤ nh + 1) = true := decide_eq_true (by omega)
        have d2 : decide (2 ≤ nh + 1) = true := decide_eq_true (by omega)
        by_cases hM : (h ++ [o]).length = M
        · rw [ExU_stop _ _ _ (Or.inl hM)]
          unfold truncG; rw [if_pos (by simp; omega), hWo, d1, d2]
          have := hTterm h 0 (by have := hb.p_gt; omega) a' true
          calc W0 * (θ * (if o.adv then x else 1)) * g a' true true
              ≤ W0 * (θ * (if o.adv then x else 1)) * v 0 a' true :=
                mul_le_mul_of_nonneg_left this (by positivity)
            _ = _ := by ring
        · have hΔ0 : 0 < Δ := by omega
          have := auto_leT hx hθ n (h ++ [o]) 0 hb' hΔ0 hlen (by simp; omega)
          rw [hpowo, hAo, hHo, d2] at this
          calc _ ≤ W0 * (θ * (if o.adv then x else 1)) * T (h ++ [o]) 0 a' true := this
            _ ≤ W0 * (θ * (if o.adv then x else 1)) * v 0 a' true :=
                mul_le_mul_of_nonneg_left (hnext o 0 hΔ0 a' true) (by positivity)
            _ = _ := by ring
      · push Not at ho
        have hdec : decide (o.hon ≠ 0) = false := by simpa using ho
        have hb' := hb.snoc_empty o ho
        have hi0 : (if o.hon ≠ 0 then 1 else 0) = 0 := if_neg (by simpa using ho)
        rw [hi0, Nat.add_zero] at hWo hHo
        have d1 : decide (1 ≤ nh) = true := decide_eq_true hnh1
        have hFf : F false o.adv = (if o.adv then x else 1) *
            (if q + 1 = Δ then g a' true (decide (2 ≤ nh)) else v (q + 1) a' (decide (2 ≤ nh))) := rfl
        rw [hdec, hFf]
        by_cases hq1 : q + 1 < Δ
        · rw [if_neg (show ¬ (q + 1 = Δ) by omega)]
          by_cases hM : (h ++ [o]).length = M
          · rw [ExU_stop _ _ _ (Or.inl hM)]
            unfold truncG; rw [if_pos (by simp; omega), hWo, d1]
            have := hTterm h (q + 1) hq1 a' (decide (2 ≤ nh))
            calc W0 * (θ * (if o.adv then x else 1)) * g a' true (decide (2 ≤ nh))
                ≤ W0 * (θ * (if o.adv then x else 1)) * v (q + 1) a' (decide (2 ≤ nh)) :=
                  mul_le_mul_of_nonneg_left this (by positivity)
              _ = _ := by ring
          · have := auto_leT hx hθ n (h ++ [o]) (q + 1) hb' hq1 hlen (by simp; omega)
            rw [hpowo, hAo, hHo] at this
            calc _ ≤ W0 * (θ * (if o.adv then x else 1)) *
                  T (h ++ [o]) (q + 1) a' (decide (2 ≤ nh)) := this
              _ ≤ W0 * (θ * (if o.adv then x else 1)) * v (q + 1) a' (decide (2 ≤ nh)) :=
                  mul_le_mul_of_nonneg_left (hnext o (q + 1) hq1 a' _) (by positivity)
              _ = _ := by ring
        · rw [if_pos (show q + 1 = Δ by omega)]
          have hPE : PE Δ M (h ++ [o]) := by
            by_cases hM : (h ++ [o]).length = M
            · exact Or.inl hM
            · exact Or.inr ⟨by simp at hM ⊢; omega, hb'.quiet_of (by omega)⟩
          rw [ExU_stop _ _ _ hPE]
          unfold truncG; rw [if_pos (by simp; omega), hWo, d1]
          apply le_of_eq; ring
    calc ∑ o, κ.p h o * ExU (κ := κ) (PE Δ M) n (truncG m G (Wt2 x θ g m)) (h ++ [o])
        ≤ ∑ o, κ.p h o * (W0 * θ * F (decide (o.hon ≠ 0)) o.adv) :=
          Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (hcont o) (κ.nonneg h o)
      _ = W0 * θ * ∑ o, κ.p h o * F (decide (o.hon ≠ 0)) o.adv := by
          rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun o _ => by ring
      _ ≤ W0 * θ * slot4 (bandOf h) F := mul_le_mul_of_nonneg_left (slot_sum4 hBh F) (by positivity)
      _ = W0 * (θ * slot4 (bandOf h) F) := by ring
      _ ≤ W0 * v q a (decide (2 ≤ nh)) := mul_le_mul_of_nonneg_left (hTstep h hm hGl q hq a _) hW0n

include hTb hg0 hTnext hTstep hTterm in
/-- **One phase, with abstract tables**, truncated at `G` slots: at most the automaton
bound of the start's band with the start's table. -/
theorem phase_autoT (hx : 0 ≤ x) (hθ : 0 ≤ θ) (hG1 : 1 ≤ G) (hΔ : 0 < Δ) {l : List Out} (hl : Start Δ l)
    (hlm : l.length = m) (hlM : l.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - l.length - 1) (truncG l.length G (Wt2 x θ g l.length)) l ≤ autoBound (bandOf l) x θ g (T l) := by
  classical
  subst hlm
  have hBl := hTb l
  set v := T l with hvdef
  have hvl : T l = v := rfl
  have hnext : ∀ o, ∀ q' < Δ, ∀ a' u', T (l ++ [o]) q' a' u' ≤ v q' a' u' :=
    fun o q' hq' a' u' => hTnext l le_rfl (by omega) o q' hq' a' u'
  set m := l.length with hm
  set F : Bool → Bool → ℝ := fun hh aa => (if aa then x else 1) *
    (if hh then v 0 (acap (if aa then 1 else 0)) false else g (acap (if aa then 1 else 0)) false false) with hF
  have hA0 : advCnt (strOf l) m m = 0 := advCnt_self _
  have hH0 : honCnt (strOf l) m m = 0 := by unfold honCnt; simp
  have hcont : ∀ o, ExU (κ := κ) (PE Δ M) (M - m - 1) (truncG m G (Wt2 x θ g m)) (l ++ [o]) ≤ θ * F (decide (o.hon ≠ 0)) o.adv := by
    intro o
    have hWo := Wt2_snoc (x := x) (θ := θ) (g := g) l o (le_of_eq hm.symm)
    rw [← hm, hA0, hH0, Nat.sub_self, pow_zero, pow_zero, one_mul, one_mul] at hWo
    have hacap : acap ((acap 0).val + if o.adv then 1 else 0) = acap (if o.adv then 1 else 0) := by
      unfold acap; ext; simp
    rw [hacap] at hWo
    have hlen : (l ++ [o]).length + (M - m - 1) = M := by simp; omega
    have hxa : 0 ≤ (if o.adv then x else 1) := by split_ifs <;> linarith
    by_cases ho : o.hon ≠ 0
    · have hdec : decide (o.hon ≠ 0) = true := by simpa using ho
      rw [hdec]; simp only [hF, ↓reduceIte]
      have hb : InBurst m (l ++ [o]) 0 := by
        refine ⟨by simp [hm], ?_, ?_⟩
        · simp only [List.length_append, List.length_singleton, Nat.sub_zero]
          rw [strOf_last]; simp only [Out.toPair]; intro h'; exact ho (Fin.ext h')
        · intro i h1 h2; simp at h1 h2; omega
      have hHo : honCnt (strOf (l ++ [o])) m (l ++ [o]).length = 1 := by
        simp only [List.length_append, List.length_singleton]
        rw [honCnt_snoc l o (le_of_eq hm.symm), ← hm, hH0]; simp [ho]
      have hAo : acap (advCnt (strOf (l ++ [o])) m (l ++ [o]).length) = acap (if o.adv then 1 else 0) := by
        simp only [List.length_append, List.length_singleton]
        rw [advCnt_snoc l o (le_of_eq hm.symm), ← hm, hA0, zero_add]
      have hpow : θ ^ ((l ++ [o]).length - m) * x ^ advCnt (strOf (l ++ [o])) m (l ++ [o]).length =
          θ * (if o.adv then x else 1) := by
        simp only [List.length_append, List.length_singleton]
        rw [advCnt_snoc l o (le_of_eq hm.symm), ← hm, hA0, zero_add, show m + 1 - m = 1 by omega, pow_one]
        split_ifs <;> simp
      by_cases hM : (l ++ [o]).length = M
      · rw [ExU_stop _ _ _ (Or.inl hM)]
        unfold truncG; rw [if_pos (by simp; omega), hWo]
        simp only [ho, ne_eq, not_false_eq_true, ↓reduceIte, zero_add, le_refl, decide_true,
          Nat.one_lt_ofNat, Nat.not_ofNat_le_one, decide_false]
        have := hTterm l 0 hΔ (acap (if o.adv then 1 else 0)) false
        calc θ * (if o.adv then x else 1) * g (acap (if o.adv then 1 else 0)) true false
            ≤ θ * (if o.adv then x else 1) * v 0 (acap (if o.adv then 1 else 0)) false :=
              mul_le_mul_of_nonneg_left this (by positivity)
          _ = _ := by ring
      · have := auto_leT T bandOf hTb hg0 hTnext hTstep hTterm hx hθ _ (l ++ [o]) 0 hb hΔ hlen (by simp; omega)
        rw [hpow, hAo, hHo] at this
        simp only [Nat.not_ofNat_le_one, decide_false] at this
        calc _ ≤ θ * (if o.adv then x else 1) *
              T (l ++ [o]) 0 (acap (if o.adv then 1 else 0)) false := this
          _ ≤ θ * (if o.adv then x else 1) * v 0 (acap (if o.adv then 1 else 0)) false :=
              mul_le_mul_of_nonneg_left (hnext o 0 hΔ _ _) (by positivity)
          _ = _ := by ring
    · push Not at ho
      have hdec : decide (o.hon ≠ 0) = false := by simpa using ho
      rw [hdec]; simp only [hF, Bool.false_eq_true, ↓reduceIte]
      have hPE : PE Δ M (l ++ [o]) := by
        by_cases hM : (l ++ [o]).length = M
        · exact Or.inl hM
        · exact Or.inr ⟨by simp at hM ⊢; omega, by simpa using start_snoc_empty hl o ho⟩
      rw [ExU_stop _ _ _ hPE]
      unfold truncG; rw [if_pos (by simp; omega), hWo]
      simp [ho]
      ring_nf; exact le_refl _
  unfold ExPh autoBound
  calc ∑ o, κ.p l o * ExU (κ := κ) (PE Δ M) (M - m - 1) (truncG m G (Wt2 x θ g m)) (l ++ [o])
      ≤ ∑ o, κ.p l o * (θ * F (decide (o.hon ≠ 0)) o.adv) :=
        Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (hcont o) (κ.nonneg l o)
    _ = θ * ∑ o, κ.p l o * F (decide (o.hon ≠ 0)) o.adv := by
        rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun o _ => by ring
    _ ≤ θ * slot4 (bandOf l) F := mul_le_mul_of_nonneg_left (slot_sum4 hBl F) hθ

end AutoT

section Auto

variable {x θ : ℝ} {g : Fin 3 → Bool → Bool → ℝ} {vpre vpost : Fin K → ℕ → Fin 3 → Bool → ℝ}
  {vmax : ℕ → Fin 3 → Bool → ℝ} (hv : AutoSolE fam Δ x θ g vpre vpost vmax)
  (hg0 : ∀ a b u, 0 ≤ g a b u) (mem : List Out → Fin K) (hband : ∀ h, κ.BandAt (fam (mem h)) h)
  (hmem : ∀ h o, (h.length + 2) % EL ≠ 0 → mem (h ++ [o]) = mem h)

/-- The table for history `h` of a phase that started at `m`. -/
noncomputable def vtab (vpre vpost : Fin K → ℕ → Fin 3 → Bool → ℝ) (EL m : ℕ) (mem : List Out → Fin K)
    (h : List Out) : ℕ → Fin 3 → Bool → ℝ := by
  classical exact if Swtd EL m h.length then vpost (mem h) else vpre (mem h)

include hv hmem in
/-- The next history's table is below the current step table. -/
theorem vtab_next (hEL : 0 < EL) {m G : ℕ} (hG : G + 1 < EL) {h : List Out} (hm : m ≤ h.length)
    (hlen : h.length + 1 ≤ m + G) (o : Out) {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) :
    vtab vpre vpost EL m mem (h ++ [o]) q a u ≤ vtab vpre vpost EL m mem h q a u := by
  classical
  unfold vtab
  simp only [List.length_append, List.length_singleton]
  by_cases hs : Swtd EL m h.length
  · -- already switched: no second boundary within the truncation
    have hnb : (h.length + 2) % EL ≠ 0 := fun hb =>
      absurd (swtd_unique hEL hs (j := h.length + 1) (by omega) le_rfl hb (by omega)) (by omega)
    rw [if_pos ((swtd_succ hm).2 (Or.inl hs)), if_pos hs, hmem h o hnb]
  · rw [if_neg hs]
    by_cases hb : (h.length + 2) % EL = 0
    · rw [if_pos ((swtd_succ hm).2 (Or.inr hb))]
      exact le_trans (hv.maxp _ q hq a u) ((hv.pre _).dom q hq a u)
    · rw [if_neg (fun h' => ((swtd_succ hm).1 h').elim hs hb), hmem h o hb]

include hv in
/-- The step table satisfies the member's recursion. -/
theorem vtab_step {m : ℕ} (h : List Out) : ∀ q < Δ, ∀ a u,
    stepR (fam (mem h)) Δ x θ g (vtab vpre vpost EL m mem h) q a u ≤ vtab vpre vpost EL m mem h q a u := by
  classical
  intro q hq a u
  by_cases hs : Swtd EL m h.length
  · simp only [vtab, hs, ↓reduceIte]; exact (hv.post (mem h)).step q hq a u
  · simp only [vtab, hs, ↓reduceIte]; exact (hv.pre (mem h)).step q hq a u

include hv in
theorem vtab_term {m : ℕ} (h : List Out) : ∀ q < Δ, ∀ a u, g a true u ≤ vtab vpre vpost EL m mem h q a u := by
  classical
  intro q hq a u
  by_cases hs : Swtd EL m h.length
  · simp only [vtab, hs, ↓reduceIte]; exact (hv.post (mem h)).term q hq a u
  · simp only [vtab, hs, ↓reduceIte]
    exact le_trans ((hv.post (mem h)).term q hq a u) (le_trans (hv.maxp (mem h) q hq a u) ((hv.pre (mem h)).dom q hq a u))

include hv hg0 hband hmem in
/-- **One phase, one member per epoch, truncated at `G` slots.** -/
theorem phase_autoE (hx : 0 ≤ x) (hθ : 0 ≤ θ) (hEL : 0 < EL) {G : ℕ} (hG : G + 1 < EL) (hG1 : 1 ≤ G)
    {e : ℝ} (he : ∀ k, autoBound (fam k) x θ g (vpre k) ≤ e) (hΔ : 0 < Δ) {l : List Out} (hl : Start Δ l)
    (hlM : l.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - l.length - 1) (truncG l.length G (Wt2 x θ g l.length)) l ≤ e := by
  classical
  have hvl : vtab vpre vpost EL l.length mem l = vpre (mem l) := by
    unfold vtab; rw [if_neg (fun ⟨j, h1, h2, _⟩ => by omega)]
  refine le_trans (phase_autoT (m := l.length) (G := G) (vtab vpre vpost EL l.length mem) (fun h => fam (mem h)) hband hg0
    (fun h hm hlen o q hq a u => vtab_next hv mem hmem hEL hG hm hlen o hq a u)
    (fun h _ _ => vtab_step hv mem h) (fun h => vtab_term hv mem h) hx hθ hG1 hΔ hl rfl hlM) ?_
  rw [hvl]; exact he (mem l)

/-- **One phase inside an epoch.** If no epoch boundary falls within the `G` slots
after the start, the member stays fixed and each member's own table bounds the
phase (no switch). -/
theorem phase_autoIn {x θ : ℝ} {g : Fin 3 → Bool → Bool → ℝ} {vpost : Fin K → ℕ → Fin 3 → Bool → ℝ}
    (hpost : ∀ k, AutoSol (fam k) Δ x θ g (vpost k)) (hg0 : ∀ a b u, 0 ≤ g a b u) (mem : List Out → Fin K)
    (hband : ∀ h, κ.BandAt (fam (mem h)) h) (hmem : ∀ h o, (h.length + 2) % EL ≠ 0 → mem (h ++ [o]) = mem h)
    (hx : 0 ≤ x) (hθ : 0 ≤ θ) {G : ℕ} (hG1 : 1 ≤ G) {e : ℝ} {l : List Out}
    (he : autoBound (fam (mem l)) x θ g (vpost (mem l)) ≤ e) (hΔ : 0 < Δ) (hl : Start Δ l) (hlM : l.length < M)
    (hnb : ∀ j, l.length < j → j ≤ l.length + G → (j + 1) % EL ≠ 0) :
    ExPh (κ := κ) (PE Δ M) (M - l.length - 1) (truncG l.length G (Wt2 x θ g l.length)) l ≤ e :=
  (phase_autoT (m := l.length) (G := G) (fun h => vpost (mem h)) (fun h => fam (mem h)) hband hg0
    (fun h hm hlen o q _ a u => by rw [hmem h o (hnb (h.length + 1) (by omega) (by omega))])
    (fun h _ _ => (hpost (mem h)).step) (fun h => (hpost (mem h)).term) hx hθ hG1 hΔ hl rfl hlM).trans he

end Auto

end Cryptarchia.Prob
