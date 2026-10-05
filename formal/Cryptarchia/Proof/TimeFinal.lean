import Cryptarchia.Proof.FinalE

/-!
# Time-based finality

A **confirmation rule** on top of the unchanged protocol: an honest node that has a
block `b` on its local chain when `slot b + Lw ≤ now` treats `b` as final. The
protocol keeps its `k` (the online fork choice still rejects forks deeper than
`k`, which is what the `window` part of the good event is for). Only the
user-facing notion of finality changes: from "`k` blocks deep" to "`Lw` slots
old".

* `time_final` (on the good event `GoodCond` with settlement depth `Lw`): such a
  block is on every honest node's local chain at every later point.
* `time_final_epochs`: the same over any number of epochs, from the lottery-level
  good event, as `final_bimm_epochs`.

Why it is worth having: `k` must cover the most blocks an `Lw` window can hold
(at the top of the TSI band, when the adversary withholds its wins from the stake
inference), so `k` blocks take about twice `Lw` at the normal rate. With this
rule the settlement time is `Lw` itself.

The proof: at any time `m`, two chains dominant at `m` share a block with slot
at least `m - Lw` (`settled`, as in `nearAt`). A block with slot at most
`m - Lw` on the first chain is below that shared block, hence on the second. Step
by step along the execution, each node's new local chain is compared with its
old one, which is dominant at the new time (at a tick by `tickD`).
-/

namespace Cryptarchia

open Settle

variable {E : Env} {es : List Event} {K : ℕ → Prop} {st : Store}

/-! ## Slots along a chain -/

/-- Slots strictly decrease down a chain. -/
theorem slot_lt_iter (hS : StoreOK st) : ∀ (j : ℕ) {b : ℕ}, Rooted st b → 1 ≤ j → j ≤ height st b →
    slotOf st ((parentOf st)^[j] b) < slotOf st b := by
  intro j
  induction j with
  | zero => intro b _ h; omega
  | succ j ih =>
    intro b hb _ hj
    have hne : b ≠ genesisId := by
      intro h; subst h; rw [height_genesis hS] at hj; omega
    obtain ⟨blk, hbk, hpar, hslot⟩ := hb.inv hne
    have hh := height_step hbk hne hpar hslot
    rw [Function.iterate_succ_apply, parentOf_eq hbk, slotOf_eq hbk]
    rcases Nat.eq_zero_or_pos j with h0 | hpos
    · subst h0; simpa using hslot
    · have := ih hpar hpos (by omega)
      omega

/-- A proper ancestor has a smaller slot. -/
theorem slot_lt_anc (hS : StoreOK st) {a b : ℕ} (hb : Rooted st b) (ha : a ∈ chainIds st b)
    (hlt : height st a < height st b) : slotOf st a < slotOf st b := by
  obtain ⟨-, -, he⟩ := anc_height hS hb ha
  have := slot_lt_iter hS (height st b - height st a) hb (by omega) (by omega)
  rwa [he] at this

/-- Of two blocks on one chain, the one with the smaller slot is below the other. -/
theorem below_of_slot (hS : StoreOK st) {b x u : ℕ} (hu : Rooted st u) (hb : b ∈ chainIds st u)
    (hx : x ∈ chainIds st u) (hsl : slotOf st b ≤ slotOf st x) : b ∈ chainIds st x := by
  by_cases h : height st b ≤ height st x
  · exact chainIds_total hS hu hx hb h
  · rw [not_le] at h
    have hxb := chainIds_total hS hu hb hx h.le
    have := slot_lt_anc hS (anc_height hS hu hb).1 hxb h
    omega

/-- The only rooted block with slot `0` is genesis. -/
theorem eq_genesis_of_slot {b : ℕ} (hb : Rooted st b) (h0 : slotOf st b = 0) : b = genesisId := by
  by_contra hne
  obtain ⟨blk, hbk, -, hs⟩ := hb.inv hne
  rw [slotOf_eq hbk] at h0; omega

/-! ## Settlement with the slot of the shared block -/

open Classical in
/-- **Settled at a time.** As `nearAt`, but returning the slot bound on the shared
block instead of its depth: two blocks of the settlement tree with slots up to
`t`, at least as high as the honest depth at the start of the phase, share a
block with slot at least `t - Lw`. -/
theorem simAt (hA : Assm E) (hK : KBase E es K) {Lw : ℕ} {e : ℕ → ℕ} {H : ℕ}
    (hG : GoodCond E es K Lw e H) {t : ℕ}
    (htN : t ≤ (wF E es).now) (htH : t ≤ H) (hA2 : A2Upto E es K t) {k : ℕ}
    (hk : e k + 1 ≤ t ∧ t ≤ e (k + 1)) {u v : ℕ} (hu : u ∈ (FT E es K).V) (hv : v ∈ (FT E es K).V)
    (hsu : slotOf (wF E es).st u ≤ t) (hsv : slotOf (wF E es).st v ≤ t)
    (hdu : (FT E es K).hd (e k - E.Δ) ≤ height (wF E es).st u)
    (hdv : (FT E es K).hd (e k - E.Δ) ≤ height (wF E es).st v) :
    ∃ x, x ∈ chainIds (wF E es).st u ∧ x ∈ chainIds (wF E es).st v ∧
      t - Lw ≤ slotOf (wF E es).st x := by
  have hw := wAt_ok (es := es) hA.ord es.length
  have hS := hw.store
  have hFt := tree_valid_upto (c := E.c) (L := E.L) (O := E.O) (G := E.G) hS E.Δ t htN
    (FTused_ok hA hK).1 (FTused_ok hA hK).2 hA2
  set Ft := (FT E es K).restrict t
  have hur : Rooted (wF E es).st u := (mem_stree.1 hu).2.1
  have hvr : Rooted (wF E es).st v := (mem_stree.1 hv).2.1
  have hu' : u ∈ Ft.V := mem_restrict.2 ⟨hu, hsu⟩
  have hv' : v ∈ Ft.V := mem_restrict.2 ⟨hv, hsv⟩
  have hancu : ∀ x, Ft.Anc x u ↔ x ∈ chainIds (wF E es).st u := fun x =>
    anc_iff (c := E.c) (L := E.L) (O := E.O) (G := E.G)
      (late := Late E es) (used := (wF E es).used.filter (fun b => decide (K b))) (N := (wF E es).now) hS hur
  have hancv : ∀ x, Ft.Anc x v ↔ x ∈ chainIds (wF E es).st v := fun x =>
    anc_iff (c := E.c) (L := E.L) (O := E.O) (G := E.G)
      (late := Late E es) (used := (wF E es).used.filter (fun b => decide (K b))) (N := (wF E es).now) hS hvr
  by_cases hLt : t ≤ Lw
  · exact ⟨genesisId, genesis_mem_chainIds hS hur, genesis_mem_chainIds hS hvr, by omega⟩
  · rw [not_le] at hLt
    have hhd : Ft.hd (e k - E.Δ) = (FT E es K).hd (e k - E.Δ) := restrict_hd (by omega)
    have hsim := PTree.Valid.settled hFt (t - Lw) e hG.e0 hG.mono
      (fun k hk => hG.quiet k (le_trans hk htH)) k t
      (by omega) hk.2 le_rfl (hG.cold t k hLt htH hk.1 hk.2) hu' hv' hsu hsv
      (by rw [hhd]; exact hdu) (by rw [hhd]; exact hdv)
    obtain ⟨x, hx, hxu, hxv, hxl⟩ := hsim
    exact ⟨x, (hancu x).1 hxu, (hancv x).1 hxv, hxl⟩

/-! ## Local chains in the settlement tree -/

/-- An honest node's local chain at a point is a block of the settlement tree,
with slot at most the time. -/
theorem cloc_facts (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {Lw : ℕ} {e : ℕ → ℕ}
    (hG : GoodCond E es K Lw e H) {p : ℕ} (hp : p ≤ es.length) (hpH : (wAt E es p).now ≤ H) {l : ℕ}
    (hl : l ∈ E.nodes) (hlo : E.online l (wAt E es p).now = true) :
    Rooted (wF E es).st ((wAt E es p).node l).cloc ∧ ((wAt E es p).node l).cloc ∈ (FT E es K).V ∧
      slotOf (wF E es).st ((wAt E es p).node l).cloc ≤ (wAt E es p).now := by
  have hw := wAt_ok (es := es) hA.ord p
  have hS := hw.store
  have hext := store_mono (m := es.length) (es := es) hA.ord hp
  have hh := hon_all (es := es) hA.ord hA.exec hA.nodup hA.sane p hp
  have hc := (hw.nodes l).rooted _ (hw.nodes l).cloc
  refine ⟨Rooted.mono hext hc, goodAt_FT hA hS hext (now_mono hp le_rfl)
    (tree_good hS (hw.nodes l) (hh.slots l) (hw.nodes l).cloc) (cloc_K hA hK hG hp hpH hl hlo), ?_⟩
  rw [slotOf_ext hext hc.exists_blk]; exact hh.slots l _ (hw.nodes l).cloc

/-- **One comparison.** At a point `q`, a block `b` at least `Lw` slots old that
lies on some chain dominant at the time is on every honest node's local chain. -/
theorem time_pair (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {Lw : ℕ} {e : ℕ → ℕ}
    (hG : GoodCond E es K Lw e H) {q : ℕ} (hq : q ≤ es.length) (hqH : (wAt E es q).now ≤ H)
    (hq1 : 1 ≤ (wAt E es q).now) {u b : ℕ} (hu : u ∈ (FT E es K).V)
    (hsu : slotOf (wF E es).st u ≤ (wAt E es q).now)
    (hdu : (FT E es K).hd ((wAt E es q).now - E.Δ - 1) ≤ height (wF E es).st u)
    (hb : b ∈ chainIds (wF E es).st u) (hbt : slotOf (wF E es).st b + Lw ≤ (wAt E es q).now)
    {l : ℕ} (hl : l ∈ E.nodes) (hlo : E.online l (wAt E es q).now = true) :
    b ∈ chainIds (wF E es).st ((wAt E es q).node l).cloc := by
  have hS := (wAt_ok (es := es) hA.ord es.length).store
  have hIH := main hA hK hG q hq hqH
  obtain ⟨hvr, hvF, hsv⟩ := cloc_facts hA hK hG hq hqH hl hlo
  obtain ⟨k, hk1, hk2⟩ := phase_of hG.e0 hG.mono hG.unb hq1
  have hur : Rooted (wF E es).st u := (mem_stree.1 hu).2.1
  obtain ⟨x, hxu, hxv, hxl⟩ := simAt hA hK.toKBase hG (now_mono hq le_rfl) hqH
    (A2_of_Hon hA hq hIH.2) ⟨hk1, hk2⟩ hu hvF hsu hsv
    (le_trans (FT_hd_mono (by omega)) hdu) (le_trans (FT_hd_mono (by omega)) (hIH.1 l hl hlo))
  have hsl : slotOf (wF E es).st b ≤ slotOf (wF E es).st x := by omega
  exact chainIds_trans hS hvr hxv (below_of_slot hS hur hb hxu hsl)

/-- A node's local chain before an event is dominant at the time after it. -/
theorem dom_next (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {Lw : ℕ} {e : ℕ → ℕ}
    (hG : GoodCond E es K Lw e H) {p : ℕ} (hp : p < es.length) (hpH : (wAt E es (p + 1)).now ≤ H)
    {l : ℕ} (hl : l ∈ E.nodes) (hlo : E.online l (wAt E es p).now = true) :
    (FT E es K).hd ((wAt E es (p + 1)).now - E.Δ - 1) ≤
      height (wF E es).st ((wAt E es p).node l).cloc := by
  have hpH' : (wAt E es p).now ≤ H := le_trans (now_mono (E := E) (es := es) (Nat.le_succ p) hp) hpH
  have hstep := wAt_succ E es hp
  cases hev : es[p] with
  | tick =>
    have hnow : (wAt E es (p + 1)).now = (wAt E es p).now + 1 := by rw [hstep, step_now, hev]
    rw [hnow]
    exact tickD hA hK hG hp hpH' hev (fun m hm => main hA hK hG m (by omega)
      (le_trans (now_mono (E := E) (es := es) hm.le hp.le) hpH')) l hl hlo
  | deliver j b =>
    have hnow : (wAt E es (p + 1)).now = (wAt E es p).now := by rw [hstep, step_now, hev]; rfl
    rw [hnow]; exact (main hA hK hG p hp.le hpH').1 l hl hlo
  | create B =>
    have hnow : (wAt E es (p + 1)).now = (wAt E es p).now := by rw [hstep, step_now, hev]; rfl
    rw [hnow]; exact (main hA hK hG p hp.le hpH').1 l hl hlo

/-! ## Time-based finality -/

/-- **Time-based finality.** If honest node `i` has block `b` on its local chain at
a point where `b` is at least `Lw` slots old, then `b` is on every honest node's
local chain at every later point (up to the horizon of the good event). -/
theorem time_final (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {Lw : ℕ} {e : ℕ → ℕ}
    (hG : GoodCond E es K Lw e H) {n n' : ℕ} (hnn : n ≤ n') (hn' : n' ≤ es.length)
    (hnH : (wAt E es n').now ≤ H) {i j : ℕ} (hi : i ∈ E.nodes) (hj : j ∈ E.nodes)
    (hio : E.online i (wAt E es n).now = true) (hjo : E.online j (wAt E es n').now = true) {b : ℕ}
    (hb : b ∈ chainIds (wAt E es n).st ((wAt E es n).node i).cloc)
    (hbt : slotOf (wAt E es n).st b + Lw ≤ (wAt E es n).now) :
    b ∈ chainIds (wAt E es n').st ((wAt E es n').node j).cloc := by
  have hS := (wAt_ok (es := es) hA.ord es.length).store
  have hn : n ≤ es.length := le_trans hnn hn'
  have hNow : ∀ p, n ≤ p → p ≤ n' → (wAt E es n).now ≤ (wAt E es p).now ∧ (wAt E es p).now ≤ H :=
    fun p h1 h2 => ⟨now_mono h1 (le_trans h2 hn'), le_trans (now_mono h2 hn') hnH⟩
  -- on the final store
  have hwn := wAt_ok (es := es) hA.ord n
  have hext := store_mono (m := es.length) (es := es) hA.ord hn
  have hci := (hwn.nodes i).rooted _ (hwn.nodes i).cloc
  have hbr : Rooted (wAt E es n).st b := (anc_height hwn.store hci hb).1
  have hbF : b ∈ chainIds (wF E es).st ((wAt E es n).node i).cloc := by
    rw [chainIds_ext hext hci]; exact hb
  have hbtF : slotOf (wF E es).st b + Lw ≤ (wAt E es n).now := by
    rw [slotOf_ext hext hbr.exists_blk]; exact hbt
  -- every point from `n` to `n'`
  have hC : ∀ d, n + d ≤ n' → ∀ l ∈ E.nodes, E.online l (wAt E es (n + d)).now = true →
      b ∈ chainIds (wF E es).st ((wAt E es (n + d)).node l).cloc := by
    rcases Nat.eq_zero_or_pos (slotOf (wF E es).st b) with h0 | hpos
    · have hbg : b = genesisId := eq_genesis_of_slot (Rooted.mono hext hbr) h0
      intro d hd l hl hlo
      subst hbg
      exact genesis_mem_chainIds hS
        (cloc_facts hA hK hG (by omega) (hNow _ (by omega) hd).2 hl hlo).1
    intro d
    induction d with
    | zero =>
      intro _ l hl hlo
      have hH0 := (hNow n le_rfl hnn).2
      obtain ⟨-, huF, hsu⟩ := cloc_facts hA hK hG hn hH0 hi hio
      exact time_pair hA hK hG hn hH0 (by omega) huF hsu
        ((main hA hK hG n hn hH0).1 i hi hio) hbF hbtF hl hlo
    | succ d ih =>
      intro hd l hl hlo
      rw [show n + (d + 1) = n + d + 1 by omega] at hd hlo ⊢
      have hp : n + d < es.length := by omega
      obtain ⟨h1, hH1⟩ := hNow (n + d + 1) (by omega) hd
      obtain ⟨h0', hH0⟩ := hNow (n + d) (by omega) (by omega)
      have hlo' : E.online l (wAt E es (n + d)).now = true :=
        hA.crash l _ _ (now_mono (E := E) (es := es) (Nat.le_succ _) hp) hlo
      obtain ⟨-, huF, hsu⟩ := cloc_facts hA hK hG hp.le hH0 hl hlo'
      have hmono := now_mono (E := E) (es := es) (Nat.le_succ (n + d)) hp
      exact time_pair (q := n + d + 1) hA hK hG hp hH1 (by omega) huF (le_trans hsu hmono)
        (dom_next hA hK hG hp hH1 hl hlo') (ih (by omega) l hl hlo') (by omega) hl hlo
  have hwn' := wAt_ok (es := es) hA.ord n'
  have hcj := (hwn'.nodes j).rooted _ (hwn'.nodes j).cloc
  have e1 : n + (n' - n) = n' := by omega
  have := hC (n' - n) (by omega) j hj (by rw [e1]; exact hjo)
  rw [e1] at this
  rw [← chainIds_ext (store_mono (m := es.length) (es := es) hA.ord hn') hcj]; exact this

variable {Lw : ℕ} {e : ℕ → ℕ}

/-- **Time-based finality over any number of epochs**, with the config's fixing
times and the simple growth condition, as `final_bimm_epochs`. -/
theorem time_final_epochs (hA : Assm E)
    {N : ℕ} (hNF : (wF E es).now ≤ N)
    (hL : GoodLS E (lotStrS E (σE E es) (lateAt E es)) N Lw e) {r G0 : ℕ}
    (hLg : GrowthS E (lotStrS E (σE E es) (lateAt E es)) e N r G0)
    {n n' : ℕ} (hnn : n ≤ n') (hn' : n' ≤ es.length) {i j : ℕ} (hi : i ∈ E.nodes) (hj : j ∈ E.nodes)
    (hio : E.online i (wAt E es n).now = true) (hjo : E.online j (wAt E es n').now = true) {b : ℕ}
    (hb : b ∈ chainIds (wAt E es n).st ((wAt E es n).node i).cloc)
    (hbt : slotOf (wAt E es n).st b + Lw ≤ (wAt E es n).now) :
    b ∈ chainIds (wAt E es n').st ((wAt E es n').node j).cloc := by
  have hfix : ∀ ep, 1 ≤ ep → E.c.cut ep ≤ E.c.fix ep ∧ E.c.fix ep + 2 ≤ E.c.epochStart ep :=
    fun ep h => hA.sane.fix_ok ep h
  have hmin : min (E.c.fix (E.c.epochOf (wF E es).now + 1 + 1)) (wF E es).now = (wF E es).now := by
    apply min_eq_right
    have a1 := (hfix (E.c.epochOf (wF E es).now + 1 + 1) (by omega)).1
    have a2 := epochStart_epochOf_succ E.c hA.sane (wF E es).now
    unfold Config.cut at a1
    simp only [Nat.add_sub_cancel] at a1
    omega
  obtain ⟨hG, hGr⟩ := stage hA hNF (AdvLeW.refl _) hL (growthS_on E hLg) (E.c.epochOf (wF E es).now + 1)
  rw [hmin] at hG hGr
  exact time_final hA (cons_ok hA hG hGr) hG hnn hn'
    (now_mono hn' le_rfl) hi hj hio hjo hb hbt

end Cryptarchia
