import Mantle.NoteSet

/-!
# The ZkTransfer and ZkProgramSpend circuits

Mantle, Appendix *Zero Knowledge Transfer Proof* and *Zero Knowledge Program Spend Proof*
(RFC-481 §2). The constraints are transcribed as relations between the public values and a
witness.

**Proofs are opaque.** The verifiers are abstract predicates of `Prims` (`Ledger.lean`); what
a verified proof establishes is stated by explicit hypotheses, assumed only by the theorems that
use them: knowledge soundness of the ZkTransfer and of the ZkProgramSpend (a verified proof has
a witness satisfying the relation below), and, for the binding of payments, that a proof
verifies for at most one statement. Nothing is assumed about Groth16 program proofs: the ledger
only records that they verified.

The circuits take 4 inputs and 8 outputs, the inactive ones holding value `0` and the verifier
setting the flags from the lengths of the published lists. The relations below range over the
active entries; the inactive ones add `0` to every sum. The inactive entries do enter
`spend_notes_hash`, as fields chosen by the prover (`inPad`, `outPad`).

Consequences proven here, used by the ledger:

* `ZkTransfer.input_note`, `ZkTransfer.output_note` (for a witness of the relation): every
  active input is a **user note**
  whose commitment is in `tx_cm_root` and whose nullifier is the one its holder derives,
  every output a user note, and the values balance (`ZkTransfer.balance`);
* `ZkProgramSpend.input_note`, `ZkProgramSpend.output_note`: inputs are notes of the program,
  outputs are notes of the program when flagged and user notes otherwise.
-/

namespace Mantle

variable (H : Hash)

/-! ## ZkTransfer -/

/-- `ZkTransferPublic`, active entries only. -/
structure ZkTransferPublic where
  inputs : List Fr
  outputs : List Fr
  excessValue : ℕ
  txCmRoot : Fr
  msg : Fr

/-- The witness of an active input: its secret key, nonce, value and Merkle path. -/
structure InputWitness where
  sk : Fr
  nonce : Fr
  value : ℕ
  path : List (Bool × Fr)

/-- The witness of an active output: its public key, nonce and value. -/
structure OutputWitness where
  pk : Fr
  nonce : Fr
  value : ℕ

/-- The note an input witness opens: a user note under the key of `sk`. -/
def InputWitness.note (w : InputWitness) : Note := ⟨w.value, w.nonce, kdf H w.sk, 0, 0⟩

/-- The note an output witness opens: a user note. -/
def OutputWitness.note (w : OutputWitness) : Note := ⟨w.value, w.nonce, w.pk, 0, 0⟩

/-- The constraints on an active input. -/
def InputOk (root nf : Fr) (w : InputWitness) : Prop :=
  nf = noteNf H (noteCm H (w.note H)) w.sk ∧ w.path.length = 32 ∧
    rootFromPath H (noteCm H (w.note H)) w.path = root

/-- The constraints on an active output. -/
def OutputOk (cm : Fr) (w : OutputWitness) : Prop :=
  cm = noteCm H w.note ∧ w.value < TOKEN_BOUND

/-- `ZkTransferWitness`, active entries only. -/
structure ZkTransferWitness where
  inputs : List InputWitness
  outputs : List OutputWitness

/-- The ZkTransfer circuit. -/
def ZkTransferRel (pub : ZkTransferPublic) (w : ZkTransferWitness) : Prop :=
  pub.inputs.length ≤ 4 ∧ pub.outputs.length ≤ 8 ∧
    List.Forall₂ (InputOk H pub.txCmRoot) pub.inputs w.inputs ∧
    List.Forall₂ (OutputOk H) pub.outputs w.outputs ∧
    (w.inputs.map (·.value)).sum = (w.outputs.map (·.value)).sum + pub.excessValue

/-! ## ZkProgramSpend -/

/-- `ZkProgramSpendPublic`, active entries only; `outputsOfProgram` is `program_outputs`. -/
structure ZkProgramSpendPublic where
  inputs : List Fr
  outputs : List Fr
  outputsOfProgram : List Bool
  txCmRoot : Fr
  programId : Fr
  paidValue : ℕ
  spendNotesHash : Fr
  msg : Fr

/-- The witness of an active input of a program spend. -/
structure SpendInputWitness where
  sk : Fr
  nonce : Fr
  value : ℕ
  data : Fr
  path : List (Bool × Fr)

/-- The witness of an active output of a program spend. -/
structure SpendOutputWitness where
  pk : Fr
  nonce : Fr
  value : ℕ
  program : Fr
  data : Fr

/-- The note of an input of a program spend: a note of the program. -/
def SpendInputWitness.note (programId : Fr) (w : SpendInputWitness) : Note :=
  ⟨w.value, w.nonce, kdf H w.sk, programId, w.data⟩

/-- The note of an output of a program spend. -/
def SpendOutputWitness.note (w : SpendOutputWitness) : Note :=
  ⟨w.value, w.nonce, w.pk, w.program, w.data⟩

/-- The constraints on an active input of a program spend. -/
def SpendInputOk (root programId nf : Fr) (w : SpendInputWitness) : Prop :=
  nf = noteNf H (noteCm H (w.note H programId)) w.sk ∧ w.path.length = 32 ∧
    rootFromPath H (noteCm H (w.note H programId)) w.path = root

/-- The constraints on an active output of a program spend, with its flag of
`outputs_of_program`. -/
def SpendOutputOk (programId : Fr) (cm : Fr) (w : SpendOutputWitness) (ofProgram : Bool) : Prop :=
  (if ofProgram then w.program = programId else w.program = 0 ∧ w.data = 0) ∧
    cm = noteCm H w.note ∧ w.value < TOKEN_BOUND

/-- `ZkProgramSpendWitness`, with the fields of the inactive entries hashed into
`spend_notes_hash`: `(nonce, sk, data)` of each inactive input, whose public key is derived
from `sk` as for an active one, and `(nonce, pk, program, data)` of each inactive output. -/
structure ZkProgramSpendWitness where
  inputs : List SpendInputWitness
  outputs : List SpendOutputWitness
  inPad : List (Fr × Fr × Fr)
  outPad : List (Fr × Fr × Fr × Fr)

/-- The preimage of `spend_notes_hash`: the flag and the note of every input, then of every
output, inactive entries holding value `0`. -/
def spendNotesPreimage (w : ZkProgramSpendWitness) : List Fr :=
  PROGRAM_SPEND_NOTES_V1 ::
    (w.inputs.flatMap fun i => [1, i.value, i.nonce, kdf H i.sk, i.data]) ++
    (w.inPad.flatMap fun p => [0, 0, p.1, kdf H p.2.1, p.2.2]) ++
    (w.outputs.flatMap fun o => [1, o.value, o.nonce, o.pk, o.program, o.data]) ++
    (w.outPad.flatMap fun p => [0, 0, p.1, p.2.1, p.2.2.1, p.2.2.2])

/-- The ZkProgramSpend circuit. -/
def ZkProgramSpendRel (pub : ZkProgramSpendPublic) (w : ZkProgramSpendWitness) : Prop :=
  pub.inputs.length ≤ 4 ∧ pub.outputs.length ≤ 8 ∧
    pub.inputs.length + w.inPad.length = 4 ∧ pub.outputs.length + w.outPad.length = 8 ∧
    pub.outputsOfProgram.length = pub.outputs.length ∧
    List.Forall₂ (SpendInputOk H pub.txCmRoot pub.programId) pub.inputs w.inputs ∧
    List.Forall₂ (fun (co : Fr × Bool) o => SpendOutputOk H pub.programId co.1 o co.2)
      (pub.outputs.zip pub.outputsOfProgram) w.outputs ∧
    pub.spendNotesHash = H.zkhash (spendNotesPreimage H w) ∧
    (w.inputs.map (·.value)).sum + pub.paidValue = (w.outputs.map (·.value)).sum

/-! ## Consequences -/

variable {H}

namespace ZkTransfer

variable {inputs outputs : List Fr} {excess : ℕ} {root msg : Fr} {wit : ZkTransferWitness}

theorem length_inputs (h : ZkTransferRel H ⟨inputs, outputs, excess, root, msg⟩ wit) :
    wit.inputs.length = inputs.length := h.2.2.1.length_eq.symm

theorem length_outputs (h : ZkTransferRel H ⟨inputs, outputs, excess, root, msg⟩ wit) :
    wit.outputs.length = outputs.length := h.2.2.2.1.length_eq.symm

/-- Every active input is a user note with a path under `tx_cm_root`, whose nullifier is the
one its holder derives. -/
theorem input_note (h : ZkTransferRel H ⟨inputs, outputs, excess, root, msg⟩ wit) {k : ℕ}
    (hk : k < inputs.length) :
    let w := wit.inputs[k]'(by rw [length_inputs h]; exact hk)
    (w.note H).IsUser ∧ (w.note H).publicKey = kdf H w.sk ∧
      inputs[k] = noteNf H (noteCm H (w.note H)) w.sk ∧
      w.path.length = 32 ∧ rootFromPath H (noteCm H (w.note H)) w.path = root := by
  have := (List.forall₂_iff_get.1 h.2.2.1).2 k hk (by rw [length_inputs h]; exact hk)
  exact ⟨⟨rfl, rfl⟩, rfl, this⟩

/-- Every output is the commitment of a user note of value below `2^64`. -/
theorem output_note (h : ZkTransferRel H ⟨inputs, outputs, excess, root, msg⟩ wit) {k : ℕ}
    (hk : k < outputs.length) :
    let w := wit.outputs[k]'(by rw [length_outputs h]; exact hk)
    w.note.IsUser ∧ outputs[k] = noteCm H w.note ∧ w.value < TOKEN_BOUND := by
  have := (List.forall₂_iff_get.1 h.2.2.2.1).2 k hk (by rw [length_outputs h]; exact hk)
  exact ⟨⟨rfl, rfl⟩, this⟩

/-- The values balance: inputs = outputs + excess. -/
theorem balance (h : ZkTransferRel H ⟨inputs, outputs, excess, root, msg⟩ wit) :
    (wit.inputs.map (·.value)).sum = (wit.outputs.map (·.value)).sum + excess :=
  h.2.2.2.2

theorem inputs_le (h : ZkTransferRel H ⟨inputs, outputs, excess, root, msg⟩ wit) : inputs.length ≤ 4 :=
  h.1

theorem outputs_le (h : ZkTransferRel H ⟨inputs, outputs, excess, root, msg⟩ wit) : outputs.length ≤ 8 :=
  h.2.1

end ZkTransfer

namespace ZkProgramSpend

variable {inputs outputs : List Fr} {flags : List Bool} {root pid : Fr} {paid : ℕ}
  {snh msg : Fr} {wit : ZkProgramSpendWitness}

theorem length_flags (h : ZkProgramSpendRel H ⟨inputs, outputs, flags, root, pid, paid, snh, msg⟩ wit) :
    flags.length = outputs.length := h.2.2.2.2.1

theorem length_inputs (h : ZkProgramSpendRel H ⟨inputs, outputs, flags, root, pid, paid, snh, msg⟩ wit) :
    wit.inputs.length = inputs.length := h.2.2.2.2.2.1.length_eq.symm

theorem length_outputs (h : ZkProgramSpendRel H ⟨inputs, outputs, flags, root, pid, paid, snh, msg⟩ wit) :
    wit.outputs.length = outputs.length := by
  have := h.2.2.2.2.2.2.1.length_eq
  simp only [List.length_zip, length_flags h, min_self] at this
  exact this.symm

/-- Every active input is a note of the program with a path under `tx_cm_root`. -/
theorem input_note (h : ZkProgramSpendRel H ⟨inputs, outputs, flags, root, pid, paid, snh, msg⟩ wit) {k : ℕ}
    (hk : k < inputs.length) :
    let w := wit.inputs[k]'(by rw [length_inputs h]; exact hk)
    (w.note H pid).program = pid ∧ (w.note H pid).publicKey = kdf H w.sk ∧
      inputs[k] = noteNf H (noteCm H (w.note H pid)) w.sk ∧
      w.path.length = 32 ∧ rootFromPath H (noteCm H (w.note H pid)) w.path = root := by
  have := (List.forall₂_iff_get.1 h.2.2.2.2.2.1).2 k hk (by rw [length_inputs h]; exact hk)
  exact ⟨rfl, rfl, this⟩

/-- Every output is a note of the program if flagged, a user note otherwise. -/
theorem output_note (h : ZkProgramSpendRel H ⟨inputs, outputs, flags, root, pid, paid, snh, msg⟩ wit) {k : ℕ}
    (hk : k < outputs.length) :
    let w := wit.outputs[k]'(by rw [length_outputs h]; exact hk)
    (if flags[k]'(by rw [length_flags h]; exact hk) then (w.note).program = pid
      else (w.note).IsUser) ∧ outputs[k] = noteCm H w.note ∧ w.value < TOKEN_BOUND := by
  have hz := (List.forall₂_iff_get.1 h.2.2.2.2.2.2.1).2 k
    (by simp [length_flags h]; exact hk) (by rw [length_outputs h]; exact hk)
  simp only [List.get_eq_getElem, List.getElem_zip] at hz
  obtain ⟨hp, hcm, hv⟩ := hz
  refine ⟨?_, hcm, hv⟩
  split_ifs at hp ⊢
  · exact hp
  · exact hp

/-- The values balance exactly: inputs + paid value = outputs. -/
theorem balance (h : ZkProgramSpendRel H ⟨inputs, outputs, flags, root, pid, paid, snh, msg⟩ wit) :
    (wit.inputs.map (·.value)).sum + paid = (wit.outputs.map (·.value)).sum :=
  h.2.2.2.2.2.2.2.2

theorem inputs_le (h : ZkProgramSpendRel H ⟨inputs, outputs, flags, root, pid, paid, snh, msg⟩ wit) :
    inputs.length ≤ 4 := h.1

theorem outputs_le (h : ZkProgramSpendRel H ⟨inputs, outputs, flags, root, pid, paid, snh, msg⟩ wit) :
    outputs.length ≤ 8 := h.2.1

end ZkProgramSpend

/-! ## Groth16 program proofs -/

/-- A Groth16 verification key, by its points (`Alpha G1, Beta Gamma Delta G2, 4 IC G1`),
abstracted as field elements. -/
structure VerificationKey where
  alpha : Fr
  beta : Fr
  gamma : Fr
  delta : Fr
  ic : List Fr
deriving DecidableEq

/-- A proof (a ZkTransfer, a ZkProgramSpend or a Groth16 program proof), as an opaque blob:
what it proves is given by the verifiers of `Prims` and their soundness hypotheses. -/
abbrev ProofBlob := ℕ

end Mantle
