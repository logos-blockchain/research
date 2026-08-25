# Equi-X in the Proof-of-Work Landscape

### Volume IV: lineage, family placement, and where Equi-X sits on the time / memory / bandwidth axes

*Part of the Equi-X implementation series · companion to Volumes I–III and V · June 2026 · revised July 2026*

---

## 0. Scope

Volumes I–III looked inward at the algorithm and its implementations. This volume looks outward: **where does Equi-X fit among proof-of-work designs, what did it inherit from its ancestors, and why are its specific choices the right ones for its niche?**

It is written to dovetail with two existing project documents and uses their vocabulary deliberately: the **Acceleration-Resistant PoW Survey** (which classifies the field into Families A–F along three parameter axes) and the **RandomX Research Survey** (whose §8.2 traces the "HashX → Equi-X → HashWX" successor lineage). The thesis here is simple and, once seen, hard to unsee:

> **Equi-X is a deliberate hybrid of two PoW families** — it grafts the CPU-binding *program-execution* core of Family D (the RandomX lineage) onto the asymmetric, small-proof, fast-verify *birthday-search shell* of Family B (Equihash), and then tunes every parameter for **denial-of-service defense rather than consensus mining.** Almost everything distinctive about it follows from that one sentence.

---

## 1. The axes, and the niche

The Acceleration-Resistant Survey frames hardware resistance along **three parameter axes** — compute/time, memory/space, and bandwidth/energy — and distinguishes *absolute* resistance (no one can do better) from *economic* resistance (no one can do better cheaply enough to matter). Two more distinctions matter for placing Equi-X:

- **Consensus mining vs. DoS defense.** A mining PoW is run continuously by adversarial profit-maximizers and must resist amortization over millions of dollars of hardware for years. A DoS puzzle is run occasionally by ordinary clients and need only make *bulk* solving uneconomic for an attacker who could otherwise impersonate many clients — and, crucially, it can be **re-keyed with a software patch** if broken. Equi-X is squarely the second kind.
- **Where Equi-X sits on the axes: tiny on all three.** ~1.8 MiB memory, ~6–8 ms solve, ~50 µs verify, 16-byte proof. It is not trying to be expensive; it is trying to be *flat* — equally cheap on a CPU and on an attacker's GPU. That is a different objective from almost every mining PoW in the landscape, and it explains why a direct "which is more ASIC-resistant" comparison often misses the point.

---

## 2. Parent #1 — Family D, the program-execution lineage

Equi-X's inner hash is the end of a clear genealogical line within Family D (CPU/VM program-execution functions):

```text
CryptoNight  ─►  RandomX  ─►  SuperscalarHash  ─►  HashX  ─►  (HashWX)
 (2013-19)      (Monero,      (RandomX's DAG-     (Equi-X's    (successor,
                 2019)         init component)     inner hash)   Vol V)
```

The decisive move, in tevador's own words (devlog): *"I remembered SuperscalarHash, which is a part of RandomX that's used only to initialize the DAG… a lightweight version of RandomX with only integer operations and no memory accesses."* HashX is a refactored, hardened SuperscalarHash: a faster generator (250 µs → 50 µs), reciprocal multiplication removed, a better JIT, and — the anti-GPU addition — input-dependent branches. The **per-instance random program** is the Family D signature: instead of a fixed compression function an attacker can bake into silicon, every challenge is a *new* function that must be (re)compiled, which is what binds the work to a general-purpose CPU.

What Equi-X inherits from this parent: CPU-friendliness, GPU/FPGA resistance via per-instance code + a dependent multiply chain + a divergent branch, and the JIT machinery. What it deliberately *sheds*: RandomX's heavy memory and slow verification (Section 5).

---

## 3. Parent #2 — Family B, the asymmetric birthday-search shell

The outer structure comes from Family B (asymmetric / proof-size PoW), whose lineage is:

```text
Momentum (2013)  ─►  Equihash (2016)  ─►  Equi-X (Equihash with SUM, not XOR)
                       Cuckoo Cycle (2014) ── asymmetric cousin (different problem)
```

Family B's appeal for a *client puzzle* is exactly its asymmetry: a memory-assisted **generalized-birthday search** to find a solution, but a tiny proof and a near-instant check. Equihash gives "find 2^k hashes that combine to zero," with memory-hardness ∝ 2^(n/(k+1)) and verification of just 2^k hash evaluations. That is precisely the small-proof/fast-verify profile a DoS puzzle needs (requirements #1 and #2).

Equi-X's one substantive change to this parent is the combiner: **modular addition instead of XOR** (the "k-SUM" variant from Wagner's original paper). Volume II §4.1 and the Research Survey cover *why* (it neutralizes HashX's collision-weak instances and taxes hardware adders); here the point is genealogical — Equi-X is Equihash's structure with a different group operation and a different inner hash.

---

## 4. Equi-X as a hybrid — which property comes from which parent

| Property | Inherited from | Mechanism |
|---|---|---|
| CPU-binding / GPU-FPGA resistance | **Family D (HashX/RandomX)** | per-instance random integer program; dependent multiply chain; one-shot branch |
| Small proof (16 B) + fast verify (50 µs) | **Family B (Equihash)** | asymmetric birthday search; verify = 8 hashes + 7 adds |
| Memory-hardness (~1.8 MiB, cache-resident) | **Family B**, tuned | n=60/k=3 sized to fit CPU cache |
| Weak-seed safety + hardware adder tax | **Equi-X's own tweak** | 2^k-SUM instead of 2^k-XOR |
| ASIC-resistance | **neither — abandoned** | DoS use case + patchability (Section 6) |

No other deployed PoW occupies this exact intersection. RandomX is Family D without the asymmetric shell (heavy verify). Equihash is Family B without the program-execution core (GPU-friendly). Equi-X is the graft of the two, which is why it is essentially *sui generis* among shipped algorithms.

---

## 5. Head-to-head on the axes

The devlog's own comparison tables, updated against 2026 reality, place Equi-X against its neighbors. (Figures are tevador's, on a Ryzen 1700 / GTX 1660 Ti unless noted; "GPU %" is GPU speed relative to CPU — **lower is better for a client puzzle**.)

| Algorithm | Family | Memory | Verify | Proof | GPU vs CPU | Niche |
|---|---|---|---|---|---|---|
| **Equi-X** | B×D hybrid | 1.8 MiB | ~50 µs | 16 B | **<50%** (extrapolated; likely far lower) | DoS puzzle |
| RandomX(-Tor) | D | >1 GiB | ~0.5–2 ms | 16 B | ~10% | consensus mining (Monero) |
| Equihash (Zcash 200,9) | B | 144 MiB | >150 µs | 1344 B | ~10–13× (GPU **faster**) | consensus mining |
| Equihash (BTG 144,5) | B | 2.5 GiB | ~10 µs | 100 B | GPU-mineable | consensus mining |
| Argon2(id) | A (KDF) | tunable | slow | — | **~300%** (low-mem) | password hashing |
| yespower/yescrypt | A (KDF) | ~2 MiB | slow | — | **~40%** (GPU-*un*friendly) | CPU-only coins |
| Cuckaroo / Cuckatoo | B (cousin) | bandwidth-bound | fast | small | GPU / ASIC resp. | consensus mining (Grin) |
| ProgPoW / KawPoW | C | DAG (GBs) | moderate | — | GPU-tuned (embraces) | GPU mining (Ravencoin) |

Reading the rows:

**vs RandomX (its ancestor).** This is the most illuminating comparison because Equi-X *is* a slimmed RandomX descendant. RandomX optimizes purely for CPU-friendliness and pays for it in verification: >2 GiB and ~2 ms (or 256 MiB and ~15 ms), "way too slow to be used as a client puzzle." RandomX-Tor trimmed it to ~0.5 ms / >1 GiB / ~2000 verif/s — still too heavy (two live seeds ⇒ >2 GiB on the service). Equi-X's leap was to keep the per-instance-program idea but wrap it in Equihash so the *memory and verify collapse to 1.8 MiB / 50 µs* while the GPU resistance is preserved. Track-record footnote: RandomX held CPU-dominance ~4 years before the **Bitmain X5 (2023)** RandomX ASIC appeared — at only ~3× efficiency — vindicating "ASIC-resistant, not ASIC-proof." Equi-X, by contrast, simply doesn't try to be ASIC-proof (Section 6).

**vs Equihash proper.** Vanilla Equihash is GPU-friendly — GPUs run it up to ~100× a CPU (devlog) — and at consensus scale it has been ASIC'd (Zcash's **Bitmain Antminer Z9**, 2018, ~10–20× a high-end GPU; Zcash *voted against* fighting it and still runs Equihash(200,9)). The cautionary cousin is **Bitcoin Gold's Equihash(144,5)/Zhash**: chosen for GPU-friendly ASIC-resistance, it kept hashrate low and rentable, and was **51%-attacked repeatedly** (~$18M in 2018; ~$70k in 2020). Equi-X inverts Equihash's GPU disadvantage by swapping Blake2b for HashX (so each leaf hash is itself CPU-bound) and shrinking n to 60 so the whole search is cache-resident. It keeps Equihash's *good* part (tiny proof, cheap verify) and removes its *bad* part (GPU dominance) — at the cost of being useless for consensus, which it never wanted to be.

**vs Argon2 / yespower (Family A KDFs).** tevador tested both and rejected them: both verify slowly, and — per the devlog — both "run faster on GPUs." That is half right by 2026 evidence. **Argon2** genuinely runs ~3× *faster* on a GPU in low-memory configurations (the working set fits GPU caches, so memory-hardness stops binding and core count wins) — a real disqualifier for a CPU puzzle. **yespower**, however, is actually GPU-*unfriendly* (it runs ~2–3× *slower* on GPU and powers CPU-only coins like Yenten and Sugarchain); the devlog's "~200%" appears to be a misattribution of Argon2's number. Either way the verification cost rules them out — KDFs are built to be slow to check, the opposite of what a DoS verifier needs.

**vs Cuckoo Cycle (Grin).** The asymmetric cousin: also small-proof and fast-verify, but its hardness is *graph-theoretic* (find a cycle) and *bandwidth-bound* rather than program-execution-bound. Grin's history is the instructive contrast in *philosophy*: it split into ASIC-resistant **Cuckaroo** and ASIC-friendly **Cuckatoo** and ran a scheduled 2-year migration from the former to the latter (completed Jan 2021), explicitly *giving up* on perpetual ASIC-resistance ("preventing single-chip ASICs no longer seems worthwhile or feasible"). Equi-X reaches the same conclusion — ASIC-resistance isn't worth chasing — but from the opposite direction: it can afford to ignore ASICs because, unlike a coin, **Tor can re-key with a patch.** Grin, now ASIC-mined and largely dormant, is a quiet warning about what happens when an asymmetric PoW's economic moat erodes.

**vs ProgPoW / KawPoW (Family C).** The polar opposite design goal: ProgPoW *embraces* GPUs and merely closes the GPU→ASIC gap. It was never activated on Ethereum (which went proof-of-stake at The Merge, Sept 2022) and lives on as Ravencoin's KawPoW. Listed here only to mark the far end of the spectrum: Family C wants GPU mining; Equi-X wants GPU *parity-or-worse*.

---

## 6. Why Equi-X's choices are the right ones for its niche

Read against the landscape, each design decision is a niche-specific optimum rather than a universal one:

- **n = 60, k = 3 (cache-resident).** Larger n (the rejected n=96 ⇒ ~2 GB) would reuse each HashX instance for 2^25 hashes — long enough for a GPU to compile an optimized per-instance kernel and to exploit its sorting bandwidth. n=60 keeps the working set under ~2 MiB so it lives in CPU cache, "the only case when CPUs can compete with GPUs in memory bandwidth." Small k keeps the proof tiny and verify cheap. This is the Family B knob tuned for the DoS axis.
- **2^k-SUM, not XOR.** Neutralizes the collision-weak HashX instances that would otherwise explode into trivial multicollision "solutions," and incidentally taxes FPGA/ASIC adders. A Family-B structure adapted to tolerate a Family-D inner hash that is only preimage-resistant.
- **Per-instance program (the RandomX inheritance).** The single most important anti-acceleration lever, and the thing no pure Family-B design has.
- **Dropping ASIC-resistance.** Legitimate *only because* of the use case: a DoS target can be patched in hours, so a >$1M ASIC can't be amortized; a consensus coin enjoys no such escape hatch, which is why RandomX, Equihash, Cuckoo, and ProgPoW all had to take ASICs seriously and Equi-X does not.

---

## 7. Placement verdict

On the Acceleration-Resistant Survey's map, Equi-X is best described as **the asymmetric (Family B) shell of Equihash filled with a Family D program-execution core, sized for the DoS corner of the design space** rather than for mining. That corner has very few residents — most asymmetric PoWs are GPU-friendly mining functions, and most program-execution PoWs are heavy mining functions — which makes Equi-X close to unique among *deployed* algorithms: a small-proof, instantly-verifiable, CPU-egalitarian puzzle that explicitly trades away ASIC-resistance for patch-ability.

Its closest conceptual neighbors are its own family members — RandomX above it (heavier, consensus-grade) and HashWX ahead of it (the GPU-hardened successor, Volume V) — and its closest *functional* role is the one the Survey's DoS-suitability section identifies as the genuinely hard target: a client puzzle that must be **flat across hardware and cheap to verify at scale**, not merely expensive. Equi-X is the most fully-realized answer to that specific problem the field has shipped to date — with the caveat, from Volume III, that its central hardware-flatness claim remains argued rather than empirically proven.
