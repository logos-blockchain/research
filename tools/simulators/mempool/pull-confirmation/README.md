# Mempool pull confirmation — sample calibration

Calibrates and verifies the confirmation rule of the mempool specification in
`logos-lips` (`docs/blockchain/raw/mempool.md`): how many providers a Logos
Blockchain node asks about a transaction, and what share of them must attest,
before the node will select it for a block proposal.

## What is being calibrated

A node disseminates a transaction by **push** — relaying it to its gossipsub
mesh — and then establishes that it is spreading by **pull**: after a delay, it
asks randomly sampled members of the active Service Declaration Protocol set
whether they hold it, and collects their positive answers, each carrying a
possession witness, as attestations. A transaction with enough attestations is
*confirmed*, and only confirmed transactions are offered to block building. The
gate is what lets a proposer include only transactions that validators will be
able to reconstruct, and as a consequence it also closes the tagging attack: a
transaction delivered to one node alone never confirms, so it never appears in
a proposal, so it never identifies a proposer.

The rule is squeezed from both sides.

**Security — a tagged transaction must not confirm.** The adversary hands a
transaction to one node and to nobody else. Every honest provider truthfully
answers that it does not hold it, so the only providers that can attest are the
adversary's own, which do hold it because the adversary wrote it. The attack
succeeds exactly when the node happens to draw enough adversarial providers. A
*stricter* rule is safer.

**Liveness — a genuinely broadcast transaction must confirm.** Honest providers
hold it and attest. The node fails when too few of the providers it sampled
attest. A *looser* rule is safer.

So the rule must sit strictly between the share of adversarial providers a run
is likely to draw and the share of attesters it is likely to draw. That window
exists only while the adversarial fraction leaves room for it, and its width is
what decides how many providers have to be sampled.

Two consequences are easy to miss and are the reason this tool exists rather
than a formula in a comment:

- **The sample size is a security parameter, not a budget.** Querying more
  providers at a fixed attestation count makes the attack *more* likely, because
  it gives the adversary more draws to accumulate attestations from. The
  specification's rule is therefore a majority of everyone asked, so the bar
  rises with the draws.
- **Withholding changes the answer by an order of magnitude.** An adversary that
  refuses to attest cannot make a tagged transaction confirm, so it does not
  enter the security bound — but it removes its whole share of every sample from
  the attesting pool, which is what the liveness bound is measured against.

## The rule

At the start of every round, a node confirms each transaction for which more
than half of the providers that have answered attest, counting at least
`PULL_SAMPLE` in the denominator; `PULL_SAMPLE` is 128, or the whole attester
set when the set is smaller. Confirmation is recorded and never revisited. A
provider that refused is asked again when the sampling draws it again, and a
refusal is outvoted by later draws rather than retried. A node keeps asking for
up to `PULL_MAX_ROUNDS` rounds.

Nothing in the rule is a network size. Confidence comes from the absolute
number of providers asked, not from their share of the set, so the floor is a
fixed count; below it the rule is a census and exact.

## Result

At the specification's assumptions — adversarial fraction **exactly one third**
of the attester set (the adversary count always rounds up), honest providers
holding a broadcast transaction with probability 0.99 by the time they are
asked, adversary withholding, targets of 4e-5 on security and 2e-4 on liveness:

| constant | value |
| --- | --- |
| `PULL_SAMPLE_SIZE` | 16 providers per round |
| `PULL_MAX_ROUNDS` | 16 |
| `PULL_SAMPLE` | 128, or the set if smaller |
| rule | more than half of everyone who answered, from 128 answers on |

| attester set | security failure | liveness failure |
| --- | --- | --- |
| 5000 | 3.15e-05 | 1.4e-08 |
| 1000 | 1.1e-05 | 2.3e-10 |
| 300 | 6.0e-08 | 7.7e-34 |

Reproduce with `make evaluate SAMPLE=16 ROUNDS=16 MIN_SAMPLE=128 WITHHOLD=1`.
Both bounds tighten on a smaller set, because 128 of 300 is nearly a census, and
at 129 or fewer the security failure is zero: a third of the set cannot be a
majority of it.

**Why 128, and why not a cryptographic target.** An earlier revision of this
analysis targeted 1e-9 and 1e-6 and needed 256 draws. Those are the wrong
targets for this threat. A successful tag is one observation of one proposal;
estimating a node's proposal rate takes tens of observations; so at 3e-5 an
adversary needs some 30 000 tagged transactions per observation and around a
million, each paying fees, for one usable estimate. Doubling the sample would buy
five orders of magnitude for twice the connections, which the threat does not
justify. The targets are the round numbers above the operating point.

**What the second half of the rounds buys.** With eight rounds the rule is
checked once, at 128 answers, and liveness is 1.2e-4 — every point of hold
probability below 0.99 costs an order of magnitude, and at 0.90 one transaction
in eighty never confirms at a node. Eight more rounds let later answers outvote
early refusals: liveness at 0.99 falls to 1.4e-8, at 0.90 to 2.2e-4, and a
transaction still spreading while it is polled confirms where before it did not.
The price is that the adversary is checked again at every later round, which
raises the security failure from 2.8e-5 to 3.2e-5. Checking after every answer
instead of once a round would raise it to 5.6e-5, which is why the
specification checks once a round.

| rounds | security failure | liveness, hold 0.99 | hold 0.95 | hold 0.90 |
| --- | --- | --- | --- | --- |
| 8 | 2.8e-05 | 1.2e-04 | 1.3e-03 | 1.3e-02 |
| 12 | 3.2e-05 | 1.1e-06 | 4.0e-05 | 1.4e-03 |
| 16 | 3.2e-05 | 1.4e-08 | 1.9e-06 | 2.2e-04 |

**Even floors.** A majority of an even count needs a two-vote margin, of an odd
count a single vote, so the security failure alternates with the parity of the
floor: 128 gives 3.2e-5 where 130 gives 1.9e-5 and 132 gives 1.3e-5. Pick even.

How it degrades with the adversarial fraction (floor 128, 16 rounds):

| adversarial fraction | security failure | liveness failure |
| --- | --- | --- |
| 0.30 | 5.4e-07 | 8.3e-12 |
| 1/3 | 3.2e-05 | 1.4e-08 |
| 0.36 | 4.5e-04 | 1.7e-06 |
| 0.40 | 1.1e-02 | 4.2e-04 |
| 0.45 | 1.6e-01 | 3.8e-02 |

One third is the tolerated fraction. Above one half a tagged transaction and a
broadcast one return the same share of positive answers and no rule separates
them, which is a property of the mechanism, not of the parameter choice.

**Cost.** As specified — fresh draws from the whole set every round, a refusal
re-asked when drawn again — a broadcast transaction confirms after 6.7 rounds
and 106 queries on average against a withholding adversary, and after 5 rounds
and 80 queries against one that cooperates. A tagged transaction spends all 16
rounds and about 254 queries. `make cost SAMPLE=16 ROUNDS=16 MIN_SAMPLE=128
WITHHOLD=1 RESAMPLE=1` reproduces these.

## Usage

No dependencies beyond the standard library; every analysis target runs with a
bare `python3`.

```
make evaluate SAMPLE=16 ROUNDS=16 MIN_SAMPLE=128 WITHHOLD=1   # score the specification (reproduces the headline)
make cost SAMPLE=16 ROUNDS=16 MIN_SAMPLE=128 WITHHOLD=1 RESAMPLE=1   # queries and rounds, as specified
make verify SEQUENTIAL=1 WITHHOLD=1                # the walk against the simulated protocol
make evaluate SAMPLE=16 ROUNDS=8 WITHHOLD=1        # the fixed majority of 128 (a single check)
make evaluate SAMPLE=32 ROUNDS=8 THRESHOLD=133 WITHHOLD=1   # score an absolute threshold
make calibrate WITHHOLD=1 MAJORITY=1               # smallest fixed sample a majority rule needs
make calibrate                                     # cheapest fixed configuration, per adversarial fraction
make verify                                        # closed forms against the simulated protocol
make verify WITHHOLD=1 RESAMPLE=1                  # what skipping repeats costs the fixed rule
make test                                          # unit tests (needs the venv)
```

Override the assumptions on any target that uses them: `PROVIDERS`, `FRACTION`
(evaluate/cost), `FRACTIONS` (the calibrate sweep list), `HOLD`, `WITHHOLD`,
`TRIALS` (verify). The headline table assumes a withholding adversary, so
reproducing it requires `WITHHOLD=1`.

## Layout

| path | what it holds |
| --- | --- |
| `src/pull_confirmation/model.py` | closed forms for the fixed rule, and the walk for the specification's rule |
| `src/pull_confirmation/calibrate.py` | search over sample size and threshold for the fixed rule |
| `src/pull_confirmation/simulate.py` | Monte-Carlo of the round-based protocol, either rule |
| `src/pull_confirmation/cli.py` | `evaluate`, `calibrate`, `verify`, `cost` |
| `tests/` | distributional checks, monotonicity, simulator agreement |

## Method notes

Sampling is without replacement from a finite declaration set, so every count is
hypergeometric rather than binomial. At the set sizes Bedrock expects, that is
not a cosmetic difference: without-replacement draws concentrate the count, so
the binomial approximation overstates the security tail (by ~3x at the design
point — 6.7e-10 against the exact 2.3e-10). The exact model is therefore what
makes the calibrated sample genuinely minimal; a binomial calibration would have
been safe but oversized. Distributions are built by an anchored ratio recurrence
from the mode outward and tails are accumulated inward, because the interesting
probabilities are around 1e-10 and a naive sum loses them.

The specification's rule is checked at every round boundary, so its failure
probabilities are first-passage probabilities rather than tails of one
distribution. They are computed exactly by walking the draw sequence as a
Markov chain on the running counts and removing the mass that confirms at each
boundary. The walk draws from an urn; the protocol draws from the whole set
each round and re-asks a provider that refused. `make verify SEQUENTIAL=1`
checks the walk against an urn simulation, where the two must agree, and then
runs the protocol as specified beside it, where repeats delay the floor on a
small set and a re-asked provider rolls its hold afresh — a few tenths of a
round at 5 000 providers, a round and a quarter at 300.

`make verify` checks the fixed rule's closed forms against a simulator that runs
the protocol as specified — in rounds, accumulating across them, stopping early
once the threshold is met — at parameters whose failure rates a 1e5-trial run
can actually resolve. Agreement there is what licenses trusting the closed forms
out at 1e-9, where no simulation could reach.

**Feasibility is not monotone in the sample size.** Both bounds are thresholds on
an integer count and they step at different sample sizes, so just where the
window opens, a feasible sample is often followed by an infeasible one. Those
isolated points are real but they are knife edges — a percent of drift in any
assumption closes them — so `calibrate` reports the smallest sample from which
feasibility *holds and continues to hold*, and `first_feasible_sample` exposes
the difference. `tests/test_calibrate.py` pins both behaviours.

## What is not modelled

- `PULL_DELAY` enters only through `hold_probability`, the chance that an honest
  provider already holds a broadcast transaction when asked. Deriving that from
  gossipsub propagation for the mempool topic is separate work; 0.99 is an
  assumption, not a measurement. Under the specification's rule a lower value
  costs queries rather than confirmations, which is the point of the later
  rounds.
- Correlated failure. Providers are assumed to answer independently, so an
  adversary that can partition the network, or a hosting failure that takes out a
  correlated block of declarations, is outside the model.
- The adversary is assumed not to be able to influence *which* providers a node
  samples. The specification requires the sample to be drawn from local
  randomness for exactly this reason.
- Unanswered queries. A provider that does not answer is neither an attester nor
  in the denominator, and is asked again when drawn again; the walk has no term
  for the queries this costs.
