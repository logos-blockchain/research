# Equi-X — Future Directions and Improvements

### Volume V: the successor primitive (HashWX), the control-loop fix, and the open research agenda

*Part of the Equi-X implementation series · companion to Volumes I–IV · June 2026 · revised July 2026*

---

## 0. Scope

The first four volumes described Equi-X as it exists: how it works (I), how it's built (II), how well it resists acceleration (III), and where it sits in the landscape (IV). This volume looks forward — **what is already designed to replace or fix parts of it, what is still unverified, and what the prioritized research agenda should be.**

It draws on first-party material where possible: tevador's HashWX repository and its design document for the successor primitive, the Tor protocol specs and Proposal 362 for the deployment layer, and the recent Equihash-family cryptanalysis. It is consistent with — and extends — the Research Survey's §8 ("Future Directions") and the revised Technical Reference's §10.5 (the control loop). Where a direction is speculative, it is labeled as such.

The headline: **the primitive is conservative and probably fine; the deployed risk is economic (the effort controller); the designed successor (HashWX) is ready on paper but adopted nowhere; and the most valuable missing work is empirical, not theoretical.**

---

## 1. The successor primitive: HashWX

The most concrete "future direction" already has a repository. **HashWX** is tevador's redesign of HashX, and the HashX README now formally declares itself "superseded by HashWX." It is the natural drop-in upgrade for Equi-X's inner-hash layer.

### 1.1 What HashWX fixes

Its design document names five HashX problems — each of which Volumes I–III touched — and addresses every one:

| # | HashX problem (per HashWX design.md) | Volume cross-ref |
|---|---|---|
| 1 | Repeated multiplies accumulate trailing zeros ⇒ ~0.2% "weak" instances | II §4.1, the SUM workaround |
| 2 | 16 branches at rate 1/16 ⇒ **insufficient GPU divergence** | III §3 |
| 3 | **No memory at all** ⇒ GPUs keep VM registers in shared memory | III §3 |
| 4 | Instruction set too x86-centric ⇒ poor ARM/WASM performance | II §3.3 |
| 5 | Program generation is complex and can *fail* (~1/10⁴ seeds) | II §2.5 |

### 1.2 How it fixes them

- **Healing multiplies (problem 1).** Every multiply is fused with an entropy-preserving op: `MULOR` (`(dst|imm)*src`), `MULXOR` (`(dst^imm)*src`), `MULADD` (`(dst+imm)*src`), with odd immediates from {1, 9, 33}. Empirically these cap trailing-zero accumulation at ~4 bits (MULXOR/MULADD) or ~1 (MULOR), versus HashX's runaway zeros. Two **read-only registers R8/R9** preserve input entropy even when R0–R7 degrade (and double as the PRNG's multiplier constants).
- **Far more divergence (problem 2).** A HashWX instance is **64 sub-programs, each a loop that repeats with probability 1/2.** A CPU runs each ~2× on average (cheap, and pipeline bubbles fill by running 2 threads/core); a 32-thread GPU warp must run ~6× on average because of divergence. This is the direct answer to HashX's too-weak branch.
- **Actual memory (problem 3).** A **2 KB scratchpad**, L1-resident on a CPU (3–4 cycle latency, hideable by scheduling) but forced into higher-latency local/L2 memory (~100 cycles) on a GPU, where it competes with the L1 carve-out.
- **Portable instruction set (problem 4).** Only operations expressible in **WebAssembly 1.0** (64-bit mul/add/sub, XOR/OR, rotate/shift), 7-bit immediates for compact x86/ARM/RISC-V encoding, and an **MCG (Lehmer) generator** for branch randomness (one multiply + one rotate per output, constants 3 and 5 mod 8).
- **Simpler, infallible generation (problem 5).** A **constant number** of random draws, **no backtracking**, destination registers chosen as a permutation (so every register is written), source-register rules replaced by precomputed permutation lists. Result: **~5× faster generation than HashX, and it never fails** — which removes the `EQUIX_CHALLENGE`/`ProgramConstraints` reject path entirely.

### 1.3 Status and what adoption would mean

HashWX is **design-complete but unshipped**: the repo carries reference C, JavaScript, and a **WebAssembly JIT** (`compiler_wasm.c`), a written `specification.md`, and benchmarks (~20,000 cycles to generate, <2,400 cycles/hash compiled, ~10× slower interpreted, on Zen 2). But there is **no tagged release, no audit, and no use in Tor** — still true as of July 2026 (latest repo activity: April 2026, a design-doc fix). WebAssembly reaches ~70% of native speed, and the recommended per-instance reuse drops to **463 attempts** (65,536 in-browser) — versus Equi-X's 2¹⁶ — explicitly to make per-instance compilation dominate on a GPU.

Folding HashWX into Equi-X would be a **"v2" puzzle**: genuine (and harder-to-doubt) GPU resistance, fixed weak seeds, native cross-platform/WASM execution, and faster verification. But it is not free:

- It requires a **new `hspow-spec` scheme version** and full re-benchmarking; no such Tor proposal exists.
- HashWX is itself **unaudited**, and several of its choices (2 KB scratchpad sizing, the 64×½ branch structure) are *heuristic*, not proven — it trades HashX's known-soft GPU resistance for new, untested machinery.
- The infallible generator is a real ergonomic win (no skipped seeds), but changes the Equi-X verifier's error model.

**Direction:** HashWX is the obvious primitive-level upgrade and the clearest signal that the designer considers HashX's GPU margin too thin. Adopting it should wait on (a) an audit and (b) the empirical hardware study of Section 3 — ideally measuring HashX *and* HashWX on the same GPU to quantify the actual improvement before committing Tor to a v2.

---

## 2. The deployment layer: fix the effort controller (highest priority)

The most important "future direction" is **not** about the primitive at all. Equi-X the function is doing its job; the demonstrated weakness in deployed Tor is the **economic control loop layered on top of it.**

The OnionFlation attacks (USENIX Security 2025) game Tor's suggested-effort AIMD controller to inflate difficulty for *all* clients at ~$1.20 to trigger and ~$0.10/hour to sustain, with a proven impossibility result (no update algorithm resists both congestion and inflation simultaneously). Tor's answer is **Proposal 362, "Updating the Proof-of-Work Control Loop"** (Aptekar-Cassels; torspec#329) — a time-independent controller that makes a request count the same regardless of when in the update period it arrives, caps both suggested and accepted effort, and adds consensus parameters. As of July 2026 it is **open and unmerged**, so deployed Tor (and Arti) still run the vulnerable loop.

This is the top of the roadmap for three reasons: it is the *only demonstrated* attack on the deployed system; it is **independent of the primitive** (no HashWX migration needed); and the fix is already drafted but needs to **land and then receive independent scrutiny** — the redesign itself has had none. See the Research Survey §4/§8 and the Technical Reference §10.5; Volume III §6 explains why this, not a GPU solver, is how an attacker actually takes down a service today.

---

## 3. Empirical hardware validation (the biggest unverified assumption)

Volume III's verdict: the CPU-friendliness claim is **argued, not measured.** No public GPU, FPGA, or ASIC solver for Equi-X or HashX exists; the headline "<50% of CPU on GPU" is an extrapolation from RandomX (conservative — real RandomX GPU performance is ~6–10% of CPU — but still an extrapolation), and the comparison table literally lists Equi-X's GPU figure as "?".

The single highest-value research project is therefore to **build adversarial GPU and FPGA solvers and benchmark them.** Concretely:

- A CUDA/OpenCL Equi-X solver that JITs a kernel per challenge and measures real GPU-vs-CPU throughput, including the warp-divergence cost of the one-shot branch and the bandwidth cost of the cache-vs-local-memory sort.
- The same for HashX in isolation, and for **HashWX**, so the GPU-resistance *improvement* of the successor can be quantified before Tor commits to a v2 (Section 1.3).
- An FPGA feasibility study: soft-core vs per-challenge reconfiguration, and the real LUT cost of the modular-SUM adders vs XOR.

This would convert the design's central claim from "well-reasoned" to "demonstrated" (or refute it) and is the prerequisite for every primitive-level decision below.

---

## 4. Independent cryptanalysis

HashX's security rests on (a) Equihash/Wagner birthday hardness and (b) HashX's *claimed* preimage resistance — and **(b) has never been independently cryptanalyzed.** Open theoretical questions:

- **HashX/HashWX preimage security and weak-seed density.** The ~0.2% weak-instance figure is the author's; the SUM-binding argument that makes a non-collision-resistant inner hash safe has never been refereed.
- **How much Equihash-family cryptanalysis transfers.** Recent work is pointed but aimed elsewhere: Alcock–Ren (CCSW 2017) showed Equihash has *no proven tradeoff bound*; ePrint 2025/2141 gives a ~50%-memory / ~2×-time Wagner tradeoff plus an ASIC-friendly external-memory framework; ePrint 2025/1351 argues the **index-pointer technique weakens Equihash's ASIC-resistance** and proposes **Requihash**, explicitly extending to the **k-SUM** variant Equi-X uses. The honest assessment (Volumes III–IV): these mostly target large-n, XOR, ASIC-scale Equihash, and transfer *weakly* to Equi-X's tiny cache-resident SUM instance that abandons ASIC-resistance anyway — but the family's foundations are clearly under active, skeptical study, and **Requihash is worth evaluating as an alternative shell** if a v2 is ever opened.

**Direction:** solicit refereed analysis of HashX/HashWX specifically (not just the Equihash shell), and track the Tang–Sun–Gong line of work for any small-n / SUM result that *does* transfer.

---

## 5. Parameter retuning as hardware evolves

Equi-X's parameters are **patchable but not runtime-tunable**, and several are pinned to *today's* hardware:

- **n, k and the cache-resident working set.** The whole GPU-resistance argument depends on the ~1.8 MiB sort fitting in CPU L2/L3. As cache sizes grow and as **unified-memory architectures** (the Acceleration-Resistant Survey §12) erode the CPU-vs-GPU bandwidth gap, the "only case where CPUs compete on bandwidth" premise weakens, and n may need revisiting.
- **Instance lifetime.** 2¹⁶ hashes per HashX instance (vs HashWX's 463) is a CPU-vs-GPU-amortization knob; wider SIMD (AVX-512) or cheaper GPU JIT could shift the optimum.
- **Pipeline assumptions.** The generator models a ~12-year-old 3-port Ivy-Bridge core (Volume II §2.3); HashWX's design doc explicitly criticizes this as outdated. A retune toward modern issue widths is part of the HashWX rationale.

None of these are runtime parameters, so any change is a spec revision + re-benchmark — manageable for Tor (patchability again), but a reason to keep the empirical study (Section 3) running as hardware moves.

---

## 6. Quantum and longer-horizon questions

No Equi-X-specific quantum analysis exists. A first-principles read: Equi-X's binding cost is **memory bandwidth plus program execution, not hash inversion**, so Grover-style speedups on the inner hash are likely secondary; the more relevant question is quantum algorithms for the generalized-birthday / k-list problem, which is speculative and not obviously threatening at n=60. This is **low priority** for a patchable DoS puzzle, but worth a paragraph in any long-lived adopter's threat model — and a sharp reminder (Volume IV) that **any consensus system tempted to reuse Equi-X would inherit real ASIC risk**, since Equi-X drops ASIC-resistance by design and leans entirely on Tor's patch-ability assumption.

---

## 7. Broader adoption and the WASM/CAPTCHA bet

HashWX is explicitly aimed at a market Equi-X never entered: **browser CAPTCHA-style client puzzles**, via its WebAssembly build. The opportunity is real — today's PoW-CAPTCHA ecosystem (Anubis, ALTCHA, Cap, Friendly Captcha) still leans on Hashcash-style static SHA-256 or KDFs, all of which inherit the GPU-offload weakness HashX/HashWX were built to remove. Tellingly, **Anubis evaluated HashX/Equi-X and declined** — partly because the Rust `equix` crate runs interpreter-only under WebAssembly, handing native-compiled attackers an edge. **That is exactly the gap HashWX's WASM JIT closes**, which is why HashWX's CAPTCHA framing is the designer's bid to enter this space. As of July 2026 no CAPTCHA product has adopted it, and Equi-X adoption beyond Tor remains essentially nil.

**Direction:** a released, audited HashWX with a maintained WASM package is the precondition for any non-Tor adoption; the browser-CAPTCHA niche is the most plausible second home.

---

## 8. Concrete implementation improvements

Smaller, code-level items surfaced by Volumes I–II:

- **The bit-packed ~1 MiB solver heap.** The devlog notes the 1.81 MiB heap compresses to ~1 MiB with bit-packing at ~25% discarded solutions — "viable only for custom hardware." Not worth it for the CPU reference, but relevant to any hardware-resistance study (Section 3).
- **Retire the vestigial wide-multiply PRNG draw.** Both implementations consume an otherwise-unused `u32` per wide multiply purely for stream-compatibility (Volume II §2.4); a clean v2 could remove it — but *only* in a compatibility-breaking revision, alongside HashWX.
- **Shared, expanded conformance vectors.** The Rust crates already pin reference streams at every layer; a primitive-independent, cross-implementation conformance suite (the Volume II §7 checklist as runnable tests) would de-risk any third implementation and any v2 migration.
- **SIMD-batched verification** for services checking many proofs, where throughput (not single-proof latency) matters.

---

## 9. A prioritized roadmap

| Priority | Direction | Layer | Status / dependency |
|---|---|---|---|
| **1** | Land **Proposal 362** and have the new control loop independently reviewed | Protocol | drafted, open, unmerged; the only *demonstrated* deployed weakness (§2) |
| **2** | Build & benchmark a **GPU/FPGA solver** for Equi-X, HashX, HashWX | Empirical | none exists; gates every primitive decision (§3) |
| **3** | **Independent cryptanalysis** of HashX/HashWX; track Requihash & k-SUM results | Theory | never refereed (§4) |
| **4** | Audit HashWX, then design an **Equi-X v2** on it (new `hspow-spec`) | Primitive | depends on #2, #3; no proposal yet (§1) |
| **5** | **Retune parameters** for modern caches / unified memory / wide SIMD | Maintenance | patch-only; ongoing as hardware moves (§5) |
| **6** | **Quantum** threat-model note; explicit warning for consensus reuse | Theory | low priority (§6) |

The ordering reflects a single principle: **fix what is demonstrably broken (the control loop) first, measure what is merely assumed (hardware resistance) second, and only then change the primitive.**

---

## 10. Synthesis

Equi-X's future is unusually legible because so much of it is already written down. The deployed system's real risk is economic and has a drafted fix awaiting deployment and review (Proposal 362). The primitive's headline property — GPU/FPGA flatness — is well-argued but unmeasured, and the person best placed to judge it has already built a hardened successor (HashWX) that fixes HashX's acknowledged soft spots and targets the browser-CAPTCHA market HashX couldn't serve. The cryptographic foundations are quietly contested at the Equihash-family level, though the critiques transfer weakly to Equi-X's specific, ASIC-indifferent parameter choices.

The throughline across all five volumes is that **Equi-X's safety has always rested less on any single primitive being unbreakable than on a use case that lets it be patched.** That same property defines its future: every improvement here — a control-loop fix, a measured GPU verdict, a HashWX-based v2, a parameter retune — is something Tor can ship as an update, exactly the freedom a consensus blockchain never has. The work that remains is real, but none of it is existential, and most of it is already on someone's bench.
