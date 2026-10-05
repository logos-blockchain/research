import Cryptarchia.Proof.Settlement
import Cryptarchia.Settle.Mono

/-!
# The lottery string, for any assignment of epoch states to slots

`σ i` is the epoch state that the lottery of slot `i` runs under. The lottery
string `lotStrS σ` records per slot how many honest nodes hold a winning note
under `σ i` and whether the adversary does. Two hypotheses tie it to an
execution:

* every honest node, when it leads at slot `t`, derives `σ t` on its local chain;
* every adversarial block of the settlement tree (for the block predicate `K`)
  is validated under `σ` of its slot.

Then the execution's string is dominated by the lottery string (`advLe_lotS`).
`Proof/Lottery.lean` is the first-epoch instance (`σ = es0`, `K = True`);
`Proof/LotteryE.lean` is the multi-epoch one (`σ` = canonical states,
`K` = consistency).
-/

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

theorem store_genesis {es : List Event} (hord : E.OrderOK) (n : ℕ) :
    (wAt E es n).st genesisId = some genesisBlock := by
  have h0 : (wAt E es 0).st genesisId = some genesisBlock := by rw [wAt_zero]; simp [World.init]
  exact store_mono (es := es) hord (Nat.zero_le n) _ _ h0

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

/-- **The lottery invariant of a world**: every honest block is the single
proposal of a node that won its slot, and every such win produced a block. -/
structure LotOKS (E : Env) (σ : ℕ → EpochState) (w : World) : Prop where
  won : ∀ b B j, w.st b = some B → B.hdr.signer = .honest j →
    j ∈ E.nodes ∧ actS E σ j B.hdr.slot = true ∧ 1 ≤ B.hdr.slot ∧ B.hdr.slot ≤ w.now
  uniq : ∀ b b' B B' j, w.st b = some B → w.st b' = some B' → B.hdr.signer = .honest j →
    B'.hdr.signer = .honest j → B.hdr.slot = B'.hdr.slot → b = b'
  made : ∀ i j, 1 ≤ i → i ≤ w.now → j ∈ E.nodes → actS E σ j i = true →
    ∃ b B, w.st b = some B ∧ B.hdr.signer = .honest j ∧ B.hdr.slot = i

theorem init_lotS : LotOKS E σ World.init := by
  refine ⟨?_, ?_, ?_⟩
  · intro b B j hb hj
    simp only [World.init] at hb; split at hb
    · cases hb; simp [genesisBlock] at hj
    · simp at hb
  · intro b b' B B' j hb _ hj _ _
    simp only [World.init] at hb; split at hb
    · cases hb; simp [genesisBlock] at hj
    · simp at hb
  · intro i j h1 h2; simp [World.init] at h2; omega

theorem lead_off {w : World} {i : ℕ} (hio : E.online i w.now = false) : w.lead E i = w := by
  unfold World.lead
  simp [hio]

theorem lead_none {w : World} {i : ℕ} (hio : E.online i w.now = true)
    (hp : propose E.c w.st E.L E.O E.G i w.now w.fresh (w.node i) = none) : w.lead E i = w := by
  unfold World.lead
  simp only [hio, Bool.not_true, Bool.false_eq_true, if_false]
  rw [hp]

theorem lead_some {w : World} {i : ℕ} {C : Block} (hio : E.online i w.now = true)
    (hp : propose E.c w.st E.L E.O E.G i w.now w.fresh (w.node i) = some C) :
    (w.lead E i).st = (w.add C).st ∧ (w.lead E i).now = w.now := by
  unfold World.lead
  simp only [hio, Bool.not_true, Bool.false_eq_true, if_false]
  rw [hp]
  exact ⟨rfl, rfl⟩

/-- **One lead step, precisely.** With every node online, node `i` proposes exactly
when it wins the current slot, adding one block signed by it at that slot under
a fresh ID. -/
theorem lead_specS (hN : HonestStake E.L) {w₀ : World}
    (hw₀ : WorldOK E w₀) (i : ℕ)
    (hσ : E.online i w₀.now = true →
      epochState E.c E.L E.O E.G (chainUp w₀.st (w₀.node i).cloc) (E.c.epochOf w₀.now) = σ w₀.now) :
    (w₀.lead E i).now = w₀.now ∧
      ((actS E σ i w₀.now = false ∧ (w₀.lead E i).st = w₀.st) ∨
       (actS E σ i w₀.now = true ∧ ∃ C, C.hdr.signer = .honest i ∧ C.hdr.slot = w₀.now ∧
          C.hdr.id ∉ w₀.used ∧ (w₀.lead E i).st = (w₀.add C).st)) := by
  cases hio : E.online i w₀.now with
  | false =>
    rw [lead_off hio]
    exact ⟨rfl, Or.inl ⟨by simp [actS, hio], rfl⟩⟩
  | true =>
  have hpi := propose_iffS (t := w₀.now) (newId := w₀.fresh) (j := i) hN (hw₀.nodes i) (hσ hio)
  have hact : actS E σ i w₀.now = honWinsS E σ i w₀.now := by simp [actS, hio]
  rw [hact]
  cases hp : propose E.c w₀.st E.L E.O E.G i w₀.now w₀.fresh (w₀.node i) with
  | none =>
    rw [lead_none hio hp]
    refine ⟨rfl, Or.inl ⟨?_, rfl⟩⟩
    cases hc : honWinsS E σ i w₀.now
    · rfl
    · obtain ⟨C, hC⟩ := hpi.2 hc
      rw [hp] at hC; cases hC
  | some C =>
    obtain ⟨hid, hsig, -, hsl⟩ := propose_id hp
    obtain ⟨hst, hnw⟩ := lead_some hio hp
    exact ⟨hnw, Or.inr ⟨hpi.1 ⟨C, hp⟩, C, hsig, hsl, by rw [hid]; exact fresh_not_used w₀, hst⟩⟩

theorem lead_other (w : World) {i j : ℕ} (hji : j ≠ i) : (w.lead E i).node j = w.node j := by
  unfold World.lead
  split
  · rfl
  · split
    · rfl
    · simp only; rw [if_neg hji]; rfl

/-- A tick keeps the lottery invariant. -/
theorem tick_lotS (hN : HonestStake E.L) (hord : E.OrderOK)
    (hnd : E.nodes.Nodup) {w : World} (hw : WorldOK E w) (hl : LotOKS E σ w)
    (hσ : ∀ j ∈ E.nodes, E.online j (w.now + 1) = true →
      epochState E.c E.L E.O E.G (chainUp w.st (w.node j).cloc) (E.c.epochOf (w.now + 1)) = σ (w.now + 1)) :
    LotOKS E σ (w.step E .tick) := by
  simp only [World.step]
  set w₁ : World := { w with now := w.now + 1 } with hw₁
  -- the fold over the nodes
  have key : ∀ (l : List ℕ) (w₀ : World), l.Nodup → (∀ j ∈ l, j ∈ E.nodes) → WorldOK E w₀ →
      w₀.now = w.now + 1 → StoreExt w.st w₀.st → (∀ j ∈ l, w₀.node j = w.node j) →
      (∀ b B j, w₀.st b = some B → B.hdr.signer = .honest j →
        j ∈ E.nodes ∧ actS E σ j B.hdr.slot = true ∧ 1 ≤ B.hdr.slot ∧ B.hdr.slot ≤ w.now + 1) →
      (∀ b b' B B' j, w₀.st b = some B → w₀.st b' = some B' → B.hdr.signer = .honest j →
        B'.hdr.signer = .honest j → B.hdr.slot = B'.hdr.slot → b = b') →
      (∀ j ∈ l, ∀ b B, w₀.st b = some B → B.hdr.signer = .honest j → B.hdr.slot ≠ w.now + 1) →
      (∀ j ∈ E.nodes, j ∉ l → actS E σ j (w.now + 1) = true →
        ∃ b B, w₀.st b = some B ∧ B.hdr.signer = .honest j ∧ B.hdr.slot = w.now + 1) →
      (∀ b B j, (l.foldl (World.lead E) w₀).st b = some B → B.hdr.signer = .honest j →
        j ∈ E.nodes ∧ actS E σ j B.hdr.slot = true ∧ 1 ≤ B.hdr.slot ∧ B.hdr.slot ≤ w.now + 1) ∧
      (∀ b b' B B' j, (l.foldl (World.lead E) w₀).st b = some B →
        (l.foldl (World.lead E) w₀).st b' = some B' → B.hdr.signer = .honest j →
        B'.hdr.signer = .honest j → B.hdr.slot = B'.hdr.slot → b = b') ∧
      (∀ j ∈ E.nodes, actS E σ j (w.now + 1) = true →
        ∃ b B, (l.foldl (World.lead E) w₀).st b = some B ∧ B.hdr.signer = .honest j ∧
          B.hdr.slot = w.now + 1) ∧
      StoreExt w₀.st (l.foldl (World.lead E) w₀).st := by
    intro l
    induction l with
    | nil =>
      intro w₀ _ _ _ _ _ _ h1 h2 _ h4
      exact ⟨h1, h2, fun j hj hw' => h4 j hj (by simp) hw', StoreExt.refl _⟩
    | cons i is ih =>
      intro w₀ hnd' hsub hw₀ hnow hext hsame h1 h2 h3 h4
      simp only [List.foldl_cons]
      have hi : i ∈ E.nodes := hsub i List.mem_cons_self
      have hσ₀ : E.online i w₀.now = true →
          epochState E.c E.L E.O E.G (chainUp w₀.st (w₀.node i).cloc) (E.c.epochOf w₀.now) = σ w₀.now := by
        intro hio
        rw [hsame i List.mem_cons_self, hnow,
          chainUp_ext hext ((hw.nodes i).rooted _ (hw.nodes i).cloc)]
        rw [hnow] at hio
        exact hσ i hi hio
      have hlead := lead_ok E hord hw₀ i
      obtain ⟨hnow', hcase⟩ := lead_specS hN hw₀ i hσ₀
      have hext' : StoreExt w₀.st (w₀.lead E i).st := hlead.2.1
      -- the store after `i`'s lead, block by block
      have hnewblk : ∀ b B, (w₀.lead E i).st b = some B → w₀.st b = some B ∨
          (w₀.st b = none ∧ B.hdr.signer = .honest i ∧ B.hdr.slot = w.now + 1) := by
        intro b B hb
        rcases hcase with ⟨-, hst⟩ | ⟨-, C, hCs, hCsl, hCu, hst⟩
        · rw [hst] at hb; exact Or.inl hb
        · rw [hst] at hb
          by_cases hbC : b = C.hdr.id
          · subst hbC
            have hBC : B = C := by simp [World.add] at hb; exact hb.symm
            subst hBC
            refine Or.inr ⟨?_, hCs, by rw [hCsl, hnow]⟩
            cases hc : w₀.st B.hdr.id with
            | none => rfl
            | some _ => exact absurd ((hw₀.used _).1 ⟨_, hc⟩) hCu
          · left; simpa [World.add, hbC] using hb
      apply (ih _ (List.nodup_cons.1 hnd').2 (fun j hj => hsub j (List.mem_cons_of_mem _ hj)) hlead.1
        (by rw [hnow', hnow]) (hext.trans hext')
        (fun j hj => by
          have hji : j ≠ i := fun h => (List.nodup_cons.1 hnd').1 (h ▸ hj)
          rw [lead_other w₀ hji]; exact hsame j (List.mem_cons_of_mem _ hj))
        ?_ ?_ ?_ ?_) |> fun h => ⟨h.1, h.2.1, h.2.2.1, hext'.trans h.2.2.2⟩
      · intro b B j hb hj
        rcases hnewblk b B hb with hb' | ⟨hn, hsig, hsl⟩
        · exact h1 b B j hb' hj
        · rw [hsig] at hj; cases hj
          rcases hcase with ⟨-, hst⟩ | ⟨hw', -⟩
          · rw [hst, hn] at hb; cases hb
          · refine ⟨hi, by rw [hsl, ← hnow]; exact hw', by omega, by omega⟩
      · intro b b' B B' j hb hb' hj hj' hsl
        rcases hnewblk b B hb with hb1 | ⟨hn1, hs1, hl1⟩ <;> rcases hnewblk b' B' hb' with hb2 | ⟨hn2, hs2, hl2⟩
        · exact h2 b b' B B' j hb1 hb2 hj hj' hsl
        · rw [hs2] at hj'; cases hj'
          exact absurd (hsl.trans hl2) (h3 i List.mem_cons_self b B hb1 hj)
        · rw [hs1] at hj; cases hj
          exact absurd (hsl.symm.trans hl1) (h3 i List.mem_cons_self b' B' hb2 hj')
        · -- two new blocks: the lead adds only one
          rcases hcase with ⟨-, hst⟩ | ⟨-, C, -, -, -, hst⟩
          · rw [hst] at hb; rw [hb] at hn1; simp at hn1
          · rw [hst] at hb hb'
            by_cases h1C : b = C.hdr.id <;> by_cases h2C : b' = C.hdr.id
            · rw [h1C, h2C]
            · have : (w₀.add C).st b' = w₀.st b' := by simp [World.add, h2C]
              rw [this, hn2] at hb'; simp at hb'
            · have : (w₀.add C).st b = w₀.st b := by simp [World.add, h1C]
              rw [this, hn1] at hb; simp at hb
            · have : (w₀.add C).st b = w₀.st b := by simp [World.add, h1C]
              rw [this, hn1] at hb; simp at hb
      · intro j hj b B hb hsig
        rcases hnewblk b B hb with hb' | ⟨-, hs, -⟩
        · exact h3 j (List.mem_cons_of_mem _ hj) b B hb' hsig
        · rw [hsig] at hs; cases hs
          exact absurd hj (List.nodup_cons.1 hnd').1
      · intro j hj hjn hwin
        by_cases hji : j = i
        · subst hji
          rcases hcase with ⟨hw', -⟩ | ⟨-, C, hCs, hCsl, -, hst⟩
          · rw [hnow] at hw'; rw [hw'] at hwin; cases hwin
          · refine ⟨C.hdr.id, C, by rw [hst]; simp [World.add], hCs, by rw [hCsl, hnow]⟩
        · obtain ⟨b, B, hb, hsig, hsl⟩ := h4 j hj (by
            intro hm; rcases List.mem_cons.1 hm with h | h
            · exact hji h
            · exact hjn h) hwin
          exact ⟨b, B, hext' b B hb, hsig, hsl⟩
  obtain ⟨k1, k2, k3, k4⟩ := key E.nodes w₁ hnd (fun _ h => h) ⟨hw.store, hw.used, hw.nodes⟩ rfl
    (StoreExt.refl _) (fun _ _ => rfl)
    (fun b B j hb hj => by
      obtain ⟨a1, a2, a3, a4⟩ := hl.won b B j hb hj; exact ⟨a1, a2, a3, by omega⟩)
    hl.uniq
    (fun j _ b B hb hj hsl => by have := (hl.won b B j hb hj).2.2.2; omega)
    (fun j _ hjn _ => absurd ‹j ∈ E.nodes› hjn)
  have hnow : (E.nodes.foldl (World.lead E) w₁).now = w.now + 1 := by
    have : ∀ (l : List ℕ) (w₀ : World), (l.foldl (World.lead E) w₀).now = w₀.now := by
      intro l; induction l with
      | nil => intro; rfl
      | cons i is ih =>
        intro w₀; simp only [List.foldl_cons]; rw [ih]
        unfold World.lead; split
        · rfl
        · split <;> rfl
    rw [this]
  refine ⟨?_, k2, ?_⟩
  · intro b B j hb hj; rw [hnow]; exact k1 b B j hb hj
  · intro i j h1 h2 hj hwin
    rw [hnow] at h2
    rcases Nat.lt_or_ge i (w.now + 1) with hlt | hge
    · obtain ⟨b, B, hb, hsig, hsl⟩ := hl.made i j h1 (by omega) hj hwin
      exact ⟨b, B, k4 b B hb, hsig, hsl⟩
    · have : i = w.now + 1 := by omega
      subst this; exact k3 j hj hwin

/-- Every event keeps the lottery invariant (a tick within the first epoch). -/
theorem step_lotS (hN : HonestStake E.L) (hord : E.OrderOK)
    (hnd : E.nodes.Nodup) {w : World} (hw : WorldOK E w) (hl : LotOKS E σ w) (e : Event)
    (hσ : e = .tick → ∀ j ∈ E.nodes, E.online j (w.now + 1) = true →
      epochState E.c E.L E.O E.G (chainUp w.st (w.node j).cloc)
      (E.c.epochOf (w.now + 1)) = σ (w.now + 1)) : LotOKS E σ (w.step E e) := by
  cases e with
  | tick => exact tick_lotS hN hord hnd hw hl (hσ rfl)
  | deliver i b =>
    simp only [World.step]; split
    · exact ⟨hl.won, hl.uniq, hl.made⟩
    · exact hl
  | create B =>
    simp only [World.step]; split
    · rename_i hc
      simp only [Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at hc
      obtain ⟨hadv, hfr⟩ := hc
      have hfr' : B.hdr.id ∉ w.used := by
        intro hm; have := List.contains_iff_mem.2 hm; rw [hfr] at this; cases this
      have hext := (add_ok hw B hfr').1
      have hnew : ∀ b C, (w.add B).st b = some C → w.st b = some C ∨ C.hdr.signer = .adv := by
        intro b C hb
        by_cases hbB : b = B.hdr.id
        · right; simp [World.add, hbB] at hb; rw [← hb]; exact hadv
        · left; simpa [World.add, hbB] using hb
      refine ⟨?_, ?_, ?_⟩
      · intro b C j hb hj
        rcases hnew b C hb with h | h
        · exact hl.won b C j h hj
        · rw [h] at hj; cases hj
      · intro b b' C C' j hb hb' hj hj' hsl
        rcases hnew b C hb with h | h
        · rcases hnew b' C' hb' with h' | h'
          · exact hl.uniq b b' C C' j h h' hj hj' hsl
          · rw [h'] at hj'; cases hj'
        · rw [h] at hj; cases hj
      · intro i j h1 h2 hj hwin
        obtain ⟨b, C, hb, hs, hsl⟩ := hl.made i j h1 h2 hj hwin
        exact ⟨b, C, hext b C hb, hs, hsl⟩
    · exact hl

/-- The lottery each honest node runs at every tick of the execution is `σ`'s. -/
def StatesOK (E : Env) (es : List Event) (σ : ℕ → EpochState) : Prop :=
  ∀ n < es.length, es[n]? = some .tick → ∀ j ∈ E.nodes, E.online j ((wAt E es n).now + 1) = true →
    epochState E.c E.L E.O E.G (chainUp (wAt E es n).st ((wAt E es n).node j).cloc)
      (E.c.epochOf ((wAt E es n).now + 1)) = σ ((wAt E es n).now + 1)

/-- **The lottery invariant holds throughout an execution.** -/
theorem lot_allS (hA : Assm E) (hN : HonestStake E.L) (hσ : StatesOK E es σ) :
    ∀ n ≤ es.length, LotOKS E σ (wAt E es n) := by
  intro n
  induction n with
  | zero => intro _; rw [wAt_zero]; exact init_lotS
  | succ n ih =>
    intro hn
    rw [wAt_succ E es (by omega)]
    refine step_lotS hN hA.ord hA.nodup (wAt_ok hA.ord n) (ih (by omega)) es[n] ?_
    intro htick
    exact hσ n (by omega) (by rw [List.getElem?_eq_getElem (by omega), htick])

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

open Classical in
/-- **Honest successes are the lottery's**: at every slot of the horizon, the
settlement tree has one honest block per honest node that won the slot. -/
theorem hon_countS (hA : Assm E) (hN : HonestStake E.L) (hσ : StatesOK E es σ)
    (hKh : ∀ b B, (wF E es).st b = some B → IsHon B → K b) {i : ℕ} (h1 : 1 ≤ i)
    (h2 : i ≤ (wF E es).now) : (WS E es K i).1 = (lotStrS E σ (lateAt E es) i).1 := by
  have hw := wAt_ok (es := es) hA.ord es.length
  have hS := hw.store
  have hl := lot_allS hA hN hσ es.length le_rfl
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
    obtain ⟨hjn, hwin, -, -⟩ := hl.won v B j hB hj
    rw [sigOf_eq hB hj, List.mem_toFinset, List.mem_filter]
    rw [slotOf_eq hB] at hsl; rw [hsl] at hwin
    refine ⟨hjn, ?_⟩
    simp only [Bool.and_eq_true, Bool.not_eq_true', decide_eq_false_iff_not]
    refine ⟨hwin, ?_⟩
    rintro ⟨b', B', hb', hs', hsl', hlate⟩
    have := hl.uniq v b' B B' j hB hb' hj hs' (hsl.trans hsl'.symm)
    subst this; exact hnl hlate
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
    exact hl.uniq v v' B B' j hB hB' hj hj' (hsl.trans hsl'.symm)
  · intro j hj
    rw [List.mem_toFinset, List.mem_filter] at hj
    simp only [Bool.and_eq_true, Bool.not_eq_true', decide_eq_false_iff_not] at hj
    obtain ⟨b, B, hb, hsig, hsl⟩ := hl.made i j h1 h2 hj.1 hj.2.1
    have hgood := (hon_stored hA le_rfl hb ⟨j, hsig⟩).1
    refine ⟨b, ?_, sigOf_eq hb hsig⟩
    simp only [Finset.mem_filter]
    have hb0 : b ≠ genesisId := hng b (by rw [slotOf_eq hb, hsl])
    refine ⟨mem_stree.2 ⟨mem_FTused.2 ⟨(hw.used b).1 ⟨B, hb⟩, hKh b B hb ⟨j, hsig⟩⟩, hgood⟩,
      (honL_iff hb0).2 ⟨honB_of hb hsig, fun hlate => hj.2.2 ⟨b, B, hb, hsig, hsl, hlate⟩⟩,
      by rw [slotOf_eq hb, hsl]⟩

open Classical in
/-- After the horizon the execution string has no honest successes. -/
theorem hon_lateS {i : ℕ} (h : (wF E es).now < i) : (WS E es K i).1 = 0 := by
  show ((FT E es K).V.filter (fun v => honL (wF E es).st (Late E es) v = true ∧ slotOf (wF E es).st v = i)).card = 0
  rw [Finset.card_eq_zero, Finset.filter_eq_empty_iff]
  rintro v hv ⟨-, hsl⟩
  have := (mem_stree.1 hv).2.2.1
  omega

/-- Adversarial blocks of the tree are validated under `σ` of their slot. -/
def AdvStatesOK (E : Env) (es : List Event) (K : ℕ → Prop) (σ : ℕ → EpochState) : Prop :=
  ∀ v ∈ (FT E es K).V, ∀ B, (wF E es).st v = some B → B.hdr.signer = .adv →
    epochState E.c E.L E.O E.G (chainUp (wF E es).st B.hdr.parent) (E.c.epochOf B.hdr.slot) = σ B.hdr.slot

open Classical in
/-- **Adversarial slots of the execution are adversarial lottery wins.** -/
theorem adv_domS (hA : Assm E) (hσa : AdvStatesOK E es K σ) {i : ℕ} (h : (WS E es K i).2 = true) :
    (lotStrS E σ (lateAt E es) i).2 = true := by
  have hw := wAt_ok (es := es) hA.ord es.length
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

/-- **The execution string is dominated by the lottery string.** -/
theorem advLe_lotS (hA : Assm E) (hN : HonestStake E.L) (hσ : StatesOK E es σ)
    (hKh : ∀ b B, (wF E es).st b = some B → IsHon B → K b) (hσa : AdvStatesOK E es K σ) :
    AdvLe (wF E es).now (WS E es K) (lotStrS E σ (lateAt E es)) :=
  ⟨fun _ h1 h2 => hon_countS hA hN hσ hKh h1 h2, fun _ h => hon_lateS h, fun _ h => adv_domS hA hσa h⟩


/-! ## Up to a horizon -/

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
theorem lot_uptoS (hA : Assm E) (hN : HonestStake E.L) {Hz : ℕ}
    (hσ : ∀ n < es.length, es[n]? = some .tick → (wAt E es n).now + 1 ≤ Hz → ∀ j ∈ E.nodes,
      E.online j ((wAt E es n).now + 1) = true → epochState E.c E.L E.O E.G (chainUp (wAt E es n).st ((wAt E es n).node j).cloc)
        (E.c.epochOf ((wAt E es n).now + 1)) = σ ((wAt E es n).now + 1)) :
    ∀ n ≤ es.length, (wAt E es n).now ≤ Hz → LotOKS E σ (wAt E es n) := by
  intro n
  induction n with
  | zero => intro _ _; rw [wAt_zero]; exact init_lotS
  | succ n ih =>
    intro hn hnH
    have hmono : (wAt E es n).now ≤ (wAt E es (n + 1)).now := now_mono (Nat.le_succ n) hn
    have hstep := wAt_succ E es (show n < es.length by omega)
    rw [hstep]
    refine step_lotS hN hA.ord hA.nodup (wAt_ok hA.ord n) (ih (by omega) (by omega)) es[n] ?_
    intro htick
    refine hσ n (by omega) (by rw [List.getElem?_eq_getElem (by omega), htick]) ?_
    have := hnH; rw [hstep, step_now, htick] at this; simpa using this

open Classical in
/-- **Honest successes are the lottery's up to the horizon.** -/
theorem hon_count_upto (hA : Assm E) (hN : HonestStake E.L) {Hz : ℕ}
    (hσ : ∀ n < es.length, es[n]? = some .tick → (wAt E es n).now + 1 ≤ Hz → ∀ j ∈ E.nodes,
      E.online j ((wAt E es n).now + 1) = true → epochState E.c E.L E.O E.G (chainUp (wAt E es n).st ((wAt E es n).node j).cloc)
        (E.c.epochOf ((wAt E es n).now + 1)) = σ ((wAt E es n).now + 1))
    (hKh : ∀ b B, (wF E es).st b = some B → IsHon B → B.hdr.slot ≤ Hz → K b) {i : ℕ} (h1 : 1 ≤ i)
    (h2 : i ≤ (wF E es).now) (h3 : i ≤ Hz) : (WS E es K i).1 = (lotStrS E σ (lateAt E es) i).1 := by
  have hw := wAt_ok (es := es) hA.ord es.length
  have hS := hw.store
  obtain ⟨n, hnl, hni⟩ := exists_index_now (E := E) (es := es) h2
  have hl := lot_uptoS hA hN hσ n hnl (by omega)
  have hext := store_mono (m := es.length) (es := es) hA.ord hnl
  -- honest blocks of slot `i` are already stored at `n`
  have hat : ∀ v B, (wF E es).st v = some B → IsHon B → B.hdr.slot = i → (wAt E es n).st v = some B := by
    intro v B hB hBh hsl
    cases hc : (wAt E es n).st v with
    | some B' => have := hext v B' hc; rw [hB] at this; rw [Option.some_inj.1 this]
    | none =>
      have := created_later (es := es) hA.ord hA.exec hA.nodup hA.sane es.length hnl le_rfl v B hB hBh hc
      omega
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
    obtain ⟨hjn, hwin, -, -⟩ := hl.won v B j (hat v B hB ⟨j, hj⟩ hsl) hj
    rw [sigOf_eq hB hj, List.mem_toFinset, List.mem_filter]
    rw [hsl] at hwin
    refine ⟨hjn, ?_⟩
    simp only [Bool.and_eq_true, Bool.not_eq_true', decide_eq_false_iff_not]
    refine ⟨hwin, ?_⟩
    rintro ⟨b', B', hb', hs', hsl', hlate⟩
    have := hl.uniq v b' B B' j (hat v B hB ⟨j, hj⟩ hsl) (hat b' B' hb' ⟨j, hs'⟩ hsl') hj hs'
      (hsl.trans hsl'.symm)
    subst this; exact hnl hlate
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
    exact hl.uniq v v' B B' j (hat v B hB ⟨j, hj⟩ hsl) (hat v' B' hB' ⟨j, hj'⟩ hsl') hj hj'
      (hsl.trans hsl'.symm)
  · intro j hj
    rw [List.mem_toFinset, List.mem_filter] at hj
    simp only [Bool.and_eq_true, Bool.not_eq_true', decide_eq_false_iff_not] at hj
    obtain ⟨b, B, hb, hsig, hsl⟩ := hl.made i j h1 (by omega) hj.1 hj.2.1
    have hbF := hext b B hb
    have hgood := (hon_stored hA le_rfl hbF ⟨j, hsig⟩).1
    refine ⟨b, ?_, sigOf_eq hbF hsig⟩
    simp only [Finset.mem_filter]
    have hb0 : b ≠ genesisId := hng b (by rw [slotOf_eq hbF, hsl])
    refine ⟨mem_stree.2 ⟨mem_FTused.2 ⟨(hw.used b).1 ⟨B, hbF⟩, hKh b B hbF ⟨j, hsig⟩ (by omega)⟩, hgood⟩,
      (honL_iff hb0).2 ⟨honB_of hbF hsig, fun hlate => hj.2.2 ⟨b, B, hbF, hsig, hsl, hlate⟩⟩,
      by rw [slotOf_eq hbF, hsl]⟩

/-- **Weak domination up to the horizon.** -/
theorem advLeW_upto (hA : Assm E) (hN : HonestStake E.L) {Hz : ℕ}
    (hσ : ∀ n < es.length, es[n]? = some .tick → (wAt E es n).now + 1 ≤ Hz → ∀ j ∈ E.nodes,
      E.online j ((wAt E es n).now + 1) = true → epochState E.c E.L E.O E.G (chainUp (wAt E es n).st ((wAt E es n).node j).cloc)
        (E.c.epochOf ((wAt E es n).now + 1)) = σ ((wAt E es n).now + 1))
    (hKh : ∀ b B, (wF E es).st b = some B → IsHon B → B.hdr.slot ≤ Hz → K b)
    (hσa : AdvStatesOK E es K σ) (hHN : Hz ≤ (wF E es).now) :
    AdvLeW Hz (WS E es K) (lotStrS E σ (lateAt E es)) :=
  ⟨fun _ h1 h2 => hon_count_upto hA hN hσ hKh h1 (by omega) h2, fun _ h => adv_domS hA hσa h⟩

end Cryptarchia
