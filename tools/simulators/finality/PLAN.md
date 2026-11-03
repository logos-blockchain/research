# Fast finalization for Cryptarchia — the plan

An exploratory study of how far, and by which means, the time until a Cryptarchia block can be
relied on can be shortened. It sizes every route by number before any design is chosen. It
changes no specification.

Branch `fast-finalization-slots`, from `fast-finalization` at `bd90263`, reads the study again
with `k` counted in slots (Phase K), and sizes certificates signed by Blend's declared nodes
(Phase L). Branch `fast-finalization`, based on `origin/master` at
`272fd9a`, counts it in blocks. The TSI per-node engine
(`../tsi/tsi-sim-pernode`) is consumed as a library for fork structure, delay and attacks.
Specifications are read at `logos-lips` `47a73cdc`. The node is read at `logos-blockchain`
`4e0405d51`, and testnet 0.3.0 at `865df42ba`.

## How to read this

*In plain words: this is the notebook the study starts from — the brief, what a first
calculation already says, the levers worth pulling, the questions only the owner can settle,
and the order of work. The finished story is `../../../reports/finality/`.*

| section | what it carries |
| --- | --- |
| §0 | the brief, and the constraints carried from the Cryptarchia specification |
| §1 | a first look: where the time goes, what `k` buys, what each lever is worth (numbers from `firstlook.py`) |
| §2 | the levers, each with a hypothesis that can fail |
| §3 | the owner's decisions on the questions that shape the study |
| §4 | the work plan, phases A–L |
| §5 | the measurement protocol |
| §6 | what depends on `k` today, in the specifications and in the node |
| §7 | literature to reproduce before it is relied on |

## Status

Executed from 2026-10-05 to 2026-10-20, Phase K on 2026-10-21, K.7 and K.8 on 2026-10-23, and
Phase L on 2026-11-03. Results live in nine notes beside this plan:

- `MAPPING.md`: A2, A3.
- `RATE.md`: A1, C1–C4.
- `SETTLEMENT.md`: B1–B7.
- `CERTIFIED.md`: D0–D6.
- `DAG.md`: E0–E6, J.0–J.3.
- `FURTHER.md`: G1–G7.
- `DESIGNS.md`: H.1–H.3.
- `SLOTS.md`: K.0–K.5, K.7–K.9, on the branch `fast-finalization-slots`.
- `NETWORK.md`: L.0–L.6, on the same branch.

Phase by phase:

| phase | status |
| --- | --- |
| A1 baseline | done; reproduces the TSI report's and the specification's measured orphan shares; the engine starts a cascade at the slot where the specification releases a round later, −0.02 growth and +5–10 % depth; eight runs give 0.845, 32 give 0.832–0.834, and equal stakes 0.819, so the report's convention reads a chain on which every node produces low; the private attack it stands for needs less, 160 / 261 blocks against 30 % / a third with the specification's two copies released a round later, within the convention's 165 / 276 (`RATE.md` A1) |
| A2, A3 map and self-healing horizon | done |
| B1 bounds | done; the port reproduces all 152 proof-of-stake cells of the paper's Table 1 |
| B2 depth over share and delay | done, worst case |
| B3 engine validation | done: the private-chain attack under random delays, and the delay-scheduling attacker of the lower bound on the slot lottery |
| B4 confirmation rule | done: the depth table, and a rule that reads elapsed time |
| B5 smaller `k` | done: the share each `k` holds, both routes of Q8, a trigger for automatic recovery, and its horizon against stake turnover |
| B6 grinding | done: the nonces a coalition can choose between, bounded from both sides given its lead after the cut-off, for an attack that meets one ground nonce and for one that meets two; what they add to the depths and take from the recovery horizon |
| B7 nonce | done: a delay function's cap on the nonces evaluated, and a nonce from the smallest contributions of sub-windows, whose factor per nonce is an estimated 5.9–7.3 against a third on the specification's Blend and 10.6–18.1 under the worst case at 10 s, counting its own blocks withheld and honest minima removed; not bounded |
| C1 rate surface | done |
| C2 Blend parameters | the delay map is done; the privacy trade is with the Blend owners |
| C3 GHOST | done |
| C4 Taktikos | done: no fewer orphans; a regular interval settles faster on the specification's Blend at more blocks |
| D0 emission map, D2 committee realism | done |
| D1b opt-in committee | done: the share of the stake that must declare, and how many of the largest holders that takes |
| D5 privacy | done: votes sample stake at D0's multiple; times to identify and size a holder through Blend and by direct gossip |
| D1, D3, D4 | sketched, open questions listed; D3 prices verification with the Raspberry Pi 5 measurement of Blend; `tools/benchmarks/pol-proving` times proving, not yet run on the Pi 5 |
| D6 simulation | done: votes on a target 30 slots back never split under random delay; a round certifies within one Blend delivery; an adversary that schedules delays splits shallow rounds |
| E0 audit of the Areon simulator | done |
| E1–E6 Areon-Base on the engine | done: built on the TSI engine (the owner's choice); the private race, the §5.6 fit, worst-case delay, eligibility, ledger and cost |
| F report | `reports/finality/README.md`, a draft |
| G1 delayed nonce | done, corrected by H.2 and the review of 2026-10-15: the delay must span the last sub-window; a choice is still open ten minutes past the cut-off in 30 % of windows against a third under the worst case, counting the coalition's lead at the cut-off; B7's contributions, known ahead, leave a factor of 1.005–1.054 at a margin of 10 minutes, the depth within seven blocks of the unground one; bound to the parent's contribution, 1.002–1.04 (H.2) |
| G2 epoch decoupled from `k` | done, from B6 and B7's `k = 2160` rows |
| G3 Blend's delay | done: both delay models over the twelve Blend settings of A1, with `E[G_min]` read per setting and model |
| G4 settlement on a chain nobody withholds from | done: B4's elapsed-time rule already settles it in 39 / 53 minutes against 30 % / a third, but its rates hold only while the inferred stake is the true stake; with the rates after a total-stake adjustment and the depth rule as a cap, 66 / 106 minutes, and the depth rule's depth on a chain withheld from; a rule that reads density directly is dominated |
| G5 anchoring | analysis only, read with H.1: an anchor timestamps a block and does not show it was public, so it settles forks that did not exist when it was written, never a partition |
| G6 adversarial relays | done: the engine's `blend_adversary_relays`, `blend_adversary_action` and `blend_copies`, and a hold to the sender's deadline; holding costs 3–8 % of depth, to the deadline 14–23 % against a third; dropping costs 47 % (352 against 240) with two copies, 62 % with one; the report's convention covers holding only against a third with one copy released at the slot |
| G7 the inference as a lever | done: a period of withholding raises every threshold by `1/(1 − α)`, and B2's depth at 10 s becomes its depth at `10/(1 − α)` s, 2,426 blocks against a third and 1,248 against 30 %, so no `k` the study considered holds its share after it; under random delay the convention's depth is unchanged and comes sooner, but the chain withheld from then grows as one on which every node produces, and the engine's race needs 189 / 334 blocks against 30 % / a third where it needed 158 / 257, past the convention's 165 / 276, and 240 / 473 with relays that hold to the sender's deadline; a cap on the correction of 5 % a period prices the deflation at 36 days |
| H.1 recovery in a partition | done (`DESIGNS.md`): the impossibility at a third; recovery attestations, a one-off vote round, with the seats per share; anchoring placed; rule 8 as a detector; the seats need relays that deliver, since relays at the adversary's share that drop leave no round at 25–30 %; the detector reads a side only while the side runs at the thresholds set before the split, at least 3 days at `k = 2160` |
| H.2 the delay function | done: the rule in Praos's model; a candidate of the last sub-window exists from the sub-window's start, so the delay must span it, with the minima taken over a contribution every node derives from the parent's contribution and the block's win tag, `c(b) = hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖ ρ_LEAD(b))`, which leaves `ρ_LEAD` the parent-independent win tag, forms a branch's values when the block it forks from arrives and admits no body variants; four bindings compared by the values seen while reachable; the blind switch and the evaluator term bounded; the honest cost against the speed ratio and `k`; the design; `E[G_min]` bounded from B6's walk, with the crossing forks the previous sub-window completes; the literature pinned |
| I.1 the papers pinned and the reduction placed | done: Praos (revision 2023-04-27) and Genesis (2019-02-22) read from the archive's snapshots; the union bound over `r` candidates and its `log r` in Theorem 11, Corollary 3's `log tkq`, Genesis's `Q` in `ε_lift` and its grinding remark quoted; the lemma placed: the rule bounds the same `r` by the evaluated candidates; Theorem 1 covers the Online rule, Theorem 2 the Bootstrap rule |
| I.2 class-group sequentiality | done: the time-lock and adaptive-root assumptions pinned; Biasse, Jacobson and Silvester's Table 4 is the discrete logarithm's cost by Vollmer's algorithm, `2^91.4` at 1024 bits by its rows, which come out of their method only with the anchor at 4.8 MIPS, and `2^101.4` at the stated 4,800 MIPS, with the class group 1.33–1.61 times that; within the delay that takes two hundred thousand to three hundred million machines of `10^18` operations a second; 2048 bits give `2^139.4`–`2^149.4` at no cost in time if the speed ratio holds there |
| I.3 a partition mode in the engine | done: `tsi_sim` splits the honest nodes for a span, loses Blend copies across the cut and reads far arrivals at the span's end; per occupied slot a side grows as the network does (0.863 / 0.845 / 0.829 for sides of 30 / 35 / 40 %), and at that growth the closed form lies within 0.5 standard errors of the engine; at A1's growth it misses by up to 19 points; the coalition's nodes sit on either side of the cut, as it chooses: a 30 % fork beats a 35 % side in 65 % of windows with its nodes beyond the cut and 42 % beside the side, a third's beats a 40 % side in 55 % and 17 %, and a third's beats a third always; two copies give 0.637 / 0.504; H.1's detector sees every side; even sides tie in 1.0–1.6 % |
| H.3 time under the worst case | done: B4's rule beaten in 51–58 % of its acceptances; the counting bound, empty on a slow chain; the observed counting rule, counting the distinct slots of the forks received, 408 blocks against a third under worst-case delay and 374 when only withheld from; it holds `ε` per target by computation with the worst-case walk's law, not given the view, and not under its own geometric law; a balancing coalition with its own blocks counted stalls it; a time-conditioned B2 bound not derived |
| K finality counted in slots | done, on the branch `fast-finalization-slots` (`SLOTS.md`). K.0: Praos, Genesis and the specification count `k` in blocks, and Crypsinous reads it as slots only where it evolves its encryption keys; the rules for a window of `K` slots, with a density floor in a depth form and a density form. K.1: a wait under random delay, B4's chance averaged over the wait, 5.10 hours against a third at `1e-9`, 1.25 times the depth rule's time; under the worst case B2's bound at the depth the wait guarantees, 26.3 hours at 10 s, 1.15 times B2 on its clock. K.2: `⌊k/f⌋` slots hold 0.310 at 10 s where 2,160 blocks hold a third; `3⌊k/f⌋` holds a third with the nonce of §3.1 (26.6 hours) and after a deflated inference (29.8), not with today's nonce (67–109 hours); a deflation costs 13 % in slots against 61 % in blocks. K.3: without a floor an eclipse or a split fixes a fork after `K` slots whatever its stake; a floor of 3,264 blocks at `3⌊k/f⌋` restores more than `k = 2160` gave; as a quorum it separates a quarter only at windows of days to weeks and a third at none. K.4: a race lasts at most `K`, so every target stays inside B6's bound while `K ≤ 4⌊k/f⌋`. K.5: under the worst case a faster block rate needs a longer `K`; relays that drop cost 56 % as a wait. K.7: a bound for a wait in GRR's own model, their chain frozen at the phase in which the wait passes and run on the slot lottery at `Δ + 1` slots, gives 10.1 hours against a third at 10 s where K.1 read 26.3, so `⌊k/f⌋` holds a third at 10 s without grinding, with the nonce of §3.1 (10.2 hours) and after a deflation (12.5), not with today's nonce (25.9–42.0); `3⌊k/f⌋` holds it in every case at 10 s; B2's code freezes at half the count the paper's argument needs. K.8: a cap on the inference's correction an epoch lengthens the density floor's protection and its stall after a genuine fall alike, 0.73–1.38 of each other at every cap, and buys the depth form almost nothing; the specification's inference rounds its target to 0.033 occupied slots a slot, the residual the TSI report records. K.9: counted as the inference counts, on occupied slots with referenced uncles, the floor under random delay rises by a fifth, 1,225 at 18 hours against a third, the stake below which finality stalls falls from 0.665 to 0.562, and a floor separates partitions against a quarter from 2.24 days; under the worst case the count is at least the canonical one, so the floor of 1,019 holds |
| J a fork choice that tolerates delay | J.0–J.3 done (`DAG.md`), and the phase stops at J.2 on its stop condition. J.0: the readings without the owner's answer are E1's, with `k` in slots. J.1: one weight per win under the win tag `ρ_LEAD`; a nonce contribution every node derives from the parent's contribution, at no cost to the proof (3.5–5.9 % if proved); ties broken by each side's first block. J.2: with one move per win the strongest attack within `Δ` against a third needs 2.8 hours at 1 s and 5.0 at 10 s, against the chain's 3.5 and 6.8; but a tag found on both sides weighs on neither, so a coalition retracts a placed win with a second copy on the other side and one win moves the balance twice, and no rule every node applies alike blocks it; the balancing edges then fall below a third at every delay, 0.318 / 0.326 at 1 s and 0.235 / 0.279 at 10 s with ties steered / fixed, so no attack depth exists against a third and no variant beats the chain. J.3, computed anyway: neither Kiffer, Rajaraman and shelat nor Gaži, Motaqy and Russell gives an error against depth; the opportunity bound is finite only up to 0.223 at 10 s and needs 14.2 hours against 25 % at 1 s, where the chain's bound needs 3.3. J.4–J.6 not run, moot against a third. J.7 is this verdict: a fork choice that weighs every honest block gives no smaller `k` |
| L certificates from the network | done, on the branch `fast-finalization-slots` (`NETWORK.md`). L.0: SDP's declarations, Mantle's service notes, the minimum-stake analysis and Casper FFG pinned; the gadget on Cryptarchia's clock, and three compositions with the slot rule: certificates only, a fast path, both required. L.1: safety needs the coalition below a third of the declared weight, liveness `u(1 − a) ≥ 2/3`; under the study's convention the set holds every coalition below a third at full uptime; under SDP's economics the honest declared stake must exceed `2α/(3u − 2)` of the active stake whatever the minimum stake, so at today's minimum 500 declarations, 1.67 % of the active stake, hold a third of a network of 1,000, 30 % needs 60 % declared and online without a gap, and a third none. L.2: with rounds of 60 slots a block is final in 120 s on average and 147 s at the 95th percentile on the specification's Blend at a lag of 30; the lag must outlast Blend's delays, 60 slots at the heavy point (177 s), else justified checkpoints leave the longest chain. L.3: below a third of the declared weight one side at most certifies, in the closed form and in every engine run; at 0.34 an even split finalizes both; an eclipsed node finalizes nothing while the coalition holds less than two thirds. L.4: the lag sets which assumption carries safety; with FFG's fork choice two thirds of the declared weight, 6.67 % of the active stake today, finalize at any lag; a variant that votes only on its own chain is safe at the chain's settlement at the lag, 12.5 hours against a third, while every honest block reaches every honest node; an eclipse or a split still rests on the declared set unless a floor covers the lag; its liveness not derived. L.5: 6.0 % of one Pi 5 core at 20,000 declarations with ed25519-dalek; ML-DSA-44 certificates 36 times larger. L.6: pruning must keep the uncle window, slashing needs a Mantle operation, a released note frees its key one epoch after its node stops signing. Not recommended at today's minimum stake |

Before review, in this order:

1. **The DAG's worst case.** Done (E5): the balancing attack.
2. **Grinding the epoch nonce.** Done (B6).
3. **The opt-in committee and the privacy of votes.** Done (D1b, D5).
4. **A confirmation rule that reads elapsed time.** Done (B4).
5. **Proving a vote on a Raspberry Pi 5** (D3). Prepared: `tools/benchmarks/pol-proving` times
   the node's proof of leadership; the run on the board is the owner's.
6. **A nonce that resists grinding.** Done (B7).

Three independent reviews of the notes, the report and the code are applied. The second added the
premined lead to the random-delay closed form, the displacement of honest minima to B7's estimate,
and the partition case to B5's trigger. The third, of 2026-10-15, bound the contribution to the
parent's contribution rather than the parent block, counted the values the coalition sees while it
can still choose them, put the lead at the cut-off into G1's law, stated H.3's rule per target and
counted its forks by slot, read I.3's growth per occupied slot, held G6's relays to the sender's
deadline, and found that G7's random-delay depth rests on the convention, not on a faster chain.
The owner's review follows.

Findings about the protocol as it stands:

- A restart, even with `--bootstrap`, does not return a node from the losing side of a split deeper
  than `k`; only a re-sync from genesis or a checkpoint does (`SETTLEMENT.md` B5).
- At testnet's `k = 120` the Bootstrap rule's density window is 15 minutes, and a quarter of the
  stake wins about one such window in 460 (B5).
- `maxvalid-bg` reads the depth of the local branch, so after a split the two sides can choose
  different chains until both pass `k` (B5).
- The epoch nonce can be ground. Against a third of the stake at `1e-9`, a block whose race meets
  two ground nonces needs 1,171–1,245 blocks instead of 276 under random delay on the
  specification's Blend, and 5,732–6,287 instead of 1,510 under the worst case at 10 s. Against
  30 % under that worst case it needs 2,424–2,825, more than `k`, from `2^40` nonces evaluated an
  epoch (B6).
- The total-stake inference can be deflated. A coalition that withholds for one period raises every
  lottery threshold by `1/(1 − α)` for the next epoch: B2's depth at 10 s against a third becomes
  2,426 blocks, and the private attack under random delay needs 334 on the engine where it needed
  257 (G7).
- LCanalysis follows its lower-bound attack for 80 phases, too few past Table 1's depths: at a
  third of the stake, `Δ = 1` s and depth 60, the port at 30 states falls from `6.9e-3` to
  `5.5e-12`, and the original code run in Octave at its 19 states to `5.4e-13`. It also scores the
  attack only at the moment of confirmation (B1, B3).
- LCanalysis freezes its upper bound at half the count the paper's argument needs. The paper puts
  the earliest settlement error at `ρ + h + 2a ≥ 2k`, two chains of `k` blocks above the target;
  the code freezes at `ρ + h + 2a ≥ k`, and its Table 1 uses that count. At the paper's count B2's
  depths halve: 755 blocks against a third at 10 s and `1e-9` instead of 1,510 (`SLOTS.md` K.7).
- The total-stake inference rounds its target, as the TSI report records (`reports/tsi/README.md`
  §2.2, Appendix A). `total_stake_inference` computes `f_p = truncate(f·PRECISION)` with
  `PRECISION = 1e3`, so for `f = 1/30` it holds the occupied slots at 0.033 a slot: at rest the
  estimate is 1 % above the stake and an occupied slot comes every 30.3 slots (`SLOTS.md` K.8).

Hypotheses:

| hypothesis | verdict |
| --- | --- |
| H1 | fails for the guarantee: at 25 % and `ε = 1e-9` the upper bound exceeds 216 blocks at every delay, from 288 at 1 s; with two nonces ground by a coalition that evaluates `2^64` nonces an epoch, 477–950 blocks at 1–10 s. Holds for the best known attack, without grinding, at least to 20 s |
| H2 | holds for delays up to 13 s without grinding; at 10 s with a nonce from the smallest contributions of sub-windows at B7's estimates (1,859–1,939 blocks), and with that nonce under H.2's delay, 1,511 blocks sampled and 1,523 as a bound within B6's model with one delay evaluator; each only while the inference is not deflated, after which B2's depth at 10 s is 2,426 blocks (G7). With today's nonce B6's bounds prove it with one ground nonce up to 5 s against a coalition that evaluates `2^40` nonces an epoch and up to 2 s against `2^64`, and with two only at 1 s against `2^40`. At the specification's Blend (`Δ = 10` s) these bounds cannot prove it once grinding is counted |
| H3 | holds |
| H4 | refuted for a delay chosen by an adversary: GHOST's safe region never exceeds the longest-chain rule's, and in proof of stake it needs equivocation control, which Cryptarchia's private lottery cannot give: the win tag counts a win once on a side, but a second copy on the other side retracts the first, so one win moves the balance twice and a third holds two sides level for ever at every delay (`DAG.md` J.1, J.2). Untested on the chain under random delay |
| H5 | fails against Blend's present budget: with the cover raised by D0's multiple, every committee exceeds the read limit `r_1` of a core connection, against a quarter of the stake unless rounds last 33 hours (D3). Whether that budget may grow is the owner's line (Q7) |
| H6 | holds for eclipses with the trigger of `SETTLEMENT.md` B5 (rules 1–8): a density test below `B_imm` within a horizon `H`, with a window set apart from `k`, a tie-break, and no comparison from a chain that was sparse over the window. Fails for a partition deeper than `k`: each honest side then holds its own share, and against an honest side of 35 % of all stake a 30 % adversary's withheld fork is denser in 64–70 % of the specification's windows, a third's against an honest third always (rule 8). Fails as first stated, a switch to the Bootstrap rule. At Bitcoin's turnover, against 25 % with every freed key for sale, `H` is 48 to 92 days with an 8-hour window at `k = 2160` once grinding is counted (B6), and 38 to 71 days with a 4-hour window without it. At `k = 120`, whose window is at most 4 hours, no horizon holds a quarter with grinding |
| H8 | fails as stated: 15,000 seats separate 30 % with every honest vote counted, 158,000 with a tenth lost (`DESIGNS.md` H.1), above the 10,000 the hypothesis named; 2,300 separate a quarter; at a third none. The impossibility at a third holds. Vote splitting lets the adversary choose which honest history survives, not its own; relays at the adversary's share that drop what they carry leave no round at a quarter or 30 % unless lost votes fall back to direct broadcast |
| H9 | fails as stated: 100 honest minutes blind nothing, since a candidate nonce of the last sub-window can be evaluated from the sub-window's start, 4.3 hours before the cut-off at `k = 2160`. Holds for a delay that spans the sub-window with the contribution bound to the parent's contribution: a margin of ten minutes leaves a factor of 1.009 against a third at `k = 2160`, sampled, and at most the walk's 1.08 plus 0.016 for a blind switch plus `1.6·10^-6` per delay evaluator, against a ratio of 15 to 16, the most the phase's squarings hold (`DESIGNS.md` H.2); Chia's class-group ASIC is 3 to 5 times a CPU and the CIP's 10 is an assumption, so honest nodes compute 13–22 hours at `k = 2160` at the documented ratio and 45 at 10; the proof is one group element and verification takes 2–4 ms, not under one |
| H11 | holds: both papers bound the nonce's bias by a union bound over the `r` candidates the adversary can set it to (Praos §4.9, Theorem 11's `log r`) and then bound `r` by the oracle queries (Corollary 3, Genesis's `Q`); Genesis's Theorem 2 adds to Theorem 1 only a term in `k` and `s` for `maxvalid-bg`; the nonce enters both through the leader schedule, and the stake of epoch `ep − 2` is fixed before any candidate exists, so the lemma's count of the candidates seen while reachable stands where `Q` does (`DESIGNS.md` H.2) |
| H12 | holds as stated at the paper's own conversion: by Biasse, Jacobson and Silvester's Section 5 at 4,800 MIPS, the discrete logarithm of a 1024-bit discriminant costs `2^101.4` operations and the class group 1.33–1.61 times that, beyond `2^100`; their Table 4's rows, which come out of that method only at 4.8 MIPS, put it at `2^91.4`, below. Either way it holds for the delay's threat, a class group within hours of a discriminant first formed at the sub-window's start, which needs two hundred thousand to three hundred million machines of `10^18` operations a second; 2048 bits give `2^139.4`–`2^149.4`, at no cost in time if the speed ratio holds there (`DESIGNS.md` H.2) |
| H13 | fails as stated: a 30 % side grows faster than A1's 0.845 (0.863) and a 40 % side slower (0.829), per occupied slot, which moves the beaten share 18–19 points from the closed form at A1's growth (0.195 against 0.371, 0.547 against 0.355); read at the side's growth the closed form matches the engine within 0.5 standard errors; the figures that decide stand, 65 % against a 35 % side with the coalition's nodes beyond the cut and every window against a third (`SETTLEMENT.md` B5) |
| H10 | fails for B4's rule (51–58 % of its acceptances); holds per target by computation for the observed counting rule, which reads `(n, t)` and the distinct slots of the forks received: 408 blocks against a third under worst-case delay, 374 when withheld from, where B2 needs 1,510; with the worst-case walk's law a coalition keeping its chain private until acceptance fails at most 0.10 ε at `1e-3` and 0.0018 ε at `1e-9`, where the geometric law would allow 1.16 ε; not given the client's view; balancing, or publishing every win from 30 % up, stalls it and the depth rule caps it (`DESIGNS.md` H.3) |
| H7 | fails by two of its three tests (`DAG.md`, H7). Under a delay chosen by an adversary (E5) the balancing attack needs no more than GHOST's share, less than the chain's region at every block rate: counting one move per win, 0.40–0.45 at today's rate and `Δ = 10` s against 0.46, and 3–6 % at `f_A = 0.25`. As specified, one win can add weight on both sides of a conflict (E3); under E3's rule a second copy retracts the first, so one win still moves the balance twice, and the attack needs 0.235–0.279 at today's rate and 10 s and 0.318–0.326 at 1 s, below a third at every delay (`DAG.md` J.2). Under random delay the DAG settles against 25 % in 38 minutes at `1e-9`, against 59 on the chain (E2) |
| H14 | fails: with one move per win the first part fails (1.78 times as long at 10 s as at 1 s, against 1.25) and the second holds (4.97 hours against the chain's 6.78); with retraction, which E3's rule allows, neither holds: against a third no attack has a depth at any delay, and the phase stops at J.2 (`DAG.md` J.2) |
| H15 | fails: under J.1's rule a third holds the balance for ever at every delay from 1 s, so no bound exists against it; without retraction, which no rule every node applies alike achieves, the opportunity bound would need 31.2 hours at 10 s, above the chain's 23.0 (`DAG.md` J.3) |
| H16 | not tested: the phase stopped at J.2 |
| H17 | holds at the edge: against a third at `1e-9` on the specification's Blend the wait is 5.10 hours, 1.249 times the depth rule's 4.08 on the report's clock, which the hypothesis names; on the model's own clock it is 1.271 times (`SLOTS.md` K.1) |
| H18 | holds: 26.3 hours against a third at `Δ = 10` s and `1e-9`, 1.15 times B2's 1,510 blocks on the worst-case clock (`SLOTS.md` K.1); under K.7's bound by more, 10.1 hours, 0.44 times |
| H19 | holds: after `⌊k/f⌋` = 64,800 slots the chance against a third at 10 s is 6.6e-7, and `3⌊k/f⌋` = 194,400 holds a third with the nonce of §3.1 under its delay (26.6 hours) and after a deflated inference (29.8 hours, H.2's factor read at the old rates), with a factor of 1.8e+07 to spare (`SLOTS.md` K.2). Under K.7's bound the first part fails: after 64,800 slots the chance against a third at 10 s is 1.2e-16 (`SLOTS.md` K.7) |
| H20 | holds: without a floor one block and `K` slots fix a fork whatever the stake; at `3⌊k/f⌋` the floor against a third is 3,264 blocks under the worst case and 3,318 under random delay, and a chain nobody withholds from falls below it with chance below `1e-99`. Both forms of the floor meet the inference's correction, as blocks do: an eclipse by the smallest stake takes 8.6 or 9.75 days, against 8.2 in blocks (`SLOTS.md` K.3) |
| H21 | fails in its first part: at `3⌊k/f⌋` no floor separates partitions against a quarter in either model; the least window is 2.9 days under the worst case at 1 s, 17.5 at 5 s and none at 10 s, and under random delay 3.3 days with a side at the engine's growth. The second part holds: at a third none exists at any `K`, since `(1 + α)/2 = 1 − α` (`SLOTS.md` K.3). Counted on occupied slots, as the stake inference counts, the first part holds under random delay, a floor separating a quarter from 2.24 days, and still fails under the worst case (`SLOTS.md` K.9) |
| H22 | holds: against a third at 10 s and `1e-9` the bound for a wait in GRR's own model is 10.1 hours on the slot lottery and 9.2 in the continuous reading, under half of K.1's 26.3, and `⌊k/f⌋` = 18 hours holds a third at 10 s without grinding, the chance after it 1.2e-16 (`SLOTS.md` K.7) |
| H23 | holds under random delay, and under the worst case at 10 s fails in its second part: a cap of 5 % an epoch keeps a side of 0.3 below the density floor at `3⌊k/f⌋` for 62 days, against 9.75 without it; a fall of the active stake to 60 % then stalls finality under that form for 20.25 days under random delay, within three epochs, and 27.75 under the worst case, past them; the protection against a side of 0.3 lasts 0.73 to 1.38 times the stall after a fall to half at every cap, since the inference reads a split and a fall alike. Under the depth form a cap buys almost nothing and finality never stalls (`SLOTS.md` K.8) |
| H24 | holds: under random delay the floor on occupied slots, with referenced uncles, is 1,225 at 18 hours against a third, a fifth above the 1,022 on blocks, and separates partitions against a quarter from 2.24 days, against 516 on blocks; under the worst case the count of occupied slots is at least the count of blocks on every path, so the floor of 1,019 keeps its liveness (`SLOTS.md` K.9) |
| H25 | holds on testnet's Blend and the specification's, 147 s at the 95th percentile with rounds of 60 slots and a lag of 30, every round justified; fails as stated at the heavy point, where a lag of 30 lets a justified checkpoint leave the longest chain in 18 of 36 runs, and a lag of 60 gives 177 s (`NETWORK.md` L.2) |
| H26 | holds: at the analysis' minimum, 500 declarations, 1.67 % of the active stake, hold a third of a network of 1,000; holding 30 % needs honest declarations that lock 60 % of the active stake at full uptime, and none suffices at 95 % (`NETWORK.md` L.1) |
| H27 | holds: below a third of the declared weight one side at most certifies, in the closed form and in every engine run; at 0.34 an even split finalizes both sides (`NETWORK.md` L.3) |
| H28 | holds: 6.0 % of one Pi 5 core at 20,000 declared nodes and 60-slot rounds with ed25519-dalek (`NETWORK.md` L.5) |

Three notions of finality carry the document. They are measured separately and never mixed.

- **k-finality.** The latest immutable block `B_imm` of the Cryptarchia specification, the block
  `k` blocks deep. A node never reorganises past it. It is a protocol rule.
- **Settlement.** A block at depth `d` is displaced with probability at most `ε`, against an
  adversary holding stake share `α`, under a stated delay model. It is a client rule and needs no
  protocol change.
- **Certified finality.** A block is final once a certificate of anonymous votes exists for it.
  It is a protocol addition.

The multi-proposer DAG (L6) keeps the settlement notion but changes the structure it is measured
on: depth counts references inside a window of a block DAG instead of blocks on a chain.

| symbol | meaning |
| --- | --- |
| `f`, `k` | slot activation coefficient (1/30) and security parameter (2160 blocks); one slot is 1 s |
| `o` | orphan share: the share of produced blocks that end off the canonical chain |
| `α`, `α_eff` | adversary stake share; its share of chain-extending blocks, `α / (α + (1−α)(1−o))` |
| `ε` | accepted failure probability, per block for settlement, per round for votes |
| `D_vis`, `ρ` | mean time for a block to reach every node; the load `ρ = f·D_vis` (TSI report §3.3) |
| `Δ` | the delay bound of the adversarial network model, in slots |
| `n`, `Q` | expected anonymous committee seats per voting round; the quorum |

## 0. The brief

Stated by the owner, 2026-10-05: plan an exploratory research to investigate possible ways of
decreasing finalization times of Cryptarchia consensus.

The brief names no target time, no adversary and no finality notion. §3 Q1–Q3 ask for them.

Five constraints are carried from the Introduction of `cryptarchia-v1-protocol.md`. All five
bind; one opt-in relaxation of C1 is explored as a variant (§3 Q4).

- **C1 — Stake stays private.** No mechanism may reveal a participant's stake or link its
  actions. The specification names the mechanism to avoid: "If the activity of the leader
  reveals their stake values (e.g. through weighted voting), then this value can be used to
  reduce the anonymity set for the leader".
- **C2 — Liveness first.** Block production continues through a partition. Finality may stall;
  the chain may not halt.
- **C3 — No known participant set.** Any committee is drawn by a private lottery, never by
  identity.
- **C4 — Lottery wins travel through Blend.** A message that proves a lottery win reveals its
  sender's stake over time unless its origin is hidden. A vote is a lottery win. The node
  publishes block proposals through Blend, and gossips them directly only while the Blend
  membership is below its minimum size.
- **C5 — The node class.** Verification and bandwidth fit the slowest node the protocol
  targets.

## 1. What a first look says

Every number in this section is printed by `firstlook.py` beside this file
(`python3 firstlook.py`, a few seconds). Six gates check it against published or independent
results:

- Nakamoto's §11 tables, digit for digit.
- Grunspan and Pérez-Marco's corrected tables and their closed form `I_{4pq}(z, 1/2)`.
- The honest shares the specification's Praos annex reads off its plots.
- A bisection of Dembo et al.'s threshold equation.
- The Blend report's emission-quota table.
- A direct convolution of the committee tail.

A mutated copy of each implementation fails its gate. The models are crude on purpose: they size
the problem. §1.8 lists what they leave out and the phase that replaces each.

Three Blend configurations frame the numbers. The specification's has at most three blending
operations and `Δ_max` = 3 rounds per hop. At 3 hops and 2 s per hop, with a 6 s mean
end-to-end delay, the stake-inference analysis measured `o = 0.15` before uncle references
existed (`analysis-total-stake-inference.md`, `q = 0.85`). Testnet 0.3.0 runs one Blend layer
with a 1-round maximum delay. The TSI report's operating point, 8 s per hop with `o = 0.35`
(`reports/tsi/README.md` §6.10), is the heavy case.

### 1.1 Where the time goes

With uncle references, the stake inference holds *occupied* slots, canonical or referenced, at
`f`. The canonical chain therefore grows at about `f(1 − o)`, and k-finality takes about
`k / (f(1 − o))` slots. Before uncle references the inference held the canonical chain itself
at `f` and over-produced blocks instead (`analysis-total-stake-inference.md`, Cryptarchia
Metrics).

| configuration | `k` | no forks | `o = 0.15` | `o = 0.35` |
| --- | --- | --- | --- | --- |
| specification | 2160 | 18.0 h | 21.2 h | 27.7 h |
| testnet 0.3.0 | 120 | 1.0 h | — | — |

`k` also sizes the epoch. `s = 3⌊k/f⌋` is 54.0 h, and the epoch, `10⌊k/f⌋` slots, is 7.5 days
(10.0 h on testnet). A change to `k` moves both unless they are decoupled (§6.4).

`k` also bounds the partition the network heals on its own. When a partition ends, the side
that loses rolls back every block it made since the split. The Online rule "rejects chains that
diverge by more than `k` blocks" (Fork Choice Rule), and a node re-enters the Bootstrap rule
only at startup (§6.1). A side holding half the stake makes `k` blocks in 35.7 h, and one
holding a fifth in 88.8 h. At `k/10` these become 3.6 h and 8.9 h; at testnet's `k`, 2.0 h and
4.9 h.

### 1.2 What `k` buys

Under the Rosenfeld model the attacker mines privately from the moment the target block is
published, and wins if its chain ever overtakes. The depth it takes at `ε = 1e-9`, in blocks
and minutes:

| `α` | `o = 0` | `o = 0.15` | `o = 0.35` |
| --- | --- | --- | --- |
| 0.10 | 19 · 10 min | 22 · 13 min | 28 · 22 min |
| 0.20 | 43 · 22 min | 54 · 32 min | 86 · 66 min |
| 0.25 | 66 · 33 min | 89 · 52 min | 171 · 132 min |
| 0.30 | 108 · 54 min | 163 · 96 min | 434 · 334 min |
| 1/3 | 159 · 80 min | 269 · 158 min | 1,088 · 837 min |
| 0.40 | 458 · 229 min | 1,269 · 746 min | none |

`firstlook.py` prints the same table at `ε = 1e-3` and `1e-6`.

The model is exact for what it describes: it reproduces Grunspan and Pérez-Marco's corrected
double-spend tables, for example 6, 20, 32 and 133 confirmations for 0.1 % at `q` = 0.10, 0.25,
0.30 and 0.40. That is a proof-of-work race without delay. It does not cover a proof-of-stake
race under delay. The rigorous bounds for that case (Gaži, Ren and Russell, revised 2025-05-02,
§7) are the method B1 reproduces. Expect them to ask for more depth than this table.

Read the other way, `k = 2160` holds `ε = 1e-9` up to `α_eff = 0.4536`. That is `α` = 0.4536,
0.4137 and 0.3505 at `o` = 0, 0.15 and 0.35. `α_eff` reaches 1/2, and no depth suffices, at
`α = 0.4595` when `o = 0.15` and at `α = 0.3939` when `o = 0.35`. Testnet's `k = 120` holds
`ε = 1e-9` up to `α = 0.2764` at `o = 0.15`.

Two readings follow, both to be re-established under the proof-of-stake delay model (Phase B):

- The depth is set by the adversary the protocol must tolerate and by `ε`, not by the network.
  Against `α ≤ 0.25` the depth needed is 1–8 % of `k`.
- Forks lower the threshold itself: 0.46 at `o = 0.15` and 0.39 at `o = 0.35`, not 1/2.

### 1.3 What the specification already says about delay

The only delay analysis in the specifications is the Praos condition in the annex of
`analysis-block-times-blend-network.md`: `α_h (1 − f)^{Δ+1} ≥ (1 + ε)/2`, where `α_h` is the
honest stake share and `Δ` the maximum network delay. At `f = 1/30` and `ε = 1e-6` it admits an
adversary of at most 0.427 at `Δ` = 3 s, 0.366 at 6 s, 0.249 at 11 s and 0.169 at 14 s. The
annex reads 75 % and 83 % honest for the last two. At 15 s it admits 0.140, and beyond 19 s no
stake split satisfies it. The annex calls the common-prefix bound
"very loose". No specification derives `k = 2160`; it appears as a constant and as a simulation
input.

The condition is Praos's Theorem 7, for static stake. The full protocol's result is Theorem 11,
and Corollary 3 with a hash-derived nonce. Its bound adds the system's lifetime, the stake shift
over two epochs and a grinding term. Praos gives no concrete `k`, `f` or failure probability,
and never states the constant hidden in its `Ω(k)`. Its proven confirmation time, `u = 8k/f`,
is 6.0 days at `k = 2160`. The bound is loose by construction: it counts an honest slot only
when that slot has a single leader and the `Δ` slots after it are empty. Crypsinous proves no
consensus theorem of its own and inherits Ouroboros Genesis's.

So the only guarantee the specifications give, at the delay they modelled (about 11 s at most),
covers `α ≤ 0.25`.

The tight result is wider. Dembo et al. prove that the private attack is the worst attack, for
proof of work and for Praos-type proof of stake alike. A chain is safe while
`β < (1 − β)/(1 + (1 − β)fΔ)`, where `β` is the adversary's stake share (§7). At `f = 1/30` the
threshold is:

| `Δ` | 3 s | 6 s | 11 s | 15 s |
| --- | --- | --- | --- | --- |
| `β*` | 0.4875 | 0.4751 | 0.4545 | 0.4384 |

`Δ` is a variable of this study, not a fixed input (Q3). Blend's delivery deadline,
`T_M = ß(Δ_max + η)`, is 1 × (1 + 2) = 3 rounds on testnet and 3 × (3 + 2) = 15 rounds in the
specification today. Both are settings: the study derives the `Δ` each lever needs, and Blend's
parameters are chosen from it (C2). A threshold says whether a depth exists, not how deep it
is. The loose proof, not the protocol, is what caps the specification's guarantee at 0.25. How
much depth `k = 2160` buys near `β*` is B2's question.

### 1.4 The orphan share is the strongest lever; the block rate is not one, yet

`o` enters twice: through `α_eff` in the depth, and through `1/(f(1 − o))` in the time per
canonical block. At `α = 0.25` and `ε = 1e-9` the time to settle is 33 min at `o = 0`, 52 min
at 0.15, 63 min at 0.20, 132 min at 0.35 and 458 min at 0.5.

A collision model, `o = (1 − e^{−2ρ})/2`, matches the TSI engine at per-hop delays of 2 s
(0.21 against 0.20) and 8 s (0.34 against 0.35). It under-predicts at 32 s (0.49 against 0.60),
so it is used only for `ρ ≤ 1`. Under it, at `α = 0.25` and `ε = 1e-9`, in minutes:

| `D_vis` \ block interval | 60 s | 45 s | 30 s | 20 s | 15 s | 10 s |
| --- | --- | --- | --- | --- | --- | --- |
| 3 s | 76 | 59 | 43 | 33 | 28 | 23 |
| 6 s | 86 | 70 | 55 | 47 | 44 | 44 |
| 8 s | 93 | 78 | 65 | 59 | 58 | 61 |
| 17 s | 135 | 126 | 123 | 130 | — | — |
| 30 s | 216 | 221 | 235 | — | — | — |

`—` marks `ρ > 1`. At the TSI operating point (`D_vis` = 17 s) every block interval from 60 s to
20 s settles in 123–135 min: a faster block rate forks more and gains nothing. At `D_vis` = 3 s,
the order of testnet's single 1 s hop, shortening blocks from 30 s to 10 s cuts 43 min to
23 min. The block rate becomes a lever only once `D_vis` is small.

### 1.5 The repository's confirmation rule answers another question

The TSI report recommends waiting 4, 8 and 17 blocks for 99.9 % against 10, 20 and 30 % stake
(§6.10; §8.1, row 15). Its tail, `(α_eff/(1 − α_eff))^d`, is the chance that an attacker `d`
blocks behind ever draws level: the depth of the deepest reorganisation an attacker can force
from an arbitrary moment. A receiver needs something else: the chance that a block it relies on
is displaced by an attacker who began mining privately when that block appeared. With the same
inputs (`o = 0.35`, `ε = 1e-3`) the Rosenfeld depths are 9, 25 and 126 blocks. A client rule is
built on the second question (B4).

### 1.6 Votes cost thousands of anonymous seats a round

C1 forbids stake-weighted votes, so a vote is a private lottery win: one seat per note per
round, proven in zero knowledge and deduplicated by a nullifier. Honest seats vote once;
adversarial seats vote for both sides. Two conflicting quorums need `H + 2A ≥ 2Q`; a round
stalls when `H < Q`. With seats Poisson-distributed, the smallest expected committee that holds
both at `ε` per round:

| `α` | `ε = 1e-6` | `ε = 1e-9` |
| --- | --- | --- |
| 0.10 | 421 | 665 |
| 0.20 | 1,313 | 2,085 |
| 0.25 | 3,364 | 5,355 |
| 0.30 | 21,024 | 33,473 |

No quorum exists at `α ≥ 1/3`. Offline honest stake shrinks the window further: with a fifth
of it offline, and seats still drawn against all stake until the inference adapts, `ε = 1e-6`
takes 628, 3,067 and 17,872 seats at `α` = 0.10, 0.20 and 0.25, and none exists at 0.30.

`ε` is per round. One round per 30 s block is 1,051,200 rounds a year, so `ε = 1e-9` means
1.1e-3 expected safety failures a year; one round per 10 minutes means 5.3e-5. The
specification's `ProofOfLeadership` is 224 bytes, of which the Groth16 proof is 128 (Block
Header). A vote is at least a proof plus a nullifier and a target. At 5,355 seats and 224 bytes
each, one round carries 1.2 MB before Blend overhead.

### 1.7 Every extra lottery win is an emission, and Blend prices emissions

Blend hides a node's lottery wins only while they fit its cover quota. At the baseline cover
rate of one message a second across the network, the Blend report puts that ceiling at 0.147 %
of inferred stake at N = 20,000 (`reports/blend/README.md` §3.10). A vote is one more lottery
win, so votes multiply a node's emissions by `1 + n/(R·f)` for `n` seats per round of `R` slots.
A multi-proposer DAG (Areon, L6) makes every block a vote. At a production coefficient `f_A` the
stake wins `−ln(1 − f_A)` blocks a slot, which multiplies them by `ln(1 − f_A)/ln(1 − f)`:

| design | parameters | emissions per unit stake |
| --- | --- | --- |
| Peras-style votes | `n = 900` per 90 s (Peras's `U`) | ×301 |
| votes, `α = 0.25`, `ε = 1e-9` | `n = 5,355` per 90 s | ×1,786 |
| Peras-style votes | `n = 900` per 10 min | ×46 |
| votes, `α = 0.25`, `ε = 1e-9` | `n = 5,355` per 10 min | ×269 |
| Areon DAG | `f_A = 0.05` | ×1.5 |
| Areon DAG | `f_A = 0.25` (the paper's default) | ×8.5 |

The votes come to 10.0, 59.5, 1.5 and 8.9 messages a second across the network. To keep today's
ceiling, the cover rate, which every node carries, must rise by the same factor. This, not the
committee arithmetic, is the first constraint on L5 (D0). A DAG pays one to two orders of
magnitude less than votes.

### 1.8 What the first look leaves out

- **Proof-of-stake races.** The lottery ticket hashes the epoch nonce, the slot and the note, not
  the parent (`cryptarchia-proof-of-leadership.md`, ticket computation). One win can therefore
  sign blocks on several branches. The Rosenfeld model lets each win extend one chain. → B1.
- **Adversarial delay.** `o` was measured under random Blend delays. An adversary that schedules
  delivery within `Δ` can split honest leaders on purpose. → B1, B3.
- **Pre-mining.** An attacker may start its private chain before the target block. → B1.
- **The deployed delay.** Neither measured `o` comes from the node's own Blend. → A1.
- **Committee realism.** Offline stake enters as one case only. Error in the inferred total
  stake, honest votes split across forks and Blend loss are not in the seat model. → D2.
- **Spread.** The figures are means. The time to `d` blocks is Gamma-distributed, with a 95th
  percentile 1.57× the mean at `d = 10`, 1.32× at 30 and 1.17× at 100. → §5.

## 2. The levers

| lever | what changes | protocol change | first-look effect | main risk | phase |
| --- | --- | --- | --- | --- | --- |
| L1 settlement rule | a client confirmation depth `d(α, Δ, ε)` | none in consensus; a third level in the node's APIs | at `o = 0.15`, `ε = 1e-9`: 13 min (`α = 0.10`) to 52 min (`α = 0.25`), against 21.2 h | the depth diverges as `α` nears the threshold | B |
| L2 smaller `k` | the finality depth | `k`, and with it the epoch and everything timed by it, unless decoupled (§6.4) | proportional to `k`; testnet already runs `k = 120` | lowers the tolerated `α`; shortens the self-healing horizon | A3, B2, B5 |
| L3 fewer orphans | `D_vis` (Blend); a lottery threshold that rises with the slots since the parent (Ouroboros Taktikos); or a fork choice that weighs referenced uncles | Blend parameters, the lottery, or fork choice | `o` 0.35 → 0.15 cuts 132 min to 52 | Blend's privacy budget; GHOST-style weighting narrows the safe region (§7) | C |
| L4 block rate | `f` | a constant | none at `D_vis` = 17 s; 43 → 23 min at 3 s | more forks | C1 |
| L5 certified finality | anonymous-seat votes: a Peras-style certificate with a fork-choice boost and a cool-down, a checkpoint gadget, or endorsements carried in blocks; optionally slashable nullifiers. Variants: an opt-in public committee (Q4); certificates signed by Blend's declared nodes (Q12) | large | about two minutes in Peras | Blend's emission budget (§1.7); thousands of seats a round; safety only below 1/3; for Blend's declared nodes, safety rests on the declared set | D, L |
| L6 multi-proposer DAG (Areon) | several proposers per slot; blocks reference the recent tips; a fork choice local to the closest common ancestor counts recent references | replaces the chain and its fork choice; the ledger needs a total order | the paper: `k ≥ C1·w + C2·ln(1/ε)` with window `w ≥ Δ`; its comparison with Praos mixes block rates and metrics (`DAG.md`, E0) | anonymous eligibility (one block per win); emissions ×`ln(1 − f_A)/ln(1 − f)`; GHOST-style weighting may narrow the safe region | E |
| L7 other structures | parallel chains, ledger combiners | very large | — | multiplies proofs and emissions by the number of chains | §7 only |

Each hypothesis below can fail, and says what would fail it.

- **H1.** Under the proof-of-stake delay analysis, settlement against `α = 0.25` at
  `ε = 1e-9` needs at most `k/10` = 216 blocks at a `Δ` Blend can reach. B2 derives the largest
  such `Δ`. Fails if it is below what one Blend hop takes (testnet's 3 s).
- **H2.** `k = 2160` holds `ε = 1e-9` against `α = 1/3` up to the `Δ` the other levers need. B2
  derives the largest `Δ` at which it does. If that falls short, the study's first finding is a
  safety margin, not a latency.
- **H3.** The time to settle falls at least as `1/(1 − o)` as `o` falls. Fails if C1's
  engine-measured surface is flatter than the collision model.
- **H4.** A fork choice that weighs referenced uncles brings `α_eff` back to `α` without opening
  a cheaper attack. Expected to fail: the tight GHOST analysis finds its safe region inferior to
  the longest-chain rule's (§7). C3 confirms or refutes this at Cryptarchia's parameters.
- **H5.** A certified-finality design fits Blend's emission budget and the node budget of Q7 at
  `α = 0.25`. Fails if, for every committee size and round length that meet `ε`, either the
  cover-rate multiple `1 + n/(R·f)` (D0) or the verification cost (D3) exceeds the budget.
- **H6.** Automatic recovery can be made safe, so the self-healing horizon stops bounding `k`.
  A node that sees a fork deeper than `k` switches to the Bootstrap rule by itself and rejoins
  the honest chain. Fails if B5 finds that an attacker can trigger the switch to its advantage,
  or that the Bootstrap rule cannot tell the honest chain apart soon enough after a split.
- **H7.** Areon, instantiated with Cryptarchia's private lottery and `w ≥ Δ`,
  settles against `α = 0.25` at `ε = 1e-9` faster than L1 does on the chain, within the
  emission budget of Q7. Fails if E2's fitted depth gives a longer time than B2, if one win can
  add weight more than once (E3), or if its safe region under worst-case delay is narrower than
  the longest-chain rule's (E5).
- **H8.** A one-off round of recovery attestations separates an honest side holding `(1 − α)/2`
  from an adversary's fork holding `α` at `ε = 1e-9` with at most 10,000 seats for `α ≤ 0.30`,
  and no rule that reads chains and stake-weighted content alone does so at `α = 1/3`. Fails if
  the seats needed at 30 % exceed what one Blend round carries (D3), or if the adversary's vote
  splitting or timing lets its fork win (Phase H, H.1).
- **H9.** A Wesolowski class-group delay with an honest time of 100 minutes keeps the factor per
  nonce below 1.1 against a coalition up to 20 times faster than an honest node, with a proof
  under 1 KB verified in under a millisecond. Fails if documented hardware exceeds 20× or the
  verification cost is material at Cryptarchia's node class (Phase H, H.2).
- **H10.** Under a worst case of `Δ = 10` s a time-reading rule exists that accepts a chain at
  the worst-case honest rate no later than B2's depth and a chain nobody delays sooner. Fails if
  B3's delay-scheduling attack beats every candidate at its `ε`, or if every bound found exceeds
  B2's depth at every speed (Phase H, H.3).
- **H11.** The grinding term of Praos's Theorem 11 and of Genesis's main theorem depends on the
  number of nonces the adversary evaluates and on nothing else about its choice, and the nonce
  enters each bound only through the next epoch's leader distribution, so the lemma of H.2
  carries to `maxvalid-bg` with the same factor. Fails if either theorem conditions on the nonce
  elsewhere, through the stake snapshot or the density window, or if its grinding term is not
  linear in the candidates (Phase I, I.1).
- **H12.** The published estimates put the class number of a 1024-bit discriminant beyond
  `2^100` operations for the best algorithm, and a discriminant derived from the pre-nonce each
  epoch admits no precomputation, so the delay's sequentiality rests on a documented assumption at
  the design's size. Fails if an estimate puts 1024 bits below `2^100`, or if a published attack
  applies to derived discriminants; the discriminant then grows to 2048 bits, which doubles the
  squaring, or the group becomes an RSA group with a trusted setup (Phase I, I.2).
- **H13.** On the engine, a 30 % coalition's withheld fork is denser than an honest side holding
  35 % of all stake in 64–70 % of 36-hour windows and a third's in every one, within three
  points of B5's closed form, and two honest sides of an even split tie in 0.5–0.7 % of windows.
  Fails if the honest sides grow faster during a partition than the closed form assumes by enough
  to move the beaten share by more than five points, which makes rule 8's thresholds the
  engine's, not the model's (Phase I, I.3).
- **H14.** A fork choice that weighs every honest block turns delay into time, not depth. At
  `f = 1/30`, with one weight per win and a fixed tie rule, the strongest attack of J.2 against a
  third at `1e-9` needs less than a quarter more time at `Δ = 10` s than at 1 s, where B2's attack
  on the chain needs 1.9 times as much (3.5 to 6.8 hours). It also needs less time than the
  chain's attack at 10 s. Fails if neither variant of Phase J meets both parts (Phase J, J.2).
- **H15.** That robustness can be proven. A bound for such a fork choice under a delay chosen
  within `Δ`, ported or derived for the slot lottery, holds a third at `1e-9` and `Δ = 10` s
  within 11.5 hours: half of B2's 22.9, and about what the chain needs at `Δ = 1` s (9.6 hours).
  Fails if no analysis gives a depth against `ε`, or if the bound exceeds 11.5 hours (Phase J,
  J.3).
- **H16.** What `k` carries survives the change. On the chosen variant the nonce's choices at the
  cut-off stay within 10 % of the chain's under H.2's rule, and a deflated inference raises the
  depth by less than a fifth, where it raises the chain's bound by 61 % (1,510 to 2,426 blocks).
  Fails if either does not hold (Phase J, J.5 and J.6).
- **H17.** Under random delay a fixed wait costs little over the depth rule. Against a third at
  `1e-9` on the specification's Blend, the wait that holds `ε` is within a quarter of the depth
  rule's mean time: 5.1 hours, where 276 blocks take 4.1. Fails if longer (Phase K, K.1).
- **H18.** Under the worst case a wait costs less than a fifth over B2's depth on its clock.
  Against a third at `Δ = 10` s and `1e-9`, within 27.5 hours, where 1,510 blocks take 22.9.
  Fails if longer (Phase K, K.1).
- **H19.** The specification's slot parameter holds where the plain conversion fails.
  `K = ⌊k/f⌋`, 18 hours at `k = 2160`, does not hold a third at `Δ = 10` s and `1e-9`, and
  `K = s = 3⌊k/f⌋`, 54 hours, does, with the nonce of §3.1 under its delay, also after a deflated
  inference. Fails if either part does not hold (Phase K, K.2).
- **H20.** Finality in slots needs a floor. Without one, eclipsing a node for `K` slots fixes a
  fork there, whatever the adversary's stake. A floor sized at `1e-9` for the honest chain a third
  withholds from, at `K = s`, makes the eclipsed chain need more blocks than `k = 2160`, and delays
  finality on a chain nobody withholds from with chance below `ε`. Fails if either does not hold
  (Phase K, K.3).
- **H21.** Below a third a floor separates partitions. At `K = s`, against 25 % under both delay
  models, a floor exists that no two sides of a partition both reach while the adversary signs on
  both, and that the honest chain the adversary withholds from still reaches, each at `1e-9`. At
  a third none exists at any `K`. Fails if either part does not hold (Phase K, K.3).
- **H22.** In GRR's own model a wait costs far less than K.1 reads. B2 freezes its chain once the
  honest successes and twice the coalition's could make the target `D` deep, about `4/3` per block
  interval against a third, where the honest chain grows `D` blocks at its slowest, about `0.55` per
  block interval at 10 s. Against a third at `Δ = 10` s and `1e-9`, the bound for a wait is at most
  half of K.1's 26.3 hours, so `⌊k/f⌋` = 18 hours holds a third at 10 s without grinding. Fails if
  longer (Phase K, K.7).
- **H23.** A cap on the inference's correction buys the density floor time at a fixed rate in
  stalls. With a cap of 5 % an epoch, a cut-off side of 0.3 stays below the density floor at
  `K = 3⌊k/f⌋` for at least 45 days, and a fall of the active stake to 60 %, with nobody
  withholding, stalls finality under that form for at most three epochs. But at every cap the
  protection against a side of 0.3 lasts less than twice the stall after a fall to 50 %. Fails if
  any part does not hold (Phase K, K.8).
- **H24.** The floor gains from counting what the stake inference counts. Counted as occupied
  slots, canonical or referenced as uncles, the honest chain the coalition withholds from reads its
  stake's full occupancy under random delay, where blocks lose the orphans. At 18 hours against a
  third that floor lies at least a sixth above the floor on blocks, and under random delay a floor
  on occupied slots separates the sides of a partition against a quarter within a week. Under the
  worst case the count never falls below the canonical one, so the floor of 1,019 keeps its
  liveness. Fails if any part does not hold (Phase K, K.9).
- **H25.** Certificates of Blend's declared nodes are fast once they flow. With rounds of 60
  slots, a lag of 30 slots and votes gossiped directly, a block is finalized within 3 minutes of
  its slot at the 95th-percentile node, on every Blend of Q3, and every round with the honest
  declarations' votes at `q` justifies. Fails if either does not hold (Phase L, L.2).
- **H26.** SDP's minimum stake does not bound the declared set as the stake bounds the chain. At
  the minimum-stake analysis' parameters a coalition holding 2 % of the active stake holds a third
  of the declarations, and keeping a coalition of 30 % below a third needs honest declarations
  that lock at least 60 % of the active stake. Fails if the coalition needs more, or the honest
  declarations less (Phase L, L.1).
- **H27.** While the coalition holds less than a third of the declared weight, no partition
  certifies on both sides, so with certificates as the only finality every split heals without an
  operator, where no floor separates a partition against a third of the stake. Fails if two sides
  certify, on the closed form or on the engine's partition mode (Phase L, L.3).
- **H28.** Votes cost little at the Raspberry Pi 5. With 60-slot rounds, verifying a round's
  votes from 20,000 declared nodes takes under a tenth of one core with the node's Ed25519
  library, as the repository measured it. Fails if more (Phase L, L.5).

## 3. Questions for the owner

The first nine were settled by the owner on 2026-10-05, Q10 and Q11 on 2026-10-24, and Q12 on
2026-11-03, one at a time. Each entry records the decision and what it changes.

- **Q1 — Which notion is the target?** *Settled 2026-10-05 by the owner:* this is exploratory
  work, so every notion is explored: settlement (L1), a smaller `k` (L2), certified finality
  (L5) and the multi-proposer DAG (L6). Each runs to its own exit, numbers or a reasoned no.
  Phase A comes first. Phases B to E then run side by side, and F closes. No lever is cut at its
  first obstacle; an obstacle becomes a constraint the lever's designs are measured against.
- **Q2 — Which attacker share `α` and failure probability `ε` head the results?** *Settled
  2026-10-05 by the owner:* no headline pair. Every result is reported as curves across `α` and
  `ε`. `ε` is per block for settlement and per round for votes, each with its yearly failure
  rate. The hypotheses of §2 keep `α = 0.25` and `ε = 1e-9` as test points only. *2026-10-06, the
  owner:* the findings are reviewed against at most a third of the stake, 30 % at the loosest.
- **Q3 — Which delay model, and which Blend?** *Settled 2026-10-05 by the owner:* `Δ` is a
  variable, not Blend's present deadline. Every result is reported as a function of `Δ`. The
  study derives the `Δ` each lever needs, and Blend's parameters are adapted to it (C2). Inside
  `Δ`, both delay models are reported side by side, with no headline: the worst case, where an
  adversary delivers each message as late as `Δ` allows (the proofs, B2), and Blend's random
  mixing delays (the simulations, B3, C1, Phase E). The specification's Blend, testnet's and the
  TSI report's 8 s per hop are marked as reference points on the `Δ` axis.
- **Q4 — Do the five constraints C1–C5 of §0 bind?** *Settled 2026-10-05 by the owner:* all
  five bind. One relaxation is also explored, as a variant of L5: an opt-in public committee,
  where holders who choose to reveal their stake vote under their identity and everyone else
  stays private (D1). Other designs that break a constraint appear in the report as described
  alternatives with their numbers.
- **Q5 — Are protocol changes in scope?** *Settled 2026-10-05 by the owner:* yes; L2, L5 and L6
  change the protocol, and all are explored (Q1, Q9). The study ends in a ranked report that
  names RFC candidates. No specification is edited on this branch; RFCs are written later in
  `logos-lips`. *2026-10-06, the owner:* no RFC is drafted until the study is complete and
  reviewed.
- **Q6 — Do votes travel through Blend?** *Settled 2026-10-05 by the owner:* anonymous votes
  travel through Blend, as C4 requires. The opt-in committee's votes are public and may be
  gossiped directly (D1b). Anonymous votes sent by direct gossip are described as an
  alternative, with their stake leakage measured in D5, to price what Blend buys.
- **Q7 — What budget does finality traffic get?** *Settled 2026-10-05 by the owner:* curves
  first, the line later. Costs (cover-rate multiple, bandwidth, proving and verification time)
  are reported as curves on a Raspberry Pi 5, the node the repository's benchmarks already use.
  The owner draws the budget line once the curves exist.
- **Q8 — How long must a network split heal without an operator?** *Settled 2026-10-05 by the
  owner:* no fixed horizon. Today's 35.7 h for an even split is a reference point, not a bound.
  Both routes are explored in B5. One is shorter horizons, where an operator restarts nodes after
  shorter splits and a smaller `k` becomes possible. The other is automatic recovery, where a
  node that sees a fork deeper than `k` switches to the Bootstrap rule by itself.
- **Q9 — Is Areon in scope as a replacement for the chain, and is its simulator available?**
  *Settled 2026-10-05 by the owner:* Areon is in scope as L6. The simulator that produced the
  paper's values is `~/Logos/areon-simulations`, commit `4230a92`
  (`github.com/madxor/areon-simulations`). It is one notebook, `areon-full.ipynb`, holding an
  Areon simulator with greedy and ILP attacks and a Praos baseline. It needs Python 3.13,
  `pulp`, `numpy`, `joblib`, `psutil`, `matplotlib` and `pyvis`. Its own note puts a full run at
  up to 48 h on an M3 Pro with 48 GB. The owner warns it may not be correct, so E0 audits it
  before E1 relies on it.
- **Q10 — Which finality window `K`?** *Settled 2026-10-24 by the owner, after K.7:* `K = ⌊k/f⌋`,
  64,800 slots, 18 hours at `k = 2160`. Against a third at 10 s and `1e-9` it holds with the nonce
  of §3.1 under its delay, also after a deflated inference, with a factor of `1.2·10^4` to spare.
  With today's nonce it does not, so it rests on that nonce; at 20 s it does not either
  (`SLOTS.md` K.7).
- **Q11 — Which form of the floor?** *Settled 2026-10-24 by the owner, after K.8:* the depth form,
  with no cap on the inference's correction. `B_imm` passes a block once it is `K` slots old and
  `φ` = 1,019 blocks follow it, the worst case's floor at 10 s against a third. It never stalls
  finality. It holds a cut-off side back while the side makes `φ + 1` blocks: 1.05 days for a third
  and 3.5 for a tenth, where 2,160 blocks give 2.2 and 7.4 (`SLOTS.md` K.3, K.8). *2026-10-24, the
  owner, after K.9:* the floor counts occupied slots, a canonical block's or a referenced uncle's,
  as the stake inference counts them, at `φ` = 1,019. The protection does not move, and finality
  survives a larger fall of the active stake (`SLOTS.md` K.9).
- **Q12 — Which signers do certificates that shorten finality come from?** *Settled 2026-11-03 by
  the owner:* Blend's declared nodes. The nodes SDP registers for the Blend network sign blocks
  under their public keys, and two thirds of them form a certificate. Safety then rests on the
  declared set, which SDP's minimum stake bounds, not on the stake majority. Votes are plain
  signatures gossiped directly. The signers are a known set, so this route relaxes C3 as the
  opt-in committee of Q4 does (Phase L).

## 4. Work plan

### Phase A — the baseline and the map (`MAPPING.md`)

- **A1.** Measure, in the TSI engine at each Blend configuration of Q3: the orphan share, the
  distribution of `D_vis`, the canonical growth rate, and the time to depth `d` at p50 and p95.
  Where the engine's Blend model differs from the node's (release delay uniform in
  `[1, Δ_max]` rounds, delivery deadline `T_M = ß(Δ_max + η)`), align it first.
- **A2.** The dependency map. §6 is its first draft; A2 re-derives every number in it and adds
  what changes if finality comes 10× or 100× sooner.
- **A3.** The self-healing horizon: how many blocks each side of a partition makes per hour,
  against `k`, and what returns an online node on the losing side to the honest chain.

Exit: `o` and `D_vis` per configuration, with replicates and standard errors, and `MAPPING.md`.

### Phase B — settlement (`SETTLEMENT.md`)

- **B1.** Reproduce Table 1 of the 2025-05-02 revision of Gaži, Ren and Russell with the
  authors' `LCanalysis` code (MATLAB/Octave). The code takes the honest ratio and `D = f·Δ` as
  its inputs, so Cryptarchia's cases are new values of `D`. Gate: the table reproduces, and a
  mutation of the code's inputs fails it.
- **B2.** Tables of `d(α, Δ, ε)` at `f = 1/30` over a range of `Δ`, as upper and lower bounds,
  with the reference points of Q3 marked. Add the `(α, ε)` that `k = 2160` and `k = 120` hold at
  each `Δ`, and the largest `Δ` for H1 and H2. Where the bounds stay far apart, the lower bound
  is an attack and the upper bound the guarantee; report both.
- **B3.** Validate against the engine. Add a targeted private-chain attacker (starts at the
  target block, may pre-mine, may sign several branches per win) and a delay-scheduling
  attacker. Compare measured displacement rates with B2 where they are measurable
  (`ε ≥ 1e-4`).
- **B4.** A client confirmation rule: a depth table, the assumptions a client accepts with it,
  and the third level the node's APIs would expose between tip and LIB.
- **B5.** A smaller `k` (L2). For `k` = 2160, 1080, 432, 216 and 120: the `(α, ε)` each holds
  (B2), the self-healing horizon it gives (A3), and the epoch-timed effects of §6.4. Do this
  once with the epoch tied to `k`, as today, and once with the epoch decoupled from it. Sketch
  the decoupling: which epoch phases need `k`-deep finality, and which need only chain growth or
  chain quality. Then the two routes of Q8:
  - **Shorter horizons.** What an operator must do after a split each `k` no longer heals.
  - **Automatic recovery.** A node that sees a fork deeper than `k` switches to the Bootstrap
    rule by itself. Design the trigger, then attack it: can an adversary build a deep fork that
    drags honest nodes into the Bootstrap rule to its advantage? Decides H6.

### Phase C — rate and forks (`RATE.md`)

- **C1.** The time-to-settle surface over `(f, D_vis)`, from the engine's measured `o` instead of
  the collision model. Decides H3.
- **C2.** From the `Δ` each lever needs (B2, D1, E2), derive Blend parameters that deliver it,
  through `T_M = ß(Δ_max + η)` and the resulting `D_vis`, and what they cost in privacy. Settled
  with the Blend owners, not here.
- **C3.** A fork choice that weighs referenced uncles. First compute the GHOST safe regions of
  Gaži, Motaqy and Russell at `f = 1/30` and each `Δ`. Only if a region beats the longest-chain
  rule's, write the rule and run the attacks (private chain, balance) in the engine. Decides H4.
- **C4.** A lottery threshold that rises with the slots since the parent (Ouroboros Taktikos):
  read the paper, check that the slot gap can be a public input of the proof of leadership, and
  measure the orphan share it leaves in the engine.

### Phase D — certified finality (`CERTIFIED.md`)

- **D0.** The emission budget, first. Map the cover-rate multiple `1 + n/(R·f)` over every
  committee size and round length that meets `ε`, and what the quota ceiling becomes. D1
  designs against this map. Once the owner draws the budget line (Q7), D1 states, for any
  design beyond it, what would have to change for it to fit: a larger cover budget, longer
  rounds, or fewer emissions per vote.
- **D1.** Design sketches, led by a Peras-style certificate with anonymous lottery tickets as
  votes, a fork-choice boost and a cool-down. Beside it: a two-round checkpoint gadget, and
  endorsements carried in blocks. For each: how it keeps C1–C5; how it composes with the
  longest-chain rule, `B_imm`, pruning and the uncle window (§6.4); and what it does when a round
  fails. Peras's proofs assume private sortition with a known expected committee size; D1 checks
  that the assumption holds for anonymous tickets. A seat's tag per round can reuse the
  construction of `ρ_LEAD` under a vote domain separator: fixed per note and round, unlinkable
  across rounds. Stake moved during the epoch carries no honest vote, as Crypsinous rules for
  leadership.
- **D1b.** The opt-in public committee (Q4). Holders who choose to reveal their stake vote
  under their identity; everyone else stays private. Their votes need no anonymous seats, so a
  stake-weighted committee becomes possible, and with it signature aggregation and direct
  gossip. Questions:
  - What share of all stake must volunteer for safety and liveness?
  - Whose honesty does a certificate then rest on: the volunteers' or the chain's?
  - How does the private chain treat a certificate?
  - What do volunteers reveal, and does it narrow the anonymity set of everyone else?
- **D2.** Committee tails with offline stake, error in the inferred total stake, votes split
  across forks, and Blend loss. The seat lottery is derived from the leader lottery.
- **D3.** The cost model: vote size, proving and verification time on the node of Q7, Blend
  load, and aggregation options. Cryptarchia's proof of leadership is the base for a vote
  proof; Crypsinous's leadership circuit, for scale, has 201,493 constraints. Decides H5.
- **D4.** Forward security and accountability. Cryptarchia leaves out Crypsinous's protection
  against adaptive adversaries: no note evolution, no per-slot key erasure (PoL specification,
  Comparison with Original Crypsinous PoL). Whoever later learns a note's key can therefore
  sign for its past wins, and could forge past rounds' certificates the same way. Decide
  whether votes carry their own forward security, either a per-round key erased after voting
  (as Crypsinous does per slot) or Praos's key-evolving signatures, and what a bootstrapping
  node may then trust. Then accountability: nullifiers that reveal the note key when a seat
  votes twice in a round (rate-limiting-nullifier style), and the note lock that slashing would
  need.
- **D5.** Privacy beyond the count, including what anonymous votes would leak if gossiped
  directly instead of through Blend (Q6). Crypsinous's model makes the frequency of leader
  election "the only privacy leakage"; votes add a sample every round. Each vote also reveals
  which block its sender saw, the signal the specification's tagging attack exploits
  (Limitations of Cryptarchia V1). Measure what seats leak beyond block wins, against
  `analysis-cryptarchia-de-anonymisation-of-relative-stake.md` and the leakage results of §7.
- **D6.** Simulate the leading design in the engine: time to certificate, liveness under
  partition, safety under the delay-scheduling attacker.

Exit: a ranked design with numbers, or a reasoned no.

### Phase E — the multi-proposer DAG (`DAG.md`)

- **E0.** Audit the simulator (Q9) against the paper's algorithms before any figure is trusted.
  A first read found seven items to confirm or fix:
  - **Attack choice.** Every figure cell attacks through `attack_on_block`, which calls the
    greedy attack. The ILP attack, which the paper reports as the stronger one (§6.4, §6.9), is
    present but not wired in.
  - **Delay rounding.** Arrival times are stored as `int32`, so sub-slot delays are truncated.
  - **Unbounded delay.** Delays are exponential and so have no bound, which leaves the
    theorem's `w ≥ Δ` without a `Δ`. The figure cells sweep mean delays from 2 s to 60 s and
    fix 10 s elsewhere, against the paper's stated default of 7.5 s.
  - **Units.** The notebook defines a virtual block as 30 slots (cells 22 and 24) and bins its
    histograms in 30-slot bins. The paper never defines the unit; E1 confirms it per figure.
  - **One adversary identity.** The adversary is one identity and wins at most one block a
    slot. Its withheld blocks are scored as a weight race after the fact; honest nodes never see
    them released.
  - **Reorg measure.** Reorg length is measured in slots, from the attacked block to the last
    adversarial block. The code's own comment calls this imprecise. Definition 5.1 counts
    depth along short references.
  - **Seeds.** The Areon cells set no random seed; the Praos cells do.
- **E1.** Reproduce Areon's comparison with Praos at 30 % stake with the audited simulator:
  15-block reorgs at about 1e-2 for Praos against 1.5e-5 for Areon-Base, 10-block reorgs at 0.7
  against 8e-5 (§6.9). Then run its empirical settlement procedure (§5.6): fit
  `P_reorg(d) ≈ A·e^{−ϱd}` and report `d*(ε) = ln(A/ε)/ϱ`. Gate: the paper's figures
  reproduce.
- **E2.** Instantiate at Cryptarchia's parameters: `w ≥ Δ` over the `Δ` range of B2, the
  reference points of Q3, and `α` from 0.10 to 0.30. Fit `C1` and `C2` of Theorem 5.6 and set
  `d*(ε)` and its wall-clock time against B2's chain numbers.
- **E3.** Private eligibility. Areon-Base signs blocks under an identified validator's VRF key;
  Cryptarchia's proof of leadership is anonymous and does not depend on the parent. Weight
  counts references, so a win must add weight once. The tag exists: every header carries
  `ρ_LEAD = hash(NONCE_CONTRIB_V1 ‖ sl ‖ noteID ‖ sk)`, which is fixed per note and slot, so a
  second block from the same win repeats it. Specify how the weight counts each `ρ_LEAD` once,
  and what happens to both blocks. Cryptarchia's lottery runs per note, so an
  adversary that splits its stake can win several blocks in one slot, where the simulator's
  single identity wins at most one. Measure what that adds. Check the paper's parallelism bias
  (§6.3) under the private lottery.
- **E4.** The ledger. Areon exports a partial order; its total order is an analysis device only.
  Mantle executes transactions in order, so specify a deterministic order over the preferred
  frontier's ancestors and check it against channels, SDP and the execution market. State how
  the stake inference counts a DAG, where concurrent blocks are referenced rather than orphaned.
- **E5.** The safe region under worst-case delay: does the window-filtered, CCA-local weight keep
  the longest-chain threshold, or narrow it as GHOST's weight does (§7)? Analysis, plus the
  delay-scheduling attacker of B3.
- **E6.** The cost: the emission multiplier `ln(1 − f_A)/ln(1 − f)` (§1.7), references per block, and the
  maximum-antichain computation on the node of Q7.

Exit: Areon ranked against L1 and L5 by number, or a reasoned no.

### Phase F — the report (`reports/finality/`)

The options ranked by time gained, protocol change, privacy cost, resource cost and residual
risk, with RFC candidates. Every number reproduces from a `make` target.

### Phase G — further routes (`FURTHER.md`)

Ways to shorten finality that phases B–E do not cover, each read against 30 % and a third.

- **G1.** B7's nonce passed through a sequential delay that outlasts the coalition's decision
  windows, so that its decisions before the cut-off are blind. Read the chance that the lead after
  the cut-off outlasts the delay (B6's `Z`), and the depth with the choices at the cut-off alone.
- **G2.** The epoch length decoupled from `k`: which of route 3's costs it removes, from B6 and B7's
  `k = 2160` rows.
- **G3.** Blend's delay as a lever: the depth under both delay models for every Blend setting A1
  measured, with `Δ` the setting's 99th-percentile delay.
- **G4.** A client rule that also reads the chain's density, a first look under random delay: the
  depth at which a chain nobody withholds from settles, and what the total-stake inference does to
  the signal.
- **G5.** Anchoring a checkpoint to another chain: analysis only.
- **G6.** Blend's delays under adversarial relays: the engine with the coalition's relays holding
  every honest block for the longest mixing delay, and B3's race on its timelines.
- **G7.** The total-stake inference as a lever: the depths after a period of withholding under
  both delay models, the gain from choosing the raise level, and a cap on the correction.

Exit: each route with its gain, its cost and what is open, in `FURTHER.md` and the report.

### Phase H — three open designs

The three questions phases B–G leave open, each with a hypothesis (H8–H10 in §2) that can fail.
Order: H.2 first, the cheapest and the one route 1's specification candidate waits for; then
H.1; then H.3, the only one that is research rather than design.

- **H.1 — A recovery trigger that survives a partition.** B5's rule 8 shows that no density test
  tells a third's withheld fork from an honest third, and that a 30 % fork beats an honest 35 %
  side in 64–70 % of windows.
  1. *The impossibility, stated.* A short argument in `SETTLEMENT.md` B5: after an even partition
     under an adversary holding a third, three chains each produced by a third of the stake are
     indistinguishable by any rule that reads chains and their stake-weighted content alone, so
     any such rule picks the adversary's fork with probability at least a third. Below a third
     the honest sides hold `(1 − α)/2 > α` each, and the question is how much stake-weighted
     evidence separates `(1 − α)/2` from `α` at `ε`.
  2. *Recovery attestations.* A one-off round of anonymous-seat votes (Phase D's machinery:
     `committee.py` for the seats, `votes.py` for the round through Blend), cast only after a node
     holds two chains that both exceed `k` blocks since their divergence, in which each node votes
     for the chain it followed. Rule: discard every chain whose attested share, with the round's
     noise margin, is at or below `α`; among the rest take the densest; break ties by rule 7.
     Compute the seats that separate `(1 − α)/2` from `α` at `1e-9` per incident for `α` of 0.25,
     0.30, 0.32 and 0.33 (the count diverges at a third), the round's Blend cover and the stake it
     reveals (D5) as a one-off cost, and the adversary's moves: splitting its votes between the
     honest sides (it then chooses which honest history survives, which any resolution gives it),
     withholding its votes, and voting while the honest sides are still unevenly reconnected.
  3. *Anchoring, placed.* An anchor on another chain timestamps a block; it does not show the
     block was public, and an anchor carrying a proof of leadership is stake-weighted and meets the
     same symmetry. Write the decision table: which mechanism resolves an eclipse (rules 1–8), a
     partition below a third (attestations), a partition at a third (none), a long-range fork with
     bought keys (anchors or the horizon `H`), and bootstrapping (checkpoints).
  4. *Partition detection in the node.* Rule 8's test as a detector: the density a node's own
     chain shows against the `(1 − α)` expectation over the window, its false-alarm rate from the
     binomial model (`recovery.py`), and what the node does while it fires: it reports `B_imm` as
     provisional and refuses the recovery comparison.
  Exit: `DESIGNS.md` H.1 (the one-off round), the report's §6 and §13. If H8 fails, the trigger
  stays an eclipse-only device and partitions deeper than `k` are the operators', as today.
- **H.2 — The delay function and its speed ratio.** G1 needs a delay of `T_a` ≥ 10 minutes on the
  coalition's hardware; honest nodes pay `R·T_a` for a speed ratio `R`; the lottery-constants
  phase leaves 36–72 hours.
  1. *Literature, pinned:* Wesolowski (ePrint 2018/623) and Pietrzak (2018/627); the Boneh, Bünz
     and Fisch survey (2018/712); Chia's class-group VDF and the measured speed-ups of its hardware
     competitions; the Ethereum VDF work and MinRoot's cryptanalysis (2023); CIP-0161's 10× and
     its sources. ePrint PDFs through the archive; Chia's and Ethereum's pages directly.
  2. *The design:* the input `hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m)`, fixed at the cut-off; the output as
     the epoch's nonce; a Wesolowski proof carried by the first block that uses the nonce, and
     verified by every node in place of the computation; the computation by any node, the honest
     leaders of the phase included; the validity rule for blocks of the new epoch; and what
     happens if no block carries the proof before the epoch starts.
  3. *Sensitivity* (`scripts/h2_delay.py`): the factor per nonce G1 measures at `T_a` of 1, 3, 5,
     10 and 20 minutes against the honest time `R·T_a` for `R` of 2, 5, 10, 30 and 100, and the
     share of the phase that time takes. The design's margin is the ratio of the honest time to
     the decision window before the cut-off, a few minutes: with 100 honest minutes a coalition up
     to about 20 times faster still decides blind, and a faster one returns B7's estimate. This
     premise was wrong: a candidate of the last sub-window exists from the sub-window's start, so
     the delay must span the sub-window (H9's verdict, `DESIGNS.md` H.2).
  Exit: `DESIGNS.md` H.2 gains the parameters and the literature table; the report's §13; the
  specification candidate of §1 gains the delay. If H9 fails, the delay stays an estimate's
  support and route 1 keeps B7's factor.
- **H.3 — The time-reading rule under a worst case of `Δ`.** B4's rule is derived under random
  delay; under the worst case the coalition also delays honest blocks and runs the two-chain
  attack of B3, and the proven depth reads no time.
  1. *The counting bound.* Every block of a competing chain is a distinct lottery win: the
     coalition's, or an honest one that is not on the canonical chain. Given `n` canonical blocks
     in `t` slots, the competing chain holds at most `A(t) + H(t) − n` blocks above the fork, with
     `A` and `H` Poisson at the coalition's and the honest rates, so the target falls only if
     `A(t) + H(t) ≥ 2n + 1`, plus the lead and the catch-up walk. Compute the depth this gives at
     the worst-case honest rate; the expectation is that it is loose, about 3,000 blocks against a
     third at 10 s, since `E[A + H]` is `1.85 n` there.
  2. *A pre-check before any derivation.* Play B3's delay-scheduling attack (`grr_attack.py`) and
     the private attack on the slot lottery at `Δ = 10` s, record `(n, t)` at each candidate
     rule's acceptance, and measure each attack's success against the rule at `1e-3`. A rule the
     attack beats is dead; a rule that holds motivates a bound.
  3. *A time-conditioned bound.* Adapt the port's recursion (`lcbounds.py`, the Markov chain over
     the slot alphabet) to a fixed elapsed time with the canonical depth as a state, so that the
     bound is read at `(n, t)` rather than at `n` alone. Research: days, and it may not close.
  Exit: `DESIGNS.md` H.3, a worst-case variant or the negative result; the report's §3.2 and
  §13. If H10 fails, the client keeps the depth rule under the worst case and reads time under
  random delay only, as now.

### Phase I — what the designs still rest on

Three items phase H left open, each with a hypothesis (H11–H13 in §2) that can fail. Order:
I.1 and I.2 first, both reading, both cheap, both feeding `DESIGNS.md` H.2; then I.3, the only
engine work. None depends on another.

- **I.1 — Praos and Genesis, pinned, and the reduction placed against them.** H.2's argument
  attributes Praos's grinding term to the pinned reading of §7.1 and does not quote it, and says
  nothing of Genesis, whose fork choice Cryptarchia's Bootstrap rule is (`MAPPING.md`,
  `maxvalid-bg`). The ePrint server answers 403 to this tool; the archive's raw snapshots do not:
  Praos (2017/573) at `web.archive.org/web/20250102045847id_/`, Genesis (2018/378) at
  `20241228192149id_/`, Wesolowski (2018/623) at `20241227125535id_/`, each fetched with `curl`
  into a directory of its own and read page by page.
  1. *Pin.* For each paper the revision date on its first page and the SHA-1 of the file, in
     §7.1 beside the existing entries; where the snapshot is an older revision than the one §7.1
     names, the difference is recorded and the newer one asked of the owner.
  2. *Quote.* Praos: the statement of Theorem 11 and of Corollary 3, with the grinding term as
     written and the definition of the quantity it depends on; the epoch-randomness rule, which
     slots' VRF outputs the nonce hashes; any sentence that bounds the adversary's influence on the
     nonce. Genesis: the main theorem for `maxvalid-bg`, the dynamic-availability assumptions it
     adds, where the nonce enters its proof, and its grinding term. Each quote verbatim into
     `DESIGNS.md` H.2 under its source.
  3. *Place the lemma.* State H.2's reduction in the papers' terms: candidates formed at times
     `τ_i` with outputs at `τ_i + T_a`; a choice among candidates without outputs is blind and the
     schedule is a fresh sample; a choice among evaluated ones costs the union bound over their
     expected number, `E[G_min]` bounded by H.2. Then check, against the quotes, that each
     theorem's bad event is a property of the leader schedule given a uniformly random nonce, that
     the nonce enters only there, and that the stake snapshot is fixed before any candidate exists.
     Record which theorem covers which of Cryptarchia's two rules: the Online rule is
     `maxvalid-mc` within `k`, the Bootstrap rule `maxvalid-bg`.
  4. *What remains.* The formal write-up; the lifetime sum over epochs as Praos takes it; the
     bad events' independence across epochs, which Praos's proof handles and ours inherits.
  Exit: `DESIGNS.md` H.2 gains the quotes and the lemma, §7.1 gains Genesis, the report's §13
  names the rule each theorem covers. If H11 fails, the obstruction is named as what a proof
  needs, and the factor stays a result within B6's model.
- **I.2 — Class-group sequentiality, pinned and sized.** The delay's security is an assumption,
  not a theorem; the design has to state it, size its parameters from published estimates and
  say what breaks if it fails.
  1. *The assumption.* Wesolowski's statement of sequential squaring in a group of unknown order,
     and the adaptive-root assumption his proof needs, from 2018/623 and the Boneh, Bünz and
     Fisch survey already pinned (2018/712), verbatim.
  2. *The class number.* The best published algorithms for the class number of an imaginary
     quadratic order and their cost at 1024 and 2048 bits: Hafner and McCurley, Buchmann and
     Hamdy's parameter table, Biasse and Jacobson's improvements; Chia's rationale for 1024 bits
     and its discriminant derived from each challenge; the small-order elements that a discriminant
     must avoid and how Chia avoids them. ePrint through the archive, Chia's pages directly, as
     H.2 read them.
  3. *The design's size.* The discriminant derived from the pre-nonce each epoch, so that no
     class group is known before its candidate is formed; 1024 bits if the estimates hold H12,
     2048 if not, with the squaring time and the honest hours of H.2's table at each; and the
     failure mode: a class number computed for the epoch's discriminant evaluates the delay at
     once, under which the coalition sees every value the binding gives at the cut-off and its
     decisions before it, still no worse than today's nonce.
  Exit: H.2's sources table gains the rows, its design paragraph the discriminant and its size,
  the report's §13 one sentence. If H12 fails, the design names the fallback and its cost.
- **I.3 — A partition mode in the engine.** B5's rule 8 and H.1's detector read partitions in
  closed form only; the engine cannot split the network. The closed form takes each honest side
  to grow at the measured growth `g` for its share; a side that is a smaller network with a lower
  block rate may grow faster per win, which is what the engine can show.
  1. *The mode.* `tsi_sim` gains a partition: a share of the honest nodes, chosen by stake as the
     coalition is, cut from the rest for a span of slots. A block made on one side reaches the
     other no earlier than the span's end plus the path latency; blocks made before the span are
     unaffected. A Blend copy whose relay lies across the cut is lost and the sender's fallback
     applies, through G6's copies and fallback. The windowed fork choice assumes every old block
     has reached every node, which a partition breaks, so a partition forces the full scan as the
     selfish strategy does. The fields enter the key only when set.
  2. *The measurement* (`scripts/b5_partition_engine.py`, 64 runs a cell): for `α` of 0.25,
     0.30 and a third, an honest side of 0.30, 0.35 or 0.40 of all stake against the rest, a
     36-hour window that the partition spans, the coalition withholding: each side's density over
     the window as rule 8 counts it, the chain's blocks, as `maxvalid-bg` does (the runs reference
     no uncles); the share of windows in which
     the coalition's fork is strictly denser than the smaller side, against `partition.csv`; ties
     between even honest sides without a coalition, against `ties.csv`; each side's own density
     against the `(1 − α)` threshold of H.1's detector; and at rejoin, which chain the nodes of
     each side follow under the engine's longest-chain choice, with the note that the engine has
     no `k` cap.
  3. *Gates.* Without a partition every key and every tree is unchanged; with a partition no
     block crosses before the span ends; a copy through a relay across the cut is lost; two even
     honest sides without a coalition tie at the closed form's rate; the beaten shares lie within
     three points of the closed form or the difference is traced to the sides' growth, which the
     run records.
  Exit: `SETTLEMENT.md` B5 gains the engine's columns beside the closed form, the report's §6
  reads them, the engine gains the mode and its tests. If H13 fails, rule 8's thresholds are
  re-read from the engine's growth per side and H.1's seats recomputed at it.

### Phase J — a fork choice that tolerates delay, to shrink `k`

`k` binds every node, so it must hold under the worst case. Under the longest-chain rule the worst
case grows with the delay. Against a third at `1e-9`, B2's bound doubles from `Δ = 1` s to 10 s,
758 to 1,510 blocks, and its attack grows from 278 to 445 blocks. In time that is 9.6 to 22.9
hours for the bound and 3.5 to 6.8 for the attack. The adversary turns each second of delay into
honest blocks the chain discards. Areon (§7.1) counts every honest block made within a window
instead, so that a delay costs time, not weight. Its Theorem 5.6 asks `k ≥ C1·w + C2·ln(1/ε)`
with `w ≥ Δ`, and the delay enters only through `w`.

Phase E measured the premise and what blocks it:

- **The premise holds for the private attack.** Under a delay of 1–20 s at today's block rate,
  the DAG's private race against a third needs 34–42 layers at `1e-3`, 28–40 minutes, and no
  honest block is wasted (E5).
- **No bound covers the DAG.** The paper's model lets the adversary schedule every delivery
  within `Δ` (§2.1). Its drift, `E[G] ≥ γ·λ_h·w` (equation (4)), assumes that the honest
  references land on one side. E5's balancing attack splits them: at `f_A = 0.25` and
  `Δ = 10` s, 3–6 % of the stake holds the balance. The paper does not discuss the attack.
- **At today's block rate a third is inside the edge, counting one move per win.** At `Δ = 10` s
  the balancing attack needs 0.404 of the stake with ties the adversary steers, and 0.451 with a
  tie rule every node applies alike, such as the win tag of each side's first block (`DAG.md` J.1).
  The paper's own rule, the tip with the larger `y` (Definition 2.5), is one the adversary steers.
  With one move per win a third cannot hold the balance forever. How long it can, and so how deep
  a block must be before every attack within `Δ` has failed at `1e-9`, was not measured before
  J.2. J.1 then found that a second copy of a win retracts the first, and with it the edges fall
  to 0.235 and 0.279, below a third (`DAG.md` J.1, J.2).

This phase measures that depth, and bounds it if it can. Two variants are carried side by side:

- **(a) The chain with GHOST's weight.** The fork choice weighs each branch by every block that
  descends from it and that the node holds, orphans included, each win once. Uncle references,
  in the protocol since revision 1.2.0 with a window of 12 block intervals, carry the orphans on
  chain. The ledger, the nonce and Mantle's order stay the chain's. This is C3's rule.
- **(b) Areon-Base**, as E1 built it, with Phase E's corrections: weight since the closest common
  ancestor (E2), one weight per win (E3), references only to the preferred frontier (E4), and a
  window of `Δ` plus several block intervals (E2, E5).

Order: J.0 first. Then J.1 and J.2, the cheap test: if no variant beats the chain's attack, the
phase stops there. Then J.3, the research. J.4–J.6 run beside J.3, and J.7 closes the phase.

- **J.0 — The reading, settled with the owner.** The owner co-authored Areon. Three readings
  decide what is analysed, asked one at a time:
  1. *The adversary.* Whether Theorem 5.6 is meant against an adversary that schedules every
     delivery within `Δ`, as §2.1 states, and if so which step of its proof excludes E5's
     balancing attack.
  2. *The weight.* Accumulated since the closest common ancestor, the only reading E2 found to
     settle, rather than over the last `w` slots, as Definition 5.3 counts it.
  3. *The unit of `k`.* Slots, as Corollary 5.9's `T_final = k·τ_slot` reads it, rather than
     short-reference layers, as Definition 5.1 counts them. E5 found that a depth in layers holds
     only at the delay it was set for.
  Without an answer the phase takes E1's choices and counts `k` in slots. The v1 PDF read for
  this plan has SHA-1 `6b3b4082`.
- **J.1 — One weight per win, and the tie rule.**
  1. *The tag.* The weight counts each win once on a side, and a win found on both sides weighs
     on neither (E3). The tag must be the same whatever the parent, as today's `ρ_LEAD` is. H.2
     binds the nonce contribution to the parent, so it differs from parent to parent. The proof of
     leadership then carries two values: a win tag that does not depend on the parent, for the
     weight, the tie rule and equivocation; and the contribution, for the nonce, bound to a parent
     value the adversary cannot vary. Price the second hash in the circuit.
  2. *The tie rule.* Equal weights are broken by the win tag of each side's first block. Every node
     holding both sides decides alike, unlike the paper's rule on the tips, and a withheld block
     wins a tie only when its tag is smaller, unlike under `(slot, y)` (`DAG.md` J.1). Measure
     what the adversary gains by choosing which withheld win to publish when its tag wins the tie:
     B7's displacement, on the new rule.
  3. *A repeated tag.* Both blocks stay valid and referable, and the rule above sets their weight.
- **J.2 — Every attack within `Δ`, at today's block rate** (`balance.py`, `e5_delay.py`,
  `areon.py`, `grr_attack.py`).
  1. *The balance's tail.* Extend E5's phase chain from the edge to the chance that the balance
     still holds after `t` slots: `α` of 0.25, 0.30 and a third, `f = 1/30`, `Δ` of 1, 2, 5, 10
     and 20 s, with the fixed tie rule and with ties the adversary steers.
  2. *The combined attack.* The adversary holds the balance while it builds a private branch, and
     releases the branch at the moment that maximises its success at each depth. Played on the
     slot lottery with a delay chosen per block within `Δ`, as B3 plays GRR's attack on the chain.
  3. *The tie rule's exploit* of J.1, inside the same play.
  4. *Both variants, and the chain beside them* at B2's lower bound.
  Gates: with `Δ = 0` the plays equal E2's race; on a chain-shaped DAG they equal B3's; the
  balance's tail matches a slot-level simulation of the phases; each attack's success falls with
  depth; each gate has a mutation that fails it. The depth in slots at `1e-9` of the strongest
  attack, extrapolated as B2's lower depths are, is the least `k` a variant can claim. If no
  variant beats the chain's attack at `Δ = 10` s against a third, 445 blocks or 6.8 hours, H14
  fails and the phase stops.
- **J.3 — A bound.** `k` binds every node, so it rests on a proven bound, as B2 is for the chain.
  1. *Read and pin* Kiffer, Rajaraman and shelat (§7.2), which treats GHOST and the balance attack
     with Markov chains, and Gaži, Motaqy and Russell (ePrint 2024/1830, read for C3's regions),
     for a settlement error against depth rather than a region alone.
  2. *Port* one that gives it to the slot lottery with one weight per win, as B1 ported GRR. Gate
     it against J.2: it must lie above every attack at every depth.
  3. *If neither gives one,* derive it: a Markov chain over the split of the honest weight between
     two sides and the adversary's reserve that dominates every schedule within `Δ`, the analogue
     of GRR's alphabet for this weight. Research: weeks, and it may not close.
  Without a bound a variant gives a settlement level read from attacks, as the random-delay table
  is, and no smaller `k`.
- **J.4 — What `k` is, and what a smaller `k` breaks.**
  1. *The rules.* `k` in slots for both variants. `B_imm` is the latest block of the preferred
     ancestry made at least `k` slots ago, and the Online rule ignores forks that diverge before
     it. The Bootstrap rule compares weight, one per win, over its window after the divergence.
  2. *The epoch apart from `k`* (G2), so that the nonce's sub-windows, the inference's period and
     the recovery window keep their lengths at `k = 2160`. §6.1's uncle-window rule
     `W ≤ ⌊0.6k⌋` is read again.
  3. *The consumers* of §6.3, each against a `k` in slots.
  4. *Splits longer than `k`.* A split heals by itself only within `k` (B5). A smaller `k` also
     shortens the offline grace margin and the even-split horizon (§6.4). H.1's attestations
     cover a split below a third and operators the rest; both are restated at the new `k`.
- **J.5 — The nonce on the new fork choice.** B7's minima over the preferred ancestry. The fork law
  at the cut-off is redone for a weight race since the closest common ancestor, by
  `fork_bound.py`'s method; on a chain-shaped DAG it must equal the chain's law. Then `E[G_min]`
  under H.2's delay, at the sub-windows of the decoupled epoch.
- **J.6 — The inference.** Count blocks, one per win tag (E4), in place of occupied slots. Then
  replay G7's deflation. On the chain a deflated inference reads `Δ` as `Δ/(1 − α)`. A fork
  choice whose depth barely moves with `Δ` may lose little to it; J.2's plays at the raised
  rates measure how little.
- **J.7 — The synthesis.** For each variant, against 30 % and a third at `Δ = 10` s: `k` in slots
  and hours, from J.3's bound or, marked as such, from J.2's attacks; J.5's nonce and J.6's
  inference included; the splits of J.4; the cost: references per block and header bytes (E6),
  the ledger order of (b) (E4), and the fork choice's computation on the reference node. Beside
  them, today's `k = 2160` and B2's 1,510 blocks.
  Exit: `DAG.md` gains J's sections and `RATE.md` C3 the chain variant; the report's §9 and §12
  gain a row each; H7's verdict is read again. If H15 fails, the route gives at most a settlement
  level and `k` stays the chain's.

### Phase K — finality counted in slots

Phases A–J count `k` in blocks, as the specification does at `47a73cdc`: "Block depth finality.
Blocks deeper than `k` on any given chain are considered immutable", 2160 blocks
(`cryptarchia-v1-protocol.md`, Notation), and the Online rule rejects "any forks that diverge
further back than `k` blocks" (`fork-choice.md`). The owner's direction is to count it in slots,
as the owner reads Crypsinous, the design Cryptarchia follows. This phase reads every result again
under that assumption, on the branch `fast-finalization-slots`. `SLOTS.md` carries it.

What the sources count (K.0 quotes them, pinned):

- **Praos** defines persistence in blocks, "more than k blocks deep in the ledger", and liveness in
  slots, "after the passing of time corresponding to u slots" (§2.2).
- **Genesis** keeps a chain only "if (Ci forks from Cmax at most k blocks)" (`maxvalid-bg`), and
  a read outputs the local chain "chopping of k blocks" (§3.3).
- **Crypsinous** uses Genesis's rule: "we utilize the same chain selection rule in our protocol"
  (§6.2). Its ledger maintenance then updates the forward-secure encryption "for its time to be a
  least τ − k" (Appendix C.3, step 28), which reads `k` as slots.
- **The specification** defines beside `k` the slot security parameter `s = 3⌊k/f⌋`, "Sufficient
  slots such that `k` blocks have been produced with high probability", which times the epoch's
  phases.

The rules under the phase's reading, for a window of `K` slots:

- `B_imm` is the latest block of the local chain whose slot is at most `sl − K`, for the current
  slot `sl`. Commit, fork pruning and rule 8 of Block Header Validation read it as today.
- The Online rule ignores a fork that diverges before `B_imm`, so a rollback reaches at most `K`
  slots back.
- The Bootstrap rule compares a fork that diverges before `B_imm` by its density.
- A variant adds a density floor `φ`. Under its depth form `B_imm` moves to a block once the
  block is `K` slots old and `φ` blocks follow it: the later of a time and a depth. Under its
  density form `B_imm` moves to a block once the `K` slots after it hold `φ` blocks.

The candidates for `K` are `⌊k/f⌋` = 64,800 slots, 18 hours, the time 2,160 blocks take at the
full rate with no forks; `s = 3⌊k/f⌋` = 194,400 slots, 54 hours, the specification's own slot
parameter; and the least `K` that holds each `(α, ε, Δ)`. The epoch keeps its length,
`10⌊k/f⌋` slots at `k = 2160`, unless a step says otherwise (G2).

Three things change in kind:

- **A wait is a time.** A coalition that withholds no longer lengthens it. `K` must instead hold
  while the honest chain grows slowly: from the honest stake alone, and under the worst case one
  block per `Δ + 1/p_h` slots. A depth converts to a time only with the honest chain's growth
  over the wait, and the time must also cover that growth's lower tail.
- **Finality no longer needs blocks.** An eclipsed node finalizes the chain it is shown once `K`
  slots pass, whatever stake made that chain, its own blocks included. Counted in blocks, the fork
  needs `k` of them. A partition side finalizes after `K` slots whatever its share, where its
  horizon in blocks grows as its share falls (`MAPPING.md` §5).
- **Both branches of a fork have one divergence age.** A node holding both decides alike, so the
  Bootstrap rule's depth test can no longer split the nodes after a split (`SETTLEMENT.md` B5,
  rule 2).

Steps:

- **K.0 — The reading.** Quote the sources above. Record the rules and the candidates. Taken
  without the owner's answer: these rules, the floor measured as a variant, and the epoch at
  today's length.
- **K.1 — Settlement after a wait of `T` slots** (`slots.py`).
  1. *Random delay.* The private race with a premined lead, scored `T` slots after the target:
     B4's exact chance `P(n, t)` averaged over the canonical blocks the honest chain makes in the
     wait, in closed form at A1's growth; and the race played on the engine's timelines, scored
     at `T`. Gates: the chance at every depth is B4's; the closed form matches the race played on
     its model's slots; on a chain with one block every `c` slots a wait of `d·c` is the depth
     `d`, target by target.
  2. *The worst case, a bound.* Once the prefix up to the target's slot lies `D` deep, B2 bounds
     its displacement. After `T` slots it lies at least `N − W − 2` deep, `N` the honest
     renewals of the wait, honest wins at least `Δ` apart, each delivered within it (B5's law),
     and `W` the coalition's private lead at the target's slot, the stationary excess of its wins
     over those renewals, independent of `N`. So `ε(T) ≤ min_D [B2(D) + P(N − W − 2 < D)]`.
     Gates: `W`'s law matches the walk it stands for, sampled; the bound lies above the private
     race played on the worst case's own timelines, and falls with `T`.
  3. *The worst case, the attack.* B3's delay-scheduling attack on the slot lottery, scored `T`
     slots after the target.
  Each gate has a mutation that fails it. Table: `T` at `1e-6` and `1e-9` for `α` from 5 % to a
  third and `Δ` from 1 to 20 s, in hours, beside B2's depth on the worst-case clock.
- **K.2 — What a `K` holds.** The largest share each `K` holds at `1e-9`, as B5's table does
  for `k`, under random delay and the worst case: without grinding; with today's nonce, one and
  two ground nonces (B6's factors); with the nonce of §3.1 under H.2's delay (its factor); and
  after a deflated inference, the race at the raised rates with `Δ` fixed in slots (G7). For
  `K = ⌊k/f⌋` and `3⌊k/f⌋` at `k` of 2160, 1620, 1080, 432, 216 and 120.
- **K.3 — Splits and eclipses.**
  1. *Without a floor.* The self-healing horizon is `K` for every share. An eclipse fixes a fork
     after `K` slots and one block the honest chain lacks. Each against today's horizon in blocks.
  2. *The floor*, in its depth form and its density form. Size `φ` so that the honest chain a
     coalition of `α_max` withholds from reaches it within `K` at `ε`, under each delay model.
     What it costs: finality waits on a sparse chain, and how often a chain nobody withholds from
     waits. What it buys: an eclipse needs `φ` blocks of the eclipsed chain; under the density
     form a partition side below the floor stays provisional and rejoins when the split ends.
  3. *A floor as a quorum*, in the density form. The adversary signs on both sides of a
     partition, so two sides both reach the floor once `h_1 + α` and `h_2 + α` both do. The floor
     separates partitions only if it lies above the density of `(1 + α)/2` of the stake and below
     the lower tail of the honest chain a coalition of `α` withholds from: H.1's bound, with blocks
     as the votes. Find the least `K` at which one exists against 25 % and 30 %, under both delay
     models.
  4. *The Bootstrap rule, the offline grace period and recovery.* Rule 2 holds by construction.
     The density window, `T_offline` and the trigger's rules 3–8 read again against `K`; H.1's
     attestations and detector at the new `K`.
- **K.4 — The nonce and the epoch.** B7's sub-windows, H.2's span `W + margin` and the
  `4⌊k/f⌋` phase are in slots and keep their lengths with the epoch. A race lasts at most `K`
  slots, so B6's two-nonce coverage reads at `K`. A factor `F` per nonce is absorbed when
  `ε(K) ≤ ε/F`.
- **K.5 — Every other result, read again.** `MAPPING.md`: the rules, the consumers and the
  `k`-sized quantities with `K`. `RATE.md`: k-finality no longer shrinks with the block rate, and
  B2's bound in time at `f` of 1/20 and 1/15. `FURTHER.md`: G3's Blend settings, G4, G6 and G7 in
  time. `DESIGNS.md`: H.3's rules already read time. `CERTIFIED.md` and `DAG.md`: J.0 counted `k`
  in slots; what moves.
- **K.6 — The report.** `reports/finality/` on this branch, read under the slot assumption
  throughout.
- **K.7 — The wait in GRR's own model** (`waitbound.py`). K.1's worst case reads B2's bound at
  the depth a wait guarantees. B2 freezes its chain at the earliest moment the target could be
  `D` deep, and K.1 then also waits for the honest chain to grow `D` blocks at its slowest. The
  paper's Lemma 10 settles the prefix up to a slot once the margin stays negative, so the paper's
  chain bounds a wait directly, with a clock in place of the count.
  1. *The bound.* LCanalysis's chain, each phase costed by its wait for the next success,
     rounded up to a slot, and its span, at most `h·Δ` for `h` honest successes; the phase that
     covers the target weighted by its length. The chain freezes at the phase in which the wait
     passes. Gates: with LCanalysis's counts as costs the pass is `ub_curve`; the bound lies above
     its own chain played with the phases' true lengths in continuous time, and within a stated
     factor of it; it lies above the paper's attack, scored against a wait on the per-slot
     lottery. Checks: half-slot levels, twice the states, and the spans charged at the depth they
     add, which brackets what the `h·Δ` charge costs.
  2. *Read again.* K.1's worst-case table, K.2's shares, waits and factors absorbed, the floor at
     the least `K`, and K.5's block rates and Blend settings, under the bound.
  Table: `T` at `1e-6` and `1e-9` for `α` from 5 % to a third and `Δ` from 1 to 20 s, beside K.1's
  bound and the attack's estimate.
- **K.8 — A capped correction.** Both forms of the floor hold only until a sparse chain's
  inferred stake corrects. A cap `c` limits each epoch's correction: `D' ≥ (1 − c)·D`.
  1. *What it buys.* The days a side of share `σ`, cut off from the rest, stays below each form of
     the floor at `K = ⌊k/f⌋` and `3⌊k/f⌋`, for `c` from 2 % to 20 % and none, with the split
     aligned so that its corrections come earliest.
  2. *What it costs.* After a fall of the active stake to `r` with nobody withholding, the days
     finality stalls under the density form and what it takes under the depth form, with the fall
     aligned so that its corrections come latest; and the days the chain runs slow. G7 prices the
     deflation under each cap.
  Table: per cap, the protection for `σ` from 0.1 to 0.45 and the stall for `r` of 0.8, 0.6 and
  0.5.
- **K.9 — The floor counted as the stake inference counts.** The inference counts occupied
  slots, a slot holding a canonical block or an uncle the chain references, and recovers the
  honest stake at 0.998–1.001 under Blend with one uncle a block (`reports/tsi/README.md` §3.2a).
  The floor of K.3 counts canonical blocks, which lose the orphans. Read the floor on occupied
  slots: its size under random delay, where the honest chain reads its full occupancy; the
  protection it gives a cut-off side at its fastest, which counts the same either way; the stake
  below which finality stalls or slows; and the floor as a quorum under random delay with both
  sides counted alike. Under the worst case the count is at least the canonical one, pathwise, and
  an adversary that orphans a run of honest blocks leaves one countable uncle (TSI report §6.6), so
  no larger worst-case floor is read.

Exit: `SLOTS.md` carries K.0–K.9, each note gains a short section on what slots change, and the
report states every result in slots. H17–H24 get their verdicts.

### Phase L — certificates from the network (`NETWORK.md`)

The owner's direction (Q12): certificates signed by Blend's declared nodes. Phase D's voters are
anonymous seats the stake lottery draws, so every vote costs a Blend emission and the committee
needs a sampling margin. These signers are a public set that exists already, so a certificate needs
neither. The phase sizes what the certificates gain in time, and what their safety then rests on.

What the sources say (L.0 quotes them, at `logos-lips` `bd1ca2c8`):

- SDP keeps "a known and agreed-upon list of participants" for the protocols that need one, the
  Blend network first among them. A declaration carries an Ed25519 provider key and a service note
  that holds at least the minimum stake (`bedrock-service-declaration-protocol.md`; Mantle's Declare
  Operation).
- Mantle's ledger is transparent. A note backs at most one declaration per service, and service
  notes "can still participate in Proof of Stake" (Mantle, Service notes).
- The minimum stake is 0.001 % of the supply at launch, set for "a network size that is considered
  small", 1,000 nodes (`analysis-static-minimum-stake-estimation-for-service-declaration-protocol.md`).
  The block rewards measure security against a target of 30 % of the supply staked
  (`block-rewards.md`).
- Blend runs with at least 32 declared nodes. A node keeps its declaration by proving activity
  each epoch (`blend-protocol.md`).

The gadget L.0 records is Casper FFG's, on Cryptarchia's clock:

- A round starts every `R` slots. In round `r` each declared node votes a link from the latest
  justified checkpoint it holds to its checkpoint of round `r`: the latest block at least `L` slots
  old on its best chain among the chains that contain that justified checkpoint.
- A checkpoint is justified once links from one justified checkpoint to it carry `q` of the
  declared weight. It is finalized once the next round justifies a link from it.
- A node never votes twice in a round, and never casts a link that surrounds another of its own.
  Two conflicting finalized checkpoints then need `2q − 1` of the weight to have broken one of the
  two rules (Casper FFG's accountable safety).
- Two compositions with the slot rule. *Certificates only*: `B_imm` is the latest finalized
  checkpoint, and the slot rule moves it no more. *Fast path*: `B_imm` is the later of that
  checkpoint and the slot rule's block.

Steps:

- **L.0 — The reading.** Quote the sources above, and Casper FFG's accountable safety and plausible
  liveness, pinned. Record the gadget and both compositions. Taken without the owner's answer: one
  weight per declaration, as Blend counts its nodes; `q = 2/3`; both compositions measured side by
  side.
- **L.1 — What the declared set holds** (`netcert.py`). The coalition's share `a` of the declared
  weight, from its share `α` of the active stake, in two readings. The study's convention gives it
  its stake share of Blend's nodes, `a = α` (G6). The economics let it lock its stake in service
  notes of the minimum stake, one declaration each, against honest declarations that lock `L_h` in
  all. Safety with the honest votes split needs `a < 2q − 1`; liveness needs `u(1 − a) ≥ q` at an
  uptime `u` of the honest declarations. Read: the largest `α` held at the analysis' parameters;
  for `α` from 10 % to a third and `u` of 1, 0.95 and 0.9, the honest declared stake, the honest
  nodes at today's minimum stake, and the minimum stake for 1,000 honest nodes; the stake a
  violation puts at risk. Gates: the closed form against an enumeration of the coalition's
  allocations; D1b's frontier reproduced when the weight is a note's value; the analysis' 1,000 LGO
  reproduced. Each with a mutation.
- **L.2 — Time to finality on the engine** (`gadget.py`). The A1 configuration at the three Blends,
  every node a declared node of weight one, votes gossiped over the engine's peering graph without
  Blend. Rounds of 30, 60 and 600 slots; lags of 0, 10, 30 and 60 slots; the coalition's
  declarations withheld at `a` of 0, 0.25 and 0.3. Per canonical block, the time from its slot
  until the median and the 95th-percentile node hold it final; the share of rounds justified and
  finalized. Gates: justification counts links from one source to one target; finalization needs
  the next round's link; a block is final once a finalized checkpoint holds it; with no coalition
  and every view agreed, the mean time is `L + 3R/2` plus the votes' delivery. Each with a
  mutation.
- **L.3 — Partitions and eclipses.** The coalition signs on both sides. A side certifies once its
  honest declarations online and `a` reach `q`, so both sides can only when `a ≥ 2q − 1`. The share
  of the honest declared weight a side needs, by `a` and `u`. What each composition does on the
  side that stalls and when the split ends, and on an eclipsed node. Checked on the engine's
  partition mode (I.3). Read against the floor (`SLOTS.md` K.3, K.9) and H.1's attestations.
- **L.4 — The lag as a hedge.** With the honest views agreed, a coalition below `q` of the declared
  weight justifies nothing that honest nodes did not vote for. To finalize a conflicting checkpoint
  it must split the honest votes between two chains at the target's age. So the lag that keeps `ε`
  when the coalition holds between `2q − 1` and `q` of the declared weight is the chain's own
  settlement wait (`SLOTS.md` K.1, K.7). Read that lag, and what the gadget then gains over `K`.
- **L.5 — Cost.** Votes a second, bandwidth and verification on a Raspberry Pi 5, for 32 to 20,000
  declared nodes, from the Ed25519 and ML-DSA-44 verification times the repository measured on one
  (`reports/pqc`). The size of a certificate for a node that bootstraps.
- **L.6 — What else changes.** What reads finality once it takes minutes (`MAPPING.md` §7): the
  uncle window and pruning, the Bootstrap rule and the offline grace period, SDP's lag, the wallet.
  Which key signs; accountability, slashing a service note, and certificates forged with keys whose
  notes were released. What signers reveal (C1).
- **L.7 — The report.** `reports/finality/network.md`, and the study's report.

Exit: `NETWORK.md` carries L.0–L.6, and H25–H28 get their verdicts.

## 5. Measurement protocol

- **Time to finality** is measured from the target block's publication. Report p50 and p95: for
  settlement, the time to depth `d`; for certificates, the time until the median and the 95th
  percentile node holds one.
- **Failure rates** are per block for settlement and per round for certificates, with the
  yearly expectation stated beside each.
- **Engine runs** keep the TSI conventions: burn-in, replicates, standard errors, committed
  configs, fixed seeds.
- **Gates** must fail under mutation. Each gate records the mutation that failed it.
- **Sources** are pinned: specification commit, node commit, paper version.

## 6. What depends on `k` today

First draft of A2. Specifications at `logos-lips` `47a73cdc`; node at `logos-blockchain`
`4e0405d51`.

### 6.1 The rules that read `k`

| role | where | what `k` sets |
| --- | --- | --- |
| finality | `cryptarchia-v1-protocol.md`: Latest Immutable Block, Chain Maintenance, Commit, Fork Pruning, Block Header Validation rule 8 | `B_imm` is the `k`-deep block under the Online rule; forks diverging below it are pruned; a block at or below its height is rejected |
| Online fork choice | `fork-choice.md` (`maxvalid-mc`) | a fork deeper than `k` is ignored: `k` is the maximum rollback |
| Bootstrap fork choice | `fork-choice.md` (`maxvalid-bg`); `cryptarchia-v1-bootstr-sync.md` | a fork deeper than `k` is decided by density over `s_gen = ⌊k/4f⌋` slots (4.5 h). A node enters the Bootstrap rule only at startup: from genesis or a checkpoint, after more than `T_offline` = 20 min offline, or on the operator's flag. It stays in it for `T_boot` = 24 h |
| epoch | protocol, Epoch Schedule | `10⌊k/f⌋` slots in phases of 3, 3 and 4 `⌊k/f⌋` that wait for the snapshot, the nonce and the inferred stake to finalize; the inference counts the first `6⌊k/f⌋` slots |
| uncle window | protocol, note under Uncle Selection | `W ≤ ⌊0.6k⌋` keeps every uncle candidate inside the finalization window |

The offline grace period rests on the attacker being unable to grow a `k`-block fork within it.
Its margin `(k/f)/T_offline` is 54.0 at `k = 2160` and 3.0 at testnet's `k`.

### 6.2 What reads `k` through the epoch

Since sessions were removed (`blend-protocol.md` revision 1.1.0, 2026-06-22), these protocols run
on consensus epochs, so `k` times them:

- **SDP.** Services read the registry of `finalized_epoch = current_epoch - 2`. A declaration
  serves from epoch `e+2`; a withdrawal takes effect at `e+2`.
- **Blend.** The epoch is written as `E = 648000` rounds. Quotas, keys, nullifier caches and
  rewards are per epoch.
- **Proof of work.** `EXPECTED_BLOCKS_PER_EPOCH = 21_600`, commented `N_b = 10 k`.
- **Rewards.** Leader vouchers and service rewards settle at epoch boundaries.
- **Proof of leadership.** A note is eligible once it was in the note set at the start of the
  previous epoch.
- **Storage market.** The price is fixed within a timeframe, an epoch for permanent storage.

### 6.3 Who waits for finality

In the specifications:

- **Mantle.** A Zone crediting a deposit waits for finality or uses the atomic transfer. Channel
  parent references exist because "Cryptarchia has long finality times".
- **Cross-channel messaging** (template). Asynchronous messages wait for finality. "Channels can
  choose a specific probability threshold or wait for finality to achieve a 100% guarantee" —
  the place a settlement rule plugs in.
- **Architecture overview.** "Block finalizes after being buried by 2160 blocks".

In the node:

- **The LIB** is the `k`-th ancestor of the node's own tip under the Online rule, and frozen under
  the Bootstrap rule (`consensus/cryptarchia-engine/src/lib.rs`, `lib`).
- **Consumers.** The wallet prunes state at the LIB, and its leader-claim reservations expire
  after `k` immutable blocks. The SDP service stops tracking an activity once it is in the LIB
  ledger. The zone SDK and `logos_sql` finalize transactions, deposits and channel notes when the
  LIB advances. The HTTP and C APIs expose `lib-stream`, immutable-only block queries and `lib`
  in `info`. Storage and sync prune at the LIB.
- **Not consumers.** The mempool, proof-of-work claims, the leader and Blend membership work
  from the tip.
- **Two levels only.** The APIs expose the tip and the LIB. No confirmation depth exists.
- **`k` is a deployment setting**, not committed in genesis. No configuration sets 2160:
  testnet 0.3.0 uses 120 at `f = 1/30`, the embedded default 30 at `f = 1/20`.
- **The prolonged bootstrap period** defaults to 1 h in the node, against 24 h in the
  specification.

### 6.4 What each route changes

- **A smaller `k` (L2)** shrinks every epoch-timed rule of §6.2 unless the epoch is decoupled
  from `k`. At `k/10`: the epoch is 18 h and SDP's two-epoch lag 36 h; the inference's
  per-epoch noise grows by `√10` (TSI report, Appendix B); the per-epoch anonymity set of leader
  vouchers shrinks tenfold; the offline grace margin falls from 54.0 to 5.4; the even-split
  partition horizon from 35.7 h to 3.6 h. `W = 12` needs `k ≥ 20`.
- **Why the epoch phases are sized from `k`.** Praos sizes its windows from chain growth:
  `8k/f` slots add `k` blocks. That way the stake snapshot is `k` deep before the nonce is drawn,
  an honest block contributes to the nonce, and a quiet period lets the nonce settle (Theorem 11
  and its proof; epoch `24k/f`, nonce from its first `16k/f` slots). Cryptarchia's phases of 3, 3
  and 4 `⌊k/f⌋` play the same three roles; no document derives the 3. Under a faster finality
  notion, the snapshot and settling phases could shrink toward its finality time. The buffer
  that guarantees an honest nonce contribution is set by chain quality and grinding, not by
  finality.
- **A faster notion beside `k` (L1, L5, L6)** helps the direct consumers of §6.3 at once. The
  epoch-timed rules of §6.2 gain nothing unless rewritten against a finalized block, as SDP's
  `current_epoch - 2` could be. A certified block must never be reverted, so `B_imm` becomes at
  least the latest certified block in commit, pruning and rule 8. If certification comes sooner
  than the 360-slot uncle window, pruning at it would discard uncle candidates the inference
  still needs; D1 decouples the two.

## 7. Literature to reproduce before it is relied on

### 7.1 Read for this plan

- David, Gaži, Kiayias, Russell, "Ouroboros Praos: An Adaptively-Secure, Semi-synchronous
  Proof-of-Stake Blockchain", EUROCRYPT 2018; ePrint 2017/573, revision 2023-04-27 (SHA-1
  `373e7ba1`). Theorem 7 is the condition the specification quotes. Theorem 11 and Corollary 3
  cover the full protocol. Also used: the epoch rule `R = 24k/f` and its windows, and
  key-evolving signatures. §1.3, §6.4, D4.
- Badertscher, Gaži, Kiayias, Russell, Zikas, "Ouroboros Genesis: Composable Proof-of-Stake
  Blockchains with Dynamic Availability", CCS 2018; ePrint 2018/378, revision 2019-02-22 (SHA-1
  `81b39baf`, the archive's snapshot of 2024-12-28). Theorems 1 and 2, `maxvalid-mc` and
  `maxvalid-bg`, the nonce rule and the grinding remark of Appendix E. `DESIGNS.md` H.2.
- Wesolowski, "Efficient verifiable delay functions", ePrint 2018/623; the archive's PDF of
  2024-12-27 carries a build date of 2020-07-24 (SHA-1 `820180dc`), older than the revision of
  2022-10-26 the listing names. Assumptions 1 and 2, Example 2. `DESIGNS.md` H.2.
- Boneh, Bünz, Fisch, "A Survey of Two Verifiable Delay Functions", ePrint 2018/712, revision
  2020-01-05 (SHA-1 `8f8669bb`). Definitions 1 and 2, Theorem 2. `DESIGNS.md` H.2.
- Biasse, Jacobson, Silvester, "Security Estimates for Quadratic Field Based Cryptosystems",
  ACISP 2010; arXiv 1004.5512v1 (SHA-1 `8bca0421`). Table 4. `DESIGNS.md` H.2.
- Long, "Binary quadratic forms", Chia Network's class-group note (`Chia-Network/vdf-competition`,
  `classgroups.pdf`, SHA-1 `01f5c6d1`); Chia's Proof of Time page (docs.chia.net, read
  2026-10-09). `DESIGNS.md` H.2.
- Kerber, Kiayias, Kohlweiss, Zikas, "Ouroboros Crypsinous: Privacy-Preserving
  Proof-of-Stake", IEEE S&P 2019; ePrint 2018/1132, revision 2019-05-15 (SHA-1 `5a9913a9`). It
  proves no consensus theorem of its own. It treats leader-election frequency as the only
  leakage. Its coin evolution and per-slot key tree are what Cryptarchia leaves out, and its
  leadership circuit has 201,493 constraints. D1, D3–D5.
- Nakamoto, "Bitcoin: A Peer-to-Peer Electronic Cash System", §11. The attacker tables; gate.
- Grunspan, Pérez-Marco, "Double spend races", IJTAF 21(8), 2018; arXiv 1702.02867v3.
  `P(z) = I_{4pq}(z, 1/2)` and the corrected tables; gate.
- Dembo, Kannan, Tas, Tse, Viswanath, Wang, Zeitouni, "Everything is a Race and Nakamoto Always
  Wins", ACM CCS 2020; arXiv 2005.10484v4. Eq. (2), the private-attack threshold, is the true
  threshold for proof of work and for Ouroboros/Snow White proof of stake; gate.
- Gaži, Ren, Russell, "Practical Settlement Bounds for Longest-Chain Consensus", CRYPTO 2023;
  ePrint 2022/1571, revised 2025-05-02; code `github.com/renling/LCanalysis`. B1's method.
- Gaži, Motaqy, Russell, "A Tight Analysis of GHOST Consistency", ePrint 2024/1830, revision
  2026-09-11 (PDF SHA-1 `93a92b8a…`). GHOST's safe region is inferior to the longest-chain rule's;
  C3. Phase J quotes revision 2025-02-20 (archive snapshot `20260421005417`, SHA-1 `b1e3648d`),
  since the 2026-09-11 PDF could not be fetched again (`DAG.md` J.3).
- CIP-0140, "Ouroboros Peras – Faster Settlement", status Proposed. Committee `n = 900`, quorum
  `τ = 675`, round `U = 90` slots, boost `B = 15` blocks, cool-down `K = 780` rounds. Fast
  settlement against up to a quarter of the stake, Praos-like behaviour above it. Settlement
  known "after as little as two minutes". Voters drawn by VRF sortition among stake-pool
  operators; D1.
- Castro-Castilla, Pawlowski, Zhou, "Areon: Latency-Friendly and Resilient Multi-Proposer
  Consensus", arXiv 2511.23025v1, 2025-11-28; Phase E. Theorem 5.6 gives `(k, ε)`-finality once
  `k ≥ C1·w + C2·ln(1/ε)`, for absolute constants `C1`, `C2`, under honest stake above 1/2,
  `w ≥ Δ` and honest coverage `q > 0`. Depth is counted along references inside the window, and
  `T_final = k·τ_slot`. Its worked example fits `C1 ≈ 1.8` and `C2 ≈ 2.7` for illustration,
  giving `k ≈ 91` at `w = 30` and `ε = 1e-6`. The simulations (default: 7.5 s mean delay,
  `w = 30`, 30 % stake, 1,000 validators) compare against Praos at `f = 0.05`. Their finality
  proxy, the age after which the reorg probability falls below 1e-6, is "roughly 30–40 virtual
  blocks" at 30 % stake, a 0.5 s delay and `w = 30`, and about 60 at 45 % (§6.8). At the
  notebook's 30 slots a virtual block (E0), that is 900–1,200 slots at 30 % stake, 15–20 min at
  1 s slots, not the worked example's 91 s. The model makes
  four assumptions Phase E must lift:
  - Validators are identified: each block carries a validator, a VRF proof and a signature.
  - Privacy-preserving stake is "orthogonal to our fork-choice rule but interact[s] with
    eligibility and incentives".
  - Each block carries one payload.
  - The total order is an analysis device only.

### 7.2 To read before use

Identified by the literature survey run for this plan, which checked each identifier. Not yet
read here.

- **Settlement analysis.** Gaži, Kiayias, Russell, "Tight Consistency Bounds for Bitcoin", CCS
  2020. Guo, Ren, "Bitcoin's Latency–Security Analysis Made Simple", AFT 2022. Li, Guo, Ren,
  "Close Latency–Security Trade-off for the Nakamoto Consensus", AFT 2021. Kiffer, Rajaraman,
  shelat, "A Better Method to Analyze Blockchain Consistency", CCS 2018, which also treats GHOST
  and the balance attack (ePrint 2022/601, archive snapshot `20231202114621`, SHA-1 `32193802`;
  `DAG.md` J.3). Blum, Kiayias, Moore, Quader, Russell, "The Combinatorics of the
  Longest-Chain Rule: Linear Consistency for Proof-of-Stake Blockchains", SODA 2020.
- **Random delay.** Sankagiri, Gandlur, Hajek, "The Longest-Chain Protocol Under Random Delays",
  Stochastic Systems 2023. The model nearest Blend's random mixing delays; B1, B3.
- **Leader election.** Azouvi, Cappelletti, "Private Attacks in Longest Chain Proof-of-Stake
  Protocols with Single Secret Leader Elections", AFT 2021. What independent lotteries cost in
  settlement.
- **Finality overlays.** Badertscher, Coretti, Gaži, Kiayias, Russell, "Adaptively Secure Fast
  Settlement with Dynamic Participation and Self-Healing" (the Peras paper), SCN 2026. Neu, Tas,
  Tse, "Ebb-and-Flow Protocols", IEEE S&P 2021. FIP-0086, "Fast Finality in Filecoin (F3)", a
  deployed overlay whose finality halts while the chain continues. Pass, Shi, "Thunderella",
  EUROCRYPT 2018.
- **Votes under changing participation.** D'Amato, Neu, Tas, Tse, "Goldfish", FC 2024. Malkhi,
  Momose, Ren, "Towards Practical Sleepy BFT", CCS 2023. D'Amato, Saltini, Tran, Zanolini,
  TOB-SVD, ICDCS 2025. Their voters are identified, so C1 rules them out as specified.
- **Ruled out by C1 as specified** (voters identified, weights public). Casper FFG; Gasper;
  GRANDPA; Afgjort (SCN 2020); Mithril (CANS 2024). GRANDPA and Afgjort also bind block
  production to finality, against C2. Q12's signers are identified, so Casper FFG (Buterin,
  Griffith, arXiv 1710.09437) is Phase L's template, read and pinned in L.0.
- **Anonymous committees.** Ganesh, Orlandi, Tschudi, "Proof-of-Stake Protocols for
  Privacy-Aware Blockchains", EUROCRYPT 2019 (anonymous VRF). Baldimtsi, Madathil, Scafuro, Zhou,
  "Anonymous Lottery in the Proof-of-Stake Setting", CSF 2020. David, Lavagnino, Pagnin,
  Stankovski Wagner, "Tail-Hammer", SCN 2026 (committee statistics). Gilad, Hemo, Micali,
  Vlachos, Zeldovich, "Algorand: Scaling Byzantine Agreements for Cryptocurrencies", SOSP 2017
  (committee sizes against a 20 % adversary).
- **Leakage.** Kohlweiss, Madathil, Nayak, Scafuro, "On the Anonymity Guarantees of Anonymous
  Proof-of-Stake Protocols", IEEE S&P 2021; D5.
- **Structural.** Fitzi, Gaži, Kiayias, Russell, "Ledger Combiners for Fast Settlement", TCC
  2020. Bagaria, Kannan, Tse, Fanti, Viswanath, "Prism", CCS 2019. Schutza, Behrens, Duong, Aman,
  "Ouroboros Taktikos", BlockSys 2023; C4.
- **Impossibility.** Lewis-Pye, Roughgarden, "Resource Pools and the CAP Theorem", arXiv
  2006.10698. Pass, Shi, "The Sleepy Model of Consensus", ASIACRYPT 2017. They bound what any
  design can offer: a ledger live under unknown participation cannot also be safe under
  partition, so fast finality is either probabilistic or a finalized prefix that may lag.

### 7.3 What the survey did not find

- A finality committee that keeps voter stake private. The two privacy chains it found with
  committee finality, Dusk and Zcash Crosslink, publish voter stake. D1 has no template to
  copy.
- A proof-of-stake confirmation rule that conditions on observed forks, density or
  participation. B4 tests one in the engine: the rule that reads elapsed time.
- A documented derivation of `k = 2160`, for Cardano or for Cryptarchia.
