import Cryptarchia.Proof.Bridge

/-!
# Honest proposals are valid

Within the first epoch every chain derives the genesis epoch state, so a block
valid on its own chain is valid on any chain it is carried by (as an uncle). An
honest node's proposal therefore passes every node-independent check: its Proof
of Leadership is the one the node computed, its uncles are blocks the node had
accepted, and its transactions execute (an assumption on the ledger: the honest
payload always executes).
-/

namespace Cryptarchia

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}

theorem chainUp_ids (hS : StoreOK st) {b : ℕ} (hb : Rooted st b) :
    (chainUp st b).map (·.hdr.id) = (chainIds st b).reverse := by
  unfold chainUp chainIds; rw [List.map_reverse]

theorem mem_chainUp (hS : StoreOK st) {b : ℕ} {x : Block} (hx : x ∈ chainUp st b) :
    st x.hdr.id = some x := mem_chainUp_store hS hx

/-- On a rooted chain, the only block with the genesis ID is the genesis block. -/
theorem prefixBelow_zero (hS : StoreOK st) {b : ℕ} (hb : Rooted st b) {g : Block}
    (hg : st genesisId = some g) : prefixBelow (chainUp st b) 0 = [g] := by
  unfold prefixBelow
  have hfil : (chainUp st b).filter (fun x => x.hdr.id = genesisId ∨ x.hdr.slot < 0) =
      (chainUp st b).filter (fun x => x.hdr.id = genesisId) := by
    apply List.filter_congr; intro x _; simp
  rw [hfil]
  -- every such block is `g`, and there is exactly one
  have hall : ∀ x ∈ (chainUp st b).filter (fun x => x.hdr.id = genesisId), x = g := by
    intro x hx
    rw [List.mem_filter] at hx
    have := mem_chainUp hS hx.1
    simp only [decide_eq_true_eq] at hx
    rw [hx.2, hg] at this; exact (Option.some_inj.1 this).symm
  have hlen : ((chainUp st b).filter (fun x => x.hdr.id = genesisId)).length = 1 := by
    have hc : ((chainUp st b).map (·.hdr.id)).count genesisId = 1 := by
      rw [chainUp_ids hS hb, List.count_reverse]
      exact List.count_eq_one_of_mem (chainIds_nodup hS hb) (genesis_mem_chainIds hS hb)
    rw [List.count, List.countP_map, List.countP_eq_length_filter] at hc
    rw [← hc]
    congr 1
  obtain ⟨y, hy⟩ := List.length_eq_one_iff.1 hlen
  rw [hy]
  have := hall y (by rw [hy]; exact List.mem_singleton_self y)
  rw [this]

/-- **Every chain derives the genesis epoch state for the first epoch.** -/
theorem epochState_zero (hS : StoreOK st) {a b : ℕ} (ha : Rooted st a) (hb : Rooted st b) :
    epochState c L O G (chainUp st a) 0 = epochState c L O G (chainUp st b) 0 := by
  obtain ⟨g, hg, -, -⟩ := hS.gen
  unfold epochState
  have he : c.epochStart 0 = 0 := by simp [Config.epochStart]
  simp only [he, Nat.zero_sub, prefixBelow_zero hS ha hg, prefixBelow_zero hS hb hg]

/-- Within the first epoch, Proof-of-Leadership validity does not depend on the
chain the epoch state is derived on. -/
theorem polValid_zero (hS : StoreOK st) {a b : ℕ} (ha : Rooted st a) (hb : Rooted st b)
    (P : List Block) (h : Header) (h0 : c.epochOf h.slot = 0) :
    polValid c L O G (chainUp st a) P h = polValid c L O G (chainUp st b) P h := by
  unfold polValid; rw [h0, epochState_zero hS ha hb]

theorem selectUncles_length (T : List ℕ) (cloc sl : ℕ) :
    (selectUncles c st T cloc sl).length ≤ c.maxUncles := by
  unfold selectUncles
  simp only
  generalize (List.mergeSort _ _) = l
  have : ∀ (l : List Header) (acc : List Header), acc.length ≤ c.maxUncles →
      (l.foldl (fun (acc : List Header) U =>
        if acc.length < c.maxUncles && !(acc.map (·.slot)).contains U.slot then acc ++ [U] else acc)
        acc).length ≤ c.maxUncles := by
    intro l
    induction l with
    | nil => intro acc h; exact h
    | cons U us ih =>
      intro acc h
      simp only [List.foldl_cons]
      apply ih
      split
      · rename_i hc; simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
        simp; omega
      · exact h
  exact this l [] (by simp)

theorem mem_selectUncles {T : List ℕ} {cloc sl : ℕ} {U : Header}
    (hU : U ∈ selectUncles c st T cloc sl) :
    ∃ x ∈ T, ∃ blk, st x = some blk ∧ blk.hdr = U ∧ (chainIds st cloc).contains U.parent = true ∧
      (chainIds st cloc).contains U.id = false ∧ U.slot < sl ∧ sl - slotOf st U.parent ≤ c.uncleWindow := by
  unfold selectUncles at hU
  simp only at hU
  -- the picked uncles are among the sorted candidates
  have hsub : ∀ (l : List Header) (acc : List Header), ∀ U ∈ l.foldl (fun (acc : List Header) U =>
      if acc.length < c.maxUncles && !(acc.map (·.slot)).contains U.slot then acc ++ [U] else acc) acc,
      U ∈ acc ∨ U ∈ l := by
    intro l
    induction l with
    | nil => intro acc U h; exact Or.inl h
    | cons V vs ih =>
      intro acc U h
      simp only [List.foldl_cons] at h
      rcases ih _ U h with h | h
      · split at h
        · rcases List.mem_append.1 h with h | h
          · exact Or.inl h
          · simp at h; subst h; exact Or.inr List.mem_cons_self
        · exact Or.inl h
      · exact Or.inr (List.mem_cons_of_mem _ h)
  rcases hsub _ [] U hU with h | h
  · simp at h
  rw [List.mem_mergeSort] at h
  rw [List.mem_filter] at h
  obtain ⟨hmem, hcond⟩ := h
  simp only [Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at hcond
  obtain ⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, -⟩ := hcond
  rw [List.mem_map] at hmem
  obtain ⟨blk, hblk, rfl⟩ := hmem
  rw [List.mem_filterMap] at hblk
  obtain ⟨x, hx, hxb⟩ := hblk
  exact ⟨x, hx, blk, hxb, rfl, h1, h2, h3, h4⟩

end Cryptarchia
