# Fork simulator: how many honest wins does the TSI count see?

`uncle_sim.py` estimates μ, the fraction of honest-won slots in a window that the
canonical chain's TSI count misses. That count is the distinct occupied slots of
the chain's blocks and their uncles. The multi-epoch certificate assumes μ ≤ 0.1
(hypothesis `hlo` of `final_bimm_ro_tsi4`). This simulation is the evidence for
that value.

The model has the following parts:
- Each slot has Poisson-many honest winners and an adversarial win with probability `a`.
- Honest proposers build on the longest chain they see.
- They include uncles by the specification's rule:
  - the uncle's parent is on the chain;
  - the uncle's parent is at most 360 slots old;
  - at most 4 uncles per block, oldest first.

Strategies:

| Strategy | What the adversary does |
|---|---|
| `S0` | nothing: random delays within Δ, random tie-breaking |
| `S1` | every honest block delayed by Δ, ties steered to keep forks balanced |
| `S2` | `S1`, plus a balance attack: it releases its blocks to re-tie a fork |

`python3 uncle_sim.py 40000` gives these values (3 seeds, β = 0.2, Δ = 11):

| | S0 | S1 | S2 |
|---|---|---|---|
| nominal rates | 0.7 % | 4.9 % | 6.1 % |
| fastest band member (+36 % rates) | 1.4 % | 8.2 % | 9.8 % |

The loss is from forks of depth two or more. The uncle rule requires an uncle's
parent to be on the chain, so such forks are never counted. The window length and
the number of uncles per block make no difference. A proof from chain growth alone
gives μ ≈ 0.25; that is the fully proven fallback.
