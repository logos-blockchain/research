# Outstanding items owed upstream — prepared, awaiting a go

Things this workstream has an answer for that belong in somebody else's document.
Each entry is written so it can be posted without redoing the work: the question, the answer,
the evidence, and where the code is. **Nothing here has been sent.** Posting to a public PR is
outward-facing and needs the design owner's explicit go.

*Last verified 2026-08-25 against logos-lips PR 375 at head `2b3b698`.*

---

## 1. PR 375's open boundary question — `P_t ≥ 0` in the early-life regime

### What they asked

PR 375's own "Risks and open questions" leaves one item for reviewers:

> the pool balance constraint `P_t ≥ 0` is stated but the early-life regime where `R̄_t`
> exceeds cumulative inflows deserves an explicit boundary treatment during review.

### The short answer

**The regime is real rather than hypothetical, it is not confined to early life, and one line
fixes it: clip the distribution to what the pool actually holds.**

### Why it happens

The recycled term distributes `(1 − A_t) · R̄_t`, where `R̄_t` is the average pooled fee over
the look-back window `T`. The average is over the *window*, but the pool only ever received
the *actual* fees. So after any burst of fees followed by quiet, the window still remembers the
burst and keeps paying against it while nothing is coming in. The pool pays out history it
never banked.

Nothing about this is specific to genesis. It needs only a fee spike, then quiet, with `A_t`
low enough that the recycled term is carrying the reward — which is exactly the mature,
at-target regime the design aims for. Early life is where it is *most likely*, not where it is
*confined*.

### Measured

One 120-LGO block, then 240 quiet ones, at `A_t = 0`, reserve empty:

| | worst pool balance | final | conserves? |
| --- | --- | --- | --- |
| unguarded (the spec as written) | **−119.00 LGO** | −119.00 | yes |
| guarded (the proposal below) | **0.00 LGO** | 0.00 | yes |

The guard binds for **119 blocks** — one block short of the window — and then releases on its
own as the spike rolls out of the look-back. It is self-clearing; no operator action, no state.

### The proposed treatment

| `distribution_t = min( (1 − A_t) · R̄_t ,  P_{t−1} + R_block,t )` |
| --- |

Pay what the pool holds, never more. Three properties, all measured:

- **`P_t ≥ 0` holds by construction**, which is what the specification already asserts and
  currently has no mechanism to deliver.
- **Conservation is untouched.** `ΔS + ΔP + ΔB = 0` still closes exactly, because the clip
  moves a payment rather than destroying one.
- **Nothing is lost, only deferred.** The tokens stay in the pool and are distributed once the
  window reflects reality again.

### The point worth making in the review

**Conservation and `P_t ≥ 0` are independent claims, and the RFC's conservation argument does
not imply the constraint.** The unguarded run above conserves perfectly while sitting at
−119 LGO — a state the specification forbids. Anyone checking the conservation algebra and
concluding the pool is safe has checked the wrong thing. That is worth saying explicitly,
because the conservation argument is the part of PR 375 reviewers were asked to scrutinise.

### Provenance

`empowering_sim.emission.Stocks` implements both readings behind `guard_pool`. The gates are
in `empowering_sim.validate`, `gate_emission`:

- `unguarded, the early-life pool balance goes NEGATIVE after a spike`
- `guarded, the distribution clips to the pool and the balance floors at zero`

Reproduce with `cd tools/simulators/empowering && PYTHONPATH=src python3 -m empowering_sim.validate`.

*(Note for whoever posts this: it is the same move the de-novo engine's room cap already makes
— admit while the pool can pay, stop when it cannot. Worth mentioning only if the reviewer
wants precedent; it is not an argument on its own.)*

---

## 2. The `POW_SHARE` carve-out, acknowledged as a pool outflow

### What is needed

One sentence in PR 375. `storage-markets.md`'s Fee Routing subsection and
`execution-market.md`'s closing derivation both say fees route into the pending rewards pool
**"in full"**, and the decomposition `R_block = R̂_STR + R̂_pooled` has no proof-of-work term.
EmPoWering diverts `POW_SHARE` (10%). As written, the two specifications contradict each other
the day both merge.

### What was decided here

**2026-08-24, design owner: the pool's routing stands and EmPoWering carves its share out of
the pooled flow** — the pool's *first outflow*, not an interception ahead of it. So "in full"
stays literally true and nothing in PR 375's arithmetic changes; what it needs is an
acknowledgement that the pool has an outflow the decomposition does not currently name.

Recorded with its accounting consequences as contradiction 4.13
(`tools/simulators/empowering/docs/CONTRADICTIONS.md`). Implemented in
`emission.pooled_inflow_lgo`, gated, and costed: identical at `A_t = 1` where every published
figure sits, 0.0005% near target, and exactly `1/(1 − pow_share)` only in the genesis-seed
transient.

---

## 3. The leader-incentive concern, if wanted

A reviewer on PR 375 (`block-rewards.md:262`) raised that pool retention when `A_t → 1` leaves
leaders uninterested in tips during the adoption phase. **Not answered — we have the machinery
to quantify it in the strategy simulator, and have not been asked to.** Listed so the question
is not mistaken for one nobody noticed.
