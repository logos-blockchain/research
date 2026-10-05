import Cryptarchia.Prob.Potential

/-!
# Expectations over one phase

From a phase end `m` (a quiet slot, or genesis), the next phase is either one slot
with no honest success, or a **burst**: it starts at an honest slot and ends after
`Δ` slots with no honest success (or at the horizon `M`). We bound, under any
kernel within a band of per-slot probabilities (`Band`, `Kern.Within`):

* `phase_upper`: `E[θ^L · x^A · y^B]` from above (`L` the phase length, `A` its
  adversarial slots, `B` whether it has an honest success), through a solution `u`
  of the burst recursion (`BurstSol`);
* `phase_lower`: the probability of one fixed pattern (one honest slot, no
  adversary, then `Δ` empty slots) from below. It is a crossing, and a phase with
  no adversarial slot.
-/

namespace Cryptarchia.Prob

open Finset Settle

/-! ## Bands of per-slot probabilities -/

/-- Bounds on the next slot's distribution, valid after every history. -/
structure Band where
  /-- `P(some honest leader) ≤ hhi` -/
  hhi : ℝ
  /-- `P(some honest leader) ≥ hlo` -/
  hlo : ℝ
  /-- `P(adversary wins) ≤ amax` -/
  amax : ℝ
  /-- `P(some honest leader and the adversary wins) ≤ hahi` -/
  hahi : ℝ
  /-- `P(exactly one honest leader, adversary does not win) ≥ slo` -/
  slo : ℝ
  /-- `P(some honest leader, adversary does not win) ≥ hnlo` -/
  hnlo : ℝ
  /-- `P(empty slot) ≥ elo` -/
  elo : ℝ
  /-- `P(adversary wins) ≥ alo` -/
  alo : ℝ := 0
  /-- `P(some honest leader and the adversary wins) ≥ halo` -/
  halo : ℝ := 0

/-- The kernel is within the band after every history. -/
structure Kern.Within (κ : Kern) (B : Band) : Prop where
  hhi : ∀ l, κ.pr l (fun o => o.hon ≠ 0) ≤ B.hhi
  hlo : ∀ l, B.hlo ≤ κ.pr l (fun o => o.hon ≠ 0)
  amax : ∀ l, κ.pr l (fun o => o.adv = true) ≤ B.amax
  hahi : ∀ l, κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) ≤ B.hahi
  slo : ∀ l, B.slo ≤ κ.p l ⟨1, false⟩
  hnlo : ∀ l, B.hnlo ≤ κ.p l ⟨1, false⟩ + κ.p l ⟨2, false⟩
  elo : ∀ l, B.elo ≤ κ.p l ⟨0, false⟩
  alo : ∀ l, B.alo ≤ κ.pr l (fun o => o.adv = true)
  halo : ∀ l, B.halo ≤ κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true)

variable {κ : Kern} {B : Band}

/-- The next slot's law after history `l` is within the band. -/
structure Kern.BandAt (κ : Kern) (B : Band) (l : List Out) : Prop where
  hhi : κ.pr l (fun o => o.hon ≠ 0) ≤ B.hhi
  hlo : B.hlo ≤ κ.pr l (fun o => o.hon ≠ 0)
  amax : κ.pr l (fun o => o.adv = true) ≤ B.amax
  hahi : κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) ≤ B.hahi
  slo : B.slo ≤ κ.p l ⟨1, false⟩
  hnlo : B.hnlo ≤ κ.p l ⟨1, false⟩ + κ.p l ⟨2, false⟩
  elo : B.elo ≤ κ.p l ⟨0, false⟩
  alo : B.alo ≤ κ.pr l (fun o => o.adv = true)
  halo : B.halo ≤ κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true)

/-- **A family of bands**: after every history, the next slot's law is within one
of the bands (which one may depend on the history). -/
def Kern.Fam (κ : Kern) (Bs : List Band) : Prop := ∀ l, ∃ B ∈ Bs, κ.BandAt B l

theorem Kern.Within.at {κ : Kern} {B : Band} (h : κ.Within B) (l : List Out) : κ.BandAt B l :=
  ⟨h.hhi l, h.hlo l, h.amax l, h.hahi l, h.slo l, h.hnlo l, h.elo l, h.alo l, h.halo l⟩

theorem Kern.Within.fam {κ : Kern} {B : Band} (h : κ.Within B) : κ.Fam [B] :=
  fun l => ⟨B, List.mem_singleton_self B, h.at l⟩

/-- `H` is weaker than `B` in every bound: a law within `B` is within `H`. -/
structure Band.Weaker (H B : Band) : Prop where
  hhi : B.hhi ≤ H.hhi
  hlo : H.hlo ≤ B.hlo
  amax : B.amax ≤ H.amax
  hahi : B.hahi ≤ H.hahi
  slo : H.slo ≤ B.slo
  hnlo : H.hnlo ≤ B.hnlo
  elo : H.elo ≤ B.elo
  alo : H.alo ≤ B.alo
  halo : H.halo ≤ B.halo

theorem Band.Weaker.refl (B : Band) : B.Weaker B :=
  ⟨le_rfl, le_rfl, le_rfl, le_rfl, le_rfl, le_rfl, le_rfl, le_rfl, le_rfl⟩

/-- A kernel within a family is within any band weaker than all of its members. -/
theorem Kern.Fam.within {κ : Kern} {Bs : List Band} {H : Band} (hF : κ.Fam Bs)
    (hw : ∀ B ∈ Bs, H.Weaker B) : κ.Within H := by
  refine ⟨fun l => ?_, fun l => ?_, fun l => ?_, fun l => ?_, fun l => ?_, fun l => ?_, fun l => ?_,
    fun l => ?_, fun l => ?_⟩ <;> obtain ⟨B, hB, hl⟩ := hF l <;> have w := hw B hB
  · exact hl.hhi.trans w.hhi
  · exact w.hlo.trans hl.hlo
  · exact hl.amax.trans w.amax
  · exact hl.hahi.trans w.hahi
  · exact w.slo.trans hl.slo
  · exact w.hnlo.trans hl.hnlo
  · exact w.elo.trans hl.elo
  · exact w.alo.trans hl.alo
  · exact w.halo.trans hl.halo


/-- The adversary factor of a slot. -/
def advF (x : ℝ) (o : Out) : ℝ := if o.adv then x else 1

theorem advF_nonneg {x : ℝ} (hx : 0 ≤ x) (o : Out) : 0 ≤ advF x o := by
  unfold advF; split_ifs <;> linarith

theorem pr_le_one (l : List Out) (P : Out → Prop) [DecidablePred P] : κ.pr l P ≤ 1 := by
  unfold Kern.pr
  calc ∑ o, (if P o then κ.p l o else 0) ≤ ∑ o, κ.p l o :=
        Finset.sum_le_sum fun o _ => by split_ifs <;> linarith [κ.nonneg l o]
    _ = 1 := κ.sum_one l

theorem pr_nonneg (l : List Out) (P : Out → Prop) [DecidablePred P] : 0 ≤ κ.pr l P := by
  unfold Kern.pr
  exact Finset.sum_nonneg fun o _ => by split_ifs <;> linarith [κ.nonneg l o]

/-- **One slot.** With an adversary factor `x ≥ 1`, value `U1` after an honest
success and `U2` otherwise. -/
theorem slot_sum (hB : κ.Within B) (l : List Out) {x U1 U2 : ℝ} (hx : 1 ≤ x) (hU2 : 0 ≤ U2) :
    ∑ o, κ.p l o * (advF x o * (if o.hon ≠ 0 then U1 else U2)) ≤
      (1 + B.amax * (x - 1)) * U2 +
        (U1 - U2) * (if U2 ≤ U1 then B.hhi + (x - 1) * B.hahi else B.hlo) := by
  have hsplit : ∀ o, κ.p l o * (advF x o * (if o.hon ≠ 0 then U1 else U2)) =
      U2 * (κ.p l o + (x - 1) * (if o.adv = true then κ.p l o else 0)) +
        (U1 - U2) * ((if o.hon ≠ 0 then κ.p l o else 0) +
          (x - 1) * (if o.hon ≠ 0 ∧ o.adv = true then κ.p l o else 0)) := by
    intro o; unfold advF
    by_cases h1 : o.hon ≠ 0 <;> by_cases h2 : o.adv = true <;> simp [h1, h2] <;> ring
  simp only [hsplit, Finset.sum_add_distrib, ← Finset.mul_sum]
  rw [κ.sum_one]
  have e1 : ∑ o, (if o.adv = true then κ.p l o else 0) = κ.pr l (fun o => o.adv = true) := rfl
  have e2 : ∑ o, (if o.hon ≠ 0 then κ.p l o else 0) = κ.pr l (fun o => o.hon ≠ 0) := rfl
  have e3 : ∑ o, (if o.hon ≠ 0 ∧ o.adv = true then κ.p l o else 0) =
      κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) := rfl
  rw [e1, e2, e3]
  have ha := hB.amax l
  have hh := hB.hhi l
  have hlo := hB.hlo l
  have hha := hB.hahi l
  have h0 : 0 ≤ κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) := pr_nonneg l _
  have hx1 : 0 ≤ x - 1 := by linarith
  have t1 : U2 * (1 + (x - 1) * κ.pr l (fun o => o.adv = true)) ≤ (1 + B.amax * (x - 1)) * U2 := by
    have := mul_le_mul_of_nonneg_left ha (mul_nonneg hx1 hU2)
    nlinarith
  split_ifs with hU
  · have : (U1 - U2) * (κ.pr l (fun o => o.hon ≠ 0) + (x - 1) * κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true))
        ≤ (U1 - U2) * (B.hhi + (x - 1) * B.hahi) := by
      apply mul_le_mul_of_nonneg_left _ (by linarith)
      nlinarith
    linarith
  · have : (U1 - U2) * (κ.pr l (fun o => o.hon ≠ 0) + (x - 1) * κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true))
        ≤ (U1 - U2) * B.hlo := by
      apply mul_le_mul_of_nonpos_left _ (by linarith)
      nlinarith
    linarith

/-! ## Phase ends as a stopping rule -/

/-- A history ends a phase: it reaches the horizon, or its last slot is quiet. -/
def PE (Δ M : ℕ) (x : List Out) : Prop :=
  x.length = M ∨ (x.length < M ∧ Quiet Δ (strOf x) x.length)

noncomputable instance (Δ M : ℕ) : DecidablePred (PE Δ M) := Classical.decPred _

variable {Δ M : ℕ}

theorem advCnt_succ (w : CStr) {a b : ℕ} (hab : a ≤ b) :
    advCnt w a (b + 1) = advCnt w a b + (if (w (b + 1)).2 = true then 1 else 0) := by
  have h := advCnt_add (w := w) hab (show b ≤ b + 1 by omega)
  have h1 : advCnt w b (b + 1) = (if (w (b + 1)).2 = true then 1 else 0) := by
    unfold advCnt
    rw [show Finset.Ioc b (b + 1) = {b + 1} by ext; simp only [Finset.mem_Ioc, Finset.mem_singleton]; omega]
    by_cases hb : (w (b + 1)).2 = true <;> simp [Finset.filter_singleton, hb]
  omega

theorem strOf_sim (x t : List Out) (a : ℕ) : SimOn (strOf (x ++ t)) (strOf x) a x.length :=
  SimOn.of_eq fun i _ hi => strOf_append_of_le hi

theorem advCnt_snoc (x : List Out) (o : Out) {m : ℕ} (hm : m ≤ x.length) :
    advCnt (strOf (x ++ [o])) m (x.length + 1) =
      advCnt (strOf x) m x.length + (if o.adv = true then 1 else 0) := by
  rw [advCnt_succ _ hm, advCnt_congr (strOf_sim x [o] m), strOf_last]
  rfl

theorem honIn_snoc (x : List Out) (o : Out) {m : ℕ} (hm : m ≤ x.length) :
    HonIn (strOf (x ++ [o])) m (x.length + 1) ↔ HonIn (strOf x) m x.length ∨ o.hon ≠ 0 := by
  constructor
  · rintro ⟨i, h1, h2, h3⟩
    rcases Nat.lt_or_ge i (x.length + 1) with hi | hi
    · left; refine ⟨i, h1, by omega, ?_⟩
      rwa [strOf_append_of_le (by omega)] at h3
    · right
      have : i = x.length + 1 := by omega
      subst this
      rw [strOf_last] at h3
      intro h; apply h3; simp [Out.toPair, h]
  · rintro (⟨i, h1, h2, h3⟩ | h)
    · exact ⟨i, h1, by omega, by rwa [strOf_append_of_le h2]⟩
    · refine ⟨x.length + 1, by omega, le_rfl, ?_⟩
      rw [strOf_last]
      simp only [Out.toPair]
      intro h'; apply h; exact Fin.ext h'

/-- The weight of a history for a phase that started at `m`. -/
noncomputable def Wt (x θ y : ℝ) (m : ℕ) (h : List Out) : ℝ :=
  θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length *
    (by classical exact if HonIn (strOf h) m h.length then y else 1)

theorem Wt_snoc {x θ y : ℝ} {m : ℕ} (h : List Out) (o : Out) (hm : m ≤ h.length) :
    Wt x θ y m (h ++ [o]) =
      θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length * (θ * advF x o) *
        (by classical exact if HonIn (strOf h) m h.length ∨ o.hon ≠ 0 then y else 1) := by
  classical
  unfold Wt
  simp only [List.length_append, List.length_singleton]
  rw [advCnt_snoc h o hm, show h.length + 1 - m = (h.length - m) + 1 by omega, pow_succ, pow_add]
  have : (if HonIn (strOf (h ++ [o])) m (h.length + 1) then y else 1) =
      (if HonIn (strOf h) m h.length ∨ o.hon ≠ 0 then y else 1) := by
    simp only [honIn_snoc h o hm]
  rw [this]
  unfold advF
  split_ifs <;> simp only [pow_add, pow_one, add_zero, pow_zero, mul_one] <;> ring

/-- In a burst: the last honest slot is `p > m`, followed by `q` slots with none. -/
structure InBurst (m : ℕ) (h : List Out) (q : ℕ) : Prop where
  p_gt : m + q < h.length
  hon : (strOf h (h.length - q)).1 ≠ 0
  quiet : ∀ i, h.length - q < i → i ≤ h.length → (strOf h i).1 = 0

theorem InBurst.honIn {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) :
    HonIn (strOf h) m h.length := ⟨h.length - q, by have := hb.p_gt; omega, by omega, hb.hon⟩

theorem InBurst.not_quiet {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) (hq : q < Δ) :
    ¬ Quiet Δ (strOf h) h.length := by
  intro hQ
  have := hb.p_gt
  exact hb.hon (hQ _ (by omega) (by omega) (by have := hb.p_gt; omega))

theorem InBurst.quiet_of {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) (hq : Δ ≤ q) :
    Quiet Δ (strOf h) h.length := fun i h1 h2 _ => hb.quiet i (by omega) h2

theorem InBurst.snoc_hon {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) (o : Out) (ho : o.hon ≠ 0) :
    InBurst m (h ++ [o]) 0 := by
  refine ⟨by simp; have := hb.p_gt; omega, ?_, ?_⟩
  · simp only [List.length_append, List.length_singleton, Nat.sub_zero]
    rw [strOf_last]; simp only [Out.toPair]; intro h'; exact ho (Fin.ext h')
  · intro i h1 h2; simp at h1 h2; omega

theorem InBurst.snoc_empty {m : ℕ} {h : List Out} {q : ℕ} (hb : InBurst m h q) (o : Out) (ho : o.hon = 0) :
    InBurst m (h ++ [o]) (q + 1) := by
  have hp := hb.p_gt
  refine ⟨by simp; omega, ?_, ?_⟩
  · simp only [List.length_append, List.length_singleton]
    rw [show h.length + 1 - (q + 1) = h.length - q by omega, strOf_append_of_le (by omega)]
    exact hb.hon
  · intro i h1 h2
    simp only [List.length_append, List.length_singleton] at h1 h2
    rcases Nat.lt_or_ge i (h.length + 1) with hi | hi
    · rw [strOf_append_of_le (by omega)]; exact hb.quiet i (by omega) (by omega)
    · have : i = h.length + 1 := by omega
      subst this; rw [strOf_last]; simp [Out.toPair, ho]

/-- A solution of the burst recursion for adversary factor `x` and tilt `θ`:
`u q` bounds the rest of a burst `q` slots after its last honest success. -/
structure BurstSol (B : Band) (Δ : ℕ) (x θ : ℝ) (u : ℕ → ℝ) : Prop where
  one_le : ∀ q ≤ Δ, 1 ≤ u q
  le_zero : ∀ q ≤ Δ, u q ≤ u 0
  step : ∀ q < Δ, θ * ((1 + B.amax * (x - 1)) * u (q + 1) +
    (u 0 - u (q + 1)) * (B.hhi + (x - 1) * B.hahi)) ≤ u q

/-- **Inside a burst.** -/
theorem burst_le (hB : κ.Within B) {x θ y : ℝ} (hx : 1 ≤ x) (hθ : 0 ≤ θ) (hy : 0 ≤ y) {u : ℕ → ℝ}
    (hu : BurstSol B Δ x θ u) {m : ℕ} :
    ∀ (n : ℕ) (h : List Out) (q : ℕ), InBurst m h q → q < Δ → h.length + n = M →
      ExU (κ := κ) (PE Δ M) n (Wt x θ y m) h ≤ Wt x θ y m h * u q
  | 0, h, q, hb, hq, hn => by
    -- at the horizon: impossible inside a burst before `M`... the history is a phase end
    have hPE : PE Δ M h := Or.inl (by omega)
    rw [ExU_stop _ _ _ hPE]
    have := hu.one_le q hq.le
    have hW : 0 ≤ Wt x θ y m h := by unfold Wt; split_ifs <;> positivity
    nlinarith
  | n + 1, h, q, hb, hq, hn => by
    classical
    have hm : m ≤ h.length := by have := hb.p_gt; omega
    have hnPE : ¬ PE Δ M h := by
      rintro (h1 | ⟨-, h2⟩)
      · omega
      · exact hb.not_quiet hq h2
    rw [ExU_go _ _ _ hnPE]
    have hHon := hb.honIn
    set W0 := θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length with hW0
    have hW0n : 0 ≤ W0 := by positivity
    have hWh : Wt x θ y m h = W0 * y := by
      unfold Wt; simp only [hHon, ↓reduceIte, hW0]
    -- each continuation
    have hcont : ∀ o, ExU (κ := κ) (PE Δ M) n (Wt x θ y m) (h ++ [o]) ≤
        W0 * y * θ * (advF x o * (if o.hon ≠ 0 then u 0 else u (q + 1))) := by
      intro o
      have hWo : Wt x θ y m (h ++ [o]) = W0 * y * θ * advF x o := by
        rw [Wt_snoc h o hm]; simp only [hHon, true_or, ↓reduceIte]; rw [hW0]; ring
      have hlen : (h ++ [o]).length + n = M := by simp; omega
      by_cases ho : o.hon ≠ 0
      · simp only [ho, ↓reduceIte, ne_eq, not_false_eq_true]
        have hb' := hb.snoc_hon o ho
        by_cases hD0 : 0 < Δ
        · calc ExU (κ := κ) (PE Δ M) n (Wt x θ y m) (h ++ [o]) ≤ Wt x θ y m (h ++ [o]) * u 0 :=
                burst_le hB hx hθ hy hu n (h ++ [o]) 0 hb' hD0 hlen
            _ = _ := by rw [hWo]; ring
        · omega
      · push Not at ho
        simp only [ho, ne_eq, not_true_eq_false, ↓reduceIte]
        have hb' := hb.snoc_empty o ho
        by_cases hq1 : q + 1 < Δ
        · calc ExU (κ := κ) (PE Δ M) n (Wt x θ y m) (h ++ [o]) ≤ Wt x θ y m (h ++ [o]) * u (q + 1) :=
                burst_le hB hx hθ hy hu n (h ++ [o]) (q + 1) hb' hq1 hlen
            _ = _ := by rw [hWo]; ring
        · -- the burst ends here
          have hPE : PE Δ M (h ++ [o]) := by
            by_cases hM : (h ++ [o]).length = M
            · exact Or.inl hM
            · exact Or.inr ⟨by simp at hM ⊢; omega, hb'.quiet_of (by omega)⟩
          rw [ExU_stop _ _ _ hPE, hWo]
          have h1 := hu.one_le (q + 1) (by omega)
          have : 0 ≤ W0 * y * θ * advF x o := by
            have := advF_nonneg (by linarith : (0 : ℝ) ≤ x) o; positivity
          nlinarith
    calc ∑ o, κ.p h o * ExU (κ := κ) (PE Δ M) n (Wt x θ y m) (h ++ [o])
        ≤ ∑ o, κ.p h o * (W0 * y * θ * (advF x o * (if o.hon ≠ 0 then u 0 else u (q + 1)))) :=
          Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (hcont o) (κ.nonneg h o)
      _ = W0 * y * θ * ∑ o, κ.p h o * (advF x o * (if o.hon ≠ 0 then u 0 else u (q + 1))) := by
          rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun o _ => by ring
      _ ≤ W0 * y * θ * ((1 + B.amax * (x - 1)) * u (q + 1) +
            (u 0 - u (q + 1)) * (B.hhi + (x - 1) * B.hahi)) := by
          apply mul_le_mul_of_nonneg_left _ (by positivity)
          have := slot_sum hB h hx (U1 := u 0) (U2 := u (q + 1))
            (by linarith [hu.one_le (q + 1) (by omega)])
          rwa [if_pos (hu.le_zero (q + 1) (by omega))] at this
      _ = W0 * y * (θ * ((1 + B.amax * (x - 1)) * u (q + 1) +
            (u 0 - u (q + 1)) * (B.hhi + (x - 1) * B.hahi))) := by ring
      _ ≤ W0 * y * u q := mul_le_mul_of_nonneg_left (hu.step q hq) (by positivity)
      _ = Wt x θ y m h * u q := by rw [hWh]

/-- A phase start: genesis, or a quiet slot. -/
def Start (Δ : ℕ) (l : List Out) : Prop := l.length = 0 ∨ Quiet Δ (strOf l) l.length

theorem start_snoc_empty {l : List Out} (hl : Start Δ l) (o : Out) (ho : o.hon = 0) :
    Quiet Δ (strOf (l ++ [o])) (l.length + 1) := by
  intro i h1 h2 h3
  rcases Nat.lt_or_ge i (l.length + 1) with hi | hi
  · rw [strOf_append_of_le (by omega)]
    rcases hl with h0 | hq
    · omega
    · exact hq i (by omega) (by omega) h3
  · have : i = l.length + 1 := by omega
    subst this; rw [strOf_last]; simp [Out.toPair, ho]

/-- The phase's bound. -/
noncomputable def phaseBound (B : Band) (x θ y u0 : ℝ) : ℝ :=
  θ * ((1 + B.amax * (x - 1)) +
    (y * u0 - 1) * (if 1 ≤ y * u0 then B.hhi + (x - 1) * B.hahi else B.hlo))

/-- **One phase, from above.** -/
theorem phase_upper (hB : κ.Within B) {x θ y : ℝ} (hx : 1 ≤ x) (hθ : 0 ≤ θ) (hy : 0 ≤ y)
    {u : ℕ → ℝ} (hu : BurstSol B Δ x θ u) (hΔ : 0 < Δ) {l : List Out} (hl : Start Δ l)
    (hlM : l.length < M) :
    ExPh (κ := κ) (PE Δ M) (M - l.length - 1) (Wt x θ y l.length) l ≤ phaseBound B x θ y (u 0) := by
  classical
  set m := l.length with hm
  have hcont : ∀ o, ExU (κ := κ) (PE Δ M) (M - m - 1) (Wt x θ y m) (l ++ [o]) ≤
      θ * (advF x o * (if o.hon ≠ 0 then y * u 0 else 1)) := by
    intro o
    have hl0 : ¬ HonIn (strOf l) l.length l.length := by
      rintro ⟨i, h1, h2, -⟩; omega
    have hWo : Wt x θ y m (l ++ [o]) = θ * advF x o * (if o.hon ≠ 0 then y else 1) := by
      rw [hm, Wt_snoc l o le_rfl]
      simp only [hl0, false_or, Nat.sub_self, pow_zero, advCnt_self, one_mul]
    have hlen : (l ++ [o]).length + (M - m - 1) = M := by simp; omega
    by_cases ho : o.hon ≠ 0
    · simp only [ho, ne_eq, not_false_eq_true, ↓reduceIte]
      have hb : InBurst m (l ++ [o]) 0 := by
        refine ⟨by simp [hm], ?_, ?_⟩
        · simp only [List.length_append, List.length_singleton, Nat.sub_zero]
          rw [strOf_last]; simp only [Out.toPair]; intro h'; exact ho (Fin.ext h')
        · intro i h1 h2; simp at h1 h2; omega
      calc ExU (κ := κ) (PE Δ M) (M - m - 1) (Wt x θ y m) (l ++ [o])
          ≤ Wt x θ y m (l ++ [o]) * u 0 := burst_le hB hx hθ hy hu _ _ 0 hb hΔ hlen
        _ = θ * (advF x o * (y * u 0)) := by rw [hWo, if_pos ho]; ring
    · have hne := ho
      push Not at ho
      rw [if_neg hne, mul_one]
      have hPE : PE Δ M (l ++ [o]) := by
        by_cases hM : (l ++ [o]).length = M
        · exact Or.inl hM
        · exact Or.inr ⟨by simp at hM ⊢; omega, by simpa using start_snoc_empty hl o ho⟩
      rw [ExU_stop _ _ _ hPE, hWo, if_neg hne, mul_one]
  unfold ExPh phaseBound
  calc ∑ o, κ.p l o * ExU (κ := κ) (PE Δ M) (M - m - 1) (Wt x θ y m) (l ++ [o])
      ≤ ∑ o, κ.p l o * (θ * (advF x o * (if o.hon ≠ 0 then y * u 0 else 1))) :=
        Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (hcont o) (κ.nonneg l o)
    _ = θ * ∑ o, κ.p l o * (advF x o * (if o.hon ≠ 0 then y * u 0 else 1)) := by
        rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun o _ => by ring
    _ ≤ θ * ((1 + B.amax * (x - 1)) * 1 +
          (y * u 0 - 1) * (if 1 ≤ y * u 0 then B.hhi + (x - 1) * B.hahi else B.hlo)) :=
        mul_le_mul_of_nonneg_left (slot_sum hB l hx (U1 := y * u 0) (U2 := 1) zero_le_one) hθ
    _ = _ := by ring

/-! ## A fixed pattern, from below -/

theorem ExU_ge_snoc {S : List Out → Prop} [DecidablePred S] {G : List Out → ℝ} (hG : ∀ h, 0 ≤ G h)
    {h : List Out} (hS : ¬ S h) (n : ℕ) (o : Out) :
    κ.p h o * ExU (κ := κ) S n G (h ++ [o]) ≤ ExU (κ := κ) S (n + 1) G h := by
  rw [ExU_go S n G hS]
  exact Finset.single_le_sum (f := fun o => κ.p h o * ExU (κ := κ) S n G (h ++ [o]))
    (fun o _ => mul_nonneg (κ.nonneg h o) (ExU_nonneg S n hG _)) (Finset.mem_univ o)

/-- The pattern: an honest slot `o1`, then `Δ` empty slots. -/
def pat (o1 : Out) (i : ℕ) : List Out := o1 :: List.replicate i Out.empty

theorem strOf_pat_first (l : List Out) (o1 : Out) (i : ℕ) :
    strOf (l ++ pat o1 i) (l.length + 1) = o1.toPair := by
  unfold strOf pat
  simp

theorem strOf_pat_after (l : List Out) (o1 : Out) (i j : ℕ) (hj1 : l.length + 1 < j) :
    (strOf (l ++ pat o1 i) j).1 = 0 ∧ (strOf (l ++ pat o1 i) j).2 = false := by
  unfold strOf pat
  have hj0 : j ≠ 0 := by omega
  simp only [hj0, ↓reduceIte]
  rw [List.getD_append_right _ _ _ _ (by omega)]
  rw [show j - 1 - l.length = (j - 2 - l.length) + 1 by omega, List.getD_cons_succ]
  rcases Nat.lt_or_ge (j - 2 - l.length) i with hi | hi
  · rw [List.getD_eq_getElem _ _ (by simpa using hi)]; simp [Out.empty, Out.toPair]
  · rw [List.getD_eq_default _ _ (by simpa using hi)]; simp [Out.empty, Out.toPair]

theorem strOf_pat_before (l : List Out) (o1 : Out) (i j : ℕ) (hj : j ≤ l.length) :
    strOf (l ++ pat o1 i) j = strOf l j := strOf_append_of_le hj

theorem pat_snoc (o1 : Out) (i : ℕ) : pat o1 i ++ [Out.empty] = pat o1 (i + 1) := by
  unfold pat; simp [List.replicate_succ']

/-- **One pattern, from below.** For `G ≥ 0`, the expectation over the next phase
is at least the probability of the pattern times `G` at its end. -/
theorem phase_lower (hB : κ.Within B) (helo : 0 ≤ B.elo) (hΔ : 0 < Δ) {l : List Out} (hlM : l.length + Δ + 1 ≤ M)
    {G : List Out → ℝ} (hG : ∀ h, 0 ≤ G h) (o1 : Out) (ho1 : o1.hon ≠ 0) :
    κ.p l o1 * B.elo ^ Δ * G (l ++ pat o1 Δ) ≤ ExPh (κ := κ) (PE Δ M) (M - l.length - 1) G l := by
  have hlen : ∀ i, (l ++ pat o1 i).length = l.length + 1 + i := fun i => by simp [pat]; omega
  -- not a phase end before the pattern finishes
  have hnot : ∀ i < Δ, ¬ PE Δ M (l ++ pat o1 i) := by
    intro i hi
    rintro (h1 | ⟨-, h2⟩)
    · rw [hlen] at h1; omega
    · have := h2 (l.length + 1) (by rw [hlen]; omega) (by rw [hlen]; omega) (by omega)
      rw [strOf_pat_first] at this
      exact ho1 (Fin.ext (by simpa [Out.toPair] using this))
  have hend : PE Δ M (l ++ pat o1 Δ) := by
    by_cases hM : (l ++ pat o1 Δ).length = M
    · exact Or.inl hM
    · refine Or.inr ⟨by rw [hlen] at hM ⊢; omega, ?_⟩
      intro j h1 h2 _
      rw [hlen] at h1 h2
      exact (strOf_pat_after l o1 Δ j (by omega)).1
  -- backward induction along the pattern
  have key : ∀ j ≤ Δ, B.elo ^ j * G (l ++ pat o1 Δ) ≤
      ExU (κ := κ) (PE Δ M) (M - l.length - 1 - (Δ - j)) G (l ++ pat o1 (Δ - j)) := by
    intro j hj
    induction j with
    | zero => simp only [pow_zero, one_mul, Nat.sub_zero]; rw [ExU_stop _ _ _ hend]
    | succ j ih =>
      have ih' := ih (by omega)
      have hfuel : M - l.length - 1 - (Δ - (j + 1)) = (M - l.length - 1 - (Δ - j)) + 1 := by omega
      rw [hfuel]
      have hs := ExU_ge_snoc (κ := κ) hG (hnot (Δ - (j + 1)) (by omega))
        (M - l.length - 1 - (Δ - j)) Out.empty
      rw [List.append_assoc, pat_snoc, show Δ - (j + 1) + 1 = Δ - j by omega] at hs
      have he := hB.elo (l ++ pat o1 (Δ - (j + 1)))
      have hU := ExU_nonneg (κ := κ) (PE Δ M) (M - l.length - 1 - (Δ - j)) hG (l ++ pat o1 (Δ - j))
      have he0 : 0 ≤ B.elo ^ j * G (l ++ pat o1 Δ) := mul_nonneg (pow_nonneg helo _) (hG _)
      calc B.elo ^ (j + 1) * G (l ++ pat o1 Δ) = B.elo * (B.elo ^ j * G (l ++ pat o1 Δ)) := by ring
        _ ≤ κ.p (l ++ pat o1 (Δ - (j + 1))) Out.empty *
            ExU (κ := κ) (PE Δ M) (M - l.length - 1 - (Δ - j)) G (l ++ pat o1 (Δ - j)) := by
            apply mul_le_mul he ih' he0 (κ.nonneg _ _)
        _ ≤ _ := hs
  have h0 := key Δ le_rfl
  simp only [Nat.sub_self, Nat.sub_zero] at h0
  unfold ExPh
  have hsingle : κ.p l o1 * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o1]) ≤
      ∑ o, κ.p l o * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o]) :=
    Finset.single_le_sum (f := fun o => κ.p l o * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o]))
      (fun o _ => mul_nonneg (κ.nonneg l o) (ExU_nonneg _ _ hG _)) (Finset.mem_univ o1)
  have hp0 : pat o1 0 = [o1] := rfl
  rw [hp0] at h0
  calc κ.p l o1 * B.elo ^ Δ * G (l ++ pat o1 Δ) = κ.p l o1 * (B.elo ^ Δ * G (l ++ pat o1 Δ)) := by ring
    _ ≤ κ.p l o1 * ExU (κ := κ) (PE Δ M) (M - l.length - 1) G (l ++ [o1]) :=
        mul_le_mul_of_nonneg_left h0 (κ.nonneg l o1)
    _ ≤ _ := hsingle

/-- The pattern is a crossing, with no adversarial slot and an honest success. -/
theorem pat_cross (l : List Out) (o1 : Out) (ho1 : o1.hon = 1) (ha : o1.adv = false) :
    Cross (strOf (l ++ pat o1 Δ)) 0 l.length (l.length + 1 + Δ) := by
  refine ⟨?_, l.length + 1, by omega, by omega, Nat.zero_le _, ?_, ?_⟩
  · unfold advCnt
    rw [Finset.card_eq_zero, Finset.filter_eq_empty_iff]
    intro i hi
    rw [Finset.mem_Ioc] at hi
    rcases Nat.lt_or_ge (l.length + 1) i with h | h
    · simp [(strOf_pat_after l o1 Δ i h).2]
    · have : i = l.length + 1 := by omega
      subst this; rw [strOf_pat_first]; simp [Out.toPair, ha]
  · rw [strOf_pat_first]; simp [Out.toPair, ho1]
  · intro i h1 h2 h3
    exact (strOf_pat_after l o1 Δ i (by omega)).1

theorem pat_advCnt (l : List Out) (o1 : Out) (ha : o1.adv = false) :
    advCnt (strOf (l ++ pat o1 Δ)) l.length (l.length + 1 + Δ) = 0 := by
  unfold advCnt
  rw [Finset.card_eq_zero, Finset.filter_eq_empty_iff]
  intro i hi
  rw [Finset.mem_Ioc] at hi
  rcases Nat.lt_or_ge (l.length + 1) i with h | h
  · simp [(strOf_pat_after l o1 Δ i h).2]
  · have : i = l.length + 1 := by omega
    subst this; rw [strOf_pat_first]; simp [Out.toPair, ha]

theorem pat_honIn (l : List Out) (o1 : Out) (ho : o1.hon ≠ 0) :
    HonIn (strOf (l ++ pat o1 Δ)) l.length (l.length + 1 + Δ) := by
  refine ⟨l.length + 1, by omega, by omega, ?_⟩
  rw [strOf_pat_first]; simp only [Out.toPair]; intro h; exact ho (Fin.ext h)

end Cryptarchia.Prob
