# Mapping the Space of Acceleration-Resistant Proof-of-Work

### A survey and decision guide, written to be read at two levels

**Classified by time, memory, and bandwidth (proof size).**
Prepared for the project *ASIC-Resistant Proof of Work* · Updated July 2026
*(This Markdown edition supersedes the June 2026 report and folds in the year's hardware news — most importantly, the arrival of RandomX ASICs.)*

---

## The one-sentence answer

If you want a proof-of-work puzzle that keeps ordinary computers competitive, stays cheap to check, is light enough for a phone, and has actually survived real attacks in the wild, **Equi-X is the best candidate available today** — it takes the acceleration-resistance of the strongest CPU-bound design (RandomX) and removes that design's fatal weakness, the crushing cost of *verifying* a solution.

The rest of this document earns that conclusion, family by family, and is honest about the one thing Equi-X deliberately gives up (resistance to custom chips) and why that trade is the right one.

---

## How to read this document

This survey is written in **two layers**, and every topic is covered twice, back to back:

- **In plain terms —** a paragraph or so assuming no background at all. If you only read these, you will still follow the whole argument and reach the same conclusion.
- **Going deeper —** the technical version for a reader who wants the mechanisms, parameters, and named results.

Skim the plain layer for the story; drop into the deeper layer wherever you want the detail. Every specialized word (ASIC, memory-hard, asymmetric, and so on) is defined the first time it appears and again in the **Glossary** at the end. A set of **reference tables** and a **sources** list close the document.

---

## Executive summary

**In plain terms.** "Proof-of-work" is a way of proving you spent some real effort — electricity and computer time — to earn something, whether that's the right to add a block to a cryptocurrency or simply the right to load a web page during an attack. The trouble is that as soon as a puzzle becomes valuable to solve, someone builds a *machine* that solves only that puzzle, thousands of times more cheaply than your laptop. That machine is called an **ASIC**, and when one exists, mining stops being something anyone can do and becomes a game for whoever owns the factory. "Acceleration-resistant" puzzles are designed to stop that from happening — to keep everyday hardware competitive so that power stays spread out rather than concentrated.

The hard news from both the research literature and a decade of real deployments is that you can never win this fight *permanently*: any fixed puzzle can eventually be cast into a chip. The realistic goal is to make building that chip **not worth it** — to shrink the specialist's advantage until the engineering bill never pays off. This report sorts the whole field by the three levers a designer can pull — how much **time** a solution takes, how much **memory** it needs, and how big the **answer** is that has to travel across the network — and adds a fourth that turns out to decide everything: **how cheap it is to check a solution.**

**Going deeper.** The report classifies acceleration-resistant PoW along the project's three axes — **time** (sequential work per evaluation), **memory** (both capacity and, critically, *bandwidth*: off-chip traffic), and **message/proof size** (bytes added to every block or request) — plus the dominating **verification-cost** axis. Six families emerge: (A) memory-hard key-derivation functions (scrypt, Argon2, Balloon, yescrypt); (B) asymmetric / small-proof PoW (Equihash, Cuckoo Cycle, MTP); (C) GPU-oriented, bandwidth-bound DAG functions (Ethash, ProgPoW); (D) CPU / virtual-machine program functions (CryptoNight, RandomX); (E) multi-hash chains (X11, X16R); and (F) proof-of-space and space-time (Chia, Spacemesh). Their track records diverge sharply, and 2024–2026 delivered the decisive data point: **RandomX, long the poster child for "no ASIC," now has commercial ASICs** (Bitmain's Antminer X5, X9, and the Pinecone R1X), confirming that even the strongest compute-bound design is eventually silicon.

**The verdict, stated plainly.** Once you accept that no puzzle resists custom chips forever, the winning design is the one that maximizes everything *else* that matters — everyday-CPU fairness, tiny proofs, trivially cheap checking, a light memory footprint any device can bear, and a real deployment record — while staying nimble enough to change the puzzle when a chip finally appears. **Equi-X (tevador, 2023) is that design.** It fuses the small-proof, easy-to-check structure of Equihash with a constantly-changing CPU program (HashX) from the same family as RandomX, so it inherits RandomX's resistance to graphics cards and reconfigurable chips **without** RandomX's multi-gigabyte, milliseconds-long verification. It runs in about 1.8 MB of memory — enough to blunt a graphics card, light enough for a budget phone — produces a 16-byte answer, and verifies in roughly 50 microseconds. And unlike every rival here, it is already in production at scale, defending the Tor network's onion services against real denial-of-service attacks since 2023. Its one deliberate omission — it does *not* try to resist ASICs, because it assumes you will patch the puzzle instead — is, in light of RandomX's fall, the more honest and durable bet.

---

# Part 1 — The problem, in plain terms

## 1. What proof-of-work is, and why "acceleration resistance" matters

**In plain terms.** Imagine a lottery where, instead of buying a ticket, you earn one by solving a scratch-off puzzle that takes a little electricity and a few seconds of computer time. Whoever solves puzzles fastest wins the most often. In a cryptocurrency like Bitcoin, "winning" means getting to add the next page to the shared ledger and collect a reward; the puzzles are what keep the ledger honest, because rewriting history would mean re-solving mountains of them. The same idea has an older, humbler use: a website under attack can demand a small puzzle from every visitor, so that a flood of fake requests becomes too expensive to sustain while a real user barely notices.

The catch is specialization. A general-purpose computer is a jack-of-all-trades. If a puzzle is simple and always the same, an engineer can design a chip that does *only* that puzzle and nothing else — no screen, no keyboard support, no ability to run other programs — and it will crush your laptop by a factor of thousands. That single-purpose chip is an **ASIC** (Application-Specific Integrated Circuit). When ASICs exist, the lottery is no longer open to everyone; it belongs to whoever can afford the chip factory. "Acceleration resistance" is the art of designing puzzles that stubbornly refuse to be sped up by specialized hardware — so that the humble laptop, or the phone, stays in the game and the power stays spread out.

**Going deeper.** An **accelerator** is anything that solves the puzzle more cost-effectively than the commodity hardware the designer intends. Acceleration arrives by two routes, and a strong design must block both. The first is **hardware**: a ladder of increasing specialization, CPU < GPU < FPGA < ASIC, each rung trading flexibility for efficiency (Section 17 details it). The second is **algorithmic**: a cleverer method — a time-memory tradeoff, a parallel or amortized search — that cuts the honest cost with no new silicon at all. "ASIC resistance" is just the strongest hardware case of the broader goal.

Why do specialized chips win so decisively? For a brute-force search the right cost metric is not the number of operations but **dollar-seconds** — roughly *area × time* (AT), plus recurring energy. Bitcoin's double-SHA-256 uses almost no memory, so a vendor packs thousands of tiny hashing cores onto one die and pays perhaps a thousandth of a CPU's energy per hash. Colin Percival's 2009 insight, which founded this whole field, is the antidote: force the puzzle to use a large **memory** footprint. Memory is expensive to replicate in silicon but cheap on a general-purpose computer, so a big memory requirement erases much of the chip's advantage. A useful rule of thumb: doubling the runtime of a sequential memory-hard puzzle *quadruples* an ASIC's AT cost, because both the time and the memory it must carry double at once.

## 2. The uncomfortable truth: you can only make it "not worth it"

**In plain terms.** You cannot build a puzzle that resists specialized chips forever. Given enough money and motivation, any fixed puzzle can be turned into a chip — there is always *some* part of a general-purpose computer that the puzzle doesn't use and that a specialist can therefore throw away. So the goal is not "impossible to accelerate," which is a fantasy, but "not worth accelerating": keep the specialist's advantage small enough that the cost of designing and fabricating the chip never pays for itself. If a custom chip would only be, say, twice as efficient as a gaming PC, and it costs a million dollars to design, most attackers won't bother.

The year 2024 delivered the textbook proof of this. RandomX, the Monero cryptocurrency's puzzle, was for five years the great success story — the one design that had *never* attracted an ASIC. Then it did. Commercial RandomX ASICs are now sold openly. This didn't happen because RandomX was badly designed; it happened because *no fixed puzzle can hold out forever*. The lesson isn't "RandomX failed." The lesson is that any honest design has to plan for the day the chip arrives.

**Going deeper.** The literature converges on a distinction every designer should internalize:

- **Absolute (information-theoretic) resistance** — unattainable. "There will always be at least some parts of a CPU that will prove to be extraneous… and can be removed for efficiency." A sufficiently funded actor can always build dedicated silicon for a *fixed* algorithm.
- **Economic (relative, constant-factor) resistance** — the real target. Minimize any accelerator's price-performance and energy advantage so the non-recurring engineering cost is never repaid. Vitalik Buterin's threshold: if an accelerator's speed-up over commodity hardware is less than (H+E)/E — hardware-plus-electricity over electricity — ordinary users mining on machines they already own stay competitive. David Vorick, who actually built mining ASICs, warned the arms race structurally favors hardware engineers over protocol designers, and that secret ASICs may exist before anyone observes them.

The 2024–2026 RandomX ASICs make this concrete. Bitmain's **Antminer X5** (2024, ~212 kH/s, ~1,350 W) was the first commercially successful RandomX ASIC; it was followed by the **Antminer X9** (over 1 MH/s) and the **Pinecone R1X** (~1.2 MH/s, ~2,055 W). Against a high-end CPU's ~30 kH/s, a single ASIC box now delivers on the order of **35× the throughput** and roughly **5× the energy efficiency** (these are vendor figures and should be read as approximate, but the qualitative fact — RandomX's "no ASIC" moat has fallen — is not in doubt). RandomX bought about five years of resistance; that is a *good* result, and it is also the ceiling of what "resist forever" designs achieve. The alternative philosophy — resist the *cheap* accelerators (GPUs, FPGAs) and simply **patch the puzzle** when a chip appears — is the one Equi-X embodies, and it looks better every year.

## 3. The dials a designer can turn

**In plain terms.** Every acceleration-resistant puzzle is built by turning some combination of a few dials. **Time** is how much sequential work a solution takes — you can't shortcut it by throwing more processors at it. **Memory** is how much scratch space the puzzle forces you to use; a big memory requirement is the classic way to neutralize a chip, because memory is the one thing chips can't cheaply multiply. **Bandwidth** is a subtler cousin of memory: not how *much* space you need, but how much data you have to shuttle back and forth — and moving data is where most of the energy goes. **Proof size** is how big the answer is that has to be sent across the network and stored forever; a puzzle that produces huge answers clogs the very system it protects.

And then there is the dial that quietly decides everything: **how cheap it is to check a solution.** A puzzle can be brutally hard to solve yet trivial to verify — like a finished jigsaw, which takes hours to assemble but one glance to confirm. Puzzles with that property are called **asymmetric**, and as we'll see, asymmetry is the single most valuable feature a real-world puzzle can have. It is the property that lets a puzzle be used everywhere — in a currency, in a website's defenses, in a lightweight phone client — and it is precisely where the heavyweight "mining" designs fall down and where Equi-X shines.

**Going deeper.** The project's three axes map directly onto measurable quantities. **Time** is sequential computation per evaluation (resistant to parallel speed-up). **Memory** splits into *capacity* (how many bytes must be held at once) and *bandwidth* (off-chip traffic per evaluation) — a distinction Section 5 shows is decisive. **Message/proof size** is the on-the-wire cost paid on every block and every share. Layered on top is **verification cost**, which governs where a puzzle can be deployed at all.

Two formal ideas anchor the deeper discussion. First, **Cumulative Memory Complexity (CMC)** — the sum of memory in use at every time step of a (possibly parallel) computation — is the modern measure of memory-hardness, because it resists an attacker amortizing many evaluations at once in a way that peak memory does not; the ideal is CMC = Ω(N²). Second, **bandwidth-hardness** (Ren–Devadas): capacity-hardness only neutralizes a chip's one-time *area* advantage, while the larger, *recurring* advantage is energy — and off-chip memory-access energy is comparable for a CPU and an ASIC, so a puzzle that forces heavy off-chip *traffic* equalizes them where mere capacity does not. Keep both in mind; they explain why "just use a lot of memory" is not enough, and why the exact character of a puzzle's memory use matters more than the raw number of bytes.

---

# Part 2 — The toolbox: five ways to make a puzzle hard

Before touring the actual algorithms, it helps to understand the handful of *tricks* they are built from. Each trick targets a different weakness of specialized hardware. Real designs mix several.

## 4. Trick one: make it need a lot of memory (memory-hardness)

**In plain terms.** The oldest and most important trick is to force the puzzle to use a big chunk of memory — a large "desk" it has to spread its work across. A specialized chip wins by cramming thousands of tiny calculators onto one piece of silicon, but memory is bulky and expensive to put on a chip. If your puzzle insists on a gigabyte of scratch space, the chip-maker has to attach a gigabyte of memory to *each* of those thousands of calculators, and suddenly the chip looks a lot like… a regular computer. That's the whole idea: make the puzzle need so much memory that a specialist can't out-build a commodity machine.

**Going deeper.** The single most consequential design choice within memory-hardness is whether memory accesses are **data-dependent** (the addresses you touch depend on the data you're hashing) or **data-independent** (a fixed, public access pattern). Data-dependent functions (scrypt, Argon2d) can reach the ideal CMC = Ω(N²) and best resist amortization, but they leak information through cache-timing side channels — irrelevant for PoW, where there is no secret, which is exactly why PoW favors them. Data-independent functions (Argon2i, Balloon) are side-channel-safe but *provably* weaker: the Alwen–Blocki barrier (2016) shows every constant-indegree data-independent function has cumulative cost strictly below the quadratic ideal. The governing property behind high CMC is **depth-robustness** of the underlying computation graph. Practical upshot: for PoW you want *data-dependent* memory-hardness, and you want the footprint sized well above any attacker's on-chip cache — the lesson Litecoin learned the hard way when its tiny-footprint scrypt got ASICs.

## 5. Trick two: make it move a lot of data (bandwidth-hardness)

**In plain terms.** Here's a subtlety that took the field years to appreciate. Making a puzzle need a lot of memory stops a chip from being *smaller* than a real computer — but it doesn't necessarily stop the chip from being *cheaper to run*. Most of the electricity a computation burns isn't spent on the thinking; it's spent shuttling data back and forth between the processor and the memory. So the sharper trick is to force the puzzle to move enormous amounts of data around. Moving data costs about the same energy for a specialist chip as for your PC, so a puzzle bottlenecked on data-movement erases the chip's energy edge, not just its size edge.

**Going deeper.** This is the Ren–Devadas (2017) critique of pure memory-hardness. Their cost model — analyzed with the "red-blue pebble game" of cheap on-chip versus expensive off-chip accesses — separates **capacity-hard** from **bandwidth-hard**. A function can demand lots of memory yet have enough *locality* that an on-chip cache filters most off-chip traffic, restoring the ASIC's energy advantage (the stacked double-butterfly graph is the cautionary example). The positive results: scrypt, Catena-BRG, and Balloon are genuinely bandwidth-hard at suitable parameters, and scrypt is near-optimal on both axes — but *only* when its footprint dwarfs the attacker's cache. This is the technical reason "capacity alone is insufficient," and why the most durable memory designs are those whose access pattern defeats caching.

## 6. Trick three: make it act like a whole computer (CPU-binding)

**In plain terms.** A different and powerful trick is to make the puzzle behave like a little computer program that changes every single time — full of unpredictable branches, arithmetic, and decisions. Graphics cards are fast only when they can do the *same* simple thing to thousands of pieces of data in lockstep; feed them a twisty, unpredictable program and they stall. Reconfigurable chips (FPGAs) are fast only when the task is *fixed* so they can be wired up for it in advance; hand them a program that's different every time and they can't wire up ahead. So if your puzzle is essentially "here's a brand-new random program, now run it," you've targeted the one thing a general-purpose CPU is uniquely good at — and made life miserable for every specialist. This is the idea behind RandomX, and it's the "brain" inside Equi-X.

**Going deeper.** The insight is that the CPU's distinguishing strengths — accepting *dynamic code* (the program itself is an input), branchy speculative execution, double-precision floating point, and large flexible caches — are exactly what GPUs (which punish branch divergence) and FPGAs (which cannot re-wire per evaluation; a bitstream reload takes seconds) are worst at. A frequently regenerated program is the strongest single FPGA defense and a strong GPU defense at once. RandomX takes this to its limit: it JIT-compiles randomly generated programs for a virtual CPU, exercising integer and IEEE-754 floating-point units, AES, and branches, over a latency-bound scratchpad and a large dataset. HashX — the inner function of Equi-X — is the same idea in miniature: a per-instance random program, hashing-oriented and memory-light, designed as a client puzzle rather than a mining function.

## 7. Trick four: make answers tiny and easy to check (asymmetric puzzles)

**In plain terms.** The most under-appreciated trick is to make the puzzle *lopsided*: fiendishly hard to solve, but instantly easy to check — and to make the answer tiny. Think of a completed crossword: filling it in is the hard part, but confirming it's correct takes seconds. Why does this matter so much? Because in the real world, *checking* solutions is something the system does constantly — a cryptocurrency checks every share miners submit; a website under attack checks every visitor's answer. If checking is slow or the answers are huge, the checker itself becomes the bottleneck and a new target for attack. A puzzle that's hard to solve but trivial to verify, with a 16-byte answer, can be dropped into almost any system. This lopsidedness is called **asymmetry**, and it is the property that makes Equi-X special.

**Going deeper.** Asymmetric PoW separates a hard-to-compute function from a cheap-to-verify *relation*. Equihash (2016) pioneered the modern version: it reduces PoW to the generalized birthday problem, so a solution is a small set of colliding hash inputs that a verifier confirms with a handful of hashes and an ordering check. Cuckoo Cycle produces a 42-edge graph cycle (~168 bytes) checkable in ~84 siphashes. The payoff is threefold: tiny on-chain footprint, verification that never becomes the attack surface, and — as Section 19 explains — cheap **zero-knowledge** provability, because a proof system only has to re-run the light verifier, never the heavy solver. The structural tension is that binding memory into an asymmetric puzzle tends to *enlarge* the proof (MTP's ~200 KB proof is the extreme); the art is getting memory-hardness *and* a small proof, which is exactly what Equi-X achieves by putting the memory inside a HashX program rather than in the proof.

## 8. Trick five: use storage instead of computing (proof-of-space)

**In plain terms.** The last approach changes the game entirely: instead of proving you did a lot of *computing*, you prove you set aside a lot of *disk space*. Chips have no special advantage at storing files — a terabyte costs the same whether you're a hobbyist or a factory — so this sidesteps the whole chip arms race, and it uses far less electricity. The cost is a new wrinkle: it's hard to be sure someone is really *keeping* the data around rather than cleverly regenerating it on demand, and aggressive compression can turn "space" back into "computing."

**Going deeper.** Proof-of-Space (Dziembowski et al., 2015) has a prover commit to a labeling of a hard-to-pebble graph via a Merkle tree; storing less than the full labeling forces expensive recomputation, penalized by pebbling lower bounds. Plain PoSpace proves space only at an instant, so Proof-of-Space-**Time** (Moran–Orlov) proves storage held over a *duration*. Chia pairs proof-of-space with a verifiable delay function (proof-of-time) to stop regeneration and grinding, splitting work into a one-time "plotting" phase and cheap ongoing "farming." The open problem — aggressive plot compression re-introducing a compute-for-space tradeoff — is why "Proof of Space 2.0" is an active topic. It is a genuinely different point in the design space, strong on energy and chip-resistance, weaker on maturity.

---

# Part 3 — The contenders: six families of puzzle

This is the heart of the survey: a tour of every serious approach, grouped into six families. For each, the plain layer says what it is and how it fared; the deeper layer gives the mechanism and key parameters; and a **Verdict** line sums up where it sits today.

## 9. Family A — Memory-hard key-derivation functions

*scrypt · Argon2 · Balloon · yescrypt*

**In plain terms.** These are the original "big desk" puzzles (Trick one). They were mostly invented for a different job — safely storing passwords — and then borrowed for proof-of-work because the same "force a large memory footprint" property that slows down password-crackers also slows down mining chips. scrypt is the grandparent; Argon2 is the modern, award-winning standard; yescrypt is a CPU-friendly descendant. They are excellent building blocks, and in fact one of them (Argon2) sits *inside* both RandomX and Equi-X. On their own, though, their track record as mining puzzles is mixed, and it comes down entirely to whether the designer set the memory dial high enough.

**Going deeper.** All expose explicit **time** (passes/iterations) and **memory** parameters; the data-dependent members (scrypt, Argon2d) are also bandwidth-hard at large footprints.

- **scrypt (Percival, 2009):** the theoretical gold standard — proven maximally memory-hard (CMC = Ω(N²)) even against parallel attackers. Its famous failure is not the algorithm but the *parameters*: Litecoin and Dogecoin deployed it at a ~128 KB footprint, small enough to sit in an ASIC's on-chip memory, so scrypt ASICs appeared quickly. Correctly understood, scrypt is **capacity- and bandwidth-hard**, not latency-bound.
- **Argon2 (2015, PHC winner, RFC 9106):** three variants — Argon2d (data-dependent, for PoW), Argon2i (data-independent, side-channel-safe), Argon2id (hybrid default). Fills up to a gigabyte in a fraction of a second; Argon2d is tradeoff-resistant and is the memory primitive inside RandomX and MTP.
- **Balloon (2016):** the first practical *data-independent* memory-hard function with a proven bound; consequently subject to the Alwen–Blocki attack that limits all data-independent designs.
- **yescrypt / Lyra2 / NeoScrypt:** scrypt descendants with tunable memory. **yescrypt** is deliberately CPU-friendly and **GPU-*unfriendly*** (a GPU runs it at roughly a fraction of CPU throughput, not faster), with no ASICs reported — though it remains niche.

**Verdict.** Indispensable as *components* and strong when the memory dial is set high, but a bare memory-hard KDF is symmetric (the verifier redoes the work) and GPU-leaky in several cases. Great ingredients; rarely the best finished dish.

## 10. Family B — Asymmetric, small-proof PoW

*Momentum · Equihash · Cuckoo Cycle · MTP · (and the synthesis, Equi-X)*

**In plain terms.** This is the "lopsided puzzle" family (Trick four): hard to solve, easy to check. It is the most important family for our purposes, because it's the one Equi-X belongs to. The defining extra concern here is the *size of the answer* — because these puzzles trade in solutions that travel across the network, a design that produces bloated answers can undo its own benefits. The family runs from tiny, elegant designs (Cuckoo Cycle, 168-byte proofs) to a cautionary disaster (MTP, whose 200-kilobyte proofs sank it).

**Going deeper.** The family exploits hard-to-compute, easy-to-verify problems, with **proof size in bytes** as the extra axis.

- **Momentum (Larimer, 2013):** the precursor — find two nonces whose birthday-hashes collide. Small proof, trivial verify, but too small a table to resist amortization. Not resistant in practice, but the conceptual ancestor of Equihash.
- **Equihash (Biryukov–Khovratovich, 2016):** reduces PoW to the generalized birthday problem solved with Wagner's algorithm — find 2ᵏ Blake2b outputs XOR-ing to zero under an "algorithm-binding" constraint that blocks amortization. Parameters (n, k) trade time, memory, and proof size. Zcash's (200, 9) uses ~144 MB and a **1,344-byte** proof. **Track record:** Bitmain's Antminer Z9 (2018) built an Equihash ASIC, breaking the (200,9) resistance claim; the lesson was that the memory parameter was set too low. Higher-memory variants (144,5) resisted longer.
- **Cuckoo Cycle (Tromp, 2014):** find a 42-cycle in a hash-seeded graph. The standout for economy: a **~168-byte** proof verified in ~84 siphashes. Memory ranges from ~128 MB (lean, latency-bound) to ~2.2 GB (mean, bandwidth-bound). Grin's Cuckatoo variant was *deliberately* ASIC-friendly; Cuckaroo was the ASIC-resistant sibling.
- **MTP — Merkle Tree Proof (2016):** builds a ~2 GB Argon2d array and opens random blocks with authentication paths. Verification is cheap, but the **proof is ~180–200 KB** — a fatal "bandwidth hog." A time-memory tradeoff attack (Dinur–Nadler, 2017) let cheaters use ~128 MB instead of 2 GB; deployed by Zcoin/Firo in 2018 and abandoned by 2021. Effectively deprecated.

**Verdict.** The right family for any setting where solutions travel and get checked constantly — i.e. almost all real settings. Its best members (Cuckoo Cycle, and above all Equi-X, Section 16) are the most *deployable* puzzles in the entire survey. Its worst (MTP) shows what happens when you let the proof balloon.

## 11. Family C — GPU-oriented, bandwidth-bound DAG functions

*Ethash · ProgPoW*

**In plain terms.** These puzzles don't try to keep everyone on a laptop; they aim one rung up the ladder, at **graphics cards**, and try to make sure a specialized chip can't do much better than a good gaming GPU. They work by forcing the puzzle to constantly pull data from a large table too big to fit on a chip, so the bottleneck becomes raw memory speed — and gaming GPUs already have world-class memory speed. Ethereum used this (Ethash) for years; it worked reasonably well, holding chips to roughly a 2× edge rather than 1000×.

**Going deeper.** Both make off-chip DRAM **bandwidth** the bottleneck over a large dataset (DAG), exposing only a tiny on-chain message (nonce + mix hash).

- **Ethash / Dagger-Hashimoto (2015–2022):** streams pseudo-random DAG pages per hash (~8 KB random DRAM traffic each). The DAG grew from ~1 GiB to ~5 GB by 2022; light clients verify from a ~16 MB cache. **Track record:** resistance held ~3 years, then the Antminer E3 (2018) delivered only ~2×–2.5× GPU efficiency — far below SHA-256's ~1000×; growing DAG size eventually pushed fixed-memory ASICs off-chain. PoW ended at Ethereum's Merge (Sept 2022).
- **ProgPoW (EIP-1057):** a drop-in Ethash extension that regenerates a **random program every ~2 minutes** and saturates the *whole* GPU (registers, ALUs, a small cache), squeezing the ASIC gap toward ~1.1–1.2×. Passed audits but was never activated on Ethereum (dropped amid community opposition before the move to proof-of-stake); it lives on in KawPow (Ravencoin) and FiroPoW.

**Verdict.** The best answer *if your target hardware is the GPU* rather than the CPU — genuinely narrows the ASIC gap. But it targets the wrong machine for an egalitarian, everyone-can-play puzzle, carries a large and growing dataset, and its small on-chain message hides a symmetric, memory-heavy verify.

## 12. Family D — CPU / virtual-machine program functions (and the ASIC that finally came)

*CryptoNight · RandomX*

**In plain terms.** This family aims squarely at the ordinary **CPU** — the machine almost everyone owns — using Trick three: make the puzzle behave like a constantly-changing computer program. RandomX is its masterpiece and, until recently, the field's biggest success: for five years no specialized chip could beat a CPU at it. It is the design Equi-X borrows its "brain" from. The twist in this story, and the reason this survey needed updating, is that in 2024 the long-awaited RandomX chip finally arrived — proving the point from Section 2 that nothing resists forever.

**Going deeper.**

- **CryptoNight (2013–2019):** a memory-*latency*-bound hash with a ~2 MB scratchpad sized to fit L3 cache. Because a 2 MB latency loop is easy to place on-chip, Bitmain built efficient ASICs by ~2017; Monero's repeated emergency tweaks failed to hold, motivating RandomX.
- **RandomX (Monero, tevador et al., 2019):** runs randomly generated programs in a virtual CPU, JIT-compiled to native code — integer and full IEEE-754 floating-point math (all rounding modes), AES, branches, a 2 MiB latency-bound scratchpad, and a ~2,080 MiB dataset (256 MiB "light mode" for verification). To beat it, an ASIC would essentially have to *reimplement a superscalar CPU with floating point and 2 GiB of fast memory* — erasing its own advantage. It depends on bandwidth/capacity **and** latency **and** heavy compute at once.
- **The update:** four independent audits in 2019 found no critical flaws, and RandomX held with no dominant ASIC from its Nov 2019 activation until ~2024 — the strongest real-world record of any compute-style PoW. **But that record is now broken.** Commercial RandomX ASICs exist as of 2024–2026 (Antminer X5, then X9, and the Pinecone R1X), with roughly a 5× efficiency and ~35×-per-box throughput edge over a CPU. RandomX's resistance was excellent and finite.

**Verdict.** The strongest *acceleration-resistance* mechanism in the survey, and the direct ancestor of Equi-X's inner function. Its two liabilities are decisive, though: **verification is heavy** (light mode still needs 256 MiB and milliseconds, so the verifier can become the bottleneck or an attack surface), and it now has ASICs. Equi-X keeps RandomX's mechanism and discards its verification cost — which is the crux of this report's conclusion.

## 13. Family E — Multi-hash chains, and why they failed

*X11 · X16R*

**In plain terms.** An intuitive but flawed idea: string together many different hash functions, hoping that a chip would have to be eleven or sixteen times as complicated and therefore not worth building. It didn't work. Chaining cheap, well-known calculations just gives the chip-maker a slightly bigger — but still cheap — circuit to lay down. Even shuffling the order each block only slowed things a little.

**Going deeper.** These are compute-bound with negligible memory, so they offered little durable resistance. **X11** (Dash, 2014) chained 11 hashes in fixed order — trivially pipelined into an ASIC by ~2016. **X16R** (Ravencoin, 2018) randomized the ordering by the previous block hash, which only forced ASICs to make their cores routable — a modest cost; X16R ASICs mined it within a year. The lesson: combining many fast, low-memory hashes, even with random ordering, does not confer resistance, because each function is a cheap known circuit and the bottleneck stays in cheap compute.

**Verdict.** A dead end, kept here as an instructive failure. Ravencoin itself moved on to the memory-hard KawPow.

## 14. Family F — Proof-of-space and proof-of-space-time

*Chia · Spacemesh*

**In plain terms.** The outsider that changes the rules (Trick five): compete on **disk space** instead of computation. Chips give no edge on dollars-per-terabyte, so the compute arms race simply doesn't apply, and energy use plummets. The price is a less mature security story and a tricky "are you really storing it?" problem.

**Going deeper.** **Chia (2019)** combines proof-of-space with a verifiable delay function to stop regeneration and grinding: a one-time compute-heavy **plotting** phase writes a plot file (minimum ~101.4 GiB at k=32; ~256-byte proofs), then cheap ongoing **farming** does lookups. **Spacemesh** realizes a non-interactive proof-of-space-time, alternating storage proofs with proof-of-elapsed-time for a race-free, energy-light protocol. The active caveat is plot **compression**, which re-introduces a compute-for-space tradeoff.

**Verdict.** The strongest way to *exit* the compute arms race entirely, and by far the most energy-efficient. But it answers a different question than "what's the best acceleration-resistant *compute* puzzle," carries its own tradeoffs, and — being storage rather than a quick per-request challenge — cannot serve the lightweight puzzle roles where Equi-X excels.

---

# Part 4 — What actually happened, and the design that learned from it

## 15. The scoreboard: a decade of track record

**In plain terms.** Theory is one thing; what actually happened when these puzzles met real chip-makers is another. The pattern across ten years is remarkably clean. Every puzzle whose "hot" working data was small enough to fit inside a chip's own fast memory was beaten within months to a couple of years. Puzzles that forced either huge data-movement or full-blown computer-program behavior held out for years and kept the chip's advantage small. And the storage-based approach sidestepped chips entirely. The single best predictor of survival was simple: *did the puzzle force work that a chip can't cheaply absorb onto its own silicon?*

**Going deeper.** The record, updated through 2026:

| Algorithm | Resistance mechanism | ASICs appeared? | Outcome |
|---|---|---|---|
| scrypt (small N) | Memory-hard (tiny footprint) | Yes (Litecoin era) | Footprint too small; resisted only briefly |
| X11 / X16R | Multi-hash chain | Yes (~2016 / 2019) | Failed; Ravencoin moved to KawPow |
| CryptoNight | 2 MB latency loop | Yes (~2017) | Failed; replaced by RandomX |
| Equihash (200,9) | Generalized birthday + memory | Yes (2018, Antminer Z9) | Failed at these params; forks raised memory |
| MTP | Argon2 + Merkle openings | FPGA pressure | Attacked (2017); abandoned 2021 |
| Ethash | Memory-bandwidth (DAG) | Yes (~2×, E3 2018) | Modest gap; PoW ended at the Merge, 2022 |
| ProgPoW | Full-GPU saturation | Not deployed on ETH | ~1.1–1.2× target; used by smaller chains |
| **RandomX** | **CPU VM (mem + latency + compute)** | **Yes — since ~2024 (X5/X9/R1X)** | **Held 2019–2024; strongest record, now broken** |
| yescrypt | Memory-hard (tunable), CPU-friendly | None reported | Holding (niche) |
| Chia (PoSpace-Time) | Commodity storage | N/A (storage, not compute) | Holding; compression tradeoff noted |
| **Equi-X** | **HashX program + Equihash memory** | **n/a by design (patchable puzzle)** | **Deployed in Tor since 2023; holding** |

The stark reading: designs whose hot set fit cheap on-die SRAM (X11/X16R, CryptoNight, small-N scrypt) fell fast; designs forcing large off-chip bandwidth or full general-purpose execution (Ethash, RandomX) compressed the ASIC gap to single-digit multiples and bought years; storage-based schemes sidestep compute ASICs entirely. The new 2024 line in the table — RandomX ASICs — is the most important update since the original report, and it reframes the whole question, as the next section explains.

## 16. The synthesis: Equi-X

**In plain terms.** Now we can meet the recommendation directly. **Equi-X** was built in 2023 by *tevador* — the same engineer behind RandomX — for a very demanding customer: the Tor network, which needed a puzzle to fend off denial-of-service attacks on its onion services without shutting out ordinary people on modest devices. Think about what that job requires all at once. The puzzle has to be *fair* — a phone and a gaming rig shouldn't be wildly far apart. It has to produce a *tiny answer*, because millions of them fly across the network during an attack. It has to be *trivially cheap to check*, because the machine under attack is checking constantly and can't afford to sweat over each one. And it has to run in a *small amount of memory*, so a cheap laptop can play. No single earlier design ticked all four boxes.

Equi-X ticks all four by *combining the two best ideas in the field.* It takes the lopsided, tiny-answer structure of **Equihash** (Trick four — hard to solve, a glance to check) and drops a miniature **RandomX-style changing-program** (Trick three — the thing GPUs and reconfigurable chips can't handle) into its core. The result is a puzzle with RandomX's resistance to graphics cards and FPGAs, but with a 16-byte answer, a check that takes about 50 microseconds, and a memory footprint of about 1.8 MB — small enough for any device, big enough to spoil a GPU's day. It is, in a sentence, **RandomX's brain in Equihash's body.** And crucially, it isn't a paper proposal: it has been quietly doing this exact job inside Tor since 2023.

**Going deeper.** Equi-X wraps an Equihash-style solver (find values that sum to zero under an algorithm-binding constraint) around **HashX**, a per-instance randomly-generated hash program in the RandomX lineage. Two engineering decisions make it resist the cheap accelerators that matter for its threat model:

- **It added a memory element** (the Equihash layer) precisely because HashX on its own is memory-light, and a memory-free, logic-only function stays *FPGA-viable* — an FPGA can route a fixed integer datapath with no DRAM bottleneck. HashX's own documentation flagged exactly this ("logic-only FPGAs could be a viable option"); the Equihash memory closes it.
- **It replaced XOR-to-zero with modular-SUM-to-zero.** Adders cost more FPGA logic than XOR gates, so this small change raises the FPGA's cost further. These are the accumulated lessons of a decade of failures, baked into one design.

Its parameters sit at the deliberate *opposite* corner from a mining function: a **~1.8 MiB cache-resident** footprint (blunts GPUs without excluding weak clients or burdening the verifier), a **16-byte** solution, and **asymmetric ~50 µs verification**. It resists GPUs (per-hash program changes defeat lockstep parallelism) and FPGAs (no fixed datapath to wire; the SUM adders and memory raise the cost), and it explicitly **does not** aim to resist ASICs — the assumption being that a client-puzzle can be *changed with a software patch*, instantly bricking any custom chip, an option a slow-moving cryptocurrency lacks. It shipped in **Tor 0.4.8 (2023)** and has a maintained Rust implementation in the Arti codebase. In the language of this survey's axes, Equi-X occupies the sweet spot: minimal proof size, minimal and stateless verification, light-but-real memory-hardness, tunable time — the profile that makes a puzzle *usable everywhere*, which is why this report names it the best candidate.

---

# Part 5 — Three more lenses that confirm the choice

The verdict doesn't rest on the parameter axes alone. Three further lenses — the hardware ladder, the direction hardware is heading, and two important deployment settings (zero-knowledge proofs and denial-of-service defense) — all point the same way.

## 17. The hardware-acceleration ladder: GPU, FPGA, ASIC

**In plain terms.** "Specialized hardware" isn't one thing; it's a ladder of four rungs, each less flexible and more efficient than the last: an ordinary **CPU**, a **graphics card (GPU)**, a **reconfigurable chip (FPGA)**, and a fully custom **ASIC**. A puzzle can beat one rung and lose to another, so "ASIC-resistant" alone is too narrow a phrase. In practice, the attacker's realistic weapon is usually a graphics card or a reconfigurable chip — not a multi-million-dollar custom chip — so resisting *those* is what actually matters for most designs. The remarkable thing is that the way to resist all the cheap rungs at once is to aim at the CPU: the things a CPU is uniquely good at are exactly the things the other rungs are worst at.

**Going deeper.** Each rung has distinct strengths and, therefore, distinct levers that resist it:

| Rung | Good at | Levers that resist it |
|---|---|---|
| CPU | Branchy, irregular, sequential code; large flexible caches; dynamic code; FP64 | *(This is the target — the strongest designs bind work TO the CPU)* |
| GPU | Thousands of identical lanes in lockstep; coalesced bandwidth; FP32 | Sequential dependencies; divergent/random branches; large per-thread state; FP64; variable-time code |
| FPGA | One fixed function hardwired into low-latency logic; cheap XOR | Frequently-changing programs (bitstream reload takes seconds); large DRAM demand; floating point; modular SUM instead of XOR |
| ASIC | One fixed function at maximum efficiency; custom SRAM | Large dynamic DRAM dataset; FP/integer division; high verification cost; **ability to hard-fork the algorithm** |

Two nuances matter. First, **FPGA-resistance can be *harder* to achieve than ASIC-resistance**: a memory-light, logic-only function stays FPGA-viable because its fixed datapath routes cleanly with no memory bottleneck — the exact problem HashX had and Equi-X fixed with a memory element and SUM-not-XOR adders. Second, the levers are **separable** — GPU-resistance and FPGA-resistance are different targets. A track-record summary by rung:

| Algorithm | GPU-res. | FPGA-res. | ASIC-res. | Notes |
|---|---|---|---|---|
| Ethash | No | No | Partial | GPU-friendly by design |
| ProgPoW | No (by design) | Mostly | Mostly | Targets the whole GPU |
| Equihash (200,9) | No | No | No | GPUs ~100× CPU; Z9 ASIC |
| RandomX | Yes | Yes | **No longer** | Held all three 2019–2024; now has ASICs |
| Cuckoo / Cuckatoo | Partial | No | No | Lean miner is SRAM-heavy by design |
| yespower | CPU-favoring | Neutral | Neutral | Designed CPU-friendly / GPU-unfriendly |
| HashX (bare puzzle) | Yes | No | n/a | Per-instance program; but memory-free → FPGA-viable |
| **Equi-X** | **Yes** | **Yes** | **n/a (patchable)** | **HashX + Equihash memory + SUM adders; Tor 0.4.8** |

The unifying insight: **the broadest resistance comes from CPU-targeting**, because a frequently-changing program is the single strongest FPGA defense and a strong GPU defense at once. Only RandomX and Equi-X resisted both the GPU and the FPGA rung — and of the two, only Equi-X pairs that resistance with a cheap verifier and a light footprint.

## 18. The hardware trends that change the game

**In plain terms.** Two shifts in modern hardware are quietly rewriting the rules. First, **unified memory**: in machines like Apple's M-series, the CPU and graphics chip now share one big fast pool of memory instead of each having their own. That means an integrated graphics chip can suddenly reach into a huge memory pool that used to be a discrete GPU's private preserve — which weakens puzzles that relied on "your data won't fit in a GPU's memory." Second, and more durably, **memory latency has barely improved in years even as bandwidth has soared.** In plain terms: computers can move data faster than ever, but the *delay* before the first byte arrives is stuck. Puzzles built around that stubborn delay have the most durable moat — though even that erodes as chips grow ever-larger on-board caches.

**Going deeper.** Unified Memory Architectures (Apple M-series up to ~800 GB/s and 512 GB shared; NVIDIA Grace Hopper; AMD MI300A; the game consoles) collapse the CPU/GPU memory split. The consequences differ by family: **bandwidth-bound** designs (Ethash, ProgPoW, RandomX's dataset) see higher absolute hash rates on commodity machines but no restored *hardness*, because an ASIC pairs the same HBM/GDDR — the tide lifts both boats. **Capacity-bound** designs suffer most: integrated GPUs can now address hundreds of GB, so "outgrew my VRAM" defenses evaporate. **Latency-bound** designs keep the most durable moat, because DRAM latency has hovered at ~50–90 ns for years (the "memory wall") — but the moat erodes as on-chip caches balloon (AMD 3D V-Cache toward ~192 MB; MI300A's 256 MB Infinity Cache), because once a puzzle's hot set fits in cache the off-chip energy term vanishes and the edge shifts to whoever bolts on the most SRAM. Design implication: a memory-hard puzzle meant to last should be *latency-bound and data-dependent* and size its hot set *above the largest commodity cache* — a target now in the hundreds of megabytes. For Equi-X's purpose this is not the binding constraint (it is a light, patchable client puzzle, not a decade-stable coin), which is another reason its "patch, don't out-engineer" philosophy ages well.

## 19. Lens: cheap zero-knowledge verification

**In plain terms.** A growing need in modern systems is to prove, cheaply and even *privately*, that a puzzle was solved correctly — for lightweight clients, cross-chain bridges, or anonymous "I did the work" tokens that reveal nothing else. Here the lopsided (asymmetric) puzzles win again, for a beautiful reason: to prove a solution is valid, you only have to re-run the cheap *check*, never the expensive *solve*. So a puzzle that's cheap to check is automatically cheaper to prove. The heavyweight mining designs, whose checking is itself heavy, are the worst at this; the small-proof designs are the best.

**Going deeper.** Zero-knowledge proving cost scales with the number of field-arithmetic constraints; anything bit-heavy (SHA-256 ~27k constraints; Keccak ~150k+) or memory-hard arithmetizes badly, while ZK-friendly hashes (Poseidon ~200 constraints) are cheap but weaker against hardware. The decisive principle: **asymmetric PoW separates a hard solve from a cheap-to-verify relation, and a ZK circuit need only re-execute the verifier.** So ZK-friendliness is governed by *verification* weight, not evaluation weight. RandomX is "very poor" (memory-hard even to verify; FP and dynamic code arithmetize terribly), while Cuckoo Cycle and the Equihash collision check are "good/fair" (small, constant-size verifiers). Techniques exist to soften the tension — STARK/Binius lookups, recursion, GKR batching (Keccacheck), or flipping the model so that *generating a proof is the work* (Aleo, Nockchain) — but the clean structural win belongs to light-verification, asymmetric designs. Equi-X inherits Equihash's light verifier, so it sits on the friendly side of this axis too.

## 20. Lens: stopping denial-of-service attacks

**In plain terms.** Long before cryptocurrency, proof-of-work was invented to fight spam and denial-of-service: make every request cost a little effort, so a flood becomes unaffordable. This is the job Equi-X was actually built for, and it flips the priorities. Here the defender is the one under attack and doing the checking, so a puzzle that's expensive to check or that produces big answers is *worse than useless* — it hands the attacker a new weapon. What you want is exactly Equi-X's profile: tiny answers, near-free checking, light memory that keeps ordinary users included, and difficulty you can crank up smoothly as an attack intensifies. And you explicitly *don't* need ASIC-resistance — because you can patch the puzzle, and because no attacker will fund a million-dollar chip to attack one website.

**Going deeper.** The design constraints invert the mining case. Verification is paramount and must be cheap, stateless, ideally constant-time — which mandates *asymmetric* puzzles and rules out full RandomX (~2 GiB, milliseconds to verify) and symmetric memory-hard hashers (Argon2, yespower — the verifier redoes the work). Proof size must be tiny (Tor required <200 bytes; Equi-X delivers 16); MTP's ~200 KB and Equihash's 1,344 B are amplification vectors. Memory is double-edged — it equalizes hardware but can exclude weak clients, so it should be *light and cache-resident*, exactly Equi-X's ~1.8 MiB. And the required resistance is **GPU/FPGA, not ASIC**, for three reasons: an ASIC costs >$1M an attacker can't amortize against one victim; the defender can change the algorithm with a software patch, instantly bricking silicon; and the real threat is commodity GPUs/FPGAs cheaply simulating many "clients." Suitability by family:

| Approach | Suitability | Why |
|---|---|---|
| Hashcash (SHA-256) | Good baseline | Tiny proof, stateless verify; but pure CPU-bound → GPU edge, unfair across CPUs |
| Equihash (crypto params) | Ill-suited | GPUs ~100× CPU; 1,344-byte proofs |
| RandomX (full) | Ill-suited | ~2 GiB / ~ms verification makes the *verifier* the DoS vector |
| Argon2 / yespower | Ill-suited | Symmetric (verifier redoes work); GPU-leaky in cases |
| Cuckoo Cycle | Promising | Small proof, fast verify; keep memory client-friendly |
| **Equi-X** | **Best-in-class** | **Asymmetric ~50 µs verify; 16-byte solution; ~1.8 MiB blunts GPUs without burdening clients; deployed Tor 0.4.8** |
| Proof-of-space | Ill-suited | Needs a persistent storage commitment, not a quick challenge |

For DoS defense, the optimal point in time/memory/bandwidth space is in several respects the *opposite* of the cryptocurrency optimum — and Equi-X sits exactly on it. This is not a coincidence: it is the problem Equi-X was engineered to solve, and it solved it well enough to ship in one of the internet's most adversarial environments.

---

# Part 6 — The verdict

## 21. Why Equi-X is the best candidate

**In plain terms.** Pull the threads together. We started with an uncomfortable fact: no puzzle resists custom chips forever, and in 2024 even the champion, RandomX, finally got its chip. Once you accept that, the question stops being "which puzzle is un-beatable?" (none are) and becomes "which puzzle wins on *everything else that matters* — fairness on ordinary machines, tiny answers, near-free checking, a footprint any device can bear, and a real track record — while staying nimble enough to change when a chip eventually shows up?"

On that scorecard, **Equi-X wins**, and it isn't especially close:

1. **It keeps the strong part of the champion.** Its HashX core is a RandomX-style changing program, so it inherits the resistance to graphics cards and reconfigurable chips that made RandomX the best — the two accelerators an attacker actually reaches for.
2. **It discards the champion's fatal flaw.** RandomX is brutally expensive to *check* (gigabytes, milliseconds). Equi-X checks a 16-byte answer in about 50 microseconds. Cheap checking is not a nicety — it's what lets a puzzle be used in a currency, a website defense, a phone, or a privacy proof at all.
3. **It's light enough for everyone.** About 1.8 MB of memory: enough to spoil a GPU, small enough for a budget phone. RandomX's ~2 GB shuts out the very people an egalitarian puzzle is supposed to include.
4. **It's honest about the endgame.** Instead of betting on resisting chips forever — a bet RandomX just lost — it assumes you'll patch the puzzle when a chip appears, which for anything that can ship a software update is the more realistic and durable posture.
5. **It has actually done the job.** It isn't a whitepaper. It has defended Tor's onion services against real, sustained attacks since 2023. No other candidate here can point to a comparable production record in this exact role.

**Going deeper — the head-to-head.** Scoring the leading candidates across every axis this survey uses (✔ strong, ~ partial, ✗ weak):

| Property (what you want) | **Equi-X** | RandomX | Cuckoo Cycle | Ethash / ProgPoW | Proof-of-Space (Chia) |
|---|---|---|---|---|---|
| CPU-egalitarian (fair across devices) | ✔ | ✔ | ~ | ✗ (GPU) | ✔ (storage) |
| GPU-resistant | ✔ | ✔ | ~ | ✗ | n/a |
| FPGA-resistant | ✔ | ✔ | ✗ | ✗ | n/a |
| Cheap, stateless verification | ✔ (~50 µs) | ✗ (256 MiB, ms) | ✔ | ~ | ✔ |
| Tiny proof / message | ✔ (16 B) | ✔ (small) | ✔ (168 B) | ✔ | ~ (256 B) |
| Light footprint (weak devices included) | ✔ (~1.8 MiB) | ✗ (~2 GiB) | ~ | ✗ (GB DAG) | ✗ (100+ GB disk) |
| ZK-friendly (cheap to prove) | ✔ | ✗ | ✔ | ✗ | ~ |
| Proven in production | ✔ (Tor, 2023–) | ✔ (Monero) | ~ (Grin/dual) | ✔ (ETH, retired) | ✔ (Chia) |
| Resists custom ASICs | ✗ *(by design)* | ✗ *(as of 2024)* | ✗ | ~ | ✔ (no chip edge) |

Equi-X is the only column that is strong on *both* hardware-resistance (GPU **and** FPGA) *and* the deployability cluster (cheap verify, tiny proof, light footprint, ZK-friendly, shipped). RandomX matches its hardware column but fails the entire deployability cluster — and has now lost the ASIC row it was famous for. Cuckoo Cycle matches the deployability cluster but is weaker on hardware-resistance (FPGA-viable by design). Proof-of-space wins the ASIC row outright but is a different kind of system that can't fill the lightweight-puzzle roles at all.

**The honest caveats — and why they don't change the answer.** Three things Equi-X gives up, stated plainly:

- **It is not ASIC-resistant, on purpose.** For a system that *cannot* patch quickly — a high-value cryptocurrency that would need a contentious hard fork — this is a real limitation. But the same RandomX ASICs that arrived in 2024 show the "resist forever" alternative also fails on that timescale; the difference is that Equi-X *planned* for it. If you must maximize coin-grade ASIC-resistance, you would size the memory far larger (toward the scrypt/RandomX heavy end) and accept the verification cost — while remembering that this only buys years, not permanence.
- **Its footprint is small.** ~1.8 MiB is tuned for an inclusive client puzzle, not to maximize memory-hardness. That is the right call for fairness and for weak devices, but it means the raw memory-hardness "moat" is modest; the resistance comes from the changing program plus memory, not from sheer size.
- **It was designed as a puzzle, not a currency.** Its production record is DoS defense, not securing billions in coin value. That record is real and adversarial, but it is not identical to a decade of mining economics.

None of these dislodge the conclusion for the realistic, general goal — an acceleration-resistant proof-of-work that is *actually deployable* and *honest about the chip endgame*. They simply mark the one scenario (a never-patched, maximal-ASIC-resistance coin) where you'd deliberately trade Equi-X's balance for brute memory weight, and note that even there the payoff is finite.

**Where the alternatives still make sense.** If you specifically need CPU-egalitarian *mining* and can afford heavy verification, RandomX remains the strongest mechanism (now with a known ASIC premium to price in). If you want to leave the compute arms race entirely and care most about energy, proof-of-space (Chia, Spacemesh) is the answer. If you want the smallest possible proof with a simple graph problem and don't need FPGA-resistance, Cuckoo Cycle is elegant. And if your hardware target is genuinely the GPU, ProgPoW narrows the gap best. But for the broad, practical definition of the problem this project set out to map — keep ordinary computers competitive, stay cheap to verify, stay light, and stay deployable — **Equi-X is the best candidate available today.**

**Closing.** The decade's clearest lesson is that acceleration-resistance is a *balance*, not a fortress: the design choices that maximize raw chip-resistance (huge memory, floating point, dynamic code) are exactly the ones that maximize verification cost and network bloat, and even they only buy time. Equi-X is the design that strikes the balance best — it keeps the resistance that matters against the accelerators attackers actually use, pays almost nothing to verify, fits on any device, and is honest enough to plan for the chip instead of pretending it will never come. That combination, proven in the wild, is why it tops this survey.

---

# Part 7 — Reference tables

## 22. Master classification matrix (by scarce resource)

The high-level taxonomy: what each class makes scarce, and which specialist advantage that neutralizes.

| Class | Scarce resource | Advantage neutralized | Representative algorithms |
|---|---|---|---|
| Compute / sequential-time | CPU cycles | (baseline — ASICs dominate) | SHA-256; X11, X16R |
| Memory-capacity-hard | RAM capacity | Area | Argon2i/d, Balloon, Equihash, MTP, Ethash |
| Bandwidth-hard | Off-chip DRAM traffic | Energy | scrypt, Catena-BRG, Balloon, Ethash, ProgPoW |
| Latency + compute (CPU-VM) | CPU memory latency + ALU/FPU | Area + energy | CryptoNight, RandomX, **HashX / Equi-X core** |
| Space / space-time | Commodity storage over time | Compute entirely (sidestepped) | PoSpace, PoST, Chia, Spacemesh |

## 23. Parameter cheat-sheet (the three axes at a glance)

Approximate figures; parameters are tunable and the numbers below reflect the commonly-cited deployments.

| Algorithm | Time (work) | Memory | Proof / message | Verify cost | Note |
|---|---|---|---|---|---|
| scrypt | N iterations | 128·N·r bytes (tunable) | — (symmetric) | redo the work | Maximally memory-hard; failed at tiny N |
| Argon2d | t passes | m KiB → GiBs | — (symmetric) | redo the work | Primitive inside RandomX & MTP |
| Equihash (200,9) | Wagner search | ~144 MB | 1,344 B | a few hashes | ASIC'd 2018 (Z9) |
| Cuckoo Cycle | graph build/trim | 128 MB – 2.2 GB | ~168 B | ~84 siphash | Smallest elegant proof |
| MTP | 70 open rounds | ~2 GB | ~180–200 KB | ~70 openings | Abandoned 2021 (proof bloat) |
| Ethash | 64 DAG reads | ~5 GB DAG (16 MB light) | ~40 B | light cache | PoW retired 2022 |
| ProgPoW | random prog + 64 reads | ~5 GB DAG | ~40 B | light cache | ~1.1–1.2× ASIC gap |
| CryptoNight | scratchpad loop | 2 MB | small | redo | ASIC'd ~2017 |
| RandomX | 8 progs × 256 instr | 2,080 MiB (256 MiB light) | small | **256 MiB, ~ms** | **ASICs since 2024** |
| yescrypt | tunable | tunable (R8–R32) | — (symmetric) | redo | CPU-friendly, GPU-unfriendly |
| Chia (PoSpace-Time) | one-time plotting | ≥101.4 GiB disk | 256 B | a few hashes | Storage, not compute |
| HashX (bare) | random program | memory-light | — (puzzle) | ~µs | FPGA-viable *alone* |
| **Equi-X** | **HashX program + solve** | **~1.8 MiB** | **16 B** | **~50 µs** | **GPU+FPGA-resistant; Tor 0.4.8 (2023)** |

---

## Glossary

**Proof-of-work (PoW).** A puzzle that takes real computer effort to solve but is easy to check, used to earn something (a block reward, or the right to make a request) so that the effort itself keeps the system honest or affordable.

**CPU / GPU / FPGA / ASIC.** The four rungs of hardware, from flexible to specialized. A **CPU** is the general-purpose processor in every computer. A **GPU** (graphics card) does thousands of identical operations at once. An **FPGA** is a chip you can re-wire for one fixed task. An **ASIC** is a chip permanently built for one task only — the fastest and least flexible.

**Accelerator / acceleration resistance.** An accelerator is any hardware or algorithm that solves the puzzle far more cheaply than the everyday machine the designer intended. A puzzle is *acceleration-resistant* if it denies those shortcuts, keeping ordinary hardware competitive. "ASIC resistance" is the strongest hardware case of this.

**Absolute vs. economic resistance.** *Absolute* resistance (no accelerator can ever help) is impossible. *Economic* resistance (the accelerator's advantage is too small to be worth building) is the real goal.

**Memory-hard.** A puzzle deliberately built to need a large amount of memory, because memory is cheap on a normal computer but expensive to replicate on a chip.

**Capacity-hard vs. bandwidth-hard.** *Capacity-hard* means you need a lot of memory at once (fights a chip's size advantage). *Bandwidth-hard* means you must move a lot of data back and forth (fights a chip's energy advantage, which is bigger). The strongest designs are both.

**Latency-bound.** Bottlenecked by the *delay* before memory responds, not by how much data moves. Memory delay has barely improved for years, so latency-bound puzzles have a durable moat — until on-chip caches grow large enough to swallow the working data.

**Data-dependent vs. data-independent.** Whether the memory addresses a puzzle touches depend on the data being hashed. Data-dependent is harder to accelerate (preferred for PoW); data-independent is safer for passwords but provably weaker.

**Asymmetric puzzle.** Hard to solve, but trivially easy and cheap to *check* — like a completed jigsaw. The single most valuable property for real-world deployment.

**Symmetric puzzle.** One where checking a solution costs about as much as producing it (the verifier redoes the work) — bad for any system that checks many solutions.

**Proof / message size.** How many bytes a solution adds to every block or request. Small is good; large proofs clog the network.

**Time-memory tradeoff / amortization.** Algorithmic shortcuts that cut the honest cost with no new hardware — e.g. using less memory in exchange for extra recomputation, or sharing work across many attempts.

**KDF (key-derivation function).** A function (scrypt, Argon2) originally for turning passwords into keys, borrowed for PoW because it is memory-hard.

**DAG.** A large table of data too big to fit on a chip, streamed from memory during solving (Ethash, ProgPoW).

**Scratchpad.** A block of fast memory a puzzle reads and writes in a tight loop (CryptoNight, RandomX).

**Proof-of-space / space-time.** Prove you set aside disk *space* (and held it over *time*) instead of doing computation — sidesteps the chip race and uses little energy (Chia, Spacemesh).

**VDF (verifiable delay function).** A computation that provably takes a set amount of wall-clock time and can't be sped up by parallelism; used with proof-of-space to stop cheating.

**Zero-knowledge proof / ZK-friendly.** A way to prove a statement is true (e.g. "I solved the puzzle") while revealing nothing else. A puzzle is *ZK-friendly* if that proof is cheap to produce — which, happily, tracks with cheap verification.

**Denial-of-service (DoS) / client puzzle.** An attack that floods a service with junk requests; a *client puzzle* makes each request cost a little work so floods become unaffordable. The job Equi-X was built for.

**Hard fork / patchable.** Changing the puzzle. A website can patch its puzzle instantly (bricking any attacker's chip); a cryptocurrency needs a slow, contentious "hard fork," which is why coins fear ASICs more.

**Unified memory (UMA).** Modern designs (e.g. Apple M-series) where the CPU and GPU share one memory pool, which weakens puzzles that relied on a GPU's memory being separate and limited.

**Equihash / generalized birthday.** An asymmetric PoW: find a set of hash outputs that combine to zero. Small-ish proof, cheap verify; the structural parent of Equi-X.

**RandomX / HashX.** RandomX is Monero's CPU-bound puzzle that runs a fresh random program each time — the strongest acceleration mechanism, but heavy to verify. **HashX** is its small, memory-light sibling, used as the engine inside Equi-X.

**Equi-X.** The 2023 design (by RandomX's author) that puts a HashX program inside an Equihash structure: RandomX-grade GPU/FPGA resistance with a 16-byte answer, ~50 µs verification, and a ~1.8 MB footprint. Deployed in Tor. The best candidate in this survey.

---

## Sources & further reading

**The updated facts (2024–2026).**

- RandomX ASIC miners (Antminer X5 / X9, Pinecone R1X) — [Monero Mining Guide 2026, MillionMiner](https://millionminer.com/news/monero-mining-guide-2026-antminer-x5-x9-pinecone-r1x-randomx); [Antminer X5 profit/specs, ASIC Miner Value](https://www.asicminervalue.com/miners/bitmain/antminer-x5)
- Equi-X in Tor — [Onion-service PoW: Version 1, Equi-X and Blake2b (Tor spec)](https://spec.torproject.org/hspow-spec/v1-equix.html); [Introducing Proof-of-Work Defense for Onion Services (Tor Project blog)](https://blog.torproject.org/introducing-proof-of-work-defense-for-onion-services/); [Proposal 327: PoW over introduction](https://spec.torproject.org/proposals/327-pow-over-intro.html)
- Equi-X / HashX reference implementation — [tevador/equix](https://github.com/tevador/equix) and [tevador/hashx](https://github.com/tevador/hashx)

**Foundational theory.**

- [Stronger Key Derivation via Sequential Memory-Hard Functions](https://www.tarsnap.com/scrypt/scrypt.pdf) — Percival, 2009 (scrypt)
- [Scrypt is Maximally Memory-Hard](https://eprint.iacr.org/2016/989.pdf) — Alwen et al., EUROCRYPT 2017
- [Efficiently Computing Data-Independent Memory-Hard Functions](https://eprint.iacr.org/2016/115) — Alwen, Blocki, CRYPTO 2016 (the iMHF barrier)
- [Bandwidth Hard Functions for ASIC Resistance](https://eprint.iacr.org/2017/225.pdf) — Ren, Devadas, TCC 2017
- [Argon2 / RFC 9106](https://www.rfc-editor.org/rfc/rfc9106.html) — IRTF CFRG, 2021

**The algorithms.**

- [Equihash: Asymmetric PoW Based on the Generalized Birthday Problem](https://eprint.iacr.org/2015/946.pdf) — Biryukov, Khovratovich, NDSS 2016
- [Cuckoo Cycle](https://eprint.iacr.org/2014/059.pdf) — Tromp, 2014
- [Egalitarian Computing (MTP)](https://arxiv.org/pdf/1606.03588) — Biryukov, Khovratovich, USENIX 2016; and the [MTP tradeoff attack](https://eprint.iacr.org/2017/497.pdf) — Dinur, Nadler, 2017
- [EIP-1057: ProgPoW](https://eips.ethereum.org/EIPS/eip-1057) — IfDefElse, 2018; [Ethash spec](https://ethereum.org/en/developers/docs/consensus-mechanisms/pow/mining-algorithms/ethash/)
- [RandomX specification](https://github.com/tevador/RandomX/blob/master/doc/specs.md) and [design](https://github.com/tevador/RandomX/blob/master/doc/design.md) — tevador et al., 2019
- [Proofs of Space](https://eprint.iacr.org/2013/796) — Dziembowski et al., 2015; [Chia greenpaper](https://www.chia.net/wp-content/uploads/2023/01/proof_of_space.pdf); [Spacemesh PoST](https://platform.spacemesh.io/docs/protocol/mining/post/)

**Economics & hardware trends.**

- [On Mining](https://blog.ethereum.org/2014/06/19/mining) — Buterin, 2014 (economic ASIC resistance)
- [The State of Cryptocurrency Mining](https://medium.com/obelisk-blog/the-state-of-cryptocurrency-mining-2d8521bd754a) — Vorick, 2018
- [AI and Memory Wall](https://arxiv.org/html/2403.14123v1) — Gholami et al., 2024 (bandwidth vs. latency divergence)
- [Inside the AMD Instinct MI300A's Memory Subsystem](https://chipsandcheese.com/p/inside-the-amd-radeon-instinct-mi300as) — Chips and Cheese, 2025

**Client puzzles & DoS.**

- [Pricing via Processing, or Combatting Junk Mail](https://link.springer.com/chapter/10.1007/3-540-48071-4_10) — Dwork, Naor, 1992
- [Hashcash — A Denial of Service Counter-Measure](http://www.hashcash.org/hashcash.pdf) — Back, 2002

---

*Companion documents in this project (in the workspace folder): the Equi-X Research Survey and Technical Reference, the RandomX survey pair, the Memory-Latency-Bound-Functions and PoW-Design-Discussion notes, the five-volume Equi-X Markdown series, and the LaTeX-built books (Equi-X Complete Reference, Acceleration-Resistant PoW Field Guide).*





