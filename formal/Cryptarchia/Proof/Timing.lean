import Cryptarchia.Proof.EpochCut

/-!
# Timing and honest blocks

Two more facts about every execution (in every epoch, for sane parameters):

* no node's tree holds a block from the future (`slot ≤ now`);
* every honest block is logged with its creation slot and passes the
  node-independent validity checks.

The second needs the ledger assumption that honest payloads execute
(`HonestExec`).
-/

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

/-- **An honest proposal is valid.** -/
theorem propose_valid (hS : StoreOK st) {s : NodeState} (hs : NodeOK c.k st L O G c s)
    {i t newId : ℕ} {B : Block} (hB : propose c st L O G i t newId s = some B)
    (hslots : ∀ x ∈ s.tree, slotOf st x < t) (hc : c.Sane) (hexec : HonestExec L)
    {st' : Store} (hS' : StoreOK st') (hext : StoreExt st st') (hst' : st' B.hdr.id = some B)
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

end Cryptarchia
