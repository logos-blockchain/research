import Mantle.Leadership

/-!
# Programs governing channel notes

RFC-481 and Mantle, *Programs*, table **What enforces what**. Each row is proven at the check
the table names:

| Property | Lean |
|---|---|
| No value is created | `applyTx_value` (`NoValueCreated.lean`) |
| A user note moves only with the key of its holder | `ZkTransfer.input_note`: the circuit derives the key from the secret key |
| A payment only pays the program it names, for the intent its holder signed | **`payment_proof_bound`**, `step_proof_not_payment` |
| A program note is created and consumed only with the proof of its program | `ZkTransfer.not_program_output`, `ZkTransfer.not_program_input`, `pol_not_program_note`, **`validateSteps_program_outputs`**, **`validateSteps_program_inputs`** |
| A program step serves the intents over LGO as the rule of the program states | the program proof, required by every program step (`validateSteps_program_outputs`) |
| The opening of every note of a program is available to the next sequencer | `validateSteps_program_outputs`: every created note of a program has its published opening |
| A program step serves the intents over the assets of the zone | not checked by the ledger (the users of the zone) |

The ZkProgramSpend and the program proof are bound to the `op_id` of the inscription
(`spend_proof_bound`).
-/

namespace Mantle

open Classical

noncomputable section

variable {H : Hash}

/-! ## The ZkTransfer moves user notes only -/

namespace ZkTransfer

variable {ins outs : List Fr} {ex : ℕ} {R msg : Fr} {wit : ZkTransferWitness}

/-- A ZkTransfer never creates a note of a program. -/
theorem not_program_output (hv : ZkTransferRel H ⟨ins, outs, ex, R, msg⟩ wit) {n : Note} (hn : n.program ≠ 0) :
    noteCm H n ∉ outs := by
  intro hmem
  obtain ⟨k, hk, hkn⟩ := List.getElem_of_mem hmem
  obtain ⟨hu, hcm, -⟩ := output_note hv hk
  rw [hkn] at hcm
  exact noteCm_ne_of_program hn hu hcm

/-- A ZkTransfer never consumes a note of a program, whatever secret key. -/
theorem not_program_input (hv : ZkTransferRel H ⟨ins, outs, ex, R, msg⟩ wit) {n : Note} (hn : n.program ≠ 0)
    (sk : Fr) : noteNf H (noteCm H n) sk ∉ ins := by
  intro hmem
  obtain ⟨k, hk, hkn⟩ := List.getElem_of_mem hmem
  obtain ⟨hu, -, hnf, -, -⟩ := input_note hv hk
  rw [hkn] at hnf
  exact noteCm_ne_of_program hn hu (noteNf_injective hnf).1

end ZkTransfer

/-- **A verified ZkTransfer never creates nor consumes a note of a program**, by knowledge
soundness. -/
theorem zkTransfer_user_notes {P : Prims} [P.ZkTransferSound] {ins outs : List Fr} {ex : ℕ}
    {R msg : Fr} {π : ProofBlob} (hv : P.zkTransferVerify ⟨ins, outs, ex, R, msg⟩ π) {n : Note}
    (hn : n.program ≠ 0) : noteCm P.H n ∉ outs ∧ ∀ sk, noteNf P.H (noteCm P.H n) sk ∉ ins := by
  obtain ⟨w, hw⟩ := Prims.ZkTransferSound.sound hv
  exact ⟨ZkTransfer.not_program_output hw hn, ZkTransfer.not_program_input hw hn⟩

/-! ## The ZkProgramSpend moves the notes of its program -/

namespace ZkProgramSpend

variable {ins outs : List Fr} {flags : List Bool} {R pid : Fr} {paid : ℕ} {snh msg : Fr}
  {wit : ZkProgramSpendWitness}

/-- Every input of a program spend is a note of its program. -/
theorem input_program (hv : ZkProgramSpendRel H ⟨ins, outs, flags, R, pid, paid, snh, msg⟩ wit) {n : Note} {sk : Fr}
    (hmem : noteNf H (noteCm H n) sk ∈ ins) : n.program = pid := by
  obtain ⟨k, hk, hkn⟩ := List.getElem_of_mem hmem
  obtain ⟨hp, -, hnf, -, -⟩ := input_note hv hk
  rw [hkn] at hnf
  rw [noteCm_injective (noteNf_injective hnf).1]
  exact hp

/-- Every output of a program spend is a note of its program if flagged, a user note
otherwise. -/
theorem output_cases (hv : ZkProgramSpendRel H ⟨ins, outs, flags, R, pid, paid, snh, msg⟩ wit) {k : ℕ}
    (hk : k < outs.length) :
    (flags[k]'(by rw [length_flags hv]; exact hk) = true →
      ∃ n : Note, n.program = pid ∧ outs[k] = noteCm H n) ∧
    (flags[k]'(by rw [length_flags hv]; exact hk) = false →
      ∃ n : Note, n.IsUser ∧ outs[k] = noteCm H n) := by
  obtain ⟨hp, hcm, -⟩ := output_note hv hk
  constructor
  · intro hf; rw [hf] at hp; exact ⟨_, hp, hcm⟩
  · intro hf; rw [hf] at hp; exact ⟨_, hp, hcm⟩

end ZkProgramSpend

/-! ## What the ledger checks of a program step -/

/-- The proofs of a program step verified: the program is registered, and its program proof
verified under the registered key on `(spend_notes_hash, payments_hash, op_id)`. -/
def ProgramProven (P : Prims) (programs : Fr → Option VerificationKey) (opIdFr : Fr)
    (ps : ProgramStep) : Prop :=
  ∃ (key : VerificationKey) (gπ : ProofBlob), programs ps.programId = some key ∧
    P.groth16Verify key [ps.spendNotesHash, paymentsHash P.H ps, opIdFr] gπ

theorem validatePayments_outputs {P : Prims} [P.ZkTransferSound] {pid : Fr} (pays : List Payment) :
    ∀ (πs : List ProofBlob) (s : NoteSet) (nfs : Finset Fr) {r : NoteSet × Finset Fr × ℕ},
      validatePayments P pid s nfs pays πs = some r →
      (∀ c ∈ pays.flatMap (·.outputs), ∃ u : Note, u.IsUser ∧ c = noteCm P.H u) ∧
      (∀ nf ∈ pays.flatMap (·.inputs), ∃ (u : Note) (sk : Fr), u.IsUser ∧
        nf = noteNf P.H (noteCm P.H u) sk) := by
  induction pays with
  | nil => intro πs s nfs r _; simp
  | cons p ps ih =>
    intro πs s nfs r h
    cases πs with
    | nil => simp [validatePayments] at h
    | cons π πs =>
      simp only [validatePayments, ensure_eq_some, option_bind_eq_some, option_pure_eq,
        exists_const] at h
      obtain ⟨-, -, -, R, -, hv0, ⟨s', nfs', paid'⟩, hrest, -⟩ := h
      obtain ⟨wit, hv⟩ := Prims.ZkTransferSound.sound hv0
      obtain ⟨ihO, ihI⟩ := ih πs _ _ hrest
      refine ⟨fun c hc => ?_, fun nf hnf => ?_⟩
      · rw [List.flatMap_cons, List.mem_append] at hc
        rcases hc with hc | hc
        · obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hc
          obtain ⟨hu, hcm, -⟩ := ZkTransfer.output_note hv hk
          exact ⟨_, hu, hcm⟩
        · exact ihO c hc
      · rw [List.flatMap_cons, List.mem_append] at hnf
        rcases hnf with hnf | hnf
        · obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hnf
          obtain ⟨hu, -, hn, -, -⟩ := ZkTransfer.input_note hv hk
          exact ⟨_, _, hu, hn⟩
        · exact ihI nf hnf

/-- **A note of a program is created only by a program step of that program**, whose program
proof verified under the registered key, and with its opening published: every output of the
steps of a valid inscription is a user note or a flagged output of a program step, opened
with that step's program. -/
theorem validateSteps_program_outputs {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound]
    {opIdFr : Fr}
    {programs : Fr → Option VerificationKey} (steps : List Step) :
    ∀ (πs : List StepProof) (s : NoteSet) (nfs : Finset Fr) {sv : NoteSet},
      validateSteps P opIdFr programs s nfs steps πs = some sv →
      ∀ c ∈ steps.flatMap Step.outs, (∃ u : Note, u.IsUser ∧ c = noteCm P.H u) ∨
        ∃ ps, Step.program ps ∈ steps ∧ c ∈ programCms ps ∧
          ProgramProven P programs opIdFr ps ∧
          ∃ o : ProgramNoteOpening,
            c = noteCm P.H ⟨o.value, o.nonce, o.publicKey, ps.programId, o.data⟩ := by
  induction steps with
  | nil => intro πs s nfs sv _; simp
  | cons step rest ih =>
    intro πs s nfs sv h c hc
    cases πs with
    | nil => cases step <;> simp [validateSteps] at h
    | cons sp πs =>
      rw [List.flatMap_cons, List.mem_append] at hc
      cases step with
      | user u =>
        cases sp with
        | program _ _ _ _ => simp [validateSteps] at h
        | user π =>
          simp only [validateSteps, ensure_eq_some, option_bind_eq_some, exists_const] at h
          obtain ⟨-, -, -, R, -, hv0, hrest⟩ := h
          obtain ⟨wit, hv⟩ := Prims.ZkTransferSound.sound hv0
          rcases hc with hc | hc
          · obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hc
            obtain ⟨hu, hcm, -⟩ := ZkTransfer.output_note hv hk
            exact Or.inl ⟨_, hu, hcm⟩
          · rcases ih πs _ _ hrest c hc with h' | ⟨ps, hps, h'⟩
            · exact Or.inl h'
            · exact Or.inr ⟨ps, List.mem_cons_of_mem _ hps, h'⟩
      | program ps =>
        cases sp with
        | user _ => simp [validateSteps] at h
        | program pπs spend gπ openings =>
          simp only [validateSteps, ensure_eq_some, option_bind_eq_some, exists_const] at h
          obtain ⟨key, hkey, ⟨s1, nfs1, paid⟩, hpay, -, -, -, R, -, hv0, hop, hg, hrest⟩ := h
          obtain ⟨wit, hv⟩ := Prims.ZkProgramSpendSound.sound hv0
          rcases hc with hc | hc
          · simp only [Step.outs, List.mem_append] at hc
            rcases hc with hc | hc
            · exact Or.inl ((validatePayments_outputs ps.payments pπs s nfs hpay).1 c hc)
            · obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hc
              have hflen := ZkProgramSpend.length_flags hv
              have hk' : k < ps.programOutputs.length := by rw [hflen]; exact hk
              cases hf : ps.programOutputs[k] with
              | false =>
                obtain ⟨n, hu, hcm⟩ := (ZkProgramSpend.output_cases hv hk).2 hf
                exact Or.inl ⟨n, hu, hcm⟩
              | true =>
                right
                have hpc : ps.outputs[k] ∈ programCms ps := by
                  simp only [programCms, List.mem_filterMap]
                  refine ⟨(ps.outputs[k], true), ?_, by simp⟩
                  rw [List.mem_iff_getElem]
                  exact ⟨k, by simp [hflen]; exact hk, by simp [hf]⟩
                obtain ⟨o, -, ho⟩ := forall₂_mem_left hop hpc
                exact ⟨ps, List.mem_cons_self .., hpc, ⟨key, gπ, hkey, hg⟩, o, ho⟩
          · rcases ih πs _ _ hrest c hc with h' | ⟨ps', hps, h'⟩
            · exact Or.inl h'
            · exact Or.inr ⟨ps', List.mem_cons_of_mem _ hps, h'⟩

/-- **A note of a program is consumed only by a program step of that program**, whose program
proof verified under the registered key: every nullifier the steps of a valid inscription
consume is that of a user note, or an input of a program step on a note of its program. -/
theorem validateSteps_program_inputs {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound]
    {opIdFr : Fr}
    {programs : Fr → Option VerificationKey} (steps : List Step) :
    ∀ (πs : List StepProof) (s : NoteSet) (nfs : Finset Fr) {sv : NoteSet},
      validateSteps P opIdFr programs s nfs steps πs = some sv →
      ∀ nf ∈ steps.flatMap Step.ins,
        (∃ (u : Note) (sk : Fr), u.IsUser ∧ nf = noteNf P.H (noteCm P.H u) sk) ∨
        ∃ ps, Step.program ps ∈ steps ∧ nf ∈ ps.inputs ∧ ProgramProven P programs opIdFr ps ∧
          ∃ (n : Note) (sk : Fr), n.program = ps.programId ∧ nf = noteNf P.H (noteCm P.H n) sk := by
  induction steps with
  | nil => intro πs s nfs sv _; simp
  | cons step rest ih =>
    intro πs s nfs sv h nf hnf
    cases πs with
    | nil => cases step <;> simp [validateSteps] at h
    | cons sp πs =>
      rw [List.flatMap_cons, List.mem_append] at hnf
      cases step with
      | user u =>
        cases sp with
        | program _ _ _ _ => simp [validateSteps] at h
        | user π =>
          simp only [validateSteps, ensure_eq_some, option_bind_eq_some, exists_const] at h
          obtain ⟨-, -, -, R, -, hv0, hrest⟩ := h
          obtain ⟨wit, hv⟩ := Prims.ZkTransferSound.sound hv0
          rcases hnf with hnf | hnf
          · obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hnf
            obtain ⟨hu, -, hn, -, -⟩ := ZkTransfer.input_note hv hk
            exact Or.inl ⟨_, _, hu, hn⟩
          · rcases ih πs _ _ hrest nf hnf with h' | ⟨ps, hps, h'⟩
            · exact Or.inl h'
            · exact Or.inr ⟨ps, List.mem_cons_of_mem _ hps, h'⟩
      | program ps =>
        cases sp with
        | user _ => simp [validateSteps] at h
        | program pπs spend gπ openings =>
          simp only [validateSteps, ensure_eq_some, option_bind_eq_some, exists_const] at h
          obtain ⟨key, hkey, ⟨s1, nfs1, paid⟩, hpay, -, -, -, R, -, hv0, -, hg, hrest⟩ := h
          obtain ⟨wit, hv⟩ := Prims.ZkProgramSpendSound.sound hv0
          rcases hnf with hnf | hnf
          · simp only [Step.ins, List.mem_append] at hnf
            rcases hnf with hnf | hnf
            · exact Or.inl ((validatePayments_outputs ps.payments pπs s nfs hpay).2 nf hnf)
            · right
              obtain ⟨k, hk, rfl⟩ := List.getElem_of_mem hnf
              obtain ⟨hp, -, hn, -, -⟩ := ZkProgramSpend.input_note hv hk
              exact ⟨ps, List.mem_cons_self .., hnf, ⟨key, gπ, hkey, hg⟩, _, _, hp, hn⟩
          · rcases ih πs _ _ hrest nf hnf with h' | ⟨ps', hps, h'⟩
            · exact Or.inl h'
            · exact Or.inr ⟨ps', List.mem_cons_of_mem _ hps, h'⟩

/-- A note of a program `P ≠ 0` created by an inscription: its step is a step of `P`, proven. -/
theorem program_note_created {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {opIdFr : Fr} {programs : Fr → Option VerificationKey}
    {steps : List Step} {πs : List StepProof} {s sv : NoteSet} {nfs : Finset Fr}
    (h : validateSteps P opIdFr programs s nfs steps πs = some sv) {n : Note}
    (hn : n.program ≠ 0) (hc : noteCm P.H n ∈ steps.flatMap Step.outs) :
    ∃ ps, Step.program ps ∈ steps ∧ ps.programId = n.program ∧
      ProgramProven P programs opIdFr ps ∧ noteCm P.H n ∈ programCms ps := by
  rcases validateSteps_program_outputs steps πs s nfs h _ hc with ⟨u, hu, he⟩ | ⟨ps, hps, hpc, hpr, o, ho⟩
  · exact absurd he (noteCm_ne_of_program hn hu)
  · refine ⟨ps, hps, ?_, hpr, hpc⟩
    rw [noteCm_injective ho]

/-- A note of a program `P ≠ 0` consumed by an inscription: by a step of `P`, proven. -/
theorem program_note_consumed {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {opIdFr : Fr} {programs : Fr → Option VerificationKey}
    {steps : List Step} {πs : List StepProof} {s sv : NoteSet} {nfs : Finset Fr}
    (h : validateSteps P opIdFr programs s nfs steps πs = some sv) {n : Note}
    (hn : n.program ≠ 0) {sk : Fr} (hc : noteNf P.H (noteCm P.H n) sk ∈ steps.flatMap Step.ins) :
    ∃ ps, Step.program ps ∈ steps ∧ ps.programId = n.program ∧ ProgramProven P programs opIdFr ps := by
  rcases validateSteps_program_inputs steps πs s nfs h _ hc with
    ⟨u, sk', hu, he⟩ | ⟨ps, hps, -, hpr, m, sk', hm, he⟩
  · exact absurd (noteNf_injective he).1 (noteCm_ne_of_program hn hu)
  · refine ⟨ps, hps, ?_, hpr⟩
    rw [noteCm_injective (noteNf_injective he).1, hm]

/-! ## Messages: payments, steps and program spends are bound to what they sign -/

theorem tag_ne : CHANNEL_STEP_V1 ≠ PROGRAM_PAYMENT_V1 := by decide

/-- A list prefixed by its length determines the list and what follows. -/
theorem lenPrefixed_inj {a b c d : List Fr} (h : (a.length :: a ++ c) = (b.length :: b ++ d)) :
    a = b ∧ c = d := by
  simp only [List.cons_append, List.cons.injEq] at h
  obtain ⟨hl, h⟩ := h
  exact List.append_inj h hl

/-- `payment_msg` determines the program, the intent, the inputs and the outputs. -/
theorem paymentMsg_inj {pid pid' : Fr} {p p' : Payment}
    (h : paymentMsg H pid p = paymentMsg H pid' p') :
    pid = pid' ∧ p.intent = p'.intent ∧ p.inputs = p'.inputs ∧ p.outputs = p'.outputs := by
  unfold paymentMsg at h
  have := H.injective h
  simp only [List.cons_append, List.cons.injEq] at this
  obtain ⟨-, h1, h2, h3⟩ := this
  have h3' := lenPrefixed_inj (a := p.inputs) (b := p'.inputs)
    (c := p.outputs.length :: p.outputs) (d := p'.outputs.length :: p'.outputs)
    (by simpa using h3)
  simp only [List.cons.injEq] at h3'
  exact ⟨h1, h2, h3'.1, h3'.2.2⟩

/-- A user step and a payment never sign the same message. -/
theorem stepMsg_ne_paymentMsg (u : UserStep) (pid : Fr) (p : Payment) :
    stepMsg H u ≠ paymentMsg H pid p := by
  intro h
  unfold stepMsg paymentMsg at h
  have := H.injective h
  simp only [List.cons_append, List.cons.injEq] at this
  exact tag_ne this.1

/-- **A payment only pays the program it names, for its intent**: a payment's proof verifies
for no other program or intent, since a proof verifies for one statement. -/
theorem payment_proof_bound {P : Prims} [P.ProofBinding] {π : ProofBlob}
    {ins outs ins' outs' : List Fr} {ex ex' : ℕ} {R R' pid pid' : Fr} {p p' : Payment}
    (h : P.zkTransferVerify ⟨ins, outs, ex, R, paymentMsg P.H pid p⟩ π)
    (h' : P.zkTransferVerify ⟨ins', outs', ex', R', paymentMsg P.H pid' p'⟩ π)
    : pid = pid' ∧ p.intent = p'.intent := by
  have := Prims.ProofBinding.zkTransfer h h'
  simp only [ZkTransferPublic.mk.injEq] at this
  obtain ⟨-, -, -, -, hm⟩ := this
  obtain ⟨h1, h2, -⟩ := paymentMsg_inj hm
  exact ⟨h1, h2⟩

/-- The proof of a user step cannot serve as a payment. -/
theorem step_proof_not_payment {P : Prims} [P.ProofBinding] {π : ProofBlob}
    {ins outs ins' outs' : List Fr} {ex ex' : ℕ} {R R' pid : Fr} {u : UserStep} {p : Payment}
    (h : P.zkTransferVerify ⟨ins, outs, ex, R, stepMsg P.H u⟩ π)
    (h' : P.zkTransferVerify ⟨ins', outs', ex', R', paymentMsg P.H pid p⟩ π) :
    False := by
  have := Prims.ProofBinding.zkTransfer h h'
  simp only [ZkTransferPublic.mk.injEq] at this
  exact stepMsg_ne_paymentMsg u pid p this.2.2.2.2

/-- The program spend of a step is bound to the `op_id` of its inscription. -/
theorem spend_proof_bound {P : Prims} [P.ProofBinding] {π : ProofBlob}
    {ins outs ins' outs' : List Fr} {flags flags' : List Bool} {R R' pid pid' snh snh' : Fr}
    {paid paid' : ℕ} {m m' : Fr}
    (h : P.zkProgramSpendVerify ⟨ins, outs, flags, R, pid, paid, snh, m⟩ π)
    (h' : P.zkProgramSpendVerify ⟨ins', outs', flags', R', pid', paid', snh', m'⟩ π) : m = m' := by
  have := Prims.ProofBinding.zkProgramSpend h h'
  simp only [ZkProgramSpendPublic.mk.injEq] at this
  exact this.2.2.2.2.2.2.2

end

end Mantle
