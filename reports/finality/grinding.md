# The epoch nonce, the lottery and the length of finality

A review of the approaches to grinding in Cryptarchia's slot lottery and of what each leaves of
the depth a block needs before it is final. It reads the measurements of the finality study
([`README.md`](README.md), §3.1, §5, §12 and §13; `tools/simulators/finality/`, notes B6, B7, G1,
G7, H.2) and the papers the study pinned. Figures are at a failure probability of `1e-9` per
block, against an adversary holding 30 % or a third of the stake, under two delay models: random
Blend delays on the specification's Blend, where the figure is the private attack's, and a worst
case in which the adversary delivers every honest block as late as a bound `Δ = 10` s allows,
where the figure is proven against every attack.

## 1. The problem

Cryptarchia's lottery is Praos's. A holder of stake wins a slot when its verifiable random
function, evaluated on the slot and the epoch's nonce, falls below a threshold set by its share.
The nonce of the next epoch is the hash chain of the contributions `ρ_LEAD` of the blocks up to a
cut-off slot, `6⌊k/f⌋` into the epoch (`cryptarchia-v1-protocol.md`, Epoch Nonce). An adversary
that withholds the blocks it wins chooses which of them end the chain at the cut-off, and so
chooses among several nonces, each a different leader schedule for the next epoch. Praos names
the effect: "the possibility of adversarial grinding in Ouroboros Praos is also present in
previous work that derives randomness by hashing [Mic16, DPS19], as opposed to a dedicated
coin-tossing protocol as in [KRDO17]", and bounds it by the hashes the adversary can afford
(ePrint 2017/573, revision 2023-04-27, §1; the references are Algorand, Snow White and the first
Ouroboros).

What grinding costs finality is a factor. If an attack's chance against one schedule must be at
most `ε`, and the adversary picks the schedule among `G` it can reach and evaluate, the chance
against one schedule must fall to `ε/G`, and the depth that holds `ε` is the depth that holds
`ε/G`. An attack whose race crosses an epoch's end meets two nonces, and the factor is the
product. The study writes the factor per nonce as `R` and reads the depth at `ε/R²`; a factor of
2 against a third under the worst case adds 34–104 blocks to 1,510, a factor of `10^14` adds
4,200–4,800.

## 2. What today's nonce leaves

The adversary's choices at a cut-off are counted exactly from a random walk of its lead, and two
bounds bracket the factor (note B6). With `2^64` evaluations an epoch, the row that stands for
unlimited hardware, two ground nonces turn 276 blocks into 1,171–1,245 against a third under
random delay and 1,510 into 5,732–6,287 under the worst case; against 30 %, 165 into 504–574 and
892 into 2,424–2,825. `k = 2160` can then no longer be proven against 30 % at `Δ = 10` s, nor
against a third from `2^8` evaluations. The hash budget sets the factor from 30 % of the stake:
one evaluation costs one hash per slot of the attack window, `1.6·10^24` hashes an epoch at `2^64`.

## 3. The approaches

### 3.1 Bound the evaluations by the hash budget

This is Praos's own treatment. The factor is the number of random-oracle queries the adversary
can pose while the nonce's inputs are open, `q` per party per slot, and Corollary 3 carries it as
`log tkq`. It is a bound, not a design: the budget is the adversary's to set, and at `2^40` an
epoch, `9.6·10^16` hashes, the depths against 30 % are 459–479 and 2,246–2,436. Nothing in the
protocol changes, and nothing in the protocol limits the factor.

### 3.2 Cap the evaluations with a delay on the hash chain

Ouroboros Phalanx (CIP-0161) keeps the hash chain and derives the nonce from it through a
verifiable delay function, 82 independent iterations of about nine minutes each on a CPU,
computed by the first leaders of hour-long intervals. Every candidate nonce costs the adversary
all 82, on hardware the CIP takes to be ten times faster: one candidate in 72 minutes on one
machine, one every 53 seconds on 82. The cap binds how many nonces the adversary evaluates, not
how many it can choose between, and a candidate's hash-chain value is known the moment its last
block exists, hours before the cut-off, so the adversary evaluates throughout the window: about
3,700 candidates on 82 machines over the 54-hour window of `k = 1080`. The cap lies between the
`2^8` and `2^16` rows: 2,048–2,812 blocks against a third under the worst case, 388–532 under
random delay. A cap of two nonces would leave 1,544–1,614.

### 3.3 Shrink the nonces the adversary can reach

The study's rule takes the nonce from the smallest contribution of each of `m` sub-windows of
the window before the cut-off, `η_e = hash(η_(e−1) ‖ μ_1 ‖ … ‖ μ_m)`, 25 sub-windows at
`k = 2160` (note B7). A withheld block changes the nonce only if it holds a sub-window's minimum.
At the cut-off the adversary reaches 1.06 nonces on average against a third, and at most 1.08 as
a bound from the walk of B6 (note H.2): 277 blocks under random delay and 1,518 under the worst
case at the mean, 278 and 1,521 at the bound, within eleven of a nonce no one chose at
`k = 2160`. Before the cut-off it still decides, as blocks appear,
whether to publish each of its own and whether to remove an honest one that holds a minimum, by
racing it or, under the worst case, by delivering a rival within `Δ`; counted in hindsight those
decisions leave an estimated 5.9–7.3 per nonce against a third under random delay and 10.6–18.1
under the worst case, 326–333 and 1,859–1,939 blocks. The rule needs the contribution bound to
the epoch nonce, so that no key can be chosen for small contributions, notes frozen one epoch
earlier, so that no adversary that holds every minimum predicts the next nonce before its keys
are fixed, and sub-windows of at least 54 hours in all. It is a hard fork.

### 3.4 Blind the decisions with a delay that spans a sub-window

A delay makes a decision blind if the adversary cannot see the nonce each outcome gives before it
must act. The rule's candidates can be formed from the start of the last sub-window, since the
earlier minima are fixed by then and the adversary knows its own contributions ahead, so a delay
of minutes blinds nothing. Two changes make it work (note H.2). The delay spans the sub-window
with a margin, `T_a = W + 10` minutes on the adversary's hardware, 4.5 hours at `k = 2160`, so that
no candidate's value arrives sooner than ten minutes after the cut-off, and a value counts only if
the adversary can still publish a fork that reaches it when it arrives. And the minima are taken
over a contribution bound to the parent's contribution, `c(b) = hash(NONCE_CONTRIB_V2 ‖ c(parent) ‖
ρ_LEAD(b))`, which every node derives from public values while `ρ_LEAD` stays the win tag it is
today, so that a value of the adversary's branch exists only once the block the branch forks from
does, which also replaces the two conditions above. Bound to the parent block itself, a branch's
later blocks take as many contributions as body variants the adversary computes; bound to the
parent's own tag, a block on the adversary's own previous win has a value known ahead, and the
factor is worse than with no binding. With the chained contribution the factor against a third
under the worst case at `k = 2160` is 1.009, sampled, almost all of it the chance that the
adversary sees the honest default's value while a branch it has not seen can still replace it.
As a bound it is the walk's 1.08 on the choices at the cut-off, plus 0.016 for that switch, plus
`1.6·10^-6` for each delay evaluator the adversary runs, for the branches that keep up with the
honest chain over the delay's span. The depths are 892 / 1,511 under the worst case sampled and
895 / 1,523 at the bounds, against 30 % / a third, within thirteen blocks of a nonce no one chose
at `k = 2160`; `k = 1620` holds a third against up to 7,800 evaluators and `k = 1080` holds 30 %
against up to 450,000, while the inferred stake is the true stake. A lemma carries the count into
Praos's and Genesis's theorems in place of their hash budget, under the sequentiality of the delay
and a random oracle for the hash of its output. Honest nodes compute the delay once an epoch,
`R·T_a` for a speed ratio `R`: 22 hours at `R = 5` and 45 at `R = 10` at `k = 2160`, 11 and 22 at
`k = 1080`, and the `4⌊k/f⌋` slots before the nonce is first used hold a ratio of 15 to 16 counting
the squarings. The documented ratio of Chia's class-group hardware to a CPU is 3 to 5. The function
is Wesolowski's over the class group of a prime discriminant derived from each candidate: a proof
of one group element, verified in 2–4 ms; a 1024-bit discriminant costs `2^91.4` operations for the
discrete logarithm by Biasse, Jacobson and Silvester's table and `2^101.4` by their stated method,
and 2048 bits `2^139.4` and `2^149.4`, at no cost in time if the speed ratio holds there.

### 3.5 A beacon that is not a hash of the chain

A dedicated coin-tossing protocol, as in the first Ouroboros, or a threshold signature over the
epoch, removes the bias at its source. Each needs a set of identified parties that run a round
among themselves. Cryptarchia's leaders are anonymous, and the study's reading of certified
finality prices any round of anonymous votes through Blend at thousands of seats and finds no
committee at a third of the stake ([`README.md`](README.md), §8). A beacon of that kind is a
larger change than the nonce rule and does not fit the lottery as it stands.

### 3.6 The lottery's thresholds as a lever

Grinding is not the only way an adversary moves the schedule. The total-stake inference sets
every threshold from the occupied slots of the previous period and corrects in full each period.
An adversary that withholds every block for one period, 4.5 days at `k = 2160`, lowers the
inferred stake by its share and raises every threshold by `1/(1 − α)` for the next epoch, and the
deflation holds while it withholds. The catch-up ratio is unchanged. Under the worst case the depth
moves all the same: the delay is fixed in slots while blocks come faster, so 10 s reads as 15 s
against a third and the proven depth is 2,426 blocks, 1,248 against 30 %. No `k` the study
considered holds its share after it. Under random delay the report's convention stays where it
is, 165 / 276, and comes sooner. The convention reads a chain on which every node produces, and the
deflation turns the chain the adversary withholds from into one: on the engine the private race
needs 189 / 334 blocks after it, where at the true thresholds it needs 158 / 257, within the
convention (note G7).
Choosing the raise level after seeing its own wins is worth under half a percent of the
adversary's wins. A cap on the correction of 5 % a period prices the deflation at 36 days of
withholding and slows the inference's response to stake that leaves by the same factor; a client
can read the worst-case table at `Δ` divided by what remains of the inferred stake (note G7).

## 4. The approaches side by side

Depth in blocks at `1e-9` with two ground nonces at `k = 2160`, against 30 % / a third; hours on
the honest chain's clock, 50.7 / 53.2 s a block under random delay and 52.6 / 54.7 s under the
worst case. "Bound" means a figure that holds for every strategy within the stated model;
"estimate" means a hindsight count of the adversary's decisions.

| approach | factor per nonce | random delay | worst case, 10 s | what it costs | status |
| --- | --- | --- | --- | --- | --- |
| no grinding | 1 | 165 / 276 (2.3 / 4.1 h) | 892 / 1,510 (13.0 / 23.0 h) | – | the reference |
| today's nonce, `2^64` evaluations | `10^11`–`10^14` | 504–574 / 1,171–1,245 (7.1–8.1 / 17.3–18.4 h) | 2,424–2,825 / 5,732–6,287 (35–41 / 87–96 h) | nothing | bound, both sides |
| today's nonce, `2^40` evaluations | set by the budget | 459–479 / 865–893 (6.5–6.7 / 12.8–13.2 h) | 2,246–2,436 / 4,437–4,617 (33–36 / 67–70 h) | nothing | bound, both sides |
| a delay on the hash chain (Phalanx) | `2^8`–`2^16` | 220–296 / 388–532 (3.1–4.2 / 5.7–7.9 h) | 1,142–1,539 / 2,048–2,812 (17–23 / 31–43 h) | 82 iterations of nine minutes an epoch, by hourly leaders | bound on the evaluations |
| the smallest contributions, choices at the cut-off | 1.03 / 1.06 | 165 / 277 | 894 / 1,518 | a hard fork, 25 sub-windows, two conditions on keys and notes | bound within the walk's model, 1.04 / 1.08 |
| the smallest contributions, decisions before the cut-off | 3.7–4.1 / 5.9–7.3 (random), 6.6–9.4 / 10.6–18.1 (worst) | 187–189 / 326–333 (2.6–2.7 / 4.8–4.9 h) | 1,057–1,088 / 1,859–1,939 (15.5–15.9 / 28.3–29.5 h) | the same | estimate |
| the smallest contributions with a delay that spans a sub-window | 1.002–1.003 / 1.009–1.011 sampled; at most 1.05 / 1.10 plus a term per delay evaluator | 165 / 276–278 (2.3 / 4.1 h) | 892–895 / 1,511–1,523 (13.0–13.1 / 23.0–23.2 h) | the contribution bound to the parent's contribution; about a day of sequential computation an epoch; a proof an epoch | sampled, and bound within the walk's model for a stated number of delay evaluators; the lemma in Praos's model |
| the inference deflated, no grinding | 1 | 165 / 276 in the convention (1.6 / 2.7 h at 35.5 s a block); 189 / 334 on the engine's race | 1,248 / 2,426 (13.9 / 27.0 h at 40 s a block) | one period of the adversary's rewards | bound; a cap on the correction prices it |

## 5. What to take, and what to decide

The combination of §3.3 and §3.4 is the only approach that leaves the depth within a few blocks
of a nonce no one chose, as a bound rather than an estimate, and it is the one the study
recommends ([`README.md`](README.md), §1). Its price is a hard fork, a contribution bound to its
parent's contribution, sub-windows of 54 hours in all, and a sequential computation of about a day
each epoch by whoever first needs the nonce, with a short proof for everyone else. Phalanx's delay
costs less computation and leaves a factor between `2^8` and `2^16`; today's nonce costs nothing
and leaves `k = 2160` unprovable at the specification's Blend against 30 % of the stake.

Four parameters remain to be chosen:

- the sub-window count `m`, which sets the delay's span `W = ⌊6⌊k/f⌋/m⌋` against the choices a
  fork across a boundary adds, 25 at `k = 2160`;
- the margin beyond `W`, ten minutes, and the speed ratio `R` to design for, 5 by the documented
  hardware and 10 by CIP-0161's assumption, 15 to 16 at most within the phase counting the
  squarings;
- the discriminant's size, 1024 bits as Chia runs it or 2048 at no cost in time if the speed ratio
  holds there;
- whether to cap the inference's correction, and at what rate, which the deflation of §3.6 makes
  a question for the lottery whatever the nonce.

What stays open is the sequentiality assumption itself, which no proof removes; the number of
delay evaluators an adversary runs, which the bound grows with; and the formal write-up of the
lemma, which the design note states and proves in Praos's resettable model.

## 6. Counted in slots

Counted in slots, a block is final once `K` slots have passed since its slot (`SLOTS.md` K.0). A
factor `F` per nonce is then absorbed where the chance against a wait of `K` slots is at most
`ε/F`. The waits that hold `ε = 1e-9`, against 30 % / a third (`SLOTS.md` K.2):

| approach | random delay, the specification's Blend | worst case, 10 s |
| --- | --- | --- |
| no grinding | 3.1 / 5.1 h | 15.5 / 26.3 h |
| today's nonce, one ground nonce | 7.6–7.8 / 13.9–14.3 h | 35.7–36.8 / 67.4–69.4 h |
| today's nonce, two ground nonces | 9.5–10.8 / 21.7–23.1 h | 42.0–49.0 / 99.5–109.1 h |
| the smallest contributions with a delay that spans a sub-window, two nonces at H.2's bound | 3.1 / 5.1 h | 15.6 / 26.6 h |
| the inference deflated, no grinding | 2.2 / 3.4 h in the convention's model, 2.5 / 4.2 h at the engine's growth | 15.9 / 29.8 h |

- **With today's nonce no `K` up to 54 hours holds a third at 10 s.** The specification's slot
  parameter, `s = 3⌊k/f⌋`, holds 30 % with two ground nonces.
- **With the delayed nonce a third needs 26.6 hours,** 0.3 more than a nonce that is not ground.
- **Every target stays inside the bound while `K` is at most `4⌊k/f⌋` slots.** A race lasts at
  most `K`, so a target meets two ground nonces only within `K` slots of its epoch's end, and none
  meets a nonce its own private chain set (`SLOTS.md` K.4). Counted in blocks, 13 % of targets lay
  outside the bound.
