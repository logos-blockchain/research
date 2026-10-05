import Cryptarchia.Prob.Final2E

/-!
# Helpers for multi-epoch certificates

A one-switch automaton solution (`AutoSolE`) from per-member pieces, so that a
generated certificate proves each member's tables separately.
-/

namespace Cryptarchia.Prob

/-- The pre-switch table of one member: above `vmax`, and its own recursion. -/
structure PreSol (B : Band) (Δ : ℕ) (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ)
    (vmax vpre : ℕ → Fin 3 → Bool → ℝ) : Prop where
  dom : ∀ q < Δ, ∀ a u, vmax q a u ≤ vpre q a u
  step : ∀ q < Δ, ∀ a u, θ * slot4 B (fun hh aa =>
    (if aa then x else 1) *
      (if hh then vpre 0 (acap (a.val + if aa then 1 else 0)) true
        else if q + 1 = Δ then g (acap (a.val + if aa then 1 else 0)) true u
          else vpre (q + 1) (acap (a.val + if aa then 1 else 0)) u)) ≤ vpre q a u

theorem AutoSolE.mk' {K : ℕ} {fam : Fin K → Band} {Δ : ℕ} {x θ : ℝ} {g : Fin 3 → Bool → Bool → ℝ}
    {vpre vpost : Fin K → ℕ → Fin 3 → Bool → ℝ} {vmax : ℕ → Fin 3 → Bool → ℝ}
    (hpost : ∀ k, AutoSol (fam k) Δ x θ g (vpost k))
    (hmax : ∀ k, ∀ q < Δ, ∀ a u, vpost k q a u ≤ vmax q a u)
    (hpre : ∀ k, PreSol (fam k) Δ x θ g vmax (vpre k)) : AutoSolE fam Δ x θ g vpre vpost vmax :=
  ⟨hpost, hmax, fun k => (hpre k).dom, fun k => (hpre k).step⟩

end Cryptarchia.Prob
