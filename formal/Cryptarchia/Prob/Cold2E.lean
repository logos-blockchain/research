import Cryptarchia.Prob.Cold2
import Cryptarchia.Prob.AutoE

/-!
# The potential contracts over truncated phases

With one band member per epoch, phase expectations are bounded only for phases cut
at `G` slots (`phase_autoE`). This file gives the contraction of the potential `V2`
for truncated phases (`ex_post2G`): the same class conditions as `ex_post2`, from
truncated per-expectation bounds. The crossing pattern of the warm-zero class has
`Δ + 1` slots, so it survives the truncation when `Δ + 1 ≤ G` (`ex_cross_trunc`).
-/

namespace Cryptarchia.Prob

open Finset Settle

variable {B : Band} {Δ M : ℕ} {κ : Kern}

/-- A phase function, cut at `G` slots after `m`. -/
noncomputable def truncG (m G : ℕ) (f : List Out → ℝ) (h : List Out) : ℝ := if h.length ≤ m + G then f h else 0

theorem truncG_nonneg {m G : ℕ} {f : List Out → ℝ} (hf : ∀ h, 0 ≤ f h) (h : List Out) : 0 ≤ truncG m G f h := by
  unfold truncG; split_ifs; exacts [hf h, le_rfl]

theorem ex_cross_trunc (hB : κ.Within B) (helo : 0 ≤ B.elo) (hΔ : 0 < Δ) {θ : ℝ} (hθ : 0 ≤ θ) {h : List Out}
    (hlM : h.length + Δ + 1 ≤ M) {G : ℕ} (hG : Δ + 1 ≤ G) :
    B.slo * B.elo ^ Δ * θ ^ (Δ + 1) ≤
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG θ h.length)) h := by
  classical
  have hG0 : ∀ x, 0 ≤ truncG h.length G (crossG θ h.length) x :=
    truncG_nonneg (fun x => by unfold crossG; split_ifs <;> positivity)
  have hl := phase_lower (κ := κ) hB helo hΔ hlM hG0 ⟨1, false⟩ (by decide)
  have hval : truncG h.length G (crossG θ h.length) (h ++ pat ⟨1, false⟩ Δ) = θ ^ (Δ + 1) := by
    have hlen : (h ++ pat ⟨1, false⟩ Δ).length = h.length + 1 + Δ := by simp [pat]; omega
    unfold truncG crossG
    rw [hlen, if_pos (by omega), if_pos (pat_cross h ⟨1, false⟩ rfl rfl)]
    rw [show h.length + 1 + Δ - h.length = Δ + 1 by omega, mul_one]
  rw [hval] at hl
  have hs := hB.slo h
  have : B.slo * B.elo ^ Δ * θ ^ (Δ + 1) ≤ κ.p h ⟨1, false⟩ * B.elo ^ Δ * θ ^ (Δ + 1) := by
    apply mul_le_mul_of_nonneg_right _ (by positivity)
    exact mul_le_mul_of_nonneg_right hs (by positivity)
  linarith

theorem iaOf_ne (st : ℤ × ℤ) : iaOf st ≠ 2 ∧ iaOf st ≠ 17 := by unfold iaOf; split_ifs <;> decide
theorem ibOf_ne (st : ℤ × ℤ) : ibOf st ≠ 2 ∧ ibOf st ≠ 17 := by unfold ibOf; split_ifs <;> decide
theorem iabsOf_ne (st : ℤ × ℤ) : iabsOf st ≠ 2 ∧ iabsOf st ≠ 17 := by unfold iabsOf; split_ifs <;> decide

/-- The class conditions of a contraction `lp` with phase bounds `e` and crossing bound
`pat`, for the potential's constants of `P`. -/
structure ClassOK (P : Cert2 B Δ) (lp : ℝ) (e : Fin 19 → ℝ) (pat : ℝ) : Prop where
  w1 : e 0 ≤ lp
  w0 : e 1 - (1 - (P.s + P.κ) * P.z⁻¹) * pat ≤ lp
  m1r0 : P.s * (e 3 - lp) + P.κ * (e 7 - lp) ≤ 0
  m1r1 : P.s * P.c * (e 4 - lp) + P.κ * P.d * (e 8 - lp) ≤ 0
  m1r2 : P.s * P.c ^ 2 * (e 4 - lp) + P.κ * P.d ^ 2 * (e 9 - lp) ≤ 0
  m1r3a : e 4 ≤ lp
  m1r3 : P.s * P.c ^ 3 * (e 4 - lp) + P.κ * P.d ^ 3 * max (e 10 - lp) 0 + P.κ * e 15 ≤ 0
  m2r0 : P.s * (e 5 - lp) + P.κ * (e 11 - lp) ≤ 0
  m2r1 : P.s * P.c * (e 6 - lp) + P.κ * P.d * (e 12 - lp) ≤ 0
  m2r2 : P.s * P.c ^ 2 * (e 6 - lp) + P.κ * P.d ^ 2 * (e 13 - lp) ≤ 0
  m2r3a : e 6 ≤ lp
  m2r3 : P.s * P.c ^ 3 * (e 6 - lp) + P.κ * P.d ^ 3 * max (e 14 - lp) 0 + P.κ * e 16 ≤ 0

theorem Cert2.classOK (P : Cert2 B Δ) : ClassOK P P.lp P.e (B.slo * B.elo ^ Δ) :=
  ⟨P.w1, P.w0, P.m1r0, P.m1r1, P.m1r2, P.m1r3a, P.m1r3, P.m2r0, P.m2r1, P.m2r2, P.m2r3a, P.m2r3⟩

/-- **The potential contracts by `lp` over one truncated phase**, in every state, for
any phase bounds `e` and crossing bound `pat` meeting the class conditions. -/
theorem ex_post2G_gen (P : Cert2 B Δ) {lp pat : ℝ} {e : Fin 19 → ℝ} (hcl : ClassOK P lp e pat) {G : ℕ}
    {st : ℤ × ℤ} (hst : Inv st) {h : List Out} (hlM : h.length + Δ + 1 ≤ M)
    (hcross : pat ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (crossG 1 h.length)) h)
    (hE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ e i) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (postB2 P st h.length)) h ≤
      lp * V2 P.c P.z P.s P.κ P.d st := by
  have hc := P.hc; have hz := P.hz; have hs := P.hs; have hκ := P.hκ
  have hd0 := P.hd0; have hd1 := P.hd1
  have hc0 : 0 < P.c := by linarith
  have hz0 : 0 < P.z := by linarith
  have hlM' : h.length < M := by omega
  have E : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ e i :=
    fun i h2 h17 => hE i h2 h17
  obtain ⟨h0, h1, h2⟩ := hst
  by_cases hwarm : 1 ≤ st.1 ∧ st.2 = st.1
  · have hT : truncG h.length G (postB2 P st h.length) =
        fun h' => P.c ^ st.1 * truncG h.length G (WP P 0 h.length) h' := by
      funext h'; unfold truncG postB2; rw [if_pos hwarm]; split_ifs <;> ring
    rw [hT, ExPh_mul_const, V2_warm (by omega)]
    have := mul_le_mul_of_nonneg_left ((E 0 (by decide) (by decide)).trans hcl.w1) (by positivity : (0 : ℝ) ≤ P.c ^ st.1)
    linarith
  · by_cases hneg : st.2 < 0
    · rw [V2_cold hneg]
      have hsc : 0 ≤ P.s * P.c ^ st.1 * P.z ^ st.2 := by have := P.hs; positivity
      have hkd : 0 ≤ P.κ * P.d ^ st.1 * P.z ^ st.2 := by positivity
      have hzμ : 0 < P.z ^ st.2 := by positivity
      have hT : truncG h.length G (postB2 P st h.length) = fun h' =>
          P.s * P.c ^ st.1 * P.z ^ st.2 * truncG h.length G (WP P (iaOf st) h.length) h' +
            P.κ * P.d ^ st.1 * P.z ^ st.2 * truncG h.length G (WP P (ibOf st) h.length) h' +
            (if 3 ≤ st.1 then P.κ * P.z ^ st.2 * truncG h.length G (WP P (iabsOf st) h.length) h' else 0) := by
        funext h'; unfold truncG postB2; rw [if_neg hwarm, if_pos hneg]; split_ifs <;> ring
      rw [hT]
      have hlin : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun h' =>
          P.s * P.c ^ st.1 * P.z ^ st.2 * truncG h.length G (WP P (iaOf st) h.length) h' +
            P.κ * P.d ^ st.1 * P.z ^ st.2 * truncG h.length G (WP P (ibOf st) h.length) h' +
            (if 3 ≤ st.1 then P.κ * P.z ^ st.2 * truncG h.length G (WP P (iabsOf st) h.length) h' else 0)) h ≤
          P.s * P.c ^ st.1 * P.z ^ st.2 * e (iaOf st) + P.κ * P.d ^ st.1 * P.z ^ st.2 * e (ibOf st) +
            (if 3 ≤ st.1 then P.κ * P.z ^ st.2 * e (iabsOf st) else 0) := by
        rw [ExPh_add, ExPh_add, ExPh_mul_const, ExPh_mul_const]
        have t1 := mul_le_mul_of_nonneg_left (E (iaOf st) (iaOf_ne st).1 (iaOf_ne st).2) hsc
        have t2 := mul_le_mul_of_nonneg_left (E (ibOf st) (ibOf_ne st).1 (ibOf_ne st).2) hkd
        split_ifs with h3
        · rw [ExPh_mul_const]
          have t3 := mul_le_mul_of_nonneg_left (E (iabsOf st) (iabsOf_ne st).1 (iabsOf_ne st).2)
            (by positivity : (0 : ℝ) ≤ P.κ * P.z ^ st.2)
          linarith
        · rw [ExPh_const]; linarith
      refine hlin.trans ?_
      -- the class conditions
      have key : P.s * P.c ^ st.1 * (e (iaOf st) - lp) + P.κ * P.d ^ st.1 * (e (ibOf st) - lp) +
          (if 3 ≤ st.1 then P.κ * e (iabsOf st) else 0) ≤ 0 := by
        unfold iaOf ibOf iabsOf
        by_cases hm1 : st.2 = -1
        · simp only [hm1, ↓reduceIte]
          by_cases r0 : st.1 = 0
          · simp only [r0, ↓reduceIte, zpow_zero, mul_one]; norm_num; linarith [hcl.m1r0]
          · by_cases r1 : st.1 = 1
            · simp only [r1, ↓reduceIte, zpow_one]; norm_num; linarith [hcl.m1r1]
            · by_cases r2 : st.1 = 2
              · simp only [r2, ↓reduceIte]; norm_num
                have := hcl.m1r2; simp only [pow_two] at this ⊢
                linarith
              · have h3 : 3 ≤ st.1 := by omega
                simp only [r0, r1, r2, ↓reduceIte, h3]
                have hcρ : P.c ^ (3 : ℕ) ≤ P.c ^ st.1 := by
                  rw [← zpow_natCast]; exact zpow_le_zpow_right₀ hc (by exact_mod_cast h3)
                have hdρ : P.d ^ st.1 ≤ P.d ^ (3 : ℕ) := by
                  rw [← zpow_natCast]; exact zpow_le_zpow_right_of_le_one₀ hd0 hd1 (by exact_mod_cast h3)
                have ha := hcl.m1r3a
                have t1 : P.s * P.c ^ st.1 * (e 4 - lp) ≤ P.s * P.c ^ 3 * (e 4 - lp) := by
                  have := mul_le_mul_of_nonneg_left hcρ (by linarith : (0 : ℝ) ≤ P.s)
                  nlinarith
                have t2 : P.κ * P.d ^ st.1 * (e 10 - lp) ≤ P.κ * P.d ^ 3 * max (e 10 - lp) 0 := by
                  have hm := le_max_left (e 10 - lp) 0
                  have hm0 := le_max_right (e 10 - lp) 0
                  have : 0 ≤ P.d ^ st.1 := by positivity
                  have h1' : P.κ * P.d ^ st.1 * (e 10 - lp) ≤ P.κ * P.d ^ st.1 * max (e 10 - lp) 0 :=
                    mul_le_mul_of_nonneg_left hm (by positivity)
                  have h2' : P.κ * P.d ^ st.1 * max (e 10 - lp) 0 ≤ P.κ * P.d ^ 3 * max (e 10 - lp) 0 :=
                    mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hdρ hκ) hm0
                  linarith
                linarith [hcl.m1r3]
        · simp only [hm1, ↓reduceIte]
          by_cases r0 : st.1 = 0
          · simp only [r0, ↓reduceIte, zpow_zero, mul_one]; norm_num; linarith [hcl.m2r0]
          · by_cases r1 : st.1 = 1
            · simp only [r1, ↓reduceIte, zpow_one]; norm_num; linarith [hcl.m2r1]
            · by_cases r2 : st.1 = 2
              · simp only [r2, ↓reduceIte]; norm_num
                have := hcl.m2r2; simp only [pow_two] at this ⊢
                linarith
              · have h3 : 3 ≤ st.1 := by omega
                simp only [r0, r1, r2, ↓reduceIte, h3]
                have hcρ : P.c ^ (3 : ℕ) ≤ P.c ^ st.1 := by
                  rw [← zpow_natCast]; exact zpow_le_zpow_right₀ hc (by exact_mod_cast h3)
                have hdρ : P.d ^ st.1 ≤ P.d ^ (3 : ℕ) := by
                  rw [← zpow_natCast]; exact zpow_le_zpow_right_of_le_one₀ hd0 hd1 (by exact_mod_cast h3)
                have ha := hcl.m2r3a
                have t1 : P.s * P.c ^ st.1 * (e 6 - lp) ≤ P.s * P.c ^ 3 * (e 6 - lp) := by
                  have := mul_le_mul_of_nonneg_left hcρ (by linarith : (0 : ℝ) ≤ P.s)
                  nlinarith
                have t2 : P.κ * P.d ^ st.1 * (e 14 - lp) ≤ P.κ * P.d ^ 3 * max (e 14 - lp) 0 := by
                  have hm := le_max_left (e 14 - lp) 0
                  have hm0 := le_max_right (e 14 - lp) 0
                  have h1' : P.κ * P.d ^ st.1 * (e 14 - lp) ≤ P.κ * P.d ^ st.1 * max (e 14 - lp) 0 :=
                    mul_le_mul_of_nonneg_left hm (by positivity)
                  have h2' : P.κ * P.d ^ st.1 * max (e 14 - lp) 0 ≤ P.κ * P.d ^ 3 * max (e 14 - lp) 0 :=
                    mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hdρ hκ) hm0
                  linarith
                linarith [hcl.m2r3]
      have key' := mul_le_mul_of_nonneg_left key hzμ.le
      split_ifs at key' ⊢ <;> nlinarith
    · push Not at hneg
      have hμ : st.2 = st.1 := by rcases h1 with h1 | h1 <;> [exact h1; omega]
      have hρ0 : st.1 = 0 := by by_contra hne; exact hwarm ⟨by omega, hμ⟩
      have hT : truncG h.length G (postB2 P st h.length) = fun h' =>
          truncG h.length G (WP P 1 h.length) h' - (1 - (P.s + P.κ) * P.z⁻¹) * truncG h.length G (crossG 1 h.length) h' := by
        funext h'; unfold truncG postB2; rw [if_neg hwarm, if_neg (show ¬ st.2 < 0 by omega)]; split_ifs <;> ring
      rw [hT, V2_warm (by omega), hρ0, zpow_zero, mul_one, ExPh_sub, ExPh_mul_const]
      have h1' := E 1 (by decide) (by decide)
      have h2' := hcross
      have hz1 : 0 ≤ 1 - (P.s + P.κ) * P.z⁻¹ := by
        rw [sub_nonneg, ← div_eq_mul_inv, div_le_one hz0]; exact P.hsz
      have := mul_le_mul_of_nonneg_left h2' hz1
      linarith [hcl.w0]

/-- **The potential contracts by `λp` over one truncated phase**, in every state. -/
theorem ex_post2G_at (P : Cert2 B Δ) (hW : κ.Within B) {G : ℕ} (hG : Δ + 1 ≤ G)
    {st : ℤ × ℤ} (hst : Inv st) {h : List Out} (hpe : PE Δ M h) (hlM : h.length + Δ + 1 ≤ M)
    (hE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ P.e i) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (postB2 P st h.length)) h ≤
      P.lp * V2 P.c P.z P.s P.κ P.d st :=
  ex_post2G_gen P P.classOK hst hlM
    (by simpa using ex_cross_trunc (κ := κ) (θ := 1) hW P.helo P.hΔ zero_le_one hlM hG) hE

theorem ex_post2G (P : Cert2 B Δ) (hW : κ.Within B) {G : ℕ} (hG : Δ + 1 ≤ G)
    (hE : ∀ i : Fin 19, i ≠ 2 → i ≠ 17 → ∀ h, PE Δ M h → h.length < M →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (WP P i h.length)) h ≤ P.e i)
    {st : ℤ × ℤ} (hst : Inv st) {h : List Out} (hpe : PE Δ M h) (hlM : h.length + Δ + 1 ≤ M) :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (postB2 P st h.length)) h ≤
      P.lp * V2 P.c P.z P.s P.κ P.d st :=
  ex_post2G_at P hW hG hst hpe hlM fun i h2 h17 => hE i h2 h17 h hpe (by omega)

end Cryptarchia.Prob
