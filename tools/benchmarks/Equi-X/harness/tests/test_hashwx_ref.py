"""The from-specification HashWX against upstream's vectors and the reference library."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from equix_bench.hashwx_ref import HashWX, derive_seed, ticket

ROOT = Path(__file__).resolve().parents[2]
SPECIFICATION = ROOT / "vendored" / "hashwx" / "doc" / "specification.md"
VECTORS_TOOL = ROOT / "build" / "runners" / "hashwx-c" / "hashwx_vectors"

needs_source = pytest.mark.skipif(not SPECIFICATION.exists(), reason="run scripts/setup_hashwx.sh")
needs_tool = pytest.mark.skipif(not VECTORS_TOOL.exists(), reason="run scripts/setup_hashwx.sh")

SEED_A = "5468697320697320612074657374207365656420666f72206861736877780000"
SEED_B = "4c6f72656d20697073756d20646f6c6f722073697420616d6574000000000000"

# doc/specification.md, Appendix F.
UPSTREAM = [
    (SEED_A, 0, 0x973684176f8ee362),
    (SEED_A, 123456, 0x401983bb07d69b07),
    (SEED_B, 123456, 0x4af38d834a9a8d3d),
    (SEED_B, 987654321123456789, 0x6a8a5514432e17a3),
]


@needs_source
@pytest.mark.parametrize("seed,nonce,expected", UPSTREAM)
def test_upstream_vectors(seed, nonce, expected):
    assert HashWX(bytes.fromhex(seed), SPECIFICATION)(nonce) == expected


def test_seed_changes_at_the_group_boundary():
    challenge = bytes.fromhex("deadbeef")
    assert derive_seed(challenge, 0) == derive_seed(challenge, 462)
    assert derive_seed(challenge, 462) != derive_seed(challenge, 463)
    assert derive_seed(challenge, 463) == derive_seed(challenge, 925)


@needs_source
@needs_tool
@pytest.mark.parametrize("nonce", [0, 462, 463, 2**32 + 7, 2**64 - 1])
def test_against_the_reference_library(nonce):
    challenge = "00112233445566778899aabbccddeeff" * 2
    out = subprocess.run([str(VECTORS_TOOL), "ticket", challenge, str(nonce)],
                         capture_output=True, text=True, check=True).stdout
    fields = dict(line.split(" ", 1) for line in out.splitlines() if " " in line)
    mine = ticket(bytes.fromhex(challenge), nonce, SPECIFICATION)
    assert fields["seed"] == derive_seed(bytes.fromhex(challenge), nonce).hex()
    assert int(fields["interpreted"], 16) == mine
    assert int(fields["compiled"], 16) == mine
