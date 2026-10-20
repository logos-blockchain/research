"""Gates for the price of a second hash in the proof of leadership (scripts/j1_circuit.py)."""

import pathlib
import shutil
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from j1_circuit import CHECKOUT, OUT, measure  # noqa: E402

# Poseidon2 over BN254 with a state of three: 8 external rounds of three S-boxes and 56 internal
# rounds of one (common-cryptographic-components.md at logos-lips 47a73cdc); x^5 takes three
# multiplications.
PER_PERMUTATION = 3 * (8 * 3 + 56)

# The released v0.5.6 proving key (pol/proving_key.zkey of the macos-aarch64 release, SHA-1
# e04c4a7e): 20,531 variables, 9 public values, a domain of 2^15, and coefficients over 20,470
# rows, the constraints plus the public values and the constant.
RELEASED = dict(constraints=20460, wires=20531, public=9, domain=32768)

needs_circom = pytest.mark.skipif(shutil.which("circom") is None or not CHECKOUT.exists(),
                                  reason="needs circom 2.2.2 and logos-blockchain-circuits v0.5.6")


@needs_circom
def test_each_hash_costs_its_permutations():
    """A hash absorbs its domain tag, its values and a padding element, one permutation each; the
    first sees only constants and is folded away, so n values cost n + 1 permutations."""
    t = measure().set_index("variant")
    for key, value in RELEASED.items():
        assert t.loc["today", key] == value
    permutations = {"the contribution derived by every node": 0,
                    "the tag bound to the epoch nonce": 1,
                    "the contribution proved from the tag": 2 + 1,
                    "the contribution proved from the secrets": 4 + 1}
    for variant, n in permutations.items():
        assert t.loc[variant, "added"] == n * PER_PERMUTATION
    recorded = pd.read_csv(OUT / "circuit.csv").set_index("variant")
    assert (recorded[["constraints", "wires", "public", "domain"]]
            == t[["constraints", "wires", "public", "domain"]]).all().all()
