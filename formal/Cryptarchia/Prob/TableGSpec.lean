module

public import Cryptarchia.Prob.TableSpec
public import Cryptarchia.Prob.TableGCert
public import Mathlib.Analysis.Complex.ExponentialBounds

/-!
# Finality from a grouped table certificate

As `TableSpec.lean`, with the grouped table (`TableGCert.lean`) as the failed-check potential. Its start
factor `γ ^ (EL - 1)` scales the checked phase's bound in the settlement bound; with `(EL - 1)(γ - 1) ≤ 1`
it is at most `e < eUp` (`pow_le_eUp`), and the numeric conditions are checked with the checked phase's
bound times `eUp` (`finChkSpecE`). The data are computed by rule: each (group, representative)'s terminal
table and one-switch tables at `γ` per slot (`FamCfg.repDataG`), and the contractions (`tabLpG`,
`tabLpiG`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory

/-- An upper bound on `e`. -/
def eUp : ℚ := 27182818286 / 10000000000

/-- **The start factor**: `γ ^ n ≤ e < eUp` when `n (γ - 1) ≤ 1`. -/
theorem pow_le_eUp {γ : ℚ} {n : ℕ} (hγ : 1 ≤ γ) (h : (n : ℚ) * (γ - 1) ≤ 1) : (γ : ℝ) ^ n ≤ (eUp : ℝ) := by
  have h1 : (γ : ℝ) ≤ Real.exp ((γ : ℝ) - 1) := by linarith [Real.add_one_le_exp ((γ : ℝ) - 1)]
  have h0 : (0 : ℝ) ≤ γ := by have : (1 : ℝ) ≤ γ := by exact_mod_cast hγ
                              linarith
  calc (γ : ℝ) ^ n ≤ Real.exp ((γ : ℝ) - 1) ^ n := pow_le_pow_left₀ h0 h1 n
    _ = Real.exp (n * ((γ : ℝ) - 1)) := by rw [← Real.exp_nat_mul]
    _ ≤ Real.exp 1 := Real.exp_le_exp.2 (by exact_mod_cast h)
    _ ≤ (eUp : ℝ) := by
        have := Real.exp_one_lt_d9
        unfold eUp; push_cast; linarith

theorem settleChkQ_e2 {d Δ : ℕ} {Bq : BandR} {e17 τ lp e2 b lr c lpi x yy : ℚ} {k Ccap Lw r T : ℕ}
    (h : settleChkQ d Δ Bq e17 τ lp e2 b lr c lpi x yy k Ccap Lw r T = true) : 0 ≤ e2 := by
  simp only [settleChkQ, Bool.and_eq_true, decide_eq_true_eq] at h
  exact h.1.1.1.1.1.1.1.1.1.1.2

namespace FamCfg

variable {F : FamCfg}

/-- **Finality from a grouped table certificate's data** (`finality_fam` with the grouped table as the
failed-check potential): the switching tables for the reach, the checked phase and spans, and the grouped
table certificate; the checked phase's bound is scaled by the potential's start factor `γ ^ (EL - 1)`. -/
theorem finality_famTG {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
    {E : Env} (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} {lpd lp lpi : ℚ} {Q : TabQG} {nG m G : ℕ}
    {γ Γ : ℚ} {D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)}
    (hP : cert2ChkQ Bq F.Δ F.c F.z F.s 0 F.d F.τ lpd (lrOf dat) (bOf dat) (eOf dat) = true) (hS : F.S.chk F.famZ F.D = true)
    (hD : 0 < F.D) (hBq : Bq = F.S.weakest) (hsw : ∀ i : Fin 19, isSw i = true → F.idxChkSw i (dat i) = true)
    (htab : F.tabChkG Q nG γ Γ E.c.epochLength G lp lpi D = true) (htabA : F.tabChkAG Q γ D) {n : ℕ}
    (hK : F.S.K = n + 1) (T : TBandQ) (hT : famChkQ F T = true) (es : Ω → List Event) (hMod : Model μ O E es) {N : ℕ}
    (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N) (hΔ : E.Δ = F.Δ) (hG1 : F.Δ + 1 ≤ G)
    (hGEL : G + 1 < E.c.epochLength) {M G' J Lw r Tg : ℕ} {x yy : ℚ} (hx : 1 ≤ x) (hyy0 : 0 < yy) (hyy1 : yy ≤ 1)
    (hT1 : 1 ≤ Tg) (hNM : N + G + G' + F.Δ + 2 ≤ M) (hhi1 : Bq.hhi ≤ 1) (hlo0 : 0 ≤ Bq.hlo) (hlo1 : Bq.hlo ≤ 1)
    (helo1 : Bq.elo ≤ 1) (hLw : Lw + G < E.c.epochLength) (hOG : E.c.nonceOffset + G + 2 ≤ E.c.epochLength)
    (hc : LotConsts E.c (1 / 10 ^ 70)) (hb : E.c.betaP = E.c.precision) (hprec : 0 < E.c.precision)
    (hPf : 0 < E.c.period * E.c.fP) (hP1 : 1 ≤ E.c.period) (hPEL : E.c.period ≤ E.c.epochLength) {Ne : ℕ}
    (hNe : M / E.c.epochLength < Ne) {ρ Hmin : ℝ} (hρ : 0 < ρ) (hHm : 0 < Hmin)
    (hup : (1 - T.toTBand.μ) + 2 * T.toTBand.ℓhi / (lam0 E.c * Hmin) ≤
      T.toTBand.ℓhi * Kc E.c * (1 - T.toTBand.μ) * (1 - T.toTBand.δ) * T.toTBand.clo * ((E.c.period : ℝ) - 1) / ρ)
    (hdn : T.toTBand.ℓlo * Kc E.c * (1 + T.toTBand.δ) * T.toTBand.chi * E.c.period * ρ + Kc E.c * ρ +
      3 * T.toTBand.ℓlo / (lam0 E.c * Hmin) ≤ 1)
    (hg1 : T.toTBand.ℓlo ≤ lam0 E.c) (hg2 : (1 - T.toTBand.μ) * lam0 E.c ≤ T.toTBand.ℓhi)
    {Smax : ℝ} (hSm : Smax / E.c.p + Smax ^ 2 / E.c.p ≤ T.ζ)
    (hNw : ∀ e, e + 1 < Ne → e * E.c.epochLength + E.c.period ≤ N)
    (hG : GenesisOK E) (hSt : ∀ ω, Exec.StakeOK E (O ω) (es ω) T.β Smax)
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) T.μ N) (hDr : ∀ ω, Exec.StakeDrift E (O ω) (es ω) ρ N)
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) Hmin) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤
      ENNReal.ofReal (settleEps3G E Bq.toBand (cert2T hP) lp lpi ((cert2T hP).e 2 * (γ : ℝ) ^ (E.c.epochLength - 1)) G N G
        G' J Lw r Tg x yy) +
      Ne * ENNReal.ofReal (bandEps T.toTBand E.c.period) := by
  simp only [famChkQ, Bool.and_eq_true, decide_eq_true_eq] at hT
  obtain ⟨⟨⟨⟨⟨⟨ok, hη⟩, hζ⟩, hβ⟩, hηlot⟩, cov0⟩, cov1⟩ := hT
  obtain ⟨⟨Δ, c, z, s, d', τ⟩, ⟨η, ζ, β, d, dy, K, ys⟩, famZL, Dz⟩ := F
  simp only at hK hη hζ hβ cov0 cov1
  subst hK
  have hβ1 : β < 1 := by
    have h := (TBandQ.ok_of ok).β1
    simp only [TBandQ.toTBand] at h
    rw [hβ]; exact_mod_cast h
  exact finalityG (M := M) (Ne := Ne) (Tb := T.toTBand) es hMod hN hΔ
    (cert2BT hP hS hD hBq hsw E.c.epochLength G hG1 hGEL)
    (fun κ hκ => tabFailPotG htab htabA hS hD hBq (cert2T hP) rfl rfl hG1 hκ)
    (fun _ _ => rfl) (fun _ _ => rfl) (fun _ _ => rfl) (FamSpec.prod hS)
    (G' := G') (J := J) (Lw := Lw) (r := r) (T := Tg) (x := x) (yy := yy)
    (by exact_mod_cast hx) (by exact_mod_cast hyy0) (by exact_mod_cast hyy1) hT1 hNM
    (by simp only [BandR.toBand_hhi]; exact_mod_cast hhi1) (by simp only [BandR.toBand_hlo]; exact_mod_cast hlo0)
    (by simp only [BandR.toBand_hlo]; exact_mod_cast hlo1) (by simp only [BandR.toBand_elo]; exact_mod_cast helo1)
    hLw hOG (by simp only [TBandQ.toTBand, hηlot]; convert hc using 2; norm_num) (TBandQ.ok_of ok)
    hb hprec hPf hP1 hPEL hNe (mem := FamSpec.mem ⟨η, ζ, β, d, dy, n + 1, ys⟩) (fun _ => rfl)
    (fun k => by have := FamSpec.ok hS k; simp only [TBandQ.toTBand, ← hη, ← hζ]; exact this)
    (cover_of_chain (by simpa using FamSpec.chained ⟨η, ζ, β, d, dy, n + 1, ys⟩ rfl)
      (by rw [← TBandQ.ylo_cast]; simp only [FamSpec.mem, FamSpec.mQ, MemberQ.toMember_ylo, memberOfQ_ylo,
        Fin.val_zero]; exact_mod_cast cov0)
      (by rw [← TBandQ.Yh_cast]; simp only [FamSpec.mem, FamSpec.mQ, MemberQ.toMember_yhi, memberOfQ_yhi,
        Fin.val_last]; exact_mod_cast cov1))
    (fun _ => memberOfQ_adv hβ1 (by simp only [TBandQ.toTBand, hβ])) hρ hHm hup hdn hg1 hg2 hSm hNw hG hSt hQ hDr hH


/-- **Finality at the specification, from a grouped table certificate's data.** The switching index checks,
the family's, the grouped table certificate's and the numeric conditions (`finChkSpecE`, with the checked
phase's bound scaled by `eUp`, above the start factor) give the finality bound `fin`. -/
theorem finality_specTG {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
    {E : Env} (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} (p : SpecData) (q : SpecDerived) {lpd : ℚ}
    {Q : TabQG} {nG m : ℕ} {γ Γ : ℚ} {D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)}
    (hC2 : cert2ChkQ Bq F.Δ F.c F.z F.s 0 F.d F.τ lpd (lrOf dat) (bOf dat) (eOf dat) = true) (hS : F.S.chk F.famZ F.D = true)
    (hD : 0 < F.D) (hBq : Bq = F.S.weakest) (hsw : ∀ i : Fin 19, isSw i = true → F.idxChkSw i (dat i) = true)
    (htab : F.tabChkG Q nG γ Γ (Config.specK p.k).epochLength q.G q.lp q.lpi D = true) (htabA : F.tabChkAG Q γ D)
    {n : ℕ} (hK : F.S.K = n + 1) (T : TBandQ) (hfin : finChkSpecE F Bq dat (eOf dat 2 * eUp) T p q = true)
    (hc : E.c = Config.specK p.k) (hΔ : E.Δ = F.Δ) (es : Ω → List Event) (hMod : Model μ O E es)
    (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ p.N) {Smax : ℚ}
    (hSm : Smax / Config.spec.p + Smax ^ 2 / Config.spec.p ≤ T.ζ)
    (hNw : (q.Ne - 2) * (Config.specK p.k).epochLength + (Config.specK p.k).period ≤ p.N) (hG : GenesisOK E)
    (hSt : ∀ ω, Exec.StakeOK E (O ω) (es ω) T.β Smax) (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) T.μ p.N)
    (hDr : ∀ ω, Exec.StakeDrift E (O ω) (es ω) p.ρ p.N) (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) p.Hmin) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal q.fin := by
  obtain ⟨k, κ, N, ε, ρ, Hmin⟩ := p
  obtain ⟨Lw, J, x, G, G', r, Tg, yy, M, Ne, lp, lpi, tgt, bx, fin⟩ := q
  have f := finChkSpecE.facts hfin
  have hEL : E.c.epochLength = (Config.specK k).epochLength := by rw [hc]
  have hP : E.c.period = (Config.specK k).period := by rw [hc]
  have hδ := f.drift
  simp only [driftChkQ, Bool.and_eq_true, decide_eq_true_eq] at hδ
  obtain ⟨⟨⟨⟨⟨hup, hdn⟩, hg1⟩, hg2⟩, hρ⟩, hHm⟩ := hδ
  have tf := FamCfg.tabChkG.facts htab
  have hb := finality_famTG F hC2 hS hD hBq hsw (by rw [hEL]; exact htab) htabA hK T f.fam es hMod hN hΔ f.hG1
    (by rw [hEL]; exact f.hGEL)
    (M := M) (G' := G') (J := J) (Lw := Lw) (r := r) f.hx f.hyy0 f.hyy1 f.hT f.hNM f.hhi1 f.hlo0 f.hlo1 f.helo1
    (by rw [hEL]; exact f.hLw) (by rw [hc]; exact f.hOG)
    (by rw [hc]; exact ⟨lot_spec.p_pos, lot_spec.t0_pos, lot_spec.t1_le, lot_spec.a1_le, lot_spec.a1_near⟩)
    (by rw [hc]; rfl) (by rw [hc]; show 0 < 1000; decide) (by rw [hc]; exact f.hPf) (by rw [hP]; exact f.hP1)
    (by rw [hP, hEL]; exact f.hPEL) (by rw [hEL]; exact f.hNe)
    (ρ := ρ) (Hmin := Hmin) (by exact_mod_cast hρ) (by exact_mod_cast hHm)
    (by rw [hc, ← lam0Q_cast, ← KcQ_cast, ← TBandQ.clo_cast]; simp only [TBandQ.toTBand]; exact_mod_cast hup)
    (by rw [hc, ← lam0Q_cast, ← KcQ_cast, ← TBandQ.chi_cast]; simp only [TBandQ.toTBand]; exact_mod_cast hdn)
    (by rw [hc, ← lam0Q_cast]; simp only [TBandQ.toTBand]; exact_mod_cast hg1)
    (by rw [hc, ← lam0Q_cast]; simp only [TBandQ.toTBand]; exact_mod_cast hg2)
    (Smax := Smax) (by rw [hc]; simp only [Config.specK]; exact_mod_cast hSm)
    (fun e he => by
      have h2 : e ≤ Ne - 2 := by omega
      rw [hEL, hP]
      exact le_trans (Nat.add_le_add_right (Nat.mul_le_mul_right _ h2) _) hNw)
    hG hSt hQ hDr hH
  rw [hP] at hb
  have hk : E.c.k = k := by rw [hc]; rfl
  have hne : nEp E N = (N + 2) / (Config.specK k).epochLength := by unfold nEp; rw [hEL]
  have hnb : nbD E F.Δ G Tg = nbSpec (Config.specK k) F.Δ G Tg := by
    unfold nbD growLen nbSpec; rw [hc]
  have he2 : (cert2T hC2).e 2 * (γ : ℝ) ^ (E.c.epochLength - 1) ≤ ((eOf dat 2 * eUp : ℚ) : ℝ) := by
    have h0 : (0 : ℝ) ≤ (eOf dat 2 : ℚ) := by
      have := (settleChkQ_e2 f.eps)
      have hu : (0 : ℚ) < eUp := by norm_num [eUp]
      exact_mod_cast nonneg_of_mul_nonneg_left this hu
    push_cast
    exact mul_le_mul_of_nonneg_left (pow_le_eUp tf.γ1 (by rw [hEL]; exact tf.epoch)) h0
  have h1 := ((settleEps3G_mono_e2 E Bq.toBand (cert2T hC2) (by exact_mod_cast tf.lpi0) (by exact_mod_cast tf.le) he2
    G N G G' J Lw r Tg x yy).trans
    (settleEps3G_le_Q (d := 14) (lpi := lpi) (x := x) (yy := yy) (Ccap := G) (N := N) (G := G) (G' := G')
    (J := J) (Lw := Lw) (r := r) (T := Tg) (e2R := ((eOf dat 2 * eUp : ℚ) : ℝ)) (cert2T hC2) Bq rfl rfl rfl rfl
    rfl rfl rfl rfl hk hne hnb f.eps)).trans
    (Rat.cast_le.2 f.epsle)
  have h2 := (bandEps_le_Q f.band).trans (Rat.cast_le.2 f.bandle)
  refine hb.trans ((add_le_add (ENNReal.ofReal_le_ofReal h1) (mul_le_mul_right (ENNReal.ofReal_le_ofReal h2) _)).trans ?_)
  have ht : (0 : ℝ) ≤ tgt := by exact_mod_cast f.tgt0
  have hx : (0 : ℝ) ≤ bx := by exact_mod_cast f.bx0
  rw [← ENNReal.ofReal_natCast, ← ENNReal.ofReal_mul (by positivity), ← ENNReal.ofReal_add ht (by positivity)]
  exact ENNReal.ofReal_le_ofReal (by exact_mod_cast f.fin)

end FamCfg

/-! ## A grouped table certificate's data, computed -/

namespace FamCfg

variable (F : FamCfg)

/-- **A (group, representative)'s data**, computed: the group's table's terminal table and its
one-switch tables' seeds and bounds, at `γ` per slot. -/
def repDataG (Q : TabQ) (γ : ℚ) (s : ℤ × ℤ) : RepData :=
  let g := Q.gList s
  let X := PhZ.ofQ (Q.x, γ, fun a b _ => g.getD (2 * a.val + if b then 1 else 0) 0)
  let post := F.postSeedsX X
  let pre := F.preSeedsX X post
  ⟨g, post, pre, F.eInListX X post, F.eEOfX X post pre⟩

/-- All the chunks' entries. -/
def allRepsG {m : ℕ} (D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)) : List (ℕ × (ℤ × ℤ) × RepData) :=
  (List.finRange m).flatMap D

/-- **The grouped table's contractions by rule**: the largest, over the entries, of each of the group's
members' in-epoch bound less the crossing's credit (`lpi`), and of the one-switch bound (`lp`), over the
group's table's value, rounded up to 13 digits. -/
def tabLpiG {m : ℕ} (Q : TabQG) (n : ℕ) (D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)) : ℚ :=
  rupQ 13 (((allRepsG D).map fun p =>
    (((List.finRange F.S.K).filter fun k => F.grpOf n k == p.1).map fun k =>
      (F.repEIn p.2.2 k - (Q.tab p.1).crQ p.2.1 * F.S.patQ F.Δ k) / (Q.tab p.1).VQ p.2.1).foldl max 0).foldl max 0)

def tabLpG {m : ℕ} (Q : TabQG) (D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)) : ℚ :=
  rupQ 13 (((allRepsG D).map fun p => p.2.2.eE / (Q.tab p.1).VQ p.2.1).foldl max 0)

end FamCfg

end Cryptarchia.Prob
