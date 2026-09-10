"""Where the transaction byte counts come from.

`claim_tx_bytes` and `transfer_tx_bytes` were carried in the config as
``DERIVED  sim: fee.claim_tx_bytes()``. No such module exists, in this repository or its
history: the package was moved in from an external working tree and that module did not come
with it. This module replaces the citation with an actual derivation.

**What is specified.** Every primitive width below is read from
`mantle-transaction-encoding.md`, "Common Structures": a Groth16 proof is 128 bytes
(`pi_a` 32 + `pi_b` 64 + `pi_c` 32), `ZkSignature = Groth16`, a field element and a hash are
32, a `UINT64` is 8, a `Byte` is 1. `Note = Value ZkPublicKey` is therefore 40 and
`NoteId = FieldElement` is 32. `OpsProofs` is one `OpProof` per Operation, its variant fixed
by the Operation's opcode. The `Transfer` payload is `Inputs Outputs`, each a count byte
followed by its elements; its proof is a `ZkSignature`. The claim payload is given in the
Mantle specification's `ClaimPowRewardOp`: three 32-byte fields, `epoch_nonce`, `block_hash`
and `public_key` -- and since 2026-09-04 (PR 400, `d145eaf7`) its proof is a `ZkSignature`
over the transaction hash, where before it was `None`.

**What is not.** `CLAIM_POW_REWARD` still does not appear in `mantle-transaction-encoding.md`
-- not in the `OpPayload` list, not in `OpProof`'s variant list, which can therefore not
derive the claim's proof type it now has. So the encoded size of a claim transaction is
**not derivable from the specification tree**, and this module states the framing it assumes
rather than pretending otherwise:

- a two-byte operation count, where the document says `OpCount = Byte`;
- a two-byte length prefix on each operation, which the document does not describe.

Under the `None`-proof rule those assumptions reproduced **both** figures the specification's
own arithmetic then required -- 207 for a transfer and 306 for a claim transaction, the pair
behind the 6,664-lepta claim fee the pre-2026-09 Mantle text stated. That anchor now lives in
the PR 400 description rather than in the specification (the rationale was moved out on
2026-09-03), and the description's 6,664 predates the PR's own proof-and-gas change: with the
claim's ZkSignature the same framing gives **434** bytes, and with `CLAIM_POW_REWARD_GAS` at
590 the resting-price fee is `(434 + 1,180) * 7 = 11,298` lepta. The framing is unchanged
from the version both published figures pinned; only the specified inputs moved.

**And the uncertainty would not propagate far in any case.** Almost every result in the study
depends on the *ratio* of the two sizes rather than on either alone. Under the strict reading
(one-byte count, no per-operation prefixes) the sizes become 204 and 429, moving the fee
ratio and the claim fee by well under one percent.
"""
from __future__ import annotations

from dataclasses import dataclass

# --- primitive widths, `mantle-transaction-encoding.md` "Common Structures" --------------
GROTH16 = 128                 # pi_a (32) + pi_b (64) + pi_c (32)
ZK_SIGNATURE = GROTH16        # ZkSignature = Groth16
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


def transfer_payload(inputs: int = 1, outputs: int = 1) -> int:
    """`Transfer = Inputs Outputs`, each a count byte followed by its elements."""
    return BYTE + inputs * NOTE_ID + BYTE + outputs * NOTE


def claim_payload() -> int:
    """`ClaimPowRewardOp`: `epoch_nonce`, `block_hash`, `public_key`, all 32 bytes."""
    return HASH32 + HASH32 + ZK_PUBLIC_KEY


def encoded(payloads: list[int], proofs: list[int], *, framed: bool = True) -> int:
    """| ``bytes = op_count + sum(op_length + opcode + payload) + sum(proofs)``

    ``proofs`` carries one entry per Operation, per `OpsProofs`; a proof of `None`
    contributes zero bytes, which is how the pre-2026-09 claim encoded.
    """
    op_count = OP_COUNT_WIDTH if framed else BYTE
    prefix = OP_LENGTH_PREFIX if framed else 0
    return (op_count
            + sum(prefix + BYTE + p for p in payloads)
            + sum(proofs))


@dataclass(frozen=True)
class Sizes:
    transfer: int
    claim: int

    @property
    def difference(self) -> int:
        """What the claim operation adds: its 96-byte payload, its 128-byte ZkSignature,
        its opcode, and its framing."""
        return self.claim - self.transfer


def sizes(framed: bool = True) -> Sizes:
    """The two figures the config carries, or their strict-reading alternatives.

    The claim transaction is the self-funding pair from the Mantle example -- the claim
    Operation plus the `TRANSFER` spending the reward note -- each with its `ZkSignature`.
    """
    return Sizes(
        transfer=encoded([transfer_payload()], [ZK_SIGNATURE], framed=framed),
        claim=encoded([claim_payload(), transfer_payload()],
                      [ZK_SIGNATURE, ZK_SIGNATURE], framed=framed),
    )


def unframed() -> Sizes:
    """The strict reading of the encoding document: one-byte count, no length prefixes.

    Gives 204 and 429 against the config's 207 and 434. Kept so the sensitivity is visible
    rather than asserted.
    """
    return sizes(framed=False)
