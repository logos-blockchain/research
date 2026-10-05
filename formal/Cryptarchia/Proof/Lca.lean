import Cryptarchia.Proof.Chains

/-!
# Ancestry and latest common ancestors in the block store

For rooted blocks in a well-formed store, `chainIds b` is the list
`b, parent b, parent² b, …, genesis`; `isAncestor` is membership in it; and `lca`
is the deepest common ancestor.
-/

namespace Cryptarchia

variable {st : Store}

/-- A well-formed store: blocks are filed under their own IDs, and genesis is
stored, at slot 0, as its own parent. -/
structure StoreOK (st : Store) : Prop where
  idOK : IdOK st
  gen : ∃ g, st genesisId = some g ∧ g.hdr.slot = 0 ∧ g.hdr.parent = genesisId

theorem StoreOK.genSelf (h : StoreOK st) : GenSelf st := by
  intro g hg
  obtain ⟨g', hg', -, hp⟩ := h.gen
  rw [hg] at hg'; cases hg'; exact hp

theorem StoreOK.rooted_gen (h : StoreOK st) : Rooted st genesisId := by
  obtain ⟨g, hg, hs, -⟩ := h.gen
  exact Rooted.gen g hg hs

/-- The chain as the iterated parent. -/
theorem chainIds_eq (hS : StoreOK st) {b : ℕ} (hb : Rooted st b) :
    chainIds st b = (List.range (height st b + 1)).map (fun j => (parentOf st)^[j] b) := by
  induction hb with
  | gen g hg hs =>
    unfold chainIds
    rw [chain_genesis hg hs]
    simp [height, chain_genesis hg hs, hS.idOK _ _ hg]
  | step b blk hbk hne hpar hslot ih =>
    unfold chainIds at ih ⊢
    rw [chain_step hbk hne hpar hslot, height_step hbk hne hpar hslot, List.range_succ_eq_map]
    simp only [List.map_cons, List.map_map, Function.iterate_zero_apply]
    rw [hS.idOK _ _ hbk, ih]
    congr 1
    apply List.map_congr_left
    intro j _
    simp only [Function.comp_apply, Function.iterate_succ_apply, parentOf_eq hbk]

theorem height_iter (hS : StoreOK st) {b : ℕ} (hb : Rooted st b) (j : ℕ) :
    Rooted st ((parentOf st)^[j] b) ∧ height st ((parentOf st)^[j] b) = height st b - j := by
  induction j generalizing b with
  | zero => simpa using hb
  | succ j ih =>
    rw [Function.iterate_succ_apply]
    have hp := hb.parent_rooted hS.genSelf
    obtain ⟨h1, h2⟩ := ih hp
    refine ⟨h1, ?_⟩
    rw [h2]
    rcases eq_or_ne b genesisId with hg | hg
    · subst hg
      obtain ⟨g, hgs, -, hgp⟩ := hS.gen
      rw [parentOf_eq hgs, hgp]
      have : height st genesisId = 0 := by
        obtain ⟨g, hgs, hs, -⟩ := hS.gen
        simp [height, chain_genesis hgs hs]
      omega
    · obtain ⟨blk, hbk, hpar, hslot⟩ := hb.inv hg
      rw [parentOf_eq hbk, height_step hbk hg hpar hslot]
      omega

theorem mem_chainIds (hS : StoreOK st) {a b : ℕ} (hb : Rooted st b) :
    a ∈ chainIds st b ↔ ∃ j ≤ height st b, (parentOf st)^[j] b = a := by
  rw [chainIds_eq hS hb]
  simp only [List.mem_map, List.mem_range]
  constructor
  · rintro ⟨j, hj, rfl⟩; exact ⟨j, by omega, rfl⟩
  · rintro ⟨j, hj, rfl⟩; exact ⟨j, by omega, rfl⟩

/-- An ancestor at a given height is determined. -/
theorem anc_height (hS : StoreOK st) {a b : ℕ} (hb : Rooted st b) (ha : a ∈ chainIds st b) :
    Rooted st a ∧ height st a ≤ height st b ∧ (parentOf st)^[height st b - height st a] b = a := by
  obtain ⟨j, hj, rfl⟩ := (mem_chainIds hS hb).1 ha
  obtain ⟨h1, h2⟩ := height_iter hS hb j
  refine ⟨h1, by omega, ?_⟩
  rw [h2]; congr 1; omega

theorem self_mem_chainIds (hS : StoreOK st) {b : ℕ} (hb : Rooted st b) : b ∈ chainIds st b :=
  (mem_chainIds hS hb).2 ⟨0, Nat.zero_le _, rfl⟩

theorem genesis_mem_chainIds (hS : StoreOK st) {b : ℕ} (hb : Rooted st b) :
    genesisId ∈ chainIds st b := by
  rw [mem_chainIds hS hb]
  refine ⟨height st b, le_rfl, ?_⟩
  obtain ⟨h1, h2⟩ := height_iter hS hb (height st b)
  -- the only rooted block of height 0 is genesis
  have : ∀ x, Rooted st x → height st x = 0 → x = genesisId := by
    intro x hx hx0
    by_contra hne
    obtain ⟨blk, hbk, hpar, hslot⟩ := hx.inv hne
    rw [height_step hbk hne hpar hslot] at hx0; omega
  exact this _ h1 (by rw [h2]; simp)

/-- Ancestry is transitive. -/
theorem chainIds_trans (hS : StoreOK st) {a x b : ℕ} (hb : Rooted st b) (hx : x ∈ chainIds st b)
    (ha : a ∈ chainIds st x) : a ∈ chainIds st b := by
  obtain ⟨hxr, hxb, hxe⟩ := anc_height hS hb hx
  obtain ⟨i, hi, rfl⟩ := (mem_chainIds hS hxr).1 ha
  rw [mem_chainIds hS hb]
  refine ⟨i + (height st b - height st x), by omega, ?_⟩
  rw [Function.iterate_add_apply, hxe]

/-- Two ancestors of one block: the shallower one is an ancestor of the deeper. -/
theorem chainIds_total (hS : StoreOK st) {x y b : ℕ} (hb : Rooted st b) (hx : x ∈ chainIds st b)
    (hy : y ∈ chainIds st b) (hxy : height st y ≤ height st x) : y ∈ chainIds st x := by
  obtain ⟨hxr, hxb, hxe⟩ := anc_height hS hb hx
  obtain ⟨hyr, hyb, hye⟩ := anc_height hS hb hy
  rw [mem_chainIds hS hxr]
  refine ⟨height st x - height st y, by omega, ?_⟩
  have e : height st x - height st y + (height st b - height st x) = height st b - height st y := by
    omega
  have := hye
  rw [← e, Function.iterate_add_apply, hxe] at this
  exact this

/-- A block's chain, the IDs, contains no ID twice. -/
theorem chainIds_nodup (hS : StoreOK st) {b : ℕ} (hb : Rooted st b) : (chainIds st b).Nodup := by
  rw [chainIds_eq hS hb, List.nodup_map_iff_inj_on (List.nodup_range)]
  intro i hi j hj hij
  simp only [List.mem_range] at hi hj
  have h1 := (height_iter hS hb i).2
  have h2 := (height_iter hS hb j).2
  rw [hij] at h1
  omega

/-- **`lca` is the deepest common ancestor.** For rooted `a`, `b`: `lca a b` is
on both chains, and every common ancestor is an ancestor of it. -/
theorem lca_spec (hS : StoreOK st) {a b : ℕ} (ha : Rooted st a) (hb : Rooted st b) :
    lca st a b ∈ chainIds st a ∧ lca st a b ∈ chainIds st b ∧
      ∀ x, x ∈ chainIds st a → x ∈ chainIds st b → x ∈ chainIds st (lca st a b) := by
  have hex : ∃ x ∈ chainIds st a, (chainIds st b).contains x = true :=
    ⟨genesisId, genesis_mem_chainIds hS ha, by simpa using genesis_mem_chainIds hS hb⟩
  obtain ⟨y, hy⟩ := List.find?_isSome.2 hex |> Option.isSome_iff_exists.1
  have hlca : lca st a b = y := by unfold lca; rw [hy]; rfl
  have hya := List.mem_of_find?_eq_some hy
  have hyb : y ∈ chainIds st b := by simpa using List.find?_some hy
  rw [hlca]
  refine ⟨hya, hyb, ?_⟩
  intro x hxa hxb
  -- `x` is at or after `y` in `a`'s chain (tip first), i.e. no deeper
  apply chainIds_total hS ha hya hxa
  rw [chainIds_eq hS ha] at hy
  rw [List.find?_eq_some_iff_append] at hy
  obtain ⟨-, l₁, l₂, hsplit, hbefore⟩ := hy
  set f := fun j => (parentOf st)^[j] a with hf
  have hlen : (List.map f (List.range (height st a + 1))).length = l₁.length + 1 + l₂.length := by
    rw [hsplit]; simp; omega
  simp only [List.length_map, List.length_range] at hlen
  -- `y` sits at index `l₁.length`
  have hyidx : f l₁.length = y := by
    have : (List.map f (List.range (height st a + 1)))[l₁.length]? = some y := by
      rw [hsplit]; simp
    rw [List.getElem?_map, List.getElem?_range (by omega)] at this
    simpa using this
  obtain ⟨i, hi, hxi⟩ := (mem_chainIds hS ha).1 hxa
  -- `x` is not before `y` in the list
  have hil : l₁.length ≤ i := by
    by_contra hlt
    push Not at hlt
    have hxl : x ∈ l₁ := by
      have : (List.map f (List.range (height st a + 1)))[i]? = some x := by
        rw [List.getElem?_map, List.getElem?_range (by omega)]; simp [hf, hxi]
      rw [hsplit, List.getElem?_append_left hlt] at this
      exact List.mem_of_getElem? this
    have := hbefore x hxl
    simp at this
    exact this hxb
  have h1 := (height_iter hS ha i).2
  have h2 := (height_iter hS ha l₁.length).2
  rw [hxi] at h1
  rw [show (parentOf st)^[l₁.length] a = y from hyidx] at h2
  omega

end Cryptarchia
