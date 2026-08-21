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

At the specification's assumptions — 5000 active declarations, adversarial
fraction 1/3, honest providers holding a broadcast transaction with probability
0.99 by the time they are asked, security failure at most 1e-9 and liveness
failure at most 1e-6, adversary withholding:

| constant | value |
| --- | --- |
| `PULL_SAMPLE_SIZE` | 32 providers per round |
| `PULL_MAX_ROUNDS` | 8 |
| total sampled | 256 |
| `PULL_CONFIRMATIONS` | 134 |

giving a security failure of 4.4e-11 and a liveness failure of 7.5e-7 (the
4.4e-11 reproduces exactly under integer arithmetic). The feasible thresholds at
this sample are 131 to 134; 134 is chosen as the one furthest from the security
bound, since a tagging success cannot be retried away whereas a confirmation
failure can.

Strictly the smallest stable total sample is 236 (threshold 122, security
9.7e-10); 256 is adopted as the operating point because it splits into clean
32-provider rounds and buys a further 20x of security margin for 20 extra
queries. The threshold belongs to the sample: 134 is calibrated for a 256-draw
run and is not safe over a larger one.

How it degrades, at the same constants:

| adversarial fraction | security failure | liveness failure |
| --- | --- | --- |
| 0.20 | 1.9e-32 | 1.5e-23 |
| 0.33 | 4.4e-11 | 7.5e-07 |
| 0.40 | 2.8e-05 | 8.0e-03 |

One third is therefore the tolerated fraction, and the margin past it is thin —
which is a property of the mechanism, not of the parameter choice: above one half
no threshold satisfies both bounds at any sample size.

**A previously proposed `PULL_CONFIRMATIONS = 24` over a sample of 64 fails
badly**: at f = 1/3 its security failure is 2.5e-01. Reproduce with

```
make evaluate SAMPLE=8 ROUNDS=8 THRESHOLD=24 PROVIDERS=1000
```

## Usage

No dependencies beyond the standard library; every analysis target runs with a
bare `python3`.

```
make calibrate               # cheapest safe configuration, per adversarial fraction
make calibrate-withhold      # the same against an adversary that refuses to attest
make evaluate SAMPLE=32 ROUNDS=8 THRESHOLD=134    # score one candidate
make cost SAMPLE=32 ROUNDS=8 THRESHOLD=134        # expected queries and rounds
make verify                  # closed forms against the simulated protocol
make test                    # unit tests (needs the venv)
```

Override the assumptions on any target: `PROVIDERS`, `FRACTION`, `HOLD`.

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
point — 1.4e-10 against the exact 4.4e-11). The exact model is therefore what
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
