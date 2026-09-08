# Mempool pull confirmation — threshold calibration

Calibrates and verifies `PULL_CONFIRMATIONS`, the number of attestations a
transaction must collect before a Logos Blockchain node will select it for a
block proposal. Supports the mempool specification in `logos-lips`
(`docs/blockchain/raw/mempool.md`).

## What is being calibrated

A node disseminates a transaction by **push** — relaying it to its gossipsub
mesh — and then establishes that it actually spread by **pull**: after a delay,
it asks randomly sampled members of the active Service Declaration Protocol set
whether they hold it, and collects their signed positive answers as
attestations. A transaction with enough attestations is *confirmed*, and only
confirmed transactions are offered to block building. That gate is the mitigation
for the tagging attack: a transaction delivered to one node alone never confirms,
so it never appears in a proposal, so it never identifies a proposer.

The threshold is the whole security parameter, and it is squeezed from both
sides.

**Security — a tagged transaction must not confirm.** The adversary hands a
transaction to one node and to nobody else. Every honest provider truthfully
answers that it does not hold it, so the only providers that can attest are the
adversary's own, which do hold it because the adversary wrote it. The attack
succeeds exactly when the node happens to draw enough adversarial providers. A
*higher* threshold is safer.

**Liveness — a genuinely broadcast transaction must confirm.** Honest providers
hold it and attest. The node fails when too few of the providers it sampled
attest. A *lower* threshold is safer.

So the threshold must sit strictly between the number of adversarial providers a
run is likely to draw and the number of attesters it is likely to draw. That
window exists only while the adversarial fraction leaves room for it, and its
width is what decides how many providers have to be sampled.

Two consequences are easy to miss and are the reason this tool exists rather
than a formula in a comment:

- **The sample size is a security parameter, not a budget.** Querying more
  providers at a fixed threshold makes the attack *more* likely, because it gives
  the adversary more draws to accumulate attestations from. Sample and threshold
  move together; neither can be rounded independently.
- **Withholding changes the answer by an order of magnitude.** An adversary that
  refuses to attest cannot make a tagged transaction confirm, so it does not
  enter the security bound — but it removes its whole share of every sample from
  the attesting pool, which is what the liveness bound is measured against.

## Result

The specification's rule is a **majority of a fixed sample**: a transaction is
confirmed when more than half of `PULL_SAMPLE` distinct providers attest to it,
where `PULL_SAMPLE` is 128 or the whole attester set when the set is smaller.
Nothing in the rule is a network size. Confidence comes from the absolute number
of distinct providers asked, not from their share of the set, so the sample is a
fixed count; below it the rule is a census and exact.

At the specification's assumptions — adversarial fraction **exactly one third**
of the attester set (the adversary count always rounds up), honest providers
holding a broadcast transaction with probability 0.99 by the time they are
asked, adversary withholding:

| constant | value |
| --- | --- |
| `PULL_SAMPLE_SIZE` | 16 providers per round |
| `PULL_MAX_ROUNDS` | 8 |
| `PULL_SAMPLE` | 128, or the set if smaller |
| rule | more than half of `PULL_SAMPLE` attest (65 of 128) |

| attester set | security failure | liveness failure |
| --- | --- | --- |
| 5000 | 2.76e-05 | 1.15e-04 |
| 1000 | 6.9e-06 | 3.1e-05 |
| 300 | 6.0e-08 | 1.1e-06 |

Reproduce with `make evaluate SAMPLE=16 ROUNDS=8 WITHHOLD=1` (omitting
`THRESHOLD` selects the majority rule). Both bounds tighten on a smaller set,
because 128 of 300 is nearly a census.

**Why 128, and why not a cryptographic target.** The earlier revision of this
analysis targeted 1e-9 and 1e-6 and needed 256 draws. Those are the wrong
targets for this threat. A successful tag is one observation of one proposal;
estimating a node's proposal rate takes tens of observations; so at 2.8e-5 an
adversary needs some 36 000 tagged transactions per observation and around a
million, each paying fees, for one usable estimate. Doubling the sample would buy
five orders of magnitude for twice the connections, which the threat does not
justify. The cost lands on liveness: 1.15e-4 per transaction per node is about
350 transactions a day that one node never selects. Other proposers do, so it is
a delay rather than a loss.

**Even samples.** A majority of an even sample needs a two-vote margin, of an odd
sample a single vote, so security failure alternates with the parity of the
sample: at one third, 128, 130 and 132 meet 3e-5 while 129 and 131 do not.
`make calibrate WITHHOLD=1` with `--majority` reports 132 as the first sample from
which every larger sample also passes; 128 is chosen as the even sample that
meets the targets at the intended round count. Pick even.

How it degrades with the adversarial fraction (sample 128, majority rule):

| adversarial fraction | security failure | liveness failure |
| --- | --- | --- |
| 0.30 | 5.0e-07 | 3.0e-06 |
| 1/3 | 2.8e-05 | 1.2e-04 |
| 0.36 | 3.7e-04 | 1.2e-03 |
| 0.40 | 8.0e-03 | 1.8e-02 |
| 0.45 | 1.1e-01 | 1.8e-01 |

One third is the tolerated fraction. Above one half a tagged transaction and a
broadcast one return the same share of positive answers and no rule separates
them, which is a property of the mechanism, not of the parameter choice.

**Draws must be distinct.** The closed forms draw the whole sample without
replacement, as an urn. An earlier revision of the specification re-sampled from
the whole set every round and merely skipped a provider it had already asked, so
repeats were wasted draws and the effective sample shrank with the set. Under the
old absolute threshold of 133 that lost a third of all transactions at 500
declarations; under the majority rule the loss is a few tenths of a percent, but
the closed forms no longer describe the protocol. The specification now excludes
the providers sampled in the previous `PULL_MAX_ROUNDS - 1` rounds, which makes
eight consecutive rounds an urn draw exactly. `make verify WITHHOLD=1
RESAMPLE=1` measures the gap the old sampling opened.

## Usage

No dependencies beyond the standard library; every analysis target runs with a
bare `python3`.

```
make calibrate                                     # cheapest safe configuration, per adversarial fraction
make calibrate WITHHOLD=1                          # the same against an adversary that refuses to attest
make evaluate SAMPLE=16 ROUNDS=8 WITHHOLD=1            # score the majority rule (reproduces the headline)
make evaluate SAMPLE=32 ROUNDS=8 THRESHOLD=133 WITHHOLD=1   # score an absolute threshold
make calibrate WITHHOLD=1 MAJORITY=1                   # smallest sample the majority rule needs
make cost SAMPLE=16 ROUNDS=8 WITHHOLD=1                # expected queries and rounds
make verify WITHHOLD=1 RESAMPLE=1                      # what re-sampling each round costs
make verify                                        # closed forms against the simulated protocol
make test                                          # unit tests (needs the venv)
```

Override the assumptions on any target that uses them: `PROVIDERS`, `FRACTION`
(evaluate/cost), `FRACTIONS` (the calibrate sweep list), `HOLD`, `WITHHOLD`,
`TRIALS` (verify). The headline table assumes a withholding adversary, so
reproducing it requires `WITHHOLD=1`.

## Layout

| path | what it holds |
| --- | --- |
| `src/pull_confirmation/model.py` | closed forms for both failure probabilities |
| `src/pull_confirmation/calibrate.py` | search over sample size and threshold |
| `src/pull_confirmation/simulate.py` | Monte-Carlo of the round-based protocol |
| `src/pull_confirmation/cli.py` | `evaluate`, `calibrate`, `verify`, `cost` |
| `tests/` | distributional checks, monotonicity, simulator agreement |

## Method notes

Sampling is without replacement from a finite declaration set, so every count is
hypergeometric rather than binomial. At the set sizes Bedrock expects, that is
not a cosmetic difference: without-replacement draws concentrate the count, so
the binomial approximation overstates the security tail (by ~3x at the design
point — 6.7e-10 against the exact 2.3e-10). The exact model is therefore what
makes the calibrated sample genuinely minimal; a binomial calibration would have
been safe but oversized. Distributions are built by an anchored
ratio recurrence from the mode outward and tails are accumulated inward, because
the interesting probabilities are around 1e-10 and a naive sum loses them.

`make verify` checks the closed forms against a simulator that runs the protocol
as specified — in rounds, accumulating across them, stopping early once the
threshold is met — at parameters whose failure rates a 1e5-trial run can actually
resolve. Agreement there is what licenses trusting the closed forms out at 1e-9,
where no simulation could reach.

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
  assumption, not a measurement.
- Correlated failure. Providers are assumed to answer independently, so an
  adversary that can partition the network, or a hosting failure that takes out a
  correlated block of declarations, is outside the model.
- The adversary is assumed not to be able to influence *which* providers a node
  samples. The specification requires the sample to be drawn from local
  randomness for exactly this reason.
- The known-holder exclusion. The specification does not ask the providers a
  transaction arrived from (`received_from`); the model samples uniformly from
  the full declaration set. Excluding known holders removes guaranteed-yes
  providers from the pool, which is anti-conservative for liveness and
  conservative for security; at a handful of excluded peers against a large set
  the shift is well inside the margins above, but it is a fidelity gap, not a
  modelling choice, and on a set near the sample size it is not small.
