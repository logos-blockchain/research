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

A phase that starts more than `R` slots before the next boundary but within `G` of it may still switch
member. The group's delayed tables bound it (`chkDlyG`, `phase_autoD`): `R` recursion steps from `vmax`,
each the largest over the group's members. Each member's bound with them less the crossing's credit is at
most `lpi` times the table's value too, so the contraction `lp` is paid only within `R` slots of a
boundary.
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

/-- A member's delayed bound in a representative's data. -/
def repED (d : RepData) (k : Fin F.S.K) : ℚ := d.eD.getD k.val 0

/-- A member's envelope `(Z, λ, aZ)` in a representative's data. -/
def repEnv (d : RepData) (k : Fin F.S.K) : List (List ℤ) × ℚ × ℚ := d.env.getD k.val ([], 1, 0)

/-- The worst band's post-switch table `W` of a representative, from its seeds. -/
def tabW (d : RepData) (X : PhZ) : ℕ → Fin 3 → Bool → ℤ := fillZ (worstZ F.famL) F.D F.Δ X SZ (gFloorZ X SZ) (seedL d.w)

/-- The worst band's pre-switch table, above `W`, from its seeds. -/
def tabPW (d : RepData) (X : PhZ) : ℕ → Fin 3 → Bool → ℤ := fillZ (worstZ F.famL) F.D F.Δ X SZ (F.tabW d X) (seedL d.pw)

/-- Group `g`'s members. -/
def grpMem (n g : ℕ) : List (Fin F.S.K) := (List.finRange F.S.K).filter fun k => F.grpOf n k == g

theorem mem_grpMem {n g : ℕ} {k : Fin F.S.K} (h : F.grpOf n k = g) : k ∈ F.grpMem n g := by
  simp [grpMem, h]

/-- **A representative's tables** in group `g`'s table: its terminal table above the table's own; its
one-switch tables over the integers at `γ` per slot, from the family's worst band (`chkOneW`), with each
of the group's members' own post-switch table; the crossing's credit nonnegative; and each of the group's
members' envelope against `W` (`chkEnvW`), with its delayed bound after `R` steps at most `eD`. -/
def repChkAG (Q : TabQ) (γ : ℚ) (n g R : ℕ) (s : ℤ × ℤ) (d : RepData) : Bool :=
  Q.domQ s d && decide ((d.XG Q.x γ).Rep Q.x γ d.gq) &&
    chkOneW F.famZ F.D F.Δ (d.XG Q.x γ) SZ (worstZ F.famL) (seedL d.w) (seedL d.pw) (F.repPost d) (F.grpMem n g)
      (F.repEIn d) d.eE &&
    decide (0 ≤ Q.crQ s) && (F.grpMem n g).all fun k =>
      chkEnvW F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.tabW d (d.XG Q.x γ)) (F.repPost d) k (F.repEnv d k).1
        (F.repEnv d k).2.1 (F.repEnv d k).2.2 &&
        decide (F.repEIn d k + (F.repEnv d k).2.1 ^ R * (F.repEnv d k).2.2 ≤ F.repED d k)

/-- **A representative's contraction** in group `g`'s table: each of the group's members' in-epoch and
delayed bounds less the crossing's credit at most `lpi` times the table's value; the one-switch bound at
most `lp` times it. -/
def repChkCG (Q : TabQ) (n g : ℕ) (lp lpi : ℚ) (s : ℤ × ℤ) (d : RepData) : Bool :=
  (List.finRange F.S.K).all (fun k => !(F.grpOf n k == g) ||
    decide (F.repEIn d k - Q.crQ s * F.S.patQ F.Δ k ≤ lpi * Q.VQ s) &&
      decide (F.repED d k - Q.crQ s * F.S.patQ F.Δ k ≤ lpi * Q.VQ s)) &&
    decide (d.eE ≤ lp * Q.VQ s)

/-- **The representatives' tables, in chunks**, each entry a group, a representative and its data. -/
def tabChkAG {m : ℕ} (Q : TabQG) (γ : ℚ) (n R : ℕ) (D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)) : Prop :=
  ∀ j, (D j).all (fun p => F.repChkAG (Q.tab p.1) γ n p.1 R p.2.1 p.2.2) = true

/-- **The grouped table certificate's checks**: each group's table's shape and ties; every
(group, representative) covered by a chunk; every entry's contraction; the tables within `Γ` of each
other at the representatives; the growth `γ` per slot covering `Γ` over an epoch of `EL` slots less
`2G`, and at most `1` over the epoch; `0 < lpi ≤ lp`; the delayed tables at least `Δ + 2` steps. -/
def tabChkG {m : ℕ} (Q : TabQG) (n : ℕ) (γ Γ : ℚ) (EL G R : ℕ) (lp lpi : ℚ)
    (D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)) : Bool :=
  decide (0 < n) &&
    (List.range n).all (fun g => (Q.tab g).shapeQ && (Q.tab g).tiesQ F.c F.z) &&
    (List.range n).all (fun g => (Q.tab g).repList.all fun s =>
      (List.finRange m).any fun j => (D j).any fun p => p.1 == g && p.2.1 == s) &&
    (List.finRange m).all (fun j => (D j).all fun p => F.repChkCG (Q.tab p.1) n p.1 lp lpi p.2.1 p.2.2) &&
    (List.range n).all (fun g => (List.range n).all fun g' => (Q.tab g).repList.all fun s =>
      decide ((Q.tab g').VQ s ≤ Γ * (Q.tab g).VQ s)) &&
    decide (1 ≤ γ) && decide (0 ≤ Γ) && decide (2 * G + 1 < EL) && decide (Γ ≤ 1 + ((EL - 2 * G : ℕ) : ℚ) * (γ - 1)) &&
    decide (((EL - 1 : ℕ) : ℚ) * (γ - 1) ≤ 1) && decide (0 < lpi) && decide (lpi ≤ lp) && decide (F.Δ + 2 ≤ R)

end FamCfg

/-- The facts the grouped table certificate's checks give. -/
structure TabGFacts (F : FamCfg) {m : ℕ} (Q : TabQG) (n : ℕ) (γ Γ : ℚ) (EL G R : ℕ) (lp lpi : ℚ)
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
  hR : F.Δ + 2 ≤ R

theorem FamCfg.tabChkG.facts {F : FamCfg} {m : ℕ} {Q : TabQG} {n : ℕ} {γ Γ : ℚ} {EL G R : ℕ} {lp lpi : ℚ}
    {D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)} (h : F.tabChkG Q n γ Γ EL G R lp lpi D = true) :
    TabGFacts F Q n γ Γ EL G R lp lpi D := by
  simp only [FamCfg.tabChkG, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true, List.any_eq_true,
    List.mem_range, beq_iff_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨hn, hsh⟩, hcov⟩, hcon⟩, hrat⟩, hγ⟩, hΓ⟩, hGEL⟩, hramp⟩, hep⟩, hlpi⟩, hle⟩, hR⟩ := h
  refine ⟨hn, fun g hg => (hsh g hg).1, fun g hg => (hsh g hg).2, ?_, fun j p hp => hcon j (List.mem_finRange j) p hp,
    fun g hg g' hg' s hs => hrat g hg g' hg' s hs, hγ, hΓ, hGEL, hramp, hep, hlpi, hle, hR⟩
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
noncomputable def FamCfg.tabFailPotG {F : FamCfg} {m : ℕ} {Q : TabQG} {n : ℕ} {γ Γ : ℚ} {EL G R : ℕ} {Bq : BandR}
    {lp lpi : ℚ} {D : Fin m → List (ℕ × (ℤ × ℤ) × RepData)} (h : F.tabChkG Q n γ Γ EL G R lp lpi D = true)
    (hA : F.tabChkAG Q γ n R D) (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D) (hBq : Bq = F.S.weakest)
    (P : Cert2 Bq.toBand F.Δ) (hc : P.c = F.c) (hz : P.z = F.z) (hG : F.Δ + 1 ≤ G) {κ : Kern} {M : ℕ}
    (hκ : κ.EpochFam EL F.S.fam) :
    FailPot κ M G P (fun t => ¬ NoSw EL R t) := by
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
      AutoSolE F.S.fam F.Δ (Q.x : ℝ) γ (castG d.gq) (fun _ => castZ SZ (F.tabPW d (d.XG Q.x γ)))
        (fun _ => castZ SZ (F.tabW d (d.XG Q.x γ))) (castZ SZ (F.tabW d (d.XG Q.x γ))) ∧
      (∀ k, F.grpOf n k = g →
        AutoSol (F.S.fam k) F.Δ (Q.x : ℝ) γ (castG d.gq) (castZ SZ (postF F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.repPost d) k)) ∧
        autoBound (F.S.fam k) (Q.x : ℝ) γ (castG d.gq)
          (castZ SZ (postF F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.repPost d) k)) ≤ F.repEIn d k ∧
        autoBound (F.S.fam k) (Q.x : ℝ) γ (castG d.gq) (castZ SZ (F.tabPW d (d.XG Q.x γ))) ≤ d.eE) ∧
      0 ≤ (Q.tab g).crQ s ∧
      (∀ k, F.grpOf n k = g → F.repEIn d k - (Q.tab g).crQ s * F.S.patQ F.Δ k ≤ lpi * (Q.tab g).VQ s) ∧
      d.eE ≤ lp * (Q.tab g).VQ s ∧
      (d.XG Q.x γ).Rep Q.x γ d.gq ∧
      (∀ k, F.grpOf n k = g → chkEnvW F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.tabW d (d.XG Q.x γ)) (F.repPost d) k
        (F.repEnv d k).1 (F.repEnv d k).2.1 (F.repEnv d k).2.2 = true ∧
        F.repEIn d k + (F.repEnv d k).2.1 ^ R * (F.repEnv d k).2.2 ≤ F.repED d k) ∧
      (∀ k, F.grpOf n k = g → F.repED d k - (Q.tab g).crQ s * F.S.patQ F.Δ k ≤ lpi * (Q.tab g).VQ s) := by
    intro g s hs
    rw [TabQG.toFam_T] at hs
    obtain ⟨j, p, hp, hg, hsp⟩ := f.cover g g.isLt s (TabQ.mem_repList _ hs)
    have hA' := List.all_eq_true.1 (hA j) p hp
    have hC := f.contr j p hp
    rw [hg, hsp] at hA' hC
    simp only [FamCfg.repChkAG, FamCfg.repChkCG, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true,
      Bool.or_eq_true, Bool.not_eq_true', beq_eq_false_iff_ne, ne_eq] at hA' hC
    obtain ⟨⟨⟨⟨hdom, hX⟩, hone⟩, hcr⟩, hdly⟩ := hA'
    obtain ⟨hin, hE⟩ := hC
    have hsound := oneSwitchW_sound (F.S.rep hS) F.S.agrees hD hX SZ_pos hone
    refine ⟨p.2.2, hdom, hsound.1, fun k hk => hsound.2 k (F.mem_grpMem hk), hcr, fun k hk => ?_, hE, hX,
      fun k hk => ?_, fun k hk => ?_⟩
    · rcases hin k (List.mem_finRange k) with h1 | h1
      · exact absurd hk h1
      · exact h1.1
    · exact hdly k (F.mem_grpMem hk)
    · rcases hin k (List.mem_finRange k) with h1 | h1
      · exact absurd hk h1
      · exact h1.2
  refine TabFam.toFailPotG (F := Q.toFam n) hSh P hT hmem grp hγ f.GEL (Γ := Γ) (by exact_mod_cast f.Γ0) ?_ ?_ ?_
    (lp := lp) (lpi := lpi) (by exact_mod_cast f.lpi0) (by exact_mod_cast f.le) (G1 := R) f.hR ?_ ?_
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
    obtain ⟨d, -, -, -, hcr, -, -, -, -, -⟩ := facts g s hs
    rw [TabQG.toFam_T, TabQ.crT_cast]; exact_mod_cast hcr
  · -- any phase: the one-switch tables
    intro g s hs l hpe hlM hgl
    obtain ⟨d, hdom, hsol, hown, -, -, hE, -, -, -⟩ := facts g s hs
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
    refine hle.trans ((phase_autoE1 hsol (gq_nonneg' hS' hdom) mem hband hmem hx.le (by linarith) hEL hGEL hG1
      P.hΔ (hown (mem l) (congrArg Fin.val hgl)).2.2 (start_of_pe hpe (show l.length < M by omega))
      (show l.length < M by omega)).trans ?_)
    rw [TabQ.V_cast]; exact_mod_cast hE
  · -- a phase with no boundary within `R + 1` slots: the member's own or delayed tables, and the crossing
    intro g s hs l hpe hlM hnb1 hgl
    obtain ⟨d, hdom, hsol, hown, hcr, hin, -, hX, hdly, hfar⟩ := facts g s hs
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
    have hk : F.grpOf n (mem l) = g := congrArg Fin.val hgl
    have h2 := ex_cross_truncIn1 mem hband hmem (F.S.pat_le F.Δ (mem l)) (F.S.elo hS) P.hΔ hlM hG
      (G1 := R) (by have := f.hR; omega) hnb1
    -- the phase's bound: the member's own tables without a boundary within `G`, its delayed ones otherwise
    have h1 : ExPh (κ := κ) (PE F.Δ M) (M - l.length - 1) (truncG l.length G (Wt2 (Q.x : ℝ) γ (castG d.gq) l.length)) l ≤
        max (F.repEIn d (mem l) : ℝ) (F.repED d (mem l)) := by
      by_cases hnb : NoSw EL G l.length
      · -- the group's members' own post-switch tables, `W` for the others
        classical
        let vp : Fin F.S.K → ℕ → Fin 3 → Bool → ℝ := fun k' => if F.grpOf n k' = g then
          castZ SZ (postF F.famZ F.D F.Δ (d.XG Q.x γ) SZ (F.repPost d) k') else castZ SZ (F.tabW d (d.XG Q.x γ))
        have hvp : ∀ k', AutoSol (F.S.fam k') F.Δ (Q.x : ℝ) γ (castG d.gq) (vp k') := fun k' => by
          by_cases h' : F.grpOf n k' = g
          · simp only [vp, if_pos h']; exact (hown k' h').1
          · simp only [vp, if_neg h']; exact hsol.post k'
        have hb : autoBound (F.S.fam (mem l)) (Q.x : ℝ) γ (castG d.gq) (vp (mem l)) ≤ F.repEIn d (mem l) := by
          simp only [vp, if_pos hk]; exact (hown (mem l) hk).2.1
        exact le_trans (phase_autoIn hvp (gq_nonneg' hS' hdom) mem hband hmem hx.le (by linarith) hG1
          hb P.hΔ (start_of_pe hpe (show l.length < M by omega)) (show l.length < M by omega) hnb)
          (le_max_left _ _)
      · have hex : ∃ j, l.length < j ∧ j ≤ l.length + G ∧ (j + 1) % EL = 0 := by
          unfold NoSw at hnb; push Not at hnb; exact hnb
        have hb := Nat.find_spec hex
        have hbl : l.length + R + 1 ≤ Nat.find hex := by
          by_contra hc; push Not at hc
          exact hnb1 (Nat.find hex) hb.1 (by omega) hb.2.2
        obtain ⟨henv, hED⟩ := hdly (mem l) hk
        obtain ⟨hZ0, hD0, hZ, hl0, hl1, haZ⟩ := envW_sound (F.S.rep hS) F.S.agrees hD hX SZ_pos henv
        refine le_trans (phase_autoEnv hsol (gq_nonneg' hS' hdom) mem hband hmem hEL hGEL hx.le (by linarith) hG1
          (R := R) (hown (mem l) hk).1 hZ0 hl0 hl1 hZ hD0 P.hΔ (start_of_pe hpe (show l.length < M by omega))
          (show l.length < M by omega) rfl hb.2.2 hbl
          (fun j h1 h2 h3 => Nat.find_min hex h2 ⟨h1, by omega, h3⟩)) ?_
        refine le_trans ?_ (le_max_right _ _)
        have hED' : ((F.repEIn d (mem l) + (F.repEnv d (mem l)).2.1 ^ R * (F.repEnv d (mem l)).2.2 : ℚ) : ℝ) ≤
            F.repED d (mem l) := by exact_mod_cast hED
        push_cast at hED'
        have := (hown (mem l) hk).2.1
        have h2 := mul_le_mul_of_nonneg_left haZ (pow_nonneg hl0 R)
        linarith
    have hin' : max (F.repEIn d (mem l) : ℝ) (F.repED d (mem l)) - (Q.tab g).crQ s * F.S.patQ F.Δ (mem l) ≤
        lpi * (Q.tab g).VQ s := by
      rw [← max_sub_sub_right]
      exact max_le (by exact_mod_cast hin (mem l) hk) (by exact_mod_cast hfar (mem l) hk)
    rw [TabQ.crT_cast, ← TabQ.V_cast] at *
    nlinarith [mul_le_mul_of_nonneg_left h2 hcrR]

end Cryptarchia.Prob
