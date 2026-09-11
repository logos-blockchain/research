# Proof-system transition

Analysis supporting the dual-key notes RFC, [logos-lips#442], and the later
move of the hand-written circuits from Groth16 over BN254 to a STARK-based
proof system over the Goldilocks field.

| Report | Question it answers |
|---|---|
| [analysis-proof-system-transition.md](analysis-proof-system-transition.md) | Given that every note commits to a STARK-field public key from day one, what happens at the transition: which derivations change, how nodes re-key the ledger from public data, what is kept for legacy reward claims, and what stays open. |

The normative specifications carry only the pre-transition change (the second
key in every note and declaration, bound by the note identifier). Everything
about the transition itself lives here until it is specified in its own right.

[logos-lips#442]: https://github.com/logos-co/logos-lips/pull/442
