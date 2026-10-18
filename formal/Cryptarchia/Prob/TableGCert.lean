module

public import Cryptarchia.Prob.TableG
public import Cryptarchia.Prob.TableCert

/-!
# A grouped table certificate for failed checks

Rational tables by group (`TabQG`), one per group of consecutive band members (`FamCfg.grpOf`),
sharing their box and extension factors, are a failed-check potential (`TabFam.toFailPotG`) once each
(group, representative) passes its checks: its terminal table above the group's table, its one-switch
tables at the automaton's factor `γ` per slot (`repChkAG`), the in-epoch bound of each of the group's
members less the crossing's credit at most `lpi` times the table's value, and the one-switch bound at
most `lp` times it (`repChkCG`); and the tables are within a factor `Γ` of each other, which the growth
`γ` per slot over an epoch covers (`Γ ≤ 1 + (EL - 2G)(γ - 1) ≤ γ ^ (EL - 2G)`).
-/

@[expose] public section

namespace Cryptarchia.Prob

/-- **Tables by group** over `ℚ`: a shared box and extension factors, each group's warm and cold
values. -/
structure TabQG where
  R : ℕ
  M : ℕ
  cw : ℚ
  zc : ℚ
  x : ℚ
  w : List (List ℚ)
  c : List (List (List ℚ))

namespace TabQG

variable (Q : TabQG)

/-- Group `g`'s table. -/
def tab (g : ℕ) : TabQ := ⟨Q.R, Q.M, Q.cw, Q.zc, Q.x, Q.w.getD g [], Q.c.getD g []⟩

/-- The tables over `ℝ`. -/
noncomputable def toFam (n : ℕ) : TabFam n :=
  ⟨Q.R, Q.M, Q.cw, Q.zc, Q.x, fun g r => ((Q.tab g).wQ r : ℝ), fun g r j => ((Q.tab g).cQ r j : ℝ)⟩

theorem toFam_T (n : ℕ) (g : Fin n) : (Q.toFam n).T g = (Q.tab g).toPot := rfl

theorem repList_eq (g g' : ℕ) : (Q.tab g).repList = (Q.tab g').repList := rfl

end TabQG

/-- The phase expectation of a representative's terminal table, at the automaton's factor `x` and `θ`
per slot. -/
def RepData.XG (d : RepData) (x θ : ℚ) : PhZ := PhZ.ofQ (x, θ, d.gq)

namespace FamCfg

variable (F : FamCfg)

/-- **The groups**: `n` groups of consecutive members. -/
def grpOf (n : ℕ) (k : Fin F.S.K) : ℕ := k.val * n / F.S.K

theorem grpOf_lt {n : ℕ} (hn : 0 < n) (k : Fin F.S.K) : F.grpOf n k < n := by
  unfold grpOf
  have hK : 0 < F.S.K := Nat.lt_of_le_of_lt (Nat.zero_le _) k.isLt
  rw [Nat.div_lt_iff_lt_mul hK]
  exact Nat.mul_lt_mul_of_lt_of_le k.isLt le_rfl hn |>.trans_eq (Nat.mul_comm _ _)

/-- **A representative's tables** in a group's table: its terminal table above the table's own, its
one-switch tables over the integers at `γ` per slot, the crossing's credit nonnegative. -/
def repChkAG (Q : TabQ) (γ : ℚ) (s : ℤ × ℤ) (d : RepData) : Bool :=
  Q.domQ s d && decide ((d.XG Q.x γ).Rep Q.x γ d.gq) &&
    (List.finRange F.S.K).all (chkOneF F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.repPost d) (F.repPre d) (F.repEIn d) d.eE) &&
    decide (0 ≤ Q.crQ s)

/-- **A representative's contraction** in group `g`'s table: each of the group's members' in-epoch bound
less the crossing's credit at most `lpi` times the table's value; the one-switch bound at most `lp` times
it. -/
def repChkCG (Q : TabQ) (n g : ℕ) (lp lpi : ℚ) (s : ℤ × ℤ) (d : RepData) : Bool :=
  (List.finRange F.S.K).all (fun k => !(F.grpOf n k == g) ||
    decide (F.repEIn d k - Q.crQ s * F.S.patQ F.Δ k ≤ lpi * Q.VQ s)) &&
    decide (d.eE ≤ lp * Q.VQ s)

/-- **The representatives' tables, in chunks**, each entry a group, a representative and its data. -/
def tabChkAG {m : ℕ} (Q : TabQG) (γ : ℚ) (D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)) : Prop :=
  ∀ j, (D j).all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true

/-- **The grouped table certificate's checks**: each group's table's shape and ties; every
(group, representative) covered by a chunk; every entry's contraction; the tables within `Γ` of each
other at the representatives; the growth `γ` per slot covering `Γ` over an epoch of `EL` slots less
`2G`, and at most `1` over the epoch; `0 < lpi ≤ lp`. -/
def tabChkG {m : ℕ} (Q : TabQG) (n : ℕ) (γ Γ : ℚ) (EL G : ℕ) (lp lpi : ℚ)
    (D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)) : Bool :=
  decide (0 < n) &&
    (List.range n).all (fun g => (Q.tab g).shapeQ && (Q.tab g).tiesQ F.c F.z) &&
    (List.range n).all (fun g => (Q.tab g).repList.all fun s =>
      (List.finRange m).any fun j => (D j).any fun p => p.1 == g && p.2.1 == s) &&
    (List.finRange m).all (fun j => (D j).all fun p => F.repChkCG (Q.tab p.1) n p.1 lp lpi p.2.1 p.2.2) &&
    (List.range n).all (fun g => (List.range n).all fun g' => (Q.tab g).repList.all fun s =>
      decide ((Q.tab g').VQ s ≤ Γ * (Q.tab g).VQ s)) &&
    decide (1 ≤ γ) && decide (0 ≤ Γ) && decide (2 * G + 1 < EL) && decide (Γ ≤ 1 + ((EL - 2 * G : ℕ) : ℚ) * (γ - 1)) &&
    decide (((EL - 1 : ℕ) : ℚ) * (γ - 1) ≤ 1) && decide (0 < lpi) && decide (lpi ≤ lp)

end FamCfg

/-- The facts the grouped table certificate's checks give. -/
structure TabGFacts (F : FamCfg) {m : ℕ} (Q : TabQG) (n : ℕ) (γ Γ : ℚ) (EL G : ℕ) (lp lpi : ℚ)
    (D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)) : Prop where
  n_pos : 0 < n
  shape : ∀ g < n, (Q.tab g).shapeQ = true
  ties : ∀ g < n, (Q.tab g).tiesQ F.c F.z = true
  cover : ∀ g < n, ∀ s ∈ (Q.tab g).repList, ∃ j, ∃ p ∈ D j, p.1 = g ∧ p.2.1 = s
  contr : ∀ j, ∀ p ∈ D j, F.repChkCG (Q.tab p.1) n p.1 lp lpi p.2.1 p.2.2 = true
  ratio : ∀ g < n, ∀ g' < n, ∀ s ∈ (Q.tab g).repList, (Q.tab g').VQ s ≤ Γ * (Q.tab g).VQ s
  γ1 : 1 ≤ γ
  Γ0 : 0 ≤ Γ
  GEL : 2 * G + 1 < EL
  ramp : Γ ≤ 1 + ((EL - 2 * G : ℕ) : ℚ) * (γ - 1)
  epoch : ((EL - 1 : ℕ) : ℚ) * (γ - 1) ≤ 1
  lpi0 : 0 < lpi
  le : lpi ≤ lp

theorem FamCfg.tabChkG.facts {F : FamCfg} {m : ℕ} {Q : TabQG} {n : ℕ} {γ Γ : ℚ} {EL G : ℕ} {lp lpi : ℚ}
    {D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)} (h : F.tabChkG Q n γ Γ EL G lp lpi D = true) :
    TabGFacts F Q n γ Γ EL G lp lpi D := by
  simp only [FamCfg.tabChkG, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true, List.any_eq_true,
    List.mem_range, beq_iff_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨hn, hsh⟩, hcov⟩, hcon⟩, hrat⟩, hγ⟩, hΓ⟩, hGEL⟩, hramp⟩, hep⟩, hlpi⟩, hle⟩ := h
  refine ⟨hn, fun g hg => (hsh g hg).1, fun g hg => (hsh g hg).2, ?_, fun j p hp => hcon j (List.mem_finRange j) p hp,
    fun g hg g' hg' s hs => hrat g hg g' hg' s hs, hγ, hΓ, hGEL, hramp, hep, hlpi, hle⟩
  intro g hg s hs
  obtain ⟨j, -, p, hp, h1, h2⟩ := hcov g hg s hs
  exact ⟨j, p, hp, h1, h2⟩

theorem gq_nonneg' {Q : TabQ} {s : ℤ × ℤ} {d : RepData} (hS : Q.toPot.Shape) (hdom : Q.domQ s d = true)
    (a : Fin 3) (b u : Bool) : 0 ≤ castG d.gq a b u :=
  le_trans (TabFam.gT_nonneg hS a b u) (TabQ.gT_le hdom a b u)

theorem crossG_mono {θ : ℝ} (hθ : 1 ≤ θ) (m : ℕ) (h : List Out) : crossG 1 m h ≤ crossG θ m h := by
  unfold crossG; rw [one_pow, one_mul]
  exact le_mul_of_one_le_left (by split_ifs <;> norm_num) (one_le_pow₀ hθ)

/-- **The grouped table certificate as a failed-check potential.** -/
noncomputable def FamCfg.tabFailPotG {F : FamCfg} {m : ℕ} {Q : TabQG} {n : ℕ} {γ Γ : ℚ} {EL G : ℕ} {Bq : BandR}
    {lp lpi : ℚ} {D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)} (h : F.tabChkG Q n γ Γ EL G lp lpi D = true)
    (hA : F.tabChkAG Q γ D) (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D) (hBq : Bq = F.S.weakest)
    (P : Cert2 Bq.toBand F.Δ) (hc : P.c = F.c) (hz : P.z = F.z) (hG : F.Δ + 1 ≤ G) {κ : Kern} {M : ℕ}
    (hκ : κ.EpochFam EL F.S.fam) :
    FailPot κ M G P (fun t => ¬ NoSw EL G t) := by
  classical
  have f := FamCfg.tabChkG.facts h
  have hEL : 0 < EL := by have := f.GEL; omega
  have hGEL : G + 1 < EL := by have := f.GEL; have := P.hΔ; omega
  have hG1 : 1 ≤ G := by have := P.hΔ; omega
  have hW : κ.Within Bq.toBand := hκ.fam.within fun B' hB' => by
    obtain ⟨k, rfl⟩ := List.mem_ofFn.1 hB'
    exact hBq ▸ F.S.weak hS k
  set mem := Classical.choose hκ
  have hband : ∀ l, κ.BandAt (F.S.fam (mem l)) l := (Classical.choose_spec hκ).1
  have hmem : ∀ l o, (l.length + 2) % EL ≠ 0 → mem (l ++ [o]) = mem l := (Classical.choose_spec hκ).2
  let grp : Fin F.S.K → Fin n := fun k => ⟨F.grpOf n k, F.grpOf_lt f.n_pos k⟩
  have hSh : ∀ g : Fin n, ((Q.toFam n).T g).Shape := fun g => by
    rw [TabQG.toFam_T]; exact TabQ.shape_of (f.shape g g.isLt)
  have hT : ∀ g : Fin n, ((Q.toFam n).T g).Ties P := fun g => by
    rw [TabQG.toFam_T]; exact TabQ.ties_of (f.ties g g.isLt) P hc hz
  have hγ : (1 : ℝ) ≤ γ := by exact_mod_cast f.γ1
  -- the facts of an entry's checks
  have facts : ∀ g : Fin n, ∀ s, ((Q.toFam n).T g).IsRep s → ∃ d : RepData, (Q.tab g).domQ s d = true ∧
      AutoSolE F.S.fam F.Δ (Q.x : ℝ) γ (castG d.gq)
        (fun k => castZ SZ (preF F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.repPost d) (F.repPre d) k))
        (fun k => castZ SZ (postF F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.repPost d) k))
        (castZ SZ (vmaxF F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.repPost d))) ∧
      (∀ k, autoBound (F.S.fam k) (Q.x : ℝ) γ (castG d.gq)
        (castZ SZ (postF F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.repPost d) k)) ≤ F.repEIn d k) ∧
      (∀ k, autoBound (F.S.fam k) (Q.x : ℝ) γ (castG d.gq)
        (castZ SZ (preF F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.repPost d) (F.repPre d) k)) ≤ d.eE) ∧
      0 ≤ (Q.tab g).crQ s ∧
      (∀ k, F.grpOf n k = g → F.repEIn d k - (Q.tab g).crQ s * F.S.patQ F.Δ k ≤ lpi * (Q.tab g).VQ s) ∧
      d.eE ≤ lp * (Q.tab g).VQ s := by
    intro g s hs
    rw [TabQG.toFam_T] at hs
    obtain ⟨j, p, hp, hg, hsp⟩ := f.cover g g.isLt s (TabQ.mem_repList _ hs)
    have hA' := List.all_eq_true.1 (hA j) p hp
    have hC := f.contr j p hp
    rw [hg, hsp] at hA' hC
    simp only [FamCfg.repChkAG, FamCfg.repChkCG, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true,
      Bool.or_eq_true, Bool.not_eq_true', beq_eq_false_iff_ne, ne_eq] at hA' hC
    obtain ⟨⟨⟨hdom, hX⟩, hone⟩, hcr⟩ := hA'
    obtain ⟨hin, hE⟩ := hC
    have hsound := oneSwitchF_sound (F.S.rep hS) F.S.agrees hD hX SZ_pos (List.all_eq_true.2 hone)
    refine ⟨p.2.2, hdom, hsound.1, hsound.2.1, hsound.2.2, hcr, fun k hk => ?_, hE⟩
    rcases hin k (List.mem_finRange k) with h1 | h1
    · exact absurd hk h1
    · exact h1
  refine TabFam.toFailPotG (F := Q.toFam n) hSh P hT hmem grp hγ f.GEL (Γ := Γ) (by exact_mod_cast f.Γ0) ?_ ?_ ?_
    (lp := lp) (lpi := lpi) (by exact_mod_cast f.lpi0) (by exact_mod_cast f.le) ?_ ?_
  · -- the growth over an epoch covers the ratio
    have hr : ((Γ : ℚ) : ℝ) ≤ 1 + ((EL - 2 * G : ℕ) : ℝ) * ((γ : ℝ) - 1) := by exact_mod_cast f.ramp
    refine hr.trans ?_
    have := one_add_mul_le_pow (show (-2 : ℝ) ≤ (γ : ℝ) - 1 by linarith) (EL - 2 * G)
    simpa using this
  · -- the ratio at the representatives
    intro g g' s hs
    rw [TabQG.toFam_T] at hs
    rw [TabQG.toFam_T, TabQG.toFam_T, TabQ.V_cast, TabQ.V_cast]
    have := f.ratio g g.isLt g' g'.isLt s (TabQ.mem_repList _ hs)
    exact_mod_cast this
  · intro g s hs
    obtain ⟨d, -, -, -, -, hcr, -, -⟩ := facts g s hs
    rw [TabQG.toFam_T, TabQ.crT_cast]; exact_mod_cast hcr
  · -- any phase: the one-switch tables
    intro g s hs l hpe hlM hgl
    obtain ⟨d, hdom, hsol, -, hpre, -, -, hE⟩ := facts g s hs
    have hS' := hSh g
    rw [TabQG.toFam_T] at hS' ⊢
    have hx := TabPot.x_pos hS'
    have hle : ExPh (κ := κ) (PE F.Δ M) (M - l.length - 1)
        (truncG l.length G (Wt2 (Q.toFam n).x γ ((Q.tab g).toPot.gT s) l.length)) l ≤
        ExPh (κ := κ) (PE F.Δ M) (M - l.length - 1) (truncG l.length G (Wt2 (Q.x : ℝ) γ (castG d.gq) l.length)) l := by
      refine ExPh_mono_on _ _ _ fun o t _ _ _ => ?_
      unfold truncG
      split_ifs
      · exact TabQ.Wt2_mono hx.le (by linarith) (TabQ.gT_le hdom) _ _
      · exact le_rfl
    refine hle.trans ((phase_autoE hsol (gq_nonneg' hS' hdom) mem hband hmem hx.le (by linarith) hEL hGEL hG1 hpre
      P.hΔ (start_of_pe hpe (show l.length < M by omega)) (show l.length < M by omega)).trans ?_)
    rw [TabQ.V_cast]; exact_mod_cast hE
  · -- an in-epoch phase: the member's own tables and crossing bound
    intro g s hs l hpe hlM hnb hgl
    obtain ⟨d, hdom, hsol, hpost, -, hcr, hin, -⟩ := facts g s hs
    have hS' := hSh g
    rw [TabQG.toFam_T] at hS' ⊢
    have hx := TabPot.x_pos hS'
    have hcrR : 0 ≤ (Q.tab g).toPot.crT s := by rw [TabQ.crT_cast]; exact_mod_cast hcr
    have hle : ExPh (κ := κ) (PE F.Δ M) (M - l.length - 1) (truncG l.length G (fun y =>
          Wt2 (Q.toFam n).x γ ((Q.tab g).toPot.gT s) l.length y - (Q.tab g).toPot.crT s * crossG γ l.length y)) l ≤
        ExPh (κ := κ) (PE F.Δ M) (M - l.length - 1) (truncG l.length G (fun y =>
          Wt2 (Q.x : ℝ) γ (castG d.gq) l.length y - (Q.tab g).toPot.crT s * crossG 1 l.length y)) l := by
      refine ExPh_mono_on _ _ _ fun o t _ _ _ => ?_
      unfold truncG
      split_ifs
      · exact sub_le_sub (TabQ.Wt2_mono hx.le (by linarith) (TabQ.gT_le hdom) _ _)
          (mul_le_mul_of_nonneg_left (crossG_mono hγ _ _) hcrR)
      · exact le_rfl
    refine hle.trans ?_
    rw [TabQ.truncG_sub, ExPh_sub, TabPot.truncG_mul, ExPh_mul_const]
    have h1 := phase_autoIn hsol.post (gq_nonneg' hS' hdom) mem hband hmem hx.le (by linarith) hG1 (hpost (mem l)) P.hΔ
      (start_of_pe hpe (show l.length < M by omega)) (show l.length < M by omega) hnb
    have h2 := ex_cross_truncIn mem hband hmem (F.S.pat_le F.Δ (mem l)) (F.S.elo hS) P.hΔ hlM hG hnb
    have hin' : (F.repEIn d (mem l) : ℝ) - (Q.tab g).crQ s * F.S.patQ F.Δ (mem l) ≤ lpi * (Q.tab g).VQ s := by
      exact_mod_cast hin (mem l) (congrArg Fin.val hgl)
    rw [TabQ.crT_cast, ← TabQ.V_cast] at *
    nlinarith [mul_le_mul_of_nonneg_left h2 hcrR]

end Cryptarchia.Prob
