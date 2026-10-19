module

public import Cryptarchia.Prob.CertSpec
public import Cryptarchia.Prob.TableCert

/-!
# Finality from a table certificate

A certificate whose failed-check potential is a table (`TableCert.lean`) needs, besides the table
certificate, only the switching tables for the reach, the checked phase and spans (indices `0`, `1`, `2`,
`17`; `idxChkSw`): the potential certificate `cert2T` takes the two-term potential with its second
term off (`κ = 0`), whose class conditions hold without one-switch tables. `finality_famT` and
`finality_specT` are `finality_fam` and `finality_spec` with the table as the failed-check potential
(`finalityG`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory

namespace FamCfg

variable (F : FamCfg)

/-- **The switching checks of index `i`** (no one-switch tables). -/
def idxChkSw (i : ℕ) (dat : IdxData) : Bool :=
  decide ((F.X i).Rep (xgNQ F.c F.z F.s F.d F.τ i).1 (xgNQ F.c F.z F.s F.d F.τ i).2.1 (xgNQ F.c F.z F.s F.d F.τ i).2.2) &&
    (List.finRange F.S.K).all (chkSwF F.famZ F.D F.Δ (F.X i) SZ (seedL dat.vs) fun _ => dat.eS)

variable {F}

theorem idx_swS (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D) {i : Fin 19} {dat : IdxData}
    (h : F.idxChkSw i dat = true) :
    (∀ k, AutoSol (F.S.fam k) F.Δ (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vsR i dat)) ∧
      ∀ k, autoBound (F.S.fam k) (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vsR i dat) ≤ dat.eS := by
  simp only [idxChkSw, Bool.and_eq_true, decide_eq_true_eq] at h
  have := switchF_sound (eS := fun _ => dat.eS) (F.S.rep hS) F.S.agrees hD h.1 SZ_pos h.2
  rw [xgR, xg_ofQ rfl rfl rfl rfl rfl i]
  exact this

variable {Bq : BandR} {dat : Fin 19 → IdxData} {lpd : ℚ}

/-- **The potential certificate of a table certificate**: the two-term potential with its second term
off. -/
noncomputable def cert2T (hP : cert2ChkQ Bq F.Δ F.c F.z F.s 0 F.d F.τ lpd (lrOf dat) (bOf dat) (eOf dat) = true) :
    Cert2 Bq.toBand F.Δ :=
  Cert2.ofQ Bq F.Δ F.c F.z F.s 0 F.d F.τ lpd (lrOf dat) (bOf dat) (eOf dat) hP

/-- **The base certificate of a table certificate**: the switching tables for the reach, the checked
phase and spans. -/
noncomputable def cert2BT (hP : cert2ChkQ Bq F.Δ F.c F.z F.s 0 F.d F.τ lpd (lrOf dat) (bOf dat) (eOf dat) = true)
    (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D) (hBq : Bq = F.S.weakest)
    (hsw : ∀ i : Fin 19, isSw i = true → F.idxChkSw i (dat i) = true) (EL G : ℕ) (hG : F.Δ + 1 ≤ G)
    (hGEL : G + 1 < EL) : Cert2B Bq.toBand F.Δ F.S.fam EL G where
  P := cert2T hP
  weakF := fun k => hBq ▸ F.S.weak hS k
  hG := hG
  hGEL := hGEL
  vs := fun i => F.vsR i (dat i)
  solS := fun i hi k => (idx_swS hS hD (hsw i (isSw_of hi))).1 k
  heS0 := fun k => ((idx_swS hS hD (hsw 0 rfl)).2 k).trans (by
    show ((dat 0).eS : ℝ) ≤ ((max (dat 0).eS (dat 0).eE : ℚ) : ℝ); exact_mod_cast le_max_left _ _)
  heS1 := fun k => ((idx_swS hS hD (hsw 1 rfl)).2 k).trans (by
    show ((dat 1).eS : ℝ) ≤ ((max (max (dat 1).eS (dat 1).eE) 1 : ℚ) : ℝ)
    exact_mod_cast (le_max_left _ _).trans (le_max_left _ _))
  heS2 := fun k => ((idx_swS hS hD (hsw 2 rfl)).2 k).trans le_rfl
  heS17 := fun k => ((idx_swS hS hD (hsw 17 rfl)).2 k).trans le_rfl

/-- **Finality from a table certificate's data** (`finality_fam` with the table as the failed-check
potential): the switching tables for the reach, the checked phase and spans, and the table certificate. -/
theorem finality_famT {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
    {E : Env} (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} {lpd lp lpi : ℚ} {Q : TabQ} {m : ℕ}
    {D : Fin m → List ((ℤ × ℤ) × RepData)}
    (hP : cert2ChkQ Bq F.Δ F.c F.z F.s 0 F.d F.τ lpd (lrOf dat) (bOf dat) (eOf dat) = true) (hS : F.S.chk F.famZ F.D = true)
    (hD : 0 < F.D) (hBq : Bq = F.S.weakest) (hsw : ∀ i : Fin 19, isSw i = true → F.idxChkSw i (dat i) = true)
    (htab : F.tabChk Q Bq lp lpi D = true) (htabA : F.tabChkA Q D) (hties : Q.tiesQ F.c F.z = true) {n : ℕ} (hK : F.S.K = n + 1)
    (T : TBandQ) (hT : famChkQ F T = true) (es : Ω → List Event) (hMod : Model μ O E es) {N : ℕ}
    (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N) (hΔ : E.Δ = F.Δ) {G : ℕ} (hG1 : F.Δ + 1 ≤ G)
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
      ENNReal.ofReal (settleEps3G E Bq.toBand (cert2T hP) lp lpi ((cert2T hP).e 2 * 1) G N G G' J Lw r Tg x yy) +
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
    (cert2BT hP hS hD hBq hsw E.c.epochLength G hG1 hGEL) le_rfl
    (fun κ hκ => tabFailPot htab htabA hS hD hBq (cert2T hP) (TabQ.ties_of hties _ rfl rfl) hG1 hGEL hκ)
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


/-- **Finality at the specification, from a table certificate's data.** The switching index checks, the
family's, the table certificate's and the numeric conditions (`finChkSpec`) give the finality bound `fin`. -/
theorem finality_specT {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
    {E : Env} (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} (p : SpecData) (q : SpecDerived) {lpd : ℚ}
    {Q : TabQ} {m : ℕ} {D : Fin m → List ((ℤ × ℤ) × RepData)}
    (hC2 : cert2ChkQ Bq F.Δ F.c F.z F.s 0 F.d F.τ lpd (lrOf dat) (bOf dat) (eOf dat) = true) (hS : F.S.chk F.famZ F.D = true)
    (hD : 0 < F.D) (hBq : Bq = F.S.weakest) (hsw : ∀ i : Fin 19, isSw i = true → F.idxChkSw i (dat i) = true)
    (htab : F.tabChk Q Bq q.lp q.lpi D = true) (htabA : F.tabChkA Q D) (hties : Q.tiesQ F.c F.z = true) {n : ℕ} (hK : F.S.K = n + 1)
    (T : TBandQ) (hfin : finChkSpec F Bq dat T p q = true)
    (hc : E.c = Config.specK p.k) (hΔ : E.Δ = F.Δ) (es : Ω → List Event) (hMod : Model μ O E es)
    (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ p.N) {Smax : ℚ}
    (hSm : Smax / Config.spec.p + Smax ^ 2 / Config.spec.p ≤ T.ζ)
    (hNw : (q.Ne - 2) * (Config.specK p.k).epochLength + (Config.specK p.k).period ≤ p.N) (hG : GenesisOK E)
    (hSt : ∀ ω, Exec.StakeOK E (O ω) (es ω) T.β Smax) (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) T.μ p.N)
    (hDr : ∀ ω, Exec.StakeDrift E (O ω) (es ω) p.ρ p.N) (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) p.Hmin) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal q.fin := by
  obtain ⟨k, κ, N, ε, ρ, Hmin⟩ := p
  obtain ⟨Lw, J, x, G, G', r, Tg, yy, M, Ne, lp, lpi, tgt, bx, fin⟩ := q
  have f := finChkSpec.facts hfin
  have hEL : E.c.epochLength = (Config.specK k).epochLength := by rw [hc]
  have hP : E.c.period = (Config.specK k).period := by rw [hc]
  have hδ := f.drift
  simp only [driftChkQ, Bool.and_eq_true, decide_eq_true_eq] at hδ
  obtain ⟨⟨⟨⟨⟨hup, hdn⟩, hg1⟩, hg2⟩, hρ⟩, hHm⟩ := hδ
  have hb := finality_famT F hC2 hS hD hBq hsw htab htabA hties hK T f.fam es hMod hN hΔ f.hG1 (by rw [hEL]; exact f.hGEL)
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
  have h1 := (settleEps3G_le_Q (d := 14) (lpi := lpi) (x := x) (yy := yy) (Ccap := G) (N := N) (G := G) (G' := G')
    (J := J) (Lw := Lw) (r := r) (T := Tg) (e2R := (cert2T hC2).e 2 * 1) (cert2T hC2) Bq rfl rfl rfl rfl
    (by rw [mul_one]; rfl) rfl rfl rfl hk hne hnb
    f.eps).trans
    (Rat.cast_le.2 f.epsle)
  have h2 := (bandEps_le_Q f.band).trans (Rat.cast_le.2 f.bandle)
  refine hb.trans ((add_le_add (ENNReal.ofReal_le_ofReal h1) (mul_le_mul_right (ENNReal.ofReal_le_ofReal h2) _)).trans ?_)
  have ht : (0 : ℝ) ≤ tgt := by exact_mod_cast f.tgt0
  have hx : (0 : ℝ) ≤ bx := by exact_mod_cast f.bx0
  rw [← ENNReal.ofReal_natCast, ← ENNReal.ofReal_mul (by positivity), ← ENNReal.ofReal_add ht (by positivity)]
  exact ENNReal.ofReal_le_ofReal (by exact_mod_cast f.fin)

end FamCfg

/-! ## A table certificate's data, computed -/

deriving instance Lean.ToExpr for RepData

namespace TabQ

variable (Q : TabQ)

/-- The largest `V(next) / x^A` over `2 ≤ A ≤ AX`. -/
def gmaxQ (s : ℤ × ℤ) (b : Bool) : ℚ :=
  ((List.range (Q.AX - 1)).map fun i => Q.VQ (stepO s ((i + 2 : ℕ) : ℤ) (TabPot.bI b) false) / Q.x ^ (i + 2)).foldl max 0

/-- **A representative's terminal table**, from the table's own values, rounded up to 13 digits. -/
def gList (s : ℤ × ℤ) : List ℚ :=
  [Q.VQ (stepO s 0 0 false), Q.VQ (stepO s 0 1 false), Q.VQ (stepO s 1 0 false) / Q.x, Q.VQ (stepO s 1 1 false) / Q.x,
    Q.gmaxQ s false, Q.gmaxQ s true].map (rupQ 13)

end TabQ

namespace FamCfg

variable (F : FamCfg)

/-- The terminal table's entries at `(0, a, true)`, for a phase expectation `X`. -/
def floorX (X : PhZ) : List ℤ := [gFloorZ X SZ 0 0 true, gFloorZ X SZ 0 1 true, gFloorZ X SZ 0 2 true]

/-- The solvers of the phase indices (`postSeeds`, `preSeeds`, `eInList`, `eEOf`) for any phase expectation. -/
def postSeedsX (X : PhZ) : List (List ℤ) :=
  seedsZ F.D F.Δ X SZ (gFloorZ X SZ) (2 ^ 32) (2 ^ 8) 3 2 200 F.famL (floorX X)

def preSeedsX (X : PhZ) (post : List (List ℤ)) : List (List ℤ) :=
  preSeedsZ F.famL F.D F.Δ X SZ (2 ^ 32) (2 ^ 8) 0 200 post

def eInListX (X : PhZ) (post : List (List ℤ)) : List ℚ := eInListQ F.famL F.D F.Δ X SZ 13 post

def eEOfX (X : PhZ) (post pre : List (List ℤ)) : ℚ :=
  let vm := vmaxListZ F.famL F.D F.Δ X SZ post
  (List.zipWith (fun B t => rupQ 13 ((autoBoundZ B F.D X SZ (tabZ (fillRowsZ [B] F.D F.Δ X SZ (tabZ vm) (seedL t) 0 F.Δ)) : ℚ) /
    (X.M F.D * SZ : ℤ))) F.famL pre).foldl max 0

/-- **A representative's data**, computed: its terminal table and its one-switch tables' seeds and bounds. -/
def repData (Q : TabQ) (s : ℤ × ℤ) : RepData :=
  let g := Q.gList s
  let X := PhZ.ofQ (Q.x, 1, fun a b _ => g.getD (2 * a.val + if b then 1 else 0) 0)
  let post := F.postSeedsX X
  let pre := F.preSeedsX X post
  ⟨g, post, pre, F.eInListX X post, F.eEOfX X post pre, [], [], [], []⟩

/-- All the chunks' representatives with their data. -/
def allReps {n : ℕ} (D : Fin n → List ((ℤ × ℤ) × RepData)) : List ((ℤ × ℤ) × RepData) := (List.finRange n).flatMap D

/-- **The table's contractions by rule**: the largest, over the representatives, of each member's in-epoch
bound less the crossing's credit (`lpi`), and of the one-switch bound less it (`lp`), over the table's
value, rounded up to 13 digits. -/
def tabLpi {n : ℕ} (Q : TabQ) (D : Fin n → List ((ℤ × ℤ) × RepData)) : ℚ :=
  rupQ 13 (((allReps D).map fun p =>
    ((List.finRange F.S.K).map fun k => (F.repEIn p.2 k - Q.crQ p.1 * F.S.patQ F.Δ k) / Q.VQ p.1).foldl max 0).foldl max 0)

def tabLp {n : ℕ} (Q : TabQ) (Bq : BandR) (D : Fin n → List ((ℤ × ℤ) × RepData)) : ℚ :=
  rupQ 13 (((allReps D).map fun p => (p.2.eE - Q.crQ p.1 * (Bq.slo * Bq.elo ^ F.Δ)) / Q.VQ p.1).foldl max 0)

end FamCfg

end Cryptarchia.Prob
