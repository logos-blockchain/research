# Equi-X — Documentation Set

Equi-X is the CPU-friendly, GPU/FPGA-resistant **asymmetric client puzzle** that Tor onion services use to defend against denial-of-service (shipped in Tor 0.4.8, Aug 2023). It is `Equihash(60, 3)` with two changes: the Blake2b inner hash is replaced by **HashX** (a per-challenge randomly-generated hash function), and XOR is replaced by **modular addition mod 2⁶⁰**.

This **Equi-X Documentation** folder holds the **5-volume Markdown series** that reads the actual reference code. Its DOCX companions (the Technical Reference and Research Survey) and the broader project surveys live in the **main project folder, one level up**. This file is the index to all of them.

---

## The implementation series (Markdown)

A five-volume set built by reading the real implementations — the C reference (`tevador/equix` + `tevador/hashx`, v1.0.0) and the Rust crates (`equix` 0.6.1 + `hashx` 0.7.1, from Tor's Arti). Those are the versions *read*; as of July 2026 the C is unchanged (v1.0.0 remains the only tagged release) and the crates have moved to `equix` 0.7.0 / `hashx` 0.9.0 (June 30, 2026) with no algorithmic changes — output compatibility is frozen by the shared test vectors. The volumes cross-reference each other; read in order for a full treatment, or jump to the one matching your question.

| # | File | What it answers |
|---|------|-----------------|
| I | [Equi-X-Vol-I-Walkthrough.md](Equi-X-Vol-I-Walkthrough.md) | **How it works.** Intuition-first, data-flow walkthrough of both layers (HashX → the Equihash search), C and Rust side by side. |
| II | [Equi-X-Vol-II-Deep-Analysis.md](Equi-X-Vol-II-Deep-Analysis.md) | **How it's built.** Rigorous C↔Rust correspondence, the generator/scheduler internals, solver complexity & birthday math, memory, determinism, security. |
| III | [Equi-X-Vol-III-Attacking-and-Accelerating.md](Equi-X-Vol-III-Attacking-and-Accelerating.md) | **How well it holds up.** Optimized solving, GPU/FPGA/ASIC feasibility grounded in the code, and an honest verdict on the CPU-friendliness claim. |
| IV | [Equi-X-Vol-IV-PoW-Landscape.md](Equi-X-Vol-IV-PoW-Landscape.md) | **Where it fits.** Lineage and placement against RandomX, Equihash, Argon2/yespower, Cuckoo Cycle, ProgPoW, on the time/memory/bandwidth axes. |
| V | [Equi-X-Vol-V-Future-Directions.md](Equi-X-Vol-V-Future-Directions.md) | **What's next.** HashWX (the successor primitive), Proposal 362 (the control-loop fix), and a prioritized open-research roadmap. |

### Where to start

- **New to Equi-X?** Volume I, then II.
- **Implementing or porting it?** Volumes I–II (II §7 is the bit-exact compatibility checklist).
- **Evaluating its security / hardware resistance?** Volume III, then V §3.
- **Choosing a PoW / comparing designs?** Volume IV.
- **Planning the next version?** Volume V.

---

## The book (single-source consolidation)

Everything below — the five volumes, the Technical Reference, the Research Survey, and a component-by-component C↔Rust implementation study — is consolidated, de-duplicated, and fact-checked into one book:

- **[Equi-X: The Complete Reference](../Books/Equi-X-Complete-Reference.pdf)** (`Books/Equi-X-Complete-Reference.pdf`; LaTeX source alongside it). If you read only one document, read this one.

---

## The reference documents (DOCX)

Specification- and survey-grade companions to the code series. The `-revised` copies are the current versions (originals retained).

- **[Equi-X-Technical-Reference-revised.docx](../Equi-X-Technical-Reference-revised.docx)** — implementation-grade specification of the algorithm and the Tor integration (the *what*, to the series' *how*).
- **[Equi-X-Research-Survey-revised.docx](../Equi-X-Research-Survey-revised.docx)** — the literature/landscape survey: the design record, independent scrutiny (OnionFlation, Proposal 362), and HashWX.

---

## Broader project context

The volumes cross-reference these wider surveys in the main project folder (one level up), which place Equi-X within the larger proof-of-work space:

- **Acceleration-Resistant-PoW-Survey.docx** — the master taxonomy (Families A–F, the three parameter axes) that Volume IV builds on.
- **RandomX-Research-Survey.docx** / **RandomX-Technical-Reference.docx** — Equi-X's direct ancestor (HashX descends from RandomX's SuperscalarHash).
- **Memory-Latency-Bound-Functions.docx** — theory background on the egalitarian/CPU-friendly thesis.
- **PoW-Design-Discussion-DoS-and-Mining.docx** — the DoS-vs-consensus framing.

---

## Source & provenance

The series is derived from primary sources: the reference C and Rust code, tevador's `equix` devlog, the HashWX design document, the Tor `hspow-spec` and Proposal 362, and the cited academic papers — with constants and code claims verified against the source, and 2020-era figures updated against 2026 evidence where they had aged. Compiled June 2026; revised July 2026 (all code snippets re-verified against the sources, crate-version currency noted, status lines re-checked: Proposal 362 still open, HashWX still unreleased, still no public GPU/FPGA solver).
