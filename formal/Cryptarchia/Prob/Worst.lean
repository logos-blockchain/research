import Cryptarchia.Prob.Burst

/-!
# From conditional slot laws to a kernel

The lottery string of an execution is not sampled by one fixed kernel: the next
slot's law depends on the epoch state, which depends on everything the adversary
did. This file turns per-slot conditional laws into the kernel form the bounds
use.

Suppose that, given the past, each slot's outcome has the law `qh ⊗ Bern(qa)`: an
honest part `qh` in the band's honest polytope (`HB`) and, independently, an
adversarial win with probability `qa ≤ amax` (`hcond` in `law_le`). Take an event
`S` about the first `M` slots that is closed under adding adversarial slots
(`UpClosed`). Then `S` is at most as likely as under the **worst-case kernel**
(`worstK`), which at each history plays the honest law in `HB` that maximizes the
probability of `S` from there, with the adversary winning with probability
exactly `amax`. That kernel is within the band (`worstK_within`).

The worst case is a backward recursion (`Wv`): a maximum over the compact set
`HB`, attained (`Wv_attain`). It is monotone in adversarial slots (`Wv_mono`),
which is why an adversary winning less often than `amax` only helps.
-/

namespace Cryptarchia.Prob

open MeasureTheory Finset

instance : MeasurableSpace Out := ⊤

instance : MeasurableSingletonClass Out := ⟨fun _ => trivial⟩

/-- `o'` has the same honest leaders as `o`, and an adversarial win wherever `o` has one. -/
def OutLe (o o' : Out) : Prop := o.hon = o'.hon ∧ (o.adv = true → o'.adv = true)

theorem OutLe.refl (o : Out) : OutLe o o := ⟨rfl, id⟩

theorem OutLe.trans {o o' o'' : Out} (h : OutLe o o') (h' : OutLe o' o'') : OutLe o o'' :=
  ⟨h.1.trans h'.1, fun x => h'.2 (h.2 x)⟩

/-- A set of histories closed under adding adversarial slots. -/
def UpClosed (S : Set (List Out)) : Prop := ∀ l l', List.Forall₂ OutLe l l' → l ∈ S → l' ∈ S

theorem forall₂_refl (l : List Out) : List.Forall₂ OutLe l l := by
  induction l with
  | nil => exact List.Forall₂.nil
  | cons o l ih => exact List.Forall₂.cons (OutLe.refl o) ih

theorem forall₂_trans {l l' l'' : List Out} (h : List.Forall₂ OutLe l l') (h' : List.Forall₂ OutLe l' l'') :
    List.Forall₂ OutLe l l'' := by
  induction h generalizing l'' with
  | nil => cases h'; exact List.Forall₂.nil
  | cons ho _ ih =>
    cases h' with
    | cons ho' ht' => exact List.Forall₂.cons (ho.trans ho') (ih ht')

theorem forall₂_append {l l' m m' : List Out} (h : List.Forall₂ OutLe l l') (hm : List.Forall₂ OutLe m m') :
    List.Forall₂ OutLe (l ++ m) (l' ++ m') := List.rel_append h hm

/-- Sums over outcomes. -/
theorem sum_out {β : Type*} [AddCommMonoid β] (f : Out → β) :
    ∑ o, f o = ∑ h : Fin 3, (f ⟨h, false⟩ + f ⟨h, true⟩) := by
  let e : Out ≃ Fin 3 × Bool := ⟨fun o => (o.hon, o.adv), fun p => ⟨p.1, p.2⟩, fun _ => rfl, fun _ => rfl⟩
  rw [← e.symm.sum_comp, Fintype.sum_prod_type]
  refine Finset.sum_congr rfl fun h _ => ?_
  rw [Fintype.sum_bool, add_comm]
  rfl

/-! ## The honest polytope and product laws -/

/-- **The honest polytope** of a band: laws of the honest part (no leader, one, two
or more) consistent with the band when the adversary wins with probability `amax`,
independently. -/
def HB (B : Band) : Set (Fin 3 → ℝ) :=
  {q | (∀ h, 0 ≤ q h) ∧ q 0 + q 1 + q 2 = 1 ∧ B.hlo ≤ q 1 + q 2 ∧ q 1 + q 2 ≤ B.hhi ∧
    B.slo ≤ q 1 * (1 - B.amax) ∧ B.hnlo ≤ (q 1 + q 2) * (1 - B.amax) ∧ B.elo ≤ q 0 * (1 - B.amax)}

/-- The law of a slot: honest part `q`, and independently an adversarial win with
probability `a`. -/
def prodLaw (q : Fin 3 → ℝ) (a : ℝ) (o : Out) : ℝ := q o.hon * (if o.adv then a else 1 - a)

/-- The band facts the worst-case kernel needs. -/
structure Band.Prod (B : Band) : Prop where
  a0 : 0 ≤ B.amax
  a1 : B.amax ≤ 1
  alo : B.alo ≤ B.amax
  hahi : B.hhi * B.amax ≤ B.hahi
  halo : B.halo ≤ B.hlo * B.amax

variable {B : Band}

theorem prodLaw_nonneg {q : Fin 3 → ℝ} (hq : ∀ h, 0 ≤ q h) {a : ℝ} (ha0 : 0 ≤ a) (ha1 : a ≤ 1) (o : Out) :
    0 ≤ prodLaw q a o := by
  unfold prodLaw; split_ifs <;> exact mul_nonneg (hq _) (by linarith)

theorem sum_prodLaw (q : Fin 3 → ℝ) (a : ℝ) (W : Out → ℝ) :
    ∑ o, prodLaw q a o * W o = ∑ h : Fin 3, q h * ((1 - a) * W ⟨h, false⟩ + a * W ⟨h, true⟩) := by
  rw [sum_out]
  refine Finset.sum_congr rfl fun h _ => ?_
  simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]
  ring

theorem sum_prodLaw_one {q : Fin 3 → ℝ} (hq : q 0 + q 1 + q 2 = 1) (a : ℝ) : ∑ o, prodLaw q a o = 1 := by
  have := sum_prodLaw q a (fun _ => 1)
  simp only [mul_one] at this
  rw [this, Fin.sum_univ_three]
  linear_combination hq

theorem HB_isCompact : IsCompact (HB B) := by
  apply Metric.isCompact_of_isClosed_isBounded
  · have e : HB B = (⋂ h, {q : Fin 3 → ℝ | 0 ≤ q h}) ∩ ({q | q 0 + q 1 + q 2 = 1} ∩
        ({q | B.hlo ≤ q 1 + q 2} ∩ ({q | q 1 + q 2 ≤ B.hhi} ∩ ({q | B.slo ≤ q 1 * (1 - B.amax)} ∩
          ({q | B.hnlo ≤ (q 1 + q 2) * (1 - B.amax)} ∩ {q | B.elo ≤ q 0 * (1 - B.amax)}))))) := by
      ext q; simp [HB, Set.mem_iInter]
    rw [e]
    exact (isClosed_iInter fun h => isClosed_le continuous_const (continuous_apply h)).inter
      ((isClosed_eq (by fun_prop) continuous_const).inter
      ((isClosed_le continuous_const (by fun_prop)).inter
      ((isClosed_le (by fun_prop) continuous_const).inter
      ((isClosed_le continuous_const (by fun_prop)).inter
      ((isClosed_le continuous_const (by fun_prop)).inter
      (isClosed_le continuous_const (by fun_prop)))))))
  · refine (Metric.isBounded_closedBall (x := (0 : Fin 3 → ℝ)) (r := 1)).subset ?_
    intro q hq
    obtain ⟨h0, hs, -⟩ := hq
    rw [Metric.mem_closedBall, dist_zero_right, pi_norm_le_iff_of_nonneg zero_le_one]
    intro h
    rw [Real.norm_eq_abs, abs_le]
    have := h0 0; have := h0 1; have := h0 2
    fin_cases h <;> simp <;> constructor <;> linarith

/-! ## The worst case -/

/-- The admissible slot laws of a family of bands: an adversarial win probability
`amax` of a member, with an honest part in that member's polytope. -/
def Adm (Bs : List Band) : Set (ℝ × (Fin 3 → ℝ)) := {p | ∃ B ∈ Bs, p.1 = B.amax ∧ p.2 ∈ HB B}

variable {Bs : List Band}

theorem Adm_isCompact : IsCompact (Adm Bs) := by
  have e : Adm Bs = ⋃ B ∈ {B | B ∈ Bs}, ({B.amax} : Set ℝ) ×ˢ HB B := by
    ext p; simp only [Adm, Set.mem_setOf_eq, Set.mem_iUnion, Set.mem_prod, Set.mem_singleton_iff, exists_prop]
  rw [e]
  exact (List.finite_toSet Bs).isCompact_biUnion fun B _ => isCompact_singleton.prod HB_isCompact

theorem Adm_amax (hB : ∀ B ∈ Bs, B.Prod) {p : ℝ × (Fin 3 → ℝ)} (hp : p ∈ Adm Bs) :
    0 ≤ p.1 ∧ p.1 ≤ 1 ∧ ∀ h, 0 ≤ p.2 h := by
  obtain ⟨B, hBm, h1, h2⟩ := hp
  rw [h1]; exact ⟨(hB B hBm).a0, (hB B hBm).a1, h2.1⟩

/-- The value of a history to the worst case, with `n` slots to go. -/
noncomputable def Wv (Bs : List Band) (F : List Out → ℝ) : ℕ → List Out → ℝ
  | 0, l => F l
  | n + 1, l => sSup ((fun p : ℝ × (Fin 3 → ℝ) => ∑ o, prodLaw p.2 p.1 o * Wv Bs F n (l ++ [o])) '' Adm Bs)

theorem Wv_attain {F : List Out → ℝ} (hne : (Adm Bs).Nonempty) (n : ℕ) (l : List Out) :
    ∃ p ∈ Adm Bs, Wv Bs F (n + 1) l = ∑ o, prodLaw p.2 p.1 o * Wv Bs F n (l ++ [o]) ∧
      ∀ p' ∈ Adm Bs, ∑ o, prodLaw p'.2 p'.1 o * Wv Bs F n (l ++ [o]) ≤ Wv Bs F (n + 1) l := by
  set φ : ℝ × (Fin 3 → ℝ) → ℝ := fun p => ∑ o, prodLaw p.2 p.1 o * Wv Bs F n (l ++ [o]) with hφ
  have hc : Continuous φ := by
    refine continuous_finsetSum _ fun o _ => ?_
    unfold prodLaw
    refine (((continuous_apply o.hon).comp continuous_snd).mul ?_).mul continuous_const
    split_ifs
    · exact continuous_fst
    · exact continuous_const.sub continuous_fst
  obtain ⟨p, hp, hmax⟩ := Adm_isCompact.exists_isMaxOn hne hc.continuousOn
  have hg : IsGreatest (φ '' Adm Bs) (φ p) :=
    ⟨⟨p, hp, rfl⟩, by rintro _ ⟨p', hp', rfl⟩; exact hmax hp'⟩
  have hW : Wv Bs F (n + 1) l = φ p := hg.csSup_eq
  exact ⟨p, hp, hW, fun p' hp' => hW ▸ hmax hp'⟩

theorem Wv_nonneg (hB : ∀ B ∈ Bs, B.Prod) {F : List Out → ℝ} (hF : ∀ l, 0 ≤ F l)
    (hne : (Adm Bs).Nonempty) : ∀ n l, 0 ≤ Wv Bs F n l
  | 0, l => hF l
  | n + 1, l => by
    obtain ⟨p, hp, hW, -⟩ := Wv_attain (F := F) hne n l
    obtain ⟨a0, a1, hq⟩ := Adm_amax hB hp
    rw [hW]
    exact Finset.sum_nonneg fun o _ =>
      mul_nonneg (prodLaw_nonneg hq a0 a1 o) (Wv_nonneg hB hF hne n _)

/-- **The worst case is monotone in adversarial slots.** -/
theorem Wv_mono (hB : ∀ B ∈ Bs, B.Prod) {F : List Out → ℝ}
    (hF : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l')
    (hne : (Adm Bs).Nonempty) : ∀ n l l', List.Forall₂ OutLe l l' → Wv Bs F n l ≤ Wv Bs F n l'
  | 0, l, l', h => hF l l' h
  | n + 1, l, l', h => by
    obtain ⟨p, hp, hW, -⟩ := Wv_attain (F := F) hne n l
    obtain ⟨-, -, -, hmax'⟩ := Wv_attain (F := F) hne n l'
    obtain ⟨a0, a1, hq⟩ := Adm_amax hB hp
    rw [hW]
    refine le_trans (Finset.sum_le_sum fun o _ => ?_) (hmax' p hp)
    exact mul_le_mul_of_nonneg_left
      (Wv_mono hB hF hne n _ _ (forall₂_append h (List.Forall₂.cons (OutLe.refl o) List.Forall₂.nil)))
      (prodLaw_nonneg hq a0 a1 o)

/-- **One slot of the true law** is at most the worst case: the honest part is in
the polytope of a member, and the adversary wins with probability at most its `amax`. -/
theorem step_le (hB : ∀ B ∈ Bs, B.Prod) {F : List Out → ℝ}
    (hF : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l')
    (hne : (Adm Bs).Nonempty) {B : Band} (hBm : B ∈ Bs) {q : Fin 3 → ℝ} (hq : q ∈ HB B) {a : ℝ}
    (ha : a ≤ B.amax) (n : ℕ) (l : List Out) :
    ∑ o, prodLaw q a o * Wv Bs F n (l ++ [o]) ≤ Wv Bs F (n + 1) l := by
  obtain ⟨-, -, -, hmax⟩ := Wv_attain (F := F) hne n l
  refine le_trans ?_ (hmax (B.amax, q) ⟨B, hBm, rfl, hq⟩)
  rw [sum_prodLaw, sum_prodLaw]
  refine Finset.sum_le_sum fun h _ => mul_le_mul_of_nonneg_left ?_ (hq.1 h)
  have hm := Wv_mono hB hF hne n (l ++ [⟨h, false⟩]) (l ++ [⟨h, true⟩])
    (forall₂_append (forall₂_refl l) (List.Forall₂.cons ⟨rfl, fun x => absurd x (by simp)⟩ List.Forall₂.nil))
  simp only
  nlinarith

/-! ## The worst-case kernel -/

/-- The worst-case slot law at a history, for the horizon `M`. -/
noncomputable def worstQ (Bs : List Band) (F : List Out → ℝ) (M : ℕ) (hne : (Adm Bs).Nonempty)
    (l : List Out) : ℝ × (Fin 3 → ℝ) :=
  Classical.choose (Wv_attain (Bs := Bs) (F := F) hne (M - l.length - 1) l)

theorem worstQ_mem {F : List Out → ℝ} {M : ℕ} (hne : (Adm Bs).Nonempty) (l : List Out) :
    worstQ Bs F M hne l ∈ Adm Bs :=
  (Classical.choose_spec (Wv_attain (Bs := Bs) (F := F) hne (M - l.length - 1) l)).1

theorem worstQ_val {F : List Out → ℝ} {M : ℕ} (hne : (Adm Bs).Nonempty) (l : List Out) :
    Wv Bs F (M - l.length - 1 + 1) l =
      ∑ o, prodLaw (worstQ Bs F M hne l).2 (worstQ Bs F M hne l).1 o * Wv Bs F (M - l.length - 1) (l ++ [o]) :=
  (Classical.choose_spec (Wv_attain (Bs := Bs) (F := F) hne (M - l.length - 1) l)).2.1

/-- **The worst-case kernel.** -/
noncomputable def worstK (hB : ∀ B ∈ Bs, B.Prod) (F : List Out → ℝ) (M : ℕ) (hne : (Adm Bs).Nonempty) :
    Kern where
  p l o := prodLaw (worstQ Bs F M hne l).2 (worstQ Bs F M hne l).1 o
  nonneg l o := by
    obtain ⟨a0, a1, hq⟩ := Adm_amax hB (worstQ_mem hne l)
    exact prodLaw_nonneg hq a0 a1 o
  sum_one l := by
    obtain ⟨B, -, -, hq⟩ := worstQ_mem (F := F) (M := M) hne l
    exact sum_prodLaw_one hq.2.1 _

theorem worstK_Ex (hB : ∀ B ∈ Bs, B.Prod) {F : List Out → ℝ} {M : ℕ} (hne : (Adm Bs).Nonempty) :
    ∀ n (l : List Out), l.length + n = M → Ex (worstK hB F M hne) n F l = Wv Bs F n l
  | 0, l, _ => rfl
  | n + 1, l, h => by
    rw [Ex_succ]
    have e : M - l.length - 1 = n := by omega
    have hv := worstQ_val (F := F) (M := M) hne l
    rw [e] at hv
    rw [hv]
    refine Finset.sum_congr rfl fun o _ => ?_
    rw [worstK_Ex hB hne n (l ++ [o]) (by simp; omega)]
    rfl

theorem pr_prodLaw (q : Fin 3 → ℝ) (a : ℝ) (P : Out → Prop) [DecidablePred P] :
    ∑ o, (if P o then prodLaw q a o else 0) =
      ∑ h : Fin 3, ((if P ⟨h, false⟩ then q h * (1 - a) else 0) + (if P ⟨h, true⟩ then q h * a else 0)) := by
  rw [sum_out]
  refine Finset.sum_congr rfl fun h _ => ?_
  simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]

/-- A kernel whose next slot after `l` has the law `qh ⊗ Bern(amax)` with `qh` in the
band's polytope is within the band there. -/
theorem bandAt_prodLaw {κ : Kern} {l : List Out} {B : Band} (hB : B.Prod) {q : Fin 3 → ℝ} (mem : q ∈ HB B)
    (pk : ∀ o, κ.p l o = prodLaw q B.amax o) : κ.BandAt B l := by
  have ha0 := hB.a0
  have prh : κ.pr l (fun o => o.hon ≠ 0) = q 1 + q 2 := by
    unfold Kern.pr; simp only [pk]; rw [pr_prodLaw, Fin.sum_univ_three]; simp; ring
  have pra : κ.pr l (fun o => o.adv = true) = B.amax := by
    unfold Kern.pr; simp only [pk]; rw [pr_prodLaw, Fin.sum_univ_three]; simp
    have := mem.2.1
    linear_combination B.amax * this
  have prha : κ.pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) = (q 1 + q 2) * B.amax := by
    unfold Kern.pr; simp only [pk]; rw [pr_prodLaw, Fin.sum_univ_three]; simp; ring
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · rw [prh]; exact mem.2.2.2.1
  · rw [prh]; exact mem.2.2.1
  · rw [pra]
  · rw [prha]; exact le_trans (mul_le_mul_of_nonneg_right mem.2.2.2.1 ha0) hB.hahi
  · rw [pk]; simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]; exact mem.2.2.2.2.1
  · rw [pk, pk]; simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]
    have := mem.2.2.2.2.2.1; linarith
  · rw [pk]; simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]; exact mem.2.2.2.2.2.2
  · rw [pra]; exact hB.alo
  · rw [prha]; exact le_trans hB.halo (mul_le_mul_of_nonneg_right mem.2.2.1 ha0)

/-- **The worst-case kernel is within the family.** -/
theorem worstK_fam (hB : ∀ B ∈ Bs, B.Prod) {F : List Out → ℝ} {M : ℕ} (hne : (Adm Bs).Nonempty) :
    (worstK hB F M hne).Fam Bs := by
  intro l
  obtain ⟨B, hBm, h1, mem⟩ := worstQ_mem (F := F) (M := M) hne l
  refine ⟨B, hBm, ?_⟩
  have hBp := hB B hBm
  have ha0 := hBp.a0
  set q := (worstQ Bs F M hne l).2 with hq
  have pk : ∀ o, (worstK hB F M hne).p l o = prodLaw q B.amax o := fun o => by
    show prodLaw _ _ o = _; rw [h1]
  have prh : (worstK hB F M hne).pr l (fun o => o.hon ≠ 0) = q 1 + q 2 := by
    unfold Kern.pr; simp only [pk]; rw [pr_prodLaw, Fin.sum_univ_three]; simp; ring
  have pra : (worstK hB F M hne).pr l (fun o => o.adv = true) = B.amax := by
    unfold Kern.pr; simp only [pk]; rw [pr_prodLaw, Fin.sum_univ_three]; simp
    have := mem.2.1
    linear_combination B.amax * this
  have prha : (worstK hB F M hne).pr l (fun o => o.hon ≠ 0 ∧ o.adv = true) = (q 1 + q 2) * B.amax := by
    unfold Kern.pr; simp only [pk]; rw [pr_prodLaw, Fin.sum_univ_three]; simp; ring
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · rw [prh]; exact mem.2.2.2.1
  · rw [prh]; exact mem.2.2.1
  · rw [pra]
  · rw [prha]; exact le_trans (mul_le_mul_of_nonneg_right mem.2.2.2.1 ha0) hBp.hahi
  · rw [pk]; simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]; exact mem.2.2.2.2.1
  · rw [pk, pk]; simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]
    have := mem.2.2.2.2.2.1; linarith
  · rw [pk]; simp only [prodLaw, Bool.false_eq_true, ↓reduceIte]; exact mem.2.2.2.2.2.2
  · rw [pra]; exact hBp.alo
  · rw [prha]; exact le_trans hBp.halo (mul_le_mul_of_nonneg_right mem.2.2.1 ha0)

/-! ## Conditional laws to the worst-case kernel -/

open scoped ENNReal

theorem nonempty_of_prob {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ] :
    Nonempty Ω := by
  by_contra h
  rw [not_nonempty_iff] at h
  have := measure_univ (μ := μ)
  rw [Set.univ_eq_empty_iff.mpr h, measure_empty] at this
  exact zero_ne_one this

/-- **From conditional slot laws to a kernel.** Let `X k` be the outcome of slot
`k + 1`, and `m n` what is known before slot `n + 1` (it determines the earlier
outcomes). Suppose that given `m n`, slot `n + 1` has the law
`prodLaw (qh n) (qa n)`: an honest part in `HB` and, independently, an adversarial win
with probability at most `amax` (`hcond`: for every `m n`-measurable weight `f`, the
weighted probability of each outcome is the weighted conditional law). Then every
event about the first `M` slots that is closed under adding adversarial slots is at
most as likely as under some kernel within the band. -/
theorem law_le {Ω : Type*} [mΩ : MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ]
    {Bs : List Band} (hB : ∀ B ∈ Bs, B.Prod) {M : ℕ} (hM : 0 < M) (X : ℕ → Ω → Out) (hXm : ∀ j, Measurable (X j))
    (m : ℕ → MeasurableSpace Ω) (hm : ∀ n, m n ≤ mΩ) (hX : ∀ n j, j < n → Measurable[m n] (X j))
    (qh : ℕ → Ω → Fin 3 → ℝ) (qa : ℕ → Ω → ℝ)
    (hQ : ∀ n < M, ∀ ω, ∃ B ∈ Bs, qh n ω ∈ HB B ∧ 0 ≤ qa n ω ∧ qa n ω ≤ B.amax)
    (hQm : ∀ n < M, ∀ o, Measurable[m n] fun ω => ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o))
    (hcond : ∀ n < M, ∀ f : Ω → ℝ≥0∞, Measurable[m n] f → ∀ o,
      ∫⁻ ω, f ω * (if X n ω = o then 1 else 0) ∂μ =
        ∫⁻ ω, f ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ)
    {S : Set (List Out)} (hS : UpClosed S) :
    ∃ κ : Kern, κ.Fam Bs ∧
      μ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} ≤ ENNReal.ofReal (Ex κ M (S.indicator 1) []) := by
  classical
  obtain ⟨ω0⟩ := nonempty_of_prob μ
  have hne : (Adm Bs).Nonempty := by
    obtain ⟨B, hBm, hq, -, -⟩ := hQ 0 hM ω0
    exact ⟨(B.amax, qh 0 ω0), B, hBm, rfl, hq⟩
  set F : List Out → ℝ := S.indicator 1 with hFdef
  have hF0 : ∀ l, 0 ≤ F l := fun l => Set.indicator_nonneg (fun _ _ => zero_le_one) l
  have hFm : ∀ l l', List.Forall₂ OutLe l l' → F l ≤ F l' := by
    intro l l' h
    by_cases hl : l ∈ S
    · rw [hFdef, Set.indicator_of_mem hl, Set.indicator_of_mem (hS l l' h hl)]; exact le_rfl
    · rw [hFdef, Set.indicator_of_notMem hl]; exact hF0 l'
  refine ⟨worstK hB F M hne, worstK_fam hB hne, ?_⟩
  -- the value of the history so far, to the worst case
  set I : ℕ → ℝ≥0∞ := fun n =>
    ∫⁻ ω, ENNReal.ofReal (Wv Bs F (M - n) (List.ofFn fun k : Fin n => X k ω)) ∂μ with hI
  have hvec : ∀ n, Measurable[m n] (fun ω (k : Fin n) => X k ω) :=
    fun n => by letI := m n; exact measurable_pi_iff.mpr fun k : Fin n => hX n k.val k.2
  have hstep : ∀ n < M, I (n + 1) ≤ I n := by
    intro n hn
    obtain ⟨k, hk⟩ : ∃ k, M - n = k + 1 := ⟨M - (n + 1), by omega⟩
    have hk' : M - (n + 1) = k := by omega
    set f : Out → Ω → ℝ≥0∞ := fun o ω =>
      ENNReal.ofReal (Wv Bs F k ((List.ofFn fun j : Fin n => X j ω) ++ [o])) with hf
    have hfm : ∀ o, Measurable[m n] (f o) := fun o =>
      (measurable_of_countable (fun v : Fin n → Out => ENNReal.ofReal (Wv Bs F k (List.ofFn v ++ [o])))).comp
        (hvec n)
    have hind : ∀ o, Measurable fun ω => (if X n ω = o then (1 : ℝ≥0∞) else 0) := fun o =>
      (measurable_of_countable (fun x : Out => if x = o then (1 : ℝ≥0∞) else 0)).comp (hXm n)
    have hsplit : ∀ ω, ENNReal.ofReal (Wv Bs F (M - (n + 1)) (List.ofFn fun j : Fin (n + 1) => X j ω)) =
        ∑ o, f o ω * (if X n ω = o then 1 else 0) := by
      intro ω
      rw [hk', List.ofFn_succ_last]
      simp only [mul_ite, mul_one, mul_zero, Finset.sum_ite_eq, Finset.mem_univ, ↓reduceIte, hf]
      rfl
    calc I (n + 1) = ∫⁻ ω, ∑ o, f o ω * (if X n ω = o then 1 else 0) ∂μ := by
          simp only [hI]; exact lintegral_congr fun ω => hsplit ω
      _ = ∑ o, ∫⁻ ω, f o ω * (if X n ω = o then 1 else 0) ∂μ :=
          lintegral_finsetSum _ fun o _ => ((hfm o).mono (hm n) le_rfl).mul (hind o)
      _ = ∑ o, ∫⁻ ω, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ :=
          Finset.sum_congr rfl fun o _ => hcond n hn (f o) (hfm o) o
      _ = ∫⁻ ω, ∑ o, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o) ∂μ :=
          (lintegral_finsetSum _ fun o _ =>
            (((hfm o).mul (hQm n hn o))).mono (hm n) le_rfl).symm
      _ ≤ I n := by
          simp only [hI]
          refine lintegral_mono fun ω => ?_
          obtain ⟨B, hBm, hq, ha0, ha⟩ := hQ n hn ω
          have ha1 : qa n ω ≤ 1 := le_trans ha (hB B hBm).a1
          have hnn : ∀ o, 0 ≤ prodLaw (qh n ω) (qa n ω) o * Wv Bs F k ((List.ofFn fun j : Fin n => X j ω) ++ [o]) :=
            fun o => mul_nonneg (prodLaw_nonneg hq.1 ha0 ha1 o) (Wv_nonneg hB hF0 hne k _)
          calc ∑ o, f o ω * ENNReal.ofReal (prodLaw (qh n ω) (qa n ω) o)
              = ENNReal.ofReal (∑ o, prodLaw (qh n ω) (qa n ω) o *
                  Wv Bs F k ((List.ofFn fun j : Fin n => X j ω) ++ [o])) := by
                rw [ENNReal.ofReal_sum_of_nonneg fun o _ => hnn o]
                refine Finset.sum_congr rfl fun o _ => ?_
                rw [hf, mul_comm, ENNReal.ofReal_mul (prodLaw_nonneg hq.1 ha0 ha1 o)]
            _ ≤ ENNReal.ofReal (Wv Bs F (M - n) (List.ofFn fun j : Fin n => X j ω)) := by
                rw [hk]
                exact ENNReal.ofReal_le_ofReal (step_le hB hFm hne hBm hq ha k _)
  have hchain : ∀ n ≤ M, I n ≤ I 0 := by
    intro n hn
    induction n with
    | zero => exact le_rfl
    | succ n ih => exact (hstep n (by omega)).trans (ih (by omega))
  have h0 : I 0 = ENNReal.ofReal (Ex (worstK hB F M hne) M F []) := by
    simp only [hI, Nat.sub_zero, List.ofFn_zero, lintegral_const, measure_univ, mul_one]
    rw [worstK_Ex hB hne M [] (by simp)]
  have hMeq : I M = μ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} := by
    have hv : Measurable (fun ω (k : Fin M) => X k ω) := measurable_pi_iff.mpr fun k : Fin M => hXm k.val
    have hms : MeasurableSet {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} :=
      hv (Set.toFinite {v : Fin M → Out | List.ofFn v ∈ S}).measurableSet
    rw [← lintegral_indicator_one hms]
    simp only [hI, Nat.sub_self]
    refine lintegral_congr fun ω => ?_
    simp only [Wv, hFdef, Set.indicator, Set.mem_setOf_eq, Pi.one_apply]
    split_ifs <;> simp
  rw [← hMeq, ← h0]
  exact hchain M le_rfl

end Cryptarchia.Prob
