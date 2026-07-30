# Adapter / Plugin Protocol

The benchmark harness is **implementation-agnostic**. Any Equi-X implementation
can be benchmarked by wrapping it in a **runner**: an executable that speaks a
tiny JSON-over-stdio protocol. The reference C and Rust runners are just two
adapters; add your own (in any language) by satisfying this contract and dropping
in a manifest.

## Contract

1. The runner reads **one** job-spec JSON object from **stdin**.
2. It performs the requested operation, measuring in-process.
3. It writes **one** result JSON object to **stdout** (the last line of stdout, so
   you may print progress/diagnostics before it — everything else goes to stderr).
4. Exit code `0` on success, non-zero on error (still print a result JSON with
   `"ok": false` and an `"error"` message when possible).

One job = one process. The harness spawns a fresh process per parameter cell so
`peak_rss_kb` is attributable.

## Job-spec (stdin)

```jsonc
{
  "schema_version": 1,
  "operation": "solve",            // "solve" | "verify" | "effort" | "hashx_compile"
  "runtime": "try-compile",        // "interpret" | "try-compile" | "must-compile"
  "repetitions": 20,               // timed iterations
  "warmup": 3,                     // untimed iterations before timing

  // solve / verify / hashx_compile:
  "challenge_hex": "deadbeef",     // hex challenge bytes (HashX seed)
  "solution_hex": "6f27...0dc9",   // verify only: 16-byte packed solution (8x u16 LE)
  "challenge_seed_hex": "abcd",    // solve/verify only, OPTIONAL, ALTERNATIVE to
                                   //   challenge_hex: each rep uses a fresh challenge
                                   //   from a SHA-256 chain over this seed
                                   //   (challenge_0 = SHA256(seed), challenge_{i+1} =
                                   //   SHA256(challenge_i)) so measurements span many
                                   //   challenges. Challenge generation, and (for
                                   //   verify) the setup solve that yields a token,
                                   //   MUST be excluded from every timed region.
                                   //   No solution_hex needed for verify: the runner
                                   //   self-solves each derived challenge.

  // effort / hashx_compile (nonce search):
  "challenge_base_hex": "abcd",    // challenge = base || little_endian(nonce, nonce_bytes)
  "nonce_bytes": 8,
  "nonce_start": 0,
  "target_effort": 1000,           // effort: stop when achieved >= target
  "max_attempts": 5000000          // effort: safety cap
}
```

Only the fields relevant to the operation are present. Unknown fields must be
ignored.

## Result (stdout)

```jsonc
{
  "schema_version": 1,
  "ok": true,
  "impl": { "name": "equix-c", "version": "1.0.0", "commit": "b7bb7d9",
            "runtime_effective": "compiled" },
  "operation": "solve",
  "runtime_requested": "try-compile",
  "runtime_effective": "compiled",         // may differ (try-compile fallback)
  "env": { "os": "linux", "compiler": "gcc-13.3.0",
           "cpu": "Intel(R) Xeon(R) ... @ 2.10GHz",  // device model string
           "arch": "x86_64",                          // x86_64 | aarch64 | ...
           "device": "cpu",                           // "cpu" | "gpu"
           "os_version": "6.18.5" },                  // kernel release; folded into the auto device label
  "runs": [                                 // one entry per TIMED rep (warmups excluded)
    { "index": 0, "wall_ns": 7582269, "solutions": 4, "compile_ns": 0,
      "attempts": 0, "achieved_effort": 0, "verify_result": null }
  ],
  "solutions_hex": ["6f27...", "..."],      // solve: final-rep solutions; effort: the winning solution; else null
  "winning_nonce_hex": "0300000000000000",  // effort only, OPTIONAL: wire bytes (LE, nonce_bytes long)
                                            //   of the winning token's nonce — lets the harness
                                            //   measure message sizes vs difficulty
  "peak_rss_kb": 4548,                      // whole-process high-water; Linux KB
  "error": null
}
```

### Field semantics per operation

| operation | must populate | notes |
|-----------|---------------|-------|
| `solve` | `runs[].wall_ns`, `runs[].solutions`, `solutions_hex` | `solutions_hex` (final rep) enables the interop cross-check. |
| `verify` | `runs[].wall_ns`, `runs[].verify_result`, `runs[].solutions` (1/0) | `verify_result` ∈ `OK`/`CHALLENGE`/`ORDER`/`PARTIAL_SUM`/`FINAL_SUM` (or impl-specific string). |
| `effort` | `runs[].wall_ns`, `runs[].attempts`, `runs[].achieved_effort` | Effort formula: BLAKE2b-256(`challenge‖solution_bytes`), `achieved = (2^32-1)/hash32` (hash32 = first 4 bytes big-endian). **Must match byte-for-byte** — the cross-check enforces it. Report the winning token via `solutions_hex` + `winning_nonce_hex` when the target was reached (enables message-size measurement). |
| `hashx_compile` | `runs[].compile_ns`, `runs[].wall_ns` | `compile_ns` = program-gen + compile; `wall_ns` = one execution. |

`solution_bytes` = the 8 solution indices as little-endian `uint16` (16 bytes).

### Device (CPU/GPU) reporting

Each runner reports the hardware it ran on in `env.cpu` / `env.arch` / `env.device`.
The harness stamps this onto every result so figures reflect the executing device
and results from different machines can be merged (`combine`). A CPU runner sets
`device: "cpu"`; **a GPU implementation would set `device: "gpu"`** and its device
name, and it then appears on the comparison figures automatically — no harness
change. Equi-X/HashX is CPU-oriented by design, so no GPU runner ships today, but
the protocol is ready for one.

## Manifest

Register an adapter by adding `<name>.manifest.toml` to a manifest directory
(default `adapters/examples/`, override with `--manifests`):

```toml
name = "my-equix"
exec = "path/to/runner"          # or ["python3", "my_runner.py"]; paths are relative to repo root
protocol_version = 1
capabilities = ["solve", "verify", "effort", "hashx_compile"]
runtimes = ["interpret", "try-compile", "must-compile"]

[env]                            # optional environment for the runner process
MY_VAR = "value"
```

The harness skips (with a warning) any cell whose operation/runtime is not in the
adapter's declared `capabilities`/`runtimes`, and any adapter whose `exec` is not
found — so a partially built tree degrades gracefully instead of crashing.

See `manifest.schema.json` for a machine-readable schema.
