import Mathlib

/-!
# Execution Gas

Mantle, Appendix *Gas Determination*, with the measurements of RFC-480 (Chores) and RFC-481
§6 and the Execution Gas limit of the Cryptoeconomics overview. One unit of Execution Gas is
`1,000` CPU cycles, and a cost in cycles is rounded up (`gasOfCycles`).

Every constant of the table is checked against the measurement it comes from:

* `transfer_gas_eq`: a ZkTransfer costs `618,797` cycles in the batch, so `619`;
* `program_spend_gas_eq`: a ZkProgramSpend costs `618,796` cycles in its batch, so `619`;
* `program_proof_gas_eq`: a program proof, `2,221,544 + 228,669` cycles, so `2,451`;
* `program_register_gas_eq`: the subgroup checks and `e(α, β)`, `573,324 + 1,322,111` cycles,
  so `1,896`;
* `sdp_gas_eq`: the SDP declaration and withdrawal are a ZkTransfer and a signature;
* `limit_eq`: the fixed parts of the two batches, `3,540,612 + 3,975,765` cycles, take
  `7,517` from the `3,200,000` budget, so `G_max = 3,192,483` and `G_target = 1,596,241`;
* `transfers_per_block`: the limit covers `5,157` ZkTransfers, over `5,000` and over the
  `1,024` transactions a block references (PR #480's motivation);
* `blocks_to_fill_set`: at that rate a note set, capped at `2^32 - 1` commitments by its
  depth-32 tree, fills in about 36 days of full blocks.
-/

namespace Mantle

/-- `⌈cycles / 1000⌉`. -/
def gasOfCycles (cycles : ℕ) : ℕ := (cycles + 999) / 1000

def EXECUTION_TRANSFER_GAS : ℕ := 619
def EXECUTION_CHANNEL_INSCRIBE_GAS : ℕ := 59
def EXECUTION_CHANNEL_CONFIG_GAS : ℕ := 59
def EXECUTION_CHANNEL_DEPOSIT_GAS : ℕ := 619
def EXECUTION_CHANNEL_WITHDRAW_GAS : ℕ := 619
def EXECUTION_SDP_DECLARE_GAS : ℕ := 678
def EXECUTION_SDP_WITHDRAW_GAS : ℕ := 678
def EXECUTION_SDP_ACTIVE_GAS : ℕ := 59
def EXECUTION_CLAIM_POW_REWARD_GAS : ℕ := 0
def EXECUTION_PROGRAM_REGISTER_GAS : ℕ := 1896
def EXECUTION_PROGRAM_SPEND_GAS : ℕ := 619
def EXECUTION_PROGRAM_PROOF_GAS : ℕ := 2451

/-- The Execution Gas of one Ed25519 signature check. -/
def ED25519_GAS : ℕ := 59

/-- The CPU budget of a leader: 1 second at 80% of the minimum CPU, in Execution Gas. -/
def LEADER_BUDGET : ℕ := 3_200_000

/-- `limit_Ex = G_max`. -/
def G_MAX : ℕ := 3_192_483

/-- `G_target`. -/
def G_TARGET : ℕ := 1_596_241

theorem transfer_gas_eq : gasOfCycles 618_797 = EXECUTION_TRANSFER_GAS := by decide

theorem deposit_withdraw_gas_eq :
    EXECUTION_CHANNEL_DEPOSIT_GAS = EXECUTION_TRANSFER_GAS ∧
      EXECUTION_CHANNEL_WITHDRAW_GAS = EXECUTION_TRANSFER_GAS := ⟨rfl, rfl⟩

theorem program_spend_gas_eq : gasOfCycles 618_796 = EXECUTION_PROGRAM_SPEND_GAS := by decide

theorem program_proof_gas_eq :
    gasOfCycles (2_221_544 + 228_669) = EXECUTION_PROGRAM_PROOF_GAS := by decide

theorem program_register_gas_eq :
    gasOfCycles (573_324 + 1_322_111) = EXECUTION_PROGRAM_REGISTER_GAS := by decide

theorem sdp_gas_eq :
    EXECUTION_SDP_DECLARE_GAS = EXECUTION_TRANSFER_GAS + ED25519_GAS ∧
      EXECUTION_SDP_WITHDRAW_GAS = EXECUTION_TRANSFER_GAS + ED25519_GAS ∧
      EXECUTION_SDP_ACTIVE_GAS = ED25519_GAS := ⟨rfl, rfl, rfl⟩

/-- The fixed parts of the ZkTransfer and ZkProgramSpend batch verifications are deducted from
the leader budget. -/
theorem limit_eq :
    LEADER_BUDGET - gasOfCycles (3_540_612 + 3_975_765) = G_MAX ∧ G_TARGET = G_MAX / 2 := by
  decide

/-- The block limit covers over 5,000 ZkTransfers, more than the 1,024 transactions a block
can reference. -/
theorem transfers_per_block : G_MAX / EXECUTION_TRANSFER_GAS = 5157 ∧ 5000 < 5157 ∧
    1024 < G_MAX / EXECUTION_TRANSFER_GAS := by decide

/-- **Capacity of a note set.** A ZkTransfer creates at most 8 notes, so a block at the
Execution Gas limit appends up to `5,157 · 8 = 41,256` commitments to the ledger set (or to a
channel set, through steps). The `2^32 - 1` commitments of a depth-32 MMR (`mmrRoot_full`) are
then exhausted in `104,106` such blocks, about 36 days at one block every 30 seconds. -/
theorem blocks_to_fill_set :
    G_MAX / EXECUTION_TRANSFER_GAS * 8 = 41_256 ∧
      (2 ^ 32 - 1) / (G_MAX / EXECUTION_TRANSFER_GAS * 8) + 1 = 104_106 ∧
      104_106 * 30 / 86_400 = 36 := by decide

/-- The Execution Gas of a program step with `n` payments. -/
def programStepGas (n : ℕ) : ℕ :=
  EXECUTION_TRANSFER_GAS * n + EXECUTION_PROGRAM_SPEND_GAS + EXECUTION_PROGRAM_PROOF_GAS

/-- Byte sizes of RFC-481 §5: a `ProgramNoteOpening` (`Value NoteNonce ZkPublicKey
ProgramNoteData`) and a verification key (`Alpha G1, Beta Gamma Delta G2, 4 IC G1`, compressed
points of 32 and 64 bytes). -/
theorem encoding_sizes : 8 + 32 + 32 + 32 = 104 ∧ 32 + 3 * 64 + 4 * 32 = 352 := by decide

end Mantle
