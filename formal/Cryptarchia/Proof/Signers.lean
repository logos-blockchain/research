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
public import Cryptarchia.Proof.Trace
import Cryptarchia.Proof.LotteryG

/-!
# Honest signers were online

Every stored block signed by an honest node was proposed by that node, at the
block's slot, while it was online (`signOK_all`): only a node's own lead step adds
blocks it signs, and it leads only while online. The adversary's `create` adds only
adversarial blocks, and deliveries do not change the store.
-/

@[expose] public section

namespace Cryptarchia

variable {E : Env} {es : List Event}

/-- **Honest signers were online**: every stored block signed by an honest node `j`
has `j` among the nodes, online at the block's slot. -/
def SignOK (E : Env) (w : World) : Prop :=
  ∀ b B j, w.st b = some B → B.hdr.signer = .honest j → j ∈ E.nodes ∧ E.online j B.hdr.slot = true

theorem signOK_init : SignOK E World.init := by
  intro b B j hb hj
  simp only [World.init] at hb; split at hb
  · cases hb; simp [genesisBlock] at hj
  · simp at hb

theorem signOK_lead {w : World} (hw : SignOK E w) {i : ℕ} (hi : i ∈ E.nodes) : SignOK E (w.lead E i) := by
  cases hio : E.online i w.now with
  | false => rw [lead_off hio]; exact hw
  | true =>
    cases hp : propose E.c w.st E.L E.O E.G i w.now w.fresh (w.node i) with
    | none => rw [lead_none hio hp]; exact hw
    | some C =>
      obtain ⟨-, hsig, -, hsl⟩ := propose_id hp
      intro b B j hb hj
      rw [(lead_some hio hp).1] at hb
      by_cases hbC : b = C.hdr.id
      · have hBC : B = C := by simp [World.add, hbC] at hb; exact hb.symm
        subst hBC
        rw [hsig] at hj; cases hj
        exact ⟨hi, by rw [hsl]; exact hio⟩
      · exact hw b B j (by simpa [World.add, hbC] using hb) hj

theorem signOK_fold : ∀ (l : List ℕ) {w : World}, (∀ j ∈ l, j ∈ E.nodes) → SignOK E w →
    SignOK E (l.foldl (World.lead E) w)
  | [], _, _, hw => hw
  | i :: l, _, hl, hw => by
    simp only [List.foldl_cons]
    exact signOK_fold l (fun j hj => hl j (List.mem_cons_of_mem _ hj))
      (signOK_lead hw (hl i List.mem_cons_self))

theorem signOK_step {w : World} (hw : SignOK E w) (e : Event) : SignOK E (w.step E e) := by
  cases e with
  | tick =>
    simp only [World.step]
    exact signOK_fold E.nodes (fun _ h => h) (w := { w with now := w.now + 1 }) hw
  | deliver i b =>
    simp only [World.step]; split
    · exact hw
    · exact hw
  | create B =>
    simp only [World.step]; split
    · rename_i hc
      simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
      intro b C j hb hj
      by_cases hbB : b = B.hdr.id
      · have hCB : C = B := by simp [World.add, hbB] at hb; exact hb.symm
        subst hCB; rw [hc.1] at hj; cases hj
      · exact hw b C j (by simpa [World.add, hbB] using hb) hj
    · exact hw

/-- **Honest signers were online, throughout an execution.** -/
theorem signOK_all : ∀ n ≤ es.length, SignOK E (wAt E es n)
  | 0, _ => by rw [wAt_zero]; exact signOK_init
  | n + 1, hn => by
    rw [wAt_succ E es (by omega)]
    exact signOK_step (signOK_all n (by omega)) es[n]

end Cryptarchia
