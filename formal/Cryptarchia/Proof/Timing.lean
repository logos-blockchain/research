module

public import Cryptarchia.Proof.EpochCut
public import Cryptarchia.Proof.WorldStep
import Std.Tactic.BVDecide.Normalize.BitVec
import Mathlib.Algebra.Order.Floor.Extended

/-!
# Honest proposals and the assumptions

An honest node's proposal passes every node-independent check (`propose_valid`), in
every epoch for sane parameters: its Proof of Leadership is the one the node
computed, its uncles are blocks the node had accepted (valid on their own chains,
hence on the proposal's, `polValid_common`), and its payload executes (an
assumption on the ledger, `HonestExec`). It passes the proposer's own validation
(`propose_header`). `Assm` collects the assumptions on the environment.
-/

@[expose] public section

namespace Cryptarchia

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}

/-- The ledger executes honest blocks' payloads. -/
def HonestExec (L : Ledger) : Prop :=
  ∀ C (B : Block) i, B.hdr.signer = .honest i → L.execOK (C ++ [B]) = true

/-- Honest stakers never spend their notes: an honest note in the ledger after
the part of a chain below some slot is still in the ledger after the whole chain. -/
def HonestStake (L : Ledger) : Prop :=
  ∀ (C : List Block) (s : ℕ) (n : Note), (∃ j, n.owner = .honest j) →
    n ∈ L.notes (prefixBelow C s) → n ∈ L.notes C

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

/-- The assumptions on the environment. (There is no delivery assumption: an
honest block the network fails to deliver within `Δ` is `Late` and counts as
adversarial in the settlement tree.) -/
structure Assm (E : Env) : Prop where
  ord : E.OrderOK
  crash : ∀ i t t', t ≤ t' → E.online i t' = true → E.online i t = true
  exec : HonestExec E.L
  nodup : E.nodes.Nodup
  sane : E.c.Sane
  stake : HonestStake E.L

/-- **An honest proposal is valid.** -/
theorem propose_valid (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    {i t newId : ℕ} {B : Block} (hB : propose c st L O G i t newId s = some B)
    (hslots : ∀ x ∈ s.tree, slotOf st x < t) (hc : c.Sane) (hexec : HonestExec L)
    {st' : Store} (hext : StoreExt st st') (hst' : st' B.hdr.id = some B)
    (hne : newId ≠ genesisId) :
    validCore c st' L O G B = true := by
  obtain ⟨hid, hsig, hpar, hsl⟩ := propose_id hB
  have hcr : Rooted st s.cloc := hs.rooted _ hs.cloc
  have hcr' : Rooted st' s.cloc := hcr.mono hext
  unfold propose at hB
  split at hB
  · simp at hB
  split at hB
  · simp at hB
  rename_i n ns hwin
  simp only [Option.some.injEq] at hB
  subst hB
  have hn : n ∈ winningNotes c st L O G i s.cloc t := by rw [hwin]; exact List.mem_cons_self
  unfold winningNotes at hn
  simp only [List.mem_filter, Bool.and_eq_true, decide_eq_true_eq] at hn
  obtain ⟨hnl, ⟨hno, hnc⟩, hnw⟩ := hn
  unfold validCore
  simp only [Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true]
  refine ⟨⟨⟨⟨⟨⟨hne, ?_⟩, ?_⟩, ?_⟩, ?_⟩, ?_⟩, ?_⟩
  · exact selectUncles_length _ _ _
  · rw [slotOf_ext hext hcr.exists_blk]; exact hslots _ hs.cloc
  · -- the Proof of Leadership the node computed
    rw [chainUp_ext hext hcr]
    unfold polValid
    simp only [List.any_eq_true, decide_eq_true_eq]
    exact ⟨n, hnl, rfl, hno, by simpa using hnc, by simpa using hnw⟩
  · unfold genuine; rw [hst']; simp
  · intro U hU
    obtain ⟨x, hx, blk, hxb, hbU, hc1, hc2, hc3, hc4⟩ := mem_selectUncles hU
    subst hbU
    have hx0 : x ≠ genesisId := by
      intro h; subst h
      have hid0 := hS.idOK _ _ hxb
      rw [hid0] at hc2
      have := genesis_mem_chainIds hS hcr
      simp at hc2
      exact hc2 this
    obtain ⟨B', hB', hvx⟩ := (hs.valid x hx).resolve_left hx0
    rw [hxb] at hB'; cases hB'
    have hUp : Rooted st blk.hdr.parent := by
      rw [List.contains_iff_mem] at hc1
      exact (anc_height hS hcr hc1).1
    unfold validCore at hvx
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hvx
    obtain ⟨⟨⟨⟨⟨⟨-, -⟩, -⟩, hpol⟩, -⟩, -⟩, -⟩ := hvx
    unfold validUncle
    simp only [Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true']
    refine ⟨⟨⟨⟨⟨?_, ?_⟩, ?_⟩, ?_⟩, ?_⟩, ?_⟩
    · rwa [chainIds_ext hext hcr]
    · rwa [chainIds_ext hext hcr]
    · exact hc3
    · rw [slotOf_ext hext hUp.exists_blk]; exact hc4
    · -- valid on its own chain; both chains pass through the uncle's parent, which is
      -- after the cut of the uncle's epoch
      rw [chainUp_ext hext hcr, chainUp_ext hext hUp]
      rw [List.contains_iff_mem] at hc1
      have hself : blk.hdr.parent ∈ chainIds st blk.hdr.parent := self_mem_chainIds hS hUp
      have hcut : c.epochOf blk.hdr.slot = 0 ∨
          c.cut (c.epochOf blk.hdr.slot) ≤ slotOf st blk.hdr.parent + 1 := by
        set e := c.epochOf blk.hdr.slot
        have hW := hc.uncle_le
        rcases Nat.eq_zero_or_pos e with h0 | h1
        · exact Or.inl h0
        · right
          have hE : c.epochStart e ≤ blk.hdr.slot := by
            unfold Config.epochStart; exact Nat.div_mul_le_self _ _
          have hs1 : c.epochStart e = c.epochStart (e - 1) + c.epochLength := by
            rw [← epochStart_succ]; congr 1; omega
          unfold Config.cut
          omega
      rw [polValid_common hc hS hcr hUp hc1 hself _ _ hcut]; exact hpol
    · unfold genuine
      have hid := hS.idOK _ _ hxb
      rw [hid, hext _ _ hxb]; simp
  · exact hexec _ _ _ hsig

/-- **An honest proposal passes its proposer's validation.** -/
theorem propose_header (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    {i t newId : ℕ} {B : Block} (hB : propose c st L O G i t newId s = some B)
    (hslots : ∀ x ∈ s.tree, slotOf st x < t) (hc : c.Sane) (hexec : HonestExec L)
    {st' : Store} (hext : StoreExt st st') (hst' : st' B.hdr.id = some B)
    (hne : newId ≠ genesisId) :
    validHeader c st' L O G s.tree s.bimm t B = true := by
  obtain ⟨-, -, hpar, hsl⟩ := propose_id hB
  have hcr := hs.rooted _ hs.cloc
  obtain ⟨hbr, hbc⟩ := hs.bimm_on_cloc hS
  rw [validHeader_iff]
  refine ⟨propose_valid hS hs hB hslots hc hexec hext hst' hne, hsl.le, hpar ▸ hs.cloc, ?_⟩
  rw [hpar, height_ext hext hbr, height_ext hext hcr, hs.bimm, blockAtDepth_height hS hcr]
  omega

end Cryptarchia
