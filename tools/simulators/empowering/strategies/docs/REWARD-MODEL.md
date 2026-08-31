<!-- Extracted from the reward-extraction agent-run log on 2026-08-18. This file used to BE
that log: a truncated JSON dump that opened mid-key and carried the document inside a
"result"."model" string, with the raw per-stream extraction data after it. The document is now
the document; the log, with the extraction streams and their citations, is preserved verbatim
in REWARD-MODEL-extraction-log.txt alongside. -->

# Reward Model of Record — Logos Blockchain

> **Substrate note (2026-08-24).** This extraction records the burn/mint substrate of its
> source tree. Lips **PR 375** (`block-rewards.md` 1.1.0, merged 2026-08-26) replaces it with
> pooling/distributing/releasing: fees route in full into a pending rewards pool, rewards
> distribute from it topped up by a metered release from a finite genesis reserve
> (`B_0 = 10⁹ LGO`), the recycled term becomes the windowed average over `T = 120` blocks,
> and `S_tge` is removed for `S_cap` (numerically identical). The extraction below remains
> the record of what it read; the differences are implemented and gated in `emission.py` and
> recorded as contradictions **4.12** (the PR's own real/integer divergence) and **4.13**
> (the `pow_share` diversion re-founded as the pool's first outflow, decided 2026-08-24).
> No number this simulator publishes moves under the new substrate; the settled blend pool
> is pinned by a gate to the LGO.

**Source tree:** `/Users/x/Logos/logos-lips/.claude/worktrees/Bedrock-RFC-EmPoWering/docs/blockchain/raw/`
All citations below are `file:line` relative to that directory. This document folds in the independent verification of each extraction: invented elements have been removed, wrong citations corrected, missed elements added. Where a verification found an extraction claim to be arithmetically wrong, the corrected number is used and the error is not repeated.

**Status vocabulary.** SPECIFIED = a value in a Standards Track document's normative text or constant table. ILLUSTRATIVE = a number appearing only in an Informational analysis, an example, or a simulation assumption. UNSET = the specification names the quantity but gives no value anywhere.

---

## 1. The reward streams

There are four token flows. Three pay participants; the fourth (emission) is the source of two of them.

```
fees collected by a block
   ├── 10/100 diverted BEFORE the burn ─────────────► PoW reward pool ──► PoW claims
   └── remainder burnt = D_1,t = R_block
                │
                ▼
        block reward Rewards_t = A_t·(I_max·S_tge·Δ_t/f)  +  (1−A_t)·R_block
                │                    └ newly minted ┘        └ re-mint of burnt ┘
                ├── 60% ──► Blend service pool ──► service rewards (flat per active node)
                └── 40% ──► leader pool ─────────► leader claims (flat per voucher)
                            + 100% of execution tips
```

---

### 1.1 Proof-of-work claims (`CLAIM_POW_REWARD`)

The only stream that is not funded by emission and does not mint. A claim moves tokens that already exist in a pool into circulation (`bedrock-v1.1-mantle-specification.md:1578`).

#### Formula — per-claim reward, exact integer arithmetic

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

Denominator is the compile-time constant `200 × 10 × 21600 = 43,200,000`. So σ_e = ⌊pool / 43,200,000⌋, **one** flooring site. The residue is not lost: *"what the flooring withholds is not lost: it simply remains in the pool, to be counted again at the next boundary"* (`:1791`).

#### Formula — pool refill, exact integer arithmetic

`overview-cryptoeconomics.md:180-184`:

```python
def get_pow_pool_refill(e: epoch):
    refill = 0
    for b in e.blocks:
        refill += get_collected_fees(b) * POW_SHARE // SHARE_DEN
    return refill
```

Flooring is **per block**: Σ_b ⌊fees_b · 10 / 100⌋, not ⌊Σ_b fees_b · 10 / 100⌋. The sub-lepton residue of each flooring *"stays with the remainder and is burnt"* (`overview-cryptoeconomics.md:187`). The diverted share is taken from the fee burn, never minted (`bedrock-v1.1-mantle-specification.md:1814`).

Boundary order, `:1805-1812` — refill **then** recompute:

```python
def on_epoch_boundary(epoch_blocks: list[Block]):
    pow_reward_pool = checked_uint64(pow_reward_pool + get_pow_pool_refill(epoch_blocks))
    epoch_pow_reward = compute_epoch_pow_reward(pow_reward_pool)
```

#### Formula — reward difficulty retarget, every block, exact integer arithmetic

`bedrock-v1.1-mantle-specification.md:1866-1884`:

```python
demand = max(1, (EMA_SMOOTHING_PRECISION - EMA_SMOOTHING_FACTOR) * claims_in_block
                + EMA_SMOOTHING_FACTOR * TARGET_CLAIMS_PER_BLOCK)
new_target = (TARGET_CLAIMS_PER_BLOCK * current_target
              * EMA_SMOOTHING_PRECISION) // demand
return min(new_target, p - 1)
```

At the specified constants this reduces to `new_target = ⌊100 · current_target / (claims_in_block + 90)⌋`. The `max(1, …)` is dead code at F=9, P=10, T=10 — it binds only if the constants change. Arithmetic is **arbitrary-precision, not `checked_uint64`** (`:135`; intermediate reaches ~2^261). Fixed point at 10 claims. At zero claims the target multiplies by 10/9 per block. Controller invariant, stated at `:1899`: *"the estimate equals `TARGET_CLAIMS_PER_BLOCK` divided by the current target."*

#### Eligibility gate

No stake, no declaration, no prior tokens. The Operation carries no signature and no ZK proof — *"the authorisation is the puzzle solution itself"* (`:1640`). Ticket:

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
4. `claim.epoch_nonce == get_current_epoch_nonce()` (the Cryptarchia η)
5. `puzzle_ticket < difficulty_reward` (smaller target is harder, `:1576`)
6. `puzzle_ticket not in pow_nullifiers` — **the nullifier is the ticket itself** (`:1686`)

Conditions 1 and 2 are evaluated per claim against the pool as preceding Operations left it, including within a single transaction (`:217`, `:1826`). A claim failing only on the pool guard invalidates its whole transaction.

#### Timing and lags

- **Per claim:** immediate. Output note of value `epoch_pow_reward`; `pow_reward_pool -= epoch_pow_reward`, exact, no flooring.
- **Per block:** difficulty retarget with a **one-block lag** — *"Every claim in a block is validated against the target produced by the previous block's update; the update from a block's own accepted count is applied after the block is processed and governs the next block"* (`:1887`). The controller observes claims **included in blocks**, not solutions found (`:1893`).
- **Per epoch:** refill lags one full epoch (fees of epoch e−1 fund epoch e). σ_e is then **frozen for the whole epoch** even as the pool it is paid from shrinks (`:1820`). Freezing is what makes the self-funding claim transaction possible — the reward note's id is computable in advance (`:1768-1770`).
- **Epoch nonce coupling:** a solution dies at the epoch boundary and must be re-mined (`:1694`); but the nonce is public part way through the *preceding* epoch, so solutions for epoch N can be ground during N−1 (`:1696`).
- **Acceptance window:** `WINDOW = ⌊W_b/f⌋ = 300 slots` at W_b=10, f=1/30 (`:1597`, `:1600`).

#### The claim's own fee

No special rule: *"This Operation performs no fee or balance check of its own"* (`:1690`). Canonical self-funding transaction is `CLAIM_POW_REWARD + TRANSFER`, execution gas 56 + 590 = 646 (`:2255`, `:2245`, `analysis-gas-cost-determination.md:248`). The transaction's encoded byte size — the other half of its fee — is **UNSET**, and worse: `mantle-transaction-encoding.md:65-74` does not define a `ClaimPowReward` payload at all, so the size is not even derivable from field widths.

---

### 1.2 Leader rewards

#### Formula — the split

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

#### Formula — what an individual leader receives

`bedrock-anonymous-leaders-reward.md:93-98`:

$$
share = \begin{cases} 0 & \text{if } |voucher\_cm| = |voucher\_nf| \\ \left\lfloor\dfrac{leader\_rewards}{|voucher\_cm| - |voucher\_nf|}\right\rfloor & \text{otherwise}\end{cases}
$$

Integer division over `TokenValue`. The denominator is the **cumulative** count of vouchers admitted since genesis minus nullifiers spent (`overview-cryptoeconomics.md:63`). No-overdraw invariant, `bedrock-anonymous-leaders-reward.md:100`: *"Rounding down guarantees that share × (|voucher_cm| − |voucher_nf|) ≤ leader_rewards, an inequality that every claim preserves since it decreases both sides by one share and one voucher respectively."* Residue: `:102` *"the remainder stays in `leader_rewards` until it is claimed or aggregated with the rewards of the next epoch."* Writing `leader_rewards = q·n + r`, the first n−r claimants get q and the last r get q+1.

**A leader's payment is not a function of the block it proposed** (`:87`). It is `⌊pool / unclaimed⌋` at claim time.

#### Formula — the lottery

`cryptarchia-proof-of-leadership.md:180-184`. Win iff `ticket < t` where

- `ticket = Poseidon2(LEAD_V1 || η || sl || noteID || sk)`
- `t = v · (t_0 + t_1 · v)`, v = the note's value

with (`:210-212`, `:219-223`, `:233-248`):

```
t_0 = t_0_constant // inferred_total_stake
t_1 = p - (t_1_constant // inferred_total_stake**2)
t_0_constant = 0x1a3fb997fd5838f2a1585ee090a95c88129ab25cc4d2e2d28f1a95f81d85465
t_1_constant = 0x71e790b4199113a9a00298d823c5716ddac764a110a45fe3b770bbb3e8a57
p            = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001
```

This is the 2nd-order Taylor expansion of φ_f(α) = 1 − (1−f)^α. **The leading coefficient is −ln(1−f) = 0.033901, not f = 0.033333** — a 1.7% difference in block rate. `t_1` is stored as `p − |t_1|`, so the real-valued threshold is `v·t_0 − v²·|t_1|`, a downward-opening parabola (`:296`). Pathological regime at v ≫ D: threshold peaks near 29D, crosses zero near 58D, then wraps in F_p and *"The note wins nearly every slot"*; spec says *"No circuit-level mitigation is strictly necessary"* (`:315`).

#### Eligibility gate

1. **Note aging.** Unspent **and** a member of the note set at the start of the *previous* epoch (`cryptarchia-v1-protocol.md:160`, `:208-212`). Enforced as dual Merkle membership in `ledger_AGED` and `ledger_LATEST` (`cryptarchia-proof-of-leadership.md:145-149`). *(DERIVED: effective minimum age is one full epoch, maximum two.)*
2. **Win the lottery** in a slot.
3. **No minimum stake.** Affirmatively stated, not an omission: *"Blend nodes must stake a minimum amount while leaders have no such requirement"* (`overview-cryptoeconomics.md:149`). The SDP min stake governs service declaration only.
4. **Produce a valid block**, sign it with a single-use Ed25519 key bound to the PoL (`cryptarchia-proof-of-leadership.md:189-193`), and embed one fresh 32-byte `leader_voucher` commitment in the header (`bedrock-v1.1-block-construction.md:122`).
5. **Claim** against the voucher root frozen at the start of the current epoch, with an unused nullifier (`bedrock-v1.1-mantle-specification.md:1497-1501`).

#### Timing and lags

- **Per slot:** one lottery per note. `f = 1/30`; *"For each slot, we can have 0 or more winners"* (`cryptarchia-v1-protocol.md:232`) — simultaneous winners are guaranteed forks.
- **Per block:** nothing is paid. A voucher commitment is placed in the header and sits outside the tree.
- **Epoch boundary (first block of e+1):** two things happen — the voucher is appended to the tree (`bedrock-anonymous-leaders-reward.md:72`; `bedrock-v1.1-block-construction.md:241`), and the pool is credited with epoch e's 40% + tips (`bedrock-anonymous-leaders-reward.md:91`).
- **Lag:** a block in epoch e becomes claimable at the start of e+1. Bounds: one block to one full epoch (7.5 days). *(DERIVED: mean ≈ 3.75 days.)*
- **Claim time:** chosen by the leader. Share recomputed at execution, **not** frozen at the epoch boundary — contrast the PoW pool, which explicitly is frozen (`:1820`). Claim costs `EXECUTION_LEADER_CLAIM_GAS = 580` (`:2254`).
- **No expiry.** Vouchers remain claimable indefinitely. The spec demonstrably knew how to write an expiry — the PoW path has an explicit Window of Acceptance (`:1580-1585`) — and did not write one here.

---

### 1.3 Service rewards (Service Declaration Protocol + Service Reward Distribution Protocol)

Only one service type exists: `ServiceType.BN`, the Blend Network (`bedrock-service-declaration-protocol.md:79-84`; *"Any declaration that is not one of the above must be rejected"*).

#### Formula — the framework delegates

`bedrock-service-reward-distribution.md:70-76`: `Rewards^n := serviceReward(n, Rewards_Epoch)`, where `Rewards_Epoch` is *"the total rewards of epoch N"* and the linked reference *"calculates how much each service receives."* **`I` (the Blend service's income) = 0.6 × `Rewards_Epoch`, not `Rewards_Epoch` itself.**

#### Formula — the per-provider split

`blend-protocol.md:1106-1126`:

$$B = \sum_{i=1}^{N}\mathrm{true}(\pi_A^{i,t,e}) \qquad P = \sum_{i=1}^{N}\min_{\Delta_{\mathcal H}}(\mathrm{true}(\pi_A^{i,t,e}))$$
$$R = \frac{I}{B+P} \qquad R(n) = R \cdot [\mathrm{true}(\pi_A^{i,t,e}) + \min_{\Delta_{\mathcal H}}(\mathrm{true}(\pi_A^{i,t,e}))]$$

Base reward to every provider with a true proof; **doubled** for those at the minimal Hamming distance. *(DERIVED: Σ R(n) = R·(B+P) = I exactly, so the stream distributes its full 60% share whenever B ≥ 1.)*

**No integer/rounding rule is given** for R — in contrast to the leader pool and the PoW pool, both of which are explicit about flooring and residue. This is a determinism gap in a protocol that requires identical execution on every node (`bedrock-service-reward-distribution.md:87`).

#### Formula — the activity lottery

`blend-protocol.md:1026-1036`: a proof is `true` iff Proof of Quota holds, Proof of Selection holds, and

$$\Delta_{\mathcal H}(H(t)_\epsilon, H(R_{e+1})_\epsilon) < \mathcal{A}_\epsilon$$

with (`:1070-1080`) `A_ε = χ − ν − θ`, `ν = ⌈log₂(N+1)⌉`, `χ = ⌈log₂(Q_C^Total + 1)⌉`, `θ = 1`, and `ε = ⌈log₂(Q_C^Total+1)/8⌉ · 8` (`:1044`). N is the core-node set returned by SDP (`:468-469`).

#### Eligibility gate — seven conditions, in order

1. **Network-size gate (whole service).** Fewer than 32 unique ProviderIds ⇒ *"Rewards are not calculated"* at all (`:1110`, `:150`). And the service itself shuts down: *"If the minimal network size is not reached, nodes must not use the Blend protocol… nodes must broadcast data messages directly, bypassing the Blend network"* (`:158`).
2. **Declaration visible in the epoch's SDP snapshot**, taken at the last block of `current_epoch − 2` (`bedrock-service-declaration-protocol.md:63`, `:127-130`). Epochs 0 and 1 read the genesis snapshot.
3. **Exactly one `SDP_ACTIVE` transaction** for epoch e, submitted during epoch e+1 after the 30-round transition period. Late ⇒ no reward at all (`blend-protocol.md:1104`, `:1135-1137`).
4. **Valid Activity Proof** in metadata, signed by `zk_id`, monotone nonce.
5. **The proof must win the Hamming lottery.** A provider that did the work and was unlucky earns nothing.
6. **Minimal Hamming distance** for the 2× premium.
7. **Not inactive** (2 epochs without an Active message) and not past `withdraw_at`.

**Stake dependence: none.** The formula contains no stake term. Stake is a binary admission gate, `assert note.value >= min_stake.stake_threshold` (`bedrock-v1.1-mantle-specification.md:1119`). Staking more buys nothing.

#### Timing and lags

Epoch N work → Active message in N+1 → computation at end of N+1 → payout in the **first block of N+2**, inserted directly into the ledger with no Mantle validation, `op_id = hash(ServiceType || epoch_number)`, outputs ordered by ascending `zk_id` (`bedrock-service-reward-distribution.md:80-87`). Work-to-payment lag: **2 epochs = 15 days**. *(DERIVED: total exposure from declaring to first possible reward is up to 4 epochs ≈ 30 days.)*

SDP Epoch Finalization runs in the same first block of N+2, **after** the payout, removing declarations with `withdraw_at <= current_epoch − 2` (`bedrock-v1.1-mantle-specification.md:1342-1384`).

---

### 1.4 The emission that funds leader and service rewards

#### Formula — total minted per block, equation (1)

`block-rewards.md:193-206`:

$$A_t \cdot \frac{I_{max} \cdot S_{tge} \cdot \Delta_t}{f} + (1-A_t) \cdot R_{block}, \qquad R_{block} = D_{1,t}$$

**Only the first term is new tokens.** The second is a re-mint of what the block just burnt: *"if far from the target, the system mints new tokens; if close to the target, the system mints exactly what was burned (up to I_max of TGE)"* (`:176-181`).

Supply evolution, `analysis-block-rewards.md:69-83` — the only statement in the tree of how minted rewards accumulate:

$$S_t = \min\{S_{cap},\ S_{tge}\times(1 + \textstyle\sum_{\tau=1}^t A_\tau \cdot I_{max}\cdot\Delta_\tau)\}$$

*"It is assumed here that S_{t−1} already accounts for the burned tokens. This equation implies that the supply evolution does not compound over time."*

#### Formula — the control function

`block-rewards.md:228-232`:

$$A_t = \min\{1, \max\{0, \tfrac{\alpha_d\delta_t + \alpha_a\gamma_t + I_{min}}{I_{max}}\}\}$$

$$\delta_t = \sum_i w_i\frac{D_{i,target}-D_{i,t}}{D_{i,target}} \qquad \gamma_t = \frac{1}{\Delta_t}\sum_i w_i\Bigl(\frac{1}{T}\sum_{\tau=t-T+1}^{t}\frac{D_{i,\tau}}{D_{i,target}}\Bigr)$$

Partitioned by KPI: *"To measure the deviation, only the total estimated stake KPI is used"* (`:298`); *"To measure the average, only the average burning rate KPI is used"* (`:338`). So δ_t reads KPI 0 only, γ_t reads KPI 1 only, each with weight 1.

#### Formula — the normative integer form

Because block rewards affect consensus state, *"the consensus rule itself should be defined only in terms of integer arithmetic"* (`:378`). Substituting α_d=1/4, α_a=1, I_max=10⁻², T=120, f=1, D_0,target=3e9, D_1,target=S_tge=1e10, Δ_t=1/(365·2880) gives `:443-451`:

$$A_t' = \min\{12\cdot10^7,\ \max\{0,\ 3\cdot10^9 - D_{0,t} + 10512\textstyle\sum_{\tau=t-119}^{t}D_{1,\tau}\}\},\quad A_t = \frac{A_t'}{12\cdot10^7}$$

with `I_max·S_tge·Δ_t/f = 10⁸/1051200 = 62500/657` LGO per block (`:462-464`), and `:468-473`:

$$\text{Rewards}_t = \frac{62500\cdot A_t' + 657\cdot(12\cdot10^7 - A_t')\cdot D_{1,t}}{657\cdot 12\cdot 10^7}$$

Reference implementation, `:477-501` — reproduced as written, defects and all:

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

#### Formula — the stake KPI D and its inference

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

*(DERIVED: at the specified β = 1.0 this collapses to a pure ratio update, D^ep = D^{ep−1} · N_BLOCKS^{ep−1} / (PERIOD · f).)*

**The estimator is biased and the spec says so.** `analysis-total-stake-inference.md:71-83`: it converges not to true stake but to `E[D_inf] = (log(1−f)/log(1−f/q)) · D_TRUE`, where q is honest slot utilization; *"increased network delay, which reduces the honest slot utilization rate through wasted blocks results in a systematic underestimate of true total stake."* At f=1/30, q=0.85 the factor is ≈ 0.847. A persistent ~15% underestimate of stake is a persistent positive δ_t, i.e. persistent extra emission. Convergence: steady state after 5 epochs (`:97`), recovery from massive shocks within 2 epochs (`:204`).

#### Eligibility gate

**None.** A_t is a pure function of chain state, evaluated every block, clamped to [0,1] on both sides. There is no minimum stake, no activity threshold, no gate of any kind in the emission-rate-factor function.

#### Timing and lags

- **Per block:** equation (1) evaluated once. Δ_t and f=1 are chosen so one time step = one 30-second block. Max newly minted = 62500/657 LGO, *"rounded down where an integer is required, losing less than one lepton per block"* (`bedrock-v1.1-mantle-specification.md:2123`).
- **Burn KPI: no lag.** γ_t reads τ = t−119 … t, **including the current block** (`:305`, `:438`; `last_burned_fee = burned_fees_window[-1]`). One hour of look-back.
- **Stake KPI: substantial lag.** D^ep is inferred from the block count in the **first 6⌊k/f⌋ slots of epoch ep−1** (`cryptarchia-v1-protocol.md:224-226`) and is *"the stake relativization constant for the following epoch"* (`:156`). *(DERIVED: the observation window closes 259,200 slots = 3 days = **0.4 epochs** before D takes effect; the oldest observed block is 648,000 slots = 7.5 days = **1.0 epoch** before. Mean dead time **0.7 epochs = 5.25 days**.)*
- **Payout:** 60% aggregated at the Blend epoch boundary, allocated on Active messages during e+2; 40% credited to the leader pool at the start of e+1.

---

## 2. Parameter table

### 2.1 SPECIFIED — emission / block reward

| Symbol | Value | Citation |
|---|---|---|
| S_tge | 10 billion LGO (1e10) | `block-rewards.md:160` |
| I_max | 1% / yr (0.01) | `block-rewards.md:167` |
| I_min | 0% | `block-rewards.md:168` |
| α_a | 1 | `block-rewards.md:162` |
| **α_d** | **1/4** — *contested, see §4.2* | `block-rewards.md:163`, `:389` |
| T (look-back) | 120 blocks (1 hour) | `block-rewards.md:161` |
| w_i | 1 (constraint Σw_i = 1) | `block-rewards.md:164`, `:143` |
| D_0,target | 3 billion LGO (30% of S_tge) | `block-rewards.md:165` |
| D_1,target | 10 billion LGO (a normalizer) | `block-rewards.md:166` |
| Δ_t | 1/(365·2880) | `block-rewards.md:170` |
| f (block-rewards) | 1 — **not** the Cryptarchia f | `block-rewards.md:169` |
| A_SCALE | 120,000,000 | `block-rewards.md:478` |
| INFLATION_NUMERATOR | 62,500 | `block-rewards.md:479` |
| INFLATION_DENOMINATOR | 657 | `block-rewards.md:480` |
| FEE_AVG_NUMERATOR | 10,512 | `block-rewards.md:481` |
| STAKE_TARGET | 3e9 | `block-rewards.md:482` |
| Blend share | 60% (`*6 // (den*10)`) | `overview-cryptoeconomics.md:145`; `block-rewards.md:497` |
| Leader share | 40% (`*4 // (den*10)`) | `overview-cryptoeconomics.md:144`; `block-rewards.md:498` |

### 2.2 SPECIFIED — consensus / timing

| Symbol | Value | Citation |
|---|---|---|
| f (Cryptarchia) | 1/30 | `cryptarchia-v1-protocol.md:94` |
| k | 2160 | `cryptarchia-v1-protocol.md:95` |
| slot length | 1 s | `cryptarchia-v1-protocol.md:96` |
| MAX_BLOCK_SIZE | 1 MB (`overview:115` says 1 MiB) | `cryptarchia-v1-protocol.md:97` |
| MAX_BLOCK_TXS | 1024 | `cryptarchia-v1-protocol.md:98` |
| s | 3⌊k/f⌋ | `cryptarchia-v1-protocol.md:104` |
| EPOCH_LENGTH | 10⌊k/f⌋ slots *(= 648,000 s = 7.5 d, derived)* | `cryptarchia-v1-protocol.md:144`; `block-rewards.md:136` |
| EXPECTED_BLOCKS_PER_EPOCH | 21,600 (= 10k) | `cryptarchia-v1-protocol.md:146`; `mantle:1780` |
| β (stake inference) | 1.0 | `cryptarchia-total-stake-inference.md:49` |
| PERIOD | 6⌊k/f⌋ *(= 388,800 slots, derived)* | `cryptarchia-total-stake-inference.md:50` |
| PRECISION | 1e3 | `cryptarchia-total-stake-inference.md:64` |
| **D_GENESIS** | **rule, not numeral:** *"the total tokens distributed at genesis"* | `bedrock-genesis-block.md:317` |
| p (BN254 scalar field) | 0x30644e72…f0000001 | `cryptarchia-proof-of-leadership.md:219` |
| t_0_constant, t_1_constant | see §1.2 | `cryptarchia-proof-of-leadership.md:220-221` |

### 2.3 SPECIFIED — leader stream

| Symbol | Value | Citation |
|---|---|---|
| voucher Merkle depth | 32 | `bedrock-anonymous-leaders-reward.md:123` |
| vouchers per block | exactly 1, 32 bytes | `bedrock-v1.1-block-construction.md:122` |
| genesis leader voucher | 0 / `bytes(32)` | `bedrock-genesis-block.md:201`, `:215` |
| LEADER_CLAIM opcode | 0x30 | `mantle:258` |
| EXECUTION_LEADER_CLAIM_GAS | 580 | `mantle:2254` |
| minimum stake for leadership | **none** (affirmative) | `overview-cryptoeconomics.md:149`, `:152` |

### 2.4 SPECIFIED — service stream

| Symbol | Value | Citation |
|---|---|---|
| Minimal Network Size | 32 unique ProviderIds | `blend-protocol.md:150` |
| θ (activity threshold) | 1 | `blend-protocol.md:1080` |
| β_C | 3 | `blend-protocol.md:477` |
| E (rounds/epoch) | 648,000 | `blend-protocol.md:475` |
| transition period | 30 rounds | `blend-protocol.md:570` |
| premium multiplier | 2× | `blend-protocol.md:1124-1126` |
| ServiceType set | `BN` only | `bedrock-service-declaration-protocol.md:79-84` |
| inactivity_period (BN) | 2 epochs | `bedrock-service-declaration-protocol.md:360-364` |
| SDP snapshot | `current_epoch − 2` | `bedrock-service-declaration-protocol.md:63` |
| max locators / declaration | 8 (≥1), each ≤ 329 chars | `bedrock-service-declaration-protocol.md:164`, `:145` |
| EXECUTION_SDP_ACTIVE_GAS | 590 | `mantle:2253` |
| provider cap | **none** | `analysis-static-minimum-stake…:111` |

### 2.5 SPECIFIED — PoW stream

| Symbol | Value | Citation |
|---|---|---|
| POW_SHARE / SHARE_DEN | 10 / 100 | `mantle:1806-1807` |
| EPOCH_POW_DISTRIBUTION_RATE_NUM / _DEN | 1 / 200 | `mantle:1777-1778`, `:1836` |
| TARGET_CLAIMS_PER_BLOCK | 10 | `mantle:1779` |
| EXPECTED_BLOCKS_PER_WINDOW | 10 | `mantle:1585` |
| WINDOW | ⌊W_b/f⌋ = **300 slots** (prose only, never assigned) | `mantle:1597`, `:1600` |
| EMA_SMOOTHING_FACTOR / PRECISION | 9 / 10 | `mantle:1867-1868` |
| difficulty_reward at genesis | p ÷ 2²⁶ (prose; rounding direction not stated) | `mantle:1901` |
| POW_REWARD_POOL_GENESIS | 5/1000 of launch supply — **fraction, deliberately not a numeral** | `bedrock-genesis-block.md:76-80`; `mantle:1856` |
| EXECUTION_CLAIM_POW_REWARD_GAS | 56 | `mantle:2255` |
| EXECUTION_TRANSFER_GAS | 590 | `mantle:2245` |
| CLAIM_POW_REWARD opcode | 0x40 | `mantle:260` |

### 2.6 SPECIFIED — fee markets and units

| Symbol | Value | Citation |
|---|---|---|
| lepton | 1 LGO = 1e9 lepta; supply 1e19 lepta | `mantle:2119`, `:2121` |
| **b_exec[0]** | **1** (initialized at 1 for the first block) | `execution-market.md:95` |
| G_max | 3,193,460 | `execution-market.md:99` |
| G_target | 1,596,730 | `execution-market.md:100` |
| φ (fee adjustment rate) | 1/8 | `execution-market.md:101` |
| q (EMA smoothing) | 9/10 (≈19-block lookback) | `execution-market.md:102` |
| base fee rounding | **ceil**; effective floor 1 | `execution-market.md:206` |
| storage price rounding | **ceil**; floor 1 (see §4.8 on units) | `storage-markets.md:224` |
| T_RA(−1) at genesis | T_base | `storage-markets.md:231` |

### 2.7 ILLUSTRATIVE — do not configure a simulator from these

| Quantity | Value | Where it comes from |
|---|---|---|
| **α_d = 1/6** | conflicts with normative 1/4 | `analysis-block-reward-parameter-calibration.md:80` |
| α_d = α_a = 1, T = 0, S_tge = 1 LGO, S_cap = ∞, Δ_t = 1/365, f = 2880 | baseline simulation only | `analysis-block-rewards.md:88-97` |
| APY 20% → 3.33% as stake goes 5% → 30% | Table 1, computed as I_max/SecurityLevel | `analysis-block-rewards.md:143` |
| min stake = 0.001% × S_TGE (bound 0.015%) → 1,000 LGO | Informational; and under that doc's own S_TGE = 1e8 | `analysis-static-minimum-stake…:60`, `:116`, `:122` |
| r_stake = 15%, N_stakers = 1000 | inputs to that derivation | same, `:93`, `:97` |
| S_TGE = S_max = 100,000,000 LGO | that document's assumption, contradicts `block-rewards.md:160` | same, `:151-152` |
| inferred_total_stake = 23.5B "as in Cardano" | error-analysis assumption | `cryptarchia-proof-of-leadership.md:255` |
| q = 0.85 honest slot utilization | estimator-bias example | `analysis-total-stake-inference.md` |
| 6,664 lepta claim fee | stated at the markets' RESTING level of 7, giving 306 bytes and 646 gas | `mantle:1858` |
| ~3 hours/core per PoW solution; "a few thousand cores" for target rate | prose calibration, "target machine" undefined | `mantle:1903` |

### 2.8 UNSET — the simulator must supply a value

| Quantity | Why it matters | Where the gap is |
|---|---|---|
| **S_cap** | supply hard cap; introduced *"if any"*, never valued | `block-rewards.md:132` |
| **min_stake.stake_threshold** | admission gate for the entire service stream | `bedrock-service-declaration-protocol.md:88-96`; `mantle:1119` |
| **F_C, R_C** ⇒ Q_C^Total ⇒ χ ⇒ ε ⇒ A_ε | without these the *probability an honest provider is paid at all* is not computable | `blend-protocol.md:461`, `:466` |
| **P_STR(0)** | *"Set to a pre-determined value established by genesis governance"* | `storage-markets.md:231` |
| **genesis token distribution** | hence the numeric D_GENESIS | `bedrock-genesis-block.md:317` |
| **leaders_rewards at genesis** | no seed stated; only `pow_reward_pool` is seeded | absent from `mantle`, `bedrock-genesis-block.md:296-301` |
| **encoded byte size** of claim / leader-claim transactions | half of their fee; `ClaimPowReward` absent from the encoding spec entirely | `mantle-transaction-encoding.md:65-74` |
| **moving-average warm-up** | γ_t is undefined for t < 119 | `block-rewards.md:305` |
| **burned-fee window at genesis** | initial contents of `burned_fees_window` | — |
| **voucher claiming policy** | no expiry ⇒ the per-share value depends entirely on claimant behaviour | `bedrock-anonymous-leaders-reward.md:102` |
| **size semantics of P** | argmin set (typically 1) or top-k? | `blend-protocol.md:1116` vs `:277` |
| **residue of the 60/40 split** | the two floors do not sum to the total | `block-rewards.md:497-498` |
| **fate of Blend income when the gate fails or B = 0** | no `blend_reward_pool` state variable exists | absent from `mantle` |

---

## 3. What the specification does not determine

Ranked by how much a simulator's output moves with the assumption.

**1. The validator yield itself.** See §4.1. Two readings of the same parameter set differ by 2.5× in leader APY. Everything downstream — participation, the stake trajectory, hence D, hence A_t, hence emission — depends on which one is modelled.

**2. Voucher claiming policy.** No expiry, and the denominator counts every unclaimed voucher since genesis (`overview-cryptoeconomics.md:63`). The per-share value is therefore set entirely by an unmodelled behaviour. *(DERIVED: with a stationary backlog it tends to (0.4·Σ block rewards + Σ tips)/21,600 per epoch; if leaders delay, the backlog grows and the per-share value falls below this while total value per leader is preserved.)* The only hint is a soft one: *"The marginally larger reward of the late claimants also mildly encourages leaders to spread their claims over time"* (`bedrock-anonymous-leaders-reward.md:102`).

**3. The activity-lottery acceptance rate.** With F_C and R_C unset, the fraction B/N of honest providers that get paid is a free parameter. Since R = I/(B+P), this directly scales every provider's income. There is no stated target acceptance rate.

**4. The minimum stake.** Unset in normative text. It is the sole Sybil defence for a reward that is **flat per declaration** — *(DERIVED: splitting stake across many threshold-meeting declarations multiplies the reward, since uniqueness is enforced only per (service, provider_id) and per (service, zk_id), and there is no provider cap.)* A simulator's answer to "how many Blend providers are there" is essentially the answer to "how low is the threshold."

**5. The fee process.** D_1,t drives (1−A_t)·R_block, which is the *whole* block reward once the stake target is reached. `execution-market.md:222-229` gives R̂_burned(s) = Σ g_t·b_exec[s] and the base-fee dynamics, but transaction demand — g_t and the arrival process — is exogenous. In the mature regime the entire reward system is a function of an unspecified input.

**6. Whether supply increases at block time or epoch time.** `block-rewards.md` speaks of amounts minted *per block*; `overview-cryptoeconomics.md:154-172` credits the pools only at the epoch boundary. A supply-tracking simulator must choose.

**7. Genesis initial conditions.** D_GENESIS is a rule without a numeral; `leaders_rewards` has no stated seed; the burned-fee window has no stated initial contents; the moving average has no warm-up rule.

**8. Reorg semantics.** Nothing states how A_t is carried across a reorganisation, whether the burned-fee window follows the chain or the node's local view, or whether vouchers from orphaned blocks enter the anonymity set. Relevant because the spec itself says simultaneous lottery winners produce guaranteed forks (`cryptarchia-v1-protocol.md:232`).

**9. Whether the PoW diversion is inside or outside D_1,t.** Stated only as prose in one document (`overview-cryptoeconomics.md:195`). `block-rewards.md` contains no mention of proof of work at all.

**10. Hashrate → solution rate.** Only prose calibration; the "target machine" is undefined. PoW claim volume, and therefore the difficulty controller's trajectory, is a free input.

**11. Determinism gaps in the service payout.** No rounding rule for R; no rule for the residue of I mod (B+P); no rule for the 60/40 flooring residue.

**12. Multi-service apportionment.** `serviceReward` and `Rewards_Epoch` are written for N services; only one exists and only one split is specified.

---

## 4. Contradictions between documents

Stated as contradictions. Not reconciled.

### 4.1 The APY contradiction — *the load-bearing one*

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
| Blend payment basis | — | **flat per active node**, not per stake — so it is not a yield on capital at all; it is a per-node fee gated by a minimum stake |
| I_max that would deliver 3.33% to leaders | 1% | **2.5%** |

Consequence for a simulator: under Reading B the parameter that was chosen to hit 3.33% delivers 1.33%, and the participation incentive that the whole stake-KPI control loop is built around is 2.5× weaker than the calibration assumed. The stake trajectory, hence D, hence δ_t, hence A_t, hence emission — the entire loop — sits on this.

There is also a **third inconsistency inside Reading A itself.** At D_0,t = D_0,target we have δ_t = 0, so A_t = α_a·γ_t/I_max — driven purely by the burn. If the annualized burn rate is below 1% of S_tge, A_t < 1 and the minted emission is *less* than 1e8 LGO; at zero burn A_t = 0 and minted emission is zero, with the block reward reduced to a pure recycling of that block's burnt fees. The "3.33% APY at the target" figure is computed as if A_t were still 1 at the target, which the control function contradicts. The APY table is valid strictly *below* target and discontinuous with the mechanism *at* it. `analysis-block-rewards.md:137` half-concedes this — *"this section only evaluates the APY within the range [0, D_0,target]"* — but `block-rewards.md:167` states the 3.33% as holding *when* the target is reached.

### 4.2 α_d: 1/4 versus 1/6

`block-rewards.md:163` and `:389` specify **1/4**, and cite `analysis-block-reward-parameter-calibration.md` as the justification. That document, at `:80`, says: *"The value α_d = 1/6 is chosen so that when the total inferred stake is off target by 16.6%… the system starts moving from the maximum inflationary regime to the regime driven by the burned fees."*

The normative integer form is built on 1/4: adopting 1/6 changes `A_SCALE` from 12e7 to 18e7 and the transition band from 4% to 6% of the target.

**Neither value reproduces the stated rationale.** A_t leaves saturation at δ_t = I_max/α_d, which is **4%** at α_d = 1/4 and **6%** at α_d = 1/6 — not the 16.6% claimed. The likely root cause is a units disagreement: `analysis-block-reward-parameter-calibration.md:43` says *"δ_t is measured in percentage units"*, while `block-rewards.md:265-268` defines δ_t as a dimensionless ratio and `:412-424` substitutes it as a raw fraction. Under the percentage reading A_t would be saturated essentially always, so the fraction reading is the only workable one — and the 16.6% figure fits neither.

### 4.3 D at genesis versus the bootstrap narrative

`bedrock-genesis-block.md:317`: *"D: The initial estimate of total stake will be the total tokens distributed at genesis."* That is on the order of the full launch supply, ~1e10 LGO — **more than 3× above** D_0,target = 3e9.

`block-rewards.md:357`: *"when the blockchain starts, D_{0,t}|_{t=0} is very likely a small number compared to the target. Therefore, the equation above tilts towards 1."*

Under the genesis rule, δ_t at genesis ≈ −2.33, A_t clamps to **0**, and the chain opens in the pure fee-recycling regime — the exact opposite of the bootstrap story, and the opposite of the entire APY-attracts-validators argument in `analysis-block-rewards.md:155-160`. A simulator that seeds D low will reproduce the intended curve for the wrong reason.

### 4.4 Service payout lag: e+2 versus e−1

Three statements say the epoch-N reward is paid in the first block of epoch **N+2**: `bedrock-service-reward-distribution.md:49`, `overview-cryptoeconomics.md:65`, `overview-cryptoeconomics.md:139`, plus `blend-protocol.md:1136`. One statement says one epoch: `overview-cryptoeconomics.md:228` — *"When a new service epoch e starts, rewards for the previous epoch e−1 are calculated and directly inserted in the ledger."* The dissent is internal to the Informational overview; the Standards Track SRDP says e+2.

### 4.5 Execution tips: 100% to leaders, or split 60/40?

`overview-cryptoeconomics.md:170-171` adds tips to `leader_rewards` **after and in addition to** the 40% share — leaders get all of them. `execution-market.md:62`: *"The priority_fee… is directed into the block builders reward stream. 40% of the rewards will be allocated to block builders and the remaining 60% to Blend nodes"* — which on one reading applies the split to tips as well, moving 60% of all tips to Blend.

### 4.6 Per-block integer split versus per-epoch float split

`block-rewards.md:497-498` floors each share **per block** on the reward numerator. `overview-cryptoeconomics.md:158-171` sums `0.6 * get_block_rewards(b)` and `0.4 * …` in real arithmetic over the epoch. Summing floored per-block shares ≠ flooring the summed share; over 21,600 blocks an epoch the divergence is up to ~21,600 units per pool. Neither document says which is normative.

Additionally, the two floors do not sum to the total: the shortfall against the exact rational total is strictly less than 2 units, i.e. at most 1 whole unit below ⌊total⌋. The spec is explicit about the residue for the leader pool (`bedrock-anonymous-leaders-reward.md:102`, stays in the pool) and for the PoW diversion (`overview-cryptoeconomics.md:187`, burnt) — and silent here.

### 4.7 Units: LGO or lepta?

`mantle:2119`: *"The indivisible unit is the lepton… `TokenValue` counts lepta: every quantity of that type — note values, balances, fees, prices and pool balances — is an integer number of lepta."* But `block-rewards.md`'s reference implementation works in **LGO**: `STAKE_TARGET = int(3e9)` is 3 billion *LGO* (`:165`), and 62500/657 is ~95 *LGO* per block (`mantle:2123` confirms it is LGO). A_t′ is dimensionful — it adds `3e9 − D_0,t` to `10512·Σ D_1,τ` and compares against 12e7 — so `total_stake` and `burned_fees_window` must be in the **same unit as the literal 3e9**. If those inputs arrive as `TokenValue` lepta, `STAKE_TARGET` must be 3e18 and `A_SCALE` 12e16. **No conversion rule is specified anywhere.** A simulator that feeds lepta into `block_reward()` unchanged is wrong by 10⁹.

### 4.8 The storage-price floor: 1 LGO or 1 lepton?

`storage-markets.md:224`: *"Rounding upwards makes 1 LGO per Permanent Storage Gas the effective floor of the price."* `mantle:2119`: *"both fee markets price in whole lepta per unit of gas and can never go below one."* A factor of 10⁹. The Mantle statement is the later and more explicit one, but the conflict is unresolved in the text.

### 4.9 S_TGE: 1e10 or 1e8?

`block-rewards.md:160` gives 10 billion LGO. `analysis-static-minimum-stake…:151-152` assumes `S_TGE = S_max = 100,000,000 LGO` (and its own `:75`/`:77` use 10 million / 1 million as examples). The derived minimum stake of 0.001% × S_TGE is therefore 1,000 LGO under the analysis and 100,000 LGO under `block-rewards.md`.

### 4.10 ServiceType naming

`bedrock-service-declaration-protocol.md:80-82` and `mantle:1016-1017` define `ServiceType.BN`. `bedrock-genesis-block.md:102`, `:258` construct declarations with `ServiceType.BLEND`. This is not cosmetic: the service payout `op_id` is `hash(ServiceType || epoch_number)`.

### 4.11 `p` is defined nowhere it is pointed to

`mantle:1634` refers the reader to *Common Cryptographic Components* for the scalar field modulus. `common-cryptographic-components.md:133` names BN254 but **states no modulus**. The only numeric value in the tree is `cryptarchia-proof-of-leadership.md:219`.

---

## 5. Implementation notes

### 5.1 Every flooring site, and what happens to the residue

| Site | Expression | Residue |
|---|---|---|
| PoW pool refill, **per block** | ⌊fees_b · 10 / 100⌋ | **burnt** (`overview:187`) |
| PoW per-claim reward, per epoch | ⌊pool · 1 / 43,200,000⌋ | **stays in the pool** (`mantle:1791`) |
| PoW difficulty retarget, per block | ⌊100·target / (c+90)⌋, **arbitrary precision** | n/a |
| PoW pool decrement | exact, no flooring | n/a |
| Block reward 60% split, per block | `num*6 // (den*10)` | **UNSPECIFIED** |
| Block reward 40% split, per block | `num*4 // (den*10)` | **UNSPECIFIED** |
| Leader per-voucher share, per claim | ⌊pool / unclaimed⌋ | **stays in `leader_rewards`** (`:102`) |
| Service reward R = I/(B+P) | **no rounding rule given** | **UNSPECIFIED** — determinism gap |
| Block reward → lepta | round down, <1 lepton/block (`mantle:2123`) | lost |
| Execution base fee update | **ceil**, floor 1 (`execution-market.md:206`) | — |
| Storage price update | **ceil**, floor 1 (`storage-markets.md:224`) | — |
| Storage usage EMA | **floor** — deliberately opposite to the price | — |

A_t itself is **never materialised as an integer.** The integer form keeps it as the exact rational A_t′/12e7 and rounds only at the final reward division. The spec never says this in words.

### 5.2 Which snapshot each value is read from

| Value | Read from |
|---|---|
| ℂ_LEAD (eligible notes) | commitment root at slot (ep−1)·EPOCH_LENGTH — *start of the previous epoch* |
| η (epoch nonce) | slot sl_{ep−1} + ⌊6k/f⌋ |
| D (inferred total stake) | block count in the **first 6⌊k/f⌋ slots of epoch ep−1**; in force for the whole of epoch ep |
| SDP provider set | last block of `current_epoch − 2` |
| voucher Merkle root for claims | **frozen** at the start of the current epoch (`mantle:1489`) |
| leader per-share amount | **recomputed at claim execution**, *not* frozen (`bedrock-anonymous-leaders-reward.md:91-98`) |
| `epoch_pow_reward` | **frozen** at the epoch boundary (`mantle:1820`) |
| `difficulty_reward` | produced by the **previous** block's update (`mantle:1887`) |
| burned-fee window γ_t | last 120 blocks **including the current one** |
| D_1,t for the recycling term | **the current block** — no lag |

### 5.3 What lags what

- **PoW pool refill:** one full epoch. Fees of e−1 fund the pool used in e.
- **PoW difficulty:** one block.
- **PoW solution validity:** dies at the epoch boundary; but can be pre-mined from the moment the next epoch's nonce is public, part way through the preceding epoch.
- **Leader pool credit:** at the start of e+1 for blocks of e. Lag from one block to one full epoch.
- **Service reward:** two epochs (15 days), work in N → Active in N+1 → paid first block of N+2.
- **Service declaration:** up to two epochs before the declaration is visible.
- **Stake KPI D:** 0.4 to 1.0 epochs of dead time (mean 0.7 epochs = 5.25 days) between observation and effect. Plus 5 epochs to steady state and 2 epochs to recover from a shock. This is the control loop's dominant dead time and it is not stated anywhere in the spec.
- **Burn KPI:** zero lag, 120-block moving average.

### 5.4 Where a naive reading goes wrong

- **The two symbols named `f` are different quantities.** `block-rewards.md:169` f = 1 (blocks per Δ_t); `cryptarchia-v1-protocol.md:94` f = 1/30 (slot activation coefficient). Neither document flags the collision. Confusing them misscales emission by 30×. Worse, block-rewards' f is not even single-valued: `:137-139` shows the same symbol taking 2880 and 21600 for other time steps.
- **`I` is not `Rewards_Epoch`.** `I = 0.6 × Rewards_Epoch`. Feeding the total epoch reward into R = I/(B+P) overstates the service stream by 1.67×.
- **The block reward's fee input is net of the PoW diversion.** Feed `0.9 × collected_fees` into `burned_fees_window`, not gross. Overstating it inflates the recycled term by ~11% in the mature regime. Stated only in prose, `overview-cryptoeconomics.md:195`; `block-rewards.md` never mentions PoW.
- **The leadership win probability's leading coefficient is −ln(1−f) = 0.033901, not f = 0.033333.** Seeding a simulator with f·v/D produces a block rate ~1.7% below what the specified t_0 delivers.
- **`t_1` is stored as p − |t_1|.** The real-valued threshold is v·t_0 − v²·|t_1|. A simulator that treats t_1 as positive gets the parabola upside-down and misses the v ≫ D wrap-around entirely.
- **The stake estimator is biased low by construction.** ≈0.847× true stake at f=1/30, q=0.85. This is a *permanent* positive δ_t and therefore permanent extra emission — an equilibrium property, not a transient.
- **The transaction-count limit binds first, and `MAX_BLOCK_TXS` is the operative cap.** *(WITHDRAWN, and reversed. An earlier revision inferred a ~6,018-byte claim transaction by decomposing the 6,664-lepta fee at a price of 1, and concluded that 1 MB capped a block at ~170 claims rather than at `MAX_BLOCK_TXS` = 1024. The decomposition is wrong on two counts. The fee is stated at the markets' RESTING level, which is 7 rather than 1 -- the downward step has fixed points across the first several units, so an idle market settles at 7 -- and 6,664 = (306 + 646) * 7 exactly. And 6,018 bytes is implausible on its face: `ClaimPowRewardOp` carries three 32-byte fields, so the Operation is 96 bytes and the envelope and signature bring the transaction to roughly 306. At 306 bytes 1 MB holds ~3,400 claims, so the count limit binds at 1024 and the spec's "impossible by construction" margin is exactly as claimed rather than larger.)*
- **The PoW `max(1, …)` in the retarget is dead code** at the specified constants. Do not treat it as a live branch.
- **The leader claim's effect differs between documents.** `bedrock-anonymous-leaders-reward.md:112` says *"Increase the balance of the Mantle Transaction by the share amount"* (a balance credit consumable by other Operations in the same transaction — this is what makes the atomic self-spend at `:85` work). `mantle:1519-1526` says construct a single output note and insert it into the Ledger. These differ for UTXO-count modelling.
- **The genesis voucher.** `bedrock-genesis-block.md:201` sets it to 0 *"as there is no leader block reward for the initial block"*, and `:290` says header processing is skipped for genesis — which resolves the question, since the voucher append at `bedrock-v1.1-block-construction.md:241` is part of block execution. Admitting a zero leaf would permanently inflate the denominator by 1 and strand one share forever.
- **Do not copy the reference implementations verbatim.** Known transcription defects: `block-rewards.md:222` (`R_block_cur` undefined; parameter is `D_1_t`); `:287` (`weight * deviation value`, syntax error); `:323` (asserts against `kpi_deviations`, not a parameter of that function); `:494` (`a_num` undefined, invalid line continuation); `:152` (states the per-step emission as `A_t·I_max·Δ_t`, omitting S_tge — contradicts `:185-187`). And `cryptarchia-total-stake-inference.md:63-83` will not compile: `const PRECISION: u64 = 1e3` assigns a float literal, and lines 77–78 mix u64 and i128 without casts. The arithmetic intent is unambiguous in every case.
- **`WINDOW`, `EPOCH_POW_DISTRIBUTION_RATE`, and `EPOCH_LENGTH` are not greppable constants.** `WINDOW` is defined only by a LaTeX relation and a prose value; `EPOCH_POW_DISTRIBUTION_RATE` exists only as `_NUM`/`_DEN`; `EPOCH_LENGTH` is prose in Cryptarchia and a symbol only in the epoch-state pseudocode.

### 5.5 Derived numbers a simulator can check itself against

- ⌊k/f⌋ = 64,800 slots. EPOCH_LENGTH = 648,000 slots = 7.5 days. 48.667 epochs/year. PERIOD = 388,800 slots; expected blocks in the observation window = 12,960.
- 62500/657 = 95.1294… LGO/block; × 1,051,200 blocks/yr = exactly 1e8 LGO/yr = 1% of S_tge.
- Emission saturation band in stake terms: A_t = 1 at D_0,t ≤ 2.88e9; A_t = 0 at D_0,t = 3.0e9 (holding γ_t = 0). Band width 1.2e8 LGO — numerically equal to `A_SCALE`, which is a useful consistency check that the integer form is in LGO.
- Burn-side saturation: Σ over the 120-block window of D_1,τ ≥ 12e7/10512 ≈ 11,415 LGO saturates A_t on its own, i.e. a sustained burn of 1e8 LGO/yr. Note this sits in tension with `analysis-block-reward-parameter-calibration.md:96`: *"As a consequence of the parametrization, specifically α_a = 1, the emission rate I_t never reaches the maximum value"* — true of that document's stochastic example, not of the mechanism.
- Service stream at A_t = 1, zero fees: 21,600 × 95.1294 × 0.6 ≈ **1,232,877 LGO/epoch ≈ 60.0 million LGO/yr = 0.6% of S_tge**. At the 32-provider floor with P = 1 and all active, ≈ 37,360 LGO per provider per epoch; at 1,000 providers, ≈ 1,232 LGO per provider per epoch.
- PoW: genesis pool = 0.005 × 1e19 = 5e16 lepta ⇒ opening reward ⌊5e16/43,200,000⌋ = **1,157,407,407 lepta ≈ 1.157 LGO**. Pool settles at 1/ρ = 200 epochs ≈ 4 years of distribution. At zero claims the target eases by 10/9 per block, so recovery from a 100×-too-hard target takes log(100)/log(10/9) ≈ 44 blocks ≈ 22 minutes — matching the spec's "corrects itself within an hour" (`mantle:1901`). The over-permissive direction is spec-stated: a hundredfold-too-easy genesis target costs ~1,200 extra claims over ~20 blocks, ~3×10⁻⁵ of the genesis pool.
- Claim transaction execution gas = 56 + 590 = 646. The stated 6,664-lepta fee decomposes as (306 + 646) * 7 at the markets' resting level, giving an encoded size of **306 bytes** -- consistent with a 96-byte `ClaimPowRewardOp` (three 32-byte fields) plus envelope and signature. The earlier reading, 6,018 bytes at a price of 1, is withdrawn: it is implausible against the stated payload and assumes the floor rather than the resting level. The 306 is now derived rather than asserted -- see `txsize.py`, which builds both sizes from the encoding document's primitives -- but with a caveat recorded there: **`CLAIM_POW_REWARD` does not appear in `mantle-transaction-encoding.md` at all**, neither in `OpPayload` nor in `OpProof`. It entered Mantle at revision 1.11.0 on 2026-08-11 and the encoding document has not been updated for it, so the framing is reconstructed. The reconstruction is pinned by the specification's own arithmetic: only it reproduces the 6,664 lepta of `mantle:1858`, where the strict reading of the encoding document gives 6,629. **Worth reporting upstream:** the encoding document needs a `ClaimPowReward` production and an `OpProof` variant for it.
- **The two gas markets are separate but rest at the same level.** Execution gas is charged per Operation, permanent storage gas on the encoded size of the whole signed transaction at one gas per byte (`mantle:71`, `mantle:148`), and each discovers its price independently. Both floor at one lepton and settle at 7, so `mantle:1858`'s 6,664-lepta claim fee is `(306 + 646) * 7`. `storage-markets.md:124-126` reads "1 LGO per Permanent Storage Gas", which is superseded: that document was last revised 2026-07-28, and *Logos Token: Units and Precision* (2026-08-11) -- which `mantle:2119` defers to by name -- tabulates `P_STR` in lepta per gas unit, floors it at one lepton, and computes a GiB of permanent storage at 1.0737 LOGOS. At 1 LGO per byte that GiB would cost 1.07 billion LOGOS and the 6,664-lepta figure would be unreproducible. See `CONTRADICTIONS.md` section 4.8, which records this resolution being reversed and reinstated.
- The `mantle:1858` "twice the fee" claim does not check out: it states the opening reward exceeds twice the claim's fee for fee ≤ 1.157×10⁻¹⁰ of launch supply, but 1.157×10⁻¹⁰ × 1e19 = 1.157e9 lepta, which *is* the opening reward, not half of it. Either the threshold is the one-times-fee threshold mislabelled, or a different reward is meant. Not reconciled here.
