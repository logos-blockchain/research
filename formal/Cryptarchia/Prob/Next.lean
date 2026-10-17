module

public import Cryptarchia.Prob.Burst
import Cryptarchia.Settle.Mono
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.NNRat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.Height.NumberField
import Mathlib.NumberTheory.Height.Projectivization
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.SelbergSieve
import Mathlib.RingTheory.PiTensorProduct
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.RingTheory.WittVector.IsPoly
import Mathlib.Tactic.Echelon.Zsqrtd
import Mathlib.Tactic.NormNum.Irrational
import Mathlib.Tactic.NormNum.IsCoprime
import Mathlib.Tactic.NormNum.IsSquare
import Mathlib.Tactic.NormNum.LegendreSymbol
import Mathlib.Tactic.NormNum.ModEq
import Mathlib.Tactic.NormNum.NatFib
import Mathlib.Tactic.NormNum.NatLog
import Mathlib.Tactic.NormNum.NatSqrt
import Mathlib.Tactic.NormNum.Ordinal
import Mathlib.Tactic.NormNum.Parity
import Mathlib.Tactic.NormNum.Prime
import Mathlib.Tactic.NormNum.RealSqrt
import Mathlib.Topology.Sheaves.Init
import Std.Tactic.BVDecide.Normalize.Prop
import Mathlib.Algebra.Order.Star.Real
import Mathlib.Tactic.ENatToNat
import Mathlib.Tactic.Polynomial.Basic
import Mathlib.Tactic.ReduceModChar

/-!
# The next phase, as the sampled histories see it

Sampling over one phase from a phase end `h` reaches histories `h'` that are the
**first** phase end after `h` (`FirstPE`). At such an `h'`, the greedy phase ends of
`strOf h'` agree with those of `strOf h` up to `h`'s index `j`, and the next one is
`h'` itself, with index `j + 1` (`firstPE_gend`). So the bound process at `h'` is
one `step` of the one at `h` (`bnd_next`, `runFrom_next`).
-/

@[expose] public section

namespace Cryptarchia.Prob

section

open Finset Settle

variable {κ : Kern} {Δ M : ℕ}

/-- **Monotonicity on reached histories.** -/
theorem ExU_mono_on (S : List Out → Prop) [DecidablePred S] :
    ∀ (n : ℕ) (x : List Out) {F G : List Out → ℝ},
      (∀ t : List Out, t.length ≤ n → (∀ k < t.length, ¬ S (x ++ t.take k)) →
        (S (x ++ t) ∨ t.length = n) → F (x ++ t) ≤ G (x ++ t)) →
      ExU (κ := κ) S n F x ≤ ExU (κ := κ) S n G x
  | 0, x, F, G, h => by simpa [ExU_zero] using h [] le_rfl (by simp) (Or.inr rfl)
  | n + 1, x, F, G, h => by
    by_cases hS : S x
    · rw [ExU_stop S _ F hS, ExU_stop S _ G hS]
      simpa using h [] (by simp) (by simp) (Or.inl (by simpa using hS))
    · rw [ExU_go S n F hS, ExU_go S n G hS]
      refine Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left ?_ (κ.nonneg x o)
      apply ExU_mono_on S n (x ++ [o])
      intro t ht hk hend
      have := h (o :: t) (by simp; omega) ?_ ?_
      · simpa using this
      · intro k hk'
        cases k with
        | zero => simpa using hS
        | succ k =>
          have := hk k (by simp at hk'; omega)
          simpa [List.take_succ_cons] using this
      · rcases hend with h1 | h1
        · left; simpa using h1
        · right; simp [h1]

theorem ExPh_mono_on (S : List Out → Prop) [DecidablePred S] (n : ℕ) (x : List Out)
    {F G : List Out → ℝ}
    (h : ∀ (o : Out) (t : List Out), t.length ≤ n → (∀ k < t.length, ¬ S (x ++ [o] ++ t.take k)) →
      (S (x ++ [o] ++ t) ∨ t.length = n) → F (x ++ [o] ++ t) ≤ G (x ++ [o] ++ t)) :
    ExPh (κ := κ) S n F x ≤ ExPh (κ := κ) S n G x := by
  unfold ExPh
  exact Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left
    (ExU_mono_on S n (x ++ [o]) (h o)) (κ.nonneg x o)

theorem ExPh_add (S : List Out → Prop) [DecidablePred S] (n : ℕ) (F G : List Out → ℝ) (x : List Out) :
    ExPh (κ := κ) S n (fun y => F y + G y) x = ExPh (κ := κ) S n F x + ExPh (κ := κ) S n G x := by
  unfold ExPh
  simp only [ExU_add, mul_add, Finset.sum_add_distrib]

theorem ExPh_mul_const (S : List Out → Prop) [DecidablePred S] (n : ℕ) (a : ℝ) (F : List Out → ℝ)
    (x : List Out) : ExPh (κ := κ) S n (fun y => a * F y) x = a * ExPh (κ := κ) S n F x := by
  unfold ExPh
  simp only [ExU_mul_const, Finset.mul_sum]
  exact Finset.sum_congr rfl fun o _ => by ring

theorem ExPh_const (S : List Out → Prop) [DecidablePred S] (n : ℕ) (a : ℝ) (x : List Out) :
    ExPh (κ := κ) S n (fun _ => a) x = a := by
  unfold ExPh
  simp only [ExU_const]
  rw [← Finset.sum_mul, κ.sum_one, one_mul]

theorem ExPh_sub (S : List Out → Prop) [DecidablePred S] (n : ℕ) (F G : List Out → ℝ) (x : List Out) :
    ExPh (κ := κ) S n (fun y => F y - G y) x = ExPh (κ := κ) S n F x - ExPh (κ := κ) S n G x := by
  have h := ExPh_add (κ := κ) S n (fun y => F y - G y) G x
  simp only [sub_add_cancel] at h
  linarith

theorem ExPh_nonneg (S : List Out → Prop) [DecidablePred S] (n : ℕ) {F : List Out → ℝ}
    (hF : ∀ y, 0 ≤ F y) (x : List Out) : 0 ≤ ExPh (κ := κ) S n F x := by
  unfold ExPh
  exact Finset.sum_nonneg fun o _ => mul_nonneg (κ.nonneg x o) (ExU_nonneg S n hF _)

/-! ## The first phase end after a history -/

/-- `h'` is the first phase end after `h`. -/
structure FirstPE (Δ M : ℕ) (h h' : List Out) : Prop where
  pre : h <+: h'
  lt : h.length < h'.length
  pe : PE Δ M h'
  first : ∀ p, h.length < p → p < h'.length → ¬ PE Δ M (h'.take p)

/-- The histories reached over one phase are first phase ends. -/
theorem firstPE_of_reached {h : List Out} (hlM : h.length < M) (o : Out) (t : List Out)
    (ht : t.length ≤ M - h.length - 1)
    (hk : ∀ k < t.length, ¬ PE Δ M (h ++ [o] ++ t.take k))
    (hend : PE Δ M (h ++ [o] ++ t) ∨ t.length = M - h.length - 1) :
    FirstPE Δ M h (h ++ [o] ++ t) := by
  refine ⟨⟨[o] ++ t, by simp⟩, by simp, ?_, ?_⟩
  · rcases hend with h1 | h1
    · exact h1
    · left; simp; omega
  · intro p h1 h2
    have hp : (h ++ [o] ++ t).take p = h ++ [o] ++ t.take (p - h.length - 1) := by
      rw [List.append_assoc, List.take_append, List.take_of_length_le (by omega)]
      simp only [List.length_append, List.length_singleton, List.append_assoc]
      congr 1
      rw [show p - h.length = (p - h.length - 1) + 1 by omega]
      simp
    rw [hp]
    exact hk _ (by simp at h2; omega)

/-- **Monotonicity over one phase**: on the first phase ends after `h`. -/
theorem ExPh_mono_first {h : List Out} (hlM : h.length < M) {F G : List Out → ℝ}
    (hFG : ∀ h', FirstPE Δ M h h' → F h' ≤ G h') :
    ExPh (κ := κ) (PE Δ M) (M - h.length - 1) F h ≤ ExPh (κ := κ) (PE Δ M) (M - h.length - 1) G h :=
  ExPh_mono_on _ _ _ fun o t ht hk hend => hFG _ (firstPE_of_reached hlM o t ht hk hend)

/-- A value that no first phase end after `h` exceeds bounds the expectation. -/
theorem ExPh_le_first {h : List Out} (hlM : h.length < M) {F : List Out → ℝ} {c : ℝ}
    (hF : ∀ h', FirstPE Δ M h h' → F h' ≤ c) : ExPh (κ := κ) (PE Δ M) (M - h.length - 1) F h ≤ c :=
  (ExPh_mono_first hlM hF).trans (le_of_eq (ExPh_const _ _ _ _))

theorem start_of_pe {h : List Out} (hpe : PE Δ M h) (hlM : h.length < M) : Start Δ h := by
  rcases hpe with h1 | ⟨-, h2⟩
  · omega
  · exact Or.inr h2

theorem pe_nil (hM : 0 < M) : PE Δ M [] := by
  right; refine ⟨by simpa using hM, ?_⟩
  intro i h1 h2 h3; simp at h2; omega

/-- A phase end's index. -/
theorem gend_pidx_pe {h : List Out} (hpe : PE Δ M h) :
    gend Δ M (strOf h) (pidx Δ M (strOf h) h.length) = h.length := by
  apply gend_pidx_of_end
  rcases hpe with h1 | ⟨h1, h2⟩
  · exact Or.inr (Or.inl h1)
  · exact Or.inr (Or.inr ⟨h1, h2⟩)

theorem simOn_prefix {h h' : List Out} (hp : h <+: h') (a : ℕ) :
    SimOn (strOf h') (strOf h) a h.length := by
  obtain ⟨t, rfl⟩ := hp
  exact strOf_sim h t a

/-- **The phase structure at the next phase end.** -/
theorem firstPE_gend {h h' : List Out} (hpe : PE Δ M h) (hlM : h.length < M) (hf : FirstPE Δ M h h') :
    (∀ i ≤ pidx Δ M (strOf h) h.length, gend Δ M (strOf h') i = gend Δ M (strOf h) i) ∧
      gend Δ M (strOf h') (pidx Δ M (strOf h) h.length + 1) = h'.length ∧
      pidx Δ M (strOf h') h'.length = pidx Δ M (strOf h) h.length + 1 := by
  set j := pidx Δ M (strOf h) h.length with hj
  have hej := gend_pidx_pe hpe
  rw [← hj] at hej
  have hsim : SimOn (strOf h) (strOf h') 0 h.length := (simOn_prefix hf.pre 0).symm
  have hagree : ∀ i ≤ j, gend Δ M (strOf h') i = gend Δ M (strOf h) i := by
    intro i hi
    have hle : gend Δ M (strOf h) i ≤ h.length := by
      rw [← hej]; exact gend_strictMono.monotone hi
    exact (gend_congr hsim i hle).symm
  have hh'M : h'.length ≤ M := by
    rcases hf.pe with h1 | h1
    · omega
    · omega
  -- no quiet slot strictly between
  have hnq : ∀ p, h.length < p → p < h'.length → p < M → ¬ Quiet Δ (strOf h') p := by
    intro p h1 h2 hpM hq
    apply hf.first p h1 h2
    right
    have hlen : (h'.take p).length = p := by simp; omega
    refine ⟨by omega, ?_⟩
    rw [hlen]
    have hs : SimOn (strOf h') (strOf (h'.take p)) (p - Δ) p := by
      have := simOn_prefix (List.take_prefix p h') (p - Δ)
      rwa [hlen] at this
    exact (quiet_congr hs).1 hq
  have hnext : gend Δ M (strOf h') (j + 1) = h'.length := by
    rw [gend_succ, hagree j le_rfl, hej]
    apply le_antisymm
    · rcases hf.pe with h1 | ⟨h1, h2⟩
      · rw [h1]; exact nextE_le hlM
      · exact nextE_le_of_quiet hf.lt h1 h2
    · by_contra hlt
      push Not at hlt
      have hgt := nextE_gt (Δ := Δ) (M := M) (w := strOf h') h.length
      have hle := nextE_le (Δ := Δ) (w := strOf h') hlM
      have hM' : nextE Δ M (strOf h') h.length < M := by omega
      exact hnq _ hgt hlt hM' (nextE_quiet hM')
  refine ⟨hagree, hnext, ?_⟩
  apply le_antisymm
  · exact pidx_le_of (le_of_eq hnext.symm)
  · by_contra hlt
    push Not at hlt
    have h1 := le_gend_pidx (Δ := Δ) (M := M) (w := strOf h') h'.length
    rw [hagree _ (by omega)] at h1
    have h2 : gend Δ M (strOf h) (pidx Δ M (strOf h') h'.length) ≤ h.length := by
      rw [← hej]; exact gend_strictMono.monotone (by omega)
    have := hf.lt
    omega

/-! ## The bound process along agreeing phase ends -/

theorem bnd_congr2 {w w' : CStr} {ℓ : ℕ} {e e' : ℕ → ℕ} (hmono : ∀ k, e k ≤ e (k + 1)) :
    ∀ k, (∀ i ≤ k, e i = e' i) → SimOn w w' 0 (e k) → bnd Δ w ℓ e k = bnd Δ w' ℓ e' k
  | 0, _, _ => rfl
  | k + 1, he, h => by
    simp only [bnd]
    rw [bnd_congr2 hmono k (fun i hi => he i (by omega)) (h.mono le_rfl (hmono k)),
      step_congr (h.mono (Nat.zero_le _) le_rfl), he k (by omega), he (k + 1) le_rfl]

theorem runFrom_congr2 {w w' : CStr} {ℓ : ℕ} {e e' : ℕ → ℕ} (hmono : ∀ k, e k ≤ e (k + 1)) (k0 : ℕ)
    (b0 : ℤ × ℤ) : ∀ j, (∀ i ≤ k0 + j, e i = e' i) → SimOn w w' 0 (e (k0 + j)) →
      runFrom (Δ := Δ) (w := w) ℓ e k0 b0 j = runFrom (Δ := Δ) (w := w') ℓ e' k0 b0 j
  | 0, _, _ => rfl
  | j + 1, he, h => by
    simp only [runFrom]
    rw [runFrom_congr2 hmono k0 b0 j (fun i hi => he i (by omega))
      (h.mono le_rfl (by rw [← Nat.add_assoc]; exact hmono _)),
      step_congr (h.mono (Nat.zero_le _) (by rw [Nat.add_assoc])), he (k0 + j) (by omega),
      he (k0 + j + 1) (by omega)]

end

/-!
## The cold condition fails rarely

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

open Finset Settle

variable {B : Band} {Δ : ℕ}

/-! ## The bound process from the anchor -/

variable (Δ) (M N W : ℕ)

/-- The reach bound at phase `k0`. -/
noncomputable def rho0 (w : CStr) (k0 : ℕ) : ℤ := (bnd Δ w 0 (gend Δ M w) k0).1

/-- The bound process restarted at phase `k0` with margin = reach. -/
noncomputable def rf (w : CStr) (k0 n : ℕ) : ℤ × ℤ :=
  runFrom (Δ := Δ) (w := w) 0 (gend Δ M w) k0 (rho0 Δ M w k0, rho0 Δ M w k0) n

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

end Next

/-! ## Expectations over the next phase -/

open Classical in
/-- `θ^L` on a crossing phase. -/
noncomputable def crossG (θ : ℝ) (m : ℕ) (h : List Out) : ℝ :=
  θ ^ (h.length - m) * (if Cross (strOf h) 0 m h.length then 1 else 0)

variable {κ : Kern}

/-! ## Pointwise bounds at the next phase end -/

theorem zpow_sub_ind {c : ℝ} (hc : 0 < c) (A : ℕ) (P : Prop) [Decidable P] :
    c ^ ((A : ℤ) - (if P then 1 else 0)) = c ^ A * (if P then c⁻¹ else 1) := by
  split_ifs
  · rw [zpow_sub₀ hc.ne', zpow_natCast, zpow_one, div_eq_mul_inv]
  · simp

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

end Cryptarchia.Prob
