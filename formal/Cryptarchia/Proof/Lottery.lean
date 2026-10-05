import Cryptarchia.Proof.LotteryG

/-!
# The lottery string of the first epoch

Within the first epoch every chain derives the genesis epoch state. The
**lottery string** records, for each slot, how many honest nodes hold a winning
note and whether the adversary does. It is a function of the lottery (the
tickets) alone, not of the adversary.

This is the first-epoch instance of `Proof/LotteryG.lean`, with every slot's
state the genesis one and every valid block in the tree:

* the settlement tree's honest successes at each slot are exactly the lottery's
  (given that honest staking notes stay unspent within the epoch);
* the tree's adversarial slots are among the adversary's lottery wins.

Hence the good event checked on the lottery string implies the execution's good
event, whatever the adversary does (`good_of_lottery`).
-/

namespace Cryptarchia

open Settle

variable (E : Env)

/-- The genesis epoch state. -/
def es0 : EpochState := epochState E.c E.L E.O E.G [genesisBlock] 0

/-- Honest node `j` holds a winning note for slot `i`. -/
abbrev honWins (j i : ℕ) : Bool := honWinsS E (fun _ => es0 E) j i

/-- The adversary holds a winning note for slot `i`. -/
abbrev advWins (i : ℕ) : Bool := advWinsS E (fun _ => es0 E) i

/-- **The lottery string**, given which honest proposals are late. -/
noncomputable abbrev lotStr (lt : ℕ → ℕ → Prop) : CStr := lotStrS E (fun _ => es0 E) lt

variable {E} {es : List Event}

/-- Every chain of an execution derives the genesis epoch state for the first epoch. -/
theorem epochState_es0 {st : Store} (hS : StoreOK st) (hg : st genesisId = some genesisBlock)
    {b : ℕ} (hb : Rooted st b) : epochState E.c E.L E.O E.G (chainUp st b) 0 = es0 E := by
  rw [epochState_zero hS hb hS.rooted_gen]
  unfold es0
  congr 1
  unfold chainUp; rw [chain_genesis hg rfl]; rfl

/-- **The execution string is dominated by the lottery string.** -/
theorem advLe_lot (hA : Assm E) (hE0 : (wF E es).now < E.c.epochLength) :
    AdvLe (wF E es).now (WS E es (fun _ => True)) (lotStr E (lateAt E es)) := by
  have hwF := wAt_ok (es := es) hA.ord es.length
  refine advLe_lotS hA hA.stake ?_ (fun _ _ _ _ => trivial) ?_
  · intro n hn htick j _ _
    have hw := wAt_ok (es := es) hA.ord n
    have hev : es[n] = .tick := by
      rw [List.getElem?_eq_getElem hn] at htick; exact Option.some_inj.1 htick
    have := now_mono (E := E) (es := es) (m := es.length) (n := n + 1) hn le_rfl
    rw [wAt_succ E es hn, step_now, hev] at this
    rw [epoch_of_le (show (wAt E es n).now + 1 ≤ (wF E es).now by simpa using this) hE0,
      epochState_es0 hw.store (store_genesis hA.ord n) ((hw.nodes j).rooted _ (hw.nodes j).cloc)]
  · intro v hv B hB _
    obtain ⟨-, ⟨hr, hsN, -⟩⟩ := mem_stree.1 hv
    have hpr : Rooted (wF E es).st B.hdr.parent := by
      have := hr.parent_rooted hwF.store.genSelf; rwa [parentOf_eq hB] at this
    rw [slotOf_eq hB] at hsN
    rw [epoch_of_le hsN hE0, epochState_es0 hwF.store (store_genesis hA.ord es.length) hpr]

end Cryptarchia
