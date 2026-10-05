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
- `emitE.py BETA DELTA DELTA_TSI K N NAME OUTDIR [main]` writes `Certs/NAME/Fam.lean`, `Certs/NAME/I<i>.lean` (one file per phase index) and `Certs/NAME.lean`. The last holds the potential `P`, the certificates `C : Cert2E` and `D3 : Cert3E`, the numbers `eps_le`, the band constants `Tb` with `band_le`, and the theorems `certified` and `certified_tsi`. With `main`, only `NAME.lean` is rewritten, from the cached plan `res_NAME.pkl`.

Build the files one at a time; each table file takes a few minutes and a few GB.

Example: `python3 emitE.py 0.2 11 0.09 6 31536000 E20D11 ../../Cryptarchia/Prob/Certs`
