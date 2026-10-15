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
case at the mean, 278 and 1,521 at the bound, within eleven of a nonce no one chose. Before the cut-off it still decides, as blocks appear,
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
of minutes blinds nothing. Two changes make it work (note H.2). The contribution is bound to the
parent block, `ρ_LEAD := hash(NONCE_CONTRIB_V1 ‖ parent ‖ sl ‖ noteID ‖ sk)`, so that no
contribution exists before its block is built, which also replaces the two conditions above. And
the delay spans the sub-window with a margin, `T_a = W + 10` minutes on the adversary's hardware,
4.5 hours at `k = 2160`, so that every candidate's value arrives after the cut-off and the
adversary's choice is open only while its lead lasts the margin. The factor is then at most 1.08:
278 blocks under random delay and 1,521 under the worst case against a third, 165 and 895
against 30 %; `k = 1620` holds a third and `k = 1080` holds 30 % while the inferred stake is the
true stake. The bound is within the walk's model, and a lemma carries it into Praos's and
Genesis's theorems in place of their hash budget, under the sequentiality of the delay and a
random oracle for the hash of its output. Honest nodes compute the delay once an epoch, `R·T_a`
for a speed ratio `R`: 22 hours at `R = 5` and 45 at `R = 10` at `k = 2160`, 11 and 22 at
`k = 1080`, within the `4⌊k/f⌋` slots before the nonce is first used up to `R = 16`. The
documented ratio of Chia's class-group hardware to a CPU is 3 to 5. The function is Wesolowski's
over the class group of a prime discriminant derived from the input each epoch: a proof of one
group element, verified in milliseconds; a 1024-bit discriminant costs about `2^91` operations to
break and two hundred thousand machines of `10^18` operations a second to break within the delay,
and 2048 bits give `2^139` at no cost in time.

### 3.5 A beacon that is not a hash of the chain

A dedicated coin-tossing protocol, as in the first Ouroboros, or a threshold signature over the
epoch, removes the bias at its source. Each needs a set of identified parties that run a round
among themselves. Cryptarchia's leaders are anonymous, and the study's phase on certified
finality prices any round of anonymous votes through Blend at thousands of seats and finds no
committee at a third of the stake ([`README.md`](README.md), §8). A beacon of that kind is a
larger change than the nonce rule and does not fit the lottery as it stands.

### 3.6 The lottery's thresholds as a lever

Grinding is not the only way an adversary moves the schedule. The total-stake inference sets
every threshold from the occupied slots of the previous period and corrects in full each period.
An adversary that withholds every block for one period, 4.5 days at `k = 2160`, lowers the
inferred stake by its share and raises every threshold by `1/(1 − α)` for the next epoch, and the
deflation holds while it withholds. The catch-up ratio is unchanged and the depth moves all the
same: under the worst case the delay is fixed in slots while blocks come faster, so 10 s reads as
15 s against a third and the proven depth is 2,426 blocks, 1,248 against 30 %; under random delay
the orphan share rises with the rate and 276 blocks become 404. No `k` the study considered holds
its share after it. Choosing the raise level after seeing its own wins is worth under half a
percent of the adversary's wins. A cap on the correction of 5 % a period prices the deflation at
36 days of withholding and slows the inference's response to stake that leaves by the same
factor; a client can read the worst-case table at `Δ` divided by what remains of the inferred
stake (note G7).

## 4. The approaches side by side

Depth in blocks at `1e-9` with two ground nonces at `k = 2160`, against 30 % / a third; hours on
the honest chain's clock, 50.7 / 53.2 s a block under random delay and 52.6 / 54.8 s under the
worst case. "Bound" means a figure that holds for every strategy within the stated model;
"estimate" means a hindsight count of the adversary's decisions.

| approach | factor per nonce | random delay | worst case, 10 s | what it costs | status |
| --- | --- | --- | --- | --- | --- |
| no grinding | 1 | 165 / 276 (2.3 / 4.1 h) | 892 / 1,510 (13.0 / 23.0 h) | – | the reference |
| today's nonce, `2^64` evaluations | `10^11`–`10^14` | 504–574 / 1,171–1,245 (7.1–8.1 / 17.3–18.4 h) | 2,424–2,825 / 5,732–6,287 (35–41 / 87–96 h) | nothing | bound, both sides |
| today's nonce, `2^40` evaluations | set by the budget | 459–479 / 865–893 (6.5–6.7 / 12.8–13.2 h) | 2,246–2,436 / 4,437–4,617 (33–36 / 67–70 h) | nothing | bound, both sides |
| a delay on the hash chain (Phalanx) | `2^8`–`2^16` | 220–296 / 388–532 (3.1–4.2 / 5.7–7.9 h) | 1,142–1,539 / 2,048–2,812 (17–22 / 31–43 h) | 82 iterations of nine minutes an epoch, by hourly leaders | bound on the evaluations |
| the smallest contributions, choices at the cut-off | 1.03 / 1.06 | 165 / 277 | 894 / 1,518 | a hard fork, 25 sub-windows, two conditions on keys and notes | bound within the walk's model, 1.04 / 1.08 |
| the smallest contributions, decisions before the cut-off | 3.7–4.1 / 5.9–7.3 (random), 6.6–9.4 / 10.6–18.1 (worst) | 187–189 / 326–333 (2.6 / 4.8–4.9 h) | 1,057–1,088 / 1,859–1,939 (15.5–15.9 / 28.3–29.5 h) | the same | estimate |
| the smallest contributions with a delay that spans a sub-window | at most 1.04 / 1.08 | 165 / 278 (2.3 / 4.1 h) | 895 / 1,521 (13.1 / 23.1 h) | the contribution bound to the parent; about a day of sequential computation an epoch; a proof an epoch | bound within the walk's model; the lemma in Praos's model |
| the inference deflated, no grinding | 1 | 219 / 404 | 1,248 / 2,426 (13.9 / 27.0 h) | one period of the adversary's rewards | bound; a cap on the correction prices it |

## 5. What to take, and what to decide

The combination of §3.3 and §3.4 is the only approach that leaves the depth within a few blocks
of a nonce no one chose, as a bound rather than an estimate, and it is the one the study
recommends ([`README.md`](README.md), §1). Its price is a hard fork, a contribution bound to its
parent block, sub-windows of 54 hours in all, and a sequential computation of about a day each
epoch by whoever first needs the nonce, with a short proof for everyone else. Phalanx's delay
costs less computation and leaves a factor between `2^8` and `2^16`; today's nonce costs nothing
and leaves `k = 2160` unprovable at the specification's Blend against 30 % of the stake.

The decisions are the owner's:

- the sub-window count `m`, which sets the delay's span `W = ⌊6⌊k/f⌋/m⌋` against the choices a
  fork across a boundary adds, 25 at `k = 2160`;
- the margin beyond `W`, ten minutes, and the speed ratio `R` to design for, 5 by the documented
  hardware and 10 by CIP-0161's assumption, 16 at most within the phase;
- the discriminant's size, 1024 bits as Chia runs it or 2048 at no cost in time;
- whether to cap the inference's correction, and at what rate, which the deflation of §3.6 makes
  a question for the lottery whatever the nonce.

What stays open is the sequentiality assumption itself, which no proof removes, and the formal
write-up of the lemma, which the design note states and proves in Praos's resettable model.
