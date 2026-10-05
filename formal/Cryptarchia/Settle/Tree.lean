import Mathlib

/-!
# Longest-chain settlement: proof-of-stake trees

The combinatorial core of the settlement analysis of Gaži, Ren and Russell,
*Practical Settlement Bounds for Longest-Chain Consensus* (CRYPTO 2023,
ePrint 2022/1571), §2 and §4, formalized.

* A **characteristic string** gives, for each slot `i ≥ 1`, the number of honest
  leaders `(w i).1` and whether the adversary has a winning ticket `(w i).2`.
* A **PoS tree** for the first `n` slots (Def. 10): a rooted tree whose vertices
  are blocks, labelled by slot. Labels strictly increase along chains (S3); slot
  `i` has exactly `(w i).1` honest vertices, and adversarial vertices only if
  `(w i).2` (S4, any number of them: an adversarial success can sign any number
  of blocks); honest vertices more than `Δ` slots apart have increasing depth (A2).

Two departures from the paper, both strengthening the upper bounds proven here:

* **Dominance** is measured against the deepest honest vertex at least `Δ` slots
  old (`hd F (n - Δ)`), which is what honest parties are guaranteed to have seen
  (the paper's `D_t`, §2.2). The paper measures against `len(F⌈Δ)` for *public*
  trees; our advantage is at least theirs, so our bounds imply theirs, and we
  need no notion of public tree.
* Only **upper bounds** on reach and margin are formalized, as statements about
  every tree (`Recurrence.lean`), rather than as maxima over trees.
-/

namespace Cryptarchia.Settle

/-- A characteristic string: slot `i` has `(w i).1` honest leaders and an
adversarial success iff `(w i).2`. Slot `0` is genesis. -/
abbrev CStr := ℕ → ℕ × Bool

/-- A labelled rooted tree; the root is vertex `0`. -/
structure PTree where
  V : Finset ℕ
  par : ℕ → ℕ
  lab : ℕ → ℕ
  hon : ℕ → Bool
  dep : ℕ → ℕ

variable (Δ : ℕ) (w : CStr)

/-- **A PoS tree for the first `n` slots of `w`** (Def. 10, with (A1), (A2),
(S3), (S4)), with the depth function made explicit. -/
structure PTree.Valid (F : PTree) (n : ℕ) : Prop where
  root_mem : 0 ∈ F.V
  root_par : F.par 0 = 0
  root_lab : F.lab 0 = 0
  root_hon : F.hon 0 = true
  root_dep : F.dep 0 = 0
  par_mem : ∀ v ∈ F.V, F.par v ∈ F.V
  lab_lt : ∀ v ∈ F.V, v ≠ 0 → F.lab (F.par v) < F.lab v
  dep_succ : ∀ v ∈ F.V, v ≠ 0 → F.dep v = F.dep (F.par v) + 1
  lab_le : ∀ v ∈ F.V, F.lab v ≤ n
  lab_pos : ∀ v ∈ F.V, v ≠ 0 → 0 < F.lab v
  /-- (A2): honest vertices more than `Δ` slots apart have increasing depth. -/
  A2 : ∀ u ∈ F.V, ∀ v ∈ F.V, F.hon u = true → F.hon v = true →
    F.lab u + Δ < F.lab v → F.dep u < F.dep v
  /-- (S4), honest part: exactly `(w i).1` honest vertices with label `i`. -/
  honCount : ∀ i, 1 ≤ i → i ≤ n →
    (F.V.filter (fun v => F.hon v = true ∧ F.lab v = i)).card = (w i).1
  /-- (S4), adversarial part: adversarial vertices only in adversarial slots. -/
  advSlot : ∀ v ∈ F.V, F.hon v = false → (w (F.lab v)).2 = true

namespace PTree

variable {Δ w} (F : PTree)

/-- `u` is an ancestor of `v` (or `v` itself). -/
def Anc (u v : ℕ) : Prop := F.dep u ≤ F.dep v ∧ F.par^[F.dep v - F.dep u] v = u

/-- `T ∼ℓ T'`: the chains ending in `u` and `v` share a vertex with label `≥ ℓ`
(Def. 4). -/
def Sim (ℓ u v : ℕ) : Prop := ∃ x ∈ F.V, F.Anc x u ∧ F.Anc x v ∧ ℓ ≤ F.lab x

/-- The depth of the deepest honest vertex with label at most `m`. -/
def hd (m : ℕ) : ℕ := (F.V.filter (fun v => F.hon v = true ∧ F.lab v ≤ m)).sup F.dep

end PTree

/-- Adversarial slots in `(a, b]`. -/
def advCnt (a b : ℕ) : ℕ := ((Finset.Ioc a b).filter (fun j => (w j).2 = true)).card

/-- **Reach** of the chain ending in `v`, in a tree for the first `n` slots:
its advantage `dep v - hd(n - Δ)` plus its reserve, the adversarial slots after
its last label (Def. 11). -/
def reach (F : PTree) (n v : ℕ) : ℤ :=
  (F.dep v : ℤ) - F.hd (n - Δ) + advCnt w (F.lab v) n

/-- **Honest depth** `h_Δ` of the slots `(a, b]` (Def. 6): the longest sequence of
honest slots in `(a, b]` more than `Δ` apart, counted greedily from the end. -/
def hD (a : ℕ) : ℕ → ℕ
  | b => if hb : b ≤ a then 0 else
      if (w b).1 = 0 then hD a (b - 1) else hD a (b - Δ - 1) + 1
termination_by b => b
decreasing_by all_goals omega

/-- No honest successes in `(m - Δ, m]`. -/
def Quiet (m : ℕ) : Prop := ∀ j, m - Δ < j → j ≤ m → 1 ≤ j → (w j).1 = 0

end Cryptarchia.Settle
