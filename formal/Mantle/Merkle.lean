import Mantle.Crypto

/-!
# Merkle trees and Merkle paths

The commitment MMR, the nullifier IMT and the eligible tree are Merkle trees of depth `32`
whose node hash is `zkhash(left, right)` and whose positions past the last leaf hold `0`
(Mantle, *Commitment Merkle Mountain Range*). A tree is given by its leaf function
`g : ℕ → Fr`.

* `subtree g h i` is the root of the perfect subtree of height `h` holding the leaves
  `[i 2^h, (i+1) 2^h)`; `subtree g 32 0` is the root of the tree.
* `emptyRoot h` is `empty_root(height)`: the root of a subtree whose leaves are all `0`
  (`subtree_eq_emptyRoot`).
* A Merkle path lists its selectors and nodes **from the leaf level up**, the selector of a
  level being `1` when the path node is on the left, which is the bit of the leaf index at
  that level (RFC-480 §1). `rootFromPath` computes the root a path proves, `pathIndex` the
  index its selectors spell.

Results: `rootFromPath_pathOf` (every leaf has a path to the root, whose selectors are the
bits of its index) and **`rootFromPath_eq_subtree`** (binding: under a collision-free hash, a
path to the root proves exactly the leaf at the index its selectors spell).
-/

namespace Mantle

variable (H : Hash)

/-- The root of the perfect subtree of height `h` over the leaves `[i 2^h, (i+1) 2^h)`. -/
def subtree (g : ℕ → Fr) : ℕ → ℕ → Fr
  | 0, i => g i
  | h + 1, i => H.node (subtree g h (2 * i)) (subtree g h (2 * i + 1))

/-- `empty_root(height)`: the root of a perfect subtree of the given height whose leaves all
hold `0`. -/
def emptyRoot : ℕ → Fr
  | 0 => 0
  | h + 1 => H.node (emptyRoot h) (emptyRoot h)

/-- One level up: the parents of the nodes of `g`. -/
def up (g : ℕ → Fr) (k : ℕ) : Fr := H.node (g (2 * k)) (g (2 * k + 1))

/-- The root a Merkle path proves for a leaf: nodes and selectors from the leaf level up, a
selector being `true` when the path node is on the left. -/
def rootFromPath (leaf : Fr) : List (Bool × Fr) → Fr
  | [] => leaf
  | (s, n) :: p => rootFromPath (if s then H.node n leaf else H.node leaf n) p

/-- The leaf index the selectors of a path spell, least significant bit first. -/
def pathIndex : List (Bool × Fr) → ℕ
  | [] => 0
  | (s, _) :: p => (if s then 1 else 0) + 2 * pathIndex p

/-- The path of the leaf `i` in a tree of height `d`. -/
def pathOf (g : ℕ → Fr) : ℕ → ℕ → List (Bool × Fr)
  | 0, _ => []
  | d + 1, i => (i % 2 = 1, if i % 2 = 1 then g (i - 1) else g (i + 1)) :: pathOf (up H g) d (i / 2)

variable {H}

theorem subtree_succ' (g : ℕ → Fr) (h i : ℕ) : subtree H g (h + 1) i = subtree H (up H g) h i := by
  induction h generalizing i with
  | zero => rfl
  | succ h ih => rw [subtree, ih, ih, subtree]

/-- A subtree whose leaves are all `0` has root `emptyRoot`. -/
theorem subtree_eq_emptyRoot {g : ℕ → Fr} {h i : ℕ}
    (hg : ∀ j, i * 2 ^ h ≤ j → j < (i + 1) * 2 ^ h → g j = 0) :
    subtree H g h i = emptyRoot H h := by
  induction h generalizing i with
  | zero => simpa [subtree, emptyRoot] using hg i (by simp) (by simp)
  | succ h ih =>
    simp only [subtree, emptyRoot]
    rw [ih, ih]
    · intro j h1 h2
      apply hg j <;> rw [pow_succ] <;> nlinarith
    · intro j h1 h2
      apply hg j <;> rw [pow_succ] <;> nlinarith

/-- Two sibling subtrees hash to their parent. -/
theorem node_subtree_even (g : ℕ → Fr) (h q : ℕ) (hq : q % 2 = 0) :
    H.node (subtree H g h q) (subtree H g h (q + 1)) = subtree H g (h + 1) (q / 2) := by
  rw [subtree, show 2 * (q / 2) = q by omega]

theorem node_subtree_odd (g : ℕ → Fr) (h q : ℕ) (hq : q % 2 = 1) :
    H.node (subtree H g h (q - 1)) (subtree H g h q) = subtree H g (h + 1) (q / 2) := by
  rw [subtree, show 2 * (q / 2) = q - 1 by omega, show q - 1 + 1 = q by omega]

/-- **Completeness.** The path of a leaf proves it under the root of its subtree. -/
theorem rootFromPath_pathOf (g : ℕ → Fr) (d i : ℕ) :
    rootFromPath H (g i) (pathOf H g d i) = subtree H g d (i / 2 ^ d) := by
  induction d generalizing g i with
  | zero => simp [pathOf, rootFromPath, subtree]
  | succ d ih =>
    have hstep : rootFromPath H (g i) (pathOf H g (d + 1) i)
        = rootFromPath H (up H g (i / 2)) (pathOf H (up H g) d (i / 2)) := by
      simp only [pathOf, rootFromPath, up]
      rcases Nat.mod_two_eq_zero_or_one i with h | h
      · simp only [h, zero_ne_one, decide_false, Bool.false_eq_true, ↓reduceIte]
        rw [show 2 * (i / 2) = i by omega]
      · simp only [h, decide_true, ↓reduceIte]
        rw [show 2 * (i / 2) = i - 1 by omega, show i - 1 + 1 = i by omega]
    rw [hstep, ih, subtree_succ', Nat.div_div_eq_div_mul, pow_succ, mul_comm]

/-- The selectors of the path of a leaf spell its index. -/
theorem pathIndex_pathOf (g : ℕ → Fr) (d i : ℕ) (hi : i < 2 ^ d) :
    pathIndex (pathOf H g d i) = i := by
  induction d generalizing g i with
  | zero => simp at hi; simp [pathOf, pathIndex, hi]
  | succ d ih =>
    simp only [pathOf, pathIndex]
    rw [ih _ _ (by rw [pow_succ] at hi; omega)]
    split_ifs <;> simp_all <;> omega

theorem length_pathOf (g : ℕ → Fr) (d i : ℕ) : (pathOf H g d i).length = d := by
  induction d generalizing g i with
  | zero => rfl
  | succ d ih => simp [pathOf, ih]

/-- **Binding.** Under a collision-free hash, a path whose root is the root of a tree proves
the leaf of that tree at the index its selectors spell. -/
theorem rootFromPath_eq_subtree {g : ℕ → Fr} {leaf : Fr} {p : List (Bool × Fr)}
    (h : rootFromPath H leaf p = subtree H g p.length 0) : leaf = g (pathIndex p) := by
  induction p generalizing g leaf with
  | nil => simpa [rootFromPath, subtree, pathIndex] using h
  | cons a p ih =>
    obtain ⟨s, n⟩ := a
    simp only [rootFromPath, List.length_cons, subtree_succ'] at h
    have h' := ih h
    simp only [up] at h'
    simp only [pathIndex]
    cases s
    · have := (Hash.node_injective h').1
      simpa using this
    · have := (Hash.node_injective h').2
      simp only [↓reduceIte] at this ⊢
      rw [this]; congr 1; omega

end Mantle
