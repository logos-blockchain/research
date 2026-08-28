# Who pays: sender/receiver asymmetry in post-quantum primitives

*Measured with [`make stress`](../../tools/benchmarks/pqc) — both sides of an exchange running flat out at the same time. Encoder = the side that produces the wire object; decoder = the side that consumes it. Ratios are decoder cost ÷ encoder cost, so **> 1 means the receiver pays more**. Every figure is the median of three runs; the spread across them is reported.*

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
asymmetry.** Ed25519 makes the *receiver* pay 2.50× what the sender pays. Every
PQ signature scheme measured inverts that: ML-DSA moves the cost to the signer
(0.29–0.38), Falcon further (0.15), and SLH-DSA to the point of absurdity —
SLH-DSA-SHA2-128s signs in 239 ms and verifies in 233 µs, a ratio of 0.001. For
a network whose nodes verify far more signatures than they produce, this is the
favourable direction: the migration bill lands on the side doing the signing.

**Rejecting a bad message costs the same as accepting a good one — everywhere.**
Timed against deliberately corrupted input, all 29 algorithms with a rejection
path land between 0.95× and 1.03× of their valid-input cost. These are
constant-time implementations; none bails out early. The honest-peer ratios are
therefore also the adversarial ones, and the two need not be reasoned about
separately.

**Post-quantum is also the better direction for flood resistance, because the
messages are bigger.** An attacker spends bandwidth, not CPU, so what bounds a
flood is receiver-CPU purchased per byte sent. A 64-byte Ed25519 signature buys
41 µs of verification — 641 ns/byte. A 3309-byte ML-DSA-65 signature buys 58 µs
— 17.5 ns/byte, **37× less**. Key exchange likewise: X25519 costs 563 ns/byte
against ML-KEM-768's 9.2. PQ's large wire objects, normally counted as the
migration's cost, are a defensive asset here.

**Classic McEliece is disqualified on this metric, and only in one direction.**
Flooding its *decapsulator* buys 140 000–337 000 ns of CPU per byte — four
orders of magnitude worse than anything else measured. Flooding its
*encapsulator* buys 0.05 ns/byte, the safest figure in the table, because the
attacker must ship a 261 KB public key to purchase 12 µs of work. Same
algorithm, a factor of 2.8 million between the two directions.

## Results

Apple M4 Pro (14 cores), 2 s per phase leg, liboqs 0.15.0 pinned. Median of
three runs started at 1-minute load 1.66 / 1.99 / 1.64; per-algorithm spread is
given below. **A cross-platform datapoint, not a reference measurement** — see
*Status*.

| algorithm | roles | encoder | decoder | per message | spread | per session | contended |
|---|---|---:|---:|---:|---:|---:|---:|
| **X25519** | derive/derive | 18 µs | 18 µs | **1.000** | 0.0% | 1.000 | 0.99 |
| **Ed25519** | sign/verify | 16 µs | 40 µs | **2.500** | 0.0% | 2.500 | 2.46 |
| ML-KEM-512 | encaps/decaps | 6 µs | 7 µs | 1.167 | 0.0% | 2.000 | 1.20 |
| ML-KEM-768 | encaps/decaps | 9 µs | 10 µs | 1.111 | 0.0% | 2.000 | 1.15 |
| ML-KEM-1024 | encaps/decaps | 13 µs | 16 µs | 1.231 | 0.0% | 2.231 | 1.17 |
| FrodoKEM-640-AES | encaps/decaps | 211 µs | 204 µs | 0.967 | 0.0% | 1.72 | 0.96 |
| FrodoKEM-976-AES | encaps/decaps | 365 µs | 349 µs | 0.956 | 0.3% | 1.718 | 0.96 |
| FrodoKEM-1344-AES | encaps/decaps | 637 µs | 615 µs | 0.966 | 0.2% | 1.74 | 0.96 |
| Classic-McEliece-348864 | encaps/decaps | 12 µs | 13.5 ms | **1122** | 0.4% | — | 937 |
| Classic-McEliece-6960119 | encaps/decaps | 84 µs | 56.4 ms | **671** | 1.5% | — | 611 |
| Classic-McEliece-8192128 | encaps/decaps | 48 µs | 70.1 ms | **1461** | 0.8% | — | 1270 |
| ML-DSA-44 | sign/verify | 118 µs | 36 µs | 0.305 | 2.5% | 0.305 | 0.23 |
| ML-DSA-65 | sign/verify | 199 µs | 58 µs | 0.291 | 1.0% | 0.291 | 0.24 |
| ML-DSA-87 | sign/verify | 251 µs | 94 µs | 0.376 | 2.6% | 0.376 | 0.31 |
| Falcon-512 | sign/verify | 106 µs | 16 µs | 0.151 | 0.0% | 0.151 | 0.16 |
| Falcon-1024 | sign/verify | 211 µs | 32 µs | 0.152 | 1.0% | 0.152 | 0.16 |
| SLH-DSA-SHA2-128f | sign/verify | 11.5 ms | 678 µs | 0.059 | 2.9% | 0.059 | 0.06 |
| SLH-DSA-SHA2-128s | sign/verify | 239 ms | 233 µs | **0.001** | 0.0% | 0.001 | 0.001 |
| SLH-DSA-SHA2-256f | sign/verify | 38.5 ms | 1.02 ms | 0.026 | 0.8% | 0.026 | 0.03 |

*Per message* ignores keygen (long-lived keys). *Spread* is (max−min)/median
across the three runs. *Per session* generates the keypair per exchange, the TLS
shape: for a KEM only the decoder pays it, for a DH exchange both peers do, and
for a signature it does not apply because keys are long-lived identities; it
reads "—" for Classic McEliece, whose seconds-long keygen yields too few samples
in a 2 s leg to support the figure. *Contended* is the same quantity measured
under load — how many decoder cores one encoder thread keeps busy while both
compete for the machine — rather than derived from isolated latencies. All 30
candidates are in the results files; regenerate with
`python3 analyze/asymmetry.py <file>...`.

## What an attacker pays for

The ratios above are what two *honest* peers pay. An attacker is not honest: it
sends something that will not verify, and what matters then is what the receiver
spends before it can say no. Every decoder was therefore also timed against a
corrupted wire object — a valid message with a bit flipped, which costs an
attacker nothing to produce from any message it has seen, and drives the
receiver as deep into verification as the algorithm's structure allows. It is
*not* random bytes: those are cheaper to produce but are typically thrown out by
a length or encoding check, which would understate what a receiver can be made
to do.

The unit is receiver-nanoseconds per byte the attacker put on the wire — the
defender's scarce resource over the attacker's. It is reported **per message**,
because an exchange has more than one and they are not alike:

| algorithm | encoder receives | ns/byte | decoder receives | ns/byte honest | ns/byte attacked | reject/accept |
|---|---:|---:|---:|---:|---:|---:|
| X25519 | 32 B share | **563** | 32 B share | **563** | *no rejection path* | — |
| Ed25519 | *nothing* | — | 64 B signature | 625 | **641** | 1.03 |
| ML-KEM-512 | 800 B public key | 7.5 | 768 B ciphertext | 9.1 | 9.1 | 1.00 |
| ML-KEM-768 | 1184 B public key | **7.6** | 1088 B ciphertext | **9.2** | 9.2 | 1.00 |
| ML-KEM-1024 | 1568 B public key | 8.3 | 1568 B ciphertext | 10.2 | 10.2 | 1.00 |
| FrodoKEM-976-AES | 15632 B public key | 23.4 | 15744 B ciphertext | 22.2 | 22.2 | 1.00 |
| ML-DSA-44 | *nothing* | — | 2420 B signature | 14.9 | 14.9 | 1.00 |
| ML-DSA-65 | *nothing* | — | 3309 B signature | **17.5** | **17.5** | 1.00 |
| ML-DSA-87 | *nothing* | — | 4627 B signature | 20.3 | 20.3 | 1.00 |
| Falcon-512 | *nothing* | — | 752 B signature | 21.3 | 21.3 | 1.00 |
| SLH-DSA-SHA2-128f | *nothing* | — | 17088 B signature | 39.7 | 39.7 | 1.00 |
| Classic-McEliece-348864 | 261120 B public key | **0.05** | 96 B ciphertext | 140 219 | **139 958** | 1.00 |
| Classic-McEliece-8192128 | 1357824 B public key | **0.04** | 208 B ciphertext | 337 111 | 335 615 | 1.00 |

Three things follow.

**Nothing here rejects early.** Every reject/accept ratio sits at 1.0 within
noise, because these are constant-time implementations by design — the work is
done before the answer is known. That is good for side-channel resistance, and
it means garbage traffic costs a receiver exactly what real traffic costs. The
honest column and the attacked column are the same column.

**Direction matters more than algorithm for KEMs.** A KEM has two messages and
they are not symmetric: the encapsulator receives a public key, the decapsulator
receives a ciphertext. For ML-KEM the two are close (7.6 against 9.2 ns/byte).
For Classic McEliece they differ by a factor of 2.8 million, because its public
key is enormous and its ciphertext is tiny. Quoting one number per algorithm
would be meaningless.

**X25519's missing rejection path is not good news.** It has none because every
32-byte string is a well-formed public key: there is nothing to reject, so
*everything* is processed at full cost. That is the maximally amplifying shape,
and at 563 ns/byte it is 61× worse than ML-KEM-768.

To make the unit concrete — 1 Gbps of attack traffic (125 MB/s) against the
primitive alone:

| what is flooded | bytes per message | receiver cores consumed |
|---|---:|---:|
| Ed25519 signatures | 64 | **80** |
| X25519 shares | 32 | 70 |
| ML-DSA-65 signatures | 3 309 | **2.2** |
| ML-KEM-768 ciphertexts (the client) | 1 088 | 1.2 |
| ML-KEM-768 public keys (the server) | 1 184 | 0.95 |
| Classic-McEliece-348864 ciphertexts | 96 | **17 495** |
| Classic-McEliece-348864 public keys | 261 120 | 0.01 |

These are *primitive-level bounds, not protocol attacks.* A real deployment puts
a handshake, a cookie, or a rate limiter in front of the expensive operation,
and these figures say nothing about how well it does that. They also count only
the cryptographic object: a real flood also carries the message, headers, and on
first contact a public key or certificate, all of which raise the attacker's
byte cost and so lower the true amplification. What the figures do say is what
the primitive costs once an attacker is past the gate, and how much margin each
choice leaves.

## What the numbers mean for Logos

**Signature migration bills the signer, not the verifier.** In absolute terms
verification gets ~1.45× more expensive moving Ed25519 → ML-DSA-65 (40 µs →
58 µs), while signing gets ~12× more expensive (16 µs → 199 µs). A node that
verifies many signatures and produces few — which is what consensus
participation looks like — absorbs the smaller half of the migration cost. A
node that signs at high rate does not.

**Ephemeral ML-KEM shifts key-exchange cost to the key publisher.** X25519's
symmetry is not a property PQ inherits: in TLS the client generates the ML-KEM
keypair and decapsulates while the server only encapsulates, so the client's
share grows. At ML-KEM-768 that is 8 µs of keygen plus 10 µs of decaps against
the server's 9 µs of encaps — a per-session ratio of 2.0 against X25519's 1.0.

**Flood resistance improves in the same direction, for an unrelated reason.**
Larger wire objects mean fewer messages per gigabit, and the receiver's cost is
per message. Every axis measured here moves the same way when signatures go
post-quantum.

**Falcon's keygen is a trap worth noting.** Falcon-512 verifies in 16 µs and
signs in 106 µs — attractive — but generates a keypair in 2.9 ms, 45× ML-DSA-65's
64 µs. Fine for long-lived identities, disqualifying for anything per-session.

## How much the measurements can be trusted

Three runs, medians reported, spread stated per algorithm. Most spreads are
under 1%; the largest among the meaningful ratios is 2.9% (SLH-DSA-128f). The
20% spread on SPHINCS+-128s is an artefact of rounding a ratio of ~0.001 — both
ends mean "verification is about a thousand times cheaper than signing".

**These runs were taken on a quiet but not idle machine** (1-min load 1.66 /
1.99 / 1.64 on 14 cores; a desktop with its normal background processes). A
fourth sweep was run accidentally at load 113, and comparing it against the
quiet three measures what that costs:

| | load 113 | quiet runs |
|---|---:|---:|
| X25519 derive, absolute | 24 000 ns | 18 000–19 000 ns |
| Ed25519 ratio | 2.476 | 2.500 |
| ML-DSA-65 ratio | 0.277 | 0.289–0.291 |
| Falcon-512 ratio | 0.157 | 0.151 |
| X25519 ratio | 1.000 | 1.000 |

So **absolute latency is badly distorted by competing load — 26–33% here — while
the ratios are self-normalising**, because load steals cycles from both roles
alike. A 60× difference in machine load moved the ratios by under 4%. That run
is kept in [`results/`](results) as the evidence for this claim rather than
discarded; it is not part of the medians above.

The practical consequence: the ratio columns are robust and travel. The
absolute latencies and every per-byte figure derived from them are only as good
as the machine was quiet, and should be re-measured on a dedicated box before
being used for capacity planning.

## Limitations

**One corruption shape, not all of them.** The rejection path uses a valid
message with a bit flipped — the cheap-for-the-attacker, expensive-for-the-
receiver corner. A structurally malformed input may be rejected sooner, and an
input crafted against a specific implementation may behave differently again.
The uniform ~1.0 ratios make a large surprise unlikely for these constant-time
implementations; they do not rule one out.

**Fast operations are limited by the platform's clock.** macOS resolves ~1 µs,
so a 6 µs ML-KEM-512 encapsulation lands on a coarse grid and its median ratio
can take only a few discrete values. The results carry a mean-based ratio
computed over every operation the leg completed; for anything under ~20 µs that
is the figure to prefer. Nothing above ~100 µs is affected.

**The contended phase understates the encoder.** It runs one encoder thread
against a full set of decoder threads on the same cores, so the single encoder
is oversubscribed — the multiplier it reports is a floor, not a midpoint.

**Reference-platform run: prediction confirmed, with one nuance.** The same
sweep on the Raspberry Pi 5 (`stress-rasberrypi5-20260812T043436Z`: governor
`performance`, 1-min load 0.00 at start, X25519 control 1.0004) reproduces the
structure-driven ratios: Ed25519 2.48 (vs 2.50 here), ML-KEM 1.16–1.17, ML-DSA
0.28–0.37, Falcon 0.17–0.18, SLH-DSA 0.001–0.06, FrodoKEM 0.97–1.00. An Apple
M3 median-of-three agrees as well — measured on an interactive machine at
1-min loads 3.8–8.1, and still within a few percent of the quiet-M4 medians,
which is the load-robustness claim above doing its job. The nuance is Classic
McEliece: its decaps/encaps ratio is 2–3× smaller on the Pi (307–523× against
690–1490× here), so for the table-heavy decoder the *exact* ratio is
platform-dependent — what transfers is the magnitude class, a 2.5-order
asymmetry that disqualifies it either way. The per-byte figures scale with
absolute speed as expected: a Pi buys more receiver-CPU per attacker byte, so
it remains proportionally easier to flood than these M4 figures suggest.

## Status and provenance

Stress runs carry `is_stress_grade` and never `is_baseline_grade: true`. They
cannot satisfy the reference gate — pinning to a single core would defeat the
concurrency being measured — and each file records its own
`not_reference_because` list, including the load average at which it started.
The distinct field name is deliberate: it stops a stress file from being merged
into the reference dataset by anything that only checks a flag.

Reproduce with:

```bash
cd tools/benchmarks/pqc
make build && make stress                        # one sweep; ~10 min
python3 analyze/asymmetry.py <f1> <f2> <f3>      # medians + spread across runs
python3 analyze/asymmetry.py <file> --reject     # the per-received-byte view
```

Run it on as quiet a machine as you can get, and check `run.loadavg_before` in
the output before quoting any absolute number from it.
