# Formal verification (Lean 4 + Mathlib)

Machine-checked definitions and proofs for the Logos blockchain, in Lean 4 with Mathlib: a formal specification of the protocol that the specification documents, the implementation and the security analysis can all be checked against, and machine-checked versions of results in [`reports/`](../reports).

- **Lean** v4.34.1, **Mathlib** v4.34.1 (pinned in `lean-toolchain` and `lake-manifest.json`).
- **Status:** no `sorry`, no custom axioms. Every headline theorem uses only Lean's standard three (`propext`, `Classical.choice`, `Quot.sound`); the `*Test/Axioms.lean` files check them.

## What is here

| Library | Contents |
|---|---|
| [`Cryptarchia`](Cryptarchia/README.md) | The consensus protocol: its specification, settlement combinatorics, deterministic safety over executions, and the probability layer, including total stake inference (TSI). |
| `CryptarchiaCerts` | A generated numeric certificate for Cryptarchia's settlement theorem at the specification's parameters (`E20D11`: β = 0.2, one year). It takes about an hour to build and is not a default target. |
| `CryptarchiaTest` | Axiom checks, and differential tests of the specification's definitions against an independent transliteration of the pseudocode. |

Libraries formalizing individual reports:

| Library | Report | Contents |
|---|---|---|
| [`StochasticRecurrence`](StochasticRecurrence/README.md) | [`analysis_of_stochastic_recurrence_equation.tex`](../reports/analysis_of_stochastic_recurrence_equation.tex) | The stake-estimate recurrence: binomial reduction (Prop. 2.1), concentration around the mean-field recursion (Thm. 2.1, `theorem_2_1`), the critical threshold `D_c`, and `E[D_ℓ] ≤ d_ℓ` |
| [`MiningOnboarding`](MiningOnboarding/README.md) | [`mining_funded_onboarding.tex`](../reports/mining_funded_onboarding.tex) | The mining-funded onboarding model: the fixed-population ODE system and its unique solution, properties of `A(t;M)`, exact existence and uniqueness of `m_min` (`feasible_iff`), two-sided small-growth bounds, continuing entry with delayed unlocking; plus a `Float` calculator and cohort simulator for exploring the design |

Each protocol component is its own Lean library at the top level of this folder. New components (for example the Mantle ledger or Blend networking) go next to `Cryptarchia`, not inside it.

## Layout

```
formal/
  lakefile.toml           one Lake package; one lean_lib per component
  Cryptarchia.lean        library root: imports every module
  Cryptarchia/
    Spec/                 the protocol as specified: definitions only
    Settle/               settlement combinatorics (PoS trees)
    Proof/                deterministic safety over executions
    Prob/                 probability layer: random oracle, kernels, bounds, TSI
    Prob/Certs/           generated certificate (library CryptarchiaCerts)
  CryptarchiaCerts.lean   certificate library root
  CryptarchiaTest/        axiom checks, differential tests
  StochasticRecurrence/   report formalization (+ StochasticRecurrenceTest/)
  MiningOnboarding/       report formalization (+ MiningOnboardingTest/)
  tools/
    certgen/              Python generator for Prob/Certs
    difftest/             Python generator for CryptarchiaTest/Diff.lean
    forksim/              fork simulator: how many honest wins the TSI count sees
  shell.nix               pinned dev shell (elan, Python with numpy and scipy)
```

## Conventions

These keep the foundation usable as more components arrive.

1. **The specification layer is definitions only.** Files under `<Component>/Spec/` transcribe the specification documents rule by rule, as computable Lean definitions. Each file cites the document and revision it follows. Proofs about these definitions live in `Proof/` or `Prob/`, not in `Spec/`. Where the specification is silent or ambiguous, the definition takes the reading the implementation uses, or becomes a parameter so that theorems cover every reading. Each such point is recorded in the component's README.
2. **Analysis is separate from the specification.** A theorem states its assumptions as explicit hypotheses or as fields of a named structure (for example `Assm E`). Idealizations (random oracle, synchronized clocks, Δ-delivery) are listed in the component's README.
3. **No `sorry`, no new axioms.** Add each headline theorem to `CryptarchiaTest/Axioms.lean`, or to the equivalent file for a new component.
4. **Differential tests for executable definitions.** `tools/difftest` transliterates the pseudocode independently in Python and emits `#guard` checks. Extend it when you add or change a `Spec` definition.
5. **Generated files are reproducible.** Certificates under `Prob/Certs/` come from `tools/certgen` (see its README). Do not edit them by hand.
6. **Namespaces follow libraries.** `Cryptarchia.*` lives in `Cryptarchia/`, its probability layer in `Cryptarchia.Prob`. A new component uses its own top-level namespace.
7. **Shared abstractions.** Cryptarchia currently models the ledger abstractly (`Ledger` in `Cryptarchia/Spec/EpochState.lean`: the notes held after a chain). A ledger component should replace this abstraction, not duplicate it. Move anything two components need into a shared library at this level.

## Building

With Nix:

```sh
cd formal
nix-shell                         # elan and Python, with ELAN_HOME=formal/.elan
lake exe cache get                # Mathlib's prebuilt .olean files (about 5 GB)
lake build                        # every default target (all libraries except CryptarchiaCerts)
lake build CryptarchiaCerts       # the certificate: about an hour, a few GB of memory per file
lake env lean CryptarchiaTest/Axioms.lean    # axioms of every headline theorem
lake env lean StochasticRecurrenceTest/Axioms.lean
lake env lean MiningOnboardingTest/Axioms.lean
lake env lean MiningOnboardingTest/Report.lean   # calculator vs. the report's numbers
```

Without Nix, install [elan](https://github.com/leanprover/elan); the `lean-toolchain` file selects the Lean version. Then run the same `lake` commands.

On machines with limited memory, build with `LEAN_NUM_THREADS=4`, and build certificate files one at a time.
