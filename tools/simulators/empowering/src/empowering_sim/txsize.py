"""Where the transaction byte counts come from.

`claim_tx_bytes = 306` and `transfer_tx_bytes = 207` were carried in the config as
``DERIVED  sim: fee.claim_tx_bytes()``. No such module exists, in this repository or its
history: the package was moved in from an external working tree and that module did not come
with it. This module replaces the citation with an actual derivation.

**What is specified.** Every primitive width below is read from
`mantle-transaction-encoding.md`, "Common Structures": a Groth16 proof is 128 bytes
(`pi_a` 32 + `pi_b` 64 + `pi_c` 32), a field element and a hash are 32, a `UINT64` is 8, a
`Byte` is 1. `Note = Value ZkPublicKey` is therefore 40 and `NoteId = FieldElement` is 32. The
`Transfer` payload is `Inputs Outputs`, each a count byte followed by its elements. The claim
payload is given in the Mantle specification's `ClaimPowRewardOp`: three 32-byte fields,
`epoch_nonce`, `block_hash` and `public_key`.

**What is not.** `CLAIM_POW_REWARD` does not appear in `mantle-transaction-encoding.md` at all
-- not in the `OpPayload` list, not in `OpProof`. The operation entered Mantle at revision
1.11.0 on 2026-08-11 and the encoding document has not been updated for it. So the encoded size
of a claim transaction is **not derivable from the specification tree**, and this module states
the framing it assumes rather than pretending otherwise:

- a two-byte operation count, where the document says `OpCount = Byte`;
- a two-byte length prefix on each operation, which the document does not describe;
- one proof for the transaction, where `OpsProofs` is one proof per operation.

Those three assumptions reproduce **both** published figures exactly, which is why they are the
ones recorded. They are a reconstruction of what the lost module must have done, not a reading
of the specification, and `unframed()` gives the strict-reading alternative for comparison.

**The specification settles it anyway.** `mantle:1858` states a claim's fee at the markets'
resting level as 6,664 lepta. The framed reading gives `(306 + 646) * 7 = 6,664` exactly; the
strict reading gives 6,629. So the assumed framing is not merely the one that reproduces the
config, it is the one the specification's own arithmetic requires -- which is as close to a
derivation as this can get while the encoding document omits the operation.

**And the uncertainty would not propagate far in any case.** Almost every result in the study
depends on the *ratio* of the two sizes rather than on either alone. Under the strict reading
the sizes become 204 and 301, moving the fee ratio by 0.15% and the claim fee by 0.53%.
"""
from __future__ import annotations

from dataclasses import dataclass

# --- primitive widths, `mantle-transaction-encoding.md` "Common Structures" --------------
GROTH16 = 128                 # pi_a (32) + pi_b (64) + pi_c (32)
FIELD_ELEMENT = 32            # BN254 field element, little-endian
HASH32 = 32
ZK_PUBLIC_KEY = FIELD_ELEMENT
UINT64 = 8
UINT16 = 2
BYTE = 1

NOTE = UINT64 + ZK_PUBLIC_KEY          # Note = Value ZkPublicKey
NOTE_ID = FIELD_ELEMENT                # NoteId = FieldElement

# --- framing, ASSUMED: reconstructed, not read. See the module docstring. ----------------
OP_COUNT_WIDTH = UINT16                # the document says `OpCount = Byte`
OP_LENGTH_PREFIX = UINT16              # the document describes no per-operation prefix
PROOFS_PER_TX = 1                      # `OpsProofs` is specified as one proof per operation


def transfer_payload(inputs: int = 1, outputs: int = 1) -> int:
    """`Transfer = Inputs Outputs`, each a count byte followed by its elements."""
    return BYTE + inputs * NOTE_ID + BYTE + outputs * NOTE


def claim_payload() -> int:
    """`ClaimPowRewardOp`: `epoch_nonce`, `block_hash`, `public_key`, all 32 bytes."""
    return HASH32 + HASH32 + ZK_PUBLIC_KEY


def encoded(payloads: list[int], *, framed: bool = True) -> int:
    """| ``bytes = op_count + sum(op_length + opcode + payload) + proofs * groth16``"""
    op_count = OP_COUNT_WIDTH if framed else BYTE
    prefix = OP_LENGTH_PREFIX if framed else 0
    return (op_count
            + sum(prefix + BYTE + p for p in payloads)
            + PROOFS_PER_TX * GROTH16)


@dataclass(frozen=True)
class Sizes:
    transfer: int
    claim: int

    @property
    def difference(self) -> int:
        """What the claim operation adds: its 96-byte payload, its opcode, and its framing."""
        return self.claim - self.transfer


def sizes(framed: bool = True) -> Sizes:
    """The two figures the config carries, or their strict-reading alternatives."""
    return Sizes(
        transfer=encoded([transfer_payload()], framed=framed),
        claim=encoded([claim_payload(), transfer_payload()], framed=framed),
    )


def unframed() -> Sizes:
    """The strict reading of the encoding document: one-byte count, no length prefixes.

    Gives 204 and 301 against the config's 207 and 306. Kept so the sensitivity is visible
    rather than asserted.
    """
    return sizes(framed=False)
