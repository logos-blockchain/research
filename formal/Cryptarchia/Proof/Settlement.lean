module

public import Cryptarchia.Proof.Main
import Cryptarchia.Proof.NodeStep
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
import Std.Tactic.BVDecide.Normalize.BitVec
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# Cryptarchia settlement theorems

* `bimm_persist` (every execution): a node's latest immutable block `B_imm`
  never reverts: each later `B_imm` of the node descends from it (`StepOK.bimm`).
  This is what the online rule's `k`-deep rejection and pruning are designed to give.
* `agree_now` (on the good event): at every point, any two honest nodes' local
  chains meet within `k` blocks below each, and each node's `B_imm` is on every
  honest node's local chain.
* `bimm_final` (on the good event): **a block that any honest node has committed
  as immutable is on every honest node's local chain at every later point.**
  This is Cryptarchia's `k`-deep finality.
-/

@[expose] public section

namespace Cryptarchia

open Settle

variable {c : Config} {L : Ledger} {O : Oracle} {G : Genesis} {st : Store}

variable {E : Env} {es : List Event} {K : ℕ → Prop}

/-- **`B_imm` never reverts**, along the whole execution, for every node. -/
theorem bimm_persist (hA : Assm E) (i : ℕ) {n n' : ℕ} (hnn : n ≤ n') :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n').st ((wAt E es n').node i).bimm :=
  (wAt_le hA hnn).bimm i

/-- Before the first slot, every honest node is still on genesis. -/
theorem cloc_genesis_at_zero (hA : Assm E) {n : ℕ} (hn : n ≤ es.length) (h0 : (wAt E es n).now = 0)
    (i : ℕ) : ((wAt E es n).node i).cloc = genesisId := by
  have hw := wAt_ok (es := es) hA n
  by_contra hne
  have hin := (hw.nodes i).cloc
  have hsl := hw.slots i _ hin
  obtain ⟨blk, hbk, -, hs⟩ := ((hw.nodes i).rooted _ hin).inv hne
  rw [slotOf_eq hbk, h0] at hsl; omega

/-- **Agreement at a point**, from the invariant there: node `i`'s `B_imm` is on
node `j`'s local chain. -/
theorem agree_of (hA : Assm E) (hK : KBase E es K) {W : ℕ → ℕ} {e : ℕ → ℕ} {H : ℕ} (hG : GoodCondW E es K W e H)
    {n : ℕ} (hn : n ≤ es.length) (hnH : (wAt E es n).now ≤ H)
    (hD : DomAt (E := E) (es := es) (K := K) n ((wAt E es n).now - E.Δ - 1))
    (hH : HonAt (E := E) (es := es) (K := K) n) {i j : ℕ} (hi : i ∈ E.nodes) (hj : j ∈ E.nodes)
    (hio : E.online i (wAt E es n).now = true) (hjo : E.online j (wAt E es n).now = true)
    (hKi : K ((wAt E es n).node i).cloc) (hKj : K ((wAt E es n).node j).cloc) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st ((wAt E es n).node j).cloc := by
  have hw := wAt_ok (es := es) hA n
  have hS := hw.store
  have hext := store_mono (m := es.length) (es := es) hA hn
  have hci := (hw.nodes i).cloc_rooted
  have hcj := (hw.nodes j).cloc_rooted
  rcases Nat.eq_zero_or_pos (wAt E es n).now with h0 | hpos
  · rw [cloc_genesis_at_zero hA hn h0 j, (hw.nodes i).bimm, cloc_genesis_at_zero hA hn h0 i]
    have hmem := blockAtDepth_mem hS hS.rooted_gen E.c.k
    have hgen : chainIds (wAt E es n).st genesisId = [genesisId] := by
      obtain ⟨g, hg, hs, -⟩ := hS.gen
      unfold chainIds; rw [chain_genesis hg hs]; simp [hS.idOK _ _ hg]
    rw [hgen] at hmem ⊢; exact hmem
  obtain ⟨k, hk1, hk2⟩ := phase_of hG.e0 hG.mono hG.unb hpos
  have hNF : (wAt E es n).now ≤ (wF E es).now := now_mono hn le_rfl
  have hgi := goodAt_FT hA hS hext hNF (tree_good hS (hw.nodes i) (hw.slots i) (hw.nodes i).cloc) hKi
  have hgj := goodAt_FT hA hS hext hNF (tree_good hS (hw.nodes j) (hw.slots j) (hw.nodes j).cloc) hKj
  have hhd : ∀ l ∈ E.nodes, E.online l (wAt E es n).now = true →
      (FT E es K).hd (e k - E.Δ) ≤ height (wF E es).st ((wAt E es n).node l).cloc :=
    fun l hl hlo => le_trans (FT_hd_mono (by omega)) (hD l hl hlo)
  obtain ⟨x, hx1, hx2, hx3⟩ := nearAt hA hK hG hpos hNF hnH (A2_of_Hon hA hn hH) ⟨hk1, hk2⟩ hgi hgj
    (by rw [slotOf_ext hext hci.exists_blk]; exact hw.slots i _ (hw.nodes i).cloc)
    (by rw [slotOf_ext hext hcj.exists_blk]; exact hw.slots j _ (hw.nodes j).cloc)
    (hhd i hi hio) (hhd j hj hjo)
  rw [chainIds_ext hext hci] at hx1
  rw [chainIds_ext hext hcj] at hx2
  have hxr := (anc_height hS hci hx1).1
  rw [height_ext hext hci, height_ext hext hxr] at hx3
  rw [(hw.nodes i).bimm]
  exact chainIds_trans hS hcj hx2 (bimm_anc hS hci hx1 hx3)

/-- A node's local chain satisfies the block predicate at every point. -/
theorem cloc_K (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {W : ℕ → ℕ} {e : ℕ → ℕ} (hG : GoodCondW E es K W e H)
    {n : ℕ} (hn : n ≤ es.length) (hnH : (wAt E es n).now ≤ H) {i : ℕ} (hi : i ∈ E.nodes)
    (hio : E.online i (wAt E es n).now = true) : K ((wAt E es n).node i).cloc := by
  have hw := wAt_ok (es := es) hA n
  exact hK.step n hn hnH (fun m hm => main hA hK hG m (by omega)
    (le_trans (now_mono (E := E) (es := es) hm.le hn) hnH)) i hi hio _
    (hw.nodes i).cloc_rooted (hw.slots i _ (hw.nodes i).cloc)
    ((hw.nodes i).bimm_on_cloc hw.store).2

/-- **Agreement at every point.** Each honest node's `B_imm` is on every honest
node's local chain. -/
theorem agree_now (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {W : ℕ → ℕ} {e : ℕ → ℕ} (hG : GoodCondW E es K W e H)
    {n : ℕ} (hn : n ≤ es.length) (hnH : (wAt E es n).now ≤ H) {i j : ℕ} (hi : i ∈ E.nodes)
    (hj : j ∈ E.nodes) (hio : E.online i (wAt E es n).now = true) (hjo : E.online j (wAt E es n).now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st ((wAt E es n).node j).cloc :=
  agree_of hA hK.toKBase hG hn hnH (main hA hK hG n hn hnH).1 (main hA hK hG n hn hnH).2 hi hj hio hjo
    (cloc_K hA hK hG hn hnH hi hio) (cloc_K hA hK hG hn hnH hj hjo)

/-- **`k`-deep finality.** A block that an honest node has committed as immutable
(`B_imm`) is on every honest node's local chain at every later point of the
execution. -/
theorem bimm_final (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {W : ℕ → ℕ} {e : ℕ → ℕ} (hG : GoodCondW E es K W e H)
    {n n' : ℕ}
    (hnn : n ≤ n') (hn' : n' ≤ es.length) (hnH : (wAt E es n').now ≤ H) {i j : ℕ} (hi : i ∈ E.nodes)
    (hj : j ∈ E.nodes) (hio : E.online i (wAt E es n').now = true) (hjo : E.online j (wAt E es n').now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n').st ((wAt E es n').node j).cloc := by
  have hw := wAt_ok (es := es) hA n'
  exact chainIds_trans hw.store (hw.nodes j).cloc_rooted (agree_now hA hK hG hn' hnH hi hj hio hjo)
    (bimm_persist hA i hnn)

end Cryptarchia
