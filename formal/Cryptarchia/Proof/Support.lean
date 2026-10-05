import Cryptarchia.Proof.Honesty

/-!
# Auxiliary facts for the main induction
-/

namespace Cryptarchia

open Settle

variable {E : Env}

/-! ## The honest log -/

/-- Every honest block is logged with its slot. -/
def LogOK (w : World) : Prop :=
  ∀ b B, w.st b = some B → IsHon B → (b, B.hdr.slot) ∈ w.honestLog

theorem init_log : LogOK World.init := by
  intro b B hb hh
  simp only [World.init] at hb
  split at hb
  · cases hb; obtain ⟨j, hj⟩ := hh; simp [genesisBlock] at hj
  · simp at hb

theorem lead_log {w : World} (hw : WorldOK E w) (hl : LogOK w) (i : ℕ) : LogOK (w.lead E i) := by
  unfold World.lead
  split
  · exact hl
  split
  · exact hl
  rename_i B hB
  obtain ⟨hid, -, -, hsl⟩ := propose_id hB
  intro b C hb hC
  simp only at hb ⊢
  by_cases hbB : b = B.hdr.id
  · subst hbB
    have : C = B := by simp [World.add] at hb; exact hb.symm
    subst this
    rw [hsl]; exact List.mem_cons_self
  · have hb' : w.st b = some C := by
      have : (w.add B).st b = w.st b := by simp [World.add, hbB]
      rw [← this]; exact hb
    exact List.mem_cons_of_mem _ (hl b C hb' hC)

theorem step_log (hord : E.OrderOK) {w : World} (hw : WorldOK E w) (hl : LogOK w) (e : Event) :
    LogOK (w.step E e) := by
  cases e with
  | tick =>
    simp only [World.step]
    have key : ∀ (l : List ℕ) (w₀ : World), WorldOK E w₀ → LogOK w₀ →
        LogOK (l.foldl (World.lead E) w₀) := by
      intro l
      induction l with
      | nil => intro w₀ _ h; exact h
      | cons i is ih =>
        intro w₀ hw₀ hl₀
        exact ih _ (lead_ok E hord hw₀ i).1 (lead_log hw₀ hl₀ i)
    exact key _ _ ⟨hw.store, hw.used, hw.nodes⟩ hl
  | deliver i b => simp only [World.step]; split <;> exact hl
  | create B =>
    simp only [World.step]
    split
    · rename_i hc
      simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
      intro b C hb hC
      by_cases hbB : b = B.hdr.id
      · subst hbB
        have : C = B := by simp [World.add] at hb; exact hb.symm
        obtain ⟨j, hj⟩ := hC; rw [this, hc.1] at hj; cases hj
      · have hb' : w.st b = some C := by
          have : (w.add B).st b = w.st b := by simp [World.add, hbB]
          rw [← this]; exact hb
        exact hl b C hb' hC
    · exact hl

theorem log_all (hord : E.OrderOK) {es : List Event} : ∀ n ≤ es.length, LogOK (wAt E es n) := by
  intro n
  induction n with
  | zero => intro _; rw [wAt_zero]; exact init_log
  | succ n ih =>
    intro hn
    rw [wAt_succ E es (by omega)]
    exact step_log hord (wAt_ok hord n) (ih (by omega)) _

/-! ## What `receive` can add -/

theorem receive_sub {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store} {s : NodeState}
    (hrule : s.rule = .online) (hS : StoreOK st) (hs : NodeOK c.k st L O G c s) (fastPath : Bool)
    (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now b : ℕ) :
    ∀ x ∈ (receive c st L O G fastPath ord now s b).tree, x ∈ s.tree ∨ x ∈ chainIds st b := by
  unfold receive
  have key : ∀ (l : List Block), (∀ x ∈ l, st x.hdr.id = some x ∧ x.hdr.id ∈ chainIds st b) → ∀ s,
      NodeOK c.k st L O G c s → ∀ x ∈ (l.foldl (onBlock c st L O G fastPath ord now) s).tree,
        x ∈ s.tree ∨ x ∈ chainIds st b := by
    intro l
    induction l with
    | nil => intro _ s _ x hx; exact Or.inl hx
    | cons B bs ih =>
      intro hst s hs x hx
      simp only [List.foldl_cons] at hx
      have hB := hst B List.mem_cons_self
      rcases ih (fun y hy => hst y (List.mem_cons_of_mem _ hy)) _
        (onBlock_ok hS hs fastPath ord hord now B hB.1).1 x hx with h | h
      · rcases onBlock_tree_sub hs.rule fastPath ord now B x h with h' | h'
        · exact Or.inl h'
        · right; rw [h']; exact hB.2
      · exact Or.inr h
  apply key _ _ s hs
  intro x hx
  refine ⟨mem_chainUp_store hS hx, ?_⟩
  unfold chainUp at hx
  rw [List.mem_reverse] at hx
  unfold chainIds
  exact List.mem_map_of_mem hx

/-! ## The restricted tree -/

theorem restrict_anc {F : PTree} {t u v : ℕ} : (F.restrict t).Anc u v ↔ F.Anc u v := Iff.rfl

theorem restrict_hd {F : PTree} {t m : ℕ} (hm : m ≤ t) : (F.restrict t).hd m = F.hd m := by
  classical
  unfold PTree.hd
  congr 1
  ext v
  simp only [Finset.mem_filter, mem_restrict]
  constructor
  · rintro ⟨⟨h1, -⟩, h2⟩; exact ⟨h1, h2⟩
  · rintro ⟨h1, h2, h3⟩; exact ⟨⟨h1, show F.lab v ≤ t by
      exact le_trans h3 hm⟩, h2, h3⟩

end Cryptarchia

namespace Cryptarchia

variable {E : Env}

/-- **What a tick adds**: honest blocks, each built on some node's local chain
as it stood before the tick. -/
theorem lead_now (w : World) (i : ℕ) : (w.lead E i).now = w.now := by
  unfold World.lead; split
  · rfl
  · split <;> rfl

theorem tick_new (hord : E.OrderOK) (hnd : E.nodes.Nodup) {w : World} (hw : WorldOK E w) :
    ∀ b B, (w.step E .tick).st b = some B → w.st b = none →
      IsHon B ∧ ∃ j ∈ E.nodes, B.hdr.parent = (w.node j).cloc ∧ E.online j (w.now + 1) = true := by
  simp only [World.step]
  set w₁ : World := { w with now := w.now + 1 } with hw₁
  have key : ∀ (l : List ℕ) (w₀ : World), l.Nodup → WorldOK E w₀ → w₀.now = w.now + 1 →
      (∀ i ∈ l, w₀.node i = w.node i) →
      (∀ b B, w₀.st b = some B → w.st b = none →
        IsHon B ∧ ∃ j ∈ E.nodes, B.hdr.parent = (w.node j).cloc ∧ E.online j (w.now + 1) = true) →
      (∀ i ∈ l, i ∈ E.nodes) →
      ∀ b B, (l.foldl (World.lead E) w₀).st b = some B → w.st b = none →
        IsHon B ∧ ∃ j ∈ E.nodes, B.hdr.parent = (w.node j).cloc ∧ E.online j (w.now + 1) = true := by
    intro l
    induction l with
    | nil => intro w₀ _ _ _ _ hnew _; exact hnew
    | cons i is ih =>
      intro w₀ hnd' hw₀ hnow hsame hnew hin
      simp only [List.foldl_cons]
      apply ih _ (List.nodup_cons.1 hnd').2 (lead_ok E hord hw₀ i).1 (by rw [lead_now, hnow])
      · intro j hj
        have hji : j ≠ i := fun h => (List.nodup_cons.1 hnd').1 (h ▸ hj)
        unfold World.lead; split
        · exact hsame j (List.mem_cons_of_mem _ hj)
        split
        · exact hsame j (List.mem_cons_of_mem _ hj)
        · simp only; rw [if_neg hji]; exact hsame j (List.mem_cons_of_mem _ hj)
      · intro b B hb hn
        unfold World.lead at hb; split at hb
        · exact hnew b B hb hn
        rename_i honl
        split at hb
        · exact hnew b B hb hn
        rename_i C hC
        obtain ⟨hid, hsig, hpar, -⟩ := propose_id hC
        simp only at hb
        by_cases hbC : b = C.hdr.id
        · subst hbC
          have : B = C := by simp [World.add] at hb; exact hb.symm
          subst this
          refine ⟨⟨i, hsig⟩, i, hin i List.mem_cons_self, by rw [hpar, hsame i List.mem_cons_self], ?_⟩
          rw [← hnow]; simpa using honl
        · have : (w₀.add C).st b = w₀.st b := by simp [World.add, hbC]
          rw [this] at hb; exact hnew b B hb hn
      · intro j hj; exact hin j (List.mem_cons_of_mem _ hj)
  exact key E.nodes w₁ hnd ⟨hw.store, hw.used, hw.nodes⟩ rfl (fun _ _ => rfl)
    (fun b B hb hn => by simp [w₁] at hb; rw [hb] at hn; simp at hn) (fun _ h => h)

end Cryptarchia

namespace Cryptarchia

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}

/-- **A proposer adopts its own block** (or something higher): the block is one
above the local chain, so the fork-choice loop either switches to it or has
already moved higher. -/
theorem own_adopt (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ) (B : Block)
    (hB : st B.hdr.id = some B) (hpar : B.hdr.parent = s.cloc) (hnew : B.hdr.id ∉ s.tree)
    (hval : validHeader c st L O G s.tree s.bimm now B = true) :
    height st B.hdr.id ≤ height st (onBlock c st L O G fastPath ord now s B).cloc := by
  have hacc : ¬(s.tree.contains B.hdr.id || !validHeader c st L O G s.tree s.bimm now B) = true := by
    simp [hval, hnew]
  obtain ⟨hcore, -, hparT, -⟩ := (validHeader_iff c st L O G _ _ _ _).1 hval
  have hcore' := hcore
  unfold validCore at hcore'
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hcore'
  obtain ⟨⟨⟨⟨⟨⟨hne, -⟩, hslot⟩, -⟩, -⟩, -⟩, -⟩ := hcore'
  have hcr := hs.rooted _ hs.cloc
  have hBr : Rooted st B.hdr.id := Rooted.step B.hdr.id B hB hne (hs.rooted _ hparT) hslot
  have hBh : height st B.hdr.id = height st s.cloc + 1 := by
    rw [height_step hB hne (hs.rooted _ hparT) hslot, hpar]
  unfold onBlock
  rw [if_neg hacc, hs.rule]
  simp only
  set T' := s.tree ++ [B.hdr.id]
  have hT'r : ∀ y ∈ T', Rooted st y := by
    intro y hy; rw [List.mem_append] at hy
    rcases hy with hy | hy
    · exact hs.rooted y hy
    · simp at hy; subst hy; exact hBr
  split
  · exact le_rfl
  · unfold forkChoice; simp only
    have htips : ∀ f ∈ ord (tips st T'), f ∈ T' := fun f hf =>
      List.mem_of_mem_filter ((hord (tips st T')).mem_iff.1 hf)
    have hr : ∀ f ∈ ord (tips st T'), Rooted st f := fun f hf => hT'r f (htips f hf)
    -- `B` is a tip: nothing in the tree has it as parent
    have hBtip : B.hdr.id ∈ tips st T' := by
      unfold tips
      rw [List.mem_filter]
      refine ⟨List.mem_append_right _ (List.mem_singleton_self _), ?_⟩
      simp only [Bool.not_eq_true', List.any_eq_false, decide_eq_true_eq, not_and]
      intro x hx hxne hxp
      rw [List.mem_append] at hx
      rcases hx with hx | hx
      · exact hnew (hxp ▸ hs.closed x hx)
      · simp at hx; exact hxne hx
    have hBf : B.hdr.id ∈ ord (tips st T') := (hord _).mem_iff.2 hBtip
    let P : ℕ → Prop := fun cl => Rooted st cl ∧ (cl = s.cloc ∨ height st s.cloc < height st cl)
    have := fc_reaches hS P c.k (ord (tips st T')) hr hBf
      (by
        intro cl hP hclr hlt
        rcases hP.2 with rfl | hP'
        · -- the running choice is still the local chain, the parent of `B`
          have hin : s.cloc ∈ chainIds st B.hdr.id := by
            unfold chainIds
            rw [chain_step hB hne (hs.rooted _ hparT) hslot, hpar]
            simp only [List.map_cons, List.mem_cons]
            right; simpa [chainIds] using self_mem_chainIds hS hcr
          obtain ⟨hla, hlb, hmax⟩ := lca_spec hS hcr hBr
          have := hmax s.cloc (self_mem_chainIds hS hcr) hin
          have := (anc_height hS (anc_height hS hcr hla).1 this).2.1
          have := (anc_height hS hcr hla).2.1
          omega
        · omega)
      s.cloc ⟨hcr, Or.inl rfl⟩ hcr
      (by
        intro c' f hP hf hswitch
        obtain ⟨-, -, hlt⟩ := onlineStep_switch hS hP.1 (hr f hf) hswitch
        refine ⟨hr f hf, Or.inr ?_⟩
        rcases hP.2 with rfl | hP' <;> omega)
    exact this

end Cryptarchia

namespace Cryptarchia

variable {E : Env}

/-- The two outcomes of a lead step. -/
theorem lead_cases (w : World) (i : ℕ) :
    w.lead E i = w ∨ ∃ C, propose E.c w.st E.L E.O E.G i w.now w.fresh (w.node i) = some C ∧
      w.lead E i = { w.add C with
        node := fun j => if j = i then
          onBlock E.c (w.add C).st E.L E.O E.G E.fastPath (E.ord i) (w.add C).now (w.node i) C
          else (w.add C).node j
        honestLog := (C.hdr.id, w.now) :: w.honestLog } := by
  unfold World.lead
  split
  · exact Or.inl rfl
  split
  · exact Or.inl rfl
  · rename_i C hC; exact Or.inr ⟨C, hC, rfl⟩

/-- **After a tick, anything new in a node's tree is no higher than its new local
chain** (the only new block is its own proposal, which it adopts). -/
theorem tick_tree (hord : E.OrderOK) (hexec : HonestExec E.L) (hnd : E.nodes.Nodup) {w : World}
    (hw : WorldOK E w) (hh : HonOK E w) (hc : E.c.Sane) :
    ∀ i, ∀ x ∈ ((w.step E .tick).node i).tree, x ∉ (w.node i).tree →
      height (w.step E .tick).st x ≤ height (w.step E .tick).st ((w.step E .tick).node i).cloc := by
  simp only [World.step]
  set w₁ : World := { w with now := w.now + 1 } with hw₁
  have key : ∀ (l : List ℕ) (w₀ : World), l.Nodup → WorldOK E w₀ → w₀.now = w.now + 1 →
      StoreExt w.st w₀.st → (∀ i ∈ l, w₀.node i = w.node i) →
      (∀ i, ∀ x ∈ (w₀.node i).tree, x ∉ (w.node i).tree → height w₀.st x ≤ height w₀.st (w₀.node i).cloc) →
      ∀ i, ∀ x ∈ ((l.foldl (World.lead E) w₀).node i).tree, x ∉ (w.node i).tree →
        height (l.foldl (World.lead E) w₀).st x ≤
          height (l.foldl (World.lead E) w₀).st ((l.foldl (World.lead E) w₀).node i).cloc := by
    intro l
    induction l with
    | nil => intro w₀ _ _ _ _ _ h; exact h
    | cons i is ih =>
      intro w₀ hnd' hw₀ hnow hext hsame hR
      simp only [List.foldl_cons]
      have hlead := lead_ok E hord hw₀ i
      apply ih _ (List.nodup_cons.1 hnd').2 hlead.1 ?_ (hext.trans hlead.2.1) ?_ ?_
      · -- the clock does not move within the tick
        unfold World.lead; split
        · exact hnow
        split
        · exact hnow
        · exact hnow
      · intro j hj
        have hji : j ≠ i := fun h => (List.nodup_cons.1 hnd').1 (h ▸ hj)
        unfold World.lead; split
        · exact hsame j (List.mem_cons_of_mem _ hj)
        split
        · exact hsame j (List.mem_cons_of_mem _ hj)
        · simp only; rw [if_neg hji]; exact hsame j (List.mem_cons_of_mem _ hj)
      · -- the property after node `i`'s lead
        intro j x hx hxn
        rcases lead_cases (E := E) w₀ i with hL | ⟨C, hC, hL⟩
        · rw [hL] at hx ⊢; exact hR j x hx hxn
        rw [hL] at hx ⊢
        obtain ⟨hid, -, hpar, hsl⟩ := propose_id hC
        obtain ⟨hextC, hSC, -⟩ := add_ok hw₀ C (by rw [hid]; exact fresh_not_used w₀)
        have hC' : (w₀.add C).st C.hdr.id = some C := by simp [World.add]
        simp only at hx ⊢
        by_cases hji : j = i
        · subst hji
          rw [if_pos rfl] at hx ⊢
          -- node `j` (= `i`) processed its own block
          have hsi : w₀.node j = w.node j := hsame j List.mem_cons_self
          have hnodes' := nodeOK_ext hextC hw₀.store (hw₀.nodes j)
          rcases onBlock_tree_sub hnodes'.rule E.fastPath (E.ord j) (w₀.add C).now C x hx with h | h
          · rw [hsi] at h; exact absurd h hxn
          · subst h
            have hne : w₀.fresh ≠ genesisId := by
              intro h0; have := fresh_not_used w₀; rw [h0] at this; exact this (genesis_used hw₀)
            have hslots : ∀ y ∈ (w₀.node j).tree, slotOf w₀.st y < w₀.now := by
              intro y hy; rw [hsi] at hy
              rw [slotOf_ext hext ((hw.nodes j).rooted y hy).exists_blk, hnow]
              exact Nat.lt_succ_of_le (hh.slots j y hy)
            have hvalid := propose_valid hw₀.store (hw₀.nodes j) hC hslots hc
              hexec hSC hextC hC' hne
            have hcr := (hw₀.nodes j).rooted _ (hw₀.nodes j).cloc
            have hnewC : C.hdr.id ∉ (w₀.node j).tree := by
              intro hin
              have := (hw₀.used _).1 ((hw₀.nodes j).rooted _ hin).exists_blk
              rw [hid] at this; exact fresh_not_used w₀ this
            have hvh : validHeader E.c (w₀.add C).st E.L E.O E.G (w₀.node j).tree (w₀.node j).bimm
                (w₀.add C).now C = true := by
              rw [validHeader_iff]
              refine ⟨hvalid, by simp [World.add, hsl], by rw [hpar]; exact (hw₀.nodes j).cloc, ?_⟩
              rw [hpar, (hw₀.nodes j).bimm,
                height_ext hextC (anc_height hw₀.store hcr (blockAtDepth_mem hw₀.store hcr _)).1,
                blockAtDepth_height hw₀.store hcr, height_ext hextC hcr]
              omega
            exact own_adopt hSC hnodes' E.fastPath (E.ord j) (hord j) _ C hC' hpar hnewC hvh
        · rw [if_neg hji] at hx ⊢
          have := hR j x hx hxn
          have hxr := (hw₀.nodes j).rooted x hx
          have hcr := (hw₀.nodes j).rooted _ (hw₀.nodes j).cloc
          rw [show (w₀.add C).node j = w₀.node j from rfl, height_ext hextC hxr,
            height_ext hextC hcr]; exact this
  exact key E.nodes w₁ hnd ⟨hw.store, hw.used, hw.nodes⟩ rfl (StoreExt.refl _) (fun _ _ => rfl)
    (fun i x hx hxn => absurd hx hxn)

end Cryptarchia
