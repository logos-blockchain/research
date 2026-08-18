mary": "Extract every reward formula the strategy simulator needs, from the specs",
  "agentCount": 9,
  "logs": [
    "extracting 4 reward streams from the specification tree",
    "1/4 faithful on first pass"
  ],
  "result": {
    "model": "# Reward Model of Record â Logos Blockchain

**Source tree:** `/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/`
All citations below are `file:line` relative to that directory. This document folds in the independent verification of each extraction: invented elements have been removed, wrong citations corrected, missed elements added. Where a verification found an extraction claim to be arithmetically wrong, the corrected number is used and the error is not repeated.

**Status vocabulary.** SPECIFIED = a value in a Standards Track document's normative text or constant table. ILLUSTRATIVE = a number appearing only in an Informational analysis, an example, or a simulation assumption. UNSET = the specification names the quantity but gives no value anywhere.

---

## 1. The reward streams

There are four token flows. Three pay participants; the fourth (emission) is the source of two of them.

```
fees collected by a block
   âââ 10/100 diverted BEFORE the burn ââââââââââââââº PoW reward pool âââº PoW claims
   âââ remainder burnt = D_1,t = R_block
                â
                â¼
        block reward Rewards_t = A_tÂ·(I_maxÂ·S_tgeÂ·Î_t/f)  +  (1âA_t)Â·R_block
                â                    â newly minted â        â re-mint of burnt â
                âââ 60% âââº Blend service pool âââº service rewards (flat per active node)
                âââ 40% âââº leader pool ââââââââââº leader claims (flat per voucher)
                            + 100% of execution tips
```

---

### 1.1 Proof-of-work claims (`CLAIM_POW_REWARD`)

The only stream that is not funded by emission and does not mint. A claim moves tokens that already exist in a pool into circulation (`bedrock-v1.1-mantle-specification.md:1578`).

#### Formula â per-claim reward, exact integer arithmetic

`bedrock-v1.1-mantle-specification.md:1776-1787`:

```python
EPOCH_POW_DISTRIBUTION_RATE_NUM: uint64 = 1     # rho
EPOCH_POW_DISTRIBUTION_RATE_DEN: uint64 = 200
TARGET_CLAIMS_PER_BLOCK: uint64 = 10            # T
EXPECTED_BLOCKS_PER_EPOCH: uint64 = 21_600      # N_b

def compute_epoch_pow_reward(pow_reward_pool: TokenValue) -> TokenValue:
    denominator = (EPOCH_POW_DISTRIBUTION_RATE_DEN
                   * TARGET_CLAIMS_PER_BLOCK
                   * EXPECTED_BLOCKS_PER_EPOCH)
    return (pow_reward_pool * EPOCH_POW_DISTRIBUTION_RATE_NUM) // denominator
```

Denominator is the compile-time constant `200 Ã 10 Ã 21600 = 43,200,000`. So Ï_e = âpool / 43,200,000â, **one** flooring site. The residue is not lost: *"what the flooring withholds is not lost: it simply remains in the pool, to be counted again at the next boundary"* (`:1791`).

#### Formula â pool refill, exact integer arithmetic

`overview-cryptoeconomics.md:180-184`:

```python
def get_pow_pool_refill(e: epoch):
    refill = 0
    for b in e.blocks:
        refill += get_collected_fees(b) * POW_SHARE // SHARE_DEN
    return refill
```

Flooring is **per block**: Î£_b âfees_b Â· 10 / 100â, not âÎ£_b fees_b Â· 10 / 100â. The sub-lepton residue of each flooring *"stays with the remainder and is burnt"* (`overview-cryptoeconomics.md:187`). The diverted share is taken from the fee burn, never minted (`bedrock-v1.1-mantle-specification.md:1814`).

Boundary order, `:1805-1812` â refill **then** recompute:

```python
def on_epoch_boundary(epoch_blocks: list[Block]):
    pow_reward_pool = checked_uint64(pow_reward_pool + get_pow_pool_refill(epoch_blocks))
    epoch_pow_reward = compute_epoch_pow_reward(pow_reward_pool)
```

#### Formula â reward difficulty retarget, every block, exact integer arithmetic

`bedrock-v1.1-mantle-specification.md:1866-1884`:

```python
demand = max(1, (EMA_SMOOTHING_PRECISION - EMA_SMOOTHING_FACTOR) * claims_in_block
                + EMA_SMOOTHING_FACTOR * TARGET_CLAIMS_PER_BLOCK)
new_target = (TARGET_CLAIMS_PER_BLOCK * current_target
              * EMA_SMOOTHING_PRECISION) // demand
return min(new_target, p - 1)
```

At the specified constants this reduces to `new_target = â100 Â· current_target / (claims_in_block + 90)â`. The `max(1, â¦)` is dead code at F=9, P=10, T=10 â it binds only if the constants change. Arithmetic is **arbitrary-precision, not `checked_uint64`** (`:135`; intermediate reaches ~2^261). Fixed point at 10 claims. At zero claims the target multiplies by 10/9 per block. Controller invariant, stated at `:1899`: *"the estimate equals `TARGET_CLAIMS_PER_BLOCK` divided by the current target."*

#### Eligibility gate

No stake, no declaration, no prior tokens. The Operation carries no signature and no ZK proof â *"the authorisation is the puzzle solution itself"* (`:1640`). Ticket:

```python
def get_puzzle_ticket(claim) -> zkhash:
    return zkhash(claim.epoch_nonce,
                  FiniteField(claim.block_hash, byte_order="little", modulus=p),
                  claim.public_key)
```

Accepted iff **all** of (`:1663-1681`):

1. `epoch_pow_reward > 0`
2. `pow_reward_pool >= epoch_pow_reward`
3. referenced block is **canonical** and `0 <= current_slot - block.slot <= WINDOW`
4. `claim.epoch_nonce == get_current_epoch_nonce()` (the Cryptarchia Î·)
5. `puzzle_ticket < difficulty_reward` (smaller target is harder, `:1576`)
6. `puzzle_ticket not in pow_nullifiers` â **the nullifier is the ticket itself** (`:1686`)

Conditions 1 and 2 are evaluated per claim against the pool as preceding Operations left it, including within a single transaction (`:217`, `:1826`). A claim failing only on the pool guard invalidates its whole transaction.

#### Timing and lags

- **Per claim:** immediate. Output note of value `epoch_pow_reward`; `pow_reward_pool -= epoch_pow_reward`, exact, no flooring.
- **Per block:** difficulty retarget with a **one-block lag** â *"Every claim in a block is validated against the target produced by the previous block's update; the update from a block's own accepted count is applied after the block is processed and governs the next block"* (`:1887`). The controller observes claims **included in blocks**, not solutions found (`:1893`).
- **Per epoch:** refill lags one full epoch (fees of epoch eâ1 fund epoch e). Ï_e is then **frozen for the whole epoch** even as the pool it is paid from shrinks (`:1820`). Freezing is what makes the self-funding claim transaction possible â the reward note's id is computable in advance (`:1768-1770`).
- **Epoch nonce coupling:** a solution dies at the epoch boundary and must be re-mined (`:1694`); but the nonce is public part way through the *preceding* epoch, so solutions for epoch N can be ground during Nâ1 (`:1696`).
- **Acceptance window:** `WINDOW = âW_b/fâ = 300 slots` at W_b=10, f=1/30 (`:1597`, `:1600`).

#### The claim's own fee

No special rule: *"This Operation performs no fee or balance check of its own"* (`:1690`). Canonical self-funding transaction is `CLAIM_POW_REWARD + TRANSFER`, execution gas 56 + 590 = 646 (`:2255`, `:2245`, `analysis-gas-cost-determination.md:248`). The transaction's encoded byte size â the other half of its fee â is **UNSET**, and worse: `mantle-transaction-encoding.md:65-74` does not define a `ClaimPowReward` payload at all, so the size is not even derivable from field widths.

---

### 1.2 Leader rewards

#### Formula â the split

`overview-cryptoeconomics.md:142-145`: *"40% for the leader. 60% for the Blend service."* Pool accrual, `:164-173`:

```python
def update_leader_rewards(e: epoch, leader_rewards: int):
    for b in e.blocks:
        leader_rewards += 0.4 * get_block_rewards(b)
        leader_rewards += get_execution_market_tips(b)
    return leader_rewards
```

Integer form, `block-rewards.md:497-498`:

```python
blend_reward  = reward_numerator * 6 // (reward_denominator * 10)
leader_reward = reward_numerator * 4 // (reward_denominator * 10)
```

Two independent floors, applied to the reward *numerator*; a single "block reward" is never materialised and then split.

#### Formula â what an individual leader receives

`bedrock-anonymous-leaders-reward.md:93-98`:

$$
share = \begin{cases} 0 & \text{if } |voucher\_cm| = |voucher\_nf| \\ \left\lfloor\dfrac{leader\_rewards}{|voucher\_cm| - |voucher\_nf|}\right\rfloor & \text{otherwise}\end{cases}
$$

Integer division over `TokenValue`. The denominator is the **cumulative** count of vouchers admitted since genesis minus nullifiers spent (`overview-cryptoeconomics.md:63`). No-overdraw invariant, `bedrock-anonymous-leaders-reward.md:100`: *"Rounding down guarantees that share Ã (|voucher_cm| â |voucher_nf|) â¤ leader_rewards, an inequality that every claim preserves since it decreases both sides by one share and one voucher respectively."* Residue: `:102` *"the remainder stays in `leader_rewards` until it is claimed or aggregated with the rewards of the next epoch."* Writing `leader_rewards = qÂ·n + r`, the first nâr claimants get q and the last r get q+1.

**A leader's payment is not a function of the block it proposed** (`:87`). It is `âpool / unclaimedâ` at claim time.

#### Formula â the lottery

`cryptarchia-proof-of-leadership.md:180-184`. Win iff `ticket < t` where

- `ticket = Poseidon2(LEAD_V1 || Î· || sl || noteID || sk)`
- `t = v Â· (t_0 + t_1 Â· v)`, v = the note's value

with (`:210-212`, `:219-223`, `:233-248`):

```
t_0 = t_0_constant // inferred_total_stake
t_1 = p - (t_1_constant // inferred_total_stake**2)
t_0_constant = 0x1a3fb997fd5838f2a1585ee090a95c88129ab25cc4d2e2d28f1a95f81d85465
t_1_constant = 0x71e790b4199113a9a00298d823c5716ddac764a110a45fe3b770bbb3e8a57
p            = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001
```

This is the 2nd-order Taylor expansion of Ï_f(Î±) = 1 â (1âf)^Î±. **The leading coefficient is âln(1âf) = 0.033901, not f = 0.033333** â a 1.7% difference in block rate. `t_1` is stored as `p â |t_1|`, so the real-valued threshold is `vÂ·t_0 â vÂ²Â·|t_1|`, a downward-opening parabola (`:296`). Pathological regime at v â« D: threshold peaks near 29D, crosses zero near 58D, then wraps in F_p and *"The note wins nearly every slot"*; spec says *"No circuit-level mitigation is strictly necessary"* (`:315`).

#### Eligibility gate

1. **Note aging.** Unspent **and** a member of the note set at the start of the *previous* epoch (`cryptarchia-v1-protocol.md:160`, `:208-212`). Enforced as dual Merkle membership in `ledger_AGED` and `ledger_LATEST` (`cryptarchia-proof-of-leadership.md:145-149`). *(DERIVED: effective minimum age is one full epoch, maximum two.)*
2. **Win the lottery** in a slot.
3. **No minimum stake.** Affirmatively stated, not an omission: *"Blend nodes must stake a minimum amount while leaders have no such requirement"* (`overview-cryptoeconomics.md:149`). The SDP min stake governs service declaration only.
4. **Produce a valid block**, sign it with a single-use Ed25519 key bound to the PoL (`cryptarchia-proof-of-leadership.md:189-193`), and embed one fresh 32-byte `leader_voucher` commitment in the header (`bedrock-v1.1-block-construction.md:122`).
5. **Claim** against the voucher root frozen at the start of the current epoch, with an unused nullifier (`bedrock-v1.1-mantle-specification.md:1497-1501`).

#### Timing and lags

- **Per slot:** one lottery per note. `f = 1/30`; *"For each slot, we can have 0 or more winners"* (`cryptarchia-v1-protocol.md:232`) â simultaneous winners are guaranteed forks.
- **Per block:** nothing is paid. A voucher commitment is placed in the header and sits outside the tree.
- **Epoch boundary (first block of e+1):** two things happen â the voucher is appended to the tree (`bedrock-anonymous-leaders-reward.md:72`; `bedrock-v1.1-block-construction.md:241`), and the pool is credited with epoch e's 40% + tips (`bedrock-anonymous-leaders-reward.md:91`).
- **Lag:** a block in epoch e becomes claimable at the start of e+1. Bounds: one block to one full epoch (7.5 days). *(DERIVED: mean â 3.75 days.)*
- **Claim time:** chosen by the leader. Share recomputed at execution, **not** frozen at the epoch boundary â contrast the PoW pool, which explicitly is frozen (`:1820`). Claim costs `EXECUTION_LEADER_CLAIM_GAS = 580` (`:2254`).
- **No expiry.** Vouchers remain claimable indefinitely. The spec demonstrably knew how to write an expiry â the PoW path has an explicit Window of Acceptance (`:1580-1585`) â and did not write one here.

---

### 1.3 Service rewards (Service Declaration Protocol + Service Reward Distribution Protocol)

Only one service type exists: `ServiceType.BN`, the Blend Network (`bedrock-service-declaration-protocol.md:79-84`; *"Any declaration that is not one of the above must be rejected"*).

#### Formula â the framework delegates

`bedrock-service-reward-distribution.md:70-76`: `Rewards^n := serviceReward(n, Rewards_Epoch)`, where `Rewards_Epoch` is *"the total rewards of epoch N"* and the linked reference *"calculates how much each service receives."* **`I` (the Blend service's income) = 0.6 Ã `Rewards_Epoch`, not `Rewards_Epoch` itself.**

#### Formula â the per-provider split

`blend-protocol.md:1106-1126`:

$$B = \sum_{i=1}^{N}\mathrm{true}(\pi_A^{i,t,e}) \qquad P = \sum_{i=1}^{N}\min_{\Delta_{\mathcal H}}(\mathrm{true}(\pi_A^{i,t,e}))$$
$$R = \frac{I}{B+P} \qquad R(n) = R \cdot [\mathrm{true}(\pi_A^{i,t,e}) + \min_{\Delta_{\mathcal H}}(\mathrm{true}(\pi_A^{i,t,e}))]$$

Base reward to every provider with a true proof; **doubled** for those at the minimal Hamming distance. *(DERIVED: Î£ R(n) = RÂ·(B+P) = I exactly, so the stream distributes its full 60% share whenever B â¥ 1.)*

**No integer/rounding rule is given** for R â in contrast to the leader pool and the PoW pool, both of which are explicit about flooring and residue. This is a determinism gap in a protocol that requires identical execution on every node (`bedrock-service-reward-distribution.md:87`).

#### Formula â the activity lottery

`blend-protocol.md:1026-1036`: a proof is `true` iff Proof of Quota holds, Proof of Selection holds, and

$$\Delta_{\mathcal H}(H(t)_\epsilon, H(R_{e+1})_\epsilon) < \mathcal{A}_\epsilon$$

with (`:1070-1080`) `A_Îµ = Ï â Î½ â Î¸`, `Î½ = âlogâ(N+1)â`, `Ï = âlogâ(Q_C^Total + 1)â`, `Î¸ = 1`, and `Îµ = âlogâ(Q_C^Total+1)/8â Â· 8` (`:1044`). N is the core-node set returned by SDP (`:468-469`).

#### Eligibility gate â seven conditions, in order

1. **Network-size gate (whole service).** Fewer than 32 unique ProviderIds â *"Rewards are not calculated"* at all (`:1110`, `:150`). And the service itself shuts down: *"If the minimal network size is not reached, nodes must not use the Blend protocolâ¦ nodes must broadcast data messages directly, bypassing the Blend network"* (`:158`).
2. **Declaration visible in the epoch's SDP snapshot**, taken at the last block of `current_epoch â 2` (`bedrock-service-declaration-protocol.md:63`, `:127-130`). Epochs 0 and 1 read the genesis snapshot.
3. **Exactly one `SDP_ACTIVE` transaction** for epoch e, submitted during epoch e+1 after the 30-round transition period. Late â no reward at all (`blend-protocol.md:1104`, `:1135-1137`).
4. **Valid Activity Proof** in metadata, signed by `zk_id`, monotone nonce.
5. **The proof must win the Hamming lottery.** A provider that did the work and was unlucky earns nothing.
6. **Minimal Hamming distance** for the 2Ã premium.
7. **Not inactive** (2 epochs without an Active message) and not past `withdraw_at`.

**Stake dependence: none.** The formula contains no stake term. Stake is a binary admission gate, `assert note.value >= min_stake.stake_threshold` (`bedrock-v1.1-mantle-specification.md:1119`). Staking more buys nothing.

#### Timing and lags

Epoch N work â Active message in N+1 â computation at end of N+1 â payout in the **first block of N+2**, inserted directly into the ledger with no Mantle validation, `op_id = hash(ServiceType || epoch_number)`, outputs ordered by ascending `zk_id` (`bedrock-service-reward-distribution.md:80-87`). Work-to-payment lag: **2 epochs = 15 days**. *(DERIVED: total exposure from declaring to first possible reward is up to 4 epochs â 30 days.)*

SDP Epoch Finalization runs in the same first block of N+2, **after** the payout, removing declarations with `withdraw_at <= current_epoch â 2` (`bedrock-v1.1-mantle-specification.md:1342-1384`).

---

### 1.4 The emission that funds leader and service rewards

#### Formula â total minted per block, equation (1)

`block-rewards.md:193-206`:

$$A_t \cdot \frac{I_{max} \cdot S_{tge} \cdot \Delta_t}{f} + (1-A_t) \cdot R_{block}, \qquad R_{block} = D_{1,t}$$

**Only the first term is new tokens.** The second is a re-mint of what the block just burnt: *"if far from the target, the system mints new tokens; if close to the target, the system mints exactly what was burned (up to I_max of TGE)"* (`:176-181`).

Supply evolution, `analysis-block-rewards.md:69-83` â the only statement in the tree of how minted rewards accumulate:

$$S_t = \min\{S_{cap},\ S_{tge}\times(1 + \textstyle\sum_{\tau=1}^t A_\tau \cdot I_{max}\cdot\Delta_\tau)\}$$

*"It is assumed here that S_{tâ1} already accounts for the burned tokens. This equation implies that the supply evolution does not compound over time."*

#### Formula â the control function

`block-rewards.md:228-232`:

$$A_t = \min\{1, \max\{0, \tfrac{\alpha_d\delta_t + \alpha_a\gamma_t + I_{min}}{I_{max}}\}\}$$

$$\delta_t = \sum_i w_i\frac{D_{i,target}-D_{i,t}}{D_{i,target}} \qquad \gamma_t = \frac{1}{\Delta_t}\sum_i w_i\Bigl(\frac{1}{T}\sum_{\tau=t-T+1}^{t}\frac{D_{i,\tau}}{D_{i,target}}\Bigr)$$

Partitioned by KPI: *"To measure the deviation, only the total estimated stake KPI is used"* (`:298`); *"To measure the average, only the average burning rate KPI is used"* (`:338`). So Î´_t reads KPI 0 only, Î³_t reads KPI 1 only, each with weight 1.

#### Formula â the normative integer form

Because block rewards affect consensus state, *"the consensus rule itself should be defined only in terms of integer arithmetic"* (`:378`). Substituting Î±_d=1/4, Î±_a=1, I_max=10â»Â², T=120, f=1, D_0,target=3e9, D_1,target=S_tge=1e10, Î_t=1/(365Â·2880) gives `:443-451`:

$$A_t' = \min\{12\cdot10^7,\ \max\{0,\ 3\cdot10^9 - D_{0,t} + 10512\textstyle\sum_{\tau=t-119}^{t}D_{1,\tau}\}\},\quad A_t = \frac{A_t'}{12\cdot10^7}$$

with `I_maxÂ·S_tgeÂ·Î_t/f = 10â¸/1051200 = 62500/657` LGO per block (`:462-464`), and `:468-473`:

$$\text{Rewards}_t = \frac{62500\cdot A_t' + 657\cdot(12\cdot10^7 - A_t')\cdot D_{1,t}}{657\cdot 12\cdot 10^7}$$

Reference implementation, `:477-501` â reproduced as written, defects and all:

```python
A_SCALE = 120_000_000
INFLATION_NUMERATOR = 62_500
INFLATION_DENOMINATOR = 657
FEE_AVG_NUMERATOR = 10_512
STAKE_TARGET = int(3e9)

def block_reward(total_stake: int, burned_fees_window: list[int]) -> tuple[int, int]:
    sum_fees = sum(burned_fees_window)
    last_burned_fee = burned_fees_window[-1]
    a_numerator = min(max(STAKE_TARGET + FEE_AVG_NUMERATOR * sum_fees - total_stake, 0), A_SCALE)
    reward_numerator = INFLATION_NUMERATOR * a_numerator
                       + INFLATION_DENOMINATOR * (A_SCALE - a_num) * last_burned_fee   # a_num undefined; not valid Python
    reward_denominator = INFLATION_DENOMINATOR * A_SCALE
    blend_reward  = reward_numerator * 6 // (reward_denominator * 10)
    leader_reward = reward_numerator * 4 // (reward_denominator * 10)
    return blend_reward, leader_reward
```

`a_num` should be `a_numerator`; the line continuation is missing. The formula at `:471` is correct and is not a bug.

#### Formula â the stake KPI D and its inference

`cryptarchia-total-stake-inference.md:59-83`:

```rust
const PRECISION: u64 = 1e3
fn total_stake_inference(total_stake_estimate: u64, epoch_slot: u64) -> u64 {
    let beta_p = truncate(beta * PRECISION); let f_p = truncate(f * PRECISION)
    let tse_p = total_stake_estimate * PRECISION
    let measured_density_p = density_over_slots(epoch_slot, PERIOD) * PRECISION
    let expected_density_p = PERIOD * f_p
    let density_diff_p = expected_density_p - measured_density_p
    let slot_activation_error_p = (tse_p * density_diff_p) / expected_density_p
    let correction_p = (beta_p * slot_activation_error_p) / PRECISION
    max((tse_p - correction_p) / PRECISION, 1)
}
```

*(DERIVED: at the specified Î² = 1.0 this collapses to a pure ratio update, D^ep = D^{epâ1} Â· N_BLOCKS^{epâ1} / (PERIOD Â· f).)*

**The estimator is biased and the spec says so.** `analysis-total-stake-inference.md:71-83`: it converges not to true stake but to `E[D_inf] = (log(1âf)/log(1âf/q)) Â· D_TRUE`, where q is honest slot utilization; *"increased network delay, which reduces the honest slot utilization rate through wasted blocks results in a systematic underestimate of true total stake."* At f=1/30, q=0.85 the factor is â 0.847. A persistent ~15% underestimate of stake is a persistent positive Î´_t, i.e. persistent extra emission. Convergence: steady state after 5 epochs (`:97`), recovery from massive shocks within 2 epochs (`:204`).

#### Eligibility gate

**None.** A_t is a pure function of chain state, evaluated every block, clamped to [0,1] on both sides. There is no minimum stake, no activity threshold, no gate of any kind in the emission-rate-factor function.

#### Timing and lags

- **Per block:** equation (1) evaluated once. Î_t and f=1 are chosen so one time step = one 30-second block. Max newly minted = 62500/657 LGO, *"rounded down where an integer is required, losing less than one lepton per block"* (`bedrock-v1.1-mantle-specification.md:2123`).
- **Burn KPI: no lag.** Î³_t reads Ï = tâ119 â¦ t, **including the current block** (`:305`, `:438`; `last_burned_fee = burned_fees_window[-1]`). One hour of look-back.
- **Stake KPI: substantial lag.** D^ep is inferred from the block count in the **first 6âk/fâ slots of epoch epâ1** (`cryptarchia-v1-protocol.md:224-226`) and is *"the stake relativization constant for the following epoch"* (`:156`). *(DERIVED: the observation window closes 259,200 slots = 3 days = **0.4 epochs** before D takes effect; the oldest observed block is 648,000 slots = 7.5 days = **1.0 epoch** before. Mean dead time **0.7 epochs = 5.25 days**.)*
- **Payout:** 60% aggregated at the Blend epoch boundary, allocated on Active messages during e+2; 40% credited to the leader pool at the start of e+1.

---

## 2. Parameter table

### 2.1 SPECIFIED â emission / block reward

| Symbol | Value | Citation |
|---|---|---|
| S_tge | 10 billion LGO (1e10) | `block-rewards.md:160` |
| I_max | 1% / yr (0.01) | `block-rewards.md:167` |
| I_min | 0% | `block-rewards.md:168` |
| Î±_a | 1 | `block-rewards.md:162` |
| **Î±_d** | **1/4** â *contested, see Â§4.2* | `block-rewards.md:163`, `:389` |
| T (look-back) | 120 blocks (1 hour) | `block-rewards.md:161` |
| w_i | 1 (constraint Î£w_i = 1) | `block-rewards.md:164`, `:143` |
| D_0,target | 3 billion LGO (30% of S_tge) | `block-rewards.md:165` |
| D_1,target | 10 billion LGO (a normalizer) | `block-rewards.md:166` |
| Î_t | 1/(365Â·2880) | `block-rewards.md:170` |
| f (block-rewards) | 1 â **not** the Cryptarchia f | `block-rewards.md:169` |
| A_SCALE | 120,000,000 | `block-rewards.md:478` |
| INFLATION_NUMERATOR | 62,500 | `block-rewards.md:479` |
| INFLATION_DENOMINATOR | 657 | `block-rewards.md:480` |
| FEE_AVG_NUMERATOR | 10,512 | `block-rewards.md:481` |
| STAKE_TARGET | 3e9 | `block-rewards.md:482` |
| Blend share | 60% (`*6 // (den*10)`) | `overview-cryptoeconomics.md:145`; `block-rewards.md:497` |
| Leader share | 40% (`*4 // (den*10)`) | `overview-cryptoeconomics.md:144`; `block-rewards.md:498` |

### 2.2 SPECIFIED â consensus / timing

| Symbol | Value | Citation |
|---|---|---|
| f (Cryptarchia) | 1/30 | `cryptarchia-v1-protocol.md:94` |
| k | 2160 | `cryptarchia-v1-protocol.md:95` |
| slot length | 1 s | `cryptarchia-v1-protocol.md:96` |
| MAX_BLOCK_SIZE | 1 MB (`overview:115` says 1 MiB) | `cryptarchia-v1-protocol.md:97` |
| MAX_BLOCK_TXS | 1024 | `cryptarchia-v1-protocol.md:98` |
| s | 3âk/fâ | `cryptarchia-v1-protocol.md:104` |
| EPOCH_LENGTH | 10âk/fâ slots *(= 648,000 s = 7.5 d, derived)* | `cryptarchia-v1-protocol.md:144`; `block-rewards.md:136` |
| EXPECTED_BLOCKS_PER_EPOCH | 21,600 (= 10k) | `cryptarchia-v1-protocol.md:146`; `mantle:1780` |
| Î² (stake inference) | 1.0 | `cryptarchia-total-stake-inference.md:49` |
| PERIOD | 6âk/fâ *(= 388,800 slots, derived)* | `cryptarchia-total-stake-inference.md:50` |
| PRECISION | 1e3 | `cryptarchia-total-stake-inference.md:64` |
| **D_GENESIS** | **rule, not numeral:** *"the total tokens distributed at genesis"* | `bedrock-genesis-block.md:317` |
| p (BN254 scalar field) | 0x30644e72â¦f0000001 | `cryptarchia-proof-of-leadership.md:219` |
| t_0_constant, t_1_constant | see Â§1.2 | `cryptarchia-proof-of-leadership.md:220-221` |

### 2.3 SPECIFIED â leader stream

| Symbol | Value | Citation |
|---|---|---|
| voucher Merkle depth | 32 | `bedrock-anonymous-leaders-reward.md:123` |
| vouchers per block | exactly 1, 32 bytes | `bedrock-v1.1-block-construction.md:122` |
| genesis leader voucher | 0 / `bytes(32)` | `bedrock-genesis-block.md:201`, `:215` |
| LEADER_CLAIM opcode | 0x30 | `mantle:258` |
| EXECUTION_LEADER_CLAIM_GAS | 580 | `mantle:2254` |
| minimum stake for leadership | **none** (affirmative) | `overview-cryptoeconomics.md:149`, `:152` |

### 2.4 SPECIFIED â service stream

| Symbol | Value | Citation |
|---|---|---|
| Minimal Network Size | 32 unique ProviderIds | `blend-protocol.md:150` |
| Î¸ (activity threshold) | 1 | `blend-protocol.md:1080` |
| Î²_C | 3 | `blend-protocol.md:477` |
| E (rounds/epoch) | 648,000 | `blend-protocol.md:475` |
| transition period | 30 rounds | `blend-protocol.md:570` |
| premium multiplier | 2Ã | `blend-protocol.md:1124-1126` |
| ServiceType set | `BN` only | `bedrock-service-declaration-protocol.md:79-84` |
| inactivity_period (BN) | 2 epochs | `bedrock-service-declaration-protocol.md:360-364` |
| SDP snapshot | `current_epoch â 2` | `bedrock-service-declaration-protocol.md:63` |
| max locators / declaration | 8 (â¥1), each â¤ 329 chars | `bedrock-service-declaration-protocol.md:164`, `:145` |
| EXECUTION_SDP_ACTIVE_GAS | 590 | `mantle:2253` |
| provider cap | **none** | `analysis-static-minimum-stakeâ¦:111` |

### 2.5 SPECIFIED â PoW stream

| Symbol | Value | Citation |
|---|---|---|
| POW_SHARE / SHARE_DEN | 10 / 100 | `mantle:1806-1807` |
| EPOCH_POW_DISTRIBUTION_RATE_NUM / _DEN | 1 / 200 | `mantle:1777-1778`, `:1836` |
| TARGET_CLAIMS_PER_BLOCK | 10 | `mantle:1779` |
| EXPECTED_BLOCKS_PER_WINDOW | 10 | `mantle:1585` |
| WINDOW | âW_b/fâ = **300 slots** (prose only, never assigned) | `mantle:1597`, `:1600` |
| EMA_SMOOTHING_FACTOR / PRECISION | 9 / 10 | `mantle:1867-1868` |
| difficulty_reward at genesis | p Ã· 2Â²â¶ (prose; rounding direction not stated) | `mantle:1901` |
| POW_REWARD_POOL_GENESIS | 5/1000 of launch supply â **fraction, deliberately not a numeral** | `bedrock-genesis-block.md:76-80`; `mantle:1856` |
| EXECUTION_CLAIM_POW_REWARD_GAS | 56 | `mantle:2255` |
| EXECUTION_TRANSFER_GAS | 590 | `mantle:2245` |
| CLAIM_POW_REWARD opcode | 0x40 | `mantle:260` |

### 2.6 SPECIFIED â fee markets and units

| Symbol | Value | Citation |
|---|---|---|
| lepton | 1 LGO = 1e9 lepta; supply 1e19 lepta | `mantle:2119`, `:2121` |
| **b_exec[0]** | **1** (initialized at 1 for the first block) | `execution-market.md:95` |
| G_max | 3,193,460 | `execution-market.md:99` |
| G_target | 1,596,730 | `execution-market.md:100` |
| Ï (fee adjustment rate) | 1/8 | `execution-market.md:101` |
| q (EMA smoothing) | 9/10 (â19-block lookback) | `execution-market.md:102` |
| base fee rounding | **ceil**; effective floor 1 | `execution-market.md:206` |
| storage price rounding | **ceil**; floor 1 (see Â§4.8 on units) | `storage-markets.md:224` |
| T_RA(â1) at genesis | T_base | `storage-markets.md:231` |

### 2.7 ILLUSTRATIVE â do not configure a simulator from these

| Quantity | Value | Where it comes from |
|---|---|---|
| **Î±_d = 1/6** | conflicts with normative 1/4 | `analysis-block-reward-parameter-calibration.md:80` |
| Î±_d = Î±_a = 1, T = 0, S_tge = 1 LGO, S_cap = â, Î_t = 1/365, f = 2880 | baseline simulation only | `analysis-block-rewards.md:88-97` |
| APY 20% â 3.33% as stake goes 5% â 30% | Table 1, computed as I_max/SecurityLevel | `analysis-block-rewards.md:143` |
| min stake = 0.001% Ã S_TGE (bound 0.015%) â 1,000 LGO | Informational; and under that doc's own S_TGE = 1e8 | `analysis-static-minimum-stakeâ¦:60`, `:116`, `:122` |
| r_stake = 15%, N_stakers = 1000 | inputs to that derivation | same, `:93`, `:97` |
| S_TGE = S_max = 100,000,000 LGO | that document's assumption, contradicts `block-rewards.md:160` | same, `:151-152` |
| inferred_total_stake = 23.5B "as in Cardano" | error-analysis assumption | `cryptarchia-proof-of-leadership.md:255` |
| q = 0.85 honest slot utilization | estimator-bias example | `analysis-total-stake-inference.md` |
| 6,664 lepta claim fee | stated at the markets' RESTING level of 7, giving 306 bytes and 646 gas; **and computed with one price for both markets, which `storage-markets.md:126` contradicts by 10⁹** | `mantle:1858` |
| ~3 hours/core per PoW solution; "a few thousand cores" for target rate | prose calibration, "target machine" undefined | `mantle:1903` |

### 2.8 UNSET â the simulator must supply a value

| Quantity | Why it matters | Where the gap is |
|---|---|---|
| **S_cap** | supply hard cap; introduced *"if any"*, never valued | `block-rewards.md:132` |
| **min_stake.stake_threshold** | admission gate for the entire service stream | `bedrock-service-declaration-protocol.md:88-96`; `mantle:1119` |
| **F_C, R_C** â Q_C^Total â Ï â Îµ â A_Îµ | without these the *probability an honest provider is paid at all* is not computable | `blend-protocol.md:461`, `:466` |
| **P_STR(0)** | *"Set to a pre-determined value established by genesis governance"* | `storage-markets.md:231` |
| **genesis token distribution** | hence the numeric D_GENESIS | `bedrock-genesis-block.md:317` |
| **leaders_rewards at genesis** | no seed stated; only `pow_reward_pool` is seeded | absent from `mantle`, `bedrock-genesis-block.md:296-301` |
| **encoded byte size** of claim / leader-claim transactions | half of their fee; `ClaimPowReward` absent from the encoding spec entirely | `mantle-transaction-encoding.md:65-74` |
| **moving-average warm-up** | Î³_t is undefined for t < 119 | `block-rewards.md:305` |
| **burned-fee window at genesis** | initial contents of `burned_fees_window` | â |
| **voucher claiming policy** | no expiry â the per-share value depends entirely on claimant behaviour | `bedrock-anonymous-leaders-reward.md:102` |
| **size semantics of P** | argmin set (typically 1) or top-k? | `blend-protocol.md:1116` vs `:277` |
| **residue of the 60/40 split** | the two floors do not sum to the total | `block-rewards.md:497-498` |
| **fate of Blend income when the gate fails or B = 0** | no `blend_reward_pool` state variable exists | absent from `mantle` |

---

## 3. What the specification does not determine

Ranked by how much a simulator's output moves with the assumption.

**1. The validator yield itself.** See Â§4.1. Two readings of the same parameter set differ by 2.5Ã in leader APY. Everything downstream â participation, the stake trajectory, hence D, hence A_t, hence emission â depends on which one is modelled.

**2. Voucher claiming policy.** No expiry, and the denominator counts every unclaimed voucher since genesis (`overview-cryptoeconomics.md:63`). The per-share value is therefore set entirely by an unmodelled behaviour. *(DERIVED: with a stationary backlog it tends to (0.4Â·Î£ block rewards + Î£ tips)/21,600 per epoch; if leaders delay, the backlog grows and the per-share value falls below this while total value per leader is preserved.)* The only hint is a soft one: *"The marginally larger reward of the late claimants also mildly encourages leaders to spread their claims over time"* (`bedrock-anonymous-leaders-reward.md:102`).

**3. The activity-lottery acceptance rate.** With F_C and R_C unset, the fraction B/N of honest providers that get paid is a free parameter. Since R = I/(B+P), this directly scales every provider's income. There is no stated target acceptance rate.

**4. The minimum stake.** Unset in normative text. It is the sole Sybil defence for a reward that is **flat per declaration** â *(DERIVED: splitting stake across many threshold-meeting declarations multiplies the reward, since uniqueness is enforced only per (service, provider_id) and per (service, zk_id), and there is no provider cap.)* A simulator's answer to "how many Blend providers are there" is essentially the answer to "how low is the threshold."

**5. The fee process.** D_1,t drives (1âA_t)Â·R_block, which is the *whole* block reward once the stake target is reached. `execution-market.md:222-229` gives RÌ_burned(s) = Î£ g_tÂ·b_exec[s] and the base-fee dynamics, but transaction demand â g_t and the arrival process â is exogenous. In the mature regime the entire reward system is a function of an unspecified input.

**6. Whether supply increases at block time or epoch time.** `block-rewards.md` speaks of amounts minted *per block*; `overview-cryptoeconomics.md:154-172` credits the pools only at the epoch boundary. A supply-tracking simulator must choose.

**7. Genesis initial conditions.** D_GENESIS is a rule without a numeral; `leaders_rewards` has no stated seed; the burned-fee window has no stated initial contents; the moving average has no warm-up rule.

**8. Reorg semantics.** Nothing states how A_t is carried across a reorganisation, whether the burned-fee window follows the chain or the node's local view, or whether vouchers from orphaned blocks enter the anonymity set. Relevant because the spec itself says simultaneous lottery winners produce guaranteed forks (`cryptarchia-v1-protocol.md:232`).

**9. Whether the PoW diversion is inside or outside D_1,t.** Stated only as prose in one document (`overview-cryptoeconomics.md:195`). `block-rewards.md` contains no mention of proof of work at all.

**10. Hashrate â solution rate.** Only prose calibration; the "target machine" is undefined. PoW claim volume, and therefore the difficulty controller's trajectory, is a free input.

**11. Determinism gaps in the service payout.** No rounding rule for R; no rule for the residue of I mod (B+P); no rule for the 60/40 flooring residue.

**12. Multi-service apportionment.** `serviceReward` and `Rewards_Epoch` are written for N services; only one exists and only one split is specified.

---

## 4. Contradictions between documents

Stated as contradictions. Not reconciled.

### 4.1 The APY contradiction â *the load-bearing one*

**Document A.** `block-rewards.md:167` justifies I_max = 1% thus: *"This value guarantees that, when the total inferred stake reaches D_0,target, then the APY for validation is ~3.33%."* `analysis-block-reward-parameter-calibration.md:152` repeats it at 3.34%. `analysis-block-rewards.md:150` gives the arithmetic explicitly:

$$\text{APY} = \frac{I_{max}\times S_{tge}}{D_{0,target}} = \frac{I_{max}}{\text{Security Level}} = \frac{1\%}{30\%} = 3.33\%$$

and `analysis-block-rewards.md:166`: *"The reward per validator is proportional to the size of the validator's stake with respect to the total stake."* This formula has **no split factor in it**. It assumes the entire annual emission, 1e8 LGO, accrues to the 3e9 LGO of stake.

**Document B.** `overview-cryptoeconomics.md:144-145`: *"40% for the leader. 60% for the Blend service."* `block-rewards.md:498` implements it. `execution-market.md:62` corroborates it.

**Both cannot hold.**

| | Reading A (whole emission to validators) | Reading B (40/60 split) |
|---|---|---|
| Annual emission at A_t = 1 | 1e8 LGO | 1e8 LGO |
| To leaders | 1e8 LGO | 4e7 LGO |
| Leader APY on 3e9 staked | **3.33%** | **1.33%** |
| To Blend | 0 | 6e7 LGO |
| Blend payment basis | â | **flat per active node**, not per stake â so it is not a yield on capital at all; it is a per-node fee gated by a minimum stake |
| I_max that would deliver 3.33% to leaders | 1% | **2.5%** |

Consequence for a simulator: under Reading B the parameter that was chosen to hit 3.33% delivers 1.33%, and the participation incentive that the whole stake-KPI control loop is built around is 2.5Ã weaker than the calibration assumed. The stake trajectory, hence D, hence Î´_t, hence A_t, hence emission â the entire loop â sits on this.

There is also a **third inconsistency inside Reading A itself.** At D_0,t = D_0,target we have Î´_t = 0, so A_t = Î±_aÂ·Î³_t/I_max â driven purely by the burn. If the annualized burn rate is below 1% of S_tge, A_t < 1 and the minted emission is *less* than 1e8 LGO; at zero burn A_t = 0 and minted emission is zero, with the block reward reduced to a pure recycling of that block's burnt fees. The "3.33% APY at the target" figure is computed as if A_t were still 1 at the target, which the control function contradicts. The APY table is valid strictly *below* target and discontinuous with the mechanism *at* it. `analysis-block-rewards.md:137` half-concedes this â *"this section only evaluates the APY within the range [0, D_0,target]"* â but `block-rewards.md:167` states the 3.33% as holding *when* the target is reached.

### 4.2 Î±_d: 1/4 versus 1/6

`block-rewards.md:163` and `:389` specify **1/4**, and cite `analysis-block-reward-parameter-calibration.md` as the justification. That document, at `:80`, says: *"The value Î±_d = 1/6 is chosen so that when the total inferred stake is off target by 16.6%â¦ the system starts moving from the maximum inflationary regime to the regime driven by the burned fees."*

The normative integer form is built on 1/4: adopting 1/6 changes `A_SCALE` from 12e7 to 18e7 and the transition band from 4% to 6% of the target.

**Neither value reproduces the stated rationale.** A_t leaves saturation at Î´_t = I_max/Î±_d, which is **4%** at Î±_d = 1/4 and **6%** at Î±_d = 1/6 â not the 16.6% claimed. The likely root cause is a units disagreement: `analysis-block-reward-parameter-calibration.md:43` says *"Î´_t is measured in percentage units"*, while `block-rewards.md:265-268` defines Î´_t as a dimensionless ratio and `:412-424` substitutes it as a raw fraction. Under the percentage reading A_t would be saturated essentially always, so the fraction reading is the only workable one â and the 16.6% figure fits neither.

### 4.3 D at genesis versus the bootstrap narrative

`bedrock-genesis-block.md:317`: *"D: The initial estimate of total stake will be the total tokens distributed at genesis."* That is on the order of the full launch supply, ~1e10 LGO â **more than 3Ã above** D_0,target = 3e9.

`block-rewards.md:357`: *"when the blockchain starts, D_{0,t}|_{t=0} is very likely a small number compared to the target. Therefore, the equation above tilts towards 1."*

Under the genesis rule, Î´_t at genesis â â2.33, A_t clamps to **0**, and the chain opens in the pure fee-recycling regime â the exact opposite of the bootstrap story, and the opposite of the entire APY-attracts-validators argument in `analysis-block-rewards.md:155-160`. A simulator that seeds D low will reproduce the intended curve for the wrong reason.

### 4.4 Service payout lag: e+2 versus eâ1

Three statements say the epoch-N reward is paid in the first block of epoch **N+2**: `bedrock-service-reward-distribution.md:49`, `overview-cryptoeconomics.md:65`, `overview-cryptoeconomics.md:139`, plus `blend-protocol.md:1136`. One statement says one epoch: `overview-cryptoeconomics.md:228` â *"When a new service epoch e starts, rewards for the previous epoch eâ1 are calculated and directly inserted in the ledger."* The dissent is internal to the Informational overview; the Standards Track SRDP says e+2.

### 4.5 Execution tips: 100% to leaders, or split 60/40?

`overview-cryptoeconomics.md:170-171` adds tips to `leader_rewards` **after and in addition to** the 40% share â leaders get all of them. `execution-market.md:62`: *"The priority_feeâ¦ is directed into the block builders reward stream. 40% of the rewards will be allocated to block builders and the remaining 60% to Blend nodes"* â which on one reading applies the split to tips as well, moving 60% of all tips to Blend.

### 4.6 Per-block integer split versus per-epoch float split

`block-rewards.md:497-498` floors each share **per block** on the reward numerator. `overview-cryptoeconomics.md:158-171` sums `0.6 * get_block_rewards(b)` and `0.4 * â¦` in real arithmetic over the epoch. Summing floored per-block shares â  flooring the summed share; over 21,600 blocks an epoch the divergence is up to ~21,600 units per pool. Neither document says which is normative.

Additionally, the two floors do not sum to the total: the shortfall against the exact rational total is strictly less than 2 units, i.e. at most 1 whole unit below âtotalâ. The spec is explicit about the residue for the leader pool (`bedrock-anonymous-leaders-reward.md:102`, stays in the pool) and for the PoW diversion (`overview-cryptoeconomics.md:187`, burnt) â and silent here.

### 4.7 Units: LGO or lepta?

`mantle:2119`: *"The indivisible unit is the leptonâ¦ `TokenValue` counts lepta: every quantity of that type â note values, balances, fees, prices and pool balances â is an integer number of lepta."* But `block-rewards.md`'s reference implementation works in **LGO**: `STAKE_TARGET = int(3e9)` is 3 billion *LGO* (`:165`), and 62500/657 is ~95 *LGO* per block (`mantle:2123` confirms it is LGO). A_tâ² is dimensionful â it adds `3e9 â D_0,t` to `10512Â·Î£ D_1,Ï` and compares against 12e7 â so `total_stake` and `burned_fees_window` must be in the **same unit as the literal 3e9**. If those inputs arrive as `TokenValue` lepta, `STAKE_TARGET` must be 3e18 and `A_SCALE` 12e16. **No conversion rule is specified anywhere.** A simulator that feeds lepta into `block_reward()` unchanged is wrong by 10â¹.

### 4.8 The storage-price floor: 1 LGO or 1 lepton?

`storage-markets.md:224`: *"Rounding upwards makes 1 LGO per Permanent Storage Gas the effective floor of the price."* `mantle:2119`: *"both fee markets price in whole lepta per unit of gas and can never go below one."* A factor of 10â¹. The Mantle statement is the later and more explicit one, but the conflict is unresolved in the text.

### 4.9 S_TGE: 1e10 or 1e8?

`block-rewards.md:160` gives 10 billion LGO. `analysis-static-minimum-stakeâ¦:151-152` assumes `S_TGE = S_max = 100,000,000 LGO` (and its own `:75`/`:77` use 10 million / 1 million as examples). The derived minimum stake of 0.001% Ã S_TGE is therefore 1,000 LGO under the analysis and 100,000 LGO under `block-rewards.md`.

### 4.10 ServiceType naming

`bedrock-service-declaration-protocol.md:80-82` and `mantle:1016-1017` define `ServiceType.BN`. `bedrock-genesis-block.md:102`, `:258` construct declarations with `ServiceType.BLEND`. This is not cosmetic: the service payout `op_id` is `hash(ServiceType || epoch_number)`.

### 4.11 `p` is defined nowhere it is pointed to

`mantle:1634` refers the reader to *Common Cryptographic Components* for the scalar field modulus. `common-cryptographic-components.md:133` names BN254 but **states no modulus**. The only numeric value in the tree is `cryptarchia-proof-of-leadership.md:219`.

---

## 5. Implementation notes

### 5.1 Every flooring site, and what happens to the residue

| Site | Expression | Residue |
|---|---|---|
| PoW pool refill, **per block** | âfees_b Â· 10 / 100â | **burnt** (`overview:187`) |
| PoW per-claim reward, per epoch | âpool Â· 1 / 43,200,000â | **stays in the pool** (`mantle:1791`) |
| PoW difficulty retarget, per block | â100Â·target / (c+90)â, **arbitrary precision** | n/a |
| PoW pool decrement | exact, no flooring | n/a |
| Block reward 60% split, per block | `num*6 // (den*10)` | **UNSPECIFIED** |
| Block reward 40% split, per block | `num*4 // (den*10)` | **UNSPECIFIED** |
| Leader per-voucher share, per claim | âpool / unclaimedâ | **stays in `leader_rewards`** (`:102`) |
| Service reward R = I/(B+P) | **no rounding rule given** | **UNSPECIFIED** â determinism gap |
| Block reward â lepta | round down, <1 lepton/block (`mantle:2123`) | lost |
| Execution base fee update | **ceil**, floor 1 (`execution-market.md:206`) | â |
| Storage price update | **ceil**, floor 1 (`storage-markets.md:224`) | â |
| Storage usage EMA | **floor** â deliberately opposite to the price | â |

A_t itself is **never materialised as an integer.** The integer form keeps it as the exact rational A_tâ²/12e7 and rounds only at the final reward division. The spec never says this in words.

### 5.2 Which snapshot each value is read from

| Value | Read from |
|---|---|
| â_LEAD (eligible notes) | commitment root at slot (epâ1)Â·EPOCH_LENGTH â *start of the previous epoch* |
| Î· (epoch nonce) | slot sl_{epâ1} + â6k/fâ |
| D (inferred total stake) | block count in the **first 6âk/fâ slots of epoch epâ1**; in force for the whole of epoch ep |
| SDP provider set | last block of `current_epoch â 2` |
| voucher Merkle root for claims | **frozen** at the start of the current epoch (`mantle:1489`) |
| leader per-share amount | **recomputed at claim execution**, *not* frozen (`bedrock-anonymous-leaders-reward.md:91-98`) |
| `epoch_pow_reward` | **frozen** at the epoch boundary (`mantle:1820`) |
| `difficulty_reward` | produced by the **previous** block's update (`mantle:1887`) |
| burned-fee window Î³_t | last 120 blocks **including the current one** |
| D_1,t for the recycling term | **the current block** â no lag |

### 5.3 What lags what

- **PoW pool refill:** one full epoch. Fees of eâ1 fund the pool used in e.
- **PoW difficulty:** one block.
- **PoW solution validity:** dies at the epoch boundary; but can be pre-mined from the moment the next epoch's nonce is public, part way through the preceding epoch.
- **Leader pool credit:** at the start of e+1 for blocks of e. Lag from one block to one full epoch.
- **Service reward:** two epochs (15 days), work in N â Active in N+1 â paid first block of N+2.
- **Service declaration:** up to two epochs before the declaration is visible.
- **Stake KPI D:** 0.4 to 1.0 epochs of dead time (mean 0.7 epochs = 5.25 days) between observation and effect. Plus 5 epochs to steady state and 2 epochs to recover from a shock. This is the control loop's dominant dead time and it is not stated anywhere in the spec.
- **Burn KPI:** zero lag, 120-block moving average.

### 5.4 Where a naive reading goes wrong

- **The two symbols named `f` are different quantities.** `block-rewards.md:169` f = 1 (blocks per Î_t); `cryptarchia-v1-protocol.md:94` f = 1/30 (slot activation coefficient). Neither document flags the collision. Confusing them misscales emission by 30Ã. Worse, block-rewards' f is not even single-valued: `:137-139` shows the same symbol taking 2880 and 21600 for other time steps.
- **`I` is not `Rewards_Epoch`.** `I = 0.6 Ã Rewards_Epoch`. Feeding the total epoch reward into R = I/(B+P) overstates the service stream by 1.67Ã.
- **The block reward's fee input is net of the PoW diversion.** Feed `0.9 Ã collected_fees` into `burned_fees_window`, not gross. Overstating it inflates the recycled term by ~11% in the mature regime. Stated only in prose, `overview-cryptoeconomics.md:195`; `block-rewards.md` never mentions PoW.
- **The leadership win probability's leading coefficient is âln(1âf) = 0.033901, not f = 0.033333.** Seeding a simulator with fÂ·v/D produces a block rate ~1.7% below what the specified t_0 delivers.
- **`t_1` is stored as p â |t_1|.** The real-valued threshold is vÂ·t_0 â vÂ²Â·|t_1|. A simulator that treats t_1 as positive gets the parabola upside-down and misses the v â« D wrap-around entirely.
- **The stake estimator is biased low by construction.** â0.847Ã true stake at f=1/30, q=0.85. This is a *permanent* positive Î´_t and therefore permanent extra emission â an equilibrium property, not a transient.
- **The transaction-count limit binds first, and `MAX_BLOCK_TXS` is the operative cap.** *(WITHDRAWN, and reversed. An earlier revision inferred a ~6,018-byte claim transaction by decomposing the 6,664-lepta fee at a price of 1, and concluded that 1 MB capped a block at ~170 claims rather than at `MAX_BLOCK_TXS` = 1024. The decomposition is wrong on two counts. The fee is stated at the markets' RESTING level, which is 7 rather than 1 -- the downward step has fixed points across the first several units, so an idle market settles at 7 -- and 6,664 = (306 + 646) * 7 exactly. And 6,018 bytes is implausible on its face: `ClaimPowRewardOp` carries three 32-byte fields, so the Operation is 96 bytes and the envelope and signature bring the transaction to roughly 306. At 306 bytes 1 MB holds ~3,400 claims, so the count limit binds at 1024 and the spec's "impossible by construction" margin is exactly as claimed rather than larger.)*
- **The PoW `max(1, â¦)` in the retarget is dead code** at the specified constants. Do not treat it as a live branch.
- **The leader claim's effect differs between documents.** `bedrock-anonymous-leaders-reward.md:112` says *"Increase the balance of the Mantle Transaction by the share amount"* (a balance credit consumable by other Operations in the same transaction â this is what makes the atomic self-spend at `:85` work). `mantle:1519-1526` says construct a single output note and insert it into the Ledger. These differ for UTXO-count modelling.
- **The genesis voucher.** `bedrock-genesis-block.md:201` sets it to 0 *"as there is no leader block reward for the initial block"*, and `:290` says header processing is skipped for genesis â which resolves the question, since the voucher append at `bedrock-v1.1-block-construction.md:241` is part of block execution. Admitting a zero leaf would permanently inflate the denominator by 1 and strand one share forever.
- **Do not copy the reference implementations verbatim.** Known transcription defects: `block-rewards.md:222` (`R_block_cur` undefined; parameter is `D_1_t`); `:287` (`weight * deviation value`, syntax error); `:323` (asserts against `kpi_deviations`, not a parameter of that function); `:494` (`a_num` undefined, invalid line continuation); `:152` (states the per-step emission as `A_tÂ·I_maxÂ·Î_t`, omitting S_tge â contradicts `:185-187`). And `cryptarchia-total-stake-inference.md:63-83` will not compile: `const PRECISION: u64 = 1e3` assigns a float literal, and lines 77â78 mix u64 and i128 without casts. The arithmetic intent is unambiguous in every case.
- **`WINDOW`, `EPOCH_POW_DISTRIBUTION_RATE`, and `EPOCH_LENGTH` are not greppable constants.** `WINDOW` is defined only by a LaTeX relation and a prose value; `EPOCH_POW_DISTRIBUTION_RATE` exists only as `_NUM`/`_DEN`; `EPOCH_LENGTH` is prose in Cryptarchia and a symbol only in the epoch-state pseudocode.

### 5.5 Derived numbers a simulator can check itself against

- âk/fâ = 64,800 slots. EPOCH_LENGTH = 648,000 slots = 7.5 days. 48.667 epochs/year. PERIOD = 388,800 slots; expected blocks in the observation window = 12,960.
- 62500/657 = 95.1294â¦ LGO/block; Ã 1,051,200 blocks/yr = exactly 1e8 LGO/yr = 1% of S_tge.
- Emission saturation band in stake terms: A_t = 1 at D_0,t â¤ 2.88e9; A_t = 0 at D_0,t = 3.0e9 (holding Î³_t = 0). Band width 1.2e8 LGO â numerically equal to `A_SCALE`, which is a useful consistency check that the integer form is in LGO.
- Burn-side saturation: Î£ over the 120-block window of D_1,Ï â¥ 12e7/10512 â 11,415 LGO saturates A_t on its own, i.e. a sustained burn of 1e8 LGO/yr. Note this sits in tension with `analysis-block-reward-parameter-calibration.md:96`: *"As a consequence of the parametrization, specifically Î±_a = 1, the emission rate I_t never reaches the maximum value"* â true of that document's stochastic example, not of the mechanism.
- Service stream at A_t = 1, zero fees: 21,600 Ã 95.1294 Ã 0.6 â **1,232,877 LGO/epoch â 60.0 million LGO/yr = 0.6% of S_tge**. At the 32-provider floor with P = 1 and all active, â 37,360 LGO per provider per epoch; at 1,000 providers, â 1,232 LGO per provider per epoch.
- PoW: genesis pool = 0.005 Ã 1e19 = 5e16 lepta â opening reward â5e16/43,200,000â = **1,157,407,407 lepta â 1.157 LGO**. Pool settles at 1/Ï = 200 epochs â 4 years of distribution. At zero claims the target eases by 10/9 per block, so recovery from a 100Ã-too-hard target takes log(100)/log(10/9) â 44 blocks â 22 minutes â matching the spec's "corrects itself within an hour" (`mantle:1901`). The over-permissive direction is spec-stated: a hundredfold-too-easy genesis target costs ~1,200 extra claims over ~20 blocks, ~3Ã10â»âµ of the genesis pool.
- Claim transaction execution gas = 56 + 590 = 646. The stated 6,664-lepta fee decomposes as (306 + 646) * 7 at the markets' resting level, giving an encoded size of **306 bytes** -- consistent with a 96-byte `ClaimPowRewardOp` (three 32-byte fields) plus envelope and signature. The earlier reading, 6,018 bytes at a price of 1, is withdrawn: it is implausible against the stated payload and assumes the floor rather than the resting level.
- **`mantle:1858` prices both gas markets at 7, while `storage-markets.md:126` prices permanent storage at 1 LGO per byte.** These disagree by nine orders of magnitude, and it is the sharpest contradiction in the tree: both are Standards Track and one of them is this mechanism's own document. It is not presentational. At 1 LGO/byte the claim fee is 306 LGO against a 1.157 LGO opening reward, which violates the affordability bound `mantle:1858` states on ITSELF by 264x, so no miner reaches the bond and the mechanism does not start. The simulator prices the two markets separately, as the tree requires, and runs at 1e-3 LGO/byte -- the largest round value satisfying `storage-markets.md`'s own requirement that the price be "sufficiently low so as not to suppress early adoption". See `CONTRADICTIONS.md` section 4.8.
- The `mantle:1858` "twice the fee" claim does not check out: it states the opening reward exceeds twice the claim's fee for fee â¤ 1.157Ã10â»Â¹â° of launch supply, but 1.157Ã10â»Â¹â° Ã 1e19 = 1.157e9 lepta, which *is* the opening reward, not half of it. Either the threshold is the one-times-fee threshold mislabelled, or a different reward is meant. Not reconciled here.",
    "streams": [
      {
        "stream": "emission",
        "formula": {
          "stream": "Block reward per block and the emission-rate-factor control function A_t (including the inferred-total-stake KPI D and its lag)",
          "formula": "=== 1. TOTAL MINTED PER BLOCK â block-rewards.md:193-197 (equation (1)) ===

$$
\begin{equation}
A_t \cdot \dfrac{I_{max} \cdot S_{tge} \cdot \Delta_t}{f} + (1-A_t) \cdot R_\text{block}
\end{equation}
$$

with (block-rewards.md:199-206):
- $`A_t`$ is the emission rate factor on a per year basis.
- $`I_{max}`$ is the maximum emission rate per year.
- $`S_{tge}`$ denotes the token supply at Token Generation Event (TGE).
- $`\Delta_t`$ denotes the fraction of year in one time step per e.g., epoch, block, or day.
- $f$ be the average number of block proposal within $`\Delta_{t}`$ units.
- $`R_\text{block} = D_{1,t}`$ denotes the total amount of Execution base fees and Storage fees that are burned when the block is proposed.

Reference pseudocode, block-rewards.md:208-224 (reproduced verbatim, including its bug â `R_block_cur` is undefined; the parameter is named `D_1_t`):

```python
def block_rewards(
    S_tge:float,
    emission_rate_factor:float,
    I_max:float,
    Delta_t:float,
    f:float,
    D_1_t: float
) -> float:
    """
    Calculate the rewards per block.
    It implements equation (1).
    """
    emission_from_inflation = emission_rate_factor * I_max * S_tge * Delta_t / f
    emission_from_rewards = (1. - emission_rate_factor) * R_block_cur
    return emission_from_inflation + emission_from_rewards
```

Note: only the FIRST term is newly minted. The pure-inflation emission within a time step is stated separately at block-rewards.md:185-187 as
$$
A_t \cdot I_{max} \cdot S_{tge} \cdot \Delta_t.
$$

=== 2. THE EMISSION RATE FACTOR FUNCTION â block-rewards.md:228-232 (restated identically at 382-384) ===

"The emission rate factor $`A_t \in [0,1]`$ determines the portion of $`I_{max}`$ that should be emitted based on current values of $`\delta_t`$ and $`\gamma_t`$:"

$$
A_t = \min \lbrace 1, \max \lbrace 0, \dfrac{ \alpha_d \cdot \delta_t + \alpha_a \cdot \gamma_t + I_{min}}{I_{max}} \rbrace \rbrace.
$$

"All terms are displayed in annualized form to ease comparison." (block-rewards.md:243)

Reference pseudocode, block-rewards.md:245-259:

```python
def calculate_emission_rate_factor(
    alpha_dev:float,
    weighted_target_deviation: float,
    alpha_avg:float,
    weighted_avg: float,
    i_min: float = 0.0,
    i_max: float = 0.01
) -> float:
    """It calculates the current emission rate factor"""
    emission_rate:float = alpha_dev * weighted_target_deviation + alpha_avg * weighted_avg + i_min
    emission_rate_factor:float = emission_rate / i_max
    emission_rate_factor = min(1.0, max(emission_rate_factor, 0.0))
    return emission_rate_factor
```

=== 3. KPI DEVIATION FROM TARGET (delta_t) â block-rewards.md:263-268 ===

"The weighted deviation from target"
$$
\delta_t = \sum_i w_i \times 
\dfrac{D_{i,target} - D_{i,t}}{D_{i,target}}.
$$

Gating note, block-rewards.md:298: "> To measure the deviation, only the total estimated stake KPI is used in this part of the computation"

Sign convention, block-rewards.md:294-296:
- $`\delta_t \gt 0`$ â KPI below target â should increase the token emission by a factor of $`\alpha_d \cdot \delta_t`$.
- $`\delta_t = 0`$ â KPI at target â should not change the token emission.
- $`\delta_t \lt 0`$ â KPI above target â should reduce the token emission by a factor of $`\alpha_d \cdot \delta_t`$.

Reference pseudocode, block-rewards.md:270-290 (reproduced verbatim; line 287 `weighted_target_deviation += weight * deviation value` is a syntax error in the spec):

```python
def weighted_deviation_from_target(
    kpi_weights: List[float],
    kpi_deviations: List[float]
) -> float:
    """
    Calculate the normalized deviation (delta_t).
    ...
    """
    assert len(kpi_weights) == len(kpi_deviations)

    weighted_target_deviation:float = 0.0
    for deviation, weight in zip(kpi_deviations, kpi_weights):
        weighted_target_deviation += weight * deviation value

    return weighted_target_deviation
```

=== 4. KPI AVERAGE (gamma_t) â block-rewards.md:302-311 ===

"The weighted average metric is defined as"
$$
\gamma_t = \dfrac{1}{\Delta_t} \sum_i w_i \cdot \Bigl(\dfrac{1}{T}  \sum_{\tau=t-T+1}^t \dfrac{ D_{i,\tau}}{D_{i,target}} \Bigr).
$$
"where:
- The value $`D_{j,target}`$ can be any number with the same units of $`D_{j,i}`$.
- The factor $`\dfrac{1}{\Delta_t}`$ turns $`\gamma_t`$ into an annualized quantity. This depends on the specific KPI."

Gating note, block-rewards.md:338: "> To measure the average, only the average burning rate KPI is used in this part of the computation"

=== 5. THE TWO KPIs â block-rewards.md:342-374 ===

KPI 1 (block-rewards.md:346-349):
- $`D_{0,t}`$ denotes the evolution of the inferred total stake.
- $`D_{0,target}`$ denotes the total stake that is considered secure. For the blockchain to be secure, we aim for $30\%$ of the TGE supply.
Security level (block-rewards.md:361-363): $$\text{Security Level} = \dfrac{D_{0,target}}{S_{tge}}.$$

KPI 2 (block-rewards.md:369-372):
- $`D_{1,t}`$ denote the amount of Storage fees and Execution base fees burned since $t-1$.
- $`D_{1,target}=S_{tge}`$ denote the "normalizing factor" (it is the TGE supply, in this case).

=== 6. NORMATIVE INTEGER FORM â block-rewards.md:376-501 ===

Preamble (block-rewards.md:378): "Because block rewards affect consensus state, the implementation must be fully deterministic across all nodes. For that reason, the normative implementation of the reward function should not rely on floating-point arithmetic ... the consensus rule itself should be defined only in terms of integer arithmetic."

Substituting the specified constants (block-rewards.md:388-397: alpha_d=1/4, alpha_a=1, I_max=1e-2, T=120, f=1, R_block=D_{1,t}, D_{0,target}=3e9, D_{1,target}=S_tge=1e10, Delta_t=1/(365*2880)), block-rewards.md:437-439 gives:

$$
A_t=\min\!\lbrace1,\max\!\lbrace0,\quad \frac{3\cdot 10^9-D_{0,t}+10512\sum_{\tau=t-120+1}^{t}D_{1,\tau}}{12\cdot 10^7}\rbrace\rbrace.
$$

and block-rewards.md:443-451:
$$
\begin{aligned}
A_t'
&=
\min\!\lbrace12\cdot 10^7,\max\!\lbrace0,\quad3\cdot 10^9-D_{0,t}+10512\sum_{\tau=t-120+1}^{t}D_{1,\tau}\rbrace\rbrace,
\\
A_t&=\frac{A_t'}{12\cdot 10^7}.
\end{aligned}
$$

with the per-block inflation constant (block-rewards.md:462-464):
$$
\frac{I_{\max} \cdot S_{\mathrm{tge}}\cdot \Delta_t}{f}=\frac{10^{-2}\cdot 10^{10}}{365\cdot 2880}=\frac{10^8}{1051200}=\frac{62500}{657}.
$$

and the total reward (block-rewards.md:468-473):
$$
\text{Rewards}_t=
\frac{A_t'}{12\cdot 10^7} \cdot \frac{62500}{657} + (1-\frac{A_t'}{12\cdot 10^7})\cdot D_{1,t} =\\
\frac{62500\cdot A_t' + 657\cdot(12\cdot 10^7-A_t')\cdot D_{1,t}}{657\cdot 12\cdot 10^7}
.
$$

Reference implementation, block-rewards.md:477-501 (reproduced verbatim, including its bugs: `a_num` is undefined â it should be `a_numerator`; the line continuation on 493-494 is not valid Python as written; and the numerator on 471 multiplies 62500 by A_t' only, i.e. the first term is NOT multiplied by D_{1,t}):

```python
A_SCALE = 120_000_000            # denominator of 1/(I_max * D1_target * Delta_t * T) 
INFLATION_NUMERATOR = 62_500     # numerator of I_max * S_TGE * DELTA_t / f
INFLATION_DENOMINATOR = 657      # denominator of I_max * S_TGE * DELTA_t / f
FEE_AVG_NUMERATOR = 10_512       # numerator of 1/(I_max * D1_target * Delta_t * T) 
STAKE_TARGET = int(3e9)

def block_reward(total_stake: int, burned_fees_window: list[int]) -> tuple[int, int]:
    sum_fees = sum(burned_fees_window)
    last_burned_fee = burned_fees_window[-1]

    a_numerator = min(
        max(STAKE_TARGET + FEE_AVG_NUMERATOR * sum_fees - total_stake, 0),
        A_SCALE
    )

    reward_numerator = INFLATION_NUMERATOR * a_numerator
                                           + INFLATION_DENOMINATOR * (A_SCALE - a_num) * last_burned_fee
    reward_denominator = INFLATION_DENOMINATOR * A_SCALE

    blend_reward = reward_numerator * 6 // (reward_denominator * 10)
    leader_reward = reward_numerator * 4 // (reward_denominator * 10)

    return blend_reward, leader_reward
```

=== 7. HOW THE INFERRED TOTAL STAKE D IS COMPUTED â cryptarchia-total-stake-inference.md:59-83 ===

"For a current epoch's estimate `total_stake_estimate` and the epoch's first slot `epoch_slot`, the next epoch's estimate is calculated as shown below:"

```rust
const PRECISION: u64 = 1e3
fn total_stake_inference(total_stake_estimate: u64, epoch_slot: u64) -> u64 {
    // f: f64
    // PERIOD: u64
    // density_over_slots(u64, u64) -> u64

    let beta_p: u64 = truncate(beta * PRECISION)
    let f_p: u64 = truncate(f * PRECISION)
    let tse_p: u64 = total_stake_estimate * PRECISION

    let measured_density_p: u64 = density_over_slots(epoch_slot, PERIOD) * PRECISION
    let expected_density_p: u64 = PERIOD * f_p
    let density_diff_p: i128 = (expected_density_p as i128) - (measured_density_p as i128)
        let slot_activation_error_p: i128 = (tse_p * density_diff_p) / (expected_density_p as i128)
        let correction_p: i128 = (beta_p * slot_activation_error_p) / PRECISION;
        let new_total_stake_estimate = (tse_p - correction_p) / PRECISION;

        max(new_total_stake_estimate, 1) as u64
}
```

with $`\textbf{density\_over\_slots}(s, p)`$ = "Returns the number of blocks produced in the $`p`$ slots following slot $`s`$ in the honest chain." (cryptarchia-total-stake-inference.md:56-57)

=== 8. THE LAG ON D â cryptarchia-v1-protocol.md:196-228 ===

$`\text{define } \textbf{compute\_epoch\_state}(ep, tip \in T)\to(\mathbb{C}_\text{LEAD}^{ep},\eta^{ep},D^{ep})`$ :
  $`\textbf{case}\space ep = 0:`$   $`\textbf{return}\space (\mathbb{C}_\text{GENESIS}, \eta_\text{GENESIS}, D_\text{GENESIS})`$
  $`\textbf{otherwise}:`$
    $`sl_{ep-1} \coloneqq (ep-1) \cdot \text{EPOCH\_LENGTH}`$
    $`(\_,\_,D^{ep-1}) \coloneqq \textbf{compute\_epoch\_state}(ep-1,tip)`$
    $`N_\text{BLOCKS}^{ep-1} \coloneqq |\{B \in T | sl_{ep - 1} \le sl_B \lt sl_{ep-1}+\lfloor 6\frac{k}{f} \rfloor\}|`$
    $`D^{ep} \coloneqq \textbf{infer\_total\_active\_stake}(D^{ep-1}, N_\text{BLOCKS}^{ep-1})`$
    $`\textbf{return}\space (\mathbb{C}_\text{LEAD}^{ep}, \eta^{ep}, D^{ep})`$

and cryptarchia-v1-protocol.md:156: "$`D`$ | Inferred Total Stake (Lottery Difficulty) | Total stake inferred from watching the results of the lottery during the course of the epoch. $`D`$ is used as the stake relativization constant for the following epoch."

and cryptarchia-v1-protocol.md:142: "Lottery Constants Finalization | $`s+\lfloor\frac{k}{f}\rfloor=4\lfloor\frac{k}{f}\rfloor`$ slots | On the $`2s^{th}`$ slot into the epoch, the epoch nonce $`\eta`$ and the inferred total stake $`D`$ can be computed. We wait another $`4\frac{k}{f}`$ slots for these values to finalize."",
          "citations": [
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:90-92 (high-level block reward equation)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:127-146 (Core Variables)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:156-172 (Parametrization table)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:183-187 (emission from inflation within a time step)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:193-197 (equation (1), the block reward)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:199-206 (symbol list for eq (1); R_block = D_1,t)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:208-224 (block_rewards pseudocode)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:226-243 (Emission Rate Factor Function, A_t)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:245-259 (calculate_emission_rate_factor pseudocode)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:263-268 (delta_t)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:270-290 (weighted_deviation_from_target pseudocode)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:292-298 (delta_t sign convention; deviation uses only the stake KPI)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:302-311 (gamma_t)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:313-338 (weighted_average pseudocode; average uses only the burn KPI)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:342-363 (KPI 1, inferred total stake; Security Level)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:365-374 (KPI 2, average burning rate; D_1,target = S_tge)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:376-397 (integer-arithmetic requirement and the constant substitutions)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:412-433 (derivation of the 25/(12e7) and 10512/(12e7) coefficients)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:437-451 (integer A_t and A_t')",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:455-473 (integer Rewards_t; 62500/657)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:477-501 (integer reference implementation, incl. 60/40 split)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/analysis-block-reward-parameter-calibration.md:41-80 (alpha_d rationale; states alpha_d = 1/6)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/analysis-block-reward-parameter-calibration.md:82-106 (alpha_a rationale)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/analysis-block-reward-parameter-calibration.md:108-133 (D_0,target and D_1,target rationale)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/analysis-block-reward-parameter-calibration.md:135-156 (I_max and I_min rationale)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/analysis-block-rewards.md:67-97 (supply evolution S_t; baseline simulation uses alpha_d = alpha_a = 1, T = 0)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-total-stake-inference.md:45-57 (beta, PERIOD, f, k; density_over_slots)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-total-stake-inference.md:59-83 (total_stake_inference algorithm)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:92-98 (f = 1/30, k = 2160, slot length 1s)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:134-146 (epoch schedule; epoch length 10*floor(k/f); 21,600 expected blocks per epoch)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:148-156 (epoch state tuple; D is the relativization constant for the FOLLOWING epoch)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:196-228 (compute_epoch_state; N_BLOCKS from first 6k/f slots of epoch ep-1)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:135-173 (60/40 Blend/leader split; get_blend_reward, update_leader_rewards)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:175-201 (PoW pool funded by diverting POW_SHARE/SHARE_DEN of fees BEFORE the burn; who bears the cost)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1806-1814 (POW_SHARE = 10, SHARE_DEN = 100)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:2117-2123 (denomination: 1 LGO = 1e9 lepta; max minted block reward is 62500/657 LGO, rounded down where an integer is required)",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:91-102 (leader pool share = floor(leader_rewards / unclaimed vouchers))"
          ],
          "parameters": [
            {
              "name": "Emission rate factor (the control output)",
              "symbol": "A_t",
              "value": "computed; A_t in [0,1]; A_t = min{1, max{0, (alpha_d*delta_t + alpha_a*gamma_t + I_min)/I_max}}",
              "citation": "block-rewards.md:228-232 and 382-384; range stated at block-rewards.md:151"
            },
            {
              "name": "Control responsiveness to KPI deviation metrics",
              "symbol": "alpha_d",
              "value": "1/4 (block-rewards.md). CONFLICT: the calibration analysis states 1/6. Both quoted under ambiguities.",
              "citation": "block-rewards.md:163 (table, default 1/4); block-rewards.md:389 (alpha_d = 1/4 in the integer derivation); analysis-block-reward-parameter-calibration.md:80 ("The value alpha_d = 1/6 is chosen ...")"
            },
            {
              "name": "Control responsiveness to KPI average metrics",
              "symbol": "alpha_a",
              "value": "1",
              "citation": "block-rewards.md:162 (table); block-rewards.md:390 (integer derivation)"
            },
            {
              "name": "Minimum emission rate per year",
              "symbol": "I_min",
              "value": "0% (i.e. 0.0)",
              "citation": "block-rewards.md:140 (core variables, "default: 0%"); block-rewards.md:168 (table); block-rewards.md:252 (i_min: float = 0.0); analysis-block-reward-parameter-calibration.md:156"
            },
            {
              "name": "Maximum emission rate per year",
              "symbol": "I_max",
              "value": "1% (i.e. 0.01)",
              "citation": "block-rewards.md:141 (core variables, "default: 1%"); block-rewards.md:167 (table); block-rewards.md:253 (i_max: float = 0.01); block-rewards.md:391 (I_max = 1e-2)"
            },
            {
              "name": "Token supply at TGE",
              "symbol": "S_tge",
              "value": "10 billion LGO (1e10)",
              "citation": "block-rewards.md:160 (table); block-rewards.md:395 (S_tge = 1e10)"
            },
            {
              "name": "Maximum allowable token supply (hard cap)",
              "symbol": "S_cap",
              "value": "UNSET â introduced as "if any" and never given a value in block-rewards.md; the analysis sets S_cap = infinity only for its baseline simulation",
              "citation": "block-rewards.md:132 ("the maximum allowable token supply (hard cap), if any"); analysis-block-rewards.md:90 (simulation assumption S_cap = infinity, not a specified default)"
            },
            {
              "name": "Time step as a fraction of a year",
              "symbol": "Delta_t",
              "value": "1/(365*2880) â one block every 30 seconds",
              "citation": "block-rewards.md:170 (table); block-rewards.md:396"
            },
            {
              "name": "Average number of block proposals within Delta_t",
              "symbol": "f",
              "value": "1 ("The time step Delta_t was chosen so that f equals to 1")",
              "citation": "block-rewards.md:169 (table); block-rewards.md:392"
            },
            {
              "name": "Look-back window length for the moving average (in time steps / blocks)",
              "symbol": "T",
              "value": "120 ("the minting averages the fees burned in the last hour")",
              "citation": "block-rewards.md:161 (table); block-rewards.md:392; window index range t-T+1..t at block-rewards.md:305"
            },
            {
              "name": "Weight of the i-th KPI",
              "symbol": "w_i",
              "value": "1 ("There's only one KPI of this type in our system"); constraint sum_i w_i = 1",
              "citation": "block-rewards.md:143 (definition and constraint); block-rewards.md:164 (table, default 1); block-rewards.md:408 (constraint restated)"
            },
            {
              "name": "Target for KPI 0 (inferred total stake)",
              "symbol": "D_0,target",
              "value": "3 billion LGO (3e9) = 30% of TGE supply",
              "citation": "block-rewards.md:165 (table); block-rewards.md:394; block-rewards.md:482 (STAKE_TARGET = int(3e9))"
            },
            {
              "name": "Normalizer for KPI 1 (burned fees)",
              "symbol": "D_1,target",
              "value": "10 billion LGO (1e10), equal to S_tge; "in the context of this KPI, this value behaves as a normalizer"",
              "citation": "block-rewards.md:166 (table); block-rewards.md:372; block-rewards.md:395"
            },
            {
              "name": "Inferred total stake at time t (KPI 0)",
              "symbol": "D_0,t",
              "value": "computed by the Cryptarchia total-stake inference; a chain-state input to the reward function, not a parameter",
              "citation": "block-rewards.md:348; cryptarchia-total-stake-inference.md:59-83; cryptarchia-v1-protocol.md:220-226"
            },
            {
              "name": "Fees burned in block t (KPI 1), also R_block",
              "symbol": "D_1,t = R_block",
              "value": "computed; "the amount of Storage fees and Execution base fees burned since t-1"",
              "citation": "block-rewards.md:371; block-rewards.md:206 (R_block = D_1,t); block-rewards.md:154"
            },
            {
              "name": "Integer scale for A_t (denominator of A_t')",
              "symbol": "A_SCALE",
              "value": "120,000,000 (= 12e7)",
              "citation": "block-rewards.md:478; derived at block-rewards.md:412-424"
            },
            {
              "name": "Integer numerator of I_max*S_tge*Delta_t/f",
              "symbol": "INFLATION_NUMERATOR",
              "value": "62,500",
              "citation": "block-rewards.md:479; derived at block-rewards.md:462-464"
            },
            {
              "name": "Integer denominator of I_max*S_tge*Delta_t/f",
              "symbol": "INFLATION_DENOMINATOR",
              "value": "657",
              "citation": "block-rewards.md:480; derived at block-rewards.md:462-464"
            },
            {
              "name": "Integer coefficient on the summed burned-fee window",
              "symbol": "FEE_AVG_NUMERATOR",
              "value": "10,512",
              "citation": "block-rewards.md:481; derived at block-rewards.md:428-433"
            },
            {
              "name": "Share of the block reward to the Blend service",
              "symbol": "(none)",
              "value": "60%",
              "citation": "overview-cryptoeconomics.md:145 and 160; block-rewards.md:497 (reward_numerator * 6 // (reward_denominator * 10))"
            },
            {
              "name": "Share of the block reward to the leader pool",
              "symbol": "(none)",
              "value": "40%",
              "citation": "overview-cryptoeconomics.md:144 and 170; block-rewards.md:498 (reward_numerator * 4 // (reward_denominator * 10))"
            },
            {
              "name": "Total-stake inference learning rate",
              "symbol": "beta",
              "value": "1.0",
              "citation": "cryptarchia-total-stake-inference.md:49"
            },
            {
              "name": "Total-stake inference observation period (slots)",
              "symbol": "PERIOD",
              "value": "6*floor(k/f)",
              "citation": "cryptarchia-total-stake-inference.md:50"
            },
            {
              "name": "Total-stake inference fixed-point scale",
              "symbol": "PRECISION",
              "value": "1e3",
              "citation": "cryptarchia-total-stake-inference.md:64"
            },
            {
              "name": "Slot activation coefficient",
              "symbol": "f (Cryptarchia)",
              "value": "1/30 â NOTE: this f is a DIFFERENT quantity from the block-rewards f (blocks per Delta_t), which is 1",
              "citation": "cryptarchia-v1-protocol.md:94; block-rewards.md:169"
            },
            {
              "name": "Security parameter",
              "symbol": "k",
              "value": "2160 blocks",
              "citation": "cryptarchia-v1-protocol.md:95"
            },
            {
              "name": "Slot length",
              "symbol": "(none)",
              "value": "1 second",
              "citation": "cryptarchia-v1-protocol.md:96"
            },
            {
              "name": "Genesis inferred total stake",
              "symbol": "D_GENESIS",
              "value": "UNSET â referenced as hardcoded at chain initialization, but no value is given in any document searched (including bedrock-genesis-block.md)",
              "citation": "cryptarchia-v1-protocol.md:200-202"
            },
            {
              "name": "Fraction of collected fees diverted to the PoW reward pool before the burn",
              "symbol": "POW_SHARE / SHARE_DEN (beta)",
              "value": "10/100 = 1/10",
              "citation": "bedrock-v1.1-mantle-specification.md:1806-1807; overview-cryptoeconomics.md:183-187"
            },
            {
              "name": "Token denomination",
              "symbol": "lepton",
              "value": "1 LGO = 1e9 lepta; TokenValue (uint64) counts lepta",
              "citation": "bedrock-v1.1-mantle-specification.md:2119"
            }
          ],
          "eligibility": "The per-block reward computed by equation (1) is not paid to any individual directly. It is split and pooled:

- 60% to the Blend service. "At the start of each Blend epoch, a Blend reward variable is computed. Its amount equals 60% of the total block rewards of the previous epoch" (overview-cryptoeconomics.md:154-162). Distributed to active Blend nodes via bedrock-service-reward-distribution.md.
- 40% to the leader reward pool. "At the start of each epoch, the rewards are added to the leader rewards. Its amount is increased by 40% of the total block rewards of the previous epoch", plus Execution market tips (overview-cryptoeconomics.md:164-172). A leader receives floor(leader_rewards / (|voucher_cm| - |voucher_nf|)) per voucher, i.e. an equal share of the pool, never an amount tied to the block they proposed (bedrock-anonymous-leaders-reward.md:91-102).
- Proof-of-work miners are NOT eligible for any part of the block reward. Their pool is funded separately by diverting POW_SHARE/SHARE_DEN = 1/10 of the fees a block collects before the burn (overview-cryptoeconomics.md:175-189; bedrock-v1.1-mantle-specification.md:1806-1814). "Fees rather than block rewards" is stated explicitly as a design decision.

Gates on A_t itself: none â A_t is a pure function of chain state (D_0,t and the last T blocks of burned fees), evaluated for every block. It is clamped to [0,1] on both sides (block-rewards.md:231, 257, 488-491). There is no eligibility condition, no minimum stake, and no activity threshold in the emission-rate-factor function.

Note the routing consequence for the simulator: only A_t * I_max * S_tge * Delta_t / f is newly minted; (1-A_t) * R_block is a re-mint of tokens already burned in that block (block-rewards.md:176-181: "if far from the target, the system mints new tokens; if close to the target, the system mints exactly what was burned (up to I_max of TGE)").",
          "timing": "PER BLOCK (the reward):
- Equation (1) is evaluated once per block. Delta_t = 1/(365*2880) and f = 1 are chosen so that one time step = one block of 30 seconds (block-rewards.md:169-170). So the reward per block is a maximum of 62500/657 LGO of newly minted tokens (block-rewards.md:462-464), rounded down to whole lepta where an integer is required (bedrock-v1.1-mantle-specification.md:2123).
- The moving-average term gamma_t reads the last T = 120 blocks of burned fees, tau = t-T+1 .. t, i.e. it INCLUDES the current block (block-rewards.md:305, 438; and `last_burned_fee = burned_fees_window[-1]` at block-rewards.md:486). One hour of look-back at 30s blocks (block-rewards.md:161).
- No lag is specified on the burn KPI: D_1,t is "the amount of Storage fees and Execution base fees burned since t-1" (block-rewards.md:371), read in the same block.

PER EPOCH (the stake KPI D):
- D^ep is computed once per epoch. Epoch length = 10*floor(k/f) slots (cryptarchia-v1-protocol.md:144); expected blocks per epoch = 10k = 21,600 (cryptarchia-v1-protocol.md:146).
- D^ep = infer_total_active_stake(D^{ep-1}, N_BLOCKS^{ep-1}), where N_BLOCKS^{ep-1} counts blocks in the FIRST 6*floor(k/f) slots of epoch ep-1 (cryptarchia-v1-protocol.md:224-226).
- Within epoch ep, D can be computed at the 2s-th slot (= 6*floor(k/f) slots) into the epoch and is finalized 4*floor(k/f) slots later, i.e. at the end of the epoch (cryptarchia-v1-protocol.md:142).
- "D is used as the stake relativization constant for the following epoch" (cryptarchia-v1-protocol.md:156).
- Consequence: the D in force during epoch ep reflects block production during the first 60% of epoch ep-1. The observation window closes 4*floor(k/f) slots before epoch ep begins, so the lag between the last observed block and the first block at which D is in force is 0.4 epochs, rising to 1.4 epochs for the oldest observed block. See derived_not_stated.

PER EPOCH (the payout):
- Blend: 60% of the previous epoch's total block rewards, computed at the start of each Blend epoch, allocated on reported Active Messages during epoch e+2 (overview-cryptoeconomics.md:139, 154-162).
- Leaders: 40% of the previous epoch's total block rewards is added to the leader pool at the start of epoch e+1; vouchers of epoch e become claimable then (overview-cryptoeconomics.md:140, 164-172; bedrock-anonymous-leaders-reward.md:91).",
          "ambiguities": [
            "alpha_d is 1/4 in the normative spec and 1/6 in the calibration analysis that the normative spec cites as its justification. block-rewards.md:163: "| $`\alpha_d`$ | Denotes the control responsiveness to KPI deviation metrics. | $1/4$ | See [\[Analysis\] Block Reward Parameter Calibration](analysis-block-reward-parameter-calibration.md), for details. |" and block-rewards.md:389: "\alpha_d=\frac{1}{4}". Against analysis-block-reward-parameter-calibration.md:80: "The value $`\alpha_d=1/6`$ is chosen so that when the total inferred stake is off target by $16.6\%$ (i.e. $`\delta_t=16.6\%`$), the system starts moving from the maximum inflationary regime to the regime driven by the burned fees. If $`D_{0,target}=30\%`$, this means that this happens when the security level reaches $25\%$." I do not reconcile these. Note that the integer normative form at block-rewards.md:412-424 and 478-482 is built on 1/4, so adopting 1/6 would change A_SCALE from 12e7 to 18e7.",
            "The calibration rationale for alpha_d does not reproduce under either candidate value. With A_t = (alpha_d*delta_t)/I_max clamped to [0,1], A_t leaves the saturated regime at delta_t = I_max/alpha_d, which is 4% for alpha_d = 1/4 and 6% for alpha_d = 1/6 â not the 16.6% claimed at analysis-block-reward-parameter-calibration.md:80. This may be a units disagreement: analysis-block-reward-parameter-calibration.md:43 says "The normalized deviation from target, namely $`\delta_t`$, is measured in percentage units", while block-rewards.md:265-268 defines delta_t as a dimensionless ratio (D_target - D_t)/D_target and block-rewards.md:412-424 substitutes it as a raw fraction. The spec does not state which. Under the percentage reading, alpha_d*delta_t would be 100x larger and A_t would be saturated at essentially all times, so the fraction reading is the only one that produces the described behaviour â but the 16.6% figure fits neither.",
            "The constraint "sum_i w_i = 1" (block-rewards.md:143, 408) is inconsistent with the table default w_i = 1 (block-rewards.md:164) applied to two KPIs. The prose resolves this by partitioning: block-rewards.md:298 says the deviation term uses only the stake KPI and block-rewards.md:338 says the average term uses only the burn KPI, so each of the two sums has exactly one member with weight 1. The parametrization table lists only "$`w_i`$ | Denotes the weight of the $i$-th KPI in the normalized deviation from target | $1$", i.e. it names a default for the deviation weight and not explicitly for the average weight. The integer derivation at block-rewards.md:412-433 uses weight 1 for both.",
            "Units: block-rewards.md computes in whole LGO (STAKE_TARGET = int(3e9), the reward 62500/657) while consensus TokenValue counts lepta at 1 LGO = 1e9 lepta (bedrock-v1.1-mantle-specification.md:2119). A_t' at block-rewards.md:443-451 is dimensionful â it adds 3e9 - D_0,t to 10512*sum(D_1,tau) and compares against 12e7 â so D_0,t and D_1,tau must be in the SAME unit as the literal 3e9. The spec never states which unit the reward reference implementation's integers are in. If they are lepta, STAKE_TARGET must be 3e18 and A_SCALE 12e16; if LGO, the fee window sums must be converted from lepta first. bedrock-v1.1-mantle-specification.md:2123 ("The maximum minted block reward ... is $`62500/657`$ LGO") indicates block-rewards.md is written in LGO, but no conversion rule is specified.",
            "Whether the PoW pool diversion is inside or outside D_1,t. overview-cryptoeconomics.md:195 states "The emission model measures the fees that are actually burnt and mints against them, so diverting a share before the burn reduces that measurement by the same share", which implies D_1,t = collected_fees - floor(collected_fees * POW_SHARE / SHARE_DEN). block-rewards.md:371 predates this and simply says D_1,t is "the amount of Storage fees and Execution base fees burned since t-1" with no mention of a diversion. Consistent under the overview's reading, but block-rewards.md itself never states it.",
            "The block-rewards.md reference implementations contain transcription errors that a simulator must not copy: (a) block-rewards.md:222 uses undefined `R_block_cur` where the parameter is `D_1_t`; (b) block-rewards.md:494 uses undefined `a_num` where the variable is `a_numerator`, and the line continuation as written is not valid Python; (c) block-rewards.md:287 reads `weighted_target_deviation += weight * deviation value`, a syntax error; (d) block-rewards.md:323 asserts against `kpi_deviations` inside `weighted_average`, where that name is not a parameter.",
            "The 60/40 split at block-rewards.md:497-498 floors each share independently (`* 6 // (den*10)` and `* 4 // (den*10)`), so blend_reward + leader_reward can be strictly less than the total reward, by up to 2 units. The spec does not say what happens to the residue. Compare bedrock-anonymous-leaders-reward.md:100, which is explicit that the flooring residue there "stays in `leader_rewards`", and overview-cryptoeconomics.md:187, which is explicit that the PoW flooring residue "stays with the remainder and is burnt". No such statement exists for the 60/40 split.",
            "Which D_0,t the reward function reads. block-rewards.md indexes D_0,t by the block time step t and takes `total_stake: int` as an argument (block-rewards.md:484) without saying it is the epoch constant D^ep from Cryptarchia. Cryptarchia computes D exactly once per epoch (cryptarchia-v1-protocol.md:196-228). Whether the reward function is meant to hold D_0,t constant across an epoch, or to read some finer-grained estimate, is not stated in either document. Holding it constant per epoch is the only value the protocol produces, but that is inference on my part.",
            "The total_stake_inference pseudocode at cryptarchia-total-stake-inference.md:63-83 has type problems: `const PRECISION: u64 = 1e3` assigns a float literal to u64; line 77 multiplies `tse_p` (u64) by `density_diff_p` (i128) without a cast, and line 78 does the same for `beta_p`; `new_total_stake_estimate` is i128 and is compared against the integer literal 1 before the `as u64`. The arithmetic intent is unambiguous but the code will not compile as written.",
            "cryptarchia-v1-protocol.md:142 writes the Lottery Constants Finalization phase as "$`s+\lfloor\frac{k}{f}\rfloor=4\lfloor\frac{k}{f}\rfloor`$ slots" and then says "We wait another $`4\frac{k}{f}`$ slots". With s = 3*floor(k/f) (cryptarchia-v1-protocol.md:104), the phase length is 4*floor(k/f) but the additional wait after D can be computed is only floor(k/f), not 4k/f. The line is internally inconsistent; the phase-length arithmetic (which sums to the stated 10*floor(k/f) epoch length at line 144) is the one that is self-consistent."
          ],
          "not_specified": [
            "No value for S_cap (the supply hard cap). block-rewards.md:132 introduces it as "if any" and it never appears in the parametrization table or in equation (1). It appears only in the supply-evolution formula in the informational analysis (analysis-block-rewards.md:72), which sets it to infinity as a simulation assumption.",
            "No value for D_GENESIS, the genesis inferred total stake. cryptarchia-v1-protocol.md:200-202 says "The genesis epoch state is hardcoded upon chain initialization" and returns D_GENESIS, but no document in the tree â including bedrock-genesis-block.md â gives a number. A simulator must treat this as a free input.",
            "No warm-up rule for the moving average. gamma_t sums tau from t-T+1 to t (block-rewards.md:305), which is undefined for t < T-1. The spec does not say whether the first 119 blocks use a shorter window, pad with zeros, or divide by the actual count. The integer form at block-rewards.md:438 and the `burned_fees_window` list at block-rewards.md:484 both assume a full window exists.",
            "No statement of how A_t is carried across a chain reorganisation, nor whether the burned-fee window follows the chain or the node's local view.",
            "No rounding rule for A_t itself. The integer form keeps A_t as the exact rational A_t'/12e7 and only rounds at the final reward division (block-rewards.md:443-451, 493-498), so A_t is never materialised as an integer â but the spec does not say this in words.",
            "No specified behaviour when D_0,t exceeds D_0,target far enough that alpha_d*delta_t + alpha_a*gamma_t + I_min goes negative. The clamp at 0 handles it arithmetically (A_t = 0, reward = R_block), but the spec offers no discussion of a sustained over-target regime beyond the sign convention at block-rewards.md:296.",
            "No conversion between the reward-side time index t (blocks) and the epoch index used by Cryptarchia for D. The two documents use unrelated indices and nothing maps between them.",
            "No statement of whether the reward is minted at the block that computes it or credited to the pools only at the epoch boundary. overview-cryptoeconomics.md:154-172 aggregates the previous epoch's block rewards at the epoch boundary; block-rewards.md speaks of amounts "minted per block". Whether the supply increases at block time or at epoch time is not stated.",
            "No specified value for the initial burned-fee window contents at genesis."
          ],
          "derived_not_stated": [
            "DERIVED: with alpha_a = 0 contribution ignored, A_t = 1 (fully saturated, maximum inflation) whenever delta_t >= I_max/alpha_d. At alpha_d = 1/4 and I_max = 0.01 that is delta_t >= 4%, i.e. D_0,t <= 0.96 * 3e9 = 2.88e9 LGO. The 'smooth transition' the calibration analysis describes therefore occupies only the last 4% of the approach to target. At alpha_d = 1/6 it would be the last 6%. The spec does not state this threshold anywhere.",
            "DERIVED: with alpha_a = 1, the burn term alone saturates A_t whenever the annualized average burn rate reaches I_max = 1% of S_tge per year. Since gamma_t/I_max = (annualized average burn rate)/0.01, a sustained burn of 1e8 LGO/yr sets A_t = 1 on its own. Equivalently, in the integer form, sum over the 120-block window of D_1,tau >= 12e7/10512 ~= 11,415 (in the LGO units of that expression) saturates A_t by itself.",
            "DERIVED: at alpha_d = 1/4 the emission-rate factor's stake half of the numerator has slope 25 per unit of delta_t (block-rewards.md:412-424 shows the 25 explicitly, then folds it into 1/(12e7)), so the whole transition band in stake terms is 12e7 LGO wide â from D_0,t = 2.88e9 (A_t = 1) to D_0,t = 3.0e9 (A_t = 0), holding gamma_t = 0.",
            "DERIVED: with beta = 1.0, the total-stake inference collapses to a pure ratio update. new = tse - tse*(expected - measured)/expected = tse * measured/expected, i.e. D^ep = D^{ep-1} * N_BLOCKS^{ep-1} / (PERIOD * f). The spec gives only the general beta form (cryptarchia-total-stake-inference.md:63-83); the collapse at the specified beta is mine.",
            "DERIVED: numeric slot values at the specified constants. floor(k/f) = floor(2160/(1/30)) = 64,800 slots. Epoch length = 10*floor(k/f) = 648,000 slots = 648,000 seconds = 7.5 days. PERIOD = 6*floor(k/f) = 388,800 slots. Expected blocks in the observation window = PERIOD * f = 388,800/30 = 12,960 blocks; expected blocks per epoch = 21,600, which the spec does state (cryptarchia-v1-protocol.md:146). Note that block-rewards.md:136 independently mentions a 7.5-day epoch, consistent with this.",
            "DERIVED: the lag on D_0,t. The observation window for D^ep is the first 6*floor(k/f) = 388,800 slots of epoch ep-1, and epoch ep begins 648,000 slots after epoch ep-1 began. So the last observed block is 648,000 - 388,800 = 259,200 slots (3 days, 0.4 epochs) before D^ep takes effect, and the first observed block is 648,000 slots (7.5 days, 1.4 epochs) before. Mean lag ~0.9 epochs ~ 6.75 days. The spec states the windows (cryptarchia-v1-protocol.md:142, 224-226) but never states the lag.",
            "DERIVED: 62500/657 LGO = 95.1294... LGO = 95,129,375,951.29... lepta per block at A_t = 1, over 365*2880 = 1,051,200 blocks per year, giving exactly 1e8 LGO/yr = 1% of S_tge. The mantle spec states the 62500/657 figure (bedrock-v1.1-mantle-specification.md:2123); the per-year check is mine.",
            "DERIVED: at f = 1/30 the true expected block interval is 30 slots = 30 seconds, matching the 2880 blocks/day assumed by Delta_t. But the reward formula's per-block emission is a fixed constant per BLOCK, not per slot, so if actual block production runs above or below the 1/30 rate the realised annual emission scales with it. The spec does not discuss this coupling. For a simulator with no network delay, honest production will track f closely, but the emission is nevertheless block-indexed, not time-indexed.",
            "DERIVED: the two symbols named f are different quantities with different values â f = 1 in block-rewards.md (blocks per Delta_t) and f = 1/30 in cryptarchia-v1-protocol.md (slot activation coefficient). Neither document flags the collision."
          ]
        },
        "check": {
          "stream": "Block reward per block and the emission-rate-factor control function A_t (including the inferred-total-stake KPI D and its lag)",
          "citations_verified": false,
          "invented_elements": [
            "INVENTED DEFECT (ambiguities[10]): the claimed internal inconsistency in the epoch schedule does not exist. cryptarchia-v1-protocol.md:142 reads: '| Lottery Constants Finalization | $`s+\lfloor\frac{k}{f}\rfloor=4\lfloor\frac{k}{f}\rfloor`$ slots | On the $`2s^{th}`$ slot into the epoch, the epoch nonce $`\eta`$ and the inferred total stake $`D`$ can be computed. We wait another $`4\frac{k}{f}`$ slots for these values to finalize. |'. With s = 3*floor(k/f) (line 104), phase 3 begins at slot 2s = 6*floor(k/f) â exactly when D can be computed â and runs 4*floor(k/f) slots to the epoch end at 10*floor(k/f) (line 144). The stated 'another 4k/f slots' therefore agrees with the phase length; 's + floor(k/f)' is just an alternative way of writing 4*floor(k/f). The extraction's assertion that 'the additional wait after D can be computed is only floor(k/f), not 4k/f' and that 'the line is internally inconsistent' is not in the source and is arithmetically wrong.",
            "ARITHMETIC ERROR in derived_not_stated[6] (the lag on D): 'the first observed block is 648,000 slots (7.5 days, 1.4 epochs) before' â 648,000 slots IS one epoch length (line 144: 10*floor(k/f) = 648,000 slots = 7.5 days), i.e. 1.0 epoch, not 1.4. The follow-on 'Mean lag ~0.9 epochs ~ 6.75 days' is wrong for the same reason: the correct span is 0.4 to 1.0 epochs, mean 0.7 epochs = 5.25 days. A simulator calibrating the control loop's dead time from this bullet would over-lag D by ~40%.",
            "OVERSTATED (not strictly invented, but not in the source): 'blend_reward + leader_reward can be strictly less than the total reward, by up to 2 units.' Each of the two independent floors at block-rewards.md:497-498 discards a fraction < 1, so the shortfall against the exact rational total is < 2 units, i.e. at most 1 whole unit below floor(total). The spec says nothing about a residue here â that part of the observation is correct and correctly flagged as unstated."
          ],
          "wrong_citations": [
            "block-rewards.md:392 cited for 'f = 1' (parameters, symbol f). Line 392 reads 'T=120,\quad'; f=1 is on line 393: 'f=1,\quad R_\text{block} = D_{1,t}\\'. The T=120 citation to :392 is correct; the f citation is off by one.",
            "bedrock-anonymous-leaders-reward.md:100 cited in ambiguities[7] for the flooring residue that 'stays in `leader_rewards`'. Line 100 actually says 'Rounding down guarantees that $`share \times (|voucher\_cm| - |voucher\_nf|) \leq leader\_rewards`$...'. The quoted phrase is on line 102: 'Nothing is lost to the rounding either: the remainder stays in `leader_rewards` until it is claimed or aggregated with the rewards of the next epoch.' Content correct, line off by two.",
            "cryptarchia-v1-protocol.md:200-202 cited for D_GENESIS with the claim that 'no value is given in any document searched (including bedrock-genesis-block.md)'. The cited lines are correct ('The genesis epoch state is hardcoded upon chain initialization.' / return (C_GENESIS, eta_GENESIS, D_GENESIS)), but the accompanying negative claim is false â see missed_elements."
          ],
          "missed_elements": [
            "D_GENESIS IS SPECIFIED â bedrock-genesis-block.md:317: '3. $`D`$: The initial estimate of total stake will be the total tokens distributed at genesis.' (under '### Initial Epoch State', lines 309-317, alongside eta from genesis_epoch_nonce and C_LEAD from the initial distribution ledger root). This is the single most consequential omission for this stream. D_0,t starts at ~the full launch supply (1e10 LGO, minus the 5/1000 PoW pool seed held as a balance, bedrock-genesis-block.md:73-84), i.e. more than 3x ABOVE D_0,target = 3e9. delta_t at genesis is therefore about -2.33, A_t clamps to 0, and the chain opens in the pure fee-recycling regime â the exact opposite of the bootstrap story the spec tells at block-rewards.md:357 ('when the blockchain starts, $`D_{0,t}\vert_{t=0}`$ is very likely a small number compared to the target. Therefore, the equation above tilts towards 1'). A simulator that treats D_GENESIS as a free input, or seeds it low, will produce the intended bootstrap curve for the wrong reason. This tension between the two documents belongs in ambiguities.",
            "Systematic bias of the stake estimator â analysis-total-stake-inference.md:71-83. The process converges not to the true stake but to E[D_inf] = (log(1-f)/log(1-f/q)) * D_TRUE, where q is the honest slot utilization rate; line 83: 'increased network delay, which reduces the honest slot utilization rate through wasted blocks results in a systematic underestimate of true total stake.' At the parameters used throughout that document (f=1/30, q=0.85) the factor is ~0.847 (line 571). The extraction's derived collapse D^ep = D^{ep-1} * N_BLOCKS/(PERIOD*f) at beta=1 is correct for the algorithm, but the extraction never notes that the KPI feeding A_t is a biased estimate â a persistent ~15% underestimate of stake is a persistent positive delta_t, i.e. persistent extra emission. Same document, line 97: steady state 'after 5 epochs'; line 204: convergence 'within 2 epochs' after massive shocks. None of this is cited anywhere in the extraction.",
            "The supply-evolution equation is cited but never reproduced. analysis-block-rewards.md:69-73: $`S_{t} = \min \lbrace S_{cap},  S_{tge} \times (1 + \sum_{\tau=1}^t A_\tau \cdot I_{max} \cdot \Delta_\tau) \rbrace`$, with line 83: 'It is assumed here that $`S_{t-1}`$ already accounts for the burned tokens. This equation implies that the supply evolution does not compound over time.' This is the only place in the tree that says how minted rewards accumulate into supply, and it is the direct source for the extraction's own claim that only the first term is newly minted. A supply-tracking simulator needs it stated, not just cited.",
            "Where D_1,t / R_block actually comes from. block-rewards.md:154 defers it: 'Refer to [Execution Market](execution-market.md) and [Storage Markets](storage-markets.md) for how to compute $`R_{block}`$.' execution-market.md:222-229 gives it concretely: $`\hat{R}_{\mathrm{burned}}(s) = \sum_{t \in \mathcal{B}_s} (g_t \cdot b_{\mathrm{exec}}[s])`$ â gas times base fee summed over the block's transactions, plus the storage-fee side â and line 229: 'This burned quantity is then used as a input for the computation of the block rewards.' The extraction treats D_1,t as an opaque input without recording the pointer.",
            "One spec transcription bug not in the extraction's otherwise-complete bug list. block-rewards.md:152: '- This implies that $`A_t \cdot I_{max} \cdot \Delta_t`$ denotes the emission within the time-step.' â S_tge is missing; the same quantity at lines 185-187 is $`A_t \cdot I_{max} \cdot S_{tge} \cdot \Delta_t`$. The extraction lists four other transcription errors (lines 222, 287, 323, 494) but not this one.",
            "Two calibration statements that bear on the extraction's derived saturation claims. block-rewards.md:167 explains I_max=1% as 'This value guarantees that, when the total inferred stake reaches $`D_{0,target}`$, then the APY for validation is ~3.33%' (analysis-block-reward-parameter-calibration.md:152 says 3.34%) â a free invariant check for a simulator. And analysis-block-reward-parameter-calibration.md:96: 'As a consequence of the parametrization, specifically $`\alpha_a=1`$, the emission rate $`I_t`$ never reaches the maximum value' â which sits in tension with derived_not_stated[1] ('with alpha_a = 1, the burn term alone saturates A_t whenever the annualized average burn rate reaches I_max'). Both are arithmetically reconcilable (the calibration figure is a specific stochastic example), but the source's contrary sentence should have been surfaced."
          ],
          "corrections": [
            "Delete ambiguities[10]. cryptarchia-v1-protocol.md:142 is self-consistent: phase 3 length 4*floor(k/f) = s + floor(k/f) with s = 3*floor(k/f); D is computable at 2s = 6*floor(k/f) into the epoch; the 4*floor(k/f) wait runs to the epoch boundary at 10*floor(k/f).",
            "Fix derived_not_stated[6]: the oldest observed block is 648,000 slots = 7.5 days = 1.0 epoch before D^ep takes effect (not 1.4 epochs); the newest is 259,200 slots = 3 days = 0.4 epochs; mean lag 0.7 epochs = 5.25 days (not 0.9 epochs / 6.75 days).",
            "Replace the D_GENESIS 'UNSET' entry with: SPECIFIED as a rule, not a numeral â bedrock-genesis-block.md:317, 'The initial estimate of total stake will be the total tokens distributed at genesis', i.e. ~1e10 LGO. Add the resulting conflict with block-rewards.md:357 to ambiguities, and drop the corresponding not_specified bullet.",
            "Move the f=1 citation from block-rewards.md:392 to :393; move the 'stays in leader_rewards' citation from bedrock-anonymous-leaders-reward.md:100 to :102.",
            "Add analysis-total-stake-inference.md:71-83 (accuracy: E[D_inf] = log(1-f)/log(1-f/q) * D_TRUE, systematic underestimate under network delay) and :97/:204 (5-epoch steady state, 2-epoch shock recovery) to the citation set and to the D-side description.",
            "Reproduce the supply-evolution equation (analysis-block-rewards.md:69-83) in the formula body, including the non-compounding note, since the extraction's minting/re-minting routing claim rests on it.",
            "Add block-rewards.md:154 -> execution-market.md:222-229 for the definition of D_1,t, and add block-rewards.md:152 (missing S_tge) to the list of spec transcription errors.",
            "Tighten the 60/40 residue statement: the shortfall against the exact rational total is strictly less than 2 units, i.e. at most 1 whole unit below floor(total).",
            "Reword the section 6 preamble: the observation that 'the numerator on 471 multiplies 62500 by A_t' only' is listed under 'including its bugs', but it is not a bug â line 471 and the reference implementation at 493-494 agree; only a_num/a_numerator and the line continuation are defects."
          ],
          "verdict": "needs-correction"
        }
      },
      {
        "stream": "leader",
        "formula": {
          "stream": "THE LEADER REWARD â what a block's proposer receives in Logos/Bedrock (Cryptarchia PoS leadership), covering the 40/60 split, the voucher-based anonymous claim path, the lottery win condition and stake weighting, note aging, minimum-stake question, and the slot/block relationship.",
          "formula": "=== A. THE SPLIT: 40% of each block reward to leaders ===

overview-cryptoeconomics.md:142-145 (prose, normative):
  "Each block reward of each block is split as follows between the Blend service and the leader:
   - 40% for the leader.
   - 60% for the Blend service."

overview-cryptoeconomics.md:164-173 (the leader-pool accrual pseudocode, quoted verbatim):
```python
def update_leader_rewards(e: epoch, # rewards for the epoch e
    leader_rewards: int): # added to the leader reward pool
    for b in e.blocks: # for each block of the previous epoch
        leader_rewards += 0.4 * get_block_rewards(b) # get 40% of the rewards
        leader_rewards += get_execution_market_tips(b) # get Execution market tips
    return leader_rewards
```
Its Blend counterpart, overview-cryptoeconomics.md:156-162:
```python
def get_blend_reward(e: epoch): # rewards for the epoch e
    blend_rewards = 0
    for b in e.blocks: # for each block of the previous epoch
        blend_rewards += 0.6 * get_block_rewards(b) # get 60% of the rewards
    return blend_rewards
```

block-rewards.md:477-501 gives the SAME split as INTEGER arithmetic, per block, inside the
reference implementation of the block reward itself (quoted verbatim, including the
apparent typo `a_num` on line 494 and the broken line continuation on 493-494):
```python
A_SCALE = 120_000_000            # denominator of 1/(I_max * D1_target * Delta_t * T) 
INFLATION_NUMERATOR = 62_500     # numerator of I_max * S_TGE * DELTA_t / f
INFLATION_DENOMINATOR = 657      # denominator of I_max * S_TGE * DELTA_t / f
FEE_AVG_NUMERATOR = 10_512       # numerator of 1/(I_max * D1_target * Delta_t * T) 
STAKE_TARGET = int(3e9)

def block_reward(total_stake: int, burned_fees_window: list[int]) -> tuple[int, int]:
    sum_fees = sum(burned_fees_window)
    last_burned_fee = burned_fees_window[-1]

    a_numerator = min(
        max(STAKE_TARGET + FEE_AVG_NUMERATOR * sum_fees - total_stake, 0),
        A_SCALE
    )

    reward_numerator = INFLATION_NUMERATOR * a_numerator
                                       + INFLATION_DENOMINATOR * (A_SCALE - a_num) * last_burned_fee
    reward_denominator = INFLATION_DENOMINATOR * A_SCALE

    blend_reward = reward_numerator * 6 // (reward_denominator * 10)
    leader_reward = reward_numerator * 4 // (reward_denominator * 10)

    return blend_reward, leader_reward
```
The 60/40 split is restated as invariant under the PoW-pool diversion at
overview-cryptoeconomics.md:201: "The split between the Blend service and the leader is
itself unchanged: they continue to divide the block reward 60/40, on whatever the block
reward turns out to be." And at overview-cryptoeconomics.md:197: "**The cost falls on the
Blend service and the leaders**, in the 60/40 proportion in which they divide the block
reward." Independently corroborated in execution-market.md:62: "40% of the rewards will be
allocated to block builders and the remaining 60% to Blend nodes."

CONFIRMED: the leader share is 0.4 of the block reward, plus 100% of that block's
execution-market priority fees (tips).

=== B. HOW THE REWARD REACHES THE LEADER (unlinkability) ===

Three-step: voucher in header -> voucher appended to a global Merkle tree at the next epoch
boundary -> anonymous ZK claim against a pool.

1. Voucher creation, bedrock-anonymous-leaders-reward.md:61-72:
   "When producing a block, a leader performs the following:
    1. Generate a one-time random secret voucher <-$ F_p.
    2. Compute the commitment:
```python
voucher_cm = zkhash(
    FiniteField(b"REWARD_VOUCHER", byte_order="little", modulus= p),
    voucher)
```
    3. Include the `voucher_cm` in the block header.
   Each `voucher_cm` is added to a Merkle tree of voucher commitments by validators during
   the execution of the first block of the following epoch"
   The header field is `leader_voucher: RewardVoucher  # 32 bytes`
   (bedrock-v1.1-block-construction.md:122; cryptarchia-v1-protocol.md:285
   `leader_voucher: zkhash  # 32 bytes`), and it is hashed into the block id
   (cryptarchia-v1-protocol.md:267).
   Block execution, bedrock-v1.1-block-construction.md:241: "Append the `leader_voucher`
   contained in the block to the set of reward vouchers **when the following epoch starts**."

2. Nullifier, bedrock-anonymous-leaders-reward.md:133-137:
```python
voucher_nf = zkhash(
    FiniteField(b"VOUCHER_NF", byte_order="little", modulus= p),
    voucher)
```

3. THE PER-CLAIM AMOUNT, bedrock-anonymous-leaders-reward.md:91-98 (verbatim LaTeX):
$$
share = \begin{cases}
  0 &\textbf{if } |voucher\_cm|=|voucher\_nf| \\
\left\lfloor\frac{leader\_rewards}{|voucher\_cm| - |voucher\_nf|}\right\rfloor &\textbf{if } |voucher\_cm| \neq |voucher\_nf|
\end{cases}
$$
   i.e. share = floor(leader_rewards / number_of_unclaimed_vouchers), integer division over
   `TokenValue` (bedrock-anonymous-leaders-reward.md:100). The denominator is the CUMULATIVE
   count of vouchers ever admitted minus the cumulative count of nullifiers, i.e. every
   unclaimed voucher since genesis (overview-cryptoeconomics.md:63: "each unclaimed reward
   (since genesis) representing one equal share of the pool").

4. Claim operation, bedrock-v1.1-mantle-specification.md:1461-1529:
```python
class ClaimRequest:
    rewards_root: zkhash # Merkle root used in the proof for voucher membership
    voucher_nf: zkhash
    public_key: ZkPublicKey
```
   Validation (bedrock-v1.1-mantle-specification.md:1497-1501):
```python
assert claim.voucher_nf not in voucher_nullifier_set
assert claim.rewards_root == last_voucher_root
validate_proof(claim, proof, mantle_txhash)
```
   where `last_voucher_root` is "The last root of the voucher Merkle tree at the start of the
   epoch" (bedrock-v1.1-mantle-specification.md:1489-1490).
   Execution (bedrock-v1.1-mantle-specification.md:1518-1529): add voucher_nf to the nullifier
   set; mint a single output note of value `leader_reward` under `claim.public_key`; "Reduce
   the leader's reward `leaders_rewards` value by the same amount (without ZK proof)."

   Unlinkability is stated at bedrock-anonymous-leaders-reward.md:87: "every leader will
   receive a reward that is independent of the block content to avoid de-anonymization. This
   means that the fees of the block cannot be collected by the leader directly, or need to be
   pooled for all the leaders."

=== C. THE LOTTERY WIN CONDITION AND HOW STAKE WEIGHT ENTERS ===

cryptarchia-proof-of-leadership.md:180-184 (circuit constraints 4-6, verbatim):
  "4. The computation of the lottery ticket: $`ticket := \text{hash}(\text{LEAD\_V1}||\eta||sl||noteID||sk)`$ using [Poseidon2]
   5. The computation of the threshold: $`t:= v(t_0+t_1\cdot v)`$.
     The ticket must be lower than this threshold to win the lottery.
   6. The check that indeed $`ticket \lt t`$."

So: WIN IFF  ticket < t,  with  t = v*(t_0 + t_1*v),  v = the note's value (stake weight
enters linearly at leading order, with a second-order correction).

The constants (cryptarchia-proof-of-leadership.md:141, 210-212):
  t_0 = -(VRF_order * ln(1-f)) / inferred_total_stake
  t_1 = -(VRF_order * ln^2(1-f)) / (2 * inferred_total_stake^2)
This is a 2nd-order Taylor expansion of the Ouroboros Crypsinous
phi_f(alpha) = 1 - (1-f)^alpha  (cryptarchia-proof-of-leadership.md:199, 201-208):
$$
\begin{align*}1-(1-f)^x &= 1-e^{x\ln(1-f)} \\ 1-e^{x\ln(1-f)} &\underset{0}{\sim}x(-\ln(1-f)-0.5\lnÂ²(1-f)x)\end{align*}
$$
Field-element form to be used in implementations
(cryptarchia-proof-of-leadership.md:217-223, verbatim table):
  p            = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001
  t_0_constant = 0x1a3fb997fd5838f2a1585ee090a95c88129ab25cc4d2e2d28f1a95f81d85465
  t_1_constant = 0x71e790b4199113a9a00298d823c5716ddac764a110a45fe3b770bbb3e8a57
  t_0 = t_0_constant / inferred_total_stake
  t_1 = p - floor(t_1_constant / inferred_total_stake^2)
Reference derivation (cryptarchia-proof-of-leadership.md:227-248, verbatim):
```python
from sage.all import RealField


FIELD_ORDER = 0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000001
R = RealField(512)
F = R(1) / R(30)

t_0_constant = int(-R(FIELD_ORDER) * (R(1) - F).log())
t_1_constant = int(R(FIELD_ORDER) * (R(1) - F).log() ** 2 / R(2))


def lottery_constants(inferred_total_stake: int) -> tuple[int, int]:
    t_0 = t_0_constant // inferred_total_stake
    t_1 = FIELD_ORDER - (t_1_constant // inferred_total_stake**2)
    return t_0, t_1
```
VRF_order = p, the BN254 scalar field order (cryptarchia-proof-of-leadership.md:214).
Note t_1 is stored as p - |t_1| (a negative value in F_p), so the real-valued threshold is
v*t_0 - v^2*|t_1|, a downward-opening parabola (cryptarchia-proof-of-leadership.md:296).

Note also the pathological regime, cryptarchia-proof-of-leadership.md:296-302: if
v >> inferred_total_stake the threshold peaks near v ~= 29*inferred_total_stake and crosses
zero near v ~= 58*inferred_total_stake; past the peak the real threshold is negative, wraps
in F_p to a value near p, and "The note wins nearly every slot." Spec says
"No circuit-level mitigation is strictly necessary" (line 315).

=== D. NOTE AGING ===

cryptarchia-v1-protocol.md:160: "A note is eligible to participate in the leadership lottery
if it has not been spent and was a member of the note set at the beginning of the previous
epoch, i.e. they are members of $`\mathbb{C}_\text{LEAD}`$."
cryptarchia-v1-protocol.md:210-212:
  "Notes eligible for leadership lottery are those present in the commitment root at the start
   of the previous epoch."
  $`\mathbb{C}_\text{LEAD}^{ep} \coloneqq \textbf{commitment\_root\_at\_slot}(sl_{ep-1}, tip)`$
  with $`sl_{ep-1} \coloneqq (ep-1) \cdot \text{EPOCH\_LENGTH}`$ (line 208).
Rationale, cryptarchia-v1-protocol.md:164: "If an adversary knows the epoch nonce eta, they
may grind a note that wins the lottery more frequently than should be statistically expected.
Thus, it's critical that notes participating in the lottery are sufficiently old..."
Enforced in the ZK circuit as membership in BOTH ledger_AGED (proves age/existence) and
ledger_LATEST (proves unspent): cryptarchia-proof-of-leadership.md:53-54, 145-149, 179.

=== E. MINIMUM STAKE TO WIN THE LOTTERY ===

There is NONE. Stated affirmatively at overview-cryptoeconomics.md:149: "Blend nodes must
stake a minimum amount while leaders have no such requirement, making Blend nodes more
exposed to risks." And overview-cryptoeconomics.md:152: "Leaders who cannot afford the
minimum stake can still earn enough to eventually reach it." The minimum stake
(bedrock-service-declaration-protocol.md:88, enforced at
bedrock-v1.1-mantle-specification.md:1119 `assert note.value >= min_stake.stake_threshold`)
applies only to SDP service declaration, not to the leadership lottery. No threshold appears
anywhere in cryptarchia-v1-protocol.md or cryptarchia-proof-of-leadership.md.

=== F. ACTIVE SLOT COEFFICIENT AND SLOTS vs BLOCKS ===

cryptarchia-v1-protocol.md:94 (constants table, verbatim row):
  | $`f`$ | slot activation coefficient | The target rate of occupied slots. Not all slots
  contain blocks, many are empty. (see ANALYSIS-BLOCK-TIMES-BLEND-NETWORK for analysis
  leading to the choice of value) | 1/30 |
cryptarchia-v1-protocol.md:96: slot length = 1 second.
cryptarchia-v1-protocol.md:122: "Time is divided up into slots of equal length, where one
instance of the leadership lottery is held in each slot. A slot is said to be occupied if
some validator has won the leadership lottery and proposed a block for that slot, otherwise
the slot is said to be unoccupied."
cryptarchia-v1-protocol.md:232: "A lottery is run for every slot to decide who is eligible to
propose a block. For each slot, we can have 0 or more winners." (=> 0, 1, or several blocks
per slot; several winners in one slot are "guaranteed forks".)
cryptarchia-v1-protocol.md:144: epoch length = 3*floor(k/f) + 3*floor(k/f) + 4*floor(k/f)
  = 10*floor(k/f) slots.
cryptarchia-v1-protocol.md:146: "Since a fraction $`f`$ of slots carries a block in
expectation, the **expected number of blocks in an epoch** follows directly:
$`10 \lfloor \frac{k}{f} \rfloor \cdot f = 10k = 21{,}600`$ blocks".
Restated as a constant at bedrock-v1.1-mantle-specification.md:1780:
`EXPECTED_BLOCKS_PER_EPOCH: uint64 = 21_600      # N_b, derived below`.

=== G. TIPS (the second leader income term) ===

execution-market.md:210-214, the effective priority fee per transaction:
$$
p_t = c_t - b_{\mathrm{exec}}[s].
$$
execution-market.md:96: "$`p_t`$ | Priority Fee | ... The portion of the Execution Gas price
that serves as a tip to the block builder ($`p_t = c_t - b_{\mathrm{exec}}[s]`$)."
execution-market.md:103: $`F_t = g_t \cdot (b_{\mathrm{exec}}[s] + p_t) = g_t \cdot c_t`$
execution-market.md:222-227, ONLY the base-fee part is burnt and fed to block rewards:
$$
\hat{R}_{\mathrm{burned}}(s) = \sum_{t \in \mathcal{B}_s} \bigl(g_t \cdot b_{\mathrm{exec}}[s]\bigr).
$$
execution-market.md:62: "The priority_fee is not immediately distributed to the block builder
(to preserve privacy), but instead it is directed into the block builders reward stream."
NOTE: `get_execution_market_tips(b)` is invoked at overview-cryptoeconomics.md:171 but is
never defined by any document. See not_specified.",
          "citations": [
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:142",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:144",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:145",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:156",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:164",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:166",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:170",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:171",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:197",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:201",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:63",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:140",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:149",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:152",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/overview-cryptoeconomics.md:214",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:477",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:493",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:497",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:498",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:160",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:167",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:169",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:170",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/block-rewards.md:136",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:55",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:61",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:65",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:72",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:78",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:87",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:91",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:100",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:102",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:123",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-anonymous-leaders-reward.md:133",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:94",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:95",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:96",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:97",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:98",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:104",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:122",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:138",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:144",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:146",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:160",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:164",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:208",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:212",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:216",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:224",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:226",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:232",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:240",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:267",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-v1-protocol.md:285",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:141",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:145",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:148",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:161",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:179",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:180",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:181",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:184",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:199",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:207",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:210",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:214",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:219",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:220",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:221",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:233",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:254",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:296",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/cryptarchia-proof-of-leadership.md:315",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:258",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1461",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1467",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1476",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1489",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1497",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1512",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1519",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1529",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1780",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:1806",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:2254",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-mantle-specification.md:2356",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-block-construction.md:122",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-block-construction.md:130",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-block-construction.md:139",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-v1.1-block-construction.md:241",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/execution-market.md:52",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/execution-market.md:62",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/execution-market.md:96",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/execution-market.md:103",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/execution-market.md:210",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/execution-market.md:222",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-genesis-block.md:201",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-genesis-block.md:290",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-genesis-block.md:316",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-genesis-block.md:317",
            "/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/bedrock-service-declaration-protocol.md:88"
          ],
          "parameters": [
            {
              "name": "Leader share of the block reward",
              "symbol": "0.4 / (4 // 10)",
              "value": "0.4 (40%); integer form `reward_numerator * 4 // (reward_denominator * 10)`",
              "citation": "overview-cryptoeconomics.md:144 and :170; block-rewards.md:498; execution-market.md:62"
            },
            {
              "name": "Blend share of the block reward",
              "symbol": "0.6 / (6 // 10)",
              "value": "0.6 (60%); integer form `reward_numerator * 6 // (reward_denominator * 10)`",
              "citation": "overview-cryptoeconomics.md:145 and :160; block-rewards.md:497"
            },
            {
              "name": "Slot activation coefficient (active slot coefficient)",
              "symbol": "f",
              "value": "1/30",
              "citation": "cryptarchia-v1-protocol.md:94; corroborated by `F = R(1) / R(30)` in cryptarchia-proof-of-leadership.md:233 and "For f = 1/30" at cryptarchia-proof-of-leadership.md:254"
            },
            {
              "name": "Slot length",
              "symbol": "(none given)",
              "value": "1 second",
              "citation": "cryptarchia-v1-protocol.md:96"
            },
            {
              "name": "Security parameter (block-depth finality)",
              "symbol": "k",
              "value": "2160 blocks",
              "citation": "cryptarchia-v1-protocol.md:95"
            },
            {
              "name": "Slot security parameter",
              "symbol": "s",
              "value": "3*floor(k/f)  [= 194,400 slots at k=2160, f=1/30 â the numeric value is DERIVED, not stated]",
              "citation": "cryptarchia-v1-protocol.md:104"
            },
            {
              "name": "Epoch length",
              "symbol": "EPOCH_LENGTH",
              "value": "10*floor(k/f) slots  [= 648,000 slots = 7.5 days â DERIVED; block-rewards.md:136 independently says an epoch "lasts 7.5 days"]",
              "citation": "cryptarchia-v1-protocol.md:144; block-rewards.md:136"
            },
            {
              "name": "Expected blocks per epoch",
              "symbol": "N_b / EXPECTED_BLOCKS_PER_EPOCH",
              "value": "10k = 21,600",
              "citation": "cryptarchia-v1-protocol.md:146; bedrock-v1.1-mantle-specification.md:1780"
            },
            {
              "name": "Lottery threshold, first-order coefficient",
              "symbol": "t_0",
              "value": "t_0_constant // inferred_total_stake, with t_0_constant = 0x1a3fb997fd5838f2a1585ee090a95c88129ab25cc4d2e2d28f1a95f81d85465",
              "citation": "cryptarchia-proof-of-leadership.md:220, :222, :240"
            },
            {
              "name": "Lottery threshold, second-order coefficient",
              "symbol": "t_1",
              "value": "p - (t_1_constant // inferred_total_stake^2), with t_1_constant = 0x71e790b4199113a9a00298d823c5716ddac764a110a45fe3b770bbb3e8a57",
              "citation": "cryptarchia-proof-of-leadership.md:221, :223, :241"
            },
            {
              "name": "VRF order / field modulus (BN254 scalar field)",
              "symbol": "p = VRF_order",
              "value": "0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001",
              "citation": "cryptarchia-proof-of-leadership.md:214, :219, :231"
            },
            {
              "name": "Inferred total stake (lottery difficulty)",
              "symbol": "D / inferred_total_stake",
              "value": "UNSET at steady state (recomputed each epoch by infer_total_active_stake(D^{ep-1}, N_BLOCKS^{ep-1}), specified in cryptarchia-total-stake-inference.md). Genesis value D_GENESIS = "the total tokens distributed at genesis" â no number given.",
              "citation": "cryptarchia-v1-protocol.md:156, :226; bedrock-genesis-block.md:317"
            },
            {
              "name": "Note value / stake weight of the leadership note",
              "symbol": "v",
              "value": "UNSET (per-note private input)",
              "citation": "cryptarchia-proof-of-leadership.md:163, :181"
            },
            {
              "name": "Epoch nonce",
              "symbol": "eta",
              "value": "UNSET (evolved per block; eta^{ep} = epoch_nonce_at_slot(sl_{ep-1} + floor(6k/f), tip))",
              "citation": "cryptarchia-v1-protocol.md:179, :216"
            },
            {
              "name": "Minimum stake to win the leadership lottery",
              "symbol": "(none)",
              "value": "NONE â explicitly no requirement for leaders",
              "citation": "overview-cryptoeconomics.md:149, :152"
            },
            {
              "name": "Minimum stake (SDP services only; NOT leadership)",
              "symbol": "min_stake.stake_threshold",
              "value": "UNSET numerically in the normative spec (methodology only, in analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md)",
              "citation": "bedrock-service-declaration-protocol.md:88; bedrock-v1.1-mantle-specification.md:1119"
            },
            {
              "name": "Note aging requirement",
              "symbol": "C_LEAD / ledger_AGED",
              "value": "Note must be unspent AND present in the note set at the start of the PREVIOUS epoch (snapshot slot sl_{ep-1} = (ep-1)*EPOCH_LENGTH). Effective minimum age is thus one full epoch, maximum two.",
              "citation": "cryptarchia-v1-protocol.md:160, :208, :212; cryptarchia-proof-of-leadership.md:145"
            },
            {
              "name": "Voucher Merkle tree depth",
              "symbol": "(none)",
              "value": "32",
              "citation": "bedrock-anonymous-leaders-reward.md:123"
            },
            {
              "name": "Vouchers per block",
              "symbol": "leader_voucher",
              "value": "exactly 1, 32 bytes, in the block header's ProofOfLeadership",
              "citation": "bedrock-v1.1-block-construction.md:122, :130"
            },
            {
              "name": "Voucher commitment domain separator",
              "symbol": "REWARD_VOUCHER",
              "value": "b"REWARD_VOUCHER" (little-endian, modulus p)",
              "citation": "bedrock-anonymous-leaders-reward.md:66-68"
            },
            {
              "name": "Voucher nullifier domain separator",
              "symbol": "VOUCHER_NF",
              "value": "b"VOUCHER_NF" (little-endian, modulus p)",
              "citation": "bedrock-anonymous-leaders-reward.md:134-136"
            },
            {
              "name": "Lottery ticket domain separator",
              "symbol": "LEAD_V1",
              "value": "LEAD_V1 (ticket = Poseidon2(LEAD_V1 || eta || sl || noteID || sk))",
              "citation": "cryptarchia-proof-of-leadership.md:180"
            },
            {
              "name": "Entropy-contribution domain separator",
              "symbol": "NONCE_CONTRIB_V1",
              "value": "NONCE_CONTRIB_V1 (rho_LEAD = hash(NONCE_CONTRIB_V1 || sl || noteID || sk))",
              "citation": "cryptarchia-proof-of-leadership.md:185"
            },
            {
              "name": "Leader claim operation opcode",
              "symbol": "LEADER_CLAIM",
              "value": "0x30",
              "citation": "bedrock-v1.1-mantle-specification.md:258"
            },
            {
              "name": "Execution gas for a leader claim",
              "symbol": "EXECUTION_LEADER_CLAIM_GAS",
              "value": "580",
              "citation": "bedrock-v1.1-mantle-specification.md:2254"
            },
            {
              "name": "Max block transactions",
              "symbol": "MAX_BLOCK_TXS",
              "value": "1024",
              "citation": "cryptarchia-v1-protocol.md:98"
            },
            {
              "name": "Max block size",
              "symbol": "MAX_BLOCK_SIZE",
              "value": "1 MB (cryptarchia-v1-protocol.md:97); overview-cryptoeconomics.md:115 says 1 MiB",
              "citation": "cryptarchia-v1-protocol.md:97; overview-cryptoeconomics.md:115"
            },
            {
              "name": "Fee share diverted to the PoW pool before the burn (reduces the burn that feeds the block reward, hence the leader reward)",
              "symbol": "POW_SHARE / SHARE_DEN (beta)",
              "value": "10/100 = 1/10",
              "citation": "bedrock-v1.1-mantle-specification.md:1806-1807; overview-cryptoeconomics.md:187"
            },
            {
              "name": "Block-reward emission constants (context for get_block_rewards)",
              "symbol": "A_SCALE, INFLATION_NUMERATOR, INFLATION_DENOMINATOR, FEE_AVG_NUMERATOR, STAKE_TARGET",
              "value": "120_000_000; 62_500; 657; 10_512; int(3e9)",
              "citation": "block-rewards.md:478-482"
            },
            {
              "name": "Max annual emission rate",
              "symbol": "I_max",
              "value": "1%",
              "citation": "block-rewards.md:167"
            },
            {
              "name": "Token supply at TGE",
              "symbol": "S_tge",
              "value": "10 billion LGO",
              "citation": "block-rewards.md:160"
            },
            {
              "name": "Block-rewards time step",
              "symbol": "Delta_t",
              "value": "1/(365 * 2880)  â one block every 30 seconds",
              "citation": "block-rewards.md:170"
            },
            {
              "name": "Block-rewards 'f' (DIFFERENT symbol from Cryptarchia's f)",
              "symbol": "f (block-rewards.md)",
              "value": "1 â "The average number of block proposal within Delta_t"",
              "citation": "block-rewards.md:169"
            },
            {
              "name": "Base fee initial value (tips are computed against it)",
              "symbol": "b_exec[0]",
              "value": "1",
              "citation": "execution-market.md:95"
            },
            {
              "name": "Genesis leader voucher",
              "symbol": "leader_voucher (genesis)",
              "value": "0 / bytes(32) â "as there is no leader block reward for the initial block"",
              "citation": "bedrock-genesis-block.md:201, :215"
            },
            {
              "name": "Initial value of the leader reward pool",
              "symbol": "leaders_rewards (genesis)",
              "value": "UNSET â no genesis seed is specified for this pool (only the PoW reward pool is explicitly seeded at genesis)",
              "citation": "bedrock-v1.1-mantle-specification.md:1578 (PoW pool seeding); no corresponding statement for leaders_rewards anywhere"
            }
          ],
          "eligibility": "WHO CAN RECEIVE THE LEADER REWARD

Gate 1 â win the lottery in a slot. Any holder of an eligible note. Eligible means
(cryptarchia-v1-protocol.md:160) "not been spent and was a member of the note set at the
beginning of the previous epoch". Enforced cryptographically as dual Merkle membership:
the note ID must be in ledger_AGED (the commitment root at slot (ep-1)*EPOCH_LENGTH,
cryptarchia-v1-protocol.md:212) and in ledger_LATEST (proving unspent,
cryptarchia-proof-of-leadership.md:148-149, :179).

Gate 2 â win condition. ticket < t, where
  ticket = Poseidon2(LEAD_V1 || eta || sl || noteID || sk)   [cryptarchia-proof-of-leadership.md:180]
  t      = v * (t_0 + t_1 * v)                                [cryptarchia-proof-of-leadership.md:181]
Stake weight enters ONLY through v, the note's value, as the second-order Taylor expansion
of phi_f(alpha) = 1 - (1-f)^alpha with alpha = v/inferred_total_stake. Win probability per
slot per note is therefore ~ f * v/D at leading order. Independence-of-notes: the ticket is
per-noteID, so splitting a holding across notes gives (to first order) the same aggregate
rate, with a small second-order gain because t_1 < 0 penalises large single notes.

Gate 3 â NO MINIMUM STAKE. overview-cryptoeconomics.md:149: "Blend nodes must stake a minimum
amount while leaders have no such requirement". overview-cryptoeconomics.md:152: "Leaders who
cannot afford the minimum stake can still earn enough to eventually reach it." No threshold
appears in cryptarchia-v1-protocol.md, cryptarchia-proof-of-leadership.md, or
bedrock-v1.1-block-construction.md. The SDP minimum stake
(bedrock-service-declaration-protocol.md:88) governs SERVICE declaration only.

Gate 4 â produce a valid block. The winner constructs a proposal
(bedrock-v1.1-block-construction.md:139: "The node becomes a leader only after successfully
generating a valid PoL for a given (Epoch, Slot)"), binds the PoL to a ONE-TIME Ed25519 key
that signs the block (cryptarchia-proof-of-leadership.md:189-193: "The key is single-use, as
reusing the same one could allow multiple PoLs to be linked to the same identity"), and puts
a fresh random voucher commitment in the header.

Gate 5 â claim. Anyone holding the secret voucher behind any commitment that is (a) in the
voucher Merkle tree as of the root frozen at the start of the current epoch, and (b) whose
nullifier is not yet in the nullifier set. The claimant proves membership in ZK without
revealing which leaf (bedrock-anonymous-leaders-reward.md:127), so the claim is unlinkable to
any block. Claims are not time-limited by anything the specs state â a voucher from any past
epoch remains claimable ("each unclaimed reward (since genesis) representing one equal share
of the pool", overview-cryptoeconomics.md:63).

CRITICALLY FOR THE SIMULATOR: what a leader receives is NOT a function of the block it
proposed. It is floor(leaders_rewards / #unclaimed_vouchers) evaluated at claim time. A
leader's expected total income is (number of blocks it proposed) x (the per-share value at
whatever times it chooses to claim). Bedrock-anonymous-leaders-reward.md:87: "every leader
will receive a reward that is independent of the block content to avoid de-anonymization."",
          "timing": "PER SLOT (1 second, cryptarchia-v1-protocol.md:96): one lottery instance per slot per note.
A slot is occupied with target probability f = 1/30; "For each slot, we can have 0 or more
winners" (cryptarchia-v1-protocol.md:232) â so the block rate is Poisson-ish at ~1 block per
30 slots = 1 block per 30 seconds, and simultaneous winners are "guaranteed forks".

PER BLOCK:
  - The block reward for that block is computed from the emission model
    (block-rewards.md:484-500), taking the fees burnt in that block as input.
  - The leader's 40% is NOT paid out. Nothing goes to the proposer at proposal time.
  - The proposer embeds one fresh `leader_voucher` commitment in the header
    (bedrock-anonymous-leaders-reward.md:70; bedrock-v1.1-block-construction.md:122).
  - The voucher is NOT yet in the tree; it sits until the epoch boundary.

PER EPOCH BOUNDARY (start of epoch e+1, for blocks of epoch e). Two things happen atomically,
both during execution of the FIRST block of the new epoch:
  1. Voucher admission: "Each `voucher_cm` is added to a Merkle tree of voucher commitments by
     validators during the execution of the first block of the following epoch"
     (bedrock-anonymous-leaders-reward.md:72); "Append the `leader_voucher` contained in the
     block to the set of reward vouchers **when the following epoch starts**"
     (bedrock-v1.1-block-construction.md:241).
  2. Pool credit: `leaders_rewards += sum over blocks b of epoch e of
     [0.4 * get_block_rewards(b) + get_execution_market_tips(b)]`
     (overview-cryptoeconomics.md:166-173; bedrock-anonymous-leaders-reward.md:91: "At the
     start of epoch N+1, validators aggregate the leaders rewards of epoch N into the leader
     rewards variable.")

LAG: a block proposed in epoch e yields a claimable share no earlier than the start of
epoch e+1. Worst case the lag is one full epoch (7.5 days) for a block early in epoch e,
best case ~one block for a block at the very end of epoch e. Mean lag ~ half an epoch
(~3.75 days) â this mean is DERIVED, not stated.

WITHIN AN EPOCH: the root used in claims is frozen â `assert claim.rewards_root ==
last_voucher_root` where last_voucher_root is "The last root of the voucher Merkle tree at the
start of the epoch" (bedrock-v1.1-mantle-specification.md:1489-1499). The numerator
(leaders_rewards) and the denominator (unclaimed count) both decrease by one share / one
voucher per claim, so the share is stable up to rounding
(bedrock-anonymous-leaders-reward.md:102): writing leader_rewards = q*n + r at the start of
the epoch, "the first n-r leaders to claim receive q and the last r receive q+1."

CLAIM TIME: the leader chooses. The share is "computed when the claim Operation is executed"
(overview-cryptoeconomics.md:140). The reward is minted as a single output note under a
public key the claimant chooses (bedrock-v1.1-mantle-specification.md:1519-1527), and
leaders_rewards is decremented by the same amount (:1529). The claim transaction pays
EXECUTION_LEADER_CLAIM_GAS = 580 execution gas
(bedrock-v1.1-mantle-specification.md:1480, :2254), and can atomically spend the reward in
the same transaction (bedrock-anonymous-leaders-reward.md:85).

EPOCH SCHEDULE (cryptarchia-v1-protocol.md:138-144), for the lottery constants the simulator
must roll forward: Stake Distribution Snapshot = s slots; Buffer = s slots; Lottery Constants
Finalization = s + floor(k/f) = 4*floor(k/f) slots. eta^ep is read at
sl_{ep-1} + floor(6k/f) (:216). D^ep is inferred from the block count in the FIRST
floor(6k/f) slots of the previous epoch (:224-226).",
          "ambiguities": [
            "ROUNDING AND ORDER OF THE 40% SPLIT â the two documents disagree. overview-cryptoeconomics.md:170 uses floating-point per block and sums: `leader_rewards += 0.4 * get_block_rewards(b)`. block-rewards.md:498 uses integer floor division per block on the reward NUMERATOR before the split: `leader_reward = reward_numerator * 4 // (reward_denominator * 10)`. These differ (a) by rounding â the integer form floors each block's leader share, discarding up to 1 lepton per block, ~21,600 leptons per epoch; and (b) structurally â the integer form never materialises a single 'block reward' that is then split, it computes the two shares directly from reward_numerator/reward_denominator, so blend_reward + leader_reward may be less than the block reward by up to 2 units per block. Neither document says which is normative. Simulator must choose; the integer form in block-rewards.md is the 'reference implementation' and is the more likely intent.",
            "THE PSEUDOCODE AT overview-cryptoeconomics.md:166-173 IS INTERNALLY INCONSISTENT ABOUT WHICH EPOCH IT ITERATES. The signature comment says 'e: epoch # rewards for the epoch e'; the loop is over `e.blocks` with the comment '# for each block of the previous epoch'; and the prose at line 164 says 'The blocks from the previous epoch are denoted by B in the pseudocode below' â but no B appears in the code. The same inconsistency is in get_blend_reward (lines 157-159). The prose elsewhere (bedrock-anonymous-leaders-reward.md:91) is unambiguous: at the start of epoch N+1, epoch N's rewards are aggregated. Simulator should follow the prose.",
            "SYMBOL COLLISION ON f. cryptarchia-v1-protocol.md:94 defines f = 1/30 as the slot activation coefficient. block-rewards.md:169 defines f = 1 as 'The average number of block proposal within Delta_t', and INFLATION_NUMERATOR/INFLATION_DENOMINATOR at block-rewards.md:479-480 are labelled 'numerator/denominator of I_max * S_TGE * DELTA_t / f' using THIS f. They are unrelated quantities with the same letter. Getting them confused would misscale the emission by a factor of 30.",
            "TIPS: WHERE IN THE ORDER DO THEY ENTER, AND ARE THEY SUBJECT TO THE 60/40 SPLIT? overview-cryptoeconomics.md:170-171 adds tips to leader_rewards AFTER and IN ADDITION TO the 40% share, i.e. leaders get 100% of tips. execution-market.md:52 reads 'we mint rewards to which we add tips which are given to the block builders', consistent. But execution-market.md:62 reads 'The priority_fee ... is directed into the block builders reward stream. 40% of the rewards will be allocated to block builders and the remaining 60% to Blend nodes' â which on one reading applies the 40/60 split to the tips too. The pseudocode is the more specific statement and gives leaders 100% of tips; flagging because the sentence in execution-market.md:62 can be read the other way.",
            "WHETHER THE GENESIS BLOCK'S ZERO VOUCHER ENTERS THE ANONYMITY SET. bedrock-genesis-block.md:201 sets `leader_voucher: 0 (as there is no leader block reward for the initial block)` and :290 says 'processing of `proof_of_leadership` is skipped'. But bedrock-v1.1-block-construction.md:241 says unconditionally to append the block's leader_voucher at the next epoch start. If a zero leaf were admitted it would be an unclaimable voucher permanently inflating the denominator |voucher_cm| - |voucher_nf| by 1 and stranding one share forever. The genesis spec's parenthetical strongly implies exclusion but no rule states it.",
            "WHETHER VOUCHERS FROM ORPHANED/FORKED BLOCKS ENTER THE SET. Everything is phrased in terms of 'the blocks of epoch e' with no explicit statement that only canonical-chain blocks count. Implicit from block execution being chain-state, but not stated. Matters for a simulator that models forks (which per cryptarchia-v1-protocol.md:232 do occur when two leaders win the same slot).",
            "THE SHARE FORMULA'S SETS ARE READ AT CLAIM TIME, NOT FROZEN AT EPOCH START. bedrock-anonymous-leaders-reward.md:91-98 computes share from the CURRENT |voucher_cm| and |voucher_nf|. bedrock-anonymous-leaders-reward.md:102 and overview-cryptoeconomics.md:214 both describe the amount as 'almost stable'/'stable during an epoch'. These reconcile (both numerator and denominator shrink together), but note the mantle spec at bedrock-v1.1-mantle-specification.md:1513 passes `leader_reward: TokenValue  # The amount one leader can claim` in as a GIVEN without saying when it is computed, which reads as if it could be an epoch-frozen value like the PoW pool's `epoch_pow_reward` (which explicitly IS frozen, :1820). It is not â bedrock-anonymous-leaders-reward.md is explicit that it is recomputed per claim.",
            "THE REFERENCE IMPLEMENTATION AT block-rewards.md:493-494 DOES NOT PARSE. `reward_numerator = INFLATION_NUMERATOR * a_numerator` is followed by a separate indented line beginning `+ INFLATION_DENOMINATOR * (A_SCALE - a_num) * last_burned_fee` with no line continuation, and references `a_num` where `a_numerator` is defined. The intent is clear from the LaTeX at block-rewards.md:471 but the code as written is broken.",
            "MAX BLOCK SIZE IS GIVEN AS '1 MB' AT cryptarchia-v1-protocol.md:97 AND '1 MiB' AT overview-cryptoeconomics.md:115. Minor, and not on the leader-reward path, but noted."
          ],
          "not_specified": [
            "`get_execution_market_tips(b)` IS NEVER DEFINED. It is called at overview-cryptoeconomics.md:171 and defined nowhere in the tree. execution-market.md gives p_t = c_t - b_exec[s] (line 213) and F_t = g_t*c_t (line 219) and defines the burnt quantity R_burned(s) = sum_t g_t*b_exec[s] (lines 224-226), but never writes the tip aggregate. The obvious reading (sum over transactions of g_t * p_t) is DERIVED â see derived_not_stated. Do not treat it as quoted.",
            "`get_block_rewards(b)` IS NEVER DEFINED UNDER THAT NAME. block-rewards.md defines Rewards_t (line 456) and the function `block_reward(total_stake, burned_fees_window)` (line 484) which already returns the split pair. The mapping between the two APIs is left implicit.",
            "THE INITIAL VALUE OF `leaders_rewards` AT GENESIS. The PoW reward pool has an explicit genesis seed (bedrock-v1.1-mantle-specification.md:1578, :2125). Nothing analogous is stated for leaders_rewards. Presumably 0, but the specification does not state this.",
            "ANY EXPIRY OR DEADLINE ON VOUCHERS. Nothing in bedrock-anonymous-leaders-reward.md or the mantle spec caps how long a voucher stays claimable, and overview-cryptoeconomics.md:63 says the denominator counts unclaimed rewards 'since genesis'. So the equilibrium share depends entirely on claimant behaviour, which the specification does not model. A simulator MUST choose a claiming policy; the spec offers only the soft hint at bedrock-anonymous-leaders-reward.md:102 that 'The marginally larger reward of the late claimants also mildly encourages leaders to spread their claims over time'.",
            "WHETHER THE PoW-POOL DIVERSION APPLIES BEFORE OR AFTER THE BURN THAT FEEDS THE BLOCK REWARD, IN NUMERIC TERMS. overview-cryptoeconomics.md:195 says the diversion 'reduces that measurement by the same share' â so the block reward input R_block is (1 - POW_SHARE/SHARE_DEN) of the fees collected. Stated as prose; no formula ties get_collected_fees(b) to R_block = D_{1,t}.",
            "NUMERIC GENESIS VALUE OF inferred_total_stake. bedrock-genesis-block.md:317 says only 'the total tokens distributed at genesis'. The genesis distribution itself is not given as a number in the documents read. S_tge = 10 billion LGO (block-rewards.md:160) is the TOTAL supply at TGE, which is not the same as the staked/distributed amount for lottery purposes.",
            "THE EXACT `infer_total_active_stake` FUNCTION. cryptarchia-v1-protocol.md:226 invokes it and defers to cryptarchia-total-stake-inference.md (not read for this stream). Its output D is the denominator of t_0 and t_1 and therefore directly sets the block rate.",
            "WHETHER A LEADER MAY PROPOSE MORE THAN ONE BLOCK PER SLOT (e.g. with several winning notes). The lottery is per-note (ticket includes noteID), so multiple notes could win the same slot for one holder, but no rule states whether more than one block may be proposed. Not on the reward path except that it would yield more than one voucher.",
            "NO MINIMUM STAKE FOR LEADERSHIP IS SPECIFIED â and this is an affirmative 'none', not an omission. overview-cryptoeconomics.md:149 states leaders 'have no such requirement'. Listing it here so the simulator does not go looking for one."
          ],
          "derived_not_stated": [
            "DERIVED: numeric epoch length. floor(k/f) = 2160 / (1/30) = 64,800 slots; EPOCH_LENGTH = 10 * 64,800 = 648,000 slots = 648,000 seconds = 7.5 days. The formula 10*floor(k/f) IS stated (cryptarchia-v1-protocol.md:144) and '7.5 days' appears at block-rewards.md:136, but the 648,000 figure is not written anywhere.",
            "DERIVED: s = 3*floor(k/f) = 194,400 slots; the 2s point where eta and D are computed = 388,800 slots in; floor(6k/f) = 388,800. The formulas are stated (cryptarchia-v1-protocol.md:104, :142, :216, :224), the numbers are not.",
            "DERIVED: mean block interval = 1/f = 30 seconds; consistent with block-rewards.md:170's Delta_t = 1/(365*2880) which is exactly '1 block every 30 seconds' with 2880 blocks/day. 2880 * 7.5 = 21,600 blocks/epoch, matching the 10k figure at cryptarchia-v1-protocol.md:146. Cross-check is mine, the coincidence is stated only implicitly.",
            "DERIVED: per-slot win probability for a note of value v is P = t/p = v*(t_0 + t_1*v)/p, which equals the Taylor expansion of phi_f(v/D) = 1 - (1-f)^(v/D) ~= (v/D)*(-ln(1-f)) - 0.5*(v/D)^2*ln^2(1-f). At leading order P ~= f*v/D for small f. The expansion IS stated (cryptarchia-proof-of-leadership.md:207); the reading of 'ticket < t over a uniform field element' as giving probability t/p is my inference from ticket being a Poseidon2 output over F_p (cryptarchia-proof-of-leadership.md:214).",
            "DERIVED: `get_execution_market_tips(b)` = sum over transactions t in block b of g_t * p_t = sum of g_t*(c_t - b_exec[s]). This follows from execution-market.md:96, :103, :213, :219 and from R_burned counting only the base-fee part (:224-226), but the aggregate is never written. NOT A QUOTED FORMULA.",
            "DERIVED: a leader's expected number of vouchers per epoch = 21,600 * (its stake / inferred_total_stake), assuming its stake is aged and unspent and the inference is accurate.",
            "DERIVED: in steady state with all vouchers eventually claimed and a stationary claim policy, the per-share value tends to (epoch leader income) / (vouchers admitted per epoch) = (0.4 * sum of block rewards + sum of tips) / 21,600. This is the natural fixed point but the specification does not state it, and it holds only if the unclaimed-voucher backlog is stationary. If leaders delay claiming, the backlog grows and the per-share value falls below this while total value per leader is preserved.",
            "DERIVED: mean lag from block proposal to claimability ~= half an epoch ~= 3.75 days (uniform over the epoch). Bounds (one block to one full epoch) follow from the epoch-boundary rule at bedrock-v1.1-block-construction.md:241; the mean is arithmetic of mine.",
            "DERIVED: the block reward available to split is reduced by the PoW diversion in the recycling regime, so the leader's effective take is 0.4 * f(0.9 * fees) rather than 0.4 * f(fees). overview-cryptoeconomics.md:197 states the direction and the 60/40 incidence in prose; the composition with POW_SHARE = 10/100 is mine.",
            "DERIVED: t_1 stored as p - |t_1| means the real-valued threshold is v*t_0 - v^2*|t_1|. The spec states the storage convention (cryptarchia-proof-of-leadership.md:223, :241) and separately describes the parabola (:296), but does not spell out the sign handling that a simulator must implement to reproduce the wrap-around behaviour at v >> D."
          ]
        },
        "check": {
          "stream": "THE LEADER REWARD â 40/60 split, voucher-based anonymous claim, lottery win condition and stake weighting, note aging, minimum-stake question, slot/block relationship.",
          "citations_verified": true,
          "invented_elements": [
            "NONE FABRICATED. No formula, parameter, or numeric value in the extraction is absent from the source. Every quoted block I checked is verbatim â including the two deliberate warts (`a_num` at block-rewards.md:494 and the broken continuation at 493-494), the hex constants at cryptarchia-proof-of-leadership.md:219-221, and the LaTeX share formula at bedrock-anonymous-leaders-reward.md:93-98. The items below are DERIVED reasoning stated in narrative voice without a derived-flag; they are not fabrications of source text, but a reader could mistake them for spec.",
            "UNFLAGGED DERIVATION (parameters, 'Note aging requirement'): 'Effective minimum age is thus one full epoch, maximum two.' cryptarchia-v1-protocol.md:160 and :208-212 state only membership in commitment_root_at_slot((ep-1)*EPOCH_LENGTH). The one-to-two-epoch window is correct arithmetic but is nowhere in the source, and unlike the other derivations it is not listed in derived_not_stated.",
            "UNFLAGGED DERIVATION (eligibility, Gate 2): 'Independence-of-notes: the ticket is per-noteID, so splitting a holding across notes gives (to first order) the same aggregate rate, with a small second-order gain because t_1 < 0 penalises large single notes.' Correct, but no such statement exists in cryptarchia-proof-of-leadership.md. The spec's only discussion of note-value scale is the corner case at :283-315 (v >> D), which is the opposite regime.",
            "IMPRECISE DERIVATION (eligibility, Gate 2 and derived_not_stated): 'Win probability per slot per note is therefore ~ f * v/D at leading order.' The spec's leading coefficient is -ln(1-f), not f (cryptarchia-proof-of-leadership.md:210, :257). At f = 1/30 these differ by 1.7% (0.033901 vs 0.033333). A simulator seeded with f*v/D reproduces a block rate ~1.7% below what the specified t_0 actually produces. The extraction does state the -ln(1-f) form correctly elsewhere; only the shorthand is off."
          ],
          "wrong_citations": [
            "PARTIAL â parameters, 'Fee share diverted to the PoW pool', value '10/100 = 1/10', cited as 'bedrock-v1.1-mantle-specification.md:1806-1807; overview-cryptoeconomics.md:187'. The mantle citation is exact (1806: `POW_SHARE: uint64 = 10`, 1807: `SHARE_DEN: uint64 = 100`). overview-cryptoeconomics.md:187 contains NO number: it reads '...and `POW_SHARE / SHARE_DEN` is the fraction diverted. The share is computed with integer division, which rounds down...'. The concept is there, the value is not. Anyone chasing the 1/10 from the overview citation finds nothing.",
            "NO OTHER WRONG CITATIONS. Spot-checked all ~100 entries in the citations array against the files. Every one lands on the claimed content, including the awkward cases: bedrock-anonymous-leaders-reward.md:91 legitimately serves both the 'At the start of epoch N+1, validators aggregate...' prose (main text) and the opening of the share-formula range 91-98; bedrock-v1.1-mantle-specification.md:1489-1490 does span the two-line comment 'The last root of the voucher Merkle tree / at the start of the epoch'; execution-market.md:210-214 and :222-227 do enclose p_t and R_burned respectively."
          ],
          "missed_elements": [
            "THE STAKE-INFERENCE ALGORITHM IS FULLY SPECIFIED AND THE EXTRACTION SAYS IT ISN'T. not_specified claims 'THE EXACT `infer_total_active_stake` FUNCTION ... defers to cryptarchia-total-stake-inference.md (not read for this stream)'. That file is 87 lines and contains a complete reference implementation at lines 63-83: `fn total_stake_inference(total_stake_estimate: u64, epoch_slot: u64) -> u64` with PRECISION = 1e3, and a parameter table at :49-52 giving `beta` = 1.0 (learning rate) and `PERIOD` = 6*floor(k/f) (observation period). The update is D_new = D - beta*D*(expected_density - measured_density)/expected_density, floored at 1. This is the feedback loop that sets D, hence t_0/t_1, hence the block rate, hence the entire reward flow. It is the single most load-bearing omission for a simulator.",
            "TOKEN UNITS ARE NEVER ESTABLISHED, AND THE SPEC IS INTERNALLY INCONSISTENT ABOUT THEM. bedrock-v1.1-mantle-specification.md:2119: 'The indivisible unit is the lepton, and one LGO is $`10^{9}`$ lepta. `TokenValue` counts lepta: every quantity of that type â note values, balances, fees, prices and pool balances â is an integer number of lepta'. :2123: 'The maximum minted block reward derived in [Block Rewards] is $`62500/657`$ LGO ... where an integer is required it is rounded down, losing less than one lepton per block.' But the reference implementation the extraction quotes verbatim works in LGO, not lepta: INFLATION_NUMERATOR/INFLATION_DENOMINATOR = 62500/657 is 95.13 LGO/block, and STAKE_TARGET = int(3e9) is 3 billion LGO (block-rewards.md:165, D_0,target = '3 billion LOGOS'). A simulator that treats block_reward()'s output as TokenValue lepta is off by 10^9. The extraction's ambiguity #1 casually says 'up to 1 lepton per block' without ever establishing what a lepton is or noting the unit mismatch.",
            "THE PARAMETRIZATION TABLE THAT GIVES THE MAGIC CONSTANTS THEIR MEANING. block-rewards.md:158-170 is cited only for :160, :167, :169, :170. Also there and needed to reproduce FEE_AVG_NUMERATOR = 10_512 and A_SCALE = 120_000_000: T = 120 (:161, 'the minting averages the fees burned in the last hour'), alpha_a = 1 (:162), alpha_d = 1/4 (:163), D_0,target = 3 billion LOGOS (:165), D_1,target = 10 billion LOGOS (:166, 'this value behaves as a normalizer'). Without D_1,target and T the extraction's block_reward() is an opaque box; with them, A_SCALE = 1/(I_max*D1_target*Delta_t*T) is reconstructible.",
            "THE TWO SPECS DESCRIBE THE PAYOUT MECHANISM DIFFERENTLY AND THE EXTRACTION SILENTLY PICKS ONE. bedrock-anonymous-leaders-reward.md:112 says the effect is 'Increase the balance of the Mantle Transaction by the share amount' (a balance credit consumed by other Operations in the same tx). bedrock-v1.1-mantle-specification.md:1519-1526 says 'construct a single output note with value leader_reward under the public key defined in the payload, and insert it into the Ledger'. The extraction reports only the mantle version. These differ for a simulator modelling UTXO growth and note counts, and the anonymous-leaders-reward version is what makes :85's atomic spend work.",
            "THE EXECUTION-MARKET CONSTANTS THAT DRIVE R_burned. execution-market.md:99-102: G_max = 3,193,460, G_target = 1,596,730 ('half of G_max'), phi = 1/8 (fee adjustment rate), q = 9/10 (EMA smoothing, 'economically equivalent to a lookback period of approximately 19 blocks'), plus the base-fee update at :201-203 with ceil rounding. The extraction takes R_burned as an exogenous input. If the simulator is to generate its own fee stream rather than being handed one, these are required, and the ceil-vs-floor rounding rationale at :206 matters (base fee floor is 1, 0 would be absorbing).",
            "LEADER CLAIMS HAVE NO EXPIRY *AND THE SPEC SHOWS IT KNEW HOW TO WRITE ONE*. The extraction correctly reports no deadline, but strengthening evidence is unused: the PoW claim path has an explicit 'Window of Acceptance' (bedrock-v1.1-mantle-specification.md:1580-1585, EXPECTED_BLOCKS_PER_WINDOW = 10) so that 'a solution cannot be presented arbitrarily long after it was found'. The absence of any analogue in the LEADER_CLAIM section is a deliberate contrast, not an oversight.",
            "THE NO-OVERDRAW INVARIANT. bedrock-anonymous-leaders-reward.md:100 is cited only for 'integer division over TokenValue'. The rest of that line is a simulator-relevant guarantee: 'Rounding down guarantees that share x (|voucher_cm| - |voucher_nf|) <= leader_rewards, an inequality that every claim preserves since it decreases both sides by one share and one voucher respectively. The pool can therefore never be overdrawn and every unclaimed voucher remains payable.' A simulator can assert this."
          ],
          "corrections": [
            "UNSET/SPECIFIED AUDIT â the four UNSET verdicts are genuine. (1) `inferred_total_stake` at steady state: correctly UNSET; genesis is bedrock-genesis-block.md:317 'The initial estimate of total stake will be the total tokens distributed at genesis' â no number, confirmed. (2) Note value v: correctly UNSET, it is a private circuit input at cryptarchia-proof-of-leadership.md:163. (3) Epoch nonce eta: correctly UNSET, evolved per block per cryptarchia-v1-protocol.md:168-184. (4) `leaders_rewards` at genesis: correctly UNSET â I grepped the whole raw/ tree for `leaders_rewards`/`leader_rewards`; the only hits are overview-cryptoeconomics.md:167-172, bedrock-anonymous-leaders-reward.md:55/91/102/113, bedrock-v1.1-mantle-specification.md:1512/1529, and one appendix copy. No genesis seed exists, and bedrock-genesis-block.md:296-301 seeds only `pow_reward_pool`, `epoch_pow_reward`, `difficulty_blend`, `difficulty_reward`. Confirmed.",
            "CORRECTION to the fifth UNSET â the SDP minimum stake is NOT 'methodology only'. analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:119-122 states 'In order to lower even further any barriers to enter and promote decentralization, we set the minimum stake as: Stake_LGO = 0.001% * S_TGE' (also at :57-60), i.e. 100,000 LGO at S_TGE = 10 billion, with a bound at :116 of Stake_LGO <= 0.015% * S_TGE. It is unset in the normative spec (bedrock-service-declaration-protocol.md:88-95 defines only the `MinStake` structure and a uint64 `stake_threshold`) but the analysis picks a concrete value. Off the leader path, so harmless here, but the characterisation is wrong.",
            "SPECIFIED-vs-ILLUSTRATIVE AUDIT â everything the extraction presents as specified is genuinely normative, not an example. f = 1/30, k = 2160, slot = 1s, MAX_BLOCK_SIZE, MAX_BLOCK_TXS are the Value column of the Constants table at cryptarchia-v1-protocol.md:92-98. EXPECTED_BLOCKS_PER_EPOCH = 21_600 is a live constant (mantle:1780) and :1789 explicitly says it 'is not a free choice and is not defined here' but inherited from Cryptarchia â with the caveat, which the extraction omits, that 'the constant values throughout this section are **mainnet values**; a test network may substitute values sized to its expected activity'. POW_SHARE = 10 / SHARE_DEN = 100 are live constants (:1806-1807). The t_0/t_1 hex constants are a normative derivation table (:217-223), not an example; the sage block at :227-248 is explicitly the code that produced them. EXECUTION_LEADER_CLAIM_GAS = 580 is a real table row (:2254). LEADER_CLAIM = 0x30 is a real opcode row (:258). Merkle depth 32 is normative (bedrock-anonymous-leaders-reward.md:123). The only illustrative numbers I found nearby are ones the extraction correctly did NOT lift: 'inferred_total_stake is 23.5B as in Cardano' (cryptarchia-proof-of-leadership.md:255, error-analysis assumption only) and `secret_voucher = 0xDEADBEAF` (mantle:1534).",
            "The block-rewards Delta_t entry is right but the reason is worth stating: block-rewards.md:169 gives f = 1 with the justification 'The time step Delta_t was chosen so that f equals to 1', while :137-139 shows the same f taking 2880 (per-day step) or 21600 (per-epoch step). The extraction's symbol-collision warning (ambiguity #3) is correct and, if anything, understated â f in block-rewards.md is not a single-valued constant at all, it is whatever the chosen time step makes it.",
            "Ambiguity #7 slightly overstates the mantle spec's silence. It says :1513 'passes `leader_reward: TokenValue` in as a GIVEN without saying when it is computed'. mantle:1519 does say where it comes from: 'Denoting by `leader_reward` the amount defined for leader rewards in [Leaders Reward](bedrock-anonymous-leaders-reward.md#leaders-reward)'. The extraction's conclusion (recomputed per claim, not epoch-frozen) is right; the framing of the tension is a touch stronger than the text supports. The genuine contrast it draws with the frozen PoW value is exactly right and verified at mantle:1768-1770 ('If the reward varied within the epoch the wallet could not name the note in advance') and :1820 ('the per-claim value is not recomputed until the next boundary') â both of which are unambiguously in the PoW section, so no leader-side self-funding claim is implied.",
            "Ambiguity #2 is confirmed word for word. overview-cryptoeconomics.md:164 does say 'The blocks from the previous epoch are denoted by B in the pseudocode below:' and no B appears in lines 166-173. The identical defect is present in the blend function (:157 signature comment 'rewards for the epoch e' vs :159 loop comment 'for each block of the previous epoch'). Following the prose at bedrock-anonymous-leaders-reward.md:91 is the right call.",
            "Ambiguity #5 (genesis zero voucher) is real and correctly stated. bedrock-genesis-block.md:201 '`leader_voucher`: 0 (as there is no leader block reward for the initial block)' and :215 `leader_voucher=bytes(32)`; :290 'No validation or execution is done for the Genesis block header; in particular, processing of `proof_of_leadership` is skipped' â which is the closest thing to an exclusion rule and does arguably resolve it, since the append at bedrock-v1.1-block-construction.md:241 is part of Block Execution and genesis skips header processing. Worth stating that resolution rather than leaving it fully open."
          ],
          "verdict": "faithful"
        }
      },
      {
        "stream": "service",
        "formula": {
          "stream": "Service provision reward (Service Declaration Protocol + Service Reward Distribution Protocol; the only declared service is the Blend Network, `ServiceType.BN`)",
          "formula": "The SRDP itself specifies only a delegation, not a formula:

  bedrock-service-reward-distribution.md:70-76
  "At the end of epoch **N+1**, service rewards for the validator `n` for the epoch **N** are computed by the different services taking as input the rewards of the epoch:
   $$ Rewards^n := serviceReward(n,Rewards\_Epoch) $$
   Where $`Rewards\_Epoch`$ are the total rewards of epoch **N**. The $`Rewards\_Epoch`$ is determined by the linked reference, which calculates how much each service receives based on fees burnt during epoch N and the blockchain's state. $`Rewards^n`$ is stored as an array that maps each validator's `zk_id` to their allocated reward."

STEP 1 â the service's share of the block reward (the input $I$ / Rewards_Epoch).

  overview-cryptoeconomics.md:142-145
  "Each block reward of each block is split as follows between the Blend service and the leader:
   - 40% for the leader.
   - 60% for the Blend service."

  overview-cryptoeconomics.md:154-162
  "At the start of each Blend epoch, a Blend reward variable is computed. Its amount equals 60% of the total block rewards of the previous epoch:
   ```python
   def get_blend_reward(e: epoch): # rewards for the epoch e
       blend_rewards = 0
       for b in e.blocks: # for each block of the previous epoch
           blend_rewards += 0.6 * get_block_rewards(b) # get 60% of the rewards
       return blend_rewards
   ```"

  Integer form, block-rewards.md:484-500 (tail of the reference implementation; `block_reward` returns the pair):
   ```python
   def block_reward(total_stake: int, burned_fees_window: list[int]) -> tuple[int, int]:
       sum_fees = sum(burned_fees_window)
       last_burned_fee = burned_fees_window[-1]

       a_numerator = min(
           max(STAKE_TARGET + FEE_AVG_NUMERATOR * sum_fees - total_stake, 0),
           A_SCALE
       )

       reward_numerator = INFLATION_NUMERATOR * a_numerator
                          + INFLATION_DENOMINATOR * (A_SCALE - a_num) * last_burned_fee
       reward_denominator = INFLATION_DENOMINATOR * A_SCALE

       blend_reward = reward_numerator * 6 // (reward_denominator * 10)
       leader_reward = reward_numerator * 4 // (reward_denominator * 10)

       return blend_reward, leader_reward
   ```
  (reproduced verbatim, including the `a_num`/`a_numerator` and `R_block_cur` defects noted under ambiguities)

STEP 2 â the per-provider split, defined by the service (Blend), blend-protocol.md:1106-1126:

  "The node rewards for epoch $`s`$ are calculated according to the following schema:
   1. Rewards are not calculated if the number of nodes (unique `ProviderId`s from declarations) retrieved from the SDP protocol is lower than the [Minimal Network Size](#minimal-network-size).
   2. Count the number of true activity proofs registered on the ledger:
      $$B = \sum_{i=1}^{N}\mathrm{true}(\pi_{A}^{i,t,e})$$
      This value is used for calculating the base reward paid for all active nodes.
   3. Count the number of true activity proofs registered on the ledger with the smallest Hamming distanceâthat is, calculate the number of nodes with the minimal distance among all submitted active messages:
      $$P = \sum_{i=1}^{N}\min_{\Delta_{\mathcal H}}(\mathrm{true}(\pi_{A}^{i,t,e}))$$
      This value is used for calculating the premium reward, which is paid for all active nodes that have their activity proofs closest to the epoch randomness.
   4. Calculate the base reward:
      $$R = {I \over B + P}$$
      where $`I`$ is the value of income for the Blend Network service for the epoch $`s`$.  For more details about the income calculation, refer to linked reference.
   5. Calculate the reward of the node $`n`$:
      $$R(n) = R \cdot [\mathrm{true}(\pi_{A}^{i,t,e}) + \min_{\Delta_{\mathcal H}}(\mathrm{true}(\pi_{A}^{i,t,e}))]$$
      That is, a base reward ($`R`$) is paid out to all nodes who have submitted a true activity proof, and the reward is doubled for nodes that submitted a true proof with a minimal Hamming distance."

STEP 3 â the activity gate that decides whether a provider is counted in B (blend-protocol.md:1026-1036):

  "the activity proof is $`\text{true}`$ when: A node $`l`$ has a blending token $`t \in \mathcal{T}^{l,s}`$ collected during epoch $`e`$, and that: Proof of Quota ... is true ...; Proof of Selection ... is true ...
   - The Hamming distance ... between the blending token $`t`$ and the next epoch randomness $`R_{e+1}`$ is smaller than the node activity threshold $`\mathcal A _{\epsilon}`$. That is:
     $$\Delta_{\mathcal H}(H(t)_{\epsilon},H(R_{e+1})_{\epsilon}) < {\mathcal A}_{\epsilon}$$"

  Activity threshold, blend-protocol.md:1070-1080:
  "$$ {\mathcal A}_{\epsilon} = \chi - \nu- \theta $$
   - $`\nu=\left\lceil \log_2(N + 1) \right\rceil`$ ... number of nodes in the network $`N`$ ...;
   - $`\chi=\left\lceil\log_2(Q_C^{Total}+1)\right\rceil`$ ... where $`Q_C^{Total}`$ is the total number of cover messages generated by the network during an epoch ...;
   - $`\theta=1`$ represents a sensitivity parameter that controls the winning conditions of the lottery."

STEP 4 â payout mechanics, bedrock-service-reward-distribution.md:80-87:
  "Starting immediately after epoch **N+1**, service rewards are distributed in the first block of epoch **N+2.** The rewards are inserted directly in the ledger without triggering any Mantle validation. The `NoteId` is computed using the result of `hash(ServiceType || epoch_number)` as the `op_id`. The output number corresponds to the position of the `zk_id` when sorted in ascending order.
   The reward must:
   - Transfer the correct reward amount according to [Service Reward Calculation](#service-reward-calculation).
   - Be sent to the public key `zk_id` of the validator registered during declaration of the service.
   - Be distributed into a single note if several rewards share the same `zk_id`.
   - Be executed identically by every node processing the first block of epoch N+2. This happens by inserting notes in the ledger in ascending order of `zk_id`."",
          "citations": [
            "bedrock-service-reward-distribution.md:70-76",
            "bedrock-service-reward-distribution.md:45-49",
            "bedrock-service-reward-distribution.md:80-87",
            "bedrock-service-reward-distribution.md:91",
            "bedrock-service-reward-distribution.md:55",
            "bedrock-service-reward-distribution.md:62",
            "overview-cryptoeconomics.md:142-145",
            "overview-cryptoeconomics.md:147-152",
            "overview-cryptoeconomics.md:154-162",
            "overview-cryptoeconomics.md:164-173",
            "overview-cryptoeconomics.md:201",
            "overview-cryptoeconomics.md:218-224",
            "overview-cryptoeconomics.md:226-228",
            "block-rewards.md:477-501",
            "block-rewards.md:497-498",
            "block-rewards.md:158-171",
            "blend-protocol.md:1106-1126",
            "blend-protocol.md:1128-1137",
            "blend-protocol.md:1022-1045",
            "blend-protocol.md:1066-1082",
            "blend-protocol.md:1084-1104",
            "blend-protocol.md:148-158",
            "blend-protocol.md:583-602",
            "blend-protocol.md:473-481",
            "blend-protocol.md:546-570",
            "bedrock-service-declaration-protocol.md:34",
            "bedrock-service-declaration-protocol.md:40-41",
            "bedrock-service-declaration-protocol.md:51-61",
            "bedrock-service-declaration-protocol.md:63",
            "bedrock-service-declaration-protocol.md:73-84",
            "bedrock-service-declaration-protocol.md:86-104",
            "bedrock-service-declaration-protocol.md:106-123",
            "bedrock-service-declaration-protocol.md:125-130",
            "bedrock-service-declaration-protocol.md:132-137",
            "bedrock-service-declaration-protocol.md:151-171",
            "bedrock-service-declaration-protocol.md:172-199",
            "bedrock-service-declaration-protocol.md:217-228",
            "bedrock-service-declaration-protocol.md:282-295",
            "bedrock-service-declaration-protocol.md:297-312",
            "bedrock-service-declaration-protocol.md:314-328",
            "bedrock-service-declaration-protocol.md:356-364",
            "bedrock-v1.1-mantle-specification.md:1013-1043",
            "bedrock-v1.1-mantle-specification.md:1077-1128",
            "bedrock-v1.1-mantle-specification.md:1299-1314",
            "bedrock-v1.1-mantle-specification.md:1342-1384",
            "bedrock-v1.1-mantle-specification.md:1386-1434",
            "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:57-67",
            "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:91-97",
            "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:108-123",
            "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:148-172",
            "cryptarchia-v1-protocol.md:92-97",
            "cryptarchia-v1-protocol.md:144-146",
            "execution-market.md:60-62",
            "bedrock-genesis-block.md:90-109",
            "bedrock-genesis-block.md:319-323"
          ],
          "parameters": [
            {
              "name": "Blend/service share of the block reward",
              "symbol": "(none given; 60% / 6//10)",
              "value": "60% (0.6). Integer form: reward_numerator * 6 // (reward_denominator * 10), floored per block.",
              "citation": "overview-cryptoeconomics.md:145; overview-cryptoeconomics.md:160; block-rewards.md:497; overview-cryptoeconomics.md:201"
            },
            {
              "name": "Leader share of the block reward (complement)",
              "symbol": "(none given; 40% / 4//10)",
              "value": "40% (0.4)",
              "citation": "overview-cryptoeconomics.md:144; block-rewards.md:498"
            },
            {
              "name": "Blend service income for the epoch (input to the per-node split)",
              "symbol": "I  (= Rewards_Epoch for the BN service)",
              "value": "UNSET as a number; defined as sum over the epoch's blocks of 0.6 * block_reward(b)",
              "citation": "blend-protocol.md:1122; overview-cryptoeconomics.md:154-162; bedrock-service-reward-distribution.md:76"
            },
            {
              "name": "Number of nodes with a true activity proof registered for the epoch",
              "symbol": "B",
              "value": "UNSET (state-dependent; counted from the ledger)",
              "citation": "blend-protocol.md:1112-1114"
            },
            {
              "name": "Number of nodes with a true activity proof at the minimal Hamming distance (premium winners)",
              "symbol": "P",
              "value": "UNSET (state-dependent; counted from the ledger)",
              "citation": "blend-protocol.md:1116-1118"
            },
            {
              "name": "Base reward per active provider",
              "symbol": "R",
              "value": "R = I / (B + P)  â derived quantity, not a free parameter",
              "citation": "blend-protocol.md:1120-1122"
            },
            {
              "name": "Premium multiplier for minimal-Hamming-distance providers",
              "symbol": "(none)",
              "value": "2x the base reward (R(n) = R * [true + min])",
              "citation": "blend-protocol.md:1124-1126"
            },
            {
              "name": "Minimal Network Size (gate: below it, NO rewards are calculated at all)",
              "symbol": "(none)",
              "value": "32 unique ProviderIds from SDP declarations",
              "citation": "blend-protocol.md:148-150; blend-protocol.md:1110"
            },
            {
              "name": "Minimum stake threshold for a declaration",
              "symbol": "min_stake.stake_threshold (StakeThreshold); alpha_0 in the inference analysis",
              "value": "UNSET. No normative document states a number. The SDP defines only the structure `class MinStake: stake_threshold: StakeThreshold; epoch: EpochNumber` and Mantle only asserts `note.value >= min_stake.stake_threshold`. The genesis spec sets no value for it.",
              "citation": "bedrock-service-declaration-protocol.md:88-96; bedrock-v1.1-mantle-specification.md:1024-1026; bedrock-v1.1-mantle-specification.md:1119"
            },
            {
              "name": "Minimum stake, informational analysis value",
              "symbol": "Stake_LGO",
              "value": "Stake_LGO = 0.001% * S_TGE (an upper bound of 0.015% * S_TGE is also derived). Under that document's own assumption S_TGE = S_max = 100,000,000 LGO this evaluates to 1,000 LGO (= $1,000 at FDV $100M). This is an Informational analysis, not a Standards Track value.",
              "citation": "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:60; analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:116; analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:122; analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:148-172"
            },
            {
              "name": "Staking-ratio input to the min-stake derivation",
              "symbol": "r_stake",
              "value": "15%",
              "citation": "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:93"
            },
            {
              "name": "Target number of service providers used in the min-stake derivation (NOT a protocol cap)",
              "symbol": "N_stakers",
              "value": "1000",
              "citation": "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:97"
            },
            {
              "name": "Token supply at TGE (as used by Block Rewards)",
              "symbol": "S_tge",
              "value": "10 billion LGO",
              "citation": "block-rewards.md:160"
            },
            {
              "name": "Token supply at TGE (as assumed by the min-stake analysis)",
              "symbol": "S_TGE = S_max",
              "value": "100,000,000 LGO",
              "citation": "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:151-152"
            },
            {
              "name": "Service type set",
              "symbol": "ServiceType",
              "value": "BN only (`class ServiceType(Enum): BN="BN" # Blend Network`). "Any declaration that is not one of the above must be rejected."",
              "citation": "bedrock-service-declaration-protocol.md:79-84; bedrock-v1.1-mantle-specification.md:1016-1017"
            },
            {
              "name": "Inactivity period for the Blend Network service (max epochs without an Active message before the declaration is inactive)",
              "symbol": "inactivity_period",
              "value": "2 epochs (BlendNetworkServiceParameters: inactivity_period: 2, epoch: 0). The generic constraint is "at least 2 epochs long due to finalization reasons".",
              "citation": "bedrock-service-declaration-protocol.md:360-364; bedrock-service-declaration-protocol.md:110"
            },
            {
              "name": "SDP snapshot / declaration-effect lag",
              "symbol": "finalized_epoch",
              "value": "finalized_epoch = current_epoch - 2. "messages sent during epoch `n` are included in the next snapshot (for epoch `n+2`)". Epochs 0 and 1 read the genesis-block snapshot.",
              "citation": "bedrock-service-declaration-protocol.md:63; bedrock-service-declaration-protocol.md:127-130"
            },
            {
              "name": "Reward payout lag",
              "symbol": "(none)",
              "value": "epoch N activity -> Active messages in epoch N+1 -> computation at end of N+1 -> payout in the FIRST BLOCK of epoch N+2",
              "citation": "bedrock-service-reward-distribution.md:45-49; bedrock-service-reward-distribution.md:80; blend-protocol.md:1134-1136"
            },
            {
              "name": "Withdrawal / last rewardable epoch",
              "symbol": "withdraw_at = e",
              "value": "Withdrawal epoch e is the node's last rewardable epoch; the declaration is removed and stake unlocked at epoch e+2, after the epoch-e reward is paid (condition `withdraw_at <= current_epoch - 2`)",
              "citation": "bedrock-service-declaration-protocol.md:316; bedrock-v1.1-mantle-specification.md:1342-1354"
            },
            {
              "name": "Max locators per declaration",
              "symbol": "(none)",
              "value": "8 (list must be non-empty); each Locator at most 329 characters",
              "citation": "bedrock-service-declaration-protocol.md:164; bedrock-service-declaration-protocol.md:145; bedrock-v1.1-mantle-specification.md:1109-1113"
            },
            {
              "name": "Activity-threshold sensitivity parameter",
              "symbol": "theta",
              "value": "1",
              "citation": "blend-protocol.md:1080"
            },
            {
              "name": "Activity-threshold node-count term",
              "symbol": "nu",
              "value": "ceil(log2(N+1)), N = number of core nodes returned by SDP for the epoch â no fixed number",
              "citation": "blend-protocol.md:1078"
            },
            {
              "name": "Activity-threshold total-token term",
              "symbol": "chi",
              "value": "ceil(log2(Q_C^Total + 1)); Q_C^Total = C * (beta_C + R_C * beta_C)",
              "citation": "blend-protocol.md:1079; blend-protocol.md:601"
            },
            {
              "name": "Hamming-comparison bit width",
              "symbol": "epsilon",
              "value": "epsilon = ceil(log2(Q_C^Total + 1)/8) * 8",
              "citation": "blend-protocol.md:1044"
            },
            {
              "name": "Expected blending operations per cover message",
              "symbol": "beta_C",
              "value": "3",
              "citation": "blend-protocol.md:477"
            },
            {
              "name": "Cover-message redundancy parameter",
              "symbol": "R_C",
              "value": "UNSET (no numeric value stated anywhere)",
              "citation": "blend-protocol.md:466; blend-protocol.md:595"
            },
            {
              "name": "Cover-message generation frequency per round",
              "symbol": "F_C",
              "value": "UNSET (no numeric value stated); C = E * F_C",
              "citation": "blend-protocol.md:461; blend-protocol.md:592"
            },
            {
              "name": "Rounds per epoch",
              "symbol": "E",
              "value": "648000",
              "citation": "blend-protocol.md:475"
            },
            {
              "name": "Epoch length (consensus)",
              "symbol": "EPOCH_LENGTH",
              "value": "10*floor(k/f) slots = 648,000 slots = 648,000 s = 7.5 days (k = 2160, f = 1/30, slot length 1 s)",
              "citation": "cryptarchia-v1-protocol.md:144; cryptarchia-v1-protocol.md:94-96"
            },
            {
              "name": "Expected blocks per epoch",
              "symbol": "(none)",
              "value": "10k = 21,600 blocks",
              "citation": "cryptarchia-v1-protocol.md:146"
            },
            {
              "name": "Transition period (Active message must be sent after it)",
              "symbol": "T",
              "value": "30 rounds",
              "citation": "blend-protocol.md:570; blend-protocol.md:1135"
            },
            {
              "name": "Cap on the number of providers per service",
              "symbol": "(none)",
              "value": "NONE. "There is no cap to the amount of validators that can register to a specific service." The only structural bound is per-service uniqueness of provider_id and zk_id.",
              "citation": "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:111; bedrock-service-declaration-protocol.md:217-228"
            },
            {
              "name": "Cap on the total service reward",
              "symbol": "(none)",
              "value": "No explicit cap. It is implicitly bounded by 60% of the block reward, which is itself bounded by the emission model (I_max = 1%/yr of S_tge, plus the recycled-fee term).",
              "citation": "overview-cryptoeconomics.md:145; block-rewards.md:167; block-rewards.md:191-197"
            }
          ],
          "eligibility": "WHO CAN RECEIVE IT
- A node that has a stored `DeclarationInfo` in the SDP registry for `ServiceType.BN`, created by a valid `SDP_DECLARE` (bedrock-service-declaration-protocol.md:282-295). Validity requires: the sender meets the stake requirement and `locked_note_id` is valid; `declaration_id` is unique; `provider_id` and `zk_id` are each unique within the service; the sender knows the secret behind `provider_id`; 1 <= len(locators) <= 8; nonce increases monotonically.
- Mantle's stake check is exactly `assert ledger.is_unspent(declaration.locked_note_id); note = ledger.get_note(...); assert note.value >= min_stake.stake_threshold` (bedrock-v1.1-mantle-specification.md:1117-1119). One note may back declarations for several services but not two declarations of the same service (bedrock-v1.1-mantle-specification.md:1122-1128).
- Rewards are paid to the `zk_id` of the declaration, not to `provider_id` (bedrock-service-reward-distribution.md:55, :85). Several rewards sharing a `zk_id` are merged into a single note (bedrock-service-reward-distribution.md:86).

GATES, in order
1. Network-size gate (whole-service): "Rewards are not calculated if the number of nodes (unique `ProviderId`s from declarations) retrieved from the SDP protocol is lower than the Minimal Network Size" = 32 (blend-protocol.md:1110, :150). Below 32 nobody is paid.
2. Declaration must be visible in the epoch's SDP snapshot, which is taken at the last block of `current_epoch - 2` (bedrock-service-declaration-protocol.md:63, :127-130). A declaration submitted in epoch n is first usable in epoch n+2.
3. The provider must submit exactly one `SDP_ACTIVE` Mantle Transaction for epoch e, during epoch e+1, after the transition period; duplicates are rejected; late submission forfeits the reward entirely ("If a node does not send the Active Message on time, then it will not receive a reward.", blend-protocol.md:1104, :1096, :1135-1137).
4. The Active message's metadata must carry a valid Activity Proof (version byte 0x01 + ActivityProof), signed by the `zk_id`, nonce monotonically increasing (blend-protocol.md:1088, bedrock-service-declaration-protocol.md:243-245, bedrock-v1.1-mantle-specification.md:1423-1429).
5. The activity proof must be `true`: valid Proof of Quota and Proof of Selection for epoch e, AND Hamming distance between H(token) and H(R_{e+1}) strictly below the activity threshold A_epsilon = chi - nu - theta (blend-protocol.md:1026-1036, :1070-1080). This is a lottery: a provider that worked but was unlucky earns nothing.
6. Being counted in P (the doubling) additionally requires the submitted proof to be at the minimal Hamming distance among all submitted active messages (blend-protocol.md:1116-1118).
7. Inactivity: a declaration that has not sent an Active message within `inactivity_period` = 2 epochs is considered inactive (bedrock-service-declaration-protocol.md:41, :60, :110, :360-364). The Active action reactivates "inactive (but not expired) providers" (bedrock-service-declaration-protocol.md:301).
8. Withdrawal: `withdraw_at = e` makes epoch e the last rewardable epoch; removal and stake unlock happen at e+2 after the payout (bedrock-service-declaration-protocol.md:316, bedrock-v1.1-mantle-specification.md:1344-1354).

DEPENDENCE ON STAKE SIZE: none. The reward formula R = I/(B+P) and R(n) = R*[true + min] contains no stake term. Stake is a binary admission gate at `note.value >= min_stake.stake_threshold`; staking more than the threshold buys no additional service reward.

DEPENDENCE ON SERVICE TYPE: the framework is per-service by construction â "Each service defines: The validator activity rule ... The reward formula for distributing the epoch's rewards" and "The protocol does not prescribe a unique activity rule" (bedrock-service-reward-distribution.md:36-39, :62). But only one service type exists (`BN`), and only one reward split (60/40) and one per-node formula are specified, so in practice there is no service-type variation to model.

GENESIS: the Blend provider set is bootstrapped by >= 32 `SDP_DECLARE` Operations inside the Genesis Mantle Transaction, and genesis is treated as finalized so Blend uses the set immediately without the usual finalization delay (bedrock-genesis-block.md:90-109, :319-323).",
          "timing": "PER BLOCK
- Each block produces a block reward Rewards_t (block-rewards.md:456-473). 60% of it is the Blend/service share; 40% is the leader share. In the integer reference implementation the split is applied per block with floor division (block-rewards.md:497-498).

PER EPOCH (epoch = 648,000 slots = 7.5 days; ~21,600 blocks expected)
- Epoch N: providers do the work and collect blending tokens.
- End of epoch N / start of N+1: epoch randomness R_{N+1} becomes known; the service income I for epoch N is the sum of the 60% shares of all block rewards of epoch N ("At the start of each Blend epoch, a Blend reward variable is computed. Its amount equals 60% of the total block rewards of the previous epoch", overview-cryptoeconomics.md:154).
- Epoch N+1 (after the 30-round transition period): each provider submits exactly one `SDP_ACTIVE` transaction attesting to epoch N.
- End of epoch N+1: nodes compute B, P, R = I/(B+P) and R(n) for every provider (bedrock-service-reward-distribution.md:48, :70).
- First block of epoch N+2: notes are inserted directly into the ledger, no Mantle validation, `op_id = hash(ServiceType || epoch_number)`, outputs ordered by ascending `zk_id` (bedrock-service-reward-distribution.md:49, :80-87).
- Same first block of N+2, AFTER the payout: SDP Epoch Finalization removes every declaration with `withdraw_at <= current_epoch - 2` and unlocks its note (bedrock-v1.1-mantle-specification.md:1342-1384; bedrock-service-reward-distribution.md:91).

LAGS, summarized
- Work-to-payment lag: 2 epochs (15 days) from the end of the earning epoch to the payout block.
- Declaration-to-eligibility lag: up to 2 epochs (the snapshot is taken at the last block of current_epoch - 2; epochs 0 and 1 use the genesis snapshot).
- Withdrawal-to-unlock lag: 2 epochs after the withdrawal epoch.
- Inactivity tolerance: 2 epochs without an Active message.",
          "ambiguities": [
            "PAYOUT LAG: the SRDP and the overview disagree by one epoch. bedrock-service-reward-distribution.md:49 â 'Service Reward Distribution (First block of epoch N+2): Rewards are distributed to validators marked as active for the service' (i.e. epoch-N rewards paid at the start of N+2, a two-epoch lag), corroborated by blend-protocol.md:1136 'When the following epoch begins ($e+2$) Mantle distributes rewards'. But overview-cryptoeconomics.md:228 says 'When a new service epoch $e$ starts, rewards for the previous epoch $e-1$ are calculated and directly inserted in the ledger. The reward amount is calculated as the sum of service block rewards from the previous epoch $e-1$' â a one-epoch lag. I do not reconcile these; the SRDP is the Standards Track document for the payout and is the more detailed of the two.",
            "DO EXECUTION-MARKET TIPS REACH SERVICE PROVIDERS? Two documents disagree. execution-market.md:62 â 'The priority_fee is not immediately distributed to the block builder (to preserve privacy), but instead it is directed into the block builders reward stream. 40% of the rewards will be allocated to block builders and the remaining 60% to Blend nodes.' Against that, overview-cryptoeconomics.md:167-172 puts 100% of the tips in the leader pool: 'leader_rewards += 0.4 * get_block_rewards(b) # get 40% of the rewards' then 'leader_rewards += get_execution_market_tips(b) # get Execution market tips' â the tips are added whole, with no 60% diverted to Blend. overview-cryptoeconomics.md:140 likewise describes the leader pool as 'a fraction of the block rewards AND a portion of the Execution fees minted back'. Under the overview, service providers get 60% of the block reward only; under execution-market.md they would also get 60% of tips.",
            "PER-BLOCK vs PER-EPOCH ROUNDING OF THE 60% SHARE. block-rewards.md:497 floors the Blend share per block ('reward_numerator * 6 // (reward_denominator * 10)'), while overview-cryptoeconomics.md:158-161 sums '0.6 * get_block_rewards(b)' in real arithmetic over the epoch. Summing floored per-block shares is not the same as flooring the summed share, and neither document says which is normative. Note also that the two floors in block-rewards.md:497-498 do not sum to the block reward â the flooring residue of 6//10 and 4//10 is unaccounted for, and the spec does not say where it goes.",
            "DEFECTS IN THE block-rewards.md REFERENCE IMPLEMENTATION (block-rewards.md:477-501). Line 494 uses 'a_num' where 'a_numerator' was defined at 488, so the function as written raises NameError. Line 222 in the earlier 'block_rewards' helper uses an undefined 'R_block_cur' where the parameter is named 'D_1_t'. Line 287 in 'weighted_deviation_from_target' reads 'weighted_target_deviation += weight * deviation value', which is not valid Python. These are transcription defects, not alternative semantics, but a simulator must choose an interpretation.",
            "S_TGE IS INCONSISTENT ACROSS DOCUMENTS, which makes even the derived minimum stake ambiguous. block-rewards.md:160 sets S_tge = '10 billion LGO'; analysis-static-minimum-stake...:151-152 assumes 'S_max = 100,000,000 LGO' and 'S_TGE = S_max = 100,000,000 LGO' (and its own line 75 offers yet another illustrative '10 million LGO' / '1 million LGO' pair). Stake_LGO = 0.001% * S_TGE therefore evaluates to 1,000 LGO under the analysis's numbers and 100,000 LGO under Block Rewards' S_tge. I do not choose between them.",
            "DEFINITION OF P (the premium set). blend-protocol.md:1116 defines P as 'the number of nodes with the minimal distance among all submitted active messages' â i.e. the argmin set, normally of size 1. But the overview of the mechanics at blend-protocol.md:277 says a node is rewarded 'if the token is in the set of the most similar tokens (as defined below)', plural and suggesting a set of some size, and overview-cryptoeconomics.md:222 says 'with additional bonuses for those achieving the closest matches'. If P is strictly the argmin set then typically P = 1 and the premium is a single-winner lottery; if it is a top-k set the parameter k is nowhere stated. UNSET either way.",
            "WHETHER THE SDP `active` FIELD OR THE ACTIVITY PROOF IS THE OPERATIVE GATE. bedrock-service-reward-distribution.md:49 pays 'validators marked as active for the service' (the `DeclarationInfo.active` field, set by the service-specific logic per bedrock-service-declaration-protocol.md:312 and bedrock-v1.1-mantle-specification.md:1434), while blend-protocol.md:1112-1126 computes the reward purely from true activity proofs on the ledger. Whether a declaration whose `active` epoch has gone stale (beyond inactivity_period = 2) is excluded from B, and whether an inactive-but-not-withdrawn declaration is still returned by the SDP snapshot that feeds N and the Minimal Network Size check, is not stated.",
            "SERVICE TYPE NAMING. bedrock-service-declaration-protocol.md:80-82 and bedrock-v1.1-mantle-specification.md:1016-1017 define `class ServiceType(Enum): BN="BN"`, but bedrock-genesis-block.md:102 and :258 construct declarations with `ServiceType.BLEND`. Same service, two identifiers; this matters because the payout `op_id` is `hash(ServiceType || epoch_number)`.",
            "C = E*F_C or C = S*F_C? blend-protocol.md:463 defines 'C = S \cdot F_C' while blend-protocol.md:592 defines 'C = E \cdot F_C'. E = 648000 rounds per epoch is defined at :475; S is not defined in the current text (apparently a residue of the removed 'session' concept)."
          ],
          "not_specified": [
            "The numeric value of `min_stake.stake_threshold`. No Standards Track document states it; the SDP defines only the `MinStake` structure and Mantle only compares against it. The genesis block specification, which does set other protocol constants, does not set this one. Only the Informational analysis gives a formula (0.001% * S_TGE).",
            "How and when `MinStake` / `stake_thresholds` are updated after genesis. The structure carries an `epoch` at which the threshold was set and the SDP exposes `GetMinStake(epoch)` / `GetMinStakeSince(epoch)`, implying it can change, but no mechanism, governance path, or Operation for changing it is specified anywhere.",
            "Whether the minimum-stake check is re-evaluated after declaration. The spec checks `note.value >= min_stake.stake_threshold` only at SDP_DECLARE (bedrock-v1.1-mantle-specification.md:1119). Nothing says what happens to an existing declaration if the threshold is later raised.",
            "Numeric values for F_C and R_C, hence Q_C^Total, hence chi and epsilon, hence the activity threshold A_epsilon. Without these the probability that an honest provider's activity proof is `true` cannot be computed from the specification.",
            "The success probability of the activity lottery per honest provider, and therefore the expected fraction B/N. The spec gives the accept/reject rule but no target acceptance rate.",
            "What happens to the residue when B + P does not divide I, and whether R is floored. The SRDP requires byte-identical execution across nodes (bedrock-service-reward-distribution.md:87) but gives no integer/rounding rule for the service reward, in contrast to the explicit integer treatment given to the leader pool (overview-cryptoeconomics.md:214) and the PoW pool.",
            "Whether the Blend service income I is carried over when it cannot be distributed. If the Minimal Network Size gate fails, or if B = 0 (nobody submitted a valid proof), the spec does not say whether the 60% share is burnt, retained, rolled into the next epoch, or never minted at all. There is no 'Blend reward pool' state variable in the Mantle specification analogous to `leaders_rewards` or `pow_reward_pool`.",
            "Any cap on the number of declared providers, and any per-provider cap on the reward. Explicitly the opposite is stated for the provider count (analysis-static-minimum-stake...:111).",
            "Any stake-weighting, any seniority weighting, and any slashing of the locked stake. The stake is a lock, never described as at risk.",
            "Whether more than one declaration per operator is prevented. Uniqueness is enforced per (`service`, `provider_id`) and (`service`, `zk_id`) only, so an operator holding several notes above the threshold may hold several declarations; nothing in the spec links declarations to a single economic entity.",
            "The gas/fee cost a provider must pay to submit its Active message each epoch, relative to the reward. EXECUTION_SDP_ACTIVE_GAS = 590 is specified (bedrock-v1.1-mantle-specification.md:2253), but the spec never checks that the service reward exceeds the cost of claiming it â unlike the PoW pool, where that comparison is made explicitly.",
            "How `Rewards_Epoch` is apportioned between services when more than one service exists. The SRDP says it 'calculates how much each service receives' by reference to a linked document, but the only split specified anywhere is the two-way 60/40 Blend/leader split."
          ],
          "derived_not_stated": [
            "DERIVED: the total paid out to providers for an epoch equals I exactly. Summing R(n) over all providers gives R*(B + P) = I. So the service stream distributes the full 60% share whenever B >= 1, and each of the B non-premium providers receives I/(B+P) while each of the P premium providers receives 2I/(B+P). The specification does not state this identity; it follows from blend-protocol.md:1120-1126.",
            "DERIVED: if P = 1 (the natural reading of 'the minimal distance'), the per-provider base reward is I/(B+1) and the single winner receives 2I/(B+1).",
            "DERIVED: minimum stake in absolute LGO. 0.001% * 10,000,000,000 = 100,000 LGO using Block Rewards' S_tge; 0.001% * 100,000,000 = 1,000 LGO using the analysis's own S_TGE (the latter figure IS stated, at analysis-static-minimum-stake...:171, but only under that document's assumptions). Neither is a normative protocol constant.",
            "DERIVED: per-epoch service income at maximum emission and zero fees. With A_t = 1, each block mints I_max*S_tge*Delta_t/f = 62500/657 ~= 95.13 LGO, of which 60% ~= 57.08 goes to the service; over 21,600 expected blocks that is ~1.23 million LGO per epoch to the service stream, ~8.0 million LGO/yr (48.667 epochs/yr), i.e. 0.6% of S_tge per year â consistent with 60% of the 1% I_max cap. Assembled from block-rewards.md:463, :167, cryptarchia-v1-protocol.md:146; the specification nowhere states this number.",
            "DERIVED: per-provider annual yield at the 32-provider floor and at the 1000-provider design point, assuming P = 1 and full emission: ~1.23M/33 ~= 37,000 LGO per provider per epoch at N = 32 (all active), versus ~1,230 LGO per provider per epoch at N = 1000. Not stated; follows from the two figures above.",
            "DERIVED: the epoch is 648,000 slots = 7.5 days and there are 48.667 epochs per year. cryptarchia-v1-protocol.md:144 gives 10*floor(k/f) and :94-96 give k = 2160, f = 1/30, slot = 1 s; block-rewards.md:136 independently uses '1 epoch, which lasts 7.5 days' and blend-protocol.md:475 independently states E = 648000 rounds. The arithmetic tying them together is mine.",
            "DERIVED: a provider's total exposure window from declaring to first possible reward is up to 4 epochs (~30 days): up to 2 epochs before the declaration enters an SDP snapshot, 1 epoch of work, then payout 2 epochs after that work epoch ends. Composed from bedrock-service-declaration-protocol.md:128 and bedrock-service-reward-distribution.md:45-49; not stated as a single figure anywhere.",
            "DERIVED (framing, not fact): the service reward is FLAT PER ACTIVE PROVIDER, not proportional to stake â the formula has no stake term, only a binary threshold gate. The specification never says this in so many words; it is an inference from the absence of any stake variable in blend-protocol.md:1120-1126 and from bedrock-v1.1-mantle-specification.md:1119 being a `>=` admission test.",
            "DERIVED: because the reward is flat per zk_id and there is no cap on providers, splitting stake across many declarations that each meet the threshold multiplies the reward. The specs enforce uniqueness of provider_id/zk_id per service but say nothing about one operator holding many declarations; the Sybil resistance rests entirely on the stake threshold's absolute size. This is my reading, not a statement in the specification."
          ]
        },
        "check": {
          "stream": "Service provision reward (Service Declaration Protocol + Service Reward Distribution Protocol; Blend Network, ServiceType.BN)",
          "citations_verified": true,
          "invented_elements": [
            "CONFLATION (not a fabricated formula, but a wrong identity a simulator would encode): the parameter table gives the Blend income as `I  (= Rewards_Epoch for the BN service)`, and STEP 1 is headed `the service's share of the block reward (the input I / Rewards_Epoch)`. The source does not equate them. bedrock-service-reward-distribution.md:76 reads: "Where $`Rewards\_Epoch`$ are the total rewards of epoch **N**. The $`Rewards\_Epoch`$ is determined by the linked reference, which calculates how much each service receives". Rewards_Epoch is the TOTAL epoch reward passed into serviceReward(); I in blend-protocol.md:1122 is "the value of income for the Blend Network service", i.e. 0.6 x Rewards_Epoch. Correct relation: I = 0.6 * Rewards_Epoch, not I = Rewards_Epoch.",
            "Symbol `EPOCH_LENGTH` (parameter table, "Epoch length (consensus)") does not exist in cryptarchia-v1-protocol.md. Line 144 uses prose only: "The **epoch length** is the sum of the individual phases: $`3\lfloor k/f \rfloor + 3\lfloor k/f \rfloor + 4\lfloor k/f \rfloor =10 \lfloor k/f \rfloor`$ slots." There is no named constant. The value 648,000 is itself correct (10*floor(2160/(1/30))), but it is derived, not a stated constant â the derived_not_stated list does admit this.",
            "ARITHMETIC ERROR in derived_not_stated item 4: "~1.23 million LGO per epoch to the service stream, ~8.0 million LGO/yr (48.667 epochs/yr), i.e. 0.6% of S_tge per year". 1.23e6 x 48.667 = ~60.0 million LGO/yr, and 0.6% of S_tge (10e9) = 60,000,000 â so the stated 8.0 million contradicts both its own inputs and its own conclusion in the same sentence. It is low by a factor of 7.5 (the epoch length in days). A simulator calibrated on 8.0M/yr would understate the whole service stream by 7.5x. The per-epoch figure (1.23M) and the per-provider figures (~37,000 at N=32, ~1,230 at N=1000) are correct."
          ],
          "wrong_citations": [
            "`blend-protocol.md:592` (cited twice: ambiguity "C = E*F_C or C = S*F_C?" and the F_C parameter row) â line 592 is blank. Line 591 is "Where:"; the definition is at line 593: "- $`C = E \cdot F_C`$ denotes an expected number of cover messages that are generated during an epoch by the core nodes;". The claimed content and the ambiguity itself are real (blend-protocol.md:463 does read "- $`C = S \cdot F_C`$ denote the expected number of cover messages..."), only the line number is off by one.",
            "analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md:75 â the ambiguity says "its own line 75 offers yet another illustrative '10 million LGO' / '1 million LGO' pair". Line 75 carries only the first: "- $`S_{\text{max}}`$ denote the maximum supply of LGO (e.g., 10 million LGO)." The "1 million LGO" is at line 77: "- $`S_{\text{TGE}}`$ denote the supply at token generation event (e.g., 1 million LGO)." Substance is right, one of the two lines is misattributed.",
            "bedrock-service-reward-distribution.md:87 is cited in not_specified as requiring "byte-identical execution across nodes". Line 87 actually says: "Be executed identically by every node processing the first block of epoch N+2. This happens by inserting notes in the ledger in ascending order of `zk_id`." "Identically", not "byte-identical" â a strengthening, though the inference (determinism demands a rounding rule) stands.",
            "blend-protocol.md:1078 is cited for "N = number of core nodes returned by SDP for the epoch". Line 1078 says only "...the number of nodes in the network $`N`$, it makes the lottery difficulty a function of the network size". The "returned by SDP" gloss is correct but comes from blend-protocol.md:468-469 ("$`\mathcal{N} = \text{SDP}(s)`$ denote a set of core nodes providing the Blend service for the epoch $`e`$ returned by the SDP protocol"; "$`N = |\mathcal N|`$"), which is never cited.",
            "Minor: the STEP 4 quotation of bedrock-service-reward-distribution.md:84 silently drops a source typo. Line 84 reads "...according to [Service Reward Calculation](#service-reward-calculation).2" â with a stray trailing "2". Immaterial, but the block is presented as a quotation.",
            "Minor: the ambiguity "PAYOUT LAG: the SRDP and the overview disagree by one epoch" mislocates the disagreement. overview-cryptoeconomics.md contradicts ITSELF, not the SRDP: line 65 says "During the first block of epoch $e+2$, Blend validators from epoch $e$ receive their portion" and line 139 says "allocated to nodes based on their reported Active Messages ... during epoch $e+2$" â both agreeing with the SRDP. Only line 228 dissents. The extraction's conclusion (follow the SRDP) is right, and is in fact better supported than it states: it is 3 statements to 1, all inside the same Informational document."
          ],
          "missed_elements": [
            "POW_SHARE = 10, SHARE_DEN = 100 â bedrock-v1.1-mantle-specification.md:1806-1807: `POW_SHARE: uint64 = 10   # beta, as the fraction POW_SHARE / SHARE_DEN` / `SHARE_DEN: uint64 = 100`. This is a normative numeric constant that feeds directly into the service stream and is absent from the parameter list entirely (the PoW pool appears only as an aside in not_specified). A tenth of every block's collected fees is diverted BEFORE the burn, so the burned-fee series that drives the block reward is (1 - 1/10) of collected fees. overview-cryptoeconomics.md:195: "The emission model measures the fees that are actually burnt and mints against them, so diverting a share before the burn reduces that measurement by the same share." And :197: "the block reward is the amount burnt, so reducing that amount reduces the block reward in the same proportion ... **The cost falls on the Blend service and the leaders**, in the 60/40 proportion in which they divide the block reward." mantle:1816 confirms: "in the mature network the diversion is borne by the Blend service and the leaders". A simulator that feeds gross collected fees into `burned_fees_window` overstates I in the recycling regime by ~11%.",
            "The block-reward model's own parameters are absent from the parameter table, appearing only implicitly inside the reproduced code block. block-rewards.md:158-170 specifies: T = 120 (look-back window, :161), alpha_a = 1 (:162), alpha_d = 1/4 (:163), w_i = 1 (:164), D_0,target = 3 billion LGO = 30% of supply (:165), D_1,target = 10 billion (:166), I_min = 0% (:168), f = 1 (:169), Delta_t = 1/(365*2880) (:170). Without these, I cannot be computed at all â the extraction lists only S_tge and I_max. The integer constants A_SCALE / INFLATION_NUMERATOR / INFLATION_DENOMINATOR / FEE_AVG_NUMERATOR / STAKE_TARGET appear in the quoted code but are never named or explained as parameters.",
            "The below-32 fallback. blend-protocol.md:158: "If the minimal network size is not reached, nodes must not use the Blend protocol. In such cases, nodes must broadcast data messages directly, bypassing the Blend network." The extraction states the reward gate but not that the service is switched off entirely â relevant to the (correctly identified) open question of what happens to the 60% share when the gate fails.",
            "A fourth transcription defect in block-rewards.md, not listed among the three the extraction flags. Line 323, inside `weighted_average`, reads `assert len(kpi_weights) == len(kpi_deviations)` â `kpi_deviations` is undefined in that function (its parameters are `kpi_weights` and `kpi_average`). Same class of copy-paste defect as the `a_num` and `R_block_cur` ones already noted.",
            "Who executes the payout. bedrock-v1.1-block-construction.md:61 ("They execute the [**Service Reward Distribution Protocol**] to generate reward notes locally.") and :242 ("Execute the reward distribution protocol ... to generate reward notes locally and include them in the ledger.") are the only statements binding the SRDP into block construction and validation. Low impact for an economic simulator, but the file is never cited.",
            "The activity-proof inputs now include a proof-of-work branch. blend-protocol.md:686: "$`q=Q_C + Q_L^n + Q_W^n`$ is the sum of core quota, leadership quota and proof of work quota for the node $`n`$" and :751 makes PoQ a logical OR of the three. The extraction's chi = ceil(log2(Q_C^Total+1)) faithfully reproduces blend-protocol.md:1079, but the threshold is normalized against cover-message quota only while the tokens in circulation may also come from Q_L and Q_W â an unmodelled inconsistency in the lottery calibration that is visible in the source and not raised."
          ],
          "corrections": [
            "Replace "~8.0 million LGO/yr" with "~60.0 million LGO/yr" in derived_not_stated item 4. 1,232,928 LGO/epoch x 48.667 epochs = 59,999,... ~= 60M = 0.6% of S_tge = 10e9, which is what the same sentence concludes.",
            "Change the I parameter to "I = 0.6 * Rewards_Epoch", not "I (= Rewards_Epoch for the BN service)". bedrock-service-reward-distribution.md:76 defines Rewards_Epoch as the TOTAL epoch rewards handed to serviceReward(); the 60% Blend share is what blend-protocol.md:1122 calls I.",
            "Add POW_SHARE/SHARE_DEN = 10/100 (bedrock-v1.1-mantle-specification.md:1806-1807) as a parameter, and note that the burned-fee series driving the block reward is net of it (overview-cryptoeconomics.md:195, :197; mantle:1814, :1816).",
            "Fix blend-protocol.md:592 -> :593 for `C = E * F_C` (both occurrences).",
            "Fix analysis-static-minimum-stake...:75 -> :75 and :77 for the "10 million / 1 million LGO" illustrative pair.",
            "Restate the payout-lag ambiguity as internal to overview-cryptoeconomics.md: :65 and :139 agree with the SRDP's e+2; only :228 says e-1/one-epoch. The extraction's resolution (follow the SRDP) is correct and better supported than it claims.",
            "Add the block-reward parameters (T=120, alpha_d=1/4, alpha_a=1, D_0,target=3e9, D_1,target=1e10, I_min=0, f=1, Delta_t=1/(365*2880)) from block-rewards.md:158-170 to the parameter list; the simulator needs them to produce I at all.",
            "Cite blend-protocol.md:468-469 for "N = number of core nodes returned by SDP" rather than resting it on :1078."
          ],
          "verdict": "needs-correction"
        }
      },
      {
        "stream": "pow",
        "formula": {
          "stream": "Proof of Work claim reward (CLAIM_POW_REWARD): per-claim reward, pool refill, distribution rate, target claim rate, reward-difficulty retarget, and the claim transaction's own fee.",
          "formula": "CONFIRMED with two corrections (rho is 1/200, not unspecified; there is ONE floor, over a single combined denominator, not two divisions).

=== A. Per-claim reward, computed at the epoch boundary and fixed for the epoch ===
bedrock-v1.1-mantle-specification.md:1776-1787
```python
EPOCH_POW_DISTRIBUTION_RATE_NUM: uint64 = 1     # rho, as a fraction NUM / DEN
EPOCH_POW_DISTRIBUTION_RATE_DEN: uint64 = 200
TARGET_CLAIMS_PER_BLOCK: uint64 = 10      # T
EXPECTED_BLOCKS_PER_EPOCH: uint64 = 21_600      # N_b, derived below

def compute_epoch_pow_reward(pow_reward_pool: TokenValue) -> TokenValue:
    denominator = (EPOCH_POW_DISTRIBUTION_RATE_DEN
                   * TARGET_CLAIMS_PER_BLOCK
                   * EXPECTED_BLOCKS_PER_EPOCH)
    return (pow_reward_pool * EPOCH_POW_DISTRIBUTION_RATE_NUM) // denominator
```
Exact integer arithmetic: denominator = 200 * 10 * 21600 = 43,200,000, a compile-time constant. sigma_e = floor(pool * 1 / 43_200_000). Exactly ONE flooring site, applied after the single multiply-by-NUM. "The division rounds down, and what the flooring withholds is not lost: it simply remains in the pool, to be counted again at the next boundary." (:1791)

=== B. Epoch boundary: refill first, then recompute ===
bedrock-v1.1-mantle-specification.md:1805-1812
```python
POW_SHARE: uint64 = 10                    # beta, as the fraction POW_SHARE / SHARE_DEN
SHARE_DEN: uint64 = 100

def on_epoch_boundary(epoch_blocks: list[Block]):
    pow_reward_pool = checked_uint64(pow_reward_pool + get_pow_pool_refill(epoch_blocks))
    epoch_pow_reward = compute_epoch_pow_reward(pow_reward_pool)
```
":1803 At each epoch boundary, before any block of the new epoch is processed, the pool is credited with the refill accrued over the previous epoch and the per-claim reward is then recomputed from the refilled pool"

=== C. Refill rule (the only definition of get_pow_pool_refill) ===
overview-cryptoeconomics.md:180-184
```python
def get_pow_pool_refill(e: epoch): # refill for the epoch e
    refill = 0
    for b in e.blocks: # for each block of the previous epoch
        refill += get_collected_fees(b) * POW_SHARE // SHARE_DEN
    return refill
```
":187 where `get_collected_fees(b)` is the total Execution base fees and Permanent Storage fees paid by the transactions of block `b`... The share is computed with integer division, which rounds down... the sub-lepton residue of each flooring stays with the remainder and is burnt."
Exact integer arithmetic: flooring is PER BLOCK â floor(fees_b * 10 / 100) summed over blocks, NOT floor(sum(fees) * 10 / 100). Python `*` then `//` binds left-to-right, so it is floor((fees_b * 10) / 100), which is exact-then-floor, not floor(fees_b/10)*10.
Refill is diverted from the fee burn, never minted (:1814, overview:195-197).

=== D. Per-claim validation gate and execution ===
bedrock-v1.1-mantle-specification.md:1663-1681 (Validate)
```python
# 1. Claiming must be enabled for this block: the pool must be able to cover a reward.
assert epoch_pow_reward > 0
assert pow_reward_pool >= epoch_pow_reward

# 2. The referenced block must be canonical and within the acceptance window.
assert accept_claim_pow_op(claim, current_slot)

# 3. The solution must have been found against the current epoch.
assert claim.epoch_nonce == get_current_epoch_nonce()   # the Cryptarchia epoch nonce

# 4. The ticket must satisfy the reward threshold.
puzzle_ticket = get_puzzle_ticket(claim)
assert puzzle_ticket < difficulty_reward

# 5. The solution must not have been claimed before. The nullifier is the ticket,
#    so the value computed in step 4 is reused.
assert puzzle_ticket not in pow_nullifiers
```
bedrock-v1.1-mantle-specification.md:1714-1727 (Execute)
```python
output_note = Note(
    value = epoch_pow_reward,
    public_key = claim.public_key,
)
claim_id = derive_op_id(claim)
ledger.execute_adding(claim_id, [output_note])
```
```python
pow_reward_pool = checked_uint64(pow_reward_pool - epoch_pow_reward)
```
The pool guard is evaluated per claim against the pool as the preceding Operations left it, within a transaction as well as between transactions (:217, :1826). Claims mint nothing: "a claim transfers tokens that already exist into circulation, and cannot be executed if the pool cannot cover it" (:1578).

=== E. Puzzle ticket and the acceptance window ===
bedrock-v1.1-mantle-specification.md:1626-1631
```python
def get_puzzle_ticket(claim: ClaimPowRewardOp) -> zkhash:
    return zkhash(
        claim.epoch_nonce,
        FiniteField(claim.block_hash, byte_order="little", modulus=p),
        claim.public_key,
    )
```
Accepted when the ticket's canonical integer representative is strictly below the target's; a SMALLER target is HARDER (:1576). No domain separation tag (:1636).
bedrock-v1.1-mantle-specification.md:1584-1591
```python
EXPECTED_BLOCKS_PER_WINDOW: uint64 = 10   # W_b: window depth, in expected blocks

def accept_claim_pow_op(claim: ClaimPowRewardOp, current_slot: SlotNumber) -> bool:
    block = get_block_from_hash(claim.block_hash)   # None if unknown or not canonical
    if block is None:
        return False
    return 0 <= current_slot - block.slot <= WINDOW
```
:1597  WINDOW = floor(W_b / f);  ":1600 With W_b = 10 and f = 1/30 this is 300 slots."
Nullifier = the puzzle ticket itself (:1686-1687), retained only while the referenced block is inside the window (:1606).

=== F. Reward difficulty retarget â EVERY BLOCK ===
bedrock-v1.1-mantle-specification.md:1866-1884
```python
EMA_SMOOTHING_FACTOR: uint64 = 9      # F, the weight given to the previous estimate
EMA_SMOOTHING_PRECISION: uint64 = 10  # P, the scale F is expressed against; F < P

def compute_new_reward_difficulty(claims_in_block: uint64,
                                  current_target: PowTarget) -> PowTarget:
    # `current_target` and the result are canonical integer representatives of
    # their field elements; the arithmetic is over arbitrary-precision integers per
    # [Arithmetic], and the capped result converts back without reduction.
    # The demand implied by this block, reconstructed from the target that
    # produced it, then smoothed against the target rate. Floored at 1 so the
    # division below is always defined, including when no claims arrived.
    demand = max(1, (EMA_SMOOTHING_PRECISION - EMA_SMOOTHING_FACTOR) * claims_in_block
                    + EMA_SMOOTHING_FACTOR * TARGET_CLAIMS_PER_BLOCK)
    new_target = (TARGET_CLAIMS_PER_BLOCK * current_target
                  * EMA_SMOOTHING_PRECISION) // demand
    # Capped so that converting back into the field cannot reduce modulo p and
    # turn a very easy target into a very hard one.
    return min(new_target, p - 1)
```
Exact integer arithmetic: at the specified constants demand = max(1, 1*claims_in_block + 90); new_target = floor(10 * current_target * 10 / demand) = floor(100 * current_target / (claims_in_block + 90)), one flooring site, over ARBITRARY-PRECISION integers (checked_uint64 explicitly does NOT apply; intermediate reaches ~2**261) (:135, :1874-1876). Fixed point at claims_in_block = 10 (demand = 100, new = current). At zero claims the target multiplies by 100/90 = P/F.
Ordering (consensus-critical): ":1887 Every claim in a block is validated against the target produced by the previous block's update; the update from a block's own accepted count is applied after the block is processed and governs the next block. Genesis supplies the value the first block is validated against."
The observed rate is claims INCLUDED in blocks, not solutions found (:1893).
Genesis: ":1901 `difficulty_reward` is set at genesis to the scalar field modulus divided by 2^26." i.e. p // 2**26 (the "//" form is prose, not pseudocode).

=== G. The claim transaction's own fee ===
There is NO special fee rule for a claim. ":1690 This Operation performs no fee or balance check of its own. The transaction's fee is settled at the transaction level as normal." ":1644 Claim Operations have a fixed Execution Gas cost of `EXECUTION_CLAIM_POW_REWARD_GAS`... paid as part of the transaction's normal fee, which is typically settled from the reward note itself."
bedrock-v1.1-mantle-specification.md:144-157
```python
def mandatory_fees(signed_tx: SignedMantleTx,
                   permanent_storage_gas_price: TokenValue, # Given by Storage Market
                   execution_gas_base_price: TokenValue) -> uint64:  # Given by Execution Market
    mantle_tx = signed_tx.tx
    permanent_storage_fees = checked_uint64(len(encode(signed_mantle_tx)) * permanent_storage_gas_price)
    tx_execution_gas = 0

    for op in mantle_tx.ops:
        # Compute how much execution gas of this operation as defined
        # in the gas determination Appendix
        tx_execution_gas += execution_gas(op)
    execution_base_fees = checked_uint64(tx_execution_gas * execution_gas_base_price)

    return checked_uint64(execution_base_fees + permanent_storage_fees)
```
The canonical self-funding claim transaction carries CLAIM_POW_REWARD + TRANSFER (:1756-1759), so its execution gas is 56 + 590 = 646 ("the transaction already carries a `TRANSFER` at 590", analysis-gas-cost-determination.md:248). Its encoded byte size is NOT specified anywhere.",
          "citations": [
            "bedrock-v1.1-mantle-specification.md:1564 â Proof of Work Operations section start",
            "bedrock-v1.1-mantle-specification.md:1568-1574 â consensus state: pow_reward_pool, epoch_pow_reward, difficulty_reward, pow_nullifiers, block_slots",
            "bedrock-v1.1-mantle-specification.md:1576 â PowTarget arithmetic; smaller target is harder; big-integer, not field, arithmetic",
            "bedrock-v1.1-mantle-specification.md:1578 â pool is a reserve, seeded at genesis, refilled at epoch boundary, never minted on demand",
            "bedrock-v1.1-mantle-specification.md:1584-1591 â EXPECTED_BLOCKS_PER_WINDOW and accept_claim_pow_op",
            "bedrock-v1.1-mantle-specification.md:1597 â WINDOW = floor(W_b / f)",
            "bedrock-v1.1-mantle-specification.md:1600 â WINDOW = 300 slots at W_b = 10, f = 1/30",
            "bedrock-v1.1-mantle-specification.md:1617-1621 â ClaimPowRewardOp payload",
            "bedrock-v1.1-mantle-specification.md:1626-1631 â get_puzzle_ticket",
            "bedrock-v1.1-mantle-specification.md:1636 â no domain separation tag",
            "bedrock-v1.1-mantle-specification.md:1640 â no signature, no ZK proof; op_proof is None",
            "bedrock-v1.1-mantle-specification.md:1644 â EXECUTION_CLAIM_POW_REWARD_GAS, paid as normal tx fee",
            "bedrock-v1.1-mantle-specification.md:1663-1681 â validation, incl. epoch_pow_reward > 0 and pool >= reward",
            "bedrock-v1.1-mantle-specification.md:1686-1687 â pow_nullifier(claim) = get_puzzle_ticket(claim)",
            "bedrock-v1.1-mantle-specification.md:1690 â no fee check of its own",
            "bedrock-v1.1-mantle-specification.md:1692 â the two failure modes of the pool guard",
            "bedrock-v1.1-mantle-specification.md:1694 â epoch nonce is the Cryptarchia eta",
            "bedrock-v1.1-mantle-specification.md:1713-1727 â execution: nullifier insert, output note, pool decrement",
            "bedrock-v1.1-mantle-specification.md:1735-1766 â self-funding claim example (CLAIM + TRANSFER)",
            "bedrock-v1.1-mantle-specification.md:1768-1770 â reward fixed for the epoch is what makes self-funding possible",
            "bedrock-v1.1-mantle-specification.md:1772-1787 â Reward Pool: rho, T, N_b, compute_epoch_pow_reward",
            "bedrock-v1.1-mantle-specification.md:1789 â EXPECTED_BLOCKS_PER_EPOCH taken from Cryptarchia; mainnet values",
            "bedrock-v1.1-mantle-specification.md:1791 â flooring remains in the pool",
            "bedrock-v1.1-mantle-specification.md:1795 â net delivery proportional to beta*n - T",
            "bedrock-v1.1-mantle-specification.md:1799 â target set to 10; rationale",
            "bedrock-v1.1-mantle-specification.md:1803-1812 â POW_SHARE, SHARE_DEN, on_epoch_boundary",
            "bedrock-v1.1-mantle-specification.md:1814 â get_pow_pool_refill semantics, diverted not minted",
            "bedrock-v1.1-mantle-specification.md:1816 â share set to a tenth; zero disables refilling",
            "bedrock-v1.1-mantle-specification.md:1818 â all arithmetic checked; pool must not saturate",
            "bedrock-v1.1-mantle-specification.md:1822-1830 â Exhaustion within an epoch; rho is not a spending cap",
            "bedrock-v1.1-mantle-specification.md:1832 â epoch at target rate distributes exactly rho of the pool",
            "bedrock-v1.1-mantle-specification.md:1834-1836 â rho = 1/200 selection",
            "bedrock-v1.1-mantle-specification.md:1838 â POW_REWARD_POOL_GENESIS = 5/1000 of launch supply",
            "bedrock-v1.1-mantle-specification.md:1842-1848 â settled reward level; rho cancels",
            "bedrock-v1.1-mantle-specification.md:1850-1858 â Genesis section, seed rationale, 6,664 lepta figure",
            "bedrock-v1.1-mantle-specification.md:1862-1884 â Reward Difficulty, EMA constants, compute_new_reward_difficulty",
            "bedrock-v1.1-mantle-specification.md:1887 â retarget ordering is consensus",
            "bedrock-v1.1-mantle-specification.md:1891 â fixed point at target; P/F rise at zero claims",
            "bedrock-v1.1-mantle-specification.md:1893 â controller observes included claims only",
            "bedrock-v1.1-mantle-specification.md:1895 â builder self-claims are self-correcting",
            "bedrock-v1.1-mantle-specification.md:1899 â F/P = 9/10 rationale, ~10 block time constant",
            "bedrock-v1.1-mantle-specification.md:1901 â genesis difficulty_reward = p / 2**26",
            "bedrock-v1.1-mantle-specification.md:135 â PowTarget controllers use arbitrary-precision integers",
            "bedrock-v1.1-mantle-specification.md:121-133 â checked_uint64 definition",
            "bedrock-v1.1-mantle-specification.md:139-158 â mandatory_fees",
            "bedrock-v1.1-mantle-specification.md:217 â interleaving makes the per-claim pool guard sound within a transaction",
            "bedrock-v1.1-mantle-specification.md:260 â CLAIM_POW_REWARD opcode 0x40",
            "bedrock-v1.1-mantle-specification.md:2243-2255 â gas table: EXECUTION_CLAIM_POW_REWARD_GAS = 56, EXECUTION_TRANSFER_GAS = 590",
            "bedrock-v1.1-mantle-specification.md:2119 â TokenValue counts lepta; 1 LGO = 10^9 lepta",
            "bedrock-v1.1-mantle-specification.md:2121 â supply 10^10 LGO = 10^19 lepta",
            "overview-cryptoeconomics.md:175-187 â Proof of Work Reward Pool, get_pow_pool_refill",
            "overview-cryptoeconomics.md:191-201 â who bears the cost of the diversion",
            "overview-cryptoeconomics.md:61 â all fees burnt except the diverted share",
            "overview-cryptoeconomics.md:93 â both markets round price upwards; one unit is the floor",
            "bedrock-genesis-block.md:71-88 â Initial Proof of Work Reward Pool, POW_REWARD_POOL_GENESIS = 5/1000 of launch supply",
            "bedrock-genesis-block.md:298-301 â genesis initialization of pow_reward_pool, epoch_pow_reward, difficulty_reward, pow_nullifiers",
            "cryptarchia-v1-protocol.md:94-98 â f = 1/30, k = 2160, slot = 1s, MAX_BLOCK_TXS = 1024",
            "cryptarchia-v1-protocol.md:144-146 â epoch length 10*floor(k/f) slots; expected blocks per epoch = 10k = 21,600",
            "cryptarchia-proof-of-leadership.md:219 â p = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001",
            "analysis-gas-cost-determination.md:79 â CLAIM_POW_REWARD_GAS = 56",
            "analysis-gas-cost-determination.md:246-248 â 56 is a conservative over-estimate; claim tx already carries a TRANSFER at 590",
            "execution-market.md:206 â base fee rounds up; 1 is the effective floor",
            "storage-markets.md:224 â storage price rounds up; 1 lepton per gas is the effective floor"
          ],
          "parameters": [
            {
              "name": "Proof of work reward pool balance (consensus state)",
              "symbol": "pow_reward_pool",
              "value": "Initialized to POW_REWARD_POOL_GENESIS at genesis; thereafter changed only by the epoch refill and by claims",
              "citation": "bedrock-v1.1-mantle-specification.md:1569, :1852; bedrock-genesis-block.md:298"
            },
            {
              "name": "Reward per claim, fixed for the epoch (consensus state)",
              "symbol": "epoch_pow_reward / sigma_e",
              "value": "compute_epoch_pow_reward(pow_reward_pool), recomputed only at each epoch boundary; set at genesis from the genesis pool",
              "citation": "bedrock-v1.1-mantle-specification.md:1570, :1782-1786, :1811; bedrock-genesis-block.md:299"
            },
            {
              "name": "Distribution rate numerator",
              "symbol": "EPOCH_POW_DISTRIBUTION_RATE_NUM (rho numerator)",
              "value": "1",
              "citation": "bedrock-v1.1-mantle-specification.md:1777"
            },
            {
              "name": "Distribution rate denominator",
              "symbol": "EPOCH_POW_DISTRIBUTION_RATE_DEN (rho denominator)",
              "value": "200 (rho = 1/200)",
              "citation": "bedrock-v1.1-mantle-specification.md:1778, :1834"
            },
            {
              "name": "Target accepted claims per block",
              "symbol": "TARGET_CLAIMS_PER_BLOCK / T",
              "value": "10",
              "citation": "bedrock-v1.1-mantle-specification.md:1779, :1799"
            },
            {
              "name": "Expected blocks per epoch",
              "symbol": "EXPECTED_BLOCKS_PER_EPOCH / N_b",
              "value": "21600 (= 10k, restated from Cryptarchia)",
              "citation": "bedrock-v1.1-mantle-specification.md:1780, :1789; cryptarchia-v1-protocol.md:146"
            },
            {
              "name": "Fee share diverted to the pool, numerator",
              "symbol": "POW_SHARE / beta numerator",
              "value": "10",
              "citation": "bedrock-v1.1-mantle-specification.md:1806"
            },
            {
              "name": "Fee share diverted to the pool, denominator",
              "symbol": "SHARE_DEN",
              "value": "100 (beta = 10/100 = a tenth)",
              "citation": "bedrock-v1.1-mantle-specification.md:1807, :1816"
            },
            {
              "name": "Genesis pool seed",
              "symbol": "POW_REWARD_POOL_GENESIS",
              "value": "5/1000 of the supply at network launch. NOT stated as a count of lepta anywhere.",
              "citation": "bedrock-genesis-block.md:76-80; bedrock-v1.1-mantle-specification.md:1838, :1854"
            },
            {
              "name": "Acceptance window depth, in expected blocks",
              "symbol": "EXPECTED_BLOCKS_PER_WINDOW / W_b",
              "value": "10",
              "citation": "bedrock-v1.1-mantle-specification.md:1585"
            },
            {
              "name": "Acceptance window, in slots",
              "symbol": "WINDOW",
              "value": "floor(W_b / f) = 300 slots at W_b = 10, f = 1/30. Note: given only as a formula plus prose; no python constant assignment.",
              "citation": "bedrock-v1.1-mantle-specification.md:1597, :1600"
            },
            {
              "name": "EMA smoothing weight on the previous estimate",
              "symbol": "EMA_SMOOTHING_FACTOR / F",
              "value": "9",
              "citation": "bedrock-v1.1-mantle-specification.md:1867"
            },
            {
              "name": "EMA smoothing scale",
              "symbol": "EMA_SMOOTHING_PRECISION / P",
              "value": "10 (F < P required)",
              "citation": "bedrock-v1.1-mantle-specification.md:1868"
            },
            {
              "name": "Genesis reward difficulty",
              "symbol": "difficulty_reward at genesis / d_reward(0)",
              "value": "p / 2**26 (scalar field modulus divided by 2^26)",
              "citation": "bedrock-v1.1-mantle-specification.md:1901; bedrock-genesis-block.md:301"
            },
            {
              "name": "Scalar field modulus",
              "symbol": "p",
              "value": "0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001 (BN254 scalar field)",
              "citation": "cryptarchia-proof-of-leadership.md:219; common-cryptographic-components.md:133"
            },
            {
              "name": "Execution gas of the claim Operation",
              "symbol": "EXECUTION_CLAIM_POW_REWARD_GAS",
              "value": "56",
              "citation": "bedrock-v1.1-mantle-specification.md:2255; analysis-gas-cost-determination.md:79, :246"
            },
            {
              "name": "Execution gas of the accompanying TRANSFER (self-funding claim tx)",
              "symbol": "EXECUTION_TRANSFER_GAS",
              "value": "590",
              "citation": "bedrock-v1.1-mantle-specification.md:2245; analysis-gas-cost-determination.md:248"
            },
            {
              "name": "Execution base fee price",
              "symbol": "execution_gas_base_price / b_exec",
              "value": "UNSET here â a per-block market price from the Execution Market; its effective floor is 1 lepton per gas",
              "citation": "bedrock-v1.1-mantle-specification.md:141, :146; execution-market.md:206"
            },
            {
              "name": "Permanent storage gas price",
              "symbol": "permanent_storage_gas_price / P_STR",
              "value": "UNSET here â a per-block market price from the Storage Market; initial price 1 and effective floor 1 lepton per gas",
              "citation": "bedrock-v1.1-mantle-specification.md:141, :145; storage-markets.md:224"
            },
            {
              "name": "Encoded size of a claim transaction (drives its storage fee)",
              "symbol": "len(encode(signed_mantle_tx))",
              "value": "UNSET â never stated. Only the resulting fee at the market floor is given: 6,664 lepta.",
              "citation": "bedrock-v1.1-mantle-specification.md:148, :1858"
            },
            {
              "name": "Slot activation coefficient",
              "symbol": "f",
              "value": "1/30",
              "citation": "cryptarchia-v1-protocol.md:94"
            },
            {
              "name": "Security parameter",
              "symbol": "k",
              "value": "2160 blocks",
              "citation": "cryptarchia-v1-protocol.md:95"
            },
            {
              "name": "Max transactions per block",
              "symbol": "MAX_BLOCK_TXS",
              "value": "1024",
              "citation": "cryptarchia-v1-protocol.md:98; bedrock-v1.1-mantle-specification.md:1828"
            },
            {
              "name": "Indivisible token unit",
              "symbol": "lepton",
              "value": "1 LGO = 10^9 lepta; launch supply 10^10 LGO = 10^19 lepta",
              "citation": "bedrock-v1.1-mantle-specification.md:2119, :2121"
            },
            {
              "name": "CLAIM_POW_REWARD opcode",
              "symbol": "0x40",
              "value": "0x40",
              "citation": "bedrock-v1.1-mantle-specification.md:260"
            }
          ],
          "eligibility": "Anyone at all â no stake, no declaration, no prior tokens. A miner searches for a `public_key` whose ticket `zkhash(epoch_nonce, block_hash, public_key)` falls strictly below `difficulty_reward` (bedrock-v1.1-mantle-specification.md:1626-1634, :1676). The Operation carries no signature and no zero-knowledge proof; "the authorisation is the puzzle solution itself" (:1640).

A claim is accepted iff ALL of (:1663-1681):
1. `epoch_pow_reward > 0` â fails once the pool has fallen so far that compute_epoch_pow_reward floors to zero (permanent stop);
2. `pow_reward_pool >= epoch_pow_reward` â fails when the pool has been drained within the epoch to less than one reward (claiming stops until the next boundary);
3. the referenced `block_hash` resolves on the CANONICAL chain and `0 <= current_slot - block.slot <= WINDOW`;
4. `claim.epoch_nonce == get_current_epoch_nonce()` â the Cryptarchia eta of the current epoch;
5. `puzzle_ticket < difficulty_reward`;
6. `puzzle_ticket not in pow_nullifiers` (the nullifier IS the ticket).

Conditions 1 and 2 are evaluated PER CLAIM against the pool as it stands at that point in the block, and, because validation is interleaved with execution, also net of earlier claims within the same transaction (:1692, :1826, :217). A claim that fails only because the pool is exhausted is simply invalid and its whole transaction is rejected (:1826).

The claim is self-funding: the reward note's id is computable in advance (because sigma_e is fixed for the epoch), so a following TRANSFER in the same transaction can spend it to pay the transaction's own fee (:1735-1770). No tokens are required beforehand.

A block builder may include its own claims; this is permitted and made self-correcting by the difficulty controller (:1895). Reorg of the referenced block invalidates a claim, which must then be re-mined (:1608).",
          "timing": "PER CLAIM (any block): the pool guard, the window check, the nonce check, the threshold check and the nullifier check; on success, one output note of value `epoch_pow_reward` and `pow_reward_pool -= epoch_pow_reward`, applied immediately in-block (:1663-1727).

PER BLOCK: `difficulty_reward` is retargeted. Ordering is consensus-critical and gives a ONE-BLOCK LAG: every claim in a block is validated against the target produced by the PREVIOUS block's update; the update computed from a block's own accepted claim count is applied AFTER the block is processed and governs the NEXT block (:1864, :1887). Genesis supplies the target the first block is validated against (:1887, :1901).

PER EPOCH: at each epoch boundary, BEFORE any block of the new epoch is processed, (a) `pow_reward_pool += get_pow_pool_refill(previous epoch's blocks)`, then (b) `epoch_pow_reward = compute_epoch_pow_reward(pow_reward_pool)` â in that order (:1803-1812). So the refill lags by ONE FULL EPOCH (fees of epoch e-1 fund the pool used in epoch e), and sigma_e is then frozen for the whole of epoch e even as the pool it is paid from shrinks with every claim (:1820, :1692).

Epoch length: 10*floor(k/f) = 648,000 slots = 648,000 s â 7.5 days, with 21,600 blocks expected (cryptarchia-v1-protocol.md:144-146, :96).

NOT the same schedule as the Blend difficulty: `difficulty_blend` is per-epoch, fixed at the epoch N-1 lottery-constants snapshot from epoch N-2's load, and is never evaluated by any Operation (:1907-1913). The two difficulties are independent (:1909).",
          "ambiguities": [
            "The 'twice the fee' sentence at bedrock-v1.1-mantle-specification.md:1858 appears internally inconsistent by a factor of 2. It states: 'A seed of five thousandths yields an opening reward that exceeds twice the claim's fee for as long as the fee is at or below 1.157 x 10^-10 of the launch supply.' But 1.157e-10 of 10^19 lepta is 1.157e9 lepta, which is exactly the opening reward itself (5e16 * 1 // 43,200,000 = 1,157,407,407). reward > 2*fee requires fee <= reward/2 ~ 5.787e-11 of supply. Either the stated threshold is the one-times-fee threshold mislabelled, or a different reward is meant. I do not reconcile it. (The recomputation is mine and is marked derived.)",
            "'WINDOW' is used in the pseudocode at bedrock-v1.1-mantle-specification.md:1591 but is never assigned as a python constant; only `EXPECTED_BLOCKS_PER_WINDOW = 10` is declared (:1585) and WINDOW is defined by the LaTeX relation floor(W_b/f) at :1597 with the value 300 given in prose at :1600. An implementer must read the prose to get the constant.",
            "The constant is named `EPOCH_POW_DISTRIBUTION_RATE` in prose at :1834 ('`EPOCH_POW_DISTRIBUTION_RATE` is set to a two-hundredth') but no constant of that name exists; the declared constants are `EPOCH_POW_DISTRIBUTION_RATE_NUM` and `_DEN` (:1777-1778). Cosmetic, but the name will not be found by grep in an implementation.",
            "`difficulty_reward` genesis value is given only in prose as 'the scalar field modulus divided by 2^26' (:1901), with no python assignment and no explicit rounding direction. By analogy with `BLEND_DIFFICULTY_BASE: PowTarget = p // 2**19` (:1918) floor division is the evident intent, but it is not stated for the reward target.",
            "`get_pow_pool_refill` is defined only in overview-cryptoeconomics.md:180-184, whose signature takes an `epoch` object and iterates `e.blocks`, while bedrock-v1.1-mantle-specification.md:1809 calls it as `get_pow_pool_refill(epoch_blocks)` on a `list[Block]`. Same semantics, mismatched signatures across the two documents. Neither doc defines `get_collected_fees(b)` in code; it is defined in prose (overview:187) as 'the total Execution base fees and Permanent Storage fees paid by the transactions of block b'.",
            "Whether execution TIPS are inside `get_collected_fees(b)` is not stated explicitly. The prose names only 'Execution base fees and Permanent Storage fees' (overview:187), and tips are separately reminted to leaders (overview:171, :244), which reads as tips being excluded â but the spec never says so in those words.",
            "The two documents describe the same diversion at different granularities without contradiction but without a single normative statement: overview-cryptoeconomics.md:177 says the share is credited 'A fixed share of the fees a block collects' (per block, credited as fees are collected), while bedrock-v1.1-mantle-specification.md:1803 credits the whole epoch's accrual to the pool at the boundary. An implementation must accrue per block and credit at the boundary; the pool balance visible to claims does not rise mid-epoch.",
            "`compute_epoch_pow_reward` is not marked as checked or unchecked arithmetic. :1818 says 'All arithmetic here is checked' for the Reward Pool section, and :135 exempts only PowTarget controllers, so it is checked_uint64 â but the pseudocode at :1786 has no checked_uint64 wrapper, unlike :1810 and :1726.",
            "Nothing states what happens to `epoch_pow_reward` if the pool is empty at a boundary beyond the reward flooring to 0 and claiming stopping 'permanently' (:1830). Recovery is possible in principle if refill later lifts the pool back above 43,200,000 lepta, but the spec calls it a permanent stop without qualifying it."
          ],
          "not_specified": [
            "POW_REWARD_POOL_GENESIS as a count of lepta. Only '5/1000 of the supply at network launch' is stated (bedrock-genesis-block.md:76-80, mantle:1838, :1854), and the spec explicitly says it is stated as a fraction on purpose (:1856).",
            "The encoded byte size of a CLAIM_POW_REWARD transaction, which is half of its fee. Only the resulting fee at the market floor is given (6,664 lepta, :1858).",
            "Any minimum, initial, or launch value for `execution_gas_base_price` or `permanent_storage_gas_price` in the Mantle spec itself. Both are market outputs; only the rounding floor of 1 is given (execution-market.md:206, storage-markets.md:224).",
            "Any per-block or per-transaction cap on the NUMBER of claims. There is none: 'Nothing stops a block from carrying more claims than the target' (:1824). The only limits are MAX_BLOCK_TXS = 1024, MAX_BLOCK_SIZE, and the pool guard.",
            "Any rule about who may include claims, or ordering of claims within a block, beyond the interleaved per-Operation pool guard.",
            "Any mempool or propagation rule for claims, or any anti-spam rule for solutions that fail the pool guard.",
            "The hashrate-to-solution-rate relation. Only a prose calibration: at 2^26 'a solution is around three hours of work on one core of the target machine' and reaching the target rate 'requires a few thousand cores' (:1903). The 'target machine' is not defined here.",
            "How `claims_in_block` counts claims in a block that a transaction later invalidated â the spec says 'accepted count' (:1887) but does not define the counter beyond that.",
            "Whether the emission model's measurement of burnt fees is reduced by the diversion in the pseudocode of block-rewards.md. It is stated only in prose in overview-cryptoeconomics.md:195-197. block-rewards.md contains no mention of proof of work at all (grep: zero hits).",
            "Any interaction between the PoW pool and the 60/40 Blend/leader split, other than the prose statement that the split is unchanged and applies to whatever the block reward turns out to be (overview:201)."
          ],
          "derived_not_stated": [
            "DERIVED BY ME: the reward denominator is the compile-time constant 200 * 10 * 21600 = 43,200,000, so sigma_e = floor(pool / 43_200_000) at the specified values. The spec gives the three factors separately (:1783-1786).",
            "DERIVED BY ME: opening reward at genesis = floor(5e16 * 1 / 43,200,000) = 1,157,407,407 lepta ~= 1.157 LGO, using POW_REWARD_POOL_GENESIS = 0.005 * 10^19 = 5 x 10^16 lepta. The 5e16 figure is itself derived from '5/1000 of launch supply' (bedrock-genesis-block.md:77) times 'supply of 10^19 lepta' (mantle:2121). The spec never writes either number.",
            "DERIVED BY ME: at the specified constants the retarget reduces to new_target = floor(100 * current_target / (claims_in_block + 90)), since demand = max(1, (10-9)*c + 9*10) = c + 90 which is never below 90. The max(1, ...) floor is therefore dead code at F=9, P=10, T=10 â it only binds if the constants change.",
            "DERIVED BY ME: at zero claims the target multiplies by 100/90 ~ 1.111 per block; recovering from a target 100x too hard therefore takes log(100)/log(10/9) ~ 44 blocks ~ 22 minutes at f=1/30 â consistent with the spec's 'corrects itself within an hour' (:1901), which is itself a prose derivation.",
            "DERIVED BY ME: the canonical self-funding claim transaction's execution gas is 646 (56 + 590). The spec gives the two constants and states the transaction 'already carries a TRANSFER at 590' (analysis-gas-cost-determination.md:248) but never writes the sum.",
            "DERIVED BY ME: the 6,664-lepta floor fee implies an encoded transaction size of 6,664 - 646 = 6,018 bytes when both market prices are at their floor of 1. The spec states neither the size nor this decomposition; treat 6,018 as an inference, not a specified quantity. [WITHDRAWN -- see 5.5: the fee is stated at the RESTING price of 7, giving 306 bytes, not at the floor of 1; ClaimPowRewardOp is three 32-byte fields, so 6,018 is implausible and the count limit binds first.]",
            "STATED AS A SPEC DERIVATION (not my own): EXPECTED_BLOCKS_PER_EPOCH = 10*floor(k/f)*f = 10k = 21,600, 'the simplification being exact because k/f is an integer at the specified constants' (cryptarchia-v1-protocol.md:146). The Mantle spec restates it as a constant and says it is not a free choice (:1789).",
            "STATED AS A SPEC DERIVATION: an epoch running at the target rate distributes exactly the fraction rho of the pool, since T * N_b * sigma_e = rho * pool, independent of T (:1832).",
            "STATED AS A SPEC DERIVATION: the pool settles at 1/rho epochs' worth of distribution, i.e. ~200 epochs ~ 4 years of reserve at rho = 1/200 (:1834); and the settled reward per claim is beta times one block's fees divided by T, with rho cancelling out (:1842).",
            "STATED AS A SPEC DERIVATION: within-epoch exhaustion requires T/rho = 2,000 claims in every block for a whole epoch (7.5 days) against MAX_BLOCK_TXS = 1024, hence 'impossible by construction' (:1828, :1836).",
            "STATED AS A SPEC DERIVATION: the reward covers the claim's own fee once a block carries at least T/beta ~ 120 transactions; 2x the fee at ~240 and 5x at ~600 (:1844).",
            "NOTE FOR THE SIMULATOR: the flooring sites are exactly three and they are all distinct â (1) per-block refill floor: floor(fees_b * 10 / 100); (2) per-epoch reward floor: floor(pool * 1 / 43_200_000), whose residue stays in the pool (:1791); (3) per-block retarget floor: floor(100 * target / (c + 90)) over big integers. There is no flooring in the pool decrement, which is exact."
          ]
        },
        "check": {
          "stream": "Proof of Work claim reward (CLAIM_POW_REWARD) â verification of the extraction against /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw

VERDICT IN ONE LINE: the reward machinery itself is extracted faithfully â zero invented formulas, zero invented constants, and every pseudocode block is quoted verbatim from the cited lines. The defects are all at the fee-market boundary (the claim's own fee), where one "UNSET" is wrong and one "initial price 1" is an illustrative value promoted to a specified one.

=== A. FORMULAS AND CONSTANTS: ALL CONFIRMED VERBATIM ===

Every python block in the extraction matches the source character-for-character at the cited lines:
- compute_epoch_pow_reward and the four constants at bedrock-v1.1-mantle-specification.md:1776-1787 â confirmed, including the single `// denominator` (one flooring site, as claimed). rho = 1/200 is real: line 1778 reads `EPOCH_POW_DISTRIBUTION_RATE_DEN: uint64 = 200`, and :1836 closes "A two-hundredth is where the pressures now meet, and is the value specified."
- on_epoch_boundary, POW_SHARE=10, SHARE_DEN=100 at :1805-1812 â confirmed. :1803 reads exactly "At each epoch boundary, before any block of the new epoch is processed, the pool is credited with the refill accrued over the previous epoch and the per-claim reward is then recomputed from the refilled pool" â the refill-then-recompute ordering is real.
- get_pow_pool_refill at overview-cryptoeconomics.md:180-184 â confirmed verbatim, including `get_collected_fees(b) * POW_SHARE // SHARE_DEN` inside the per-block loop, so the "flooring is PER BLOCK" claim is correct.
- Validation asserts at :1663-1681 and execution at :1713-1727 â confirmed verbatim, both asserts of the pool guard present.
- get_puzzle_ticket at :1626-1631 â confirmed, including the `FiniteField(claim.block_hash, byte_order="little", modulus=p)` wrapper. :1636 "Note that this derivation carries no domain separation tag." â exact.
- accept_claim_pow_op at :1584-1591, WINDOW = floor(W_b/f) at :1597, "With W_b = 10 and f = 1/30 this is 300 slots" at :1600 â all exact.
- compute_new_reward_difficulty at :1866-1884 â confirmed verbatim including comments. EMA_SMOOTHING_FACTOR=9 (:1867), PRECISION=10 (:1868).
- mandatory_fees at :144-157 â confirmed verbatim (the extraction's "144-157" is right; the citation list's ":139-158" spans the heading and closing fence, also fine).
- Gas table :2245 EXECUTION_TRANSFER_GAS 590 and :2255 EXECUTION_CLAIM_POW_REWARD_GAS 56 â confirmed. analysis-gas-cost-determination.md:79 `CLAIM_POW_REWARD_GAS = 56` and :248 "the transaction already carries a `TRANSFER` at 590" â confirmed verbatim.
- Opcode 0x40 at :260, checked_uint64 at :121-133, the big-integer exemption and 2**261 figure at :135, lepton/10^19 at :2119/:2121, interleaving at :217 â all confirmed.
- bedrock-genesis-block.md:76-80 (POW_REWARD_POOL_GENESIS = 5/1000 of launch supply, as a comment on an unassigned declaration) and :298-301 â confirmed.
- cryptarchia-v1-protocol.md:94 f=1/30, :95 k=2160, :96 slot=1s, :98 MAX_BLOCK_TXS=1024, :146 "10*floor(k/f)*f = 10k = 21,600" â confirmed.
- cryptarchia-proof-of-leadership.md:219 p = 0x30644e72â¦0001 â confirmed.

The derived quantities are all correctly labelled as derived and all arithmetically right: 200*10*21600 = 43,200,000; floor(5e16/43,200,000) = 1,157,407,407; demand reduces to c+90; new = floor(100*target/(c+90)); log(100)/log(10/9) â 43.7 blocks â 22 min.

=== B. THE "TWICE THE FEE" INCONSISTENCY IS REAL ===
:1858 reads: "A seed of five thousandths yields an opening reward that exceeds twice the claim's fee for as long as the fee is at or below 1.157 Ã 10^-10 of the launch supply". 1.157e-10 Ã 1e19 = 1.157e9 lepta, which equals the opening reward exactly, not half of it. The extraction's refusal to reconcile it, and its labelling of the recomputation as derived, is the correct handling. This is a defect in the source, not in the extraction.

=== C. WHAT IS WRONG ===
Two citations do not say what is claimed, and both concern the two market prices â i.e. the claim's own fee, which is explicitly inside this stream's scope. See wrong_citations and corrections. The consequence for a simulator: it would model the execution base fee as a free parameter when the spec actually pins its launch value at 1, and it would model the storage price as pinned at 1 when the spec actually leaves it to genesis governance. That is exactly backwards on both.

=== D. UNSET CHECK ===
- POW_REWARD_POOL_GENESIS as a count of lepta: genuinely unstated. bedrock-genesis-block.md:76-78 declares `POW_REWARD_POOL_GENESIS: TokenValue` with no value, only the comment "= 5/1000 of the supply at network launch"; :1856 says it is stated as a fraction on purpose. CORRECT.
- Encoded byte size of a claim transaction: genuinely unstated, and worse than the extraction says â see missed_elements.
- permanent_storage_gas_price: genuinely unset as a number, but for the opposite reason the extraction gives.
- execution_gas_base_price: NOT unset at launch. See corrections.
- WINDOW as a python constant: genuinely never assigned. grep for "WINDOW" in the mantle spec returns only :1585 (EXPECTED_BLOCKS_PER_WINDOW), :1591 (use), :1597 (LaTeX), :1656 (comment). The extraction's ambiguity note is exactly right.
- `EPOCH_POW_DISTRIBUTION_RATE` bare name: grep confirms it appears only at :1834; the declared constants are _NUM and _DEN. Correct.

=== E. ILLUSTRATIVE-VS-SPECIFIED CHECK ===
The only value the extraction presents as specified that is actually illustrative is the storage market's "initial price 1". Everything in the PoW section marked as specified is a real constant assignment. The prose figures the extraction lists under "STATED AS A SPEC DERIVATION" (120/240/600 transactions at :1844, 2000 claims/block at :1828 and :1836, ~200 epochs â 4 years at :1834, 3 hours per core at :1903) are all present at those lines and are correctly classed as spec-stated derivations rather than constants.

=== F. NO INVENTED ELEMENTS ===
I looked specifically for a fabricated second division, a fabricated per-block pool credit, a fabricated claims-per-block cap, and a fabricated genesis lepta figure. None are present. The extraction is notably careful in exactly the places where invention is tempting: it refuses to write POW_REWARD_POOL_GENESIS as a number without labelling it derived, refuses to reconcile the :1858 factor of 2, and flags that the retarget's max(1,â¦) is dead code at the specified constants rather than silently dropping it.",
          "citations_verified": false,
          "invented_elements": [],
          "wrong_citations": [
            "storage-markets.md:224 â cited in the parameters table for "initial price 1 and effective floor 1 lepton per gas". The line actually reads "Rounding upwards makes 1 LGO per Permanent Storage Gas the effective floor of the price" â LGO, not lepton. The extraction silently normalises the unit. The source docs genuinely conflict here (bedrock-v1.1-mantle-specification.md:2119 asserts "both fee markets price in whole lepta per unit of gas", and :2121 repeats it), so the correction is probably right, but it should be flagged as a source conflict rather than presented as what the line says.",
            "storage-markets.md:224 â cited for "initial price 1". Line 224 mentions P_STR(0)=1 only inside a counterfactual about rounding direction ("the initial price $P_{STR}(0)=1$ would be mapped to 0 by the first downward adjustment"). The normative statement is at storage-markets.md:230, under "### Genesis State": "Initial Price P_STR(0): Set to a pre-determined value established by genesis governance." So the initial storage price is UNSET, and the 1 in the extraction is an illustrative number lifted out of a hypothetical.",
            "common-cryptographic-components.md:133 â cited alongside cryptarchia-proof-of-leadership.md:219 as a source for the value of p. Line 133 names BN254 ("the Logos Blockchain relies on the BN254 elliptic curve, so the $\mathbb{F}_p$ elements are taken from the prime field corresponding to BN254") but states no modulus. The numeric value comes only from cryptarchia-proof-of-leadership.md:219. Worth noting because bedrock-v1.1-mantle-specification.md:1634 points the reader to Common Cryptographic Components for p, and that document does not give it â a real spec gap the extraction did not surface."
          ],
          "missed_elements": [
            "execution-market.md:95 specifies the launch value of the execution base fee: "$b_{exec}[s]$ | Base Fee | - | The protocol-defined Execution Gas price for inclusion in block $s$. This is initialized at 1 for the first block." The extraction marks execution_gas_base_price as "UNSET here" and lists "Any minimum, initial, or launch value for execution_gas_base_price" under not_specified. A simulator needs this: it is the value that produces the 6,664-lepta floor fee the extraction reasons from.",
            "The whole execution base-fee dynamics, needed to model the claim's own fee over time: execution-market.md:99 G_max = 3,193,460; :100 G_target = 1,596,730; :101 phi = 1/8; :102 q = 9/10; and the reference implementation at :188-203 (BASE_FEE_NUMERATOR = 11_177_110, BASE_FEE_DENOMINATOR = 12_773_840, update_g_avg floors, update_base_fee uses ceil_div). The extraction cites only :206 (the rounding-direction prose) and treats the price as an exogenous unknown.",
            "MAX_BLOCK_SIZE = 1 MB (cryptarchia-v1-protocol.md:97; overview-cryptoeconomics.md:91 says "Blocks are limited to 1MiB with a maximum of 1024 Mantle Transactions per block"). The extraction names MAX_BLOCK_SIZE in not_specified but gives it no value or citation. This matters concretely: with the extraction's own inferred claim-transaction size of ~6,018 bytes, the 1 MB body limit caps a block at roughly 170 claim transactions â an order of magnitude tighter than the MAX_BLOCK_TXS = 1024 the spec's exhaustion argument at :1828 leans on. A simulator of the drain path needs the tighter bound. [WITHDRAWN -- see 5.5: the fee is stated at the RESTING price of 7, giving 306 bytes, not at the floor of 1; ClaimPowRewardOp is three 32-byte fields, so 6,018 is implausible and the count limit binds first.]",
            "bedrock-v1.1-mantle-specification.md:1694: "A claim built against any other epoch is rejected, so a solution is usable only within the epoch it was found in and must be re-mined afterwards", and :1696: the epoch nonce "is fixed part way through the *preceding* epoch and is public from that moment, so solutions for an epoch can be computed before it begins." The extraction records the assert at step 3 but not these two operational consequences â all in-flight work is invalidated at each epoch boundary, but mining may be front-run into the preceding epoch. Both change how a miner-behaviour simulator schedules work.",
            "mantle-transaction-encoding.md does not define a ClaimPowReward payload at all: the OpPayload alternation at lines 65-74 lists Transfer, ChannelInscribe, ChannelConfig, ChannelDeposit, ChannelWithdraw, ChannelTransfer, SDPDeclare, SDPWithdraw, SDPActive, LeaderClaim â and stops. The extraction says the encoded size is "never stated"; the stronger and more useful fact is that the operation is absent from the encoding specification entirely, so the size is not even derivable from field widths.",
            "bedrock-v1.1-mantle-specification.md:1901 gives the quantitative cost of the over-permissive genesis-difficulty direction: "for an initial value a hundredfold too permissive comes to some twelve hundred extra claims over about twenty blocks â in aggregate about three thousandths of one percent of the genesis pool." The extraction derives the too-hard direction (~44 blocks) but omits this one, which is the better validation target for a simulator, since it is a spec-stated number the model should reproduce.",
            "bedrock-v1.1-mantle-specification.md:1899 states the controller invariant explicitly: "the invariant is that the estimate equals `TARGET_CLAIMS_PER_BLOCK` divided by the current target". This is the closed-form the retarget implements and is the cheapest correctness check on a simulator's difficulty loop; the extraction cites :1899 only for the F/P rationale and the ~10-block time constant.",
            "bedrock-v1.1-mantle-specification.md:2259: "The value bounds the fee a claim transaction must pay, and therefore bears on whether a claim is worth making at all: a claim whose fee exceeds its reward is never submitted." Minor, but it is the spec's own statement of the participation condition a simulator would encode."
          ],
          "corrections": [
            "Replace the parameter entry for execution_gas_base_price. It is not "UNSET here". execution-market.md:95 specifies it is initialized at 1 for the first block, and execution-market.md:188-203 gives its complete update rule. Correspondingly, delete or heavily qualify the not_specified item "Any minimum, initial, or launch value for execution_gas_base_price or permanent_storage_gas_price in the Mantle spec itself" â the hedge "in the Mantle spec itself" is technically true but reads as a claim that no launch value exists anywhere, which is false for execution.",
            "Replace the parameter entry for permanent_storage_gas_price. Drop "initial price 1": storage-markets.md:230 says "Initial Price P_STR(0): Set to a pre-determined value established by genesis governance" â genuinely unset, a free parameter a simulator must sweep. Keep the rounding floor, but record that storage-markets.md:224 states that floor as "1 LGO per Permanent Storage Gas" while bedrock-v1.1-mantle-specification.md:2119/:2121 states it as one lepton per gas â a source conflict of 10^9, worth listing under ambiguities rather than resolving silently.",
            "Add MAX_BLOCK_SIZE = 1 MB (cryptarchia-v1-protocol.md:97) to the parameters, and add a note that at the extraction's own inferred ~6,018-byte claim transaction the size limit binds at roughly 170 claim transactions per block, well before MAX_BLOCK_TXS = 1024. The spec's own "impossible by construction" margin at :1828 and :1836 is therefore larger than the spec itself states. [WITHDRAWN -- see 5.5: the fee is stated at the RESTING price of 7, giving 306 bytes, not at the floor of 1; ClaimPowRewardOp is three 32-byte fields, so 6,018 is implausible and the count limit binds first.]",
            "Drop common-cryptographic-components.md:133 as a citation for the value of p; it names BN254 but gives no modulus. Cite cryptarchia-proof-of-leadership.md:219 alone, and add to ambiguities that bedrock-v1.1-mantle-specification.md:1634 refers the reader to a document that does not contain the value.",
            "Add to the eligibility/timing sections that a solution dies at the epoch boundary and must be re-mined (:1694), while solutions for epoch N may be ground from the moment N's nonce is public part way through N-1 (:1696).",
            "Everything else stands as written. In particular the two corrections the extraction flags in its own headline â rho = 1/200, and one floor over a single combined denominator rather than two divisions â are both confirmed against :1778, :1836 and :1782-1786."
          ],
          "verdict": "needs-correction"
        }
      }
    ]
  },
  "workflowProgress": [
    {
      "type": "workflow_phase",
      "index": 1,
      "title": "Extract"
    },
    {
      "type": "workflow_phase",
      "index": 2,
      "title": "Verify"
    },
    {
      "type": "workflow_phase",
      "index": 3,
      "title": "Consolidate"
    },
    {
      "type": "workflow_agent",
      "index": 1,
      "label": "extract:emission",
      "phaseIndex": 1,
      "phaseTitle": "Extract",
      "agentId": "a28590eb00cb8ef80",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1786974160985,
      "queuedAt": 1786974155671,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "Block reward per block and the emission-rate-factor controlâ¦",
      "promptPreview": "You are extracting reward formulas from the Logos blockchain specifications so a simulator can
implement them EXACTLY as specified. The specification tree is at:

  /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw

Relevant documents include: block-rewards.md, overview-cryptoeconomics.md,
bedrock-v1.1-mantle-specification.md, bedrock-service-reward-distributioâ¦",
      "lastProgressAt": 1786974610578,
      "tokens": 81817,
      "toolCalls": 19,
      "durationMs": 449592,
      "resultPreview": "{"stream":"Block reward per block and the emission-rate-factor control function A_t (including the inferred-total-stake KPI D and its lag)","formula":"=== 1. TOTAL MINTED PER BLOCK â block-rewards.md:193-197 (equation (1)) ===\n\n$$\n\\begin{equation}\nA_t \\cdot \\dfrac{I_{max} \\cdot S_{tge} \\cdot \\Delta_t}{f} + (1-A_t) \\cdot R_\\text{block}\n\\end{equation}\n$$\n\nwith (block-rewards.md:199-â¦"
    },
    {
      "type": "workflow_agent",
      "index": 2,
      "label": "extract:leader",
      "phaseIndex": 1,
      "phaseTitle": "Extract",
      "agentId": "aa959eb1f2375c928",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1786974166660,
      "queuedAt": 1786974155671,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "THE LEADER REWARD â what a block's proposer receives in Logâ¦",
      "promptPreview": "You are extracting reward formulas from the Logos blockchain specifications so a simulator can
implement them EXACTLY as specified. The specification tree is at:

  /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw

Relevant documents include: block-rewards.md, overview-cryptoeconomics.md,
bedrock-v1.1-mantle-specification.md, bedrock-service-reward-distributioâ¦",
      "lastProgressAt": 1786974651679,
      "tokens": 82985,
      "toolCalls": 26,
      "durationMs": 485019,
      "resultPreview": "{"stream":"THE LEADER REWARD â what a block's proposer receives in Logos/Bedrock (Cryptarchia PoS leadership), covering the 40/60 split, the voucher-based anonymous claim path, the lottery win condition and stake weighting, note aging, minimum-stake question, and the slot/block relationship.","formula":"=== A. THE SPLIT: 40% of each block reward to leaders ===\n\noverview-cryptoeconomics.md:142-14â¦"
    },
    {
      "type": "workflow_agent",
      "index": 3,
      "label": "extract:service",
      "phaseIndex": 1,
      "phaseTitle": "Extract",
      "agentId": "a04c6990171835df2",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1786974164855,
      "queuedAt": 1786974155671,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "Service provision reward (Service Declaration Protocol + Seâ¦",
      "promptPreview": "You are extracting reward formulas from the Logos blockchain specifications so a simulator can
implement them EXACTLY as specified. The specification tree is at:

  /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw

Relevant documents include: block-rewards.md, overview-cryptoeconomics.md,
bedrock-v1.1-mantle-specification.md, bedrock-service-reward-distributioâ¦",
      "lastProgressAt": 1786974632935,
      "tokens": 110895,
      "toolCalls": 31,
      "durationMs": 468080,
      "resultPreview": "{"stream":"Service provision reward (Service Declaration Protocol + Service Reward Distribution Protocol; the only declared service is the Blend Network, `ServiceType.BN`)","formula":"The SRDP itself specifies only a delegation, not a formula:\n\n  bedrock-service-reward-distribution.md:70-76\n  \"At the end of epoch **N+1**, service rewards for the validator `n` for the epoch **N** are computed bâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 4,
      "label": "extract:pow",
      "phaseIndex": 1,
      "phaseTitle": "Extract",
      "agentId": "a6a50a88e65e88363",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1786974162770,
      "queuedAt": 1786974155671,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "Proof of Work claim reward (CLAIM_POW_REWARD): per-claim reâ¦",
      "promptPreview": "You are extracting reward formulas from the Logos blockchain specifications so a simulator can
implement them EXACTLY as specified. The specification tree is at:

  /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw

Relevant documents include: block-rewards.md, overview-cryptoeconomics.md,
bedrock-v1.1-mantle-specification.md, bedrock-service-reward-distributioâ¦",
      "lastProgressAt": 1786974510269,
      "tokens": 66625,
      "toolCalls": 22,
      "durationMs": 347499,
      "resultPreview": "{"stream":"Proof of Work claim reward (CLAIM_POW_REWARD): per-claim reward, pool refill, distribution rate, target claim rate, reward-difficulty retarget, and the claim transaction's own fee.","formula":"CONFIRMED with two corrections (rho is 1/200, not unspecified; there is ONE floor, over a single combined denominator, not two divisions).\n\n=== A. Per-claim reward, computed at the epoch boundarâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 5,
      "label": "verify:pow",
      "phaseIndex": 2,
      "phaseTitle": "Verify",
      "agentId": "a9b04330145085eb8",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1786974523797,
      "queuedAt": 1786974513272,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "Proof of Work claim reward (CLAIM_POW_REWARD) â verificatioâ¦",
      "promptPreview": "You are verifying an extraction of reward formulas from the Logos blockchain
specifications at /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw.

Go to each cited file and line and check that it says what the extraction claims. Then check
for elements present in the specification but ABSENT from the extraction.

Report, specifically:
1. Any INVENTED element â â¦",
      "lastProgressAt": 1786974875063,
      "tokens": 84588,
      "toolCalls": 20,
      "durationMs": 351265,
      "resultPreview": "{"stream":"Proof of Work claim reward (CLAIM_POW_REWARD) â verification of the extraction against /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw\n\nVERDICT IN ONE LINE: the reward machinery itself is extracted faithfully â zero invented formulas, zero invented constants, and every pseudocode block is quoted verbatim from the cited lines. The defects are all â¦"
    },
    {
      "type": "workflow_agent",
      "index": 6,
      "label": "verify:emission",
      "phaseIndex": 2,
      "phaseTitle": "Verify",
      "agentId": "abfb311374d346200",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1786974619127,
      "queuedAt": 1786974612437,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "Block reward per block and the emission-rate-factor controlâ¦",
      "promptPreview": "You are verifying an extraction of reward formulas from the Logos blockchain
specifications at /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw.

Go to each cited file and line and check that it says what the extraction claims. Then check
for elements present in the specification but ABSENT from the extraction.

Report, specifically:
1. Any INVENTED element â â¦",
      "lastProgressAt": 1786974990402,
      "tokens": 101850,
      "toolCalls": 20,
      "durationMs": 371274,
      "resultPreview": "{"stream":"Block reward per block and the emission-rate-factor control function A_t (including the inferred-total-stake KPI D and its lag)","citations_verified":false,"invented_elements":["INVENTED DEFECT (ambiguities[10]): the claimed internal inconsistency in the epoch schedule does not exist. cryptarchia-v1-protocol.md:142 reads: '| Lottery Constants Finalization | $`s+\\lfloor\\frac{k}{f}\\rflâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 7,
      "label": "verify:service",
      "phaseIndex": 2,
      "phaseTitle": "Verify",
      "agentId": "a04856930ac7d5b65",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1786974643257,
      "queuedAt": 1786974635074,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "Service provision reward (Service Declaration Protocol + Seâ¦",
      "promptPreview": "You are verifying an extraction of reward formulas from the Logos blockchain
specifications at /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw.

Go to each cited file and line and check that it says what the extraction claims. Then check
for elements present in the specification but ABSENT from the extraction.

Report, specifically:
1. Any INVENTED element â â¦",
      "lastProgressAt": 1786975004115,
      "tokens": 122985,
      "toolCalls": 24,
      "durationMs": 360857,
      "resultPreview": "{"stream":"Service provision reward (Service Declaration Protocol + Service Reward Distribution Protocol; Blend Network, ServiceType.BN)","citations_verified":true,"invented_elements":["CONFLATION (not a fabricated formula, but a wrong identity a simulator would encode): the parameter table gives the Blend income as `I  (= Rewards_Epoch for the BN service)`, and STEP 1 is headed `the service's shaâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 8,
      "label": "verify:leader",
      "phaseIndex": 2,
      "phaseTitle": "Verify",
      "agentId": "aaace5c63f46c39cb",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1786974658827,
      "queuedAt": 1786974653725,
      "attempt": 1,
      "lastToolName": "StructuredOutput",
      "lastToolSummary": "THE LEADER REWARD â 40/60 split, voucher-based anonymous clâ¦",
      "promptPreview": "You are verifying an extraction of reward formulas from the Logos blockchain
specifications at /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw.

Go to each cited file and line and check that it says what the extraction claims. Then check
for elements present in the specification but ABSENT from the extraction.

Report, specifically:
1. Any INVENTED element â â¦",
      "lastProgressAt": 1786975037463,
      "tokens": 113320,
      "toolCalls": 25,
      "durationMs": 378636,
      "resultPreview": "{"stream":"THE LEADER REWARD â 40/60 split, voucher-based anonymous claim, lottery win condition and stake weighting, note aging, minimum-stake question, slot/block relationship.","citations_verified":true,"invented_elements":["NONE FABRICATED. No formula, parameter, or numeric value in the extraction is absent from the source. Every quoted block I checked is verbatim â including the two deliberatâ¦"
    },
    {
      "type": "workflow_agent",
      "index": 9,
      "label": "consolidate",
      "phaseIndex": 3,
      "phaseTitle": "Consolidate",
      "agentId": "a183c4cdd4d1bf86f",
      "model": "claude-opus-5[1m]",
      "state": "done",
      "startedAt": 1786975044099,
      "queuedAt": 1786975039483,
      "attempt": 1,
      "lastToolName": "Bash",
      "lastToolSummary": "cd /Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-â¦",
      "promptPreview": "You are writing the REWARD MODEL OF RECORD for a simulator of the
Logos blockchain's economics. Four reward streams were extracted from the specifications and
each extraction was independently verified against the source.

Where the verification found an invented element, REMOVE IT and mark it "not specified".
Where it found a wrong citation, correct it. Where it found a missed element, add it.

Pâ¦",
      "lastProgressAt": 1786975448773,
      "tokens": 133912,
      "toolCalls": 10,
      "durationMs": 404673,
      "resultPreview": "# Reward Model of Record â Logos Blockchain

**Source tree:** `/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/`
All citations below are `file:line` relative to that directory. This document folds in the independent verification of each extraction: invented elements have been removed, wrong citations corrected, missed elements added. Where a verification founâ¦"
    }
  ],
  "totalTokens": 898977,
  "totalToolCalls": 197
