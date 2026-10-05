import Cryptarchia.Spec.Chain

/-!
# Cryptarchia: fork choice

`fork-choice.md` rev 1.1.0, *Bootstrap Fork Choice Rule* (`maxvalid-bg`) and
*Online Fork Choice Rule* (`maxvalid-mc`). Both are a loop over the tips `F_T`,
updating a running choice `c_max` that starts at the local chain `c_loc`.

**Order.** The specification iterates over a *set* of forks and does not fix the
order; the result can depend on it (a fork accepted early moves `c_max`, which
changes which later forks are within `k`). The implementation iterates in the
hash-trie order of the tip IDs (`consensus/cryptarchia-engine/src/lib.rs:270`).
The model takes the order as an argument, and every theorem about fork choice
quantifies over all orders.
-/

namespace Cryptarchia

variable (st : Store)

/-- Which fork choice rule a node runs. -/
inductive Rule
  | online
  | bootstrap
  deriving DecidableEq, Repr

/-- One iteration of `online_fork_choice`: switch to `fork` if it diverges from
`c_max` at most `k` blocks deep and is strictly longer. -/
def onlineStep (k cmax fork : ℕ) : ℕ :=
  let d := commonPrefixDepth st cmax fork
  if d.1 ≤ k then (if d.1 < d.2 then fork else cmax) else cmax

/-- One iteration of `bootstrap_fork_choice`: within `k`, the longest chain; beyond
`k`, the chain denser in the `s_gen` slots after the divergence. -/
def bootstrapStep (k sGen cmax fork : ℕ) : ℕ :=
  let d := commonPrefixDepth st cmax fork
  if d.1 ≤ k then (if d.1 < d.2 then fork else cmax)
  else (if density st cmax d.1 sGen < density st fork d.2 sGen then fork else cmax)

/-- **`fork_choice(c_loc, forks, k, s)`**, the forks visited in the given order. -/
def forkChoice (rule : Rule) (k sGen cloc : ℕ) (forks : List ℕ) : ℕ :=
  match rule with
  | .online => forks.foldl (onlineStep st k) cloc
  | .bootstrap => forks.foldl (bootstrapStep st k sGen) cloc

end Cryptarchia
