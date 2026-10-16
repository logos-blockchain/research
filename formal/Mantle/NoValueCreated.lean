import Mantle.Conservation

/-!
# No Operation creates value

One theorem per Operation (`applyTransfer_spec`, …): from a state satisfying `Inv`, a valid
Operation leaves a state satisfying `Inv`, whose note sets only grew, and whose value plus what
the Operation adds to `tx_balance` is at most the value before. They combine into
`applyOp_spec`, `applyOps_spec` and **`applyTx_value`**.
-/

namespace Mantle

open Classical

noncomputable section

variable {H : Hash}

/-! ## Framing -/

theorem mem_setSet_cms {st : State} {i : ℕ} {s : NoteSet} (hgrow : (st.sets i).cms <+: s.cms)
    {j : ℕ} {c : Fr} (hc : c ∈ (st.sets j).cms) : c ∈ ((st.setSet i s).sets j).cms := by
  by_cases hj : j = i
  · subst hj; simpa using hgrow.subset hc
  · rwa [setSet_sets_of_ne _ hj]

/-- Replacing one note set by a well-formed one whose commitments extend it. -/
theorem Inv.setSet {st : State} (I : Inv H st) {i : ℕ} (hi : i < st.numSets) {s : NoteSet}
    (hs : SetInv H s) (hgrow : (st.sets i).cms <+: s.cms) :
    Inv H (st.setSet i s) ∧ Grows st (st.setSet i s) := by
  refine ⟨⟨I.two_le, fun j hj => ?_, I.chan, I.declNodup, fun e he => ?_, I.declOutputs,
    fun w hw => ?_⟩, le_rfl, fun j hj => ?_⟩
  · by_cases hji : j = i
    · subst hji; simpa using hs
    · rw [setSet_sets_of_ne _ hji]; exact I.sets j hj
  · exact mem_setSet_cms hgrow (I.declNote e he)
  · obtain ⟨h1, h2, h3, cs, hn, hcs, hv⟩ := I.pending w hw
    exact ⟨h1, h2, h3, cs, hn, fun c hc => mem_setSet_cms hgrow (hcs c hc), hv⟩
  · by_cases hji : j = i
    · subst hji; simpa using hgrow
    · rw [setSet_sets_of_ne _ hji]

theorem ledger_lt {st : State} (I : Inv H st) : LEDGER_SET < st.numSets := by
  have := I.two_le; simp only [LEDGER_SET]; omega

theorem sdp_lt {st : State} (I : Inv H st) : SDP_SET < st.numSets := by
  have := I.two_le; simp only [SDP_SET]; omega


/-! ## Helpers -/

theorem setSet_setSet (st : State) (i : ℕ) (a b : NoteSet) :
    (st.setSet i a).setSet i b = st.setSet i b := by
  simp [State.setSet]

theorem setSet_comm (st : State) {i j : ℕ} (h : i ≠ j) (a b : NoteSet) :
    (st.setSet i a).setSet j b = (st.setSet j b).setSet i a := by
  simp [State.setSet, Function.update_comm h]

theorem SetInv.extend_add {s : NoteSet} (I : SetInv H s) (outs : List Fr) :
    SetInv H ((s.extendBuffer outs).executeAdding outs) where
  window := NoteSet.windowInv_executeAdding (NoteSet.windowInv_extendBuffer I.window _) _
  sublist := by simpa using I.sublist.append_right outs
  imt := I.imt

theorem SetInv.add {s : NoteSet} (I : SetInv H s) (outs : List Fr) :
    SetInv H (s.executeAdding outs) where
  window := NoteSet.windowInv_executeAdding I.window _
  sublist := I.sublist.trans (List.sublist_append_left _ _)
  imt := I.imt

@[simp] theorem updateDecl_sets (st : State) (id : DeclarationId) (f) :
    (st.updateDecl id f).sets = st.sets := rfl
@[simp] theorem updateDecl_numSets (st : State) (id : DeclarationId) (f) :
    (st.updateDecl id f).numSets = st.numSets := rfl
@[simp] theorem updateDecl_channels (st : State) (id : DeclarationId) (f) :
    (st.updateDecl id f).channels = st.channels := rfl
@[simp] theorem updateDecl_pending (st : State) (id : DeclarationId) (f) :
    (st.updateDecl id f).pendingWithdrawals = st.pendingWithdrawals := rfl
@[simp] theorem updateDecl_pool (st : State) (id : DeclarationId) (f) :
    (st.updateDecl id f).powRewardPool = st.powRewardPool := rfl

theorem mem_of_lookup {l : List (DeclarationId × DeclarationInfo)} {k : DeclarationId}
    {v : DeclarationInfo} (h : l.lookup k = some v) : (k, v) ∈ l := by
  obtain ⟨l1, l2, rfl, -⟩ := List.lookup_eq_some_iff.1 h
  simp

theorem not_mem_keys_of_lookup {l : List (DeclarationId × DeclarationInfo)} {k : DeclarationId}
    (h : l.lookup k = none) : k ∉ l.map Prod.fst := by
  rw [List.lookup_eq_none_iff] at h
  simp only [List.mem_map, not_exists, not_and]
  intro p hp hk
  have := h p hp
  simp [hk] at this

/-- Updating the declaration `id` changes the in-flight value by the change of its released
notes. -/
theorem inflight_updateDecl {st : State} (hn : (st.declarations.map Prod.fst).Nodup)
    {id : DeclarationId} {info : DeclarationInfo} (h : st.declarations.lookup id = some info)
    (f : DeclarationInfo → DeclarationInfo) :
    inflight H (st.updateDecl id f) + listValue H info.withdrawOutputs =
      inflight H st + listValue H (f info).withdrawOutputs := by
  obtain ⟨l1, l2, hl, hl1⟩ := List.lookup_eq_some_iff.1 h
  simp only [inflight, State.updateDecl, State.withDecls_declarations, hl] at hn ⊢
  have h1 : ∀ p ∈ l1, p.1 ≠ id := by
    intro p hp hp'; have := hl1 p hp; simp [hp'] at this
  have h2 : ∀ p ∈ l2, p.1 ≠ id := by
    intro p hp hp'
    simp only [List.map_append, List.map_cons, List.nodup_append, List.nodup_cons,
      List.mem_map] at hn
    exact hn.2.1.1 ⟨p, hp, hp'⟩
  have e1 : (l1.map fun e => if e.1 = id then (e.1, f e.2) else e) = l1 := by
    conv_rhs => rw [← List.map_id l1]
    exact List.map_congr_left fun p hp => by simp [h1 p hp]
  have e2 : (l2.map fun e => if e.1 = id then (e.1, f e.2) else e) = l2 := by
    conv_rhs => rw [← List.map_id l2]
    exact List.map_congr_left fun p hp => by simp [h2 p hp]
  simp only [List.map_append, List.map_cons, e1, e2, List.sum_append, List.sum_cons,
    ↓reduceIte]
  omega

theorem inflight_updateDecl_of_outputs {st : State} {id : DeclarationId}
    {f : DeclarationInfo → DeclarationInfo} (hf : ∀ i, (f i).withdrawOutputs = i.withdrawOutputs) :
    inflight H (st.updateDecl id f) = inflight H st := by
  simp only [inflight, State.updateDecl, State.withDecls_declarations, List.map_map]
  congr 1
  apply List.map_congr_left
  intro e _
  simp only [Function.comp]
  split_ifs <;> simp [hf]

theorem Inv.updateDecl {st : State} (I : Inv H st) {id : DeclarationId}
    {f : DeclarationInfo → DeclarationInfo}
    (hnote : ∀ i, (f i).serviceNote = i.serviceNote)
    (hout : ∀ i, (i.withdrawAt = none → i.withdrawOutputs = []) →
      (f i).withdrawAt = none → (f i).withdrawOutputs = []) :
    Inv H (st.updateDecl id f) where
  two_le := I.two_le
  sets := I.sets
  chan := I.chan
  declNodup := by
    simp only [State.updateDecl, State.withDecls_declarations, List.map_map]
    convert I.declNodup using 1
    apply List.map_congr_left
    intro e _
    simp only [Function.comp]
    split_ifs <;> rfl
  declNote e he := by
    simp only [State.updateDecl, State.withDecls_declarations, List.mem_map] at he
    obtain ⟨e', he', rfl⟩ := he
    split_ifs
    · simpa [hnote] using I.declNote e' he'
    · exact I.declNote e' he'
  declOutputs e he := by
    simp only [State.updateDecl, State.withDecls_declarations, List.mem_map] at he
    obtain ⟨e', he', rfl⟩ := he
    split_ifs
    · exact hout _ (I.declOutputs e' he')
    · exact I.declOutputs e' he'
  pending := I.pending

/-! ## `TRANSFER` -/

theorem applyTransfer_spec {P : Prims} [P.ZkTransferSound] {st st' : State} {txh : Fr} {t : Transfer}
    {π : ProofBlob} {fee : ℕ} (I : Inv P.H st) (h : applyTransfer P st txh t π = some (st', fee))
    (hcap : Cap st') : Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  simp only [applyTransfer, ensure_eq_some, option_bind_eq_some, option_pure_eq,
    Option.some.injEq, Prod.mk.injEq, exists_const] at h
  obtain ⟨hsp, R, hR, hv, rfl, rfl⟩ := h
  have hi := ledger_lt I
  have SI := I.sets _ hi
  have hcap' := hcap LEDGER_SET hi
  simp only [setSet_sets_self, NoteSet.executeAdding_cms,
    NoteSet.executeSpending_cms, NoteSet.extendBuffer_cms, List.length_append] at hcap'
  obtain ⟨cs, hnames, hmem, hval⟩ :=
    ZkTransfer.consumed SI.window hR hv (SI.cap (by omega))
  have key := supply_spend_append_le (H := P.H) (cms := (st.sets LEDGER_SET).cms)
    (outs := t.outputs) (N := (st.sets LEDGER_SET).nullifiers) hnames hsp.2.1
    (fun c hc => Or.inl (SI.mem_cms (hmem c hc))) hsp.2.2.2
  obtain ⟨I', G⟩ := I.setSet hi (SI.spend_add t.outputs
    ⟨hsp.2.1, fun nf h => ⟨hsp.2.2.2 nf h, hnames.ne_zero nf h⟩⟩) (by simp)
  refine ⟨I', G, ?_⟩
  have := setsValue_setSet (H := P.H) hi
    ((((st.sets LEDGER_SET).extendBuffer t.outputs).executeSpending t.inputs).executeAdding t.outputs)
  simp only [value, inflight_setSet, setSet_pool]
  simp only [NoteSet.supply, NoteSet.executeAdding_cms, NoteSet.executeAdding_nullifiers,
    NoteSet.executeSpending_cms, NoteSet.executeSpending_nullifiers, NoteSet.extendBuffer_cms,
    NoteSet.extendBuffer_nullifiers] at this
  omega

/-! ## `CHANNEL_DEPOSIT` -/

/-- Two note sets updated at once. -/
theorem setsValue_setSet_two {st : State} {i j : ℕ} (hij : i ≠ j) (hi : i < st.numSets)
    (hj : j < st.numSets) (A B : NoteSet) :
    setsValue H ((st.setSet i A).setSet j B) + (st.sets i).supply H + (st.sets j).supply H =
      setsValue H st + A.supply H + B.supply H := by
  have v1 := setsValue_setSet (H := H) hi A
  have v2 := setsValue_setSet (H := H) (st := st.setSet i A) hj B
  rw [setSet_sets_of_ne _ (Ne.symm hij)] at v2
  omega

theorem Inv.setSet_two {st : State} (I : Inv H st) {i j : ℕ} (hij : i ≠ j) (hi : i < st.numSets)
    (hj : j < st.numSets) {A B : NoteSet} (hA : SetInv H A) (hB : SetInv H B)
    (gA : (st.sets i).cms <+: A.cms) (gB : (st.sets j).cms <+: B.cms) :
    Inv H ((st.setSet i A).setSet j B) ∧ Grows st ((st.setSet i A).setSet j B) := by
  obtain ⟨I1, G1⟩ := I.setSet hi hA gA
  obtain ⟨I2, G2⟩ := I1.setSet (i := j) hj hB (by rwa [setSet_sets_of_ne _ (Ne.symm hij)])
  exact ⟨I2, G1.trans G2⟩

theorem applyDeposit_spec {P : Prims} [P.ZkTransferSound] {st st' : State} {txh : Fr} {d : ChannelDeposit}
    {π : ProofBlob} {fee : ℕ} (I : Inv P.H st) (h : applyDeposit P st txh d π = some (st', fee))
    (hcap : Cap st') : Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  simp only [applyDeposit, ensure_eq_some, option_bind_eq_some, option_pure_eq,
    Option.some.injEq, Prod.mk.injEq, exists_const] at h
  obtain ⟨-, chan, hchan, j, hj, hsp, R, hR, hv, rfl, rfl⟩ := h
  obtain ⟨hj2, hjn⟩ := I.chan _ _ hchan j hj
  have hj0 : j ≠ LEDGER_SET := by simp only [LEDGER_SET]; omega
  have hi := ledger_lt I
  simp only [setSet_sets_of_ne _ hj0, setSet_sets_of_ne _ (Ne.symm hj0), setSet_sets_self]
    at hcap ⊢
  rw [setSet_comm _ hj0, setSet_setSet] at hcap ⊢
  have S0 := I.sets _ hi
  have Sj := I.sets _ hjn
  have hcap0 := hcap LEDGER_SET hi
  simp only [setSet_sets_of_ne _ (Ne.symm hj0), setSet_sets_self,
    NoteSet.executeSpending_cms] at hcap0
  obtain ⟨cs, hnames, hmem, hval⟩ := ZkTransfer.consumed S0.window hR hv (S0.cap hcap0)
  obtain ⟨I2, G2⟩ := I.setSet_two (Ne.symm hj0) hi hjn
    (S0.spend ⟨hsp.2.1, fun nf h => ⟨hsp.2.2.2 nf h, hnames.ne_zero nf h⟩⟩) (Sj.extend_add _)
    (by simp) (by simp)
  refine ⟨I2, G2, ?_⟩
  have key0 := supply_spend (H := P.H) hnames hsp.2.1
    (fun c hc => S0.mem_cms (hmem c hc)) hsp.2.2.2
  have keyj := supply_append_le (H := P.H) (st.sets j).cms d.outputs (st.sets j).nullifiers
  have v := setsValue_setSet_two (H := P.H) (Ne.symm hj0) hi hjn
    ((st.sets LEDGER_SET).executeSpending d.inputs)
    (((st.sets j).extendBuffer d.outputs).executeAdding d.outputs)
  simp only [value, inflight_setSet, setSet_pool]
  simp only [NoteSet.supply, NoteSet.executeAdding_cms, NoteSet.executeAdding_nullifiers,
    NoteSet.executeSpending_cms, NoteSet.executeSpending_nullifiers, NoteSet.extendBuffer_cms,
    NoteSet.extendBuffer_nullifiers] at v
  omega

/-! ## `CHANNEL_WITHDRAW` -/

theorem applyChannelWithdraw_spec {P : Prims} [P.ZkTransferSound] {E : Env} {st st' : State} {txh : Fr}
    {w : ChannelWithdraw} {π : ProofBlob} {fee : ℕ} (I : Inv P.H st)
    (h : applyChannelWithdraw P E st txh w π = some (st', fee)) (hcap : Cap st') :
    Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  simp only [applyChannelWithdraw, ensure_eq_some, option_bind_eq_some, option_pure_eq,
    Option.some.injEq, Prod.mk.injEq, exists_const] at h
  obtain ⟨chan, hchan, j, hj, hsp, R, hR, hv, rfl, rfl⟩ := h
  obtain ⟨hj2, hjn⟩ := I.chan _ _ hchan j hj
  have Sj := I.sets _ hjn
  obtain ⟨cs, hnames, hmem, hval⟩ :=
    ZkTransfer.consumed Sj.window hR hv (Sj.cap (hcap j hjn))
  refine ⟨⟨I.two_le, I.sets, I.chan, I.declNodup, I.declNote, I.declOutputs, ?_⟩,
    Grows.refl _, le_of_eq (by simp [value])⟩
  intro x hx
  simp only [State.withPending_pending] at hx
  rcases List.mem_append.1 hx with hx | hx
  · exact I.pending x hx
  · simp only [List.mem_singleton] at hx
    subst hx
    exact ⟨hj2, hjn, hsp.2.1, cs, hnames, fun c hc => Sj.mem_cms (hmem c hc), by simpa using hval⟩

/-! ## `SDP_DECLARE` -/

theorem applyDeclare_spec {P : Prims} [P.ZkTransferSound] {E : Env} {st st' : State} {txh : Fr}
    {d : DeclarationMessage} {π : ProofBlob} {sig : Fr} {fee : ℕ} (I : Inv P.H st)
    (h : applyDeclare P E st txh d π sig = some (st', fee)) (hcap : Cap st') :
    Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  simp only [applyDeclare, ensure_eq_some, option_bind_eq_some, option_pure_eq,
    Option.some.injEq, Prod.mk.injEq, exists_const] at h
  obtain ⟨R, hR, hv, -, hlook, -, hsp, -, rfl, rfl⟩ := h
  have hi := ledger_lt I
  have hs := sdp_lt I
  have h01 : LEDGER_SET ≠ SDP_SET := by simp [SDP_SET, LEDGER_SET]
  simp only [setSet_sets_of_ne _ (Ne.symm h01)] at hcap ⊢
  have S0 := I.sets _ hi
  have S1 := I.sets _ hs
  have hcap0 := hcap LEDGER_SET hi
  simp only [State.withDecls_sets, setSet_sets_of_ne _ h01, setSet_sets_self,
    NoteSet.executeSpending_cms] at hcap0
  obtain ⟨cs, hnames, hmem, hval⟩ := ZkTransfer.consumed S0.window hR hv (S0.cap hcap0)
  obtain ⟨I2, G2⟩ := I.setSet_two h01 hi hs
    (S0.spend ⟨hsp.2.1, fun nf h => ⟨hsp.2.2.2 nf h, hnames.ne_zero nf h⟩⟩) (S1.add _)
    (by simp) (by simp)
  refine ⟨⟨I2.two_le, I2.sets, I2.chan, ?_, ?_, ?_, I2.pending⟩, G2, ?_⟩
  · simp only [State.withDecls_declarations, List.map_append, List.map_cons, List.map_nil]
    rw [List.nodup_append]
    refine ⟨I2.declNodup, List.nodup_singleton _, fun a ha b hb => ?_⟩
    simp only [List.mem_singleton] at hb; subst hb
    intro hab; subst hab
    exact not_mem_keys_of_lookup hlook (by simpa using ha)
  · intro e he
    simp only [State.withDecls_declarations] at he
    rcases List.mem_append.1 he with he | he
    · exact I2.declNote e he
    · simp only [List.mem_singleton] at he; subst he
      simp
  · intro e he
    simp only [State.withDecls_declarations] at he
    rcases List.mem_append.1 he with he | he
    · exact I2.declOutputs e he
    · simp only [List.mem_singleton] at he; subst he; simp
  · have key0 := supply_spend (H := P.H) hnames hsp.2.1
      (fun c hc => S0.mem_cms (hmem c hc)) hsp.2.2.2
    have key1 := supply_append_le (H := P.H) (st.sets SDP_SET).cms
      [noteCm P.H (serviceNote P d)] (st.sets SDP_SET).nullifiers
    have v := setsValue_setSet_two (H := P.H) h01 hi hs
      ((st.sets LEDGER_SET).executeSpending d.inputs)
      ((st.sets SDP_SET).executeAdding [noteCm P.H (serviceNote P d)])
    have hcmv : listValue P.H [noteCm P.H (serviceNote P d)] = d.amount := by
      simp [listValue, cmValue_noteCm, serviceNote]
    simp only [listValue_nil, zero_add] at hval
    simp only [value, setsValue_withDecls, State.withDecls_pool, setSet_pool]
    simp only [inflight, State.withDecls_declarations, List.map_append, List.sum_append,
      List.map_cons, List.map_nil, List.sum_cons, List.sum_nil, listValue_nil, add_zero,
      setSet_declarations]
    simp only [NoteSet.supply, NoteSet.executeAdding_cms, NoteSet.executeAdding_nullifiers,
      NoteSet.executeSpending_cms, NoteSet.executeSpending_nullifiers] at v
    omega

/-! ## `SDP_WITHDRAW` -/

theorem applySdpWithdraw_spec {P : Prims} [P.ZkTransferSound] {E : Env} {st st' : State} {txh : Fr}
    {w : WithdrawMessage} {π : ProofBlob} {sig : Fr} {fee : ℕ} (I : Inv P.H st)
    (h : applySdpWithdraw P E st txh w π sig = some (st', fee)) (hcap : Cap st') :
    Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  simp only [applySdpWithdraw, ensure_eq_some, option_bind_eq_some, option_pure_eq,
    Option.some.injEq, Prod.mk.injEq, exists_const] at h
  obtain ⟨info, hlook, hwa, -, -, hnf, hv0, rfl, rfl⟩ := h
  obtain ⟨wit, hv⟩ := Prims.ZkTransferSound.sound hv0
  have hs := sdp_lt I
  have S1 := I.sets _ hs
  have hmemd := mem_of_lookup hlook
  have hnote := I.declNote _ hmemd
  have hout := I.declOutputs _ hmemd hwa
  simp only at hnote hout
  -- the input of the withdrawal is the service note of the declaration
  have hcs : ∀ c ∈ ZkTransfer.inputCms P.H wit, c = info.serviceNote := by
    intro c hc
    simp only [ZkTransfer.inputCms, List.mem_map] at hc
    obtain ⟨wi, hw, rfl⟩ := hc
    obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hw
    have hk' : k < [w.serviceNoteNf].length := by rw [← ZkTransfer.length_inputs hv]; exact hk
    obtain ⟨-, -, -, hp, hpath⟩ := ZkTransfer.input_note hv hk'
    have := mem_of_mmrRoot (l := [info.serviceNote]) (by norm_num) (noteCm_ne_zero _) hp hpath
    simpa using this
  have hnames := ZkTransfer.names hv
  obtain ⟨c, hc⟩ := List.length_eq_one_iff.1 (hnames.length_eq.symm.trans (by simp))
  have hc' : c = info.serviceNote := hcs c (by simp [hc])
  rw [hc, hc'] at hnames
  have I1 := I.updateDecl (id := w.declaration) (f := fun i =>
    { i with nonce := w.nonce, withdrawAt := some (E.currentEpoch + 2),
             withdrawOutputs := w.outputs }) (fun _ => rfl) (fun _ _ h => by simp at h)
  obtain ⟨I2, G2⟩ := I1.setSet hs (S1.spend ⟨List.nodup_singleton _, fun nf h => by
    simp only [List.mem_singleton] at h; subst h
    exact ⟨hnf, hnames.ne_zero _ (by simp)⟩⟩) (by simp)
  refine ⟨I2, G2, ?_⟩
  have key := supply_spend (H := P.H) (cms := (st.sets SDP_SET).cms)
    (N := (st.sets SDP_SET).nullifiers) hnames (List.nodup_singleton _)
    (fun c hc => by simp at hc; subst hc; exact hnote) (by simpa using hnf)
  have hval := ZkTransfer.value_eq hv
  rw [hc, hc'] at hval
  have v1 := setsValue_setSet (H := P.H) (st := st.updateDecl w.declaration fun i =>
    { i with nonce := w.nonce, withdrawAt := some (E.currentEpoch + 2),
             withdrawOutputs := w.outputs }) hs
    ((st.sets SDP_SET).executeSpending [w.serviceNoteNf])
  have v2 := inflight_updateDecl (H := P.H) I.declNodup hlook fun i =>
    { i with nonce := w.nonce, withdrawAt := some (E.currentEpoch + 2),
             withdrawOutputs := w.outputs }
  rw [hout] at v2
  simp only [value, inflight_setSet, setSet_pool, updateDecl_pool, updateDecl_sets]
  simp only [updateDecl_sets, NoteSet.supply, NoteSet.executeSpending_cms,
    NoteSet.executeSpending_nullifiers] at v1
  have hsv : setsValue P.H (st.updateDecl w.declaration fun i =>
    { i with nonce := w.nonce, withdrawAt := some (E.currentEpoch + 2),
             withdrawOutputs := w.outputs }) = setsValue P.H st := rfl
  simp only [listValue_nil] at v2 hval
  simp only [listValue_cons, listValue_nil, add_zero] at key hval
  omega

/-! ## `SDP_ACTIVE`, `PROGRAM_REGISTER`, `CLAIM_POW_REWARD` -/

theorem applyActive_spec {P : Prims} {E : Env} {st st' : State} {txh : Fr} {a : Active}
    {sig : Fr} {fee : ℕ} (I : Inv P.H st) (h : applyActive P E st txh a sig = some (st', fee)) :
    Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  simp only [applyActive, ensure_eq_some, option_bind_eq_some, option_pure_eq,
    Option.some.injEq, Prod.mk.injEq, exists_const] at h
  obtain ⟨info, -, -, -, -, rfl, rfl⟩ := h
  refine ⟨I.updateDecl (fun _ => rfl) (fun i h => h), Grows.refl _, le_of_eq ?_⟩
  have := inflight_updateDecl_of_outputs (H := P.H) (st := st) (id := a.declaration)
    (f := fun i => { i with nonce := a.nonce, active := E.currentEpoch }) (fun _ => rfl)
  simp only [value, add_zero, this, updateDecl_pool]
  rfl

theorem applyRegister_spec {P : Prims} {st st' : State} {r : ProgramRegister} {fee : ℕ}
    (I : Inv P.H st) (h : applyRegister P st r = some (st', fee)) :
    Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  simp only [applyRegister, ensure_eq_some, option_bind_eq_some, option_pure_eq,
    Option.some.injEq, Prod.mk.injEq, exists_const] at h
  obtain ⟨-, rfl, rfl⟩ := h
  split_ifs
  · exact ⟨⟨I.two_le, I.sets, I.chan, I.declNodup, I.declNote, I.declOutputs, I.pending⟩,
      Grows.refl _, le_of_eq (by simp [value])⟩
  · exact ⟨I, Grows.refl _, le_rfl⟩

theorem applyClaimPow_spec {P : Prims} {E : Env} {st st' : State} {c : ClaimPowReward}
    {fee : ℕ} (I : Inv P.H st) (h : applyClaimPow P E st c = some (st', fee)) :
    Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  simp only [applyClaimPow, ensure_eq_some, option_bind_eq_some, option_pure_eq,
    Option.some.injEq, Prod.mk.injEq, exists_const] at h
  obtain ⟨-, hpool, slot, -, -, -, -, -, rfl, rfl⟩ := h
  have hi := ledger_lt I
  have I0 : ∀ a b, Inv P.H (st.withPow a b) := fun a b =>
    ⟨I.two_le, I.sets, I.chan, I.declNodup, I.declNote, I.declOutputs, I.pending⟩
  obtain ⟨I1, G1⟩ := (I0 (st.powRewardPool - st.epochPowReward)
    (insert (P.H.zkhash [c.publicKey, c.nonce, c.blockHash, c.epochNonce]) st.powNullifiers)).setSet
    (i := LEDGER_SET) hi ((I.sets _ hi).extend_add [noteCm P.H (powNote P st c)]) (by simp)
  refine ⟨I1, G1, ?_⟩
  have key := supply_append_le (H := P.H) (st.sets LEDGER_SET).cms
    [noteCm P.H (powNote P st c)] (st.sets LEDGER_SET).nullifiers
  have v1 := setsValue_setSet (H := P.H) (st := st.withPow (st.powRewardPool - st.epochPowReward)
    (insert (P.H.zkhash [c.publicKey, c.nonce, c.blockHash, c.epochNonce]) st.powNullifiers)) hi
    (((st.sets LEDGER_SET).extendBuffer [noteCm P.H (powNote P st c)]).executeAdding
      [noteCm P.H (powNote P st c)])
  have hcmv : listValue P.H [noteCm P.H (powNote P st c)] = st.epochPowReward := by
    simp [listValue, cmValue_noteCm, powNote]
  simp only [value, inflight_setSet, setSet_pool, inflight_withPow, State.withPow_pool]
  simp only [setsValue_withPow, State.withPow_sets, NoteSet.supply, NoteSet.executeAdding_cms,
    NoteSet.executeAdding_nullifiers, NoteSet.extendBuffer_cms,
    NoteSet.extendBuffer_nullifiers] at v1
  omega

/-! ## The steps of an inscription -/

@[simp] theorem NoteSet.extendBuffer_nil (s : NoteSet) : s.extendBuffer [] = s := by
  cases s; simp [NoteSet.extendBuffer]

theorem NoteSet.extendBuffer_append (s : NoteSet) (a b : List Fr) :
    (s.extendBuffer a).extendBuffer b = s.extendBuffer (a ++ b) := by
  simp [NoteSet.extendBuffer, List.append_assoc]

@[simp] theorem NoteSet.extendBuffer_recentBlocks (s : NoteSet) (l : List Fr) :
    (s.extendBuffer l).recentBlocks = s.recentBlocks := rfl

/-- What the validation of the payments of a program step establishes. -/
theorem validatePayments_spec {P : Prims} [P.ZkTransferSound] {pid : Fr} (pays : List Payment) :
    ∀ (πs : List ProofBlob) (s : NoteSet) (nfs : Finset Fr) {s1 : NoteSet} {nfs1 : Finset Fr}
      {paid : ℕ}, s.WindowInv P.H →
      s.cms.length + s.buffer.length + (pays.flatMap (·.outputs)).length < 2 ^ 32 →
      validatePayments P pid s nfs pays πs = some (s1, nfs1, paid) →
      s1 = s.extendBuffer (pays.flatMap (·.outputs)) ∧
      nfs1 = nfs ∪ (pays.flatMap (·.inputs)).toFinset ∧
      (pays.flatMap (·.inputs)).Nodup ∧
      (∀ nf ∈ pays.flatMap (·.inputs), nf ∉ nfs ∧ nf ∉ s.nullifiers) ∧
      ∃ cs, Names P.H (pays.flatMap (·.inputs)) cs ∧
        (∀ c ∈ cs, c ∈ s.cms ∨ c ∈ s.buffer ∨ c ∈ pays.flatMap (·.outputs)) ∧
        listValue P.H cs = listValue P.H (pays.flatMap (·.outputs)) + paid := by
  induction pays with
  | nil =>
    intro πs s nfs s1 nfs1 paid _ _ h
    cases πs with
    | nil =>
      simp only [validatePayments, Option.some.injEq, Prod.mk.injEq] at h
      obtain ⟨rfl, rfl, rfl⟩ := h
      exact ⟨by simp, by simp, List.nodup_nil, by simp, [], List.Forall₂.nil, by simp, by simp⟩
    | cons _ _ => simp [validatePayments] at h
  | cons p ps ih =>
    intro πs s nfs s1 nfs1 paid W hcap h
    cases πs with
    | nil => simp [validatePayments] at h
    | cons π πs =>
      simp only [validatePayments, ensure_eq_some, option_bind_eq_some, option_pure_eq,
        Option.some.injEq, Prod.mk.injEq, exists_const] at h
      obtain ⟨hsp, hdisj, hbuf, R, hR, hv, ⟨s', nfs', paid'⟩, hrest, -, rfl, rfl, rfl⟩ := h
      simp only [List.flatMap_cons, List.length_append] at hcap
      obtain ⟨e1, e2, hnd, hfr, cs, hn, hmem, hval⟩ :=
        ih πs (s.extendBuffer p.outputs) (nfs ∪ p.inputs.toFinset)
          (NoteSet.windowInv_extendBuffer W _)
          (by simp only [NoteSet.extendBuffer_cms, NoteSet.extendBuffer_buffer,
            List.length_append]; omega) hrest
      obtain ⟨cp, hnp, hmemp, hvalp⟩ := ZkTransfer.consumed W hR hv (by omega)
      refine ⟨by rw [e1, NoteSet.extendBuffer_append]; simp, by rw [e2]; simp [Finset.union_assoc],
        ?_, ?_, cp ++ cs, hnp.append hn, ?_, ?_⟩
      · rw [List.flatMap_cons, List.nodup_append]
        refine ⟨hsp.2.1, hnd, fun a ha b hb hab => ?_⟩
        subst hab
        exact (hfr a hb).1 (Finset.mem_union_right _ (List.mem_toFinset.2 ha))
      · intro nf hnf
        rw [List.flatMap_cons, List.mem_append] at hnf
        rcases hnf with hnf | hnf
        · exact ⟨hdisj nf hnf, hsp.2.2.2 nf hnf⟩
        · have := hfr nf hnf
          exact ⟨fun h => this.1 (Finset.mem_union_left _ h), this.2⟩
      · intro c hc
        rw [List.flatMap_cons]
        rcases List.mem_append.1 hc with hc | hc
        · rcases hmemp c hc with h | h
          · exact Or.inl h
          · exact Or.inr (Or.inl (List.mem_of_mem_take h))
        · rcases hmem c hc with h | h | h
          · exact Or.inl h
          · simp only [NoteSet.extendBuffer_buffer, List.mem_append] at h
            rcases h with h | h
            · exact Or.inr (Or.inl h)
            · exact Or.inr (Or.inr (List.mem_append_left _ h))
          · exact Or.inr (Or.inr (List.mem_append_right _ h))
      · rw [List.flatMap_cons, listValue_append, listValue_append, hvalp, hval]
        ring

/-- **What the validation of the steps of an inscription establishes**: the buffer is extended
with every output, no two steps or payments consume the same note, every consumed note is
unspent, and the consumed notes, among the set, its buffer and the outputs of earlier steps,
are worth exactly the outputs. -/
theorem validateSteps_spec {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {opIdFr : Fr} {programs : Fr → Option VerificationKey}
    (steps : List Step) :
    ∀ (πs : List StepProof) (s : NoteSet) (nfs : Finset Fr) {sv : NoteSet}, s.WindowInv P.H →
      s.cms.length + s.buffer.length + (steps.flatMap Step.outs).length < 2 ^ 32 →
      validateSteps P opIdFr programs s nfs steps πs = some sv →
      sv = s.extendBuffer (steps.flatMap Step.outs) ∧
      (steps.flatMap Step.ins).Nodup ∧
      (∀ nf ∈ steps.flatMap Step.ins, nf ∉ nfs ∧ nf ∉ s.nullifiers) ∧
      ∃ cs, Names P.H (steps.flatMap Step.ins) cs ∧
        (∀ c ∈ cs, c ∈ s.cms ∨ c ∈ s.buffer ∨ c ∈ steps.flatMap Step.outs) ∧
        listValue P.H cs = listValue P.H (steps.flatMap Step.outs) := by
  induction steps with
  | nil =>
    intro πs s nfs sv _ _ h
    cases πs with
    | nil =>
      simp only [validateSteps, Option.some.injEq] at h
      subst h
      exact ⟨by simp, List.nodup_nil, by simp, [], List.Forall₂.nil, by simp, by simp⟩
    | cons _ _ => simp [validateSteps] at h
  | cons step rest ih =>
    intro πs s nfs sv W hcap h
    cases πs with
    | nil => cases step <;> simp [validateSteps] at h
    | cons sp πs =>
      cases step with
      | user u =>
        cases sp with
        | program _ _ _ _ => simp [validateSteps] at h
        | user π =>
        simp only [validateSteps, ensure_eq_some, option_bind_eq_some, exists_const] at h
        obtain ⟨hsp, hdisj, hbuf, R, hR, hv, hrest⟩ := h
        simp only [List.flatMap_cons, Step.outs, Step.ins, List.length_append] at hcap ⊢
        obtain ⟨e1, hnd, hfr, cs, hn, hmem, hval⟩ :=
          ih πs (s.extendBuffer u.outputs) (nfs ∪ u.inputs.toFinset)
            (NoteSet.windowInv_extendBuffer W _)
            (by simp only [NoteSet.extendBuffer_cms, NoteSet.extendBuffer_buffer,
              List.length_append]; omega) hrest
        obtain ⟨cp, hnp, hmemp, hvalp⟩ := ZkTransfer.consumed W hR hv (by omega)
        refine ⟨by rw [e1, NoteSet.extendBuffer_append], ?_, ?_, cp ++ cs, hnp.append hn, ?_, ?_⟩
        · rw [List.nodup_append]
          refine ⟨hsp.2.1, hnd, fun a ha b hb hab => ?_⟩
          subst hab
          exact (hfr a hb).1 (Finset.mem_union_right _ (List.mem_toFinset.2 ha))
        · intro nf hnf
          rcases List.mem_append.1 hnf with hnf | hnf
          · exact ⟨hdisj nf hnf, hsp.2.2.2 nf hnf⟩
          · have := hfr nf hnf
            exact ⟨fun h => this.1 (Finset.mem_union_left _ h), this.2⟩
        · intro c hc
          rcases List.mem_append.1 hc with hc | hc
          · rcases hmemp c hc with h | h
            · exact Or.inl h
            · exact Or.inr (Or.inl (List.mem_of_mem_take h))
          · rcases hmem c hc with h | h | h
            · exact Or.inl h
            · simp only [NoteSet.extendBuffer_buffer, List.mem_append] at h
              rcases h with h | h
              · exact Or.inr (Or.inl h)
              · exact Or.inr (Or.inr (List.mem_append_left _ h))
            · exact Or.inr (Or.inr (List.mem_append_right _ h))
        · rw [listValue_append, listValue_append, hvalp, hval]
          simp
      | program ps =>
        cases sp with
        | user _ => simp [validateSteps] at h
        | program pπs spend gπ openings =>
        simp only [validateSteps, ensure_eq_some, option_bind_eq_some, exists_const] at h
        obtain ⟨key, -, ⟨s1, nfs1, paid⟩, hpay, hspd, ⟨hnd0, hdisj⟩, -, R, hR, hv, -, -, hrest⟩ := h
        simp only [List.flatMap_cons, Step.outs, Step.ins, List.length_append] at hcap ⊢
        obtain ⟨e1, e2, hndp, hfrp, cp, hnp, hmemp, hvalp⟩ :=
          validatePayments_spec ps.payments pπs s nfs W (by omega) hpay
        subst e1 e2
        have W1 := NoteSet.windowInv_extendBuffer W (ps.payments.flatMap (·.outputs))
        obtain ⟨e3, hnd, hfr, cs, hn, hmem, hval⟩ :=
          ih πs _ _ (NoteSet.windowInv_extendBuffer W1 ps.outputs)
            (by simp only [NoteSet.extendBuffer_cms, NoteSet.extendBuffer_buffer,
              List.length_append]; omega) hrest
        -- the program spend
        obtain ⟨cps, hns, hms, hvs⟩ := ZkProgramSpend.consumed W1 hR hv
          (by simp only [NoteSet.extendBuffer_cms, NoteSet.extendBuffer_buffer,
            List.length_append]; omega)
        have hfr0 : ∀ nf ∈ ps.inputs, nf ∉ s.nullifiers := by
          intro nf hnf
          by_cases hne : ps.inputs = []
          · simp [hne] at hnf
          · rw [ite_eq_left hne] at hspd
            simpa using hspd.2.2.2 nf hnf
        refine ⟨by rw [e3, NoteSet.extendBuffer_append, NoteSet.extendBuffer_append,
            List.append_assoc], ?_, ?_, cp ++ cps ++ cs,
          (hnp.append hns).append hn, ?_, ?_⟩
        · rw [List.append_assoc, List.nodup_append, List.nodup_append]
          refine ⟨hndp, ⟨hnd0, hnd, fun a ha b hb hab => ?_⟩, fun a ha b hb hab => ?_⟩
          · subst hab
            exact (hfr a hb).1 (Finset.mem_union_right _ (List.mem_toFinset.2 ha))
          · subst hab
            rcases List.mem_append.1 hb with hb | hb
            · exact hdisj a hb (Finset.mem_union_right _ (List.mem_toFinset.2 ha))
            · exact (hfr a hb).1 (Finset.mem_union_left _
                (Finset.mem_union_right _ (List.mem_toFinset.2 ha)))
        · intro nf hnf
          simp only [List.mem_append] at hnf
          rcases hnf with (hnf | hnf) | hnf
          · exact hfrp nf hnf
          · exact ⟨fun h => hdisj nf hnf (Finset.mem_union_left _ h), hfr0 nf hnf⟩
          · have := hfr nf hnf
            exact ⟨fun h => this.1 (Finset.mem_union_left _ (Finset.mem_union_left _ h)),
              by simpa using this.2⟩
        · intro c hc
          simp only [List.mem_append] at hc
          rcases hc with (hc | hc) | hc
          · rcases hmemp c hc with h | h | h
            · exact Or.inl h
            · exact Or.inr (Or.inl h)
            · exact Or.inr (Or.inr (by simp [h]))
          · rcases hms c hc with h | h
            · exact Or.inl h
            · have h := List.mem_of_mem_take h
              simp only [NoteSet.extendBuffer_buffer, List.mem_append] at h
              rcases h with h | h
              · exact Or.inr (Or.inl h)
              · exact Or.inr (Or.inr (by simp [h]))
          · rcases hmem c hc with h | h | h
            · exact Or.inl h
            · simp only [NoteSet.extendBuffer_buffer, List.mem_append] at h
              rcases h with (h | h) | h
              · exact Or.inr (Or.inl h)
              · exact Or.inr (Or.inr (by simp [h]))
              · exact Or.inr (Or.inr (by simp [h]))
            · exact Or.inr (Or.inr (by simp [h]))
        · simp only [listValue_append] at hvalp hval ⊢
          dsimp only at hvs
          omega

/-! ## Executing steps -/

theorem executePayments_fields (pays : List Payment) : ∀ s : NoteSet,
    (pays.foldl executePayment s).cms = s.cms ++ pays.flatMap (·.outputs) ∧
    (pays.foldl executePayment s).nullifiers = s.nullifiers ∪ (pays.flatMap (·.inputs)).toFinset ∧
    (pays.foldl executePayment s).buffer = s.buffer ∧
    (pays.foldl executePayment s).recentRoots = s.recentRoots ∧
    (pays.foldl executePayment s).recentBlocks = s.recentBlocks ∧
    (pays.foldl executePayment s).imt =
      (pays.flatMap (·.inputs)).foldl IMT.insertNullifier s.imt := by
  induction pays with
  | nil => intro s; simp
  | cons p ps ih =>
    intro s
    obtain ⟨h1, h2, h3, h4, h5, h6⟩ := ih (executePayment s p)
    simp only [List.foldl_cons, h1, h2, h3, h4, h5, h6, List.flatMap_cons, List.toFinset_append,
      List.foldl_append]
    refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
      simp [executePayment, Finset.union_assoc, NoteSet.executeSpending,
        NoteSet.executeAdding]

theorem executeSteps_fields (steps : List Step) : ∀ s : NoteSet,
    (executeSteps s steps).cms = s.cms ++ steps.flatMap Step.outs ∧
    (executeSteps s steps).nullifiers = s.nullifiers ∪ (steps.flatMap Step.ins).toFinset ∧
    (executeSteps s steps).buffer = s.buffer ∧
    (executeSteps s steps).recentRoots = s.recentRoots ∧
    (executeSteps s steps).recentBlocks = s.recentBlocks ∧
    (executeSteps s steps).imt = (steps.flatMap Step.ins).foldl IMT.insertNullifier s.imt := by
  induction steps with
  | nil => intro s; simp [executeSteps]
  | cons st rest ih =>
    intro s
    have e : executeSteps s (st :: rest) = executeSteps (executeStep s st) rest := rfl
    obtain ⟨h1, h2, h3, h4, h5, h6⟩ := ih (executeStep s st)
    rw [e, h1, h2, h3, h4, h5, h6]
    cases st with
    | user u =>
      refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
        simp [executeStep, Step.outs, Step.ins, Finset.union_assoc, List.foldl_append,
          NoteSet.executeSpending, NoteSet.executeAdding]
    | program ps =>
      obtain ⟨p1, p2, p3, p4, p5, p6⟩ := executePayments_fields ps.payments s
      simp only [executeStep, NoteSet.executeAdding_cms, NoteSet.executeSpending_cms, p1,
        NoteSet.executeAdding_nullifiers, NoteSet.executeSpending_nullifiers, p2,
        NoteSet.executeAdding_buffer, NoteSet.executeSpending_buffer, p3, List.flatMap_cons,
        Step.outs, Step.ins, List.append_assoc, List.toFinset_append, Finset.union_assoc,
        List.foldl_append]
      refine ⟨by simp, by simp, by simp, p4, p5, ?_⟩
      simp only [NoteSet.executeAdding, NoteSet.executeSpending, p6]

theorem NoteSet.WindowInv.of_grow {s s' : NoteSet} (W : s.WindowInv H)
    (hr : s'.recentRoots = s.recentRoots) (hb : s'.recentBlocks = s.recentBlocks)
    (hc : s.cms <+: s'.cms) : s'.WindowInv H where
  keys r := by rw [hr, hb]; exact W.keys r
  length_le := by rw [hb]; exact W.length_le
  isPrefix r p h := by
    rw [hr] at h
    obtain ⟨k, hk, hp, hr'⟩ := W.isPrefix r p h
    obtain ⟨t, ht⟩ := hc
    refine ⟨k, by rw [← ht]; simp; omega, ?_, hr'⟩
    rw [hp, ← ht, List.take_append_of_le_length hk]

/-- Executing validated steps keeps the note set well formed. -/
theorem SetInv.executeSteps {s : NoteSet} (I : SetInv H s) (steps : List Step)
    (hf : Fresh s (steps.flatMap Step.ins)) :
    SetInv H (Mantle.executeSteps (s.extendBuffer (steps.flatMap Step.outs)) steps) := by
  obtain ⟨h1, h2, h3, h4, h5, h6⟩ :=
    executeSteps_fields steps (s.extendBuffer (steps.flatMap Step.outs))
  refine ⟨I.window.of_grow (by rw [h4]; rfl) (by rw [h5]; rfl) (by rw [h1]; simp), ?_, ?_⟩
  · rw [h1, h3]
    simpa using I.sublist.append_right (steps.flatMap Step.outs)
  · rw [h2, h6]
    exact IMT.inv_foldl _ _ _ I.imt hf.1 hf.2

/-! ## Creating a channel -/

theorem setsValue_addSet (st : State) (s : NoteSet) :
    setsValue H (st.addSet s) = setsValue H st + s.supply H := by
  simp only [setsValue, State.addSet_numSets, State.addSet_sets, Finset.sum_range_succ,
    Function.update_self]
  congr 1
  apply Finset.sum_congr rfl
  intro j hj
  rw [Function.update_of_ne (Finset.mem_range.1 hj).ne]

theorem supply_empty : (NoteSet.empty H).supply H = 0 := by
  simp only [NoteSet.supply, supply, NoteSet.empty, List.toFinset_nil]
  exact Finset.sum_eq_zero (fun i hi => absurd (Finset.mem_filter.1 hi).1 (Finset.notMem_empty _))

/-- Changing the channels, keeping their note sets in range. -/
theorem Inv.withChannels {st : State} (I : Inv H st) (f : ChannelId → Option ChannelState)
    (hf : ∀ c ch, f c = some ch → ∀ j, ch.noteSet = some j → 2 ≤ j ∧ j < st.numSets) :
    Inv H (st.withChannels f) :=
  ⟨I.two_le, I.sets, hf, I.declNodup, I.declNote, I.declOutputs, I.pending⟩

/-- Updating one channel without changing its note set. -/
theorem Inv.updateChannel {st : State} (I : Inv H st) {id : ChannelId} {ch ch' : ChannelState}
    (hc : st.channels id = some ch) (hn : ch'.noteSet = ch.noteSet) :
    Inv H (st.withChannels (Function.update st.channels id (some ch'))) := by
  apply I.withChannels
  intro c x hx j hj
  by_cases hcid : c = id
  · subst hcid
    simp only [Function.update_self, Option.some.injEq] at hx
    subst hx
    exact I.chan _ _ hc j (hn ▸ hj)
  · rw [Function.update_of_ne hcid] at hx
    exact I.chan _ _ hx j hj

theorem createChannel_spec {P : Prims} {st : State} (I : Inv P.H st) (id : ChannelId)
    (slot : Slot) (keys : List Fr) :
    Inv P.H (createChannel P st id slot keys) ∧ Grows st (createChannel P st id slot keys) ∧
      value P.H (createChannel P st id slot keys) = value P.H st ∧
      (createChannel P st id slot keys).channels id =
        some (defaultChannel slot keys (if id = 0 then none else some st.numSets)) := by
  unfold createChannel
  split_ifs with h0
  · refine ⟨I.withChannels _ ?_, Grows.refl _, by simp [value], by simp⟩
    intro c ch hch j hj
    by_cases hc : c = id
    · subst hc; simp only [Function.update_self, Option.some.injEq] at hch
      subst hch; simp [defaultChannel] at hj
    · rw [Function.update_of_ne hc] at hch; exact I.chan _ _ hch j hj
  · have I1 : Inv P.H (st.addSet (NoteSet.empty P.H)) := by
      refine ⟨by simp; have := I.two_le; omega, fun j hj => ?_, fun c ch hch j hj => ?_,
        I.declNodup, fun e he => ?_, I.declOutputs, fun w hw => ?_⟩
      · simp only [State.addSet_numSets] at hj
        simp only [State.addSet_sets]
        by_cases hjn : j = st.numSets
        · subst hjn; simpa using SetInv.empty
        · rw [Function.update_of_ne hjn]; exact I.sets j (by omega)
      · have := I.chan c ch hch j hj; simp; omega
      · simp only [State.addSet_sets]
        rw [Function.update_of_ne (sdp_lt I).ne]
        exact I.declNote e he
      · obtain ⟨h1, h2, h3, cs, hn, hcs, hv⟩ := I.pending w hw
        refine ⟨h1, by simp; omega, h3, cs, hn, fun c hc => ?_, hv⟩
        simp only [State.addSet_sets]
        rw [Function.update_of_ne h2.ne]
        exact hcs c hc
    refine ⟨I1.withChannels _ ?_, ⟨by simp, fun i hi => ?_⟩, ?_, by simp⟩
    · intro c ch hch j hj
      by_cases hc : c = id
      · subst hc; simp only [Function.update_self, Option.some.injEq] at hch
        subst hch; simp only [defaultChannel, Option.some.injEq] at hj
        subst hj; simp; have := I.two_le; omega
      · rw [Function.update_of_ne hc] at hch
        have := I.chan _ _ hch j hj; simp; omega
    · simp only [State.withChannels_sets, State.addSet_sets]
      rw [Function.update_of_ne hi.ne]
    · simp only [value, setsValue_withChannels, inflight_withChannels, State.withChannels_pool,
        setsValue_addSet, inflight_addSet, State.addSet_pool, supply_empty, add_zero]

/-! ## `CHANNEL_INSCRIBE` -/

theorem validatePayments_eq {P : Prims} {pid : Fr} (pays : List Payment) :
    ∀ (πs : List ProofBlob) (s : NoteSet) (nfs : Finset Fr) {s1 : NoteSet} {nfs1 : Finset Fr}
      {paid : ℕ}, validatePayments P pid s nfs pays πs = some (s1, nfs1, paid) →
      s1 = s.extendBuffer (pays.flatMap (·.outputs)) := by
  induction pays with
  | nil =>
    intro πs s nfs s1 nfs1 paid h
    cases πs with
    | nil => simp only [validatePayments, Option.some.injEq, Prod.mk.injEq] at h; simp [h.1]
    | cons _ _ => simp [validatePayments] at h
  | cons p ps ih =>
    intro πs s nfs s1 nfs1 paid h
    cases πs with
    | nil => simp [validatePayments] at h
    | cons π πs =>
      simp only [validatePayments, ensure_eq_some, option_bind_eq_some, option_pure_eq,
        Option.some.injEq, Prod.mk.injEq, exists_const] at h
      obtain ⟨-, -, -, R, -, -, ⟨s', nfs', paid'⟩, hrest, -, rfl, rfl, rfl⟩ := h
      rw [ih πs _ _ hrest, NoteSet.extendBuffer_append, List.flatMap_cons]

theorem validateSteps_eq {P : Prims} {opIdFr : Fr} {programs : Fr → Option VerificationKey}
    (steps : List Step) :
    ∀ (πs : List StepProof) (s : NoteSet) (nfs : Finset Fr) {sv : NoteSet},
      validateSteps P opIdFr programs s nfs steps πs = some sv →
      sv = s.extendBuffer (steps.flatMap Step.outs) := by
  induction steps with
  | nil =>
    intro πs s nfs sv h
    cases πs with
    | nil => simp only [validateSteps, Option.some.injEq] at h; simp [h]
    | cons _ _ => simp [validateSteps] at h
  | cons step rest ih =>
    intro πs s nfs sv h
    cases πs with
    | nil => cases step <;> simp [validateSteps] at h
    | cons sp πs =>
      cases step with
      | user u =>
        cases sp with
        | program _ _ _ _ => simp [validateSteps] at h
        | user π =>
          simp only [validateSteps, ensure_eq_some, option_bind_eq_some, exists_const] at h
          obtain ⟨-, -, -, R, -, -, hrest⟩ := h
          rw [ih πs _ _ hrest, NoteSet.extendBuffer_append, List.flatMap_cons, Step.outs]
      | program ps =>
        cases sp with
        | user _ => simp [validateSteps] at h
        | program pπs spend gπ openings =>
          simp only [validateSteps, ensure_eq_some, option_bind_eq_some, exists_const] at h
          obtain ⟨key, -, ⟨s1, nfs1, paid⟩, hpay, -, -, -, R, -, -, -, -, hrest⟩ := h
          rw [ih πs _ _ hrest, validatePayments_eq ps.payments pπs s nfs hpay,
            NoteSet.extendBuffer_append, NoteSet.extendBuffer_append, List.flatMap_cons,
            Step.outs, List.append_assoc]

/-- What the validation of an inscription establishes about its steps. -/
theorem validateInscribe_spec {P : Prims} {E : Env} {st : State} {txh opIdFr : Fr}
    {m : Inscribe} {sig : Fr} {πs : List StepProof} {v : Option NoteSet}
    (h : validateInscribe P E st txh opIdFr m sig πs = some v) :
    (∀ chan, st.channels m.channel = some chan →
      (∀ j, chan.noteSet = some j →
        ∃ sv, v = some sv ∧ validateSteps P opIdFr st.programs (st.sets j) ∅ m.steps πs = some sv) ∧
      (chan.noteSet = none → m.steps = [])) ∧
    (st.channels m.channel = none →
      (m.channel ≠ 0 →
        ∃ sv, validateSteps P opIdFr st.programs (NoteSet.empty P.H) ∅ m.steps πs = some sv) ∧
      (m.channel = 0 → m.steps = [])) := by
  unfold validateInscribe at h
  simp only [ensure_eq_some, option_bind_eq_some, option_pure_eq, exists_const] at h
  obtain ⟨-, h⟩ := h
  cases hc : st.channels m.channel with
  | none =>
    simp only [hc, ensure_eq_some, option_bind_eq_some, exists_const, Option.some.injEq] at h
    obtain ⟨-, a, rfl, -, hns, -, hv⟩ := h
    refine ⟨fun chan h => by simp at h, fun _ => ⟨fun h0 => ?_, fun h0 => ?_⟩⟩
    · rw [ite_eq_left h0] at hv
      obtain ⟨sv, hsv, -⟩ := Option.map_eq_some_iff.1 hv
      exact ⟨sv, hsv⟩
    · simpa [h0] using hns
  | some chan =>
    simp only [hc, ensure_eq_some, option_bind_eq_some, exists_const, Option.some.injEq] at h
    obtain ⟨-, -, a, rfl, -, hns, -, hv⟩ := h
    refine ⟨fun chan' h' => ?_, fun h => by simp at h⟩
    simp only [Option.some.injEq] at h'
    subst h'
    refine ⟨fun j hj => ?_, fun hj => by simpa [hj] using hns⟩
    simp only [hj, Option.map_some] at hv
    obtain ⟨sv, hsv, rfl⟩ := Option.map_eq_some_iff.1 hv
    exact ⟨sv, rfl, hsv⟩

@[simp] theorem NoteSet.empty_cms (H : Hash) : (NoteSet.empty H).cms = [] := rfl
@[simp] theorem NoteSet.empty_nullifiers (H : Hash) : (NoteSet.empty H).nullifiers = ∅ := rfl
@[simp] theorem NoteSet.empty_buffer (H : Hash) : (NoteSet.empty H).buffer = [] := rfl

theorem createChannel_sets_new {P : Prims} {st : State} {id : ChannelId} (h0 : id ≠ 0)
    (slot : Slot) (keys : List Fr) :
    (createChannel P st id slot keys).sets st.numSets = NoteSet.empty P.H ∧
      (createChannel P st id slot keys).numSets = st.numSets + 1 := by
  simp [createChannel, h0]

/-- The steps an inscription applies never create value. -/
theorem executeInscribeSteps_spec {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {E : Env} {st : State} {txh opIdFr : Fr}
    {m : Inscribe} {sig : Fr} {πs : List StepProof} {v : Option NoteSet} (I : Inv P.H st)
    (h : validateInscribe P E st txh opIdFr m sig πs = some v)
    (hcap : Cap (executeInscribeSteps P E st m v)) :
    Inv P.H (executeInscribeSteps P E st m v) ∧ Grows st (executeInscribeSteps P E st m v) ∧
      value P.H (executeInscribeSteps P E st m v) ≤ value P.H st := by
  obtain ⟨hsome, hnone⟩ := validateInscribe_spec h
  unfold executeInscribeSteps at hcap ⊢
  cases hc : st.channels m.channel with
  | some chan =>
    simp only [hc] at hcap ⊢
    obtain ⟨h1, -⟩ := hsome chan hc
    cases hj : chan.noteSet with
    | none => exact ⟨I, Grows.refl _, le_rfl⟩
    | some j =>
      obtain ⟨sv, rfl, hsv⟩ := h1 j hj
      simp only [hj] at hcap ⊢
      obtain ⟨hj2, hjn⟩ := I.chan _ _ hc j hj
      have SJ := I.sets j hjn
      have esv := validateSteps_eq m.steps πs _ _ hsv
      subst esv
      obtain ⟨f1, f2, -, -, -, -⟩ := executeSteps_fields m.steps
        ((st.sets j).extendBuffer (m.steps.flatMap Step.outs))
      have hcj := hcap j hjn
      simp only [setSet_sets_self, f1, NoteSet.extendBuffer_cms, List.length_append] at hcj
      have hbl := SJ.sublist.length_le
      obtain ⟨-, hnd, hfr, cs, hn, hmem, hval⟩ :=
        validateSteps_spec m.steps πs (st.sets j) ∅ SJ.window (by omega) hsv
      have key := supply_spend_append_le (H := P.H) hn hnd
        (fun c hc => by
          rcases hmem c hc with h | h | h
          · exact Or.inl h
          · exact Or.inl (SJ.sublist.subset h)
          · exact Or.inr h)
        (fun nf hnf => (hfr nf hnf).2)
      obtain ⟨I', G'⟩ := I.setSet hjn
        (SJ.executeSteps m.steps ⟨hnd, fun nf h => ⟨(hfr nf h).2, hn.ne_zero nf h⟩⟩)
        (by rw [f1]; simp)
      refine ⟨I', G', ?_⟩
      have v1 := setsValue_setSet (H := P.H) hjn
        (executeSteps ((st.sets j).extendBuffer (m.steps.flatMap Step.outs)) m.steps)
      simp only [NoteSet.supply, f1, f2, NoteSet.extendBuffer_cms,
        NoteSet.extendBuffer_nullifiers] at v1
      simp only [value, inflight_setSet, setSet_pool]
      omega
  | none =>
    simp only [hc] at hcap ⊢
    obtain ⟨h1, h2⟩ := hnone hc
    obtain ⟨Ic, Gc, Vc, -⟩ := createChannel_spec I m.channel E.blockSlot [m.signer]
    by_cases h0 : m.channel = 0
    · simp only [h0, ne_eq, not_true_eq_false, ite_false] at hcap ⊢
      rw [h0] at Ic Gc Vc
      exact ⟨Ic, Gc, Vc.le⟩
    · simp only [ne_eq, h0, not_false_eq_true, ite_true] at hcap ⊢
      obtain ⟨sv, hsv⟩ := h1 h0
      obtain ⟨es, en⟩ := createChannel_sets_new (P := P) (st := st) h0 E.blockSlot [m.signer]
      rw [es] at hcap ⊢
      have hlt : st.numSets < (createChannel P st m.channel E.blockSlot [m.signer]).numSets := by
        rw [en]; omega
      obtain ⟨f1, f2, f3, f4, f5, f6⟩ := executeSteps_fields m.steps (NoteSet.empty P.H)
      have hcj := hcap st.numSets hlt
      simp only [setSet_sets_self, f1, List.length_append, NoteSet.empty_cms,
        List.length_nil] at hcj
      have W0 : (NoteSet.empty P.H).WindowInv P.H := NoteSet.windowInv_empty
      obtain ⟨-, hnd, hfr, cs, hn, hmem, hval⟩ :=
        validateSteps_spec m.steps πs (NoteSet.empty P.H) ∅ W0
          (by simp only [NoteSet.empty_cms, NoteSet.empty_buffer, List.length_nil]; omega) hsv
      have key := supply_spend_append_le (H := P.H) (cms := []) (N := ∅) hn hnd
        (fun c hc => by
          rcases hmem c hc with h | h | h
          · simp [NoteSet.empty] at h
          · simp [NoteSet.empty] at h
          · exact Or.inr h)
        (by simp)
      have SE : SetInv P.H (executeSteps (NoteSet.empty P.H) m.steps) :=
        ⟨W0.of_grow f4 f5 (by rw [f1]; simp [NoteSet.empty]), by
          rw [f3, f1]; simp [NoteSet.empty], by
          rw [f2, f6]
          exact IMT.inv_foldl _ _ _ IMT.inv_init hnd fun nf h =>
            ⟨by simp, hn.ne_zero nf h⟩⟩
      obtain ⟨I', G'⟩ := Ic.setSet hlt SE (by rw [es, f1]; simp [NoteSet.empty])
      refine ⟨I', Gc.trans G', ?_⟩
      have v1 := setsValue_setSet (H := P.H) hlt (executeSteps (NoteSet.empty P.H) m.steps)
      rw [es, supply_empty] at v1
      have hsE : (executeSteps (NoteSet.empty P.H) m.steps).supply P.H = 0 := by
        have hz : supply P.H [] ∅ = 0 := by
          simp only [supply, List.toFinset_nil]
          exact Finset.sum_eq_zero fun i hi => absurd (Finset.mem_filter.1 hi).1
            (Finset.notMem_empty _)
        simp only [NoteSet.supply, f1, f2, NoteSet.empty_cms, NoteSet.empty_nullifiers,
          List.nil_append, Finset.empty_union] at key ⊢
        omega
      simp only [value, inflight_setSet, setSet_pool]
      simp only [value] at Vc
      omega

theorem applyInscribe_spec {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {E : Env} {st st' : State} {txh opIdFr : Fr}
    {m : Inscribe} {sig : Fr} {πs : List StepProof} {fee : ℕ} (I : Inv P.H st)
    (h : applyInscribe P E st txh opIdFr m sig πs = some (st', fee)) (hcap : Cap st') :
    Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  unfold applyInscribe at h
  simp only [option_bind_eq_some, option_pure_eq, Option.some.injEq, Prod.mk.injEq] at h
  obtain ⟨v, hv, chan, hchan, rfl, rfl⟩ := h
  obtain ⟨I1, G1, V1⟩ := executeInscribeSteps_spec I hv hcap
  exact ⟨I1.updateChannel hchan rfl, G1, by simpa [value] using V1⟩

/-! ## `CHANNEL_CONFIG` -/

theorem applyConfig_spec {P : Prims} {E : Env} {st st' : State} {txh : Fr} {c : ChannelConfig}
    {sigs : List Fr} {idx : List ℕ} {fee : ℕ} (I : Inv P.H st)
    (h : applyConfig P E st txh c sigs idx = some (st', fee)) :
    Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  unfold applyConfig at h
  simp only [ensure_eq_some, option_bind_eq_some, option_pure_eq, exists_const] at h
  obtain ⟨-, -, -, h⟩ := h
  cases hc : st.channels c.channel with
  | none =>
    simp only [hc, ensure_eq_some, option_bind_eq_some, exists_const,
      Option.some.injEq, Prod.mk.injEq, Option.isSome_none, Bool.false_eq_true, ite_false] at h
    obtain ⟨-, -, chan, hchan, rfl, rfl⟩ := h
    obtain ⟨Ic, Gc, Vc, -⟩ := createChannel_spec I c.channel E.blockSlot c.keys
    exact ⟨Ic.updateChannel hchan rfl, Gc, by simpa [value] using Vc.le⟩
  | some ch =>
    simp only [hc, ensure_eq_some, option_bind_eq_some, exists_const,
      Option.some.injEq, Prod.mk.injEq, Option.isSome_some, ite_true] at h
    obtain ⟨-, -, chan, hchan, rfl, rfl⟩ := h
    subst hchan
    exact ⟨I.updateChannel hc rfl, Grows.refl _, by simp [value]⟩

/-! ## Operations and transactions -/

/-- **No Operation creates value.** -/
theorem applyOp_spec {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {E : Env} {st st' : State} {txh : Fr} {op : Op}
    {π : OpProof} {fee : ℕ} (I : Inv P.H st) (h : applyOp P E st txh op π = some (st', fee))
    (hcap : Cap st') : Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fee ≤ value P.H st := by
  cases op <;> cases π <;> simp only [applyOp, reduceCtorEq] at h
  · exact applyTransfer_spec I h hcap
  · exact applyRegister_spec I h
  · exact applyConfig_spec I h
  · exact applyInscribe_spec I h hcap
  · exact applyDeposit_spec I h hcap
  · exact applyChannelWithdraw_spec I h hcap
  · exact applyDeclare_spec I h hcap
  · exact applySdpWithdraw_spec I h hcap
  · exact applyActive_spec I h
  · exact applyClaimPow_spec I h

/-! ### Note sets only grow -/

theorem Grows.setSet {st : State} {i : ℕ} {s : NoteSet}
    (h : i < st.numSets → (st.sets i).cms <+: s.cms) : Grows st (st.setSet i s) := by
  refine ⟨le_rfl, fun j hj => ?_⟩
  by_cases hji : j = i
  · subst hji; simpa using h hj
  · rw [setSet_sets_of_ne _ hji]

theorem Grows.of_sets {st st' : State} (h1 : st'.sets = st.sets) (h2 : st'.numSets = st.numSets) :
    Grows st st' := ⟨h2.ge, fun i _ => by rw [h1]⟩

theorem createChannel_grows (P : Prims) (st : State) (id : ChannelId) (slot : Slot)
    (keys : List Fr) : Grows st (createChannel P st id slot keys) := by
  unfold createChannel
  split_ifs
  · exact Grows.of_sets rfl rfl
  · refine ⟨by simp, fun i hi => ?_⟩
    simp only [State.withChannels_sets, State.addSet_sets]
    rw [Function.update_of_ne hi.ne]

theorem executeInscribeSteps_grows {P : Prims} {E : Env} {st : State} {txh opIdFr : Fr}
    {m : Inscribe} {sig : Fr} {πs : List StepProof} {v : Option NoteSet}
    (h : validateInscribe P E st txh opIdFr m sig πs = some v) :
    Grows st (executeInscribeSteps P E st m v) := by
  obtain ⟨hsome, -⟩ := validateInscribe_spec h
  unfold executeInscribeSteps
  cases hc : st.channels m.channel with
  | some chan =>
    simp only
    cases hj : chan.noteSet with
    | none => exact Grows.refl _
    | some j =>
      obtain ⟨sv, rfl, hsv⟩ := (hsome chan hc).1 j hj
      apply Grows.setSet
      intro _
      rw [(executeSteps_fields m.steps sv).1, validateSteps_eq m.steps πs _ _ hsv]
      simp
  | none =>
    simp only
    split_ifs
    · refine (createChannel_grows P st m.channel E.blockSlot [m.signer]).trans (Grows.setSet ?_)
      intro _
      rw [(executeSteps_fields m.steps _).1]
      exact List.prefix_append _ _
    · exact createChannel_grows P st m.channel E.blockSlot [m.signer]

/-- Every Operation only appends commitments to the note sets, and only adds note sets. -/
theorem applyOp_grows {P : Prims} {E : Env} {st st' : State} {txh : Fr} {op : Op}
    {π : OpProof} {fee : ℕ} (h : applyOp P E st txh op π = some (st', fee)) : Grows st st' := by
  cases op <;> cases π <;> simp only [applyOp, reduceCtorEq] at h
  · simp only [applyTransfer, ensure_eq_some, option_bind_eq_some, option_pure_eq,
      Option.some.injEq, Prod.mk.injEq, exists_const] at h
    obtain ⟨-, R, -, -, rfl, rfl⟩ := h
    exact Grows.setSet fun _ => by simp
  · simp only [applyRegister, ensure_eq_some, option_bind_eq_some, option_pure_eq,
      Option.some.injEq, Prod.mk.injEq, exists_const] at h
    obtain ⟨-, rfl, rfl⟩ := h
    split_ifs <;> exact Grows.of_sets rfl rfl
  · rename_i c sigs idx
    unfold applyConfig at h
    simp only [ensure_eq_some, option_bind_eq_some, option_pure_eq, exists_const] at h
    obtain ⟨-, -, -, h⟩ := h
    cases hc : st.channels c.channel with
    | none =>
      simp only [hc, ensure_eq_some, option_bind_eq_some, exists_const,
        Option.some.injEq, Prod.mk.injEq, Option.isSome_none, Bool.false_eq_true, ite_false] at h
      obtain ⟨-, -, chan, -, rfl, rfl⟩ := h
      exact (createChannel_grows P st _ _ _).trans (Grows.of_sets rfl rfl)
    | some ch =>
      simp only [hc, ensure_eq_some, option_bind_eq_some, exists_const,
        Option.some.injEq, Prod.mk.injEq, Option.isSome_some, ite_true] at h
      obtain ⟨-, -, chan, -, rfl, rfl⟩ := h
      exact Grows.of_sets rfl rfl
  · unfold applyInscribe at h
    simp only [option_bind_eq_some, option_pure_eq, Option.some.injEq, Prod.mk.injEq] at h
    obtain ⟨v, hv, chan, -, rfl, rfl⟩ := h
    exact (executeInscribeSteps_grows hv).trans (Grows.of_sets rfl rfl)
  · simp only [applyDeposit, ensure_eq_some, option_bind_eq_some, option_pure_eq,
      Option.some.injEq, Prod.mk.injEq, exists_const] at h
    obtain ⟨-, chan, -, j, -, -, R, -, -, rfl, rfl⟩ := h
    refine ((Grows.setSet fun _ => by simp).trans (Grows.setSet fun _ => by simp)).trans
      (Grows.setSet fun _ => ?_)
    by_cases hj : j = LEDGER_SET
    · subst hj; simp
    · simp [setSet_sets_of_ne _ hj]
  · simp only [applyChannelWithdraw, ensure_eq_some, option_bind_eq_some, option_pure_eq,
      Option.some.injEq, Prod.mk.injEq, exists_const] at h
    obtain ⟨chan, -, j, -, -, R, -, -, rfl, rfl⟩ := h
    exact Grows.of_sets rfl rfl
  · simp only [applyDeclare, ensure_eq_some, option_bind_eq_some, option_pure_eq,
      Option.some.injEq, Prod.mk.injEq, exists_const] at h
    obtain ⟨R, -, -, -, -, -, -, -, rfl, rfl⟩ := h
    exact ((Grows.setSet fun _ => by simp).trans (Grows.setSet fun _ => by simp)).trans
      (Grows.of_sets rfl rfl)
  · simp only [applySdpWithdraw, ensure_eq_some, option_bind_eq_some, option_pure_eq,
      Option.some.injEq, Prod.mk.injEq, exists_const] at h
    obtain ⟨info, -, -, -, -, -, -, rfl, rfl⟩ := h
    exact (Grows.of_sets rfl rfl).trans (Grows.setSet fun _ => by simp)
  · simp only [applyActive, ensure_eq_some, option_bind_eq_some, option_pure_eq,
      Option.some.injEq, Prod.mk.injEq, exists_const] at h
    obtain ⟨info, -, -, -, -, rfl, rfl⟩ := h
    exact Grows.of_sets rfl rfl
  · simp only [applyClaimPow, ensure_eq_some, option_bind_eq_some, option_pure_eq,
      Option.some.injEq, Prod.mk.injEq, exists_const] at h
    obtain ⟨-, -, slot, -, -, -, -, -, rfl, rfl⟩ := h
    exact (Grows.of_sets rfl rfl).trans (Grows.setSet fun _ => by simp)

theorem applyOps_grows {P : Prims} {E : Env} {txh : Fr} (ops : List Op) :
    ∀ (πs : List OpProof) (st st' : State) (bal gas : ℕ),
      applyOps P E st txh ops πs = some (st', bal, gas) → Grows st st' := by
  induction ops with
  | nil =>
    intro πs st st' bal gas h
    cases πs with
    | nil =>
      simp only [applyOps, Option.some.injEq, Prod.mk.injEq] at h
      obtain ⟨rfl, -, -⟩ := h
      exact Grows.refl _
    | cons _ _ => simp [applyOps] at h
  | cons op ops ih =>
    intro πs st st' bal gas h
    cases πs with
    | nil => simp [applyOps] at h
    | cons π πs =>
      simp only [applyOps, option_bind_eq_some, ensure_eq_some, option_pure_eq, exists_const,
        Option.some.injEq, Prod.mk.injEq] at h
      obtain ⟨⟨st1, fee⟩, h1, ⟨st2, bal', gas'⟩, h2, -, rfl, rfl, rfl⟩ := h
      exact (applyOp_grows h1).trans (ih πs st1 st2 bal' gas' h2)

theorem applyOps_spec {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {E : Env} {txh : Fr} (ops : List Op) :
    ∀ (πs : List OpProof) (st st' : State) (bal gas : ℕ), Inv P.H st →
      applyOps P E st txh ops πs = some (st', bal, gas) → Cap st' →
      Inv P.H st' ∧ Grows st st' ∧ value P.H st' + bal ≤ value P.H st := by
  induction ops with
  | nil =>
    intro πs st st' bal gas I h _
    cases πs with
    | nil =>
      simp only [applyOps, Option.some.injEq, Prod.mk.injEq] at h
      obtain ⟨rfl, rfl, rfl⟩ := h
      exact ⟨I, Grows.refl _, le_rfl⟩
    | cons _ _ => simp [applyOps] at h
  | cons op ops ih =>
    intro πs st st' bal gas I h hcap
    cases πs with
    | nil => simp [applyOps] at h
    | cons π πs =>
      simp only [applyOps, option_bind_eq_some, ensure_eq_some, option_pure_eq, exists_const,
        Option.some.injEq, Prod.mk.injEq] at h
      obtain ⟨⟨st1, fee⟩, h1, ⟨st2, bal', gas'⟩, h2, -, rfl, rfl, rfl⟩ := h
      -- the later Operations only grow the note sets, so the capacity holds before them
      obtain ⟨I1, G1, V1⟩ := applyOp_spec I h1
        (hcap.of_grows (applyOps_grows ops πs st1 st2 bal' gas' h2))
      obtain ⟨I2, G2, V2⟩ := ih πs st1 st2 bal' gas' I1 h2 hcap
      refine ⟨I2, G1.trans G2, ?_⟩
      dsimp only at V1 V2 ⊢
      omega

theorem Inv.clearBuffers {st : State} (I : Inv H st) : Inv H st.clearBuffers where
  two_le := I.two_le
  sets i hi := ⟨⟨(I.sets i hi).window.keys, (I.sets i hi).window.length_le,
    (I.sets i hi).window.isPrefix⟩, List.nil_sublist _, (I.sets i hi).imt⟩
  chan := I.chan
  declNodup := I.declNodup
  declNote := I.declNote
  declOutputs := I.declOutputs
  pending := I.pending

theorem value_clearBuffers (st : State) : value H st.clearBuffers = value H st := rfl

/-- **No Mantle Transaction creates value.** From a well-formed state, a valid Mantle
Transaction leaves a well-formed state whose value, plus the mandatory fee and the tip the
transaction pays, is at most the value before: the value of the unspent notes of every note
set, of the notes withdrawn SDP declarations will release, and of the proof of work pool. -/
theorem applyTx_value {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {E : Env} {st st' : State} {stx : SignedMantleTx}
    {fee tip : ℕ} (I : Inv P.H st) (h : applyTx P E st stx = some (st', fee, tip))
    (hcap : Cap st') : Inv P.H st' ∧ value P.H st' + fee + tip ≤ value P.H st := by
  simp only [applyTx, ensure_eq_some, option_bind_eq_some, option_pure_eq, exists_const,
    Option.some.injEq, Prod.mk.injEq] at h
  obtain ⟨-, ⟨st1, bal, gas⟩, hops, f, -, hle, rfl, rfl, rfl⟩ := h
  obtain ⟨I1, -, V1⟩ := applyOps_spec _ _ _ _ _ _ I.clearBuffers hops (by simpa using hcap)
  refine ⟨I1, ?_⟩
  rw [value_clearBuffers] at V1
  dsimp only at hle ⊢
  omega

end

end Mantle
