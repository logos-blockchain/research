# EmPoWering — the on-ramp from proof of work into proof of stake

*Three simulators, three candidate designs, and the reports they produce. Simulators:
[`empowering/tokenomics`](../../tools/simulators/empowering/tokenomics),
[`empowering/strategies`](../../tools/simulators/empowering/strategies) and
[`empowering/denovo`](../../tools/simulators/empowering/denovo), with the proof-of-work cost
estimator at [`benchmarks/powcost`](../../tools/benchmarks/powcost) and the Poseidon2
measurements at [`benchmarks/empowering`](../../tools/benchmarks/empowering). Money is in
**LGO** unless a figure says lepta, and one LGO is 10⁹ lepta. Time is in **epochs**; one epoch
is 21,600 blocks, and 48.7 epochs make a year. Every chain simulated here is honest and
fork-free unless the document says otherwise.*

The mechanism exists to answer one question: **can somebody who owns no tokens work their way
in?** Mine, get paid, save until you can post the 1,000-LGO bond that lets you run a paid
service, and so become part of what secures the network. These reports measure whether the
mechanism does that, at what cost, and for how many people — and, because the answer for the
current design turned out to be *fewer than intended and only for a while*, they also measure
a redesign against the same brief.

## Start here

| if you have… | read |
| --- | --- |
| ten minutes, and want the decision | [`denovo/SUMMARY.md`](denovo/SUMMARY.md) — what the designs are, what was found, what to do |
| no appetite for arithmetic at all | [`denovo/design-comparison.md`](denovo/design-comparison.md) §0, the mechanism in everyday terms |
| a participant's question — *what does joining pay?* | [`strategies/strategies-report.md`](strategies/strategies-report.md) |
| an implementation to write | [`MODEL.md`](../../tools/simulators/empowering/denovo/MODEL.md), the normative rules |
| a specific number, and want to see it derived | [`tokenomics/tokenomics-model.md`](tokenomics/tokenomics-model.md) — the most technical document here, and **not** the place to start |

## Headline

**The current design onboards fewer nodes than intended, and the window closes.** Its outflow
is fixed by the pool rather than by demand, so arrivals only thin everyone's share: elevation
lands at **5,690** nodes against a 50,000 ceiling if bonded miners keep mining, **25,935** if
they retire — a 4.5× swing on a behaviour the specification never addresses. Under a Poisson
arrival process the on-ramp has a *best* adoption speed rather than a fastest one, and at
fifty arrivals an epoch the last cohort with runway to the bond is seated at **epoch 83**.

**For a participant, the ordering is not close.** A node providing the privacy service earns
**5.68×** a plain stakeholder; mining alone earns 0.31× — weakest not because it is expensive
but because it pays little.

**The redesign fixes the structural faults and concedes a different one.** Stating the design
as *pool, nodes, years* delivers **24,674 bonds against a 25,000 intent** when bonded miners
retire, and **7,643** when each one re-decides for itself and keeps mining — which is what
they do at the reference token price. It absorbs a ×100 spike the current design cannot. Its
cost was a whale exposure of 55% at the worst moment, which the `de novo*` variant closes to
**9%**, flat in the attacker's size, for one added parameter.

The recommendation, and the one blocking defect found on review, are in
[`denovo/SUMMARY.md`](denovo/SUMMARY.md) §4.

## Contents

**The decision**

- [`denovo/SUMMARY.md`](denovo/SUMMARY.md) — the three designs, the findings, and the recommendation. Written to be read straight through.
- [`denovo/design-comparison.md`](denovo/design-comparison.md) — current against redesign, number for number, scored on the same brief. §0 explains the mechanism with no arithmetic.

**The measurements**

- [`strategies/strategies-report.md`](strategies/strategies-report.md) — five ways to take part, simulated on one chain with paired draws: what each earns, how many nodes the pool can elevate, and (§7) what a stochastic arrival process does to the window.
- [`denovo/denovo-report.md`](denovo/denovo-report.md) — the redesign's own reference run, its spike behaviour, and its requirements validated one by one.
- [`denovo/adversarial-analysis.md`](denovo/adversarial-analysis.md) — both designs attacked: whales, withholding, sybils, flooding.
- [`tokenomics/tokenomics-model.md`](tokenomics/tokenomics-model.md) — the closed forms behind the current design: reward pool, both difficulty controllers, the claim fee, endowment sizing, bootstrap security. Grew by addendum rather than rewrite; **read its §0.5 first**, which says which of the body still stands.

**The proof-of-work function**

- [`Acceleration-Resistant-PoW-Survey.md`](Acceleration-Resistant-PoW-Survey.md) — what makes a puzzle resistant to acceleration, and the candidates.
- [`Equi-X/`](Equi-X/) — the Equi-X analysis and benchmark harness.

**For upstream**

- [`UPSTREAM-PENDING.md`](UPSTREAM-PENDING.md) — prepared answers to the questions these reports raise against the specification tree.

## Re-running any number here

Every figure and every quoted number is reproducible, and each report's numbers are gated
against the simulator that produces them rather than transcribed:

```
cd tools/simulators/empowering/tokenomics && make all verify notation report-numbers plots
cd tools/simulators/empowering/strategies && PYTHONPATH=src python3 -m empowering_sim.validate
                                          && PYTHONPATH=src python3 -m empowering_sim.report_numbers
cd tools/simulators/empowering/denovo     && make validate report-numbers study plots web
```

`validate` checks the model against its closed forms; `report-numbers` checks the *document*
against the model, so a table that drifts from the run behind it fails rather than surviving
until a reader notices. `make check LIPS=<path-to-logos-lips>` in the tokenomics simulator
compares the config against the specification tree.
