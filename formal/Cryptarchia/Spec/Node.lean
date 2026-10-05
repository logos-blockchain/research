import Cryptarchia.Spec.ForkChoice
import Cryptarchia.Spec.EpochState

/-!
# Cryptarchia: validation, chain maintenance, and the honest proposer

`cryptarchia-v1-protocol.md`: *Block Header Validation* (steps 5–10; steps 1–4
are serialization and size checks, which the model does not represent),
*Uncle References*, *Uncle Selection*, *Chain Maintenance*, *Commit*,
*Fork Pruning*; `cryptarchia-v1-bootstr-sync.md`: *Proposing New Blocks*.

**Two readings of `on_block`.** The specification sets `c_loc' = B` when
`parent(B) = c_loc`, and runs fork choice otherwise. The implementation always
runs fork choice over all tips (`consensus/cryptarchia-engine/src/lib.rs:469`).
The flag `fastPath` selects between them; theorems quantify over both.
-/

namespace Cryptarchia

variable (c : Config) (st : Store) (L : Ledger) (O : Oracle) (G : Genesis)

/-- A node's consensus state `(c_loc, B_imm, T)`, and the fork choice rule it
runs. -/
structure NodeState where
  cloc : ℕ
  bimm : ℕ
  tree : List ℕ
  rule : Rule
  deriving DecidableEq, Repr

/-- The header of a stored block is genuine: the carried header is exactly the
header that its signer created (signatures are unforgeable). -/
def genuine (h : Header) : Bool :=
  match st h.id with
  | none => false
  | some b => b.hdr = h

/-- **`valid_uncle(U, A)`**: `A` extends `parent`. The parent of `U` is on `A`'s
chain, `U` is not, `U` precedes `A`, `U`'s parent is at most `⌊W/f⌋` slots before
`A`, `U`'s Proof of Leadership verifies against the epoch state derived on `A`'s
chain and the notes as of `U`'s parent, and its signature verifies. -/
def validUncle (parent slotA : ℕ) (U : Header) : Bool :=
  let ids := chainIds st parent
  ids.contains U.parent && !ids.contains U.id && decide (U.slot < slotA) &&
    decide (slotA - slotOf st U.parent ≤ c.uncleWindow) &&
    polValid c L O G (chainUp st parent) (chainUp st U.parent) U && genuine st U

/-- **`valid_header(B)`** for a node with block tree `T` and latest immutable block
`bimm`, at wall-clock slot `now` (steps 5–10), with the decoding bound on uncles,
and execution validity from the ledger. -/
def validHeader (T : List ℕ) (bimm now : ℕ) (B : Block) : Bool :=
  let par := B.hdr.parent
  decide (B.hdr.id ≠ genesisId) && decide (B.uncles.length ≤ c.maxUncles) &&
    decide (slotOf st par < B.hdr.slot) &&                  -- step 5
    decide (B.hdr.slot ≤ now) &&                            -- step 6
    T.contains par &&                                       -- step 7
    decide (height st bimm < height st par + 1) &&          -- step 8
    polValid c L O G (chainUp st par) (chainUp st par) B.hdr && genuine st B.hdr &&  -- step 9
    B.uncles.all (validUncle c st L O G par B.hdr.slot) &&  -- step 10
    L.execOK (chainUp st par ++ [B])

/-- **`prune_forks(T, B)`**: remove every fork that diverged below `B`, from its
tip down to (not including) the divergence point. -/
def pruneForks (T : List ℕ) (B : ℕ) : List ℕ :=
  let removed := (tips st T).flatMap (fun t =>
    let d := lca st t B
    if d = B then [] else (chainIds st t).takeWhile (· ≠ d))
  T.filter (fun x => !removed.contains x)

/-- **`on_block(state, B)`**. `ord` orders the tips for fork choice (any order);
`fastPath` selects the specification's shortcut for blocks extending `c_loc`. -/
def onBlock (fastPath : Bool) (ord : List ℕ → List ℕ) (now : ℕ) (s : NodeState) (B : Block) :
    NodeState :=
  if s.tree.contains B.hdr.id || !validHeader c st L O G s.tree s.bimm now B then s
  else
    let T' := s.tree ++ [B.hdr.id]
    let cloc' := if fastPath && B.hdr.parent = s.cloc then B.hdr.id
      else forkChoice st s.rule c.k c.sGen s.cloc (ord (tips st T'))
    match s.rule with
    | .online =>
      let bimm' := blockAtDepth st cloc' c.k
      { s with cloc := cloc', bimm := bimm', tree := pruneForks st T' bimm' }
    | .bootstrap => { s with cloc := cloc', tree := T' }

/-- Receiving a block: the node processes the block's chain in parent-to-child
order (the missing ancestors are downloaded first, *Downloading Blocks*). -/
def receive (fastPath : Bool) (ord : List ℕ → List ℕ) (now : ℕ) (s : NodeState) (b : ℕ) :
    NodeState :=
  (chainUp st b).foldl (onBlock c st L O G fastPath ord now) s

/-- The slots occupied on the chain a new block extends: its ancestors' slots
and the slots of the uncles they reference. -/
def occupiedOn (cloc : ℕ) : List ℕ :=
  (chain st cloc).flatMap (fun x => x.hdr.slot :: x.uncles.map (·.slot))

/-- **`select_uncles_oldest(B)`** for a block at slot `sl` extending `cloc`, from the
node's tree `T`: the valid candidates that add a new occupied slot, oldest parent
first (ties by slot, then ID), one per slot, at most `MAX_UNCLES`. -/
def selectUncles (T : List ℕ) (cloc sl : ℕ) : List Header :=
  let ids := chainIds st cloc
  let occ := occupiedOn st cloc
  let cands := (T.filterMap st).map (·.hdr) |>.filter (fun U =>
    ids.contains U.parent && !ids.contains U.id && decide (U.slot < sl) &&
      decide (sl - slotOf st U.parent ≤ c.uncleWindow) && !occ.contains U.slot)
  -- Python's `sorted(key=(sl_parent(U), sl_U, block_id(U)))`: lexicographic order
  -- (`≤` on `ℕ × ℕ × ℕ` would be the componentwise partial order).
  let lexLE (a b : Header) : Bool :=
    let x := (slotOf st a.parent, a.slot, a.id)
    let y := (slotOf st b.parent, b.slot, b.id)
    decide (x.1 < y.1 ∨ (x.1 = y.1 ∧ (x.2.1 < y.2.1 ∨ (x.2.1 = y.2.1 ∧ x.2.2 ≤ y.2.2))))
  let sorted := cands.mergeSort lexLE
  let pick := sorted.foldl (fun (acc : List Header) U =>
    if acc.length < c.maxUncles && !(acc.map (·.slot)).contains U.slot then acc ++ [U] else acc) []
  pick

/-- The notes of honest node `i` that win slot `sl` on the chain of `cloc`. -/
def winningNotes (i cloc sl : ℕ) : List Note :=
  let C := chainUp st cloc
  let es := epochState c L O G C (c.epochOf sl)
  es.lead.filter (fun n => n.owner = .honest i && (L.notes C).contains n &&
    wins c es.D n.value (O.ticket es.eta sl n.id))

/-- **The honest proposer.** At slot `sl`, an online node that has left the
bootstrap period and holds a winning note proposes one block (the first winning
note; the implementation proposes at most one block per slot,
`services/chain/chain-leader/src/leadership.rs:58`) on its local chain, with
uncles chosen by `select_uncles_oldest`. -/
def propose (i sl newId : ℕ) (s : NodeState) : Option Block :=
  if s.rule = .bootstrap then none else
  match winningNotes c st L O G i s.cloc sl with
  | [] => none
  | n :: _ => some { hdr := { id := newId, parent := s.cloc, slot := sl, note := n.id,
                              signer := .honest i, payload := 0 },
                     uncles := selectUncles c st s.tree s.cloc sl }

end Cryptarchia
