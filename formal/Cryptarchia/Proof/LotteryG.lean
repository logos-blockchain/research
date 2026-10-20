module

public import Cryptarchia.Settle.Mono
public import Cryptarchia.Proof.Main
import Std.Tactic.BVDecide.Normalize.BitVec

/-!
# The lottery string, for any assignment of epoch states to slots

`σ i` is the epoch state that the lottery of slot `i` runs under. The lottery
string `lotStrS σ` records per slot how many honest nodes hold a winning note
under `σ i` and whether the adversary does. Two hypotheses tie it to an
execution:

* every honest node, when it leads at slot `t`, derives `σ t` on its local chain;
* every adversarial block of the settlement tree (for the block predicate `K`)
  is validated under `σ` of its slot.

Then the execution's string is weakly dominated by the lottery string up to a
horizon (`advLeW_upto`). `Proof/LotteryE.lean` is the instance (`σ` = canonical
states, `K` = consistency).
-/

@[expose] public section

namespace Cryptarchia

open Settle

variable (E : Env) (σ : ℕ → EpochState)

/-- Honest node `j` holds a winning note for slot `i` under `σ i`. -/
def honWinsS (j i : ℕ) : Bool :=
  (σ i).lead.any (fun n => decide (n.owner = .honest j) &&
    wins E.c (σ i).D n.value (E.O.ticket (σ i).eta i n.id))

/-- The adversary holds a winning note for slot `i` under `σ i`. -/
def advWinsS (i : ℕ) : Bool :=
  (σ i).lead.any (fun n => decide (n.owner = .adv) &&
    wins E.c (σ i).D n.value (E.O.ticket (σ i).eta i n.id))

/-- Honest node `j` is online at slot `i` and holds a winning note: it leads. -/
def actS (j i : ℕ) : Bool := E.online j i && honWinsS E σ j i

open Classical in
/-- **The lottery string**, given which honest proposals are late (`lt j i`: node
`j`'s block for slot `i` was not delivered in time): the online honest winners whose
block is timely, and whether the adversary wins or some honest block of the slot
is late (late honest blocks count as adversarial). -/
noncomputable def lotStrS (lt : ℕ → ℕ → Prop) : CStr := fun i =>
  ((E.nodes.filter (fun j => actS E σ j i && !decide (lt j i))).length,
    advWinsS E σ i || decide (∃ j, lt j i))

/-- Under honest stake, an honest note in the lead set a chain derives is unspent
on that chain. -/
theorem HonestStake.lead {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} (h : HonestStake L)
    {C : List Block} {ep : ℕ} {n : Note} (hn : n ∈ (epochState c L O G C ep).lead)
    (hh : ∃ j, n.owner = .honest j) : n ∈ L.notes C :=
  h C _ n hh (h _ _ n hh hn)

variable {E σ} {es : List Event}

/-- On a chain deriving `σ i`, an honest node's lottery is the string's. -/
theorem winningNotes_iffS (hN : HonestStake E.L) {st : Store} {j cl i : ℕ}
    (hσ : epochState E.c E.L E.O E.G (chainUp st cl) (E.c.epochOf i) = σ i) :
    winningNotes E.c st E.L E.O E.G j cl i ≠ [] ↔ honWinsS E σ j i = true := by
  unfold winningNotes honWinsS
  dsimp only
  rw [hσ]
  simp only [ne_eq, List.filter_eq_nil_iff, not_forall, not_not, Bool.and_eq_true,
    decide_eq_true_eq, List.any_eq_true]
  constructor
  · rintro ⟨n, hn, ⟨hno, -⟩, hnw⟩; exact ⟨n, hn, hno, hnw⟩
  · rintro ⟨n, hn, hno, hnw⟩
    exact ⟨n, hn, ⟨hno, by simpa using hN.lead (hσ ▸ hn) ⟨j, hno⟩⟩, hnw⟩

/-- An honest node proposes exactly when it holds a winning note. -/
theorem propose_iffS (hN : HonestStake E.L) {st : Store} {j t newId : ℕ} {s : NodeState}
    (hs : NodeOK E.c.k st E.L E.O E.G E.c s)
    (hσ : epochState E.c E.L E.O E.G (chainUp st s.cloc) (E.c.epochOf t) = σ t) :
    (∃ B, propose E.c st E.L E.O E.G j t newId s = some B) ↔ honWinsS E σ j t = true := by
  rw [← winningNotes_iffS hN hσ]
  unfold propose
  rw [if_neg (by rw [hs.rule]; simp)]
  constructor
  · rintro ⟨B, hB⟩ h
    rw [h] at hB; simp at hB
  · intro h
    cases hw : winningNotes E.c st E.L E.O E.G j s.cloc t with
    | nil => exact absurd hw h
    | cons n ns => exact ⟨_, rfl⟩

/-- **The lottery invariant of a world**: every honest block's signer won its slot,
and every win up to the current slot produced a block. -/
structure LotOKS (E : Env) (σ : ℕ → EpochState) (w : World) : Prop where
  won : ∀ b B j, w.st b = some B → B.hdr.signer = .honest j → actS E σ j B.hdr.slot = true
  made : ∀ i j, 1 ≤ i → i ≤ w.now → j ∈ E.nodes → actS E σ j i = true →
    ∃ b B, w.st b = some B ∧ B.hdr.signer = .honest j ∧ B.hdr.slot = i

theorem init_lotS : LotOKS E σ World.init := by
  refine ⟨fun b B j hb hj => ?_, fun i j h1 h2 => by simp [World.init] at h2; omega⟩
  simp only [World.init] at hb; split at hb
  · cases hb; simp [genesisBlock] at hj
  · simp at hb

/-- A tick keeps the lottery invariant, given that every online node derives the
lottery's state on its local chain. -/
theorem tick_lotS (hA : Assm E) {w : World} (hw : WorldOK E w) (hl : LotOKS E σ w)
    (hσ : ∀ j ∈ E.nodes, E.online j (w.now + 1) = true →
      epochState E.c E.L E.O E.G (chainUp w.st (w.node j).cloc) (E.c.epochOf (w.now + 1)) = σ (w.now + 1)) :
    LotOKS E σ (w.step E .tick) := by
  -- the fold over the nodes: each block won, and each node led wins for the new slot only with a block
  obtain ⟨h, hwon, hmade⟩ := tick_induct hA.nodup (fun l w₀ => StepOK E w w₀ ∧
      (∀ b B j, w₀.st b = some B → B.hdr.signer = .honest j → actS E σ j B.hdr.slot = true) ∧
      ∀ j ∈ l, actS E σ j (w.now + 1) = true →
        ∃ b B, w₀.st b = some B ∧ B.hdr.signer = .honest j ∧ B.hdr.slot = w.now + 1)
    ⟨tick0_ok hw, hl.won, fun _ h => by simp at h⟩ (by
      intro l w₀ i hi _ ⟨h, hwon, hmade⟩ hnow hsame hsig
      have hw₀ := h.ok
      have hpi : E.online i w₀.now = true →
          ((∃ C, propose E.c w₀.st E.L E.O E.G i w₀.now w₀.fresh (w₀.node i) = some C) ↔
            honWinsS E σ i w₀.now = true) := by
        intro hio
        refine propose_iffS hA.stake (hw₀.nodes i) ?_
        rw [hsame, hnow, chainUp_ext h.ext (hw.nodes i).cloc_rooted]
        exact hσ i hi (hnow ▸ hio)
      have h' := lead_ok hA hw h hnow hi hsame hsig
      refine ⟨h', fun b B j hb hj => ?_, fun j hj hwin => ?_⟩
      · rcases lead_st hb with hb | ⟨hio, hC⟩
        · exact hwon b B j hb hj
        · obtain ⟨-, hs, -, hsl⟩ := propose_id hC
          rw [hs] at hj; cases hj
          simp only [actS, hsl, hio, (hpi hio).1 ⟨B, hC⟩, Bool.and_self]
      · rcases List.mem_cons.1 hj with rfl | hj
        · simp only [actS, Bool.and_eq_true, ← hnow] at hwin
          obtain ⟨C, hC⟩ := (hpi hwin.1).2 hwin.2
          obtain ⟨-, hs, -, hsl⟩ := propose_id hC
          exact ⟨_, C, lead_st_some hwin.1 hC, hs, hsl.trans hnow⟩
        · obtain ⟨b, B, hb, hs, hsl⟩ := hmade j hj hwin
          exact ⟨b, B, lead_ext hw₀ i b B hb, hs, hsl⟩)
  have hnow : (w.step E .tick).now = w.now + 1 := step_now w .tick
  refine ⟨hwon, fun i j h1 h2 hj hwin => ?_⟩
  rw [hnow] at h2
  rcases Nat.lt_or_ge i (w.now + 1) with hlt | hge
  · obtain ⟨b, B, hb, hsig, hsl⟩ := hl.made i j h1 (by omega) hj hwin
    exact ⟨b, B, h.ext b B hb, hsig, hsl⟩
  · obtain rfl : i = w.now + 1 := by omega
    exact hmade j (List.mem_reverse.2 hj) hwin

/-- Every event keeps the lottery invariant (a tick given the lottery's states). -/
theorem step_lotS (hA : Assm E) {w : World} (hw : WorldOK E w) (hl : LotOKS E σ w) (e : Event)
    (hσ : e = .tick → ∀ j ∈ E.nodes, E.online j (w.now + 1) = true →
      epochState E.c E.L E.O E.G (chainUp w.st (w.node j).cloc)
      (E.c.epochOf (w.now + 1)) = σ (w.now + 1)) : LotOKS E σ (w.step E e) := by
  cases e with
  | tick => exact tick_lotS hA hw hl (hσ rfl)
  | deliver i b =>
    simp only [World.step]; split
    · exact ⟨hl.won, hl.made⟩
    · exact hl
  | create B =>
    simp only [World.step]; split
    · rename_i hc
      simp only [Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at hc
      have hext := (add_ok hw B (by intro hm; have := List.contains_iff_mem.2 hm; simp_all)).1
      refine ⟨fun b C j hb hj => ?_, fun i j h1 h2 hj hwin => ?_⟩
      · rcases add_st_cases hb with ⟨-, rfl⟩ | hb
        · rw [hc.1] at hj; cases hj
        · exact hl.won b C j hb hj
      · obtain ⟨b, C, hb, hs, hsl⟩ := hl.made i j h1 h2 hj hwin
        exact ⟨b, C, hext b C hb, hs, hsl⟩
    · exact hl

/-! ## The execution string against the lottery string -/

/-- The honest node that signed a stored block. -/
def sigOf (st : Store) (v : ℕ) : ℕ := match st v with
  | some B => (match B.hdr.signer with | .honest j => j | .adv => 0)
  | none => 0

theorem sigOf_eq {st : Store} {v j : ℕ} {B : Block} (hB : st v = some B)
    (hj : B.hdr.signer = .honest j) : sigOf st v = j := by
  simp [sigOf, hB, hj]

theorem honB_of {st : Store} {v j : ℕ} {B : Block} (hB : st v = some B)
    (hj : B.hdr.signer = .honest j) : honB st v = true := by
  simp [honB, hB, hj]

/-- Node `j`'s block for slot `i` is late (in the final store). -/
def lateAt (E : Env) (es : List Event) (j i : ℕ) : Prop :=
  ∃ b B, (wF E es).st b = some B ∧ B.hdr.signer = .honest j ∧ B.hdr.slot = i ∧ Late E es b

/-- Under Δ-delivery of every honest block, no proposal is late. -/
theorem lateAt_none (hD : DeltaDelivery E es) (j i : ℕ) : ¬ lateAt E es j i := by
  rintro ⟨b, B, -, -, -, hl⟩
  exact hl ((deltaDelivery_iff E es).1 hD b)

open Classical in
/-- Under Δ-delivery the lottery string is the plain one: all online honest
winners, and the adversary's wins. -/
theorem lotStrS_of_delivery (hD : DeltaDelivery E es) :
    lotStrS E σ (lateAt E es) = fun i => ((E.nodes.filter (fun j => actS E σ j i)).length, advWinsS E σ i) := by
  funext i
  simp [lotStrS, lateAt_none hD]

variable {K : ℕ → Prop}

/-- Adversarial blocks of the tree are validated under `σ` of their slot. -/
def AdvStatesOK (E : Env) (es : List Event) (K : ℕ → Prop) (σ : ℕ → EpochState) : Prop :=
  ∀ v ∈ (FT E es K).V, ∀ B, (wF E es).st v = some B → B.hdr.signer = .adv →
    epochState E.c E.L E.O E.G (chainUp (wF E es).st B.hdr.parent) (E.c.epochOf B.hdr.slot) = σ B.hdr.slot

open Classical in
/-- **Adversarial slots of the execution are adversarial lottery wins.** -/
theorem adv_domS (hA : Assm E) (hσa : AdvStatesOK E es K σ) {i : ℕ} (h : (WS E es K i).2 = true) :
    (lotStrS E σ (lateAt E es) i).2 = true := by
  have hw := wAt_ok (es := es) hA es.length
  have hS := hw.store
  have h' : ∃ v ∈ (FT E es K).V, honL (wF E es).st (Late E es) v = false ∧ slotOf (wF E es).st v = i := by
    simp only [WS, sstr, decide_eq_true_eq] at h; exact h
  obtain ⟨v, hv, hhL, hsl⟩ := h'
  obtain ⟨-, ⟨hr, hsN, hch⟩⟩ := mem_stree.1 hv
  have hv0 : v ≠ genesisId := by intro h0; rw [h0, honL_genesis] at hhL; cases hhL
  -- a late honest block: the slot is marked late in the lottery string
  by_cases hhb : honB (wF E es).st v = true
  · have hlate : Late E es v := by
      by_contra hnl
      have := (honL_iff (late := Late E es) hv0).2 ⟨hhb, hnl⟩
      rw [this] at hhL; cases hhL
    obtain ⟨B, hB, j, hj⟩ := honB_signed hhb hv0 hr.exists_blk
    simp only [lotStrS, Bool.or_eq_true, decide_eq_true_eq]
    right
    exact ⟨j, v, B, hB, hj, by rw [← slotOf_eq hB]; exact hsl, hlate⟩
  have hh : honB (wF E es).st v = false := by simpa using hhb
  rcases hch v (self_mem_chainIds hS hr) with h0 | ⟨B, hB, hval⟩
  · exact absurd h0 hv0
  obtain ⟨B', hB', hpr, -⟩ := hr.inv hv0
  rw [hB] at hB'; cases hB'
  have hsig : B.hdr.signer = .adv := by
    cases hs : B.hdr.signer with
    | adv => rfl
    | honest j => rw [honB_of hB hs] at hh; cases hh
  rw [slotOf_eq hB] at hsl
  have hpol : polValid E.c E.L E.O E.G (chainUp (wF E es).st B.hdr.parent)
      (chainUp (wF E es).st B.hdr.parent) B.hdr = true := by
    unfold validCore at hval
    simp only [Bool.and_eq_true] at hval
    exact hval.1.1.1.2
  unfold polValid at hpol
  rw [hσa v hv B hB hsig] at hpol
  simp only [lotStrS, advWinsS, List.any_eq_true, Bool.and_eq_true, Bool.or_eq_true, decide_eq_true_eq] at hpol ⊢
  left
  obtain ⟨n, hn, hcond⟩ := hpol
  rw [← hsl]
  refine ⟨n, hn, ?_, hcond.2.2.2⟩
  rw [hcond.2.1, hsig]

/-! ## Up to a horizon -/

/-- Every honest node leading at a tick up to the horizon `Hz` derives the lottery's
state on its local chain. -/
def TickStates (E : Env) (es : List Event) (σ : ℕ → EpochState) (Hz : ℕ) : Prop :=
  ∀ n < es.length, es[n]? = some .tick → (wAt E es n).now + 1 ≤ Hz → ∀ j ∈ E.nodes,
    E.online j ((wAt E es n).now + 1) = true →
      epochState E.c E.L E.O E.G (chainUp (wAt E es n).st ((wAt E es n).node j).cloc)
        (E.c.epochOf ((wAt E es n).now + 1)) = σ ((wAt E es n).now + 1)

/-- The clock takes every value up to the end of the execution. -/
theorem exists_index_now {i : ℕ} (hi : i ≤ (wF E es).now) : ∃ n ≤ es.length, (wAt E es n).now = i := by
  have key : ∀ m ≤ es.length, i ≤ (wAt E es m).now → ∃ n ≤ m, (wAt E es n).now = i := by
    intro m
    induction m with
    | zero => intro _ h; exact ⟨0, le_rfl, by rw [wAt_zero] at h ⊢; simp [World.init] at h ⊢; omega⟩
    | succ m ih =>
      intro hm h
      by_cases hle : i ≤ (wAt E es m).now
      · obtain ⟨n, hn, he⟩ := ih (by omega) hle; exact ⟨n, by omega, he⟩
      · have : (wAt E es (m + 1)).now ≤ (wAt E es m).now + 1 := by
          rw [wAt_succ E es (by omega), step_now]; split <;> omega
        exact ⟨m + 1, le_rfl, by omega⟩
  obtain ⟨n, hn, he⟩ := key es.length le_rfl hi
  exact ⟨n, hn, he⟩

/-- **The lottery invariant up to the horizon `H`**, from the lottery states of
the ticks up to `H`. -/
theorem lot_uptoS (hA : Assm E) {Hz : ℕ} (hσ : TickStates E es σ Hz) :
    ∀ n ≤ es.length, (wAt E es n).now ≤ Hz → LotOKS E σ (wAt E es n) := by
  intro n
  induction n with
  | zero => intro _ _; rw [wAt_zero]; exact init_lotS
  | succ n ih =>
    intro hn hnH
    have hmono : (wAt E es n).now ≤ (wAt E es (n + 1)).now := now_mono (Nat.le_succ n) hn
    have hstep := wAt_succ E es (show n < es.length by omega)
    rw [hstep]
    refine step_lotS hA (wAt_ok hA n) (ih (by omega) (by omega)) es[n] ?_
    intro htick
    refine hσ n (by omega) (by rw [List.getElem?_eq_getElem (by omega), htick]) ?_
    have := hnH; rw [hstep, step_now, htick] at this; simpa using this

open Classical in
/-- **Honest successes are the lottery's up to the horizon.** -/
theorem hon_count_upto (hA : Assm E) {Hz : ℕ} (hσ : TickStates E es σ Hz)
    (hKh : ∀ b B, (wF E es).st b = some B → IsHon B → B.hdr.slot ≤ Hz → K b) {i : ℕ} (h1 : 1 ≤ i)
    (h2 : i ≤ (wF E es).now) (h3 : i ≤ Hz) : (WS E es K i).1 = (lotStrS E σ (lateAt E es) i).1 := by
  have hw := wAt_ok (es := es) hA es.length
  have hS := hw.store
  obtain ⟨n, hnl, hni⟩ := exists_index_now (E := E) (es := es) h2
  have hl := lot_uptoS hA hσ n hnl (by omega)
  have hext := store_mono (m := es.length) (es := es) hA hnl
  -- honest blocks of slot `i` are already stored at `n`
  have hat : ∀ v B, (wF E es).st v = some B → IsHon B → B.hdr.slot = i → (wAt E es n).st v = some B :=
    fun v B hB hBh hsl => (wAt_le hA hnl).old hB hBh (by omega)
  have hng : ∀ v, slotOf (wF E es).st v = i → v ≠ genesisId := by
    intro v hv h0; rw [h0, slotOf_genesis hS] at hv; omega
  show ((FT E es K).V.filter (fun v => honL (wF E es).st (Late E es) v = true ∧ slotOf (wF E es).st v = i)).card =
    (E.nodes.filter (fun j => actS E σ j i && !decide (lateAt E es j i))).length
  rw [← List.toFinset_card_of_nodup (hA.nodup.filter _)]
  apply Finset.card_bij (fun v _ => sigOf (wF E es).st v)
  · intro v hv
    simp only [Finset.mem_filter] at hv
    obtain ⟨hvF, hhL, hsl⟩ := hv
    have hh := honB_of_honL hhL
    have hnl := not_late_of_honL hhL (hng v hsl)
    obtain ⟨B, hB, j, hj⟩ := honB_signed hh (hng v hsl) ((hw.used v).2 (mem_FTused.1 (mem_stree.1 hvF).1).1)
    rw [slotOf_eq hB] at hsl
    have hwin := hl.won v B j (hat v B hB ⟨j, hj⟩ hsl) hj
    rw [sigOf_eq hB hj, List.mem_toFinset, List.mem_filter]
    rw [hsl] at hwin
    refine ⟨(hw.hon v B j hB hj).node, ?_⟩
    simp only [Bool.and_eq_true, Bool.not_eq_true', decide_eq_false_iff_not]
    refine ⟨hwin, ?_⟩
    rintro ⟨b', B', hb', hs', hsl', hlate⟩
    obtain rfl := (hw.hon v B j hB hj).uniq b' B' hb' hs' (hsl'.trans hsl.symm)
    exact hnl hlate
  · intro v hv v' hv' heq
    simp only [Finset.mem_filter] at hv hv'
    obtain ⟨hvF, hh, hsl⟩ := hv
    obtain ⟨hvF', hh', hsl'⟩ := hv'
    replace hh := honB_of_honL hh
    replace hh' := honB_of_honL hh'
    obtain ⟨B, hB, j, hj⟩ := honB_signed hh (hng v hsl) ((hw.used v).2 (mem_FTused.1 (mem_stree.1 hvF).1).1)
    obtain ⟨B', hB', j', hj'⟩ := honB_signed hh' (hng v' hsl') ((hw.used v').2 (mem_FTused.1 (mem_stree.1 hvF').1).1)
    rw [sigOf_eq hB hj, sigOf_eq hB' hj'] at heq
    subst heq
    rw [slotOf_eq hB] at hsl; rw [slotOf_eq hB'] at hsl'
    exact (hw.hon v' B' j hB' hj').uniq v B hB hj (hsl.trans hsl'.symm)
  · intro j hj
    rw [List.mem_toFinset, List.mem_filter] at hj
    simp only [Bool.and_eq_true, Bool.not_eq_true', decide_eq_false_iff_not] at hj
    obtain ⟨b, B, hb, hsig, hsl⟩ := hl.made i j h1 (by omega) hj.1 hj.2.1
    have hbF := hext b B hb
    have hgood := (hon_stored hA hbF ⟨j, hsig⟩).1
    refine ⟨b, ?_, sigOf_eq hbF hsig⟩
    simp only [Finset.mem_filter]
    have hb0 : b ≠ genesisId := hng b (by rw [slotOf_eq hbF, hsl])
    refine ⟨mem_stree.2 ⟨mem_FTused.2 ⟨(hw.used b).1 ⟨B, hbF⟩, hKh b B hbF ⟨j, hsig⟩ (by omega)⟩, hgood⟩,
      (honL_iff hb0).2 ⟨honB_of hbF hsig, fun hlate => hj.2.2 ⟨b, B, hbF, hsig, hsl, hlate⟩⟩,
      by rw [slotOf_eq hbF, hsl]⟩

/-- **Weak domination up to the horizon.** -/
theorem advLeW_upto (hA : Assm E) {Hz : ℕ} (hσ : TickStates E es σ Hz)
    (hKh : ∀ b B, (wF E es).st b = some B → IsHon B → B.hdr.slot ≤ Hz → K b)
    (hσa : AdvStatesOK E es K σ) (hHN : Hz ≤ (wF E es).now) :
    AdvLeW Hz (WS E es K) (lotStrS E σ (lateAt E es)) :=
  ⟨fun _ h1 h2 => hon_count_upto hA hσ hKh h1 (by omega) h2, fun _ h => adv_domS hA hσa h⟩

end Cryptarchia
