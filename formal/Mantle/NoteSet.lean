import Mantle.MMR
import Mantle.IMT

/-!
# Note sets

Mantle, *Ledger* (RFC-480 §1): every note lives in one note set, the ledger set, the SDP set,
or the set of its channel. A set keeps

* the commitments of its notes in a commitment MMR. Here `cms` lists them in insertion order
  and the peaks the specification stores are `commitments = mmrPeaks cms`;
* the nullifiers of its spent notes, as a set (`nullifiers`) maintained in an IMT (`imt`);
* the commitment roots of the last `1024` blocks with their peaks (`recentRoots`, a
  dictionary given as a function) and the root at the end of each of these blocks
  (`recentBlocks`, oldest first);
* the transaction buffer `tx_cm_buffer`.

The methods are the specification's: `Spendable` is `assert_spendable`, `txCmRoot` is
`tx_cm_root`, `executeSpending`, `executeAdding` and `recordCmRoot` are `execute_spending`,
`execute_adding` and `record_cm_root`.

Results:

* `WindowInv` (preserved by every method, `windowInv_recordCmRoot`): the dictionary holds
  exactly the roots of `recentBlocks`, at most `1024` of them, each with the peaks of a prefix
  of the commitments. The removal test `oldest not in recent_cm_root_blocks` is what keeps a
  root that repeats across blocks;
* **`mem_of_txCmRoot`**: a non-zero commitment proven under `tx_cm_root` is a commitment of
  the set or of the part of the buffer the root covers;
* **`txCmRoot_of_prefix`**: `tx_cm_root` with `buffered = b` depends on the first `b`
  commitments of the buffer only. This is why a step or payment proven against a recent root
  "holds at any position" once the buffer has those `b` commitments.
-/

namespace Mantle

/-- `class NoteSet`. -/
structure NoteSet where
  cms : List Fr
  nullifiers : Finset Fr
  imt : List NfLeaf
  recentRoots : Fr → Option Peaks
  recentBlocks : List Fr
  buffer : List Fr

/-- The number of blocks whose commitment roots stay referenceable. -/
def ROOT_WINDOW : ℕ := 1024

namespace NoteSet

variable (H : Hash)

/-- The peaks the specification stores in `commitments`. -/
def commitments (s : NoteSet) : Peaks := mmrPeaks H s.cms

/-- `cm_root()`. -/
def cmRoot (s : NoteSet) : Fr := mmrRoot H (s.commitments H)

/-- `nf_root()`. -/
def nfRoot (s : NoteSet) : Fr := IMT.root H s.imt

/-- `empty_note_set()`. -/
def empty : NoteSet where
  cms := []
  nullifiers := ∅
  imt := [NfLeaf.sentinel]
  recentRoots := fun r => if r = mmrRoot H [] then some [] else none
  recentBlocks := [mmrRoot H []]
  buffer := []

/-- `assert_spendable(inputs, cm_merkle_root)`. -/
def Spendable (s : NoteSet) (inputs : List Fr) (root : Fr) : Prop :=
  inputs ≠ [] ∧ inputs.Nodup ∧ (s.recentRoots root).isSome ∧ ∀ nf ∈ inputs, nf ∉ s.nullifiers

/-- `tx_cm_root(cm_merkle_root, buffered)`: the referenced root extended with the first
`buffered` commitments of the buffer, all of them for `none`. `none` if the root is not
recent (the dictionary lookup fails). -/
def txCmRoot (s : NoteSet) (root : Fr) (buffered : Option ℕ) : Option Fr :=
  (s.recentRoots root).map fun peaks =>
    mmrRoot H ((s.buffer.take (buffered.getD s.buffer.length)).foldl (mmrAppend H) peaks)

/-- `execute_spending(inputs)`. -/
def executeSpending (s : NoteSet) (inputs : List Fr) : NoteSet :=
  { s with nullifiers := s.nullifiers ∪ inputs.toFinset
           imt := inputs.foldl IMT.insertNullifier s.imt }

/-- `execute_adding(outputs)`. -/
def executeAdding (s : NoteSet) (outputs : List Fr) : NoteSet :=
  { s with cms := s.cms ++ outputs }

/-- `tx_cm_buffer.extend(outputs)`. -/
def extendBuffer (s : NoteSet) (outputs : List Fr) : NoteSet :=
  { s with buffer := s.buffer ++ outputs }

/-- `record_cm_root()`. -/
def recordCmRoot (s : NoteSet) : NoteSet :=
  let root := mmrRoot H (s.commitments H)
  let roots := Function.update s.recentRoots root (some (s.commitments H))
  let blocks := s.recentBlocks ++ [root]
  if ROOT_WINDOW < blocks.length then
    { s with recentRoots := if blocks.head! ∈ blocks.tail then roots
                            else Function.update roots blocks.head! none
             recentBlocks := blocks.tail }
  else
    { s with recentRoots := roots, recentBlocks := blocks }

/-! ## The root window -/

/-- The dictionary of recent roots holds exactly the roots of `recentBlocks`, at most `1024`,
each with the peaks of a prefix of the commitments, whose root it is. -/
structure WindowInv (s : NoteSet) : Prop where
  keys : ∀ r, (s.recentRoots r).isSome ↔ r ∈ s.recentBlocks
  length_le : s.recentBlocks.length ≤ ROOT_WINDOW
  isPrefix : ∀ r p, s.recentRoots r = some p →
    ∃ k ≤ s.cms.length, p = mmrPeaks H (s.cms.take k) ∧ r = mmrRoot H p

variable {H}

theorem windowInv_empty : WindowInv H (empty H) where
  keys r := by by_cases h : r = mmrRoot H [] <;> simp [empty, h]
  length_le := by simp [empty, ROOT_WINDOW]
  isPrefix r p h := by
    by_cases hr : r = mmrRoot H [] <;> simp [empty, hr] at h
    subst h hr
    exact ⟨0, le_rfl, by simp [mmrPeaks], rfl⟩

theorem windowInv_executeAdding {s : NoteSet} (W : WindowInv H s) (outs : List Fr) :
    WindowInv H (s.executeAdding outs) where
  keys := W.keys
  length_le := W.length_le
  isPrefix r p h := by
    obtain ⟨k, hk, hp, hr⟩ := W.isPrefix r p h
    refine ⟨k, by simp [executeAdding]; omega, ?_, hr⟩
    simp [executeAdding, List.take_append_of_le_length hk, hp]

theorem windowInv_executeSpending {s : NoteSet} (W : WindowInv H s) (ins : List Fr) :
    WindowInv H (s.executeSpending ins) := ⟨W.keys, W.length_le, W.isPrefix⟩

theorem windowInv_extendBuffer {s : NoteSet} (W : WindowInv H s) (outs : List Fr) :
    WindowInv H (s.extendBuffer outs) := ⟨W.keys, W.length_le, W.isPrefix⟩

theorem window_keys_drop_mem {roots : Fr → Option Peaks} {B : List Fr}
    (hk : ∀ r, (roots r).isSome ↔ r ∈ B) (hm : B.head! ∈ B.tail) (r : Fr) :
    (roots r).isSome ↔ r ∈ B.tail := by
  cases B with
  | nil => simp at hm
  | cons a t =>
    simp only [List.head!_cons, List.tail_cons] at hm ⊢
    rw [hk, List.mem_cons]
    constructor
    · rintro (rfl | h) <;> assumption
    · exact Or.inr

theorem window_keys_drop_not_mem {roots : Fr → Option Peaks} {B : List Fr}
    (hk : ∀ r, (roots r).isSome ↔ r ∈ B) (hm : B.head! ∉ B.tail) (hne : B ≠ []) (r : Fr) :
    (Function.update roots B.head! none r).isSome ↔ r ∈ B.tail := by
  cases B with
  | nil => simp at hne
  | cons a t =>
    simp only [List.head!_cons, List.tail_cons] at hm ⊢
    by_cases hr : r = a
    · subst hr; simp [hm]
    · rw [Function.update_of_ne hr, hk]
      simp [hr]

/-- **Recording a root keeps the window**: the roots of the last `1024` blocks, a root that
repeats across blocks staying as long as one of its blocks is in the window. -/
theorem windowInv_recordCmRoot {s : NoteSet} (W : WindowInv H s) :
    WindowInv H (s.recordCmRoot H) := by
  have hpre : ∀ r p, Function.update s.recentRoots (mmrRoot H (s.commitments H))
      (some (s.commitments H)) r = some p →
      ∃ k ≤ s.cms.length, p = mmrPeaks H (s.cms.take k) ∧ r = mmrRoot H p := by
    intro r p h
    by_cases hr : r = mmrRoot H (s.commitments H)
    · subst hr
      simp only [Function.update_self, Option.some.injEq] at h
      subst h
      exact ⟨s.cms.length, le_rfl, by simp [commitments], rfl⟩
    · rw [Function.update_of_ne hr] at h
      exact W.isPrefix r p h
  have hkeys : ∀ r, (Function.update s.recentRoots (mmrRoot H (s.commitments H))
      (some (s.commitments H)) r).isSome ↔ r ∈ s.recentBlocks ++ [mmrRoot H (s.commitments H)] := by
    intro r
    by_cases hr : r = mmrRoot H (s.commitments H)
    · subst hr; simp
    · rw [Function.update_of_ne hr, W.keys]; simp [hr]
  have hlen0 := W.length_le
  unfold recordCmRoot
  dsimp only
  split_ifs with hlen hm
  · refine ⟨window_keys_drop_mem hkeys hm, ?_, hpre⟩
    simp only [List.length_tail, List.length_append, List.length_singleton]; omega
  · refine ⟨window_keys_drop_not_mem hkeys hm (by simp), ?_, fun r p h => ?_⟩
    · simp only [List.length_tail, List.length_append, List.length_singleton]; omega
    · dsimp only at h ⊢
      by_cases hr : r = (s.recentBlocks ++ [mmrRoot H (s.commitments H)]).head!
      · rw [hr] at h; simp at h
      · rw [Function.update_of_ne hr] at h; exact hpre r p h
  · exact ⟨hkeys, by simpa using hlen, hpre⟩

/-! ## Verification against a recent root extended with the buffer -/

/-- **Membership.** A non-zero commitment proven by a path of length `32` under `tx_cm_root`
is a commitment of the set, or one of the commitments of the buffer the root covers. -/
theorem mem_of_txCmRoot {s : NoteSet} (W : WindowInv H s) {root R : Fr} {b : Option ℕ}
    (h : s.txCmRoot H root b = some R) {cm : Fr} (hcm : cm ≠ 0) {p : List (Bool × Fr)}
    (hp : p.length = 32) (hpath : rootFromPath H cm p = R)
    (hcap : s.cms.length + s.buffer.length < 2 ^ 32) :
    cm ∈ s.cms ∨ cm ∈ s.buffer.take (b.getD s.buffer.length) := by
  simp only [txCmRoot, Option.map_eq_some_iff] at h
  obtain ⟨peaks, hpk, rfl⟩ := h
  obtain ⟨k, hk, rfl, -⟩ := W.isPrefix root peaks hpk
  rw [← mmrPeaks_append] at hpath
  have hlen : (s.cms.take k ++ s.buffer.take (b.getD s.buffer.length)).length < 2 ^ 32 := by
    simp only [List.length_append, List.length_take]
    omega
  rcases List.mem_append.1 (mem_of_mmrRoot hlen hcm hp hpath) with h | h
  · exact Or.inl (List.mem_of_mem_take h)
  · exact Or.inr h

/-- **A note cannot be consumed by a later transaction of the block that creates it** (Block
Construction, *Block Proposal Validation*): if every recent root is the root of a prefix of the
first `n₀` commitments (the commitments at the start of the block), a commitment appended after
them and absent from the buffer of the current transaction has no path under any
`tx_cm_root`. -/
theorem not_provable_of_fresh {s : NoteSet} {n₀ : ℕ}
    (hpre : ∀ r p, s.recentRoots r = some p → ∃ k ≤ n₀, p = mmrPeaks H (s.cms.take k))
    {root R : Fr} {b : Option ℕ} (h : s.txCmRoot H root b = some R) {cm : Fr} (hcm : cm ≠ 0)
    (hfresh : cm ∉ s.cms.take n₀) (hbuf : cm ∉ s.buffer)
    (hcap : n₀ + s.buffer.length < 2 ^ 32) :
    ∀ p : List (Bool × Fr), p.length = 32 → rootFromPath H cm p ≠ R := by
  intro p hp hpath
  simp only [txCmRoot, Option.map_eq_some_iff] at h
  obtain ⟨peaks, hpk, rfl⟩ := h
  obtain ⟨k, hk, rfl⟩ := hpre root peaks hpk
  rw [← mmrPeaks_append] at hpath
  have hlen : (s.cms.take k ++ s.buffer.take (b.getD s.buffer.length)).length < 2 ^ 32 := by
    simp only [List.length_append, List.length_take]; omega
  rcases List.mem_append.1 (mem_of_mmrRoot hlen hcm hp hpath) with h | h
  · exact hfresh (List.take_subset_take_left _ hk h)
  · exact hbuf (List.mem_of_mem_take h)

/-- With `buffered = 0`, `tx_cm_root` is the referenced root itself. -/
theorem txCmRoot_zero {s : NoteSet} (W : WindowInv H s) {root : Fr}
    (h : (s.recentRoots root).isSome) : s.txCmRoot H root (some 0) = some root := by
  obtain ⟨peaks, hpk⟩ := Option.isSome_iff_exists.1 h
  obtain ⟨k, -, -, hr⟩ := W.isPrefix root _ hpk
  simp only [txCmRoot, hpk, Option.map_some, Option.getD_some, List.take_zero, List.foldl_nil]
  rw [hr]

/-- **Position independence.** `tx_cm_root` with `buffered = b` is the same in two note sets
with the same recent roots whose buffers share their first `b` commitments. -/
theorem txCmRoot_of_prefix {s s' : NoteSet} (hroots : s.recentRoots = s'.recentRoots)
    {b : ℕ} (hb : s.buffer.take b = s'.buffer.take b) (root : Fr) :
    s.txCmRoot H root (some b) = s'.txCmRoot H root (some b) := by
  simp only [txCmRoot, Option.getD_some, hroots, hb]

/-- In particular, once the buffer holds `b` commitments, appending more changes nothing for
a proof covering the first `b`. -/
theorem txCmRoot_extendBuffer {s : NoteSet} {b : ℕ} (hb : b ≤ s.buffer.length)
    (outs : List Fr) (root : Fr) :
    (s.extendBuffer outs).txCmRoot H root (some b) = s.txCmRoot H root (some b) := by
  exact txCmRoot_of_prefix (s := s.extendBuffer outs) (s' := s) rfl
    (by simp [extendBuffer, List.take_append_of_le_length hb]) root

end NoteSet

end Mantle
