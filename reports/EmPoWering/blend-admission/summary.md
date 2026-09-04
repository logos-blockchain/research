# Blend load-driven admission — simulation results

## 1. The door under flood
- Escalation floor→ceiling in 60 rounds; decay back in 150 rounds after the flood.
- During the flood the attacker takes 96% of the acceptance rate; 75% of honest offers are refused at the rate cap (retried next rounds).
- Peak CPU 37% of one Pi 5 core (headers + token checks) — the door holds the verification budget.
## 1b. Adaptive attacker (give-up 800)
- No sawtooth: the price settles at 750 — the deadband holds the one value just below the give-up, so the generic controller's oscillation (research run 4) does not occur under the specified integer rule.
- The equilibrium is a stable, priced occupation instead: attack duty 98% of the window, 97% of the acceptance rate, 48/1800 rounds above the upper deadband. The floor on that occupation is the work itself: just-below-trip pressure costs ~57 fastest cores at any price the attacker settles at.
## 2. Grace window

| device | d | mean solve | P(stranded), worst case |
|---|---|---|---|
| Pi 5, 4 cores | 300 | 0.72 s | 4.5e-37 |
| Pi 5, 4 cores | 1000 | 2.36 s | 8.8e-12 |
| Pi 5, 1 core | 300 | 2.87 s | 8.2e-10 |
| Pi 5, 1 core | 1000 | 9.43 s | 0.0017 |

- Through the flood trace: 0/3510 four-core and 0/3606 single-core solvers stranded (price steps are what strands, not the tail alone).
## 3. Median robustness
- Below half the reporters, the per-epoch multiplier stays within the x2 clamp and re-anchors to BASE*4/median: at 30% colluders the mean multiplier is 0.74 (tighten) / 1.39 (loosen) at N=100.
- The zero-median branch, uncapped, doubles per epoch and reaches free admission in 19 epochs from BASE — which is why the rule caps the loosening at the level-1 fixed point: under a sustained median of 0 it now settles at 4*BASE (4x BASE) and stays.
- Sixteen levels leave 89% of 100 heterogeneous reporters sharing a level — the targeting oracle sees buckets, not a ranking.
## 4. Edge leader

| d | pre-mine duty (3 tokens / rotation) | P(3 solves > 15 s) | P(> 30 s) |
|---|---|---|---|
| 300 | 0.36% | 0.00% | 0.000% |
| 1000 | 1.18% | 4.75% | 0.028% |

- Pre-mining to the ceiling costs ~1.2% of a Pi 5 and removes the slot-time risk; solving at slot time at the ceiling misses the 15 s traversal budget 4.8% of the time.
