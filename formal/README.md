# Formal verification (Lean 4 + Mathlib)

Machine-checked versions of results in [`reports/`](../reports) and of specifications under review in [logos-lips](https://github.com/logos-co/logos-lips).

- **Lean** v4.34.1, **Mathlib** v4.34.1.
- **Status:** no `sorry`s, no custom axioms, no warnings.

```sh
# from formal/, inside `nix-shell` (shell.nix provides elan; the toolchain is pinned in lean-toolchain)
lake exe cache get                               # fetch prebuilt Mathlib
lake build                                       # check every proof, and run the MantleTest and
                                                 # TokenEconomicsTest libraries: axiom gates, Mantle's
                                                 # test vectors, the block reward and base fee vs.
                                                 # hand-computed values, the supply projection
lake env lean StochasticRecurrenceTest/Axioms.lean   # axioms used by the main results
lake env lean MiningOnboardingTest/Axioms.lean
lake env lean MiningOnboardingTest/Report.lean       # calculator vs. the report's numbers
```

## Libraries

| Library | Report | Contents |
|---|---|---|
| [`StochasticRecurrence`](StochasticRecurrence/README.md) | [`analysis_of_stochastic_recurrence_equation.tex`](../reports/analysis_of_stochastic_recurrence_equation.tex) | The stake-estimate recurrence: binomial reduction (Prop. 2.1), concentration around the mean-field recursion (Thm. 2.1, `theorem_2_1`), the critical threshold `D_c`, and `E[D_ℓ] ≤ d_ℓ` |
| [`MiningOnboarding`](MiningOnboarding/README.md) | [`mining_funded_onboarding.tex`](../reports/mining_funded_onboarding.tex) | The mining-funded onboarding model: the fixed-population ODE system and its unique solution, properties of `A(t;M)`, exact existence and uniqueness of `m_min` (`feasible_iff`), two-sided small-growth bounds, continuing entry with delayed unlocking; plus a `Float` calculator and cohort simulator for exploring the design |
| [`Mantle`](Mantle/README.md) | Mantle 2.1.0 with [logos-lips#480](https://github.com/logos-co/logos-lips/pull/480) and [#481](https://github.com/logos-co/logos-lips/pull/481) | The private UTXO ledger with programs: MMR and IMT correctness, the 1024-root window, every Operation transcribed, **no Mantle Transaction creates value** (`applyTx_value`), mini-block reordering, withdrawals, Proof of Leadership soundness over the eligible root and its lottery (approximation bounds, exact constants), program notes moved only by their program's proof, payment binding, a canonical transaction encoding with the test vectors checked, gas constants |
| [`TokenEconomics`](TokenEconomics/README.md) | Block Rewards, Cryptoeconomics Overview and Execution Market, as modified by the same PRs | The integer block reward is the floored reward equation, its `int128` bounds, the pool never goes below zero, the Blend share always covers its payment, the base fee update, **no token is ever minted** over any chain of blocks (`executeChain_total`), and the 10-year supply projection (bounds, steady state, the noise-free scenario, a simulator) |
