import Cryptarchia.Proof.LotteryE

/-!
# The stake estimate's update on the canonical prefix

The probability layer's hypothesis `Recur` (`Prob/TSIRO.lean`) has three parts:

1. **The recursion.** Epoch `e + 1`'s canonical estimate is the specification's update
   (`infer`) of epoch `e`'s, by the occupied-slot count of the canonical chain in
   epoch `e`'s window (`cs_succ_D`).
2. **The upper bound.** Every occupied slot the chain counts was won in the lottery.
3. **The lower bound.** Honest wins in the window are counted, directly or as uncles.

This file proves part 1 from the consistency of canonical prefixes: epoch `e + 1`'s
canonical prefix, cut at epoch `e`'s cut, is epoch `e`'s canonical prefix.
-/

namespace Cryptarchia

variable {E : Env} {es : List Event}

/-- Every epoch's window ends by the next epoch's cut. -/
theorem window_le_cut {c : Config} (hc : c.Sane) {e : ℕ} :
    ∀ e', e' < e → c.epochStart e' + c.period ≤ c.cut e := by
  intro e' he'
  unfold Config.cut
  have := epochStart_mono (c := c) (show e' ≤ e - 1 by omega)
  have := hc.period_le
  omega

/-- **The canonical estimate follows the specification's update.** If epoch `e + 1`'s
canonical prefix, cut at epoch `e`'s cut, is epoch `e`'s canonical prefix, then epoch
`e + 1`'s estimate is `infer` of epoch `e`'s by the canonical chain's occupied slots in
epoch `e`'s window. -/
theorem cs_succ_D (hA : Assm E) {e : ℕ}
    (hcons : 1 ≤ e → prefixBelow (CP E es (e + 1)) (E.c.cut e) = CP E es e) :
    (CS E es (e + 1)).D = infer E.c (CS E es e).D (occupied E.c (CP E es (e + 1)) e) := by
  have hc := hA.sane
  have hwin : E.c.epochStart e + E.c.period ≤ E.c.epochStart (e + 1) := by
    rw [epochStart_succ]; have := hc.period_le; have := hc.offset_le; omega
  have hD1 : (CS E es (e + 1)).D = stakeEstimate E.c E.G
      (prefixBelow (CP E es (e + 1)) (E.c.epochStart (e + 1))) (e + 1) := by
    unfold CS; rw [if_neg (by omega)]; rfl
  rw [hD1]
  simp only [stakeEstimate]
  rw [occupied_prefix _ hwin]
  congr 1
  rcases Nat.eq_zero_or_pos e with h0 | he
  · subst h0; rfl
  · -- both estimates read the blocks below epoch `e`'s cut, where the prefixes agree
    have hce : E.c.cut e ≤ E.c.epochStart e := cut_le_start hc he
    have hce1 : E.c.cut e ≤ E.c.epochStart (e + 1) := le_trans hce (epochStart_mono (by omega))
    have hDe : (CS E es e).D = stakeEstimate E.c E.G (prefixBelow (CP E es e) (E.c.epochStart e)) e := by
      unfold CS; rw [if_neg (by omega)]; rfl
    rw [hDe, ← stakeEstimate_prefix (G := E.G) _ e (window_le_cut hc),
      ← stakeEstimate_prefix (G := E.G) (prefixBelow (CP E es e) _) e (window_le_cut hc),
      prefixBelow_prefixBelow _ hce1, prefixBelow_prefixBelow _ hce, hcons he]
    unfold CP
    rw [prefixBelow_prefixBelow _ le_rfl]

variable {W : ℕ → ℕ} {e : ℕ → ℕ} {H : ℕ}

/-- **Consistent canonical prefixes.** On the good event up to epoch `ep + 1`'s fixing
time, with an honest node online then, epoch `ep + 1`'s canonical prefix, cut at epoch
`ep`'s cut, is epoch `ep`'s canonical prefix. -/
theorem cp_consistent (hA : Assm E) (hG : GoodCondW E es (Cons E es) W e H) (hGr : Growth E es e H)
    (hHN : H ≤ (wF E es).now) {ep : ℕ} (hep : 1 ≤ ep) (hfix : E.c.fix (ep + 1) ≤ H)
    (hon : ∃ j ∈ E.nodes, E.online j (wAt E es (idxE E es (ep + 1))).now = true) :
    prefixBelow (CP E es (ep + 1)) (E.c.cut ep) = CP E es ep := by
  classical
  have hreach : E.c.fix (ep + 1) ≤ (wF E es).now := by omega
  obtain ⟨hmle, hnow, -⟩ := idxE_spec hreach
  set m := idxE E es (ep + 1) with hm
  have hmH : (wAt E es m).now ≤ H := by rw [hnow]; exact hfix
  have hK := cons_ok hA hG hGr
  have hDm : ∀ m' ≤ m, DomAt (E := E) (es := es) (K := Cons E es) m' ((wAt E es m').now - E.Δ - 1) ∧
      HonAt (E := E) (es := es) (K := Cons E es) m' := fun m' hm' =>
    main hA hK hG m' (by omega) (le_trans (now_mono (E := E) (es := es) hm' hmle) hmH)
  obtain ⟨hKb, -⟩ := bimm_cloc_of hA hmle
    (hK.step m hmle hmH (fun m' hm' => hDm m' hm'.le))
  -- the reference node is online
  have hi0 : i0 E es (ep + 1) ∈ E.nodes ∧ E.online (i0 E es (ep + 1)) (wAt E es m).now = true := by
    unfold i0; rw [dif_pos hon]; exact Classical.choose_spec hon
  set b := ((wAt E es m).node (i0 E es (ep + 1))).bimm with hb
  have hKbb : Cons E es b := hKb _ hi0.1 hi0.2
  have hcut := bimm_past_cut hA hG hGr (by omega : 1 ≤ ep + 1) hfix hreach (hDm m le_rfl).1 (hDm m le_rfl).2
    hi0.1 hi0.2 hKbb
  -- its slot is past epoch `ep`'s start
  have hw := wAt_ok (es := es) hA.ord m
  have hbr : Rooted (wAt E es m).st b := ((hw.nodes _).bimm_on_cloc hw.store).1
  have hext := store_mono (m := es.length) (es := es) hA.ord hmle
  have hslF : slotOf (wF E es).st b = slotOf (wAt E es m).st b := slotOf_ext hext hbr.exists_blk
  have hcut' : E.c.cut (ep + 1) ≤ slotOf (wAt E es m).st b + 1 := hcut
  have hstart : E.c.epochStart ep ≤ slotOf (wF E es).st b := by
    rw [hslF]
    have : E.c.cut (ep + 1) = E.c.epochStart ep + E.c.nonceOffset := by simp [Config.cut]
    have := hA.sane.offset_pos
    omega
  have hcons := hKbb ep hep hstart
  have hcc : E.c.cut ep ≤ E.c.cut (ep + 1) := by
    unfold Config.cut
    have := epochStart_mono (c := E.c) (show ep - 1 ≤ ep + 1 - 1 by omega)
    omega
  show prefixBelow (prefixBelow (chainUp (wF E es).st b) (E.c.cut (ep + 1))) (E.c.cut ep) = CP E es ep
  rw [prefixBelow_prefixBelow _ hcc, hcons]

end Cryptarchia
