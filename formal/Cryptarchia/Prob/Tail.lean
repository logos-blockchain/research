import Cryptarchia.Prob.Good

/-!
# The probability that the good event fails

`settle_bound`: under any kernel within the band, the probability that the good
event `GoodLS` or the growth condition `GrowthS` fails on the sampled string (with
the greedy phase ends) is at most

  `εLong + εCold + εWin + εReach + εDepth`

(`settleEps`). Each term bounds one bad event of `good_of`; the bad indicator is at
most a sum of nonnegative block products, failure counts, and reach moments
(`bad_le`), whose expectations are bounded by `blocks_le`, `cold_anchor` and
`reach_tail`.
-/

namespace Cryptarchia.Prob

open Finset Settle

/-- Some honest leader. -/
def honQ (o : Out) : Prop := o.hon ≠ 0

/-- An occupied slot. -/
def occQ (o : Out) : Prop := o.hon ≠ 0 ∨ o.adv = true

instance : DecidablePred honQ := fun o => inferInstanceAs (Decidable (o.hon ≠ 0))
instance : DecidablePred occQ := fun o => inferInstanceAs (Decidable (o.hon ≠ 0 ∨ o.adv = true))

theorem strOf_fst (l : List Out) {i : ℕ} (hi : 1 ≤ i) : (strOf l i).1 = (l.getD (i - 1) Out.empty).hon.val := by
  have hi0 : i ≠ 0 := by omega
  unfold strOf; simp [hi0, Out.toPair]

theorem strOf_snd (l : List Out) {i : ℕ} (hi : 1 ≤ i) : (strOf l i).2 = (l.getD (i - 1) Out.empty).adv := by
  have hi0 : i ≠ 0 := by omega
  unfold strOf; simp [hi0, Out.toPair]

theorem honQ_iff (l : List Out) {i : ℕ} (hi : 1 ≤ i) : honQ (l.getD (i - 1) Out.empty) ↔ (strOf l i).1 ≠ 0 := by
  rw [strOf_fst l hi]; unfold honQ; constructor
  · intro h h'; exact h (Fin.ext h')
  · intro h h'; exact h (by rw [h']; rfl)

theorem occQ_iff (l : List Out) {i : ℕ} (hi : 1 ≤ i) :
    occQ (l.getD (i - 1) Out.empty) ↔ (1 ≤ (strOf l i).1 ∨ (strOf l i).2 = true) := by
  have h1 := honQ_iff l hi
  unfold honQ at h1; unfold occQ
  rw [strOf_snd l hi, h1, Nat.one_le_iff_ne_zero]

theorem prod_ite_pow {a : ℝ} (P : ℕ → Prop) [DecidablePred P] (n : ℕ) :
    ∏ i ∈ Finset.range n, (if P i then a else 1) = a ^ ((Finset.range n).filter P).card := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Finset.prod_range_succ, ih, Finset.range_add_one, Finset.filter_insert]
    split_ifs with h
    · rw [Finset.card_insert_of_notMem (by simp), pow_succ]
    · rw [mul_one]

theorem occCnt_succ (w : CStr) {a b : ℕ} (hab : a ≤ b) :
    occCnt w a (b + 1) = occCnt w a b + (if 1 ≤ (w (b + 1)).1 ∨ (w (b + 1)).2 = true then 1 else 0) := by
  unfold occCnt
  rw [show Finset.Ioc a (b + 1) = insert (b + 1) (Finset.Ioc a b) by
    ext i; simp only [Finset.mem_Ioc, Finset.mem_insert]; omega, Finset.filter_insert]
  split_ifs with h
  · rw [Finset.card_insert_of_notMem (by simp)]
  · rw [add_zero]

theorem occ_count (l : List Out) (y : ℕ) : ∀ n,
    ((Finset.range n).filter fun k => occQ (l.getD (y + k) Out.empty)).card = occCnt (strOf l) y (y + n) := by
  intro n
  induction n with
  | zero => simp [occCnt]
  | succ n ih =>
    rw [Finset.range_add_one, Finset.filter_insert, show y + (n + 1) = (y + n) + 1 by omega,
      occCnt_succ _ (by omega), ← ih]
    have := occQ_iff l (i := y + n + 1) (by omega)
    rw [show y + n + 1 - 1 = y + n by omega] at this
    split_ifs with h1 h2 h2
    · rw [Finset.card_insert_of_notMem (by simp)]
    · exact absurd (this.1 h1) h2
    · exact absurd (this.2 h2) h1
    · rw [add_zero]

variable {B : Band} {Δ M : ℕ} {κ : Kern}

theorem pr_occ_le (hB : κ.Within B) (l : List Out) : κ.pr l occQ ≤ 1 - B.elo := by
  have hsum := κ.sum_one l
  have he := hB.elo l
  have h1 : ∑ o, κ.p l o = κ.pr l occQ + ∑ o, (if occQ o then 0 else κ.p l o) := by
    unfold Kern.pr; rw [← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl fun o _ => by split_ifs <;> ring
  have h2 : κ.p l ⟨0, false⟩ ≤ ∑ o, (if occQ o then 0 else κ.p l o) := by
    have := Finset.single_le_sum (f := fun o => if occQ o then 0 else κ.p l o)
      (fun o _ => by split_ifs <;> linarith [κ.nonneg l o]) (Finset.mem_univ (⟨0, false⟩ : Out))
    simpa [occQ] using this
  linarith

/-! ## The bad events as products -/

variable (Δ) in
/-- Every block of `Δ` slots after `y` (up to `G`) has an honest leader. -/
noncomputable def longF (G y : ℕ) (h : List Out) : ℝ :=
  ∏ k ∈ Finset.range (G / Δ), blockG honQ 0 1 y Δ Δ k h

/-- `x` to the number of occupied slots in the window before `t`. -/
noncomputable def winF (Lw : ℕ) (x : ℝ) (t : ℕ) (h : List Out) : ℝ :=
  ∏ k ∈ Finset.range (t - (t - Lw)), blockG occQ 1 x (t - Lw) 1 1 k h

/-- `yy` to the number of blocks with an honest leader. -/
noncomputable def depthF (yy : ℝ) (a Lb T nb : ℕ) (h : List Out) : ℝ :=
  ∏ i ∈ Finset.range nb, blockG honQ 1 yy a Lb T i h

open Classical in
theorem blockG_cases (Q : Out → Prop) [DecidablePred Q] (a0 a1 : ℝ) (y Lb T k : ℕ) (h : List Out) :
    blockG Q a0 a1 y Lb T k h = if hitIn Q (y + k * Lb) T h then a1 else a0 := by
  unfold blockG; rfl

theorem longF_one {G y : ℕ} {h : List Out} (hno : ¬ ∃ m, y < m ∧ m ≤ y + G ∧ Quiet Δ (strOf h) m) :
    longF Δ G y h = 1 := by
  classical
  unfold longF
  apply Finset.prod_eq_one
  intro k hk
  rw [Finset.mem_range] at hk
  rw [blockG_cases, if_pos]
  by_contra hnot
  apply hno
  refine ⟨y + k * Δ + Δ, ?_, ?_, ?_⟩
  · rcases Nat.eq_zero_or_pos Δ with h0 | h0
    · simp [h0] at hk
    · omega
  · have : (k + 1) * Δ ≤ G := by
      have := Nat.div_mul_le_self G Δ
      nlinarith [Nat.mul_le_mul_right Δ (show k + 1 ≤ G / Δ by omega)]
    nlinarith
  · intro i h1 h2 h3
    have := honQ_iff h h3
    by_contra hne
    exact hnot ⟨i, by omega, by omega, this.2 hne⟩

theorem winF_eq {Lw : ℕ} {x : ℝ} (t : ℕ) (h : List Out) :
    winF Lw x t h = x ^ occCnt (strOf h) (t - Lw) t := by
  classical
  unfold winF
  simp only [blockG_cases]
  have : ∀ k, hitIn occQ (t - Lw + k * 1) 1 h ↔ occQ (h.getD (t - Lw + k) Out.empty) := by
    intro k; unfold hitIn; constructor
    · rintro ⟨i, h1, h2, h3⟩
      have : i = t - Lw + k + 1 := by omega
      subst this; simpa using h3
    · intro hq; exact ⟨t - Lw + k + 1, by omega, by omega, by simpa using hq⟩
  simp only [this]
  rw [prod_ite_pow, occ_count, show t - Lw + (t - (t - Lw)) = t by omega]

theorem depthF_eq {yy : ℝ} {a Lb T nb : ℕ} (h : List Out) [DecidablePred fun i => blockHon (strOf h) a Lb T i] :
    depthF yy a Lb T nb h = yy ^ ((Finset.range nb).filter fun i => blockHon (strOf h) a Lb T i).card := by
  classical
  unfold depthF
  simp only [blockG_cases]
  have : ∀ i, hitIn honQ (a + i * Lb) T h ↔ blockHon (strOf h) a Lb T i := by
    intro i; unfold hitIn blockHon; constructor
    · rintro ⟨j, h1, h2, h3⟩; exact ⟨j, h1, h2, (honQ_iff h (by omega)).1 h3⟩
    · rintro ⟨j, h1, h2, h3⟩; exact ⟨j, h1, h2, (honQ_iff h (by omega)).2 h3⟩
  simp only [this]
  rw [prod_ite_pow]

/-! ## The bad indicator -/

/-- The parameters of the growth bound for an environment. -/
structure GrowthPar where
  G : ℕ
  r : ℕ
  T : ℕ
  yy : ℝ

/-- The slots of the growth window of an epoch, after the first `G`. -/
def growLen (E : Env) (Δ G : ℕ) : ℕ := E.c.epochLength - E.c.nonceOffset - Δ - 3 - G

/-- The number of depth blocks in an epoch's growth window. -/
def nbD (E : Env) (Δ G T : ℕ) : ℕ := (growLen E Δ G + Δ) / (T + Δ)

/-- The epochs whose state is fixed by `N`. -/
def nEp (E : Env) (N : ℕ) : ℕ := (N + 2) / E.c.epochLength

theorem accH_ge_one {N W k0 : ℕ} {h : List Out} (hne : accH Δ M N W k0 h ≠ 0) : 1 ≤ accH Δ M N W k0 h := by
  classical
  unfold accH acc at *
  obtain ⟨k, hk, hk0⟩ := Finset.exists_ne_zero_of_sum_ne_zero hne
  have hval : failK Δ M N W (strOf h) k0 k = 1 := by
    unfold failK at hk0 ⊢; split_ifs at hk0 ⊢ <;> simp_all
  have := Finset.single_le_sum (f := fun k => failK Δ M N W (strOf h) k0 k)
    (fun i _ => by unfold failK; split_ifs <;> norm_num) hk
  linarith

theorem accH_nonneg {N W k0 : ℕ} (h : List Out) : 0 ≤ accH Δ M N W k0 h := acc_nonneg _ _ _

theorem blockG_nonneg (Q : Out → Prop) [DecidablePred Q] {a0 a1 : ℝ} (h0 : 0 ≤ a0) (h1 : 0 ≤ a1)
    (y Lb T k : ℕ) (h : List Out) : 0 ≤ blockG Q a0 a1 y Lb T k h := by
  rw [blockG_cases]; split_ifs <;> assumption

/-- **The bad indicator is at most a sum of nonnegative terms.** -/
theorem bad_le (E : Env) (hΔ : E.Δ = Δ) (hsane : E.c.Sane) {N W G Lw r T : ℕ} {c x yy : ℝ}
    (hc : 1 ≤ c) (hx : 1 ≤ x) (hyy0 : 0 < yy) (hyy1 : yy ≤ 1) (hT : 1 ≤ T)
    (hNG : N + G < M) (hW : W + 2 * G ≤ Lw) (hGL : G ≤ Lw) {h : List Out} (hlen : h.length = M) :
    (by classical exact if (GoodLS E (strOf h) N Lw (gend Δ M (strOf h)) ∧
        GrowthS E (strOf h) (gend Δ M (strOf h)) N r G) then (0 : ℝ) else 1) ≤
      ∑ y ∈ Finset.range (N + 1), longF Δ G y h +
      ∑ k0 ∈ Finset.range (N + 1), accH Δ M N W k0 h +
      ∑ t ∈ Finset.range (N + 1), winF Lw x t h / x ^ (E.c.k + 1) +
      ∑ j0 ∈ Finset.range (N + G + 1), reachH Δ M c j0 h / c ^ (r + 1) +
      ∑ ep ∈ Finset.Icc 1 (nEp E N),
        depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T) h / yy ^ (E.c.k + r) := by
  classical
  have hc0 : 0 < c := by linarith
  have hx0 : 0 < x := by linarith
  -- every term is nonnegative
  have n1 : ∀ y, 0 ≤ longF Δ G y h := fun y =>
    Finset.prod_nonneg fun k _ => blockG_nonneg _ le_rfl zero_le_one _ _ _ _ _
  have n2 : ∀ k0, 0 ≤ accH Δ M N W k0 h := fun k0 => accH_nonneg h
  have n3 : ∀ t, 0 ≤ winF Lw x t h / x ^ (E.c.k + 1) := fun t => by
    rw [winF_eq]; positivity
  have n4 : ∀ j0, 0 ≤ reachH Δ M c j0 h / c ^ (r + 1) := fun j0 => by
    unfold reachH; split_ifs <;> positivity
  have n5 : ∀ ep, 0 ≤ depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T) h / yy ^ (E.c.k + r) := fun ep => by
    rw [depthF_eq]; positivity
  have s1 := Finset.sum_nonneg fun y (_ : y ∈ Finset.range (N + 1)) => n1 y
  have s2 := Finset.sum_nonneg fun k0 (_ : k0 ∈ Finset.range (N + 1)) => n2 k0
  have s3 := Finset.sum_nonneg fun t (_ : t ∈ Finset.range (N + 1)) => n3 t
  have s4 := Finset.sum_nonneg fun j0 (_ : j0 ∈ Finset.range (N + G + 1)) => n4 j0
  have s5 := Finset.sum_nonneg fun ep (_ : ep ∈ Finset.Icc 1 (nEp E N)) => n5 ep
  split_ifs with hg
  · linarith
  · by_contra hlt
    push Not at hlt
    apply hg
    apply good_of E hΔ hsane hlen hNG hW hGL
    · -- no long phase
      intro y hy
      by_contra hno
      have := longF_one (Δ := Δ) (G := G) hno
      have := Finset.single_le_sum (fun y _ => n1 y) (Finset.mem_range.2 (show y < N + 1 by omega))
      linarith
    · intro k0 hk0
      by_contra hne
      have := accH_ge_one hne
      have := Finset.single_le_sum (fun k0 _ => n2 k0) (Finset.mem_range.2 (show k0 < N + 1 by omega))
      linarith
    · intro t ht
      by_contra hw
      push Not at hw
      have hge : 1 ≤ winF Lw x t h / x ^ (E.c.k + 1) := by
        rw [winF_eq, le_div_iff₀ (by positivity), one_mul]
        exact pow_le_pow_right₀ hx hw
      have := Finset.single_le_sum (fun t _ => n3 t) (Finset.mem_range.2 (show t < N + 1 by omega))
      linarith
    · intro j0 hj0
      by_contra hr
      push Not at hr
      have hjM : j0 ≤ pidx Δ M (strOf h) h.length := by
        rw [hlen]
        by_contra hc'; push Not at hc'
        have := gend_strictMono.monotone (f := gend Δ M (strOf h)) hc'.le
        rw [gend_pidx_M] at this; omega
      have hge : 1 ≤ reachH Δ M c j0 h / c ^ (r + 1) := by
        unfold reachH
        rw [if_pos hjM, le_div_iff₀ (by positivity), one_mul, ← zpow_natCast]
        exact zpow_le_zpow_right₀ hc (by push_cast; omega)
      have hj0' : j0 < N + G + 1 := by have := le_gend (Δ := Δ) (M := M) (w := strOf h) j0; omega
      have := Finset.single_le_sum (fun j0 _ => n4 j0) (Finset.mem_range.2 hj0')
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
          -- the blocks fit in the growth window
          have hfit : E.c.cut ep + G + (nbD E Δ G T - 1) * (T + Δ) + T ≤ E.c.fix ep - Δ - 1 := by
            have h1 : nbD E Δ G T * (T + Δ) ≤ growLen E Δ G + Δ := Nat.div_mul_le_self _ _
            have h2 : (nbD E Δ G T - 1) * (T + Δ) + T + Δ = nbD E Δ G T * (T + Δ) := by
              have : nbD E Δ G T = (nbD E Δ G T - 1) + 1 := by omega
              conv_rhs => rw [this]
              ring
            have hg : T + Δ ≤ growLen E Δ G + Δ := by
              have := (Nat.div_pos_iff (a := growLen E Δ G + Δ) (b := T + Δ)).1 hpos
              exact this.2
            have h3 : E.c.cut ep + G + growLen E Δ G ≤ E.c.fix ep - Δ - 1 := by
              unfold growLen at hg ⊢
              unfold Config.cut Config.fix
              have := epochStart_succ (c := E.c) (ep - 1)
              rw [show ep - 1 + 1 = ep by omega] at this
              omega
            omega
          have hm := hD_mono (Δ := Δ) (w := strOf h) (a := E.c.cut ep + G) hfit
          omega
      have := Finset.single_le_sum (fun ep _ => n5 ep) (Finset.mem_Icc.2 ⟨hep, hepN⟩)
      linarith

/-! ## The bound -/

/-- **The failure probability of the good event.** -/
noncomputable def settleEps (E : Env) (B : Band) (P : ColdCert B Δ) (N W G Lw r T : ℕ) (x yy : ℝ) : ℝ :=
  -- long phases
  (N + 1) * (1 - (1 - B.hhi) ^ Δ) ^ (G / Δ) +
  -- cold failures
  (N + 1) * (P.C W * (1 + (P.b - 1) / (1 - P.lr))) +
  -- crowded windows
  (N + 1) * ((1 + (x - 1) * (1 - B.elo)) ^ Lw / x ^ (E.c.k + 1)) +
  -- large reach
  (N + G + 1) * ((1 + (P.b - 1) / (1 - P.lr)) / P.c ^ (r + 1)) +
  -- slow growth
  nEp E N * ((1 + (yy - 1) * PT 1 yy B.hlo B.hhi T) ^ nbD E Δ G T / yy ^ (E.c.k + r))

theorem Ex_div (n : ℕ) (F : List Out → ℝ) (a : ℝ) (l : List Out) :
    Ex κ n (fun x => F x / a) l = Ex κ n F l / a := by
  simp only [div_eq_mul_inv]
  rw [show (fun x => F x * a⁻¹) = (fun x => a⁻¹ * F x) by ext; ring, Ex_mul_const]; ring

/-- **The good event fails rarely.** Under any kernel within the band, the
probability that `GoodLS` or `GrowthS` fails on the sampled string, with the
greedy phase ends, is at most `settleEps`. -/
theorem settle_bound (E : Env) (hΔ : E.Δ = Δ) (hsane : E.c.Sane) (hB : κ.Within B) (P : ColdCert B Δ)
    {N W G Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy) (hyy1 : yy ≤ 1) (hT : 1 ≤ T)
    (hNM : N + G + Δ + 2 ≤ M) (hW : W + 2 * G ≤ Lw) (hGL : G ≤ Lw)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (helo1 : B.elo ≤ 1) :
    Ex κ M (fun h => by classical exact if (GoodLS E (strOf h) N Lw (gend Δ M (strOf h)) ∧
        GrowthS E (strOf h) (gend Δ M (strOf h)) N r G) then (0 : ℝ) else 1) [] ≤
      settleEps E B P N W G Lw r T x yy := by
  classical
  have hc : 1 ≤ P.c := P.hc
  have hc0 : 0 < P.c := by linarith
  have hEL := hsane.epochLength_pos
  refine (Ex_mono_len (κ := κ) M [] (G := fun h =>
      ∑ y ∈ Finset.range (N + 1), longF Δ G y h +
      ∑ k0 ∈ Finset.range (N + 1), accH Δ M N W k0 h +
      ∑ t ∈ Finset.range (N + 1), winF Lw x t h / x ^ (E.c.k + 1) +
      ∑ j0 ∈ Finset.range (N + G + 1), reachH Δ M P.c j0 h / P.c ^ (r + 1) +
      ∑ ep ∈ Finset.Icc 1 (nEp E N),
        depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T) h / yy ^ (E.c.k + r))
    (fun t ht => by
      simp only [List.nil_append]
      exact bad_le E hΔ hsane hc hx hyy0 hyy1 hT (by omega) hW hGL ht)).trans ?_
  simp only [Ex_add, Ex_sum, Ex_div]
  unfold settleEps
  -- long phases
  have e1 : ∀ y ∈ Finset.range (N + 1), Ex κ M (longF Δ G y) [] ≤ (1 - (1 - B.hhi) ^ Δ) ^ (G / Δ) := by
    intro y hy
    rw [Finset.mem_range] at hy
    have := blocks_le (κ := κ) honQ (a0 := 0) (a1 := 1) (qlo := 0) (qhi := B.hhi) le_rfl zero_le_one
      (fun l => hB.hhi l) (fun l => pr_nonneg l _) hhi1 le_rfl (y := y) (Lb := Δ) (T := Δ)
      (nb := G / Δ) (M := M) le_rfl (by have := Nat.div_mul_le_self G Δ; omega)
    unfold PT at this
    have hl : longF Δ G y = fun x => ∏ k ∈ Finset.range (G / Δ), blockG honQ 0 1 y Δ Δ k x := rfl
    rw [hl]; simpa using this
  -- crowded windows
  have e3 : ∀ t ∈ Finset.range (N + 1), Ex κ M (winF Lw x t) [] ≤ (1 + (x - 1) * (1 - B.elo)) ^ Lw := by
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
  -- cold failures
  have e2 : ∀ k0 ∈ Finset.range (N + 1), Ex κ M (accH Δ M N W k0) [] ≤ P.C W * (1 + (P.b - 1) / (1 - P.lr)) :=
    fun k0 _ => cold_anchor hB P (by omega) k0
  -- large reach
  have e4 : ∀ j0 ∈ Finset.range (N + G + 1), Ex κ M (reachH Δ M P.c j0) [] ≤ 1 + (P.b - 1) / (1 - P.lr) :=
    fun j0 _ => reach_tail hB P (by omega) j0
  -- slow growth
  have e5 : ∀ ep ∈ Finset.Icc 1 (nEp E N), Ex κ M (depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T)) [] ≤
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
  have s3 : ∑ t ∈ Finset.range (N + 1), Ex κ M (winF Lw x t) [] / x ^ (E.c.k + 1) ≤
      ∑ t ∈ Finset.range (N + 1), (1 + (x - 1) * (1 - B.elo)) ^ Lw / x ^ (E.c.k + 1) :=
    Finset.sum_le_sum fun t ht => div_le_div_of_nonneg_right (e3 t ht) (by positivity)
  have s4 : ∑ j0 ∈ Finset.range (N + G + 1), Ex κ M (reachH Δ M P.c j0) [] / P.c ^ (r + 1) ≤
      ∑ j0 ∈ Finset.range (N + G + 1), (1 + (P.b - 1) / (1 - P.lr)) / P.c ^ (r + 1) :=
    Finset.sum_le_sum fun j0 hj => div_le_div_of_nonneg_right (e4 j0 hj) (by positivity)
  have s5 : ∑ ep ∈ Finset.Icc 1 (nEp E N),
      Ex κ M (depthF yy (E.c.cut ep + G) (T + Δ) T (nbD E Δ G T)) [] / yy ^ (E.c.k + r) ≤
      ∑ ep ∈ Finset.Icc 1 (nEp E N), (1 + (yy - 1) * PT 1 yy B.hlo B.hhi T) ^ nbD E Δ G T / yy ^ (E.c.k + r) :=
    Finset.sum_le_sum fun ep hep => div_le_div_of_nonneg_right (e5 ep hep) (by positivity)
  simp only [Finset.sum_const, Finset.card_range, Nat.card_Icc, nsmul_eq_mul] at s1 s2 s3 s4 s5
  push_cast at s1 s2 s3 s4 s5 ⊢
  linarith

end Cryptarchia.Prob
