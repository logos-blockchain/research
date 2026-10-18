module

public import Cryptarchia.Claim.Lottery

/-!
# The claim: probabilistic finality

`Claim.Finality k Δ N β Smax μ ρ Hmin ε` says: at the specification's parameters with security
parameter `k`, network delay `Δ` slots and executions up to slot `N`, under the execution model and
the assumptions below, a finality violation has probability at most `ε`. The certificates prove
instances of it (`CryptarchiaCerts.lean`); this file and the two it imports (`Claim/Exec.lean`,
`Claim/Lottery.lean`), with the specification, are all a reader needs to check what they state.
A test (`CryptarchiaTest/Claim.lean`) checks that the instances' statements use no definition from
outside `Cryptarchia.Spec` and `Cryptarchia.Claim`.

The randomness is a probability space `Ω`: each `ω` fixes the ticket oracle `O ω` and the
execution `es ω` (the adversary's events, which may depend on the tickets).

**The execution model** (`Model`): honest nodes follow the protocol, only crash, have distinct
ids, and the configuration is the specification's layout; honest blocks reach every honest node
online throughout the next `Δ` slots; tickets are a random oracle; each slot's tickets are
independent of everything before it, including the epoch state the slot's lottery runs under
(no grinding); honest nodes go online or offline only at epoch boundaries; some honest node is
online at every slot.

**The assumptions on executions**, stated about the canonical epoch states `σE` (`Claim/Exec.lean`):

* `GenesisOK`: the genesis stake estimate is the genesis stake, all of it online;
* `Exec.StakeOK β Smax`: at every slot the adversary holds at most a fraction `β` of the
  participating stake (online honest plus adversarial); the honest online stake and the
  adversary's stake are each at most `Smax`; lead note identifiers are distinct; and the stake
  estimate is at most `t0Const / 2` (about `3.7 · 10⁷⁴`), so that lottery thresholds stay
  below the field size;
* `Exec.ChainQuality μ N`: for every epoch whose stake-inference window closes by slot `N`, the
  canonical chain counts (as blocks or uncles) at least a fraction `1 - μ` of the window's slots
  that an online honest node won. It is what the stake estimate's update needs to track the
  honest stake. **It is assumed, not proven**: chain growth alone gives about `μ = 0.25`; an
  adversary that cannot predict honest leaders can force about `0.122` (an MDP analysis, outside
  Lean), and one that can, which `Model` does not exclude, about `0.22`;
* `Exec.StakeDrift ρ N`: from every such window to the following epoch, stake moves by at most
  a factor `ρ`;
* `Exec.MinStake Hmin`: the honest online stake is at least `Hmin` at every slot.
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory

variable {Ω : Type*} [MeasurableSpace Ω]

/-- **The execution model.** Each `ω` fixes the oracle `O ω` and the execution `es ω`. -/
structure Model (μ : Measure Ω) (O : Ω → Oracle) (E : Env) (es : Ω → List Event) : Prop where
  /-- honest nodes follow the protocol, only crash, have distinct ids; the configuration is sane -/
  assm : Assm E
  /-- honest blocks reach every honest node online throughout the next `Δ` slots -/
  delivery : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω)
  /-- lottery tickets are a random oracle -/
  oracle : RandomOracle μ O E.c.p
  /-- each slot's epoch state is a measurable function of the randomness -/
  measurable : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i
  /-- each slot's tickets are independent of everything before it (no grinding) -/
  fresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω)
  /-- honest nodes go online or offline only at epoch boundaries -/
  onlineEpoch : OnlineEpoch E
  /-- some honest node is online at every slot -/
  live : ∀ t, ∃ j ∈ E.nodes, E.online j t = true

/-- **The genesis estimate is the genesis stake**, all of it online at the first slot. -/
def GenesisOK (E : Env) : Prop :=
  stakeOf (honNotes E 0 (es0 E) E.nodes) + stakeOf (advNotes (es0 E)) = (es0 E).D

/-- **Honest majority of stake at slot `i`**, under the slot's epoch state `s`. -/
structure SlotStake (E : Env) (β Smax : ℝ) (i : ℕ) (s : EpochState) : Prop where
  /-- lead note identifiers are distinct -/
  nodup : (s.lead.map Note.id).Nodup
  /-- the stake estimate is at most `t0Const / 2`, so lottery thresholds stay below the field size -/
  D_le : 2 * s.D ≤ E.c.t0Const
  /-- the online honest stake is at most `Smax` -/
  hon_le : hstake E i s ≤ Smax
  /-- the adversary's stake is at most `Smax` -/
  adv_le : astake s ≤ Smax
  /-- the adversary holds at most a fraction `β` of the participating stake -/
  frac : (1 - β) * astake s ≤ β * hstake E i s

namespace Exec

/-- **Honest majority of stake** at every slot (`SlotStake`). -/
def StakeOK (E : Env) (o : Oracle) (es : List Event) (β Smax : ℝ) : Prop :=
  ∀ i, SlotStake E β Smax i (σE (E.withO o) es i)

/-- **Chain quality for the stake estimate**: for every epoch `e` whose observation window
closes by slot `N`, the canonical chain of epoch `e + 1` counts (as block or uncle slots) at
least a fraction `1 - μ` of the window's slots that an online honest node won. -/
def ChainQuality (E : Env) (o : Oracle) (es : List Event) (μ : ℝ) (N : ℕ) : Prop :=
  ∀ e, e * E.c.epochLength + E.c.period ≤ N → (1 - μ) *
    hcnt E (fun k => slotOut E (k + 1) (σE (E.withO o) es (k + 1)) (fun η id => o.ticket η (k + 1) id)) e ≤
      (occupied E.c (CP (E.withO o) es (e + 1)) e : ℝ)

/-- **Stake drifts by at most a factor `ρ`** from every epoch whose observation window closes by
slot `N` to the next. -/
def StakeDrift (E : Env) (o : Oracle) (es : List Event) (ρ : ℝ) (N : ℕ) : Prop :=
  ∀ e, e * E.c.epochLength + E.c.period ≤ N → Prob.StakeDrift E (σE (E.withO o) es) ρ e

/-- **Honest online stake is at least `Hmin`** at every slot. -/
def MinStake (E : Env) (o : Oracle) (es : List Event) (Hmin : ℝ) : Prop := Prob.MinStake E (σE (E.withO o) es) Hmin

end Exec

end Cryptarchia.Prob

namespace Cryptarchia.Claim

open MeasureTheory Prob

universe u

/-- **Finality with failure probability at most `ε`.** At the specification's parameters with
security parameter `k` (`Config.specK k`), network delay `Δ` slots and executions up to slot `N`:
for every probability space, oracle and executions satisfying the execution model, if the
genesis estimate is the genesis stake, the adversary holds at most a fraction `β` of the
participating stake (and stakes are at most `Smax`), the canonical chain counts at least a
fraction `1 - μ` of each window's honestly won slots, stake drifts by at most a factor `ρ` per
epoch and honest online stake is at least `Hmin`, then the probability that some honest node's
immutable block is later missing from some honest node's chain is at most `ε`. -/
def Finality (k Δ N : ℕ) (β Smax μ ρ Hmin ε : ℝ) : Prop :=
  ∀ (Ω : Type u) [MeasurableSpace Ω] (P : Measure Ω) [IsProbabilityMeasure P] (O : Ω → Oracle) (E : Env)
    (es : Ω → List Event),
    Model P O E es → E.c = Config.specK k → E.Δ = Δ → (∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N) →
    GenesisOK E → (∀ ω, Exec.StakeOK E (O ω) (es ω) β Smax) → (∀ ω, Exec.ChainQuality E (O ω) (es ω) μ N) →
    (∀ ω, Exec.StakeDrift E (O ω) (es ω) ρ N) → (∀ ω, Exec.MinStake E (O ω) (es ω) Hmin) →
    P {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal ε

end Cryptarchia.Claim
