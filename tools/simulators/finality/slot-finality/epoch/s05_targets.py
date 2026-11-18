"""The share of targets whose race meets two epoch nonces (REVIEW.md, statement 6.2).

An epoch of E slots: epoch e holds the slots [e E, (e + 1) E), and the lottery of slot s reads the
nonce of epoch floor(s / E). A race for a target in slot t that draws the lotteries of the slots
t, ..., t + L meets  n(t, L) = floor((t + L) / E) - floor(t / E) + 1  nonces.
Proved in REVIEW.md: for L <= E, n = 2 exactly when t is one of the last L slots of its epoch, a share
L / E of the slots, and n = 1 otherwise; for every L the mean of n over the slots of an epoch is
1 + L / E. This script checks both by enumeration at small sizes, and prints the shares for the
specification's K and for shorter epochs.
Usage: python s05_targets.py > out_05_targets.txt
"""
from fractions import Fraction

from common import CASES, EPOCH, H


def nonces(t: int, L: int, E: int) -> int:
    return (t + L) // E - t // E + 1


if __name__ == "__main__":
    checked = 0
    for E in range(1, 41):
        for L in range(0, 3 * E + 2):
            counts = [nonces(t, L, E) for t in range(5 * E, 6 * E)]       # the slots of one epoch
            assert Fraction(sum(counts), E) == 1 + Fraction(L, E)
            if L <= E:
                two = [t for t in range(5 * E, 6 * E) if nonces(t, L, E) == 2]
                assert two == list(range(6 * E - L, 6 * E))               # the last L slots of the epoch
                assert all(c in (1, 2) for c in counts)
            assert max(counts) == 1 + -(-L // E)                          # 1 + ceil(L / E)
            checked += 1
    print(f"enumeration: {checked} pairs (E, L) with E <= 40 and L <= 3 E + 1: the last-L-slots rule, the mean 1 + L/E and the maximum 1 + ceil(L/E) all hold")

    print("\nshare of targets whose race of K slots meets two nonces, K / E")
    print(" epoch (h) | " + " | ".join(f"{name}: K = {K}" for name, (K, _) in CASES.items()))
    for hours in (180, 150, 120, 118.2, 100, 90, 72, 60, 54, 45, 36, 30, 24.5, 24, 20):
        E = int(round(hours * H))
        cells = []
        for name, (K, _) in CASES.items():
            if K <= E:
                cells.append(f"{100 * K / E:6.2f} %")
            else:
                cells.append(f"all; up to {1 + -(-K // E)} nonces")
        print(f"{hours:10.1f} | " + " | ".join(cells))
    print(f"\nthe specification's epoch is {EPOCH} slots; a race that lasts longer than K reaches more targets:")
    for name, (K, _) in CASES.items():
        for hours in sorted({K / H, 11, 12, 13, 14.2, 18, 24}):
            L = int(round(hours * H))
            if L >= K:
                print(f"  {name}: a race of {hours:5.1f} h meets two nonces for {100 * L / EPOCH:5.2f} % of targets")
