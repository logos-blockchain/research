# QUIC handshake — what a hybrid key exchange costs

Measures a QUIC handshake with `X25519` against one with `X25519MLKEM768`, on
the real quinn + rustls stack, for the post-quantum transport RFC (phase 0).

```bash
make check     # read-only environment check
make record    # both arms + packet trace -> results/<machine>.txt
```

## The question this exists to answer

We already have handshake numbers for the hybrid group from the PQC benchmark
(`reports/pqc`), but they are **TCP-TLS**, where the concern is a handshake
outgrowing a packet. QUIC behaves differently in two ways that pull in opposite
directions, and neither is obvious without measuring:

- a QUIC client's Initial is padded to at least 1200 bytes whatever it carries,
  so a bigger ClientHello may cost nothing until it spills into a second
  datagram — and
- a server may not send more than 3× what it has received before validating the
  peer's address, so a bigger client flight *raises* the server's allowance.

## What is held constant

The two arms differ in `kx_groups` and nothing else. TLS 1.3, the cipher
suites, the self-signed certificate and the ALPN are identical, so the delta is
attributable to the key exchange.

The absolute numbers are shaped like libp2p's handshake — same suites, same
self-signed certificate with no CA chain — but this is **not** libp2p: there is
no peer-identity extension and no custom verifier. Those cost the same in both
arms, so they do not affect the comparison, but it means the absolute byte
counts are a close model rather than a capture of production traffic.

## Reading the output

**`make record` reports two things, and only one of them is trustworthy.**

The **datagram counts, byte totals and flight structure are
protocol-determined**: they follow from the 1200-byte Initial padding and the
size of the ClientHello, not from the CPU. They reproduce exactly across runs
and will be identical on any machine. These are the results.

The **wall-clock number is not usable**. On loopback it is dominated by async
scheduler wakeups rather than by cryptography: repeated runs of the *same* arm
on the same machine have spanned 0.6–2.0 ms. It is printed for completeness and
should not be quoted. The CPU cost of the key exchange is small and already
measured properly elsewhere — ML-KEM-768 is 9 µs to encapsulate and 10 µs to
decapsulate on the reference Pi 5 (`reports/pqc`), tens of microseconds against
a handshake measured in milliseconds.

This is why there is no per-machine results matrix here: the meaningful
quantities do not vary by machine, and the quantity that does is measured
better by the PQC benchmark.

## Results

`results/<machine>.txt`, written by `make record`, stamped with the CPU and
toolchain that produced it.

Summary of the current run:

| | X25519 | X25519MLKEM768 |
|---|---|---|
| client first flight | 1 datagram, 1200 B | **2 datagrams, 2400 B** |
| handshake total | 5202 B | 7653 B (**×1.47**) |
| round trips | — | **unchanged** |

The flight structure is identical in both arms — client flight, server flight,
client flight — so the hybrid group costs no additional round trip. On a real
link, where latency is set by RTT rather than by CPU, that is the number that
matters.

One run in three produced one extra client datagram (6 rather than 5), most
likely a retransmission; the trace and the other quantities were unchanged.
