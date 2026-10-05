import Cryptarchia.Proof.Canon
import Cryptarchia.Proof.Lottery

/-!
# The lottery string over many epochs

Each slot's lottery runs under the **canonical state** of its epoch
(`CS`: the genesis state for epoch 0, otherwise the state derived on the
canonical prefix `CP E.c.fix e`). Given the settlement invariant up to a horizon `H'`
that covers the fixing point of every epoch starting by `Hs`:

* every honest node leads under the canonical state at every tick up to `Hs`
  (`node_state`), because its local chain carries the canonical prefix;
* every honest block with slot up to `Hs` is consistent (`hon_cons_upto`);
* every adversarial block of the consistent tree is validated under the
  canonical state (`advStatesOK_E`, at every slot: consistency is definitional).
-/

namespace Cryptarchia

open Settle

variable (E : Env) (es : List Event)

/-- **The canonical epoch state of epoch `e`.** -/
noncomputable def CS (e : ℕ) : EpochState :=
  if e = 0 then es0 E else epochState E.c E.L E.O E.G (CP E es e) e

/-- The state each slot's lottery runs under. -/
noncomputable def σE (t : ℕ) : EpochState := CS E es (E.c.epochOf t)

variable {E es}

theorem prefixBelow_snoc (C : List Block) {B : Block} {s : ℕ} (hB : B.hdr.id ≠ genesisId)
    (hs : s ≤ B.hdr.slot) : prefixBelow (C ++ [B]) s = prefixBelow C s := by
  unfold prefixBelow
  rw [List.filter_append]
  simp [hB]; omega

theorem epochStart_epochOf_le (c : Config) (t : ℕ) : c.epochStart (c.epochOf t) ≤ t := by
  unfold Config.epochStart Config.epochOf; exact Nat.div_mul_le_self _ _

/-- An epoch state derived on a chain with the canonical prefix is canonical. -/
theorem state_of_prefix (hA : Assm E) {C : List Block} {e : ℕ} (he : 1 ≤ e)
    (hC : prefixBelow C (E.c.cut e) = CP E es e) : epochState E.c E.L E.O E.G C e = CS E es e := by
  unfold CS
  rw [if_neg (by omega), ← epochState_cut hA.sane C he, hC]

variable {W : ℕ → ℕ} {e : ℕ → ℕ} {H' : ℕ}

/-- **Honest chains carry the canonical prefix** of every epoch fixed within the
horizon of the invariant. -/
theorem canon_node (hA : Assm E)
   
    (hG : GoodCondW E es (Cons E es) W e H') (hGr : Growth E es e H') (hH'N : H' ≤ (wF E es).now)
    {ep : ℕ} (hep : 1 ≤ ep) (hfixH : E.c.fix ep ≤ H') {n : ℕ} (hn : n ≤ es.length) (hFn : E.c.fix ep ≤ (wAt E es n).now)
    {i : ℕ} (hi : i ∈ E.nodes) (hio : E.online i (wAt E es n).now = true) {cl : ℕ}
    (hcl : Rooted (wAt E es n).st cl)
    (hz : ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st cl) :
    prefixBelow (chainUp (wF E es).st cl) (E.c.cut ep) = CP E es ep := by
  have hK := cons_ok hA hG hGr
  have hreach : E.c.fix ep ≤ (wF E es).now := by omega
  obtain ⟨hmle, hnow, -⟩ := idxE_spec (e := ep) hreach
  have hDm : ∀ m ≤ idxE E es ep, DomAt (E := E) (es := es) (K := Cons E es) m
      ((wAt E es m).now - E.Δ - 1) ∧ HonAt (E := E) (es := es) (K := Cons E es) m := fun m hm =>
    main hA hK hG m (by omega) (le_trans (now_mono (E := E) (es := es) hm hmle) (by omega))
  obtain ⟨hKb, hKc⟩ := bimm_cloc_of hA hmle
    (cons_step hA hG hGr _ hmle (by omega) (fun m hm => hDm m hm.le))
  exact canon_of hA hG hGr hep hfixH hreach hDm hKb hKc hn (idxE_le hn hFn) hi hio hcl hz

/-- **Every honest leader runs the canonical lottery** at every tick up to `Hs`. -/
theorem node_state (hA : Assm E)
   
    (hG : GoodCondW E es (Cons E es) W e H') (hGr : Growth E es e H') (hH'N : H' ≤ (wF E es).now)
    {Hs : ℕ} (hcov : ∀ ep, 1 ≤ ep → E.c.epochStart ep ≤ Hs → E.c.fix ep ≤ H')
    {n : ℕ} (hn : n ≤ es.length) (htH : (wAt E es n).now + 1 ≤ Hs) {j : ℕ} (hj : j ∈ E.nodes)
    (hjo : E.online j ((wAt E es n).now + 1) = true) :
    epochState E.c E.L E.O E.G (chainUp (wAt E es n).st ((wAt E es n).node j).cloc)
      (E.c.epochOf ((wAt E es n).now + 1)) = σE E es ((wAt E es n).now + 1) := by
  have hw := wAt_ok (es := es) hA.ord n
  have hcr := (hw.nodes j).rooted _ (hw.nodes j).cloc
  unfold σE
  set t := (wAt E es n).now + 1
  rcases Nat.eq_zero_or_pos (E.c.epochOf t) with h0 | h1
  · rw [h0, epochState_es0 hw.store (store_genesis hA.ord n) hcr]; simp [CS]
  · have hext := store_mono (m := es.length) (es := es) hA.ord hn
    have hst := epochStart_epochOf_le E.c t
    have hfix2 := (hA.sane.fix_ok _ h1).2
    rw [← chainUp_ext hext hcr]
    apply state_of_prefix hA h1
    exact canon_node hA hG hGr hH'N h1 (hcov _ h1 (by omega)) hn (by omega) hj
      (hA.crash j _ _ (Nat.le_succ _) hjo) hcr ((hw.nodes j).bimm_on_cloc hw.store).2

/-- **Honest blocks are consistent**, up to `Hs`. -/
theorem hon_cons_upto (hA : Assm E)
   
    (hG : GoodCondW E es (Cons E es) W e H') (hGr : Growth E es e H') (hH'N : H' ≤ (wF E es).now)
    {Hs : ℕ} (hcov : ∀ ep, 1 ≤ ep → E.c.epochStart ep ≤ Hs → E.c.fix ep ≤ H') :
    ∀ n ≤ es.length, ∀ b B, (wAt E es n).st b = some B → IsHon B → B.hdr.slot ≤ Hs → Cons E es b := by
  have hwF := wAt_ok (es := es) hA.ord es.length
  have hS := hwF.store
  intro n
  induction n with
  | zero =>
    intro _ b B hb hBh _
    rw [wAt_zero] at hb
    simp only [World.init] at hb
    split at hb
    · cases hb; obtain ⟨j, hj⟩ := hBh; simp [genesisBlock] at hj
    · simp at hb
  | succ n ih =>
    intro hn b B hb hBh hBs
    have hnl : n < es.length := by omega
    by_cases hold : (wAt E es n).st b = none
    · have hwn := wAt_ok (es := es) hA.ord n
      have hstep := step_hon hA.ord hA.exec hA.nodup hwn
        (hon_all (es := es) hA.ord hA.exec hA.nodup hA.sane n hnl.le) es[n] hA.sane
      rw [wAt_succ E es hnl] at hb
      have hsl := hstep.2 b B hb hold hBh
      cases hev : es[n] with
      | tick =>
        rw [hev] at hb
        obtain ⟨-, j, hj, hpj⟩ := tick_new hA.ord hA.nodup hwn b B hb hold
        have hpar := hpj.1
        have hb1 : (wAt E es (n + 1)).st b = some B := by rw [wAt_succ E es hnl, hev]; exact hb
        have hext1 := store_mono (m := es.length) (es := es) hA.ord hn
        have hbF := hext1 b B hb1
        have hbr : Rooted (wAt E es (n + 1)).st b :=
          ((hon_all (es := es) hA.ord hA.exec hA.nodup hA.sane (n + 1) hn).hon b B hb1 hBh).1
        have hb0 : b ≠ genesisId := by
          intro h0; subst h0
          have := store_genesis (E := E) (es := es) hA.ord es.length
          rw [hbF] at this; cases this; obtain ⟨j', hj'⟩ := hBh; simp [genesisBlock] at hj'
        obtain ⟨B', hB', hpr, hps⟩ := (hbr.mono hext1).inv hb0
        rw [hbF] at hB'; cases hB'
        have hid := hS.idOK _ _ hbF
        intro ep hep hs
        rw [slotOf_eq hbF] at hs
        rw [chainUp_step hbF hb0 hpr hps,
          prefixBelow_snoc _ (by rw [hid]; exact hb0) (le_trans (cut_le_start hA.sane hep) hs), hpar]
        have hcr := (hwn.nodes j).rooted _ (hwn.nodes j).cloc
        have hfix2 := (hA.sane.fix_ok ep hep).2
        exact canon_node hA hG hGr hH'N hep (hcov ep hep (by omega)) hnl.le (by omega) hj
          (hA.crash j _ _ (Nat.le_succ _) hpj.2) hcr ((hwn.nodes j).bimm_on_cloc hwn.store).2
      | deliver i x =>
        rw [hev] at hb; simp only [World.step] at hb
        split at hb <;> rw [hold] at hb <;> cases hb
      | create C =>
        rw [hev] at hb; simp only [World.step] at hb
        split at hb
        · rename_i hc
          simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
          by_cases hbC : b = C.hdr.id
          · subst hbC
            have : B = C := by simp [World.add] at hb; exact hb.symm
            obtain ⟨j, hj⟩ := hBh; rw [this, hc.1] at hj; cases hj
          · have : (World.add (wAt E es n) C).st b = (wAt E es n).st b := by simp [World.add, hbC]
            rw [this, hold] at hb; cases hb
        · rw [hold] at hb; cases hb
    · obtain ⟨B', hB'⟩ := Option.ne_none_iff_exists'.1 hold
      have : B' = B := by
        have := store_mono (E := E) (es := es) hA.ord (Nat.le_succ n) b B' hB'
        rw [hb] at this; exact (Option.some_inj.1 this).symm
      rw [← this] at hBh hBs
      exact ih (by omega) b B' hB' hBh hBs

/-- **Adversarial blocks of the consistent tree run the canonical lottery.** -/
theorem advStatesOK_E (hA : Assm E) : AdvStatesOK E es (Cons E es) (σE E es) := by
  intro v hv B hB _
  have hwF := wAt_ok (es := es) hA.ord es.length
  have hS := hwF.store
  obtain ⟨hvu, ⟨hr, hsN, -⟩⟩ := mem_stree.1 hv
  have hKv := (mem_FTused.1 hvu).2
  have hpr : Rooted (wF E es).st B.hdr.parent := by
    have := hr.parent_rooted hS.genSelf; rwa [parentOf_eq hB] at this
  unfold σE
  rcases Nat.eq_zero_or_pos (E.c.epochOf B.hdr.slot) with h0 | h1
  · rw [h0, epochState_es0 hS (store_genesis hA.ord es.length) hpr]; simp [CS]
  · apply state_of_prefix hA h1
    have hv0 : v ≠ genesisId := by
      intro h0; subst h0
      have hg := store_genesis (E := E) (es := es) hA.ord es.length
      rw [hB] at hg; cases hg
      simp [genesisBlock, Config.epochOf] at h1
    obtain ⟨B', hB', hpr', hps⟩ := hr.inv hv0
    rw [hB] at hB'; cases hB'
    have hs : E.c.epochStart (E.c.epochOf B.hdr.slot) ≤ slotOf (wF E es).st v := by
      rw [slotOf_eq hB]; exact epochStart_epochOf_le E.c _
    have := hKv _ h1 hs
    rw [chainUp_step hB hv0 hpr' hps,
      prefixBelow_snoc _ (by rw [hS.idOK _ _ hB]; exact hv0)
        (le_trans (cut_le_start hA.sane h1) (by rw [slotOf_eq hB] at hs; exact hs))] at this
    exact this

/-- **Weak domination by the multi-epoch lottery string up to `Hs`.** -/
theorem advLeW_lotE (hA : Assm E)
   
    (hG : GoodCondW E es (Cons E es) W e H') (hGr : Growth E es e H') (hH'N : H' ≤ (wF E es).now)
    {Hs : ℕ} (hcov : ∀ ep, 1 ≤ ep → E.c.epochStart ep ≤ Hs → E.c.fix ep ≤ H') (hHs : Hs ≤ (wF E es).now) :
    AdvLeW Hs (WS E es (Cons E es)) (lotStrS E (σE E es) (lateAt E es)) :=
  advLeW_upto hA hA.stake (fun n hn _ htH j hj hjo => node_state hA hG hGr hH'N hcov hn.le htH hj hjo)
    (fun b B hb hBh hBs => hon_cons_upto hA hG hGr hH'N hcov es.length le_rfl b B hb hBh hBs)
    (advStatesOK_E hA) hHs

end Cryptarchia
