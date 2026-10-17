module

public import Cryptarchia.Proof.Canon
public import Cryptarchia.Proof.LotteryG
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
import Mathlib.Tactic.ENatToNat
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
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# The lottery string over many epochs

Each slot's lottery runs under the **canonical state** of its epoch
(`CS`: the genesis state for epoch 0, otherwise the state derived on the
canonical prefix `CP E.c.fix e`). Given the settlement invariant up to a horizon `H'`
that covers the fixing point of every epoch starting by `Hs`:

* every honest node leads under the canonical state at every tick up to `Hs`
  (`node_state`), because its local chain carries the canonical prefix;
* every honest block with slot up to `Hs` is consistent (`hon_cons_upto`);
* every adversarial block of the consistent tree is validated under the
  canonical state (`advStatesOK_E`, at every slot: consistency is definitional).
-/

@[expose] public section

namespace Cryptarchia

open Settle

/-- The genesis epoch state. -/
def es0 (E : Env) : EpochState := epochState E.c E.L E.O E.G [genesisBlock] 0

/-- Every chain of an execution derives the genesis epoch state for the first epoch. -/
theorem epochState_es0 {E : Env} {st : Store} (hS : StoreOK st)
    (hg : st genesisId = some genesisBlock) {b : ℕ} (hb : Rooted st b) :
    epochState E.c E.L E.O E.G (chainUp st b) 0 = es0 E := by
  rw [epochState_zero hS hb hS.rooted_gen]
  unfold es0
  congr 1
  unfold chainUp; rw [chain_genesis hg rfl]; rfl

variable (E : Env) (es : List Event)

/-- **The canonical epoch state of epoch `e`.** -/
noncomputable def CS (e : ℕ) : EpochState :=
  if e = 0 then es0 E else epochState E.c E.L E.O E.G (CP E es e) e

/-- The state each slot's lottery runs under. -/
noncomputable def σE (t : ℕ) : EpochState := CS E es (E.c.epochOf t)

variable {E es}

theorem prefixBelow_snoc (C : List Block) {B : Block} {s : ℕ} (hB : B.hdr.id ≠ genesisId)
    (hs : s ≤ B.hdr.slot) : prefixBelow (C ++ [B]) s = prefixBelow C s := by
  unfold prefixBelow
  rw [List.filter_append]
  simp [hB]; omega

theorem epochStart_epochOf_le (c : Config) (t : ℕ) : c.epochStart (c.epochOf t) ≤ t := by
  unfold Config.epochStart Config.epochOf; exact Nat.div_mul_le_self _ _

/-- An epoch state derived on a chain with the canonical prefix is canonical. -/
theorem state_of_prefix (hA : Assm E) {C : List Block} {e : ℕ} (he : 1 ≤ e)
    (hC : prefixBelow C (E.c.cut e) = CP E es e) : epochState E.c E.L E.O E.G C e = CS E es e := by
  unfold CS
  rw [if_neg (by omega), ← epochState_cut hA.sane C he, hC]

variable {W : ℕ → ℕ} {e : ℕ → ℕ} {H' : ℕ}

/-- **Honest chains carry the canonical prefix** of every epoch fixed within the
horizon of the invariant. -/
theorem canon_node (hA : Assm E)
   
    (hG : GoodCondW E es (Cons E es) W e H') (hGr : Growth E es e H') (hH'N : H' ≤ (wF E es).now)
    {ep : ℕ} (hep : 1 ≤ ep) (hfixH : E.c.fix ep ≤ H') {n : ℕ} (hn : n ≤ es.length) (hFn : E.c.fix ep ≤ (wAt E es n).now)
    {i : ℕ} (hi : i ∈ E.nodes) (hio : E.online i (wAt E es n).now = true) {cl : ℕ}
    (hcl : Rooted (wAt E es n).st cl)
    (hz : ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st cl) :
    prefixBelow (chainUp (wF E es).st cl) (E.c.cut ep) = CP E es ep := by
  have hK := cons_ok hA hG hGr
  have hreach : E.c.fix ep ≤ (wF E es).now := by omega
  obtain ⟨hmle, hnow, -⟩ := idxE_spec (e := ep) hreach
  have hDm : ∀ m ≤ idxE E es ep, InvAt E es (Cons E es) m := fun m hm =>
    main hA hK hG m (by omega) (le_trans (now_mono (E := E) (es := es) hm hmle) (by omega))
  obtain ⟨hKb, hKc⟩ := bimm_cloc_of hA hmle
    (cons_step hA hG hGr _ hmle (by omega) (fun m hm => hDm m hm.le))
  exact canon_of hA hG hGr hep hfixH hreach hDm hKb hKc hn (idxE_le hn hFn) hi hio hcl hz

/-- **Every honest leader runs the canonical lottery** at every tick up to `Hs`. -/
theorem node_state (hA : Assm E)
   
    (hG : GoodCondW E es (Cons E es) W e H') (hGr : Growth E es e H') (hH'N : H' ≤ (wF E es).now)
    {Hs : ℕ} (hcov : ∀ ep, 1 ≤ ep → E.c.epochStart ep ≤ Hs → E.c.fix ep ≤ H')
    {n : ℕ} (hn : n ≤ es.length) (htH : (wAt E es n).now + 1 ≤ Hs) {j : ℕ} (hj : j ∈ E.nodes)
    (hjo : E.online j ((wAt E es n).now + 1) = true) :
    epochState E.c E.L E.O E.G (chainUp (wAt E es n).st ((wAt E es n).node j).cloc)
      (E.c.epochOf ((wAt E es n).now + 1)) = σE E es ((wAt E es n).now + 1) := by
  have hw := wAt_ok (es := es) hA n
  have hcr := (hw.nodes j).cloc_rooted
  unfold σE
  set t := (wAt E es n).now + 1
  rcases Nat.eq_zero_or_pos (E.c.epochOf t) with h0 | h1
  · rw [h0, epochState_es0 hw.store (store_genesis hA n) hcr]; simp [CS]
  · have hext := store_mono (m := es.length) (es := es) hA hn
    have hst := epochStart_epochOf_le E.c t
    have hfix2 := (hA.sane.fix_ok _ h1).2
    rw [← chainUp_ext hext hcr]
    apply state_of_prefix hA h1
    exact canon_node hA hG hGr hH'N h1 (hcov _ h1 (by omega)) hn (by omega) hj
      (hA.crash j _ _ (Nat.le_succ _) hjo) hcr ((hw.nodes j).bimm_on_cloc hw.store).2

/-- **Honest blocks are consistent**, up to `Hs`. -/
theorem hon_cons_upto (hA : Assm E)
   
    (hG : GoodCondW E es (Cons E es) W e H') (hGr : Growth E es e H') (hH'N : H' ≤ (wF E es).now)
    {Hs : ℕ} (hcov : ∀ ep, 1 ≤ ep → E.c.epochStart ep ≤ Hs → E.c.fix ep ≤ H') :
    ∀ n ≤ es.length, ∀ b B, (wAt E es n).st b = some B → IsHon B → B.hdr.slot ≤ Hs → Cons E es b := by
  have hS := (wAt_ok (es := es) hA es.length).store
  intro n
  induction n with
  | zero =>
    intro _ b B hb hBh _
    rw [wAt_zero] at hb
    simp only [World.init] at hb
    split at hb
    · cases hb; obtain ⟨j, hj⟩ := hBh; simp [genesisBlock] at hj
    · simp at hb
  | succ n ih =>
    intro hn b B hb hBh hBs
    have hnl : n < es.length := by omega
    by_cases hold : (wAt E es n).st b = none
    · -- a block created by a tick, on a node's local chain
      obtain ⟨-, j, hj, hpar, hsl, hjon⟩ := new_hon hA hnl hb hold hBh
      have hext := store_mono (es := es) hA hn
      have hbF := hext b B hb
      have hb0 : b ≠ genesisId := fun h0 => by rw [h0, store_genesis hA n] at hold; cases hold
      obtain ⟨B', hB', hpr, hps⟩ := (((wAt_ok (es := es) hA (n + 1)).good hb hBh).1.mono hext).inv hb0
      rw [hbF] at hB'; cases hB'
      intro ep hep hs
      rw [slotOf_eq hbF] at hs
      rw [chainUp_step hbF hb0 hpr hps, prefixBelow_snoc _ (by rw [hS.idOK _ _ hbF]; exact hb0)
        (le_trans (cut_le_start hA.sane hep) hs), hpar]
      have hwn := wAt_ok (es := es) hA n
      have hfix2 := (hA.sane.fix_ok ep hep).2
      exact canon_node hA hG hGr hH'N hep (hcov ep hep (by omega)) hnl.le (by omega) hj
        (hA.crash j _ _ (Nat.le_succ _) hjon) (hwn.nodes j).cloc_rooted ((hwn.nodes j).bimm_on_cloc hwn.store).2
    · obtain ⟨B', hB'⟩ := Option.ne_none_iff_exists'.1 hold
      obtain rfl : B' = B := Option.some_inj.1 ((store_mono hA (Nat.le_succ n) b B' hB').symm.trans hb)
      exact ih (by omega) b B' hB' hBh hBs

/-- **Adversarial blocks of the consistent tree run the canonical lottery.** -/
theorem advStatesOK_E (hA : Assm E) : AdvStatesOK E es (Cons E es) (σE E es) := by
  intro v hv B hB _
  have hwF := wAt_ok (es := es) hA es.length
  have hS := hwF.store
  obtain ⟨hvu, ⟨hr, hsN, -⟩⟩ := mem_stree.1 hv
  have hKv := (mem_FTused.1 hvu).2
  have hpr : Rooted (wF E es).st B.hdr.parent := by
    have := hr.parent_rooted hS.genSelf; rwa [parentOf_eq hB] at this
  unfold σE
  rcases Nat.eq_zero_or_pos (E.c.epochOf B.hdr.slot) with h0 | h1
  · rw [h0, epochState_es0 hS (store_genesis hA es.length) hpr]; simp [CS]
  · apply state_of_prefix hA h1
    have hv0 : v ≠ genesisId := by
      intro h0; subst h0
      have hg := store_genesis (E := E) (es := es) hA es.length
      rw [hB] at hg; cases hg
      simp [genesisBlock, Config.epochOf] at h1
    obtain ⟨B', hB', hpr', hps⟩ := hr.inv hv0
    rw [hB] at hB'; cases hB'
    have hs : E.c.epochStart (E.c.epochOf B.hdr.slot) ≤ slotOf (wF E es).st v := by
      rw [slotOf_eq hB]; exact epochStart_epochOf_le E.c _
    have := hKv _ h1 hs
    rw [chainUp_step hB hv0 hpr' hps,
      prefixBelow_snoc _ (by rw [hS.idOK _ _ hB]; exact hv0)
        (le_trans (cut_le_start hA.sane h1) (by rw [slotOf_eq hB] at hs; exact hs))] at this
    exact this

/-- **Weak domination by the multi-epoch lottery string up to `Hs`.** -/
theorem advLeW_lotE (hA : Assm E)
   
    (hG : GoodCondW E es (Cons E es) W e H') (hGr : Growth E es e H') (hH'N : H' ≤ (wF E es).now)
    {Hs : ℕ} (hcov : ∀ ep, 1 ≤ ep → E.c.epochStart ep ≤ Hs → E.c.fix ep ≤ H') (hHs : Hs ≤ (wF E es).now) :
    AdvLeW Hs (WS E es (Cons E es)) (lotStrS E (σE E es) (lateAt E es)) :=
  advLeW_upto hA (fun n hn _ htH j hj hjo => node_state hA hG hGr hH'N hcov hn.le htH hj hjo)
    (fun b B hb hBh hBs => hon_cons_upto hA hG hGr hH'N hcov es.length le_rfl b B hb hBh hBs)
    (advStatesOK_E hA) hHs

end Cryptarchia
