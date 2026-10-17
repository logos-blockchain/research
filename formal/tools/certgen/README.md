# Cryptarchia certificate generator

Generates `formal/Cryptarchia/Prob/Certs/*.lean`: numeric certificates for `final_bimm_prob2`.

- `plan.py BETA DELTA` picks parameters and prints a JSON plan. It runs a float search that minimises `lp`, then splits the error between spans, failed checks and crowded windows.
- `mkcfg.py BETA DELTA NAME OUTDIR` rounds the plan. It builds the exact certificate (`cert2.py`: automaton solutions in rationals, mirroring `Auto.lean` / `Cold2.lean`) and writes the Lean file (`emit2.py`) at the best power-of-ten bound.
- `auto.py`, `eps5.py` are the float models; `certnum.py`, `gen.py` hold the rounding and the repeated-squaring power chains; `powq.py` mirrors the computed powers of `Prob/CertGen.lean` (`powUpQ`).

Example: `python3 plan.py 0.3 11 > plan_0.3_11.json && python3 mkcfg.py 0.3 11 B30D11 ../../Cryptarchia/Prob/Certs`

## Multi-epoch certificates (`Cert3E`)

- `certE.py` builds the exact tables for one band family. The members are honest exponent ranges covering `[(1-β)ℓlo, ℓhi]` from the estimate's band (`tband`), with the adversary at most `β/(1-β)` times the honest exponent. The tables are:
  - switching tables for phase indices 0, 1, 2, 17, one table solving every member's recursion;
  - one-switch tables for the other indices: `vpost` (each member's own solution), `vmax` (their maximum) and `vpre` (each member's recursion, floored at `vmax`).
  
  It also returns the in-epoch bounds `ei`, taken from the `vpost` tables, and the crossing bound `pat0 = min_k slo_k · elo_k^Δ`.
- `planE.py BETA DELTA DELTA_TSI K N` plans the potential's constants on the top member's band. It builds the exact tables and computes the in-epoch contraction `lpi`. It then picks the span, window, empty-run and growth parameters against the weakest band (`stage2`), and prints the seven terms of `settleEps3E` and the band term `Ne · bandEps`.
- The settlement parameters follow fixed rules (`SpecData.derive` in Lean, mirrored by `emitF.spec_rules`): `Lw` and `J` minimize the main terms (spans, failed checks, crowded windows) by ternary search, the window at its best Chernoff tilt `x`; `G`, `G'` and `r` are each the least making their term at most `ε = 1/100` of the main terms; `T` minimizes the slow-growth term over `1, …, 64` at its best tilt `yy`.
- `emitE.py BETA DELTA DELTA_TSI K N NAME OUTDIR [all|emit] [MU]` plans (or, with `emit`, reloads the potential from the cached plan `res_NAME.pkl` and rebuilds the family's tables, `emitE.retable`) and writes the certificate with `emitF.py`.

**A certificate is its data.** It states only the numbers a search chose; Lean computes the rest and the kernel checks it, with the generic constructions and theorems in `Prob/CertGen.lean`, `Prob/CertSpec.lean` and (closed form) `Prob/CertClosed.lean`:

- **`Certs/NAME/Params.lean`**: every number the search chose, each with a line comment: the potential's parameters `pot : PotCfg` (`Δ` and `c z s d τ`) and the other numbers `par` (the potential's `κ`, the horizon, `ε`, the drift `ρ` and `Hmin`). The estimate's band `Tq` is the least the drift conditions allow (`TBandQ.ofDrift`: 30 rounds of the conditions solved for `ℓhi` and `ℓlo`, at 8 digits, as `certE.tband`), and the band family `S : FamSpec` splits it geometrically (`geomYs`: the least 12-decimal ratio whose `K`-th power spans `[ylo, Yh]`, as `certE.geom_ys`); both are computed at elaboration time (`eval%`).
- **`Certs/NAME/Data.lean`**: the configuration `F : FamCfg` (the potential's parameters, the family, and its integer bands, computed once), and each phase index's data. Each member's band is computed from its breakpoints exactly as `emit_gen.member_band` computes it (`memberOfQ`, `Prob/CertGen.lean`), the weakest band as their minimum and maximum, and one kernel check (`famOK`) gives `Member.OK`, `Band.Prod`, `Band.Weaker` and the integer bands for every member; consecutive members chain by construction. Each index's seeds and bounds are computed at elaboration time (`eval%`, `Prob/EvalLit.lean`) and checked by the kernel (`chk<i>`, `idxChk`). A table is determined by its three seeds, its entries at `(0, a, true)`: every other entry is one recursion step from the next row (`fillZ`, `fillAllZ`, rounded up to the scale `2⁶⁴`), and a fill solves the recursion everywhere but at the seeds by construction (`fillAllZ_entry`, `Prob/AutoZ.lean`), so the checks reduce to the seeds (`seedOKZ`). The seeds come from Newton's method on finite differences, warm-started from the previous member; the kernel only checks them, so the solver needs no proof and adds no axiom. The checks run in integer arithmetic (`Prob/AutoZ.lean`), each exactly proportional to the real one (`stepZ_cast`, `slot4Z_cast`).
- **`Certs/NAME.lean`**: the derived numbers `der := eval% par.derive …` (`SpecData.derive`: the contractions `lp` and `lpi` from the tables' bounds, the settlement parameters by their rules, `M`, `Ne`, and the settlement, band and finality bounds), computed at elaboration time, not written; the kernel checks every condition on them, so the rules need no proof; the theorem's stated epoch count and bound are checked against them (`derNe`, `derFin`); two kernel checks (`mainOK`: the potential's conditions and every member's class conditions; `finOK`: every numeric condition of the finality theorem, the specification's constants taken from `Config.spec`); and the finality theorem, one application of `FamCfg.finality_spec`.

`emitZ.py`, `powq.py` and `emitF.py` mirror these computations exactly, and the generator runs every check before writing a file; it also checks that the expectations Lean derives from the tables are at most the planned ones, so the planned contractions and targets hold. No axioms beyond Lean's standard three. Lean checks a file's theorems one after another, so a certificate's 19 index checks take about 2.3 min; the three certificates build in parallel in about 2.5 min. The generated files are modules.

Examples (the committed certificates, with μ = 0.13 and the default stake drift ρ = 1.01, `RHO` in `certE.py`):

```sh
python3 emitE.py 0.2 11 0.085 32 31536000 E20D11 ../../Cryptarchia/Prob/Certs all 0.13
python3 emitE.py 0.2 11 0.085 32 5184000 E20D11M2 ../../Cryptarchia/Prob/Certs all 0.13
```

The arguments are β, Δ, the TSI band δ, the number of band members, the horizon, the name, the output directory, `all` or `emit`, and μ. More members narrow each member's exponent range and so tighten the automaton bounds; δ trades the band term `Ne · bandEps` (smaller for larger δ) against the members' spread (wider for larger δ). At β = 0.2 the best total was at K = 32 and δ = 0.085 (sweeps over K ∈ {6, 10, 16, 24, 32}, δ ∈ {0.075, …, 0.09}).

## Closed-form certificates

`emitC.py BETA DELTA DELTA_TSI K NAME OUTDIR K0 [MU] [RHO]` writes a certificate for every depth `k ≥ K0` and every horizon `N`, at the configuration `Config.specK k` (the specification with depth `k`). The automaton tables do not depend on `k`; the settlement parameters are linear in `t = k / 20` (`G' = g t`, `J = j t`, `Lw = w t`, `r = ρ t`); `g, j, w, ρ`, the phase cut `G`, the growth block `T` and the tilts follow the rules of the specification's certificates, at the horizon `N1 = 5184000` and depth `k1 = 2160` (`ClosedData.derive`, `emitF.closed_rules`), the non-decaying phase-cut term fitted at `t1 + t1 / 4`. Each of `settleEps3E`'s seven terms is then bounded by `(N + c) · A · qᵗ` (`settleEps3E_closed` in `Prob/Closed.lean`), and the band by `C · Q⁻ᵗ` per epoch (`bandEps_closed`), with the band's drift conditions checked at `K0` (`hup_of_k0`, `hdn_of_k0`). The constants are derived in Lean (`ClosedData.derive`, mirrored by `emitF.closed_derive`), and the certificate is again its data (`emitF.emit_closed`): the parameter and data files as above, the chosen numbers `par : ClosedData` (the depth per `t`, the least depth, the fitting point `N1`, `k1` and `ε`) in `Params.lean`, with the estimate's band by rule at the least depth (`TBandQ.ofDrift (Config.specK par.k0)`), and a main file with the derived numbers `der := eval% par.derive …` (`ClosedData.derive`: the settlement parameters and tilts by rule, the contractions, the growth blocks, the constants `A`, `q`, `C`, `Q` and the short form's rates), computed, not written, one kernel check of every condition on them (`closedOK`, `closedChk` in `Prob/CertClosed.lean`), and:

- `finality_closed`: the bound `par.epsC der N k`, the sum of the nine geometric terms (`FamCfg.finality_closed_gen`);
- `finality_closed_short`: the same, folded from `t ≥ K0 / 20` on into one settlement rate and one band rate (`par.epsShort der N k`, `epsC_le_short`).

Three facts about the rates' growth in `k` (the growth blocks, `w t + G < 300 k`, and the epoch count) are nonlinear in `k`; the certificate proves each with `omega` on its numbers.

Example (the committed certificate): `python3 emitC.py 0.2 11 0.085 32 E20D11C ../../Cryptarchia/Prob/Certs 1000 0.13 101/100`. It prints the bound at a few `(N, k)`.
