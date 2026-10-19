import Mantle.Circuits
import Mantle.Gas
import Mantle.Codec

/-!
# The Mantle state and its Operations

A transcription of the validation and execution of every Mantle Operation (Mantle 2.1.0,
RFC-480 and RFC-481), and of a Mantle Transaction. A failed `assert` is `none` (`ensure`):

* `applyOp` validates one Operation against the state the previous Operations left, then
  executes it, returning the new state and what the Operation adds to `tx_balance` (the
  `excess_value` of `TRANSFER`, `CHANNEL_DEPOSIT` and `SDP_WITHDRAW`, `0` otherwise);
* `applyTx` resets the buffers, runs the Operations in order with checked arithmetic, and
  checks that `tx_balance` pays the mandatory fee, returning the fee and the tip;
* `releaseWithdrawals` and `finalizeDeclarations` are the block-level steps of
  `CHANNEL_WITHDRAW` and *SDP Epoch Finalization*.

Abstract primitives (`Prims`) stand for what the specification leaves to other documents or to
classical hashing: `mantle_txhash`, `derive_op_id`, `declaration_id`, the encoding hashes of
inscriptions and configurations, `derive_program_id`, Ed25519, the key and locator checks,
the activity rule and the encoded size. No property of them is assumed anywhere.

Modelling choices:

* `ledger.sets` is a function `sets : ℕ → NoteSet` with a count `numSets`, and
  `declarations` an association list, so that sums over them are finite.
* The Python pseudocode validates all the steps of an inscription, mutating the buffer of the
  channel set (or of a temporary set for a channel being created), then executes them. The
  same two phases are kept: `validateSteps` returns the set with its buffer extended,
  `executeSteps` applies the steps.
* A `declare_id` is a natural standing for its 32 bytes, read little-endian as the encoding
  does (`Encoding.h32`); SDP Epoch Finalization orders ids by those bytes, first byte first
  (`releaseOrder`), not by the natural.
* `mantle_txhash` (`Prims.txHash`) is the 32-byte digest, which the Ed25519 signatures sign; the
  ZK proofs receive it reduced modulo `p`, `mantle_txhash_fr` (`toFr`). The specification's
  digest is `Encoding.mantleTxHash`. Nothing is assumed about it, nor about `ed25519Verify`.
* The gas prices of `Env` are any naturals, `0` included; nothing needs the base fee's floor
  of `1`.
* The checked sums of `tx_balance` and `tx_execution_gas` are checked once per Operation, from
  the last: the partial sums of naturals are below `2^64` iff the total is.
-/

namespace Mantle

open Classical

noncomputable section

abbrev ChannelId := ℕ
abbrev DeclarationId := ℕ
abbrev Slot := ℕ
abbrev Epoch := ℕ

def LEDGER_SET : ℕ := 0
def SDP_SET : ℕ := 1

/-- `WITHDRAW_DELAY`: one day of slots. -/
def WITHDRAW_DELAY : Slot := 86_400

/-- `assert` in the `Option` monad. -/
def ensure (p : Prop) [Decidable p] : Option Unit := if p then some () else none

@[simp] theorem ensure_bind {p : Prop} [Decidable p] {α : Type} {f : Unit → Option α} {x : α} :
    (ensure p >>= f) = some x ↔ p ∧ f () = some x := by
  unfold ensure; split_ifs <;> simp [*]

@[simp] theorem ensure_eq_some {p : Prop} [Decidable p] {u : Unit} : ensure p = some u ↔ p := by
  unfold ensure; split_ifs <;> simp [*]

@[simp] theorem option_bind_eq_some {α β : Type} {x : Option α} {f : α → Option β} {y : β} :
    (x >>= f) = some y ↔ ∃ a, x = some a ∧ f a = some y := Option.bind_eq_some_iff

@[simp] theorem option_pure_eq {α : Type} (a : α) : (pure a : Option α) = some a := rfl

/-! ## Payloads and proofs -/

structure Transfer where
  inputs : List Fr
  outputs : List Fr
  cmMerkleRoot : Fr
  excessValue : ℕ

structure UserStep where
  inputs : List Fr
  outputs : List Fr
  cmMerkleRoot : Fr
  buffered : ℕ

structure Payment where
  inputs : List Fr
  outputs : List Fr
  cmMerkleRoot : Fr
  buffered : ℕ
  paidValue : ℕ
  intent : Fr

structure ProgramStep where
  programId : Fr
  payments : List Payment
  inputs : List Fr
  outputs : List Fr
  programOutputs : List Bool
  cmMerkleRoot : Fr
  spendNotesHash : Fr

inductive Step where
  | user (s : UserStep)
  | program (s : ProgramStep)

structure Inscribe where
  channel : ChannelId
  inscription : List UInt8
  parent : Fr
  signer : Fr
  steps : List Step

structure ChannelConfig where
  channel : ChannelId
  parent : Fr
  keys : List Fr
  postingTimeframe : ℕ
  postingTimeout : ℕ
  configurationThreshold : ℕ

structure ChannelDeposit where
  channel : ChannelId
  inputs : List Fr
  cmMerkleRoot : Fr
  outputs : List Fr
  excessValue : ℕ
  metadata : List UInt8

structure ChannelWithdraw where
  channel : ChannelId
  inputs : List Fr
  cmMerkleRoot : Fr
  outputs : List Fr

structure DeclarationMessage where
  serviceType : ℕ
  locators : List (List UInt8)
  providerId : Fr
  zkId : Fr
  inputs : List Fr
  cmMerkleRoot : Fr
  amount : ℕ

structure WithdrawMessage where
  declaration : DeclarationId
  nonce : ℕ
  serviceNoteNf : Fr
  outputs : List Fr
  excessValue : ℕ

structure Active where
  declaration : DeclarationId
  nonce : ℕ
  metadata : List UInt8

structure ClaimPowReward where
  epochNonce : Fr
  blockHash : Fr
  publicKey : Fr
  nonce : Fr

structure ProgramRegister where
  key : VerificationKey

inductive Op where
  | transfer (t : Transfer)
  | programRegister (r : ProgramRegister)
  | channelConfig (c : ChannelConfig)
  | channelInscribe (m : Inscribe)
  | channelDeposit (d : ChannelDeposit)
  | channelWithdraw (w : ChannelWithdraw)
  | sdpDeclare (d : DeclarationMessage)
  | sdpWithdraw (w : WithdrawMessage)
  | sdpActive (a : Active)
  | claimPowReward (c : ClaimPowReward)

structure ProgramNoteOpening where
  value : ℕ
  nonce : Fr
  publicKey : Fr
  data : Fr

inductive StepProof where
  | user (π : ProofBlob)
  | program (paymentProofs : List ProofBlob) (spend : ProofBlob)
      (programProof : ProofBlob) (openings : List ProgramNoteOpening)

inductive OpProof where
  | zk (π : ProofBlob)
  | inscribe (signature : Fr) (stepProofs : List StepProof)
  | multiSig (signatures : List Fr) (indexes : List ℕ)
  | declare (π : ProofBlob) (providerSig : Fr)
  | withdraw (π : ProofBlob) (providerSig : Fr)
  | sig (s : Fr)
  | empty

structure MantleTx where
  ops : List Op

structure SignedMantleTx where
  tx : MantleTx
  opProofs : List OpProof

/-! ## State -/

structure ChannelState where
  accreditedKeys : List Fr
  configurationThreshold : ℕ
  tipHash : Fr
  configTipHash : Fr
  tipSlot : Slot
  tipSequencer : ℕ
  tipSequencerStartingSlot : Slot
  postingTimeframe : ℕ
  postingTimeout : ℕ
  noteSet : Option ℕ

structure DeclarationInfo where
  service : ℕ
  locators : List (List UInt8)
  providerId : Fr
  zkId : Fr
  serviceNote : Fr
  withdrawOutputs : List Fr
  created : Epoch
  active : Epoch
  withdrawAt : Option Epoch
  nonce : ℕ

structure State where
  sets : ℕ → NoteSet
  numSets : ℕ
  pendingWithdrawals : List (Slot × ℕ × List Fr × List Fr)
  programs : Fr → Option VerificationKey
  channels : ChannelId → Option ChannelState
  declarations : List (DeclarationId × DeclarationInfo)
  powRewardPool : ℕ
  epochPowReward : ℕ
  powNullifiers : Finset Fr

/-- What the specification leaves abstract. Nothing is assumed about these functions; the
properties of the proof verifiers that some theorems use are the classes below. -/
structure Prims where
  H : Hash
  /-- `ZkTransfer_verify(inputs, outputs, excess_value, tx_cm_root, msg, proof)`. -/
  zkTransferVerify : ZkTransferPublic → ProofBlob → Prop
  /-- `ZkProgramSpend_verify(...)`. -/
  zkProgramSpendVerify : ZkProgramSpendPublic → ProofBlob → Prop
  /-- `Groth16_verify(key, public_inputs, proof)`. -/
  groth16Verify : VerificationKey → List Fr → ProofBlob → Prop
  ed25519Verify : Fr → Fr → Fr → Prop
  /-- `mantle_txhash(tx)`: the 32-byte digest. -/
  txHash : MantleTx → Fr
  opId : Op → Fr
  declarationId : DeclarationMessage → DeclarationId
  inscribeHash : Inscribe → Fr
  configHash : ChannelConfig → Fr
  programId : VerificationKey → Fr
  validKey : VerificationKey → Prop
  activityValid : Active → Prop
  encodedSize : SignedMantleTx → ℕ
  maxOpDataSize : ℕ

/-- The block-level inputs of validation. -/
structure Env where
  blockSlot : Slot
  currentEpoch : Epoch
  minStake : ℕ
  epochNonceCurrent : Fr
  epochNoncePrevious : Fr
  powWindow : ℕ
  difficultyReward : ℕ
  canonicalSlot : Fr → Option Slot
  storageGasPrice : ℕ
  executionGasPrice : ℕ

/-- **Knowledge soundness of the ZkTransfer**: a verified proof has a witness satisfying the
circuit. Assumed by the theorems that rest on what a ZkTransfer proves. -/
class Prims.ZkTransferSound (P : Prims) : Prop where
  sound : ∀ {pub π}, P.zkTransferVerify pub π → ∃ w, ZkTransferRel P.H pub w

/-- **Knowledge soundness of the ZkProgramSpend.** -/
class Prims.ZkProgramSpendSound (P : Prims) : Prop where
  sound : ∀ {pub π}, P.zkProgramSpendVerify pub π → ∃ w, ZkProgramSpendRel P.H pub w

/-- **A proof verifies for at most one statement**, so it is bound to its public inputs,
`msg` included. Assumed only by the binding of payments and program spends. -/
class Prims.ProofBinding (P : Prims) : Prop where
  zkTransfer : ∀ {pub pub' π}, P.zkTransferVerify pub π → P.zkTransferVerify pub' π → pub = pub'
  zkProgramSpend : ∀ {pub pub' π}, P.zkProgramSpendVerify pub π →
    P.zkProgramSpendVerify pub' π → pub = pub'

/-! ### The proof hypotheses are satisfiable

`Prims.symbolic` keeps every primitive of `P` but verifies a ZkTransfer or a ZkProgramSpend
proof iff it is the code of a statement that has a witness: it satisfies all three classes and
accepts every true statement (`symbolic_complete`), so the theorems that assume them are not
vacuous. -/

/-- An injective code of the statements. -/
def ZkTransferPublic.code (pub : ZkTransferPublic) : ℕ :=
  Encodable.encode (pub.inputs, pub.outputs, pub.excessValue, pub.txCmRoot, pub.msg)

def ZkProgramSpendPublic.code (pub : ZkProgramSpendPublic) : ℕ :=
  Encodable.encode (pub.inputs, pub.outputs, pub.outputsOfProgram, pub.txCmRoot, pub.programId,
    pub.paidValue, pub.spendNotesHash, pub.msg)

theorem ZkTransferPublic.code_injective : Function.Injective ZkTransferPublic.code := by
  intro a b h
  have := Encodable.encode_injective h
  cases a; cases b; simp_all

theorem ZkProgramSpendPublic.code_injective : Function.Injective ZkProgramSpendPublic.code := by
  intro a b h
  have := Encodable.encode_injective h
  cases a; cases b; simp_all

/-- `P` with symbolic proofs. -/
def Prims.symbolic (P : Prims) : Prims :=
  { P with
    zkTransferVerify := fun pub π => π = pub.code ∧ ∃ w, ZkTransferRel P.H pub w
    zkProgramSpendVerify := fun pub π => π = pub.code ∧ ∃ w, ZkProgramSpendRel P.H pub w }

instance (P : Prims) : P.symbolic.ZkTransferSound := ⟨fun h => h.2⟩
instance (P : Prims) : P.symbolic.ZkProgramSpendSound := ⟨fun h => h.2⟩
instance (P : Prims) : P.symbolic.ProofBinding :=
  ⟨fun h h' => ZkTransferPublic.code_injective (h.1.symm.trans h'.1),
   fun h h' => ZkProgramSpendPublic.code_injective (h.1.symm.trans h'.1)⟩

/-- The symbolic verifiers accept every statement that has a witness. -/
theorem symbolic_complete (P : Prims) :
    (∀ pub w, ZkTransferRel P.H pub w → P.symbolic.zkTransferVerify pub pub.code) ∧
    (∀ pub w, ZkProgramSpendRel P.H pub w → P.symbolic.zkProgramSpendVerify pub pub.code) :=
  ⟨fun _ w h => ⟨rfl, w, h⟩, fun _ w h => ⟨rfl, w, h⟩⟩

namespace State

def setSet (st : State) (i : ℕ) (s : NoteSet) : State :=
  { st with sets := Function.update st.sets i s }

def clearBuffers (st : State) : State :=
  { st with sets := fun i => { st.sets i with buffer := [] } }

/-- Replace the declarations. -/
def withDecls (st : State) (l : List (DeclarationId × DeclarationInfo)) : State :=
  { st with declarations := l }

def updateDecl (st : State) (id : DeclarationId) (f : DeclarationInfo → DeclarationInfo) :
    State :=
  st.withDecls (st.declarations.map fun e => if e.1 = id then (e.1, f e.2) else e)

/-- Replace the pending withdrawals. -/
def withPending (st : State) (l : List (Slot × ℕ × List Fr × List Fr)) : State :=
  { st with pendingWithdrawals := l }

/-- Replace the registered programs. -/
def withPrograms (st : State) (f : Fr → Option VerificationKey) : State :=
  { st with programs := f }

/-- Replace the channels. -/
def withChannels (st : State) (f : ChannelId → Option ChannelState) : State :=
  { st with channels := f }

/-- Replace the proof of work pool and its nullifiers. -/
def withPow (st : State) (pool : ℕ) (nfs : Finset Fr) : State :=
  { st with powRewardPool := pool, powNullifiers := nfs }

/-- `ledger.sets.append(s)`. -/
def addSet (st : State) (s : NoteSet) : State :=
  { st with sets := Function.update st.sets st.numSets s, numSets := st.numSets + 1 }

end State

/-! ## Messages bound into the proofs of the steps -/

section Msgs

variable (H : Hash)

/-- `step_msg(step)`. -/
def stepMsg (u : UserStep) : Fr :=
  H.zkhash (CHANNEL_STEP_V1 :: u.inputs.length :: u.inputs ++ u.outputs.length :: u.outputs)

/-- `payment_msg(program_id, payment)`. -/
def paymentMsg (pid : Fr) (p : Payment) : Fr :=
  H.zkhash (PROGRAM_PAYMENT_V1 :: pid :: p.intent :: p.inputs.length :: p.inputs ++
    p.outputs.length :: p.outputs)

/-- `payments_hash(step)`. -/
def paymentsHash (ps : ProgramStep) : Fr :=
  H.zkhash (PROGRAM_PAYMENTS_V1 :: ps.payments.length ::
    ps.payments.flatMap fun p => [p.paidValue, p.intent])

end Msgs

/-- The commitments of the outputs of a program step flagged as notes of the program. -/
def programCms (ps : ProgramStep) : List Fr :=
  (ps.outputs.zip ps.programOutputs).filterMap fun c => if c.2 then some c.1 else none

/-! ## Operations -/

variable (P : Prims) (E : Env)

/-- `TRANSFER`. -/
def applyTransfer (st : State) (txh : Fr) (t : Transfer) (π : ProofBlob) :
    Option (State × ℕ) := do
  let s := st.sets LEDGER_SET
  ensure (s.Spendable t.inputs t.cmMerkleRoot)
  let R ← s.txCmRoot P.H t.cmMerkleRoot none
  ensure (P.zkTransferVerify ⟨t.inputs, t.outputs, t.excessValue, R, toFr txh⟩ π)
  pure (st.setSet LEDGER_SET
    (((s.extendBuffer t.outputs).executeSpending t.inputs).executeAdding t.outputs), t.excessValue)

/-- `CHANNEL_DEPOSIT`. -/
def applyDeposit (st : State) (txh : Fr) (d : ChannelDeposit) (π : ProofBlob) :
    Option (State × ℕ) := do
  ensure (d.metadata.length ≤ P.maxOpDataSize)
  let chan ← st.channels d.channel
  let j ← chan.noteSet
  let s := st.sets LEDGER_SET
  ensure (s.Spendable d.inputs d.cmMerkleRoot)
  let R ← s.txCmRoot P.H d.cmMerkleRoot none
  ensure (P.zkTransferVerify ⟨d.inputs, d.outputs, d.excessValue, R, toFr txh⟩ π)
  let st1 := st.setSet j ((st.sets j).extendBuffer d.outputs)
  let st2 := st1.setSet LEDGER_SET ((st1.sets LEDGER_SET).executeSpending d.inputs)
  pure (st2.setSet j ((st2.sets j).executeAdding d.outputs), d.excessValue)

/-- `CHANNEL_WITHDRAW`: kept until its due slot. -/
def applyChannelWithdraw (st : State) (txh : Fr) (w : ChannelWithdraw) (π : ProofBlob) :
    Option (State × ℕ) := do
  let chan ← st.channels w.channel
  let j ← chan.noteSet
  let s := st.sets j
  ensure (s.Spendable w.inputs w.cmMerkleRoot)
  let R ← s.txCmRoot P.H w.cmMerkleRoot none
  ensure (P.zkTransferVerify ⟨w.inputs, w.outputs, 0, R, toFr txh⟩ π)
  pure (st.withPending
    (st.pendingWithdrawals ++ [(E.blockSlot + WITHDRAW_DELAY, j, w.inputs, w.outputs)]), 0)

/-- The service note of a declaration. -/
def serviceNote (d : DeclarationMessage) : Note :=
  ⟨d.amount, noteNonce P.H (P.opId (.sdpDeclare d)) 0 d.amount d.zkId, d.zkId, 0, 0⟩

/-- `SDP_DECLARE`. -/
def applyDeclare (st : State) (txh : Fr) (d : DeclarationMessage) (π : ProofBlob) (sig : Fr) :
    Option (State × ℕ) := do
  let s := st.sets LEDGER_SET
  let R ← s.txCmRoot P.H d.cmMerkleRoot none
  ensure (P.zkTransferVerify ⟨d.inputs, [], d.amount, R, toFr txh⟩ π)
  ensure (P.ed25519Verify txh d.providerId sig)
  ensure (st.declarations.lookup (P.declarationId d) = none)
  ensure (1 ≤ d.locators.length ∧ d.locators.length ≤ 8)
  ensure (s.Spendable d.inputs d.cmMerkleRoot)
  ensure (E.minStake ≤ d.amount)
  let cm := noteCm P.H (serviceNote P d)
  let st1 := st.setSet LEDGER_SET (s.executeSpending d.inputs)
  let st2 := st1.setSet SDP_SET ((st1.sets SDP_SET).executeAdding [cm])
  pure (st2.withDecls (st2.declarations ++
    [(P.declarationId d, ⟨d.serviceType, d.locators, d.providerId, d.zkId, cm, [],
      E.currentEpoch, E.currentEpoch + 2, none, 0⟩)]), 0)

/-- `SDP_WITHDRAW`. -/
def applySdpWithdraw (st : State) (txh : Fr) (w : WithdrawMessage) (π : ProofBlob) (sig : Fr) :
    Option (State × ℕ) := do
  let info ← st.declarations.lookup w.declaration
  ensure (info.withdrawAt = none)
  ensure (P.ed25519Verify txh info.providerId sig)
  ensure (info.nonce < w.nonce)
  ensure (w.serviceNoteNf ∉ (st.sets SDP_SET).nullifiers)
  ensure (P.zkTransferVerify ⟨[w.serviceNoteNf], w.outputs, w.excessValue,
    mmrRoot P.H (mmrPeaks P.H [info.serviceNote]), toFr txh⟩ π)
  let st1 := st.updateDecl w.declaration fun i =>
    { i with nonce := w.nonce, withdrawAt := some (E.currentEpoch + 2),
             withdrawOutputs := w.outputs }
  pure (st1.setSet SDP_SET ((st1.sets SDP_SET).executeSpending [w.serviceNoteNf]), w.excessValue)

/-- `SDP_ACTIVE`. -/
def applyActive (st : State) (txh : Fr) (a : Active) (sig : Fr) : Option (State × ℕ) := do
  let info ← st.declarations.lookup a.declaration
  ensure (info.nonce < a.nonce)
  ensure (P.ed25519Verify txh info.providerId sig)
  ensure (P.activityValid a)
  pure (st.updateDecl a.declaration fun i => { i with nonce := a.nonce, active := E.currentEpoch },
    0)

/-- The reward note of a proof of work claim. -/
def powNote (st : State) (c : ClaimPowReward) : Note :=
  ⟨st.epochPowReward, noteNonce P.H (P.opId (.claimPowReward c)) 0 st.epochPowReward c.publicKey,
    c.publicKey, 0, 0⟩

/-- `CLAIM_POW_REWARD`. -/
def applyClaimPow (st : State) (c : ClaimPowReward) : Option (State × ℕ) := do
  ensure (0 < st.epochPowReward)
  ensure (st.epochPowReward ≤ st.powRewardPool)
  let slot ← E.canonicalSlot c.blockHash
  ensure (slot ≤ E.blockSlot ∧ E.blockSlot - slot ≤ E.powWindow)
  ensure (c.epochNonce = E.epochNonceCurrent ∨ c.epochNonce = E.epochNoncePrevious)
  let ticket := P.H.zkhash [c.publicKey, c.nonce, c.blockHash, c.epochNonce]
  ensure (ticket < E.difficultyReward)
  ensure (ticket ∉ st.powNullifiers)
  let cm := noteCm P.H (powNote P st c)
  let s := st.sets LEDGER_SET
  pure ((st.withPow (st.powRewardPool - st.epochPowReward) (insert ticket st.powNullifiers)).setSet
    LEDGER_SET ((s.extendBuffer [cm]).executeAdding [cm]), 0)

/-- `PROGRAM_REGISTER`. -/
def applyRegister (st : State) (r : ProgramRegister) : Option (State × ℕ) := do
  ensure (P.validKey r.key)
  let pid := P.programId r.key
  pure (if st.programs pid = none then
    st.withPrograms (Function.update st.programs pid (some r.key)) else st, 0)

/-! ### Channels -/

/-- `default_channel(block_slot, keys, note_set)`. -/
def defaultChannel (slot : Slot) (keys : List Fr) (noteSet : Option ℕ) : ChannelState :=
  ⟨keys, 1, 0, 0, slot, 0, slot, 0, 0, noteSet⟩

/-- `create_channel(channel_id, block_slot, keys)`: the null channel gets no note set, any
other channel the next one. -/
def createChannel (st : State) (id : ChannelId) (slot : Slot) (keys : List Fr) : State :=
  if id = 0 then
    st.withChannels (Function.update st.channels id (some (defaultChannel slot keys none)))
  else
    (st.addSet (NoteSet.empty P.H)).withChannels
      (Function.update st.channels id (some (defaultChannel slot keys (some st.numSets))))

/-- `round_robin(block_slot, channel)`. -/
def roundRobin (slot : Slot) (c : ChannelState) : ℕ × Slot :=
  let elapsed := slot - c.tipSlot
  if c.postingTimeout ≤ elapsed ∧ c.postingTimeout ≠ 0 then
    let k := elapsed / c.postingTimeout
    ((c.tipSequencer + k) % c.accreditedKeys.length, c.tipSlot + k * c.postingTimeout)
  else if c.postingTimeframe = 0 then
    (c.tipSequencer, c.tipSequencerStartingSlot)
  else
    let d := slot - c.tipSequencerStartingSlot
    ((c.tipSequencer + d / c.postingTimeframe) % c.accreditedKeys.length,
      c.tipSequencerStartingSlot + d / c.postingTimeframe * c.postingTimeframe)

/-- `MultiEd25519_verify(msg, signatures, indexes, keys, threshold)`. -/
def MultiSigOk (msg : Fr) (sigs : List Fr) (idx : List ℕ) (keys : List Fr) (threshold : ℕ) :
    Prop :=
  sigs.length = idx.length ∧ sigs.length = threshold ∧ idx.IsChain (· < ·) ∧
    ∀ p ∈ sigs.zip idx, ∃ k, keys[p.2]? = some k ∧ P.ed25519Verify msg k p.1

/-- `CHANNEL_CONFIG`. -/
def applyConfig (st : State) (txh : Fr) (c : ChannelConfig) (sigs : List Fr) (idx : List ℕ) :
    Option (State × ℕ) := do
  ensure (0 < c.configurationThreshold)
  ensure (0 < c.keys.length ∧ c.keys.length < 2 ^ 16)
  ensure (c.configurationThreshold ≤ c.keys.length)
  match st.channels c.channel with
  | some chan =>
    ensure (c.parent = chan.configTipHash)
    ensure (MultiSigOk P txh sigs idx chan.accreditedKeys chan.configurationThreshold)
  | none =>
    ensure (c.parent = 0)
    ensure (MultiSigOk P txh sigs idx [] 0)
  let st1 := if (st.channels c.channel).isSome then st
    else createChannel P st c.channel E.blockSlot c.keys
  let chan ← st1.channels c.channel
  pure (st1.withChannels (Function.update st1.channels c.channel (some
    { chan with accreditedKeys := c.keys, configurationThreshold := c.configurationThreshold,
                tipSlot := E.blockSlot, tipSequencer := 0, tipSequencerStartingSlot := E.blockSlot,
                postingTimeframe := c.postingTimeframe, postingTimeout := c.postingTimeout,
                configTipHash := P.configHash c })), 0)

/-- The payments of a program step, validated in order: each is spendable, consumes no note
an earlier step or payment consumed (`nfs`, the `step_nfs` of the specification), covers at
most the buffer, and its ZkTransfer verifies with `payment_msg` and an excess of its
`paid_value`; its change goes to the buffer. Returns the set, the nullifiers and the total
paid value. -/
def validatePayments (pid : Fr) : NoteSet → Finset Fr → List Payment → List ProofBlob →
    Option (NoteSet × Finset Fr × ℕ)
  | s, nfs, [], [] => some (s, nfs, 0)
  | s, nfs, p :: ps, π :: πs => do
    ensure (s.Spendable p.inputs p.cmMerkleRoot)
    ensure (∀ nf ∈ p.inputs, nf ∉ nfs)
    ensure (p.buffered ≤ s.buffer.length)
    let R ← s.txCmRoot P.H p.cmMerkleRoot (some p.buffered)
    ensure (P.zkTransferVerify ⟨p.inputs, p.outputs, p.paidValue, R, paymentMsg P.H pid p⟩ π)
    let (s', nfs', paid) ← validatePayments pid (s.extendBuffer p.outputs)
      (nfs ∪ p.inputs.toFinset) ps πs
    ensure (p.paidValue + paid < TOKEN_BOUND)
    pure (s', nfs', p.paidValue + paid)
  | _, _, _, _ => none

/-- The steps of an inscription, validated in order against the set `s`, whose buffer the
validation extends, and the nullifiers `nfs` consumed by the earlier steps. -/
def validateSteps (opIdFr : Fr) (programs : Fr → Option VerificationKey) :
    NoteSet → Finset Fr → List Step → List StepProof → Option NoteSet
  | s, _, [], [] => some s
  | s, nfs, .user u :: rest, .user π :: πs => do
    ensure (s.Spendable u.inputs u.cmMerkleRoot)
    ensure (∀ nf ∈ u.inputs, nf ∉ nfs)
    ensure (u.buffered ≤ s.buffer.length)
    let R ← s.txCmRoot P.H u.cmMerkleRoot (some u.buffered)
    ensure (P.zkTransferVerify ⟨u.inputs, u.outputs, 0, R, stepMsg P.H u⟩ π)
    validateSteps opIdFr programs (s.extendBuffer u.outputs) (nfs ∪ u.inputs.toFinset) rest πs
  | s, nfs, .program ps :: rest, .program pπs spend gπ openings :: πs => do
    let key ← programs ps.programId
    let (s1, nfs1, paid) ← validatePayments P ps.programId s nfs ps.payments pπs
    ensure (if ps.inputs ≠ [] then s1.Spendable ps.inputs ps.cmMerkleRoot
      else (s1.recentRoots ps.cmMerkleRoot).isSome)
    ensure (ps.inputs.Nodup ∧ ∀ nf ∈ ps.inputs, nf ∉ nfs1)
    ensure (ps.programOutputs.length = ps.outputs.length)
    let R ← s1.txCmRoot P.H ps.cmMerkleRoot none
    ensure (P.zkProgramSpendVerify ⟨ps.inputs, ps.outputs, ps.programOutputs, R, ps.programId,
      paid, ps.spendNotesHash, opIdFr⟩ spend)
    ensure (List.Forall₂ (fun cm (o : ProgramNoteOpening) =>
      cm = noteCm P.H ⟨o.value, o.nonce, o.publicKey, ps.programId, o.data⟩)
      (programCms ps) openings)
    ensure (P.groth16Verify key [ps.spendNotesHash, paymentsHash P.H ps, opIdFr] gπ)
    validateSteps opIdFr programs (s1.extendBuffer ps.outputs) (nfs1 ∪ ps.inputs.toFinset)
      rest πs
  | _, _, _, _ => none

/-- The nullifiers a step consumes, payments first. -/
def Step.ins : Step → List Fr
  | .user u => u.inputs
  | .program ps => ps.payments.flatMap (·.inputs) ++ ps.inputs

/-- The commitments a step creates, in the order they reach the buffer and the MMR. -/
def Step.outs : Step → List Fr
  | .user u => u.outputs
  | .program ps => ps.payments.flatMap (·.outputs) ++ ps.outputs

/-- Execution of one payment. -/
def executePayment (s : NoteSet) (p : Payment) : NoteSet :=
  (s.executeSpending p.inputs).executeAdding p.outputs

/-- Execution of one step: the payments of a program step, then its program spend. -/
def executeStep (s : NoteSet) : Step → NoteSet
  | .user u => (s.executeSpending u.inputs).executeAdding u.outputs
  | .program ps =>
    ((ps.payments.foldl executePayment s).executeSpending ps.inputs).executeAdding ps.outputs

/-- Execution of the steps of an inscription, in their order. -/
def executeSteps (s : NoteSet) (steps : List Step) : NoteSet := steps.foldl executeStep s

/-- The validation of `CHANNEL_INSCRIBE`: the inscription continues or creates its channel and
is signed by its sequencer, the null channel receives no step, and the steps validate against
the note set of the channel (a new empty set for a channel being created). Returns that set,
its buffer extended by the validation, if the channel has one. -/
def validateInscribe (st : State) (txh opIdFr : Fr) (m : Inscribe) (sig : Fr)
    (πs : List StepProof) : Option (Option NoteSet) := do
  ensure (m.inscription.length ≤ P.maxOpDataSize)
  let ns ← match st.channels m.channel with
    | some chan => do
      ensure (chan.accreditedKeys[(roundRobin E.blockSlot chan).1]? = some m.signer)
      ensure (m.parent = chan.tipHash)
      pure (chan.noteSet.map st.sets)
    | none => do
      ensure (m.parent = 0)
      pure (if m.channel ≠ 0 then some (NoteSet.empty P.H) else none)
  ensure (P.ed25519Verify txh m.signer sig)
  ensure (ns.isSome ∨ m.steps = [])
  ensure (πs.length = m.steps.length)
  match ns with
  | some s => (validateSteps P opIdFr st.programs s ∅ m.steps πs).map some
  | none => pure none

/-- The execution of the steps of `CHANNEL_INSCRIBE`: on the validated set of an existing
channel, or on the note set a channel being created gets. -/
def executeInscribeSteps (st : State) (m : Inscribe) (validated : Option NoteSet) : State :=
  match st.channels m.channel with
  | some chan =>
    match chan.noteSet, validated with
    | some j, some sv => st.setSet j (executeSteps sv m.steps)
    | _, _ => st
  | none =>
    let st' := createChannel P st m.channel E.blockSlot [m.signer]
    if m.channel ≠ 0 then st'.setSet st.numSets (executeSteps (st'.sets st.numSets) m.steps)
    else st'

/-- `CHANNEL_INSCRIBE`. -/
def applyInscribe (st : State) (txh opIdFr : Fr) (m : Inscribe) (sig : Fr)
    (πs : List StepProof) : Option (State × ℕ) := do
  let validated ← validateInscribe P E st txh opIdFr m sig πs
  let st1 := executeInscribeSteps P E st m validated
  let chan ← st1.channels m.channel
  let rr := roundRobin E.blockSlot chan
  pure (st1.withChannels (Function.update st1.channels m.channel (some
    { chan with tipSequencerStartingSlot := rr.2, tipSequencer := rr.1,
                tipHash := P.inscribeHash m, tipSlot := E.blockSlot })), 0)

/-! ## Operations and transactions -/

/-- `validate_mantle_op` then `execute_mantle_op`: the new state and what the Operation adds
to `tx_balance`. -/
def applyOp (st : State) (txh : Fr) (op : Op) (proof : OpProof) : Option (State × ℕ) :=
  match op, proof with
  | .transfer t, .zk π => applyTransfer P st txh t π
  | .programRegister r, .empty => applyRegister P st r
  | .channelConfig c, .multiSig sigs idx => applyConfig P E st txh c sigs idx
  | .channelInscribe m, .inscribe sig πs => applyInscribe P E st txh (P.opId op) m sig πs
  | .channelDeposit d, .zk π => applyDeposit P st txh d π
  | .channelWithdraw w, .zk π => applyChannelWithdraw P E st txh w π
  | .sdpDeclare d, .declare π sig => applyDeclare P E st txh d π sig
  | .sdpWithdraw w, .withdraw π sig => applySdpWithdraw P E st txh w π sig
  | .sdpActive a, .sig s => applyActive P E st txh a s
  | .claimPowReward c, .empty => applyClaimPow P E st c
  | _, _ => none

/-- The Execution Gas of a step. -/
def Step.gas : Step → ℕ
  | .user _ => EXECUTION_TRANSFER_GAS
  | .program ps => programStepGas ps.payments.length

/-- The Execution Gas of an Operation, against the state it is validated against. -/
def executionGas (st : State) : Op → ℕ
  | .transfer _ => EXECUTION_TRANSFER_GAS
  | .programRegister _ => EXECUTION_PROGRAM_REGISTER_GAS
  | .channelConfig c =>
    EXECUTION_CHANNEL_CONFIG_GAS * ((st.channels c.channel).map (·.configurationThreshold)).getD 0
  | .channelInscribe m => EXECUTION_CHANNEL_INSCRIBE_GAS + (m.steps.map Step.gas).sum
  | .channelDeposit _ => EXECUTION_CHANNEL_DEPOSIT_GAS
  | .channelWithdraw _ => EXECUTION_CHANNEL_WITHDRAW_GAS
  | .sdpDeclare _ => EXECUTION_SDP_DECLARE_GAS
  | .sdpWithdraw _ => EXECUTION_SDP_WITHDRAW_GAS
  | .sdpActive _ => EXECUTION_SDP_ACTIVE_GAS
  | .claimPowReward _ => EXECUTION_CLAIM_POW_REWARD_GAS

/-- The Operations of a transaction in order, each validated against the state the previous
ones left: the final state, `tx_balance` and the total Execution Gas. -/
def applyOps (st : State) (txh : Fr) : List Op → List OpProof → Option (State × ℕ × ℕ)
  | [], [] => some (st, 0, 0)
  | op :: ops, π :: πs => do
    let (st1, fee) ← applyOp P E st txh op π
    let (st2, bal, gas) ← applyOps st1 txh ops πs
    ensure (fee + bal < TOKEN_BOUND)
    ensure (executionGas st op + gas < TOKEN_BOUND)
    pure (st2, fee + bal, executionGas st op + gas)
  | _, _ => none

/-- `mandatory_fees`, with its checked products. -/
def mandatoryFee (size gas : ℕ) : Option ℕ := do
  let storage := size * E.storageGasPrice
  let exec := gas * E.executionGasPrice
  ensure (storage < TOKEN_BOUND ∧ exec < TOKEN_BOUND ∧ storage + exec < TOKEN_BOUND)
  pure (storage + exec)

/-- A Mantle Transaction: the new state, the mandatory fee and the priority tip. -/
def applyTx (st : State) (stx : SignedMantleTx) : Option (State × ℕ × ℕ) := do
  ensure (stx.opProofs.length = stx.tx.ops.length)
  let (st', bal, gas) ← applyOps P E st.clearBuffers (P.txHash stx.tx) stx.tx.ops stx.opProofs
  let fee ← mandatoryFee E (P.encodedSize stx) gas
  ensure (fee ≤ bal)
  pure (st', fee, bal - fee)

/-! ## Block-level steps -/

/-- One pending withdrawal at `release_withdrawals(block_slot)`: kept if not due, applied if
its inputs are still unspent, dropped otherwise. -/
def releaseOne (slot : Slot) (acc : State × List (Slot × ℕ × List Fr × List Fr))
    (w : Slot × ℕ × List Fr × List Fr) : State × List (Slot × ℕ × List Fr × List Fr) :=
  let (st, pending) := acc
  let (due, j, ins, outs) := w
  if slot < due then (st, pending ++ [w])
  else if ∀ nf ∈ ins, nf ∉ (st.sets j).nullifiers then
    let st1 := st.setSet j ((st.sets j).executeSpending ins)
    (st1.setSet LEDGER_SET ((st1.sets LEDGER_SET).executeAdding outs), pending)
  else (st, pending)

/-- `release_withdrawals(block_slot)`. -/
def releaseWithdrawals (st : State) (slot : Slot) : State :=
  let r := st.pendingWithdrawals.foldl (releaseOne slot) (st, [])
  r.1.withPending r.2

/-- The declarations SDP Epoch Finalization removes at `epoch`. -/
def IsDue (epoch : Epoch) (e : DeclarationId × DeclarationInfo) : Prop :=
  ∃ w, e.2.withdrawAt = some w ∧ w + 1 ≤ epoch

/-- The order of SDP Epoch Finalization: "ascending lexicographic order of the 32 bytes of
`declare_id`". -/
def declIdLe (a b : DeclarationId) : Bool :=
  Encoding.Codec.lexLe (Encoding.Codec.leBytes 32 a) (Encoding.Codec.leBytes 32 b)

/-- `declIdLe` on the entries of `declarations`. -/
def releaseOrder (a b : DeclarationId × DeclarationInfo) : Bool := declIdLe a.1 b.1

/-- SDP Epoch Finalization: in ascending byte order of `declare_id`, release the notes of every
due declaration in the ledger set and remove it. -/
def finalizeDeclarations (st : State) (epoch : Epoch) : State :=
  let due := (st.declarations.filter fun e => decide (IsDue epoch e)).mergeSort releaseOrder
  let s := due.foldl (fun s e => s.executeAdding e.2.withdrawOutputs) (st.sets LEDGER_SET)
  (st.setSet LEDGER_SET s).withDecls (st.declarations.filter fun e => !decide (IsDue epoch e))

end

end Mantle
