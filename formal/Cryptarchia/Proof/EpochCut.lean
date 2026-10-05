import Cryptarchia.Proof.Honest

/-!
# Epoch states agree on chains through a recent common block

The epoch state of epoch `e ≥ 1` is a function of the chain's blocks with slot
below the **cut** `cut e = epochStart (e - 1) + nonceOffset`
(`epochState_cut`): the eligible notes are fixed at `epochStart (e - 1)`, the
nonce at the cut itself, and the stake estimate counts occupied slots in
windows `[epochStart e', epochStart e' + PERIOD)` with `e' < e`, which end by
the cut when `PERIOD ≤ nonceOffset`. At the spec parameters the cut is
`4⌊k/f⌋` slots (72 h) before the epoch starts.

So two chains through a common block with slot at least `cut e - 1` derive the
same epoch-`e` state (`epochState_common`). This replaces the first-epoch
hypothesis wherever a block is validated on another chain than its own (uncles).
-/

namespace Cryptarchia

/-- The parameters are laid out as the specification does: the stake-inference
window ends by the nonce cut, the nonce cut is inside the previous epoch, the
uncle window is shorter than the time between the cut and the epoch start, and
that time is at least two slots (so an epoch's state can be fixed before the
epoch starts, `Config.fix`). -/
structure Config.Sane (c : Config) : Prop where
  period_le : c.period ≤ c.nonceOffset
  offset_le : c.nonceOffset ≤ c.epochLength
  uncle_le : c.uncleWindow + c.nonceOffset ≤ c.epochLength
  offset_pos : 1 ≤ c.nonceOffset
  fix_le : c.nonceOffset + 2 ≤ c.epochLength

theorem Config.spec_sane : Config.spec.Sane :=
  ⟨by decide, by decide, by decide, by decide, by decide⟩

/-- Epochs have positive length: `1 ≤ nonceOffset ≤ epochLength`. -/
theorem Config.Sane.epochLength_pos {c : Config} (h : c.Sane) : 0 < c.epochLength :=
  lt_of_lt_of_le h.offset_pos h.offset_le

/-- The cut of epoch `e`. -/
def Config.cut (c : Config) (e : ℕ) : ℕ := c.epochStart (e - 1) + c.nonceOffset

/-- **The fixing time of epoch `e`**: two slots before it starts. The analysis
reads each epoch's canonical state here; the protocol has no such moment. -/
def Config.fix (c : Config) (e : ℕ) : ℕ := c.epochStart e - 2

/-- The fixing time is after the cut and two slots before the epoch starts. -/
theorem Config.Sane.fix_ok {c : Config} (h : c.Sane) (e : ℕ) (he : 1 ≤ e) :
    c.cut e ≤ c.fix e ∧ c.fix e + 2 ≤ c.epochStart e := by
  obtain ⟨e0, rfl⟩ : ∃ e0, e = e0 + 1 := ⟨e - 1, by omega⟩
  have hs : c.epochStart (e0 + 1) = c.epochStart e0 + c.epochLength := by
    unfold Config.epochStart; ring
  have := h.fix_le
  unfold Config.cut Config.fix
  simp only [Nat.add_sub_cancel]
  omega

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}

theorem prefixBelow_prefixBelow (C : List Block) {a b : ℕ} (hab : a ≤ b) :
    prefixBelow (prefixBelow C b) a = prefixBelow C a := by
  unfold prefixBelow
  rw [List.filter_filter]
  apply List.filter_congr
  intro x _
  by_cases h1 : x.hdr.id = genesisId <;> by_cases h2 : x.hdr.slot < a <;> simp [h1, h2] <;> omega

theorem prefixBelow_min (C : List Block) (a b : ℕ) :
    prefixBelow (prefixBelow C a) b = prefixBelow C (min a b) := by
  unfold prefixBelow
  rw [List.filter_filter]
  apply List.filter_congr
  intro x _
  by_cases h1 : x.hdr.id = genesisId <;> simp [h1, Nat.lt_min, Bool.and_comm]

theorem occupied_prefix (C : List Block) {e s : ℕ} (hs : c.epochStart e + c.period ≤ s) :
    occupied c (prefixBelow C s) e = occupied c C e := by
  unfold occupied prefixBelow
  have : (C.filter (fun x => x.hdr.id = genesisId ∨ x.hdr.slot < s)).filter
      (fun x => inWindow c e x.hdr.slot) = C.filter (fun x => inWindow c e x.hdr.slot) := by
    rw [List.filter_filter]
    apply List.filter_congr
    intro x _
    by_cases hw : inWindow c e x.hdr.slot = true
    · have : x.hdr.slot < s := by unfold inWindow at hw; simp at hw; omega
      simp [hw, this]
    · simp [hw]
  simp only [this]

theorem stakeEstimate_prefix (C : List Block) {s : ℕ} :
    ∀ e, (∀ e', e' < e → c.epochStart e' + c.period ≤ s) →
      stakeEstimate c G (prefixBelow C s) e = stakeEstimate c G C e := by
  intro e
  induction e with
  | zero => intro _; rfl
  | succ e ih =>
    intro h
    simp only [stakeEstimate]
    rw [ih (fun e' he' => h e' (by omega)), occupied_prefix C (h e (by omega))]

theorem epochStart_mono {a b : ℕ} (h : a ≤ b) : c.epochStart a ≤ c.epochStart b := by
  unfold Config.epochStart; exact Nat.mul_le_mul_right _ h

theorem epochStart_succ (e : ℕ) : c.epochStart (e + 1) = c.epochStart e + c.epochLength := by
  unfold Config.epochStart; ring

/-- **The epoch state of epoch `e ≥ 1` depends only on the blocks below its cut.** -/
theorem epochState_cut (hc : c.Sane) (C : List Block) {e : ℕ} (he : 1 ≤ e) :
    epochState c L O G (prefixBelow C (c.cut e)) e = epochState c L O G C e := by
  obtain ⟨e0, rfl⟩ : ∃ e0, e = e0 + 1 := ⟨e - 1, by omega⟩
  have hcut : c.cut (e0 + 1) = c.epochStart e0 + c.nonceOffset := by simp [Config.cut]
  have hcs : c.cut (e0 + 1) ≤ c.epochStart (e0 + 1) := by
    rw [hcut, epochStart_succ]; have := hc.offset_le; omega
  have hl : c.epochStart e0 ≤ c.cut (e0 + 1) := by rw [hcut]; omega
  have hwin : ∀ e', e' < e0 + 1 → c.epochStart e' + c.period ≤ c.cut (e0 + 1) := by
    intro e' he'
    rw [hcut]; have := epochStart_mono (c := c) (show e' ≤ e0 by omega); have := hc.period_le; omega
  have hwin' : ∀ e', e' < e0 + 1 → c.epochStart e' + c.period ≤ c.epochStart (e0 + 1) :=
    fun e' he' => le_trans (hwin e' he') hcs
  unfold epochState
  simp only [Nat.add_sub_cancel, Nat.add_one_ne_zero, if_false, prefixBelow_min]
  rw [Nat.min_eq_left hcs, Nat.min_eq_right hl, Nat.min_eq_right (le_trans hl hcs), ← hcut, min_self,
    Nat.min_eq_right hcs, stakeEstimate_prefix C _ hwin, stakeEstimate_prefix C _ hwin']

theorem chainUp_step {a : ℕ} {A : Block} (ha : st a = some A) (hne : a ≠ genesisId)
    (hpar : Rooted st A.hdr.parent) (hslot : slotOf st A.hdr.parent < A.hdr.slot) :
    chainUp st a = chainUp st A.hdr.parent ++ [A] := by
  unfold chainUp; rw [chain_step ha hne hpar hslot]; simp

theorem chainUp_genesis (hS : StoreOK st) : ∃ g, st genesisId = some g ∧ chainUp st genesisId = [g] := by
  obtain ⟨g, hg, hs, -⟩ := hS.gen
  exact ⟨g, hg, by unfold chainUp; rw [chain_genesis hg hs]; simp⟩

/-- The chain of `b`, genesis first, starts with the chain of any ancestor. -/
theorem chainUp_split (hS : StoreOK st) {b h : ℕ} (hb : Rooted st b) (hh : h ∈ chainIds st b) :
    ∃ R, chainUp st b = chainUp st h ++ R := by
  induction hb with
  | gen g hg hs =>
    unfold chainIds at hh; rw [chain_genesis hg hs] at hh
    simp [hS.idOK _ _ hg] at hh; subst hh; exact ⟨[], by simp⟩
  | step b blk hbk hne hpar hslot ih =>
    by_cases hbh : h = b
    · subst hbh; exact ⟨[], by simp⟩
    · have : h ∈ chainIds st blk.hdr.parent := by
        unfold chainIds at hh ⊢
        rw [chain_step hbk hne hpar hslot] at hh
        simp only [List.map_cons, List.mem_cons] at hh
        rcases hh with hh | hh
        · exact absurd (hh.trans (hS.idOK _ _ hbk)) hbh
        · exact hh
      obtain ⟨R, hR⟩ := ih this
      exact ⟨R ++ [blk], by rw [chainUp_step hbk hne hpar hslot, hR, List.append_assoc]⟩

/-- The chain of `b`, genesis first, is the chain of an ancestor `h` followed by
non-genesis blocks with later slots. -/
theorem chainUp_split_slots (hS : StoreOK st) {b h : ℕ} (hb : Rooted st b) (hh : h ∈ chainIds st b) :
    ∃ R, chainUp st b = chainUp st h ++ R ∧ (∀ y ∈ R, slotOf st h < y.hdr.slot ∧ y.hdr.id ≠ genesisId) ∧
      slotOf st h ≤ slotOf st b := by
  induction hb with
  | gen g hg hs =>
    unfold chainIds at hh; rw [chain_genesis hg hs] at hh
    simp [hS.idOK _ _ hg] at hh; subst hh; exact ⟨[], by simp, by simp, le_rfl⟩
  | step b blk hbk hne hpar hslot ih =>
    by_cases hbh : h = b
    · subst hbh; exact ⟨[], by simp, by simp, le_rfl⟩
    · have : h ∈ chainIds st blk.hdr.parent := by
        unfold chainIds at hh ⊢
        rw [chain_step hbk hne hpar hslot] at hh
        simp only [List.map_cons, List.mem_cons] at hh
        rcases hh with hh | hh
        · exact absurd (hh.trans (hS.idOK _ _ hbk)) hbh
        · exact hh
      obtain ⟨R, hR, hRs, hle⟩ := ih this
      refine ⟨R ++ [blk], by rw [chainUp_step hbk hne hpar hslot, hR, List.append_assoc], ?_, ?_⟩
      · intro y hy
        rw [List.mem_append, List.mem_singleton] at hy
        rcases hy with hy | hy
        · exact hRs y hy
        · subst hy; exact ⟨by omega, by rw [hS.idOK _ _ hbk]; exact hne⟩
      · rw [slotOf_eq hbk]; omega

theorem prefixBelow_common (hS : StoreOK st) {a x s : ℕ} (ha : Rooted st a) (hx : x ∈ chainIds st a)
    (hs : s ≤ slotOf st x + 1) : prefixBelow (chainUp st a) s = prefixBelow (chainUp st x) s := by
  obtain ⟨R, hR, hRs, -⟩ := chainUp_split_slots hS ha hx
  rw [hR]
  unfold prefixBelow
  rw [List.filter_append]
  have : R.filter (fun y => y.hdr.id = genesisId ∨ y.hdr.slot < s) = [] := by
    rw [List.filter_eq_nil_iff]
    intro y hy
    have := hRs y hy
    simp only [decide_eq_true_eq, not_or]
    exact ⟨this.2, by omega⟩
  rw [this, List.append_nil]

/-- **Chains through a common block at or after the cut derive the same epoch state.** -/
theorem epochState_common (hc : c.Sane) (hS : StoreOK st) {a b x : ℕ} (ha : Rooted st a) (hb : Rooted st b)
    (hxa : x ∈ chainIds st a) (hxb : x ∈ chainIds st b) {e : ℕ} (hs : e = 0 ∨ c.cut e ≤ slotOf st x + 1) :
    epochState c L O G (chainUp st a) e = epochState c L O G (chainUp st b) e := by
  rcases Nat.eq_zero_or_pos e with h0 | h1
  · subst h0; exact epochState_zero hS ha hb
  · have hs := hs.resolve_left (by omega)
    rw [← epochState_cut hc (chainUp st a) h1, ← epochState_cut hc (chainUp st b) h1,
      prefixBelow_common hS ha hxa hs, prefixBelow_common hS hb hxb hs]

theorem polValid_common (hc : c.Sane) (hS : StoreOK st) {a b x : ℕ} (ha : Rooted st a) (hb : Rooted st b)
    (hxa : x ∈ chainIds st a) (hxb : x ∈ chainIds st b) (P : List Block) (h : Header)
    (hs : c.epochOf h.slot = 0 ∨ c.cut (c.epochOf h.slot) ≤ slotOf st x + 1) :
    polValid c L O G (chainUp st a) P h = polValid c L O G (chainUp st b) P h := by
  unfold polValid; rw [epochState_common hc hS ha hb hxa hxb hs]

end Cryptarchia
