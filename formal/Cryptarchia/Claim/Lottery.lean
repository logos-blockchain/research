module

public import Cryptarchia.Claim.Exec
public import Mathlib.Basic.Real.Basic
public import Mathlib.Probability.Independence.Basic
public import Mathlib.Tactic.DeriveFintype

/-!
# The claim: the lottery and stake

The vocabulary of the finality claim (`Claim/Finality.lean`) that is about the lottery and stake.
Like `Claim/Exec.lean`, this layer imports only the specification and Mathlib.

* **The random-oracle model**: slot `i`'s ticket table `tk O i` holds the ticket of every note
  under every nonce; within one table and one nonce the tickets of distinct notes are independent
  and uniform on `[0, p)` (`RandomOracle`); each slot's table is independent of what is known
  before it, including the epoch state the slot's lottery runs under (`Fresh`: no grinding).
* **A slot's outcome** (`slotOut`): how many online honest nodes win (capped at two) and whether
  the adversary wins.
* **Stake under an epoch state**: the online honest nodes' stake (`hstake`), the adversary's
  (`astake`), both (`tstake`).
* **The stake estimate's observation window** of an epoch (`win`) and the honestly won slots in
  it (`hcnt`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory ProbabilityTheory Finset

/-! ## Slot outcomes -/

/-- The outcome of one slot: the number of honest leaders (`0`, `1`, or `2` for two
or more) and whether the adversary wins. -/
structure Out where
  hon : Fin 3
  adv : Bool
  deriving DecidableEq, Fintype

/-- A slot of a characteristic string as an outcome, capping honest leaders at two. -/
def enc (p : ℕ × Bool) : Out := ⟨if p.1 = 0 then 0 else if p.1 = 1 then 1 else 2, p.2⟩

/-- A ticket table: `T η id`. -/
abbrev Tab := ℕ → ℕ → ℕ

/-- Honest node `j` holds a winning note under `s` with tickets `T`. -/
def honW (c : Config) (s : EpochState) (T : Tab) (j : ℕ) : Bool :=
  s.lead.any (fun n => decide (n.owner = .honest j) && wins c s.D n.value (T s.eta n.id))

/-- The adversary holds a winning note under `s` with tickets `T`. -/
def advW (c : Config) (s : EpochState) (T : Tab) : Bool :=
  s.lead.any (fun n => decide (n.owner = .adv) && wins c s.D n.value (T s.eta n.id))

/-- The number of online honest nodes that win slot `i`. -/
def honCount (E : Env) (i : ℕ) (s : EpochState) (T : Tab) : ℕ :=
  (E.nodes.filter (fun j => E.online j i && honW E.c s T j)).length

/-- **Slot `i`'s outcome** under state `s` with tickets `T`. -/
def slotOut (E : Env) (i : ℕ) (s : EpochState) (T : Tab) : Out :=
  enc (honCount E i s T, advW E.c s T)

/-- Slot `i`'s ticket table. -/
def tk {Ω : Type*} (O : Ω → Oracle) (i : ℕ) (ω : Ω) : Tab := fun η id => (O ω).ticket η i id

/-! ## The random oracle -/

instance : Countable Signer := by
  refine Function.Injective.countable (f := fun s : Signer => match s with | .honest i => some i | .adv => none) ?_
  intro a b h; cases a <;> cases b <;> simp_all

instance : Countable Note :=
  Function.Injective.countable (f := fun n : Note => (n.id, n.value, n.owner))
    (fun a b h => by cases a; cases b; simp_all)

instance : Countable EpochState :=
  Function.Injective.countable (f := fun s : EpochState => (s.lead, s.eta, s.D))
    (fun a b h => by cases a; cases b; simp_all)

instance : MeasurableSpace EpochState := ⊤

instance : MeasurableSingletonClass EpochState := ⟨fun _ => trivial⟩

/-- **A random oracle** for the tickets: within one slot's table and one nonce, the
tickets of distinct notes are independent and uniform on `[0, p)`. -/
structure RandomOracle {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω) (O : Ω → Oracle) (p : ℕ) : Prop where
  pos : 0 < p
  meas : ∀ i, Measurable (tk O i)
  indep : ∀ i η, iIndepFun (fun id ω => tk O i ω η id) μ
  unif : ∀ i η id t, t ≤ p → μ {ω | tk O i ω η id < t} = ENNReal.ofReal ((t : ℝ) / p)

section

variable {Ω : Type*} [MeasurableSpace Ω]

/-- What is known before slot `i`'s tickets are drawn: the earlier slots' ticket
tables and the epoch states of the slots up to `i`. -/
@[instance_reducible]
def hist (O : Ω → Oracle) (σ : Ω → ℕ → EpochState) (i : ℕ) : MeasurableSpace Ω :=
  (⨆ j ∈ Finset.range i, MeasurableSpace.comap (tk O j) inferInstance) ⊔
    (⨆ j ∈ Finset.range (i + 1), MeasurableSpace.comap (fun ω => σ ω j) inferInstance)

/-- **Fresh lotteries** (no grinding): each slot's ticket table is independent of
what is known before it, including the epoch state the slot's lottery runs under. -/
def Fresh (μ : Measure Ω) (O : Ω → Oracle) (σ : Ω → ℕ → EpochState) : Prop :=
  ∀ i, Indep (hist O σ i) (MeasurableSpace.comap (tk O i) inferInstance) μ

end

/-! ## Stake -/

/-- The notes of the online honest nodes in `K`. -/
def honNotes (E : Env) (i : ℕ) (s : EpochState) (K : List ℕ) : List Note :=
  s.lead.filter fun n => K.any fun j => E.online j i && decide (n.owner = .honest j)

/-- The adversary's notes. -/
def advNotes (s : EpochState) : List Note := s.lead.filter fun n => decide (n.owner = .adv)

/-- The stake of a list of notes. -/
def stakeOf (L : List Note) : ℕ := (L.map Note.value).sum

/-- The honest stake online at slot `i` under `s`. -/
noncomputable def hstake (E : Env) (i : ℕ) (s : EpochState) : ℝ := (stakeOf (honNotes E i s E.nodes) : ℝ)

/-- The adversary's stake under `s`. -/
noncomputable def astake (s : EpochState) : ℝ := (stakeOf (advNotes s) : ℝ)

/-- All stake under `s` that slot `i`'s lottery counts: online honest and adversarial. -/
noncomputable def tstake (E : Env) (i : ℕ) (s : EpochState) : ℝ := hstake E i s + astake s

/-- **The online schedule changes only at epoch boundaries**: each node's online
status at a slot is its status at the epoch's first slot. -/
def OnlineEpoch (E : Env) : Prop :=
  ∀ j ∈ E.nodes, ∀ i, E.online j i = E.online j (i / E.c.epochLength * E.c.epochLength)

/-! ## The stake estimate's window -/

/-- The observation window of epoch `e`, as the indices `k` of slots `k + 1`
(slot `0` is genesis). -/
def win (E : Env) (e : ℕ) : Finset ℕ :=
  Ico (e * E.c.epochLength - 1) (e * E.c.epochLength + E.c.period - 1)

/-- The indicator of a set of outcomes, as a real. -/
def indA (A : Out → Prop) [DecidablePred A] (o : Out) : ℝ := if A o then 1 else 0

/-- Some honest leader. -/
def honA (o : Out) : Prop := o.hon ≠ 0

instance : DecidablePred honA := fun o => inferInstanceAs (Decidable (o.hon ≠ 0))

/-- Honest occupied slots in epoch `e`'s window. -/
noncomputable def hcnt (E : Env) (X : ℕ → Out) (e : ℕ) : ℝ := ∑ k ∈ win E e, indA honA (X k)

/-- **Stake drifts by at most a factor `ρ` from epoch `e` to `e + 1`.** At every slot of
epoch `e + 1`, honest online stake is at most `ρ` times that at any slot of epoch `e`'s
window, and all participating stake is at least `1/ρ` times that at any slot of the
window and at the epoch's first slot. -/
structure StakeDrift (E : Env) (σ : ℕ → EpochState) (ρ : ℝ) (e : ℕ) : Prop where
  hon : ∀ j, (e + 1) * E.c.epochLength ≤ j → j < (e + 2) * E.c.epochLength → ∀ k ∈ win E e,
    hstake E j (σ j) ≤ ρ * hstake E (k + 1) (σ (k + 1))
  tot : ∀ j, (e + 1) * E.c.epochLength ≤ j → j < (e + 2) * E.c.epochLength → ∀ k ∈ win E e,
    tstake E (k + 1) (σ (k + 1)) ≤ ρ * tstake E j (σ j)
  tot0 : ∀ j, (e + 1) * E.c.epochLength ≤ j → j < (e + 2) * E.c.epochLength →
    tstake E (e * E.c.epochLength) (σ (e * E.c.epochLength)) ≤ ρ * tstake E j (σ j)

/-- **Honest online stake is at least `Hmin`** at every slot. -/
def MinStake (E : Env) (σ : ℕ → EpochState) (Hmin : ℝ) : Prop := ∀ j, Hmin ≤ hstake E j (σ j)

end Cryptarchia.Prob
