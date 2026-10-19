import Mantle.Encoding
import Mantle.Channels

/-!
# The gas check of a Mantle Transaction never rejects an encodable one

Mantle, *Validation*: `tx_execution_gas = checked_uint64(tx_execution_gas + execution_gas(...))`.
An encodable transaction has at most `255` Operations, an inscription at most `65,535` steps and
a program step at most `255` payments, and every channel has a `uint16` threshold (`ChanInv`), so
an Operation costs at most `MAX_OP_GAS ≈ 1.05·10¹⁰` and a transaction less than `2^42`:

* `applyOps_gas_lt`: the gas of a valid sequence of Operations is below `2^64`, the check being
  in force;
* `executionGas_le`, **`gas_check_holds`**: at every Operation of an encodable transaction, the
  check's condition holds, so it never rejects one; it binds only on Operations no encoding
  carries.
-/

namespace Mantle

open Encoding

noncomputable section

variable {P : Prims} {E : Env}

/-- The most Execution Gas an encodable Operation costs: an inscription of `65,535` program
steps of `255` payments each. -/
def MAX_OP_GAS : ℕ := EXECUTION_CHANNEL_INSCRIBE_GAS + 65535 * programStepGas 255

theorem step_gas_le {s : Step} (h : stepC.wf s) : s.gas ≤ programStepGas 255 := by
  cases s with
  | user u =>
    simp only [Step.gas, programStepGas]
    omega
  | program ps =>
    have hp : ps.payments.length ≤ 255 := h.1.2.1.1
    simp only [Step.gas, programStepGas]
    have := Nat.mul_le_mul_left EXECUTION_TRANSFER_GAS hp
    omega

/-- The Execution Gas of an encodable Operation, against a state whose channels are `ChanOk`, is
at most `MAX_OP_GAS`. -/
theorem executionGas_le {st : State} (C : ChanInv st) {op : Op} (h : op.Wf) :
    executionGas st op ≤ MAX_OP_GAS := by
  cases op with
  | channelConfig c =>
    simp only [executionGas]
    cases hc : st.channels c.channel with
    | none => simp
    | some ch =>
      have := (C _ _ hc).2.2
      simp only [Option.map_some, Option.getD_some, MAX_OP_GAS, EXECUTION_CHANNEL_CONFIG_GAS,
        EXECUTION_CHANNEL_INSCRIBE_GAS, programStepGas, EXECUTION_TRANSFER_GAS,
        EXECUTION_PROGRAM_SPEND_GAS, EXECUTION_PROGRAM_PROOF_GAS]
      omega
  | channelInscribe m =>
    have hw : m.steps.length ≤ 65535 ∧ ∀ s ∈ m.steps, stepC.wf s := h.1.2.2.2.2
    simp only [executionGas, MAX_OP_GAS]
    have hs : (m.steps.map Step.gas).sum ≤ m.steps.length * programStepGas 255 := by
      simpa using List.sum_le_length_nsmul (m.steps.map Step.gas) (programStepGas 255)
        (fun g hg => by
          obtain ⟨s, hs, rfl⟩ := List.mem_map.1 hg
          exact step_gas_le (hw.2 s hs))
    have := Nat.mul_le_mul_right (programStepGas 255) hw.1
    omega
  | _ => simp only [executionGas, MAX_OP_GAS, programStepGas]; decide

/-- The check is in force: the gas of a valid sequence of Operations is below `2^64`. -/
theorem applyOps_gas_lt {txh : Fr} {ops : List Op} {πs : List OpProof} {st st' : State}
    {bal gas : ℕ} (h : applyOps P E st txh ops πs = some (st', bal, gas)) : gas < TOKEN_BOUND := by
  cases ops with
  | nil =>
    cases πs with
    | nil =>
      simp only [applyOps, Option.some.injEq, Prod.mk.injEq] at h
      rw [← h.2.2]
      decide
    | cons _ _ => simp [applyOps] at h
  | cons op ops =>
    cases πs with
    | nil => simp [applyOps] at h
    | cons π πs =>
      simp only [applyOps, option_bind_eq_some, ensure_eq_some, option_pure_eq, exists_const,
        Option.some.injEq, Prod.mk.injEq] at h
      obtain ⟨⟨st1, fee⟩, -, ⟨st2, bal', gas'⟩, -, -, hg, -, -, rfl⟩ := h
      exact hg

/-- The gas of the encodable Operations `ops`, valid from a state whose channels are `ChanOk`,
is at most `MAX_OP_GAS` each. -/
theorem applyOps_gas_le {txh : Fr} (ops : List Op) :
    ∀ (πs : List OpProof) (st st' : State) (bal gas : ℕ), ChanInv st → (∀ op ∈ ops, op.Wf) →
      applyOps P E st txh ops πs = some (st', bal, gas) → gas ≤ ops.length * MAX_OP_GAS := by
  induction ops with
  | nil =>
    intro πs st st' bal gas _ _ h
    cases πs with
    | nil =>
      simp only [applyOps, Option.some.injEq, Prod.mk.injEq] at h
      simp [← h.2.2]
    | cons _ _ => simp [applyOps] at h
  | cons op ops ih =>
    intro πs st st' bal gas C hw h
    cases πs with
    | nil => simp [applyOps] at h
    | cons π πs =>
      simp only [applyOps, option_bind_eq_some, ensure_eq_some, option_pure_eq, exists_const,
        Option.some.injEq, Prod.mk.injEq] at h
      obtain ⟨⟨st1, fee⟩, h1, ⟨st2, bal', gas'⟩, h2, -, -, -, -, rfl⟩ := h
      have e1 := executionGas_le C (hw op (List.mem_cons_self ..))
      have e2 := ih πs st1 st2 bal' gas' (C.applyOp h1) (fun o ho => hw o (List.mem_cons_of_mem _ ho)) h2
      simp only [List.length_cons, Nat.succ_mul]
      omega

/-- **The gas check never rejects an encodable transaction**: at an Operation `op` followed by
fewer than `255` Operations (an encodable transaction has at most `255`), the condition of the
check, `execution_gas(op) + tx_execution_gas < 2^64`, holds whenever the later Operations are
valid. -/
theorem gas_check_holds {txh : Fr} {st st1 st2 : State} {op : Op} {π : OpProof} {ops : List Op}
    {πs : List OpProof} {fee bal gas : ℕ} (C : ChanInv st) (hop : op.Wf)
    (hops : ∀ o ∈ ops, o.Wf) (hlen : ops.length < 255)
    (h1 : applyOp P E st txh op π = some (st1, fee))
    (h2 : applyOps P E st1 txh ops πs = some (st2, bal, gas)) :
    executionGas st op + gas < TOKEN_BOUND := by
  have e1 := executionGas_le C hop
  have e2 := applyOps_gas_le ops πs st1 st2 bal gas (C.applyOp h1) hops h2
  have e3 := Nat.mul_le_mul_right MAX_OP_GAS (Nat.le_of_lt_succ hlen)
  have : MAX_OP_GAS + 254 * MAX_OP_GAS < TOKEN_BOUND := by decide
  omega

/-- An encodable transaction has at most `255` Operations. -/
theorem mantleTx_ops_le {tx : MantleTx} (h : mantleTxC.wf tx) :
    tx.ops.length ≤ 255 ∧ ∀ op ∈ tx.ops, op.Wf := h.1

end

end Mantle
