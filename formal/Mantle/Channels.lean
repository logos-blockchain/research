import Mantle.Programs

/-!
# Channels: steps, mini-blocks, withdrawals, sequencing

RFC-480 §2 and Mantle, *Channel Operations*.

**Steps at any position, mini-blocks** (`validateSteps_users_iff`,
**`validateSteps_users_perm`**). Steps that cover at most the commitments the buffer holds
when they start (`buffered ≤ len(tx_cm_buffer)`) validate together iff each validates on its
own against that buffer and no two consume the same note. The condition does not depend on
their order: the steps of a mini-block can be published in any order. With `buffered = 0`
for every step this is the first mini-block, proven against recent roots only.

**Withdrawals** (`releaseOne_*`): a withdrawal waits `WITHDRAW_DELAY` slots; at its due slot
it is applied if none of its inputs was consumed in the meantime, and dropped otherwise, so a
valid step consuming one of its notes before then cancels it; once released, its inputs are
spent and no later step can consume them (`not_spendable_of_mem`). It carries no fee.

**Sequencing and configuration**: `roundRobin_lt` (the sequencer index is a key of the
channel, given `SeqOk`, which every write of `tip_sequencer` keeps: `seqOk_defaultChannel`,
`seqOk_config`, `seqOk_inscribe`), **`roundRobin_infinite`** (an infinite posting timeframe
never rotates), `multiSigOk_nodup` (the signatures of a configuration come from distinct accredited
keys), and the null channel has no note set and so receives no step (`createChannel_null`,
`validateInscribe_no_set`).
-/

namespace Mantle

open Classical

noncomputable section

variable {P : Prims}

/-! ## Steps at any position -/

/-- A user step checked on its own against a note set. -/
def UserStepOk (P : Prims) (s : NoteSet) (u : UserStep) (π : ProofBlob) : Prop :=
  s.Spendable u.inputs u.cmMerkleRoot ∧ u.buffered ≤ s.buffer.length ∧
    ∃ R, s.txCmRoot P.H u.cmMerkleRoot (some u.buffered) = some R ∧
      P.zkTransferVerify ⟨u.inputs, u.outputs, 0, R, stepMsg P.H u⟩ π

theorem userStepOk_extendBuffer {s : NoteSet} {u : UserStep} {π : ProofBlob}
    (hb : u.buffered ≤ s.buffer.length) (outs : List Fr) :
    UserStepOk P (s.extendBuffer outs) u π ↔ UserStepOk P s u π := by
  unfold UserStepOk
  rw [NoteSet.txCmRoot_extendBuffer hb]
  simp only [NoteSet.extendBuffer_buffer, List.length_append]
  constructor
  · rintro ⟨h1, -, h3⟩; exact ⟨h1, hb, h3⟩
  · rintro ⟨h1, -, h3⟩; exact ⟨h1, by omega, h3⟩

/-- **User steps covering at most the current buffer validate together iff each validates on
its own and no two consume the same note**, nor a note consumed by an earlier step. -/
theorem validateSteps_users_iff {opIdFr : Fr} {programs : Fr → Option VerificationKey}
    (l : List (UserStep × ProofBlob)) :
    ∀ (s : NoteSet) (nfs : Finset Fr), (∀ x ∈ l, x.1.buffered ≤ s.buffer.length) →
      ((validateSteps P opIdFr programs s nfs (l.map fun x => Step.user x.1)
        (l.map fun x => StepProof.user x.2)).isSome ↔
      (∀ x ∈ l, UserStepOk P s x.1 x.2) ∧ (l.flatMap fun x => x.1.inputs).Nodup ∧
        ∀ nf ∈ l.flatMap (fun x => x.1.inputs), nf ∉ nfs) := by
  induction l with
  | nil => intro s nfs _; simp [validateSteps]
  | cons x l ih =>
    intro s nfs hb
    obtain ⟨u, π⟩ := x
    have hbu : u.buffered ≤ s.buffer.length := hb _ (List.mem_cons_self ..)
    have hbl : ∀ y ∈ l, y.1.buffered ≤ (s.extendBuffer u.outputs).buffer.length := by
      intro y hy
      have := hb y (List.mem_cons_of_mem _ hy)
      simp only [NoteSet.extendBuffer_buffer, List.length_append]; omega
    have ihx := ih (s.extendBuffer u.outputs) (nfs ∪ u.inputs.toFinset) hbl
    have hrest : ∀ y ∈ l, UserStepOk P (s.extendBuffer u.outputs) y.1 y.2 ↔
        UserStepOk P s y.1 y.2 := fun y hy =>
      userStepOk_extendBuffer (hb y (List.mem_cons_of_mem _ hy)) _
    simp only [List.map_cons, validateSteps]
    rw [Option.isSome_iff_exists]
    simp only [option_bind_eq_some, ensure_eq_some, exists_const]
    constructor
    · rintro ⟨sv, hsp, hdisj, hbuf, R, hR, hv, hval⟩
      have := ihx.1 (Option.isSome_iff_exists.2 ⟨sv, hval⟩)
      obtain ⟨hok, hnd, hfr⟩ := this
      refine ⟨?_, ?_, ?_⟩
      · intro y hy
        rcases List.mem_cons.1 hy with rfl | hy
        · exact ⟨hsp, hbuf, R, hR, hv⟩
        · exact (hrest y hy).1 (hok y hy)
      · rw [List.flatMap_cons, List.nodup_append]
        refine ⟨hsp.2.1, hnd, fun a ha b hb hab => ?_⟩
        subst hab
        exact hfr a hb (Finset.mem_union_right _ (List.mem_toFinset.2 ha))
      · intro nf hnf
        rw [List.flatMap_cons, List.mem_append] at hnf
        rcases hnf with hnf | hnf
        · exact hdisj nf hnf
        · exact fun h => hfr nf hnf (Finset.mem_union_left _ h)
    · rintro ⟨hok, hnd, hfr⟩
      obtain ⟨hsp, hbuf, R, hR, hv⟩ := hok _ (List.mem_cons_self ..)
      rw [List.flatMap_cons, List.nodup_append] at hnd
      have := ihx.2 ⟨fun y hy => (hrest y hy).2 (hok y (List.mem_cons_of_mem _ hy)), hnd.2.1,
        fun nf hnf h => by
          rcases Finset.mem_union.1 h with h | h
          · exact hfr nf (by rw [List.flatMap_cons]; exact List.mem_append_right _ hnf) h
          · exact hnd.2.2 nf (List.mem_toFinset.1 h) nf hnf rfl⟩
      obtain ⟨sv, hsv⟩ := Option.isSome_iff_exists.1 this
      exact ⟨sv, hsp, fun nf h => hfr nf (by rw [List.flatMap_cons]; exact List.mem_append_left _ h),
        hbuf, R, hR, hv, hsv⟩

/-- **The steps of a mini-block can be published in any order**: reordering user steps that
cover at most the buffer they start from does not change whether they validate. -/
theorem validateSteps_users_perm {opIdFr : Fr} {programs : Fr → Option VerificationKey}
    {l l' : List (UserStep × ProofBlob)} (hp : l.Perm l') {s : NoteSet} {nfs : Finset Fr}
    (hb : ∀ x ∈ l, x.1.buffered ≤ s.buffer.length) :
    (validateSteps P opIdFr programs s nfs (l.map fun x => Step.user x.1)
        (l.map fun x => StepProof.user x.2)).isSome ↔
      (validateSteps P opIdFr programs s nfs (l'.map fun x => Step.user x.1)
        (l'.map fun x => StepProof.user x.2)).isSome := by
  rw [validateSteps_users_iff l s nfs hb,
    validateSteps_users_iff l' s nfs (fun x hx => hb x (hp.mem_iff.2 hx))]
  have hf := hp.flatMap_right fun x : UserStep × ProofBlob => x.1.inputs
  constructor
  · rintro ⟨h1, h2, h3⟩
    exact ⟨fun x hx => h1 x (hp.mem_iff.2 hx), hf.nodup_iff.1 h2,
      fun nf hnf => h3 nf (hf.mem_iff.2 hnf)⟩
  · rintro ⟨h1, h2, h3⟩
    exact ⟨fun x hx => h1 x (hp.mem_iff.1 hx), hf.nodup_iff.2 h2,
      fun nf hnf => h3 nf (hf.mem_iff.1 hnf)⟩

/-- **No two steps or payments of an inscription consume the same note.** -/
theorem validateSteps_nodup [P.ZkTransferSound] [P.ZkProgramSpendSound] {opIdFr : Fr} {programs : Fr → Option VerificationKey}
    {steps : List Step} {πs : List StepProof} {s sv : NoteSet} {nfs : Finset Fr}
    (W : s.WindowInv P.H) (hcap : s.cms.length + s.buffer.length + (steps.flatMap Step.outs).length < 2 ^ 32)
    (h : validateSteps P opIdFr programs s nfs steps πs = some sv) :
    (steps.flatMap Step.ins).Nodup :=
  (validateSteps_spec steps πs s nfs W hcap h).2.1

/-! ## Withdrawals -/

/-- A withdrawal is kept until its due slot, `WITHDRAW_DELAY` slots after it was posted. -/
theorem releaseOne_not_due {slot due j : ℕ} {ins outs : List Fr} {st : State}
    {pending : List (Slot × ℕ × List Fr × List Fr)} (h : slot < due) :
    releaseOne slot (st, pending) (due, j, ins, outs) = (st, pending ++ [(due, j, ins, outs)]) := by
  simp [releaseOne, h]

/-- **A step consuming one of its notes before it is due cancels a withdrawal**: it is dropped,
and nothing changes. -/
theorem releaseOne_cancelled {slot due j : ℕ} {ins outs : List Fr} {st : State}
    {pending : List (Slot × ℕ × List Fr × List Fr)} (h : due ≤ slot) {nf : Fr} (hnf : nf ∈ ins)
    (hspent : nf ∈ (st.sets j).nullifiers) :
    releaseOne slot (st, pending) (due, j, ins, outs) = (st, pending) := by
  simp only [releaseOne, ite_eq_right (not_lt.2 h)]
  rw [ite_eq_right (fun hall => hall nf hnf hspent)]

/-- A due withdrawal whose inputs are unspent consumes them in its channel set and creates its
outputs in the ledger set. -/
theorem releaseOne_applied {slot due j : ℕ} {ins outs : List Fr} {st : State}
    {pending : List (Slot × ℕ × List Fr × List Fr)} (h : due ≤ slot)
    (hun : ∀ nf ∈ ins, nf ∉ (st.sets j).nullifiers) :
    releaseOne slot (st, pending) (due, j, ins, outs) =
      ((st.setSet j ((st.sets j).executeSpending ins)).setSet LEDGER_SET
        (((st.setSet j ((st.sets j).executeSpending ins)).sets LEDGER_SET).executeAdding outs),
        pending) := by
  simp only [releaseOne, ite_eq_right (not_lt.2 h)]
  rw [ite_eq_left hun]

/-- Once a note is spent, no Operation or step can consume it: `assert_spendable` fails. -/
theorem not_spendable_of_mem {s : NoteSet} {ins : List Fr} {root nf : Fr} (h : nf ∈ ins)
    (hspent : nf ∈ s.nullifiers) : ¬ s.Spendable ins root :=
  fun hs => hs.2.2.2 nf h hspent

/-- A channel withdrawal carries no fee, and is due `WITHDRAW_DELAY` slots after it is posted. -/
theorem applyChannelWithdraw_fee {E : Env} {st st' : State} {txh : Fr} {w : ChannelWithdraw}
    {π : ProofBlob} {fee : ℕ} (h : applyChannelWithdraw P E st txh w π = some (st', fee)) :
    fee = 0 ∧ ∃ j, st'.pendingWithdrawals =
      st.pendingWithdrawals ++ [(E.blockSlot + WITHDRAW_DELAY, j, w.inputs, w.outputs)] := by
  simp only [applyChannelWithdraw, ensure_eq_some, option_bind_eq_some, option_pure_eq,
    Option.some.injEq, Prod.mk.injEq, exists_const] at h
  obtain ⟨-, -, j, -, -, R, -, -, rfl, rfl⟩ := h
  exact ⟨rfl, j, rfl⟩

/-! ## Sequencing and configuration -/

/-- The tip sequencer of a channel is one of its accredited keys. -/
def SeqOk (c : ChannelState) : Prop := c.tipSequencer < c.accreditedKeys.length

/-- The round robin names one of the accredited keys. The infinite timeframe returns the tip
sequencer unreduced, so this needs `SeqOk`. -/
theorem roundRobin_lt (slot : Slot) (c : ChannelState) (h : c.accreditedKeys ≠ [])
    (hs : SeqOk c) : (roundRobin slot c).1 < c.accreditedKeys.length := by
  have := List.length_pos_iff.2 h
  simp only [roundRobin]
  split_ifs
  · exact Nat.mod_lt _ this
  · exact hs
  · exact Nat.mod_lt _ this

/-- **An infinite posting timeframe never rotates**: while no timeout is due, the tip sequencer
keeps its turn and its starting slot. A new channel has both parameters `0`, so its creator
sequences it until a configuration changes them. -/
theorem roundRobin_infinite (slot : Slot) (c : ChannelState) (hf : c.postingTimeframe = 0)
    (ht : ¬(c.postingTimeout ≤ slot - c.tipSlot ∧ c.postingTimeout ≠ 0)) :
    roundRobin slot c = (c.tipSequencer, c.tipSequencerStartingSlot) := by
  simp only [roundRobin, ht, hf, ite_false, ite_true]

/-- Every write of `tip_sequencer` keeps it below the number of keys: a new channel (`0` of one
key), a configuration (`0`, with at least one key) and an inscription (`round_robin`). -/
theorem seqOk_defaultChannel (slot : Slot) (k : Fr) (n : Option ℕ) :
    SeqOk (defaultChannel slot [k] n) := by
  simp [SeqOk, defaultChannel]

theorem seqOk_config (c : ChannelState) (keys : List Fr) (h : keys ≠ []) (t : ℕ) (slot : Slot)
    (pf po : ℕ) (cfg : Fr) :
    SeqOk { c with accreditedKeys := keys, configurationThreshold := t, tipSlot := slot,
                   tipSequencer := 0, tipSequencerStartingSlot := slot, postingTimeframe := pf,
                   postingTimeout := po, configTipHash := cfg } :=
  List.length_pos_iff.2 h

theorem seqOk_inscribe (c : ChannelState) (h : c.accreditedKeys ≠ []) (hs : SeqOk c)
    (slot : Slot) (tip : Fr) :
    SeqOk { c with tipSequencerStartingSlot := (roundRobin slot c).2,
                   tipSequencer := (roundRobin slot c).1, tipHash := tip, tipSlot := slot } :=
  roundRobin_lt slot c h hs

/-- The signatures of a configuration come from distinct accredited keys, as many as the
threshold. -/
theorem multiSigOk_nodup {msg : Fr} {sigs : List Fr} {idx : List ℕ} {keys : List Fr} {t : ℕ}
    (h : MultiSigOk P msg sigs idx keys t) :
    idx.Nodup ∧ idx.length = t ∧ ∀ i ∈ idx, i < keys.length := by
  obtain ⟨h1, h2, h3, h4⟩ := h
  refine ⟨(List.isChain_iff_pairwise.1 h3).imp fun h => h.ne, by omega, fun i hi => ?_⟩
  obtain ⟨k, hk, hki⟩ := List.getElem_of_mem hi
  obtain ⟨key, hkey, -⟩ := h4 (sigs[k]'(by omega), i) (by
    rw [List.mem_iff_getElem]; exact ⟨k, by simp; omega, by simp [hki]⟩)
  exact (List.getElem?_eq_some_iff.1 hkey).1

/-- The null channel gets no note set. -/
theorem createChannel_null (st : State) (slot : Slot) (keys : List Fr) :
    (createChannel P st 0 slot keys).channels 0 = some (defaultChannel slot keys none) := by
  simp [createChannel]

/-- An inscription to a channel without a note set, such as the null channel, carries no step. -/
theorem validateInscribe_no_set {E : Env} {st : State} {txh opIdFr : Fr} {m : Inscribe} {sig : Fr}
    {πs : List StepProof} {v : Option NoteSet}
    (h : validateInscribe P E st txh opIdFr m sig πs = some v)
    (hset : ∀ ch, st.channels m.channel = some ch → ch.noteSet = none)
    (hnull : st.channels m.channel = none → m.channel = 0) : m.steps = [] := by
  obtain ⟨hsome, hnone⟩ := validateInscribe_spec h
  cases hc : st.channels m.channel with
  | some ch => exact (hsome ch hc).2 (hset ch hc)
  | none => exact (hnone hc).2 (hnull hc)

end

end Mantle
