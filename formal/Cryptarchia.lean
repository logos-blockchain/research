-- The specification
import Cryptarchia.Spec.Params
import Cryptarchia.Spec.Lottery
import Cryptarchia.Spec.StakeInference
import Cryptarchia.Spec.Chain
import Cryptarchia.Spec.ForkChoice
import Cryptarchia.Spec.EpochState
import Cryptarchia.Spec.Node
import Cryptarchia.Spec.Execution
-- Settlement combinatorics
import Cryptarchia.Settle.Tree
import Cryptarchia.Settle.TreeBasic
import Cryptarchia.Settle.Recurrence
import Cryptarchia.Settle.Phases
import Cryptarchia.Settle.Mono
import Cryptarchia.Settle.Reduce
-- Deterministic safety over executions
import Cryptarchia.Proof.Chains
import Cryptarchia.Proof.Lca
import Cryptarchia.Proof.Maintenance
import Cryptarchia.Proof.Structural
import Cryptarchia.Proof.NodeStep
import Cryptarchia.Proof.WorldStep
import Cryptarchia.Proof.Bridge
import Cryptarchia.Proof.Honest
import Cryptarchia.Proof.Timing
import Cryptarchia.Proof.Local
import Cryptarchia.Proof.Trace
import Cryptarchia.Proof.Honesty
import Cryptarchia.Proof.Support
import Cryptarchia.Proof.Main
import Cryptarchia.Proof.Settlement
import Cryptarchia.Proof.EpochCut
import Cryptarchia.Proof.Canon
import Cryptarchia.Proof.LotteryG
import Cryptarchia.Proof.Lottery
import Cryptarchia.Proof.Final
import Cryptarchia.Proof.LotteryE
import Cryptarchia.Proof.FinalE
import Cryptarchia.Proof.TimeFinal
import Cryptarchia.Proof.Recur
-- The probability layer
import Cryptarchia.Prob.InferClose
import Cryptarchia.Prob.Kernel
import Cryptarchia.Prob.Phases
import Cryptarchia.Prob.Potential
import Cryptarchia.Prob.Burst
import Cryptarchia.Prob.Next
import Cryptarchia.Prob.Cold
import Cryptarchia.Prob.Reach
import Cryptarchia.Prob.Blocks
import Cryptarchia.Prob.Depth
import Cryptarchia.Prob.Good
import Cryptarchia.Prob.Tail
import Cryptarchia.Prob.Final
import Cryptarchia.Prob.Auto
import Cryptarchia.Prob.Potential2
import Cryptarchia.Prob.Cold2
import Cryptarchia.Prob.Fail2
import Cryptarchia.Prob.Good2
import Cryptarchia.Prob.Reach2
import Cryptarchia.Prob.Tail2
import Cryptarchia.Prob.Final2
import Cryptarchia.Prob.Cert
import Cryptarchia.Prob.Worst
import Cryptarchia.Prob.RO
import Cryptarchia.Prob.Stake
import Cryptarchia.Prob.WorstE
import Cryptarchia.Prob.ROEpoch
import Cryptarchia.Prob.AutoE
import Cryptarchia.Prob.Cold2E
import Cryptarchia.Prob.Fail2E
import Cryptarchia.Prob.Tail2E
import Cryptarchia.Prob.Final2E
import Cryptarchia.Prob.TSIRO
import Cryptarchia.Prob.FinalTSI
import Cryptarchia.Prob.Fail3E
import Cryptarchia.Prob.Tail3E
import Cryptarchia.Prob.Final3E
import Cryptarchia.Prob.CertE
import Cryptarchia.Prob.ExpBound

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
