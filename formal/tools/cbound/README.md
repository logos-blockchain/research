# cbound

A numeric upper bound on P(not `GoodL`), the lottery's good event for settlement: phase law, stationary reach, fine-phase margin DP, ever-fail, Chernoff phase bound, and the `curve` and `curve_block` sweeps over the settlement window. It is a Rust port of `reports/fast-finality/model/cryptarchia_bound.py` and `cryptarchia_params.run`, restored here from commit `56a5f93` to measure how far the certificates' bound is from what a richer witness could give.

## Robust over a band (`band.py`)

A config may give the slot law explicitly: fields 9-11 are `h, p1, a`, P(some honest leader), P(exactly one honest leader) and P(adversary wins), the honest part independent of the adversary's as in the Lean model (`prodLaw`, `Prob/Worst.lean`). `band.py BETA DELTA K DEPTH N [MU] [Δ]` builds a certificate's band family exactly as `tools/certgen` does (`certE.tband`, `epoch_members`, at depth `k`), runs `cbound` at the four vertices of every member's honest polytope with the adversary at `amax`, and keeps the worst. It adds the stake estimate's band term `Ne · bandEps` and replaces the fixed 1e-12 window term by the one at depth `k`. A fixed vertex is weaker than the Lean model's adversary, which picks the honest law slot by slot, so the result is a lower estimate of the robust value: a floor for any witness under the current proof structure, not a bound.

## A table witness for the failed-check term (`lean_rate.py`, `proto.py`, `lp.py`)

The certificates bound a failed check (a margin not cold `J` phases after an anchor) with a two-term exponential potential, contracting by `lpi` per phase inside an epoch. `lean_rate.py` computes the true decay rate under Lean's phases and `step` for a fixed slot law. `proto.py` is the check a table potential `V(ρ, μ)` would have to pass in Lean, state by state: the phase bounded through the per-slot automaton of `Prob/Auto.lean` (`slot4`, the `min(A, 2)` counter with a factor `x^A`, the least `AutoSol`) and the crossing credited through the pattern bound (`slo · elo^Δ`). `lp.py` finds the best such table on a box by linear programming: for a fixed `λ` the check is linear in `V`, the automaton tables and the terminal entries, each `slot4` the largest of 8 linear forms.

At the k = 1000 certificate's band (β = 0.2, δ = 0.07), on a 16 × 32 box:

| | in-epoch contraction (member 0, binding) |
|---|---|
| the certificate's potential | 0.99774 |
| table witness, existing automaton, `x = 2.6` | 0.99676 |
| true rate, fixed law at the worst vertex | 0.99672 |

The per-slot adversary and `slot4`'s marginal bounds cost nothing measurable; the automaton's factor `x` matters (`x = 1.9`: 0.99722). With 0.99676 the generator's rules give a settlement bound of 4.2e-5 against 1.2e-2.

```
cargo build --release
echo '[[0.0333333333, 0.33, 11, 30, 648000, 1]]' | ./target/release/cbound > out.json
python3 band.py 0.2 0.07 32 1000 5184000      # robust over the k = 1000 certificate's band
```

Input is a JSON list of `[f, beta, Delta, cap_hours, N, fine, p_late?, rule?, wslots?, h?, p1?, a?]`. Output is a JSON list with keys `f, beta, Delta, cap, N, fine, p_late, rule, wslots, law, K, mean_phase, curve, curve_block`; `curve` lists `[window, bound, J]` per settlement window of `window` slots. Configs run in parallel, and each margin-DP step is also split across threads. `CB_DEBUG=1` prints stage timings. `CB_DUMP=path` writes `q`, `ev` and `V` of the last config.

## Rigor and performance notes

- **Rounding.** Every transition probability is inflated by 1e-9 relative (`INFL`), more than the rounding error in computing it. The DP adds and multiplies only non-negative numbers, so the computed state masses and failure probabilities can only be too large. After the DP, each `q_J` and `ev_J` is multiplied by the worst-case round-to-nearest factor `(1 - u)^-(J * steps * (terms + 1))`, which is about 1 + 1e-7. Together these make the outputs upper bounds whatever the floating-point rounding. They move results by at most 7e-6 relative.
- **Margin depth `M`** (`CB_M`, default 200). Clipping the margin at `-M` is pessimistic, so any `M` is sound. Against `M = 300` the default changes no result by more than 3e-8, and it is about 30 % faster.
- **Grouped cold step.** Cold transitions with the same shift `A - H` are applied in one pass, except for rows below the reach floor. The results are identical; `CB_UNGROUPED=1` uses the per-transition path.
- **Early exits** (`CB_NOSTOP=1` disables them). Once converged or hopeless, the remaining units are filled with failure probability 1, which is always a valid value.
- **Profile** (`CB_DEBUG=1`), at 40 % and 72 h on an M3 Pro: about 1.2 ms per burst step (16M multiply-adds) plus 0.9 ms per gap step. This is close to memory bandwidth, so further speed comes from running fewer configs.
- **Lateness.** An optional 7th config field is `p_late`, the probability that an honest proposal is late. Late proposals count as adversarial, as in the Lean `lotStrS`.
