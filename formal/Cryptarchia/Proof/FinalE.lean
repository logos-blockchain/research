import Cryptarchia.Proof.LotteryE

/-!
# Settlement from the lottery, over any number of epochs

The good event is a condition on the **multi-epoch lottery string**
`lotStrS E (σE E es)`: per slot, the honest nodes and the adversary holding a
winning note under the canonical state of the slot's epoch. Under the
idealization that each epoch's lottery is fresh randomness (no nonce grinding),
its law depends only on the canonical stake distribution and stake estimate of
the epoch, which the probability layer bounds.

`GoodLSW w N W e` is the good event on a string `w` up to `N`, with a settlement
window `W t` that may depend on the slot (`GoodLS w N Lw e` is the constant case); `GrowthOn` the
growth condition (both from `Proof/Canon.lean` and `Proof/Final.lean`).

**Staged argument.** Domination of the execution's string by the lottery string
needs canonical states, which need settlement, which needs the good event on the
execution's string. The circle is broken epoch by epoch (`stage`): with the
invariant up to `H_s = min (E.c.fix (s+1)) now`, every epoch starting by `H_(s+1)` is
already fixed, so domination holds up to `H_(s+1)`, and with it the execution's
good event up to `H_(s+1)`.

`final_bimm_epochs`: on the lottery's good event and the simple growth condition
(`GrowthS`), with each epoch's state read at the config's fixing time
(`Config.fix`, two slots before the epoch starts), **a block that an honest node
has committed as immutable is on every honest node's local chain at every later
point, over any number of epochs, whatever the adversary does.**
The proof turns `GrowthS` into the general growth condition `GrowthOn` (`growthS_on`).
-/

namespace Cryptarchia

open Settle

variable (E : Env)

/-- **The good event on a string `w`**, up to `N`. -/
structure GoodLSW (w : CStr) (N : ℕ) (W : ℕ → ℕ) (e : ℕ → ℕ) : Prop where
  e0 : e 0 = 0
  mono : ∀ k, e k ≤ e (k + 1)
  quiet : ∀ k, e k ≤ N → Quiet E.Δ w (e k)
  unb : ∀ t, ∃ k, t ≤ e k
  cold : ∀ t k, W t < t → t ≤ N → e k + 1 ≤ t → t ≤ e (k + 1) →
    (bnd E.Δ w (t - W t) e k).2 < -(advCnt w (e k) (e (k + 1)) : ℤ)
  window : ∀ t, t ≤ N → occCnt w (t - W t) t ≤ E.c.k

/-- The good event with a constant settlement window `Lw`. -/
abbrev GoodLS (w : CStr) (N Lw : ℕ) (e : ℕ → ℕ) : Prop := GoodLSW E w N (fun _ => Lw) e

variable {E} {es : List Event} {W : ℕ → ℕ} {e : ℕ → ℕ}

/-- **Transfer to the execution** up to a horizon `Hs`, from weak domination. -/
theorem good_of_dom {K : ℕ → Prop} {w : CStr} {N Hs : ℕ} (hle : AdvLeW Hs (WS E es K) w)
    (hHN : Hs ≤ N) (hL : GoodLSW E w N W e) : GoodCondW E es K W e Hs := by
  refine ⟨hL.e0, hL.mono, fun k hk => quiet_of_le hle hk (hL.quiet k (by omega)), hL.unb, ?_, ?_⟩
  · intro t k h1 h2 h3 h4
    have hb := (bnd_mono (Δ := E.Δ) hle (t - W t) e hL.mono k (by omega)).2
    have ha : (advCnt (WS E es K) (e k) (e (k + 1)) : ℤ) ≤ advCnt w (e k) (e (k + 1)) := by
      exact_mod_cast advCnt_le hle _ _
    have := hL.cold t k h1 (by omega) h3 h4
    omega
  · intro t ht
    exact le_trans (occCnt_le hle ht) (hL.window t (by omega))

theorem growth_of_dom {w : CStr} {N Hs : ℕ} (hle : AdvLeW Hs (WS E es (Cons E es)) w)
    (hHN : Hs ≤ N) (hmono : ∀ k, e k ≤ e (k + 1)) (hL : GrowthOn E w e N) :
    Growth E es e Hs := by
  intro ep hep hFH
  obtain ⟨j, h1, h2, h3⟩ := hL ep hep (by omega)
  refine ⟨j, h1, h2, ?_⟩
  have hb := (bnd_mono (Δ := E.Δ) hle 0 e hmono j (by omega)).1
  have hh := hD_eq (Δ := E.Δ) hle (e j) (E.c.fix ep - E.Δ - 1) (by omega)
  rw [hh]; linarith

/-- The good event up to horizon `0` holds for every string. -/
theorem good_zero {K : ℕ → Prop} (he0 : e 0 = 0) (hmono : ∀ k, e k ≤ e (k + 1))
    (hunb : ∀ t, ∃ k, t ≤ e k) : GoodCondW E es K W e 0 := by
  refine ⟨he0, hmono, ?_, hunb, fun t k h1 h2 => by omega, ?_⟩
  · intro k hk j h1 h2 h3; omega
  · intro t ht
    have : t = 0 := by omega
    subst this
    unfold occCnt; simp

theorem epochStart_epochOf_succ (c : Config) (hc : c.Sane) (t : ℕ) :
    t < c.epochStart (c.epochOf t + 1) := by
  unfold Config.epochStart Config.epochOf
  have := Nat.lt_div_mul_add (a := t) hc.epochLength_pos
  rw [Nat.add_mul, one_mul]; exact this

/-- **The stages.** For every `s`, the execution's good event and growth hold up
to `min (E.c.fix (s+1)) now`. -/
theorem stage (hA : Assm E)
    {N : ℕ} (hNF : (wF E es).now ≤ N) {w : CStr} (hdom : AdvLeW N (lotStrS E (σE E es) (lateAt E es)) w)
    (hL : GoodLSW E w N W e) (hLg : GrowthOn E w e N) :
    ∀ s, GoodCondW E es (Cons E es) W e (min (E.c.fix (s + 1)) (wF E es).now) ∧
      Growth E es e (min (E.c.fix (s + 1)) (wF E es).now) := by
  have hfix : ∀ ep, 1 ≤ ep → E.c.cut ep ≤ E.c.fix ep ∧ E.c.fix ep + 2 ≤ E.c.epochStart ep :=
    fun ep h => hA.sane.fix_ok ep h
  have hfix2 : ∀ ep, 1 ≤ ep → E.c.fix ep + 2 ≤ E.c.epochStart ep := fun ep h => (hfix ep h).2
  -- the fixing points are ordered with the epochs
  have hord : ∀ ep ep', 1 ≤ ep → ep ≤ ep' → E.c.fix ep ≤ E.c.fix ep' := by
    intro ep ep' h1 h2
    rcases Nat.eq_or_lt_of_le h2 with h | h
    · rw [h]
    · have a1 := (hfix ep h1).2
      have a2 := (hfix ep' (by omega)).1
      have a3 : E.c.epochStart ep ≤ E.c.epochStart (ep' - 1) := epochStart_mono (by omega)
      unfold Config.cut at a2
      omega
  -- one stage from a previous horizon `H'`
  have step : ∀ (H' Hs : ℕ), H' ≤ (wF E es).now → Hs ≤ (wF E es).now →
      GoodCondW E es (Cons E es) W e H' → Growth E es e H' →
      (∀ ep, 1 ≤ ep → E.c.epochStart ep ≤ Hs → E.c.fix ep ≤ H') →
      GoodCondW E es (Cons E es) W e Hs ∧ Growth E es e Hs := by
    intro H' Hs hH' hHs hG hGr hcov
    have hle := (advLeW_lotE hA hG hGr hH' hcov hHs).trans hdom (by omega)
    exact ⟨good_of_dom hle (by omega) hL, growth_of_dom hle (by omega) hL.mono hLg⟩
  intro s
  induction s with
  | zero =>
    -- from the empty horizon: no epoch starts by `E.c.fix 1`
    have hG0 : GoodCondW E es (Cons E es) W e 0 := good_zero hL.e0 hL.mono hL.unb
    have hGr0 : Growth E es e 0 := by
      intro ep hep hF
      have := (hfix ep hep).1
      have : 1 ≤ E.c.cut ep := by unfold Config.cut; have := hA.sane.offset_pos; omega
      omega
    refine step 0 _ (Nat.zero_le _) (min_le_right _ _) hG0 hGr0 ?_
    intro ep hep hst
    simp only [Nat.zero_add] at hst
    have a1 := hfix2 1 le_rfl
    have a2 : E.c.epochStart 1 ≤ E.c.epochStart ep := epochStart_mono hep
    have := min_le_left (E.c.fix 1) (wF E es).now
    omega
  | succ s ih =>
    refine step _ _ (min_le_right _ _) (min_le_right _ _) ih.1 ih.2 ?_
    intro ep hep hst
    have hm1 := min_le_left (E.c.fix (s + 1 + 1)) (wF E es).now
    have hm2 := min_le_right (E.c.fix (s + 1 + 1)) (wF E es).now
    -- the epoch starts before `E.c.fix (s+2)`, so it is at most `s+1`
    have hep' : ep ≤ s + 1 := by
      by_contra hc; push Not at hc
      have a1 := hfix2 (s + 1 + 1) (by omega)
      have a2 : E.c.epochStart (s + 1 + 1) ≤ E.c.epochStart ep := epochStart_mono (by omega)
      omega
    have h1 := hord ep (s + 1) hep hep'
    have h2 := hfix2 ep hep
    exact le_min h1 (by omega)

/-- **`k`-deep finality from the lottery, over any number of epochs.** Each
epoch's canonical state is read at the config's fixing time (`Config.fix`, two
slots before the epoch starts). On the lottery's good event and the simple growth
condition (`GrowthS`: a reach cap `r` near the cut, and honest depth growing by more
than `k + r` over the epoch's last phase), a block that an honest node has committed
as immutable is on every honest node's local chain at every later point, whatever
the adversary does.

Stated for any string `w` that dominates the lottery string (`AdvLeW`: the same
honest successes, and every adversarial slot of the lottery string adversarial in
`w`); `final_bimm_epochs` is the case `w` = the lottery string. -/
theorem final_bimm_dom (hA : Assm E)
    {N : ℕ} (hNF : (wF E es).now ≤ N) {w : CStr} (hdom : AdvLeW N (lotStrS E (σE E es) (lateAt E es)) w)
    (hL : GoodLSW E w N W e) {r G0 : ℕ} (hLg : GrowthS E w e N r G0)
    {n n' : ℕ} (hnn : n ≤ n') (hn' : n' ≤ es.length) {i j : ℕ} (hi : i ∈ E.nodes) (hj : j ∈ E.nodes)
    (hio : E.online i (wAt E es n').now = true) (hjo : E.online j (wAt E es n').now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n').st ((wAt E es n').node j).cloc := by
  have hfix : ∀ ep, 1 ≤ ep → E.c.cut ep ≤ E.c.fix ep ∧ E.c.fix ep + 2 ≤ E.c.epochStart ep :=
    fun ep h => hA.sane.fix_ok ep h
  have hmin : min (E.c.fix (E.c.epochOf (wF E es).now + 1 + 1)) (wF E es).now = (wF E es).now := by
    apply min_eq_right
    have a1 := (hfix (E.c.epochOf (wF E es).now + 1 + 1) (by omega)).1
    have a2 := epochStart_epochOf_succ E.c hA.sane (wF E es).now
    unfold Config.cut at a1
    simp only [Nat.add_sub_cancel] at a1
    omega
  obtain ⟨hG, hGr⟩ := stage hA hNF hdom hL (growthS_on E hLg) (E.c.epochOf (wF E es).now + 1)
  rw [hmin] at hG hGr
  exact bimm_final_epochs hA hG hGr hnn hn' (now_mono hn' le_rfl) hi hj hio hjo

/-- **Finality over any number of epochs**, on the lottery string's good event. -/
theorem final_bimm_epochs (hA : Assm E)
    {N : ℕ} (hNF : (wF E es).now ≤ N) {Lw : ℕ}
    (hL : GoodLS E (lotStrS E (σE E es) (lateAt E es)) N Lw e) {r G0 : ℕ}
    (hLg : GrowthS E (lotStrS E (σE E es) (lateAt E es)) e N r G0)
    {n n' : ℕ} (hnn : n ≤ n') (hn' : n' ≤ es.length) {i j : ℕ} (hi : i ∈ E.nodes) (hj : j ∈ E.nodes)
    (hio : E.online i (wAt E es n').now = true) (hjo : E.online j (wAt E es n').now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n').st ((wAt E es n').node j).cloc :=
  final_bimm_dom hA hNF (AdvLeW.refl _) hL hLg hnn hn' hi hj hio hjo

/-- A settlement window chosen per epoch: slot `t` uses `Wk` of its epoch. -/
def epochWindow (c : Config) (Wk : ℕ → ℕ) : ℕ → ℕ := fun t => Wk (c.epochOf t)

/-- **Finality with a settlement window per epoch.** As `final_bimm_epochs`, with
the good event's window at slot `t` set by `t`'s epoch (`Wk e` slots in epoch `e`).
The deterministic argument only uses each slot's own window, so any assignment of
windows to epochs works. -/
theorem final_bimm_epochWin (hA : Assm E)
    {N : ℕ} (hNF : (wF E es).now ≤ N) {Wk : ℕ → ℕ}
    (hL : GoodLSW E (lotStrS E (σE E es) (lateAt E es)) N (epochWindow E.c Wk) e) {r G0 : ℕ}
    (hLg : GrowthS E (lotStrS E (σE E es) (lateAt E es)) e N r G0)
    {n n' : ℕ} (hnn : n ≤ n') (hn' : n' ≤ es.length) {i j : ℕ} (hi : i ∈ E.nodes) (hj : j ∈ E.nodes)
    (hio : E.online i (wAt E es n').now = true) (hjo : E.online j (wAt E es n').now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n').st ((wAt E es n').node j).cloc :=
  final_bimm_dom hA hNF (AdvLeW.refl _) hL hLg hnn hn' hi hj hio hjo

end Cryptarchia
