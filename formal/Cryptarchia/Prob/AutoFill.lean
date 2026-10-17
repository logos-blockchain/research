module

public import Cryptarchia.Prob.AutoZ
public import Cryptarchia.Prob.EvalLit
public import Mathlib.Algebra.Order.Floor.Defs
public import Mathlib.Data.Rat.Floor
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
# Automaton tables computed by the kernel

`AutoZ` checks tables whose seeds (the three entries at `(0, a, true)`) a certificate
supplies. Here the kernel computes the seeds as well, so a certificate needs no tables at all.

* **Fills are solutions by construction** (`fillAllZ_entry`). Every entry of a fill other
  than a seed is at least its floor `lo` and at least each band's step, rounded up. So the
  recursion holds everywhere once it holds at the three seeds (`seedOKZ`): the fill is an
  `AutoSol` or a `PreSol` with no pass over the table (`fill_autoSol`, `fill_preSol`), and
  below the entrywise maximum `vmax` by construction (`le_maxTabZ`).
* **Seeds by Newton's method** (`solveSeedsZ`). The seeds are a fixed point of a monotone,
  piecewise affine map of three integers. Newton steps on finite differences find it, raised
  by a small pad, then steps of the map itself until the seeds are a solution. Across a band
  family each member starts from the previous member's seeds (`seedsZ`, `preSeedsZ`). A
  certificate runs the solver at elaboration time (`eval%`, `EvalLit.lean`) and the kernel
  only checks its result, so the solver needs no soundness theorem.
* **One check per phase index** (`oneSwitchF_sound`, `switchF_sound`): the one-switch
  tables (`AutoSolE`) or the switching table, for the whole family, with their bounds.
-/

@[expose] public section

namespace Cryptarchia.Prob

/-! ## Rounding and folds -/

theorem cdivZ_mul_ge {n m : ℤ} (hm : 0 < m) : n ≤ cdivZ n m * m := by
  unfold cdivZ
  have := Int.ediv_mul_le (-n) hm.ne'
  linarith [neg_mul ((-n) / m) m]

theorem le_of_cdivZ_le {n m v : ℤ} (hm : 0 < m) (h : cdivZ n m ≤ v) : n ≤ v * m :=
  (cdivZ_mul_ge hm).trans (mul_le_mul_of_nonneg_right h hm.le)

/-- A running maximum is above its start and above every value it folds in. -/
theorem foldl_ite_max {α : Type*} (s : α → ℤ) : ∀ (l : List α) (m : ℤ),
    m ≤ l.foldl (fun m B => if m ≤ s B then s B else m) m ∧
      ∀ B ∈ l, s B ≤ l.foldl (fun m B => if m ≤ s B then s B else m) m
  | [], m => ⟨le_rfl, by simp⟩
  | B :: l, m => by
    have h1 : m ≤ (if m ≤ s B then s B else m) := by split_ifs <;> omega
    have h2 : s B ≤ (if m ≤ s B then s B else m) := by split_ifs <;> omega
    obtain ⟨ih1, ih2⟩ := foldl_ite_max s l (if m ≤ s B then s B else m)
    refine ⟨h1.trans ih1, fun B' hB' => ?_⟩
    rcases List.mem_cons.1 hB' with rfl | h
    · exact h2.trans ih1
    · exact ih2 B' h

theorem foldl_max_ge {α : Type*} (s : α → ℤ) : ∀ (l : List α) (m : ℤ),
    m ≤ l.foldl (fun m t => max m (s t)) m ∧ ∀ t ∈ l, s t ≤ l.foldl (fun m t => max m (s t)) m
  | [], m => ⟨le_rfl, by simp⟩
  | t :: l, m => by
    obtain ⟨ih1, ih2⟩ := foldl_max_ge s l (max m (s t))
    refine ⟨(le_max_left _ _).trans ih1, fun t' ht' => ?_⟩
    rcases List.mem_cons.1 ht' with rfl | h
    · exact (le_max_right _ _).trans ih1
    · exact ih2 t' h

/-! ## Fills are solutions by construction -/

section Fill

variable {Bs : List BandZ} {D : ℤ} {Δ : ℕ} {X : PhZ} {S : ℤ} {lo : ℕ → Fin 3 → Bool → ℤ} {top : Fin 3 → ℤ}

theorem fillRowZ_length (q : ℕ) (nxt : List ℤ) : (fillRowZ Bs D Δ X S lo top q nxt).length = 6 := rfl

theorem fillRowsZ_getD : ∀ (j n q i : ℕ), j < n → i < 6 →
    (fillRowsZ Bs D Δ X S lo top q n).getD (6 * j + i) 0 =
      (fillRowZ Bs D Δ X S lo top (q + j) (fillRowsZ Bs D Δ X S lo top (q + j + 1) (n - j - 1))).getD i 0
  | 0, n + 1, q, i, _, hi => by
    simp only [fillRowsZ, Nat.mul_zero, Nat.zero_add, Nat.add_zero]
    exact List.getD_append _ _ _ _ (by rw [fillRowZ_length]; exact hi)
  | j + 1, n + 1, q, i, hj, hi => by
    simp only [fillRowsZ]
    rw [List.getD_append_right _ _ _ _ (by rw [fillRowZ_length]; omega), fillRowZ_length,
      show 6 * (j + 1) + i - 6 = 6 * j + i by omega,
      fillRowsZ_getD j n (q + 1) i (by omega) hi]
    simp only [show q + 1 + j = q + (j + 1) by omega, show n - j - 1 = n + 1 - (j + 1) - 1 by omega]

theorem fillAllZ_eq {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) :
    fillAllZ Bs D Δ X S lo top q a u =
      (fillRowZ Bs D Δ X S lo top q (fillRowsZ Bs D Δ X S lo top (q + 1) (Δ - q - 1))).getD
        (2 * a.val + if u then 1 else 0) 0 := by
  have ha := a.isLt
  unfold fillAllZ tabZ
  rw [show 6 * q + 2 * a.val + (if u then 1 else 0) = 6 * q + (2 * a.val + if u then 1 else 0) by omega,
    fillRowsZ_getD q Δ 0 _ hq (by split <;> omega)]
  simp only [Nat.zero_add]

theorem fillRowZ_getD (q : ℕ) (nxt : List ℤ) (a : Fin 3) (u : Bool) :
    (fillRowZ Bs D Δ X S lo top q nxt).getD (2 * a.val + if u then 1 else 0) 0 =
      if q = 0 ∧ u = true then top a else
        Bs.foldl (fun m B => if m ≤ cdivZ (stepZ B D Δ X S (fun q' a u =>
          if q' = 0 then top a else nxt.getD (2 * a.val + if u then 1 else 0) 0) q a u) (X.M D) then
            cdivZ (stepZ B D Δ X S (fun q' a u =>
              if q' = 0 then top a else nxt.getD (2 * a.val + if u then 1 else 0) 0) q a u) (X.M D)
          else m) (lo q a u) := by
  fin_cases a <;> cases u <;> rfl

theorem fillAllZ_seed (hΔ : 0 < Δ) (a : Fin 3) : fillAllZ Bs D Δ X S lo top 0 a true = top a := by
  rw [fillAllZ_eq hΔ, fillRowZ_getD, if_pos ⟨rfl, rfl⟩]

/-- `stepZ` reads a table only at the seeds and at the next row. -/
theorem stepZ_congr (B : BandZ) {w w' : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} (hq : q < Δ)
    (h0 : ∀ a, w 0 a true = w' 0 a true) (h1 : q + 1 < Δ → ∀ a u, w (q + 1) a u = w' (q + 1) a u)
    (a : Fin 3) (u : Bool) : stepZ B D Δ X S w q a u = stepZ B D Δ X S w' q a u := by
  unfold stepZ
  by_cases hΔ : q + 1 = Δ
  · simp only [hΔ, h0, ite_true]
  · simp only [hΔ, h0, h1 (by omega), ite_false]

/-- **Every entry of a fill but the seeds is a solution of the recursion**, for every band
it was filled for, and above its floor. -/
theorem fillAllZ_entry (hM : 0 < X.M D) {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool)
    (hnt : ¬(q = 0 ∧ u = true)) :
    lo q a u ≤ fillAllZ Bs D Δ X S lo top q a u ∧
      ∀ B ∈ Bs, stepZ B D Δ X S (fillAllZ Bs D Δ X S lo top) q a u ≤
        fillAllZ Bs D Δ X S lo top q a u * X.M D := by
  rw [fillAllZ_eq hq, fillRowZ_getD, if_neg hnt]
  set nxt := fillRowsZ Bs D Δ X S lo top (q + 1) (Δ - q - 1)
  set w : ℕ → Fin 3 → Bool → ℤ := fun q' a u => if q' = 0 then top a else nxt.getD (2 * a.val + if u then 1 else 0) 0
  have hw : ∀ B, stepZ B D Δ X S w q a u = stepZ B D Δ X S (fillAllZ Bs D Δ X S lo top) q a u := fun B =>
    stepZ_congr B hq (fun a => by simp only [w, ite_true]; exact (fillAllZ_seed (by omega) a).symm)
      (fun hq1 a u => by
        simp only [w, Nat.add_one_ne_zero, ite_false, nxt]
        rw [fillAllZ_eq hq1, show 2 * a.val + (if u then 1 else 0) = 6 * 0 + (2 * a.val + if u then 1 else 0) by omega,
          fillRowsZ_getD 0 _ _ _ (by omega) (by have := a.isLt; split <;> omega)]
        simp only [Nat.add_zero, Nat.mul_zero, Nat.zero_add, show Δ - q - 1 - 0 - 1 = Δ - (q + 1) - 1 by omega]) a u
  obtain ⟨h1, h2⟩ := foldl_ite_max (fun B => cdivZ (stepZ B D Δ X S w q a u) (X.M D)) Bs (lo q a u)
  refine ⟨h1, fun B hB => ?_⟩
  rw [← hw B]
  exact le_of_cdivZ_le hM (h2 B hB)

/-- The seeds of a fill solve the recursion for `B` and lie above the floor. -/
def seedOKZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo v : ℕ → Fin 3 → Bool → ℤ) : Bool :=
  let p : Fin 3 → Bool := fun a =>
    decide (lo 0 a true ≤ v 0 a true) && decide (stepZ B D Δ X S v 0 a true ≤ v 0 a true * X.M D)
  p 0 && p 1 && p 2

theorem seedOKZ_sound {B : BandZ} {v : ℕ → Fin 3 → Bool → ℤ} (h : seedOKZ B D Δ X S lo v = true) (a : Fin 3) :
    lo 0 a true ≤ v 0 a true ∧ stepZ B D Δ X S v 0 a true ≤ v 0 a true * X.M D := by
  simp only [seedOKZ, Bool.and_eq_true, decide_eq_true_eq] at h
  fin_cases a
  exacts [h.1.1, h.1.2, h.2]

/-- Every entry of a fill whose seeds check is above its floor and solves the recursion. -/
theorem fillAllZ_sol (hM : 0 < X.M D) {B : BandZ} (hB : B ∈ Bs)
    (hs : seedOKZ B D Δ X S lo (fillAllZ Bs D Δ X S lo top) = true) {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) :
    lo q a u ≤ fillAllZ Bs D Δ X S lo top q a u ∧
      stepZ B D Δ X S (fillAllZ Bs D Δ X S lo top) q a u ≤ fillAllZ Bs D Δ X S lo top q a u * X.M D := by
  by_cases hnt : q = 0 ∧ u = true
  · obtain ⟨rfl, rfl⟩ := hnt
    exact seedOKZ_sound hs a
  · obtain ⟨h1, h2⟩ := fillAllZ_entry (top := top) hM hq a u hnt
    exact ⟨h1, h2 B hB⟩

end Fill

/-- The terminal table rounded up is a floor above `g`. -/
theorem gFloorZ_ge {X : PhZ} {S : ℤ} (hgd : 0 < X.gd) (q : ℕ) (a : Fin 3) (u : Bool) :
    X.gn a true u * S ≤ gFloorZ X S q a u * X.gd := cdivZ_mul_ge hgd

section Sol

variable {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D) {X : PhZ}
  {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) {Δ : ℕ} {Bs : List BandZ}
  (hB : B ∈ Bs) {top : Fin 3 → ℤ}
include hR hA hD hX hS hB

/-- **A fill floored at `g` whose seeds check solves the recursion.** -/
theorem fill_autoSol (hs : seedOKZ B D Δ X S (gFloorZ X S) (fillAllZ Bs D Δ X S (gFloorZ X S) top) = true) :
    AutoSol Bb Δ x θ (castG g) (castZ S (fillAllZ Bs D Δ X S (gFloorZ X S) top)) where
  term q hq a u := by
    have hgd : (0 : ℝ) < X.gd := by exact_mod_cast hX.gd
    have hS' : (0 : ℝ) < S := by exact_mod_cast hS
    refine le_trans ?_ (castZ_le hS (fillAllZ_sol (X.M_pos hX hD) hB hs hq a u).1)
    rw [castG, castZ, hX.g]
    push_cast
    rw [div_le_div_iff₀ hgd hS']
    exact_mod_cast gFloorZ_ge hX.gd q a u
  step q hq a u := stepZ_le hR hA hD hX hS (fillAllZ_sol (X.M_pos hX hD) hB hs hq a u).2

/-- **A fill floored at `vmax` whose seeds check is a pre-switch table.** -/
theorem fill_preSol {vmax : ℕ → Fin 3 → Bool → ℤ}
    (hs : seedOKZ B D Δ X S vmax (fillAllZ Bs D Δ X S vmax top) = true) :
    PreSol Bb Δ x θ (castG g) (castZ S vmax) (castZ S (fillAllZ Bs D Δ X S vmax top)) where
  dom _ hq a u := castZ_le hS (fillAllZ_sol (X.M_pos hX hD) hB hs hq a u).1
  step _ hq a u := stepZ_le hR hA hD hX hS (fillAllZ_sol (X.M_pos hX hD) hB hs hq a u).2

end Sol

/-! ## Tables listed once -/

/-- The rows `q, …, q + n - 1` of a table, listed by `(q, a, u)`. -/
def matRowsZ (v : ℕ → Fin 3 → Bool → ℤ) : ℕ → ℕ → List ℤ
  | _, 0 => []
  | q, n + 1 => [v q 0 false, v q 0 true, v q 1 false, v q 1 true, v q 2 false, v q 2 true] ++ matRowsZ v (q + 1) n

theorem matRowsZ_getD (v : ℕ → Fin 3 → Bool → ℤ) : ∀ (j n q : ℕ) (a : Fin 3) (u : Bool), j < n →
    (matRowsZ v q n).getD (6 * j + (2 * a.val + if u then 1 else 0)) 0 = v (q + j) a u
  | 0, n + 1, q, a, u, _ => by
    rw [matRowsZ, Nat.mul_zero, Nat.zero_add, List.getD_append _ _ _ _ (by simp; have := a.isLt; split <;> omega)]
    fin_cases a <;> cases u <;> rfl
  | j + 1, n + 1, q, a, u, hj => by
    have ha := a.isLt
    rw [matRowsZ, List.getD_append_right _ _ _ _ (by simp; omega)]
    simp only [List.length_cons, List.length_nil]
    rw [show 6 * (j + 1) + (2 * a.val + if u then 1 else 0) - 6 = 6 * j + (2 * a.val + if u then 1 else 0) by
      split <;> omega, matRowsZ_getD v j n (q + 1) a u (by omega), show q + 1 + j = q + (j + 1) by omega]

/-- A table evaluated once and listed, so that later lookups do not recompute it. -/
def memoZ (Δ : ℕ) (v : ℕ → Fin 3 → Bool → ℤ) : ℕ → Fin 3 → Bool → ℤ := tabZ (matRowsZ v 0 Δ)

theorem memoZ_eq {Δ : ℕ} {v : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) :
    memoZ Δ v q a u = v q a u := by
  unfold memoZ tabZ
  rw [show 6 * q + 2 * a.val + (if u then 1 else 0) = 6 * q + (2 * a.val + if u then 1 else 0) by omega,
    matRowsZ_getD v q Δ 0 a u hq, Nat.zero_add]

/-- The entrywise maximum of tables (at least `0`), listed once. -/
def maxTabZ (Δ : ℕ) (ts : List (ℕ → Fin 3 → Bool → ℤ)) : ℕ → Fin 3 → Bool → ℤ :=
  memoZ Δ fun q a u => ts.foldl (fun m t => max m (t q a u)) 0

theorem le_maxTabZ {Δ : ℕ} {ts : List (ℕ → Fin 3 → Bool → ℤ)} {t : ℕ → Fin 3 → Bool → ℤ} (ht : t ∈ ts)
    {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) : t q a u ≤ maxTabZ Δ ts q a u := by
  unfold maxTabZ
  rw [memoZ_eq hq]
  exact (foldl_max_ge (fun t => t q a u) ts 0).2 t ht

/-! ## Seeds by Newton's method -/

/-- Three seeds as a function. -/
def seedL (l : List ℤ) : Fin 3 → ℤ := fun a => l.getD a.val 0

/-- The step at `(0, a, true)` for the table with seeds `t`: its maximum over the bands,
rounded up, at least the floor. The seeds solve the recursion iff this is at most `t`. -/
def seedStepZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (t : List ℤ) : List ℤ :=
  -- the rows listed once, so that compiled code does not recompute them at each lookup
  let w := tabZ (fillRowsZ Bs D Δ X S lo (seedL t) 0 Δ)
  [0, 1, 2].map fun a : Fin 3 =>
    Bs.foldl (fun m B => max m (cdivZ (stepZ B D Δ X S w 0 a true) (X.M D))) (lo 0 a true)

def det3Z (a b c d e f g h i : ℤ) : ℤ := a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)

/-- One Newton step for the fixed point of `seedStepZ` from `t`, on differences of size `h`,
rounded up; `t` itself if the linear system is singular. -/
def newtonZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (h : ℤ) (t : List ℤ) : List ℤ :=
  let F := seedStepZ Bs D Δ X S lo
  let f := F t
  let t0 := t.getD 0 0
  let t1 := t.getD 1 0
  let t2 := t.getD 2 0
  let g0 := F [t0 + h, t1, t2]
  let g1 := F [t0, t1 + h, t2]
  let g2 := F [t0, t1, t2 + h]
  -- the slopes times `h`, column `j` from `gj`
  let d := fun (g : List ℤ) (i : ℕ) => g.getD i 0 - f.getD i 0
  -- `(h I - D) x = h f - D t`
  let r := fun i => h * f.getD i 0 - (d g0 i * t0 + d g1 i * t1 + d g2 i * t2)
  let m := det3Z (h - d g0 0) (-d g1 0) (-d g2 0) (-d g0 1) (h - d g1 1) (-d g2 1) (-d g0 2) (-d g1 2) (h - d g2 2)
  if m ≤ 0 then t else
    [cdivZ (det3Z (r 0) (-d g1 0) (-d g2 0) (r 1) (h - d g1 1) (-d g2 1) (r 2) (-d g1 2) (h - d g2 2)) m,
     cdivZ (det3Z (h - d g0 0) (r 0) (-d g2 0) (-d g0 1) (r 1) (-d g2 1) (-d g0 2) (r 2) (h - d g2 2)) m,
     cdivZ (det3Z (h - d g0 0) (-d g1 0) (r 0) (-d g0 1) (h - d g1 1) (r 1) (-d g0 2) (-d g1 2) (r 2)) m]

def leL (l m : List ℤ) : Bool := (List.zipWith (fun x y => decide (x ≤ y)) l m).all id

/-- Seeds solving the recursion at `(0, a, true)`: `n` Newton steps from `t`, each raised by
`pad` and floored at `lo`, then up to `k` steps of the recursion itself (which only raise the
seeds) while they are not yet a solution. -/
def solveSeedsZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (h pad : ℤ) (n k : ℕ) (t : List ℤ) : List ℤ :=
  let N := fun t => List.zipWith max [lo 0 0 true, lo 0 1 true, lo 0 2 true]
    ((newtonZ Bs D Δ X S lo h t).map (· + pad))
  let rec go : ℕ → List ℤ → List ℤ
    | 0, x => x
    | k + 1, x => let y := seedStepZ Bs D Δ X S lo x; if leL y x then x else go k (List.zipWith max x y)
  go k (N^[n] t)

/-- The seeds of each member in turn, by `n` Newton steps for the first member (from `t`) and
`n'` for each later one, from the previous member's seeds. -/
def seedsZ (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ) (h pad : ℤ) (n n' k : ℕ) :
    List BandZ → List ℤ → List (List ℤ)
  | [], _ => []
  | B :: Bs, t =>
    let x := solveSeedsZ [B] D Δ X S lo h pad n k t
    x :: seedsZ D Δ X S lo h pad n' n' k Bs x

/-- `vmax` listed by `(q, a, u)`, from every member's post-switch seeds. -/
def vmaxListZ (famL : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (seeds : List (List ℤ)) : List ℤ :=
  (List.zipWith (fun B t => fillRowsZ [B] D Δ X S (gFloorZ X S) (seedL t) 0 Δ) famL seeds).foldl
    (List.zipWith max) (List.replicate (6 * Δ) 0)

/-- Every member's pre-switch seeds, from `vmax`'s (`n` Newton steps, then up to `k` steps of
the recursion). -/
def preSeedsZ (famL : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (h pad : ℤ) (n k : ℕ)
    (seeds : List (List ℤ)) : List (List ℤ) :=
  let vm := vmaxListZ famL D Δ X S seeds
  famL.map fun B => solveSeedsZ [B] D Δ X S (tabZ vm) h pad n k [vm.getD 1 0, vm.getD 3 0, vm.getD 5 0]

/-! ## Rounding to significant digits -/

/-- The number of decimal digits of `n` (one for `0`), with fuel `f`. -/
def ndigits : ℕ → ℕ → ℕ
  | 0, _ => 0
  | f + 1, n => if n < 10 then 1 else ndigits f (n / 10) + 1

/-- `⌊log₁₀ x⌋` for `0 < x`, computed as the generator computes it (`certnum.flog10`). -/
def flog10Q (x : ℚ) : ℤ :=
  let e : ℤ := (ndigits 1000 x.num.natAbs : ℤ) - (ndigits 1000 x.den : ℤ)
  let e := if x < (10 : ℚ) ^ e then e - 1 else e
  if (10 : ℚ) ^ (e + 1) ≤ x then e + 1 else e

/-- `x` rounded up to `d` significant digits (`certnum.rup`). -/
def rupQ (d : ℕ) (x : ℚ) : ℚ :=
  if x = 0 then 0 else ⌈x / (10 : ℚ) ^ (flog10Q x - d + 1)⌉ * (10 : ℚ) ^ (flog10Q x - d + 1)

/-- `x` rounded down to `d` significant digits (`certnum.rdn`). -/
def rdnQ (d : ℕ) (x : ℚ) : ℚ :=
  if x = 0 then 0 else ⌊x / (10 : ℚ) ^ (flog10Q x - d + 1)⌋ * (10 : ℚ) ^ (flog10Q x - d + 1)

theorem le_rupQ (d : ℕ) (x : ℚ) : x ≤ rupQ d x := by
  unfold rupQ
  split_ifs with h
  · exact h.le
  · have hq : (0 : ℚ) < 10 ^ (flog10Q x - d + 1) := zpow_pos (by norm_num) _
    calc x = x / 10 ^ (flog10Q x - d + 1) * 10 ^ (flog10Q x - d + 1) := by field_simp
      _ ≤ _ := mul_le_mul_of_nonneg_right (Int.le_ceil _) hq.le

theorem rdnQ_le (d : ℕ) (x : ℚ) : rdnQ d x ≤ x := by
  unfold rdnQ
  split_ifs with h
  · exact h.ge
  · have hq : (0 : ℚ) < 10 ^ (flog10Q x - d + 1) := zpow_pos (by norm_num) _
    calc _ ≤ x / 10 ^ (flog10Q x - d + 1) * 10 ^ (flog10Q x - d + 1) :=
          mul_le_mul_of_nonneg_right (Int.floor_le _) hq.le
      _ = x := by field_simp

/-! ## Data computed for a certificate -/

/-- A phase expectation's numbers over the integers, from their rational values: `x`, `θ` as
fractions, `g` over the least common denominator of its entries. -/
def PhZ.ofQ (p : ℚ × ℚ × (Fin 3 → Bool → Bool → ℚ)) : PhZ :=
  let gs := [p.2.2 0 false false, p.2.2 0 false true, p.2.2 0 true false, p.2.2 0 true true,
    p.2.2 1 false false, p.2.2 1 false true, p.2.2 1 true false, p.2.2 1 true true,
    p.2.2 2 false false, p.2.2 2 false true, p.2.2 2 true false, p.2.2 2 true true]
  let gd : ℕ := gs.foldl (fun m q => Nat.lcm m q.den) 1
  ⟨p.1.num, p.1.den, p.2.1.num, p.2.1.den, fun a b u => (p.2.2 a b u * gd).num, gd⟩

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up to `d`
significant digits. -/
def eInListQ (famL : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (d : ℕ) (seeds : List (List ℤ)) : List ℚ :=
  List.zipWith (fun B t => rupQ d ((autoBoundZ B D X S (tabZ (fillRowsZ [B] D Δ X S (gFloorZ X S) (seedL t) 0 Δ)) : ℚ) /
    (X.M D * S : ℤ))) famL seeds

/-! ## One check per phase index -/

section Index

variable {K : ℕ} {famZ : Fin K → BandZ} {D : ℤ} {famQ : Fin K → BandQ} {fam : Fin K → Band}
  {X : PhZ} {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} {S : ℤ} {Δ : ℕ}

/-- The post-switch table of a member, from its seeds. -/
def postF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop : Fin K → Fin 3 → ℤ) (k : Fin K) :
    ℕ → Fin 3 → Bool → ℤ :=
  fillZ (famZ k) D Δ X S (gFloorZ X S) (postTop k)

/-- `vmax`: the entrywise maximum of the post-switch tables. -/
def vmaxF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop : Fin K → Fin 3 → ℤ) :
    ℕ → Fin 3 → Bool → ℤ :=
  maxTabZ Δ ((List.finRange K).map (postF famZ D Δ X S postTop))

/-- The pre-switch table of a member, from its seeds: floored at `vmax`. -/
def preF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop preTop : Fin K → Fin 3 → ℤ) (k : Fin K) :
    ℕ → Fin 3 → Bool → ℤ :=
  fillZ (famZ k) D Δ X S (vmaxF famZ D Δ X S postTop) (preTop k)

/-- Every check of member `k` of a one-switch index. -/
def chkOneF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop preTop : Fin K → Fin 3 → ℤ)
    (eIn : Fin K → ℚ) (eE : ℚ) (k : Fin K) : Bool :=
  let post := postF famZ D Δ X S postTop k
  let pre := preF famZ D Δ X S postTop preTop k
  seedOKZ (famZ k) D Δ X S (gFloorZ X S) post && seedOKZ (famZ k) D Δ X S (vmaxF famZ D Δ X S postTop) pre &&
    decide ((autoBoundZ (famZ k) D X S post : ℚ) ≤ eIn k * (X.M D * S : ℤ)) &&
    decide ((autoBoundZ (famZ k) D X S pre : ℚ) ≤ eE * (X.M D * S : ℤ))

/-- **The one-switch tables of an index, for the whole family, from seeds alone.** -/
theorem oneSwitchF_sound (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D)
    (hX : X.Rep x θ g) (hS : 0 < S) {postTop preTop : Fin K → Fin 3 → ℤ} {eIn : Fin K → ℚ} {eE : ℚ}
    (h : (List.finRange K).all (chkOneF famZ D Δ X S postTop preTop eIn eE) = true) :
    AutoSolE fam Δ x θ (castG g) (fun k => castZ S (preF famZ D Δ X S postTop preTop k))
        (fun k => castZ S (postF famZ D Δ X S postTop k)) (castZ S (vmaxF famZ D Δ X S postTop)) ∧
      (∀ k, autoBound (fam k) x θ (castG g) (castZ S (postF famZ D Δ X S postTop k)) ≤ eIn k) ∧
      (∀ k, autoBound (fam k) x θ (castG g) (castZ S (preF famZ D Δ X S postTop preTop k)) ≤ eE) := by
  have hk : ∀ k, _ := fun k => List.all_eq_true.1 h k (List.mem_finRange k)
  simp only [chkOneF, Bool.and_eq_true, decide_eq_true_eq] at hk
  have hB := fun k => List.mem_singleton_self (famZ k)
  refine ⟨⟨fun k => fill_autoSol (hR k) (hA k) hD hX hS (hB k) (hk k).1.1.1,
    fun k q hq a u => castZ_le hS (le_maxTabZ (List.mem_map.2 ⟨k, List.mem_finRange k, rfl⟩) hq a u),
    fun k => fill_preSol (hR k) (hA k) hD hX hS (hB k) (hk k).1.1.2⟩,
    fun k => autoBoundZ_le (hR k) (hA k) hD hX hS (hk k).1.2, fun k => autoBoundZ_le (hR k) (hA k) hD hX hS (hk k).2⟩

/-- Every check of member `k` against a switching table. -/
def chkSwF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (top : Fin 3 → ℤ) (eS : Fin K → ℚ)
    (k : Fin K) : Bool :=
  let vs := fillAllZ ((List.finRange K).map famZ) D Δ X S (gFloorZ X S) top
  seedOKZ (famZ k) D Δ X S (gFloorZ X S) vs && decide ((autoBoundZ (famZ k) D X S vs : ℚ) ≤ eS k * (X.M D * S : ℤ))

/-- **A switching table of an index, for the whole family, from its seeds alone.** -/
theorem switchF_sound (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D)
    (hX : X.Rep x θ g) (hS : 0 < S) {top : Fin 3 → ℤ} {eS : Fin K → ℚ}
    (h : (List.finRange K).all (chkSwF famZ D Δ X S top eS) = true) :
    (∀ k, AutoSol (fam k) Δ x θ (castG g) (castZ S (fillAllZ ((List.finRange K).map famZ) D Δ X S (gFloorZ X S) top))) ∧
      (∀ k, autoBound (fam k) x θ (castG g)
        (castZ S (fillAllZ ((List.finRange K).map famZ) D Δ X S (gFloorZ X S) top)) ≤ eS k) := by
  have hk : ∀ k, _ := fun k => List.all_eq_true.1 h k (List.mem_finRange k)
  simp only [chkSwF, Bool.and_eq_true, decide_eq_true_eq] at hk
  exact ⟨fun k => fill_autoSol (hR k) (hA k) hD hX hS (List.mem_map.2 ⟨k, List.mem_finRange k, rfl⟩) (hk k).1,
    fun k => autoBoundZ_le (hR k) (hA k) hD hX hS (hk k).2⟩

end Index

end Cryptarchia.Prob
