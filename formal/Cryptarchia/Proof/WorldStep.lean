import Cryptarchia.Proof.NodeStep

/-!
# Every event keeps the world well formed

The store only grows (`StoreExt`); rooted blocks keep their chains, heights and
validity when it does; and every event (a tick with honest proposals, a
delivery, an adversarial block) keeps the store well formed, keeps every node
well formed, and never lowers any node's local chain.
-/

namespace Cryptarchia

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis}

/-- `st'` extends `st`. -/
def StoreExt (st st' : Store) : Prop := ∀ b blk, st b = some blk → st' b = some blk

variable {st st' : Store}

theorem StoreExt.refl (st : Store) : StoreExt st st := fun _ _ h => h

theorem StoreExt.trans {st'' : Store} (h1 : StoreExt st st') (h2 : StoreExt st' st'') :
    StoreExt st st'' := fun b blk h => h2 b blk (h1 b blk h)

section Ext

variable (hx : StoreExt st st')
include hx

theorem slotOf_ext {b : ℕ} (hb : ∃ blk, st b = some blk) : slotOf st' b = slotOf st b := by
  obtain ⟨blk, h⟩ := hb; simp [slotOf, h, hx _ _ h]

theorem parentOf_ext {b : ℕ} (hb : ∃ blk, st b = some blk) : parentOf st' b = parentOf st b := by
  obtain ⟨blk, h⟩ := hb; simp [parentOf, h, hx _ _ h]

theorem chainIds_ext {b : ℕ} (hb : Rooted st b) : chainIds st' b = chainIds st b := by
  unfold chainIds; rw [chain_mono hx hb]

theorem chainUp_ext {b : ℕ} (hb : Rooted st b) : chainUp st' b = chainUp st b := by
  unfold chainUp; rw [chain_mono hx hb]

theorem height_ext {b : ℕ} (hb : Rooted st b) : height st' b = height st b := by
  unfold height; rw [chain_mono hx hb]

theorem blockAtDepth_ext {b : ℕ} (hb : Rooted st b) (d : ℕ) :
    blockAtDepth st' b d = blockAtDepth st b d := by
  unfold blockAtDepth; rw [chainIds_ext hx hb]

theorem lca_ext {a b : ℕ} (ha : Rooted st a) (hb : Rooted st b) : lca st' a b = lca st a b := by
  unfold lca; rw [chainIds_ext hx ha, chainIds_ext hx hb]

theorem tips_ext {T : List ℕ} (hT : ∀ y ∈ T, ∃ blk, st y = some blk) : tips st' T = tips st T := by
  unfold tips
  apply List.filter_congr
  intro b _
  have : (T.any fun y => decide (y ≠ b ∧ parentOf st' y = b)) =
      (T.any fun y => decide (y ≠ b ∧ parentOf st y = b)) := by
    rw [Bool.eq_iff_iff]
    simp only [List.any_eq_true, decide_eq_true_eq]
    constructor <;> rintro ⟨y, hy, h1, h2⟩ <;> refine ⟨y, hy, h1, ?_⟩
    · rwa [parentOf_ext hx (hT y hy)] at h2
    · rwa [parentOf_ext hx (hT y hy)]
  rw [this]

theorem genuine_ext {h : Header} (hg : genuine st h = true) : genuine st' h = true := by
  unfold genuine at *
  cases hb : st h.id with
  | none => rw [hb] at hg; simp at hg
  | some b => rw [hb] at hg; rw [hx _ _ hb]; exact hg

theorem validUncle_ext (hS : StoreOK st) {par slotA : ℕ} (hpar : Rooted st par) {U : Header}
    (hv : validUncle c st L O G par slotA U = true) : validUncle c st' L O G par slotA U = true := by
  unfold validUncle at *
  simp only [Bool.and_eq_true, decide_eq_true_eq, List.contains_iff_mem, Bool.not_eq_true'] at *
  obtain ⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩ := hv
  have hUp : Rooted st U.parent := (anc_height hS hpar h1).1
  refine ⟨⟨⟨⟨⟨?_, ?_⟩, h3⟩, ?_⟩, ?_⟩, genuine_ext hx h6⟩
  · rwa [chainIds_ext hx hpar]
  · rwa [chainIds_ext hx hpar]
  · rwa [slotOf_ext hx hUp.exists_blk]
  · rwa [chainUp_ext hx hpar, chainUp_ext hx hUp]

theorem validCore_ext (hS : StoreOK st) {B : Block} (hpar : Rooted st B.hdr.parent)
    (hv : validCore c st L O G B = true) : validCore c st' L O G B = true := by
  unfold validCore at *
  simp only [Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true] at *
  obtain ⟨⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩, h7⟩ := hv
  refine ⟨⟨⟨⟨⟨⟨h1, h2⟩, ?_⟩, ?_⟩, genuine_ext hx h5⟩, ?_⟩, ?_⟩
  · rwa [slotOf_ext hx hpar.exists_blk]
  · rwa [chainUp_ext hx hpar]
  · intro U hU; exact validUncle_ext hx hS hpar (h6 U hU)
  · rwa [chainUp_ext hx hpar]

theorem nodeOK_ext (hS : StoreOK st) {k : ℕ} {s : NodeState} (hs : NodeOK k st L O G c s) :
    NodeOK k st' L O G c s := by
  refine ⟨fun y hy => (hs.rooted y hy).mono hx, ?_, ?_, hs.gen, hs.cloc, ?_, hs.rule⟩
  · intro y hy
    rcases hs.valid y hy with h | ⟨B, hB, hv⟩
    · exact Or.inl h
    · refine Or.inr ⟨B, hx _ _ hB, ?_⟩
      have hyr := hs.rooted y hy
      have hy0 : y ≠ genesisId := by
        intro h; subst h
        unfold validCore at hv; simp only [Bool.and_eq_true, decide_eq_true_eq] at hv
        have := hS.idOK _ _ hB
        exact hv.1.1.1.1.1.1 this
      obtain ⟨blk, hbk, hpr, -⟩ := hyr.inv hy0
      rw [hbk] at hB; cases hB
      exact validCore_ext hx hS hpr hv
  · intro y hy
    rw [parentOf_ext hx (hs.rooted y hy).exists_blk]; exact hs.closed y hy
  · rw [hs.bimm, blockAtDepth_ext hx (hs.rooted _ hs.cloc)]

end Ext

/-! ## The world invariant -/

/-- The world is well formed. -/
structure WorldOK (E : Env) (w : World) : Prop where
  store : StoreOK w.st
  used : ∀ b, (∃ blk, w.st b = some blk) ↔ b ∈ w.used
  nodes : ∀ i, NodeOK E.c.k w.st E.L E.O E.G E.c (w.node i)

theorem fresh_not_used (w : World) : w.fresh ∉ w.used := by
  intro h
  have : ∀ l : List ℕ, ∀ a, ∀ x ∈ l, x ≤ l.foldl max a := by
    intro l
    induction l with
    | nil => simp
    | cons y ys ih =>
      intro a x hx
      simp only [List.foldl_cons]
      rcases List.mem_cons.1 hx with rfl | hx
      · have : ∀ l : List ℕ, ∀ a, a ≤ l.foldl max a := by
          intro l; induction l with
          | nil => simp
          | cons z zs ih' => intro a; simp only [List.foldl_cons]; exact le_trans (le_max_left _ _) (ih' _)
        exact le_trans (le_max_right _ _) (this ys _)
      · exact ih _ x hx
  have := this w.used 0 w.fresh h
  unfold World.fresh at this; omega

theorem genesis_used {E : Env} {w : World} (hw : WorldOK E w) : genesisId ∈ w.used := by
  obtain ⟨g, hg, -, -⟩ := hw.store.gen
  exact (hw.used genesisId).1 ⟨g, hg⟩

/-- Adding a block under a fresh ID extends the store and keeps it well formed. -/
theorem add_ok {E : Env} {w : World} (hw : WorldOK E w) (B : Block) (hfr : B.hdr.id ∉ w.used) :
    StoreExt w.st (w.add B).st ∧ StoreOK (w.add B).st ∧
      ∀ b, (∃ blk, (w.add B).st b = some blk) ↔ b ∈ (w.add B).used := by
  have hnone : w.st B.hdr.id = none := by
    by_contra h
    obtain ⟨blk, hb⟩ := Option.ne_none_iff_exists'.1 h
    exact hfr ((hw.used _).1 ⟨blk, hb⟩)
  have hext : StoreExt w.st (w.add B).st := by
    intro b blk hb
    simp only [World.add]
    rw [if_neg (by rintro rfl; rw [hnone] at hb; simp at hb)]; exact hb
  refine ⟨hext, ⟨?_, ?_⟩, ?_⟩
  · intro b blk hb
    simp only [World.add] at hb
    split at hb
    · cases hb; rename_i h; exact h.symm
    · exact hw.store.idOK b blk hb
  · obtain ⟨g, hg, h1, h2⟩ := hw.store.gen
    exact ⟨g, hext _ _ hg, h1, h2⟩
  · intro b
    simp only [World.add, List.mem_cons]
    constructor
    · rintro ⟨blk, hb⟩
      split at hb
      · left; assumption
      · right; exact (hw.used b).1 ⟨blk, hb⟩
    · rintro (rfl | h)
      · exact ⟨B, by simp⟩
      · obtain ⟨blk, hb⟩ := (hw.used b).2 h
        refine ⟨blk, ?_⟩
        rw [if_neg (by rintro rfl; exact hfr h)]; exact hb

theorem init_ok (E : Env) : WorldOK E World.init := by
  have hst : World.init.st genesisId = some genesisBlock := by simp [World.init]
  have hS : StoreOK World.init.st := by
    refine ⟨?_, ⟨genesisBlock, hst, rfl, rfl⟩⟩
    intro b blk hb
    simp only [World.init] at hb
    split at hb
    · cases hb; rename_i h; exact h.symm
    · simp at hb
  have hgr : Rooted World.init.st genesisId := hS.rooted_gen
  refine ⟨hS, ?_, ?_⟩
  · intro b
    simp only [World.init, List.mem_singleton]
    constructor
    · rintro ⟨blk, hb⟩; split at hb <;> simp_all
    · rintro rfl; exact ⟨genesisBlock, by simp⟩
  · intro i
    simp only [World.init]
    refine ⟨?_, ?_, ?_, by simp, by simp, ?_, rfl⟩
    · intro y hy; simp at hy; subst hy; exact hgr
    · intro y hy; simp at hy; exact Or.inl hy
    · intro y hy; simp at hy; subst hy
      simp [parentOf, genesisBlock]
    · -- `B_imm` of the genesis chain is genesis
      have hmem := blockAtDepth_mem hS hgr E.c.k
      have : chainIds World.init.st genesisId = [genesisId] := by
        unfold chainIds; rw [chain_genesis hst rfl]; simp [genesisBlock]
      rw [this] at hmem; simp at hmem; exact hmem.symm

theorem propose_id {c : Config} {st : Store} {L : Ledger} {O : Oracle} {G : Genesis}
    {i sl newId : ℕ} {s : NodeState} {B : Block} (h : propose c st L O G i sl newId s = some B) :
    B.hdr.id = newId ∧ B.hdr.signer = .honest i ∧ B.hdr.parent = s.cloc ∧ B.hdr.slot = sl := by
  unfold propose at h
  split at h
  · simp at h
  · split at h
    · simp at h
    · simp at h; subst h; simp

/-- What an event preserves: the world invariant, a growing store, and every
node's local-chain height. -/
def StepOK (E : Env) (w w' : World) : Prop :=
  WorldOK E w' ∧ StoreExt w.st w'.st ∧
    ∀ j, height w.st (w.node j).cloc ≤ height w'.st (w'.node j).cloc

theorem StepOK.trans {E : Env} {w₁ w₂ w₃ : World} (h1 : StepOK E w₁ w₂) (h2 : StepOK E w₂ w₃) :
    StepOK E w₁ w₃ :=
  ⟨h2.1, h1.2.1.trans h2.2.1, fun j => le_trans (h1.2.2 j) (h2.2.2 j)⟩

theorem stepOK_refl {E : Env} {w : World} (hw : WorldOK E w) : StepOK E w w :=
  ⟨hw, StoreExt.refl _, fun _ => le_rfl⟩

theorem lead_ok (E : Env) (hord : E.OrderOK) {w : World} (hw : WorldOK E w) (i : ℕ) :
    StepOK E w (w.lead E i) := by
  unfold World.lead
  split
  · exact stepOK_refl hw
  split
  · exact stepOK_refl hw
  rename_i B hB
  obtain ⟨hid, -, -, -⟩ := propose_id hB
  obtain ⟨hext, hS', hused'⟩ := add_ok hw B (by rw [hid]; exact fresh_not_used w)
  have hB' : (w.add B).st B.hdr.id = some B := by simp [World.add]
  have hn : ∀ j, NodeOK E.c.k (w.add B).st E.L E.O E.G E.c (w.node j) :=
    fun j => nodeOK_ext hext hw.store (hw.nodes j)
  obtain ⟨hon, honh⟩ := onBlock_ok hS' (hn i) E.fastPath (E.ord i) (hord i) (w.add B).now B hB'
  refine ⟨⟨hS', hused', ?_⟩, hext, ?_⟩
  · intro j
    simp only
    split
    · rename_i h; subst h; exact hon
    · exact hn j
  · intro j
    simp only
    have hr := (hw.nodes j).rooted _ (hw.nodes j).cloc
    split
    · rename_i h; subst h
      exact le_trans (le_of_eq (height_ext hext hr).symm) honh
    · simpa [World.add] using le_of_eq (height_ext hext hr).symm

theorem step_ok (E : Env) (hord : E.OrderOK) {w : World} (hw : WorldOK E w) (e : Event) :
    StepOK E w (w.step E e) := by
  cases e with
  | tick =>
    simp only [World.step]
    have h0 : StepOK E w { w with now := w.now + 1 } :=
      ⟨⟨hw.store, hw.used, hw.nodes⟩, StoreExt.refl _, fun _ => le_rfl⟩
    have key : ∀ (l : List ℕ) (w₀ : World), StepOK E w w₀ → StepOK E w (l.foldl (World.lead E) w₀) := by
      intro l
      induction l with
      | nil => intro w₀ h; exact h
      | cons i is ih =>
        intro w₀ h
        simp only [List.foldl_cons]
        exact ih _ (h.trans (lead_ok E hord h.1 i))
    exact key _ _ h0
  | deliver i b =>
    simp only [World.step]
    split
    · refine ⟨⟨hw.store, hw.used, ?_⟩, StoreExt.refl _, ?_⟩
      · intro j
        simp only
        split
        · rename_i h; subst h
          exact (receive_ok hw.store (hw.nodes j) E.fastPath (E.ord j) (hord j) w.now b).1
        · exact hw.nodes j
      · intro j
        simp only
        split
        · rename_i h; subst h
          exact (receive_ok hw.store (hw.nodes j) E.fastPath (E.ord j) (hord j) w.now b).2
        · exact le_rfl
    · exact stepOK_refl hw
  | create B =>
    simp only [World.step]
    split
    · rename_i h
      simp only [Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at h
      have hnu : B.hdr.id ∉ w.used := by
        intro hm; have := List.contains_iff_mem.2 hm; simp_all
      obtain ⟨hext, hS', hused'⟩ := add_ok hw B hnu
      refine ⟨⟨hS', hused', fun j => nodeOK_ext hext hw.store (hw.nodes j)⟩, hext, ?_⟩
      intro j
      simpa [World.add] using le_of_eq (height_ext hext ((hw.nodes j).rooted _ (hw.nodes j).cloc)).symm
    · exact stepOK_refl hw

/-- **Every execution keeps the world well formed**, the store growing and every
node's local chain never losing height. -/
theorem run_ok (E : Env) (hord : E.OrderOK) :
    ∀ (es : List Event) (w : World), WorldOK E w → StepOK E w (run E w es) := by
  intro es
  induction es with
  | nil => intro w hw; exact stepOK_refl hw
  | cons e es ih =>
    intro w hw
    have h1 := step_ok E hord hw e
    exact h1.trans (ih _ h1.1)

end Cryptarchia
