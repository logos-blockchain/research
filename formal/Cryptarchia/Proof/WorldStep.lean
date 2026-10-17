module

public import Cryptarchia.Proof.Structural
public import Cryptarchia.Spec.Execution
public import Cryptarchia.Proof.NodeStep
import Std.Tactic.BVDecide.Normalize.BitVec
import Std.Tactic.BVDecide.Normalize.Prop
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

/-!
# Stores and worlds

The store only grows (`StoreExt`); rooted blocks keep their chains, heights and
validity when it does, and good blocks stay good (`GoodAt.mono`). The two moves that
change a world's store: adding a block (`World.add`), and a node's lead step
(`lead_cases`), which adds at most the node's proposal.
-/

@[expose] public section

namespace Cryptarchia

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis}

/-- `st'` extends `st`. -/
def StoreExt (st st' : Store) : Prop := ∀ b blk, st b = some blk → st' b = some blk

/-- A block is **good at time `t`**: rooted, not from the future, its whole chain
valid. The blocks of the settlement tree up to `N` are the good ones at `N`; every
block of every node's tree is good at the current time. -/
def GoodAt (c : Config) (L : Ledger) (O : Oracle) (G : Genesis) (st : Store) (t b : ℕ) : Prop :=
  Rooted st b ∧ slotOf st b ≤ t ∧
    ∀ x ∈ chainIds st b, x = genesisId ∨ ∃ B, st x = some B ∧ validCore c st L O G B = true

variable {st st' : Store}

theorem StoreExt.refl (st : Store) : StoreExt st st := fun _ _ h => h

theorem StoreExt.trans {st'' : Store} (h1 : StoreExt st st') (h2 : StoreExt st' st'') :
    StoreExt st st'' := fun b blk h => h2 b blk (h1 b blk h)

section Ext

variable (hx : StoreExt st st')
include hx

theorem slotOf_ext {b : ℕ} (hb : ∃ blk, st b = some blk) : slotOf st' b = slotOf st b := by
  obtain ⟨blk, h⟩ := hb; simp [slotOf, h, hx _ _ h]

theorem parentOf_ext {b : ℕ} (hb : ∃ blk, st b = some blk) : parentOf st' b = parentOf st b := by
  obtain ⟨blk, h⟩ := hb; simp [parentOf, h, hx _ _ h]

theorem chainIds_ext {b : ℕ} (hb : Rooted st b) : chainIds st' b = chainIds st b := by
  unfold chainIds; rw [chain_mono hx hb]

theorem chainUp_ext {b : ℕ} (hb : Rooted st b) : chainUp st' b = chainUp st b := by
  unfold chainUp; rw [chain_mono hx hb]

theorem height_ext {b : ℕ} (hb : Rooted st b) : height st' b = height st b := by
  unfold height; rw [chain_mono hx hb]

theorem blockAtDepth_ext {b : ℕ} (hb : Rooted st b) (d : ℕ) :
    blockAtDepth st' b d = blockAtDepth st b d := by
  unfold blockAtDepth; rw [chainIds_ext hx hb]

theorem genuine_ext {h : Header} (hg : genuine st h = true) : genuine st' h = true := by
  unfold genuine at *
  cases hb : st h.id with
  | none => rw [hb] at hg; simp at hg
  | some b => rw [hb] at hg; rw [hx _ _ hb]; exact hg

theorem validUncle_ext (hS : StoreOK st) {par slotA : ℕ} (hpar : Rooted st par) {U : Header}
    (hv : validUncle c st L O G par slotA U = true) : validUncle c st' L O G par slotA U = true := by
  unfold validUncle at *
  simp only [Bool.and_eq_true, decide_eq_true_eq, List.contains_iff_mem, Bool.not_eq_true'] at *
  obtain ⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩ := hv
  have hUp : Rooted st U.parent := (anc_height hS hpar h1).1
  refine ⟨⟨⟨⟨⟨?_, ?_⟩, h3⟩, ?_⟩, ?_⟩, genuine_ext hx h6⟩
  · rwa [chainIds_ext hx hpar]
  · rwa [chainIds_ext hx hpar]
  · rwa [slotOf_ext hx hUp.exists_blk]
  · rwa [chainUp_ext hx hpar, chainUp_ext hx hUp]

theorem validCore_ext (hS : StoreOK st) {B : Block} (hpar : Rooted st B.hdr.parent)
    (hv : validCore c st L O G B = true) : validCore c st' L O G B = true := by
  unfold validCore at *
  simp only [Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true] at *
  obtain ⟨⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩, h7⟩ := hv
  refine ⟨⟨⟨⟨⟨⟨h1, h2⟩, ?_⟩, ?_⟩, genuine_ext hx h5⟩, ?_⟩, ?_⟩
  · rwa [slotOf_ext hx hpar.exists_blk]
  · rwa [chainUp_ext hx hpar]
  · intro U hU; exact validUncle_ext hx hS hpar (h6 U hU)
  · rwa [chainUp_ext hx hpar]

/-- A rooted block valid in a store is valid in any extension. -/
theorem valid_ext (hS : StoreOK st) {y : ℕ} (hy : Rooted st y)
    (h : y = genesisId ∨ ∃ B, st y = some B ∧ validCore c st L O G B = true) :
    y = genesisId ∨ ∃ B, st' y = some B ∧ validCore c st' L O G B = true := by
  rcases eq_or_ne y genesisId with h0 | h0
  · exact Or.inl h0
  obtain ⟨B, hB, hv⟩ := h.resolve_left h0
  obtain ⟨blk, hbk, hpr, -⟩ := hy.inv h0
  rw [hbk] at hB; cases hB
  exact Or.inr ⟨_, hx _ _ hbk, validCore_ext hx hS hpr hv⟩

theorem nodeOK_ext (hS : StoreOK st) {k : ℕ} {s : NodeState} (hs : NodeOK k st L O G c s) :
    NodeOK k st' L O G c s := by
  refine ⟨fun y hy => (hs.rooted y hy).mono hx, fun y hy => valid_ext hx hS (hs.rooted y hy) (hs.valid y hy),
    ?_, hs.gen, hs.cloc, ?_, hs.rule⟩
  · intro y hy
    rw [parentOf_ext hx (hs.rooted y hy).exists_blk]; exact hs.closed y hy
  · rw [hs.bimm, blockAtDepth_ext hx (hs.rooted _ hs.cloc)]

end Ext

/-- Goodness survives a growing store and a later time. -/
theorem GoodAt.mono (hS : StoreOK st) (hx : StoreExt st st') {t t' b : ℕ} (htt : t ≤ t')
    (h : GoodAt c L O G st t b) : GoodAt c L O G st' t' b := by
  obtain ⟨hr, hsl, hv⟩ := h
  refine ⟨hr.mono hx, by rw [slotOf_ext hx hr.exists_blk]; omega, fun x hx' => ?_⟩
  rw [chainIds_ext hx hr] at hx'
  exact valid_ext hx hS (anc_height hS hr hx').1 (hv x hx')

/-! ## Worlds -/

variable {E : Env}

@[simp] theorem add_st_self (w : World) (B : Block) : (w.add B).st B.hdr.id = some B := by
  simp [World.add]

theorem add_st_of_ne {w : World} {B : Block} {b : ℕ} (h : b ≠ B.hdr.id) : (w.add B).st b = w.st b := by
  simp [World.add, h]

theorem add_st_cases {w : World} {B C : Block} {b : ℕ} (h : (w.add B).st b = some C) :
    (b = B.hdr.id ∧ C = B) ∨ w.st b = some C := by
  by_cases hb : b = B.hdr.id
  · subst hb; rw [add_st_self] at h; exact Or.inl ⟨rfl, (Option.some_inj.1 h).symm⟩
  · rw [add_st_of_ne hb] at h; exact Or.inr h

theorem fresh_not_used (w : World) : w.fresh ∉ w.used := by
  intro h
  have : ∀ l : List ℕ, ∀ a, ∀ x ∈ l, x ≤ l.foldl max a := by
    intro l
    induction l with
    | nil => simp
    | cons y ys ih =>
      intro a x hx
      simp only [List.foldl_cons]
      rcases List.mem_cons.1 hx with rfl | hx
      · have : ∀ l : List ℕ, ∀ a, a ≤ l.foldl max a := by
          intro l; induction l with
          | nil => simp
          | cons z zs ih' => intro a; simp only [List.foldl_cons]; exact le_trans (le_max_left _ _) (ih' _)
        exact le_trans (le_max_right _ _) (this ys _)
      · exact ih _ x hx
  have := this w.used 0 w.fresh h
  unfold World.fresh at this; omega

theorem propose_id {c : Config} {st : Store} {L : Ledger} {O : Oracle} {G : Genesis}
    {i sl newId : ℕ} {s : NodeState} {B : Block} (h : propose c st L O G i sl newId s = some B) :
    B.hdr.id = newId ∧ B.hdr.signer = .honest i ∧ B.hdr.parent = s.cloc ∧ B.hdr.slot = sl := by
  unfold propose at h
  split at h
  · simp at h
  · split at h
    · simp at h
    · simp at h; subst h; simp

/-- **The two outcomes of a lead step**: nothing (the node is offline or does not
win), or the node's proposal is added, logged, and processed by the node. -/
theorem lead_cases (w : World) (i : ℕ) :
    ((E.online i w.now = true → propose E.c w.st E.L E.O E.G i w.now w.fresh (w.node i) = none) ∧
      w.lead E i = w) ∨
    ∃ C, E.online i w.now = true ∧ propose E.c w.st E.L E.O E.G i w.now w.fresh (w.node i) = some C ∧
      w.lead E i = { w.add C with
        node := fun j => if j = i then
          onBlock E.c (w.add C).st E.L E.O E.G E.fastPath (E.ord i) (w.add C).now (w.node i) C
          else (w.add C).node j
        honestLog := (C.hdr.id, w.now) :: w.honestLog } := by
  unfold World.lead
  split
  · rename_i h; exact Or.inl ⟨fun h' => by simp [h'] at h, rfl⟩
  rename_i hio
  simp only [Bool.not_eq_true', Bool.not_eq_false] at hio
  split
  · rename_i h; exact Or.inl ⟨fun _ => h, rfl⟩
  · rename_i C hC; exact Or.inr ⟨C, hio, hC, rfl⟩

theorem lead_now (w : World) (i : ℕ) : (w.lead E i).now = w.now := by
  rcases lead_cases (E := E) w i with ⟨-, h⟩ | ⟨C, -, -, h⟩ <;> rw [h]; rfl

theorem lead_other (w : World) {i j : ℕ} (hji : j ≠ i) : (w.lead E i).node j = w.node j := by
  rcases lead_cases (E := E) w i with ⟨-, h⟩ | ⟨C, -, -, h⟩ <;> rw [h]
  simp [hji, World.add]

/-- A lead step adds at most the node's proposal. -/
theorem lead_st {w : World} {i b : ℕ} {B : Block} (h : (w.lead E i).st b = some B) :
    w.st b = some B ∨
      (E.online i w.now = true ∧ propose E.c w.st E.L E.O E.G i w.now w.fresh (w.node i) = some B) := by
  rcases lead_cases (E := E) w i with ⟨-, hL⟩ | ⟨C, hio, hC, hL⟩ <;> rw [hL] at h
  · exact Or.inl h
  · rcases add_st_cases h with ⟨-, rfl⟩ | h
    · exact Or.inr ⟨hio, hC⟩
    · exact Or.inl h

/-- A winning node's lead step adds its proposal. -/
theorem lead_st_some {w : World} {i : ℕ} {C : Block} (hio : E.online i w.now = true)
    (hC : propose E.c w.st E.L E.O E.G i w.now w.fresh (w.node i) = some C) :
    (w.lead E i).st C.hdr.id = some C := by
  rcases lead_cases (E := E) w i with ⟨h, -⟩ | ⟨C', -, hC', hL⟩
  · rw [h hio] at hC; cases hC
  · rw [hC] at hC'; cases hC'; rw [hL]; exact add_st_self w C

end Cryptarchia
