import Mantle.NoValueCreated

/-!
# The block-level steps of Mantle create no value

Block Execution (Block Construction 1.4.x) runs, besides the transactions, three steps of
Mantle: the SDP Epoch Finalization, the release of the due channel withdrawals, and the
recording of the commitment root of every note set. None of them creates value:

* **`releaseWithdrawals_value`**: a due withdrawal whose inputs are unspent consumes them and
  creates its outputs, which are worth as much (it balanced when posted); one whose inputs were
  consumed in the meantime, by a step of the channel, is dropped;
* **`finalizeDeclarations_value`**: the notes a removed declaration releases were already
  counted in `inflight`;
* `recordCmRoots_value`: recording roots moves no value.
-/

namespace Mantle

open Classical

noncomputable section

variable {H : Hash}

/-! ## Releasing channel withdrawals -/

theorem withPending_setSet (st : State) (l) (i : ℕ) (s : NoteSet) :
    (st.withPending l).setSet i s = (st.setSet i s).withPending l := rfl

theorem Inv.withPending_sub {st : State} {l l' : List (Slot × ℕ × List Fr × List Fr)}
    (I : Inv H (st.withPending l)) (h : ∀ w ∈ l', w ∈ l) : Inv H (st.withPending l') :=
  ⟨I.two_le, I.sets, I.chan, I.declNodup, I.declNote, I.declOutputs,
    fun w hw => I.pending w (h w hw)⟩

/-- One step of `release_withdrawals` keeps the invariant, with the withdrawals still pending
or still to be examined, and creates no value. -/
theorem releaseOne_spec {slot : Slot} {st : State} {pending rest : List (Slot × ℕ × List Fr × List Fr)}
    {w : Slot × ℕ × List Fr × List Fr} (I : Inv H (st.withPending (pending ++ w :: rest))) :
    let acc := releaseOne slot (st, pending) w
    Inv H (acc.1.withPending (acc.2 ++ rest)) ∧ value H acc.1 ≤ value H st ∧
      acc.1.numSets = st.numSets := by
  obtain ⟨due, j, ins, outs⟩ := w
  simp only [releaseOne]
  split_ifs with hdue hun
  · refine ⟨by simpa using I, le_rfl, rfl⟩
  · -- applied: consume the inputs in the channel set and create the outputs in the ledger set
    have hw : (due, j, ins, outs) ∈ (st.withPending (pending ++ (due, j, ins, outs) :: rest)).pendingWithdrawals := by
      simp
    obtain ⟨hj2, hjn, hnd, cs, hn, hcs, hv⟩ := I.pending _ hw
    dsimp only at hj2 hjn hnd hn hcs hv
    simp only [State.withPending_numSets, State.withPending_sets] at hjn hcs
    have hj0 : j ≠ LEDGER_SET := by simp only [LEDGER_SET]; omega
    have hi : LEDGER_SET < st.numSets := by simp only [LEDGER_SET]; omega
    have I' := I.withPending_sub (l' := pending ++ rest) (by intro x hx; simp at hx ⊢; tauto)
    obtain ⟨I2, -⟩ := I'.setSet_two (i := j) (j := LEDGER_SET) hj0 hjn hi
      ((I'.sets j hjn).spend ⟨hnd, fun nf h => ⟨hun nf h, hn.ne_zero nf h⟩⟩)
      ((I'.sets _ hi).add outs) (by simp) (by simp)
    simp only [setSet_sets_of_ne _ (Ne.symm hj0)]
    refine ⟨by simpa [withPending_setSet] using I2, ?_, by simp⟩
    have key0 := supply_spend (H := H) hn hnd hcs hun
    have key1 := supply_append_le (H := H) (st.sets LEDGER_SET).cms outs
      (st.sets LEDGER_SET).nullifiers
    have v := setsValue_setSet_two (H := H) hj0 hjn hi ((st.sets j).executeSpending ins)
      ((st.sets LEDGER_SET).executeAdding outs)
    simp only [value, inflight_setSet, setSet_pool]
    simp only [NoteSet.supply, NoteSet.executeAdding_cms, NoteSet.executeAdding_nullifiers,
      NoteSet.executeSpending_cms, NoteSet.executeSpending_nullifiers] at v
    omega
  · -- dropped: an input was consumed in the meantime
    exact ⟨I.withPending_sub (by intro x hx; simp at hx ⊢; tauto), le_rfl, rfl⟩

theorem foldl_releaseOne_spec (slot : Slot) (rest : List (Slot × ℕ × List Fr × List Fr)) :
    ∀ (st : State) (pending : List (Slot × ℕ × List Fr × List Fr)),
      Inv H (st.withPending (pending ++ rest)) →
      let acc := rest.foldl (releaseOne slot) (st, pending)
      Inv H (acc.1.withPending acc.2) ∧ value H acc.1 ≤ value H st := by
  induction rest with
  | nil =>
    intro st pending I
    simp only [List.append_nil] at I
    exact ⟨I, le_rfl⟩
  | cons w rest ih =>
    intro st pending I
    obtain ⟨I1, V1, -⟩ := releaseOne_spec (slot := slot) I
    simp only [List.foldl_cons]
    have := ih _ _ I1
    exact ⟨this.1, this.2.trans V1⟩

/-- **Releasing the due channel withdrawals creates no value.** -/
theorem releaseWithdrawals_value {st : State} (I : Inv H st) (slot : Slot) :
    Inv H (releaseWithdrawals st slot) ∧ value H (releaseWithdrawals st slot) ≤ value H st := by
  have I0 : Inv H (st.withPending ([] ++ st.pendingWithdrawals)) :=
    ⟨I.two_le, I.sets, I.chan, I.declNodup, I.declNote, I.declOutputs,
      fun w hw => I.pending w (by simpa using hw)⟩
  obtain ⟨h1, h2⟩ := foldl_releaseOne_spec (H := H) slot st.pendingWithdrawals st [] I0
  exact ⟨h1, by simpa [releaseWithdrawals, value] using h2⟩

/-! ## SDP Epoch Finalization -/

theorem inflight_filter (H : Hash) (l : List (DeclarationId × DeclarationInfo)) (p : _ → Bool) :
    (l.map fun e => listValue H e.2.withdrawOutputs).sum =
      ((l.filter p).map fun e => listValue H e.2.withdrawOutputs).sum +
      ((l.filter fun e => !p e).map fun e => listValue H e.2.withdrawOutputs).sum := by
  induction l with
  | nil => simp
  | cons e l ih =>
    by_cases he : p e <;> simp [he, ih] <;> ring

theorem foldl_add_cms (l : List (DeclarationId × DeclarationInfo)) (s : NoteSet) :
    (l.foldl (fun s e => s.executeAdding e.2.withdrawOutputs) s).cms =
      s.cms ++ l.flatMap fun e => e.2.withdrawOutputs := by
  induction l generalizing s with
  | nil => simp
  | cons e l ih => simp [ih]

theorem foldl_add_eq (l : List (DeclarationId × DeclarationInfo)) (s : NoteSet) :
    l.foldl (fun s e => s.executeAdding e.2.withdrawOutputs) s =
      s.executeAdding (l.flatMap fun e => e.2.withdrawOutputs) := by
  induction l generalizing s with
  | nil => cases s; simp [NoteSet.executeAdding]
  | cons e l ih => rw [List.foldl_cons, ih]; simp [NoteSet.executeAdding]

/-- **SDP Epoch Finalization creates no value**: the notes it releases were counted in
`inflight`. -/
theorem finalizeDeclarations_value {st : State} (I : Inv H st) (epoch : Epoch) :
    Inv H (finalizeDeclarations st epoch) ∧
      value H (finalizeDeclarations st epoch) ≤ value H st := by
  set due := (st.declarations.filter fun e => decide (IsDue epoch e)).mergeSort releaseOrder
  have hi := ledger_lt I
  have hperm : due.Perm (st.declarations.filter fun e => decide (IsDue epoch e)) :=
    List.mergeSort_perm _ _
  have hfold := foldl_add_eq due (st.sets LEDGER_SET)
  simp only [finalizeDeclarations]
  rw [hfold]
  obtain ⟨I1, -⟩ := I.setSet hi ((I.sets _ hi).add (due.flatMap fun e => e.2.withdrawOutputs))
    (by simp)
  refine ⟨⟨I1.two_le, I1.sets, I1.chan, ?_, fun e he => ?_, fun e he => ?_, I1.pending⟩, ?_⟩
  · simp only [State.withDecls_declarations]
    exact I.declNodup.sublist (List.Sublist.map Prod.fst (List.filter_sublist))
  · simp only [State.withDecls_declarations, List.mem_filter] at he
    exact I1.declNote e he.1
  · simp only [State.withDecls_declarations, List.mem_filter] at he
    exact I1.declOutputs e he.1
  · have key := supply_append_le (H := H) (st.sets LEDGER_SET).cms
      (due.flatMap fun e => e.2.withdrawOutputs) (st.sets LEDGER_SET).nullifiers
    have v := setsValue_setSet (H := H) hi
      ((st.sets LEDGER_SET).executeAdding (due.flatMap fun e => e.2.withdrawOutputs))
    have hsplit := inflight_filter H st.declarations fun e => decide (IsDue epoch e)
    have hdue : listValue H (due.flatMap fun e => e.2.withdrawOutputs) =
        ((st.declarations.filter fun e => decide (IsDue epoch e)).map
          fun e => listValue H e.2.withdrawOutputs).sum := by
      rw [listValue_flatMap]
      exact (hperm.map _).sum_eq
    simp only [value, setsValue_withDecls, State.withDecls_pool, setSet_pool]
    simp only [inflight, State.withDecls_declarations]
    simp only [NoteSet.supply, NoteSet.executeAdding_cms, NoteSet.executeAdding_nullifiers] at v
    omega

/-! ## Recording the roots -/

/-- `for note_set in ledger.sets: note_set.record_cm_root()`. -/
def recordCmRoots (H : Hash) (st : State) : State :=
  { st with sets := fun i => if i < st.numSets then (st.sets i).recordCmRoot H else st.sets i }

@[simp] theorem NoteSet.recordCmRoot_cms (s : NoteSet) : (s.recordCmRoot H).cms = s.cms := by
  simp only [NoteSet.recordCmRoot]; split_ifs <;> rfl
@[simp] theorem NoteSet.recordCmRoot_nullifiers (s : NoteSet) :
    (s.recordCmRoot H).nullifiers = s.nullifiers := by
  simp only [NoteSet.recordCmRoot]; split_ifs <;> rfl
@[simp] theorem NoteSet.recordCmRoot_imt (s : NoteSet) : (s.recordCmRoot H).imt = s.imt := by
  simp only [NoteSet.recordCmRoot]; split_ifs <;> rfl
@[simp] theorem NoteSet.recordCmRoot_buffer (s : NoteSet) :
    (s.recordCmRoot H).buffer = s.buffer := by
  simp only [NoteSet.recordCmRoot]; split_ifs <;> rfl

theorem recordCmRoots_sets (st : State) (i : ℕ) :
    (recordCmRoots H st).sets i = if i < st.numSets then (st.sets i).recordCmRoot H else st.sets i :=
  rfl

/-- Recording the roots keeps the invariant and moves no value. -/
theorem recordCmRoots_value {st : State} (I : Inv H st) :
    Inv H (recordCmRoots H st) ∧ value H (recordCmRoots H st) = value H st ∧
      ∀ i, ((recordCmRoots H st).sets i).cms = (st.sets i).cms := by
  have hcms : ∀ i, ((recordCmRoots H st).sets i).cms = (st.sets i).cms := by
    intro i; rw [recordCmRoots_sets]; split_ifs <;> simp
  have hnf : ∀ i, ((recordCmRoots H st).sets i).nullifiers = (st.sets i).nullifiers := by
    intro i; rw [recordCmRoots_sets]; split_ifs <;> simp
  refine ⟨⟨I.two_le, fun i hi => ?_, I.chan, I.declNodup, fun e he => ?_, I.declOutputs,
    fun w hw => ?_⟩, ?_, hcms⟩
  · have SI := I.sets i hi
    have e : (recordCmRoots H st).sets i = (st.sets i).recordCmRoot H := by
      rw [recordCmRoots_sets, ite_eq_left (show i < st.numSets from hi)]
    rw [e]
    exact ⟨NoteSet.windowInv_recordCmRoot SI.window, by simpa using SI.sublist,
      by simpa using SI.imt⟩
  · show e.2.serviceNote ∈ ((recordCmRoots H st).sets SDP_SET).cms
    rw [hcms]; exact I.declNote e he
  · obtain ⟨h1, h2, h3, cs, hn, hcs, hv⟩ := I.pending w hw
    exact ⟨h1, h2, h3, cs, hn, fun c hc => by
      show c ∈ ((recordCmRoots H st).sets w.2.1).cms
      rw [hcms]; exact hcs c hc, hv⟩
  · simp only [value, setsValue, inflight, NoteSet.supply, hcms, hnf]
    rfl

end

end Mantle
