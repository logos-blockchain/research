module

public import Cryptarchia.Prob.Tail
public import Cryptarchia.Prob.Phases
public import Cryptarchia.Proof.FinalE
public import Cryptarchia.Prob.Worst
import Cryptarchia.Proof.Consist
public import Mathlib.MeasureTheory.Measure.MeasureSpaceDef
import Mathlib.Data.Nat.Choose.Multinomial

/-!
# Lottery strings as outcome lists, and the good event cut at a horizon

The lottery string of an execution (`lotStr`), cut to its first `M` slots and with
honest leader counts capped at two, is a list of outcomes (`slots`). A finality
violation is `Unsafe`.

The greedy phase ends `gend Δ M` cap the last phase at `M`; strings that agree up to the
cap have the same ends (`gend_congr_all`). Below a smaller cap `Ms` the ends agree with
those for any larger cap `Mb` (`gend_agree`), and past it the smaller cap's end is `Ms`,
at most the larger cap's. So the lottery's good event (`GoodCap`) with the larger cap
implies the one with the smaller cap (`good_trunc`), and with the smaller cap the event
is determined by the first `Ms` slots (`good_congr_cap`). An outcome list dominating the
lottery string's first `Ms` slots with the good event therefore gives a string
dominating the lottery string with it (`good_dom`), and a robust failure of the good
event (`RBad`) at a horizon decides its failure at any later horizon (`lift_bad`).

A split of the canonical prefixes is such a robust failure (`split_up`): if epoch
`e + 1`'s canonical prefix does not extend epoch `e`'s, the good event fails up to
`N_e = min (fix (e + 1)) N`, cut at `N_e + 1`, which is determined by epoch `e`'s and
earlier slots.
-/

@[expose] public section

namespace Cryptarchia.Prob

open Finset Settle MeasureTheory

/-- **The first `M` slots of a characteristic string.** -/
def slots (w : CStr) (M : ℕ) : List Out := (List.range M).map fun i => enc (w (i + 1))

theorem slots_length (w : CStr) (M : ℕ) : (slots w M).length = M := by simp [slots]

theorem slots_take (w : CStr) {m n : ℕ} (h : m ≤ n) : (slots w n).take m = slots w m := by
  unfold slots
  rw [← List.map_take, List.take_range, min_eq_left h]

theorem slots_get (w : CStr) (M k : ℕ) (hk : k < (slots w M).length) :
    (slots w M)[k] = enc (w (k + 1)) := by
  simp [slots]

theorem enc_hon_zero (p : ℕ × Bool) : (enc p).hon.val = 0 ↔ p.1 = 0 := by
  unfold enc; split_ifs <;> simp_all

theorem enc_hon_one (p : ℕ × Bool) : (enc p).hon.val = 1 ↔ p.1 = 1 := by
  unfold enc; split_ifs <;> simp_all

variable {Δ M : ℕ}

/-- Strings that agree up to the horizon have the same phase ends. -/
theorem gend_congr_all {w w' : CStr} (h : SimOn w w' 0 M) : ∀ k, gend Δ M w k = gend Δ M w' k := by
  intro k
  induction k with
  | zero => rfl
  | succ k ih =>
    by_cases hk : gend Δ M w (k + 1) ≤ M
    · exact gend_congr (h.mono le_rfl le_rfl) (k + 1) hk
    · rw [gend_succ, gend_succ, ← ih]
      by_cases hm : gend Δ M w k < M
      · have := nextE_le (Δ := Δ) (w := w) hm
        rw [gend_succ] at hk; omega
      · push Not at hm
        rw [nextE_of_ge hm, nextE_of_ge hm]

/-- The lottery string of an execution. -/
noncomputable abbrev lotStr (E : Env) (es : List Event) : CStr := lotStrS E (σE E es) (lateAt E es)

/-- The assumptions do not involve the oracle. -/
theorem _root_.Cryptarchia.Assm.withO {E : Env} (h : Assm E) (O : Oracle) : Assm (E.withO O) :=
  ⟨h.ord, h.crash, h.exec, h.nodup, h.sane, h.stake⟩

/-- The good event does not involve the oracle. -/
theorem goodLS_withO {E : Env} {O : Oracle} {w : CStr} {N Lw : ℕ} {e : ℕ → ℕ} (h : GoodLS E w N Lw e) :
    GoodLS (E.withO O) w N Lw e :=
  ⟨h.e0, h.mono, h.quiet, h.unb, h.cold, h.window⟩

section

variable {w : CStr}

theorem nextE_agree {Ms Mb m : ℕ} (hm : m < Ms) (hMs : Ms ≤ Mb)
    (h : nextE Δ Ms w m < Ms ∨ nextE Δ Mb w m < Ms) : nextE Δ Ms w m = nextE Δ Mb w m := by
  classical
  unfold nextE at h ⊢
  by_cases hs : ∃ j, m < j ∧ j < Ms ∧ Quiet Δ w j
  · have hb : ∃ j, m < j ∧ j < Mb ∧ Quiet Δ w j :=
      ⟨Nat.find hs, (Nat.find_spec hs).1, lt_of_lt_of_le (Nat.find_spec hs).2.1 hMs, (Nat.find_spec hs).2.2⟩
    rw [dif_pos hs, dif_pos hb]
    have h1 : Nat.find hb ≤ Nat.find hs :=
      Nat.find_min' hb ⟨(Nat.find_spec hs).1, lt_of_lt_of_le (Nat.find_spec hs).2.1 hMs, (Nat.find_spec hs).2.2⟩
    have h2 : Nat.find hs ≤ Nat.find hb :=
      Nat.find_min' hs ⟨(Nat.find_spec hb).1, lt_of_le_of_lt h1 (Nat.find_spec hs).2.1, (Nat.find_spec hb).2.2⟩
    exact le_antisymm h2 h1
  · exfalso
    rw [dif_neg hs] at h
    by_cases hb : ∃ j, m < j ∧ j < Mb ∧ Quiet Δ w j
    · rw [dif_pos hb] at h
      rcases h with h | h
      · have := le_max_left Ms (m + 1); omega
      · exact hs ⟨Nat.find hb, (Nat.find_spec hb).1, h, (Nat.find_spec hb).2.2⟩
    · rw [dif_neg hb] at h
      rcases h with h | h
      · have := le_max_left Ms (m + 1); omega
      · have := le_max_left Mb (m + 1); omega

/-- **The phase ends agree below the smaller cap.** -/
theorem gend_agree {Ms Mb : ℕ} (hMs : Ms ≤ Mb) :
    ∀ k, (gend Δ Ms w k < Ms ∨ gend Δ Mb w k < Ms) → ∀ j ≤ k, gend Δ Ms w j = gend Δ Mb w j
  | 0, _, j, hj => by rw [Nat.le_zero.1 hj]; rfl
  | k + 1, h, j, hj => by
    have hs := gend_lt_succ (Δ := Δ) (M := Ms) (w := w) k
    have hb := gend_lt_succ (Δ := Δ) (M := Mb) (w := w) k
    have ih := gend_agree hMs k (by omega)
    have hk := ih k le_rfl
    rcases Nat.lt_or_ge j (k + 1) with hj' | hj'
    · exact ih j (by omega)
    · have : j = k + 1 := by omega
      subst this
      rw [gend_succ, gend_succ, hk]
      refine nextE_agree (by omega) hMs ?_
      rw [gend_succ, gend_succ, hk] at h
      exact h

/-- Past the smaller cap, its phase end is the cap, at most the larger cap's. -/
theorem gend_cap {Ms Mb : ℕ} (hMs : Ms ≤ Mb) {k : ℕ} (hk : gend Δ Ms w k < Ms)
    (h : Ms ≤ gend Δ Ms w (k + 1)) : gend Δ Ms w (k + 1) = Ms ∧ Ms ≤ gend Δ Mb w (k + 1) := by
  have hag := gend_agree (w := w) (Δ := Δ) hMs k (Or.inl hk) k le_rfl
  have h1 : gend Δ Ms w (k + 1) ≤ Ms := by rw [gend_succ]; exact nextE_le hk
  refine ⟨le_antisymm h1 h, ?_⟩
  by_contra hlt; push Not at hlt
  have := gend_agree (w := w) (Δ := Δ) hMs (k + 1) (Or.inr hlt) (k + 1) le_rfl
  omega

variable (E : Env)

/-- **The lottery's good event** up to `N`, with the phases capped at `M`. -/
abbrev GoodCap (N M Lw r G : ℕ) (w : CStr) : Prop :=
  GoodLS E w N Lw (gend E.Δ M w) ∧ GrowthS E w (gend E.Δ M w) N r G

/-- **The good event with the larger cap implies the one with the smaller cap**, for a
horizon below the smaller cap whose growth witnesses lie below it too. -/
theorem good_trunc {N Lw r G Ms Mb : ℕ} (hNs : N < Ms) (hMs : Ms ≤ Mb)
    (hgr : ∀ ep, 1 ≤ ep → E.c.fix ep ≤ N → E.c.cut ep + G < Ms)
    (hg : GoodCap E N Mb Lw r G w) : GoodCap E N Ms Lw r G w := by
  obtain ⟨⟨h0, -, hq, -, hcold, hwin⟩, hgr'⟩ := hg
  have hag : ∀ k, (gend E.Δ Ms w k < Ms ∨ gend E.Δ Mb w k < Ms) → ∀ j ≤ k, gend E.Δ Ms w j = gend E.Δ Mb w j :=
    gend_agree hMs
  refine ⟨⟨rfl, gend_mono, ?_, gend_unb, ?_, hwin⟩, ?_⟩
  · intro k hk
    rw [hag k (Or.inl (by omega)) k le_rfl]
    exact hq k (by rw [← hag k (Or.inl (by omega)) k le_rfl]; exact hk)
  · intro t k h1 h2 h3 h4
    have hk : gend E.Δ Ms w k < Ms := by omega
    have hagk := hag k (Or.inl hk)
    have hb : bnd E.Δ w (t - Lw) (gend E.Δ Ms w) k = bnd E.Δ w (t - Lw) (gend E.Δ Mb w) k :=
      bnd_congr2 (w' := w) gend_mono k hagk (fun _ _ _ => ⟨Iff.rfl, Iff.rfl, rfl⟩)
    rw [hb, hagk k le_rfl]
    by_cases hk1 : gend E.Δ Ms w (k + 1) < Ms
    · rw [hag (k + 1) (Or.inl hk1) (k + 1) le_rfl]
      exact hcold t k h1 h2 (by rw [← hagk k le_rfl]; exact h3) (by rw [← hag (k + 1) (Or.inl hk1) (k + 1) le_rfl]; exact h4)
    · push Not at hk1
      obtain ⟨he, hle⟩ := gend_cap hMs hk hk1
      have := hcold t k h1 h2 (by rw [← hagk k le_rfl]; exact h3) (by omega)
      have hadv : (advCnt w (gend E.Δ Mb w k) (gend E.Δ Ms w (k + 1)) : ℤ) ≤
          advCnt w (gend E.Δ Mb w k) (gend E.Δ Mb w (k + 1)) := by
        exact_mod_cast advCnt_mono_right (by omega)
      linarith
  · intro ep hep hfix
    obtain ⟨j, j1, j2, j3, j4⟩ := hgr' ep hep hfix
    have hj : gend E.Δ Mb w j < Ms := lt_of_le_of_lt j2 (hgr ep hep hfix)
    have hagj := hag j (Or.inr hj)
    refine ⟨j, by rw [hagj j le_rfl]; exact j1, by rw [hagj j le_rfl]; exact j2, ?_, j4⟩
    rw [bnd_congr2 (w' := w) gend_mono j hagj (fun _ _ _ => ⟨Iff.rfl, Iff.rfl, rfl⟩)]
    exact j3

/-- **The good event sees the string only up to the cap**, given `N < M` and growth
witnesses below `M`. -/
theorem good_congr_cap {w w' : CStr} {M : ℕ} (h : SimOn w w' 0 M)
    {N Lw r G : ℕ} (hNM : N < M) (hgr : ∀ ep, 1 ≤ ep → E.c.fix ep ≤ N → E.c.cut ep + G < M)
    (hg : GoodCap E N M Lw r G w) : GoodCap E N M Lw r G w' := by
  have he : gend E.Δ M w = gend E.Δ M w' := funext (gend_congr_all h)
  unfold GoodCap
  rw [← he]
  obtain ⟨⟨h0, hmono, hq, hunb, hcold, hwin⟩, hgr'⟩ := hg
  refine ⟨⟨h0, hmono, fun k hk => (quiet_congr (h.mono (Nat.zero_le _) (by omega))).1 (hq k hk), hunb, ?_, ?_⟩, ?_⟩
  · intro t k h1 h2 h3 h4
    have hk1 : gend E.Δ M w (k + 1) ≤ M := by
      rw [gend_succ]; exact nextE_le (by omega)
    rw [← bnd_congr gend_mono k (h.mono le_rfl (by have := gend_mono (Δ := E.Δ) (M := M) (w := w) k; omega)),
      ← advCnt_congr (h.mono (Nat.zero_le _) hk1)]
    exact hcold t k h1 h2 h3 h4
  · intro t ht
    rw [← occCnt_congr (h.mono (Nat.zero_le _) (by omega))]
    exact hwin t ht
  · intro ep hep hfix
    obtain ⟨j, h1, h2, h3, h4⟩ := hgr' ep hep hfix
    have hcg := hgr ep hep hfix
    refine ⟨j, h1, h2, ?_, ?_⟩
    · rw [← bnd_congr gend_mono j (h.mono le_rfl (by omega))]
      exact h3
    · rw [← hD_congr (h.mono (Nat.zero_le _) (by unfold Config.fix at hfix ⊢; omega))]
      exact h4

/-- **A dominating outcome list with the good event gives a dominating string with it.**
If `l'` dominates the first `M` slots of `lot` and has the good event up to `N < M`
(growth witnesses below `M`), so does a string with `lot`'s honest leaders and at least
its adversarial slots. -/
theorem good_dom {lot : CStr} {N M Lw r G : ℕ} (hNM : N < M)
    (hgr : ∀ ep, 1 ≤ ep → E.c.fix ep ≤ N → E.c.cut ep + G < M) {l' : List Out}
    (hl : List.Forall₂ OutLe (slots lot M) l') (hg : GoodCap E N M Lw r G (strOf l')) :
    ∃ w, AdvLeW N lot w ∧ GoodCap E N M Lw r G w := by
  obtain ⟨hlen, hget⟩ := List.forall₂_iff_get.1 hl
  rw [slots_length] at hlen
  -- the outcome at slot `i` of `l'` dominates the lottery string's
  have hdom : ∀ i, 1 ≤ i → i ≤ M → OutLe (enc (lot i)) (l'.getD (i - 1) Out.empty) := by
    intro i h1 h2
    have hk : i - 1 < l'.length := by omega
    have := hget (i - 1) (by rw [slots_length]; omega) hk
    rw [List.getD_eq_getElem _ _ hk]
    simp only [List.get_eq_getElem, slots_get, show i - 1 + 1 = i by omega] at this
    exact this
  have hstr : ∀ i, 1 ≤ i → strOf l' i = (l'.getD (i - 1) Out.empty).toPair := by
    intro i hi; unfold strOf; rw [if_neg (by omega)]
  refine ⟨fun i => if 1 ≤ i ∧ i ≤ M then ((lot i).1, (strOf l' i).2) else lot i,
    ⟨fun i _ _ => by dsimp only; split_ifs <;> rfl, fun i hi => ?_⟩, good_congr_cap E (fun i h1 h2 => ?_) hNM hgr hg⟩
  · dsimp only
    split_ifs with h
    · rw [hstr i h.1]
      exact (hdom i h.1 h.2).2 (by simpa [enc] using hi)
    · exact hi
  · simp only [if_pos (show 1 ≤ i ∧ i ≤ M by omega)]
    rw [hstr i (by omega)]
    simp only [Out.toPair]
    rw [← (hdom i (by omega) h2).1]
    exact ⟨enc_hon_zero _, enc_hon_one _, trivial⟩

/-- **The good event at a horizon implies it at an earlier one.** -/
theorem good_horizon_mono {w : CStr} {N N' M Lw r G : ℕ} (hN : N' ≤ N) (hg : GoodCap E N M Lw r G w) :
    GoodCap E N' M Lw r G w := by
  obtain ⟨⟨h0, hm, hq, hu, hc, hw⟩, hgr⟩ := hg
  exact ⟨⟨h0, hm, fun k hk => hq k (by omega), hu, fun t k h1 h2 h3 h4 => hc t k h1 (by omega) h3 h4,
    fun t ht => hw t (by omega)⟩, fun ep hep hf => hgr ep hep (by omega)⟩

/-- **The good event fails robustly** at `l`: every outcome list dominating `l` fails it. -/
def RBad (N M Lw r G : ℕ) : Set (List Out) :=
  {l | ∀ l', List.Forall₂ OutLe l l' → ¬ GoodCap E N M Lw r G (strOf l')}

theorem GoodCap.withO {O : Oracle} {N M Lw r G : ℕ} (h : GoodCap E N M Lw r G w) :
    GoodCap (E.withO O) N M Lw r G w :=
  ⟨goodLS_withO h.1, h.2⟩

theorem RBad.upClosed {N M Lw r G : ℕ} : UpClosed (RBad E N M Lw r G) :=
  fun _ _ h hl l' h' => hl l' (forall₂_trans h h')

/-- **A robust failure cut at a horizon decides the failure up to `N`.** If `x`, of length
`Ms`, fails robustly the good event up to `Ne < Ms` cut at `Ms`, then every continuation
of `x` to length `M` fails robustly the good event up to `N ≥ Ne` cut at `M`. -/
theorem lift_bad {N Ne Ms M Lw r G : ℕ} (hNe : Ne ≤ N) (hNs : Ne < Ms) (hMs : Ms ≤ M)
    (hgr : ∀ ep, 1 ≤ ep → E.c.fix ep ≤ Ne → E.c.cut ep + G < Ms) {x : List Out} (hx : x.length = Ms)
    (h : x ∈ RBad E Ne Ms Lw r G) : Decided (RBad E N M Lw r G) M x := by
  intro y _ l' hl' hg
  have hlen : Ms ≤ l'.length := by rw [← hl'.length_eq, List.length_append]; omega
  have hsim : SimOn (strOf l') (strOf (l'.take Ms)) 0 Ms := by
    intro i _ h2
    have : strOf l' i = strOf (l'.take Ms) i := by
      conv_lhs => rw [← List.take_append_drop Ms l']
      exact strOf_append_of_le (by rw [List.length_take]; omega)
    rw [this]; exact ⟨Iff.rfl, Iff.rfl, rfl⟩
  have hl := List.forall₂_take Ms hl'
  rw [List.take_append_of_le_length (by omega), List.take_of_length_le (by omega)] at hl
  exact h _ hl (good_congr_cap E hsim hNs hgr (good_trunc E hNs hMs hgr (good_horizon_mono E hNe hg)))

end

/-- **A split is a robust failure of the truncated good event.** If epoch `ep + 1`'s
canonical prefix does not extend epoch `ep`'s, every outcome list dominating the
lottery string's first `Ms` slots fails the good event up to `min (fix (ep + 1)) N`, cut
at `Ms`. -/
theorem split_up (E : Env) (hA : Assm E) (hlive : ∀ t, ∃ j ∈ E.nodes, E.online j t = true) {O : Oracle}
    {es : List Event} {N Ms Lw r G ep : ℕ} (hNF : (wF (E.withO O) es).now ≤ N) (hep : 1 ≤ ep)
    (hMs : min (E.c.fix (ep + 1)) N < Ms)
    (hgr : ∀ ep', 1 ≤ ep' → E.c.fix ep' ≤ min (E.c.fix (ep + 1)) N → E.c.cut ep' + G < Ms)
    (hsplit : prefixBelow (CP (E.withO O) es (ep + 1)) (E.c.cut ep) ≠ CP (E.withO O) es ep) :
    slots (lotStr (E.withO O) es) Ms ∈ RBad E (min (E.c.fix (ep + 1)) N) Ms Lw r G := by
  intro l' hl hg
  obtain ⟨w, hdom, hgw⟩ := good_dom (E.withO O) hMs hgr hl hg.withO
  exact hsplit (cons_of_lot (hA.withO O) hlive hep (min_le_min le_rfl hNF) hdom hgw.1 (growthS_on _ hgw.2))

/-- Growth witnesses of epochs fixed by a horizon lie before it. -/
theorem cut_add_lt {c : Config} (hc : c.Sane) {G : ℕ} (hOG : c.nonceOffset + G + 2 ≤ c.epochLength)
    {H Ms : ℕ} (hHM : H < Ms) : ∀ ep, 1 ≤ ep → c.fix ep ≤ H → c.cut ep + G < Ms := by
  intro ep hep hfix
  have : c.cut ep + G ≤ c.fix ep := by
    obtain ⟨e0, rfl⟩ : ∃ e0, ep = e0 + 1 := ⟨ep - 1, by omega⟩
    have hs : c.epochStart (e0 + 1) = c.epochStart e0 + c.epochLength := by
      unfold Config.epochStart; ring
    unfold Config.cut Config.fix
    simp only [Nat.add_sub_cancel]
    omega
  omega

end Cryptarchia.Prob
