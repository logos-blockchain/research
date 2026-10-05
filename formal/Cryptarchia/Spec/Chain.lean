import Cryptarchia.Spec.Params

/-!
# Cryptarchia: blocks, chains and the block tree

`cryptarchia-v1-protocol.md`: *Block Header*, *Uncle References*, *Notation*;
`fork-choice.md`: *Definitions* (`common_prefix_depth`, `density`).

**Idealisation of the cryptography.** Block IDs are collision-free (a block is
named by its ID); signatures are unforgeable (a header names who signed it, and
only that party can have created it); the Proof of Leadership is a sound and
zero-knowledge proof (a header names the note it proves a win for, and validity
checks that the note really won). Poseidon2 is a random oracle (see
`Lottery.lean`). The header fields the model does not need (`bedrock_version`,
`body_root`, the Groth16 proof bytes, the leader key) are folded into `payload`
and `note`.

The **global store** `st` holds every block ever created, by anyone; a node's
**block tree** is the list of IDs it has accepted.
-/

namespace Cryptarchia

/-- Who signed a header: honest node `i`, or the adversary. -/
inductive Signer
  | honest (i : ℕ)
  | adv
  deriving DecidableEq, Repr

/-- A block header (`Header`, 297 bytes in the specification). -/
structure Header where
  id : ℕ
  parent : ℕ
  slot : ℕ
  /-- The note whose lottery win the Proof of Leadership proves. -/
  note : ℕ
  /-- The holder of the one-time leader key that signed the header. -/
  signer : Signer
  /-- The body commitment (transactions), abstract. -/
  payload : ℕ
  deriving DecidableEq, Repr

/-- A block: its header and the signed headers of the uncles it references
(`uncle_headers`, at most `MAX_UNCLES`, enforced at decoding). -/
structure Block where
  hdr : Header
  uncles : List Header
  deriving DecidableEq, Repr

/-- The ID of the genesis block. -/
def genesisId : ℕ := 0

/-- The global store: every block ever created, by ID. -/
abbrev Store := ℕ → Option Block

variable (st : Store)

/-- The chain ending at `b`, **tip first**, down to genesis (`ancestors(b)`,
including `b`). The fuel bounds the length; valid blocks have strictly increasing
slots along the chain, so `slot + 1` is always enough (`chain`). A chain whose
walk hits an unknown ID stops there. -/
def chainF : ℕ → ℕ → List Block
  | 0, _ => []
  | n + 1, b => match st b with
    | none => []
    | some blk => if b = genesisId then [blk] else blk :: chainF n blk.hdr.parent

/-- The chain of `b`, tip first. -/
def chain (b : ℕ) : List Block :=
  match st b with
  | none => []
  | some blk => chainF st (blk.hdr.slot + 2) b

/-- The IDs of the chain of `b`, tip first. -/
def chainIds (b : ℕ) : List ℕ := (chain st b).map (·.hdr.id)

/-- `is_ancestor(a, b)`: `a` is on the chain of `b` (a block is its own ancestor). -/
def isAncestor (a b : ℕ) : Bool := (chainIds st b).contains a

/-- Height: the number of blocks above genesis. -/
def height (b : ℕ) : ℕ := (chain st b).length - 1

/-- The slot of a block (`0` for unknown IDs). -/
def slotOf (b : ℕ) : ℕ := match st b with
  | none => 0
  | some blk => blk.hdr.slot

/-- The parent of a block. -/
def parentOf (b : ℕ) : ℕ := match st b with
  | none => b
  | some blk => blk.hdr.parent

/-- The latest common ancestor of `a` and `b`: the first block of `a`'s chain
(tip first) that is also on `b`'s chain. -/
def lca (a b : ℕ) : ℕ := ((chainIds st a).find? (fun x => (chainIds st b).contains x)).getD genesisId

/-- **`common_prefix_depth(a, b)`**: how far each tip is above the common ancestor. -/
def commonPrefixDepth (a b : ℕ) : ℕ × ℕ :=
  let l := lca st a b
  (height st a - height st l, height st b - height st l)

/-- `block_at_depth(b, d)`: the `d`-th ancestor of `b`, or genesis if the chain
is shorter. -/
def blockAtDepth (b d : ℕ) : ℕ := ((chainIds st b)[d]?).getD genesisId

/-- **`density(b, d, s_gen)`**: the number of blocks of the chain of `b` in the
`s_gen` slots following its `d`-th ancestor, i.e. with slot in
`(slot(b_{i-d}), slot(b_{i-d}) + s_gen]`. Uncles are not counted
(`fork-choice.md` rev 1.1.0). -/
def density (b d sGen : ℕ) : ℕ :=
  let s0 := slotOf st (blockAtDepth st b d)
  ((chain st b).filter (fun x => s0 < x.hdr.slot ∧ x.hdr.slot ≤ s0 + sGen)).length

/-- The tips `F_T` of a block tree `T`: blocks of `T` that are no block's parent
in `T`. -/
def tips (T : List ℕ) : List ℕ := T.filter (fun b => !(T.any (fun c => c ≠ b ∧ parentOf st c = b)))

end Cryptarchia
