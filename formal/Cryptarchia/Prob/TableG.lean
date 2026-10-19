module

public import Cryptarchia.Prob.Table
public import Cryptarchia.Prob.Fail3E

/-!
# Epochs along a phase

A grouped table potential (`TableGCert.lean`) uses one table per group of band members, chosen by the
epoch's member, and grows with the epoch's age (`ageE`: slots since the history's epoch began) so that
a phase crossing into the next epoch, where the member and so the table change, only lowers it.

Along an extension `l ++ t` of a history: without an epoch boundary in its slots (`NoSw EL t.length
l.length`) the member is unchanged (`mem_ext`) and the age grows by `t.length` (`age_ext`); with one, the
age at the end is less than `t.length` (`age_after`). A history within `G` slots before a boundary is at
least `EL - G` slots into its epoch (`age_ge_of_sw`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open Settle

/-- **The epoch's age**: slots since the history's epoch began (its member changes when `l.length + 1`
is a multiple of `EL`). -/
def ageE (EL : ℕ) (h : List Out) : ℕ := (h.length + 1) % EL

theorem ageE_lt {EL : ℕ} (hEL : 0 < EL) (h : List Out) : ageE EL h < EL := Nat.mod_lt _ hEL

theorem NoSw.mono {EL G G' t : ℕ} (h : NoSw EL G t) (hG : G' ≤ G) : NoSw EL G' t :=
  fun j h1 h2 => h j h1 (by omega)

/-- **No boundary: the member is unchanged.** -/
theorem mem_ext {EL K : ℕ} {mem : List Out → Fin K} (hmem : ∀ h o, (h.length + 2) % EL ≠ 0 → mem (h ++ [o]) = mem h)
    {l : List Out} (t : List Out) (hnb : NoSw EL t.length l.length) : mem (l ++ t) = mem l := by
  induction t using List.reverseRecOn with
  | nil => simp
  | append_singleton t o ih =>
    simp only [List.length_append, List.length_singleton] at hnb
    rw [← List.append_assoc, hmem _ _ (by
      simp only [List.length_append]
      exact hnb (l.length + t.length + 1) (by omega) (by omega))]
    exact ih (hnb.mono (by omega))

/-- **No boundary: the age grows by the slots.** -/
theorem age_ext {EL : ℕ} (hEL : 1 < EL) {l : List Out} (t : List Out) (hnb : NoSw EL t.length l.length) :
    ageE EL (l ++ t) = ageE EL l + t.length := by
  unfold ageE
  simp only [List.length_append]
  have key : ∀ i, i ≤ t.length → (l.length + i + 1) % EL = (l.length + 1) % EL + i := by
    intro i hi
    induction i with
    | zero => simp
    | succ i ih =>
      have h1 := ih (by omega)
      have hne := hnb (l.length + i + 1) (by omega) (by omega)
      have hlt := Nat.mod_lt (l.length + i + 1) (by omega : 0 < EL)
      have hstep : (l.length + i + 1 + 1) % EL = ((l.length + i + 1) % EL + 1) % EL := by
        rw [Nat.add_mod, Nat.mod_eq_of_lt (show 1 < EL from hEL)]
      rw [hstep] at hne
      have hlt2 : (l.length + i + 1) % EL + 1 < EL := by
        by_contra hc
        exact hne (by rw [show (l.length + i + 1) % EL + 1 = EL by omega, Nat.mod_self])
      rw [show l.length + (i + 1) + 1 = l.length + i + 1 + 1 by omega, hstep, Nat.mod_eq_of_lt hlt2, h1]
      omega
  have := key t.length le_rfl
  rw [show l.length + t.length + 1 = l.length + t.length + 1 from rfl, this]

/-- **Past a boundary: the age is less than the slots.** -/
theorem age_after {EL : ℕ} {l : List Out} (t : List Out) (hb : ¬ NoSw EL t.length l.length) :
    ageE EL (l ++ t) < t.length := by
  unfold NoSw at hb
  push Not at hb
  obtain ⟨j, hj1, hj2, hj⟩ := hb
  unfold ageE
  simp only [List.length_append]
  obtain ⟨q, hq⟩ := Nat.dvd_of_mod_eq_zero hj
  have : l.length + t.length + 1 = EL * q + (l.length + t.length - j) := by omega
  rw [this, Nat.mul_add_mod]
  exact lt_of_le_of_lt (Nat.mod_le _ _) (by omega)

/-- **Before a boundary: the age is at least `EL - G`.** -/
theorem age_ge_of_sw {EL G : ℕ} (hGEL : G < EL) {l : List Out} (hb : ¬ NoSw EL G l.length) :
    EL - G ≤ ageE EL l := by
  unfold NoSw at hb
  push Not at hb
  obtain ⟨j, hj1, hj2, hj⟩ := hb
  unfold ageE
  obtain ⟨q, hq⟩ := Nat.dvd_of_mod_eq_zero hj
  have hq1 : 1 ≤ q := by
    rcases q with _ | q
    · omega
    · omega
  have : l.length + 1 = EL * (q - 1) + (EL - (j - l.length)) := by
    have : EL * q = EL * (q - 1) + EL := by
      rw [show q = q - 1 + 1 from (Nat.sub_add_cancel hq1).symm, Nat.mul_add, Nat.mul_one, Nat.add_sub_cancel]
    omega
  rw [this, Nat.mul_add_mod, Nat.mod_eq_of_lt (by omega)]
  omega

/-! ## Tables by group -/

/-- **Tables by group**, sharing their box, extension factors and automaton factor. -/
structure TabFam (n : ℕ) where
  R : ℕ
  M : ℕ
  cw : ℝ
  zc : ℝ
  x : ℝ
  w : Fin n → ℕ → ℝ
  c : Fin n → ℕ → ℕ → ℝ

namespace TabFam

variable {n : ℕ} (F : TabFam n)

/-- Group `g`'s table. -/
def T (g : Fin n) : TabPot := ⟨F.R, F.M, F.cw, F.zc, F.x, F.w g, F.c g⟩

theorem fac_eq (g g' : Fin n) (st : ℤ × ℤ) : (F.T g).fac st = (F.T g').fac st := rfl

theorem rep_eq (g g' : Fin n) (st : ℤ × ℤ) : (F.T g).rep st = (F.T g').rep st := rfl

theorem isRep_eq (g g' : Fin n) (s : ℤ × ℤ) : (F.T g).IsRep s = (F.T g').IsRep s := rfl

theorem isRep_rep' (T : TabPot) {st : ℤ × ℤ} (h0 : 0 ≤ st.1) : T.IsRep (T.rep st) := by
  unfold TabPot.IsRep TabPot.rep
  have hm1 : min st.1 (T.R + 1) ≤ T.R + 1 := min_le_right _ _
  have hm0 : 0 ≤ min st.1 (T.R + 1) := le_min h0 (by omega)
  split_ifs with hw
  · exact ⟨hm0, hm1, Or.inl rfl⟩
  · exact ⟨hm0, hm1, Or.inr ⟨le_max_right _ _, max_lt (by omega) (by omega)⟩⟩

variable {F}

/-- **The ratio between groups' tables**, at every state, from the representatives. -/
theorem V_ratio (hS : ∀ g, (F.T g).Shape) {Γ : ℝ}
    (hΓ : ∀ g g' s, (F.T g).IsRep s → (F.T g').V s ≤ Γ * (F.T g).V s) (g g' : Fin n) {st : ℤ × ℤ}
    (h0 : 0 ≤ st.1) (hm : st.2 ≤ st.1) : (F.T g').V st ≤ Γ * (F.T g).V st := by
  rw [TabPot.V_rep (hS g') h0 hm, TabPot.V_rep (hS g) h0 hm, fac_eq F g' g, rep_eq F g' g]
  calc (F.T g).fac st * (F.T g').V ((F.T g).rep st) ≤ (F.T g).fac st * (Γ * (F.T g).V ((F.T g).rep st)) :=
        mul_le_mul_of_nonneg_left (hΓ g g' _ (isRep_rep' _ h0)) ((F.T g).fac_nonneg (hS g) st)
    _ = Γ * ((F.T g).fac st * (F.T g).V ((F.T g).rep st)) := by ring

theorem bI_nonneg (b : Bool) : 0 ≤ TabPot.bI b := by unfold TabPot.bI; split <;> norm_num

/-- **The ratio between groups' terminal tables.** -/
theorem gT_ratio (hS : ∀ g, (F.T g).Shape) {Γ : ℝ} (hΓ0 : 0 ≤ Γ)
    (hΓ : ∀ g g' s, (F.T g).IsRep s → (F.T g').V s ≤ Γ * (F.T g).V s) (g g' : Fin n) {s : ℤ × ℤ} (hs : Inv s)
    (a : Fin 3) (b u : Bool) : (F.T g').gT s a b u ≤ Γ * (F.T g).gT s a b u := by
  have hx : 0 < F.x := TabPot.x_pos (hS g)
  have hst : ∀ A : ℕ, 0 ≤ (stepO s A (TabPot.bI b) false).1 ∧
      (stepO s A (TabPot.bI b) false).2 ≤ (stepO s A (TabPot.bI b) false).1 := fun A =>
    ⟨le_trans (by positivity) (le_max_right _ _), TabPot.stepO_inv hs (by positivity) (bI_nonneg b) (by simp)⟩
  unfold TabPot.gT
  split_ifs with h0 h1
  · exact V_ratio hS hΓ g g' (hst 0).1 (hst 0).2
  · rw [mul_div_assoc']
    exact div_le_div_of_nonneg_right (V_ratio hS hΓ g g' (hst 1).1 (hst 1).2) hx.le
  · unfold TabPot.gmax
    refine Finset.sup'_le _ _ fun A hA => ?_
    rw [Finset.mem_Icc] at hA
    calc (F.T g').V (stepO s A (TabPot.bI b) false) / (F.T g').x ^ A
        ≤ Γ * (F.T g).V (stepO s A (TabPot.bI b) false) / (F.T g).x ^ A :=
          div_le_div_of_nonneg_right (V_ratio hS hΓ g g' (hst A).1 (hst A).2) (pow_nonneg hx.le _)
      _ = Γ * ((F.T g).V (stepO s A (TabPot.bI b) false) / (F.T g).x ^ A) := by ring
      _ ≤ Γ * (F.T g).gmax s (TabPot.bI b) := mul_le_mul_of_nonneg_left
          ((F.T g).le_gmax hA.1 (by simpa [TabPot.AX, T] using hA.2)) hΓ0

theorem Wt2_theta (x θ : ℝ) (g : Fin 3 → Bool → Bool → ℝ) (m : ℕ) (h : List Out) :
    θ ^ (h.length - m) * Wt2 x 1 g m h = Wt2 x θ g m h := by
  unfold Wt2; rw [one_pow, one_mul]; ring

theorem crossG_theta (θ : ℝ) (m : ℕ) (h : List Out) : θ ^ (h.length - m) * crossG 1 m h = crossG θ m h := by
  unfold crossG; rw [one_pow, one_mul]

theorem crossG_nonneg {θ : ℝ} (hθ : 0 ≤ θ) (m : ℕ) (h : List Out) : 0 ≤ crossG θ m h := by
  unfold crossG; split_ifs <;> simp [pow_nonneg hθ]

theorem Wt2_nonneg {x θ : ℝ} (hx : 0 ≤ x) (hθ : 0 ≤ θ) {g : Fin 3 → Bool → Bool → ℝ} (hg : ∀ a b u, 0 ≤ g a b u)
    (m : ℕ) (h : List Out) : 0 ≤ Wt2 x θ g m h := by
  unfold Wt2; exact mul_nonneg (by positivity) (hg _ _ _)

theorem Wt2_scale {x θ Γ : ℝ} (hx : 0 ≤ x) (hθ : 0 ≤ θ) {g g' : Fin 3 → Bool → Bool → ℝ}
    (hg : ∀ a b u, g a b u ≤ Γ * g' a b u) (m : ℕ) (h : List Out) : Wt2 x θ g m h ≤ Γ * Wt2 x θ g' m h := by
  unfold Wt2
  calc θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length * g _ _ _
      ≤ θ ^ (h.length - m) * x ^ advCnt (strOf h) m h.length * (Γ * g' _ _ _) :=
        mul_le_mul_of_nonneg_left (hg _ _ _) (by positivity)
    _ = _ := by ring

theorem gT_nonneg {T : TabPot} (hS : T.Shape) {s : ℤ × ℤ} (a : Fin 3) (b u : Bool) : 0 ≤ T.gT s a b u := by
  have hx := TabPot.x_pos hS
  unfold TabPot.gT
  split_ifs
  · exact (TabPot.V_pos hS _).le
  · exact div_nonneg (TabPot.V_pos hS _).le hx.le
  · exact le_trans (div_nonneg (TabPot.V_pos hS _).le (pow_nonneg hx.le _))
      (T.le_gmax (A := 2) le_rfl (by unfold TabPot.AX; omega))

/-! ## The grouped potential -/

variable {B : Band} {Δ : ℕ} {κ : Kern} {M G : ℕ}

variable (F) in
/-- **The grouped potential**: the table of the epoch's member's group, grown by `γ` per slot of the
epoch's age. -/
noncomputable def Vg (EL : ℕ) {K : ℕ} (mem : List Out → Fin K) (grp : Fin K → Fin n) (γ : ℝ) (h : List Out)
    (st : ℤ × ℤ) : ℝ :=
  γ ^ ageE EL h * (F.T (grp (mem h))).V st

variable (F) in
/-- The bound after a phase, by the table of the end's group. -/
noncomputable def postg (EL : ℕ) {K : ℕ} (mem : List Out → Fin K) (grp : Fin K → Fin n) (γ : ℝ) (st : ℤ × ℤ)
    (m : ℕ) (h : List Out) : ℝ :=
  γ ^ ageE EL h * (F.T (grp (mem h))).post st m h

section Pot

variable (hS : ∀ g, (F.T g).Shape) {EL K : ℕ} {mem : List Out → Fin K}
  (hmem : ∀ l o, (l.length + 2) % EL ≠ 0 → mem (l ++ [o]) = mem l) (grp : Fin K → Fin n) {γ Γ : ℝ}
  (hγ : 1 ≤ γ) (hGEL : 2 * G + 1 < EL)

include hS hmem hγ hGEL

omit hS hγ in
/-- **In an epoch**: after a phase whose next `G` slots have no boundary, the grouped potential is the
start's table grown by `γ` per slot. -/
theorem postg_in {st : ℤ × ℤ} {h : List Out} (hnb : NoSw EL G h.length) (o : Out) (t : List Out) :
    truncG h.length G (postg F EL mem grp γ st h.length) (h ++ [o] ++ t) =
      γ ^ ageE EL h * ((F.T (grp (mem h))).fac st * truncG h.length G (fun y =>
        Wt2 F.x γ ((F.T (grp (mem h))).gT ((F.T (grp (mem h))).rep st)) h.length y -
        (F.T (grp (mem h))).crT ((F.T (grp (mem h))).rep st) * crossG γ h.length y) (h ++ [o] ++ t)) := by
  unfold truncG
  split_ifs with hl
  · have ht : ([o] ++ t).length ≤ G := by simp only [List.length_append] at hl ⊢; omega
    have hnb' := hnb.mono ht
    have hy : h ++ [o] ++ t = h ++ ([o] ++ t) := List.append_assoc _ _ _
    have hm : mem (h ++ [o] ++ t) = mem h := by rw [hy]; exact mem_ext hmem _ hnb'
    have ha : ageE EL (h ++ [o] ++ t) = ageE EL h + ([o] ++ t).length := by
      rw [hy]; exact age_ext (by omega) _ hnb'
    have hlen : (h ++ [o] ++ t).length - h.length = ([o] ++ t).length := by simp
    unfold postg TabPot.post TabPot.post0
    beta_reduce
    rw [hm, ha, pow_add, ← Wt2_theta F.x γ, ← crossG_theta γ, hlen]
    simp only [T]; ring
  · ring

omit hS hγ in
/-- `postg_in` at one history: no boundary within its slots after the start. -/
theorem postg_in_at {st : ℤ × ℤ} {h : List Out} (o : Out) (t : List Out) (hnb : NoSw EL ([o] ++ t).length h.length) :
    truncG h.length G (postg F EL mem grp γ st h.length) (h ++ [o] ++ t) =
      γ ^ ageE EL h * ((F.T (grp (mem h))).fac st * truncG h.length G (fun y =>
        Wt2 F.x γ ((F.T (grp (mem h))).gT ((F.T (grp (mem h))).rep st)) h.length y -
        (F.T (grp (mem h))).crT ((F.T (grp (mem h))).rep st) * crossG γ h.length y) (h ++ [o] ++ t)) := by
  unfold truncG
  split_ifs with hl
  · have hy : h ++ [o] ++ t = h ++ ([o] ++ t) := List.append_assoc _ _ _
    have hm : mem (h ++ [o] ++ t) = mem h := by rw [hy]; exact mem_ext hmem _ hnb
    have ha : ageE EL (h ++ [o] ++ t) = ageE EL h + ([o] ++ t).length := by
      rw [hy]; exact age_ext (by omega) _ hnb
    have hlen : (h ++ [o] ++ t).length - h.length = ([o] ++ t).length := by simp
    unfold postg TabPot.post TabPot.post0
    beta_reduce
    rw [hm, ha, pow_add, ← Wt2_theta F.x γ, ← crossG_theta γ, hlen]
    simp only [T]; ring
  · ring

/-- **Across a boundary**: the grouped potential after any phase is at most the start's table, grown by
`γ` per slot, without the crossing's credit. -/
theorem postg_le {st : ℤ × ℤ} (hst : Inv st) {h : List Out} (hΓ0 : 0 ≤ Γ) (hγΓ : Γ ≤ γ ^ (EL - 2 * G))
    (hratio : ∀ g g' s, (F.T g).IsRep s → (F.T g').V s ≤ Γ * (F.T g).V s)
    (hcr : ∀ g s, (F.T g).IsRep s → 0 ≤ (F.T g).crT s) (o : Out) (t : List Out) :
    truncG h.length G (postg F EL mem grp γ st h.length) (h ++ [o] ++ t) ≤
      γ ^ ageE EL h * ((F.T (grp (mem h))).fac st *
        truncG h.length G (Wt2 F.x γ ((F.T (grp (mem h))).gT ((F.T (grp (mem h))).rep st)) h.length) (h ++ [o] ++ t)) := by
  set g := grp (mem h)
  set s := (F.T g).rep st
  have hx := TabPot.x_pos (hS g)
  have hγ0 : 0 ≤ γ := by linarith
  have hs : (F.T g).IsRep s := (F.T g).isRep_rep hst
  have hsI : Inv s := by
    obtain ⟨h0, h1, h2⟩ := hs
    refine ⟨h0, ?_, ?_⟩ <;> rcases h2 with h2 | h2 <;> [exact Or.inl h2; exact Or.inr h2.2; omega; omega]
  have hfac := (F.T g).fac_nonneg (hS g) st
  have hW : ∀ θ, 0 ≤ θ → ∀ g', 0 ≤ Wt2 F.x θ ((F.T g').gT s) h.length (h ++ [o] ++ t) := fun θ hθ g' =>
    Wt2_nonneg hx.le hθ (fun a b u => gT_nonneg (hS g') a b u) _ _
  have hθ1 : Wt2 F.x 1 ((F.T g).gT s) h.length (h ++ [o] ++ t) ≤ Wt2 F.x γ ((F.T g).gT s) h.length (h ++ [o] ++ t) := by
    rw [← Wt2_theta F.x γ]
    exact le_mul_of_one_le_left (hW 1 zero_le_one g) (one_le_pow₀ hγ)
  unfold truncG
  split_ifs with hl
  swap
  · simp
  have ht : ([o] ++ t).length ≤ G := by simp only [List.length_append] at hl ⊢; omega
  have hy : h ++ [o] ++ t = h ++ ([o] ++ t) := List.append_assoc _ _ _
  by_cases hb : NoSw EL ([o] ++ t).length h.length
  · -- no boundary: the start's table, less a nonnegative credit
    have hm : mem (h ++ [o] ++ t) = mem h := by rw [hy]; exact mem_ext hmem _ hb
    have ha : ageE EL (h ++ [o] ++ t) = ageE EL h + ([o] ++ t).length := by rw [hy]; exact age_ext (by omega) _ hb
    have hlen : (h ++ [o] ++ t).length - h.length = ([o] ++ t).length := by simp
    unfold postg TabPot.post TabPot.post0
    rw [hm, ha, pow_add]
    have hc := mul_nonneg (hcr g s hs) (crossG_nonneg zero_le_one h.length (h ++ [o] ++ t))
    have hW1 := hW 1 zero_le_one g
    calc γ ^ ageE EL h * γ ^ ([o] ++ t).length * ((F.T g).fac st * (Wt2 (F.T g).x 1 ((F.T g).gT s) h.length (h ++ [o] ++ t) -
          (F.T g).crT s * crossG 1 h.length (h ++ [o] ++ t)))
        ≤ γ ^ ageE EL h * γ ^ ([o] ++ t).length * ((F.T g).fac st * Wt2 (F.T g).x 1 ((F.T g).gT s) h.length (h ++ [o] ++ t)) := by
          gcongr; linarith
      _ = γ ^ ageE EL h * ((F.T g).fac st * Wt2 F.x γ ((F.T g).gT s) h.length (h ++ [o] ++ t)) := by
          rw [← Wt2_theta F.x γ, hlen]; simp only [T]; ring
  · -- past a boundary: the end's table, within `Γ`, and an age below `G`
    have hsw : ¬ NoSw EL G h.length := fun h' => hb (h'.mono ht)
    have hage := age_ge_of_sw (by omega) hsw
    have hage' : ageE EL (h ++ [o] ++ t) ≤ G := by
      rw [hy]; have := age_after _ hb; omega
    set g' := grp (mem (h ++ [o] ++ t))
    unfold postg TabPot.post TabPot.post0
    rw [fac_eq F g' g, rep_eq F g' g]
    have hc := mul_nonneg (hcr g' s (by rw [isRep_eq F g' g]; exact hs)) (crossG_nonneg zero_le_one h.length (h ++ [o] ++ t))
    have hr : Wt2 F.x 1 ((F.T g').gT s) h.length (h ++ [o] ++ t) ≤ Γ * Wt2 F.x 1 ((F.T g).gT s) h.length (h ++ [o] ++ t) :=
      Wt2_scale hx.le zero_le_one (gT_ratio hS hΓ0 hratio g g' hsI) _ _
    have hpow : γ ^ ageE EL (h ++ [o] ++ t) * Γ ≤ γ ^ ageE EL h := by
      calc γ ^ ageE EL (h ++ [o] ++ t) * Γ ≤ γ ^ G * γ ^ (EL - 2 * G) :=
            mul_le_mul (pow_le_pow_right₀ hγ hage') hγΓ hΓ0 (by positivity)
        _ = γ ^ (EL - G) := by rw [← pow_add]; congr 1; omega
        _ ≤ γ ^ ageE EL h := pow_le_pow_right₀ hγ hage
    calc γ ^ ageE EL (h ++ [o] ++ t) * ((F.T g).fac st * (Wt2 (F.T g').x 1 ((F.T g').gT s) h.length (h ++ [o] ++ t) -
          (F.T g').crT s * crossG 1 h.length (h ++ [o] ++ t)))
        ≤ γ ^ ageE EL (h ++ [o] ++ t) * ((F.T g).fac st * (Γ * Wt2 F.x 1 ((F.T g).gT s) h.length (h ++ [o] ++ t))) := by
          gcongr; simp only [T] at hc hr ⊢; linarith
      _ = (γ ^ ageE EL (h ++ [o] ++ t) * Γ) * ((F.T g).fac st * Wt2 F.x 1 ((F.T g).gT s) h.length (h ++ [o] ++ t)) := by
          ring
      _ ≤ γ ^ ageE EL h * ((F.T g).fac st * Wt2 F.x γ ((F.T g).gT s) h.length (h ++ [o] ++ t)) :=
          mul_le_mul hpow (mul_le_mul_of_nonneg_left hθ1 hfac) (mul_nonneg hfac (hW 1 zero_le_one g)) (by positivity)



end Pot

/-- **The grouped potential as a failed-check potential**, given the representatives' checks: each
group's bound (the automaton with `γ` per slot, less the crossing's credit) over a phase with no boundary
within `G1` slots at most `lpi` times its value, and its bound over any phase (without the credit) at
most `lp` times it; the tables within a factor `Γ` of each other, which the growth over an epoch covers
(`Γ ≤ γ ^ (EL - 2G)`). A phase reaching a boundary more than `G1 ≥ Δ + 2` slots on is no crossing
(`crossG_long`), so past the boundary the credit is not needed. The potential starts at most
`γ ^ (EL - 1)` above the reach potential. -/
noncomputable def toFailPotG (hS : ∀ g, (F.T g).Shape) (P : Cert2 B Δ) (hT : ∀ g, (F.T g).Ties P) {EL K : ℕ}
    {mem : List Out → Fin K} (hmem : ∀ l o, (l.length + 2) % EL ≠ 0 → mem (l ++ [o]) = mem l) (grp : Fin K → Fin n)
    {γ Γ : ℝ} (hγ : 1 ≤ γ) (hGEL : 2 * G + 1 < EL) (hΓ0 : 0 ≤ Γ) (hγΓ : Γ ≤ γ ^ (EL - 2 * G))
    (hratio : ∀ g g' s, (F.T g).IsRep s → (F.T g').V s ≤ Γ * (F.T g).V s)
    (hcr : ∀ g s, (F.T g).IsRep s → 0 ≤ (F.T g).crT s) {lp lpi : ℝ} (hlpi : 0 < lpi) (hle : lpi ≤ lp)
    {G1 : ℕ} (hG1 : Δ + 2 ≤ G1)
    (hex : ∀ g s, (F.T g).IsRep s → ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M → grp (mem h) = g →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (Wt2 F.x γ ((F.T g).gT s) h.length)) h ≤
        lp * (F.T g).V s)
    (hexIn : ∀ g s, (F.T g).IsRep s → ∀ h, PE Δ M h → h.length + Δ + 1 ≤ M → NoSw EL G1 h.length → grp (mem h) = g →
      ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (fun y =>
        Wt2 F.x γ ((F.T g).gT s) h.length y - (F.T g).crT s * crossG γ h.length y)) h ≤ lpi * (F.T g).V s) :
    FailPot κ M G P (fun t => ¬ NoSw EL G1 t) where
  V := Vg F EL mem grp γ
  post := postg F EL mem grp γ
  lp := lp
  lpi := lpi
  cs := γ ^ (EL - 1)
  hlpi := hlpi
  hle := hle
  hcs := by positivity
  nonneg h st := mul_nonneg (by positivity) ((F.T _).V_pos (hS _) st).le
  warm h ρ hρ := by
    unfold Vg
    have hEL : 0 < EL := by omega
    exact mul_le_mul (pow_le_pow_right₀ hγ (by have := ageE_lt hEL h; omega)) ((F.T _).V_warm_le (hS _) (hT _) ρ hρ)
      ((F.T _).V_pos (hS _) _).le (by positivity)
  fail h st hst A hA := by
    unfold Vg
    have hf := (F.T (grp (mem h))).one_le_V_z (hS _) (hT _) st A hA
    have hz : 0 ≤ P.z ^ A := pow_nonneg (by linarith [P.hz]) _
    calc (1 : ℝ) ≤ (F.T (grp (mem h))).V st * P.z ^ A := hf
      _ ≤ γ ^ ageE EL h * (F.T (grp (mem h))).V st * P.z ^ A := by
          rw [mul_assoc]; exact le_mul_of_one_le_left (mul_nonneg ((F.T _).V_pos (hS _) st).le hz) (one_le_pow₀ hγ)
  post_le st hst m h _ := mul_le_mul_of_nonneg_left ((F.T _).post_le (hS _) hst m h) (by positivity)
  ex st hst h hpe hlM := by
    set g := grp (mem h)
    have hfac := (F.T g).fac_nonneg (hS g) st
    have hrep := (F.T g).isRep_rep hst
    have hle1 : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (postg F EL mem grp γ st h.length)) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun y => γ ^ ageE EL h * ((F.T g).fac st *
          truncG h.length G (Wt2 F.x γ ((F.T g).gT ((F.T g).rep st)) h.length) y)) h :=
      ExPh_mono_on _ _ _ fun o t _ _ _ =>
        postg_le hS hmem grp hγ hGEL hst hΓ0 hγΓ hratio hcr o t
    refine hle1.trans ?_
    rw [ExPh_mul_const, ExPh_mul_const, Vg, (F.T g).V_rep (hS g) hst.1 hst.2.2]
    calc γ ^ ageE EL h * ((F.T g).fac st * ExPh (κ := κ) (PE Δ M) (M - h.length - 1)
          (truncG h.length G (Wt2 F.x γ ((F.T g).gT ((F.T g).rep st)) h.length)) h)
        ≤ γ ^ ageE EL h * ((F.T g).fac st * (lp * (F.T g).V ((F.T g).rep st))) := by
          gcongr; exact hex g _ hrep h hpe hlM rfl
      _ = _ := by ring
  exIn st hst h hpe hlM hsw := by
    have hnb : NoSw EL G1 h.length := not_not.1 hsw
    set g := grp (mem h)
    have hfac := (F.T g).fac_nonneg (hS g) st
    have hrep := (F.T g).isRep_rep hst
    have heq : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (truncG h.length G (postg F EL mem grp γ st h.length)) h ≤
        ExPh (κ := κ) (PE Δ M) (M - h.length - 1) (fun y => γ ^ ageE EL h * ((F.T g).fac st *
          truncG h.length G (fun y => Wt2 F.x γ ((F.T g).gT ((F.T g).rep st)) h.length y -
            (F.T g).crT ((F.T g).rep st) * crossG γ h.length y) y)) h :=
      ExPh_mono_on _ _ _ fun o t ht hpre _ => by
        by_cases hb : NoSw EL ([o] ++ t).length h.length
        · exact le_of_eq (postg_in_at hmem grp hGEL o t hb)
        · -- past a boundary the phase has more than `G1` slots: no crossing, no credit needed
          have hlong : G1 < ([o] ++ t).length := by
            by_contra hc; push Not at hc; exact hb (hnb.mono hc)
          have hc0 : crossG γ h.length (h ++ [o] ++ t) = 0 :=
            crossG_long (start_of_pe hpe (by omega)) (by simp; omega) hpre (by simp at hlong ⊢; omega)
          refine (postg_le hS hmem grp hγ hGEL hst hΓ0 hγΓ hratio hcr o t).trans (le_of_eq ?_)
          unfold truncG
          split_ifs
          · beta_reduce; rw [hc0, mul_zero, sub_zero]
          · rfl
    refine heq.trans ?_
    rw [ExPh_mul_const, ExPh_mul_const, Vg, (F.T g).V_rep (hS g) hst.1 hst.2.2]
    calc γ ^ ageE EL h * ((F.T g).fac st * ExPh (κ := κ) (PE Δ M) (M - h.length - 1)
          (truncG h.length G (fun y => Wt2 F.x γ ((F.T g).gT ((F.T g).rep st)) h.length y -
            (F.T g).crT ((F.T g).rep st) * crossG γ h.length y)) h)
        ≤ γ ^ ageE EL h * ((F.T g).fac st * (lpi * (F.T g).V ((F.T g).rep st))) := by
          gcongr; exact hexIn g _ hrep h hpe hlM hnb rfl
      _ = _ := by ring

end TabFam

end Cryptarchia.Prob
