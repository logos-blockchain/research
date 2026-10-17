module

public import Cryptarchia.Proof.Structural
import Cryptarchia.Proof.Maintenance
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.NNRat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.Height.NumberField
import Mathlib.NumberTheory.Height.Projectivization
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.SelbergSieve
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.Tactic.Echelon.Zsqrtd
import Mathlib.Tactic.NormNum.Irrational
import Mathlib.Tactic.NormNum.IsCoprime
import Mathlib.Tactic.NormNum.IsSquare
import Mathlib.Tactic.NormNum.LegendreSymbol
import Mathlib.Tactic.NormNum.ModEq
import Mathlib.Tactic.NormNum.NatFib
import Mathlib.Tactic.NormNum.NatLog
import Mathlib.Tactic.NormNum.NatSqrt
import Mathlib.Tactic.NormNum.Ordinal
import Mathlib.Tactic.NormNum.Parity
import Mathlib.Tactic.NormNum.Prime
import Mathlib.Tactic.NormNum.RealSqrt
import Mathlib.Topology.Sheaves.Init
import Std.Tactic.BVDecide.Normalize.Bool
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# `on_block` and `receive` preserve well-formedness

`onBlock_step`: processing a stored block keeps a node well formed, adds only
blocks not from after the current time, never lowers the height of its local chain,
and keeps its immutable block below the new one (`NodeStep`), whichever reading of
`on_block` (with or without the shortcut) and whichever tip order. `receive_step`:
so does receiving a block.
-/

@[expose] public section

namespace Cryptarchia

variable {c : Config} {st : Store} {L : Ledger} {O : Oracle} {G : Genesis}

theorem blockAtDepth_mem (hS : StoreOK st) {b : ℕ} (hb : Rooted st b) (d : ℕ) :
    blockAtDepth st b d ∈ chainIds st b := by
  unfold blockAtDepth
  cases h : (chainIds st b)[d]? with
  | none => exact genesis_mem_chainIds hS hb
  | some x => exact List.mem_of_getElem? h

theorem mem_chainF_store (hS : StoreOK st) : ∀ n b x, x ∈ chainF st n b → st x.hdr.id = some x := by
  intro n
  induction n with
  | zero => intro b x h; simp [chainF] at h
  | succ n ih =>
    intro b x h
    unfold chainF at h
    cases hb : st b with
    | none => rw [hb] at h; simp at h
    | some blk =>
      rw [hb] at h
      simp only at h
      have hid := hS.idOK b blk hb
      split at h
      · simp at h; subst h; rw [hid]; exact hb
      · rcases List.mem_cons.1 h with h | h
        · subst h; rw [hid]; exact hb
        · exact ih _ _ h

theorem mem_chainUp (hS : StoreOK st) {b : ℕ} {x : Block} (h : x ∈ chainUp st b) :
    st x.hdr.id = some x := by
  unfold chainUp chain at h
  rw [List.mem_reverse] at h
  cases hb : st b with
  | none => rw [hb] at h; simp at h
  | some blk => rw [hb] at h; exact mem_chainF_store hS _ _ _ h

theorem chainIds_closed {T : List ℕ} (hS : StoreOK st) (hT : ∀ y ∈ T, Rooted st y)
    (hcl : ∀ y ∈ T, parentOf st y ∈ T) {b : ℕ} (hb : b ∈ T) : ∀ x ∈ chainIds st b, x ∈ T := by
  intro x hx
  obtain ⟨j, -, rfl⟩ := (mem_chainIds hS (hT b hb)).1 hx
  clear hx
  induction j with
  | zero => simpa using hb
  | succ j ih => rw [Function.iterate_succ_apply']; exact hcl _ ih

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

/-- A node's immutable block is rooted, on its local chain. -/
theorem NodeOK.bimm_on_cloc (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s) :
    Rooted st s.bimm ∧ s.bimm ∈ chainIds st s.cloc := by
  have hcr := hs.rooted _ hs.cloc
  have hm : s.bimm ∈ chainIds st s.cloc := by rw [hs.bimm]; exact blockAtDepth_mem hS hcr _
  exact ⟨(anc_height hS hcr hm).1, hm⟩

/-! ## The two outcomes of `on_block` -/

/-- `on_block` ignores a block it holds or that fails validation. -/
theorem onBlock_ign {s : NodeState} {fastPath : Bool} {ord : List ℕ → List ℕ} {now : ℕ} {B : Block}
    (h : ¬ (B.hdr.id ∉ s.tree ∧ validHeader c st L O G s.tree s.bimm now B = true)) :
    onBlock c st L O G fastPath ord now s B = s := by
  unfold onBlock
  rw [if_pos (by
    by_contra hc
    simp only [Bool.or_eq_true, List.contains_iff_mem, Bool.not_eq_true', not_or,
      Bool.not_eq_false] at hc
    exact h hc)]

/-- **`on_block` accepts a new valid block**: it moves to the block itself (the
shortcut) or to the fork choice over the extended tree's tips, and prunes at the new
`B_imm`. -/
theorem onBlock_acc {s : NodeState} (hrule : s.rule = .online) (fastPath : Bool)
    (ord : List ℕ → List ℕ) {now : ℕ} {B : Block} (hnew : B.hdr.id ∉ s.tree)
    (hval : validHeader c st L O G s.tree s.bimm now B = true) :
    ∃ cl, (cl = B.hdr.id ∧ B.hdr.parent = s.cloc ∨
        cl = forkChoice st .online c.k c.sGen s.cloc (ord (tips st (s.tree ++ [B.hdr.id])))) ∧
      onBlock c st L O G fastPath ord now s B =
        { s with cloc := cl, bimm := blockAtDepth st cl c.k,
                 tree := pruneForks st (s.tree ++ [B.hdr.id]) (blockAtDepth st cl c.k) } := by
  unfold onBlock
  rw [if_neg (by simp [hnew, hval]), hrule]
  dsimp only
  by_cases hfp : (fastPath && decide (B.hdr.parent = s.cloc)) = true
  · rw [if_pos hfp]
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hfp
    exact ⟨_, Or.inl ⟨rfl, hfp.2⟩, rfl⟩
  · rw [if_neg hfp]
    exact ⟨_, Or.inr rfl, rfl⟩

/-- **An accepted block** extends the tree by rooted blocks, closed under parents,
each valid. -/
theorem accept_ok {s : NodeState} (hs : NodeOK c.k st L O G c s) {now : ℕ} {B : Block}
    (hB : st B.hdr.id = some B) (hval : validHeader c st L O G s.tree s.bimm now B = true) :
    ∀ y ∈ s.tree ++ [B.hdr.id], Rooted st y ∧ parentOf st y ∈ s.tree ++ [B.hdr.id] ∧
      (y = genesisId ∨ ∃ B', st y = some B' ∧ validCore c st L O G B' = true) := by
  obtain ⟨hcore, -, hpar, -⟩ := (validHeader_iff c st L O G _ _ _ _).1 hval
  have hcore' := hcore
  unfold validCore at hcore'
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hcore'
  obtain ⟨⟨⟨⟨⟨⟨hne, -⟩, hslot⟩, -⟩, -⟩, -⟩, -⟩ := hcore'
  intro y hy
  rcases List.mem_append.1 hy with hy | hy
  · exact ⟨hs.rooted y hy, List.mem_append_left _ (hs.closed y hy), hs.valid y hy⟩
  · rw [List.mem_singleton] at hy; subst hy
    exact ⟨Rooted.step _ B hB hne (hs.rooted _ hpar) hslot,
      by rw [parentOf_eq hB]; exact List.mem_append_left _ hpar, Or.inr ⟨B, hB, hcore⟩⟩

/-- An accepted block is one above its parent. -/
theorem accept_height {s : NodeState} (hs : NodeOK c.k st L O G c s) {now : ℕ} {B : Block}
    (hB : st B.hdr.id = some B) (hval : validHeader c st L O G s.tree s.bimm now B = true) :
    height st B.hdr.id = height st B.hdr.parent + 1 := by
  obtain ⟨hcore, -, hpar, -⟩ := (validHeader_iff c st L O G _ _ _ _).1 hval
  unfold validCore at hcore
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hcore
  exact height_step hB hcore.1.1.1.1.1.1 (hs.rooted _ hpar) hcore.1.1.1.1.2

/-- **The local chain on accepting a block** is in the extended tree, rooted, and no
lower than before. -/
theorem accept_cl (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    {ord : List ℕ → List ℕ} (hord : ∀ l, (ord l).Perm l) {now : ℕ} {B : Block}
    (hB : st B.hdr.id = some B) (hval : validHeader c st L O G s.tree s.bimm now B = true) {cl : ℕ}
    (hcl : cl = B.hdr.id ∧ B.hdr.parent = s.cloc ∨
      cl = forkChoice st .online c.k c.sGen s.cloc (ord (tips st (s.tree ++ [B.hdr.id])))) :
    cl ∈ s.tree ++ [B.hdr.id] ∧ Rooted st cl ∧ height st s.cloc ≤ height st cl := by
  have hT := accept_ok hs hB hval
  rcases hcl with ⟨rfl, hp⟩ | rfl
  · have hBr := (hT _ (List.mem_append_right _ (List.mem_singleton_self _))).1
    refine ⟨List.mem_append_right _ (List.mem_singleton_self _), hBr, ?_⟩
    have hpc := parent_mem_chainIds hS hBr
    rw [parentOf_eq hB, hp] at hpc
    exact (anc_height hS hBr hpc).2.1
  · unfold forkChoice
    have htips : ∀ f ∈ ord (tips st (s.tree ++ [B.hdr.id])), f ∈ s.tree ++ [B.hdr.id] :=
      fun f hf => List.mem_of_mem_filter ((hord _).mem_iff.1 hf)
    obtain ⟨h1, h2⟩ := fc_height hS c.k _ (fun f hf => (hT f (htips f hf)).1) s.cloc
      (hs.rooted _ hs.cloc)
    refine ⟨?_, h1, h2⟩
    rcases foldl_online_mem (st := st) c.k (ord (tips st (s.tree ++ [B.hdr.id]))) s.cloc with h | h
    · rw [h]; exact List.mem_append_left _ hs.cloc
    · exact htips _ h

/-! ## What `on_block` keeps -/

/-- **`on_block` keeps a node well formed and never lowers `c_loc`.** -/
theorem onBlock_ok (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ) (B : Block)
    (hB : st B.hdr.id = some B) :
    NodeOK c.k st L O G c (onBlock c st L O G fastPath ord now s B) ∧
      height st s.cloc ≤ height st (onBlock c st L O G fastPath ord now s B).cloc := by
  by_cases hacc : B.hdr.id ∉ s.tree ∧ validHeader c st L O G s.tree s.bimm now B = true
  · obtain ⟨cl, hcl, heq⟩ := onBlock_acc hs.rule fastPath ord hacc.1 hacc.2
    rw [heq]
    have hT := accept_ok hs hB hacc.2
    obtain ⟨hclT, hclr, hclh⟩ := accept_cl hS hs hord hB hacc.2 hcl
    have hbiC := blockAtDepth_mem hS hclr c.k
    have hbir := (anc_height hS hclr hbiC).1
    have hTr : ∀ y ∈ s.tree ++ [B.hdr.id], Rooted st y := fun y hy => (hT y hy).1
    refine ⟨⟨fun y hy => hTr y (List.mem_of_mem_filter hy),
      fun y hy => (hT y (List.mem_of_mem_filter hy)).2.2,
      prune_closed hS hTr (fun y hy => (hT y hy).2.1) hbir,
      mem_prune hS hTr hbir (List.mem_append_left _ hs.gen) (Or.inr (genesis_mem_chainIds hS hbir)),
      mem_prune hS hTr hbir hclT (Or.inl hbiC), rfl, hs.rule⟩, hclh⟩
  · rw [onBlock_ign hacc]; exact ⟨hs, le_rfl⟩

/-- `on_block` adds at most the processed block, and only if it is not from after `now`. -/
theorem onBlock_tree {s : NodeState} (hrule : s.rule = .online) (fastPath : Bool)
    (ord : List ℕ → List ℕ) (now : ℕ) {B : Block} (hB : st B.hdr.id = some B) :
    ∀ x ∈ (onBlock c st L O G fastPath ord now s B).tree,
      x ∈ s.tree ∨ (x = B.hdr.id ∧ slotOf st x ≤ now) := by
  by_cases hacc : B.hdr.id ∉ s.tree ∧ validHeader c st L O G s.tree s.bimm now B = true
  · obtain ⟨cl, -, heq⟩ := onBlock_acc hrule fastPath ord hacc.1 hacc.2
    rw [heq]
    intro x hx
    rcases List.mem_append.1 (List.mem_of_mem_filter hx) with h | h
    · exact Or.inl h
    · rw [List.mem_singleton] at h; subst h
      exact Or.inr ⟨rfl, by
        rw [slotOf_eq hB]; exact ((validHeader_iff c st L O G _ _ _ _).1 hacc.2).2.1⟩
  · rw [onBlock_ign hacc]; exact fun x hx => Or.inl hx

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
  set s' := onBlock c st L O G fastPath ord now s B
  have hcr := hs.rooted _ hs.cloc
  have hcr' := hok.1.rooted _ hok.1.cloc
  obtain ⟨-, hbm⟩ := hs.bimm_on_cloc hS
  -- the old `B_imm` is on the new local chain
  have hon : s.bimm ∈ chainIds st s'.cloc := by
    by_cases hacc : B.hdr.id ∉ s.tree ∧ validHeader c st L O G s.tree s.bimm now B = true
    · obtain ⟨cl, hcl, heq⟩ := onBlock_acc hs.rule fastPath ord hacc.1 hacc.2
      simp only [s', heq]
      have hT := accept_ok hs hB hacc.2
      rcases hcl with ⟨rfl, hp⟩ | rfl
      · -- the new block extends the local chain
        have hBr := (hT _ (List.mem_append_right _ (List.mem_singleton_self _))).1
        have hpc := parent_mem_chainIds hS hBr
        rw [parentOf_eq hB, hp] at hpc
        exact chainIds_trans hS hBr hpc hbm
      · unfold forkChoice
        have htips : ∀ f ∈ ord (tips st (s.tree ++ [B.hdr.id])), f ∈ s.tree ++ [B.hdr.id] :=
          fun f hf => List.mem_of_mem_filter ((hord _).mem_iff.1 hf)
        apply (fc_inv (st := st) (fun cl => Rooted st cl ∧ s.bimm ∈ chainIds st cl ∧
          height st s.cloc ≤ height st cl) c.k _ s.cloc ⟨hcr, hbm, le_rfl⟩ ?_).2.1
        intro cl f ⟨hclr, hclb, hclh⟩ hf hsw
        have hfr := (hT f (htips f hf)).1
        exact ⟨hfr, bimm_switch hS hs hclr hfr hclb hclh hsw,
          le_trans hclh (onlineStep_switch hS hclr hfr hsw).2.2.le⟩
    · simp only [s', onBlock_ign hacc]; exact hbm
  -- the new `B_imm` is at least as high, on the same chain
  obtain ⟨-, hnb⟩ := hok.1.bimm_on_cloc hS
  have hnh : height st s'.bimm = height st s'.cloc - c.k := by
    rw [hok.1.bimm]; exact blockAtDepth_height hS hcr' _
  have hoh : height st s.bimm = height st s.cloc - c.k := by
    rw [hs.bimm]; exact blockAtDepth_height hS hcr _
  exact chainIds_total hS hcr' hnb hon (by have := hok.2; omega)

/-! ## Processing blocks -/

/-- **A fold** keeps every property its steps keep. -/
theorem foldl_inv {α β : Type*} {P : α → Prop} {f : α → β → α} {l : List β}
    (h : ∀ a, P a → ∀ x ∈ l, P (f a x)) : ∀ a, P a → P (l.foldl f a) := by
  induction l with
  | nil => exact fun a ha => ha
  | cons x l ih =>
    intro a ha
    exact ih (fun a ha y hy => h a ha y (List.mem_cons_of_mem _ hy)) _ (h a ha x List.mem_cons_self)

/-- What processing blocks keeps at a node, with the clock at `now`: the node stays
well formed, adds only blocks not from after `now`, never lowers its local chain, and
its immutable block stays below the new one. -/
structure NodeStep (c : Config) (L : Ledger) (O : Oracle) (G : Genesis) (st : Store) (now : ℕ)
    (s s' : NodeState) : Prop where
  ok : NodeOK c.k st L O G c s'
  tree : ∀ x ∈ s'.tree, x ∈ s.tree ∨ slotOf st x ≤ now
  mono : height st s.cloc ≤ height st s'.cloc
  bimm : s.bimm ∈ chainIds st s'.bimm

theorem NodeStep.refl (hS : StoreOK st) {now : ℕ} {s : NodeState} (hs : NodeOK c.k st L O G c s) :
    NodeStep c L O G st now s s :=
  ⟨hs, fun _ h => Or.inl h, le_rfl, self_mem_chainIds hS (hs.bimm_on_cloc hS).1⟩

theorem NodeStep.trans (hS : StoreOK st) {now : ℕ} {s s' s'' : NodeState}
    (h1 : NodeStep c L O G st now s s') (h2 : NodeStep c L O G st now s' s'') :
    NodeStep c L O G st now s s'' :=
  ⟨h2.ok, fun x hx => (h2.tree x hx).elim (h1.tree x) Or.inr, h1.mono.trans h2.mono,
    chainIds_trans hS (h2.ok.bimm_on_cloc hS).1 h2.bimm h1.bimm⟩

theorem onBlock_step (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ) (B : Block)
    (hB : st B.hdr.id = some B) :
    NodeStep c L O G st now s (onBlock c st L O G fastPath ord now s B) :=
  ⟨(onBlock_ok hS hs fastPath ord hord now B hB).1,
    fun x hx => (onBlock_tree hs.rule fastPath ord now hB x hx).imp_right And.right,
    (onBlock_ok hS hs fastPath ord hord now B hB).2, onBlock_bimm hS hs fastPath ord hord now B hB⟩

/-- **Processing a list of stored blocks.** -/
theorem foldl_step (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ)
    {l : List Block} (hl : ∀ x ∈ l, st x.hdr.id = some x) :
    NodeStep c L O G st now s (l.foldl (onBlock c st L O G fastPath ord now) s) :=
  foldl_inv (P := NodeStep c L O G st now s) (fun _ h x hx =>
    h.trans hS (onBlock_step hS h.ok fastPath ord hord now x (hl x hx))) s (.refl hS hs)

/-- **`receive`.** -/
theorem receive_step (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now b : ℕ) :
    NodeStep c L O G st now s (receive c st L O G fastPath ord now s b) :=
  foldl_step hS hs fastPath ord hord now (fun _ hx => mem_chainUp hS hx)

end Cryptarchia
