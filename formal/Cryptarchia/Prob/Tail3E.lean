import Cryptarchia.Prob.Tail2E
import Cryptarchia.Prob.Fail3E

/-!
# The settlement bound with an in-epoch contraction

As `Tail2E.lean`, with failed checks bounded through `fail_checkE3`: the failed-checks
term is `lpi^J · (lp/lpi)^Ccap · e₂ · stat` instead of `lp^J · e₂ · stat`. A failed check
counts only within `Lw` slots of its anchor; the span term already pays for longer spans.
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {B : Band} {Δ M N : ℕ} {κ : Kern}

theorem bad_le3E (E : Env) (hΔ : E.Δ = Δ) (hsane : E.c.Sane) (P : Cert2 B Δ) {G G' J Lw r T : ℕ} {x yy : ℝ}
    (hx : 1 ≤ x) (hyy0 : 0 < yy) (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNG : N + G < M) (hNG' : N + G' < M)
    (hNGG : N + G' + G < M)
    {h : List Out} (hlen : h.length = M) :
    (by classical exact if (GoodLS E (strOf h) N Lw (gend Δ M (strOf h)) ∧
        GrowthS E (strOf h) (gend Δ M (strOf h)) N r G) then (0 : ℝ) else 1) ≤
      ∑ y ∈ Finset.range (N + G' + 1), longF Δ G y h +
      ∑ y ∈ Finset.range (N + 1), occF G' y h +
      ∑ k ∈ Finset.range (N + G' + 1), spanH Δ M P.τ (k - J) (k + 1) h / P.τ ^ (Lw + 1) +
      ∑ k ∈ Finset.Icc J (N + G'), failHE3 Δ M G Lw (N + G') (k - J) k h +
      ∑ t ∈ Finset.range (N + 1), winF Lw x t h / x ^ (E.c.k + 1) +
      ∑ j0 ∈ Finset.range (N + G + 1), reachH2 Δ M P.c j0 h / P.c ^ (r + 1) +
      ∑ ep ∈ Finset.Icc 1 (nEp E N),
        depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T) h / yy ^ (E.c.k + r) := by
  classical
  have hc := P.hc
  have hc0 : 0 < P.c := by linarith
  have hτ : 1 ≤ P.τ := P.hτ
  have hτ0 : 0 < P.τ := by linarith
  have hx0 : 0 < x := by linarith
  have n1 : ∀ y, 0 ≤ longF Δ G y h := fun y =>
    Finset.prod_nonneg fun k _ => blockG_nonneg _ le_rfl zero_le_one _ _ _ _ _
  have n2 : ∀ y, 0 ≤ occF G' y h := fun y =>
    Finset.prod_nonneg fun k _ => blockG_nonneg _ zero_le_one le_rfl _ _ _ _ _
  have n3 : ∀ k, 0 ≤ spanH Δ M P.τ (k - J) (k + 1) h / P.τ ^ (Lw + 1) := fun k =>
    div_nonneg (spanH_nonneg _ hτ0.le _ _ h) (by positivity)
  have n4 : ∀ k, 0 ≤ failHE3 Δ M G Lw (N + G') (k - J) k h := fun k => by
    unfold failHE3 failH; split_ifs
    · exact failC_nonneg _ _ _ _
    · exact le_rfl
    · exact le_rfl
  have n5 : ∀ t, 0 ≤ winF Lw x t h / x ^ (E.c.k + 1) := fun t => by rw [winF_eq]; positivity
  have n6 : ∀ j0, 0 ≤ reachH2 Δ M P.c j0 h / P.c ^ (r + 1) := fun j0 => by
    unfold reachH2; split_ifs <;> positivity
  have n7 : ∀ ep, 0 ≤ depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T) h / yy ^ (E.c.k + r) := fun ep => by
    rw [depthF_eq]; positivity
  have s1 := Finset.sum_nonneg fun y (_ : y ∈ Finset.range (N + G' + 1)) => n1 y
  have s2 := Finset.sum_nonneg fun y (_ : y ∈ Finset.range (N + 1)) => n2 y
  have s3 := Finset.sum_nonneg fun k (_ : k ∈ Finset.range (N + G' + 1)) => n3 k
  have s4 := Finset.sum_nonneg fun k (_ : k ∈ Finset.Icc J (N + G')) => n4 k
  have s5 := Finset.sum_nonneg fun t (_ : t ∈ Finset.range (N + 1)) => n5 t
  have s6 := Finset.sum_nonneg fun j0 (_ : j0 ∈ Finset.range (N + G + 1)) => n6 j0
  have s7 := Finset.sum_nonneg fun ep (_ : ep ∈ Finset.Icc 1 (nEp E N)) => n7 ep
  -- phases before `N + G'` are complete
  have hidx : ∀ k, gend Δ M (strOf h) k < M → k < pidx Δ M (strOf h) h.length := by
    intro k hk
    rw [hlen]
    by_contra hc'; push Not at hc'
    have := gend_strictMono.monotone (f := gend Δ M (strOf h)) hc'
    rw [gend_pidx_M] at this; omega
  split_ifs with hg
  · linarith
  · by_contra hlt
    push Not at hlt
    apply hg
    have hq' : ∀ y ≤ N + G', ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ (strOf h) m := by
      intro y hy
      by_contra hno
      have := longF_one (Δ := Δ) (G := G) hno
      have := Finset.single_le_sum (fun y _ => n1 y) (Finset.mem_range.2 (show y < N + G' + 1 by omega))
      linarith
    apply good_of2 (G := G) (G' := G') (J := J) (Lw := Lw) (r := r) E hΔ hsane hlen hNG hNG'
    · intro y hy
      exact hq' y (by omega)
    · intro y hy
      by_contra hno
      have := occF_one (G' := G') hno
      have := Finset.single_le_sum (fun y _ => n2 y) (Finset.mem_range.2 (show y < N + 1 by omega))
      linarith
    · intro k hk
      by_contra hsp
      push Not at hsp
      have hk1 : k + 1 ≤ pidx Δ M (strOf h) h.length := hidx k (by omega)
      have hge : 1 ≤ spanH Δ M P.τ (k - J) (k + 1) h / P.τ ^ (Lw + 1) := by
        unfold spanH
        rw [if_pos hk1, le_div_iff₀ (by positivity), one_mul]
        apply pow_le_pow_right₀ hτ
        omega
      have hkr : k < N + G' + 1 := by have := le_gend (Δ := Δ) (M := M) (w := strOf h) k; omega
      have := Finset.single_le_sum (fun k _ => n3 k) (Finset.mem_range.2 hkr)
      linarith
    · intro k hk hJ
      by_contra hne
      have hge : 1 ≤ failHE3 Δ M G Lw (N + G') (k - J) k h := by
        have hc1 : failC Δ M (N + G') (k - J) k (strOf h) = 1 ∧ gend Δ M (strOf h) k ≤ N + G' := by
          by_cases hcond : gend Δ M (strOf h) k ≤ N + G' ∧
              -(advCnt (strOf h) (gend Δ M (strOf h) k) (gend Δ M (strOf h) (k + 1)) : ℤ) ≤
                (rf Δ M (strOf h) (k - J) (k - (k - J))).2 ∧
              (1 ≤ advCnt (strOf h) (gend Δ M (strOf h) k) (gend Δ M (strOf h) (k + 1)) ∨
                1 ≤ honCnt (strOf h) (gend Δ M (strOf h) k) (gend Δ M (strOf h) (k + 1)))
          · exact ⟨by unfold failC; rw [if_pos hcond], hcond.1⟩
          · exfalso; apply hne; unfold failC; rw [if_neg hcond]
        have hnl : NoLong Δ M G (k - J) k (strOf h) := fun i h1 h2 =>
          phase_short (N := N + G') hNGG hq'
            (le_trans (gend_strictMono.monotone (f := gend Δ M (strOf h)) (show i ≤ k by omega)) hc1.2)
        have hspk : gend Δ M (strOf h) k ≤ gend Δ M (strOf h) (k - J) + Lw := by
          have hsp : gend Δ M (strOf h) (k + 1) - gend Δ M (strOf h) (k - J) ≤ Lw := by
            by_contra hsp
            push Not at hsp
            have hk1 : k + 1 ≤ pidx Δ M (strOf h) h.length := hidx k (by omega)
            have hge : 1 ≤ spanH Δ M P.τ (k - J) (k + 1) h / P.τ ^ (Lw + 1) := by
              unfold spanH
              rw [if_pos hk1, le_div_iff₀ (by positivity), one_mul]
              apply pow_le_pow_right₀ hτ
              omega
            have hkr : k < N + G' + 1 := by omega
            have := Finset.single_le_sum (fun k _ => n3 k) (Finset.mem_range.2 hkr)
            linarith
          have h1 := gend_strictMono (Δ := Δ) (M := M) (w := strOf h) (show k < k + 1 by omega)
          have h2 := gend_strictMono.monotone (f := gend Δ M (strOf h)) (show k - J ≤ k by omega)
          omega
        unfold failHE3; rw [if_pos ⟨hnl, hspk⟩]
        unfold failH
        rw [if_pos (hidx k (by omega)), hc1.1]
      have := Finset.single_le_sum (fun k _ => n4 k) (Finset.mem_Icc.2 ⟨hJ, hk⟩)
      linarith
    · intro t ht
      by_contra hw
      push Not at hw
      have hge : 1 ≤ winF Lw x t h / x ^ (E.c.k + 1) := by
        rw [winF_eq, le_div_iff₀ (by positivity), one_mul]
        exact pow_le_pow_right₀ hx hw
      have := Finset.single_le_sum (fun t _ => n5 t) (Finset.mem_range.2 (show t < N + 1 by omega))
      linarith
    · intro j0 hj0
      by_contra hr
      push Not at hr
      have hjM : j0 ≤ pidx Δ M (strOf h) h.length := (hidx j0 (by omega)).le
      have hge : 1 ≤ reachH2 Δ M P.c j0 h / P.c ^ (r + 1) := by
        unfold reachH2
        rw [if_pos hjM, le_div_iff₀ (by positivity), one_mul, ← zpow_natCast]
        exact zpow_le_zpow_right₀ hc (by push_cast; omega)
      have hj0' : j0 < N + G + 1 := by have := le_gend (Δ := Δ) (M := M) (w := strOf h) j0; omega
      have := Finset.single_le_sum (fun j0 _ => n6 j0) (Finset.mem_range.2 hj0')
      linarith
    · intro ep hep hfix
      by_contra hd
      push Not at hd
      have hEL := hsane.epochLength_pos
      have hepN : ep ≤ nEp E N := by
        unfold nEp
        rw [Nat.le_div_iff_mul_le hEL]
        unfold Config.fix Config.epochStart at hfix
        omega
      have hge : 1 ≤ depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T) h / yy ^ (E.c.k + r) := by
        rw [depthF_eq, le_div_iff₀ (by positivity), one_mul]
        apply pow_le_pow_of_le_one hyy0.le hyy1
        rcases Nat.eq_zero_or_pos (nbD E Δ G T) with h0 | hpos
        · rw [h0]; simp
        · have hb := hD_blocks (Δ := Δ) (w := strOf h) (y := E.c.cut ep + G) (T := T) (Lb := T + Δ) rfl
            (nbD E Δ G T - 1)
          rw [show nbD E Δ G T - 1 + 1 = nbD E Δ G T by omega] at hb
          have hfit : E.c.cut ep + G + (nbD E Δ G T - 1) * (T + Δ) + T ≤ E.c.fix ep - Δ - 1 := by
            have h1 : nbD E Δ G T * (T + Δ) ≤ growLen E Δ G + Δ := Nat.div_mul_le_self _ _
            have h2 : (nbD E Δ G T - 1) * (T + Δ) + T + Δ = nbD E Δ G T * (T + Δ) := by
              have : nbD E Δ G T = (nbD E Δ G T - 1) + 1 := by omega
              conv_rhs => rw [this]
              ring
            have hg : T + Δ ≤ growLen E Δ G + Δ := ((Nat.div_pos_iff).1 hpos).2
            have h3 : E.c.cut ep + G + growLen E Δ G ≤ E.c.fix ep - Δ - 1 := by
              unfold growLen at hg ⊢
              unfold Config.cut Config.fix
              have := epochStart_succ (c := E.c) (ep - 1)
              rw [show ep - 1 + 1 = ep by omega] at this
              omega
            omega
          have hm := hD_mono (Δ := Δ) (w := strOf h) (a := E.c.cut ep + G) hfit
          omega
      have := Finset.single_le_sum (fun ep _ => n7 ep) (Finset.mem_Icc.2 ⟨hep, hepN⟩)
      linarith

/-- **The failure probability of the good event.** -/
noncomputable def settleEps3E (E : Env) (B : Band) (P : Cert2 B Δ) (lpi : ℝ) (Ccap N G G' J Lw r T : ℕ)
    (x yy : ℝ) : ℝ :=
  -- long phases
  (N + G' + 1) * (1 - (1 - B.hhi) ^ Δ) ^ (G / Δ) +
  -- long empty runs
  (N + 1) * (1 - B.hlo) ^ G' +
  -- long spans of `J + 1` phases
  (N + G' + 1) * (P.e 17 ^ (J + 1) / P.τ ^ (Lw + 1)) +
  -- failed checks
  (N + G' + 1) * (lpi ^ J * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr))) +
  -- crowded windows
  (N + 1) * ((1 + (x - 1) * (1 - B.elo)) ^ Lw / x ^ (E.c.k + 1)) +
  -- large reach
  (N + G + 1) * ((1 + (P.b - 1) / (1 - P.lr)) / P.c ^ (r + 1)) +
  -- slow growth
  nEp E N * ((1 + (yy - 1) * PT 1 yy B.hlo B.hhi T) ^ nbD E Δ G T / yy ^ (E.c.k + r))

theorem settle_bound3E (E : Env) (hΔ : E.Δ = Δ) (hsane : E.c.Sane) (P : Cert2 B Δ) (hB : κ.Within B)
    {G G' J Lw r T : ℕ} (hG : Δ + 1 ≤ G)
    (hR0 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 0 h.length) h ≤ P.lr)
    (hR1 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 1 h.length) h ≤ P.b)
    (hC2 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 2 h.length) h ≤ P.e 2)
    (h17 : ∀ h, PE Δ M h → h.length < M → ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (WP P 17 h.length) h ≤ P.e 17)
    (hE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ h, PE Δ M h → h.length < M →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ P.e i)
    {lpi : ℝ} (hlpi0 : 0 < lpi) (hlpi : lpi ≤ P.lp)
    (Sw : ℕ → Prop) {Ccap : ℕ} (hcap : ∀ t, swCnt Sw t (t + Lw) ≤ Ccap)
    (hIn : ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M → ¬ Sw h.length → ∃ (e : Fin 19 → ℝ) (pat : ℝ),
      ClassOK P lpi e pat ∧
      pat ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG 1 h.length)) h ∧
      ∀ i : Fin 19, i ≠ 2 → i ≠ 17 →
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ e i)
    {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy) (hyy1 : yy ≤ 1) (hT : 1 ≤ T)
    (hNM : N + G + G' + Δ + 2 ≤ M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1) :
    Ex κ M (fun h => by classical exact if (GoodLS E (strOf h) N Lw (gend Δ M (strOf h)) ∧
        GrowthS E (strOf h) (gend Δ M (strOf h)) N r G) then (0 : ℝ) else 1) [] ≤
      settleEps3E E B P lpi Ccap N G G' J Lw r T x yy := by
  classical
  have hc := P.hc
  have hc0 : 0 < P.c := by linarith
  have hτ0 : 0 < P.τ := by linarith [P.hτ]
  have hEL := hsane.epochLength_pos
  have hM : 0 < M := by omega
  refine (Ex_mono_len (κ := κ) M [] (G := fun h =>
      ∑ y ∈ Finset.range (N + G' + 1), longF Δ G y h +
      ∑ y ∈ Finset.range (N + 1), occF G' y h +
      ∑ k ∈ Finset.range (N + G' + 1), spanH Δ M P.τ (k - J) (k + 1) h / P.τ ^ (Lw + 1) +
      ∑ k ∈ Finset.Icc J (N + G'), failHE3 Δ M G Lw (N + G') (k - J) k h +
      ∑ t ∈ Finset.range (N + 1), winF Lw x t h / x ^ (E.c.k + 1) +
      ∑ j0 ∈ Finset.range (N + G + 1), reachH2 Δ M P.c j0 h / P.c ^ (r + 1) +
      ∑ ep ∈ Finset.Icc 1 (nEp E N),
        depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T) h / yy ^ (E.c.k + r))
    (fun t ht => by
      simp only [List.nil_append]
      exact bad_le3E E hΔ hsane P hx hyy0 hyy1 hT (by omega) (by omega) (by omega) ht)).trans ?_
  simp only [Ex_add, Ex_sum, Ex_div]
  unfold settleEps3E
  have e1 : ∀ y ∈ Finset.range (N + G' + 1), Ex κ M (longF Δ G y) [] ≤ (1 - (1 - B.hhi) ^ Δ) ^ (G / Δ) := by
    intro y hy
    rw [Finset.mem_range] at hy
    have := blocks_le (κ := κ) honQ (a0 := 0) (a1 := 1) (qlo := 0) (qhi := B.hhi) le_rfl zero_le_one
      (fun l => hB.hhi l) (fun l => pr_nonneg l _) hhi1 le_rfl (y := y) (Lb := Δ) (T := Δ)
      (nb := G / Δ) (M := M) le_rfl (by have := Nat.div_mul_le_self G Δ; omega)
    unfold PT at this
    have hl : longF Δ G y = fun x => ∏ k ∈ Finset.range (G / Δ), blockG honQ 0 1 y Δ Δ k x := rfl
    rw [hl]; simpa using this
  have e2 : ∀ y ∈ Finset.range (N + 1), Ex κ M (occF G' y) [] ≤ (1 - B.hlo) ^ G' := by
    intro y hy
    rw [Finset.mem_range] at hy
    have := blocks_le (κ := κ) occQ (a0 := 1) (a1 := 0) (qlo := B.hlo) (qhi := 1) zero_le_one le_rfl
      (fun l => pr_le_one l _) (fun l => pr_occ_ge hB l) le_rfl hlo0 (y := y) (Lb := 1) (T := 1)
      (nb := G') (M := M) le_rfl (by omega)
    unfold PT at this
    rw [if_neg (by norm_num)] at this
    have hl : occF G' y = fun x => ∏ i ∈ Finset.range G', blockG occQ 1 0 y 1 1 i x := rfl
    rw [hl]; simpa [sub_eq_add_neg] using this
  have e3 : ∀ k ∈ Finset.range (N + G' + 1), Ex κ M (spanH Δ M P.τ (k - J) (k + 1)) [] ≤ P.e 17 ^ (J + 1) := by
    intro k hk
    have h1 : k - J ≤ k + 1 := Nat.le_succ_of_le (Nat.sub_le k J)
    refine (span_bound' P h17 hM h1).trans (pow_le_pow_right₀ P.he17 ?_)
    omega
  have e4 : ∀ k ∈ Finset.Icc J (N + G'), Ex κ M (failHE3 Δ M G Lw (N + G') (k - J) k) [] ≤
      lpi ^ J * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) := by
    intro k hk
    rw [Finset.mem_Icc] at hk
    have := fail_checkE3 (M := M) P hB hG hR0 hR1 hC2 hE hlpi0 hlpi Sw hcap hIn (Hc := N + G') (by omega)
      (k0 := k - J) (k := k) (by omega)
    rwa [show k - (k - J) = J by omega] at this
  have e5 : ∀ t ∈ Finset.range (N + 1), Ex κ M (winF Lw x t) [] ≤ (1 + (x - 1) * (1 - B.elo)) ^ Lw := by
    intro t ht
    rw [Finset.mem_range] at ht
    have := blocks_le (κ := κ) occQ (a0 := 1) (a1 := x) (qlo := 0) (qhi := 1 - B.elo) zero_le_one
      (by linarith) (fun l => pr_occ_le hB l) (fun l => pr_nonneg l _) (by linarith [P.helo]) le_rfl
      (y := t - Lw) (Lb := 1) (T := 1) (nb := t - (t - Lw)) (M := M) le_rfl (by omega)
    unfold PT at this
    rw [if_pos hx] at this
    simp only [pow_one, sub_sub_cancel] at this
    refine this.trans ?_
    apply pow_le_pow_right₀ _ (by omega)
    have := mul_nonneg (by linarith : (0 : ℝ) ≤ x - 1) (by linarith : (0 : ℝ) ≤ 1 - B.elo)
    linarith
  have e6 : ∀ j0 ∈ Finset.range (N + G + 1), Ex κ M (reachH2 Δ M P.c j0) [] ≤ 1 + (P.b - 1) / (1 - P.lr) :=
    fun j0 _ => reach_tail2' P hR0 hR1 hM j0
  have e7 : ∀ ep ∈ Finset.Icc 1 (nEp E N), Ex κ M (depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T)) [] ≤
      (1 + (yy - 1) * PT 1 yy B.hlo B.hhi T) ^ nbD E Δ G T := by
    intro ep hep
    rw [Finset.mem_Icc] at hep
    have hfixN : E.c.fix ep ≤ N := by
      have := hep.2
      unfold nEp at this
      rw [Nat.le_div_iff_mul_le hEL] at this
      unfold Config.fix Config.epochStart; omega
    have hcf := (hsane.fix_ok ep hep.1).1
    have hfit : E.c.cut ep + G + nbD E Δ G T * (T + Δ) ≤ M := by
      rcases Nat.eq_zero_or_pos (nbD E Δ G T) with h0 | hpos
      · rw [h0]; omega
      · have h1 : nbD E Δ G T * (T + Δ) ≤ growLen E Δ G + Δ := Nat.div_mul_le_self _ _
        have hg : T + Δ ≤ growLen E Δ G + Δ := ((Nat.div_pos_iff).1 hpos).2
        have h3 : E.c.cut ep + G + growLen E Δ G ≤ E.c.fix ep - Δ - 1 := by
          unfold growLen at hg ⊢
          unfold Config.cut Config.fix
          have := epochStart_succ (c := E.c) (ep - 1)
          rw [show ep - 1 + 1 = ep by omega] at this
          omega
        omega
    exact blocks_le (κ := κ) honQ (a0 := 1) (a1 := yy) (qlo := B.hlo) (qhi := B.hhi) zero_le_one hyy0.le
      (fun l => hB.hhi l) (fun l => hB.hlo l) hhi1 hlo0 (y := E.c.cut ep + G) (Lb := T + Δ) (T := T)
      (nb := nbD E Δ G T) (M := M) (by omega) hfit
  have s1 := Finset.sum_le_sum e1
  have s2 := Finset.sum_le_sum e2
  have s3 : ∑ k ∈ Finset.range (N + G' + 1), Ex κ M (spanH Δ M P.τ (k - J) (k + 1)) [] / P.τ ^ (Lw + 1) ≤
      ∑ k ∈ Finset.range (N + G' + 1), P.e 17 ^ (J + 1) / P.τ ^ (Lw + 1) :=
    Finset.sum_le_sum fun k hk => div_le_div_of_nonneg_right (e3 k hk) (by positivity)
  have s4 := Finset.sum_le_sum e4
  have s5 : ∑ t ∈ Finset.range (N + 1), Ex κ M (winF Lw x t) [] / x ^ (E.c.k + 1) ≤
      ∑ t ∈ Finset.range (N + 1), (1 + (x - 1) * (1 - B.elo)) ^ Lw / x ^ (E.c.k + 1) :=
    Finset.sum_le_sum fun t ht => div_le_div_of_nonneg_right (e5 t ht) (by positivity)
  have s6 : ∑ j0 ∈ Finset.range (N + G + 1), Ex κ M (reachH2 Δ M P.c j0) [] / P.c ^ (r + 1) ≤
      ∑ j0 ∈ Finset.range (N + G + 1), (1 + (P.b - 1) / (1 - P.lr)) / P.c ^ (r + 1) :=
    Finset.sum_le_sum fun j0 hj => div_le_div_of_nonneg_right (e6 j0 hj) (by positivity)
  have s7 : ∑ ep ∈ Finset.Icc 1 (nEp E N),
      Ex κ M (depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T)) [] / yy ^ (E.c.k + r) ≤
      ∑ ep ∈ Finset.Icc 1 (nEp E N), (1 + (yy - 1) * PT 1 yy B.hlo B.hhi T) ^ nbD E Δ G T / yy ^ (E.c.k + r) :=
    Finset.sum_le_sum fun ep hep => div_le_div_of_nonneg_right (e7 ep hep) (by positivity)
  have hcard : ((Finset.Icc J (N + G')).card : ℝ) ≤ N + G' + 1 := by
    rw [Nat.card_Icc]; push_cast; have : (↑(N + G' + 1 - J) : ℝ) ≤ ↑(N + G' + 1) := by exact_mod_cast Nat.sub_le _ _
    push_cast at this; linarith
  have hfail0 : 0 ≤ lpi ^ J * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) := by
    have h1 : 0 ≤ P.e 2 := le_trans (ExPh_nonneg _ _ (fun y => WP_nonneg P 2 0 y (by decide)) _)
      (hC2 [] (pe_nil hM) (by simpa using hM))
    have h2 : 0 ≤ (P.b - 1) / (1 - P.lr) := div_nonneg (by linarith [P.hb1]) (by linarith [P.hlr1])
    exact mul_nonneg (mul_nonneg (mul_nonneg (pow_nonneg hlpi0.le _) (pow_nonneg (div_nonneg P.hlp0 hlpi0.le) _)) h1)
      (by linarith)
  simp only [Finset.sum_const, Finset.card_range, Nat.card_Icc, nsmul_eq_mul] at s1 s2 s3 s4 s5 s6 s7
  have s4' : ((N + G' + 1 - J : ℕ) : ℝ) * (lpi ^ J * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr))) ≤
      ((N : ℝ) + G' + 1) * (lpi ^ J * (P.lp / lpi) ^ Ccap * P.e 2 * (1 + (P.b - 1) / (1 - P.lr))) := by
    apply mul_le_mul_of_nonneg_right _ hfail0
    have : ((N + G' + 1 - J : ℕ) : ℝ) ≤ ((N + G' + 1 : ℕ) : ℝ) := by exact_mod_cast Nat.sub_le _ _
    push_cast at this; linarith
  push_cast at s1 s2 s3 s4 s5 s6 s7 s4' ⊢
  linarith

end Cryptarchia.Prob
