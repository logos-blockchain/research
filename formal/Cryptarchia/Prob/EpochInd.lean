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
public import Cryptarchia.Prob.Trunc
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
    ¬ GoodCap E (min (E.c.fix (ep + 1)) N) Ms Lw r G (strOf l') := by
  intro hg
  obtain ⟨w, hdom, hgw⟩ := good_dom E hMs hgr hl hg
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
