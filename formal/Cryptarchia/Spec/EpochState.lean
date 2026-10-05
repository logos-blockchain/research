import Cryptarchia.Spec.Chain
import Cryptarchia.Spec.Lottery
import Cryptarchia.Spec.StakeInference

/-!
# Cryptarchia: epoch state, derived on a chain

`cryptarchia-v1-protocol.md`: *Epoch*, *Epoch Schedule*, *Eligible Leader Notes*,
*Epoch Nonce*, *Total Stake Inference*, *Epoch State Pseudocode*;
`cryptarchia-proof-of-leadership.md`: *Circuit Constraints*;
`bedrock-genesis-block.md`: *Initial Epoch State*.

The epoch state `(C_LEAD, η, D)` of epoch `ep` is derived **on a chain**: two
forks can hold different states. Everything here is a function of the chain's
blocks with slot below `epochStart ep`, so the state of epoch `ep` is fixed once
a chain reaches epoch `ep`.

* `C_LEAD`: the notes present after the last block with slot strictly below
  `epochStart (ep - 1)` (genesis for `ep ≤ 1`). The specification says "at slot
  `sl_{ep-1}`"; the implementation takes the state after the last block strictly
  before it (`ledger/src/cryptarchia/mod.rs:145-155`), which the model follows.
* `η`: the nonce after the last block with slot strictly below
  `epochStart (ep - 1) + 6⌊k/f⌋`, the start of the lottery constants finalization
  phase; each block evolves it as `η_B = H(η_parent, ρ_B, sl_B)`.
* `D`: `D^0 = D_GENESIS`; `D^ep = infer(D^(ep-1), N^(ep-1))`, where `N^(ep-1)` is
  the number of distinct occupied slots in the first `6⌊k/f⌋` slots of epoch
  `ep - 1`: slots of the chain's blocks in that window, and slots in that window
  of the uncles those in-window blocks carry.

**The ledger** (Mantle notes and transactions) is abstract: a function from a
chain to the notes it holds. Honest and adversarial blocks carry abstract
payloads; which transactions exist, and whether a block's transactions execute,
is the ledger's business (`Ledger.execOK`).
-/

namespace Cryptarchia

/-- A note: its identifier, its value, and who holds its secret key. -/
structure Note where
  id : ℕ
  value : ℕ
  owner : Signer
  deriving DecidableEq, Repr

/-- The ledger, abstractly: the notes held after executing a chain (genesis
first), and whether a block's transactions execute on its parent's state. -/
structure Ledger where
  notes : List Block → List Note
  execOK : List Block → Bool

/-- The random oracle (Poseidon2), as three functions:
* `ticket η sl note` = `hash(LEAD_V1 ‖ η ‖ sl ‖ noteID ‖ sk)`, a value in `[0, p)`;
* `rho sl note` = `hash(NONCE_CONTRIB_V1 ‖ sl ‖ noteID ‖ sk)`;
* `nonce η ρ sl` = `zkHASH(EPOCH_NONCE_V1 ‖ η ‖ ρ ‖ Fr(sl))`. -/
structure Oracle where
  ticket : ℕ → ℕ → ℕ → ℕ
  rho : ℕ → ℕ → ℕ
  nonce : ℕ → ℕ → ℕ → ℕ

/-- The genesis epoch state: `genesis_epoch_nonce`, and the total tokens
distributed at genesis as `D_GENESIS`. -/
structure Genesis where
  nonce : ℕ
  D : ℕ

/-- The epoch state `(C_LEAD, η, D)`. -/
structure EpochState where
  lead : List Note
  eta : ℕ
  D : ℕ

variable (c : Config) (st : Store) (L : Ledger) (O : Oracle) (G : Genesis)

/-- The chain of `b`, **genesis first**. -/
def chainUp (b : ℕ) : List Block := (chain st b).reverse

/-- The prefix of a chain (genesis first) of blocks with slot below `s`, always
keeping genesis. -/
def prefixBelow (C : List Block) (s : ℕ) : List Block :=
  C.filter (fun x => x.hdr.id = genesisId ∨ x.hdr.slot < s)

/-- The nonce after the last block of a chain (genesis first). -/
def nonceAfter (C : List Block) : ℕ :=
  C.foldl (fun η x => if x.hdr.id = genesisId then η
    else O.nonce η (O.rho x.hdr.slot x.hdr.note) x.hdr.slot) G.nonce

/-- The window of the total stake inference for epoch `e`:
`epochStart e ≤ sl < epochStart e + PERIOD`. -/
def inWindow (e sl : ℕ) : Bool :=
  decide (c.epochStart e ≤ sl ∧ sl < c.epochStart e + c.period)

/-- **`N^e`**: distinct occupied slots in epoch `e`'s window: slots of the
chain's blocks in the window, and window slots of the uncles those in-window
blocks carry. -/
def occupied (C : List Block) (e : ℕ) : ℕ :=
  let inW := C.filter (fun x => inWindow c e x.hdr.slot)
  let own := inW.map (·.hdr.slot)
  let unc := (inW.flatMap (·.uncles)).map (·.slot) |>.filter (inWindow c e)
  (own ++ unc).dedup.length

/-- **`D^ep`** on a chain (genesis first). -/
def stakeEstimate (C : List Block) : ℕ → ℕ
  | 0 => G.D
  | e + 1 => infer c (stakeEstimate C e) (occupied c C e)

/-- **The epoch state of epoch `ep`**, derived on a chain (genesis first). -/
def epochState (C : List Block) (ep : ℕ) : EpochState :=
  let C := prefixBelow C (c.epochStart ep)
  { lead := L.notes (prefixBelow C (c.epochStart (ep - 1)))
    eta := if ep = 0 then G.nonce else nonceAfter O G (prefixBelow C (c.epochStart (ep - 1) + c.nonceOffset))
    D := stakeEstimate c G C ep }

/-- **Proof of Leadership, ideal.** Header `h` proves a lottery win for slot
`h.slot`, with the epoch state derived on chain `C` (genesis first) and the
unspent check against the notes after chain `P` (the chain of the parent):
the note is held by the signer, is in `C_LEAD`, is unspent, and its ticket is
below the threshold for its value. -/
def polValid (C P : List Block) (h : Header) : Bool :=
  let es := epochState c L O G C (c.epochOf h.slot)
  es.lead.any (fun n => n.id = h.note ∧ n.owner = h.signer ∧ (L.notes P).contains n ∧
    wins c es.D n.value (O.ticket es.eta h.slot n.id))

end Cryptarchia
