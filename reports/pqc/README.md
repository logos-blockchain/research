# Post-quantum cryptography — migration-cost measurements

*Benchmark: [`pqc`](../../tools/benchmarks/pqc). Reference platform: **Raspberry Pi 5** (Broadcom BCM2712, Cortex-A76, aarch64). All latencies are medians; TLS byte counts are on-the-wire handshake totals.*

This directory holds the measurement record for the question *what does it cost
to move Logos from the cryptography it uses today — X25519 key exchange and
Ed25519 signatures — to post-quantum candidates?* Every run measures the
classical baseline alongside the PQ candidates on the same machine in the same
pass, so the PQ "tax" is a ratio measured under identical conditions rather than
a comparison across sources.

Everything the benchmark produces lands here:

| what | where | produced by |
|---|---|---|
| per-run results (one self-describing JSON per run) | [`results/`](results) | `make run` |
| role-asymmetry stress runs (`stress-*.json`) | [`results/`](results) | `make stress` |
| exported figures | `figures/` | `make figures` |
| written analysis | this directory | by hand, from the above |

Analyses published here so far:

- [Sender/receiver asymmetry](sender-receiver-asymmetry.md) — which side of an
  exchange pays, measured with both sides running flat out, and how migrating
  to PQ changes the answer.
- [Does the benchmark need sudo?](sudo-and-measurement-conditions.md) — what
  the one privileged step buys, what a run without it loses, and how to remove
  the need for it entirely.

The one deliberate exception is `dashboard/data/merged.json`, which stays in the
tool: it is not a result but the dashboard's input, fetched by a relative path so
the static dashboard stays deployable on its own. `make merge` regenerates it
from the runs in [`results/`](results).

## Published dataset

Four runs make up the current published set. Membership is explicit — a run is
published by listing it in
[`analyze/published_runs.txt`](../../tools/benchmarks/pqc/analyze/published_runs.txt)
and un-ignoring it in [`results/.gitignore`](results/.gitignore) — so an ad-hoc
local run can never drift into the dataset by accident.

| run | machine | OS | duration | baseline-grade |
|---|---|---|---|---|
| `rasberrypi5-20260730T212145Z` | Raspberry Pi 5 Model B Rev 1.1 | Debian 13 (trixie) | 1692 s | **yes** — the reference run |
| `mehmetmac-20260719T224937Z` | Apple M3 | macOS 26.3.1 | 2172 s | no |
| `Mac-20260730T134951Z` | Apple M4 Pro | macOS 26.6 | 1212 s | no |
| `fedora-20260730T120637Z` | Intel Core Ultra 9 285HX | Fedora 44 | 394 s | no |

Only the Pi 5 run is **baseline-grade**: measured on the reference platform with
the CPU governor at `performance`, pinned to an isolated core, with a thermal
trace showing no throttling. The other three are cross-platform datapoints —
useful for the shape of the results, not for the reference numbers. Each file
stamps its own `is_baseline_grade` flag and the reasons it failed the gate, so
the distinction survives outside this table.

Earlier runs remain in [`results/`](results) as history. They are retired rather
than deleted: they predate the schema-2.0.0 measurement groups and the SLH-DSA
rename, and one of them
(`rasberrypi5-20260614T205226Z`) is load-bearing as the schema-1.0.0
compatibility fixture for `make test`.

## Headline

On the reference Pi 5, the honest summary is that **post-quantum is not so much
slower as bigger.**

- **Hybrid key exchange (phase 0, hedging against harvest-now-decrypt-later)
  costs ×1.26 in handshake latency and ×2.49 in handshake bytes** —
  X25519 + Ed25519 at 1.291 ms / 1518 B versus X25519MLKEM768 + Ed25519 at
  1.633 ms / 3782 B, both on OpenSSL-native. The latency cost is modest; the
  size cost is what pushes the handshake past a single packet.
- **The TLS stack matters more than the algorithm.** Across the 14 handshake
  cells measured on both stacks, rustls + aws-lc-rs completes the same handshake
  **2.1–3.8× faster** than OpenSSL-native — smallest on classical and
  hybrid-KEM cells (×2.1–2.5), largest once ML-DSA signatures are in play
  (×3.3–3.8). Choosing the implementation is worth more than any single
  algorithm choice at this layer.

The per-algorithm detail — KEM and signature primitives across liboqs,
RustCrypto and aws-lc-rs, and the full three-stack TLS phase matrix — is in the
result files and rendered by the tool's dashboard (`make dashboard`).

## Reproducing

From [`tools/benchmarks/pqc`](../../tools/benchmarks/pqc):

```bash
make check     # read-only environment check; prints what to install
make build     # vendored liboqs + pinned OpenSSL + oqs-provider + Rust harnesses
make test      # ~1-2 min verification gate before spending 30 min measuring
make run       # the full benchmark; writes reports/pqc/results/<host>-<ts>.json
make merge     # fold the published set into the dashboard dataset
make figures   # export PNGs into reports/pqc/figures
```

`make where` prints the exact results and figures directories the tool will use.
A reference-grade run needs the reference platform and its measurement
conditions — see
[the benchmark's README](../../tools/benchmarks/pqc/README.md#is_baseline_grade)
for what `is_baseline_grade` requires and why a run that misses it is still
worth keeping.
