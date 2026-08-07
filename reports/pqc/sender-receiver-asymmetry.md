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
asymmetry.** Today's Ed25519 makes the *receiver* pay 2.48× what the sender
pays. Every PQ signature scheme measured inverts that: ML-DSA moves the cost to
the signer (0.31–0.38), Falcon further (0.16), and SLH-DSA to the point of
absurdity — SLH-DSA-SHA2-128s signs in 371 ms and verifies in 300 µs, a ratio of
0.0008. For a network whose nodes verify far more signatures than they produce,
this is the favourable direction: the migration bill lands on the side signing.

**Rejecting a bad message costs the same as accepting a good one — everywhere.**
Timed against deliberately corrupted input, all 29 algorithms with a rejection
path land between 0.91× and 1.08× of their valid-input cost. These are
constant-time implementations; none of them bails out early. So the ratios above
are not merely the honest-peer case, they are also the attack case, and the two
do not need to be reasoned about separately.

**Post-quantum is also the better direction for flood resistance, because the
messages are bigger.** An attacker spends bandwidth, not CPU, so what bounds a
flood is receiver-CPU purchased per byte sent. A 64-byte Ed25519 signature buys
875 ns of verification — 875 ns/byte. A 3309-byte ML-DSA-65 signature buys
75 µs — 23 ns/byte, **38× less**. The same holds for key exchange: X25519 is
594 ns/byte against ML-KEM-768's 10 ns/byte. PQ's large wire objects, usually
counted as a cost, are a defensive asset here.

**Classic McEliece is disqualified on this metric, by three orders of
magnitude.** Decapsulation costs 740–1770× encapsulation, and its very small
ciphertext turns that into 141 000–522 000 ns of receiver CPU per byte — a
thousandfold worse than anything else measured, ML-KEM included. Its compact
ciphertext is a real bandwidth advantage, and this is its price.

## Results

Apple M4 Pro (14 cores), 2 s per phase leg, liboqs 0.15.0 pinned, from
[`results/stress-Mac-20260807T090258Z.json`](results). **A cross-platform
datapoint, not a reference measurement** — see *Status* below.

| algorithm | roles | encoder | decoder | per message | mean | per session | contended |
|---|---|---:|---:|---:|---:|---:|---:|
| **X25519** | derive/derive | 19 µs | 19 µs | **1.00** | 1.00 | 1.00 | 0.97 |
| **Ed25519** | sign/verify | 21 µs | 52 µs | **2.48** | 2.59 | 2.48 | 2.45 |
| ML-KEM-512 | encaps/decaps | 6 µs | 7 µs | 1.17 | 1.17 | 2.00 | 1.20 |
| ML-KEM-768 | encaps/decaps | 9 µs | 11 µs | 1.22 | 1.16 | 2.22 | 1.21 |
| ML-KEM-1024 | encaps/decaps | 14 µs | 16 µs | 1.14 | 1.21 | 2.07 | 1.18 |
| FrodoKEM-640-AES | encaps/decaps | 259 µs | 285 µs | 1.10 | 1.06 | 1.94 | 0.98 |
| FrodoKEM-976-AES | encaps/decaps | 474 µs | 454 µs | 0.96 | 0.94 | 1.72 | 0.98 |
| FrodoKEM-1344-AES | encaps/decaps | 827 µs | 798 µs | 0.96 | 0.99 | 1.74 | 1.01 |
| Classic-McEliece-348864 | encaps/decaps | 12 µs | 13.6 ms | **1137** | 999 | — | 937 |
| Classic-McEliece-8192128 | encaps/decaps | 63 µs | 111.5 ms | **1770** | 1381 | — | 1270 |
| ML-DSA-44 | sign/verify | 162 µs | 50 µs | 0.31 | 0.25 | 0.31 | 0.23 |
| ML-DSA-65 | sign/verify | 259 µs | 81 µs | 0.31 | 0.27 | 0.31 | 0.23 |
| ML-DSA-87 | sign/verify | 342 µs | 131 µs | 0.38 | 0.32 | 0.38 | 0.31 |
| Falcon-512 | sign/verify | 131 µs | 21 µs | 0.16 | 0.17 | 0.16 | 0.15 |
| Falcon-1024 | sign/verify | 260 µs | 45 µs | 0.17 | 0.16 | 0.17 | 0.16 |
| SLH-DSA-SHA2-128f | sign/verify | 14.8 ms | 884 µs | 0.06 | 0.06 | 0.06 | 0.06 |
| SLH-DSA-SHA2-128s | sign/verify | 371 ms | 300 µs | **0.0008** | 0.0008 | 0.0008 | 0.0008 |
| SLH-DSA-SHA2-256f | sign/verify | 59.5 ms | 1.43 ms | 0.02 | 0.03 | 0.02 | 0.03 |

*Per message* ignores keygen (long-lived keys). *Mean* is the same ratio from
each role's mean cost per operation instead of its median — see the note on
clock granularity under *Limitations*. *Per session* generates the keypair per
exchange, the TLS shape: for a KEM only the decoder pays it, for a DH exchange
both peers do, and for a signature it does not apply because keys are long-lived
identities; it reads "—" for Classic McEliece, whose seconds-long keygen yields
too few samples in a 2 s leg to support the figure. *Contended* is the same
quantity measured under load — how many decoder cores one encoder thread keeps
busy while both compete for the machine — rather than derived from isolated
latencies. All 30 candidates are in the results file; regenerate this view with
`python3 analyze/asymmetry.py <file>`.

## What an attacker pays for

The ratios above are what two *honest* peers pay. An attacker is not honest: it
sends something that will not verify, and what matters then is what the receiver
spends before it can say no. Every decoder was therefore also timed against a
corrupted wire object — a valid one with a bit flipped, which costs an attacker
nothing to produce from any message it has seen, and drives the receiver as deep
into verification as the algorithm's structure allows.

`python3 analyze/asymmetry.py <file> --reject`:

| algorithm | wire bytes | accept | reject | reject/accept | ns per attacker byte |
|---|---:|---:|---:|---:|---:|
| X25519 | 32 | 19 µs | *no rejection path* | — | **594** |
| Ed25519 | 64 | 52 µs | 56 µs | 1.08 | **875** |
| ML-KEM-768 | 1088 | 11 µs | 11 µs | 1.00 | **10** |
| ML-KEM-1024 | 1568 | 16 µs | 16 µs | 1.00 | 10 |
| FrodoKEM-976-AES | 15744 | 454 µs | 453 µs | 1.00 | 29 |
| ML-DSA-44 | 2420 | 50 µs | 50 µs | 1.00 | 21 |
| ML-DSA-65 | 3309 | 81 µs | 75 µs | 0.93 | **23** |
| ML-DSA-87 | 4627 | 131 µs | 123 µs | 0.94 | 27 |
| Falcon-512 | 752 | 21 µs | 21 µs | 1.00 | 28 |
| SLH-DSA-SHA2-128f | 17088 | 884 µs | 887 µs | 1.00 | 52 |
| Classic-McEliece-348864 | 96 | 13.6 ms | 13.6 ms | 0.99 | **141 287** |
| Classic-McEliece-8192128 | 208 | 111 ms | 109 ms | 0.97 | **522 014** |

Two things follow.

**Nothing here rejects early.** Every ratio sits at 1.0 within noise, because
these are constant-time implementations by design — the work is done before the
answer is known. That is good for side-channel resistance, and it means garbage
traffic costs a receiver exactly what real traffic costs. It also means the
honest-peer asymmetry measured above transfers directly to the adversarial case.

**X25519's missing rejection path is not good news.** It has none because every
32-byte string is a well-formed public key: there is nothing to reject, so
*everything* is processed at full cost. That is the maximally amplifying shape,
and at 594 ns/byte it is 59× worse than ML-KEM-768.

To make the unit concrete — 1 Gbps of attack traffic (125 MB/s), against the
primitive alone:

| what is flooded | messages/s | receiver cores consumed |
|---|---:|---:|
| Ed25519 signatures | 1.95 M | **109** |
| X25519 shares | 3.91 M | 74 |
| ML-DSA-65 signatures | 37.8 k | **2.8** |
| ML-KEM-768 ciphertexts | 115 k | 1.3 |
| Classic-McEliece-348864 ciphertexts | 1.30 M | **17 700** |

These are *primitive-level bounds, not protocol attacks.* A real deployment puts
a handshake, a cookie, or a rate limiter in front of the expensive operation,
and the figures above say nothing about how well it does that. What they do say
is what the primitive costs once an attacker gets past it, and how much margin
each choice leaves.

## What the numbers mean for Logos

**Signature migration bills the signer, not the verifier.** In absolute terms,
verification gets ~1.6× more expensive moving Ed25519 → ML-DSA-65 (52 µs →
81 µs), while signing gets ~12× more expensive (21 µs → 259 µs). A node that
verifies many signatures and produces few — which is what consensus
participation looks like — absorbs the smaller half of the migration cost. A
node that signs at high rate does not.

**Ephemeral ML-KEM shifts key-exchange cost to the key publisher.** X25519's
symmetry is not a property PQ inherits: in TLS the client generates the ML-KEM
keypair and decapsulates while the server only encapsulates, so the client's
share of the handshake grows. At ML-KEM-768 that is 10 µs of keygen plus 11 µs
of decaps against the server's 9 µs of encaps — a per-session ratio of 2.2
against X25519's 1.0.

**Flood resistance improves in the same direction, for an unrelated reason.**
Larger wire objects mean fewer messages per gigabit, and the receiver's cost is
per message. Every axis measured here — who pays, and how much an attacker buys
per byte — moves the same way when signatures go post-quantum.

**The measures agree, which is the reason to believe them.** Isolated median,
mean cost per operation, and the contended head-to-head are three largely
independent ways of asking the same question, and for every algorithm they land
in the same place — X25519 at 1.00/1.00/0.97, Ed25519 at 2.48/2.59/2.45,
ML-DSA-65 at 0.31/0.27/0.23. X25519 earns its place in the sweep for exactly
this reason: its two roles are *the identical operation*, so a ratio other than
~1.0 is a bug in the role plumbing rather than a finding, and `make test`
asserts it stays there.

## Limitations

**One corruption shape, not all of them.** The rejection path is measured
against a valid message with a bit flipped. That is the cheap-for-the-attacker,
expensive-for-the-receiver case, and it is the right one to bound with — but a
structurally malformed input (wrong length, invalid encoding) may be rejected
sooner, and an input crafted against a specific implementation may behave
differently again. The uniform ~1.0 ratios make a large surprise unlikely for
these constant-time implementations; they do not rule one out.

**Fast operations are limited by the platform's clock, not by the harness.**
macOS resolves ~1 µs, so a 6 µs ML-KEM-512 encapsulation lands on a coarse grid
and its *median* ratio can only take a few discrete values. The mean is taken
over every operation the leg completed (hundreds of thousands), so for anything
under ~20 µs it is the figure to quote. Nothing above ~100 µs is affected.

**Absolute rates do not leave this machine; ratios do.** A stress run uses every
core and is deliberately unpinned, so its throughput numbers carry the host's
thermal and scheduler behaviour. The ratio between two roles measured in the
same phase, on the same silicon, at the same moment is what transfers. Repeat
runs move the ratios by a few percent (Ed25519 measured 2.35 and 2.48 on two
sweeps); treat the second decimal place as noise.

**The contended phase understates the encoder.** It runs one encoder thread
against a full set of decoder threads on the same cores, so the single encoder
is oversubscribed — the multiplier it reports is a floor, not a midpoint.

**No reference-platform run yet.** The sweep above is an Apple M4 Pro. The
ratios should be dominated by algorithm structure rather than microarchitecture,
but that is a prediction, not a measurement, until the same sweep runs on the
reference platform. The per-byte figures in particular scale with absolute
speed and will be larger on a Raspberry Pi 5.

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
make build && make stress            # full sweep; ~20 min
./stress.sh --alg ML-KEM-768         # one algorithm
python3 analyze/asymmetry.py reports/pqc/results/stress-<host>-<ts>.json
python3 analyze/asymmetry.py <file> --reject     # the flood view
```
