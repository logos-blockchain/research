# Formal verification (Lean 4 + Mathlib)

Machine-checked versions of results in [`reports/`](../reports).

- **Lean** v4.34.1, **Mathlib** v4.34.1.
- **Status:** no `sorry`s, no custom axioms, no warnings.

```sh
# from formal/ (needs elan; the toolchain is pinned in lean-toolchain)
lake exe cache get                               # fetch prebuilt Mathlib
lake build                                       # check every proof
lake env lean StochasticRecurrenceTest/Axioms.lean   # axioms used by the main results
```

## Libraries

| Library | Report | Contents |
|---|---|---|
| [`StochasticRecurrence`](StochasticRecurrence/README.md) | [`analysis_of_stochastic_recurrence_equation.tex`](../reports/analysis_of_stochastic_recurrence_equation.tex) | The stake-estimate recurrence: binomial reduction (Prop. 2.1), concentration around the mean-field recursion (Thm. 2.1, `theorem_2_1`), the critical threshold `D_c`, and `E[D_ℓ] ≤ d_ℓ` |
