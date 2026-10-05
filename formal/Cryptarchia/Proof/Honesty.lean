import Cryptarchia.Proof.Trace

/-!
# Honest blocks along an execution

In every epoch (for sane parameters), and when honest payloads execute: node trees never hold
blocks from the future; every honest block is good (rooted, valid chain, not
from the future); and honest blocks created after a point have later slots.
-/

namespace Cryptarchia

variable {E : Env}

/-- Honest-signed blocks. -/
def IsHon (B : Block) : Prop := ∃ j, B.hdr.signer = .honest j

/-- The honest-block invariant of a world. -/
structure HonOK (E : Env) (w : World) : Prop where
  slots : ∀ i, ∀ x ∈ (w.node i).tree, slotOf w.st x ≤ w.now
  hon : ∀ b B, w.st b = some B → IsHon B → GoodAt E.c E.L E.O E.G w.st w.now b

theorem GoodAt.mono {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st st' : Store}
    (hS : StoreOK st) (hx : StoreExt st st') {t t' b : ℕ} (htt : t ≤ t')
    (h : GoodAt c L O G st t b) : GoodAt c L O G st' t' b := by
  obtain ⟨hr, hsl, hv⟩ := h
  refine ⟨hr.mono hx, by rw [slotOf_ext hx hr.exists_blk]; omega, ?_⟩
  intro x hx'
  rw [chainIds_ext hx hr] at hx'
  rcases hv x hx' with h0 | ⟨B, hB, hvB⟩
  · exact Or.inl h0
  · refine Or.inr ⟨B, hx _ _ hB, ?_⟩
    have hxr := (anc_height hS hr hx').1
    have hx0 : x ≠ genesisId := by
      intro h0; subst h0
      unfold validCore at hvB; simp only [Bool.and_eq_true, decide_eq_true_eq] at hvB
      exact hvB.1.1.1.1.1.1 (hS.idOK _ _ hB)
    obtain ⟨blk, hbk, hpr, -⟩ := hxr.inv hx0
    rw [hbk] at hB; cases hB
    exact validCore_ext hx hS hpr hvB

theorem init_hon : HonOK E World.init := by
  refine ⟨?_, ?_⟩
  · intro i x hx; simp [World.init] at hx; subst hx; simp [World.init, slotOf, genesisBlock]
  · intro b B hb hh
    simp only [World.init] at hb
    split at hb
    · cases hb; obtain ⟨j, hj⟩ := hh; simp [genesisBlock] at hj
    · simp at hb

/-- The facts a lead step needs. -/
theorem lead_hon (hord : E.OrderOK) (hexec : HonestExec E.L) {w : World} (hw : WorldOK E w)
    (hh : HonOK E w) (hc : E.c.Sane)
    (i : ℕ) (hpast : ∀ x ∈ (w.node i).tree, slotOf w.st x < w.now) :
    HonOK E (w.lead E i) ∧ (∀ j, j ≠ i → (w.lead E i).node j = w.node j) ∧
      StoreExt w.st (w.lead E i).st ∧ (w.lead E i).now = w.now ∧
      (∀ b B, (w.lead E i).st b = some B → w.st b = none → B.hdr.slot = w.now) := by
  unfold World.lead
  split
  · exact ⟨hh, fun _ _ => rfl, StoreExt.refl _, rfl, fun b B h1 h2 => by rw [h1] at h2; simp at h2⟩
  split
  · exact ⟨hh, fun _ _ => rfl, StoreExt.refl _, rfl, fun b B h1 h2 => by rw [h1] at h2; simp at h2⟩
  rename_i B hB
  obtain ⟨hid, hsig, hpar, hsl⟩ := propose_id hB
  obtain ⟨hext, hS', hused'⟩ := add_ok hw B (by rw [hid]; exact fresh_not_used w)
  have hB' : (w.add B).st B.hdr.id = some B := by simp [World.add]
  have hne : w.fresh ≠ genesisId := by
    intro h; have := fresh_not_used w; rw [h] at this; exact this (genesis_used hw)
  have hvalid := propose_valid hw.store (hw.nodes i) hB hpast hc hexec hS' hext hB' hne
  have hcr := (hw.nodes i).rooted _ (hw.nodes i).cloc
  have hslp : slotOf w.st (w.node i).cloc < B.hdr.slot := by rw [hsl]; exact hpast _ (hw.nodes i).cloc
  have hBr : Rooted (w.add B).st B.hdr.id := by
    refine Rooted.step _ B hB' (by rw [hid]; exact hne) (by rw [hpar]; exact hcr.mono hext) ?_
    rw [hpar, slotOf_ext hext hcr.exists_blk]; exact hslp
  have hnodes' : ∀ j, NodeOK E.c.k (w.add B).st E.L E.O E.G E.c (w.node j) :=
    fun j => nodeOK_ext hext hw.store (hw.nodes j)
  refine ⟨⟨?_, ?_⟩, ?_, hext, rfl, ?_⟩
  · intro i' x hx
    simp only at hx ⊢
    split at hx
    · rename_i hi; subst hi
      exact onBlock_slots (hnodes' i').rule E.fastPath (E.ord i') (w.add B).now B hB'
        (fun y hy => by
          rw [slotOf_ext hext ((hw.nodes i').rooted y hy).exists_blk]
          exact (hpast y hy).le) x hx
    · rw [slotOf_ext hext ((hw.nodes i').rooted x hx).exists_blk]; exact hh.slots i' x hx
  · intro b C hb hC
    simp only at hb ⊢
    by_cases hbB : b = B.hdr.id
    · subst hbB
      refine ⟨hBr, by rw [slotOf_eq hB', hsl]; exact le_rfl, ?_⟩
      intro x hx
      have hpr : Rooted (w.add B).st B.hdr.parent := by rw [hpar]; exact hcr.mono hext
      have hchain : chainIds (w.add B).st B.hdr.id = B.hdr.id :: chainIds (w.add B).st B.hdr.parent := by
        unfold chainIds
        rw [chain_step hB' (by rw [hid]; exact hne) hpr (by
          rw [hpar, slotOf_ext hext hcr.exists_blk]; exact hslp)]
        simp
      rw [hchain, List.mem_cons] at hx
      rcases hx with rfl | hx
      · exact Or.inr ⟨B, hB', hvalid⟩
      · rw [hpar] at hx
        have := (tree_good hw.store (hw.nodes i) (fun y hy => (hpast y hy).le) (hw.nodes i).cloc).mono
          hw.store hext le_rfl
        exact this.2.2 x hx
    · have hb' : w.st b = some C := by
        have : (w.add B).st b = w.st b := by simp [World.add, hbB]
        rw [← this]; exact hb
      exact (hh.hon b C hb' hC).mono hw.store hext le_rfl
  · intro j hj; simp only; rw [if_neg hj]; rfl
  · intro b C hb hn
    simp only at hb
    by_cases hbB : b = B.hdr.id
    · subst hbB; rw [hB'] at hb; cases hb; exact hsl
    · have : (w.add B).st b = w.st b := by simp [World.add, hbB]
      rw [this, hn] at hb; simp at hb

/-- **A tick.** The clock moves on and every (distinct) node proposes at most
once, on a tree holding only earlier slots. -/
theorem tick_hon (hord : E.OrderOK) (hexec : HonestExec E.L) (hnd : E.nodes.Nodup) {w : World}
    (hw : WorldOK E w) (hh : HonOK E w) (hc : E.c.Sane) :
    HonOK E (w.step E .tick) ∧
      (∀ b B, (w.step E .tick).st b = some B → w.st b = none → B.hdr.slot = w.now + 1) := by
  simp only [World.step]
  set w₁ : World := { w with now := w.now + 1 } with hw₁
  have hw₁ok : WorldOK E w₁ := ⟨hw.store, hw.used, hw.nodes⟩
  have hh₁ : HonOK E w₁ := ⟨fun i x hx => le_trans (hh.slots i x hx) (by simp [w₁]),
    fun b B hb hB => (hh.hon b B hb hB).mono hw.store (StoreExt.refl _) (by simp [w₁])⟩
  -- fold over the nodes, each node proposing on a tree of earlier slots
  have key : ∀ (l : List ℕ) (w₀ : World), l.Nodup → WorldOK E w₀ → HonOK E w₀ → w₀.now = w.now + 1 →
      StoreExt w.st w₀.st → (∀ b B, w₀.st b = some B → w.st b = none → B.hdr.slot = w.now + 1) →
      (∀ i ∈ l, ∀ x ∈ (w₀.node i).tree, slotOf w₀.st x < w₀.now) →
      HonOK E (l.foldl (World.lead E) w₀) ∧
        (∀ b B, (l.foldl (World.lead E) w₀).st b = some B → w.st b = none → B.hdr.slot = w.now + 1) := by
    intro l
    induction l with
    | nil => intro w₀ _ _ hh₀ _ _ hnew _; exact ⟨hh₀, hnew⟩
    | cons i is ih =>
      intro w₀ hnd' hw₀ hh₀ hnow hext₀ hnew hpast
      simp only [List.foldl_cons]
      obtain ⟨h1, h2, h3, h4, h5⟩ := lead_hon hord hexec hw₀ hh₀ hc i (hpast i List.mem_cons_self)
      have hw' := (lead_ok E hord hw₀ i).1
      apply ih _ (List.nodup_cons.1 hnd').2 hw' h1 (by rw [h4, hnow]) (hext₀.trans h3)
      · intro b B hb hn
        by_cases h0 : w₀.st b = none
        · rw [h5 b B hb h0, hnow]
        · obtain ⟨B', hB'⟩ := Option.ne_none_iff_exists'.1 h0
          have hBB : B' = B := by
            have := h3 b B' hB'; rw [hb] at this; exact (Option.some_inj.1 this).symm
          rw [← hBB]; exact hnew b B' hB' hn
      · intro j hj x hx
        have hji : j ≠ i := fun h => (List.nodup_cons.1 hnd').1 (h ▸ hj)
        rw [h2 j hji] at hx
        rw [h4, slotOf_ext h3 ((hw₀.nodes j).rooted x hx).exists_blk]
        exact hpast j (List.mem_cons_of_mem _ hj) x hx
  exact key E.nodes w₁ hnd hw₁ok hh₁ rfl (StoreExt.refl _)
    (fun b B hb hn => by simp [w₁] at hb; rw [hb] at hn; simp at hn)
    (fun i _ x hx => lt_of_le_of_lt (hh.slots i x hx) (by simp [w₁]))

theorem receive_slots {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}
    (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s) (fastPath : Bool)
    (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now b : ℕ)
    (hsl : ∀ x ∈ s.tree, slotOf st x ≤ now) :
    ∀ x ∈ (receive c st L O G fastPath ord now s b).tree, slotOf st x ≤ now := by
  unfold receive
  have key : ∀ (l : List Block), (∀ x ∈ l, st x.hdr.id = some x) → ∀ s, NodeOK c.k st L O G c s →
      (∀ x ∈ s.tree, slotOf st x ≤ now) →
      ∀ x ∈ (l.foldl (onBlock c st L O G fastPath ord now) s).tree, slotOf st x ≤ now := by
    intro l
    induction l with
    | nil => intro _ s _ h; exact h
    | cons B bs ih =>
      intro hst s hs hsl
      simp only [List.foldl_cons]
      have hB := hst B List.mem_cons_self
      exact ih (fun x hx => hst x (List.mem_cons_of_mem _ hx)) _
        (onBlock_ok hS hs fastPath ord hord now B hB).1 (onBlock_slots hs.rule fastPath ord now B hB hsl)
  exact key _ (fun x hx => mem_chainUp_store hS hx) s hs hsl

/-- **Every event** keeps the honest-block invariant, and honest blocks are only created by ticks, with the new slot. -/
theorem step_hon (hord : E.OrderOK) (hexec : HonestExec E.L) (hnd : E.nodes.Nodup) {w : World}
    (hw : WorldOK E w) (hh : HonOK E w) (e : Event) (hc : E.c.Sane) :
    HonOK E (w.step E e) ∧
      (∀ b B, (w.step E e).st b = some B → w.st b = none → IsHon B → B.hdr.slot = w.now + 1) := by
  cases e with
  | tick =>
    obtain ⟨h1, h2⟩ := tick_hon hord hexec hnd hw hh hc
    exact ⟨h1, fun b B hb hn _ => h2 b B hb hn⟩
  | deliver i b =>
    simp only [World.step]
    split
    · refine ⟨⟨?_, hh.hon⟩, fun b' B hb hn _ => by rw [hb] at hn; simp at hn⟩
      intro j x hx
      simp only at hx ⊢
      split at hx
      · rename_i hji; subst hji
        exact receive_slots hw.store (hw.nodes j) E.fastPath (E.ord j) (hord j) w.now b
          (hh.slots j) x hx
      · exact hh.slots j x hx
    · exact ⟨hh, fun b' B hb hn _ => by rw [hb] at hn; simp at hn⟩
  | create B =>
    simp only [World.step]
    split
    · rename_i hc
      simp only [Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at hc
      have hnu : B.hdr.id ∉ w.used := by
        intro hm; have := List.contains_iff_mem.2 hm; simp_all
      obtain ⟨hext, hS', -⟩ := add_ok hw B hnu
      refine ⟨⟨?_, ?_⟩, ?_⟩
      · intro j x hx
        rw [slotOf_ext hext ((hw.nodes j).rooted x hx).exists_blk]; exact hh.slots j x hx
      · intro b C hb hC
        by_cases hbB : b = B.hdr.id
        · subst hbB
          have : C = B := by simp [World.add] at hb; exact hb.symm
          obtain ⟨j, hj⟩ := hC; rw [this, hc.1] at hj; cases hj
        · have hb' : w.st b = some C := by
            have : (w.add B).st b = w.st b := by simp [World.add, hbB]
            rw [← this]; exact hb
          exact (hh.hon b C hb' hC).mono hw.store hext le_rfl
      · intro b C hb hn hC
        by_cases hbB : b = B.hdr.id
        · subst hbB
          have : C = B := by simp [World.add] at hb; exact hb.symm
          obtain ⟨j, hj⟩ := hC; rw [this, hc.1] at hj; cases hj
        · have : (w.add B).st b = w.st b := by simp [World.add, hbB]
          rw [this, hn] at hb; simp at hb
    · exact ⟨hh, fun b' B hb hn _ => by rw [hb] at hn; simp at hn⟩

variable {es : List Event}

/-- The epoch of the whole execution. -/
theorem epoch_of_le {c : Config} {t N : ℕ} (htN : t ≤ N) (hN : N < c.epochLength) : c.epochOf t = 0 := by
  unfold Config.epochOf; exact Nat.div_eq_of_lt (by omega)

/-- **The honest-block invariant holds throughout an execution.** -/
theorem hon_all (hord : E.OrderOK) (hexec : HonestExec E.L) (hnd : E.nodes.Nodup)
    (hc : E.c.Sane) :
    ∀ n ≤ es.length, HonOK E (wAt E es n) := by
  intro n
  induction n with
  | zero => intro _; rw [wAt_zero]; exact init_hon
  | succ n ih =>
    intro hn
    rw [wAt_succ E es (by omega)]
    exact (step_hon hord hexec hnd (wAt_ok hord n) (ih (by omega)) es[n] hc).1

/-- **Honest blocks created after index `n` have a slot later than the time at
`n`.** -/
theorem created_later (hord : E.OrderOK) (hexec : HonestExec E.L) (hnd : E.nodes.Nodup)
    (hc : E.c.Sane) {n : ℕ} :
    ∀ m, n ≤ m → m ≤ es.length → ∀ b B, (wAt E es m).st b = some B → IsHon B →
      (wAt E es n).st b = none → (wAt E es n).now < B.hdr.slot := by
  intro m
  induction m with
  | zero => intro hnm _ b B hb _ hn; have : n = 0 := by omega
            subst this; rw [hb] at hn; simp at hn
  | succ m ih =>
    intro hnm hm b B hb hB hn
    rcases Nat.eq_or_lt_of_le hnm with heq | hlt
    · rw [heq, hb] at hn; simp at hn
    by_cases hbm : (wAt E es m).st b = none
    · have hml : m < es.length := by omega
      have hstep := step_hon hord hexec hnd (wAt_ok hord m) (hon_all hord hexec hnd hc m hml.le)
        (es[m]'hml) hc
      rw [wAt_succ E es (by omega)] at hb
      have := hstep.2 b B hb hbm hB
      have := now_mono (E := E) (es := es) (n := n) (m := m) (by omega) (by omega)
      omega
    · obtain ⟨B', hB'⟩ := Option.ne_none_iff_exists'.1 hbm
      have hext := store_mono (E := E) (es := es) hord (Nat.le_succ m) b B' hB'
      rw [hb] at hext
      have hBB : B' = B := (Option.some_inj.1 hext).symm
      rw [← hBB] at hB ⊢
      exact ih (by omega) (by omega) b B' hB' hB hn

end Cryptarchia
