import Mantle.Channels

/-!
# What any valid Genesis provides

The results of `Mantle` and `TokenEconomics` hold from any state satisfying the invariants
`Inv` and `ChanInv`. No Genesis state is built: instead, `State.IsGenesis` states what any valid
Genesis visibly leaves, in the terms of the Genesis block, and **`Inv.of_genesis`**,
**`ChanInv.of_genesis`** show that it satisfies both invariants.

A valid Genesis (Genesis Block) appends the initial commitments to empty note sets, spends in
the ledger set the nullifiers of the notes its declarations consume, and records the root of
every set (`NoteSet.IsInitial`); its declarations have distinct ids and service notes in the
SDP set, and have released nothing; it posts no channel withdrawal; and its inscriptions create
the null channel only, which has no note set. Nothing is required of the commitments, the
values, the declarations' content, the programs or the proof of work state.
-/

namespace Mantle

open Classical

noncomputable section

variable {H : Hash}

/-- A note set as Genesis leaves it: the empty set to which commitments are appended and in which
distinct non-zero nullifiers are spent, its root then recorded. -/
def NoteSet.IsInitial (H : Hash) (s : NoteSet) : Prop :=
  ∃ cms nfs : List Fr, nfs.Nodup ∧ 0 ∉ nfs ∧
    s = (((NoteSet.empty H).executeAdding cms).executeSpending nfs).recordCmRoot H

/-- What any valid Genesis leaves. -/
structure State.IsGenesis (H : Hash) (st : State) : Prop where
  /-- The ledger and SDP sets. -/
  two_le : 2 ≤ st.numSets
  sets : ∀ i < st.numSets, (st.sets i).IsInitial H
  declNodup : (st.declarations.map Prod.fst).Nodup
  declNote : ∀ e ∈ st.declarations, e.2.serviceNote ∈ (st.sets SDP_SET).cms
  /-- No declaration has released notes. -/
  declOutputs : ∀ e ∈ st.declarations, e.2.withdrawOutputs = []
  noPending : st.pendingWithdrawals = []
  /-- Channels without note sets, each with a key, its tip sequencer one of them and a
  `uint16` threshold: the null channel Genesis inscribes to. -/
  channels : ∀ c ch, st.channels c = some ch → ch.noteSet = none ∧ ChanOk ch

theorem NoteSet.IsInitial.setInv {s : NoteSet} (h : s.IsInitial H) : SetInv H s := by
  obtain ⟨cms, nfs, hnd, h0, rfl⟩ := h
  have S1 := (SetInv.empty (H := H)).add cms
  have S2 := S1.spend (ins := nfs) ⟨hnd, fun nf hnf => ⟨by simp [NoteSet.empty,
    NoteSet.executeAdding], fun e => h0 (e ▸ hnf)⟩⟩
  exact ⟨NoteSet.windowInv_recordCmRoot S2.window, by simp,
    by simpa using S2.imt⟩

/-- **Any valid Genesis satisfies the ledger invariant.** -/
theorem Inv.of_genesis {st : State} (G : st.IsGenesis H) : Inv H st where
  two_le := G.two_le
  sets i hi := (G.sets i hi).setInv
  chan c ch hc j hj := by simp [(G.channels c ch hc).1] at hj
  declNodup := G.declNodup
  declNote := G.declNote
  declOutputs e he _ := G.declOutputs e he
  pending w hw := by simp [G.noPending] at hw

/-- **Any valid Genesis satisfies the channel invariant.** -/
theorem ChanInv.of_genesis {st : State} (G : st.IsGenesis H) : ChanInv st :=
  fun c ch hc => (G.channels c ch hc).2

/-- `State.IsGenesis` is satisfiable, so the results stated from it are not vacuous: two note
sets holding the given commitments, a channel created by an inscription to the null channel,
and no declaration. -/
theorem isGenesis_exists (cms₀ cms₁ : List Fr) (k : Fr) (slot : Slot) :
    ∃ st : State, st.IsGenesis H ∧ st.numSets = 2 ∧ (st.sets LEDGER_SET).cms = cms₀ ∧
      (st.sets SDP_SET).cms = cms₁ ∧ (st.channels 0).isSome := by
  let mk : List Fr → NoteSet := fun c =>
    (((NoteSet.empty H).executeAdding c).executeSpending []).recordCmRoot H
  refine ⟨⟨fun i => if i = 0 then mk cms₀ else mk cms₁, 2, [], fun _ => none,
    fun c => if c = 0 then some (defaultChannel slot [k] none) else none, [], 0, 0, ∅⟩,
    ⟨le_rfl, fun i _ => ?_, by simp, by simp, by simp, rfl, fun c ch hc => ?_⟩,
    rfl, ?_, ?_, by simp⟩
  · show NoteSet.IsInitial H (if i = 0 then mk cms₀ else mk cms₁)
    split_ifs
    · exact ⟨cms₀, [], List.nodup_nil, by simp, rfl⟩
    · exact ⟨cms₁, [], List.nodup_nil, by simp, rfl⟩
  · simp only at hc
    split_ifs at hc
    cases hc
    exact ⟨rfl, List.cons_ne_nil _ _, seqOk_defaultChannel slot k none, by simp [defaultChannel]⟩
  · simp [mk, LEDGER_SET, NoteSet.executeAdding, NoteSet.empty]
  · simp [mk, SDP_SET, NoteSet.executeAdding, NoteSet.empty]

end

end Mantle
