module

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
import Cryptarchia.Prob.Trunc
import Cryptarchia.Proof.Consist
public import Cryptarchia.Prob.Final
public import Cryptarchia.Prob.Worst
import Cryptarchia.Prob.RO

/-!
# A split of the canonical prefixes is a failure of the good event

`split_up`: if epoch `e + 1`'s canonical prefix does not extend epoch `e`'s, the
lottery's good event fails up to `N_e = min (fix (e + 1)) N`, cut at `N_e + 1`, which is
determined by epoch `e`'s and earlier slots.
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory Settle
open scoped ENNReal

/-- **A split is a failure of the truncated good event.** If epoch `ep + 1`'s canonical
prefix does not extend epoch `ep`'s, every string dominating the lottery string's first
`Ms` slots fails the good event up to `min (fix (ep + 1)) N`, cut at `Ms`. -/
theorem split_up (E : Env) (hA : Assm E) (hlive : ∀ t, ∃ j ∈ E.nodes, E.online j t = true) {es : List Event}
    {N Ms Lw r G ep : ℕ} (hNF : (wF E es).now ≤ N) (hep : 1 ≤ ep)
    (hMs : min (E.c.fix (ep + 1)) N < Ms)
    (hgr : ∀ ep', 1 ≤ ep' → E.c.fix ep' ≤ min (E.c.fix (ep + 1)) N → E.c.cut ep' + G < Ms)
    (hsplit : prefixBelow (CP E es (ep + 1)) (E.c.cut ep) ≠ CP E es ep) {l' : List Out}
    (hl : List.Forall₂ OutLe (slots (lotStr E es) Ms) l') :
    ¬ (GoodLS E (strOf l') (min (E.c.fix (ep + 1)) N) Lw (gend E.Δ Ms (strOf l')) ∧
      GrowthS E (strOf l') (gend E.Δ Ms (strOf l')) (min (E.c.fix (ep + 1)) N) r G) := by
  classical
  intro hg
  set Ne := min (E.c.fix (ep + 1)) N
  set lot := lotStr E es with hlot
  obtain ⟨hlen, hget⟩ := List.forall₂_iff_get.1 hl
  rw [slots_length] at hlen
  have hdom1 : ∀ i, 1 ≤ i → i ≤ Ms → OutLe (enc (lot i)) (l'.getD (i - 1) Out.empty) := by
    intro i h1 h2
    have hk1 : i - 1 < (slots lot Ms).length := by rw [slots_length]; omega
    have hk2 : i - 1 < l'.length := by omega
    have := hget (i - 1) hk1 hk2
    rw [List.getD_eq_getElem _ _ hk2]
    simp only [List.get_eq_getElem, slots_get, show i - 1 + 1 = i by omega] at this
    exact this
  set w : CStr := fun i => if 1 ≤ i ∧ i ≤ Ms then ((lot i).1, (strOf l' i).2) else lot i with hw
  have hstr : ∀ i, 1 ≤ i → strOf l' i = (l'.getD (i - 1) Out.empty).toPair := by
    intro i hi; unfold strOf; rw [if_neg (by omega)]
  have hdom : AdvLeW Ne lot w := by
    refine ⟨fun i _ _ => by simp only [hw]; split_ifs <;> rfl, fun i hi => ?_⟩
    simp only [hw]
    split_ifs with h
    · rw [hstr i h.1]
      exact (hdom1 i h.1 h.2).2 (by simpa [enc] using hi)
    · exact hi
  have hsim : SimOn (strOf l') w 0 Ms := by
    intro i h1 h2
    have hd := hdom1 i (by omega) h2
    simp only [hw, if_pos (show 1 ≤ i ∧ i ≤ Ms by omega)]
    rw [hstr i (by omega)]
    simp only [Out.toPair]
    rw [← hd.1]
    exact ⟨enc_hon_zero _, enc_hon_one _, trivial⟩
  have hgw := good_congr_cap E rfl hsim hMs hgr hg
  exact hsplit (cons_of_lot hA hlive hep (min_le_min le_rfl hNF) hdom hgw.1 (growthS_on E hgw.2))

/-- Growth witnesses of epochs fixed by a horizon lie before it. -/
theorem cut_add_lt {c : Config} (hc : c.Sane) {G : ℕ} (hOG : c.nonceOffset + G + 2 ≤ c.epochLength)
    {H Ms : ℕ} (hHM : H < Ms) : ∀ ep, 1 ≤ ep → c.fix ep ≤ H → c.cut ep + G < Ms := by
  intro ep hep hfix
  have : c.cut ep + G ≤ c.fix ep := by
    obtain ⟨e0, rfl⟩ : ∃ e0, ep = e0 + 1 := ⟨ep - 1, by omega⟩
    have hs : c.epochStart (e0 + 1) = c.epochStart e0 + c.epochLength := by
      unfold Config.epochStart; ring
    unfold Config.cut Config.fix
    simp only [Nat.add_sub_cancel]
    omega
  omega

end Cryptarchia.Prob
