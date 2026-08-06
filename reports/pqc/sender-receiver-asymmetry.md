# Who pays: sender/receiver asymmetry in post-quantum primitives

*Measured with [`make stress`](../../tools/benchmarks/pqc) — both sides of an exchange running flat out at the same time. Encoder = the side that produces the wire object; decoder = the side that consumes it. All ratios are decoder cost ÷ encoder cost, so **> 1 means the receiver pays more**.*

The per-operation benchmark answers *what does an operation cost?* This asks a
different question, and it is a protocol-design question rather than a
performance one: **when a message is sent, how does the work split between the
peer that sent it and the peer that receives it?**

The ratio matters because it is a multiplier available to anyone. If consuming
a message costs more than producing one, a peer can impose more work than it
performs, and the receiving side is where a network falls over — at a rate set
by the ratio, not by either side's absolute speed.

## Headline

**Migrating to post-quantum signatures reverses the direction of the signature
asymmetry.** Today's Ed25519 makes the *receiver* pay 2.35× what the sender
pays. Every PQ signature scheme measured inverts that: ML-DSA moves the cost to
the signer (0.28–0.38), Falcon further (0.15), and SLH-DSA to the point of
absurdity — SLH-DSA-SHA2-128s signs in 298 ms and verifies in 272 µs, a ratio of
0.001. For a network whose nodes verify far more signatures than they produce,
this is the favourable direction: the cost of migration lands on the side doing
the signing.

**Key exchange moves the other way, mildly.** X25519 is symmetric by
construction: both peers generate an ephemeral share and both derive, so the
exchange costs both sides the same (measured: 1.00). ML-KEM is not symmetric —
only the decoder generates a keypair — so with ephemeral keys the receiver pays
2.1–2.3× the sender. Per message alone, ignoring keygen, it is a mild 1.2×.

**Classic McEliece is in a category of its own and is disqualified by this
metric.** Decapsulation costs 600–1500× encapsulation: a peer hands the receiver
three orders of magnitude more work than it spent, per message, with no attack
required. Keygen additionally runs into whole seconds (0.2–2.7 s), so ephemeral
keys are not on the table at all. Its very small ciphertext is a genuine
bandwidth advantage, and this is its price.

## Results

Apple M4 Pro (14 cores), 2 s per phase leg, liboqs 0.15.0 pinned. **This is a
cross-platform datapoint, not a reference measurement** — see *Status* below.

| algorithm | roles | encoder | decoder | per message | mean | per session | contended |
|---|---|---:|---:|---:|---:|---:|---:|
| **X25519** | derive/derive | 22 µs | 22 µs | **1.00** | 0.99 | 1.00 | 1.00 |
| **Ed25519** | sign/verify | 20 µs | 47 µs | **2.35** | 2.39 | 2.35 | 2.38 |
| ML-KEM-512 | encaps/decaps | 6 µs | 8 µs | 1.33 | 1.24 | 2.33 | 1.16 |
| ML-KEM-768 | encaps/decaps | 10 µs | 12 µs | 1.20 | 1.18 | 2.20 | 1.14 |
| ML-KEM-1024 | encaps/decaps | 16 µs | 18 µs | 1.12 | 1.17 | 2.06 | 1.19 |
| FrodoKEM-640-AES | encaps/decaps | 246 µs | 239 µs | 0.97 | 1.00 | 1.76 | 0.95 |
| FrodoKEM-976-AES | encaps/decaps | 424 µs | 406 µs | 0.96 | 0.98 | 1.72 | 0.95 |
| FrodoKEM-1344-AES | encaps/decaps | 738 µs | 713 µs | 0.97 | 0.97 | 1.74 | 0.96 |
| Classic-McEliece-348864 | encaps/decaps | 15 µs | 15.6 ms | **1041** | 944 | — | 958 |
| Classic-McEliece-6960119 | encaps/decaps | 102 µs | 69.2 ms | **678** | 622 | — | 611 |
| Classic-McEliece-8192128 | encaps/decaps | 59 µs | 87.5 ms | **1483** | 1275 | — | 1250 |
| ML-DSA-44 | sign/verify | 148 µs | 42 µs | 0.28 | 0.23 | 0.28 | 0.23 |
| ML-DSA-65 | sign/verify | 233 µs | 68 µs | 0.29 | 0.24 | 0.29 | 0.23 |
| ML-DSA-87 | sign/verify | 292 µs | 110 µs | 0.38 | 0.31 | 0.38 | 0.32 |
| Falcon-512 | sign/verify | 121 µs | 19 µs | 0.16 | 0.15 | 0.16 | 0.16 |
| Falcon-1024 | sign/verify | 247 µs | 37 µs | 0.15 | 0.16 | 0.15 | 0.15 |
| SLH-DSA-SHA2-128f | sign/verify | 13.2 ms | 833 µs | 0.06 | 0.06 | 0.06 | 0.06 |
| SLH-DSA-SHA2-128s | sign/verify | 298 ms | 272 µs | **0.00097** | 0.001 | 0.001 | 0.001 |
| SLH-DSA-SHA2-256f | sign/verify | 46.6 ms | 1.21 ms | 0.03 | 0.03 | 0.03 | 0.03 |

*Per message* ignores keygen (long-lived keys). *Mean* is the same ratio from
each role's mean cost per operation instead of its median — see the note on
clock granularity under *Limitations*. *Per session* generates the keypair per
exchange, the TLS shape: for a KEM only the decoder pays it, for a DH exchange
both peers do, and for a signature it does not apply because keys are long-lived
identities; it reads "—" for Classic McEliece, whose seconds-long keygen yields
too few samples in a 2 s leg to support the figure. *Contended* is the same
quantity measured under load — how many decoder cores one encoder thread keeps
busy while both compete for the machine — rather than derived from isolated
latencies.

The full sweep, covering all 30 candidates, is in
[`results/stress-Mac-20260806T171550Z.json`](results); regenerate this view with
`python3 analyze/asymmetry.py <file>`.

## What the numbers mean for Logos

**Signature migration bills the signer, not the verifier.** In absolute terms,
verification gets ~1.4× more expensive moving Ed25519 → ML-DSA-65 (47 µs →
68 µs), while signing gets ~12× more expensive (20 µs → 233 µs). A node that
verifies many signatures and produces few — which is what consensus
participation looks like — absorbs the smaller half of the migration cost. A
node that signs at high rate does not.

**Ephemeral ML-KEM shifts key-exchange cost to the key publisher.** X25519's
symmetry is not a property PQ inherits: in TLS the client generates the ML-KEM
keypair and decapsulates while the server only encapsulates, so the client's
share of the handshake grows. At ML-KEM-768 that is 10 µs of keygen plus 12 µs
of decaps against the server's 10 µs of encaps.

**The measures agree, which is the reason to believe them.** Isolated median,
mean cost per operation, and the contended head-to-head are three largely
independent ways of asking the same question, and for every algorithm they land
in the same place — X25519 at 1.00/0.99/1.00, Ed25519 at 2.35/2.39/2.38,
ML-DSA-65 at 0.29/0.24/0.23. X25519 earns its place in the sweep for exactly
this reason: its two roles are *the identical operation*, so a ratio other than
~1.0 is a bug in the role plumbing rather than a finding, and `make test`
asserts it stays there.

## Limitations

**These are valid-input costs, and a denial-of-service attacker does not send
valid inputs.** Every measurement here uses a ciphertext that really decapsulates
and a signature that really verifies. An attacker sends garbage, and for several
of these algorithms a malformed input is rejected much earlier than a valid one
is accepted — so the ratios above are the *honest-peer* asymmetry, not an attack
cost model. Measuring the rejection path is the natural next step and would
change the DoS reading, possibly substantially.

**Fast operations are limited by the platform's clock, not by the harness.**
macOS resolves ~1 µs, so a 6 µs ML-KEM-512 encapsulation lands on a coarse grid
and its *median* ratio can only take a few discrete values — which is why that
row reads 1.33 by median and 1.24 by mean, and why the median moved between
repeat runs while the mean did not. The mean is taken over every operation the
leg completed (hundreds of thousands), so for anything under ~20 µs it is the
figure to quote. Nothing above ~100 µs is affected.

**Absolute rates do not leave this machine; ratios do.** A stress run uses every
core and is deliberately unpinned, so its throughput numbers carry the host's
thermal and scheduler behaviour. The ratio between two roles measured in the
same phase, on the same silicon, at the same moment is what transfers.

**The contended phase understates the encoder.** It runs one encoder thread
against a full set of decoder threads on the same cores, so the single encoder
is oversubscribed — the multiplier it reports is a floor, not a midpoint.

**No reference-platform run yet.** The sweep above is an Apple M4 Pro. The
ratios are unlikely to move much — they are dominated by algorithm structure,
not microarchitecture — but that is a prediction, not a measurement, until the
same sweep runs on the reference platform.

## Status and provenance

Stress runs carry `is_stress_grade` and never `is_baseline_grade: true`. They
cannot satisfy the reference gate — pinning to a single core would defeat the
concurrency being measured — and each file records its own
`not_reference_because` list. The distinct field name is deliberate: it stops a
stress file from being merged into the reference dataset by anything that only
checks a flag.

Reproduce with:

```bash
cd tools/benchmarks/pqc
make build && make stress            # full sweep; ~15 min
./stress.sh --alg ML-KEM-768         # one algorithm
python3 analyze/asymmetry.py reports/pqc/results/stress-<host>-<ts>.json
```
