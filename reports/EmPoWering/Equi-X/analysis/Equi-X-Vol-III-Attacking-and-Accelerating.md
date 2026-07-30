# Equi-X — Attacking and Accelerating

### Volume III: how hard is it *really*? Optimized solving, hardware feasibility, and an honest verdict on the CPU-friendliness claim

*Part of the Equi-X implementation series · companion to Volumes I (Walkthrough), II (Deep Analysis), IV (PoW Landscape), V (Future Directions) · June 2026 · revised July 2026*

---

## 0. Scope

Volumes I and II explained what Equi-X computes and how the C and Rust implementations build it. This volume turns adversarial: **assume you want to solve Equi-X as cheaply and as fast as possible — how far can you get, and where does the design stop you?** That question is the entire point of the algorithm (its third and "most important" requirement is that GPUs and FPGAs gain little advantage), and it is the open problem the project's Research Survey flags as highest-value.

The analysis is grounded in the code (Volumes I–II) and in tevador's own design log, which contains the only first-party hardware-resistance reasoning that exists. Where the devlog's 2020-era empirical claims have aged, this volume corrects them against 2026 evidence. Absolute performance figures are approximate and hardware-specific; the structural arguments are what matter.

A framing note up front: Equi-X is a **DoS puzzle, not a mining function**. The attacker's goal is not to win a block race but to *impersonate many legitimate clients cheaply* — to solve at volume for less than the defender assumes, or to turn the puzzle itself into a DoS vector. That changes which attacks matter, as Section 6 shows.

---

## 1. What "winning" means for an attacker

The reference design states three requirements and one explicit non-goal (devlog):

1. Proof < ~200 bytes — *Equi-X solutions are 16 bytes.*
2. Verification must be fast — *~50 µs, exact, no memory.*
3. **GPUs/FPGAs must not provide a large solving advantage** — "the most important one."
4. **ASIC-resistance is explicitly NOT required** — a 28 nm ASIC costs >US$1M, and Tor can change the algorithm with a patch, unlike a consensus blockchain.

So an attacker "wins" by achieving any of:

- **(A) A large per-dollar solving speedup on commodity parallel hardware** (GPU/FPGA), letting them mint solutions far faster than a browser CPU. This is the threat the design targets.
- **(B) Making verification expensive** (a junk-proof flood). The asymmetric verifier is the defense.
- **(C) Attacking the protocol economics around the puzzle** rather than the puzzle itself — precomputation, or gaming the effort controller. In practice this is where the deployed system is actually weak (Section 6).

ASIC silicon-proofing is *not* on the attacker's win list from the defender's perspective, because the defender's answer to an ASIC is a one-line algorithm patch. We return to that asymmetry in Section 5.

---

## 2. Accelerating the CPU solver

Before reaching for exotic hardware, how much headroom does the *reference CPU solver* leave? First, where the time goes (Volume II, §9):

> A solve is **dominated by the 2¹⁶ = 65,536 HashX evaluations in stage 0.** Program generation is ~0.05 ms; the three bucket passes are `Θ(2¹⁶)` and cheap next to the hashing; HashX overhead is "under 1%" of an attempt (devlog). So *accelerating Equi-X ≈ accelerating HashX throughput*, with the bucket sort a distant second.

That single fact shapes every optimization:

**Batching and SIMD.** The reference evaluates indices one at a time. A throughput solver wants to run many hash evaluations in parallel lanes. But HashX resists data-parallelism at the instruction level: each hash is a **single dependent chain of ~512 integer ops filling ~195 cycles** (Volume II, §2.5), dominated by `MUL`/wide-multiply latency, with almost no instruction-level parallelism *within* one hash. You can run *different* indices in different SIMD lanes, but the chain is full of 64×64→128 multiplies and one-shot input-dependent branches, which vectorize poorly (no wide-lane high-multiply on common SIMD; divergent branches break lockstep). The practical CPU win is *thread-level* parallelism across indices (the reference already uses 16 threads for ~2400 Sol/s) plus the JIT — not lane-level SIMD inside a hash. The JIT already captures most of the win; the interpreter is ~10× slower and exists mainly as the portable spec.

**The bucket sort: a known memory–time knob.** The solver heap is 1.81 MiB "with negligible solution discarding," and the devlog notes it "could be reduced to a minimum of 1 MiB with perfect bit packing and around 25% of discarded solutions, although this is viable only for custom hardware." That is a real memory–time tradeoff, but it cuts the *cheap* part of the solve (the sort), not the dominant hashing, and it costs solutions — so it does nothing for a CPU attacker and only matters when squeezing a hardware datapath (Section 4–5).

**The 2025 Wagner memory–time tradeoffs, and why they barely touch Equi-X.** Recent cryptanalysis — ePrint 2025/2141, *"Memory Optimizations of Wagner's Algorithm with Applications to Equihash"* (Tang, Ding, Sun, Gong; TCHES 2026) — gives a near-linear tradeoff that **halves Wagner's peak memory (2nN → nN bits) for ~2× time across all Equihash parameters**, plus an "ASIC-friendly framework leveraging an external-memory caching mechanism." This is significant for *large* Equihash (Zcash's 144 MiB, BTG's 2.5 GiB), where peak memory is the binding constraint. For **Equi-X it is largely moot**: the working set is already ~1.8 MiB and *deliberately cache-resident*, so halving it buys nothing a CPU cares about, and the "external-memory caching" framing is precisely the ASIC/large-memory regime Equi-X engineered itself out of. The companion paper (ePrint 2025/1351, *Single or K Lists?*) is more pointed — it argues Equihash's **index-pointer technique weakens ASIC-resistance** and proposes *Requihash* — and it explicitly extends to the **k-SUM** variant Equi-X uses. But its target is ASIC-resistance, which Equi-X never claims; see Section 5.

**Bottom line for CPU:** the reference solver is already near the achievable envelope — JIT + threads + cache-resident sort. The interesting question is whether *other* hardware can beat a CPU at all.

---

## 3. GPU feasibility, grounded in the code

This is requirement #3, the one that matters. The structural reasons a GPU struggles with Equi-X are all visible in the implementation:

- **Per-instance code generation.** Every challenge produces a *different* 512-instruction program (Volume I, §3). A GPU can't bake Equi-X into a fixed kernel; it must JIT a new kernel (or interpret) for each challenge, and that cost is amortized over only **2¹⁶ hashes per instance** — small. (The successor HashWX slashes this to **463 attempts per instance**, deliberately, to make per-instance compilation dominate on a GPU.)
- **Latency-bound hashes, not throughput-bound.** Each hash is a ~195-cycle dependent multiply chain with near-zero internal ILP (Section 2). GPUs win on throughput over thousands of independent threads, but each Equi-X hash is serial and multiply-heavy; you need enormous occupancy to hide the latency, and the integer-multiply units are the bottleneck.
- **Warp divergence from the one-shot branch.** HashX's input-dependent branch (≈1/16) was *added specifically to hinder GPUs* (devlog). On a 32-thread warp, divergent branches serialize. (HashWX's design doc concedes 16 branches at 1/16 is *insufficient* divergence — which is exactly why HashWX moves to 64 sub-programs each looping with probability 1/2.)
- **Cache-residency neutralizes the GPU's trump card.** A GPU's main edge is memory bandwidth. Equi-X's ~1.8 MiB sort fits in CPU L2/L3, "the only case when CPUs can compete with GPUs in memory bandwidth" (devlog). On a GPU the sort lands in higher-latency local/L2 memory.

**What the evidence actually says.** As of July 2026, **no public GPU (or FPGA or ASIC) solver for Equi-X or HashX exists** — confirmed by exhaustive search (re-checked July 2026) and by the author's own devlog footnote: *"No GPU implementation exists; upper bound based on RandomX performance."* The headline "<50% of CPU" is therefore an **extrapolation, not a measurement**, and the comparison table lists Equi-X's GPU figure as literally "?".

How good is that extrapolation? It rests on RandomX's GPU behavior via `SChernykh/RandomX_CUDA`. A crucial subtlety the devlog glosses: that project's oft-quoted ~144–153% figures are **GPU-vs-old-GPU-algorithm, not GPU-vs-CPU**. Measured GPU-vs-CPU for RandomX is roughly **6–10%** (a top GPU ~2000 H/s vs a top CPU ~28,000–31,000 H/s). So if HashX/Equi-X resemble RandomX on a GPU, **"<50%" is conservative** — the real figure could be far lower. That is the optimistic reading.

The honest, pessimistic reading is equally important: **the designer himself is no longer confident.** HashWX's design document lists HashX's GPU weaknesses plainly — too few branches at too low a rate, and *no memory at all*, so "GPUs can achieve good interpreter performance while storing VM registers in shared memory." HashWX exists *because* HashX's GPU resistance was softer than first implied. So the defensible verdict is: **probably GPU-resistant, plausibly by a wide margin, but unproven — and the primitive's own author has shipped a redesign to shore it up.**

---

## 4. FPGA feasibility

FPGAs are the reason the Equihash layer exists at all. The devlog: *"I still felt a bit uneasy about HashX using no memory. This means that logic-only FPGAs could be a viable option to run HashX."* Three code-level facts bound an FPGA attack:

- **HashX is essentially a tiny CPU.** A per-instance program means an FPGA can't hard-wire one datapath; it must either reconfigure per challenge (bitstream generation is far slower than a CPU JIT) or implement a *soft processor* that interprets HashX — and a soft-core on an FPGA fabric will not out-run a hardened CPU at integer multiply chains.
- **The memory layer forces storage.** The ~1.8 MiB sort gives a logic-only FPGA something it must hold in block RAM, and the bandwidth-bound sort doesn't favor the fabric the way bespoke pipelines would.
- **SUM, not XOR, taxes the adders.** Equi-X sums hashes mod 2⁶⁰ instead of XORing them. "XOR is much faster in custom hardware… an FPGA-based solver will have to use slightly more resources to calculate the modular additions" (devlog). The carry chains cost real LUTs/area at scale.

No public FPGA solver exists. By analogy, FPGA attempts at RandomX (a close relative) are non-competitive: low clock speed and memory-latency bottlenecks mean "only an ASIC can outperform" the CPU. Equi-X's FPGA story is plausibly stronger still, because the per-instance program defeats fixed pipelines. **Verdict: FPGA acceleration is unlikely to beat a CPU, though — like the GPU case — this is reasoned, not demonstrated.**

---

## 5. ASIC feasibility — and why it's deliberately off the table

Equi-X **drops ASIC-resistance by design**, for two stated reasons: a 28 nm ASIC exceeds ~US$1M (un-amortizable against one victim), and Tor can swap the algorithm with a patch. An ASIC attacker would build a small CPU-like core (the HashX VM: 8 registers, integer ALU with fast multiply, one branch unit) plus modular adders and ~1.8 MiB of on-die SRAM, replicated for parallel attempts.

How much would that win? The most instructive data point is **RandomX, which *does* target ASIC-resistance and got ASIC'd anyway**: Bitmain's Antminer **X5** (2023) and **X9** (late 2025; ~1 MH/s at ~2.5 kW) are real commercial RandomX ASICs. But their edge is only **~3× CPU energy-efficiency — right at tevador's own predicted single-die ceiling** — a far cry from the millions-fold gap of SHA-256 ASICs. The lesson generalizes: a program-execution PoW caps the ASIC advantage at "a better CPU," not "a different universe." A hypothetical Equi-X ASIC would likely land in the same low-single-digit multiple — meaningful for a consensus coin, **irrelevant against a target Tor can re-key with a patch and that costs an attacker far less to DDoS by other means.**

The 2025 cryptanalysis (ePrint 2025/2141's external-memory ASIC framework; 2025/1351's index-pointer critique and *Requihash*) sharpens the ASIC picture for the **Equihash family at large-n** — but its relevance to Equi-X is limited precisely by Equi-X's choices: tiny cache-resident n=60, modular SUM rather than XOR, and the explicit abandonment of ASIC-resistance as a goal. **Verdict: an Equi-X ASIC is buildable and would win a bounded ~few× margin — and that's fine, because silicon-proofing was never the defense. Patchability is.**

---

## 6. The real attack surface: economics, not silicon

For a DoS puzzle the decisive question isn't "can you build faster hardware" but "can you make the *defended system* cheap to overwhelm." Here the code and the deployment diverge, and the honest answer is that **the deployed weakness is the protocol around Equi-X, not Equi-X.**

- **Precomputation is bounded but real.** Seeds rotate every ~105 min–2 h, and the challenge binds the server seed, the blinded service identity, and a client nonce (Volume I). Within a seed window an attacker can pre-mine solutions, but each `(seed, nonce)` is replay-checked, and effort is a *linear bid* rather than a fixed target — so precomputation buys a burst at seed rollover, not a standing advantage.
- **Verification flooding is well-defended.** The verifier is ~50 µs, checks the *ordering constraint first with no hashing*, and rebuilds the hash only if order passes (Volume II, §6). Junk proofs are rejected almost for free; the puzzle does not become a DoS vector on itself.
- **The control loop is the soft underbelly.** The genuinely demonstrated attack on deployed Tor is **OnionFlation** (USENIX Security 2025): gaming the suggested-effort AIMD controller to inflate difficulty for *all* clients for ~$1.20 to trigger and ~$0.10/hour to sustain — with a proven impossibility result that no estimator resists both congestion and inflation at once. This attacks the *economics*, not the primitive; Tor's response is **Proposal 362** (open, unmerged as of July 2026). See the Research Survey and the Technical Reference §10.5; this is also Volume V's top priority.

In other words: an attacker who wants to take down an onion service does **not** build an Equi-X GPU solver — they game the control loop. The primitive is doing its job; the surrounding protocol is where the value is.

---

## 7. Verdict: does the CPU-friendliness claim hold?

A scorecard, by requirement:

| Property | Status | Basis |
|---|---|---|
| Small proof (<200 B) | **✓ proven** | 16 bytes, by construction |
| Fast, cheap verify | **✓ proven** | ~50 µs, exact, memoryless, order-checked first |
| GPU resistance | **✓ likely, UNPROVEN** | no public solver; "<50%" extrapolated from RandomX (conservative — real RandomX GPU is ~6–10% of CPU); but the author shipped HashWX to harden known gaps |
| FPGA resistance | **✓ plausible, UNPROVEN** | register-only HashX + cache-resident SUM sort; per-instance program defeats fixed pipelines; no public solver |
| ASIC resistance | **✗ by design** | abandoned deliberately; bounded ~few× (cf. RandomX's ~3× ASIC); defense is patchability + economics |
| Resistance to economic attack | **✗ at the protocol layer** | OnionFlation games the effort loop; fix (Prop 362) not yet deployed |

The structural case for CPU-friendliness is strong and coherent — per-instance latency-bound programs, an anti-GPU branch, modular-SUM, and a cache-resident sort all push in the same direction, and a decade of the RandomX family shows program-execution PoW caps specialized-hardware gains at low multiples. But the **central claim rests on an extrapolation, not a demonstration**, and the designer's own successor signals the margin is thinner than the "<50%" headline suggests.

The single highest-value adversarial project, therefore, is the one nobody has published: **build a real GPU (and FPGA) Equi-X/HashX solver and measure it.** Until then, "GPUs gain little" is a well-argued, conservatively-extrapolated, but still *unverified* claim — and that gap, not any ASIC, is the most interesting thing an attacker (or an honest researcher) could close. Volume V puts this at the top of the open agenda.
