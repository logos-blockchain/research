import Cryptarchia.Proof.Main

/-!
# Cryptarchia settlement theorems

* `bimm_persist` (every execution): a node's latest immutable block `B_imm`
  never reverts: each later `B_imm` of the node descends from it. This is what
  the online rule's `k`-deep rejection and pruning are designed to give.
* `agree_now` (on the good event): at every point, any two honest nodes' local
  chains meet within `k` blocks below each, and each node's `B_imm` is on every
  honest node's local chain.
* `bimm_final` (on the good event): **a block that any honest node has committed
  as immutable is on every honest node's local chain at every later point.**
  This is Cryptarchia's `k`-deep finality.
-/

namespace Cryptarchia

open Settle

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}

variable {E : Env} {es : List Event} {K : ℕ → Prop}

/-- A node's immutable block is rooted, on its local chain. -/
theorem bimm_rooted (hord : E.OrderOK) (n i : ℕ) :
    Rooted (wAt E es n).st ((wAt E es n).node i).bimm ∧
      ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st ((wAt E es n).node i).cloc := by
  have hw := wAt_ok (es := es) hord n
  have hcr := (hw.nodes i).rooted _ (hw.nodes i).cloc
  have hm : ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st ((wAt E es n).node i).cloc := by
    rw [(hw.nodes i).bimm]; exact blockAtDepth_mem hw.store hcr _
  exact ⟨(anc_height hw.store hcr hm).1, hm⟩

/-- **`B_imm` never reverts**, along the whole execution, for every node. -/
theorem bimm_persist (hord : E.OrderOK) (hnd : E.nodes.Nodup) (i : ℕ) {n : ℕ} :
    ∀ n', n ≤ n' → n' ≤ es.length →
      ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n').st ((wAt E es n').node i).bimm := by
  intro n'
  induction n' with
  | zero =>
    intro hn _; have : n = 0 := by omega
    subst this; exact self_mem_chainIds (wAt_ok hord 0).store (bimm_rooted hord 0 i).1
  | succ m ih =>
    intro hnm hm
    rcases Nat.eq_or_lt_of_le hnm with h | h
    · subst h; exact self_mem_chainIds (wAt_ok hord _).store (bimm_rooted hord _ i).1
    have hwm := wAt_ok (es := es) hord m
    have hext : StoreExt (wAt E es m).st (wAt E es (m + 1)).st := store_mono hord (Nat.le_succ m)
    have hS1 := (wAt_ok (es := es) hord (m + 1)).store
    have h1 := ih (by omega) (by omega)
    have hbr := (bimm_rooted (es := es) hord m i).1
    rw [← chainIds_ext hext hbr] at h1
    -- one event keeps node `i`'s old `B_imm` below its new one
    have hstep : ((wAt E es m).node i).bimm ∈
        chainIds (wAt E es (m + 1)).st ((wAt E es (m + 1)).node i).bimm := by
      rw [wAt_succ E es (by omega)]
      rw [wAt_succ E es (by omega)] at hS1
      cases hev : es[m] with
      | tick =>
        -- the node's own proposal, if any, goes through `on_block`
        simp only [World.step]
        set w₁ : World := { (wAt E es m) with now := (wAt E es m).now + 1 }
        have key : ∀ (l : List ℕ) (w₀ : World), WorldOK E w₀ →
            StoreExt (wAt E es m).st w₀.st →
            ((wAt E es m).node i).bimm ∈ chainIds w₀.st (w₀.node i).bimm →
            ((wAt E es m).node i).bimm ∈ chainIds (l.foldl (World.lead E) w₀).st
              ((l.foldl (World.lead E) w₀).node i).bimm := by
          intro l
          induction l with
          | nil => intro w₀ _ _ h; exact h
          | cons j js ihl =>
            intro w₀ hw₀ hx₀ hin₀
            simp only [List.foldl_cons]
            have hl := lead_ok E hord hw₀ j
            apply ihl _ hl.1 (hx₀.trans hl.2.1)
            have hbr₀ : Rooted w₀.st (w₀.node i).bimm := by
              have hcr := (hw₀.nodes i).rooted _ (hw₀.nodes i).cloc
              have hmem : (w₀.node i).bimm ∈ chainIds w₀.st (w₀.node i).cloc := by
                rw [(hw₀.nodes i).bimm]; exact blockAtDepth_mem hw₀.store hcr _
              exact (anc_height hw₀.store hcr hmem).1
            rcases lead_cases (E := E) w₀ j with hL | ⟨C, hC, hL⟩
            · rw [hL]; exact hin₀
            · rw [hL]
              obtain ⟨hid, -, -, -⟩ := propose_id hC
              obtain ⟨hextC, hSC, -⟩ := add_ok hw₀ C (by rw [hid]; exact fresh_not_used w₀)
              have hC' : (w₀.add C).st C.hdr.id = some C := by simp [World.add]
              simp only
              have hin' : ((wAt E es m).node i).bimm ∈ chainIds (w₀.add C).st (w₀.node i).bimm := by
                rw [chainIds_ext hextC hbr₀]; exact hin₀
              by_cases hji : i = j
              · subst hji
                rw [if_pos rfl]
                have hn' := nodeOK_ext hextC hw₀.store (hw₀.nodes i)
                have := onBlock_bimm hSC hn' E.fastPath (E.ord i) (hord i) (w₀.add C).now C hC'
                have hr' : Rooted (w₀.add C).st
                    (onBlock E.c (w₀.add C).st E.L E.O E.G E.fastPath (E.ord i) (w₀.add C).now
                      (w₀.node i) C).bimm := by
                  have hok := (onBlock_ok hSC hn' E.fastPath (E.ord i) (hord i) (w₀.add C).now C hC').1
                  have hcr := hok.rooted _ hok.cloc
                  have hmem := blockAtDepth_mem hSC hcr E.c.k
                  rw [← hok.bimm] at hmem
                  exact (anc_height hSC hcr hmem).1
                exact chainIds_trans hSC hr' this hin'
              · rw [if_neg hji]; exact hin'
        exact key _ w₁ ⟨hwm.store, hwm.used, hwm.nodes⟩ (StoreExt.refl _)
          (self_mem_chainIds hwm.store hbr)
      | deliver j b =>
        simp only [World.step]
        split
        · simp only
          split
          · rename_i hji; subst hji
            have := fold_bimm hwm.store E.fastPath (E.ord i) (hord i) (wAt E es m).now
              (chainUp (wAt E es m).st b) (fun x hx => mem_chainUp_store hwm.store hx) _ (hwm.nodes i)
            exact this
          · exact self_mem_chainIds hwm.store hbr
        · exact self_mem_chainIds hwm.store hbr
      | create B =>
        simp only [World.step]
        split
        · rename_i hc
          simp only [Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at hc
          have hnu : B.hdr.id ∉ (wAt E es m).used := by
            intro hmu; have := List.contains_iff_mem.2 hmu; simp_all
          obtain ⟨hextB, -, -⟩ := add_ok hwm B hnu
          show _ ∈ chainIds ((wAt E es m).add B).st ((wAt E es m).node i).bimm
          rw [chainIds_ext hextB hbr]; exact self_mem_chainIds hwm.store hbr
        · exact self_mem_chainIds hwm.store hbr
    have hr1 := (bimm_rooted (es := es) hord (m + 1) i).1
    exact chainIds_trans hS1 hr1 hstep h1

/-- Before the first slot, every honest node is still on genesis. -/
theorem cloc_genesis_at_zero (hA : Assm E) {n : ℕ} (hn : n ≤ es.length) (h0 : (wAt E es n).now = 0)
    (i : ℕ) : ((wAt E es n).node i).cloc = genesisId := by
  have hw := wAt_ok (es := es) hA.ord n
  have hh := hon_all (es := es) hA.ord hA.exec hA.nodup hA.sane n hn
  by_contra hne
  have hin := (hw.nodes i).cloc
  have hsl := hh.slots i _ hin
  obtain ⟨blk, hbk, -, hs⟩ := ((hw.nodes i).rooted _ hin).inv hne
  rw [slotOf_eq hbk, h0] at hsl; omega

/-- **Agreement at a point**, from the invariant there: node `i`'s `B_imm` is on
node `j`'s local chain. -/
theorem agree_of (hA : Assm E) (hK : KBase E es K) {W : ℕ → ℕ} {e : ℕ → ℕ} {H : ℕ} (hG : GoodCondW E es K W e H)
    {n : ℕ} (hn : n ≤ es.length) (hnH : (wAt E es n).now ≤ H)
    (hD : DomAt (E := E) (es := es) (K := K) n ((wAt E es n).now - E.Δ - 1))
    (hH : HonAt (E := E) (es := es) (K := K) n) {i j : ℕ} (hi : i ∈ E.nodes) (hj : j ∈ E.nodes)
    (hio : E.online i (wAt E es n).now = true) (hjo : E.online j (wAt E es n).now = true)
    (hKi : K ((wAt E es n).node i).cloc) (hKj : K ((wAt E es n).node j).cloc) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st ((wAt E es n).node j).cloc := by
  have hw := wAt_ok (es := es) hA.ord n
  have hS := hw.store
  have hext := store_mono (m := es.length) (es := es) hA.ord hn
  have hh := hon_all (es := es) hA.ord hA.exec hA.nodup hA.sane n hn
  have hci := (hw.nodes i).rooted _ (hw.nodes i).cloc
  have hcj := (hw.nodes j).rooted _ (hw.nodes j).cloc
  rcases Nat.eq_zero_or_pos (wAt E es n).now with h0 | hpos
  · rw [cloc_genesis_at_zero hA hn h0 j, (hw.nodes i).bimm, cloc_genesis_at_zero hA hn h0 i]
    have hmem := blockAtDepth_mem hS hS.rooted_gen E.c.k
    have hgen : chainIds (wAt E es n).st genesisId = [genesisId] := by
      obtain ⟨g, hg, hs, -⟩ := hS.gen
      unfold chainIds; rw [chain_genesis hg hs]; simp [hS.idOK _ _ hg]
    rw [hgen] at hmem ⊢; exact hmem
  obtain ⟨k, hk1, hk2⟩ := phase_of hG.e0 hG.mono hG.unb hpos
  have hNF : (wAt E es n).now ≤ (wF E es).now := now_mono hn le_rfl
  have hgi := goodAt_FT hA hS hext hNF (tree_good hS (hw.nodes i) (hh.slots i) (hw.nodes i).cloc) hKi
  have hgj := goodAt_FT hA hS hext hNF (tree_good hS (hw.nodes j) (hh.slots j) (hw.nodes j).cloc) hKj
  have hhd : ∀ l ∈ E.nodes, E.online l (wAt E es n).now = true →
      (FT E es K).hd (e k - E.Δ) ≤ height (wF E es).st ((wAt E es n).node l).cloc :=
    fun l hl hlo => le_trans (FT_hd_mono (by omega)) (hD l hl hlo)
  obtain ⟨x, hx1, hx2, hx3⟩ := nearAt hA hK hG hpos hNF hnH (A2_of_Hon hA hn hH) ⟨hk1, hk2⟩ hgi hgj
    (by rw [slotOf_ext hext hci.exists_blk]; exact hh.slots i _ (hw.nodes i).cloc)
    (by rw [slotOf_ext hext hcj.exists_blk]; exact hh.slots j _ (hw.nodes j).cloc)
    (hhd i hi hio) (hhd j hj hjo)
  rw [chainIds_ext hext hci] at hx1
  rw [chainIds_ext hext hcj] at hx2
  have hxr := (anc_height hS hci hx1).1
  rw [height_ext hext hci, height_ext hext hxr] at hx3
  rw [(hw.nodes i).bimm]
  exact chainIds_trans hS hcj hx2 (bimm_anc hS hci hx1 hx3)

/-- A node's local chain satisfies the block predicate at every point. -/
theorem cloc_K (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {W : ℕ → ℕ} {e : ℕ → ℕ} (hG : GoodCondW E es K W e H)
    {n : ℕ} (hn : n ≤ es.length) (hnH : (wAt E es n).now ≤ H) {i : ℕ} (hi : i ∈ E.nodes)
    (hio : E.online i (wAt E es n).now = true) : K ((wAt E es n).node i).cloc := by
  have hw := wAt_ok (es := es) hA.ord n
  have hh := hon_all (es := es) hA.ord hA.exec hA.nodup hA.sane n hn
  exact hK.step n hn hnH (fun m hm => main hA hK hG m (by omega)
    (le_trans (now_mono (E := E) (es := es) hm.le hn) hnH)) i hi hio _
    ((hw.nodes i).rooted _ (hw.nodes i).cloc) (hh.slots i _ (hw.nodes i).cloc)
    ((hw.nodes i).bimm_on_cloc hw.store).2

/-- **Agreement at every point.** Each honest node's `B_imm` is on every honest
node's local chain. -/
theorem agree_now (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {W : ℕ → ℕ} {e : ℕ → ℕ} (hG : GoodCondW E es K W e H)
    {n : ℕ} (hn : n ≤ es.length) (hnH : (wAt E es n).now ≤ H) {i j : ℕ} (hi : i ∈ E.nodes)
    (hj : j ∈ E.nodes) (hio : E.online i (wAt E es n).now = true) (hjo : E.online j (wAt E es n).now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st ((wAt E es n).node j).cloc :=
  agree_of hA hK.toKBase hG hn hnH (main hA hK hG n hn hnH).1 (main hA hK hG n hn hnH).2 hi hj hio hjo
    (cloc_K hA hK hG hn hnH hi hio) (cloc_K hA hK hG hn hnH hj hjo)

/-- **`k`-deep finality.** A block that an honest node has committed as immutable
(`B_imm`) is on every honest node's local chain at every later point of the
execution. -/
theorem bimm_final (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {W : ℕ → ℕ} {e : ℕ → ℕ} (hG : GoodCondW E es K W e H)
    {n n' : ℕ}
    (hnn : n ≤ n') (hn' : n' ≤ es.length) (hnH : (wAt E es n').now ≤ H) {i j : ℕ} (hi : i ∈ E.nodes)
    (hj : j ∈ E.nodes) (hio : E.online i (wAt E es n').now = true) (hjo : E.online j (wAt E es n').now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n').st ((wAt E es n').node j).cloc := by
  have hS := (wAt_ok (es := es) hA.ord n').store
  have h1 := bimm_persist (es := es) hA.ord hA.nodup i n' hnn hn'
  have h2 := agree_now hA hK hG hn' hnH hi hj hio hjo
  exact chainIds_trans hS ((wAt_ok (es := es) hA.ord n').nodes j |>.rooted _
    ((wAt_ok (es := es) hA.ord n').nodes j).cloc) h2 h1


/-- The trivial block predicate (every valid block is in the tree). -/
theorem KOK_true (H : ℕ) : KOK E es (fun _ => True) H :=
  ⟨⟨trivial, fun _ _ _ => trivial⟩, fun _ _ _ _ _ _ _ _ _ _ _ => trivial⟩

end Cryptarchia
