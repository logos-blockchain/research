import Cryptarchia.Prob.Tail2
import Cryptarchia.Prob.Final

/-!
# Probabilistic finality, sharper

`final_bimm_prob2`: `final_bimm_prob` with the automaton certificate `Cert2` and the
bound `settleEps2`.
-/

namespace Cryptarchia.Prob

open Finset Settle MeasureTheory

/-- **Probabilistic finality.**

For any probability space `Ω` and executions `es ω` whose clocks stay below `N`: if
the first `M` slots of the lottery string have (at most) the law of a kernel within
the band `B`, a finality violation has probability at most `settleEps2`. -/
theorem final_bimm_prob2 {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω)
    (E : Env) (hA : Assm E) (es : Ω → List Event) {N M : ℕ} (hNF : ∀ ω, (wF E (es ω)).now ≤ N)
    {κ : Kern} {B : Band}
    (hlaw : ∀ S : Set (List Out), μ {ω | slots (lotStr E (es ω)) M ∈ S} ≤
      ENNReal.ofReal (Ex κ M (S.indicator 1) []))
    {Δ : ℕ} (hΔ : E.Δ = Δ) (P : Cert2 B Δ) (hB : κ.Fam P.Bs) {G G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + Δ + 2 ≤ M) (hNM' : N + G' + Δ + 1 < M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1) :
    μ {ω | Unsafe E (es ω)} ≤ ENNReal.ofReal (settleEps2 E B P N G G' J Lw r T x yy) := by
  classical
  subst hΔ
  set Bad : Set (List Out) := {l | ¬ (GoodLS E (strOf l) N Lw (gend E.Δ M (strOf l)) ∧
    GrowthS E (strOf l) (gend E.Δ M (strOf l)) N r G)} with hBad
  have hsub : {ω | Unsafe E (es ω)} ⊆ {ω | slots (lotStr E (es ω)) M ∈ Bad} := by
    intro ω hω
    simp only [Set.mem_setOf_eq, hBad, not_not] at hω ⊢
    intro hg
    exact not_unsafe E hA (M := M) (hNF ω)
      (good_congr E rfl hA.sane (sim_slots (lotStr E (es ω)) M) (by omega) hg) hω
  refine (measure_mono hsub).trans ((hlaw Bad).trans (ENNReal.ofReal_le_ofReal ?_))
  refine le_trans ?_ (settle_bound2 E rfl hA.sane P hB hx hyy0 hyy1 hT hNM hNM' hhi1 hlo0 hlo1 helo1)
  apply Ex_mono_len
  intro t ht
  simp only [List.nil_append, Set.indicator, hBad, Set.mem_setOf_eq, Pi.one_apply]
  split_ifs <;> simp_all

end Cryptarchia.Prob
