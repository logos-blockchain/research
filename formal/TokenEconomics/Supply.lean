import Mantle.Block
import TokenEconomics.Pools

/-!
# No token is ever minted

Block Construction, *Block Execution*, with Block Rewards and the Cryptoeconomics Overview:
the steps of a block, in order (`executeBlock`):

1. in the first block of an epoch, the Blend reward notes are paid from
   `blend_rewards_pending`, what they do not use returning to the rewards pool, the withdrawn
   SDP declarations are removed and their notes released, and the proof of work pool is
   refilled with the share of the fees diverted during the previous epoch;
2. the due channel withdrawals are released;
3. the Mantle Transactions are executed, collecting the mandatory fees and the tips;
4. the pooled fees, net of the share diverted to the proof of work pool, enter the window, the
   reserve releases and the pool pays the block reward, the leader receives one note worth 40%
   of the reward plus the tips under its `reward_key`, and the Blend share waits in
   `blend_rewards_pending`;
5. every note set records its commitment root.

The tokens of a block state (`total`) are those of its notes (unspent, of every note set),
of the notes withdrawn declarations will release, of the proof of work pool and of the fees
diverted to it, of the reserve, of the rewards pool and of the pending Blend share.

**`executeBlock_total`**: executing a block never increases the total; **`executeChain_total`**:
so the total of any chain of blocks never exceeds that of Genesis, the maximum supply
`S_cap` fixed at Genesis. **`executeChain_tokenValue`**: from a Genesis of at most `10¹⁹` units
of `10⁻⁹` LGO, every unspent note and every stock stays at most `10¹⁹ < 2^64`, so every token
value fits a `TokenValue` (Mantle, *Arithmetic*). The leader reward, the Blend reward and the release of the reserve
move tokens between these stocks; the only way the total decreases is notes that can never be
spent, such as two leader rewards of the same value under the same `reward_key` (one
commitment, so one spendable note).

Hypotheses: the share diverted to the proof of work pool is at most the fees
(`POW_SHARE ≤ SHARE_DEN`), and the capacity `Cap` of the note sets.
-/

namespace TokenEconomics

open Mantle Classical

noncomputable section

/-- The state a block is executed against: the Mantle state, the reward state, and the fees
diverted to the proof of work pool during the current epoch. -/
structure BlockState where
  ledger : Mantle.State
  rewards : RewardState
  powPending : ℕ

/-- The Blend rewards of an epoch: the Blend reward, and one note per rewarded `zk_id`. -/
structure ServiceRewards where
  blendReward : ℕ
  notes : List Note

/-- What a block brings. -/
structure BlockInputs where
  env : Env
  epochStart : Bool
  service : Option ServiceRewards
  txs : List SignedMantleTx
  stake : ℕ
  rewardKey : Fr

/-- `POW_SHARE / SHARE_DEN`, the share of the collected fees diverted to the proof of work
pool. -/
structure PowShare where
  num : ℕ
  den : ℕ
  le : num ≤ den

/-- The Mantle Transactions of a block, in order: the state, the collected fees and the tips. -/
def applyTxs (P : Prims) (E : Env) : Mantle.State → List SignedMantleTx → Option (Mantle.State × ℕ × ℕ)
  | st, [] => some (st, 0, 0)
  | st, tx :: txs => do
    let (st1, f, t) ← applyTx P E st tx
    let (st2, F, T) ← applyTxs P E st1 txs
    pure (st2, f + F, t + T)

/-- Step 1: the Blend reward notes of the epoch, paid from `blend_rewards_pending`. -/
def payService (P : Prims) (st : Mantle.State) (r : RewardState) :
    Option ServiceRewards → Option (Mantle.State × RewardState)
  | none => some (st, r)
  | some sr => do
    let paid := (sr.notes.map (·.value)).sum
    ensure (paid ≤ sr.blendReward ∧ sr.blendReward ≤ r.pending)
    pure (st.setSet LEDGER_SET ((st.sets LEDGER_SET).executeAdding (sr.notes.map (noteCm P.H))),
      payBlend r sr.blendReward paid)

/-- The leader reward note of a block. -/
def leaderNote (R tips : ℕ) (rewardKey : Fr) : Note := ⟨leaderShare R + tips, 0, rewardKey, 0, 0⟩

/-- **Block Execution.** -/
def executeBlock (P : Prims) (pow : PowShare) (b : BlockState) (inp : BlockInputs) :
    Option BlockState := do
  -- 1. service rewards, SDP Epoch Finalization, proof of work refill
  let (st1, r1) ← payService P b.ledger b.rewards inp.service
  let st2 := if inp.epochStart then finalizeDeclarations st1 inp.env.currentEpoch else st1
  let st3 := if inp.epochStart then st2.withPow (st2.powRewardPool + b.powPending) st2.powNullifiers
    else st2
  let pp := if inp.epochStart then 0 else b.powPending
  -- 2. channel withdrawals
  let st4 := releaseWithdrawals st3 inp.env.blockSlot
  -- 3. transactions
  let (st5, fees, tips) ← applyTxs P inp.env st4 inp.txs
  -- 4. leader reward and reward state
  let diverted := fees * pow.num / pow.den
  let (r2, R) := rewardStep r1 inp.stake (fees - diverted)
  let st6 := st5.setSet LEDGER_SET ((st5.sets LEDGER_SET).executeAdding
    [noteCm P.H (leaderNote R tips inp.rewardKey)])
  -- 5. record the roots
  pure ⟨recordCmRoots P.H st6, r2, pp + diverted⟩

/-- The tokens of a block state. -/
def total (H : Hash) (b : BlockState) : ℕ :=
  value H b.ledger + b.powPending + b.rewards.reserve + b.rewards.pool + b.rewards.pending

/-! ## Transactions -/

theorem applyTx_grows {P : Prims} {E : Env} {st st' : Mantle.State} {stx : SignedMantleTx}
    {fee tip : ℕ} (h : applyTx P E st stx = some (st', fee, tip)) : Grows st st' := by
  simp only [applyTx, ensure_eq_some, option_bind_eq_some, option_pure_eq, exists_const,
    Option.some.injEq, Prod.mk.injEq] at h
  obtain ⟨-, ⟨st1, bal, gas⟩, hops, f, -, -, rfl, -, -⟩ := h
  have G0 : Grows st st.clearBuffers := ⟨le_rfl, fun i _ => List.prefix_refl _⟩
  exact G0.trans (applyOps_grows _ _ _ _ _ _ hops)

theorem applyTxs_spec {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {E : Env} (txs : List SignedMantleTx) :
    ∀ (st st' : Mantle.State) (fees tips : ℕ), Inv P.H st →
      applyTxs P E st txs = some (st', fees, tips) → Cap st' →
      Inv P.H st' ∧ Grows st st' ∧ value P.H st' + fees + tips ≤ value P.H st := by
  induction txs with
  | nil =>
    intro st st' fees tips I h _
    simp only [applyTxs, Option.some.injEq, Prod.mk.injEq] at h
    obtain ⟨rfl, rfl, rfl⟩ := h
    exact ⟨I, Grows.refl _, le_rfl⟩
  | cons tx txs ih =>
    intro st st' fees tips I h hcap
    simp only [applyTxs, option_bind_eq_some, option_pure_eq, Option.some.injEq,
      Prod.mk.injEq] at h
    obtain ⟨⟨st1, f, t⟩, h1, ⟨st2, F, T⟩, h2, rfl, rfl, rfl⟩ := h
    have G2 : Grows st1 st2 := by
      clear ih h1 I hcap
      induction txs generalizing st1 F T with
      | nil =>
        simp only [applyTxs, Option.some.injEq, Prod.mk.injEq] at h2
        rw [h2.1]; exact Grows.refl _
      | cons tx' txs' ih' =>
        simp only [applyTxs, option_bind_eq_some, option_pure_eq, Option.some.injEq,
          Prod.mk.injEq] at h2
        obtain ⟨⟨s1, f1, t1⟩, h21, ⟨s2, F2, T2⟩, h22, rfl, rfl, rfl⟩ := h2
        exact (applyTx_grows h21).trans (ih' s1 F2 T2 h22)
    obtain ⟨I1, V1⟩ := applyTx_value I h1 (hcap.of_grows G2)
    obtain ⟨I2, G2', V2⟩ := ih st1 st2 F T I1 h2 hcap
    refine ⟨I2, (applyTx_grows h1).trans G2', ?_⟩
    dsimp only at V1 V2 ⊢
    omega

/-! ## The steps of a block -/

theorem listValue_notes (H : Hash) (notes : List Note) :
    listValue H (notes.map (noteCm H)) = (notes.map (·.value)).sum := by
  simp only [listValue, List.map_map]
  congr 1
  apply List.map_congr_left
  intro n _
  simp [cmValue_noteCm]

/-- The tokens of the reward state. -/
def RewardState.stock (r : RewardState) : ℕ := r.reserve + r.pool + r.pending

theorem payService_spec {P : Prims} {st st1 : Mantle.State} {r r1 : RewardState}
    {sv : Option ServiceRewards} (I : Inv P.H st) (IP : PoolInv r)
    (h : payService P st r sv = some (st1, r1)) :
    Inv P.H st1 ∧ PoolInv r1 ∧ Grows st st1 ∧ value P.H st1 + r1.stock ≤ value P.H st + r.stock := by
  cases sv with
  | none =>
    simp only [payService, Option.some.injEq, Prod.mk.injEq] at h
    obtain ⟨rfl, rfl⟩ := h
    exact ⟨I, IP, Grows.refl _, le_rfl⟩
  | some sr =>
    simp only [payService, ensure_eq_some, option_bind_eq_some, option_pure_eq, exists_const,
      Option.some.injEq, Prod.mk.injEq] at h
    obtain ⟨⟨hpaid, hpend⟩, rfl, rfl⟩ := h
    have hi := ledger_lt I
    obtain ⟨I1, G1⟩ := I.setSet hi ((I.sets _ hi).add (sr.notes.map (noteCm P.H))) (by simp)
    refine ⟨I1, poolInv_payBlend IP _ _, G1, ?_⟩
    have key := supply_append_le (H := P.H) (st.sets LEDGER_SET).cms (sr.notes.map (noteCm P.H))
      (st.sets LEDGER_SET).nullifiers
    have v := setsValue_setSet (H := P.H) hi
      ((st.sets LEDGER_SET).executeAdding (sr.notes.map (noteCm P.H)))
    rw [listValue_notes] at key
    simp only [NoteSet.supply, NoteSet.executeAdding_cms, NoteSet.executeAdding_nullifiers] at v
    simp only [value, inflight_setSet, setSet_pool, RewardState.stock, payBlend]
    omega

theorem releaseOne_grows (slot : Slot) (acc : Mantle.State × List (Slot × ℕ × List Fr × List Fr))
    (w : Slot × ℕ × List Fr × List Fr) : Grows acc.1 (releaseOne slot acc w).1 := by
  obtain ⟨st, pending⟩ := acc
  obtain ⟨due, j, ins, outs⟩ := w
  simp only [releaseOne]
  split_ifs
  · exact Grows.refl _
  · exact (Grows.setSet fun _ => by simp).trans (Grows.setSet fun _ => by
      by_cases hj : LEDGER_SET = j
      · rw [← hj]; simp
      · simp [setSet_sets_of_ne _ hj])
  · exact Grows.refl _

theorem releaseWithdrawals_grows (st : Mantle.State) (slot : Slot) :
    Grows st (releaseWithdrawals st slot) := by
  have : ∀ (l : List (Slot × ℕ × List Fr × List Fr)) acc,
      Grows acc.1 (l.foldl (releaseOne slot) acc).1 := by
    intro l
    induction l with
    | nil => intro acc; exact Grows.refl _
    | cons w l ih => intro acc; exact (releaseOne_grows slot acc w).trans (ih _)
  exact (this st.pendingWithdrawals (st, [])).trans (Grows.of_sets rfl rfl)

theorem finalizeDeclarations_grows (st : Mantle.State) (epoch : Epoch) :
    Grows st (finalizeDeclarations st epoch) := by
  simp only [finalizeDeclarations, foldl_add_eq]
  exact (Grows.setSet fun _ => by simp).trans (Grows.of_sets rfl rfl)

theorem recordCmRoots_grows (H : Hash) (st : Mantle.State) : Grows st (recordCmRoots H st) :=
  ⟨le_rfl, fun i hi => by
    show (st.sets i).cms <+: ((recordCmRoots H st).sets i).cms
    rw [recordCmRoots_sets, ite_eq_left hi]
    simp⟩

theorem Cap.of_recordCmRoots {H : Hash} {st : Mantle.State} (h : Cap (recordCmRoots H st)) :
    Cap st := by
  intro i hi
  have := h i hi
  rw [recordCmRoots_sets, ite_eq_left hi] at this
  simpa using this

/-- **Executing a block never increases the tokens.** -/
theorem executeBlock_total {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {pow : PowShare} {b b' : BlockState} {inp : BlockInputs}
    (I : Inv P.H b.ledger) (IP : PoolInv b.rewards) (h : executeBlock P pow b inp = some b')
    (hcap : Cap b'.ledger) :
    Inv P.H b'.ledger ∧ PoolInv b'.rewards ∧ Grows b.ledger b'.ledger ∧
      total P.H b' ≤ total P.H b := by
  simp only [executeBlock, option_bind_eq_some, option_pure_eq, Option.some.injEq] at h
  obtain ⟨⟨st1, r1⟩, h1, ⟨st5, fees, tips⟩, h5, rfl⟩ := h
  -- step 1
  obtain ⟨I1, IP1, G1, V1⟩ := payService_spec I IP h1
  set st2 := if inp.epochStart then finalizeDeclarations st1 inp.env.currentEpoch else st1
    with hst2
  have I2 : Inv P.H st2 ∧ Grows st1 st2 ∧ value P.H st2 ≤ value P.H st1 := by
    rw [hst2]; split_ifs
    · exact ⟨(finalizeDeclarations_value I1 _).1, finalizeDeclarations_grows _ _,
        (finalizeDeclarations_value I1 _).2⟩
    · exact ⟨I1, Grows.refl _, le_rfl⟩
  set st3 := if inp.epochStart then st2.withPow (st2.powRewardPool + b.powPending)
    st2.powNullifiers else st2 with hst3
  set pp := if inp.epochStart then 0 else b.powPending with hpp
  have I3 : Inv P.H st3 ∧ Grows st2 st3 ∧ value P.H st3 + pp = value P.H st2 + b.powPending := by
    rw [hst3, hpp]; split_ifs
    · refine ⟨⟨I2.1.two_le, I2.1.sets, I2.1.chan, I2.1.declNodup, I2.1.declNote,
        I2.1.declOutputs, I2.1.pending⟩, Grows.of_sets rfl rfl, ?_⟩
      simp only [value, setsValue_withPow, inflight_withPow, State.withPow_pool]
      omega
    · exact ⟨I2.1, Grows.refl _, rfl⟩
  -- step 2
  obtain ⟨I4, V4⟩ := releaseWithdrawals_value I3.1 inp.env.blockSlot
  -- step 5 then 4: the capacity of the last states
  have hcap6 := Cap.of_recordCmRoots hcap
  have G6 : Grows st5 (st5.setSet LEDGER_SET ((st5.sets LEDGER_SET).executeAdding
      [noteCm P.H (leaderNote (rewardStep r1 inp.stake (fees - fees * pow.num / pow.den)).2 tips
        inp.rewardKey)])) := Grows.setSet fun _ => by simp
  -- step 3
  obtain ⟨I5, G5, V5⟩ := applyTxs_spec inp.txs _ _ _ _ I4 h5 (hcap6.of_grows G6)
  -- step 4
  have hi := ledger_lt I5
  obtain ⟨I6, -⟩ := I5.setSet hi ((I5.sets _ hi).add [noteCm P.H (leaderNote
    (rewardStep r1 inp.stake (fees - fees * pow.num / pow.den)).2 tips inp.rewardKey)]) (by simp)
  have hv6 : value P.H (st5.setSet LEDGER_SET ((st5.sets LEDGER_SET).executeAdding
      [noteCm P.H (leaderNote (rewardStep r1 inp.stake (fees - fees * pow.num / pow.den)).2 tips
        inp.rewardKey)])) ≤ value P.H st5 +
      (leaderShare (rewardStep r1 inp.stake (fees - fees * pow.num / pow.den)).2 + tips) := by
    have key := supply_append_le (H := P.H) (st5.sets LEDGER_SET).cms
      [noteCm P.H (leaderNote (rewardStep r1 inp.stake (fees - fees * pow.num / pow.den)).2 tips
        inp.rewardKey)] (st5.sets LEDGER_SET).nullifiers
    have v6 := setsValue_setSet (H := P.H) hi
      ((st5.sets LEDGER_SET).executeAdding [noteCm P.H (leaderNote
        (rewardStep r1 inp.stake (fees - fees * pow.num / pow.den)).2 tips inp.rewardKey)])
    have hlv : listValue P.H [noteCm P.H (leaderNote
        (rewardStep r1 inp.stake (fees - fees * pow.num / pow.den)).2 tips inp.rewardKey)] =
        leaderShare (rewardStep r1 inp.stake (fees - fees * pow.num / pow.den)).2 + tips := by
      simp [listValue, cmValue_noteCm, leaderNote]
    simp only [NoteSet.supply, NoteSet.executeAdding_cms, NoteSet.executeAdding_nullifiers] at v6
    simp only [value, inflight_setSet, setSet_pool]
    omega
  have cons := rewardStep_conserves IP1 inp.stake (fees - fees * pow.num / pow.den)
  have hdiv : fees * pow.num / pow.den ≤ fees := by
    rcases Nat.eq_zero_or_pos pow.den with h0 | h0
    · simp [h0]
    · exact Nat.div_le_of_le_mul (by rw [Nat.mul_comm pow.den]; exact Nat.mul_le_mul_left _ pow.le)
  -- step 5
  obtain ⟨I7, V7, -⟩ := recordCmRoots_value (H := P.H) I6
  refine ⟨I7, poolInv_rewardStep IP1 _ _, ?_, ?_⟩
  · exact G1.trans (I2.2.1.trans (I3.2.1.trans ((releaseWithdrawals_grows _ _).trans
      (G5.trans (G6.trans (recordCmRoots_grows _ _))))))
  · simp only [total, RewardState.stock] at V1 cons ⊢
    rw [V7]
    have e3 := I3.2.2
    have e2 := I2.2.2
    omega

/-- A chain of blocks. -/
def executeChain (P : Prims) (pow : PowShare) : BlockState → List BlockInputs → Option BlockState
  | b, [] => some b
  | b, inp :: rest => do
    let b1 ← executeBlock P pow b inp
    executeChain P pow b1 rest

theorem applyTxs_grows {P : Prims} {E : Env} (txs : List SignedMantleTx) :
    ∀ (st st' : Mantle.State) (f t : ℕ), applyTxs P E st txs = some (st', f, t) →
      Grows st st' := by
  induction txs with
  | nil =>
    intro st st' f t h
    simp only [applyTxs, Option.some.injEq, Prod.mk.injEq] at h
    rw [← h.1]; exact Grows.refl _
  | cons tx txs ih =>
    intro st st' f t h
    simp only [applyTxs, option_bind_eq_some, option_pure_eq, Option.some.injEq,
      Prod.mk.injEq] at h
    obtain ⟨⟨s1, f1, t1⟩, h1, ⟨s2, F2, T2⟩, h2, rfl, rfl, rfl⟩ := h
    exact (applyTx_grows h1).trans (ih s1 s2 F2 T2 h2)

theorem payService_grows {P : Prims} {st st1 : Mantle.State} {r r1 : RewardState}
    {sv : Option ServiceRewards} (h : payService P st r sv = some (st1, r1)) : Grows st st1 := by
  cases sv with
  | none =>
    simp only [payService, Option.some.injEq, Prod.mk.injEq] at h
    rw [← h.1]; exact Grows.refl _
  | some sr =>
    simp only [payService, ensure_eq_some, option_bind_eq_some, option_pure_eq, exists_const,
      Option.some.injEq, Prod.mk.injEq] at h
    rw [← h.2.1]; exact Grows.setSet fun _ => by simp

/-- Executing a block only appends commitments to the note sets. -/
theorem executeBlock_grows {P : Prims} {pow : PowShare} {b b' : BlockState} {inp : BlockInputs}
    (h : executeBlock P pow b inp = some b') : Grows b.ledger b'.ledger := by
  simp only [executeBlock, option_bind_eq_some, option_pure_eq, Option.some.injEq] at h
  obtain ⟨⟨st1, r1⟩, h1, ⟨st5, fees, tips⟩, h5, rfl⟩ := h
  refine (payService_grows h1).trans (Grows.trans ?_ ((applyTxs_grows _ _ _ _ _ h5).trans
    ((Grows.setSet fun _ => by simp).trans (recordCmRoots_grows _ _))))
  refine Grows.trans ?_ (releaseWithdrawals_grows _ _)
  dsimp only
  split_ifs
  · exact (finalizeDeclarations_grows _ _).trans (Grows.of_sets rfl rfl)
  · exact Grows.refl _

/-- **No token is ever minted**: along any chain of blocks, the tokens never exceed those of
the first state, the maximum supply fixed at Genesis. -/
theorem executeChain_total {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound] {pow : PowShare} (blocks : List BlockInputs) :
    ∀ (b b' : BlockState), Inv P.H b.ledger → PoolInv b.rewards →
      executeChain P pow b blocks = some b' → Cap b'.ledger →
      Inv P.H b'.ledger ∧ PoolInv b'.rewards ∧ total P.H b' ≤ total P.H b := by
  induction blocks with
  | nil =>
    intro b b' I IP h _
    simp only [executeChain, Option.some.injEq] at h
    subst h
    exact ⟨I, IP, le_rfl⟩
  | cons inp rest ih =>
    intro b b' I IP h hcap
    simp only [executeChain, option_bind_eq_some] at h
    obtain ⟨b1, h1, h2⟩ := h
    have G : Grows b1.ledger b'.ledger := by
      clear ih h1 I IP hcap
      induction rest generalizing b1 with
      | nil => simp only [executeChain, Option.some.injEq] at h2; rw [h2]; exact Grows.refl _
      | cons inp' rest' ih' =>
        simp only [executeChain, option_bind_eq_some] at h2
        obtain ⟨b2, h21, h22⟩ := h2
        exact (executeBlock_grows h21).trans (ih' b2 h22)
    obtain ⟨I1, IP1, -, T1⟩ := executeBlock_total I IP h1 (hcap.of_grows G)
    obtain ⟨I2, IP2, T2⟩ := ih b1 b' I1 IP1 h2 hcap
    exact ⟨I2, IP2, T2.trans T1⟩

/-! ## Every token value fits a `TokenValue` -/

/-- The maximum supply: `10¹⁰` LGO, `10¹⁹` units of `10⁻⁹` LGO. -/
def MAX_SUPPLY : ℕ := 10 ^ 19

theorem maxSupply_lt : MAX_SUPPLY < TOKEN_BOUND := by decide

/-- An unspent note of a set counts at most the tokens of the block state. -/
theorem cmValue_le_total (H : Hash) (b : BlockState) {i : ℕ} {c : Fr}
    (hi : i < b.ledger.numSets) (hc : c ∈ (b.ledger.sets i).cms)
    (hu : Unspent H (b.ledger.sets i).nullifiers c) : cmValue H c ≤ total H b := by
  have h1 : cmValue H c ≤ (b.ledger.sets i).supply H :=
    Finset.single_le_sum (f := cmValue H) (fun _ _ => Nat.zero_le _)
      (Finset.mem_filter.2 ⟨List.mem_toFinset.2 hc, hu⟩)
  have h2 : (b.ledger.sets i).supply H ≤ setsValue H b.ledger :=
    Finset.single_le_sum (f := fun j => (b.ledger.sets j).supply H) (fun _ _ => Nat.zero_le _)
      (Finset.mem_range.2 hi)
  simp only [total, value]
  omega

/-- **Every token value fits a `TokenValue`**: along any chain of blocks from a state holding at
most the maximum supply, every unspent note, the proof of work pool, the reserve, the rewards
pool and the pending Blend share are at most `10¹⁹`, below `2^64`. -/
theorem executeChain_tokenValue {P : Prims} [P.ZkTransferSound] [P.ZkProgramSpendSound]
    {pow : PowShare} {blocks : List BlockInputs} {b b' : BlockState} (I : Inv P.H b.ledger)
    (IP : PoolInv b.rewards) (hg : total P.H b ≤ MAX_SUPPLY)
    (h : executeChain P pow b blocks = some b') (hcap : Cap b'.ledger) :
    total P.H b' ≤ MAX_SUPPLY ∧
      (∀ i < b'.ledger.numSets, ∀ c ∈ (b'.ledger.sets i).cms,
        Unspent P.H (b'.ledger.sets i).nullifiers c → cmValue P.H c ≤ MAX_SUPPLY) ∧
      b'.ledger.powRewardPool ≤ MAX_SUPPLY ∧ b'.rewards.reserve ≤ MAX_SUPPLY ∧
      b'.rewards.pool ≤ MAX_SUPPLY ∧ b'.rewards.pending ≤ MAX_SUPPLY := by
  have ht := (executeChain_total blocks b b' I IP h hcap).2.2.trans hg
  refine ⟨ht, fun i hi c hc hu => (cmValue_le_total P.H b' hi hc hu).trans ht, ?_⟩
  simp only [total, value] at ht
  omega

end

end TokenEconomics
