module

public import Cryptarchia.Prob.TSIRO
import Cryptarchia.Proof.NodeStep
import Cryptarchia.Proof.Honest
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
import Cryptarchia.Proof.Signers

/-!
# The canonical chain's occupied slots are lottery wins (`hhi`)

The stake estimate counts the distinct slots of the canonical chain's blocks in an
epoch's window, and of the uncles they carry (`occupied`). Each such slot other than
genesis is occupied in the lottery under the canonical state (`occupied_le_wcnt`):
every counted block and uncle carries a Proof of Leadership that verifies against
the epoch state derived on the block's parent chain, which below the cut is the
canonical prefix (given consistent canonical prefixes, `hcons`); its winning note is
the adversary's or an honest node's, and an honest signer was online at the slot
(`signOK_all`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open Cryptarchia Finset

variable {E : Env} {es : List Event}

theorem idxE_le_length (e : ℕ) : idxE E es e ≤ es.length := by
  classical
  exact Nat.find_min' (⟨es.length, Or.inl rfl⟩ : ∃ n, n = es.length ∨ E.c.fix e ≤ (wAt E es n).now) (Or.inl rfl)

/-- **The canonical chain is valid.** Epoch `e`'s canonical prefix is cut from a
chain rooted in the final store whose every block passes `validCore` there. -/
theorem cp_good (hA : Assm E) (e : ℕ) :
    ∃ b, Rooted (wF E es).st b ∧ CP E es e = prefixBelow (chainUp (wF E es).st b) (E.c.cut e) ∧
      ∀ x ∈ chainIds (wF E es).st b, x = genesisId ∨
        ∃ B, (wF E es).st x = some B ∧ validCore E.c (wF E es).st E.L E.O E.G B = true := by
  set n := idxE E es e
  have hw := wAt_ok (es := es) hA.ord n
  have hs := hw.nodes (i0 E es e)
  obtain ⟨hbr, hbc⟩ := hs.bimm_on_cloc hw.store
  set b := ((wAt E es n).node (i0 E es e)).bimm
  have hgood : GoodAt E.c E.L E.O E.G (wAt E es n).st (slotOf (wAt E es n).st b) b := by
    refine ⟨hbr, le_rfl, fun x hx => ?_⟩
    have hxc := chainIds_trans hw.store (hs.rooted _ hs.cloc) hbc hx
    exact hs.valid x (chainIds_closed hw.store hs.rooted hs.closed hs.cloc x hxc)
  have hext := store_mono (es := es) hA.ord (idxE_le_length (E := E) (es := es) e)
  obtain ⟨hr, -, hv⟩ := GoodAt.mono hw.store hext le_rfl hgood
  exact ⟨b, hr, rfl, hv⟩

/-- **The state an in-window canonical block was validated under is canonical.** -/
theorem state_par (hA : Assm E) {e : ℕ} {b : ℕ} (hb : Rooted (wF E es).st b)
    (hCP : CP E es (e + 1) = prefixBelow (chainUp (wF E es).st b) (E.c.cut (e + 1)))
    (hcons : 1 ≤ e → prefixBelow (CP E es (e + 1)) (E.c.cut e) = CP E es e)
    {B : Block} (hBid : B.hdr.id ∈ chainIds (wF E es).st b) (hB : (wF E es).st B.hdr.id = some B)
    (hB0 : B.hdr.id ≠ genesisId) (hsl : E.c.epochStart e ≤ B.hdr.slot) :
    epochState E.c E.L E.O E.G (chainUp (wF E es).st B.hdr.parent) e = CS E es e := by
  have hS := (wAt_ok (es := es) hA.ord es.length).store
  have hBr := (anc_height hS hb hBid).1
  obtain ⟨B', hB', hpar, hpsl⟩ := hBr.inv hB0
  rw [hB] at hB'; cases hB'
  rcases Nat.eq_zero_or_pos e with h0 | he
  · subst h0
    rw [epochState_es0 hS (store_genesis hA.ord _) hpar]
    simp [CS]
  · apply state_of_prefix hA he
    have hce : E.c.cut e ≤ E.c.epochStart e := cut_le_start hA.sane he
    have hcc : E.c.cut e ≤ E.c.cut (e + 1) := by
      unfold Config.cut
      have := epochStart_mono (c := E.c) (show e - 1 ≤ e + 1 - 1 by omega)
      omega
    rw [← hcons he, hCP, prefixBelow_prefixBelow _ hcc,
      prefixBelow_common hS hb hBid (by rw [slotOf_eq hB]; omega),
      chainUp_step hB hB0 hpar hpsl, prefixBelow_snoc _ hB0 (by omega)]

/-- **A verified header is a lottery win.** A header whose Proof of Leadership
verifies under the canonical state of its slot, and that is a stored block's header,
makes its slot occupied in the lottery under that state. -/
theorem occ_of_header (hA : Assm E) {h : Header} {C P : List Block}
    (hpol : polValid E.c E.L E.O E.G C P h = true)
    (hst : epochState E.c E.L E.O E.G C (E.c.epochOf h.slot) = σE E es h.slot)
    (hgen : genuine (wF E es).st h = true) :
    occA (slotOut E h.slot (σE E es h.slot) (fun η id => E.O.ticket η h.slot id)) := by
  unfold polValid at hpol
  rw [hst] at hpol
  simp only [List.any_eq_true, decide_eq_true_eq] at hpol
  obtain ⟨n, hn, hcond⟩ := hpol
  set s := σE E es h.slot
  unfold occA slotOut enc
  cases hsig : h.signer with
  | adv =>
    right
    show advW E.c s (fun η id => E.O.ticket η h.slot id) = true
    unfold advW
    simp only [List.any_eq_true, Bool.and_eq_true, decide_eq_true_eq]
    exact ⟨n, hn, by rw [hcond.2.1, hsig], hcond.2.2.2⟩
  | honest j =>
    left
    -- the signer is a node, online at the slot
    have hS := (wAt_ok (es := es) hA.ord es.length).store
    cases hb : (wF E es).st h.id with
    | none => simp [genuine, hb] at hgen
    | some b' =>
      have hbh : b'.hdr = h := by simpa [genuine, hb] using hgen
      obtain ⟨hjn, hjo⟩ := signOK_all (E := E) (es := es) es.length le_rfl h.id b' j hb (by rw [hbh, hsig])
      rw [hbh] at hjo
      have hw : honW E.c s (fun η id => E.O.ticket η h.slot id) j = true := by
        unfold honW
        simp only [List.any_eq_true, Bool.and_eq_true, decide_eq_true_eq]
        exact ⟨n, hn, by rw [hcond.2.1, hsig], hcond.2.2.2⟩
      have hpos : 0 < honCount E h.slot s (fun η id => E.O.ticket η h.slot id) := by
        unfold honCount
        exact List.length_pos_of_mem (List.mem_filter.2 ⟨hjn, by simp [hjo, hw]⟩)
      simp only
      split_ifs <;> simp_all

/-- Window slots belong to the window's epoch. -/
theorem inWindow_iff {c : Config} {e j : ℕ} :
    inWindow c e j = true ↔ c.epochStart e ≤ j ∧ j < c.epochStart e + c.period := by
  unfold inWindow; exact decide_eq_true_iff

theorem epochOf_window (hA : Assm E) {e j : ℕ} (hw : inWindow E.c e j = true) : E.c.epochOf j = e := by
  rw [inWindow_iff] at hw; unfold Config.epochStart at hw
  have := hA.sane.period_le
  have := hA.sane.offset_le
  unfold Config.epochOf
  have hEL := hA.sane.epochLength_pos
  apply Nat.div_eq_of_lt_le
  · omega
  · rw [add_mul, one_mul]; omega

/-- Window slots past genesis index the window (`win`). -/
theorem win_of_window {e j : ℕ} (hw : inWindow E.c e j = true) (hj : 1 ≤ j) : j - 1 ∈ win E e := by
  rw [inWindow_iff] at hw; unfold Config.epochStart at hw
  simp only [win, mem_Ico]
  omega

/-- Blocks of a rooted chain are stored under their IDs and on the chain. -/
theorem mem_chainUp_iff' (hS : StoreOK (wF E es).st) {b : ℕ} (hb : Rooted (wF E es).st b) {B : Block}
    (hB : B ∈ chainUp (wF E es).st b) :
    (wF E es).st B.hdr.id = some B ∧ B.hdr.id ∈ chainIds (wF E es).st b := by
  refine ⟨mem_chainUp hS hB, ?_⟩
  have := List.mem_map_of_mem (f := fun x : Block => x.hdr.id) hB
  rw [chainUp_ids hS hb, List.mem_reverse] at this
  exact this

/-- **Every counted slot past genesis is occupied in the lottery.** -/
theorem counted_occ (hA : Assm E) {e : ℕ}
    (hcons : 1 ≤ e → prefixBelow (CP E es (e + 1)) (E.c.cut e) = CP E es e) {j : ℕ}
    (hj : j ∈ ((CP E es (e + 1)).filter (fun x => inWindow E.c e x.hdr.slot)).map (·.hdr.slot) ++
      ((((CP E es (e + 1)).filter (fun x => inWindow E.c e x.hdr.slot)).flatMap (·.uncles)).map (·.slot)).filter
        (inWindow E.c e))
    (hj1 : 1 ≤ j) :
    occA (slotOut E j (σE E es j) (fun η id => E.O.ticket η j id)) ∧ inWindow E.c e j = true := by
  have hS := (wAt_ok (es := es) hA.ord es.length).store
  obtain ⟨b, hb, hCP, hval⟩ := cp_good (es := es) hA (e + 1)
  have hgen := store_genesis (E := E) (es := es) hA.ord es.length
  -- an in-window canonical block other than genesis, valid, validated under the canonical state
  have hblk : ∀ B ∈ CP E es (e + 1), inWindow E.c e B.hdr.slot = true → B.hdr.id ≠ genesisId →
      (wF E es).st B.hdr.id = some B ∧ validCore E.c (wF E es).st E.L E.O E.G B = true ∧
        epochState E.c E.L E.O E.G (chainUp (wF E es).st B.hdr.parent) e = CS E es e := by
    intro B hB hw hB0
    have hBc : B ∈ chainUp (wF E es).st b := by rw [hCP] at hB; exact (List.mem_filter.1 hB).1
    obtain ⟨hBs, hBid⟩ := mem_chainUp_iff' hS hb hBc
    rcases hval _ hBid with h0 | ⟨B', hB', hv⟩
    · exact absurd h0 hB0
    rw [hBs] at hB'; cases hB'
    exact ⟨hBs, hv, state_par hA hb hCP hcons hBid hBs hB0 ((inWindow_iff.1 hw).1)⟩
  -- a genesis-ID block of the canonical chain is genesis
  have hgB : ∀ B ∈ CP E es (e + 1), B.hdr.id = genesisId → B = genesisBlock := by
    intro B hB h0
    have hBc : B ∈ chainUp (wF E es).st b := by rw [hCP] at hB; exact (List.mem_filter.1 hB).1
    have := mem_chainUp hS hBc
    rw [h0, hgen] at this
    exact (Option.some_injective _ this).symm
  have hσ : ∀ {i : ℕ}, inWindow E.c e i = true → σE E es i = CS E es e := fun hw => by
    unfold σE; rw [epochOf_window hA hw]
  rw [List.mem_append] at hj
  rcases hj with hj | hj
  · -- a block's own slot
    obtain ⟨B, hB, rfl⟩ := List.mem_map.1 hj
    obtain ⟨hBC, hw⟩ := List.mem_filter.1 hB
    have hB0 : B.hdr.id ≠ genesisId := by
      intro h0; rw [hgB B hBC h0] at hj1; simp [genesisBlock] at hj1
    obtain ⟨-, hv, hst⟩ := hblk B hBC hw hB0
    unfold validCore at hv
    simp only [Bool.and_eq_true] at hv
    refine ⟨occ_of_header hA hv.1.1.1.2 ?_ hv.1.1.2, hw⟩
    rw [epochOf_window hA hw, hσ hw]; exact hst
  · -- an uncle's slot
    obtain ⟨hj', hw⟩ := List.mem_filter.1 hj
    obtain ⟨U, hU, rfl⟩ := List.mem_map.1 hj'
    obtain ⟨B, hB, hUB⟩ := List.mem_flatMap.1 hU
    obtain ⟨hBC, hwB⟩ := List.mem_filter.1 hB
    have hB0 : B.hdr.id ≠ genesisId := by
      intro h0; rw [hgB B hBC h0] at hUB; simp [genesisBlock] at hUB
    obtain ⟨-, hv, hst⟩ := hblk B hBC hwB hB0
    unfold validCore at hv
    simp only [Bool.and_eq_true] at hv
    have hu := List.all_eq_true.1 hv.1.2 U hUB
    unfold validUncle at hu
    simp only [Bool.and_eq_true] at hu
    refine ⟨occ_of_header hA hu.1.2 ?_ hu.2, hw⟩
    rw [epochOf_window hA hw, hσ hw]; exact hst

/-- **`hhi`: the canonical chain's occupied-slot count is at most the window's
occupied lottery slots plus genesis**, given consistent canonical prefixes. -/
theorem occupied_le_wcnt (hA : Assm E) {e : ℕ}
    (hcons : 1 ≤ e → prefixBelow (CP E es (e + 1)) (E.c.cut e) = CP E es e) :
    (occupied E.c (CP E es (e + 1)) e : ℝ) ≤
      wcnt E (fun k => slotOut E (k + 1) (σE E es (k + 1)) (fun η id => E.O.ticket η (k + 1) id)) e + 1 := by
  classical
  set X : ℕ → Out := fun k => slotOut E (k + 1) (σE E es (k + 1)) (fun η id => E.O.ticket η (k + 1) id)
  set F := (win E e).filter (fun k => occA (X k))
  have hw : wcnt E X e = (F.card : ℝ) := by
    unfold wcnt indA; rw [Finset.sum_boole]
  rw [hw]
  unfold occupied
  set Lst := ((CP E es (e + 1)).filter (fun x => inWindow E.c e x.hdr.slot)).map (·.hdr.slot) ++
      ((((CP E es (e + 1)).filter (fun x => inWindow E.c e x.hdr.slot)).flatMap (·.uncles)).map (·.slot)).filter
        (inWindow E.c e)
  have hsub : Lst.dedup.toFinset ⊆ insert 0 (F.image (· + 1)) := by
    intro j hj
    rw [List.mem_toFinset, List.mem_dedup] at hj
    rcases Nat.eq_zero_or_pos j with h0 | h1
    · rw [h0]; exact Finset.mem_insert_self _ _
    · obtain ⟨hocc, hwin⟩ := counted_occ hA hcons hj h1
      refine Finset.mem_insert_of_mem (Finset.mem_image.2 ⟨j - 1, Finset.mem_filter.2 ⟨win_of_window hwin h1, ?_⟩,
        by omega⟩)
      show occA (slotOut E (j - 1 + 1) (σE E es (j - 1 + 1)) (fun η id => E.O.ticket η (j - 1 + 1) id))
      rw [show j - 1 + 1 = j by omega]; exact hocc
  have hcard : Lst.dedup.length ≤ F.card + 1 := by
    rw [← List.toFinset_card_of_nodup (List.nodup_dedup _)]
    calc Lst.dedup.toFinset.card ≤ (insert 0 (F.image (· + 1))).card := Finset.card_le_card hsub
      _ ≤ (F.image (· + 1)).card + 1 := Finset.card_insert_le _ _
      _ ≤ F.card + 1 := by have := Finset.card_image_le (s := F) (f := (· + 1)); omega
  exact_mod_cast hcard

end Cryptarchia.Prob
