import Cryptarchia.Proof.Maintenance
import Cryptarchia.Spec.Execution

/-!
# Structural invariants of executions

Facts that hold in every execution, whatever the lottery and the adversary:
the store only grows and stays well formed; every honest node's block tree
holds only rooted blocks that pass the node-independent validity checks, and is
closed under parents; `c_loc` is in the tree with `B_imm` its `k`-th ancestor;
and `c_loc` never loses height.
-/

namespace Cryptarchia

variable (c : Config) (st : Store) (L : Ledger) (O : Oracle) (G : Genesis)

/-- The part of `valid_header` that depends only on the block and the chain it
extends (steps 5, 9, 10, the uncle bound, execution), not on the validating node. -/
def validCore (B : Block) : Bool :=
  let par := B.hdr.parent
  decide (B.hdr.id ≠ genesisId) && decide (B.uncles.length ≤ c.maxUncles) &&
    decide (slotOf st par < B.hdr.slot) &&
    polValid c L O G (chainUp st par) (chainUp st par) B.hdr && genuine st B.hdr &&
    B.uncles.all (validUncle c st L O G par B.hdr.slot) &&
    L.execOK (chainUp st par ++ [B])

theorem validHeader_iff (T : List ℕ) (bimm now : ℕ) (B : Block) :
    validHeader c st L O G T bimm now B = true ↔
      validCore c st L O G B = true ∧ B.hdr.slot ≤ now ∧ B.hdr.parent ∈ T ∧
        height st bimm < height st B.hdr.parent + 1 := by
  unfold validHeader validCore
  simp only [Bool.and_eq_true, decide_eq_true_eq, List.contains_iff_mem]
  tauto

variable {c st L O G}

/-- A node's state is well formed. -/
structure NodeOK (k : ℕ) (st : Store) (L : Ledger) (O : Oracle) (G : Genesis) (c : Config)
    (s : NodeState) : Prop where
  rooted : ∀ x ∈ s.tree, Rooted st x
  valid : ∀ x ∈ s.tree, x = genesisId ∨ ∃ B, st x = some B ∧ validCore c st L O G B = true
  closed : ∀ x ∈ s.tree, parentOf st x ∈ s.tree
  gen : genesisId ∈ s.tree
  cloc : s.cloc ∈ s.tree
  bimm : s.bimm = blockAtDepth st s.cloc k
  rule : s.rule = .online

/-! ## Trees, tips and pruning -/

/-- The fork-choice result is the running choice or one of the forks. -/
theorem foldl_online_mem (k : ℕ) (forks : List ℕ) :
    ∀ c, forks.foldl (onlineStep st k) c = c ∨ forks.foldl (onlineStep st k) c ∈ forks := by
  induction forks with
  | nil => intro c; left; rfl
  | cons f fs ih =>
    intro c
    simp only [List.foldl_cons]
    rcases ih (onlineStep st k c f) with h | h
    · rw [h]
      rcases onlineStep_eq (st := st) k c f with h' | h'
      · left; exact h'
      · right; rw [h']; exact List.mem_cons_self
    · right; exact List.mem_cons_of_mem _ h

/-- A list element all of whose predecessors (and itself) differ from `d` is kept by
`takeWhile (· ≠ d)`. -/
theorem mem_takeWhile_of_idx : ∀ (l : List ℕ) (i y d : ℕ), l[i]? = some y →
    (∀ m ≤ i, l[m]? ≠ some d) → y ∈ l.takeWhile (fun z => z ≠ d) := by
  intro l
  induction l with
  | nil => intro i y d h; simp at h
  | cons a l ih =>
    intro i y d h hne
    have ha : a ≠ d := by
      intro had; exact hne 0 (Nat.zero_le _) (by simp [had])
    rw [List.takeWhile_cons_of_pos (by simpa using ha)]
    rcases i with _ | i
    · simp at h; subst h; exact List.mem_cons_self
    · apply List.mem_cons_of_mem
      exact ih i y d (by simpa using h) (fun m hm => by simpa using hne (m + 1) (by omega))

/-- A block with a height gap above an ancestor sits before it in the chain. -/
theorem mem_takeWhile_of_height (hS : StoreOK st) {t y d : ℕ} (ht : Rooted st t)
    (hy : y ∈ chainIds st t) (hd : d ∈ chainIds st t) (hlt : height st d < height st y) :
    y ∈ (chainIds st t).takeWhile (fun z => z ≠ d) := by
  obtain ⟨i, hi, hyi⟩ := (mem_chainIds hS ht).1 hy
  obtain ⟨j, hj, hdj⟩ := (mem_chainIds hS ht).1 hd
  have h1 := (height_iter hS ht i).2
  have h2 := (height_iter hS ht j).2
  rw [hyi] at h1; rw [hdj] at h2
  have hidx : ∀ m ≤ height st t, (chainIds st t)[m]? = some ((parentOf st)^[m] t) := by
    intro m hm
    rw [chainIds_eq hS ht, List.getElem?_map, List.getElem?_range (by omega)]; rfl
  apply mem_takeWhile_of_idx _ i y d (by rw [hidx i hi, hyi])
  intro m hm h
  rw [hidx m (by omega)] at h
  simp only [Option.some.injEq] at h
  have := (height_iter hS ht m).2
  rw [h] at this; omega

/-- **Every block of a tree lies below some tip.** -/
theorem exists_tip (hS : StoreOK st) {T : List ℕ} (hT : ∀ x ∈ T, Rooted st x) {y : ℕ} (hy : y ∈ T) :
    ∃ t ∈ tips st T, y ∈ chainIds st t := by
  classical
  let D := T.filter (fun x => y ∈ chainIds st x)
  have hD : D ≠ [] := by
    intro h
    have : y ∈ D := List.mem_filter.2 ⟨hy, by simpa using self_mem_chainIds hS (hT y hy)⟩
    rw [h] at this; simp at this
  obtain ⟨t, htD, htmax⟩ := D.toFinset.exists_max_image (height st)
    (by obtain ⟨z, hz⟩ := List.exists_mem_of_ne_nil D hD; exact ⟨z, List.mem_toFinset.2 hz⟩)
  rw [List.mem_toFinset] at htD
  have ⟨htT, hyt⟩ := List.mem_filter.1 htD
  refine ⟨t, ?_, by simpa using hyt⟩
  unfold tips
  rw [List.mem_filter]
  refine ⟨htT, ?_⟩
  simp only [Bool.not_eq_true', List.any_eq_false, decide_eq_true_eq, not_and]
  intro c hc hne hpar
  -- a child of `t` in `T` would be higher and still above `y`
  have hcr := hT c hc
  have hc0 : c ≠ genesisId := by
    intro h; subst h
    obtain ⟨g, hg, -, hgp⟩ := hS.gen
    rw [parentOf_eq hg, hgp] at hpar; exact hne hpar
  obtain ⟨blk, hbk, hpr, hsl⟩ := hcr.inv hc0
  rw [parentOf_eq hbk] at hpar
  have hh := height_step hbk hc0 hpr hsl
  rw [hpar] at hh
  have hyc : y ∈ chainIds st c := by
    have : chainIds st c = c :: chainIds st t := by
      unfold chainIds; rw [chain_step hbk hc0 hpr hsl, hpar]; simp [hS.idOK _ _ hbk]
    rw [this]; exact List.mem_cons_of_mem _ (by simpa using hyt)
  have := htmax c (List.mem_toFinset.2 (List.mem_filter.2 ⟨hc, by simpa using hyc⟩))
  omega

/-- A block removed by pruning is not comparable with the pruning point. -/
theorem not_cmp_of_pruned (hS : StoreOK st) {T : List ℕ} {B x : ℕ} (hT : ∀ y ∈ T, Rooted st y)
    (hB : Rooted st B) (hx : x ∈ T) (hxp : x ∉ pruneForks st T B) :
    B ∉ chainIds st x ∧ x ∉ chainIds st B := by
  constructor
  · intro h; exact hxp (mem_prune hS hT hB hx (Or.inl h))
  · intro h; exact hxp (mem_prune hS hT hB hx (Or.inr h))

/-- **Pruning keeps a tree closed under parents.** -/
theorem prune_closed (hS : StoreOK st) {T : List ℕ} {B : ℕ} (hT : ∀ y ∈ T, Rooted st y)
    (hcl : ∀ y ∈ T, parentOf st y ∈ T) (hB : Rooted st B) :
    ∀ y ∈ pruneForks st T B, parentOf st y ∈ pruneForks st T B := by
  intro y hyp
  have hy : y ∈ T := List.mem_of_mem_filter hyp
  by_contra hxp
  have hx := hcl y hy
  obtain ⟨hBx, hxB⟩ := not_cmp_of_pruned hS hT hB hx hxp
  have hyr := hT y hy
  have hy0 : y ≠ genesisId := by
    intro h; subst h
    obtain ⟨g, hg, -, hgp⟩ := hS.gen
    rw [parentOf_eq hg, hgp] at hxB
    exact hxB (genesis_mem_chainIds hS hB)
  obtain ⟨blk, hbk, hpr, hsl⟩ := hyr.inv hy0
  have hchain : chainIds st y = y :: chainIds st (parentOf st y) := by
    unfold chainIds; rw [chain_step hbk hy0 hpr hsl, parentOf_eq hbk]
    simp [hS.idOK _ _ hbk]
  -- `y` is removed by any tip above it
  obtain ⟨t, htip, hyt⟩ := exists_tip hS hT hy
  have ht := hT t (List.mem_of_mem_filter htip)
  have hxt : parentOf st y ∈ chainIds st t := chainIds_trans hS ht hyt (by rw [hchain]; exact List.mem_cons_of_mem _ (self_mem_chainIds hS (hT _ hx)))
  obtain ⟨hla, hlb, hlmax⟩ := lca_spec hS ht hB
  have hne : lca st t B ≠ B := by
    intro h
    rw [h] at hla
    rcases le_total (height st (parentOf st y)) (height st B) with hle | hle
    · exact hxB (chainIds_total hS ht hla hxt hle)
    · exact hBx (chainIds_total hS ht hxt hla hle)
  have hhx : height st (lca st t B) < height st (parentOf st y) := by
    by_contra hle
    push Not at hle
    exact hxB (chainIds_trans hS hB hlb (chainIds_total hS ht hla hxt hle))
  have hhy : height st (lca st t B) < height st y := by
    rw [height_step hbk hy0 hpr hsl, ← parentOf_eq hbk]; omega
  have hrem : y ∈ (chainIds st t).takeWhile (fun z => z ≠ lca st t B) :=
    mem_takeWhile_of_height hS ht hyt hla hhy
  apply (List.mem_filter.1 hyp).2 |> fun h => ?_
  simp only [Bool.not_eq_true'] at h
  simp at h
  exact h t htip hne (by simpa using hrem)

end Cryptarchia
