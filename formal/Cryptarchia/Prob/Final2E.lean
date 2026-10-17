module

public import Cryptarchia.Prob.Fail2E
public import Cryptarchia.Prob.Tail2
import Cryptarchia.Prob.Good
public import Cryptarchia.Prob.AutoE
public import Cryptarchia.Prob.RO
public import Cryptarchia.Prob.WorstE
import Cryptarchia.Prob.ROEpoch
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
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# Probabilistic finality over many epochs

`final_bimm_ro_epoch`: under a random oracle, fresh lotteries and Δ-delivery, if every
epoch state is within the band of a member of a family (`pick`), a finality
violation has probability at most `settleEps2E`, for any certificate `Cert2E` of the
family. The member may differ from epoch to epoch.

`Cert2E` holds a potential certificate `P` (its constants and class conditions,
with `P.e i` the bounds for phases cut at `G` slots and `P.lr`, `P.b`, `P.e 2`,
`P.e 17` bounds for any phase), automaton solutions that switch member at any slot
for the reach, the checked phase and spans (`vs`), and one-switch automaton
solutions for the contraction (`vpre`, `vpost`, `vmax`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle MeasureTheory

/-- **A certificate for a family of bands with one member per epoch.** -/
structure Cert2E (B : Band) (Δ : ℕ) {K : ℕ} (fam : Fin K → Band) (EL G : ℕ) where
  P : Cert2 B Δ
  weakF : ∀ k, B.Weaker (fam k)
  hG : Δ + 1 ≤ G
  hGEL : G + 1 < EL
  /-- tables for phases of any length, switching member at any slot -/
  vs : Fin 19 → ℕ → Fin 3 → Bool → ℝ
  solS : ∀ i : Fin 19, (i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 17) → ∀ k,
    AutoSol (fam k) Δ (xg P.c P.z P.s P.d P.τ i).1 (xg P.c P.z P.s P.d P.τ i).2.1 (xg P.c P.z P.s P.d P.τ i).2.2 (vs i)
  heS0 : ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ 0).1 (xg P.c P.z P.s P.d P.τ 0).2.1
    (xg P.c P.z P.s P.d P.τ 0).2.2 (vs 0) ≤ P.lr
  heS1 : ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ 1).1 (xg P.c P.z P.s P.d P.τ 1).2.1
    (xg P.c P.z P.s P.d P.τ 1).2.2 (vs 1) ≤ P.b
  heS2 : ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ 2).1 (xg P.c P.z P.s P.d P.τ 2).2.1
    (xg P.c P.z P.s P.d P.τ 2).2.2 (vs 2) ≤ P.e 2
  heS17 : ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ 17).1 (xg P.c P.z P.s P.d P.τ 17).2.1
    (xg P.c P.z P.s P.d P.τ 17).2.2 (vs 17) ≤ P.e 17
  /-- one-switch tables for phases cut at `G` slots -/
  vpre : Fin 19 → Fin K → ℕ → Fin 3 → Bool → ℝ
  vpost : Fin 19 → Fin K → ℕ → Fin 3 → Bool → ℝ
  vmax : Fin 19 → ℕ → Fin 3 → Bool → ℝ
  solE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → AutoSolE fam Δ (xg P.c P.z P.s P.d P.τ i).1 (xg P.c P.z P.s P.d P.τ i).2.1
    (xg P.c P.z P.s P.d P.τ i).2.2 (vpre i) (vpost i) (vmax i)
  heE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ k, autoBound (fam k) (xg P.c P.z P.s P.d P.τ i).1
    (xg P.c P.z P.s P.d P.τ i).2.1 (xg P.c P.z P.s P.d P.τ i).2.2 (vpre i k) ≤ P.e i

variable {B : Band} {Δ M : ℕ} {κ : Kern}

theorem xg_g_nonneg (P : Cert2 B Δ) (i : Fin 19) (a : Fin 3) (b u : Bool) :
    0 ≤ (xg P.c P.z P.s P.d P.τ i).2.2 a b u := by
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have hs0 : 0 < P.s := by linarith [P.hs]
  have hd0 : 0 < P.d := P.hd0
  fin_cases i <;> simp only [xg, xgN, gtab] <;> first | positivity | (split_ifs <;> positivity)

section Derive

variable {K EL G : ℕ} {fam : Fin K → Band} (C : Cert2E B Δ fam EL G) (hκ : κ.EpochFam EL fam)
include C hκ

theorem Cert2E.within : κ.Within B :=
  hκ.fam.within fun B' hB' => by
    obtain ⟨k, rfl⟩ := List.mem_ofFn.1 hB'
    exact C.weakF k

theorem Cert2E.anyPhase (i : Fin 19) (hi : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 17) {e : ℝ}
    (he : ∀ k, autoBound (fam k) (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).1 (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).2.1
      (xg C.P.c C.P.z C.P.s C.P.d C.P.τ i).2.2 (C.vs i) ≤ e) :
    ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP C.P i h.length) h ≤ e := by
  intro h hpe hlM
  have hx := xg_nonneg C.P i
  exact phase_auto hκ.fam hx.1 hx.2 (fun B' hB' => by obtain ⟨k, rfl⟩ := List.mem_ofFn.1 hB'; exact C.solS i hi k)
    (fun B' hB' => by obtain ⟨k, rfl⟩ := List.mem_ofFn.1 hB'; exact he k) C.P.hΔ (start_of_pe hpe hlM) hlM

theorem Cert2E.truncPhase : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ h, PE Δ M h → h.length < M →
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP C.P i h.length)) h ≤ C.P.e i := by
  intro i h2 h17 h hpe hlM
  obtain ⟨mem, hband, hmem⟩ := hκ
  have hx := xg_nonneg C.P i
  have hEL : 0 < EL := by have := C.hGEL; omega
  have hG1 : 1 ≤ G := by have := C.hG; omega
  exact phase_autoE (C.solE i h2 h17) (xg_g_nonneg C.P i) mem hband hmem hx.1 hx.2 hEL C.hGEL hG1
    (C.heE i h2 h17) C.P.hΔ (start_of_pe hpe hlM) hlM

end Derive

end Cryptarchia.Prob
