import Cryptarchia.Spec.Node

/-!
# Cryptarchia: executions

An execution is a sequence of events chosen by the adversary:

* `tick`: the wall clock advances one slot; every online honest node then runs
  the leader lottery for the new slot and, if it wins, proposes on its local
  chain and processes its own block.
* `deliver i b`: block `b` (with any ancestors node `i` lacks, parent to child)
  reaches honest node `i`, which runs `on_block` on each.
* `create B`: the adversary creates a block. It can sign only with its own keys
  (`signer = adv`); anything else about the block is free: any parent, any slot
  (backdating), any number of blocks per winning slot (equivocation), any
  uncles, any payload. Whether honest nodes accept it is decided by validation.

**Network assumption (Δ-delivery).** Every honest block created at slot `s`
reaches every honest node that is online throughout slots `s … s + Δ` by slot
`s + Δ` (`DeltaDelivery`). Adversarial blocks reach whom the adversary chooses,
when it chooses. This is stronger for the adversary than the implementation,
where gossipsub forwards every block (`chain-network/.../libp2p.rs`); the
adversary can always deliver to everyone if it wants to.

**Tip order.** Each node visits tips in an order the adversary picks (any
permutation); this covers the specification's unspecified order and the
implementation's hash order.
-/

namespace Cryptarchia

/-- What the adversary does. -/
inductive Event
  | tick
  | deliver (i b : ℕ)
  | create (B : Block)
  deriving Repr

/-- The environment of an execution: the constants, the ledger, the oracle,
genesis, the honest nodes and when they are online, the tip order, and which
reading of `on_block` nodes run. -/
structure Env where
  c : Config
  L : Ledger
  O : Oracle
  G : Genesis
  /-- The honest nodes. -/
  nodes : List ℕ
  /-- Node `i` is online at slot `sl`. -/
  online : ℕ → ℕ → Bool
  /-- The order in which node `i` visits tips (a permutation of its argument,
  see `Env.OrderOK`). -/
  ord : ℕ → List ℕ → List ℕ
  fastPath : Bool
  /-- The Δ of the network, in slots. -/
  Δ : ℕ

/-- Tip orders are permutations. -/
def Env.OrderOK (E : Env) : Prop := ∀ i l, (E.ord i l).Perm l

/-- The state of the world: the wall-clock slot, every block created, the honest
nodes' states, and a log of honest blocks with their creation slots. -/
structure World where
  now : ℕ
  st : Store
  used : List ℕ
  node : ℕ → NodeState
  honestLog : List (ℕ × ℕ)

variable (E : Env)

/-- The genesis block. -/
def genesisBlock : Block :=
  { hdr := { id := genesisId, parent := genesisId, slot := 0, note := 0, signer := .adv,
             payload := 0 }, uncles := [] }

/-- The initial world: only genesis; every honest node on it, running the
online rule (nodes that start from genesis and stay online). -/
def World.init : World :=
  { now := 0
    st := fun b => if b = genesisId then some genesisBlock else none
    used := [genesisId]
    node := fun _ => { cloc := genesisId, bimm := genesisId, tree := [genesisId], rule := .online }
    honestLog := [] }

/-- Add a block to the store. -/
def World.add (w : World) (B : Block) : World :=
  { w with st := fun b => if b = B.hdr.id then some B else w.st b, used := B.hdr.id :: w.used }

/-- A fresh block ID. -/
def World.fresh (w : World) : ℕ := w.used.foldl max 0 + 1

/-- Node `i` runs the lottery for the current slot and, if it wins, proposes and
processes its own block. -/
def World.lead (w : World) (i : ℕ) : World :=
  if !E.online i w.now then w else
  match propose E.c w.st E.L E.O E.G i w.now w.fresh (w.node i) with
  | none => w
  | some B =>
    let w' := w.add B
    { w' with
      node := fun j => if j = i then
        onBlock E.c w'.st E.L E.O E.G E.fastPath (E.ord i) w'.now (w.node i) B else w'.node j
      honestLog := (B.hdr.id, w.now) :: w.honestLog }

/-- One event. -/
def World.step (w : World) : Event → World
  | .tick =>
    let w := { w with now := w.now + 1 }
    E.nodes.foldl (World.lead E) w
  | .deliver i b =>
    if E.nodes.contains i && E.online i w.now then
      { w with node := fun j => if j = i then
          receive E.c w.st E.L E.O E.G E.fastPath (E.ord i) w.now (w.node i) b else w.node j }
    else w
  | .create B =>
    if B.hdr.signer = .adv && !w.used.contains B.hdr.id then w.add B else w

/-- The worlds of an execution, before each event (and the final one last). -/
def trace (w : World) : List Event → List World
  | [] => [w]
  | e :: es => w :: trace (w.step E e) es

/-- Run an execution. -/
def run (w : World) (es : List Event) : World := es.foldl (World.step E) w

/-- **Δ-delivery.** For every honest block `b` created at slot `s` and every node
`i` online throughout `s … s + Δ`, the execution delivers `b` to `i` at some point
when the clock is in `s … s + Δ`, provided the execution runs until slot `s + Δ`. -/
def DeltaDelivery (es : List Event) : Prop :=
  let ws := trace E World.init es
  let final := run E World.init es
  ∀ b s, (b, s) ∈ final.honestLog → s + E.Δ ≤ final.now →
    ∀ i ∈ E.nodes, (∀ t, s ≤ t → t ≤ s + E.Δ → E.online i t) →
      ∃ n, ∃ h : n < es.length, (match es[n] with
          | .deliver j b' => j = i ∧ b' = b
          | _ => False) ∧
        s ≤ (ws[n]?.map (·.now)).getD 0 ∧ (ws[n]?.map (·.now)).getD 0 ≤ s + E.Δ

/-- **Timely delivery of one block.** If `b` is an honest block created at slot `s`,
then every node online throughout `s … s + Δ` receives it with the clock in
`s … s + Δ` (provided the execution runs until slot `s + Δ`). -/
def Delivered (es : List Event) (b : ℕ) : Prop :=
  let ws := trace E World.init es
  let final := run E World.init es
  ∀ s, (b, s) ∈ final.honestLog → s + E.Δ ≤ final.now →
    ∀ i ∈ E.nodes, (∀ t, s ≤ t → t ≤ s + E.Δ → E.online i t) →
      ∃ n, ∃ h : n < es.length, (match es[n] with
          | .deliver j b' => j = i ∧ b' = b
          | _ => False) ∧
        s ≤ (ws[n]?.map (·.now)).getD 0 ∧ (ws[n]?.map (·.now)).getD 0 ≤ s + E.Δ

/-- A **late** block: one the network did not deliver within `Δ` to some node that
was online throughout. Late honest blocks count as adversarial in the settlement
analysis; the probability layer bounds how often honest blocks are late. -/
def Late (es : List Event) (b : ℕ) : Prop := ¬ Delivered E es b

/-- Δ-delivery is timely delivery of every block. -/
theorem deltaDelivery_iff (es : List Event) : DeltaDelivery E es ↔ ∀ b, Delivered E es b := by
  unfold DeltaDelivery Delivered
  exact ⟨fun h b s => h b s, fun h b s => h b s⟩

end Cryptarchia
