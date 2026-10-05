import Cryptarchia.Spec.Chain

/-!
# Chains in the block store

Facts about `chain`, `height` and ancestry for **rooted** blocks: blocks whose
parent links reach genesis through stored blocks with strictly decreasing slots.
Every block an honest node accepts is rooted (`validHeader` checks the parent is
accepted and has an earlier slot), and the store only grows, so rooted blocks'
chains never change.
-/

namespace Cryptarchia

variable (st : Store)

/-- `b` is rooted: its parent links reach genesis through stored blocks, with
strictly decreasing slots. -/
inductive Rooted : ℕ → Prop
  | gen (g : Block) : st genesisId = some g → g.hdr.slot = 0 → Rooted genesisId
  | step (b : ℕ) (blk : Block) : st b = some blk → b ≠ genesisId → Rooted blk.hdr.parent →
      slotOf st blk.hdr.parent < blk.hdr.slot → Rooted b

variable {st}

theorem Rooted.exists_blk {b : ℕ} (h : Rooted st b) : ∃ blk, st b = some blk := by
  cases h with
  | gen g hg _ => exact ⟨g, hg⟩
  | step _ blk hb _ _ _ => exact ⟨blk, hb⟩

theorem chain_ne_nil {b : ℕ} {blk : Block} (hb : st b = some blk) : chain st b ≠ [] := by
  unfold chain
  rw [hb]
  simp only
  unfold chainF
  simp only [hb]
  split <;> simp

/-- The chain of a rooted block, with enough fuel, is the full chain. -/
theorem chainF_rooted {b : ℕ} (h : Rooted st b) :
    ∀ n, slotOf st b + 1 ≤ n → chainF st n b = chainF st (slotOf st b + 1) b := by
  induction h with
  | gen g hg _ =>
    intro n hn
    obtain ⟨n, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
    simp [chainF, hg, slotOf]
  | step b blk hb hne hpar hslot ih =>
    intro n hn
    have hsb : slotOf st b = blk.hdr.slot := by simp [slotOf, hb]
    obtain ⟨n, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
    rw [hsb]
    simp only [chainF, hb, hne, if_false]
    congr 1
    rw [ih n (by rw [hsb] at hn; omega), ih blk.hdr.slot (by omega)]

theorem chain_eq_chainF {b : ℕ} (h : Rooted st b) : chain st b = chainF st (slotOf st b + 1) b := by
  obtain ⟨blk, hb⟩ := h.exists_blk
  have hs : slotOf st b = blk.hdr.slot := by simp [slotOf, hb]
  unfold chain
  rw [hb]
  simp only
  rw [← hs]
  exact chainF_rooted h _ (by omega)

/-- **The chain recursion.** -/
theorem chain_step {b : ℕ} {blk : Block} (hb : st b = some blk) (hne : b ≠ genesisId)
    (hpar : Rooted st blk.hdr.parent) (hslot : slotOf st blk.hdr.parent < blk.hdr.slot) :
    chain st b = blk :: chain st blk.hdr.parent := by
  have h := Rooted.step b blk hb hne hpar hslot
  rw [chain_eq_chainF h, chain_eq_chainF hpar]
  have hs : slotOf st b = blk.hdr.slot := by simp [slotOf, hb]
  rw [hs]
  conv_lhs => unfold chainF
  simp only [hb, hne, if_false]
  rw [chainF_rooted hpar blk.hdr.slot (by omega)]

theorem chain_genesis {g : Block} (hg : st genesisId = some g) (hs : g.hdr.slot = 0) :
    chain st genesisId = [g] := by
  rw [chain_eq_chainF (Rooted.gen g hg hs)]
  simp [chainF, hg, slotOf, hs]

/-- Unfolding a rooted non-genesis block. -/
theorem Rooted.inv {b : ℕ} (h : Rooted st b) (hne : b ≠ genesisId) :
    ∃ blk, st b = some blk ∧ Rooted st blk.hdr.parent ∧ slotOf st blk.hdr.parent < blk.hdr.slot := by
  cases h with
  | gen g _ _ => exact absurd rfl hne
  | step _ blk hb _ hpar hslot => exact ⟨blk, hb, hpar, hslot⟩

theorem height_step {b : ℕ} {blk : Block} (hb : st b = some blk) (hne : b ≠ genesisId)
    (hpar : Rooted st blk.hdr.parent) (hslot : slotOf st blk.hdr.parent < blk.hdr.slot) :
    height st b = height st blk.hdr.parent + 1 := by
  unfold height
  rw [chain_step hb hne hpar hslot]
  have : (chain st blk.hdr.parent).length ≠ 0 := by
    obtain ⟨p, hp⟩ := hpar.exists_blk
    have := chain_ne_nil hp; intro h0; exact this (List.eq_nil_of_length_eq_zero h0)
  simp only [List.length_cons]
  omega

/-- **Growing the store** keeps rooted blocks rooted and their chains unchanged. -/
theorem Rooted.mono {st' : Store} (hsub : ∀ b blk, st b = some blk → st' b = some blk)
    {b : ℕ} (h : Rooted st b) : Rooted st' b := by
  induction h with
  | gen g hg hs => exact Rooted.gen g (hsub _ _ hg) hs
  | step b blk hb hne _ hslot ih =>
    refine Rooted.step b blk (hsub _ _ hb) hne ih ?_
    have : slotOf st' blk.hdr.parent = slotOf st blk.hdr.parent := by
      obtain ⟨p, hp⟩ := (show Rooted st blk.hdr.parent from by assumption).exists_blk
      simp [slotOf, hp, hsub _ _ hp]
    rwa [this]

theorem chain_mono {st' : Store} (hsub : ∀ b blk, st b = some blk → st' b = some blk)
    {b : ℕ} (h : Rooted st b) : chain st' b = chain st b := by
  induction h with
  | gen g hg hs => rw [chain_genesis hg hs, chain_genesis (hsub _ _ hg) hs]
  | step b blk hb hne hpar hslot ih =>
    have hpar' := hpar.mono hsub
    have hs' : slotOf st' blk.hdr.parent = slotOf st blk.hdr.parent := by
      obtain ⟨p, hp⟩ := hpar.exists_blk
      simp [slotOf, hp, hsub _ _ hp]
    rw [chain_step hb hne hpar hslot, chain_step (hsub _ _ hb) hne hpar' (by rwa [hs']), ih]

end Cryptarchia

namespace Cryptarchia

variable {st : Store}

theorem slotOf_eq {b : ℕ} {blk : Block} (hb : st b = some blk) : slotOf st b = blk.hdr.slot := by
  simp [slotOf, hb]

theorem parentOf_eq {b : ℕ} {blk : Block} (hb : st b = some blk) : parentOf st b = blk.hdr.parent := by
  simp [parentOf, hb]

/-- The IDs of a stored block's chain start with the block itself. -/
theorem chainIds_head {b : ℕ} {blk : Block} (hb : st b = some blk) (hid : blk.hdr.id = b) :
    ∃ l, chainIds st b = b :: l := by
  unfold chainIds chain
  rw [hb]; simp only
  unfold chainF; simp only [hb]
  split <;> simp [hid]

/-- A stored block's header carries its own ID (true of every store an execution
builds: `World.add` files a block under its header's ID). -/
def IdOK (st : Store) : Prop := ∀ b blk, st b = some blk → blk.hdr.id = b

/-- Genesis is its own parent (true of every store an execution builds). -/
def GenSelf (st : Store) : Prop := ∀ g, st genesisId = some g → g.hdr.parent = genesisId

theorem Rooted.parent_rooted (hgs : GenSelf st) {b : ℕ} (h : Rooted st b) :
    Rooted st (parentOf st b) := by
  cases h with
  | gen g hg hs => rw [parentOf_eq hg, hgs g hg]; exact Rooted.gen g hg hs
  | step b blk hb _ hpar _ => rw [parentOf_eq hb]; exact hpar

end Cryptarchia
