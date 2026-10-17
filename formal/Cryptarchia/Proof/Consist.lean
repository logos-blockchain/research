module

public import Cryptarchia.Proof.FinalE
import Cryptarchia.Proof.Recur
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
# Consistent canonical prefixes from the lottery's good event

`cons_of_lot`: if a string dominating the lottery string is good up to epoch `e + 1`'s
fixing time, epoch `e + 1`'s canonical prefix, cut at epoch `e`'s cut, is epoch `e`'s
canonical prefix (`hcons`), provided some honest node is online at every slot. The
good event is needed only up to the fixing time, not up to the end of the execution
(`stage_cap`, which is `stage` with the horizon capped).
-/

@[expose] public section

namespace Cryptarchia

open Settle

variable {E : Env} {es : List Event} {W : ℕ → ℕ} {e : ℕ → ℕ}

/-- **The stages, up to a horizon `N`.** As `stage`, without assuming that the
execution ends by `N`: the execution's good event and growth hold up to
`min (min (E.c.fix (s+1)) now) N`. -/
theorem stage_cap (hA : Assm E)
    {N : ℕ} {w : CStr} (hdom : AdvLeW N (lotStrS E (σE E es) (lateAt E es)) w)
    (hL : GoodLSW E w N W e) (hLg : GrowthOn E w e N) :
    ∀ s, GoodCondW E es (Cons E es) W e (min (min (E.c.fix (s + 1)) (wF E es).now) N) ∧
      Growth E es e (min (min (E.c.fix (s + 1)) (wF E es).now) N) := by
  have hfix : ∀ ep, 1 ≤ ep → E.c.cut ep ≤ E.c.fix ep ∧ E.c.fix ep + 2 ≤ E.c.epochStart ep :=
    fun ep h => hA.sane.fix_ok ep h
  have hfix2 : ∀ ep, 1 ≤ ep → E.c.fix ep + 2 ≤ E.c.epochStart ep := fun ep h => (hfix ep h).2
  have hord : ∀ ep ep', 1 ≤ ep → ep ≤ ep' → E.c.fix ep ≤ E.c.fix ep' := by
    intro ep ep' h1 h2
    rcases Nat.eq_or_lt_of_le h2 with h | h
    · rw [h]
    · have a1 := (hfix ep h1).2
      have a2 := (hfix ep' (by omega)).1
      have a3 : E.c.epochStart ep ≤ E.c.epochStart (ep' - 1) := epochStart_mono (by omega)
      unfold Config.cut at a2
      omega
  have step : ∀ (H' Hs : ℕ), H' ≤ (wF E es).now → Hs ≤ (wF E es).now → Hs ≤ N →
      GoodCondW E es (Cons E es) W e H' → Growth E es e H' →
      (∀ ep, 1 ≤ ep → E.c.epochStart ep ≤ Hs → E.c.fix ep ≤ H') →
      GoodCondW E es (Cons E es) W e Hs ∧ Growth E es e Hs := by
    intro H' Hs hH' hHs hHN hG hGr hcov
    have hle := (advLeW_lotE hA hG hGr hH' hcov hHs).trans hdom hHN
    exact ⟨good_of_dom hle hHN hL, growth_of_dom hle hHN hL.mono hLg⟩
  intro s
  induction s with
  | zero =>
    have hG0 : GoodCondW E es (Cons E es) W e 0 := good_zero hL.e0 hL.mono hL.unb
    have hGr0 : Growth E es e 0 := by
      intro ep hep hF
      have := (hfix ep hep).1
      have : 1 ≤ E.c.cut ep := by unfold Config.cut; have := hA.sane.offset_pos; omega
      omega
    refine step 0 _ (Nat.zero_le _) (le_trans (min_le_left _ _) (min_le_right _ _)) (min_le_right _ _) hG0 hGr0 ?_
    intro ep hep hst
    simp only [Nat.zero_add] at hst
    have a1 := hfix2 1 le_rfl
    have a2 : E.c.epochStart 1 ≤ E.c.epochStart ep := epochStart_mono hep
    have := le_trans (min_le_left (min (E.c.fix 1) (wF E es).now) N) (min_le_left (E.c.fix 1) (wF E es).now)
    omega
  | succ s ih =>
    refine step _ _ (le_trans (min_le_left _ _) (min_le_right _ _)) (le_trans (min_le_left _ _) (min_le_right _ _))
      (min_le_right _ _) ih.1 ih.2 ?_
    intro ep hep hst
    have hm1 : min (min (E.c.fix (s + 1 + 1)) (wF E es).now) N ≤ E.c.fix (s + 1 + 1) :=
      le_trans (min_le_left _ _) (min_le_left _ _)
    have hm2 : min (min (E.c.fix (s + 1 + 1)) (wF E es).now) N ≤ (wF E es).now :=
      le_trans (min_le_left _ _) (min_le_right _ _)
    have hm3 := min_le_right (min (E.c.fix (s + 1 + 1)) (wF E es).now) N
    have hep' : ep ≤ s + 1 := by
      by_contra hc; push Not at hc
      have a1 := hfix2 (s + 1 + 1) (by omega)
      have a2 : E.c.epochStart (s + 1 + 1) ≤ E.c.epochStart ep := epochStart_mono (by omega)
      omega
    have h1 := hord ep (s + 1) hep hep'
    have h2 := hfix2 ep hep
    exact le_min (le_min h1 (by omega)) (by omega)

/-- An epoch whose fixing time the execution never reaches is fixed at its end. -/
theorem idxE_eq_length {ep : ℕ} (h : (wF E es).now < E.c.fix ep) : idxE E es ep = es.length := by
  classical
  have hex : ∃ n, n = es.length ∨ E.c.fix ep ≤ (wAt E es n).now := ⟨es.length, Or.inl rfl⟩
  have hle : idxE E es ep ≤ es.length := Nat.find_min' hex (Or.inl rfl)
  rcases Nat.find_spec hex with h1 | h2
  · exact h1
  · have := now_mono (E := E) (es := es) hle le_rfl
    exact absurd (le_trans h2 this) (by unfold wF at h; omega)

/-- **Consistent canonical prefixes from the lottery's good event.** If a string
dominating the lottery string is good, with growth, up to a horizon `Hc` at least
`min (E.c.fix (ep + 1)) now`, and some honest node is online at every slot, epoch
`ep + 1`'s canonical prefix, cut at epoch `ep`'s cut, is epoch `ep`'s canonical
prefix. -/
theorem cons_of_lot (hA : Assm E) (hlive : ∀ t, ∃ j ∈ E.nodes, E.online j t = true) {ep : ℕ} (hep : 1 ≤ ep)
    {Hc : ℕ} (hHc : min (E.c.fix (ep + 1)) (wF E es).now ≤ Hc)
    {w : CStr} (hdom : AdvLeW Hc (lotStrS E (σE E es) (lateAt E es)) w)
    (hL : GoodLSW E w Hc W e) (hLg : GrowthOn E w e Hc) :
    prefixBelow (CP E es (ep + 1)) (E.c.cut ep) = CP E es ep := by
  obtain ⟨hG, hGr⟩ := stage_cap hA hdom hL hLg ep
  have hcc : E.c.cut ep ≤ E.c.cut (ep + 1) := by
    unfold Config.cut
    have := epochStart_mono (c := E.c) (show ep - 1 ≤ ep + 1 - 1 by omega)
    omega
  rcases le_or_gt (E.c.fix (ep + 1)) (wF E es).now with hreach | hshort
  · -- the execution reaches the fixing time
    have hH : min (min (E.c.fix (ep + 1)) (wF E es).now) Hc = E.c.fix (ep + 1) := by
      rw [min_eq_left hreach] at hHc ⊢; exact min_eq_left hHc
    rw [hH] at hG hGr
    exact cp_consistent hA hG hGr hreach hep le_rfl (hlive _)
  · have hH : min (min (E.c.fix (ep + 1)) (wF E es).now) Hc = (wF E es).now := by
      rw [min_eq_right hshort.le] at hHc ⊢; exact min_eq_left hHc
    rw [hH] at hG hGr
    have hidx := idxE_eq_length (E := E) (es := es) hshort
    rcases le_or_gt (E.c.fix ep) (wF E es).now with hreach' | hshort'
    · -- epoch `ep` is fixed, epoch `ep + 1` only at the end
      have hw := wAt_ok (es := es) hA.ord es.length
      have hon : ∃ j ∈ E.nodes, E.online j (wAt E es (idxE E es (ep + 1))).now = true := by
        rw [hidx]; exact hlive _
      have hi0 : i0 E es (ep + 1) ∈ E.nodes ∧ E.online (i0 E es (ep + 1)) (wAt E es (idxE E es (ep + 1))).now = true := by
        unfold i0; rw [dif_pos hon]; exact Classical.choose_spec hon
      rw [hidx] at hi0
      have hbr := ((hw.nodes (i0 E es (ep + 1))).bimm_on_cloc hw.store).1
      have hcan := canon_node hA hG hGr le_rfl hep hreach' le_rfl hreach' hi0.1 hi0.2 hbr
        (self_mem_chainIds hw.store hbr)
      unfold CP
      rw [hidx, prefixBelow_prefixBelow _ hcc]
      exact hcan
    · -- neither is fixed: both are read at the end, from the same node
      have hidx' := idxE_eq_length (E := E) (es := es) hshort'
      have hi : i0 E es (ep + 1) = i0 E es ep := by unfold i0; rw [hidx, hidx']
      unfold CP
      rw [hi, hidx, hidx', prefixBelow_prefixBelow _ hcc]

end Cryptarchia
