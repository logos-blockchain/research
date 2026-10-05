import Cryptarchia.Prob.Next

/-!
# The cold condition fails rarely

Fix an anchor phase `k0`. From `k0` on, run the bound process restarted with
margin = reach (`rf`), as in `cold_of_run`. A **failure** at phase `k ≥ k0` is a
phase that ends before `N`, at least `W` slots after phase `k0`, whose margin is
not cold for the next phase (`failK`).

`cold_anchor`: under a kernel within the band, the expected number of failures
anchored at `k0` is at most `C · (1 + b / (1 - λr))`, with

  `C = mz / (θ^W (1 - λp))`.

The proof is a supermartingale over phases (`Ex_phase`). Before `k0` it tracks
`c^ρ` (the reach bound, which has a stationary bound); after `k0` it tracks
`V(ρ, μ) · θ^(slots since k0)`, which contracts by `λp` per phase in expectation
(`ColdCert`), plus the failures so far.
-/

namespace Cryptarchia.Prob

open Finset Settle

/-- The numbers behind the cold bound, and the inequalities they satisfy. -/
structure ColdCert (B : Band) (Δ : ℕ) where
  c : ℝ
  z : ℝ
  s : ℝ
  θ : ℝ
  lp : ℝ
  lr : ℝ
  b : ℝ
  mz : ℝ
  u1 : ℕ → ℝ
  u2 : ℕ → ℝ
  u3 : ℕ → ℝ
  u4 : ℕ → ℝ
  hc : 1 ≤ c
  hz : 1 ≤ z
  hs1 : 1 ≤ s
  hsz : s ≤ z
  hθ : 1 ≤ θ
  hlp : lp < 1
  hlr0 : 0 ≤ lr
  hlr1 : lr < 1
  hb0 : 0 ≤ b
  hb1 : 1 ≤ b
  hmz0 : 0 ≤ mz
  helo : 0 ≤ B.elo
  hΔ : 0 < Δ
  s1 : BurstSol B Δ c θ u1
  s2 : BurstSol B Δ (c * z) θ u2
  s3 : BurstSol B Δ z 1 u3
  s4 : BurstSol B Δ c 1 u4
  /-- warm, positive reach -/
  warm1 : phaseBound B c θ c⁻¹ (u1 0) ≤ lp
  /-- warm, zero reach -/
  warm0 : phaseBound B c θ 1 (u1 0) - (1 - s * z⁻¹) * θ ^ (Δ + 1) * (B.slo * B.elo ^ Δ) ≤ lp
  /-- cold -/
  cold : phaseBound B (c * z) θ s⁻¹ (u2 0) - (s⁻¹ - z⁻¹) * θ ^ (Δ + 1) * (B.slo * B.elo ^ Δ) ≤ lp
  /-- the next phase's adversarial slots -/
  hmz : phaseBound B z 1 1 (u3 0) ≤ mz
  /-- the reach bound, from a positive reach -/
  hlr : phaseBound B c 1 c⁻¹ (u4 0) ≤ lr
  /-- the reach bound, from zero -/
  hb : phaseBound B c 1 1 (u4 0) ≤ b

variable {B : Band} {Δ : ℕ}

/-- The constant of the cold bound. -/
noncomputable def ColdCert.C (P : ColdCert B Δ) (W : ℕ) : ℝ := P.mz / (P.θ ^ W * (1 - P.lp))

theorem ColdCert.C_nonneg (P : ColdCert B Δ) (W : ℕ) : 0 ≤ P.C W := by
  unfold ColdCert.C
  have := P.hθ; have := P.hlp; have := P.hmz0
  apply div_nonneg this (mul_nonneg (pow_nonneg (by linarith) _) (by linarith))

theorem ColdCert.C_eq (P : ColdCert B Δ) (W : ℕ) : P.C W * P.lp + P.mz / P.θ ^ W = P.C W := by
  unfold ColdCert.C
  have h1 : 0 < P.θ ^ W := pow_pos (by linarith [P.hθ]) _
  have h2 : 0 < 1 - P.lp := by linarith [P.hlp]
  field_simp
  ring

/-! ## The bound process from the anchor -/

variable (Δ) (M N W : ℕ)

/-- The reach bound at phase `k0`. -/
noncomputable def rho0 (w : CStr) (k0 : ℕ) : ℤ := (bnd Δ w 0 (gend Δ M w) k0).1

/-- The bound process restarted at phase `k0` with margin = reach. -/
noncomputable def rf (w : CStr) (k0 n : ℕ) : ℤ × ℤ :=
  runFrom (Δ := Δ) (w := w) 0 (gend Δ M w) k0 (rho0 Δ M w k0, rho0 Δ M w k0) n

open Classical in
/-- A failure at phase `k`, anchored at `k0`. -/
noncomputable def failK (w : CStr) (k0 k : ℕ) : ℝ :=
  if gend Δ M w k < N ∧ W + gend Δ M w k0 ≤ gend Δ M w k ∧
      -(advCnt w (gend Δ M w k) (gend Δ M w (k + 1)) : ℤ) ≤ (rf Δ M w k0 (k - k0)).2 then 1 else 0

/-- The failures anchored at `k0` among phases `< j`. -/
noncomputable def acc (w : CStr) (k0 j : ℕ) : ℝ := ∑ k ∈ Finset.Ico k0 j, failK Δ M N W w k0 k

/-- The failures anchored at `k0` that a history has completed. -/
noncomputable def accH (k0 : ℕ) (h : List Out) : ℝ :=
  acc Δ M N W (strOf h) k0 (pidx Δ M (strOf h) h.length)

/-- **The potential.** -/
noncomputable def Φc (P : ColdCert B Δ) (k0 : ℕ) (h : List Out) : ℝ :=
  if pidx Δ M (strOf h) h.length < k0 then
    P.C W * (P.lr ^ (k0 - pidx Δ M (strOf h) h.length) *
      P.c ^ (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) (pidx Δ M (strOf h) h.length)).1 +
      (P.b - P.lr) * ∑ i ∈ Finset.range (k0 - pidx Δ M (strOf h) h.length), P.lr ^ i)
  else acc Δ M N W (strOf h) k0 (pidx Δ M (strOf h) h.length) +
    (if h.length ≤ N then P.C W * (V P.c P.z P.s (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0)) *
      P.θ ^ (h.length - gend Δ M (strOf h) k0)) else 0)

variable {Δ M N W}

theorem bnd_fst_nonneg {w : CStr} {ℓ : ℕ} {e : ℕ → ℕ} : ∀ k, 0 ≤ (bnd Δ w ℓ e k).1
  | 0 => le_rfl
  | k + 1 => by
    simp only [bnd, step]
    exact le_trans (by positivity) (le_max_right _ _)

theorem rf_inv (w : CStr) (k0 : ℕ) : ∀ n, Inv (rf Δ M w k0 n)
  | 0 => inv_start (bnd_fst_nonneg k0)
  | n + 1 => by
    unfold rf at *
    simp only [runFrom]
    exact inv_step (rf_inv w k0 n)

theorem acc_nonneg (w : CStr) (k0 j : ℕ) : 0 ≤ acc Δ M N W w k0 j :=
  Finset.sum_nonneg fun k _ => by unfold failK; split_ifs <;> norm_num

theorem acc_of_lt {w : CStr} {k0 j : ℕ} (h : j ≤ k0) : acc Δ M N W w k0 j = 0 := by
  unfold acc; rw [Finset.Ico_eq_empty_of_le h, Finset.sum_empty]

/-! ## At the next phase end -/

section Next

variable {h h' : List Out} (hpe : PE Δ M h) (hlM : h.length < M) (hf : FirstPE Δ M h h')
include hpe hlM hf

theorem next_pidx : pidx Δ M (strOf h') h'.length = pidx Δ M (strOf h) h.length + 1 :=
  (firstPE_gend hpe hlM hf).2.2

theorem next_gend_last : gend Δ M (strOf h') (pidx Δ M (strOf h) h.length + 1) = h'.length :=
  (firstPE_gend hpe hlM hf).2.1

theorem next_gend {i : ℕ} (hi : i ≤ pidx Δ M (strOf h) h.length) :
    gend Δ M (strOf h') i = gend Δ M (strOf h) i :=
  (firstPE_gend hpe hlM hf).1 i hi

theorem next_sim : SimOn (strOf h') (strOf h) 0 h.length := simOn_prefix hf.pre 0

theorem gend_le_len {i : ℕ} (hi : i ≤ pidx Δ M (strOf h) h.length) :
    gend Δ M (strOf h) i ≤ h.length := by
  have := gend_pidx_pe hpe
  rw [← this]; exact gend_strictMono.monotone hi

theorem next_bnd {i : ℕ} (hi : i ≤ pidx Δ M (strOf h) h.length) :
    bnd Δ (strOf h') 0 (gend Δ M (strOf h')) i = bnd Δ (strOf h) 0 (gend Δ M (strOf h)) i := by
  apply bnd_congr2 gend_mono i
  · intro i' hi'; exact next_gend hpe hlM hf (by omega)
  · rw [next_gend hpe hlM hf hi]
    exact (next_sim hpe hlM hf).mono le_rfl (gend_le_len hpe hlM hf hi)

theorem next_bnd_succ :
    bnd Δ (strOf h') 0 (gend Δ M (strOf h')) (pidx Δ M (strOf h) h.length + 1) =
      step Δ (strOf h') 0 h.length h'.length
        (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) (pidx Δ M (strOf h) h.length)) := by
  simp only [bnd]
  rw [next_bnd hpe hlM hf le_rfl, next_gend hpe hlM hf le_rfl, gend_pidx_pe hpe,
    next_gend_last hpe hlM hf]

theorem next_rho0 {k0 : ℕ} (hk : k0 ≤ pidx Δ M (strOf h) h.length) :
    rho0 Δ M (strOf h') k0 = rho0 Δ M (strOf h) k0 := by
  unfold rho0; rw [next_bnd hpe hlM hf hk]

theorem next_rf {k0 n : ℕ} (hk : k0 + n ≤ pidx Δ M (strOf h) h.length) :
    rf Δ M (strOf h') k0 n = rf Δ M (strOf h) k0 n := by
  unfold rf
  rw [next_rho0 hpe hlM hf (by omega)]
  apply runFrom_congr2 gend_mono k0 _ n
  · intro i hi; exact next_gend hpe hlM hf (by omega)
  · rw [next_gend hpe hlM hf hk]
    exact (next_sim hpe hlM hf).mono le_rfl (gend_le_len hpe hlM hf hk)

theorem next_rf_succ {k0 : ℕ} (hk : k0 ≤ pidx Δ M (strOf h) h.length) :
    rf Δ M (strOf h') k0 (pidx Δ M (strOf h) h.length + 1 - k0) =
      step Δ (strOf h') 0 h.length h'.length
        (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0)) := by
  set j := pidx Δ M (strOf h) h.length with hj
  rw [show j + 1 - k0 = (j - k0) + 1 by omega]
  have hrf := next_rf hpe hlM hf (k0 := k0) (n := j - k0) (by omega)
  unfold rf at hrf ⊢
  simp only [runFrom]
  rw [hrf, show k0 + (j - k0) = j by omega, next_gend hpe hlM hf le_rfl, gend_pidx_pe hpe,
    show j + 1 = pidx Δ M (strOf h) h.length + 1 from rfl, next_gend_last hpe hlM hf]

theorem next_failK {k0 k : ℕ} (hk0 : k0 ≤ k) (hk : k < pidx Δ M (strOf h) h.length) :
    failK Δ M N W (strOf h') k0 k = failK Δ M N W (strOf h) k0 k := by
  unfold failK
  rw [next_gend hpe hlM hf (by omega : k ≤ _), next_gend hpe hlM hf (by omega : k + 1 ≤ _),
    next_gend hpe hlM hf (by omega : k0 ≤ _), next_rf hpe hlM hf (k0 := k0) (n := k - k0) (by omega),
    advCnt_congr ((next_sim hpe hlM hf).mono (Nat.zero_le _) (gend_le_len hpe hlM hf (by omega)))]

theorem next_acc {k0 : ℕ} (hk : k0 ≤ pidx Δ M (strOf h) h.length) :
    acc Δ M N W (strOf h') k0 (pidx Δ M (strOf h) h.length + 1) =
      acc Δ M N W (strOf h) k0 (pidx Δ M (strOf h) h.length) +
        failK Δ M N W (strOf h') k0 (pidx Δ M (strOf h) h.length) := by
  unfold acc
  rw [Finset.sum_Ico_succ_top hk]
  congr 1
  exact Finset.sum_congr rfl fun k hk' => by
    rw [Finset.mem_Ico] at hk'; exact next_failK hpe hlM hf hk'.1 hk'.2

theorem next_failK_last {k0 : ℕ} (hk : k0 ≤ pidx Δ M (strOf h) h.length) :
    failK Δ M N W (strOf h') k0 (pidx Δ M (strOf h) h.length) =
      (by classical exact if h.length < N ∧ W + gend Δ M (strOf h) k0 ≤ h.length ∧
        -(advCnt (strOf h') h.length h'.length : ℤ) ≤
          (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0)).2 then 1 else 0) := by
  unfold failK
  rw [next_gend hpe hlM hf le_rfl, gend_pidx_pe hpe, next_gend_last hpe hlM hf,
    next_gend hpe hlM hf hk, next_rf hpe hlM hf (k0 := k0) (n := _ - k0) (by omega)]

end Next

/-! ## Expectations over the next phase -/

open Classical in
/-- `θ^L` on a crossing phase. -/
noncomputable def crossG (θ : ℝ) (m : ℕ) (h : List Out) : ℝ :=
  θ ^ (h.length - m) * (if Cross (strOf h) 0 m h.length then 1 else 0)

open Classical in
/-- `θ^L` on a phase with an honest success and no adversarial slot. -/
noncomputable def zeroG (θ : ℝ) (m : ℕ) (h : List Out) : ℝ :=
  θ ^ (h.length - m) * (if advCnt (strOf h) m h.length = 0 ∧ HonIn (strOf h) m h.length then 1 else 0)

variable {κ : Kern}

theorem ex_cross (hB : κ.Within B) (helo : 0 ≤ B.elo) (hΔ : 0 < Δ) {θ : ℝ} (hθ : 0 ≤ θ) {h : List Out}
    (hlM : h.length + Δ + 1 ≤ M) :
    B.slo * B.elo ^ Δ * θ ^ (Δ + 1) ≤
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (crossG θ h.length) h := by
  classical
  have hG : ∀ x, 0 ≤ crossG θ h.length x := fun x => by unfold crossG; split_ifs <;> positivity
  have hl := phase_lower (κ := κ) hB helo hΔ hlM hG ⟨1, false⟩ (by decide)
  have hval : crossG θ h.length (h ++ pat ⟨1, false⟩ Δ) = θ ^ (Δ + 1) := by
    unfold crossG
    have hlen : (h ++ pat ⟨1, false⟩ Δ).length = h.length + 1 + Δ := by simp [pat]; omega
    rw [hlen, if_pos (pat_cross h ⟨1, false⟩ rfl rfl)]
    rw [show h.length + 1 + Δ - h.length = Δ + 1 by omega, mul_one]
  rw [hval] at hl
  have hs := hB.slo h
  have : B.slo * B.elo ^ Δ * θ ^ (Δ + 1) ≤ κ.p h ⟨1, false⟩ * B.elo ^ Δ * θ ^ (Δ + 1) := by
    apply mul_le_mul_of_nonneg_right _ (by positivity)
    exact mul_le_mul_of_nonneg_right hs (by positivity)
  linarith

theorem ex_zero (hB : κ.Within B) (helo : 0 ≤ B.elo) (hΔ : 0 < Δ) {θ : ℝ} (hθ : 0 ≤ θ) {h : List Out}
    (hlM : h.length + Δ + 1 ≤ M) :
    B.slo * B.elo ^ Δ * θ ^ (Δ + 1) ≤
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (zeroG θ h.length) h := by
  classical
  have hG : ∀ x, 0 ≤ zeroG θ h.length x := fun x => by unfold zeroG; split_ifs <;> positivity
  have hl := phase_lower (κ := κ) hB helo hΔ hlM hG ⟨1, false⟩ (by decide)
  have hval : zeroG θ h.length (h ++ pat ⟨1, false⟩ Δ) = θ ^ (Δ + 1) := by
    unfold zeroG
    have hlen : (h ++ pat ⟨1, false⟩ Δ).length = h.length + 1 + Δ := by simp [pat]; omega
    rw [hlen, if_pos ⟨pat_advCnt h ⟨1, false⟩ rfl, pat_honIn h ⟨1, false⟩ (by decide)⟩]
    rw [show h.length + 1 + Δ - h.length = Δ + 1 by omega, mul_one]
  rw [hval] at hl
  have hs := hB.slo h
  have : B.slo * B.elo ^ Δ * θ ^ (Δ + 1) ≤ κ.p h ⟨1, false⟩ * B.elo ^ Δ * θ ^ (Δ + 1) := by
    apply mul_le_mul_of_nonneg_right _ (by positivity)
    exact mul_le_mul_of_nonneg_right hs (by positivity)
  linarith

theorem ex_wt (hB : κ.Within B) (hΔ : 0 < Δ) {x θ y : ℝ} (hx : 1 ≤ x) (hθ : 0 ≤ θ) (hy : 0 ≤ y)
    {u : ℕ → ℝ} (hu : BurstSol B Δ x θ u) {h : List Out} (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Wt x θ y h.length) h ≤ phaseBound B x θ y (u 0) :=
  phase_upper hB hx hθ hy hu hΔ (start_of_pe hpe hlM) hlM

/-! ## Pointwise bounds at the next phase end -/

theorem zpow_sub_ind {c : ℝ} (hc : 0 < c) (A : ℕ) (P : Prop) [Decidable P] :
    c ^ ((A : ℤ) - (if P then 1 else 0)) = c ^ A * (if P then c⁻¹ else 1) := by
  split_ifs
  · rw [zpow_sub₀ hc.ne', zpow_natCast, zpow_one, div_eq_mul_inv]
  · simp

theorem wt_def (x θ y : ℝ) (m : ℕ) (h : List Out) [Decidable (HonIn (strOf h) m h.length)] :
    Wt x θ y m h = θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length *
      (if HonIn (strOf h) m h.length then y else 1) := by
  unfold Wt; congr

/-- The potential after one phase, from a state satisfying the invariant. -/
noncomputable def postBound (c z s θ : ℝ) (st : ℤ × ℤ) (m : ℕ) (h : List Out) : ℝ :=
  if 1 ≤ st.1 ∧ st.2 = st.1 then V c z s st * Wt c θ c⁻¹ m h
  else if st.2 < 0 then V c z s st * (Wt (c * z) θ s⁻¹ m h - (s⁻¹ - z⁻¹) * zeroG θ m h)
  else Wt c θ 1 m h - (1 - s * z⁻¹) * crossG θ m h

theorem post_le {c z s θ : ℝ} (hc : 1 ≤ c) (hz : 1 ≤ z) (hs : 1 ≤ s) (hsz : s ≤ z) (hθ : 0 ≤ θ)
    {st : ℤ × ℤ} (hst : Inv st) (m : ℕ) (h : List Out) (hm : m ≤ h.length) :
    V c z s (step Δ (strOf h) 0 m h.length st) * θ ^ (h.length - m) ≤ postBound c z s θ st m h := by
  classical
  have hc0 : 0 < c := by linarith
  have hθL : 0 ≤ θ ^ (h.length - m) := pow_nonneg hθ _
  obtain ⟨h0, h1, h2⟩ := hst
  unfold postBound
  by_cases hw : 1 ≤ st.1 ∧ st.2 = st.1
  · rw [if_pos hw]
    obtain ⟨hρ, hμ⟩ := hw
    have hst : st = (st.1, st.1) := by ext <;> simp [hμ]
    have := warm_pos (Δ := Δ) (w := strOf h) (ℓ := 0) (a := m) (b := h.length) (z := z) (s := s) hc hρ
    rw [← hst] at this
    rw [zpow_sub_ind hc0] at this
    rw [wt_def]
    calc V c z s (step Δ (strOf h) 0 m h.length st) * θ ^ (h.length - m)
        ≤ V c z s st * (c ^ advCnt (strOf h) m h.length *
            (if HonIn (strOf h) m h.length then c⁻¹ else 1)) * θ ^ (h.length - m) := by
          rw [← zpow_natCast] at this ⊢
          exact mul_le_mul_of_nonneg_right this hθL
      _ = _ := by ring
  · rw [if_neg hw]
    by_cases hneg : st.2 < 0
    · rw [if_pos hneg]
      have := cold_step (Δ := Δ) (w := strOf h) (ℓ := 0) (a := m) (b := h.length) hc hz hs hsz h0 hneg h2
      have hzG : zeroG θ m h = θ ^ (h.length - m) *
          (if advCnt (strOf h) m h.length = 0 ∧ HonIn (strOf h) m h.length then 1 else 0) := by
        unfold zeroG; congr
      rw [wt_def, hzG]
      calc V c z s (step Δ (strOf h) 0 m h.length st) * θ ^ (h.length - m)
          ≤ V c z s st * ((c * z) ^ ((advCnt (strOf h) m h.length : ℕ) : ℤ) *
              (if HonIn (strOf h) m h.length then s⁻¹ else 1) -
              (if advCnt (strOf h) m h.length = 0 ∧ HonIn (strOf h) m h.length then s⁻¹ - z⁻¹ else 0)) *
              θ ^ (h.length - m) := mul_le_mul_of_nonneg_right this hθL
        _ = _ := by
          rw [zpow_natCast]
          split_ifs <;> ring
    · rw [if_neg hneg]
      have hμ : st.2 = st.1 := by rcases h1 with h1 | h1 <;> [exact h1; omega]
      have hρ0 : st.1 = 0 := by
        by_contra hne; exact hw ⟨by omega, hμ⟩
      have hst : st = (0, 0) := by ext <;> simp [hρ0, hμ]
      rw [hst]
      have := warm_zero (Δ := Δ) (w := strOf h) (ℓ := 0) (a := m) (b := h.length) (c := c) (z := z) (s := s)
      have hcG : crossG θ m h = θ ^ (h.length - m) *
          (if Cross (strOf h) 0 m h.length then 1 else 0) := by
        unfold crossG; congr
      rw [wt_def, hcG]
      calc V c z s (step Δ (strOf h) 0 m h.length (0, 0)) * θ ^ (h.length - m)
          ≤ (c ^ ((advCnt (strOf h) m h.length : ℕ) : ℤ) -
              (if Cross (strOf h) 0 m h.length then 1 - s * z⁻¹ else 0)) * θ ^ (h.length - m) :=
            mul_le_mul_of_nonneg_right this hθL
        _ = _ := by
          rw [zpow_natCast]
          split_ifs <;> ring

theorem ex_post (hB : κ.Within B) (P : ColdCert B Δ) {st : ℤ × ℤ} (hst : Inv st) {h : List Out}
    (hpe : PE Δ M h) (hlM : h.length + Δ + 1 ≤ M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (postBound P.c P.z P.s P.θ st h.length) h ≤
      V P.c P.z P.s st * P.lp := by
  have hθ0 : 0 ≤ P.θ := by linarith [P.hθ]
  have hz0 : 0 < P.z := by linarith [P.hz]
  have hs0 : 0 < P.s := by linarith [P.hs1]
  have hz1 : 0 ≤ 1 - P.s * P.z⁻¹ := by
    rw [sub_nonneg, ← div_eq_mul_inv, div_le_one hz0]; exact P.hsz
  have hsz' : 0 ≤ P.s⁻¹ - P.z⁻¹ := by
    rw [sub_nonneg]; exact inv_anti₀ hs0 P.hsz
  have hlM' : h.length < M := by omega
  have hVpos := V_pos (c := P.c) (z := P.z) (s := P.s) (by linarith [P.hc]) hz0 hs0 st
  unfold postBound
  by_cases hw : 1 ≤ st.1 ∧ st.2 = st.1
  · simp only [if_pos hw]
    rw [ExPh_mul_const]
    have h1 := ex_wt (κ := κ) (y := P.c⁻¹) hB P.hΔ P.hc hθ0 (inv_nonneg.mpr (by linarith [P.hc]))
      P.s1 hpe hlM'
    exact mul_le_mul_of_nonneg_left (h1.trans P.warm1) hVpos.le
  · simp only [if_neg hw]
    by_cases hneg : st.2 < 0
    · simp only [if_pos hneg]
      rw [ExPh_mul_const, ExPh_sub, ExPh_mul_const]
      have h1 := ex_wt (κ := κ) (y := P.s⁻¹) hB P.hΔ (by nlinarith [P.hc, P.hz]) hθ0 (inv_nonneg.mpr hs0.le)
        P.s2 hpe hlM'
      have h2 := ex_zero (κ := κ) hB P.helo P.hΔ hθ0 hlM
      have h3 := P.cold
      have : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Wt (P.c * P.z) P.θ P.s⁻¹ h.length) h -
          (P.s⁻¹ - P.z⁻¹) * ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (zeroG P.θ h.length) h ≤ P.lp := by
        have := mul_le_mul_of_nonneg_left h2 hsz'
        nlinarith
      exact mul_le_mul_of_nonneg_left this hVpos.le
    · simp only [if_neg hneg]
      obtain ⟨h0, h1, h2⟩ := hst
      have hμ : st.2 = st.1 := by rcases h1 with h1 | h1 <;> [exact h1; omega]
      have hρ0 : st.1 = 0 := by by_contra hne; exact hw ⟨by omega, hμ⟩
      have hV1 : V P.c P.z P.s st = 1 := by rw [V_warm (by omega), hρ0, zpow_zero]
      rw [hV1, one_mul, ExPh_sub, ExPh_mul_const]
      have h1 := ex_wt (κ := κ) hB P.hΔ P.hc hθ0 zero_le_one P.s1 hpe hlM'
      have h2 := ex_cross (κ := κ) hB P.helo P.hΔ hθ0 hlM
      have h3 := P.warm0
      have := mul_le_mul_of_nonneg_left h2 hz1
      nlinarith

theorem postBound_nonneg {c z s θ : ℝ} (hc : 1 ≤ c) (hz : 1 ≤ z) (hs : 1 ≤ s) (hsz : s ≤ z) (hθ : 0 ≤ θ)
    {st : ℤ × ℤ} (hst : Inv st) (m : ℕ) (h : List Out) (hm : m ≤ h.length) : 0 ≤ postBound c z s θ st m h :=
  le_trans (mul_nonneg (V_pos (by linarith) (by linarith) (by linarith) _).le (pow_nonneg hθ _))
    (post_le (Δ := 0) hc hz hs hsz hθ hst m h hm)

theorem wt_one (x y : ℝ) (m : ℕ) (h : List Out) [Decidable (HonIn (strOf h) m h.length)] :
    Wt x 1 y m h = x ^ advCnt (strOf h) m h.length * (if HonIn (strOf h) m h.length then y else 1) := by
  rw [wt_def]; simp

/-- **The potential is a supermartingale over phases.** -/
theorem phi_step (hB : κ.Within B) (P : ColdCert B Δ) (hNM : N + Δ + 1 ≤ M) (k0 : ℕ) {h : List Out}
    (hpe : PE Δ M h) (hlM : h.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φc Δ M N W P k0) h ≤ Φc Δ M N W P k0 h := by
  classical
  have hc0 : 0 < P.c := by linarith [P.hc]
  have hθ0 : 0 ≤ P.θ := by linarith [P.hθ]
  have hC := P.C_nonneg W
  obtain ⟨j, hj⟩ : ∃ j, pidx Δ M (strOf h) h.length = j := ⟨_, rfl⟩
  have hej : gend Δ M (strOf h) j = h.length := by rw [← hj]; exact gend_pidx_pe hpe
  have reach : ∀ (o : Out) (t : List Out), t.length ≤ M - h.length - 1 →
      (∀ k < t.length, ¬ PE Δ M (h ++ [o] ++ t.take k)) →
      (PE Δ M (h ++ [o] ++ t) ∨ t.length = M - h.length - 1) → FirstPE Δ M h (h ++ [o] ++ t) :=
    fun o t ht hk hend => firstPE_of_reached hlM o t ht hk hend
  by_cases hjk : j < k0
  · -- before the anchor: the reach bound
    obtain ⟨ρ, hρ⟩ : ∃ ρ, (bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j).1 = ρ := ⟨_, rfl⟩
    have hρ0 : 0 ≤ ρ := by rw [← hρ]; exact bnd_fst_nonneg j
    obtain ⟨n, hn⟩ : ∃ n, k0 - j = n := ⟨_, rfl⟩
    have hn1 : 1 ≤ n := by omega
    have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φc Δ M N W P k0) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => P.C W * (P.lr ^ (n - 1) *
          (if 1 ≤ ρ then P.c ^ ρ * Wt P.c 1 P.c⁻¹ h.length h' else Wt P.c 1 1 h.length h') +
            (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i)) h := by
      apply ExPh_mono_on
      intro o t ht hk hend
      have hf := reach o t ht hk hend
      generalize hh' : h ++ [o] ++ t = h' at hf ⊢
      have hp' := next_pidx hpe hlM hf
      have hbs := next_bnd_succ hpe hlM hf
      rw [hj] at hp' hbs
      obtain ⟨ρ', hρ'⟩ : ∃ ρ', (bnd Δ (strOf h') 0 (gend Δ M (strOf h')) (j + 1)).1 = ρ' := ⟨_, rfl⟩
      have hρ'0 : 0 ≤ ρ' := by rw [← hρ']; exact bnd_fst_nonneg _
      have hcr : P.c ^ ρ' ≤
          (if 1 ≤ ρ then P.c ^ ρ * Wt P.c 1 P.c⁻¹ h.length h' else Wt P.c 1 1 h.length h') := by
        have := c_pow_reach (Δ := Δ) (w := strOf h') (ℓ := 0) (a := h.length) (b := h'.length) P.hc
          (st := bnd Δ (strOf h) 0 (gend Δ M (strOf h)) j) (by rw [hρ]; exact hρ0) (bnd_le 0 _ j)
        rw [← hρ', hbs]
        rw [hρ] at this
        by_cases h1 : 1 ≤ ρ
        · rw [if_pos h1] at this
          rw [if_pos h1, wt_one]
          refine this.trans (le_of_eq ?_)
          split_ifs with hb
          · rw [zpow_sub₀ hc0.ne', zpow_natCast, zpow_one, div_eq_mul_inv]
          · simp
        · rw [if_neg h1] at this
          rw [if_neg h1, wt_one]
          refine this.trans (le_of_eq ?_)
          rw [zpow_natCast]; simp
      have hval : Φc Δ M N W P k0 h' ≤
          P.C W * (P.lr ^ (n - 1) * P.c ^ ρ' + (P.b - P.lr) * ∑ i ∈ Finset.range (n - 1), P.lr ^ i) := by
        unfold Φc
        rw [hp']
        by_cases hjk' : j + 1 < k0
        · rw [if_pos hjk', show k0 - (j + 1) = n - 1 by omega, hρ']
        · rw [if_neg hjk', acc_of_lt (by omega), zero_add, show n - 1 = 0 by omega]
          simp only [pow_zero, one_mul, Finset.range_zero, Finset.sum_empty, mul_zero, add_zero]
          split_ifs
          · apply mul_le_mul_of_nonneg_left _ hC
            have hk0 : k0 = j + 1 := by omega
            rw [show j + 1 - k0 = 0 by omega]
            unfold rf rho0
            simp only [runFrom]
            have hlast := next_gend_last hpe hlM hf
            rw [hj] at hlast
            rw [hk0, hlast, Nat.sub_self, pow_zero, mul_one, hρ']
            rw [V_warm (show (0 : ℤ) ≤ (ρ', ρ').2 from hρ'0)]
          · exact mul_nonneg hC (zpow_nonneg hc0.le _)
      refine hval.trans ?_
      apply mul_le_mul_of_nonneg_left _ hC
      have := mul_le_mul_of_nonneg_left hcr (pow_nonneg P.hlr0 (n - 1))
      linarith
    refine hle.trans ?_
    have hS : ∑ i ∈ Finset.range n, P.lr ^ i = ∑ i ∈ Finset.range (n - 1), P.lr ^ i + P.lr ^ (n - 1) := by
      rw [show n = (n - 1) + 1 by omega, Finset.sum_range_succ, Nat.add_sub_cancel]
    have hval : Φc Δ M N W P k0 h = P.C W * (P.lr ^ n * P.c ^ ρ + (P.b - P.lr) * ∑ i ∈ Finset.range n, P.lr ^ i) := by
      unfold Φc; rw [hj, if_pos hjk, hn, hρ]
    rw [hval, ExPh_mul_const]
    apply mul_le_mul_of_nonneg_left _ hC
    rw [ExPh_add, ExPh_const, ExPh_mul_const]
    have hcρ : 0 ≤ P.c ^ ρ := zpow_nonneg hc0.le _
    have hlrn : 0 ≤ P.lr ^ (n - 1) := pow_nonneg P.hlr0 _
    have hpow : P.lr ^ n = P.lr ^ (n - 1) * P.lr := by
      rw [← pow_succ, show n - 1 + 1 = n by omega]
    split_ifs with h1
    · rw [ExPh_mul_const]
      have := ex_wt (κ := κ) (y := P.c⁻¹) hB P.hΔ P.hc zero_le_one (inv_nonneg.mpr hc0.le) P.s4 hpe hlM
      have h2 := this.trans P.hlr
      have := mul_le_mul_of_nonneg_left h2 hcρ
      have := mul_le_mul_of_nonneg_left this hlrn
      rw [hS, hpow]
      have hbl : 0 ≤ P.b - P.lr := by linarith [P.hb1, P.hlr1]
      nlinarith [mul_nonneg hbl hlrn]
    · have := ex_wt (κ := κ) (y := 1) hB P.hΔ P.hc zero_le_one zero_le_one P.s4 hpe hlM
      have h2 := this.trans P.hb
      have := mul_le_mul_of_nonneg_left h2 hlrn
      have hc1 : P.c ^ ρ = 1 := by rw [show ρ = 0 by omega, zpow_zero]
      rw [hS, hpow, hc1]
      nlinarith
  · push Not at hjk
    by_cases hmN : h.length ≤ N
    · obtain ⟨st, hst⟩ : ∃ st, rf Δ M (strOf h) k0 (j - k0) = st := ⟨_, rfl⟩
      have hinv : Inv st := by rw [← hst]; exact rf_inv _ k0 _
      obtain ⟨T, hT⟩ : ∃ T, P.θ ^ (h.length - gend Δ M (strOf h) k0) = T := ⟨_, rfl⟩
      have hT0 : 0 ≤ T := by rw [← hT]; exact pow_nonneg hθ0 _
      have hVs := V_pos (c := P.c) (z := P.z) (s := P.s) hc0 (by linarith [P.hz]) (by linarith [P.hs1]) st
      have hk0 : gend Δ M (strOf h) k0 ≤ h.length := by rw [← hej]; exact gend_strictMono.monotone hjk
      have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φc Δ M N W P k0) h ≤
          ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' => acc Δ M N W (strOf h) k0 j +
            (T / P.θ ^ W * V P.c P.z P.s st) * Wt P.z 1 1 h.length h' +
              (P.C W * T) * postBound P.c P.z P.s P.θ st h.length h') h := by
        apply ExPh_mono_on
        intro o t ht hk hend
        have hf := reach o t ht hk hend
        generalize hh' : h ++ [o] ++ t = h' at hf ⊢
        have hm' : h.length ≤ h'.length := hf.lt.le
        have hp' := next_pidx hpe hlM hf
        have hacc := next_acc (N := N) (W := W) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
        have hfl := next_failK_last (N := N) (W := W) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
        have hrs := next_rf_succ hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
        have hgk := next_gend hpe hlM hf (i := k0) (by rw [hj]; exact hjk)
        rw [hj] at hp' hacc hfl hrs
        rw [hst] at hfl hrs
        -- the failure term
        have hfail : failK Δ M N W (strOf h') k0 j ≤ (T / P.θ ^ W * V P.c P.z P.s st) * Wt P.z 1 1 h.length h' := by
          rw [hfl]
          have hWt : Wt P.z 1 1 h.length h' = P.z ^ advCnt (strOf h') h.length h'.length := by
            rw [wt_one]; split_ifs <;> simp
          rw [hWt]
          split_ifs with hc
          · obtain ⟨-, hW, hA⟩ := hc
            have h1 := fail_le P.hc P.hz P.hs1 hinv (advCnt (strOf h') h.length h'.length)
            rw [if_pos hA, zpow_natCast] at h1
            have hTW : 1 ≤ T / P.θ ^ W := by
              rw [le_div_iff₀ (pow_pos (by linarith [P.hθ]) _), one_mul, ← hT]
              exact pow_le_pow_right₀ P.hθ (by omega)
            have := mul_le_mul hTW h1 zero_le_one (by positivity)
            linarith [mul_assoc (T / P.θ ^ W) (V P.c P.z P.s st) (P.z ^ advCnt (strOf h') h.length h'.length)]
          · have : 0 ≤ T / P.θ ^ W := div_nonneg hT0 (pow_nonneg hθ0 _)
            have := pow_nonneg (by linarith [P.hz] : (0 : ℝ) ≤ P.z) (advCnt (strOf h') h.length h'.length)
            positivity
        -- the potential term
        have hpb := postBound_nonneg P.hc P.hz P.hs1 P.hsz hθ0 hinv h.length h' hm'
        have hpot : (if h'.length ≤ N then P.C W * (V P.c P.z P.s (rf Δ M (strOf h') k0 (j + 1 - k0)) *
            P.θ ^ (h'.length - gend Δ M (strOf h') k0)) else 0) ≤
            (P.C W * T) * postBound P.c P.z P.s P.θ st h.length h' := by
          split_ifs
          · rw [hrs, hgk]
            have hpow : P.θ ^ (h'.length - gend Δ M (strOf h) k0) = T * P.θ ^ (h'.length - h.length) := by
              rw [← hT, ← pow_add]; congr 1; omega
            rw [hpow]
            have := post_le (Δ := Δ) P.hc P.hz P.hs1 P.hsz hθ0 hinv h.length h' hm'
            calc P.C W * (V P.c P.z P.s (step Δ (strOf h') 0 h.length h'.length st) * (T * P.θ ^ (h'.length - h.length)))
                = (P.C W * T) * (V P.c P.z P.s (step Δ (strOf h') 0 h.length h'.length st) *
                    P.θ ^ (h'.length - h.length)) := by ring
              _ ≤ _ := mul_le_mul_of_nonneg_left this (mul_nonneg hC hT0)
          · exact mul_nonneg (mul_nonneg hC hT0) hpb
        unfold Φc
        rw [hp', if_neg (by omega), hacc]
        linarith
      refine hle.trans ?_
      have hval : Φc Δ M N W P k0 h = acc Δ M N W (strOf h) k0 j + P.C W * (V P.c P.z P.s st * T) := by
        unfold Φc; rw [hj, if_neg (by omega), if_pos hmN, hst, hT]
      rw [hval, ExPh_add, ExPh_add, ExPh_const, ExPh_mul_const, ExPh_mul_const]
      have h1 := ex_wt (κ := κ) (y := 1) hB P.hΔ P.hz zero_le_one zero_le_one P.s3 hpe hlM
      have h2 := ex_post (κ := κ) hB P hinv hpe (by omega : h.length + Δ + 1 ≤ M)
      have hc1 : 0 ≤ T / P.θ ^ W * V P.c P.z P.s st := mul_nonneg (div_nonneg hT0 (pow_nonneg hθ0 _)) hVs.le
      have e1 := mul_le_mul_of_nonneg_left (h1.trans P.hmz) hc1
      have e2 := mul_le_mul_of_nonneg_left h2 (mul_nonneg hC hT0)
      have hCe := P.C_eq W
      have : T / P.θ ^ W * V P.c P.z P.s st * P.mz + P.C W * T * (V P.c P.z P.s st * P.lp) =
          P.C W * (V P.c P.z P.s st * T) := by
        calc T / P.θ ^ W * V P.c P.z P.s st * P.mz + P.C W * T * (V P.c P.z P.s st * P.lp)
            = T * V P.c P.z P.s st * (P.C W * P.lp + P.mz / P.θ ^ W) := by ring
          _ = _ := by rw [hCe]; ring
      linarith
    · -- past the check horizon: nothing more can fail
      push Not at hmN
      have hle : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (Φc Δ M N W P k0) h ≤
          ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun _ => acc Δ M N W (strOf h) k0 j) h := by
        apply ExPh_mono_on
        intro o t ht hk hend
        have hf := reach o t ht hk hend
        generalize hh' : h ++ [o] ++ t = h' at hf ⊢
        have hp' := next_pidx hpe hlM hf
        have hacc := next_acc (N := N) (W := W) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
        have hfl := next_failK_last (N := N) (W := W) hpe hlM hf (k0 := k0) (by rw [hj]; exact hjk)
        rw [hj] at hp' hacc hfl
        unfold Φc
        rw [hp', if_neg (by omega), hacc, hfl, if_neg (by omega), if_neg (by have := hf.lt; omega)]
        simp
      refine hle.trans ?_
      rw [ExPh_const]
      unfold Φc
      rw [hj, if_neg (by omega), if_neg (by omega), add_zero]

theorem accH_le_phi (P : ColdCert B Δ) (k0 : ℕ) (h : List Out) : accH Δ M N W k0 h ≤ Φc Δ M N W P k0 h := by
  have hC := P.C_nonneg W
  have hc0 : 0 < P.c := by linarith [P.hc]
  unfold accH Φc
  split_ifs with h1 h2
  · rw [acc_of_lt h1.le]
    apply mul_nonneg hC
    apply add_nonneg (mul_nonneg (pow_nonneg P.hlr0 _) (zpow_nonneg hc0.le _))
    exact mul_nonneg (by linarith [P.hb1, P.hlr1]) (Finset.sum_nonneg fun i _ => pow_nonneg P.hlr0 _)
  · have := mul_nonneg hC (mul_nonneg (V_pos (c := P.c) (z := P.z) (s := P.s) hc0 (by linarith [P.hz]) (by linarith [P.hs1]) (rf Δ M (strOf h) k0 (pidx Δ M (strOf h) h.length - k0))).le
      (pow_nonneg (by linarith [P.hθ] : (0 : ℝ) ≤ P.θ) (h.length - gend Δ M (strOf h) k0)))
    linarith
  · linarith

theorem geom_le {r : ℝ} (h0 : 0 ≤ r) (h1 : r < 1) (n : ℕ) : ∑ i ∈ Finset.range n, r ^ i ≤ 1 / (1 - r) := by
  rw [geom_sum_eq (by linarith : r ≠ 1)]
  have hr : 0 < 1 - r := by linarith
  rw [show (r ^ n - 1) / (r - 1) = (1 - r ^ n) / (1 - r) by
    rw [← neg_sub, ← neg_sub (1 : ℝ) r, neg_div_neg_eq]]
  apply div_le_div_of_nonneg_right _ hr.le
  linarith [pow_nonneg h0 n]

/-- The pre-stage bound mixes `1` and the stationary bound. -/
theorem geom_mix {r b : ℝ} (h0 : 0 ≤ r) (h1 : r < 1) (hb : 1 ≤ b) (n : ℕ) :
    r ^ n + (b - r) * ∑ i ∈ Finset.range n, r ^ i ≤ 1 + (b - 1) / (1 - r) := by
  have hr : 0 < 1 - r := by linarith
  rw [geom_sum_eq (by linarith : r ≠ 1)]
  have hrn : r ^ n ≤ 1 := pow_le_one₀ h0 h1.le
  have hrn0 : 0 ≤ r ^ n := pow_nonneg h0 n
  rw [show (r ^ n - 1) / (r - 1) = (1 - r ^ n) / (1 - r) by
    rw [← neg_sub, ← neg_sub (1 : ℝ) r, neg_div_neg_eq]]
  have e1 : r ^ n + (b - r) * ((1 - r ^ n) / (1 - r)) = (r ^ n * (1 - r) + (b - r) * (1 - r ^ n)) / (1 - r) := by
    field_simp
  have e2 : 1 + (b - 1) / (1 - r) = (b - r) / (1 - r) := by
    field_simp; ring
  rw [e1, e2, div_le_div_iff_of_pos_right hr]
  nlinarith

/-- **The failures anchored at one phase are rare.** -/
theorem cold_anchor (hB : κ.Within B) (P : ColdCert B Δ) (hNM : N + Δ + 1 ≤ M) (k0 : ℕ) :
    Ex κ M (accH Δ M N W k0) [] ≤ P.C W * (1 + (P.b - 1) / (1 - P.lr)) := by
  have hM : 0 < M := by omega
  have hC := P.C_nonneg W
  calc Ex κ M (accH Δ M N W k0) [] ≤ Ex κ M (Φc Δ M N W P k0) [] :=
        Ex_mono M (accH_le_phi P k0) []
    _ ≤ Φc Δ M N W P k0 [] := by
        have := Ex_phase (κ := κ) (PE Δ M) (Φ := Φc Δ M N W P k0) (M := M)
          (fun h hpe hlM => phi_step hB P hNM k0 hpe hlM) (pe_nil hM) (by simp)
        simpa using this
    _ ≤ P.C W * (1 + (P.b - 1) / (1 - P.lr)) := by
        have hp0 : pidx Δ M (strOf []) ([] : List Out).length = 0 := by
          apply Nat.eq_zero_of_le_zero
          exact pidx_le_of (by simp [gend_zero])
        unfold Φc
        rw [hp0]
        have hlr := P.hlr1
        have hgeo := geom_le P.hlr0 P.hlr1 k0
        split_ifs with h1 h2
        · apply mul_le_mul_of_nonneg_left _ hC
          have hb0 : (bnd Δ (strOf []) 0 (gend Δ M (strOf [])) 0).1 = 0 := rfl
          rw [hb0, zpow_zero, mul_one, Nat.sub_zero]
          exact geom_mix P.hlr0 P.hlr1 P.hb1 k0
        · have hk : k0 = 0 := by omega
          subst hk
          rw [acc_of_lt le_rfl, zero_add]
          apply mul_le_mul_of_nonneg_left _ hC
          unfold rf rho0
          simp only [runFrom, gend_zero, Nat.sub_self, pow_zero, mul_one, List.length_nil]
          have hb0 : (bnd Δ (strOf []) 0 (gend Δ M (strOf [])) 0).1 = 0 := rfl
          rw [hb0, V_warm (show (0 : ℤ) ≤ ((0 : ℤ), (0 : ℤ)).2 from le_rfl), zpow_zero]
          have : 0 ≤ (P.b - 1) / (1 - P.lr) := div_nonneg (by linarith [P.hb1]) (by linarith)
          linarith
        · simp at h2

end Cryptarchia.Prob
