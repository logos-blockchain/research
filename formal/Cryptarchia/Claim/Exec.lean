module

public import Cryptarchia.Spec.Execution
public import Mathlib.Data.Nat.Find

/-!
# The claim: executions

The vocabulary of the finality claim (`Claim/Finality.lean`) that is about executions, on top of
the specification (`Cryptarchia/Spec`). Like the specification, this layer imports no proof: to
read the claim, read `Spec`, `Claim` and nothing else.

* the assumptions on the environment (`Assm`), with the parameters laid out as the specification
  does (`Config.Sane`);
* the world after the first `n` events of an execution (`wAt`) and at its end (`wF`);
* **the canonical epoch states** (`CS`, `σE`): the state each slot's lottery runs under in the
  analysis. Epoch `0` runs under the genesis state; epoch `e ≥ 1` under the state derived on the
  canonical prefix `CP e`: the part below the cut of epoch `e` (`Config.cut`, 72 h before the
  epoch starts at the specification's parameters) of the chain of the immutable block of an
  online honest node, read two slots before the epoch starts (`Config.fix`). The proof shows
  that every honest node leads under these states while finality holds; the claim's stake
  assumptions are stated about them;
* **a finality violation** (`Unsafe`).
-/

@[expose] public section

namespace Cryptarchia

/-! ## The parameters and the assumptions on the environment -/

/-- The parameters are laid out as the specification does: the stake-inference
window ends by the nonce cut, the nonce cut is inside the previous epoch, the
uncle window is shorter than the time between the cut and the epoch start, and
that time is at least two slots (so an epoch's state can be fixed before the
epoch starts, `Config.fix`). -/
structure Config.Sane (c : Config) : Prop where
  period_le : c.period ≤ c.nonceOffset
  offset_le : c.nonceOffset ≤ c.epochLength
  uncle_le : c.uncleWindow + c.nonceOffset ≤ c.epochLength
  offset_pos : 1 ≤ c.nonceOffset
  fix_le : c.nonceOffset + 2 ≤ c.epochLength

/-- The cut of epoch `e`. -/
def Config.cut (c : Config) (e : ℕ) : ℕ := c.epochStart (e - 1) + c.nonceOffset

/-- **The fixing time of epoch `e`**: two slots before it starts. The analysis
reads each epoch's canonical state here; the protocol has no such moment. -/
def Config.fix (c : Config) (e : ℕ) : ℕ := c.epochStart e - 2

/-- The specification's constants with security parameter `k`. -/
def Config.specK (k : ℕ) : Config := { Config.spec with k := k }

/-- The ledger executes honest blocks' payloads. -/
def HonestExec (L : Ledger) : Prop :=
  ∀ C (B : Block) i, B.hdr.signer = .honest i → L.execOK (C ++ [B]) = true

/-- Honest stakers never spend their notes: an honest note in the ledger after
the part of a chain below some slot is still in the ledger after the whole chain. -/
def HonestStake (L : Ledger) : Prop :=
  ∀ (C : List Block) (s : ℕ) (n : Note), (∃ j, n.owner = .honest j) →
    n ∈ L.notes (prefixBelow C s) → n ∈ L.notes C

/-- The assumptions on the environment. (There is no delivery assumption: an
honest block the network fails to deliver within `Δ` is `Late` and counts as
adversarial in the settlement tree.) -/
structure Assm (E : Env) : Prop where
  ord : E.OrderOK
  crash : ∀ i t t', t ≤ t' → E.online i t' = true → E.online i t = true
  exec : HonestExec E.L
  nodup : E.nodes.Nodup
  sane : E.c.Sane
  stake : HonestStake E.L

/-- The environment with oracle `O`. -/
def Env.withO (E : Env) (O : Oracle) : Env := { E with O := O }

/-! ## Indexed executions -/

/-- The world after the first `n` events. -/
def wAt (E : Env) (es : List Event) (n : ℕ) : World := run E World.init (es.take n)

/-- The final world. -/
abbrev wF (E : Env) (es : List Event) : World := wAt E es es.length

/-! ## The canonical epoch states -/

/-- The genesis epoch state. -/
def es0 (E : Env) : EpochState := epochState E.c E.L E.O E.G [genesisBlock] 0

open Classical in
/-- The index at which epoch `e`'s canonical state is fixed: the first point at
which the clock has reached the fixing time `E.c.fix e` (the end of the trace if
never). -/
noncomputable def idxE (E : Env) (es : List Event) (e : ℕ) : ℕ :=
  Nat.find (⟨es.length, Or.inl rfl⟩ : ∃ n, n = es.length ∨ E.c.fix e ≤ (wAt E es n).now)

open Classical in
/-- The reference node for epoch `e`: a node online at the fixing point, if any. -/
noncomputable def i0 (E : Env) (es : List Event) (e : ℕ) : ℕ :=
  if h : ∃ j ∈ E.nodes, E.online j (wAt E es (idxE E es e)).now = true then Classical.choose h else 0

/-- **The canonical prefix of epoch `e`.** -/
noncomputable def CP (E : Env) (es : List Event) (e : ℕ) : List Block :=
  prefixBelow (chainUp (wF E es).st ((wAt E es (idxE E es e)).node (i0 E es e)).bimm) (E.c.cut e)

/-- **The canonical epoch state of epoch `e`.** -/
noncomputable def CS (E : Env) (es : List Event) (e : ℕ) : EpochState :=
  if e = 0 then es0 E else epochState E.c E.L E.O E.G (CP E es e) e

/-- The state each slot's lottery runs under. -/
noncomputable def σE (E : Env) (es : List Event) (t : ℕ) : EpochState := CS E es (E.c.epochOf t)

/-! ## Finality -/

/-- **A finality violation**: a block an honest node had as `B_imm` is missing from
an honest node's chain at a later point where both are online. -/
def Prob.Unsafe (E : Env) (es : List Event) : Prop :=
  ∃ n n' i j, n ≤ n' ∧ n' ≤ es.length ∧ i ∈ E.nodes ∧ j ∈ E.nodes ∧
    E.online i (wAt E es n').now ∧ E.online j (wAt E es n').now ∧
    ((wAt E es n).node i).bimm ∉ chainIds (wAt E es n').st ((wAt E es n').node j).cloc

end Cryptarchia
