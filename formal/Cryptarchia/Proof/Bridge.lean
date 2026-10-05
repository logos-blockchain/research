import Cryptarchia.Proof.WorldStep
import Cryptarchia.Settle.Phases

/-!
# From an execution to a PoS tree

The **settlement tree** of a store: every stored block that is rooted, whose whole
chain passes the node-independent validity checks, with slot at most `N`. Its
characteristic string is read off the tree: slot `i` has as many honest successes
as honest blocks with slot `i`, and an adversarial success iff an adversarial
block with slot `i` is in the tree. (The probability layer relates this string
to the lottery.)

`tree_valid_upto`: restricted to slots `≤ t`, the tree is a valid PoS tree, as
soon as honest blocks at most `t` satisfy the depth axiom (A2).
`anc_iff`: ancestry in the tree is ancestry in the store.
-/

namespace Cryptarchia

open Settle

variable (c : Config) (L : Ledger) (O : Oracle) (G : Genesis) (st : Store)

/-- A block of the settlement tree: rooted, its whole chain valid, slot at most `N`. -/
def Good (N b : ℕ) : Prop :=
  Rooted st b ∧ slotOf st b ≤ N ∧
    ∀ x ∈ chainIds st b, x = genesisId ∨ ∃ B, st x = some B ∧ validCore c st L O G B = true

/-- Honest blocks (and genesis). -/
def honB (b : ℕ) : Bool :=
  decide (b = genesisId) || (match st b with
    | some B => match B.hdr.signer with
      | .honest _ => true
      | .adv => false
    | none => false)

open Classical in
/-- **Honest and timely**: genesis, or an honest block not marked `late`. A late
honest block (one the network failed to deliver in time) counts as adversarial in
the settlement tree and its string. -/
noncomputable def honL (late : ℕ → Prop) (b : ℕ) : Bool :=
  honB st b && (decide (b = genesisId) || !decide (late b))

open Classical in
/-- **The settlement tree** of a store, over the IDs `used`, up to slot `N`; the
honest vertices are the honest blocks not marked `late`. -/
noncomputable def stree (late : ℕ → Prop) (used : List ℕ) (N : ℕ) : PTree where
  V := used.toFinset.filter (fun b => Good c L O G st N b)
  par := parentOf st
  lab := slotOf st
  hon := honL st late
  dep := height st

open Classical in
/-- **Its characteristic string.** -/
noncomputable def sstr (late : ℕ → Prop) (used : List ℕ) (N : ℕ) : CStr := fun i =>
  (((stree c L O G st late used N).V.filter
      (fun v => honL st late v = true ∧ slotOf st v = i)).card,
    decide (∃ v ∈ (stree c L O G st late used N).V, honL st late v = false ∧ slotOf st v = i))

open Classical in
/-- The tree restricted to slots at most `t`. -/
noncomputable def Settle.PTree.restrict (F : PTree) (t : ℕ) : PTree :=
  { F with V := F.V.filter (fun v => F.lab v ≤ t) }

variable {c L O G st}

theorem mem_stree {late : ℕ → Prop} {used : List ℕ} {N b : ℕ} :
    b ∈ (stree c L O G st late used N).V ↔ b ∈ used ∧ Good c L O G st N b := by
  classical
  show b ∈ used.toFinset.filter _ ↔ _
  rw [Finset.mem_filter, List.mem_toFinset]

theorem mem_restrict {F : Settle.PTree} {t v : ℕ} : v ∈ (F.restrict t).V ↔ v ∈ F.V ∧ F.lab v ≤ t := by
  classical
  show v ∈ F.V.filter _ ↔ _
  rw [Finset.mem_filter]

theorem honB_genesis : honB st genesisId = true := by simp [honB]

theorem honL_genesis {late : ℕ → Prop} : honL st late genesisId = true := by simp [honL, honB]

/-- A timely-honest block is honest. -/
theorem honB_of_honL {late : ℕ → Prop} {b : ℕ} (h : honL st late b = true) : honB st b = true := by
  unfold honL at h; simp only [Bool.and_eq_true] at h; exact h.1

/-- A timely-honest block other than genesis is not late. -/
theorem not_late_of_honL {late : ℕ → Prop} {b : ℕ} (h : honL st late b = true) (h0 : b ≠ genesisId) :
    ¬ late b := by
  classical
  unfold honL at h; simp [h0] at h; exact h.2

theorem honL_iff {late : ℕ → Prop} {b : ℕ} (h0 : b ≠ genesisId) :
    honL st late b = true ↔ honB st b = true ∧ ¬ late b := by
  classical
  unfold honL; simp [h0]

section

variable (hS : StoreOK st)
include hS

theorem height_genesis : height st genesisId = 0 := by
  obtain ⟨g, hg, hs, -⟩ := hS.gen
  simp [height, chain_genesis hg hs]

theorem slotOf_genesis : slotOf st genesisId = 0 := by
  obtain ⟨g, hg, hs, -⟩ := hS.gen
  simp [slotOf, hg, hs]

theorem Good.parent {N b : ℕ} (h : Good c L O G st N b) : Good c L O G st N (parentOf st b) := by
  obtain ⟨hr, hsl, hv⟩ := h
  have hpr := hr.parent_rooted hS.genSelf
  have hpc : parentOf st b ∈ chainIds st b := by
    rw [mem_chainIds hS hr]
    rcases eq_or_ne b genesisId with h0 | h0
    · subst h0; exact ⟨0, Nat.zero_le _, by
        obtain ⟨g, hg, -, hgp⟩ := hS.gen; simp [parentOf_eq hg, hgp]⟩
    · refine ⟨1, ?_, rfl⟩
      obtain ⟨blk, hbk, hp, hs⟩ := hr.inv h0
      rw [height_step hbk h0 hp hs]; omega
  refine ⟨hpr, ?_, fun x hx => hv x (chainIds_trans hS hr hpc hx)⟩
  have := (anc_height hS hr hpc)
  -- the parent's slot is at most the block's
  rcases eq_or_ne b genesisId with h0 | h0
  · subst h0
    obtain ⟨g, hg, -, hgp⟩ := hS.gen
    rw [parentOf_eq hg, hgp]; exact hsl
  · obtain ⟨blk, hbk, hp, hs⟩ := hr.inv h0
    rw [parentOf_eq hbk]
    rw [slotOf_eq hbk] at hsl
    omega

theorem good_genesis (N : ℕ) : Good c L O G st N genesisId := by
  refine ⟨hS.rooted_gen, by rw [slotOf_genesis hS]; omega, ?_⟩
  intro x hx
  left
  obtain ⟨g, hg, hs, -⟩ := hS.gen
  unfold chainIds at hx; rw [chain_genesis hg hs] at hx
  simp [hS.idOK _ _ hg] at hx; exact hx

/-- Ancestry in the tree is ancestry in the store. -/
theorem anc_iff {late : ℕ → Prop} {used : List ℕ} {N u b : ℕ} (hb : Rooted st b) :
    (stree c L O G st late used N).Anc u b ↔ u ∈ chainIds st b := by
  unfold PTree.Anc
  simp only [stree]
  constructor
  · rintro ⟨hle, heq⟩
    rw [mem_chainIds hS hb]; exact ⟨_, Nat.sub_le _ _, heq⟩
  · intro hu
    obtain ⟨-, h1, h2⟩ := anc_height hS hb hu
    exact ⟨h1, h2⟩

/-- **The settlement tree up to slot `t` is a PoS tree**, given the depth axiom
for honest blocks up to `t`. -/
theorem tree_valid_upto {late : ℕ → Prop} {used : List ℕ} {N : ℕ} (Δ t : ℕ) (htN : t ≤ N)
    (hgen : genesisId ∈ used) (hpar : ∀ b ∈ used, Good c L O G st N b → parentOf st b ∈ used)
    (hA2 : ∀ u ∈ (stree c L O G st late used N).V, ∀ v ∈ (stree c L O G st late used N).V,
      honL st late u = true → honL st late v = true → slotOf st v ≤ t → slotOf st u + Δ < slotOf st v →
      height st u < height st v) :
    ((stree c L O G st late used N).restrict t).Valid Δ (sstr c L O G st late used N) t := by
  classical
  have hmem : ∀ b, b ∈ ((stree c L O G st late used N).restrict t).V ↔
      Good c L O G st N b ∧ b ∈ used ∧ slotOf st b ≤ t := by
    intro b
    rw [mem_restrict, mem_stree]
    constructor
    · rintro ⟨⟨h1, h2⟩, h3⟩; exact ⟨h2, h1, h3⟩
    · rintro ⟨h1, h2, h3⟩; exact ⟨⟨h2, h1⟩, h3⟩
  obtain ⟨g, hg, hgs, hgp⟩ := hS.gen
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · rw [hmem]
    exact ⟨good_genesis hS N, hgen,
      le_trans (le_of_eq (slotOf_genesis hS)) (Nat.zero_le _)⟩
  · exact (parentOf_eq hg).trans hgp
  · exact slotOf_genesis hS
  · exact honL_genesis (st := st) (late := late)
  · exact height_genesis hS
  · intro v hv
    rw [hmem] at hv ⊢
    obtain ⟨hgv, hvu, hvt⟩ := hv
    have hp := hgv.parent hS
    refine ⟨hp, hpar v hvu hgv, ?_⟩
    simp only [PTree.restrict, stree]
    exact le_trans (by
      rcases eq_or_ne v genesisId with h0 | h0
      · subst h0; rw [parentOf_eq hg, hgp]
      · obtain ⟨blk, hbk, hpr, hs⟩ := hgv.1.inv h0
        rw [parentOf_eq hbk, slotOf_eq hbk]; exact hs.le) hvt
  · intro v hv h0
    rw [hmem] at hv
    simp only [PTree.restrict, stree]
    obtain ⟨blk, hbk, hpr, hs⟩ := hv.1.1.inv h0
    rw [parentOf_eq hbk, slotOf_eq hbk]; exact hs
  · intro v hv h0
    rw [hmem] at hv
    simp only [PTree.restrict, stree]
    obtain ⟨blk, hbk, hpr, hs⟩ := hv.1.1.inv h0
    rw [parentOf_eq hbk, height_step hbk h0 hpr hs]
  · intro v hv; rw [hmem] at hv; exact hv.2.2
  · intro v hv h0
    rw [hmem] at hv
    simp only [PTree.restrict, stree]
    obtain ⟨blk, hbk, hpr, hs⟩ := hv.1.1.inv h0
    rw [slotOf_eq hbk]; omega
  · intro u hu v hv huh hvh hl
    rw [hmem] at hu hv
    exact hA2 u (mem_stree.2 ⟨hu.2.1, hu.1⟩) v (mem_stree.2 ⟨hv.2.1, hv.1⟩)
      huh hvh hv.2.2 hl
  · intro i hi1 hit
    simp only [sstr]
    congr 1
    ext v
    rw [Finset.mem_filter, Finset.mem_filter, mem_restrict]
    constructor
    · rintro ⟨⟨h1, -⟩, h2, h3⟩; exact ⟨h1, h2, h3⟩
    · rintro ⟨h1, h2, h3⟩; exact ⟨⟨h1, by show slotOf st v ≤ t; omega⟩, h2, h3⟩
  · intro v hv hh
    simp only [sstr, decide_eq_true_eq]
    rw [mem_restrict] at hv
    exact ⟨v, hv.1, hh, rfl⟩

end

end Cryptarchia
