import Mantle.Codec
import Mantle.Ledger

/-!
# Mantle Transaction Encoding

Mantle Transaction Encoding 2.1.0 (RFC-480 §7, RFC-481 §5), production by production, as
codecs (`Codec.lean`) over the types of the ledger model (`Ledger.lean`): a `FieldElement`,
`Hash32` or `Ed25519PublicKey` is a 32-byte little-endian integer, an `Ed25519Signature` or a
`G2Point` 64 bytes, a `Groth16Proof` 128 bytes; counts and lengths are `Byte`, `UINT16` or
`UINT32` prefixes with the bounds of the specification (`MAX_OPERATION_DATA_SIZE` for
inscriptions and deposit metadata, 329 bytes per locator and 8 locators, 8 outputs for a
program spend, the bit mask of `ProgramOutputs` with no bit set from `OutputCount` up, the
activity metadata type `0x01`). The proofs are decoded from the Operations parsed before them:
one `StepProof` per step, one payment proof per payment, one opening per bit of
`ProgramOutputs`.

* **`signedTx_canonical`**: a byte string decodes to a signed Mantle Transaction iff it is the
  encoding of that transaction, which is well formed: the encoding is canonical and
  unambiguous, as the specification requires;
* `signedTx_encode_injective`, `mantleTx_encode_injective`: distinct transactions have distinct
  encodings (so `mantle_txhash` and `op_id` hash distinct preimages);
* `fieldElement_not_canonical_mod_p`: a `FieldElement` is any 32 bytes, so the encodings of
  `x` and `x + p` are distinct and both accepted for values below `2^256 - p`: up to 5 encodings
  per field element, unless the decoder rejects values `≥ p`, which the specification does not
  require.
-/

namespace Mantle.Encoding

open Codec

/-! ## Terminals -/

/-- `FieldElement`, `Hash32`, `Ed25519PublicKey`, `ZkPublicKey`, `G1Point`: 32 bytes. -/
def fe : Codec ℕ := uint 32
/-- `Ed25519Signature`, `G2Point`: 64 bytes. -/
def b64 : Codec ℕ := uint 64
/-- `Groth16Proof`: 128 bytes. -/
def groth : Codec ℕ := uint 128
def u8 : Codec ℕ := uint 1
def u16 : Codec ℕ := uint 2
def u32 : Codec ℕ := uint 4
def u64 : Codec ℕ := uint 8

/-- `MAX_OPERATION_DATA_SIZE`. -/
def MAX_OPERATION_DATA_SIZE : ℕ := 1_835_008

/-- `Inputs`, `Outputs`: a `Byte` count of field elements. -/
def fes : Codec (List ℕ) := list 1 255 (by norm_num) fe

/-- `Inscription`, `DepositMetadata`: a `UINT32` length, at most `MAX_OPERATION_DATA_SIZE`. -/
def opData : Codec Bytes := varBytes 4 MAX_OPERATION_DATA_SIZE (by norm_num [MAX_OPERATION_DATA_SIZE])

/-- A structure encoded through a tuple, both ways definitional. -/
abbrev via {α β : Type} (A : Codec α) (f : α → β) (g : β → α) (hfg : ∀ b, f (g b) = b := by
    intro b; rfl) (hgf : ∀ a, g (f a) = a := by intro a; rfl) : Codec β :=
  iso A f g (fun _ => True) (fun b _ => hfg b) (fun a _ => ⟨hgf a, trivial⟩)

/-! ## Operations -/

/-- `Transfer = Inputs Outputs CmMerkleRoot Value`. -/
def transferC : Codec Transfer :=
  via (pair fes (pair fes (pair fe u64)))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2⟩)
    (fun t => (t.inputs, t.outputs, t.cmMerkleRoot, t.excessValue))

/-- `UserStep = Inputs Outputs CmMerkleRoot Buffered`. -/
def userStepC : Codec UserStep :=
  via (pair fes (pair fes (pair fe u16)))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2⟩)
    (fun u => (u.inputs, u.outputs, u.cmMerkleRoot, u.buffered))

/-- `Payment = Inputs Outputs CmMerkleRoot Buffered Value Intent`. -/
def paymentC : Codec Payment :=
  via (pair fes (pair fes (pair fe (pair u16 (pair u64 fe)))))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2.1, x.2.2.2.2.1, x.2.2.2.2.2⟩)
    (fun p => (p.inputs, p.outputs, p.cmMerkleRoot, p.buffered, p.paidValue, p.intent))

/-- The outputs of a program spend, at most 8, with their `ProgramOutputs` mask. -/
def programOutputsC : Codec (List ℕ × List Bool) :=
  bind (list 1 8 (by norm_num) fe) fun outs => bitmask outs.length

/-- `ProgramStep = ProgramId Payments Inputs Outputs ProgramOutputs CmMerkleRoot
SpendNotesHash`. -/
def programStepC : Codec ProgramStep :=
  via (pair fe (pair (list 1 255 (by norm_num) paymentC) (pair fes
      (pair programOutputsC (pair fe fe)))))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2.1.1, x.2.2.2.1.2, x.2.2.2.2.1, x.2.2.2.2.2⟩)
    (fun p => (p.programId, p.payments, p.inputs, (p.outputs, p.programOutputs), p.cmMerkleRoot,
      p.spendNotesHash))

/-- `Step = (%x00 UserStep) / (%x01 ProgramStep)`. -/
def stepC : Codec Step where
  wf
    | .user u => userStepC.wf u
    | .program p => programStepC.wf p
  enc
    | .user u => 0 :: userStepC.enc u
    | .program p => 1 :: programStepC.enc p
  dec
    | x :: b =>
      if x = 0 then (userStepC.dec b).map fun ur => (.user ur.1, ur.2)
      else if x = 1 then (programStepC.dec b).map fun pr => (.program pr.1, pr.2)
      else none
    | [] => none
  dec_enc := by
    intro s r h
    cases s with
    | user u => simp [userStepC.dec_enc r h]
    | program p => simp [programStepC.dec_enc r h]
  enc_dec := by
    intro b s r h
    cases b with
    | nil => simp at h
    | cons x b =>
      simp only at h
      split_ifs at h with h0 h1
      · subst h0
        simp only [Option.map_eq_some_iff, Prod.mk.injEq] at h
        obtain ⟨⟨u, r'⟩, h1, rfl, rfl⟩ := h
        obtain ⟨w, rfl⟩ := userStepC.enc_dec h1
        exact ⟨w, rfl⟩
      · subst h1
        simp only [Option.map_eq_some_iff, Prod.mk.injEq] at h
        obtain ⟨⟨p, r'⟩, h1, rfl, rfl⟩ := h
        obtain ⟨w, rfl⟩ := programStepC.enc_dec h1
        exact ⟨w, rfl⟩

/-- `ChannelInscribe = ChannelId Inscription Parent Signer Steps`. -/
def inscribeC : Codec Inscribe :=
  via (pair fe (pair opData (pair fe (pair fe (list 2 65535 (by norm_num) stepC)))))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2.1, x.2.2.2.2⟩)
    (fun m => (m.channel, m.inscription, m.parent, m.signer, m.steps))

/-- `ChannelConfig = ChannelId Parent KeyCount *Signer PostingTimeframe PostingTimeout
ConfigThreshold`. -/
def configC : Codec ChannelConfig :=
  via (pair fe (pair fe (pair (list 2 65535 (by norm_num) fe) (pair u32 (pair u32 u16)))))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2.1, x.2.2.2.2.1, x.2.2.2.2.2⟩)
    (fun c => (c.channel, c.parent, c.keys, c.postingTimeframe, c.postingTimeout,
      c.configurationThreshold))

/-- `ChannelDeposit = ChannelId Inputs CmMerkleRoot Outputs Value DepositMetadata`. -/
def depositC : Codec ChannelDeposit :=
  via (pair fe (pair fes (pair fe (pair fes (pair u64 opData)))))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2.1, x.2.2.2.2.1, x.2.2.2.2.2⟩)
    (fun d => (d.channel, d.inputs, d.cmMerkleRoot, d.outputs, d.excessValue, d.metadata))

/-- `ChannelWithdraw = ChannelId Inputs CmMerkleRoot Outputs`. -/
def withdrawC : Codec ChannelWithdraw :=
  via (pair fe (pair fes (pair fe fes)))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2⟩)
    (fun w => (w.channel, w.inputs, w.cmMerkleRoot, w.outputs))

/-- `Locators = LocatorCount *Locator`, at most 8 locators of at most 329 bytes. -/
def locatorsC : Codec (List Bytes) :=
  list 1 8 (by norm_num) (varBytes 2 329 (by norm_num))

/-- `SDPDeclare = ServiceType Locators ProviderId ZkId Inputs CmMerkleRoot Value`. -/
def declareC : Codec DeclarationMessage :=
  via (pair u8 (pair locatorsC (pair fe (pair fe (pair fes (pair fe u64))))))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2.1, x.2.2.2.2.1, x.2.2.2.2.2.1, x.2.2.2.2.2.2⟩)
    (fun d => (d.serviceType, d.locators, d.providerId, d.zkId, d.inputs, d.cmMerkleRoot,
      d.amount))

/-- `SDPWithdraw = DeclarationId Nonce NoteNf Outputs Value`. -/
def sdpWithdrawC : Codec WithdrawMessage :=
  via (pair fe (pair u64 (pair fe (pair fes u64))))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2.1, x.2.2.2.2⟩)
    (fun w => (w.declaration, w.nonce, w.serviceNoteNf, w.outputs, w.excessValue))

/-- `ActivityMetadata = ActivityMetadataType ActivityMetadataPayload`: the type `0x01`
(rejected otherwise) and the 228-byte `BlendActivityProof`. -/
def activityC : Codec Bytes := filter (bytes 229) fun b => b.head? = some 1

/-- `SDPActive = DeclarationId Nonce ActivityMetadata`. -/
def activeC : Codec Active :=
  via (pair fe (pair u64 activityC))
    (fun x => ⟨x.1, x.2.1, x.2.2⟩)
    (fun a => (a.declaration, a.nonce, a.metadata))

/-- `ClaimPowReward = EpochNonce BlockHash ZkPublicKey PowNonce`. -/
def claimC : Codec ClaimPowReward :=
  via (pair fe (pair fe (pair fe fe)))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2⟩)
    (fun c => (c.epochNonce, c.blockHash, c.publicKey, c.nonce))

/-- `ProgramRegister = Groth16VerificationKey = Alpha Beta Gamma Delta IC`, with exactly four
`IC` points: 352 bytes. -/
def registerC : Codec ProgramRegister :=
  via (pair fe (pair b64 (pair b64 (pair b64 (exactList 4 fe)))))
    (fun x => ⟨⟨x.1, x.2.1, x.2.2.1, x.2.2.2.1, x.2.2.2.2⟩⟩)
    (fun r => (r.key.alpha, r.key.beta, r.key.gamma, r.key.delta, r.key.ic))

/-- The opcode of an Operation. -/
def _root_.Mantle.Op.opcode : Op → UInt8
  | .transfer _ => 0x00
  | .programRegister _ => 0x01
  | .channelConfig _ => 0x10
  | .channelInscribe _ => 0x11
  | .channelDeposit _ => 0x12
  | .channelWithdraw _ => 0x13
  | .sdpDeclare _ => 0x20
  | .sdpWithdraw _ => 0x21
  | .sdpActive _ => 0x22
  | .claimPowReward _ => 0x30

/-- The payload of an Operation (the preimage of `op_id`, after its domain separation tag). -/
def _root_.Mantle.Op.payload : Op → Bytes
  | .transfer t => transferC.enc t
  | .programRegister r => registerC.enc r
  | .channelConfig c => configC.enc c
  | .channelInscribe m => inscribeC.enc m
  | .channelDeposit d => depositC.enc d
  | .channelWithdraw w => withdrawC.enc w
  | .sdpDeclare d => declareC.enc d
  | .sdpWithdraw w => sdpWithdrawC.enc w
  | .sdpActive a => activeC.enc a
  | .claimPowReward c => claimC.enc c

/-- The payload is well formed. -/
def _root_.Mantle.Op.Wf : Op → Prop
  | .transfer t => transferC.wf t
  | .programRegister r => registerC.wf r
  | .channelConfig c => configC.wf c
  | .channelInscribe m => inscribeC.wf m
  | .channelDeposit d => depositC.wf d
  | .channelWithdraw w => withdrawC.wf w
  | .sdpDeclare d => declareC.wf d
  | .sdpWithdraw w => sdpWithdrawC.wf w
  | .sdpActive a => activeC.wf a
  | .claimPowReward c => claimC.wf c

/-- Decode a payload of a given opcode. -/
def decPayload : UInt8 → Bytes → Option (Op × Bytes)
  | 0x00, b => (transferC.dec b).map fun x => (.transfer x.1, x.2)
  | 0x01, b => (registerC.dec b).map fun x => (.programRegister x.1, x.2)
  | 0x10, b => (configC.dec b).map fun x => (.channelConfig x.1, x.2)
  | 0x11, b => (inscribeC.dec b).map fun x => (.channelInscribe x.1, x.2)
  | 0x12, b => (depositC.dec b).map fun x => (.channelDeposit x.1, x.2)
  | 0x13, b => (withdrawC.dec b).map fun x => (.channelWithdraw x.1, x.2)
  | 0x20, b => (declareC.dec b).map fun x => (.sdpDeclare x.1, x.2)
  | 0x21, b => (sdpWithdrawC.dec b).map fun x => (.sdpWithdraw x.1, x.2)
  | 0x22, b => (activeC.dec b).map fun x => (.sdpActive x.1, x.2)
  | 0x30, b => (claimC.dec b).map fun x => (.claimPowReward x.1, x.2)
  | _, _ => none

theorem decPayload_enc (op : Op) (r : Bytes) (h : op.Wf) :
    decPayload op.opcode (op.payload ++ r) = some (op, r) := by
  cases op <;> simp only [Op.Wf] at h <;> simp [decPayload, Op.opcode, Op.payload, Codec.dec_enc _ r h]

theorem decPayload_spec {c : UInt8} {b : Bytes} {op : Op} {r : Bytes}
    (h : decPayload c b = some (op, r)) : op.Wf ∧ op.opcode = c ∧ b = op.payload ++ r := by
  unfold decPayload at h
  split at h <;> simp only [Option.map_eq_some_iff, Prod.mk.injEq, reduceCtorEq] at h <;>
    obtain ⟨⟨x, r'⟩, h1, rfl, rfl⟩ := h <;>
    obtain ⟨w, rfl⟩ := Codec.enc_dec _ h1 <;>
    exact ⟨w, rfl, rfl⟩

/-- `Op = Opcode OpPayload`. -/
def opC : Codec Op where
  wf := Op.Wf
  enc op := op.opcode :: op.payload
  dec
    | c :: b => decPayload c b
    | [] => none
  dec_enc := by intro op r h; simp [decPayload_enc op r h]
  enc_dec := by
    intro b op r h
    match b, h with
    | c :: b, h =>
      obtain ⟨w, hc, rfl⟩ := decPayload_spec h
      exact ⟨w, by simp [hc]⟩

/-- `MantleTx = OpCount *Op`. -/
def mantleTxC : Codec MantleTx :=
  via (list 1 255 (by norm_num) opC) (fun ops => ⟨ops⟩) (fun tx => tx.ops)

/-! ## Proofs -/

instance : Inhabited StepProof := ⟨.user 0⟩
instance : Inhabited OpProof := ⟨.empty⟩

/-- `ProgramNoteOpening = Value NoteNonce ZkPublicKey ProgramNoteData`: 104 bytes. -/
def openingC : Codec ProgramNoteOpening :=
  via (pair u64 (pair fe (pair fe fe)))
    (fun x => ⟨x.1, x.2.1, x.2.2.1, x.2.2.2⟩)
    (fun o => (o.value, o.nonce, o.publicKey, o.data))

/-- The proof of a step: a `ZkTransfer` for a user step; for a program step, one `ZkTransfer`
per payment, the `ZkProgramSpend`, the program proof and one opening per output of the
program. -/
def stepProofC : Step → Codec StepProof
  | .user _ =>
    iso groth StepProof.user (fun | .user π => π | _ => 0) (fun | .user _ => True | _ => False)
      (by intro b hb; cases b <;> simp_all) (by intro a _; exact ⟨rfl, trivial⟩)
  | .program ps =>
    iso (pair (exactList ps.payments.length groth) (pair groth (pair groth
        (exactList (ps.programOutputs.filter id).length openingC))))
      (fun x => .program x.1 x.2.1 x.2.2.1 x.2.2.2)
      (fun | .program a b c d => (a, b, c, d) | _ => ([], 0, 0, []))
      (fun | .program _ _ _ _ => True | _ => False)
      (by intro b hb; cases b <;> simp_all) (by intro a _; exact ⟨rfl, trivial⟩)

theorem zip_map_fst_snd {α β : Type} (l : List (α × β)) :
    (l.map Prod.fst).zip (l.map Prod.snd) = l := by
  induction l with
  | nil => rfl
  | cons x l ih => simp [ih]

/-- `IndexedSignature = SignerIndex Ed25519Signature`, in a `ChannelMultiSigProof`. -/
def multiSigC : Codec (List ℕ × List ℕ) :=
  iso (list 2 65535 (by norm_num) (pair u16 b64)) (fun l => (l.map Prod.snd, l.map Prod.fst))
    (fun p => p.2.zip p.1) (fun p => p.1.length = p.2.length)
    (by
      intro p hp
      obtain ⟨sigs, idx⟩ := p
      simp only at hp ⊢
      rw [List.map_snd_zip (by omega), List.map_fst_zip (by omega)])
    (by intro l _; exact ⟨zip_map_fst_snd l, by simp⟩)

/-- The proof of an Operation, whose variant the Operation selects. -/
def proofC : Op → Codec OpProof
  | .transfer _ | .channelDeposit _ | .channelWithdraw _ =>
    iso groth OpProof.zk (fun | .zk π => π | _ => 0) (fun | .zk _ => True | _ => False)
      (by intro b hb; cases b <;> simp_all) (by intro a _; exact ⟨rfl, trivial⟩)
  | .programRegister _ | .claimPowReward _ =>
    iso empty (fun _ => OpProof.empty) (fun _ => ()) (fun | .empty => True | _ => False)
      (by intro b hb; cases b <;> simp_all) (by intro a _; exact ⟨rfl, trivial⟩)
  | .channelConfig _ =>
    iso multiSigC (fun p => OpProof.multiSig p.1 p.2) (fun | .multiSig s i => (s, i) | _ => ([], []))
      (fun | .multiSig _ _ => True | _ => False)
      (by intro b hb; cases b <;> simp_all) (by intro a _; exact ⟨rfl, trivial⟩)
  | .channelInscribe m =>
    iso (pair b64 (depList stepProofC m.steps)) (fun p => OpProof.inscribe p.1 p.2)
      (fun | .inscribe s l => (s, l) | _ => (0, []))
      (fun | .inscribe _ _ => True | _ => False)
      (by intro b hb; cases b <;> simp_all) (by intro a _; exact ⟨rfl, trivial⟩)
  | .sdpDeclare _ =>
    iso (pair groth b64) (fun p => OpProof.declare p.1 p.2) (fun | .declare π s => (π, s) | _ => (0, 0))
      (fun | .declare _ _ => True | _ => False)
      (by intro b hb; cases b <;> simp_all) (by intro a _; exact ⟨rfl, trivial⟩)
  | .sdpWithdraw _ =>
    iso (pair groth b64) (fun p => OpProof.withdraw p.1 p.2)
      (fun | .withdraw π s => (π, s) | _ => (0, 0))
      (fun | .withdraw _ _ => True | _ => False)
      (by intro b hb; cases b <;> simp_all) (by intro a _; exact ⟨rfl, trivial⟩)
  | .sdpActive _ =>
    iso b64 OpProof.sig (fun | .sig s => s | _ => 0) (fun | .sig _ => True | _ => False)
      (by intro b hb; cases b <;> simp_all) (by intro a _; exact ⟨rfl, trivial⟩)

/-- `SignedMantleTx = MantleTx OpsProofs`, the proofs following the Operations. -/
def signedTxC : Codec SignedMantleTx :=
  via (bind mantleTxC fun tx => depList proofC tx.ops)
    (fun p => ⟨p.1, p.2⟩) (fun s => (s.tx, s.opProofs))

/-! ## Results -/

/-- **The encoding of a signed Mantle Transaction is canonical**: a byte string decodes to a
transaction iff it is the encoding of that well-formed transaction. -/
theorem signedTx_canonical {b : Bytes} {stx : SignedMantleTx} :
    signedTxC.decodeAll b = some stx ↔ signedTxC.wf stx ∧ b = signedTxC.enc stx :=
  signedTxC.decodeAll_iff

theorem signedTx_encode_injective {s s' : SignedMantleTx} (h : signedTxC.wf s)
    (h' : signedTxC.wf s') (he : signedTxC.enc s = signedTxC.enc s') : s = s' :=
  signedTxC.enc_injective h h' he

/-- Distinct Mantle Transactions have distinct encodings, the preimages of `mantle_txhash`. -/
theorem mantleTx_encode_injective {t t' : MantleTx} (h : mantleTxC.wf t) (h' : mantleTxC.wf t')
    (he : mantleTxC.enc t = mantleTxC.enc t') : t = t' :=
  mantleTxC.enc_injective h h' he

/-- A well-formed signed transaction has one proof per Operation, of the variant it selects. -/
theorem signedTx_wf_proofs {s : SignedMantleTx} (h : signedTxC.wf s) :
    s.opProofs.length = s.tx.ops.length := by
  obtain ⟨⟨-, hp⟩, -⟩ := h
  simp only at hp
  generalize s.opProofs = ps at hp
  generalize s.tx.ops = ops at hp
  induction ops generalizing ps with
  | nil => simpa [depList, nil] using hp
  | cons op ops ih =>
    simp only [depList, iso, pair, Codec.bind] at hp
    obtain ⟨⟨-, h2⟩, hne⟩ := hp
    cases ps with
    | nil => exact absurd rfl hne
    | cons p ps => simp [ih ps h2]

/-- The order of the scalar field of BN254. -/
def P : ℕ := 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001

/-- **A `FieldElement` is not canonical modulo `p`**: `0` and `p` are both accepted, with
distinct encodings, and every value below `2^256 - p` has the same issue; a field element has
up to `⌊2^256 / p⌋ = 5` encodings. -/
theorem fieldElement_not_canonical_mod_p :
    fe.wf 0 ∧ fe.wf P ∧ fe.enc 0 ≠ fe.enc P ∧ 0 % P = P % P ∧ 2 ^ 256 / P = 5 := by
  have h0 : fe.wf 0 := by show (0 : ℕ) < 256 ^ 32; norm_num
  have hP : fe.wf P := by show P < 256 ^ 32; decide
  refine ⟨h0, hP, ?_, by simp, by decide⟩
  intro h
  have := fe.enc_injective h0 hP h
  exact absurd this (by decide)

end Mantle.Encoding
