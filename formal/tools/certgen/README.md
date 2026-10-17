# Cryptarchia certificate generator

Generates `formal/Cryptarchia/Prob/Certs/*.lean`: numeric certificates for `final_bimm_prob2`.

- `plan.py BETA DELTA` picks parameters and prints a JSON plan. It runs a float search that minimises `lp`, then splits the error between spans, failed checks and crowded windows.
- `mkcfg.py BETA DELTA NAME OUTDIR` rounds the plan. It builds the exact certificate (`cert2.py`: automaton solutions in rationals, mirroring `Auto.lean` / `Cold2.lean`) and writes the Lean file (`emit2.py`) at the best power-of-ten bound.
- `auto.py`, `eps5.py` are the float models; `certnum.py`, `gen.py` hold the rounding and the repeated-squaring power chains.

Example: `python3 plan.py 0.3 11 > plan_0.3_11.json && python3 mkcfg.py 0.3 11 B30D11 ../../Cryptarchia/Prob/Certs`

## Multi-epoch certificates (`Cert3E`)

- `certE.py` builds the exact tables for one band family. The members are honest exponent ranges covering `[(1-β)ℓlo, ℓhi]` from the estimate's band (`tband`), with the adversary at most `β/(1-β)` times the honest exponent. The tables are:
  - switching tables for phase indices 0, 1, 2, 17, one table solving every member's recursion;
  - one-switch tables for the other indices: `vpost` (each member's own solution), `vmax` (their maximum) and `vpre` (each member's recursion, floored at `vmax`).
  
  It also returns the in-epoch bounds `ei`, taken from the `vpost` tables, and the crossing bound `pat0 = min_k slo_k · elo_k^Δ`.
- `planE.py BETA DELTA DELTA_TSI K N` plans the potential's constants on the top member's band. It builds the exact tables and computes the in-epoch contraction `lpi`. It then picks the span, window, empty-run and growth parameters against the weakest band (`stage2`), and prints the seven terms of `settleEps3E` and the band term `Ne · bandEps`.
- `optnum.py` re-optimizes the settlement parameters (`G'`, `J`, `Lw`, `r`, `T`, `x`, `yy`) against the exact seven terms: Nelder–Mead in the logarithm of their sum, then an integer polish. `emitE.py` runs it on the plan before setting the target.
- `emitE.py BETA DELTA DELTA_TSI K N NAME OUTDIR [all|main|emit] [MU]` writes `Certs/NAME/Fam.lean`, `Certs/NAME/I<i>.lean` (one file per phase index, from `emitZ.py`) and `Certs/NAME.lean`. The last holds the potential `P`, the certificates `C : Cert2E` and `D3 : Cert3E`, the numbers `eps_le`, the band constants `Tb` with `band_le`, and the theorems `certified` and `certified_tsi`. With `main`, only `NAME.lean` is rewritten, from the cached plan `res_NAME.pkl`; with `emit`, every file is rewritten from it.

Each table is given by its three entries at `(0, a, true)`, the state just after an honest success: every other entry is one recursion step from the next row, so Lean computes the table from them by backward recursion (`fillZ`, and `fillAllZ` for a switching table, the step's maximum over the members), each step rounded up to the scale `2⁶⁴`. A one-switch index also gives `vmax` in full, so that each member's checks stand alone. The checks (`AutoSol`, `PreSol`, `post ≤ vmax`, `autoBound ≤ e`) run in integer arithmetic (`Cryptarchia/Prob/AutoZ.lean`): band fields over a common denominator (`famZ`, `DZ` in `Fam.lean`), `x`, `θ`, `g` over theirs (`X<i>`), tables at scale `2⁶⁴`. Each integer check is exactly equivalent to the rational one (`stepZ_cast`, `slot4Z_cast`), so its soundness comes from the lemmas in `AutoQ.lean`; the kernel evaluates it with its arbitrary-precision `Nat` arithmetic, by `decide +kernel`, with no normalization of rationals. No axioms beyond Lean's standard three. `emitZ.py` mirrors the Lean computation exactly and runs every check before writing a file. Each index has its own file (`I<i>.lean`), and Lake checks the 19 in parallel; a whole certificate (32 members) builds in about 1.5 min. The generated files are modules, with the imports `lake shake` computes (`EXT`, `FAM_IMPORTS`, `MAIN_IMPORTS` in `emitE.py`); after changing the emitted proofs, rerun `lake shake CryptarchiaCerts` and update those lists.

Examples (the committed certificates, with μ = 0.13 and the default stake drift ρ = 1.01, `RHO` in `certE.py`):

```sh
python3 emitE.py 0.2 11 0.085 32 31536000 E20D11 ../../Cryptarchia/Prob/Certs all 0.13
python3 emitE.py 0.2 11 0.085 32 5184000 E20D11M2 ../../Cryptarchia/Prob/Certs all 0.13
```

The arguments are β, Δ, the TSI band δ, the number of band members, the horizon, the name, the output directory, `all` or `main`, and μ. More members narrow each member's exponent range and so tighten the automaton bounds; δ trades the band term `Ne · bandEps` (smaller for larger δ) against the members' spread (wider for larger δ). At β = 0.2 the best total was at K = 32 and δ = 0.085 (sweeps over K ∈ {6, 10, 16, 24, 32}, δ ∈ {0.075, …, 0.09}).

## Closed-form certificates

`emitC.py BETA DELTA DELTA_TSI K NAME OUTDIR K0 [MU] [RHO]` writes a certificate for every depth `k ≥ K0` and every horizon `N`, at the configuration `Config.specK k` (the specification with depth `k`). The automaton tables do not depend on `k`; the settlement parameters are linear in `t = k / 20` (`G' = g t`, `J = j t`, `Lw = w t`, `r = ρ t`, with `g, j, w, ρ` chosen by `opt_params` to minimize the bound at `k = 2160`, `N = 5184000`). Each of `settleEps3E`'s seven terms is then bounded by `(N + c) · A · qᵗ` (`settleEps3E_closed` in `Prob/Closed.lean`; the powers by repeated squaring), and the band by `C · Q⁻ᵗ` per epoch (`bandEps_closed`), with the band's drift conditions checked at `K0` (`hup_of_k0`, `hdn_of_k0`). The file states:

- `finality_closed`: the bound `epsC N k`, the sum of the nine geometric terms;
- `finality_closed_short`: the same, folded from `t ≥ K0 / 20` on into one settlement rate and one band rate (`geom_le_of`).

Example (the committed certificate): `python3 emitC.py 0.2 11 0.085 32 E20D11C ../../Cryptarchia/Prob/Certs 1000 0.13 101/100`. It prints the bound at a few `(N, k)`.
