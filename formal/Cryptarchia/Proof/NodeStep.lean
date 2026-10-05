import Cryptarchia.Proof.Structural

/-!
# `on_block` and `receive` preserve well-formedness

`onBlock_ok`: processing a stored block keeps a node well formed and never
lowers the height of its local chain, whichever reading of `on_block` (with or
without the shortcut) and whichever tip order.
-/

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

theorem mem_chainUp_store (hS : StoreOK st) {b : ℕ} {x : Block} (h : x ∈ chainUp st b) :
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

/-- **`on_block` keeps a node well formed and never lowers `c_loc`.** -/
theorem onBlock_ok (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now : ℕ) (B : Block)
    (hB : st B.hdr.id = some B) :
    NodeOK c.k st L O G c (onBlock c st L O G fastPath ord now s B) ∧
      height st s.cloc ≤ height st (onBlock c st L O G fastPath ord now s B).cloc := by
  unfold onBlock
  split
  · exact ⟨hs, le_rfl⟩
  rename_i hacc
  rw [hs.rule]
  simp only
  simp only [Bool.or_eq_true, not_or, Bool.not_eq_true, Bool.not_eq_eq_eq_not, Bool.not_true] at hacc
  obtain ⟨hnew, hval⟩ := hacc
  have hval' : validHeader c st L O G s.tree s.bimm now B = true := by simpa using hval
  obtain ⟨hcore, -, hpar, -⟩ := (validHeader_iff c st L O G _ _ _ _).1 hval'
  have hcore' := hcore
  unfold validCore at hcore'
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hcore'
  obtain ⟨⟨⟨⟨⟨⟨hne, -⟩, hslot⟩, -⟩, -⟩, -⟩, -⟩ := hcore'
  have hBr : Rooted st B.hdr.id := Rooted.step B.hdr.id B hB hne (hs.rooted _ hpar) hslot
  set T' := s.tree ++ [B.hdr.id] with hT'
  have hT'r : ∀ y ∈ T', Rooted st y := by
    intro y hy; rw [List.mem_append] at hy
    rcases hy with hy | hy
    · exact hs.rooted y hy
    · simp at hy; subst hy; exact hBr
  have hT'cl : ∀ y ∈ T', parentOf st y ∈ T' := by
    intro y hy; rw [List.mem_append] at hy
    rcases hy with hy | hy
    · exact List.mem_append_left _ (hs.closed y hy)
    · simp at hy; subst hy; rw [parentOf_eq hB]; exact List.mem_append_left _ hpar
  have hT'v : ∀ x ∈ T', x = genesisId ∨ ∃ B', st x = some B' ∧ validCore c st L O G B' = true := by
    intro y hy; rw [List.mem_append] at hy
    rcases hy with hy | hy
    · exact hs.valid y hy
    · simp at hy; subst hy; exact Or.inr ⟨B, hB, hcore⟩
  -- the new local chain
  set cl := (if fastPath && B.hdr.parent = s.cloc then B.hdr.id
      else forkChoice st .online c.k c.sGen s.cloc (ord (tips st T'))) with hcl
  have htips : ∀ f ∈ ord (tips st T'), f ∈ T' := by
    intro f hf
    have := (hord (tips st T')).mem_iff.1 hf
    exact List.mem_of_mem_filter this
  have hcl_mem : cl ∈ T' ∧ Rooted st cl ∧ height st s.cloc ≤ height st cl := by
    rw [hcl]
    split
    · rename_i hfp
      simp only [Bool.and_eq_true, decide_eq_true_eq] at hfp
      refine ⟨List.mem_append_right _ (by simp), hBr, ?_⟩
      obtain ⟨-, hp⟩ := hfp
      rw [height_step hB hne (hs.rooted _ hpar) hslot, hp]; omega
    · unfold forkChoice
      simp only
      have hr : ∀ f ∈ ord (tips st T'), Rooted st f := fun f hf => hT'r f (htips f hf)
      obtain ⟨h1, h2⟩ := fc_height hS c.k _ hr s.cloc (hs.rooted _ hs.cloc)
      refine ⟨?_, h1, h2⟩
      rcases foldl_online_mem (st := st) c.k (ord (tips st T')) s.cloc with h | h
      · rw [h]; exact List.mem_append_left _ hs.cloc
      · exact htips _ h
  obtain ⟨hclT, hclr, hclh⟩ := hcl_mem
  set bi := blockAtDepth st cl c.k with hbi
  have hbiC : bi ∈ chainIds st cl := blockAtDepth_mem hS hclr c.k
  have hbir : Rooted st bi := (anc_height hS hclr hbiC).1
  refine ⟨⟨?_, ?_, ?_, ?_, ?_, rfl, rfl⟩, hclh⟩
  · intro y hy; exact hT'r y (List.mem_of_mem_filter hy)
  · intro y hy; exact hT'v y (List.mem_of_mem_filter hy)
  · exact prune_closed hS hT'r hT'cl hbir
  · exact mem_prune hS hT'r hbir (List.mem_append_left _ hs.gen)
      (Or.inr (genesis_mem_chainIds hS hbir))
  · exact mem_prune hS hT'r hbir hclT (Or.inl hbiC)

/-- **`receive` keeps a node well formed and never lowers `c_loc`.** -/
theorem receive_ok (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    (fastPath : Bool) (ord : List ℕ → List ℕ) (hord : ∀ l, (ord l).Perm l) (now b : ℕ) :
    NodeOK c.k st L O G c (receive c st L O G fastPath ord now s b) ∧
      height st s.cloc ≤ height st (receive c st L O G fastPath ord now s b).cloc := by
  unfold receive
  have key : ∀ (l : List Block), (∀ x ∈ l, st x.hdr.id = some x) → ∀ s, NodeOK c.k st L O G c s →
      NodeOK c.k st L O G c (l.foldl (onBlock c st L O G fastPath ord now) s) ∧
        height st s.cloc ≤ height st (l.foldl (onBlock c st L O G fastPath ord now) s).cloc := by
    intro l
    induction l with
    | nil => intro _ s hs; exact ⟨hs, le_rfl⟩
    | cons x xs ih =>
      intro hx s hs
      simp only [List.foldl_cons]
      obtain ⟨h1, h2⟩ := onBlock_ok hS hs fastPath ord hord now x (hx x List.mem_cons_self)
      obtain ⟨h3, h4⟩ := ih (fun y hy => hx y (List.mem_cons_of_mem _ hy)) _ h1
      exact ⟨h3, le_trans h2 h4⟩
  exact key _ (fun x hx => mem_chainUp_store hS hx) s hs

end Cryptarchia
