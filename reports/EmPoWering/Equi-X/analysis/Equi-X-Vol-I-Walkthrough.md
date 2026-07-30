# Equi-X — An Implementation Walkthrough and Analysis

### Volume I: a unified, comparative reading of the C and Rust code, built to give you the *intuition* first

*Part of the Equi-X implementation series — Volume I of V (II: Deep Analysis · III: Attacking & Accelerating · IV: PoW Landscape · V: Future Directions). Companion to the Equi-X Technical Reference and Research Survey · June 2026 · revised July 2026*

---

## 0. What this document is

The Technical Reference in this project specifies *what* Equi-X computes. This document reads the *code that actually computes it* and tries to make the design click — why each piece exists, what it is really doing, and how the two real-world implementations express the same idea in very different styles.

It is **unified and comparative**: instead of two separate tours, we follow the data as it flows through the algorithm and, at each step, look at both implementations side by side. It is also **intuition-first** — code appears only where it illuminates an idea, and every snippet is preceded by the mental model it supports.

The two implementations:

| | Reference C | Rust (Arti) |
|---|---|---|
| Repos | [`tevador/equix`](https://github.com/tevador/equix) + [`tevador/hashx`](https://github.com/tevador/hashx) | `equix` + `hashx` crates (part of [Arti](https://gitlab.torproject.org/tpo/core/arti)) |
| Version read here | v1.0.0 (2020) | `equix` 0.6.1 · `hashx` 0.7.1 |
| Author / maintainer | tevador (designer) | The Tor Project |
| Role | The normative, canonical behavior | A safe, idiomatic reimplementation, bug-for-bug compatible |
| License | LGPL-3.0 | LGPL-3.0 |

A crucial fact that shapes everything below: **there is no separate written specification.** The C code *is* the specification, and the Rust crates are written to reproduce its output exactly — including quirks the Rust authors flag as probable bugs but deliberately preserve. Both ship the same published test vectors.

*(Version currency, July 2026: the C is unchanged — v1.0.0 is still the only tagged release — and the crates have moved on to `equix` 0.7.0 / `hashx` 0.9.0, published June 30, 2026. The newer crate versions carry no algorithmic changes; the test vectors freeze the behavior this volume describes.)*

---

## 1. The one-paragraph mental model

Equi-X is an **asymmetric client puzzle**: hard to solve, trivial to check. It is built from two layers that solve two different problems.

> **Layer 1 — HashX** turns a *challenge* into a brand-new, one-off **hash function**. Not a hash *value* — an actual function, a little randomly-generated program of integer math. This is the trick that makes the puzzle CPU-friendly: the program is shaped to saturate a real CPU pipeline, so specialized hardware can't do much better than your laptop.
>
> **Layer 2 — Equihash(60, 3)** poses a search puzzle *over that function*: find **eight 16-bit inputs whose hash outputs sum to zero in the low 60 bits** (modular addition, not XOR). Finding them needs a memory-hungry birthday search; checking them needs just eight hash evaluations and seven additions.

Everything else is detail in service of those two sentences. Hold onto this picture:

```text
  challenge bytes
        │
        ▼
 ┌─────────────────────────────────────────────┐
 │ LAYER 1: HashX                               │
 │   Blake2b("HashX v1") ── 512-bit seed        │
 │        │                                     │
 │        ├── key0 ─▶ SipHash1,3 PRNG ─▶ generate a 512-instruction program
 │        │                                (simulated superscalar CPU)
 │        └── key1 ─▶ register init + digest    │
 │                                              │
 │   H(i) :  i (u64) ─▶ [run program] ─▶ 64-bit digest
 └─────────────────────────────────────────────┘
        │   (H is now a fixed function of the challenge)
        ▼
 ┌─────────────────────────────────────────────┐
 │ LAYER 2: Equihash(60,3), SUM not XOR         │
 │   find i0..i7 in [0, 2^16) with              │
 │     H(i0)+...+H(i7) ≡ 0 (mod 2^60)           │
 │   via Wagner's tree:                         │
 │     pairs cancel 15 bits ─▶ quads 30 ─▶ all-8 60
 └─────────────────────────────────────────────┘
        │
        ▼
   solution = 8 × u16  = 16 bytes
```

The rest of the document expands each box, then steps back to compare the two codebases and draw out what the implementation teaches about the design.

---

## 2. A map of the code

Both projects split cleanly along the two layers. The inner hash lives in its own library (`hashx`); the puzzle layer (`equix`) depends on it.

**Reference C** — small, macro-and-struct, performance-first:

```text
hashx/                          equix/
  include/hashx.h   API           include/equix.h   API
  src/siphash.c     PRNG core      src/equix.c       solve/verify entry + verifier
  src/siphash_rng.c PRNG stream    src/solver.c      Wagner's algorithm (stages 0–3)
  src/program.c     generator      src/solver_heap.h the 1.81 MiB memory layout
  src/program_exec.c interpreter   src/context.c     allocation
  src/compiler_x86.c JIT (x86-64)
  src/compiler_a64.c JIT (ARM64)
  src/hashx.c       exec + digest
```

**Rust (Arti)** — typed, generic, safety-annotated:

```text
hashx/src/                      equix/src/
  lib.rs        HashX/Builder     lib.rs         EquiX/Builder + free fns
  siphash.rs    PRNG core         solution.rs    puzzle definition + verify
  rand.rs       PRNG stream       solver.rs      Wagner's algorithm (3 layers)
  generator.rs  generator         collision.rs   the collision search primitive
  scheduler.rs  superscalar model bucket_array/  generic sorting-bucket memory
  constraints.rs program rules
  program.rs    instr set + interpreter
  compiler/     JIT (dynasmrt)
  register.rs   register file + digest
```

The public entry points line up almost one to one:

| Operation | C | Rust |
|---|---|---|
| Make the puzzle's hash | `hashx_make(ctx, seed, len)` | `HashX::new(seed)` |
| Evaluate the hash | `hashx_exec(ctx, i, out)` | `hash.hash_to_u64(i)` |
| Build an Equi-X instance | `equix_alloc` + first `equix_solve`/`verify` | `EquiX::new(challenge)` |
| Solve | `equix_solve(ctx, ch, len, out[8])` | `equix::solve(challenge)` |
| Verify | `equix_verify(ctx, ch, len, sol)` | `equix::verify(challenge, sol)` |

Notice the Rust API returns a *value* (`EquiX`, `Solution`) where C fills a caller-owned buffer and returns a status — the first of many "same algorithm, different idiom" contrasts.

---

## 3. Layer 1 — HashX, a hash function generated per challenge

This is the conceptually deepest part of Equi-X, so we spend the most time here. The promise of HashX: **given a seed, deterministically produce a unique one-way function** whose runtime cost is essentially fixed and whose shape resembles a tight loop of dependent integer instructions on a real CPU.

### 3.1 Seeding — from arbitrary bytes to two key blocks

Everything starts by stretching the seed (for Equi-X, the challenge string) into 512 pseudorandom bits with Blake2b, personalized with the literal string `"HashX v1"`. Those 512 bits are split into **two** 256-bit SipHash key blocks with different jobs:

- **key0** seeds the PRNG that *generates the program*.
- **key1** seeds the *register file* at hash time and is folded back in during finalization.

The Rust says this almost declaratively:

```rust
// hashx/src/siphash.rs
pub fn pair_from_seed(seed: &[u8]) -> (SipState, SipState) {
    let mut core = Core::new_with_params(b"HashX v1", &[], 0, 64);   // Blake2b, 64-byte out
    // ... hash the seed ...
    (Self::new_from_bytes(&digest[0..32]),     // key0  → program generator
     Self::new_from_bytes(&digest[32..64]))    // key1  → register init + digest
}
```

The C is the same computation inside `hashx_make`: `blake2b` the seed into `siphash_state keys[2]`, hand `keys[0]` to the generator and stash `keys[1]` for execution.

> **Intuition.** The seed never touches the math directly. It is laundered through Blake2b so that even a tiny challenge change produces a completely different program *and* different register initialization. key0 and key1 are kept separate so the program's *structure* and its *input mixing* are independent pseudorandom streams.

### 3.2 The PRNG — SipHash as a faucet of decision bits

Program generation is a long sequence of small random choices ("which opcode? which register? which rotation amount?"). HashX draws them from **SipHash1,3 in counter mode**: a fast, weak-but-sufficient stream, since this randomness only has to be unpredictable enough to resist shortcutting, not cryptographically strong.

```rust
// hashx/src/rand.rs — the underlying 64-bit stream
fn next_u64(&mut self) -> u64 {
    let value = siphash13_ctr(self.key, self.counter);   // SipHash1,3(key0, counter)
    self.counter += 1;
    value
}
```

A subtlety worth its own note, because it is exactly the kind of thing a reimplementation must get bit-for-bit right: the generator consumes a mix of `u8` and `u32` values, and both are carved out of that shared `u64` stream through small queues. The Rust wraps this in an `RngBuffer` holding "up to one u32 and up to seven bytes," and the C does the equivalent in `siphash_rng.c`. The *order* in which u8s and u32s are pulled changes which bytes of each u64 go where — so the queueing rule is part of the spec, not an implementation detail. The Rust comments call this out explicitly and even ship a captured reference stream as a test.

### 3.3 What a "program" is

A HashX program is a fixed-length list of **512 instructions** over a tiny register-only virtual machine: **8 integer registers (R0–R7), no memory, no I/O.** The instruction set is deliberately small and CPU-flavored:

| Instruction | Meaning | Latency | Notes |
|---|---|---|---|
| `UMULH_R` / `SMULH_R` | high 64 bits of a 64×64 multiply (unsigned/signed) | 4 | sets the value tested by the next branch |
| `MUL_R` | `dst *= src` (low 64 bits) | 3 | |
| `ADD_RS` | `dst += src << s`, `s ∈ 0..3` | 1 | `dst ≠ R5` (an x86 encoding quirk) |
| `SUB_R`, `XOR_R` | register–register | 1 | `dst ≠ src` |
| `ADD_C`, `XOR_C` | with a sign-extended 32-bit constant | 1 | |
| `ROR_C` | rotate right by a constant | 1 | |
| `TARGET` / `BRANCH` | the one-shot conditional jump | 1 | see below |

The Rust models this as an `enum Instruction`; the C as a `struct instruction { opcode; src; dst; imm32; op_par; }`. Same eleven operations.

**The one-shot branch** is HashX's signature anti-GPU feature. `TARGET` marks a spot; `BRANCH` carries a 32-bit mask with exactly 4 bits set, and jumps back to the target *iff* the masked bits of the last wide-multiply result are zero — but **at most once per execution**. The interpreter shows the whole mechanism plainly:

```rust
// hashx/src/program.rs (interpret)
Instruction::Branch { mask } => {
    if allow_branch && (mask & mulh_result) == 0 {
        allow_branch = false;                 // fuse blows: never branch again
        branch_target
            .expect("generated programs always have a target before branch")
    } else { next_pc }
}
```

> **Intuition.** A 4-bit mask means the branch is taken with probability ≈ 1/16, and it depends on data the CPU can't know until mid-execution. That single unpredictable, input-dependent jump is cheap on a CPU's branch predictor but punishes the lock-step execution model of GPUs. Making it *one-shot* keeps every instance's worst-case runtime bounded and uniform — there is no loop to unroll.

### 3.4 The heart: generating a program by simulating a CPU

Here is the idea that makes HashX more than "a random sequence of ops." The generator builds the program **against a simulated superscalar CPU** (modeled on Intel Ivy Bridge: 3 execution ports, instruction latencies, in-order issue). It only emits an instruction if the simulated CPU could issue it *now* without stalling, and it keeps going until a fixed cycle budget is spent. A program is accepted only if it lands on exact targets.

The scheduler model is stated as constants — and the C and Rust agree to the number:

```rust
// hashx/src/scheduler.rs
const TARGET_CYCLES: usize = 192;       // stop issuing once we reach this cycle
const NUM_EXECUTION_PORTS: usize = 3;   // P5, P0, P1  (multiply only on P1)
// latency: ALU = 1, Mul = 3, wide-mul (UMulH/SMulH) = 4
```

```c
/* hashx/src/program.c */
#define TARGET_CYCLE 192
#define REQUIREMENT_SIZE 512
#define REQUIREMENT_MUL_COUNT 192
#define REQUIREMENT_LATENCY 195
```

The generator threads three pieces of state (named the same in both languages):

1. **A scheduler** (`scheduler.rs` / the port map in `program.c`) — a scoreboard of which of the 3 ports are busy on which cycle, and when each register's last write retires. It answers "at the earliest cycle, on which port, could this op run, and which registers are ready by then?"
2. **A validator / constraints** (`constraints.rs`) — the anti-shortcut rules: no two identical ops back to back, no back-to-back register add/sub, no `dst == src` for several ops, R5 may not be an `ADD_RS` destination, and others.
3. **A selector pattern** — the opcode to attempt is chosen by position in a repeating **36-sub-cycle template**, so the *mix* of instructions (and the count of multiplies and branches) is constant across all instances.

The selector pattern is the clearest single piece of "why programs look alike":

```rust
// hashx/src/generator.rs — choose_opcode_selector (paraphrased)
let n = sub_cycle % 36;
if n == 1            { Target }
else if n == 19      { Branch }
else if n == 12 || n == 24 { WideMul }
else if n % 3 == 0   { Mul }            // the (Mul, _, _) backbone
else                 { Normal }          // Add/Sub/Xor/Rotate/...
```

Generation is **multi-pass and self-healing**. For each slot it tries an *original* pass; if register selection fails it tries a simplified *retry* pass (immediate-source ops only); if that also fails it **stalls** one cycle (advancing simulated time so more registers retire) and tries again. The Rust loop is the readable version of the same control flow in C's big `while` loop:

```rust
// hashx/src/generator.rs
fn generate_instruction(&mut self) -> Result<.., ()> {
    loop {
        if let Ok(r) = self.instruction_gen_attempt(Pass::Original) { return Ok(r); }
        if let Ok(r) = self.instruction_gen_attempt(Pass::Retry)    { return Ok(r); }
        self.scheduler.stall()?;          // ran out of time → stop
    }
}
```

Finally, **acceptance**. A finished program is kept only if it hits all three targets exactly:

```rust
// hashx/src/constraints.rs — check_whole_program
instructions.len() == 512
  && scheduler.overall_latency() == 194     // last write retires here
  && multiply_count == 192
```

This is where the famous "≈195 cycles" and "192 multiplies" come from. Note the off-by-one that a careful reader will trip on: Rust checks `== 194` while C `#define`s `REQUIREMENT_LATENCY 195`. They agree — the C acceptance test is `latency == REQUIREMENT_LATENCY - 1` with the comment *"cycles are numbered from 0."* So both require the final register write to retire on the 195th cycle (index 194). About **1 seed in a few thousand** fails these checks; the caller must skip it (`Error::ProgramConstraints` / `hashx_make` returns 0).

> **Intuition.** The acceptance criteria are the real "proof of work shape." By forcing every accepted program to contain exactly 192 multiplications and to fill a ~195-cycle dependency chain on a realistic 3-port machine, HashX guarantees that (a) every instance costs the same, and (b) the cost is dominated by a long chain of multiplies that a CPU is *already optimized for* and that a GPU/FPGA cannot meaningfully accelerate. The program generator is, in effect, a tiny optimizing compiler run backwards: it manufactures code that is maximally friendly to a CPU and maximally boring to anything else.

### 3.5 Evaluating the hash

With a program in hand, computing `H(input)` is three steps, identical in both languages:

1. **Initialize 8 registers** from key1 and the input via SipHash2,4 counter mode (`siphash24_ctr(key1, input)` → `[u64; 8]`).
2. **Run the program** (interpret or JIT — next section).
3. **Finalize / digest** to remove a multiply-induced bias toward zero, then fold to the output width.

The digest is small and worth seeing because it pins down the output exactly — and because the C and Rust are byte-identical here:

```rust
// hashx/src/register.rs — digest (Equi-X uses only the first returned word)
let mut x = SipState { v0: r0+key.v0, v1: r1+key.v1, v2: r2, v3: r3 };
let mut y = SipState { v0: r4, v1: r5, v2: r6+key.v2, v3: r7+key.v3 };
x.sip_round();  y.sip_round();
[x.v0 ^ y.v0, x.v1 ^ y.v1, x.v2 ^ y.v2, x.v3 ^ y.v3]
```

```c
/* hashx/src/hashx.c — same arithmetic */
r[0]+=keys.v0; r[1]+=keys.v1; r[6]+=keys.v2; r[7]+=keys.v3;
SIPROUND(r[0],r[1],r[2],r[3]);  SIPROUND(r[4],r[5],r[6],r[7]);
/* out: r[0]^r[4], r[1]^r[5], r[2]^r[6], r[3]^r[7] */
```

Equi-X calls the inner hash with the 16-bit index as the input and keeps only the **first 64-bit word** of the digest (of which the low 60 bits matter). In Rust that is `hash_to_u64(item)`; in C it is `load64(hash)` of the first eight output bytes.

> **Intuition.** Initialization makes the input "spray" across all 8 registers before any program logic runs; finalization runs one SipHash round over each half and XOR-combines them so that the heavy multiplications (which statistically pull bits toward 0) don't bias the output. The result behaves like a good hash even though the middle is a random integer program.

### 3.6 Interpreter vs JIT — the same program, two engines

Both libraries can either **interpret** the instruction list or **JIT-compile** it to native code; both default to "try to compile, fall back to interpret." The compiled path is roughly an order of magnitude faster and is what real deployments use.

The difference is purely in *how* they emit machine code:

- **C** hand-emits raw opcode bytes. `compiler_x86.c` is full of `memcpy`'d byte arrays with assembly in the comments — e.g. the prologue loads R0–R7 into the native registers `r8`–`r15`:

  ```c
  static const uint8_t x86_prologue[] = {
      0x48,0x89,0xF9,        /* mov rcx, rdi  ; rcx = &registers */
      ...
      0x4C,0x8B,0x01,        /* mov r8,  [rcx+0]   ; R0 */
      0x4C,0x8B,0x49,0x08,   /* mov r9,  [rcx+8]   ; R1 */
      ... };                  /* one emitter each for x86-64 and ARM64 */
  ```

- **Rust** uses the `dynasmrt` runtime-assembler crate and the `dynasm!` macro, so the backend reads like annotated assembly rather than hex:

  ```rust
  // hashx/src/compiler/x86_64.rs
  use dynasmrt::{DynasmApi, DynasmLabelApi, x64};
  dynasm!(asm ; .arch x64 ; mov rcx, rdi ; ...);
  ```

Both map HashX's 8 virtual registers onto the same physical registers and produce a function that takes a pointer to the register file. The choice is an engineering trade — the C is dependency-free and tiny; the Rust is far more readable and memory-safe at the cost of a build-time assembler dependency. The mapping detail also explains a generation-time rule we already met: **R5 ↔ x86 `r13`**, whose addressing-mode encoding forces the "no `ADD_RS` into R5" constraint *even on ARM*, so that every backend produces the same program.

---

## 4. Layer 2 — Equihash(60, 3): the search puzzle

Now `H` is a fixed function. The puzzle is to find structure in its outputs. Equi-X uses Equihash with two changes the C README states up front:

> "It is based on Equihash(60, 3) with two major changes: (1) Blake2b is replaced with HashX; (2) **XOR is replaced with modular addition**."

### 4.1 The puzzle, precisely

A solution is **eight 16-bit indices** `i0..i7` such that, writing `H(i)` for the low 64 bits of the inner hash:

```text
H(i0) + H(i1) + ... + H(i7) ≡ 0   (mod 2^60)
```

plus a **partial-sum (tree) structure** proving the solution came from Wagner's algorithm, and an **ordering constraint** that makes each solution canonical (so you can't rearrange one solution into many).

The parameters fall out of the names `N = 60`, `K = 3`:

```rust
// equix/src/solution.rs
pub(crate) const EQUIHASH_N: usize = 60;   // bits that must cancel
pub(crate) const EQUIHASH_K: usize = 3;    // tree depth  →  2^K = 8 items
pub const NUM_ITEMS: usize = 1 << EQUIHASH_K;          // 8
pub const NUM_BYTES: usize = NUM_ITEMS * 2;            // 16-byte solution
```

The "tree structure" is just the requirement that the cancellation happen **level by level**: each adjacent pair cancels the low 15 bits, each group of four cancels 30, and all eight cancel 60. The Rust verifier expresses this with a recursion that is the single clearest statement of the whole puzzle in either codebase:

```rust
// equix/src/solution.rs — check_tree_sums
fn check_tree_sums(func, items, n_bits) -> Result<HashValue, ()> {
    let sum = if items.len() == 2 {
        item_hash(func, items[0]).wrapping_add(item_hash(func, items[1]))
    } else {
        let (left, right) = items.split_at(items.len() / 2);
        check_tree_sums(func, left,  n_bits / 2)?         // 60 → 30 → 15
            .wrapping_add(check_tree_sums(func, right, n_bits / 2)?)
    };
    if (sum & ((1 << n_bits) - 1)) == 0 { Ok(sum) } else { Err(()) }
}
```

Called with `n_bits = 60` on 8 items, it recurses into 30-bit checks on each half and 15-bit checks on each pair — exactly the spec's `STAGE1/STAGE2/FULL` masks. The C verifier (`verify_internal`) is the same logic written flat, with the masks named:

```c
/* equix/src/solver.h */
#define EQUIX_STAGE1_MASK ((1ull << 15) - 1)   /* pairs cancel 15 bits */
#define EQUIX_STAGE2_MASK ((1ull << 30) - 1)   /* quads cancel 30 bits */
#define EQUIX_FULL_MASK   ((1ull << 60) - 1)   /* all eight cancel 60   */
```

> **Why SUM instead of XOR — the decisive line.** Equihash's security assumes a *collision-resistant* inner hash, but HashX is only preimage-resistant: about 0.2% of instances have many internal collisions. Under XOR, two equal hashes cancel to zero, so one small multicollision explodes into billions of trivial "solutions." Switching the combiner to addition mod 2^60 means equal values no longer cancel, which neutralizes weak instances — and, as a bonus, modular adders with their carry chains cost custom hardware slightly more than XOR gates. This one substitution is what lets Equi-X safely build on a non-collision-resistant hash, and it is why the solver below works with carries.

### 4.2 Intuition for Wagner's algorithm

Brute force over eight indices is `(2^16)^8 = 2^128` — hopeless. Wagner's generalized-birthday algorithm trades memory for time and finds the eight-way sum in a tree of two-way steps:

1. Compute all `2^16` hashes (cheap — that's only 65,536 evaluations).
2. **Find pairs** whose sum has the low 15 bits zero. There are ~65,536 hashes and ~2^15 possible low-15-bit values, so by the birthday principle you get ~2^16 such pairs.
3. **Find pairs of pairs** whose (already-15-bit-zero) sums *also* zero the next 15 bits — now 30 bits are zero across four indices.
4. **Find pairs of quads** that zero the final 30 bits — 60 bits zero across all eight. Those are solutions (~2 per challenge on average).

The engine for "find pairs that cancel the next 15 bits" is bucketing: drop every value into a bucket keyed by the bits that must cancel, then only compare values in **complementary** buckets (bucket `b` with bucket `−b`), because only those *can* sum to zero in those bits. That is the birthday meet-in-the-middle, made concrete.

### 4.3 The solver, walked

Both solvers implement exactly that tree, with **identical bucket geometry** (this is deliberate — it makes them discard the same overflow solutions and thus produce identical output):

```text
INDEX_SPACE        = 2^16 = 65536      coarse buckets = 256  (8 bits)
COARSE_BUCKET_ITEMS = 336              fine buckets   = 128  (7 bits)
FINE_BUCKET_ITEMS   = 12               8 + 7          = 15 bits cancelled per layer
```

Each 15-bit cancellation is split into a **coarse** pass (8 bits, by `value % 256`) and a **fine** pass (7 bits, by `value % 128`) using a small scratch hash table — `8 + 7 = 15`. Stage 0 fills the first table; stages 1–3 each cancel 15 more bits:

```c
/* equix/src/solver.c — stage 0: hash everything, bucket by 8 bits */
for (u32 i = 0; i < INDEX_SPACE; ++i) {
    uint64_t value = hash_value(hash_func, i);
    u32 bucket_idx = value % NUM_COARSE_BUCKETS;       /* low 8 bits */
    ...
    STAGE1_DATA(bucket_idx, item_idx) = value / NUM_COARSE_BUCKETS;  /* keep 52 bits */
}
```

The Rust expresses the same three layers declaratively, calling a single generic `collision::search` per layer instead of the C's three near-identical `MAKE_PAIRS` macros:

```rust
// equix/src/solver.rs (structure)
for item in u16::MIN..=u16::MAX { layer0.insert(item_hash(func, item), item); }
collision::search(&layer0, temp, 15,      |sum, loc| layer1.insert(sum, pack(loc)));
collision::search(&layer1, temp, 30 - 15, |sum, loc| layer2.insert(sum, pack(loc)));
collision::search(&layer2, temp, 60 - 30, |_,   loc| { /* assemble 8 items */ });
```

Inside `collision::search`, the complementary-bucket pairing is explicit, and it carries the same **carry-bit correction** the C uses (`value + CARRY`, where `CARRY = bucket_idx != 0`) because the coarse complement wraps mod 256:

```rust
// equix/src/collision.rs
for first_bucket in 0..=(NUM_BUCKETS / 2) {
    let second_bucket = first_bucket.wrapping_neg() % NUM_BUCKETS;   // −b
    // index the first bucket by its key remainder, then for each item in the
    // complementary bucket, look up matches and keep those whose full sum
    // has the required low bits zero:
    if sum.low_bits_are_zero(num_bits) { predicate(sum >> num_bits, location); }
}
```

> **Intuition for the carry.** When you pair bucket `b` with bucket `256 − b`, their coarse parts sum to 256, i.e. they produce a carry *out* of the 8-bit coarse field into the bits above. The `+ CARRY` term re-injects that carry before the fine pass so the arithmetic stays exact. It is a tiny line that is easy to get wrong and is precisely the sort of thing the Rust had to copy faithfully.

### 4.4 Remembering *where* solutions came from

As the tree is built, each combined node must remember its two parents so the eight original indices can be reconstructed at the end. Both implementations pack `(parent bucket, left item index, right item index)` into one integer with the **same bit widths** — 8 bits of bucket, 9 + 9 bits of item index:

```c
/* equix/src/solver.c */
#define MAKE_ITEM(bucket, left, right) ((left) << 17 | (right) << 8 | (bucket))
```

```rust
// equix/src/solver.rs
type Layer0Collision = PackedCollision<u32, 8, 9>;   // BUCKET_BITS = 8, ITEM_BITS = 9
```

At the end, the solver walks this little tree back down to the leaves to collect the eight `SolutionItem`s, then puts them in canonical order. The C does it with explicit swaps guided by the `tree_cmp1/2/4` comparators; the Rust collects then calls `Solution::sort_from_array`. Both enforce the same rule: compare index groups as little-endian byte strings and keep the smaller branch on the left.

```c
/* equix/src/solver.c — build_solution (top level) */
if (!tree_cmp4(&solution->idx[0], &solution->idx[4])) {   /* 8-byte LE compare */
    SWAP_IDX(solution->idx[0], solution->idx[4]); ... }    /* swap whole quads */
```

```rust
// equix/src/solution.rs — same ordering, as a predicate
fn branches_are_sorted(left, right) -> bool {
    matches!(left.iter().rev().cmp(right.iter().rev()), Less | Equal)
}
```

This ordering is what makes a solution **canonical**: without it, the same eight indices could be emitted in many permutations, each passing the sum test — so the order rule is a genuine part of validity, checked first during verification.

### 4.5 The memory — engineered to live in cache

The whole point of the bucketed search is to fit in CPU cache, where a CPU's memory bandwidth is competitive with a GPU's. Both implementations therefore pack everything into one preallocated block of **~1.81 MiB** and even **reuse** the same bytes for different purposes across stages via a union.

The C declares the layout as a single struct, with a literal `union` overlapping the stage-1 data (no longer needed late) with the stage-3 tables:

```c
/* equix/src/solver_heap.h */
typedef struct solver_heap {
    stage1_idx_hashtab  stage1_indices;     /* 172 544 bytes */
    stage2_idx_hashtab  stage2_indices;     /* 344 576 */
    stage2_data_hashtab stage2_data;        /* 688 128 */
    union {                                  /* reuse the same memory:        */
        stage1_data_hashtab stage1_data;     /*   early stages need this ...   */
        struct { stage3_idx_hashtab stage3_indices;
                 stage3_data_hashtab stage3_data; };   /* ... late stages this */
    };
    fine_hashtab scratch_ht;                /*   3 200 */
} solver_heap;                              /* TOTAL: 1 897 088 bytes */
```

The Rust does the *same optimization* with a checked `union Overlay { first: OverlayFirst, second: OverlaySecond }`, but wraps it in a `MaybeUninit`-based abstraction (`bucket_array`) whose module doc explains the reasoning — a single static layout is "between 2% and 10%" faster than separate allocations, but too large for the stack, so it is built in uninitialized heap memory with access policed by the borrow checker. Its self-test even pins the size:

```rust
// equix/src/solver.rs
assert_eq!(SolverMemory::SIZE, 1_895_424);   // ~1.81 MiB (counters live outside)
```

> The ~1,664-byte difference from the C total is purely because the Rust keeps its per-bucket counters in separate storage. The *engineering intent* is identical: one cache-resident block, reused in place.

### 4.6 Verification — the cheap half

Verification is where "asymmetric" pays off. It needs **no search and no memory** — eight hash evaluations and a handful of additions — and both implementations check from cheapest to most expensive so a flood of junk proofs is rejected almost for free:

1. **Order** — pure integer comparisons on the raw indices, *before any hashing*. Fail → `EQUIX_ORDER` / `Error::Order`.
2. **Challenge** — build the HashX instance; if program generation fails its constraints (the rare ~1-in-several-thousand seed) → `EQUIX_CHALLENGE`.
3. **Sums** — recompute the eight hashes, check the pair/quad partial sums (`EQUIX_PARTIAL_SUM`) and the final 60-bit sum (`EQUIX_FINAL_SUM`). All pass → `EQUIX_OK`.

```c
/* equix/src/equix.c — order first, then hash, then sums */
equix_result equix_verify(ctx, challenge, len, solution) {
    if (!verify_order(solution))                  return EQUIX_ORDER;
    if (!hashx_make(ctx->hash_func, challenge, len)) return EQUIX_CHALLENGE;
    return verify_internal(ctx->hash_func, solution);   /* staged sums */
}
```

The Rust reaches the same order through its type system: you cannot hold a `Solution` without having passed the order check (it is enforced in `try_from_bytes`/`try_from_array`), so `EquiX::verify` only has to "check hash tree sums," exactly as its doc comment says.

> **Intuition.** A verifier does ~50 µs of work to check what cost a solver ~5 ms to find — and it does the free check (ordering) before spending anything on hashing. That asymmetry, plus the tiny 16-byte proof, is the entire reason Equi-X is usable as a DoS defense: an attacker can't make verification itself expensive.

---

## 5. The two implementations, compared

Same algorithm, same outputs, different philosophies. The contrasts are instructive in their own right.

| Dimension | Reference C | Rust (Arti) |
|---|---|---|
| Primary goal | Be the canonical definition; be fast and small | Be safe, auditable, and *exactly* compatible |
| Program/solver code | Macros (`MAKE_PAIRS1/2/3`), structs, manual indexing | Generics + traits (`BucketArray`, `collision::search`, `PackedCollision`) |
| JIT | Hand-emitted opcode bytes (`compiler_x86.c`, `compiler_a64.c`) | `dynasmrt` runtime assembler with `dynasm!` |
| Memory model | One `struct` + `union`, allocated once | `MaybeUninit` block + checked `union`, borrow-policed |
| Errors | Return codes / sentinels (`HASHX_NOTSUPP`, `equix_result`) | `Result<…, Error>` enums |
| API shape | Caller-owned buffers, opaque `ctx` | Owned values, builders, free functions |
| Randomness handling | Implicit in code order | Documented as spec, with captured reference streams as tests |

The most telling detail is **deliberate bug-for-bug compatibility.** During wide-multiply generation, HashX draws an extra 32-bit value from the PRNG and uses it only as a tie-breaker for a writer-collision check. The Rust authors believe this is vestigial — but they keep it, with a comment that doubles as design commentary:

```rust
// hashx/src/constraints.rs
// "As far as I can tell this is a bug in the original implementation but we
//  can't change the behavior without breaking compatibility. ... It seems like
//  this was a vestigial feature ... but I can't be sure."
```

That single comment captures the relationship between the two codebases: **the C defines truth; the Rust reproduces it, warts and all, but explains itself.** For anyone trying to understand *why* a step exists, reading the two together is far more illuminating than either alone — the Rust narrates the intent, the C settles the ground truth.

---

## 6. End-to-end: following one solve and one verify

Pulling the layers together, here is the whole journey with the intuition attached.

**Solving** `solve(challenge)`:

1. `EquiX::new(challenge)` / `equix_solve` → `HashX::new` builds the per-challenge function: Blake2b the challenge, generate a 512-instruction program against the simulated CPU, JIT it. (≈0.05 ms; ~1/few-thousand challenges are rejected here.)
2. Stage 0: evaluate `H` on all 65,536 indices into 256 coarse buckets. (This is the bulk of the ~5 ms; it's just a lot of hashing.)
3. Stages 1–3: three rounds of complementary-bucket pairing, each cancelling 15 more bits (coarse 8 + fine 7), remembering parent pointers.
4. For each all-60-bits-zero hit, walk the parent tree to recover 8 indices, sort them canonically, dedup, and emit. (~2 solutions per challenge on average; at most 8 returned.)

**Verifying** `verify(challenge, solution)`:

1. Check the six ordering comparisons on the raw 16 bytes — no hashing yet.
2. Rebuild `H` from the challenge (fails closed on a bad seed).
3. Evaluate `H` on the eight indices; check pair sums (15 bits), quad sums (30 bits), and the full sum (60 bits), cheapest first.

The asymmetry between these two lists — a memory-bound search over 65,536 hashes versus eight hash evaluations and a few adds — *is* Equi-X.

---

## 7. What the implementation teaches

Reading the code (rather than the spec) surfaces a few things worth stating plainly:

- **The cost is deliberately front-loaded into hashing, not searching.** Stage 0's 65,536 evaluations dominate a solve; the bucketed tree is comparatively cheap. So the puzzle's hardness rests almost entirely on HashX being genuinely CPU-shaped, which is why so much engineering goes into the *generator*, not the search.
- **Determinism is a feature with teeth.** Interpreter and JIT must agree bit-for-bit; C and Rust must agree bit-for-bit; even a probable bug is preserved. The PRNG draw order, the carry bit, the 8/9/9 packing, the `194`-vs-`195` cycle convention — these are not incidental, and the Rust's habit of capturing reference streams as tests is how that discipline is enforced.
- **Memory is treated as the real adversary.** Both keep the solver inside ~1.81 MiB and overlap buffers via a union so the working set stays cache-resident — the precondition for a CPU to compete with a GPU on bandwidth. The Rust shows you can keep that micro-optimization *and* memory safety with `MaybeUninit` and borrow-checked unions.
- **Verification is structurally cheap, by construction.** Ordering is checked before any hash runs; sums are checked cheapest-first. The 16-byte proof and ~50 µs check are what make Equi-X viable as an anti-DoS gate rather than a curiosity.
- **One honest caveat lives in the code.** HashX's branch makes control flow input-dependent, so secret values must never be hashed with it (timing would leak them). For a *public* client puzzle this is fine — and the source treats it as an explicit, accepted trade rather than an accident.

If you want to go deeper, the highest-leverage files to read in full are, in order: `hashx/src/generator.rs` (the idea), `hashx/src/scheduler.rs` (the CPU model), `equix/src/solution.rs` (the puzzle), and `equix/src/solver.c` (the search, most compactly stated). Read each Rust file with its C counterpart open beside it.

---

## Appendix A — Key constants (both implementations agree)

| Constant | Value | Where |
|---|---|---|
| HashX program size | 512 instructions | `NUM_INSTRUCTIONS` / `REQUIREMENT_SIZE` |
| Required multiplies | 192 | `REQUIRED_MULTIPLIES` / `REQUIREMENT_MUL_COUNT` |
| Scheduler target | 192 cycles | `TARGET_CYCLES` / `TARGET_CYCLE` |
| Required final latency | retire at cycle 194 (= "195th", 0-indexed) | `REQUIRED_OVERALL_RESULT_AT_CYCLE` / `REQUIREMENT_LATENCY - 1` |
| Registers | 8 (R5 special-cased) | `NUM_REGISTERS` / `x86_reg_map` |
| Execution ports | 3 (P5, P0, P1; mul on P1) | `scheduler.rs` / `program.c` |
| Branch probability | ≈ 1/16 (mask weight 4) | `BRANCH_MASK_BIT_WEIGHT` / `LOG2_BRANCH_PROB` |
| Equihash N, K | 60, 3 | `EQUIHASH_N/K` |
| Items per solution | 8 → 16 bytes | `NUM_ITEMS` / `EQUIX_NUM_IDX` |
| Index space | 2^16 = 65536 | `INDEX_SPACE` |
| Coarse / fine buckets | 256 / 128 (8 + 7 = 15 bits) | `NUM_COARSE/FINE_BUCKETS` |
| Bucket capacities | 336 coarse / 12 fine | `COARSE/FINE_BUCKET_ITEMS` |
| Stage masks | 2^15−1, 2^30−1, 2^60−1 | `EQUIX_STAGE1/STAGE2/FULL_MASK` |
| Solver memory | ≈ 1.81 MiB (C 1,897,088 B; Rust 1,895,424 B) | `solver_heap` / `SolverMemory::SIZE` |
| Max solutions returned | 8 | `EQUIX_MAX_SOLS` |

## Appendix B — Provenance

- **C:** `tevador/equix` and `tevador/hashx`, v1.0.0 (2020), LGPL-3.0. The normative reference; no separate written spec exists.
- **Rust:** `equix` 0.6.1 and `hashx` 0.7.1 (crates.io), part of the Tor Project's Arti, LGPL-3.0. Written to reproduce the C output exactly; ships the shared Tor test vectors (`tests/tor_equix_vectors.rs`, `hashx_vectors.rs`). Later crate versions (`equix` 0.7.0 / `hashx` 0.9.0, June 2026) change packaging, not behavior.
- Snippets above are lightly trimmed for readability (elided lines marked `...`); identifiers, constants, and control flow are verbatim from the sources named in each caption. Re-verified against the sources, July 2026.

