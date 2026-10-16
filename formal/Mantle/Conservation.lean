import Mantle.Supply

/-!
# No Mantle Transaction creates value

The value of a Mantle state (`value`) is the value of the distinct unspent notes of every note
set, plus the value of the notes that SDP withdrawals release at the removal of their
declarations (`inflight`), plus the proof of work reward pool.

**`applyTx_value`**: a valid Mantle Transaction leaves a state whose value, plus the mandatory
fee and the tip it pays, is at most the value before. No Operation creates value:

* a ZkTransfer balances its inputs with its outputs and its excess, and its inputs are notes
  of their set that are still unspent (`ZkTransfer.consumed`);
* the steps of an inscription balance exactly, payments into the program spend, and no two
  steps consume the same note (`validateSteps_spec`, `validateSteps_names`);
* an SDP withdrawal consumes exactly the service note of its declaration, and the value it
  releases waits in the declaration;
* a proof of work claim moves value from the pool;
* a channel withdrawal moves nothing until it is released, and is balanced when posted.

The statement is an inequality because notes can be lost: an output whose commitment already
exists (same value, nonce, key, program and data) can never be spent separately.

Hypotheses: the invariant `Inv` (established by `Inv` being preserved, from any state
satisfying it), and `Cap`: every note set holds fewer than `2^31` commitments, so that the
trees a proof refers to, of at most twice that many leaves, stay within depth `32`.
-/

namespace Mantle

open Classical

noncomputable section

variable {H : Hash}

/-! ## What a verified ZkTransfer consumes -/

namespace ZkTransfer

variable {ins outs : List Fr} {ex : ℕ} {R msg : Fr} {wit : ZkTransferWitness}

/-- The commitments of the inputs of a ZkTransfer. -/
def inputCms (H : Hash) (wit : ZkTransferWitness) : List Fr :=
  wit.inputs.map fun w => noteCm H (w.note H)

theorem outputs_eq (hv : ZkTransferRel H ⟨ins, outs, ex, R, msg⟩ wit) :
    outs = wit.outputs.map fun w => noteCm H w.note := by
  apply List.ext_getElem (by simp [length_outputs hv])
  intro k h1 h2
  simpa using (output_note hv h1).2.1

theorem listValue_outputs (hv : ZkTransferRel H ⟨ins, outs, ex, R, msg⟩ wit) :
    listValue H outs = (wit.outputs.map (·.value)).sum := by
  rw [outputs_eq hv, listValue, List.map_map]
  congr 1
  apply List.map_congr_left
  intro w _
  simp [cmValue_noteCm, OutputWitness.note]

theorem listValue_inputCms (wit : ZkTransferWitness) :
    listValue H (inputCms H wit) = (wit.inputs.map (·.value)).sum := by
  rw [inputCms, listValue, List.map_map]
  congr 1
  apply List.map_congr_left
  intro w _
  simp [cmValue_noteCm, InputWitness.note]

theorem names (hv : ZkTransferRel H ⟨ins, outs, ex, R, msg⟩ wit) : Names H ins (inputCms H wit) := by
  unfold Names
  rw [List.forall₂_iff_get]
  refine ⟨by simp [inputCms, length_inputs hv], fun k h1 h2 => ?_⟩
  obtain ⟨-, hpk, hnf, -, -⟩ := input_note hv h1
  simp only [List.get_eq_getElem, inputCms, List.getElem_map]
  rw [cmNf_of_kdf _ _ hpk, ← hnf]

/-- The inputs balance the outputs and the excess. -/
theorem value_eq (hv : ZkTransferRel H ⟨ins, outs, ex, R, msg⟩ wit) :
    listValue H (inputCms H wit) = listValue H outs + ex := by
  rw [listValue_inputCms, listValue_outputs hv, balance hv]

/-- The inputs are commitments of the set or of the buffer the root covers. -/
theorem inputs_mem {s : NoteSet} (W : s.WindowInv H) {root : Fr} {b : Option ℕ}
    (hR : s.txCmRoot H root b = some R) (hv : ZkTransferRel H ⟨ins, outs, ex, R, msg⟩ wit)
    (hcap : s.cms.length + s.buffer.length < 2 ^ 32) :
    ∀ c ∈ inputCms H wit, c ∈ s.cms ∨ c ∈ s.buffer.take (b.getD s.buffer.length) := by
  intro c hc
  simp only [inputCms, List.mem_map] at hc
  obtain ⟨w, hw, rfl⟩ := hc
  obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hw
  have hk' : k < ins.length := by rw [← length_inputs hv]; exact hk
  obtain ⟨-, -, -, hp, hpath⟩ := input_note hv hk'
  exact NoteSet.mem_of_txCmRoot W hR (noteCm_ne_zero _) hp hpath hcap

/-- A witness of the ZkTransfer consumes distinct notes of its set (or of the buffer), named by
its nullifiers, whose value is its outputs' plus its excess. -/
theorem consumedRel {s : NoteSet} (W : s.WindowInv H) {root : Fr} {b : Option ℕ}
    (hR : s.txCmRoot H root b = some R) (hv : ZkTransferRel H ⟨ins, outs, ex, R, msg⟩ wit)
    (hcap : s.cms.length + s.buffer.length < 2 ^ 32) :
    ∃ cs, Names H ins cs ∧ (∀ c ∈ cs, c ∈ s.cms ∨ c ∈ s.buffer.take (b.getD s.buffer.length)) ∧
      listValue H cs = listValue H outs + ex :=
  ⟨_, names hv, inputs_mem W hR hv hcap, value_eq hv⟩

/-- **A verified ZkTransfer consumes distinct notes of its set (or of the buffer), named by
its nullifiers, whose value is its outputs' plus its excess**, by knowledge soundness. -/
theorem consumed {P : Prims} [P.ZkTransferSound] {s : NoteSet} (W : s.WindowInv P.H)
    {root : Fr} {b : Option ℕ} (hR : s.txCmRoot P.H root b = some R) {π : ProofBlob}
    (hv : P.zkTransferVerify ⟨ins, outs, ex, R, msg⟩ π)
    (hcap : s.cms.length + s.buffer.length < 2 ^ 32) :
    ∃ cs, Names P.H ins cs ∧ (∀ c ∈ cs, c ∈ s.cms ∨ c ∈ s.buffer.take (b.getD s.buffer.length)) ∧
      listValue P.H cs = listValue P.H outs + ex := by
  obtain ⟨w, hw⟩ := Prims.ZkTransferSound.sound hv
  exact consumedRel W hR hw hcap

end ZkTransfer

namespace ZkProgramSpend

variable {ins outs : List Fr} {flags : List Bool} {R pid : Fr} {paid : ℕ} {snh msg : Fr}
  {wit : ZkProgramSpendWitness}

/-- The commitments of the inputs of a program spend. -/
def inputCms (H : Hash) (pid : Fr) (wit : ZkProgramSpendWitness) : List Fr :=
  wit.inputs.map fun w => noteCm H (w.note H pid)

theorem outputs_eq (hv : ZkProgramSpendRel H ⟨ins, outs, flags, R, pid, paid, snh, msg⟩ wit) :
    outs = wit.outputs.map fun w => noteCm H w.note := by
  apply List.ext_getElem (by simp [length_outputs hv])
  intro k h1 h2
  simpa using (output_note hv h1).2.1

theorem names (hv : ZkProgramSpendRel H ⟨ins, outs, flags, R, pid, paid, snh, msg⟩ wit) :
    Names H ins (inputCms H pid wit) := by
  unfold Names
  rw [List.forall₂_iff_get]
  refine ⟨by simp [inputCms, length_inputs hv], fun k h1 h2 => ?_⟩
  obtain ⟨-, hpk, hnf, -, -⟩ := input_note hv h1
  simp only [List.get_eq_getElem, inputCms, List.getElem_map]
  rw [cmNf_of_kdf _ _ hpk, ← hnf]

/-- The inputs and the paid value balance the outputs exactly. -/
theorem value_eq (hv : ZkProgramSpendRel H ⟨ins, outs, flags, R, pid, paid, snh, msg⟩ wit) :
    listValue H (inputCms H pid wit) + paid = listValue H outs := by
  have h1 : listValue H (inputCms H pid wit) = (wit.inputs.map (·.value)).sum := by
    rw [inputCms, listValue, List.map_map]
    congr 1
    apply List.map_congr_left
    intro w _
    simp [cmValue_noteCm, SpendInputWitness.note]
  have h2 : listValue H outs = (wit.outputs.map (·.value)).sum := by
    rw [outputs_eq hv, listValue, List.map_map]
    congr 1
    apply List.map_congr_left
    intro w _
    simp [cmValue_noteCm, SpendOutputWitness.note]
  rw [h1, h2, balance hv]

theorem inputs_mem {s : NoteSet} (W : s.WindowInv H) {root : Fr} {b : Option ℕ}
    (hR : s.txCmRoot H root b = some R) (hv : ZkProgramSpendRel H ⟨ins, outs, flags, R, pid, paid, snh, msg⟩ wit)
    (hcap : s.cms.length + s.buffer.length < 2 ^ 32) :
    ∀ c ∈ inputCms H pid wit, c ∈ s.cms ∨ c ∈ s.buffer.take (b.getD s.buffer.length) := by
  intro c hc
  simp only [inputCms, List.mem_map] at hc
  obtain ⟨w, hw, rfl⟩ := hc
  obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hw
  have hk' : k < ins.length := by rw [← length_inputs hv]; exact hk
  obtain ⟨-, -, -, hp, hpath⟩ := input_note hv hk'
  exact NoteSet.mem_of_txCmRoot W hR (noteCm_ne_zero _) hp hpath hcap

/-- **A verified program spend consumes distinct notes of the set (or of the buffer), named
by its nullifiers, which with the paid value are worth exactly its outputs**, by knowledge
soundness. -/
theorem consumed {P : Prims} [P.ZkProgramSpendSound] {s : NoteSet} (W : s.WindowInv P.H)
    {root : Fr} {b : Option ℕ} (hR : s.txCmRoot P.H root b = some R) {π : ProofBlob}
    (hv : P.zkProgramSpendVerify ⟨ins, outs, flags, R, pid, paid, snh, msg⟩ π)
    (hcap : s.cms.length + s.buffer.length < 2 ^ 32) :
    ∃ cs, Names P.H ins cs ∧ (∀ c ∈ cs, c ∈ s.cms ∨ c ∈ s.buffer.take (b.getD s.buffer.length)) ∧
      listValue P.H cs + paid = listValue P.H outs := by
  obtain ⟨w, hw⟩ := Prims.ZkProgramSpendSound.sound hv
  exact ⟨_, names hw, inputs_mem W hR hw hcap, value_eq hw⟩

end ZkProgramSpend

/-! ## The value of a state -/

/-- The value of the unspent notes of a set. -/
def NoteSet.supply (H : Hash) (s : NoteSet) : ℕ := Mantle.supply H s.cms s.nullifiers

/-- The value of the unspent notes of every note set. -/
def setsValue (H : Hash) (st : State) : ℕ :=
  ∑ i ∈ Finset.range st.numSets, (st.sets i).supply H

/-- The value SDP withdrawals release at the removal of their declarations. -/
def inflight (H : Hash) (st : State) : ℕ :=
  (st.declarations.map fun e => listValue H e.2.withdrawOutputs).sum

/-- The value of a Mantle state. -/
def value (H : Hash) (st : State) : ℕ := setsValue H st + inflight H st + st.powRewardPool

/-! ### State setters -/

namespace State

variable (st : State)

@[simp] theorem withDecls_sets (l) : (st.withDecls l).sets = st.sets := rfl
@[simp] theorem withDecls_numSets (l) : (st.withDecls l).numSets = st.numSets := rfl
@[simp] theorem withDecls_channels (l) : (st.withDecls l).channels = st.channels := rfl
@[simp] theorem withDecls_pending (l) :
    (st.withDecls l).pendingWithdrawals = st.pendingWithdrawals := rfl
@[simp] theorem withDecls_declarations (l) : (st.withDecls l).declarations = l := rfl
@[simp] theorem withDecls_pool (l) : (st.withDecls l).powRewardPool = st.powRewardPool := rfl

@[simp] theorem withPending_sets (l) : (st.withPending l).sets = st.sets := rfl
@[simp] theorem withPending_numSets (l) : (st.withPending l).numSets = st.numSets := rfl
@[simp] theorem withPending_channels (l) : (st.withPending l).channels = st.channels := rfl
@[simp] theorem withPending_pending (l) : (st.withPending l).pendingWithdrawals = l := rfl
@[simp] theorem withPending_declarations (l) :
    (st.withPending l).declarations = st.declarations := rfl
@[simp] theorem withPending_pool (l) : (st.withPending l).powRewardPool = st.powRewardPool := rfl

@[simp] theorem withPrograms_sets (f) : (st.withPrograms f).sets = st.sets := rfl
@[simp] theorem withPrograms_numSets (f) : (st.withPrograms f).numSets = st.numSets := rfl
@[simp] theorem withPrograms_channels (f) : (st.withPrograms f).channels = st.channels := rfl
@[simp] theorem withPrograms_pending (f) :
    (st.withPrograms f).pendingWithdrawals = st.pendingWithdrawals := rfl
@[simp] theorem withPrograms_declarations (f) :
    (st.withPrograms f).declarations = st.declarations := rfl
@[simp] theorem withPrograms_pool (f) : (st.withPrograms f).powRewardPool = st.powRewardPool := rfl

@[simp] theorem withChannels_sets (f) : (st.withChannels f).sets = st.sets := rfl
@[simp] theorem withChannels_numSets (f) : (st.withChannels f).numSets = st.numSets := rfl
@[simp] theorem withChannels_channels (f) : (st.withChannels f).channels = f := rfl
@[simp] theorem withChannels_pending (f) :
    (st.withChannels f).pendingWithdrawals = st.pendingWithdrawals := rfl
@[simp] theorem withChannels_declarations (f) :
    (st.withChannels f).declarations = st.declarations := rfl
@[simp] theorem withChannels_pool (f) : (st.withChannels f).powRewardPool = st.powRewardPool := rfl
@[simp] theorem withChannels_programs (f) : (st.withChannels f).programs = st.programs := rfl

@[simp] theorem withPow_sets (a b) : (st.withPow a b).sets = st.sets := rfl
@[simp] theorem withPow_numSets (a b) : (st.withPow a b).numSets = st.numSets := rfl
@[simp] theorem withPow_channels (a b) : (st.withPow a b).channels = st.channels := rfl
@[simp] theorem withPow_pending (a b) :
    (st.withPow a b).pendingWithdrawals = st.pendingWithdrawals := rfl
@[simp] theorem withPow_declarations (a b) : (st.withPow a b).declarations = st.declarations := rfl
@[simp] theorem withPow_pool (a b) : (st.withPow a b).powRewardPool = a := rfl

@[simp] theorem addSet_sets (s) : (st.addSet s).sets = Function.update st.sets st.numSets s := rfl
@[simp] theorem addSet_numSets (s) : (st.addSet s).numSets = st.numSets + 1 := rfl
@[simp] theorem addSet_channels (s) : (st.addSet s).channels = st.channels := rfl
@[simp] theorem addSet_pending (s) : (st.addSet s).pendingWithdrawals = st.pendingWithdrawals :=
  rfl
@[simp] theorem addSet_declarations (s) : (st.addSet s).declarations = st.declarations := rfl
@[simp] theorem addSet_pool (s) : (st.addSet s).powRewardPool = st.powRewardPool := rfl
@[simp] theorem addSet_programs (s) : (st.addSet s).programs = st.programs := rfl

end State

@[simp] theorem setsValue_withDecls (st : State) (l) :
    setsValue H (st.withDecls l) = setsValue H st := rfl
@[simp] theorem setsValue_withPending (st : State) (l) :
    setsValue H (st.withPending l) = setsValue H st := rfl
@[simp] theorem setsValue_withPrograms (st : State) (f) :
    setsValue H (st.withPrograms f) = setsValue H st := rfl
@[simp] theorem setsValue_withChannels (st : State) (f) :
    setsValue H (st.withChannels f) = setsValue H st := rfl
@[simp] theorem setsValue_withPow (st : State) (a b) :
    setsValue H (st.withPow a b) = setsValue H st := rfl
@[simp] theorem inflight_withPending (st : State) (l) :
    inflight H (st.withPending l) = inflight H st := rfl
@[simp] theorem inflight_withPrograms (st : State) (f) :
    inflight H (st.withPrograms f) = inflight H st := rfl
@[simp] theorem inflight_withChannels (st : State) (f) :
    inflight H (st.withChannels f) = inflight H st := rfl
@[simp] theorem inflight_withPow (st : State) (a b) :
    inflight H (st.withPow a b) = inflight H st := rfl
@[simp] theorem inflight_addSet (st : State) (s) :
    inflight H (st.addSet s) = inflight H st := rfl

/-- A note set is well formed: its root window, a buffer made of commitments of the set, and an
IMT that is the sorted linked list of exactly its nullifiers. -/
structure SetInv (H : Hash) (s : NoteSet) : Prop where
  window : s.WindowInv H
  sublist : List.Sublist s.buffer s.cms
  imt : IMT.Inv s.imt s.nullifiers

/-- Nullifiers that can be inserted: distinct, not yet spent, and non-zero. -/
def Fresh (s : NoteSet) (ins : List Fr) : Prop :=
  ins.Nodup ∧ ∀ nf ∈ ins, nf ∉ s.nullifiers ∧ nf ≠ 0

theorem IMT.inv_foldl (l : List Fr) : ∀ (leaves : List NfLeaf) (S : Finset Fr),
    IMT.Inv leaves S → l.Nodup → (∀ nf ∈ l, nf ∉ S ∧ nf ≠ 0) →
    IMT.Inv (l.foldl IMT.insertNullifier leaves) (S ∪ l.toFinset) := by
  induction l with
  | nil => intro leaves S I _ _; simpa using I
  | cons a l ih =>
    intro leaves S I hn hf
    rw [List.nodup_cons] at hn
    have I' := IMT.inv_insertNullifier I (hf a (by simp)).2 (hf a (by simp)).1
    have := ih _ _ I' hn.2 (fun nf h => ⟨by
      rw [Finset.mem_insert, not_or]
      exact ⟨fun e => hn.1 (e ▸ h), (hf nf (by simp [h])).1⟩, (hf nf (by simp [h])).2⟩)
    rw [List.foldl_cons, List.toFinset_cons, Finset.union_insert, ← Finset.insert_union]
    exact this

/-- A pending channel withdrawal is balanced, and its inputs are distinct notes of its set. -/
def PendingOk (H : Hash) (st : State) (w : Slot × ℕ × List Fr × List Fr) : Prop :=
  2 ≤ w.2.1 ∧ w.2.1 < st.numSets ∧ w.2.2.1.Nodup ∧
    ∃ cs, Names H w.2.2.1 cs ∧ (∀ c ∈ cs, c ∈ (st.sets w.2.1).cms) ∧
      listValue H cs = listValue H w.2.2.2

/-- The invariant of a Mantle state. -/
structure Inv (H : Hash) (st : State) : Prop where
  two_le : 2 ≤ st.numSets
  sets : ∀ i < st.numSets, SetInv H (st.sets i)
  chan : ∀ c ch, st.channels c = some ch → ∀ j, ch.noteSet = some j → 2 ≤ j ∧ j < st.numSets
  declNodup : (st.declarations.map Prod.fst).Nodup
  declNote : ∀ e ∈ st.declarations, e.2.serviceNote ∈ (st.sets SDP_SET).cms
  declOutputs : ∀ e ∈ st.declarations, e.2.withdrawAt = none → e.2.withdrawOutputs = []
  pending : ∀ w ∈ st.pendingWithdrawals, PendingOk H st w

/-- Every note set holds fewer than `2^31` commitments. -/
def Cap (st : State) : Prop := ∀ i < st.numSets, 2 * (st.sets i).cms.length < 2 ^ 32

/-- The note sets only grow. -/
def Grows (st st' : State) : Prop :=
  st.numSets ≤ st'.numSets ∧ ∀ i < st.numSets, (st.sets i).cms <+: (st'.sets i).cms

theorem Grows.refl (st : State) : Grows st st := ⟨le_rfl, fun _ _ => List.prefix_refl _⟩

theorem Grows.trans {a b c : State} (h1 : Grows a b) (h2 : Grows b c) : Grows a c :=
  ⟨h1.1.trans h2.1, fun i hi => (h1.2 i hi).trans (h2.2 i (lt_of_lt_of_le hi h1.1))⟩

theorem Cap.of_grows {st st' : State} (h : Cap st') (hg : Grows st st') : Cap st := by
  intro i hi
  have := (hg.2 i hi).length_le
  have := h i (lt_of_lt_of_le hi hg.1)
  omega

/-! ### Updating one note set -/

theorem setsValue_setSet {st : State} {i : ℕ} (hi : i < st.numSets) (s : NoteSet) :
    setsValue H (st.setSet i s) + (st.sets i).supply H = setsValue H st + s.supply H := by
  have hmem : i ∈ Finset.range st.numSets := Finset.mem_range.2 hi
  simp only [setsValue, State.setSet]
  rw [← Finset.add_sum_erase _ _ hmem, ← Finset.add_sum_erase _ _ hmem, Function.update_self,
    Finset.sum_congr rfl (fun j hj => by rw [Function.update_of_ne (Finset.ne_of_mem_erase hj)])]
  ring

@[simp] theorem setSet_sets_self (st : State) (i : ℕ) (s : NoteSet) :
    (st.setSet i s).sets i = s := by simp [State.setSet]

theorem setSet_sets_of_ne (st : State) {i j : ℕ} (h : j ≠ i) (s : NoteSet) :
    (st.setSet i s).sets j = st.sets j := by simp [State.setSet, h]

@[simp] theorem setSet_numSets (st : State) (i : ℕ) (s : NoteSet) :
    (st.setSet i s).numSets = st.numSets := rfl

@[simp] theorem setSet_declarations (st : State) (i : ℕ) (s : NoteSet) :
    (st.setSet i s).declarations = st.declarations := rfl

@[simp] theorem setSet_channels (st : State) (i : ℕ) (s : NoteSet) :
    (st.setSet i s).channels = st.channels := rfl

@[simp] theorem setSet_pending (st : State) (i : ℕ) (s : NoteSet) :
    (st.setSet i s).pendingWithdrawals = st.pendingWithdrawals := rfl

@[simp] theorem setSet_pool (st : State) (i : ℕ) (s : NoteSet) :
    (st.setSet i s).powRewardPool = st.powRewardPool := rfl

theorem inflight_setSet (st : State) (i : ℕ) (s : NoteSet) :
    inflight H (st.setSet i s) = inflight H st := rfl

/-! ### Note set methods -/

@[simp] theorem NoteSet.executeAdding_cms (s : NoteSet) (l : List Fr) :
    (s.executeAdding l).cms = s.cms ++ l := rfl
@[simp] theorem NoteSet.executeAdding_nullifiers (s : NoteSet) (l : List Fr) :
    (s.executeAdding l).nullifiers = s.nullifiers := rfl
@[simp] theorem NoteSet.executeAdding_buffer (s : NoteSet) (l : List Fr) :
    (s.executeAdding l).buffer = s.buffer := rfl
@[simp] theorem NoteSet.executeSpending_cms (s : NoteSet) (l : List Fr) :
    (s.executeSpending l).cms = s.cms := rfl
@[simp] theorem NoteSet.executeSpending_nullifiers (s : NoteSet) (l : List Fr) :
    (s.executeSpending l).nullifiers = s.nullifiers ∪ l.toFinset := rfl
@[simp] theorem NoteSet.executeSpending_buffer (s : NoteSet) (l : List Fr) :
    (s.executeSpending l).buffer = s.buffer := rfl
@[simp] theorem NoteSet.extendBuffer_cms (s : NoteSet) (l : List Fr) :
    (s.extendBuffer l).cms = s.cms := rfl
@[simp] theorem NoteSet.extendBuffer_nullifiers (s : NoteSet) (l : List Fr) :
    (s.extendBuffer l).nullifiers = s.nullifiers := rfl
@[simp] theorem NoteSet.extendBuffer_buffer (s : NoteSet) (l : List Fr) :
    (s.extendBuffer l).buffer = s.buffer ++ l := rfl
@[simp] theorem NoteSet.extendBuffer_recentRoots (s : NoteSet) (l : List Fr) :
    (s.extendBuffer l).recentRoots = s.recentRoots := rfl

theorem SetInv.spend_add {s : NoteSet} (I : SetInv H s) {ins : List Fr} (outs : List Fr)
    (hf : Fresh s ins) :
    SetInv H (((s.extendBuffer outs).executeSpending ins).executeAdding outs) where
  window := NoteSet.windowInv_executeAdding (NoteSet.windowInv_executeSpending
    (NoteSet.windowInv_extendBuffer I.window _) _) _
  sublist := by simpa using I.sublist.append_right outs
  imt := IMT.inv_foldl ins _ _ I.imt hf.1 hf.2

theorem SetInv.spend {s : NoteSet} (I : SetInv H s) {ins : List Fr} (hf : Fresh s ins) :
    SetInv H (s.executeSpending ins) :=
  ⟨NoteSet.windowInv_executeSpending I.window _, I.sublist, IMT.inv_foldl ins _ _ I.imt hf.1 hf.2⟩

theorem SetInv.empty : SetInv H (NoteSet.empty H) :=
  ⟨NoteSet.windowInv_empty, by simp [NoteSet.empty], IMT.inv_init⟩

/-- The nullifiers of notes are never `0`. -/
theorem Names.ne_zero {ins cs : List Fr} (h : Names H ins cs) : ∀ nf ∈ ins, nf ≠ 0 := by
  intro nf hnf
  obtain ⟨c, -, hc⟩ := forall₂_mem_left h hnf
  simp only [cmNf, Option.bind_eq_some_iff, Option.map_eq_some_iff] at hc
  obtain ⟨_, _, _, _, rfl⟩ := hc
  exact noteNf_ne_zero _ _

/-- The buffer covered by a root is among the commitments of a well-formed set. -/
theorem SetInv.mem_cms {s : NoteSet} (I : SetInv H s) {c : Fr} {b : Option ℕ}
    (h : c ∈ s.cms ∨ c ∈ s.buffer.take (b.getD s.buffer.length)) : c ∈ s.cms := by
  rcases h with h | h
  · exact h
  · exact I.sublist.subset (List.mem_of_mem_take h)

theorem SetInv.cap {s : NoteSet} (I : SetInv H s) (h : 2 * s.cms.length < 2 ^ 32) :
    s.cms.length + s.buffer.length < 2 ^ 32 := by
  have := I.sublist.length_le; omega

end

end Mantle
