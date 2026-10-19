import Mantle.Block

/-!
# The Proof of Leadership over the eligible root

RFC-480 §3, Proof of Leadership 1.2.x: the eligible root is a Merkle tree of depth `32` whose
leaf `i` is `zkhash(ELIGIBLE_SET_LEAF_V1, cm_root_i, nf_root_i)` for note set `i`, positions
past the last set holding `0`. The Proof of Leadership proves its note

* **aged**: its commitment in the commitment MMR of its set, and the leaf of that set, with
  the set's aged nullifier root, under `eligible_aged`;
* **latest**: its nullifier absent from the IMT of the same set, and the leaf of the set, with
  its latest commitment root, under `eligible_latest`;

both set paths using the same selectors. The note commitment is derived with `program` and
`data` set to `0` (RFC-481 §1).

`PoLWitness` and `PoLRel` transcribe these constraints (the lottery and the entropy
contribution are left out: they do not bear on which note leads). Results:

* `pathIndex_eq_of_selectors`: two paths with the same selectors prove the same position, so
  **both checks name the same set**;
* **`pol_sound`** (and `pol_sound_of_inv` for states reached by Mantle): under a collision-free
  hash, a proof satisfying `PoLRel` against the eligible
  roots of two snapshots of the ledger proves a note that is a commitment of set `i` in the aged
  snapshot and whose nullifier is not spent in set `i` in the latest snapshot;
* `pol_user_note`: the note is a user note, so program notes do not lead.
-/

namespace Mantle

open Classical

noncomputable section

variable (H : Hash)

/-- The leaf of a note set in the eligible tree. -/
def eligibleLeaf (cmRoot nfRoot : Fr) : Fr := H.zkhash [ELIGIBLE_SET_LEAF_V1, cmRoot, nfRoot]

/-- The leaves of the eligible tree over the roots of the note sets, then `0`. -/
def eligibleLeaves (roots : List (Fr × Fr)) (i : ℕ) : Fr :=
  if h : i < roots.length then eligibleLeaf H roots[i].1 roots[i].2 else 0

/-- The eligible root over the `(cm_root, nf_root)` of each note set. -/
def eligibleRoot (roots : List (Fr × Fr)) : Fr := subtree H (eligibleLeaves H roots) 32 0

/-- The roots of a ledger snapshot: for every note set, its commitment MMR root and its
nullifier IMT root. -/
def setRoots (st : State) : List (Fr × Fr) :=
  (List.range st.numSets).map fun i => ((st.sets i).cmRoot H, (st.sets i).nfRoot H)

/-- The witness of the eligibility part of a Proof of Leadership. -/
structure PoLWitness where
  sk : Fr
  value : ℕ
  nonce : Fr
  cmPath : List (Bool × Fr)
  agedNfRoot : Fr
  agedSetPath : List (Bool × Fr)
  low : NfLeaf
  lowPath : List (Bool × Fr)
  latestCmRoot : Fr
  latestSetPath : List (Bool × Fr)

/-- The note a Proof of Leadership proves: a user note under the key of `sk`. -/
def PoLWitness.note (w : PoLWitness) : Note := ⟨w.value, w.nonce, kdf H w.sk, 0, 0⟩

/-- The eligibility constraints of the Proof of Leadership. -/
def PoLRel (eligibleAged eligibleLatest : Fr) (w : PoLWitness) : Prop :=
  let cm := noteCm H (w.note H)
  let nf := noteNf H cm w.sk
  w.cmPath.length = 32 ∧ w.agedSetPath.length = 32 ∧ w.lowPath.length = 32 ∧
    w.latestSetPath.length = 32 ∧
    -- aged: the note in its set, the set under the aged eligible root
    rootFromPath H (eligibleLeaf H (rootFromPath H cm w.cmPath) w.agedNfRoot) w.agedSetPath =
      eligibleAged ∧
    -- latest: the nullifier absent from the same set, the set under the latest eligible root
    w.low.nf < nf ∧ (nf < w.low.nextNf ∨ w.low.nextNf = 0) ∧
    rootFromPath H (eligibleLeaf H w.latestCmRoot
      (rootFromPath H (IMT.leafHash H w.low) w.lowPath)) w.latestSetPath = eligibleLatest ∧
    -- the same set selectors
    w.agedSetPath.map Prod.fst = w.latestSetPath.map Prod.fst

variable {H}

/-- The selectors of a path determine the position it proves. -/
theorem pathIndex_eq_of_selectors {p q : List (Bool × Fr)} (h : p.map Prod.fst = q.map Prod.fst) :
    pathIndex p = pathIndex q := by
  induction p generalizing q with
  | nil => cases q with
    | nil => rfl
    | cons _ _ => simp at h
  | cons a p ih =>
    cases q with
    | nil => simp at h
    | cons b q =>
      simp only [List.map_cons, List.cons.injEq] at h
      obtain ⟨⟨s, x⟩, ⟨t, y⟩⟩ := (a, b)
      simp only [pathIndex, h.1, ih h.2]

theorem eligibleLeaf_injective {a b a' b' : Fr} (h : eligibleLeaf H a b = eligibleLeaf H a' b') :
    a = a' ∧ b = b' := by
  have := H.injective h
  simp only [List.cons.injEq, and_true, true_and] at this
  exact this

/-- A leaf proven under the eligible root is the leaf of a note set. -/
theorem eligible_mem {roots : List (Fr × Fr)} {c n : Fr} {p : List (Bool × Fr)}
    (hp : p.length = 32) (h : rootFromPath H (eligibleLeaf H c n) p = eligibleRoot H roots) :
    ∃ hi : pathIndex p < roots.length, roots[pathIndex p] = (c, n) := by
  rw [eligibleRoot, ← hp] at h
  have := rootFromPath_eq_subtree h
  simp only [eligibleLeaves] at this
  split_ifs at this with hi
  · obtain ⟨h1, h2⟩ := eligibleLeaf_injective this
    exact ⟨hi, Prod.ext h1.symm h2.symm⟩
  · exact absurd this (H.ne_zero _)

theorem getElem_setRoots {st : State} {i : ℕ} (hi : i < (setRoots H st).length) :
    (setRoots H st)[i] = ((st.sets i).cmRoot H, (st.sets i).nfRoot H) := by
  simp [setRoots]

/-- **Soundness of the eligibility checks.** A Proof of Leadership against the eligible roots
of an aged and a latest snapshot proves a note that is a commitment of some set `i` in the aged
snapshot and whose nullifier is unspent in the same set `i` in the latest snapshot. -/
theorem pol_sound {aged latest : State} (Iaged : ∀ i < aged.numSets, (aged.sets i).cms.length < 2 ^ 32)
    (Ilatest : ∀ i < latest.numSets, IMT.Inv (latest.sets i).imt (latest.sets i).nullifiers)
    {w : PoLWitness}
    (h : PoLRel H (eligibleRoot H (setRoots H aged)) (eligibleRoot H (setRoots H latest)) w) :
    ∃ i, i < aged.numSets ∧ i < latest.numSets ∧
      noteCm H (w.note H) ∈ (aged.sets i).cms ∧
      noteNf H (noteCm H (w.note H)) w.sk ∉ (latest.sets i).nullifiers := by
  obtain ⟨hc, ha, hl, hls, hAged, hlt, hnext, hLatest, hsel⟩ := h
  obtain ⟨hi, hroot⟩ := eligible_mem ha hAged
  obtain ⟨hi', hroot'⟩ := eligible_mem hls hLatest
  have hij := pathIndex_eq_of_selectors hsel
  have hia : pathIndex w.agedSetPath < aged.numSets := by simpa [setRoots] using hi
  have hil : pathIndex w.latestSetPath < latest.numSets := by simpa [setRoots] using hi'
  rw [getElem_setRoots] at hroot hroot'
  simp only [Prod.mk.injEq] at hroot hroot'
  refine ⟨pathIndex w.agedSetPath, hia, hij ▸ hil, ?_, ?_⟩
  · -- the commitment is in the MMR of set `i`
    have h1 := hroot.1
    simp only [NoteSet.cmRoot, NoteSet.commitments] at h1
    exact mem_of_mmrRoot (Iaged _ hia) (noteCm_ne_zero _) hc h1.symm
  · -- the nullifier is not in the IMT of set `i`
    have h2 := hroot'.2
    simp only [NoteSet.nfRoot] at h2
    rw [hij]
    exact IMT.not_mem_of_path (Ilatest _ hil) (noteNf_ne_zero _ _) hl h2.symm hlt hnext

/-- **`pol_sound` for ledger states reached by Mantle**: the invariant `Inv` keeps every IMT
the sorted list of its set's nullifiers. The Proof of Leadership involves no buffer, so the
capacity it needs is the specification's, fewer than `2^32` commitments per set. -/
theorem pol_sound_of_inv {aged latest : State}
    (hcap : ∀ i < aged.numSets, (aged.sets i).cms.length < 2 ^ 32)
    (Il : Inv H latest) {w : PoLWitness}
    (h : PoLRel H (eligibleRoot H (setRoots H aged)) (eligibleRoot H (setRoots H latest)) w) :
    ∃ i, i < aged.numSets ∧ i < latest.numSets ∧
      noteCm H (w.note H) ∈ (aged.sets i).cms ∧
      noteNf H (noteCm H (w.note H)) w.sk ∉ (latest.sets i).nullifiers :=
  pol_sound hcap (fun i hi => (Il.sets i hi).imt) h

/-- The note of a Proof of Leadership is a user note: no program note leads. -/
theorem pol_user_note (w : PoLWitness) : (w.note H).IsUser := ⟨rfl, rfl⟩

/-- A program note never has the commitment a Proof of Leadership proves. -/
theorem pol_not_program_note (w : PoLWitness) {n : Note} (hn : n.program ≠ 0) :
    noteCm H n ≠ noteCm H (w.note H) :=
  noteCm_ne_of_program hn (pol_user_note w)

end

end Mantle
