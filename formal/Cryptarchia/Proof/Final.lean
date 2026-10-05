import Cryptarchia.Proof.Lottery

/-!
# Settlement from the lottery alone

The good event is now a condition on the **lottery string** (`lotStr`): per slot,
how many honest nodes hold a winning note under the genesis epoch state, and
whether the adversary does. It mentions no adversarial choice (block creation,
delivery schedule, tip order), so its probability is a function of the stake
distribution and the lottery parameters only.

`GoodL N Lw e` for a horizon `N` (in slots), a settlement depth `Lw` (in slots)
and a phase decomposition `e`:
* `quiet`: every phase ends with `Δ` slots without honest successes;
* `cold`: for every time `t ≤ N` after `Lw`, the margin bound for divergence
  before `t - Lw` is cold at the start of the phase containing `t - 1`;
* `window`: no `Lw` consecutive slots up to `N` hold more than `k` occupied slots.

`good_of_lottery`: `GoodL` implies the execution's good event (`GoodCond`), for
every adversary, when the execution stays within the horizon. Hence the
settlement theorems (`final_bimm`, `final_agree`) hold on `GoodL`.
-/

namespace Cryptarchia

open Settle

variable (E : Env)

/-- **The good event on the lottery string.** -/
structure GoodL (lt : ℕ → ℕ → Prop) (N Lw : ℕ) (e : ℕ → ℕ) : Prop where
  e0 : e 0 = 0
  mono : ∀ k, e k ≤ e (k + 1)
  quiet : ∀ k, e k ≤ N → Quiet E.Δ (lotStr E lt) (e k)
  unb : ∀ t, ∃ k, t ≤ e k
  cold : ∀ t k, Lw < t → t ≤ N → e k + 1 ≤ t → t ≤ e (k + 1) →
    (bnd E.Δ (lotStr E lt) (t - Lw) e k).2 < -(advCnt (lotStr E lt) (e k) (e (k + 1)) : ℤ)
  window : ∀ t, t ≤ N → occCnt (lotStr E lt) (t - Lw) t ≤ E.c.k

variable {E} {es : List Event}

/-- **The lottery's good event implies the execution's**, for every adversary. -/
theorem good_of_lottery (hA : Assm E) (hE0 : (wF E es).now < E.c.epochLength) {N Lw : ℕ} {e : ℕ → ℕ}
    (hNF : (wF E es).now ≤ N) (hG : GoodL E (lateAt E es) N Lw e) :
    GoodCond E es (fun _ => True) Lw e (wF E es).now := by
  have hle := advLe_lot hA hE0
  refine ⟨hG.e0, hG.mono, fun k hk => quiet_of hle _ (hG.quiet k (by omega)), hG.unb, ?_, ?_⟩
  · intro t k h1 h2 h3 h4
    have hb := (bnd_mono (Δ := E.Δ) hle.weak (t - Lw) e hG.mono k (by omega)).2
    have ha : (advCnt (WS E es (fun _ => True)) (e k) (e (k + 1)) : ℤ) ≤ advCnt (lotStr E (lateAt E es)) (e k) (e (k + 1)) := by
      exact_mod_cast advCnt_le hle.weak _ _
    have := hG.cold t k h1 (by omega) h3 h4
    omega
  · intro t ht
    exact le_trans (occCnt_le hle.weak ht) (hG.window t (by omega))

/-- **`k`-deep finality from the lottery.** On the lottery's good event, a block
an honest node has committed as immutable is on every honest node's local chain
at every later point, whatever the adversary does. -/
theorem final_bimm (hA : Assm E) (hE0 : (wF E es).now < E.c.epochLength) {N Lw : ℕ} {e : ℕ → ℕ}
    (hNF : (wF E es).now ≤ N) (hG : GoodL E (lateAt E es) N Lw e) {n n' : ℕ}
    (hnn : n ≤ n') (hn' : n' ≤ es.length) {i j : ℕ} (hi : i ∈ E.nodes) (hj : j ∈ E.nodes)
    (hio : E.online i (wAt E es n').now = true) (hjo : E.online j (wAt E es n').now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n').st ((wAt E es n').node j).cloc :=
  bimm_final hA (KOK_true _) (good_of_lottery hA hE0 hNF hG) hnn hn' (now_mono hn' le_rfl) hi hj hio hjo

/-- **Agreement from the lottery.** On the lottery's good event, at every point of
the execution each honest node's `B_imm` is on every honest node's local chain. -/
theorem final_agree (hA : Assm E) (hE0 : (wF E es).now < E.c.epochLength) {N Lw : ℕ} {e : ℕ → ℕ}
    (hNF : (wF E es).now ≤ N) (hG : GoodL E (lateAt E es) N Lw e) {n : ℕ} (hn : n ≤ es.length) {i j : ℕ}
    (hi : i ∈ E.nodes) (hj : j ∈ E.nodes) (hio : E.online i (wAt E es n).now = true)
    (hjo : E.online j (wAt E es n).now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st ((wAt E es n).node j).cloc :=
  agree_now hA (KOK_true _) (good_of_lottery hA hE0 hNF hG) hn (now_mono hn le_rfl) hi hj hio hjo

end Cryptarchia
