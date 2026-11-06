"""HashWX written from its specification, doc/specification.md at v1.0.0.

It exists to cross-check the reference library, so that test vectors come from two
implementations, and to show that the specification is enough to write one. Its
author had read parts of the library's src/hashwx.c, so it is not a clean-room
implementation and says nothing about licensing. It is
far too slow to mine with, a few milliseconds a hash. The permutation lists are read from
the specification rather than copied here.
"""
from __future__ import annotations

import hashlib
import itertools
import re
from pathlib import Path

M64 = (1 << 64) - 1
NONCES_PER_SEED = 463
DEEP_PROGRAMS = {0, 6, 12, 18, 24, 30}

MULOR, MULXOR, MULADD, RMCG = 0, 1, 2, 3
XORROR, ADDROR, SUBROR = 4, 5, 6
XORASR, ADDASR, SUBASR = 7, 8, 9
XORLSR, ADDLSR, SUBLSR = 10, 11, 12
CBRANCH, UBRANCH, STORE = 13, 14, 15

XAS_TABLE = [XORROR, ADDROR, SUBROR, XORASR, ADDASR, SUBASR, XORLSR, ADDLSR, SUBLSR]
MUL_TABLE = [MULOR, MULXOR, MULADD]
# Appendix B lists every arrangement of 3 M and 4 X, lexicographically sorted.
TEMPLATES = sorted({"".join(p) for p in itertools.permutations("MMMXXXX")})
assert len(TEMPLATES) == 35


def _rotr(x: int, n: int) -> int:
    n &= 63
    return ((x >> n) | (x << (64 - n))) & M64 if n else x


def _sipround(v0: int, v1: int, v2: int, v3: int) -> tuple[int, int, int, int]:
    v0 = (v0 + v1) & M64
    v2 = (v2 + v3) & M64
    v1 = _rotr(v1, 51)
    v3 = _rotr(v3, 48)
    v1 ^= v0
    v3 ^= v2
    v0 = _rotr(v0, 32)
    v2 = (v2 + v1) & M64
    v0 = (v0 + v3) & M64
    v1 = _rotr(v1, 47)
    v3 = _rotr(v3, 43)
    v1 ^= v2
    v3 ^= v0
    v2 = _rotr(v2, 32)
    return v0, v1, v2, v3


class _Generator:
    """The Siphash generator of Appendix A."""

    def __init__(self, k0: int, k1: int, salt: int) -> None:
        self.k0, self.k1 = k0, k1
        v0 = 0x736f6d6570736575 ^ k0
        v1 = 0x646f72616e646f6d ^ k1
        v2 = 0x6c7967656e657261 ^ k0
        v3 = 0x7465646279746573 ^ k1
        v3 ^= salt
        v0, v1, v2, v3 = _sipround(v0, v1, v2, v3)
        v0 ^= salt
        v2 ^= 0xbb
        for _ in range(3):
            v0, v1, v2, v3 = _sipround(v0, v1, v2, v3)
        self.state = [v0, v1, v2, v3]
        self.pos = 3

    def next(self) -> int:
        if self.pos < 0:
            v0, v1, v2, v3 = self.state
            v0 ^= self.k0
            v1 ^= self.k1
            v2 ^= self.k0
            v3 ^= self.k1
            for _ in range(4):
                v0, v1, v2, v3 = _sipround(v0, v1, v2, v3)
            self.state = [v0, v1, v2, v3]
            self.pos = 3
        out = self.state[self.pos]
        self.pos -= 1
        return out


def _load_permutations(specification: Path) -> tuple[list[str], list[str]]:
    text = specification.read_text()

    def block(heading: str) -> list[str]:
        section = text.split(heading, 1)[1]
        code = section.split("```", 2)[1]
        return re.findall(r"\b[0-7]{8}\b", code)

    shallow = block("#### D.1 Shallow permutations")
    deep = block("#### D.2 Deep permutations")
    if len(shallow) != 256 or len(deep) != 24:
        raise ValueError(f"expected 256 and 24 permutations, read {len(shallow)} and {len(deep)}")
    return shallow, deep


class HashWX:
    """One instance: 32 programs and a Siphash key, generated from a 32-byte seed."""

    def __init__(self, seed: bytes, specification: Path) -> None:
        if len(seed) != 32:
            raise ValueError("a seed is 32 bytes")
        words = [int.from_bytes(seed[i:i + 8], "little") for i in range(0, 32, 8)]
        shallow, deep = _load_permutations(specification)
        self.key = (words[2], words[3])
        gen = _Generator(words[0], words[1], M64)
        self.programs = [self._program(gen, j, shallow, deep) for j in range(32)]

    @staticmethod
    def _program(gen: _Generator, index: int, shallow: list[str], deep: list[str]):
        g = [gen.next() for _ in range(16)]
        template = TEMPLATES[g[7] % 35]

        # Appendix C: Fisher-Yates over the high 32 bits of gen[0] to gen[6].
        dst = [0] * 8
        for i in range(1, 8):
            dst[i] = i
            j = (g[i - 1] >> 32) % (i + 1)
            dst[i] = dst[j]
            dst[j] = i

        if index in DEEP_PROGRAMS:
            perm = deep[g[7] % 24]
        else:
            perm = shallow[g[7] % 256]

        def immediate(op: int, i: int) -> int:
            v = g[7 + i]
            if op <= MULADD:
                return (1, 9, 33)[v % 3]
            if op <= SUBROR:
                return 1 + v % 63
            return 1 + v % 3

        body = [(STORE, 0, 0, 0), (RMCG, dst[0], 8, immediate(RMCG, 1))]
        for slot in range(7):
            low = g[slot] & 0xffffffff
            op = MUL_TABLE[low % 3] if template[slot] == "M" else XAS_TABLE[low % 9]
            position = slot + 1  # dst[1] and perm[1] belong to the first arithmetic instruction
            body.append((op, dst[position], dst[int(perm[position])], immediate(op, slot + 2)))
        body.append((UBRANCH if index == 31 else CBRANCH, 0, 0, 0))
        return body

    def __call__(self, nonce: int) -> int:
        gen = _Generator(self.key[0], self.key[1], nonce & M64)
        r = [gen.next() for _ in range(8)]
        r.append(((r[0] ^ r[4]) & (M64 ^ 7)) | 3)
        memory = bytearray(16392)
        memory[16384:16392] = r[8].to_bytes(8, "little")
        sp = 16384

        def load(address: int) -> int:
            a = address % 16384
            return int.from_bytes(memory[a:a + 8], "little")

        def signed(x: int) -> int:
            return x - (1 << 64) if x >> 63 else x

        for mf in (0, 1):
            for _ in range(4):
                bc = 32
                for program in self.programs:
                    bf = 0
                    pc = 0
                    while pc < len(program):
                        op, d, s, imm = program[pc]
                        pc += 1
                        if op == STORE:
                            if not mf:
                                sp -= 64
                                for k in range(8):
                                    memory[sp + 8 * k:sp + 8 * k + 8] = r[7 - k].to_bytes(8, "little")
                        elif op == RMCG:
                            r[d] = _rotr((r[d] * r[8]) & M64, imm)
                            bf = (r[d] >> 5) & 1
                        elif op == CBRANCH:
                            if bc and not bf:
                                bc -= 1
                                pc = 0
                        elif op == UBRANCH:
                            if bc:
                                bc -= 1
                                pc = 0
                        else:
                            v = load(r[s]) if mf else r[s]
                            if op == MULOR:
                                r[d] = ((r[d] | imm) * v) & M64
                            elif op == MULXOR:
                                r[d] = ((r[d] ^ imm) * v) & M64
                            elif op == MULADD:
                                r[d] = (((r[d] + imm) & M64) * v) & M64
                            elif op == XORROR:
                                r[d] = _rotr(r[d], imm) ^ v
                            elif op == ADDROR:
                                r[d] = (_rotr(r[d], imm) + v) & M64
                            elif op == SUBROR:
                                r[d] = (_rotr(r[d], imm) - v) & M64
                            elif op == XORASR:
                                r[d] = ((signed(r[d]) >> imm) & M64) ^ v
                            elif op == ADDASR:
                                r[d] = (((signed(r[d]) >> imm) & M64) + v) & M64
                            elif op == SUBASR:
                                r[d] = (((signed(r[d]) >> imm) & M64) - v) & M64
                            elif op == XORLSR:
                                r[d] = (r[d] >> imm) ^ v
                            elif op == ADDLSR:
                                r[d] = ((r[d] >> imm) + v) & M64
                            elif op == SUBLSR:
                                r[d] = ((r[d] >> imm) - v) & M64

        r[0], r[1], r[2], r[3] = _sipround(r[0], r[1], r[2], r[3])
        r[4], r[5], r[6], r[7] = _sipround(r[4], r[5], r[6], r[7])
        return r[3] ^ r[7] ^ r[8]


def derive_seed(challenge: bytes, nonce: int) -> bytes:
    group = nonce // NONCES_PER_SEED
    return hashlib.blake2b(challenge + group.to_bytes(8, "little"), digest_size=32).digest()


def ticket(challenge: bytes, nonce: int, specification: Path) -> int:
    """The output a nonce gives for a challenge, as Common Cryptographic Components defines it."""
    return HashWX(derive_seed(challenge, nonce), specification)(nonce)
