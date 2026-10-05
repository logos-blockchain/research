import Cryptarchia.Proof.Timing

/-!
# One node processing blocks: acceptance and adoption

Local facts about a single node, with the settlement input as a hypothesis
(`Near`): every candidate local chain meets the chain of `h` within `k` blocks.

* `claimA`: when a block `h` is accepted, the node's local chain afterwards is at
  least as high as `h`, for any tip order and either reading of `on_block`.
* `claimB`: receiving a block whose chain contains `h` accepts every block of
  `h`'s chain (none is pruned), and adopts a chain at least as high as `h` if `h`
  was new.
-/

namespace Cryptarchia

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}

theorem blockAtDepth_height (hS : StoreOK st) {b : ℕ} (hb : Rooted st b) (d : ℕ) :
    height st (blockAtDepth st b d) = height st b - d := by
  unfold blockAtDepth
  rcases le_or_gt d (height st b) with hd | hd
  · rw [chainIds_eq hS hb, List.getElem?_map, List.getElem?_range (by omega)]
    simp only [Option.map_some, Option.getD_some]
    exact (height_iter hS hb d).2
  · rw [List.getElem?_eq_none (by rw [chainIds_eq hS hb]; simp; omega)]
    simp only [Option.getD_none]
    rw [height_genesis hS]; omega

/-- If `x` is on `c`'s chain at most `k` below `c`, then `c`'s `k`-th ancestor is
an ancestor of `x`. -/
theorem bimm_anc (hS : StoreOK st) {cl x k : ℕ} (hcl : Rooted st cl) (hx : x ∈ chainIds st cl)
    (hk : height st cl - height st x ≤ k) : blockAtDepth st cl k ∈ chainIds st x := by
  have hbm := blockAtDepth_mem hS hcl k
  have hbh := blockAtDepth_height hS hcl k
  exact chainIds_total hS hcl hx hbm (by omega)

/-- A block is **good at time `t`**: rooted, not from the future, its whole chain
valid. Every block of every node's tree is. -/
def GoodAt (c : Config) (L : Ledger) (O : Oracle) (G : Genesis) (st : Store) (t b : ℕ) : Prop :=
  Rooted st b ∧ slotOf st b ≤ t ∧
    ∀ x ∈ chainIds st b, x = genesisId ∨ ∃ B, st x = some B ∧ validCore c st L O G B = true

/-- The settlement input: every good candidate at least as high as `H0` meets the
chain of `h` within `k` blocks. -/
def Near (c : Config) (L : Ledger) (O : Oracle) (G : Genesis) (st : Store) (t H0 h z : ℕ) : Prop :=
  ∀ cl, GoodAt c L O G st t cl → H0 ≤ height st cl → z ∈ chainIds st cl →
    ∃ x, x ∈ chainIds st cl ∧ x ∈ chainIds st h ∧ height st cl - height st x ≤ c.k

/-- Tree blocks are good. -/
theorem tree_good (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s) {t : ℕ}
    (hsl : ∀ x ∈ s.tree, slotOf st x ≤ t) {b : ℕ} (hb : b ∈ s.tree) : GoodAt c L O G st t b := by
  refine ⟨hs.rooted b hb, hsl b hb, ?_⟩
  intro x hx
  have hxT := chainIds_closed hS hs.rooted hs.closed hb x hx
  exact hs.valid x hxT

/-- `on_block` keeps every block of the tree at a slot no later than `now`. -/
theorem onBlock_slots {s : NodeState} (hrule : s.rule = .online) (fastPath : Bool)
    (ord : List ℕ → List ℕ) (now : ℕ)
    (B : Block) (hB : st B.hdr.id = some B) (hsl : ∀ x ∈ s.tree, slotOf st x ≤ now) :
    ∀ x ∈ (onBlock c st L O G fastPath ord now s B).tree, slotOf st x ≤ now := by
  unfold onBlock
  split
  · exact hsl
  rename_i hacc
  simp only [Bool.or_eq_true, not_or, Bool.not_eq_true, Bool.not_eq_eq_eq_not, Bool.not_true] at hacc
  have hv : validHeader c st L O G s.tree s.bimm now B = true := by simpa using hacc.2
  obtain ⟨-, hnow, -, -⟩ := (validHeader_iff c st L O G _ _ _ _).1 hv
  have hT' : ∀ x ∈ s.tree ++ [B.hdr.id], slotOf st x ≤ now := by
    intro x hx; rw [List.mem_append] at hx
    rcases hx with hx | hx
    · exact hsl x hx
    · simp at hx; subst hx; rw [slotOf_eq hB]; exact hnow
  rw [hrule]
  dsimp only
  intro x hx
  exact hT' x (List.mem_of_mem_filter hx)

/-- **Fork choice keeps `B_imm`.** A switch of the online loop from a candidate that
contains the node's `B_imm` and is at least as high as its local chain goes to a
chain that also contains `B_imm`. -/
theorem bimm_switch (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s) {cl f : ℕ}
    (hclr : Rooted st cl) (hfr : Rooted st f) (hclb : s.bimm ∈ chainIds st cl)
    (hclh : height st s.cloc ≤ height st cl) (hsw : onlineStep st c.k cl f ≠ cl) :
    s.bimm ∈ chainIds st f := by
  have hcr := hs.rooted _ hs.cloc
  have hbm : s.bimm ∈ chainIds st s.cloc := by rw [hs.bimm]; exact blockAtDepth_mem hS hcr _
  have hbr : Rooted st s.bimm := (anc_height hS hcr hbm).1
  have hoh : height st s.bimm = height st s.cloc - c.k := by
    rw [hs.bimm]; exact blockAtDepth_height hS hcr _
  obtain ⟨-, hk, hlt⟩ := onlineStep_switch hS hclr hfr hsw
  obtain ⟨hla, hlb, -⟩ := lca_spec hS hclr hfr
  have hlh := (anc_height hS hclr hla).2.1
  have hb_l : s.bimm ∈ chainIds st (lca st cl f) := by
    rcases le_total (height st s.bimm) (height st (lca st cl f)) with hle | hle
    · exact chainIds_total hS hclr hla hclb hle
    · have : height st s.bimm = height st (lca st cl f) := by omega
      have hbl : lca st cl f ∈ chainIds st s.bimm := chainIds_total hS hclr hclb hla hle
      obtain ⟨-, -, he⟩ := anc_height hS hbr hbl
      rw [this, Nat.sub_self, Function.iterate_zero_apply] at he
      rw [← he]; exact self_mem_chainIds hS hbr
  exact chainIds_trans hS hfr hlb hb_l

/-- **The immutable block never reverts under `on_block`.** -/
theorem onBlock_bimm (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ) (B : Block)
    (hB : st B.hdr.id = some B) :
    s.bimm ∈ chainIds st (onBlock c st L O G fastPath ord now s B).bimm := by
  have hok := onBlock_ok hS hs fastPath ord hord now B hB
  have hcr := hs.rooted _ hs.cloc
  set s' := onBlock c st L O G fastPath ord now s B
  have hcr' := hok.1.rooted _ hok.1.cloc
  -- the old `B_imm` is on the new local chain
  have hon : s.bimm ∈ chainIds st s'.cloc := by
    have hbm : s.bimm ∈ chainIds st s.cloc := by rw [hs.bimm]; exact blockAtDepth_mem hS hcr _
    have hbh : height st s.bimm = height st s.cloc - c.k := by rw [hs.bimm]; exact blockAtDepth_height hS hcr _
    have hbr : Rooted st s.bimm := (anc_height hS hcr hbm).1
    simp only [s']
    unfold onBlock
    split
    · exact hbm
    rename_i hacc
    simp only [Bool.or_eq_true, not_or, Bool.not_eq_true, Bool.not_eq_eq_eq_not, Bool.not_true] at hacc
    have hv : validHeader c st L O G s.tree s.bimm now B = true := by simpa using hacc.2
    obtain ⟨hcore, -, hpar, -⟩ := (validHeader_iff c st L O G _ _ _ _).1 hv
    have hcore' := hcore
    unfold validCore at hcore'
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hcore'
    obtain ⟨⟨⟨⟨⟨⟨hne, -⟩, hslot⟩, -⟩, -⟩, -⟩, -⟩ := hcore'
    have hBr : Rooted st B.hdr.id := Rooted.step B.hdr.id B hB hne (hs.rooted _ hpar) hslot
    have hT'r : ∀ y ∈ s.tree ++ [B.hdr.id], Rooted st y := by
      intro y hy; rw [List.mem_append] at hy
      rcases hy with hy | hy
      · exact hs.rooted y hy
      · simp at hy; subst hy; exact hBr
    rw [hs.rule]; dsimp only
    split
    · rename_i hfp
      simp only [Bool.and_eq_true, decide_eq_true_eq] at hfp
      -- the new block extends the local chain
      have : chainIds st B.hdr.id = B.hdr.id :: chainIds st B.hdr.parent := by
        unfold chainIds; rw [chain_step hB hne (hs.rooted _ hpar) hslot]; simp [hS.idOK _ _ hB]
      rw [this, hfp.2]; exact List.mem_cons_of_mem _ hbm
    · unfold forkChoice; simp only
      have htips : ∀ f ∈ ord (tips st (s.tree ++ [B.hdr.id])), f ∈ s.tree ++ [B.hdr.id] := fun f hf =>
        List.mem_of_mem_filter ((hord _).mem_iff.1 hf)
      apply (fc_inv (st := st) (fun cl => Rooted st cl ∧ s.bimm ∈ chainIds st cl ∧
        height st s.cloc ≤ height st cl) c.k _ s.cloc ⟨hcr, hbm, le_rfl⟩ ?_).2.1
      intro cl f ⟨hclr, hclb, hclh⟩ hf hsw
      have hfr := hT'r f (htips f hf)
      obtain ⟨-, hk, hlt⟩ := onlineStep_switch hS hclr hfr hsw
      obtain ⟨hla, hlb, -⟩ := lca_spec hS hclr hfr
      have hlh := (anc_height hS hclr hla).2.1
      refine ⟨hfr, ?_, by omega⟩
      -- `lca` is at least as high as the old `B_imm`, and both are on `cl`'s chain
      have hb_l : s.bimm ∈ chainIds st (lca st cl f) := by
        rcases le_total (height st s.bimm) (height st (lca st cl f)) with hle | hle
        · exact chainIds_total hS hclr hla hclb hle
        · -- only possible when the chain is shorter than `k`: then `B_imm` is genesis
          have : height st s.bimm = height st (lca st cl f) := by omega
          have hbl : lca st cl f ∈ chainIds st s.bimm := chainIds_total hS hclr hclb hla hle
          obtain ⟨-, -, he⟩ := anc_height hS hbr hbl
          rw [this, Nat.sub_self, Function.iterate_zero_apply] at he
          rw [← he]; exact self_mem_chainIds hS hbr
      exact chainIds_trans hS hfr hlb hb_l
  -- the new `B_imm` is at least as high, on the same chain
  have hnb : s'.bimm ∈ chainIds st s'.cloc := by rw [hok.1.bimm]; exact blockAtDepth_mem hS hcr' _
  have hnh : height st s'.bimm = height st s'.cloc - c.k := by
    rw [hok.1.bimm]; exact blockAtDepth_height hS hcr' _
  have hoh : height st s.bimm = height st s.cloc - c.k := by
    rw [hs.bimm]; exact blockAtDepth_height hS hcr _
  exact chainIds_total hS hcr' hnb hon (by have := hok.2; omega)

/-- **Claim A (adoption).** When `on_block` accepts `h` and every good candidate
at least as high as the current local chain meets `h`'s chain within `k`, the new
local chain is at least as high as `h`. -/
theorem claimA (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ)
    (B : Block) (hB : st B.hdr.id = some B) (hsl : ∀ x ∈ s.tree, slotOf st x ≤ now)
    (hnew : B.hdr.id ∉ s.tree) (hval : validHeader c st L O G s.tree s.bimm now B = true)
    {z : ℕ} (hz : z ∈ chainIds st s.bimm)
    (hnear : Near c L O G st now (height st s.cloc) B.hdr.id z) :
    height st B.hdr.id ≤ height st (onBlock c st L O G fastPath ord now s B).cloc := by
  have hacc : ¬(s.tree.contains B.hdr.id || !validHeader c st L O G s.tree s.bimm now B) = true := by
    simp [hval, hnew]
  obtain ⟨hcore, -, hpar, -⟩ := (validHeader_iff c st L O G _ _ _ _).1 hval
  have hcore' := hcore
  unfold validCore at hcore'
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hcore'
  obtain ⟨⟨⟨⟨⟨⟨hne, -⟩, hslot⟩, -⟩, -⟩, -⟩, -⟩ := hcore'
  have hBr : Rooted st B.hdr.id := Rooted.step B.hdr.id B hB hne (hs.rooted _ hpar) hslot
  unfold onBlock
  rw [if_neg hacc, hs.rule]
  simp only
  set T' := s.tree ++ [B.hdr.id] with hT'
  have hT'r : ∀ y ∈ T', Rooted st y := by
    intro y hy; rw [List.mem_append] at hy
    rcases hy with hy | hy
    · exact hs.rooted y hy
    · simp at hy; subst hy; exact hBr
  have hT'sl : ∀ y ∈ T', slotOf st y ≤ now := by
    intro y hy; rw [List.mem_append] at hy
    rcases hy with hy | hy
    · exact hsl y hy
    · simp at hy; subst hy; rw [slotOf_eq hB]
      exact ((validHeader_iff c st L O G _ _ _ _).1 hval).2.1
  have hT'good : ∀ y ∈ T', GoodAt c L O G st now y := by
    intro y hy
    refine ⟨hT'r y hy, hT'sl y hy, ?_⟩
    intro x hx
    have hcl : ∀ z ∈ T', parentOf st z ∈ T' := by
      intro z hz; rw [List.mem_append] at hz
      rcases hz with hz | hz
      · exact List.mem_append_left _ (hs.closed z hz)
      · simp at hz; subst hz; rw [parentOf_eq hB]; exact List.mem_append_left _ hpar
    have hxT := chainIds_closed hS hT'r hcl hy x hx
    rw [List.mem_append] at hxT
    rcases hxT with hxT | hxT
    · exact hs.valid x hxT
    · simp at hxT; subst hxT; exact Or.inr ⟨B, hB, hcore⟩
  -- the new local chain
  split
  · rename_i hfp
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hfp
    exact le_rfl
  · unfold forkChoice
    simp only
    have htips : ∀ f ∈ ord (tips st T'), f ∈ T' := by
      intro f hf
      exact List.mem_of_mem_filter ((hord (tips st T')).mem_iff.1 hf)
    have hr : ∀ f ∈ ord (tips st T'), Rooted st f := fun f hf => hT'r f (htips f hf)
    obtain ⟨f₀, hf₀tip, hBf₀⟩ := exists_tip hS hT'r (List.mem_append_right _ (List.mem_singleton_self _))
    have hf₀ : f₀ ∈ ord (tips st T') := (hord _).mem_iff.2 hf₀tip
    have hf₀r := hr f₀ hf₀
    have hBle : height st B.hdr.id ≤ height st f₀ := (anc_height hS hf₀r hBf₀).2.1
    have hcr0 := hs.rooted _ hs.cloc
    have hbm0 : s.bimm ∈ chainIds st s.cloc := by rw [hs.bimm]; exact blockAtDepth_mem hS hcr0 _
    let P : ℕ → Prop := fun cl => cl ∈ T' ∧ height st s.cloc ≤ height st cl ∧ s.bimm ∈ chainIds st cl
    have hreach := fc_reaches hS P c.k (ord (tips st T')) hr hf₀
      (by
        intro cl hPc hclr _
        obtain ⟨x, hxc, hxB, hk⟩ := hnear cl (hT'good cl hPc.1) hPc.2.1
          (chainIds_trans hS hclr hPc.2.2 hz)
        have hxf : x ∈ chainIds st f₀ := chainIds_trans hS hf₀r hBf₀ hxB
        obtain ⟨-, -, hmax⟩ := lca_spec hS hclr hf₀r
        have hxl := hmax x hxc hxf
        obtain ⟨hlr, -, -⟩ := anc_height hS hclr (lca_spec hS hclr hf₀r).1
        have := (anc_height hS hlr hxl).2.1
        omega)
      s.cloc ⟨List.mem_append_left _ hs.cloc, le_rfl, hbm0⟩ (hs.rooted _ hs.cloc)
      (by
        intro c' f hPc hf hne
        obtain ⟨-, -, hlt⟩ := onlineStep_switch hS (hT'r _ hPc.1) (hr f hf) hne
        exact ⟨htips f hf, by omega, bimm_switch hS hs (hT'r _ hPc.1) (hr f hf) hPc.2.2 hPc.2.1 hne⟩)
    omega

end Cryptarchia

namespace Cryptarchia

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}

/-- `on_block` adds at most the processed block. -/
theorem onBlock_tree_sub {s : NodeState} (hrule : s.rule = .online) (fastPath : Bool)
    (ord : List ℕ → List ℕ) (now : ℕ) (B : Block) :
    ∀ x ∈ (onBlock c st L O G fastPath ord now s B).tree, x ∈ s.tree ∨ x = B.hdr.id := by
  unfold onBlock
  split
  · intro x hx; exact Or.inl hx
  rw [hrule]; dsimp only
  intro x hx
  have := List.mem_of_mem_filter hx
  rw [List.mem_append] at this
  rcases this with h | h
  · exact Or.inl h
  · simp at h; exact Or.inr h

/-- The fold invariant: a well-formed node, no block from the future, and a
local chain at least `H0` high. -/
def FoldInv (c : Config) (L : Ledger) (O : Oracle) (G : Genesis) (st : Store) (now H0 z : ℕ)
    (s : NodeState) : Prop :=
  NodeOK c.k st L O G c s ∧ (∀ x ∈ s.tree, slotOf st x ≤ now) ∧ H0 ≤ height st s.cloc ∧
    z ∈ chainIds st s.bimm

theorem onBlock_inv (hS : StoreOK st) {now H0 z : ℕ} {s : NodeState} (hs : FoldInv c L O G st now H0 z s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (B : Block)
    (hB : st B.hdr.id = some B) :
    FoldInv c L O G st now H0 z (onBlock c st L O G fastPath ord now s B) := by
  obtain ⟨h1, h2⟩ := onBlock_ok hS hs.1 fastPath ord hord now B hB
  have hb := onBlock_bimm hS hs.1 fastPath ord hord now B hB
  have hcr := h1.rooted _ h1.cloc
  have hbr : Rooted st (onBlock c st L O G fastPath ord now s B).bimm := by
    have : (onBlock c st L O G fastPath ord now s B).bimm ∈ chainIds st
        (onBlock c st L O G fastPath ord now s B).cloc := by
      rw [h1.bimm]; exact blockAtDepth_mem hS hcr _
    exact (anc_height hS hcr this).1
  exact ⟨h1, onBlock_slots hs.1.rule fastPath ord now B hB hs.2.1, le_trans hs.2.2.1 h2,
    chainIds_trans hS hbr hb hs.2.2.2⟩

/-- Under `Near`, the node's immutable block is on `h`'s chain. -/
theorem bimm_on (hS : StoreOK st) {now H0 h z : ℕ} {s : NodeState} (hs : FoldInv c L O G st now H0 z s)
    (hhr : Rooted st h) (hnear : Near c L O G st now H0 h z) : s.bimm ∈ chainIds st h := by
  have hcr := hs.1.rooted _ hs.1.cloc
  have hbm : s.bimm ∈ chainIds st s.cloc := by rw [hs.1.bimm]; exact blockAtDepth_mem hS hcr _
  obtain ⟨x, hxc, hxh, hk⟩ := hnear s.cloc (tree_good hS hs.1 hs.2.1 hs.1.cloc) hs.2.2.1
    (chainIds_trans hS hcr hbm hs.2.2.2)
  rw [hs.1.bimm]
  exact chainIds_trans hS hhr hxh (bimm_anc hS hcr hxc hk)

/-- `on_block` keeps every block comparable with the new immutable block. -/
theorem onBlock_keep (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s) (fastPath : Bool)
    (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ) (B : Block)
    (hB : st B.hdr.id = some B) {x : ℕ}
    (hx : x ∈ s.tree ∨ (x = B.hdr.id ∧ validHeader c st L O G s.tree s.bimm now B = true))
    (hcmp : (onBlock c st L O G fastPath ord now s B).bimm ∈ chainIds st x ∨
      x ∈ chainIds st (onBlock c st L O G fastPath ord now s B).bimm) :
    x ∈ (onBlock c st L O G fastPath ord now s B).tree := by
  have hok := (onBlock_ok hS hs fastPath ord hord now B hB).1
  revert hcmp
  unfold onBlock
  split
  · rename_i hign
    intro _
    rcases hx with hx | ⟨rfl, hv⟩
    · exact hx
    · simp only [hv, Bool.not_true, Bool.or_false, List.contains_iff_mem] at hign; exact hign
  rename_i hacc
  simp only [Bool.or_eq_true, not_or, Bool.not_eq_true, Bool.not_eq_eq_eq_not, Bool.not_true] at hacc
  have hv : validHeader c st L O G s.tree s.bimm now B = true := by simpa using hacc.2
  obtain ⟨hcore, -, hpar, -⟩ := (validHeader_iff c st L O G _ _ _ _).1 hv
  have hcore' := hcore
  unfold validCore at hcore'
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hcore'
  obtain ⟨⟨⟨⟨⟨⟨hne, -⟩, hslot⟩, -⟩, -⟩, -⟩, -⟩ := hcore'
  have hBr : Rooted st B.hdr.id := Rooted.step B.hdr.id B hB hne (hs.rooted _ hpar) hslot
  have hT'r : ∀ y ∈ s.tree ++ [B.hdr.id], Rooted st y := by
    intro y hy; rw [List.mem_append] at hy
    rcases hy with hy | hy
    · exact hs.rooted y hy
    · simp at hy; subst hy; exact hBr
  rw [hs.rule]
  dsimp only
  intro hcmp
  -- the new immutable block is rooted: it is on the new local chain
  have hbr : ∀ cl, Rooted st cl → Rooted st (blockAtDepth st cl c.k) := fun cl hcl =>
    (anc_height hS hcl (blockAtDepth_mem hS hcl c.k)).1
  have hclr : Rooted st (if (fastPath && decide (B.hdr.parent = s.cloc)) = true then B.hdr.id
      else forkChoice st Rule.online c.k c.sGen s.cloc (ord (tips st (s.tree ++ [B.hdr.id])))) := by
    split
    · exact hBr
    · unfold forkChoice; simp only
      exact (fc_height hS c.k _ (fun f hf => hT'r f (List.mem_of_mem_filter
        ((hord _).mem_iff.1 hf))) s.cloc (hs.rooted _ hs.cloc)).1
  apply mem_prune hS hT'r (hbr _ hclr) _ hcmp
  rcases hx with hx | ⟨rfl, -⟩
  · exact List.mem_append_left _ hx
  · exact List.mem_append_right _ (List.mem_singleton_self _)

/-- Slots do not increase towards genesis. -/
theorem slot_anc_le (hS : StoreOK st) {a b : ℕ} (hb : Rooted st b) (ha : a ∈ chainIds st b) :
    slotOf st a ≤ slotOf st b := by
  obtain ⟨j, -, rfl⟩ := (mem_chainIds hS hb).1 ha
  clear ha
  induction j generalizing b with
  | zero => simp
  | succ j ih =>
    rw [Function.iterate_succ_apply]
    have hp := hb.parent_rooted hS.genSelf
    refine le_trans (ih hp) ?_
    rcases eq_or_ne b genesisId with h0 | h0
    · subst h0; obtain ⟨g, hg, -, hgp⟩ := hS.gen; rw [parentOf_eq hg, hgp]
    · obtain ⟨blk, hbk, -, hs⟩ := hb.inv h0
      rw [parentOf_eq hbk, slotOf_eq hbk]; exact hs.le

theorem Near.mono {now H0 H1 h z : ℕ} (hn : Near c L O G st now H0 h z) (hle : H0 ≤ H1) :
    Near c L O G st now H1 h z := fun cl hg hh hz => hn cl hg (le_trans hle hh) hz

/-- A block on `h`'s chain, not yet in the tree, whose parent is, is accepted. -/
theorem accept_on_chain (hS : StoreOK st) {now H0 h a z : ℕ} {s : NodeState}
    (hs : FoldInv c L O G st now H0 z s) (hhr : Rooted st h) (hnear : Near c L O G st now H0 h z)
    (hah : a ∈ chainIds st h) (hslh : slotOf st h ≤ now) {A : Block} (hA : st a = some A)
    (hvalA : validCore c st L O G A = true) (hnew : a ∉ s.tree) (hpar : A.hdr.parent ∈ s.tree) :
    validHeader c st L O G s.tree s.bimm now A = true := by
  have hid := hS.idOK _ _ hA
  rw [validHeader_iff]
  have hsa : A.hdr.slot ≤ now := by
    have := slot_anc_le hS hhr hah; rw [slotOf_eq hA] at this; omega
  refine ⟨hvalA, hsa, hpar, ?_⟩
  -- step 8: otherwise `a` would be below the immutable block, hence already in the tree
  by_contra hle
  push Not at hle
  have hbm := bimm_on hS hs hhr hnear
  have hcr := hs.1.rooted _ hs.1.cloc
  have har := (anc_height hS hhr hah).1
  have hunfold : a ≠ genesisId := by
    intro h0; subst h0; exact hnew hs.1.gen
  obtain ⟨blk, hbk, hp, hsl⟩ := har.inv hunfold
  rw [hA] at hbk; cases hbk
  have hha : height st a = height st A.hdr.parent + 1 := height_step hA hunfold hp hsl
  have hab : a ∈ chainIds st s.bimm := chainIds_total hS hhr hbm hah (by omega)
  have hbc : s.bimm ∈ chainIds st s.cloc := by rw [hs.1.bimm]; exact blockAtDepth_mem hS hcr c.k
  exact hnew (chainIds_closed hS hs.1.rooted hs.1.closed hs.1.cloc a (chainIds_trans hS hcr hbc hab))

section Fold

variable (hS : StoreOK st) {now H0 h z : ℕ} (hhr : Rooted st h)
  (hvalh : ∀ a ∈ chainIds st h, a = genesisId ∨ ∃ A, st a = some A ∧ validCore c st L O G A = true)
  (hslh : slotOf st h ≤ now) (hnear : Near c L O G st now H0 h z)
  (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l)
include hS hhr hvalh hslh hnear hord

/-- **Processing `h`'s chain up to `a`** accepts all of it and adds nothing else. -/
theorem fold_chain : ∀ a, Rooted st a → a ∈ chainIds st h → ∀ s, FoldInv c L O G st now H0 z s →
    FoldInv c L O G st now H0 z ((chainUp st a).foldl (onBlock c st L O G fastPath ord now) s) ∧
      (∀ x ∈ chainIds st a, x ∈ ((chainUp st a).foldl (onBlock c st L O G fastPath ord now) s).tree) ∧
      (∀ x ∈ ((chainUp st a).foldl (onBlock c st L O G fastPath ord now) s).tree,
        x ∈ s.tree ∨ x ∈ chainIds st a) := by
  intro a ha
  induction ha with
  | gen g hg hs0 =>
    intro _ s hs
    have hc : chainUp st genesisId = [g] := by unfold chainUp; rw [chain_genesis hg hs0]; simp
    have hid := hS.idOK _ _ hg
    rw [hc]
    simp only [List.foldl_cons, List.foldl_nil]
    have hsame : onBlock c st L O G fastPath ord now s g = s := by
      unfold onBlock
      rw [if_pos (by simp [hid, hs.1.gen])]
    rw [hsame]
    refine ⟨hs, ?_, fun x hx => Or.inl hx⟩
    intro x hx
    unfold chainIds at hx; rw [chain_genesis hg hs0] at hx
    simp [hid] at hx; subst hx; exact hs.1.gen
  | step a A hA hne hpar hslot ih =>
    intro hah s hs
    have hid := hS.idOK _ _ hA
    have har : Rooted st a := Rooted.step a A hA hne hpar hslot
    have hpc : A.hdr.parent ∈ chainIds st a := by
      unfold chainIds; rw [chain_step hA hne hpar hslot]; simp [(hS.idOK _ _ hA)]
      right; exact self_mem_chainIds hS hpar |> fun h => by simpa [chainIds] using h
    have hph : A.hdr.parent ∈ chainIds st h := chainIds_trans hS hhr hah hpc
    obtain ⟨hi1, hi2, hi3⟩ := ih hph s hs
    rw [chainUp_step hA hne hpar hslot, List.foldl_append]
    simp only [List.foldl_cons, List.foldl_nil]
    set sp := (chainUp st A.hdr.parent).foldl (onBlock c st L O G fastPath ord now) s
    have hA' : st A.hdr.id = some A := by rw [hid]; exact hA
    have hinv := onBlock_inv hS hi1 fastPath ord hord A hA'
    have hbm' := bimm_on hS hinv hhr hnear
    have hchainA : chainIds st a = a :: chainIds st A.hdr.parent := by
      unfold chainIds; rw [chain_step hA hne hpar hslot]; simp [hid]
    refine ⟨hinv, ?_, ?_⟩
    · -- every block of `a`'s chain is kept or added
      have hkeep : ∀ x ∈ chainIds st a, x ∈ sp.tree ∨ x = a →
          x ∈ (onBlock c st L O G fastPath ord now sp A).tree := by
        intro x hxa hx
        have hxh : x ∈ chainIds st h := chainIds_trans hS hhr hah hxa
        have hcmp : (onBlock c st L O G fastPath ord now sp A).bimm ∈ chainIds st x ∨
            x ∈ chainIds st (onBlock c st L O G fastPath ord now sp A).bimm := by
          rcases le_total (height st x) (height st (onBlock c st L O G fastPath ord now sp A).bimm)
            with hle | hle
          · right; exact chainIds_total hS hhr hbm' hxh hle
          · left; exact chainIds_total hS hhr hxh hbm' hle
        rcases hx with hx | hxa
        · exact onBlock_keep hS hi1.1 fastPath ord hord now A hA' (Or.inl hx) hcmp
        · -- `a` itself: kept if present, otherwise accepted
          subst hxa
          by_cases hin : x ∈ sp.tree
          · exact onBlock_keep hS hi1.1 fastPath ord hord now A hA' (Or.inl hin) hcmp
          · have hvalA : validCore c st L O G A = true := by
              rcases hvalh x hah with h0 | ⟨A', hA'', hv⟩
              · exact absurd h0 hne
              · rw [hA] at hA''; cases hA''; exact hv
            have hacc := accept_on_chain hS hi1 hhr hnear hah hslh hA hvalA hin
              (hi2 _ (self_mem_chainIds hS hpar))
            exact onBlock_keep hS hi1.1 fastPath ord hord now A hA' (Or.inr ⟨hid.symm, hacc⟩) hcmp
      intro x hx
      rw [hchainA, List.mem_cons] at hx
      rcases hx with rfl | hx
      · exact hkeep x (self_mem_chainIds hS har) (Or.inr rfl)
      · exact hkeep x (by rw [hchainA]; exact List.mem_cons_of_mem _ hx) (Or.inl (hi2 x hx))
    · intro x hx
      rcases onBlock_tree_sub hi1.1.rule fastPath ord now A x hx with hx | hx
      · rcases hi3 x hx with h1 | h1
        · exact Or.inl h1
        · right; rw [hchainA]; exact List.mem_cons_of_mem _ h1
      · right; rw [hx, hid]; exact self_mem_chainIds hS har

/-- **Claim B (acceptance).** Receiving any block whose chain contains `h` accepts
all of `h`'s chain; if `h` was new, the local chain ends at least as high as `h`. -/
theorem claimB {b : ℕ} (hbr : Rooted st b) (hhb : h ∈ chainIds st b) {s : NodeState}
    (hs : FoldInv c L O G st now H0 z s) :
    let s' := receive c st L O G fastPath ord now s b
    (∀ x ∈ chainIds st h, x ∈ s'.tree) ∧ (h ∉ s.tree → height st h ≤ height st s'.cloc) := by
  intro s'
  obtain ⟨R, hR⟩ := chainUp_split hS hbr hhb
  have hs' : s' = R.foldl (onBlock c st L O G fastPath ord now)
      ((chainUp st h).foldl (onBlock c st L O G fastPath ord now) s) := by
    simp only [s', receive, hR, List.foldl_append]
  obtain ⟨hf1, hf2, hf3⟩ := fold_chain hS hhr hvalh hslh hnear fastPath ord hord h hhr
    (self_mem_chainIds hS hhr) s hs
  set sh := (chainUp st h).foldl (onBlock c st L O G fastPath ord now) s
  have hRst : ∀ x ∈ R, st x.hdr.id = some x := by
    intro x hx
    have : x ∈ chainUp st b := by rw [hR]; exact List.mem_append_right _ hx
    exact mem_chainUp_store hS this
  -- the rest keeps `h`'s chain and never lowers the local chain
  have hrest : ∀ (l : List Block), (∀ x ∈ l, st x.hdr.id = some x) → ∀ s₀,
      FoldInv c L O G st now H0 z s₀ → (∀ x ∈ chainIds st h, x ∈ s₀.tree) →
      (∀ x ∈ chainIds st h, x ∈ (l.foldl (onBlock c st L O G fastPath ord now) s₀).tree) ∧
        height st s₀.cloc ≤ height st (l.foldl (onBlock c st L O G fastPath ord now) s₀).cloc := by
    intro l
    induction l with
    | nil => intro _ s₀ _ h; exact ⟨h, le_rfl⟩
    | cons B bs ih =>
      intro hst s₀ hs₀ hin
      simp only [List.foldl_cons]
      have hB := hst B List.mem_cons_self
      have hinv := onBlock_inv hS hs₀ fastPath ord hord B hB
      have hbm := bimm_on hS hinv hhr hnear
      have hkept : ∀ x ∈ chainIds st h, x ∈ (onBlock c st L O G fastPath ord now s₀ B).tree := by
        intro x hx
        apply onBlock_keep hS hs₀.1 fastPath ord hord now B hB (Or.inl (hin x hx))
        rcases le_total (height st x) (height st (onBlock c st L O G fastPath ord now s₀ B).bimm)
          with hle | hle
        · right; exact chainIds_total hS hhr hbm hx hle
        · left; exact chainIds_total hS hhr hx hbm hle
      obtain ⟨h1, h2⟩ := ih (fun x hx => hst x (List.mem_cons_of_mem _ hx)) _ hinv hkept
      exact ⟨h1, le_trans (onBlock_ok hS hs₀.1 fastPath ord hord now B hB).2 h2⟩
  obtain ⟨hr1, hr2⟩ := hrest R hRst sh hf1 hf2
  rw [hs']
  refine ⟨hr1, ?_⟩
  intro hnew
  refine le_trans ?_ hr2
  -- `h` was added in the last step of processing its chain
  rcases eq_or_ne h genesisId with h0 | h0
  · subst h0; exact absurd hs.1.gen hnew
  obtain ⟨H, hH, hpar, hslot⟩ := hhr.inv h0
  have hid := hS.idOK _ _ hH
  have hsplit : sh = onBlock c st L O G fastPath ord now
      ((chainUp st H.hdr.parent).foldl (onBlock c st L O G fastPath ord now) s) H := by
    simp only [sh, chainUp_step hH h0 hpar hslot, List.foldl_append, List.foldl_cons, List.foldl_nil]
  have hpc : H.hdr.parent ∈ chainIds st h := by
    unfold chainIds; rw [chain_step hH h0 hpar hslot]; simp
    right; simpa [chainIds] using self_mem_chainIds hS hpar
  obtain ⟨hp1, hp2, hp3⟩ := fold_chain hS hhr hvalh hslh hnear fastPath ord hord H.hdr.parent hpar hpc s hs
  set sp := (chainUp st H.hdr.parent).foldl (onBlock c st L O G fastPath ord now) s
  have hnotp : h ∉ sp.tree := by
    intro hin
    rcases hp3 h hin with h1 | h1
    · exact hnew h1
    · have := (anc_height hS hpar h1).2.1
      rw [height_step hH h0 hpar hslot] at this; omega
  have hvalH : validCore c st L O G H = true := by
    rcases hvalh h (self_mem_chainIds hS hhr) with h1 | ⟨H', hH', hv⟩
    · exact absurd h1 h0
    · rw [hH] at hH'; cases hH'; exact hv
  have hacc := accept_on_chain hS hp1 hhr hnear (self_mem_chainIds hS hhr) hslh hH hvalH hnotp
    (hp2 _ (self_mem_chainIds hS hpar))
  rw [hsplit]
  have hH' : st H.hdr.id = some H := by rw [hid]; exact hH
  have := claimA hS hp1.1 fastPath ord hord now H hH' hp1.2.1 (by rw [hid]; exact hnotp) hacc
    hp1.2.2.2 (by rw [hid]; exact hnear.mono hp1.2.2.1)
  rwa [hid] at this

end Fold

theorem receive_ok_list (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ) :
    ∀ (l : List Block), (∀ x ∈ l, st x.hdr.id = some x) →
      NodeOK c.k st L O G c (l.foldl (onBlock c st L O G fastPath ord now) s) ∧
        height st s.cloc ≤ height st (l.foldl (onBlock c st L O G fastPath ord now) s).cloc := by
  intro l
  induction l generalizing s with
  | nil => intro _; exact ⟨hs, le_rfl⟩
  | cons x xs ih =>
    intro hx
    simp only [List.foldl_cons]
    obtain ⟨h1, h2⟩ := onBlock_ok hS hs fastPath ord hord now x (hx x List.mem_cons_self)
    obtain ⟨h3, h4⟩ := ih h1 (fun y hy => hx y (List.mem_cons_of_mem _ hy))
    exact ⟨h3, le_trans h2 h4⟩

/-- A block added by `on_block` passed validation. -/
theorem onBlock_added_valid {s : NodeState} (fastPath : Bool) (ord : List ℕ → List ℕ) (now : ℕ)
    (B : Block) (hnew : B.hdr.id ∉ s.tree)
    (hin : B.hdr.id ∈ (onBlock c st L O G fastPath ord now s B).tree) :
    validHeader c st L O G s.tree s.bimm now B = true := by
  by_contra hv
  have : onBlock c st L O G fastPath ord now s B = s := by
    unfold onBlock; rw [if_pos (by simp [hv])]
  rw [this] at hin; exact hnew hin

/-- **Whatever list of blocks a node processes**, if `h` enters its tree, the
node ends with a local chain at least as high as `h`. -/
theorem fold_adds (hS : StoreOK st) {now H0 h z : ℕ} (hnear : Near c L O G st now H0 h z)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) :
    ∀ (l : List Block), (∀ x ∈ l, st x.hdr.id = some x) → ∀ s, FoldInv c L O G st now H0 z s →
      h ∉ s.tree → h ∈ (l.foldl (onBlock c st L O G fastPath ord now) s).tree →
      height st h ≤ height st (l.foldl (onBlock c st L O G fastPath ord now) s).cloc := by
  intro l
  induction l with
  | nil => intro _ s _ hn hin; exact absurd hin hn
  | cons B bs ih =>
    intro hst s hs hn hin
    simp only [List.foldl_cons] at hin ⊢
    have hB := hst B List.mem_cons_self
    have hinv := onBlock_inv hS hs fastPath ord hord B hB
    have hmono : ∀ s', FoldInv c L O G st now H0 z s' →
        height st s'.cloc ≤ height st (bs.foldl (onBlock c st L O G fastPath ord now) s').cloc := by
      intro s' hs'
      exact (receive_ok_list hS hs'.1 fastPath ord hord now bs (fun x hx => hst x (List.mem_cons_of_mem _ hx))).2
    by_cases hh : h ∈ (onBlock c st L O G fastPath ord now s B).tree
    · -- `h` was added in this step
      rcases onBlock_tree_sub hs.1.rule fastPath ord now B h hh with h1 | h1
      · exact absurd h1 hn
      · subst h1
        have hval := onBlock_added_valid fastPath ord now B hn hh
        have := claimA hS hs.1 fastPath ord hord now B hB hs.2.1 hn hval hs.2.2.2 (hnear.mono hs.2.2.1)
        exact le_trans this (hmono _ hinv)
    · exact ih (fun x hx => hst x (List.mem_cons_of_mem _ hx)) _ hinv hh hin

theorem fold_bimm (hS : StoreOK st) (fastPath : Bool) (ord : List ℕ → List ℕ)
    (hord : ∀ l, (ord l).Perm l) (now : ℕ) :
    ∀ (l : List Block), (∀ x ∈ l, st x.hdr.id = some x) → ∀ s, NodeOK c.k st L O G c s →
      s.bimm ∈ chainIds st (l.foldl (onBlock c st L O G fastPath ord now) s).bimm := by
  intro l
  induction l with
  | nil =>
    intro _ s hs
    simp only [List.foldl_nil]
    have hmem : s.bimm ∈ chainIds st s.cloc := by
      rw [hs.bimm]; exact blockAtDepth_mem hS (hs.rooted _ hs.cloc) _
    exact self_mem_chainIds hS (anc_height hS (hs.rooted _ hs.cloc) hmem).1
  | cons B bs ih =>
    intro hst s hs
    simp only [List.foldl_cons]
    have hB := hst B List.mem_cons_self
    have hok := onBlock_ok hS hs fastPath ord hord now B hB
    have h1 := onBlock_bimm hS hs fastPath ord hord now B hB
    have h2 := ih (fun x hx => hst x (List.mem_cons_of_mem _ hx)) _ hok.1
    have hr : Rooted st (bs.foldl (onBlock c st L O G fastPath ord now)
        (onBlock c st L O G fastPath ord now s B)).bimm := by
      have hok2 := receive_ok_list hS hok.1 fastPath ord hord now bs
        (fun x hx => hst x (List.mem_cons_of_mem _ hx))
      have hcr := hok2.1.rooted _ hok2.1.cloc
      have hmem : (bs.foldl (onBlock c st L O G fastPath ord now)
          (onBlock c st L O G fastPath ord now s B)).bimm ∈ chainIds st
          (bs.foldl (onBlock c st L O G fastPath ord now) (onBlock c st L O G fastPath ord now s B)).cloc := by
        rw [hok2.1.bimm]; exact blockAtDepth_mem hS hcr _
      exact (anc_height hS hcr hmem).1
    exact chainIds_trans hS hr h2 h1


theorem NodeOK.bimm_on_cloc (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s) :
    Rooted st s.bimm ∧ s.bimm ∈ chainIds st s.cloc := by
  have hcr := hs.rooted _ hs.cloc
  have hm : s.bimm ∈ chainIds st s.cloc := by rw [hs.bimm]; exact blockAtDepth_mem hS hcr _
  exact ⟨(anc_height hS hcr hm).1, hm⟩

end Cryptarchia
