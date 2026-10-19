# Cryptarchia certificate generator

Generates `formal/Cryptarchia/Prob/Certs/*.lean`: the finality certificates, instances of `Prob.finality` (`emitE.py`, at the specification with a given depth `k`) and of its closed form (`emitC.py`, every depth).

- `plan.py` picks the potential's parameters by a float search that minimises the contraction `lp` (`auto.py`, `eps5.py` are its float models); `cert2.py` holds the exact automaton solutions in rationals; `certnum.py` the rounding, `gen.py` the repeated-squaring power chains; `emit_gen.py` a member's band (`memberOfQ`); `powq.py` mirrors the computed powers of `Prob/CertGen.lean` (`powUpQ`).

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
- **`Certs/NAME/Data.lean`** and **`Certs/NAME/I<g>.lean`**: the configuration `F : FamCfg` (the potential's parameters, the family, and its integer bands, computed once), and each phase index's data, a few indices per file (`emitF.IDX_FILES`). Each member's band is computed from its breakpoints exactly as `emit_gen.member_band` computes it (`memberOfQ`, `Prob/CertGen.lean`), the weakest band as their minimum and maximum, and one kernel check (`famOK`) gives `Member.OK`, `Band.Prod`, `Band.Weaker` and the integer bands for every member; consecutive members chain by construction. Each index's seeds and bounds are computed at elaboration time (`eval%`, `Prob/EvalLit.lean`) and checked by the kernel (`chk<i>`, `idxChk`). A table is determined by its three seeds, its entries at `(0, a, true)`: every other entry is one recursion step from the next row (`fillZ`, `fillAllZ`, rounded up to the scale `2⁶⁴`), and a fill solves the recursion everywhere but at the seeds by construction (`fillAllZ_entry`, `Prob/AutoZ.lean`), so the checks reduce to the seeds (`seedOKZ`). The seeds come from Newton's method on finite differences, warm-started from the previous member; the kernel only checks them, so the solver needs no proof and adds no axiom. The checks run in integer arithmetic (`Prob/AutoZ.lean`), each exactly proportional to the real one (`stepZ_cast`, `slot4Z_cast`).
- **`Certs/NAME.lean`**: the derived numbers `der := eval% par.derive …` (`SpecData.derive`: the contractions `lp` and `lpi` from the tables' bounds, the settlement parameters by their rules, `M`, `Ne`, and the settlement, band and finality bounds), computed at elaboration time, not written; the kernel checks every condition on them, so the rules need no proof; the theorem's stated epoch count and bound are checked against them (`derNe`, `derFin`); two kernel checks (`mainOK`: the potential's conditions and every member's class conditions; `finOK`: every numeric condition of the finality theorem, the constants taken from `Config.specK k`); and the finality theorem, an instance of `Claim.Finality` (one application of `FamCfg.finality_spec`), restated by hand in `formal/CryptarchiaCerts.lean`.

`emitZ.py`, `powq.py` and `emitF.py` mirror these computations exactly, and the generator runs every check before writing a file; it also checks that the expectations Lean derives from the tables are at most the planned ones, so the planned contractions and targets hold. No axioms beyond Lean's standard three. Lean checks a file's theorems one after another, so the 19 index checks are split over seven files per certificate, which Lake builds in parallel: the three certificates build in about 2.5 min on 12 cores (3.6 min with one data file each; one file per index is slower, at 10 min, since every file pays the start-up of loading the evaluator). The generated files are modules.

Examples (the committed certificates, with μ = 0.13 and the default stake drift ρ = 1.01, `RHO` in `certE.py`):

```sh
python3 emitE.py 0.2 11 0.085 32 31536000 E20D11 ../../Cryptarchia/Prob/Certs all 0.13
```

The arguments are β, Δ, the TSI band δ, the number of band members, the horizon, the name, the output directory, `all` or `emit`, μ, and the depth k (2160 by default; the configuration is `Config.specK k`, with the epoch geometry set by `certE.set_depth`). More members narrow each member's exponent range and so tighten the automaton bounds; δ trades the band term `Ne · bandEps` (smaller for larger δ) against the members' spread (wider for larger δ). At β = 0.2 and k = 2160 the best total was at K = 32 and δ = 0.085 (sweeps over K ∈ {6, 10, 16, 24, 32}, δ ∈ {0.075, …, 0.09}); at k = 1000, where the observation period is shorter, at δ = 0.07 (δ ∈ {0.055, …, 0.085}).

## Table certificates

`emitT.py` writes a certificate whose failed checks are bounded by a table potential (`Prob/Table.lean`,
`TableCert.lean`, `TableSpec.lean`) instead of the two-term exponential one: a two-month certificate at
k = 1000 (`E20D11T`), 1.5e-3 against 1.5e-2 with the exponential potential (in-epoch contraction 0.997217
against 0.99774), since replaced by the grouped `E20D11G` below. The table comes from the linear program of `tools/cbound/witness.py` (saved with
`WITNESS_OUT`, or by a script calling `Witness.solve`), rounded to rationals that keep its shape
(`emitT.round_table`). Lean computes each representative state's terminal table and one-switch tables
(`FamCfg.repData`), the contractions by rule (`tabLp`, `tabLpi`) and the derived numbers; the other
indices need only their switching tables (0, 1, 2, 17). The representatives are checked in chunks of 11
(`R<j>.lean`), one kernel check per representative (about 7 s and 2 GB each; one check per chunk would keep the kernel's cache for the whole chunk), built four at a time (each chunk imports the one four before it).
Two passes: `emit` writes all but the main file; after building those, `main` reads the derived numbers
from Lean and writes the main file.

```sh
python3 emitT.py 1/5 7/100 32 5184000 1000 V.npy 10 20 27/20 13/10 13/5 27/20 2 41/40 E20D11T ../../Cryptarchia/Prob/Certs emit
lake build $(for j in $(seq 0 23); do printf 'Cryptarchia.Prob.Certs.E20D11T.R%d ' $j; done)
python3 emitT.py 1/5 7/100 32 5184000 1000 V.npy 10 20 27/20 13/10 13/5 27/20 2 41/40 E20D11T ../../Cryptarchia/Prob/Certs main
```

The arguments are β, δ, the members, the horizon, the depth, the LP's table, the box (`R`, `M`), the
extension factors `cw`, `zc`, the automaton's factor `x`, the reach and check bases `c`, `z`, the span tilt
`τ`, the name and the output directory.

`emitTG.py` writes the grouped variant (`Prob/TableG.lean`, `TableGCert.lean`, `TableGSpec.lean`): one table
per group of consecutive band members (`FamCfg.grpOf`), solved jointly by `Witness.solve_joint` with the
tables within a factor `Γ` of each other. The potential grows by `γ = 1 + 1/(k₀ (EL − 1))` per slot of the
epoch's age, which covers `Γ` when an epoch ends and costs a start factor `γ^(EL−1) ≤ e^(1/k₀) ≤ sU`
(`startChk`). This is the two-month certificate (`E20D11G`, 4.3e-5): four groups at δ = 0.085, where the band
term is 18 × 6.6e-7, with in-epoch contraction 0.996862. The tables' box is 5 warm rows by 20 margins
(616 entries); the box 10 × 20 (1056 entries) gives 3.8e-5, 6 × 20 gives 4.1e-5 and 4 × 20 gives 5.4e-5, while fewer margins cost more
(10 × 12: 5.4e-5, 10 × 8: 1.4e-4).

Each (group, representative) is checked in about 1.4 s and 1.7 GB in the kernel (`repChkAG`), its tables given by rows
over `ℕ` and computed once at elaboration time:

- the one-switch tables come from the family's worst band (`chkOneWN`): one post-switch table `W`, which bounds
  every member's because `slot4` is monotone in the band, and one pre-switch table above it. Each of the
  group's members also has its own post-switch table, for its in-epoch bound;
- a phase starting more than `RDLY` slots before a boundary is bounded by the member's geometric envelope
  `P + λ^r Z` (`chkEnvN`, `phase_autoEnv`): `P` its own post-switch table, `Z ≥ W − P` with one step of the
  recursion's linear part at most `λ Z`, which suffices since the step is subadditive. So the one-switch
  contraction (1.0039) is paid only for the `RDLY = 60` slots before a boundary (`Ccap`).

The checks run over `ℕ` (`stepN`, `chkOneWN`, `chkEnvN`), whose arithmetic the kernel does by GMP, with the
constants as literals (`ChkCst`); `der` is written by the generator from `tabsim.py`. The 56 chunks build eight
at a time in about 6.5 min, the main file in about 1 min.

```sh
python3 emitTG.py 1/5 85/1000 32 5184000 1000 VJ.npy 4 5 20 27/20 13/10 13/5 27/20 2 41/40 219/200 10 60 E20D11G ../../Cryptarchia/Prob/Certs emit
lake build $(for j in $(seq 0 55); do printf 'Cryptarchia.Prob.Certs.E20D11G.R%d ' $j; done)
python3 emitTG.py 1/5 85/1000 32 5184000 1000 VJ.npy 4 5 20 27/20 13/10 13/5 27/20 2 41/40 219/200 10 60 E20D11G ../../Cryptarchia/Prob/Certs main
```

The arguments are as `emitT`'s, with the number of groups after the LP's tables (an array of one table per
group), and `Γ`, `k₀` and `RDLY` after `τ`.

## Predicting a table certificate

`tabsim.py` mirrors the grouped certificate's computations exactly, with the integer mirrors of `emitZ`: each
entry's data (`rep_w`, as `FamCfg.repDataG`), the contractions (`tabLpG`, `tabLpiG`) and the derived numbers
(`SpecData.deriveLE`). Over all the entries it takes about a minute on eleven cores, against half an hour for
the Lean build, and caches each entry's data in `.tabsim_cache`. Its bound for `E20D11G` agrees with Lean's to
the digit (lp 1.003842, lpi 0.9968621, settlement 3.1e-5, 4.3e-5). Use it to choose the tables, groups and
`RDLY` before building.

## Closed-form certificates

`emitC.py BETA DELTA DELTA_TSI K NAME OUTDIR K0 [MU] [RHO]` writes a certificate for every depth `k ≥ K0` and every horizon `N`, at the configuration `Config.specK k` (the specification with depth `k`). The automaton tables do not depend on `k`; the settlement parameters are linear in `t = k / 20` (`G' = g t`, `J = j t`, `Lw = w t`, `r = ρ t`); `g, j, w, ρ`, the phase cut `G`, the growth block `T` and the tilts follow the rules of the specification's certificates, at the horizon `N1 = 5184000` and depth `k1 = 2160` (`ClosedData.derive`, `emitF.closed_rules`), the non-decaying phase-cut term fitted at `t1 + t1 / 4`. Each of `settleEps3E`'s seven terms is then bounded by `(N + c) · A · qᵗ` (`settleEps3E_closed` in `Prob/Closed.lean`), and the band by `C · Q⁻ᵗ` per epoch (`bandEps_closed`), with the band's drift conditions checked at `K0` (`hup_of_k0`, `hdn_of_k0`). The constants are derived in Lean (`ClosedData.derive`, mirrored by `emitF.closed_derive`), and the certificate is again its data (`emitF.emit_closed`): the parameter and data files as above, the chosen numbers `par : ClosedData` (the depth per `t`, the least depth, the fitting point `N1`, `k1` and `ε`) in `Params.lean`, with the estimate's band by rule at the least depth (`TBandQ.ofDrift (Config.specK par.k0)`), and a main file with the derived numbers `der := eval% par.derive …` (`ClosedData.derive`: the settlement parameters and tilts by rule, the contractions, the growth blocks, the constants `A`, `q`, `C`, `Q` and the short form's rates), computed, not written, one kernel check of every condition on them (`closedOK`, `closedChk` in `Prob/CertClosed.lean`), and:

- `finality_closed`: the bound `par.epsC der N k`, the sum of the nine geometric terms (`FamCfg.finality_closed_gen`);
- `finality_closed_short`: the same, folded from `t ≥ K0 / 20` on into one settlement rate and one band rate (`par.epsShort der N k`, `epsC_le_short`) and stated as an explicit formula, its constants rounded up to a few digits (`emitF.dec_up`). This is the one `formal/CryptarchiaCerts.lean` restates: its statement uses no certificate data.

Three facts about the rates' growth in `k` (the growth blocks, `w t + G < 300 k`, and `G + g t + Δ + 2 + 180 k ≤ 300 k`, which keeps the epochs the proof needs inside the horizon's windows) are nonlinear in `k`; the certificate proves each with `omega` on its numbers.

Example (the committed certificate): `python3 emitC.py 0.2 11 0.085 32 E20D11C ../../Cryptarchia/Prob/Certs 1000 0.13 101/100`. It prints the bound at a few `(N, k)`.
