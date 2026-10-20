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

A failed check's window can cross one epoch boundary, where the member changes. `shared.py` finds one table for a set of members by constraint generation (solve for a few members, check all with the operator, add the worst). One table for all 32 members reaches only 0.99709 (members 0 and 31 want different shapes); four tables, one per group of eight consecutive members, reach 0.99680 (group 0 binding), with ratios at most 1.89 between the tables, a factor paid once per check. The check starts at an anchor where the margin equals the reach, bounded by the reach potential `c_r^ρ`; the table costs the factor `C = max V(ρ, ρ) / c_r^ρ` (`startfac.py`, the least `C` at a fixed `λ`). Against the certificate's `c = 1.1785` that factor is unbounded (the warm tail grows by 1.9), but with the reach potential at `c_r = 1.9` it is `C = 1` for every group, and the reach constant `stat` goes from 2.50 to 4.83 (`lr` 0.995947, `b` 1.015524, from the generator's own tables). With everything charged (four groups at `λ = 0.99681`, switching ×2.5, `c_r = 1.9`), the generator's rules give a settlement bound of 1.7e-4, against 1.2e-2 certified now; one shared table (`λ = 0.99709`, no switching) gives 4.2e-4.

The span tilt `τ` (`span.py`) is a searched constant of the certificate, 1.01 at k = 1000, chosen for the old potential. With the faster failed checks the best tilt moves to 1.02 (`e17` 1.034222), and the estimate drops to 4.7e-5: failed checks 4.2e-5, crowded windows 2.5e-6, spans 1.8e-6, the rest below 3e-7. A tilt chosen by rule (the least total over a grid) would also remove a searched constant.

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

## A sound table witness, and the Lean side (status)

`witness.py` asks the table for everything a proof uses: the extension's representatives (the row
`ρ = R + 1` and the column `μ = -(M + 1)`), the shape conditions (monotone, margin decay at least `zc`,
warm growth at most `cw`, `x ≥ cw · zc`, cold values at least `z^μ`), and boundary phases through the
one-switch automaton over the members (as `AutoSolE`). All 32 members of the k = 1000 family with one
shared table (`cw = 1.35`, `zc = 1.3`, `x = 2.6`, a 10 × 20 box): in-epoch 0.99736 at boundary 0.998, or
0.99716 at 0.9985 (the certificates' potential: 0.99774, 0.99899). With the reach potential at
`c_r = 1.35` (`stat` 2.89), the check base `z = 2` (`e2` 0.0687) and the span tilt re-chosen (1.025),
the generator's rules give a settlement bound of 1.2e-4 at β = 0.2, against 1.2e-2 certified now.

Lean, done: `Prob/Fail3E.lean` (`FailPot`, `fail_checkF`: the failed-check bound for any potential with
those properties; `FailPot.ofV2`), `Prob/Table.lean` (`TabPot`, its shape conditions, `V_mono`, `V_rep`,
`post_le`: the pointwise bound after a phase at every state, through the representatives; `toFailPot`,
given the contraction checks at the finitely many representatives). To do:

1. a rational table (`ℚ` data, decidable shape and tie checks, cast lemmas for `V`, `gT`, `crT`);
2. the table certificate: per representative, one-switch tables for its terminal table `gT` (seeds by
   `eval%`, `chkOneF` / `oneSwitchF_sound` as for the 19 indices), the crossing bounds, and the
   contraction checks, giving `toFailPot`'s hypotheses;
3. the settlement bound and `Prob.finality` with a `FailPot` (`lp`, `lpi` from it);
4. the certificate checks and rules (`CertSpec`), and the generator (solve, rationalize, emit);
5. the k = 1000 certificate with the table.
