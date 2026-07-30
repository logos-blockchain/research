# Equi-X — Deep Technical Comparison and Code Analysis

### Volume II: a rigorous C ↔ Rust correspondence, exact algorithmic mechanics, and design analysis

*Part of the Equi-X implementation series — Volume II of V (I: Walkthrough · III: Attacking & Accelerating · IV: PoW Landscape · V: Future Directions) · June 2026 · revised July 2026*

---

## 0. Scope

Volume I built the intuition: HashX manufactures a per-challenge hash function shaped like CPU-friendly code, and Equihash(60, 3) searches for eight inputs whose hashes sum to zero mod 2⁶⁰. This volume assumes that picture and goes underneath it. It is deliberately denser and more code-level, organized around four questions:

1. **Correspondence** — exactly how the C reference and the Rust crates map onto each other, structure by structure.
2. **Mechanics** — the parts Volume I summarized: the PRNG's compatibility contract, the superscalar scheduler, register-selection constraints, the JIT, the bucket solver's arithmetic.
3. **Analysis** — complexity and the birthday accounting; where time and memory actually go; why the solver is heuristic but the verifier is exact.
4. **Discipline** — determinism, bug-for-bug compatibility, and the security-relevant consequences of specific code choices.

Sources are the same four trees as Volume I: C `tevador/equix` + `tevador/hashx` (v1.0.0); Rust `equix` 0.6.1 + `hashx` 0.7.1 (later crate versions — 0.7.0/0.9.0, June 2026 — change packaging, not behavior). Snippets are trimmed (elisions marked `...`) but identifiers, constants, and arithmetic are verbatim; re-verified against the sources, July 2026.

---

## 1. Architectural correspondence

The two codebases are the *same algorithm* under two engineering philosophies: the C is a compact, macro-and-struct performance reference that **defines** the behavior; the Rust is a generic, trait-driven, memory-safe reimplementation that **reproduces** it. The single most useful artifact for reading them together is a map.

### 1.1 HashX (inner hash)

| Concept | C (`hashx/src`) | Rust (`hashx/src`) |
|---|---|---|
| Seed → key material | `hashx_make` → Blake2b(`HashX v1`) → `siphash_state keys[2]` | `SipState::pair_from_seed` → `(key0, key1)` |
| Decision PRNG | `siphash_rng` (`siphash_rng.c`) over SipHash1,3 | `SipRand` + `RngBuffer` (`rand.rs`) over SipHash1,3 |
| Program generator | `hashx_program_generate` (`program.c`) | `Generator::generate_program` (`generator.rs`) |
| Superscalar model | `generator_ctx.ports[]` + `schedule_instr` | `Scheduler` / `ExecSchedule` (`scheduler.rs`) |
| Constraints | inlined in `select_destination`/`select_template` | `Validator` (`constraints.rs`) |
| Instruction repr | `struct instruction {opcode,src,dst,imm32,op_par}` | `enum Instruction { ... }` (`program.rs`) |
| Interpreter | `hashx_program_execute` (`program_exec.c`) | `Program::interpret` (`program.rs`) |
| JIT | `compiler_x86.c`, `compiler_a64.c` (raw bytes) | `compiler/x86_64.rs`, `aarch64.rs` (`dynasmrt`) |
| Register file + digest | `r[8]` + finalize in `hashx_exec` | `RegisterFile` + `digest` (`register.rs`) |
| Failure signal | `hashx_make` returns `0` | `Error::ProgramConstraints` |

### 1.2 Equi-X (puzzle)

| Concept | C (`equix/src`) | Rust (`equix/src`) |
|---|---|---|
| Public puzzle ops | `equix_solve` / `equix_verify` (`equix.c`) | `EquiX::solve` / `verify`, free fns (`lib.rs`) |
| Solution definition + order/sum checks | `verify_order`, `verify_internal` (`equix.c`), `tree_cmp*` (`solver.h`) | `Solution`, `check_tree_order`, `check_tree_sums` (`solution.rs`) |
| Wagner solver | `solve_stage0..3` (`solver.c`) | `find_solutions` + `collision::search` (`solver.rs`, `collision.rs`) |
| Sorting memory | `struct solver_heap` + `union` (`solver_heap.h`) | `BucketArrayMemory` + `Overlay` union (`bucket_array/`) |
| Parent-pointer pack | `MAKE_ITEM(b,l,r)` | `PackedCollision<u32, 8, 9>` |
| Error taxonomy | `enum equix_result` | `enum Error` (`err.rs`) |

Read any Rust file with its C row open beside it and the design becomes legible from both directions: the Rust narrates *intent* in doc-comments, the C settles *ground truth* in bytes.

---

## 2. The HashX generator, exactly

The generator is the part most worth reading at the level of individual decisions, because *every* decision is part of the spec — a compatible third implementation must reproduce all of them bit for bit.

### 2.1 The PRNG and its compatibility contract

HashX draws generation decisions from SipHash1,3 in counter mode, but the *packaging* of that stream into `u8` and `u32` values is itself normative. Two rules matter:

**Rule 1 — big-endian extraction.** Each 64-bit SipHash output is sliced from the most-significant end. The C shifts down by a decreasing count:

```c
/* hashx/src/siphash_rng.c */
uint8_t hashx_siphash_rng_u8(siphash_rng* gen) {
    if (gen->count8 == 0) {
        gen->buffer8 = hashx_siphash13_ctr(gen->counter, &gen->keys);
        gen->counter++;
        gen->count8 = sizeof(gen->buffer8);     /* = 8 */
    }
    gen->count8--;
    return gen->buffer8 >> (gen->count8 * 8);   /* high byte first */
}
```

The Rust reaches the same order by popping bytes off the end of a little-endian array:

```rust
// hashx/src/rand.rs
let bytes = self.inner.next_u64().to_le_bytes();
let (last, saved) = bytes.split_last()...;   // returns MSB first, saves the rest
```

**Rule 2 — separate `u8` and `u32` buffers over one shared counter.** `u8` and `u32` each have their own refill buffer, but both pull from the *same* incrementing counter. So whether a given 64-bit draw becomes bytes or words depends on the **order** in which the generator asks for them — interleaving is part of the contract. The Rust spells this out:

> *"It's important for the u8 and u32 queues to share a common generator. The order of dequeueing u8 items vs u32 items intentionally modifies the assignment of particular u64 RngCore values to the two queues."* — `rand.rs`

Both projects guard this with **captured reference streams** as unit tests (`rng_vectors` in `rand.rs`; the Tor vectors in C). The practical upshot: you cannot refactor the order of `next_u8`/`next_u32` calls without breaking every downstream hash.

### 2.2 The 36-slot instruction template

The opcode attempted at each step is fixed by position in a repeating 36-sub-cycle layout, which is why every accepted program has the same instruction *mix* (notably exactly 192 multiplies and one branch site). The C stores it as an array; the Rust as a match. They are identical:

| sub-cycle mod 36 | C `program_layout[]` | Rust `choose_opcode_selector` | Opcode(s) |
|---|---|---|---|
| 1 | `item_target` | `n == 1` | `TARGET` |
| 19 | `item_branch` | `n == 19` | `BRANCH` |
| 12, 24 | `item_wide_mul` | `n == 12 \|\| 24` | `SMULH`/`UMULH` |
| 0,3,6,9,15,18,21,27,30,33 | `item_mul` | `n % 3 == 0` | `MUL` |
| all others | `item_any` | `Normal` / `ImmediateSrc` | ALU op from a table |

The "any" slot draws from an 8-entry table on the first pass and a 4-entry immediate-source-only table on retry:

```c
/* C: item_any.mask0 = 7 (8 ops), mask1 = 3 (4 ops, no src register) */
const static instr_template* instr_lookup[] =
  { &tpl_ror_c,&tpl_xor_c,&tpl_add_c,&tpl_add_c,&tpl_sub_r,&tpl_xor_r,&tpl_xor_c,&tpl_add_rs };
```

```rust
// Rust: identical tables
const NORMAL_OPS_TABLE:   [Opcode;8] = [Rotate,XorConst,AddConst,AddConst,Sub,Xor,XorConst,AddShift];
const IMMEDIATE_SRC_OPS_TABLE:[Opcode;4] = [Rotate,XorConst,AddConst,AddConst];
```

A subtle shared rule: the `item_any` slot forbids repeating the *previous* op's **group** (`duplicates = false` in C; `disallow_opcode_pair` in Rust), and `Sub` and `AddShift` share one group, so they can't be adjacent either. This is checked at the selector level and costs only a re-roll, not a failed instruction.

### 2.3 The superscalar scheduler

The generator places each instruction on a simulated Ivy-Bridge-like core: **3 ports** (the C calls them P0/P1/P5; multiply lives only on P1), per-opcode **latencies** (ALU 1, `MUL` 3, wide-mul 4), and a per-register **retire-cycle scoreboard**. Two mechanisms deserve attention.

**Port allocation order is P5 → P0 → P1**, deliberately checking the multiply port *last* so general ALU ops don't starve multiplications:

```c
/* hashx/src/program.c — schedule_uop */
if ((uop & PORT_P5) && !ctx->ports[cycle][2]) { ...; return cycle; }
if ((uop & PORT_P0) && !ctx->ports[cycle][0]) { ...; return cycle; }
if ((uop & PORT_P1) && !ctx->ports[cycle][1]) { ...; return cycle; }
```

The Rust encodes the same priority in its bit numbering and iteration:

```rust
// scheduler.rs — P5 = 1<<0, P0 = 1<<1, P1 = 1<<2; iterate indices 0,1,2
for index in 0..NUM_EXECUTION_PORTS { if (ports.0 & (1<<index)) != 0 && !busy { return ... } }
```

**Two-µop instructions** (the wide multiplies, `TARGET`, `BRANCH`) are scheduled *conservatively*: the generator searches forward for the first cycle on which **both** µops can issue simultaneously. The C tries a non-committing probe of both, then commits only on a match:

```c
/* schedule_instr, 2-uop branch */
for (int cycle = ctx->cycle; cycle < PORT_MAP_SIZE; ++cycle) {
    int c1 = schedule_uop(tpl->uop1, ctx, cycle, false);   // probe
    int c2 = schedule_uop(tpl->uop2, ctx, cycle, false);
    if (c1 >= 0 && c1 == c2) { /* commit both */ return c1; }
}
```

The Rust `instruction_plan` does precisely this two-port "same cycle" search and returns an `InstructionPlan` carrying the issue cycle and the chosen ports. The scoreboard then records the destination register's **retire cycle** (`issue + latency`) so later instructions only pick operands that are ready.

### 2.4 Register selection and the constraint stack

Once an opcode and a timing plan exist, the generator must pick source/destination registers that (a) are ready by the issue cycle and (b) satisfy the anti-shortcut rules. The C builds the candidate set with a **branchless filter** that ANDs five conditions and accumulates without a branch:

```c
/* program.c — select_destination (conditions condensed) */
for (int i = 0; i < 8; ++i) {
    bool available = ctx->registers[i].latency <= cycle;                       // ready in time
    available &= ((!tpl->distinct_dst) | (i != instr->src));                   // dst != src (some ops)
    available &= (ctx->chain_mul | (tpl->group != INSTR_MUL_R)
                                 | (ctx->registers[i].last_op != INSTR_MUL_R));// no back-to-back MUL
    available &= ((ctx->registers[i].last_op != tpl->group)
                 | (ctx->registers[i].last_op_par != instr->op_par));          // no trivial repeat
    available &= ((instr->opcode != INSTR_ADD_RS) | (i != 5));                 // R5 not ADD_RS dst
    available_regs[regs_count] = available ? i : 0;
    regs_count += available;
}
```

The Rust expresses the identical five conditions through `RegisterSet::from_filter` plus a `Validator::dst_registers_allowed` checker — same logic, type-checked instead of bit-ANDed. The conditions exist to forbid *optimizable* sequences (`xor r,r`; `ror r,c1; ror r,c2`; runaway multiplication that floods a register with trailing zeros) so that an attacker can't simplify the function.

Two details that a reimplementation must copy and that the Rust flags explicitly:

- **The R5 / `ADD_RS` source short-circuit.** When only two registers are free for an `ADD_RS` and one is R5 (which can't be the *destination*), HashX deterministically forces R5 to be the *source* rather than rolling the dice — preventing a frequent dead-end. Present in both (`select_source` in C; `src_registers_allowed` in Rust).
- **The wide-multiply "vestigial" RNG draw.** `UMULH`/`SMULH` are `op_par_src = false, distinct_dst = false`, so the C falls into `op_par = hashx_siphash_rng_u32(gen)` — it consumes a `u32` whose *only* use is the "no trivial repeat" check above. The Rust keeps it as `RegisterWriter::UMulH(u32)` with a comment calling it a probable bug it cannot remove without breaking compatibility. It costs one PRNG draw per wide multiply and changes the stream alignment for everything after it.

### 2.5 Multi-pass generation, acceptance, and the 194/195 question

Each slot is attempted up to twice before time advances. The C uses an `attempt` counter and `MAX_RETRIES = 1`; on the retry it sets `chain_mul = true` (allowing back-to-back multiplies on a register if nothing else fits — the "prevents catastrophic failure" path). If both attempts fail it advances a full cycle (`sub_cycle += 3`) and resets. The Rust mirrors this as `Pass::Original → Pass::Retry → scheduler.stall()`.

Generation stops when an instruction would schedule at or beyond cycle 192 (`TARGET_CYCLE`), or the 512-slot buffer fills. A finished program is then **accepted only if it hits three exact targets**:

```c
/* program.c — the only thing that makes a program "real" */
return (program->code_size == 512)
     & (ctx.mul_count == 192)
     & (ctx.latency == REQUIREMENT_LATENCY - 1);   /* 195 - 1; "cycles numbered from 0" */
```

```rust
// constraints.rs — same three gates
instructions.len() == 512
  && scheduler.overall_latency().as_usize() == 194
  && multiply_count == 192
```

This resolves a discrepancy a careful reader will hit: the C `#define REQUIREMENT_LATENCY 195` but tests `latency == 194`; the Rust hard-codes `194`. They agree — the final register write must retire on the cycle indexed 194 (the "195th"). The C source notes ~**1 seed in 10,000** fails these gates; the Rust says "once per several thousand." Callers must skip such seeds — this is the `EQUIX_CHALLENGE` / `Error::ProgramConstraints` path, distinct from the ~0.2% of seeds that *generate fine* but are collision-weak (handled by Layer 2's use of addition).

> **What the generator guarantees.** Every accepted instance is a 512-instruction, 192-multiply program whose dependency chain exactly fills a ~195-cycle window on a realistic 3-port core. That uniformity is the proof-of-work "shape": equal cost across instances, dominated by a long multiply chain a CPU executes natively and a GPU/FPGA cannot meaningfully shorten. Generation is itself cheap — O(512) instructions, each a bounded forward search over the ~196-entry port map.

---

## 3. HashX execution: interpreter and JIT

### 3.1 The exact hash pipeline

`H(input)` is fully determined by: initialize 8 registers from `key1` and the input via SipHash2,4 counter mode; run the program; finalize. The arithmetic is unsigned 64-bit **wrapping** throughout, constants are **sign-extended** from 32 bits, rotates are by a constant, and the wide multiplies keep the **upper** 64 bits of a 128-bit product. The finalization (identical in both; verified byte-for-byte) folds `key1` back in to cancel the multiply-induced bias toward zero:

```c
/* hashx.c */
r[0]+=keys.v0; r[1]+=keys.v1; r[6]+=keys.v2; r[7]+=keys.v3;
SIPROUND(r[0],r[1],r[2],r[3]); SIPROUND(r[4],r[5],r[6],r[7]);
/* out = r0^r4, r1^r5, r2^r6, r3^r7 ; Equi-X keeps only out[0..8) */
```

### 3.2 The one-shot branch in three forms

The branch is the same idea expressed three ways, and seeing all three removes any ambiguity about its semantics.

**Interpreter** (both languages identical in effect): a `branch_enable` fuse, blown the first time any branch is taken; the test is against the low 32 bits of the most recent wide-multiply result:

```c
/* program_exec.c */
case INSTR_BRANCH:
    if (branch_enable && (result & instr->imm32) == 0) { i = target; branch_enable = false; }
    break;
```

One micro-difference worth noting for bit-pedants: on a taken branch the **C interpreter resumes at `target + 1`** (the `for` loop's `++i` after `i = target`), whereas the **Rust interpreter re-executes the `Target` instruction** (a no-op that just re-marks the target). Identical results, since `Target` has no effect once the fuse is blown.

**Compiled** (C x86): the one-shot is implemented without a second test by exploiting the flags that caused the jump. The `Target` site is `test edi,edi; «label»: cmovz esi,edi`, and `Branch` is `or edx,esi; test edx,imm; jz label`. When `jz` is taken, the zero flag is still set on arrival at the label, so `cmovz` moves `edi`(= −1) into `esi`; thereafter `or edx,esi` forces the `test` non-zero and the branch can never be taken again. A genuinely elegant branchless disable, and exactly the sort of thing the interpreter exists to specify unambiguously.

### 3.3 JIT: raw bytes vs `dynasmrt`

Both compile the program to native code that takes a pointer to the register file; the difference is how bytes are produced.

The **C** emits pre-encoded machine code, one `EMIT` per instruction, mapping HashX R0–R7 to native `r8`–`r15`:

```c
/* compiler_x86.c — e.g. MUL_R is a single 4-byte imul */
case INSTR_MUL_R:
    EMIT_U32(pos, 0xc0af0f4d | (instr->dst << 27) | (instr->src << 24));   /* imul dst,src */
```

It brackets emission with a **W^X** transition — `hashx_vm_rw(code,…)` before writing, `hashx_vm_rx(code,…)` after — and sizes the page as `align(512·5 + 1024, 4096)` (`COMP_AVG_INSTR_SIZE = 5`). The ARM64 backend (`compiler_a64.c`) does the same with fixed 4-byte instructions (`ldr x7,[x0,#56]`, …).

The **Rust** uses the `dynasmrt` runtime assembler, so the backend reads like annotated assembly and the buffer is an `ExecutableBuffer` mmap managed by the crate:

```rust
// hashx/src/compiler/x86_64.rs
use dynasmrt::{DynasmApi, DynasmLabelApi, x64};
dynasm!(asm ; .arch x64 ; mov rcx, rdi ; ...);
```

Both default to **try-compile-then-fall-back-to-interpret** (`RuntimeOption::TryCompile`; in C, `hashx_alloc(HASHX_COMPILED)` else `HASHX_INTERPRETED`), and the compiler is only available on x86-64 and aarch64 — elsewhere the interpreter is mandatory. The crucial invariant across all four execution engines — C-interp, C-x86, C-arm, and the Rust trio — is **bit-identical output**, enforced by shared test vectors.

> **Determinism is a cross-product property.** {interpret, x86 JIT, arm JIT} × {C, Rust} must all agree, for every seed and input. That is why the generator's PRNG order, the wrapping/sign-extension rules, the digest, and even the "vestigial" draw are pinned: any of them differing would split the matrix.

---

## 4. The Equihash search, analyzed

With `H` fixed, the puzzle is a constrained subset-sum. This section states it formally, explains the solver's arithmetic precisely, and derives its complexity.

### 4.1 The puzzle, formally

A solution is eight 16-bit indices `i0..i7` such that, with `H(i)` the low 64 bits of the inner hash and all sums taken mod 2⁶⁴:

- **Full sum:** `Σ H(iₖ) ≡ 0 (mod 2⁶⁰)`.
- **Tree partial sums (Wagner structure):** each adjacent pair zeros the low 15 bits; each group of four zeros the low 30; all eight zero 60. (`N/(K+1) = 60/4 = 15` bits per level.)
- **Ordering (canonicalization):** at each tree node the left branch must be ≤ the right branch when the index groups are compared as little-endian byte strings (`tree_cmp1/2/4` over 2/4/8 bytes).

The ordering constraint is not cosmetic: without it the same eight hashes could be permuted into many distinct "solutions," so it is a genuine validity condition and is checked *first* (before any hashing) during verification. The Rust verifier is the cleanest statement of the sum tree — one recursion halving the bit-width at each level:

```rust
// equix/src/solution.rs
fn check_tree_sums(func, items, n_bits) -> Result<HashValue, ()> {
    let sum = if items.len() == 2 {
        item_hash(func, items[0]).wrapping_add(item_hash(func, items[1]))
    } else {
        let (l, r) = items.split_at(items.len()/2);
        check_tree_sums(func,l,n_bits/2)?.wrapping_add(check_tree_sums(func,r,n_bits/2)?)
    };
    if (sum & ((1 << n_bits) - 1)) == 0 { Ok(sum) } else { Err(()) }   // 60 → 30 → 15
}
```

### 4.2 Wagner as bucketed meet-in-the-middle, with the carry

Finding the sum directly is `2^128`. Wagner's algorithm finds it level by level: to zero 15 more bits of a sum, bucket every value by those 15 bits and only combine **complementary** buckets — bucket `b` with bucket `−b mod 2¹⁵` — because only those can cancel. Each 15-bit cancellation is split into a **coarse** pass (8 bits, `value % 256`) and a **fine** pass (7 bits, `value % 128`); `8 + 7 = 15`.

The one piece of arithmetic that is easy to get wrong — and therefore a precise compatibility checkpoint — is the **carry correction**. When you pair coarse bucket `b` with bucket `256 − b`, their coarse parts sum to exactly 256, producing a carry out of the 8-bit field. The C re-injects it before the fine pass with `value + CARRY`, where `CARRY = (bucket_idx != 0)`:

```c
/* solver.c — MAKE_PAIRS1 (per layer; same shape for 2 and 3) */
stage1_data_item value = STAGE1_DATA(bucket_idx, item_idx) + CARRY;   /* +1 if b != 0 */
u32 fine_buck_idx   = value % NUM_FINE_BUCKETS;
u32 fine_cpl_bucket = INVERT_SCRATCH(fine_buck_idx);                  /* -f mod 128 */
... stage1_data_item sum = value + cpl_value;
    assert((sum % NUM_FINE_BUCKETS) == 0);                            /* fine bits cancel */
    sum /= NUM_FINE_BUCKETS;                                          /* shift off 7 bits */
```

The Rust performs the identical correction inside `collision::search`, iterating `first_bucket in 0..=(N/2)` and pairing with `first_bucket.wrapping_neg() % N`, then keeping sums whose `low_bits_are_zero(num_bits)`. Same buckets, same complement, same carry — by construction, so that both implementations *discard the same overflow solutions* and emit identical output.

### 4.3 Complexity and the birthday accounting

Let `S = 2¹⁶` be the index space. The four stages:

- **Stage 0** — evaluate `H` on all `S` indices; bucket by 8 bits into 256 coarse buckets. Mean occupancy `S/256 = 256` items/bucket (cap `COARSE_BUCKET_ITEMS = 336`). Cost: `S` HashX evaluations — *this dominates a solve.*
- **Stage 1** — within each complementary coarse-bucket pair (~512 items) sub-bucket by 7 fine bits (128 fine buckets, cap 12) and combine complements. Pairs with low 15 bits zero ≈ `C(S,2) / 2¹⁵ ≈ 2³¹ / 2¹⁵ = 2¹⁶`. So ~`S` items survive into layer 2.
- **Stage 2** — same on the 15-bit-zero items; ~`2¹⁶ / 2¹⁵·... ≈ 2¹⁶` survive with 30 bits zero.
- **Stage 3** — match the final 30 bits; expected solutions ≈ `2¹⁶ / 2¹⁵ ≈ 2`.

That last line is the origin of the famous **"~2 solutions per challenge on average."** Each layer keeps the population near `2¹⁶`, so total work is `Θ(2¹⁶)` operations with a small constant, and **time is dominated by the 65,536 stage-0 hash evaluations**, not the bucketing. Peak memory is the fixed solver heap, ≈ **1.81 MiB**.

**Why the solver is heuristic but the verifier is exact.** Bucket capacities (336 coarse, 12 fine) are finite, and occupancy is roughly Poisson. Coarse mean 256 vs cap 336 is ~5σ (σ ≈ 16), so overflow is rare but *possible*; when a bucket overflows, extra items are silently dropped (`if (item_idx >= CAP) continue;`). Therefore the solver may **miss** some valid solutions — it is a probabilistic search tuned to find *enough*, not *all*. The Rust documents this as intentional and matches the C's capacities precisely so the two miss the *same* solutions. The **verifier**, by contrast, does no bucketing and is exact: it recomputes the eight hashes and checks the sums directly. This asymmetry is fine for a client puzzle — a solver only needs one solution; a verifier must be sound.

### 4.4 Self-complementary buckets, dedup, and the solution cap

Two coarse buckets are their own complement: `0` (since `−0 = 0`) and `128` (since `−128 ≡ 128 mod 256`). Pairing a bucket with itself would double-count and produce duplicate pairs, so the solver special-cases `cpl_bucket == bucket_idx`: it interleaves matching into the scratch-building loop so each item only pairs with *earlier* items in the same bucket. The C carries a `nodup`/branch for this; the Rust's `collision::search` handles it by construction. The solver returns at most `EQUIX_MAX_SOLS = 8` solutions (the Rust `SolutionArray` is an `ArrayVec<Solution, 8>`), and dedups adjacent equal solutions before pushing.

### 4.5 Parent pointers and canonical reconstruction

Each combined node stores where its two parents live, packed into one integer with **8 bits of bucket + 9 + 9 bits of item index** — identical widths in both:

```c
#define MAKE_ITEM(bucket, left, right) ((left) << 17 | (right) << 8 | (bucket))
```

```rust
type Layer0Collision = PackedCollision<u32, 8, 9>;   // BUCKET_BITS=8, ITEM_BITS=9
```

At the end the solver walks this tree back to the leaves to recover the eight indices, then puts them in canonical order. The C does it with explicit conditional swaps at each level (`tree_cmp1/2/4` deciding whether to swap pairs/quads/halves); the Rust collects the leaves and calls `Solution::sort_from_array`, whose `branches_are_sorted` predicate compares groups reversed (i.e., as little-endian values). Same canonical form, so the emitted 16-byte solutions match.

---

## 5. Solver memory: two designs for the same 1.81 MiB

Both implementations keep the entire search in one preallocated block sized to live in cache, and both **reuse** the same bytes across stages via a union. The implementations of that idea are a study in contrasts.

**C — one struct, one union, hand-counted bytes.** `solver_heap.h` lays out every table explicitly and overlaps the early-stage data with the late-stage tables:

```c
typedef struct solver_heap {
    stage1_idx_hashtab  stage1_indices;     /* 172 544 B */
    stage2_idx_hashtab  stage2_indices;     /* 344 576 B */
    stage2_data_hashtab stage2_data;        /* 688 128 B */
    union {                                  /* reuse: early vs late stages   */
        stage1_data_hashtab stage1_data;     /* 688 128 B   (stages 0–1)       */
        struct { stage3_idx_hashtab stage3_indices;     /* 344 576 B          */
                 stage3_data_hashtab stage3_data; };    /* 344 064 B (stage 3)*/
    };
    fine_hashtab scratch_ht;                /*   3 200 B */
} solver_heap;                              /* TOTAL: 1 897 088 B */
```

Per-bucket counts live *inside* each table (`uint16_t counts[256]`), and the block is obtained with plain `malloc` — or `hashx_vm_alloc_huge` when `EQUIX_CTX_HUGEPAGES` is set, the one allocation knob the C exposes.

**Rust — `MaybeUninit` layout, checked union, counts outside.** The same overlap is a `union Overlay { first: OverlayFirst, second: OverlaySecond }`, but the whole structure is built from `BucketArrayMemory<N, M, T>([[ MaybeUninit<T>; M]; N])` and marked with an `unsafe` `Uninit` trait that promises the bytes are safe to leave uninitialized until written. Allocation goes straight to the heap (too large for the stack) and is reused across solves via `SolverMemory`:

```rust
// bucket_array/mem.rs — the safety-critical insert: count only ever rises after a real write
fn insert<F: FnMut(usize)>(&mut self, bucket: usize, mut writer: F) -> Result<(), ()> {
    let n: usize = self.counts[bucket].into();
    if n < CAP { writer(n); self.counts[bucket] = self.counts[bucket] + C::one(); Ok(()) }
    else { Err(()) }
}
```

The safety argument is explicit and worth appreciating: reads use `assume_init`, which is only sound if `counts` accurately reflects which slots were written; the code guarantees this by *only* incrementing a count after the writer has unconditionally written, and by tying everything to a `&mut` whose lifetime begins with zeroed counts. Switching layouts is done by borrowing a different union field, so the borrow checker enforces that the two overlays are never live at once. Because the bucket *counters* live outside the overlaid block, the Rust's measured size is **1,895,424 B** vs the C's **1,897,088 B** — a ~1,664-byte difference of bookkeeping placement, not of algorithm.

| | C `solver_heap` | Rust `SolverMemory` |
|---|---|---|
| Total | 1,897,088 B | 1,895,424 B |
| Counters | inside each table | in separate `BucketState` |
| Reuse mechanism | `union` | checked `union Overlay` |
| Uninit handling | raw `malloc` (bytes undefined) | `MaybeUninit` + `unsafe Uninit` |
| Big pages | `EQUIX_CTX_HUGEPAGES` | (none) |
| Reuse across solves | caller keeps `ctx->heap` | `solve_with_memory(&mut SolverMemory)` |
| Bucket geometry | 256×336 / 128×12 | **identical** |

The identical geometry is the point: same capacities ⇒ same overflow-discard behavior ⇒ identical solution sets.

---

## 6. API surface and error models

The libraries diverge most visibly at their edges, and the differences are idiomatic rather than algorithmic.

**Lifecycle.** C uses an opaque context allocated once and reused (`equix_alloc(flags)` → many `equix_solve`/`equix_verify`), with `flags` selecting verify/solve, compiled/interpreted, and hugepages. Rust uses values and builders (`EquiX::new(challenge)`, `EquiXBuilder` for `RuntimeOption`), plus free functions (`equix::solve`, `verify`, `verify_bytes`) for the common path. Solver scratch is a caller-held `ctx->heap` in C and a `SolverMemory` you can thread through `solve_with_memory` in Rust.

**Errors.** The taxonomies line up one-to-one, but Rust splits the *order* check into the type system:

| C `equix_result` | Rust | When |
|---|---|---|
| `EQUIX_OK` | `Ok(())` | valid |
| `EQUIX_ORDER` | `Error::Order` | indices not canonical (checked first, no hashing) |
| `EQUIX_CHALLENGE` | `Error::Hash(ProgramConstraints)` | HashX won't build for this seed |
| `EQUIX_PARTIAL_SUM` / `EQUIX_FINAL_SUM` | `Error::HashSum` | tree/full sum check failed |

In Rust you cannot hold a `Solution` without having passed the order check (it's enforced in `try_from_bytes`/`try_from_array`), so `EquiX::verify` only ever needs to check sums — the same cheapest-first ordering as the C `equix_verify`, but encoded in types. The Rust additionally surfaces `Error::Hash(Compiler(...))` when `RuntimeOption::CompileOnly` is chosen and the JIT is unavailable, a state the C reaches via the `HASHX_NOTSUPP` sentinel at `alloc` time.

---

## 7. Determinism and compatibility as an engineering discipline

Equi-X has no prose specification; correctness *is* reproducing the reference's output. Reading the two codebases together, you can enumerate exactly what a third implementation must match. This is the checklist:

- **Endianness:** hash output read little-endian (`load64`); PRNG bytes/words extracted big-endian from each SipHash block.
- **PRNG consumption order:** separate `u8`/`u32` buffers over a shared counter; the *interleaving* of draws is significant (§2.1).
- **The vestigial wide-multiply `u32` draw** (§2.4) — must be consumed even though unused, or the stream desynchronizes.
- **Arithmetic semantics:** 64-bit wrapping add/sub/mul; 32-bit immediates sign-extended; wide multiply keeps the high 64 bits; rotate-right by constant.
- **Acceptance gates:** 512 instructions, 192 multiplies, retire at cycle 194 (§2.5).
- **Digest:** fold `key1` into `r0,r1,r6,r7`, one SipRound per half, XOR-combine (§3.1).
- **Solver geometry:** 256/128 buckets, 336/12 capacities, the `b ↔ −b` complement, the `+CARRY` correction, the 8/9/9 parent packing, and the canonical ordering (§4) — so even *which* solutions are discarded matches.

The Rust enforces all of this with **captured reference vectors** at every layer (`rng_vectors`, `siphash24_ctr_vectors`, `hashx_vectors`, `tor_equix_vectors`), which is how it can be both idiomatic and bug-for-bug faithful. The few intentional internal differences are behaviorally invisible: the interpreter's `target + 1` vs re-running `Target` (§3.2), and where bucket counters are stored (§5). Everything an external observer can see — generated programs, hash outputs, the set of emitted solutions, verification verdicts — is identical.

---

## 8. Security-relevant code analysis

Reading the implementations surfaces several properties that bear on Equi-X's security posture. Stated precisely, with what the code does and does not defend:

- **No secret inputs.** HashX's control flow is input-dependent (the one-shot branch tests live data), so evaluation time can leak the input. The code is explicit that this is acceptable *only because the puzzle input is public*. Using HashX as a keyed hash over secret data would be a timing-side-channel mistake. (Volume I's "intuition" caveat, here as a hard rule.)
- **Weak instances are neutralized by addition, not avoided.** ~0.2% of seeds produce HashX functions with many internal collisions. Under XOR these would yield enormous numbers of trivial solutions; Equi-X's switch to **sum mod 2⁶⁰** means equal hashes no longer cancel, so weak instances don't become exploitable. The solver and verifier therefore never need a collision-resistance assumption on HashX — only preimage resistance.
- **Solver non-exhaustiveness is sound.** Bucket overflow silently discards candidates (§4.3), so the solver can miss solutions — but it can never *invent* one, because every emitted solution is rebuilt from real items and (in practice) re-checked by the exact verifier. Missing solutions only costs the solver attempts, never soundness.
- **JIT hardening.** The compiled path uses W^X page permissions (`vm_rw` to emit, then `vm_rx` to execute) so the code page is never simultaneously writable and executable. Emission is straight-line from a trusted program with no input-derived lengths, limiting the JIT's attack surface.
- **The memory-hardness/branch interplay is by design and acknowledged as imperfect.** HashX itself is register-only (no scratchpad), which is what makes its program shape so CPU-like; the Equihash layer adds the ~1.81 MiB cache-resident working set that blunts a GPU's bandwidth edge and gives a logic-only FPGA something it must store. The generator even computes a hypothetical **"ASIC latency"** (`asic_latencies`, assuming unlimited parallelism and 1-cycle ops) in its stats build — a window into the designer's own modeling of the parallel lower bound. None of this targets true ASIC-resistance, which Equi-X explicitly abandons.
- **Memory-safety boundary.** The C solver is classic manual indexing into a `malloc`'d block; correctness rests on the capacity checks (`if (idx >= CAP) continue;`). The Rust achieves the same layout but routes every read through `assume_init` guarded by a borrow-checked count, converting "don't read uninitialized memory" from a discipline into a compile-time-checked invariant. Same bytes, very different safety story.

---

## 9. Performance model

A coherent mental model of where the cost goes, assembled from the code structure (absolute figures are the designer's, on era-specific hardware, and approximate):

- **Solve ≈ 5–8 ms.** Decomposes as: one program generation (~0.05 ms, O(512) with bounded per-slot search), then `2¹⁶` HashX evaluations in stage 0 (the dominant term), then three `Θ(2¹⁶)` bucket passes (cheap relative to hashing). HashX overhead vs the search is well under 1%.
- **Verify ≈ 50 µs.** Eight HashX evaluations + a few additions + six integer comparisons, with the free ordering check rejecting malformed proofs before any hash runs.
- **The asymmetry, quantified.** A solver performs ~`2¹⁶` hash evaluations to a verifier's 8 — a factor of ~`2¹³ ≈ 8000` in hashing alone — and the wall-clock ratio is ~100×. The 16-byte proof keeps the *verifier's* input cost negligible, which is the property that makes Equi-X usable as a DoS gate rather than a self-inflicted one.
- **JIT vs interpret.** Compiled HashX is roughly an order of magnitude faster than interpreted and is the deployed path; both are required to agree bit-for-bit, so the interpreter doubles as the executable specification and the portable fallback.
- **C vs Rust.** The Rust crate's own tests note it is modestly slower than the C reference (its comments reference small solver/verifier deltas), the expected cost of generic, bounds-checked, memory-safe code; the algorithmic complexity and outputs are identical.

---

## 10. Synthesis

The C and Rust implementations are a near-perfect natural experiment: the same nontrivial algorithm written once for *speed and definition* and once for *safety and clarity*, constrained to produce identical output down to which solutions they discard. Reading them in parallel is the most efficient way to understand Equi-X, because each compensates for the other's weakness as a teaching text — the C answers "what exactly happens," the Rust answers "why, and what's safe."

The deeper lesson the code carries is that Equi-X's security rests less on any single clever primitive than on **disciplined uniformity**: a program generator that manufactures equal-cost, CPU-shaped functions; a combiner (addition) chosen so a weak hash can't be exploited; a solver engineered to stay in cache; and a verifier kept structurally cheap and exact. The implementations make those choices legible in a way the (nonexistent) prose spec never could.

---

## Appendix A — Constant and parameter correspondence

| Quantity | Value | C symbol | Rust symbol |
|---|---|---|---|
| Program size | 512 | `REQUIREMENT_SIZE` / `HASHX_PROGRAM_MAX_SIZE` | `NUM_INSTRUCTIONS` |
| Required multiplies | 192 | `REQUIREMENT_MUL_COUNT` | `REQUIRED_MULTIPLIES` |
| Scheduler target | 192 cycles | `TARGET_CYCLE` | `TARGET_CYCLES` |
| Required final retire | cycle 194 | `REQUIREMENT_LATENCY - 1` | `REQUIRED_OVERALL_RESULT_AT_CYCLE` |
| Ports | 3 (P5,P0,P1) | `NUM_PORTS` | `NUM_EXECUTION_PORTS` |
| Latencies | 1 / 3 / 4 | per `instr_template.latency` | `instruction_latency_cycles` |
| Branch mask weight | 4 (≈1/16) | `LOG2_BRANCH_PROB` | `BRANCH_MASK_BIT_WEIGHT` |
| Registers | 8; R5 special | `REGISTER_NEEDS_DISPLACEMENT = 5` | `register::R5` |
| Gen reject rate | ~1 / 10⁴ seeds | comment in `program.c` | doc in `program.rs` |
| Weak-seed rate | ~0.2% | (HashX README) | (HashX README) |
| Equihash N, K | 60, 3 | `EQUIX_*_MASK` widths | `EQUIHASH_N`, `EQUIHASH_K` |
| Items / solution | 8 → 16 B | `EQUIX_NUM_IDX` | `Solution::NUM_ITEMS` |
| Index space | 2¹⁶ | `INDEX_SPACE` | `u16::MIN..=u16::MAX` |
| Coarse / fine buckets | 256 / 128 | `NUM_COARSE/FINE_BUCKETS` | bucket array `N` params |
| Bucket capacities | 336 / 12 | `COARSE/FINE_BUCKET_ITEMS` | `CAP` params |
| Parent pack | 8 / 9 / 9 bits | `MAKE_ITEM` shifts | `PackedCollision<u32,8,9>` |
| Stage masks | 2¹⁵, 2³⁰, 2⁶⁰ −1 | `EQUIX_STAGE1/STAGE2/FULL_MASK` | `n_bits` recursion |
| Solver memory | ~1.81 MiB | 1,897,088 B (`solver_heap`) | 1,895,424 B (`SolverMemory::SIZE`) |
| Max solutions | 8 | `EQUIX_MAX_SOLS` | `SolutionArray` capacity |

## Appendix B — Instruction template fields (C `instr_template`)

Each C template carries the fields the generator and JIT consume; the Rust spreads the same data across `scheduler::model` (ports/latency), `generator::model` (selection), and `program::Instruction` (semantics).

| Opcode | latency | uop1 / uop2 | distinct dst? | has src? | immediate |
|---|---|---|---|---|---|
| `UMULH_R` / `SMULH_R` | 4 | P1 / P5 | no | yes | — (draws an unused `op_par` u32) |
| `MUL_R` | 3 | P1 / — | yes | yes | — |
| `SUB_R` | 1 | P015 / — | yes | yes | — |
| `XOR_R` | 1 | P015 / — | yes | yes | — |
| `ADD_RS` | 1 | P01 / — | yes | yes | 2-bit shift; dst ≠ R5 |
| `ROR_C` | 1 | P05 / — | yes | no | 6-bit rotate (nonzero) |
| `ADD_C` / `XOR_C` | 1 | P015 / — | yes | no | 32-bit (nonzero) |
| `TARGET` / `BRANCH` | 1 | P015 / P015 | — | no | branch: 4-bit-weight mask |

## Appendix C — Provenance

- **C:** `tevador/equix`, `tevador/hashx`, v1.0.0 (2020), LGPL-3.0. The normative reference; no separate written spec.
- **Rust:** `equix` 0.6.1, `hashx` 0.7.1 (crates.io), Tor Project / Arti, LGPL-3.0. Reproduces the C output exactly; ships shared Tor test vectors. Later versions (`equix` 0.7.0 / `hashx` 0.9.0, June 30, 2026) carry no algorithmic changes.
- Snippets trimmed for readability (`...`); identifiers, constants, and arithmetic verbatim from the cited files (re-verified July 2026). Read alongside Volume I (the Walkthrough) for the conceptual model this analysis assumes.


