import Cryptarchia.Proof.Settlement

/-!
# Canonical epoch states across epochs

Every chain derives its own epoch state. For the settlement analysis over many
epochs, the settlement tree is restricted to chains **consistent** with one
canonical state per epoch (`Cons`): a block with slot at or after the start of
epoch `e ≥ 1` must have the canonical prefix below the cut of `e`
(`Config.cut`, 72 h before the epoch starts at the spec parameters).

The canonical prefix `CP e` is read off node `i0`'s immutable block two slots
before epoch `e` starts (`idxE e`). `cons_step` proves the obligation `KOK.step`:
at every point, every chain through an honest node's immutable block is
consistent, for every tip order and whatever the adversary does, provided the
**growth** condition holds (`Growth`): honest depth grows by more than
`k` plus the reach bound between the cut and the epoch start. Then

* every honest immutable block has passed the cut when the epoch's state is
  first used (from dominance, the reach bound, and growth), and
* all honest nodes' immutable blocks share the prefix below the cut (agreement);

and immutable blocks never revert, so honest nodes never leave the canonical
prefix: the online rule rejects every fork that diverged below `B_imm`.
-/

namespace Cryptarchia

open Settle

variable (E : Env) (es : List Event)

open Classical in
/-- The index at which epoch `e`'s canonical state is fixed: the first point at
which the clock has reached the fixing time `E.c.fix e` (the end of the trace if
never). -/
noncomputable def idxE (e : ℕ) : ℕ :=
  Nat.find (⟨es.length, Or.inl rfl⟩ : ∃ n, n = es.length ∨ E.c.fix e ≤ (wAt E es n).now)

open Classical in
/-- The reference node for epoch `e`: a node online at the fixing point, if any. -/
noncomputable def i0 (e : ℕ) : ℕ :=
  if h : ∃ j ∈ E.nodes, E.online j (wAt E es (idxE E es e)).now = true then Classical.choose h else 0

/-- **The canonical prefix of epoch `e`.** -/
noncomputable def CP (e : ℕ) : List Block :=
  prefixBelow (chainUp (wF E es).st ((wAt E es (idxE E es e)).node (i0 E es e)).bimm) (E.c.cut e)

/-- **Consistency** with the canonical epoch states. -/
def Cons (b : ℕ) : Prop :=
  ∀ e, 1 ≤ e → E.c.epochStart e ≤ slotOf (wF E es).st b →
    prefixBelow (chainUp (wF E es).st b) (E.c.cut e) = CP E es e

/-- **The growth condition** on a characteristic string `w`, for each epoch whose
state is fixed within the horizon `H`: the fixing time is at least two slots
before the epoch starts, and between the cut and the fixing time there is a
phase end after which honest depth grows by more than `k` plus the reach bound
there. -/
def GrowthOn (w : CStr) (e : ℕ → ℕ) (H : ℕ) : Prop :=
  ∀ ep, 1 ≤ ep → E.c.fix ep ≤ H →
    ∃ j, E.c.cut ep - 2 ≤ e j ∧ e j + E.Δ + 1 ≤ E.c.fix ep ∧
      (bnd E.Δ w 0 e j).1 + E.c.k < (hD E.Δ w (e j) (E.c.fix ep - E.Δ - 1) : ℤ)

/-- Moving the start of a window later never increases honest depth. -/
theorem hD_anti {Δ : ℕ} {w : CStr} {a a' : ℕ} (h : a ≤ a') : ∀ b, hD Δ w a' b ≤ hD Δ w a b := by
  intro b
  induction b using Nat.strong_induction_on with
  | _ b ih =>
    unfold hD
    by_cases hb' : b ≤ a'
    · simp only [hb', ↓reduceDIte, Nat.zero_le]
    · have hba : ¬ b ≤ a := by omega
      rw [dif_neg hb', dif_neg hba]
      by_cases hw : (w b).1 = 0
      · simp only [hw, ↓reduceIte]; exact ih (b - 1) (by omega)
      · simp only [hw, ↓reduceIte]; exact Nat.add_le_add_right (ih (b - Δ - 1) (by omega)) 1

/-- An honest depth above zero needs a nonempty window. -/
theorem lt_of_hD_pos {Δ : ℕ} {w : CStr} {a b : ℕ} (h : 0 < hD Δ w a b) : a < b := by
  by_contra hle; push Not at hle
  rw [hD] at h; simp only [hle, ↓reduceDIte] at h; omega

/-- **The simple growth condition**, on a characteristic string `w`, for each
epoch whose fixing time `Config.fix` falls within the horizon `H`:

* some phase ends between two slots before the cut and `G0` slots after it, and
  the adversary's reach bound there is at most `r`;
* honest depth grows by more than `k + r` from `G0` slots after the cut to `Δ + 1`
  slots before the fixing time.

Both are lottery events with simple tails (a reach cap, and a lower tail on
honest depth over most of the epoch's last phase). -/
def GrowthS (w : CStr) (e : ℕ → ℕ) (H r G0 : ℕ) : Prop :=
  ∀ ep, 1 ≤ ep → E.c.fix ep ≤ H →
    ∃ j, E.c.cut ep - 2 ≤ e j ∧ e j ≤ E.c.cut ep + G0 ∧ (bnd E.Δ w 0 e j).1 ≤ (r : ℤ) ∧
      E.c.k + r < hD E.Δ w (E.c.cut ep + G0) (E.c.fix ep - E.Δ - 1)

/-- The simple growth condition gives the growth condition at the config's fixing
times. -/
theorem growthS_on {w : CStr} {e : ℕ → ℕ} {H r G0 : ℕ} (h : GrowthS E w e H r G0) :
    GrowthOn E w e H := by
  intro ep hep hH
  obtain ⟨j, h1, h2, hr, hg⟩ := h ep hep hH
  have hlt := lt_of_hD_pos (Δ := E.Δ) (w := w) (by omega : 0 < hD E.Δ w (E.c.cut ep + G0) (E.c.fix ep - E.Δ - 1))
  have hanti := hD_anti (Δ := E.Δ) (w := w) h2 (E.c.fix ep - E.Δ - 1)
  refine ⟨j, h1, by omega, ?_⟩
  have : ((E.c.k + r : ℕ) : ℤ) < (hD E.Δ w (e j) (E.c.fix ep - E.Δ - 1) : ℤ) := by exact_mod_cast (by omega)
  push_cast at this
  linarith

/-- Growth on the execution's (consistent) string. -/
abbrev Growth (e : ℕ → ℕ) (H : ℕ) : Prop := GrowthOn E (WS E es (Cons E es)) e H

variable {E es}

theorem now_succ_le {n : ℕ} (hn : n < es.length) : (wAt E es (n + 1)).now ≤ (wAt E es n).now + 1 := by
  rw [wAt_succ E es hn, step_now]; split <;> omega

/-- The clock at `idxE e` is exactly `E.c.fix e` (if the execution gets there), and
earlier it was lower. -/
theorem idxE_spec {e : ℕ} (hreach : E.c.fix e ≤ (wF E es).now) :
    idxE E es e ≤ es.length ∧ (wAt E es (idxE E es e)).now = E.c.fix e ∧
      ∀ n < idxE E es e, (wAt E es n).now < E.c.fix e := by
  classical
  have hex : ∃ n, n = es.length ∨ E.c.fix e ≤ (wAt E es n).now := ⟨es.length, Or.inl rfl⟩
  have hspec := Nat.find_spec hex
  have hmin : ∀ n < Nat.find hex, ¬ (n = es.length ∨ E.c.fix e ≤ (wAt E es n).now) :=
    fun n hn => Nat.find_min hex hn
  have hle : Nat.find hex ≤ es.length := Nat.find_min' hex (Or.inl rfl)
  have hreach' : E.c.fix e ≤ (wAt E es (Nat.find hex)).now := by
    rcases hspec with h | h
    · rw [h]; exact hreach
    · exact h
  have hbefore : ∀ n < Nat.find hex, (wAt E es n).now < E.c.fix e := by
    intro n hn
    have := hmin n hn; push Not at this; exact this.2
  refine ⟨hle, ?_, hbefore⟩
  show (wAt E es (Nat.find hex)).now = E.c.fix e
  rcases Nat.eq_zero_or_pos (Nat.find hex) with h0 | hpos
  · rw [h0, wAt_zero] at hreach' ⊢; simp [World.init] at hreach' ⊢; omega
  · obtain ⟨p, hp⟩ : ∃ p, Nat.find hex = p + 1 := ⟨Nat.find hex - 1, by omega⟩
    have hb := hbefore p (by omega)
    have hs := now_succ_le (E := E) (es := es) (n := p) (by omega)
    rw [hp] at hreach' ⊢; omega

/-- The first index at which the clock reaches `E.c.fix e` is at most any index at
which it has. -/
theorem idxE_le {e n : ℕ} (hn : n ≤ es.length) (h : E.c.fix e ≤ (wAt E es n).now) : idxE E es e ≤ n := by
  classical
  have hex : ∃ n, n = es.length ∨ E.c.fix e ≤ (wAt E es n).now := ⟨es.length, Or.inl rfl⟩
  exact Nat.find_min' hex (Or.inr h)

theorem cons_gen (hA : Assm E) : Cons E es genesisId := by
  have hEL := hA.sane.epochLength_pos
  intro e he hs
  have hw := wAt_ok (es := es) hA.ord es.length
  rw [slotOf_genesis hw.store] at hs
  have : E.c.epochLength ≤ E.c.epochStart e := by
    unfold Config.epochStart; exact Nat.le_mul_of_pos_left _ he
  omega

theorem cut_le_start {c : Config} (hc : c.Sane) {e : ℕ} (he : 1 ≤ e) : c.cut e ≤ c.epochStart e := by
  unfold Config.cut
  obtain ⟨e0, rfl⟩ : ∃ e0, e = e0 + 1 := ⟨e - 1, by omega⟩
  simp only [Nat.add_sub_cancel]; rw [epochStart_succ]; have := hc.offset_le; omega

theorem cons_par (hA : Assm E) {b : ℕ} (hb : Rooted (wF E es).st b) (hK : Cons E es b) :
    Cons E es (parentOf (wF E es).st b) := by
  have hw := wAt_ok (es := es) hA.ord es.length
  have hS := hw.store
  intro e he hs
  have hpb : parentOf (wF E es).st b ∈ chainIds (wF E es).st b := by
    rcases eq_or_ne b genesisId with h0 | h0
    · subst h0; obtain ⟨g, hg, -, hgp⟩ := hS.gen; rw [parentOf_eq hg, hgp]
      exact self_mem_chainIds hS hb
    · obtain ⟨blk, hbk, hpr, hsl⟩ := hb.inv h0
      rw [parentOf_eq hbk]
      unfold chainIds; rw [chain_step hbk h0 hpr hsl]; simp
      right; simpa [chainIds] using self_mem_chainIds hS hpr
  have hsb := slot_anc_le hS hb hpb
  have hcut : E.c.cut e ≤ slotOf (wF E es).st (parentOf (wF E es).st b) + 1 := by
    have := cut_le_start hA.sane he; omega
  rw [← prefixBelow_common hS hb hpb hcut]
  exact hK e he (le_trans hs hsb)

theorem cons_base (hA : Assm E) : KBase E es (Cons E es) :=
  ⟨cons_gen hA, fun _ hb hK => cons_par hA hb hK⟩

theorem bnd_fst_nonneg {Δ : ℕ} {w : CStr} (ℓ : ℕ) (e : ℕ → ℕ) (k : ℕ) : 0 ≤ (bnd Δ w ℓ e k).1 := by
  cases k with
  | zero => simp [bnd]
  | succ k => simp only [bnd, step]; exact le_trans (by positivity) (le_max_right _ _)

variable {W : ℕ → ℕ} {e : ℕ → ℕ} {H : ℕ}

/-- **Growth.** At the point fixing epoch `ep`, every honest node's immutable
block has passed the cut of `ep`. -/
theorem bimm_past_cut (hA : Assm E)
    (hG : GoodCondW E es (Cons E es) W e H) (hGr : Growth E es e H) {ep : ℕ} (hep : 1 ≤ ep)
    (hFH : E.c.fix ep ≤ H) (hreach : E.c.fix ep ≤ (wF E es).now)
    (hD : DomAt (E := E) (es := es) (K := Cons E es) (idxE E es ep)
      ((wAt E es (idxE E es ep)).now - E.Δ - 1))
    (hH : HonAt (E := E) (es := es) (K := Cons E es) (idxE E es ep))
    {j : ℕ} (hj : j ∈ E.nodes) (hjo : E.online j (wAt E es (idxE E es ep)).now = true)
    (hKb : Cons E es ((wAt E es (idxE E es ep)).node j).bimm) :
    E.c.cut ep ≤ slotOf (wAt E es (idxE E es ep)).st ((wAt E es (idxE E es ep)).node j).bimm + 1 := by
  obtain ⟨ph, hph1, hph2, hgrow⟩ := hGr ep hep hFH
  obtain ⟨hmle, hnow, -⟩ := idxE_spec hreach
  set m := idxE E es ep with hm
  set b := E.c.fix ep - E.Δ - 1 with hb
  have hwF := wAt_ok (es := es) hA.ord es.length
  have hS := hwF.store
  have hw := wAt_ok (es := es) hA.ord m
  have hext := store_mono (m := es.length) (es := es) hA.ord hmle
  have hh := hon_all (es := es) hA.ord hA.exec hA.nodup hA.sane m hmle
  have hmN : (wAt E es m).now ≤ (wF E es).now := now_mono hmle le_rfl
  have hbN : b ≤ (wF E es).now := by omega
  have hA2 : A2Upto E es (Cons E es) b := by
    intro u hu v hv huh hvh hvb huv
    exact A2_of_Hon hA hmle hH u hu v hv huh hvh (by omega) huv
  have hF := tree_valid_upto (c := E.c) (L := E.L) (O := E.O) (G := E.G) hS E.Δ b hbN
    (FTused_ok hA (cons_base hA)).1 (FTused_ok hA (cons_base hA)).2 hA2
  by_contra hlt
  push Not at hlt
  have hcr := (hw.nodes j).rooted _ (hw.nodes j).cloc
  obtain ⟨hbr, hbc⟩ := (hw.nodes j).bimm_on_cloc hw.store
  set z := ((wAt E es m).node j).bimm with hz
  have hzT : z ∈ ((wAt E es m).node j).tree :=
    chainIds_closed hw.store (hw.nodes j).rooted (hw.nodes j).closed (hw.nodes j).cloc z hbc
  have hzG := tree_good hw.store (hw.nodes j) (hh.slots j) hzT
  have hzFT : z ∈ (FT E es (Cons E es)).V := goodAt_FT hA hw.store hext hmN hzG hKb
  have hzs : slotOf (wF E es).st z = slotOf (wAt E es m).st z := slotOf_ext hext hbr.exists_blk
  have hzF : z ∈ ((FT E es (Cons E es)).restrict b).V :=
    mem_restrict.2 ⟨hzFT, by show slotOf (wF E es).st z ≤ b; omega⟩
  have hq_ph : ∀ k, e k ≤ b → Quiet E.Δ (WS E es (Cons E es)) (e k) :=
    fun k hk => hG.quiet k (by omega)
  set F := (FT E es (Cons E es)).restrict b with hFdef
  set w := WS E es (Cons E es) with hwdef
  set R := (bnd E.Δ w 0 e ph).1 with hRdef
  set C := height (wAt E es m).st ((wAt E es m).node j).cloc with hC
  have hRB0 := (hF.bnd_sound 0 e hG.e0 hG.mono hq_ph ph (by omega)).1 z hzF
    (by show slotOf (wF E es).st z ≤ e ph; omega)
  have hRB : (F.dep z : ℤ) - F.hd (e ph - E.Δ) + advCnt w (F.lab z) (e ph) ≤ R := hRB0
  have hq : F.hd (e ph - E.Δ) = F.hd (e ph) := hF.hd_quiet (hq_ph ph (by omega))
  have hgr : F.hd (e ph) + Settle.hD E.Δ w (e ph) b ≤ (FT E es (Cons E es)).hd b := by
    have := hF.hd_growth (hq_ph ph (by omega)) b (by omega) le_rfl
    rw [show F.hd b = (FT E es (Cons E es)).hd b from restrict_hd le_rfl] at this
    exact this
  have hadv : (0 : ℤ) ≤ (advCnt w (F.lab z) (e ph) : ℤ) := by positivity
  have hdom : (FT E es (Cons E es)).hd b ≤ C := by
    have h1 := hD j hj hjo
    rw [show (wAt E es m).now - E.Δ - 1 = b by omega] at h1
    rw [hC, ← height_ext hext hcr]; exact h1
  have hzh : height (wAt E es m).st z = C - E.c.k := by
    rw [hz, (hw.nodes j).bimm]; exact blockAtDepth_height hw.store hcr _
  have hdz : F.dep z = C - E.c.k := by
    show height (wF E es).st z = C - E.c.k
    rw [height_ext hext hbr]; exact hzh
  have hgrow' : R + E.c.k < (Settle.hD E.Δ w (e ph) b : ℤ) := hgrow
  have hR0 : 0 ≤ R := bnd_fst_nonneg 0 e ph
  have hk0 : E.c.k ≤ C := by
    have : ((E.c.k : ℕ) : ℤ) < ((Settle.hD E.Δ w (e ph) b : ℕ) : ℤ) := by linarith
    have : E.c.k < Settle.hD E.Δ w (e ph) b := by exact_mod_cast this
    omega
  rw [hq, hdz, Nat.cast_sub hk0] at hRB
  have h1 : ((F.hd (e ph) + Settle.hD E.Δ w (e ph) b : ℕ) : ℤ) ≤ (C : ℤ) := by
    exact_mod_cast le_trans hgr hdom
  push_cast at h1
  linarith

/-- **The canonical prefix at the point fixing epoch `ep`:** every honest node's
immutable block has passed the cut and carries the canonical prefix. -/
theorem canon_at (hA : Assm E)
    (hG : GoodCondW E es (Cons E es) W e H) (hGr : Growth E es e H) {ep : ℕ} (hep : 1 ≤ ep)
    (hFH : E.c.fix ep ≤ H) (hreach : E.c.fix ep ≤ (wF E es).now)
    (hD : DomAt (E := E) (es := es) (K := Cons E es) (idxE E es ep)
      ((wAt E es (idxE E es ep)).now - E.Δ - 1))
    (hH : HonAt (E := E) (es := es) (K := Cons E es) (idxE E es ep))
    (hKb : ∀ j ∈ E.nodes, E.online j (wAt E es (idxE E es ep)).now = true →
      Cons E es ((wAt E es (idxE E es ep)).node j).bimm)
    (hKc : ∀ j ∈ E.nodes, E.online j (wAt E es (idxE E es ep)).now = true →
      Cons E es ((wAt E es (idxE E es ep)).node j).cloc)
    {j : ℕ} (hj : j ∈ E.nodes) (hjo : E.online j (wAt E es (idxE E es ep)).now = true) :
    E.c.cut ep ≤ slotOf (wAt E es (idxE E es ep)).st ((wAt E es (idxE E es ep)).node j).bimm + 1 ∧
      prefixBelow (chainUp (wF E es).st ((wAt E es (idxE E es ep)).node j).bimm) (E.c.cut ep) =
        CP E es ep := by
  obtain ⟨hmle, hnow, -⟩ := idxE_spec hreach
  set m := idxE E es ep with hm
  have hex : ∃ j ∈ E.nodes, E.online j (wAt E es m).now = true := ⟨j, hj, hjo⟩
  have hi0 : i0 E es ep ∈ E.nodes ∧ E.online (i0 E es ep) (wAt E es m).now = true := by
    unfold i0; rw [dif_pos hex]; exact Classical.choose_spec hex
  have hcj := bimm_past_cut hA hG hGr hep hFH hreach hD hH hj hjo (hKb j hj hjo)
  have hci := bimm_past_cut hA hG hGr hep hFH hreach hD hH hi0.1 hi0.2 (hKb _ hi0.1 hi0.2)
  refine ⟨hcj, ?_⟩
  have hwF := wAt_ok (es := es) hA.ord es.length
  have hS := hwF.store
  have hw := wAt_ok (es := es) hA.ord m
  have hext := store_mono (m := es.length) (es := es) hA.ord hmle
  have hagree := agree_of hA (cons_base hA) hG hmle (by rw [hnow]; exact hFH) hD hH hj hi0.1 hjo hi0.2
    (hKc j hj hjo) (hKc _ hi0.1 hi0.2)
  have hci0 := (hw.nodes (i0 E es ep)).rooted _ (hw.nodes (i0 E es ep)).cloc
  have hbi0 := ((hw.nodes (i0 E es ep)).bimm_on_cloc hw.store)
  have hbj := ((hw.nodes j).bimm_on_cloc hw.store)
  rw [← chainIds_ext hext hci0] at hagree
  have hbi0' := hbi0.2
  rw [← chainIds_ext hext hci0] at hbi0'
  have hr := hci0.mono hext
  have p1 := prefixBelow_common (s := E.c.cut ep) hS hr hagree
    (by rw [slotOf_ext hext hbj.1.exists_blk]; exact hcj)
  have p2 := prefixBelow_common (s := E.c.cut ep) hS hr hbi0'
    (by rw [slotOf_ext hext hbi0.1.exists_blk]; exact hci)
  unfold CP
  rw [← p1, p2]

/-- **Chains through honest immutable blocks carry the canonical prefix**, from
the invariant at the fixing point. -/
theorem canon_of (hA : Assm E)
    (hG : GoodCondW E es (Cons E es) W e H) (hGr : Growth E es e H) {ep : ℕ} (hep : 1 ≤ ep)
    (hFH : E.c.fix ep ≤ H) (hreach : E.c.fix ep ≤ (wF E es).now)
    (hDm : ∀ m ≤ idxE E es ep, DomAt (E := E) (es := es) (K := Cons E es) m ((wAt E es m).now - E.Δ - 1) ∧
      HonAt (E := E) (es := es) (K := Cons E es) m)
    (hKb : ∀ j ∈ E.nodes, E.online j (wAt E es (idxE E es ep)).now = true →
      Cons E es ((wAt E es (idxE E es ep)).node j).bimm)
    (hKc : ∀ j ∈ E.nodes, E.online j (wAt E es (idxE E es ep)).now = true →
      Cons E es ((wAt E es (idxE E es ep)).node j).cloc)
    {n : ℕ} (hn : n ≤ es.length) (hmn : idxE E es ep ≤ n) {i : ℕ} (hi : i ∈ E.nodes)
    (hio : E.online i (wAt E es n).now = true) {cl : ℕ}
    (hcl : Rooted (wAt E es n).st cl) (hz : ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st cl) :
    prefixBelow (chainUp (wF E es).st cl) (E.c.cut ep) = CP E es ep := by
  have hwF := wAt_ok (es := es) hA.ord es.length
  have hS := hwF.store
  obtain ⟨hmle, -, -⟩ := idxE_spec hreach
  set m := idxE E es ep with hm
  have hiom : E.online i (wAt E es m).now = true :=
    hA.crash i _ _ (now_mono (E := E) (es := es) hmn hn) hio
  obtain ⟨hcut, hpre⟩ := canon_at hA hG hGr hep hFH hreach (hDm m le_rfl).1 (hDm m le_rfl).2
    hKb hKc hi hiom
  have hw := wAt_ok (es := es) hA.ord n
  have hext := store_mono (m := es.length) (es := es) hA.ord hn
  have hwm := wAt_ok (es := es) hA.ord m
  have hpers := bimm_persist (es := es) hA.ord hA.nodup i (n := m) n hmn hn
  have hmem : ((wAt E es m).node i).bimm ∈ chainIds (wAt E es n).st cl :=
    chainIds_trans hw.store hcl hz hpers
  rw [← chainIds_ext hext hcl] at hmem
  have hbm := ((hwm.nodes i).bimm_on_cloc hwm.store).1
  have hextm := store_mono (m := es.length) (es := es) hA.ord hmle
  rw [prefixBelow_common (s := E.c.cut ep) hS (hcl.mono hext) hmem
    (by rw [slotOf_ext hextm hbm.exists_blk]; exact hcut)]
  exact hpre

/-- The immutable block and local chain of every node satisfy a predicate that
holds for every chain through the node's immutable block. -/
theorem bimm_cloc_of {n : ℕ} (hA : Assm E) (hn : n ≤ es.length) {P : ℕ → Prop}
    (hP : ∀ i ∈ E.nodes, E.online i (wAt E es n).now = true →
      ∀ cl, Rooted (wAt E es n).st cl → slotOf (wAt E es n).st cl ≤ (wAt E es n).now →
      ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st cl → P cl) :
    (∀ j ∈ E.nodes, E.online j (wAt E es n).now = true → P ((wAt E es n).node j).bimm) ∧
      (∀ j ∈ E.nodes, E.online j (wAt E es n).now = true → P ((wAt E es n).node j).cloc) := by
  have hw := wAt_ok (es := es) hA.ord n
  have hh := hon_all (es := es) hA.ord hA.exec hA.nodup hA.sane n hn
  constructor
  · intro j hj hjo
    obtain ⟨hbr, hbc⟩ := (hw.nodes j).bimm_on_cloc hw.store
    exact hP j hj hjo _ hbr
      (le_trans (slot_anc_le hw.store ((hw.nodes j).rooted _ (hw.nodes j).cloc) hbc)
        (hh.slots j _ (hw.nodes j).cloc))
      (self_mem_chainIds hw.store hbr)
  · intro j hj hjo
    exact hP j hj hjo _ ((hw.nodes j).rooted _ (hw.nodes j).cloc) (hh.slots j _ (hw.nodes j).cloc)
      ((hw.nodes j).bimm_on_cloc hw.store).2

/-- **The consistency obligation**, up to the horizon: at every point, every
current chain through an honest node's immutable block is consistent. -/
theorem cons_step (hA : Assm E)
    (hG : GoodCondW E es (Cons E es) W e H) (hGr : Growth E es e H) :
    ∀ n ≤ es.length, (wAt E es n).now ≤ H →
    (∀ m < n, DomAt (E := E) (es := es) (K := Cons E es) m ((wAt E es m).now - E.Δ - 1) ∧
      HonAt (E := E) (es := es) (K := Cons E es) m) →
    ∀ i ∈ E.nodes, E.online i (wAt E es n).now = true →
      ∀ cl, Rooted (wAt E es n).st cl → slotOf (wAt E es n).st cl ≤ (wAt E es n).now →
      ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st cl → Cons E es cl := by
  intro n
  induction n using Nat.strong_induction_on with
  | _ n ih =>
    intro hn hnH hIH i hi hio cl hcl hsl hz ep hep hs
    have hext := store_mono (m := es.length) (es := es) hA.ord hn
    have hslF : slotOf (wF E es).st cl = slotOf (wAt E es n).st cl := slotOf_ext hext hcl.exists_blk
    have hnN : (wAt E es n).now ≤ (wF E es).now := now_mono hn le_rfl
    have hfix2 := (hA.sane.fix_ok ep hep).2
    have hFn : E.c.fix ep < (wAt E es n).now := by omega
    have hreach : E.c.fix ep ≤ (wF E es).now := by omega
    obtain ⟨hmle, hnow, -⟩ := idxE_spec hreach
    set m := idxE E es ep with hm
    have hmn : m < n := by
      by_contra hge; push Not at hge
      have := now_mono (E := E) (es := es) hge hmle
      omega
    have hIHm : ∀ m' < m, DomAt (E := E) (es := es) (K := Cons E es) m' ((wAt E es m').now - E.Δ - 1) ∧
        HonAt (E := E) (es := es) (K := Cons E es) m' := fun m' hm' => hIH m' (by omega)
    obtain ⟨hKb, hKc⟩ := bimm_cloc_of hA hmle (ih m hmn hmle (by omega) hIHm)
    exact canon_of hA hG hGr hep (by omega) hreach (fun m' hm' => hIH m' (by omega)) hKb hKc hn hmn.le hi hio hcl hz

/-- **The canonical-consistency predicate meets its obligations** up to the horizon. -/
theorem cons_ok (hA : Assm E)
    (hG : GoodCondW E es (Cons E es) W e H) (hGr : Growth E es e H) : KOK E es (Cons E es) H :=
  ⟨cons_base hA, cons_step hA hG hGr⟩

/-- **`k`-deep finality over any number of epochs**, on the good event of the
consistent tree and growth, up to the horizon. -/
theorem bimm_final_epochs (hA : Assm E)
   
    (hG : GoodCondW E es (Cons E es) W e H) (hGr : Growth E es e H) {n n' : ℕ}
    (hnn : n ≤ n') (hn' : n' ≤ es.length) (hnH : (wAt E es n').now ≤ H) {i j : ℕ} (hi : i ∈ E.nodes)
    (hj : j ∈ E.nodes) (hio : E.online i (wAt E es n').now = true) (hjo : E.online j (wAt E es n').now = true) :
    ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n').st ((wAt E es n').node j).cloc :=
  bimm_final hA (cons_ok hA hG hGr) hG hnn hn' hnH hi hj hio hjo

end Cryptarchia
