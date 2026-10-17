module

public import Cryptarchia.Proof.Timing
public import Cryptarchia.Proof.Local
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
import Mathlib.RingTheory.WittVector.IsPoly
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
import Mathlib.Tactic.ReduceModChar
import Mathlib.Topology.Sheaves.Init
import Std.Tactic.BVDecide.Normalize.BitVec
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# Executions

**The world invariant** (`WorldOK`): the store and every node are well formed, no
node's tree holds a block from the future, and every honest block is good, logged
with its slot, signed by a node online at its slot, and its signer's only block at
that slot (`HonBlk`).

**From a world to a later one** (`StepOK`): the later world is well formed, the store
grows, the clock does not go back, no node's local chain loses height or its
immutable block, and honest blocks created in between have later slots. Every event
gives it (`step_ok`, under the assumptions `Assm`), and it composes, so it relates
any two points of an execution (`wAt_le`; `wAt es n` is the world after the first
`n` events). A tick is a fold of the nodes' lead steps (`tick_induct`), each node
leading once; what it adds (`tick_new`, `tick_tree`).
-/

@[expose] public section

namespace Cryptarchia

variable {E : Env}

/-- Honest-signed blocks. -/
def IsHon (B : Block) : Prop := ∃ j, B.hdr.signer = .honest j

/-- What holds of an honest block `b` signed by `j`, in a store with a clock and a
log: it is good, logged with its slot, signed by a node online at its slot, and the
only block of `j` with that slot. -/
structure HonBlk (E : Env) (st : Store) (now : ℕ) (log : List (ℕ × ℕ)) (b : ℕ) (B : Block)
    (j : ℕ) : Prop where
  good : GoodAt E.c E.L E.O E.G st now b
  log : (b, B.hdr.slot) ∈ log
  node : j ∈ E.nodes
  online : E.online j B.hdr.slot = true
  uniq : ∀ b' B', st b' = some B' → B'.hdr.signer = .honest j → B'.hdr.slot = B.hdr.slot → b' = b

/-- **The world is well formed.** -/
structure WorldOK (E : Env) (w : World) : Prop where
  store : StoreOK w.st
  used : ∀ b, (∃ blk, w.st b = some blk) ↔ b ∈ w.used
  nodes : ∀ i, NodeOK E.c.k w.st E.L E.O E.G E.c (w.node i)
  slots : ∀ i, ∀ x ∈ (w.node i).tree, slotOf w.st x ≤ w.now
  hon : ∀ b B j, w.st b = some B → B.hdr.signer = .honest j → HonBlk E w.st w.now w.honestLog b B j

theorem WorldOK.good {w : World} (hw : WorldOK E w) {b : ℕ} {B : Block} (hb : w.st b = some B)
    (hB : IsHon B) : GoodAt E.c E.L E.O E.G w.st w.now b :=
  let ⟨j, hj⟩ := hB; (hw.hon b B j hb hj).good

theorem genesis_used {w : World} (hw : WorldOK E w) : genesisId ∈ w.used := by
  obtain ⟨g, hg, -, -⟩ := hw.store.gen
  exact (hw.used genesisId).1 ⟨g, hg⟩

/-- An honest block keeps its facts as the store grows by blocks that are not
its signer's at its slot, the log grows and the clock moves on. -/
theorem HonBlk.mono {st st' : Store} {t t' : ℕ} {lg lg' : List (ℕ × ℕ)} (hS : StoreOK st)
    (hx : StoreExt st st') (ht : t ≤ t') (hlg : ∀ p ∈ lg, p ∈ lg') {b j : ℕ} {B : Block}
    (hnew : ∀ b' B', st' b' = some B' → B'.hdr.signer = .honest j → B'.hdr.slot = B.hdr.slot →
      st b' = some B') (h : HonBlk E st t lg b B j) : HonBlk E st' t' lg' b B j :=
  ⟨h.good.mono hS hx ht, hlg _ h.log, h.node, h.online,
    fun b' B' hb' hj hs => h.uniq b' B' (hnew b' B' hb' hj hs) hj hs⟩

/-- Adding a block under a fresh ID extends the store and keeps it well formed. -/
theorem add_ok {w : World} (hw : WorldOK E w) (B : Block) (hfr : B.hdr.id ∉ w.used) :
    StoreExt w.st (w.add B).st ∧ StoreOK (w.add B).st ∧
      ∀ b, (∃ blk, (w.add B).st b = some blk) ↔ b ∈ (w.add B).used := by
  have hext : StoreExt w.st (w.add B).st := by
    intro b blk hb
    rw [add_st_of_ne (by rintro rfl; exact hfr ((hw.used _).1 ⟨blk, hb⟩))]; exact hb
  refine ⟨hext, ⟨fun b blk hb => ?_, ?_⟩, fun b => ?_⟩
  · rcases add_st_cases hb with ⟨rfl, rfl⟩ | hb
    · rfl
    · exact hw.store.idOK b blk hb
  · obtain ⟨g, hg, h1, h2⟩ := hw.store.gen
    exact ⟨g, hext _ _ hg, h1, h2⟩
  · simp only [World.add, List.mem_cons]
    rw [← hw.used b]
    by_cases hb : b = B.hdr.id <;> simp [hb]

theorem lead_ext {w : World} (hw : WorldOK E w) (i : ℕ) : StoreExt w.st (w.lead E i).st := by
  rcases lead_cases (E := E) w i with ⟨-, hL⟩ | ⟨C, -, hC, hL⟩ <;> rw [hL]
  · exact StoreExt.refl _
  · exact (add_ok hw C (by rw [(propose_id hC).1]; exact fresh_not_used w)).1

theorem init_ok (E : Env) : WorldOK E World.init := by
  have hst : World.init.st genesisId = some genesisBlock := by simp [World.init]
  have hone : ∀ b B, World.init.st b = some B → b = genesisId ∧ B = genesisBlock := by
    intro b B hb
    simp only [World.init] at hb
    split at hb
    · cases hb; exact ⟨‹_›, rfl⟩
    · simp at hb
  have hS : StoreOK World.init.st :=
    ⟨fun b blk hb => by obtain ⟨rfl, rfl⟩ := hone b blk hb; rfl, ⟨genesisBlock, hst, rfl, rfl⟩⟩
  have hgr : Rooted World.init.st genesisId := hS.rooted_gen
  refine ⟨hS, fun b => ?_, fun i => ?_, fun i x hx => ?_, fun b B j hb hj => ?_⟩
  · simp only [World.init, List.mem_singleton]
    exact ⟨fun ⟨blk, hb⟩ => (hone b blk hb).1, by rintro rfl; exact ⟨_, hst⟩⟩
  · simp only [World.init]
    refine ⟨?_, ?_, ?_, by simp, by simp, ?_, rfl⟩
    · intro y hy; simp at hy; subst hy; exact hgr
    · intro y hy; simp at hy; exact Or.inl hy
    · intro y hy; simp at hy; subst hy
      simp [parentOf, genesisBlock]
    · -- `B_imm` of the genesis chain is genesis
      have hmem := blockAtDepth_mem hS hgr E.c.k
      have : chainIds World.init.st genesisId = [genesisId] := by
        unfold chainIds; rw [chain_genesis hst rfl]; simp [genesisBlock]
      rw [this] at hmem; simp at hmem; exact hmem.symm
  · simp [World.init] at hx; subst hx; simp [World.init, slotOf, genesisBlock]
  · obtain ⟨-, rfl⟩ := hone b B hb; simp [genesisBlock] at hj

/-- A node of a well-formed world, as the start of processing blocks. -/
theorem WorldOK.foldInv {w : World} (hw : WorldOK E w) (i : ℕ) :
    FoldInv E.c E.L E.O E.G w.st w.now (height w.st (w.node i).cloc) (w.node i).bimm (w.node i) :=
  ⟨hw.nodes i, hw.slots i, le_rfl, self_mem_chainIds hw.store ((hw.nodes i).bimm_on_cloc hw.store).1⟩

/-! ## From a world to a later one -/

/-- **From a world to a later one.** -/
structure StepOK (E : Env) (w w' : World) : Prop where
  ok : WorldOK E w'
  ext : StoreExt w.st w'.st
  clock : w.now ≤ w'.now
  mono : ∀ j, height w.st (w.node j).cloc ≤ height w'.st (w'.node j).cloc
  bimm : ∀ j, (w.node j).bimm ∈ chainIds w'.st (w'.node j).bimm
  new : ∀ b B, w'.st b = some B → w.st b = none → IsHon B → w.now < B.hdr.slot

theorem stepOK_refl {w : World} (hw : WorldOK E w) : StepOK E w w :=
  ⟨hw, StoreExt.refl _, le_rfl, fun _ => le_rfl,
    fun j => self_mem_chainIds hw.store ((hw.nodes j).bimm_on_cloc hw.store).1,
    fun _ _ hb hn => (Option.some_ne_none _ (hb.symm.trans hn)).elim⟩

/-- Extending a step from `w` to `w₀` by a step to `w₁` that adds honest blocks
only with slots after `w`'s time. -/
theorem StepOK.extend {w w₀ w₁ : World} (h : StepOK E w w₀) (hw : WorldOK E w₁)
    (hx : StoreExt w₀.st w₁.st) (hc : w₀.now ≤ w₁.now)
    (hm : ∀ j, height w₀.st (w₀.node j).cloc ≤ height w₁.st (w₁.node j).cloc)
    (hb : ∀ j, (w₀.node j).bimm ∈ chainIds w₁.st (w₁.node j).bimm)
    (hn : ∀ b B, w₁.st b = some B → w₀.st b = none → IsHon B → w.now < B.hdr.slot) :
    StepOK E w w₁ := by
  refine ⟨hw, h.ext.trans hx, h.clock.trans hc, fun j => (h.mono j).trans (hm j), fun j => ?_,
    fun b B hb' hnb hB => ?_⟩
  · refine chainIds_trans hw.store ((hw.nodes j).bimm_on_cloc hw.store).1 (hb j) ?_
    rw [chainIds_ext hx ((h.ok.nodes j).bimm_on_cloc h.ok.store).1]; exact h.bimm j
  · cases h0 : w₀.st b with
    | none => exact hn b B hb' h0 hB
    | some B' =>
      obtain rfl : B' = B := Option.some_inj.1 ((hx b B' h0).symm.trans hb')
      exact h.new b B' h0 hnb hB

theorem StepOK.trans {w₁ w₂ w₃ : World} (h1 : StepOK E w₁ w₂) (h2 : StepOK E w₂ w₃) :
    StepOK E w₁ w₃ :=
  h1.extend h2.ok h2.ext h2.clock h2.mono h2.bimm
    fun b B hb hn hB => h1.clock.trans_lt (h2.new b B hb hn hB)

/-- An honest block of the later world with a slot up to the earlier world's time
was already there. -/
theorem StepOK.old {w w' : World} (h : StepOK E w w') {b : ℕ} {B : Block} (hb : w'.st b = some B)
    (hB : IsHon B) (hsl : B.hdr.slot ≤ w.now) : w.st b = some B := by
  cases h0 : w.st b with
  | none => have := h.new b B hb h0 hB; omega
  | some B' => exact (h.ext b B' h0).symm.trans hb

/-! ## The events -/

theorem deliver_ok (hord : E.OrderOK) {w : World} (hw : WorldOK E w) (i b : ℕ) :
    StepOK E w (w.step E (.deliver i b)) := by
  simp only [World.step]
  split
  · have key : ∀ j, NodeStep E.c E.L E.O E.G w.st w.now (w.node j) (if j = i then
        receive E.c w.st E.L E.O E.G E.fastPath (E.ord i) w.now (w.node i) b else w.node j) := by
      intro j; split
      · rename_i hj; subst hj
        exact receive_step hw.store (hw.nodes j) E.fastPath (E.ord j) (hord j) w.now b
      · exact .refl hw.store (hw.nodes j)
    exact ⟨⟨hw.store, hw.used, fun j => (key j).ok,
      fun j x hx => ((key j).tree x hx).elim (hw.slots j x) id, hw.hon⟩, StoreExt.refl _, le_rfl,
      fun j => (key j).mono, fun j => (key j).bimm,
      fun _ _ hb hn => (Option.some_ne_none _ (hb.symm.trans hn)).elim⟩
  · exact stepOK_refl hw

theorem create_ok {w : World} (hw : WorldOK E w) (B : Block) : StepOK E w (w.step E (.create B)) := by
  simp only [World.step]
  split
  · rename_i hc
    simp only [Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at hc
    have hnu : B.hdr.id ∉ w.used := by
      intro hm; have := List.contains_iff_mem.2 hm; simp_all
    obtain ⟨hext, hS', hused'⟩ := add_ok hw B hnu
    -- the new block is adversarial
    have hold : ∀ b C j, (w.add B).st b = some C → C.hdr.signer = .honest j → w.st b = some C :=
      fun b C j hb hj => (add_st_cases hb).resolve_left (by rintro ⟨-, rfl⟩; rw [hc.1] at hj; cases hj)
    refine ⟨⟨hS', hused', fun j => nodeOK_ext hext hw.store (hw.nodes j), fun j x hx => ?_,
      fun b C j hb hj => (hw.hon b C j (hold b C j hb hj) hj).mono hw.store hext le_rfl
        (fun _ hp => hp) (fun b' C' hb' hj' _ => hold b' C' j hb' hj')⟩, hext, le_rfl,
      fun j => (height_ext hext (hw.nodes j).cloc_rooted).ge, fun j => ?_,
      fun b C hb hn ⟨j, hj⟩ => by simp [hold b C j hb hj] at hn⟩
    · rw [slotOf_ext hext ((hw.nodes j).rooted x hx).exists_blk]; exact hw.slots j x hx
    · have hbr := ((hw.nodes j).bimm_on_cloc hw.store).1
      show _ ∈ chainIds (w.add B).st (w.node j).bimm
      rw [chainIds_ext hext hbr]; exact self_mem_chainIds hw.store hbr
  · exact stepOK_refl hw

/-- The clock moving on, at the start of a tick. -/
theorem tick0_ok {w : World} (hw : WorldOK E w) : StepOK E w { w with now := w.now + 1 } :=
  ⟨⟨hw.store, hw.used, hw.nodes, fun i x hx => (hw.slots i x hx).trans (Nat.le_succ _),
    fun b B j hb hj => (hw.hon b B j hb hj).mono hw.store (StoreExt.refl _) (Nat.le_succ _)
      (fun _ hp => hp) (fun _ _ hb' _ _ => hb')⟩, StoreExt.refl _, Nat.le_succ _, fun _ => le_rfl,
    fun j => self_mem_chainIds hw.store ((hw.nodes j).bimm_on_cloc hw.store).1,
    fun _ _ hb hn => (Option.some_ne_none _ (hb.symm.trans hn)).elim⟩

/-- **Induction over a tick.** A property of the nodes led so far and the world
that holds once the clock has moved on, and is kept by the lead step of every node
not led yet (whose state is still the one before the tick, and which has signed no
block added during the tick), holds after the tick. -/
theorem tick_induct (hnd : E.nodes.Nodup) {w : World} (P : List ℕ → World → Prop)
    (h0 : P [] { w with now := w.now + 1 })
    (hstep : ∀ l w₀ i, i ∈ E.nodes → i ∉ l → P l w₀ → w₀.now = w.now + 1 → w₀.node i = w.node i →
      (∀ b B, w₀.st b = some B → B.hdr.signer = .honest i → w.st b = some B) →
      P (i :: l) (w₀.lead E i)) :
    P E.nodes.reverse (w.step E .tick) := by
  simp only [World.step]
  suffices key : ∀ (r l : List ℕ) (w₀ : World), l.reverse ++ r = E.nodes → P l w₀ →
      w₀.now = w.now + 1 → (∀ i ∈ r, w₀.node i = w.node i) →
      (∀ i ∈ r, ∀ b B, w₀.st b = some B → B.hdr.signer = .honest i → w.st b = some B) →
      P (r.reverse ++ l) (r.foldl (World.lead E) w₀) by
    simpa using key E.nodes [] _ (by simp) h0 rfl (fun _ _ => rfl) (fun _ _ _ _ hb _ => hb)
  intro r
  induction r with
  | nil => intro l w₀ _ hP _ _ _; simpa using hP
  | cons i r ih =>
    intro l w₀ hl hP hnow hsame hsig
    have hnd' : (l.reverse ++ i :: r).Nodup := hl ▸ hnd
    have hil : i ∉ l := fun h => (List.nodup_append.1 hnd').2.2 i (List.mem_reverse.2 h) i
      List.mem_cons_self rfl
    have hir : i ∉ r := (List.nodup_cons.1 (List.nodup_append.1 hnd').2.1).1
    simp only [List.foldl_cons, List.reverse_cons, List.append_assoc, List.singleton_append]
    refine ih (i :: l) _ (by simpa using hl)
      (hstep l w₀ i (hl ▸ by simp) hil hP hnow (hsame i List.mem_cons_self)
        (hsig i List.mem_cons_self)) (by rw [lead_now, hnow])
      (fun j hj => by
        rw [lead_other w₀ (fun h => hir (by rw [← h]; exact hj))]
        exact hsame j (List.mem_cons_of_mem _ hj))
      (fun j hj b B hb hs => ?_)
    rcases lead_st hb with hb | ⟨-, hC⟩
    · exact hsig j (List.mem_cons_of_mem _ hj) b B hb hs
    · rw [(propose_id hC).2.1] at hs; cases hs; exact absurd hj hir

/-- Within a tick, a node that has not led yet holds no block from the current slot. -/
theorem tick_past {w w₀ : World} (hw : WorldOK E w) (h : StepOK E w w₀) (hnow : w₀.now = w.now + 1)
    {i : ℕ} (hsame : w₀.node i = w.node i) : ∀ x ∈ (w₀.node i).tree, slotOf w₀.st x < w₀.now := by
  intro x hx
  rw [hsame] at hx
  rw [slotOf_ext h.ext ((hw.nodes i).rooted x hx).exists_blk, hnow]
  exact Nat.lt_succ_of_le (hw.slots i x hx)

/-- **A lead step within a tick**, by a node that has not led yet: it adds at most
its own valid proposal for the new slot, and processes it. -/
theorem lead_ok (hA : Assm E) {w w₀ : World} (hw : WorldOK E w) (h : StepOK E w w₀)
    (hnow : w₀.now = w.now + 1) {i : ℕ} (hi : i ∈ E.nodes) (hsame : w₀.node i = w.node i)
    (hsig : ∀ b B, w₀.st b = some B → B.hdr.signer = .honest i → w.st b = some B) :
    StepOK E w (w₀.lead E i) := by
  have hw₀ := h.ok
  rcases lead_cases (E := E) w₀ i with ⟨-, hL⟩ | ⟨C, hio, hC, hL⟩
  · rw [hL]; exact h
  rw [hL]
  obtain ⟨hid, hCs, -, hsl⟩ := propose_id hC
  obtain ⟨hext, hS', hused'⟩ := add_ok hw₀ C (by rw [hid]; exact fresh_not_used w₀)
  have hC' : (w₀.add C).st C.hdr.id = some C := add_st_self w₀ C
  have hn : ∀ j, NodeOK E.c.k (w₀.add C).st E.L E.O E.G E.c (w₀.node j) :=
    fun j => nodeOK_ext hext hw₀.store (hw₀.nodes j)
  have hval := propose_header hw₀.store (hw₀.nodes i) hC (tick_past hw h hnow hsame) hA.sane hA.exec
    hS' hext hC' (fun h0 => fresh_not_used w₀ (h0 ▸ genesis_used hw₀))
  -- the earlier blocks signed by `i` are from before the tick
  have hsig' : ∀ b B, w₀.st b = some B → B.hdr.signer = .honest i → B.hdr.slot < w₀.now := by
    intro b B hb hj
    have := (hw.hon b B i (hsig b B hb hj) hj).good.2.1
    rw [slotOf_eq (hsig b B hb hj)] at this; omega
  -- the proposal is good
  have hT := accept_ok (hn i) hC' hval
  have hCT : C.hdr.id ∈ (w₀.node i).tree ++ [C.hdr.id] := List.mem_append_right _ (List.mem_singleton_self _)
  have hCgood : GoodAt E.c E.L E.O E.G (w₀.add C).st w₀.now C.hdr.id :=
    ⟨(hT _ hCT).1, by rw [slotOf_eq hC', hsl],
      fun x hx => (hT x (chainIds_closed hS' (fun y hy => (hT y hy).1) (fun y hy => (hT y hy).2.1)
        hCT x hx)).2.2⟩
  -- node `i` processes its block; the others keep their state
  have key : ∀ j, NodeStep E.c E.L E.O E.G (w₀.add C).st w₀.now (w₀.node j) (if j = i then
      onBlock E.c (w₀.add C).st E.L E.O E.G E.fastPath (E.ord i) (w₀.add C).now (w₀.node i) C
      else (w₀.add C).node j) := by
    intro j; split
    · rename_i hj; subst hj; exact onBlock_step hS' (hn j) E.fastPath (E.ord j) (hA.ord j) _ C hC'
    · exact .refl hS' (hn j)
  refine h.extend ⟨hS', hused', fun j => (key j).ok, fun j x hx => ?_, fun b B j hb hj => ?_⟩ hext
    le_rfl (fun j => ?_) (fun j => (key j).bimm) (fun b B hb hnb _ => ?_)
  · rcases (key j).tree x hx with hx | hx
    · rw [slotOf_ext hext ((hw₀.nodes j).rooted x hx).exists_blk]; exact hw₀.slots j x hx
    · exact hx
  · rcases add_st_cases hb with ⟨rfl, rfl⟩ | hb₀
    · rw [hCs] at hj; cases hj
      refine ⟨hCgood, by rw [hsl]; exact List.mem_cons_self, hi, by rw [hsl]; exact hio,
        fun b' B' hb' hj' hs => ?_⟩
      rcases add_st_cases hb' with ⟨rfl, -⟩ | hb'
      · rfl
      · have := hsig' b' B' hb' hj'; omega
    · refine (hw₀.hon b B j hb₀ hj).mono hw₀.store hext le_rfl (fun _ hp => List.mem_cons_of_mem _ hp)
        (fun b' B' hb' hj' hs => (add_st_cases hb').resolve_left ?_)
      rintro ⟨-, rfl⟩
      rw [hCs] at hj'; cases hj'
      have := hsig' b B hb₀ hj; omega
  · rw [← height_ext hext (hw₀.nodes j).cloc_rooted]; exact (key j).mono
  · rcases add_st_cases hb with ⟨-, rfl⟩ | hb₀
    · omega
    · simp [hb₀] at hnb

/-- **Every event** keeps the world well formed. -/
theorem step_ok (hA : Assm E) {w : World} (hw : WorldOK E w) : ∀ e, StepOK E w (w.step E e)
  | .tick => tick_induct hA.nodup (fun _ w₀ => StepOK E w w₀) (tick0_ok hw)
      fun _ _ _ hi _ h hnow hsame hsig => lead_ok hA hw h hnow hi hsame hsig
  | .deliver i b => deliver_ok hA.ord hw i b
  | .create B => create_ok hw B

/-- **Every execution keeps the world well formed**, along the relation between a
world and a later one. -/
theorem run_ok (hA : Assm E) (es : List Event) {w : World} (hw : WorldOK E w) :
    StepOK E w (run E w es) :=
  foldl_inv (P := StepOK E w) (fun _ h e _ => h.trans (step_ok hA h.ok e)) w (stepOK_refl hw)

/-! ## What a tick adds -/

/-- **What a tick adds**: honest blocks for the new slot, each signed by a node
online at it and built on that node's local chain as it stood before the tick. -/
theorem tick_new (hnd : E.nodes.Nodup) (w : World) :
    ∀ b B, (w.step E .tick).st b = some B → w.st b = none →
      ∃ j ∈ E.nodes, B.hdr.signer = .honest j ∧ B.hdr.parent = (w.node j).cloc ∧
        B.hdr.slot = w.now + 1 ∧ E.online j (w.now + 1) = true := by
  refine tick_induct hnd (fun _ w₀ => ∀ b B, w₀.st b = some B → w.st b = none →
      ∃ j ∈ E.nodes, B.hdr.signer = .honest j ∧ B.hdr.parent = (w.node j).cloc ∧
        B.hdr.slot = w.now + 1 ∧ E.online j (w.now + 1) = true)
    (fun _ _ hb hn => (Option.some_ne_none _ (hb.symm.trans hn)).elim) ?_
  intro _ w₀ i hi _ hP hnow hsame _ b B hb hn
  rcases lead_st hb with hb | ⟨hio, hC⟩
  · exact hP b B hb hn
  · obtain ⟨-, hs, hp, hsl⟩ := propose_id hC
    exact ⟨i, hi, hs, hp.trans (by rw [hsame]), hsl.trans hnow, hnow ▸ hio⟩

/-- **After a tick, anything new in a node's tree is no higher than its new local
chain** (the only new block is its own proposal, which it adopts). -/
theorem tick_tree (hA : Assm E) {w : World} (hw : WorldOK E w) :
    ∀ i, ∀ x ∈ ((w.step E .tick).node i).tree, x ∉ (w.node i).tree →
      height (w.step E .tick).st x ≤ height (w.step E .tick).st ((w.step E .tick).node i).cloc := by
  refine (tick_induct hA.nodup (fun _ w₀ => StepOK E w w₀ ∧ ∀ i, ∀ x ∈ (w₀.node i).tree,
      x ∉ (w.node i).tree → height w₀.st x ≤ height w₀.st (w₀.node i).cloc)
    ⟨tick0_ok hw, fun _ x hx hxn => absurd hx hxn⟩ ?_).2
  intro _ w₀ i hi _ ⟨h, hR⟩ hnow hsame hsig
  have hw₀ := h.ok
  refine ⟨lead_ok hA hw h hnow hi hsame hsig, fun j x hx hxn => ?_⟩
  rcases lead_cases (E := E) w₀ i with ⟨-, hL⟩ | ⟨C, -, hC, hL⟩
  · rw [hL] at hx ⊢; exact hR j x hx hxn
  rw [hL] at hx ⊢
  obtain ⟨hid, -, hpar, -⟩ := propose_id hC
  obtain ⟨hext, hS', -⟩ := add_ok hw₀ C (by rw [hid]; exact fresh_not_used w₀)
  have hC' : (w₀.add C).st C.hdr.id = some C := add_st_self w₀ C
  simp only at hx ⊢
  by_cases hji : j = i
  · subst hji
    rw [if_pos rfl] at hx ⊢
    -- node `j` (= `i`) processed its own block
    have hn := nodeOK_ext hext hw₀.store (hw₀.nodes j)
    rcases onBlock_tree hn.rule E.fastPath (E.ord j) _ hC' x hx with hx | ⟨rfl, -⟩
    · rw [hsame] at hx; exact absurd hx hxn
    have hnewC : C.hdr.id ∉ (w₀.node j).tree := fun hin =>
      fresh_not_used w₀ (hid ▸ (hw₀.used _).1 ((hw₀.nodes j).rooted _ hin).exists_blk)
    exact own_adopt hS' hn E.fastPath (E.ord j) (hA.ord j) _ C hC' hpar hnewC
      (propose_header hw₀.store (hw₀.nodes j) hC (tick_past hw h hnow hsame) hA.sane hA.exec hS'
        hext hC' (fun h0 => fresh_not_used w₀ (h0 ▸ genesis_used hw₀)))
  · rw [if_neg hji] at hx ⊢
    rw [show (w₀.add C).node j = w₀.node j from rfl, height_ext hext ((hw₀.nodes j).rooted x hx),
      height_ext hext (hw₀.nodes j).cloc_rooted]
    exact hR j x hx hxn

/-! ## Indexed executions -/

variable (E) (es : List Event)

/-- The world after the first `n` events. -/
def wAt (n : ℕ) : World := run E World.init (es.take n)

theorem wAt_zero : wAt E es 0 = World.init := by simp [wAt, run]

theorem wAt_succ {n : ℕ} (hn : n < es.length) : wAt E es (n + 1) = (wAt E es n).step E es[n] := by
  simp only [wAt, run]
  rw [List.take_succ, List.getElem?_eq_getElem hn, Option.toList_some, List.foldl_append]
  rfl

theorem wAt_length : wAt E es es.length = run E World.init es := by simp [wAt]

theorem trace_getElem : ∀ (es : List Event) (w : World) (n : ℕ), n ≤ es.length →
    (trace E w es)[n]? = some (run E w (es.take n)) := by
  intro es
  induction es with
  | nil => intro w n hn; simp at hn; subst hn; simp [trace, run]
  | cons e es ih =>
    intro w n hn
    rcases n with _ | n
    · simp [trace, run]
    · simp only [trace, List.getElem?_cons_succ, List.take_succ_cons]
      rw [ih _ n (by simpa using hn)]
      simp [run]

variable {E es}

/-- How an event moves the clock. -/
theorem step_now (w : World) (e : Event) :
    (w.step E e).now = w.now + (match e with | .tick => 1 | _ => 0) := by
  cases e with
  | tick =>
    simp only [World.step]
    exact foldl_inv (P := fun w' : World => w'.now = w.now + 1)
      (fun _ h i _ => (lead_now _ i).trans h) _ rfl
  | deliver i b => simp only [World.step]; split <;> rfl
  | create B => simp only [World.step]; split <;> rfl

theorem now_mono {n m : ℕ} (hnm : n ≤ m) (hm : m ≤ es.length) : (wAt E es n).now ≤ (wAt E es m).now := by
  induction m with
  | zero => have : n = 0 := by omega
            subst this; rfl
  | succ m ih =>
    rcases Nat.eq_or_lt_of_le hnm with h | h
    · rw [h]
    · rw [wAt_succ E es (by omega), step_now]
      have := ih (by omega) (by omega); omega

theorem wAt_ok (hA : Assm E) (n : ℕ) : WorldOK E (wAt E es n) := (run_ok hA _ (init_ok E)).ok

/-- **Any two points of an execution**, the later world from the earlier one. -/
theorem wAt_le (hA : Assm E) {n m : ℕ} (hnm : n ≤ m) : StepOK E (wAt E es n) (wAt E es m) := by
  have hd : (es.take m).take n = es.take n := by rw [List.take_take, min_eq_left hnm]
  unfold wAt
  conv_rhs => rw [← List.take_append_drop n (es.take m), hd]
  simp only [run, List.foldl_append]
  exact run_ok hA _ (wAt_ok hA n)

theorem store_mono (hA : Assm E) {n m : ℕ} (hnm : n ≤ m) :
    StoreExt (wAt E es n).st (wAt E es m).st := (wAt_le hA hnm).ext

theorem store_genesis (hA : Assm E) (n : ℕ) : (wAt E es n).st genesisId = some genesisBlock :=
  store_mono hA (Nat.zero_le n) _ _ (by rw [wAt_zero]; simp [World.init])

/-- **An honest block new at an event** was made by a tick, for the new slot, on the
local chain of a node online at it. -/
theorem new_hon (hA : Assm E) {n : ℕ} (hn : n < es.length) {b : ℕ} {B : Block}
    (hb : (wAt E es (n + 1)).st b = some B) (hold : (wAt E es n).st b = none) (hB : IsHon B) :
    es[n] = .tick ∧ ∃ j ∈ E.nodes, B.hdr.parent = ((wAt E es n).node j).cloc ∧
      B.hdr.slot = (wAt E es n).now + 1 ∧ E.online j ((wAt E es n).now + 1) = true := by
  have hlt := (wAt_le (es := es) hA (Nat.le_succ n)).new b B hb hold hB
  have hle := ((wAt_ok (es := es) hA (n + 1)).good hb hB).2.1
  rw [slotOf_eq hb, wAt_succ E es hn, step_now] at hle
  rw [wAt_succ E es hn] at hb
  cases hev : es[n] with
  | tick =>
    rw [hev] at hb
    obtain ⟨j, hj, -, hpar, hsl, hjon⟩ := tick_new hA.nodup _ b B hb hold
    exact ⟨rfl, j, hj, hpar, hsl, hjon⟩
  | deliver _ _ | create _ => rw [hev] at hle; simp only [Nat.add_zero] at hle; omega

end Cryptarchia
