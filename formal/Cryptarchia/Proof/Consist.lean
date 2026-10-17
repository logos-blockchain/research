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
  obtain ⟨hG, hGr⟩ := stage hA hdom hL hLg ep
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
