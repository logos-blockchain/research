import TokenEconomics.BlockReward

/-!
# The reserve, the rewards pool and the pending Blend share

Block Rewards, *Deterministic Implementation*, and Cryptoeconomics Overview, *Blend Service
and Consensus Leaders* (RFC-480 §6). At each block

```python
pooled_fees_window = pooled_fees_window[1:] + [pooled_fees]
release, payout = block_reward(total_stake, pooled_fees_window, rewards_reserve)
rewards_reserve -= release
rewards_pool += pooled_fees
rewards_pool -= payout
blend_rewards_pending += release + payout - leader_share(block)
```

(`RewardState`, `rewardStep`), with `leader_share = 2 R // 5`. The Blend reward of an epoch is
paid from `blend_rewards_pending` in the first block of the epoch after next, and what its
notes do not use returns to the pool (`payBlend`).

Results:

* **`poolInv_rewardStep`**: the invariant `120 · pool ≥ ∑ᵢ i · window[i]` (each pooled fee
  keeps the `1/120` shares of the windows it has not yet been paid in) holds at genesis and
  after every block, so **the pool never goes below zero**: `pool + pooled_fees ≥ payout`
  (`payout_le_pool`), as the specification claims ("every pooled fee is paid out at most once");
* `rewardStep_conserves`: a block moves tokens between the stocks:
  `reserve' + pool' + pending' + leader_share = reserve + pool + pending + pooled_fees`;
* `leaderShare_le`, `blendShare_ge`: the leader gets 40% rounded down, the Blend service the
  rest, at least 60%;
* **`runEpochs_pending`**, **`blend_payment_covered`**: along epochs of blocks (`rewardStep`),
  the Blend reward of epoch `e` being paid at the start of epoch `e + 2` (`payBlend`),
  `blend_rewards_pending` is exactly the Blend rewards of the two unpaid epochs, and so always
  covers the payment.
-/

namespace TokenEconomics

/-- The consensus state of the block reward. -/
structure RewardState where
  reserve : ℕ
  pool : ℕ
  pending : ℕ
  window : List ℕ

/-- The state set at Genesis: `B_0 = 10¹⁸` units (`10⁹` LGO), an empty pool, nothing pending, a
zero window. -/
def genesisRewards : RewardState := ⟨10 ^ 18, 0, 0, List.replicate WINDOW 0⟩

/-- `leader_share(b)`: 40% of the block reward, rounded down. -/
def leaderShare (R : ℕ) : ℕ := 2 * R / 5

/-- The Blend share of a block reward: the rest. -/
def blendShare (R : ℕ) : ℕ := R - leaderShare R

/-- The reward of a block, at stake `stake` and with `pooled` fees pooled in it: the new
state, and the block reward. -/
def rewardStep (st : RewardState) (stake pooled : ℕ) : RewardState × ℕ :=
  let window := st.window.tail ++ [pooled]
  let rel := release stake window.sum st.reserve
  let pay := payout stake window.sum
  let R := rel + pay
  (⟨st.reserve - rel, st.pool + pooled - pay, st.pending + blendShare R, window⟩, R)

/-- Paying the Blend reward `B` of an epoch with notes worth `paid ≤ B`: the reward leaves
`blend_rewards_pending`, what the notes do not use returns to the pool. -/
def payBlend (st : RewardState) (B paid : ℕ) : RewardState :=
  { st with pending := st.pending - B, pool := st.pool + (B - paid) }

theorem leaderShare_le (R : ℕ) : leaderShare R ≤ R := by unfold leaderShare; omega

theorem leaderShare_add_blendShare (R : ℕ) : leaderShare R + blendShare R = R := by
  unfold blendShare; have := leaderShare_le R; omega

/-- The Blend service receives at least 60% of the block reward. -/
theorem blendShare_ge (R : ℕ) : 3 * R ≤ 5 * blendShare R := by
  unfold blendShare leaderShare; omega

/-! ## The pool never goes below zero -/

/-- `∑ᵢ i · l[i]`: the shares of the pooled fees of the window not yet paid out. -/
def unpaidShares : List ℕ → ℕ
  | [] => 0
  | _ :: l => l.sum + unpaidShares l

theorem unpaidShares_append (l : List ℕ) (x : ℕ) :
    unpaidShares (l ++ [x]) = unpaidShares l + l.length * x := by
  induction l with
  | nil => simp [unpaidShares]
  | cons a l ih => simp only [List.cons_append, unpaidShares, ih, List.sum_append]; simp; ring

theorem unpaidShares_replicate (n : ℕ) : unpaidShares (List.replicate n 0) = 0 := by
  induction n with
  | zero => rfl
  | succ n ih => simp [List.replicate_succ, unpaidShares, ih]

/-- The pool holds every share of the pooled fees of the window not yet paid out. -/
structure PoolInv (st : RewardState) : Prop where
  length : st.window.length = WINDOW
  shares : unpaidShares st.window ≤ WINDOW * st.pool

theorem poolInv_genesis : PoolInv genesisRewards :=
  ⟨by simp [genesisRewards], by simp [genesisRewards, unpaidShares_replicate]⟩

/-- **No underflow: the pool and the pooled fees of the block cover its payout.** -/
theorem payout_le_pool {st : RewardState} (I : PoolInv st) (stake pooled : ℕ) :
    payout stake (st.window.tail ++ [pooled]).sum ≤ st.pool + pooled := by
  have hp := payout_le stake (st.window.tail ++ [pooled]).sum
  obtain ⟨a, t, ht⟩ : ∃ a t, st.window = a :: t := by
    cases h : st.window with
    | nil => have := I.length; simp [h, WINDOW] at this
    | cons a t => exact ⟨a, t, rfl⟩
  have hs := I.shares
  rw [ht] at hs
  simp only [ht, List.tail_cons, List.sum_append, List.sum_singleton] at hp ⊢
  simp only [unpaidShares] at hs
  simp only [WINDOW] at hp hs
  omega

/-- **The pool invariant holds after every block**, and after any amount returns to the pool. -/
theorem poolInv_rewardStep {st : RewardState} (I : PoolInv st) (stake pooled : ℕ) :
    PoolInv (rewardStep st stake pooled).1 := by
  obtain ⟨a, t, ht⟩ : ∃ a t, st.window = a :: t := by
    cases h : st.window with
    | nil => have := I.length; simp [h, WINDOW] at this
    | cons a t => exact ⟨a, t, rfl⟩
  have hlen := I.length
  have hs := I.shares
  have hp := payout_le stake (st.window.tail ++ [pooled]).sum
  have hle := payout_le_pool I stake pooled
  rw [ht] at hlen hs hp hle
  simp only [List.length_cons] at hlen
  refine ⟨by simp [rewardStep, ht]; omega, ?_⟩
  simp only [rewardStep, ht, List.tail_cons, unpaidShares_append, List.sum_append,
    List.sum_singleton]
  simp only [List.tail_cons, List.sum_append, List.sum_singleton] at hp hle
  simp only [unpaidShares] at hs
  simp only [WINDOW] at hp hs hlen ⊢
  have hl' : t.length = 119 := by omega
  rw [hl', Nat.mul_sub, Nat.mul_add]
  omega

theorem poolInv_payBlend {st : RewardState} (I : PoolInv st) (B paid : ℕ) :
    PoolInv (payBlend st B paid) :=
  ⟨I.length, I.shares.trans (Nat.mul_le_mul_left _ (Nat.le_add_right _ _))⟩

/-- **A block moves tokens between the stocks**: what leaves the reserve and the pool, with the
pooled fees, is the leader share and the pending Blend share. -/
theorem rewardStep_conserves {st : RewardState} (I : PoolInv st) (stake pooled : ℕ) :
    (rewardStep st stake pooled).1.reserve + (rewardStep st stake pooled).1.pool +
        (rewardStep st stake pooled).1.pending + leaderShare (rewardStep st stake pooled).2 =
      st.reserve + st.pool + st.pending + pooled := by
  have h1 := release_le_reserve stake (st.window.tail ++ [pooled]).sum st.reserve
  have h2 := payout_le_pool I stake pooled
  have h3 := leaderShare_add_blendShare
    (release stake (st.window.tail ++ [pooled]).sum st.reserve +
      payout stake (st.window.tail ++ [pooled]).sum)
  simp only [rewardStep]
  omega

/-- The reserve only decreases, by at most `MAX_RELEASE` units per block. -/
theorem reserve_step {st : RewardState} (stake pooled : ℕ) :
    (rewardStep st stake pooled).1.reserve ≤ st.reserve ∧
      st.reserve ≤ (rewardStep st stake pooled).1.reserve + MAX_RELEASE := by
  have := release_le stake (st.window.tail ++ [pooled]).sum st.reserve
  simp only [rewardStep]
  omega

/-! ## The Blend reward of an epoch -/

/-- The Blend reward of an epoch: the Blend shares of its blocks (`get_blend_reward`). -/
def blendReward (rewards : List ℕ) : ℕ := (rewards.map blendShare).sum

/-- The blocks of an epoch, each given by its stake and its pooled fees: the state after them
and their block rewards. -/
def runEpoch : RewardState → List (ℕ × ℕ) → RewardState × List ℕ
  | st, [] => (st, [])
  | st, b :: bs =>
    ((runEpoch (rewardStep st b.1 b.2).1 bs).1, (rewardStep st b.1 b.2).2 :: (runEpoch (rewardStep st b.1 b.2).1 bs).2)

/-- An epoch adds the Blend share of each of its block rewards to `blend_rewards_pending`. -/
theorem runEpoch_pending (st : RewardState) (bs : List (ℕ × ℕ)) :
    (runEpoch st bs).1.pending = st.pending + blendReward (runEpoch st bs).2 := by
  induction bs generalizing st with
  | nil => simp [runEpoch, blendReward]
  | cons b bs ih =>
    simp only [runEpoch, ih, blendReward, List.map_cons, List.sum_cons, rewardStep]
    ring

/-- A sequence of epochs from `st`: at the start of epoch `n ≥ 2`, the Blend reward of epoch
`n - 2` is paid from `blend_rewards_pending` with notes worth `paid n`, at most that reward
(`payBlend`), then the blocks `epochs n` run. Returns the state at the start of epoch `n`,
before its payment, and the Blend rewards of epochs `0, …, n - 1`. -/
def runEpochs (st : RewardState) (epochs : ℕ → List (ℕ × ℕ)) (paid : ℕ → ℕ) :
    ℕ → RewardState × List ℕ
  | 0 => (st, [])
  | n + 1 =>
    let s := (runEpochs st epochs paid n).1
    let hist := (runEpochs st epochs paid n).2
    let B := hist.getD (n - 2) 0
    let s1 := if 2 ≤ n then payBlend s B (min (paid n) B) else s
    ((runEpoch s1 (epochs n)).1, hist ++ [blendReward (runEpoch s1 (epochs n)).2])

/-- **`blend_rewards_pending` holds the Blend rewards of the two unpaid epochs**: from a state
with nothing pending, at the start of epoch `n` it is the Blend reward of epoch `n - 2` plus
that of epoch `n - 1`. -/
theorem runEpochs_pending (st : RewardState) (h0 : st.pending = 0)
    (epochs : ℕ → List (ℕ × ℕ)) (paid : ℕ → ℕ) (n : ℕ) :
    (runEpochs st epochs paid n).2.length = n ∧
      (runEpochs st epochs paid n).1.pending =
        (if 2 ≤ n then (runEpochs st epochs paid n).2.getD (n - 2) 0 else 0) +
          (if 1 ≤ n then (runEpochs st epochs paid n).2.getD (n - 1) 0 else 0) := by
  induction n with
  | zero => simp [runEpochs, h0]
  | succ n ih =>
    obtain ⟨hl, hp⟩ := ih
    simp only [runEpochs]
    generalize (runEpochs st epochs paid n).1 = s at hp
    generalize (runEpochs st epochs paid n).2 = hist at hl hp
    have hp1 : (if 2 ≤ n then payBlend s (hist.getD (n - 2) 0)
        (min (paid n) (hist.getD (n - 2) 0)) else s).pending =
        if 1 ≤ n then hist.getD (n - 1) 0 else 0 := by
      split_ifs with h2 h1 h1
      · simp only [payBlend, hp, h2, h1, ite_true]
        omega
      · omega
      · simp only [hp, h2, h1, ite_true, ite_false]
        omega
      · simp only [hp, h2, h1, ite_false]
    rw [runEpoch_pending, hp1]
    generalize blendReward _ = x
    have ga : ∀ k < hist.length, (hist ++ [x]).getD k 0 = hist.getD k 0 := by
      intro k hk
      simp [List.getD_eq_getElem?_getD, List.getElem?_append_left hk]
    have gb : ∀ k, k = hist.length → (hist ++ [x]).getD k 0 = x := by
      intro k hk
      subst hk
      simp [List.getD_eq_getElem?_getD]
    refine ⟨by simp [hl], ?_⟩
    rcases n with _ | _ | n
    · simp only [show ¬(2 ≤ 0 + 1) by omega, show 1 ≤ 0 + 1 by omega, show ¬(1 ≤ 0) by omega,
        ite_true, ite_false, show 0 + 1 - 1 = 0 by rfl, gb 0 hl.symm, Nat.zero_add]
    · simp only [show 2 ≤ 0 + 1 + 1 by omega, show 1 ≤ 0 + 1 + 1 by omega,
        show 1 ≤ 0 + 1 by omega, ite_true, show 0 + 1 + 1 - 2 = 0 by rfl,
        show 0 + 1 + 1 - 1 = 1 by rfl, ga 0 (by omega),
        gb 1 hl.symm]
    · have e1 := ga (n + 1) (by omega)
      have e2 := gb (n + 2) hl.symm
      simp only [show 1 ≤ n + 1 + 1 by omega, show 2 ≤ n + 1 + 1 + 1 by omega,
        show 1 ≤ n + 1 + 1 + 1 by omega, ite_true, show n + 1 + 1 + 1 - 2 = n + 1 by omega,
        show n + 1 + 1 + 1 - 1 = n + 2 by omega, show n + 1 + 1 - 1 = n + 1 by omega, e1, e2]

/-- **The Blend reward of an epoch is always covered when paid**: at the start of epoch
`n ≥ 2`, the Blend reward of epoch `n - 2` is at most `blend_rewards_pending`, so the payment the
service reward distribution makes never exceeds it. -/
theorem blend_payment_covered (st : RewardState) (h0 : st.pending = 0)
    (epochs : ℕ → List (ℕ × ℕ)) (paid : ℕ → ℕ) {n : ℕ} (hn : 2 ≤ n) :
    (runEpochs st epochs paid n).2.getD (n - 2) 0 ≤ (runEpochs st epochs paid n).1.pending := by
  rw [(runEpochs_pending st h0 epochs paid n).2]
  simp only [hn, ite_true]
  omega

end TokenEconomics
