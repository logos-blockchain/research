module

public import Cryptarchia.Prob.TableQ
public import Cryptarchia.Prob.Final3E

/-!
# A table certificate for failed checks

A rational table (`TabQ`) is a failed-check potential (`FailPot`) once each representative state
(`TabPot.IsRep`) passes its contraction check. A certificate gives the representatives in chunks, each
with its data (`RepData`): a terminal table `g` above the table's own (`TabPot.gT`), and
the seeds and bounds of its one-switch tables for that terminal table. The checks (`repChk`) are the
domination, the one-switch tables' checks over the integers (`chkOneF`, as for the certificates' phase
indices), and the contraction: each member's in-epoch bound less the crossing's credit at most `lpi`
times the table's value, and the one-switch bound less the credit at most `lp` times it.
-/

@[expose] public section

namespace Cryptarchia.Prob

/-- **A representative's data**: its terminal table `g` (by `min(A, 2)` and honest success, listed as
`[g 0 false, g 0 true, g 1 false, g 1 true, g 2 false, g 2 true]`), each member's post- and
pre-switch seeds, the members' in-epoch bounds, the largest pre-switch bound, and the members' delayed
bounds with their envelopes `(Z, λ, aZ)`, and the worst band's post- and pre-switch seeds
(`TableGCert.lean`; empty for a single table). -/
structure RepData where
  g : List ℚ
  post : List (List ℤ)
  pre : List (List ℤ)
  eIn : List ℚ
  eE : ℚ
  eD : List ℚ
  env : List (List (List ℤ) × ℚ × ℚ)
  w : List ℤ
  pw : List ℤ

namespace RepData

variable (d : RepData)

/-- The terminal table. -/
def gq : Fin 3 → Bool → Bool → ℚ := fun a b _ => d.g.getD (2 * a.val + if b then 1 else 0) 0

/-- The phase expectation over the integers, at the automaton's factor `x`. -/
def X (x : ℚ) : PhZ := PhZ.ofQ (x, 1, d.gq)

end RepData

namespace TabQ

variable (Q : TabQ)

/-- Adversarial counts the terminal table covers (`TabPot.AX`). -/
def AX : ℕ := Q.R + Q.M + 2

/-- **The representatives**: reach `0 … R + 1`, warm and with margin `-1 … -(M + 1)`. -/
def repList : List (ℤ × ℤ) :=
  (List.range (Q.R + 2)).flatMap fun (r : ℕ) =>
    ((r : ℤ), (r : ℤ)) :: (List.range (Q.M + 1)).map fun (j : ℕ) => ((r : ℤ), -((j : ℤ) + 1))

theorem mem_repList {s : ℤ × ℤ} (h : Q.toPot.IsRep s) : s ∈ Q.repList := by
  obtain ⟨h0, h1, h2⟩ := h
  simp only [toPot_R, toPot_M] at h1 h2
  unfold repList
  rw [List.mem_flatMap]
  refine ⟨s.1.toNat, List.mem_range.2 (show s.1.toNat < Q.R + 2 by omega), ?_⟩
  have hr : ((s.1.toNat : ℕ) : ℤ) = s.1 := Int.toNat_of_nonneg h0
  rcases h2 with h2 | h2
  · rw [List.mem_cons]; left
    exact Prod.ext hr.symm (by rw [hr, h2])
  · rw [List.mem_cons]; right
    rw [List.mem_map]
    refine ⟨(-s.2 - 1).toNat, List.mem_range.2 (show (-s.2 - 1).toNat < Q.M + 1 by omega), Prod.ext hr ?_⟩
    simp only; omega

/-- **The terminal table dominates the table's own**: at each honest flag, the values after zero and one
adversarial slots, and after `2 … AX` over `x^A`. -/
def domQ (s : ℤ × ℤ) (d : RepData) : Bool :=
  [false, true].all fun b =>
    decide (Q.VQ (stepO s 0 (TabPot.bI b) false) ≤ d.gq 0 b false) &&
    decide (Q.VQ (stepO s 1 (TabPot.bI b) false) / Q.x ≤ d.gq 1 b false) &&
    (List.range (Q.AX - 1)).all fun i =>
      decide (Q.VQ (stepO s ((i + 2 : ℕ) : ℤ) (TabPot.bI b) false) / Q.x ^ (i + 2) ≤ d.gq 2 b false)

variable {Q}

theorem gT_le {s : ℤ × ℤ} {d : RepData} (h : Q.domQ s d = true) (a : Fin 3) (b u : Bool) :
    Q.toPot.gT s a b u ≤ castG d.gq a b u := by
  have hb : ∀ b : Bool, _ := fun b => List.all_eq_true.1 h b (by cases b <;> simp)
  have h' := hb b
  simp only [Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true, List.mem_range] at h'
  obtain ⟨⟨h0, h1⟩, h2⟩ := h'
  have hu : ∀ a, d.gq a b u = d.gq a b false := fun _ => rfl
  unfold TabPot.gT castG
  rw [hu]
  split_ifs with ha0 ha1
  · have : a = 0 := Fin.ext ha0
    subst this
    rw [V_cast]; exact_mod_cast h0
  · have : a = 1 := Fin.ext ha1
    subst this
    rw [V_cast, toPot_x]; exact_mod_cast h1
  · have : a = 2 := by fin_cases a <;> simp_all
    subst this
    unfold TabPot.gmax
    refine Finset.sup'_le _ _ fun A hA => ?_
    rw [Finset.mem_Icc] at hA
    have := h2 (A - 2) (by simp only [TabPot.AX, AX, toPot_R, toPot_M] at hA ⊢; omega)
    rw [show A - 2 + 2 = A by omega] at this
    rw [V_cast, toPot_x]; exact_mod_cast this

theorem truncG_sub (m G : ℕ) (f g : List Out → ℝ) :
    truncG m G (fun h => f h - g h) = fun h => truncG m G f h - truncG m G g h := by
  funext h; unfold truncG; split_ifs <;> ring

theorem Wt2_mono {x θ : ℝ} (hx : 0 ≤ x) (hθ : 0 ≤ θ) {g g' : Fin 3 → Bool → Bool → ℝ} (hg : ∀ a b u, g a b u ≤ g' a b u)
    (m : ℕ) (h : List Out) : Wt2 x θ g m h ≤ Wt2 x θ g' m h := by
  unfold Wt2
  exact mul_le_mul_of_nonneg_left (hg _ _ _) (by positivity)

end TabQ

/-! ## The checks -/

namespace FamCfg

variable (F : FamCfg)

/-- The post- and pre-switch seeds and the in-epoch bounds of a representative, by member. -/
def repPost (d : RepData) (k : Fin F.S.K) : Fin 3 → ℤ := seedL (d.post.getD k.val [])
def repPre (d : RepData) (k : Fin F.S.K) : Fin 3 → ℤ := seedL (d.pre.getD k.val [])
def repEIn (d : RepData) (k : Fin F.S.K) : ℚ := d.eIn.getD k.val 0

/-- **A representative's tables**: its terminal table above the table's own; its one-switch tables over
the integers; the crossing's credit nonnegative. -/
def repChkA (Q : TabQ) (s : ℤ × ℤ) (d : RepData) : Bool :=
  Q.domQ s d && decide ((d.X Q.x).Rep Q.x 1 d.gq) &&
    (List.finRange F.S.K).all (chkOneF F.famZ F.D F.Δ (d.X Q.x) SZ (F.repPost d) (F.repPre d) (F.repEIn d) d.eE) &&
    decide (0 ≤ Q.crQ s)

/-- **A representative's contraction**: each member's in-epoch bound less the crossing's credit at most
`lpi` times the table's value; the one-switch bound less the credit (with the weakest band's crossing
bound) at most `lp` times it. -/
def repChkC (Q : TabQ) (Bq : BandR) (lp lpi : ℚ) (s : ℤ × ℤ) (d : RepData) : Bool :=
  (List.finRange F.S.K).all (fun k => decide (F.repEIn d k - Q.crQ s * F.S.patQ F.Δ k ≤ lpi * Q.VQ s)) &&
    decide (d.eE - Q.crQ s * (Bq.slo * Bq.elo ^ F.Δ) ≤ lp * Q.VQ s)

/-- **A representative's checks.** -/
def repChk (Q : TabQ) (Bq : BandR) (lp lpi : ℚ) (s : ℤ × ℤ) (d : RepData) : Bool :=
  F.repChkA Q s d && F.repChkC Q Bq lp lpi s d

/-- **The representatives' tables, in chunks** (the heavy checks, one chunk at a time). -/
def tabChkA {n : ℕ} (Q : TabQ) (D : Fin n → List ((ℤ × ℤ) × RepData)) : Prop :=
  ∀ j, (D j).all (fun p => F.repChkA Q p.1 p.2) = true

/-- **The table certificate's checks**: the shape, every representative covered by a chunk, every
chunk's contractions, and `0 < lpi ≤ lp`. -/
def tabChk {n : ℕ} (Q : TabQ) (Bq : BandR) (lp lpi : ℚ) (D : Fin n → List ((ℤ × ℤ) × RepData)) : Bool :=
  Q.shapeQ && Q.repList.all (fun s => (List.finRange n).any fun j => (D j).any fun p => p.1 == s) &&
    (List.finRange n).all (fun j => (D j).all fun p => F.repChkC Q Bq lp lpi p.1 p.2) &&
    decide (0 < lpi) && decide (lpi ≤ lp)

end FamCfg

section Sound

variable {F : FamCfg} {Q : TabQ} {Bq : BandR} {lp lpi : ℚ} {n : ℕ} {D : Fin n → List ((ℤ × ℤ) × RepData)}
  (h : F.tabChk Q Bq lp lpi D = true)
include h

theorem tabChk_shape : Q.toPot.Shape := by
  simp only [FamCfg.tabChk, Bool.and_eq_true] at h; exact TabQ.shape_of h.1.1.1.1

theorem tabChk_lpi : (0 : ℝ) < lpi ∧ (lpi : ℝ) ≤ lp := by
  simp only [FamCfg.tabChk, Bool.and_eq_true, decide_eq_true_eq] at h
  exact ⟨by exact_mod_cast h.1.2, by exact_mod_cast h.2⟩

theorem tabChk_rep (hA : F.tabChkA Q D) {s : ℤ × ℤ} (hs : Q.toPot.IsRep s) : ∃ d, F.repChk Q Bq lp lpi s d = true := by
  simp only [FamCfg.tabChk, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true, List.any_eq_true,
    beq_iff_eq] at h
  obtain ⟨⟨⟨⟨-, hcov⟩, hall⟩, -⟩, -⟩ := h
  obtain ⟨j, -, p, hp, rfl⟩ := hcov s (TabQ.mem_repList Q hs)
  exact ⟨p.2, by
    simp only [FamCfg.repChk, Bool.and_eq_true]
    exact ⟨List.all_eq_true.1 (hA j) p hp, hall j (List.mem_finRange j) p hp⟩⟩

theorem gq_nonneg {s : ℤ × ℤ} {d : RepData} (hS : Q.toPot.Shape) (hdom : Q.domQ s d = true) (a : Fin 3) (b u : Bool) :
    0 ≤ castG d.gq a b u := by
  refine le_trans ?_ (TabQ.gT_le hdom a b u)
  have hx := TabPot.x_pos hS
  unfold TabPot.gT
  split_ifs
  · exact (TabPot.V_pos hS _).le
  · exact div_nonneg (TabPot.V_pos hS _).le hx.le
  · exact le_trans (div_nonneg (TabPot.V_pos hS _).le (pow_nonneg hx.le _))
      (TabPot.le_gmax (A := 2) le_rfl (by unfold TabPot.AX; omega))

end Sound

/-- **The table certificate as a failed-check potential.** -/
noncomputable def FamCfg.tabFailPot {F : FamCfg} {Q : TabQ} {Bq : BandR} {lp lpi : ℚ} {n : ℕ}
    {D : Fin n → List ((ℤ × ℤ) × RepData)} (h : F.tabChk Q Bq lp lpi D = true) (hA : F.tabChkA Q D) (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D) (hBq : Bq = F.S.weakest)
    (P : Cert2 Bq.toBand F.Δ) (hT : Q.toPot.Ties P) {EL G : ℕ} (hG : F.Δ + 1 ≤ G) (hGEL : G + 1 < EL)
    {κ : Kern} {M : ℕ} (hκ : κ.EpochFam EL F.S.fam) :
    FailPot κ M G P (fun t => ¬ NoSw EL G t) := by
  classical
  have hSh := tabChk_shape h
  have hx := TabPot.x_pos hSh
  have hEL : 0 < EL := by omega
  have hG1 : 1 ≤ G := by have := P.hΔ; omega
  have hW : κ.Within Bq.toBand := hκ.fam.within fun B' hB' => by
    obtain ⟨k, rfl⟩ := List.mem_ofFn.1 hB'
    exact hBq ▸ F.S.weak hS k
  -- the facts of a representative's checks
  have facts : ∀ s, Q.toPot.IsRep s → ∃ d : RepData, Q.domQ s d = true ∧
      AutoSolE F.S.fam F.Δ (Q.x : ℝ) 1 (castG d.gq) (fun k => castZ SZ (preF F.famZ F.D F.Δ (d.X Q.x) SZ (F.repPost d) (F.repPre d) k))
        (fun k => castZ SZ (postF F.famZ F.D F.Δ (d.X Q.x) SZ (F.repPost d) k)) (castZ SZ (vmaxF F.famZ F.D F.Δ (d.X Q.x) SZ (F.repPost d))) ∧
      (∀ k, autoBound (F.S.fam k) (Q.x : ℝ) 1 (castG d.gq) (castZ SZ (postF F.famZ F.D F.Δ (d.X Q.x) SZ (F.repPost d) k)) ≤ F.repEIn d k) ∧
      (∀ k, autoBound (F.S.fam k) (Q.x : ℝ) 1 (castG d.gq)
        (castZ SZ (preF F.famZ F.D F.Δ (d.X Q.x) SZ (F.repPost d) (F.repPre d) k)) ≤ d.eE) ∧
      0 ≤ Q.crQ s ∧ (∀ k, F.repEIn d k - Q.crQ s * F.S.patQ F.Δ k ≤ lpi * Q.VQ s) ∧
      d.eE - Q.crQ s * (Bq.slo * Bq.elo ^ F.Δ) ≤ lp * Q.VQ s := by
    intro s hs
    obtain ⟨d, hd⟩ := tabChk_rep h hA hs
    simp only [FamCfg.repChk, FamCfg.repChkA, FamCfg.repChkC, Bool.and_eq_true, decide_eq_true_eq,
      List.all_eq_true] at hd
    obtain ⟨⟨⟨⟨hdom, hX⟩, hone⟩, hcr⟩, hin, hE⟩ := hd
    have hsound := oneSwitchF_sound (F.S.rep hS) F.S.agrees hD hX SZ_pos (List.all_eq_true.2 hone)
    simp only [Rat.cast_one] at hsound
    exact ⟨d, hdom, hsound.1, hsound.2.1, hsound.2.2, hcr, fun k => hin k (List.mem_finRange k), hE⟩
  refine Q.toPot.toFailPot hSh P hT (tabChk_lpi h).1 (tabChk_lpi h).2 ?_ ?_
  · -- any phase: the one-switch tables, and the weakest band's crossing bound
    intro s hs hh hpe hlM
    obtain ⟨d, hdom, hsol, -, hpre, hcr, -, hE⟩ := facts s hs
    obtain ⟨mem, hband, hmem⟩ := hκ
    have hcrR : 0 ≤ Q.toPot.crT s := by rw [TabQ.crT_cast]; exact_mod_cast hcr
    have hle : ExPh (κ := κ) (PE F.Δ M) (M - hh.length - 1) (truncG hh.length G (Q.toPot.post0 s hh.length)) hh ≤
        ExPh (κ := κ) (PE F.Δ M) (M - hh.length - 1)
          (truncG hh.length G (fun y => Wt2 (Q.x : ℝ) 1 (castG d.gq) hh.length y - Q.toPot.crT s * crossG 1 hh.length y)) hh := by
      refine ExPh_mono_on _ _ _ fun o t _ _ _ => ?_
      unfold truncG TabPot.post0
      split_ifs
      · exact sub_le_sub_right (TabQ.Wt2_mono hx.le zero_le_one (TabQ.gT_le hdom) _ _) _
      · exact le_rfl
    refine hle.trans ?_
    rw [TabQ.truncG_sub, ExPh_sub, TabPot.truncG_mul, ExPh_mul_const]
    have h1 := phase_autoE hsol (gq_nonneg h hSh hdom) mem hband hmem hx.le zero_le_one hEL hGEL hG1 hpre P.hΔ
      (start_of_pe hpe (show hh.length < M by omega)) (show hh.length < M by omega)
    have h2 := ex_cross_trunc (κ := κ) P.helo P.hΔ hlM hG (hW.slo hh) (fun i _ => hW.elo _)
    have hE' : (d.eE : ℝ) - Q.crQ s * (Bq.slo * Bq.elo ^ F.Δ) ≤ lp * Q.VQ s := by exact_mod_cast hE
    rw [TabQ.crT_cast, ← TabQ.V_cast] at *
    simp only [BandR.toBand_slo, BandR.toBand_elo] at h2
    nlinarith [mul_le_mul_of_nonneg_left h2 hcrR]
  · -- an in-epoch phase: the member's own tables and crossing bound
    intro s hs hh hpe hlM hsw
    obtain ⟨d, hdom, hsol, hpost, -, hcr, hin, -⟩ := facts s hs
    obtain ⟨mem, hband, hmem⟩ := hκ
    have hnb : NoSw EL G hh.length := not_not.1 hsw
    have hcrR : 0 ≤ Q.toPot.crT s := by rw [TabQ.crT_cast]; exact_mod_cast hcr
    have hle : ExPh (κ := κ) (PE F.Δ M) (M - hh.length - 1) (truncG hh.length G (Q.toPot.post0 s hh.length)) hh ≤
        ExPh (κ := κ) (PE F.Δ M) (M - hh.length - 1)
          (truncG hh.length G (fun y => Wt2 (Q.x : ℝ) 1 (castG d.gq) hh.length y - Q.toPot.crT s * crossG 1 hh.length y)) hh := by
      refine ExPh_mono_on _ _ _ fun o t _ _ _ => ?_
      unfold truncG TabPot.post0
      split_ifs
      · exact sub_le_sub_right (TabQ.Wt2_mono hx.le zero_le_one (TabQ.gT_le hdom) _ _) _
      · exact le_rfl
    refine hle.trans ?_
    rw [TabQ.truncG_sub, ExPh_sub, TabPot.truncG_mul, ExPh_mul_const]
    have h1 := phase_autoIn hsol.post (gq_nonneg h hSh hdom) mem hband hmem hx.le zero_le_one hG1 (hpost (mem hh)) P.hΔ
      (start_of_pe hpe (show hh.length < M by omega)) (show hh.length < M by omega) hnb
    have h2 := ex_cross_truncIn mem hband hmem (F.S.pat_le F.Δ (mem hh)) (F.S.elo hS) P.hΔ hlM hG hnb
    have hin' : (F.repEIn d (mem hh) : ℝ) - Q.crQ s * F.S.patQ F.Δ (mem hh) ≤ lpi * Q.VQ s := by
      exact_mod_cast hin (mem hh)
    rw [TabQ.crT_cast, ← TabQ.V_cast] at *
    nlinarith [mul_le_mul_of_nonneg_left h2 hcrR]

end Cryptarchia.Prob
