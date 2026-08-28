# Block proposal compression

Research supporting the compressed block proposal, [logos-lips#389].

| Report | Question it answers |
|---|---|
| [reference-prefix-length.md](reference-prefix-length.md) | How many bytes of the transaction hash must a block proposal carry to refer to a transaction? Prices the birthday-collision attack against measured generation rates, and reconstruction cost against a measured latency curve on the target validator. |

Benchmark suite: [`tools/benchmarks/block-proposal/reference-prefix-length`](../../tools/benchmarks/block-proposal/reference-prefix-length/).

Start with the report's **Notation and terms** section if you are picking this up
cold — every symbol used (`L`, `k`, `b`, `n`, `R_gen`) is defined there.

[logos-lips#389]: https://github.com/logos-co/logos-lips/pull/389
