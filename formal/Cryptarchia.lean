module -- shake: keep-all

-- The specification
public import Cryptarchia.Spec.Params
public import Cryptarchia.Spec.Lottery
public import Cryptarchia.Spec.StakeInference
public import Cryptarchia.Spec.Chain
public import Cryptarchia.Spec.ForkChoice
public import Cryptarchia.Spec.EpochState
public import Cryptarchia.Spec.Node
public import Cryptarchia.Spec.Execution
-- Settlement combinatorics
public import Cryptarchia.Settle.Tree
public import Cryptarchia.Settle.TreeBasic
public import Cryptarchia.Settle.Recurrence
public import Cryptarchia.Settle.Phases
public import Cryptarchia.Settle.Mono
public import Cryptarchia.Settle.Reduce
-- Deterministic safety over executions
public import Cryptarchia.Proof.Chains
public import Cryptarchia.Proof.Lca
public import Cryptarchia.Proof.Maintenance
public import Cryptarchia.Proof.Structural
public import Cryptarchia.Proof.NodeStep
public import Cryptarchia.Proof.WorldStep
public import Cryptarchia.Proof.Bridge
public import Cryptarchia.Proof.Honest
public import Cryptarchia.Proof.Timing
public import Cryptarchia.Proof.Local
public import Cryptarchia.Proof.Trace
public import Cryptarchia.Proof.Honesty
public import Cryptarchia.Proof.Support
public import Cryptarchia.Proof.Main
public import Cryptarchia.Proof.Settlement
public import Cryptarchia.Proof.EpochCut
public import Cryptarchia.Proof.Canon
public import Cryptarchia.Proof.LotteryG
public import Cryptarchia.Proof.Lottery
public import Cryptarchia.Proof.Final
public import Cryptarchia.Proof.LotteryE
public import Cryptarchia.Proof.FinalE
public import Cryptarchia.Proof.TimeFinal
public import Cryptarchia.Proof.Recur
-- The probability layer
public import Cryptarchia.Prob.InferClose
public import Cryptarchia.Prob.Kernel
public import Cryptarchia.Prob.Phases
public import Cryptarchia.Prob.Potential
public import Cryptarchia.Prob.Burst
public import Cryptarchia.Prob.Next
public import Cryptarchia.Prob.Cold
public import Cryptarchia.Prob.Reach
public import Cryptarchia.Prob.Blocks
public import Cryptarchia.Prob.Depth
public import Cryptarchia.Prob.Good
public import Cryptarchia.Prob.Tail
public import Cryptarchia.Prob.Final
public import Cryptarchia.Prob.Auto
public import Cryptarchia.Prob.Potential2
public import Cryptarchia.Prob.Cold2
public import Cryptarchia.Prob.Fail2
public import Cryptarchia.Prob.Good2
public import Cryptarchia.Prob.Reach2
public import Cryptarchia.Prob.Tail2
public import Cryptarchia.Prob.Final2
public import Cryptarchia.Prob.Cert
public import Cryptarchia.Prob.Worst
public import Cryptarchia.Prob.RO
public import Cryptarchia.Prob.Stake
public import Cryptarchia.Prob.WorstE
public import Cryptarchia.Prob.ROEpoch
public import Cryptarchia.Prob.AutoE
public import Cryptarchia.Prob.Cold2E
public import Cryptarchia.Prob.Fail2E
public import Cryptarchia.Prob.Tail2E
public import Cryptarchia.Prob.Final2E
public import Cryptarchia.Prob.TSIRO
public import Cryptarchia.Prob.FinalTSI
public import Cryptarchia.Prob.Fail3E
public import Cryptarchia.Prob.Tail3E
public import Cryptarchia.Prob.Final3E
public import Cryptarchia.Prob.CertE
public import Cryptarchia.Prob.AutoQ
public import Cryptarchia.Prob.Pick
public import Cryptarchia.Prob.Occupied
public import Cryptarchia.Proof.Signers
public import Cryptarchia.Proof.Consist
public import Cryptarchia.Prob.Trunc
public import Cryptarchia.Prob.EpochInd
public import Cryptarchia.Prob.Drift
public import Cryptarchia.Prob.WorstStop
public import Cryptarchia.Prob.ROStop
public import Cryptarchia.Prob.FinalTight
public import Cryptarchia.Prob.Finality
public import Cryptarchia.Prob.ExpBound


/-!
# Cryptarchia

The consensus protocol of the Logos blockchain, formalized from its specification.

* `Cryptarchia.Spec` — the protocol as specified: parameters, the lottery, total stake
  inference, chains and fork choice, epoch states, honest nodes, executions.
* `Cryptarchia.Settle` — settlement combinatorics on PoS trees (reach and margin bounds).
* `Cryptarchia.Proof` — deterministic safety: k-deep finality over every execution on a
  good event of the lottery string.
* `Cryptarchia.Prob` — the probability layer: the lottery as a random oracle, the
  worst-case kernels, the settlement bound, and the stake estimate's concentration.

The generated numeric certificates are a separate library (`CryptarchiaCerts`).
-/
