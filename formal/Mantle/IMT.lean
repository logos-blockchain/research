import Mantle.Merkle

/-!
# The nullifier indexed Merkle tree

Mantle, *Nullifier Indexed Merkle Tree*: the nullifiers of a note set are the leaves of an
IMT, appended in insertion order. A leaf `NullifierLeaf(nf, next_nf, next_index)` points to the
leaf of the next greater nullifier, so the leaves form a sorted linked list; the first leaf is
the sentinel `(0, 0, 0)`, and `next_nf = 0` means there is no greater nullifier.

* `walk` is the `while` loop of `insert_nullifier`, run with a fuel of one step per leaf
  (`walk_spec` shows the fuel never runs out before the loop ends where it should);
* `insertNullifier` is `insert_nullifier`.

Results, for the leaves built from the sentinel by inserting the nullifiers of a set `S`
(`Inv leaves S`, which holds initially, `inv_init`, and after every insertion of a fresh
non-zero nullifier, **`inv_insertNullifier`**):

* **`not_mem_iff`**: the non-membership criterion of the specification, `nf ∉ S` iff some leaf
  `low` has `low.nf < nf` and either `nf < low.next_nf` or `low.next_nf = 0`;
* **`not_mem_of_path`**: its circuit form, as the Proof of Leadership uses it. A leaf proven
  by a Merkle path under the IMT root, whose fields satisfy the criterion, shows `nf ∉ S`.
  Positions past the last leaf hold `0`, which no leaf hash equals, so they cannot serve.
-/

namespace Mantle

/-- `NullifierLeaf`. -/
structure NfLeaf where
  nf : Fr
  nextNf : Fr
  nextIndex : ℕ
deriving DecidableEq

/-- The sentinel leaf `(0, 0, 0)`. -/
def NfLeaf.sentinel : NfLeaf := ⟨0, 0, 0⟩

namespace IMT

/-- The leaf at index `j`, the sentinel past the end. -/
def get (leaves : List NfLeaf) (j : ℕ) : NfLeaf := leaves[j]?.getD NfLeaf.sentinel

/-- The loop of `insert_nullifier`: walk the sorted list to the leaf of the greatest
nullifier lower than `nf`. -/
def walk (leaves : List NfLeaf) (nf : Fr) : ℕ → ℕ → ℕ
  | 0, i => i
  | fuel + 1, i =>
    if (get leaves i).nextNf ≠ 0 ∧ (get leaves i).nextNf < nf then
      walk leaves nf fuel (get leaves i).nextIndex
    else i

/-- The insertion after the leaf `i`: the new leaf takes the successor of `low = leaves[i]`,
and `low` points to the new leaf. -/
def insertAt (leaves : List NfLeaf) (i : ℕ) (nf : Fr) : List NfLeaf :=
  let low := get leaves i
  leaves.set i ⟨low.nf, nf, leaves.length⟩ ++ [⟨nf, low.nextNf, low.nextIndex⟩]

/-- `insert_nullifier(leaves, nf)`. -/
def insertNullifier (leaves : List NfLeaf) (nf : Fr) : List NfLeaf :=
  insertAt leaves (walk leaves nf leaves.length 0) nf

/-- Leaf `L` points to the successor of `L.nf` among the nullifiers `S`. -/
def Succ (leaves : List NfLeaf) (S : Finset Fr) (L : NfLeaf) : Prop :=
  (L.nextNf = 0 ∧ L.nextIndex = 0 ∧ ∀ x ∈ S, x ≤ L.nf) ∨
  (L.nextNf ∈ S ∧ L.nf < L.nextNf ∧ (∀ x ∈ S, L.nf < x → L.nextNf ≤ x) ∧
    L.nextIndex < leaves.length ∧ (get leaves L.nextIndex).nf = L.nextNf)

/-- The invariant of the leaves of an IMT holding the nullifiers `S`. -/
structure Inv (leaves : List NfLeaf) (S : Finset Fr) : Prop where
  zero_not_mem : 0 ∉ S
  head : (get leaves 0).nf = 0
  nodup : (leaves.map NfLeaf.nf).Nodup
  nfs : (leaves.map NfLeaf.nf).toFinset = insert 0 S
  succ : ∀ k < leaves.length, Succ leaves S (get leaves k)

theorem get_of_lt {leaves : List NfLeaf} {k : ℕ} (hk : k < leaves.length) :
    get leaves k = leaves[k] := by
  simp [get, hk]

theorem length_pos {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) :
    0 < leaves.length := by
  rcases leaves with _ | _
  · exact absurd I.nfs.symm (by simp)
  · simp

theorem length_eq {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) :
    leaves.length = S.card + 1 := by
  have := List.toFinset_card_of_nodup I.nodup
  rw [I.nfs, Finset.card_insert_of_notMem I.zero_not_mem, List.length_map] at this
  exact this.symm

theorem nf_mem {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) {k : ℕ}
    (hk : k < leaves.length) : (get leaves k).nf = 0 ∨ (get leaves k).nf ∈ S := by
  have : (get leaves k).nf ∈ insert 0 S := by
    rw [← I.nfs, get_of_lt hk]; simp only [List.mem_toFinset, List.mem_map]
    exact ⟨_, List.getElem_mem hk, rfl⟩
  simpa using this

theorem exists_index {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) {x : Fr}
    (hx : x = 0 ∨ x ∈ S) : ∃ k < leaves.length, (get leaves k).nf = x := by
  have : x ∈ (leaves.map NfLeaf.nf).toFinset := by rw [I.nfs]; simpa using hx
  simp only [List.mem_toFinset, List.mem_map] at this
  obtain ⟨L, hL, rfl⟩ := this
  obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hL
  exact ⟨k, hk, by rw [get_of_lt hk]⟩

theorem index_unique {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) {k k' : ℕ}
    (hk : k < leaves.length) (hk' : k' < leaves.length)
    (h : (get leaves k).nf = (get leaves k').nf) : k = k' := by
  rw [get_of_lt hk, get_of_lt hk'] at h
  have := I.nodup
  rw [List.nodup_iff_injective_get] at this
  have := @this ⟨k, by simpa using hk⟩ ⟨k', by simpa using hk'⟩ (by simpa using h)
  simpa using this

/-- The IMT holding only its sentinel. -/
theorem inv_init : Inv [NfLeaf.sentinel] ∅ where
  zero_not_mem := by simp
  head := rfl
  nodup := by simp
  nfs := by simp [NfLeaf.sentinel]
  succ := by
    intro k hk
    simp only [List.length_singleton, Nat.lt_one_iff] at hk
    subst hk
    left; simp [get, NfLeaf.sentinel]

/-- **The non-membership criterion.** -/
theorem not_mem_iff {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) {nf : Fr}
    (hnf : nf ≠ 0) :
    nf ∉ S ↔ ∃ L ∈ leaves, L.nf < nf ∧ (nf < L.nextNf ∨ L.nextNf = 0) := by
  constructor
  · intro hS
    -- the leaf of the greatest element of `{0} ∪ S` below `nf`
    let T := (insert 0 S).filter (· < nf)
    have hT : T.Nonempty := ⟨0, by simp [T]; omega⟩
    have hmax := Finset.mem_filter.1 (Finset.max'_mem T hT)
    obtain ⟨k, hk, hkx⟩ := exists_index I (x := T.max' hT) (Finset.mem_insert.1 hmax.1)
    refine ⟨get leaves k, by rw [get_of_lt hk]; exact List.getElem_mem hk, ?_, ?_⟩
    · rw [hkx]; exact hmax.2
    · rcases I.succ k hk with ⟨h0, -, -⟩ | ⟨hmem, hlt, hmin, -, -⟩
      · exact Or.inr h0
      · left
        by_contra hge
        push Not at hge
        have hne : (get leaves k).nextNf ≠ nf := fun h => hS (h ▸ hmem)
        have : (get leaves k).nextNf ≤ T.max' hT :=
          Finset.le_max' T _ (by simp [T, hmem]; omega)
        omega
  · rintro ⟨L, hL, hlt, hnext⟩ hS
    obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hL
    rw [← get_of_lt hk] at hlt hnext
    rcases I.succ k hk with ⟨h0, -, hmax⟩ | ⟨hmem, -, hmin, -, -⟩
    · have := hmax nf hS; omega
    · have := hmin nf hS hlt
      rcases hnext with h | h
      · omega
      · rw [h] at hmem; exact I.zero_not_mem hmem

/-- The walk ends at the predecessor of `nf`: the leaf of the greatest element of `{0} ∪ S`
below `nf`. -/
theorem walk_spec {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) {nf : Fr} :
    ∀ fuel i, i < leaves.length → (get leaves i).nf < nf →
      ((S.filter fun x => (get leaves i).nf < x ∧ x < nf).card ≤ fuel) →
      let j := walk leaves nf fuel i
      j < leaves.length ∧ (get leaves j).nf < nf ∧ ∀ x ∈ S, x < nf → x ≤ (get leaves j).nf := by
  intro fuel
  induction fuel with
  | zero =>
    intro i hi hlt hcard
    simp only [walk]
    refine ⟨hi, hlt, fun x hx hxn => ?_⟩
    by_contra hc
    push Not at hc
    have : x ∈ S.filter fun x => (get leaves i).nf < x ∧ x < nf := by simp [hx, hc, hxn]
    rw [Finset.card_eq_zero.1 (Nat.le_zero.1 hcard)] at this
    simp at this
  | succ fuel ih =>
    intro i hi hlt hcard
    simp only [walk]
    split_ifs with hcond
    · obtain ⟨hne, hnlt⟩ := hcond
      rcases I.succ i hi with ⟨h0, -, -⟩ | ⟨hmem, hgt, hmin, hidx, hnfidx⟩
      · exact absurd h0 hne
      apply ih _ hidx (by rw [hnfidx]; exact hnlt)
      rw [hnfidx]
      have hsub : (S.filter fun x => (get leaves i).nextNf < x ∧ x < nf) ⊂
          (S.filter fun x => (get leaves i).nf < x ∧ x < nf) := by
        rw [Finset.ssubset_iff_of_subset]
        · exact ⟨(get leaves i).nextNf, by simp [hmem, hgt, hnlt], by simp⟩
        · intro x hx
          simp only [Finset.mem_filter] at hx ⊢
          exact ⟨hx.1, by omega, hx.2.2⟩
      have := Finset.card_lt_card hsub
      omega
    · refine ⟨hi, hlt, fun x hx hxn => ?_⟩
      push Not at hcond
      by_contra hc
      push Not at hc
      rcases I.succ i hi with ⟨h0, -, hmax⟩ | ⟨hmem, hgt, hmin, -, -⟩
      · have := hmax x hx; omega
      · have h1 := hmin x hx hc
        have h2 := hcond (by intro h; rw [h] at hmem; exact I.zero_not_mem hmem)
        omega

theorem walk_pred {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) {nf : Fr}
    (hnf : nf ≠ 0) :
    let j := walk leaves nf leaves.length 0
    j < leaves.length ∧ (get leaves j).nf < nf ∧ ∀ x ∈ S, x < nf → x ≤ (get leaves j).nf := by
  apply walk_spec I _ 0 (length_pos I) (by rw [I.head]; omega)
  calc _ ≤ S.card := Finset.card_filter_le _ _
    _ ≤ leaves.length := by rw [length_eq I]; omega

theorem get_insertAt (leaves : List NfLeaf) (i : ℕ) (nf : Fr) (j : ℕ) :
    get (insertAt leaves i nf) j =
      if j = i ∧ j < leaves.length then ⟨(get leaves j).nf, nf, leaves.length⟩
      else if j = leaves.length then ⟨nf, (get leaves i).nextNf, (get leaves i).nextIndex⟩
      else get leaves j := by
  simp only [insertAt, get]
  rcases lt_trichotomy j leaves.length with hj | rfl | hj
  · rw [List.getElem?_append_left (by simpa using hj), List.getElem?_set]
    by_cases hw : i = j
    · subst hw; simp [hj]
    · simp [hw, Ne.symm hw, hj.ne]
  · rw [List.getElem?_append_right (by simp)]
    simp
  · rw [List.getElem?_append_right (by simp; omega)]
    simp only [List.length_set, List.getElem?_singleton]
    rw [ite_eq_right (by omega), ite_eq_right (by omega), ite_eq_right (by omega)]
    simp [List.getElem?_eq_none (show leaves.length ≤ j by omega)]

theorem length_insertAt (leaves : List NfLeaf) (i : ℕ) (nf : Fr) :
    (insertAt leaves i nf).length = leaves.length + 1 := by
  simp [insertAt]

theorem map_nf_insertAt (leaves : List NfLeaf) (i : ℕ) (nf : Fr) :
    (insertAt leaves i nf).map NfLeaf.nf = leaves.map NfLeaf.nf ++ [nf] := by
  simp only [insertAt, List.map_append, List.map_set, List.map_cons, List.map_nil]
  congr 1
  by_cases h : i < leaves.length
  · have : (get leaves i).nf = (leaves.map NfLeaf.nf)[i]'(by simpa using h) := by
      simp [get_of_lt h]
    simp only [this, List.set_getElem_self]
  · exact List.set_eq_of_length_le (by simpa using h)

/-- Inserting `nf` after its predecessor `i` preserves the sorted linked list. -/
theorem inv_insertAt {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) {nf : Fr}
    (hnf : nf ≠ 0) (hS : nf ∉ S) {i : ℕ} (hi : i < leaves.length)
    (hlow : (get leaves i).nf < nf) (hpred : ∀ x ∈ S, x < nf → x ≤ (get leaves i).nf) :
    Inv (insertAt leaves i nf) (insert nf S) := by
  have hlen := length_insertAt leaves i nf
  -- nullifiers are unchanged at the old indices
  have hnf_old : ∀ j < leaves.length, (get (insertAt leaves i nf) j).nf = (get leaves j).nf := by
    intro j hj
    rw [get_insertAt]
    split_ifs <;> simp_all
  have hnf_new : (get (insertAt leaves i nf) leaves.length).nf = nf := by
    rw [get_insertAt, ite_eq_right (by omega), ite_eq_left rfl]
  have hpos := length_pos I
  have hgap : ∀ k < leaves.length, (get leaves k).nf < nf → k ≠ i →
      (get leaves k).nf < (get leaves i).nf := by
    intro k hk hlt hki
    have hle : (get leaves k).nf ≤ (get leaves i).nf := by
      rcases nf_mem I hk with h | h
      · rw [h]; exact Nat.zero_le _
      · exact hpred _ h hlt
    rcases hle.lt_or_eq with h | h
    · exact h
    · exact absurd (index_unique I hk hi h) hki
  refine
    { zero_not_mem := by simp [Ne.symm hnf, I.zero_not_mem]
      head := by rw [hnf_old 0 hpos, I.head]
      nodup := by
        rw [map_nf_insertAt, List.nodup_append]
        refine ⟨I.nodup, by simp, ?_⟩
        intro a ha b hb
        simp only [List.mem_singleton] at hb
        subst hb
        intro hab; subst hab
        have : a ∈ insert 0 S := by rw [← I.nfs]; simpa using ha
        rcases Finset.mem_insert.1 this with h | h
        · exact hnf h
        · exact hS h
      nfs := by
        rw [map_nf_insertAt, List.toFinset_append, I.nfs]
        ext x; simp only [Finset.mem_union, Finset.mem_insert, List.mem_toFinset,
          List.mem_singleton]; tauto
      succ := ?_ }
  intro k hk
  rw [hlen] at hk
  rw [get_insertAt]
  by_cases hki : k = i ∧ k < leaves.length
  · -- the predecessor now points to `nf`
    rw [ite_eq_left hki]
    obtain ⟨rfl, -⟩ := hki
    right
    dsimp only
    refine ⟨Finset.mem_insert_self _ _, hlow, ?_, by omega, hnf_new⟩
    intro x hx hlt
    rcases Finset.mem_insert.1 hx with rfl | hx
    · exact le_rfl
    · by_contra hc; push Not at hc
      have := hpred x hx hc; omega
  rw [ite_eq_right hki]
  by_cases hkn : k = leaves.length
  · -- the new leaf takes the old successor of the predecessor
    rw [ite_eq_left hkn]
    rcases I.succ i hi with ⟨h0, h0i, hmax⟩ | ⟨hmem, hgt, hmin, hidx, hnfidx⟩
    · left
      refine ⟨h0, h0i, fun x hx => ?_⟩
      rcases Finset.mem_insert.1 hx with rfl | hx
      · exact le_rfl
      · have := hmax x hx; dsimp only; omega
    · have hnext : nf < (get leaves i).nextNf := by
        rcases lt_trichotomy (get leaves i).nextNf nf with h | h | h
        · have := hpred _ hmem h; omega
        · exact absurd (h ▸ hmem) hS
        · exact h
      right
      refine ⟨Finset.mem_insert_of_mem hmem, hnext, ?_, by dsimp only; omega, ?_⟩
      · intro x hx hlt
        rcases Finset.mem_insert.1 hx with rfl | hx
        · dsimp only at hlt; omega
        · exact hmin x hx (by dsimp only at hlt; omega)
      · dsimp only; rw [hnf_old _ hidx, hnfidx]
  · -- every other leaf keeps its successor
    rw [ite_eq_right hkn]
    have hkn' : k < leaves.length := by omega
    have hki' : k ≠ i := fun h => hki ⟨h, hkn'⟩
    rcases I.succ k hkn' with ⟨h0, h0i, hmax⟩ | ⟨hmem, hgt, hmin, hidx, hnfidx⟩
    · left
      refine ⟨h0, h0i, fun x hx => ?_⟩
      rcases Finset.mem_insert.1 hx with rfl | hx
      · by_contra hc; push Not at hc
        have h1 := hgap k hkn' hc hki'
        have h2 : (get leaves i).nf ≤ (get leaves k).nf := by
          rcases nf_mem I hi with h | h
          · rw [h]; exact Nat.zero_le _
          · exact hmax _ h
        omega
      · exact hmax x hx
    · right
      refine ⟨Finset.mem_insert_of_mem hmem, hgt, ?_, by omega, by rw [hnf_old _ hidx, hnfidx]⟩
      intro x hx hlt
      rcases Finset.mem_insert.1 hx with rfl | hx
      · by_contra hc; push Not at hc
        have h1 := hgap k hkn' hlt hki'
        rcases nf_mem I hi with h | h
        · omega
        · have := hmin _ h h1; omega
      · exact hmin x hx hlt

/-- **Inserting a fresh non-zero nullifier preserves the sorted linked list.** -/
theorem inv_insertNullifier {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) {nf : Fr}
    (hnf : nf ≠ 0) (hS : nf ∉ S) : Inv (insertNullifier leaves nf) (insert nf S) := by
  obtain ⟨hi, hlow, hpred⟩ := walk_pred I hnf
  exact inv_insertAt I hnf hS hi hlow hpred

/-! ## The IMT root and the circuit's non-membership proof -/

variable (H : Hash)

/-- `nullifier_leaf_hash`. -/
def leafHash (L : NfLeaf) : Fr := H.zkhash [NULLIFIER_IMT_LEAF_V1, L.nf, L.nextNf, L.nextIndex]

/-- The leaves of the IMT tree: the leaf hashes, then `0`. -/
def leafHashes (leaves : List NfLeaf) (j : ℕ) : Fr :=
  if h : j < leaves.length then leafHash H leaves[j] else 0

/-- The root of the IMT: the depth-32 Merkle root over the leaf hashes. -/
def root (leaves : List NfLeaf) : Fr := subtree H (leafHashes H leaves) 32 0

variable {H}

/-- **The circuit's non-membership proof is sound.** A leaf `low` proven by a path of length
`32` under the IMT root, with `low.nf < nf` and `nf < low.next_nf` or `low.next_nf = 0`,
shows `nf ∉ S`. -/
theorem not_mem_of_path {leaves : List NfLeaf} {S : Finset Fr} (I : Inv leaves S) {nf : Fr}
    (hnf : nf ≠ 0) {low : NfLeaf} {p : List (Bool × Fr)} (hp : p.length = 32)
    (hpath : rootFromPath H (leafHash H low) p = root H leaves)
    (hlt : low.nf < nf) (hnext : nf < low.nextNf ∨ low.nextNf = 0) : nf ∉ S := by
  rw [root, ← hp] at hpath
  have := rootFromPath_eq_subtree hpath
  simp only [leafHashes] at this
  split_ifs at this with h
  · have hmem : low ∈ leaves := by
      have := H.injective this
      simp only [List.cons.injEq, and_true, true_and] at this
      obtain ⟨h1, h2, h3⟩ := this
      have : low = leaves[pathIndex p] := by
        cases low; cases hL : leaves[pathIndex p]; simp_all
      rw [this]; exact List.getElem_mem h
    exact (not_mem_iff I hnf).2 ⟨low, hmem, hlt, hnext⟩
  · exact absurd this (H.ne_zero _)

end IMT

end Mantle
