module

public import Cryptarchia.Proof.Structural
public import Cryptarchia.Proof.Bridge
import Cryptarchia.Proof.EpochCut
import Cryptarchia.Proof.Maintenance
public import Cryptarchia.Proof.NodeStep
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
import Mathlib.Tactic.ENatToNat
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
import Std.Tactic.BVDecide.Normalize.BitVec
import Std.Tactic.BVDecide.Normalize.Prop

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

@[expose] public section

namespace Cryptarchia

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}

/-- If `x` is on `c`'s chain at most `k` below `c`, then `c`'s `k`-th ancestor is
an ancestor of `x`. -/
theorem bimm_anc (hS : StoreOK st) {cl x k : ℕ} (hcl : Rooted st cl) (hx : x ∈ chainIds st cl)
    (hk : height st cl - height st x ≤ k) : blockAtDepth st cl k ∈ chainIds st x := by
  have hbm := blockAtDepth_mem hS hcl k
  have hbh := blockAtDepth_height hS hcl k
  exact chainIds_total hS hcl hx hbm (by omega)

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
  obtain ⟨cl, hcl, heq⟩ := onBlock_acc hs.rule fastPath ord hnew hval
  rw [heq]
  rcases hcl with ⟨rfl, -⟩ | rfl
  · exact le_rfl
  set T' := s.tree ++ [B.hdr.id] with hT'
  have hT := accept_ok hs hB hval
  have hT'r : ∀ y ∈ T', Rooted st y := fun y hy => (hT y hy).1
  have hT'good : ∀ y ∈ T', GoodAt c L O G st now y := by
    intro y hy
    refine ⟨hT'r y hy, ?_, fun x hx =>
      (hT x (chainIds_closed hS hT'r (fun z hz => (hT z hz).2.1) hy x hx)).2.2⟩
    rcases List.mem_append.1 hy with hy | hy
    · exact hsl y hy
    · rw [List.mem_singleton] at hy; subst hy; rw [slotOf_eq hB]
      exact ((validHeader_iff c st L O G _ _ _ _).1 hval).2.1
  -- the fork choice reaches `B`'s height
  unfold forkChoice
  simp only
  have htips : ∀ f ∈ ord (tips st T'), f ∈ T' := by
    intro f hf
    exact List.mem_of_mem_filter ((hord (tips st T')).mem_iff.1 hf)
  have hr : ∀ f ∈ ord (tips st T'), Rooted st f := fun f hf => hT'r f (htips f hf)
  obtain ⟨f₀, hf₀tip, hBf₀⟩ := exists_tip hS hT'r (List.mem_append_right _ (List.mem_singleton_self _))
  have hf₀ : f₀ ∈ ord (tips st T') := (hord _).mem_iff.2 hf₀tip
  have hf₀r := hr f₀ hf₀
  have hBle : height st B.hdr.id ≤ height st f₀ := (anc_height hS hf₀r hBf₀).2.1
  have hbm0 := (hs.bimm_on_cloc hS).2
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

/-- **A proposer adopts its own block** (or something higher): the block is one
above the local chain, so the fork-choice loop either switches to it or has
already moved higher. -/
theorem own_adopt (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ) (B : Block)
    (hB : st B.hdr.id = some B) (hpar : B.hdr.parent = s.cloc) (hnew : B.hdr.id ∉ s.tree)
    (hval : validHeader c st L O G s.tree s.bimm now B = true) :
    height st B.hdr.id ≤ height st (onBlock c st L O G fastPath ord now s B).cloc := by
  obtain ⟨cl, hcl, heq⟩ := onBlock_acc hs.rule fastPath ord hnew hval
  rw [heq]
  rcases hcl with ⟨rfl, -⟩ | rfl
  · exact le_rfl
  set T' := s.tree ++ [B.hdr.id]
  have hT := accept_ok hs hB hval
  have hcr := hs.rooted _ hs.cloc
  have hBr : Rooted st B.hdr.id := (hT _ (List.mem_append_right _ (List.mem_singleton_self _))).1
  have hBh := accept_height hs hB hval
  rw [hpar] at hBh
  have hT'r : ∀ y ∈ T', Rooted st y := fun y hy => (hT y hy).1
  unfold forkChoice; simp only
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
  exact fc_reaches hS P c.k (ord (tips st T')) hr hBf
    (by
      intro cl hP hclr hlt
      rcases hP.2 with rfl | hP'
      · -- the running choice is still the local chain, the parent of `B`
        have hin := parent_mem_chainIds hS hBr
        rw [parentOf_eq hB, hpar] at hin
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

/-- The fold invariant: a well-formed node, no block from the future, and a
local chain at least `H0` high. -/
def FoldInv (c : Config) (L : Ledger) (O : Oracle) (G : Genesis) (st : Store) (now H0 z : ℕ)
    (s : NodeState) : Prop :=
  NodeOK c.k st L O G c s ∧ (∀ x ∈ s.tree, slotOf st x ≤ now) ∧ H0 ≤ height st s.cloc ∧
    z ∈ chainIds st s.bimm

theorem onBlock_inv (hS : StoreOK st) {now H0 z : ℕ} {s : NodeState}
    (hs : FoldInv c L O G st now H0 z s) (fastPath : Bool) (ord : List ℕ → List ℕ)
    (hord : ∀ l, (ord l).Perm l) (B : Block) (hB : st B.hdr.id = some B) :
    FoldInv c L O G st now H0 z (onBlock c st L O G fastPath ord now s B) := by
  have h := onBlock_step hS hs.1 fastPath ord hord now B hB
  exact ⟨h.ok, fun x hx => (h.tree x hx).elim (hs.2.1 x) id, le_trans hs.2.2.1 h.mono,
    chainIds_trans hS (h.ok.bimm_on_cloc hS).1 h.bimm hs.2.2.2⟩

/-- Under `Near`, the node's immutable block is on `h`'s chain. -/
theorem bimm_on (hS : StoreOK st) {now H0 h z : ℕ} {s : NodeState} (hs : FoldInv c L O G st now H0 z s)
    (hhr : Rooted st h) (hnear : Near c L O G st now H0 h z) : s.bimm ∈ chainIds st h := by
  have hcr := hs.1.cloc_rooted
  have hbm := (hs.1.bimm_on_cloc hS).2
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
  by_cases hacc : B.hdr.id ∉ s.tree ∧ validHeader c st L O G s.tree s.bimm now B = true
  · obtain ⟨cl, hcl, heq⟩ := onBlock_acc hs.rule fastPath ord hacc.1 hacc.2
    rw [heq] at hcmp ⊢
    have hT := accept_ok hs hB hacc.2
    obtain ⟨-, hclr, -⟩ := accept_cl hS hs hord hB hacc.2 hcl
    apply mem_prune hS (fun y hy => (hT y hy).1) (anc_height hS hclr (blockAtDepth_mem hS hclr c.k)).1
      _ hcmp
    rcases hx with hx | ⟨rfl, -⟩
    · exact List.mem_append_left _ hx
    · exact List.mem_append_right _ (List.mem_singleton_self _)
  · rw [onBlock_ign hacc]
    rcases hx with hx | ⟨rfl, hv⟩
    · exact hx
    · by_contra hn; exact hacc ⟨hn, hv⟩

/-- Under `Near`, `on_block` keeps every block of `h`'s chain that the node holds or
accepts. -/
theorem onBlock_keep_on (hS : StoreOK st) {now H0 h z : ℕ} {s : NodeState}
    (hs : FoldInv c L O G st now H0 z s) (hhr : Rooted st h) (hnear : Near c L O G st now H0 h z)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (B : Block)
    (hB : st B.hdr.id = some B) {x : ℕ} (hxh : x ∈ chainIds st h)
    (hx : x ∈ s.tree ∨ (x = B.hdr.id ∧ validHeader c st L O G s.tree s.bimm now B = true)) :
    x ∈ (onBlock c st L O G fastPath ord now s B).tree := by
  have hbm := bimm_on hS (onBlock_inv hS hs fastPath ord hord B hB) hhr hnear
  refine onBlock_keep hS hs.1 fastPath ord hord now B hB hx ?_
  rcases le_total (height st x) (height st (onBlock c st L O G fastPath ord now s B).bimm) with hle | hle
  · exact Or.inr (chainIds_total hS hhr hbm hxh hle)
  · exact Or.inl (chainIds_total hS hhr hxh hbm hle)

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
  have hcr := hs.1.cloc_rooted
  have har := (anc_height hS hhr hah).1
  have hunfold : a ≠ genesisId := by
    intro h0; subst h0; exact hnew hs.1.gen
  obtain ⟨blk, hbk, hp, hsl⟩ := har.inv hunfold
  rw [hA] at hbk; cases hbk
  have hha : height st a = height st A.hdr.parent + 1 := height_step hA hunfold hp hsl
  have hab : a ∈ chainIds st s.bimm := chainIds_total hS hhr hbm hah (by omega)
  have hbc := (hs.1.bimm_on_cloc hS).2
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
    rw [onBlock_ign (fun h => h.1 (hid ▸ hs.1.gen))]
    refine ⟨hs, ?_, fun x hx => Or.inl hx⟩
    intro x hx
    unfold chainIds at hx; rw [chain_genesis hg hs0] at hx
    simp [hid] at hx; subst hx; exact hs.1.gen
  | step a A hA hne hpar hslot ih =>
    intro hah s hs
    have hid := hS.idOK _ _ hA
    have har : Rooted st a := Rooted.step a A hA hne hpar hslot
    have hpc := parent_mem_chainIds hS har
    rw [parentOf_eq hA] at hpc
    have hph : A.hdr.parent ∈ chainIds st h := chainIds_trans hS hhr hah hpc
    obtain ⟨hi1, hi2, hi3⟩ := ih hph s hs
    rw [chainUp_step hA hne hpar hslot, List.foldl_append]
    simp only [List.foldl_cons, List.foldl_nil]
    set sp := (chainUp st A.hdr.parent).foldl (onBlock c st L O G fastPath ord now) s
    have hA' : st A.hdr.id = some A := by rw [hid]; exact hA
    have hinv := onBlock_inv hS hi1 fastPath ord hord A hA'
    have hchainA := chainIds_step hS hA hne hpar hslot
    refine ⟨hinv, ?_, ?_⟩
    · -- every block of `a`'s chain is kept or added
      have hkeep : ∀ x ∈ chainIds st a, x ∈ sp.tree ∨ x = a →
          x ∈ (onBlock c st L O G fastPath ord now sp A).tree := by
        intro x hxa hx
        refine onBlock_keep_on hS hi1 hhr hnear fastPath ord hord A hA' (chainIds_trans hS hhr hah hxa) ?_
        rcases hx with hx | rfl
        · exact Or.inl hx
        -- `a` itself: kept if present, otherwise accepted
        by_cases hin : x ∈ sp.tree
        · exact Or.inl hin
        · have hvalA : validCore c st L O G A = true := by
            rcases hvalh x hah with h0 | ⟨A', hA'', hv⟩
            · exact absurd h0 hne
            · rw [hA] at hA''; cases hA''; exact hv
          exact Or.inr ⟨hid.symm, accept_on_chain hS hi1 hhr hnear hah hslh hA hvalA hin
            (hi2 _ (self_mem_chainIds hS hpar))⟩
      intro x hx
      rw [hchainA, List.mem_cons] at hx
      rcases hx with rfl | hx
      · exact hkeep x (self_mem_chainIds hS har) (Or.inr rfl)
      · exact hkeep x (by rw [hchainA]; exact List.mem_cons_of_mem _ hx) (Or.inl (hi2 x hx))
    · intro x hx
      rcases onBlock_tree hi1.1.rule fastPath ord now hA' x hx with hx | hx
      · rcases hi3 x hx with h1 | h1
        · exact Or.inl h1
        · right; rw [hchainA]; exact List.mem_cons_of_mem _ h1
      · right; rw [hx.1, hid]; exact self_mem_chainIds hS har

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
    exact mem_chainUp hS this
  -- the rest keeps `h`'s chain and never lowers the local chain
  obtain ⟨-, hr1, hr2⟩ := foldl_inv (l := R) (P := fun s₀ => FoldInv c L O G st now H0 z s₀ ∧
      (∀ x ∈ chainIds st h, x ∈ s₀.tree) ∧ height st sh.cloc ≤ height st s₀.cloc)
    (fun s₀ ⟨hs₀, hin, hle⟩ B hB => ⟨onBlock_inv hS hs₀ fastPath ord hord B (hRst B hB),
      fun x hx => onBlock_keep_on hS hs₀ hhr hnear fastPath ord hord B (hRst B hB) hx (Or.inl (hin x hx)),
      hle.trans (onBlock_ok hS hs₀.1 fastPath ord hord now B (hRst B hB)).2⟩) sh ⟨hf1, hf2, le_rfl⟩
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
  have hpc := parent_mem_chainIds hS hhr
  rw [parentOf_eq hH] at hpc
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

/-- A block added by `on_block` passed validation. -/
theorem onBlock_added_valid {s : NodeState} (fastPath : Bool) (ord : List ℕ → List ℕ) (now : ℕ)
    (B : Block) (hnew : B.hdr.id ∉ s.tree)
    (hin : B.hdr.id ∈ (onBlock c st L O G fastPath ord now s B).tree) :
    validHeader c st L O G s.tree s.bimm now B = true := by
  by_contra hv
  rw [onBlock_ign (fun h => hv h.2)] at hin; exact hnew hin

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
        height st s'.cloc ≤ height st (bs.foldl (onBlock c st L O G fastPath ord now) s').cloc :=
      fun s' hs' => (foldl_step hS hs'.1 fastPath ord hord now
        (fun x hx => hst x (List.mem_cons_of_mem _ hx))).mono
    by_cases hh : h ∈ (onBlock c st L O G fastPath ord now s B).tree
    · -- `h` was added in this step
      rcases onBlock_tree hs.1.rule fastPath ord now hB h hh with h1 | ⟨rfl, -⟩
      · exact absurd h1 hn
      · have hval := onBlock_added_valid fastPath ord now B hn hh
        have := claimA hS hs.1 fastPath ord hord now B hB hs.2.1 hn hval hs.2.2.2 (hnear.mono hs.2.2.1)
        exact le_trans this (hmono _ hinv)
    · exact ih (fun x hx => hst x (List.mem_cons_of_mem _ hx)) _ hinv hh hin

end Cryptarchia
