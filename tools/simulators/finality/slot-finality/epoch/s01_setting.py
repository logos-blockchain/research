"""The setting of the latest #533 and of its base (REVIEW.md, sections 1.2 and 5.8): the constants,
the values derived from them, and the finality floor.

The floor is computed twice:
  1. with the code that cryptarchia-v1-protocol.md prints in Finality Floor (lines 528-551 on the
     10-hour branch), copied here without change except that K is an argument;
  2. in exact integer arithmetic: blocks_short(n) = sum_{i<n} C(m, i) 29^(m-i) / 30^m with
     m = K - n T_M, compared with 10^-9 without rounding.
Usage: python s01_setting.py > out_01_setting.txt
"""
from math import exp, lgamma, log

from common import CASES, CUT_OFF, EPOCH, F_DEN, GAP, H, K_SEC, PERIOD, PHASE_1, PHASE_2, PHASE_3, S_GEN, T_M, U

f = 1 / 30
EPSILON = 1e-9      # ε, the chance allowed that the chain misses the floor


def spec_floor(K: int) -> int:
    # --- copied from the specification, Finality Floor -------------------------------------
    def blocks_short(n: int) -> float:
        # The chance that fewer than n blocks fit in K slots. A gap between blocks is T_M
        # slots plus the wait for the next win, whose chance per slot is f. So n blocks fit
        # only if the slots left after n delays hold at least n wins.
        slots = K - n * T_M
        if slots < n:
            return 1.0
        return sum(
            exp(lgamma(slots + 1) - lgamma(i + 1) - lgamma(slots - i + 1)
                + i * log(f) + (slots - i) * log(1 - f))
            for i in range(n)
        )

    def finality_floor() -> int:
        n = 0
        while blocks_short(n + 1) <= EPSILON:
            n += 1
        return n
    # ----------------------------------------------------------------------------------------
    return finality_floor()


def exact_short(K: int, n: int, d: int = T_M):
    """(numerator, denominator) of blocks_short(n) at f = 1/30, exact."""
    m = K - n * d
    if m < n:
        return 1, 1
    term = 29 ** m                       # C(m, 0) 29^m
    total = 0
    for i in range(n):
        total += term
        term = term * (m - i) // ((i + 1) * 29)   # C(m, i+1) 29^(m-i-1), an exact division
    return total, 30 ** m


def as_float(num: int, den: int) -> float:
    scale = 10 ** 40
    return (num * scale // den) / scale


if __name__ == "__main__":
    print("constants (slots of 1 second)")
    print(f"  f = 1/{F_DEN}, k = {K_SEC}, floor(k/f) = {U} slots = {U / H:g} h")
    print(f"  phases: {PHASE_1}, {PHASE_2}, {PHASE_3} slots = {PHASE_1 / H:g} h, {PHASE_2 / H:g} h, {PHASE_3 / H:g} h")
    print(f"  epoch: {EPOCH} slots = {EPOCH / H:g} h")
    print(f"  cut-off: slot {CUT_OFF} of the epoch = {CUT_OFF / H:g} h; gap to the next epoch: {GAP} slots = {GAP / H:g} h")
    print(f"  PERIOD = {PERIOD} slots = {PERIOD / H:g} h")
    print(f"  s_gen = floor(k/(4f)) = {S_GEN} slots = {S_GEN / H:g} h; 2 s_gen = {2 * S_GEN} slots = {2 * S_GEN / H:g} h")
    print(f"  T_M = {T_M} slots")
    for name, (K, phi) in CASES.items():
        print(f"\n{name}: K = {K} slots = {K / H:g} h, phi = {phi}")
        print(f"  K / epoch = {K / EPOCH:.6f}; phase 1 / K = {PHASE_1 / K:.3f}; phase 3 / K = {PHASE_3 / K:.3f}; K - 2 s_gen = {K - 2 * S_GEN} slots")
        got = spec_floor(K)
        print(f"  the specification's code, as printed: finality_floor() = {got}  ({'equal to' if got == phi else 'DIFFERENT FROM'} the Constants row)")
        for n in (phi, phi + 1):
            num, den = exact_short(K, n)
            below = num * 10 ** 9 <= den
            print(f"  exact: blocks_short({n}) = {as_float(num, den):.6e}  {'<=' if below else '>'} 1e-9")
        for d in (T_M, 10, 0):
            # blocks_short(n) grows with n, so the floor is found by bisection
            lo, hi = 0, K // (d + 1) + 1          # blocks_short(lo) <= 1e-9 < blocks_short(hi)
            while hi - lo > 1:
                mid = (lo + hi) // 2
                num, den = exact_short(K, mid, d)
                if num * 10 ** 9 <= den:
                    lo = mid
                else:
                    hi = mid
            print(f"  exact: the derivation with every block {d} slots late gives {lo}")
